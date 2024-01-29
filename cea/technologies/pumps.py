# -*- coding: utf-8 -*-
"""
pumps
"""




from math import log

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.constants import P_WATER_KGPERM3
from cea.optimization.constants import PUMP_ETA
from cea.analysis.costs.equations import calc_capex_annualized

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# operation and total costs

def Pump_operation(P_design):
    """
    Modeled after:
        05_merkblatt_wirtschaftlichkeit_14.pdf
        23_merkblatt_pumpen_web.pdf
        ER_2010_11_Heizungspumpen.pdf
        MerkblattPreiseFU2010_2011.pdf
        MerkblattPreiseMotoren2010_2011.pdf
    P_design : float
        Load of time step
    eta_el : float
        electric efficiency of Pumping operation in abs. numbers (e.g. 0.93)
    """

    x = [0.5, 0.75, 1.1, 1.5, 2.2, 3, 4, 5.5, 7.5, 11, 15, 18, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200,
         220]  # Nominal load in kW
    y = [83, 83.5, 84, 85.2, 86.8, 87.8, 88.8, 89.5, 90.5, 91.5, 92.2, 92.6, 93, 93.6, 93.9, 94.3, 94.6, 95, 95.2, 95.4,
         95.6, 95.9, 96, 96]  # efficiency in %
    # do the interpolation
    eff_of_Pmax = interp1d(x, y, kind='cubic')
    eta_motor = eff_of_Pmax(float(P_design) / float(100))
    eta_pump_fluid = 0.8
    eta_pumping = eta_pump_fluid * eta_motor
    return eta_pumping, eta_pump_fluid, eta_motor


def calc_Ctot_pump(master_to_slave_vars, network_features, locator, network_type
                   ):
    """
    Computes the total pump investment cost
    :type master_to_slave_vars : class context
    :type network_features : class ntwFeatures
    :rtype pumpCosts : float
    :returns pumpCosts: pumping cost
    """

    if network_type == "DH":
        # local variables
        nominal_E_pump_W = network_features.E_pump_DHN_W
        nominal_massflowrate_kgs = network_features.mass_flow_rate_DHN

        #get the mass flow rate of this neworkt and the pressireloss
        data = master_to_slave_vars.DH_network_summary_individual
        mass_flow_rate_kgs = data["mdot_DH_netw_total_kgpers"].values

    if network_type == "DC":
        # local variables
        nominal_E_pump_W = network_features.E_pump_DCN_W
        nominal_massflowrate_kgs = network_features.mass_flow_rate_DCN

        #get the mass flow rate of this neworkt and the pressireloss
        data = master_to_slave_vars.DC_network_summary_individual
        if master_to_slave_vars.WasteServersHeatRecovery == 1:
            mass_flow_rate_kgs = data["mdot_cool_space_cooling_and_refrigeration_netw_all_kgpers"].values
        else:
            mass_flow_rate_kgs = data["mdot_cool_space_cooling_data_center_and_refrigeration_netw_all_kgpers"].values

    #get pumping energy and peak load
    E_pump_W = nominal_E_pump_W * (mass_flow_rate_kgs / nominal_massflowrate_kgs)
    peak_pump_power_W = np.max(E_pump_W)

    #get costs
    Capex_a_pump_USD, \
    Opex_fixed_pump_USD, \
    Capex_pump_USD = calc_Cinv_pump(peak_pump_power_W, locator, 'PU1')  # investment of Machinery

    return Capex_a_pump_USD, Opex_fixed_pump_USD, Capex_pump_USD, E_pump_W


# investment and maintenance costs

def calc_pump_power(mass_flow_rate_kgs, pressure_loss_Pa):
    E_pump_W = mass_flow_rate_kgs * pressure_loss_Pa / P_WATER_KGPERM3 / PUMP_ETA
    return E_pump_W


def calc_Cinv_pump(pump_peak_W, locator, technology_type):
    """
    Calculates the cost of a pumping device.
    if the nominal load (electric) > 375kW, a new pump is installed
    if the nominal load (electric) < 500W, a pump with Pel_design = 500W is assumed
    Investement costs are calculated upon the life time of a GHP (20y) and a GHP- related interest rate of 6%
    :type deltaP : float
    :param deltaP: nominal pressure drop that has to be overcome with the pump
    :type mdot_kgpers : float
    :param mdot_kgpers: nominal mass flow
    :type eta_pumping : float
    :param pump efficiency: (set 0.8 as standard value, eta = E_pumping / E_elec)
    :rtype InvC_return : float
    :returns InvC_return: total investment Cost in CHF
    :rtype InvCa : float
    :returns InvCa: annualized investment costs in CHF/year
    """

    Pump_max_kW = 375.0
    Pump_min_kW = 0.5
    nPumps = int(np.ceil(pump_peak_W / 1000.0 / Pump_max_kW))
    # if the nominal load (electric) > 375kW, a new pump is installed
    Pump_Array_W = np.zeros((nPumps))
    Pump_Remain_W = pump_peak_W

    Capex_a_pump_USD = 0.0
    Opex_fixed_pump_USD = 0.0
    Capex_pump_USD = 0.0

    for pump_i in range(nPumps):
        # calculate pump nominal capacity
        Pump_Array_W[pump_i] = min(Pump_Remain_W, Pump_max_kW * 1000)
        if Pump_Array_W[pump_i] < Pump_min_kW * 1000:
            Pump_Array_W[pump_i] = Pump_min_kW * 1000
        Pump_Remain_W -= Pump_Array_W[pump_i]

        PUMP_COST_DATA = pd.read_excel(locator.get_database_conversion_systems(), sheet_name="Pump")
        pump_cost_data = PUMP_COST_DATA[PUMP_COST_DATA['code'] == technology_type]
        # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
        # capacity for the corresponding technology from the database
        if Pump_Array_W[pump_i] < pump_cost_data.iloc[0]['cap_min']:
            Pump_Array_W[pump_i] = pump_cost_data.iloc[0]['cap_min']
        pump_cost_data = pump_cost_data[
            (pump_cost_data['cap_min'] <= Pump_Array_W[pump_i]) & (pump_cost_data['cap_max'] > Pump_Array_W[pump_i])]

        Inv_a = pump_cost_data.iloc[0]['a']
        Inv_b = pump_cost_data.iloc[0]['b']
        Inv_c = pump_cost_data.iloc[0]['c']
        Inv_d = pump_cost_data.iloc[0]['d']
        Inv_e = pump_cost_data.iloc[0]['e']
        Inv_IR = pump_cost_data.iloc[0]['IR_%']
        Inv_LT = pump_cost_data.iloc[0]['LT_yr']
        Inv_OM = pump_cost_data.iloc[0]['O&M_%'] / 100

        InvC = Inv_a + Inv_b * (Pump_Array_W[pump_i]) ** Inv_c + (Inv_d + Inv_e * Pump_Array_W[pump_i]) * log(
            Pump_Array_W[pump_i])

        Capex_a_pump_USD += calc_capex_annualized(InvC, Inv_IR, Inv_LT)
        Opex_fixed_pump_USD += InvC * Inv_OM
        Capex_pump_USD += InvC

    return Capex_a_pump_USD, Opex_fixed_pump_USD, Capex_pump_USD


def calc_water_body_uptake_pumping(Q_gen_W,
                                   T_district_return_K,
                                   T_district_supply_K):
    # Values for the calculation of Delta P (from F. Muller network optimization code)
    # WARNING : current = values for Inducity - Zug
    DELTA_P_COEFF = 104.81
    DELTA_P_ORIGIN = 59016

    mdot_DCN_kgpers = Q_gen_W / abs((
                                            T_district_return_K - T_district_supply_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)  # since it is used for heating and cooling
    deltaP = 2 * (DELTA_P_COEFF * mdot_DCN_kgpers + DELTA_P_ORIGIN)
    E_used_Lake_W = deltaP * (mdot_DCN_kgpers / 1000) / PUMP_ETA
    if E_used_Lake_W == float("inf"):
        print(f"{mdot_DCN_kgpers} {deltaP} {E_used_Lake_W} {Q_gen_W} {T_district_return_K} {T_district_supply_K}")

    return E_used_Lake_W

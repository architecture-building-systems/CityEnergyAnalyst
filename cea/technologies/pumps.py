# -*- coding: utf-8 -*-
"""
pumps
"""
from __future__ import division
import os
import pandas as pd
from scipy.interpolate import interp1d
from math import log
import numpy as np
from cea.optimization.constants import PUMP_ETA
from cea.constants import DENSITY_OF_WATER_AT_60_DEGREES_KGPERM3

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


def calc_Ctot_pump(dicoSupply, ntwFeat, locator, lca, config):
    """
    Computes the total pump investment cost
    :type dicoSupply : class context
    :type ntwFeat : class ntwFeatures
    :rtype pumpCosts : float
    :returns pumpCosts: pumping cost
    """
    Opex_var_pumps = 0
    # nBuild = dicoSupply.nBuildingsConnected
    # ntot = len(buildList)

    Opex_var_pumps = 0
    if config.district_heating_network:


        df = pd.read_csv(locator.get_optimization_network_data_folder(dicoSupply.network_data_file_heating), usecols=["mdot_DH_netw_total_kgpers"])
        mdotA_kgpers = np.array(df)
        mdotnMax_kgpers = np.amax(mdotA_kgpers)

        # mdot0Max = np.amax( np.array( pd.read_csv("Network_summary_result_all.csv", usecols=["mdot_heat_netw_total"]) ) )

        for i in range(int(np.shape(mdotA_kgpers)[0])):
            deltaP = 2 * (104.81 * mdotA_kgpers[i][0] + 59016)
            Opex_var_pumps += deltaP * mdotA_kgpers[i][0] / 1000 * lca.ELEC_PRICE / PUMP_ETA

        deltaPmax = np.max((ntwFeat.DeltaP_DHN) * dicoSupply.number_of_buildings_connected_heating / dicoSupply.total_buildings)

        Capex_a_pump_USD, Opex_fixed_pump_USD, Capex_pump_USD = calc_Cinv_pump(2*deltaPmax, mdotnMax_kgpers, PUMP_ETA, config, locator, 'PU1')  # investment of Machinery

    if config.district_cooling_network:

        if dicoSupply.WasteServersHeatRecovery == 1:
            df = pd.read_csv(locator.get_optimization_network_data_folder(dicoSupply.network_data_file_heating),
                             usecols=["mdot_cool_space_cooling_and_refrigeration_netw_all_kgpers"])
        else:
            df = pd.read_csv(locator.get_optimization_network_data_folder(dicoSupply.network_data_file_heating),
                             usecols=["mdot_cool_space_cooling_data_center_and_refrigeration_netw_all_kgpers"])

        mdotA_kgpers = np.array(df)
        mdotnMax_kgpers = np.amax(mdotA_kgpers)

        # mdot0Max = np.amax( np.array( pd.read_csv("Network_summary_result_all.csv", usecols=["mdot_heat_netw_total"]) ) )

        for i in range(int(np.shape(mdotA_kgpers)[0])):
            deltaP = 2 * (104.81 * mdotA_kgpers[i][0] + 59016)
            Opex_var_pumps += deltaP * mdotA_kgpers[i][0] / 1000 * lca.ELEC_PRICE[i] / PUMP_ETA

        deltaPmax = np.max((ntwFeat.DeltaP_DCN) * dicoSupply.number_of_buildings_connected_cooling / dicoSupply.total_buildings)

        Capex_a_pump_USD, Opex_fixed_pump_USD, Capex_pump_USD = calc_Cinv_pump(2*deltaPmax, mdotnMax_kgpers, PUMP_ETA, config,
                                             locator, 'PU1')  # investment of Machinery


    return Capex_a_pump_USD, Opex_fixed_pump_USD, Opex_var_pumps, Capex_pump_USD


# investment and maintenance costs

def calc_Cinv_pump(deltaP, mdot_kgpers, eta_pumping, config, locator, technology_type):
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

    E_pumping_required_W = mdot_kgpers * deltaP / DENSITY_OF_WATER_AT_60_DEGREES_KGPERM3
    P_motor_tot_W = E_pumping_required_W / eta_pumping  # electricty to run the motor

    x = [0.4999, 0.75, 1.1, 1.5, 2.2, 3, 4, 5.5, 7.5, 11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200, 220,
         260, 315, 335, 375]  # Nominal load in kW
    y = [630, 580, 500, 420, 350, 315, 285, 260, 240, 220, 210, 205, 195, 190, 185, 182, 180, 176, 175, 174, 173, 170,
         169, 168, 167, 165, 162, 161.9]  # efficiency in %
    # do the interpolation
    x1 = [0.4999, 0.75, 1.1, 1.5, 2.2, 3, 4, 5.5, 7.5, 11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200,
          220, 260, 315, 335, 375]  # Nominal load in kW
    y1 = [720, 680, 585, 425, 330, 275, 220, 195, 180, 150, 145, 143, 135, 120, 115, 114, 110, 100, 90, 88, 85, 80, 75,
          74, 74, 73, 72, 71.9]  # efficiency in %
    InvC_mot = interp1d(x, y, kind='cubic')
    InvC_VFC = interp1d(x1, y1, kind='cubic')

    Pump_max_kW = 375.0
    Pump_min_kW = 0.5
    nPumps = int(np.ceil(P_motor_tot_W / 1000.0 / Pump_max_kW))
    # if the nominal load (electric) > 375kW, a new pump is installed
    Pump_Array_W = np.zeros((nPumps))
    Pump_Remain_W = P_motor_tot_W

    # if PpumpRemain < PpumpMinkW * 1000:
    #   PpumpRemain = PpumpMinkW * 1000

    Capex_a_pump_USD = 0.0
    Opex_fixed_pump_USD = 0.0
    Capex_pump_USD = 0.0

    for pump_i in range(nPumps):
        # calculate pump nominal capacity
        Pump_Array_W[pump_i] = min(Pump_Remain_W, Pump_max_kW * 1000)
        if Pump_Array_W[pump_i] < Pump_min_kW * 1000:
            Pump_Array_W[pump_i] = Pump_min_kW * 1000
        Pump_Remain_W -= Pump_Array_W[pump_i]

        pump_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="Pump")
        pump_cost_data = pump_cost_data[pump_cost_data['code'] == technology_type]
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
        Inv_IR = (pump_cost_data.iloc[0]['IR_%']) / 100
        Inv_LT = pump_cost_data.iloc[0]['LT_yr']
        Inv_OM = pump_cost_data.iloc[0]['O&M_%'] / 100

        InvC = Inv_a + Inv_b * (Pump_Array_W[pump_i]) ** Inv_c + (Inv_d + Inv_e * Pump_Array_W[pump_i]) * log(Pump_Array_W[pump_i])

        Capex_a_pump_USD += InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
        Opex_fixed_pump_USD += Capex_a_pump_USD * Inv_OM
        Capex_pump_USD += InvC


    return Capex_a_pump_USD, Opex_fixed_pump_USD, Capex_pump_USD



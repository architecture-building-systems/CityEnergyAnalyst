# -*- coding: utf-8 -*-
"""
condensing boilers
"""


from __future__ import division
from scipy.interpolate import interp1d
from math import log
import pandas as pd
from cea.optimization.constants import *


__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

#operation costs

def cond_boiler_operation(Q_load_W, Q_design_W, T_return_to_boiler_K):

    """
    This function calculates efficiency for operation of condensing Boilers at DH plant based on LHV.
    This efficiency accounts for boiler efficiency only (not plant efficiency!)

    operational efficiency after:
        http://www.greenshootscontrols.net/?p=153

    :param Q_load_W: Load of time step
    :type Q_load_W: float

    :type Q_design_W: float
    :param Q_design_W: Design Load of Boiler

    :type T_return_to_boiler_K : float
    :param T_return_to_boiler_K: Return Temperature of the network to the boiler [K]

    :retype boiler_eff: float
    :returns boiler_eff: efficiency of Boiler (Lower Heating Value), in abs. numbers

    _[T. Vollrath, 2016] Tim Vollrath. Microgrid Modelling and Optimisation in the Context of Rural Transformation.
    Master Thesis, ETH Zurich. 2016.
    """

    x = [0, 15.5, 21, 26.7, 32.2, 37.7, 43.3, 49, 54.4, 60, 65.6, 71.1, 100] # Return Temperature Dependency
    y = [96.8, 96.8, 96.2, 95.5, 94.7, 93.2, 91.2, 88.9, 87.3, 86.3, 86.0, 85.9, 85.8] # Return Temperature Dependency
    x1 = [0, 0.05, 0.25, 0.5, 0.75, 1] # Load Point dependency
    y1 = [99.5, 99.3, 98.3, 97.6, 97.1, 96.8] # Load Point Dependency

    # do the interpolation
    eff_of_T_return = interp1d(x, y, kind='linear')
    eff_of_phi = interp1d(x1, y1, kind='cubic')

    # get input variables
    if Q_design_W > 0:
        phi = float(Q_load_W) / float(Q_design_W)
    else:
        phi = 0

    if T_return_to_boiler_K == 0: # accounting with times with no flow
        T_return = 0
    else:
        T_return = T_return_to_boiler_K - 273
    eff_score = eff_of_phi(phi) / eff_of_phi(1)
    boiler_eff = (eff_score * eff_of_T_return(T_return) )/ 100.0

    return boiler_eff


def cond_boiler_op_cost(Q_therm_W, Q_design_W, T_return_to_boiler_K, BoilerFuelType, ElectricityType, gV, prices):
    """
    Calculates the operation cost of a Condensing Boiler (only operation, not annualized cost)

    :type Q_therm_W : float
    :param Q_therm_W: Load of time step

    :type Q_design_W: float
    :param Q_design_W: Design Load of Boiler

    :type T_return_to_boiler_K : float
    :param T_return_to_boiler_K: return temperature to Boiler (from DH network)

    :param gV: globalvar.py

    :rtype C_boil_therm : float
    :returns C_boil_therm: Total generation cost for required load (per hour) in CHF

    :rtype C_boil_per_Wh : float
    :returns C_boil_per_Wh: cost per Wh in CHF / kWh

    :rtype Q_primary : float
    :returns Q_primary: required thermal energy per hour (in Wh Natural Gas)

    :rtype E_aux_Boiler: float
    :returns E_aux_Boiler: auxiliary electricity of boiler operation
    """

    # boiler efficiency
    eta_boiler = cond_boiler_operation(Q_therm_W, Q_design_W, T_return_to_boiler_K)


    if BoilerFuelType == 'BG':
        GAS_PRICE = prices.BG_PRICE
    else:
        GAS_PRICE = prices.NG_PRICE

    if ElectricityType == 'green':
        ELEC_PRICE = gV.ELEC_PRICE_GREEN
    else:
        ELEC_PRICE = prices.ELEC_PRICE

    C_boil_therm = Q_therm_W / eta_boiler * GAS_PRICE + (Boiler_P_aux * ELEC_PRICE) * Q_therm_W #  CHF / Wh - cost of thermal energy
    C_boil_per_Wh = 1/ eta_boiler * GAS_PRICE + Boiler_P_aux* ELEC_PRICE
    E_aux_Boiler_req_W = Boiler_P_aux * Q_therm_W

    Q_primary_W = Q_therm_W / eta_boiler

    return C_boil_therm, C_boil_per_Wh, Q_primary_W, E_aux_Boiler_req_W


def calc_Cop_boiler(Q_load_W, Q_design_W, T_return_to_boiler_K):

    """
    This function calculates efficiency for operation of condensing Boilers based on LHV.
    This efficiency accounts for boiler efficiency only (not plant efficiency!)

    operational efficiency after:
        http://www.greenshootscontrols.net/?p=153


    :param Q_load_W: Load of time step
    :type Q_load_W: float

    :type Q_design_W: float
    :param Q_design_W: Design Load of Boiler

    :type T_return_to_boiler_K : float
    :param T_return_to_boiler_K: Return Temperature of the network to the boiler [K]


    :retype boiler_eff: float
    :returns boiler_eff: efficiency of Boiler (Lower Heating Value), in abs. numbers
    """

    #Implement Curves provided by http://www.greenshootscontrols.net/?p=153
    x = [0, 15.5, 21, 26.7, 32.2, 37.7, 43.3, 49, 54.4, 60, 65.6, 71.1, 100] # Return Temperature Dependency
    y = [96.8, 96.8, 96.2, 95.5, 94.7, 93.2, 91.2, 88.9, 87.3, 86.3, 86.0, 85.9, 85.8] # Return Temperature Dependency
    x1 = [0.0, 0.05, 0.25, 0.5, 0.75, 1.0] # Load Point dependency
    y1 = [100.0, 99.3, 98.3, 97.6, 97.1, 96.8] # Load Point Dependency

     # do the interpolation
    eff_of_T_return = interp1d(x, y, kind='linear')
    eff_of_phi = interp1d(x1, y1, kind='cubic')

    # get input variables
    if Q_design_W > 0:
        phi = float(Q_load_W) / float(Q_design_W)

    else:
        phi = 0

    T_return_C = T_return_to_boiler_K - 273
    eff_score = eff_of_phi(phi) / eff_of_phi(1)
    boiler_eff = (eff_score * eff_of_T_return(T_return_C) )/ 100.0

    return boiler_eff

# investment and maintenance costs

def calc_Cinv_boiler(Q_design_W, Q_annual_W, locator, config, technology=0):
    """
    Calculates the annual cost of a boiler (based on A+W cost of oil boilers) [CHF / a]
    and Faz. 2012 data

    :type Q_design_W : float
    :param Q_design_W: Design Load of Boiler in [W]

    :type Q_annual_W : float
    :param Q_annual_W: Annual thermal load required from Boiler in [Wh]

    :param gV: globalvar.py

    :rtype InvCa : float
    :returns InvCa: Annualized investment costs in CHF/a including Maintenance Cost
    """

    if Q_design_W >0:

        boiler_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="Boiler")
        technology_code = list(set(boiler_cost_data['code']))
        boiler_cost_data[boiler_cost_data['code'] == technology_code[technology]]
        # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
        # capacity for the corresponding technology from the database
        if Q_design_W < boiler_cost_data['cap_min'][0]:
            Q_design_W = boiler_cost_data['cap_min'][0]
        boiler_cost_data = boiler_cost_data[(boiler_cost_data['cap_min'] <= Q_design_W) & (boiler_cost_data['cap_max'] > Q_design_W)]

        Inv_a = boiler_cost_data.iloc[0]['a']
        Inv_b = boiler_cost_data.iloc[0]['b']
        Inv_c = boiler_cost_data.iloc[0]['c']
        Inv_d = boiler_cost_data.iloc[0]['d']
        Inv_e = boiler_cost_data.iloc[0]['e']
        Inv_IR = (boiler_cost_data.iloc[0]['IR_%']) / 100
        Inv_LT = boiler_cost_data.iloc[0]['LT_yr']
        Inv_OM = boiler_cost_data.iloc[0]['O&M_%'] / 100

        InvC = Inv_a + Inv_b * (Q_design_W) ** Inv_c + (Inv_d + Inv_e * Q_design_W) * log(Q_design_W)

        Capex_a =  InvC * (Inv_IR) * (1+ Inv_IR) ** Inv_LT / ((1+Inv_IR) ** Inv_LT - 1)
        Opex_fixed = Capex_a * Inv_OM

    else:
        Capex_a = 0
        Opex_fixed = 0

    return Capex_a, Opex_fixed


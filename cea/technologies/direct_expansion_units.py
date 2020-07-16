# -*- coding: utf-8 -*-
"""
direct expansion units
"""

from __future__ import division

import numpy as np
import pandas as pd
import time
import math

from cea.analysis.costs.equations import calc_capex_annualized
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.utilities.physics import kelvin_to_fahrenheit

__author__ = "Shanshan Hsieh"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# FIXME: this model is simplified, and required update
PRICE_DX_PER_W = 1.6  # USD FIXME: to be moved to database

# operation costs
def calc_DX_q(mdot_kgpers, T_sup_K, T_re_K):
    if np.isclose(mdot_kgpers, 0.0):
        q_chw_W = 0.0
    else:
        q_chw_W = mdot_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK * (T_re_K - T_sup_K)

    return q_chw_W

def calc_DX_el(q_DX_chw_Wh, T_odb_K, T_re_AHU_ARU_SCU_K, n_households, n_units_per_HH, rated_capacity_per_unit, cop_rated, DX_configuration_values):

    cop_DX = calc_cop_DX(q_DX_chw_Wh, T_odb_K, T_re_AHU_ARU_SCU_K, n_households, n_units_per_HH, rated_capacity_per_unit,cop_rated, DX_configuration_values)

    wdot_W = q_DX_chw_Wh / cop_DX

    return 0 if math.isnan(wdot_W) else wdot_W

def calc_cop_DX(q_DX_chw_Wh, T_odb_K, T_re_AHU_ARU_SCU_K, n_households, n_units_per_HH, rated_capacity_per_unit, cop_rated, DX_configuration_values):
    """
    Calculates the COP adjusting for part load efficiency and temperature.
    :param float q_DX_chw_Wh: in W
    :param float T_odb_K: outdoor air dry-bulb temperature
    :param float T_re_AHU_ARU_SCU_K: return temperature from the AHU temperature
    :param integer n_households: number of households, fed by DX
    :param integer n_units_per_HH: number of DX units per household
    :param float rated_capacity_per_unit: in kW
    :param float cop_rated: rated COP of the DX units
    :param dictionary DX_configuration_values: dictionary containing config information
    :return float cop_DX: adjusted COP for a specific hour
    """
    q_DX_chw_kWh_per_HH = q_DX_chw_Wh / n_households /1000
    CAP_FT, EIR_FT = calculate_FT(T_odb_K, T_re_AHU_ARU_SCU_K, DX_configuration_values)
    available_capacity_per_unit = rated_capacity_per_unit * CAP_FT
    EIR_FPLR = average_EIR_FPLR(q_DX_chw_kWh_per_HH, available_capacity_per_unit, n_units_per_HH,  DX_configuration_values)

    capacity_per_HH = rated_capacity_per_unit*n_units_per_HH
    P_rated = capacity_per_HH/cop_rated
    P_operating = P_rated * CAP_FT * EIR_FT * EIR_FPLR

    cop_DX = q_DX_chw_kWh_per_HH / P_operating

    return cop_DX

def direct_expansion_design(Q_rated_kW_per_HH, DX_properties):
    """
    Creates a general DX setup according to industry knowledge with a certain amount of equally-sized DX units per household.
     (Source: https://comnet.org/index.php/375-cooling-systems)
    Depending on the design capacity, different DX types are employed to increase the overall COP.
    All DX are air source.
    :param float Q_rated_kW_per_HH: rated design capacity in kW
    :param DirectExpansionUnit DX_properties:  object containing scale, capacity and config properties
    :return dictionary DX_properties: dictionary with config information
    :return integer n_units: number of equally sized DX units
    :return float rated_capacity_per_unit: size of equally sized DX units
    :return float cop_rated: rated COP of the DX units
    """
    source_type = 'AIR'
    SINGLE_max_cap = DX_properties.get_max_capacity(source_type, 'SINGLE')
    SPLIT_max_cap = DX_properties.get_max_capacity(source_type, 'SPLIT')

    if Q_rated_kW_per_HH <= SINGLE_max_cap/2:
        DX_type = 'SINGLE'
        n_units = 1
        rated_capacity_per_unit = Q_rated_kW_per_HH/n_units
        cop_rated = DX_properties.get_COP(source_type, DX_type, rated_capacity_per_unit)
        DX_configuration_values = DX_properties.configuration_values(source_type, DX_type, rated_capacity_per_unit)
    elif SINGLE_max_cap/2 < Q_rated_kW_per_HH <= SINGLE_max_cap :
        DX_type = 'SPLIT'
        n_units = 2
        rated_capacity_per_unit = Q_rated_kW_per_HH/n_units
        cop_rated = DX_properties.get_COP(source_type, DX_type, rated_capacity_per_unit)
        DX_configuration_values = DX_properties.configuration_values(source_type, DX_type, rated_capacity_per_unit)
    elif SINGLE_max_cap < Q_rated_kW_per_HH <= SPLIT_max_cap:
        DX_type = 'SPLIT'
        n_units = max(2, Q_rated_kW_per_HH/SPLIT_max_cap)
        rated_capacity_per_unit = Q_rated_kW_per_HH/n_units
        cop_rated = DX_properties.get_COP(source_type, DX_type, rated_capacity_per_unit)
        DX_configuration_values = DX_properties.configuration_values(source_type, DX_type, rated_capacity_per_unit)

    return DX_configuration_values, n_units, rated_capacity_per_unit, cop_rated

def calculate_FT(T_odb_K, T_re_AHU_ARU_SCU_K, DX_configuration_values):
    """
    calculates the DX Cooling Capacity Adjustment Curve
    for both 'cooling capacity function of temperature curve' (CAP_FT)
    and 'electric input to cooling output factor for temperature function curve'(EIR_FT)
    coefficients taken from  https://comnet.org/index.php/375-cooling-systems
    :param float T_odb_K: outdoor air dry-bulb temperature
    :param float T_re_AHU_ARU_SCU_K: return temperature from the AHU temperature
    :param dictionary DX_configuration_values: dictionary containing config values
    :return float CAP_FT: cooling capacity function of temperature curve
    :return float EIR_FT: electric input to cooling output factor for temperature function curve
    """
    t_wb = kelvin_to_fahrenheit(T_re_AHU_ARU_SCU_K)
    t_odb = kelvin_to_fahrenheit(T_odb_K)
    Cap_fts = DX_configuration_values['Cap_fts']
    CAP_FT = Cap_fts['cap_ft_a'] + Cap_fts['cap_ft_b'] * t_wb + Cap_fts['cap_ft_c'] * t_wb**2 + Cap_fts['cap_ft_d'] * t_odb +\
             Cap_fts['cap_ft_e'] * t_odb**2 + Cap_fts['cap_ft_f'] * t_wb * t_odb
    EIR_FTs = DX_configuration_values['Eir_fts']
    EIR_FT = EIR_FTs['eir_ft_a'] + EIR_FTs['eir_ft_b'] * t_wb + EIR_FTs['eir_ft_c'] * t_wb**2 + EIR_FTs['eir_ft_d'] * t_odb +\
             EIR_FTs['eir_ft_e'] * t_odb**2 + EIR_FTs['eir_ft_f'] * t_wb * t_odb
    return CAP_FT, EIR_FT

def average_EIR_FPLR(q_DX_chw_kWh_per_HH, available_capacity_per_unit, n_units_per_HH,  DX_configuration_values):
    """
    Calculates the part load factor of installed DX setup for a given cooling load.
    Includes the design of the DX based on peak load and chiller plant scale to define the part load ratio.
    :param float q_DX_chw_kWh_per_HH: in kW
    :param float available_capacity_per_unit: in W
    :param float n_units_per_HH: number of DX per Household
    :param dictionary DX_configuration_values: contains config details
    :return float EIR_FPLR:  electric input to cooling output factor for part-load function curve
    """
    Q_operating = q_DX_chw_kWh_per_HH
    Q_available = available_capacity_per_unit * n_units_per_HH
    PLR = Q_operating/Q_available

    EIR_FPLR = calc_EIR_FPLR(PLR, DX_configuration_values['PLFs'])  # calculates the average PLF value EIR_FPLR
    return EIR_FPLR

def calc_EIR_FPLR(PLR, PLFs):
    """
    Electric Chiller Cooling Efficiency Adjustment Curves
    coefficients taken from https://comnet.org/index.php/375-cooling-systems
    :param np.array PLR: part load ratio
    :param np.array PLFs: part load factor coefficients
    :return np.array EIR_FPLR: part load factor
    """
    EIR_FPLR = PLFs['plf_a'] + PLFs['plf_b'] * PLR + PLFs['plf_c'] * PLR**2 + PLFs['plf_d'] * PLR**3

    return EIR_FPLR

# investment and maintenance costs

def calc_Cinv_DX(Q_design_W):
    """
    Assume the same cost as gas boilers.
    :type Q_design_W : float
    :param Q_design_W: Design Load of Boiler in [W]
    :rtype InvCa : float
    :returns InvCa: Annualized investment costs in CHF/a including Maintenance Cost
    """
    Capex_a_DX_USD = 0
    Opex_fixed_DX_USD = 0
    Capex_DX_USD = 0

    if Q_design_W > 0:
        InvC = Q_design_W * PRICE_DX_PER_W
        Inv_IR = 5
        Inv_LT = 25
        Inv_OM = 5 / 100

        Capex_a_DX_USD = calc_capex_annualized(InvC, Inv_IR, Inv_LT)
        Opex_fixed_DX_USD = InvC * Inv_OM
        Capex_DX_USD = InvC

    return Capex_a_DX_USD, Opex_fixed_DX_USD, Capex_DX_USD


class DirectExpansionUnit(object):
    __slots__ = ["locator", "DX_database"]

    def __init__(self, locator):
        self.locator = locator
        self.DX_database = None
        self.setup()

    def setup(self):
        self.DX_database = pd.read_excel(self.locator.get_database_conversion_systems(), sheet_name="DX")

    def get_COP(self, source_type, DX_type, capacity):
        df = self.DX_database
        df = df[(df['SOURCE'] == source_type) & (df['TYPE'] == DX_type)\
                & (df['MIN CAPACITY [kW]'] <= capacity) & (capacity < df['MAX CAPACITY [kW]'])]
        rated_cop = float(df['COP'])
        return rated_cop

    def get_max_capacity(self, source_type, DX_type):
        df = self.DX_database
        df = df[(df['SOURCE'] == source_type) & (df['TYPE'] == DX_type)]
        max_capacity = float(df['MAX CAPACITY [kW]'].max())
        return max_capacity

    def configuration_values(self, source_type, DX_type, capacity):
        df = self.DX_database
        df = df[(df['SOURCE'] == source_type) & (df['TYPE'] == DX_type)\
                & (df['MIN CAPACITY [kW]'] <= capacity) & (capacity < df['MAX CAPACITY [kW]'])]

        filter_plfs = [col for col in df if col.startswith('plf')]
        filter_eir_ft = [col for col in df if col.startswith('eir_ft')]
        filter_cap_ft = [col for col in df if col.startswith('cap_ft')]

        plfs = df[filter_plfs].to_dict('records')[0]
        eir_fts = df[filter_eir_ft].to_dict('records')[0]
        cap_fts = df[filter_cap_ft].to_dict('records')[0]

        return {'PLFs': plfs, 'Eir_fts': eir_fts, 'Cap_fts' : cap_fts}
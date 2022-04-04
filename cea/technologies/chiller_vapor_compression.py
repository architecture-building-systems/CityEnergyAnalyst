"""
Vapor-compressor chiller
"""

import pandas as pd
from math import log, ceil
import numpy as np

from cea.technologies.constants import G_VALUE_CENTRALIZED, G_VALUE_DECENTRALIZED, CHILLER_DELTA_T_HEX_CT, \
    CHILLER_DELTA_T_APPROACH, T_EVAP_AHU, T_EVAP_ARU, T_EVAP_SCU, DT_NETWORK_CENTRALIZED, CENTRALIZED_AUX_PERCENTAGE, \
    DECENTRALIZED_AUX_PERCENTAGE, COMPRESSOR_TYPE_LIMIT_LOW, COMPRESSOR_TYPE_LIMIT_HIGH, ASHRAE_CAPACITY_LIMIT

from cea.optimization.constants import VCC_CODE_CENTRALIZED, VCC_CODE_DECENTRALIZED
from cea.analysis.costs.equations import calc_capex_annualized, calc_opex_annualized
from cea.utilities.physics import kelvin_to_fahrenheit

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# technical model
def calc_VCC(peak_cooling_load, q_chw_load_Wh, T_chw_sup_K, T_chw_re_K, T_cw_in_K, VC_chiller):
    """
    For the operation of a Vapor-compressor chiller between a district cooling network and a condenser with fresh water
    to a cooling tower following [D.J. Swider, 2003]_.
    The physically based fundamental thermodynamic model(LR4) is implemented in this function.
    :type mdot_kgpers : float
    :param mdot_kgpers: plant supply mass flow rate to the district cooling network
    :type T_chw_sup_K : float
    :param T_chw_sup_K: plant supply temperature to DCN
    :type T_chw_re_K : float
    :param T_chw_re_K: plant return temperature from DCN
    :rtype Q_VCC_unit_size_W : float
    :returns Q_VCC_unit_size_W: chiller installed capacity
    ..[D.J. Swider, 2003] D.J. Swider (2003). A comparison of empirically based steady-state models for
    vapor-compression liquid chillers. Applied Thermal Engineering.
    """

    if q_chw_load_Wh == 0.0:
        wdot_W = 0.0
        q_cw_W = 0.0

    elif q_chw_load_Wh > 0.0:
        COP = calc_COP_with_carnot_efficiency(peak_cooling_load, q_chw_load_Wh, T_chw_sup_K, T_cw_in_K, VC_chiller)
        if COP < 0.0:
            print(f'Negative COP: {COP} {T_chw_sup_K} {T_chw_re_K} {q_chw_load_Wh}', )

        # calculate chiller outputs
        # print('COP is: ', COP)
        wdot_W = q_chw_load_Wh / COP
        q_cw_W = wdot_W + q_chw_load_Wh  # heat rejected to the cold water (cw) loop
    else:
        raise ValueError('negative cooling load to VCC: ', q_chw_load_Wh)

    chiller_operation = {'wdot_W': wdot_W, 'q_cw_W': q_cw_W, 'q_chw_W': q_chw_load_Wh}

    return chiller_operation


def calc_COP(T_cw_in_K, T_chw_re_K, q_chw_load_Wh):
    A = 0.0201E-3 * q_chw_load_Wh / T_cw_in_K
    B = T_chw_re_K / T_cw_in_K
    C = 0.1980E3 * T_chw_re_K / q_chw_load_Wh + 168.1846E3 * (T_cw_in_K - T_chw_re_K) / (T_cw_in_K * q_chw_load_Wh)
    COP = 1 / ((1 + C) / (B - A) - 1)
    return COP


def calc_COP_with_carnot_efficiency(peak_cooling_load, q_chw_load_Wh, T_chw_sup_K, T_cw_in_K, VCC_chiller):
    PLF = calc_averaged_PLF(peak_cooling_load, q_chw_load_Wh, T_chw_sup_K, T_cw_in_K,
                            VCC_chiller)  # calculates the weighted average Part load factor across all chillers based on load distribution
    cop_chiller = VCC_chiller.g_value * T_chw_sup_K / (T_cw_in_K - T_chw_sup_K) * PLF
    return cop_chiller


# Investment costs
def calc_Cinv_VCC(Q_nom_W, locator, technology_type):
    """
    Annualized investment costs for the vapor compressor chiller

    :type Q_nom_W : float
    :param Q_nom_W: Nominal cooling demand in [W]

    :returns InvCa: annualized chiller investment cost in CHF/a
    :rtype InvCa: float

    """
    Capex_a_VCC_USD = 0
    Opex_fixed_VCC_USD = 0
    Capex_VCC_USD = 0

    if Q_nom_W > 0:
        VCC_cost_data = pd.read_excel(locator.get_database_conversion_systems(), sheet_name="Chiller")
        VCC_cost_data = VCC_cost_data[VCC_cost_data['code'] == technology_type]
        max_chiller_size = max(VCC_cost_data['cap_max'].values)
        # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
        # capacity for the corresponding technology from the database
        if Q_nom_W < VCC_cost_data.iloc[0]['cap_min']:
            Q_nom_W = VCC_cost_data.iloc[0]['cap_min']
        if Q_nom_W <= max_chiller_size:
            VCC_cost_data = VCC_cost_data[(VCC_cost_data['cap_min'] <= Q_nom_W) & (VCC_cost_data['cap_max'] >= Q_nom_W)]
            Inv_a = VCC_cost_data.iloc[0]['a']
            Inv_b = VCC_cost_data.iloc[0]['b']
            Inv_c = VCC_cost_data.iloc[0]['c']
            Inv_d = VCC_cost_data.iloc[0]['d']
            Inv_e = VCC_cost_data.iloc[0]['e']
            Inv_IR = VCC_cost_data.iloc[0]['IR_%']
            Inv_LT = VCC_cost_data.iloc[0]['LT_yr']
            Inv_OM = VCC_cost_data.iloc[0]['O&M_%'] / 100
            InvC = Inv_a + Inv_b * (Q_nom_W) ** Inv_c + (Inv_d + Inv_e * Q_nom_W) * log(Q_nom_W)
            Capex_a_VCC_USD = calc_capex_annualized(InvC, Inv_IR, Inv_LT)
            Opex_fixed_VCC_USD = InvC * Inv_OM
            Capex_VCC_USD = InvC
        else:  # more than one unit of ACH are activated
            number_of_chillers = int(ceil(Q_nom_W / max_chiller_size))
            Q_nom_each_chiller = Q_nom_W / number_of_chillers
            for i in range(number_of_chillers):
                VCC_cost_data = VCC_cost_data[
                    (VCC_cost_data['cap_min'] <= Q_nom_each_chiller) & (VCC_cost_data['cap_max'] >= Q_nom_each_chiller)]
                Inv_a = VCC_cost_data.iloc[0]['a']
                Inv_b = VCC_cost_data.iloc[0]['b']
                Inv_c = VCC_cost_data.iloc[0]['c']
                Inv_d = VCC_cost_data.iloc[0]['d']
                Inv_e = VCC_cost_data.iloc[0]['e']
                Inv_IR = VCC_cost_data.iloc[0]['IR_%']
                Inv_LT = VCC_cost_data.iloc[0]['LT_yr']
                Inv_OM = VCC_cost_data.iloc[0]['O&M_%'] / 100
                InvC = Inv_a + Inv_b * (Q_nom_each_chiller) ** Inv_c + (Inv_d + Inv_e * Q_nom_each_chiller) * log(
                    Q_nom_each_chiller)
                Capex_a1 = calc_capex_annualized(InvC, Inv_IR, Inv_LT)
                Capex_a_VCC_USD = Capex_a_VCC_USD + Capex_a1
                Opex_fixed_VCC_USD = Opex_fixed_VCC_USD + InvC * Inv_OM
                Capex_VCC_USD = Capex_VCC_USD + InvC

    return Capex_a_VCC_USD, Opex_fixed_VCC_USD, Capex_VCC_USD


def calc_VCC_COP(weather_data, load_types, centralized=True):
    """
    Calculates the VCC COP based on evaporator and compressor temperatures, VCC g-value, and an assumption of
    auxiliary power demand for centralized and decentralized systems.
    This approximation only works in tropical climates

    Clark D (CUNDALL). Chiller energy efficiency 2013.

    :param load_types: a list containing the systems (aru, ahu, scu) that the chiller is supplying for
    :param centralized:
    :return:
    """
    if centralized == True:
        g_value = G_VALUE_CENTRALIZED
    else:
        g_value = G_VALUE_DECENTRALIZED
    T_evap_K = 10000000  # some high enough value
    for load_type in load_types:  # find minimum evap temperature of supplied loads
        if load_type == 'ahu':
            T_evap_K = min(T_evap_K, T_EVAP_AHU)
        elif load_type == 'aru':
            T_evap_K = min(T_evap_K, T_EVAP_ARU)
        elif load_type == 'scu':
            T_evap_K = min(T_evap_K, T_EVAP_SCU)
        else:
            print('Undefined cooling load_type for chiller COP calculation.')
    if centralized == True:  # Todo: improve this to a better approximation than a static value DT_Network
        # for the centralized case we have to supply somewhat colder, currently based on CEA calculation for MIX_m case
        T_evap_K = T_evap_K - DT_NETWORK_CENTRALIZED
    # calculate condenser temperature with static approach temperature assumptions # FIXME: only work for tropical climates
    T_cond_K = np.mean(weather_data['wetbulb_C']) + CHILLER_DELTA_T_APPROACH + CHILLER_DELTA_T_HEX_CT + 273.15
    # calculate chiller COP
    cop_chiller = g_value * T_evap_K / (T_cond_K - T_evap_K)
    # calculate system COP with pumping power of auxiliaries
    if centralized == True:
        cop_system = 1 / (1 / cop_chiller * (1 + CENTRALIZED_AUX_PERCENTAGE / 100))
    else:
        cop_system = 1 / (1 / cop_chiller * (1 + DECENTRALIZED_AUX_PERCENTAGE / 100))

    return cop_system, cop_chiller


def get_max_VCC_unit_size(locator, VCC_code='CH3'):
    VCC_cost_data = pd.read_excel(locator.get_database_conversion_systems(), sheet_name="Chiller")
    VCC_cost_data = VCC_cost_data[VCC_cost_data['code'] == VCC_code]
    max_VCC_unit_size_W = max(VCC_cost_data['cap_max'].values)
    return max_VCC_unit_size_W


def calc_averaged_PLF(peak_cooling_load, q_chw_load_Wh, T_chw_sup_K, T_cw_in_K, VCC_chiller):
    """
    Calculates the part load factor of installed Vapor compression chillers for a given cooling load.
    Includes the design of the chillers based on peak load and chiller plant scale to define the part load ratio.
    :param float peak_cooling_load: in W
    :param float q_chw_load_Wh: in W
    :param float T_chw_sup_K: in Kelvin
    :param float T_cw_in_K: in Kelvin
    :param VaporCompressionChiller VCC_chiller: VCC_chiller object containing scale, capacity and config properties
    :param str scale: either "BUILDING" or "DISTRICT"
    :return float averaged_PLF: averaged part load factor over all chillers [0..1]
    """
    design_capacity = peak_cooling_load  # * 1.15 # for future implementation, a safety factor could be introduced. As of now this would be in conflict with the master_to_slave_variables.WS_BaseVCC_size_W
    if VCC_chiller.scale == 'BUILDING':
        if design_capacity <= COMPRESSOR_TYPE_LIMIT_LOW:  # according to ASHRAE 90.1 Appendix G: if design cooling load smaller than lower limit, implement one screw chiller
            source_type = 'WATER'
            compressor_type = 'SCREW'
            ch_configuration_values = VCC_chiller.configuration_values(source_type, compressor_type)
            n_units = 1
        elif COMPRESSOR_TYPE_LIMIT_LOW < design_capacity < COMPRESSOR_TYPE_LIMIT_HIGH:  # according to ASHRAE 90.1 Appendix G: if design cooling load between limits, implement two screw chillers
            source_type = 'WATER'
            compressor_type = 'SCREW'
            ch_configuration_values = VCC_chiller.configuration_values(source_type, compressor_type)
            n_units = 2
        elif design_capacity >= COMPRESSOR_TYPE_LIMIT_HIGH:  # according to ASHRAE 90.1 Appendix G: if design cooling load larger than upper limit, implement centrifugal chillers
            source_type = 'WATER'
            compressor_type = 'CENTRIFUGAL'
            ch_configuration_values = VCC_chiller.configuration_values(source_type, compressor_type)
            n_units = ceil(
                design_capacity / ASHRAE_CAPACITY_LIMIT)  # according to ASHRAE 90.1 Appendix G, chiller shall not be large then 800 tons (2813 kW)
        else:
            raise ValueError('Unable to assign chiller type based on design capacity')
        cooling_capacity_per_unit = design_capacity / n_units  # calculate the capacity per chiller installed

    elif VCC_chiller.scale == 'DISTRICT':
        source_type = 'WATER'
        compressor_type = 'CENTRIFUGAL'
        ch_configuration_values = VCC_chiller.configuration_values(source_type, compressor_type)
        if design_capacity <= (2 * VCC_chiller.min_VCC_capacity):  # design one chiller for small scale DCS
            n_units = 1
            cooling_capacity_per_unit = max(design_capacity, VCC_chiller.min_VCC_capacity)
        elif (
                2 * VCC_chiller.min_VCC_capacity) <= design_capacity <= VCC_chiller.max_VCC_capacity:  # design two chillers above the twice the minimum chiller size
            n_units = 2
            cooling_capacity_per_unit = design_capacity / n_units
        elif design_capacity >= VCC_chiller.max_VCC_capacity:  # design a minimum of 2 chillers if above the maximum chiller size
            n_units = max(2, ceil(
                design_capacity / VCC_chiller.max_VCC_capacity))  # have minimum size of capacity to quailfy as DCS, have minimum of 2 chillers
            cooling_capacity_per_unit = design_capacity / n_units
        else:
            raise ValueError('Unable to assign chiller type based on design capacity')
    else:
        raise ValueError('VCC_chiller scale can only be "BUILDING" or "DISTRICT" got: {scale}'.format(
            scale=VCC_chiller.scale))

    available_capacity_per_unit = calc_available_capacity(cooling_capacity_per_unit, ch_configuration_values['Qs'],
                                                          T_chw_sup_K,
                                                          T_cw_in_K)  # calculate the available capacity(dependent on conditions)

    # calculate the load distribution across the chillers heuristically,
    # assuming the PLF factor is monotonously increasing with increasing PLR. Filling one chiller after the other.
    n_chillers_filled = int(q_chw_load_Wh // available_capacity_per_unit)
    part_load_chiller = float(divmod(q_chw_load_Wh, available_capacity_per_unit)[1]) / float(
        available_capacity_per_unit)

    load_distribution_list = []
    for i in range(n_chillers_filled):
        load_distribution_list.append(1)
    load_distribution_list.append(part_load_chiller)
    for i in range(int(n_units) - n_chillers_filled - 1):
        load_distribution_list.append(0)
    load_distribution = np.array(load_distribution_list)

    averaged_PLF = np.sum(calc_PLF(load_distribution, ch_configuration_values[
        'PLFs']) * load_distribution * available_capacity_per_unit) / q_chw_load_Wh  # calculates the weighted average PLF value
    return averaged_PLF


def calc_PLF(PLR, PLFs):
    """
    takes the part load ratio as an input and outputs the part load factor
    coefficients taken from https://comnet.org/index.php/382-chillers and only includes water source electrical chillers
    :param np.array PLR: part load ratio for each chiller
    :return np.array PLF: part load factor for each chiller
    """
    PLF = PLFs['plf_a'] + PLFs['plf_b'] * PLR + PLFs['plf_c'] * PLR ** 2
    return PLF


def calc_available_capacity(rated_capacity, Qs, T_chw_sup_K, T_cw_in_K):
    """
    calculates the available Chiller capacity based on the rated capacity
    coefficients taken from https://comnet.org/index.php/382-chillers
    :param float rated_capacity: rated capacity of chiller
    :param float T_chw_sup_K: supplied chilled water temperature in Kelvin
    :param float T_cw_in_K: condenser water supply temperature in Kelvin
    :return np.array PLF: part load factor for each chiller
    """
    t_chws_F = kelvin_to_fahrenheit(T_chw_sup_K)
    t_cws_F = kelvin_to_fahrenheit(T_cw_in_K)

    available_capacity = rated_capacity * (
                Qs['q_a'] + Qs['q_b'] * t_chws_F + Qs['q_c'] * t_chws_F ** 2 + Qs['q_d'] * t_cws_F + Qs[
            'q_e'] * t_cws_F ** 2 + Qs['q_f'] * t_chws_F * t_cws_F)
    return available_capacity


class VaporCompressionChiller(object):
    __slots__ = ["max_VCC_capacity", "min_VCC_capacity", "g_value", "scale", "locator", "chiller_configuration"]

    def __init__(self, locator, scale):
        self.max_VCC_capacity = 0
        self.min_VCC_capacity = 0
        self.g_value = 0.0
        self.scale = scale
        self.locator = locator
        self.chiller_configuration = None
        self.setup()

    def setup(self):
        VCC_database = pd.read_excel(self.locator.get_database_conversion_systems(), sheet_name="Chiller")
        if self.scale == 'DISTRICT':
            technology_type = VCC_CODE_CENTRALIZED
        elif self.scale == 'BUILDING':
            technology_type = VCC_CODE_DECENTRALIZED
        else:
            raise ValueError('scale must be of type "DISTRICT" or "BUILDING"')

        VCC_database = VCC_database[VCC_database['code'] == technology_type]
        self.max_VCC_capacity = int(VCC_database['cap_max'])
        self.min_VCC_capacity = int(VCC_database['cap_min'])
        self.g_value = float(VCC_database['G_VALUE'])
        self.chiller_configuration = pd.read_excel(self.locator.get_database_conversion_systems(),
                                                   sheet_name="Chiller_configuration")

    def configuration_values(self, source_type, compressor_type):
        df = self.chiller_configuration
        df = df[(df['SOURCE'] == source_type) & (df['COMPRESSOR'] == compressor_type)]

        filter_plfs = [col for col in df if col.startswith('plf')]
        filter_qs = [col for col in df if col.startswith('q')]

        plfs = df[filter_plfs].to_dict('records')[0]
        qs = df[filter_qs].to_dict('records')[0]
        return {'PLFs': plfs, 'Qs': qs}

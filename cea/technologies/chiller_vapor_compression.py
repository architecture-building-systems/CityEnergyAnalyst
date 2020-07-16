"""
Vapor-compressor chiller
"""
from __future__ import division
import pandas as pd
from math import log, ceil, floor
import numpy as np
import time

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
def calc_VCC(peak_cooling_load, q_chw_load_Wh, T_chw_sup_K, T_chw_re_K, T_cw_in_K, VCC_chiller):
    """
    For th e operation of a Vapor-compressor chiller between a district cooling network and a condenser with fresh water
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
        # COP = calc_temperature_adjusted_COP(peak_cooling_load, T_chw_sup_K, T_cw_in_K, VCC_chiller)
        COP = calc_part_load_adjusted_COP(peak_cooling_load, q_chw_load_Wh, T_chw_sup_K, T_cw_in_K, VCC_chiller) # choose between just temperature or also part load adjusted.
        if COP < 0.0:
            print ('Negative COP: ', COP, T_chw_sup_K, T_chw_re_K, q_chw_load_Wh)

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

def calc_temperature_adjusted_COP(peak_cooling_load, T_chw_sup_K, T_cw_in_K, VCC_chiller):
    """
    Calculates the COP adjusting for part load efficiency and temperature.
    :param float peak_cooling_load: in W
    :param float T_chw_sup_K: chilled water supply temperature, evaporator_outlet
    :param float T_cw_in_K: condenser water inlet temperature
    :param VaporCompressionChiller VCC_chiller: VCC_chiller object containing scale, capacity and config properties
    :return float cop_chiller: temperature adjusted COP for a specific hour
    """
    g_value = vcc_plant_design_g_value(peak_cooling_load, VCC_chiller)

    cop_chiller = g_value * T_chw_sup_K / (T_cw_in_K - T_chw_sup_K)

    return cop_chiller

def calc_part_load_adjusted_COP(peak_cooling_load, q_chw_load_Wh, T_chw_sup_K, T_cw_in_K, VCC_chiller):
    """
    Calculates the COP adjusting for part load efficiency and temperature.
    :param float peak_cooling_load: in W
    :param float q_chw_load_Wh: in W
    :param float T_chw_sup_K: chilled water supply temperature
    :param float T_cw_in_K: condenser water inlet temperature
    :param VaporCompressionChiller VCC_chiller: VCC_chiller object containing scale, capacity and config properties
    :return float cop_chiller: temperature and part load adjusted COP for a specific hour
    """
    design_capacity = peak_cooling_load  # for future implementation, a safety factor could be introduced. As of now this would be in conflict with the master_to_slave_variables.WS_BaseVCC_size_W
    vcc_configuration_values, n_units, rated_capacity_per_unit, cop_rated = vcc_plant_design(design_capacity, VCC_chiller)
    CAP_FT, EIR_FT = calculate_FT(T_cw_in_K, T_chw_sup_K, vcc_configuration_values)
    available_capacity_per_unit = rated_capacity_per_unit * CAP_FT
    EIR_FPLR = staging_EIR_FPLR(q_chw_load_Wh, available_capacity_per_unit, n_units,
                                  vcc_configuration_values)

    P_rated = design_capacity / cop_rated
    P_operating = P_rated * CAP_FT * EIR_FT * EIR_FPLR

    cop_chiller = q_chw_load_Wh / P_operating

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
            print 'Undefined cooling load_type for chiller COP calculation.'
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

def vcc_plant_design_g_value(design_capacity, VCC_chiller):
    """
    Creates a general chiller plant design according to ASHRAE 90.1 Appendix G,
    with a certain amount of equally-sized chillers. (Source: https://comnet.org/index.php/382-chillers)
    Depending on the design capacity, different VCC types are employed to increase the overall g_value.
    All chillers are currently water cooled (cooling towers), but could be easily extended to include air source chillers.
    :param float peak_cooling_load: in W
    :param VaporCompressionChiller VCC_chiller: VCC_chiller object containing scale, capacity and config properties
    :return float g_value: rated g_value of the chiller
    """
    source_type = 'WATER'
    if VCC_chiller.scale == 'BUILDING':
        if design_capacity <= COMPRESSOR_TYPE_LIMIT_LOW:  # according to ASHRAE 90.1 Appendix G: if design cooling load smaller than lower limit, implement one screw chiller
            compressor_type = 'SCREW'
            n_units = 1
        elif COMPRESSOR_TYPE_LIMIT_LOW < design_capacity < COMPRESSOR_TYPE_LIMIT_HIGH:  # according to ASHRAE 90.1 Appendix G: if design cooling load between limits, implement two screw chillers
            compressor_type = 'SCREW'
            n_units = 2
        elif design_capacity >= COMPRESSOR_TYPE_LIMIT_HIGH:  # according to ASHRAE 90.1 Appendix G: if design cooling load larger than upper limit, implement centrifugal chillers
            compressor_type = 'CENTRIFUGAL'
            n_units = ceil(
                design_capacity / ASHRAE_CAPACITY_LIMIT)  # according to ASHRAE 90.1 Appendix G, chiller shall not be large then 800 tons (2813 kW)
        else:
            raise ValueError('Unable to assign chiller type based on design capacity')
    elif VCC_chiller.scale == 'DISTRICT':
        if design_capacity <= COMPRESSOR_TYPE_LIMIT_LOW:  # according to ASHRAE 90.1 Appendix G: if design cooling load smaller than lower limit, implement one screw chiller
            compressor_type = 'SCREW'
            n_units = 1
        elif COMPRESSOR_TYPE_LIMIT_LOW < design_capacity < COMPRESSOR_TYPE_LIMIT_HIGH:  # according to ASHRAE 90.1 Appendix G: if design cooling load between limits, implement two screw chillers
            compressor_type = 'SCREW'
            n_units = 2
        elif design_capacity >= COMPRESSOR_TYPE_LIMIT_HIGH:  # according to ASHRAE 90.1 Appendix G: if design cooling load larger than upper limit, implement centrifugal chillers
            compressor_type = 'CENTRIFUGAL'
            max_VCC_capacity = VCC_chiller.get_max_capacity(source_type, compressor_type)
            n_units = max(2, ceil(design_capacity / max_VCC_capacity))  # chiller shall not be large then 14000 kW
        else:
            raise ValueError('Unable to assign chiller type based on design capacity')
    else:
        raise ValueError('VCC_chiller scale can only be "BUILDING" or "DISTRICT" got: {scale}'.format(
            scale=VCC_chiller.scale))
    rated_capacity_per_unit = design_capacity / n_units  # calculate the capacity per chiller installed
    g_value = VCC_chiller.get_g_value(source_type, compressor_type, rated_capacity_per_unit)

    return g_value

def vcc_plant_design(design_capacity, VCC_chiller):
    """
    Creates a general chiller plant design according to ASHRAE 90.1 Appendix G,
    with a certain amount of equally-sized chillers. (Source: https://comnet.org/index.php/382-chillers)
    Depending on the design capacity, different VCC types are employed to increase the overall COP.
    All chillers are currently water cooled (cooling towers), but could be easily extende to include air source chillers.
    :param float peak_cooling_load: in W
    :param VaporCompressionChiller VCC_chiller: VCC_chiller object containing scale, capacity and config properties
    :return dictionary vcc_configuration_values: dictionary with config information
    :return integer n_units: number of equally sized chillers
    :return float rated_capacity_per_unit: size of equally sized chillers
    :return float cop_rated: rated cop of the chiller
    """
    source_type = 'WATER'
    if VCC_chiller.scale == 'BUILDING':
        if design_capacity <= COMPRESSOR_TYPE_LIMIT_LOW:  # according to ASHRAE 90.1 Appendix G: if design cooling load smaller than lower limit, implement one screw chiller
            compressor_type = 'SCREW'
            n_units = 1
        elif COMPRESSOR_TYPE_LIMIT_LOW < design_capacity < COMPRESSOR_TYPE_LIMIT_HIGH:  # according to ASHRAE 90.1 Appendix G: if design cooling load between limits, implement two screw chillers
            compressor_type = 'SCREW'
            n_units = 2
        elif design_capacity >= COMPRESSOR_TYPE_LIMIT_HIGH:  # according to ASHRAE 90.1 Appendix G: if design cooling load larger than upper limit, implement centrifugal chillers
            compressor_type = 'CENTRIFUGAL'
            n_units = int(ceil(
                design_capacity / ASHRAE_CAPACITY_LIMIT))  # according to ASHRAE 90.1 Appendix G, chiller shall not be large then 800 tons (2813 kW)
        else:
            raise ValueError('Unable to assign chiller type based on design capacity')

    elif VCC_chiller.scale == 'DISTRICT':
        if design_capacity <= COMPRESSOR_TYPE_LIMIT_LOW:  # according to ASHRAE 90.1 Appendix G: if design cooling load smaller than lower limit, implement one screw chiller
            compressor_type = 'SCREW'
            n_units = 1
        elif COMPRESSOR_TYPE_LIMIT_LOW < design_capacity < COMPRESSOR_TYPE_LIMIT_HIGH:  # according to ASHRAE 90.1 Appendix G: if design cooling load between limits, implement two screw chillers
            compressor_type = 'SCREW'
            n_units = 2
        elif design_capacity >= COMPRESSOR_TYPE_LIMIT_HIGH:  # according to ASHRAE 90.1 Appendix G: if design cooling load larger than upper limit, implement centrifugal chillers
            compressor_type = 'CENTRIFUGAL'
            max_VCC_capacity = VCC_chiller.get_max_capacity(source_type, compressor_type)
            n_units = int(max(2, ceil(design_capacity / max_VCC_capacity)))  # chiller shall not be large then 14000 kW
        else:
            raise ValueError('Unable to assign chiller type based on design capacity')
    else:
        raise ValueError('VCC_chiller scale can only be "BUILDING" or "DISTRICT" got: {scale}'.format(
            scale=VCC_chiller.scale))

    rated_capacity_per_unit = design_capacity / n_units  # calculate the capacity per chiller installed
    vcc_configuration_values = VCC_chiller.get_configuration(source_type, compressor_type, rated_capacity_per_unit)

    cop_rated = VCC_chiller.get_rated_cop(source_type, compressor_type, rated_capacity_per_unit)

    return vcc_configuration_values, n_units, rated_capacity_per_unit, cop_rated

def staging_EIR_FPLR(q_chw_load_Wh, available_capacity_per_unit, n_units, vcc_configuration_values):
    """
    Calculates the part load factor of installed Vapor compression chillers for a given cooling based on simplified staging.
    Includes the design of the chillers based on peak load and chiller plant scale to define the part load ratio.
    Due to monotonously decreasing PLF curve (the higher the PLR, the lower the chiller efficiency), we want run as
    many chillers as possible at part load.
    :param float q_chw_load_Wh: in W
    :param float available_capacity_per_unit: in W
    :param integer n_units: number of chillers per plant
    :param dictionary vcc_configuration_values: contains config details
    :return float EIR_FPLR:  electric input to cooling output factor for part-load function curve
    """
    staging = 'SIMULTANEOUS'
    if staging == 'SEQUENTIAL':
        ### sequential staging
        n_chillers_filled = int(q_chw_load_Wh // available_capacity_per_unit)
        part_load_chiller = max(0.2,float(divmod(q_chw_load_Wh, available_capacity_per_unit)[1]) / float(
            available_capacity_per_unit))

        load_distribution_list = []
        for i in range(n_chillers_filled):
            load_distribution_list.append(1)
        load_distribution_list.append(part_load_chiller)
        for i in range(int(n_units) - n_chillers_filled - 1):
            load_distribution_list.append(0)
        load_distribution = np.array(load_distribution_list)

    elif staging == 'SIMULTANEOUS':
        ### simultaneous staging
        cutoff = 0.2
        min_load_per_unit = cutoff*available_capacity_per_unit
        units_on = max(1, min(int(floor(q_chw_load_Wh/min_load_per_unit)), n_units))

        part_load = q_chw_load_Wh/(units_on*available_capacity_per_unit)

        load_distribution_list = []
        for i in range(units_on):
            load_distribution_list.append(part_load)
        for i in range(int(n_units) - units_on):
            load_distribution_list.append(0)
        load_distribution = np.array(load_distribution_list)

    EIR_FPLR = np.sum(calc_EIR_FPLR(load_distribution, vcc_configuration_values[
        'PLFs']) * load_distribution * available_capacity_per_unit) / q_chw_load_Wh  # calculates the average EIR_FPLR value
    return EIR_FPLR


def calc_EIR_FPLR(PLR, PLFs):
    """
    Electric Chiller Cooling Efficiency Adjustment Curves
    coefficients taken from https://comnet.org/index.php/382-chillers and only includes water source electrical chillers
    :param np.array PLR: part load ratio
    :param np.array PLFs: part load factor coefficients
    :return np.array EIR_FPLR: part load factor
    """
    EIR_FPLR = PLFs['plf_a'] + PLFs['plf_b'] * PLR + PLFs['plf_c'] * PLR ** 2

    return EIR_FPLR


def calculate_FT(T_cw_in_K, T_chw_sup_K, vcc_configuration_values):
    """
    calculates the Chiller Cooling Capacity Adjustment Curve
    for both 'cooling capacity function of temperature curve' (CAP_FT)
    and 'electric input to cooling output factor for temperature function curve'(EIR_FT)
    coefficients taken from https://comnet.org/index.php/382-chillers
    :param float T_cw_in_K: condenser water supply temperature in Kelvin
    :param float T_chw_sup_K: supplied chilled water temperature in Kelvin
    :param dictionary vcc_configuration_values: dictionary containing config values
    :return float CAP_FT: cooling capacity function of temperature curve
    :return float EIR_FT: electric input to cooling output factor for temperature function curve
    """
    if vcc_configuration_values['IP_SI'] == 'SI':
        t_chws_F = T_chw_sup_K - 273.15
        t_cws_F = T_cw_in_K - 273.15
    else:
        t_chws_F = kelvin_to_fahrenheit(T_chw_sup_K)
        t_cws_F = kelvin_to_fahrenheit(T_cw_in_K)

    Cap_fts = vcc_configuration_values['Cap_fts']
    CAP_FT = Cap_fts['cap_ft_a'] + Cap_fts['cap_ft_b'] * t_chws_F + Cap_fts['cap_ft_c'] * t_chws_F ** 2 + Cap_fts[
        'cap_ft_d'] * t_cws_F + \
             Cap_fts['cap_ft_e'] * t_cws_F ** 2 + Cap_fts['cap_ft_f'] * t_chws_F * t_cws_F
    EIR_FTs = vcc_configuration_values['Eir_fts']
    EIR_FT = EIR_FTs['eir_ft_a'] + EIR_FTs['eir_ft_b'] * t_chws_F + EIR_FTs['eir_ft_c'] * t_chws_F ** 2 + EIR_FTs[
        'eir_ft_d'] * t_cws_F + \
             EIR_FTs['eir_ft_e'] * t_cws_F ** 2 + EIR_FTs['eir_ft_f'] * t_chws_F * t_cws_F
    return CAP_FT, EIR_FT


class VaporCompressionChiller(object):
    __slots__ = ["locator","scale", "VCC_database"]

    def __init__(self, locator, scale):
        self.locator = locator
        self.scale = scale
        self.VCC_database = None
        self.setup()

    def setup(self):
        self.VCC_database = pd.read_excel(self.locator.get_database_conversion_systems(), sheet_name="Chiller")

    def get_g_value(self, source_type, compressor_type, capacity):
        df = self.VCC_database
        df = df[(df['SOURCE'] == source_type) & (df['COMPRESSOR'] == compressor_type) \
                & (df['cap_min'] <= capacity) & (capacity < df['cap_max'])]
        g_value = float(df['G_VALUE'])
        return g_value

    def get_rated_cop(self, source_type, compressor_type, capacity):
        df = self.VCC_database
        df = df[(df['SOURCE'] == source_type) & (df['COMPRESSOR'] == compressor_type) \
                & (df['cap_min'] <= capacity) & (capacity < df['cap_max'])]
        rated_cop = float(df['COP'])
        return rated_cop

    def get_max_capacity(self, source_type, compressor_type):
        df = self.VCC_database
        df = df[(df['SOURCE'] == source_type) & (df['COMPRESSOR'] == compressor_type)]
        max_capacity = float(df['cap_max'].max())
        return max_capacity

    def get_configuration(self, source_type, compressor_type, capacity):
        df = self.VCC_database
        df = df[(df['SOURCE'] == source_type) & (df['COMPRESSOR'] == compressor_type) \
                & (df['cap_min'] <= capacity) & (capacity < df['cap_max'])]

        filter_plfs = [col for col in df if col.startswith('plf')]
        filter_eir_ft = [col for col in df if col.startswith('eir_ft')]
        filter_cap_ft = [col for col in df if col.startswith('cap_ft')]

        ip_si = str(df['IP_SI'].values[0])
        plfs = df[filter_plfs].to_dict('records')[0]
        eir_fts = df[filter_eir_ft].to_dict('records')[0]
        cap_fts = df[filter_cap_ft].to_dict('records')[0]

        return {'PLFs': plfs, 'Eir_fts': eir_fts, 'Cap_fts' : cap_fts, 'IP_SI': ip_si}

"""
Vapor-compressor chiller
"""

import pandas as pd
from math import log, ceil
import numpy as np

from cea.technologies.constants import G_VALUE_CENTRALIZED, G_VALUE_DECENTRALIZED, CHILLER_DELTA_T_HEX_CT, \
    CHILLER_DELTA_T_APPROACH, T_EVAP_AHU, T_EVAP_ARU, T_EVAP_SCU, DT_NETWORK_CENTRALIZED, CENTRALIZED_AUX_PERCENTAGE, \
    DECENTRALIZED_AUX_PERCENTAGE

from cea.optimization.constants import VCC_CODE_CENTRALIZED, VCC_CODE_DECENTRALIZED
from cea.analysis.costs.equations import calc_capex_annualized

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# technical model
def calc_VCC_const(q_chw_load_Wh, COP):
    """
    Calculate vapor compression chiller operation for a fixed COP. Return required power supply and thermal energy
    output to cold water loop for a given chilled water cooling load.

    :param q_chw_load_Wh: Chilled water cooling load in Watt-hours (single value or time series).
    :type q_chw_load_Wh: int, float, list or pd.Series
    :param COP: Characteristic coefficient of performance of the vapor compression chiller
    :type COP: int, float

    :return p_supply_Wh: Electrical power supply required to provide the given cooling load (single value or time series)
    :rtype p_supply_Wh: int, float, list or pd.Series
    :return q_cw_out_Wh: Thermal energy output to cold water loop, i.e. waste heat (single value or time series)
    :rtype q_cw_out_Wh: int, float, list or pd.Series
    """
    p_supply_Wh = q_chw_load_Wh / COP
    q_cw_out_Wh = p_supply_Wh + q_chw_load_Wh

    return p_supply_Wh, q_cw_out_Wh


def calc_VCC(q_chw_load_Wh, T_chw_sup_K, T_chw_re_K, T_cw_in_K, VC_chiller):
    """
    For the operation of a vapor compression chiller between a district cooling network and a condenser with fresh water
    to a cooling tower following [D.J. Swider, 2003]_.
    The physically based fundamental thermodynamic model(LR4) is implemented in this function.
    :type peak_cooling_load : float
    :param peak_cooling_load: peak cooling load provided by the VCC (which is set equal to its max. capacity in the
                              centralised optimization script)
    :type q_chw_load_Wh : float
    :param q_chw_load_Wh: current cooling demand of building or DCN (i.e. chilled water load)
    :type T_chw_sup_K : float
    :param T_chw_sup_K: plant supply temperature to DCN (i.e. chilled water supply temperature)
    :type T_chw_re_K : float
    :param T_chw_re_K: plant return temperature from DCN (i.e. chilled water return temperature)
    :type T_cw_in_K : float
    :param T_cw_in_K: temperature of water coming into the condenser (from cooling tower or water body)
    :type VC_chiller : cea.technologies.chiller_vapor_compression.VaporCompressionChiller class object
    :param VC_chiller: object containing properties of eligible vapor compression chillers
    :rtype chiller_operation : dict (3 x float)
    :return chiller_operation: electrical energy input, cooling energy input and cooling energy output of VCC
    ..[D.J. Swider, 2003] D.J. Swider (2003). A comparison of empirically based steady-state models for
    vapor-compression liquid chillers. Applied Thermal Engineering.
    """

    if q_chw_load_Wh == 0.0:
        wdot_W = 0.0
        q_cw_W = 0.0
    elif q_chw_load_Wh > 0.0:
        COP = calc_COP_g(T_chw_sup_K, T_cw_in_K, VC_chiller)
        if COP < 0.0:
            print(f'Negative COP: {COP} {T_chw_sup_K} {T_chw_re_K} {T_cw_in_K}, {q_chw_load_Wh}', )
        # calculate chiller outputs
        # print('COP is: ', COP)
        wdot_W = q_chw_load_Wh / COP
        q_cw_W = wdot_W + q_chw_load_Wh  # heat rejected to the cold water (cw) loop
    else:
        raise ValueError('negative cooling load to VCC: ', q_chw_load_Wh)

    chiller_operation = {'wdot_W': wdot_W, 'q_cw_W': q_cw_W, 'q_chw_W': q_chw_load_Wh}

    return chiller_operation


def calc_COP_g(T_evap_K, T_cond_K, VC_chiller):
    """
    Calculate the approximate COP at rated operating conditions using the g-value (sometimes also called
    the second-law efficiency [Bejan, 2016]).
    Assuming a rated COP for all calculations is a strong simplification, but accurate enough for most cases in CEA.

    [Bejan, 2016] Adrian Bejan, 2016, Andvanced engineering thermodynamics (p. 106)
    """
    cop_chiller = VC_chiller.g_value * T_evap_K / (T_cond_K - T_evap_K)
    return cop_chiller


def eta_th_vcc_g(T_evap_K, T_cond_K, VC_chiller):
    """
    Calculate vapour compression chiller's thermal efficiency (= Qc_evap / Qc_cond,
    i.e. heat_from_DC / heat_to_waterORair ) in accordance with the g-value VCC model.
    This calculation also assumes that all heat from the VCC is directed to the heat sink
    (i.e. Qc_evap + P_el = Qc_cond).

    eta_th = Qc_evap / Qc_cond
           = Qc_evap / (Qc_evap + P_el)
           = 1 / (1 + P_el/Qc_evap)
           = 1 / (1 + 1/COP)
    """
    thermal_efficiency = 1 / (1 + 1 / calc_COP_g(T_evap_K, T_cond_K, VC_chiller))

    return thermal_efficiency


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
    if centralized is True:
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
    if centralized is True:  # Todo: improve this to a better approximation than a static value DT_Network
        # for the centralized case we have to supply somewhat colder, currently based on CEA calculation for MIX_m case
        T_evap_K = T_evap_K - DT_NETWORK_CENTRALIZED
    # calculate condenser temperature with static approach temperature assumptions # FIXME: only work for tropical climates
    T_cond_K = np.mean(weather_data['wetbulb_C']) + CHILLER_DELTA_T_APPROACH + CHILLER_DELTA_T_HEX_CT + 273.15
    # calculate chiller COP
    cop_chiller = g_value * T_evap_K / (T_cond_K - T_evap_K)
    # calculate system COP with pumping power of auxiliaries
    if centralized is True:
        cop_system = 1 / (1 / cop_chiller * (1 + CENTRALIZED_AUX_PERCENTAGE / 100))
    else:
        cop_system = 1 / (1 / cop_chiller * (1 + DECENTRALIZED_AUX_PERCENTAGE / 100))

    return cop_system, cop_chiller


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

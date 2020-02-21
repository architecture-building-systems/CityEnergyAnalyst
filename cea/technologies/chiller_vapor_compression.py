"""
Vapor-compressor chiller
"""
from __future__ import division
import pandas as pd
from math import log, ceil
import numpy as np

from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.technologies.constants import G_VALUE_CENTRALIZED, G_VALUE_DECENTRALIZED, CHILLER_DELTA_T_HEX_CT, \
    CHILLER_DELTA_T_APPROACH, T_EVAP_AHU, T_EVAP_ARU, T_EVAP_SCU, DT_NETWORK_CENTRALIZED, CENTRALIZED_AUX_PERCENTAGE, \
    DECENTRALIZED_AUX_PERCENTAGE

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# technical model

def calc_VCC(q_chw_load_Wh, T_chw_sup_K, T_chw_re_K, T_cw_in_K, g_value):
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
        COP = calc_COP_with_carnot_efficiency(T_chw_sup_K, T_cw_in_K, g_value)
        if COP < 0.0:
            print ('Negative COP: ', COP, T_chw_sup_K, T_chw_re_K, q_chw_load_Wh)

        # calculate chiller outputs
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


def calc_COP_with_carnot_efficiency(T_evap_K, T_cond_K, g_value):
    cop_chiller = g_value * T_evap_K / (T_cond_K - T_evap_K)
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
            Inv_IR = (VCC_cost_data.iloc[0]['IR_%']) / 100
            Inv_LT = VCC_cost_data.iloc[0]['LT_yr']
            Inv_OM = VCC_cost_data.iloc[0]['O&M_%'] / 100
            InvC = Inv_a + Inv_b * (Q_nom_W) ** Inv_c + (Inv_d + Inv_e * Q_nom_W) * log(Q_nom_W)
            Capex_a_VCC_USD = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
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
                Inv_IR = (VCC_cost_data.iloc[0]['IR_%']) / 100
                Inv_LT = VCC_cost_data.iloc[0]['LT_yr']
                Inv_OM = VCC_cost_data.iloc[0]['O&M_%'] / 100
                InvC = Inv_a + Inv_b * (Q_nom_each_chiller) ** Inv_c + (Inv_d + Inv_e * Q_nom_each_chiller) * log(
                    Q_nom_each_chiller)
                Capex_a1 = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
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

def get_max_VCC_unit_size(locator, VCC_code='CH3'):
    VCC_cost_data = pd.read_excel(locator.get_database_conversion_systems(), sheet_name="Chiller")
    VCC_cost_data = VCC_cost_data[VCC_cost_data['code'] == VCC_code]
    max_VCC_unit_size_W = max(VCC_cost_data['cap_max'].values)
    return max_VCC_unit_size_W

def main():
    Qc_W = 10
    T_chw_sup_K = 273.15 + 6
    T_chw_re_K = 273.15 + 11
    T_cw_in_K = 273.15 + 28
    g_value = G_VALUE_CENTRALIZED
    chiller_operation = calc_VCC(Qc_W, T_chw_sup_K, T_chw_re_K, T_cw_in_K, g_value)
    print chiller_operation


if __name__ == '__main__':
    main()

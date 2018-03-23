"""
Absorption chillers
"""
from __future__ import division
import cea.config
import cea.globalvar
import cea.inputlocator
import pandas as pd
import numpy as np
from math import log
from cea.optimization.constants import *
from sympy import *

__author__ = "Shanshan Hsieh"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# technical model

def calc_chiller_abs_main(mdot_chw_kgpers, T_chw_sup_K, T_chw_re_K, T_hw_in_C, T_ground_K, Qc_nom_W, locator, gv):
    """
    Assumptions: constant flow rate at the secondary sides (chilled water, cooling water, hot water)

    :type mdot_chw_kgpers : float
    :param mdot_chw_kgpers: plant supply mass flow rate to the district cooling network
    :type T_chw_sup_K : float
    :param T_chw_sup_K: plant supply temperature to DCN
    :type T_chw_re_K : float
    :param T_chw_re_K: plant return temperature from DCN
    :param gV: globalvar.py

    :rtype wdot : float
    :returns wdot: chiller electric power requirement
    :rtype qhotdot : float
    :returns qhotdot: condenser heat rejection

    ..[D.J. Swider, 2003] D.J. Swider (2003). A comparison of empirically based steady-state models for
    vapor-compression liquid chillers. Applied Thermal Engineering.

    """
    input_conditions = {'T_chw_sup_K': T_chw_sup_K, 'T_chw_re_K': T_chw_re_K, 'T_hw_in_C': T_hw_in_C,
                        'T_ground_K': T_ground_K}
    mcp_chw_WperK = mdot_chw_kgpers * gv.Cpw * 1000  # TODO: replace gv.Cpw
    input_conditions['q_chw_W'] = mcp_chw_WperK * (T_chw_re_K - T_chw_sup_K) if mdot_chw_kgpers != 0 else 0

    if mdot_chw_kgpers == 0:
        wdot_W = 0
        q_cw_W = 0
        q_hw_W = 0
        T_hw_out_C = np.nan
        EER = 0
    else:
        # solve operating conditions at given demand
        if input_conditions['q_chw_W'] > 0:
            chiller_prop = pd.read_excel(locator.get_supply_systems(gv.config.region), sheetname="Abs_chiller",
                                         usecols=['cap_min', 'cap_max', 'code', 'el_W', 's_e', 'r_e', 's_g', 'r_g',
                                                  'a_e', 'e_e', 'a_g', 'e_g', 'm_cw', 'm_hw'])
            technology_code = list(set(chiller_prop['code']))  # read the list of technology
            chiller_prop = chiller_prop[
                chiller_prop['code'] == technology_code[2]]  # FIXME: pass technology code here instead of 0
            input_conditions['q_chw_W'] = chiller_prop['cap_min'].values if input_conditions['q_chw_W'] < chiller_prop[
                'cap_min'].values else input_conditions['q_chw_W']  # minimum load
            chiller_prop = chiller_prop[(chiller_prop['cap_min'] <= input_conditions['q_chw_W']) & (
                chiller_prop['cap_max'] > input_conditions['q_chw_W'])]  # keep properties of the associated capacity
            if chiller_prop.empty:
                raise ValueError('The operation range is not in the supply_system database. Please add new chillers.')

        operating_conditions = calc_operating_conditions(chiller_prop, input_conditions, gv)
        wdot_W = chiller_prop['el_W']  # TODO: check if change with capacity
        q_cw_W = operating_conditions['q_cw_W']  # to W
        q_hw_W = operating_conditions['q_hw_W']  # to W
        T_hw_out_C = operating_conditions['T_hw_out_C']
        EER = input_conditions['q_chw_W'] / (q_hw_W + wdot_W)

    chiller_operation = {'wdot_W': wdot_W, 'q_cw_W': q_cw_W, 'q_hw_W': q_hw_W, 'T_hw_out_C': T_hw_out_C,
                         'q_chw_W': input_conditions['q_chw_W'], 'EER': EER}

    return chiller_operation


def calc_operating_conditions(chiller_prop, input_conditions, gv):
    # external water circuits (e: chilled water, ac: cooling water, d: hot water)
    T_cw_in_C = input_conditions['T_ground_K'] - 273.0  # condenser water inlet temperature
    T_chw_in_C = input_conditions['T_chw_re_K'] - 273.0  # inlet to the evaporator
    T_chw_out_C = input_conditions['T_chw_sup_K'] - 273.0
    q_chw_kW = input_conditions['q_chw_W'] / 1000
    m_cw_kgpers = chiller_prop['m_cw']
    m_hw_kgpers = chiller_prop['m_hw']
    mcp_cw_kWperK = m_cw_kgpers * gv.Cpw
    mcp_hw_kWperK = m_hw_kgpers * gv.Cpw

    # variables to solve
    T_hw_out_C, T_cw_out_C, q_hw_kW = symbols('T_hw_out_C T_cw_out_C q_hw_kW')

    # characteristic temperature differences
    T_hw_mean_C = (input_conditions['T_hw_in_C'] + T_hw_out_C) / 2
    T_cw_mean_C = (T_cw_in_C + T_cw_out_C) / 2
    T_chw_mean_C = (T_chw_in_C + T_chw_out_C) / 2
    ddt_e = T_hw_mean_C + chiller_prop['a_e'].values[0] * T_cw_mean_C + chiller_prop['e_e'].values[0] * T_chw_mean_C
    ddt_g = T_hw_mean_C + chiller_prop['a_g'].values[0] * T_cw_mean_C + chiller_prop['e_g'].values[0] * T_chw_mean_C

    # systems of equations
    eq_e = chiller_prop['s_e'].values[0] * ddt_e + chiller_prop['r_e'].values[0] - q_chw_kW
    eq_g = chiller_prop['s_g'].values[0] * ddt_g + chiller_prop['r_g'].values[0] - q_hw_kW
    eq_bal_g = (input_conditions['T_hw_in_C'] - T_hw_out_C) - q_hw_kW / mcp_hw_kWperK

    # solve the system of equation with sympy
    eq_sys = [eq_e, eq_g, eq_bal_g]
    unknown_variables = (T_hw_out_C, T_cw_out_C, q_hw_kW)
    (T_hw_out_C, T_cw_out_C, q_hw_kW) = tuple(*linsolve(eq_sys, unknown_variables))

    # calculate results
    q_cw_kW = q_hw_kW + q_chw_kW  # approximation
    T_hw_out_C = input_conditions['T_hw_in_C'] - q_hw_kW / mcp_hw_kWperK
    T_cw_out_C = T_cw_in_C + q_cw_kW / mcp_cw_kWperK  # TODO: set upper bound of the chiller operation

    return {'T_hw_out_C': T_hw_out_C, 'T_cw_out_C': T_cw_out_C, 'q_chw_W': q_chw_kW * 1000, 'q_hw_W': q_hw_kW * 1000,
            'q_cw_W': q_cw_kW * 1000}


# Investment costs

def calc_Cinv_chiller_abs(qcold_W, gv, locator, technology=2):
    """
    Annualized investment costs for the vapor compressor chiller

    :type qcold_W : float
    :param qcold_W: peak cooling demand in [W]
    :param gV: globalvar.py

    :returns InvCa: annualized chiller investment cost in CHF/a
    :rtype InvCa: float

    """
    if qcold_W > 0:
        cost_data = pd.read_excel(locator.get_supply_systems(gv.config.region), sheetname="Abs_chiller",
                                  usecols=['code', 'cap_min', 'cap_max', 'a', 'b', 'c', 'd', 'e', 'IR_%', 'LT_yr',
                                           'O&M_%'])
        technology_code = list(set(cost_data['code']))
        cost_data = cost_data[cost_data['code'] == technology_code[2]]  # FIXME: where to get the technology input?
        qcold_W = cost_data['cap_min'].values.min() if qcold_W < cost_data['cap_min'].values.min() else qcold_W  # minimum technology size
        cost_data = cost_data[(cost_data['cap_min'] <= qcold_W) & (
            cost_data['cap_max'] > qcold_W)]  # keep properties of the associated capacity

        Inv_a = cost_data.iloc[0]['a']
        Inv_b = cost_data.iloc[0]['b']
        Inv_c = cost_data.iloc[0]['c']
        Inv_d = cost_data.iloc[0]['d']
        Inv_e = cost_data.iloc[0]['e']
        Inv_IR = (cost_data.iloc[0]['IR_%']) / 100
        Inv_LT = cost_data.iloc[0]['LT_yr']
        Inv_OM = cost_data.iloc[0]['O&M_%'] / 100

        InvC = Inv_a + Inv_b * (qcold_W) ** Inv_c + (Inv_d + Inv_e * qcold_W) * log(qcold_W)
        Capex_a = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
        Opex_fixed = Capex_a * Inv_OM
    else:
        Capex_a = 0
        Opex_fixed = 0

    return Capex_a, Opex_fixed


def main(config):
    """
    run the whole preprocessing routine
    """
    gv = cea.globalvar.GlobalVariables()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    mdot_chw_kgpers = 35
    T_chw_sup_K = 7 + 273.0
    T_chw_re_K = 14 + 273.0
    T_hw_in_C = 98
    T_ground_K = 300
    building_name = 'B01'
    Qc_nom_W = 10000
    SC_data = pd.read_csv(locator.SC_results(building_name=building_name),
                          usecols=["T_SC_sup_C", "T_SC_re_C", "mcp_SC_kWperC", "Q_SC_gen_kWh"])
    chiller_operation = calc_chiller_abs_main(mdot_chw_kgpers, T_chw_sup_K, T_chw_re_K, T_hw_in_C, T_ground_K, Qc_nom_W,
                                              locator, gv)
    print chiller_operation

    print 'test_decentralized_buildings_cooling() succeeded'


if __name__ == '__main__':
    main(cea.config.Configuration())

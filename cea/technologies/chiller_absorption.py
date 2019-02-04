"""
Absorption chillers
"""
from __future__ import division, print_function
import cea.config
import cea.globalvar
import cea.inputlocator
import pandas as pd
import numpy as np
from math import log, ceil
import sympy
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK

__author__ = "Shanshan Hsieh"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# technical model

def calc_chiller_main(mdot_chw_kgpers, T_chw_sup_K, T_chw_re_K, T_hw_in_C, T_ground_K, ACH_type, Qc_nom_W, locator, config):
    """
    This model calculates the operation conditions of the absorption chiller given the chilled water loads in
    evaporators and the hot water inlet temperature in the generator (desorber).
    This is an empiral model using characteristic equation method developed by _[Kuhn A. & Ziegler F., 2005].
    The parameters of each absorption chiller can be derived from experiments or performance curves from manufacturer's
    catalog, more details are described in _[Puig-Arnavat M. et al, 2010].
    Assumptions: constant external flow rates (chilled water at the evaporator, cooling water at the condensor and
    absorber, hot water at the generator).
    :param mdot_chw_kgpers: required chilled water flow rate
    :type mdot_chw_kgpers: float
    :param T_chw_sup_K: required chilled water supply temperature (outlet from the evaporator)
    :type T_chw_sup_K: float
    :param T_chw_re_K: required chilled water return temperature (inlet to the evaporator)
    :type T_chw_re_K: float
    :param T_hw_in_C: hot water inlet temperature to the generator
    :type T_hw_in_C: float
    :param T_ground_K: ground temperature
    :type T_ground_K: float
    :param Qc_nom_W: nominal chiller capacity
    :param locator: locator class
    :return:
    ..[Kuhn A. & Ziegler F., 2005] Operational results of a 10kW absorption chiller and adaptation of the characteristic
    equation. In: Proceedings of the interantional conference solar air confitioning. Bad Staffelstein, Germany: 2005.
    ..[Puig-Arnavat M. et al, 2010] Analysis and parameter identification for characteristic equations of single- and
    double-effect absorption chillers by means of multivariable regression. Int J Refrig: 2010.
    """

    # create a dict of input operating conditions
    input_conditions = {'T_chw_sup_K': T_chw_sup_K, 'T_chw_re_K': T_chw_re_K, 'T_hw_in_C': T_hw_in_C,
                        'T_ground_K': T_ground_K}
    mcp_chw_WperK = mdot_chw_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK
    input_conditions['q_chw_W'] = mcp_chw_WperK * (T_chw_re_K - T_chw_sup_K) if mdot_chw_kgpers != 0 else 0

    if np.isclose(input_conditions['q_chw_W'], 0.0):
        wdot_W = 0
        q_cw_W = 0
        q_hw_W = 0
        T_hw_out_C = np.nan
        EER = 0
    else:
        # read chiller operation parameters from database
        chiller_prop = pd.read_excel(locator.get_supply_systems(config.region),
                                                     sheetname="Absorption_chiller")
        chiller_prop = chiller_prop[chiller_prop['type'] == ACH_type]
        input_conditions['q_chw_W'] = chiller_prop['cap_min'].values if input_conditions['q_chw_W'] < chiller_prop[
            'cap_min'].values.min() else input_conditions['q_chw_W']  # minimum load

        max_chiller_size = max(chiller_prop['cap_max'].values)

        if input_conditions['q_chw_W'] <= max_chiller_size:
            # solve operating conditions at given input conditions
            chiller_prop = chiller_prop[(chiller_prop['cap_min'] <= input_conditions['q_chw_W']) & (
                    chiller_prop['cap_max'] > input_conditions[
                'q_chw_W'])]  # keep properties of the associated capacity
            operating_conditions = calc_operating_conditions(chiller_prop, input_conditions)
            wdot_W = chiller_prop['el_W'].values[0]  # TODO: check if change with capacity
            q_cw_W = operating_conditions['q_cw_W']  # to W
            q_hw_W = operating_conditions['q_hw_W']  # to W
            T_hw_out_C = operating_conditions['T_hw_out_C']
            EER = input_conditions['q_chw_W'] / (q_hw_W + wdot_W)
        else:
            number_of_chillers = int(ceil(input_conditions['q_chw_W'] / max_chiller_size))
            Q_nom_each_chiller = input_conditions['q_chw_W'] / number_of_chillers
            input_conditions['q_chw_W'] = Q_nom_each_chiller
            chiller_prop = chiller_prop[(chiller_prop['cap_min'] <= input_conditions['q_chw_W']) & (
                    chiller_prop['cap_max'] > input_conditions[
                'q_chw_W'])]  # keep properties of the associated capacity
            operating_conditions = calc_operating_conditions(chiller_prop, input_conditions)
            wdot_W = chiller_prop['el_W'].values[0] * number_of_chillers  # TODO: check if change with capacity
            q_cw_W = operating_conditions['q_cw_W'] * number_of_chillers  # to W
            q_hw_W = operating_conditions['q_hw_W'] * number_of_chillers  # to W
            T_hw_out_C = operating_conditions['T_hw_out_C']
            EER = input_conditions['q_chw_W'] * number_of_chillers / (q_hw_W + wdot_W)

    if input_conditions['q_chw_W'] != 0:
        if T_hw_out_C < 0:
            print (T_hw_out_C)

    chiller_operation = {'wdot_W': wdot_W, 'q_cw_W': q_cw_W, 'q_hw_W': q_hw_W, 'T_hw_out_C': T_hw_out_C,
                         'q_chw_W': input_conditions['q_chw_W'], 'EER': EER}

    return chiller_operation

def calc_operating_conditions(chiller_prop, input_conditions):
    """
    Calculates chiller operating conditions at given input conditions by solving the characteristic equations and the
    energy balance equations. This method is adapted from _[Kuhn A. & Ziegler F., 2005].
    :param chiller_prop: parameters in the characteristic equations and the external flow rates.
    :type chiller_prop: dict
    :param input_conditions:
    :type input_conditions: dict
    :return: a dict with operating conditions of the chilled water, cooling water and hot water loops in a absorption
    chiller.
    ..[Kuhn A. & Ziegler F., 2005] Operational results of a 10kW absorption chiller and adaptation of the characteristic
    equation. In: Proceedings of the interantional conference solar air confitioning. Bad Staffelstein, Germany: 2005.
    """
    # external water circuits (e: chilled water, ac: cooling water, d: hot water)
    T_cw_in_C = input_conditions['T_ground_K'] - 273.0  # condenser water inlet temperature
    T_chw_in_C = input_conditions['T_chw_re_K'] - 273.0  # inlet to the evaporator
    T_chw_out_C = input_conditions['T_chw_sup_K'] - 273.0  # outlet from the evaporator
    q_chw_kW = input_conditions['q_chw_W'] / 1000  # cooling load ata the evaporator
    m_cw_kgpers = chiller_prop['m_cw'].values[0]  # external flow rate of cooling water at the condensor and absorber
    m_hw_kgpers = chiller_prop['m_hw'].values[0]  # external flow rate of hot water at the generator
    mcp_cw_kWperK = m_cw_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK/1000
    mcp_hw_kWperK = m_hw_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK/1000

    # variables to solve
    T_hw_out_C, T_cw_out_C, q_hw_kW = sympy.symbols('T_hw_out_C T_cw_out_C q_hw_kW')

    # characteristic temperature differences
    T_hw_mean_C = (input_conditions['T_hw_in_C'] + T_hw_out_C) / 2
    T_cw_mean_C = (T_cw_in_C + T_cw_out_C) / 2
    T_chw_mean_C = (T_chw_in_C + T_chw_out_C) / 2
    ddt_e = T_hw_mean_C + chiller_prop['a_e'].values[0] * T_cw_mean_C + chiller_prop['e_e'].values[0] * T_chw_mean_C
    ddt_g = T_hw_mean_C + chiller_prop['a_g'].values[0] * T_cw_mean_C + chiller_prop['e_g'].values[0] * T_chw_mean_C

    # systems of equations to solve
    eq_e = chiller_prop['s_e'].values[0] * ddt_e + chiller_prop['r_e'].values[0] - q_chw_kW
    eq_g = chiller_prop['s_g'].values[0] * ddt_g + chiller_prop['r_g'].values[0] - q_hw_kW
    eq_bal_g = (input_conditions['T_hw_in_C'] - T_hw_out_C) - q_hw_kW / mcp_hw_kWperK

    # solve the system of equations with sympy
    eq_sys = [eq_e, eq_g, eq_bal_g]
    unknown_variables = (T_hw_out_C, T_cw_out_C, q_hw_kW)
    (T_hw_out_C, T_cw_out_C, q_hw_kW) = tuple(*sympy.linsolve(eq_sys, unknown_variables))

    # calculate results
    q_cw_kW = q_hw_kW + q_chw_kW  # approximation
    T_hw_out_C = input_conditions['T_hw_in_C'] - q_hw_kW / mcp_hw_kWperK
    T_cw_out_C = T_cw_in_C + q_cw_kW / mcp_cw_kWperK  # TODO: set upper bound of the chiller operation

    return {'T_hw_out_C': T_hw_out_C, 'T_cw_out_C': T_cw_out_C, 'q_chw_W': q_chw_kW * 1000, 'q_hw_W': q_hw_kW * 1000,
            'q_cw_W': q_cw_kW * 1000}


# Investment costs

def calc_Cinv_ACH(qcold_W, locator, ACH_type, config):
    """
    Annualized investment costs for the vapor compressor chiller
    :type qcold_W : float
    :param qcold_W: peak cooling demand in [W]
    :param gV: globalvar.py
    :returns InvCa: annualized chiller investment cost in CHF/a
    :rtype InvCa: float
    """
    Capex_a_ACH_USD = 0
    Opex_fixed_ACH_USD = 0
    Capex_ACH_USD = 0
    if qcold_W > 0:
        Absorption_chiller_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="Absorption_chiller")
        Absorption_chiller_cost_data = Absorption_chiller_cost_data[Absorption_chiller_cost_data['type'] == ACH_type]
        max_chiller_size = max(Absorption_chiller_cost_data['cap_max'].values)

        qcold_W = Absorption_chiller_cost_data['cap_min'].values.min() if qcold_W < Absorption_chiller_cost_data[
            'cap_min'].values.min() else qcold_W  # minimum technology size


        if qcold_W <= max_chiller_size:

            Absorption_chiller_cost_data = Absorption_chiller_cost_data[
                (Absorption_chiller_cost_data['cap_min'] <= qcold_W) & (
                        Absorption_chiller_cost_data[
                            'cap_max'] > qcold_W)]  # keep properties of the associated capacity
            Inv_a = Absorption_chiller_cost_data.iloc[0]['a']
            Inv_b = Absorption_chiller_cost_data.iloc[0]['b']
            Inv_c = Absorption_chiller_cost_data.iloc[0]['c']
            Inv_d = Absorption_chiller_cost_data.iloc[0]['d']
            Inv_e = Absorption_chiller_cost_data.iloc[0]['e']
            Inv_IR = (Absorption_chiller_cost_data.iloc[0]['IR_%']) / 100
            Inv_LT = Absorption_chiller_cost_data.iloc[0]['LT_yr']
            Inv_OM = Absorption_chiller_cost_data.iloc[0]['O&M_%'] / 100

            InvC = Inv_a + Inv_b * (qcold_W) ** Inv_c + (Inv_d + Inv_e * qcold_W) * log(qcold_W)
            Capex_a_ACH_USD = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
            Opex_fixed_ACH_USD = Capex_a_ACH_USD * Inv_OM
            Capex_ACH_USD = InvC
        else:
            number_of_chillers = int(ceil(qcold_W / max_chiller_size))
            Q_nom_each_chiller = qcold_W / number_of_chillers
            for i in range(number_of_chillers):
                Absorption_chiller_cost_data = Absorption_chiller_cost_data[
                    (Absorption_chiller_cost_data['cap_min'] <= Q_nom_each_chiller) & (
                            Absorption_chiller_cost_data[
                                'cap_max'] > Q_nom_each_chiller)]  # keep properties of the associated capacity
                Inv_a = Absorption_chiller_cost_data.iloc[0]['a']
                Inv_b = Absorption_chiller_cost_data.iloc[0]['b']
                Inv_c = Absorption_chiller_cost_data.iloc[0]['c']
                Inv_d = Absorption_chiller_cost_data.iloc[0]['d']
                Inv_e = Absorption_chiller_cost_data.iloc[0]['e']
                Inv_IR = (Absorption_chiller_cost_data.iloc[0]['IR_%']) / 100
                Inv_LT = Absorption_chiller_cost_data.iloc[0]['LT_yr']
                Inv_OM = Absorption_chiller_cost_data.iloc[0]['O&M_%'] / 100

                InvC = Inv_a + Inv_b * (Q_nom_each_chiller) ** Inv_c + (Inv_d + Inv_e * Q_nom_each_chiller) * log(Q_nom_each_chiller)
                Capex_a1 = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
                Capex_a_ACH_USD = Capex_a_ACH_USD + Capex_a1
                Opex_fixed_ACH_USD = Opex_fixed_ACH_USD + Capex_a1 * Inv_OM
                Capex_ACH_USD = Capex_ACH_USD + InvC

    return Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD


def main(config):
    """
    run the whole preprocessing routine
    """
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    mdot_chw_kgpers = 35
    T_chw_sup_K = 7 + 273.0
    T_chw_re_K = 14 + 273.0
    T_hw_in_C = 98
    T_ground_K = 300
    building_name = 'B01'
    Qc_nom_W = 10000
    ACH_type = 'single'
    chiller_operation = calc_chiller_main(mdot_chw_kgpers, T_chw_sup_K, T_chw_re_K, T_hw_in_C, T_ground_K, ACH_type,
                                          Qc_nom_W, locator, config)
    print(chiller_operation)

    print('test_decentralized_buildings_cooling() succeeded')


if __name__ == '__main__':
    main(cea.config.Configuration())


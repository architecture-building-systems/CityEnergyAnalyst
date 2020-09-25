"""
Absorption chillers
"""
import cea.config
import cea.inputlocator
import pandas as pd
import numpy as np
from math import log, ceil
import sympy
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.analysis.costs.equations import calc_capex_annualized, calc_opex_annualized

__author__ = "Shanshan Hsieh"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# technical model

def calc_chiller_main(mdot_chw_kgpers, T_chw_sup_K, T_chw_re_K, T_hw_in_C, T_ground_K, absorption_chiller):
    """
    This model calculates the operation conditions of the absorption chiller given the chilled water loads in
    evaporators and the hot water inlet temperature in the generator (desorber).
    This is an empirical model using characteristic equation method developed by _[Kuhn A. & Ziegler F., 2005].
    The parameters of each absorption chiller can be derived from experiments or performance curves from manufacturer's
    catalog, more details are described in _[Puig-Arnavat M. et al, 2010].
    Assumptions: constant external flow rates (chilled water at the evaporator, cooling water at the condenser and
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
    :param locator: locator class
    :return:
    ..[Kuhn A. & Ziegler F., 2005] Operational results of a 10kW absorption chiller and adaptation of the characteristic
    equation. In: Proceedings of the interantional conference solar air conditioning. Bad Staffelstein, Germany: 2005.
    ..[Puig-Arnavat M. et al, 2010] Analysis and parameter identification for characteristic equations of single- and
    double-effect absorption chillers by means of multivariable regression. Int J Refrig: 2010.
    """
    chiller_prop = absorption_chiller.chiller_prop # get data from the class
    # create a dict of input operating conditions
    input_conditions = {'T_chw_sup_K': T_chw_sup_K,
                        'T_chw_re_K': T_chw_re_K,
                        'T_hw_in_C': T_hw_in_C,
                        'T_ground_K': T_ground_K}
    mcp_chw_WperK = mdot_chw_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK
    q_chw_total_W = mcp_chw_WperK * (T_chw_re_K - T_chw_sup_K)

    if np.isclose(q_chw_total_W, 0.0):
        wdot_W = 0.0
        q_cw_W = 0.0
        q_hw_W = 0.0
        T_hw_out_C = np.nan
        EER = 0.0
        input_conditions['q_chw_W'] = 0.0
    else:
        min_chiller_size_W = min(chiller_prop['cap_min'].values)
        max_chiller_size_W = max(chiller_prop['cap_max'].values)
        # get chiller properties and input conditions according to load
        if q_chw_total_W < min_chiller_size_W:
            # get chiller property according to load
            chiller_prop = chiller_prop[chiller_prop['cap_min'] == min_chiller_size_W]
            # operate at minimum load
            number_of_chillers_activated = 1.0  # only activate one chiller
            input_conditions['q_chw_W'] = chiller_prop['cap_min'].values  # minimum load
        elif q_chw_total_W <= max_chiller_size_W:
            # get chiller property according to load
            chiller_prop = chiller_prop[(chiller_prop['cap_min'] <= q_chw_total_W) &
                                        (chiller_prop['cap_max'] >= q_chw_total_W)]
            # operate one chiller at the cooling load
            number_of_chillers_activated = 1.0  # only activate one chiller
            input_conditions['q_chw_W'] = q_chw_total_W # operate at the chilled water load
        else:
            # get chiller property according to load
            chiller_prop = chiller_prop[chiller_prop['cap_max'] == max_chiller_size_W]
            # distribute loads to multiple chillers
            number_of_chillers_activated = q_chw_total_W / max_chiller_size_W
            # operate at maximum load
            input_conditions['q_chw_W'] = max(chiller_prop['cap_max'].values)

        absorption_chiller.update_data(chiller_prop)
        operating_conditions = calc_operating_conditions(absorption_chiller, input_conditions)

        # calculate chiller outputs
        wdot_W = calc_power_demand(input_conditions['q_chw_W'], chiller_prop) * number_of_chillers_activated
        q_cw_W = operating_conditions['q_cw_W'] * number_of_chillers_activated
        q_hw_W = operating_conditions['q_hw_W'] * number_of_chillers_activated
        T_hw_out_C = operating_conditions['T_hw_out_C']
        EER = q_chw_total_W / (q_hw_W + wdot_W)

        if T_hw_out_C < 0.0 :
            print ('T_hw_out_C = ', T_hw_out_C, ' incorrect condition, check absorption chiller script.')

    chiller_operation = {'wdot_W': wdot_W, 'q_cw_W': q_cw_W, 'q_hw_W': q_hw_W, 'T_hw_out_C': T_hw_out_C,
                         'q_chw_W': q_chw_total_W, 'EER': EER}

    return chiller_operation


def calc_operating_conditions(absorption_chiller, input_conditions):
    """
    Calculates chiller operating conditions at given input conditions by solving the characteristic equations and the
    energy balance equations. This method is adapted from _[Kuhn A. & Ziegler F., 2005].
    The heat rejection to cooling tower is approximated with the energy balance:
    Q(condenser) + Q(absorber) = Q(generator) + Q(evaporator)

    :param AbsorptionChiller chiller_prop: parameters in the characteristic equations and the external flow rates.
    :param input_conditions:
    :type input_conditions: dict
    :return: a dict with operating conditions of the chilled water, cooling water and hot water loops in a absorption
             chiller.

    To improve speed, the system of equations was solved using sympy for the output variable ``q_hw_kW`` which is
    then used to compute the remaining output variables. The following code was used to create the expression to
    calculate ``q_hw_kW`` with::

        # use symbolic computation to derive a formula for q_hw_kW:

        # first, make sure all the variables are sympy symbols:
        T_chw_in_C, T_chw_out_C, T_cw_in_C, T_hw_in_C, mcp_cw_kWperK, mcp_hw_kWperK, q_chw_kW = sympy.symbols(
            "T_chw_in_C, T_chw_out_C, T_cw_in_C, T_hw_in_C, mcp_cw_kWperK, mcp_hw_kWperK, q_chw_kW")
        T_hw_out_C, T_cw_out_C, q_hw_kW = sympy.symbols('T_hw_out_C, T_cw_out_C, q_hw_kW')
        a_e, a_g, e_e, e_g, r_e, r_g, s_e, s_g = sympy.symbols("a_e, a_g, e_e, e_g, r_e, r_g, s_e, s_g")
        ddt_e, ddt_g = sympy.symbols("ddt_e, ddt_g")

        # the system of equations:
        eq_e = s_e * ddt_e + r_e - q_chw_kW
        eq_ddt_e = ((T_hw_in_C + T_hw_out_C) / 2.0
                    + a_e * (T_cw_in_C + T_cw_out_C) / 2.0
                    + e_e * (T_chw_in_C + T_chw_out_C) / 2.0
                    - ddt_e)
        eq_g = s_g * ddt_g + r_g - q_hw_kW
        eq_ddt_g = ((T_hw_in_C + T_hw_out_C) / 2.0
                    + a_g * (T_cw_in_C
                    + T_cw_out_C) / 2.0
                    + e_g * (T_chw_in_C + T_chw_out_C) / 2.0
                    - ddt_g)
        eq_bal_g = (T_hw_in_C - T_hw_out_C) - q_hw_kW / mcp_hw_kWperK

        # solve the system of equations with sympy
        eq_sys = [eq_e, eq_g, eq_bal_g, eq_ddt_e, eq_ddt_g]
        unknown_variables = (T_hw_out_C, T_cw_out_C, q_hw_kW, ddt_e, ddt_g)

        a, b = sympy.linear_eq_to_matrix(eq_sys, unknown_variables)
        T_hw_out_C, T_cw_out_C, q_hw_kW, ddt_e, ddt_g = tuple(*sympy.linsolve(eq_sys, unknown_variables))

        q_hw_kW.simplify()

    ..[Kuhn A. & Ziegler F., 2005] Operational results of a 10kW absorption chiller and adaptation of the characteristic
    equation. In: Proceedings of the interantional conference solar air conditioning. Bad Staffelstein, Germany: 2005.
    """
    # external water circuits (e: chilled water, ac: cooling water, d: hot water)
    T_hw_in_C = input_conditions['T_hw_in_C']
    T_cw_in_C = input_conditions['T_ground_K'] - 273.0  # condenser water inlet temperature
    T_chw_in_C = input_conditions['T_chw_re_K'] - 273.0  # inlet to the evaporator
    T_chw_out_C = input_conditions['T_chw_sup_K'] - 273.0  # outlet from the evaporator
    q_chw_kW = input_conditions['q_chw_W'] / 1000  # cooling load ata the evaporator
    m_cw_kgpers = absorption_chiller.m_cw_kgpers  # external flow rate of cooling water at the condenser and absorber
    m_hw_kgpers = absorption_chiller.m_hw_kgpers  # external flow rate of hot water at the generator
    mcp_cw_kWperK = m_cw_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK / 1000
    mcp_hw_kWperK = m_hw_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK / 1000

    # chiller_props (these are constants from the Absorption_chiller sheet in systems.xls)
    s_e = absorption_chiller.s_e
    r_e = absorption_chiller.r_e
    s_g = absorption_chiller.s_g
    r_g = absorption_chiller.r_g
    a_e = absorption_chiller.a_e
    e_e = absorption_chiller.e_e
    a_g = absorption_chiller.a_g
    e_g = absorption_chiller.e_g

    # variables to solve
    # T_hw_out_C, T_cw_out_C, q_hw_kW, ddt_e, ddt_g = sympy.symbols('T_hw_out_C T_cw_out_C q_hw_kW , ddt_e, ddt_g')
    #
    # # systems of equations to solve
    # eq_e = s_e * ddt_e + r_e - q_chw_kW
    # eq_ddt_e = ((T_hw_in_C + T_hw_out_C) / 2.0 + a_e * (T_cw_in_C + T_cw_out_C) / 2.0 + e_e * (T_chw_in_C + T_chw_out_C) / 2.0 - ddt_e)
    # eq_g = s_g * ddt_g + r_g - q_hw_kW
    # eq_ddt_g = ((T_hw_in_C + T_hw_out_C) / 2.0 + a_g * (T_cw_in_C + T_cw_out_C) / 2.0 + e_g * (T_chw_in_C + T_chw_out_C) / 2.0- ddt_g)
    # eq_bal_g = (T_hw_in_C - T_hw_out_C) - q_hw_kW / mcp_hw_kWperK
    #
    # # solve the system of equations with sympy
    # eq_sys = [eq_e, eq_g, eq_bal_g, eq_ddt_e, eq_ddt_g]
    # unknown_variables = (T_hw_out_C, T_cw_out_C, q_hw_kW, ddt_e, ddt_g)
    # (T_hw_out_C, T_cw_out_C, q_hw_kW, ddt_e, ddt_g) = tuple(*sympy.linsolve(eq_sys, unknown_variables))

    # a = np.array([
    #     [0, 0, 0, s_e, 0],
    #     [0, 0, -1, 0, s_g],
    #     [-1, 0, -1 / mcp_hw_kWperK, 0, 0],
    #     [0.5, 0, 0, -1, 0],
    #     [0.5, 0, 0, 0, -1]])
    # b = np.array([
    #     [q_chw_kW - r_e],
    #     [-r_g],
    #     [-T_hw_in_C],
    #     [-0.5 * T_hw_in_C - 0.5 * e_e * (T_chw_in_C + T_chw_out_C)],
    #     [-0.5 * T_hw_in_C - 0.5 * e_g * (T_chw_in_C + T_chw_out_C)]])

    # the below equation for q_hw_kW was created with sympy.linsolve using symbols for all the variables.
    q_hw_kW = ((r_g * s_e * (0.5 * a_e * mcp_hw_kWperK + 0.25 * s_g * (a_e - a_g))
                + s_g * (0.5 * a_g * mcp_hw_kWperK * (q_chw_kW - r_e)
                         + s_e * (0.5 * mcp_hw_kWperK
                                  * (a_e * (0.5 * T_chw_in_C * e_g
                                            + 0.5 * T_chw_out_C * e_g
                                            + 0.5 * T_cw_in_C * a_g
                                            + 1.0 * T_hw_in_C)
                                     - a_g * (0.5 * T_chw_in_C * e_e
                                              + 0.5 * T_chw_out_C * e_e
                                              + 0.5 * T_cw_in_C * a_e
                                              + 1.0 * T_hw_in_C))
                                  - 0.25 * r_g * (a_e - a_g))))
               / (s_e * (0.5 * a_e * mcp_hw_kWperK + 0.25 * s_g * (a_e - a_g))))

    # calculate results
    q_cw_kW = q_hw_kW + q_chw_kW  # Q(condenser) + Q(absorber)
    T_hw_out_C = T_hw_in_C - q_hw_kW / mcp_hw_kWperK
    T_cw_out_C = T_cw_in_C + q_cw_kW / mcp_cw_kWperK  # TODO: set upper bound of the chiller operation

    return {'T_hw_out_C': T_hw_out_C,
            'T_cw_out_C': T_cw_out_C,
            'q_chw_W': q_chw_kW * 1000,
            'q_hw_W': q_hw_kW * 1000,
            'q_cw_W': q_cw_kW * 1000}


def calc_power_demand(q_chw_W, chiller_prop):
    """
    Calculates the power demand of the solution and refrigeration pumps in absorption chillers.
    Linear equations derived from manufacturer's catalog _[Broad Air Conditioning, 2018].
    :param q_chw_W:
    :param ACH_type:
    :return:

    ..[Broad Air Conditioning, 2018] BROAD XII NON-ELECTRIC CHILLER. (2018).
    etrieved from https://www.broadusa.net/en/wp-content/uploads/2018/12/BROAD-XII-US-Catalog2018-12.pdf

    """
    ach_type = chiller_prop['type'].values[0]
    if ach_type == 'single':
        w_dot_W = 0.0028 + 2941
    else:
        w_dot_W = 0.0021 * q_chw_W + 2757 # assuming the same for double and triple effect chillers

    return w_dot_W

# Investment costs


def calc_Cinv_ACH(Q_nom_W, Absorption_chiller_cost_data, ACH_type):
    """
    Annualized investment costs for the vapor compressor chiller
    :type Q_nom_W : float
    :param Q_nom_W: peak cooling demand in [W]
    :returns InvCa: annualized chiller investment cost in CHF/a
    :rtype InvCa: float
    """
    Capex_a_ACH_USD = 0
    Opex_fixed_ACH_USD = 0
    Capex_ACH_USD = 0
    if Q_nom_W > 0:
        Absorption_chiller_cost_data = Absorption_chiller_cost_data[Absorption_chiller_cost_data['type'] == ACH_type]
        max_chiller_size = max(Absorption_chiller_cost_data['cap_max'].values)

        Q_nom_W = Absorption_chiller_cost_data['cap_min'].values.min() if Q_nom_W < Absorption_chiller_cost_data[
            'cap_min'].values.min() else Q_nom_W  # minimum technology size


        if Q_nom_W <= max_chiller_size:

            Absorption_chiller_cost_data = Absorption_chiller_cost_data[
                (Absorption_chiller_cost_data['cap_min'] <= Q_nom_W) & (
                        Absorption_chiller_cost_data[
                            'cap_max'] > Q_nom_W)]  # keep properties of the associated capacity
            Inv_a = Absorption_chiller_cost_data.iloc[0]['a']
            Inv_b = Absorption_chiller_cost_data.iloc[0]['b']
            Inv_c = Absorption_chiller_cost_data.iloc[0]['c']
            Inv_d = Absorption_chiller_cost_data.iloc[0]['d']
            Inv_e = Absorption_chiller_cost_data.iloc[0]['e']
            Inv_IR = Absorption_chiller_cost_data.iloc[0]['IR_%']
            Inv_LT = Absorption_chiller_cost_data.iloc[0]['LT_yr']
            Inv_OM = Absorption_chiller_cost_data.iloc[0]['O&M_%'] / 100

            InvC = Inv_a + Inv_b * (Q_nom_W) ** Inv_c + (Inv_d + Inv_e * Q_nom_W) * log(Q_nom_W)
            Capex_a_ACH_USD = calc_capex_annualized(InvC, Inv_IR, Inv_LT)
            Opex_fixed_ACH_USD = InvC * Inv_OM
            Capex_ACH_USD = InvC
        else:
            number_of_chillers = int(ceil(Q_nom_W / max_chiller_size))
            Q_nom_each_chiller = Q_nom_W / number_of_chillers
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
                Inv_IR = Absorption_chiller_cost_data.iloc[0]['IR_%']
                Inv_LT = Absorption_chiller_cost_data.iloc[0]['LT_yr']
                Inv_OM = Absorption_chiller_cost_data.iloc[0]['O&M_%'] / 100

                InvC = Inv_a + Inv_b * (Q_nom_each_chiller) ** Inv_c + (Inv_d + Inv_e * Q_nom_each_chiller) * log(Q_nom_each_chiller)
                Capex_a1 = calc_capex_annualized(InvC, Inv_IR, Inv_LT)
                Capex_a_ACH_USD = Capex_a_ACH_USD + Capex_a1
                Opex_fixed_ACH_USD = Opex_fixed_ACH_USD + InvC * Inv_OM
                Capex_ACH_USD = Capex_ACH_USD + InvC

    return Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD


class AbsorptionChiller(object):
    __slots__ = ["code", "chiller_prop", "m_cw_kgpers", "m_hw_kgpers",
                 "s_e", "r_e", "s_g", "r_g", "a_e", "e_e", "a_g", "e_g"]

    def __init__(self, chiller_prop, ACH_type):
        self.chiller_prop = chiller_prop[chiller_prop['type'] == ACH_type]

        # copy first row to self for faster lookup (avoid pandas __getitem__ in tight loops)
        self.code = chiller_prop['code'].values[0]
        # external flow rate of cooling water at the condenser and absorber
        self.m_cw_kgpers = chiller_prop['m_cw'].values[0]

        # external flow rate of hot water at the generator
        self.m_hw_kgpers = chiller_prop['m_hw'].values[0]
        self.s_e = chiller_prop['s_e'].values[0]
        self.r_e = chiller_prop['r_e'].values[0]
        self.s_g = chiller_prop['s_g'].values[0]
        self.r_g = chiller_prop['r_g'].values[0]
        self.a_e = chiller_prop['a_e'].values[0]
        self.e_e = chiller_prop['e_e'].values[0]
        self.a_g = chiller_prop['a_g'].values[0]
        self.e_g = chiller_prop['e_g'].values[0]

    def update_data(self, chiller_prop):
        """Due to how AbsorptionChiller is currently used (FIXME: can we fix this?), we somedimes need to update
        the instance variables from the databaframe chiller_prop.
        """
        if self.code != chiller_prop['code'].values[0]:
            # only update if new code...
            # print("Updating chiller_prop data! old code: {0}, new code: {1}".format(self.code, chiller_prop['code'].values[0]))
            self.code = chiller_prop['code'].values[0]
            self.m_cw_kgpers = chiller_prop['m_cw'].values[0]
            self.m_hw_kgpers = chiller_prop['m_hw'].values[0]
            self.s_e = chiller_prop['s_e'].values[0]
            self.r_e = chiller_prop['r_e'].values[0]
            self.s_g = chiller_prop['s_g'].values[0]
            self.r_g = chiller_prop['r_g'].values[0]
            self.a_e = chiller_prop['a_e'].values[0]
            self.e_e = chiller_prop['e_e'].values[0]
            self.a_g = chiller_prop['a_g'].values[0]
            self.e_g = chiller_prop['e_g'].values[0]


def main(config):
    """
    run the whole preprocessing routine
    test case 1) q_hw_W = 24213, q_chw_W = 20088, EER = 0.829, T_hw_out_C = 67.22 _[Kuhn, 2011]
    test case 2) q_hw_W = 824105, q_chw_W = 1163011, EER = 1.41, T_hw_out_C = 165.93 _[Shirazi, 2016]
    test case 3) q_hw_W = 623379, q_chw_W = 1163430, EER = 1.87, T_hw_out_C = 195.10 _[Shirazi, 2016]

    ..[Kuhn A., Ozgur-Popanda C., & Ziegler F., 2011] A 10kW Indirectly Fired Absorption Heat Pump: Concepts for a
    reversible operation. 10th International Heat Pump Conference, 2011.
    ..[Shirazi A., Taylor R.A., White S.D., Morrison G.L.] A systematic parametric study and feasibility assessment
    of solar-assisted single-effect, double-effect, and triple-effect absorption chillers for heating and cooling
    applications. Energy Conversion and Management, 2016

    """
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    # Input parameters for test cases
    case_1_dict = {'mdot_chw_kgpers':0.8, 'T_chw_sup_K': 280.0, 'T_chw_re_K': 286.0, 'T_hw_in_C': 84.6, 'ACH_type': 'single'}
    case_2_dict = {'mdot_chw_kgpers': 39.7, 'T_chw_sup_K': 280.0, 'T_chw_re_K': 287.0, 'T_hw_in_C': 180,
                   'ACH_type': 'double'}
    case_3_dict = {'mdot_chw_kgpers': 55.6, 'T_chw_sup_K': 280.0, 'T_chw_re_K': 285.0, 'T_hw_in_C': 210,
                   'ACH_type': 'triple'}

    # Unpack parameters
    case_dict = case_1_dict
    mdot_chw_kgpers = case_dict['mdot_chw_kgpers']
    T_chw_sup_K = case_dict['T_chw_sup_K']
    T_chw_re_K = case_dict['T_chw_re_K']
    T_hw_in_C = case_dict['T_hw_in_C']
    T_ground_K = 300
    ach_type = case_dict['ACH_type']

    chiller_prop = AbsorptionChiller(pd.read_excel(locator.get_database_conversion_systems(), sheet_name="Absorption_chiller"), ach_type)

    chiller_operation = calc_chiller_main(mdot_chw_kgpers, T_chw_sup_K, T_chw_re_K, T_hw_in_C, T_ground_K, chiller_prop)
    print(chiller_operation)
    print('test_decentralized_buildings_cooling() succeeded. Please doubel check results in the description.')


if __name__ == '__main__':
    main(cea.config.Configuration())


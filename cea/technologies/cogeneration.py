"""
cogeneration (combined heat and power)
"""

from __future__ import division
import numpy as np
from scipy import interpolate
import scipy
import pandas as pd
from math import log
from cea.optimization.constants import GT_MIN_PART_LOAD, LHV_NG, LHV_BG, GT_MAX_SIZE, CC_AIRRATIO, CC_EXIT_T_BG, \
    CC_EXIT_T_NG, ST_DELTA_T, CC_DELTA_T_DH, ST_GEN_ETA
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.technologies.constants import SPEC_VOLUME_STEAM

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# ===========================
# Combined Cycle Gas Turbine
# ===========================


def calc_cop_CCGT(GT_size_W, T_sup_K, fuel_type, prices, lca_hour):
    """
    This function calcualates the COP of a combined cycle, the gas turbine (GT) exhaust gas is used by
    the steam turbine (ST) to generate electricity and heat.
    This function iterates the combined cycle operation between its nominal capacity and minimum load and generate
    linear functions of the GT operation.
    The generated function calculates operation points and associated costs of the cogeneration at given
    thermal load (Q_therm_requested).
    How to use the return functions : input Q_therm_requested into the output interpolation functions
    Conditions: not below or above boundaries Q_therm_min & Q_therm_max

    :type GT_size_W : float
    :param GT_size_W: Nominal capacity of Gas Turbine (only GT not cogeneration)
    :type T_sup_K : float
    :param T_sup_K: CHP plant supply temperature to DHN or to absorption chillers
    :type fuel_type : string
    :param fuel_type: type of fuel, either "NG" or "BG"
    :rtype wdot_interpol : function
    :returns wdot_interpol: interpolation function for part load electricity requirement for given Q_therm_requested
    :rtype Q_used_prim_interpol: function
    :returns Q_used_prim_interpol: interpolation function, primary energy used for given Q_therm_requested
    :rtype fuel_cost_per_Wh_th_interpol_with_q_output : function
    :returns fuel_cost_per_Wh_th_interpol_with_q_output: interpolation function, operation cost per thermal energy generated at Q_therm_requested
    :rtype Q_therm_min : float
    :returns Q_therm_min: minimum thermal energy output
    :rtype Q_therm_max : float
    :returns Q_therm_max: maximum thermal energy output
    :rtype eta_el_interpol_with_q_input: function
    :returns eta_el_interpol_with_q_input: interpolation function, electrical efficiency at Q_therm_requested

    ..[C. Weber, 2008] C.Weber, Multi-objective design and optimization of district energy systems including
    polygeneration energy conversion technologies., PhD Thesis, EPFL
    """

    it_len = 50

    # create empty arrays
    range_el_output_CC_W = np.zeros(it_len)
    range_q_output_CC_W = np.zeros(it_len)
    range_eta_el_CC = np.zeros(it_len)
    range_eta_thermal_CC = np.zeros(it_len)
    range_q_input_CC_W = np.zeros(it_len)
    range_op_cost_per_Wh_th = np.zeros(it_len)

    # create range of electricity output from the GT between the minimum and nominal load
    range_el_output_from_GT_W = np.linspace(GT_size_W * GT_MIN_PART_LOAD, GT_size_W, it_len)

    # calculate the operation data at different electricity load
    for i in range(len(range_el_output_from_GT_W)):
        el_output_from_GT_W = range_el_output_from_GT_W[i]

        # combine cycle operation
        CC_operation = calc_CC_operation(el_output_from_GT_W, GT_size_W, fuel_type, T_sup_K)
        range_el_output_CC_W[i] = CC_operation['el_output_W']  # Electricity output from the combined cycle
        range_q_output_CC_W[i] = CC_operation['q_output_ST_W']  # Thermal output from the combined cycle
        range_eta_el_CC[i] = CC_operation['eta_el']  # el. efficiency
        range_eta_thermal_CC[i] = CC_operation['eta_thermal']  # thermal efficiency

        range_q_input_CC_W[i] = range_q_output_CC_W[i] / range_eta_thermal_CC[i]  # thermal energy input
        range_op_cost_per_Wh_th[i] = (range_q_input_CC_W[i] * prices.NG_PRICE - range_el_output_CC_W[
            i] * lca_hour) / range_q_output_CC_W[i]

    # create interpolation functions as a function of heat output
    el_output_interpol_with_q_output_W = interpolate.interp1d(range_q_output_CC_W, range_el_output_from_GT_W,
                                                              kind="linear")
    q_input_interpol_with_q_output_W = interpolate.interp1d(range_q_output_CC_W, range_q_input_CC_W, kind="linear")
    op_cost_per_Wh_th_interpol_with_q_output = interpolate.interp1d(range_q_output_CC_W, range_op_cost_per_Wh_th,
                                                                      kind="linear")
    # create interpolation functions as a function of thermal energy input
    eta_el_interpol_with_q_input = interpolate.interp1d(range_q_input_CC_W, range_eta_el_CC,
                                                        kind="linear")

    q_output_min_W = min(range_q_output_CC_W)
    q_output_max_W = max(range_q_output_CC_W)

    return {'el_output_fn_q_input_W': el_output_interpol_with_q_output_W,
            'q_input_fn_q_output_W': q_input_interpol_with_q_output_W,
            'fuel_cost_per_Wh_th_fn_q_output_W': op_cost_per_Wh_th_interpol_with_q_output,
            'q_output_min_W': q_output_min_W, 'q_output_max_W': q_output_max_W,
            'eta_el_fn_q_input': eta_el_interpol_with_q_input}


def calc_CC_operation(el_output_from_GT_W, GT_size_W, fuel_type, T_sup_K):
    """
    Operation Function of Combined Cycle at given electricity input to run the gas turbine (el_input_W).
    The gas turbine (GT) exhaust gas is used by the steam turbine (ST).
    :type el_output_from_GT_W : float
    :param el_output_from_GT_W: Electricity input to run the gas turbine (only GT output, not CC output!)
    :type GT_size_W : float
    :param GT_size_W: size of the gas turbine and (not CC)(P_el_max)
    :type fuel_type : string
    :param fuel_type: fuel used, either 'NG' (natural gas) or 'BG' (biogas)
    :type T_sup_K : float
    :param T_sup_K: plant supply temperature to district heating network (hot) or absorption chiller
    :rtype wtot : float
    :returns wtot: total electric power output from the combined cycle (both GT + ST !)
    :rtype qdot : float
    :returns qdot: thermal output from teh combined cycle
    :rtype eta_el : float
    :returns eta_el: total electric efficiency
    :rtype eta_thermal : float
    :returns eta_thermal: total thermal efficiency
    :rtype eta_total : float
    :returns eta_total: sum of total electric and thermal efficiency
    """

    (eta0, m0_exhaust_GT_kgpers) = calc_GT_operation_fullload(GT_size_W, fuel_type)
    (eta, m_exhaust_GT_kgpers, T_exhaust_GT_K, m_fuel_kgpers) = calc_GT_operation_partload(el_output_from_GT_W,
                                                                                           GT_size_W, eta0,
                                                                                           m0_exhaust_GT_kgpers,
                                                                                           fuel_type)

    (q_output_ST_W, el_output_ST_W) = calc_ST_operation(m_exhaust_GT_kgpers, T_exhaust_GT_K, T_sup_K, fuel_type)

    LHV = LHV_NG if fuel_type == 'NG' else LHV_BG  # read LHV of NG or BG

    eta_el = (el_output_from_GT_W + el_output_ST_W) / (m_fuel_kgpers * LHV)
    eta_thermal = q_output_ST_W / (m_fuel_kgpers * LHV)
    eta_total = eta_el + eta_thermal
    el_output_W = el_output_ST_W + el_output_from_GT_W

    return {'el_output_W': el_output_W, 'q_output_ST_W': q_output_ST_W, 'eta_el': eta_el, 'eta_thermal': eta_thermal,
            'eta_total': eta_total}


def calc_GT_operation_fullload(gt_size_W, fuel_type):
    """
    Calculates gas turbine efficiency and exhaust gas mass flow rate at full load.

    :type gt_size_W : float
    :param gt_size_W: nominal capacity of the gas turbine
    :type fuel_type : string
    :param fuel_type: fuel used, either NG (Natural Gas) or BG (Biogas)
    :rtype eta0 : float
    :returns eta0: efficiency at full load
    :rtype mdot0 : float
    :returns mdot0: exhaust gas mass flow rate at full load

    ..[C. Weber, 2008] C.Weber, Multi-objective design and optimization of district energy systems including
    polygeneration energy conversion technologies., PhD Thesis, EPFL
    """
    if gt_size_W < GT_MAX_SIZE + 0.001:
        if gt_size_W == 0:
            eta0 = 0.01
        else:
            eta0 = 0.0196 * scipy.log(gt_size_W * 1E-3) + 0.1317  # (4.4) [C. Weber, 2008]_

        LHV = LHV_NG if fuel_type == 'NG' else LHV_BG  # read LHV of NG or BG
        mdot_fuel_kgpers = gt_size_W / (eta0 * LHV)

        if fuel_type == 'NG':
            mdot0_exhaust_kgpers = (103.7 * 44E-3 + 196.2 * 18E-3 + 761.4 * 28E-3 + 200.5 * 32E-3 * (CC_AIRRATIO - 1) +
                                    200.5 * 3.773 * 28E-3 * (
                                        CC_AIRRATIO - 1)) * mdot_fuel_kgpers / 1.8156  # TODO: reference?
        else:
            mdot0_exhaust_kgpers = (98.5 * 44E-3 + 116 * 18E-3 + 436.8 * 28E-3 + 115.5 * 32E-3 * (CC_AIRRATIO - 1) +
                                    115.5 * 3.773 * 28E-3 * (
                                        CC_AIRRATIO - 1)) * mdot_fuel_kgpers / 2.754  # TODO: reference?
    else:
        gt_size_W = GT_MAX_SIZE
        if gt_size_W == 0:
            eta0 = 0.01
        else:
            eta0 = 0.0196 * scipy.log(gt_size_W * 1E-3) + 0.1317  # [C. Weber, 2008]_

        LHV = LHV_NG if fuel_type == 'NG' else LHV_BG  # read LHV of NG or BG
        mdot_fuel_kgpers = gt_size_W / (eta0 * LHV)

        if fuel_type == 'NG':
            mdot0_exhaust_kgpers = (103.7 * 44E-3 + 196.2 * 18E-3 + 761.4 * 28E-3 + 200.5 * 32E-3 * (CC_AIRRATIO - 1) +
                                    200.5 * 3.773 * 28E-3 * (
                                        CC_AIRRATIO - 1)) * mdot_fuel_kgpers / 1.8156  # TODO: reference?
        else:
            mdot0_exhaust_kgpers = (98.5 * 44E-3 + 116 * 18E-3 + 436.8 * 28E-3 + 115.5 * 32E-3 * (CC_AIRRATIO - 1) +
                                    115.5 * 3.773 * 28E-3 * (
                                        CC_AIRRATIO - 1)) * mdot_fuel_kgpers / 2.754  # TODO: reference?

    return eta0, mdot0_exhaust_kgpers


def calc_GT_operation_partload(wdot_W, gt_size_W, eta0, m0_exhaust_from_GT_kgpers, fuel_type):
    """
    Calculates GT operational parameters at part load

    :type wdot_W : float
    :param wdot_W: GT electric output (load)
    :type gt_size_W : float
    :param gt_size_W: Maximum electric load that is demanded to the gas turbine
    :type eta0 : float
    :param eta0: GT electric efficiency at full-load
    :type m0_exhaust_from_GT_kgpers : float
    :param m0_exhaust_from_GT_kgpers: GT exhaust gas mass flow at full-load
    :type fuel_type : string
    :param fuel_type: fuel used, either 'NG' (natural gas) or 'BG' (biogas)
    :rtype eta : float
    :returns eta: GT part-load electric efficiency
    :rtype mdot : float
    :returns mdot: GT part-load exhaust gas mass flow rate
    :rtype T_exhaust_GT_K : float
    :returns T_exhaust_GT_K: exhaust gas temperature
    :rtype mdotfuel : float
    :returns mdotfuel: mass flow rate of fuel(gas) requirement
    ..[C. Weber, 2008] C.Weber, Multi-objective design and optimization of district energy systems including
    polygeneration energy conversion technologies., PhD Thesis, EPFL
    """
    assert wdot_W <= gt_size_W

    if fuel_type == 'NG':
        exitT = CC_EXIT_T_NG
        LHV = LHV_NG
    else:
        exitT = CC_EXIT_T_BG
        LHV = LHV_BG

    part_load_factor = (wdot_W + 1) / gt_size_W  # avoid calculation errors # TODO: reference?
    if part_load_factor < GT_MIN_PART_LOAD:
        raise ValueError('The load (', wdot_W, ')is lower than minimum part load (', gt_size_W * GT_MIN_PART_LOAD, ').')

    eta = (0.4089 + 0.9624 * part_load_factor - 0.3726 * part_load_factor ** 2) * eta0  # (4.12) [C. Weber, 2008]_
    # mdot = (0.9934 + 0.0066 * part_load_factor) * mdot0
    T_exhaust_GT_K = (0.7379 + 0.2621 * part_load_factor) * exitT  # (4.14) [C. Weber, 2008]_
    m_fuel_kgpers = wdot_W / (eta * LHV)

    if fuel_type == 'NG':
        m_exhaust_GT_kgpers = (103.7 * 44E-3 + 196.2 * 18E-3 + 761.4 * 28E-3 + 200.5 * 32E-3 * (CC_AIRRATIO - 1) +
                               200.5 * 3.773 * 28E-3 * (CC_AIRRATIO - 1)) * m_fuel_kgpers / 1.8156  # TODO: reference?

    else:
        m_exhaust_GT_kgpers = (98.5 * 44E-3 + 116 * 18E-3 + 436.8 * 28E-3 + 115.5 * 32E-3 * (CC_AIRRATIO - 1) + \
                               115.5 * 3.773 * 28E-3 * (CC_AIRRATIO - 1)) * m_fuel_kgpers / 2.754  # TODO: reference?

    return eta, m_exhaust_GT_kgpers, T_exhaust_GT_K, m_fuel_kgpers


def calc_ST_operation(m_exhaust_GT_kgpers, T_exhaust_GT_K, T_sup_K, fuel_type):
    """
    Operation of a double pressure (LP,HP) steam turbine connected to a district heating network following
    [C. Weber, 2008]_
    :type m_exhaust_GT_kgpers : float
    :param m_exhaust_GT_kgpers: GT part-load exhaust gas mass flow rate
    :type T_exhaust_GT_K : float
    :param T_exhaust_GT_K: GT exhaust gas temperature
    :type T_sup_K : float
    :param T_sup_K: plant supply temperature to district heating network (hot)
    :param fuel_type: fuel used, either 'NG' (natural gas) or 'BG' (biogas)
    :rtype qdot : float
    :returns qdot: heat power supplied to the DHN
    :rtype wdotfin : float
    :returns wdotfin: electric power generated from the steam cycle
    ..[C. Weber, 2008] C.Weber, Multi-objective design and optimization of district energy systems including
    polygeneration energy conversion technologies., PhD Thesis, EPFL
    """

    # calaulate High Pressure (HP) and Low Pressure (LP) mass flow of a double pressure steam turbine
    temp_i_K = (0.9 * ((6 / 48.2) ** (0.4 / 1.4) - 1) + 1) * (T_exhaust_GT_K - ST_DELTA_T)
    if fuel_type == 'NG':
        Mexh = 103.7 * 44E-3 + 196.2 * 18E-3 + 761.4 * 28E-3 + 200.5 * (CC_AIRRATIO - 1) * 32E-3 \
               + 200.5 * (CC_AIRRATIO - 1) * 3.773 * 28E-3
        ncp_exh = 103.7 * 44 * 0.846 + 196.2 * 18 * 1.8723 + 761.4 * 28 * 1.039 \
                  + 200.5 * (CC_AIRRATIO - 1) * 32 * 0.918 + 200.5 * (CC_AIRRATIO - 1) * 3.773 * 28 * 1.039
        cp_exh = ncp_exh / Mexh  # J/kgK
    else:
        Mexh = 98.5 * 44E-3 + 116 * 18E-3 + 436.8 * 28E-3 + 115.5 * (CC_AIRRATIO - 1) * 32E-3 \
               + 115.5 * (CC_AIRRATIO - 1) * 3.773 * 28E-3
        ncp_exh = 98.5 * 44 * 0.846 + 116 * 18 * 1.8723 + 436.8 * 28 * 1.039 \
                  + 115.5 * (CC_AIRRATIO - 1) * 32 * 0.918 + 115.5 * (CC_AIRRATIO - 1) * 3.773 * 28 * 1.039
        cp_exh = ncp_exh / Mexh  # J/kgK

    a = np.array([[1653E3 + HEAT_CAPACITY_OF_WATER_JPERKGK * (T_exhaust_GT_K - ST_DELTA_T - 534.5), \
                   HEAT_CAPACITY_OF_WATER_JPERKGK * (temp_i_K - 534.5)], \
                  [HEAT_CAPACITY_OF_WATER_JPERKGK * (534.5 - 431.8), \
                   2085.8E3 + HEAT_CAPACITY_OF_WATER_JPERKGK * (534.5 - 431.8)]])
    b = np.array([m_exhaust_GT_kgpers * cp_exh * (T_exhaust_GT_K - (534.5 + ST_DELTA_T)), \
                  m_exhaust_GT_kgpers * cp_exh * (534.5 - 431.8)])
    [mdotHP_kgpers, mdotLP_kgpers] = np.linalg.solve(a, b)

    # calculate thermal output
    T_cond_0_K = T_sup_K + CC_DELTA_T_DH  # condensation temperature constrained by the DH network temperature
    pres0 = (0.0261 * (T_cond_0_K - 273) ** 2 - 2.1394 * (T_cond_0_K - 273) + 52.893) * 1E3

    delta_h_evap_Jperkg = (-2.4967 * (T_cond_0_K - 273) + 2507) * 1E3
    q_output_ST_W = (mdotHP_kgpers + mdotLP_kgpers) * delta_h_evap_Jperkg  # thermal output of ST

    # temp_c = (0.9 * ((pres0/48.2E5) ** (0.4/1.4) - 1) + 1) * (texh - gV.ST_deltaT)
    # qdot = (mdotHP + mdotLP) * (HEAT_CAPACITY_OF_WATER_JPERKGK * (temp_c - T_cond_0_K) + delta_h_evap_Jperkg)
    # presSTexit = pres0 + gV.ST_deltaP
    # wdotST = 0.9 / 18E-3 * 1.4 / 0.4 * 8.31 * \
    #         (mdotHP * 534.5 * ( (6/48.2) ** (0.4/1.4) - 1 )\
    #         + (mdotLP + mdotHP) * temp_i * ( (presSTexit/6E5) ** (0.4/1.4) - 1 ) )
    #
    # temp1 = (((6E5/pres0) ** (0.4/1.4) - 1) / 0.87 + 1) * T_cond_0_K
    # wdotcomp = 0.87 / 18E-3 * 1.4 / 0.4 * 8.31 * \
    #           (mdotHP * temp1 * ( (48.2/6) ** (0.4/1.4) - 1 )\
    #           + (mdotHP + mdotLP) * T_cond_0_K * ( (6E5/pres0) ** (0.4/1.4) - 1 ))


    # calculate electricity output
    h_HP_Jperkg = (2.5081 * (T_exhaust_GT_K - ST_DELTA_T - 273) + 2122.7) * 1E3  # J/kg
    h_LP_Jperkg = (2.3153 * (temp_i_K - 273) + 2314.7) * 1E3  # J/kg
    h_cond_Jperkg = (1.6979 * (T_cond_0_K - 273) + 2506.6) * 1E3  # J/kg

    el_produced_ST_W = mdotHP_kgpers * (h_HP_Jperkg - h_LP_Jperkg) + \
                       (mdotHP_kgpers + mdotLP_kgpers) * (h_LP_Jperkg - h_cond_Jperkg)  # turbine electricity output

    el_input_compressor_W = SPEC_VOLUME_STEAM * (
        mdotLP_kgpers * (6E5 - pres0) + (mdotHP_kgpers + mdotLP_kgpers) * (48.2E5 - 6E5))  # compressor electricity use

    el_output_ST_W = ST_GEN_ETA * (el_produced_ST_W - el_input_compressor_W)  # gross electricity production of turbine

    return q_output_ST_W, el_output_ST_W


# ===========================
# Fuel Cell
# ===========================

def calc_eta_FC(Q_load_W, Q_design_W, phi_threshold, approach_call):
    """
    Efficiency for operation of a SOFC (based on LHV of NG) including all auxiliary losses
    Valid for Q_load in range of 1-10 [kW_el]
    Modeled after:

        - **Approach A (NREL Approach)**:
          http://energy.gov/eere/fuelcells/distributedstationary-fuel-cell-systems
          and
          NREL : p.5  of [M. Zolot et al., 2004]_

        - **Approach B (Empiric Approach)**: [Iain Staffell]_

    :type Q_load_W : float
    :param Q_load_W: Load at each time step
    :type Q_design_W : float
    :param Q_design_W: Design Load of FC
    :type phi_threshold : float
    :param phi_threshold: where Maximum Efficiency is reached, used for Approach A
    :type approach_call : string
    :param appraoch_call: choose "A" or "B": A = NREL-Approach, B = Empiric Approach
    :rtype eta_el : float
    :returns eta_el: electric efficiency of FC (Lower Heating Value), in abs. numbers
    :rtype Q_fuel : float
    :returns Q_fuel: Heat demand from fuel (in Watt)

    ..[M. Zolot et al., 2004] M. Zolot et al., Analysis of Fuel Cell Hybridization and Implications for Energy Storage
    Devices, NREL, 4th International Advanced Automotive Battery.
    http://www.nrel.gov/vehiclesandfuels/energystorage/pdfs/36169.pdf
    ..[Iain Staffell, 2009] Iain Staffell, For Domestic Heat and Power: Are They Worth It?, PhD Thesis, Birmingham:
    University of Birmingham. http://etheses.bham.ac.uk/641/1/Staffell10PhD.pdf
    """
    phi = 0.0

    ## Approach A - NREL Approach
    if approach_call == "A":

        phi = float(Q_load_W) / float(Q_design_W)
        eta_max = 0.425  # from energy.gov

        if phi >= phi_threshold:  # from NREL-Shape
            eta_el = eta_max - ((1 / 6.0 * eta_max) / (1.0 - phi_threshold)) * abs(phi - phi_threshold)

        if phi < phi_threshold:
            if phi <= 118 / 520.0 * phi_threshold:
                eta_el = eta_max * 2 / 3 * (phi / (phi_threshold * 118 / 520.0))

            if phi < 0.5 * phi_threshold and phi >= 118 / 520.0 * phi_threshold:
                eta_el = eta_max * 2 / 3.0 + \
                         eta_max * 0.25 * (phi - phi_threshold * 118 / 520.0) / (phi_threshold * (0.5 - 118 / 520.0))

            if phi > 0.5 * phi_threshold and phi < phi_threshold:
                eta_el = eta_max * (2 / 3.0 + 0.25) + \
                         1 / 12.0 * eta_max * (phi - phi_threshold * 0.5) / (phi_threshold * (1 - 0.5))

        eta_therm_max = 0.45  # constant, after energy.gov

        if phi < phi_threshold:
            eta_therm = 0.5 * eta_therm_max * (phi / phi_threshold)

        else:
            eta_therm = 0.5 * eta_therm_max * (1 + eta_therm_max * ((phi - phi_threshold) / (1 - phi_threshold)))

    ## Approach B - Empiric Approach
    if approach_call == "B":

        if Q_design_W > 0:
            phi = float(Q_load_W) / float(Q_design_W)

        else:
            phi = 0

        eta_el_max = 0.39
        eta_therm_max = 0.58  # * 1.11 as this source gives eff. of HHV
        eta_el_score = -0.220 + 5.277 * phi - 9.127 * phi ** 2 + 7.172 * phi ** 3 - 2.103 * phi ** 4
        eta_therm_score = 0.9 - 0.07 * phi + 0.17 * phi ** 2

        eta_el = eta_el_max * eta_el_score
        eta_therm = eta_therm_max * eta_therm_score

        if phi < 0.2:
            eta_el = 0

    return eta_el, eta_therm


# investment and maintenance costs

def calc_Cinv_CCGT(CC_size_W, locator, config, technology=0):
    """
    Annualized investment costs for the Combined cycle
    :type CC_size_W : float
    :param CC_size_W: Electrical size of the CC
    :rtype InvCa : float
    :returns InvCa: annualized investment costs in CHF
    ..[C. Weber, 2008] C.Weber, Multi-objective design and optimization of district energy systems including
    polygeneration energy conversion technologies., PhD Thesis, EPFL
    """
    CCGT_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="CCGT")
    technology_code = list(set(CCGT_cost_data['code']))
    CCGT_cost_data[CCGT_cost_data['code'] == technology_code[technology]]
    # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
    # capacity for the corresponding technology from the database
    if CC_size_W < CCGT_cost_data['cap_min'][0]:
        CC_size_W = CCGT_cost_data['cap_min'][0]
    CCGT_cost_data = CCGT_cost_data[
        (CCGT_cost_data['cap_min'] <= CC_size_W) & (CCGT_cost_data['cap_max'] > CC_size_W)]

    Inv_a = CCGT_cost_data.iloc[0]['a']
    Inv_b = CCGT_cost_data.iloc[0]['b']
    Inv_c = CCGT_cost_data.iloc[0]['c']
    Inv_d = CCGT_cost_data.iloc[0]['d']
    Inv_e = CCGT_cost_data.iloc[0]['e']
    Inv_IR = (CCGT_cost_data.iloc[0]['IR_%']) / 100
    Inv_LT = CCGT_cost_data.iloc[0]['LT_yr']
    Inv_OM = CCGT_cost_data.iloc[0]['O&M_%'] / 100

    InvC = Inv_a + Inv_b * (CC_size_W) ** Inv_c + (Inv_d + Inv_e * CC_size_W) * log(CC_size_W)

    Capex_a_CCGT_USD = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
    Opex_fixed_CCGT_USD = Capex_a_CCGT_USD * Inv_OM
    Capex_CCGT_USD = InvC

    return Capex_a_CCGT_USD, Opex_fixed_CCGT_USD, Capex_CCGT_USD


def calc_Cinv_FC(P_design_W, locator, config, technology=0):
    """
    Calculates the investment cost of a Fuel Cell in CHF
    http://hexis.com/sites/default/files/media/publikationen/140623_hexis_galileo_ibb_profitpaket.pdf?utm_source=HEXIS+Mitarbeitende&utm_campaign=06d2c528a5-1_Newsletter_2014_Mitarbeitende_DE&utm_medium=email&utm_term=0_e97bc1703e-06d2c528a5-
    :type P_design_W : float
    :param P_design_W: Design thermal Load of Fuel Cell [W_th]
    :rtype InvCa: float
    :returns InvCa: annualized investment costs in CHF
    """
    FC_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="FC")
    technology_code = list(set(FC_cost_data['code']))
    FC_cost_data[FC_cost_data['code'] == technology_code[technology]]
    # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
    # capacity for the corresponding technology from the database
    if P_design_W < FC_cost_data['cap_min'][0]:
        P_design_W = FC_cost_data['cap_min'][0]
    FC_cost_data = FC_cost_data[
        (FC_cost_data['cap_min'] <= P_design_W) & (FC_cost_data['cap_max'] > P_design_W)]

    Inv_a = FC_cost_data.iloc[0]['a']
    Inv_b = FC_cost_data.iloc[0]['b']
    Inv_c = FC_cost_data.iloc[0]['c']
    Inv_d = FC_cost_data.iloc[0]['d']
    Inv_e = FC_cost_data.iloc[0]['e']
    Inv_IR = (FC_cost_data.iloc[0]['IR_%']) / 100
    Inv_LT = FC_cost_data.iloc[0]['LT_yr']
    Inv_OM = FC_cost_data.iloc[0]['O&M_%'] / 100

    InvC = Inv_a + Inv_b * (P_design_W) ** Inv_c + (Inv_d + Inv_e * P_design_W) * log(P_design_W)

    Capex_a_FC_USD = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
    Opex_fixed_FC_USD = Capex_a_FC_USD * Inv_OM
    Capex_FC_USD = InvC

    return Capex_a_FC_USD, Opex_fixed_FC_USD, Capex_FC_USD

# -*- coding: utf-8 -*-
"""
=========================================
Sensible space heating and space cooling loads
EN-13970
=========================================

"""
from __future__ import division
import numpy as np

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Shanshan Hsieh", "Daren Thomas", "Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


"""
=========================================
capacity of emission/control system
=========================================
"""


def calc_Qhs_Qcs_sys_max(Af, prop_HVAC):
    # TODO: Documentation
    # Refactored from CalcThermalLoads

    IC_max = -prop_HVAC['Qcsmax_Wm2'] * Af
    IH_max = prop_HVAC['Qhsmax_Wm2'] * Af
    return IC_max, IH_max


"""
=========================================
solar and heat gains
=========================================
"""


def calc_Qgain_sen(t, tsd, bpr, gv):
    # TODO

    # internal loads
    tsd['I_sol'][t], tsd['I_rad'][t] = calc_I_sol(t, bpr, tsd, gv)

    return tsd


def calc_Qgain_lat(people, X_ghp, sys_e_cooling, sys_e_heating):
    # TODO: Documentation
    # Refactored from CalcThermalLoads

    # X_ghp is the humidity gain from people in g/h

    if sys_e_heating == 'T3' or sys_e_cooling == 'T3':
        w_int = people * X_ghp / (1000 * 3600)  # kg/s
    else:
        w_int = 0

    return w_int

def calc_I_sol(t, bpr, tsd, gv):
    """
    This function calculates the net solar radiation (incident -reflected - re-irradiated) according to ISO 13790

    :param t: hour of the year
    :param bpr: building properties object
    :param tsd: time series dataframe
    :param gv: global variables class
    :return:
        I_sol: vector of net solar radiation to the building
        I_rad: vector solar radiation re-irradiated to the sky.
    """

    Asol_wall, Asol_roof, Asol_win = calc_Asol(t, bpr, gv)
    I_rad = calc_I_rad(t, tsd, bpr, gv)
    I_sol = bpr.solar['I_roof'][t] * Asol_roof + bpr.solar['I_win'][t]*Asol_win + bpr.solar['I_wall'][t]*Asol_wall
    I_sol_net = I_sol - I_rad

    return I_sol_net, I_rad # vector in W

def calc_I_rad(t, tsd, bpr, gv):
    """
    This function calculates the solar radiation re-irradiated from a building to the sky according to ISO 13790

    :param t: hour of the year
    :param tsd: time series dataframe
    :param bpr:  building properties object
    :param gv: global variables class
    :return:
        I_rad: vector solar radiation re-irradiated to the sky.
    """

    temp_s_prev = tsd['theta_c'][t - 1] if not np.isnan(tsd['theta_c'][t - 1]) else tsd['T_ext'][t-1]
    theta_ss = tsd['T_sky'][t] - temp_s_prev
    Fform_wall, Fform_win, Fform_roof = 0.5,0.5,1 # 50% reiradiated by vertical surfaces and 100% by horizontal.
    I_rad_win = gv.Rse * bpr.rc_model['U_win']*calc_hr(bpr.architecture['e_win'], theta_ss, gv) * bpr.rc_model['Aw'] * theta_ss
    I_rad_roof = gv.Rse * bpr.rc_model['U_roof']*calc_hr(bpr.architecture['e_roof'], theta_ss, gv) * bpr.rc_model['Aroof'] * theta_ss
    I_rad_wall = gv.Rse * bpr.rc_model['U_wall']*calc_hr(bpr.architecture['e_wall'], theta_ss, gv) * bpr.rc_model['Awall_all'] * theta_ss
    I_rad = Fform_wall*I_rad_wall + Fform_win*I_rad_win + Fform_roof*I_rad_roof

    return I_rad

def calc_hr(emissivity, theta_ss, gv):
    """
    This function calculates the external radiative heat transfer coefficient according to ISO 13790

    :param emissivity: emissivity of the considered surface
    :param theta_ss: delta of temperature between building surface and the sky.
    :param gv: global variables class
    :return:
        hr:

    """
    return 4 * emissivity * gv.blotzman * (theta_ss + 273) ** 3

def calc_Asol(t, bpr, gv):
    """
    This function calculates the effective collecting solar area accounting for use of blinds according to ISO 13790,
    for the sake of simplicity and to avoid iterations, the delta is calculated based on the last time step.

    :param t: time of the year
    :param bpr: building properties object
    :param gv: global variables class
    :return:
    """
    from cea.technologies import blinds
    Fsh_win = blinds.calc_blinds_activation(bpr.solar['I_win'][t], bpr.architecture['G_win'], bpr.architecture['rf_sh'])
    Asol_wall = bpr.rc_model['Awall_all'] * bpr.architecture['a_wall'] * gv.Rse * bpr.rc_model['U_wall']
    Asol_roof = bpr.rc_model['Aroof'] * bpr.architecture['a_roof'] * gv.Rse * bpr.rc_model['U_roof']
    Asol_win = Fsh_win * bpr.rc_model['Aw'] * (1 - gv.F_f)

    return Asol_wall, Asol_roof, Asol_win
"""
=========================================
temperature of emission/control system
=========================================
"""


def calc_temperatures_emission_systems(tsd, bpr, Qcsf_0, Qhsf_0, gv):
    from cea.technologies import radiators, heating_coils, tabs
    # local variables
    Ta_0 = np.nanmax(tsd['ta_hs_set'])
    if bpr.hvac['type_hs'] == 'T0':
        Ths_sup = np.zeros(8760)  # in C
        Ths_re = np.zeros(8760)  # in C
        mcphs = np.zeros(8760)  # in KW/C

    if bpr.hvac['type_cs'] == 'T0':
        Tcs_re = np.zeros(8760)  # in C
        Tcs_sup = np.zeros(8760)  # in C
        mcpcs = np.zeros(8760)  # in KW/C

    if bpr.hvac['type_hs'] == 'T1' or bpr.hvac['type_hs'] == 'T2':  # radiators

        Ths_sup, Ths_re, mcphs = np.vectorize(radiators.calc_radiator)(tsd['Qhsf'], tsd['theta_a'], Qhsf_0, Ta_0,
                                                                        bpr.building_systems['Ths_sup_0'],
                                                                        bpr.building_systems['Ths_re_0'])

    if bpr.hvac['type_hs'] == 'T3':  # air conditioning
        index = np.where(tsd['Qhsf'] == Qhsf_0)
        ma_sup_0 = tsd['ma_sup_hs'][index[0][0]]
        Ta_sup_0 = tsd['Ta_sup_hs'][index[0][0]] + 273
        Ta_re_0 = tsd['Ta_re_hs'][index[0][0]] + 273
        Ths_sup, Ths_re, mcphs = np.vectorize(heating_coils.calc_heating_coil)(tsd['Qhsf'], Qhsf_0, tsd['Ta_sup_hs'], tsd['Ta_re_hs'],
                                                                               bpr.building_systems['Ths_sup_0'], bpr.building_systems['Ths_re_0'], tsd['ma_sup_hs'],ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, gv.Cpa, gv)

    if bpr.hvac['type_cs'] == 'T3':  # air conditioning

        index = np.where(tsd['Qcsf'] == Qcsf_0)
        ma_sup_0 = tsd['ma_sup_cs'][index[0][0]]
        Ta_sup_0 = tsd['Ta_sup_cs'][index[0][0]] + 273
        Ta_re_0 = tsd['Ta_re_cs'][index[0][0]] + 273
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(tsd['Qcsf'], Qcsf_0, tsd['Ta_sup_cs'], tsd['Ta_re_cs'],
                                                                               bpr.building_systems['Tcs_sup_0'], bpr.building_systems['Tcs_re_0'], tsd['ma_sup_cs'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, gv.Cpa, gv)

    if bpr.hvac['type_hs'] == 'T4':  # floor heating

        Ths_sup, Ths_re, mcphs = np.vectorize(tabs.calc_floorheating)(tsd['Qhsf'], tsd['theta_m'], Qhsf_0,
                                                                      bpr.building_systems['Ths_sup_0'],
                                                                      bpr.building_systems['Ths_re_0'],
                                                                      bpr.rc_model['Af'])

    return Tcs_re, Tcs_sup, Ths_re, Ths_sup, mcpcs, mcphs  # C,C, C,C, W/C, W/C


"""
=========================================
space heating/cooling losses
=========================================
"""


def calc_Qhs_Qcs_dis_ls(tair, text, Qhs, Qcs, tsh, trh, tsc, trc, Qhs_max, Qcs_max, D, Y, SystemH, SystemC, Bf, Lv):
    """calculates distribution losses based on ISO 15316"""
    # Calculate tamb in basement according to EN
    tamb = tair - Bf * (tair - text)
    if SystemH != 'T0' and Qhs > 0:
        Qhs_d_ls = ((tsh + trh) / 2 - tamb) * (Qhs / Qhs_max) * (Lv * Y)
    else:
        Qhs_d_ls = 0
    if SystemC != 'T0' and Qcs < 0:
        Qcs_d_ls = ((tsc + trc) / 2 - tamb) * (Qcs / Qcs_max) * (Lv * Y)
    else:
        Qcs_d_ls = 0

    return Qhs_d_ls, Qcs_d_ls


def calc_Qhs_Qcs_em_ls(SystemH, SystemC):
    """model of losses in the emission and control system for space heating and cooling.
    correction factor for the heating and cooling setpoints. extracted from SIA 2044 (replacing EN 15243)"""
    tHC_corr = [0, 0]
    # values extracted from SIA 2044 - national standard replacing values suggested in EN 15243
    if SystemH == 'T4' or 'T1':
        tHC_corr[0] = 0.5 + 1.2
    elif SystemH == 'T2':
        tHC_corr[0] = 0 + 1.2
    elif SystemH == 'T3':  # no emission losses but emissions for ventilation
        tHC_corr[0] = 0.5 + 1  # regulation is not taking into account here
    else:
        tHC_corr[0] = 0.5 + 1.2

    if SystemC == 'T4':
        tHC_corr[1] = 0 - 1.2
    elif SystemC == 'T5':
        tHC_corr[1] = - 0.4 - 1.2
    elif SystemC == 'T3':  # no emission losses but emissions for ventilation
        tHC_corr[1] = 0 - 1  # regulation is not taking into account here
    else:
        tHC_corr[1] = 0 + - 1.2

    return list(tHC_corr)


control_delta_heating = {'T1': 2.5, 'T2': 1.2, 'T3': 0.9, 'T4': 1.8}
control_delta_cooling = {'T1': -2.5, 'T2': -1.2, 'T3': -0.9, 'T4': -1.8}
system_delta_heating = {'T0': 0.0, 'T1': 0.15, 'T2': -0.1, 'T3': -1.1, 'T4': -0.9}
system_delta_cooling = {'T0': 0.0, 'T1': 0.5, 'T2': 0.7, 'T3': 0.5}

def setpoint_correction_for_space_emission_systems(heating_system, cooling_system, control_system):
    """
    Model of losses in the emission and control system for space heating and cooling.

    Correction factor for the heating and cooling setpoints. Extracted from EN 15316-2

    (see cea\databases\CH\Systems\emission_systems.xls for valid values for the heating and cooling system values)

    T0 means there's no heating/cooling systems installed, therefore, also no control systems for heating/cooling.
    In short, when the input system is T0, the output set point correction should be 0.0.
    So if there is no cooling systems, the setpoint_correction_for_space_emission_systems function input: (T1, T0, T1) (type_hs, type_cs, type_ctrl),
    return should be (2.65, 0.0), the control system is only specified for the heating system.
    In another case with no heating systems: input: (T0, T3, T1) return: (0.0, -2.0), the control system is only
    specified for the heating system.

    PARAMETERS
    ----------

    :param heating_system: The heating system used. Valid values: T0, T1, T2, T3, T4
    :type heating_system: str

    :param cooling_system: The cooling system used. Valid values: T0, T1, T2, T3
    :type cooling_system: str

    :param control_system: The control system used. Valid values: T1, T2, T3, T4 - as defined in the
        contributors manual under Databases / Archetypes / Building Properties / Mechanical systems.
        T1 for none, T2 for PI control, T3 for PI control with optimum tuning, and T4 for room temperature control
        (electromagnetically/electronically).
    :type control_system: str

    RETURNS
    -------

    :returns: two delta T to correct the set point temperature, dT_heating, dT_cooling
    :rtype: tuple(double, double)
    """
    __author__ = "Shanshan Hsieh"
    __credits__ = ["Shanshan Hsieh", "Daren Thomas"]

    try:
        result_heating = 0.0 if heating_system == 'T0' else (control_delta_heating[control_system] +
                                                             system_delta_heating[heating_system])
        result_cooling = 0.0 if cooling_system == 'T0' else (control_delta_cooling[control_system] +
                                                             system_delta_cooling[cooling_system])
    except KeyError:
        raise ValueError(
            'Invalid system / control combination: %s, %s, %s' % (heating_system, cooling_system, control_system))

    return result_heating, result_cooling

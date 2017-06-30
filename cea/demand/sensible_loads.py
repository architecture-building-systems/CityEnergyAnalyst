# -*- coding: utf-8 -*-
"""
Sensible space heating and space cooling loads
EN-13970
"""
from __future__ import division
import numpy as np
from cea.utilities.physics import BOLTZMANN
from cea.demand import occupancy_model

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Shanshan Hsieh", "Daren Thomas", "Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"



# capacity of emission/control system

def calc_Qhs_Qcs_sys_max(Af, prop_HVAC):
    # TODO: Documentation
    # Refactored from CalcThermalLoads

    IC_max = -prop_HVAC['Qcsmax_Wm2'] * Af
    IH_max = prop_HVAC['Qhsmax_Wm2'] * Af
    return IC_max, IH_max



# solar and heat gains

def calc_Qgain_sen(t, tsd, bpr, gv):
    # TODO

    # internal loads
    tsd['I_sol'][t], tsd['I_rad'][t] = calc_I_sol(t, bpr, tsd, gv)

    return tsd


def calc_Qgain_lat(schedules, X_ghp, Af, sys_e_cooling, sys_e_heating):
    # TODO: Documentation
    # Refactored from CalcThermalLoads
    """
    :param list_uses: The list of uses used in the project
    :type list_uses: list
    :param schedules: The list of schedules defined for the project - in the same order as `list_uses`
    :type schedules: list[ndarray[float]]
    :param X_ghp: humidity gain from people in g/h/p for each occupancy type
    :type X_ghp: list[float]
    :param occupancy: for each use in `list_uses`, the percentage of that use for this building. Sum of values is 1.0
    :type occupancy: dict[str, float]
    :param Af: total conditioned floor area
    :type Af: float

    :param sys_e_heating: cooling system code as defined in the systems database (e.g. 'T0' if no cooling)
    :param sys_e_heating: string
    :param sys_e_cooling: cooling system code as defined in the systems database (e.g. 'T0' if no cooling)
    :param sys_e_cooling: string

    :return w_int: yearly schedule

    """
    # calc yearly humidity gains based on occupancy schedule and specific humidity gains for each occupancy type in the
    # building
    humidity_schedule = schedules['X'] * X_ghp  # in g/h/m2
    if sys_e_heating == 'T3' or sys_e_cooling == 'T3':
        w_int = humidity_schedule * Af / (1000 * 3600)  # kg/s
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
    I_rad = calc_I_rad(t, tsd, bpr, gv.Rse)
    I_sol = bpr.solar.I_roof[t] * Asol_roof + bpr.solar.I_win[t] * Asol_win + bpr.solar.I_wall[t] * Asol_wall
    I_sol_net = I_sol - I_rad

    return I_sol_net, I_rad # vector in W


def calc_I_rad(t, tsd, bpr, Rse):
    """
    This function calculates the solar radiation re-irradiated from a building to the sky according to ISO 13790

    :param t: hour of the year
    :param tsd: time series dataframe
    :param bpr:  building properties object
    :param gv: global variables class
    :return:
        I_rad: vector solar radiation re-irradiated to the sky.
    """

    temp_s_prev = tsd['theta_c'][t - 1]
    if np.isnan(tsd['theta_c'][t - 1]):
        temp_s_prev = tsd['T_ext'][t-1]

    theta_ss = tsd['T_sky'][t] - temp_s_prev
    Fform_wall, Fform_win, Fform_roof = 0.5, 0.5, 1  # 50% reiradiated by vertical surfaces and 100% by horizontal.
    I_rad_win = Rse * bpr.rc_model['U_win'] * calc_hr(bpr.architecture.e_win, theta_ss) * bpr.rc_model[
        'Aw'] * theta_ss
    I_rad_roof = Rse * bpr.rc_model['U_roof'] * calc_hr(bpr.architecture.e_roof, theta_ss) * bpr.rc_model[
        'Aroof'] * theta_ss
    I_rad_wall = Rse * bpr.rc_model['U_wall'] * calc_hr(bpr.architecture.e_wall, theta_ss) * bpr.rc_model[
        'Awall_all'] * theta_ss
    I_rad = Fform_wall * I_rad_wall + Fform_win * I_rad_win + Fform_roof * I_rad_roof

    return I_rad


def calc_hr(emissivity, theta_ss):
    """
    This function calculates the external radiative heat transfer coefficient according to ISO 13790

    :param emissivity: emissivity of the considered surface
    :param theta_ss: delta of temperature between building surface and the sky.
    :return:
        hr:

    """
    return 4.0 * emissivity * BOLTZMANN * (theta_ss + 273.0) ** 3.0


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
    Fsh_win = blinds.calc_blinds_activation(bpr.solar.I_win[t], bpr.architecture.G_win, bpr.architecture.rf_sh)
    Asol_wall = bpr.rc_model['Awall_all'] * bpr.architecture.a_wall * gv.Rse * bpr.rc_model['U_wall']
    Asol_roof = bpr.rc_model['Aroof'] * bpr.architecture.a_roof * gv.Rse * bpr.rc_model['U_roof']
    Asol_win = Fsh_win * bpr.rc_model['Aw'] * (1 - gv.F_f)

    return Asol_wall, Asol_roof, Asol_win


# temperature of emission/control system

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



# space heating/cooling losses

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

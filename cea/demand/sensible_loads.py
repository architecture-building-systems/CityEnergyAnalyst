# -*- coding: utf-8 -*-
"""
Sensible space heating and space cooling loads
EN-13970
"""
from __future__ import division
import numpy as np
from cea.utilities.physics import BOLTZMANN
from cea.demand import control_heating_cooling_systems, constants

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Shanshan Hsieh", "Daren Thomas", "Martin Mosteiro", "Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# import from GV
B_F = constants.B_F
D = constants.D
C_P_A = constants.C_P_A
RSE = constants.RSE


# capacity of emission/control system


def calc_Qhs_Qcs_sys_max(Af, prop_HVAC):
    # TODO: Documentation
    # Refactored from CalcThermalLoads

    IC_max = -prop_HVAC['Qcsmax_Wm2'] * Af
    IH_max = prop_HVAC['Qhsmax_Wm2'] * Af
    return IC_max, IH_max


# solar and heat gains


def calc_Qgain_sen(t, tsd, bpr):
    # TODO

    # internal loads
    tsd['I_sol_and_I_rad'][t], tsd['I_rad'][t], tsd['I_sol'][t] = calc_I_sol(t, bpr, tsd)

    return tsd


def calc_Qgain_lat(schedules, bpr):
    # TODO: Documentation
    # Refactored from CalcThermalLoads
    """

    :param schedules: The list of schedules defined for the project - in the same order as `list_uses`
    :type schedules: list[ndarray[float]]

    :return w_int: yearly schedule

    """
    # calc yearly humidity gains based on occupancy schedule and specific humidity gains for each occupancy type in the
    # building
    humidity_schedule = schedules['X'] * bpr.internal_loads['X_ghp']  # in g/h
    w_int = humidity_schedule / (1000 * 3600)  # kg/s

    return w_int


def calc_I_sol(t, bpr, tsd):
    """
    This function calculates the net solar radiation (incident -reflected - re-irradiated) according to ISO 13790

    :param t: hour of the year
    :param bpr: building properties object
    :param tsd: time series dataframe
    :return:
        I_sol_net: vector of net solar radiation to the building
        I_rad: vector solar radiation re-irradiated to the sky.
        I_sol_gross : vector of incident radiation to the building.
    """

    # calc irradiation to the sky
    I_rad = calc_I_rad(t, tsd, bpr)

    # get incident radiation
    I_sol_gross = bpr.solar.I_sol[t]

    I_sol_net = I_sol_gross + I_rad

    return I_sol_net, I_rad, I_sol_gross  # vector in W


def calc_I_rad(t, tsd, bpr):
    """
    This function calculates the solar radiation re-irradiated from a building to the sky according to ISO 13790

    :param t: hour of the year
    :param tsd: time series dataframe
    :param bpr:  building properties object
    :return:
        I_rad: vector solar radiation re-irradiated to the sky.
    """

    temp_s_prev = tsd['theta_c'][t - 1]
    if np.isnan(tsd['theta_c'][t - 1]):
        temp_s_prev = tsd['T_ext'][t - 1]

    theta_ss = tsd['T_sky'][t] - temp_s_prev
    Fform_wall, Fform_win, Fform_roof = 0.5, 0.5, 1  # 50% reiradiated by vertical surfaces and 100% by horizontal.
    I_rad_win = RSE * bpr.rc_model['U_win'] * calc_hr(bpr.architecture.e_win, theta_ss) * bpr.rc_model[
        'Aw'] * theta_ss
    I_rad_roof = RSE * bpr.rc_model['U_roof'] * calc_hr(bpr.architecture.e_roof, theta_ss) * bpr.rc_model[
        'Aroof'] * theta_ss
    I_rad_wall = RSE * bpr.rc_model['U_wall'] * calc_hr(bpr.architecture.e_wall, theta_ss) * bpr.rc_model[
        'Aop_sup'] * theta_ss
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


def calc_final_heating_cooling_loads(tsd):

    # TODO: refactor this stuff and document
    tsd['Qcsf_lat'] = tsd['Qcs_lat_sys']
    tsd['Qhsf_lat'] = tsd['Qhs_lat_sys']
    # Calc requirements of generation systems (both cooling and heating do not have a storage):
    tsd['Qhs'] = tsd['Qhs_sen_sys']
    tsd['Qhsf'] = tsd['Qhs'] + tsd['Qhs_em_ls'] + tsd[
        'Qhs_dis_ls']  # no latent is considered because it is already added a
    # s electricity from the adiabatic system. --> TODO
    tsd['Qcs'] = tsd['Qcs_sen_sys'] + tsd['Qcsf_lat']
    tsd['Qcsf'] = tsd['Qcs'] + tsd['Qcs_em_ls'] + tsd['Qcs_dis_ls']

    frac_ahu = [ahu / sys if sys > 0 else 0 for ahu, sys in zip(tsd['Qhs_sen_ahu'], tsd['Qhs_sen_sys'])]
    tsd['Qhsf_ahu'] = tsd['Qhs_sen_ahu'] + (tsd['Qhs_em_ls'] + tsd['Qhs_dis_ls']) * frac_ahu

    frac_aru = [aru / sys if sys > 0 else 0 for aru, sys in zip(tsd['Qhs_sen_aru'], tsd['Qhs_sen_sys'])]
    tsd['Qhsf_aru'] = tsd['Qhs_sen_aru'] + (tsd['Qhs_em_ls'] + tsd['Qhs_dis_ls']) * frac_aru

    frac_shu = [shu / sys if sys > 0 else 0 for shu, sys in zip(tsd['Qhs_sen_shu'], tsd['Qhs_sen_sys'])]
    tsd['Qhsf_shu'] = tsd['Qhs_sen_shu'] + (tsd['Qhs_em_ls'] + tsd['Qhs_dis_ls']) * frac_shu

    frac_ahu = [ahu / sys if sys < 0 else 0 for ahu, sys in zip(tsd['Qcs_sen_ahu'], tsd['Qcs_sen_sys'])]
    tsd['Qcsf_ahu'] = tsd['Qcs_sen_ahu'] + tsd['Qcs_lat_ahu'] + (tsd['Qcs_em_ls'] + tsd['Qcs_dis_ls']) * frac_ahu

    frac_aru = [aru / sys if sys < 0 else 0 for aru, sys in zip(tsd['Qcs_sen_aru'], tsd['Qcs_sen_sys'])]
    tsd['Qcsf_aru'] = tsd['Qcs_sen_aru'] + tsd['Qcs_lat_aru'] + (tsd['Qcs_em_ls'] + tsd['Qcs_dis_ls']) * frac_aru

    frac_scu = [scu / sys if sys < 0 else 0 for scu, sys in zip(tsd['Qcs_sen_scu'], tsd['Qcs_sen_sys'])]
    tsd['Qcsf_scu'] = tsd['Qcs_sen_scu'] + (tsd['Qcs_em_ls'] + tsd['Qcs_dis_ls']) * frac_scu

    return







# temperature of emission/control system

def calc_temperatures_emission_systems(bpr, tsd):
    """
    Calculate temperature of emission systems.
    Using radiator function also for cooling ('radiators.calc_radiator')
    Modified from legacy

    Gabriel Happle, Feb. 2018

    :param bpr: Building Properties
    :type bpr: BuildingPropertiesRow
    :param tsd: Time series data of building
    :type tsd: dict
    :return: modifies tsd
    :rtype: None
    """

    from cea.technologies import radiators, heating_coils, tabs

    #
    # TEMPERATURES HEATING SYSTEMS
    #
    if not control_heating_cooling_systems.has_heating_system(bpr):
        # if no heating system

        tsd['Thsf_sup_ahu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Thsf_re_ahu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcphsf_ahu'] = np.zeros(8760)
        tsd['Thsf_sup_aru'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Thsf_re_aru'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcphsf_aru'] = np.zeros(8760)
        tsd['Thsf_sup_shu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Thsf_re_shu'] = np.zeros(8760) * np.nan # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcphsf_shu'] = np.zeros(8760)

    elif control_heating_cooling_systems.has_radiator_heating_system(bpr):
        # if radiator heating system
        Ta_heating_0 = np.nanmax(tsd['ta_hs_set'])
        Qhsf_0 = np.nanmax(tsd['Qhsf_shu'])  # in W

        tsd['Thsf_sup_ahu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Thsf_re_ahu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcphsf_ahu'] = np.zeros(8760)
        tsd['Thsf_sup_aru'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Thsf_re_aru'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcphsf_aru'] = np.zeros(8760)

        Ths_sup, Ths_re, mcphs = np.vectorize(radiators.calc_radiator)(tsd['Qhsf_shu'], tsd['T_int'], Qhsf_0, Ta_heating_0,
                                                                       bpr.building_systems['Ths_sup_shu_0'],
                                                                       bpr.building_systems['Ths_re_shu_0'])

        tsd['Thsf_sup_shu'] = Ths_sup
        tsd['Thsf_re_shu'] = Ths_re
        tsd['mcphsf_shu'] = mcphs

    elif control_heating_cooling_systems.has_central_ac_heating_system(bpr):

        # ahu
        # consider losses according to loads of systems
        Qhsf_ahu_0 = np.nanmax(tsd['Qhsf_ahu'])  # in W

        index = np.where(tsd['Qhsf_ahu'] == Qhsf_ahu_0)
        ma_sup_0 = tsd['ma_sup_hs_ahu'][index[0][0]]
        Ta_sup_0 = tsd['ta_sup_hs_ahu'][index[0][0]] + 273
        Ta_re_0 = tsd['ta_re_hs_ahu'][index[0][0]] + 273
        Ths_sup, Ths_re, mcphs = np.vectorize(heating_coils.calc_heating_coil)(tsd['Qhsf_ahu'], Qhsf_ahu_0, tsd['ta_sup_hs_ahu'],
                                                                               tsd['ta_re_hs_ahu'],
                                                                               bpr.building_systems['Ths_sup_ahu_0'],
                                                                               bpr.building_systems['Ths_re_ahu_0'],
                                                                               tsd['ma_sup_hs_ahu'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, C_P_A)
        tsd['Thsf_sup_ahu'] = Ths_sup  # in C
        tsd['Thsf_re_ahu'] = Ths_re  # in C
        tsd['mcphsf_ahu'] = mcphs

        # ARU
        # consider losses according to loads of systems
        Qhsf_aru_0 = np.nanmax(tsd['Qhsf_aru'])  # in W

        index = np.where(tsd['Qhsf_aru'] == Qhsf_aru_0)
        ma_sup_0 = tsd['ma_sup_hs_aru'][index[0][0]]
        Ta_sup_0 = tsd['ta_sup_hs_aru'][index[0][0]] + 273
        Ta_re_0 = tsd['ta_re_hs_aru'][index[0][0]] + 273
        Ths_sup, Ths_re, mcphs = np.vectorize(heating_coils.calc_heating_coil)(tsd['Qhsf_aru'], Qhsf_aru_0,
                                                                               tsd['ta_sup_hs_aru'],
                                                                               tsd['ta_re_hs_aru'],
                                                                               bpr.building_systems['Ths_sup_aru_0'],
                                                                               bpr.building_systems['Ths_re_aru_0'],
                                                                               tsd['ma_sup_hs_aru'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, C_P_A)
        tsd['Thsf_sup_aru'] = Ths_sup  # in C
        tsd['Thsf_re_aru'] = Ths_re  # in C
        tsd['mcphsf_aru'] = mcphs

        # SHU
        tsd['Thsf_sup_shu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Thsf_re_shu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcphsf_shu'] = np.zeros(8760)

    elif control_heating_cooling_systems.has_floor_heating_system(bpr):

        Qhsf_0 = np.nanmax(tsd['Qhsf_shu'])  # in W

        tsd['Thsf_sup_ahu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Thsf_re_ahu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcphsf_ahu'] = np.zeros(8760)
        tsd['Thsf_sup_aru'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Thsf_re_aru'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcphsf_aru'] = np.zeros(8760)

        Ths_sup, Ths_re, mcphs = np.vectorize(tabs.calc_floorheating)(tsd['Qhsf_shu'], tsd['theta_m'], Qhsf_0,
                                                                      bpr.building_systems['Ths_sup_shu_0'],
                                                                      bpr.building_systems['Ths_re_shu_0'],
                                                                      bpr.rc_model['Af'])
        tsd['Thsf_sup_shu'] = Ths_sup
        tsd['Thsf_re_shu'] = Ths_re
        tsd['mcphsf_shu'] = mcphs

    else:
        raise Exception('Heating system not defined in function: "calc_temperatures_emission_systems"')


    #
    # TEMPERATURES COOLING SYSTEMS
    #
    if not control_heating_cooling_systems.has_cooling_system(bpr):
        # if no heating system

        tsd['Tcsf_sup_ahu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Tcsf_re_ahu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcpcsf_ahu'] = np.zeros(8760)
        tsd['Tcsf_sup_aru'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Tcsf_re_aru'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcpcsf_aru'] = np.zeros(8760)
        tsd['Tcsf_sup_scu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Tcsf_re_scu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcpcsf_scu'] = np.zeros(8760)

    elif control_heating_cooling_systems.has_central_ac_cooling_system(bpr):

        # AHU
        # consider losses according to loads of systems
        Qcsf_ahu_0 = np.nanmin(tsd['Qcsf_ahu'])  # in W

        index = np.where(tsd['Qcsf_ahu'] == Qcsf_ahu_0)
        ma_sup_0 = tsd['ma_sup_cs_ahu'][index[0][0]]
        Ta_sup_0 = tsd['ta_sup_cs_ahu'][index[0][0]] + 273
        Ta_re_0 = tsd['ta_re_cs_ahu'][index[0][0]] + 273
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(tsd['Qcsf_ahu'], Qcsf_ahu_0, tsd['ta_sup_cs_ahu'],
                                                                               tsd['ta_re_cs_ahu'],
                                                                               bpr.building_systems['Tcs_sup_ahu_0'],
                                                                               bpr.building_systems['Tcs_re_ahu_0'],
                                                                               tsd['ma_sup_cs_ahu'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, C_P_A)
        tsd['Tcsf_sup_ahu'] = Tcs_sup  # in C
        tsd['Tcsf_re_ahu'] = Tcs_re  # in C
        tsd['mcpcsf_ahu'] = mcpcs

        # ARU
        # consider losses according to loads of systems
        Qcsf_aru_0 = np.nanmin(tsd['Qcsf_aru'])  # in W

        index = np.where(tsd['Qcsf_aru'] == Qcsf_aru_0)
        ma_sup_0 = tsd['ma_sup_cs_aru'][index[0][0]]
        Ta_sup_0 = tsd['ta_sup_cs_aru'][index[0][0]] + 273
        Ta_re_0 = tsd['ta_re_cs_aru'][index[0][0]] + 273
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(tsd['Qcsf_aru'], Qcsf_aru_0, tsd['ta_sup_cs_aru'],
                                                                               tsd['ta_re_cs_aru'],
                                                                               bpr.building_systems['Tcs_sup_aru_0'],
                                                                               bpr.building_systems['Tcs_re_aru_0'],
                                                                               tsd['ma_sup_cs_aru'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, C_P_A)
        tsd['Tcsf_sup_aru'] = Tcs_sup  # in C
        tsd['Tcsf_re_aru'] = Tcs_re  # in C
        tsd['mcpcsf_aru'] = mcpcs

        # SCU
        tsd['Tcsf_sup_scu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Tcsf_re_scu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcpcsf_scu'] = np.zeros(8760)

    elif control_heating_cooling_systems.has_local_ac_cooling_system(bpr):

        # AHU
        tsd['Tcsf_sup_ahu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Tcsf_re_ahu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcpcsf_ahu'] = np.zeros(8760)

        # ARU
        # Calc nominal temperatures of systems
        Qcsf_aru_0 = np.nanmin(tsd['Qcsf_aru'])  # in W

        index = np.where(tsd['Qcsf_aru'] == Qcsf_aru_0)
        ma_sup_0 = tsd['ma_sup_cs_aru'][index[0][0]]
        Ta_sup_0 = tsd['ta_sup_cs_aru'][index[0][0]] + 273
        Ta_re_0 = tsd['ta_re_cs_aru'][index[0][0]] + 273
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(tsd['Qcsf_aru'], Qcsf_aru_0,
                                                                               tsd['ta_sup_cs_aru'],
                                                                               tsd['ta_re_cs_aru'],
                                                                               bpr.building_systems['Tcs_sup_aru_0'],
                                                                               bpr.building_systems['Tcs_re_aru_0'],
                                                                               tsd['ma_sup_cs_aru'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, C_P_A)
        tsd['Tcsf_sup_aru'] = Tcs_sup  # in C
        tsd['Tcsf_re_aru'] = Tcs_re  # in C
        tsd['mcpcsf_aru'] = mcpcs

        # SCU
        tsd['Tcsf_sup_scu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Tcsf_re_scu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcpcsf_scu'] = np.zeros(8760)

    elif control_heating_cooling_systems.has_3for2_cooling_system(bpr):

        # AHU
        Qcsf_ahu_0 = np.nanmin(tsd['Qcsf_ahu'])  # in W

        index = np.where(tsd['Qcsf_ahu'] == Qcsf_ahu_0)
        ma_sup_0 = tsd['ma_sup_cs_ahu'][index[0][0]]
        Ta_sup_0 = tsd['ta_sup_cs_ahu'][index[0][0]] + 273
        Ta_re_0 = tsd['ta_re_cs_ahu'][index[0][0]] + 273
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(tsd['Qcsf_ahu'], Qcsf_ahu_0,
                                                                               tsd['ta_sup_cs_ahu'],
                                                                               tsd['ta_re_cs_ahu'],
                                                                               bpr.building_systems['Tcs_sup_ahu_0'],
                                                                               bpr.building_systems['Tcs_re_ahu_0'],
                                                                               tsd['ma_sup_cs_ahu'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, C_P_A)
        tsd['Tcsf_sup_ahu'] = Tcs_sup  # in C
        tsd['Tcsf_re_ahu'] = Tcs_re  # in C
        tsd['mcpcsf_ahu'] = mcpcs

        # ARU
        # Calc nominal temperatures of systems
        Qcsf_aru_0 = np.nanmin(tsd['Qcsf_aru'])  # in W

        index = np.where(tsd['Qcsf_aru'] == Qcsf_aru_0)
        ma_sup_0 = tsd['ma_sup_cs_aru'][index[0][0]]
        Ta_sup_0 = tsd['ta_sup_cs_aru'][index[0][0]] + 273
        Ta_re_0 = tsd['ta_re_cs_aru'][index[0][0]] + 273
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(tsd['Qcsf_aru'], Qcsf_aru_0,
                                                                               tsd['ta_sup_cs_aru'],
                                                                               tsd['ta_re_cs_aru'],
                                                                               bpr.building_systems['Tcs_sup_aru_0'],
                                                                               bpr.building_systems['Tcs_re_aru_0'],
                                                                               tsd['ma_sup_cs_aru'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, C_P_A)
        tsd['Tcsf_sup_aru'] = Tcs_sup  # in C
        tsd['Tcsf_re_aru'] = Tcs_re  # in C
        tsd['mcpcsf_aru'] = mcpcs

        # SCU
        Qcsf_scu_0 = np.nanmin(tsd['Qcsf_scu'])  # in W
        Ta_cooling_0 = np.nanmin(tsd['ta_cs_set'])

        Tcs_sup, Tcs_re, mcpcs = np.vectorize(radiators.calc_radiator)(tsd['Qcsf_scu'], tsd['T_int'], Qcsf_scu_0, Ta_cooling_0,
                                                                       bpr.building_systems['Tcs_sup_scu_0'],
                                                                       bpr.building_systems['Tcs_re_scu_0'])
        tsd['Tcsf_sup_scu'] = Tcs_sup  # in C
        tsd['Tcsf_re_scu'] = Tcs_re  # in C
        tsd['mcpcsf_scu'] = mcpcs

    elif control_heating_cooling_systems.has_ceiling_cooling_system(bpr):

        # SCU
        Qcsf_scu_0 = np.nanmin(tsd['Qcsf_scu'])  # in W
        Ta_cooling_0 = np.nanmin(tsd['ta_cs_set'])

        # use radiator for ceiling cooling calculation
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(radiators.calc_radiator)(tsd['Qcsf_scu'], tsd['T_int'], Qcsf_scu_0, Ta_cooling_0,
                                                                       bpr.building_systems['Tcs_sup_scu_0'],
                                                                       bpr.building_systems['Tcs_re_scu_0'])

        tsd['Tcsf_sup_scu'] = Tcs_sup  # in C
        tsd['Tcsf_re_scu'] = Tcs_re  # in C
        tsd['mcpcsf_scu'] = mcpcs

        # AHU
        tsd['Tcsf_sup_ahu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Tcsf_re_ahu'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcpcsf_ahu'] = np.zeros(8760)

        # ARU
        tsd['Tcsf_sup_aru'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Tcsf_re_aru'] = np.zeros(8760) * np.nan  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcpcsf_aru'] = np.zeros(8760)

    else:
        raise Exception('Cooling system not defined in function: "calc_temperatures_emission_systems"')


# space heating/cooling losses


def calc_q_dis_ls_heating_cooling(bpr, tsd):
    """
    Calculate distribution losses of emission systems.

    Modified from legacy:
        calculates distribution losses based on ISO 15316

    Gabriel Happle, Feb. 2018

    :param bpr: Building Properties
    :type bpr: BuildingPropertiesRow
    :param tsd: Time series data of building
    :type tsd: dict
    :return: modifies tsd
    :rtype: None
    """

    # look up properties
    Y = bpr.building_systems['Y'][0]
    Lv = bpr.building_systems['Lv']

    tsh_ahu = bpr.building_systems['Ths_sup_ahu_0']
    trh_ahu = bpr.building_systems['Ths_re_ahu_0']
    tsh_aru = bpr.building_systems['Ths_sup_aru_0']
    trh_aru = bpr.building_systems['Ths_re_aru_0']
    tsh_shu = bpr.building_systems['Ths_sup_shu_0']
    trh_shu = bpr.building_systems['Ths_re_shu_0']

    tsc_ahu = bpr.building_systems['Tcs_sup_ahu_0']
    trc_ahu = bpr.building_systems['Tcs_re_ahu_0']
    tsc_aru = bpr.building_systems['Tcs_sup_aru_0']
    trc_aru = bpr.building_systems['Tcs_re_aru_0']
    tsc_scu = bpr.building_systems['Tcs_sup_scu_0']
    trc_scu = bpr.building_systems['Tcs_re_scu_0']

    tair = tsd['T_int']
    text = tsd['T_ext']

    # Calculate tamb in basement according to EN
    tamb = tair - B_F * (tair - text)

    if np.any(tsd['Qhs_sen_ahu'] > 0):
        frac_ahu = [ahu / sys if sys > 0 else 0 for ahu, sys in zip(tsd['Qhs_sen_ahu'], tsd['Qhs_sen_sys'])]
        qhs_sen_ahu_incl_em_ls = tsd['Qhs_sen_ahu'] + tsd['Qhs_em_ls'] * frac_ahu
        qhs_sen_ahu_incl_em_ls = np.nan_to_num(qhs_sen_ahu_incl_em_ls)
        Qhs_d_ls_ahu = ((tsh_ahu + trh_ahu) / 2 - tamb) * (
        qhs_sen_ahu_incl_em_ls / np.nanmax(qhs_sen_ahu_incl_em_ls)) * (Lv * Y)

    else:
        Qhs_d_ls_ahu = np.zeros(8760)

    if np.any(tsd['Qhs_sen_aru'] > 0):
        frac_aru = [aru / sys if sys > 0 else 0 for aru, sys in zip(tsd['Qhs_sen_aru'], tsd['Qhs_sen_sys'])]
        qhs_sen_aru_incl_em_ls = tsd['Qhs_sen_aru'] + tsd['Qhs_em_ls'] * frac_aru
        qhs_sen_aru_incl_em_ls = np.nan_to_num(qhs_sen_aru_incl_em_ls)
        Qhs_d_ls_aru = ((tsh_aru + trh_aru) / 2 - tamb) * (
        qhs_sen_aru_incl_em_ls / np.nanmax(qhs_sen_aru_incl_em_ls)) * (
                           Lv * Y)
    else:
        Qhs_d_ls_aru = np.zeros(8760)

    if np.any(tsd['Qhs_sen_shu'] > 0):
        frac_shu = [shu / sys if sys > 0 else 0 for shu, sys in zip(tsd['Qhs_sen_shu'], tsd['Qhs_sen_sys'])]
        qhs_sen_shu_incl_em_ls = tsd['Qhs_sen_shu'] + tsd['Qhs_em_ls'] * frac_shu
        qhs_sen_shu_incl_em_ls = np.nan_to_num(qhs_sen_shu_incl_em_ls)
        qhs_d_ls_shu = ((tsh_shu + trh_shu) / 2 - tamb) * (
        qhs_sen_shu_incl_em_ls / np.nanmax(qhs_sen_shu_incl_em_ls)) * (
                           Lv * Y)
    else:
        qhs_d_ls_shu = np.zeros(8760)

    if np.any(tsd['Qcs_sen_ahu'] < 0):
        frac_ahu = [ahu / sys if sys < 0 else 0 for ahu, sys in zip(tsd['Qcs_sen_ahu'], tsd['Qcs_sen_sys'])]
        qcs_sen_ahu_incl_em_ls = tsd['Qcs_sen_ahu'] + tsd['Qcs_lat_ahu'] + tsd['Qcs_em_ls'] * frac_ahu
        qcs_sen_ahu_incl_em_ls = np.nan_to_num(qcs_sen_ahu_incl_em_ls)
        qcs_d_ls_ahu = ((tsc_ahu + trc_ahu) / 2 - tamb) * (qcs_sen_ahu_incl_em_ls / np.nanmin(qcs_sen_ahu_incl_em_ls))\
                       * (Lv * Y)
    else:
        qcs_d_ls_ahu = np.zeros(8760)

    if np.any(tsd['Qcs_sen_aru'] < 0):
        frac_aru = [aru / sys if sys < 0 else 0 for aru, sys in zip(tsd['Qcs_sen_aru'], tsd['Qcs_sen_sys'])]
        qcs_sen_aru_incl_em_ls = tsd['Qcs_sen_aru'] + tsd['Qcs_lat_aru'] + tsd['Qcs_em_ls'] * frac_aru
        qcs_sen_aru_incl_em_ls = np.nan_to_num(qcs_sen_aru_incl_em_ls)
        qcs_d_ls_aru = ((tsc_aru + trc_aru) / 2 - tamb) * (qcs_sen_aru_incl_em_ls / np.nanmin(qcs_sen_aru_incl_em_ls))\
                        * (Lv * Y)
    else:
        qcs_d_ls_aru = np.zeros(8760)

    if np.any(tsd['Qcs_sen_scu'] < 0):
        frac_scu = [scu / sys if sys < 0 else 0 for scu, sys in zip(tsd['Qcs_sen_scu'], tsd['Qcs_sen_sys'])]
        qcs_sen_scu_incl_em_ls = tsd['Qcs_sen_scu'] + tsd['Qcs_em_ls'] * frac_scu
        qcs_sen_scu_incl_em_ls = np.nan_to_num(qcs_sen_scu_incl_em_ls)
        Qcs_d_ls_scu = ((tsc_scu + trc_scu) / 2 - tamb) * (qcs_sen_scu_incl_em_ls / np.nanmin(qcs_sen_scu_incl_em_ls)) * (
        Lv * Y)
    else:
        Qcs_d_ls_scu = np.zeros(8760)

    tsd['Qhs_dis_ls'] = Qhs_d_ls_ahu + Qhs_d_ls_aru + qhs_d_ls_shu
    tsd['Qcs_dis_ls'] = qcs_d_ls_ahu + qcs_d_ls_aru + Qcs_d_ls_scu

    return

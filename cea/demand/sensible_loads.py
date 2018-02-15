# -*- coding: utf-8 -*-
"""
Sensible space heating and space cooling loads
EN-13970
"""
from __future__ import division
import numpy as np
from cea.utilities.physics import BOLTZMANN
from cea.demand import control_heating_cooling_systems
from cea import globalvar

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
    tsd['I_sol_and_I_rad'][t], tsd['I_rad'][t], tsd['I_sol'][t] = calc_I_sol(t, bpr, tsd, gv)

    return tsd


def calc_Qgain_lat(schedules, bpr):
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
    humidity_schedule = schedules['X'] * bpr.internal_loads['X_ghp']  # in g/h/m2
    w_int = humidity_schedule * bpr.rc_model['Af'] / (1000 * 3600)  # kg/s

    return w_int


def calc_I_sol(t, bpr, tsd, gv):
    """
    This function calculates the net solar radiation (incident -reflected - re-irradiated) according to ISO 13790

    :param t: hour of the year
    :param bpr: building properties object
    :param tsd: time series dataframe
    :param gv: global variables class
    :return:
        I_sol_net: vector of net solar radiation to the building
        I_rad: vector solar radiation re-irradiated to the sky.
        I_sol_gross : vector of incident radiation to the building.
    """

    # calc irradiation to the sky
    I_rad = calc_I_rad(t, tsd, bpr, gv.Rse)

    # get incident radiation
    I_sol_gross = bpr.solar.I_sol[t]

    I_sol_net = I_sol_gross + I_rad

    return I_sol_net, I_rad, I_sol_gross  # vector in W


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
        temp_s_prev = tsd['T_ext'][t - 1]

    theta_ss = tsd['T_sky'][t] - temp_s_prev
    Fform_wall, Fform_win, Fform_roof = 0.5, 0.5, 1  # 50% reiradiated by vertical surfaces and 100% by horizontal.
    I_rad_win = Rse * bpr.rc_model['U_win'] * calc_hr(bpr.architecture.e_win, theta_ss) * bpr.rc_model[
        'Aw'] * theta_ss
    I_rad_roof = Rse * bpr.rc_model['U_roof'] * calc_hr(bpr.architecture.e_roof, theta_ss) * bpr.rc_model[
        'Aroof'] * theta_ss
    I_rad_wall = Rse * bpr.rc_model['U_wall'] * calc_hr(bpr.architecture.e_wall, theta_ss) * bpr.rc_model[
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


# temperature of emission/control system

def calc_temperatures_emission_systems(tsd, bpr, gv):
    from cea.technologies import radiators, heating_coils, tabs
    # local variables
    Ta_heating_0 = np.nanmax(tsd['ta_hs_set'])
    Ta_cooling_0 = np.nanmin(tsd['ta_cs_set'])

    #
    # TEMPERATURES HEATING SYSTEMS
    #
    if not control_heating_cooling_systems.has_heating_system(bpr):
        # if no heating system

        tsd['Thsf_sup_ahu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Thsf_re_ahu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcphsf_ahu'] = np.zeros(8760)
        tsd['Thsf_sup_aru'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Thsf_re_aru'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcphsf_aru'] = np.zeros(8760)
        tsd['Thsf_sup_shu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Thsf_re_shu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcphsf_shu'] = np.zeros(8760)

    elif control_heating_cooling_systems.has_radiator_heating_system(bpr):
        # if radiator heating system

        # Calc nominal temperatures of systems
        Qhsf_0 = np.nanmax(tsd['Qhsf'])  # in W
        #Qcsf_0 = np.nanmin(tsd['Qcsf'])  # in W in negative

        tsd['Thsf_sup_ahu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Thsf_re_ahu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcphsf_ahu'] = np.zeros(8760)
        tsd['Thsf_sup_aru'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Thsf_re_aru'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcphsf_aru'] = np.zeros(8760)

        Ths_sup, Ths_re, mcphs = np.vectorize(radiators.calc_radiator)(tsd['Qhsf'], tsd['T_int'], Qhsf_0, Ta_heating_0,
                                                                       bpr.building_systems['Ths_sup_shu_0'],
                                                                       bpr.building_systems['Ths_re_shu_0'])

        tsd['Thsf_sup_shu'] = Ths_sup
        tsd['Thsf_re_shu'] = Ths_re
        tsd['mcphsf_shu'] = mcphs

    elif control_heating_cooling_systems.has_central_ac_heating_system(bpr):

        # ahu
        # consider losses according to loads of systems
        qhsf_ahu = tsd['Qhs_sen_ahu'] + (tsd['Qhs_em_ls'] + tsd['Qhs_dis_ls']) * tsd['Qhs_sen_ahu']/tsd['Qhs_sen_sys']

        # Calc nominal temperatures of systems
        Qhsf_ahu_0 = np.nanmax(qhsf_ahu)  # in W

        index = np.where(qhsf_ahu == Qhsf_ahu_0)
        ma_sup_0 = tsd['ma_sup_hs_ahu'][index[0][0]]
        Ta_sup_0 = tsd['ta_sup_hs_ahu'][index[0][0]] + 273
        Ta_re_0 = tsd['ta_re_hs_ahu'][index[0][0]] + 273
        Ths_sup, Ths_re, mcphs = np.vectorize(heating_coils.calc_heating_coil)(qhsf_ahu, Qhsf_ahu_0, tsd['ta_sup_hs_ahu'],
                                                                               tsd['ta_re_hs_ahu'],
                                                                               bpr.building_systems['Ths_sup_ahu_0'],
                                                                               bpr.building_systems['Ths_re_ahu_0'],
                                                                               tsd['ma_sup_hs_ahu'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, gv.Cpa)
        tsd['Thsf_sup_ahu'] = Ths_sup  # in C
        tsd['Thsf_re_ahu'] = Ths_re  # in C
        tsd['mcphsf_ahu'] = mcphs

        # ARU
        # consider losses according to loads of systems
        qhsf_aru = tsd['Qhs_sen_aru'] + (tsd['Qhs_em_ls'] + tsd['Qhs_dis_ls']) * tsd['Qhs_sen_aru'] / tsd['Qhs_sen_sys']

        # Calc nominal temperatures of systems
        Qhsf_aru_0 = np.nanmax(qhsf_aru)  # in W

        index = np.where(qhsf_aru == Qhsf_aru_0)
        ma_sup_0 = tsd['ma_sup_hs_aru'][index[0][0]]
        Ta_sup_0 = tsd['ta_sup_hs_aru'][index[0][0]] + 273
        Ta_re_0 = tsd['ta_re_hs_aru'][index[0][0]] + 273
        Ths_sup, Ths_re, mcphs = np.vectorize(heating_coils.calc_heating_coil)(qhsf_aru, Qhsf_aru_0,
                                                                               tsd['ta_sup_hs_aru'],
                                                                               tsd['ta_re_hs_aru'],
                                                                               bpr.building_systems['Ths_sup_aru_0'],
                                                                               bpr.building_systems['Ths_re_aru_0'],
                                                                               tsd['ma_sup_hs_aru'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, gv.Cpa)
        tsd['Thsf_sup_ahu'] = Ths_sup  # in C
        tsd['Thsf_re_ahu'] = Ths_re  # in C
        tsd['mcphsf_ahu'] = mcphs

        # SHU
        tsd['Thsf_sup_shu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Thsf_re_shu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcphsf_shu'] = np.zeros(8760)

    else:
        raise Exception('Heating system not defined in function: "calc_temperatures_emission_systems"')


    #
    # TEMPERATURES COOLING SYSTEMS
    #
    if not control_heating_cooling_systems.has_cooling_system(bpr):
        # if no heating system

        tsd['Tcsf_sup_ahu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Tcsf_re_ahu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcpcsf_ahu'] = np.zeros(8760)
        tsd['Tcsf_sup_aru'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Tcsf_re_aru'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcpcsf_aru'] = np.zeros(8760)
        tsd['Tcsf_sup_scu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Tcsf_re_scu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcpcsf_scu'] = np.zeros(8760)

    elif control_heating_cooling_systems.has_central_ac_cooling_system(bpr):

        # AHU
        # consider losses according to loads of systems
        frac_ahu = [ahu / sys if sys < 0 else 0 for ahu, sys in zip(tsd['Qcs_sen_ahu'], tsd['Qcs_sen_sys'])]
        qcsf_ahu = tsd['Qcs_sen_ahu'] + (tsd['Qcs_em_ls'] + tsd['Qcs_dis_ls']) * frac_ahu

        # Calc nominal temperatures of systems
        Qcsf_ahu_0 = np.nanmin(qcsf_ahu)  # in W

        index = np.where(qcsf_ahu == Qcsf_ahu_0)
        ma_sup_0 = tsd['ma_sup_cs_ahu'][index[0][0]]
        Ta_sup_0 = tsd['ta_sup_cs_ahu'][index[0][0]] + 273
        Ta_re_0 = tsd['ta_re_cs_ahu'][index[0][0]] + 273
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(qcsf_ahu, Qcsf_ahu_0, tsd['ta_sup_cs_ahu'],
                                                                               tsd['ta_re_cs_ahu'],
                                                                               bpr.building_systems['Tcs_sup_ahu_0'],
                                                                               bpr.building_systems['Tcs_re_ahu_0'],
                                                                               tsd['ma_sup_cs_ahu'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, gv.Cpa)
        tsd['Tcsf_sup_ahu'] = Tcs_sup  # in C
        tsd['Tcsf_re_ahu'] = Tcs_re  # in C
        tsd['mcpcsf_ahu'] = mcpcs

        # ARU
        # consider losses according to loads of systems
        frac_aru = [aru / sys if sys < 0 else 0 for aru, sys in zip(tsd['Qcs_sen_aru'], tsd['Qcs_sen_sys'])]
        qcsf_aru = tsd['Qcs_sen_aru'] + (tsd['Qcs_em_ls'] + tsd['Qcs_dis_ls']) * frac_aru

        # Calc nominal temperatures of systems
        Qcsf_aru_0 = np.nanmin(qcsf_aru)  # in W

        index = np.where(qcsf_aru == Qcsf_aru_0)
        ma_sup_0 = tsd['ma_sup_cs_aru'][index[0][0]]
        Ta_sup_0 = tsd['ta_sup_cs_aru'][index[0][0]] + 273
        Ta_re_0 = tsd['ta_re_cs_aru'][index[0][0]] + 273
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(qcsf_aru, Qcsf_aru_0, tsd['ta_sup_cs_aru'],
                                                                               tsd['ta_re_cs_aru'],
                                                                               bpr.building_systems['Tcs_sup_aru_0'],
                                                                               bpr.building_systems['Tcs_re_aru_0'],
                                                                               tsd['ma_sup_cs_aru'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, gv.Cpa)
        tsd['Tcsf_sup_aru'] = Tcs_sup  # in C
        tsd['Tcsf_re_aru'] = Tcs_re  # in C
        tsd['mcpcsf_aru'] = mcpcs

        # SHU
        tsd['Thsf_sup_shu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Thsf_re_shu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcphsf_shu'] = np.zeros(8760)

    elif control_heating_cooling_systems.has_local_ac_cooling_system(bpr):

        # AHU
        tsd['Tcsf_sup_ahu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Tcsf_re_ahu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcpcsf_ahu'] = np.zeros(8760)

        # ARU
        # consider losses according to loads of systems
        qcsf_aru = tsd['Qcs_sen_aru'] + (tsd['Qcs_em_ls'] + tsd['Qcs_dis_ls']) * tsd['Qcs_sen_aru'] / tsd['Qcs_sen_sys'] #FIXME: not necessary, check!

        # Calc nominal temperatures of systems
        Qcsf_aru_0 = np.nanmax(qcsf_aru)  # in W

        index = np.where(qcsf_aru == Qcsf_aru_0)
        ma_sup_0 = tsd['ma_sup_cs_aru'][index[0][0]]
        Ta_sup_0 = tsd['ta_sup_cs_aru'][index[0][0]] + 273
        Ta_re_0 = tsd['ta_re_cs_aru'][index[0][0]] + 273
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(qcsf_aru, Qcsf_aru_0,
                                                                               tsd['ta_sup_cs_aru'],
                                                                               tsd['ta_re_cs_aru'],
                                                                               bpr.building_systems['Tcs_sup_aru_0'],
                                                                               bpr.building_systems['Tcs_re_aru_0'],
                                                                               tsd['ma_sup_cs_aru'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, gv.Cpa)
        tsd['Tcsf_sup_aru'] = Tcs_sup  # in C
        tsd['Tcsf_re_aru'] = Tcs_re  # in C
        tsd['mcpcsf_aru'] = mcpcs

        # SHU
        tsd['Thsf_sup_shu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['Thsf_re_shu'] = np.zeros(8760)  # in C  #FIXME: I don't like that non-existing temperatures are 0
        tsd['mcphsf_shu'] = np.zeros(8760)

    elif control_heating_cooling_systems.has_3for2_cooling_system(bpr):

        # AHU
        # consider losses according to loads of systems
        frac_ahu = [ahu/sys if sys < 0 else 0 for ahu, sys in zip(tsd['Qcs_sen_ahu'],tsd['Qcs_sen_sys'])]
        qcsf_ahu = tsd['Qcs_sen_ahu'] + (tsd['Qcs_em_ls'] + tsd['Qcs_dis_ls']) * frac_ahu
        qcsf_ahu = np.nan_to_num(qcsf_ahu)

        # Calc nominal temperatures of systems
        Qcsf_ahu_0 = np.nanmin(qcsf_ahu)  # in W

        index = np.where(qcsf_ahu == Qcsf_ahu_0)
        ma_sup_0 = tsd['ma_sup_cs_ahu'][index[0][0]]
        Ta_sup_0 = tsd['ta_sup_cs_ahu'][index[0][0]] + 273
        Ta_re_0 = tsd['ta_re_cs_ahu'][index[0][0]] + 273
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(qcsf_ahu, Qcsf_ahu_0,
                                                                               tsd['ta_sup_cs_ahu'],
                                                                               tsd['ta_re_cs_ahu'],
                                                                               bpr.building_systems['Tcs_sup_ahu_0'],
                                                                               bpr.building_systems['Tcs_re_ahu_0'],
                                                                               tsd['ma_sup_cs_ahu'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, gv.Cpa)
        tsd['Tcsf_sup_ahu'] = Tcs_sup  # in C
        tsd['Tcsf_re_ahu'] = Tcs_re  # in C
        tsd['mcpcsf_ahu'] = mcpcs

        # ARU
        # consider losses according to loads of systems
        frac_aru = [aru / sys if sys < 0 else 0 for aru, sys in zip(tsd['Qcs_sen_aru'], tsd['Qcs_sen_sys'])]
        qcsf_aru = tsd['Qcs_sen_aru'] + (tsd['Qcs_em_ls'] + tsd['Qcs_dis_ls']) * frac_aru
        qcsf_aru = np.nan_to_num(qcsf_aru)

        # Calc nominal temperatures of systems
        Qcsf_aru_0 = np.nanmin(qcsf_aru)  # in W

        index = np.where(qcsf_aru == Qcsf_aru_0)
        ma_sup_0 = tsd['ma_sup_cs_aru'][index[0][0]]
        Ta_sup_0 = tsd['ta_sup_cs_aru'][index[0][0]] + 273
        Ta_re_0 = tsd['ta_re_cs_aru'][index[0][0]] + 273
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(qcsf_aru, Qcsf_aru_0,
                                                                               tsd['ta_sup_cs_aru'],
                                                                               tsd['ta_re_cs_aru'],
                                                                               bpr.building_systems['Tcs_sup_aru_0'],
                                                                               bpr.building_systems['Tcs_re_aru_0'],
                                                                               tsd['ma_sup_cs_aru'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, gv.Cpa)
        tsd['Tcsf_sup_aru'] = Tcs_sup  # in C
        tsd['Tcsf_re_aru'] = Tcs_re  # in C
        tsd['mcpcsf_aru'] = mcpcs

        # SCU
        # consider losses according to loads of systems
        frac_scu = [scu / sys if sys < 0 else 0 for scu, sys in zip(tsd['Qcs_sen_scu'], tsd['Qcs_sen_sys'])]
        qcsf_scu = tsd['Qcs_sen_scu'] + (tsd['Qcs_em_ls'] + tsd['Qcs_dis_ls']) * frac_scu
        qcsf_scu = np.nan_to_num(qcsf_scu)

        # Calc nominal temperatures of systems
        Qcsf_scu_0 = np.nanmin(qcsf_scu)  # in W

        Tcs_sup, Tcs_re, mcpcs = np.vectorize(radiators.calc_radiator)(qcsf_scu, tsd['T_int'], Qcsf_scu_0, Ta_cooling_0,
                                                                       bpr.building_systems['Tcs_sup_scu_0'],
                                                                       bpr.building_systems['Tcs_re_scu_0'])
        tsd['Tcsf_sup_scu'] = Tcs_sup  # in C
        tsd['Tcsf_re_scu'] = Tcs_re  # in C
        tsd['mcpcsf_scu'] = mcpcs

    else:
        raise Exception('Cooling system not defined in function: "calc_temperatures_emission_systems"')



    '''
    if bpr.hvac['type_hs'] == 'T0':
        Ths_sup = np.zeros(8760)  # in C
        Ths_re = np.zeros(8760)  # in C
        mcphs = np.zeros(8760)  # in KW/C

    if bpr.hvac['type_cs'] == 'T0':
        Tcs_re = np.zeros(8760)  # in C
        Tcs_sup = np.zeros(8760)  # in C
        mcpcs = np.zeros(8760)  # in KW/C

    if bpr.hvac['type_hs'] == 'T1' or bpr.hvac['type_hs'] == 'T2':  # radiators

        Ths_sup, Ths_re, mcphs = np.vectorize(radiators.calc_radiator)(tsd['Qhsf'], tsd['T_int'], Qhsf_0, Ta_0,
                                                                       bpr.building_systems['Ths_sup_0'],
                                                                       bpr.building_systems['Ths_re_0'])

    if bpr.hvac['type_hs'] == 'T3':  # air conditioning
        index = np.where(tsd['Qhsf'] == Qhsf_0)
        ma_sup_0 = tsd['ma_sup_hs'][index[0][0]]
        Ta_sup_0 = tsd['Ta_sup_hs'][index[0][0]] + 273
        Ta_re_0 = tsd['Ta_re_hs'][index[0][0]] + 273
        Ths_sup, Ths_re, mcphs = np.vectorize(heating_coils.calc_heating_coil)(tsd['Qhsf'], Qhsf_0, tsd['Ta_sup_hs'],
                                                                               tsd['Ta_re_hs'],
                                                                               bpr.building_systems['Ths_sup_0'],
                                                                               bpr.building_systems['Ths_re_0'],
                                                                               tsd['ma_sup_hs'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, gv.Cpa, gv)

    if bpr.hvac['type_cs'] == 'T2':  # mini-split units

        index = np.where(tsd['Qcsf'] == Qcsf_0)
        ma_sup_0 = tsd['ma_sup_cs'][index[0][0]]
        Ta_sup_0 = tsd['Ta_sup_cs'][index[0][0]] + 273
        Ta_re_0 = tsd['Ta_re_cs'][index[0][0]] + 273
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(tsd['Qcsf'], Qcsf_0, tsd['Ta_sup_cs'],
                                                                               tsd['Ta_re_cs'],
                                                                               bpr.building_systems['Tcs_sup_0'],
                                                                               bpr.building_systems['Tcs_re_0'],
                                                                               tsd['ma_sup_cs'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, gv.Cpa, gv)

    if bpr.hvac['type_cs'] == 'T3':  # air conditioning

        index = np.where(tsd['Qcsf'] == Qcsf_0)
        ma_sup_0 = tsd['ma_sup_cs'][index[0][0]]
        Ta_sup_0 = tsd['Ta_sup_cs'][index[0][0]] + 273
        Ta_re_0 = tsd['Ta_re_cs'][index[0][0]] + 273
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(tsd['Qcsf'], Qcsf_0, tsd['Ta_sup_cs'],
                                                                               tsd['Ta_re_cs'],
                                                                               bpr.building_systems['Tcs_sup_0'],
                                                                               bpr.building_systems['Tcs_re_0'],
                                                                               tsd['ma_sup_cs'], ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0, gv.Cpa, gv)

    if bpr.hvac['type_hs'] == 'T4':  # floor heating

        Ths_sup, Ths_re, mcphs = np.vectorize(tabs.calc_floorheating)(tsd['Qhsf'], tsd['theta_m'], Qhsf_0,
                                                                      bpr.building_systems['Ths_sup_0'],
                                                                      bpr.building_systems['Ths_re_0'],
                                                                      bpr.rc_model['Af'])

    
    return Tcs_re, Tcs_sup, Ths_re, Ths_sup, mcpcs, mcphs  # C,C, C,C, W/C, W/C

    '''

# space heating/cooling losses

Bf = globalvar.GlobalVariables().Bf
D = globalvar.GlobalVariables().D


def calc_q_dis_ls_heating_cooling(bpr, tsd):

    """calculates distribution losses based on ISO 15316"""
    # Calculate tamb in basement according to EN

    ### modified from legacy

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

    tamb = tair - Bf * (tair - text)

    if tsd['Qhs_sen_ahu'].any() > 0:
        qhs_sen_ahu_incl_em_ls = tsd['Qhs_sen_ahu'] + tsd['Qhs_em_ls'] * (tsd['Qhs_sen_ahu']/tsd['Qhs_sen_sys'])
        qhs_sen_ahu_incl_em_ls = np.nan_to_num(qhs_sen_ahu_incl_em_ls)
        Qhs_d_ls_ahu = ((tsh_ahu + trh_ahu) / 2 - tamb) * (
        qhs_sen_ahu_incl_em_ls / np.nanmax(qhs_sen_ahu_incl_em_ls)) * (Lv * Y)

    else:
        Qhs_d_ls_ahu = np.zeros(8760)

    if tsd['Qhs_sen_aru'].any() > 0:
        qhs_sen_aru_incl_em_ls = tsd['Qhs_sen_aru'] + tsd['Qhs_em_ls'] * (tsd['Qhs_sen_aru']/tsd['Qhs_sen_sys'])
        qhs_sen_aru_incl_em_ls = np.nan_to_num(qhs_sen_aru_incl_em_ls)
        Qhs_d_ls_aru = ((tsh_aru + trh_aru) / 2 - tamb) * (
        qhs_sen_aru_incl_em_ls / np.nanmax(qhs_sen_aru_incl_em_ls)) * (
                           Lv * Y)
    else:
        Qhs_d_ls_aru = np.zeros(8760)

    if tsd['Qhs_sen_shu'].any() > 0:
        frac_shu = [shu / sys if sys < 0 else 0 for shu, sys in zip(tsd['Qhs_sen_shu'], tsd['Qhs_sen_sys'])]
        qhs_sen_shu_incl_em_ls = tsd['Qhs_sen_shu'] + tsd['Qhs_em_ls'] * frac_shu
        qhs_sen_shu_incl_em_ls = np.nan_to_num(qhs_sen_shu_incl_em_ls)
        Qhs_d_ls_shu = ((tsh_shu + trh_shu) / 2 - tamb) * (
        qhs_sen_shu_incl_em_ls / np.nanmax(qhs_sen_shu_incl_em_ls)) * (
                           Lv * Y)
    else:
        Qhs_d_ls_shu = np.zeros(8760)

    if tsd['Qcs_sen_ahu'].any() < 0:
        qcs_sen_ahu_incl_em_ls = tsd['Qcs_sen_ahu'] + tsd['Qcs_em_ls'] * np.divide(tsd['Qcs_sen_ahu'], tsd['Qcs_sen_sys'])
        qcs_sen_ahu_incl_em_ls = np.nan_to_num(qcs_sen_ahu_incl_em_ls)
        Qcs_d_ls_ahu = ((tsc_ahu + trc_ahu) / 2 - tamb) * (qcs_sen_ahu_incl_em_ls / np.nanmin(qcs_sen_ahu_incl_em_ls)) * (Lv * Y)
    else:
        Qcs_d_ls_ahu = np.zeros(8760)

    if tsd['Qcs_sen_aru'].any() < 0:
        qcs_sen_aru_incl_em_ls = tsd['Qcs_sen_aru'] + tsd['Qcs_em_ls'] * (tsd['Qcs_sen_aru']/tsd['Qcs_sen_sys'])
        qcs_sen_aru_incl_em_ls = np.nan_to_num(qcs_sen_aru_incl_em_ls)
        Qcs_d_ls_aru = ((tsc_aru + trc_aru) / 2 - tamb) * (qcs_sen_aru_incl_em_ls / np.nanmin(qcs_sen_aru_incl_em_ls)) * (
        Lv * Y)
    else:
        Qcs_d_ls_aru = np.zeros(8760)

    if tsd['Qcs_sen_scu'].any() < 0:
        qcs_sen_scu_incl_em_ls = tsd['Qcs_sen_scu'] + tsd['Qcs_em_ls'] * (tsd['Qcs_sen_scu']/tsd['Qcs_sen_sys'])
        qcs_sen_scu_incl_em_ls = np.nan_to_num(qcs_sen_scu_incl_em_ls)
        Qcs_d_ls_scu = ((tsc_scu + trc_scu) / 2 - tamb) * (qcs_sen_scu_incl_em_ls / np.nanmin(qcs_sen_scu_incl_em_ls)) * (
        Lv * Y)
    else:
        Qcs_d_ls_scu = np.zeros(8760)

    tsd['Qhs_dis_ls'] = Qhs_d_ls_ahu + Qhs_d_ls_aru + Qhs_d_ls_shu
    tsd['Qcs_dis_ls'] = Qcs_d_ls_ahu + Qcs_d_ls_aru + Qcs_d_ls_scu


def calc_Qhs_Qcs_dis_ls(tair, text, Qhs, Qcs, tsh, trh, tsc, trc, Qhs_max, Qcs_max, D, Y, SystemH, SystemC, Bf, Lv):
    """calculates distribution losses based on ISO 15316"""
    # Calculate tamb in basement according to EN

    tair = tsd['T_int']
    text = tsd['T_ext']
    Qhs = tsd['Qhs_sen_incl_em_ls'],
    Qcs = tsd['Qcs_sen_incl_em_ls'],
    tsh = bpr.building_systems['Ths_sup_0'],
    tsc = bpr.building_systems['Ths_re_0'],
    tsbpr.building_systems['Tcs_sup_0'],
    bpr.building_systems['Tcs_re_0'],
    np.nanmax(tsd['Qhs_sen_incl_em_ls']),
    np.nanmin(tsd['Qcs_sen_incl_em_ls']),
    gv.D, bpr.building_systems['Y'][0],
    bpr.hvac['type_hs'],
    bpr.hvac['type_cs'], gv.Bf,
    bpr.building_systems['Lv']




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

# -*- coding: utf-8 -*-
"""




"""
# TODO: documentation


from __future__ import division
import numpy as np
import cea.functions as functions
import hvac_kaempf
import ventilation
import pandas as pd


def calc_tHC_corr(SystemH, SystemC, sys_e_ctrl):
    """
    Model of losses in the emission and control system for space heating and cooling.

    correction factor for the heating and cooling setpoints. extracted from EN 15316-2
    Credits to: Shanshan

    Parameters
    ----------
    SystemH
    SystemC
    sys_e_ctrl

    Returns
    -------

    """

    tHC_corr = [0,0]
    delta_ctrl = [0,0]

    # emission system room temperature control type
    if sys_e_ctrl == 'T1':
        delta_ctrl = [ 2.5 , -2.5 ]
    elif sys_e_ctrl == 'T2':
        delta_ctrl = [ 1.2 , -1.2 ]
    elif sys_e_ctrl == 'T3':
        delta_ctrl = [ 0.9 , -0.9 ]
    elif sys_e_ctrl == 'T4':
        delta_ctrl = [ 1.8 , -1.8 ]

    # calculate temperature correction
    if SystemH == 'T1':
        tHC_corr[0] = delta_ctrl[0] + 0.15
    elif SystemH == 'T2':
        tHC_corr[0] = delta_ctrl[0] - 0.1
    elif SystemH == 'T3':
        tHC_corr[0] = delta_ctrl[0] - 1.1
    elif SystemH == 'T4':
        tHC_corr[0] = delta_ctrl[0] - 0.9
    else:
        tHC_corr[0] = 0


    if SystemC == 'T1':
        tHC_corr[1] = delta_ctrl[1] + 0.5
    elif SystemC == 'T2': # no emission losses but emissions for ventilation
        tHC_corr[1] = delta_ctrl[1] + 0.7
    elif SystemC == 'T3':
        tHC_corr[1] = delta_ctrl[1] + 0.5
    else:
        tHC_corr[1] = 0

    return tHC_corr[0], tHC_corr[1]


def calc_h_ve_adj(q_m_mech, q_m_nat, temp_ext, temp_sup, temp_zone_set, gv):
    """
    calculate Hve,adj according to ISO 13790

    Parameters
    ----------
    q_m_mech : air mass flow from mechanical ventilation (kg/s)
    q_m_nat : air mass flow from windows and leakages and other natural ventilation (kg/s)
    temp_ext
    temp_sup
    temp_zone_set
    gv

    Returns
    -------
    Hve in (W/K)

    """

    c_p_air = gv.Cpa  # (kJ/(kg*K)) # TODO: maybe dynamic heat capacity of air f(temp)
    if abs(temp_sup - temp_ext) == 0:
        b_mech = 1
    else:
        eta_hru = (temp_sup - temp_ext) / (temp_zone_set - temp_ext)  # Eq. (28) in ISO 13970
        frac_hru = 1
        b_mech = (1 - frac_hru * eta_hru)  # Eq. (27) in ISO 13970

    return (b_mech * q_m_mech + q_m_nat) * c_p_air * 1000  # (W/K), Eq. (21) in ISO 13970


def calc_qm_ve_req(ve_schedule, area_f, temp_ext):
    """
    Calculates required mass flow rate of ventilation from schedules,
    modified version of 'functions.calc_qv_req()'

    Parameters
    ----------
    ve_schedule
    area_f
    temp_ext

    Returns
    -------
    qm_ve_req
    """

    qm_ve_req = ve_schedule * area_f / 3600 * ventilation.calc_rho_air(temp_ext)  # (kg/s)

    return qm_ve_req


def calc_thermal_load_hvac_timestep(t, dict_locals):
    """
    This function is executed for the case of heating or cooling with a HVAC system
    by coupling the R-C model of ISO 13790 with the HVAC model of Kaempf

    For this case natural ventilation is not considered

    Author: Gabriel Happle
    Date: May 2016

    Parameters
    ----------
    t : time step, hour of year [0..8760]
    dict_locals : locals() from calling function

    Returns
    -------
    temp_m, temp_a, q_hs_sen, q_cs_sen, uncomfort, temp_op, i_m_tot, q_hs_sen_hvac, q_cs_sen_hvac, q_hum_hvac,
     q_dhum_hvac, e_hum_aux_hvac, q_ve_loss, qm_ve_mech
    """

    # get arguments from locals
    qm_ve_req = dict_locals['qm_ve_req'][t]
    temp_ext = dict_locals['T_ext'][t]
    temp_hs_set = dict_locals['ta_hs_set'][t]
    temp_cs_set = dict_locals['ta_cs_set'][t]
    i_st = dict_locals['i_st'][t]
    i_ia = dict_locals['i_ia'][t]
    i_m = dict_locals['i_m'][t]
    flag_season = dict_locals['flag_season'][t]
    rh_ext = dict_locals['rh_ext'][t]
    w_int = dict_locals['w_int'][t]

    temp_air_prev = dict_locals['temp_air_prev']
    temp_m_prev = dict_locals['temp_m_prev']
    system_heating = dict_locals['sys_e_heating']
    system_cooling = dict_locals['sys_e_cooling']
    cm = dict_locals['cm']
    area_f = dict_locals['Af']
    temp_hs_set_corr = dict_locals['tHset_corr']
    temp_cs_set_corr = dict_locals['tCset_corr']
    i_c_max = dict_locals['i_c_max']
    i_h_max = dict_locals['i_h_max']
    temp_sup_heat = dict_locals['temp_sup_heat']
    temp_sup_cool = dict_locals['temp_sup_cool']
    gv = dict_locals['gv']

    limit_inf_season = dict_locals['limit_inf_season']
    limit_sup_season = dict_locals['limit_sup_season']

    # get constant properties of building R-C-model
    h_tr_is = dict_locals['prop_rc_model'].Htr_is
    h_tr_ms = dict_locals['prop_rc_model'].Htr_ms
    h_tr_w = dict_locals['prop_rc_model'].Htr_w
    h_tr_em = dict_locals['prop_rc_model'].Htr_em


    # first guess of mechanical ventilation mass flow rate and supply temperature for ventilation losses
    qm_ve_mech = qm_ve_req  # required air mass flow rate
    qm_ve_nat = 0  # natural ventilation # TODO: this could be a fixed percentage of the mechanical ventilation (overpressure) as a function of n50
    temp_ve_sup = hvac_kaempf.calc_hex(rh_ext, gv, qv_mech=(qm_ve_req/gv.Pair), qv_mech_dim=0, temp_ext=temp_ext,
                                            temp_zone_prev=temp_air_prev, timestep=t,
                                           stop_heating_season=limit_inf_season, start_heating_season=limit_sup_season )[0]

    qv_ve_req = qm_ve_req / ventilation.calc_rho_air(
        temp_ext)  # TODO: modify Kaempf model to accept mass flow rate instead of volume flow

    rel_diff_qm_ve_mech = 1  # initialisation of difference for while loop
    abs_diff_qm_ve_mech = 1
    rel_tolerance = 0.05  # 5% change  # TODO review tolerance
    abs_tolerance = 0.01  # 10g/s air flow  # TODO  review tolerance
    hvac_status_prev = 0  # system is turned OFF
    switch = 0

    # iterative loop to determine air mass flows and supply temperatures of the hvac system
    while (abs_diff_qm_ve_mech > abs_tolerance) and (rel_diff_qm_ve_mech > rel_tolerance) and switch < 10:

        # Hve
        h_ve = calc_h_ve_adj(qm_ve_mech, qm_ve_nat, temp_ext, temp_ve_sup, temp_air_prev, gv)  # TODO

        # Htr1, Htr2, Htr3
        h_tr_1, h_tr_2, h_tr_3 = functions.calc_Htr(h_ve, h_tr_is, h_tr_ms, h_tr_w)

        # TODO: adjust calc TL function to new way of losses calculation (adjust input parameters)
        Losses = True  # including emission and control losses for the iteration of air mass flow rate

        # calc_TL()
        temp_m_loss_true,\
        temp_a_loss_true,\
        q_hs_sen_loss_true,\
        q_cs_sen_loss_true,\
        uncomfort_loss_true,\
        temp_op_loss_true,\
        i_m_tot_loss_true = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set, temp_cs_set,
                                    h_tr_em, h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve, h_tr_w, i_ia, i_m,
                                    cm, area_f, Losses, temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max,
                                    flag_season)

        # calculate sensible heat load
        Losses = False  # Losses are set to false for the calculation of the sensible heat load and actual temperatures

        temp_m, \
        temp_a, \
        q_hs_sen, \
        q_cs_sen, \
        uncomfort, \
        temp_op, \
        i_m_tot = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set, temp_cs_set,
                                    h_tr_em, h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve, h_tr_w, i_ia,
                                    i_m, cm,
                                    area_f, Losses, temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max,
                                    flag_season)

        # ventilation losses
        q_ve_loss = h_ve*(temp_a - temp_ext)
        # q_ve_loss = qm_ve_mech * gv.Cpa * (temp_a - temp_ve_sup) * 1000  # (W/s) # TODO make air heat capacity dynamic

        # HVAC supplies load if zone has load
        if q_hs_sen > 0:
            hvac_status = 1  # system is ON
            print('HVAC ON')
            q_sen_load_hvac = q_hs_sen_loss_true  #
        elif q_cs_sen < 0:
            hvac_status = 1  # system is ON
            print('HVAC ON')
            q_sen_load_hvac = q_cs_sen_loss_true  #
        else:
            hvac_status = 0  # system is OFF
            print('HVAC OFF')
            q_sen_load_hvac = 0

        # temperature set point
        t_air_set = temp_a

        # calc_HVAC()
        q_hs_sen_hvac,\
        q_cs_sen_hvac,\
        q_hum_hvac,\
        q_dhum_hvac,\
        e_hum_aux_hvac,\
        qm_ve_hvac_h,\
        qm_ve_hvac_c,\
        temp_sup_h,\
        temp_sup_c,\
        temp_rec_h,\
        temp_rec_c,\
        w_rec,\
        w_sup,\
        temp_air = hvac_kaempf.calc_hvac(rh_ext, temp_ext, t_air_set, qv_ve_req, q_sen_load_hvac, temp_air_prev,
                                         w_int, gv, temp_sup_heat, temp_sup_cool, t, limit_inf_season, limit_sup_season)

        # mass flow rate output for cooling or heating is zero if the hvac is used only for ventilation
        qm_ve_hvac = max(qm_ve_hvac_h, qm_ve_hvac_c, qm_ve_req)  # ventilation mass flow rate of hvac system

        # calculate thermal loads with hvac mass flow rate in next iteration
        qm_ve_nat = 0  # natural ventilation
        temp_ve_sup = np.nanmax([temp_rec_h, temp_rec_c])

        # compare mass flow rates
        abs_diff_qm_ve_mech = abs(qm_ve_hvac - qm_ve_mech)
        rel_diff_qm_ve_mech = abs_diff_qm_ve_mech / qm_ve_mech
        if hvac_status_prev != hvac_status:
            switch += 1
        qm_ve_mech = qm_ve_hvac
        hvac_status_prev = hvac_status

    # calculate emission losses
    # emission losses only if heating system or cooling system is in operation (q_hs_sen > 0 or q_cs_sen < 0)
    if q_hs_sen > 0:
        qhs_em_ls = q_hs_sen_loss_true - q_hs_sen
    else:
        q_hs_sen_loss_true = 0
        qhs_em_ls = 0
    if q_cs_sen < 0:
        qcs_em_ls = q_cs_sen_loss_true - q_cs_sen
    else:
        q_cs_sen_loss_true = 0
        qcs_em_ls = 0

    return temp_m, temp_a, q_hs_sen_loss_true, q_cs_sen_loss_true, uncomfort,\
           temp_op, i_m_tot, q_hs_sen_hvac, q_cs_sen_hvac, q_hum_hvac, q_dhum_hvac, e_hum_aux_hvac,\
           q_ve_loss, qm_ve_mech, q_hs_sen, q_cs_sen, qhs_em_ls, qcs_em_ls


def calc_thermal_load_mechanical_ventilation_timestep(t, dict_locals):
    """
    This function is executed for the case of mechanical ventilation with outdoor air

    Assumptions:
    - Mechanical ventilation is controlled in a way that required ventilation rates are always met (CO2-sensor based
        or similar control)
    - No natural ventilation

    Parameters
    ----------
    t : time step, hour of year [0..8760]
    dict_locals : locals() from calling function

    Returns
    -------
    temp_m, temp_a, q_hs_sen, q_cs_sen, uncomfort, temp_op, i_m_tot, qm_ve_mech
    """

    # get arguments from locals
    qm_ve_req = dict_locals['qm_ve_req'][t]
    temp_ext = dict_locals['T_ext'][t]
    temp_hs_set = dict_locals['ta_hs_set'][t]
    temp_cs_set = dict_locals['ta_cs_set'][t]
    i_st = dict_locals['i_st'][t]
    i_ia = dict_locals['i_ia'][t]
    i_m = dict_locals['i_m'][t]
    flag_season = dict_locals['flag_season'][t]

    temp_air_prev = dict_locals['temp_air_prev']
    temp_m_prev = dict_locals['temp_m_prev']
    system_heating = dict_locals['sys_e_heating']
    system_cooling = dict_locals['sys_e_cooling']
    cm = dict_locals['cm']
    area_f = dict_locals['Af']
    temp_hs_set_corr = dict_locals['tHset_corr']
    temp_cs_set_corr = dict_locals['tCset_corr']
    i_c_max = dict_locals['i_c_max']
    i_h_max = dict_locals['i_h_max']
    gv = dict_locals['gv']

    # get constant properties of building R-C-model
    h_tr_is = dict_locals['prop_rc_model'].Htr_is
    h_tr_ms = dict_locals['prop_rc_model'].Htr_ms
    h_tr_w = dict_locals['prop_rc_model'].Htr_w
    h_tr_em = dict_locals['prop_rc_model'].Htr_em

    # mass flow rate of mechanical ventilation
    qm_ve_mech = qm_ve_req  # required air mass flow rate

    qm_ve_nat = 0  # natural ventilation

    temp_ve_sup = temp_ext  # mechanical ventilation without heat exchanger

    # calc hve
    h_ve = calc_h_ve_adj(qm_ve_mech, qm_ve_nat, temp_ext, temp_ve_sup, temp_air_prev, gv)

    # calc htr1, htr2, htr3
    h_tr_1, h_tr_2, h_tr_3 = functions.calc_Htr(h_ve, h_tr_is, h_tr_ms, h_tr_w)

    Losses = False  # TODO: adjust calc TL function to new way of losses calculation (adjust input parameters)

    # calc_TL()
    temp_m,\
    temp_a,\
    q_hs_sen,\
    q_cs_sen,\
    uncomfort,\
    temp_op,\
    i_m_tot = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set, temp_cs_set,
                                h_tr_em, h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve, h_tr_w, i_ia, i_m, cm,
                                area_f, Losses, temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max, flag_season)

    # calculate emission losses
    Losses = True
    temp_m_loss_true,\
    temp_a_loss_true,\
    q_hs_sen_loss_true,\
    q_cs_sen_loss_true,\
    uncomfort_loss_true,\
    temp_op_loss_true,\
    i_m_tot_loss_true = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set,
                                            temp_cs_set, h_tr_em, h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve,
                                            h_tr_w, i_ia, i_m, cm, area_f, Losses, temp_hs_set_corr, temp_cs_set_corr,
                                            i_c_max, i_h_max, flag_season)

    # calculate emission losses
    # emission losses only if heating system or cooling system is in operation (q_hs_sen > 0 or q_cs_sen < 0)
    if q_hs_sen > 0:
        qhs_em_ls = q_hs_sen_loss_true - q_hs_sen
    else:
        q_hs_sen_loss_true = 0
        qhs_em_ls = 0
    if q_cs_sen < 0:
        qcs_em_ls = q_cs_sen_loss_true - q_cs_sen
    else:
        q_cs_sen_loss_true = 0
        qcs_em_ls = 0

    return temp_m, temp_a, q_hs_sen_loss_true, q_cs_sen_loss_true, uncomfort,\
           temp_op, i_m_tot, qm_ve_mech, q_hs_sen, q_cs_sen, qhs_em_ls, qcs_em_ls


def calc_thermal_load_natural_ventilation_timestep(t, dict_locals):
    """
    This function is executed in the case of naturally ventilated buildings.
    Infiltration and window ventilation are considered. If infiltration provides enough air mass flow to satisfy the
    ventilation requirements, windows remain closed. Otherwise windows are incrementally opened.
    Windows are further opened to prevent buildings from over heating, i.e. reach an uncomfortable air temperature.

    Author: Gabriel Happle
    Date: May 2016

    Parameters
    ----------
    t : time step, hour of year [0..8760]
    dict_locals : locals() from calling function

    Returns
    -------
    temp_m, temp_a, q_hs_sen, q_cs_sen, uncomfort, temp_op, i_m_tot, qm_ve_nat

    """

    # get arguments from locals
    qm_ve_req = dict_locals['qm_ve_req'][t]
    temp_ext = dict_locals['T_ext'][t]
    u_wind = dict_locals['u_wind'][t]
    temp_hs_set = dict_locals['ta_hs_set'][t]
    temp_cs_set = dict_locals['ta_cs_set'][t]
    i_st = dict_locals['i_st'][t]
    i_ia = dict_locals['i_ia'][t]
    i_m = dict_locals['i_m'][t]
    flag_season = dict_locals['flag_season'][t]

    temp_air_prev = dict_locals['temp_air_prev']
    temp_m_prev = dict_locals['temp_m_prev']
    system_heating = dict_locals['sys_e_heating']
    system_cooling = dict_locals['sys_e_cooling']
    cm = dict_locals['cm']
    area_f = dict_locals['Af']
    temp_hs_set_corr = dict_locals['tHset_corr']
    temp_cs_set_corr = dict_locals['tCset_corr']
    i_c_max = dict_locals['i_c_max']
    i_h_max = dict_locals['i_h_max']
    dict_windows_building = dict_locals['dict_windows_building']
    factor_cros = dict_locals['factor_cros']
    temp_comf_max = dict_locals['temp_comf_max']
    gv = dict_locals['gv']

    # FIXME: this is quite problematic, as it is not clear visible that this is needed in ventilation.calc_air_flows(...,locals())
    dict_props_nat_vent = dict_locals['dict_props_nat_vent']

    # get constant properties of building R-C-model
    h_tr_is = dict_locals['prop_rc_model'].Htr_is
    h_tr_ms = dict_locals['prop_rc_model'].Htr_ms
    h_tr_w = dict_locals['prop_rc_model'].Htr_w
    h_tr_em = dict_locals['prop_rc_model'].Htr_em



    # qm_ve_req = qv_req * ventilation.calc_rho_air(temp_ext)  # TODO
    qm_ve_mech = 0  # mechanical ventilation mass flow rate

    # test if ventilation from infiltration is already enough to satisfy the requirements

    qm_arg_in = qm_arg_out = 0  # test ventilation with closed windows
    # infiltration and ventilation openings
    qm_ve_in, qm_ve_out = ventilation.calc_air_flows(temp_air_prev, u_wind, temp_ext, locals())  # (kg/h)
    qm_ve_nat_tot = (qm_ve_in + qm_arg_in) / 3600  # total natural ventilation mass flow rate (kg/s)

    # if building has windows
    if dict_windows_building:
        status_windows = np.array([0.01, 0.05, 0.1, 0.2, 0.5])

        # test if air flows satisfy requirements

        index_window_opening = 0
        while qm_ve_nat_tot < qm_ve_req and index_window_opening < status_windows.size:

            # increase window opening
            print('increase window opening')
            # window air flows
            qm_arg_in, qm_arg_out = ventilation.calc_qm_arg(factor_cros, temp_ext, dict_windows_building, u_wind,
                                                            temp_air_prev, status_windows[index_window_opening])

            # total air flows
            # qm_ve_sum_in, qm_ve_sum_out = ventilation.calc_air_flows(temp_air_prev, u_wind, temp_ext, locals())

            qm_ve_nat_tot = (qm_ve_in + qm_arg_in) / 3600  # total natural ventilation mass flow rate (kg/s)

            index_window_opening += 1

        # calculate h_ve
        h_ve = calc_h_ve_adj(qm_ve_mech, qm_ve_nat_tot, temp_ext, temp_ext, temp_air_prev, gv)  # (kJ/(hK))

        # calculate htr1, htr2, htr3
        h_tr_1, h_tr_2, h_tr_3 = functions.calc_Htr(h_ve, h_tr_is, h_tr_ms, h_tr_w)

        # calculate air temperature with emission and control losses
        Losses = False  # TODO: adjust calc TL function to new way of losses calculation (adjust input parameters)

        # calc_TL()
        temp_m,\
        temp_a,\
        q_hs_sen,\
        q_cs_sen,\
        uncomfort,\
        temp_op,\
        i_m_tot = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set, temp_cs_set,
                                    h_tr_em, h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve, h_tr_w, i_ia, i_m, cm,
                                    area_f, Losses, temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max, flag_season)

        # test for overheating
        while temp_a > temp_comf_max and index_window_opening < status_windows.size:

            # increase window opening to prevent overheating
            print('increase window opening to prevent over heating')
            # window air flows
            qm_arg_in, qm_arg_out = ventilation.calc_qm_arg(factor_cros, temp_ext, dict_windows_building, u_wind,
                                                        temp_air_prev, status_windows[index_window_opening])

            # total air flows
            # qm_ve_sum_in, qm_ve_sum_out = ventilation.calc_air_flows(temp_air_prev, u_wind, temp_ext, locals())

            qm_ve_nat_tot = (qm_ve_in + qm_arg_in) / 3600  # total natural ventilation mass flow rate (kg/s)

            index_window_opening += 1

            # calculate h_ve
            h_ve = calc_h_ve_adj(qm_ve_mech, qm_ve_nat_tot, temp_ext, temp_ext, temp_air_prev, gv)  # (kJ/(hK))

            # calculate htr1, htr2, htr3
            h_tr_1, h_tr_2, h_tr_3 = functions.calc_Htr(h_ve, h_tr_is, h_tr_ms, h_tr_w)

            # calc_TL()
            temp_m,\
            temp_a,\
            q_hs_sen,\
            q_cs_sen,\
            uncomfort,\
            temp_op,\
            i_m_tot = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set, temp_cs_set,
                                        h_tr_em, h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve, h_tr_w, i_ia, i_m,
                                        cm, area_f, Losses, temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max,
                                        flag_season)

    # no windows
    elif not dict_windows_building:
        # calculate h_ve
        h_ve = calc_h_ve_adj(qm_ve_mech, qm_ve_nat_tot, temp_ext, temp_ext, temp_air_prev, gv)  # (kJ/(hK))

        # calculate htr1, htr2, htr3
        h_tr_1, h_tr_2, h_tr_3 = functions.calc_Htr(h_ve, h_tr_is, h_tr_ms, h_tr_w)

        Losses = False

        # calc_TL()
        temp_m, \
        temp_a, \
        q_hs_sen, \
        q_cs_sen, \
        uncomfort, \
        temp_op, \
        i_m_tot = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set, temp_cs_set,
                                    h_tr_em, h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve, h_tr_w, i_ia,
                                    i_m, cm,
                                    area_f, Losses, temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max,
                                    flag_season)

    # calculate sensible heat load with Losses = False
    Losses = True
    temp_m_loss_true,\
    temp_a_loss_true,\
    q_hs_sen_loss_true,\
    q_cs_sen_loss_true,\
    uncomfort_loss_true,\
    temp_op_loss_true,\
    i_m_tot_loss_true = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set, temp_cs_set,
                          h_tr_em, h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve, h_tr_w, i_ia,
                          i_m, cm,
                          area_f, Losses, temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max,
                          flag_season)

    # calculate emission losses
    # emission losses only if heating system or cooling system is in operation (q_hs_sen > 0 or q_cs_sen < 0)
    if q_hs_sen > 0:
        qhs_em_ls = q_hs_sen_loss_true - q_hs_sen
    else:
        q_hs_sen_loss_true = 0
        qhs_em_ls = 0
    if q_cs_sen < 0:
        qcs_em_ls = q_cs_sen_loss_true - q_cs_sen
    else:
        q_cs_sen_loss_true = 0
        qcs_em_ls = 0


    return temp_m, temp_a, q_hs_sen_loss_true, q_cs_sen_loss_true, uncomfort,\
           temp_op, i_m_tot, qm_ve_nat_tot, q_hs_sen, q_cs_sen, qhs_em_ls, qcs_em_ls


def calc_thermal_loads_new_ventilation(Name, prop_rc_model, prop_hvac, prop_occupancy, prop_age, prop_architecture,
                                       prop_geometry, schedules, Solar, dict_climate,
                                       dict_windows_building, locationFinal, gv, list_uses, prop_internal_loads,
                                       prop_comfort, date, path_temporary_folder):
    """ calculates thermal loads of single buildings with mechanical or natural ventilation"""

    # get climate vectors
    # TODO: maybe move to inside of functions
    T_ext = dict_climate['temp_ext']  # external temperature (°C)
    rh_ext = dict_climate['rh_ext']  # external relative humidity (%)
    u_wind = dict_climate['u_wind']  # wind speed (m/s)

    # copied from original calc thermal loads
    Af = prop_rc_model.Af
    Aef = prop_rc_model.Aef
    sys_e_heating = prop_hvac.type_hs
    sys_e_cooling = prop_hvac.type_cs
    sys_e_ctrl = prop_hvac.type_ctrl  # room temperature control types

    # copied from original calc thermal loads
    mixed_schedule = functions.calc_mixed_schedule(list_uses, schedules, prop_occupancy)  # TODO: rename outputs

    # get internal loads
    Eal_nove,\
    Edataf,\
    Eprof,\
    Eref,\
    Qcrefri,\
    Qcdata,\
    vww,\
    vw = functions.get_internal_loads(mixed_schedule, prop_internal_loads, prop_architecture, Af)

    if Af > 0:  # building has conditioned area

        # get heating and cooling season
        limit_inf_season = gv.seasonhours[0] + 1  # TODO: maybe rename or remove
        limit_sup_season = gv.seasonhours[1]  # TODO maybe rename or remove

        # get occupancy
        people = functions.get_occupancy(mixed_schedule, prop_architecture, Af)

        # get internal comfort properties
        ve_schedule,\
        ta_hs_set,\
        ta_cs_set = functions.get_internal_comfort(people, prop_comfort, limit_inf_season, limit_sup_season, date.hour)

        # extract properties of building
        # copied from original calc thermal loads
        # geometry
        Am,\
        Atot,\
        Aw,\
        Awall_all,\
        cm,\
        Ll,\
        Lw,\
        Retrofit,\
        Sh_typ,\
        Year,\
        footprint,\
        nf_ag,\
        nfp = functions.get_properties_building_envelope(prop_rc_model, prop_age, prop_architecture, prop_geometry,
                                                          prop_occupancy)  # TODO: rename outputs

        # building systems
        Lcww_dis,\
        Lsww_dis,\
        Lv,\
        Lvww_c,\
        Lvww_dis,\
        Tcs_re_0,\
        Tcs_sup_0,\
        Ths_re_0,\
        Ths_sup_0,\
        Tww_re_0,\
        Tww_sup_0,\
        Y,\
        fforma = functions.get_properties_building_systems(Ll, Lw, Retrofit, Year, footprint, gv, nf_ag, nfp,
                                                            prop_hvac)  # TODO: rename outputs




        # minimum mass flow rate of ventilation according to schedule
        # qm_ve_req = numpy.vectorize(calc_qm_ve_req)(ve_schedule, area_f, temp_ext)
        # with infiltration and overheating
        qv_req = np.vectorize(functions.calc_qv_req)(ve_schedule, people, Af, gv, date.hour, range(8760),
                                                        limit_inf_season, limit_sup_season)
        qm_ve_req = qv_req * gv.Pair  # TODO:  use dynamic rho_air

        # heat flows in [W]
        # solar gains
        # copied from original calc thermal loads
        i_sol = functions.calc_heat_gains_solar(Aw, Awall_all, Sh_typ, Solar, gv)

        # sensible internal heat gains
        # copied from original calc thermal loads
        i_int_sen = functions.calc_heat_gains_internal_sensible(people, prop_internal_loads.Qs_Wp, Eal_nove, Eprof, Qcdata, Qcrefri)

        # components of internal heat gains for R-C-model
        # copied from original calc thermal loads
        i_ia, i_m, i_st = functions.calc_comp_heat_gains_sensible(Am, Atot, prop_rc_model.Htr_w, i_int_sen, i_sol)

        # internal moisture gains
        # copied from original calc thermal loads
        w_int = functions.calc_heat_gains_internal_latent(people, prop_internal_loads.X_ghp, sys_e_cooling, sys_e_heating)

        # heating and cooling loads
        # copied from original calc thermal loads
        i_c_max, i_h_max = functions.calc_capacity_heating_cooling_system(Af, prop_hvac)

        # natural ventilation building propertiess
        # new
        dict_props_nat_vent = ventilation.get_properties_natural_ventilation(prop_geometry, prop_architecture)

        # # factor for cross ventilation
        factor_cros = prop_architecture.f_cros  # TODO: get from building properties

        # define empty arrrays
        uncomfort = np.zeros(8760)
        Ta = np.zeros(8760)
        Tm = np.zeros(8760)
        Qhs_sen = np.zeros(8760)
        Qcs_sen = np.zeros(8760)
        Qhs_lat = np.zeros(8760)
        Qcs_lat = np.zeros(8760)
        Qhs_em_ls = np.zeros(8760)
        Qcs_em_ls = np.zeros(8760)
        QHC_sen = np.zeros(8760)
        ma_sup_hs = np.zeros(8760)
        Ta_sup_hs = np.zeros(8760)
        Ta_re_hs = np.zeros(8760)
        ma_sup_cs = np.zeros(8760)
        Ta_sup_cs = np.zeros(8760)
        Ta_re_cs = np.zeros(8760)
        w_sup = np.zeros(8760)
        w_re = np.zeros(8760)
        Ehs_lat_aux = np.zeros(8760)
        Qhs_sen_incl_em_ls = np.zeros(8760)
        Qcs_sen_incl_em_ls = np.zeros(8760)
        t5 = np.zeros(8760)
        Tww_re = np.zeros(8760)
        Top = np.zeros(8760)
        Im_tot = np.zeros(8760)
        q_hum_hvac = np.zeros(8760)
        q_dhum_hvac = np.zeros(8760)
        q_ve_loss = np.zeros(8760)
        qm_ve_mech = np.zeros(8760)
        qm_ve_nat = np.zeros(8760)

        q_hs_sen_hvac = np.zeros(8760)
        q_cs_sen_hvac = np.zeros(8760)
        e_hum_aux_hvac = np.zeros(8760)

        # create flag season
        flag_season = np.zeros(8760, dtype=bool)  # default is heating season
        flag_season[gv.seasonhours[0] + 1:gv.seasonhours[1]] = True

        # model of losses in the emission and control system for space heating and cooling
        tHset_corr, tCset_corr = calc_tHC_corr(sys_e_heating, sys_e_cooling, sys_e_ctrl)

        # we give a seed high enough to avoid doing a iteration for 2 years.
        temp_m_prev = 16
        # end-use demand calculation
        temp_air_prev = 21  # definition of first temperature to start calculation of air conditioning system

        temp_sup_heat = 35  # TODO: include to properties and get from properties
        temp_sup_cool = 16  # TODO: include to properties and get from properties
        temp_comf_max = 26  # TODO: include to properties and get from properties

        # case 1: mechanical ventilation
        if sys_e_heating == 'T3' or sys_e_cooling == 'T3':
            print('mechanical ventilation')

            for t in range(8760):
                print(t)

                # case 1a: heating or cooling with hvac
                if (sys_e_heating == 'T3' and (t <= gv.seasonhours[0] or t >= gv.seasonhours[1])) \
                        or (sys_e_cooling == 'T3' and gv.seasonhours[0] < t < gv.seasonhours[1]):
                    print('1a')

                    Tm[t],\
                    Ta[t], \
                    Qhs_sen_incl_em_ls[t], \
                    Qcs_sen_incl_em_ls[t],\
                    uncomfort[t],\
                    Top[t],\
                    Im_tot[t], \
                    q_hs_sen_hvac[t],\
                    q_cs_sen_hvac[t],\
                    q_hum_hvac[t],\
                    q_dhum_hvac[t],\
                    e_hum_aux_hvac[t],\
                    q_ve_loss[t],\
                    qm_ve_mech[t], \
                    Qhs_sen[t], \
                    Qcs_sen[t], \
                    Qhs_em_ls[t], \
                    Qcs_em_ls[t] = calc_thermal_load_hvac_timestep(t, locals())

                # case 1b: mechanical ventilation
                else:
                    print('1b')
                    Tm[t],\
                    Ta[t], \
                    Qhs_sen_incl_em_ls[t], \
                    Qcs_sen_incl_em_ls[t], \
                    uncomfort[t],\
                    Top[t],\
                    Im_tot[t],\
                    qm_ve_mech[t], \
                    Qhs_sen[t], \
                    Qcs_sen[t], \
                    Qhs_em_ls[t], \
                    Qcs_em_ls[t] = calc_thermal_load_mechanical_ventilation_timestep(t, locals())

                temp_air_prev = Ta[t]
                temp_m_prev = Tm[t]

        # case 2: natural ventilation
        else:
            print('natural ventilation')

            for t in range(8760):
                print(t)

                Tm[t],\
                Ta[t], \
                Qhs_sen_incl_em_ls[t], \
                Qcs_sen_incl_em_ls[t], \
                uncomfort[t],\
                Top[t],\
                Im_tot[t],\
                qm_ve_nat[t], \
                Qhs_sen[t], \
                Qcs_sen[t], \
                Qhs_em_ls[t], \
                Qcs_em_ls[t] = calc_thermal_load_natural_ventilation_timestep(t, locals())

                temp_air_prev = Ta[t]
                temp_m_prev = Tm[t]

        # TODO: check this out with Shanshan :)

        # Calc of Qhs_dis_ls/Qcs_dis_ls - losses due to distribution of heating/cooling coils
        # erase possible disruptions from dehumidification days
        # Qhs_sen_incl_em_ls[Qhs_sen_incl_em_ls < 0] = 0
        # Qcs_sen_incl_em_ls[Qcs_sen_incl_em_ls > 0] = 0
        Qhs_sen_incl_em_ls_0 = Qhs_sen_incl_em_ls.max()
        Qcs_sen_incl_em_ls_0 = Qcs_sen_incl_em_ls.min()  # cooling loads up to here in negative values
        Qhs_d_ls, Qcs_d_ls = np.vectorize(functions.calc_Qdis_ls)(Ta, T_ext, Qhs_sen_incl_em_ls, Qcs_sen_incl_em_ls,
                                                            Ths_sup_0, Ths_re_0, Tcs_sup_0, Tcs_re_0,
                                                            Qhs_sen_incl_em_ls_0, Qcs_sen_incl_em_ls_0,
                                                            gv.D, Y[0], sys_e_heating, sys_e_cooling, gv.Bf, Lv)

        # Calc requirements of generation systems (both cooling and heating do not have a storage):
        Qhsf = Qhs_sen_incl_em_ls + Qhs_d_ls  # no latent is considered because it is already added as electricity from the adiabatic system.
        Qcs = Qcs_sen_incl_em_ls + Qcs_lat
        Qcsf = Qcs + Qcs_d_ls
        Qcsf = -abs(Qcsf)
        Qcs = -abs(Qcs)

        # Calc nomincal temperatures of systems
        Qhsf_0 = Qhsf.max()  # in W
        Qcsf_0 = Qcsf.min()  # in W negative

        # Cal temperatures of all systems
        Tcs_re, Tcs_sup, Ths_re, Ths_sup, mcpcs, mcphs = functions.calc_temperatures_emission_systems(Qcsf, Qcsf_0, Qhsf,
                                                                                                Qhsf_0,
                                                                                                Ta, Ta_re_cs, Ta_re_hs,
                                                                                                Ta_sup_cs, Ta_sup_hs,
                                                                                                Tcs_re_0, Tcs_sup_0,
                                                                                                Ths_re_0, Ths_sup_0, gv,
                                                                                                ma_sup_cs, ma_sup_hs,
                                                                                                sys_e_cooling,
                                                                                                sys_e_heating,
                                                                                                ta_hs_set,
                                                                                                w_re, w_sup)
        Mww, Qww, Qww_ls_st, Qwwf, Qwwf_0, Tww_st, Vw, Vww, mcpww = functions.calc_dhw_heating_demand(Af, Lcww_dis, Lsww_dis,
                                                                                                Lvww_c, Lvww_dis, T_ext,
                                                                                                Ta,
                                                                                                Tww_re, Tww_sup_0, Y,
                                                                                                gv,
                                                                                                vw, vww)

        # clac auxiliary loads of pumping systems
        Eaux_cs, Eaux_fw, Eaux_hs, Eaux_ve, Eaux_ww = functions.calc_pumping_systems_aux_loads(Af, Ll, Lw, Mww, Qcsf, Qcsf_0,
                                                                                         Qhsf, Qhsf_0, Qww, Qwwf,
                                                                                         Qwwf_0,
                                                                                         Tcs_re, Tcs_sup, Ths_re,
                                                                                         Ths_sup,
                                                                                         Vw, Year, fforma, gv, nf_ag,
                                                                                         nfp,
                                                                                         qv_req, sys_e_cooling,
                                                                                         sys_e_heating)

        # Calc total auxiliary loads
        Eauxf = (Eaux_ww + Eaux_fw + Eaux_hs + Eaux_cs + Ehs_lat_aux + Eaux_ve)

        # calculate other quantities
        Occupancy = np.floor(people)
        Occupants = Occupancy.max()
        Waterconsumption = Vww + Vw  # volume of water consumed in m3/h
        waterpeak = Waterconsumption.max()

    # Af = 0: no conditioned floor area
    else:
        # scalars
        waterpeak = Occupants = 0
        Qwwf_0 = Ealf_0 = Qhsf_0 = Qcsf_0 = 0
        Ths_sup_0 = Ths_re_0 = Tcs_re_0 = Tcs_sup_0 = Tww_sup_0 = 0
        # arrays
        Occupancy = Eauxf = Waterconsumption = np.zeros(8760)
        Qwwf = Qww = Qhs_sen = Qhsf = Qcs_sen = Qcs = Qcsf = Qcdata = Qcrefri = Qd = Qc = Qww_ls_st = np.zeros(8760)
        Ths_sup = Ths_re = Tcs_re = Tcs_sup = mcphs = mcpcs = mcpww = Vww = Tww_re = Tww_st = uncomfort = np.zeros(
            8760)  # in C

    # calc electrical loads
    Ealf, Ealf_0, Ealf_tot, Eauxf_tot, Edata, Edata_tot, Epro, Epro_tot = functions.calc_loads_electrical(Aef, Eal_nove,
                                                                                                Eauxf, Edataf, Eprof)

    # write results to csv
    functions.results_to_csv(Af, Ealf, Ealf_0, Ealf_tot, Eauxf, Eauxf_tot, Edata, Edata_tot, Epro, Epro_tot, Name, Occupancy,
                   Occupants, Qcdata, Qcrefri, Qcs, Qcsf, Qcsf_0, Qhs_sen, Qhsf, Qhsf_0, Qww, Qww_ls_st, Qwwf, Qwwf_0,
                   Tcs_re, Tcs_re_0, Tcs_sup, Tcs_sup_0, Ths_re, Ths_re_0, Ths_sup, Ths_sup_0, Tww_re, Tww_st,
                   Tww_sup_0, Waterconsumption, locationFinal, mcpcs, mcphs, mcpww, path_temporary_folder,
                   sys_e_cooling, sys_e_heating, waterpeak, date)

    gv.report('calc-thermal-loads', locals(), locationFinal, Name)

    # print series all in kW, mcp in kW/h, cooling loads shown as positive, water consumption m3/h,
    # temperature in Degrees celcious
    DATE = pd.date_range('1/1/2010', periods=8760, freq='H')
    pd.DataFrame(
            dict(DATE=DATE, Name=Name, Tm=Tm, Ta=Ta, Qhs_sen=Qhs_sen, Qcs_sen=Qcs_sen, uncomfort=uncomfort, Top=Top,
                 Im_tot=Im_tot, qm_ve_req=qm_ve_req, i_sol=i_sol, i_int_sen=i_int_sen, q_hum=q_hum_hvac,
                 q_dhum=q_dhum_hvac, q_ve_loss=q_ve_loss, qm_ve_mech=qm_ve_mech, qm_ve_nat=qm_ve_nat,
                 q_hs_sen_hvac=q_hs_sen_hvac, q_cs_sen_hvac=q_cs_sen_hvac, e_hum_aux_hvac=e_hum_aux_hvac)).to_csv(
        locationFinal + '\\' + Name + '-new-loads-old-ve-1.csv',
            index=False, float_format='%.2f')

        # gv.report('calc-thermal-loads', locals(), locationFinal, name)
    return


# TESTING
# if __name__ == '__main__':
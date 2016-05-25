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
    temp_ext = dict_locals['temp_ext'][t]
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
    area_f = dict_locals['area_f']
    temp_hs_set_corr = dict_locals['temp_hs_set_corr']
    temp_cs_set_corr = dict_locals['temp_cs_set_corr']
    i_c_max = dict_locals['i_c_max']
    i_h_max = dict_locals['i_h_max']
    temp_sup_heat = dict_locals['temp_sup_heat']
    temp_sup_cool = dict_locals['temp_sup_cool']
    gv = dict_locals['gv']

    # get constant properties of building R-C-model
    h_tr_is = dict_locals['prop_rc_model'].Htr_is
    h_tr_ms = dict_locals['prop_rc_model'].Htr_ms
    h_tr_w = dict_locals['prop_rc_model'].Htr_w
    h_tr_em = dict_locals['prop_rc_model'].Htr_em

    # TODO: adjust calc TL function to new way of losses calculation (adjust input parameters)
    Losses = False

    # first guess of mechanical ventilation mass flow rate and supply temperature for ventilation losses
    qm_ve_mech = qm_ve_req  # required air mass flow rate
    qm_ve_nat = 0  # natural ventilation # TODO: this could be a fixed percentage of the mechanical ventilation (overpressure) as a function of n50
    temp_ve_sup = hvac_kaempf.calc_hex(rh_ext, gv, qv_mech=(qm_ve_req/gv.Pair), qv_mech_dim=0, temp_ext=temp_ext, temp_zone_prev=temp_air_prev)[0]

    qv_ve_req = qm_ve_req / ventilation.calc_rho_air(
        temp_ext)  # TODO: modify Kaempf model to accept mass flow rate instead of volume flow

    rel_diff_qm_ve_mech = 1  # initialisation of difference for while loop
    abs_diff_qm_ve_mech = 1
    rel_tolerance = 0.05  # 5% change  # TODO review tolerance
    abs_tolerance = 0.01  # 10g/s air flow  # TODO  review tolerance

    # iterative loop to determine air mass flows and supply temperatures of the hvac system
    while (abs_diff_qm_ve_mech > abs_tolerance) and (rel_diff_qm_ve_mech > rel_tolerance):

        # Hve
        h_ve = calc_h_ve_adj(qm_ve_mech, qm_ve_nat, temp_ext, temp_ve_sup, temp_air_prev, gv)  # TODO

        # Htr1, Htr2, Htr3
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

        # ventilation losses
        q_ve_loss = h_ve*(temp_a - temp_ext)
        # q_ve_loss = qm_ve_mech * gv.Cpa * (temp_a - temp_ve_sup) * 1000  # (W/s) # TODO make air heat capacity dynamic

        if q_hs_sen > 0:
            q_sen_load_hvac = q_hs_sen  # - q_ve_loss
        elif q_cs_sen < 0:
            q_sen_load_hvac = q_cs_sen  # - q_ve_loss
        else:
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
                                         w_int, gv, temp_sup_heat, temp_sup_cool)

        # mass flow rate output for cooling or heating is zero if the hvac is used only for ventilation
        qm_ve_hvac = max(qm_ve_hvac_h, qm_ve_hvac_c, qm_ve_req)  # ventilation mass flow rate of hvac system

        # calculate thermal loads with hvac mass flow rate in next iteration
        qm_ve_nat = 0  # natural ventilation
        temp_ve_sup = np.nanmax([temp_rec_h, temp_rec_c])

        # compare mass flow rates
        abs_diff_qm_ve_mech = abs(qm_ve_hvac - qm_ve_mech)
        rel_diff_qm_ve_mech = abs_diff_qm_ve_mech / qm_ve_mech
        qm_ve_mech = qm_ve_hvac

    return temp_m, temp_a, q_hs_sen, q_cs_sen, uncomfort, temp_op, i_m_tot, q_hs_sen_hvac, q_cs_sen_hvac,\
           q_hum_hvac, q_dhum_hvac, e_hum_aux_hvac, q_ve_loss, qm_ve_mech


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
    temp_ext = dict_locals['temp_ext'][t]
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
    area_f = dict_locals['area_f']
    temp_hs_set_corr = dict_locals['temp_hs_set_corr']
    temp_cs_set_corr = dict_locals['temp_cs_set_corr']
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

    return temp_m, temp_a, q_hs_sen, q_cs_sen, uncomfort, temp_op, i_m_tot, qm_ve_mech


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
    temp_ext = dict_locals['temp_ext'][t]
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
    area_f = dict_locals['area_f']
    temp_hs_set_corr = dict_locals['temp_hs_set_corr']
    temp_cs_set_corr = dict_locals['temp_cs_set_corr']
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

    Losses = False  # TODO: adjust calc TL function to new way of losses calculation (adjust input parameters)

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


    return temp_m, temp_a, q_hs_sen, q_cs_sen, uncomfort, temp_op, i_m_tot, qm_ve_nat_tot


def calc_thermal_loads_new_ventilation(name, prop_rc_model, prop_hvac, prop_occupancy, prop_age, prop_architecture,
                                       prop_geometry, schedules, Solar, dict_climate,
                                       dict_windows_building, locationFinal, gv, list_uses, prop_internal_loads, prop_comfort, date):
    """ calculates thermal loads of single buildings with mechanical or natural ventilation"""

    # get climate vectors
    # TODO: maybe move to inside of functions
    temp_ext = dict_climate['temp_ext']  # external temperature (°C)
    rh_ext = dict_climate['rh_ext']  # external relative humidity (%)
    u_wind = dict_climate['u_wind']  # wind speed (m/s)

    # copied from original calc thermal loads
    area_f = prop_rc_model.Af
    area_e_f = prop_rc_model.Aef
    sys_e_heating = prop_hvac.type_hs
    sys_e_cooling = prop_hvac.type_cs

    # copied from original calc thermal loads
    mixed_schedule = functions.calc_mixed_schedule(list_uses, schedules, prop_occupancy)  # TODO: rename outputs

    # get internal loads
    Eal_nove, Edataf, Eprof, Eref, Qcrefri, Qcdata, vww, vw = functions.get_internal_loads(mixed_schedule, prop_internal_loads,
                                                                                 prop_architecture, area_f)

    if area_f > 0:  # building has conditioned area

        # get heating and cooling season
        limit_inf_season = gv.seasonhours[0] + 1  # TODO: maybe rename or remove
        limit_sup_season = gv.seasonhours[1]  # TODO maybe rename or remove

        # get occupancy
        people = functions.get_occupancy(mixed_schedule, prop_architecture, area_f)

        # get internal comfort properties
        ve_schedule, ta_hs_set, ta_cs_set = functions.get_internal_comfort(people, prop_comfort, limit_inf_season, limit_sup_season,
                                                        date.hour)

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
        qm_ve_req = np.vectorize(functions.calc_qv_req)(ve_schedule, people, area_f, gv, date.hour, range(8760),
                                                        limit_inf_season, limit_sup_season) * gv.Pair  # TODO: use dynamic rho_air

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
        i_c_max, i_h_max = functions.calc_capacity_heating_cooling_system(area_f, prop_hvac)

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
        temp_hs_set_corr, temp_cs_set_corr = functions.calc_Qem_ls(sys_e_heating, sys_e_cooling)

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
                    Ta[t],\
                    Qhs_sen[t],\
                    Qcs_sen[t],\
                    uncomfort[t],\
                    Top[t],\
                    Im_tot[t], \
                    q_hs_sen_hvac[t],\
                    q_cs_sen_hvac[t],\
                    q_hum_hvac[t],\
                    q_dhum_hvac[t],\
                    e_hum_aux_hvac[t],\
                    q_ve_loss[t],\
                    qm_ve_mech[t] = calc_thermal_load_hvac_timestep(t, locals())

                # case 1b: mechanical ventilation
                else:
                    print('1b')
                    Tm[t],\
                    Ta[t],\
                    Qhs_sen[t],\
                    Qcs_sen[t],\
                    uncomfort[t],\
                    Top[t],\
                    Im_tot[t],\
                    qm_ve_mech[t] = calc_thermal_load_mechanical_ventilation_timestep(t, locals())

                temp_air_prev = Ta[t]
                temp_m_prev = Tm[t]

        # case 2: natural ventilation
        else:
            print('natural ventilation')

            for t in range(8760):
                print(t)

                Tm[t],\
                Ta[t],\
                Qhs_sen[t],\
                Qcs_sen[t],\
                uncomfort[t],\
                Top[t],\
                Im_tot[t],\
                qm_ve_nat[t] = calc_thermal_load_natural_ventilation_timestep(t, locals())

                temp_air_prev = Ta[t]
                temp_m_prev = Tm[t]

        # print series all in kW, mcp in kW/h, cooling loads shown as positive, water consumption m3/h,
        # temperature in Degrees celcious
        DATE = pd.date_range('1/1/2010', periods=8760, freq='H')
        pd.DataFrame(
            dict(DATE=DATE, Name=name, Tm=Tm, Ta=Ta, Qhs_sen=Qhs_sen, Qcs_sen=Qcs_sen, uncomfort=uncomfort, Top=Top,
                 Im_tot=Im_tot, qm_ve_req=qm_ve_req, i_sol=i_sol, i_int_sen=i_int_sen, q_hum=q_hum_hvac,
                 q_dhum=q_dhum_hvac, q_ve_loss=q_ve_loss, qm_ve_mech=qm_ve_mech, qm_ve_nat=qm_ve_nat,
                 q_hs_sen_hvac=q_hs_sen_hvac, q_cs_sen_hvac=q_cs_sen_hvac, e_hum_aux_hvac=e_hum_aux_hvac)).to_csv(
            locationFinal + '\\' + name + '-new-loads-old-ve-1.csv',
            index=False, float_format='%.2f')

        # gv.report('calc-thermal-loads', locals(), locationFinal, name)


# TESTING
# if __name__ == '__main__':
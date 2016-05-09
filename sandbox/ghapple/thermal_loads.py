from __future__ import division
import cea.globalvar
import numpy
import cea.functions as functions
import hvac_kaempf
import ventilation


def calc_h_ve(q_m_mech, q_m_nat, gv):
    """ Hve / Hea
    -- q_m_mech: air mass flow from mechanical ventilation (kg/s)
    -- q_m_nat: air mass flow from windows and leakages and other natural ventilation (kg/s)
    returns Hve in W/K"""

    c_p_air = gv.Cpa  # (kJ/(kg*K))

    return (q_m_mech + q_m_nat) * c_p_air * 1000  # (W/K)


def calc_temp_air_flow(q_m_mech, q_m_arg, q_m_lea, temp_ext, temp_sup_mech, h_ve, gv):
    c_p_air = gv.Cpa

    return ((q_m_mech * temp_sup_mech + (q_m_lea + q_m_arg) * temp_ext) * c_p_air * 1000) / h_ve


def calc_qm_ve_req(ve_schedule, area_f, temp_ext):
    """ calculates required mass flow rate of ventilation from schedules,
    modified version of 'functions.calc_qv_req()' """

    qm_ve_req = ve_schedule * area_f / 3600 * ventilation.calc_rho_air(temp_ext)

    return qm_ve_req


def calc_thermal_load_hvac_timestep(qm_ve_req, temp_air_prev, system_heating, system_cooling,
                                    temp_m_prev, temp_ext, temp_hs_set, temp_cs_set, i_st, i_ia, i_m, cm,
                                    area_f, temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max, flag_season,
                                    rh_ext, w_int, temp_sup_heat, temp_sup_cool, prop_rc_model, gv):
    """this function is executed for the case of heating or cooling with a HVAC system
    by coupling the R-C model of ISO 13790 with the HVAC model of Kaempf
    """

    # get constant properties of building R-C-model
    h_tr_is = prop_rc_model.Htr_is
    h_tr_ms = prop_rc_model.Htr_ms
    h_tr_w = prop_rc_model.Htr_w
    h_tr_em = prop_rc_model.Htr_em

    # TODO: adjust calc TL function to new way of losses calculation (adjust input parameters)
    Losses = False

    # first guess of mechanical ventilation mass flow rate and supply temperature for ventilation losses
    qm_ve_mech = qm_ve_req  # required air mass flow rate
    qm_ve_nat = 0  # natural ventilation
    h_ve = calc_h_ve(qm_ve_mech, qm_ve_nat, gv)  # TODO
    temp_ve_sup = numpy.mean([temp_air_prev, temp_ext])

    h_tr_1, h_tr_2, h_tr_3 = functions.calc_Htr(h_ve, h_tr_is, h_tr_ms, h_tr_w)

    temp_m, temp_a, q_hs_sen, q_cs_sen, uncomfort, temp_op, i_m_tot \
        = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set, temp_cs_set, h_tr_em,
                            h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve, h_tr_w, i_ia, i_m, cm, area_f, Losses,
                            temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max, flag_season)

    q_ve_loss = qm_ve_mech * gv.Cpa * (temp_a - temp_ve_sup)
    if q_hs_sen > 0:
        q_sen_load_HVAC = q_hs_sen - q_ve_loss
    elif q_cs_sen < 0:
        q_sen_load_HVAC = q_cs_sen - q_ve_loss
    else:
        q_sen_load_HVAC = 0

    qv_ve_req = qm_ve_req / ventilation.calc_rho_air(
        temp_ext)  # TODO: modify Kaempf model to accept mass flow rate instead of volume flow

    diff_qm_ve_mech = 1  # initialisation of difference for while loop
    tolerance = 0.01  # 1% change

    # iterative loop to determine air mass flows and supply temperatures of the hvac system
    while rel_diff_qm_ve_mech > tolerance:

        t_air_set = temp_a

        q_hs_sen, q_cs_sen, q_hum, q_dhum, e_hum_aux, qm_ve_hvac_h, qm_ve_hvac_c, temp_sup_h, temp_sup_c, temp_rec_h, temp_rec_c, w_rec, w_sup, temp_air = hvac_kaempf.calc_HVAC(
            rh_ext, temp_ext, t_air_set, qv_ve_req, q_sen_load_HVAC, temp_air_prev, w_int, gv, temp_sup_heat,
            temp_sup_cool)

        qm_ve_hvac = max(qm_ve_hvac_h, qm_ve_hvac_c)  # ventilation mass flow rate of hvac system

        rel_diff_qm_ve_mech = abs(qm_ve_hvac - qm_ve_mech) / qm_ve_mech

        # calculate thermal loads
        qm_ve_mech = qm_ve_hvac
        qm_ve_nat = 0  # natural ventilation
        h_ve = calc_h_ve(qm_ve_mech, qm_ve_nat, gv)  # TODO
        temp_ve_sup = max(temp_rec_h, temp_rec_c)

        h_tr_1, h_tr_2, h_tr_3 = functions.calc_Htr(h_ve, h_tr_is, h_tr_ms, h_tr_w)

        temp_m, temp_a, q_hs_sen, q_cs_sen, uncomfort, temp_op, i_m_tot \
            = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set, temp_cs_set,
                                h_tr_em, h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve, h_tr_w, i_ia, i_m, cm,
                                area_f,
                                Losses, temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max, flag_season)

        q_ve_loss = qm_ve_mech * gv.Cpa * (temp_a - temp_ve_sup)
        if q_hs_sen > 0:
            q_sen_load_HVAC = q_hs_sen - q_ve_loss
        elif q_cs_sen < 0:
            q_sen_load_HVAC = q_cs_sen - q_ve_loss
        else:
            q_sen_load_HVAC = 0

    return temp_m, temp_a, q_hs_sen, q_cs_sen, uncomfort, temp_op, i_m_tot


def calc_thermal_load_mechanical_ventilation_timestep(qm_ve_req, system_heating, system_cooling,
                                                      temp_m_prev, temp_ext, temp_hs_set, temp_cs_set, i_st, i_ia, i_m,
                                                      cm,
                                                      area_f, temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max,
                                                      flag_season, prop_rc_model, gv):
    """ this function is executed for the case of mechanical ventilation with outdoor air
    assumptions:
    - no infiltration due to overpressure inside the ventilation zone
    - windows are not operable """

    # get constant properties of building R-C-model
    h_tr_is = prop_rc_model.Htr_is
    h_tr_ms = prop_rc_model.Htr_ms
    h_tr_w = prop_rc_model.Htr_w
    h_tr_em = prop_rc_model.Htr_em

    # mass flow rate of mechanical ventilation
    qm_ve_mech = qm_ve_req  # required air mass flow rate
    qm_ve_nat = 0  # natural ventilation
    h_ve = calc_h_ve(qm_ve_mech, qm_ve_nat, gv)  # TODO
    temp_ve_sup = temp_ext

    h_tr_1, h_tr_2, h_tr_3 = functions.calc_Htr(h_ve, h_tr_is, h_tr_ms, h_tr_w)

    Losses = False  # TODO: adjust calc TL function to new way of losses calculation (adjust input parameters)

    temp_m, temp_a, q_hs_sen, q_cs_sen, uncomfort, temp_op, i_m_tot \
        = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set, temp_cs_set, h_tr_em,
                            h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve, h_tr_w, i_ia, i_m, cm, area_f, Losses,
                            temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max, flag_season)

    return temp_m, temp_a, q_hs_sen, q_cs_sen, uncomfort, temp_op, i_m_tot


def calc_thermal_load_natural_ventilation(qm_ve_req, system_heating, system_cooling,
                                          temp_m_prev, temp_ext, temp_hs_set, temp_cs_set, i_st, i_ia, i_m, cm, area_f,
                                          temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max, flag_season,
                                          temp_comf_max, geometry_building, windows_building, prop_rc_model):
    """ this function is executed in the case of naturally ventilated buildings """

    # get constant properties of building R-C-model
    h_tr_is = prop_rc_model.Htr_is
    h_tr_ms = prop_rc_model.Htr_ms
    h_tr_w = prop_rc_model.Htr_w
    h_tr_em = prop_rc_model.Htr_em

    Losses = False  # TODO: adjust calc TL function to new way of losses calculation (adjust input parameters)

    # qm_ve_req = qv_req * ventilation.calc_rho_air(temp_ext)  # TODO
    qm_ve_mech = 0  # mechanical ventilation mass flow rate

    # test if ventilation from infiltration is already enough to satisfy the requirements
    status_windows = 0
    qm_ve_sum_in, qm_ve_sum_out = ventilation.calc_air_flows(geometry_building, windows_building,
                                                             status_windows)
    qm_ve_nat = qm_ve_sum_in * 3600  # natural ventilation mass flow rate (kg/h)

    # if building has windows
    if not windows_building.empty:
        status_windows = numpy.array([0.1, 0.5, 0.9])

        # test if air flows satisfy requirements
        # test ventilation with closed windows
        index_window_opening = 0
        while qm_ve_nat < qm_ve_req and index_window_opening < status_windows.size:
            # increase window opening
            print('increase window opening')
            qm_ve_sum_in, qm_ve_sum_out = ventilation.calc_air_flows(geometry_building, windows_building,
                                                                     status_windows[index_window_opening])
            qm_ve_nat = qm_ve_sum_in * 3600  # natural ventilation mass flow rate (kg/h)

            index_window_opening = index_window_opening + 1

    # calculate h_ve
    h_ve = calc_h_ve(qm_ve_mech, qm_ve_nat, gv)  # (kJ/(hK))
    h_tr_1, h_tr_2, h_tr_3 = functions.calc_Htr(h_ve, h_tr_is, h_tr_ms, h_tr_w)
    # calc_TL()
    temp_m, temp_a, q_hs_sen, q_cs_sen, uncomfort, temp_op, i_m_tot \
        = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set, temp_cs_set, h_tr_em,
                            h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve, h_tr_w, i_ia, i_m, cm, area_f, Losses,
                            temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max, flag_season)

    # test for overheating
    while temp_a > temp_comf_max and index_window_opening < status_windows.size:
        # increase window opening to prevent overheating
        m_ve_sum_in, m_ve_sum_out = ventilation.calc_air_flows(geometry_building, windows_building,
                                                               status_windows[index_window_opening])
        m_ve_nat = m_ve_sum_in * 3600  # natural ventilation mass flow rate (kg/h)

        index_window_opening = index_window_opening + 1

        # calculate h_ve
        h_ve = calc_h_ve(qm_ve_mech, qm_ve_nat, gv)  # (kJ/(hK))
        h_tr_1, h_tr_2, h_tr_3 = functions.calc_Htr(h_ve, h_tr_is, h_tr_ms, h_tr_w)
        # calc_TL()
        temp_m, temp_a, q_hs_sen, q_cs_sen, uncomfort, temp_op, i_m_tot \
            = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set, temp_cs_set,
                                h_tr_em, h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve, h_tr_w, i_ia, i_m, cm,
                                area_f,
                                Losses, temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max, flag_season)

    return temp_m, temp_a, q_hs_sen, q_cs_sen, uncomfort, temp_op, i_m_tot


def calc_thermal_loads_new_ventilation(prop_rc_model, prop_hvac, prop_occupancy, prop_age, prop_architecture,
                                       prop_geometry, profiles, names_profiles, Solar, temp_ext, rh_ext,
                                       geometry_building, windows_building):
    """ calculates thermal loads of single buildings with mechanical or natural ventilation"""

    # copied from original calc thermal loads
    area_f = prop_rc_model.Af
    area_e_f = prop_rc_model.Aef
    system_heating = prop_hvac.type_hs
    system_cooling = prop_hvac.type_cs

    # copied from original calc thermal loads
    ta_hs_set, ta_cs_set, people, ve_schedule, q_int, e_al_nove, e_prof, e_data, qc_data_f, qc_refri_f, vww, vw, x_int, hour_day = functions.calc_mixed_schedule(
        profiles, names_profiles, prop_occupancy)  # TODO: rename outputs

    if area_f > 0:  # building has conditioned area

        # extract properties of building
        # copied from original calc thermal loads
        # geometry
        Am, Atot, Aw, Awall_all, Cm, Ll, Lw, Retrofit, Sh_typ, Year, footprint, nf_ag, nfp = functions.get_properties_building_envelope(
            prop_rc_model, prop_age, prop_architecture, prop_geometry, prop_occupancy)  # TODO: rename outputs

        # building systems
        Lcww_dis, Lsww_dis, Lv, Lvww_c, Lvww_dis, Tcs_re_0, Tcs_sup_0, Ths_re_0, Ths_sup_0, Tww_re_0, Tww_sup_0, Y, fforma = functions.get_properties_building_systems(
            Ll, Lw, Retrofit, Year, footprint, gv, nf_ag, nfp, prop_hvac)  # TODO: rename outputs

        # get heating and cooling season
        limit_inf_season = gv.seasonhours[0] + 1  # TODO: maybe rename or remove
        limit_sup_season = gv.seasonhours[1]  # TODO maybe rename or remove

        # data and refrigeration loads
        qc_data = qc_data_f * area_f
        qc_refri = qc_refri_f * area_f

        # minimum mass flow rate of ventilation according to schedule
        qm_ve_req = numpy.vectorize(calc_qm_ve_req)(ve_schedule, area_f, temp_ext)

        # transmission coefficients independent of ventilation
        # TODO: add or not (call directly from prop_rc_model

        # heat flows in [W]
        # solar gains
        # copied from original calc thermal loads
        i_sol = functions.calc_heat_gains_solar(Aw, Awall_all, Sh_typ, Solar, gv)

        # sensible internal heat gains
        # copied from original calc thermal loads
        i_int_sen = functions.calc_heat_gains_internal_sensible(area_f, q_int)

        # components of internal heat gains for R-C-model
        # copied from original calc thermal loads
        i_ia, i_m, i_st = functions.calc_comp_heat_gains_sensible(Am, Atot, prop_rc_model.Htr_w, i_int_sen, i_sol)

        # internal moisture gains
        # copied from original calc thermal loads
        w_int = functions.calc_heat_gains_internal_latent(area_f, x_int, system_cooling, system_heating)

        # heating and cooling loads
        # copied from original calc thermal loads
        i_c_max, i_h_max = functions.calc_capacity_heating_cooling_system(area_f, prop_hvac)

        # define empty arrrays
        uncomfort = numpy.zeros(8760)
        Ta = numpy.zeros(8760)
        Tm = numpy.zeros(8760)
        Qhs_sen = numpy.zeros(8760)
        Qcs_sen = numpy.zeros(8760)
        Qhs_lat = numpy.zeros(8760)
        Qcs_lat = numpy.zeros(8760)
        Qhs_em_ls = numpy.zeros(8760)
        Qcs_em_ls = numpy.zeros(8760)
        QHC_sen = numpy.zeros(8760)
        ma_sup_hs = numpy.zeros(8760)
        Ta_sup_hs = numpy.zeros(8760)
        Ta_re_hs = numpy.zeros(8760)
        ma_sup_cs = numpy.zeros(8760)
        Ta_sup_cs = numpy.zeros(8760)
        Ta_re_cs = numpy.zeros(8760)
        w_sup = numpy.zeros(8760)
        w_re = numpy.zeros(8760)
        Ehs_lat_aux = numpy.zeros(8760)
        Qhs_sen_incl_em_ls = numpy.zeros(8760)
        Qcs_sen_incl_em_ls = numpy.zeros(8760)
        t5 = numpy.zeros(8760)
        Tww_re = numpy.zeros(8760)
        Top = numpy.zeros(8760)
        Im_tot = numpy.zeros(8760)

        # model of losses in the emission and control system for space heating and cooling
        temp_hs_set_corr, temp_cs_set_corr = functions.calc_Qem_ls(system_heating, system_cooling)

        # we give a seed high enough to avoid doing a iteration for 2 years.
        temp_m_prev = 16
        # end-use demand calculation
        temp_air_prev = 21  # definition of first temperature to start calculation of air conditioning system
        flag_season = True # TODO: real value according to season
        temp_sup_heat = 35 # TODO: get from properties
        temp_sup_cool = 16 # TODO: get from properties
        temp_comf_max = 26 # TODO: get from properties

        # case 1: mechanical ventilation
        if system_heating == 'T3' or system_cooling == 'T3':

            for t in range(8760):

                # case 1a: heating or cooling with hvac
                if (system_heating == 'T3' and (t <= gv.seasonhours[0] or t >= gv.seasonhours[1])) \
                        or (system_cooling == 'T3' and gv.seasonhours[0] < t < gv.seasonhours):

                    Tm[t], Ta[t], Qhs_sen[t], Qcs_sen[t], uncomfort[t], Top[t], Im_tot[t] \
                        = calc_thermal_load_hvac_timestep(qm_ve_req, temp_air_prev,
                                                          system_heating, system_cooling, temp_m_prev, temp_ext[t],
                                                          ta_hs_set[t], ta_cs_set[t], i_st, i_ia, i_m, Cm,
                                                          area_f, temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max,
                                                          flag_season, rh_ext[t], w_int,
                                                          temp_sup_heat, temp_sup_cool, prop_rc_model, gv)

                # case 1b: mechanical ventilation
                else:
                    Tm[t], Ta[t], Qhs_sen[t], Qcs_sen[t], uncomfort[t], Top[t], Im_tot[t] \
                        = calc_thermal_load_mechanical_ventilation_timestep(qm_ve_req,
                                                                            system_heating, system_cooling, temp_m_prev,
                                                                            temp_ext[t], ta_hs_set[t], ta_cs_set[t],
                                                                            i_st, i_ia, i_m, Cm, area_f,
                                                                            temp_hs_set_corr, temp_cs_set_corr, i_c_max,
                                                                            i_h_max, flag_season, prop_rc_model, gv)

                temp_air_prev = Ta[t]
                temp_m_prev = Tm[t]

        # case 2: natural ventilation
        else:

            for t in range(8760):
                Tm[t], Ta[t], Qhs_sen[t], Qcs_sen[t], uncomfort[t], Top[t], Im_tot[t] \
                    = calc_thermal_load_natural_ventilation(qm_ve_req, system_heating,
                                                            system_cooling, temp_m_prev, temp_ext[t], ta_hs_set[t],
                                                            ta_cs_set[t], i_st, i_ia, i_m, Cm, area_f, temp_hs_set_corr,
                                                            temp_cs_set_corr, i_c_max, i_h_max, flag_season,
                                                            temp_comf_max, geometry_building, windows_building,
                                                            prop_rc_model)
                temp_m_prev = Tm[t]


# TESTING
if __name__ == '__main__':
    gv = cea.globalvar.GlobalVariables()

    q_m_mech = 10
    q_m_arg = 0
    q_m_lea = 0

    #temp_ext = 5
    temp_sup_mech = 15

    h_ve = calc_h_ve(q_m_mech, q_m_arg, q_m_lea, gv)

    print(h_ve)

    temp_air = calc_temp_air_flow(q_m_mech, q_m_arg, q_m_lea, temp_ext, temp_sup_mech, h_ve, gv)

    print(temp_air)

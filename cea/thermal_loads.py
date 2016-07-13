# -*- coding: utf-8 -*-
"""
Thermal loads



"""
# TODO: documentation


from __future__ import division

import numpy as np
import pandas as pd
import contributions.thermal_loads_new_ventilation.ventilation
import hvac_kaempf
import functions


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

    tHC_corr = [0, 0]
    delta_ctrl = [0, 0]

    # emission system room temperature control type
    if sys_e_ctrl == 'T1':
        delta_ctrl = [2.5, -2.5]
    elif sys_e_ctrl == 'T2':
        delta_ctrl = [1.2, -1.2]
    elif sys_e_ctrl == 'T3':
        delta_ctrl = [0.9, -0.9]
    elif sys_e_ctrl == 'T4':
        delta_ctrl = [1.8, -1.8]

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
    elif SystemC == 'T2':  # no emission losses but emissions for ventilation
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
    temp_ext : exterior air temperature (°C)
    temp_sup : ventilation system supply air temperature (°C), e.g. after HEX
    temp_zone_set : zone air temperature set point (°C)
    gv : globalvars

    Returns
    -------
    Hve,adj in (W/K)

    """

    c_p_air = gv.Cpa  # (kJ/(kg*K)) # TODO: maybe dynamic heat capacity of air f(temp)

    if abs(temp_sup - temp_ext) == 0:
        b_mech = 1

    else:
        eta_hru = (temp_sup - temp_ext) / (temp_zone_set - temp_ext)  # Eq. (28) in ISO 13970
        frac_hru = 1
        b_mech = (1 - frac_hru * eta_hru)  # Eq. (27) in ISO 13970

    return (b_mech * q_m_mech + q_m_nat) * c_p_air * 1000  # (W/K), Eq. (21) in ISO 13970


def calc_qv_req(ve, people, Af, gv, hour_day, hour_year, n50):
    """
    Modified version of calc_qv_req from functions.
    Fixed infiltration according to schedule is only considered for mechanically ventilated buildings.

    Parameters
    ----------
    ve : required ventilation rate according to schedule (?)
    people : occupancy schedules (pax?)
    Af : conditioned floor area (m2)
    gv : globalvars
    hour_day : hour of the day [0..23]
    hour_year : hour of the year [0..8760]
    n50 : building envelope leakiness from archetypes

    Returns
    -------
    q_req : required ventilation rate schedule (m3/s)
    """
    # TODO: check units

    # 'flat rate' infiltration considered for all buildings
    # estimation of infiltration air volume flow rate according to Eq. (3) in DIN 1946-6
    n_inf = 0.5 * n50 * (gv.delta_p_dim/50) ** (2/3)  # [air changes per hour]

    infiltration = gv.hf * n_inf  # m3/h.m2

    # FIXME: THIS DOES NOT MAKE SENSE! CHECK! FREE COOLING ONLY WHEN PEOPLE ABSENT (No effect on q_req) AND HEATING SEASON!
    if people > 0:
        q_req = (ve + (infiltration * Af)) / 3600  # m3/s
    else:
        if (21 < hour_day or hour_day < 7) and gv.is_heating_season(hour_year):
            q_req = (ve * 1.3 + (infiltration * Af)) / 3600  # free cooling
        else:
            q_req = (ve + (infiltration * Af)) / 3600  #

    return q_req  # m3/s


# FIXME: replace weather_data with tsd['T_ext'] and tsd['rh_ext']
def calc_thermal_load_hvac_timestep(t, tsd, bpr, gv):
    """
    This function is executed for the case of heating or cooling with a HVAC system
    by coupling the R-C model of ISO 13790 with the HVAC model of Kaempf

    For this case natural ventilation is not considered

    Author: Gabriel Happle
    Date: May 2016

    Parameters
    ----------
    t : time step, hour of year [0..8760]
    thermal_loads_input : object of type ThermalLoadsInput
    weather_data : data from epw weather file
    state_prev : dict containing air and mass temperatures of previous calculation time step
    gv : globalvars

    Returns
    -------
    temp_m, temp_a, q_hs_sen_loss_true, q_cs_sen_loss_true, uncomfort, temp_op, i_m_tot, q_hs_sen_hvac, q_cs_sen_hvac,
    q_hum_hvac, q_dhum_hvac, e_hum_aux_hvac, q_ve_loss, qm_ve_mech, q_hs_sen, q_cs_sen, qhs_em_ls, qcs_em_ls
    """

    # get arguments from inputs
    temp_ext = tsd['T_ext'][t]
    rh_ext = tsd['rh_ext'][t]

    # TODO: replace by getter methods
    qm_ve_req = tsd['qm_ve_req'][t]
    temp_hs_set = tsd['ta_hs_set'][t]
    temp_cs_set = tsd['ta_cs_set'][t]
    i_st = tsd['I_st'][t]
    i_ia = tsd['I_ia'][t]
    i_m = tsd['I_m'][t]
    flag_season = tsd['flag_season'][t]
    w_int = tsd['w_int'][t]

    system_heating = bpr.hvac.type_hs
    system_cooling = bpr.hvac.type_cs
    cm = bpr.rc_model.Cm
    area_f = bpr.rc_model.Af

    # model of losses in the emission and control system for space heating and cooling
    temp_hs_set_corr, temp_cs_set_corr = calc_tHC_corr(bpr.hvac.type_hs, bpr.hvac.type_cs, bpr.hvac.type_ctrl)

    # heating and cooling loads
    i_c_max, i_h_max = functions.calc_capacity_heating_cooling_system(bpr.rc_model.Af, bpr.hvac)

    # previous timestep data (we give a seed high enough to avoid doing a iteration for 2 years, Ta=21, Tm=16)
    temp_air_prev = tsd['Ta'][t-1] if t > 0 else gv.initial_temp_air_prev
    temp_m_prev = tsd['Tm'][t-1] if t > 0 else gv.initial_temp_m_prev

    # get constant properties of building R-C-model
    h_tr_is = bpr.rc_model.Htr_is
    h_tr_ms = bpr.rc_model.Htr_ms
    h_tr_w = bpr.rc_model.Htr_w
    h_tr_em = bpr.rc_model.Htr_em

    # initialize output
    q_hs_sen = None
    q_cs_sen = None
    q_hs_sen_loss_true = None
    q_cs_sen_loss_true = None
    temp_m = None
    temp_a = None
    uncomfort = None
    temp_op = None
    i_m_tot = None
    q_hs_sen_hvac = None
    q_cs_sen_hvac = None
    q_hum_hvac = None
    q_dhum_hvac = None
    e_hum_aux_hvac = None
    qm_ve_hvac_h = None
    qm_ve_hvac_c = None
    temp_sup_h = None
    temp_sup_c = None
    temp_rec_h = None
    temp_rec_c = None
    w_rec = None
    w_sup = None

    # ==================================================================================================================
    # ITERATION
    # ==================================================================================================================

    # first guess of mechanical ventilation mass flow rate and supply temperature for ventilation losses
    qm_ve_mech = qm_ve_req  # required air mass flow rate
    qm_ve_nat = 0  # natural ventilation # TODO: this could be a fixed percentage of the mechanical ventilation (overpressure) as a function of n50

    temp_ve_sup = hvac_kaempf.calc_hex(rh_ext, gv, qv_mech=(qm_ve_req / gv.Pair), qv_mech_dim=0, temp_ext=temp_ext,
                                       temp_zone_prev=temp_air_prev, timestep=t)[0]

    # conversion to volume flow rate
    qv_ve_req = qm_ve_req / gv.Pair  # TODO: modify Kaempf model to accept mass flow rate instead of volume flow

    # TODO: review iteration parameters
    rel_diff_qm_ve_mech = 1  # initialisation of difference for while loop
    abs_diff_qm_ve_mech = 1
    rel_tolerance = 0.05  # 5% change  # TODO review tolerance
    abs_tolerance = 0.01  # 10g/s air flow  # TODO  review tolerance
    hvac_status_prev = 0  # system is turned OFF
    switch = 0  # number of 'ON'/'OFF' switches of HVAC system during iteration to prevent an infinite loop

    # iterative loop to determine air mass flows and supply temperatures of the hvac system
    while (abs_diff_qm_ve_mech > abs_tolerance) and (rel_diff_qm_ve_mech > rel_tolerance) and switch < 10:

        # Hve
        h_ve_adj = calc_h_ve_adj(qm_ve_mech, qm_ve_nat, temp_ext, temp_ve_sup, temp_air_prev, gv)  # TODO

        # Htr1, Htr2, Htr3
        h_tr_1, h_tr_2, h_tr_3 = functions.calc_Htr(h_ve_adj, h_tr_is, h_tr_ms, h_tr_w)

        # TODO: adjust calc TL function to new way of losses calculation (adjust input parameters)
        Losses = True  # including emission and control losses for the iteration of air mass flow rate

        # calc_TL()
        temp_m_loss_true, \
        temp_a_loss_true, \
        q_hs_sen_loss_true, \
        q_cs_sen_loss_true, \
        uncomfort_loss_true, \
        temp_op_loss_true, \
        i_m_tot_loss_true = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set,
                                              temp_cs_set, h_tr_em, h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st,
                                              h_ve_adj, h_tr_w, i_ia, i_m, cm, area_f, Losses, temp_hs_set_corr,
                                              temp_cs_set_corr, i_c_max, i_h_max, flag_season)

        # calculate sensible heat load
        Losses = False  # Losses are set to false for the calculation of the sensible heat load and actual temperatures

        temp_m, \
        temp_a, \
        q_hs_sen, \
        q_cs_sen, \
        uncomfort, \
        temp_op, \
        i_m_tot = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set, temp_cs_set,
                                    h_tr_em, h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve_adj, h_tr_w, i_ia,
                                    i_m, cm, area_f, Losses, temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max,
                                    flag_season)
        # TODO: in the original calculation procedure this is calculated with another temp_m_prev (with and without losses), check if this is correct or not

        # ventilation losses
        q_ve_loss = h_ve_adj * (temp_a - temp_ext)  # not used in calculation

        # HVAC supplies load if zone has load
        if q_hs_sen > 0:
            hvac_status = 1  # system is ON
            # print('HVAC ON')
            q_sen_load_hvac = q_hs_sen_loss_true  #
        elif q_cs_sen < 0:
            hvac_status = 1  # system is ON
            # print('HVAC ON')
            q_sen_load_hvac = q_cs_sen_loss_true  #
        else:
            hvac_status = 0  # system is OFF
            # print('HVAC OFF')
            q_sen_load_hvac = 0

        # temperature set point
        t_air_set = temp_a

        # calc_HVAC()
        q_hs_sen_hvac, \
        q_cs_sen_hvac, \
        q_hum_hvac, \
        q_dhum_hvac, \
        e_hum_aux_hvac, \
        qm_ve_hvac_h, \
        qm_ve_hvac_c, \
        temp_sup_h, \
        temp_sup_c, \
        temp_rec_h, \
        temp_rec_c, \
        w_rec, \
        w_sup, \
        temp_air = hvac_kaempf.calc_hvac(rh_ext, temp_ext, t_air_set, qv_ve_req, q_sen_load_hvac, temp_air_prev,
                                         w_int, gv, t)

        # mass flow rate output for cooling or heating is zero if the hvac is used only for ventilation
        qm_ve_hvac = max(qm_ve_hvac_h, qm_ve_hvac_c, qm_ve_req)  # ventilation mass flow rate of hvac system

        # calculate thermal loads with hvac mass flow rate in next iteration
        qm_ve_nat = 0  # natural ventilation
        temp_ve_sup = np.nanmax([temp_rec_h, temp_rec_c])

        # compare mass flow rates
        # evaluate while statement of loop
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

    tsd['Tm'][t] = temp_m
    tsd['Ta'][t] = temp_a
    tsd['Qhs_sen_incl_em_ls'][t] = q_hs_sen_loss_true
    tsd['Qcs_sen_incl_em_ls'][t] = q_cs_sen_loss_true
    tsd['uncomfort'][t] = uncomfort
    tsd['Top'][t] = temp_op
    tsd['Im_tot'][t] = i_m_tot
    tsd['q_hs_sen_hvac'][t] = q_hs_sen_hvac
    tsd['q_cs_sen_hvac'][t] = q_cs_sen_hvac
    tsd['Qhs_lat'][t] = q_hum_hvac
    tsd['Qcs_lat'][t] = q_dhum_hvac
    tsd['Ehs_lat_aux'][t] = e_hum_aux_hvac
    tsd['qm_ve_mech'][t] = qm_ve_mech
    tsd['Qhs_sen'][t] = q_hs_sen
    tsd['Qcs_sen'][t] = q_cs_sen
    tsd['Qhs_em_ls'][t] = qhs_em_ls
    tsd['Qcs_em_ls'][t] = qcs_em_ls
    tsd['ma_sup_hs'][t] = qm_ve_hvac_h
    tsd['ma_sup_cs'][t] = qm_ve_hvac_c
    tsd['Ta_sup_hs'][t] = temp_sup_h
    tsd['Ta_sup_cs'][t] = temp_sup_c
    tsd['Ta_re_hs'][t] = temp_rec_h
    tsd['Ta_re_cs'][t] = temp_rec_c
    tsd['w_re'][t] = w_rec
    tsd['w_sup'][t] = w_sup

    return tsd


def calc_thermal_load_mechanical_and_natural_ventilation_timestep(t, tsd, bpr, gv):
    """
    This function is executed for the case of mechanical ventilation with outdoor air

    Assumptions:
    - Mechanical ventilation is controlled in a way that required ventilation rates are always met (CO2-sensor based
        or similar control)
    - No natural ventilation

    Parameters
    ----------
    t : time step, hour of year [0..8760]
    thermal_loads_input : object of type ThermalLoadsInput
    weather_data : data from epw weather file
    state_prev : dict containing air and mass temperatures of previous calculation time step
    gv : globalvars

    Returns
    -------
    temp_m, temp_a, q_hs_sen, q_cs_sen, uncomfort, temp_op, i_m_tot, qm_ve_mech
    """

    # get arguments from input
    temp_ext = tsd['T_ext'][t]

    qm_ve_req = tsd['qm_ve_req'][t]
    temp_hs_set = tsd['ta_hs_set'][t]
    temp_cs_set = tsd['ta_cs_set'][t]
    i_st = tsd['I_st'][t]
    i_ia = tsd['I_ia'][t]
    i_m = tsd['I_m'][t]
    flag_season = tsd['flag_season'][t]

    system_heating = bpr.hvac.type_hs
    system_cooling = bpr.hvac.type_cs
    cm = bpr.rc_model.Cm
    area_f = bpr.rc_model.Af

    # model of losses in the emission and control system for space heating and cooling
    temp_hs_set_corr, temp_cs_set_corr = calc_tHC_corr(bpr.hvac.type_hs, bpr.hvac.type_cs, bpr.hvac.type_ctrl)

    i_c_max, i_h_max = functions.calc_capacity_heating_cooling_system(bpr.rc_model.Af, bpr.hvac)

    # previous timestep data (we give a seed high enough to avoid doing a iteration for 2 years, Ta=21, Tm=16)
    temp_air_prev = tsd['Ta'][t - 1] if t > 0 else gv.initial_temp_air_prev
    temp_m_prev = tsd['Tm'][t - 1] if t > 0 else gv.initial_temp_m_prev

    # get constant properties of building R-C-model
    h_tr_is = bpr.rc_model.Htr_is
    h_tr_ms = bpr.rc_model.Htr_ms
    h_tr_w = bpr.rc_model.Htr_w
    h_tr_em = bpr.rc_model.Htr_em

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
    temp_m, \
    temp_a, \
    q_hs_sen, \
    q_cs_sen, \
    uncomfort, \
    temp_op, \
    i_m_tot = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set, temp_cs_set,
                                h_tr_em, h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve, h_tr_w, i_ia, i_m, cm,
                                area_f, Losses, temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max, flag_season)

    # calculate emission losses
    Losses = True
    temp_m_loss_true, \
    temp_a_loss_true, \
    q_hs_sen_loss_true, \
    q_cs_sen_loss_true, \
    uncomfort_loss_true, \
    temp_op_loss_true, \
    i_m_tot_loss_true = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set,
                                          temp_cs_set, h_tr_em, h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve,
                                          h_tr_w, i_ia, i_m, cm, area_f, Losses, temp_hs_set_corr, temp_cs_set_corr,
                                          i_c_max, i_h_max, flag_season)
    # TODO: in the original calculation procedure this is calculated with another temp_m_prev (with and without losses), check if this is correct or not

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

    tsd['Tm'][t] = temp_m
    tsd['Ta'][t] = temp_a
    tsd['Qhs_sen_incl_em_ls'][t] = q_hs_sen_loss_true
    tsd['Qcs_sen_incl_em_ls'][t] = q_cs_sen_loss_true
    tsd['uncomfort'][t] = uncomfort
    tsd['Top'][t] = temp_op
    tsd['Im_tot'][t] = i_m_tot
    tsd['qm_ve_mech'][t] = qm_ve_mech
    tsd['Qhs_sen'][t] = q_hs_sen
    tsd['Qcs_sen'][t] = q_cs_sen
    tsd['Qhs_em_ls'][t] = qhs_em_ls
    tsd['Qcs_em_ls'][t] = qcs_em_ls

    return tsd


def calc_thermal_loads_new_ventilation(building_name, bpr, weather_data, usage_schedules, date, gv,
                                       results_folder, temporary_folder):
    """
    Calculate thermal loads of a single building with mechanical or natural ventilation.
    Calculation procedure follows the methodology of ISO 13790


    PARAMETERS
    ----------

    :param building_name: name of building
    :type building_name: str

    :param bpr: a collection of building properties for the building used for thermal loads calculation
    :type bpr: BuildingPropertiesRow

    :param weather_data: data from the .epw weather file. Each row represents an hour of the year. The columns are:
        drybulb_C, relhum_percent, and windspd_ms
    :type weather_data: DataFrame

    :param usage_schedules: dict containing schedules and function names of buildings. The structure is:
        {
            'list_uses': ['ADMIN', 'GYM', ...],
            'schedules': [ ([...], [...], [...], [...]), (), (), () ]
        }
        each element of the 'list_uses' entry represents a building occupancy type.
        each element of the 'schedules' entry represents the schedules for a building occupancy type.
        the schedules for a building occupancy type are a 4-tuple (occupancy, electricity, domestic hot water,
        probability of use), with each element of the 4-tuple being a list of hourly values (8760 values).
    :type usage_schedules: dict

    :param date: the dates (hours) of the year (8760)
        <class 'pandas.tseries.index.DatetimeIndex'>
        [2016-01-01 00:00:00, ..., 2016-12-30 23:00:00]
        Length: 8760, Freq: H, Timezone: None
    :type date: DatetimeIndex

    :param gv: global variables / context
    :type gv: GlobalVariables

    :param results_folder: path to results folder (sample value: 'C:\reference-case\baseline\outputs\data\demand')
        obtained from inputlocator.InputLocator..get_demand_results_folder() in demand.demand_calculation
        used for writing the ${Name}.csv file and also the report file (${Name}-{yyyy-mm-dd-hh-MM-ss}.xls)
    :type results_folder: str

    :param temporary_folder: path to a temporary folder for intermediate results
        (sample value: c:\users\darthoma\appdata\local\temp')
        obtained from inputlocator.InputLocator..get_temporary_folder() in demand.demand_calculation
        used for writing the ${Name}.csv file
    :type temporary_folder: str


    RETURNS
    -------

    :returns: This function does not return anything
    :rtype: NoneType


    SIDE EFFECTS
    ------------

    A number of files in two folders:
    - results_folder
      - ${Name}.csv for each building
      - Total_demand.csv
    - temporary_folder
      - ${Name}T.csv for each building

    daren-thomas: as far as I can tell, these are the only side-effects.
    """

    # get weather

    tsd = pd.DataFrame({
        'T_ext': weather_data.drybulb_C.values,
        'rh_ext': weather_data.relhum_percent.values
    })

    # get schedules
    list_uses = usage_schedules['list_uses']
    schedules = usage_schedules['schedules']

    # get n50 value
    n50 = bpr.architecture['n50']

    # copied from original calc thermal loads
    tsd = functions.calc_mixed_schedule(tsd, list_uses, schedules, bpr.occupancy)  # TODO: rename outputs

    # get internal loads
    tsd = functions.get_internal_loads(tsd, bpr.internal_loads, bpr.architecture, bpr.rc_model.Af)

    tsd['uncomfort'] = np.zeros(8760)
    tsd['Ta'] = np.zeros(8760)
    tsd['Tm'] = np.zeros(8760)
    tsd['Qhs_sen'] = np.zeros(8760)
    tsd['Qcs_sen'] = np.zeros(8760)
    tsd['Qhs_lat'] = np.zeros(8760)
    tsd['Qhs_sen_incl_em_ls'] = np.zeros(8760)
    tsd['Qcs_sen_incl_em_ls'] = np.zeros(8760)
    tsd['Qcs_lat'] = np.zeros(8760)
    tsd['Top'] = np.zeros(8760)
    tsd['Im_tot'] = np.zeros(8760)
    tsd['q_hs_sen_hvac'] = np.zeros(8760)
    tsd['q_cs_sen_hvac'] = np.zeros(8760)
    tsd['Ehs_lat_aux'] = np.zeros(8760)
    tsd['qm_ve_mech'] = np.zeros(8760)
    tsd['Qhs_em_ls'] = np.zeros(8760)
    tsd['Qcs_em_ls'] = np.zeros(8760)
    tsd['ma_sup_hs'] = np.zeros(8760)
    tsd['ma_sup_cs'] = np.zeros(8760)
    tsd['Ta_sup_hs'] = np.zeros(8760)
    tsd['Ta_sup_cs'] = np.zeros(8760)
    tsd['Ta_re_hs'] = np.zeros(8760)
    tsd['Ta_re_cs'] = np.zeros(8760)
    tsd['w_re'] = np.zeros(8760)
    tsd['w_sup'] = np.zeros(8760)
    if bpr.rc_model.Af > 0:  # building has conditioned area

        # get heating and cooling season
        limit_inf_season = gv.seasonhours[0] + 1  # TODO: maybe rename or remove
        limit_sup_season = gv.seasonhours[1]  # TODO maybe rename or remove

        # get occupancy
        tsd = functions.get_occupancy(tsd, bpr.architecture, bpr.rc_model.Af)

        # get internal comfort properties
        tsd = functions.get_internal_comfort(tsd, bpr.comfort, limit_inf_season, limit_sup_season,
                                             date.dayofweek)

        # minimum mass flow rate of ventilation according to schedule
        # with infiltration and overheating
        tsd['qv_req'] = np.vectorize(calc_qv_req)(tsd['ve'].values, tsd['people'].values, bpr.rc_model.Af, gv,
                                                  date.hour, range(8760), n50)
        tsd['qm_ve_req'] = tsd['qv_req'] * gv.Pair  # TODO:  use dynamic rho_air

        # heat flows in [W]
        # solar gains
        # copied from original calc thermal loads
        tsd['I_sol'] = calc_heat_gains_solar(bpr, gv)

        # sensible internal heat gains
        # copied from original calc thermal loads
        tsd['I_int_sen'] = functions.calc_heat_gains_internal_sensible(tsd['people'].values, bpr.internal_loads.Qs_Wp,
                                                                       tsd['Ealf'].values, tsd['Eprof'].values,
                                                                       tsd['Qcdata'].values, tsd['Qcrefri'].values)

        # components of internal heat gains for R-C-model
        # copied from original calc thermal loads
        tsd = functions.calc_comp_heat_gains_sensible(tsd, bpr.rc_model.Am, bpr.rc_model.Atot, bpr.rc_model.Htr_w)

        # internal moisture gains
        # copied from original calc thermal loads
        tsd['w_int'] = functions.calc_heat_gains_internal_latent(tsd['people'].values, bpr.internal_loads.X_ghp,
                                                                 bpr.hvac.type_cs,
                                                                 bpr.hvac.type_hs)

        # natural ventilation building propertiess
        # new
        dict_props_nat_vent = contributions.thermal_loads_new_ventilation.ventilation.get_properties_natural_ventilation(
            bpr.geometry,
            bpr.architecture, gv)

        # # # factor for cross ventilation
        # factor_cros = architecture.f_cros  # TODO: get from building properties

        # create flag season
        tsd['flag_season'] = np.zeros(8760, dtype=bool)  # default is heating season
        tsd.loc[limit_inf_season:limit_sup_season, 'flag_season'] = True

        # ground water temperature in C during heating season (winter) according to norm
        tsd['Tww_re'] = bpr.building_systems['Tww_re_0']
        # ground water temperature in C during non-heating season (summer) according to norm
        tsd.loc[limit_inf_season:limit_sup_season-1, 'Tww_re'] = 14

        # end-use demand calculation
        for t in range(8760):

            # case 1a: heating or cooling with hvac
            if (bpr.hvac.type_hs == 'T3' and gv.is_heating_season(t)) \
                    or (bpr.hvac.type_cs == 'T3' and not gv.is_heating_season(t)):
                tsd = calc_thermal_load_hvac_timestep(t, tsd, bpr, gv)

                # case 1b: mechanical ventilation
            else:
                # print('1b')
                tsd = calc_thermal_load_mechanical_and_natural_ventilation_timestep(t, tsd, bpr, gv)

        # TODO: check this out with Shanshan :)

        # Calc of Qhs_dis_ls/Qcs_dis_ls - losses due to distribution of heating/cooling coils
        # erase possible disruptions from dehumidification days
        # Qhs_sen_incl_em_ls[Qhs_sen_incl_em_ls < 0] = 0
        # Qcs_sen_incl_em_ls[Qcs_sen_incl_em_ls > 0] = 0
        Qhs_sen_incl_em_ls_0 = tsd['Qhs_sen_incl_em_ls'].max()
        Qcs_sen_incl_em_ls_0 = tsd['Qcs_sen_incl_em_ls'].min()  # cooling loads up to here in negative values
        Qhs_d_ls, Qcs_d_ls = np.vectorize(functions.calc_Qdis_ls)(tsd['Ta'], tsd['T_ext'].values,
                                                                  tsd['Qhs_sen_incl_em_ls'].values,
                                                                  tsd['Qcs_sen_incl_em_ls'].values,
                                                                  bpr.building_systems['Ths_sup_0'],
                                                                  bpr.building_systems['Ths_re_0'],
                                                                  bpr.building_systems['Tcs_sup_0'],
                                                                  bpr.building_systems['Tcs_re_0'],
                                                                  Qhs_sen_incl_em_ls_0,
                                                                  Qcs_sen_incl_em_ls_0,
                                                                  gv.D, bpr.building_systems['Y'][0], bpr.hvac.type_hs,
                                                                  bpr.hvac.type_cs, gv.Bf,
                                                                  bpr.building_systems['Lv'])

        # Calc requirements of generation systems (both cooling and heating do not have a storage):
        Qhs = tsd['Qhs_sen_incl_em_ls'] - tsd['Qhs_em_ls']
        Qhsf = tsd[
                   'Qhs_sen_incl_em_ls'] + Qhs_d_ls  # no latent is considered because it is already added as electricity from the adiabatic system.
        Qcs = (tsd['Qcs_sen_incl_em_ls'] - tsd['Qcs_em_ls']) + tsd['Qcs_lat']
        Qcsf = Qcs + tsd['Qcs_em_ls'] + Qcs_d_ls
        Qcsf = -abs(Qcsf)
        Qcs = -abs(Qcs)

        # Calc nomincal temperatures of systems
        Qhsf_0 = Qhsf.max()  # in W
        Qcsf_0 = Qcsf.min()  # in W negative

        # Cal temperatures of all systems
        Tcs_re, Tcs_sup, Ths_re, Ths_sup, mcpcs, mcphs = functions.calc_temperatures_emission_systems(Qcsf, Qcsf_0,
                                                                                                      Qhsf, Qhsf_0,
                                                                                                      tsd['Ta'],
                                                                                                      tsd['Ta_re_cs'],
                                                                                                      tsd['Ta_re_hs'],
                                                                                                      tsd['Ta_sup_cs'],
                                                                                                      tsd['Ta_sup_hs'],
                                                                                                      bpr.building_systems['Tcs_re_0'],
                                                                                                      bpr.building_systems['Tcs_sup_0'],
                                                                                                      bpr.building_systems['Ths_re_0'],
                                                                                                      bpr.building_systems['Ths_sup_0'],
                                                                                                      gv,
                                                                                                      tsd['ma_sup_cs'],
                                                                                                      tsd['ma_sup_hs'],
                                                                                                      bpr.hvac.type_cs,
                                                                                                      bpr.hvac.type_hs,
                                                                                                      tsd['ta_hs_set'].values,
                                                                                                      tsd['w_re'],
                                                                                                      tsd['w_sup'])
        Mww, Qww, Qww_ls_st, Qwwf, Qwwf_0, Tww_st, Vw, Vww, mcpww = functions.calc_dhw_heating_demand(bpr.rc_model.Af,
                                                                                                      bpr.building_systems['Lcww_dis'],
                                                                                                      bpr.building_systems['Lsww_dis'],
                                                                                                      bpr.building_systems['Lvww_c'],
                                                                                                      bpr.building_systems['Lvww_dis'],
                                                                                                      tsd['T_ext'],
                                                                                                      tsd['Ta'],
                                                                                                      tsd['Tww_re'],
                                                                                                      bpr.building_systems['Tww_sup_0'],
                                                                                                      bpr.building_systems['Y'],
                                                                                                      gv,
                                                                                                      tsd['vw'],
                                                                                                      tsd['vww'])

        # clac auxiliary loads of pumping systems
        Eaux_cs, Eaux_fw, Eaux_hs, Eaux_ve, Eaux_ww = functions.calc_pumping_systems_aux_loads(bpr.rc_model.Af,
                                                                                               bpr.geometry.Blength,
                                                                                               bpr.geometry.Bwidth,
                                                                                               Mww, Qcsf, Qcsf_0,
                                                                                               Qhsf, Qhsf_0, Qww, Qwwf,
                                                                                               Qwwf_0,
                                                                                               Tcs_re, Tcs_sup, Ths_re,
                                                                                               Ths_sup,
                                                                                               Vw, bpr.age.built,
                                                                                               bpr.building_systems['fforma'],
                                                                                               gv,
                                                                                               bpr.geometry.floors_ag,
                                                                                               bpr.occupancy.PFloor,
                                                                                               tsd['qv_req'].values,
                                                                                               bpr.hvac.type_cs,
                                                                                               bpr.hvac.type_hs)

        # Calc total auxiliary loads
        Eauxf = (Eaux_ww + Eaux_fw + Eaux_hs + Eaux_cs + tsd['Ehs_lat_aux'] + Eaux_ve)

        # calculate other quantities
        # noinspection PyUnresolvedReferences
        Occupancy = np.floor(tsd['people'])
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
        Qwwf = Qww = Qhs_sen = Qhsf = Qcs_sen = Qcs = Qcsf = Qcdata = Qcrefri = Qd = Qc = Qhs = Qww_ls_st = np.zeros(
            8760)

        # FIXME: this is a bug (all the variables are being set to the same array)
        Ths_sup = Ths_re = Tcs_re = Tcs_sup = mcphs = mcpcs = mcpww = Vww = Tww_re = Tww_st = np.zeros(
            8760)  # in C

    # Cacl totals and peaks electrical loads
    Ealf, Ealf_0, Ealf_tot, Eauxf_tot, Edataf, Edataf_tot, Eprof, Eprof_tot = functions.calc_loads_electrical(
        bpr.rc_model.Aef, tsd['Ealf'].values, Eauxf,
        tsd[
            'Edataf'].values,
        tsd[
            'Eprof'].values)

    # write results to csv
    functions.results_to_csv(bpr.rc_model.GFA_m2, bpr.rc_model.Af, Ealf, Ealf_0, Ealf_tot, Eauxf, Eauxf_tot, Edataf,
                             Edataf_tot,
                             Eprof, Eprof_tot,
                             building_name,
                             Occupancy,
                             Occupants, tsd['Qcdata'].values, tsd['Qcrefri'].values, Qcs, Qcsf, Qcsf_0, Qhs, Qhsf,
                             Qhsf_0, Qww, Qww_ls_st, Qwwf, Qwwf_0,
                             Tcs_re, bpr.building_systems['Tcs_re_0'], Tcs_sup,
                             bpr.building_systems['Tcs_sup_0'], Ths_re, bpr.building_systems['Ths_re_0'], Ths_sup,
                             bpr.building_systems['Ths_sup_0'], tsd['Tww_re'], Tww_st,
                             bpr.building_systems['Tww_sup_0'], Waterconsumption, results_folder, mcpcs, mcphs, mcpww,
                             temporary_folder,
                             bpr.hvac.type_cs, bpr.hvac.type_hs, waterpeak, date)

    gv.report('calc-thermal-loads', locals(), results_folder, building_name)
    return


def test_thermal_loads_new_ventilation():
    """
    script to test modified thermal loads calculation with new natural ventilation and improved mechanical ventilation
     simulation

    Returns
    -------

    """
    import globalvar
    import inputlocator
    import demand

    # create globalvars
    gv = globalvar.GlobalVariables()

    locator = inputlocator.InputLocator(scenario_path=r'C:\reference-case\baseline')
    # for the interface, the user should pick a file out of of those in ...DB/Weather/...
    weather_path = locator.get_default_weather()

    # plug in new thermal loads calculation
    gv.models['calc-thermal-loads'] = calc_thermal_loads_new_ventilation

    # run demand
    demand.demand_calculation(locator=locator, weather_path=weather_path, gv=gv)
    gv.log("test_thermal_loads_new_ventilation() succeeded")


if __name__ == '__main__':
    test_thermal_loads_new_ventilation()


def calc_heat_gains_solar(bpr, gv):
    # TODO: Documentation
    # Refactored from CalcThermalLoads
    solar_specific = bpr.solar / bpr.rc_model['Awall_all']  # array in W/m2
    gl = np.vectorize(calc_gl)(solar_specific, gv.g_gl, Calc_Rf_sh(bpr.architecture['type_shade']))
    solar_effective_area = gl * (1 - gv.F_f) * bpr.rc_model['Aw']  # Calculation of solar effective area per hour in m2
    net_solar_gains = solar_effective_area * solar_specific  # how much are the net solar gains in Wh per hour of the year.
    return net_solar_gains.values


def calc_gl(radiation, g_gl, Rf_sh):
    if radiation > 300:  # in w/m2
        return g_gl * Rf_sh
    else:
        return g_gl


def Calc_Rf_sh (ShadingType):
    # this script assumes shading is always located outside! most of the cases
    # 0 for not, 1 for Rollo, 2 for Venetian blinds, 3 for Solar control glass
    d = {'Type': ['T0', 'T1', 'T2', 'T3'], 'ValueOUT': [1, 0.08, 0.15, 0.1]}
    ValuesRf_Table = pd.DataFrame(d)
    rows = ValuesRf_Table.Type.count()
    for row in range(rows):
        if ShadingType == ValuesRf_Table.loc[row, 'Type']:
            return ValuesRf_Table.loc[row, 'ValueOUT']
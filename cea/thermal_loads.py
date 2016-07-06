# -*- coding: utf-8 -*-
"""
Thermal loads



"""
# TODO: documentation


from __future__ import division

import numpy as np
import pandas as pd

import cea.functions as functions
import contributions.thermal_loads_new_ventilation.ventilation
import hvac_kaempf


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
def calc_thermal_load_hvac_timestep(t, thermal_loads_input, weather_data, state_prev, gv):
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
    temp_ext = np.array(weather_data.drybulb_C)[t]
    rh_ext = np.array(weather_data.relhum_percent)[t]

    # TODO: replace by getter methods
    qm_ve_req = thermal_loads_input._qm_ve_req[t]
    temp_hs_set = thermal_loads_input._temp_hs_set[t]
    temp_cs_set = thermal_loads_input._temp_cs_set[t]
    i_st = thermal_loads_input._i_st[t]
    i_ia = thermal_loads_input._i_ia[t]
    i_m = thermal_loads_input._i_m[t]
    flag_season = thermal_loads_input._flag_season[t]
    w_int = thermal_loads_input._w_int[t]

    system_heating = thermal_loads_input._sys_e_heating
    system_cooling = thermal_loads_input._sys_e_cooling
    cm = thermal_loads_input._cm
    area_f = thermal_loads_input._area_f
    temp_hs_set_corr = thermal_loads_input._temp_hs_set_corr
    temp_cs_set_corr = thermal_loads_input._temp_cs_set_corr
    i_c_max = thermal_loads_input._i_c_max
    i_h_max = thermal_loads_input._i_h_max

    temp_air_prev = state_prev['temp_air_prev']
    temp_m_prev = state_prev['temp_m_prev']

    # get constant properties of building R-C-model
    h_tr_is = thermal_loads_input._prop_rc_model.Htr_is
    h_tr_ms = thermal_loads_input._prop_rc_model.Htr_ms
    h_tr_w = thermal_loads_input._prop_rc_model.Htr_w
    h_tr_em = thermal_loads_input._prop_rc_model.Htr_em

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
    q_ve_loss = None
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

    return temp_m, temp_a, q_hs_sen_loss_true, q_cs_sen_loss_true, uncomfort, \
           temp_op, i_m_tot, q_hs_sen_hvac, q_cs_sen_hvac, q_hum_hvac, q_dhum_hvac, e_hum_aux_hvac, \
           qm_ve_mech, q_hs_sen, q_cs_sen, qhs_em_ls, qcs_em_ls, qm_ve_hvac_h, qm_ve_hvac_c, temp_sup_h,\
           temp_sup_c, temp_rec_h, temp_rec_c, w_rec, w_sup


def calc_thermal_load_mechanical_and_natural_ventilation_timestep(t, thermal_loads_input, weather_data, state_prev, gv):
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
    temp_ext = np.array(weather_data.drybulb_C)[t]

    qm_ve_req = thermal_loads_input._qm_ve_req[t]
    temp_hs_set = thermal_loads_input._temp_hs_set[t]
    temp_cs_set = thermal_loads_input._temp_cs_set[t]
    i_st = thermal_loads_input._i_st[t]
    i_ia = thermal_loads_input._i_ia[t]
    i_m = thermal_loads_input._i_m[t]
    flag_season = thermal_loads_input._flag_season[t]

    system_heating = thermal_loads_input._sys_e_heating
    system_cooling = thermal_loads_input._sys_e_cooling
    cm = thermal_loads_input._cm
    area_f = thermal_loads_input._area_f
    temp_hs_set_corr = thermal_loads_input._temp_hs_set_corr
    temp_cs_set_corr = thermal_loads_input._temp_cs_set_corr
    i_c_max = thermal_loads_input._i_c_max
    i_h_max = thermal_loads_input._i_h_max

    temp_air_prev = state_prev['temp_air_prev']
    temp_m_prev = state_prev['temp_m_prev']

    # get constant properties of building R-C-model
    h_tr_is = thermal_loads_input._prop_rc_model.Htr_is
    h_tr_ms = thermal_loads_input._prop_rc_model.Htr_ms
    h_tr_w = thermal_loads_input._prop_rc_model.Htr_w
    h_tr_em = thermal_loads_input._prop_rc_model.Htr_em

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

    return temp_m, temp_a, q_hs_sen_loss_true, q_cs_sen_loss_true, uncomfort, \
           temp_op, i_m_tot, qm_ve_mech, q_hs_sen, q_cs_sen, qhs_em_ls, qcs_em_ls


def calc_thermal_loads_new_ventilation(Name, bpr, weather_data, usage_schedules, date, gv,
                                       results_folder, temporary_folder):
    """
    Calculate thermal loads of a single building with mechanical or natural ventilation.
    Calculation procedure follows the methodology of ISO 13790


    PARAMETERS
    ----------

    :param Name: name of building
    :type Name: str

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

    # copied from original calc thermal loads
    GFA_m2 = bpr.rc_model.GFA_m2  # gross floor area
    Af = bpr.rc_model.Af
    Aef = bpr.rc_model.Aef
    sys_e_heating = bpr.hvac.type_hs
    sys_e_cooling = bpr.hvac.type_cs
    sys_e_ctrl = bpr.hvac.type_ctrl  # room temperature control types

    # get n50 value
    n50 = bpr.architecture['n50']

    # copied from original calc thermal loads
    tsd = functions.calc_mixed_schedule(tsd, list_uses, schedules, bpr.occupancy)  # TODO: rename outputs

    # get internal loads
    tsd = functions.get_internal_loads(tsd, bpr.internal_loads, bpr.architecture, Af)

    if Af > 0:  # building has conditioned area

        # get heating and cooling season
        limit_inf_season = gv.seasonhours[0] + 1  # TODO: maybe rename or remove
        limit_sup_season = gv.seasonhours[1]  # TODO maybe rename or remove

        # get occupancy
        tsd = functions.get_occupancy(tsd, bpr.architecture, Af)

        # get internal comfort properties
        tsd = functions.get_internal_comfort(tsd, bpr.comfort, limit_inf_season, limit_sup_season,
                                                   date.dayofweek)

        # extract properties of building
        # copied from original calc thermal loads
        # geometry
        Am, \
        Atot, \
        Aw, \
        Awall_all, \
        cm, \
        Ll, \
        Lw, \
        Retrofit, \
        Sh_typ, \
        Year, \
        footprint, \
        nf_ag, \
        nf_bg, \
        nfp = functions.get_properties_building_envelope(bpr.rc_model, bpr.age, bpr.architecture, bpr.geometry,
                                                         bpr.occupancy)  # TODO: rename outputs

        # building systems
        Lcww_dis, \
        Lsww_dis, \
        Lv, \
        Lvww_c, \
        Lvww_dis, \
        Tcs_re_0, \
        Tcs_sup_0, \
        Ths_re_0, \
        Ths_sup_0, \
        Tww_re_0, \
        Tww_sup_0, \
        Y, \
        fforma = functions.get_properties_building_systems(Ll, Lw, Retrofit, Year, footprint, gv, nf_ag, nfp, nf_bg,
                                                           bpr.hvac)  # TODO: rename outputs

        # minimum mass flow rate of ventilation according to schedule
        # qm_ve_req = numpy.vectorize(calc_qm_ve_req)(ve_schedule, area_f, temp_ext)
        # with infiltration and overheating
        tsd['qv_req'] = np.vectorize(calc_qv_req)(tsd['ve'].values, tsd['people'].values, Af, gv, date.hour, range(8760), n50)
        tsd['qm_ve_req'] = tsd['qv_req'] * gv.Pair  # TODO:  use dynamic rho_air

        # heat flows in [W]
        # solar gains
        # copied from original calc thermal loads
        tsd['I_sol'] = functions.calc_heat_gains_solar(Aw, Awall_all, Sh_typ, bpr.solar, gv).values

        # sensible internal heat gains
        # copied from original calc thermal loads
        tsd['I_int_sen'] = functions.calc_heat_gains_internal_sensible(tsd['people'].values, bpr.internal_loads.Qs_Wp,
                                                                       tsd['Ealf'].values, tsd['Eprof'].values,
                                                                       tsd['Qcdata'].values, tsd['Qcrefri'].values)

        # components of internal heat gains for R-C-model
        # copied from original calc thermal loads
        i_ia, i_m, i_st = functions.calc_comp_heat_gains_sensible(Am, Atot, bpr.rc_model.Htr_w, tsd['I_int_sen'].values,
                                                                  tsd['I_sol'].values)

        # internal moisture gains
        # copied from original calc thermal loads
        w_int = functions.calc_heat_gains_internal_latent(tsd['people'].values, bpr.internal_loads.X_ghp, sys_e_cooling,
                                                          sys_e_heating)

        # heating and cooling loads
        # copied from original calc thermal loads
        i_c_max, i_h_max = functions.calc_capacity_heating_cooling_system(Af, bpr.hvac)

        # natural ventilation building propertiess
        # new
        dict_props_nat_vent = contributions.thermal_loads_new_ventilation.ventilation.get_properties_natural_ventilation(
            bpr.geometry,
            bpr.architecture, gv)

        # # # factor for cross ventilation
        # factor_cros = architecture.f_cros  # TODO: get from building properties

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
        # QHC_sen = np.zeros(8760)
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
        Tww_re = np.zeros(8760)
        Top = np.zeros(8760)
        Im_tot = np.zeros(8760)
        qm_ve_mech = np.zeros(8760)

        q_hs_sen_hvac = np.zeros(8760)
        q_cs_sen_hvac = np.zeros(8760)

        # create flag season
        flag_season = np.zeros(8760, dtype=bool)  # default is heating season
        flag_season[gv.seasonhours[0] + 1:gv.seasonhours[1]] = True

        # model of losses in the emission and control system for space heating and cooling
        tHset_corr, tCset_corr = calc_tHC_corr(sys_e_heating, sys_e_cooling, sys_e_ctrl)

        # group function inputs
        thermal_loads_input = ThermalLoadsInput(qm_ve_req=tsd['qm_ve_req'].values, temp_hs_set=tsd['ta_hs_set'].values,
                                                temp_cs_set=tsd['ta_cs_set'].values,
                                                i_st=i_st, i_ia=i_ia, i_m=i_m, w_int=w_int, flag_season=flag_season,
                                                system_heating=sys_e_heating, system_cooling=sys_e_cooling, cm=cm,
                                                area_f=Af, temp_hs_set_corr=tHset_corr, temp_cs_set_corr=tCset_corr,
                                                i_c_max=i_c_max, i_h_max=i_h_max, prop_rc_model=(bpr.rc_model))

        # we give a seed high enough to avoid doing a iteration for 2 years.
        # definition of first temperature to start calculation of air conditioning system
        state_prev = {'temp_m_prev': 16, 'temp_air_prev': 21}

        # end-use demand calculation
        for t in range(8760):
                # print(t)

            # FIXME: Remove the setting of Tww_re[t] from this loop - it doesn't belong here and should probably
            # just be done with a pandas assignment...
            # if it is in the season
            if limit_inf_season <= t < limit_sup_season:
                # take advantage of this loop to fill the values of cold water
                Tww_re[t] = 14  # Ground water temperature in C during non-heating (summer) season according to norm
            else:
                # take advantage of this loop to fill the values of cold water
                Tww_re[t] = Tww_re_0  # Ground water temperature in C during heating (heating) season according to norm

            # case 1a: heating or cooling with hvac
            if (sys_e_heating == 'T3' and gv.is_heating_season(t)) \
                    or (sys_e_cooling == 'T3' and not gv.is_heating_season(t)):
                # print('1a')

                Tm[t], \
                Ta[t], \
                Qhs_sen_incl_em_ls[t], \
                Qcs_sen_incl_em_ls[t], \
                uncomfort[t], \
                Top[t], \
                Im_tot[t], \
                q_hs_sen_hvac[t], \
                q_cs_sen_hvac[t], \
                Qhs_lat[t], \
                Qcs_lat[t], \
                Ehs_lat_aux[t], \
                qm_ve_mech[t], \
                Qhs_sen[t], \
                Qcs_sen[t], \
                Qhs_em_ls[t],\
                Qcs_em_ls[t], \
                ma_sup_hs[t], \
                ma_sup_cs[t], \
                Ta_sup_hs[t], \
                Ta_sup_cs[t], \
                Ta_re_hs[t], \
                Ta_re_cs[t], \
                w_re[t], \
                w_sup[t] = calc_thermal_load_hvac_timestep(t, thermal_loads_input, weather_data, state_prev, gv)

                # case 1b: mechanical ventilation
            else:
                # print('1b')
                Tm[t], \
                Ta[t], \
                Qhs_sen_incl_em_ls[t], \
                Qcs_sen_incl_em_ls[t], \
                uncomfort[t], \
                Top[t], \
                Im_tot[t], \
                qm_ve_mech[t], \
                Qhs_sen[t], \
                Qcs_sen[t], \
                Qhs_em_ls[t], \
                Qcs_em_ls[t] = calc_thermal_load_mechanical_and_natural_ventilation_timestep(t, thermal_loads_input,
                                                                                     weather_data, state_prev, gv)

            state_prev['temp_air_prev'] = Ta[t]
            state_prev['temp_m_prev'] = Tm[t]


        # TODO: check this out with Shanshan :)

        # Calc of Qhs_dis_ls/Qcs_dis_ls - losses due to distribution of heating/cooling coils
        # erase possible disruptions from dehumidification days
        # Qhs_sen_incl_em_ls[Qhs_sen_incl_em_ls < 0] = 0
        # Qcs_sen_incl_em_ls[Qcs_sen_incl_em_ls > 0] = 0
        Qhs_sen_incl_em_ls_0 = Qhs_sen_incl_em_ls.max()
        Qcs_sen_incl_em_ls_0 = Qcs_sen_incl_em_ls.min()  # cooling loads up to here in negative values
        Qhs_d_ls, Qcs_d_ls = np.vectorize(functions.calc_Qdis_ls)(Ta, tsd['T_ext'].values, Qhs_sen_incl_em_ls, Qcs_sen_incl_em_ls, Ths_sup_0,
                                                        Ths_re_0, Tcs_sup_0, Tcs_re_0, Qhs_sen_incl_em_ls_0,
                                                        Qcs_sen_incl_em_ls_0,
                                                        gv.D, Y[0], sys_e_heating, sys_e_cooling, gv.Bf, Lv)

        # Calc requirements of generation systems (both cooling and heating do not have a storage):
        Qhs = Qhs_sen_incl_em_ls - Qhs_em_ls
        Qhsf = Qhs_sen_incl_em_ls + Qhs_d_ls  # no latent is considered because it is already added as electricity from the adiabatic system.
        Qcs = (Qcs_sen_incl_em_ls - Qcs_em_ls) + Qcs_lat
        Qcsf = Qcs + Qcs_em_ls + Qcs_d_ls
        Qcsf = -abs(Qcsf)
        Qcs = -abs(Qcs)

        # Calc nomincal temperatures of systems
        Qhsf_0 = Qhsf.max()  # in W
        Qcsf_0 = Qcsf.min()  # in W negative

        # Cal temperatures of all systems
        Tcs_re, Tcs_sup, Ths_re, Ths_sup, mcpcs, mcphs = functions.calc_temperatures_emission_systems(Qcsf, Qcsf_0, Qhsf, Qhsf_0,
                                                                                            Ta, Ta_re_cs, Ta_re_hs,
                                                                                            Ta_sup_cs, Ta_sup_hs,
                                                                                            Tcs_re_0, Tcs_sup_0,
                                                                                            Ths_re_0, Ths_sup_0, gv,
                                                                                            ma_sup_cs, ma_sup_hs,
                                                                                            sys_e_cooling,
                                                                                            sys_e_heating, tsd['ta_hs_set'].values,
                                                                                            w_re, w_sup)
        Mww, Qww, Qww_ls_st, Qwwf, Qwwf_0, Tww_st, Vw, Vww, mcpww = functions.calc_dhw_heating_demand(Af, Lcww_dis, Lsww_dis,
                                                                                            Lvww_c, Lvww_dis, tsd['T_ext'], Ta,
                                                                                            Tww_re, Tww_sup_0, Y, gv,
                                                                                            tsd['vw'], tsd['vww'])

        # clac auxiliary loads of pumping systems
        Eaux_cs, Eaux_fw, Eaux_hs, Eaux_ve, Eaux_ww = functions.calc_pumping_systems_aux_loads(Af, Ll, Lw, Mww, Qcsf, Qcsf_0,
                                                                                     Qhsf, Qhsf_0, Qww, Qwwf, Qwwf_0,
                                                                                     Tcs_re, Tcs_sup, Ths_re, Ths_sup,
                                                                                     Vw, Year, fforma, gv, nf_ag, nfp,
                                                                                     tsd['qv_req'].values, sys_e_cooling,
                                                                                     sys_e_heating)

        # Calc total auxiliary loads
        Eauxf = (Eaux_ww + Eaux_fw + Eaux_hs + Eaux_cs + Ehs_lat_aux + Eaux_ve)

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
        Ths_sup = Ths_re = Tcs_re = Tcs_sup = mcphs = mcpcs = mcpww = Vww = Tww_re = Tww_st = uncomfort = np.zeros(
            8760)  # in C

    # Cacl totals and peaks electrical loads
    Ealf, Ealf_0, Ealf_tot, Eauxf_tot, Edataf, Edataf_tot, Eprof, Eprof_tot = functions.calc_loads_electrical(Aef, tsd['Ealf'].values, Eauxf,
                                                                                                    tsd['Edataf'].values, tsd['Eprof'].values)

    # write results to csv
    functions.results_to_csv(GFA_m2, Af, Ealf, Ealf_0, Ealf_tot, Eauxf, Eauxf_tot, Edataf, Edataf_tot, Eprof, Eprof_tot,
                             Name,
                             Occupancy,
                             Occupants, tsd['Qcdata'].values, tsd['Qcrefri'].values, Qcs, Qcsf, Qcsf_0, Qhs, Qhsf,
                             Qhsf_0, Qww, Qww_ls_st, Qwwf, Qwwf_0,
                             Tcs_re, Tcs_re_0, Tcs_sup, Tcs_sup_0, Ths_re, Ths_re_0, Ths_sup, Ths_sup_0, Tww_re, Tww_st,
                             Tww_sup_0, Waterconsumption, results_folder, mcpcs, mcphs, mcpww, temporary_folder,
                             sys_e_cooling, sys_e_heating, waterpeak, date)

    gv.report('calc-thermal-loads', locals(), results_folder, Name)
    return


class ThermalLoadsInput(object):
    # TODO: documentation
    """
    Class to group input arguments for different tracks of calc thermal loads functions

    """

    def __init__(self, qm_ve_req=None, temp_hs_set=None, temp_cs_set=None, i_st=None,
                 i_ia=None, i_m=None, w_int=None, flag_season=None, system_heating=None, system_cooling=None,
                 cm=None, area_f=None, temp_hs_set_corr=None, temp_cs_set_corr=None, i_c_max=None, i_h_max=None,
                 prop_rc_model=None):
        self._qm_ve_req = qm_ve_req
        self._temp_hs_set = temp_hs_set
        self._temp_cs_set = temp_cs_set
        self._i_st = i_st
        self._i_ia = i_ia
        self._i_m = i_m
        self._w_int = w_int
        self._flag_season = flag_season

        self._sys_e_heating = system_heating
        self._sys_e_cooling = system_cooling
        self._cm = cm
        self._area_f = area_f
        self._temp_hs_set_corr = temp_hs_set_corr
        self._temp_cs_set_corr = temp_cs_set_corr
        self._i_c_max = i_c_max
        self._i_h_max = i_h_max
        self._prop_rc_model = prop_rc_model

    # TODO: get / set methods


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
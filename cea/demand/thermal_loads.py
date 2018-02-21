# -*- coding: utf-8 -*-
"""
Demand model of thermal loads
"""
from __future__ import division
import numpy as np
import math

from cea.resources import geothermal
from cea.demand import demand_writers
from cea.demand import occupancy_model, hourly_procedure_heating_cooling_system_load, ventilation_air_flows_simple
from cea.demand import ventilation_air_flows_detailed, control_heating_cooling_systems
from cea.demand import sensible_loads, electrical_loads, hotwater_loads, refrigeration_loads, datacenter_loads
from cea.demand import latent_loads


def calc_thermal_loads(building_name, bpr, weather_data, usage_schedules, date, gv, locator,
                       use_dynamic_infiltration_calculation, resolution_outputs, loads_output, massflows_output,
                       temperatures_output, format_output):
    """
    Calculate thermal loads of a single building with mechanical or natural ventilation.
    Calculation procedure follows the methodology of ISO 13790

    The structure of ``usage_schedules`` is:

    .. code-block:: python
        :emphasize-lines: 2,4

        {
            'list_uses': ['ADMIN', 'GYM', ...],
            'schedules': [ ([...], [...], [...], [...]), (), (), () ]
        }

    * each element of the 'list_uses' entry represents a building occupancy type.
    * each element of the 'schedules' entry represents the schedules for a building occupancy type.
    * the schedules for a building occupancy type are a 4-tuple (occupancy, electricity, domestic hot water,
      probability of use), with each element of the 4-tuple being a list of hourly values (8760 values).


    Side effect include a number of files in two folders:

    * ``scenario/outputs/data/demand``

      * ``${Name}.csv`` for each building

    * temporary folder (as returned by ``tempfile.gettempdir()``)

      * ``${Name}T.csv`` for each building

    daren-thomas: as far as I can tell, these are the only side-effects.

    :param building_name: name of building
    :type building_name: str

    :param bpr: a collection of building properties for the building used for thermal loads calculation
    :type bpr: BuildingPropertiesRow

    :param weather_data: data from the .epw weather file. Each row represents an hour of the year. The columns are:
        ``drybulb_C``, ``relhum_percent``, and ``windspd_ms``
    :type weather_data: pandas.DataFrame

    :param usage_schedules: dict containing schedules and function names of buildings.
    :type usage_schedules: dict

    :param date: the dates (hours) of the year (8760)
    :type date: pandas.tseries.index.DatetimeIndex

    :param gv: global variables / context
    :type gv: GlobalVariables

    :param locator:
    :param use_dynamic_infiltration_calculation:

    :returns: This function does not return anything
    :rtype: NoneType

"""
    schedules, tsd = initialize_inputs(bpr, gv, usage_schedules, weather_data)

    if bpr.rc_model['Af'] > 0:  # building has conditioned area

        ventilation_air_flows_simple.calc_m_ve_required(bpr, tsd)
        ventilation_air_flows_simple.calc_m_ve_leakage_simple(bpr, tsd, gv)

        # get internal comfort properties
        tsd = control_heating_cooling_systems.calc_simple_temp_control(tsd, bpr, date.dayofweek)

        # initialize first previous time step
        # this makes the 'if ... else ... ' unnecessary
        t_prev = get_hours(bpr).next() - 1
        tsd['T_int'][t_prev] = tsd['T_ext'][t_prev]
        tsd['x_int'][t_prev] = latent_loads.convert_rh_to_moisture_content(tsd['rh_ext'][t_prev], tsd['T_ext'][t_prev])

        # end-use demand calculation
        for t in get_hours(bpr):

            # heat flows in [W]
            # sensible heat gains
            tsd = sensible_loads.calc_Qgain_sen(t, tsd, bpr, gv)

            if use_dynamic_infiltration_calculation:
                # OVERWRITE STATIC INFILTRATION WITH DYNAMIC INFILTRATION RATE
                dict_props_nat_vent = ventilation_air_flows_detailed.get_properties_natural_ventilation(bpr, gv)
                qm_sum_in, qm_sum_out = ventilation_air_flows_detailed.calc_air_flows(
                    tsd['T_int'][t - 1] if not np.isnan(tsd['T_int'][t - 1]) else tsd['T_ext'][t - 1],
                    tsd['u_wind'][t], tsd['T_ext'][t], dict_props_nat_vent)
                # INFILTRATION IS FORCED NOT TO REACH ZERO IN ORDER TO AVOID THE RC MODEL TO FAIL
                tsd['m_ve_inf'][t] = max(qm_sum_in / 3600, 1 / 3600)

            # ventilation air flows [kg/s]
            ventilation_air_flows_simple.calc_air_mass_flow_mechanical_ventilation(bpr, tsd, t)
            ventilation_air_flows_simple.calc_air_mass_flow_window_ventilation(bpr, tsd, t)

            # ventilation air temperature and humidity
            ventilation_air_flows_simple.calc_theta_ve_mech(bpr, tsd, t, gv)
            latent_loads.calc_moisture_content_airflows(tsd, t)

            # heating / cooling demand of building
            hourly_procedure_heating_cooling_system_load.calc_heating_cooling_loads(bpr, tsd, t)

            # END OF FOR LOOP

        # Calc of Qhs_dis_ls/Qcs_dis_ls - losses due to distribution of heating/cooling coils
        sensible_loads.calc_q_dis_ls_heating_cooling(bpr, tsd)

        # summation
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

        # Calculate temperatures of all systems
        sensible_loads.calc_temperatures_emission_systems(tsd, bpr, gv)

        # calculate hot water load
        tsd['mww'], tsd['mcptw'], tsd['Qww'], Qww_ls_st, tsd['Qwwf'], Qwwf_0, Tww_st, Vww, Vw, tsd[
            'mcpwwf'] = hotwater_loads.calc_Qwwf(
            bpr.building_systems['Lcww_dis'], bpr.building_systems['Lsww_dis'], bpr.building_systems['Lvww_c'],
            bpr.building_systems['Lvww_dis'], tsd['T_ext'], tsd['T_int'], tsd['Twwf_re'],
            bpr.building_systems['Tww_sup_0'], bpr.building_systems['Y'], gv, schedules,
            bpr)

        # calc auxiliary electricity loads
        tsd['Eauxf'], tsd['Eauxf_hs'], tsd['Eauxf_cs'], \
        tsd['Eauxf_ve'], tsd['Eauxf_ww'], tsd['Eauxf_fw'] = electrical_loads.calc_Eauxf(tsd, bpr, Qwwf_0, Vw, gv)

    elif bpr.rc_model['Af'] == 0:  # if building does not have conditioned area

        # TODO: actually this should behave like a building without systems
        tsd = update_timestep_data_no_conditioned_area(tsd)
        tsd['T_int'] = tsd['T_ext'].copy()

    else:
        raise Exception('error')

    # calculate other quantities
    # - processes
    tsd['Qhprof'][:] = schedules['Qhpro'] * bpr.internal_loads['Qhpro_Wm2'] * bpr.rc_model['Af']  # in kWh

    # - change sign to latent and sensible cooling loads
    tsd['Qcsf_lat'] = abs(tsd['Qcsf_lat'])
    tsd['Qcsf'] = abs(tsd['Qcsf'])
    tsd['Qcs'] = abs(tsd['Qcs'])

    # - electricity demand due to heatpumps/cooling units in the building
    # TODO: do it for heatpumps tsd['Egenf_cs']
    electrical_loads.calc_heatpump_cooling_electricity(bpr, tsd, gv)

    # - number of people
    tsd['people'] = np.floor(tsd['people'])

    # Sum up
    tsd['QHf'] = tsd['Qhsf'] + tsd['Qwwf'] + tsd['Qhprof']
    tsd['QCf'] = tsd['Qcsf'] + tsd['Qcdataf'] + tsd['Qcref']
    tsd['Ef'] = tsd['Ealf'] + tsd['Edataf'] + tsd['Eprof'] + tsd['Ecaf'] + tsd['Eauxf'] + tsd['Eref'] + tsd['Egenf_cs']
    tsd['QEf'] = tsd['QHf'] + tsd['QCf'] + tsd['Ef']

    # write results
    if resolution_outputs == 'hourly':
        writer = demand_writers.HourlyDemandWriter(loads_output, massflows_output, temperatures_output)
    elif resolution_outputs == 'monthly':
        writer = demand_writers.MonthlyDemandWriter(loads_output, massflows_output, temperatures_output)
    else:
        raise Exception('error')

    if format_output == 'csv':
        writer.results_to_csv(tsd, bpr, locator, date, building_name)
    elif format_output == 'hdf5':
        writer.results_to_hdf5(tsd, bpr, locator, date, building_name)
    else:
        raise Exception('error')

    # write report
    gv.report(tsd, locator.get_demand_results_folder(), building_name)

    # visualize tsd
    quick_visualization_tsd(tsd)

    return


def quick_visualization_tsd(tsd):

    from plotly.offline import plot
    import plotly.graph_objs as go

    plot_heat_load = False
    plot_heat_temp = False
    plot_cool_load = True
    plot_cool_moisture = True
    plot_cool_air = True

    if plot_heat_load:
        traces = []
        for key in tsd_keys_heating_loads:
            y = tsd[key][50:150]
            trace = go.Scatter(x=np.linspace(1, 100, 100), y=y, name=key, mode='line-markers')
            traces.append(trace)
        fig = go.Figure(data=traces)
        plot(fig, filename='heat-load', auto_open=True)

    if plot_heat_temp:
        traces = []
        keys = []
        keys.extend(tsd_keys_heating_temp)
        keys.extend(tsd_keys_rc_temp)
        for key in keys:
            y = tsd[key][50:150]
            trace = go.Scatter(x=np.linspace(1, 100, 100), y=y, name=key, mode='line-markers')
            traces.append(trace)
        fig = go.Figure(data=traces)
        plot(fig, filename='heat-temp', auto_open=True)

    if plot_cool_load:
        traces = []
        for key in tsd_keys_cooling_loads:
            y = tsd[key][4100:4200]
            trace = go.Scatter(x=np.linspace(1, 100, 100), y=y, name=key, mode='line-markers')
            traces.append(trace)
        fig = go.Figure(data=traces)
        plot(fig, filename='cool-load', auto_open=True)

    if plot_cool_moisture:
        traces = []
        for key in tsd_keys_moisture:
            y = tsd[key][4100:4200]
            trace = go.Scatter(x=np.linspace(1, 100, 100), y=y, name=key, mode='line-markers')
            traces.append(trace)
        fig = go.Figure(data=traces)
        plot(fig, filename='cool-moisture', auto_open=True)

    if plot_cool_air:
        traces = []
        for key in tsd_keys_ventilation:
            y = tsd[key][4100:4200]
            trace = go.Scatter(x=np.linspace(1, 100, 100), y=y, name=key, mode='line-markers')
            traces.append(trace)
        fig = go.Figure(data=traces)
        plot(fig, filename='cool-air', auto_open=True)


def initialize_inputs(bpr, gv, usage_schedules, weather_data):
    """


    :param bpr:
    :param gv:
    :param usage_schedules:
    :param weather_data:
    :return:
    """
    # TODO: documentation


    # this is used in the NN please do not erase or change!!
    tsd = initialize_timestep_data(bpr, weather_data)
    # get schedules
    list_uses = usage_schedules['list_uses']
    archetype_schedules = usage_schedules['archetype_schedules']
    archetype_values = usage_schedules['archetype_values']
    schedules = occupancy_model.calc_schedules(gv.config.region, list_uses, archetype_schedules, bpr.occupancy,
                                               archetype_values)

    # calculate occupancy schedule and occupant-related parameters
    tsd['people'] = schedules['people'] * bpr.rc_model['Af']
    tsd['ve'] = schedules['ve'] * (bpr.comfort['Ve_lps'] * 3.6) * bpr.rc_model['Af']  # in m3/h
    tsd['Qs'] = schedules['Qs'] * bpr.internal_loads['Qs_Wp'] * bpr.rc_model['Af']  # in W
    # # latent heat gains
    tsd['w_int'] = sensible_loads.calc_Qgain_lat(schedules, bpr)
    # get electrical loads (no auxiliary loads)
    tsd = electrical_loads.calc_Eint(tsd, bpr, schedules)
    # get refrigeration loads
    tsd['Qcref'], tsd['mcpref'], \
    tsd['Tcref_re'], tsd['Tcref_sup'] = np.vectorize(refrigeration_loads.calc_Qcref)(tsd['Eref'])
    # get server loads
    tsd['Qcdataf'], tsd['mcpdataf'], \
    tsd['Tcdataf_re'], tsd['Tcdataf_sup'] = np.vectorize(datacenter_loads.calc_Qcdataf)(tsd['Edataf'])
    # ground water temperature in C
    tsd['Twwf_re'] = calc_water_temperature(tsd['T_ext'], depth_m=1)

    return schedules, tsd


def calc_water_temperature(T_ambient_C, depth_m):
    """
    Calculates hourly ground temperature fluctuation over a year following [Kusuda, T. et al., 1965]_.
    ..[Kusuda, T. et al., 1965] Kusuda, T. and P.R. Achenbach (1965). Earth Temperatures and Thermal Diffusivity at
    Selected Stations in the United States. ASHRAE Transactions. 71(1):61-74
    """
    heat_capacity_soil = 2000  # _[A. Kecebas et al., 2011]
    conductivity_soil = 1.6  # _[A. Kecebas et al., 2011]
    density_soil = 1600  # _[A. Kecebas et al., 2011]

    T_max = max(T_ambient_C) + 273.15  # to K
    T_avg = np.mean(T_ambient_C) + 273.15  # to K
    e = depth_m * math.sqrt(
        (math.pi * heat_capacity_soil * density_soil) / (8760 * conductivity_soil))  # soil constants
    Tg = [(T_avg + (T_max - T_avg) * math.exp(-e) * math.cos((2 * math.pi * (i + 1) / 8760) - e)) - 274
          for i in range(8760)]

    return Tg  # in C


tsd_keys_heating_loads = ['Qhs_sen_rc', 'Qhs_sen_shu', 'Qhs_sen_ahu', 'Qhs_lat_ahu', 'Qhs_sen_aru', 'Qhs_lat_aru',
                            'Qhs_sen_sys', 'Qhs_lat_sys', 'Qhs_em_ls', 'Qhs_dis_ls', 'Qhsf', 'Qhs']
tsd_keys_cooling_loads = ['Qcs_sen_rc', 'Qcs_sen_scu', 'Qcs_sen_ahu', 'Qcs_lat_ahu', 'Qcs_sen_aru', 'Qcs_lat_aru',
                            'Qcs_sen_sys', 'Qcs_lat_sys', 'Qcs_em_ls', 'Qcs_dis_ls', 'Qcsf', 'Qcs']
tsd_keys_heating_temp = ['ta_re_hs_ahu', 'ta_sup_hs_ahu', 'ta_re_hs_aru', 'ta_sup_hs_aru']
tsd_keys_heating_flows = ['ma_sup_hs_ahu', 'ma_sup_hs_aru']
tsd_keys_cooling_temp = ['ta_re_cs_ahu', 'ta_sup_cs_ahu', 'ta_re_cs_aru', 'ta_sup_cs_aru']
tsd_keys_cooling_flows = ['ma_sup_cs_ahu', 'ma_sup_cs_aru']
tsd_keys_rc_temp = ['T_int', 'theta_m', 'theta_c', 'theta_o']
tsd_keys_moisture = ['x_int', 'x_ve_inf', 'x_ve_mech', 'g_hu_ld', 'g_dhu_ld']
tsd_keys_ventilation = ['theta_ve_mech', 'm_ve_window', 'm_ve_mech', 'm_ve_rec', 'm_ve_inf', 'm_ve_required']


def initialize_timestep_data(bpr, weather_data):
    """
    initializes the time step data with the weather data and the minimum set of variables needed for computation.
    :param bpr:
    :param weather_data:
    :return: returns the `tsd` variable, a dictionary of time step data mapping variable names to ndarrays for each
    hour of the year.
    """
    # Initialize dict with weather variables
    tsd = {'Twwf_sup': [bpr.building_systems['Tww_sup_0']] * 8760,
           'T_ext': weather_data.drybulb_C.values,
           'T_ext_wetbulb': weather_data.wetbulb_C.values,
           'rh_ext': weather_data.relhum_percent.values,
           'T_sky': weather_data.skytemp_C.values,
           'u_wind': weather_data.windspd_ms}

    # fill data with nan values


    nan_fields_energy_balance_dashboard = ['Qgain_light', 'Qgain_app', 'Qgain_pers', 'Qgain_data', 'Q_cool_ref',
                                           'Qgain_wall', 'Qgain_base',
                                           'Qgain_roof', 'Qgain_wind', 'Qgain_vent']
    nan_fields_solar = ['I_sol', 'I_rad', 'I_sol_and_I_rad']

    nan_fields_electricity = ['Eauxf', 'Eauxf_ve', 'Eauxf_hs', 'Eauxf_cs', 'Eauxf_ww', 'Eauxf_fw', 'Egenf_cs',
                              'Ehs_lat_aux']
    nan_fields_water = ['mcpwwf', 'Twwf_re', 'Qwwf', 'Qww']
    nan_fields_people = ['w_int']

    nan_fields = ['QEf', 'QHf', 'QCf',
                  'Ef','Qhsf_lat', 'Qcsf_lat', 'Qhprof',
                  'mcphsf', 'mcpcsf', 'Thsf_sup', 'Thsf_re', 'Tcsf_sup', 'Tcsf_re', 'Tcdataf_re', 'Tcdataf_sup',
                  'Tcref_re', 'Tcref_sup',
                  'q_cs_lat_peop']
    nan_fields.extend(tsd_keys_heating_loads)
    nan_fields.extend(tsd_keys_cooling_loads)
    nan_fields.extend(tsd_keys_heating_temp)
    nan_fields.extend(tsd_keys_cooling_temp)
    nan_fields.extend(tsd_keys_cooling_flows)
    nan_fields.extend(tsd_keys_heating_flows)
    nan_fields.extend(tsd_keys_rc_temp)
    nan_fields.extend(tsd_keys_moisture)
    nan_fields.extend(nan_fields_energy_balance_dashboard)
    nan_fields.extend(nan_fields_solar)
    nan_fields.extend(tsd_keys_ventilation)
    nan_fields.extend(nan_fields_electricity)
    nan_fields.extend(nan_fields_water)
    nan_fields.extend(nan_fields_people)

    tsd.update(dict((x, np.zeros(8760) * np.nan) for x in nan_fields))

    # initialize system status log
    tsd['sys_status_ahu'] = np.chararray(8760, itemsize=20)
    tsd['sys_status_aru'] = np.chararray(8760, itemsize=20)
    tsd['sys_status_sen'] = np.chararray(8760, itemsize=20)
    tsd['sys_status_ahu'][:] = 'unknown'
    tsd['sys_status_aru'][:] = 'unknown'
    tsd['sys_status_sen'][:] = 'unknown'

    # TODO: add detailed infiltration air flows
    # tsd['qm_sum_in'] = np.zeros(8760) * np.nan
    # tsd['qm_sum_out'] = np.zeros(8760) * np.nan

    return tsd


def update_timestep_data_no_conditioned_area(tsd):
    """
    Update time step data with zeros for buildings without conditioned area

    Author: Gabriel Happle
    Date: 01/2017

    :param tsd: time series data dict
    :return: update tsd
    """

    zero_fields = ['Qhs_lat_sys', 'Qhs_sen_sys', 'Qcs_lat_sys', 'Qcs_sen_sys', 'Qhs_sen', 'Qcs_sen', 'Ehs_lat_aux',
                   'Qhs_em_ls', 'Qcs_em_ls', 'ma_sup_hs', 'ma_sup_cs', 'Ta_sup_hs', 'Ta_sup_cs', 'Ta_re_hs', 'Ta_re_cs',
                   'Qhsf', 'Qhs', 'Qhsf_lat', 'Qcsf', 'Qcs', 'Qcsf_lat', 'Qcsf', 'Qcs', 'Qhsf', 'Qhs', 'Eauxf',
                   'Eauxf_hs', 'Eauxf_cs', 'Eauxf_ve', 'Eauxf_ww', 'Eauxf_fw', 'Egenf_cs', 'mcphsf', 'mcpcsf', 'mcpwwf',
                   'mcpdataf',
                   'mcpref', 'Twwf_sup', 'Twwf_re', 'Thsf_sup', 'Thsf_re', 'Tcsf_sup', 'Tcsf_re', 'Tcdataf_re',
                   'Tcdataf_sup', 'Tcref_re', 'Tcref_sup', 'Qwwf', 'Qww',
                   'mcptw']

    tsd.update(dict((x, np.zeros(8760)) for x in zero_fields))

    return tsd


def get_hours(bpr):
    """


    :param bpr: BuildingPropertiesRow
    :type bpr:
    :return:
    """

    if bpr.hvac['has-heating-season']:
        # if has heating season start simulating at [before] start of heating season
        hour_start_simulation = control_heating_cooling_systems.convert_date_to_hour(bpr.hvac['heating-season-start'])
    elif not bpr.hvac['has-heating-season'] and bpr.hvac['has-cooling-season']:
        # if has no heating season but cooling season start at [before] start of cooling season
        hour_start_simulation = control_heating_cooling_systems.convert_date_to_hour(bpr.hvac['cooling-season-start'])
    elif not bpr.hvac['has-heating-season'] and not bpr.hvac['has-cooling-season']:
        # no heating or cooling
        hour_start_simulation = 0

    hours_in_year = 8760
    hours_pre_conditioning = 720  # number of hours that the building will be thermally pre-conditioned, the results of these hours will be overwritten
    # TODO: hours_pre_conditioning could be part of config in the future
    hours_simulation_total = hours_in_year + hours_pre_conditioning
    hour_start_simulation = hour_start_simulation - hours_pre_conditioning

    t = hour_start_simulation
    for i in xrange(hours_simulation_total):
        yield (t + i) % hours_in_year

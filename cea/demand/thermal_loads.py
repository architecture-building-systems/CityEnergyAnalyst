# -*- coding: utf-8 -*-
"""
Demand model of thermal loads
"""
from __future__ import division
import numpy as np

from cea.demand import occupancy_model, rc_model_crank_nicholson_procedure, ventilation_air_flows_simple
from cea.demand import ventilation_air_flows_detailed
from cea.demand import sensible_loads, electrical_loads, hotwater_loads, refrigeration_loads, datacenter_loads
from cea.technologies import controllers
from cea.utilities import helpers


# demand model of thermal and electrical loads

def calc_thermal_loads(building_name, bpr, weather_data, usage_schedules, date, gv, locator,
                       use_dynamic_infiltration_calculation=False):
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
        tsd = controllers.calc_simple_temp_control(tsd, bpr.comfort, gv.seasonhours[0] + 1, gv.seasonhours[1],
                                                   date.dayofweek)



        # end-use demand calculation
        for t in range(-720, 8760):
            hoy = helpers.seasonhour_2_hoy(t, gv)

            # heat flows in [W]
            # sensible heat gains
            tsd = sensible_loads.calc_Qgain_sen(hoy, tsd, bpr, gv)

            if use_dynamic_infiltration_calculation:
                # OVERWRITE STATIC INFILTRATION WITH DYNAMIC INFILTRATION RATE
                dict_props_nat_vent = ventilation_air_flows_detailed.get_properties_natural_ventilation(bpr, gv)
                qm_sum_in, qm_sum_out = ventilation_air_flows_detailed.calc_air_flows(
                    tsd['T_int'][hoy - 1] if not np.isnan(tsd['T_int'][hoy - 1]) else tsd['T_ext'][hoy - 1],
                    tsd['u_wind'][hoy], tsd['T_ext'][hoy], dict_props_nat_vent)
                # INFILTRATION IS FORCED NOT TO REACH ZERO IN ORDER TO AVOID THE RC MODEL TO FAIL
                tsd['m_ve_inf'][hoy] = max(qm_sum_in / 3600, 1 / 3600)

            # ventilation air flows [kg/s]
            ventilation_air_flows_simple.calc_air_mass_flow_mechanical_ventilation(bpr, tsd, hoy)
            ventilation_air_flows_simple.calc_air_mass_flow_window_ventilation(bpr, tsd, hoy)

            # ventilation air temperature
            ventilation_air_flows_simple.calc_theta_ve_mech(bpr, tsd, hoy, gv)

            # heating / cooling demand of building
            rc_model_crank_nicholson_procedure.calc_rc_model_demand_heating_cooling(bpr, tsd, hoy, gv)

            # END OF FOR LOOP

        # add emission losses to heating / cooling demand
        tsd['Qhs_sen_incl_em_ls'] = tsd['Qhs_sen_sys'] + tsd['Qhs_em_ls']
        tsd['Qcs_sen_incl_em_ls'] = tsd['Qcs_sen_sys'] + tsd['Qcs_em_ls']

        # Calc of Qhs_dis_ls/Qcs_dis_ls - losses due to distribution of heating/cooling coils
        Qhs_d_ls, Qcs_d_ls = np.vectorize(sensible_loads.calc_Qhs_Qcs_dis_ls)(tsd['T_int'], tsd['T_ext'],
                                                                              tsd['Qhs_sen_incl_em_ls'],
                                                                              tsd['Qcs_sen_incl_em_ls'],
                                                                              bpr.building_systems['Ths_sup_0'],
                                                                              bpr.building_systems['Ths_re_0'],
                                                                              bpr.building_systems['Tcs_sup_0'],
                                                                              bpr.building_systems['Tcs_re_0'],
                                                                              np.nanmax(tsd['Qhs_sen_incl_em_ls']),
                                                                              np.nanmin(tsd['Qcs_sen_incl_em_ls']),
                                                                              gv.D, bpr.building_systems['Y'][0],
                                                                              bpr.hvac['type_hs'],
                                                                              bpr.hvac['type_cs'], gv.Bf,
                                                                              bpr.building_systems['Lv'])

        tsd['Qcsf_lat'] = tsd['Qcs_lat_sys']
        tsd['Qhsf_lat'] = tsd['Qhs_lat_sys']

        # Calc requirements of generation systems (both cooling and heating do not have a storage):
        tsd['Qhs'] = tsd['Qhs_sen_sys']
        tsd['Qhsf'] = tsd['Qhs'] + tsd['Qhs_em_ls'] + Qhs_d_ls  # no latent is considered because it is already added a
        # s electricity from the adiabatic system.
        tsd['Qcs'] = tsd['Qcs_sen_sys'] + tsd['Qcsf_lat']
        tsd['Qcsf'] = tsd['Qcs'] + tsd['Qcs_em_ls'] + Qcs_d_ls
        # Calc nominal temperatures of systems
        Qhsf_0 = np.nanmax(tsd['Qhsf'])  # in W
        Qcsf_0 = np.nanmin(tsd['Qcsf'])  # in W in negative

        # Cal temperatures of all systems
        tsd['Tcsf_re'], tsd['Tcsf_sup'], tsd['Thsf_re'], \
        tsd['Thsf_sup'], tsd['mcpcsf'], tsd['mcphsf'] = sensible_loads.calc_temperatures_emission_systems(tsd, bpr,
                                                                                                          Qcsf_0,
                                                                                                          Qhsf_0,
                                                                                                          gv)

        # calc hot water load
        Mww, tsd['Qww'], Qww_ls_st, tsd['Qwwf'], Qwwf_0, Tww_st, Vww, Vw, tsd['mcpwwf'] = hotwater_loads.calc_Qwwf(
            bpr.building_systems['Lcww_dis'], bpr.building_systems['Lsww_dis'], bpr.building_systems['Lvww_c'],
            bpr.building_systems['Lvww_dis'], tsd['T_ext'], tsd['T_int'], tsd['Twwf_re'],
            bpr.building_systems['Tww_sup_0'], bpr.building_systems['Y'], gv, schedules,
            bpr)

        # calc auxiliary loads
        tsd['Eauxf'], tsd['Eauxf_hs'], tsd['Eauxf_cs'], \
        tsd['Eauxf_ve'], tsd['Eauxf_ww'], tsd['Eauxf_fw'] = electrical_loads.calc_Eauxf(bpr.geometry['Blength'],
                                                                                        bpr.geometry['Bwidth'],
                                                                                        Mww, tsd['Qcsf'], Qcsf_0,
                                                                                        tsd['Qhsf'], Qhsf_0,
                                                                                        tsd['Qww'],
                                                                                        tsd['Qwwf'], Qwwf_0,
                                                                                        tsd['Tcsf_re'],
                                                                                        tsd['Tcsf_sup'],
                                                                                        tsd['Thsf_re'],
                                                                                        tsd['Thsf_sup'],
                                                                                        Vw,
                                                                                        bpr.age['built'],
                                                                                        bpr.building_systems[
                                                                                            'fforma'],
                                                                                        gv,
                                                                                        bpr.geometry['floors_ag'],
                                                                                        bpr.occupancy['PFloor'],
                                                                                        bpr.hvac['type_cs'],
                                                                                        bpr.hvac['type_hs'],
                                                                                        tsd['Ehs_lat_aux'],
                                                                                        tsd)

    elif bpr.rc_model['Af'] == 0:  # if building does not have conditioned area

        tsd = update_timestep_data_no_conditioned_area(tsd)

    else:
        raise

    # calculate other quantities
    ##processese
    tsd['Qhprof'][:] = schedules['Qhpro'] * bpr.internal_loads['Qhpro_Wm2'] * bpr.rc_model['Af']  # in kWh

    ##change sign to latent and sensible cooling loads
    tsd['Qcsf_lat'] = abs(tsd['Qcsf_lat'])
    tsd['Qcsf'] = abs(tsd['Qcsf'])
    tsd['Qcs'] = abs(tsd['Qcs'])

    ## electricity demand due to heatpumps/cooling units in the building
    # TODO: do it for heatpumps tsd['Egenf_cs']
    electrical_loads.calc_heatpump_cooling_electricity(bpr, tsd, gv)

    ## number of people
    tsd['people'] = np.floor(tsd['people'])

    tsd['QHf'] = tsd['Qhsf'] + tsd['Qwwf'] + tsd['Qhprof']
    tsd['QCf'] = tsd['Qcsf'] + tsd['Qcdataf'] + tsd['Qcref']
    tsd['Ef'] = tsd['Ealf'] + tsd['Edataf'] + tsd['Eprof'] + tsd['Ecaf'] + tsd['Eauxf'] + tsd['Eref'] + tsd['Egenf_cs']
    tsd['QEf'] = tsd['QHf'] + tsd['QCf'] + tsd['Ef']

    # write results to csv
    gv.demand_writer.results_to_csv(tsd, bpr, locator, date, building_name)
    # write report
    gv.report(tsd, locator.get_demand_results_folder(), building_name)

    return


def initialize_inputs(bpr, gv, usage_schedules, weather_data):
    #this is used in the NN please do not erase or change!!
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
    tsd['w_int'] = sensible_loads.calc_Qgain_lat(schedules, bpr.internal_loads['X_ghp'], bpr.rc_model['Af'],
                                                 bpr.hvac['type_cs'], bpr.hvac['type_hs'])
    # get electrical loads (no auxiliary loads)
    tsd = electrical_loads.calc_Eint(tsd, bpr, schedules)
    # get refrigeration loads
    tsd['Qcref'], tsd['mcpref'], \
    tsd['Tcref_re'], tsd['Tcref_sup'] = np.vectorize(refrigeration_loads.calc_Qcref)(tsd['Eref'])
    # get server loads
    tsd['Qcdataf'], tsd['mcpdataf'], \
    tsd['Tcdataf_re'], tsd['Tcdataf_sup'] = np.vectorize(datacenter_loads.calc_Qcdataf)(tsd['Edataf'])
    # ground water temperature in C during heating season (winter) according to norm
    tsd['Twwf_re'][:] = bpr.building_systems['Tww_re_0']
    # ground water temperature in C during non-heating season (summer) according to norm  -  FIXME: which norm?
    tsd['Twwf_re'][gv.seasonhours[0] + 1:gv.seasonhours[1] - 1] = 14

    return schedules, tsd


def initialize_timestep_data(bpr, weather_data):
    """
    initializes the time step data with the weather data and the minimum set of variables needed for computation.
    :param bpr:
    :param weather_data:
    :return: returns the `tsd` variable, a dictionary of time step data mapping variable names to ndarrays for each
    hour of the year.
    """
    # Initialize dict with weather variables
    tsd = {'Twwf_sup': bpr.building_systems['Tww_sup_0'],
           'T_ext': weather_data.drybulb_C.values,
           'T_ext_wetbulb': weather_data.wetbulb_C.values,
           'rh_ext': weather_data.relhum_percent.values,
           'T_sky': weather_data.skytemp_C.values,
           'u_wind': weather_data.windspd_ms}
    # fill data with nan values
    nan_fields = ['Qhs_lat_sys', 'Qhs_sen_sys', 'Qcs_lat_sys', 'Qcs_sen_sys', 'T_int', 'theta_m', 'theta_c',
                  'theta_o', 'Qhs_sen', 'Qcs_sen', 'Ehs_lat_aux', 'Qhs_em_ls', 'Qcs_em_ls', 'ma_sup_hs', 'ma_sup_cs',
                  'Ta_sup_hs', 'Ta_sup_cs', 'Ta_re_hs', 'Ta_re_cs', 'I_sol', 'w_int', 'I_rad', 'QEf', 'QHf', 'QCf',
                  'Ef', 'Qhsf', 'Qhs', 'Qhsf_lat', 'Egenf_cs',
                  'Qwwf', 'Qww', 'Qcsf', 'Qcs', 'Qcsf_lat', 'Qhprof', 'Eauxf', 'Eauxf_ve', 'Eauxf_hs', 'Eauxf_cs',
                  'Eauxf_ww', 'Eauxf_fw', 'mcphsf', 'mcpcsf', 'mcpwwf', 'Twwf_re', 'Thsf_sup', 'Thsf_re', 'Tcsf_sup',
                  'Tcsf_re', 'Tcdataf_re', 'Tcdataf_sup', 'Tcref_re', 'Tcref_sup', 'theta_ve_mech', 'm_ve_window',
                  'm_ve_mech', 'm_ve_recirculation', 'm_ve_inf', 'I_sol_gross']
    tsd.update(dict((x, np.zeros(8760) * np.nan) for x in nan_fields))

    # initialize system status log
    tsd['system_status'] = np.chararray(8760, itemsize=20)
    tsd['system_status'][:] = 'unknown'

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
                   'Tcdataf_sup', 'Tcref_re', 'Tcref_sup', 'Qwwf', 'Qww']

    tsd.update(dict((x, np.zeros(8760)) for x in zero_fields))

    return tsd



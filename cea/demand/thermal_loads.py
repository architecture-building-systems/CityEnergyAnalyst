# -*- coding: utf-8 -*-
"""
Demand model of thermal loads
"""
from __future__ import division

import numpy as np
import pandas as pd

from cea.demand import demand_writers
from cea.demand import latent_loads
from cea.demand import occupancy_model, hourly_procedure_heating_cooling_system_load, ventilation_air_flows_simple
from cea.demand import sensible_loads, electrical_loads, hotwater_loads, refrigeration_loads, datacenter_loads
from cea.demand import ventilation_air_flows_detailed, control_heating_cooling_systems
from cea.technologies import heatpumps
from cea.demand.set_point_from_predefined_file import calc_set_point_from_predefined_file

from cea.utilities import reporting


def calc_thermal_loads(building_name, bpr, weather_data, usage_schedules, date, locator, use_stochastic_occupancy,
                       use_dynamic_infiltration_calculation, resolution_outputs, loads_output, massflows_output,
                       temperatures_output, format_output, config, region, write_detailed_output, debug):
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

    :param locator:
    :param use_dynamic_infiltration_calculation:

    :returns: This function does not return anything
    :rtype: NoneType

"""
    schedules, tsd = initialize_inputs(bpr, usage_schedules, weather_data, use_stochastic_occupancy)

    # CALCULATE ELECTRICITY LOADS
    tsd = electrical_loads.calc_Eal_Epro(tsd, bpr, schedules)

    # CALCULATE REFRIGERATION LOADS
    if refrigeration_loads.has_refrigeration_load(bpr):
        tsd = refrigeration_loads.calc_Qcre_sys(bpr, tsd, schedules)
        tsd = refrigeration_loads.calc_Qref(locator, bpr, tsd, region)
    else:
        tsd['DC_cre'] = tsd['Qcre_sys'] = tsd['Qcre'] = np.zeros(8760)
        tsd['mcpcre_sys'] = tsd['Tcre_sys_re'] = tsd['Tcre_sys_sup'] = np.zeros(8760)
        tsd['E_cre'] = np.zeros(8760)

    if np.isclose(bpr.rc_model['Af'], 0.0):  # if building does not have conditioned area

        #UPDATE ALL VALUES TO 0
        tsd = update_timestep_data_no_conditioned_area(tsd)

    else:

        #CALCULATE PROCESS HEATING
        tsd['Qhpro_sys'][:] = schedules['Qhpro'] * bpr.internal_loads['Qhpro_Wm2']  # in kWh

        # CALCULATE DATA CENTER LOADS
        if datacenter_loads.has_data_load(bpr):
            tsd = datacenter_loads.calc_Edata(bpr, tsd, schedules)  # end-use electricity
            tsd = datacenter_loads.calc_Qcdata_sys(tsd)  # system need for cooling
            tsd = datacenter_loads.calc_Qcdataf(locator, bpr, tsd, region)  # final need for cooling
        else:
            tsd['DC_cdata'] = tsd['Qcdata_sys'] = tsd['Qcdata'] = np.zeros(8760)
            tsd['mcpcdata_sys'] = tsd['Tcdata_sys_re'] = tsd['Tcdata_sys_sup'] = np.zeros(8760)
            tsd['Edata'] = tsd['E_cdata'] = np.zeros(8760)

        #CALCULATE HEATING AND COOLING DEMAND
        tsd = calc_set_points(bpr, date, tsd, building_name, config, locator)  # calculate the setpoints for every hour
        tsd = calc_Qhs_Qcs(bpr, tsd, use_dynamic_infiltration_calculation, region)  #end-use demand latent and sensible + ventilation
        tsd = sensible_loads.calc_Qhs_Qcs_loss(bpr, tsd) # losses
        tsd = sensible_loads.calc_Qhs_sys_Qcs_sys(tsd) # system (incl. losses)
        tsd = sensible_loads.calc_temperatures_emission_systems(bpr, tsd) # calculate temperatures
        tsd = electrical_loads.calc_Eauxf_ve(tsd) #calc auxiliary loads ventilation
        tsd = electrical_loads.calc_Eaux_Qhs_Qcs(tsd, bpr) #calc auxiliary loads heating and cooling

        #SOME TRICKS FOR THE GRAPHS - see where to put this.
        tsd = latent_loads.calc_latent_gains_from_people(tsd, bpr)
        tsd['Qcs_lat_sys'] = abs(tsd['Qcs_lat_sys'])
        tsd['DC_cs'] = abs(tsd['DC_cs'])
        tsd['Qcs_sys'] = abs(tsd['Qcs_sys'])

        tsd = calc_Qcs_sys(bpr, tsd) # final : including fuels and renewables
        tsd = calc_Qhs_sys(bpr, tsd) # final : including fuels and renewables

        #CALCULATE HOT WATER LOADS
        if hotwater_loads.has_hot_water_technical_system(bpr):
            tsd = electrical_loads.calc_Eaux_fw(tsd, bpr, schedules)
            tsd = hotwater_loads.calc_Qww(bpr, tsd, schedules) # end-use
            tsd = hotwater_loads.calc_Qww_sys(bpr, tsd) # system (incl. losses)
            tsd = electrical_loads.calc_Eaux_ww(tsd, bpr) #calc auxiliary loads
            tsd = hotwater_loads.calc_Qwwf(bpr, tsd) #final
        else:
            tsd = electrical_loads.calc_Eaux_fw(tsd, bpr, schedules)
            tsd['Qww'] = tsd['DH_ww'] = tsd['Qww_sys'] = np.zeros(8760)
            tsd['mcpww_sys'] = tsd['Tww_sys_re'] = tsd['Tww_sys_sup'] = np.zeros(8760)
            tsd['Eaux_ww'] = tsd['SOLAR_ww'] = np.zeros(8760)
            tsd['NG_ww'] = tsd['COAL_ww'] = tsd['OIL_ww'] =  tsd['WOOD_ww'] = np.zeros(8760)
            tsd['E_ww'] = np.zeros(8760)

            # CALCULATE SUM OF HEATING AND COOLING LOADS
        tsd = calc_QH_sys_QC_sys(tsd)  # aggregated cooling and heating loads

    #CALCULATE ELECTRICITY LOADS PART 2/2 AUXILIARY LOADS + ENERGY GENERATION
    tsd = electrical_loads.calc_Eaux(tsd) # auxiliary totals
    tsd = electrical_loads.calc_E_sys(tsd) # system (incl. losses)
    tsd = electrical_loads.calc_Ef(bpr, tsd)  # final (incl. self. generated)

    #WRITE SOLAR RESULTS
    write_results(bpr, building_name, date, format_output, loads_output, locator, massflows_output,
                  resolution_outputs, temperatures_output, tsd, write_detailed_output, debug)

    return

def calc_QH_sys_QC_sys(tsd):

    tsd['QH_sys'] = tsd['Qww_sys'] + tsd['Qhs_sys'] + tsd['Qhpro_sys']
    tsd['QC_sys'] = tsd['Qcs_sys'] + tsd['Qcdata_sys'] + tsd['Qcre_sys']

    return tsd


def write_results(bpr, building_name, date, format_output, loads_output, locator, massflows_output,
                  resolution_outputs, temperatures_output, tsd, write_detailed_output, debug):

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

    if write_detailed_output:
        print('Writing detailed demand results of {} to .xls file.'.format(building_name))
        reporting.full_report_to_xls(tsd, locator.get_demand_results_folder(), building_name)

    if debug:
        print('Creating instant plotly visualizations of demand variable time series.')
        print('Behavior can be changed in cea.utilities.reporting code.')
        reporting.quick_visualization_tsd(tsd, locator.get_demand_results_folder(), building_name)


def calc_Qcs_sys(bpr, tsd):

    # GET SYSTEMS EFFICIENCIES
    energy_source = bpr.supply['source_cs']
    scale_technology = bpr.supply['scale_cs']
    efficiency_average_year = bpr.supply['eff_cs']
    if scale_technology == "BUILDING":
        if energy_source == "GRID":
            if bpr.supply['type_cs'] in {'T2', 'T3'}:
                if bpr.supply['type_cs'] == 'T2':
                    t_source = (tsd['T_ext'] + 273)
                if bpr.supply['type_cs'] == 'T3':
                    t_source = (tsd['T_ext_wetbulb'] + 273)

                # heat pump energy for the 3 components
                # ahu
                E_for_Qcs_sys_ahu = np.vectorize(heatpumps.HP_air_air)(tsd['mcpcs_sys_ahu'], (tsd['Tcs_sys_sup_ahu'] + 273),
                                                                    (tsd['Tcs_sys_re_ahu'] + 273), t_source)
                # aru
                E_for_Qcs_sys_aru = np.vectorize(heatpumps.HP_air_air)(tsd['mcpcs_sys_aru'], (tsd['Tcs_sys_sup_aru'] + 273),
                                                                    (tsd['Tcs_sys_re_aru'] + 273), t_source)
                # scu
                E_for_Qcs_sys_scu = np.vectorize(heatpumps.HP_air_air)(tsd['mcpcs_sys_scu'], (tsd['Tcs_sys_sup_scu'] + 273),
                                                                    (tsd['Tcs_sys_re_scu'] + 273), t_source)
                # sum
                tsd['E_cs'] = E_for_Qcs_sys_scu + E_for_Qcs_sys_aru + E_for_Qcs_sys_ahu
                tsd['DC_cs'] = np.zeros(8760)
        elif energy_source == "NONE":
            tsd['E_cs'] = np.zeros(8760)
            tsd['DC_cs'] = np.zeros(8760)
        else:
            raise Exception('check potential error in input database of LCA infrastructure / COOLING')
    elif scale_technology == "DISTRICT":
        tsd['DC_cs'] = tsd['Qcs_sys'] / efficiency_average_year
        tsd['E_cs'] = np.zeros(8760)
    elif scale_technology == "NONE":
        tsd['DC_cs'] = np.zeros(8760)
        tsd['E_cs'] = np.zeros(8760)
    else:
        raise Exception('check potential error in input database of LCA infrastructure / COOLING')
    return tsd

def calc_Qhs_sys(bpr, tsd):
    """
    it calculates final loads
    """

    # GET SYSTEMS EFFICIENCIES
    # GET SYSTEMS EFFICIENCIES
    energy_source = bpr.supply['source_hs']
    scale_technology = bpr.supply['scale_hs']
    efficiency_average_year = bpr.supply['eff_hs']

    if scale_technology == "BUILDING":
        if energy_source == "GRID":
            tsd['E_hs'] =  tsd['Qhs_sys']/efficiency_average_year
            tsd['SOLAR_hs'] = np.zeros(8760)
            tsd['DH_hs'] = np.zeros(8760)
            tsd['NG_hs'] = np.zeros(8760)
            tsd['COAL_hs'] = np.zeros(8760)
            tsd['OIL_hs'] = np.zeros(8760)
            tsd['WOOD_hs'] = np.zeros(8760)
        elif energy_source == "NATURALGAS":
            tsd['NG_hs'] = tsd['Qhs_sys']/efficiency_average_year
            tsd['COAL_hs'] = np.zeros(8760)
            tsd['OIL_hs'] = np.zeros(8760)
            tsd['WOOD_hs'] = np.zeros(8760)
            tsd['DH_hs'] = np.zeros(8760)
            tsd['E_hs'] = np.zeros(8760)
            tsd['SOLAR_hs'] = np.zeros(8760)
        elif energy_source == "OIL":
            tsd['NG_hs'] = np.zeros(8760)
            tsd['COAL_hs'] = np.zeros(8760)
            tsd['OIL_hs'] = tsd['Qhs_sys']/efficiency_average_year
            tsd['WOOD_hs'] = np.zeros(8760)
            tsd['DH_hs'] = np.zeros(8760)
            tsd['E_hs'] = np.zeros(8760)
            tsd['SOLAR_hs'] = np.zeros(8760)
        elif energy_source == "COAL":
            tsd['NG_hs'] = np.zeros(8760)
            tsd['COAL_hs'] = tsd['Qhs_sys']/efficiency_average_year
            tsd['OIL_hs'] = np.zeros(8760)
            tsd['WOOD_hs'] = np.zeros(8760)
            tsd['DH_hs'] = np.zeros(8760)
            tsd['E_hs'] = np.zeros(8760)
            tsd['SOLAR_hs'] = np.zeros(8760)
        elif energy_source == "WOOD":
            tsd['NG_hs'] = np.zeros(8760)
            tsd['COAL_hs'] = np.zeros(8760)
            tsd['OIL_hs'] = np.zeros(8760)
            tsd['WOOD_hs'] = tsd['Qhs_sys']/efficiency_average_year
            tsd['DH_hs'] = np.zeros(8760)
            tsd['E_hs'] = np.zeros(8760)
            tsd['SOLAR_hs'] = np.zeros(8760)
        elif energy_source == "SOLAR":
            tsd['NG_hs'] = np.zeros(8760)
            tsd['COAL_hs'] = np.zeros(8760)
            tsd['OIL_hs'] = np.zeros(8760)
            tsd['WOOD_hs'] = np.zeros(8760)
            tsd['SOLAR_hs'] =  tsd['Qhs_sys']/efficiency_average_year
            tsd['DH_hs'] = np.zeros(8760)
            tsd['E_hs'] = np.zeros(8760)
        elif energy_source == "NONE":
            tsd['NG_hs'] = np.zeros(8760)
            tsd['COAL_hs'] = np.zeros(8760)
            tsd['OIL_hs'] = np.zeros(8760)
            tsd['WOOD_hs'] = np.zeros(8760)
            tsd['DH_hs'] = np.zeros(8760)
            tsd['E_hs'] = np.zeros(8760)
            tsd['SOLAR_hs'] = np.zeros(8760)
        else:
            raise Exception('check potential error in input database of LCA infrastructure / HEATING')
    elif scale_technology == "DISTRICT":
            tsd['NG_hs'] = np.zeros(8760)
            tsd['COAL_hs'] = np.zeros(8760)
            tsd['OIL_hs'] = np.zeros(8760)
            tsd['WOOD_hs'] = np.zeros(8760)
            tsd['DH_hs'] = tsd['Qhs_sys']/efficiency_average_year
            tsd['E_hs'] = np.zeros(8760)
            tsd['SOLAR_hs'] = np.zeros(8760)
    elif scale_technology == "NONE":
            tsd['NG_hs'] = np.zeros(8760)
            tsd['COAL_hs'] = np.zeros(8760)
            tsd['OIL_hs'] = np.zeros(8760)
            tsd['WOOD_hs'] = np.zeros(8760)
            tsd['DH_hs'] = np.zeros(8760)
            tsd['E_hs'] = np.zeros(8760)
            tsd['SOLAR_hs'] = np.zeros(8760)
    else:
        raise Exception('check potential error in input database of LCA infrastructure / HEATING')
    return tsd

def calc_set_points(bpr, date, tsd, building_name, config, locator):
    # get internal comfort properties
    # predefined set points for every given hour can be used to calculate the demand profile for a building
    # a config flag is used for this, it is present in the config.demand section
    if config.demand.predefined_hourly_setpoints:
        tsd = calc_set_point_from_predefined_file(tsd, bpr, date.dayofweek, building_name, locator)
    else:
        tsd = control_heating_cooling_systems.calc_simple_temp_control(tsd, bpr, date.dayofweek)

    t_prev = get_hours(bpr).next() - 1
    tsd['T_int'][t_prev] = tsd['T_ext'][t_prev]
    tsd['x_int'][t_prev] = latent_loads.convert_rh_to_moisture_content(tsd['rh_ext'][t_prev], tsd['T_ext'][t_prev])
    return tsd


def calc_Qhs_Qcs(bpr, tsd, use_dynamic_infiltration_calculation, region):
    # get ventilation flows
    ventilation_air_flows_simple.calc_m_ve_required(bpr, tsd, region)
    ventilation_air_flows_simple.calc_m_ve_leakage_simple(bpr, tsd)

    # end-use demand calculation
    for t in get_hours(bpr):

        # heat flows in [W]
        tsd = sensible_loads.calc_Qgain_sen(t, tsd, bpr)

        if use_dynamic_infiltration_calculation:
            # OVERWRITE STATIC INFILTRATION WITH DYNAMIC INFILTRATION RATE
            dict_props_nat_vent = ventilation_air_flows_detailed.get_properties_natural_ventilation(bpr)
            qm_sum_in, qm_sum_out = ventilation_air_flows_detailed.calc_air_flows(
                tsd['T_int'][t - 1], tsd['u_wind'][t], tsd['T_ext'][t], dict_props_nat_vent)
            # INFILTRATION IS FORCED NOT TO REACH ZERO IN ORDER TO AVOID THE RC MODEL TO FAIL
            tsd['m_ve_inf'][t] = max(qm_sum_in / 3600, 1 / 3600)

        # ventilation air flows [kg/s]
        ventilation_air_flows_simple.calc_air_mass_flow_mechanical_ventilation(bpr, tsd, t)
        ventilation_air_flows_simple.calc_air_mass_flow_window_ventilation(bpr, tsd, t)

        # ventilation air temperature and humidity
        ventilation_air_flows_simple.calc_theta_ve_mech(bpr, tsd, t)
        latent_loads.calc_moisture_content_airflows(tsd, t)

        # heating / cooling demand of building
        hourly_procedure_heating_cooling_system_load.calc_heating_cooling_loads(bpr, tsd, t)

        # END OF FOR LOOP
    return tsd


def initialize_inputs(bpr, usage_schedules, weather_data, use_stochastic_occupancy):
    """
    :param bpr: a collection of building properties for the building used for thermal loads calculation
    :type bpr: BuildingPropertiesRow
    :param usage_schedules: dict containing schedules and function names of buildings.
    :type usage_schedules: dict
    :param weather_data: data from the .epw weather file. Each row represents an hour of the year. The columns are:
        ``drybulb_C``, ``relhum_percent``, and ``windspd_ms``
    :type weather_data: pandas.DataFrame
    :param use_stochastic_occupancy: Boolean specifying whether stochastic occupancy should be used. If False,
        deterministic schedules are used.
    :type use_stochastic_occupancy: Boolean

    :return schedules:
    :rtype schedules:
    :return tsd: time series data dict
    :rtype tsd: dict
    """
    # TODO: documentation

    # this is used in the NN please do not erase or change!!
    tsd = initialize_timestep_data(bpr, weather_data)
    # get schedules
    list_uses = usage_schedules['list_uses']
    archetype_schedules = usage_schedules['archetype_schedules']
    archetype_values = usage_schedules['archetype_values']
    schedules = occupancy_model.calc_schedules(list_uses, archetype_schedules, bpr, archetype_values,
                                               use_stochastic_occupancy)

    # calculate occupancy schedule and occupant-related parameters
    tsd['people'] = np.floor(schedules['people'])
    tsd['ve'] = schedules['ve'] * (bpr.comfort['Ve_lps'] * 3.6)  # in m3/h
    tsd['Qs'] = schedules['Qs'] * bpr.internal_loads['Qs_Wp']  # in W
    # # latent heat gains
    tsd['w_int'] = sensible_loads.calc_Qgain_lat(schedules, bpr)

    return schedules, tsd


TSD_KEYS_HEATING_LOADS = ['Qhs_sen_rc', 'Qhs_sen_shu', 'Qhs_sen_ahu', 'Qhs_lat_ahu', 'Qhs_sen_aru', 'Qhs_lat_aru',
                          'Qhs_sen_sys', 'Qhs_lat_sys', 'Qhs_em_ls', 'Qhs_dis_ls', 'Qhs_sys_shu', 'Qhs_sys_ahu', 'Qhs_sys_aru',
                          'DH_hs', 'Qhs', 'Qhs_sys', 'QH_sys',
                          'DH_ww', 'Qww_sys', 'Qww', 'Qhs', 'Qhpro_sys']
TSD_KEYS_COOLING_LOADS = ['Qcs_sen_rc', 'Qcs_sen_scu', 'Qcs_sen_ahu', 'Qcs_lat_ahu', 'Qcs_sen_aru', 'Qcs_lat_aru',
                          'Qcs_sen_sys', 'Qcs_lat_sys', 'Qcs_em_ls', 'Qcs_dis_ls', 'Qcs_sys_scu', 'Qcs_sys_ahu', 'Qcs_sys_aru',
                          'DC_cs', 'Qcs', 'Qcs_sys', 'QC_sys',
                          'DC_cre', 'Qcre_sys', 'Qcre',
                          'DC_cdata', 'Qcdata_sys', 'Qcdata']
TSD_KEYS_HEATING_TEMP = ['ta_re_hs_ahu', 'ta_sup_hs_ahu', 'ta_re_hs_aru', 'ta_sup_hs_aru']
TSD_KEYS_HEATING_FLOWS = ['ma_sup_hs_ahu', 'ma_sup_hs_aru']
TSD_KEYS_COOLING_TEMP = ['ta_re_cs_ahu', 'ta_sup_cs_ahu', 'ta_re_cs_aru', 'ta_sup_cs_aru']
TSD_KEYS_COOLING_FLOWS = ['ma_sup_cs_ahu', 'ma_sup_cs_aru']
TSD_KEYS_COOLING_SUPPLY_FLOWS = ['mcpcs_sys_ahu', 'mcpcs_sys_aru', 'mcpcs_sys_scu', 'mcpcs_sys']
TSD_KEYS_COOLING_SUPPLY_TEMP = ['Tcs_sys_re_ahu', 'Tcs_sys_re_aru', 'Tcs_sys_re_scu', 'Tcs_sys_sup_ahu', 'Tcs_sys_sup_aru',
                                'Tcs_sys_sup_scu', 'Tcs_sys_sup', 'Tcs_sys_re',
                                'Tcdata_sys_re', 'Tcdata_sys_sup',
                                'Tcre_sys_re', 'Tcre_sys_sup']
TSD_KEYS_HEATING_SUPPLY_FLOWS = ['mcphs_sys_ahu', 'mcphs_sys_aru', 'mcphs_sys_shu', 'mcphs_sys']
TSD_KEYS_HEATING_SUPPLY_TEMP = ['Ths_sys_re_ahu', 'Ths_sys_re_aru', 'Ths_sys_re_shu', 'Ths_sys_sup_ahu', 'Ths_sys_sup_aru',
                                'Ths_sys_sup_shu', 'Ths_sys_sup', 'Ths_sys_re',
                                'Tww_sys_sup', 'Tww_sys_re']
TSD_KEYS_RC_TEMP = ['T_int', 'theta_m', 'theta_c', 'theta_o', 'theta_ve_mech']
TSD_KEYS_MOISTURE = ['x_int', 'x_ve_inf', 'x_ve_mech', 'g_hu_ld', 'g_dhu_ld']
TSD_KEYS_VENTILATION_FLOWS = ['m_ve_window', 'm_ve_mech', 'm_ve_rec', 'm_ve_inf', 'm_ve_required']
TSD_KEYS_ENERGY_BALANCE_DASHBOARD = ['Q_gain_sen_light', 'Q_gain_sen_app', 'Q_gain_sen_peop', 'Q_gain_sen_data',
                                     'Q_loss_sen_ref', 'Q_gain_sen_wall', 'Q_gain_sen_base', 'Q_gain_sen_roof',
                                     'Q_gain_sen_wind', 'Q_gain_sen_vent', 'Q_gain_lat_peop','Q_gain_sen_pro']
TSD_KEYS_SOLAR = ['I_sol', 'I_rad', 'I_sol_and_I_rad']
TSD_KEYS_PEOPLE = ['people', 've', 'Qs', 'w_int']


def initialize_timestep_data(bpr, weather_data):
    """
    initializes the time step data with the weather data and the minimum set of variables needed for computation.

    :param bpr: a collection of building properties for the building used for thermal loads calculation
    :type bpr: BuildingPropertiesRow
    :param weather_data: data from the .epw weather file. Each row represents an hour of the year. The columns are:
        ``drybulb_C``, ``relhum_percent``, and ``windspd_ms``
    :type weather_data: pandas.DataFrame

    :return: returns the `tsd` variable, a dictionary of time step data mapping variable names to ndarrays for each hour of the year.
    :rtype: dict
    """

    # Initialize dict with weather variables
    tsd = {'T_ext': weather_data.drybulb_C.values,
           'T_ext_wetbulb': weather_data.wetbulb_C.values,
           'rh_ext': weather_data.relhum_percent.values,
           'T_sky': weather_data.skytemp_C.values,
           'u_wind': weather_data.windspd_ms}

    # fill data with nan values

    nan_fields_electricity = ['Eaux', 'Eaux_ve', 'Eaux_hs', 'Eaux_cs', 'Eaux_ww', 'Eaux_fw', 'Ehs_lat_aux',
                              'GRID', 'PV', 'Eal', 'Edata', 'Epro', 'E_sys',
                              'E_ww', 'E_hs', 'E_cs', 'E_cre', 'E_cdata']
    nan_fields = ['mcpww_sys', 'mcptw',
                  'mcpcre_sys',
                  'mcpcdata_sys',
                  'SOLAR_ww',
                  'SOLAR_hs',
                  'NG_hs',
                  'COAL_hs',
                  'OIL_hs',
                  'WOOD_hs',
                  'NG_ww',
                  'COAL_ww',
                  'OIL_ww',
                  'WOOD_ww',
                  'vfw_m3perh']
    nan_fields.extend(TSD_KEYS_HEATING_LOADS)
    nan_fields.extend(TSD_KEYS_COOLING_LOADS)
    nan_fields.extend(TSD_KEYS_HEATING_TEMP)
    nan_fields.extend(TSD_KEYS_COOLING_TEMP)
    nan_fields.extend(TSD_KEYS_COOLING_FLOWS)
    nan_fields.extend(TSD_KEYS_HEATING_FLOWS)
    nan_fields.extend(TSD_KEYS_COOLING_SUPPLY_FLOWS)
    nan_fields.extend(TSD_KEYS_COOLING_SUPPLY_TEMP)
    nan_fields.extend(TSD_KEYS_HEATING_SUPPLY_FLOWS)
    nan_fields.extend(TSD_KEYS_HEATING_SUPPLY_TEMP)
    nan_fields.extend(TSD_KEYS_RC_TEMP)
    nan_fields.extend(TSD_KEYS_MOISTURE)
    nan_fields.extend(TSD_KEYS_ENERGY_BALANCE_DASHBOARD)
    nan_fields.extend(TSD_KEYS_SOLAR)
    nan_fields.extend(TSD_KEYS_VENTILATION_FLOWS)
    nan_fields.extend(nan_fields_electricity)
    nan_fields.extend(TSD_KEYS_PEOPLE)

    tsd.update(dict((x, np.zeros(8760) * np.nan) for x in nan_fields))

    # initialize system status log
    tsd['sys_status_ahu'] = np.chararray(8760, itemsize=20)
    tsd['sys_status_aru'] = np.chararray(8760, itemsize=20)
    tsd['sys_status_sen'] = np.chararray(8760, itemsize=20)
    tsd['sys_status_ahu'][:] = 'unknown'
    tsd['sys_status_aru'][:] = 'unknown'
    tsd['sys_status_sen'][:] = 'unknown'

    return tsd


def update_timestep_data_no_conditioned_area(tsd):
    """
    Update time step data with zeros for buildings without conditioned area

    Author: Gabriel Happle
    Date: 01/2017

    :param tsd: time series data dict
    :return: update tsd
    """

    zero_fields = ['Qhs_lat_sys', 'Qhs_sen_sys',
                   'Qcs_lat_sys', 'Qcs_sen_sys',
                   'Qhs_sen', 'Qcs_sen', 'x_int',
                   'Qhs_em_ls', 'Qcs_em_ls', 'Qhpro_sys'
                   'ma_sup_hs', 'ma_sup_cs',
                   'Ta_sup_hs', 'Ta_re_hs',
                   'Ta_sup_cs', 'Ta_re_cs',
                   'NG_hs',
                   'COAL_hs',
                   'OIL_hs',
                   'WOOD_hs',
                   'NG_ww',
                   'COAL_ww',
                   'OIL_ww',
                   'WOOD_ww','vfw_m3perh',
                   'SOLAR_hs', 'DH_hs', 'Qhs_sys', 'Qhs',
                   'SOLAR_ww', 'DH_ww', 'Qww_sys', 'Qww',
                   'DC_cs', 'DC_cs_lat', 'Qcs_sys', 'Qcs',
                   'DC_cdata', 'Qcdata_sys', 'Qcdata',
                   'DC_cre', 'Qcre_sys', 'Qcre',
                   'Eaux','Ehs_lat_aux', 'Eaux_hs', 'Eaux_cs', 'Eaux_ve', 'Eaux_ww', 'Eaux_fw',
                   'E_sys', 'PV', 'GRID', 'E_ww', 'E_hs', 'E_cs', 'E_cre', 'E_cdata', 'E_pro',
                   'Epro', 'Edata', 'Ea', 'El', 'Eal',
                   'mcphs_sys', 'mcpcs_sys', 'mcptw'
                   'mcpww_sys','mcpcdata_sys','mcpcre_sys',
                   'Tcdata_sys_re', 'Tcdata_sys_sup',
                   'Tcre_sys_re', 'Tcre_sys_sup',
                   'Tww_sys_sup', 'Tww_sys_re',
                   'Ths_sys_sup', 'Ths_sys_re',
                   'Tcs_sys_sup', 'Tcs_sys_re',
                   'DH_ww', 'Qww_sys', 'Qww',
                   'mcptw', 'I_sol', 'I_rad',
                   'Qgain_light', 'Qgain_app', 'Qgain_pers', 'Qgain_data', 'Qgain_wall', 'Qgain_base', 'Qgain_roof',
                   'Qgain_wind', 'Qgain_vent'
                   'Q_cool_ref', 'q_cs_lat_peop']

    tsd.update(dict((x, np.zeros(8760)) for x in zero_fields))

    tsd['T_int'] = tsd['T_ext'].copy()

    return tsd


HOURS_IN_YEAR = 8760
HOURS_PRE_CONDITIONING = 720  # number of hours that the building will be thermally pre-conditioned, the results of these hours will be overwritten


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

    # TODO: HOURS_PRE_CONDITIONING could be part of config in the future
    hours_simulation_total = HOURS_IN_YEAR + HOURS_PRE_CONDITIONING
    hour_start_simulation = hour_start_simulation - HOURS_PRE_CONDITIONING

    t = hour_start_simulation
    for i in xrange(hours_simulation_total):
        yield (t + i) % HOURS_IN_YEAR

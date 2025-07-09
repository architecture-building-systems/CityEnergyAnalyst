# -*- coding: utf-8 -*-
"""
Demand model of thermal loads
"""



from __future__ import annotations
import numpy as np
import pandas as pd

from cea.constants import HOURS_IN_YEAR, HOURS_PRE_CONDITIONING
from cea.demand import demand_writers
from cea.demand import hourly_procedure_heating_cooling_system_load, ventilation_air_flows_simple
from cea.demand import latent_loads
from cea.demand import sensible_loads, electrical_loads, hotwater_loads, refrigeration_loads, datacenter_loads
from cea.demand import ventilation_air_flows_detailed, control_heating_cooling_systems
from cea.demand.building_properties import get_thermal_resistance_surface
from cea.demand.latent_loads import convert_rh_to_moisture_content
from cea.utilities import reporting
from typing import TYPE_CHECKING, List, Dict, Tuple, Union

if TYPE_CHECKING:
    from cea.config import Configuration
    from cea.inputlocator import InputLocator
    from cea.demand.building_properties import BuildingPropertiesRow


def calc_thermal_loads(building_name: str, 
                       bpr: BuildingPropertiesRow, 
                       weather_data: pd.DataFrame, 
                       date_range: pd.date_range, 
                       locator: InputLocator,
                       use_dynamic_infiltration_calculation: bool, 
                       resolution_outputs: str, 
                       loads_output: List[str], 
                       massflows_output: List[str],
                       temperatures_output: List[str], 
                       config: Configuration, 
                       debug: bool,
                       ):
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
      probability of use), with each element of the 4-tuple being a list of hourly values (HOURS_IN_YEAR values).


    Side effect include a number of files in two folders:

    * ``scenario/outputs/data/demand``

      * ``${name}.csv`` for each building

    * temporary folder (as returned by ``tempfile.gettempdir()``)

      * ``${name}T.csv`` for each building

    daren-thomas: as far as I can tell, these are the only side-effects.

    :param building_name: name of building
    :type building_name: str

    :param bpr: a collection of building properties for the building used for thermal loads calculation
    :type bpr: BuildingPropertiesRow

    :param weather_data: data from the .epw weather file. Each row represents an hour of the year. The columns are:
        ``drybulb_C``, ``relhum_percent``, and ``windspd_ms``
    :type weather_data: pandas.DataFrame

    :param locator: object containing methods of locating scenario files
    :type locator: cea.inputlocator.InputLocator
    :param use_dynamic_infiltration_calculation: True if dynamic infiltration calculations are considered (slower run times!).
    :rtype use_dynamic_infiltration_calculation: bool
    :param resolution_outputs: Time step resolution of the demand simulation (hourly or monthly).
    :type resolution_outputs: str
    :param loads_output: List of loads output by the demand simulation (to simulate all load types in demand_writer, leave blank).
    :type loads_output: list[str]
    :param massflows_output: List of mass flow rates output by the demand simulation (to simulate all system mass flow rates in demand_writer, leave blank).
    :type massflows_output: list[str]
    :param temperatures_output: List of temperatures output by the demand simulation (to simulate all temperatures in demand_writer, leave blank).
    :type temperatures_output: list[str]
    :param config: cea configuration
    :type config: cea.configuration.Configuration
    :param debug: Enable debugging-specific behaviors.
    :type debug: bool

    :returns: This function does not return anything
    :rtype: NoneType

    """
    tsd = initialize_timestep_data(weather_data)
    schedules, tsd = initialize_schedules(bpr, tsd, locator)

    # CALCULATE ELECTRICITY LOADS
    tsd = electrical_loads.calc_Eal_Epro(tsd, schedules)

    # CALCULATE REFRIGERATION LOADS
    if refrigeration_loads.has_refrigeration_load(bpr):
        tsd = refrigeration_loads.calc_Qcre_sys(bpr, tsd, schedules)
        tsd = refrigeration_loads.calc_Qref(locator, bpr, tsd)
    else:
        tsd['DC_cre'] = tsd['Qcre_sys'] = tsd['Qcre'] = np.zeros(HOURS_IN_YEAR)
        tsd['mcpcre_sys'] = tsd['Tcre_sys_re'] = tsd['Tcre_sys_sup'] = np.zeros(HOURS_IN_YEAR)
        tsd['E_cre'] = np.zeros(HOURS_IN_YEAR)

    # CALCULATE PROCESS HEATING
    tsd['Qhpro_sys'] = schedules['Qhpro_W']  # in Wh

    # CALCULATE PROCESS COOLING
    tsd['Qcpro_sys'] = schedules['Qcpro_W']  # in Wh

    # CALCULATE DATA CENTER LOADS
    if datacenter_loads.has_data_load(bpr):
        tsd = datacenter_loads.calc_Edata(tsd, schedules)  # end-use electricity
        tsd = datacenter_loads.calc_Qcdata_sys(bpr, tsd)  # system need for cooling
        tsd = datacenter_loads.calc_Qcdataf(locator, bpr, tsd)  # final need for cooling
    else:
        tsd['DC_cdata'] = tsd['Qcdata_sys'] = tsd['Qcdata'] = np.zeros(HOURS_IN_YEAR)
        tsd['mcpcdata_sys'] = tsd['Tcdata_sys_re'] = tsd['Tcdata_sys_sup'] = np.zeros(HOURS_IN_YEAR)
        tsd['Edata'] = tsd['E_cdata'] = np.zeros(HOURS_IN_YEAR)

    # CALCULATE SPACE CONDITIONING DEMANDS
    if np.isclose(bpr.rc_model['Af'], 0.0):  # if building does not have conditioned area
        tsd['T_int'] = tsd['T_ext']
        tsd['x_int'] = np.vectorize(convert_rh_to_moisture_content)(tsd['rh_ext'], tsd['T_int'])
        tsd['E_cs'] = tsd['E_hs'] = np.zeros(HOURS_IN_YEAR)
        tsd['Eaux_cs'] = tsd['Eaux_hs'] = tsd['Ehs_lat_aux'] = np.zeros(HOURS_IN_YEAR)
        print(f"building {bpr.name} does not have an air-conditioned area")
    else:
        # get hourly thermal resistances of external surfaces
        tsd['RSE_wall'], \
        tsd['RSE_roof'], \
        tsd['RSE_win'], \
        tsd['RSE_underside'] = get_thermal_resistance_surface(bpr.architecture, weather_data)
        # calculate heat gains
        tsd = latent_loads.calc_Qgain_lat(tsd, schedules)
        tsd = calc_set_points(bpr, date_range, tsd, building_name, config, locator,
                              schedules)  # calculate the setpoints for every hour
        tsd = calc_Qhs_Qcs(bpr, tsd,
                           use_dynamic_infiltration_calculation, config)  # end-use demand latent and sensible + ventilation
        tsd = sensible_loads.calc_Qhs_Qcs_loss(bpr, tsd)  # losses
        tsd = sensible_loads.calc_Qhs_sys_Qcs_sys(tsd)  # system (incl. losses)
        tsd = sensible_loads.calc_temperatures_emission_systems(bpr, tsd)  # calculate temperatures
        tsd = electrical_loads.calc_Eve(tsd)  # calc auxiliary loads ventilation
        tsd = electrical_loads.calc_Eaux_Qhs_Qcs(tsd, bpr)  # calc auxiliary loads heating and cooling
        tsd = calc_Qcs_sys(bpr, tsd)  # final : including fuels and renewables
        tsd = calc_Qhs_sys(bpr, tsd)  # final : including fuels and renewables

        # Positive loads
        tsd['Qcs_lat_sys'] = abs(tsd['Qcs_lat_sys'])
        tsd['DC_cs'] = abs(tsd['DC_cs'])
        tsd['Qcs_sys'] = abs(tsd['Qcs_sys'])
        tsd['Qcre_sys'] = abs(tsd['Qcre_sys'])  # inverting sign of cooling loads for reporting and graphs
        tsd['Qcdata_sys'] = abs(tsd['Qcdata_sys'])  # inverting sign of cooling loads for reporting and graphs

    # CALCULATE HOT WATER LOADS
    if hotwater_loads.has_hot_water_technical_system(bpr):
        tsd = electrical_loads.calc_Eaux_fw(tsd, bpr, schedules)
        tsd = hotwater_loads.calc_Qww(bpr, tsd, schedules)  # end-use
        tsd = hotwater_loads.calc_Qww_sys(bpr, tsd)  # system (incl. losses)
        tsd = electrical_loads.calc_Eaux_ww(tsd, bpr)  # calc auxiliary loads
        tsd = hotwater_loads.calc_Qwwf(bpr, tsd)  # final
    else:
        tsd = electrical_loads.calc_Eaux_fw(tsd, bpr, schedules)
        tsd['Qww'] = tsd['DH_ww'] = tsd['Qww_sys'] = np.zeros(HOURS_IN_YEAR)
        tsd['mcpww_sys'] = tsd['Tww_sys_re'] = tsd['Tww_sys_sup'] = np.zeros(HOURS_IN_YEAR)
        tsd['Eaux_ww'] = np.zeros(HOURS_IN_YEAR)
        tsd['NG_ww'] = tsd['COAL_ww'] = tsd['OIL_ww'] = tsd['WOOD_ww'] = np.zeros(HOURS_IN_YEAR)
        tsd['E_ww'] = np.zeros(HOURS_IN_YEAR)

    # CALCULATE SUM OF HEATING AND COOLING LOADS
    tsd = calc_QH_sys_QC_sys(tsd)  # aggregated cooling and heating loads

    # CALCULATE ELECTRICITY LOADS PART 2/2 AUXILIARY LOADS + ENERGY GENERATION
    tsd = electrical_loads.calc_Eaux(tsd)  # auxiliary totals
    tsd = electrical_loads.calc_E_sys(tsd)  # system (incl. losses)
    tsd = electrical_loads.calc_Ef(bpr, tsd)  # final (incl. self. generated)

    # WRITE SOLAR RESULTS
    write_results(bpr, building_name, date_range, loads_output, locator, massflows_output,
                  resolution_outputs, temperatures_output, tsd, debug)

    return


def calc_QH_sys_QC_sys(tsd):
    tsd['QH_sys'] = tsd['Qww_sys'] + tsd['Qhs_sys'] + tsd['Qhpro_sys']
    tsd['QC_sys'] = tsd['Qcs_sys'] + tsd['Qcdata_sys'] + tsd['Qcre_sys'] + tsd['Qcpro_sys']

    return tsd


def write_results(bpr, building_name, date, loads_output, locator, massflows_output,
                  resolution_outputs, temperatures_output, tsd, debug):
    if resolution_outputs == 'hourly':
        writer = demand_writers.HourlyDemandWriter(loads_output, massflows_output, temperatures_output)
    elif resolution_outputs == 'monthly':
        writer = demand_writers.MonthlyDemandWriter(loads_output, massflows_output, temperatures_output)
    else:
        raise Exception('error')

    if debug:
        print('Creating instant plotly visualizations of demand variable time series.')
        print('Behavior can be changed in cea.utilities.reporting code.')
        print('Writing detailed demand results of {} to .xls file.'.format(building_name))
        reporting.quick_visualization_tsd(tsd, locator.get_demand_results_folder(), building_name)
        reporting.full_report_to_xls(tsd, locator.get_demand_results_folder(), building_name)

    writer.results_to_csv(tsd, bpr, locator, date, building_name)


def calc_Qcs_sys(bpr, tsd):
    # GET SYSTEMS EFFICIENCIES
    energy_source = bpr.supply['source_cs']
    scale_technology = bpr.supply['scale_cs']
    efficiency_average_year = bpr.supply['eff_cs']
    if scale_technology == "BUILDING":
        if energy_source == "GRID":
            # sum
            tsd['E_cs'] = abs(tsd['Qcs_sys']) / efficiency_average_year
            tsd['DC_cs'] = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "NONE":
            tsd['E_cs'] = np.zeros(HOURS_IN_YEAR)
            tsd['DC_cs'] = np.zeros(HOURS_IN_YEAR)
        else:
            raise Exception('check potential error in input database of LCA infrastructure / COOLING')
    elif scale_technology == "DISTRICT":
        if energy_source == "GRID":
            tsd['DC_cs'] = tsd['Qcs_sys'] / efficiency_average_year
            tsd['E_cs'] = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "NONE":
            tsd['DC_cs'] = np.zeros(HOURS_IN_YEAR)
            tsd['E_cs'] = np.zeros(HOURS_IN_YEAR)
        else:
            raise Exception('check potential error in input database of ALL IN ONE SYSTEMS / COOLING')
    elif scale_technology == "NONE":
        tsd['DC_cs'] = np.zeros(HOURS_IN_YEAR)
        tsd['E_cs'] = np.zeros(HOURS_IN_YEAR)
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
            tsd['E_hs'] = tsd['Qhs_sys'] / efficiency_average_year
            tsd['DH_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['NG_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['COAL_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['OIL_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['WOOD_hs'] = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "NATURALGAS":
            tsd['NG_hs'] = tsd['Qhs_sys'] / efficiency_average_year
            tsd['COAL_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['OIL_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['WOOD_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['DH_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['E_hs'] = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "OIL":
            tsd['NG_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['COAL_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['OIL_hs'] = tsd['Qhs_sys'] / efficiency_average_year
            tsd['WOOD_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['DH_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['E_hs'] = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "COAL":
            tsd['NG_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['COAL_hs'] = tsd['Qhs_sys'] / efficiency_average_year
            tsd['OIL_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['WOOD_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['DH_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['E_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['SOLAR_hs'] = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "WOOD":
            tsd['NG_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['COAL_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['OIL_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['WOOD_hs'] = tsd['Qhs_sys'] / efficiency_average_year
            tsd['DH_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['E_hs'] = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "NONE":
            tsd['NG_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['COAL_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['OIL_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['WOOD_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['DH_hs'] = np.zeros(HOURS_IN_YEAR)
            tsd['E_hs'] = np.zeros(HOURS_IN_YEAR)
        else:
            raise Exception('check potential error in input database of LCA infrastructure / HEATING')
    elif scale_technology == "DISTRICT":
        tsd['NG_hs'] = np.zeros(HOURS_IN_YEAR)
        tsd['COAL_hs'] = np.zeros(HOURS_IN_YEAR)
        tsd['OIL_hs'] = np.zeros(HOURS_IN_YEAR)
        tsd['WOOD_hs'] = np.zeros(HOURS_IN_YEAR)
        tsd['DH_hs'] = tsd['Qhs_sys'] / efficiency_average_year
        tsd['E_hs'] = np.zeros(HOURS_IN_YEAR)
    elif scale_technology == "NONE":
        tsd['NG_hs'] = np.zeros(HOURS_IN_YEAR)
        tsd['COAL_hs'] = np.zeros(HOURS_IN_YEAR)
        tsd['OIL_hs'] = np.zeros(HOURS_IN_YEAR)
        tsd['WOOD_hs'] = np.zeros(HOURS_IN_YEAR)
        tsd['DH_hs'] = np.zeros(HOURS_IN_YEAR)
        tsd['E_hs'] = np.zeros(HOURS_IN_YEAR)
    else:
        raise Exception('check potential error in input database of LCA infrastructure / HEATING')
    return tsd


def calc_set_points(bpr, date, tsd, building_name, config, locator, schedules):
    # get internal comfort properties
    tsd = control_heating_cooling_systems.get_temperature_setpoints_incl_seasonality(tsd, bpr, schedules)

    t_prev = next(get_hours(bpr)) - 1
    tsd['T_int'][t_prev] = tsd['T_ext'][t_prev]
    tsd['x_int'][t_prev] = latent_loads.convert_rh_to_moisture_content(tsd['rh_ext'][t_prev], tsd['T_ext'][t_prev])
    return tsd


def calc_Qhs_Qcs(bpr: BuildingPropertiesRow, 
                 tsd: Dict[str, np.ndarray], 
                 use_dynamic_infiltration_calculation: bool, 
                 config: Configuration):
    # get ventilation flows
    ventilation_air_flows_simple.calc_m_ve_required(tsd)
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
        hourly_procedure_heating_cooling_system_load.calc_heating_cooling_loads(bpr, tsd, t, config)

        # END OF FOR LOOP
    return tsd


def initialize_schedules(bpr: BuildingPropertiesRow, 
                         tsd: Dict[str, np.ndarray],
                         locator: InputLocator,
                         ) -> Tuple[pd.DataFrame, 
                                    Dict[str, Union[np.ndarray, pd.Series]]]:
    """
    This function reads schedules, and update the timeseries data based on schedules read.
    :param bpr: a collection of building properties for the building used for thermal loads calculation
    :type bpr: BuildingPropertiesRow
    :param weather_data: data from the .epw weather file. Each row represents an hour of the year. The columns are:
        ``drybulb_C``, ``relhum_percent``, and ``windspd_ms``
    :type weather_data: pandas.DataFrame
    :param date_range: the pd.date_range of the calculation year
    :type date_range: pd.date_range
    :param locator: the input locator
    :type locator: cea.inpultlocator.InputLocator
    :returns: one dict of schedules, one dict of time step data
    :rtype: dict
    """
    # get the building name
    building_name = bpr.name

    # get occupancy file
    occupancy_yearly_schedules = pd.read_csv(locator.get_occupancy_model_file(building_name))

    tsd['people'] = occupancy_yearly_schedules['people_p']
    tsd['ve_lps'] = occupancy_yearly_schedules['Ve_lps']
    tsd['Qs'] = occupancy_yearly_schedules['Qs_W']

    return occupancy_yearly_schedules, tsd


TSD_KEYS_HEATING_LOADS = ['Qhs_sen_rc', 'Qhs_sen_shu', 'Qhs_sen_ahu', 'Qhs_lat_ahu', 'Qhs_sen_aru', 'Qhs_lat_aru',
                          'Qhs_sen_sys', 'Qhs_lat_sys', 'Qhs_em_ls', 'Qhs_dis_ls', 'Qhs_sys_shu', 'Qhs_sys_ahu',
                          'Qhs_sys_aru',
                          'DH_hs', 'Qhs', 'Qhs_sys', 'QH_sys',
                          'DH_ww', 'Qww_sys', 'Qww', 'Qhs', 'Qhpro_sys']
TSD_KEYS_COOLING_LOADS = ['Qcs_sen_rc', 'Qcs_sen_scu', 'Qcs_sen_ahu', 'Qcs_lat_ahu', 'Qcs_sen_aru', 'Qcs_lat_aru',
                          'Qcs_sen_sys', 'Qcs_lat_sys', 'Qcs_em_ls', 'Qcs_dis_ls', 'Qcs_sys_scu', 'Qcs_sys_ahu',
                          'Qcs_sys_aru',
                          'DC_cs', 'Qcs', 'Qcs_sys', 'QC_sys',
                          'DC_cre', 'Qcre_sys', 'Qcre',
                          'DC_cdata', 'Qcdata_sys', 'Qcdata', 'Qcpro_sys']
TSD_KEYS_HEATING_TEMP = ['ta_re_hs_ahu', 'ta_sup_hs_ahu', 'ta_re_hs_aru', 'ta_sup_hs_aru']
TSD_KEYS_HEATING_FLOWS = ['ma_sup_hs_ahu', 'ma_sup_hs_aru']
TSD_KEYS_COOLING_TEMP = ['ta_re_cs_ahu', 'ta_sup_cs_ahu', 'ta_re_cs_aru', 'ta_sup_cs_aru']
TSD_KEYS_COOLING_FLOWS = ['ma_sup_cs_ahu', 'ma_sup_cs_aru']
TSD_KEYS_COOLING_SUPPLY_FLOWS = ['mcpcs_sys_ahu', 'mcpcs_sys_aru', 'mcpcs_sys_scu', 'mcpcs_sys']
TSD_KEYS_COOLING_SUPPLY_TEMP = ['Tcs_sys_re_ahu', 'Tcs_sys_re_aru', 'Tcs_sys_re_scu', 'Tcs_sys_sup_ahu',
                                'Tcs_sys_sup_aru',
                                'Tcs_sys_sup_scu', 'Tcs_sys_sup', 'Tcs_sys_re',
                                'Tcdata_sys_re', 'Tcdata_sys_sup',
                                'Tcre_sys_re', 'Tcre_sys_sup']
TSD_KEYS_HEATING_SUPPLY_FLOWS = ['mcphs_sys_ahu', 'mcphs_sys_aru', 'mcphs_sys_shu', 'mcphs_sys']
TSD_KEYS_HEATING_SUPPLY_TEMP = ['Ths_sys_re_ahu', 'Ths_sys_re_aru', 'Ths_sys_re_shu', 'Ths_sys_sup_ahu',
                                'Ths_sys_sup_aru',
                                'Ths_sys_sup_shu', 'Ths_sys_sup', 'Ths_sys_re',
                                'Tww_sys_sup', 'Tww_sys_re']
TSD_KEYS_RC_TEMP = ['T_int', 'theta_m', 'theta_c', 'theta_o', 'theta_ve_mech']
TSD_KEYS_MOISTURE = ['x_int', 'x_ve_inf', 'x_ve_mech', 'g_hu_ld', 'g_dhu_ld']
TSD_KEYS_VENTILATION_FLOWS = ['m_ve_window', 'm_ve_mech', 'm_ve_rec', 'm_ve_inf', 'm_ve_required']
TSD_KEYS_ENERGY_BALANCE_DASHBOARD = ['Q_gain_sen_light', 'Q_gain_sen_app', 'Q_gain_sen_peop', 'Q_gain_sen_data',
                                     'Q_loss_sen_ref', 'Q_gain_sen_wall', 'Q_gain_sen_base', 'Q_gain_sen_roof',
                                     'Q_gain_sen_wind', 'Q_gain_sen_vent', 'Q_gain_lat_peop', 'Q_gain_sen_pro']
TSD_KEYS_SOLAR = ['I_sol', 'I_rad', 'I_sol_and_I_rad']
TSD_KEYS_PEOPLE = ['people', 've', 'Qs', 'w_int']


def initialize_timestep_data(weather_data: pd.DataFrame) -> Dict[str, np.ndarray]:
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

    nan_fields_electricity = ['Eaux', 'Eaux_hs', 'Eaux_cs', 'Eaux_ww', 'Eaux_fw', 'Ehs_lat_aux',
                              'Eve',
                              'GRID',
                              'GRID_a',
                              'GRID_l',
                              'GRID_v',
                              'GRID_ve',
                              'GRID_data',
                              'GRID_pro',
                              'GRID_aux',
                              'GRID_ww',
                              'GRID_hs',
                              'GRID_cs'
                              'GRID_cdata',
                              'GRID_cre',
                              'PV', 'Eal', 'Edata', 'Epro', 'E_sys',
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

    tsd.update(dict((x, np.zeros(HOURS_IN_YEAR) * np.nan) for x in nan_fields))

    # initialize system status log
    tsd['sys_status_ahu'] = np.chararray(HOURS_IN_YEAR, itemsize=20)
    tsd['sys_status_aru'] = np.chararray(HOURS_IN_YEAR, itemsize=20)
    tsd['sys_status_sen'] = np.chararray(HOURS_IN_YEAR, itemsize=20)
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

    zero_fields = ['Qhs_lat_sys',
                   'Qhs_sen_sys',
                   'Qcs_lat_sys',
                   'Qcs_sen_sys',
                   'Qhs_sen',
                   'Qcs_sen',
                   'x_int',
                   'Qhs_em_ls',
                   'Qcs_em_ls',
                   'Qhpro_sys',
                   'Qcpro_sys',
                   'ma_sup_hs',
                   'ma_sup_cs',
                   'Ta_sup_hs',
                   'Ta_re_hs',
                   'Ta_sup_cs',
                   'Ta_re_cs',
                   'NG_hs',
                   'COAL_hs',
                   'OIL_hs',
                   'WOOD_hs',
                   'NG_ww',
                   'COAL_ww',
                   'OIL_ww',
                   'WOOD_ww',
                   'vfw_m3perh',
                   'DH_hs',
                   'Qhs_sys', 'Qhs',
                   'DH_ww',
                   'Qww_sys',
                   'Qww',
                   'DC_cs',
                   'DC_cs_lat',
                   'Qcs_sys',
                   'Qcs',
                   'DC_cdata',
                   'Qcdata_sys',
                   'Qcdata',
                   'DC_cre',
                   'Qcre_sys',
                   'Qcre',
                   'Eaux',
                   'Ehs_lat_aux',
                   'Eaux_hs',
                   'Eaux_cs',
                   'Eaux_ve',
                   'Eaux_ww',
                   'Eaux_fw',
                   'E_sys',
                   'GRID',
                   'E_ww',
                   'E_hs',
                   'E_cs',
                   'E_cre',
                   'E_cdata',
                   'E_pro',
                   'Epro',
                   'Edata',
                   'Ea',
                   'El',
                   'Eal',
                   'Ev',
                   'Eve',
                   'mcphs_sys',
                   'mcpcs_sys',
                   'mcptw'
                   'mcpww_sys',
                   'mcpcdata_sys',
                   'mcpcre_sys',
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

    tsd.update(dict((x, np.zeros(HOURS_IN_YEAR)) for x in zero_fields))

    tsd['T_int'] = tsd['T_ext'].copy()

    return tsd


def get_hours(bpr):
    """


    :param bpr: BuildingPropertiesRow
    :type bpr:
    :return:
    """

    if bpr.hvac['has-heating-season']:
        # if has heating season start simulating at [before] start of heating season
        hour_start_simulation = control_heating_cooling_systems.convert_date_to_hour(bpr.hvac['hvac_heat_starts'])
    elif not bpr.hvac['has-heating-season'] and bpr.hvac['has-cooling-season']:
        # if has no heating season but cooling season start at [before] start of cooling season
        hour_start_simulation = control_heating_cooling_systems.convert_date_to_hour(bpr.hvac['hvac_cool_starts'])
    elif not bpr.hvac['has-heating-season'] and not bpr.hvac['has-cooling-season']:
        # no heating or cooling
        hour_start_simulation = 0

    # TODO: HOURS_PRE_CONDITIONING could be part of config in the future
    hours_simulation_total = HOURS_IN_YEAR + HOURS_PRE_CONDITIONING
    hour_start_simulation = hour_start_simulation - HOURS_PRE_CONDITIONING

    t = hour_start_simulation
    for i in range(hours_simulation_total):
        yield (t + i) % HOURS_IN_YEAR

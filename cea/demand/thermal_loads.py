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
from cea.demand.building_properties.building_solar import get_thermal_resistance_surface
from cea.demand.latent_loads import convert_rh_to_moisture_content
from cea.demand.time_series_data import TimeSeriesData, Weather
from cea.utilities import reporting
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from cea.config import Configuration
    from cea.inputlocator import InputLocator
    from cea.demand.building_properties.building_properties_row import BuildingPropertiesRow


def calc_thermal_loads(building_name: str,
                       bpr: BuildingPropertiesRow,
                       weather_data: pd.DataFrame,
                       date_range: pd.DatetimeIndex,
                       locator: InputLocator,
                       use_dynamic_infiltration_calculation: bool,
                       resolution_outputs: str,
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
        tsd.cooling_loads.DC_cre = tsd.cooling_loads.Qcre_sys = tsd.cooling_loads.Qcre = np.zeros(HOURS_IN_YEAR)
        tsd.cooling_system_mass_flows.mcpcre_sys = tsd.cooling_system_temperatures.Tcre_sys_re = tsd.cooling_system_temperatures.Tcre_sys_sup = np.zeros(HOURS_IN_YEAR)
        tsd.electrical_loads.E_cre = np.zeros(HOURS_IN_YEAR)

    # CALCULATE PROCESS HEATING
    tsd.heating_loads.Qhpro_sys = schedules['Qhpro_W'].to_numpy()  # in Wh

    # CALCULATE PROCESS COOLING
    tsd.cooling_loads.Qcpro_sys = schedules['Qcpro_W'].to_numpy()  # in Wh

    # CALCULATE DATA CENTER LOADS
    if datacenter_loads.has_data_load(bpr):
        tsd = datacenter_loads.calc_Edata(tsd, schedules)  # end-use electricity
        tsd = datacenter_loads.calc_Qcdata_sys(bpr, tsd)  # system need for cooling
        tsd = datacenter_loads.calc_Qcdataf(locator, bpr, tsd)  # final need for cooling
    else:
        tsd.cooling_loads.DC_cdata = tsd.cooling_loads.Qcdata_sys = tsd.cooling_loads.Qcdata = np.zeros(HOURS_IN_YEAR)
        tsd.cooling_system_mass_flows.mcpcdata_sys = tsd.cooling_system_temperatures.Tcdata_sys_re = tsd.cooling_system_temperatures.Tcdata_sys_sup = np.zeros(HOURS_IN_YEAR)
        tsd.electrical_loads.Edata = tsd.electrical_loads.E_cdata = np.zeros(HOURS_IN_YEAR)

    # CALCULATE SPACE CONDITIONING DEMANDS
    if np.isclose(bpr.rc_model.Af, 0.0):  # if building does not have conditioned area
        tsd.rc_model_temperatures.T_int = tsd.weather.T_ext
        tsd.moisture.x_int = np.vectorize(convert_rh_to_moisture_content)(tsd.weather.rh_ext, tsd.rc_model_temperatures.T_int)
        tsd.electrical_loads.E_cs = tsd.electrical_loads.E_hs = np.zeros(HOURS_IN_YEAR)
        tsd.electrical_loads.Eaux_cs = tsd.electrical_loads.Eaux_hs = tsd.electrical_loads.Ehs_lat_aux = np.zeros(HOURS_IN_YEAR)
        print(f"building {bpr.name} does not have an air-conditioned area")
    else:
        # get hourly thermal resistances of external surfaces
        tsd.thermal_resistance.RSE_wall, \
        tsd.thermal_resistance.RSE_roof, \
        tsd.thermal_resistance.RSE_win, \
        tsd.thermal_resistance.RSE_underside = get_thermal_resistance_surface(bpr.envelope, weather_data)
        # calculate heat gains
        tsd = latent_loads.calc_Qgain_lat(tsd, schedules['X_gh'].to_numpy())
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
        tsd.cooling_loads.Qcs_lat_sys = np.abs(tsd.cooling_loads.Qcs_lat_sys)
        tsd.cooling_loads.DC_cs = np.abs(tsd.cooling_loads.DC_cs)
        tsd.cooling_loads.Qcs_sys = np.abs(tsd.cooling_loads.Qcs_sys)
        tsd.cooling_loads.Qcre_sys = np.abs(tsd.cooling_loads.Qcre_sys)  # inverting sign of cooling loads for reporting and graphs
        tsd.cooling_loads.Qcdata_sys = np.abs(tsd.cooling_loads.Qcdata_sys)  # inverting sign of cooling loads for reporting and graphs

    # CALCULATE HOT WATER LOADS
    if hotwater_loads.has_hot_water_technical_system(bpr):
        tsd = electrical_loads.calc_Eaux_fw(tsd, bpr, schedules)
        tsd = hotwater_loads.calc_Qww(bpr, tsd, schedules)  # end-use
        tsd = hotwater_loads.calc_Qww_sys(bpr, tsd)  # system (incl. losses)
        tsd = electrical_loads.calc_Eaux_ww(tsd, bpr)  # calc auxiliary loads
        tsd = hotwater_loads.calc_Qwwf(bpr, tsd)  # final
    else:
        tsd = electrical_loads.calc_Eaux_fw(tsd, bpr, schedules)
        tsd.heating_loads.Qww = tsd.heating_loads.DH_ww = tsd.heating_loads.Qww_sys = np.zeros(HOURS_IN_YEAR)
        tsd.heating_system_mass_flows.mcpww_sys = tsd.heating_system_temperatures.Tww_sys_re = tsd.heating_system_temperatures.Tww_sys_sup = np.zeros(HOURS_IN_YEAR)
        tsd.electrical_loads.Eaux_ww = np.zeros(HOURS_IN_YEAR)
        tsd.fuel_source.NG_ww = tsd.fuel_source.COAL_ww = tsd.fuel_source.OIL_ww = tsd.fuel_source.WOOD_ww = np.zeros(HOURS_IN_YEAR)
        tsd.electrical_loads.E_ww = np.zeros(HOURS_IN_YEAR)

    # CALCULATE SUM OF HEATING AND COOLING LOADS
    tsd = calc_QH_sys_QC_sys(tsd)  # aggregated cooling and heating loads

    # CALCULATE ELECTRICITY LOADS PART 2/2 AUXILIARY LOADS + ENERGY GENERATION
    tsd = electrical_loads.calc_Eaux(tsd)  # auxiliary totals
    tsd = electrical_loads.calc_E_sys(tsd)  # system (incl. losses)
    tsd = electrical_loads.calc_Ef(bpr, tsd)  # final (incl. self. generated)

    # WRITE SOLAR RESULTS
    write_results(bpr, building_name, date_range, locator, resolution_outputs, tsd, debug)

    return


def calc_QH_sys_QC_sys(tsd: TimeSeriesData) -> TimeSeriesData:
    tsd.heating_loads.QH_sys = tsd.heating_loads.Qww_sys + tsd.heating_loads.Qhs_sys + tsd.heating_loads.Qhpro_sys
    tsd.cooling_loads.QC_sys = tsd.cooling_loads.Qcs_sys + tsd.cooling_loads.Qcdata_sys + tsd.cooling_loads.Qcre_sys + tsd.cooling_loads.Qcpro_sys

    return tsd


def write_results(bpr: BuildingPropertiesRow, building_name, date, locator, resolution_outputs, tsd: TimeSeriesData, debug):
    if resolution_outputs == 'hourly':
        writer = demand_writers.HourlyDemandWriter()
    elif resolution_outputs == 'monthly':
        writer = demand_writers.MonthlyDemandWriter()
    else:
        raise Exception('error')

    if debug:
        print('Creating instant plotly visualizations of demand variable time series.')
        print('Behavior can be changed in cea.utilities.reporting code.')
        print('Writing detailed demand results of {} to .xls file.'.format(building_name))
        tsd_df = reporting.calc_full_hourly_dataframe(tsd, date)
        reporting.quick_visualization_tsd(tsd_df, locator.get_demand_results_folder(), building_name)
        reporting.full_report_to_xls(tsd_df, locator.get_demand_results_folder(), building_name)

    writer.results_to_csv(tsd, bpr, locator, date, building_name)


def calc_Qcs_sys(bpr: BuildingPropertiesRow, tsd: TimeSeriesData) -> TimeSeriesData:
    # GET SYSTEMS EFFICIENCIES
    energy_source = bpr.supply['source_cs']
    scale_technology = bpr.supply['scale_cs']
    efficiency_average_year = bpr.supply['eff_cs']
    if scale_technology == "BUILDING":
        if energy_source == "GRID":
            # sum
            tsd.electrical_loads.E_cs = abs(tsd.cooling_loads.Qcs_sys) / efficiency_average_year
            tsd.cooling_loads.DC_cs = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "NONE":
            tsd.electrical_loads.E_cs = np.zeros(HOURS_IN_YEAR)
            tsd.cooling_loads.DC_cs = np.zeros(HOURS_IN_YEAR)
        else:
            raise Exception('check potential error in input database of LCA infrastructure / COOLING')
    elif scale_technology == "DISTRICT":
        if energy_source == "GRID":
            tsd.cooling_loads.DC_cs = tsd.cooling_loads.Qcs_sys / efficiency_average_year
            tsd.electrical_loads.E_cs = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "NONE":
            tsd.cooling_loads.DC_cs = np.zeros(HOURS_IN_YEAR)
            tsd.electrical_loads.E_cs = np.zeros(HOURS_IN_YEAR)
        else:
            raise Exception('check potential error in input database of ALL IN ONE SYSTEMS / COOLING')
    elif scale_technology == "NONE":
        tsd.cooling_loads.DC_cs = np.zeros(HOURS_IN_YEAR)
        tsd.electrical_loads.E_cs = np.zeros(HOURS_IN_YEAR)
    else:
        raise Exception('check potential error in input database of LCA infrastructure / COOLING')
    return tsd


def calc_Qhs_sys(bpr: BuildingPropertiesRow, tsd: TimeSeriesData) -> TimeSeriesData:
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
            tsd.electrical_loads.E_hs = tsd.heating_loads.Qhs_sys / efficiency_average_year
            tsd.heating_loads.DH_hs = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.NG_hs = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.COAL_hs = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.OIL_hs = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.WOOD_hs = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "NATURALGAS":
            tsd.fuel_source.NG_hs = tsd.heating_loads.Qhs_sys / efficiency_average_year
            tsd.fuel_source.COAL_hs = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.OIL_hs = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.WOOD_hs = np.zeros(HOURS_IN_YEAR)
            tsd.heating_loads.DH_hs = np.zeros(HOURS_IN_YEAR)
            tsd.electrical_loads.E_hs = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "OIL":
            tsd.fuel_source.NG_hs = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.COAL_hs = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.OIL_hs = tsd.heating_loads.Qhs_sys / efficiency_average_year
            tsd.fuel_source.WOOD_hs = np.zeros(HOURS_IN_YEAR)
            tsd.heating_loads.DH_hs = np.zeros(HOURS_IN_YEAR)
            tsd.electrical_loads.E_hs = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "COAL":
            tsd.fuel_source.NG_hs = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.COAL_hs = tsd.heating_loads.Qhs_sys / efficiency_average_year
            tsd.fuel_source.OIL_hs = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.WOOD_hs = np.zeros(HOURS_IN_YEAR)
            tsd.heating_loads.DH_hs = np.zeros(HOURS_IN_YEAR)
            tsd.electrical_loads.E_hs = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.SOLAR_hs = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "WOOD":
            tsd.fuel_source.NG_hs = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.COAL_hs = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.OIL_hs = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.WOOD_hs = tsd.heating_loads.Qhs_sys / efficiency_average_year
            tsd.heating_loads.DH_hs = np.zeros(HOURS_IN_YEAR)
            tsd.electrical_loads.E_hs = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "NONE":
            tsd.fuel_source.NG_hs = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.COAL_hs = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.OIL_hs = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.WOOD_hs = np.zeros(HOURS_IN_YEAR)
            tsd.heating_loads.DH_hs = np.zeros(HOURS_IN_YEAR)
            tsd.electrical_loads.E_hs = np.zeros(HOURS_IN_YEAR)
        else:
            raise Exception('check potential error in input database of LCA infrastructure / HEATING')
    elif scale_technology == "DISTRICT":
        tsd.fuel_source.NG_hs = np.zeros(HOURS_IN_YEAR)
        tsd.fuel_source.COAL_hs = np.zeros(HOURS_IN_YEAR)
        tsd.fuel_source.OIL_hs = np.zeros(HOURS_IN_YEAR)
        tsd.fuel_source.WOOD_hs = np.zeros(HOURS_IN_YEAR)
        tsd.heating_loads.DH_hs = tsd.heating_loads.Qhs_sys / efficiency_average_year
        tsd.electrical_loads.E_hs = np.zeros(HOURS_IN_YEAR)
    elif scale_technology == "NONE":
        tsd.fuel_source.NG_hs = np.zeros(HOURS_IN_YEAR)
        tsd.fuel_source.COAL_hs = np.zeros(HOURS_IN_YEAR)
        tsd.fuel_source.OIL_hs = np.zeros(HOURS_IN_YEAR)
        tsd.fuel_source.WOOD_hs = np.zeros(HOURS_IN_YEAR)
        tsd.heating_loads.DH_hs = np.zeros(HOURS_IN_YEAR)
        tsd.electrical_loads.E_hs = np.zeros(HOURS_IN_YEAR)
    else:
        raise Exception('check potential error in input database of LCA infrastructure / HEATING')
    return tsd


def calc_set_points(bpr: BuildingPropertiesRow, date, tsd: TimeSeriesData, building_name, config, locator, schedules):
    # get internal comfort properties
    tsd = control_heating_cooling_systems.get_temperature_setpoints_incl_seasonality(tsd, bpr, schedules)

    t_prev = next(get_hours(bpr)) - 1
    tsd.rc_model_temperatures.T_int[t_prev] = tsd.weather.T_ext[t_prev]
    tsd.moisture.x_int[t_prev] = latent_loads.convert_rh_to_moisture_content(tsd.weather.rh_ext[t_prev], tsd.weather.T_ext[t_prev])
    return tsd


def calc_Qhs_Qcs(bpr: BuildingPropertiesRow,
                 tsd: TimeSeriesData,
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
                tsd.rc_model_temperatures.T_int[t - 1], tsd.weather.u_wind[t], tsd.weather.T_ext[t], dict_props_nat_vent)
            # INFILTRATION IS FORCED NOT TO REACH ZERO IN ORDER TO AVOID THE RC MODEL TO FAIL
            tsd.ventilation_mass_flows.m_ve_inf[t] = max(qm_sum_in / 3600, 1 / 3600)

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
                         tsd: TimeSeriesData,
                         locator: InputLocator,
                         ) -> Tuple[pd.DataFrame, TimeSeriesData]:
    """
    This function reads schedules, and update the timeseries data based on schedules read.
    :param bpr: a collection of building properties for the building used for thermal loads calculation
    :type bpr: BuildingPropertiesRow
    :param tsd: time series data object to be updated with schedules
    :type tsd: TimeSeriesData
    :param locator: the input locator
    :type locator: cea.inputlocator.InputLocator
    :returns: one dict of schedules, one dict of time step data
    :rtype: dict
    """
    # get the building name
    building_name = bpr.name

    # get occupancy file
    occupancy_yearly_schedules = pd.read_csv(locator.get_occupancy_model_file(building_name))

    tsd.occupancy.people = occupancy_yearly_schedules['people_p'].to_numpy()
    tsd.occupancy.ve_lps = occupancy_yearly_schedules['Ve_lps'].to_numpy()
    tsd.occupancy.Qs = occupancy_yearly_schedules['Qs_W'].to_numpy()

    return occupancy_yearly_schedules, tsd


def initialize_timestep_data(weather_data: pd.DataFrame) -> TimeSeriesData:
    """
    initializes the time step data with the weather data and the minimum set of variables needed for computation.

    :param weather_data: data from the .epw weather file. Each row represents an hour of the year. The columns are:
        ``drybulb_C``, ``relhum_percent``, and ``windspd_ms``
    :type weather_data: pandas.DataFrame

    :return: returns the `tsd` variable, a dictionary of time step data mapping variable names to ndarrays for each hour of the year.
    :rtype: dict
    """

    # Initialize dict with weather variables
    weather = Weather(
        T_ext=weather_data.drybulb_C.values,
        T_ext_wetbulb=weather_data.wetbulb_C.values,
        rh_ext=weather_data.relhum_percent.values,
        T_sky=weather_data.skytemp_C.values,
        u_wind=weather_data.windspd_ms.values
    )
    tsd = TimeSeriesData(weather)

    return tsd


def get_hours(bpr: BuildingPropertiesRow):
    """
    :param bpr: BuildingPropertiesRow
    :type bpr:
    :return:
    """

    if bpr.hvac['has-heating-season']:
        # if has heating season start simulating at [before] start of heating season
        hour_start_simulation = control_heating_cooling_systems.convert_date_to_hour(bpr.hvac['hvac_heat_starts'])
    elif bpr.hvac['has-cooling-season']:
        # if has no heating season but cooling season start at [before] start of cooling season
        hour_start_simulation = control_heating_cooling_systems.convert_date_to_hour(bpr.hvac['hvac_cool_starts'])
    else:
        # no heating or cooling
        hour_start_simulation = 0

    # TODO: HOURS_PRE_CONDITIONING could be part of config in the future
    hours_simulation_total = HOURS_IN_YEAR + HOURS_PRE_CONDITIONING
    hour_start_simulation = hour_start_simulation - HOURS_PRE_CONDITIONING

    t = hour_start_simulation
    for i in range(hours_simulation_total):
        yield (t + i) % HOURS_IN_YEAR

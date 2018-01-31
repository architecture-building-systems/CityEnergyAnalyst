# coding=utf-8
"""
Analytical energy demand model algorithm
"""
from __future__ import division

import multiprocessing as mp
import os

import pandas as pd
import time

import cea.globalvar
import cea.inputlocator
import cea.config
from cea.demand import occupancy_model
from cea.demand import thermal_loads
from cea.demand.building_properties import BuildingProperties
import demand_writers
from cea.utilities import epwreader

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas", "Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def demand_calculation(locator, gv, config):
    """
    Algorithm to calculate the hourly demand of energy services in buildings
    using the integrated model of [Fonseca2015]_.

    Produces a demand file per building and a total demand file for the whole zone of interest:
      - a csv file for every building with hourly demand data.
      - ``Total_demand.csv``, csv file of yearly demand data per building.


    :param locator: An InputLocator to locate input files
    :type locator: cea.inputlocator.InputLocator

    :param weather_path: A path to the EnergyPlus weather data file (.epw)
    :type weather_path: str

    :param gv: global variables
    :type gv: cea.globalvar.GlobalVariables

    :param use_dynamic_infiltration_calculation: Set this to ``True`` if the (slower) dynamic infiltration
        calculation method (:py:func:`cea.demand.ventilation_air_flows_detailed.calc_air_flows`) should be used instead
        of the standard.
    :type use_dynamic_infiltration_calculation: bool

    :param multiprocessing: Set this to ``True`` if the :py:mod:`multiprocessing` module should be used to speed up
        calculations by making use of multiple cores.
    :type multiprocessing: bool

    :returns: None
    :rtype: NoneType

    .. [Fonseca2015] Fonseca, Jimeno A., and Arno Schlueter. “Integrated Model for Characterization of
        Spatiotemporal Building Energy Consumption Patterns in Neighborhoods and City Districts.”
        Applied Energy 142 (2015): 247–265.
    """

    # INITIALIZE TIMER
    t0 = time.clock()

    # LOCAL VARIABLES
    multiprocessing = config.multiprocessing
    region = config.region
    list_building_names = config.demand.buildings
    use_dynamic_infiltration = config.demand.use_dynamic_infiltration_calculation
    use_daysim_radiation = config.demand.use_daysim_radiation
    resolution_output = config.demand.resolution_output
    loads_output = config.demand.loads_output
    massflows_output = config.demand.massflows_output
    temperatures_output = config.demand.temperatures_output
    format_output = config.demand.format_output
    override_variables = config.demand.override_variables
    weather_data = epwreader.epw_reader(config.weather)[['year','drybulb_C', 'wetbulb_C',
                                                         'relhum_percent', 'windspd_ms', 'skytemp_C']]
    year = weather_data['year'][0]

    # CALCULATE OBJECT WITH PROPERTIES OF ALL BUILDINGS
    building_properties, schedules_dict, date = properties_and_schedule(gv, locator, region, year, use_daysim_radiation,
                                                                        override_variables)

    # SPECIFY NUMBER OF BUILDINGS TO SIMULATE
    if not list_building_names:
        list_building_names = building_properties.list_building_names()
        print('Running demand calculation for all buildings in the zone')
    else:
        print('Running demand calculation for the next buildings=%s' % list_building_names)

    # DEMAND CALCULATION
    if multiprocessing and mp.cpu_count() > 1:
        print("Using %i CPU's" % mp.cpu_count())
        calc_demand_multiprocessing(building_properties, date, gv, locator, list_building_names,
                                    schedules_dict, weather_data, use_dynamic_infiltration,
                                    resolution_output, loads_output, massflows_output, temperatures_output,
                                    format_output)
    else:
        calc_demand_singleprocessing(building_properties, date, gv, locator, list_building_names, schedules_dict,
                                     weather_data, use_dynamic_infiltration,
                                     resolution_output, loads_output, massflows_output, temperatures_output,
                                     format_output)

    # WRITE TOTAL YEARLY VALUES
    writer_totals = demand_writers.YearlyDemandWriter(loads_output, massflows_output, temperatures_output)
    if format_output == 'csv':
        totals, time_series = writer_totals.write_to_csv(list_building_names, locator)
    elif format_output == 'hdf5':
        totals, time_series = writer_totals.write_to_hdf5(list_building_names, locator)
    else:
        raise Exception('error')

    return totals, time_series

    time_elapsed = time.clock() - t0
    print('done - time elapsed: %d.2f seconds' % time_elapsed)


def properties_and_schedule(gv, locator, region, year, use_daysim_radiation, override_variables=False):
    # this script is called from the Neural network please do not mess with it!

    date = pd.date_range(str(year) + '/01/01', periods=8760, freq='H')
    # building properties model

    building_properties = BuildingProperties(locator, gv, use_daysim_radiation, region, override_variables)

    # schedules model
    list_uses = list(building_properties._prop_occupancy.columns)
    archetype_schedules, archetype_values = occupancy_model.schedule_maker(region, date, locator, list_uses)

    schedules_dict = {'list_uses': list_uses, 'archetype_schedules': archetype_schedules, 'occupancy_densities':
        archetype_values['people'], 'archetype_values': archetype_values}
    return building_properties, schedules_dict, date


def calc_demand_singleprocessing(building_properties, date, gv, locator, list_building_names, usage_schedules,
                                 weather_data, use_dynamic_infiltration_calculation,
                                 resolution_outputs, loads_output, massflows_output, temperatures_output,
                                 format_output):
    num_buildings = len(list_building_names)
    for i, building in enumerate(list_building_names):
        bpr = building_properties[building]
        thermal_loads.calc_thermal_loads(building, bpr, weather_data, usage_schedules, date, gv, locator,
                                         use_dynamic_infiltration_calculation,
                                         resolution_outputs, loads_output, massflows_output, temperatures_output,
                                         format_output)
        print('Building No. %i completed out of %i: %s' % (i + 1, num_buildings, building))


def calc_demand_multiprocessing(building_properties, date, gv, locator, list_building_names,
                                usage_schedules,
                                weather_data, use_dynamic_infiltration_calculation,
                                resolution_outputs, loads_output, massflows_output, temperatures_output,
                                format_output):
    pool = mp.Pool()
    joblist = []
    num_buildings = len(list_building_names)
    for building in list_building_names:
        bpr = building_properties[building]
        job = pool.apply_async(thermal_loads.calc_thermal_loads,
                               [building, bpr, weather_data, usage_schedules, date, gv, locator,
                                use_dynamic_infiltration_calculation,
                                resolution_outputs, loads_output, massflows_output, temperatures_output,
                                format_output])
        joblist.append(job)
    for i, job in enumerate(joblist):
        job.get(240)
        print('Building No. %i completed out of %i' % (i + 1, num_buildings))
    pool.close()


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    print('Running demand calculation for scenario %s' % config.scenario)
    print('Running demand calculation with weather file %s' % config.weather)
    print('Running demand calculation for region %s' % config.region)
    print('Running demand calculation with dynamic infiltration=%s' %
          config.demand.use_dynamic_infiltration_calculation)
    print('Running demand calculation with multiprocessing=%s' % config.multiprocessing)
    print('Running demand calculation with daysim radiation=%s' % config.demand.use_daysim_radiation)

    if not radiation_files_exist(config, locator):
        raise ValueError("Missing radiation data in scenario. Consider running radiation script first.")

    demand_calculation(locator=locator, gv=cea.globalvar.GlobalVariables(), config=config)


def radiation_files_exist(config, locator):
    # verify that the necessary radiation files exist
    def daysim_results_exist(building_name):
        return os.path.exists(locator.get_radiation_metadata(building_name)) and os.path.exists(locator.get_radiation_building(building_name))

    if config.demand.use_daysim_radiation:
        return all(daysim_results_exist(building_name) for building_name in locator.get_zone_building_names())
    else:
        return os.path.exists(locator.get_radiation()) and os.path.exists(locator.get_surface_properties())


if __name__ == '__main__':
    main(cea.config.Configuration())

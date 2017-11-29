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
from cea.demand.thermal_loads import BuildingProperties
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


def demand_calculation(locator, list_building_names, weather_path, gv, use_dynamic_infiltration_calculation=False,
                       multiprocessing=False):
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
    if not os.path.exists(locator.get_radiation()) or not os.path.exists(locator.get_surface_properties()):
        raise ValueError("No radiation file found in scenario. Consider running radiation script first.")

    t0 = time.clock()

    # weather model
    weather_data = epwreader.epw_reader(weather_path)[
        ['drybulb_C', 'wetbulb_C', 'relhum_percent', 'windspd_ms', 'skytemp_C']]

    building_properties, schedules_dict, date = properties_and_schedule(gv, locator)

    # in case gv passes a list of specific buildings to simulate.
    if not list_building_names:
        list_building_names = building_properties.list_building_names()
        print('Running demand calculation for all buildings in the zone')
    else:
        print('Running demand calculation for the next buildings=%s' % list_building_names)

    # demand
    if multiprocessing and mp.cpu_count() > 1:
        print("Using %i CPU's" % mp.cpu_count())
        calc_demand_multiprocessing(building_properties, date, gv, locator, list_building_names,
                                    schedules_dict, weather_data, use_dynamic_infiltration_calculation)
    else:
        calc_demand_singleprocessing(building_properties, date, gv, locator, list_building_names, schedules_dict,
                                     weather_data, use_dynamic_infiltration_calculation)

    # write yearly totals
    config = cea.config.Configuration()
    writer = demand_writers.YearlyDemandWriter(config.demand.loads, config.demand.massflows, config.demand.temperatures)
    if config.demand.format_output == 'csv':
        totals, time_series = writer.write_to_csv(list_building_names, locator)
    elif config.demand.format_output == 'hdf5':
        totals, time_series = writer.write_to_hdf5(list_building_names, locator)
    else:
        raise

    return totals, time_series

    gv.log('done - time elapsed: %(time_elapsed).2f seconds', time_elapsed=time.clock() - t0)


def properties_and_schedule(gv, locator):
    # this script is called from the Neural network please do not mess with it!

    date = pd.date_range(gv.date_start, periods=8760, freq='H')
    # building properties model
    building_properties = BuildingProperties(locator, gv)
    # schedules model
    list_uses = list(building_properties._prop_occupancy.drop('PFloor', axis=1).columns)
    archetype_schedules, archetype_values = occupancy_model.schedule_maker(gv.config.region, date, locator, list_uses)

    schedules_dict = {'list_uses': list_uses, 'archetype_schedules': archetype_schedules, 'occupancy_densities':
        archetype_values['people'], 'archetype_values': archetype_values}
    return building_properties, schedules_dict, date


def calc_demand_singleprocessing(building_properties, date, gv, locator, list_building_names, usage_schedules,
                                 weather_data, use_dynamic_infiltration_calculation):
    num_buildings = len(list_building_names)
    for i, building in enumerate(list_building_names):
        bpr = building_properties[building]
        thermal_loads.calc_thermal_loads(building, bpr, weather_data, usage_schedules, date, gv, locator,
                                         use_dynamic_infiltration_calculation)
        print('Building No. %i completed out of %i: %s' % (i + 1, num_buildings, building))


def calc_demand_multiprocessing(building_properties, date, gv, locator, list_building_names,
                                usage_schedules,
                                weather_data, use_dynamic_infiltration_calculation):
    pool = mp.Pool()
    joblist = []
    num_buildings = len(list_building_names)
    for building in list_building_names:
        bpr = building_properties[building]
        job = pool.apply_async(thermal_loads.calc_thermal_loads,
                               [building, bpr, weather_data, usage_schedules, date, gv, locator,
                                use_dynamic_infiltration_calculation])
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
    print('Running demand calculation for year %i' % config.demand.year)
    print(
    'Running demand calculation with dynamic infiltration=%s' % config.demand.use_dynamic_infiltration_calculation)
    print('Running demand calculation with multiprocessing=%s' % config.multiprocessing)

    demand_calculation(locator=locator, list_building_names=config.demand.buildings, weather_path=config.weather,
                       gv=cea.globalvar.GlobalVariables(),
                       use_dynamic_infiltration_calculation=config.demand.use_dynamic_infiltration_calculation,
                       multiprocessing=config.multiprocessing)


if __name__ == '__main__':
    main(cea.config.Configuration())

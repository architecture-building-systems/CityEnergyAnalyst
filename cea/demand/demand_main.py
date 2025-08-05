"""
Analytical energy demand model algorithm
"""

import os
import time
from itertools import repeat

import cea.config
import cea.inputlocator
import cea.utilities.parallel
from cea import MissingInputDataException
from cea.demand import thermal_loads
from cea.demand.building_properties import BuildingProperties
from cea.utilities import epwreader
from cea.utilities.date import get_date_range_hours_from_year
from cea.demand import demand_writers
from cea.datamanagement.void_deck_migrator import migrate_void_deck_data


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas", "Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def demand_calculation(locator, config):
    """
    Algorithm to calculate the hourly demand of energy services in buildings
    using the integrated model of [Fonseca2015]_.

    Produces a demand file per building and a total demand file for the whole zone of interest:
      - a csv file for every building with hourly demand data.
      - ``Total_demand.csv``, csv file of yearly demand data per building.


    :param locator: An InputLocator to locate input files
    :type locator: cea.inputlocator.InputLocator

    :returns: None
    :rtype: NoneType

    .. [Fonseca2015] Fonseca, Jimeno A., and Arno Schlueter. “Integrated Model for Characterization of
        Spatiotemporal Building Energy Consumption Patterns in Neighborhoods and City Districts.”
        Applied Energy 142 (2015): 247–265.
    """
    migrate_void_deck_data(locator)
    # INITIALIZE TIMER
    t0 = time.perf_counter()

    # LOCAL VARIABLES
    building_names = config.demand.buildings
    use_dynamic_infiltration = config.demand.use_dynamic_infiltration_calculation
    resolution_output = config.demand.resolution_output
    loads_output = config.demand.loads_output
    massflows_output = config.demand.massflows_output
    temperatures_output = config.demand.temperatures_output
    debug = config.debug
    weather_path = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_path)[['year', 'drybulb_C', 'wetbulb_C',
                                                       'relhum_percent', 'windspd_ms', 'skytemp_C']]
    year = weather_data['year'][0]
    # create date range for the calculation year
    date_range = get_date_range_hours_from_year(year)

    # SPECIFY NUMBER OF BUILDINGS TO SIMULATE
    print('Running demand calculation for the following buildings=%s' % building_names)

    # CALCULATE OBJECT WITH PROPERTIES OF ALL BUILDINGS
    building_properties = BuildingProperties(locator, weather_data, building_names)
    building_properties.check_buildings()

    # DEMAND CALCULATION
    n = len(building_names)
    calc_thermal_loads = cea.utilities.parallel.vectorize(thermal_loads.calc_thermal_loads,
                                                          config.get_number_of_processes(), on_complete=print_progress)

    calc_thermal_loads(
        building_names,
        [building_properties[b] for b in building_names],
        repeat(weather_data, n),
        repeat(date_range, n),
        repeat(locator, n),
        repeat(use_dynamic_infiltration, n),
        repeat(resolution_output, n),
        repeat(loads_output, n),
        repeat(massflows_output, n),
        repeat(temperatures_output, n),
        repeat(config, n),
        repeat(debug, n))

    # WRITE TOTAL YEARLY VALUES
    demand_writers.YearlyDemandWriter.write_aggregate_buildings(locator, building_names)
    demand_writers.YearlyDemandWriter.write_aggregate_hourly(locator, building_names)
    time_elapsed = time.perf_counter() - t0
    print('done - time elapsed: %d.2 seconds' % time_elapsed)


def print_progress(i, n, args, _):
    print("Building No. {i} completed out of {n}: {building}".format(i=i + 1, n=n, building=args[0]))


def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    print('Running demand calculation for scenario %s' % config.scenario)
    print('Running demand calculation with dynamic infiltration=%s' %
          config.demand.use_dynamic_infiltration_calculation)
    print('Running demand calculation with multiprocessing=%s' % config.multiprocessing)
    if config.debug:
        print('Running demand in debug mode: Instant visualization of tsd activated.')
        print('Running demand calculation with write detailed output')

    if not radiation_files_exist(locator, config):
        raise MissingInputDataException("Missing radiation data in scenario. Consider running radiation script first.")

    demand_calculation(locator=locator, config=config)


def radiation_files_exist(locator, config):
    # verify that the necessary radiation files exist
    def daysim_results_exist(building_name):
        return os.path.exists(locator.get_radiation_building(building_name))

    building_names = config.demand.buildings

    return all(daysim_results_exist(building_name) for building_name in building_names)


if __name__ == '__main__':
    main(cea.config.Configuration())

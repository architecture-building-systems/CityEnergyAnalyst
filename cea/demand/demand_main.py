# coding=utf-8
"""
Analytical energy demand model algorithm
"""
from __future__ import division

import os
import time
import warnings
from itertools import repeat

import cea.config
import cea.inputlocator
import cea.utilities.parallel
import demand_writers
from cea.demand import thermal_loads
from cea.demand.building_properties import BuildingProperties
from cea.utilities import epwreader
from cea.utilities.date import get_dates_from_year

warnings.filterwarnings("ignore")

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

    :param weather_path: A path to the EnergyPlus weather data file (.epw)
    :type weather_path: str

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
    building_names = config.demand.buildings
    use_dynamic_infiltration = config.demand.use_dynamic_infiltration_calculation
    resolution_output = config.demand.resolution_output
    loads_output = config.demand.loads_output
    massflows_output = config.demand.massflows_output
    temperatures_output = config.demand.temperatures_output
    override_variables = config.demand.override_variables
    debug = config.debug
    weather_path = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_path)[['year', 'drybulb_C', 'wetbulb_C',
                                                       'relhum_percent', 'windspd_ms', 'skytemp_C']]
    year = weather_data['year'][0]
    # create date range for the calculation year
    date_range = get_dates_from_year(year)

    # CALCULATE OBJECT WITH PROPERTIES OF ALL BUILDINGS
    building_properties = BuildingProperties(locator, override_variables)

    # add a message i2065 of warning. This needs a more elegant solution
    def calc_buildings_less_100m2(building_properties):
        footprint = building_properties._prop_geometry.footprint
        floors = building_properties._prop_geometry.floors_ag
        names = building_properties._prop_geometry.index
        GFA_m2 = [x * y for x, y in zip(footprint, floors)]
        list_buildings_less_100m2 = []
        for name, gfa in zip(names, GFA_m2):
            if gfa < 100.0:
                list_buildings_less_100m2.append(name)
        return list_buildings_less_100m2

    list_buildings_less_100m2 = calc_buildings_less_100m2(building_properties)
    if list_buildings_less_100m2 != []:
        print('Warning! The following list of buildings have less than 100 m2 of gross floor area, CEA might fail: %s' % list_buildings_less_100m2)

    # SPECIFY NUMBER OF BUILDINGS TO SIMULATE
    if not building_names:
        building_names = locator.get_zone_building_names()
        print('Running demand calculation for all buildings in the zone')
    else:
        print('Running demand calculation for the following buildings=%s' % building_names)

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
    writer_totals = demand_writers.YearlyDemandWriter(loads_output, massflows_output, temperatures_output)
    totals, time_series = writer_totals.write_to_csv(building_names, locator)
    time_elapsed = time.clock() - t0
    print('done - time elapsed: %d.2 seconds' % time_elapsed)

    return totals, time_series


def print_progress(i, n, args, result):
    print("Building No. {i} completed out of {n}: {building}".format(i=i + 1, n=n, building=args[0]))


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    print('Running demand calculation for scenario %s' % config.scenario)
    print('Running demand calculation with dynamic infiltration=%s' %
          config.demand.use_dynamic_infiltration_calculation)
    print('Running demand calculation with multiprocessing=%s' % config.multiprocessing)
    if config.debug:
        print('Running demand in debug mode: Instant visulaization of tsd activated.')
        print('Running demand calculation with write detailed output')

    if not radiation_files_exist(config, locator):
        raise ValueError("Missing radiation data in scenario. Consider running radiation script first.")

    demand_calculation(locator=locator, config=config)


def radiation_files_exist(config, locator):
    # verify that the necessary radiation files exist
    def daysim_results_exist(building_name):
        return os.path.exists(locator.get_radiation_metadata(building_name)) and os.path.exists(
            locator.get_radiation_building_sensors(building_name))

    return all(daysim_results_exist(building_name) for building_name in locator.get_zone_building_names())


if __name__ == '__main__':
    main(cea.config.Configuration())

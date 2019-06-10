# coding=utf-8
"""
Analytical energy demand model algorithm
"""
from __future__ import division

import multiprocessing as mp
import os
import time

import pandas as pd

import cea.config
import cea.globalvar
import cea.inputlocator
import demand_writers
from cea.demand import occupancy_model
from cea.demand import thermal_loads
from cea.demand.building_properties import BuildingProperties, save_bpr_to_disc, load_bpr_from_disc
from cea.utilities import epwreader
import warnings
from cea.constants import HOURS_IN_YEAR

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
    multiprocessing = config.multiprocessing
    list_building_names = config.demand.buildings
    use_dynamic_infiltration = config.demand.use_dynamic_infiltration_calculation
    use_stochastic_occupancy = config.demand.use_stochastic_occupancy
    resolution_output = config.demand.resolution_output
    loads_output = config.demand.loads_output
    massflows_output = config.demand.massflows_output
    temperatures_output = config.demand.temperatures_output
    format_output = config.demand.format_output
    write_detailed_output = config.demand.write_detailed_output
    debug = config.debug
    weather_data = epwreader.epw_reader(config.weather)[['year', 'drybulb_C', 'wetbulb_C',
                                                         'relhum_percent', 'windspd_ms', 'skytemp_C']]

    year = weather_data['year'][0]
    date = pd.date_range(str(year) + '/01/01', periods=HOURS_IN_YEAR, freq='H')

    # SPECIFY NUMBER OF BUILDINGS TO SIMULATE
    if not list_building_names:
        list_building_names = locator.get_zone_building_names()
        print('Running demand calculation for all buildings in the zone')
    else:
        print('Running demand calculation for the next buildings=%s' % list_building_names)

    # DEMAND CALCULATION
    if multiprocessing and mp.cpu_count() > 1:
        calc_demand_multiprocessing(date, locator, list_building_names,
                                    weather_data, use_dynamic_infiltration, use_stochastic_occupancy,
                                    resolution_output, loads_output, massflows_output, temperatures_output,
                                    format_output, config, write_detailed_output, debug)
    else:
        calc_demand_singleprocessing(date, locator, list_building_names,
                                     weather_data, use_dynamic_infiltration, use_stochastic_occupancy,
                                     resolution_output, loads_output, massflows_output, temperatures_output,
                                     format_output, config, write_detailed_output, debug)

    # WRITE TOTAL YEARLY VALUES
    writer_totals = demand_writers.YearlyDemandWriter(loads_output, massflows_output, temperatures_output)
    if format_output == 'csv':
        totals, time_series = writer_totals.write_to_csv(list_building_names, locator)
    elif format_output == 'hdf5':
        totals, time_series = writer_totals.write_to_hdf5(list_building_names, locator)
    else:
        raise Exception('error')

    time_elapsed = time.clock() - t0
    print('done - time elapsed: %d.2f seconds' % time_elapsed)

    return totals, time_series


def calc_demand_singleprocessing(date, locator, list_building_names,
                                 weather_data, use_dynamic_infiltration_calculation,
                                 resolution_outputs, loads_output, massflows_output, temperatures_output,
                                 format_output, config, write_detailed_output, debug):
    num_buildings = len(list_building_names)
    for i, building in enumerate(list_building_names):
        bpr = load_bpr_from_disc(building, locator)
        thermal_loads.calc_thermal_loads(building, bpr, weather_data, date, locator,
                                         use_dynamic_infiltration_calculation,
                                         resolution_outputs, loads_output, massflows_output, temperatures_output,
                                         format_output, config, write_detailed_output, debug)
        print('Building No. %i completed out of %i: %s' % (i + 1, num_buildings, building))


def calc_demand_multiprocessing(date, locator, list_building_names,
                                weather_data, use_dynamic_infiltration_calculation,
                                resolution_outputs, loads_output, massflows_output, temperatures_output, format_output,
                                config, write_detailed_output, debug):
    number_of_processes = config.get_number_of_processes()
    print("Using %i CPU's" % number_of_processes)
    pool = mp.Pool(number_of_processes)
    joblist = []
    num_buildings = len(list_building_names)
    for building in list_building_names:
        bpr = load_bpr_from_disc(building, locator)
        job = pool.apply_async(thermal_loads.calc_thermal_loads,
                               [building, bpr, weather_data, date, locator,
                                use_dynamic_infiltration_calculation,
                                resolution_outputs, loads_output, massflows_output, temperatures_output,
                                format_output, config, write_detailed_output, debug])
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
    print('Running demand calculation with dynamic infiltration=%s' %
          config.demand.use_dynamic_infiltration_calculation)
    print('Running demand calculation with multiprocessing=%s' % config.multiprocessing)

    if config.demand.write_detailed_output:
        print('Running demand calculation with write detailed output=%s' % config.demand.write_detailed_output)
    if config.debug:
        print('Running demand in debug mode: Instant visulaization of tsd activated.')


    if not radiation_files_exist(config, locator):
        raise ValueError("Missing radiation data in scenario. Consider running radiation script first.")

    demand_calculation(locator=locator, config=config)


def radiation_files_exist(config, locator):
    # verify that the necessary radiation files exist
    def daysim_results_exist(building_name):
        return os.path.exists(locator.get_radiation_metadata(building_name)) and os.path.exists(
            locator.get_radiation_building(building_name))

    return all(daysim_results_exist(building_name) for building_name in locator.get_zone_building_names())


if __name__ == '__main__':
    main(cea.config.Configuration())

"""
This script creates schedules per building in CEA
"""
from __future__ import division
from __future__ import print_function

import math
import os

import pandas as pd

import cea.config
import cea.inputlocator
from cea.utilities.schedule_reader import read_cea_schedule, save_cea_schedule

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def schedule_helper(locator, config):

    #local variables
    model = config.schedule_helper.model
    buildings = config.schedule_helper.model

    #select which model to run and run it
    if model == 'matsim':
        path_matsim_file_required1 = config.schedule_helper.matsim_file1
        path_matsim_file_required2 = config.schedule_helper.matsim_file2
        if path_matsim_file_required1 == None or path_matsim_file_required2 == None:
            Exception('There are not valid inputs to run the MATSIM model, please make sure to include the correct'
                      'path to each file')
        else:
            matsim_model(locator, buildings, path_matsim_file_required1, path_matsim_file_required2)
    elif model == 'sia-switzerland':
        path_to_standard_schedule_database = locator.get_database_standard_schedules(model)
        model_with_standard_database(locator, buildings, path_to_standard_schedule_database)
    elif model == 'ashrae-singapore':
        path_to_standard_schedule_database = locator.get_database_standard_schedules(model)
        model_with_standard_database(locator, buildings, path_to_standard_schedule_database)
    else:
        Exception('There is no valid model for schedule helper')


def model_with_standard_database(locator, buildings, path_to_standard_schedule_database):

    use = 'MULTI'
    schedule_data = pd.read_csv(locator.get_database_standard_schedules_use(path_to_standard_schedule_database, use))

    for name in buildings:




        metadata = path_to_standard_schedule_database
        occupancy_density_m2p = TODO
        monthly_multiplier = TODO
        occupancy_weekday = TODO
        occupancy_saturday = TODO
        occupancy_sunday = TODO
        appliances_weekday = TODO
        appliances_saturday = TODO
        appliances_sunday = TODO
        domestic_hot_water_weekday = TODO
        domestic_hot_water_saturday = TODO
        domestic_hot_water_sunday = TODO
        setpoint_heating_weekday = TODO
        setpoint_heating_saturday = TODO
        setpoint_heating_sunday = TODO
        setpoint_cooling_weekday = TODO
        setpoint_cooling_saturday = TODO
        setpoint_cooling_sunday = TODO
        processes_weekday = TODO
        processes_saturday = TODO
        processes_sunday = TODO

        schedule_data = {
            'metadata': metadata,
            'occupancy_density_m2p': occupancy_density_m2p,
            'monthly_multiplier': monthly_multiplier,
            'occupancy_weekday': occupancy_weekday,
            'occupancy_saturday': occupancy_saturday,
            'occupancy_sunday': occupancy_sunday,
            'appliances_weekday': appliances_weekday,
            'appliances_saturday': appliances_saturday,
            'appliances_sunday': appliances_sunday,
            'domestic_hot_water_weekday': domestic_hot_water_weekday,
            'domestic_hot_water_saturday': domestic_hot_water_saturday,
            'domestic_hot_water_sunday': domestic_hot_water_sunday,
            'setpoint_heating_weekday': setpoint_heating_weekday,
            'setpoint_heating_saturday': setpoint_heating_saturday,
            'setpoint_heating_sunday': setpoint_heating_sunday,
            'setpoint_cooling_weekday': setpoint_cooling_weekday,
            'setpoint_cooling_saturday': setpoint_cooling_saturday,
            'setpoint_cooling_sunday': setpoint_cooling_sunday,
            'processes_weekday': processes_weekday,
            'processes_saturday': processes_saturday,
            'processes_sunday': processes_sunday
        }
        path_to_building_schedule = locator.get_building_schedules(name)
        save_cea_schedule(schedule_data, path_to_building_schedule)

def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    schedule_helper(locator, config)

if __name__ == '__main__':
    main(cea.config.Configuration())
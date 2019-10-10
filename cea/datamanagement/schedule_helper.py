"""
This script creates schedules per building in CEA
"""
from __future__ import division
from __future__ import print_function

import os

import cea.config
import pandas as pd
import numpy as np
import cea.inputlocator
from cea.datamanagement.data_helper import get_list_of_uses_in_case_study
from cea.utilities.dbf import dbf_to_dataframe
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
    # local variables
    model = config.data_helper.model_schedule
    buildings = config.data_helper.buildings

    # select which model to run and run it
    if model == 'matsim':
        path_matsim_file_required1 = config.data_helper.matsim_file1
        path_matsim_file_required2 = config.data_helper.matsim_file2
        if path_matsim_file_required1 == None or path_matsim_file_required2 == None:
            Exception('There are not valid inputs to run the MATSIM model, please make sure to include the correct'
                      'path to each file')
        else:
            matsim_model(locator, buildings, path_matsim_file_required1, path_matsim_file_required2)
    elif model == 'CH-SIA-2014':
        path_to_standard_schedule_database = locator.get_database_standard_schedules(model)
        model_with_standard_database(locator, buildings, path_to_standard_schedule_database)
    elif model == 'SG-ASHRAE-2009':
        path_to_standard_schedule_database = locator.get_database_standard_schedules(model)
        model_with_standard_database(locator, buildings, path_to_standard_schedule_database)
    else:
        Exception('There is no valid model for schedule helper')


def matsim_model(locator, buildings, path_matsim_file_required1, path_matsim_file_required2):
    return 'TEST'


def model_with_standard_database(locator, buildings, path_to_standard_schedule_database):

    variable_schedule_map = {'Occ_m2pax': 'OCCUPANCY',
                             'Qs_Wp': 'OCCUPANCY',
                             'X_ghp': 'OCCUPANCY',
                             'Ve_lps': 'OCCUPANCY',
                             'Ea_Wm2': 'ELECTRICITY',
                             'El_Wm2': 'ELECTRICITY',
                             'Ed_Wm2': 'ELECTRICITY',
                             'Vww_lpd': 'WATER',
                             'Vw_lpd': 'WATER',
                             'Ths_set_C': 'HEATING',
                             'Tcs_set_C': 'COOLING',
                             'Qcre_Wm2': 'PROCESSES',
                             'Qhpro_Wm2': 'PROCESSES',
                             'Qcpro_Wm2': 'PROCESSES',
                             'Epro_Wm2': 'PROCESSES',
                             }

    metadata = path_to_standard_schedule_database
    schedule_data_all_uses = ScheduleData(locator, path_to_standard_schedule_database)
    building_occupancy_df = dbf_to_dataframe(locator.get_building_occupancy()).set_index('Name')
    building_occupancy_df = building_occupancy_df.ix[buildings]

    # validate list of uses in case study
    list_uses = get_list_of_uses_in_case_study(building_occupancy_df)

    from cea.datamanagement.data_helper import calc_mainuse
    building_occupancy_df['mainuse'] = calc_mainuse(building_occupancy_df, list_uses)
    internal_DB = pd.read_excel(locator.get_archetypes_properties(), 'INTERNAL_LOADS')
    comfort_DB = pd.read_excel(locator.get_archetypes_properties(), 'INDOOR_COMFORT')
    internal_DB = internal_DB.merge(comfort_DB, left_on='Code', right_on='Code')
    internal_DB = internal_DB.set_index('Code')


    for building in buildings:
        schedule_new_data = {}
        main_use_this_building = building_occupancy_df['mainuse'][building]
        monthly_multiplier = schedule_data_all_uses.schedule_complementray_data[main_use_this_building]['MONTHLY_MULTIPLIER']
        for variable, schedule_type in variable_schedule_map.items():
            current_schedule = np.zeros(len(schedule_data_all_uses.schedule_data['HOTEL'][schedule_type]))
            normalizing_value = 0.0
            if variable in ['Ths_set_C', 'Tcs_set_C']:
                schedule_new_data[variable] = schedule_data_all_uses.schedule_data[main_use_this_building][schedule_type]
            else:
                for use in list_uses:
                    if building_occupancy_df[use][building] > 0.0:
                        current_share_of_use = building_occupancy_df[use][building]
                        if variable in ['Occ_m2pax', 'Ve_lps', 'Qs_Wp', 'X_ghp', 'Vww_lpd', 'Vw_lpd']:
                            # for variables that depend on the number of people, the schedule needs to be calculated by number
                            # of people for each use at each time step, not the share of the occupancy for each
                            share_time_occupancy_density = internal_DB.ix[use, variable] * current_share_of_use * \
                                                           (1/internal_DB.ix[use, 'Occ_m2pax'])

                        elif variable in ['Ea_Wm2','El_Wm2', 'Ed_Wm2', 'Qcre_Wm2', 'Qhpro_Wm2', 'Qcpro_Wm2', 'Epro_Wm2']:
                            share_time_occupancy_density = internal_DB.ix[use, variable] * current_share_of_use

                        normalizing_value += share_time_occupancy_density
                        print(variable, building)
                        current_schedule = np.vectorize(calc_average)(current_schedule,
                                                                      schedule_data_all_uses.schedule_data[use][schedule_type],
                                                                      share_time_occupancy_density)

                if normalizing_value == 0:
                    schedule_new_data[variable] = current_schedule * 0
                else:
                    schedule_new_data[variable] = current_schedule / normalizing_value

        # save schedule per buidling
        schedule_complementray_data = {'METADATA': metadata, 'MONTHLY_MULTIPLIER': monthly_multiplier}
        path_to_building_schedule = locator.get_building_schedules_predefined(building)
        save_cea_schedule(schedule_new_data, schedule_complementray_data, path_to_building_schedule)


def calc_average(last, current, share_of_use):
    """
    function to calculate the weighted average of schedules
    """
    return last + current * share_of_use

class ScheduleData(object):

    def __init__(self, locator, path_to_standard_schedule_database):
        self.locator = locator
        self.path_database = path_to_standard_schedule_database
        self.schedule_data, self.schedule_complementray_data = self.fill_in_data()


    def fill_in_data(self):
        get_list_uses_in_database = []
        for file in os.listdir(self.path_database):
            if file.endswith(".cea"):
                get_list_uses_in_database.append(file.split('.')[0])

        data_schedules = []
        data_schedules_complimentary = []
        for use in get_list_uses_in_database:
            path_to_schedule = self.locator.get_database_standard_schedules_use(self.path_database, use)
            data_schedule, data_metadata = read_cea_schedule(path_to_schedule)
            data_schedules.append(data_schedule)
            data_schedules_complimentary.append(data_metadata)
        return dict(zip(get_list_uses_in_database, data_schedules)), dict(zip(get_list_uses_in_database, data_schedules_complimentary))


def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    config.data_helper.model_schedule = 'SG-ASHRAE-2009'
    config.data_helper.buildings = locator.get_zone_building_names()
    schedule_helper(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())

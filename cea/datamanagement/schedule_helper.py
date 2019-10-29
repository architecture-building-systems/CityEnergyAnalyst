"""
This script creates schedules per building in CEA
"""
from __future__ import division
from __future__ import print_function

import os

import numpy as np
import pandas as pd

import cea
import cea.config
import cea.inputlocator
from cea.datamanagement.databases_verification import COLUMNS_ZONE_OCCUPANCY
from cea.demand.constants import VARIABLE_CEA_SCHEDULE_RELATION
from cea.utilities.schedule_reader import read_cea_schedule, save_cea_schedule

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

COLUMN_NAMES_CEA_SCHEDULE = ['DAY',
                             'HOUR',
                             'OCCUPANCY',
                             'APPLIANCES',
                             'LIGHTING',
                             'WATER',
                             'HEATING',
                             'COOLING',
                             'PROCESSES',
                             'SERVERS']


def calc_mixed_schedule(locator,
                        building_occupancy_df,
                        buildings):

    metadata = 'mixed-schedule'
    schedule_data_all_uses = ScheduleData(locator)
    building_occupancy_df = building_occupancy_df.set_index('Name')
    building_occupancy_df = building_occupancy_df.loc[buildings]

    # get list of uses only with a valid value in building_occupancy_df
    list_uses = get_short_list_of_uses_in_case_study(building_occupancy_df)

    internal_DB = pd.read_excel(locator.get_archetypes_properties(), 'INTERNAL_LOADS')
    internal_DB = internal_DB.set_index('Code')

    occupant_densities = {}
    for use in list_uses:
        if internal_DB.loc[use, 'Occ_m2pax'] > 0.0:
            occupant_densities[use] = 1 / internal_DB.loc[use, 'Occ_m2pax']
        else:
            occupant_densities[use] = 0.0

    for building in buildings:
        schedule_new_data = {}
        main_use_this_building = building_occupancy_df['mainuse'][building]
        monthly_multiplier = np.sum([np.array(
            schedule_data_all_uses.schedule_complementary_data[use]['MONTHLY_MULTIPLIER']) * building_occupancy_df.loc[
                                         building, use] for use in list_uses], axis=0)
        for schedule_type in VARIABLE_CEA_SCHEDULE_RELATION.values():
            current_schedule = np.zeros(len(schedule_data_all_uses.schedule_data['HOTEL'][schedule_type]))
            normalizing_value = 0.0
            if schedule_type in ['HEATING', 'COOLING']:
                schedule_new_data[schedule_type] = schedule_data_all_uses.schedule_data[main_use_this_building][
                    schedule_type]
            else:
                for use in list_uses:
                    if building_occupancy_df[use][building] > 0.0:
                        current_share_of_use = building_occupancy_df[use][building]
                        if schedule_type in ['OCCUPANCY'] and occupant_densities[use] > 0.0:
                            # for variables that depend on the number of people, the schedule needs to be calculated by number
                            # of people for each use at each time step, not the share of the occupancy for each
                            share_time_occupancy_density = current_share_of_use * occupant_densities[use]
                            normalizing_value += share_time_occupancy_density
                            current_schedule = np.vectorize(calc_average)(current_schedule,
                                                                          schedule_data_all_uses.schedule_data[use][
                                                                              schedule_type],
                                                                          share_time_occupancy_density)

                        if schedule_type in ['WATER'] and occupant_densities[use] > 0.0 and (
                                internal_DB.loc[use, 'Vw_lpdpax'] + internal_DB.loc[use, 'Vw_lpdpax']) > 0.0:
                            # for variables that depend on the number of people, the schedule needs to be calculated by number
                            # of people for each use at each time step, not the share of the occupancy for each
                            share_time_occupancy_density = current_share_of_use * occupant_densities[use] * (
                                        internal_DB.loc[use, 'Vw_lpdpax'] + internal_DB.loc[use, 'Vw_lpdpax'])
                            normalizing_value += share_time_occupancy_density
                            current_schedule = np.vectorize(calc_average)(current_schedule,
                                                                          schedule_data_all_uses.schedule_data[use][
                                                                              schedule_type],
                                                                          share_time_occupancy_density)

                        elif schedule_type in ['APPLIANCES'] and internal_DB.loc[use, 'Ea_Wm2'] > 0.0:
                            share_time_occupancy_density = current_share_of_use * internal_DB.loc[use, 'Ea_Wm2']
                            normalizing_value += share_time_occupancy_density
                            current_schedule = np.vectorize(calc_average)(current_schedule,
                                                                          schedule_data_all_uses.schedule_data[use][
                                                                              schedule_type],
                                                                          share_time_occupancy_density)

                        elif schedule_type in ['LIGHTING'] and internal_DB.loc[use, 'El_Wm2'] > 0.0:
                            share_time_occupancy_density = current_share_of_use * internal_DB.loc[use, 'El_Wm2']
                            normalizing_value += share_time_occupancy_density
                            current_schedule = np.vectorize(calc_average)(current_schedule,
                                                                          schedule_data_all_uses.schedule_data[use][
                                                                              schedule_type],
                                                                          share_time_occupancy_density)

                        elif schedule_type in ['PROCESSES'] and internal_DB.loc[use, 'Epro_Wm2'] > 0.0:
                            share_time_occupancy_density = current_share_of_use * internal_DB.loc[use, 'Epro_Wm2']
                            normalizing_value += share_time_occupancy_density
                            current_schedule = np.vectorize(calc_average)(current_schedule,
                                                                          schedule_data_all_uses.schedule_data[use][
                                                                              schedule_type],
                                                                          share_time_occupancy_density)

                        elif schedule_type in ['SERVERS'] and internal_DB.loc[use, 'Ed_Wm2'] > 0.0:
                            share_time_occupancy_density = current_share_of_use * internal_DB.loc[use, 'Ed_Wm2']

                            normalizing_value += share_time_occupancy_density
                            current_schedule = np.vectorize(calc_average)(current_schedule,
                                                                          schedule_data_all_uses.schedule_data[use][
                                                                              schedule_type],
                                                                          share_time_occupancy_density)
                if normalizing_value == 0.0:
                    schedule_new_data[schedule_type] = current_schedule * 0.0
                else:
                    schedule_new_data[schedule_type] = current_schedule / normalizing_value

        # add hour and day of the week
        DAY = {'DAY': ['WEEKDAY'] * 24 + ['SATURDAY'] * 24 + ['SUNDAY'] * 24}
        HOUR = {'HOUR': range(1, 25) + range(1, 25) + range(1, 25)}
        schedule_new_data.update(DAY)
        schedule_new_data.update(HOUR)

        # calcualate complementary_data
        schedule_complementary_data = {'METADATA': metadata, 'MONTHLY_MULTIPLIER': monthly_multiplier}

        # save cea schedule format
        path_to_building_schedule = locator.get_building_weekly_schedules(building)
        save_cea_schedule(schedule_new_data, schedule_complementary_data, path_to_building_schedule)


def calc_average(last, current, share_of_use):
    """
    function to calculate the weighted average of schedules
    """
    return last + current * share_of_use


class ScheduleData(object):

    def __init__(self, locator):
        self.locator = locator
        self.path_database = self.locator.get_database_standard_schedules()
        self.schedule_data, self.schedule_complementary_data = self.fill_in_data()

    def fill_in_data(self):
        get_list_uses_in_database = []
        for file in os.listdir(self.path_database):
            if file.endswith(".csv"):
                get_list_uses_in_database.append(file.split('.')[0])

        data_schedules = []
        data_schedules_complimentary = []
        for use in get_list_uses_in_database:
            path_to_schedule = self.locator.get_database_standard_schedules_use(self.path_database, use)
            data_schedule, data_metadata = read_cea_schedule(path_to_schedule)
            data_schedules.append(data_schedule)
            data_schedules_complimentary.append(data_metadata)
        return dict(zip(get_list_uses_in_database, data_schedules)), \
               dict(zip(get_list_uses_in_database, data_schedules_complimentary))


def get_short_list_of_uses_in_case_study(building_occupancy_df):
    """
    gets only the list of land uses that all the building occupnacy dataset has
    It avoids multiple iterations, when these landuises are not even selected in the database

    :param building_occupancy_df: dataframe of occupancy.dbf input (can be read in data-helper or in building-properties)
    :type building_occupancy_df: pandas.DataFrame
    :return: list of uses in case study
    :rtype: pandas.DataFrame.Index
    """
    columns = building_occupancy_df.columns
    # validate list of uses
    list_uses = []
    for name in columns:
        if name in COLUMNS_ZONE_OCCUPANCY:
            if building_occupancy_df[name].sum() > 0.0:
                list_uses.append(name)  # append valid uses
    return list_uses


def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    path_database = locator.get_database_standard_schedules('CH-SIA-2024')
    path_to_building_schedule = locator.get_database_standard_schedules_use(path_database, 'MULTI_RES')


if __name__ == '__main__':
    main(cea.config.Configuration())

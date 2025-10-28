"""
This script creates schedules per building in CEA
"""

import os

import geopandas as gpd
import numpy as np
import pandas as pd

import cea
import cea.config
import cea.inputlocator
from cea.datamanagement.databases_verification import COLUMNS_ZONE_TYPOLOGY
from cea.demand.constants import VARIABLE_CEA_SCHEDULE_RELATION
from cea.utilities.schedule_reader import read_cea_schedule, save_cea_schedules, save_cea_monthly_multipliers

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_mixed_schedule(locator, building_typology_df, list_var_names=None, list_var_values=None):
    """
    Builds the ``cea.inputlocator.InputLocator#get_building_weekly_schedules`` for each building in the zone,
    combining the occupancy types as indicated in the inputs.


    :param cea.inputlocator.InputLocator locator: the locator to use
    :param building_typology_df: ``occupancy.dbf``, with an added column "mainuse"
    :param list_var_names: List of column names in building_typology_df that contain the names of use-types being calculated
    :type list_var_names: list[str]
    :param list_var_values: List of column names in building_typology_df that contain values of use-type ratio in respect to list_var_names
    :type list_var_values: list[str]
    :return:
    """

    buildings = building_typology_df['name']

    metadata = 'mixed-schedule'
    schedule_data_all_uses = ScheduleData(locator)
    building_typology_df = building_typology_df.loc[building_typology_df['name'].isin(buildings)]
    list_var_names, list_var_values = get_lists_of_var_names_and_var_values(list_var_names,
                                                                            list_var_values,
                                                                            building_typology_df)

    # Get list of uses, validate, and calculate occupant densities
    list_uses, occupant_densities, internal_loads = get_occupant_densities_from_archetypes(locator, building_typology_df)

    # Set index for building_typology_df (needed for downstream operations)
    building_typology_df.set_index('name', inplace=True)

    lists_monthly_multiplier = []
    for building in buildings:
        schedule_new_data, schedule_complementary_data = calc_single_mixed_schedule(list_uses, occupant_densities, building_typology_df, internal_loads, building, schedule_data_all_uses, list_var_names, list_var_values, metadata)
        # save cea schedule format
        path_to_building_schedule = locator.get_building_weekly_schedules(building)
        locator.ensure_parent_folder_exists(path_to_building_schedule)
        save_cea_schedules(schedule_new_data, path_to_building_schedule)

        list_monthly_multiplier = list(schedule_complementary_data['MONTHLY_MULTIPLIER'])
        list_monthly_multiplier.insert(0, building)
        lists_monthly_multiplier.append(list_monthly_multiplier)
    path_to_monthly_multiplier = locator.get_building_weekly_schedules_monthly_multiplier_csv()
    locator.ensure_parent_folder_exists(path_to_monthly_multiplier)
    save_cea_monthly_multipliers(lists_monthly_multiplier, path_to_monthly_multiplier)


def calc_single_mixed_schedule(list_uses, occupant_densities, building_typology_df, internal_loads_df, building, schedule_data_all_uses, list_var_names, list_var_values, metadata='mixed-schedule'):
    """
    Builds the ``cea.inputlocator.InputLocator#get_building_weekly_schedules`` for each building in the zone,
    combining the occupancy types as indicated in the inputs.

    :param list_uses: list of uses in the project
    :type list_uses: list[str]
    :param occupant_densities: Dictionary containing the number of people per square meter for each occupancy type based
           on the archetypes
    :type occupant_densities: dict
    :param building_typology_df: ``occupancy.dbf``, with an added column "mainuse"
    :type building_typology_df: pandas.DataFrame
    :param building: name of buildings to calculate the schedules for
    :type building: str
    :param list_var_names: List of column names in building_typology_df that contain the names of use-types being calculated
    :type list_var_names: list[str]
    :param list_var_values: List of column names in building_typology_df that contain values of use-type ratio in respect to list_var_names
    :type list_var_values: list[str]
    :return:
    """
    LEN_TYPICAL_SCHEDULE_HOURS = 72 #24 hours of weekday + 24 hours of Saturday + 24 hours of Sunday
    schedule_new_data = {}
    # First name in `list_var_names` would be treated as main use
    main_use_this_building = building_typology_df.at[building, list_var_names[0]]
    monthly_multiplier = np.zeros(12)
    for var_name, var_value in zip(list_var_names, list_var_values):
        # Use .at[] for scalar access to avoid Series comparison ambiguity
        current_use_type = building_typology_df.at[building, var_name]
        current_use_ratio = building_typology_df.at[building, var_value]

        # Only process if current use exists in list_uses and has non-zero ratio
        if current_use_type in list_uses and current_use_ratio > 0:
            monthly_multiplier += (
                np.array(schedule_data_all_uses.schedule_complementary_data[current_use_type]['MONTHLY_MULTIPLIER'])
                * current_use_ratio
            )
    for schedule_type in VARIABLE_CEA_SCHEDULE_RELATION.values():
        current_schedule = np.zeros(LEN_TYPICAL_SCHEDULE_HOURS)
        normalizing_value = 0.0
        if schedule_type in ['heating', 'cooling']:
            schedule_new_data[schedule_type] = schedule_data_all_uses.schedule_data[main_use_this_building][
                schedule_type]
        else:
            # Process each use type defined in the building
            for var_name, var_value in zip(list_var_names, list_var_values):
                # Use .at[] for scalar access to avoid Series comparison ambiguity
                use = building_typology_df.at[building, var_name]
                current_share_of_use = building_typology_df.at[building, var_value]

                # Skip if invalid use or zero ratio
                if use not in list_uses or current_share_of_use <= 0.0:
                    continue

                if schedule_type in ['occupancy'] and occupant_densities[use] > 0.0:
                    # for variables that depend on the number of people, the schedule needs to be calculated by number
                    # of people for each use at each time step, not the share of the occupancy for each
                    share_time_occupancy_density = current_share_of_use * occupant_densities[use]
                    normalizing_value += share_time_occupancy_density
                    current_schedule = np.vectorize(calc_average)(current_schedule,
                                                                  schedule_data_all_uses.schedule_data[use][
                                                                      schedule_type],
                                                                  share_time_occupancy_density)

                if schedule_type in ['hot_water'] and occupant_densities[use] > 0.0 and (
                        internal_loads_df.loc[use, 'Vw_ldp'] + internal_loads_df.loc[use, 'Vw_ldp']) > 0.0:
                    # for variables that depend on the number of people, the schedule needs to be calculated by number
                    # of people for each use at each time step, not the share of the occupancy for each
                    share_time_occupancy_density = current_share_of_use * occupant_densities[use] * (
                            internal_loads_df.loc[use, 'Vw_ldp'] + internal_loads_df.loc[use, 'Vw_ldp'])
                    normalizing_value += share_time_occupancy_density
                    current_schedule = np.vectorize(calc_average)(current_schedule,
                                                                  schedule_data_all_uses.schedule_data[use][
                                                                      schedule_type],
                                                                  share_time_occupancy_density)

                elif schedule_type in ['appliances'] and internal_loads_df.loc[use, 'Ea_Wm2'] > 0.0:
                    share_time_occupancy_density = current_share_of_use * internal_loads_df.loc[use, 'Ea_Wm2']
                    normalizing_value += share_time_occupancy_density
                    current_schedule = np.vectorize(calc_average)(current_schedule,
                                                                  schedule_data_all_uses.schedule_data[use][
                                                                      schedule_type],
                                                                  share_time_occupancy_density)

                elif schedule_type in ['lighting'] and internal_loads_df.loc[use, 'El_Wm2'] > 0.0:
                    share_time_occupancy_density = current_share_of_use * internal_loads_df.loc[use, 'El_Wm2']
                    normalizing_value += share_time_occupancy_density
                    current_schedule = np.vectorize(calc_average)(current_schedule,
                                                                  schedule_data_all_uses.schedule_data[use][
                                                                      schedule_type],
                                                                  share_time_occupancy_density)

                elif schedule_type in ['processes'] and internal_loads_df.loc[use, 'Epro_Wm2'] > 0.0:
                    share_time_occupancy_density = current_share_of_use * internal_loads_df.loc[use, 'Epro_Wm2']
                    normalizing_value += share_time_occupancy_density
                    current_schedule = np.vectorize(calc_average)(current_schedule,
                                                                  schedule_data_all_uses.schedule_data[use][
                                                                      schedule_type],
                                                                  share_time_occupancy_density)

                elif schedule_type in ['servers'] and internal_loads_df.loc[use, 'Ed_Wm2'] > 0.0:
                    share_time_occupancy_density = current_share_of_use * internal_loads_df.loc[use, 'Ed_Wm2']
                    normalizing_value += share_time_occupancy_density
                    current_schedule = np.vectorize(calc_average)(current_schedule,
                                                                  schedule_data_all_uses.schedule_data[use][
                                                                      schedule_type],
                                                                  share_time_occupancy_density)

                elif schedule_type in ['electromobility'] and internal_loads_df.loc[use, 'Ev_kWveh'] > 0.0:
                    share_time_occupancy_density = current_share_of_use * internal_loads_df.loc[use, 'Ev_kWveh']
                    normalizing_value += share_time_occupancy_density
                    current_schedule = np.vectorize(calc_average)(current_schedule,
                                                                  schedule_data_all_uses.schedule_data[use][
                                                                      schedule_type],
                                                                  share_time_occupancy_density)
            if normalizing_value == 0.0:
                schedule_new_data[schedule_type] = current_schedule * 0.0
            else:
                schedule_new_data[schedule_type] = np.round(current_schedule / normalizing_value, 2)

    # Create the 'hour' column
    hour_values = (
        ['Weekday_{:02d}'.format(i) for i in range(24)] +
        ['Saturday_{:02d}'.format(i) for i in range(24)] +
        ['Sunday_{:02d}'.format(i) for i in range(24)])
    schedule_new_data['hour'] = hour_values

    # calculate complementary_data
    schedule_complementary_data = {'METADATA': metadata, 'MONTHLY_MULTIPLIER': monthly_multiplier}
    return schedule_new_data, schedule_complementary_data

def get_list_of_uses_in_case_study(building_typology_df):
    """
    validates lists of uses in case study.
    refactored from archetypes_mapper function

    :param building_typology_df: dataframe of typology.dbf input (can be read in archetypes-mapper or in building-properties)
    :type building_typology_df: pandas.DataFrame
    :return: list of uses in case study
    :rtype: pandas.DataFrame.Index
    """
    list_var_names, list_var_values = get_lists_of_var_names_and_var_values(
        list_var_names=["use_type1", 'use_type2', 'use_type3'], list_var_values=["use_type1r", 'use_type2r', 'use_type3r'],
        building_typology_df=building_typology_df)

    # validate list of uses
    list_uses = set()

    for var_name, var_value in zip(list_var_names, list_var_values):
        uses_with_value = building_typology_df[var_value] > 0.0
        filtered = building_typology_df[var_name][uses_with_value]
        list_uses.update(filtered)

    unique_uses = list(list_uses)
    return unique_uses


def verify_use_types(list_uses, occ_densities_df):
    """
    Verify that all use types found in the case study exist in the USE_TYPES database.

    :param list_uses: list of use types found in the case study
    :type list_uses: list[str]
    :param occ_densities_df: DataFrame containing the use types database (indexed by 'use_type')
    :type occ_densities_df: pandas.DataFrame
    :raises ValueError: if any use types are missing from the database
    """
    available_use_types = set(occ_densities_df.index)
    case_study_use_types = set(list_uses)

    if not case_study_use_types.issubset(available_use_types):
        missing_use_types = case_study_use_types.difference(available_use_types)

        # Create a helpful error message
        error_message = (
            f"The following use type(s) are not found in the database: {', '.join(sorted(missing_use_types))}\n\n"
            f"Available use types in the database are:\n  {', '.join(sorted(available_use_types))}\n\n"
            f"Please check your building typology file (zone.shp or zone.geojson) and ensure that:\n"
            f"  1. The use types in columns 'use_type1', 'use_type2', 'use_type3' match the available use types\n"
            f"  2. The use types are correctly spelled and use the same case\n"
            f"  3. If you need a custom use type, add it to the database"
        )
        raise ValueError(error_message)


def get_occupant_densities_from_archetypes(locator, building_typology_df):
    """
    Load archetypes database, validate use types, and calculate occupant densities.

    This function consolidates common logic used across multiple modules to:
    1. Get the list of uses from the building typology
    2. Load the archetypes use type database
    3. Validate that all use types exist in the database
    4. Calculate occupant densities from Occ_m2p values

    :param locator: InputLocator instance to get the database path
    :type locator: cea.inputlocator.InputLocator
    :param building_typology_df: dataframe of typology input
    :type building_typology_df: pandas.DataFrame
    :return: tuple of (list_uses, occupant_densities dict, internal_loads DataFrame)
    :rtype: tuple[list, dict, pandas.DataFrame]
    """
    # Get list of uses only with a valid value in building_typology_df
    list_uses = get_list_of_uses_in_case_study(building_typology_df)

    # Load archetypes database
    internal_loads = pd.read_csv(locator.get_database_archetypes_use_type())
    internal_loads = internal_loads.set_index('use_type')

    # Validate that all use types exist in the database
    verify_use_types(list_uses, internal_loads)

    # Calculate occupant densities
    # Filter to only the use types present in the case study
    use_types_data = internal_loads.loc[list_uses, 'Occ_m2p']
    occupant_densities_values = np.where(use_types_data > 0.0, 1.0 / use_types_data, 0.0)
    occupant_densities = dict(zip(list_uses, occupant_densities_values))

    return list_uses, occupant_densities, internal_loads


def get_lists_of_var_names_and_var_values(list_var_names, list_var_values, building_typology_df):
    '''
    This script checks whether there are more var names in the building typology than the default number, and if so,
    it allows more than the default number of var names to be processed.
    '''

    if list_var_names is None:
        list_var_names = ["use_type1", 'use_type2', 'use_type3']
    if list_var_values is None:
        list_var_values = ["use_type1r", 'use_type2r', 'use_type3r']
    if len([c for c in building_typology_df.columns if '_USE_R' in c]) > len(list_var_values):
        list_var_values = [c for c in building_typology_df.columns if '_USE_R' in c]
        list_var_names = ['_'.join(c.split('_')[0:2]) for c in list_var_values]

    return list_var_names, list_var_values


def calc_average(last, current, share_of_use):
    """
    function to calculate the weighted average of schedules
    """
    return last + current * share_of_use


class ScheduleData(object):

    def __init__(self, locator):
        """
        :param cea.inputlocator.InputLocator locator: InputLocator for locating schedule data
        """
        self.locator = locator
        self.schedule_data, self.schedule_complementary_data = self.fill_in_data()

    def fill_in_data(self):
        occupancy_types = []
        for file_name in os.listdir(self.locator.get_db4_archetypes_schedules_library_folder()):
            if file_name.endswith(".csv"):
                use, _ = os.path.splitext(file_name)
                if use != 'MONTHLY_MULTIPLIER':
                    occupancy_types.append(use)

        data_schedules = []
        data_schedules_complimentary = []
        for use in occupancy_types:
            data_schedule, data_metadata = read_cea_schedule(self.locator, use_type=use, building=None)
            data_schedules.append(data_schedule)
            data_schedules_complimentary.append(data_metadata)
        schedule_data = dict(zip(occupancy_types, data_schedules))
        complementary_data = dict(zip(occupancy_types, data_schedules_complimentary))
        return schedule_data, complementary_data


def main(config: cea.config.Configuration):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    # get typology data
    building_typology_df = gpd.read_file(locator.get_zone_geometry())[COLUMNS_ZONE_TYPOLOGY]

    # validate list of uses in case study
    get_list_of_uses_in_case_study(building_typology_df)

    # calculate mixed schedules
    calc_mixed_schedule(locator, building_typology_df)

if __name__ == '__main__':
    main(cea.config.Configuration())

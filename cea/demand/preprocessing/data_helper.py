"""
building properties algorithm
"""

# HISTORY:
# J. A. Fonseca  script development          22.03.15

from __future__ import division
from __future__ import absolute_import

import os
import numpy as np
import pandas as pd
from cea.utilities.dbf import dbf_to_dataframe, dataframe_to_dbf
import cea.inputlocator
import cea.config

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas", "Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def data_helper(locator, config, prop_architecture_flag, prop_hvac_flag, prop_comfort_flag, prop_internal_loads_flag,
                prop_supply_systems_flag, prop_restrictions_flag):
    """
    algorithm to query building properties from statistical database
    Archetypes_HVAC_properties.csv. for more info check the integrated demand
    model of Fonseca et al. 2015. Appl. energy.

    :param InputLocator locator: an InputLocator instance set to the scenario to work on
    :param boolean prop_architecture_flag: if True, get properties about the construction and architecture.
    :param boolean prop_comfort_flag: if True, get properties about thermal comfort.
    :param boolean prop_hvac_flag: if True, get properties about types of HVAC systems, otherwise False.
    :param boolean prop_internal_loads_flag: if True, get properties about internal loads, otherwise False.

    The following files are created by this script, depending on which flags were set:

    - building_HVAC: .dbf
        describes the queried properties of HVAC systems.

    - architecture.dbf
        describes the queried properties of architectural features

    - building_thermal: .shp
        describes the queried thermal properties of buildings

    - indoor_comfort.shp
        describes the queried thermal properties of buildings
    """

    # get occupancy and age files
    building_occupancy_df = dbf_to_dataframe(locator.get_building_occupancy())
    list_uses = list(building_occupancy_df.drop(['Name'], axis=1).columns)  # parking excluded in U-Values
    building_age_df = dbf_to_dataframe(locator.get_building_age())

    # get occupant densities from archetypes schedules
    occupant_densities = {}
    for use in list_uses:
        archetypes_schedules = pd.read_excel(locator.get_archetypes_schedules(config.region), use).T
        area_per_occupant = archetypes_schedules['density'].values[:1][0]
        if area_per_occupant > 0:
            occupant_densities[use] = 1 / area_per_occupant
        else:
            occupant_densities[use] = 0

    # prepare shapefile to store results (a shapefile with only names of buildings
    names_df = building_age_df[['Name']]

    # define main use:
    building_occupancy_df['mainuse'] = calc_mainuse(building_occupancy_df, list_uses)

    # dataframe with jonned data for categories
    categories_df = building_occupancy_df.merge(building_age_df, on='Name')

    # get properties about the construction and architecture
    if prop_architecture_flag:
        architecture_DB = get_database(locator.get_archetypes_properties(config.region), 'ARCHITECTURE')
        architecture_DB['Code'] = architecture_DB.apply(lambda x: calc_code(x['building_use'], x['year_start'],
                                                                            x['year_end'], x['standard']), axis=1)
        categories_df['cat_built'] = calc_category(architecture_DB, categories_df, 'built', 'C')
        retrofit_category = ['envelope', 'roof', 'windows']
        for category in retrofit_category:
            categories_df['cat_'+category] = calc_category(architecture_DB, categories_df, category, 'R')

        prop_architecture_df = get_prop_architecture(categories_df, architecture_DB, list_uses)

        # write to shapefile
        prop_architecture_df_merged = names_df.merge(prop_architecture_df, on="Name")

        fields = ['Name', 'Hs','void_deck', 'wwr_north', 'wwr_west','wwr_east', 'wwr_south',
                  'type_cons', 'type_leak',  'type_roof', 'type_wall', 'type_win', 'type_shade']

        dataframe_to_dbf(prop_architecture_df_merged[fields], locator.get_building_architecture())

    # get properties about types of HVAC systems
    if prop_hvac_flag:
        HVAC_DB = get_database(locator.get_archetypes_properties(config.region), 'HVAC')
        HVAC_DB['Code'] = HVAC_DB.apply(lambda x: calc_code(x['building_use'], x['year_start'],
                                                            x['year_end'], x['standard']), axis=1)

        categories_df['cat_HVAC'] = calc_category(HVAC_DB, categories_df, 'HVAC', 'R')

        # define HVAC systems types
        prop_HVAC_df = categories_df.merge(HVAC_DB, left_on='cat_HVAC', right_on='Code')

        # write to shapefile
        prop_HVAC_df_merged = names_df.merge(prop_HVAC_df, on="Name")
        fields = ['Name', 'type_cs', 'type_hs', 'type_dhw', 'type_ctrl', 'type_vent']
        dataframe_to_dbf(prop_HVAC_df_merged[fields], locator.get_building_hvac())

    if prop_comfort_flag:
        comfort_DB = get_database(locator.get_archetypes_properties(config.region), 'INDOOR_COMFORT')

        # define comfort
        prop_comfort_df = categories_df.merge(comfort_DB, left_on='mainuse', right_on='Code')

        # write to shapefile
        prop_comfort_df_merged = names_df.merge(prop_comfort_df, on="Name")
        prop_comfort_df_merged = calculate_average_multiuse(prop_comfort_df_merged, occupant_densities, list_uses,
                                                            comfort_DB)
        fields = ['Name', 'Tcs_set_C', 'Ths_set_C', 'Tcs_setb_C', 'Ths_setb_C', 'Ve_lps']
        dataframe_to_dbf(prop_comfort_df_merged[fields], locator.get_building_comfort())

    if prop_internal_loads_flag:
        internal_DB = get_database(locator.get_archetypes_properties(config.region), 'INTERNAL_LOADS')

        # define comfort
        prop_internal_df = categories_df.merge(internal_DB, left_on='mainuse', right_on='Code')

        # write to shapefile
        prop_internal_df_merged = names_df.merge(prop_internal_df, on="Name")
        prop_internal_df_merged = calculate_average_multiuse(prop_internal_df_merged, occupant_densities, list_uses,
                                                             internal_DB)
        fields = ['Name', 'Qs_Wp', 'X_ghp', 'Ea_Wm2', 'El_Wm2', 'Epro_Wm2', 'Ere_Wm2', 'Ed_Wm2', 'Vww_lpd', 'Vw_lpd',
                  'Qhpro_Wm2']
        dataframe_to_dbf(prop_internal_df_merged[fields], locator.get_building_internal())

    if prop_supply_systems_flag:
        supply_DB = get_database(locator.get_archetypes_properties(config.region), 'SUPPLY')
        supply_DB['Code'] = supply_DB.apply(lambda x: calc_code(x['building_use'], x['year_start'],
                                                            x['year_end'], x['standard']), axis=1)

        categories_df['cat_supply'] = calc_category(supply_DB, categories_df, 'HVAC', 'R')

        # define HVAC systems types
        prop_supply_df = categories_df.merge(supply_DB, left_on='cat_supply', right_on='Code')

        # write to shapefile
        prop_supply_df_merged = names_df.merge(prop_supply_df, on="Name")
        fields = ['Name', 'type_cs', 'type_hs', 'type_dhw', 'type_el']
        dataframe_to_dbf(prop_supply_df_merged[fields], locator.get_building_supply())

    if prop_restrictions_flag:
        COLUMNS_ZONE_RESTRICTIONS = ['SOLAR', 'GEOTHERMAL', 'WATERBODY', 'NATURALGAS', 'BIOGAS']
        for field in COLUMNS_ZONE_RESTRICTIONS:
            names_df[field] = 0
        dataframe_to_dbf(names_df[['Name'] + COLUMNS_ZONE_RESTRICTIONS], locator.get_building_restrictions())


def calc_code(code1, code2, code3, code4):
    return str(code1) + str(code2) + str(code3) + str(code4)


def calc_mainuse(uses_df, uses):
    """
    Calculate a building's main use
    :param uses_df: DataFrame containing the share of each building that corresponds to each occupancy type
    :type uses_df: DataFrame
    :param uses: list of building uses actually available in the area
    :type uses: list

    :return mainuse: array containing each building's main occupancy
    :rtype mainuse: ndarray

    """
    databaseclean = uses_df[uses].transpose()
    array_max = np.array(databaseclean[databaseclean[:] > 0].idxmax(skipna=True), dtype='S10')
    for i in range(len(array_max)):
        if databaseclean[i][array_max[i]] != 1:
            databaseclean[i][array_max[i]] = 0
    array_second = np.array(databaseclean[databaseclean[:] > 0].idxmax(skipna=True), dtype='S10')
    mainuse = np.array(map(calc_comparison, array_second, array_max))

    return mainuse


def get_database(path_database, sheet):
    database = pd.read_excel(path_database, sheet)
    return database


def calc_comparison(array_second, array_max):
    if array_max == 'PARKING':
        if array_second != 'PARKING':
            array_max = array_second
    return array_max


def calc_category(archetype_DB, age, field, type):
    category = []
    for row in age.index:
        if age.loc[row, field] > age.loc[row, 'built']:
            category.append(archetype_DB[(archetype_DB['year_start'] <= age.loc[row, field]) & \
                                         (archetype_DB['year_end'] >= age.loc[row, field]) & \
                                         (archetype_DB['building_use'] == age.loc[row, 'mainuse']) & \
                                         (archetype_DB['standard'] == type)].Code.values[0])
        else:
            category.append(archetype_DB[(archetype_DB['year_start'] <= age.loc[row, 'built']) & \
                                         (archetype_DB['year_end'] >= age.loc[row, 'built']) & \
                                         (archetype_DB['building_use'] == age.loc[row, 'mainuse']) & \
                                         (archetype_DB['standard'] == 'C')].Code.values[0])
        if field != 'built':
            if 0 < age.loc[row, field] < age.loc[row, 'built']:
                print('Incorrect %s renovation year in building %s: renovation year is lower than building age' %
                      (field, age['Name'][row]))
            if age.loc[row, field] == age.loc[row, 'built']:
                print('Incorrect %s renovation year in building %s: if building is not renovated, the year needs to be '
                      'set to 0' % (field, age['Name'][row]))

    return category

def correct_archetype_areas(prop_architecture_df, architecture_DB, list_uses):
    """
    Corrects the heated area 'Hs' for buildings with multiple uses.

    :var prop_architecture_df: DataFrame containing each building's occupancy, construction and renovation data as
        well as the architectural properties obtained from the archetypes.
    :type prop_architecture_df: DataFrame
    :var architecture_DB: architecture database for each archetype
    :type architecture_DB: DataFrame
    :var list_uses: list of all occupancy types in the project
    :type list_uses: list[str]

    :return Hs_list: the corrected values for 'Hs' for each building
    :type Hs_list: list[float]
    """

    indexed_DB = architecture_DB.set_index('Code')

    # weighted average of values
    def calc_average(last, current, share_of_use):
        return last + current * share_of_use

    Hs_list = []

    for building in prop_architecture_df.index:
        Hs = 0
        for use in list_uses:
            # if the use is present in the building, find the building archetype properties for that use
            if prop_architecture_df[use][building] > 0:
                # get archetype code for the current occupancy type
                current_use_code = use + str(prop_architecture_df['year_start'][building]) + \
                                   str(prop_architecture_df['year_end'][building]) + \
                                   str(prop_architecture_df['standard'][building])
                # recalculate heated floor area as an average of the archetype value for each occupancy type in the
                # building
                Hs = calc_average(Hs, indexed_DB['Hs'][current_use_code], prop_architecture_df[use][building])
        Hs_list.append(Hs)

    return Hs_list

def get_prop_architecture(categories_df, architecture_DB, list_uses):
    """
    This function obtains every building's architectural properties based on the construction and renovation years.

    :param categories_df: DataFrame containing each building's construction and renovation categories for each building
        component based on the construction and renovation years
    :type categories_df: DataFrame
    :param architecture_DB: DataFrame containing the archetypal architectural properties for each use type, construction
        and renovation year
    :type categories_df: DataFrame
    :return prop_architecture_df: DataFrame containing the architectural properties of each building in the area
    :rtype prop_architecture_df: DataFrame
    """

    # create databases from construction and renovation archetypes
    construction_DB = architecture_DB.drop(['type_leak','type_wall','type_roof','type_shade','type_win'], axis=1)
    envelope_DB = architecture_DB[['Code', 'type_leak', 'type_wall']].copy()
    roof_DB = architecture_DB[['Code','type_roof']].copy()
    window_DB = architecture_DB[['Code','type_win', 'type_shade']].copy()

    # create prop_architecture_df based on the construction categories and archetype architecture database
    prop_architecture_df = categories_df.merge(construction_DB, left_on='cat_built', right_on='Code').drop('Code',axis=1)
    # get envelope properties based on the envelope renovation year
    prop_architecture_df = prop_architecture_df.merge(envelope_DB, left_on='cat_envelope', right_on='Code').drop('Code',axis=1)
    # get roof properties based on the roof renovation year
    prop_architecture_df = prop_architecture_df.merge(roof_DB, left_on='cat_roof', right_on='Code').drop('Code',axis=1)
    # get window properties based on the window renovation year
    prop_architecture_df = prop_architecture_df.merge(window_DB, left_on='cat_windows', right_on='Code').drop('Code',axis=1)

    # adjust share of floor space that is heated ('Hs') for multiuse buildings
    prop_architecture_df['Hs'] = correct_archetype_areas(prop_architecture_df, architecture_DB, list_uses)

    return prop_architecture_df

def calculate_average_multiuse(properties_df, occupant_densities, list_uses, properties_DB):
    """
    This script calculates the average internal loads and ventilation properties for multiuse buildings.

    :param properties_df: DataFrame containing the building's occupancy type and the corresponding indoor comfort
        properties or internal loads.
    :type properties_df: DataFrame
    :param occupant_densities: DataFrame containing the number of people per square meter for each occupancy type based
        on the archetypes
    :type occupant_densities: Dict
    :param list_uses: list of uses in the project
    :type list_uses: list[str]
    :param properties_DB: DataFrame containing each occupancy type's indoor comfort properties or internal loads based
        on the corresponding archetypes
    :type properties_DB: DataFrame

    :return properties_df: the same DataFrame as the input parameter, but with the updated properties for multiuse
        buildings
    """

    indexed_DB = properties_DB.set_index('Code')

    for column in properties_df.columns:
        if column in ['Ve_lps', 'Qs_Wp', 'X_ghp', 'Vww_lpd', 'Vw_lpd']:
            # some properties are imported from the Excel files as int instead of float
            properties_df[column] = properties_df[column].astype(float)
            for building in properties_df.index:
                column_total = 0
                people_total = 0
                for use in list_uses:
                    if use in properties_df.columns:
                        column_total += properties_df[use][building] * occupant_densities[use] * indexed_DB[column][use]
                        people_total += properties_df[use][building] * occupant_densities[use]
                if people_total > 0:
                    properties_df.loc[building, column] = column_total / people_total
                else:
                    properties_df.loc[building, column] = 0

        elif column in ['Ea_Wm2', 'El_Wm2', 'Epro_Wm2', 'Ere_Wm2', 'Ed_Wm2', 'Qhpro_Wm2']:
            for building in properties_df.index:
                average = 0
                for use in list_uses:
                    average += properties_df[use][building] * indexed_DB[column][use]
                properties_df.loc[building, column] = average

    return properties_df


def main(config):
    """
    Run the properties script with input from the reference case and compare the results. This ensures that changes
    made to this script (e.g. refactorings) do not stop the script from working and also that the results stay the same.
    """

    print('Running data-helper with scenario = %s' % config.scenario)
    print('Running data-helper with archetypes = %s' % config.data_helper.archetypes)

    prop_architecture_flag = 'architecture' in config.data_helper.archetypes
    prop_hvac_flag = 'HVAC' in config.data_helper.archetypes
    prop_comfort_flag = 'comfort' in config.data_helper.archetypes
    prop_internal_loads_flag = 'internal-loads' in config.data_helper.archetypes
    prop_supply_systems_flag = 'supply' in config.data_helper.archetypes
    prop_restrictions_flag = 'restrictions' in config.data_helper.archetypes

    locator=cea.inputlocator.InputLocator(config.scenario)

    data_helper(locator=locator, config=config, prop_architecture_flag=prop_architecture_flag,
                prop_hvac_flag=prop_hvac_flag, prop_comfort_flag=prop_comfort_flag,
                prop_internal_loads_flag=prop_internal_loads_flag,
                prop_supply_systems_flag=prop_supply_systems_flag,
                prop_restrictions_flag=prop_restrictions_flag)


if __name__ == '__main__':
    main(cea.config.Configuration())

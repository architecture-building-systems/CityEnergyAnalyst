"""
building properties algorithm
"""

# HISTORY:
# J. A. Fonseca  script development          22.03.15

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import warnings

import numpy as np
import pandas as pd

import cea.config
import cea.inputlocator
from cea import InvalidOccupancyNameException
from cea.datamanagement.schedule_helper import calc_mixed_schedule
from cea.utilities.dbf import dbf_to_dataframe, dataframe_to_dbf


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas", "Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def get_technology_related_databases(locator, region):
    technology_database_template = locator.get_technology_template_for_region(region)
    print("Copying technology databases from {source}".format(source=technology_database_template))
    output_directory = locator.get_databases_folder()

    from distutils.dir_util import copy_tree
    copy_tree(technology_database_template, output_directory)


def archetypes_mapper(locator,
                      update_architecture_dbf,
                      update_air_conditioning_systems_dbf,
                      update_indoor_comfort_dbf,
                      update_internal_loads_dbf,
                      update_supply_systems_dbf,
                      update_schedule_operation_cea,
                      buildings):

    """
    algorithm to query building properties from statistical database
    Archetypes_HVAC_properties.csv. for more info check the integrated demand
    model of Fonseca et al. 2015. Appl. energy.

    :param InputLocator locator: an InputLocator instance set to the scenario to work on
    :param boolean update_architecture_dbf: if True, update the construction and architecture properties.
    :param boolean update_indoor_comfort_dbf: if True, get properties about thermal comfort.
    :param boolean update_air_conditioning_systems_dbf: if True, get properties about types of HVAC systems, otherwise False.
    :param boolean update_internal_loads_dbf: if True, get properties about internal loads, otherwise False.

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
    building_typology_df = dbf_to_dataframe(locator.get_building_typology())

    # validate list of uses in case study
    list_uses = get_list_of_uses_in_case_study(building_typology_df)

    # get occupant densities from archetypes schedules
    occupant_densities = {}
    occ_densities = pd.read_excel(locator.get_database_use_types_properties(), 'INTERNAL_LOADS').set_index('code')
    for use in list_uses:
        if occ_densities.loc[use, 'Occ_m2pax'] > 0.0:
            occupant_densities[use] = 1 / occ_densities.loc[use, 'Occ_m2pax']
        else:
            occupant_densities[use] = 0.0

    # get properties about the construction and architecture
    if update_architecture_dbf:
        architecture_mapper(locator, building_typology_df)

    # get properties about types of HVAC systems
    if update_air_conditioning_systems_dbf:
        aircon_mapper(locator, building_typology_df)

    if update_indoor_comfort_dbf:
        indoor_comfort_mapper(list_uses, locator, occupant_densities, building_typology_df)

    if update_internal_loads_dbf:
        internal_loads_mapper(list_uses, locator, occupant_densities, building_typology_df)

    if update_schedule_operation_cea:
        if not buildings:
            buildings = locator.get_zone_building_names()
        calc_mixed_schedule(locator, building_typology_df, buildings)

    if update_supply_systems_dbf:
        supply_mapper(locator, building_typology_df)


def indoor_comfort_mapper(list_uses, locator, occupant_densities, building_typology_df):
    comfort_DB = pd.read_excel(locator.get_database_use_types_properties(), 'INDOOR_COMFORT')
    # define comfort
    prop_comfort_df = building_typology_df.merge(comfort_DB, left_on='1ST_USE', right_on='code')
    # write to shapefile
    fields = ['Name',
              'Tcs_set_C',
              'Ths_set_C',
              'Tcs_setb_C',
              'Ths_setb_C',
              'Ve_lpspax',
              'RH_min_pc',
              'RH_max_pc']
    prop_comfort_df_merged = calculate_average_multiuse(fields,
                                                        prop_comfort_df,
                                                        occupant_densities,
                                                        list_uses,
                                                        comfort_DB)
    dataframe_to_dbf(prop_comfort_df_merged[fields], locator.get_building_comfort())


def internal_loads_mapper(list_uses, locator, occupant_densities, building_typology_df):
    internal_DB = pd.read_excel(locator.get_database_use_types_properties(), 'INTERNAL_LOADS')
    # define comfort
    prop_internal_df = building_typology_df.merge(internal_DB, left_on='1ST_USE', right_on='code')
    # write to shapefile
    fields = ['Name',
              'Occ_m2pax',
              'Qs_Wpax',
              'X_ghpax',
              'Ea_Wm2',
              'El_Wm2',
              'Ed_Wm2',
              'Ev_kWveh',
              'Qcre_Wm2',
              'Vww_lpdpax',
              'Vw_lpdpax',
              'Qhpro_Wm2',
              'Qcpro_Wm2',
              'Epro_Wm2']
    prop_internal_df_merged = calculate_average_multiuse(fields,
                                                         prop_internal_df,
                                                         occupant_densities,
                                                         list_uses,
                                                         internal_DB)
    dataframe_to_dbf(prop_internal_df_merged[fields], locator.get_building_internal())


def supply_mapper(locator, building_typology_df):
    supply_DB = pd.read_excel(locator.get_database_construction_standards(), 'SUPPLY_ASSEMBLIES')
    prop_supply_df = building_typology_df.merge(supply_DB, left_on='STANDARD', right_on='STANDARD')
    fields = ['Name',
              'type_cs',
              'type_hs',
              'type_dhw',
              'type_el']
    dataframe_to_dbf(prop_supply_df[fields], locator.get_building_supply())

def aircon_mapper(locator, typology_df):
    air_conditioning_DB = pd.read_excel(locator.get_database_construction_standards(), 'HVAC_ASSEMBLIES')
    # define HVAC systems types
    prop_HVAC_df = typology_df.merge(air_conditioning_DB, left_on='STANDARD', right_on='STANDARD')
    # write to shapefile
    fields = ['Name',
              'type_cs',
              'type_hs',
              'type_dhw',
              'type_ctrl',
              'type_vent',
              'heat_starts',
              'heat_ends',
              'cool_starts',
              'cool_ends']
    dataframe_to_dbf(prop_HVAC_df[fields], locator.get_building_air_conditioning())


def architecture_mapper(locator, typology_df):
    architecture_DB = pd.read_excel(locator.get_database_construction_standards(), 'ENVELOPE_ASSEMBLIES')
    prop_architecture_df = typology_df.merge(architecture_DB, left_on='STANDARD', right_on='STANDARD')
    fields = ['Name',
              'Hs_ag',
              'Hs_bg',
              'Ns',
              'Es',
              'void_deck',
              'wwr_north',
              'wwr_west',
              'wwr_east',
              'wwr_south',
              'type_cons',
              'type_leak',
              'type_floor',
              'type_part',
              'type_base',
              'type_roof',
              'type_wall',
              'type_win',
              'type_shade']
    dataframe_to_dbf(prop_architecture_df[fields], locator.get_building_architecture())


def get_list_of_uses_in_case_study(building_typology_df):
    """
    validates lists of uses in case study.
    refactored from archetypes_mapper function

    :param building_typology_df: dataframe of occupancy.dbf input (can be read in archetypes-mapper or in building-properties)
    :type building_typology_df: pandas.DataFrame
    :return: list of uses in case study
    :rtype: pandas.DataFrame.Index
    """
    list_var_names = ["1ST_USE", '2ND_USE', '3RD_USE']
    list_var_values = ["1ST_USE_R", '2ND_USE_R', '3RD_USE_R']
    # validate list of uses
    list_uses = []
    n_records = building_typology_df.shape[0]
    for row in range(n_records):
        for var_name, var_value in zip(list_var_names,list_var_values):
            if building_typology_df.loc[row, var_value] > 0.0:
                list_uses.append(building_typology_df.loc[row, var_name])  # append valid uses
    unique_uses = list(set(list_uses))
    return unique_uses


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

    # print a warning if there are equal shares of more than one "main" use
    # check if 'Name' is already the index, this is necessary because the function is used in data-helper
    #  and in building properties
    if uses_df.index.name not in ['Name']:
        # this is the behavior in data-helper
        indexed_df = uses_df.set_index('Name')
    else:
        # this is the behavior in building-properties
        indexed_df = uses_df.copy()
        uses_df = uses_df.reset_index()

    for building in indexed_df.index:
        mainuses = [use for use in uses if
                    (indexed_df.loc[building, use] == indexed_df.max(axis=1)[building]) and (use != 'PARKING')]
        if len(mainuses) > 1:
            print("%s has equal share of %s; the construction properties and systems for %s will be used." % (
                building, ' and '.join(mainuses), mainuses[0]))

    # get array of main use for each building
    databaseclean = uses_df[uses].transpose()
    array_max = np.array(databaseclean[databaseclean[:] > 0].idxmax(skipna=True), dtype='S10')
    for i in range(len(array_max)):
        if databaseclean[i][array_max[i]] != 1:
            databaseclean[i][array_max[i]] = 0
    array_second = np.array(databaseclean[databaseclean[:] > 0].idxmax(skipna=True), dtype='S10')
    mainuse = np.array(map(calc_comparison, array_second, array_max))

    return mainuse


def calc_comparison(array_second, array_max):
    if array_max == 'PARKING':
        if array_second != 'PARKING':
            array_max = array_second
    return array_max

def correct_archetype_areas(prop_architecture_df, architecture_DB, list_uses):
    """
    Corrects the heated area 'Hs_ag' and 'Hs_bg' for buildings with multiple uses.

    :var prop_architecture_df: DataFrame containing each building's occupancy, construction and renovation data as
        well as the architectural properties obtained from the archetypes.
    :type prop_architecture_df: DataFrame
    :var architecture_DB: architecture database for each archetype
    :type architecture_DB: DataFrame
    :var list_uses: list of all occupancy types in the project
    :type list_uses: list[str]

    :return Hs_ag_list, Hs_bg_list, Ns_list, Es_list: the corrected values for 'Hs_ag', 'Hs_bg', 'Ns' and 'Es' for each
    building
    :type Hs_ag_list, Hs_bg_list, Ns_list, Es_list:: list[float]
    """

    indexed_DB = architecture_DB.set_index('Code')

    # weighted average of values
    def calc_average(last, current, share_of_use):
        return last + current * share_of_use

    Hs_ag_list = []
    Hs_bg_list = []
    Ns_list = []
    Es_list = []
    for building in prop_architecture_df.index:
        Hs_ag = 0.0
        Hs_bg = 0.0
        Ns = 0.0
        Es = 0.0
        for use in list_uses:
            # if the use is present in the building, find the building archetype properties for that use
            if prop_architecture_df[use][building] > 0.0:
                # get archetype code for the current occupancy type
                current_use_code = use + str(prop_architecture_df['year_start'][building]) + \
                                   str(prop_architecture_df['year_end'][building]) + \
                                   str(prop_architecture_df['standard'][building])
                # recalculate heated floor area as an average of the archetype value for each occupancy type in the
                # building
                Hs_ag = calc_average(Hs_ag, indexed_DB['Hs_ag'][current_use_code], prop_architecture_df[use][building])
                Hs_bg = calc_average(Hs_bg, indexed_DB['Hs_bg'][current_use_code], prop_architecture_df[use][building])
                Ns = calc_average(Ns, indexed_DB['Ns'][current_use_code], prop_architecture_df[use][building])
                Es = calc_average(Es, indexed_DB['Es'][current_use_code], prop_architecture_df[use][building])
        Hs_ag_list.append(Hs_ag)
        Hs_bg_list.append(Hs_bg)
        Ns_list.append(Ns)
        Es_list.append(Es)

    return Hs_ag_list, Hs_bg_list, Ns_list, Es_list


def get_prop_architecture(typology_df, architecture_DB):
    """
    This function obtains every building's architectural properties based on the construction and renovation years.

    :param typology_df: DataFrame containing each building's construction and renovation categories for each building
        component based on the construction and renovation years
    :type typology_df: DataFrame
    :param architecture_DB: DataFrame containing the archetypal architectural properties for each use type, construction
        and renovation year
    :type categories_df: DataFrame
    :return prop_architecture_df: DataFrame containing the architectural properties of each building in the area
    :rtype prop_architecture_df: DataFrame
    """
    # create prop_architecture_df based on the construction categories and archetype architecture database
    prop_architecture_df = typology_df.merge(architecture_DB, left_on='STANDARD', right_on='STANDARD')
    return prop_architecture_df


def calculate_average_multiuse(fields, properties_df, occupant_densities, list_uses, properties_DB, list_var_names=None,
                               list_var_values=None):
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
    :param list_var_names: List of column names in properties_df that contain the names of use-types being caculated
    :type: list_var_names: list[str]
    :param list_var_values: List of column names in properties_df that contain values of use-type ratio in respect to list_var_names
    :type: list_var_values: list[str]

    :return properties_df: the same DataFrame as the input parameter, but with the updated properties for multiuse
        buildings
    """

    if list_var_names is None:
        list_var_names = ["1ST_USE", '2ND_USE', '3RD_USE']
    if list_var_values is None:
        list_var_values = ["1ST_USE_R", '2ND_USE_R', '3RD_USE_R']

    properties_DB = properties_DB.set_index('code')
    for column in fields:
        if column in ['Ve_lpspax', 'Qs_Wpax', 'X_ghpax', 'Vww_lpdpax', 'Vw_lpdpax']:
            # some properties are imported from the Excel files as int instead of float
            properties_df[column] = properties_df[column].astype(float)
            for building in properties_df.index:
                column_total = 0
                people_total = 0
                for use in list_uses:
                    for var_name, var_value in zip(list_var_names, list_var_values):
                        if use in [properties_df[var_name][building]]:
                            column_total += (properties_df[var_value][building]
                                             * occupant_densities[use]
                                             * properties_DB[column][use])
                            people_total += properties_df[var_value][building] * occupant_densities[use]
                if people_total > 0.0:
                    properties_df.loc[building, column] = column_total / people_total
                else:
                    properties_df.loc[building, column] = 0

        elif column in ['Ea_Wm2', 'El_Wm2', 'Epro_Wm2', 'Qcre_Wm2', 'Ed_Wm2', 'Qhpro_Wm2', 'Qcpro_Wm2', 'Occ_m2pax']:
            for building in properties_df.index:
                average = 0.0
                for use in list_uses:
                    for var_name, var_value in zip(list_var_names, list_var_values):
                        if use in [properties_df[var_name][building]]:
                            average += properties_df[var_value][building] * properties_DB[column][use]


                properties_df.loc[building, column] = average

    return properties_df


def main(config):
    """
    Run the properties script with input from the reference case and compare the results. This ensures that changes
    made to this script (e.g. refactorings) do not stop the script from working and also that the results stay the same.
    """

    print('Running archetypes-mapper with scenario = %s' % config.scenario)

    update_architecture_dbf = 'architecture' in config.archetypes_mapper.input_databases
    update_air_conditioning_systems_dbf = 'air-conditioning' in config.archetypes_mapper.input_databases
    update_indoor_comfort_dbf = 'comfort' in config.archetypes_mapper.input_databases
    update_internal_loads_dbf = 'internal-loads' in config.archetypes_mapper.input_databases
    update_supply_systems_dbf = 'supply' in config.archetypes_mapper.input_databases
    update_schedule_operation_cea = 'schedules' in config.archetypes_mapper.input_databases

    buildings = config.archetypes_mapper.buildings
    locator = cea.inputlocator.InputLocator(config.scenario)

    archetypes_mapper(locator=locator,
                      update_architecture_dbf=update_architecture_dbf,
                      update_air_conditioning_systems_dbf=update_air_conditioning_systems_dbf,
                      update_indoor_comfort_dbf=update_indoor_comfort_dbf,
                      update_internal_loads_dbf=update_internal_loads_dbf,
                      update_supply_systems_dbf=update_supply_systems_dbf,
                      update_schedule_operation_cea=update_schedule_operation_cea,
                      buildings=buildings)


if __name__ == '__main__':
    main(cea.config.Configuration())

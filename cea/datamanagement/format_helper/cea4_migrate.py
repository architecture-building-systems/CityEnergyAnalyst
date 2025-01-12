"""
Mirgate the format of the input data to CEA-4 format after verification.

"""

import cea.inputlocator
import os
import cea.config
import time
import pandas as pd
import geopandas as gpd


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.datamanagement.format_helper.cea4_verify import cea4_verify, verify_shp, verify_csv, \
    verify_name_duplicates
from cea.utilities.dbf import dbf_to_dataframe


## --------------------------------------------------------------------------------------------------------------------
## The paths to the input files for CEA-3
## --------------------------------------------------------------------------------------------------------------------

# The paths are relatively hardcoded for now without using the inputlocator script.
# This is because we want to iterate over all scenarios, which is currently not possible with the inputlocator script.
def path_to_input_file_without_db_3(scenario, item):

    if item == "zone":
        path_to_input_file = os.path.join(scenario, "inputs", "building-geometry", "zone.shp")
    elif item == "surroundings":
        path_to_input_file = os.path.join(scenario, "inputs", "building-geometry", "surroundings.shp")
    elif item == "air_conditioning":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "air_conditioning.dbf")
    elif item == "architecture":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "architecture.dbf")
    elif item == "indoor_comfort":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "indoor_comfort.dbf")
    elif item == "internal_loads":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "internal_loads.dbf")
    elif item == "supply_systems":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "supply_systems.dbf")
    elif item == "typology":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "typology.dbf")
    elif item == 'streets':
        path_to_input_file = os.path.join(scenario, "inputs", "networks", "streets.shp")
    elif item == 'terrain':
        path_to_input_file = os.path.join(scenario, "inputs", "topography", "terrain.tif")
    elif item == 'weather':
        path_to_input_file = os.path.join(scenario, "inputs", "weather", "weather.epw")

    return path_to_input_file


## --------------------------------------------------------------------------------------------------------------------
## Helper functions
## --------------------------------------------------------------------------------------------------------------------
def replace_shapefile_dbf(scenario, item, new_dataframe, list_attributes_3):
    """
    Replace the DBF file of a shapefile with the contents of a new DataFrame,
    ensuring matching of `['Name']` in the shapefile and `['name']` in the new DataFrame.

    :param shapefile_path: Path to the shapefile (without file extension).
    :param new_dataframe: pandas DataFrame with the new data to replace the DBF file.
    """
    # Load the original shapefile
    shapefile_path = path_to_input_file_without_db_3(scenario, item)
    gdf = gpd.read_file(shapefile_path)
    list_attributes_3_without_name = [item for item in list_attributes_3 if item != 'name']
    gdf = gdf.drop(columns=list_attributes_3_without_name, errors='ignore')

    # Perform an inner join to match rows based on ['Name'] and ['name']
    merged = gdf.merge(new_dataframe, how='outer', left_on='Name', right_on='name')

    # Ensure all geometries are preserved
    if len(merged) != len(gdf):
        raise ValueError("Not all rows in the GeoDataFrame have a matching entry in the new DataFrame.")

    # Drop duplicate or unnecessary columns, keeping only the new attributes
    new_gdf = merged.drop(columns=['Name'], errors='ignore')

    # Save the updated shapefile
    new_gdf.to_file(shapefile_path, driver="ESRI Shapefile")

def verify_file_exists_3(scenario, items):
    """
    Verify if the files in the provided list exist for a given scenario.

    Parameters:
        scenario (str): Path or identifier for the scenario.
        items (list): List of file identifiers to check.

    Returns:
        list: A list of missing file identifiers, or an empty list if all files exist.
    """
    list_missing_files = []
    for file in items:
        path = path_to_input_file_without_db_3(scenario, file)
        if not os.path.isfile(path):
            list_missing_files.append(file)
    return list_missing_files

## --------------------------------------------------------------------------------------------------------------------
## Migrate to CEA-4 format from CEA-3 format
## --------------------------------------------------------------------------------------------------------------------

def verify_dbf(scenario, item, required_attributes):
    """
    Verify if a shapefile contains all required attributes.

    Parameters:
        scenario (str): Path or identifier for the scenario.
        item (str): Either "zone" or "surroundings".
        required_attributes (list): List of attribute names to verify.

    Returns:
        A list of missing attributes, or an empty list if all attributes are present.
    """
    # Construct the shapefile path
    dbf_path = path_to_input_file_without_db_3(scenario, item)

    # Check if the shapefile exists
    if not os.path.isfile(dbf_path):
        raise FileNotFoundError(f"Shapefile not found: {dbf_path}")

    # Load the shapefile
    try:
        df = dbf_to_dataframe(dbf_path)
    except Exception as e:
        raise ValueError(f"Error reading .dbf file: {e}")

    # Get the column names from the shapefile's attribute table
    dbf_columns = df.columns.tolist()

    # Check for missing attributes
    missing_attributes = [attr for attr in required_attributes if attr not in dbf_columns]

    return missing_attributes


def migrate_cea3_to_cea4(scenario):

    # Create the list of items that has been changed from CEA-3 to CEA-4
    list_items_changed = ['zone', 'surroundings',
                          'air_conditioning', 'architecture', 'indoor_comfort', 'internal_loads', 'supply_systems',
                          'typology']
    dict_missing = cea4_verify(scenario)

    #0. get the scenario name
    scenario_name = os.path.basename(scenario)

    COLUMNS_ZONE_3 = ['Name', 'floors_bg', 'floors_ag', 'height_bg', 'height_ag']
    CSV_BUILDING_PROPERTIES_3 = ['air_conditioning', 'architecture', 'indoor_comfort', 'internal_loads', 'supply_systems', 'typology']

    COLUMNS_TYPOLOGY_3 = ['Name', 'YEAR', 'STANDARD', '1ST_USE', '1ST_USE_R', '2ND_USE', '2ND_USE_R', '3RD_USE', '3RD_USE_R']
    COLUMNS_SURROUNDINGS_3 = ['Name', 'height_ag', 'floors_ag']
    COLUMNS_AIR_CONDITIONING_3 = ['Name',
                                'type_cs', 'type_hs', 'type_dhw', 'type_ctrl', 'type_vent',
                                'heat_starts', 'heat_ends', 'cool_starts', 'cool_ends']
    COLUMNS_ARCHITECTURE_3 = ['Name',
                            'Hs_ag', 'Hs_bg', 'Ns', 'Es', 'void_deck', 'wwr_north', 'wwr_west', 'wwr_east', 'wwr_south',
                            'type_cons', 'type_leak', 'type_floor', 'type_part', 'type_base', 'type_roof', 'type_wall',
                            'type_win', 'type_shade']
    COLUMNS_INDOOR_COMFORT_3 = ['Name',
                              'Tcs_set_C', 'Ths_set_C', 'Tcs_setb_C', 'Ths_setb_C', 'Ve_lsp', 'RH_min_pc', 'RH_max_pc']
    COLUMNS_INTERNAL_LOADS_3 = ['Name',
                              'Occ_m2p', 'Qs_Wp', 'X_ghp', 'Ea_Wm2', 'El_Wm2', 'Ed_Wm2', 'Ev_kWveh', 'Qcre_Wm2',
                              'Vww_ldp', 'Vw_ldp', 'Qhpro_Wm2', 'Qcpro_Wm2', 'Epro_Wm2']
    COLUMNS_SUPPLY_SYSTEMS_3 = ['Name',
                              'type_cs', 'type_hs', 'type_dhw', 'type_el']
    columns_mapping_dict_name = {'Name': 'name'}
    columns_mapping_dict_typology = {'YEAR': 'year',
                                     'STANDARD': 'const_type',
                                     '1ST_USE': 'use_type1',
                                     '1ST_USE_R': 'use_type1r',
                                     '2ND_USE': 'use_type2',
                                     '2ND_USE_R': 'use_type2r',
                                     '3RD_USE': 'use_type3',
                                     '3RD_USE_R': 'use_type3r'
                                     }
    # Verify missing files for CEA-3 format
    list_missing_files_shp_building_geometry = dict_missing.get('building-geometry')
    list_missing_files_dbf_building_properties = verify_file_exists_3(scenario, CSV_BUILDING_PROPERTIES_3)
    if list_missing_files_dbf_building_properties:
        print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'ensure .csv file(s) are present in the building-properties folder: {missing_files_csv_building_properties}'.format(missing_files_csv_building_properties=list_missing_files_csv_building_properties))

    # Verify missing attributes/columns for CEA-4 format
    list_missing_attributes_zone_4 = dict_missing.get('zone')
    list_missing_attributes_surroundings_4 = dict_missing.get('surroundings')

    #1. about zone.shp and surroundings.shp
    if 'zone' not in list_missing_files_shp_building_geometry:
        list_missing_attributes_zone_3 = verify_shp(scenario, 'zone', COLUMNS_ZONE_3)
        if not list_missing_attributes_zone_3 and list_missing_attributes_zone_4:
            print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'zone.shp follows the CEA-3 format.')
            zone_df_3 = gpd.read_file(path_to_input_file_without_db_3(scenario, 'zone'))
            zone_df_3.rename(columns=columns_mapping_dict_name, inplace=True)
            if 'typology' not in list_missing_files_dbf_building_properties:
                list_missing_attributes_typology_3 = verify_csv(scenario, 'typology', COLUMNS_TYPOLOGY_3)
                if not list_missing_attributes_typology_3 and list_missing_attributes_zone_4:
                    print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'typology.shp follows the CEA-3 format.')
                    typology_df = dbf_to_dataframe(path_to_input_file_without_db_3(scenario, 'typology'))
                    typology_df.rename(columns=columns_mapping_dict_typology, inplace=True)
                    zone_df_4 = pd.merge(zone_df_3, typology_df, left_on=['name'], right_on=["Name"], how='left')
                    zone_df_4.drop(columns=['Name'], inplace=True)
                    replace_shapefile_dbf(scenario, 'zone', zone_df_4, COLUMNS_ZONE_3)
                    print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'CEA-3 zone.shp and typology.dbf have been merged and migrated to CEA-4 format.')
                else:
                    raise ValueError('For Scenario: {scenario}, '.format(scenario=scenario_name),
                                     'typology.shp does not follow the CEA-3 format. CEA cannot proceed with migration. '
                                     'Check the following column(s) for CEA-3 format: {list_missing_attributes_typology_3}'.format(list_missing_attributes_typology_3=list_missing_attributes_typology_3))
        elif list_missing_attributes_zone_3 and not list_missing_attributes_zone_4:
            print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'zone.shp already follows the CEA-4 format.')
        else:
            raise ValueError('For Scenario: {scenario}, '.format(scenario=scenario_name), 'zone.shp follows neither the CEA-3 nor CEA-4 format. CEA cannot proceed with the data migration.')

    if 'surroundings' not in list_missing_files_shp_building_geometry:
        list_missing_attributes_surroundings_3 = verify_shp(scenario, 'surroundings', COLUMNS_SURROUNDINGS_3)
        if not list_missing_attributes_surroundings_3 and list_missing_attributes_surroundings_4:
            print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'surroundings.shp follows the CEA-3 format.')
            surroundings_df = gpd.read_file(path_to_input_file_without_db_3(scenario, 'surroundings'))
            surroundings_df.rename(columns=columns_mapping_dict_name, inplace=True)
            replace_shapefile_dbf(scenario, 'surroundings', surroundings_df, COLUMNS_SURROUNDINGS_3)

        elif list_missing_attributes_surroundings_3 and not list_missing_attributes_surroundings_4:
            print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'surroundings.shp already follows the CEA-4 format.')
        else:
            raise ValueError('For Scenario: {scenario}, '.format(scenario=scenario_name), 'surroundings.shp follows neither the CEA-3 nor CEA-4 format. CEA cannot proceed with the data migration.')

    #2. about the .dbf files in the building-properties folde to be mirgrated to .csv files
    if 'air_conditioning' not in list_missing_files_dbf_building_properties:
        list_missing_columns_air_conditioning = verify_dbf(scenario, 'air_conditioning', COLUMNS_AIR_CONDITIONING_3)
        if list_missing_columns_air_conditioning:
            print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'ensure column(s) are present in the air_conditioning.dbf: {missing_columns_air_conditioning}'.format(missing_columns_air_conditioning=list_missing_columns_air_conditioning))
        else:
            if 'Name' not in list_missing_columns_air_conditioning:
                list_names_duplicated = verify_name_duplicates(scenario, 'air_conditioning')
                if list_names_duplicated:
                    print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'ensure name(s) are unique in air_conditioning.dbf: {list_names_duplicated} is duplicated.'.format(list_names_duplicated=list_names_duplicated))
                else:
                    air_conditioning_df = dbf_to_dataframe(path_to_input_file_without_db_3(scenario, 'air_conditioning'))
                    air_conditioning_df.rename(columns=columns_mapping_dict_typology, inplace=True)
                    os.remove(path_to_input_file_without_db_3(scenario, 'air_conditioning'))
                    print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'CEA-3 air_conditioning.dbf has been migrated to CEA-4 format.')

    if 'architecture' not in list_missing_files_dbf_building_properties:
        list_missing_columns_architecture = verify_dbf(scenario, 'architecture', COLUMNS_ARCHITECTURE_3)
        if list_missing_columns_architecture:
            print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'ensure column(s) are present in the architecture.dbf: {missing_columns_architecture}'.format(missing_columns_architecture=list_missing_columns_architecture))
        else:
            if 'Name' not in list_missing_columns_architecture:
                list_names_duplicated = verify_name_duplicates(scenario, 'architecture')
                if list_names_duplicated:
                    print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'ensure name(s) are unique in architecture.dbf: {list_names_duplicated} is duplicated.'.format(list_names_duplicated=list_names_duplicated))
                else:
                    architecture_df = dbf_to_dataframe(path_to_input_file_without_db_3(scenario, 'architecture'))
                    architecture_df.rename(columns=columns_mapping_dict_typology, inplace=True)
                    os.remove(path_to_input_file_without_db_3(scenario, 'architecture'))
                    print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'CEA-3 architecture.dbf has been migrated to CEA-4 format.')

    if 'indoor_comfort' not in list_missing_files_dbf_building_properties:
        list_missing_columns_indoor_comfort = verify_dbf(scenario, 'indoor_comfort', COLUMNS_INDOOR_COMFORT_3)
        if list_missing_columns_indoor_comfort:
            print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'ensure column(s) are present in the air_conditioning.dbf: {missing_columns_indoor_comfort}'.format(missing_columns_indoor_comfort=list_missing_columns_indoor_comfort))
        else:
            if 'Name' not in list_missing_columns_indoor_comfort:
                list_names_duplicated = verify_name_duplicates(scenario, 'indoor_comfort')
                if list_names_duplicated:
                    print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'ensure name(s) are unique in indoor_comfort.dbf: {list_names_duplicated} is duplicated.'.format(list_names_duplicated=list_names_duplicated))
                else:
                    indoor_comfort_df = dbf_to_dataframe(path_to_input_file_without_db_3(scenario, 'indoor_comfort'))
                    indoor_comfort_df.rename(columns=columns_mapping_dict_typology, inplace=True)
                    os.remove(path_to_input_file_without_db_3(scenario, 'indoor_comfort'))
                    print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'CEA-3 indoor_comfort.dbf has been migrated to CEA-4 format.')

    if 'internal_loads' not in list_missing_files_dbf_building_properties:
        list_missing_columns_internal_loads = verify_dbf(scenario, 'internal_loads', COLUMNS_INTERNAL_LOADS_3)
        if list_missing_columns_internal_loads:
            print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'ensure column(s) are present in the internal_loads.dbf: {missing_columns_internal_loads}'.format(missing_columns_internal_loads=list_missing_columns_internal_loads))
        else:
            if 'Name' not in list_missing_columns_internal_loads:
                list_names_duplicated = verify_name_duplicates(scenario, 'internal_loads')
                if list_names_duplicated:
                    print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'ensure name(s) are unique in internal_loads.dbf: {list_names_duplicated} is duplicated.'.format(list_names_duplicated=list_names_duplicated))
                else:
                    internal_loads_df = dbf_to_dataframe(path_to_input_file_without_db_3(scenario, 'internal_loads'))
                    internal_loads_df.rename(columns=columns_mapping_dict_typology, inplace=True)
                    os.remove(path_to_input_file_without_db_3(scenario, 'internal_loads'))
                    print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'CEA-3 internal_loads.dbf has been migrated to CEA-4 format.')

    if 'supply_systems' not in list_missing_files_dbf_building_properties:
        list_missing_columns_supply_systems = verify_dbf(scenario, 'supply_systems', COLUMNS_SUPPLY_SYSTEMS_3)
        if list_missing_columns_supply_systems:
            print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'ensure column(s) are present in the supply_systems.dbf: {missing_columns_supply_systems}'.format(missing_columns_supply_systems=list_missing_columns_supply_systems))
        else:
            if 'Name' not in list_missing_columns_supply_systems:
                list_names_duplicated = verify_name_duplicates(scenario, 'supply_systems')
                if list_names_duplicated:
                    print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'ensure name(s) are unique in supply_systems.dbf: {list_names_duplicated} is duplicated.'.format(list_names_duplicated=list_names_duplicated))
                else:
                    supply_systems_df = dbf_to_dataframe(path_to_input_file_without_db_3(scenario, 'supply_systems'))
                    supply_systems_df.rename(columns=columns_mapping_dict_typology, inplace=True)
                    os.remove(path_to_input_file_without_db_3(scenario, 'supply_systems'))
                    print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'CEA-3 supply_systems.dbf has been migrated to CEA-4 format.')

    if 'typology' not in list_missing_files_dbf_building_properties:
        os.remove(path_to_input_file_without_db_3(scenario, 'typology'))
        print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'CEA-3 typology.dbf has been removed as it is no longer needed by CEA-4.')

    #3. about the Database



## --------------------------------------------------------------------------------------------------------------------
## Main function
## --------------------------------------------------------------------------------------------------------------------


def main(config):
    # Start the timer
    t0 = time.perf_counter()
    assert os.path.exists(config.general.project), 'input file not found: %s' % config.project

    # Execute the verification
    migrate_cea3_to_cea4(scenario=config.scenario)

    # Execute the verification
    print("A final step to verify if all the data is in the correct format for CEA-4.")
    cea4_verify(scenario=config.scenario)

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire process of data migration from CEA-3 to CEA-4 is now completed - time elapsed: %d.2 seconds' % time_elapsed)

if __name__ == '__main__':
    main(cea.config.Configuration())

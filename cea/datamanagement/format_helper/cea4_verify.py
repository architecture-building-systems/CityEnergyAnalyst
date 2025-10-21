"""
Verify the format of the input data for CEA-4 model.

"""

import os
from typing import Dict, List
import cea.config
import time
import geopandas as gpd
import pandas as pd
from cea.schemas import schemas
import numpy as np

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


SHAPEFILES = ['zone', 'surroundings']
COLUMNS_ZONE_4 = ['name', 'floors_bg', 'floors_ag', 'void_deck', 'height_bg', 'height_ag',
                'year', 'const_type', 'use_type1', 'use_type1r', 'use_type2', 'use_type2r', 'use_type3', 'use_type3r']
CSV_BUILDING_PROPERTIES_3 = ['air_conditioning', 'architecture', 'indoor_comfort', 'internal_loads', 'supply_systems']
CSV_BUILDING_PROPERTIES_4 = ['hvac', 'envelope', 'indoor_comfort', 'internal_loads', 'supply']
CSV_BUILDING_PROPERTIES_3_CSV = ['air_conditioning_csv', 'architecture_csv', 'supply_systems_csv']
dict_mapping_building_properties = {'air_conditioning': 'hvac',
                                    'architecture': 'envelope',
                                    'indoor_comfort': 'indoor_comfort',
                                    'internal_loads': 'internal_loads',
                                    'supply_systems': 'supply'}
mapping_dict_input_item_to_schema_locator = {'zone': 'get_zone_geometry',
                                             'surroundings': 'get_surroundings_geometry',
                                             'terrain': 'get_terrain',
                                             'weather': 'get_weather',
                                             'internal_loads': 'get_building_internal',
                                             'air_conditioning': 'get_building_air_conditioning',
                                             'supply_systems': 'get_building_supply',
                                             'architecture': 'get_building_architecture',
                                             'envelope': 'get_building_architecture',
                                             'hvac': 'get_building_air_conditioning',
                                             'supply': 'get_building_supply',
                                             'indoor_comfort': 'get_building_comfort',
                                             'streets': 'get_street_network',
                                             'schedules': 'get_building_weekly_schedules',
                                             'MONTHLY_MULTIPLIERS': 'get_building_property_schedules_monthly_multiplier'
                                             }

mapping_dict_input_item_to_id_column = {'zone': 'name',
                                        'surroundings': 'name',
                                        'terrain': '',
                                        'weather': '',
                                        'internal_loads': 'name',
                                        'air_conditioning': 'name',
                                        'hvac': 'name',
                                        'envelope': 'name',
                                        'supply': 'name',
                                        'supply_systems': 'name',
                                        'architecture': 'name',
                                        'indoor_comfort': 'name',
                                        'streets': '',
                                        'schedules': 'hour',
                                        'MONTHLY_MULTIPLIERS': 'code'
                                        }


## --------------------------------------------------------------------------------------------------------------------
## The paths to the input files for CEA-4
## --------------------------------------------------------------------------------------------------------------------

# The paths are relatively hardcoded for now without using the inputlocator script.
# This is because we want to iterate over all scenarios, which is currently not possible with the inputlocator script.
def path_to_input_file_without_db_4(scenario, item, building_name=None):

    if item == "zone":
        path_to_input_file = os.path.join(scenario, "inputs", "building-geometry", "zone.shp")
    elif item == "surroundings":
        path_to_input_file = os.path.join(scenario, "inputs", "building-geometry", "surroundings.shp")
    elif item == "air_conditioning":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "hvac.csv")
    elif item == "hvac":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "hvac.csv")
    elif item == "architecture":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "envelope.csv")
    elif item == "envelope":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "envelope.csv")
    elif item == "indoor_comfort":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "indoor_comfort.csv")
    elif item == "internal_loads":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "internal_loads.csv")
    elif item == "supply_systems":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "supply.csv")
    elif item == "supply":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "supply.csv")
    elif item == 'streets':
        path_to_input_file = os.path.join(scenario, "inputs", "networks", "streets.shp")
    elif item == 'terrain':
        path_to_input_file = os.path.join(scenario, "inputs", "topography", "terrain.tif")
    elif item == 'weather':
        path_to_input_file = os.path.join(scenario, "inputs", "weather", "weather.epw")
    elif item == 'schedules':
        if building_name is None:
            path_to_input_file = os.path.join(scenario, "inputs", "building-properties", 'schedules')
        else:
            path_to_input_file = os.path.join(scenario, "inputs", "building-properties", 'schedules', "{building}.csv".format(building=building_name))
    elif item == 'MONTHLY_MULTIPLIERS':
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "schedules", "MONTHLY_MULTIPLIERS.csv")
    else:
        raise ValueError(f"Unknown item {item}")

    return path_to_input_file


## --------------------------------------------------------------------------------------------------------------------
## Helper functions
## --------------------------------------------------------------------------------------------------------------------

def verify_file_against_schema_4(scenario, item, building_name=None):
    """
    Validate a file against a schema section in a YAML file.

    Parameters:
    - scenario (str): Path to the scenario.
    - item (str): Locator for the file to validate (e.g., 'get_zone_geometry').
    - building_name (str, optional): If provided, validates a specific building file.

    Returns:
    - Tuple[List[str], List[str]]: Missing columns and validation error messages.
    """
    schema = schemas()

    # Determine file path
    if building_name is None:
        file_path = path_to_input_file_without_db_4(scenario, item)
    else:
        file_path = path_to_input_file_without_db_4(scenario, item, building_name=building_name)

    locator = mapping_dict_input_item_to_schema_locator[item]
    schema_section = schema.get(locator, {})
    schema_columns = schema_section.get('schema', {}).get('columns', {})
    id_column = mapping_dict_input_item_to_id_column[item]

    # Determine file type and load the data
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.shp'):
            gdf = gpd.read_file(file_path)
            df = pd.DataFrame(gdf.drop(columns=['geometry'], errors='ignore'))  # Drop geometry safely
        else:
            raise ValueError(f"Unsupported file type: {file_path}. Only .csv and .shp files are supported.")
    except Exception as e:
        raise ValueError(f"Failed to read file: {file_path}. Error: {e}")

    errors = []
    missing_columns = [col for col in schema_columns if col not in df.columns]

    # Remove 'geometry' and 'reference' from missing columns
    missing_columns = [col for col in missing_columns if col.lower() not in ['geometry', 'reference']]

    # Ensure ID column exists before using it
    if id_column not in df.columns:
        if 'Name' in df.columns:
            errors.append(f"- Missing required identifier column: '{id_column}'. CEA-4 uses 'name' as the identifier for buildings instead of 'Name'. In most cases, CEA should be able to handle this automatically. However, if you see this message, it means that a manual fix is required.")
        else:
            errors.append(f"- Missing required identifier column: '{id_column}'.")
        return missing_columns, errors  # Stop further validation if ID column is missing

    # Validation process
    for col_name, col_specs in schema_columns.items():
        if col_name not in df.columns:
            continue  # Already captured in `missing_columns`

        col_data = df[col_name]

        # Type validation
        expected_type = col_specs.get('type')
        if expected_type == 'string':
            invalid = ~col_data.apply(lambda x: isinstance(x, str) or pd.isnull(x))
        elif expected_type == 'int':
            invalid = ~col_data.apply(lambda x: isinstance(x, (int, np.integer)) or pd.isnull(x))
        elif expected_type == 'float':
            invalid = ~col_data.apply(lambda x: isinstance(x, (float, int, np.floating, np.integer)) or pd.isnull(x))
        else:
            invalid = pd.Series(False, index=col_data.index)  # Skip unknown types

        for idx in invalid[invalid].index:
            identifier = df.at[idx, id_column]
            errors.append(f"- The {col_name} value for row {identifier} is invalid ({col_data[idx]}). Please check the data type.")

        # Range validation
        min_value = col_specs.get('min')
        max_value = col_specs.get('max')

        if min_value is not None:
            out_of_range = col_data[col_data < min_value]
            for idx, value in out_of_range.items():
                identifier = df.at[idx, id_column]
                errors.append(f"- The {col_name} value for row {identifier} is too low ({value}). It should be at least {min_value}.")

        if max_value is not None:
            out_of_range = col_data[col_data > max_value]
            for idx, value in out_of_range.items():
                identifier = df.at[idx, id_column]
                errors.append(f"- The {col_name} value for row {identifier} is too high ({value}). It should be at most {max_value}.")

    return missing_columns, errors


def verify_shp(scenario, item, required_attributes):
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
    shapefile_path = path_to_input_file_without_db_4(scenario, item)

    # Check if the shapefile exists
    if not os.path.isfile(shapefile_path):
        raise FileNotFoundError(f"Shapefile not found: {shapefile_path}")

    # Load the shapefile
    try:
        gdf = gpd.read_file(shapefile_path)
    except Exception as e:
        raise ValueError(f"Error reading shapefile: {e}")

    # Get the column names from the shapefile's attribute table
    shapefile_columns = gdf.columns.tolist()

    # Check for missing attributes
    missing_attributes = [attr for attr in required_attributes if attr not in shapefile_columns]

    return missing_attributes


def verify_csv_4(scenario, item, required_columns):
    """
    Verify if a CSV file contains all required columns.

    Parameters:
        scenario (str): Path or identifier for the scenario.
        item (str): Identifier for the CSV file.
        required_columns (list): List of column names to verify.

    Returns:
        A list of missing columns, or an empty list if all columns are present.
    """
    # Construct the CSV file path
    csv_path = path_to_input_file_without_db_4(scenario, item)

    # Check if the CSV file exists
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Load the CSV file
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")

    # Get the column names from the CSV file
    csv_columns = df.columns.tolist()

    # Check for missing columns
    missing_columns = [col for col in required_columns if col not in csv_columns]

    return missing_columns


def verify_file_exists_4(scenario, items, building_names=None):
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
        if building_names is None:
            path = path_to_input_file_without_db_4(scenario, file)
            if not os.path.isfile(path):
                list_missing_files.append(file)
        else:
            for building_name in building_names:
                path = path_to_input_file_without_db_4(scenario, file, building_name)
                if not os.path.isfile(path):
                    list_missing_files.append(building_name)
    return list_missing_files


def verify_name_duplicates_4(scenario, item):
    """
    Verify if there are duplicate names in the 'name' column of a .csv or .shp file.

    Parameters:
        file_path (str): Path to the input file (either .csv or .shp).

    Returns:
        list: A list of duplicate names, or an empty list if no duplicates are found.
    """
    # Construct the CSV file path
    file_path = path_to_input_file_without_db_4(scenario, item)

    # Check file type and load as a DataFrame
    if file_path.endswith('.csv'):
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {e}")
    elif file_path.endswith('.shp'):
        try:
            df = gpd.read_file(file_path)
        except Exception as e:
            raise ValueError(f"Error reading shapefile: {e}")
    else:
        raise ValueError("Unsupported file type. Please provide a .csv or .shp file.")

    # Find duplicate names
    list_names_duplicated = df['name'][df['name'].duplicated()].tolist()

    return list_names_duplicated


def print_verification_results_4(scenario_name, dict_missing):

    if all(not value for value in dict_missing.values()):
        print("✓" * 3)
        print('All inputs are verified as present and compatible with the current version of CEA-4 for Scenario: {scenario}.'.format(scenario=scenario_name))
    else:
        print("!" * 3)
        print('All or some of input data files/columns are missing or incompatible with the current version of CEA-4 for Scenario: {scenario}. '.format(scenario=scenario_name))
        print('- If you are migrating your input data from CEA-3 to CEA-4 format, set the toggle `migrate_from_cea_3` to `True` for Feature CEA-4 Format Helper and click on Run. ')
        print('- If you manually prepared the input data, check the log for missing files and/or incompatible columns. Modify your input data accordingly. Otherwise, all CEA simulations will fail.')


def verify_csv_file(scenario, item, required_columns, verbose=False):
    """
    Verify a CSV file's columns and name uniqueness.

    Args:
        scenario: The scenario path
        item: The item name (e.g., 'air_conditioning')
        required_columns: List of required columns
        verbose: Whether to print verification results

    Returns:
        list: List of missing columns
    """
    list_missing_columns = verify_csv_4(scenario, item, required_columns)
    if list_missing_columns:
        if verbose:
            print(f'! Ensure column(s) are present in the {item}.csv: {list_missing_columns}')
    else:
        if 'name' not in list_missing_columns:
            list_names_duplicated = verify_name_duplicates_4(scenario, item)
            if list_names_duplicated and verbose:
                print(f'! Ensure name(s) are unique in {item}.csv: {list_names_duplicated} is duplicated.')
    return list_missing_columns


def get_shapefile_names(scenario):
    """
    Reads a shapefile and returns a list of unique names from the 'name' column.

    Parameters:
    - scenario: The scenario path

    Returns:
    - list: A list of names from the 'name' column.
    """
    shapefile_path = path_to_input_file_without_db_4(scenario, 'zone')
    try:
        # Load the shapefile
        gdf = gpd.read_file(shapefile_path)

        # Ensure 'name' column exists
        if 'name' in gdf.columns:
            return gdf['name'].dropna().astype(str).unique().tolist()
        elif 'Name' in gdf.columns:
            return gdf['Name'].dropna().astype(str).unique().tolist()
        else:
            raise ValueError(f"neither 'name' nor 'Name' column not found in {shapefile_path}")

    except Exception as e:
        print(f"Error reading shapefile: {e}")
        return []


def add_values_to_dict(existing_dict, key, values):
    """
    Add or append values to a dictionary key. If the key does not exist, it will be created.

    Parameters:
    - existing_dict (dict): The dictionary to update.
    - key: The key where values should be added.
    - values (list): A list of values to add.

    Returns:
    - None: Updates the dictionary in place.
    """
    if key not in existing_dict:
        # If key does not exist, create it with the new values as a list
        existing_dict[key] = values if isinstance(values, list) else [values]
    else:
        # If the key exists, extend the list of values
        if not isinstance(existing_dict[key], list):
            # Ensure the current value is a list
            existing_dict[key] = [existing_dict[key]]
        # Extend the list with the new values
        if isinstance(values, list):
            existing_dict[key].extend(values)
        else:
            existing_dict[key].append(values)

## --------------------------------------------------------------------------------------------------------------------
## Unique traits for the CEA-4 format
## --------------------------------------------------------------------------------------------------------------------

def cea4_verify(scenario, verbose=False) -> Dict[str, List[str]]:

    #1. about zone.shp and surroundings.shp
    list_missing_attributes_zone = []
    list_missing_attributes_surroundings = []
    list_missing_files_shp_building_geometry = verify_file_exists_4(scenario, SHAPEFILES)

    if 'zone' not in list_missing_files_shp_building_geometry:
        list_missing_attributes_zone, list_issues_against_schema_zone = verify_file_against_schema_4(scenario, 'zone')
        list_names_zone = get_shapefile_names(scenario)
        if list_missing_attributes_zone:
            if verbose:
                print('! Ensure attribute(s) are present in zone.shp: {missing_attributes_zone}.'.format(missing_attributes_zone=', '.join(map(str, list_missing_attributes_zone))))
                if list_issues_against_schema_zone:
                    print('! Check values in zone.shp:')
                    print("\n".join(f"  {item}" for item in list_issues_against_schema_zone))
        if 'name' not in list_missing_attributes_zone:
            list_names_duplicated = verify_name_duplicates_4(scenario, 'zone')
            if list_names_duplicated:
                if verbose:
                    print('! Ensure name(s) are unique in zone.shp: {list_names_duplicated} is duplicated.'.format(list_names_duplicated=', '.join(map(str, list_names_duplicated))))
    else:
        list_names_zone = []

    if 'surroundings' not in list_missing_files_shp_building_geometry:
        list_missing_attributes_surroundings, list_issues_against_schema_surroundings = verify_file_against_schema_4(scenario, 'surroundings')
        if list_missing_attributes_surroundings:
            if verbose:
                print('! Ensure attribute(s) are present in surroundings.shp: {missing_attributes_surroundings}.'.format(missing_attributes_surroundings=', '.join(map(str, list_missing_attributes_surroundings))))
                if list_issues_against_schema_surroundings:
                    print('! Check values in surroundings.shp:')
                    print("\n".join(f"  {item}" for item in list_issues_against_schema_surroundings))
        if 'name' not in list_missing_attributes_surroundings:
            list_names_duplicated = verify_name_duplicates_4(scenario, 'surroundings')
            if list_names_duplicated:
                if verbose:
                    print('! Ensure name(s) are unique in surroundings.shp: {list_names_duplicated} is duplicated.'.format(list_names_duplicated=', '.join(map(str, list_names_duplicated))))

    #2. about .csv files under the "inputs/building-properties" folder
    dict_list_missing_columns_csv_building_properties = {}

    list_missing_files_csv_building_properties_4 = verify_file_exists_4(scenario, CSV_BUILDING_PROPERTIES_4)
    if list_missing_files_csv_building_properties_4:
        if verbose:
            print('! Ensure .csv file(s) are present in the building-properties folder: {missing_files_csv_building_properties}.'.format(missing_files_csv_building_properties=', '.join(map(str, list_missing_files_csv_building_properties_4))))

    for item in CSV_BUILDING_PROPERTIES_4:
        if item not in list_missing_files_csv_building_properties_4:
            list_missing_columns_csv_building_properties, list_issues_against_csv_building_properties = verify_file_against_schema_4(scenario, item)
            dict_list_missing_columns_csv_building_properties[item] = list_missing_columns_csv_building_properties + list_issues_against_csv_building_properties
            if verbose:
                if list_missing_columns_csv_building_properties:
                    print('! Ensure column(s) are present in {item}.csv: {missing_columns}.'.format(item=item, missing_columns=', '.join(map(str, list_missing_columns_csv_building_properties))))
                if list_issues_against_csv_building_properties:
                    print('! Check values in {item}.csv: '.format(item=item))
                    print("\n".join(f"  {item}" for item in list_issues_against_csv_building_properties))
        else:
            dict_list_missing_columns_csv_building_properties[item] = []
    #2A. about .csv files under the "inputs/building-properties/schedules" folder
    list_missing_files_csv_building_properties_schedules_building = verify_file_exists_4(scenario, ['schedules'], list_names_zone)
    list_missing_files_csv_building_properties_schedules_monthly_multipliers = verify_file_exists_4(scenario, ['MONTHLY_MULTIPLIERS'])
    list_missing_files_csv_building_properties_schedules = list_missing_files_csv_building_properties_schedules_building + list_missing_files_csv_building_properties_schedules_monthly_multipliers
    if list_missing_files_csv_building_properties_schedules:
        if verbose:
            print('! Ensure .csv file(s) are present in building-properties/schedules folder: {list_missing_files_csv_building_properties_schedules}.'.format(list_missing_files_csv_building_properties_schedules=', '.join(map(str, list_missing_files_csv_building_properties_schedules))))
    # Schedules that exist in schedules folder
    dict_list_missing_items_building_properties_schedules = {}
    list_files_csv_building_properties_schedules = [item for item in list_names_zone if item not in list_missing_files_csv_building_properties_schedules]
    for schedule in list_files_csv_building_properties_schedules:
        list_missing_columns_schedules, list_issues_against_schema_schedules = verify_file_against_schema_4(scenario, 'schedules', building_name=schedule)
        if list_missing_columns_schedules:
            add_values_to_dict(dict_list_missing_items_building_properties_schedules, schedule, list_missing_columns_schedules)
            if verbose:
                print('! Ensure column(s) are present in {schedule}.csv: {missing_attributes_surroundings}.'.format(schedule=schedule, missing_attributes_surroundings=', '.join(map(str, list_missing_columns_schedules))))
                if list_issues_against_schema_schedules:
                    add_values_to_dict(dict_list_missing_items_building_properties_schedules, schedule, list_issues_against_schema_schedules)
                    print('! Check values in {schedule}.csv:'.format(schedule=schedule))
                    print("\n".join(f"  {item}" for item in list_issues_against_schema_schedules))
    if not list_missing_files_csv_building_properties_schedules_monthly_multipliers:
        list_missing_columns_schedules_monthly_multipliers, list_issues_against_schema_schedules_monthly_multipliers = verify_file_against_schema_4(scenario, 'MONTHLY_MULTIPLIERS')
        if list_missing_columns_schedules_monthly_multipliers:
            if verbose:
                print('! Ensure column(s) are present in monthly-multipliers.csv: {missing_attributes_surroundings}.'.format(missing_attributes_surroundings=', '.join(map(str, list_missing_columns_schedules_monthly_multipliers))))
                if list_issues_against_schema_schedules_monthly_multipliers:
                    print('! Check values in monthly-multipliers.csv:')
                    print("\n".join(f"  {item}" for item in list_issues_against_schema_schedules_monthly_multipliers))
    else:
        list_missing_columns_schedules_monthly_multipliers = []
    #3. verify if terrain.tif, weather.epw and streets.shp exist
    list_missing_files_terrain = verify_file_exists_4(scenario, ['terrain'])
    if list_missing_files_terrain:
        if verbose:
            print('! Ensure terrain.tif are present in the typography folder. Consider running Terrain Helper under Data Management.')

    list_missing_files_weather = verify_file_exists_4(scenario, ['weather'])
    if list_missing_files_weather:
        if verbose:
            print('! Ensure weather.epw are present in the weather folder. Consider running Weather Helper under Data Management.')

    list_missing_files_streets = verify_file_exists_4(scenario, ['streets'])
    if list_missing_files_streets:
        if verbose:
            print('! Ensure streets.shp are present in the networks folder, if Thermal-Networks analysis is required. Consider running Streets Helper under Data Management.')

    #4. verify the DB under the "inputs/technology/" folder
    list_missing_files_db = []

    # Compile the results
    dict_missing = {
        'building-geometry': list_missing_files_shp_building_geometry,
        'zone': list_missing_attributes_zone,
        'surroundings': list_missing_attributes_surroundings,
        'building-properties': list_missing_files_csv_building_properties_4,
        'schedules': list_missing_files_csv_building_properties_schedules,
        'buildings':  dict_list_missing_items_building_properties_schedules,
        'monthly_multipliers': list_missing_columns_schedules_monthly_multipliers,
        'hvac': dict_list_missing_columns_csv_building_properties['hvac'],  # previously 'air_conditioning'
        'envelope': dict_list_missing_columns_csv_building_properties['envelope'],  # previously 'architecture'
        'indoor_comfort': dict_list_missing_columns_csv_building_properties['indoor_comfort'],
        'internal_loads': dict_list_missing_columns_csv_building_properties['internal_loads'],
        'supply': dict_list_missing_columns_csv_building_properties['supply'],  # previously 'supply_systems'
        'terrain': list_missing_files_terrain,
        'weather': list_missing_files_weather,
        'streets': list_missing_files_streets,
        'db': list_missing_files_db
    }

    # # Print: End
    # if verbose:
    #     print("-" * 39)

    return dict_missing


## --------------------------------------------------------------------------------------------------------------------
## Main function
## --------------------------------------------------------------------------------------------------------------------


def main(config: cea.config.Configuration):
    # Start the timer
    t0 = time.perf_counter()
    assert os.path.exists(config.general.project), 'input file not found: %s' % config.project

    # Get the scenario name
    scenario = config.scenario
    scenario_name = os.path.basename(scenario)

    # Print: Start
    div_len = 37 - len(scenario_name)
    print('+' * 60)
    print("-" * 1 + ' Scenario: {scenario} '.format(scenario=scenario_name) + "-" * div_len)

    # Execute the verification
    dict_missing = cea4_verify(scenario, verbose=True)

    # Print the results
    print_verification_results_4(scenario_name, dict_missing)

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0

    # Print: End
    print('+' * 60)
    print('The entire process of CEA-4 format verification is now completed - time elapsed: %.2f seconds' % time_elapsed)

if __name__ == '__main__':
    main(cea.config.Configuration())

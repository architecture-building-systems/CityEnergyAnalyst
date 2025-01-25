"""
Verify the format of DB for CEA-4 model.

"""


import os
import cea.config
import time
import pandas as pd
import numpy as np
from cea.schemas import schemas
import sys


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.datamanagement.format_helper.cea4_verify import verify_file_against_schema_4

ARCHETYPES = ['CONSTRUCTION_TYPE', 'USE_TYPE']
SCHEDULES_FOLDER = ['SCHEDULES']
ENVELOPE_ASSEMBLIES = ['CONSTRUCTION', 'TIGHTNESS', 'FLOOR', 'WALL', 'WINDOW', 'SHADING', 'ROOF']
HVAC_ASSEMBLIES = ['CONTROLLER', 'HOT_WATER', 'HEATING', 'COOLING', 'VENTILATION']
SUPPLY_ASSEMBLIES = ['COOLING', 'ELECTRICITY', 'HEATING', 'HOT_WATER']
CONVERSION_COMPONENTS = ['CONVERSION']
DISTRIBUTION_COMPONENTS = ['THERMAL_GRID']
FEEDSTOCKS_COMPONENTS = ['BIOGAS', 'COAL', 'DRYBIOMASS', 'ENERGY_CARRIERS', 'GRID', 'HYDROGEN', 'NATURALGAS', 'OIL', 'SOLAR', 'WETBIOMASS', 'WOOD']
dict_envelope = {'CONSTRUCTION': 'type_cons', 'TIGHTNESS': 'type_leak', 'FLOOR': 'type_floor', 'WALL': 'type_wall', 'WINDOW': 'type_win', 'SHADING': 'type_shade', 'ROOF': 'type_roof'}
ASSEMBLIES_FOLDERS = ['ENVELOPE', 'HVAC', 'SUPPLY']
COMPONENTS_FOLDERS = ['CONVERSION', 'DISTRIBUTION', 'FEEDSTOCKS']
dict_assembly = {'ENVELOPE': ENVELOPE_ASSEMBLIES, 'HVAC': HVAC_ASSEMBLIES, 'SUPPLY': SUPPLY_ASSEMBLIES}
mapping_dict_db_item_to_schema_locator = {'CONSTRUCTION_TYPE': 'get_database_archetypes_construction_type',
                                          'USE_TYPE': 'get_database_archetypes_use_type',
                                          'SCHEDULES': 'get_database_archetypes_schedules',
                                          'CONSTRUCTION': 'get_database_assemblies_envelope_construction',
                                          'MASS': 'get_database_assemblies_envelope_mass',
                                          'FLOOR': 'get_database_assemblies_envelope_floor',
                                          'WALL': 'get_database_assemblies_envelope_wall',
                                          'WINDOW': 'get_database_assemblies_envelope_window',
                                          'SHADING': 'get_database_assemblies_envelope_shading',
                                          'ROOF': 'get_database_assemblies_envelope_roof',
                                          'TIGHTNESS': 'get_database_assemblies_envelope_tightness',
                                          'HVAC_CONTROLLER': 'get_database_assemblies_hvac_controller',
                                          'HVAC_COOLING': 'get_database_assemblies_hvac_cooling',
                                          'HVAC_HEATING': 'get_database_assemblies_hvac_heating',
                                          'HVAC_HOT_WATER': 'get_database_assemblies_hvac_hot_water',
                                          'HVAC_VENTILATION': 'get_database_assemblies_hvac_ventilation',
                                          'SUPPLY_COOLING': 'get_database_assemblies_supply_cooling',
                                          'SUPPLY_HEATING': 'get_database_assemblies_supply_heating',
                                          'SUPPLY_HOT_WATER': 'get_database_assemblies_supply_hot_water',
                                          'SUPPLY_ELECTRICITY': 'get_database_assemblies_supply_electricity',
                                          'CONVERSION': 'get_conversion_db',
                                          'DISTRIBUTION': 'get_distribution_db',
                                          'FEEDSTOCKS': 'get_feedstocks_db',
                                          }

mapping_dict_db_item_to_id_column = {'CONSTRUCTION_TYPE': 'name'

                                     }


## --------------------------------------------------------------------------------------------------------------------
## The paths to the input files for CEA-4
## --------------------------------------------------------------------------------------------------------------------

# The paths are relatively hardcoded for now without using the inputlocator script.
# This is because we want to iterate over all scenarios, which is currently not possible with the inputlocator script.
def path_to_db_file_4(scenario, item, sheet_name=None):

    if item == "CONSTRUCTION_TYPE":
        path_db_file = os.path.join(scenario, "inputs", "database", "ARCHETYPES", "CONSTRUCTION_TYPE.csv")
    elif item == "USE_TYPE":
        path_db_file = os.path.join(scenario, "inputs",  "database", "ARCHETYPES", "USE_TYPE.csv")
    elif item == "SCHEDULES":
        if sheet_name is None:
            path_db_file = os.path.join(scenario, "inputs", "database", "ARCHETYPES", "SCHEDULES")
        else:
            path_db_file = os.path.join(scenario, "inputs", "database", "ARCHETYPES", "SCHEDULES", "{use_type}.csv".format(use_type=sheet_name))
    elif item == "MONTHLY_MULTIPLIER":
        path_db_file = os.path.join(scenario, "inputs", "database", "ARCHETYPES", "SCHEDULES", "MONTHLY_MULTIPLIER.csv")
    elif item == "ENVELOPE":
        if sheet_name is None:
            path_db_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "ENVELOPE")
        else:
            path_db_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "ENVELOPE", "{envelope_assemblies}.csv".format(envelope_assemblies=sheet_name))
    elif item == "HVAC":
        if sheet_name is None:
            path_db_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "HVAC")
        else:
            path_db_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "HVAC", "{hvac_assemblies}.csv".format(hvac_assemblies=sheet_name))
    elif item == "SUPPLY":
        if sheet_name is None:
            path_db_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "SUPPLY")
        else:
            path_db_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "SUPPLY", "{supply_assemblies}.csv".format(supply_assemblies=sheet_name))
    elif item == "CONVERSION":
        if sheet_name is None:
            path_db_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "CONVERSION")
        else:
            path_db_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "CONVERSION", "{conversion_components}.csv".format(conversion_components=sheet_name))
    elif item == "DISTRIBUTION":
        if sheet_name is None:
            path_db_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "DISTRIBUTION")
        else:
            path_db_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "DISTRIBUTION", "{distribution_components}.csv".format(distribution_components=sheet_name))
    elif item == "FEEDSTOCKS":
        if sheet_name is None:
            path_db_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "FEEDSTOCKS")
        else:
            path_db_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "FEEDSTOCKS", "{feedstocks_components}.csv".format(feedstocks_components=sheet_name))
    else:
        raise ValueError(f"Unknown item {item}")

    return path_db_file


## --------------------------------------------------------------------------------------------------------------------
## Helper functions
## --------------------------------------------------------------------------------------------------------------------

def verify_file_against_schema_4_db(scenario, item, verbose=True, sheet_name=None):
    """
    Validate a file against a schema section in a YAML file.

    Parameters:
    - scenario (str): Path to the scenario.
    - item (str): Locator for the file to validate (e.g., 'get_zone_geometry').
    - self: Reference to the calling class/module.
    - verbose (bool, optional): If True, print validation errors to the console.

    Returns:
    - List[dict]: List of validation errors.
    """
    schema = schemas()

    # File path and schema section
    file_path = path_to_db_file_4(scenario, item, sheet_name)
    locator = mapping_dict_db_item_to_schema_locator[item]

    schema_section = schema[locator]
    schema_columns = schema_section['schema']['columns']
    id_column = mapping_dict_db_item_to_id_column[item]

    # Determine file type and load the data
    if file_path.endswith('.csv'):
        try:
            df = pd.read_csv(file_path)
            col_attr = 'Column'
        except Exception as e:
            raise ValueError(f"Failed to read .csv file: {file_path}. Error: {e}")
    else:
        raise ValueError(f"Unsupported file type: {file_path}. Only .csv files are supported.")

    if id_column not in df.columns:
        raise ValueError(f"A unique row identifier column such as (building) name or (component) code is not present in the file.")

    errors = []
    missing_columns = []

    # Validation process
    for col_name, col_specs in schema_columns.items():
        if col_name not in df.columns:
            missing_columns.append(col_name)
            continue

        col_data = df[col_name]

        # Check type
        if col_specs['type'] == 'string':
            invalid = ~col_data.apply(lambda x: isinstance(x, str) or pd.isnull(x))
        elif col_specs['type'] == 'int':
            invalid = ~col_data.apply(lambda x: isinstance(x, (int, np.integer)) or pd.isnull(x))
        elif col_specs['type'] == 'float':
            invalid = ~col_data.apply(lambda x: isinstance(x, (float, int, np.floating, np.integer)) or pd.isnull(x))
        else:
            invalid = pd.Series(False, index=col_data.index)  # Unknown types are skipped

        for idx in invalid[invalid].index:
            identifier = df.at[idx, id_column]
            errors.append({col_attr: col_name, "Issue": "Invalid type", "Row": identifier, "Value": col_data[idx]})

        # Check range
        if 'min' in col_specs:
            out_of_range = col_data[col_data < col_specs['min']]
            for idx, value in out_of_range.items():
                identifier = df.at[idx, id_column]
                errors.append({col_attr: col_name, "Issue": f"Below minimum ({col_specs['min']})", "Row": identifier, "Value": value})

        if 'max' in col_specs:
            out_of_range = col_data[col_data > col_specs['max']]
            for idx, value in out_of_range.items():
                identifier = df.at[idx, id_column]
                errors.append({col_attr: col_name, "Issue": f"Above maximum ({col_specs['max']})", "Row": identifier, "Value": value})

    # Rmove 'geometry' and 'reference' columns
    missing_columns = [item for item in missing_columns if item not in ['geometry', 'reference']]

    # Print results
    if errors:
        if verbose:
            for error in errors:
                print(error)
    elif verbose:
        print(f"Validation passed: All columns and values meet the CEA schema requirements.")

    return missing_columns, errors


def print_verification_results_4_db(scenario_name, dict_missing):

    if all(not value for value in dict_missing.values()):
        print("✓" * 3)
        print('The Database is verified as present and compatible with the current version of CEA-4 for Scenario: {scenario}, including:'.format(scenario=scenario_name),
              )
    else:
        print("!" * 3)
        print('All or some of Database files/columns are missing or incompatible with the current version of CEA-4 for Scenario: {scenario}. '.format(scenario=scenario_name))
        print('- If you are migrating your input data from CEA-3 to CEA-4 format, set the toggle `migrate_from_cea_3` to `True` for Feature CEA-4 Format Helper and click on Run. ')
        print('- If you manually prepared the Database, check the log for missing files and/or incompatible columns. Modify your Database accordingly.')


def verify_file_exists_4_db(scenario, items, sheet_name=None):
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
        if sheet_name is None:
            path = path_to_db_file_4(scenario, file)
            if not os.path.isfile(path):
                list_missing_files.append(file)
        else:
            for sheet in sheet_name:
                path = path_to_db_file_4(scenario, file, sheet)
                if not os.path.isfile(path):
                    list_missing_files.append(sheet)
    return list_missing_files


def verify_assembly(scenario, ASSEMBLIES, print_results=True):
    list_list_missing_columns_csv = []
    construction_type_df = pd.read_csv(path_to_db_file_4(scenario, 'CONSTRUCTION_TYPE'))
    for assembly in ASSEMBLIES:
        list_archetype_code = construction_type_df[dict_envelope[assembly]].tolist().unique()
        item_df = pd.read_csv(path_to_db_file_4(scenario, "ENVELOPE", assembly))
        list_item_code = item_df['code'].tolist().unique()
        list_missing_item = list(set(list_archetype_code) - set(list_item_code))
        if list_missing_item:
            if print_results:
                print('! Ensure {assembly} type(s) are present in {assembly}.csv: {list_missing_item}'.format(assembly=assembly, list_missing_item=list_missing_item))

        list_missing_columns_csv, list_issues_against_csv = verify_file_against_schema_4_db(scenario, 'ENVELOPE', verbose=False, sheet_name=assembly)
        list_list_missing_columns_csv.append(list_missing_columns_csv)
        if print_results:
            if list_missing_columns_csv:
                print('! Ensure column(s) are present in {assembly}.csv: {missing_columns}'.format(assembly=assembly, missing_columns=list_missing_columns_csv))
            if list_issues_against_csv:
                print('! Check values in {assembly}.csv: {list_issues_against_schema}'.format(assembly=assembly, list_issues_against_schema=list_issues_against_csv))

    return list_list_missing_columns_csv

def get_csv_filenames(folder_path):
    """
    Get the names of all .csv files in the specified folder.

    Parameters:
    - folder_path (str): Path to the folder.

    Returns:
    - List[str]: A list of file names without path and without extension.
    """
    if not os.path.isdir(folder_path):
        raise ValueError(f"The provided path '{folder_path}' is not a valid directory.")

    # List all .csv files and remove the extension
    csv_filenames = [
        os.path.splitext(file)[0]  # Remove the file extension
        for file in os.listdir(folder_path)  # List files in the folder
        if file.endswith('.csv')  # Check for .csv extension
    ]

    return csv_filenames

## --------------------------------------------------------------------------------------------------------------------
## Unique traits for the CEA-4 format
## --------------------------------------------------------------------------------------------------------------------


def cea4_verify_db(scenario, print_results=False):
    """
    Verify the database for the CEA-4 format.

    :param scenario: the scenario to verify
    :param print_results: if True, print the results
    :return: a dictionary with the missing files
    """

    dict_missing_db = {}

    #1. verify columns and values in .csv files for archetypes
    list_missing_files_csv_archetypes = verify_file_exists_4_db(scenario, ARCHETYPES)
    if list_missing_files_csv_archetypes:
        print('! Ensure .csv file(s) are present in the ARCHETYPES folder: {list_missing_files_csv}'.format(list_missing_files_csv=list_missing_files_csv_archetypes))
        print('! CONSTRUCTION_TYPE.csv and USE_TYPE.csv are fundamental and should be present in the ARCHETYPES folder.')
        print('! The CEA-4 Database verification is aborted.')
        sys.exit(0)

    for item in ARCHETYPES:
        if item not in list_missing_files_csv_archetypes:
            list_missing_columns_csv_archetypes, list_issues_against_csv_archetypes = verify_file_against_schema_4_db(scenario, item, verbose=False)
            dict_missing_db[item] = list_missing_columns_csv_archetypes
            if print_results:
                if list_missing_columns_csv_archetypes:
                    print('! Ensure column(s) are present in {item}.csv: {missing_columns}'.format(item=item, missing_columns=list_missing_columns_csv_archetypes))
                if list_issues_against_csv_archetypes:
                    print('! Check value(s) in {item}.csv: {list_issues_against_schema}'.format(item=item, list_issues_against_schema=list_issues_against_csv_archetypes))

    #2. verify columns and values in .csv files for schedules
    use_type_df = pd.read_csv(path_to_db_file_4(scenario, 'USE_TYPE'))
    list_use_types = use_type_df['code'].tolist()
    list_missing_files_csv_schedules = verify_file_exists_4_db(scenario, SCHEDULES_FOLDER, sheet_name=list_use_types)
    if list_missing_files_csv_schedules:
        if print_results:
            print('! Ensure .csv file(s) are present in the ARCHETYPES>SCHEDULES folder: {list_missing_files_csv}'.format(list_missing_files_csv=list_missing_files_csv_schedules))

    for sheet in list_use_types:
        list_missing_columns_csv_schedules, list_issues_against_csv_schedules = verify_file_against_schema_4_db(scenario, SCHEDULES_FOLDER, verbose=False, sheet_name=sheet)
        dict_missing_db[SCHEDULES_FOLDER] = list_missing_columns_csv_schedules
        if print_results:
            if list_missing_columns_csv_schedules:
                print('! Ensure column(s) are present in {sheet}.csv: {missing_columns}'.format(sheet=sheet, missing_columns=list_missing_columns_csv_schedules))
            if list_issues_against_csv_schedules:
                print('! Check value(s) in {sheet}.csv: {list_issues_against_schema}'.format(sheet=sheet, list_issues_against_schema=list_issues_against_csv_schedules))

    #3. verify columns and values in .csv files for assemblies
    for ASSEMBLIES in ASSEMBLIES_FOLDERS:
        list_missing_files_csv = verify_file_exists_4_db(scenario, [ASSEMBLIES], dict_assembly[ASSEMBLIES])
        if list_missing_files_csv:
            if print_results:
                print('! Ensure .csv file(s) are present in the ASSEMBLIES>{ASSEMBLIES} folder: {list_missing_files_csv}'.format(ASSEMBLIES=ASSEMBLIES, list_missing_files_csv=list_missing_files_csv))

        list_list_missing_columns_csv = verify_assembly(scenario, ASSEMBLIES, print_results)
        dict_missing_db[ASSEMBLIES] = list_list_missing_columns_csv

    #4. verify columns and values in .csv files for components - conversion
    list_missing_files_csv_conversion_components = verify_file_exists_4_db(scenario, ['CONVERSION'], CONVERSION_COMPONENTS)
    if list_missing_files_csv_conversion_components:
        print('! Ensure .csv file(s) are present in the COMPONENTS>CONVERSION folder: {list_missing_files_csv}'.format(list_missing_files_csv=list_missing_files_csv_conversion_components))

    list_conversion_supply = []
    list_conversion_db = get_csv_filenames(path_to_db_file_4(scenario, 'CONVERSION'))
    for supply_type in ['HEATING', 'COOLING']:
        if supply_type not in verify_file_exists_4_db(scenario, ['SUPPLY'], dict_assembly['SUPPLY']):
            supply_df = pd.read_csv(path_to_db_file_4(scenario, supply_type))
            list_conversion_supply.append(supply_df['primary_components', 'secondary_components', 'tertiary_components'].unique())
            list_conversion_supply = [item for sublist in list_conversion_supply for item in sublist]
    list_missing_conversion = list(set(list_conversion_supply) - set(list_conversion_db))
    if list_missing_conversion:
        if print_results:
            print('! Ensure .csv file(s) are present in COMPONENTS>CONVERSION folder: {list_missing_conversion}'.format(list_missing_conversion=list_missing_conversion))

    for sheet in list_conversion_db:
        list_missing_columns_csv_conversion, list_issues_against_csv_conversion = verify_file_against_schema_4_db(scenario, 'CONVERSION', verbose=False, sheet_name=sheet)
        dict_missing_db['CONVERSION'] = list_missing_columns_csv_conversion
        if print_results:
            if list_missing_columns_csv_conversion:
                print('! Ensure column(s) are present in {conversion}.csv: {missing_columns}'.format(conversion=sheet, missing_columns=list_missing_columns_csv_conversion))
            if list_issues_against_csv_conversion:
                print('! Check value(s) in {conversion}.csv: {list_issues_against_schema}'.format(conversion=sheet, list_issues_against_schema=list_issues_against_csv_conversion))

    #5. verify columns and values in .csv files for components - distribution
    list_missing_files_csv_distribution_components = verify_file_exists_4_db(scenario, ['DISTRIBUTION'], DISTRIBUTION_COMPONENTS)
    if list_missing_files_csv_distribution_components:
        print('! Ensure .csv file(s) are present in the COMPONENTS>DISTRIBUTION folder: {list_missing_files_csv}'.format(list_missing_files_csv=list_missing_files_csv_distribution_components))

    list_missing_columns_csv_distribution, list_issues_against_csv_distribution = verify_file_against_schema_4_db(scenario, ['DISTRIBUTION'], verbose=False)
    dict_missing_db['DISTRIBUTION'] = list_missing_columns_csv_distribution
    if print_results:
        if list_missing_columns_csv_distribution:
            print('! Ensure column(s) are present in DISTRIBUTION.csv: {missing_columns}'.format(missing_columns=list_missing_columns_csv_distribution))
        if list_issues_against_csv_distribution:
            print('! Check value(s) in DISTRIBUTION.csv: {list_issues_against_schema}'.format(list_issues_against_schema=list_issues_against_csv_distribution))

    #6. verify columns and values in .csv files for components - feedstocks
    list_missing_files_csv_feedstocks_components = verify_file_exists_4_db(scenario, ['FEEDSTOCKS'], FEEDSTOCKS_COMPONENTS)
    if list_missing_files_csv_feedstocks_components:
        print('! Ensure .csv file(s) are present in the COMPONENTS folder: {list_missing_files_csv}'.format(list_missing_files_csv=list_missing_files_csv_feedstocks_components))

    list_feedstocks_supply = []
    list_feedstocks_db = get_csv_filenames(path_to_db_file_4(scenario, 'FEEDSTOCKS'))
    for supply_type in SUPPLY_ASSEMBLIES:
        if supply_type not in verify_file_exists_4_db(scenario, ['SUPPLY'], dict_assembly['SUPPLY']):
            supply_df = pd.read_csv(path_to_db_file_4(scenario, supply_type))
            list_feedstocks_supply.append(supply_df['feedstock'].unique())
            list_feedstocks_supply = [item for sublist in list_feedstocks_supply for item in sublist]
    list_missing_feedstocks = list(set(list_feedstocks_supply) - set(list_feedstocks_db))
    if list_missing_feedstocks:
        if print_results:
            print('! Ensure .csv file(s) are present in COMPONENTS>FEEDSTOCKS folder: {list_missing_feedstocks}'.format(list_missing_feedstocks=list_missing_feedstocks))

    for sheet in list_feedstocks_db:
        list_missing_columns_csv_feedstocks, list_issues_against_csv_feedstocks = verify_file_against_schema_4_db(scenario, 'FEEDSTOCKS', verbose=False, sheet_name=sheet)
        dict_missing_db['FEEDSTOCKS'] = list_missing_columns_csv_feedstocks
        if print_results:
            if list_missing_columns_csv_feedstocks:
                print('! Ensure column(s) are present in {feedstocks}.csv: {missing_columns}'.format(feedstocks=sheet, missing_columns=list_missing_columns_csv_feedstocks))
            if list_issues_against_csv_feedstocks:
                print('! Check value(s) in {feedstocks}.csv: {list_issues_against_schema}'.format(feedstocks=sheet, list_issues_against_schema=list_issues_against_csv_feedstocks))

    return dict_missing_db

## --------------------------------------------------------------------------------------------------------------------
## Main function
## --------------------------------------------------------------------------------------------------------------------


def main(config):
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
    dict_missing_db = cea4_verify_db(scenario, print_results=True)

    # Print the results
    print_verification_results_4_db(scenario_name, dict_missing_db)

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0

    # Print: End
    print('+' * 60)
    print('The entire process of CEA-4 format verification is now completed - time elapsed: %.2f seconds' % time_elapsed)

if __name__ == '__main__':
    main(cea.config.Configuration())

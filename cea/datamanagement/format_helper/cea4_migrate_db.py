"""
Mirgate the format of the DB to CEA-4 format.

"""


import os
import cea.config
import time
import pandas as pd
import shutil



__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.datamanagement.format_helper.cea4_verify_db import path_to_db_file_4, print_verification_results_4_db, \
    cea4_verify_db


## --------------------------------------------------------------------------------------------------------------------
## The paths to the input files for CEA-4
## --------------------------------------------------------------------------------------------------------------------

# The paths are relatively hardcoded for now without using the inputlocator script.
# This is because we want to iterate over all scenarios, which is currently not possible with the inputlocator script.
def path_to_db_file_3(scenario, item):

    if item == 'technology':
        path_db_file = os.path.join(scenario, "inputs", "technology")
    elif item == "CONSTRUCTION_STANDARD":
        path_db_file = os.path.join(scenario, "inputs", "technology", "archetypes", "CONSTRUCTION_STANDARD.xlsx")
    elif item == "USE_TYPE_PROPERTIES":
        path_db_file = os.path.join(scenario, "inputs",  "technology", "archetypes", "use_types", "USE_TYPE_PROPERTIES.xlsx")
    elif item == "SCHEDULES":
        path_db_file = os.path.join(scenario, "inputs",  "technology", "archetypes", "use_types")
    elif item == "ENVELOPE":
        path_db_file = os.path.join(scenario, "inputs",  "technology", "assemblies", "ENVELOPE.xlsx")
    elif item == "HVAC":
        path_db_file = os.path.join(scenario, "inputs",  "technology", "assemblies", "HVAC.xlsx")
    elif item == "SUPPLY":
        path_db_file = os.path.join(scenario, "inputs",  "technology", "assemblies", "SUPPLY.xlsx")
    elif item == "CONVERSION":
        path_db_file = os.path.join(scenario, "inputs",  "technology", "components", "CONVERSION.xlsx")
    elif item == "DISTRIBUTION":
        path_db_file = os.path.join(scenario, "inputs",  "technology", "components", "DISTRIBUTION.xlsx")
    elif item == "FEEDSTOCKS":
        path_db_file = os.path.join(scenario, "inputs",  "technology", "components", "FEEDSTOCKS.xlsx")
    else:
        raise ValueError(f"Unknown item {item}")

    return path_db_file


## --------------------------------------------------------------------------------------------------------------------
## Helper functions
## --------------------------------------------------------------------------------------------------------------------


def excel_tab_to_csv(path_excel, directory_csv):
    """
    Converts each sheet of an Excel file into individual CSV files and deletes the Excel file.

    Parameters:
    - path_excel (str): The path to the input Excel file.
    - directory_csv (str): The directory where CSV files should be saved.
    """
    # Ensure the output directory exists
    os.makedirs(directory_csv, exist_ok=True)

    # Read the Excel file
    try:
        excel_data = pd.ExcelFile(path_excel)
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {e}")

    # Loop through each sheet and save as a CSV
    for sheet_name in excel_data.sheet_names:
        try:
            df = pd.read_excel(path_excel, sheet_name=sheet_name)
            output_path = os.path.join(directory_csv, f"{sheet_name}.csv")
            df.to_csv(output_path, index=False)
            print(f"Saved {sheet_name} to {output_path}")
        except Exception as e:
            print(f"Failed to save sheet {sheet_name} as CSV. Error: {e}")

    # Delete the Excel file
    try:
        os.remove(path_excel)
        print(f"Deleted the Excel file: {path_excel}")
    except Exception as e:
        print(f"Failed to delete the Excel file. Error: {e}")


def merge_excel_tab_to_csv(path_excel, column_name, path_csv, new_column_name=None):
    """
    Merge all tabs of an Excel file horizontally based on a common column and save the result as a CSV file.

    Parameters:
    - path_excel (str): Path to the input Excel file.
    - column_name (str): The column used to merge the tabs.
    - directory_csv (str): The directory to save the resulting CSV file.
    - csv_file_name (str): The name of the output CSV file.
    - new_column_name (str, optional): New name for the column used for merging. If provided, replaces column_name.

    Returns:
    - None
    """
    # Ensure the output directory exists
    directory_csv = os.path.dirname(path_csv)
    os.makedirs(directory_csv, exist_ok=True)

    # Read the Excel file
    try:
        excel_data = pd.ExcelFile(path_excel)
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {e}")

    # Initialize an empty DataFrame for merging
    merged_df = None

    # Update the key column name
    if new_column_name:
        key_column = new_column_name
    else:
        key_column = column_name

    # Loop through each sheet and merge horizontally
    for sheet_name in excel_data.sheet_names:
        try:
            df = pd.read_excel(path_excel, sheet_name=sheet_name)

            # Ensure the column_name exists
            if column_name not in df.columns:
                raise ValueError(f"Column '{column_name}' not found in sheet '{sheet_name}'.")

            # If a new column name is provided, rename it
            df.rename(columns={column_name: key_column}, inplace=True)

            # Merge with the existing DataFrame
            if merged_df is None:
                merged_df = df
            else:
                merged_df = pd.merge(merged_df, df, on=key_column, how='outer')

        except Exception as e:
            print(f"Failed to process sheet '{sheet_name}'. Error: {e}")

    # Ensure the key column is the first column
    if merged_df is not None:
        cols = [key_column] + [col for col in merged_df.columns if col != key_column]
        merged_df = merged_df[cols]

        # Save the merged DataFrame as a CSV file
        try:
            merged_df.to_csv(path_csv, index=False)
            print(f"Saved merged DataFrame to {path_csv}")
        except Exception as e:
            print(f"Failed to save merged DataFrame as CSV. Error: {e}")

    # Delete the original Excel file
    try:
        os.remove(path_excel)
        print(f"Deleted the Excel file: {path_excel}")
    except Exception as e:
        print(f"Failed to delete the Excel file. Error: {e}")

def move_files(old_directory, new_directory, list_file_extensions):
    """
    Move files with specific extensions from one directory to another and delete the old directory.

    Parameters:
    - old_directory (str): The path to the source directory.
    - new_directory (str): The path to the target directory.
    - list_file_extensions (list): List of file extensions to move (e.g., ['.txt', '.csv']).

    Returns:
    - None
    """
    # Ensure the new directory exists
    os.makedirs(new_directory, exist_ok=True)

    # Iterate through the files in the old directory
    for root, dirs, files in os.walk(old_directory):
        for file in files:
            # Check if the file has one of the specified extensions
            if any(file.endswith(ext) for ext in list_file_extensions):
                old_file_path = os.path.join(root, file)
                new_file_path = os.path.join(new_directory, file)

                # Copy the file to the new directory
                shutil.copy2(old_file_path, new_file_path)
                print(f"Copied: {old_file_path} to {new_file_path}")

def delete_files(path):
    """
    Delete all files in a directory

    - path (str): The path to the directory
    """
    try:
        shutil.rmtree(path)
        print(f"Deleted directory: {path}")
    except Exception as e:
        print(f"Failed to delete directory. Error: {e}")


## --------------------------------------------------------------------------------------------------------------------
## Migrate to CEA-4 format from CEA-3 format
## --------------------------------------------------------------------------------------------------------------------


def migrate_cea3_to_cea4_db(scenario):

    #0. verify if everything is already in the correct format for CEA-4
    # dict_missing = cea4_verify_db(scenario)
    dict_missing = {'hh':{'hh'}}
    if all(not value for value in dict_missing.values()):
        pass
    else:
        #1. about archetypes - construction types
        path_excel = path_to_db_file_3(scenario, 'CONSTRUCTION_STANDARD')
        path_csv = path_to_db_file_4(scenario, 'CONSTRUCTION_TYPE')
        merge_excel_tab_to_csv(path_excel, 'STANDARD', path_csv, new_column_name='const_type')

        #2. about archetypes - use types
        path_excel = path_to_db_file_3(scenario, 'USE_TYPE_PROPERTIES')
        path_csv = path_to_db_file_4(scenario, 'USE_TYPE')
        merge_excel_tab_to_csv(path_excel, 'code', path_csv)

        shedules_directory_3 = path_to_db_file_3(scenario, 'SCHEDULES')
        shedules_directory_4 = path_to_db_file_4(scenario, 'SCHEDULES')
        move_files(shedules_directory_3, shedules_directory_4, ['.csv', '.txt'])

        #3. about assemblies
        excel_tab_to_csv(path_to_db_file_3(scenario, 'ENVELOPE'), path_to_db_file_4(scenario, 'ENVELOPE'))
        excel_tab_to_csv(path_to_db_file_3(scenario, 'HVAC'), path_to_db_file_4(scenario, 'HVAC'))
        excel_tab_to_csv(path_to_db_file_3(scenario, 'SUPPLY'), path_to_db_file_4(scenario, 'SUPPLY'))

        #4. about components
        excel_tab_to_csv(path_to_db_file_3(scenario, 'CONVERSION'), path_to_db_file_4(scenario, 'CONVERSION'))
        excel_tab_to_csv(path_to_db_file_3(scenario, 'DISTRIBUTION'), path_to_db_file_4(scenario, 'DISTRIBUTION'))
        excel_tab_to_csv(path_to_db_file_3(scenario, 'FEEDSTOCKS'), path_to_db_file_4(scenario, 'FEEDSTOCKS'))

        # Print: End
        print('-' * 49)


## --------------------------------------------------------------------------------------------------------------------
## Main function
## --------------------------------------------------------------------------------------------------------------------


def main(config):
    # Start the timer
    t0 = time.perf_counter()
    assert os.path.exists(config.general.project), 'input file not found: %s' % config.project

    scenario = config.scenario
    scenario_name = os.path.basename(scenario)

    # Print: Start
    div_len = 37 - len(scenario_name)
    print('-' * 39)
    print("-" * 1 + ' Scenario: {scenario} '.format(scenario=scenario_name) + "-" * div_len)

    # Execute the migration
    migrate_cea3_to_cea4_db(scenario)

    # # Execute the verification again
    # dict_missing = cea4_verify_db(scenario)
    #
    # # Print the verification results
    # print_verification_results_4_db(scenario_name, dict_missing)

    # Remove the old database
    delete_files(path_to_db_file_3(scenario, 'technology'))

    # Print: End
    # print("-" * 1 + ' Scenario: {scenario} - end '.format(scenario=scenario_name) + "-" * 50)
    print('+' * 104)

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire process of Database migration from CEA-3 to CEA-4 is now completed - time elapsed: %.2f seconds' % time_elapsed)

if __name__ == '__main__':
    main(cea.config.Configuration())

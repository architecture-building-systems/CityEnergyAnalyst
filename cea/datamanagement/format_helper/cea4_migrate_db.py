"""
Mirgate the format of the DB to CEA-4 format.

"""


import os
import cea.config
import time
import pandas as pd
import shutil
import csv


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.datamanagement.format_helper.cea4_verify_db import path_to_db_file_4, cea4_verify_db, \
    print_verification_results_4_db

rename_dict = {'STANDARD': 'const_type',
               'YEAR_START': 'year_start',
               'YEAR_END': 'year_end',
               'type_cons': 'type_mass',
               'Description': 'description',
               'REFERENCE': 'reference',
               'Code': 'code',
               'Pipe_DN': 'pipe_DN',
               'DAY':'day',
               'HOUR':'hour',
               'HOURS':'hours',
               'HOURS_PER_DAY':'hours_per_day',
               'OCCUPANCY':'occupancy',
               'APPLIANCES':'appliances',
               'LIGHTING':'lighting',
               'WATER':'hot_water',
               'HEATING':'heating',
               'COOLING':'cooling',
               'PROCESSES':'processes',
               'SERVERS':'servers',
               'ELECTROMOBILITY':'electromobility',
               'unit ': 'unit',
               }


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


def excel_tab_to_csv(path_excel, directory_csv, rename_dict=None):
    """
    Converts each sheet of an Excel file into individual CSV files.

    Parameters:
    - path_excel (str): The path to the input Excel file.
    - directory_csv (str): The directory where CSV files should be saved.
    - rename_dict (dict, optional): Dictionary for renaming columns. Keys are old column names, values are new names.
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
            # Rename columns based on the rename_dict
            if rename_dict:
                df.rename(columns=rename_dict, inplace=True)
            output_path = os.path.join(directory_csv, f"{sheet_name}.csv")
            df.to_csv(output_path, index=False)
            print(f"Saved {sheet_name} to {output_path}")
        except Exception as e:
            print(f"Failed to save sheet {sheet_name} as .csv format Error: {e}")


def merge_excel_tab_to_csv(path_excel, column_name, path_csv, rename_dict=None):
    """
    Merge all tabs of an Excel file horizontally based on a common column and save the result as a CSV file.

    Parameters:
    - path_excel (str): Path to the input Excel file.
    - column_name (str): The column used to merge the tabs.
    - path_csv (str): Path to save the resulting CSV file (includes file name).
    - new_column_name (str, optional): New name for the column used for merging. If provided, replaces column_name.
    - rename_dict (dict, optional): Dictionary for renaming columns. Keys are old column names, values are new names.

    Returns:
    - None
    """
    # Ensure the output directory exists
    directory_csv = os.path.dirname(path_csv)
    os.makedirs(directory_csv, exist_ok=True)

    try:
        # Read the Excel file
        excel_data = pd.ExcelFile(path_excel)
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {e}")

    merged_df = None  # Initialize an empty DataFrame for merging

    if rename_dict and column_name in rename_dict:
        key_column = rename_dict[column_name]
    else:
        key_column = column_name  # Determine key column name

    for sheet_name in excel_data.sheet_names:
        try:
            df = pd.read_excel(path_excel, sheet_name=sheet_name)

            # Check if the key column exists in the current sheet
            if column_name not in df.columns:
                raise ValueError(f"Column '{column_name}' not found in sheet '{sheet_name}'.")

            # Rename columns based on the rename_dict
            if rename_dict:
                df.rename(columns=rename_dict, inplace=True)

            # Add prefix for sheets ending with '_ASSEMBLIES'
            if sheet_name.endswith("_ASSEMBLIES"):
                prefix = sheet_name.replace("_ASSEMBLIES", "").lower()
                df.columns = [f"{prefix}_{col}" if col != key_column else col for col in df.columns]

            # Merge horizontally with the existing DataFrame
            if merged_df is None:
                merged_df = df
            else:
                merged_df = pd.merge(merged_df, df, on=key_column, how='outer')

        except Exception as e:
            print(f"Warning: Failed to process sheet '{sheet_name}'. Error: {e}")

    # Get the file name without the extension
    file_name = os.path.splitext(os.path.basename(path_csv))[0]

    # Ensure the key column is the first column
    if merged_df is not None:
        cols = [key_column] + [col for col in merged_df.columns if col != key_column]
        merged_df = merged_df[cols]

        # Save the merged DataFrame as a CSV file
        try:
            merged_df.to_csv(path_csv, index=False)
            print(f"Saved {file_name} to {path_csv}")
        except Exception as e:
            print(f"Failed to save merged DataFrame as CSV. Error: {e}")


def move_txt_modify_csv_files(scenario):
    """
    Move .txt files and process .csv files from one directory to another.
    Also, compile specific rows from .csv files into a combined DataFrame.

    Parameters:
    - scenario: The scenario path.

    Returns:
    - None
    """
    # Paths
    shedules_directory_3 = path_to_db_file_3(scenario, 'SCHEDULES')
    shedules_directory_4 = path_to_db_file_4(scenario, 'SCHEDULES')
    compiled_rows = []

    # Ensure the target directory exists
    os.makedirs(shedules_directory_4, exist_ok=True)

    # Iterate through files in the source directory
    for root, _, files in os.walk(shedules_directory_3):
        for file in files:
            old_file_path = os.path.join(root, file)
            new_file_path = os.path.join(shedules_directory_4, file)

            # Handle .txt files: Move to new directory
            if file.endswith('.txt'):
                shutil.copy2(old_file_path, new_file_path)
                print(f"Saved schedule_references.txt to {new_file_path}")

            # Handle .csv files: Process and save
            elif file.endswith('.csv'):
                try:
                    # Read the CSV file
                    use_type = os.path.splitext(file)[0]
                    with open(old_file_path, 'r') as f:
                        reader = csv.reader(f)
                        rows = list(reader)

                    # Extract the second row for compilation: monthly multiplier
                    headers_multiplier = ['use_type',
                                          'Jan', 'Feb', 'Mar',
                                          'Apr', 'May', 'Jun',
                                          'Jul', 'Aug', 'Sep',
                                          'Oct', 'Nov', 'Dec']
                    second_row = {headers_multiplier[i]: value for i, value in enumerate(rows[1])}
                    second_row['use_type'] = use_type
                    compiled_rows.append(second_row)

                    # Clean and process the remaining data
                    # Extract rows 3 to 74
                    other_rows = rows[3:75]  # Remember Python indexing starts at 0
                    headers_schedules = rows[2]
                    schedules_df = pd.DataFrame(other_rows, columns=headers_schedules)
                    schedules_df.rename(columns=rename_dict, inplace=True)
                    schedules_df = schedules_df.apply(pd.to_numeric, errors='ignore')

                    # Drop the original 'day' and 'hour' columns
                    if 'day' in schedules_df.columns:
                        schedules_df.drop(columns=['day'], inplace=True)
                    if 'hour' in schedules_df.columns:
                        schedules_df.drop(columns=['hour'], inplace=True)

                    # Create the 'hour' column
                    hour_values = (
                        ['Weekday_{:02d}'.format(i) for i in range(24)] +
                        ['Saturday_{:02d}'.format(i) for i in range(24)] +
                        ['Sunday_{:02d}'.format(i) for i in range(24)]
                    )

                    # Add the new 'hour' column as a Series
                    schedules_df.insert(0, 'hour', pd.Series(hour_values, index=schedules_df.index[:72]))

                    # Save the cleaned data
                    schedules_df.to_csv(new_file_path, index=False)
                    print(f"Saved {use_type} to {new_file_path}")
                except Exception as e:
                    print(f"Error processing {file}: {e}")

    # Create and save the compiled DataFrame
    if compiled_rows:
        compiled_multiplier_df = pd.DataFrame(compiled_rows)
        compiled_multiplier_path = path_to_db_file_4(scenario, 'MONTHLY_MULTIPLIER')
        compiled_multiplier_df.to_csv(compiled_multiplier_path, index=False)
        print(f"Saved MONTHLY_MULTIPLIER to: {compiled_multiplier_path}")


def delete_files(path):
    """
    Delete all files in a directory

    Parameters:
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
        merge_excel_tab_to_csv(path_excel, 'STANDARD', path_csv, rename_dict=rename_dict)

        #2. about archetypes - use types
        path_excel = path_to_db_file_3(scenario, 'USE_TYPE_PROPERTIES')
        path_csv = path_to_db_file_4(scenario, 'USE_TYPE')
        merge_excel_tab_to_csv(path_excel, 'code', path_csv)
        move_txt_modify_csv_files(scenario)

        #3. about assemblies
        excel_tab_to_csv(path_to_db_file_3(scenario, 'ENVELOPE'), path_to_db_file_4(scenario, 'ENVELOPE'), rename_dict=rename_dict)
        excel_tab_to_csv(path_to_db_file_3(scenario, 'HVAC'), path_to_db_file_4(scenario, 'HVAC'), rename_dict=rename_dict)
        excel_tab_to_csv(path_to_db_file_3(scenario, 'SUPPLY'), path_to_db_file_4(scenario, 'SUPPLY'), rename_dict=rename_dict)

        #4. about components
        excel_tab_to_csv(path_to_db_file_3(scenario, 'CONVERSION'), path_to_db_file_4(scenario, 'CONVERSION'), rename_dict=rename_dict)
        excel_tab_to_csv(path_to_db_file_3(scenario, 'DISTRIBUTION'), path_to_db_file_4(scenario, 'DISTRIBUTION'), rename_dict=rename_dict)
        excel_tab_to_csv(path_to_db_file_3(scenario, 'FEEDSTOCKS'), path_to_db_file_4(scenario, 'FEEDSTOCKS'), rename_dict=rename_dict)

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
    print('-' * 50)
    print("-" * 1 + ' Scenario: {scenario} '.format(scenario=scenario_name) + "-" * div_len)

    # Execute the migration
    migrate_cea3_to_cea4_db(scenario)

    # Execute the verification again
    dict_missing = cea4_verify_db(scenario)

    # Print the verification results
    print_verification_results_4_db(scenario_name, dict_missing)

    # If verification is passed, remove the old database
    if all(not value for value in dict_missing.values()):
        delete_files(path_to_db_file_3(scenario, 'technology'))
        # Print: End
        # print("-" * 1 + ' Scenario: {scenario} - end '.format(scenario=scenario_name) + "-" * 50)
        print('+' * 104)

        # Print the time used for the entire processing
        time_elapsed = time.perf_counter() - t0
        print('The entire process of Database migration from CEA-3 to CEA-4 is now completed - time elapsed: %.2f seconds' % time_elapsed)

    # if verification is failed, keep the old database, remove the new one
    else:
        delete_files(path_to_db_file_4(scenario, 'database'))
        # Print: End
        # print("-" * 1 + ' Scenario: {scenario} - end '.format(scenario=scenario_name) + "-" * 50)
        print('+' * 104)

        # Print the time used for the entire processing
        time_elapsed = time.perf_counter() - t0
        print('The entire process of Database migration from CEA-3 to CEA-4 is not successful - time elapsed: %.2f seconds' % time_elapsed)

if __name__ == '__main__':
    main(cea.config.Configuration())

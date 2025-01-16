"""
Verify the format of DB for CEA-4 model.

"""


import os
import cea.config
import time
import pandas as pd
import shutil
import geopandas as gpd



__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


## --------------------------------------------------------------------------------------------------------------------
## The paths to the input files for CEA-4
## --------------------------------------------------------------------------------------------------------------------

# The paths are relatively hardcoded for now without using the inputlocator script.
# This is because we want to iterate over all scenarios, which is currently not possible with the inputlocator script.
def path_to_db_file_4(scenario, item):

    if item == "CONSTRUCTION_TYPE":
        path_to_input_file = os.path.join(scenario, "inputs", "database", "ARCHETYPES", "CONSTRUCTION_TYPE.xlsx")
    elif item == "USE_TYPE_PROPERTIES":
        path_to_input_file = os.path.join(scenario, "inputs",  "database", "ARCHETYPES", "USE_TYPE.xlsx")
    elif item == "SCHEDULES":
        path_to_input_file = os.path.join(scenario, "inputs", "database", "ARCHETYPES", "SCHEDULES")
    elif item == "ENVELOPE":
        path_to_input_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "ENVELOPE")
    elif item == "HVAC":
        path_to_input_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "HVAC")
    elif item == "SUPPLY":
        path_to_input_file = os.path.join(scenario, "inputs",  "database", "ASSEMBLIES", "SUPPLY")
    elif item == "CONVERSION":
        path_to_input_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "CONVERSION")
    elif item == "DISTRIBUTION":
        path_to_input_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "DISTRIBUTION")
    elif item == "FEEDSTOCKS":
        path_to_input_file = os.path.join(scenario, "inputs",  "database", "COMPONENTS", "FEEDSTOCKS")
    else:
        raise ValueError(f"Unknown item {item}")

    return path_to_input_file


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


def merge_excel_tab_to_csv(path_excel, column_name, directory_csv, csv_file_name, new_column_name=None):
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
        output_path = os.path.join(directory_csv, csv_file_name)
        try:
            merged_df.to_csv(output_path, index=False)
            print(f"Saved merged DataFrame to {output_path}")
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

    # Delete the old directory and all its contents
    try:
        shutil.rmtree(old_directory)
        print(f"Deleted old directory: {old_directory}")
    except Exception as e:
        print(f"Failed to delete old directory. Error: {e}")



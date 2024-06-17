
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import re


def load_data_from_directories(main_directory, filename):

    # Create an empty DataFrame to hold the results
    result_df = pd.DataFrame()

    # Loop through each subdirectory in the main directory
    for subdir in os.listdir(main_directory):
        subdir_path = os.path.join(main_directory, subdir)

        # Check if it is a directory
        if os.path.isdir(subdir_path):
            file_path = os.path.join(subdir_path, filename)

            # Check if the file exists in the subdirectory
            if os.path.isfile(file_path):
                # Read the file into a DataFrame and append to the list
                df = pd.read_csv(file_path)
                # Get the last row of the DataFrame
                last_row = df.iloc[[-1]]

                # Rename the row index to the filename (without extension)
                row_name = os.path.splitext(subdir)[0]
                last_row.index = [row_name]

                # Append the last row to the result DataFrame
                result_df = pd.concat([result_df, last_row])


    return result_df

def generate_and_save_plots(dataframes, plots_path):
    # Generate and save bar plots for each column in the DataFrame (except the 'Supply_System' column)
    for column in dataframes.columns:
        if column != 'Supply_System':
            plt.figure()
            dataframes[column].plot(kind='bar', title=column)
            plt.ylabel(column)
            plt.xlabel('Supply System')
            plt.tight_layout()

            # Save the plot
            plot_file_path = os.path.join(plots_path, f"{column}_plot.png")
            plt.savefig(plot_file_path)
            plt.close()

def process_files(main_directory, filename):
    # Create an empty DataFrame to hold the results
    combined_df = pd.DataFrame()
    columns_to_analyse_ren = ['Component', 'Component_type', 'Component_code', 'Capacity_kW']
    columns_to_analyse_base = ['Component_category', 'Component_type', 'Component_code', 'Capacity_kW']
    # Loop through each subdirectory in the main directory
    for subdir in os.listdir(main_directory):
        if subdir == 'current_DES' or subdir == 'debugging':
            continue
        subdir_path = os.path.join(main_directory, subdir)

        # Check if it is a directory
        if os.path.isdir(subdir_path):
            file_path = os.path.join(subdir_path, filename)

            # Check if the file exists in the subdirectory
            if os.path.isfile(file_path):
                # Read the file into a DataFrame
                df = pd.read_csv(file_path)
                if 'THESIS_TEST_CASES_RENEWABLES' in main_directory:
                    df = df[columns_to_analyse_ren]
                else:
                    df = df[columns_to_analyse_base]

                # Extract the numerical part of the folder name
                match = re.search(r'\d+', subdir)
                if match:
                    num_part = match.group(0)

                    # Rename the columns by appending the numerical part
                    df.columns = [f"{col}_{num_part}" if col != 'Supply_System' else col for col in df.columns]

                # Append the DataFrame to the combined DataFrame
                combined_df = pd.concat([combined_df, df], axis=1)

    return combined_df

                                                    ### MAIN ###

# Define the main directory and the filename
context_analysis = ['THESIS_TEST_CASES_BASE', 'THESIS_TEST_CASES_RENEWABLES'] #
folder = "D:/CEATesting/"
save_directory = "D:/CEATesting/THESIS_TEST_CASES_PLOTS/"
components_available = ['centralized', 'centralized_ALL']
directory_to_file = "/outputs/data/optimization/"
filename = "Supply_systems/Supply_systems_summary.csv"
filename_structure = 'Supply_systems/N1001_supply_system_structure.csv'

for context in context_analysis:
    directory = os.path.join(folder, context)
    scenarios = os.listdir(directory)[1:]
    scenarios.remove('dashboard.yml')
    scenarios.remove('Commercial_High_Rise')  # TODO: Remove this line after the issue is fixed

    for scenario in scenarios:
        for availability in components_available:
            main_directory = os.path.join(directory, scenario) + directory_to_file + availability

            # Load the data from the directories
            try:
                dataframe_structure = process_files(main_directory, filename_structure)
            except:
                continue
            dataframes = load_data_from_directories(main_directory, filename)
            dataframes['Supply_System'] = dataframes.index

            # Create the scenario directory and the nested directory
            if availability == 'centralized_ALL':
                save_path = os.path.join(save_directory, context, scenario, "objective_function_analysis_ALL")
            else:
                save_path = os.path.join(save_directory, context, scenario, "objective_function_analysis")
            os.makedirs(save_path, exist_ok=True)

            # Define the file path to save the DataFrame
            save_file_path = os.path.join(save_path, "Objective_functions_analysis.csv")
            save_file_path_structure = os.path.join(save_path, "System_structure_solutions.csv")

            # Save the DataFrame to a CSV file
            dataframes.to_csv(save_file_path, index=False)
            dataframe_structure.to_csv(save_file_path_structure, index=False)

            # Create the directory for plots
            if availability == 'centralized_ALL':
                plots_path = os.path.join(save_directory, context, scenario, "objective_functions_plots_ALL")
            else:
                plots_path = os.path.join(save_directory, context, scenario, "objective_functions_plots")
            os.makedirs(plots_path, exist_ok=True)

            # Generate and save bar plots
            generate_and_save_plots(dataframes, plots_path)

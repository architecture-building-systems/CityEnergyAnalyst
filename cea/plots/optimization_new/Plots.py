
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd


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


# Define the main directory and the filename
context_analysis = ['THESIS TEST CASES RENEWABLES', 'THESIS TEST CASES BASE']
folder = "D:/CEATesting/"
save_directory = "D:/CEATesting/THESIS TEST CASES PLOTS/"
directory_to_file = "/outputs/data/optimization/centralized/"
filename = "Supply_systems/Supply_systems_summary.csv"

for context in context_analysis:
    directory = os.path.join(folder, context)
    scenarios = os.listdir(directory)[1:]
    scenarios.remove('dashboard.yml')
    scenarios.remove('Commercial high-rise')  # TODO: Remove this line after the issue is fixed

    for scenario in scenarios:

        main_directory = os.path.join(directory, scenario) + directory_to_file
        dataframes = load_data_from_directories(main_directory, filename)
        dataframes['Supply_System'] = dataframes.index

        # Create the scenario directory and the nested directory
        save_path = os.path.join(save_directory, context, scenario, "objective_function_analysis")
        os.makedirs(save_path, exist_ok=True)

        # Define the file path to save the DataFrame
        save_file_path = os.path.join(save_path, "Objective_functions_analysis.csv")

        # Save the DataFrame to a CSV file
        dataframes.to_csv(save_file_path, index=False)

        # Create the directory for plots
        plots_path = os.path.join(save_directory, context, scenario, "objective_functions_plots")
        os.makedirs(plots_path, exist_ok=True)

        # Generate and save bar plots
        generate_and_save_plots(dataframes, plots_path)

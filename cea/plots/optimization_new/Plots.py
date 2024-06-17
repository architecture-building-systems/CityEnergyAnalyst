
import matplotlib.pyplot as plt
import os
import pandas as pd
import re
import numpy as np
import seaborn as sns
from pandas.plotting import parallel_coordinates
from sklearn.preprocessing import MinMaxScaler
from IPython.display import display


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

# Normalization function
def normalize_dataframe(df):
    scaler = MinMaxScaler()
    df_normalized = df.copy()
    df_normalized.iloc[:, 1:] = scaler.fit_transform(df.iloc[:, 1:])
    return df_normalized

def parallel_coordinates_plot(df, path):
    df_normalized = normalize_dataframe(df)
    labels = df_normalized['Supply_System']
    plt.figure()
    parallel_coordinates(df_normalized, 'Supply_System')
    plt.title('Parallel Coordinates Plot', pad=40)
    plt.xticks(rotation=0)
    plt.legend(labels=labels, loc='lower center', bbox_to_anchor=(0.5, 1), ncol=len(labels))
    plot_file_path = os.path.join(path, "Parallel_coordinates_plot.png")
    plt.savefig(plot_file_path)

def radar_chart(df, path):
    df_normalized = normalize_dataframe(df)
    labels = df.columns[1:]
    solutions = df_normalized.set_index('Supply_System').T.to_dict('list')

    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(subplot_kw=dict(polar=True))

    for solution, values in solutions.items():
        values += values[:1]
        ax.plot(angles, values, label=solution)
        ax.fill(angles, values, alpha=0.25)

    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)

    plt.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
    plt.title('Radar Chart')
    plt.xticks(rotation=45)
    plot_file_path = os.path.join(path, "Radar_chart_plot.png")
    plt.savefig(plot_file_path)

def scatter_plot_matrix(df, path):
    df_normalized = normalize_dataframe(df)
    sns.pairplot(df_normalized.drop(columns=['Supply_System']))
    plt.suptitle('Scatter Plot Matrix', y=1.02)  # Adjust title position
    plt.xticks(rotation=45)
    plot_file_path = os.path.join(path, "Scatter_plot_matrix.png")
    plt.savefig(plot_file_path)

def heatmap(df, path):
    df_normalized = normalize_dataframe(df)
    plt.figure()
    sns.heatmap(df_normalized.set_index('Supply_System'), annot=True, cmap='viridis')
    plt.title('Heatmap')
    plt.xticks(rotation=0)
    plot_file_path = os.path.join(path, "Heatmap_plot.png")
    plt.savefig(plot_file_path)

def generate_multi_objective_plots(dataframes, path):
    dataframes_for_plot = dataframes.copy()
    dataframes_for_plot = dataframes_for_plot.rename(columns={'Heat_Emissions_kWh': 'Heat_Emissions',
                                                            'System_Energy_Demand_kWh': 'Energy_Demand',
                                                            'GHG_Emissions_kgCO2': 'GHG_Emissions',
                                                            'Cost_USD': 'Cost'})
    # Set the global figure size
    plt.rcParams['figure.figsize'] = (12, 8)  # Adjust the size as needed

    # Set the global font size for x and y axis labels
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12

    parallel_coordinates_plot(dataframes_for_plot, path)
    radar_chart(dataframes_for_plot, path)
    scatter_plot_matrix(dataframes_for_plot, path)
    heatmap(dataframes_for_plot, path)

    # Close all figures at once
    plt.close('all')

                                                    ### MAIN ###

# Define the main directory and the filename
context_analysis = ['THESIS_TEST_CASES_BASE', 'THESIS_TEST_CASES_RENEWABLES'] #
folder = "D:/CEATesting/"
save_directory = "D:/CEATesting/THESIS_TEST_CASES_PLOTS/"
components_available = ['centralized', 'centralized_ALL'] #
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
            generate_multi_objective_plots(dataframes, plots_path)

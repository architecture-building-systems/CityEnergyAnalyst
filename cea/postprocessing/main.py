
import os

import pandas as pd

from kmedoids_clustering import (kmedoids_clustering, test_different_cluster_numbers, data_preprocessing,
                                 convert_medoids_to_original_scale)
from directories_files_handler import (load_data_from_directories, process_files, process_energy_system_data,
                                       process_scenario)
from multi_objective_plots import (plot_clusters, generate_and_save_plots, heatmap, scatter_plot,
                                   line_graph_plot, yearly_profile_plot, stellar_chart, plot_connectivity)

                                 ### MAIN ###
# Define the main directory and the filename
context_analysis = ['THESIS_TEST_CASES_BASE', 'THESIS_TEST_CASES_RENEWABLES'] #
folder = "D:/CEATesting/"
save_directory = "D:/CEATesting/THESIS_TEST_CASES_PLOTS/"
directory_to_file = "/outputs/data/optimization/centralized"
filename = "Supply_systems/Supply_systems_summary.csv"
filename_structure = 'Supply_systems/N1001_supply_system_structure.csv'
folder_combined = 'combined_analysis'
selected_systems_combined = pd.DataFrame()
selected_systems_structure = pd.DataFrame()
connectivity_df = pd.DataFrame()
percentage_variation = pd.DataFrame()
current_DES = pd.DataFrame()
dict_availabilities = {'THESIS_TEST_CASES_BASE': 'No_renewables', 'THESIS_TEST_CASES_RENEWABLES': 'All_renewables'}
carriers_profile = 'Supply_system_operation_details/N1001_annual_ec_profiles.xlsx'
geojson = 'networks/N1001_layout.geojson'
demand = 'outputs/data/demand'

# Generate and save the multi-objective plots
plots_path_combined = os.path.join(save_directory, folder_combined, "plots")
if not os.path.exists(plots_path_combined):
        os.makedirs(plots_path_combined)

# Control if the combined analysis directory exists, if not create it
path_document_combined = os.path.join(save_directory, folder_combined, "documents")
if not os.path.exists(path_document_combined):
        os.makedirs(path_document_combined)

for context in context_analysis:
    directory = os.path.join(folder, context)
    scenarios = os.listdir(directory)[1:]
    scenarios.remove('dashboard.yml')

    for scenario in scenarios:
        main_directory = os.path.join(directory, scenario) + directory_to_file

        # Load the data from the directories
        try:
            dataframe_structure = process_files(main_directory, filename_structure)
        except:
            continue
        dataframes = load_data_from_directories(main_directory, filename)
        dataframes['Supply_System'] = dataframes.index

        # Create the scenario directory and the nested directory
        save_path = os.path.join(save_directory, context, scenario, "objective_function_analysis")
        plots_path = os.path.join(save_directory, context, scenario, "objective_functions_plots")
        cluster_path = os.path.join(save_directory, context, scenario, "clustering_analysis")
        os.makedirs(save_path, exist_ok=True)
        os.makedirs(plots_path, exist_ok=True)
        os.makedirs(cluster_path, exist_ok=True)

        # Define the file path to save the DataFrame
        save_file_path = os.path.join(save_path, "Objective_functions_analysis.csv")
        save_file_path_structure = os.path.join(save_path, "System_structure_solutions.csv")

        # Apply kmedoids clustering using optimisation results
        X_scaled, scaler, objective_labels, system_names, percentage_change = data_preprocessing(dataframes)
        n_clusters = test_different_cluster_numbers(X_scaled, cluster_path)
        if n_clusters != 1:
            labels, medoids, selected_systems_names = kmedoids_clustering(X_scaled, n_medoids=n_clusters, system_names=system_names)
            plot_clusters(X_scaled, labels, medoids, cluster_path)
            selected_systems = convert_medoids_to_original_scale(medoids, scaler, objective_labels, selected_systems_names)
            selected_systems.insert(0, 'Supply_System', selected_systems_names)
        else:
            selected_systems = dataframes.copy()
            selected_systems = selected_systems.drop(index='current_DES')

        # Save the DataFrame to a CSV file
        dataframes.to_csv(save_file_path, index=False)
        dataframe_structure.to_csv(save_file_path_structure, index=False)

        # Extract current DES for the selected systems
        base_case = pd.DataFrame(dataframes.loc['current_DES']).T.reset_index(drop=True)

        # Generate and save plots
        dataframes['Supply_System'] = dataframes['Supply_System'].astype('category')
        generate_and_save_plots(dataframes, plots_path)
        systems = selected_systems['Supply_System'].tolist()
        line_graph_plot(main_directory, carriers_profile, systems, plots_path, scenario)
        yearly_profile_plot(main_directory, carriers_profile, systems, plots_path, scenario)

        # In the percentage change Dataframe, keep only the energy systems that are in the selected systems DataFrame
        percentage_change = percentage_change[percentage_change['Supply_System'].isin(selected_systems['Supply_System'])].reset_index(drop=True)

        # Combine the selected systems from different scenarios and contexts in one DataFrame
        if 'Scenario' not in selected_systems.columns:
            selected_systems.insert(1, 'Scenario', scenario)
            selected_systems.insert(2, 'Availability', dict_availabilities[context])
        else:
            selected_systems['Scenario'] = scenario
            selected_systems['Availability'] = dict_availabilities[context]

        # Combine the selected systems from different scenarios and contexts in one DataFrame
        if 'Scenario' not in percentage_change.columns:
            percentage_change.insert(1, 'Scenario', scenario)
            percentage_change.insert(2, 'Availability', dict_availabilities[context])
        else:
            percentage_change['Scenario'] = scenario
            percentage_change['Availability'] = dict_availabilities[context]

        if 'Scenario' not in base_case.columns:
            base_case.insert(1, 'Scenario', scenario)
        else:
            base_case['Scenario'] = scenario

        selected_systems = selected_systems.reset_index(drop=True)
        if selected_systems_combined.empty:
            selected_systems_combined = selected_systems.copy()
        else:
            selected_systems_combined = pd.concat([selected_systems_combined, selected_systems], axis=0, ignore_index=True)

        if percentage_variation.empty:
            percentage_variation = percentage_change.copy()
        else:
            percentage_variation = pd.concat([percentage_variation, percentage_change], axis=0, ignore_index=True)

        if current_DES.empty:
            current_DES = base_case.copy()
        else:
            current_DES = pd.concat([current_DES, base_case], axis=0, ignore_index=True)

        # Combine the selected systems structure from different scenarios and contexts in one DataFrame
        selected_systems_structure = process_energy_system_data(main_directory, selected_systems, filename_structure,
                                                                selected_systems_structure, context, scenario,
                                                                dict_availabilities)
        # Extract network analysis from results
        connectivity_df = process_scenario(connectivity_df, folder, directory_to_file, geojson, demand,
                                           selected_systems, scenario)

current_DES = current_DES.drop_duplicates(subset=['Scenario']).reset_index(drop=True)

# Sort the columns of the selected systems structure DataFrame and fill Nan with 0 for better readability
fixed_columns = selected_systems_structure.iloc[:, :3]
columns_to_sort = selected_systems_structure.iloc[:, 3:].sort_index(axis=1)
selected_systems_structure = pd.concat([fixed_columns, columns_to_sort], axis=1)
selected_systems_structure = selected_systems_structure.fillna(0)

for scenario in scenarios:
    heatmap(percentage_variation, plots_path_combined, scenario)
    scatter_plot(current_DES, selected_systems_combined, plots_path_combined, scenario)
    stellar_chart(selected_systems_structure, plots_path_combined, scenario)
    plot_connectivity(connectivity_df, scenario, plots_path_combined)

# Sort the DataFrames by Scenario and Availability and save them to a CSV file
current_DES = current_DES.set_index('Scenario')
current_DES.to_csv(path_document_combined + "/Current_DES.csv", index=False)
selected_systems_combined = selected_systems_combined.sort_values(by=['Scenario', 'Availability']).reset_index(drop=True)
selected_systems_combined.to_csv(path_document_combined + "/Selected_systems.csv", index=False)
selected_systems_structure = selected_systems_structure.sort_values(by=['Scenario', 'Availability']).reset_index(drop=True)
selected_systems_structure.to_csv(path_document_combined + '/Selected_systems_structure.csv', index=False)
percentage_variation = percentage_variation.sort_values(by=['Scenario', 'Availability']).reset_index(drop=True)
percentage_variation.to_csv(path_document_combined + "/Percentage_variation.csv", index=False)
connectivity_df.to_csv(path_document_combined + '/connectivity_analysis.csv', index=False)
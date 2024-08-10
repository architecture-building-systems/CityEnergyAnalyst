import geopandas as gpd
import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib.lines import Line2D

from directories_files_handler import drop_similar_rows, heat_sinks_analysis

# Define the main directory and the filename
base_directory = "D:/CEATesting/"
main_directory = "D:/CEATesting/THESIS_TEST_CASES_BASE/"
main_directory_ren = "D:/CEATesting/THESIS_TEST_CASES_RENEWABLES/"
directory_to_file = "inputs/building-geometry/zone.shp"
directory_to_surrounding = "inputs/building-geometry/surroundings.shp"
save_directory = "D:/CEATesting/THESIS_TEST_CASES_PLOTS/scenario_representations/"
save_directory_base = "D:/CEATesting/THESIS_TEST_CASES_PLOTS/"
folder_combined = 'combined_analysis'
selected_systems_combined = pd.DataFrame()
current_DES = pd.DataFrame()
singapore_shapefile_path = 'D:/CEATesting/THESIS_TEST_CASES_PLOTS/combined_analysis/Singapore_shapefile/SGP_adm0.shp'
irradiation_plot = 'outputs/data/potentials/solar'
combined_analysis = 'D:\CEATesting\THESIS_TEST_CASES_PLOTS\combined_analysis\documents\Percentage_variation.csv'
selected_systems = 'D:\CEATesting\THESIS_TEST_CASES_PLOTS\combined_analysis\documents\Selected_systems.csv'
selected_systems_structure = 'D:\CEATesting\THESIS_TEST_CASES_PLOTS\combined_analysis\documents\Selected_systems_structure.csv'
network_directory = 'outputs/data/optimization/centralized'
geojson_file = 'networks/N1001_layout.geojson'
connectivity_directory = 'D:\CEATesting\THESIS_TEST_CASES_PLOTS\combined_analysis\documents\connectivity_analysis.csv'
def plot_district_network(selected_systems, base_path, carriers_directory,network_path, geojson_file, scenarios, save_directory):
    """
    Combines a district cooling network from a GeoJSON file with a district shapefile
    and plots the full representation of the network inside the district.

    Parameters:
    - district_shapefile_path: str, path to the shapefile containing the district boundaries.
    - network_geojson_path: str, path to the GeoJSON file containing the district cooling network.
    - output_plot_path: str, optional, path to save the plot. If None, the plot is displayed.
    """
    availability_list = ['THESIS_TEST_CASES_BASE', 'THESIS_TEST_CASES_RENEWABLES']
    availability_dict = {'THESIS_TEST_CASES_BASE': 'No_renewables', 'THESIS_TEST_CASES_RENEWABLES': 'All_renewables'}
    systems = pd.read_csv(selected_systems)

    for avail in availability_list:
        selected_systems_avail = systems[systems['Availability'] == availability_dict[avail]]
        for scenario in scenarios:

            shapefile_path = os.path.join(base_path, avail, scenario, carriers_directory)
            network_path_system = os.path.join(base_path, avail, scenario, network_path)
            district_gdf = gpd.read_file(shapefile_path)
            selected_systems_scenario = selected_systems_avail[selected_systems_avail['Scenario'] == scenario]

            for system in selected_systems_scenario['Supply_System']:
                system_network_path = os.path.join(network_path_system, system, geojson_file)

                # Load the GeoJSON file containing the district cooling network
                network_gdf = gpd.read_file(system_network_path)

                for j, row in network_gdf.iterrows():
                    if 'NODE' in row['index']:
                        if 'CONSUMER' in row['Type']:
                            continue
                        else:
                            network_gdf = network_gdf.drop(index=j)

                network_gdf = network_gdf.reset_index(drop=True)

                # Ensure both GeoDataFrames have the same CRS
                if network_gdf.crs != district_gdf.crs:
                    network_gdf = network_gdf.to_crs(district_gdf.crs)

                # Create a plot of the district with the network overlaid
                fig, ax = plt.subplots(figsize=(10, 10))

                # Plot the district shapefile
                district_gdf.plot(ax=ax, color='lightgray', edgecolor='black', alpha=0.5, label='District')

                # Plot the cooling network
                network_gdf.plot(ax=ax, color='blue', linewidth=2, label='Cooling Network')

                # Add legend and titles
                plt.legend()
                plt.title('District Cooling Network inside District')
                plt.xlabel('Longitude', fontsize=8)
                plt.ylabel('Latitude', fontsize=8)

                # Save or show the plot
                save_path = os.path.join(save_directory, avail, scenario)
                if not os.path.exists(save_path):
                    os.makedirs(save_path)
                plt.savefig(save_path + f'/objective_functions_plots/District_network_{system}.png', bbox_inches='tight')



def calculate_occupation_density(base_path, carriers_directory, directory_to_surrounding, scenarios, save_directory):
    """
    Calculate the total area occupied by buildings, the total area of the district,
    and the density of occupation in a given district.

    Returns:
    dict: A dictionary containing the total building area, total district area, and density of occupation.
    """
    area_analysis = pd.DataFrame(index=scenarios, columns=['total_building_area', 'total_district_area', 'density_of_occupation'])
    # Create a single figure with 8 subplots (2 columns x 4 rows)
    fig, axes = plt.subplots(4, 2, figsize=(20, 20))
    axes = axes.flatten()  # Flatten the 2D array of axes for easy iteration

    for i, scenario in enumerate(scenarios):
        shapefile_path = os.path.join(base_path, scenario, carriers_directory)
        surrounding_path = os.path.join(base_path, scenario, directory_to_surrounding)

        # Check if the path exists
        if not os.path.exists(shapefile_path):
            print(f"Path {shapefile_path} does not exist.")
            continue

        district_gdf = gpd.read_file(shapefile_path)
        surrounding_gdf = gpd.read_file(surrounding_path)

        # Concatenate district buildings with surrounding buildings
        combined_gdf = gpd.GeoDataFrame(pd.concat([district_gdf, surrounding_gdf], ignore_index=True))

        # Calculate the total area of buildings in the district
        total_building_area = combined_gdf['geometry'].area.sum()

        # Create a convex hull around all building geometries
        convex_hull = combined_gdf['geometry'].unary_union.convex_hull

        # Calculate the total area of the convex hull
        total_district_area = convex_hull.area

        # Calculate the density of occupation
        density_of_occupation = round(total_building_area / total_district_area * 100, 1)

        # Store the results in the dictionary
        area_analysis.loc[scenario, 'total_building_area'] = total_building_area
        area_analysis.loc[scenario, 'total_district_area'] = total_district_area
        area_analysis.loc[scenario, 'density_of_occupation'] = density_of_occupation

        ax = axes[i]

        # Plot district buildings in blue
        district_gdf.plot(ax=ax, color='blue', edgecolor='black', alpha=0.5, label='District Buildings')

        # Plot surrounding buildings in green
        surrounding_gdf.plot(ax=ax, color='green', edgecolor='black', alpha=0.5, label='Surrounding Buildings')

        gpd.GeoSeries(convex_hull).plot(ax=ax, color='none', edgecolor='red', linewidth=2, label='Convex Hull')

        ax.set_title(f'{scenario}', pad=15, fontsize=13)
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')

        # Adjust the font size of x and y tick labels
        ax.tick_params(axis='both', which='major', labelsize=6)

    # Create custom legend elements
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='District Buildings', markersize=10,
               markerfacecolor='blue',
               alpha=0.5, markeredgecolor='black'),
        Line2D([0], [0], marker='o', color='w', label='Surrounding Buildings', markersize=10,
               markerfacecolor='green', alpha=0.5, markeredgecolor='black'),
        Line2D([0], [0], color='red', label='Convex Hull', linewidth=2)]

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.suptitle('District Buildings and Surroundings with Convex Hull', fontsize=16)

    # Add the legend to the plot
    fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.95), ncol=1, prop={'size': 15})

    # Save the combined plot
    output_path = os.path.join(save_directory, 'Scenarios_with_buffer_plotted')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    plot_file_path = os.path.join(output_path, 'combined_scenarios.png')
    plt.savefig(plot_file_path)
    plt.close()

    # Return the results as a dictionary
    return area_analysis

def plot_building_height_statistics(scenarios, base_path, directory_to_surrounding, carriers_directory, output_path):
    all_heights = []
    all_heights_surroundings = []
    building_counts = {}

    for scenario in scenarios:
        shapefile_path = os.path.join(base_path, scenario, carriers_directory)
        surrounding_path = os.path.join(base_path, scenario, directory_to_surrounding)

        # Check if the path exists
        if not os.path.exists(shapefile_path):
            print(f"Path {shapefile_path} does not exist.")
            continue
        if not os.path.exists(surrounding_path):
            print(f"Path {surrounding_path} does not exist.")
            continue

        heights = []
        heights_surroundings = []
        gdf = gpd.read_file(shapefile_path)
        gdf_surrounding = gpd.read_file(surrounding_path)

        if 'height_ag' in gdf.columns:
            height_ag_values = gdf['height_ag']
            heights.extend(height_ag_values)
            scenario_df = pd.DataFrame({'Height': heights, 'Scenario': scenario, 'Type': 'Zone'})
            all_heights.append(scenario_df)
            building_counts[scenario] = len(height_ag_values)

        if 'height_ag' in gdf_surrounding.columns:
            height_ag_values_surroundings = gdf_surrounding['height_ag']
            heights_surroundings.extend(height_ag_values_surroundings)
            surroundings_df = pd.DataFrame({'Height': heights_surroundings, 'Scenario': scenario, 'Type': 'Surrounding'})
            all_heights_surroundings.append(surroundings_df)

    # Combine all heights into a single DataFrame
    combined_heights = pd.concat(all_heights)
    combined_heights_surroundings = pd.concat(all_heights_surroundings)
    combined_heights_combined = pd.concat([combined_heights, combined_heights_surroundings])

    # Plotting the statistics
    fig, ax = plt.subplots(figsize=(12, 8))
    palette = sns.color_palette("husl", 2)
    sns.boxplot(x='Scenario', y='Height', hue= 'Type', data=combined_heights_combined, ax=ax, palette=palette, linewidth=2)

    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    ax.set_ylabel('Building Height [m]')
    ax.set_title('Building Height Statistics Across Scenarios', pad=20, fontsize= 14)

    # Annotate the plot with the building counts
    ylim = ax.get_ylim()
    for i, scenario in enumerate(scenarios):
        count = building_counts.get(scenario, 0)
        ax.annotate(f'Buildings: {count}', xy=(i, ylim[1]-ylim[1]*0.02), xytext=(0, 10), textcoords='offset points', ha='center', va='bottom')

    # Save the plot
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    plt.tight_layout()
    plot_file_path = os.path.join(output_path, 'Building_Height_Statistics.png')
    plt.savefig(plot_file_path)
    plt.close(fig)

def plot_zones_with_labels_and_image_background(main_dir, scenarios, end_path, singapore_shapefile_path, save_path):
    fig, ax = plt.subplots(figsize=(12, 12))

    # Load and plot the Singapore outline shapefile
    singapore_gdf = gpd.read_file(singapore_shapefile_path)
    singapore_crs = singapore_gdf.crs  # Get the CRS of the Singapore shapefile
    singapore_gdf.plot(ax=ax, color='lightgrey', edgecolor='black', alpha=0.5)

    # Define colors for each scenario
    colors = plt.cm.viridis(np.linspace(0, 1, len(scenarios)))

    for idx, scenario in enumerate(scenarios):
        shapefile_path = os.path.join(main_dir, scenario, end_path)
        gdf = gpd.read_file(shapefile_path)

        # Reproject the GeoDataFrame to the CRS of the Singapore shapefile
        gdf = gdf.to_crs(singapore_crs)

        # Apply buffer to scale the geometries
        gdf['geometry'] = gdf.geometry.buffer(0.003).to_crs(singapore_crs)

        gdf.loc[:0].plot(ax=ax, edgecolor='black', label=scenario, color=colors[idx])

        # Add labels near the zones
        centroid = gdf.loc[0].geometry.centroid

        # Adjust label position to avoid overlap with geometries and other labels
        if scenario == 'Commercial_Low_Rise':
            dx = -0.033
            dy = 0
        elif scenario == 'Commercial_High_Rise':
            dx = 0.033
            dy = 0
        else:
            dx = 0
            dy = 0.007

        plt.text(centroid.x + dx, centroid.y + dy, scenario, fontsize=8,
                 ha='center', va='center',
                 bbox=dict(facecolor='white', alpha=0.5, edgecolor='black', boxstyle='round,pad=0.3'))

    # Customize the plot
    ax.set_title('Zones in Singapore')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')

    # Adjust layout to make map bigger in the figure
    plt.tight_layout(pad=0)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Remove axis for better visualization
    ax.set_axis_off()

    # Save the combined plot
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    plot_file_path = os.path.join(save_path, "zones_with_labels_and_image_background.png")
    plt.savefig(plot_file_path)
    plt.close('all')

def scenarios_irradiation(area_analysis, base_path, irradiation_directory, scenarios, output_path):

    radiation_per_scenario = pd.DataFrame(index=[0], columns=scenarios)

    for scenario in scenarios:
        building_list = []
        tot_radiation_per_building = []
        file_path = os.path.join(base_path, scenario, irradiation_directory)

        # Check if the path exists
        if not os.path.exists(file_path):
            print(f"Path {file_path} does not exist.")
            return

        buildings = os.listdir(file_path)[1:-1]
        for building in buildings:
            parts = building.split('_')
            if 'B' in parts[0]:
                building_list.append(parts[0])
        building_names = list(set(building_list))
        building_names.sort()

        for name in building_names:
            radiation_file_path = os.path.join(file_path, f'{name}_PV_sensors.csv')
            radiation = pd.read_csv(radiation_file_path, index_col=0)
            # Use radiation specific to area to compare scenarios with different amount of buildings and areas
            tot_radiation = radiation['total_rad_Whm2']
            tot_radiation = np.mean(tot_radiation) / 1e6 # Take the average and convert to MWh
            tot_radiation_per_building.append(tot_radiation)

        radiation_per_scenario[f'{scenario}'][0] = np.mean(tot_radiation_per_building)

    # Plotting the radiation_per_scenario DataFrame
    fig, ax = plt.subplots(figsize=(10, 8))
    radiation_per_scenario = radiation_per_scenario.T  # Transpose for better plotting
    radiation_per_scenario.plot(kind='bar', legend=False, color='orange', ax=ax, edgecolor= 'black')
    ax.set_ylabel('Radiation (MWh/m2)', fontsize=12)
    ax.set_title('Total Yearly Radiation per Scenario', fontsize=14, pad=20)
    ax.set_xticklabels(radiation_per_scenario.index, rotation=45) # Rotate x-labels
    ylim = ax.get_ylim()
    xlim = ax.get_xlim()
    for i, scenario in enumerate(scenarios):
        district = area_analysis.loc[scenario]
        density = district['density_of_occupation']
        if i == 0:
            ax.annotate(f'Building Density in each Scenario:', xy=(xlim[1]/2, ylim[1] - ylim[1] * 0.02), xytext=(0, 10),
                        textcoords='offset points', ha='center', va='bottom')
        ax.annotate(f'{density}%', xy=(i, ylim[1]-ylim[1]*0.06), xytext=(0, 10), textcoords='offset points', ha='center', va='bottom')

    # Use tight layout to fit everything properly
    plt.tight_layout()

    # Save the plot
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    plot_file_path = os.path.join(output_path, 'Total_Radiation_per_Scenario.png')
    plt.savefig(plot_file_path)
    plt.close('all')

def heatmap_combined(df, scenarios, path):

    df = df.rename(columns={'Heat_Emissions_kWh': 'Heat Emissions',
                                                              'System_Energy_Demand_kWh': 'Energy Demand',
                                                              'GHG_Emissions_kgCO2': 'GHG Emissions',
                                                              'Cost_USD': 'Cost'})

    availabilities = ['All_renewables', 'No_renewables']
    # Create a color dictionary for scenarios
    scenario_colors = {scenario: plt.cm.tab10(i) for i, scenario in enumerate(scenarios)}

    # Find the global minimum and maximum values across both heatmaps
    min_val = df[['Energy Demand', 'GHG Emissions', 'Cost']].min().min()
    max_val = df[['Energy Demand', 'GHG Emissions', 'Cost']].max().max()

    for availability in availabilities:
        scenario_selection = pd.DataFrame()
        availability_selection = df[df['Availability'] == availability]
        for scenario in scenarios:
            selection = availability_selection[availability_selection['Scenario'] == scenario]
            cleaned_df = drop_similar_rows(selection, threshold=5)
            scenario_selection = pd.concat([scenario_selection, cleaned_df], axis=0, ignore_index=True)
        scenario_selection = scenario_selection.drop('Heat Emissions', axis=1)
        numeric_values = scenario_selection.iloc[:, 3:]

        # Calculate the number of rows and columns
        num_rows, num_cols = numeric_values.shape

        # Determine figure size based on the number of rows and columns
        fig_width = max(8, num_cols * 1.1)  # Width depends on the number of columns
        fig_height = max(6, num_rows * 0.5)  # Height depends on the number of rows

        # Scaling factors for font sizes
        base_fontsize = 9
        font_scaling_factor = min(fig_width / 8, fig_height / 6)

        plt.figure(figsize=(fig_width, fig_height))
        annot = numeric_values.applymap(lambda x: f'{x:.1f}%')
        sns.heatmap(numeric_values, annot=annot, fmt='', cmap='viridis', cbar=True, linewidths=0.5, linecolor='black',
                    annot_kws={"fontsize": base_fontsize * font_scaling_factor, "fontweight": "bold"},
                    vmin=min_val, vmax=max_val)  # Set the common color scale for all heatmaps

        # Customise plot features
        multi_line_labels = [f'{scena}\n{sys}' for scena, sys in
                             zip(scenario_selection['Scenario'], scenario_selection['Supply_System'])]

        plt.title(f'Heatmap {availability}', fontsize=base_fontsize * font_scaling_factor)
        # Adjust the subplot parameters to move the plot to the right
        plt.subplots_adjust(left=0.25, right=1, top=0.9, bottom=0.1)
        plt.xticks(rotation=0)

        ax = plt.gca()
        ax.set_yticks(np.arange(0.5, len(numeric_values) + 0.5, 1))
        ax.set_yticklabels([])

        # Add colored y-axis labels
        for idx, label in enumerate(multi_line_labels):
            scena, sys = label.split('\n')
            ax.text(-0.05, idx + 0.2, scena, color=scenario_colors[scena], va='center', ha='right',
                    fontsize=base_fontsize * font_scaling_factor, weight='bold')
            ax.text(-0.05, idx + 0.6, sys, color='black', va='center', ha='right',
                    fontsize=base_fontsize * font_scaling_factor)

        plt.savefig(path + f"Heatmap_{availability}.png")

        # Close all figures at once
        plt.close('all')

def hashed_bar_plot(percentage_variation, df_structure, scenarios, plots_path):

    percentage_variation = percentage_variation.rename(columns={'Heat_Emissions_kWh': 'Heat_Emissions',
                            'System_Energy_Demand_kWh': 'Energy_Demand',
                            'GHG_Emissions_kgCO2': 'GHG_Emissions',
                            'Cost_USD': 'Cost'})

    availabilities = ['All_renewables', 'No_renewables']
    scenario_colors = {scenario: plt.cm.tab10(i) for i, scenario in enumerate(scenarios)}

    for availability in availabilities:
        scenario_selection_percentage = pd.DataFrame()

        for scenario in scenarios:

            selection_percentage = percentage_variation[percentage_variation['Scenario'] == scenario]
            cleaned_df_percentage = drop_similar_rows(selection_percentage, threshold=5)
            scenario_selection_percentage = pd.concat([scenario_selection_percentage, cleaned_df_percentage], axis=0,
                                                      ignore_index=True)

        percentage = scenario_selection_percentage.drop(['GHG_Emissions', 'Energy_Demand', 'Cost'], axis=1)

        df_percentage = percentage[percentage['Availability'] == availability].sort_values(by='Heat_Emissions')
        df_percentage.reset_index(drop=True)

        if availability == 'All_renewables':
            df_structure_filtered = df_structure[df_structure['Availability'] == availability]
            heat_sinks = heat_sinks_analysis(df_percentage, df_structure_filtered)
            heat_sinks.to_csv(os.path.join(plots_path, f"heat_sinks_{availability}.csv"), index=False)

        # Plot hashed bar comparison
        fig, ax = plt.subplots(figsize=(12, 10))
        unit_dict = {'Heat_Emissions': 'GWh'}

        # Colors for the bars
        colors = plt.cm.viridis(np.linspace(0, 1, len(df_percentage)))

        base_value = 100
        values = df_percentage['Heat_Emissions']
        font_size = 12

        # Plot the base part of each bar
        for i, value in enumerate(values):
            plt.bar(i, base_value, color=colors[i])
            diff_percentage = values.iloc[i]

            # Plot the difference part of each bar
            if value > 0:
                plt.bar(i, value, bottom=base_value, color='red', hatch='//')  # Above base value
                plt.text(i, base_value + value, f"{diff_percentage:.1f}%", ha='center', va='bottom', fontsize=font_size)
            elif value <= 0:
                plt.bar(i, -value, bottom=base_value + value, color='green', hatch='\\\\')  # Below base value
                plt.text(i, base_value, f"{diff_percentage:.1f}%", ha='center', va='bottom', fontsize=font_size)

        plt.ylabel(f'Heat Emissions [{unit_dict["Heat_Emissions"]}]')
        plt.xlabel('Supply System')
        plt.title(f'Heat Emissions - {availability}')

        # Customise plot features
        x_tick_labels = [f'{scena}\n{sys}' for scena, sys in
                         zip(df_percentage['Scenario'], df_percentage['Supply_System'])]

        # Set x-ticks
        ax.set_xticks(range(len(df_percentage.index)))
        ax.set_xticklabels([])  # Clear default labels

        # Add colored x-axis labels with rotation
        for i, label in enumerate(x_tick_labels):
            scena, sys = label.split('\n')
            ax.text(i - 0.8, -18, scena, color=scenario_colors[scena], va='center', ha='center',
                    fontsize=font_size, weight='bold', rotation=45)
            ax.text(i - 0.5, -20, sys, color='black', va='center', ha='center',
                    fontsize=font_size, rotation=45)

        plt.tight_layout()
        plt.subplots_adjust(left=0.2, right=0.95, top=0.9, bottom=0.2)

        # Save the combined plot
        plot_file_path = os.path.join(plots_path, f"hashed_bar_{availability}.png")
        plt.savefig(plot_file_path)
        plt.close('all')


def scatter_plot_two_dataframes(connectivity, area_analysis, plots_path):
    """
    Plots a scatter plot of two columns from two different DataFrames.

    Parameters:
        df1 (pd.DataFrame): The first DataFrame.
        col1 (str): The column name from the first DataFrame to be plotted on the x-axis.
        df2 (pd.DataFrame): The second DataFrame.
        col2 (str): The column name from the second DataFrame to be plotted on the y-axis.
        xlabel (str): The label for the x-axis.
        ylabel (str): The label for the y-axis.
        title (str): The title of the plot.
    """
    # Set the plot style
    sns.set(style="whitegrid")

    connectivity_district = connectivity[connectivity['availability'] == 'No_renewables']
    area_analysis = area_analysis.reset_index(drop=False).rename(columns={'index': 'scenario'})

    # Extract the data for plotting
    x_data = connectivity_district[['scenario','connected_percentage']]
    y_data = area_analysis[['scenario','density_of_occupation']]

    merged_df = pd.merge(x_data, y_data, on='scenario', how='left')

    # Create the scatter plot
    plt.figure(figsize=(12, 8))
    scatter = sns.scatterplot(data=merged_df, x='connected_percentage', y='density_of_occupation',
                                  s=100, hue='scenario', palette='tab10', legend='full', alpha=0.6)
    # Set the labels and title
    scatter.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), ncol=1)
    # Adjust layout to make room for the legend
    plt.tight_layout(rect=[0,0,1,0.95])
    plt.xlabel('Connected buildings percentage', fontsize=12)
    plt.ylabel('Building density in district', fontsize=12)
    plt.title('District density vs connectivity percentage', fontsize=14)

    # Save the combined plot
    plot_file_path = os.path.join(plots_path, f"connection_density.png")
    plt.savefig(plot_file_path)
    plt.close('all')

# MAIN
scenarios = os.listdir(main_directory)[1:]
scenarios.remove('dashboard.yml')
percentage_variation = pd.read_csv(combined_analysis)
systems = pd.read_csv(selected_systems)
df_structure = pd.read_csv(selected_systems_structure)
connectivity = pd.read_csv(connectivity_directory)

area_analysis = calculate_occupation_density(main_directory, directory_to_file, directory_to_surrounding,
                                             scenarios, save_directory)
scatter_plot_two_dataframes(connectivity, area_analysis, save_directory)
plot_district_network(selected_systems, base_directory, directory_to_file, network_directory, geojson_file, scenarios,
                      save_directory_base)
plot_zones_with_labels_and_image_background(main_directory, scenarios, directory_to_file, singapore_shapefile_path, save_directory)
scenarios_irradiation(area_analysis, main_directory_ren, irradiation_plot, scenarios, save_directory)
plot_building_height_statistics(scenarios, main_directory, directory_to_surrounding, directory_to_file, save_directory)
heatmap_combined(percentage_variation, scenarios, save_directory)
hashed_bar_plot(percentage_variation, df_structure, scenarios, save_directory)

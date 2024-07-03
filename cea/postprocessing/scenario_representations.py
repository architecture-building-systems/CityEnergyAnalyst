import geopandas as gpd
import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib.lines import Line2D

# Define the main directory and the filename
main_directory = "D:/CEATesting/THESIS_TEST_CASES_BASE/"
main_directory_ren = "D:/CEATesting/THESIS_TEST_CASES_RENEWABLES/"
directory_to_file = "inputs/building-geometry/zone.shp"
directory_to_surrounding = "inputs/building-geometry/surroundings.shp"
save_directory = "D:/CEATesting/THESIS_TEST_CASES_PLOTS/scenario_representations/"
folder_combined = 'combined_analysis'
selected_systems_combined = pd.DataFrame()
selected_systems_structure = pd.DataFrame()
percentage_variation = pd.DataFrame()
current_DES = pd.DataFrame()
singapore_shapefile_path = 'D:/CEATesting/THESIS_TEST_CASES_PLOTS/combined_analysis/Singapore_shapefile/SGP_adm0.shp'
irradiation_plot = 'outputs/data/potentials/solar'


def calculate_occupation_density(base_path, carriers_directory, directory_to_surrounding, scenarios, save_directory):
    """
    Calculate the total area occupied by buildings, the total area of the district,
    and the density of occupation in a given district.

    Returns:
    dict: A dictionary containing the total building area, total district area, and density of occupation.
    """
    area_analysis = pd.DataFrame(index=scenarios, columns=['total_building_area', 'total_district_area', 'density_of_occupation'])
    for scenario in scenarios:
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

        # Plot the buildings and the convex hull
        fig, ax = plt.subplots(1, 1, figsize=(10, 10))
        # Plot district buildings in blue
        district_gdf.plot(ax=ax, color='blue', edgecolor='black', alpha=0.5, label='District Buildings')

        # Plot surrounding buildings in green
        surrounding_gdf.plot(ax=ax, color='green', edgecolor='black', alpha=0.5, label='Surrounding Buildings')

        gpd.GeoSeries(convex_hull).plot(ax=ax, color='none', edgecolor='red', linewidth=2, label= 'Convex Hull')

        plt.title(f'Convex Hull for scenario {scenario}', pad=20)
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')

        # Create custom legend elements
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', label='District Buildings', markersize=10, markerfacecolor='blue',
                   alpha=0.5, markeredgecolor='black'),
            Line2D([0], [0], marker='o', color='w', label='Surrounding Buildings', markersize=10,
                   markerfacecolor='green', alpha=0.5, markeredgecolor='black'),
            Line2D([0], [0], color='red', label='Convex Hull', linewidth=2)]

        # Add the legend to the plot
        ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1), ncol=3)

        plt.tight_layout()

        # Save the plot
        output_path = os.path.join(save_directory, 'Scenarios_with_buffer_plotted')
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        plot_file_path = os.path.join(output_path, f'{scenario}.png')
        plt.savefig(plot_file_path)
        plt.close(fig)

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
            tot_radiation = sum(tot_radiation) / 1e9 # Convert to GWh
            tot_radiation_per_building.append(tot_radiation)

        radiation_per_scenario[f'{scenario}'][0] = sum(tot_radiation_per_building)

    # Plotting the radiation_per_scenario DataFrame
    fig, ax = plt.subplots(figsize=(10, 8))
    radiation_per_scenario = radiation_per_scenario.T  # Transpose for better plotting
    radiation_per_scenario.plot(kind='bar', legend=False, color='orange', ax=ax, edgecolor= 'black')
    ax.set_ylabel('Radiation (GWh/m2)', fontsize=12)
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

# Example usage
scenarios = os.listdir(main_directory)[1:]
scenarios.remove('dashboard.yml')

area_analysis = calculate_occupation_density(main_directory, directory_to_file, directory_to_surrounding, scenarios, save_directory)
plot_zones_with_labels_and_image_background(main_directory, scenarios, directory_to_file, singapore_shapefile_path, save_directory)
scenarios_irradiation(area_analysis, main_directory_ren, irradiation_plot, scenarios, save_directory)
plot_building_height_statistics(scenarios, main_directory, directory_to_surrounding, directory_to_file, save_directory)

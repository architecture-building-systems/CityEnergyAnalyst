import geopandas as gpd
import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np

# Define the main directory and the filename
main_directory = "D:/CEATesting/THESIS_TEST_CASES_BASE/"
directory_to_file = "inputs/building-geometry/zone.shp"
save_directory = "D:/CEATesting/THESIS_TEST_CASES_PLOTS/"
folder_combined = 'combined_analysis'
selected_systems_combined = pd.DataFrame()
selected_systems_structure = pd.DataFrame()
percentage_variation = pd.DataFrame()
current_DES = pd.DataFrame()
singapore_shapefile_path = 'D:/CEATesting/THESIS_TEST_CASES_PLOTS/combined_analysis/Singapore_shapefile/SGP_adm0.shp'

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
    plot_file_path = os.path.join(save_path, "zones_with_labels_and_image_background.png")
    plt.savefig(plot_file_path)
    plt.close('all')

# Example usage
scenarios = os.listdir(main_directory)[1:]
scenarios.remove('dashboard.yml')

plot_zones_with_labels_and_image_background(main_directory, scenarios, directory_to_file, singapore_shapefile_path, save_directory)

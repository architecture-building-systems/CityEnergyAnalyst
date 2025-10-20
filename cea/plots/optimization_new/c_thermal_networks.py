import os
import pandas as pd
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt

from cea.inputlocator import InputLocator
import cea.config

def load_geo_data(locator, run_id=None, des_id=None):
    # Load the shapefile
    zone_gdf = gpd.read_file(locator.get_zone_geometry())

    # Load the GeoJSON files for all networks
    networks_folder = locator.get_new_optimization_optimal_networks_folder(run_id, des_id)
    network_ids = [f.split('_')[0] for f in os.listdir(networks_folder) if f.endswith('layout.geojson')]
    network_gdfs = {network_id:
                        gpd.read_file(locator.get_new_optimization_optimal_network_layout_file(run_id, des_id,
                                                                                               network_id))
                    for network_id in network_ids}

    # Check for CRS consistency
    for network_id, network_gdf in network_gdfs.items():
        if zone_gdf.crs != network_gdf.crs:
            print(f"CRS mismatch between zone_gdf and network {network_id}. Reprojecting...")
            network_gdfs[network_id] = network_gdf.to_crs(zone_gdf.crs)

    return zone_gdf, network_gdfs


def plot_geodata(zone_gdf, network_gdfs):
    # Create a base plot with the building footprints
    ax = zone_gdf.plot(figsize=(10, 10), color='lightgray', edgecolor='black', alpha=0.5)

    # Assign a unique color to each network
    colors = mpl.colormaps['tab10'].colors[:len(network_gdfs)]

    # Collect edges for overlap analysis
    all_edges = gpd.GeoDataFrame(geometry=[], crs=zone_gdf.crs)

    for i, (network_id, network_gdf) in enumerate(network_gdfs.items()):
        color = colors[i]
        plot_networks(ax, zone_gdf, network_gdf, color)

        # Collect edges for overlap analysis
        edges_gdf = network_gdf[network_gdf['geometry'].geom_type == 'LineString']
        all_edges = pd.concat([all_edges, edges_gdf])

    # Identify and plot overlapping edges
    overlapping_edges = identify_overlapping_edges(all_edges)
    if not overlapping_edges.empty:
        overlapping_edges.plot(ax=ax, color='red', linewidth=3, linestyle='-', label='Overlapping Edges')

    # Set titles and labels
    plt.title('Building Footprints and Thermal Networks')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')

    # Add legend
    plt.legend()

    # Display the plot
    plt.show()


def plot_networks(ax, zone_gdf, network_gdf, color):
    # Extract the building IDs from the networks_gdf
    connected_building_ids = network_gdf['Building'].unique()

    # Filter the zone_gdf to get only the buildings connected to the network
    connected_buildings_gdf = zone_gdf[zone_gdf['Name'].isin(connected_building_ids)]

    if connected_buildings_gdf.empty:
        print("No connected buildings found for this network. Skipping plot.")
        return

    # Plot the connected buildings in the same color as the network
    connected_buildings_gdf.plot(ax=ax, color=color, edgecolor='black')

    # Filter out intermediary nodes (nodes not connected to buildings)
    nodes_gdf = network_gdf[network_gdf['geometry'].geom_type == 'Point']
    edges_gdf = network_gdf[network_gdf['geometry'].geom_type == 'LineString']

    # Filter nodes that are connected to buildings
    connected_nodes_gdf = nodes_gdf[nodes_gdf['Building'].notna() & (nodes_gdf['Building'] != 'NONE')]

    # Plot the edges (keep all edges)
    edges_gdf.plot(ax=ax, color=color, linewidth=1)

    # Plot the connected nodes (direct connections to buildings)
    connected_nodes_gdf.plot(ax=ax, color=color, markersize=10)


def identify_overlapping_edges(all_edges):
    overlapping_edges = gpd.GeoDataFrame(geometry=[], crs=all_edges.crs)

    # Iterate through each pair of edges to check for full overlap
    for i in range(len(all_edges)):
        for j in range(i + 1, len(all_edges)):
            if all_edges.iloc[i].geometry.equals(all_edges.iloc[j].geometry):
                overlapping_edges = pd.concat([overlapping_edges, all_edges.iloc[[i]], all_edges.iloc[[j]]])

    # Drop duplicate entries (since each overlap will be counted twice in the loop)
    overlapping_edges = overlapping_edges.drop_duplicates()

    return overlapping_edges



def main(config: cea.config.Configuration):
    locator = InputLocator(config.scenario)

    zone_gdf, network_gdfs = load_geo_data(locator, des_id="DCS_101")
    plot_geodata(zone_gdf, network_gdfs)


if __name__ == '__main__':
    main(cea.config.Configuration())

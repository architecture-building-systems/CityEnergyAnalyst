import os
from typing import Tuple

import geopandas as gpd
import pandas as pd
import numpy as np

import cea.inputlocator
from cea.constants import SHAPEFILE_TOLERANCE
from cea.utilities.standardize_coordinates import validate_crs_uses_meters


def load_network_shapefiles(
    locator: cea.inputlocator.InputLocator,
    network_type: str,
    network_name: str
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Load network nodes and edges shapefiles with helpful error messages.

    File structure:
    - Edges: thermal-network/{network-name}/layout.shp
    - Nodes: thermal-network/{network-name}/{network-type}/layout/nodes.shp

    :param locator: InputLocator object
    :param network_type: DH or DC
    :param network_name: Name of network layout
    :return: Tuple of (nodes_gdf, edges_gdf)
    :raises FileNotFoundError: If network layout files do not exist
    """
    edges_path = locator.get_network_layout_shapefile(network_name)
    nodes_path = locator.get_network_layout_nodes_shapefile(network_type, network_name)

    # Check if network layout files exist with helpful error messages
    if not os.path.exists(edges_path):
        raise FileNotFoundError(
            f"{network_type} network layout is missing: {edges_path}\n"
            f"Please run 'Network Layout' (Part 1) first to create the network layout."
        )

    if not os.path.exists(nodes_path):
        demand_type = "cooling" if network_type == "DC" else "heating"
        raise FileNotFoundError(
            f"{network_type} network nodes file is missing: {nodes_path}\n"
            f"This can happen if:\n"
            f"  1. 'Network Layout' (Part 1) was not run yet, OR\n"
            f"  2. The {network_type} network was skipped because no buildings have {demand_type} demand.\n"
            f"     (Check the 'consider-only-buildings-with-demand' setting in Network Layout)\n"
            f"Please verify your buildings have {demand_type} demand and re-run 'Network Layout' (Part 1)."
        )

    nodes_gdf = gpd.read_file(nodes_path)
    edges_gdf = gpd.read_file(edges_path)

    return nodes_gdf, edges_gdf


def extract_network_from_shapefile(edge_shapefile_df: gpd.GeoDataFrame, node_shapefile_df: gpd.GeoDataFrame,
                                   coord_precision: float = SHAPEFILE_TOLERANCE, filter_edges: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extracts network data into DataFrames for pipes and nodes in the network

    :param edge_shapefile_df: GeoDataFrame containing all data imported from the edge shapefile
    :param node_shapefile_df: GeoDataFrame containing all data imported from the node shapefile
    :param coord_precision: precision for coordinate matching between edges and nodes (in number of decimal places)
    :param filter_edges: whether to filter edges that do not have matching start and end nodes
    :type edge_shapefile_df: GeoDataFrame
    :type node_shapefile_df: GeoDataFrame
    :type coord_precision: float
    :type filter_edges: bool
    :return node_df: DataFrame containing all nodes and their corresponding coordinates
    :return edge_df: list of edges and their corresponding lengths and start and end nodes
    :rtype node_df: DataFrame
    :rtype edge_df: DataFrame
    :raises ValueError: If there are duplicated NODE/PIPE IDs or CRS mismatch

    """
    # Check for duplicated NODE/PIPE IDs
    duplicated_nodes = node_shapefile_df[node_shapefile_df.name.duplicated(keep=False)]
    duplicated_edges = edge_shapefile_df[edge_shapefile_df.name.duplicated(keep=False)]
    if duplicated_nodes.size > 0:
        raise ValueError('There are duplicated NODE IDs:', duplicated_nodes.name.values)
    if duplicated_edges.size > 0:
        raise ValueError('There are duplicated PIPE IDs:', duplicated_edges.name.values)

    if edge_shapefile_df.crs != node_shapefile_df.crs:
        raise ValueError('The coordinate reference systems (CRS) of the edge and node shapefiles do not match. '
                         'Please reproject them to the same CRS before proceeding.')

    validate_crs_uses_meters(edge_shapefile_df)

    # sort node_df by index number
    node_shapefile_df = node_shapefile_df.set_index("name").sort_index(
        key=lambda x: x.str.extract(r"NODE(\d+)", expand=False).astype(int)
    )
    node_shapefile_df['coordinates'] = node_shapefile_df['geometry'].apply(lambda x: x.coords[0])

    # sort edge_df by index number
    edge_shapefile_df = edge_shapefile_df.set_index("name").sort_index(
        key=lambda x: x.str.extract(r"PIPE(\d+)", expand=False).astype(int)
    )
    edge_shapefile_df['coordinates'] = edge_shapefile_df['geometry'].apply(lambda x: x.coords[0])

    from scipy.spatial import cKDTree

    # Build KDTree from node coordinates for efficient nearest-neighbor queries
    node_coords = np.array(node_shapefile_df['coordinates'].tolist())
    node_names = node_shapefile_df.index.tolist()
    kdtree = cKDTree(node_coords)

    tolerance_m = 10 ** -coord_precision  # convert precision to tolerance in meters

    # assign edge properties
    edge_shapefile_df['start node'] = ''
    edge_shapefile_df['end node'] = ''
    # Calculate pipe length
    edge_shapefile_df['length_m'] = edge_shapefile_df['geometry'].length

    missing_edges = []
    for pipe_name, row in edge_shapefile_df.iterrows():
        # Get edge endpoints (handles curved LineStrings with multiple vertices)
        edge_coords = list(row['geometry'].coords)
        start_coord = np.array(edge_coords[0])
        end_coord = np.array(edge_coords[-1])  # Use last coord for curved edges

        # Find nearest nodes using KDTree (more robust than coordinate rounding)
        start_dist, start_idx = kdtree.query(start_coord)
        end_dist, end_idx = kdtree.query(end_coord)

        # Check if matches are within tolerance
        if start_dist <= tolerance_m:
            edge_shapefile_df.loc[pipe_name, 'start node'] = node_names[start_idx]
        else:
            missing_edges.append(pipe_name)

        if end_dist <= tolerance_m:
            edge_shapefile_df.loc[pipe_name, 'end node'] = node_names[end_idx]
        else:
            missing_edges.append(pipe_name)

    if missing_edges:
        if filter_edges:
            edge_shapefile_df = edge_shapefile_df.drop(missing_edges)
            print(f"Filtered out {len(missing_edges)} edges that do not have matching start and end nodes within the specified tolerance.")
        else:
            raise ValueError(f"The following edges do not have matching start and end nodes within the specified tolerance: {missing_edges}")
    
    return node_shapefile_df, edge_shapefile_df

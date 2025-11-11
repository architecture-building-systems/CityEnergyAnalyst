import geopandas as gpd
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree

from cea.constants import SHAPEFILE_TOLERANCE
from cea.utilities.standardize_coordinates import validate_crs_uses_meters


def extract_network_from_shapefile(edge_shapefile_df: gpd.GeoDataFrame, node_shapefile_df: gpd.GeoDataFrame,
                                   coord_precision: float = SHAPEFILE_TOLERANCE) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extracts network data into DataFrames for pipes and nodes in the network

    :param edge_shapefile_df: GeoDataFrame containing all data imported from the edge shapefile
    :param node_shapefile_df: GeoDataFrame containing all data imported from the node shapefile
    :param coord_precision: precision for coordinate matching between edges and nodes (in number of decimal places)
    :type edge_shapefile_df: GeoDataFrame
    :type node_shapefile_df: GeoDataFrame
    :type coord_precision: float
    :return node_df: DataFrame containing all nodes and their corresponding coordinates
    :return edge_df: list of edges and their corresponding lengths and start and end nodes
    :rtype node_df: DataFrame
    :rtype edge_df: DataFrame

    """
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
            print(f"Warning: Start node of {pipe_name} has no match within {tolerance_m}m (nearest: {start_dist:.6f}m)")

        if end_dist <= tolerance_m:
            edge_shapefile_df.loc[pipe_name, 'end node'] = node_names[end_idx]
        else:
            print(f"Warning: End node of {pipe_name} has no match within {tolerance_m}m (nearest: {end_dist:.6f}m)")

    return node_shapefile_df, edge_shapefile_df


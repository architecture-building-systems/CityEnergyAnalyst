"""
Plant Node Operations for Network Layout

Utilities for creating and managing plant nodes in thermal networks.
Handles both auto-generated and user-defined network layouts.
"""

import math
import pandas as pd
from geopandas import GeoDataFrame as gdf
from shapely import Point, LineString

from cea.constants import SHAPEFILE_TOLERANCE
from cea.technologies.network_layout.graph_utils import (
    normalize_coords,
    normalize_gdf_geometries
)

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def get_services_from_plant_type(plant_type):
    """
    Extract service configuration from plant node type (reverse of get_plant_type_from_services).

    :param plant_type: Plant type string from nodes.shp (e.g., 'PLANT_hs_ww', 'PLANT_ww_hs', 'PLANT')
    :return: Tuple of (services_list, is_legacy)
             services_list: List of services in priority order (e.g., ['space_heating', 'domestic_hot_water'])
             is_legacy: True if plant_type is just 'PLANT' (backwards compatibility mode)

    Examples:
        'PLANT_hs_ww' → (['space_heating', 'domestic_hot_water'], False)
        'PLANT_ww_hs' → (['domestic_hot_water', 'space_heating'], False)
        'PLANT_hs' → (['space_heating'], False)
        'PLANT_ww' → (['domestic_hot_water'], False)
        'PLANT' → (['space_heating', 'domestic_hot_water'], True)  # legacy default
        'PLANT_DC' → (['space_heating', 'domestic_hot_water'], True)  # DC network, legacy
    """
    # Abbreviation to full service name mapping
    abbrev_to_service = {
        'hs': 'space_heating',
        'ww': 'domestic_hot_water'
    }

    # Check for legacy plant types (no suffix or DC suffix)
    if plant_type == 'PLANT' or plant_type == 'PLANT_DC':
        # Legacy mode: default to both services in default order
        return (['space_heating', 'domestic_hot_water'], True)

    # Extract suffix after 'PLANT_'
    if not plant_type.startswith('PLANT_'):
        # Unexpected format, treat as legacy
        return (['space_heating', 'domestic_hot_water'], True)

    suffix = plant_type[6:]  # Remove 'PLANT_' prefix

    # Parse suffix (e.g., 'hs_ww' → ['hs', 'ww'])
    abbrevs = suffix.split('_')

    # Convert abbreviations to full service names
    services = [abbrev_to_service.get(abbrev, abbrev) for abbrev in abbrevs if abbrev in abbrev_to_service]

    if not services:
        # No valid services found, treat as legacy
        return (['space_heating', 'domestic_hot_water'], True)

    return (services, False)


def get_plant_type_from_services(itemised_dh_services, network_type='DH'):
    """
    Generate plant type name based on service configuration.

    :param itemised_dh_services: List of services in priority order
                                 (e.g., ['space_heating', 'domestic_hot_water'])
    :param network_type: 'DH' or 'DC' (only DH uses service-specific types)
    :return: Plant type string (e.g., 'PLANT_hs_ww', 'PLANT_ww_hs', 'PLANT')
    """
    if network_type == 'DC':
        return 'PLANT'  # DC always uses generic PLANT type

    if not itemised_dh_services or len(itemised_dh_services) == 0:
        # Default: both services in default order
        return 'PLANT_hs_ww'

    # Service abbreviations
    service_abbrev = {
        'space_heating': 'hs',
        'domestic_hot_water': 'ww'
    }

    # Build suffix from service order
    suffix_parts = [service_abbrev.get(svc, svc) for svc in itemised_dh_services]
    suffix = '_'.join(suffix_parts)

    return f'PLANT_{suffix}'


def get_next_node_name(nodes_gdf):
    """
    Generate the next unique node name by finding the maximum existing node number.

    This prevents duplicate node names when nodes are removed from the network during
    plant creation or other operations.

    :param nodes_gdf: GeoDataFrame containing existing nodes with 'name' column
    :return: Unique node name in format 'NODE{n}' where n is max existing number + 1
    """
    existing_node_numbers = [
        int(name.replace('NODE', ''))
        for name in nodes_gdf['name']
        if isinstance(name, str) and name.startswith('NODE')
    ]
    next_node_num = max(existing_node_numbers) + 1 if existing_node_numbers else 0
    return f'NODE{next_node_num}'


def get_next_pipe_name(edges_gdf):
    """
    Generate the next unique pipe name by finding the maximum existing pipe number.

    This prevents duplicate pipe names when edges are added during plant creation
    or when combining edges from multiple networks.

    :param edges_gdf: GeoDataFrame containing existing edges with 'name' column
    :return: Unique pipe name in format 'PIPE{n}' where n is max existing number + 1
    """
    existing_pipe_numbers = [
        int(name.replace('PIPE', ''))
        for name in edges_gdf['name']
        if isinstance(name, str) and name.startswith('PIPE')
    ]
    next_pipe_num = max(existing_pipe_numbers) + 1 if existing_pipe_numbers else 0
    return f'PIPE{next_pipe_num}'


def add_plant_close_to_anchor(building_anchor, new_mst_nodes: gdf, mst_edges: gdf, type_mat, pipe_dn,
                              itemised_dh_services=None, network_type='DH'):
    """
    Add a PLANT node near the anchor building by creating an offset node.

    All coordinates are normalized to SHAPEFILE_TOLERANCE precision to ensure
    proper connectivity with the rest of the network.

    :param building_anchor: GeoDataFrame row containing the anchor building node
    :param new_mst_nodes: GeoDataFrame of network nodes
    :param mst_edges: GeoDataFrame of network edges
    :param type_mat: Pipe material type (e.g., 'T1')
    :param pipe_dn: Pipe diameter (e.g., 150)
    :param itemised_dh_services: List of services in priority order (for DH only)
    :param network_type: 'DH' or 'DC'
    :return: Tuple of (updated nodes_gdf, updated edges_gdf)
    """
    # Find closest NONE node
    copy_of_new_mst_nodes = new_mst_nodes.copy()
    building_coordinates = building_anchor.geometry.values[0].coords
    
    # ✅ Normalize building coordinates
    x1, y1 = normalize_coords([building_coordinates[0]], precision=SHAPEFILE_TOLERANCE)[0]
    
    delta = 10E24  # big number
    node_id = None

    for node in copy_of_new_mst_nodes.iterrows():
        if node[1]['type'] == 'NONE':
            # ✅ Normalize node coordinates for comparison
            x2, y2 = normalize_coords([node[1].geometry.coords[0]], precision=SHAPEFILE_TOLERANCE)[0]
            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if 0 < distance < delta:
                delta = distance
                node_id = node[1]['name']

    if node_id is None:
        # Single building network - no NONE nodes available
        building_node = building_anchor.iloc[0]
        node_id = building_node['name']
        print("    Single-building network: Creating plant node offset from building node")

    # ✅ Get anchor node normalized coordinates
    anchor_node = new_mst_nodes[new_mst_nodes["name"] == node_id].iloc[0]
    anchor_x, anchor_y = normalize_coords([anchor_node.geometry.coords[0]], precision=SHAPEFILE_TOLERANCE)[0]
    
    # ✅ Create plant coordinates with normalization
    plant_coords = normalize_coords([(anchor_x + 1, anchor_y + 1)], precision=SHAPEFILE_TOLERANCE)[0]
    plant_geom = Point(plant_coords)
    
    # Generate unique node name
    plant_node_name = get_next_node_name(new_mst_nodes)

    # Determine plant type based on service configuration
    plant_type = get_plant_type_from_services(itemised_dh_services, network_type)

    # Create plant node with normalized geometry
    plant_node = gdf(
        pd.DataFrame([{
            "name": plant_node_name,
            "type": plant_type,
            "building": "NONE",
            "geometry": plant_geom
        }]),
        crs=new_mst_nodes.crs
    )
    new_mst_nodes = gdf(
        pd.concat([new_mst_nodes, plant_node], ignore_index=True),
        crs=new_mst_nodes.crs
    )
    
    # ✅ Create edge with normalized coordinates
    anchor_coords = (anchor_x, anchor_y)
    edge_coords = [plant_coords, anchor_coords]
    line_geom = LineString(edge_coords)
    edge_weight = line_geom.length
    
    # Get next pipe name using helper function
    pipe_name = get_next_pipe_name(mst_edges)
    
    new_edge = gdf(
        pd.DataFrame([{
            "geometry": line_geom,
            "pipe_DN": pipe_dn,
            "type_mat": type_mat,
            "name": pipe_name,
            "weight": edge_weight
        }]),
        crs=mst_edges.crs
    )
    mst_edges = gdf(
        pd.concat([mst_edges, new_edge], ignore_index=True),
        crs=mst_edges.crs
    )
    
    # ✅ CRITICAL: Final normalization pass to ensure all geometries have consistent precision
    normalize_gdf_geometries(new_mst_nodes, precision=SHAPEFILE_TOLERANCE, inplace=True)
    normalize_gdf_geometries(mst_edges, precision=SHAPEFILE_TOLERANCE, inplace=True)
    
    # Validation: Check for duplicate node names
    if new_mst_nodes['name'].duplicated().any():
        duplicates = new_mst_nodes[new_mst_nodes['name'].duplicated(keep=False)]['name'].unique().tolist()
        raise ValueError(f"Duplicate node names detected after adding plant node: {duplicates}")

    return new_mst_nodes, mst_edges

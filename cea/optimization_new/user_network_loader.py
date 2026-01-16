"""
User-Defined Network Loader and Validator

This module handles loading and validating user-provided thermal network layouts
for the base case in optimization. It supports both shapefile and GeoJSON formats.

Key Features:
- Load network layouts from shapefiles (edges.shp + nodes.shp) or GeoJSON
- Validate required attributes (edges: name, type_mat; nodes: building)
- Check building nodes are within building footprints
- Detect multiple disconnected network components
- Map networks to connectivity states (N1001, N1002, etc.)
"""

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok, Mathias Niffeler"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


import os
import itertools
import pandas as pd
import geopandas as gpd
import networkx as nx
from shapely.geometry import Point
from typing import Tuple, Dict, List, Set

from cea import CEAException

# Tolerance for network topology validation (meters)
# This is much tighter than CEA's general SHAPEFILE_TOLERANCE (6m)
# to ensure precise network connectivity and node placement
NETWORK_TOPOLOGY_TOLERANCE = 0.1  # 10 centimeters - standard GIS precision


class UserNetworkLoaderError(CEAException):
    """Custom exception for user network loading errors"""
    pass


def load_user_defined_network(config, locator, edges_shp=None, nodes_shp=None, geojson_path=None) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame] | None:
    """
    Load user-defined thermal network layout from config parameters.

    Supports two formats:
    1. Separate shapefiles (edges-shp-path + nodes-shp-path)
    2. Combined GeoJSON (network-geojson-path)

    :param config: CEA configuration object
    :param locator: InputLocator object
    :param edges_shp: Optional path to edges shapefile (overrides config)
    :param nodes_shp: Optional path to nodes shapefile (overrides config)
    :param geojson_path: Optional path to GeoJSON file (overrides config)
    :return: Tuple of (nodes_gdf, edges_gdf) or None if no user network provided
    :raises UserNetworkLoaderError: If validation fails or conflicting formats provided
    """
    # Use provided parameters or fall back to config.network_layout
    if edges_shp is None:
        edges_shp = config.network_layout.edges_shp_path if hasattr(config, 'network_layout') else None
    if nodes_shp is None:
        nodes_shp = config.network_layout.nodes_shp_path if hasattr(config, 'network_layout') else None
    if geojson_path is None:
        geojson_path = config.network_layout.network_geojson_path if hasattr(config, 'network_layout') else None

    # Check for conflicting inputs
    shp_provided = bool(edges_shp or nodes_shp)
    geojson_provided = bool(geojson_path)

    if shp_provided and geojson_provided:
        raise UserNetworkLoaderError(
            "Conflicting network layout formats provided:\n"
            "  - Shapefile paths: edges-shp-path and/or nodes-shp-path\n"
            "  - GeoJSON path: network-geojson-path\n\n"
            "These formats are mutually exclusive. Please provide ONLY ONE of:\n"
            "  1. Both 'edges-shp-path' AND 'nodes-shp-path' (shapefile format), OR\n"
            "  2. 'network-geojson-path' (GeoJSON format)\n\n"
            "To use CEA's automatic network generation, leave all three parameters blank."
        )

    # If nothing provided, return None (use automatic generation)
    if not shp_provided and not geojson_provided:
        return None

    # Load from shapefiles
    if shp_provided:
        if not edges_shp or not nodes_shp:
            raise UserNetworkLoaderError(
                "Incomplete shapefile paths provided:\n"
                f"  - edges-shp-path: {'PROVIDED' if edges_shp else 'MISSING'}\n"
                f"  - nodes-shp-path: {'PROVIDED' if nodes_shp else 'MISSING'}\n\n"
                "Both 'edges-shp-path' AND 'nodes-shp-path' must be provided together.\n"
                "To use CEA's automatic network generation, leave both parameters blank."
            )

        nodes_gdf, edges_gdf = _load_from_shapefiles(edges_shp, nodes_shp)

    # Load from GeoJSON
    else:  # geojson_provided
        nodes_gdf, edges_gdf = _load_from_geojson(geojson_path)

    # Convert simplified nodes format to full format if needed
    nodes_gdf = _convert_simplified_nodes_to_full_format(nodes_gdf)

    # Validate required attributes
    _validate_required_attributes(nodes_gdf, edges_gdf)

    return nodes_gdf, edges_gdf


def _load_from_shapefiles(edges_path: str, nodes_path: str) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Load network from separate edge and node shapefiles"""

    # Check files exist
    if not os.path.exists(edges_path):
        raise UserNetworkLoaderError(
            "Edge shapefile not found:\n"
            f"  Path: {edges_path}\n\n"
            "Please check the 'edges-shp-path' parameter in your config."
        )

    if not os.path.exists(nodes_path):
        raise UserNetworkLoaderError(
            "Node shapefile not found:\n"
            f"  Path: {nodes_path}\n\n"
            "Please check the 'nodes-shp-path' parameter in your config."
        )

    # Load shapefiles
    try:
        edges_gdf = gpd.read_file(edges_path)
        nodes_gdf = gpd.read_file(nodes_path)
    except Exception as e:
        raise UserNetworkLoaderError(
            "Error reading shapefiles:\n"
            f"  {str(e)}\n\n"
            "Please ensure files are valid ESRI Shapefiles."
        )

    # Clean empty/null geometries
    edges_before = len(edges_gdf)
    edges_gdf = edges_gdf[edges_gdf.geometry.notna()].copy()
    edges_removed = edges_before - len(edges_gdf)

    nodes_before = len(nodes_gdf)
    nodes_gdf = nodes_gdf[nodes_gdf.geometry.notna()].copy()
    nodes_removed = nodes_before - len(nodes_gdf)

    if edges_removed > 0 or nodes_removed > 0:
        print("  Removed empty/null geometries from shapefiles:")
        if edges_removed > 0:
            print(f"      - {edges_removed} edge feature(s) with no geometry")
        if nodes_removed > 0:
            print(f"      - {nodes_removed} node feature(s) with no geometry")
        print("  Note: Empty features in attribute table are automatically cleaned (in-memory only)")

    # Validate geometries
    if len(edges_gdf) == 0:
        raise UserNetworkLoaderError(
            f"No valid edge features in {edges_path}:\n"
            "  All features have null/empty geometries."
        )

    if len(nodes_gdf) == 0:
        raise UserNetworkLoaderError(
            f"No valid node features in {nodes_path}:\n"
            "  All features have null/empty geometries."
        )

    if not all(edges_gdf.geometry.geom_type == 'LineString'):
        raise UserNetworkLoaderError(
            f"Invalid edge geometry in {edges_path}:\n"
            "  All features must be LineStrings.\n"
            f"  Found: {edges_gdf.geometry.geom_type.unique().tolist()}"
        )

    if not all(nodes_gdf.geometry.geom_type == 'Point'):
        raise UserNetworkLoaderError(
            f"Invalid node geometry in {nodes_path}:\n"
            "  All features must be Points.\n"
            f"  Found: {nodes_gdf.geometry.geom_type.unique().tolist()}"
        )

    return nodes_gdf, edges_gdf


def _load_from_geojson(geojson_path: str) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Load network from combined GeoJSON file"""

    # Check file exists
    if not os.path.exists(geojson_path):
        raise UserNetworkLoaderError(
            "GeoJSON file not found:\n"
            f"  Path: {geojson_path}\n\n"
            "Please check the 'network-geojson-path' parameter in your config."
        )

    # Load GeoJSON
    try:
        gdf = gpd.read_file(geojson_path)
    except Exception as e:
        raise UserNetworkLoaderError(
            "Error reading GeoJSON file:\n"
            f"  {str(e)}\n\n"
            "Please ensure file is valid GeoJSON."
        )

    # Clean empty/null geometries
    features_before = len(gdf)
    gdf = gdf[gdf.geometry.notna()].copy()
    features_removed = features_before - len(gdf)

    if features_removed > 0:
        print(f" Removed {features_removed} feature(s) with empty/null geometries from GeoJSON")
        print("  Note: Empty features are automatically cleaned (in-memory only)")

    if len(gdf) == 0:
        raise UserNetworkLoaderError(
            f"No valid features in GeoJSON:\n"
            f"  Path: {geojson_path}\n\n"
            "  All features have null/empty geometries."
        )

    # Separate nodes and edges by geometry type
    nodes_gdf = gdf[gdf.geometry.geom_type == 'Point'].copy()
    edges_gdf = gdf[gdf.geometry.geom_type == 'LineString'].copy()

    if len(nodes_gdf) == 0:
        raise UserNetworkLoaderError(
            "No Point features found in GeoJSON:\n"
            f"  Path: {geojson_path}\n\n"
            "  - Network layout must include Point features representing nodes."
        )

    if len(edges_gdf) == 0:
        raise UserNetworkLoaderError(
            "No LineString features found in GeoJSON:\n"
            f"  Path: {geojson_path}\n\n"
            "Network layout must include LineString features representing edges."
        )

    return nodes_gdf, edges_gdf


def _convert_simplified_nodes_to_full_format(nodes_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Convert simplified user-provided nodes format to full CEA format.

    Simplified format:
    - Columns: type, geometry
    - type field contains: building name OR "NONE" OR "PLANT"/"PLANT_DC"/"PLANT_DH"

    Full format:
    - Columns: building, name, type, geometry
    - building: building name or "NONE"
    - name: node identifier (NODE0, NODE1, ...)
    - type: CONSUMER, NONE, PLANT, PLANT_DC, PLANT_DH

    :param nodes_gdf: GeoDataFrame in simplified or full format
    :return: GeoDataFrame in full format
    """
    # Normalize column names to lowercase for case-insensitive comparison
    nodes_cols_lower = {col.lower(): col for col in nodes_gdf.columns}

    # Check if already in full format (has 'building' and 'name' columns)
    if 'building' in nodes_cols_lower and 'name' in nodes_cols_lower:
        # Rename columns to lowercase if needed
        nodes_gdf = nodes_gdf.rename(columns={
            nodes_cols_lower['building']: 'building',
            nodes_cols_lower['name']: 'name',
            nodes_cols_lower.get('type', 'type'): 'type'
        })
        return nodes_gdf

    # Check if in simplified format (only has 'type' and 'geometry')
    if 'type' not in nodes_cols_lower:
        raise UserNetworkLoaderError("Invalid nodes format: missing 'type' column (case-insensitive)")

    print("  ℹ Converting simplified nodes format to full format...")

    # Create full format dataframe
    nodes_full = nodes_gdf.copy()

    # Get the actual column name for 'type' (case-insensitive)
    type_col = nodes_cols_lower['type']

    # Initialize new columns
    nodes_full['building'] = 'NONE'
    nodes_full['name'] = [f'NODE{i}' for i in range(len(nodes_full))]
    nodes_full['type_original'] = nodes_full[type_col]  # Keep original for processing

    # Classify nodes based on type field
    plant_types = ['PLANT', 'PLANT_DC', 'PLANT_DH']

    for idx, row in nodes_full.iterrows():
        type_value = str(row['type_original']).strip()

        if type_value.upper() in plant_types:
            # It's a plant node
            nodes_full.loc[idx, 'type'] = type_value.upper()
            nodes_full.loc[idx, 'building'] = 'NONE'
        elif type_value.upper() == 'NONE':
            # It's a junction node
            nodes_full.loc[idx, 'type'] = 'NONE'
            nodes_full.loc[idx, 'building'] = 'NONE'
        else:
            # It's a building node (consumer)
            nodes_full.loc[idx, 'building'] = type_value
            nodes_full.loc[idx, 'type'] = 'CONSUMER'

    # Drop temporary column
    nodes_full = nodes_full.drop(columns=['type_original'])

    # Reorder columns to match full format
    nodes_full = nodes_full[['building', 'name', 'type', 'geometry']]

    print(f"  ✓ Converted {len(nodes_full)} nodes to full format")
    building_count = len(nodes_full[nodes_full['building'] != 'NONE'])
    junction_count = len(nodes_full[(nodes_full['type'] == 'NONE') & (nodes_full['building'] == 'NONE')])
    plant_count = len(nodes_full[nodes_full['type'].str.contains('PLANT', na=False)])
    print(f"    - Buildings: {building_count}, Junctions: {junction_count}, Plants: {plant_count}")

    return nodes_full


def _validate_required_attributes(nodes_gdf: gpd.GeoDataFrame, edges_gdf: gpd.GeoDataFrame):
    """Validate that required attributes exist in the geodataframes (after conversion to full format)"""

    # Normalize column names to lowercase for case-insensitive comparison
    nodes_cols_lower = {col.lower(): col for col in nodes_gdf.columns}
    edges_cols_lower = {col.lower(): col for col in edges_gdf.columns}

    # Check node attributes - should be in full format after conversion
    required_node_attrs = ['building', 'name', 'type']
    missing_node_attrs = [attr for attr in required_node_attrs if attr not in nodes_cols_lower]

    if missing_node_attrs:
        raise UserNetworkLoaderError(
            "Missing required attribute(s) in node features:\n"
            f"  Required: {required_node_attrs}\n"
            f"  Missing: {missing_node_attrs}\n"
            f"  Found: {nodes_gdf.columns.tolist()}\n\n"
            "This error should not occur after format conversion. Please report this issue."
        )

    # Normalize node column names to lowercase
    nodes_gdf.rename(columns={
        nodes_cols_lower['building']: 'building',
        nodes_cols_lower['name']: 'name',
        nodes_cols_lower['type']: 'type'
    }, inplace=True)

    # Check edge attributes
    required_edge_attrs = ['type_mat']
    missing_edge_attrs = [attr for attr in required_edge_attrs if attr not in edges_cols_lower]

    if missing_edge_attrs:
        raise UserNetworkLoaderError(
            "Missing required attribute(s) in edge features:\n"
            f"  Required: {required_edge_attrs}\n"
            f"  Missing: {missing_edge_attrs}\n"
            f"  Found: {edges_gdf.columns.tolist()}\n\n"
            "Edges must have a 'type_mat' attribute (string) specifying pipe material type."
        )

    # Normalize edge column name to lowercase
    edges_gdf.rename(columns={edges_cols_lower['type_mat']: 'type_mat'}, inplace=True)


def _find_edges_reaching_building(
    building_name: str,
    building_geom,
    edges_gdf: gpd.GeoDataFrame,
    tolerance: float = NETWORK_TOPOLOGY_TOLERANCE
) -> List[Tuple[int, Point, float]]:
    """
    Find edges with at least one endpoint inside a building's footprint.

    Returns list of (edge_index, endpoint_inside_building, distance_to_centroid)
    """
    building_centroid = building_geom.centroid
    buffered_building = building_geom.buffer(tolerance)

    edges_reaching_building = []

    for idx, edge_row in edges_gdf.iterrows():
        edge_geom = edge_row.geometry
        start_point = Point(edge_geom.coords[0])
        end_point = Point(edge_geom.coords[-1])

        # Check if either endpoint is inside the building
        if buffered_building.contains(start_point):
            dist_to_centroid = start_point.distance(building_centroid)
            edges_reaching_building.append((idx, start_point, dist_to_centroid))
        elif buffered_building.contains(end_point):
            dist_to_centroid = end_point.distance(building_centroid)
            edges_reaching_building.append((idx, end_point, dist_to_centroid))

    return edges_reaching_building


def validate_network_covers_district_buildings(
    nodes_gdf: gpd.GeoDataFrame,
    buildings_gdf: gpd.GeoDataFrame,
    district_building_names: List[str],
    network_types: List[str],
    edges_gdf: gpd.GeoDataFrame,
    allow_augmentation: bool = False,
    strict_extra_buildings: bool = True
) -> Tuple[gpd.GeoDataFrame, List[str]]:
    """
    Validate that all buildings designated as 'district' in Building Properties/Supply settings have exactly one node
    in the network (matched by exact name, not geometric footprint location).

    Validation checks:
    - All district buildings have exactly one node (by exact name match)
    - No extra buildings in network that aren't designated for district (strict mode) OR warn only (lenient mode)
    - Each building has exactly one node (no duplicates)

    NOTE: This does NOT validate that nodes are within building footprints geometrically.
    L-shaped buildings or complex geometries may have nodes at street access points
    outside the footprint polygon, which is acceptable for practical routing.

    :param nodes_gdf: GeoDataFrame of network nodes
    :param buildings_gdf: GeoDataFrame of building footprints from zone geometry
    :param district_building_names: List of building names that should be on district network
    :param network_types: List of network types (e.g., ['DH', 'DC']) for error messaging
    :param edges_gdf: GeoDataFrame of network edges (unused - no auto-creation occurs)
    :param allow_augmentation: If True, return missing buildings list instead of raising error
    :param strict_extra_buildings: If True (default), raise error when network has extra buildings.
                                   If False, only print warning. Use False when overwrite-supply-settings=True.
    :return: Tuple of (nodes_gdf, missing_buildings_list)
             - If allow_augmentation=False: raises error if buildings missing, returns (nodes_gdf, [])
             - If allow_augmentation=True: returns (nodes_gdf, missing_buildings_list) if buildings missing
    :raises UserNetworkLoaderError: If validation fails
    """

    # Get building nodes (exclude NONE, PLANT, etc.)
    building_nodes = nodes_gdf[nodes_gdf['building'].notna() &
                                (nodes_gdf['building'].fillna('').str.upper() != 'NONE') &
                                (nodes_gdf['type'].fillna('').str.upper() != 'PLANT')].copy()

    network_building_names = set(building_nodes['building'].unique())
    district_building_set = set(district_building_names)

    # Check 1: Are all district buildings represented in the network?
    missing_buildings = district_building_set - network_building_names

    if missing_buildings:
        if allow_augmentation:
            # Return missing buildings for augmentation (caller will handle)
            return nodes_gdf, sorted(list(missing_buildings))
        else:
            # Raise error - strict validation mode
            missing_list = sorted(list(missing_buildings))[:20]
            missing_details = "\n  ".join(missing_list)
            if len(missing_buildings) > 20:
                missing_details += f"\n  ... and {len(missing_buildings) - 20} more"

            raise UserNetworkLoaderError(
                f"User-defined network is missing nodes for {len(missing_buildings)} building(s):\n\n"
                f"  {missing_details}\n\n"
                "These buildings are designated for district connection but have no nodes in the network.\n\n"
                "Resolution:\n"
                "  1. Add nodes for these buildings in your network layout (with 'type' = 'CONSUMER' or 'NONE')\n"
                "  2. Ensure node 'building' attribute exactly matches building names (case-sensitive)\n"
                "  3. Remove these buildings from the connected-buildings parameter if they shouldn't be in the network\n"
                "  4. Enable 'auto-augment-missing-buildings' parameter to automatically extend the network"
            )

    # Check 2: Are there extra buildings in the network that shouldn't be there?
    extra_buildings = network_building_names - district_building_set

    if extra_buildings:
        extra_list = sorted(list(extra_buildings))
        network_type_label = '/'.join(sorted(network_types))

        if strict_extra_buildings:
            # Strict mode (overwrite-supply-settings=False): Raise error
            # supply.csv is authoritative - extra buildings likely indicate mistake
            raise UserNetworkLoaderError(
                f"User-defined network includes buildings NOT designated for district {network_type_label}:\n\n"
                f"  - Buildings designated for district (from Building Properties/Supply): {len(district_building_set)}\n"
                f"  - Buildings found in network nodes: {len(network_building_names)}\n"
                f"  - Extra buildings: {len(extra_buildings)}\n\n"
                "  - Extra building(s) in network:\n  " + "\n  ".join(extra_list[:20]) +
                (f"\n  ... and {len(extra_list) - 20} more" if len(extra_list) > 20 else "") +
                "\n\n"
                "Resolution options:\n"
                "  1. Remove these building nodes from your network layout\n"
                "  2. Update Building Properties/Supply to set these buildings to district-scale systems\n"
                "  3. Set 'overwrite-supply-settings' to True if you want to intentionally include extra buildings\n"
                "  4. Leave network layout parameters blank to let CEA generate the network automatically"
            )
        else:
            # Lenient mode (overwrite-supply-settings=True): Just warn
            # User is experimenting with what-if scenarios - respect their network layout
            print(f"\n  ⚠ Warning: Network includes {len(extra_buildings)} building(s) NOT in 'connected-buildings' parameter:")
            print("    " + ", ".join(extra_list[:10]) +
                  (f" and {len(extra_buildings) - 10} more" if len(extra_buildings) > 10 else ""))
            print("\n    Your network layout will be used as-is (all buildings included).")
            print("    If this is intentional, you can ignore this warning.")
            print("    If you want to exclude them, remove their nodes from your network layout.\n")

    # Check 3: Validate one node per building
    # NOTE: We do NOT validate that nodes are within building footprints because:
    # - L-shaped buildings may have connection points outside the polygon
    # - Complex geometries may have nodes at street access points
    # - Practical routing often places nodes at building edges, not centroids
    # The important validation is that each building has exactly ONE node

    for building_name in district_building_names:
        # Get the building footprint
        building_row = buildings_gdf[buildings_gdf['name'] == building_name]

        if len(building_row) == 0:
            # This shouldn't happen if Supply.csv is consistent with zone geometry
            # But let's be defensive
            raise UserNetworkLoaderError(
                f"Building '{building_name}' listed in Building Properties/Supply as district-connected "
                "but not found in zone geometry (zone.shp).\n"
                "Please ensure Building Properties/Supply and zone geometry are consistent."
            )

        # Get the node for this building
        node_rows = building_nodes[building_nodes['building'] == building_name]

        if len(node_rows) == 0:
            # Already caught in Check 1, but be defensive
            continue

        if len(node_rows) > 1:
            raise UserNetworkLoaderError(
                f"Multiple nodes found for building '{building_name}':\n"
                f"  {len(node_rows)} nodes with 'building' = '{building_name}'\n\n"
                "Each building should have exactly ONE node in the network.\n"
                "Please ensure each building has a unique node."
            )

    # Return nodes (no auto-creation happens - function raises error if buildings missing)
    return nodes_gdf, []


def detect_network_components(
    nodes_gdf: gpd.GeoDataFrame,
    edges_gdf: gpd.GeoDataFrame
) -> Tuple[Dict[int, Set[str]], List[Tuple[str, str, float]], List[Tuple[str, str, str, float]]]:
    """
    Detect disconnected network components using graph analysis.

    Uses PLANT nodes as ground truth for expected number of networks:
    - components == PLANTs: Correct topology
    - components > PLANTs: Auto-snap nearby nodes (gaps detected)
    - components < PLANTs: Error (one network has multiple PLANTs - not supported)

    Returns a dictionary mapping component_id (0, 1, 2, ...) to set of building names in that component.
    Component IDs will be used to create network identifiers (N1001, N1002, etc.)

    :param nodes_gdf: GeoDataFrame of network nodes
    :param edges_gdf: GeoDataFrame of network edges
    :return: Tuple of (component_buildings dict, node-to-node snaps list, edge-to-node snaps list)
             where node-to-node snaps are (node1_name, node2_name, gap_distance)
             and edge-to-node snaps are (edge_name, endpoint, node_name, gap_distance)
    """

    # Track snapped nodes for logging
    snapped_nodes = []  # Component-level snaps (node-to-node)
    edge_snaps = []  # Edge-to-node snaps

    # Count expected number of networks based on PLANT nodes
    plant_nodes = nodes_gdf[nodes_gdf['type'].fillna('').str.upper() == 'PLANT']
    expected_networks = len(plant_nodes)

    if expected_networks == 0:
        raise UserNetworkLoaderError(
            "No PLANT nodes found in network.\n"
            "Each thermal network must have exactly one node with 'type' = 'PLANT'."
        )

    # Build a graph from the edges
    G = nx.Graph()

    # Add all nodes
    for idx, row in nodes_gdf.iterrows():
        node_id = idx  # Use index as node identifier
        G.add_node(node_id, **row.to_dict())

    # Add edges by finding nodes at edge endpoints
    unconnected_edges = []

    for idx, edge_row in edges_gdf.iterrows():
        edge_geom = edge_row.geometry
        start_point = Point(edge_geom.coords[0])
        end_point = Point(edge_geom.coords[-1])

        # Find nodes that match the start and end points
        start_node = None
        end_node = None
        min_dist_to_start = float('inf')
        min_dist_to_end = float('inf')
        nearest_start_building = None
        nearest_end_building = None

        for node_idx, node_row in nodes_gdf.iterrows():
            node_geom = node_row.geometry

            dist_to_start = node_geom.distance(start_point)
            dist_to_end = node_geom.distance(end_point)

            if start_node is None and dist_to_start < NETWORK_TOPOLOGY_TOLERANCE:
                start_node = node_idx
                # Track edge-to-node snap if gap > 0
                if dist_to_start > 0:
                    edge_name = edge_row.get('name', f'Edge_{idx}')
                    node_name = node_row.get('building', node_row.get('name', f'Node_{node_idx}'))
                    edge_snaps.append((edge_name, 'start', node_name, dist_to_start))
            if dist_to_start < min_dist_to_start:
                min_dist_to_start = dist_to_start
                nearest_start_building = node_row.get('building', 'NONE')

            if end_node is None and dist_to_end < NETWORK_TOPOLOGY_TOLERANCE:
                end_node = node_idx
                # Track edge-to-node snap if gap > 0
                if dist_to_end > 0:
                    edge_name = edge_row.get('name', f'Edge_{idx}')
                    node_name = node_row.get('building', node_row.get('name', f'Node_{node_idx}'))
                    edge_snaps.append((edge_name, 'end', node_name, dist_to_end))
            if dist_to_end < min_dist_to_end:
                min_dist_to_end = dist_to_end
                nearest_end_building = node_row.get('building', 'NONE')

            if start_node is not None and end_node is not None:
                break

        if start_node is not None and end_node is not None:
            G.add_edge(start_node, end_node)
        else:
            # Track unconnected edges for error reporting
            edge_name = edge_row.get('name', f'Edge_{idx}')
            unconnected_edges.append({
                'name': edge_name,
                'index': idx,
                'missing_start': start_node is None,
                'missing_end': end_node is None,
                'min_dist_start': min_dist_to_start,
                'min_dist_end': min_dist_to_end,
                'nearest_start_building': nearest_start_building,
                'nearest_end_building': nearest_end_building
            })

    # Report unconnected edges
    if unconnected_edges:
        error_details = []
        for edge in unconnected_edges[:10]:  # Show first 10
            issues = []
            if edge['missing_start']:
                nearest_bldg = edge['nearest_start_building']
                bldg_info = f", building: {nearest_bldg}" if nearest_bldg and nearest_bldg.upper() not in ['NONE', 'PLANT', ''] else ""
                issues.append(f"start node missing (nearest node: {edge['min_dist_start']:.3f}m away{bldg_info})")
            if edge['missing_end']:
                nearest_bldg = edge['nearest_end_building']
                bldg_info = f", building: {nearest_bldg}" if nearest_bldg and nearest_bldg.upper() not in ['NONE', 'PLANT', ''] else ""
                issues.append(f"end node missing (nearest node: {edge['min_dist_end']:.3f}m away{bldg_info})")

            error_details.append(f"  - {edge['name']}: {', '.join(issues)}")

        raise UserNetworkLoaderError(
            f"Network topology error: {len(unconnected_edges)} edge(s) cannot connect to nodes:\n\n"
            + "\n".join(error_details) +
            (f"\n  ... and {len(unconnected_edges) - 10} more" if len(unconnected_edges) > 10 else "") +
            "\n\n"
            f"  - Edges must have nodes at both endpoints within {NETWORK_TOPOLOGY_TOLERANCE}m (tolerance).\n\n"
            "Resolution:\n"
            "  1. Ensure edge endpoints EXACTLY match node coordinates\n"
            f"  2. Use GIS 'Snap' tools to connect edges to nodes (tolerance: {NETWORK_TOPOLOGY_TOLERANCE}m)\n"
            "  3. Check for missing nodes at edge endpoints\n"
            "  4. Verify coordinate precision matches between edges and nodes"
        )

    # Find connected components
    components = list(nx.connected_components(G))

    # Map each component to its building names and validate PLANT nodes
    component_buildings = {}
    component_plants = {}

    for component_id, component_nodes in enumerate(components):
        buildings_in_component = set()
        plants_in_component = []

        for node_idx in component_nodes:
            node_data = G.nodes[node_idx]
            building_name = node_data.get('building', 'NONE')
            node_type = node_data.get('type', 'NONE')

            # Track PLANT nodes (identified by 'type' attribute)
            if node_type and node_type.upper() == 'PLANT':
                plants_in_component.append(node_idx)
            # Track actual building nodes (not NONE, PLANT, etc.)
            elif building_name and building_name.upper() not in ['NONE', '']:
                buildings_in_component.add(building_name)

        # Only include components that have at least one building
        if buildings_in_component:
            component_buildings[component_id] = buildings_in_component
            component_plants[component_id] = plants_in_component

    # Compare component count with expected networks (PLANT count)
    actual_components = len(component_buildings)

    if actual_components < expected_networks:
        # One or more networks have multiple PLANTs - not supported
        raise UserNetworkLoaderError(
            f"Multiple PLANT nodes in same network component detected:\n\n"
            f"  - Expected networks (PLANT nodes): {expected_networks}\n"
            f"  - Detected components: {actual_components}\n\n"
            f"  - This means at least one network has {expected_networks - actual_components + 1} PLANT nodes.\n"
            f"  - CEA does not support multiple PLANT nodes in a single network.\n\n"
            f"Resolution:\n"
            f"  1. Keep only ONE PLANT node per network component\n"
            f"  2. Remove extra PLANT nodes\n"
            f"  3. Ensure each disconnected network has exactly one PLANT"
        )

    elif actual_components > expected_networks:
        # More components than PLANTs - likely gaps in network
        gap_count = actual_components - expected_networks
        print("Network topology issue detected:")
        print(f"  - Expected networks (based on PLANT nodes): {expected_networks}")
        print(f"  - Detected disconnected components: {actual_components}")
        print(f"  - Extra components that need merging: {gap_count}")
        print("\n  Attempting to auto-snap nearby nodes to merge components...")

        # Identify which components have PLANTs and which don't
        components_with_plants = set()
        components_without_plants = set()

        for comp_id, plants in component_plants.items():
            if len(plants) > 0:
                components_with_plants.add(comp_id)
            else:
                components_without_plants.add(comp_id)

        # Try to snap nearby nodes, but only merge components smartly
        snap_threshold = NETWORK_TOPOLOGY_TOLERANCE  # Same as edge-to-node tolerance (10cm)

        for node1_idx, node2_idx in itertools.combinations(G.nodes, 2):
            # Check if nodes are in different components
            comp1 = None
            comp2 = None
            for comp_id, comp_nodes in enumerate(components):
                if node1_idx in comp_nodes:
                    comp1 = comp_id
                if node2_idx in comp_nodes:
                    comp2 = comp_id

            if comp1 == comp2:
                continue  # Already connected

            # Check PLANT distribution before snapping
            comp1_has_plant = comp1 in components_with_plants
            comp2_has_plant = comp2 in components_with_plants

            # Skip if both components have PLANTs (would create invalid topology)
            if comp1_has_plant and comp2_has_plant:
                continue

            # Check if nodes are close
            node1_geom = nodes_gdf.loc[node1_idx].geometry
            node2_geom = nodes_gdf.loc[node2_idx].geometry
            dist = node1_geom.distance(node2_geom)

            if dist < snap_threshold:
                # Snap by adding edge
                G.add_edge(node1_idx, node2_idx)
                node1_name = nodes_gdf.loc[node1_idx].get('building', f'Node_{node1_idx}')
                node2_name = nodes_gdf.loc[node2_idx].get('building', f'Node_{node2_idx}')
                print(f"  ✓ Snapped {node1_name} to {node2_name} (gap: {dist:.3f}m)")

                # Record the snap for logging
                snapped_nodes.append((node1_name, node2_name, dist))

                # Recompute components and PLANT tracking
                components = list(nx.connected_components(G))

                # Rebuild PLANT tracking with new component IDs
                components_with_plants = set()
                components_without_plants = set()
                temp_component_plants = {}

                for comp_id, comp_nodes in enumerate(components):
                    plants = []
                    for node_idx in comp_nodes:
                        node_type = G.nodes[node_idx].get('type', 'NONE')
                        if node_type and node_type.upper() == 'PLANT':
                            plants.append(node_idx)

                    temp_component_plants[comp_id] = plants
                    if len(plants) > 0:
                        components_with_plants.add(comp_id)
                    else:
                        components_without_plants.add(comp_id)

                if len(components) == expected_networks:
                    break  # Success!

        # Recompute component_buildings after snapping
        component_buildings = {}
        component_plants = {}

        for component_id, component_nodes in enumerate(components):
            buildings_in_component = set()
            plants_in_component = []

            for node_idx in component_nodes:
                node_data = G.nodes[node_idx]
                building_name = node_data.get('building', 'NONE')
                node_type = node_data.get('type', 'NONE')

                if node_type and node_type.upper() == 'PLANT':
                    plants_in_component.append(node_idx)
                elif building_name and building_name.upper() not in ['NONE', '']:
                    buildings_in_component.add(building_name)

            if buildings_in_component:
                component_buildings[component_id] = buildings_in_component
                component_plants[component_id] = plants_in_component

        actual_components = len(component_buildings)

        if actual_components > expected_networks:
            # Still have extra components after snapping
            gap_count = actual_components - expected_networks
            raise UserNetworkLoaderError(
                f"Could not merge all network components.\n\n"
                f"  - Expected networks (based on PLANT nodes): {expected_networks}\n"
                f"  - Detected components after auto-snap: {actual_components}\n"
                f"  - Extra components that could not be merged: {gap_count}\n\n"
                f"  - Remaining gaps are larger than {snap_threshold}m threshold.\n\n"
                f"Resolution:\n"
                f"  1. Use GIS 'Snap' tools to connect disconnected edges\n"
                f"  2. Check for gaps larger than {snap_threshold}m in your network\n"
                f"  3. Ensure edges form a continuous path between all buildings"
            )
        else:
            print(f"  ✓ Successfully merged components to {actual_components} network(s)\n")

    # Validate PLANT nodes per network component
    plant_errors = []
    for component_id, buildings in component_buildings.items():
        plant_count = len(component_plants.get(component_id, []))
        network_id = f"N{1001 + component_id}"

        if plant_count == 0:
            plant_errors.append(
                f"  - {network_id} ({len(buildings)} buildings): NO PLANT NODE FOUND"
            )
        elif plant_count > 1:
            plant_errors.append(
                f"  - {network_id} ({len(buildings)} buildings): {plant_count} PLANT nodes (expected 1)"
            )

    if plant_errors:
        raise UserNetworkLoaderError(
            f"PLANT node validation failed for {len(plant_errors)} network component(s):\n\n"
            + "\n".join(plant_errors) +
            "\n\n"
            "Each thermal network requires EXACTLY ONE node with 'type' = 'PLANT'.\n\n"
            "Resolution:\n"
            "  1. Add a PLANT node to networks that are missing one (set 'type' = 'PLANT')\n"
            "  2. Remove duplicate PLANT nodes (keep only one per network)\n"
            "  3. Ensure PLANT nodes are connected to the network via edges"
        )

    return component_buildings, snapped_nodes, edge_snaps


def map_buildings_to_networks(
    nodes_gdf: gpd.GeoDataFrame,
    edges_gdf: gpd.GeoDataFrame,
    district_building_names: List[str]
) -> Tuple[Dict[str, str], List[Tuple[str, str, float]], List[Tuple[str, str, str, float]]]:
    """
    Map each district building to its network identifier (N1001, N1002, etc.).

    :param nodes_gdf: GeoDataFrame of network nodes
    :param edges_gdf: GeoDataFrame of network edges
    :param district_building_names: List of building names on district networks
    :return: Tuple of (building_to_network dict, node-to-node snaps, edge-to-node snaps)
             where building_to_network maps building_name -> network_id (e.g., 'B1001' -> 'N1001')
             node-to-node snaps are (node1_name, node2_name, gap_distance)
             and edge-to-node snaps are (edge_name, endpoint, node_name, gap_distance)
    """

    # Detect network components
    component_buildings, snapped_nodes, edge_snaps = detect_network_components(nodes_gdf, edges_gdf)

    if len(component_buildings) == 0:
        raise UserNetworkLoaderError(
            "No connected network components found with building nodes.\n"
            "Please ensure your network layout includes building nodes with 'building' attribute."
        )

    # Map components to network IDs (N1001, N1002, ...)
    building_to_network = {}

    for component_id, buildings in component_buildings.items():
        network_id = f"N{1001 + component_id}"

        for building_name in buildings:
            building_to_network[building_name] = network_id

    # Verify all district buildings are mapped
    unmapped_buildings = set(district_building_names) - set(building_to_network.keys())

    if unmapped_buildings:
        raise UserNetworkLoaderError(
            "Internal error: Some district buildings are not mapped to networks:\n"
            f"  {unmapped_buildings}\n"
            "This should not happen after validation. Please report this issue."
        )

    return building_to_network, snapped_nodes, edge_snaps


def augment_user_network_with_buildings(
    user_nodes_gdf: gpd.GeoDataFrame,
    user_edges_gdf: gpd.GeoDataFrame,
    zone_gdf: gpd.GeoDataFrame,
    missing_building_names: List[str],
    street_network_gdf: gpd.GeoDataFrame,
    locator,
    snap_tolerance: float = 0.5,
    connection_candidates: int = 3
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Augment user-provided network with additional buildings using Steiner tree optimisation.

    This function extends the user's existing network (edges.shp + nodes.shp) by connecting
    additional buildings that are required by supply.csv or connected-buildings parameter
    but are missing from the user-provided network.

    Algorithm:
    1. Create potential network graph combining user edges + street network
    2. Use Steiner tree optimisation to find optimal paths connecting missing buildings
    3. Merge new edges/nodes with user network (additive-only, never modifies existing)

    :param user_nodes_gdf: User-provided nodes (full format: building, name, type, geometry)
    :param user_edges_gdf: User-provided edges (type_mat, geometry)
    :param zone_gdf: Building footprints from zone geometry
    :param missing_building_names: List of building names to add to network
    :param street_network_gdf: Street network for routing (from locator.get_street_network())
    :param locator: InputLocator for file paths
    :param snap_tolerance: Tolerance for snapping terminal connections (metres)
    :param connection_candidates: Number of nearest streets to consider per building (1-5)
    :return: Tuple of (augmented_nodes_gdf, augmented_edges_gdf) with new buildings added
    """
    from cea.technologies.network_layout.connectivity_potential import create_terminals
    from cea.technologies.network_layout.steiner_spanning_tree import calc_steiner_spanning_tree, get_next_node_name
    from cea.technologies.network_layout.graph_utils import gdf_to_nx, nx_to_gdf, normalize_coords, SHAPEFILE_TOLERANCE

    print(f"\n  Augmenting user network with {len(missing_building_names)} missing building(s)...")
    print(f"    - Buildings to add: {', '.join(sorted(missing_building_names)[:10])}" +
          (f" and {len(missing_building_names) - 10} more" if len(missing_building_names) > 10 else ""))

    # Step 1: Create potential network combining user network + streets for routing
    print("  Step 1/3: Creating potential network graph...")
    potential_graph, building_terminals = _create_terminal_connections_for_buildings(
        user_nodes_gdf=user_nodes_gdf,
        user_edges_gdf=user_edges_gdf,
        zone_gdf=zone_gdf,
        missing_building_names=missing_building_names,
        street_network_gdf=street_network_gdf,
        snap_tolerance=snap_tolerance,
        connection_candidates=connection_candidates
    )

    # Step 2: Use Steiner tree to find optimal subset of edges connecting missing buildings to existing network
    print("  Step 2/3: Optimising network layout using Steiner tree algorithm...")
    print("    - Ensuring new buildings connect to existing user network (user edges will not be modified)")

    import tempfile
    import os
    import shutil

    # Get building geometries and convert to centroids
    missing_buildings_gdf = zone_gdf[zone_gdf['name'].isin(missing_building_names)].copy()
    missing_buildings_centroids = missing_buildings_gdf.copy()
    missing_buildings_centroids['geometry'] = missing_buildings_gdf.geometry.centroid

    # CRITICAL: Add existing user network building nodes as terminals
    # This forces Steiner tree to connect new buildings to existing network
    existing_building_nodes = user_nodes_gdf[
        user_nodes_gdf['building'].notna() &
        (user_nodes_gdf['building'].fillna('').str.upper() != 'NONE')
    ].copy()

    # Convert existing building nodes to centroids format (Point geometries at node location)
    # Use building name as 'name' column for Steiner tree
    existing_terminals = gpd.GeoDataFrame(
        {
            'name': existing_building_nodes['building'].values,
            'geometry': existing_building_nodes['geometry'].values
        },
        crs=existing_building_nodes.crs
    )

    # Combine missing buildings + existing user buildings as terminals
    # Steiner tree will find optimal path connecting ALL terminals
    all_terminals = gpd.GeoDataFrame(
        pd.concat([missing_buildings_centroids[['name', 'geometry']].reset_index(drop=True),
                   existing_terminals[['name', 'geometry']].reset_index(drop=True)],
                  ignore_index=True),
        crs=missing_buildings_centroids.crs
    )

    print(f"    - Terminals: {len(missing_buildings_centroids)} new + {len(existing_terminals)} existing = {len(all_terminals)} total")

    # Create temporary output paths for Steiner tree results
    temp_dir = tempfile.mkdtemp()
    temp_edges_path = os.path.join(temp_dir, 'steiner_edges.shp')
    temp_nodes_path = os.path.join(temp_dir, 'steiner_nodes.shp')

    # Get CRS string
    crs_projected = zone_gdf.crs.to_string()

    # Run Steiner tree optimisation with ALL buildings as terminals
    # This guarantees new buildings connect to existing network
    # Note: This writes directly to shapefiles
    calc_steiner_spanning_tree(
        crs_projected=crs_projected,
        building_centroids_df=all_terminals,  # Include existing + new buildings
        potential_network_graph=potential_graph,
        path_output_edges_shp=temp_edges_path,
        path_output_nodes_shp=temp_nodes_path,
        type_network='DH',  # Doesn't matter for pure topology
        total_demand_location=locator.get_total_demand(),
        plant_building_names=[],  # No plants needed for augmentation
        disconnected_building_names=[],
        method='kou',  # High-quality algorithm
        connection_candidates=connection_candidates
    )

    # Read back the optimised network
    steiner_nodes_gdf = gpd.read_file(temp_nodes_path)
    steiner_edges_gdf = gpd.read_file(temp_edges_path)

    # Clean up temp files
    shutil.rmtree(temp_dir)

    # Step 3: Merge optimised subnetwork with user's original network
    print("  Step 3/3: Merging augmented edges/nodes with user network...")
    augmented_nodes_gdf, augmented_edges_gdf = _merge_augmented_network(
        user_nodes_gdf=user_nodes_gdf,
        user_edges_gdf=user_edges_gdf,
        steiner_nodes_gdf=steiner_nodes_gdf,
        steiner_edges_gdf=steiner_edges_gdf,
        missing_building_names=missing_building_names
    )

    print("  ✓ Augmentation complete:")
    print(f"    - Added {len(augmented_nodes_gdf) - len(user_nodes_gdf)} new node(s)")
    print(f"    - Added {len(augmented_edges_gdf) - len(user_edges_gdf)} new edge(s)")
    print(f"    - Total network: {len(augmented_nodes_gdf)} nodes, {len(augmented_edges_gdf)} edges\n")

    return augmented_nodes_gdf, augmented_edges_gdf


def _create_terminal_connections_for_buildings(
    user_nodes_gdf: gpd.GeoDataFrame,
    user_edges_gdf: gpd.GeoDataFrame,
    zone_gdf: gpd.GeoDataFrame,
    missing_building_names: List[str],
    street_network_gdf: gpd.GeoDataFrame,
    snap_tolerance: float,
    connection_candidates: int
) -> Tuple[nx.Graph, dict]:
    """
    Create potential network graph combining user edges + street network with terminal connections
    to missing buildings.

    Returns:
    - NetworkX graph with all potential edges (user + streets + terminals)
    - Building terminals dict mapping building_name -> (x, y) node coordinate
    """
    from cea.technologies.network_layout.connectivity_potential import create_terminals
    from cea.technologies.network_layout.graph_utils import gdf_to_nx, normalize_coords, SHAPEFILE_TOLERANCE

    # Get building geometries for missing buildings
    missing_buildings_gdf = zone_gdf[zone_gdf['name'].isin(missing_building_names)].copy()

    # Convert building polygons to centroids (create_terminals expects Point geometries)
    missing_buildings_centroids_gdf = missing_buildings_gdf.copy()
    missing_buildings_centroids_gdf['geometry'] = missing_buildings_gdf.geometry.centroid

    # Combine user edges + street network (both are potential routing options)
    combined_network_gdf = gpd.GeoDataFrame(
        pd.concat([user_edges_gdf, street_network_gdf], ignore_index=True),
        crs=user_edges_gdf.crs
    )

    # Create terminal connections for missing buildings to combined network
    # This connects each building to k-nearest street/edge points
    network_with_terminals_gdf = create_terminals(
        building_centroids=missing_buildings_centroids_gdf,
        street_network=combined_network_gdf,
        connection_candidates=connection_candidates
    )

    # Convert to NetworkX graph
    potential_graph = gdf_to_nx(
        network_with_terminals_gdf,
        coord_precision=SHAPEFILE_TOLERANCE,
        preserve_geometry=True
    )

    # Extract building terminal coordinates (normalized to SHAPEFILE_TOLERANCE precision)
    building_terminals = {}
    for building_name in missing_building_names:
        building_row = missing_buildings_centroids_gdf[missing_buildings_centroids_gdf['name'] == building_name]
        if len(building_row) > 0:
            building_geom = building_row.iloc[0].geometry  # Already a Point (centroid)
            # Normalize terminal point coordinates
            coord = normalize_coords([building_geom.coords[0]], SHAPEFILE_TOLERANCE)[0]
            building_terminals[building_name] = coord

    # Store terminal mapping in graph metadata
    potential_graph.graph['building_terminals'] = building_terminals
    potential_graph.graph['crs'] = user_edges_gdf.crs

    return potential_graph, building_terminals


def _merge_augmented_network(
    user_nodes_gdf: gpd.GeoDataFrame,
    user_edges_gdf: gpd.GeoDataFrame,
    steiner_nodes_gdf: gpd.GeoDataFrame,
    steiner_edges_gdf: gpd.GeoDataFrame,
    missing_building_names: List[str]
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Merge user's original network with Steiner tree subnetwork for missing buildings.

    Strategy:
    - User edges: Keep all (never modify existing)
    - User nodes: Keep all (never modify existing)
    - Steiner edges: Add only new edges not already in user network
    - Steiner nodes: Add only new nodes for missing buildings + junction nodes

    Returns:
    - Augmented nodes GeoDataFrame
    - Augmented edges GeoDataFrame
    """
    from cea.technologies.network_layout.graph_utils import normalize_coords, SHAPEFILE_TOLERANCE

    # 1. Merge edges - keep all user edges, add new Steiner edges
    # Steiner tree output may include edges from the user's original network
    # We need to filter those out to avoid duplicates

    # Get user edge coordinates (start-end pairs) for deduplication
    user_edge_coords = set()
    for idx, row in user_edges_gdf.iterrows():
        geom = row.geometry
        start = normalize_coords([geom.coords[0]], SHAPEFILE_TOLERANCE)[0]
        end = normalize_coords([geom.coords[-1]], SHAPEFILE_TOLERANCE)[0]
        # Store as sorted tuple so (A,B) == (B,A)
        edge_coords = tuple(sorted([start, end]))
        user_edge_coords.add(edge_coords)

    # Filter Steiner edges - only add new ones
    new_steiner_edges = []
    for idx, row in steiner_edges_gdf.iterrows():
        geom = row.geometry
        start = normalize_coords([geom.coords[0]], SHAPEFILE_TOLERANCE)[0]
        end = normalize_coords([geom.coords[-1]], SHAPEFILE_TOLERANCE)[0]
        edge_coords = tuple(sorted([start, end]))

        if edge_coords not in user_edge_coords:
            new_steiner_edges.append(row)

    # Combine user edges + new Steiner edges
    if new_steiner_edges:
        augmented_edges_gdf = gpd.GeoDataFrame(
            pd.concat([user_edges_gdf, gpd.GeoDataFrame(new_steiner_edges, crs=user_edges_gdf.crs)], ignore_index=True),
            crs=user_edges_gdf.crs
        )
    else:
        augmented_edges_gdf = user_edges_gdf.copy()

    # 2. Merge nodes - keep all user nodes, add new building nodes for missing buildings

    # Get existing node names and coordinates to avoid conflicts
    existing_node_names = set(user_nodes_gdf['name'].tolist())
    user_node_coords = set()
    for idx, row in user_nodes_gdf.iterrows():
        coord = normalize_coords([row.geometry.coords[0]], SHAPEFILE_TOLERANCE)[0]
        user_node_coords.add(coord)

    # Extract building nodes from Steiner result for missing buildings ONLY
    new_building_nodes = steiner_nodes_gdf[
        steiner_nodes_gdf['building'].isin(missing_building_names)
    ].copy()

    # Rename building nodes if they conflict with existing names
    node_rename_counter = 1
    for idx, row in new_building_nodes.iterrows():
        old_name = row['name']
        if old_name in existing_node_names:
            # Rename to avoid conflict
            while True:
                new_name = f"{old_name}_n{node_rename_counter}"
                if new_name not in existing_node_names:
                    new_building_nodes.at[idx, 'name'] = new_name
                    existing_node_names.add(new_name)
                    break
                node_rename_counter += 1
        else:
            existing_node_names.add(old_name)

    # Extract junction nodes from Steiner result (nodes with building='NONE' and type='NONE')
    # These are intermediate routing points that may be needed
    new_junction_nodes = steiner_nodes_gdf[
        (steiner_nodes_gdf['building'].fillna('').str.upper() == 'NONE') &
        (steiner_nodes_gdf['type'].fillna('').str.upper() == 'NONE')
    ].copy()

    # Rename new junction nodes to avoid conflicts by adding '_n' suffix
    # This makes it clear which nodes were added during augmentation
    for idx, row in new_junction_nodes.iterrows():
        old_name = row['name']
        # Keep trying suffixes until we find a unique name
        while True:
            new_name = f"{old_name}_n{node_rename_counter}"
            if new_name not in existing_node_names:
                new_junction_nodes.at[idx, 'name'] = new_name
                existing_node_names.add(new_name)
                break
            node_rename_counter += 1

    # Deduplicate junction nodes - avoid duplicates with existing user nodes by coordinate
    # The Steiner tree may include nodes from the user's original network that we don't want to duplicate
    unique_junction_nodes = []
    for idx, row in new_junction_nodes.iterrows():
        coord = normalize_coords([row.geometry.coords[0]], SHAPEFILE_TOLERANCE)[0]
        if coord not in user_node_coords:
            unique_junction_nodes.append(row)
            user_node_coords.add(coord)  # Track to avoid duplicates within new nodes

    # Combine: user nodes + new building nodes + unique junction nodes
    augmented_nodes_gdf = gpd.GeoDataFrame(
        pd.concat([
            user_nodes_gdf,
            new_building_nodes,
            gpd.GeoDataFrame(unique_junction_nodes, crs=user_nodes_gdf.crs) if unique_junction_nodes else gpd.GeoDataFrame(columns=user_nodes_gdf.columns, crs=user_nodes_gdf.crs)
        ], ignore_index=True),
        crs=user_nodes_gdf.crs
    )

    return augmented_nodes_gdf, augmented_edges_gdf

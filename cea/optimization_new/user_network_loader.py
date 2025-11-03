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
import geopandas as gpd
import pandas as pd
import networkx as nx
from shapely.geometry import Point, LineString
from typing import Tuple, Dict, List, Set

# Tolerance for network topology validation (meters)
# This is much tighter than CEA's general SHAPEFILE_TOLERANCE (6m)
# to ensure precise network connectivity and node placement
NETWORK_TOPOLOGY_TOLERANCE = 0.01  # 1 centimeter - standard GIS precision


class UserNetworkLoaderError(Exception):
    """Custom exception for user network loading errors"""
    pass


def load_user_defined_network(config, locator) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame] | None:
    """
    Load user-defined thermal network layout from config parameters.

    Supports two formats:
    1. Separate shapefiles (edges-shp-path + nodes-shp-path)
    2. Combined GeoJSON (network-geojson-path)

    :param config: CEA configuration object
    :param locator: InputLocator object
    :return: Tuple of (nodes_gdf, edges_gdf) or None if no user network provided
    :raises UserNetworkLoaderError: If validation fails or conflicting formats provided
    """
    edges_shp = config.optimization_new.edges_shp_path
    nodes_shp = config.optimization_new.nodes_shp_path
    geojson_path = config.optimization_new.network_geojson_path

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

    # Validate geometries
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

    # Separate nodes and edges by geometry type
    nodes_gdf = gdf[gdf.geometry.geom_type == 'Point'].copy()
    edges_gdf = gdf[gdf.geometry.geom_type == 'LineString'].copy()

    if len(nodes_gdf) == 0:
        raise UserNetworkLoaderError(
            "No Point features found in GeoJSON:\n"
            f"  Path: {geojson_path}\n\n"
            "Network layout must include Point features representing nodes."
        )

    if len(edges_gdf) == 0:
        raise UserNetworkLoaderError(
            "No LineString features found in GeoJSON:\n"
            f"  Path: {geojson_path}\n\n"
            "Network layout must include LineString features representing edges."
        )

    return nodes_gdf, edges_gdf


def _validate_required_attributes(nodes_gdf: gpd.GeoDataFrame, edges_gdf: gpd.GeoDataFrame):
    """Validate that required attributes exist in the geodataframes"""

    # Check node attributes
    required_node_attrs = ['building']
    missing_node_attrs = [attr for attr in required_node_attrs if attr not in nodes_gdf.columns]

    if missing_node_attrs:
        raise UserNetworkLoaderError(
            "Missing required attribute(s) in node features:\n"
            f"  Required: {required_node_attrs}\n"
            f"  Missing: {missing_node_attrs}\n"
            f"  Found: {nodes_gdf.columns.tolist()}\n\n"
            "Nodes must have a 'building' attribute (string) matching building names.\n"
            "Non-building nodes should have 'building' = 'NONE' or similar."
        )

    # Check edge attributes
    required_edge_attrs = ['type_mat']
    missing_edge_attrs = [attr for attr in required_edge_attrs if attr not in edges_gdf.columns]

    if missing_edge_attrs:
        raise UserNetworkLoaderError(
            "Missing required attribute(s) in edge features:\n"
            f"  Required: {required_edge_attrs}\n"
            f"  Missing: {missing_edge_attrs}\n"
            f"  Found: {edges_gdf.columns.tolist()}\n\n"
            "Edges must have a 'type_mat' attribute (string) specifying pipe material type."
        )


def validate_network_covers_district_buildings(
    nodes_gdf: gpd.GeoDataFrame,
    buildings_gdf: gpd.GeoDataFrame,
    district_building_names: List[str],
    network_type: str
) -> None:
    """
    Validate that all buildings designated as 'district' in Supply.csv have:
    1. A corresponding node in the network
    2. That node is within the building's footprint (with tolerance)

    :param nodes_gdf: GeoDataFrame of network nodes
    :param buildings_gdf: GeoDataFrame of building footprints from zone geometry
    :param district_building_names: List of building names that should be on district network
    :param network_type: 'DH' or 'DC' for error messaging
    :raises UserNetworkLoaderError: If validation fails with detailed diagnostics
    """

    # Get building nodes (exclude NONE, PLANT, etc.)
    building_nodes = nodes_gdf[nodes_gdf['building'].notna() &
                                (nodes_gdf['building'].str.upper() != 'NONE') &
                                (nodes_gdf['building'].str.upper() != 'PLANT')].copy()

    network_building_names = set(building_nodes['building'].unique())
    district_building_set = set(district_building_names)

    # Check 1: Are all district buildings represented in the network?
    missing_buildings = district_building_set - network_building_names

    if missing_buildings:
        missing_list = sorted(list(missing_buildings))
        raise UserNetworkLoaderError(
            f"User-defined network does not cover all district {network_type} buildings:\n\n"
            f"Buildings requiring district connection (from Building Properties/l): {len(district_building_set)}\n"
            f"Buildings found in network nodes: {len(network_building_names)}\n"
            f"Missing buildings: {len(missing_buildings)}\n\n"
            "Missing building(s):\n  " + "\n  ".join(missing_list[:20]) +
            (f"\n  ... and {len(missing_list) - 20} more" if len(missing_list) > 20 else "") +
            "\n\n"
            "Resolution options:\n"
            "  1. Add nodes with 'building' attribute for missing buildings to your network layout\n"
            "  2. Update Building Properties/Supply to set these buildings to building-scale systems\n"
            "  3. Leave network layout parameters blank to let CEA generate the network automatically"
        )

    # Check 2: Are there extra buildings in the network that shouldn't be there?
    extra_buildings = network_building_names - district_building_set

    if extra_buildings:
        extra_list = sorted(list(extra_buildings))
        raise UserNetworkLoaderError(
            f"User-defined network includes buildings NOT designated for district {network_type}:\n\n"
            f"Buildings designated for district (from Building Properties/Supply): {len(district_building_set)}\n"
            f"Buildings found in network nodes: {len(network_building_names)}\n"
            f"Extra buildings: {len(extra_buildings)}\n\n"
            "Extra building(s) in network:\n  " + "\n  ".join(extra_list[:20]) +
            (f"\n  ... and {len(extra_list) - 20} more" if len(extra_list) > 20 else "") +
            "\n\n"
            "Resolution options:\n"
            "  1. Remove these building nodes from your network layout\n"
            "  2. Update Building Properties/Supply to set these buildings to district-scale systems\n"
            "  3. Leave network layout parameters blank to let CEA generate the network automatically"
        )

    # Check 3: Are building nodes within their respective building footprints?
    # Ensure CRS matches
    if nodes_gdf.crs != buildings_gdf.crs:
        nodes_gdf = nodes_gdf.to_crs(buildings_gdf.crs)

    misplaced_nodes = []

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

        building_geom = building_row.iloc[0].geometry

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

        node_geom = node_rows.iloc[0].geometry

        # Check if node is within building footprint (with tolerance)
        buffered_building = building_geom.buffer(NETWORK_TOPOLOGY_TOLERANCE)

        if not buffered_building.contains(node_geom):
            distance = node_geom.distance(building_geom)
            misplaced_nodes.append((building_name, distance))

    if misplaced_nodes:
        # Sort by distance (worst offenders first)
        misplaced_nodes.sort(key=lambda x: x[1], reverse=True)

        error_details = "\n".join([
            f"  - {name}: {dist:.3f} m from building footprint"
            for name, dist in misplaced_nodes[:20]
        ])

        if len(misplaced_nodes) > 20:
            error_details += f"\n  ... and {len(misplaced_nodes) - 20} more"

        raise UserNetworkLoaderError(
            "Building nodes are outside their respective building footprints:\n\n"
            f"Found {len(misplaced_nodes)} node(s) outside building footprints (tolerance: {NETWORK_TOPOLOGY_TOLERANCE} m):\n"
            f"{error_details}\n\n"
            "Resolution:\n"
            "  - Move each building's node to be within its building footprint\n"
            "  - Nodes should typically be placed at building centroids or connection points\n"
            "  - Use GIS software to verify node positions against building geometries"
        )


def detect_network_components(
    nodes_gdf: gpd.GeoDataFrame,
    edges_gdf: gpd.GeoDataFrame
) -> Dict[int, Set[str]]:
    """
    Detect disconnected network components using graph analysis.

    Returns a dictionary mapping component_id (0, 1, 2, ...) to set of building names in that component.
    Component IDs will be used to create network identifiers (N1001, N1002, etc.)

    :param nodes_gdf: GeoDataFrame of network nodes
    :param edges_gdf: GeoDataFrame of network edges
    :return: Dict mapping component_id -> set of building names
    """

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
            if dist_to_start < min_dist_to_start:
                min_dist_to_start = dist_to_start
                nearest_start_building = node_row.get('building', 'NONE')

            if end_node is None and dist_to_end < NETWORK_TOPOLOGY_TOLERANCE:
                end_node = node_idx
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
            f"Edges must have nodes at both endpoints within {NETWORK_TOPOLOGY_TOLERANCE}m (tolerance).\n\n"
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

            # Track PLANT nodes
            if building_name and building_name.upper() == 'PLANT':
                plants_in_component.append(node_idx)
            # Track actual building nodes (not NONE, PLANT, etc.)
            elif building_name and building_name.upper() not in ['NONE', '']:
                buildings_in_component.add(building_name)

        # Only include components that have at least one building
        if buildings_in_component:
            component_buildings[component_id] = buildings_in_component
            component_plants[component_id] = plants_in_component

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
            "Each thermal network requires EXACTLY ONE node with 'building' = 'PLANT'.\n\n"
            "Resolution:\n"
            "  1. Add a PLANT node to networks that are missing one\n"
            "  2. Remove duplicate PLANT nodes (keep only one per network)\n"
            "  3. Ensure PLANT nodes are connected to the network via edges"
        )

    return component_buildings


def map_buildings_to_networks(
    nodes_gdf: gpd.GeoDataFrame,
    edges_gdf: gpd.GeoDataFrame,
    district_building_names: List[str]
) -> Dict[str, str]:
    """
    Map each district building to its network identifier (N1001, N1002, etc.).

    :param nodes_gdf: GeoDataFrame of network nodes
    :param edges_gdf: GeoDataFrame of network edges
    :param district_building_names: List of building names on district networks
    :return: Dict mapping building_name -> network_id (e.g., 'B1001' -> 'N1001')
    """

    # Detect network components
    component_buildings = detect_network_components(nodes_gdf, edges_gdf)

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

    return building_to_network

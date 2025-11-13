import os
from dataclasses import dataclass, field

import geopandas as gpd
import pandas as pd

import cea.config
import cea.inputlocator
from cea.technologies.network_layout.connectivity_potential import calc_connectivity_network_with_geometry
from cea.technologies.network_layout.steiner_spanning_tree import calc_steiner_spanning_tree
from cea.technologies.network_layout.substations_location import calc_building_centroids
from cea.technologies.network_layout.graph_utils import nx_to_gdf

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def get_buildings_from_supply_csv(locator, network_type):
    """
    Read supply.csv and return list of buildings configured for district heating/cooling.

    :param locator: InputLocator instance
    :param network_type: "DH" or "DC"
    :return: List of building names
    """
    supply_df = pd.read_csv(locator.get_building_supply())

    # Read assemblies database to map codes to scale (DISTRICT vs BUILDING)
    if network_type == "DH":
        assemblies_df = pd.read_csv(locator.get_database_assemblies_supply_heating())
        system_type_col = 'supply_type_hs'
    else:  # DC
        assemblies_df = pd.read_csv(locator.get_database_assemblies_supply_cooling())
        system_type_col = 'supply_type_cs'

    # Create mapping: code -> scale (DISTRICT/BUILDING)
    scale_mapping = assemblies_df.set_index('code')['scale'].to_dict()

    # Filter buildings with DISTRICT scale
    supply_df['scale'] = supply_df[system_type_col].map(scale_mapping)
    district_buildings = supply_df[supply_df['scale'] == 'DISTRICT']['name'].tolist()

    return district_buildings


def get_buildings_with_demand(locator, network_type):
    """
    Read total_demand.csv and return list of buildings with heating/cooling demand.

    :param locator: InputLocator instance
    :param network_type: "DH" or "DC"
    :return: List of building names
    """
    total_demand = pd.read_csv(locator.get_total_demand())

    if network_type == "DH":
        field = "QH_sys_MWhyr"
    else:  # DC
        field = "QC_sys_MWhyr"

    buildings_with_demand = total_demand[total_demand[field] > 0.0]['name'].tolist()
    return buildings_with_demand


def auto_create_plant_nodes(nodes_gdf, edges_gdf, zone_gdf, plant_building_name, network_type, locator, expected_num_components=None):
    """
    Auto-create missing PLANT nodes in user-defined networks.

    Mimics auto-generation behavior:
    1. Find anchor building (user-specified or highest demand)
    2. Find closest junction node (type='NONE') to anchor building
    3. Create new PLANT node offset 1m from junction
    4. Create new edge connecting plant to junction

    :param nodes_gdf: GeoDataFrame of network nodes
    :param edges_gdf: GeoDataFrame of network edges
    :param zone_gdf: GeoDataFrame of building geometries
    :param plant_building_name: User-specified plant building (or empty string)
    :param network_type: "DH" or "DC"
    :param locator: InputLocator instance
    :param expected_num_components: Expected number of disconnected components (optional, for validation)
    :return: Tuple of (updated nodes_gdf, updated edges_gdf, list of created plants)
    """
    import networkx as nx
    from shapely.geometry import Point

    print(f"[auto_create_plant_nodes] expected_num_components = {expected_num_components}")

    # Check if any plants already exist
    existing_plants = nodes_gdf[nodes_gdf['type'].fillna('').str.upper() == 'PLANT']
    print(f"[auto_create_plant_nodes] Found {len(existing_plants)} existing PLANT nodes")

    # Build graph to detect components (need to do this even if plants exist, for validation)
    # Note: User-defined networks may not have start_node/end_node columns yet
    # We need to match edges to nodes by geometry

    # Match edges to nodes by geometry (tolerance of 10cm)
    TOPOLOGY_TOLERANCE = 0.1  # 10cm in meters

    # First pass: identify missing nodes at edge endpoints and auto-create them
    missing_nodes = {}  # key: (x, y), value: (exact Point, list of edge names)

    for edge_idx, edge in edges_gdf.iterrows():
        edge_geom = edge.geometry
        edge_name = edge.get('name', f'Edge_{edge_idx}')
        start_point = Point(edge_geom.coords[0])
        end_point = Point(edge_geom.coords[-1])

        # Check if nodes exist at endpoints
        start_has_node = any(
            node.geometry.distance(start_point) < TOPOLOGY_TOLERANCE
            for _, node in nodes_gdf.iterrows()
        )
        end_has_node = any(
            node.geometry.distance(end_point) < TOPOLOGY_TOLERANCE
            for _, node in nodes_gdf.iterrows()
        )

        # Track missing endpoints with exact coordinates (not rounded)
        if not start_has_node:
            # Use rounded key for deduplication, but store exact point
            key = (round(start_point.x, 3), round(start_point.y, 3))
            if key not in missing_nodes:
                missing_nodes[key] = (start_point, [])
            missing_nodes[key][1].append(edge_name)

        if not end_has_node:
            # Use rounded key for deduplication, but store exact point
            key = (round(end_point.x, 3), round(end_point.y, 3))
            if key not in missing_nodes:
                missing_nodes[key] = (end_point, [])
            missing_nodes[key][1].append(edge_name)

    # Auto-create missing junction nodes
    if missing_nodes:
        print(f"  ⚠ Found {len(missing_nodes)} missing junction node(s) at edge endpoints")
        print("    Auto-creating junction nodes to ensure network connectivity...")

        for key, (exact_point, edge_names) in missing_nodes.items():
            new_node = gpd.GeoDataFrame([{
                'name': f'NODE{len(nodes_gdf)}',
                'building': 'NONE',
                'type': 'NONE',
                'geometry': exact_point  # Use exact coordinates from edge endpoint
            }], crs=nodes_gdf.crs)
            nodes_gdf = pd.concat([nodes_gdf, new_node], ignore_index=True)
            print(f"      - Created NODE{len(nodes_gdf)-1} at ({exact_point.x:.2f}, {exact_point.y:.2f}) for edges: {', '.join(edge_names[:3])}")

    # Now build graph with complete node set
    G = nx.Graph()
    for idx, node in nodes_gdf.iterrows():
        G.add_node(idx, **node.to_dict())

    for edge_idx, edge in edges_gdf.iterrows():
        edge_geom = edge.geometry
        start_point = Point(edge_geom.coords[0])
        end_point = Point(edge_geom.coords[-1])

        start_node_idx = None
        end_node_idx = None

        # Find nodes that match edge endpoints
        for node_idx, node in nodes_gdf.iterrows():
            node_geom = node.geometry

            if start_node_idx is None and node_geom.distance(start_point) < TOPOLOGY_TOLERANCE:
                start_node_idx = node_idx

            if end_node_idx is None and node_geom.distance(end_point) < TOPOLOGY_TOLERANCE:
                end_node_idx = node_idx

            if start_node_idx is not None and end_node_idx is not None:
                break

        # Add edge to graph if both endpoints found
        if start_node_idx is not None and end_node_idx is not None:
            G.add_edge(start_node_idx, end_node_idx)

    components = list(nx.connected_components(G))
    print(f"[auto_create_plant_nodes] Detected {len(components)} connected component(s)")

    if len(components) == 0:
        return nodes_gdf, edges_gdf, []

    # Validate number of components if expected_num_components is specified
    if expected_num_components is not None:
        actual_num_components = len(components)
        if actual_num_components != expected_num_components:
            # Provide context-specific error message
            if actual_num_components == 1:
                context_msg = (
                    f"  - Your network has only 1 connected component but you expected {expected_num_components}.\n"
                    f"    → This means your network is fully connected (no gaps).\n"
                    f"    → Update 'number-of-components' to 1, or leave it blank to skip validation.\n"
                )
            elif actual_num_components < expected_num_components:
                context_msg = (
                    f"  - Your network has fewer components ({actual_num_components}) than expected ({expected_num_components}).\n"
                    f"    → Some components may be unintentionally connected.\n"
                    f"    → Update 'number-of-components' to {actual_num_components}, or leave it blank to skip validation.\n"
                )
            else:  # actual > expected
                context_msg = (
                    f"  - Your network has more components ({actual_num_components}) than expected ({expected_num_components}).\n"
                    f"    → Your network has unintentional gaps/disconnections.\n"
                    f"    → Check edges.shp for missing connections, or update 'number-of-components' to {actual_num_components}.\n"
                )

            raise ValueError(
                f"Network component mismatch:\n"
                f"  Expected: {expected_num_components} component(s)\n"
                f"  Found: {actual_num_components} disconnected component(s) in provided network\n\n"
                f"{context_msg}"
            )

    # If plants already exist, no need to auto-create (but we still ran validation above)
    if len(existing_plants) > 0:
        print("[auto_create_plant_nodes] Plants already exist, skipping auto-creation")
        return nodes_gdf, edges_gdf, []

    # Get building nodes for analysis
    building_nodes = nodes_gdf[nodes_gdf['building'].notna() &
                                (nodes_gdf['building'].fillna('').str.upper() != 'NONE') &
                                (nodes_gdf['type'].fillna('').str.upper() != 'PLANT')].copy()

    # Load demand data to find anchor building
    total_demand = pd.read_csv(locator.get_total_demand())
    demand_field = "QH_sys_MWhyr" if network_type == "DH" else "QC_sys_MWhyr"

    created_plants = []

    # For each component, create plant if needed
    for component_id, component_nodes in enumerate(components):
        # Get buildings in this component
        buildings_in_component = []
        for node_idx in component_nodes:
            if node_idx in building_nodes.index:
                building_name = building_nodes.loc[node_idx, 'building']
                buildings_in_component.append(building_name)

        if not buildings_in_component:
            continue  # Skip components with no buildings

        # Determine anchor building
        anchor_building = None

        if plant_building_name:
            # Use user-specified building if it's in this component
            if plant_building_name in buildings_in_component:
                anchor_building = plant_building_name

        if not anchor_building:
            # Find building with highest demand (anchor load)
            component_demand = total_demand[total_demand['name'].isin(buildings_in_component)]
            if not component_demand.empty and demand_field in component_demand.columns:
                anchor_idx = component_demand[demand_field].idxmax()
                anchor_building = component_demand.loc[anchor_idx, 'name']
            else:
                # Fallback: use first building alphabetically
                anchor_building = sorted(buildings_in_component)[0]

        # Get anchor building node
        anchor_node = building_nodes[building_nodes['building'] == anchor_building]
        if anchor_node.empty:
            continue

        # Simply update the anchor building node's type to PLANT
        # This is simpler and avoids creating duplicate nodes for the same building
        anchor_node_idx = anchor_node.index[0]
        anchor_node_name = nodes_gdf.loc[anchor_node_idx, 'name']

        # Update the type to PLANT
        nodes_gdf.loc[anchor_node_idx, 'type'] = 'PLANT'

        # Generate network identifier for reporting
        network_id = f"N{1001 + component_id}"

        created_plants.append({
            'network_id': network_id,
            'building': anchor_building,
            'node_name': anchor_node_name,
            'junction_node': None,
            'distance_to_junction': 0.0,
            'reason': 'user-specified' if plant_building_name and plant_building_name == anchor_building else 'anchor-load'
        })

    return nodes_gdf, edges_gdf, created_plants


def resolve_plant_building(plant_building_input, available_buildings):
    """
    Resolve plant building name with flexible matching.

    - Parses comma-separated input (takes first value)
    - Case-insensitive matching against available buildings
    - Returns matched building name or empty string if no match
    - Logs the resolution process

    :param plant_building_input: User input (can be comma-separated, any case)
    :param available_buildings: List of actual building names in the scenario
    :return: Matched building name or empty string
    """
    if not plant_building_input or not plant_building_input.strip():
        print("  ℹ Plant building: Not specified - will use anchor load (building with highest demand)")
        return ""

    # Parse comma-separated input and take first value
    input_parts = [s.strip() for s in plant_building_input.split(',') if s.strip()]

    if not input_parts:
        return ""

    first_input = input_parts[0]

    # Log if multiple buildings were provided
    if len(input_parts) > 1:
        print(f"  ℹ Plant building: Multiple buildings provided '{plant_building_input}'")
        print(f"    Using first value: '{first_input}'")

    # Case-insensitive matching
    input_lower = first_input.lower()
    building_map = {b.lower(): b for b in available_buildings}

    if input_lower in building_map:
        matched_building = building_map[input_lower]
        if matched_building != first_input:
            print(f"  ℹ Plant building: Matched '{first_input}' to '{matched_building}' (case-insensitive)")
        else:
            print(f"  ℹ Plant building: Using '{matched_building}' as anchor for plant placement")
        return matched_building
    else:
        print(f"  ⚠ Warning: Plant building '{first_input}' not found in connected buildings")
        print(f"    Available buildings: {', '.join(sorted(available_buildings)[:5])}" +
              (f" ... and {len(available_buildings) - 5} more" if len(available_buildings) > 5 else ""))
        print("    Plant will be placed at building with highest demand (default)")
        return ""


def layout_network(network_layout, locator: cea.inputlocator.InputLocator, plant_building_name=None):
    if plant_building_name is None:
        plant_building_name = ""
    total_demand_location = locator.get_total_demand()

    type_network = "DH"
    list_district_scale_buildings = network_layout.connected_buildings

    # Resolve plant building name (case-insensitive, handles comma-separated input)
    plant_building_name = resolve_plant_building(plant_building_name, list_district_scale_buildings)
    consider_only_buildings_with_demand = False
    allow_looped_networks = False
    steiner_algorithm = network_layout.algorithm

    path_streets_shp = locator.get_street_network()  # shapefile with the stations
    path_zone_shp = locator.get_zone_geometry()

    zone_df = gpd.GeoDataFrame.from_file(path_zone_shp)

    # Calculate points where the substations will be located (building centroids)
    building_centroids_df = calc_building_centroids(
        zone_df,
        list_district_scale_buildings,
        [plant_building_name] if plant_building_name else [],
        consider_only_buildings_with_demand,
        type_network,
        total_demand_location,
    )
    
    street_network_df = gpd.GeoDataFrame.from_file(path_streets_shp)

    # Calculate potential network graph with geometry preservation and building terminal metadata
    potential_network_graph = calc_connectivity_network_with_geometry(
        street_network_df,
        building_centroids_df,
    )

    # Convert graph to GeoDataFrame for Steiner tree algorithm
    crs_projected = potential_network_graph.graph['crs']
    potential_network_df = nx_to_gdf(potential_network_graph, crs=crs_projected, preserve_geometry=True)
    potential_network_df['length'] = potential_network_df.geometry.length
    
    if crs_projected is None:
        raise ValueError("The CRS of the potential network shapefile is undefined. Please check if the input street network has a defined projection system.")

    # Ensure building centroids is in projected crs
    building_centroids_df = building_centroids_df.to_crs(crs_projected)

    # calc minimum spanning tree and save results to disk
    path_output_edges_shp = locator.get_network_layout_edges_shapefile(type_network, network_layout.network_name)
    path_output_nodes_shp = locator.get_network_layout_nodes_shapefile(type_network, network_layout.network_name)
    os.makedirs(os.path.dirname(path_output_edges_shp), exist_ok=True)
    os.makedirs(os.path.dirname(path_output_nodes_shp), exist_ok=True)

    disconnected_building_names = []

    calc_steiner_spanning_tree(crs_projected,
                               building_centroids_df,
                               potential_network_df,
                               path_output_edges_shp,
                               path_output_nodes_shp,
                               type_network,
                               total_demand_location,
                               allow_looped_networks,
                               [plant_building_name] if plant_building_name else [],
                               disconnected_building_names,
                               steiner_algorithm)



# FIXME: Set network type as empty string for workaround
network_type = ""

@dataclass
class NetworkLayout:
    network_name: str
    connected_buildings: list[str]
    algorithm: str = ""

    # TODO: Remove unused fields
    pipe_diameter: float = 0.0
    type_mat: str = ""
    allow_looped_networks: bool = False
    consider_only_buildings_with_demand: bool = False

    disconnected_buildings: list[str] = field(default_factory=list)

    @classmethod
    def from_config(cls, network_layout, locator: cea.inputlocator.InputLocator) -> 'NetworkLayout':
        network_name = cls._validate_network_name(network_layout.network_name, locator)

        return cls(network_name=network_name,
                   connected_buildings=network_layout.connected_buildings,
                   algorithm=network_layout.algorithm)

    @staticmethod
    def _validate_network_name(network_name: str, locator: cea.inputlocator.InputLocator) -> str:
        if network_name is None or not network_name.strip():
            raise ValueError(
                "Network name is required. Provide a descriptive name for this network layout variant "
                "(e.g., 'all-connected')."
            )
        # Ensure network name is stripped of flanking whitespaces
        network_name = network_name.strip()

        # Safety check: Verify network doesn't already exist (backend validation fallback)
        output_folder = locator.get_output_thermal_network_type_folder(network_type, network_name)
        if os.path.exists(output_folder):
            edges_path = locator.get_network_layout_edges_shapefile(network_type, network_name)
            nodes_path = locator.get_network_layout_nodes_shapefile(network_type, network_name)
            if os.path.exists(edges_path) or os.path.exists(nodes_path):
                raise ValueError(
                    f"Network with name '{network_name}' already exists. "
                    "Choose a different name or delete the existing network."
                )
        return network_name


def process_user_defined_network(config, locator, network_layout, edges_shp, nodes_shp, geojson_path, plant_building_name):
    """
    Process user-defined network layout from shapefiles or GeoJSON.

    :param config: Configuration instance
    :param locator: InputLocator instance
    :param network_layout: NetworkLayout instance
    :param edges_shp: Path to edges shapefile (optional)
    :param nodes_shp: Path to nodes shapefile (optional)
    :param geojson_path: Path to GeoJSON file (optional)
    :param plant_building_name: Plant building name from config
    :return: True if network was saved successfully, False if should fall back to automatic generation
    """

    # Import validation functions from user_network_loader
    from cea.optimization_new.user_network_loader import (
        load_user_defined_network,
        validate_network_covers_district_buildings
    )

    # Load and validate user-defined network
    try:
        result = load_user_defined_network(config, locator, edges_shp, nodes_shp, geojson_path)
    except Exception as e:
        print(f"\n✗ Error loading user-defined network: {e}\n")
        print("=" * 80 + "\n")
        raise

    nodes_gdf, edges_gdf = result

    print(f"  - Nodes: {len(nodes_gdf)}")
    print(f"  - Edges: {len(edges_gdf)}")

    overwrite_supply = config.network_layout.overwrite_supply_settings
    connected_buildings_config = config.network_layout.connected_buildings

    # Get building nodes from user-provided network
    building_nodes = nodes_gdf[nodes_gdf['building'].notna() &
                               (nodes_gdf['building'].fillna('').str.upper() != 'NONE') &
                               (nodes_gdf['type'].fillna('').str.upper() != 'PLANT')].copy()
    network_building_names = sorted(building_nodes['building'].unique())

    # ALWAYS validate that network building names exist in zone geometry
    # This prevents accidentally loading a network from a different scenario (e.g., Jakarta network for Singapore scenario)
    all_zone_buildings = locator.get_zone_building_names()
    zone_gdf = gpd.read_file(locator.get_zone_geometry())

    # Check if ALL network buildings exist in the scenario's zone geometry
    invalid_buildings = [b for b in network_building_names if b not in all_zone_buildings]
    if invalid_buildings:
        raise ValueError(
            f"User-defined network contains building names that don't exist in scenario:\n\n"
            f"  Scenario: {config.scenario}\n"
            f"  Buildings in zone geometry: {len(all_zone_buildings)}\n"
            f"  Buildings in network: {len(network_building_names)}\n"
            f"  Invalid building names (not in zone.shp): {len(invalid_buildings)}\n\n"
            f"  Invalid buildings:\n    " + "\n    ".join(invalid_buildings[:20]) +
            (f"\n    ... and {len(invalid_buildings) - 20} more" if len(invalid_buildings) > 20 else "") +
            "\n\n"
            "This usually means you're using a network layout from a different scenario.\n"
            "Resolution:\n"
            "  1. Verify you're using the correct network layout for this scenario\n"
            "  2. Check that building names in the network match the zone geometry\n"
            "  3. Update the network layout to use correct building names"
        )

    # Determine which buildings should be in the network
    if overwrite_supply:
        # Use connected-buildings parameter (what-if scenarios)
        # Check if connected-buildings was explicitly set or auto-populated with all zone buildings
        is_explicitly_set = (connected_buildings_config and
                           set(connected_buildings_config) != set(all_zone_buildings))

        if is_explicitly_set:
            # User explicitly specified a subset of buildings
            buildings_to_validate = connected_buildings_config
            print("  - Mode: Overwrite supply.csv (using connected-buildings parameter)")
            print(f"  - Connected buildings (from config): {len(buildings_to_validate)}")
            print(f"  - Buildings in user layout: {len(network_building_names)}")
        else:
            # Blank connected-buildings (auto-populated): accept whatever is in user layout
            # BUT we already validated building names exist in zone geometry above
            print("  - Mode: Overwrite supply.csv (connected-buildings blank)")
            print(f"  - Using buildings from user-provided layout: {len(network_building_names)}")
            for building_name in network_building_names[:10]:
                print(f"      - {building_name}")
            if len(network_building_names) > 10:
                print(f"      ... and {len(network_building_names) - 10} more")
            buildings_to_validate = network_building_names  # Validate these buildings exist and have nodes
    else:
        # Use supply.csv to determine district buildings
        if config.network_layout.connected_buildings_filter == 'buildings_with_district_cooling':
            buildings_to_validate = get_buildings_from_supply_csv(locator, network_type='DC')
            buildings_with_demand = get_buildings_with_demand(locator, network_type='DC')
            buildings_without_demand = [b for b in buildings_to_validate if b not in buildings_with_demand]
        elif config.network_layout.connected_buildings_filter == 'buildings_with_district_heating':
            buildings_to_validate = get_buildings_from_supply_csv(locator, network_type='DH')
            buildings_with_demand = get_buildings_with_demand(locator, network_type='DH')
            buildings_without_demand = [b for b in buildings_to_validate if b not in buildings_with_demand]
        else:
            buildings_to_validate_dc = get_buildings_from_supply_csv(locator, network_type='DC')
            buildings_with_demand_dc = get_buildings_with_demand(locator, network_type='DC')
            buildings_without_demand_dc = [b for b in buildings_to_validate_dc if b not in buildings_with_demand_dc]

            buildings_to_validate_dh = get_buildings_from_supply_csv(locator, network_type='DH')
            buildings_with_demand_dh = get_buildings_with_demand(locator, network_type='DH')
            buildings_without_demand_dh = [b for b in buildings_to_validate_dh if b not in buildings_with_demand_dh]

            buildings_to_validate = list(set(buildings_to_validate_dc) | set(buildings_to_validate_dh))
            buildings_with_demand = list(set(buildings_with_demand_dc) | set(buildings_with_demand_dh))
            buildings_without_demand = list(set(buildings_without_demand_dc) | set(buildings_without_demand_dh))

        print("  - Mode: Use Building Properties/Supply settings")
        print(f"  - District buildings: {len(buildings_to_validate)}")
        print(f"  - Buildings in user layout: {len(network_building_names)}")

    if buildings_without_demand:
        print(f"  Warning: {len(buildings_without_demand)} building(s) have no {network_type} demand:")
        for building_name in buildings_without_demand[:10]:
            print(f"      - {building_name}")
        if len(buildings_without_demand) > 10:
            print(f"      ... and {len(buildings_without_demand) - 10} more")
        print("  Note: These buildings will be included in layout but may not be simulated in thermal-network")

    # Validate network covers all specified buildings
    nodes_gdf, auto_created_buildings = validate_network_covers_district_buildings(
        nodes_gdf,
        zone_gdf,  # Already loaded above for validation
        buildings_to_validate,
        network_type,
        edges_gdf
    )

    if auto_created_buildings:
        print(f"  Auto-created {len(auto_created_buildings)} missing building node(s):")
        for building_name, edge_name in auto_created_buildings[:10]:
            print(f"      - {building_name} (at endpoint of {edge_name})")
        if len(auto_created_buildings) > 10:
            print(f"      ... and {len(auto_created_buildings) - 10} more")
        print("  Note: Nodes created at edge endpoints inside building footprints")
    else:
        print("  ✓ All specified buildings have valid nodes in network")

    # Resolve plant building name (case-insensitive, handles comma-separated input)
    plant_building_name = resolve_plant_building(plant_building_name, buildings_to_validate)

    # Auto-create plant nodes if missing (zone_gdf already loaded above)
    # Get expected number of components from config
    expected_num_components = config.network_layout.number_of_components if config.network_layout.number_of_components else None
    print(f"[process_user_defined_network] number_of_components from config: {config.network_layout.number_of_components} -> expected_num_components: {expected_num_components}")

    nodes_gdf, edges_gdf, created_plants = auto_create_plant_nodes(
        nodes_gdf, edges_gdf, zone_gdf,
        plant_building_name, network_type, locator,
        expected_num_components
    )

    if created_plants:
        print(f"\n Auto-assigned {len(created_plants)} building node(s) as PLANT:")
        for plant_info in created_plants:
            reason_text = "user-specified anchor" if plant_info['reason'] == 'user-specified' else "anchor load (highest demand)"
            print(f"      - {plant_info['node_name']}: building '{plant_info['building']}' ({reason_text})")
        print("  Note: Existing building nodes converted to PLANT type")

    # Save to network-name location
    output_layout_path = locator.get_network_layout_edges_shapefile(network_type, network_layout.network_name)
    output_terminal_path = locator.get_network_layout_nodes_shapefile(network_type, network_layout.network_name)

    # Ensure output directory exists
    output_folder = os.path.dirname(output_edges_path)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Save to shapefiles
    edges_gdf.to_file(output_edges_path, driver='ESRI Shapefile')
    nodes_gdf.to_file(output_nodes_path, driver='ESRI Shapefile')

    print("\n  ✓ User-defined network saved to:")
    print(f"    {output_folder}")
    print("\n" + "=" * 80 + "\n")


def main(config: cea.config.Configuration):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    network_layout = NetworkLayout.from_config(config.network_layout, locator)
    plant_building_name = config.network_layout.plant_building

    print(f"Network name: {network_layout.network_name} (user-defined)")

    # Check if user provided custom network layout
    edges_shp = config.network_layout.edges_shp_path
    nodes_shp = config.network_layout.nodes_shp_path
    geojson_path = config.network_layout.network_geojson_path

    # Generate network layout from user-defined files if provided
    if edges_shp or nodes_shp or geojson_path:
        print("\n" + "=" * 80)
        print("USER-DEFINED NETWORK LAYOUT")
        print("=" * 80 + "\n")

        process_user_defined_network(
            config, locator, network_layout,
            edges_shp, nodes_shp, geojson_path,
            plant_building_name
        )

    # Generate network layout using Steiner tree (current behavior or fallback)
    else:
        print("\n" + "=" * 80)
        print("AUTOMATIC NETWORK LAYOUT GENERATION")
        print("=" * 80 + "\n")
        layout_network(network_layout, locator, plant_building_name=plant_building_name)


if __name__ == '__main__':
    main(cea.config.Configuration())

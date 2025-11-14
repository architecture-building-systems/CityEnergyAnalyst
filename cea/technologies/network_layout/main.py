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


def print_demand_warning(buildings_without_demand, service_name):
    if buildings_without_demand:
        print(f"  Warning: {len(buildings_without_demand)} building(s) have no {service_name} demand:")
        for building_name in buildings_without_demand[:10]:
            print(f"      - {building_name}")
        if len(buildings_without_demand) > 10:
            print(f"      ... and {len(buildings_without_demand) - 10} more")
        print("  Note: These buildings will be included in layout but may not be simulated in thermal-network")


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


def auto_create_plant_nodes(nodes_gdf, edges_gdf, zone_gdf, plant_building_names, network_type, locator, expected_num_components=None):
    """
    Auto-create missing PLANT nodes in user-defined networks.

    Supports multiple plant buildings per network:
    - For auto-generated layouts (1 component): Creates plant at each specified building
    - For user-defined layouts:
      - 1 component: Creates plant at each specified building
      - Multiple components: Raises error (cannot determine plant placement)

    :param nodes_gdf: GeoDataFrame of network nodes
    :param edges_gdf: GeoDataFrame of network edges
    :param zone_gdf: GeoDataFrame of building geometries
    :param plant_building_names: List of user-specified plant buildings (or empty list)
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

    # If plants already exist, validate that user didn't also specify plant buildings
    if len(existing_plants) > 0:
        if plant_building_names:
            raise ValueError(
                f"User-defined network already contains {len(existing_plants)} PLANT node(s), but plant buildings are also specified.\n"
                f"CEA cannot determine which plants to use.\n\n"
                f"Resolution:\n"
                f"  1. Remove plant building specifications from config (cooling-plant-building/heating-plant-building), OR\n"
                f"  2. Remove PLANT nodes from your network layout shapefile"
            )
        print("[auto_create_plant_nodes] Plants already exist, skipping auto-creation")
        return nodes_gdf, edges_gdf, []

    # Validate component count for multiple plants
    if len(components) > 1 and plant_building_names:
        raise ValueError(
            f"User-defined network has {len(components)} disconnected components and plant buildings are specified.\n"
            f"CEA cannot determine which plant should be placed in which component.\n\n"
            f"Resolution:\n"
            f"  1. Remove plant building specifications and CEA will automatically place one plant per component (anchor load), OR\n"
            f"  2. Add PLANT nodes directly to your network layout shapefile, OR\n"
            f"  3. Connect all components into a single network"
        )

    # Get building nodes for analysis
    building_nodes = nodes_gdf[nodes_gdf['building'].notna() &
                                (nodes_gdf['building'].fillna('').str.upper() != 'NONE') &
                                (nodes_gdf['type'].fillna('').str.upper() != 'PLANT')].copy()

    # Load demand data to find anchor building
    total_demand = pd.read_csv(locator.get_total_demand())
    demand_field = "QH_sys_MWhyr" if network_type == "DH" else "QC_sys_MWhyr"

    created_plants = []

    # If plant buildings are specified, create plants for each one
    if plant_building_names:
        for plant_building in plant_building_names:
            # Find the building node
            plant_node = building_nodes[building_nodes['building'] == plant_building]
            if plant_node.empty:
                print(f"  ⚠ Warning: Plant building '{plant_building}' not found in network nodes, skipping")
                continue

            # Update the building node's type to PLANT
            plant_node_idx = plant_node.index[0]
            plant_node_name = nodes_gdf.loc[plant_node_idx, 'name']
            nodes_gdf.loc[plant_node_idx, 'type'] = 'PLANT'

            created_plants.append({
                'network_id': 'N1001',  # Single component for auto-generated layouts
                'building': plant_building,
                'node_name': plant_node_name,
                'junction_node': None,
                'distance_to_junction': 0.0,
                'reason': 'user-specified'
            })

    else:
        # No plant buildings specified - use anchor load (highest demand) for each component
        for component_id, component_nodes in enumerate(components):
            # Get buildings in this component
            buildings_in_component = []
            for node_idx in component_nodes:
                if node_idx in building_nodes.index:
                    building_name = building_nodes.loc[node_idx, 'building']
                    buildings_in_component.append(building_name)

            if not buildings_in_component:
                continue  # Skip components with no buildings

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

            # Update the anchor building node's type to PLANT
            anchor_node_idx = anchor_node.index[0]
            anchor_node_name = nodes_gdf.loc[anchor_node_idx, 'name']
            nodes_gdf.loc[anchor_node_idx, 'type'] = 'PLANT'

            # Generate network identifier for reporting
            network_id = f"N{1001 + component_id}"

            created_plants.append({
                'network_id': network_id,
                'building': anchor_building,
                'node_name': anchor_node_name,
                'junction_node': None,
                'distance_to_junction': 0.0,
                'reason': 'anchor-load'
            })

    return nodes_gdf, edges_gdf, created_plants


def resolve_plant_buildings(plant_building_input, available_buildings, network_type_label=""):
    """
    Resolve plant building names with flexible matching.

    - Parses comma-separated input and matches all values
    - Case-insensitive matching against available buildings
    - Returns list of matched building names
    - Logs the resolution process

    :param plant_building_input: User input (can be comma-separated, any case)
    :param available_buildings: List of actual building names in the scenario
    :param network_type_label: Label for logging (e.g., "cooling", "heating")
    :return: List of matched building names (empty list if none match)
    """
    label = f" ({network_type_label})" if network_type_label else ""

    if not plant_building_input or not plant_building_input.strip():
        print(f"  ℹ Plant building{label}: Not specified - will use anchor load (building with highest demand)")
        return []

    # Parse comma-separated input
    input_parts = [s.strip() for s in plant_building_input.split(',') if s.strip()]

    if not input_parts:
        return []

    # Case-insensitive matching
    building_map = {b.lower(): b for b in available_buildings}
    matched_buildings = []
    unmatched_buildings = []

    for input_building in input_parts:
        input_lower = input_building.lower()
        if input_lower in building_map:
            matched_building = building_map[input_lower]
            matched_buildings.append(matched_building)
            if matched_building != input_building:
                print(f"  ℹ Plant building{label}: Matched '{input_building}' to '{matched_building}' (case-insensitive)")
        else:
            unmatched_buildings.append(input_building)

    # Log results
    if matched_buildings:
        if len(matched_buildings) == 1:
            print(f"  ℹ Plant building{label}: Using '{matched_buildings[0]}' as anchor for plant placement")
        else:
            print(f"  ℹ Plant buildings{label}: Using {len(matched_buildings)} buildings for plant placement:")
            for building in matched_buildings[:5]:
                print(f"      - {building}")
            if len(matched_buildings) > 5:
                print(f"      ... and {len(matched_buildings) - 5} more")

    if unmatched_buildings:
        print(f"  ⚠ Warning: {len(unmatched_buildings)} plant building(s){label} not found in connected buildings:")
        for building in unmatched_buildings[:5]:
            print(f"      - {building}")
        if len(unmatched_buildings) > 5:
            print(f"      ... and {len(unmatched_buildings) - 5} more")
        print(f"    Available buildings: {', '.join(sorted(available_buildings)[:5])}" +
              (f" ... and {len(available_buildings) - 5} more" if len(available_buildings) > 5 else ""))

    return matched_buildings


def auto_layout_network(config, network_layout, locator: cea.inputlocator.InputLocator, cooling_plant_building=None, heating_plant_building=None):
    if cooling_plant_building is None:
        cooling_plant_building = ""
    if heating_plant_building is None:
        heating_plant_building = ""
    total_demand_location = locator.get_total_demand()

    # Read config parameters
    overwrite_supply = config.network_layout.overwrite_supply_settings
    connected_buildings_config = config.network_layout.connected_buildings
    list_include_services = config.network_layout.include_services
    consider_only_buildings_with_demand = config.network_layout.consider_only_buildings_with_demand
    allow_looped_networks = False
    steiner_algorithm = network_layout.algorithm

    # Validate include_services is not empty
    if not list_include_services:
        raise ValueError("No thermal services selected. Please specify at least one service in 'include-services' (DC and/or DH).")

    # Get all zone buildings for validation
    all_zone_buildings = locator.get_zone_building_names()

    # Determine which buildings should be in the network
    if overwrite_supply:
        # Use connected-buildings parameter (what-if scenarios)
        # Check if connected-buildings was explicitly set or auto-populated with all zone buildings
        is_explicitly_set = (connected_buildings_config and
                           set(connected_buildings_config) != set(all_zone_buildings))

        if is_explicitly_set:
            # User explicitly specified a subset of buildings
            list_district_scale_buildings = connected_buildings_config
            print("  - Mode: Overwrite district thermal connections defined in Building Properties/Supply")
            print(f"  - User-defined connected buildings: {len(list_district_scale_buildings)}")
        else:
            # Blank connected-buildings (auto-populated): use all zone buildings
            list_district_scale_buildings = all_zone_buildings
            print("  - Mode: Overwrite district thermal connections defined in Building Properties/Supply")
            print(f"  - Using all buildings from zone geometry: {len(list_district_scale_buildings)}")

        # Check demand separately for DC and DH
        buildings_without_demand_dc = []
        buildings_without_demand_dh = []
        if 'DC' in list_include_services:
            buildings_with_demand_dc = get_buildings_with_demand(locator, network_type='DC')
            buildings_without_demand_dc = [b for b in list_district_scale_buildings if b not in buildings_with_demand_dc]
        if 'DH' in list_include_services:
            buildings_with_demand_dh = get_buildings_with_demand(locator, network_type='DH')
            buildings_without_demand_dh = [b for b in list_district_scale_buildings if b not in buildings_with_demand_dh]

    else:
        # Use supply.csv to determine district buildings
        buildings_to_validate_dc = []
        buildings_to_validate_dh = []
        buildings_without_demand_dc = []
        buildings_without_demand_dh = []

        # Warn if connected-buildings parameter has values that will be ignored
        if connected_buildings_config:
            print("  ⚠ Warning: 'connected-buildings' parameter is set but will be ignored")
            print(f"    Reason: 'overwrite-supply-settings' is False")
            print(f"    To use 'connected-buildings', set 'overwrite-supply-settings' to True")

        if 'DC' in list_include_services:
            buildings_to_validate_dc = get_buildings_from_supply_csv(locator, network_type='DC')
            buildings_with_demand_dc = get_buildings_with_demand(locator, network_type='DC')
            buildings_without_demand_dc = [b for b in buildings_to_validate_dc if b not in buildings_with_demand_dc]
        if 'DH' in list_include_services:
            buildings_to_validate_dh = get_buildings_from_supply_csv(locator, network_type='DH')
            buildings_with_demand_dh = get_buildings_with_demand(locator, network_type='DH')
            buildings_without_demand_dh = [b for b in buildings_to_validate_dh if b not in buildings_with_demand_dh]

        # Combine DC and DH buildings (union - unique values only)
        list_district_scale_buildings = list(set(buildings_to_validate_dc) | set(buildings_to_validate_dh))

        # Validate at least one building found
        if not list_district_scale_buildings:
            raise ValueError(f"No district thermal network connections found in Building Properties/Supply for service(s): {', '.join(list_include_services)}.")

        print("  - Mode: Use Building Properties/Supply settings")
        if buildings_to_validate_dc and buildings_to_validate_dh:
            print(f"  - District buildings (DC): {len(buildings_to_validate_dc)}")
            print(f"  - District buildings (DH): {len(buildings_to_validate_dh)}")
        elif buildings_to_validate_dc:
            print(f"  - District buildings (DC): {len(list_district_scale_buildings)}")
            if 'DH' in list_include_services:
                print("  - District buildings (DH): 0")
                list_include_services.remove('DH')
        elif buildings_to_validate_dh:
            print(f"  - District buildings (DH): {len(list_district_scale_buildings)}")
            if 'DC' in list_include_services:
                print("  - District buildings (DC): 0")
                list_include_services.remove('DC')

    # Apply consider_only_buildings_with_demand filter if enabled
    if consider_only_buildings_with_demand:
        # Filter separately for DC and DH services
        buildings_before_filter = len(list_district_scale_buildings)
        buildings_with_any_demand = set()

        if 'DC' in list_include_services:
            buildings_with_demand_dc = get_buildings_with_demand(locator, network_type='DC')
            buildings_filtered_dc = [b for b in list_district_scale_buildings if b not in buildings_with_demand_dc]
            if buildings_filtered_dc:
                print(f"  - consider-only-buildings-with-demand (DC): Filtered out {len(buildings_filtered_dc)} building(s) without cooling demand")
            buildings_with_any_demand.update(buildings_with_demand_dc)

        if 'DH' in list_include_services:
            buildings_with_demand_dh = get_buildings_with_demand(locator, network_type='DH')
            buildings_filtered_dh = [b for b in list_district_scale_buildings if b not in buildings_with_demand_dh]
            if buildings_filtered_dh:
                print(f"  - consider-only-buildings-with-demand (DH): Filtered out {len(buildings_filtered_dh)} building(s) without heating demand")
            buildings_with_any_demand.update(buildings_with_demand_dh)

        # Keep buildings with demand for at least one service
        list_district_scale_buildings = [b for b in list_district_scale_buildings if b in buildings_with_any_demand]
        buildings_after_filter = len(list_district_scale_buildings)

        if buildings_before_filter != buildings_after_filter:
            print(f"  - Total buildings after filtering: {buildings_after_filter} (was {buildings_before_filter})")
    else:
        # Print demand warnings when not filtering
        print_demand_warning(buildings_without_demand_dc, "cooling")
        print_demand_warning(buildings_without_demand_dh, "heating")

    # Determine network type string (unified logic for both branches)
    if 'DC' in list_include_services and 'DH' in list_include_services:
        network_type = 'DC+DH'
    elif 'DC' in list_include_services:
        network_type = 'DC'
    elif 'DH' in list_include_services:
        network_type = 'DH'
    else:
        # This should never happen due to validation above, but keep as safeguard
        raise ValueError(f"No thermal services selected: {', '.join(list_include_services)}.")

    path_streets_shp = locator.get_street_network()  # shapefile with the stations
    path_zone_shp = locator.get_zone_geometry()

    zone_df = gpd.GeoDataFrame.from_file(path_zone_shp)

    # Determine which network types to generate layouts for
    network_types_to_generate = []
    if network_type == 'DC+DH':
        network_types_to_generate = ['DC', 'DH']
    else:
        network_types_to_generate = [network_type]

    # Generate network layout for each type (DC and/or DH)
    for type_network in network_types_to_generate:
        print(f"\n  Generating {type_network} network layout...")

        # Resolve plant buildings for this network type
        if type_network == 'DC':
            plant_buildings_list = resolve_plant_buildings(cooling_plant_building, list_district_scale_buildings, "cooling")
        else:  # DH
            plant_buildings_list = resolve_plant_buildings(heating_plant_building, list_district_scale_buildings, "heating")

        # Calculate points where the substations will be located (building centroids)
        building_centroids_df = calc_building_centroids(
            zone_df,
            list_district_scale_buildings,
            plant_buildings_list,
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
        # Shared layout path (edges) - same for both DC and DH
        output_layout_path = locator.get_network_layout_shapefile(network_name=network_layout.network_name)
        # Separate node path for this network type (DC or DH)
        output_nodes_path = locator.get_network_layout_nodes_shapefile(type_network, network_layout.network_name)

        os.makedirs(os.path.dirname(output_layout_path), exist_ok=True)
        os.makedirs(os.path.dirname(output_nodes_path), exist_ok=True)

        disconnected_building_names = []

        calc_steiner_spanning_tree(crs_projected,
                                   building_centroids_df,
                                   potential_network_df,
                                   output_layout_path,
                                   output_nodes_path,
                                   type_network,
                                   total_demand_location,
                                   allow_looped_networks,
                                   plant_buildings_list,
                                   disconnected_building_names,
                                   steiner_algorithm)

        print(f"  ✓ {type_network} network layout saved")

    # Summary
    print(f"\n  ✓ Network layout generation complete for: {', '.join(network_types_to_generate)}")
    print(f"    Network name: {network_layout.network_name}")
    if network_type == 'DC+DH':
        print(f"    Output folders: DC/ and DH/")



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


def process_user_defined_network(config, locator, network_layout, edges_shp, nodes_shp, geojson_path, cooling_plant_building, heating_plant_building):
    """
    Process user-defined network layout from shapefiles or GeoJSON.

    :param config: Configuration instance
    :param locator: InputLocator instance
    :param network_layout: NetworkLayout instance
    :param edges_shp: Path to edges shapefile (optional)
    :param nodes_shp: Path to nodes shapefile (optional)
    :param geojson_path: Path to GeoJSON file (optional)
    :param cooling_plant_building: Cooling plant building names from config
    :param heating_plant_building: Heating plant building names from config
    :return: None (raises exception if processing fails)
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
    list_include_services = config.network_layout.include_services

    # Validate include_services is not empty
    if not list_include_services:
        raise ValueError("No thermal services selected. Please specify at least one service in 'include-services' (DC and/or DH).")

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
            print("  - Mode: Overwrite district thermal connections defined in Building Properties/Supply")
            print(f"  - User-defined connected buildings: {len(buildings_to_validate)}")
            print(f"  - Buildings in user layout: {len(network_building_names)}")
        else:
            # Blank connected-buildings (auto-populated): accept whatever is in user layout
            # BUT we already validated building names exist in zone geometry above
            print("  - Mode: Overwrite district thermal connections defined in Building Properties/Supply")
            print(f"  - Using buildings from user-provided layout: {len(network_building_names)}")
            for building_name in network_building_names[:10]:
                print(f"      - {building_name}")
            if len(network_building_names) > 10:
                print(f"      ... and {len(network_building_names) - 10} more")
            buildings_to_validate = network_building_names  # Validate these buildings exist and have nodes

        # Check demand separately for DC and DH
        buildings_without_demand_dc = []
        buildings_without_demand_dh = []
        if 'DC' in list_include_services:
            buildings_with_demand_dc = get_buildings_with_demand(locator, network_type='DC')
            buildings_without_demand_dc = [b for b in buildings_to_validate if b not in buildings_with_demand_dc]
        if 'DH' in list_include_services:
            buildings_with_demand_dh = get_buildings_with_demand(locator, network_type='DH')
            buildings_without_demand_dh = [b for b in buildings_to_validate if b not in buildings_with_demand_dh]

    else:
        # Use supply.csv to determine district buildings
        buildings_to_validate_dc = []
        buildings_to_validate_dh = []
        buildings_without_demand_dc = []
        buildings_without_demand_dh = []

        # Warn if connected-buildings parameter has values that will be ignored
        if connected_buildings_config:
            print("  ⚠ Warning: 'connected-buildings' parameter is set but will be ignored")
            print(f"    Reason: 'overwrite-supply-settings' is False")
            print(f"    To use 'connected-buildings', set 'overwrite-supply-settings' to True")

        if 'DC' in list_include_services:
            buildings_to_validate_dc = get_buildings_from_supply_csv(locator, network_type='DC')
            buildings_with_demand_dc = get_buildings_with_demand(locator, network_type='DC')
            buildings_without_demand_dc = [b for b in buildings_to_validate_dc if b not in buildings_with_demand_dc]
        if 'DH' in list_include_services:
            buildings_to_validate_dh = get_buildings_from_supply_csv(locator, network_type='DH')
            buildings_with_demand_dh = get_buildings_with_demand(locator, network_type='DH')
            buildings_without_demand_dh = [b for b in buildings_to_validate_dh if b not in buildings_with_demand_dh]

        # Combine DC and DH buildings (union - unique values only)
        buildings_to_validate = list(set(buildings_to_validate_dc) | set(buildings_to_validate_dh))

        # Validate at least one building found
        if not buildings_to_validate:
            raise ValueError(f"No district thermal network connections found in Building Properties/Supply for service(s): {', '.join(list_include_services)}.")

        print("  - Mode: Use Building Properties/Supply settings")
        if buildings_to_validate_dc and buildings_to_validate_dh:
            print(f"  - District buildings (DC): {len(buildings_to_validate_dc)}")
            print(f"  - District buildings (DH): {len(buildings_to_validate_dh)}")
        elif buildings_to_validate_dc:
            print(f"  - District buildings (DC): {len(buildings_to_validate)}")
            if 'DH' in list_include_services:
                print("  - District buildings (DH): 0")
                list_include_services.remove('DH')
        elif buildings_to_validate_dh:
            print(f"  - District buildings (DH): {len(buildings_to_validate)}")
            if 'DC' in list_include_services:
                print("  - District buildings (DC): 0")
                list_include_services.remove('DC')
        print(f"  - Buildings in user layout: {len(network_building_names)}")

    # Determine network type string (unified logic for both branches)
    if 'DC' in list_include_services and 'DH' in list_include_services:
        network_type = 'DC+DH'
    elif 'DC' in list_include_services:
        network_type = 'DC'
    elif 'DH' in list_include_services:
        network_type = 'DH'
    else:
        # This should never happen due to validation at line 501, but keep as safeguard
        raise ValueError(f"No thermal services selected: {', '.join(list_include_services)}.")

    # Helper function to print demand warnings
    print_demand_warning(buildings_without_demand_dc, "cooling")
    print_demand_warning(buildings_without_demand_dh, "heating")

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

    # Get expected number of components from config
    expected_num_components = config.network_layout.number_of_components if config.network_layout.number_of_components else None
    print(f"[process_user_defined_network] number_of_components from config: {config.network_layout.number_of_components} -> expected_num_components: {expected_num_components}")

    # Save to network-name location
    output_layout_path = locator.get_network_layout_shapefile(network_name=network_layout.network_name)
    output_node_path_dc = locator.get_network_layout_nodes_shapefile('DC', network_layout.network_name)
    output_node_path_dh = locator.get_network_layout_nodes_shapefile('DH', network_layout.network_name)

    # Save layout-edges shapefile (shared)
    os.makedirs(os.path.dirname(output_layout_path), exist_ok=True)
    edges_gdf.to_file(output_layout_path, driver='ESRI Shapefile')

    # Process nodes separately for DC and DH
    if network_type == 'DC' or network_type == 'DC+DH':
        # Resolve cooling plant buildings
        cooling_plant_buildings_list = resolve_plant_buildings(cooling_plant_building, buildings_to_validate, "cooling")

        # Create copy of nodes for DC network
        nodes_gdf_dc = nodes_gdf.copy()
        nodes_gdf_dc, edges_gdf_dc, created_plants_dc = auto_create_plant_nodes(
            nodes_gdf_dc, edges_gdf, zone_gdf,
            cooling_plant_buildings_list, 'DC', locator,
            expected_num_components
        )

        if created_plants_dc:
            print(f"\n Auto-assigned {len(created_plants_dc)} building node(s) as PLANT (DC):")
            for plant_info in created_plants_dc:
                reason_text = "user-specified anchor" if plant_info['reason'] == 'user-specified' else "anchor load (highest demand)"
                print(f"      - {plant_info['node_name']}: building '{plant_info['building']}' ({reason_text})")
            print("  Note: Existing building nodes converted to PLANT type")

        os.makedirs(os.path.dirname(output_node_path_dc), exist_ok=True)
        nodes_gdf_dc.to_file(output_node_path_dc, driver='ESRI Shapefile')

    if network_type == 'DH' or network_type == 'DC+DH':
        # Resolve heating plant buildings
        heating_plant_buildings_list = resolve_plant_buildings(heating_plant_building, buildings_to_validate, "heating")

        # Create copy of nodes for DH network
        nodes_gdf_dh = nodes_gdf.copy()
        nodes_gdf_dh, edges_gdf_dh, created_plants_dh = auto_create_plant_nodes(
            nodes_gdf_dh, edges_gdf, zone_gdf,
            heating_plant_buildings_list, 'DH', locator,
            expected_num_components
        )

        if created_plants_dh:
            print(f"\n Auto-assigned {len(created_plants_dh)} building node(s) as PLANT (DH):")
            for plant_info in created_plants_dh:
                reason_text = "user-specified anchor" if plant_info['reason'] == 'user-specified' else "anchor load (highest demand)"
                print(f"      - {plant_info['node_name']}: building '{plant_info['building']}' ({reason_text})")
            print("  Note: Existing building nodes converted to PLANT type")

        os.makedirs(os.path.dirname(output_node_path_dh), exist_ok=True)
        nodes_gdf_dh.to_file(output_node_path_dh, driver='ESRI Shapefile')

    print("\n  ✓ User-defined layout saved to:")
    print(f"    {os.path.dirname(output_layout_path)}")
    print("\n" + "=" * 80 + "\n")


def main(config: cea.config.Configuration):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    network_layout = NetworkLayout.from_config(config.network_layout, locator)
    cooling_plant_building = config.network_layout.cooling_plant_building
    heating_plant_building = config.network_layout.heating_plant_building

    print(f"Network name: {network_layout.network_name}")

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
            cooling_plant_building, heating_plant_building
        )

    # Generate network layout using Steiner tree (current behavior or fallback)
    else:
        print("\n" + "=" * 80)
        print("AUTOMATIC NETWORK LAYOUT GENERATION")
        print("=" * 80 + "\n")
        auto_layout_network(config, network_layout, locator, cooling_plant_building=cooling_plant_building, heating_plant_building=heating_plant_building)


if __name__ == '__main__':
    main(cea.config.Configuration())

import os
import shutil
from dataclasses import dataclass, field

import geopandas as gpd
import pandas as pd

import cea.config
import cea.inputlocator
from cea.technologies.network_layout.connectivity_potential import calc_connectivity_network_with_geometry
from cea.technologies.network_layout.steiner_spanning_tree import calc_steiner_spanning_tree, add_plant_close_to_anchor, get_next_node_name
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


def convert_simplified_nodes_to_full_format(nodes_gdf):
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

    :param nodes_gdf: GeoDataFrame in simplified format
    :return: GeoDataFrame in full format
    """
    # Check if already in full format (has 'building' and 'name' columns)
    if 'building' in nodes_gdf.columns and 'name' in nodes_gdf.columns:
        print("  ℹ Nodes already in full format, no conversion needed")
        return nodes_gdf

    # Check if in simplified format (only has 'type' and 'geometry')
    if 'type' not in nodes_gdf.columns:
        raise ValueError("Invalid nodes format: missing 'type' column")

    print("  ℹ Converting simplified nodes format to full format...")

    # Create full format dataframe
    nodes_full = nodes_gdf.copy()

    # Initialize new columns
    nodes_full['building'] = 'NONE'
    nodes_full['name'] = [f'NODE{i}' for i in range(len(nodes_full))]
    nodes_full['type_original'] = nodes_full['type']  # Keep original for processing

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

    # Check for existing plants based on network type
    # PLANT = shared (both DC and DH)
    # PLANT_DC = DC only
    # PLANT_DH = DH only
    plants_shared = nodes_gdf[nodes_gdf['type'].fillna('').str.upper() == 'PLANT']
    plants_dc = nodes_gdf[nodes_gdf['type'].fillna('').str.upper() == 'PLANT_DC']
    plants_dh = nodes_gdf[nodes_gdf['type'].fillna('').str.upper() == 'PLANT_DH']

    # Determine which plants apply to this network type
    if network_type == 'DC':
        existing_plants = pd.concat([plants_shared, plants_dc]).drop_duplicates()
    elif network_type == 'DH':
        existing_plants = pd.concat([plants_shared, plants_dh]).drop_duplicates()
    else:
        existing_plants = plants_shared

    if len(existing_plants) > 0:
        print(f"  Found {len(existing_plants)} existing PLANT nodes for {network_type} network")
        if len(plants_shared) > 0:
            print(f"    - Shared plants (PLANT): {len(plants_shared)}")
        if network_type == 'DC' and len(plants_dc) > 0:
            print(f"    - DC-only plants (PLANT_DC): {len(plants_dc)}")
        if network_type == 'DH' and len(plants_dh) > 0:
            print(f"    - DH-only plants (PLANT_DH): {len(plants_dh)}")

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
            # Generate unique node name
            node_name = get_next_node_name(nodes_gdf)

            new_node = gpd.GeoDataFrame([{
                'name': node_name,
                'building': 'NONE',
                'type': 'NONE',
                'geometry': exact_point  # Use exact coordinates from edge endpoint
            }], crs=nodes_gdf.crs)
            nodes_gdf = pd.concat([nodes_gdf, new_node], ignore_index=True)
            print(f"      - Created {node_name} at ({exact_point.x:.2f}, {exact_point.y:.2f}) for edges: {', '.join(edge_names[:3])}")

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
    print(f"  Detected {len(components)} connected component(s)")

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
        print("  Plants already exist, skipping auto-creation")
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
            # Try to find the building node (it might be in the network or in the zone but not connected)
            plant_node = building_nodes[building_nodes['building'] == plant_building]
            temp_node_added = False

            if plant_node.empty:
                # Plant building not in network - try to find it in zone geometry
                building_in_zone = zone_gdf[zone_gdf['name'] == plant_building]
                if not building_in_zone.empty:
                    # Add the building temporarily so we can create a plant near it
                    building_geom = building_in_zone.iloc[0].geometry

                    # Generate unique node name
                    node_name = get_next_node_name(nodes_gdf)

                    new_node = gpd.GeoDataFrame([{
                        'name': node_name,
                        'building': plant_building,
                        'type': 'CONSUMER',
                        'geometry': building_geom.centroid
                    }], crs=nodes_gdf.crs)
                    nodes_gdf = pd.concat([nodes_gdf, new_node], ignore_index=True)
                    plant_node = nodes_gdf[nodes_gdf['building'] == plant_building]
                    temp_node_added = True
                else:
                    print(f"  ⚠ Warning: Plant building '{plant_building}' not found in zone geometry, skipping")
                    continue

            # Create a new PLANT node near this building
            building_anchor = plant_node
            nodes_gdf, edges_gdf = add_plant_close_to_anchor(
                building_anchor,
                nodes_gdf,
                edges_gdf,
                'T1',  # Default pipe material
                150    # Default pipe diameter
            )

            # The newly created plant node is the last one
            plant_node_idx = nodes_gdf.index[-1]
            plant_node_name = nodes_gdf.loc[plant_node_idx, 'name']

            # Remove the temporary building node if we added one
            if temp_node_added:
                nodes_gdf = nodes_gdf[nodes_gdf['building'] != plant_building]

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
        print(f"  ℹ Plant building{label}: Not specified - will use anchor load (building with highest demand) or user-defined PLANT nodes")
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

    # Throw error if any plant buildings don't exist in zone
    if unmatched_buildings:
        raise ValueError(
            f"Plant building(s){label} not found in zone geometry:\n" +
            "\n".join([f"  - {b}" for b in unmatched_buildings]) +
            f"\n\nAvailable buildings: {', '.join(sorted(available_buildings)[:10])}" +
            (" ..." if len(available_buildings) > 10 else "")
        )

    # Cap to maximum 3 plant buildings
    MAX_PLANTS = 3
    if len(matched_buildings) > MAX_PLANTS:
        print(f"  ℹ Plant buildings{label}: {len(matched_buildings)} buildings specified, limiting to first {MAX_PLANTS}")
        matched_buildings = matched_buildings[:MAX_PLANTS]

    # Log results
    if matched_buildings:
        if len(matched_buildings) == 1:
            print(f"  ℹ Plant building{label}: Using '{matched_buildings[0]}' as anchor for plant placement")
        else:
            print(f"  ℹ Plant buildings{label}: Using {len(matched_buildings)} buildings for plant placement:")
            for building in matched_buildings:
                print(f"      - {building}")

    if unmatched_buildings:
        print(f"  ⚠ Warning: {len(unmatched_buildings)} plant building(s){label} not found in zone:")
        for building in unmatched_buildings[:5]:
            print(f"      - {building}")
        if len(unmatched_buildings) > 5:
            print(f"      ... and {len(unmatched_buildings) - 5} more")
        print(f"    Available buildings in zone: {', '.join(sorted(available_buildings)[:5])}" +
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
    connection_candidates = config.network_layout.connection_candidates
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
        district_buildings_set = set(list_district_scale_buildings)
        buildings_without_demand_dc = []
        buildings_without_demand_dh = []

        for service in list_include_services:
            buildings_with_demand = set(get_buildings_with_demand(locator, network_type=service))
            buildings_without_demand = district_buildings_set - buildings_with_demand

            if service == 'DC':
                buildings_without_demand_dc = list(buildings_without_demand)
            elif service == 'DH':
                buildings_without_demand_dh = list(buildings_without_demand)
    else:
        # Use supply.csv to determine district buildings
        buildings_to_validate_dc = []
        buildings_to_validate_dh = []
        buildings_without_demand_dc = []
        buildings_without_demand_dh = []

        # Warn if connected-buildings parameter has values that will be ignored
        if connected_buildings_config:
            print("  ⚠ Warning: 'connected-buildings' parameter is set but will be ignored")
            print("    Reason: 'overwrite-supply-settings' is False")
            print("    To use 'connected-buildings', set 'overwrite-supply-settings' to True")

        for service in list_include_services:
            buildings_to_validate = get_buildings_from_supply_csv(locator, network_type=service)
            buildings_with_demand = set(get_buildings_with_demand(locator, network_type=service))
            buildings_without_demand = set(buildings_to_validate) - buildings_with_demand

            if service == 'DC':
                buildings_to_validate_dc = buildings_to_validate
                buildings_without_demand_dc = list(buildings_without_demand)
            elif service == 'DH':
                buildings_to_validate_dh = buildings_to_validate
                buildings_without_demand_dh = list(buildings_without_demand)

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

    # Track which buildings belong to DC and DH networks separately
    buildings_for_dc = []
    buildings_for_dh = []

    # Apply consider_only_buildings_with_demand filter if enabled
    if consider_only_buildings_with_demand:
        buildings_before_filter = len(list_district_scale_buildings)
        district_buildings_set = set(list_district_scale_buildings)
        buildings_with_any_demand = set()

        # Process each service type
        for service in list_include_services:
            buildings_with_demand = set(get_buildings_with_demand(locator, network_type=service))

            # Assign buildings to service-specific list
            if service == 'DC':
                buildings_for_dc = list(district_buildings_set & buildings_with_demand)
            elif service == 'DH':
                buildings_for_dh = list(district_buildings_set & buildings_with_demand)

            # Track filtered buildings and print message
            buildings_filtered = district_buildings_set - buildings_with_demand
            if buildings_filtered:
                demand_type = 'cooling' if service == 'DC' else 'heating'
                print(f"  - consider-only-buildings-with-demand ({service}): Filtered out {len(buildings_filtered)} building(s) without {demand_type} demand")

            # Accumulate buildings with demand for any service
            buildings_with_any_demand.update(buildings_with_demand)

        # Keep only buildings with demand for at least one service
        list_district_scale_buildings = list(district_buildings_set & buildings_with_any_demand)
        buildings_after_filter = len(list_district_scale_buildings)

        if buildings_before_filter != buildings_after_filter:
            print(f"  - Total buildings after filtering: {buildings_after_filter} (was {buildings_before_filter})")
    else:
        # When not filtering by demand, all buildings go to both networks
        if 'DC' in list_include_services:
            buildings_for_dc = list_district_scale_buildings.copy()
        if 'DH' in list_include_services:
            buildings_for_dh = list_district_scale_buildings.copy()
        # Print demand warnings when not filtering
        print_demand_warning(buildings_without_demand_dc, "cooling")
        print_demand_warning(buildings_without_demand_dh, "heating")

    # Determine which network types to generate (use set for cleaner conditionals)
    network_types_to_generate = set()
    if 'DC' in list_include_services:
        network_types_to_generate.add('DC')
    if 'DH' in list_include_services:
        network_types_to_generate.add('DH')

    if not network_types_to_generate:
        # This should never happen due to validation above, but keep as safeguard
        raise ValueError(f"No thermal services selected: {', '.join(list_include_services)}.")

    path_streets_shp = locator.get_street_network()  # shapefile with the stations
    path_zone_shp = locator.get_zone_geometry()

    zone_df = gpd.GeoDataFrame.from_file(path_zone_shp)

    # Get all zone building names for plant building validation
    all_zone_buildings = zone_df['name'].tolist()

    # Resolve plant buildings for both network types
    # Plant buildings can be ANY building in the zone, not just connected buildings
    cooling_plant_buildings_list = resolve_plant_buildings(cooling_plant_building, all_zone_buildings, "cooling")
    heating_plant_buildings_list = resolve_plant_buildings(heating_plant_building, all_zone_buildings, "heating")

    # Prepare for network generation
    street_network_df = gpd.GeoDataFrame.from_file(path_streets_shp)

    # Paths for output files
    output_layout_path = locator.get_network_layout_shapefile(network_name=network_layout.network_name)
    os.makedirs(os.path.dirname(output_layout_path), exist_ok=True)

    # Collect all edges from both networks
    all_edges_list = []

    # Generate Steiner tree for each network type separately
    for type_network in network_types_to_generate:
        print(f"\n{'='*60}")
        print(f"  {type_network} NETWORK")
        print(f"{'='*60}")

        # Get plant buildings and connected buildings for this network type
        if type_network == 'DC':
            plant_buildings_for_type = cooling_plant_buildings_list
            connected_buildings_for_type = buildings_for_dc
        else:  # DH
            plant_buildings_for_type = heating_plant_buildings_list
            connected_buildings_for_type = buildings_for_dh

        # Calculate building centroids for this network type
        building_centroids_df = calc_building_centroids(
            zone_df,
            connected_buildings_for_type,
            plant_buildings_for_type,
            False,  # Already filtered by demand above
            type_network,
            total_demand_location,
        )

        # Calculate potential network graph
        # Use connection_candidates for k-nearest optimization (default 1 for greedy nearest)
        potential_network_graph = calc_connectivity_network_with_geometry(
            street_network_df,
            building_centroids_df,
            connection_candidates=connection_candidates,
        )

        # Convert graph to GeoDataFrame for Steiner tree algorithm
        crs_projected = potential_network_graph.graph['crs']
        potential_network_df = nx_to_gdf(potential_network_graph, crs=crs_projected, preserve_geometry=True)
        potential_network_df['length'] = potential_network_df.geometry.length

        if crs_projected is None:
            raise ValueError("The CRS of the potential network shapefile is undefined.")

        # Ensure building centroids is in projected crs
        building_centroids_df = building_centroids_df.to_crs(crs_projected)

        # Generate Steiner tree for this network WITHOUT plant nodes
        # Pass plant buildings list to prevent automatic anchor-based plant creation
        temp_nodes_path = output_layout_path.replace('layout.shp', f'_temp_nodes_{type_network}.shp')
        temp_edges_path = output_layout_path.replace('layout.shp', f'_temp_edges_{type_network}.shp')

        disconnected_building_names = []
        calc_steiner_spanning_tree(crs_projected,
                                   building_centroids_df,
                                   potential_network_df,
                                   temp_edges_path,
                                   temp_nodes_path,
                                   type_network,
                                   total_demand_location,
                                   allow_looped_networks,
                                   None,  # None = skip plant creation (caller will add plants manually)
                                   disconnected_building_names,
                                   method=steiner_algorithm,
                                   connection_candidates=connection_candidates)

        # Read generated nodes and edges
        nodes_for_type = gpd.read_file(temp_nodes_path)
        edges_for_type = gpd.read_file(temp_edges_path)

        print(f"    Base network: {len(nodes_for_type)} nodes, {len(edges_for_type)} edges")

        # Add plant nodes for this network type (marked as PLANT_DC or PLANT_DH temporarily)
        if plant_buildings_for_type:
            # User specified plant buildings - create plant at each one
            plant_buildings_to_remove = []
            for plant_building in plant_buildings_for_type:
                # Check if this plant building is in the connected buildings list
                is_connected_building = plant_building in connected_buildings_for_type

                # Find the building node for this plant
                building_anchor = nodes_for_type[nodes_for_type['building'] == plant_building]
                if not building_anchor.empty:
                    nodes_for_type, edges_for_type = add_plant_close_to_anchor(
                        building_anchor,
                        nodes_for_type,
                        edges_for_type,
                        'T1',  # Default pipe material
                        150    # Default pipe diameter
                    )
                    # Mark the newly created plant node with network-specific type
                    # The last node added is the plant node
                    last_node_idx = nodes_for_type.index[-1]
                    nodes_for_type.loc[last_node_idx, 'type'] = f'PLANT_{type_network}'
                    print(f"    ✓ Added PLANT_{type_network} node for building '{plant_building}'")

                    # Only remove the original building node if it was NOT a connected building
                    # If it's a connected building, we need to keep it to maintain network connectivity
                    if not is_connected_building:
                        plant_buildings_to_remove.append(plant_building)
                else:
                    print(f"    ⚠ Warning: Plant building '{plant_building}' not found in network nodes, skipping")

            # Remove the original building nodes for plant buildings that are NOT connected buildings
            if plant_buildings_to_remove:
                nodes_for_type = nodes_for_type[~nodes_for_type['building'].isin(plant_buildings_to_remove)]
                print(f"    Removed {len(plant_buildings_to_remove)} original building node(s) for plant buildings (not connected buildings)")
        else:
            # No plant buildings specified - use anchor load (building with highest demand)
            total_demand = pd.read_csv(total_demand_location)
            demand_field = "QH_sys_MWhyr" if type_network == "DH" else "QC_sys_MWhyr"
            
            # Get building nodes
            building_nodes = nodes_for_type[
                nodes_for_type['building'].notna() &
                (nodes_for_type['building'].fillna('').str.upper() != 'NONE')
            ].copy()
            
            if not building_nodes.empty:
                # Find building with highest demand in this network
                buildings_in_network = building_nodes['building'].unique().tolist()
                network_demand = total_demand[total_demand['name'].isin(buildings_in_network)]
                
                if not network_demand.empty and demand_field in network_demand.columns:
                    anchor_idx = network_demand[demand_field].idxmax()
                    anchor_building = network_demand.loc[anchor_idx, 'name']
                else:
                    # Fallback: use first building alphabetically
                    anchor_building = sorted(buildings_in_network)[0]
                
                # Create a separate plant node near the anchor building
                # Building node remains as CONSUMER, plant is a separate node
                building_anchor = building_nodes[building_nodes['building'] == anchor_building]
                nodes_for_type, edges_for_type = add_plant_close_to_anchor(
                    building_anchor,
                    nodes_for_type,
                    edges_for_type,
                    'T1',  # Default pipe material
                    150    # Default pipe diameter
                )
                # Mark the newly created plant node with network-specific type
                # The last node added is the plant node
                last_node_idx = nodes_for_type.index[-1]
                nodes_for_type.loc[last_node_idx, 'type'] = f'PLANT_{type_network}'
                print(f"    ✓ Auto-assigned building '{anchor_building}' as anchor for PLANT_{type_network} (highest demand)")

        # Validation: Check for duplicate node names after plant creation
        if nodes_for_type['name'].duplicated().any():
            duplicates = nodes_for_type[nodes_for_type['name'].duplicated(keep=False)]['name'].unique().tolist()
            raise ValueError(f"Duplicate node names in {type_network} network after plant creation: {duplicates}")

        # Collect edges from this network (including new plant edges)
        all_edges_list.append(edges_for_type)

        # Normalize plant types: PLANT_DC → PLANT for DC, PLANT_DH → PLANT for DH
        nodes_for_type['type'] = nodes_for_type['type'].replace({f'PLANT_{type_network}': 'PLANT'})

        # Save network-specific nodes
        output_nodes_path = locator.get_network_layout_nodes_shapefile(type_network, network_layout.network_name)
        os.makedirs(os.path.dirname(output_nodes_path), exist_ok=True)
        nodes_for_type.to_file(output_nodes_path, driver='ESRI Shapefile')
        print(f"  ✓ {type_network}/nodes.shp saved with {len(nodes_for_type)} nodes")

        # Clean up temp files for this network
        import glob
        for f in glob.glob(temp_nodes_path.replace('.shp', '.*')):
            os.remove(f)
        for f in glob.glob(temp_edges_path.replace('.shp', '.*')):
            os.remove(f)

    # Combine all edges from both networks and save to layout.shp
    if len(all_edges_list) > 0:
        # Renumber pipes globally to prevent duplicates when combining DC and DH networks
        pipe_counter = 0
        for edges_gdf in all_edges_list:
            # Extract pipe numbers and renumber them
            for idx in edges_gdf.index:
                if 'name' in edges_gdf.columns and edges_gdf.loc[idx, 'name'].startswith('PIPE'):
                    edges_gdf.loc[idx, 'name'] = f'PIPE{pipe_counter}'
                    pipe_counter += 1
        
        all_edges_gdf = gpd.GeoDataFrame(
            pd.concat(all_edges_list, ignore_index=True),
            crs=all_edges_list[0].crs
        )
        # Remove duplicate edges (edges that appear in both DC and DH networks)
        all_edges_gdf = all_edges_gdf.drop_duplicates(subset=['geometry'], keep='first')
        all_edges_gdf.to_file(output_layout_path, driver='ESRI Shapefile')
        print(f"\n  ✓ Saved layout.shp with all edges: {len(all_edges_gdf)} edges")

    # Summary
    print(f"\n  ✓ Network layout generation complete for: {', '.join(sorted(network_types_to_generate))}")
    print(f"    Network name: {network_layout.network_name}")
    if len(network_types_to_generate) > 1:
        print("    Output folders: DC/ and DH/")



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
        buildings_to_validate_set = set(buildings_to_validate)
        buildings_without_demand_dc = []
        buildings_without_demand_dh = []

        for service in list_include_services:
            buildings_with_demand = set(get_buildings_with_demand(locator, network_type=service))
            buildings_without_demand = buildings_to_validate_set - buildings_with_demand

            if service == 'DC':
                buildings_without_demand_dc = list(buildings_without_demand)
            elif service == 'DH':
                buildings_without_demand_dh = list(buildings_without_demand)

    else:
        # Use supply.csv to determine district buildings
        buildings_to_validate_dc = []
        buildings_to_validate_dh = []
        buildings_without_demand_dc = []
        buildings_without_demand_dh = []

        # Warn if connected-buildings parameter has values that will be ignored
        if connected_buildings_config:
            print("  ⚠ Warning: 'connected-buildings' parameter is set but will be ignored")
            print("    Reason: 'overwrite-supply-settings' is False")
            print("    To use 'connected-buildings', set 'overwrite-supply-settings' to True")

        for service in list_include_services:
            buildings_to_validate_service = get_buildings_from_supply_csv(locator, network_type=service)
            buildings_with_demand = set(get_buildings_with_demand(locator, network_type=service))
            buildings_without_demand = set(buildings_to_validate_service) - buildings_with_demand

            if service == 'DC':
                buildings_to_validate_dc = buildings_to_validate_service
                buildings_without_demand_dc = list(buildings_without_demand)
            elif service == 'DH':
                buildings_to_validate_dh = buildings_to_validate_service
                buildings_without_demand_dh = list(buildings_without_demand)

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

    # Determine which network types to generate (use set for cleaner conditionals)
    network_types_to_generate = set()
    if 'DC' in list_include_services:
        network_types_to_generate.add('DC')
    if 'DH' in list_include_services:
        network_types_to_generate.add('DH')

    if not network_types_to_generate:
        # This should never happen due to validation at line 501, but keep as safeguard
        raise ValueError(f"No thermal services selected: {', '.join(list_include_services)}.")

    # Helper function to print demand warnings
    print_demand_warning(buildings_without_demand_dc, "cooling")
    print_demand_warning(buildings_without_demand_dh, "heating")

    # Validate network covers all specified buildings
    # Note: validate_network_covers_district_buildings expects a string, so convert set to string
    network_type_str = 'DC+DH' if len(network_types_to_generate) > 1 else list(network_types_to_generate)[0]
    nodes_gdf, auto_created_buildings = validate_network_covers_district_buildings(
        nodes_gdf,
        zone_gdf,  # Already loaded above for validation
        buildings_to_validate,
        network_type_str,
        edges_gdf
    )

    if auto_created_buildings:
        print(f"  Auto-created {len(auto_created_buildings)} missing building node(s):")
        for building_name in auto_created_buildings[:10]:
            print(f"      - {building_name}")
        if len(auto_created_buildings) > 10:
            print(f"      ... and {len(auto_created_buildings) - 10} more")
        print("  Note: Nodes created at edge endpoints closest to building centroids (in-memory only)")
    else:
        print("  ✓ All specified buildings have valid nodes in network")

    # Get expected number of components from config
    expected_num_components = config.network_layout.number_of_components if config.network_layout.number_of_components else None

    # Save to network-name location
    output_layout_path = locator.get_network_layout_shapefile(network_name=network_layout.network_name)
    output_node_path_dc = locator.get_network_layout_nodes_shapefile('DC', network_layout.network_name)
    output_node_path_dh = locator.get_network_layout_nodes_shapefile('DH', network_layout.network_name)

    # Save layout-edges shapefile (shared)
    os.makedirs(os.path.dirname(output_layout_path), exist_ok=True)
    edges_gdf.to_file(output_layout_path, driver='ESRI Shapefile')

    # Process nodes separately for DC and DH
    if 'DC' in network_types_to_generate:
        print(f"\n{'='*60}")
        print(f"  DC NETWORK")
        print(f"{'='*60}")

        # Resolve cooling plant buildings
        # Plant buildings can be ANY building in the zone, not just connected buildings
        cooling_plant_buildings_list = resolve_plant_buildings(cooling_plant_building, all_zone_buildings, "cooling")

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

        # Normalize plant types: PLANT and PLANT_DC both become PLANT for DC network
        nodes_gdf_dc['type'] = nodes_gdf_dc['type'].replace({'PLANT_DC': 'PLANT'})

        os.makedirs(os.path.dirname(output_node_path_dc), exist_ok=True)
        nodes_gdf_dc.to_file(output_node_path_dc, driver='ESRI Shapefile')

    if 'DH' in network_types_to_generate:
        print(f"\n{'='*60}")
        print(f"  DH NETWORK")
        print(f"{'='*60}")

        # Resolve heating plant buildings
        # Plant buildings can be ANY building in the zone, not just connected buildings
        heating_plant_buildings_list = resolve_plant_buildings(heating_plant_building, all_zone_buildings, "heating")

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

        # Normalize plant types: PLANT and PLANT_DH both become PLANT for DH network
        nodes_gdf_dh['type'] = nodes_gdf_dh['type'].replace({'PLANT_DH': 'PLANT'})

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

    try:
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
    except Exception:
        # Cleanup partially created network folder on error
        network_folder = locator.get_thermal_network_folder_network_name_folder(network_layout.network_name)
        if os.path.exists(network_folder):
            shutil.rmtree(network_folder)
        raise


if __name__ == '__main__':
    main(cea.config.Configuration())

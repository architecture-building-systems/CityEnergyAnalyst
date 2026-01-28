import math
import platform
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
import wntr
import sys
import cea.config
import cea.inputlocator
import cea.technologies.substation as substation
from cea.constants import P_WATER_KGPERM3, FT_WATER_TO_PA, FT_TO_M, M_WATER_TO_PA, HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.optimization.constants import PUMP_ETA
from cea.optimization.preprocessing.preprocessing_main import get_building_names_with_load
from cea.technologies.thermal_network.utility import extract_network_from_shapefile, load_network_shapefiles
from cea.technologies.thermal_network.thermal_network_loss import calc_temperature_out_per_pipe
from cea.resources import geothermal
from cea.technologies.constants import NETWORK_DEPTH
from cea.utilities.epwreader import epw_reader
from cea.utilities.date import get_date_range_hours_from_year
from cea.technologies.network_layout.plant_node_operations import PlantServices


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# WNTR reports head loss "per unit pipe length" while EPANET reports "per 1000 ft or m"
# EPANET (2.2) [after WNTR 0.5] normalizes head loss per 1000 units of length so we don't need to scale it
if wntr.__version__.startswith('0.2'):
    scaling_factor = 1000  # EPANET 2.0 normalization
else:
    scaling_factor = 1     # EPANET 2.2 direct reporting


if sys.platform == "darwin" and platform.processor() == "arm":
     # Temp solution for EPANET toolkit on Apple Silicon: sign the library manually for WNTR v1.3.2
    # See https://github.com/USEPA/WNTR/issues/494

    from wntr.epanet.toolkit import libepanet
    import subprocess
    import importlib.util
    
    # Get the EPANET library location using modern importlib.resources
    try:
        # Python 3.9+: Use importlib.resources
        from importlib.resources import files
        epanet_location = str(files(libepanet))
    except ImportError:
        # Fallback for Python < 3.9: construct path manually using importlib
        spec = importlib.util.find_spec("wntr.epanet.toolkit")
        if spec is not None and spec.origin is not None:
            import os
            toolkit_dir = os.path.dirname(spec.origin)
            epanet_location = os.path.join(toolkit_dir, libepanet)
        else:
            raise ImportError("Could not locate wntr.epanet.toolkit module")

    result = subprocess.run(["codesign", "--verify", "--verbose", epanet_location], capture_output=True, text=True)
    if result.returncode != 0:
        subprocess.run(["codesign", "--force", "--sign", "-", epanet_location], check=True)


def add_date_to_dataframe(locator, df):
    # create date range for the calculation year
    weather_file = locator.get_weather_file()
    weather_data = epw_reader(weather_file)
    year = weather_data['year'][0]
    date_range = get_date_range_hours_from_year(year)

    # Convert date_range to datetime
    date_column = pd.to_datetime(date_range, errors='coerce')

    # Insert the 'date' column at the first position
    df.insert(0, 'date', date_column)

    return df

def calculate_ground_temperature(locator):
    """
    calculate ground temperatures.

    :param locator:
    :return: list of ground temperatures, one for each hour of the year
    :rtype: list[np.float64]
    """
    weather_file = locator.get_weather_file()
    T_ambient_C = epw_reader(weather_file)['drybulb_C']
    network_depth_m = NETWORK_DEPTH  # [m]
    T_ground_K = geothermal.calc_ground_temperature(T_ambient_C.values, network_depth_m)
    return T_ground_K


def calc_max_diameter(volume_flow_m3s, pipe_catalog: pd.DataFrame, velocity_ms, peak_load_percentage):
    if pipe_catalog.empty:
        raise ValueError("Pipe catalog is empty. Please check the thermal grid database.")

    volume_flow_m3s_corrected_to_design = volume_flow_m3s * peak_load_percentage / 100
    diameter_m = math.sqrt((volume_flow_m3s_corrected_to_design / velocity_ms) * (4 / math.pi))

    # Calculate differences and find the index of the minimum difference
    differences = (pipe_catalog['D_int_m'] - diameter_m).abs()
    closest_idx = differences.argsort().iloc[0]

    selection_of_catalog = pipe_catalog.iloc[[closest_idx]]
    D_int_m = selection_of_catalog['D_int_m'].values[0]
    pipe_DN = selection_of_catalog['pipe_DN'].values[0]
    D_ext_m = selection_of_catalog['D_ext_m'].values[0]
    D_ins_m = selection_of_catalog['D_ins_m'].values[0]

    return pipe_DN, D_ext_m, D_int_m, D_ins_m


def calc_head_loss_m(diameter_m, max_volume_flow_rates_m3s, coefficient_friction, length_m):
    hf_L = (10.67 / (coefficient_friction ** 1.85)) * (max_volume_flow_rates_m3s ** 1.852) / (diameter_m ** 4.8704)
    head_loss_m = hf_L * length_m
    return head_loss_m


def validate_network_topology_for_wntr(edge_df, node_df, consumer_nodes, plant_nodes, network_type):
    """
    Validate network topology before WNTR simulation to prevent cryptic EPANET errors.
    
    Performs comprehensive checks:
    - Network connectivity (single connected component)
    - Plant node presence and reachability from all consumers
    - Node/edge reference consistency
    - Isolated node detection
    - Edge endpoint validation
    
    :param edge_df: DataFrame of network edges with 'start node', 'end node', 'length_m'
    :param node_df: DataFrame of network nodes with index as node names
    :param consumer_nodes: List of consumer node names
    :param plant_nodes: DataFrame of plant nodes
    :param network_type: "DH" or "DC"
    :raises ValueError: If validation fails with detailed error message and resolution guidance
    """
    import networkx as nx
    
    print(f"Validating {network_type} network topology...")
    
    # 1. Check for duplicates (node IDs should already be validated, but double-check)
    duplicated_nodes = node_df[node_df.index.duplicated(keep=False)]
    duplicated_edges = edge_df[edge_df.index.duplicated(keep=False)]
    if duplicated_nodes.size > 0:
        raise ValueError(
            f"Network validation error: Duplicated NODE IDs found: {duplicated_nodes.index.values}\n"
            f"Each node must have a unique identifier.\n"
            f"Resolution: Check your network layout nodes.shp file and remove duplicate node IDs."
        )
    if duplicated_edges.size > 0:
        raise ValueError(
            f"Network validation error: Duplicated PIPE IDs found: {duplicated_edges.index.values}\n"
            f"Each pipe must have a unique identifier.\n"
            f"Resolution: Check your network layout edges.shp file and remove duplicate pipe IDs."
        )
    
    # 2. Validate edge endpoints reference existing nodes
    node_names = set(node_df.index)
    invalid_edges = []
    for edge_name, edge in edge_df.iterrows():
        start = edge['start node']
        end = edge['end node']
        
        if start not in node_names:
            invalid_edges.append(f"  - Edge '{edge_name}': start node '{start}' does not exist")
        if end not in node_names:
            invalid_edges.append(f"  - Edge '{edge_name}': end node '{end}' does not exist")
    
    if invalid_edges:
        raise ValueError(
            f"Network validation error: {len(invalid_edges)} edge(s) reference non-existent nodes:\n" +
            "\n".join(invalid_edges[:10]) +
            ("\n  ... and more" if len(invalid_edges) > 10 else "") +
            "\n\nResolution:\n"
            "  1. Check your network layout edges.shp file\n"
            "  2. Ensure all 'start node' and 'end node' values match existing node names\n"
            "  3. Regenerate network layout or manually fix node references"
        )
    
    # 3. Build NetworkX graph for topology analysis
    G = nx.Graph()
    for node_name in node_df.index:
        G.add_node(node_name)
    
    for edge_name, edge in edge_df.iterrows():
        start = edge['start node']
        end = edge['end node']
        G.add_edge(start, end)
    
    # 4. Check connectivity
    if not nx.is_connected(G):
        num_components = nx.number_connected_components(G)
        components = list(nx.connected_components(G))
        component_sizes = [len(c) for c in components]
        
        # Identify which components have plants and which don't
        plant_node_names = set(plant_nodes.index)
        components_with_plants = []
        components_without_plants = []
        
        for i, component in enumerate(components):
            if component & plant_node_names:
                components_with_plants.append((i, len(component)))
            else:
                components_without_plants.append((i, len(component), list(component)[:5]))
        
        error_details = [
            f"Network validation error: Network has {num_components} disconnected components.",
            f"Component sizes: {component_sizes}",
            f"Components with plants: {len(components_with_plants)}",
            f"Components without plants: {len(components_without_plants)}"
        ]
        
        if components_without_plants:
            error_details.append("\nDisconnected components without plant nodes:")
            for comp_id, size, sample_nodes in components_without_plants[:3]:
                error_details.append(f"  - Component {comp_id}: {size} nodes, including {sample_nodes}")
        
        error_details.extend([
            "\nWNTR/EPANET requires a fully connected network to solve hydraulic equations.",
            "\nResolution:",
            "  1. Check your network layout (edges.shp) for missing connections",
            "  2. Ensure all buildings are connected to the plant node(s)",
        ])
        
        raise ValueError("\n".join(error_details))
    
    # 5. Check for isolated nodes (degree = 0)
    isolated_nodes = [node for node, degree in G.degree() if degree == 0]
    if isolated_nodes:
        raise ValueError(
            f"Network validation error: Found {len(isolated_nodes)} isolated node(s) with no connections:\n"
            f"  {isolated_nodes[:10]}" +
            (f"\n  ... and {len(isolated_nodes) - 10} more" if len(isolated_nodes) > 10 else "") +
            "\n\nIsolated nodes cannot participate in network flow.\n"
            "Resolution:\n"
            "  1. Remove unused nodes from your network layout, or\n"
            "  2. Connect these nodes to the network with pipes"
        )
    
    # 6. Validate plant nodes
    if len(plant_nodes) == 0:
        raise ValueError(
            "Network validation error: No PLANT nodes found.\n"
            "At least one node must have type='PLANT' to serve as the network source.\n\n"
            "Resolution:\n"
            "  1. Check your network layout nodes.shp file\n"
            "  2. Ensure at least one node has type='PLANT'\n"
            "  3. Verify plant building names are correctly specified in configuration"
        )
    
    # 7. Check plant reachability from all consumers
    plant_nodes_list = plant_nodes.index.tolist()
    unreachable_consumers = []
    
    for consumer in consumer_nodes:
        has_path = any(nx.has_path(G, consumer, plant) for plant in plant_nodes_list)
        if not has_path:
            unreachable_consumers.append(consumer)
    
    if unreachable_consumers:
        raise ValueError(
            f"Network validation error: {len(unreachable_consumers)} consumer node(s) cannot reach any PLANT:\n"
            f"  {unreachable_consumers[:10]}" +
            (f"\n  ... and {len(unreachable_consumers) - 10} more" if len(unreachable_consumers) > 10 else "") +
            "\n\nAll consumers must have a path to at least one plant node.\n"
            "Resolution:\n"
            "  1. Check network connectivity between isolated consumers and plants\n"
            "  2. Add connecting pipes to link disconnected building groups\n"
            "  3. Verify the network layout includes all necessary connections"
        )
    
    # 8. Success - print summary
    print("  \u2713 Network topology validation passed:")
    print(f"    - {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"    - {len(plant_nodes)} plant node(s)")
    print(f"    - {len(consumer_nodes)} consumer node(s)")
    print("    - Network is fully connected")
    print("    - All consumers reachable from plant(s)")


def validate_demand_patterns(volume_flow_m3pers_building: pd.DataFrame, expected_hours: int = 8760):
    """
    Validate demand pattern consistency before WNTR simulation.
    
    Checks:
    - All buildings have consistent pattern lengths
    - Pattern length matches expected duration (default 8760 hours)
    - No NaN or infinite values in demand data
    
    :param volume_flow_m3pers_building: DataFrame with building demand flow rates (hours x buildings)
    :param expected_hours: Expected number of hours in demand patterns (default 8760 for full year)
    :raises ValueError: If patterns have inconsistent lengths or infinite values
    :raises Warning: If patterns don't match expected hours or contain NaN values
    """
    if volume_flow_m3pers_building.size == 0:
        warnings.warn("No demand patterns to validate (empty DataFrame).")
        return
    
    # Check pattern length consistency
    pattern_lengths = {
        building: len(volume_flow_m3pers_building[building]) 
        for building in volume_flow_m3pers_building.columns
    }
    
    if len(set(pattern_lengths.values())) > 1:
        raise ValueError(
            f"Network validation error: Demand patterns have inconsistent lengths: {pattern_lengths}\n"
            "All buildings must have demand profiles for the same time period.\n"
            "Resolution: Check your substation demand calculations."
        )
    
    # Verify pattern length matches expected hours
    actual_hours = list(pattern_lengths.values())[0] if pattern_lengths else 0
    if actual_hours != expected_hours:
        warnings.warn(
            f"Demand patterns have {actual_hours} hours, expected {expected_hours}. "
            "Simulation duration may not cover full year."
        )
    
    # Check for NaN or infinite values in demand data
    for building in volume_flow_m3pers_building.columns:
        if volume_flow_m3pers_building[building].isna().any():
            warnings.warn(
                f"Building '{building}' has NaN values in demand profile. "
                "This may cause WNTR simulation issues."
            )
        if np.isinf(volume_flow_m3pers_building[building]).any():
            raise ValueError(
                f"Network validation error: Building '{building}' has infinite values in demand profile.\n"
                "Resolution: Check substation demand calculations for this building."
            )
    
    print(f"  ✓ Demand pattern validation passed: {len(pattern_lengths)} building(s), {actual_hours} hours")


def calc_linear_thermal_loss_coefficient(diameter_ext_m, diameter_int_m, diameter_insulation_m):
    r_out_m = diameter_ext_m / 2
    r_in_m = diameter_int_m / 2
    r_s_m = diameter_insulation_m / 2
    k_pipe_WpermK = 58.7  # steel pipe
    k_ins_WpermK = 0.059  # calcium silicate insulation
    resistance_mKperW = ((math.log(r_out_m / r_in_m) / k_pipe_WpermK) + (math.log(r_s_m / r_out_m) / k_ins_WpermK))
    K_WperKm = 2 * math.pi / resistance_mKperW
    return K_WperKm

def calc_thermal_loss_per_pipe(T_in_K, m_kgpers, T_ground_K, k_kWperK):
    T_out_K = calc_temperature_out_per_pipe(T_in_K, m_kgpers, k_kWperK, T_ground_K)
    DT = T_in_K - T_out_K
    Q_loss_kWh = DT * m_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK / 1000

    return Q_loss_kWh

def calculate_minimum_network_temperature(substation_results_dict, itemised_dh_services):
    """
    Calculate minimum recommended network temperature based on PRIMARY service.

    The network temperature strategy is determined by the FIRST service in the list,
    which must match the logic in calc_DH_supply_temp_hvac() in substation.py.

    Service priority logic (based on first service in list):
    - space_heating first (PLANT_hs_ww): Network follows space heating temp (35°C min)
                                         DHW served by building boosters
    - domestic_hot_water first (PLANT_ww_hs): Network follows DHW temp (50°C min)
                                              DHW served directly from network

    In CT mode, the network supply temperature must be at least 5K higher than the
    building return temperature to allow for heat transfer (approach temperature constraint).

    :param substation_results_dict: Dictionary {building_name: substation_results_df}
    :param itemised_dh_services: List of services in priority order
                                 (e.g., ['space_heating', 'domestic_hot_water'])
    :return: Minimum recommended network temperature in °C
    """

    for building_name, df in substation_results_dict.items():
        # Get maximum return temperature when there's actual demand
        if 'Qhs_dh_W' in df.columns and 'Qww_dh_W' in df.columns:
            # Find hours with demand
            has_demand = (df['Qhs_dh_W'] + df['Qhs_booster_W'] +
                         df['Qww_dh_W'] + df['Qww_booster_W']) > 0

            if has_demand.any():
                # Get return temps from demand data (from original building demands)
                # We need to look at the actual building heating/DHW return temps
                # For now, use conservative estimates based on service type
                pass

    # Minimum temperature based on PRIMARY service (first in list)
    if itemised_dh_services is None or len(itemised_dh_services) == 0:
        # Legacy mode - assume DHW priority (conservative)
        return 50

    # Determine minimum based on PRIMARY service
    primary_service = itemised_dh_services[0]

    if primary_service == PlantServices.SPACE_HEATING:
        # PLANT_hs or PLANT_hs_ww: Low-temp network
        # Space heating return ~30°C + 5K approach = 35°C min
        return 35
    elif primary_service == PlantServices.DOMESTIC_HOT_WATER:
        # PLANT_ww or PLANT_ww_hs: High-temp network
        # DHW return ~45°C + 5K approach = 50°C min (allows preheat to 55°C, booster to 60°C)
        return 50
    else:
        # Unknown service, conservative minimum
        return 30


def calculate_maximum_network_temperature_cooling(substation_results_dict, itemised_dc_services):
    """
    Calculate maximum allowable network temperature for district cooling.

    In CT mode, the network supply temperature must be at least 5K lower than the minimum
    building supply temperature to allow for heat transfer (approach temperature constraint).

    :param substation_results_dict: Dictionary {building_name: substation_results_df}
    :param itemised_dc_services: List of services (e.g., ['space_cooling', 'data_center', 'refrigeration'])
    :return: Maximum allowable network temperature in °C
    """
    # Conservative maximum temps based on service type
    if itemised_dc_services is None:
        # Legacy mode - assume space cooling
        return 7  # Safe for typical space cooling (building needs ~12°C supply, so network at 7°C allows 5K approach)

    max_temps = []
    if PlantServices.SPACE_COOLING in itemised_dc_services:
        max_temps.append(7)  # Space cooling needs ~12°C building supply, so network at 7°C allows 5K approach
    if 'data_center' in itemised_dc_services:
        max_temps.append(10)  # Data center can use warmer supply (~15°C building supply)
    if 'refrigeration' in itemised_dc_services:
        max_temps.append(5)  # Refrigeration needs colder (~10°C building supply)

    return min(max_temps) if max_temps else 7


def thermal_network_simplified(locator: cea.inputlocator.InputLocator, config: cea.config.Configuration,
                              network_type, network_name, per_building_services=None):
    """
    Simplified thermal network model.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param network_type: 'DH' or 'DC'
    :param network_name: Name of network layout
    :param per_building_services: Dict mapping building → set of services
                                  Example: {'B001': {'space_heating', 'domestic_hot_water'},
                                           'B002': {'space_heating'}}
                                  If None, all buildings use all services (legacy behavior)
    """
    # local variables
    min_head_substation_kPa = config.thermal_network.min_head_substation
    thermal_transfer_unit_design_head_m = min_head_substation_kPa * 1000 / M_WATER_TO_PA
    coefficient_friction_hazen_williams = config.thermal_network.hw_friction_coefficient
    velocity_ms = config.thermal_network.peak_load_velocity
    fraction_equivalent_length = config.thermal_network.equivalent_length_factor
    peak_load_percentage = config.thermal_network.peak_load_percentage

    # GET INFORMATION ABOUT THE NETWORK
    network_nodes_df, network_edges_df = load_network_shapefiles(locator, network_type, network_name)
    node_df, edge_df = extract_network_from_shapefile(network_edges_df, network_nodes_df, filter_edges=True)

    # Extract service configuration from plant node type (DH only)
    itemised_dh_services = None
    is_legacy = False
    if network_type == "DH":
        from cea.technologies.network_layout.plant_node_operations import get_dh_services_from_plant_type

        # Find plant nodes
        plant_nodes = node_df[node_df['type'].str.contains('PLANT', na=False)]
        if not plant_nodes.empty:
            plant_type = plant_nodes.iloc[0]['type']
            services, is_legacy = get_dh_services_from_plant_type(plant_type)

            if is_legacy:
                print("  ℹ Using legacy temperature control:")
                print("    - Services: space heating + domestic hot water")
                print("    - Supply temperature: max(space heating temp, DHW temp)")
                print("    Hint: Run 'network-layout' with the new 'itemised-dh-services' parameter")
                # Pass None for legacy mode to trigger default behavior
                itemised_dh_services = None
            else:
                itemised_dh_services = services
                service_names = ' → '.join(itemised_dh_services)
                print(f"  ℹ DH service configuration: {service_names}")

    # GET INFORMATION ABOUT THE DEMAND OF BUILDINGS AND CONNECT TO THE NODE INFO
    # calculate substations for all buildings
    # local variables
    total_demand = pd.read_csv(locator.get_total_demand())
    volume_flow_m3pers_building = pd.DataFrame()
    T_sup_K_building = pd.DataFrame()
    T_re_K_building = pd.DataFrame()
    Q_demand_kWh_building = pd.DataFrame()
    Q_demand_DH_kWh_building = pd.DataFrame()  # DH contribution only (excludes booster) - for plant load calculation
    if network_type == "DH":
        buildings_name_with_heating = get_building_names_with_load(total_demand, load_name='QH_sys_MWhyr')
        DHN_barcode = "0"
        if buildings_name_with_heating:
            # Read network temperature configuration for DH
            fixed_network_temp_C = config.thermal_network.network_temperature_dh
            if fixed_network_temp_C is not None and fixed_network_temp_C > 0:
                print(f"  ℹ Network temperature mode: CT (Constant Temperature = {fixed_network_temp_C}°C)")
                print("    - Boosters will activate when building requirements exceed network temp")

                # Early validation: check if temperature is feasible for service type
                min_temp_required = calculate_minimum_network_temperature({}, itemised_dh_services)
                service_names = ' → '.join(itemised_dh_services) if itemised_dh_services else 'space heating + DHW'

                if fixed_network_temp_C < min_temp_required:
                    raise ValueError(
                        f"\n{'='*60}\n"
                        f"❌ TEMPERATURE CONFIGURATION ERROR\n"
                        f"{'='*60}\n"
                        f"Network temperature is too low for service configuration!\n\n"
                        f"  Service configuration: {service_names}\n"
                        f"  Network temperature:   {fixed_network_temp_C}°C\n"
                        f"  Minimum required:      {min_temp_required}°C\n\n"
                        f"With {service_names} as primary service(s), the network\n"
                        f"temperature must be at least {min_temp_required}°C for effective heat transfer.\n\n"
                        f"Explanation:\n"
                        f"  - For space heating priority: minimum 35°C (heating return ~30°C + 5K approach)\n"
                        f"  - For DHW priority: minimum 50°C (DHW return ~45°C + 5K approach)\n\n"
                        f"Current configuration will result in:\n"
                        f"  → Network provides essentially zero heat\n"
                        f"  → All heat from building boosters (defeats purpose of district heating)\n"
                        f"  → Hydraulic simulation will fail due to insufficient flow\n\n"
                        f"Solutions:\n"
                        f"  1. Increase network-temperature-dh to >={min_temp_required}°C\n"
                        f"  2. Use Variable Temperature (VT) mode: network-temperature-dh = -1\n"
                        f"  3. If DHW is priority, consider PLANT_ww_hs (needs 50-80°C)\n"
                        f"  4. If space heating is priority, use PLANT_hs_ww (needs 35-55°C)\n"
                        f"{'='*60}\n"
                    )
            else:
                print("  ℹ Network temperature mode: VT (Variable Temperature)")
                print("    - Network temp follows building requirements")
                fixed_network_temp_C = None  # Explicitly set to None for VT mode

            # Use set intersection to find buildings that exist in both collections
            node_buildings_set = set(node_df.building.values)
            buildings_with_heating_set = set(buildings_name_with_heating)
            building_names = list(buildings_with_heating_set & node_buildings_set)
            
            # Guard against empty building list
            if not building_names:
                raise ValueError('No buildings with heating demand are connected to the DH network.'
                                 ' Please check network layout and building demands.')
            
            substation.substation_main_heating(locator, total_demand, building_names,
                                               heating_configuration=7,
                                               DHN_barcode=DHN_barcode,
                                               itemised_dh_services=itemised_dh_services,
                                               per_building_services=per_building_services,  # NEW parameter
                                               fixed_network_temp_C=fixed_network_temp_C,
                                               network_type=network_type,
                                               network_name=network_name)
        else:
            raise ValueError('No district heating network created as there is no heating demand from any building.')

        # Store substation results for validation
        substation_results_dict = {}
        for building_name in building_names:
            substation_results = pd.read_csv(
                locator.get_thermal_network_substation_results_file(building_name, network_type, network_name))
            substation_results_dict[building_name] = substation_results

            volume_flow_m3pers_building[building_name] = substation_results["mdot_DH_result_kgpers"] / P_WATER_KGPERM3
            T_sup_K_building[building_name] = substation_results["T_supply_DH_result_C"] + 273.15  # Convert C to K
            T_re_K_building[building_name] = np.where(substation_results["T_return_DH_result_C"] > 0,
                                                      substation_results["T_return_DH_result_C"] + 273.15, np.nan)
            # Total demand = DH contribution + booster for both space heating and DHW
            Q_demand_kWh_building[building_name] = (
                substation_results["Qhs_dh_W"] + substation_results["Qhs_booster_W"] +
                substation_results["Qww_dh_W"] + substation_results["Qww_booster_W"]
            ) / 1000

            # DH contribution only (excludes booster heat from local equipment) - for plant load calculation
            Q_demand_DH_kWh_building[building_name] = (
                substation_results["Qhs_dh_W"] + substation_results["Qww_dh_W"]
            ) / 1000

        # Check for zero/near-zero DH flow condition
        total_dh_contribution_kWh = sum([
            (df['Qhs_dh_W'].sum() + df['Qww_dh_W'].sum()) / 1000
            for df in substation_results_dict.values()
        ])
        total_demand_kWh = sum([
            (df['Qhs_dh_W'].sum() + df['Qhs_booster_W'].sum() +
             df['Qww_dh_W'].sum() + df['Qww_booster_W'].sum()) / 1000
            for df in substation_results_dict.values()
        ])

        # Calculate space heating vs DHW contributions
        total_hs_demand_kWh = sum([
            (df['Qhs_dh_W'].sum() + df['Qhs_booster_W'].sum()) / 1000
            for df in substation_results_dict.values()
        ])
        total_ww_demand_kWh = sum([
            (df['Qww_dh_W'].sum() + df['Qww_booster_W'].sum()) / 1000
            for df in substation_results_dict.values()
        ])

        if total_demand_kWh > 0:
            dh_fraction = total_dh_contribution_kWh / total_demand_kWh
        else:
            dh_fraction = 0

        # Special validation for PLANT_hs_ww with no space heating demand
        if itemised_dh_services == ['space_heating', 'domestic_hot_water']:
            # This is a PLANT_hs_ww network (space heating priority)
            if total_hs_demand_kWh < 1.0:  # Less than 1 kWh/year of space heating
                raise ValueError(
                    f"\n{'='*70}\n"
                    f"❌ ERROR: PLANT_hs_ww network has zero space heating demand\n"
                    f"{'='*70}\n"
                    f"  Plant type: PLANT_hs_ww (space heating → DHW priority)\n"
                    f"  Space heating demand: {total_hs_demand_kWh:.2f} kWh/year\n"
                    f"  DHW demand: {total_ww_demand_kWh:.2f} kWh/year\n"
                    f"\n"
                    f"PLANT_hs_ww networks are designed for buildings with space heating needs.\n"
                    f"The network temperature is controlled by space heating requirements (35-45°C).\n"
                    f"\n"
                    f"Solutions:\n"
                    f"  1. Use PLANT_ww network type for DHW-only buildings\n"
                    f"     - Run network layout with 'itemised-dh-services' = ['domestic_hot_water']\n"
                    f"     - Network designed for higher temperatures (50-80°C)\n"
                    f"  2. Check if space heating demand exists in total-demand files\n"
                    f"     - Verify QH_sys_MWhyr > 0 for connected buildings\n"
                    f"  3. Remove buildings from network if they truly have no heating demand\n"
                    f"{'='*70}\n"
                )

        # If DH contribution is less than 1%, warn user and suggest minimum temperature (CT mode only)
        if dh_fraction < 0.01 and fixed_network_temp_C is not None:
            min_temp_required = calculate_minimum_network_temperature(substation_results_dict, itemised_dh_services)
            service_names = ' + '.join(itemised_dh_services) if itemised_dh_services else 'space heating + DHW'

            # Build detailed error message
            error_msg = (
                f"\n{'='*60}\n"
                f"⚠ WARNING: Network temperature insufficient for service type\n"
                f"{'='*60}\n"
                f"  Network temperature (CT mode): {fixed_network_temp_C}°C\n"
                f"  Service configuration: {service_names}\n"
                f"  Total building demand: {total_demand_kWh:.1f} kWh/year\n"
                f"  DH network contribution: {total_dh_contribution_kWh:.1f} kWh/year ({dh_fraction*100:.2f}%)\n"
                f"  Booster contribution: {total_demand_kWh - total_dh_contribution_kWh:.1f} kWh/year ({(1-dh_fraction)*100:.2f}%)\n"
                f"\n"
                f"  → Network supplies essentially zero heat (<1% of demand)\n"
                f"  → All heat provided by local boosters\n"
                f"  → Hydraulic simulation cannot run with zero flow\n"
                f"\n"
                f"Recommended minimum temperature for {service_names}:\n"
                f"  - Minimum: {min_temp_required}°C (allows some DH contribution)\n"
                f"  - Typical VT range: {min_temp_required + 5}-{min_temp_required + 15}°C\n"
                f"\n"
                f"Resolution:\n"
                f"  1. Increase network-temperature to >={min_temp_required}°C\n"
                f"  2. Use network-temperature=-1 for VT mode (variable temperature)\n"
                f"{'='*60}\n"
            )

            raise ValueError(error_msg)

    if network_type == "DC":
        buildings_name_with_cooling = get_building_names_with_load(total_demand, load_name='QC_sys_MWhyr')
        if buildings_name_with_cooling:
            # Use set intersection to find buildings that exist in both collections
            node_buildings_set = set(node_df.building.values)
            buildings_with_cooling_set = set(buildings_name_with_cooling)
            building_names = list(buildings_with_cooling_set & node_buildings_set)

            # Read network temperature configuration for DC
            fixed_network_temp_C = config.thermal_network.network_temperature_dc
            if fixed_network_temp_C is not None and fixed_network_temp_C > 0:
                print(f"  ℹ Network temperature mode: CT (Constant Temperature = {fixed_network_temp_C}°C)")
            else:
                print("  ℹ Network temperature mode: VT (Variable Temperature)")
                print("    - Network temp follows building requirements")
                fixed_network_temp_C = None  # Explicitly set to None for VT mode

            # Call new thermal network function (not optimization function)
            substation.substation_main_cooling_thermal_network(locator, total_demand, building_names,
                                                              fixed_network_temp_C=fixed_network_temp_C,
                                                              network_type=network_type,
                                                              network_name=network_name)
        else:
            raise ValueError('No district cooling network created as there is no cooling demand from any building.')

        # Read substation results and build dictionary for validation
        substation_results_dict = {}
        for building_name in building_names:
            substation_results = pd.read_csv(
                locator.get_thermal_network_substation_results_file(building_name, network_type, network_name))
            substation_results_dict[building_name] = substation_results

            volume_flow_m3pers_building[building_name] = substation_results["mdot_DC_result_kgpers"] / P_WATER_KGPERM3
            T_sup_K_building[building_name] = substation_results["T_supply_DC_result_C"] + 273.15  # Convert C to K
            T_re_K_building[building_name] = np.where(substation_results["T_return_DC_result_C"] > 0,
                                                      substation_results["T_return_DC_result_C"] + 273.15, np.nan)
            # Total demand = sum of all cooling types
            Q_demand_kWh_building[building_name] = (
                substation_results["Qcs_dc_W"] + substation_results["Qcdata_dc_W"] + substation_results["Qcre_dc_W"]
            ) / 1000

            # DC contribution (for DC networks, no boosters, so same as total demand)
            Q_demand_DH_kWh_building[building_name] = Q_demand_kWh_building[building_name]

        # Validate network temperature is cold enough for buildings (CT mode only)
        if fixed_network_temp_C is not None:
            # Check if heat exchangers failed (NaN or zero flow when there's demand)
            # This indicates network temperature is too warm to provide cooling
            total_demand_kWh = 0
            total_valid_flow = 0
            hours_with_demand = 0

            for b in building_names:
                df = substation_results_dict[b]
                demand_W = df["Qcs_dc_W"] + df["Qcdata_dc_W"] + df["Qcre_dc_W"]
                flow_kgpers = df["mdot_DC_result_kgpers"].fillna(0)  # Treat NaN as zero

                # Count hours with demand
                hours_with_demand += (demand_W > 100).sum()  # 100W threshold to avoid numerical noise

                # Count hours with valid flow when there's demand
                total_valid_flow += ((flow_kgpers > 0) & (demand_W > 100)).sum()

                total_demand_kWh += demand_W.sum() / 1000

            # If most hours with demand have zero flow, network temp is too warm
            if hours_with_demand > 0:
                flow_coverage_ratio = total_valid_flow / hours_with_demand
            else:
                flow_coverage_ratio = 1.0  # No demand, so no problem

            if flow_coverage_ratio < 0.01 and hours_with_demand > 0:
                # Determine cooling services (itemised loads)
                itemised_dc_services = []
                has_space_cooling = any(substation_results_dict[b]["Qcs_dc_W"].sum() > 0 for b in building_names)
                has_data_center = any(substation_results_dict[b]["Qcdata_dc_W"].sum() > 0 for b in building_names)
                has_refrigeration = any(substation_results_dict[b]["Qcre_dc_W"].sum() > 0 for b in building_names)

                if has_space_cooling:
                    itemised_dc_services.append(PlantServices.SPACE_COOLING)
                if has_data_center:
                    itemised_dc_services.append('data_center')
                if has_refrigeration:
                    itemised_dc_services.append('refrigeration')

                max_temp_allowed = calculate_maximum_network_temperature_cooling(substation_results_dict,
                                                                                 itemised_dc_services)
                service_names = ' + '.join(itemised_dc_services) if itemised_dc_services else 'space cooling'

                # Build detailed error message
                error_msg = (
                    f"\n{'='*60}\n"
                    f"⚠ WARNING: Network temperature too warm for cooling service\n"
                    f"{'='*60}\n"
                    f"  Network temperature (CT mode): {fixed_network_temp_C}°C\n"
                    f"  Service configuration: {service_names}\n"
                    f"  Total building demand: {total_demand_kWh:.1f} kWh/year\n"
                    f"  Hours with cooling demand: {hours_with_demand}\n"
                    f"  Hours with valid DC flow: {total_valid_flow} ({flow_coverage_ratio*100:.2f}%)\n"
                    f"\n"
                    f"  → Network supplies essentially zero cooling (<1% of hours)\n"
                    f"  → Network temperature too warm for heat exchangers to operate\n"
                    f"  → Hydraulic simulation cannot run with zero flow\n"
                    f"\n"
                    f"Physical constraint:\n"
                    f"  - Heat exchangers require temperature difference to transfer heat\n"
                    f"  - Network supply must be colder than building cooling coil temperature\n"
                    f"  - Typical approach temperature: 5K (heat exchanger constraint)\n"
                    f"  - Example: If building needs 12°C supply, network must be ≤7°C\n"
                    f"\n"
                    f"Recommended maximum temperature for {service_names}:\n"
                    f"  - Maximum: {max_temp_allowed}°C (allows DC to provide cooling)\n"
                    f"  - Typical VT range: 4-7°C for space cooling\n"
                    f"  - Typical VT range: 5-10°C for data center cooling\n"
                    f"\n"
                    f"Resolution:\n"
                    f"  1. Decrease network-temperature to <={max_temp_allowed}°C\n"
                    f"  2. Use network-temperature=-1 for VT mode (variable temperature)\n"
                    f"{'='*60}\n"
                )

                raise ValueError(error_msg)

    # Prepare the epanet simulation of the thermal network. To do so, as a first step, the epanet-library is loaded
    #   from within the set of utilities used by cea. In later steps, the contents of the nodes- and edges-shapefiles
    #   are transformed in a way that they can be properly interpreted by epanet.
    import cea.utilities
    with cea.utilities.pushd(locator.get_output_thermal_network_type_folder(network_type, network_name)):
        # Create a water network model
        wn = wntr.network.WaterNetworkModel()

        # add loads
        building_base_demand_m3s = {}
        building_nodes = node_df[node_df["type"] == "CONSUMER"]
        for node in building_nodes.iterrows():
            building = node[1]['building']

            if building not in volume_flow_m3pers_building.columns:
                warnings.warn(
                    f"Building {building} connected to node {node[0]} has no demand profile.\n"
                    "Please check that the building has a cooling/heating demand, or remove it from the network.\n"
                    "Setting base demand to 0."
                )
                building_base_demand_m3s[building] = 0
                wn.add_pattern(building, [0]*len(volume_flow_m3pers_building))
                continue

            building_base_demand_m3s[building] = volume_flow_m3pers_building[building].max()
            pattern_demand = (volume_flow_m3pers_building[building].values / building_base_demand_m3s[building]).tolist()
            wn.add_pattern(building, pattern_demand)
        
        # check that there is one plant node
        plant_nodes = node_df[node_df['type'].str.contains('PLANT', na=False)]
        if not len(plant_nodes) >= 1:
            raise ValueError("There should be at least one plant node in the network.")

        # Validate demand pattern consistency
        validate_demand_patterns(volume_flow_m3pers_building, expected_hours=8760)

        # Validate network topology before building WNTR model
        consumer_nodes = node_df[node_df['type'] == 'CONSUMER'].index.tolist()
        validate_network_topology_for_wntr(edge_df, node_df, consumer_nodes, plant_nodes, network_type)

        # add nodes
        consumer_nodes = []
        building_nodes_pairs = {}
        building_nodes_pairs_inversed = {}
        for node in node_df.iterrows():
            if node[1]["type"] == "CONSUMER":
                demand_pattern = node[1]['building']
                base_demand_m3s = building_base_demand_m3s[demand_pattern]
                consumer_nodes.append(node[0])
                building_nodes_pairs[node[0]] = demand_pattern
                building_nodes_pairs_inversed[demand_pattern] = node[0]
                wn.add_junction(node[0],
                                base_demand=base_demand_m3s,
                                demand_pattern=demand_pattern,
                                elevation=thermal_transfer_unit_design_head_m,
                                coordinates=node[1]["coordinates"])
            elif 'PLANT' in str(node[1]["type"]):
                base_head = int(thermal_transfer_unit_design_head_m*1.2)
                start_node = node[0]
                name_node_plant = start_node
                wn.add_reservoir(start_node,
                                 base_head=base_head,
                                 coordinates=node[1]["coordinates"])
            else:
                wn.add_junction(node[0],
                                elevation=0,
                                coordinates=node[1]["coordinates"])

        # add pipes (edge endpoints already validated in validate_network_topology_for_wntr)
        for edge in edge_df.iterrows():
            length_m = edge[1]["length_m"]
            edge_name = edge[0]
            start_node = edge[1]["start node"]
            end_node = edge[1]["end node"]
            
            wn.add_pipe(edge_name, start_node, end_node,
                        length=length_m * (1 + fraction_equivalent_length),
                        roughness=coefficient_friction_hazen_williams,
                        minor_loss=0.0,
                        initial_status='OPEN')

        # add options
        wn.options.time.duration = 8759 * 3600   # this indicates epanet to do one year simulation
        wn.options.time.hydraulic_timestep = 60 * 60
        wn.options.time.pattern_timestep = 60 * 60
        wn.options.hydraulic.accuracy = 0.01
        wn.options.hydraulic.trials = 100

        # 1st ITERATION GET MASS FLOWS AND CALCULATE DIAMETER
        print("Starting 1st iteration to calculate pipe diameters...")
        try:
            sim = wntr.sim.EpanetSimulator(wn)
            results = sim.run_sim()
        except Exception as e:
            error_msg = str(e)
            
            # Provide context-specific error messages
            if "110" in error_msg or "cannot solve" in error_msg.lower():
                raise ValueError(
                    f"WNTR simulation failed (Error 110 - cannot solve hydraulic equations):\n{error_msg}\n\n"
                    f"This typically indicates network topology or hydraulic issues:\n"
                    f"Possible causes:\n"
                    f"  - Disconnected network components (already validated - this shouldn't happen)\n"
                    f"  - Extreme pipe lengths or diameters causing numerical instability\n"
                    f"  - Conflicting pressure/flow constraints\n"
                    f"  - Insufficient pressure sources (check plant node configuration)\n\n"
                    f"Resolution:\n"
                    f"  1. Check network layout for very long pipes or unusual geometries\n"
                    f"  2. Verify min_head_substation configuration (current: {min_head_substation_kPa} kPa)\n"
                    f"  3. Check demand values are reasonable (not extremely high)\n"
                    f"  4. Review pipe friction coefficient (current: {coefficient_friction_hazen_williams})"
                ) from e
            elif "convergence" in error_msg.lower():
                raise ValueError(
                    f"WNTR simulation failed to converge:\n{error_msg}\n\n"
                    f"Possible causes:\n"
                    f"  - Network has extreme pressure/flow conditions\n"
                    f"  - Demand patterns have very high peaks\n"
                    f"  - Pipe diameters too small for required flows\n\n"
                    f"Resolution:\n"
                    f"  1. Check peak_load_percentage setting (current: {peak_load_percentage}%)\n"
                    f"  2. Increase initial pipe diameter estimates\n"
                    f"  3. Verify demand profiles are reasonable"
                ) from e
            elif "negative pressure" in error_msg.lower():
                raise ValueError(
                    f"WNTR simulation error - negative pressure detected:\n{error_msg}\n\n"
                    f"Possible causes:\n"
                    f"  - Insufficient pump head at plant node\n"
                    f"  - Network too long or high friction losses\n"
                    f"  - Elevation differences not properly accounted for\n\n"
                    f"Resolution:\n"
                    f"  1. Increase min_head_substation (current: {min_head_substation_kPa} kPa)\n"
                    f"  2. Check thermal_transfer_unit_design_head_m calculation\n"
                    f"  3. Reduce friction coefficient or increase pipe diameters"
                ) from e
            else:
                raise ValueError(
                    f"WNTR simulation failed during 1st iteration (diameter calculation):\n{error_msg}\n\n"
                    f"Check your network topology, demand patterns, and configuration parameters.\n"
                    f"Enable debug mode for more details."
                ) from e
        
        # Validate results
        if results.link['flowrate'].empty:
            raise ValueError(
                "WNTR simulation produced empty flowrate results. "
                "This indicates a problem with network definition or simulation setup."
            )
        
        if results.link['flowrate'].isna().any().any():
            nan_pipes = results.link['flowrate'].columns[results.link['flowrate'].isna().any()].tolist()
            warnings.warn(
                f"WNTR simulation produced NaN flowrates for {len(nan_pipes)} pipe(s): {nan_pipes[:5]}. "
                f"Results may be unreliable. Check network connectivity and demand patterns."
            )
        
        max_volume_flow_rates_m3s = results.link['flowrate'].abs().max()
        pipe_names = max_volume_flow_rates_m3s.index.values
        pipe_catalog = pd.read_csv(locator.get_database_components_distribution_thermal_grid('THERMAL_GRID'))
        pipe_DN, D_ext_m, D_int_m, D_ins_m = zip(
            *[calc_max_diameter(flow, pipe_catalog, velocity_ms=velocity_ms, peak_load_percentage=peak_load_percentage) for
              flow in max_volume_flow_rates_m3s])
        pipe_dn = pd.Series(pipe_DN, pipe_names)
        diameter_int_m = pd.Series(D_int_m, pipe_names)
        diameter_ext_m = pd.Series(D_ext_m, pipe_names)
        diameter_ins_m = pd.Series(D_ins_m, pipe_names)

        # 2nd ITERATION GET PRESSURE POINTS AND MASSFLOWS FOR SIZING PUMPING NEEDS - this could be for all the year
        print("Starting 2nd iteration to calculate pressure drops...")
        # modify diameter and run simulations
        edge_df['pipe_DN'] = pipe_dn
        edge_df['D_int_m'] = D_int_m
        for edge in edge_df.iterrows():
            edge_name = edge[0]
            pipe = wn.get_link(edge_name)
            pipe.diameter = diameter_int_m[edge_name]
        
        try:
            sim = wntr.sim.EpanetSimulator(wn)
            results = sim.run_sim()
        except Exception as e:
            error_msg = str(e)
            raise ValueError(
                f"WNTR simulation failed during 2nd iteration (pressure drop calculation):\n{error_msg}\n\n"
                f"This error occurred after pipe diameters were updated.\n"
                f"Calculated pipe diameters: DN {pipe_dn.min()}-{pipe_dn.max()} mm\n\n"
                f"Resolution:\n"
                f"  1. Check if calculated pipe diameters are reasonable\n"
                f"  2. Verify pipe catalog has appropriate diameter range\n"
                f"  3. Check if velocity constraint is too restrictive (current: {velocity_ms} m/s)"
            ) from e
        
        # Validate results
        if results.link['headloss'].isna().any().any():
            warnings.warn(
                "WNTR simulation produced NaN headloss values. "
                "Pressure drop calculations may be unreliable."
            )

        # 3rd ITERATION GET FINAL UTILIZATION OF THE GRID (SUPPLY SIDE)
        print("Starting 3rd iteration to calculate final utilization of the grid...")
        # get accumulated head loss per hour
        unitary_head_ftperkft = results.link['headloss'].abs()
        unitary_head_mperm = unitary_head_ftperkft * FT_TO_M / (FT_TO_M * scaling_factor)
        head_loss_m = unitary_head_mperm.copy()
        for column in head_loss_m.columns.values:
            length_m = edge_df.loc[column]['length_m']
            head_loss_m[column] = head_loss_m[column] * length_m
        reservoir_head_loss_m = head_loss_m.sum(axis=1) + thermal_transfer_unit_design_head_m*1.2 # fixme: only one thermal_transfer_unit_design_head_m from one substation?

        # apply this pattern to the reservoir and get results
        base_head = reservoir_head_loss_m.max()
        pattern_head_m = (reservoir_head_loss_m.values / base_head).tolist()
        wn.add_pattern('reservoir', pattern_head_m)
        reservoir = wn.get_node(name_node_plant)
        reservoir.head_timeseries.base_value = int(base_head)
        reservoir.head_timeseries._pattern = 'reservoir'
        
        try:
            sim = wntr.sim.EpanetSimulator(wn)
            results = sim.run_sim()
        except Exception as e:
            error_msg = str(e)
            raise ValueError(
                f"WNTR simulation failed during 3rd iteration (final utilization):\n{error_msg}\n\n"
                f"This error occurred during final network simulation with dynamic head pattern.\n"
                f"Base head: {base_head:.2f} m\n"
                f"Pattern range: {min(pattern_head_m):.3f} - {max(pattern_head_m):.3f}\n\n"
                f"Resolution:\n"
                f"  1. Check if head pattern values are reasonable\n"
                f"  2. Verify calculated head losses are not extreme\n"
                f"  3. Check for pipes with very high pressure drops"
            ) from e
        
        # Final validation of complete results
        if results.link['flowrate'].isna().all().all():
            # Calculate total demand for diagnostic
            total_flow_m3s = sum([
                volume_flow_m3pers_building[bldg].sum()
                for bldg in building_names
            ])

            raise ValueError(
                f"\n{'='*70}\n"
                f"❌ ERROR: WNTR hydraulic simulation failed completely\n"
                f"{'='*70}\n"
                f"Network type: {network_type}\n"
                f"Network name: {network_name}\n"
                f"Total demand flow: {total_flow_m3s:.6f} m³/s\n"
                f"\n"
                f"All flowrate results are NaN - hydraulic simulation could not converge.\n"
                f"\n"
                f"Common causes:\n"
                f"  1. Near-zero flow due to insufficient network temperature\n"
                f"     - Network temp too low → all heat from boosters → zero DH flow\n"
                f"     - Check previous warnings about DH contribution <1%\n"
                f"  2. Extreme pressure losses\n"
                f"     - Very small pipes with high flow rates\n"
                f"     - Check pipe diameter calculations\n"
                f"  3. Network topology issues\n"
                f"     - Disconnected segments (should be caught earlier)\n"
                f"     - Invalid boundary conditions\n"
                f"  4. Plant type mismatch with building demands\n"
                f"     - PLANT_hs_ww with zero space heating → use PLANT_ww\n"
                f"     - PLANT_ww_hs with zero DHW → use PLANT_hs_ww\n"
                f"\n"
                f"Resolution:\n"
                f"  - Review all warnings and errors printed above\n"
                f"  - Check total demand is >0 and DH contribution is significant\n"
                f"  - Verify network temperature is appropriate for service type\n"
                f"  - Use Variable Temperature mode (network-temperature=-1) if unsure\n"
                f"{'='*70}\n"
            )
        
        print("All WNTR simulations completed successfully.")

    # POSTPROCESSING
    print("Postprocessing thermal network results...")

    # $ POSTPROCESSING - PRESSURE/HEAD LOSSES PER PIPE PER HOUR OF THE YEAR
    # at the pipes
    unitary_head_loss_supply_network_ftperkft = results.link['headloss'].abs()
    linear_pressure_loss_Paperm = unitary_head_loss_supply_network_ftperkft * FT_WATER_TO_PA / (FT_TO_M * scaling_factor)
    head_loss_supply_network_Pa = linear_pressure_loss_Paperm.copy()
    for column in head_loss_supply_network_Pa.columns.values:
        length_m = edge_df.loc[column]['length_m']
        head_loss_supply_network_Pa[column] = head_loss_supply_network_Pa[column] * length_m

    head_loss_return_network_Pa = head_loss_supply_network_Pa.copy(0)
    # at the substations
    head_loss_substations_ft = results.node['head'][consumer_nodes].abs()
    head_loss_substations_Pa = head_loss_substations_ft * FT_WATER_TO_PA

    #POSTPORCESSING MASSFLOW RATES
    # MASS_FLOW_RATE (EDGES)
    flow_rate_supply_m3s = results.link['flowrate'].abs()
    massflow_supply_kgs = flow_rate_supply_m3s * P_WATER_KGPERM3

    # $ POSTPROCESSING - PRESSURE LOSSES ACCUMULATED PER HOUR OF THE YEAR (TIMES 2 to account for return)
    accumulated_head_loss_supply_Pa = head_loss_supply_network_Pa.sum(axis=1)
    accumulated_head_loss_return_Pa = head_loss_return_network_Pa.sum(axis=1)
    accumulated_head_loss_substations_Pa = head_loss_substations_Pa.sum(axis=1)
    accumulated_head_loss_total_Pa = accumulated_head_loss_supply_Pa + accumulated_head_loss_return_Pa + accumulated_head_loss_substations_Pa

    # $ POSTPROCESSING - THERMAL LOSSES PER PIPE PER HOUR OF THE YEAR (SUPPLY)
    # calculate the thermal characteristics of the grid
    temperature_of_the_ground_K = calculate_ground_temperature(locator)
    thermal_coeffcient_WperKm = pd.Series(
        np.vectorize(calc_linear_thermal_loss_coefficient)(diameter_ext_m, diameter_int_m, diameter_ins_m), pipe_names)
    average_temperature_supply_K = T_sup_K_building.mean(axis=1)


    thermal_losses_supply_kWh = results.link['headloss'].copy()
    thermal_losses_supply_kWh.reset_index(inplace=True, drop=True)
    thermal_losses_supply_Wperm = thermal_losses_supply_kWh.copy()
    for pipe in pipe_names:
        length_m = edge_df.loc[pipe]['length_m']
        massflow_kgs = massflow_supply_kgs[pipe]
        k_WperKm_pipe = thermal_coeffcient_WperKm[pipe]
        k_kWperK = k_WperKm_pipe * length_m / 1000
        thermal_losses_supply_kWh[pipe] = np.vectorize(calc_thermal_loss_per_pipe)(average_temperature_supply_K.values,
                                                                     massflow_kgs.values,
                                                                     temperature_of_the_ground_K,
                                                                     k_kWperK,
                                                                     )

        thermal_losses_supply_Wperm[pipe] = (thermal_losses_supply_kWh[pipe] / length_m) * 1000

    # return pipes
    average_temperature_return_K = T_re_K_building.mean(axis=1)
    thermal_losses_return_kWh = results.link['headloss'].copy()
    thermal_losses_return_kWh.reset_index(inplace=True, drop=True)
    for pipe in pipe_names:
        length_m = edge_df.loc[pipe]['length_m']
        massflow_kgs = massflow_supply_kgs[pipe]
        k_WperKm_pipe = thermal_coeffcient_WperKm[pipe]
        k_kWperK = k_WperKm_pipe * length_m / 1000
        thermal_losses_return_kWh[pipe] = np.vectorize(calc_thermal_loss_per_pipe)(average_temperature_return_K.values,
                                                                     massflow_kgs.values,
                                                                     temperature_of_the_ground_K,
                                                                     k_kWperK,
                                                                     )
    # WRITE TO DISK
    locator.ensure_parent_folder_exists(locator.get_thermal_network_folder())

    # Ensure network_name folder exists (for new structure: thermal-network/DC/network_name/)
    if network_name:
        import os
        network_folder = locator.get_output_thermal_network_type_folder(network_type, network_name)
        if not os.path.exists(network_folder):
            os.makedirs(network_folder)

    # LINEAR PRESSURE LOSSES (EDGES)
    linear_pressure_loss_Paperm.to_csv(locator.get_network_linear_pressure_drop_edges(network_type, network_name),
                                       index=False)

    # MASS_FLOW_RATE (EDGES)
    flow_rate_supply_m3s = results.link['flowrate'].abs()
    massflow_supply_kgs = flow_rate_supply_m3s * P_WATER_KGPERM3
    massflow_supply_kgs.to_csv(locator.get_thermal_network_layout_massflow_edges_file(network_type, network_name),
                               index=False)

    # VELOCITY (EDGES)
    velocity_edges_ms = results.link['velocity'].abs()
    velocity_edges_ms.to_csv(locator.get_thermal_network_velocity_edges_file(network_type, network_name),
                             index=False)

    # PRESSURE LOSSES (NODES)
    pressure_at_nodes_ft = results.node['pressure'].abs()
    pressure_at_nodes_Pa = pressure_at_nodes_ft * FT_TO_M * M_WATER_TO_PA
    pressure_at_nodes_Pa.to_csv(locator.get_network_pressure_at_nodes(network_type, network_name), index=False)

    # MASS_FLOW_RATE (NODES)
    # $ POSTPROCESSING - MASSFLOWRATES PER NODE PER HOUR OF THE YEAR
    flow_rate_supply_nodes_m3s = results.node['demand'].abs()
    massflow_supply_nodes_kgs = flow_rate_supply_nodes_m3s * P_WATER_KGPERM3
    massflow_supply_nodes_kgs.to_csv(locator.get_thermal_network_layout_massflow_nodes_file(network_type, network_name),
                                     index=False)

    # thermal demand per building (no losses in the network or substations)
    Q_demand_Wh_building = Q_demand_kWh_building * 1000
    Q_demand_Wh_building.to_csv(locator.get_thermal_demand_csv_file(network_type, network_name), index=False)

    # pressure losses total
    # $ POSTPROCESSING - PUMPING NEEDS PER HOUR OF THE YEAR (TIMES 2 to account for return)
    flow_rate_substations_m3s = results.node['demand'][consumer_nodes].abs()
    # head_loss_supply_kWperm = (linear_pressure_loss_Paperm * (flow_rate_supply_m3s * 3600)) / (3.6E6 * PUMP_ETA)
    # head_loss_return_kWperm = head_loss_supply_kWperm.copy()
    pressure_loss_supply_edge_kW = (head_loss_supply_network_Pa * (flow_rate_supply_m3s * 3600)) / (3.6E6 * PUMP_ETA)
    head_loss_return_kW = pressure_loss_supply_edge_kW.copy()
    head_loss_substations_kW = (head_loss_substations_Pa * (flow_rate_substations_m3s * 3600)) / (3.6E6 * PUMP_ETA)
    accumulated_head_loss_supply_kW = pressure_loss_supply_edge_kW.sum(axis=1)
    accumulated_head_loss_return_kW = head_loss_return_kW.sum(axis=1)
    accumulated_head_loss_substations_kW = head_loss_substations_kW.sum(axis=1)
    accumulated_head_loss_total_kW = accumulated_head_loss_supply_kW + \
                                     accumulated_head_loss_return_kW + \
                                     accumulated_head_loss_substations_kW
    head_loss_system_Pa = pd.DataFrame({"pressure_loss_supply_Pa": accumulated_head_loss_supply_Pa,
                                        "pressure_loss_return_Pa": accumulated_head_loss_return_Pa,
                                        "pressure_loss_substations_Pa": accumulated_head_loss_substations_Pa,
                                        "pressure_loss_total_Pa": accumulated_head_loss_total_Pa})
    head_loss_system_Pa.to_csv(locator.get_network_total_pressure_drop_file(network_type, network_name),
                               index=False)

    # $ POSTPROCESSING - PLANT HEAT REQUIREMENT moved to after thermal losses calculation (line ~1218)

    # pressure losses per piping system
    pressure_loss_supply_edge_kW.to_csv(
        locator.get_thermal_network_pressure_losses_edges_file(network_type, network_name), index=False)

    # pressure losses per substation
    head_loss_substations_kW = head_loss_substations_kW.rename(columns=building_nodes_pairs)
    head_loss_substations_kW.to_csv(locator.get_thermal_network_substation_ploss_file(network_type, network_name),
                                    index=False)

    # pumping needs losses total
    pumping_energy_system_kWh = pd.DataFrame({"pressure_loss_supply_kW": accumulated_head_loss_supply_kW,
                                              "pressure_loss_return_kW": accumulated_head_loss_return_kW,
                                              "pressure_loss_substations_kW": accumulated_head_loss_substations_kW,
                                              "pressure_loss_total_kW": accumulated_head_loss_total_kW})

    pumping_energy_system_kWh = add_date_to_dataframe(locator, pumping_energy_system_kWh)
    pumping_energy_system_kWh.to_csv(
        locator.get_network_energy_pumping_requirements_file(network_type, network_name), index=False)

    # pumping needs losses total
    temperatures_plant_C = pd.DataFrame({"temperature_supply_K": average_temperature_supply_K,
                                         "temperature_return_K": average_temperature_return_K})
    temperatures_plant_C.to_csv(locator.get_network_temperature_plant(network_type, network_name), index=False)

    # thermal losses
    thermal_losses_supply_kWh.to_csv(locator.get_network_thermal_loss_edges_file(network_type, network_name),
                                     index=False)
    thermal_losses_supply_Wperm.to_csv(locator.get_network_linear_thermal_loss_edges_file(network_type, network_name),
                                       index=False)

    # thermal losses total
    accumulated_thermal_losses_supply_kWh = thermal_losses_supply_kWh.sum(axis=1)
    accumulated_thermal_losses_return_kWh = thermal_losses_return_kWh.sum(axis=1)
    accumulated_thermal_loss_total_kWh = accumulated_thermal_losses_supply_kWh + accumulated_thermal_losses_return_kWh
    thermal_losses_total_kWh = pd.DataFrame({"thermal_loss_supply_kW": accumulated_thermal_losses_supply_kWh,
                                             "thermal_loss_return_kW": accumulated_thermal_losses_return_kWh,
                                             "thermal_loss_total_kW": accumulated_thermal_loss_total_kWh})
    thermal_losses_total_kWh.to_csv(locator.get_network_total_thermal_loss_file(network_type, network_name),
                                    index=False)

    # PLANT THERMAL LOAD REQUIREMENT
    # Plant thermal load = DH delivered to buildings + network thermal losses
    # (Use DH-only demand, excludes booster heat from local equipment at buildings)
    plant_load_kWh = Q_demand_DH_kWh_building.sum(axis=1) + accumulated_thermal_loss_total_kWh
    plant_load_kWh = pd.DataFrame(plant_load_kWh, columns=['thermal_load_kW'])
    plant_load_kWh = add_date_to_dataframe(locator, plant_load_kWh)
    plant_load_kWh.to_csv(locator.get_thermal_network_plant_heat_requirement_file(network_type, network_name))

    # return average temperature of supply at the substations
    T_sup_K_nodes = T_sup_K_building.rename(columns=building_nodes_pairs_inversed)
    average_year = T_sup_K_nodes.mean(axis=1)
    for node in node_df.index.values:
        T_sup_K_nodes[node] = average_year
    T_sup_K_nodes.to_csv(locator.get_network_temperature_supply_nodes_file(network_type, network_name),
                         index=False)

    # return average temperature of return at the substations
    T_return_K_nodes = T_re_K_building.rename(columns=building_nodes_pairs_inversed)
    average_year = T_return_K_nodes.mean(axis=1)
    for node in node_df.index.values:
        T_return_K_nodes[node] = average_year
    T_return_K_nodes.to_csv(locator.get_network_temperature_return_nodes_file(network_type, network_name),
                         index=False)

    # summary of edges used for the calculation
    fields_edges = ['length_m', 'pipe_DN', 'type_mat', 'D_int_m']
    edge_df[fields_edges].to_csv(locator.get_thermal_network_edge_list_file(network_type, network_name))
    fields_nodes = ['type', 'building']
    node_df[fields_nodes].to_csv(locator.get_thermal_network_node_types_csv_file(network_type, network_name))

    # save updated edge data back to shapefile
    fields = ['length_m', 'pipe_DN', 'type_mat', 'geometry']
    edge_df_gdf = gpd.GeoDataFrame(edge_df[fields], index=edge_df.index)
    edge_df_gdf.to_file(locator.get_network_layout_edges_shapefile(network_type, network_name))

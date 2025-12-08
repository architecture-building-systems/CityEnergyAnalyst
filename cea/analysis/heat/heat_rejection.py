"""
Anthropogenic Heat Rejection Calculations

This module calculates heat rejection to the environment from building energy systems.
It reuses the optimization-new framework's heat rejection tracking capabilities.

Key concepts:
- Anthropogenic heat = Heat_Rejection + Electricity_for_Heat_Rejection
- Building-scale: Standalone buildings and buildings providing own heating/cooling/DHW
- District-scale: Central plants in thermal networks
- Multiple plants: Heat split equally across all plant nodes

Pattern mirrors cea/analysis/costs/supply_costs.py but focuses on heat emissions.
"""
import pandas as pd
import geopandas as gpd

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def remove_leap_day(hourly_series):
    """
    Remove Feb 29 from hourly time series data to ensure 8760 hours.

    In a leap year, Feb 29 is day 60 (0-indexed: day 59).
    Hours 1416-1439 (24 hours) need to be removed.

    :param hourly_series: pd.Series or list with 8784 hours (leap year)
    :return: pd.Series or list with 8760 hours
    """
    if isinstance(hourly_series, pd.Series):
        # Remove hours 1416-1439 (Feb 29)
        return pd.concat([hourly_series.iloc[:1416], hourly_series.iloc[1440:]])
    else:
        # For lists
        return hourly_series[:1416] + hourly_series[1440:]


def anthropogenic_heat_main(locator, config):
    """
    Main function to calculate anthropogenic heat rejection.

    This follows the same 6-case building connectivity logic as system-costs:
    - Case 1: Standalone mode (no networks)
    - Cases 2-6: Network + standalone combinations

    :param locator: InputLocator instance
    :param config: Configuration instance with anthropogenic-heat parameters
    """
    print("\n" + "=" * 70)
    print("ANTHROPOGENIC HEAT ASSESSMENT")
    print("=" * 70)

    # Get network configuration
    network_name = config.system_costs.network_name
    network_types = config.system_costs.network_type

    # Validate network types
    if not network_types or len(network_types) == 0:
        raise ValueError("No network types selected. Please select at least one from: DH, DC")

    # Check for standalone-only mode
    is_standalone_only = (not network_name or network_name.strip() == "" or
                         network_name.strip() == "(none)")

    if is_standalone_only:
        print("Mode: STANDALONE ONLY (all buildings assessed as standalone systems)")
        print("District-scale supply systems will be treated as building-scale for heat calculations.")
        print(f"Network types (for supply system selection): {', '.join(network_types)}\n")
    else:
        print("Mode: NETWORK + STANDALONE")
        print(f"Network layout: {network_name}")
        print(f"Network types: {', '.join(network_types)}\n")

    # Step 1: Calculate building-level heat rejection
    print("-" * 70)
    if is_standalone_only:
        print("Calculating ALL buildings as standalone systems...")
        standalone_results = calculate_standalone_heat_rejection(locator, config, network_types)

        # In standalone mode, there are no network results
        network_results = {}

    else:
        print("Calculating standalone building heat rejection...")
        standalone_results = calculate_standalone_heat_rejection(locator, config, network_types)

        # Step 2: Calculate district network heat rejection
        network_results = {}
        for network_type in network_types:
            print("\n" + "-" * 70)
            print(f"Calculating {network_type} district network heat rejection...")

            network_heat = calculate_network_heat_rejection(
                locator, config, network_type, network_name, standalone_results
            )

            if network_heat:
                network_results[network_type] = network_heat

    # Step 3: Merge and format results
    print("\n" + "-" * 70)
    print("Merging and formatting results...")

    all_results = merge_heat_rejection_results(
        locator, standalone_results, network_results, is_standalone_only
    )

    # Step 4: Save outputs
    print("\n" + "-" * 70)
    print("Saving results...")

    save_heat_rejection_outputs(locator, all_results, is_standalone_only, network_name=network_name)

    print("\n" + "=" * 70)
    if is_standalone_only:
        print("COMPLETED (Standalone Mode)")
    else:
        print("COMPLETED")
    print("=" * 70)
    print(f"Summary: {locator.get_heat_rejection_buildings(network_name=network_name)}")
    print(f"Detailed: {locator.get_heat_rejection_components(network_name=network_name)}")
    print(f"Spatial: {locator.get_heat_rejection_hourly_spatial()}")


def calculate_standalone_heat_rejection(locator, config, network_types):
    """
    Calculate heat rejection for all buildings using building-scale systems.

    REUSES supply_costs.calculate_all_buildings_as_standalone() to ensure consistency,
    then extracts heat_rejection from the resulting supply systems.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param network_types: List of network types ['DH', 'DC']
    :return: dict of {building_id: heat_rejection_data}
    """
    import cea.config
    from cea.analysis.costs.supply_costs import (
        calculate_standalone_building_costs,  # Use this instead of calculate_all_buildings_as_standalone
        get_network_buildings  # REUSE same network detection as costs
    )

    # REUSE cost module's network detection (checks thermal-network outputs)
    network_name = config.system_costs.network_name
    dh_network_buildings = get_network_buildings(locator, network_name, 'DH')
    dc_network_buildings = get_network_buildings(locator, network_name, 'DC')

    print(f"  Found {len(dh_network_buildings)} buildings in DH network")
    print(f"  Found {len(dc_network_buildings)} buildings in DC network")

    # Create a config that maps anthropogenic_heat parameters to system_costs parameters
    # This allows us to reuse the supply_costs functions
    from cea.analysis.costs.supply_costs import filter_supply_code_by_scale

    cost_config = cea.config.Configuration()
    cost_config.scenario = config.scenario
    cost_config.system_costs.network_name = network_name  # Pass network name for network detection
    cost_config.system_costs.network_type = network_types

    # Filter supply codes to building-scale only for standalone calculations
    cost_config.system_costs.supply_type_cs = filter_supply_code_by_scale(
        locator, config.system_costs.supply_type_cs, 'SUPPLY_COOLING', is_standalone=True
    )
    cost_config.system_costs.supply_type_hs = filter_supply_code_by_scale(
        locator, config.system_costs.supply_type_hs, 'SUPPLY_HEATING', is_standalone=True
    )
    cost_config.system_costs.supply_type_dhw = filter_supply_code_by_scale(
        locator, config.system_costs.supply_type_dhw, 'SUPPLY_HOTWATER', is_standalone=True
    )

    # REUSE supply_costs function to create supply systems with 4-case logic
    # This function respects network connectivity and calculates only standalone services
    building_cost_results = calculate_standalone_building_costs(locator, cost_config, network_name)

    # Convert to heat rejection results
    results = {}
    for building_id, cost_data in building_cost_results.items():
        building_obj = cost_data.get('building')
        supply_system = cost_data.get('supply_system')

        # Collect all supply systems (main + DHW fallback)
        supply_systems_list = []
        heat_rejection_data = {}

        # Extract heat rejection from main supply system
        if supply_system is not None and hasattr(supply_system, 'heat_rejection'):
            heat_rejection_data.update(supply_system.heat_rejection)
            supply_systems_list.append(supply_system)

        # Check if building needs DHW fallback (same logic as supply_costs.py:1281-1287)
        # DHW systems have separate heat rejection that must be included
        demand_df = pd.read_csv(locator.get_total_demand())
        building_demand = demand_df[demand_df['name'] == building_id]
        if not building_demand.empty:
            qww = building_demand['Qww_sys_MWhyr'].values[0] if 'Qww_sys_MWhyr' in building_demand.columns else 0

            # Try DHW fallback if DHW demand exists
            if qww > 0:
                dhw_system = create_dhw_heat_rejection_system(locator, building_obj, supply_system)

                if dhw_system is not None:
                    # Extract heat rejection from DHW system
                    if hasattr(dhw_system, 'heat_rejection') and dhw_system.heat_rejection:
                        # Merge DHW heat rejection into total
                        for carrier, heat_series in dhw_system.heat_rejection.items():
                            if carrier in heat_rejection_data:
                                heat_rejection_data[carrier] = heat_rejection_data[carrier] + heat_series
                            else:
                                heat_rejection_data[carrier] = heat_series
                        supply_systems_list.append(dhw_system)

        results[building_id] = {
            'supply_systems': supply_systems_list,  # Changed to plural to match extraction logic
            'building': building_obj,
            'heat_rejection': heat_rejection_data,
            'is_network': False
        }

    return results


def create_dhw_heat_rejection_system(locator, building, main_supply_system):
    """
    Create DHW supply system to extract heat rejection.

    Reuses helper functions from supply_costs module to ensure consistency.
    DHW is a separate service with its own heat rejection that must be tracked.

    :param locator: InputLocator instance
    :param building: Building instance
    :param main_supply_system: Main supply system (heating or cooling)
    :return: DHW SupplySystem instance or None
    """
    import pandas as pd
    import cea.config
    from cea.optimization_new.containerclasses.supplySystemStructure import SupplySystemStructure
    from cea.optimization_new.supplySystem import SupplySystem
    from cea.optimization_new.containerclasses.energyFlow import EnergyFlow
    from cea.optimization_new.domain import Domain
    from cea.optimization_new.component import Component
    from cea.analysis.costs.supply_costs import get_dhw_component_fallback

    try:
        # Read building's DHW supply code from supply.csv
        supply_systems_df = pd.read_csv(locator.get_building_supply())
        building_supply = supply_systems_df[supply_systems_df['name'] == building.identifier]

        if building_supply.empty:
            return None

        dhw_supply_code = building_supply.get('type_dhw') or building_supply.get('supply_type_dhw')
        if dhw_supply_code is None or (hasattr(dhw_supply_code, 'empty') and dhw_supply_code.empty):
            return None

        # Extract value if Series
        if hasattr(dhw_supply_code, 'values'):
            dhw_supply_code = dhw_supply_code.values[0]

        # Read SUPPLY_HOTWATER assembly to get feedstock
        dhw_assemblies_path = locator.get_database_assemblies_supply_hot_water()
        if not pd.io.common.file_exists(dhw_assemblies_path):
            return None

        dhw_assemblies_df = pd.read_csv(dhw_assemblies_path)
        dhw_assembly = dhw_assemblies_df[dhw_assemblies_df['code'] == dhw_supply_code]

        if dhw_assembly.empty:
            return None

        feedstock = dhw_assembly['feedstock'].values[0]

        # Skip if feedstock is NONE (no DHW system)
        if not feedstock or pd.isna(feedstock) or str(feedstock).upper() == 'NONE':
            return None

        # REUSE helper from supply_costs - get fallback component code based on feedstock
        component_code = get_dhw_component_fallback(locator, building.identifier, feedstock)
        if not component_code:
            return None

        # Get DHW demand profile from building's demand file
        building_demand_file = locator.get_demand_results_file(building.identifier)
        if not pd.io.common.file_exists(building_demand_file):
            return None

        hourly_demand_df = pd.read_csv(building_demand_file)
        if 'Qww_sys_kWh' not in hourly_demand_df.columns:
            return None

        dhw_demand_profile = hourly_demand_df['Qww_sys_kWh']

        # Skip if zero demand
        if dhw_demand_profile.max() == 0:
            return None

        # Create DHW demand flow (uses T60W energy carrier for medium-temperature DHW)
        dhw_demand_flow = EnergyFlow(
            input_category='primary',
            output_category='consumer',
            energy_carrier_code='T60W',
            energy_flow_profile=dhw_demand_profile
        )

        # Initialize Component class if not already done
        if Component.code_to_class_mapping is None:
            domain_config_dhw = cea.config.Configuration()
            domain_config_dhw.scenario = locator.scenario
            temp_domain = Domain(domain_config_dhw, locator)
            Component.initialize_class_variables(temp_domain)

        # Build supply system with fallback component
        max_dhw_flow = dhw_demand_flow.isolate_peak()
        user_component_selection = {
            'primary': [component_code],
            'secondary': [],
            'tertiary': []
        }

        # Build system structure
        system_structure = SupplySystemStructure(
            max_supply_flow=max_dhw_flow,
            available_potentials={},
            user_component_selection=user_component_selection,
            target_building_or_network=building.identifier + '_dhw'
        )
        system_structure.build()

        # Create and evaluate DHW supply system
        dhw_supply_system = SupplySystem(
            system_structure,
            system_structure.capacity_indicators,
            dhw_demand_flow
        )
        dhw_supply_system.evaluate()

        return dhw_supply_system

    except Exception as e:
        print(f"    ⚠ {building.identifier}: Failed to create DHW heat rejection system - {e}")
        return None


def calculate_network_heat_rejection(locator, config, network_type, network_name, standalone_results):
    """
    Calculate heat rejection for district network central plant(s).

    REUSES supply_costs.calculate_district_network_costs() to ensure consistency,
    then extracts heat_rejection from the resulting supply system.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param network_type: 'DH' or 'DC'
    :param network_name: Network layout name
    :param standalone_results: Results from standalone calculations
    :return: dict with network heat rejection data or None if validation fails
    """
    import os
    import cea.config
    from cea.analysis.costs.supply_costs import calculate_district_network_costs
    from cea.optimization_new.domain import Domain

    # Validate network results exist
    nodes_file = locator.get_network_layout_nodes_shapefile(network_type, network_name)

    if not os.path.exists(nodes_file):
        print(f"  ⚠ Warning: Network layout not found for {network_type} network '{network_name}'")
        print(f"    Missing: {nodes_file}")
        return None

    # Read network nodes to find plants and connected buildings
    nodes_gdf = gpd.read_file(nodes_file)
    plant_nodes = nodes_gdf[nodes_gdf['type'].str.contains('PLANT', case=False, na=False)]

    if len(plant_nodes) == 0:
        print(f"  ⚠ Warning: No PLANT nodes found in {network_type} network '{network_name}'")
        return None

    print(f"  Network layout '{network_name}': {len(plant_nodes)} plant(s)")

    # Get buildings connected to this network
    consumer_nodes = nodes_gdf[nodes_gdf['type'] == 'CONSUMER']
    connected_building_ids = consumer_nodes['building'].dropna().unique().tolist()

    print(f"  Connected buildings: {len(connected_building_ids)}")

    if len(connected_building_ids) == 0:
        print(f"  ⚠ Warning: No buildings connected to {network_type} network")
        return None

    # REUSE cost module's network calculation
    # Load domain to get Building objects (required by calculate_district_network_costs)
    # Must match cost module's Domain loading (supply_costs.py:1686-1708)
    domain_config = cea.config.Configuration()
    domain_config.scenario = config.scenario
    domain_config.optimization_new.network_type = network_type

    # Set component priorities (same as cost module lines 1694-1703)
    if network_type == 'DC':
        domain_config.optimization_new.cooling_components = config.system_costs.cooling_components if config.system_costs.cooling_components else []
        domain_config.optimization_new.heating_components = []  # No heating for DC
        domain_config.optimization_new.heat_rejection_components = config.system_costs.heat_rejection_components if config.system_costs.heat_rejection_components else []
    else:  # DH
        domain_config.optimization_new.cooling_components = []  # No cooling for DH
        domain_config.optimization_new.heating_components = config.system_costs.heating_components if config.system_costs.heating_components else []
        domain_config.optimization_new.heat_rejection_components = []  # No heat rejection for DH

    domain = Domain(domain_config, locator)
    # IMPORTANT: Only load network-connected buildings (same as cost module line 1708)
    domain.load_buildings(buildings_in_domain=connected_building_ids)

    if len(domain.buildings) == 0:
        print("  ⚠ No buildings with demand found")
        return None

    # Load potentials and initialize classes (same as cost module lines 1710-1720)
    # Suppress optimization messages about missing potentials
    import sys
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        domain.load_potentials()
        domain._initialize_energy_system_descriptor_classes()
    finally:
        sys.stdout = old_stdout

    # Collect building objects and potentials
    from cea.optimization_new.building import Building
    building_energy_potentials = Building.distribute_building_potentials(
        domain.energy_potentials, domain.buildings
    )
    network_buildings = domain.buildings
    domain_potentials = domain.energy_potentials

    # REUSE calculate_district_network_costs from cost module
    print("  Calculating network supply system using cost module...")
    try:
        # Create a new config for system-costs with our anthropogenic_heat parameters
        # This avoids parameter access errors when calculate_district_network_costs reads config.system_costs.*
        cost_config_for_network = cea.config.Configuration()
        cost_config_for_network.scenario = config.scenario
        cost_config_for_network.system_costs.network_name = network_name
        cost_config_for_network.system_costs.network_type = [network_type]

        # Map anthropogenic_heat parameters to system_costs parameters
        cost_config_for_network.system_costs.supply_type_cs = config.system_costs.supply_type_cs
        cost_config_for_network.system_costs.supply_type_hs = config.system_costs.supply_type_hs
        cost_config_for_network.system_costs.supply_type_dhw = config.system_costs.supply_type_dhw
        cost_config_for_network.system_costs.cooling_components = config.system_costs.cooling_components
        cost_config_for_network.system_costs.heating_components = config.system_costs.heating_components
        cost_config_for_network.system_costs.heat_rejection_components = config.system_costs.heat_rejection_components
        cost_config_for_network.system_costs.available_feedstocks = config.system_costs.available_feedstocks

        network_costs = calculate_district_network_costs(
            locator, cost_config_for_network, network_type, network_name,
            network_buildings, building_energy_potentials, domain_potentials
        )

        if not network_costs:
            print("  ⚠ Network cost calculation returned empty")
            return None

        # Extract supply system from cost results
        network_id = f'{network_name}_{network_type}'
        if network_id not in network_costs or 'supply_system' not in network_costs[network_id]:
            print("  ⚠ No supply system in network costs")
            return None

        plant_supply_system = network_costs[network_id]['supply_system']

    except Exception as e:
        print(f"  ⚠ Error calculating network costs: {e}")
        import traceback
        traceback.print_exc()
        return None

    # Extract total heat rejection from network supply system
    total_heat_rejection = plant_supply_system.heat_rejection  # Dict[str, pd.Series]

    # Calculate totals
    annual_total = sum([heat_series.sum() for heat_series in total_heat_rejection.values()])

    # Combine all carriers into single time series for peak calculation
    if len(total_heat_rejection) > 0:
        combined_hourly = pd.concat(list(total_heat_rejection.values()), axis=1).sum(axis=1)
        peak_kw = combined_hourly.max()
        peak_datetime = combined_hourly.idxmax()
    else:
        combined_hourly = pd.Series([0] * 8760)
        peak_kw = 0
        peak_datetime = None

    print(f"  Total network heat rejection: {annual_total/1000:.1f} MWh/yr, Peak: {peak_kw:.1f} kW")

    # Handle multiple plants - split equally
    num_plants = len(plant_nodes)
    if num_plants > 1:
        print(f"  Multiple plants detected ({num_plants}), splitting heat rejection equally")

    plant_heat_annual = annual_total / num_plants
    plant_heat_hourly = combined_hourly / num_plants
    plant_peak = peak_kw / num_plants

    # Create entry for each plant
    plant_entries = []
    for idx, (_, plant_row) in enumerate(plant_nodes.iterrows(), start=1):
        plant_entries.append({
            'name': f'{network_name}_{network_type}_plant_{idx:03d}',
            'type': 'plant',
            'x_coord': plant_row.geometry.x,
            'y_coord': plant_row.geometry.y,
            'heat_rejection_annual_MWh': plant_heat_annual / 1000,  # Convert kWh to MWh
            'peak_heat_rejection_kW': plant_peak,
            'peak_datetime': peak_datetime,
            'scale': 'DISTRICT',
            'hourly_profile': plant_heat_hourly,  # For spatial output
            'heat_rejection_by_carrier': total_heat_rejection,  # For component breakdown
            'supply_system': plant_supply_system  # Include supply system for component extraction
        })

    return {
        'network_type': network_type,
        'network_name': network_name,
        'plants': plant_entries,
        'connected_buildings': connected_building_ids
    }


def merge_heat_rejection_results(locator, standalone_results, network_results, is_standalone_only):
    """
    Merge standalone and network heat rejection results using 4-case logic.

    4-Case Building Connectivity Logic:
    - Case 1: Standalone-only mode OR building not in any network → all services standalone
    - Case 2: Building in BOTH DC+DH networks → all services from district, zero standalone
    - Case 3: Building in DC only → cooling from district, heating/DHW standalone
    - Case 4: Building in DH only → heating/DHW from district, cooling standalone

    :param locator: InputLocator instance
    :param standalone_results: dict from calculate_standalone_heat_rejection
    :param network_results: dict from calculate_network_heat_rejection
    :param is_standalone_only: bool, if True all buildings are standalone (not used currently)
    :return: dict with merged results
    """
    merged = {
        'buildings': [],
        'components': []
    }

    # Collect buildings connected to networks by type
    dc_connected_buildings = set()
    dh_connected_buildings = set()
    if not is_standalone_only:
        for network_type, network_data in network_results.items():
            if network_type == 'DC':
                dc_connected_buildings.update(network_data['connected_buildings'])
            elif network_type == 'DH':
                dh_connected_buildings.update(network_data['connected_buildings'])

    # Process standalone buildings
    for building_id, data in standalone_results.items():
        # Determine connectivity case
        case = determine_building_case(
            building_id, dc_connected_buildings, dh_connected_buildings, is_standalone_only
        )

        # Filter heat rejection by case
        supply_systems = data.get('supply_systems', [])
        filtered_heat_rejection, filtered_supply_systems = filter_heat_by_case(
            data['heat_rejection'], supply_systems, case
        )

        # Case 2 (both networks): Skip building entirely - no standalone services
        if case == 2:
            continue

        if filtered_heat_rejection:
            # Calculate totals from filtered heat rejection
            annual_total = sum([heat_series.sum() for heat_series in filtered_heat_rejection.values()])

            if len(filtered_heat_rejection) > 0:
                combined_hourly = pd.concat(list(filtered_heat_rejection.values()), axis=1).sum(axis=1)
                peak_kw = combined_hourly.max()
                peak_datetime = combined_hourly.idxmax()
            else:
                combined_hourly = pd.Series([0] * 8760)
                peak_kw = 0
                peak_datetime = None

            # Get building coordinates from zone geometry
            x_coord, y_coord = get_building_coordinates_from_geometry(building_id, locator)

            merged['buildings'].append({
                'name': building_id,
                'type': 'building',
                'x_coord': x_coord,
                'y_coord': y_coord,
                'heat_rejection_annual_MWh': annual_total / 1000,
                'peak_heat_rejection_kW': peak_kw,
                'peak_datetime': peak_datetime,
                'scale': 'BUILDING',
                'case': case,  # NEW: Track which case applies
                'case_description': get_case_description(case),  # NEW: Human-readable description
                'hourly_profile': combined_hourly,
                'heat_rejection_by_carrier': filtered_heat_rejection,
                'supply_systems': filtered_supply_systems
            })

    # Add network plants
    if not is_standalone_only:
        for network_type, network_data in network_results.items():
            for plant_entry in network_data['plants']:
                merged['buildings'].append(plant_entry)

    return merged


def get_building_coordinates_from_geometry(building_name, locator):
    """
    Extract building coordinates from zone geometry shapefile.

    :param building_name: Building name/ID
    :param locator: InputLocator instance
    :return: tuple (x_coord, y_coord)
    """
    import geopandas as gpd

    try:
        zone_geom_path = locator.get_zone_geometry()
        zone_geom = gpd.read_file(zone_geom_path).set_index('name')

        if building_name in zone_geom.index:
            centroid = zone_geom.loc[building_name].geometry.centroid
            return centroid.x, centroid.y
        else:
            print(f"      Warning: Building {building_name} not found in zone geometry, using (0.0, 0.0)")
            return 0.0, 0.0
    except Exception as e:
        print(f"      Warning: Could not extract coordinates for {building_name}: {e}")
        return 0.0, 0.0


def extract_component_heat_rejection(supply_system, building_name, building_type, scale):
    """
    Extract heat rejection details from a SupplySystem, showing breakdown by component.

    :param supply_system: SupplySystem instance
    :param building_name: name of building or plant
    :param building_type: 'building' or 'plant'
    :param scale: 'BUILDING' or 'DISTRICT'
    :return: list of component dictionaries
    """
    component_details = []

    # List installed components with their capacities
    for placement, components_dict in supply_system.installed_components.items():
        for component_code, component in components_dict.items():
            component_details.append({
                'name': building_name,
                'type': building_type,
                'component_code': component_code,
                'component_type': component.__class__.__name__,
                'placement': placement,
                'capacity_kW': component.capacity,
                'scale': scale
            })

    # Add heat rejection totals by carrier (from system-level tracking)
    # Note: Heat rejection is tracked at system level, not per component
    for carrier_code, heat_series in supply_system.heat_rejection.items():
        annual_MWh = heat_series.sum() / 1000  # kWh to MWh
        peak_kW = heat_series.max()

        if annual_MWh > 0.001:  # Only include significant values
            component_details.append({
                'name': building_name,
                'type': building_type,
                'component_code': carrier_code,
                'component_type': 'energy_carrier',
                'placement': 'heat_rejection',
                'capacity_kW': 0.0,
                'heat_rejection_annual_MWh': annual_MWh,
                'peak_heat_rejection_kW': peak_kW,
                'scale': scale
            })

    return component_details


def save_heat_rejection_outputs(locator, results, is_standalone_only, network_name=None):
    """
    Save heat rejection results to CSV files.

    Outputs:
    - heat_rejection_buildings.csv: Summary by building/plant
    - heat_rejection_components.csv: Detailed component breakdown
    - heat_rejection_hourly_spatial.csv: Hourly profiles with coordinates

    :param locator: InputLocator instance
    :param results: Merged results dict
    :param is_standalone_only: bool
    :param network_name: Network layout name for subfolder organization
    """
    # Clean up existing results folder for this network (if it exists)
    import shutil
    output_file = locator.get_heat_rejection_buildings(network_name=network_name)
    output_folder = os.path.dirname(output_file)

    if os.path.exists(output_folder):
        print(f"  Cleaning up existing results: {output_folder}")
        shutil.rmtree(output_folder)

    # 1. Buildings summary file
    buildings_df = pd.DataFrame(results['buildings'])

    if not buildings_df.empty:
        # Add GFA_m2 from building properties
        try:
            building_properties = pd.read_csv(locator.get_zone_geometry())
            building_properties = building_properties.set_index('Name')

            # Add GFA_m2 column (None for plants)
            gfa_values = []
            for _, row in buildings_df.iterrows():
                if row['type'] == 'building' and row['name'] in building_properties.index:
                    gfa_values.append(building_properties.loc[row['name'], 'GFA_m2'])
                else:
                    gfa_values.append(None)
            buildings_df['GFA_m2'] = gfa_values
        except Exception as e:
            print(f"  Warning: Could not read GFA_m2 from building properties: {e}")
            buildings_df['GFA_m2'] = None

        # Reorder columns (include GFA_m2 and case if present)
        columns_order = [
            'name', 'type', 'GFA_m2', 'x_coord', 'y_coord',
            'heat_rejection_annual_MWh', 'peak_heat_rejection_kW',
            'peak_datetime', 'scale'
        ]

        # Add case and case_description if present (for debugging)
        if 'case' in buildings_df.columns:
            columns_order.append('case')
        if 'case_description' in buildings_df.columns:
            columns_order.append('case_description')

        # Only include columns that exist
        columns_order = [col for col in columns_order if col in buildings_df.columns]
        buildings_output = buildings_df[columns_order].copy()

        # Save
        output_file = locator.get_heat_rejection_buildings(network_name=network_name)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        buildings_output.to_csv(output_file, index=False, float_format='%.2f')
        print(f"  ✓ Saved buildings summary: {output_file}")

    # 2. Individual hourly files per building/plant (similar to demand)
    # Create timestamps for 8760 hours (non-leap year)
    timestamps = pd.date_range('2020-01-01', periods=8760, freq='H')

    for building_data in results['buildings']:
        building_name = building_data['name']
        hourly_profile = building_data['hourly_profile']

        # Ensure exactly 8760 hours (remove leap day if present)
        if len(hourly_profile) > 8760:
            # Remove Feb 29 (day 60, hours 1416-1439 in leap year)
            hourly_profile = remove_leap_day(hourly_profile)

        # Create DataFrame with DATE and heat_rejection_kW columns
        entity_df = pd.DataFrame({
            'date': timestamps,
            'heat_rejection_kW': hourly_profile[:8760]  # Ensure exactly 8760 values
        })

        # Save individual file
        output_file = locator.get_heat_rejection_hourly_building(building_name, network_name=network_name)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        entity_df.to_csv(output_file, index=False, float_format='%.2f')

    print(f"  ✓ Saved {len(results['buildings'])} individual hourly files")

    # 3. Components detailed file - detailed breakdown by individual component
    component_rows = []
    buildings_with_systems = 0
    for building_data in results['buildings']:
        building_name = building_data['name']
        building_type = building_data['type']
        scale = building_data['scale']

        # Handle both old single supply_system and new supply_systems list
        supply_systems = building_data.get('supply_systems', [])
        if not supply_systems:
            # Fallback to single supply_system (for network plants)
            supply_system = building_data.get('supply_system')
            if supply_system:
                supply_systems = [supply_system]

        if supply_systems:
            buildings_with_systems += 1
            # Extract component-level details from ALL supply systems
            for supply_system in supply_systems:
                component_details = extract_component_heat_rejection(
                    supply_system, building_name, building_type, scale
                )
                component_rows.extend(component_details)

    print(f"  Extracted components from {buildings_with_systems} buildings/plants")

    if component_rows:
        components_df = pd.DataFrame(component_rows)
        # Reorder columns for better readability (only include columns that exist)
        desired_order = [
            'name', 'type', 'component_code', 'component_type', 'placement',
            'capacity_kW', 'heat_rejection_annual_MWh', 'peak_heat_rejection_kW', 'scale'
        ]
        columns_order = [col for col in desired_order if col in components_df.columns]
        components_df = components_df[columns_order]
        output_file = locator.get_heat_rejection_components(network_name=network_name)
        components_df.to_csv(output_file, index=False, float_format='%.2f')
        print(f"  ✓ Saved components breakdown ({len(component_rows)} rows): {output_file}")
    else:
        # Create empty placeholder
        components_df = pd.DataFrame()
        output_file = locator.get_heat_rejection_components(network_name=network_name)
        components_df.to_csv(output_file, index=False, float_format='%.2f')
        print(f"  ✓ Saved components (empty): {output_file}")


def determine_building_case(building_id, dc_connected_buildings, dh_connected_buildings, is_standalone_only):
    """
    Determine which of the 4 connectivity cases applies to this building.

    Case 1: Standalone-only mode OR building not in any network - all services standalone
    Case 2: Building in BOTH DC+DH networks - all services from district, zero standalone
    Case 3: Building in DC only - cooling from district, heating/DHW standalone
    Case 4: Building in DH only - heating/DHW from district, cooling standalone

    :param building_id: Building identifier
    :param dc_connected_buildings: Set of building IDs in DC network
    :param dh_connected_buildings: Set of building IDs in DH network
    :param is_standalone_only: Boolean, True if network_name = "(none)"
    :return: Integer case number (1, 2, 3, or 4)
    """
    if is_standalone_only:
        return 1

    is_in_dc = building_id in dc_connected_buildings
    is_in_dh = building_id in dh_connected_buildings

    if is_in_dc and is_in_dh:
        return 2  # Both networks - all from district
    elif is_in_dc and not is_in_dh:
        return 3  # DC only - cooling from district, heating/DHW standalone
    elif is_in_dh and not is_in_dc:
        return 4  # DH only - heating/DHW from district, cooling standalone
    else:
        return 1  # Not in any network - same as standalone-only


def filter_heat_by_case(heat_rejection_data, supply_systems, case):
    """
    Filter heat rejection based on building connectivity case.

    Uses service-based filtering by checking which supply systems provide which services,
    rather than fragile temperature-based heuristics.

    :param heat_rejection_data: Dict of {carrier_code: pd.Series(hourly_kWh)}
    :param supply_systems: List of SupplySystem objects
    :param case: Integer case number (1, 2, 3, or 4)
    :return: Tuple of (filtered_heat_rejection dict, filtered_supply_systems list)
    """
    if case == 1:
        # Standalone-only or not in network - include ALL heat rejection
        return heat_rejection_data, supply_systems

    elif case == 2:
        # Both networks - NO standalone services, return empty
        return {}, []

    elif case == 3:
        # DC only - keep only heating/DHW heat (high-temp services)
        return filter_by_service_temperature(heat_rejection_data, supply_systems,
                                             temp_prefixes=['T100', 'T90', 'T80', 'T60'])

    elif case == 4:
        # DH only - keep only cooling heat (low-temp service)
        return filter_by_service_temperature(heat_rejection_data, supply_systems,
                                             temp_prefixes=['T25', 'T20', 'T15'])

    return {}, []


def filter_by_service_temperature(heat_rejection_data, supply_systems, temp_prefixes):
    """
    Filter heat rejection by temperature prefix to identify service type.

    This is a transitional implementation using temperature heuristics.
    Future enhancement: Extract explicit service metadata from SupplySystem objects.

    :param heat_rejection_data: Dict of {carrier_code: pd.Series}
    :param supply_systems: List of SupplySystem objects
    :param temp_prefixes: List of temperature prefixes to match (e.g., ['T100', 'T90'])
    :return: Tuple of (filtered_heat dict, filtered_systems list)
    """
    filtered_heat = {}
    filtered_systems = []

    for system in supply_systems:
        if hasattr(system, 'heat_rejection') and system.heat_rejection:
            system_has_match = False

            for carrier, heat_series in system.heat_rejection.items():
                # Check if carrier matches any of the temperature prefixes
                if any(prefix in carrier for prefix in temp_prefixes):
                    if carrier in filtered_heat:
                        filtered_heat[carrier] = filtered_heat[carrier] + heat_series
                    else:
                        filtered_heat[carrier] = heat_series
                    system_has_match = True

            if system_has_match and system not in filtered_systems:
                filtered_systems.append(system)

    return filtered_heat, filtered_systems


def get_case_description(case):
    """
    Get human-readable description of connectivity case.

    :param case: Integer case number (1, 2, 3, or 4)
    :return: String description
    """
    descriptions = {
        1: "Standalone (all services)",
        2: "Both DC+DH (no standalone)",
        3: "DC only (standalone heating/DHW)",
        4: "DH only (standalone cooling)"
    }
    return descriptions.get(case, "Unknown")


def apply_heat_rejection_config_fallback(locator, building_id, is_in_dc, is_in_dh, config):
    """
    Level 1 fallback: Replace DISTRICT-scale codes with BUILDING-scale from config
    for standalone services.

    Mirrors supply_costs.apply_supply_code_fallback_for_standalone()

    This ensures buildings providing standalone services don't use DISTRICT-scale
    assemblies from supply.csv. Instead, use BUILDING-scale from config parameters.

    :param locator: InputLocator instance
    :param building_id: Building identifier
    :param is_in_dc: Boolean - building in DC network
    :param is_in_dh: Boolean - building in DH network
    :param config: Configuration instance
    :return: Dict of fallback supply codes {service: code} or empty dict if no fallback needed
    """
    from cea.analysis.costs.supply_costs import filter_supply_code_by_scale

    # Read building's supply.csv
    supply_df = pd.read_csv(locator.get_building_supply())
    building_supply = supply_df[supply_df['name'] == building_id]

    if building_supply.empty:
        return {}

    building_supply = building_supply.iloc[0]
    fallbacks = {}

    # Helper to get scale of a supply code
    def get_scale(supply_code):
        """
        Extract scale from supply code by reading the SUPPLY assembly database.

        :param supply_code: Supply assembly code (e.g., 'SUPPLY_COOLING_AS1')
        :return: 'BUILDING', 'DISTRICT', or None
        """
        if not supply_code or pd.isna(supply_code):
            return None

        # Determine assembly category from code
        code_str = str(supply_code).upper()
        if 'COOLING' in code_str:
            assembly_file = 'SUPPLY_COOLING.csv'
        elif 'HEATING' in code_str:
            assembly_file = 'SUPPLY_HEATING.csv'
        elif 'HOTWATER' in code_str or 'DHW' in code_str:
            assembly_file = 'SUPPLY_HOTWATER.csv'
        elif 'ELECTRICITY' in code_str:
            assembly_file = 'SUPPLY_ELECTRICITY.csv'
        else:
            return None

        # Read from database to get scale
        try:
            import os
            database_path = locator.get_databases_assemblies_folder()
            supply_file = os.path.join(database_path, 'SUPPLY', assembly_file)

            if os.path.exists(supply_file):
                supply_db = pd.read_csv(supply_file)
                # Match by code column (e.g., 'SUPPLY_COOLING_AS1')
                match = supply_db[supply_db['code'] == supply_code]
                if not match.empty:
                    scale = match.iloc[0].get('scale', None)
                    if scale:
                        return scale.upper()
        except (IOError, KeyError, pd.errors.EmptyDataError):
            # Database file not found, missing columns, or empty file
            pass

        return None

    # Check services building provides standalone
    if not is_in_dc:
        # Cooling is standalone
        csv_code = building_supply.get('type_cs')
        if csv_code and get_scale(csv_code) == 'DISTRICT':
            # Try to replace with BUILDING-scale from config
            building_scale_code = filter_supply_code_by_scale(
                locator, config.anthropogenic_heat.supply_type_cs,
                'SUPPLY_COOLING', is_standalone=True
            )
            if building_scale_code:
                fallbacks['type_cs'] = building_scale_code

    if not is_in_dh:
        # Heating is standalone
        csv_code = building_supply.get('type_hs')
        if csv_code and get_scale(csv_code) == 'DISTRICT':
            building_scale_code = filter_supply_code_by_scale(
                locator, config.anthropogenic_heat.supply_type_hs,
                'SUPPLY_HEATING', is_standalone=True
            )
            if building_scale_code:
                fallbacks['type_hs'] = building_scale_code

        # DHW is standalone
        csv_code = building_supply.get('type_dhw')
        if csv_code and get_scale(csv_code) == 'DISTRICT':
            building_scale_code = filter_supply_code_by_scale(
                locator, config.anthropogenic_heat.supply_type_dhw,
                'SUPPLY_HOTWATER', is_standalone=True
            )
            if building_scale_code:
                fallbacks['type_dhw'] = building_scale_code

    return fallbacks

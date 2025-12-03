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
import os
import pandas as pd
import geopandas as gpd
from cea.optimization_new.domain import Domain
from cea.optimization_new.supplySystem import SupplySystem

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
    network_name = config.anthropogenic_heat.network_name
    network_types = config.anthropogenic_heat.network_type

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
        print(f"Mode: NETWORK + STANDALONE")
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
            print(f"\n-" * 70)
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

    save_heat_rejection_outputs(locator, all_results, is_standalone_only)

    print("\n" + "=" * 70)
    if is_standalone_only:
        print("COMPLETED (Standalone Mode)")
    else:
        print("COMPLETED")
    print("=" * 70)
    print(f"Summary: {locator.get_heat_rejection_buildings()}")
    print(f"Detailed: {locator.get_heat_rejection_components()}")
    print(f"Spatial: {locator.get_heat_rejection_hourly_spatial()}")


def calculate_standalone_heat_rejection(locator, config, network_types):
    """
    Calculate heat rejection for all buildings using building-scale systems.

    This is a twin of supply_costs.py - it reuses the same supply system calculation
    but extracts heat_rejection instead of costs from the SupplySystem objects.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param network_types: List of network types ['DH', 'DC']
    :return: dict of {building_id: heat_rejection_data}
    """
    import cea.config
    from cea.analysis.costs.supply_costs import calculate_all_buildings_as_standalone

    # Create a config that maps anthropogenic_heat parameters to system_costs parameters
    # This allows us to reuse the supply_costs functions
    from cea.analysis.costs.supply_costs import filter_supply_code_by_scale

    cost_config = cea.config.Configuration()
    cost_config.scenario = config.scenario
    cost_config.system_costs.network_name = None  # Force standalone mode
    cost_config.system_costs.network_type = network_types

    # Filter supply codes to building-scale only for standalone calculations
    cost_config.system_costs.supply_type_cs = filter_supply_code_by_scale(
        locator, config.anthropogenic_heat.supply_type_cs, 'SUPPLY_COOLING', is_standalone=True
    )
    cost_config.system_costs.supply_type_hs = filter_supply_code_by_scale(
        locator, config.anthropogenic_heat.supply_type_hs, 'SUPPLY_HEATING', is_standalone=True
    )
    cost_config.system_costs.supply_type_dhw = filter_supply_code_by_scale(
        locator, config.anthropogenic_heat.supply_type_dhw, 'SUPPLY_HOTWATER', is_standalone=True
    )

    # Reuse supply_costs function to create supply systems
    # This returns {network_type: {building_name: {supply_system, building, costs, ...}}}
    # NOTE: calculate_all_buildings_as_standalone puts ALL buildings under 'DH' key (with complete systems)
    # The 'DC' key is empty - this is expected behaviour from supply_costs
    cost_results = calculate_all_buildings_as_standalone(locator, cost_config, network_types)

    # Extract building data from 'DH' key (contains all buildings with all their supply systems)
    # calculate_all_buildings_as_standalone already merged DH and DC domains internally
    building_cost_results = cost_results.get('DH', {})

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
                from cea.analysis.costs.supply_costs import apply_dhw_component_fallback
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
    Create DHW supply system to extract heat rejection (mirrors apply_dhw_component_fallback).

    This is needed because DHW is a separate service with its own heat rejection.
    The main building supply system only has cooling OR heating, not DHW.

    :param locator: InputLocator instance
    :param building: Building instance
    :param main_supply_system: Main supply system (heating or cooling)
    :return: DHW SupplySystem instance or None
    """
    from cea.analysis.costs.supply_costs import apply_dhw_component_fallback

    # Use the same DHW fallback logic from supply_costs
    # This creates a complete DHW supply system with heat rejection tracking
    try:
        dhw_system = apply_dhw_component_fallback(locator, building, main_supply_system)

        # apply_dhw_component_fallback returns costs dict, not the supply system
        # We need to recreate the DHW supply system to get heat rejection
        # Actually, we need a different approach - let's directly call the DHW system creation

        # Import the necessary modules
        import pandas as pd
        from cea.optimization_new.containerclasses.supplySystemStructure import SupplySystemStructure
        from cea.optimization_new.supplySystem import SupplySystem
        from cea.optimization_new.containerclasses.energyFlow import EnergyFlow
        from cea.optimization_new.domain import Domain
        from cea.optimization_new.component import Component
        from cea.analysis.costs.supply_costs import get_dhw_component_fallback
        import cea.config

        # Read building's DHW supply system code from supply.csv
        supply_systems_df = pd.read_csv(locator.get_building_supply())
        building_supply = supply_systems_df[supply_systems_df['name'] == building.identifier]

        if building_supply.empty or 'supply_type_dhw' not in building_supply.columns:
            return None

        dhw_supply_code = building_supply['supply_type_dhw'].values[0]

        # Read SUPPLY_HOTWATER.csv to get feedstock
        dhw_assemblies_path = locator.get_database_assemblies_supply_hot_water()
        if not pd.io.common.file_exists(dhw_assemblies_path):
            return None

        dhw_assemblies_df = pd.read_csv(dhw_assemblies_path)
        dhw_assembly = dhw_assemblies_df[dhw_assemblies_df['code'] == dhw_supply_code]

        if dhw_assembly.empty:
            return None

        feedstock = dhw_assembly['feedstock'].values[0]

        # Skip if feedstock is NONE (no DHW system)
        if not feedstock or feedstock == 'NONE':
            return None

        # Get fallback component code based on feedstock
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

        # Create DHW demand flow
        dhw_demand_flow = EnergyFlow(
            input_category='primary',
            output_category='consumer',
            energy_carrier_code='T60W',  # Medium temperature for DHW
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

    Handles multiple plants by splitting heat equally across all plant nodes.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param network_type: 'DH' or 'DC'
    :param network_name: Network layout name
    :param standalone_results: Results from standalone calculations
    :return: dict with network heat rejection data or None if validation fails
    """
    # Validate network results exist
    nodes_file = locator.get_network_layout_nodes_shapefile(network_type, network_name)

    if not os.path.exists(nodes_file):
        print(f"  ⚠ Warning: Network layout not found for {network_type} network '{network_name}'")
        print(f"    Missing: {nodes_file}")
        return None

    # Read network nodes to find plants
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

    # Calculate central plant heat rejection using config supply types
    # This creates a single supply system representing the entire network capacity
    plant_supply_system = create_network_supply_system(
        locator, config, network_type, network_name, connected_building_ids, standalone_results
    )

    if plant_supply_system is None:
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


def create_network_supply_system(locator, config, network_type, network_name,
                                 connected_building_ids, standalone_results):
    """
    Create supply system for district network central plant.

    Reuses logic from supply_costs.py but focused on heat rejection extraction.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param network_type: 'DH' or 'DC'
    :param network_name: Network layout name
    :param connected_building_ids: List of building IDs connected to network
    :param standalone_results: Results from standalone calculations (for building potentials)
    :return: SupplySystem instance or None
    """
    from cea.optimization_new.containerclasses.supplySystemStructure import SupplySystemStructure
    from cea.optimization_new.containerclasses.energyFlow import EnergyFlow
    import cea.config

    print(f"    Creating {network_type} network supply system...")
    from cea.analysis.costs.supply_costs import filter_supply_code_by_scale
    # Get supply type from config (reuse system-costs parameters)
    if network_type == 'DC':
        supply_code_raw = config.anthropogenic_heat.supply_type_cs
        # Filter for district scale

        supply_code = filter_supply_code_by_scale(
            locator, supply_code_raw, 'SUPPLY_COOLING', is_standalone=False
        )
    else:  # DH
        supply_code_raw = config.anthropogenic_heat.supply_type_hs
        supply_code = filter_supply_code_by_scale(
            locator, supply_code_raw, 'SUPPLY_HEATING', is_standalone=False
        )

    if not supply_code or supply_code == "Custom (use component settings below)":
        # Use component selection from config parameters
        print(f"      Using COMPONENT selection for {network_type} network")
        user_components = get_user_component_selection(config, network_type)
    else:
        # Extract components from SUPPLY assembly
        print(f"      Using SUPPLY assembly: {supply_code}")
        from cea.analysis.costs.supply_costs import get_components_from_supply_assembly

        if network_type == 'DC':
            category = 'SUPPLY_COOLING'
        else:
            category = 'SUPPLY_HEATING'

        user_components = get_components_from_supply_assembly(locator, supply_code, category)

    # Calculate total network demand from connected buildings
    total_demand_profile = calculate_network_demand_profile(
        locator, connected_building_ids, network_type
    )

    if total_demand_profile is None or total_demand_profile.max() == 0:
        print(f"      ⚠ Zero demand for {network_type} network")
        return None

    # Create demand flow
    if network_type == 'DC':
        energy_carrier = 'T10W'  # Chilled water (10°C)
    else:  # DH
        energy_carrier = 'T30W'  # Hot water (30°C)

    demand_flow = EnergyFlow(
        input_category='primary',
        output_category='consumer',
        energy_carrier_code=energy_carrier,
        energy_flow_profile=total_demand_profile
    )

    # Get building potentials for network (solar, etc.)
    building_potentials = {}
    for building_id in connected_building_ids:
        if building_id in standalone_results:
            building = standalone_results[building_id]['building']
            if building and hasattr(building, 'potentials'):
                building_potentials[building_id] = building.potentials

    # Create supply system structure
    max_demand_flow = demand_flow.isolate_peak()

    try:
        system_structure = SupplySystemStructure(
            max_supply_flow=max_demand_flow,
            available_potentials=building_potentials,
            user_component_selection=user_components,
            target_building_or_network=f'{network_name}_{network_type}'
        )
        system_structure.build()

        # Create and evaluate supply system
        supply_system = SupplySystem(
            system_structure,
            system_structure.capacity_indicators,
            demand_flow
        )

        supply_system.evaluate()

        return supply_system

    except Exception as e:
        print(f"      ⚠ Error creating {network_type} network supply system: {e}")
        return None


def get_user_component_selection(config, network_type):
    """
    Get user component selection from config parameters.

    :param config: Configuration instance
    :param network_type: 'DH' or 'DC'
    :return: dict with component categories
    """
    if network_type == 'DC':
        return {
            'primary': config.anthropogenic_heat.cooling_components,
            'secondary': [],
            'tertiary': config.anthropogenic_heat.heat_rejection_components
        }
    else:  # DH
        return {
            'primary': config.anthropogenic_heat.heating_components,
            'secondary': [],
            'tertiary': []
        }


def calculate_network_demand_profile(locator, connected_building_ids, network_type):
    """
    Calculate total demand profile for network from connected buildings.

    :param locator: InputLocator instance
    :param connected_building_ids: List of building IDs
    :param network_type: 'DH' or 'DC'
    :return: pd.Series with hourly demand (8760 values) or None
    """
    total_demand = None

    for building_id in connected_building_ids:
        demand_file = locator.get_demand_results_file(building_id)
        if not os.path.exists(demand_file):
            continue

        demand_df = pd.read_csv(demand_file)

        if network_type == 'DC':
            column = 'Qcs_sys_kWh'
        else:  # DH - include both heating and DHW
            if 'Qhs_sys_kWh' in demand_df.columns and 'Qww_sys_kWh' in demand_df.columns:
                building_demand = demand_df['Qhs_sys_kWh'] + demand_df['Qww_sys_kWh']
            elif 'Qhs_sys_kWh' in demand_df.columns:
                building_demand = demand_df['Qhs_sys_kWh']
            else:
                continue
            column = None  # Already calculated above

        if column:
            if column not in demand_df.columns:
                continue
            building_demand = demand_df[column]

        if total_demand is None:
            total_demand = building_demand.copy()
        else:
            total_demand += building_demand

    return total_demand


def merge_heat_rejection_results(locator, standalone_results, network_results, is_standalone_only):
    """
    Merge standalone and network heat rejection results.

    :param standalone_results: dict from calculate_standalone_heat_rejection
    :param network_results: dict from calculate_network_heat_rejection
    :param is_standalone_only: bool, if True all buildings are standalone
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
        # Determine what services this building provides standalone
        # - Buildings in DC network: Include only WW (DHW) heat rejection (cooling from district)
        # - Buildings in DH network: Include only cooling heat rejection (heating/DHW from district)
        # - Buildings in both networks: Skip completely (all services from district)
        # - Standalone buildings: Include ALL heat rejection

        is_in_dc = building_id in dc_connected_buildings
        is_in_dh = building_id in dh_connected_buildings

        # Skip buildings in BOTH networks (all services from district)
        if is_in_dc and is_in_dh:
            continue

        # Filter heat rejection by service type
        filtered_heat_rejection = {}
        filtered_supply_systems = []

        if data['heat_rejection']:
            # Get the supply systems to filter by service type
            supply_systems = data.get('supply_systems', [])

            if is_in_dc and not is_in_dh:
                # Building in DC network: Only include WW (DHW) heat rejection
                # Identify WW supply systems (boilers with T100A heat rejection)
                for system in supply_systems:
                    if hasattr(system, 'heat_rejection') and system.heat_rejection:
                        # Check if this system has high-temperature heat rejection (T100A from boilers = DHW)
                        for carrier, heat_series in system.heat_rejection.items():
                            if 'T100' in carrier or 'T90' in carrier or 'T80' in carrier:
                                # This is DHW heat rejection (high temperature from boilers)
                                if carrier in filtered_heat_rejection:
                                    filtered_heat_rejection[carrier] = filtered_heat_rejection[carrier] + heat_series
                                else:
                                    filtered_heat_rejection[carrier] = heat_series
                                if system not in filtered_supply_systems:
                                    filtered_supply_systems.append(system)

            elif is_in_dh and not is_in_dc:
                # Building in DH network: Only include cooling heat rejection (T25A from chillers)
                for system in supply_systems:
                    if hasattr(system, 'heat_rejection') and system.heat_rejection:
                        for carrier, heat_series in system.heat_rejection.items():
                            if 'T25' in carrier or 'T20' in carrier or 'T15' in carrier:
                                # This is cooling heat rejection (low temperature from chillers/cooling towers)
                                if carrier in filtered_heat_rejection:
                                    filtered_heat_rejection[carrier] = filtered_heat_rejection[carrier] + heat_series
                                else:
                                    filtered_heat_rejection[carrier] = heat_series
                                if system not in filtered_supply_systems:
                                    filtered_supply_systems.append(system)

            else:
                # Standalone building: Include ALL heat rejection
                filtered_heat_rejection = data['heat_rejection']
                filtered_supply_systems = supply_systems

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
                'hourly_profile': combined_hourly,
                'heat_rejection_by_carrier': filtered_heat_rejection,  # Use filtered data
                'supply_systems': filtered_supply_systems  # Include only filtered supply systems
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


def save_heat_rejection_outputs(locator, results, is_standalone_only):
    """
    Save heat rejection results to CSV files.

    Outputs:
    - heat_rejection_buildings.csv: Summary by building/plant
    - heat_rejection_components.csv: Detailed component breakdown
    - heat_rejection_hourly_spatial.csv: Hourly profiles with coordinates

    :param locator: InputLocator instance
    :param results: Merged results dict
    :param is_standalone_only: bool
    """
    # 1. Buildings summary file
    buildings_df = pd.DataFrame(results['buildings'])

    if not buildings_df.empty:
        # Reorder columns
        columns_order = [
            'name', 'type', 'x_coord', 'y_coord',
            'heat_rejection_annual_MWh', 'peak_heat_rejection_kW',
            'peak_datetime', 'scale'
        ]
        buildings_output = buildings_df[columns_order].copy()

        # Save
        output_file = locator.get_heat_rejection_buildings()
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        buildings_output.to_csv(output_file, index=False)
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
        output_file = locator.get_heat_rejection_hourly_building(building_name)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        entity_df.to_csv(output_file, index=False)

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
        output_file = locator.get_heat_rejection_components()
        components_df.to_csv(output_file, index=False)
        print(f"  ✓ Saved components breakdown ({len(component_rows)} rows): {output_file}")
    else:
        # Create empty placeholder
        components_df = pd.DataFrame()
        output_file = locator.get_heat_rejection_components()
        components_df.to_csv(output_file, index=False)
        print(f"  ✓ Saved components (empty): {output_file}")

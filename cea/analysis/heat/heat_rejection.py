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
        standalone_results, network_results, is_standalone_only
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

    This creates a Domain with all buildings and extracts heat_rejection from their
    stand_alone_supply_system.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param network_types: List of network types ['DH', 'DC']
    :return: dict of {building_id: heat_rejection_data}
    """
    print("  Loading buildings and demands...")

    # Create domain to load all buildings
    # Note: We pass network_types to config but don't use networks yet
    domain = Domain(config, locator)

    print(f"  Calculating building-level heat rejection for all buildings...")
    print(f"    ({len(domain.buildings)} total)")

    results = {}
    zero_demand_count = 0

    for building in domain.buildings:
        if building.stand_alone_supply_system is None:
            zero_demand_count += 1
            results[building.identifier] = {
                'supply_system': None,
                'building': building,
                'heat_rejection': {},
                'is_network': False
            }
        else:
            # Extract heat rejection from supply system
            supply_system = building.stand_alone_supply_system
            heat_rejection = supply_system.heat_rejection  # Dict[str, pd.Series]

            results[building.identifier] = {
                'supply_system': supply_system,
                'building': building,
                'heat_rejection': heat_rejection,
                'is_network': False
            }

    if zero_demand_count > 0:
        print(f"  ({zero_demand_count} building(s) with zero demand)")

    print("  ✓ Standalone heat rejection calculations completed")

    return results


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
    nodes_file = locator.get_network_layout_nodes_shapefile(network_name, network_type)

    if not os.path.exists(nodes_file):
        print(f"  ⚠ Warning: Network layout not found for {network_type} network '{network_name}'")
        print(f"    Missing: {nodes_file}")
        return None

    # Read network nodes to find plants
    nodes_gdf = gpd.read_file(nodes_file)
    plant_nodes = nodes_gdf[nodes_gdf['Type'].str.contains('PLANT', case=False, na=False)]

    if len(plant_nodes) == 0:
        print(f"  ⚠ Warning: No PLANT nodes found in {network_type} network '{network_name}'")
        return None

    print(f"  Network layout '{network_name}': {len(plant_nodes)} plant(s)")

    # Get buildings connected to this network
    consumer_nodes = nodes_gdf[nodes_gdf['Type'] == 'CONSUMER']
    connected_building_ids = consumer_nodes['Building'].dropna().unique().tolist()

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
            'heat_rejection_by_carrier': total_heat_rejection  # For component breakdown
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

    # Get supply type from config (reuse system-costs parameters)
    if network_type == 'DC':
        supply_code_raw = config.anthropogenic_heat.supply_type_cs
        # Filter for district scale
        from cea.analysis.costs.supply_costs import filter_supply_code_by_scale
        supply_code = filter_supply_code_by_scale(
            locator, supply_code_raw, 'SUPPLY_COOLING', is_standalone=False
        )
    else:  # DH
        supply_code_raw = config.anthropogenic_heat.supply_type_hs
        supply_code = filter_supply_code_by_scale(
            locator, supply_code_raw, 'SUPPLY_HEATING', is_standalone=False
        )

    if not supply_code or supply_code == "Custom (use component settings below)":
        # Use component selection
        print(f"      Using COMPONENT selection for {network_type} network")
        # Will be handled by SupplySystemStructure with user_component_selection
        user_components = get_user_component_selection(config, network_type)
    else:
        print(f"      Using SUPPLY assembly: {supply_code}")
        user_components = None  # Let assembly handle it

    # Calculate total network demand from connected buildings
    total_demand_profile = calculate_network_demand_profile(
        locator, connected_building_ids, network_type
    )

    if total_demand_profile is None or total_demand_profile.max() == 0:
        print(f"      ⚠ Zero demand for {network_type} network")
        return None

    # Create demand flow
    if network_type == 'DC':
        energy_carrier = 'T12W'  # Chilled water
    else:  # DH
        energy_carrier = 'T80W'  # Hot water

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
            if building:
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


def merge_heat_rejection_results(standalone_results, network_results, is_standalone_only):
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

    # Process standalone buildings
    for building_id, data in standalone_results.items():
        if data['heat_rejection']:
            # Calculate totals
            annual_total = sum([heat_series.sum() for heat_series in data['heat_rejection'].values()])

            if len(data['heat_rejection']) > 0:
                combined_hourly = pd.concat(list(data['heat_rejection'].values()), axis=1).sum(axis=1)
                peak_kw = combined_hourly.max()
                peak_datetime = combined_hourly.idxmax()
            else:
                combined_hourly = pd.Series([0] * 8760)
                peak_kw = 0
                peak_datetime = None

            # Get building geometry for coordinates
            building = data['building']
            x_coord, y_coord = get_building_coordinates(building)

            merged['buildings'].append({
                'name': building_id,
                'type': 'building',
                'x_coord': x_coord,
                'y_coord': y_coord,
                'GFA_m2': building.GFA if building else 0,
                'heat_rejection_annual_MWh': annual_total / 1000,
                'peak_heat_rejection_kW': peak_kw,
                'peak_datetime': peak_datetime,
                'scale': 'BUILDING',
                'hourly_profile': combined_hourly,
                'heat_rejection_by_carrier': data['heat_rejection']
            })

    # Add network plants
    if not is_standalone_only:
        for network_type, network_data in network_results.items():
            for plant_entry in network_data['plants']:
                merged['buildings'].append(plant_entry)

    return merged


def get_building_coordinates(building):
    """
    Extract building coordinates from building object.

    :param building: Building instance from Domain
    :return: tuple (x_coord, y_coord)
    """
    try:
        if hasattr(building, 'geometry') and building.geometry:
            centroid = building.geometry.centroid
            return centroid.x, centroid.y
        elif hasattr(building, 'coordinates') and building.coordinates:
            return building.coordinates
        else:
            return 0.0, 0.0
    except:
        return 0.0, 0.0


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
            'name', 'type', 'GFA_m2', 'x_coord', 'y_coord',
            'heat_rejection_annual_MWh', 'peak_heat_rejection_kW',
            'peak_datetime', 'scale'
        ]
        buildings_output = buildings_df[columns_order].copy()

        # Save
        output_file = locator.get_heat_rejection_buildings()
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        buildings_output.to_csv(output_file, index=False)
        print(f"  ✓ Saved buildings summary: {output_file}")

    # 2. Hourly spatial file (for heatmaps)
    spatial_rows = []
    for building_data in results['buildings']:
        building_name = building_data['name']
        building_type = building_data['type']
        x = building_data['x_coord']
        y = building_data['y_coord']
        hourly_profile = building_data['hourly_profile']

        # Create one row per hour
        for hour_idx, heat_kw in enumerate(hourly_profile):
            # Create timestamp (assuming 2020 for now)
            timestamp = pd.Timestamp('2020-01-01') + pd.Timedelta(hours=hour_idx)
            spatial_rows.append({
                'name': building_name,
                'type': building_type,
                'x_coord': x,
                'y_coord': y,
                'DATE': timestamp,
                'Heat_rejection_kW': heat_kw
            })

    if spatial_rows:
        spatial_df = pd.DataFrame(spatial_rows)
        output_file = locator.get_heat_rejection_hourly_spatial()
        spatial_df.to_csv(output_file, index=False)
        print(f"  ✓ Saved hourly spatial: {output_file}")

    # 3. Components detailed file
    # TODO: Extract component-level breakdown from heat_rejection_by_carrier
    # For now, create placeholder
    components_df = pd.DataFrame()
    output_file = locator.get_heat_rejection_components()
    components_df.to_csv(output_file, index=False)
    print(f"  ✓ Saved components (placeholder): {output_file}")

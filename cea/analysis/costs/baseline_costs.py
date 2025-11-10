"""
Baseline costs for supply systems using detailed component specifications.

This script calculates costs for baseline supply systems using the same calculation
engine as optimization_new, providing accurate component-level cost breakdowns.

Replaces the deprecated system_costs.py with more detailed calculations.
"""

import pandas as pd
import numpy as np
from cea.inputlocator import InputLocator
from cea.optimization_new.domain import Domain
from cea.optimization_new.building import Building
from cea.optimization_new.network import Network
import cea.config

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def baseline_costs_main(locator, config):
    """
    Calculate baseline costs for heating and/or cooling systems.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :return: DataFrame with cost results
    """
    network_types = config.system_costs.network_types

    if not network_types:
        raise ValueError("No network types selected. Please select DH and/or DC in configuration.")

    all_results = {}

    # Calculate costs for each selected network type
    for network_type in network_types:
        print(f"\nCalculating {network_type} system costs...")
        results = calculate_costs_for_network_type(locator, config, network_type)
        all_results[network_type] = results

    # Merge results from all network types
    print("\nMerging results...")
    merged_results = merge_network_type_costs(all_results)

    # Format to match system_costs.py output structure
    print("Formatting output...")
    final_results, detailed_results = format_output_like_system_costs(merged_results, locator)

    # Save results
    print("Saving results...")
    locator.ensure_parent_folder_exists(locator.get_baseline_costs())
    final_results.to_csv(locator.get_baseline_costs(), index=False, float_format='%.2f', na_rep='nan')
    detailed_results.to_csv(locator.get_baseline_costs_detailed(), index=False, float_format='%.2f', na_rep='nan')

    print(f"\n✓ Baseline costs saved to: {locator.get_baseline_costs()}")
    print(f"✓ Detailed breakdown saved to: {locator.get_baseline_costs_detailed()}")

    # Check if any networks were found
    has_networks = any(name.startswith('N') for name in final_results['name'])
    if has_networks:
        print("\nℹ NOTE: Network costs include central plant equipment and thermal distribution piping.")
        print("  Variable energy costs (electricity, fuels) are NOT included.")
        print("  For complete costs including energy consumption, refer to optimization results.")

    return final_results


def calculate_network_costs(network_buildings, building_energy_potentials, domain_potentials, network_type, networks_dict=None):
    """
    Calculate costs for thermal networks (district heating/cooling systems).

    :param network_buildings: dict of {network_id: [buildings]}
    :param building_energy_potentials: dict of {building_id: potentials}
    :param domain_potentials: list of domain-level energy potentials
    :param network_type: 'DH' or 'DC'
    :param networks_dict: dict of {network_id: Network} with pre-built networks (optional)
    :return: dict of {network_id: {cost_metrics}}
    """
    from cea.optimization_new.containerclasses.supplySystemStructure import SupplySystemStructure
    from cea.optimization_new.supplySystem import SupplySystem
    from cea.optimization_new.containerclasses.energyFlow import EnergyFlow

    results = {}

    for network_id, buildings in network_buildings.items():
        print(f"    Calculating costs for network {network_id} with {len(buildings)} buildings")

        # Aggregate demand from all buildings in the network
        aggregated_demand_profile = sum([building.demand_flow.profile for building in buildings])

        # Create aggregated demand flow
        # Use the first building's demand flow as template for energy carrier
        first_building = buildings[0]
        aggregated_demand = EnergyFlow(
            input_category='primary',
            output_category='consumer',
            energy_carrier_code=first_building.demand_flow.energy_carrier.code,
            energy_flow_profile=aggregated_demand_profile
        )

        # Get network component selection from SupplySystemStructure class variable
        network_component_selection = SupplySystemStructure.initial_network_supply_systems_composition.get(
            network_id, {'primary': [], 'secondary': [], 'tertiary': []}
        )

        # Aggregate potentials from all buildings in the network
        network_potentials = {}
        for building in buildings:
            building_pots = building_energy_potentials.get(building.identifier, {})
            for ec_code, potential in building_pots.items():
                if ec_code in network_potentials:
                    # Sum up potentials from multiple buildings
                    network_potentials[ec_code].profile += potential.profile
                else:
                    network_potentials[ec_code] = potential

        # Build network supply system
        max_supply_flow = aggregated_demand.isolate_peak()
        system_structure = SupplySystemStructure(
            max_supply_flow=max_supply_flow,
            available_potentials=network_potentials,
            user_component_selection=network_component_selection,
            target_building_or_network=network_id
        )
        system_structure.build()

        # Create and evaluate supply system
        network_supply_system = SupplySystem(
            system_structure,
            system_structure.capacity_indicators,
            aggregated_demand
        )
        network_supply_system.evaluate()

        # Extract costs from network supply system
        # Pass None as building to indicate this is a network-level system
        network_costs = extract_costs_from_supply_system(
            network_supply_system, network_type, None
        )

        # Get piping costs from pre-built network (if available)
        piping_cost_annual = 0.0
        if networks_dict and network_id in networks_dict:
            network = networks_dict[network_id]
            piping_cost_annual = network.annual_piping_cost
            print(f"    Network piping cost: ${piping_cost_annual:,.2f}/year")
        else:
            print(f"    Warning: No network object found for {network_id}, piping costs not included")

        results[network_id] = {
            'network_type': network_type,  # This is for internal tracking
            'supply_system': network_supply_system,
            'buildings': buildings,  # List of buildings in this network
            'costs': network_costs,
            'piping_cost_annual': piping_cost_annual,  # Add piping cost
            'is_network': True,
            'network_id': network_id  # Store network ID for detailed output
        }

    return results


def calculate_costs_for_network_type(locator, config, network_type):
    """
    Calculate costs for either DH or DC using optimization_new engine.

    Respects network connectivity: buildings with scale='DISTRICT' are grouped into networks,
    while buildings with scale='BUILDING' are calculated as standalone systems.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param network_type: 'DH' or 'DC'
    :return: dict of {building_name or network_name: {cost_metrics}}
    """
    # Temporarily set network type for optimization_new
    original_network_type = config.optimization_new.network_type
    config.optimization_new.network_type = network_type

    try:
        # Initialise domain (reuse from optimization_new)
        domain = Domain(config, locator)

        # Load buildings
        domain.load_buildings()

        # Load energy potentials
        domain.load_potentials()

        # Initialise classes
        domain._initialize_energy_system_descriptor_classes()

        # Calculate base case supply systems
        building_energy_potentials = Building.distribute_building_potentials(
            domain.energy_potentials, domain.buildings
        )

        # Group buildings by connectivity state (network vs standalone)
        network_buildings = {}  # {network_id: [buildings]}
        standalone_buildings = []

        for building in domain.buildings:
            if building.initial_connectivity_state == 'stand_alone':
                standalone_buildings.append(building)
            else:
                # Building is connected to a network
                network_id = building.initial_connectivity_state
                if network_id not in network_buildings:
                    network_buildings[network_id] = []
                network_buildings[network_id].append(building)

        results = {}

        # Build networks to calculate piping costs
        networks_dict = {}  # {network_id: Network}
        if network_buildings:
            from cea.optimization_new.districtEnergySystem import DistrictEnergySystem

            # Create a DES to build networks
            des = DistrictEnergySystem(domain)
            built_networks = des.build_networks()
            # Store networks by ID
            for network in built_networks:
                networks_dict[network.identifier] = network

        # Calculate costs for network-connected buildings
        if network_buildings:
            print(f"  Found {len(network_buildings)} thermal network(s) for {network_type}")
            from cea.optimization_new.containerclasses.supplySystemStructure import SupplySystemStructure

            network_results = calculate_network_costs(
                network_buildings, building_energy_potentials,
                domain.energy_potentials, network_type, networks_dict
            )
            results.update(network_results)

        # Calculate costs for standalone buildings
        if standalone_buildings:
            print(f"  Calculating standalone systems for {len(standalone_buildings)} buildings")
            for building in standalone_buildings:
                building.calculate_supply_system(
                    building_energy_potentials[building.identifier]
                )

                # Extract costs from the building's supply system
                supply_system = building.stand_alone_supply_system

                results[building.identifier] = {
                    'network_type': network_type,
                    'supply_system': supply_system,
                    'building': building,
                    'costs': extract_costs_from_supply_system(supply_system, network_type, building)
                }

        return results

    finally:
        # Restore original network type
        config.optimization_new.network_type = original_network_type


def extract_costs_from_supply_system(supply_system, network_type, building):
    """
    Extract cost metrics from optimization_new supply system.

    :param supply_system: SupplySystem instance from optimization_new
    :param network_type: 'DH' or 'DC'
    :param building: Building instance
    :return: dict of cost metrics by service
    """
    costs = {}

    # 1. Component costs (CAPEX + fixed OPEX)
    for placement, components_dict in supply_system.installed_components.items():
        for component_code, component in components_dict.items():

            # Map component to energy service (e.g., BO1 → NG_hs, HP1 → GRID_hs)
            service_name = map_component_to_service(component, network_type, building)

            # Determine scale based on placement and initial connectivity
            scale = determine_scale(building, placement)

            # Aggregate costs by service
            if service_name not in costs:
                costs[service_name] = {
                    'capex_total_USD': 0.0,
                    'capex_a_USD': 0.0,
                    'opex_fixed_USD': 0.0,
                    'opex_a_fixed_USD': 0.0,
                    'opex_var_USD': 0.0,
                    'opex_a_var_USD': 0.0,
                    'scale': scale,
                    'components': []
                }

            costs[service_name]['capex_total_USD'] += component.inv_cost
            costs[service_name]['capex_a_USD'] += component.inv_cost_annual
            costs[service_name]['opex_fixed_USD'] += component.om_fix_cost_annual
            costs[service_name]['opex_a_fixed_USD'] += component.om_fix_cost_annual
            costs[service_name]['components'].append({
                'code': component_code,
                'capacity_kW': component.capacity,
                'placement': placement,
                'capex_total_USD': component.inv_cost,
                'capex_a_USD': component.inv_cost_annual,
                'opex_fixed_a_USD': component.om_fix_cost_annual
            })

    # 2. Energy carrier costs (variable OPEX)
    for ec_code, annual_cost in supply_system.annual_cost.items():
        # Map energy carrier to service (e.g., NATURALGAS → NG_hs)
        service_name = map_energy_carrier_to_service(ec_code, network_type)

        if service_name:  # Only process if mapping exists
            if service_name not in costs:
                costs[service_name] = {
                    'capex_total_USD': 0.0,
                    'capex_a_USD': 0.0,
                    'opex_fixed_USD': 0.0,
                    'opex_a_fixed_USD': 0.0,
                    'opex_var_USD': 0.0,
                    'opex_a_var_USD': 0.0,
                    'scale': determine_scale(building, 'primary'),
                    'components': []
                }

            # Energy costs are already annual and variable
            costs[service_name]['opex_var_USD'] += annual_cost
            costs[service_name]['opex_a_var_USD'] += annual_cost

    # 3. Calculate totals per service
    for service_name, service_costs in costs.items():
        service_costs['opex_USD'] = service_costs['opex_fixed_USD'] + service_costs['opex_var_USD']
        service_costs['opex_a_USD'] = service_costs['opex_a_fixed_USD'] + service_costs['opex_a_var_USD']
        service_costs['TAC_USD'] = service_costs['capex_a_USD'] + service_costs['opex_a_USD']

    return costs


def determine_scale(building, placement):
    """
    Determine if system is building, district, or city scale.

    :param building: Building instance (or None for network systems)
    :param placement: Component placement (primary/secondary/tertiary)
    :return: 'BUILDING', 'DISTRICT', or 'CITY'
    """
    # If building is None, this is a network-level system
    if building is None:
        return 'DISTRICT'

    # If building is connected to a network (state starts with 'N' for network IDs)
    if building.initial_connectivity_state != 'stand_alone':
        return 'DISTRICT'
    else:
        return 'BUILDING'


def map_component_to_service(component, network_type, building):
    """
    Map component code to energy service name (matching system_costs.py conventions).

    :param component: Component instance
    :param network_type: 'DH' or 'DC'
    :param building: Building instance
    :return: Service name string (e.g., 'NG_hs', 'GRID_cs')
    """
    # Determine service suffix based on network type
    if network_type == 'DH':
        suffix = '_hs'  # heating service
    else:  # DC
        suffix = '_cs'  # cooling service

    # Get component code
    comp_code = component.code if hasattr(component, 'code') else str(component)

    # Map based on component database definitions
    # These mappings come from COMPONENTS/CONVERSION/*.csv files

    # Boilers
    if comp_code in ['BO1', 'BO7', 'BO8', 'BO9', 'BO10']:  # Natural gas boilers
        carrier = 'NG'
    elif comp_code in ['BO2']:  # Oil boilers
        carrier = 'OIL'
    elif comp_code in ['BO4']:  # Coal boilers
        carrier = 'COAL'
    elif comp_code in ['BO5']:  # Electric boilers
        carrier = 'GRID'
    elif comp_code in ['BO6']:  # Wood boilers
        carrier = 'WOOD'

    # Heat pumps (use electricity)
    elif comp_code.startswith('HP'):
        carrier = 'GRID'

    # Chillers (use electricity)
    elif comp_code.startswith('CH') or comp_code.startswith('VCCH') or comp_code.startswith('ACH'):
        carrier = 'GRID'

    # Cogeneration plants
    elif comp_code.startswith('CCGT') or comp_code.startswith('FC'):
        carrier = 'NG'

    # District heating/cooling
    # Check if this is a network-level system (building=None) or a building connected to a network
    elif building is None or building.initial_connectivity_state == 'network':
        if network_type == 'DH':
            carrier = 'DH'
        else:
            carrier = 'DC'

    # Default to GRID if unknown
    else:
        carrier = 'GRID'

    return f"{carrier}{suffix}"


def map_energy_carrier_to_service(ec_code, network_type):
    """
    Map energy carrier code to service name.

    :param ec_code: Energy carrier code from optimization_new
    :param network_type: 'DH' or 'DC'
    :return: Service name string or None if not applicable
    """
    suffix = '_hs' if network_type == 'DH' else '_cs'

    # Map energy carriers to service prefixes
    carrier_map = {
        'NATURALGAS': 'NG',
        'GRID': 'GRID',
        'OIL': 'OIL',
        'COAL': 'COAL',
        'WOOD': 'WOOD',
        'DH': 'DH',
        'DC': 'DC',
    }

    carrier = carrier_map.get(ec_code)
    if carrier:
        return f"{carrier}{suffix}"
    else:
        # Return None for carriers that don't map to services (e.g., heat rejection)
        return None


def merge_network_type_costs(all_results):
    """
    Merge heating and cooling costs for each building.

    :param all_results: dict of {network_type: {building_name: results}}
    :return: dict of {building_name: {network_type: results}}
    """
    merged = {}

    # Get all building names across all network types
    all_buildings = set()
    for network_type, results in all_results.items():
        all_buildings.update(results.keys())

    for building_name in all_buildings:
        merged[building_name] = {}
        for network_type, results in all_results.items():
            if building_name in results:
                merged[building_name][network_type] = results[building_name]

    return merged


def format_output_like_system_costs(merged_results, locator):
    """
    Format results to match system_costs.py output structure exactly.

    :param merged_results: Merged results from all network types
    :param locator: InputLocator instance
    :return: (final_df, detailed_df) tuple of DataFrames
    """
    # Read demand to get building list and GFA
    demand = pd.read_csv(locator.get_total_demand())

    final_rows = []
    detailed_rows = []

    # Define all possible services (matching system_costs.py)
    services = [
        # Heating services
        'OIL_hs', 'NG_hs', 'WOOD_hs', 'COAL_hs', 'GRID_hs', 'DH_hs',
        # Hot water services
        'OIL_ww', 'NG_ww', 'WOOD_ww', 'COAL_ww', 'GRID_ww', 'DH_ww',
        # Cooling services
        'GRID_cs', 'GRID_cdata', 'GRID_cre', 'DC_cs',
        # Electricity services
        'GRID_pro', 'GRID_l', 'GRID_aux', 'GRID_v', 'GRID_a', 'GRID_data', 'GRID_ve'
    ]

    for identifier, network_data in merged_results.items():
        # Check if this is a network or a building
        is_network = network_data.get('DH', {}).get('is_network', False) or \
                     network_data.get('DC', {}).get('is_network', False)

        if is_network:
            # This is a network identifier (e.g., 'N1001')
            # Get all buildings in the network to sum GFA
            buildings_in_network = network_data.get('DH', {}).get('buildings') or \
                                 network_data.get('DC', {}).get('buildings', [])

            if not buildings_in_network:
                print(f"Warning: Network {identifier} has no buildings, skipping.")
                continue

            # Sum GFA from all buildings in the network
            total_gfa = 0.0
            for building in buildings_in_network:
                building_demand = demand[demand['name'] == building.identifier]
                if not building_demand.empty:
                    total_gfa += building_demand.iloc[0]['GFA_m2']

            row = {
                'name': identifier,
                'GFA_m2': total_gfa
            }
        else:
            # This is a building identifier
            building_name = identifier
            building_demand = demand[demand['name'] == building_name]
            if building_demand.empty:
                print(f"Warning: Building {building_name} not found in demand results, skipping.")
                continue

            building_demand = building_demand.iloc[0]

            row = {
                'name': building_name,
                'GFA_m2': building_demand['GFA_m2']
            }

        # Initialise all service columns to zero
        for service in services:
            row[f'{service}_capex_total_USD'] = 0.0
            row[f'{service}_opex_fixed_USD'] = 0.0
            row[f'{service}_opex_var_USD'] = 0.0
            row[f'{service}_opex_USD'] = 0.0
            row[f'{service}_capex_a_USD'] = 0.0
            row[f'{service}_opex_a_fixed_USD'] = 0.0
            row[f'{service}_opex_a_var_USD'] = 0.0
            row[f'{service}_opex_a_USD'] = 0.0
            row[f'{service}_TAC_USD'] = 0.0

            # Scale-specific columns
            row[f'{service}_capex_total_building_scale_USD'] = 0.0
            row[f'{service}_capex_total_district_scale_USD'] = 0.0
            row[f'{service}_capex_total_city_scale_USD'] = 0.0
            row[f'{service}_capex_a_building_scale_USD'] = 0.0
            row[f'{service}_capex_a_district_scale_USD'] = 0.0
            row[f'{service}_capex_a_city_scale_USD'] = 0.0
            row[f'{service}_opex_building_scale_USD'] = 0.0
            row[f'{service}_opex_district_scale_USD'] = 0.0
            row[f'{service}_opex_city_scale_USD'] = 0.0
            row[f'{service}_opex_a_building_scale_USD'] = 0.0
            row[f'{service}_opex_a_district_scale_USD'] = 0.0
            row[f'{service}_opex_a_city_scale_USD'] = 0.0

        # Fill in costs from each network type
        for network_type, data in network_data.items():
            if 'costs' in data:
                for service_name, service_costs in data['costs'].items():
                    if service_name in [s for s in services]:
                        # Main cost columns
                        row[f'{service_name}_capex_total_USD'] += service_costs['capex_total_USD']
                        row[f'{service_name}_opex_fixed_USD'] += service_costs['opex_fixed_USD']
                        row[f'{service_name}_opex_var_USD'] += service_costs['opex_var_USD']
                        row[f'{service_name}_opex_USD'] += service_costs['opex_USD']
                        row[f'{service_name}_capex_a_USD'] += service_costs['capex_a_USD']
                        row[f'{service_name}_opex_a_fixed_USD'] += service_costs['opex_a_fixed_USD']
                        row[f'{service_name}_opex_a_var_USD'] += service_costs['opex_a_var_USD']
                        row[f'{service_name}_opex_a_USD'] += service_costs['opex_a_USD']
                        row[f'{service_name}_TAC_USD'] += service_costs['TAC_USD']

                        # Scale-specific columns
                        scale = service_costs['scale']
                        if scale == 'BUILDING':
                            row[f'{service_name}_capex_total_building_scale_USD'] += service_costs['capex_total_USD']
                            row[f'{service_name}_capex_a_building_scale_USD'] += service_costs['capex_a_USD']
                            row[f'{service_name}_opex_building_scale_USD'] += service_costs['opex_USD']
                            row[f'{service_name}_opex_a_building_scale_USD'] += service_costs['opex_a_USD']
                        elif scale == 'DISTRICT':
                            row[f'{service_name}_capex_total_district_scale_USD'] += service_costs['capex_total_USD']
                            row[f'{service_name}_capex_a_district_scale_USD'] += service_costs['capex_a_USD']
                            row[f'{service_name}_opex_district_scale_USD'] += service_costs['opex_USD']
                            row[f'{service_name}_opex_a_district_scale_USD'] += service_costs['opex_a_USD']
                        elif scale == 'CITY':
                            row[f'{service_name}_capex_total_city_scale_USD'] += service_costs['capex_total_USD']
                            row[f'{service_name}_capex_a_city_scale_USD'] += service_costs['capex_a_USD']
                            row[f'{service_name}_opex_city_scale_USD'] += service_costs['opex_USD']
                            row[f'{service_name}_opex_a_city_scale_USD'] += service_costs['opex_a_USD']

                        # Add to detailed output
                        for comp in service_costs['components']:
                            # Only include network_type for network systems (starts with 'N')
                            # For standalone buildings, leave network_type empty
                            if is_network:
                                display_network_type = network_type  # Show DC/DH for networks
                            else:
                                display_network_type = ''  # Empty for standalone buildings

                            detailed_rows.append({
                                'name': identifier,  # Use identifier (works for both buildings and networks)
                                'network_type': display_network_type,
                                'service': service_name,
                                'component_code': comp['code'],
                                'capacity_kW': comp['capacity_kW'],
                                'placement': comp['placement'],
                                'capex_total_USD': comp['capex_total_USD'],
                                'capex_a_USD': comp['capex_a_USD'],
                                'opex_fixed_a_USD': comp['opex_fixed_a_USD'],
                                'scale': scale
                            })

            # Add network piping costs to detailed output (if this is a network)
            if is_network and 'piping_cost_annual' in data and data['piping_cost_annual'] > 0:
                piping_cost_annual = data['piping_cost_annual']
                # Piping costs are shown as a separate line item for networks
                detailed_rows.append({
                    'name': identifier,
                    'network_type': network_type,
                    'service': f'{network_type}_network',  # e.g., DC_network or DH_network
                    'component_code': 'PIPES',
                    'capacity_kW': 0.0,  # N/A for pipes
                    'placement': 'distribution',
                    'capex_total_USD': 0.0,  # Not available in current calculation
                    'capex_a_USD': piping_cost_annual,
                    'opex_fixed_a_USD': 0.0,  # Piping O&M could be added if needed
                    'scale': 'DISTRICT'
                })

        # Calculate aggregated system totals (matching system_costs.py exactly)
        row['Capex_total_sys_USD'] = sum(row[f'{s}_capex_total_USD'] for s in services)
        row['Opex_fixed_sys_USD'] = sum(row[f'{s}_opex_fixed_USD'] for s in services)
        row['Opex_var_sys_USD'] = sum(row[f'{s}_opex_var_USD'] for s in services)
        row['Opex_sys_USD'] = sum(row[f'{s}_opex_USD'] for s in services)
        row['Capex_a_sys_USD'] = sum(row[f'{s}_capex_a_USD'] for s in services)
        row['Opex_a_fixed_sys_USD'] = sum(row[f'{s}_opex_a_fixed_USD'] for s in services)
        row['Opex_a_var_sys_USD'] = sum(row[f'{s}_opex_a_var_USD'] for s in services)
        row['Opex_a_sys_USD'] = sum(row[f'{s}_opex_a_USD'] for s in services)
        row['TAC_sys_USD'] = sum(row[f'{s}_TAC_USD'] for s in services)

        # Calculate scale-based system totals
        row['Capex_total_sys_building_scale_USD'] = sum(row[f'{s}_capex_total_building_scale_USD'] for s in services)
        row['Capex_total_sys_district_scale_USD'] = sum(row[f'{s}_capex_total_district_scale_USD'] for s in services)
        row['Capex_total_sys_city_scale_USD'] = sum(row[f'{s}_capex_total_city_scale_USD'] for s in services)

        row['Capex_a_sys_building_scale_USD'] = sum(row[f'{s}_capex_a_building_scale_USD'] for s in services)
        row['Capex_a_sys_district_scale_USD'] = sum(row[f'{s}_capex_a_district_scale_USD'] for s in services)
        row['Capex_a_sys_city_scale_USD'] = sum(row[f'{s}_capex_a_city_scale_USD'] for s in services)

        row['Opex_sys_building_scale_USD'] = sum(row[f'{s}_opex_building_scale_USD'] for s in services)
        row['Opex_sys_district_scale_USD'] = sum(row[f'{s}_opex_district_scale_USD'] for s in services)
        row['Opex_sys_city_scale_USD'] = sum(row[f'{s}_opex_city_scale_USD'] for s in services)

        row['Opex_a_sys_building_scale_USD'] = sum(row[f'{s}_opex_a_building_scale_USD'] for s in services)
        row['Opex_a_sys_district_scale_USD'] = sum(row[f'{s}_opex_a_district_scale_USD'] for s in services)
        row['Opex_a_sys_city_scale_USD'] = sum(row[f'{s}_opex_a_city_scale_USD'] for s in services)

        final_rows.append(row)

    final_df = pd.DataFrame(final_rows)
    detailed_df = pd.DataFrame(detailed_rows)

    return final_df, detailed_df


def main(config: cea.config.Configuration):
    """
    Main entry point for baseline-costs script.

    :param config: Configuration instance
    """
    locator = InputLocator(config.scenario)
    print(f'Running baseline-costs with scenario = {config.scenario}')
    baseline_costs_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())

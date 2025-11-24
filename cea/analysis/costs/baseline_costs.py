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
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def validate_network_results_exist(locator, network_name, network_type):
    """
    Validate that thermal-network part 2 has been completed for the specified network.

    :param locator: InputLocator instance
    :param network_name: Network layout name
    :param network_type: 'DH' or 'DC'
    :raises ValueError: If required network result files don't exist
    """
    import os

    # Check for key output files from thermal-network part 2
    network_folder = locator.get_output_thermal_network_type_folder(network_type, network_name)
    layout_folder = os.path.join(network_folder, 'layout')

    # These files are created by thermal-network part 1 (layout)
    required_files = [
        os.path.join(layout_folder, 'edges.shp'),
        os.path.join(layout_folder, 'nodes.shp'),
    ]

    missing_files = [f for f in required_files if not os.path.exists(f)]

    if missing_files:
        raise ValueError(
            f"Thermal-network results not found for network '{network_name}' ({network_type}).\n\n"
            f"Missing files:\n" + "\n".join(f"  - {f}" for f in missing_files) + "\n\n"
            f"Please run 'thermal-network' script (both part 1 and part 2) before running baseline-costs.\n"
            f"Alternatively, select a different network layout that has been completed."
        )

    print(f"  ✓ {network_type} network '{network_name}' results found")


def baseline_costs_main(locator, config):
    """
    Calculate baseline costs for heating and/or cooling systems.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :return: DataFrame with cost results
    """
    # Get network types (can be list like ['DH', 'DC'] or single value like 'DH')
    network_types = config.system_costs.network_type
    if isinstance(network_types, str):
        network_types = [network_types]

    # Get network name - this is required
    network_name = config.system_costs.network_name
    if not network_name:
        raise ValueError(
            "Network name is required for baseline-costs calculation.\n"
            "Please select a network layout from the 'network-name' parameter.\n"
            "Networks are created by running 'thermal-network' script (part 1 and part 2)."
        )

    print(f"Running baseline-costs for network layout: {network_name}")
    print(f"Network type(s): {', '.join(network_types)}")

    # Validate that thermal-network part 2 has been run for each network type
    print("\nValidating thermal-network results...")
    for network_type in network_types:
        validate_network_results_exist(locator, network_name, network_type)

    all_results = {}

    # Calculate costs for each specified network type
    for network_type in network_types:
        print(f"\nCalculating {network_type} system costs...")
        try:
            results = calculate_costs_for_network_type(locator, config, network_type, network_name)
            all_results[network_type] = results
        except ValueError as e:
            # Check if this is a "no demand" or "no supply system" error
            error_msg = str(e)
            if "None of the components chosen" in error_msg or "T30W" in error_msg or "T10W" in error_msg:
                print(f"  ⚠ Skipping {network_type}: No valid supply systems found for this network type")
                print(f"    (This is expected for scenarios with no {network_type} demand)")
                continue
            else:
                # Re-raise other errors
                raise

    # Check if we got any results
    if not all_results:
        raise ValueError(
            "No valid supply systems found for any of the selected network types.\n"
            f"Selected network types: {', '.join(network_types)}\n\n"
            "Please check that:\n"
            "1. Buildings have supply systems configured in supply.csv\n"
            "2. The selected network type matches the building demands (DH for heating, DC for cooling)"
        )

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
        print("  For complete costs including energy consumption, refer to optimisation results.")

    return final_results


def calculate_district_network_costs(locator, config, network_type, network_name,
                                     network_buildings, building_energy_potentials, domain_potentials):
    """
    Calculate district network costs using component parameters (not supply.csv assemblies).

    This implements Case 1 & 2: Buildings IN network layout use component selection.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param network_type: 'DH' or 'DC'
    :param network_name: Network layout name
    :param network_buildings: list of Building objects connected to network
    :param building_energy_potentials: dict of {building_id: potentials}
    :param domain_potentials: list of domain-level energy potentials
    :return: dict of {network_id: {cost_metrics}}
    """
    from cea.optimization_new.containerclasses.supplySystemStructure import SupplySystemStructure
    from cea.optimization_new.supplySystem import SupplySystem
    from cea.optimization_new.containerclasses.energyFlow import EnergyFlow
    from cea.optimization_new.network import Network

    results = {}
    network_id = f'{network_name}_{network_type}'  # Use meaningful network ID

    print(f"    Network {network_id}: {len(network_buildings)} buildings")
    print(f"    Using component parameters (not supply.csv):")
    print(f"      - cooling-components: {config.system_costs.cooling_components}")
    print(f"      - heating-components: {config.system_costs.heating_components}")
    print(f"      - heat-rejection: {config.system_costs.heat_rejection_components}")

    # Aggregate demand from all buildings in the network
    aggregated_demand_profile = sum([building.demand_flow.profile for building in network_buildings])

    # Create aggregated demand flow
    first_building = network_buildings[0]
    aggregated_demand = EnergyFlow(
        input_category='primary',
        output_category='consumer',
        energy_carrier_code=first_building.demand_flow.energy_carrier.code,
        energy_flow_profile=aggregated_demand_profile
    )

    # Aggregate potentials from all buildings in the network
    network_potentials = {}
    for building in network_buildings:
        building_pots = building_energy_potentials.get(building.identifier, {})
        for ec_code, potential in building_pots.items():
            if ec_code in network_potentials:
                network_potentials[ec_code].profile += potential.profile
            else:
                network_potentials[ec_code] = potential

    # Build network supply system using component parameters (NO user_component_selection)
    # This allows SupplySystemStructure to use the component parameters from config
    max_supply_flow = aggregated_demand.isolate_peak()

    if max_supply_flow.profile.max() == 0.0:
        print(f"      Zero demand - skipping")
        return results

    # Build system structure WITHOUT user_component_selection
    # This makes it use config parameters (cooling_components, heating_components)
    system_structure = SupplySystemStructure(
        max_supply_flow=max_supply_flow,
        available_potentials=network_potentials,
        user_component_selection=None,  # Use config parameters, not supply.csv
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
    network_costs = extract_costs_from_supply_system(
        network_supply_system, network_type, None
    )

    # Calculate piping costs from network layout
    piping_cost_annual = 0.0
    piping_cost_total = 0.0
    try:
        # Load network from thermal-network part 2 results
        import cea.config
        network_config = cea.config.Configuration()
        network_config.scenario = config.scenario
        network = Network(locator, network_name, network_type, network_config)
        piping_cost_annual = network.annual_piping_cost
        network_lifetime_yrs = network.configuration_defaults.get('network_lifetime_yrs', 20.0)
        piping_cost_total = piping_cost_annual * network_lifetime_yrs
        print(f"      Piping: ${piping_cost_total:,.2f} total, ${piping_cost_annual:,.2f}/year")
    except Exception as e:
        print(f"      Warning: Could not load piping costs: {e}")

    results[network_id] = {
        'network_type': network_type,
        'supply_system': network_supply_system,
        'buildings': network_buildings,
        'costs': network_costs,
        'piping_cost_annual': piping_cost_annual,
        'piping_cost_total': piping_cost_total,
        'is_network': True
    }

    return results


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

        # Skip if zero demand
        if max_supply_flow.profile.max() == 0.0:
            print(f"  {network_id}: Zero demand - skipping supply system instantiation")
            return results

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
        piping_cost_total = 0.0
        if networks_dict and network_id in networks_dict:
            network = networks_dict[network_id]
            piping_cost_annual = network.annual_piping_cost
            # Calculate total CAPEX from annualized cost
            # Network._calculate_piping_cost uses: annualised = total / network_lifetime_yrs
            network_lifetime_yrs = network.configuration_defaults.get('network_lifetime_yrs', 20.0)
            piping_cost_total = piping_cost_annual * network_lifetime_yrs
            print(f"    Network piping cost: ${piping_cost_total:,.2f} total, ${piping_cost_annual:,.2f}/year")
        else:
            print(f"    Warning: No network object found for {network_id}, piping costs not included")

        results[network_id] = {
            'network_type': network_type,  # This is for internal tracking
            'supply_system': network_supply_system,
            'buildings': buildings,  # List of buildings in this network
            'costs': network_costs,
            'piping_cost_annual': piping_cost_annual,  # Annualized piping cost
            'piping_cost_total': piping_cost_total,  # Total piping CAPEX
            'is_network': True,
            'network_id': network_id  # Store network ID for detailed output
        }

    return results


def calculate_costs_for_network_type(locator, config, network_type, network_name=None):
    """
    Calculate costs for either DH or DC using optimization_new engine.

    Four-case logic (network layout is source of truth for connectivity):
    - Case 1 & 2: Building IN network layout → Use component parameters (ignore supply.csv)
    - Case 3 & 4: Building NOT in layout → Use existing supply.csv configuration

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param network_type: 'DH' or 'DC'
    :param network_name: Specific network layout to use (required)
    :return: dict of {building_name or network_name: {cost_metrics}}
    """
    import geopandas as gpd
    import pandas as pd
    import os

    # Step 1: Read network layout to determine building connectivity
    # Network layout = SOURCE OF TRUTH for connectivity
    network_folder = locator.get_output_thermal_network_type_folder(network_type, network_name)
    layout_folder = os.path.join(network_folder, 'layout')
    nodes_file = os.path.join(layout_folder, 'nodes.shp')

    nodes_df = gpd.read_file(nodes_file)
    network_buildings_from_layout = nodes_df[nodes_df['type'] == 'CONSUMER']['building'].unique().tolist()
    network_buildings_from_layout = [b for b in network_buildings_from_layout if b and b != 'NONE']

    print(f"  Network layout '{network_name}' connects {len(network_buildings_from_layout)} buildings")
    print(f"    Connected: {network_buildings_from_layout}")

    if not network_buildings_from_layout:
        print(f"  ⚠ No buildings connected in {network_type} network layout - skipping")
        return {}

    # Step 2: Load ALL buildings with their existing supply.csv (NO MODIFICATIONS)
    import cea.config
    domain_config = cea.config.Configuration()
    domain_config.scenario = config.scenario
    domain_config.optimization_new.network_type = network_type

    # Important: Set component parameters from system-costs config
    domain_config.optimization_new.cooling_components = config.system_costs.cooling_components
    domain_config.optimization_new.heating_components = config.system_costs.heating_components
    domain_config.optimization_new.heat_rejection_components = config.system_costs.heat_rejection_components

    domain = Domain(domain_config, locator)
    domain.load_buildings()

    # Load potentials and initialize classes
    domain.load_potentials()
    domain._initialize_energy_system_descriptor_classes()

    # Calculate base case supply systems
    building_energy_potentials = Building.distribute_building_potentials(
        domain.energy_potentials, domain.buildings
    )

    # Step 3: Separate buildings by connectivity (network layout is source of truth)
    print(f"\n  Four-case logic:")
    network_connected_buildings = []
    standalone_buildings = []

    for building in domain.buildings:
        if building.identifier in network_buildings_from_layout:
            # Case 1 & 2: Building IN network layout → Use component parameters
            network_connected_buildings.append(building)
            print(f"    {building.identifier}: IN layout → district plant (component parameters)")
        else:
            # Case 3 & 4: Building NOT in layout → Use existing supply.csv
            standalone_buildings.append(building)
            print(f"    {building.identifier}: NOT in layout → standalone ({building._stand_alone_supply_system_code})")

    results = {}

    # Step 4: Calculate standalone building costs (Case 3 & 4)
    # These buildings use their existing supply.csv configuration
    if standalone_buildings:
        print(f"\n  Calculating standalone building costs ({len(standalone_buildings)} buildings):")
        for building in standalone_buildings:
            building.calculate_supply_system(
                building_energy_potentials[building.identifier]
            )

            # Skip buildings with None supply system (zero demand)
            if building.stand_alone_supply_system is None:
                print(f"    {building.identifier}: Skipped (zero demand)")
                continue

            # Extract costs from the building's supply system
            supply_system = building.stand_alone_supply_system

            results[building.identifier] = {
                'network_type': network_type,
                'supply_system': supply_system,
                'building': building,
                'costs': extract_costs_from_supply_system(supply_system, network_type, building),
                'is_network': False
            }
            print(f"    {building.identifier}: Calculated using {building._stand_alone_supply_system_code}")

    # Step 5: Calculate district network costs (Case 1 & 2)
    # These buildings use component parameters, not supply.csv
    if network_connected_buildings:
        print(f"\n  Calculating district network costs ({len(network_connected_buildings)} buildings):")
        network_results = calculate_district_network_costs(
            locator, config, network_type, network_name,
            network_connected_buildings, building_energy_potentials,
            domain.energy_potentials
        )
        results.update(network_results)

    return results


def extract_costs_from_supply_system(supply_system, network_type, building):
    """
    Extract cost metrics from optimization_new supply system.

    :param supply_system: SupplySystem instance from optimization_new
    :param network_type: 'DH' or 'DC'
    :param building: Building instance (or None for network-level systems)
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
    :param building: Building instance (or None for network-level systems)
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

    # Cooling towers and heat rejection
    elif comp_code.startswith('CT'):
        carrier = 'GRID'  # Cooling towers use electricity for fans/pumps

    # District heating/cooling
    # Check if this is a network-level system (building=None) or a building connected to a network
    elif building is None or building.initial_connectivity_state != 'stand_alone':
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

    # Sort results: buildings first (B*), then networks (N*)
    # This makes the output more logical and easier to read
    sorted_identifiers = sorted(merged_results.keys(),
                                key=lambda x: (x.startswith('N'), x))

    for identifier in sorted_identifiers:
        network_data = merged_results[identifier]
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
                piping_cost_total = data.get('piping_cost_total', 0.0)
                # Piping costs are shown as a separate line item for networks
                detailed_rows.append({
                    'name': identifier,
                    'network_type': network_type,
                    'service': f'{network_type}_network',  # e.g., DC_network or DH_network
                    'component_code': 'PIPES',
                    'capacity_kW': 0.0,  # N/A for pipes
                    'placement': 'distribution',
                    'capex_total_USD': piping_cost_total,
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

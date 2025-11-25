"""
Baseline costs for supply systems using detailed component specifications.

This script calculates costs for baseline supply systems using the same calculation
engine as optimization_new, providing accurate component-level cost breakdowns.

Replaces the deprecated system_costs.py with more detailed calculations.
"""

import os
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


def get_components_from_supply_assembly(locator, supply_code, category):
    """
    Extract component codes from SUPPLY assembly definition.

    :param locator: InputLocator instance
    :param supply_code: SUPPLY assembly code (e.g., 'SUPPLY_COOLING_AS4')
    :param category: 'SUPPLY_COOLING', 'SUPPLY_HEATING', or 'SUPPLY_HOTWATER'
    :return: dict with keys 'primary', 'secondary', 'tertiary' containing lists of component codes
    """
    import pandas as pd

    # Map category to locator method
    category_to_method = {
        'SUPPLY_COOLING': locator.get_database_assemblies_supply_cooling,
        'SUPPLY_HEATING': locator.get_database_assemblies_supply_heating,
        'SUPPLY_HOTWATER': locator.get_database_assemblies_supply_hot_water,
    }

    method = category_to_method.get(category)
    if not method:
        return {'primary': [], 'secondary': [], 'tertiary': []}

    filepath = method()
    if not pd.io.common.file_exists(filepath):
        return {'primary': [], 'secondary': [], 'tertiary': []}

    df = pd.read_csv(filepath)

    # Find the row for this supply code
    row = df[df['code'] == supply_code]
    if row.empty:
        return {'primary': [], 'secondary': [], 'tertiary': []}

    # Extract component codes from columns
    def parse_components(value):
        """Parse component string, handling '-' and comma-separated values"""
        if pd.isna(value) or value == '-':
            return []
        return [c.strip() for c in str(value).split(',') if c.strip() and c.strip() != '-']

    result = {
        'primary': parse_components(row['primary_components'].iloc[0]) if 'primary_components' in row.columns else [],
        'secondary': parse_components(row['secondary_components'].iloc[0]) if 'secondary_components' in row.columns else [],
        'tertiary': parse_components(row['tertiary_components'].iloc[0]) if 'tertiary_components' in row.columns else [],
    }

    return result


def filter_to_single_component_per_category(capacity_indicator_vector):
    """
    Filter capacity indicators to keep only ONE component per category.

    For baseline costs without optimisation, we don't want to size ALL possible
    components at full capacity (e.g., all 6 boiler types). Instead, keep only
    the first viable component of each type.

    :param capacity_indicator_vector: CapacityIndicatorVector instance
    :return: CapacityIndicatorVector with filtered indicators
    """
    from cea.optimization_new.helperclasses.optimization.capacityIndicator import CapacityIndicatorVector

    # Track which component classes we've already seen per category
    seen_classes = {}
    filtered_indicators = []

    for indicator in capacity_indicator_vector.capacity_indicators:
        category = indicator.category  # 'primary', 'secondary', 'tertiary'
        code = indicator.code  # e.g., 'BO1', 'BO2', 'CH1'

        # Get the component class (e.g., 'BOILERS' from 'BO1')
        component_class = code[:2]  # 'BO' for BO1-BO6, 'CH' for CH1-CH2, 'CT' for cooling towers

        # Create a key combining category and component class
        key = f"{category}_{component_class}"

        if key not in seen_classes:
            # This is the first component of this class in this category - keep it
            seen_classes[key] = code
            filtered_indicators.append(indicator)

    return CapacityIndicatorVector(filtered_indicators, capacity_indicator_vector.dependencies)


def validate_network_results_exist(locator, network_name, network_type):
    """
    Validate that thermal-network part 2 has been completed for the specified network.

    :param locator: InputLocator instance
    :param network_name: Network layout name
    :param network_type: 'DH' or 'DC'
    :return: (is_valid, error_message) - is_valid is True if files exist, False otherwise
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
        error_msg = (
            f"Thermal-network results not found for network '{network_name}' ({network_type}).\n\n"
            f"Missing files:\n" + "\n".join(f"  - {f}" for f in missing_files) + "\n\n"
            f"Please run 'thermal-network' script (both part 1 and part 2) before running baseline-costs.\n"
            f"Alternatively, select a different network layout that has been completed."
        )
        return False, error_msg

    return True, None


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

    print(f"\n{'='*70}")
    print("BASELINE COSTS CALCULATION")
    print(f"{'='*70}")
    print(f"Network layout: {network_name}")
    print(f"Network types: {', '.join(network_types)}")

    # Validate that thermal-network part 2 has been run for each network type
    print(f"\n{'-'*70}")
    print("Validating thermal-network results...")
    validation_errors = {}
    valid_network_types = []

    for network_type in network_types:
        is_valid, error_msg = validate_network_results_exist(locator, network_name, network_type)
        if is_valid:
            print(f"  ✓ {network_type} network '{network_name}' results found")
            valid_network_types.append(network_type)
        else:
            validation_errors[network_type] = error_msg

    # If no network types passed validation, stop here
    if not valid_network_types:
        print(f"\n{'='*70}")
        print("VALIDATION ERRORS")
        print(f"{'='*70}")
        for network_type, error in validation_errors.items():
            print(f"\n{network_type} network:\n{error}\n")
        raise ValueError(
            f"All network types failed validation ({', '.join(network_types)}). "
            f"See errors above."
        )

    # Show validation warnings for failed network types (but continue with valid ones)
    if validation_errors:
        print(f"\n{'-'*70}")
        print("VALIDATION WARNINGS")
        print(f"{'-'*70}")
        for network_type, error in validation_errors.items():
            print(f"\n{network_type} network:\n{error}\n")
        print(f"Continuing with valid network types: {', '.join(valid_network_types)}")

    all_results = {}

    # Calculate standalone building costs ONCE for all services (not per network_type)
    # Standalone buildings should show all their systems regardless of which networks are being analyzed
    print(f"\n{'-'*70}")
    print("Calculating standalone building costs...")
    standalone_results = calculate_standalone_building_costs(locator, config, network_name)

    # Calculate costs for each VALID network type
    calculation_errors = {}
    succeeded = []

    for network_type in valid_network_types:
        print(f"\n{'-'*70}")
        print(f"Calculating {network_type} district network costs...")
        try:
            results = calculate_costs_for_network_type(locator, config, network_type, network_name, standalone_results)
            all_results[network_type] = results
            succeeded.append(network_type)
        except ValueError as e:
            # Check if this is a "no demand" or "no supply system" error
            error_msg = str(e)
            if "None of the components chosen" in error_msg or "T30W" in error_msg or "T10W" in error_msg:
                # Show detailed error if it's an energy carrier mismatch
                if "ERROR: Insufficient capacity" in error_msg:
                    # This is our detailed error message - show it
                    print(error_msg)
                else:
                    # Generic message for simple cases
                    print(f"  ⚠ Skipping {network_type}: No valid supply systems")
                    print(f"    (Expected for scenarios with no {network_type} demand)")
                calculation_errors[network_type] = error_msg
                continue
            else:
                # Re-raise other errors
                raise

    # Check if we got any results
    if not all_results:
        print(f"\n{'='*70}")
        print("CALCULATION ERRORS")
        print(f"{'='*70}")
        for network_type, error in calculation_errors.items():
            print(f"\n{network_type} network:\n{error}\n")
        raise ValueError(
            "No valid supply systems found for any of the selected network types.\n"
            f"Selected network types: {', '.join(network_types)}\n\n"
            "Please check that:\n"
            "1. Buildings have supply systems configured in Building Properties/Supply settings\n"
            "2. The selected network type matches the building demands (DH for heating, DC for cooling)"
        )

    # Merge results from all network types
    print(f"\n{'-'*70}")
    print("Merging and formatting results...")
    merged_results = merge_network_type_costs(all_results)

    # Import simplified formatting function
    from cea.analysis.costs.format_simplified import format_output_simplified
    final_results, detailed_results = format_output_simplified(merged_results, locator)

    # Save results
    print(f"\n{'-'*70}")
    print("Saving results...")
    locator.ensure_parent_folder_exists(locator.get_baseline_costs())
    final_results.to_csv(locator.get_baseline_costs(), index=False, float_format='%.2f', na_rep='nan')
    detailed_results.to_csv(locator.get_baseline_costs_detailed(), index=False, float_format='%.2f', na_rep='nan')

    # Show completion status based on success/failure
    all_errors = {**validation_errors, **calculation_errors}
    print(f"\n{'='*70}")
    if all_errors:
        print("PARTIALLY COMPLETED")
    else:
        print("COMPLETED")
    print(f"{'='*70}")
    print(f"Summary: {locator.get_baseline_costs()}")
    print(f"Detailed: {locator.get_baseline_costs_detailed()}")

    # Show summary of what succeeded and what failed (matching thermal-network behavior)
    if all_errors:
        failed_types = ', '.join(sorted(all_errors.keys()))
        succeeded_types = ', '.join(sorted(succeeded))
        print(f"\nCompleted: {succeeded_types}. Failed: {failed_types}.")
    else:
        print(f"\nAll network types completed successfully: {', '.join(sorted(succeeded))}")

    # Check if any networks were found
    has_networks = any(name.startswith('N') for name in final_results['name'])
    if has_networks:
        print(f"\nNote: Network costs include central plant equipment and piping.")
        print("      Variable energy costs (electricity, fuels) are NOT included.")
        print("  For complete costs including energy consumption, refer to optimisation results.")

    return final_results


def filter_services_by_network_type(costs_dict, network_type, services_filter):
    """
    Filter cost services based on network connectivity.

    :param costs_dict: Dict of {service_name: cost_data}
    :param network_type: 'DC' or 'DH'
    :param services_filter: 'all', 'heating_dhw', or 'cooling'
    :return: Filtered dict of {service_name: cost_data}
    """
    if services_filter == 'all':
        return costs_dict

    filtered = {}
    for service_name, service_costs in costs_dict.items():
        # Determine service category
        if services_filter == 'heating_dhw':
            # Include heating and DHW services (exclude cooling)
            if '_hs' in service_name or '_ww' in service_name:
                filtered[service_name] = service_costs
        elif services_filter == 'cooling':
            # Include cooling services only
            if '_cs' in service_name or '_cdata' in service_name or '_cre' in service_name:
                filtered[service_name] = service_costs

    return filtered


def calculate_standalone_building_costs(locator, config, network_name):
    """
    Calculate costs for building-level supply systems (from Properties/Supply).

    This calculates costs for ALL buildings and ALL their services (cooling, heating, DHW).
    Later, when processing each network type (DC/DH), we'll filter which services to include:
    - Buildings in DC network: Include their standalone heating/DHW costs (cooling from network)
    - Buildings in DH network: Include their standalone cooling costs (heating/DHW from network)
    - Buildings in neither network: Include ALL their standalone costs

    This function is called ONCE (not per network_type) to calculate all building-level systems.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param network_name: Network layout name (used to identify which buildings are in networks)
    :return: dict of {building_name: {cost_data, 'services': {service_name: components}}}
    """
    import geopandas as gpd
    import pandas as pd
    import os

    # Read ALL network layouts to determine which buildings are standalone
    # A building is standalone if it's NOT in ANY network layout
    all_network_buildings = set()

    # Check both DH and DC networks if they exist
    for nt in ['DH', 'DC']:
        try:
            network_folder = locator.get_output_thermal_network_type_folder(nt, network_name)
            layout_folder = os.path.join(network_folder, 'layout')
            nodes_file = os.path.join(layout_folder, 'nodes.shp')

            if os.path.exists(nodes_file):
                nodes_df = gpd.read_file(nodes_file)
                network_buildings = nodes_df[nodes_df['type'] == 'CONSUMER']['building'].unique().tolist()
                network_buildings = [b for b in network_buildings if b and b != 'NONE']
                all_network_buildings.update(network_buildings)
        except:
            pass  # Network doesn't exist, that's fine

    # Load domain WITHOUT network_type filter to get ALL services
    print(f"  Loading buildings and demands (all services)...")
    domain_config = cea.config.Configuration()
    domain_config.scenario = config.scenario
    # DON'T set network_type - we want ALL services for standalone buildings

    domain = Domain(domain_config, locator)
    domain.load_buildings()

    # Suppress optimization messages about missing potentials (not relevant for cost calculation)
    import sys
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        domain.load_potentials()
        domain._initialize_energy_system_descriptor_classes()
    finally:
        sys.stdout = old_stdout

    building_potentials = Building.distribute_building_potentials(
        domain.energy_potentials, domain.buildings
    )

    # Store which buildings are in which networks
    dc_network_buildings = set()
    dh_network_buildings = set()
    for nt in ['DH', 'DC']:
        try:
            network_folder = locator.get_output_thermal_network_type_folder(nt, network_name)
            layout_folder = os.path.join(network_folder, 'layout')
            nodes_file = os.path.join(layout_folder, 'nodes.shp')

            if os.path.exists(nodes_file):
                nodes_df = gpd.read_file(nodes_file)
                network_buildings = nodes_df[nodes_df['type'] == 'CONSUMER']['building'].unique().tolist()
                network_buildings = [b for b in network_buildings if b and b != 'NONE']
                if nt == 'DC':
                    dc_network_buildings.update(network_buildings)
                else:
                    dh_network_buildings.update(network_buildings)
        except:
            pass

    # Calculate building-level supply systems for ALL buildings
    # We'll filter services later based on network connectivity
    print(f"  Calculating building-level supply systems for all buildings...")
    print(f"    ({len(domain.buildings)} total, {len(all_network_buildings)} in networks)")

    results = {}
    zero_demand_count = 0

    for building in domain.buildings:
        building.calculate_supply_system(building_potentials[building.identifier])

        if building.stand_alone_supply_system is None:
            zero_demand_count += 1
            results[building.identifier] = {
                'supply_system': None,
                'building': building,
                'costs': {},
                'is_network': False,
                'in_dc_network': building.identifier in dc_network_buildings,
                'in_dh_network': building.identifier in dh_network_buildings
            }
        else:
            # Extract costs from all services
            supply_system = building.stand_alone_supply_system
            # Pass None as network_type to get all services
            costs = extract_costs_from_supply_system(supply_system, None, building)

            # Note: We don't check for missing components here because we don't know yet
            # which services the building will need building-scale equipment for.
            # That check happens later when we filter services based on network connectivity.

            results[building.identifier] = {
                'supply_system': supply_system,
                'building': building,
                'costs': costs,
                'is_network': False,
                'in_dc_network': building.identifier in dc_network_buildings,
                'in_dh_network': building.identifier in dh_network_buildings
            }

    if zero_demand_count > 0:
        print(f"  ({zero_demand_count} building(s) with zero demand)")

    return results


def calculate_district_network_costs(locator, config, network_type, network_name,
                                     network_buildings, building_energy_potentials, domain_potentials):
    """
    Calculate district network costs using district supply types from config.

    This implements Case 1 & 2: Buildings IN network layout use district supply assemblies
    specified in config (supply-type-cs, supply-type-hs, supply-type-dhw).

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

    print(f"  Network {network_id}: {len(network_buildings)} connected buildings")

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

    # Log aggregated demand for network sizing
    print(f"      Peak demand: {aggregated_demand_profile.max():.2f} kW")

    # Aggregate potentials from all buildings in the network
    network_potentials = {}
    for building in network_buildings:
        building_pots = building_energy_potentials.get(building.identifier, {})
        for ec_code, potential in building_pots.items():
            if ec_code in network_potentials:
                network_potentials[ec_code].profile += potential.profile
            else:
                network_potentials[ec_code] = potential

    # Build network supply system using district supply assemblies OR fallback to component categories
    # Two modes:
    # 1. SUPPLY assembly mode: Use specific components from SUPPLY_*_AS* assemblies (preferred)
    # 2. Fallback mode: Use component categories (BOILERS, CHILLERS, etc.) when no assemblies exist

    supply_components = {}
    use_fallback = False

    # Map network_type to the relevant supply category
    if network_type == 'DC':
        supply_code = config.system_costs.supply_type_cs
        # Check if user selected "Use component settings below" or if field is empty
        if supply_code and supply_code != "Use component settings below":
            # SUPPLY assemblies are designed for building-scale systems and may not size correctly
            # for district networks with large aggregated demands.
            # For district networks, fallback mode is recommended.
            print(f"      Note: Using SUPPLY assembly '{supply_code}' for district network")
            print(f"            (SUPPLY assemblies may not size correctly for large demands)")

            # Mode 1: Use SUPPLY assembly (may fail with capacity errors for large networks)
            supply_components = get_components_from_supply_assembly(locator, supply_code, 'SUPPLY_COOLING')
        else:
            # Mode 2: Fallback to component category (RECOMMENDED for district networks)
            print(f"      Using component settings: {config.system_costs.cooling_components}")
            use_fallback = True

    elif network_type == 'DH':
        supply_code_hs = config.system_costs.supply_type_hs
        supply_code_dhw = config.system_costs.supply_type_dhw
        # For DH, we use heating system components (DHW is separate service)
        # Check if user selected "Use component settings below" or if field is empty
        if supply_code_hs and supply_code_hs != "Use component settings below":
            # Mode 1: Use SUPPLY assembly
            print(f"      Using SUPPLY assembly: {supply_code_hs}")
            supply_components = get_components_from_supply_assembly(locator, supply_code_hs, 'SUPPLY_HEATING')
            if supply_components.get('primary'):
                print(f"        Primary components: {supply_components['primary']}")
        else:
            # Mode 2: Fallback to component category
            print(f"      Using component settings: {config.system_costs.heating_components}")
            use_fallback = True

    # Set user_component_selection based on mode
    if use_fallback:
        # Fallback mode: Pass None to let system use all components of the selected category
        # The filtering logic will select the first viable component
        user_component_selection = None
    else:
        # SUPPLY assembly mode: Use specific components from assembly
        # user_component_selection expects dict like: {'primary': ['BO1'], 'secondary': [], 'tertiary': []}
        user_component_selection = supply_components

    max_supply_flow = aggregated_demand.isolate_peak()

    if max_supply_flow.profile.max() == 0.0:
        print(f"      Zero demand - skipping")
        return results

    # Build system structure
    system_structure = SupplySystemStructure(
        max_supply_flow=max_supply_flow,
        available_potentials=network_potentials,
        user_component_selection=user_component_selection,  # None for fallback, dict for SUPPLY assembly
        target_building_or_network=network_id
    )
    system_structure.build()

    # Filter capacity indicators if using fallback mode
    capacity_indicators = system_structure.capacity_indicators

    if use_fallback:
        # Fallback mode: Filter to keep only ONE component per category
        # This prevents sizing all boiler types (BO1-BO6) at full capacity
        capacity_indicators = filter_to_single_component_per_category(capacity_indicators)
        print(f"      Using fallback mode: selected first viable component per category")

    # Create and evaluate supply system
    network_supply_system = SupplySystem(
        system_structure,
        capacity_indicators,
        aggregated_demand
    )

    try:
        network_supply_system.evaluate()
    except ValueError as e:
        if "capacity was insufficient" in str(e):
            # Check if it's an energy carrier mismatch
            installed_primary = network_supply_system.installed_components.get('primary', {})
            if installed_primary:
                comp_list = [f"{code} (capacity={comp.capacity:.0f} kW, EC={comp.main_energy_carrier.code})"
                           for code, comp in installed_primary.items()]
                installed_info = "\n    ".join(comp_list)
            else:
                installed_info = "NONE"

            # Check if activation order is empty
            activation_issue = ""
            if not system_structure.activation_order.get('primary'):
                max_cap_comps = list(system_structure.max_cap_active_components.get('primary', {}).keys())
                activation_issue = (
                    f"\nROOT CAUSE: Component activation order is EMPTY!\n"
                    f"  Installed components: {max_cap_comps}\n"
                    f"  Activation order: {list(system_structure.activation_order.get('primary', []))}\n"
                    f"  This means installed components cannot be activated to meet demand.\n"
                    f"  This is a known limitation when using SUPPLY assemblies.\n\n"
                )

            # Provide helpful error message for capacity issues
            error_msg = (
                f"\n{'='*70}\n"
                f"ERROR: Insufficient capacity for district network '{network_id}'\n"
                f"{'='*70}\n"
                f"{str(e)}\n\n"
                f"Installed primary components:\n    {installed_info}\n"
                f"{activation_issue}"
                f"This error occurs because SUPPLY assemblies specify component codes\n"
                f"that aren't in the optimization framework's activation priority list.\n"
                f"The components are installed but never activated.\n\n"
                f"RECOMMENDED SOLUTION:\n"
                f"  Use 'fallback mode' which uses component CATEGORIES instead of codes:\n"
                f"  1. Set 'supply-type-cs' to 'Use component settings below' (for cooling)\n"
                f"  2. Set 'supply-type-hs' to 'Use component settings below' (for heating)\n"
                f"  3. Select appropriate component categories:\n"
                f"     - cooling-components: ABSORPTION_CHILLERS or VAPOR_COMPRESSION_CHILLERS\n"
                f"     - heating-components: BOILERS\n"
                f"     - heat-rejection-components: COOLING_TOWERS\n\n"
                f"Fallback mode automatically finds ALL viable components and builds\n"
                f"a correct activation order, avoiding this issue.\n"
                f"{'='*70}\n"
            )
            raise ValueError(error_msg) from e
        else:
            # Re-raise other ValueError types
            raise

    # Extract costs from network supply system
    network_costs = extract_costs_from_supply_system(
        network_supply_system, network_type, None
    )

    # Calculate piping costs from thermal-network output files
    piping_cost_annual = 0.0
    piping_cost_total = 0.0

    edges_file = locator.get_thermal_network_edge_list_file(network_type, network_name)
    if not os.path.exists(edges_file):
        print(f"      Warning: Piping costs not calculated - missing file:")
        print(f"               {edges_file}")
        print(f"               Run 'thermal-network' (part 1 & 2) to generate network files")
    else:
        try:
            pipes_df = pd.read_csv(edges_file)

            # Read pipe catalog with unit costs
            pipe_catalog_path = locator.get_database_components_distribution_thermal_grid()
            pipe_catalog_df = pd.read_csv(pipe_catalog_path)

            # Create lookup dict: pipe_DN -> unit cost (USD/m)
            unit_cost_dict = {row['pipe_DN']: row['Inv_USD2015perm']
                             for _, row in pipe_catalog_df.iterrows()}

            # Calculate total piping cost: sum(unit_cost × length)
            piping_cost_total = sum(
                unit_cost_dict.get(row['pipe_DN'], 0.0) * row['length_m']
                for _, row in pipes_df.iterrows()
            )

            # Annualize (default network lifetime: 20 years)
            network_lifetime_yrs = 20.0
            piping_cost_annual = piping_cost_total / network_lifetime_yrs

            print(f"      Piping: ${piping_cost_total:,.2f} total, ${piping_cost_annual:,.2f}/year")
        except Exception as e:
            print(f"      Warning: Failed to calculate piping costs - {str(e)}")
            print(f"               Check that thermal-network files are valid")

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
            print(f"      Piping: ${piping_cost_total:,.2f} total, ${piping_cost_annual:,.2f}/year")
        else:
            print(f"      Warning: Piping costs not included (network object not found)")

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


def calculate_costs_for_network_type(locator, config, network_type, network_name=None, standalone_results=None):
    """
    Calculate costs for either DH or DC using optimization_new engine.

    Four-case logic (network layout is source of truth for connectivity):
    - Case 1 & 2: Building IN network layout → Use district supply types from config (supply-type-cs/hs/dhw)
    - Case 3 & 4: Building NOT in layout → Use existing Properties/Supply configuration (pre-calculated in standalone_results)

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param network_type: 'DH' or 'DC'
    :param network_name: Specific network layout to use (required)
    :param standalone_results: Pre-calculated standalone building costs (dict of {building_name: {cost_data}})
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

    print(f"  Network layout '{network_name}': {len(network_buildings_from_layout)} buildings connected")

    if not network_buildings_from_layout:
        print(f"  ⚠ No buildings connected in {network_type} network layout - skipping")
        return {}

    results = {}

    # Step 2: Add building-level supply system costs
    # For each building, determine which services to include based on network connectivity:
    # - Buildings in DC network: Include their heating/DHW building-scale costs (cooling from district)
    # - Buildings in DH network: Include their cooling building-scale costs (heating/DHW from district)
    # - Buildings in BOTH networks: Include based on which network type we're calculating
    # - Buildings in NO network: Include all services (but only once to avoid duplicates)
    if standalone_results:
        buildings_to_include = []
        for bid, building_data in standalone_results.items():
            in_dc = building_data.get('in_dc_network', False)
            in_dh = building_data.get('in_dh_network', False)

            if not in_dc and not in_dh:
                # Building not in ANY network - include all their services
                # But only in DC results to avoid duplicates in detailed CSV
                if network_type == 'DC':
                    buildings_to_include.append((bid, 'all'))
            elif in_dc and not in_dh:
                # Building in DC network only - include their heating/DHW building-scale components
                # (cooling comes from DC network)
                if network_type == 'DC':
                    buildings_to_include.append((bid, 'heating_dhw'))
            elif in_dh and not in_dc:
                # Building in DH network only - include their cooling building-scale components
                # (heating/DHW comes from DH network)
                if network_type == 'DH':
                    buildings_to_include.append((bid, 'cooling'))
            elif in_dc and in_dh:
                # Building in BOTH networks - NO building-scale components needed
                # All services (cooling from DC, heating/DHW from DH) come from networks
                pass

        if buildings_to_include:
            print(f"\n  Including building-level supply systems:")
            print(f"    {len([b for b, s in buildings_to_include if s == 'all'])} building(s) with all services")
            if network_type == 'DC':
                print(f"    {len([b for b, s in buildings_to_include if s == 'heating_dhw'])} building(s) in DC network with heating/DHW")
            else:
                print(f"    {len([b for b, s in buildings_to_include if s == 'cooling'])} building(s) in DH network with cooling")

            for building_id, services_filter in buildings_to_include:
                building_data = standalone_results[building_id]
                # Filter services based on network connectivity
                filtered_costs = filter_services_by_network_type(building_data['costs'], network_type, services_filter)

                # Check if building has demand for required services but no components
                # This helps identify missing database configuration
                import pandas as pd
                demand_df = pd.read_csv(locator.get_total_demand())
                building_demand = demand_df[demand_df['name'] == building_id]
                if not building_demand.empty:
                    qhs = building_demand['Qhs_sys_MWhyr'].values[0] if 'Qhs_sys_MWhyr' in building_demand.columns else 0
                    qww = building_demand['Qww_sys_MWhyr'].values[0] if 'Qww_sys_MWhyr' in building_demand.columns else 0
                    qcs = building_demand['Qcs_sys_MWhyr'].values[0] if 'Qcs_sys_MWhyr' in building_demand.columns else 0

                    missing_services = []
                    if services_filter == 'all':
                        # Standalone building - check all services
                        if qhs > 0 and not any('_hs' in s for s in filtered_costs.keys()):
                            missing_services.append(f'heating ({qhs:.1f} MWh/yr)')
                        if qww > 0 and not any('_ww' in s for s in filtered_costs.keys()):
                            missing_services.append(f'DHW ({qww:.1f} MWh/yr)')
                        if qcs > 0 and not any('_cs' in s for s in filtered_costs.keys()):
                            missing_services.append(f'cooling ({qcs:.1f} MWh/yr)')
                    elif services_filter == 'heating_dhw':
                        # Building in DC network - needs building-scale heating/DHW
                        if qhs > 0 and not any('_hs' in s for s in filtered_costs.keys()):
                            missing_services.append(f'heating ({qhs:.1f} MWh/yr)')
                        if qww > 0 and not any('_ww' in s for s in filtered_costs.keys()):
                            missing_services.append(f'DHW ({qww:.1f} MWh/yr)')
                    elif services_filter == 'cooling':
                        # Building in DH network - needs building-scale cooling
                        if qcs > 0 and not any('_cs' in s for s in filtered_costs.keys()):
                            missing_services.append(f'cooling ({qcs:.1f} MWh/yr)')

                    if missing_services:
                        print(f"    ⚠ {building_id}: Has demand but missing components for {', '.join(missing_services)} "
                              f"(check Properties/Supply settings and Database/Components)")

                result_copy = building_data.copy()
                result_copy['costs'] = filtered_costs
                result_copy['network_type'] = network_type
                results[building_id] = result_copy

    # Step 3: Calculate district network costs (Case 1 & 2)
    # These buildings use district supply types from config, not Properties/Supply settings
    # Load domain ONLY for network-connected buildings to calculate their costs
    print(f"\n  Calculating district network central plant costs...")

    import cea.config
    domain_config = cea.config.Configuration()
    domain_config.scenario = config.scenario
    domain_config.optimization_new.network_type = network_type

    # Set component priorities for fallback mode (when SUPPLY assemblies don't exist)
    # These will be used by SupplySystemStructure when user_component_selection=None
    # Note: All component parameters are now MultiChoiceParameter (already lists)
    domain_config.optimization_new.cooling_components = config.system_costs.cooling_components if config.system_costs.cooling_components else []
    domain_config.optimization_new.heating_components = config.system_costs.heating_components if config.system_costs.heating_components else []
    domain_config.optimization_new.heat_rejection_components = config.system_costs.heat_rejection_components if config.system_costs.heat_rejection_components else []

    domain = Domain(domain_config, locator)
    # IMPORTANT: Only load network-connected buildings to avoid errors with buildings that don't have
    # systems for this network_type (e.g., Singapore buildings with SUPPLY_HEATING_AS0 when network_type=DH)
    domain.load_buildings(buildings_in_domain=network_buildings_from_layout)

    # Load potentials and initialize classes
    # Suppress optimization messages about missing potentials (not relevant for cost calculation)
    import sys
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        domain.load_potentials()
        domain._initialize_energy_system_descriptor_classes()
    finally:
        sys.stdout = old_stdout

    # Calculate base case supply systems
    building_energy_potentials = Building.distribute_building_potentials(
        domain.energy_potentials, domain.buildings
    )

    # All buildings in domain are network-connected (we filtered in load_buildings)
    network_connected_buildings = domain.buildings


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
                    'components': [],
                    'energy_costs': []  # Track energy costs separately for detailed output
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
    # Note: supply_system.annual_cost contains BOTH component costs and energy costs
    # Component costs (CH1, CT1, BO1, etc.) are already extracted in step 1 above
    # Here we only extract energy carrier costs (E230AC, NATURALGAS, etc.)

    # Component codes to skip (already extracted in step 1)
    component_codes = set()
    for placement_dict in supply_system.installed_components.values():
        for component_code in placement_dict.keys():
            component_codes.add(component_code)

    for ec_code, annual_cost in supply_system.annual_cost.items():
        # Skip non-numeric entries
        if not isinstance(annual_cost, (int, float)):
            continue

        # Skip component codes (already extracted in step 1)
        if ec_code in component_codes:
            continue

        # Map energy carrier to service (e.g., NATURALGAS → NG_hs, E230AC → GRID_cs)
        service_name = map_energy_carrier_to_service(ec_code, network_type)

        # Warn about unmapped energy carriers with significant costs
        if not service_name and annual_cost > 1000:
            print(f"    WARNING: Unmapped energy carrier '{ec_code}' with cost ${annual_cost:,.2f}/year")

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
                    'components': [],
                    'energy_costs': []  # Track energy costs separately for detailed output
                }

            # Energy costs are already annual and variable
            costs[service_name]['opex_var_USD'] += annual_cost
            costs[service_name]['opex_a_var_USD'] += annual_cost

            # Add energy cost entry for detailed output
            # (not a physical component, but needs to appear in detailed report)
            costs[service_name]['energy_costs'].append({
                'carrier': ec_code,
                'opex_var_USD': annual_cost,
                'opex_a_var_USD': annual_cost
            })

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
    :param network_type: 'DH', 'DC', or None (for all services)
    :param building: Building instance (or None for network-level systems)
    :return: Service name string (e.g., 'NG_hs', 'GRID_cs', 'GRID_ww')
    """
    # Get component code first to help determine service type
    comp_code = component.code if hasattr(component, 'code') else str(component)

    # Determine service suffix
    # For network-level systems, use network_type to determine suffix
    # For building-level systems with network_type=None, infer from component type
    if network_type == 'DH':
        suffix = '_hs'  # heating service
    elif network_type == 'DC':
        suffix = '_cs'  # cooling service
    else:
        # network_type is None - need to infer service type from component
        # Check if component is for cooling, heating, or DHW
        if comp_code.startswith('CH') or comp_code.startswith('VCCH') or comp_code.startswith('ACH') or comp_code.startswith('CT'):
            # Chillers and cooling towers → cooling service
            suffix = '_cs'
        elif comp_code.startswith('BO') or comp_code.startswith('HP'):
            # Boilers and heat pumps could be for heating OR DHW
            # We need to check the component's output energy carrier to distinguish
            # For now, use the main_energy_carrier's temperature to determine
            if hasattr(component, 'output_energy_carrier') and hasattr(component.output_energy_carrier, 'code'):
                ec_code = component.output_energy_carrier.code
                # T60W is for heating, T10W or lower temps for DHW
                if 'T60W' in ec_code or 'T80W' in ec_code or 'T90W' in ec_code:
                    suffix = '_hs'  # space heating
                else:
                    suffix = '_ww'  # DHW (usually T10W-T40W)
            else:
                # Fallback: assume heating if we can't determine
                suffix = '_hs'
        else:
            # Default to heating for unknown components
            suffix = '_hs'

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
    # Note: Energy carrier codes come from optimization_new (e.g., 'E230AC' for electricity)
    carrier_map = {
        'NATURALGAS': 'NG',
        'E230AC': 'GRID',  # Electricity (grid)
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


def main(config: cea.config.Configuration):
    """
    Main entry point for baseline-costs script.

    :param config: Configuration instance
    """
    locator = InputLocator(config.scenario)
    baseline_costs_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())


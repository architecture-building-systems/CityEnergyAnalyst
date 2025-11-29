"""
Baseline costs for supply systems using detailed component specifications.

This script calculates costs for baseline supply systems using the same calculation
engine as optimization_new, providing accurate component-level cost breakdowns.

Replaces the deprecated system_costs.py with more detailed calculations.
"""

import os
import pandas as pd
from cea.inputlocator import InputLocator
from cea.optimization_new.domain import Domain
from cea.optimization_new.building import Building
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


def filter_supply_code_by_scale(locator, supply_codes, category, is_standalone):
    """
    Filter multi-select supply codes based on building context (standalone vs district-connected).

    When supply_type parameters are multi-select (list of codes), filter to return only the
    appropriate code based on the building's connectivity state:
    - Standalone buildings → Use BUILDING-scale assembly
    - District-connected buildings → Use DISTRICT-scale assembly

    :param locator: InputLocator instance
    :param supply_codes: Single code (str) or list of codes from multi-select parameter
    :param category: 'SUPPLY_COOLING', 'SUPPLY_HEATING', or 'SUPPLY_HOTWATER'
    :param is_standalone: True if building is standalone, False if connected to district network
    :return: Single supply code (str) or None if no match
    """
    # Handle single value (backward compatibility with non-multi-select configs)
    if isinstance(supply_codes, str):
        return supply_codes

    # Handle multi-select list
    if not isinstance(supply_codes, list) or len(supply_codes) == 0:
        return None

    # If only one code selected, use it regardless of scale
    if len(supply_codes) == 1:
        return supply_codes[0]

    # Map category to locator method
    category_to_method = {
        'SUPPLY_COOLING': locator.get_database_assemblies_supply_cooling,
        'SUPPLY_HEATING': locator.get_database_assemblies_supply_heating,
        'SUPPLY_HOTWATER': locator.get_database_assemblies_supply_hot_water,
    }

    method = category_to_method.get(category)
    if not method:
        return supply_codes[0]  # Fallback to first code

    filepath = method()
    if not pd.io.common.file_exists(filepath):
        return supply_codes[0]

    df = pd.read_csv(filepath)

    # Determine target scale based on building connectivity
    target_scale = 'BUILDING' if is_standalone else 'DISTRICT'

    # Filter codes by target scale
    for code in supply_codes:
        row = df[df['code'] == code]
        if not row.empty and 'scale' in row.columns:
            scale = row['scale'].iloc[0]
            if str(scale).upper() == target_scale:
                return code

    # Fallback: return first code if no scale match found
    return supply_codes[0]


def get_component_codes_from_categories(locator, component_categories, network_type, peak_demand_kw=None):
    """
    Convert component category names to actual component codes from the database.

    :param locator: InputLocator instance
    :param component_categories: List of category names like ['VAPOR_COMPRESSION_CHILLERS', 'BOILERS']
    :param network_type: 'DH' or 'DC'
    :param peak_demand_kw: Optional peak demand in kW - if provided, only return codes that can handle this capacity
    :return: List of component codes like ['CH1', 'CH2', 'BO1', 'BO2']
    """
    import pandas as pd

    component_codes = []

    for category in component_categories:
        # Read the appropriate conversion technology database using the correct method
        db_path = locator.get_db4_components_conversion_conversion_technology_csv(category)
        df = pd.read_csv(db_path)

        if peak_demand_kw is not None:
            # Filter to only codes that can handle the peak demand
            # Check if the peak demand falls within any capacity range for this code
            peak_demand_w = peak_demand_kw * 1000  # Convert to W

            # Group by code and check if peak_demand_w can be covered
            valid_codes = []
            for code in df['code'].dropna().unique():
                code_data = df[df['code'] == code]
                # Check if any row has a cap_max >= peak_demand_w
                if (code_data['cap_max'] >= peak_demand_w).any():
                    valid_codes.append(code)

            component_codes.extend(valid_codes)
        else:
            # No filtering - get all codes
            codes = df['code'].dropna().unique().tolist()
            component_codes.extend(codes)

    return component_codes


def get_dhw_component_fallback(locator, building_identifier, feedstock):
    """
    Get fallback DHW component code based on feedstock type.

    This is used when SUPPLY_HOTWATER assembly doesn't specify components.
    The function matches the feedstock to appropriate boiler type from COMPONENTS database.

    :param locator: InputLocator instance
    :param building_identifier: Building name (for error messages)
    :param feedstock: Feedstock code from SUPPLY_HOTWATER assembly ('GRID', 'NATURALGAS', etc.)
    :return: Component code string (e.g., 'BO5' for electrical boiler) or None if no match
    """
    import pandas as pd

    # Map feedstock to fuel_code in BOILERS.csv
    # Based on databases/SG/COMPONENTS/CONVERSION/BOILERS.csv
    feedstock_to_fuel = {
        'GRID': 'E230AC',      # Electrical boiler (BO5)
        'NATURALGAS': 'Cgas',  # Natural gas boiler (BO1/BO3)
        'Cgas': 'Cgas',        # Direct fuel code
        'OIL': 'Coil',         # Oil boiler (BO2)
        'Coil': 'Coil',        # Direct fuel code
        'COAL': 'Ccoa',        # Coal boiler (BO4)
        'Ccoa': 'Ccoa',        # Direct fuel code
        'WOOD': 'Cwod',        # Wood boiler (BO6)
        'Cwod': 'Cwod',        # Direct fuel code
    }

    fuel_code = feedstock_to_fuel.get(feedstock)
    if not fuel_code:
        print(f"    ⚠ {building_identifier}: Cannot find DHW component for feedstock '{feedstock}'")
        return None

    # Read boilers database
    boilers_path = locator.get_db4_components_conversion_conversion_technology_csv('BOILERS')
    if not pd.io.common.file_exists(boilers_path):
        print(f"    ⚠ {building_identifier}: BOILERS database not found at {boilers_path}")
        return None

    boilers_df = pd.read_csv(boilers_path)

    # Find matching boiler by fuel_code
    matching_boilers = boilers_df[boilers_df['fuel_code'] == fuel_code]

    if matching_boilers.empty:
        print(f"    ⚠ {building_identifier}: No boiler found for fuel '{fuel_code}'")
        return None

    # Get the first matching boiler code
    # For electrical: BO5
    # For natural gas: BO1 (conventional) or BO3 (condensing) - prefer BO1 for simplicity
    # For oil: BO2
    component_code = matching_boilers['code'].iloc[0]

    return component_code


def apply_dhw_component_fallback(locator, building, supply_system):
    """
    Apply DHW component fallback when SUPPLY_HOTWATER assembly has no components.

    This function:
    1. Reads the building's supply_type_dhw from supply.csv
    2. Gets the feedstock from SUPPLY_HOTWATER.csv
    3. Matches feedstock to boiler component (e.g., GRID → BO5)
    4. Creates a synthetic DHW supply system with that component
    5. Calculates and returns costs for DHW service

    :param locator: InputLocator instance
    :param building: Building instance (or minimal building with just .identifier attribute)
    :param supply_system: Existing heating supply system (for reference, can be None)
    :return: dict of DHW service costs or None if fallback fails
    """
    import pandas as pd
    from cea.optimization_new.containerclasses.supplySystemStructure import SupplySystemStructure
    from cea.optimization_new.supplySystem import SupplySystem
    from cea.optimization_new.containerclasses.energyFlow import EnergyFlow
    from cea.optimization_new.domain import Domain
    from cea.optimization_new.component import Component
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

    # Read DHW demand to size the system
    demand_df = pd.read_csv(locator.get_total_demand())
    building_demand = demand_df[demand_df['name'] == building.identifier]

    if building_demand.empty:
        return None

    # Get DHW demand profile from building's demand file
    # Use Qww_sys_kWh column which is the hourly DHW demand
    building_demand_file = locator.get_demand_results_file(building.identifier)
    if not pd.io.common.file_exists(building_demand_file):
        return None

    hourly_demand_df = pd.read_csv(building_demand_file)
    if 'Qww_sys_kWh' not in hourly_demand_df.columns:
        return None

    dhw_demand_profile = hourly_demand_df['Qww_sys_kWh']  # pandas Series, not .values (numpy array)

    # Skip if zero demand
    if dhw_demand_profile.max() == 0:
        return None

    # Create DHW demand flow
    # DHW typically requires medium temperature water (T60W, 60°C)
    # Boilers with T_water_out_rating=80°C will now produce T60W after energyCarrier.py fix
    # (when equidistant from T60W and T100W, prefer lower temperature to minimise energy waste)
    dhw_demand_flow = EnergyFlow(
        input_category='primary',
        output_category='consumer',
        energy_carrier_code='T60W',  # Medium temperature for DHW (physically correct)
        energy_flow_profile=dhw_demand_profile
    )

    # Initialize Component class if not already done
    # This is needed to map component codes to their energy carriers
    if Component.code_to_class_mapping is None:
        # Create a minimal domain just to initialize Component class
        domain_config_dhw = cea.config.Configuration()
        # Get scenario from locator (locator.scenario is the current scenario path)
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
        available_potentials={},  # No potentials for DHW fallback
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

    try:
        dhw_supply_system.evaluate()
    except Exception as e:
        print(f"    ⚠ {building.identifier}: Failed to evaluate DHW fallback system - {e}")
        return None

    # Extract costs from DHW supply system
    # Use 'DH' as network_type to indicate this is a heating-related service
    dhw_costs = extract_costs_from_supply_system(dhw_supply_system, 'DH', building)

    # Rename services to include '_ww' suffix for DHW
    dhw_costs_renamed = {}
    for service_name, service_costs in dhw_costs.items():
        # Change service suffix from '_hs' to '_ww'
        if '_hs' in service_name:
            new_service_name = service_name.replace('_hs', '_ww')
            dhw_costs_renamed[new_service_name] = service_costs
        else:
            dhw_costs_renamed[service_name] = service_costs

    return dhw_costs_renamed




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
            "Please run 'thermal-network' script (both part 1 and part 2) before running baseline-costs.\n"
            "Alternatively, select a different network layout that has been completed."
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

    # Get network name - can be None/empty to assess all buildings as standalone
    network_name = config.system_costs.network_name

    print(f"\n{'='*70}")
    print("BASELINE COSTS CALCULATION")
    print(f"{'='*70}")

    # Check if user selected "(none)" - assess all buildings as standalone
    if not network_name or network_name == '':
        print("Mode: STANDALONE ONLY (all buildings assessed as standalone systems)")
        print("District-scale supply systems will be treated as building-scale for cost calculations.")
        print(f"Network types (for supply system selection): {', '.join(network_types)}")

        # Calculate ALL buildings as standalone (ignore district-scale designation)
        all_results = calculate_all_buildings_as_standalone(locator, config, network_types)

        # Format using the same formatter as normal mode
        merged_results = merge_network_type_costs(all_results)
        from cea.analysis.costs.format_simplified import format_output_simplified
        final_results, detailed_results = format_output_simplified(merged_results, locator)

        # Save results
        print(f"\n{'-'*70}")
        print("Saving results...")
        locator.ensure_parent_folder_exists(locator.get_baseline_costs())
        final_results.to_csv(locator.get_baseline_costs(), index=False, float_format='%.2f', na_rep='nan')
        detailed_results.to_csv(locator.get_baseline_costs_detailed(), index=False, float_format='%.2f', na_rep='nan')

        print(f"\n{'='*70}")
        print("COMPLETED (Standalone Mode)")
        print(f"{'='*70}")
        print(f"Summary: {locator.get_baseline_costs()}")
        print(f"Detailed: {locator.get_baseline_costs_detailed()}")
        print(f"\nNote: Standalone-only mode provides simplified cost estimates")
        return

    print(f"Mode: NETWORK + STANDALONE")
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
            "See errors above."
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

    # Merge results from all network types (but don't format yet)
    merged_results = merge_network_type_costs(all_results)

    # Calculate solar panel costs
    print(f"\n{'-'*70}")
    print("Calculating solar panel costs...")
    from cea.analysis.costs.solar_costs import calculate_building_solar_costs, merge_solar_costs_to_buildings

    # Get list of all building names for solar calculation
    all_building_names = []
    for building_name in merged_results.keys():
        if building_name not in ['DC', 'DH']:  # Exclude network-level entries
            all_building_names.append(building_name)

    solar_details, solar_summary = calculate_building_solar_costs(config, locator, all_building_names)

    # Merge and format all results (after solar costs are calculated)
    print(f"\n{'-'*70}")
    print("Merging and formatting results...")
    from cea.analysis.costs.format_simplified import format_output_simplified
    final_results, detailed_results = format_output_simplified(merged_results, locator)

    # Append solar details to costs_components.csv
    if not solar_details.empty:
        detailed_results = pd.concat([detailed_results, solar_details], ignore_index=True)
        print(f"  Added {len(solar_details)} solar panel component rows")

    # Add/update solar costs in costs_buildings.csv
    if not solar_summary.empty:
        final_results = merge_solar_costs_to_buildings(final_results, solar_summary)
        print(f"  Updated costs for {len(solar_summary)} buildings with solar panels")

    # Sort results by building name
    final_results = final_results.sort_values('name').reset_index(drop=True)
    detailed_results = detailed_results.sort_values('name').reset_index(drop=True)

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
        print("\nNote: Network costs include central plant equipment and piping.")
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


def calculate_all_buildings_as_standalone(locator, config, network_types):
    """
    Calculate costs treating ALL buildings as standalone systems.
    This is used when network-name is "(none)" or empty.

    District-scale supply systems are treated as if they were building-scale
    for cost calculation purposes. Network type selection is IGNORED - results
    are saved for both DH and DC for compatibility with existing output format.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param network_types: List of network types (ignored but results saved for all types)
    :return: dict of {network_type: {building_name: cost_data}}
    """
    print(f"\n{'-'*70}")
    print("Calculating ALL buildings as standalone systems...")
    print("NOTE: Network-type selection is ignored - all services calculated")

    # Get all buildings in scenario
    building_names = locator.get_zone_building_names()
    print(f"  Total buildings: {len(building_names)}")

    # We need to calculate costs for ALL services
    # Strategy: Call calculate_standalone_building_costs twice (once for DC, once for DH)
    # Then merge the results

    print("  Loading cooling systems (DC)...")
    # First get cooling system costs
    try:
        # Temporarily override config to DC
        original_network_type = config.system_costs.network_type if hasattr(config.system_costs, 'network_type') else None

        # Create a domain config for DC (cooling)
        domain_config_dc = cea.config.Configuration()
        domain_config_dc.scenario = config.scenario
        domain_config_dc.optimization_new.network_type = 'DC'

        domain_dc = Domain(domain_config_dc, locator)
        domain_dc.load_buildings()  # Load all buildings (network_name=None means all are standalone)

        # Set all buildings to standalone mode
        for building in domain_dc.buildings:
            building.initial_connectivity_state = 'stand_alone'

        # Suppress potentials loading messages
        import sys, io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            domain_dc.load_potentials()
            domain_dc._initialize_energy_system_descriptor_classes()
        finally:
            sys.stdout = old_stdout

        building_potentials_dc = Building.distribute_building_potentials(
            domain_dc.energy_potentials, domain_dc.buildings
        )

        # Calculate cooling costs for each building
        results_dc = {}
        for building in domain_dc.buildings:
            building.calculate_supply_system(building_potentials_dc[building.identifier])
            if building.stand_alone_supply_system:
                # Extract cooling service costs - use the same format as calculate_standalone_building_costs
                supply_system = building.stand_alone_supply_system
                costs = extract_costs_from_supply_system(supply_system, 'DC', building)

                results_dc[building.identifier] = {
                    'supply_system': supply_system,
                    'building': building,
                    'costs': costs,
                    'is_network': False,
                    'in_dc_network': False,
                    'in_dh_network': False
                }

        print(f"    ✓ Calculated cooling costs for {len(results_dc)} buildings with systems")
    except Exception as e:
        print(f"    ! No cooling systems: {e}")
        results_dc = {}

    print("  Loading heating systems (DH)...")
    # Then get heating/DHW system costs
    try:
        domain_config_dh = cea.config.Configuration()
        domain_config_dh.scenario = config.scenario
        domain_config_dh.optimization_new.network_type = 'DH'

        domain_dh = Domain(domain_config_dh, locator)

        # Try to load buildings - this may fail if ALL buildings have zero heating demand
        # (e.g., Singapore scenario where all buildings have SUPPLY_HEATING_AS0 with no components)
        try:
            domain_dh.load_buildings()
        except ValueError as e:
            if "Network type mismatch" in str(e):
                # All buildings have zero heating demand - but may have DHW demand
                # Skip loading DH domain and apply DHW fallback for all buildings later
                print("    ⚠ All buildings have zero heating demand")
                print("      Attempting DHW-only cost calculation...")

                # Manually process DHW for each building without loading DH domain
                building_names = locator.get_zone_building_names()
                results_dh = {}
                dhw_fallback_count = 0

                for building_name in building_names:
                    # Create minimal building object for DHW fallback
                    class MinimalBuilding:
                        def __init__(self, identifier):
                            self.identifier = identifier
                            self.initial_connectivity_state = 'stand_alone'  # Required by map_component_to_service

                    minimal_building = MinimalBuilding(building_name)
                    dhw_costs = apply_dhw_component_fallback(locator, minimal_building, None)

                    if dhw_costs:
                        results_dh[building_name] = {
                            'supply_system': None,
                            'building': minimal_building,
                            'costs': dhw_costs,
                            'is_network': False,
                            'in_dc_network': False,
                            'in_dh_network': False
                        }
                        dhw_fallback_count += 1

                if dhw_fallback_count > 0:
                    print(f"    ✓ Applied DHW component fallback for {dhw_fallback_count} building(s)")

                # Skip the rest of DH processing and jump to merging results
                raise StopIteration("DHW-only processing complete")
            else:
                # Re-raise other errors
                raise

        # Set all buildings to standalone mode
        for building in domain_dh.buildings:
            building.initial_connectivity_state = 'stand_alone'

        # Suppress potentials loading messages
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            domain_dh.load_potentials()
            domain_dh._initialize_energy_system_descriptor_classes()
        finally:
            sys.stdout = old_stdout

        building_potentials_dh = Building.distribute_building_potentials(
            domain_dh.energy_potentials, domain_dh.buildings
        )

        # Calculate heating/DHW costs for each building
        results_dh = {}
        dhw_fallback_count = 0
        for building in domain_dh.buildings:
            try:
                building.calculate_supply_system(building_potentials_dh[building.identifier])
            except ValueError as e:
                # Skip buildings with zero heating demand or no heating components
                if "Network type mismatch" in str(e) or "None of the components chosen" in str(e):
                    # Building has zero heating demand - but may still have DHW demand
                    # Try to apply DHW fallback directly
                    dhw_costs = apply_dhw_component_fallback(locator, building, None)
                    if dhw_costs:
                        results_dh[building.identifier] = {
                            'supply_system': None,
                            'building': building,
                            'costs': dhw_costs,
                            'is_network': False,
                            'in_dc_network': False,
                            'in_dh_network': False
                        }
                        dhw_fallback_count += 1
                    continue
                else:
                    # Re-raise other errors
                    raise

            if building.stand_alone_supply_system:
                # Extract heating/DHW service costs - use the same format
                supply_system = building.stand_alone_supply_system
                costs = extract_costs_from_supply_system(supply_system, 'DH', building)

                # Check if DHW costs are missing and apply fallback
                has_dhw_costs = any('_ww' in service_name for service_name in costs.keys())
                if not has_dhw_costs:
                    # Check if building has DHW demand
                    demand_df = pd.read_csv(locator.get_total_demand())
                    building_demand = demand_df[demand_df['name'] == building.identifier]
                    if not building_demand.empty:
                        qww = building_demand['Qww_sys_MWhyr'].values[0] if 'Qww_sys_MWhyr' in building_demand.columns else 0
                        if qww > 0:
                            # Building has DHW demand but no costs - apply fallback
                            dhw_costs = apply_dhw_component_fallback(locator, building, supply_system)
                            if dhw_costs:
                                costs.update(dhw_costs)
                                dhw_fallback_count += 1

                results_dh[building.identifier] = {
                    'supply_system': supply_system,
                    'building': building,
                    'costs': costs,
                    'is_network': False,
                    'in_dc_network': False,
                    'in_dh_network': False
                }

        print(f"    ✓ Calculated heating/DHW costs for {len(results_dh)} buildings with systems")
        if dhw_fallback_count > 0:
            print(f"    ✓ Applied DHW component fallback for {dhw_fallback_count} building(s)")
    except StopIteration as e:
        # DHW-only processing completed successfully (from line 710)
        # results_dh is already populated, just continue
        pass
    except Exception as e:
        print(f"    ! No heating systems: {e}")
        results_dh = {}

    # Merge results from both network types
    # Need to merge costs dictionaries properly (not just overwrite)
    merged_results = {}
    all_building_names = set(list(results_dc.keys()) + list(results_dh.keys()))

    for building_name in all_building_names:
        # Start with base structure from one of the results
        if building_name in results_dc:
            merged_results[building_name] = results_dc[building_name].copy()
            merged_costs = results_dc[building_name]['costs'].copy()
        elif building_name in results_dh:
            merged_results[building_name] = results_dh[building_name].copy()
            merged_costs = results_dh[building_name]['costs'].copy()
        else:
            continue

        # Merge costs from the other network type if present
        if building_name in results_dc and building_name in results_dh:
            # Merge costs from DH results into DC costs
            dh_costs = results_dh[building_name]['costs']
            for service_name, service_costs in dh_costs.items():
                if service_name not in merged_costs:
                    merged_costs[service_name] = service_costs
                # If service exists in both, keep one (shouldn't happen with DC vs DH)

        merged_results[building_name]['costs'] = merged_costs

    # Return results only under DC to avoid duplicates in output
    # DC is used as the "primary" network type for standalone-only mode
    results_by_network_type = {
        'DC': merged_results
    }

    print("  ✓ Standalone cost calculations completed")
    return results_by_network_type


def apply_supply_code_fallback_for_standalone(locator, config, building, is_in_dc_network, is_in_dh_network):
    """
    Apply config fallback when building's supply.csv has wrong scale for standalone service.

    This implements Case 3/5/6: When building provides its own service (not from network),
    check if supply.csv has district-scale code. If so, use config parameter filtered to
    building scale as fallback.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param building: Building object
    :param is_in_dc_network: True if building is in DC network
    :param is_in_dh_network: True if building is in DH network
    :return: dict of {service: fallback_code} or {} if no fallback needed
    """
    import pandas as pd

    fallbacks = {}

    # Read building's supply.csv
    supply_csv_path = locator.get_building_supply()
    if not os.path.exists(supply_csv_path):
        return fallbacks

    supply_df = pd.read_csv(supply_csv_path)
    building_row = supply_df[supply_df['name'] == building.identifier]

    if building_row.empty:
        return fallbacks

    # Helper to check if supply code is wrong scale
    def get_scale(supply_code, category):
        if not supply_code or supply_code == '':
            return None

        category_to_method = {
            'SUPPLY_COOLING': locator.get_database_assemblies_supply_cooling,
            'SUPPLY_HEATING': locator.get_database_assemblies_supply_heating,
            'SUPPLY_HOTWATER': locator.get_database_assemblies_supply_hot_water,
        }

        filepath = category_to_method.get(category)()
        if not os.path.exists(filepath):
            return None

        df = pd.read_csv(filepath)
        row = df[df['code'] == supply_code]
        if not row.empty and 'scale' in row.columns:
            return row['scale'].iloc[0]
        return None

    # Check each service the building provides (not from network)
    services_to_check = []

    if not is_in_dc_network:  # Building provides own cooling
        services_to_check.append(('supply_type_cs', 'SUPPLY_COOLING', config.system_costs.supply_type_cs))

    if not is_in_dh_network:  # Building provides own heating/DHW
        services_to_check.append(('supply_type_hs', 'SUPPLY_HEATING', config.system_costs.supply_type_hs))
        services_to_check.append(('supply_type_dhw', 'SUPPLY_HOTWATER', config.system_costs.supply_type_dhw))

    for column, category, config_value in services_to_check:
        if column not in building_row.columns:
            continue

        csv_code = building_row[column].iloc[0]
        scale = get_scale(csv_code, category)

        # If CSV has district scale, but building is standalone for this service
        if scale == 'DISTRICT':
            # Use config as fallback, filter to BUILDING scale
            fallback_code = filter_supply_code_by_scale(
                locator, config_value, category, is_standalone=True
            )
            if fallback_code:
                fallbacks[column] = fallback_code

    return fallbacks


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
    import os

    # Read ALL network layouts to determine which buildings are standalone
    # A building is standalone if it's NOT in ANY network layout
    # If network_name is None, treat ALL buildings as standalone
    all_network_buildings = set()

    if network_name:
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

    # Load domain - use DC as default (will load all buildings with their demands)
    print("  Loading buildings and demands...")
    domain_config = cea.config.Configuration()
    domain_config.scenario = config.scenario
    domain_config.optimization_new.network_type = 'DC'

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
    print("  Calculating building-level supply systems for all buildings...")
    print(f"    ({len(domain.buildings)} total, {len(all_network_buildings)} in networks)")

    # Apply supply code fallbacks BEFORE calculating supply systems
    supply_csv_path = locator.get_building_supply()
    if os.path.exists(supply_csv_path):
        supply_df = pd.read_csv(supply_csv_path)
        fallback_count = 0

        for building in domain.buildings:
            is_in_dc = building.identifier in dc_network_buildings
            is_in_dh = building.identifier in dh_network_buildings

            # Get fallbacks if needed
            fallbacks = apply_supply_code_fallback_for_standalone(
                locator, config, building, is_in_dc, is_in_dh
            )

            # Apply fallbacks to supply.csv
            if fallbacks:
                fallback_count += 1
                building_row_idx = supply_df[supply_df['name'] == building.identifier].index
                if len(building_row_idx) > 0:
                    for column, fallback_code in fallbacks.items():
                        supply_df.at[building_row_idx[0], column] = fallback_code

        # Write back modified supply.csv temporarily
        if fallback_count > 0:
            print(f"  Applied config fallbacks for {fallback_count} standalone building(s) with wrong scale in supply.csv")
            supply_df.to_csv(supply_csv_path, index=False)

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
        supply_code_raw = config.system_costs.supply_type_cs
        # Filter multi-select codes for district scale (is_standalone=False)
        supply_code = filter_supply_code_by_scale(locator, supply_code_raw, 'SUPPLY_COOLING', is_standalone=False)

        # Check if user selected "Use component settings below" or if field is empty
        if supply_code and supply_code != "Use component settings below":
            # SUPPLY assemblies are designed for building-scale systems and may not size correctly
            # for district networks with large aggregated demands.
            # For district networks, fallback mode is recommended.
            print(f"      Note: Using SUPPLY assembly '{supply_code}' for district network")
            print("            (SUPPLY assemblies may not size correctly for large demands)")

            # Mode 1: Use SUPPLY assembly (may fail with capacity errors for large networks)
            supply_components = get_components_from_supply_assembly(locator, supply_code, 'SUPPLY_COOLING')
        else:
            # Mode 2: Fallback to component category (RECOMMENDED for district networks)
            print(f"      Using component settings: {config.system_costs.cooling_components}")
            use_fallback = True

    elif network_type == 'DH':
        supply_code_hs_raw = config.system_costs.supply_type_hs
        supply_code_dhw_raw = config.system_costs.supply_type_dhw
        # Filter multi-select codes for district scale (is_standalone=False)
        supply_code_hs = filter_supply_code_by_scale(locator, supply_code_hs_raw, 'SUPPLY_HEATING', is_standalone=False)
        supply_code_dhw = filter_supply_code_by_scale(locator, supply_code_dhw_raw, 'SUPPLY_HOTWATER', is_standalone=False)

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

    # Calculate peak demand first to filter components by capacity
    max_supply_flow = aggregated_demand.isolate_peak()

    if max_supply_flow.profile.max() == 0.0:
        print(f"      Zero demand - skipping")
        return results

    # Get peak demand in kW for component filtering
    # max_supply_flow.profile is already in kW
    peak_demand_kw = max_supply_flow.profile.max()

    # Set user_component_selection based on mode
    if use_fallback:
        # Fallback mode: Build explicit component selection based on network type
        # This prevents SupplySystemStructure from including ALL components from database
        user_component_selection = {}

        if network_type == 'DC':
            # District Cooling: only cooling components (primary) and heat rejection (tertiary)
            # Use the categories specified in config
            cooling_cats = config.system_costs.cooling_components if config.system_costs.cooling_components else []
            heat_rejection_cats = config.system_costs.heat_rejection_components if config.system_costs.heat_rejection_components else []

            # For baseline costs, exclude absorption chillers as they require heat sources in secondary category
            # which adds complexity beyond the scope of baseline cost estimation
            cooling_cats_simple = [cat for cat in cooling_cats if 'ABSORPTION' not in cat]
            if len(cooling_cats_simple) < len(cooling_cats):
                print(f"      Note: Excluding absorption chillers for baseline costs (require heat source configuration)")
                print(f"            Using: {cooling_cats_simple}")

            # Convert component categories to actual component codes from database
            # Filter by peak demand to only include codes that can handle the required capacity
            cooling_codes = get_component_codes_from_categories(locator, cooling_cats_simple, network_type, peak_demand_kw)
            heat_rejection_codes = get_component_codes_from_categories(locator, heat_rejection_cats, network_type, peak_demand_kw)

            # For baseline costs, use only the FIRST viable component per category
            # This gives a simple, conservative baseline estimate rather than an optimized mix
            # e.g., prefer CH1 (centrifugal) over CH2 (reciprocating) for large systems
            cooling_primary = cooling_codes[:1] if cooling_codes else []
            heat_rejection_tertiary = heat_rejection_codes[:1] if heat_rejection_codes else []

            # Cooling goes in primary, heat rejection in tertiary
            user_component_selection['primary'] = cooling_primary  # e.g., ['CH1'] only
            user_component_selection['secondary'] = []  # No heating for DC
            user_component_selection['tertiary'] = heat_rejection_tertiary  # e.g., ['CT1'] only

        elif network_type == 'DH':
            # District Heating: only heating components (primary/secondary)
            heating_cats = config.system_costs.heating_components if config.system_costs.heating_components else []

            # Convert component categories to actual component codes
            # Filter by peak demand to only include codes that can handle the required capacity
            heating_codes = get_component_codes_from_categories(locator, heating_cats, network_type, peak_demand_kw)

            # For baseline costs, use only the FIRST viable component
            # This gives a simple, conservative baseline estimate rather than an optimized mix
            heating_primary = heating_codes[:1] if heating_codes else []

            user_component_selection['primary'] = heating_primary  # e.g., ['BO1'] only (filtered by capacity)
            user_component_selection['secondary'] = []
            user_component_selection['tertiary'] = []  # No heat rejection for DH
    else:
        # SUPPLY assembly mode: Use specific components from assembly
        # user_component_selection expects dict like: {'primary': ['BO1'], 'secondary': [], 'tertiary': []}
        user_component_selection = supply_components

    # Build system structure
    system_structure = SupplySystemStructure(
        max_supply_flow=max_supply_flow,
        available_potentials=network_potentials,
        user_component_selection=user_component_selection,  # None for fallback, dict for SUPPLY assembly
        target_building_or_network=network_id
    )
    system_structure.build()

    # Get capacity indicators from system structure
    # No filtering needed since we explicitly selected components in user_component_selection
    capacity_indicators = system_structure.capacity_indicators

    # No debug output needed - system is working correctly

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
                    "\nROOT CAUSE: Component activation order is EMPTY!\n"
                    f"  Installed components: {max_cap_comps}\n"
                    f"  Activation order: {list(system_structure.activation_order.get('primary', []))}\n"
                    "  This means installed components cannot be activated to meet demand.\n"
                    "  This is a known limitation when using SUPPLY assemblies.\n\n"
                )

            # Provide helpful error message for capacity issues
            error_msg = (
                f"\n{'='*70}\n"
                f"ERROR: Insufficient capacity for district network '{network_id}'\n"
                f"{'='*70}\n"
                f"{str(e)}\n\n"
                f"Installed primary components:\n    {installed_info}\n"
                f"{activation_issue}"
                "This error occurs because SUPPLY assemblies specify component codes\n"
                "that aren't in the optimization framework's activation priority list.\n"
                "The components are installed but never activated.\n\n"
                "RECOMMENDED SOLUTION:\n"
                "  Use 'fallback mode' which uses component CATEGORIES instead of codes:\n"
                "  1. Set 'supply-type-cs' to 'Use component settings below' (for cooling)\n"
                "  2. Set 'supply-type-hs' to 'Use component settings below' (for heating)\n"
                "  3. Select appropriate component categories:\n"
                "     - cooling-components: ABSORPTION_CHILLERS or VAPOR_COMPRESSION_CHILLERS\n"
                "     - heating-components: BOILERS\n"
                "     - heat-rejection-components: COOLING_TOWERS\n\n"
                "Fallback mode automatically finds ALL viable components and builds\n"
                "a correct activation order, avoiding this issue.\n"
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
        print("      Warning: Piping costs not calculated - missing file:")
        print(f"               {edges_file}")
        print("               Run 'thermal-network' (part 1 & 2) to generate network files")
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
            print("               Check that thermal-network files are valid")

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
            print("\n  Including building-level supply systems:")
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
                              "(check Properties/Supply settings and Database/Components)")

                result_copy = building_data.copy()
                result_copy['costs'] = filtered_costs
                result_copy['network_type'] = network_type
                results[building_id] = result_copy

    # Step 3: Calculate district network costs (Case 1 & 2)
    # These buildings use district supply types from config, not Properties/Supply settings
    # Load domain ONLY for network-connected buildings to calculate their costs
    print("\n  Calculating district network central plant costs...")

    import cea.config
    domain_config = cea.config.Configuration()
    domain_config.scenario = config.scenario
    domain_config.optimization_new.network_type = network_type

    # Set component priorities for fallback mode (when SUPPLY assemblies don't exist)
    # These will be used by SupplySystemStructure when user_component_selection=None
    # Note: All component parameters are now MultiChoiceParameter (already lists)
    # IMPORTANT: Only set components relevant to this network type
    if network_type == 'DC':
        # District Cooling: only cooling and heat rejection components
        domain_config.optimization_new.cooling_components = config.system_costs.cooling_components if config.system_costs.cooling_components else []
        domain_config.optimization_new.heating_components = []  # No heating for DC
        domain_config.optimization_new.heat_rejection_components = config.system_costs.heat_rejection_components if config.system_costs.heat_rejection_components else []
    elif network_type == 'DH':
        # District Heating: only heating components, no cooling
        domain_config.optimization_new.cooling_components = []  # No cooling for DH
        domain_config.optimization_new.heating_components = config.system_costs.heating_components if config.system_costs.heating_components else []
        domain_config.optimization_new.heat_rejection_components = []  # No heat rejection for DH

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
    # Note: Energy carrier codes come from COMPONENTS/FEEDSTOCKS/ENERGY_CARRIERS.csv
    # Format: {carrier_code: service_prefix}
    carrier_map = {
        # Electrical carriers (E prefix)
        'E230AC': 'GRID',   # Electricity - low voltage
        'E22kAC': 'GRID',   # Electricity - medium voltage
        'E66kAC': 'GRID',   # Electricity - high voltage
        'GRID': 'GRID',     # Legacy/generic electricity

        # Fossil fuels (C prefix)
        'Cgas': 'NG',       # Natural gas
        'NATURALGAS': 'NG', # Legacy natural gas
        'Coil': 'OIL',      # Oil
        'OIL': 'OIL',       # Legacy oil
        'Ccoa': 'COAL',     # Coal
        'COAL': 'COAL',     # Legacy coal

        # Biofuels (C prefix)
        'Cwod': 'WOOD',     # Wood
        'WOOD': 'WOOD',     # Legacy wood
        'Cbig': 'BIOGAS',   # Biogas
        'Cwbm': 'WETBIOMASS',  # Wet biomass
        'Cdbm': 'DRYBIOMASS',  # Dry biomass
        'Chyd': 'HYDROGEN', # Hydrogen

        # District networks
        'DH': 'DH',         # District heating
        'DC': 'DC',         # District cooling
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


"""
Supply system cost calculation functions for baseline costs.

This module contains the core cost calculation logic for supply systems,
including standalone buildings and district networks. The main entry point
and orchestration logic is in main.py.
"""

import os
import pandas as pd
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
    # Helper to strip scale labels like '(building)' or '(district)'
    def strip_label(value):
        if not value:
            return value
        for suffix in [' (building)', ' (district)']:
            if value.endswith(suffix):
                return value[:-len(suffix)]
        return value

    # Handle single value (backward compatibility with non-multi-select configs)
    if isinstance(supply_codes, str):
        return strip_label(supply_codes)

    # Handle multi-select list
    if not isinstance(supply_codes, list) or len(supply_codes) == 0:
        return None

    # If only one code selected, use it regardless of scale
    if len(supply_codes) == 1:
        return strip_label(supply_codes[0])

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
    for code_with_label in supply_codes:
        code = strip_label(code_with_label)  # Strip label before database lookup
        row = df[df['code'] == code]
        if not row.empty and 'scale' in row.columns:
            scale = row['scale'].iloc[0]
            if str(scale).upper() == target_scale:
                return code  # Return bare code without label

    # Fallback: return first code if no scale match found
    return strip_label(supply_codes[0])


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
    # DHW fallback is always for standalone buildings
    dhw_costs = extract_costs_from_supply_system(dhw_supply_system, 'DH', building, is_network_building=False)

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


def calculate_all_buildings_as_standalone(locator, config):
    """
    Calculate costs treating ALL buildings as standalone systems.
    This is used when network-name is "(none)" or empty.

    Uses the regular standalone building calculation which respects SUPPLY assembly configuration.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :return: dict of {network_type: {building_name: cost_data}}
    """
    print(f"\n{'-'*70}")
    print("Calculating ALL buildings as standalone systems...")

    # Calculate all buildings as standalone (network_name=None means all buildings are standalone)
    # This function returns dict of {building_name: cost_data} for ALL buildings
    all_results = calculate_standalone_building_costs(locator, config, network_name=None)

    print("  ✓ Standalone cost calculations completed")

    # Return results in the expected format: {network_type: {building: costs}}
    # For standalone mode, we put all results under 'DH' to match expected structure
    return {'DH': all_results, 'DC': {}}


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


def get_network_buildings(locator, network_name, network_type):
    """
    Get list of buildings connected to a specific network.

    :param locator: InputLocator instance
    :param network_name: Network layout name
    :param network_type: 'DH' or 'DC'
    :return: set of building identifiers in the network
    """
    import geopandas as gpd
    import os

    if not network_name or network_name == "(none)":
        return set()

    try:
        network_folder = locator.get_output_thermal_network_type_folder(network_type, network_name)
        layout_folder = os.path.join(network_folder, 'layout')
        nodes_file = os.path.join(layout_folder, 'nodes.shp')

        if os.path.exists(nodes_file):
            nodes_df = gpd.read_file(nodes_file)
            network_buildings = nodes_df[nodes_df['type'] == 'CONSUMER']['building'].unique().tolist()
            return set([b for b in network_buildings if b and b != 'NONE'])
    except Exception:
        pass

    return set()


def get_all_building_ids(locator):
    """
    Get all building IDs from zone geometry.

    :param locator: InputLocator instance
    :return: set of all building identifiers
    """
    import geopandas as gpd
    zone_df = gpd.read_file(locator.get_zone_geometry())
    return set(zone_df['name'].tolist())


def determine_building_service_needs(network_name, network_types_selected, dh_network_buildings, dc_network_buildings, all_building_ids):
    """
    Determine which services each building needs at building-level.
    Implements 4-case logic based on network selection.

    :param network_name: Network layout name
    :param network_types_selected: list of network types selected (e.g. ['DH', 'DC'])
    :param dh_network_buildings: set of building IDs in DH network
    :param dc_network_buildings: set of building IDs in DC network
    :param all_building_ids: set of all building IDs
    :return: dict of {building_id: {'needs_heating': bool, 'needs_cooling': bool, 'needs_dhw': bool, 'case': int}}
    """
    service_needs = {}

    # Check if networks are selected (based on config, not building presence)
    no_network = (network_name == "(none)" or not network_name)
    dh_selected = 'DH' in network_types_selected
    dc_selected = 'DC' in network_types_selected

    for bid in all_building_ids:
        in_dh = bid in dh_network_buildings
        in_dc = bid in dc_network_buildings

        if no_network:
            # Case 1: No network - all building-level
            service_needs[bid] = {
                'needs_heating': True,
                'needs_cooling': True,
                'needs_dhw': True,
                'case': 1
            }

        elif dc_selected and not dh_selected:
            # Case 2: Only DC network selected
            service_needs[bid] = {
                'needs_heating': True,      # Always building-level
                'needs_cooling': not in_dc, # Building-level if NOT in DC network
                'needs_dhw': True,          # Always building-level
                'case': 2
            }

        elif dh_selected and not dc_selected:
            # Case 3: Only DH network selected
            service_needs[bid] = {
                'needs_heating': not in_dh, # Building-level if NOT in DH network
                'needs_cooling': True,      # Always building-level (DC not selected!)
                'needs_dhw': not in_dh,     # Building-level if NOT in DH network
                'case': 3
            }

        elif dc_selected and dh_selected:
            # Case 4: Both DC and DH networks selected
            service_needs[bid] = {
                'needs_heating': not in_dh, # Building-level if NOT in DH network
                'needs_cooling': not in_dc, # Building-level if NOT in DC network
                'needs_dhw': not in_dh,     # Building-level if NOT in DH network
                'case': 4
            }

    return service_needs


def calculate_standalone_building_costs(locator, config, network_name):
    """
    Calculate costs for building-level supply systems.
    Implements 4-case logic for network scenarios.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param network_name: Network layout name
    :return: dict of {building_name: {cost_data}}
    """
    import os

    print("  Loading buildings and demands...")

    # 0. Determine STANDALONE mode or NETWORK mode
    if network_name is None or network_name == "(none)":
        all_buildings_standalone = True
    else:
        all_buildings_standalone = False

    # 1. Get network connectivity
    if all_buildings_standalone:
        dh_network_buildings = set()
        dc_network_buildings = set()
    else:
        dh_network_buildings = get_network_buildings(locator, network_name, 'DH')
        dc_network_buildings = get_network_buildings(locator, network_name, 'DC')

    # 2. Get all building IDs
    all_building_ids = get_all_building_ids(locator)

    # 3. Get which network types are selected from config
    network_types_selected = config.system_costs.network_type

    # 4. Determine which services each building needs at building-level (4-case logic)
    service_needs = determine_building_service_needs(
        network_name, network_types_selected, dh_network_buildings, dc_network_buildings, all_building_ids
    )

    print(f"  Found {len(dh_network_buildings)} buildings in DH network")
    print(f"  Found {len(dc_network_buildings)} buildings in DC network")
    print(f"  Total buildings: {len(all_building_ids)}")
    print(f"  Network types selected: {network_types_selected}")
    if all_buildings_standalone:
        print("All thermal services are provided at the BUILDING level.")

    # 5. Apply Level 1 fallback: Config fallback for scale mismatch
    apply_config_fallbacks_for_service_needs(locator, config, service_needs, dh_network_buildings, dc_network_buildings)

    # 6. Calculate heating systems (for buildings that need building-level heating/DHW)
    heating_results = calculate_heating_systems(locator, config, service_needs, dh_network_buildings, dc_network_buildings)

    # 7. Calculate cooling systems (for buildings that need building-level cooling)
    cooling_results = calculate_cooling_systems(locator, config, service_needs, dh_network_buildings, dc_network_buildings)

    # 8. Merge heating and cooling results
    results = merge_heating_cooling_results(heating_results, cooling_results, service_needs, dh_network_buildings, dc_network_buildings)

    # 9. Apply Level 3 fallback: DHW component fallback for buildings with DHW demand but no heating components
    # This handles DHW-only buildings (common in tropical climates with zero space heating demand)
    import pandas as pd
    demand_df = pd.read_csv(locator.get_total_demand())

    for bid in all_building_ids:
        building_demand = demand_df[demand_df['name'] == bid]
        if building_demand.empty:
            continue

        qww = building_demand['Qww_sys_MWhyr'].values[0] if 'Qww_sys_MWhyr' in building_demand.columns else 0

        # Check if building has DHW demand but no DHW components in results
        if qww > 0:
            has_dhw_service = False
            if bid in results and 'costs' in results[bid]:
                has_dhw_service = any('_ww' in service for service in results[bid]['costs'].keys())

            if not has_dhw_service:
                # Building has DHW demand but no DHW components - apply fallback
                # Get building data from heating_results if available
                if bid in heating_results and heating_results[bid].get('building'):
                    building_obj = heating_results[bid]['building']
                    supply_system = heating_results[bid].get('supply_system')

                    # Apply DHW fallback
                    dhw_costs = apply_dhw_component_fallback(locator, building_obj, supply_system)

                    if dhw_costs:
                        # Add DHW costs to results
                        if bid not in results:
                            results[bid] = {
                                'building': building_obj,
                                'supply_system': supply_system,
                                'costs': {},
                                'in_dc_network': bid in dc_network_buildings,
                                'in_dh_network': bid in dh_network_buildings
                            }
                        results[bid]['costs'].update(dhw_costs)

    return results


def apply_config_fallbacks_for_service_needs(locator, config, service_needs, dh_network_buildings, dc_network_buildings):
    """
    Apply Level 1 fallback: Config fallback for scale mismatch.
    Modifies supply.csv temporarily before calculating supply systems.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param service_needs: dict of building service needs
    :param dh_network_buildings: set of buildings in DH network
    :param dc_network_buildings: set of buildings in DC network
    """
    import pandas as pd
    import os

    supply_csv_path = locator.get_building_supply()
    if not os.path.exists(supply_csv_path):
        return

    supply_df = pd.read_csv(supply_csv_path)
    fallback_count = 0

    for bid, needs in service_needs.items():
        # Determine if building needs fallback for each service
        is_in_dc = bid in dc_network_buildings
        is_in_dh = bid in dh_network_buildings

        # Create a mock building object for fallback function
        class MockBuilding:
            def __init__(self, identifier):
                self.identifier = identifier

        mock_building = MockBuilding(bid)

        # Get fallbacks if needed
        fallbacks = apply_supply_code_fallback_for_standalone(
            locator, config, mock_building, is_in_dc, is_in_dh
        )

        # Apply fallbacks to supply.csv
        if fallbacks:
            fallback_count += 1
            building_row_idx = supply_df[supply_df['name'] == bid].index
            if len(building_row_idx) > 0:
                for column, fallback_code in fallbacks.items():
                    supply_df.at[building_row_idx[0], column] = fallback_code

    # Write back modified supply.csv temporarily
    if fallback_count > 0:
        print(f"  Applied config fallbacks for {fallback_count} building(s) with scale mismatch")
        supply_df.to_csv(supply_csv_path, index=False)


def calculate_heating_systems(locator, config, service_needs, dh_network_buildings, dc_network_buildings):
    """
    Calculate heating systems only for buildings that need building-level heating/DHW.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param service_needs: dict of building service needs
    :param dh_network_buildings: set of buildings in DH network
    :param dc_network_buildings: set of buildings in DC network
    :return: dict of {building_id: {'building': Building, 'supply_system': SupplySystem, 'costs': dict}}
    """
    from cea.optimization_new.domain import Domain
    from cea.optimization_new.building import Building

    # Get buildings that need heating/DHW at building-level
    buildings_needing_heating = [bid for bid, needs in service_needs.items()
                                  if needs['needs_heating'] or needs['needs_dhw']]

    if not buildings_needing_heating:
        print("  No buildings need building-level heating systems")
        return {}

    print(f"  Calculating heating systems for {len(buildings_needing_heating)} building(s)...")

    # Load DH domain - create config for DH
    domain_config = cea.config.Configuration()
    domain_config.scenario = config.scenario
    domain_config.optimization_new.network_type = 'DH'
    domain_config.optimization_new.network_name = None
    domain = Domain(domain_config, locator)
    domain.load_buildings(buildings_needing_heating)

    if len(domain.buildings) == 0:
        print("  No buildings with heating demand found")
        return {}

    # Load potentials (suppress messages)
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

    # Calculate systems
    results = {}
    zero_demand_count = 0

    # For heating: only mark as district scale if DH network is selected
    network_types_selected = config.system_costs.network_type
    dh_selected = 'DH' in network_types_selected

    # Suppress individual "No supply system components (DHW-only)" messages
    old_stdout2 = sys.stdout
    sys.stdout = io.StringIO()
    try:
        for building in domain.buildings:
            building.calculate_supply_system(building_potentials[building.identifier])

            if building.stand_alone_supply_system is None:
                zero_demand_count += 1
                results[building.identifier] = {
                    'building': building,
                    'supply_system': None,
                    'costs': {},
                    'in_dc_network': building.identifier in dc_network_buildings,
                    'in_dh_network': building.identifier in dh_network_buildings
                }
            else:
                # Mark as district scale only if building is in DH network AND DH is selected
                is_network_building = (building.identifier in dh_network_buildings) and dh_selected
                costs = extract_costs_from_supply_system(
                    building.stand_alone_supply_system, None, building, is_network_building
                )

                results[building.identifier] = {
                    'building': building,
                    'supply_system': building.stand_alone_supply_system,
                    'costs': costs,
                    'in_dc_network': building.identifier in dc_network_buildings,
                    'in_dh_network': building.identifier in dh_network_buildings
                }
    finally:
        sys.stdout = old_stdout2

    if zero_demand_count > 0:
        print(f"{zero_demand_count} building(s) with DHW-only (no heating components) - will use heating-component fallback")

    return results


def calculate_cooling_systems(locator, config, service_needs, dh_network_buildings, dc_network_buildings):
    """
    Calculate cooling systems only for buildings that need building-level cooling.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :param service_needs: dict of building service needs
    :param dh_network_buildings: set of buildings in DH network
    :param dc_network_buildings: set of buildings in DC network
    :return: dict of {building_id: {'building': Building, 'supply_system': SupplySystem, 'costs': dict}}
    """
    from cea.optimization_new.domain import Domain
    from cea.optimization_new.building import Building

    # Get buildings that need cooling at building-level
    buildings_needing_cooling = [bid for bid, needs in service_needs.items()
                                  if needs['needs_cooling']]

    if not buildings_needing_cooling:
        print("  No buildings need building-level cooling systems")
        return {}

    print(f"  Calculating cooling systems for {len(buildings_needing_cooling)} building(s)...")
    print(f"    Buildings: {sorted(buildings_needing_cooling)[:10]}...")

    # Load DC domain - create config for DC
    domain_config = cea.config.Configuration()
    domain_config.scenario = config.scenario
    domain_config.optimization_new.network_type = 'DC'
    domain_config.optimization_new.network_name = None
    domain = Domain(domain_config, locator)
    domain.load_buildings(buildings_needing_cooling)

    print(f"    Domain loaded {len(domain.buildings)} buildings with cooling demand")
    if len(domain.buildings) > 0:
        print(f"    Buildings loaded: {sorted([b.identifier for b in domain.buildings])}")

    if len(domain.buildings) == 0:
        print("  No buildings with cooling demand found")
        return {}

    # Load potentials (suppress messages)
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

    # Calculate systems
    results = {}
    zero_demand_count = 0

    # For cooling: only mark as district scale if DC network is selected
    network_types_selected = config.system_costs.network_type
    dc_selected = 'DC' in network_types_selected

    for building in domain.buildings:
        building.calculate_supply_system(building_potentials[building.identifier])

        if building.stand_alone_supply_system is None:
            zero_demand_count += 1
            results[building.identifier] = {
                'building': building,
                'supply_system': None,
                'costs': {},
                'in_dc_network': building.identifier in dc_network_buildings,
                'in_dh_network': building.identifier in dh_network_buildings
            }
        else:
            # Mark as district scale only if building is in DC network AND DC is selected
            is_network_building = (building.identifier in dc_network_buildings) and dc_selected
            costs = extract_costs_from_supply_system(
                building.stand_alone_supply_system, None, building, is_network_building
            )

            results[building.identifier] = {
                'building': building,
                'supply_system': building.stand_alone_supply_system,
                'costs': costs,
                'in_dc_network': building.identifier in dc_network_buildings,
                'in_dh_network': building.identifier in dh_network_buildings
            }

    if zero_demand_count > 0:
        print(f"    ({zero_demand_count} building(s) with zero demand)")

    return results


def merge_heating_cooling_results(heating_results, cooling_results, service_needs, dh_network_buildings, dc_network_buildings):
    """
    Merge heating and cooling supply systems.

    :param heating_results: dict of heating results
    :param cooling_results: dict of cooling results
    :param service_needs: dict of building service needs
    :param dh_network_buildings: set of buildings in DH network
    :param dc_network_buildings: set of buildings in DC network
    :return: dict of merged results
    """
    print("  Merging heating and cooling systems...")

    all_results = heating_results.copy()
    merge_count = 0

    for bid, cooling_data in cooling_results.items():
        if bid in all_results:
            # Building has both heating and cooling - merge systems
            heating_system = all_results[bid]['supply_system']
            cooling_system = cooling_data['supply_system']

            if heating_system and cooling_system:
                # Merge components
                for placement, components in cooling_system.installed_components.items():
                    if placement not in heating_system.installed_components:
                        heating_system.installed_components[placement] = {}
                    heating_system.installed_components[placement].update(components)

                # Merge costs
                heating_system.annual_cost.update(cooling_system.annual_cost)

                # Re-extract costs with merged system
                is_network_building = (bid in dc_network_buildings or bid in dh_network_buildings)
                all_results[bid]['costs'] = extract_costs_from_supply_system(
                    heating_system, None, all_results[bid]['building'], is_network_building
                )
                merge_count += 1
            elif cooling_system and not heating_system:
                # Only cooling system exists (DHW-only building in DH network)
                all_results[bid]['supply_system'] = cooling_system
                all_results[bid]['costs'] = cooling_data['costs']
                merge_count += 1
        else:
            # Cooling-only building (not in heating_results)
            all_results[bid] = cooling_data

    if merge_count > 0:
        print(f"  Merged systems for {merge_count} building(s)")

    return all_results


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

        # Check if user selected "Custom (use component settings below)" or if field is empty
        if supply_code and supply_code != "Custom (use component settings below)":
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
        # Check if user selected "Custom (use component settings below)" or if field is empty
        if supply_code_hs and supply_code_hs != "Custom (use component settings below)":
            # Mode 1: Use SUPPLY assembly
            print(f"      Using SUPPLY assembly (heating): {supply_code_hs}")
            if supply_code_dhw and supply_code_dhw != "Custom (use component settings below)":
                print(f"      Using SUPPLY assembly (DHW): {supply_code_dhw}")
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
        print("      Zero demand - skipping")
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
                print("      Note: Excluding absorption chillers for baseline costs (require heat source configuration)")
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
                "  1. Set 'supply-type-cs' to 'Custom (use component settings below)' (for cooling)\n"
                "  2. Set 'supply-type-hs' to 'Custom (use component settings below)' (for heating)\n"
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
    # Network central plant is district-scale infrastructure
    network_costs = extract_costs_from_supply_system(
        network_supply_system, network_type, None, is_network_building=True
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
            print(f"  {network_id}: Zero demand - skipping this network")
            continue

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
        # Network infrastructure is district-scale
        network_costs = extract_costs_from_supply_system(
            network_supply_system, network_type, None, is_network_building=True
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
            print("      Warning: Piping costs not included (network object not found)")

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


def calculate_costs_for_network_type(locator, config, network_type, network_name=None, standalone_results=None, all_selected_network_types=None):
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
    :param all_selected_network_types: list of ALL selected network types (e.g., ['DH'] or ['DH', 'DC'])
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

    # Check if network layout files exist
    if not os.path.exists(layout_folder):
        print(f"  ⚠ Network layout folder not found for {network_type} network '{network_name}' - skipping")
        print(f"    Expected: {layout_folder}")
        print("    Please run 'thermal-network' (part 1 and 2) first")
        return {}

    if not os.path.exists(nodes_file):
        print(f"  ⚠ Network nodes file not found for {network_type} network '{network_name}' - skipping")
        print(f"    Expected: {nodes_file}")
        print("    Please run 'thermal-network' (part 1 and 2) first")
        return {}

    # Try to read network layout
    try:
        nodes_df = gpd.read_file(nodes_file)
        network_buildings_from_layout = nodes_df[nodes_df['type'] == 'CONSUMER']['building'].unique().tolist()
        network_buildings_from_layout = [b for b in network_buildings_from_layout if b and b != 'NONE']
    except Exception as e:
        print(f"  ⚠ Failed to read network layout for {network_type} network '{network_name}' - skipping")
        print(f"    Error: {str(e)}")
        print(f"    File: {nodes_file}")
        return {}

    print(f"  Network layout '{network_name}': {len(network_buildings_from_layout)} buildings connected")

    if not network_buildings_from_layout:
        print(f"  ⚠ No buildings connected in {network_type} network layout - skipping")
        return {}

    results = {}

    # Step 2: Add building-level supply system costs
    # For each building, determine which services to include based on:
    # 1. Network connectivity (whether building is IN network layout)
    # 2. Network selection (which networks are SELECTED by user)
    #
    # Logic:
    # - Cooling building-level: If building NOT in DC layout OR DC not selected
    # - Heating/DHW building-level: If building NOT in DH layout OR DH not selected
    if standalone_results:
        # Default to current network type if not provided
        if all_selected_network_types is None:
            all_selected_network_types = [network_type]

        dc_selected = 'DC' in all_selected_network_types
        dh_selected = 'DH' in all_selected_network_types

        buildings_to_include = []
        for bid, building_data in standalone_results.items():
            in_dc = building_data.get('in_dc_network', False)
            in_dh = building_data.get('in_dh_network', False)

            # Determine which services this building needs at building-level
            # Based on BOTH connectivity AND selection
            needs_cooling_building_level = (not in_dc) or (not dc_selected)
            needs_heating_dhw_building_level = (not in_dh) or (not dh_selected)

            # Determine what to include
            if needs_cooling_building_level and needs_heating_dhw_building_level:
                # Building needs ALL services at building-level
                # Only include in DC results to avoid duplicates
                if network_type == 'DC':
                    buildings_to_include.append((bid, 'all'))
            elif needs_heating_dhw_building_level and not needs_cooling_building_level:
                # Building needs heating/DHW at building-level, cooling from DC
                if network_type == 'DC':
                    buildings_to_include.append((bid, 'heating_dhw'))
            elif needs_cooling_building_level and not needs_heating_dhw_building_level:
                # Building needs cooling at building-level, heating/DHW from DH
                if network_type == 'DH':
                    buildings_to_include.append((bid, 'cooling'))
            else:
                # Building gets ALL services from district networks
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

                    # Try DHW fallback if DHW is missing
                    if qww > 0 and not any('_ww' in s for s in filtered_costs.keys()):
                        if services_filter in ['all', 'heating_dhw']:
                            # Try to apply DHW component fallback
                            dhw_costs = apply_dhw_component_fallback(locator, building_data['building'], building_data['supply_system'])
                            if dhw_costs:
                                # Merge DHW costs into filtered_costs
                                filtered_costs.update(dhw_costs)

                    # Check for remaining missing services after fallback attempts
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


def extract_costs_from_supply_system(supply_system, network_type, building, is_network_building=False):
    """
    Extract cost metrics from optimization_new supply system.

    :param supply_system: SupplySystem instance from optimization_new
    :param network_type: 'DH' or 'DC' or None (for standalone buildings)
    :param building: Building instance (or None for network-level systems)
    :param is_network_building: True if building is connected to network, False for standalone
    :return: dict of cost metrics by service
    """
    costs = {}

    # 1. Component costs (CAPEX + fixed OPEX)
    for placement, components_dict in supply_system.installed_components.items():
        for component_code, component in components_dict.items():

            # Map component to energy service (e.g., BO1 → NG_hs, HP1 → GRID_hs)
            service_name = map_component_to_service(component, network_type, building)

            # Determine scale based on actual network connectivity (not assembly scale)
            scale = determine_scale(building, placement, is_network_building)

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

        # For standalone systems (network_type=None), if mapping returns None (ambiguous carrier like GRID),
        # try to infer service by matching carrier prefix to existing cost entries
        if not service_name and network_type is None:
            # Extract carrier prefix from energy carrier code
            carrier_prefix = ec_code.split('_')[0] if '_' in ec_code else ec_code
            # Map carrier code to carrier prefix using the same logic as map_energy_carrier_to_service
            carrier_map = {
                'E230AC': 'GRID', 'E22kAC': 'GRID', 'E66kAC': 'GRID', 'GRID': 'GRID',
                'Cgas': 'NG', 'NATURALGAS': 'NG', 'Coil': 'OIL', 'OIL': 'OIL',
                'Ccoa': 'COAL', 'COAL': 'COAL', 'Cwod': 'WOOD', 'WOOD': 'WOOD',
                'Cbig': 'BIOGAS', 'Cwbm': 'WETBIOMASS', 'Cdbm': 'DRYBIOMASS', 'Chyd': 'HYDROGEN'
            }
            carrier_prefix = carrier_map.get(ec_code, carrier_prefix)

            # Search existing costs for a matching service (e.g., GRID_hs, GRID_cs)
            for existing_service in costs.keys():
                if existing_service.startswith(f"{carrier_prefix}_"):
                    service_name = existing_service
                    break

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
                    'scale': determine_scale(building, 'primary', is_network_building),
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


def determine_scale(building, placement, is_network_building=False):
    """
    Determine if system is building, district, or city scale.

    :param building: Building instance (or None for network systems)
    :param placement: Component placement (primary/secondary/tertiary)
    :param is_network_building: True if building is actually connected to a network, False for standalone
    :return: 'BUILDING', 'DISTRICT', or 'CITY'
    """
    # If building is None, this is a network-level system
    if building is None:
        return 'DISTRICT'

    # For standalone mode, always return BUILDING regardless of assembly scale
    # (assemblies might say DISTRICT but building is actually standalone)
    if not is_network_building:
        return 'BUILDING'

    # Building is actually in a network - return DISTRICT
    return 'DISTRICT'


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

    # Map based on component's actual input energy carriers (from database)
    # This is flexible and works with any custom database structure

    # Try to get the primary input energy carrier from the component
    carrier = None

    if hasattr(component, 'input_energy_carriers') and component.input_energy_carriers:
        # Get the first (primary) input energy carrier
        primary_input = component.input_energy_carriers[0] if isinstance(component.input_energy_carriers, list) else list(component.input_energy_carriers.values())[0]

        if hasattr(primary_input, 'code'):
            ec_code = primary_input.code

            # Map energy carrier code to service prefix
            # Based on COMPONENTS/FEEDSTOCKS/ENERGY_CARRIERS.csv
            carrier_map = {
                # Electrical carriers
                'E230AC': 'GRID', 'E22kAC': 'GRID', 'E66kAC': 'GRID',
                # Fossil fuels
                'Cgas': 'NG', 'Coil': 'OIL', 'Ccoa': 'COAL',
                # Biofuels
                'Cwod': 'WOOD', 'Cbig': 'BIOGAS', 'Cwbm': 'WETBIOMASS',
                'Cdbm': 'DRYBIOMASS', 'Chyd': 'HYDROGEN',
                # District networks
                'DH': 'DH', 'DC': 'DC'
            }

            carrier = carrier_map.get(ec_code)

    # Fallback: Check if this is a network-level system
    if not carrier:
        if building is None or (hasattr(building, 'initial_connectivity_state') and
                                building.initial_connectivity_state != 'stand_alone'):
            if network_type == 'DH':
                carrier = 'DH'
            elif network_type == 'DC':
                carrier = 'DC'

    # Final fallback: Default to GRID if we couldn't determine carrier
    if not carrier:
        carrier = 'GRID'

    return f"{carrier}{suffix}"


def map_energy_carrier_to_service(ec_code, network_type):
    """
    Map energy carrier code to service name.

    :param ec_code: Energy carrier code from optimization_new
    :param network_type: 'DH', 'DC', or None (for standalone systems)
    :return: Service name string or None if not applicable
    """
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
        'Cgas': 'NG',        # Natural gas
        'NATURALGAS': 'NG',  # Legacy natural gas
        'Coil': 'OIL',       # Oil
        'OIL': 'OIL',        # Legacy oil
        'Ccoa': 'COAL',      # Coal
        'COAL': 'COAL',      # Legacy coal

        # Biofuels (C prefix)
        'Cwod': 'WOOD',      # Wood
        'WOOD': 'WOOD',      # Legacy wood
        'Cbig': 'BIOGAS',    # Biogas
        'Cwbm': 'WETBIOMASS',  # Wet biomass
        'Cdbm': 'DRYBIOMASS',  # Dry biomass
        'Chyd': 'HYDROGEN',  # Hydrogen

        # District networks
        'DH': 'DH',         # District heating
        'DC': 'DC',         # District cooling
    }

    # Heating carriers (fuels typically used for heating)
    heating_carriers = {'NG', 'OIL', 'COAL', 'WOOD', 'BIOGAS', 'WETBIOMASS', 'DRYBIOMASS', 'HYDROGEN', 'DH'}
    # Cooling carriers
    cooling_carriers = {'DC'}

    carrier = carrier_map.get(ec_code)
    if not carrier:
        # Return None for carriers that don't map to services (e.g., heat rejection)
        return None

    # Determine suffix based on network_type or infer from carrier
    if network_type == 'DH':
        suffix = '_hs'
    elif network_type == 'DC':
        suffix = '_cs'
    elif network_type is None:
        # Standalone system - infer from carrier type
        if carrier in heating_carriers:
            suffix = '_hs'
        elif carrier in cooling_carriers:
            suffix = '_cs'
        else:
            # GRID (electricity) - ambiguous, return None for caller to handle
            return None
    else:
        # Unknown network_type
        return None

    return f"{carrier}{suffix}"

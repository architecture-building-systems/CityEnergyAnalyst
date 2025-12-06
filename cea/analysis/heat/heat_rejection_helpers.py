"""
Helper functions for heat rejection calculations.

This module contains shared utilities for filtering and processing heat rejection data
based on building connectivity cases and service types.
"""
import pandas as pd

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


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
        """Extract scale from supply code (checks database)."""
        if not supply_code or pd.isna(supply_code):
            return None

        # Read from SUPPLY assemblies to determine scale
        try:
            # Try to read from database
            from cea.databases.CH.ASSEMBLIES import SUPPLY
            # Simplified: check if code contains 'AS3' or 'AS4' (district) vs 'AS1', 'AS2' (building)
            # This is a heuristic - proper implementation should read from database
            code_str = str(supply_code).upper()
            if 'AS3' in code_str or 'AS4' in code_str:
                return 'DISTRICT'
            elif 'AS1' in code_str or 'AS2' in code_str or 'AS5' in code_str:
                return 'BUILDING'
        except:
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

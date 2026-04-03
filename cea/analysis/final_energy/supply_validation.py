"""
Supply System Validation - Pre-flight checks for Energy by Carrier (final-energy).

Validates that supply.csv is consistent with network connectivity before any
calculations begin. Called only in production mode (overwrite-supply-settings = False).

Two scenarios:
1. No network selected (standalone mode): all buildings must have BUILDING scale
2. Network selected: supply.csv must match connectivity.json exactly
"""

import json
import os

import pandas as pd


# Maps component code prefix → (CSV filename, temperature column).
# Used to look up a component's design supply temperature.
# Longer prefixes are checked first to avoid false matches.
COMPONENT_SUPPLY_TEMP_MAP = {
    'OEHR': ('COGENERATION_PLANTS', 'T_water_out_design'),
    'BO':   ('BOILERS',             'T_water_out_rating'),
    'HP':   ('HEAT_PUMPS',          'T_cond_design'),
}

# DC components: evaporator design temperature (what the chiller can supply on the cold side).
COMPONENT_DC_SUPPLY_TEMP_MAP = {
    'CH':   ('VAPOR_COMPRESSION_CHILLERS', 'T_evap_design'),
}


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def validate_whatif_params(locator, config):
    """
    Validate that all required assembly parameters are set for what-if mode.

    Loads connectivity.json to determine which buildings are connected to DH/DC,
    then checks that the corresponding district and building assembly params are set.
    Raises a single ValueError listing all missing params before any buildings are processed.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :raises ValueError: If any required assembly parameter is not set
    """
    network_name = config.final_energy.network_name

    dh_buildings: set = set()
    dc_buildings: set = set()
    if network_name:
        try:
            connectivity = load_network_connectivity(locator, network_name)
            dh_buildings = set(
                connectivity.get('networks', {}).get('DH', {}).get('per_building_services', {}).keys()
            )
            dc_buildings = set(
                connectivity.get('networks', {}).get('DC', {}).get('per_building_services', {}).keys()
            )
        except ValueError:
            pass  # No connectivity.json → treat all buildings as standalone

    # Load all buildings to determine standalone set
    try:
        import geopandas as gpd
        zone_gdf = gpd.read_file(locator.get_zone_geometry())
        all_buildings = set(zone_gdf['name'].tolist())
    except Exception:
        all_buildings = set()

    standalone_dh = all_buildings - dh_buildings
    standalone_dc = all_buildings - dc_buildings

    # Load total demand to skip params for services with zero demand
    hs_demand_buildings: set = set()
    dhw_demand_buildings: set = set()
    cs_demand_buildings: set = set()
    try:
        demand_path = locator.get_total_demand()
        demand_df = pd.read_csv(demand_path).set_index('name')
        for building in all_buildings:
            if building not in demand_df.index:
                # Unknown demand → be conservative: require params
                hs_demand_buildings.add(building)
                dhw_demand_buildings.add(building)
                cs_demand_buildings.add(building)
                continue
            row = demand_df.loc[building]
            if row.get('Qhs_sys_MWhyr', 0.0) > 0.0:
                hs_demand_buildings.add(building)
            if row.get('Qww_sys_MWhyr', 0.0) > 0.0:
                dhw_demand_buildings.add(building)
            if row.get('Qcs_sys_MWhyr', 0.0) > 0.0:
                cs_demand_buildings.add(building)
    except Exception:
        # If demand file unreadable, be conservative: require all params
        hs_demand_buildings = all_buildings.copy()
        dhw_demand_buildings = all_buildings.copy()
        cs_demand_buildings = all_buildings.copy()

    dh_hs = dh_buildings & hs_demand_buildings
    dh_dhw = dh_buildings & dhw_demand_buildings
    standalone_hs = standalone_dh & hs_demand_buildings
    standalone_dhw = standalone_dh & dhw_demand_buildings
    dc_cs = dc_buildings & cs_demand_buildings
    standalone_cs = standalone_dc & cs_demand_buildings

    missing = []

    if dh_hs and not config.final_energy.supply_type_hs_district:
        missing.append(
            f"  - 'supply-type-hs-district': required for {len(dh_hs)} DH-connected building(s) with space heating demand"
        )
    if standalone_hs and not config.final_energy.supply_type_hs_building:
        missing.append(
            f"  - 'supply-type-hs-building': required for {len(standalone_hs)} standalone building(s) with space heating demand"
        )
    if dh_dhw and not config.final_energy.supply_type_dhw_district:
        missing.append(
            f"  - 'supply-type-dhw-district': required for {len(dh_dhw)} DH-connected building(s) with hot water demand"
        )
    if standalone_dhw and not config.final_energy.supply_type_dhw_building:
        missing.append(
            f"  - 'supply-type-dhw-building': required for {len(standalone_dhw)} standalone building(s) with hot water demand"
        )
    if dc_cs and not config.final_energy.supply_type_cs_district:
        missing.append(
            f"  - 'supply-type-cs-district': required for {len(dc_cs)} DC-connected building(s) with cooling demand"
        )
    if standalone_cs and not config.final_energy.supply_type_cs_building:
        missing.append(
            f"  - 'supply-type-cs-building': required for {len(standalone_cs)} standalone building(s) with cooling demand"
        )

    if missing:
        raise ValueError(
            "What-if mode requires all assembly parameters to be explicitly set.\n"
            "The following parameters are missing:\n"
            + "\n".join(missing)
            + "\n\nPlease set these parameters in the Energy by Carrier settings."
        )


def validate_supply_consistency(locator, config):
    """
    Validate supply.csv is consistent with network connectivity.
    Entry point called from final_energy/main.py before any calculations.

    :param locator: InputLocator instance
    :param config: Configuration instance
    :raises ValueError: If supply.csv and network connectivity are inconsistent
    """
    network_name = config.final_energy.network_name

    if not network_name or network_name == '(none)':
        validate_standalone_mode(locator)
    else:
        validate_network_mode(locator, network_name, config)


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 1: No network selected
# ─────────────────────────────────────────────────────────────────────────────

def validate_standalone_mode(locator):
    """
    Validate all buildings are BUILDING scale when no network is selected.

    :param locator: InputLocator instance
    :raises ValueError: If any building has DISTRICT scale in supply.csv
    """
    supply_df = pd.read_csv(locator.get_building_supply())
    scale_mapping = load_all_assembly_scales(locator)

    service_columns = {
        'supply_type_hs': 'space heating',
        'supply_type_dhw': 'domestic hot water',
        'supply_type_cs': 'space cooling',
    }

    mismatches = []

    for col, service_label in service_columns.items():
        if col not in supply_df.columns:
            continue

        for _, row in supply_df.iterrows():
            building = row['name']
            code = row[col]

            if pd.isna(code) or str(code).strip() in ['', '-', 'NONE']:
                continue

            scale = scale_mapping.get(str(code))
            if scale == 'DISTRICT':
                mismatches.append(
                    f"  - {building}: {service_label} uses '{code}' (DISTRICT scale)"
                )

    if mismatches:
        raise ValueError(
            "No network is selected, but the following buildings have DISTRICT-scale "
            "assemblies in Building Properties/Supply:\n"
            + "\n".join(mismatches)
            + "\n\nPlease either:\n"
            "  (a) Select a network in the final-energy settings, or\n"
            "  (b) Change these buildings to BUILDING-scale assemblies in Building Properties/Supply"
            "  (c) Set 'overwrite-supply-settings = True' in final-energy settings"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 2: Network selected
# ─────────────────────────────────────────────────────────────────────────────

def validate_network_mode(locator, network_name, config):
    """
    Validate supply.csv matches network connectivity.json.

    Checks (all raise ValueError on failure):
    1. connectivity.json exists
    2. Buildings connected to DH have DISTRICT scale for their services in supply.csv
    3. Buildings connected to DC have DISTRICT scale for space_cooling in supply.csv
    4. Buildings in supply.csv with DISTRICT scale must appear in connectivity.json
    5. All DH buildings use the same space_heating assembly
    6. All DH buildings use the same domestic_hot_water assembly
    7. DH space_heating and domestic_hot_water assemblies use the same equipment components
    8. DH assembly equipment is temperature-compatible with network configuration
    9. All DC buildings use the same space_cooling assembly

    :param locator: InputLocator instance
    :param network_name: Network layout name
    :param config: Configuration instance
    :raises ValueError: If any inconsistency is found
    """
    connectivity = load_network_connectivity(locator, network_name)
    supply_df = pd.read_csv(locator.get_building_supply())
    scale_mapping = load_all_assembly_scales(locator)

    if 'DH' in connectivity.get('networks', {}):
        validate_dh_consistency(connectivity['networks']['DH'], supply_df, scale_mapping, locator, config)

    if 'DC' in connectivity.get('networks', {}):
        validate_dc_consistency(connectivity['networks']['DC'], supply_df, scale_mapping)

    # Check for buildings in supply.csv with DISTRICT scale that aren't in connectivity.json
    validate_no_orphaned_district_buildings(connectivity, supply_df, scale_mapping, network_name,
                                           locator=locator)

    # Check that buildings with booster demand have a booster assembly configured
    if 'DH' in connectivity.get('networks', {}):
        validate_booster_configuration(connectivity['networks']['DH'], network_name, locator, config)


def validate_dh_consistency(dh_network, supply_df, scale_mapping, locator, config):
    """
    Validate DH network consistency.

    Checks:
    - Each DH building has a valid DISTRICT-scale assembly for its services
    - All buildings use the same hs assembly; all use the same dhw assembly
    - hs and dhw assemblies use the same primary/secondary/tertiary equipment components

    :param dh_network: Dict from connectivity.json['networks']['DH']
    :param supply_df: DataFrame from supply.csv
    :param scale_mapping: Dict {assembly_code: scale}
    :param locator: InputLocator instance
    :param config: Configuration instance (reserved for future use)
    :raises ValueError: If any inconsistency is found
    """
    per_building_services = dh_network.get('per_building_services', {})

    hs_assemblies = {}   # {building: assembly_code}
    dhw_assemblies = {}  # {building: assembly_code}

    for building, services in per_building_services.items():
        building_row = supply_df[supply_df['name'] == building]

        if building_row.empty:
            raise ValueError(
                f"Building '{building}' is listed in the DH network (connectivity.json) "
                f"but is not found in Building Properties/Supply.\n\n"
                f"Please re-run 'network-layout' after updating Building Properties/Supply."
            )

        row = building_row.iloc[0]

        if 'space_heating' in services:
            code = row.get('supply_type_hs')
            if pd.isna(code) or str(code).strip() in ['', '-', 'NONE']:
                raise ValueError(
                    f"Building '{building}' is connected to the DH network for space heating, "
                    f"but 'supply_type_hs' is empty in Building Properties/Supply.\n\n"
                    f"Please assign a DISTRICT-scale SUPPLY_HEATING assembly to this building."
                )

            scale = scale_mapping.get(str(code))
            if scale != 'DISTRICT':
                raise ValueError(
                    f"Building '{building}' is connected to the DH network for space heating, "
                    f"but 'supply_type_hs = {code}' has {scale} scale (DISTRICT expected).\n\n"
                    f"Please assign a DISTRICT-scale SUPPLY_HEATING assembly to this building."
                )

            hs_assemblies[building] = str(code)

        if 'domestic_hot_water' in services:
            code = row.get('supply_type_dhw')
            if pd.isna(code) or str(code).strip() in ['', '-', 'NONE']:
                raise ValueError(
                    f"Building '{building}' is connected to the DH network for domestic hot water, "
                    f"but 'supply_type_dhw' is empty in Building Properties/Supply.\n\n"
                    f"Please assign a DISTRICT-scale SUPPLY_HEATING assembly to this building."
                )

            scale = scale_mapping.get(str(code))
            if scale != 'DISTRICT':
                raise ValueError(
                    f"Building '{building}' is connected to the DH network for domestic hot water, "
                    f"but 'supply_type_dhw = {code}' has {scale} scale (DISTRICT expected).\n\n"
                    f"Please assign a DISTRICT-scale SUPPLY_HEATING assembly to this building."
                )

            dhw_assemblies[building] = str(code)

    # All hs assemblies must be the same
    if len(set(hs_assemblies.values())) > 1:
        listing = "\n".join(f"  - {b}: {a}" for b, a in sorted(hs_assemblies.items()))
        raise ValueError(
            f"All buildings connected to the DH network for space heating must use the "
            f"same SUPPLY_HEATING assembly (they share one district plant).\n\n"
            f"Currently using different assemblies:\n{listing}\n\n"
            f"Please update Building Properties/Supply so all DH buildings use the same assembly."
        )

    # All dhw assemblies must be the same
    if len(set(dhw_assemblies.values())) > 1:
        listing = "\n".join(f"  - {b}: {a}" for b, a in sorted(dhw_assemblies.items()))
        raise ValueError(
            f"All buildings connected to the DH network for domestic hot water must use the "
            f"same SUPPLY_HEATING assembly (they share one district plant).\n\n"
            f"Currently using different assemblies:\n{listing}\n\n"
            f"Please update Building Properties/Supply so all DH buildings use the same assembly."
        )

    # Validate component-level consistency
    if hs_assemblies and dhw_assemblies:
        hs_assembly = next(iter(set(hs_assemblies.values())))
        dhw_assembly = next(iter(set(dhw_assemblies.values())))
        validate_component_levels_match(hs_assembly, dhw_assembly, locator)


def validate_dc_consistency(dc_network, supply_df, scale_mapping):
    """
    Validate DC network consistency.

    :param dc_network: Dict from connectivity.json['networks']['DC']
    :param supply_df: DataFrame from supply.csv
    :param scale_mapping: Dict {assembly_code: scale}
    :raises ValueError: If any inconsistency is found
    """
    per_building_services = dc_network.get('per_building_services', {})

    cs_assemblies = {}  # {building: assembly_code}

    for building, services in per_building_services.items():
        if 'space_cooling' not in services:
            continue

        building_row = supply_df[supply_df['name'] == building]

        if building_row.empty:
            raise ValueError(
                f"Building '{building}' is listed in the DC network (connectivity.json) "
                f"but is not found in Building Properties/Supply.\n\n"
                f"Please re-run 'network-layout' after updating Building Properties/Supply."
            )

        row = building_row.iloc[0]
        code = row.get('supply_type_cs')

        if pd.isna(code) or str(code).strip() in ['', '-', 'NONE']:
            raise ValueError(
                f"Building '{building}' is connected to the DC network for space cooling, "
                f"but 'supply_type_cs' is empty in Building Properties/Supply.\n\n"
                f"Please assign a DISTRICT-scale SUPPLY_COOLING assembly to this building."
            )

        scale = scale_mapping.get(str(code))
        if scale != 'DISTRICT':
            raise ValueError(
                f"Building '{building}' is connected to the DC network for space cooling, "
                f"but 'supply_type_cs = {code}' has {scale} scale (DISTRICT expected).\n\n"
                f"Please assign a DISTRICT-scale SUPPLY_COOLING assembly to this building."
            )

        cs_assemblies[building] = str(code)

    # All cs assemblies must be the same
    if len(set(cs_assemblies.values())) > 1:
        listing = "\n".join(f"  - {b}: {a}" for b, a in sorted(cs_assemblies.items()))
        raise ValueError(
            f"All buildings connected to the DC network must use the same SUPPLY_COOLING "
            f"assembly (they share one district plant).\n\n"
            f"Currently using different assemblies:\n{listing}\n\n"
            f"Please update Building Properties/Supply so all DC buildings use the same assembly."
        )


def validate_no_orphaned_district_buildings(connectivity, supply_df, scale_mapping, network_name,
                                             locator=None):
    """
    Check that no building in supply.csv has a DISTRICT-scale assembly
    without appearing in connectivity.json.

    Buildings without any demand for the relevant service are reported as
    warnings (validation skipped) rather than errors, since they produce
    zero final-energy regardless of scale.

    :param connectivity: Dict from connectivity.json
    :param supply_df: DataFrame from supply.csv
    :param scale_mapping: Dict {assembly_code: scale}
    :param network_name: Network layout name (for error message)
    :param locator: InputLocator instance (optional; needed to read demand data)
    :raises ValueError: If any building *with demand* has DISTRICT scale but is not in the network
    """
    # Collect all buildings connected to any network
    connected_dh = set(connectivity.get('networks', {}).get('DH', {}).get('per_building_services', {}).keys())
    connected_dc = set(connectivity.get('networks', {}).get('DC', {}).get('per_building_services', {}).keys())

    # Load demand data to distinguish zero-demand buildings
    demand_by_building = {}  # building → {'hs': float, 'dhw': float, 'cs': float}
    if locator is not None:
        try:
            demand_df = pd.read_csv(locator.get_total_demand()).set_index('name')
            for bldg in demand_df.index:
                demand_by_building[bldg] = {
                    'hs': demand_df.loc[bldg].get('Qhs_sys_MWhyr', 0.0),
                    'dhw': demand_df.loc[bldg].get('Qww_sys_MWhyr', 0.0),
                    'cs': demand_df.loc[bldg].get('Qcs_sys_MWhyr', 0.0),
                }
        except Exception:
            pass  # If demand data unavailable, treat all as having demand (conservative)

    # Map service columns to the demand key used for zero-demand check
    service_columns = {
        'supply_type_hs':  ('DH', 'space heating', 'hs'),
        'supply_type_dhw': ('DH', 'domestic hot water', 'dhw'),
        'supply_type_cs':  ('DC', 'space cooling', 'cs'),
    }

    def _has_demand(bldg_name, dkey):
        """Return True if building has non-zero demand for the given service."""
        bd = demand_by_building.get(bldg_name)
        if bd is None:
            return True  # Unknown demand → conservative, treat as having demand
        return bd.get(dkey, 0.0) > 0.0

    # Group mismatches by (service_label, assembly_code, network_type) to avoid
    # repeating the same message for every building.
    from collections import defaultdict
    grouped_error = defaultdict(list)    # buildings WITH demand → error
    grouped_warning = defaultdict(list)  # buildings WITHOUT demand → warning

    for col, (network_type, service_label, dem_key) in service_columns.items():
        if col not in supply_df.columns:
            continue

        connected = connected_dh if network_type == 'DH' else connected_dc

        for _, row in supply_df.iterrows():
            building = row['name']
            code = row[col]

            if pd.isna(code) or str(code).strip() in ['', '-', 'NONE']:
                continue

            scale = scale_mapping.get(str(code))
            if scale == 'DISTRICT' and building not in connected:
                if _has_demand(building, dem_key):
                    grouped_error[(service_label, str(code), network_type)].append(building)
                else:
                    grouped_warning[(service_label, str(code), network_type)].append(building)

    # Print warnings for zero-demand buildings (validation skipped)
    if grouped_warning:
        all_warned = set()
        for buildings in grouped_warning.values():
            all_warned.update(buildings)
        names = ", ".join(sorted(all_warned))
        print(f"  Warning: validation skipped for buildings without demand: {names}")

    # Raise error only for buildings that actually have demand
    if grouped_error:
        lines = []
        for (service_label, code, network_type), buildings in grouped_error.items():
            names = ", ".join(buildings)
            lines.append(
                f"  - {service_label} uses '{code}' (DISTRICT scale) "
                f"but not in {network_type} network '{network_name}': {names}"
            )
        raise ValueError(
            "The following buildings have DISTRICT-scale assemblies in Building Properties/Supply "
            "but are not connected to the selected network. "
            "This may mean Building Properties/Supply was updated after running network-layout.\n\n"
            + "\n".join(lines)
            + "\n\nPlease either:\n"
            "  (a) Re-run 'network-layout' to regenerate connectivity.json (Set consider-only-buildings-with-demand = false), or\n"
            "  (b) Change these buildings to BUILDING-scale assemblies in Building Properties/Supply\n"
            "  (c) Set 'overwrite-supply-settings = True' in final-energy settings"
        )


def validate_booster_configuration(dh_network, network_name, locator, config):
    """
    Validate that buildings with booster demand have a booster assembly configured.

    Reads substation files for all DH-connected buildings and checks whether
    space heating or domestic hot water booster demand is present. If so,
    the corresponding booster assembly must be set in the config.

    Called before any building is processed so the script fails fast with
    a single consolidated error instead of per-building failures.

    :param dh_network: Dict from connectivity.json['networks']['DH']
    :param network_name: Network layout name (for substation file paths)
    :param locator: InputLocator instance
    :param config: Configuration instance
    :raises ValueError: If any building has booster demand without a configured assembly
    """
    hs_booster_type = config.final_energy.hs_booster_type_building
    dhw_booster_type = config.final_energy.dhw_booster_type_building

    hs_needs_booster = []
    dhw_needs_booster = []

    per_building_services = dh_network.get('per_building_services', {})

    for building, services in per_building_services.items():
        substation_file = locator.get_thermal_network_substation_results_file(
            building, 'DH', network_name
        )

        if not os.path.exists(substation_file):
            continue

        try:
            substation_df = pd.read_csv(substation_file)
        except Exception:
            continue

        if 'space_heating' in services and 'Qhs_booster_W' in substation_df.columns:
            if substation_df['Qhs_booster_W'].sum() > 0 and not hs_booster_type:
                hs_needs_booster.append(building)

        if 'domestic_hot_water' in services and 'Qww_booster_W' in substation_df.columns:
            if substation_df['Qww_booster_W'].sum() > 0 and not dhw_booster_type:
                dhw_needs_booster.append(building)

    messages = []

    if hs_needs_booster:
        listing = "\n".join(f"  - {b}" for b in sorted(hs_needs_booster))
        messages.append(
            f"The following buildings have space heating booster demand from the "
            f"low-temperature district heating network, but no booster assembly is configured:\n"
            f"{listing}\n\n"
            f"Please select a booster assembly in 'hs-booster-type-building' "
            f"(Energy by Carrier settings)."
        )

    if dhw_needs_booster:
        listing = "\n".join(f"  - {b}" for b in sorted(dhw_needs_booster))
        messages.append(
            f"The following buildings have domestic hot water booster demand from the "
            f"low-temperature district heating network, but no booster assembly is configured:\n"
            f"{listing}\n\n"
            f"Please select a booster assembly in 'dhw-booster-type-building' "
            f"(Energy by Carrier settings)."
        )

    if messages:
        raise ValueError("\n\n".join(messages))


def validate_booster_temperature_compatibility(dh_network, network_name, locator, config):
    """
    Validate that booster assemblies can supply the temperatures required by each building.

    Reads T_target_hs_C and T_target_dhw_C from substation files (written by thermal-network
    Part 2) and compares against the booster component's design supply temperature.

    :param dh_network: Dict from connectivity.json['networks']['DH']
    :param network_name: Network layout name
    :param locator: InputLocator instance
    :param config: Configuration instance
    :raises ValueError: If any booster cannot reach the required temperature
    """
    hs_booster_code = config.final_energy.hs_booster_type_building
    dhw_booster_code = config.final_energy.dhw_booster_type_building

    # Look up booster component design temperatures
    hs_booster_temp = None
    dhw_booster_temp = None
    if hs_booster_code:
        components = load_assembly_components(hs_booster_code, locator)
        primary = components.get('primary_components')
        if primary:
            hs_booster_temp = get_component_design_supply_temperature(primary, locator)

    if dhw_booster_code:
        components = load_assembly_components(dhw_booster_code, locator)
        primary = components.get('primary_components')
        if primary:
            dhw_booster_temp = get_component_design_supply_temperature(primary, locator)

    per_building_services = dh_network.get('per_building_services', {})
    # Group by required temperature: {t_required: [building_names]}
    hs_groups = {}  # {t_required_C: [building, ...]}
    dhw_groups = {}

    needs_check = hs_booster_temp is not None or dhw_booster_temp is not None

    for building in per_building_services:
        substation_file = locator.get_thermal_network_substation_results_file(
            building, 'DH', network_name
        )
        if not os.path.exists(substation_file):
            continue

        try:
            sub_df = pd.read_csv(substation_file)
        except Exception:
            continue

        # Check for missing temperature columns (backward compatibility)
        if needs_check:
            missing_cols = []
            if hs_booster_temp is not None and 'T_target_hs_C' not in sub_df.columns:
                if sub_df.get('Qhs_booster_W') is not None and sub_df['Qhs_booster_W'].sum() > 0:
                    missing_cols.append('T_target_hs_C')
            if dhw_booster_temp is not None and 'T_target_dhw_C' not in sub_df.columns:
                if sub_df.get('Qww_booster_W') is not None and sub_df['Qww_booster_W'].sum() > 0:
                    missing_cols.append('T_target_dhw_C')
            if missing_cols:
                raise ValueError(
                    f"Substation file for building '{building}' is missing columns: "
                    f"{', '.join(missing_cols)}.\n\n"
                    f"This is likely because the thermal network was simulated with an older version of CEA.\n\n"
                    f"Please re-run Thermal Network Part 2 to regenerate the substation files.\n"
                    f"If the error persists, re-run Thermal Network Part 1 as well."
                )

        # Check HS booster temperature
        if hs_booster_temp is not None and 'T_target_hs_C' in sub_df.columns:
            t_required = round(sub_df['T_target_hs_C'].max())
            if t_required > 0 and hs_booster_temp < t_required - 0.5:
                hs_groups.setdefault(t_required, []).append(building)

        # Check DHW booster temperature
        if dhw_booster_temp is not None and 'T_target_dhw_C' in sub_df.columns:
            t_required = round(sub_df['T_target_dhw_C'].max())
            if t_required > 0 and dhw_booster_temp < t_required - 0.5:
                dhw_groups.setdefault(t_required, []).append(building)

    messages = []

    if hs_groups:
        hs_primary = load_assembly_components(hs_booster_code, locator).get('primary_components', '?')
        lines = []
        for t_req, buildings in sorted(hs_groups.items()):
            names = ", ".join(sorted(buildings))
            lines.append(
                f"  - Requires {t_req:.0f} degrees C: {names}"
            )
        messages.append(
            f"Space heating booster assembly ({hs_booster_code}, component {hs_primary}) "
            f"can only supply {hs_booster_temp:.0f} degrees C, which is insufficient for:\n"
            + "\n".join(lines)
            + f"\n\nPlease select a booster assembly with a component that can supply "
            f"a higher temperature."
        )

    if dhw_groups:
        dhw_primary = load_assembly_components(dhw_booster_code, locator).get('primary_components', '?')
        lines = []
        for t_req, buildings in sorted(dhw_groups.items()):
            names = ", ".join(sorted(buildings))
            lines.append(
                f"  - Requires {t_req:.0f} degrees C: {names}"
            )
        messages.append(
            f"DHW booster assembly ({dhw_booster_code}, component {dhw_primary}) "
            "can only supply {dhw_booster_temp:.0f} degrees C, which is insufficient for:\n"
            + "\n".join(lines)
            + f"\n\nPlease select a booster assembly with a component that can supply "
            "a higher temperature."
        )

    if messages:
        raise ValueError("\n\n".join(messages))


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_assembly_components(assembly_code, locator):
    """
    Load component codes for a given supply assembly.

    :param assembly_code: Assembly code, e.g. 'SUPPLY_HEATING_AS9'
    :param locator: InputLocator instance
    :return: Dict with keys 'primary_components', 'secondary_components', 'tertiary_components'
             (values are component code strings or None if not specified)
    :raises ValueError: If assembly code not found in database
    """
    code = str(assembly_code).strip()

    if code.startswith('SUPPLY_HEATING'):
        filepath = locator.get_database_assemblies_supply_heating()
    elif code.startswith('SUPPLY_HOTWATER'):
        filepath = locator.get_database_assemblies_supply_hot_water()
    elif code.startswith('SUPPLY_COOLING'):
        filepath = locator.get_database_assemblies_supply_cooling()
    else:
        raise ValueError(f"Unknown assembly code prefix: '{code}'")

    if not os.path.exists(filepath):
        raise ValueError(f"Assembly database file not found: {filepath}")

    df = pd.read_csv(filepath)
    row = df[df['code'] == code]

    if row.empty:
        raise ValueError(f"Assembly '{code}' not found in database: {filepath}")

    row = row.iloc[0]

    def safe_get(col):
        val = row.get(col)
        if pd.isna(val) or str(val).strip() in ['', '-', 'NONE', 'None']:
            return None
        return str(val).strip()

    return {
        'primary_components':   safe_get('primary_components'),
        'secondary_components': safe_get('secondary_components'),
        'tertiary_components':  safe_get('tertiary_components'),
    }


def get_component_design_supply_temperature(component_code, locator):
    """
    Look up the design supply temperature of a heating component.

    Uses COMPONENT_SUPPLY_TEMP_MAP to find the correct CSV and column.
    Returns None for unknown component types (check is silently skipped).

    :param component_code: Component code, e.g. 'BO6', 'HP3'
    :param locator: InputLocator instance
    :return: Design supply temperature in degrees C, or None if unknown type
    """
    if not component_code:
        return None

    code = str(component_code).strip()

    # Check longer prefixes first to avoid false matches (e.g. OEHR before O)
    matched_entry = None
    for prefix in sorted(COMPONENT_SUPPLY_TEMP_MAP.keys(), key=len, reverse=True):
        if code.startswith(prefix):
            matched_entry = COMPONENT_SUPPLY_TEMP_MAP[prefix]
            break

    if matched_entry is None:
        return None

    csv_name, temp_col = matched_entry
    filepath = locator.get_db4_components_conversion_conversion_technology_csv(csv_name)

    if not os.path.exists(filepath):
        return None

    df = pd.read_csv(filepath)
    row = df[df['code'] == code]

    if row.empty:
        return None

    val = row.iloc[0].get(temp_col)
    if pd.isna(val):
        return None

    return float(val)


def validate_component_levels_match(hs_code, dhw_code, locator):
    """
    Validate that hs and dhw assemblies use the same equipment at all three component levels.

    The district heating plant is a single physical installation, so both space heating
    and domestic hot water must reference assemblies with identical components.

    :param hs_code: Space heating assembly code (e.g., 'SUPPLY_HEATING_AS9')
    :param dhw_code: Domestic hot water assembly code (e.g., 'SUPPLY_HOTWATER_AS9')
    :param locator: InputLocator instance
    :raises ValueError: If any component level differs between the two assemblies
    """
    hs_components = load_assembly_components(hs_code, locator)
    dhw_components = load_assembly_components(dhw_code, locator)

    level_labels = {
        'primary_components':   'primary',
        'secondary_components': 'secondary',
        'tertiary_components':  'tertiary',
    }

    for key, label in level_labels.items():
        hs_val = hs_components[key]
        dhw_val = dhw_components[key]

        if hs_val != dhw_val:
            raise ValueError(
                f"The district heating plant serves both space heating and domestic hot water "
                f"from the same source, but their supply assemblies specify different {label} "
                f"equipment.\n\n"
                f"  Space heating   ({hs_code}):      {label} = {hs_val or '(none)'}\n"
                f"  Domestic hot water ({dhw_code}): {label} = {dhw_val or '(none)'}\n\n"
                f"Both assemblies must reference the same {label} equipment component, "
                f"since the district plant is a single physical installation that needs "
                f"one consistent efficiency and sizing curve.\n\n"
                f"Please update Building Properties/Supply so both services use assemblies "
                f"with matching {label} components."
            )


def validate_assembly_temperature_vs_network(assembly_code, locator, dh_temperature_mode,
                                             network_temperature_dh, tolerance=5.0):
    """
    Validate that the assembly's primary component can supply the required network temperature.

    VT mode temperature ranges (with tolerance applied at both ends):
      low-temperature:  30–65 °C
      high-temperature: 50–95 °C

    CT mode: component must reach the fixed supply temperature (only too-cold is checked).

    :param assembly_code: Assembly code to check
    :param locator: InputLocator instance
    :param dh_temperature_mode: 'low-temperature' or 'high-temperature' (VT mode)
    :param network_temperature_dh: Fixed supply temperature in degrees C (-1 = VT mode)
    :param tolerance: Allowable temperature deviation in degrees C
    :raises ValueError: If component temperature is incompatible with network configuration
    """
    components = load_assembly_components(assembly_code, locator)
    primary_code = components.get('primary_components')

    if not primary_code:
        return

    t_design = get_component_design_supply_temperature(primary_code, locator)

    if t_design is None:
        return

    is_ct_mode = network_temperature_dh is not None and float(network_temperature_dh) > 0

    if is_ct_mode:
        t_ct = float(network_temperature_dh)
        if t_design < t_ct - tolerance:
            raise ValueError(
                f"The assembly '{assembly_code}' (primary component: {primary_code}) is "
                f"incompatible with the district heating network configuration.\n\n"
                f"Network mode: CT (constant temperature) at {t_ct:.0f} °C\n"
                f"Component '{primary_code}' design supply temperature: {t_design:.0f} °C "
                f"(minimum required: {t_ct - tolerance:.0f} °C with {tolerance:.0f} °C tolerance)\n\n"
                f"The district plant cannot reach the required network supply temperature.\n\n"
                f"Please either:\n"
                f"  (a) Select an assembly with a higher-temperature component, or\n"
                f"  (b) Reduce 'network-temperature-dh' in thermal-network settings to match "
                f"the equipment capability"
            )
    else:
        if dh_temperature_mode == 'high-temperature':
            t_min, t_max = 50.0, 95.0
            mode_label = 'VT high-temperature'
        else:
            t_min, t_max = 30.0, 65.0
            mode_label = 'VT low-temperature'

        if t_design < t_min - tolerance:
            raise ValueError(
                f"The assembly '{assembly_code}' (primary component: {primary_code}) is "
                f"incompatible with the district heating network configuration.\n\n"
                f"Network mode: {mode_label}\n"
                f"Valid temperature range: {t_min:.0f}–{t_max:.0f} °C "
                f"(with {tolerance:.0f} °C tolerance: {t_min - tolerance:.0f}–{t_max + tolerance:.0f} °C)\n"
                f"Component '{primary_code}' design supply temperature: {t_design:.0f} °C (too low)\n\n"
                f"Please either:\n"
                f"  (a) Select an assembly with a higher-temperature component, or\n"
                f"  (b) Change 'dh-temperature-mode' in thermal-network settings"
            )

        if t_design > t_max + tolerance:
            raise ValueError(
                f"The assembly '{assembly_code}' (primary component: {primary_code}) is "
                f"incompatible with the district heating network configuration.\n\n"
                f"Network mode: {mode_label}\n"
                f"Valid temperature range: {t_min:.0f}–{t_max:.0f} °C "
                f"(with {tolerance:.0f} °C tolerance: {t_min - tolerance:.0f}–{t_max + tolerance:.0f} °C)\n"
                f"Component '{primary_code}' design supply temperature: {t_design:.0f} °C (too high)\n\n"
                f"Please either:\n"
                f"  (a) Select an assembly with a lower-temperature component "
                f"(e.g., heat pump or low-temperature boiler), or\n"
                f"  (b) Change 'dh-temperature-mode' to 'high-temperature' in thermal-network settings"
            )


def get_component_dc_supply_temperature(component_code, locator):
    """
    Look up the design supply temperature of a cooling component (evaporator side).

    :param component_code: Component code, e.g. 'CH1', 'CH2'
    :param locator: InputLocator instance
    :return: Design evaporator temperature in degrees C, or None if unknown type
    """
    if not component_code:
        return None

    code = str(component_code).strip()

    matched_entry = None
    for prefix in sorted(COMPONENT_DC_SUPPLY_TEMP_MAP.keys(), key=len, reverse=True):
        if code.startswith(prefix):
            matched_entry = COMPONENT_DC_SUPPLY_TEMP_MAP[prefix]
            break

    if matched_entry is None:
        return None

    csv_name, temp_col = matched_entry
    filepath = locator.get_db4_components_conversion_conversion_technology_csv(csv_name)

    if not os.path.exists(filepath):
        return None

    df = pd.read_csv(filepath)
    row = df[df['code'] == code]

    if row.empty:
        return None

    val = row.iloc[0].get(temp_col)
    if pd.isna(val):
        return None

    return float(val)


def validate_plant_temperature_vs_network_results(locator, network_name, config):
    """
    Validate that the district plant component can supply the temperature
    required by the actual thermal-network Part 2 simulation results.

    Reads the maximum supply temperature from the plant temperature file
    and compares against the component's design temperature.

    For DH: component T_design must be >= network supply temperature
    For DC: component T_design must be <= network supply temperature

    :param locator: InputLocator instance
    :param network_name: Network layout name
    :param config: Configuration instance
    :raises ValueError: If temperature is incompatible
    """
    if not network_name:
        return

    # --- DH check ---
    dh_temp_file = locator.get_network_temperature_plant('DH', network_name)
    if os.path.exists(dh_temp_file):
        # Get the district assembly for heating
        if config.final_energy.overwrite_supply_settings:
            hs_assembly = config.final_energy.supply_type_hs_district
        else:
            supply_df = pd.read_csv(locator.get_building_supply())
            scale_mapping = load_all_assembly_scales(locator)
            # Find the first DISTRICT-scale heating assembly
            hs_assembly = None
            if 'supply_type_hs' in supply_df.columns:
                for _, row in supply_df.iterrows():
                    code = row.get('supply_type_hs')
                    if code and not pd.isna(code) and scale_mapping.get(str(code)) == 'DISTRICT':
                        hs_assembly = str(code)
                        break

        if hs_assembly:
            components = load_assembly_components(hs_assembly, locator)
            primary_code = components.get('primary_components')
            t_component = get_component_design_supply_temperature(primary_code, locator)

            if t_component is not None:
                temp_df = pd.read_csv(dh_temp_file)
                if 'temperature_supply_K' in temp_df.columns:
                    # Filter out zero rows (no demand hours)
                    active = temp_df[temp_df['temperature_supply_K'] > 0]
                    if not active.empty:
                        t_network_K = active['temperature_supply_K'].max()
                        t_network_C = t_network_K - 273.15

                        if t_component < t_network_C - 0.5:  # 0.5°C tolerance for floating point
                            raise ValueError(
                                f"Temperature incompatibility: the selected DH plant assembly "
                                f"({hs_assembly}) uses {primary_code} with a maximum supply "
                                f"temperature of {t_component:.0f} degrees C, which is below the network "
                                f"supply temperature of {t_network_C:.0f} degrees C.\n\n"
                                f"Options:\n"
                                f"  1. Select a different assembly with a supply temperature "
                                f"higher than {t_network_C:.0f} degrees C\n"
                                f"  2. Re-run Thermal Network Part 2 with "
                                f"dh-temperature-mode = low-temperature\n"
                                f"  3. Re-run Thermal Network Part 2 with "
                                f"network-temperature-dh = {t_component:.0f} "
                                f"(or slightly below) to match the plant component"
                            )

    # --- DC check ---
    dc_temp_file = locator.get_network_temperature_plant('DC', network_name)
    if os.path.exists(dc_temp_file):
        # Get the district assembly for cooling
        if config.final_energy.overwrite_supply_settings:
            cs_assembly = config.final_energy.supply_type_cs_district
        else:
            supply_df = pd.read_csv(locator.get_building_supply())
            scale_mapping = load_all_assembly_scales(locator)
            cs_assembly = None
            if 'supply_type_cs' in supply_df.columns:
                for _, row in supply_df.iterrows():
                    code = row.get('supply_type_cs')
                    if code and not pd.isna(code) and scale_mapping.get(str(code)) == 'DISTRICT':
                        cs_assembly = str(code)
                        break

        if cs_assembly:
            components = load_assembly_components(cs_assembly, locator)
            primary_code = components.get('primary_components')
            t_component = get_component_dc_supply_temperature(primary_code, locator)

            if t_component is not None:
                temp_df = pd.read_csv(dc_temp_file)
                if 'temperature_supply_K' in temp_df.columns:
                    active = temp_df[temp_df['temperature_supply_K'] > 0]
                    if not active.empty:
                        t_network_K = active['temperature_supply_K'].min()
                        t_network_C = t_network_K - 273.15

                        if t_component > t_network_C + 0.5:  # 0.5°C tolerance for floating point
                            raise ValueError(
                                f"Temperature incompatibility: the selected DC plant assembly "
                                f"({cs_assembly}) uses {primary_code} with a minimum supply "
                                f"temperature of {t_component:.0f} degrees C, which is above the network "
                                f"supply temperature of {t_network_C:.0f} degrees C.\n\n"
                                f"Options:\n"
                                f"  1. Select a different assembly with a supply temperature "
                                f"lower than {t_network_C:.0f} degrees C\n"
                                f"  2. Re-run Thermal Network Part 2 with "
                                f"network-temperature-dc = {t_component:.0f} "
                                f"(or slightly above) to match the plant component"
                            )


def load_network_connectivity(locator, network_name):
    """
    Load and parse connectivity.json for the given network.

    :param locator: InputLocator instance
    :param network_name: Network layout name
    :return: Dict with connectivity data
    :raises ValueError: If file is missing
    """
    connectivity_file = locator.get_network_connectivity_file(network_name)

    if not os.path.exists(connectivity_file):
        raise ValueError(
            f"Network connectivity file not found for network '{network_name}'.\n\n"
            f"Expected at: {connectivity_file}\n\n"
            f"Please run 'network-layout' first to generate this file."
        )

    with open(connectivity_file, 'r') as f:
        return json.load(f)


def load_all_assembly_scales(locator):
    """
    Load assembly scale mapping from all SUPPLY databases.

    :param locator: InputLocator instance
    :return: Dict {assembly_code: scale}
             Example: {'SUPPLY_HEATING_AS3': 'BUILDING', 'SUPPLY_HEATING_AS9': 'DISTRICT'}
    """
    scale_mapping = {}

    for get_method in [
        locator.get_database_assemblies_supply_heating,
        locator.get_database_assemblies_supply_hot_water,
        locator.get_database_assemblies_supply_cooling,
    ]:
        filepath = get_method()
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            if 'code' in df.columns and 'scale' in df.columns:
                scale_mapping.update(df.set_index('code')['scale'].to_dict())

    return scale_mapping

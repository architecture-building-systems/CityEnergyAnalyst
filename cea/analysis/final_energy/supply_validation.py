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


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


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
        validate_network_mode(locator, network_name)


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

def validate_network_mode(locator, network_name):
    """
    Validate supply.csv matches network connectivity.json.

    Checks (all raise ValueError on failure):
    1. connectivity.json exists
    2. Buildings connected to DH have DISTRICT scale for their services in supply.csv
    3. Buildings connected to DC have DISTRICT scale for space_cooling in supply.csv
    4. Buildings in supply.csv with DISTRICT scale must appear in connectivity.json
    5. All DH buildings use the same space_heating assembly
    6. All DH buildings use the same domestic_hot_water assembly
    7. DH space_heating assembly == domestic_hot_water assembly (Option 1 rule)
    8. All DC buildings use the same space_cooling assembly

    :param locator: InputLocator instance
    :param network_name: Network layout name
    :raises ValueError: If any inconsistency is found
    """
    connectivity = load_network_connectivity(locator, network_name)
    supply_df = pd.read_csv(locator.get_building_supply())
    scale_mapping = load_all_assembly_scales(locator)

    if 'DH' in connectivity.get('networks', {}):
        validate_dh_consistency(connectivity['networks']['DH'], supply_df, scale_mapping)

    if 'DC' in connectivity.get('networks', {}):
        validate_dc_consistency(connectivity['networks']['DC'], supply_df, scale_mapping)

    # Check for buildings in supply.csv with DISTRICT scale that aren't in connectivity.json
    validate_no_orphaned_district_buildings(connectivity, supply_df, scale_mapping, network_name)


def validate_dh_consistency(dh_network, supply_df, scale_mapping):
    """
    Validate DH network consistency (Option 1: same plant serves hs + dhw).

    :param dh_network: Dict from connectivity.json['networks']['DH']
    :param supply_df: DataFrame from supply.csv
    :param scale_mapping: Dict {assembly_code: scale}
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

    # Option 1: hs assembly must equal dhw assembly (same plant, same fuel)
    if hs_assemblies and dhw_assemblies:
        hs_assembly = next(iter(set(hs_assemblies.values())))
        dhw_assembly = next(iter(set(dhw_assemblies.values())))

        if hs_assembly != dhw_assembly:
            raise ValueError(
                f"The district heating plant serves both space heating and domestic hot water "
                f"from the same source, so both must use the same assembly.\n\n"
                f"Currently:\n"
                f"  - space heating (supply_type_hs):       {hs_assembly}\n"
                f"  - domestic hot water (supply_type_dhw): {dhw_assembly}\n\n"
                f"Please set both to the same SUPPLY_HEATING assembly "
                f"(e.g., both use {hs_assembly})."
            )


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


def validate_no_orphaned_district_buildings(connectivity, supply_df, scale_mapping, network_name):
    """
    Check that no building in supply.csv has a DISTRICT-scale assembly
    without appearing in connectivity.json.

    :param connectivity: Dict from connectivity.json
    :param supply_df: DataFrame from supply.csv
    :param scale_mapping: Dict {assembly_code: scale}
    :param network_name: Network layout name (for error message)
    :raises ValueError: If any building has DISTRICT scale but is not in the network
    """
    # Collect all buildings connected to any network
    connected_dh = set(connectivity.get('networks', {}).get('DH', {}).get('per_building_services', {}).keys())
    connected_dc = set(connectivity.get('networks', {}).get('DC', {}).get('per_building_services', {}).keys())

    service_columns = {
        'supply_type_hs':  ('DH', 'space heating'),
        'supply_type_dhw': ('DH', 'domestic hot water'),
        'supply_type_cs':  ('DC', 'space cooling'),
    }

    mismatches = []

    for col, (network_type, service_label) in service_columns.items():
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
                mismatches.append(
                    f"  - {building}: {service_label} uses '{code}' (DISTRICT scale) "
                    f"but is not in {network_type} network '{network_name}'"
                )

    if mismatches:
        raise ValueError(
            "The following buildings have DISTRICT-scale assemblies in Building Properties/Supply "
            "but are not connected to the selected network. "
            "This may mean Building Properties/Supply was updated after running network-layout.\n\n"
            + "\n".join(mismatches)
            + "\n\nPlease either:\n"
            "  (a) Re-run 'network-layout' to regenerate connectivity.json, or\n"
            "  (b) Change these buildings to BUILDING-scale assemblies in Building Properties/Supply"
            "  (c) Set 'overwrite-supply-settings = True' in final-energy settings"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

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

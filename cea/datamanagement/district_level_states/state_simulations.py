from __future__ import annotations

import os
import shutil
from copy import deepcopy
from typing import Any

import geopandas as gpd
import pandas as pd

from cea.config import Configuration
from cea.datamanagement.utils import migrate_void_deck_data
from cea.datamanagement.district_level_states.district_emission_timeline import create_district_material_timeline
from cea.datamanagement.district_level_states.state_scenario import DistrictEventTimeline, DistrictStateYear
from cea.datamanagement.district_level_states.timeline_integrity import check_district_timeline_log_yaml_integrity
from cea.inputlocator import InputLocator

DISTRICT_SERVICES = ("DC", "DH")
SERVICE_LABELS = {"DC": "cooling", "DH": "heating"}
DH_ITEMISED_SERVICES = ["space_heating", "domestic_hot_water"]

EMISSIONS_STEP: dict[str, Any] = {
    "script": "emissions",
    "parameters": {
        "grid-decarbonise-reference-year": None,  # apply decarbonisation after timeline being assembled
        "grid-decarbonise-target-year": None,
        "grid-decarbonise-target-emission-factor": None,
    },
}


def should_include_photovoltaic(config: Configuration | None) -> bool:
    """Return whether Step 4 should keep the photovoltaic script in the base workflow."""
    if config is None:
        return True
    with config.ignore_restrictions():
        return bool(getattr(config.emissions, "include_pv", False))


def should_use_crax_radiation(state_locator: InputLocator) -> bool:
    """Return True when the state has no buildings with `void_deck > 0`."""
    try:
        migrate_void_deck_data(state_locator)
        zone_gdf = gpd.read_file(state_locator.get_zone_geometry())
    except Exception as exc:
        print(
            f"Warning: Could not inspect void_deck values for radiation engine selection: {exc}. "
            "Falling back to DAYSIM."
        )
        return False

    if "void_deck" not in zone_gdf.columns:
        return True

    void_deck = pd.to_numeric(zone_gdf["void_deck"], errors="coerce").fillna(0)
    return bool((void_deck <= 0).all())


def build_base_simulation_workflow(
    config: Configuration | None = None,
    *,
    use_crax_radiation: bool = False,
) -> list[dict[str, Any]]:
    workflow: list[dict[str, Any]] = [
        {"config": "."},  # use state-in-time scenario as base config
        {"script": "radiation-crax" if use_crax_radiation else "radiation"},
        {"script": "occupancy"},
        {"script": "demand"},
    ]
    if should_include_photovoltaic(config):
        workflow.append({"script": "photovoltaic"})
    return workflow


def prepare_base_workflow_for_state(
    config: Configuration,
    timeline_name: str,
    year: int,
) -> list[dict[str, Any]]:
    main_locator = InputLocator(config.scenario)
    state_locator = InputLocator(
        main_locator.get_state_in_time_scenario_folder(
            timeline_name=timeline_name, year_of_state=year
        )
    )
    use_crax_radiation = should_use_crax_radiation(state_locator)

    if use_crax_radiation:
        print(
            f"Warning: State {year} has no buildings with void_deck > 0. "
            "Using radiation-crax instead of radiation (DAYSIM)."
        )

    if not should_include_photovoltaic(config):
        print(
            f"State {year}: Skipping photovoltaic because emissions.include-pv is False."
        )

    return build_base_simulation_workflow(
        config,
        use_crax_radiation=use_crax_radiation,
    )


def build_default_workflow() -> list[dict[str, Any]]:
    workflow = build_base_simulation_workflow()
    workflow.append(deepcopy(EMISSIONS_STEP))
    return workflow


default_workflow = build_default_workflow()


def get_state_service_eligibility(
    state_locator: InputLocator,
) -> dict[str, dict[str, list[str]]]:
    """Return district-service eligibility per thermal service for one state scenario."""
    service_eligibility: dict[str, dict[str, list[str]]] = {}

    for network_type in DISTRICT_SERVICES:
        eligibility = {
            "district_buildings": [],
            "demand_buildings": [],
            "eligible_buildings": [],
        }
        try:
            district_buildings = sorted(set(get_buildings_with_district_service(state_locator, network_type)))
            demand_buildings = sorted(set(get_buildings_with_demand_for_service(state_locator, network_type)))
            eligible_buildings = sorted(set(district_buildings) & set(demand_buildings))

            eligibility["district_buildings"] = district_buildings
            eligibility["demand_buildings"] = demand_buildings
            eligibility["eligible_buildings"] = eligible_buildings
        except FileNotFoundError as exc:
            print(f"Warning: Could not check {network_type} requirements - {exc}")
        except Exception as exc:
            print(f"Warning: Error checking {network_type} requirements - {exc}")

        service_eligibility[network_type] = eligibility

    return service_eligibility


def determine_required_services_for_state(state_locator: InputLocator) -> list[str]:
    """
    Determine which district thermal services (DC, DH, or both) are required for a state.

    This function performs proactive checks to determine if a state needs district cooling
    and/or heating networks by examining:
    1. Building supply properties (which buildings use DISTRICT scale systems)
    2. Building demand data (which buildings have actual demand)

    Args:
        state_locator: InputLocator for the state-in-time scenario.
            Example: InputLocator("C:/scenario/district_timelines/timeline1/state_2025")

    Returns:
        List of required services based on buildings with district configuration AND demand:
            - ['DC'] if only district cooling is needed
            - ['DH'] if only district heating is needed
            - ['DC', 'DH'] if both services are needed
            - [] if no district services are needed
    """
    service_eligibility = get_state_service_eligibility(state_locator)
    return [
        network_type
        for network_type in DISTRICT_SERVICES
        if service_eligibility.get(network_type, {}).get("eligible_buildings")
    ]


def get_buildings_with_district_service(locator: InputLocator, network_type: str) -> list[str]:
    """
    Get buildings configured to use district heating or cooling from supply.csv.

    Reads Building Properties/Supply and checks which buildings have supply types
    configured at DISTRICT scale by cross-referencing supply codes with assemblies databases.

    Args:
        locator: InputLocator instance for the scenario to check.
        network_type: Type of network to check. Either:
            - "DH" = district heating (checks supply_type_hs and supply_type_dhw)
            - "DC" = district cooling (checks supply_type_cs)

    Returns:
        List of building names with DISTRICT scale service.
            Example: ['B001', 'B003', 'B010'] or [] if none found
    """
    supply_df = pd.read_csv(locator.get_building_supply())
    
    # Read assemblies databases for code-to-scale mapping
    scale_mapping = {}
    
    if network_type == "DH":
        heating_assemblies_df = pd.read_csv(locator.get_database_assemblies_supply_heating())
        hotwater_assemblies_df = pd.read_csv(locator.get_database_assemblies_supply_hot_water())
        scale_mapping.update(heating_assemblies_df.set_index('code')['scale'].to_dict())
        scale_mapping.update(hotwater_assemblies_df.set_index('code')['scale'].to_dict())
    else:  # DC
        cooling_assemblies_df = pd.read_csv(locator.get_database_assemblies_supply_cooling())
        scale_mapping = cooling_assemblies_df.set_index('code')['scale'].to_dict()
    
    buildings_with_district = []
    
    for _, row in supply_df.iterrows():
        building_name = row['name']
        has_district_service = False
        
        # Check space heating service (DH only)
        if network_type == "DH" and 'supply_type_hs' in supply_df.columns:
            hs_code = row.get('supply_type_hs', None)
            if hs_code and not pd.isna(hs_code):
                hs_scale = scale_mapping.get(hs_code, None)
                if hs_scale == 'DISTRICT':
                    has_district_service = True
        
        # Check domestic hot water service (DH only)
        if network_type == "DH" and 'supply_type_dhw' in supply_df.columns:
            dhw_code = row.get('supply_type_dhw', None)
            if dhw_code and not pd.isna(dhw_code):
                dhw_scale = scale_mapping.get(dhw_code, None)
                if dhw_scale == 'DISTRICT':
                    has_district_service = True
        
        # Check cooling service (DC only)
        if network_type == "DC" and 'supply_type_cs' in supply_df.columns:
            cs_code = row.get('supply_type_cs', None)
            if cs_code and not pd.isna(cs_code):
                cs_scale = scale_mapping.get(cs_code, None)
                if cs_scale == 'DISTRICT':
                    has_district_service = True
        
        if has_district_service:
            buildings_with_district.append(building_name)
    
    return buildings_with_district


def get_buildings_with_demand_for_service(locator: InputLocator, network_type: str) -> list[str]:
    """
    Get buildings with actual heating or cooling demand from total_demand.csv.

    Checks annual energy demand to identify buildings that actually need the service,
    avoiding network generation for buildings with zero demand.

    Args:
        locator: InputLocator instance for the scenario to check.
            Example: InputLocator("C:/scenario/district_timelines/timeline1/state_2025")
        network_type: Type of demand to check. Either:
            - "DH" = district heating (checks QH_sys_MWhyr > 0)
            - "DC" = district cooling (checks QC_sys_MWhyr > 0)

    Returns:
        List of building names with demand > 0.
            Example: ['B001', 'B002', 'B010'] or [] if no buildings have demand
    """
    demand_path = locator.get_total_demand()
    total_demand = pd.read_csv(demand_path)
    
    # Determine demand field based on network type
    if network_type == "DH":
        # For DH: use QH_sys_MWhyr (total heating including space heating + DHW)
        field = "QH_sys_MWhyr"
        buildings_with_demand = total_demand[
            total_demand[field] > 0.0
        ]['name'].tolist()
    else:  # DC
        field = "QC_sys_MWhyr"
        buildings_with_demand = total_demand[
            total_demand[field] > 0.0
        ]['name'].tolist()
    
    return buildings_with_demand


def find_latest_network_folder(
    main_locator: InputLocator,
    timeline_name: str,
    current_year: int,
    state_years: list[int],
) -> tuple[str | None, int | None]:
    """
    Find the latest previous state year that has a thermal network folder.

    Searches backward in time through previous state years to find the most recent
    thermal network layout that can be used as a starting point for the current year.

    Args:
        main_locator: InputLocator for the main scenario (not a state folder).
            Example: InputLocator("C:/scenario")
        timeline_name: Name of the timeline to search in.
            Example: "baseline_scenario" or "test_timeline"
        current_year: Current state year being prepared.
            Example: 2040
        state_years: List of all state years in the timeline (sorted ascending).
            Example: [2000, 2025, 2040, 2050]

    Returns:
        Tuple of (network_name, source_year) or (None, None):
            - If found: ("thermal_network_2025", 2025)
            - If not found: (None, None)
        
        Example scenarios:
            - For current_year=2040 with existing network in 2025:
              Returns ("thermal_network_2025", 2025)
            - For current_year=2000 (first state):
              Returns (None, None)
    """
    # Get all previous years (in descending order)
    previous_years = [y for y in state_years if y < current_year]
    previous_years.sort(reverse=True)
    
    for year in previous_years:
        # Create locator for previous state
        previous_state_locator = InputLocator(
            main_locator.get_state_in_time_scenario_folder(
                timeline_name=timeline_name, year_of_state=year
            )
        )
        
        # Check if thermal-network output folder exists
        thermal_network_base = previous_state_locator.get_thermal_network_folder()
        
        if not os.path.exists(thermal_network_base):
            continue
        
        # Look for network folder matching pattern "thermal_network_{year}"
        expected_network_name = f"thermal_network_{year}"
        network_folder = previous_state_locator.get_thermal_network_folder_network_name_folder(
            expected_network_name
        )
        
        if os.path.exists(network_folder):
            # Check if it has layout files (not just DC/DH subfolders)
            layout_shp = previous_state_locator.get_network_layout_shapefile(expected_network_name)
            has_layout = os.path.exists(layout_shp)
            
            if has_layout:
                return expected_network_name, year
    
    return None, None


def copy_network_layout_files(
    source_network_folder: str,
    target_network_folder: str,
) -> None:
    """
    Copy the reusable network-layout artefacts from source to target.

    Copies the root `layout.*` files plus the service-specific `DC/layout` and `DH/layout`
    subfolders. Those service layout folders contain the `nodes.shp` files that
    `network-layout --existing-network` requires for augment / filter / validate mode,
    while still avoiding the large hourly simulation outputs elsewhere in `DC/` and `DH/`.

    Args:
        source_network_folder: Absolute path to source network folder (from previous state).
            Example: "C:/scenario/district_timelines/timeline1/state_2025/outputs/data/thermal-network/thermal_network_2025"
        target_network_folder: Absolute path to target network folder (current state).
            Example: "C:/scenario/district_timelines/timeline1/state_2040/outputs/data/thermal-network/thermal_network_2025"
    
    Files copied:
        - Root-level layout files (e.g. `layout.shp`, `layout.dbf`, ...)
        - `DC/layout/*` if present
        - `DH/layout/*` if present

    Files skipped:
        - Other files and folders under `DC/` and `DH/` (hourly simulation outputs, reports, etc.)
    """
    os.makedirs(target_network_folder, exist_ok=True)

    for item in os.listdir(source_network_folder):
        source_item = os.path.join(source_network_folder, item)

        if os.path.isdir(source_item) and item in ['DC', 'DH']:
            source_layout_folder = os.path.join(source_item, 'layout')
            if os.path.isdir(source_layout_folder):
                target_layout_folder = os.path.join(target_network_folder, item, 'layout')
                shutil.copytree(source_layout_folder, target_layout_folder, dirs_exist_ok=True)
            continue

        target_item = os.path.join(target_network_folder, item)

        if os.path.isfile(source_item):
            shutil.copy2(source_item, target_item)
        elif os.path.isdir(source_item):
            shutil.copytree(source_item, target_item, dirs_exist_ok=True)


def build_network_layout_step(
    year: int,
    required_services: list[str],
    service_eligibility: dict[str, dict[str, list[str]]],
    previous_network_name: str | None,
) -> dict[str, Any]:
    network_name = f"thermal_network_{year}"
    return {
        "script": "network-layout",
        "parameters": {
            "network-name": network_name,
            "include-services": required_services,
            "overwrite-supply-settings": True,
            "itemised-dh-services": list(DH_ITEMISED_SERVICES),
            "heating-connected-buildings": list(service_eligibility["DH"]["eligible_buildings"]),
            "cooling-connected-buildings": list(service_eligibility["DC"]["eligible_buildings"]),
            "network-layout-mode": "augment",
            "auto-modify-network": True,
            "existing-network": previous_network_name,
        },
    }


def build_thermal_network_step(year: int, required_services: list[str]) -> dict[str, Any]:
    network_name = f"thermal_network_{year}"
    return {
        "script": "thermal-network",
        "parameters": {
            "network-name": [network_name],
            "network-type": list(required_services),
            "multi-phase-mode": False,
        },
    }


def cleanup_target_network_outputs(state_locator: InputLocator, year: int) -> None:
    """Remove stale current-year network outputs before rerunning network-layout."""
    network_name = f"thermal_network_{year}"
    target_network_folder = state_locator.get_thermal_network_folder_network_name_folder(
        network_name
    )
    if not os.path.exists(target_network_folder):
        return

    print(
        f"Warning: State {year} already contains network outputs for '{network_name}'. "
        "Removing the stale current-year folder before rerunning network-layout."
    )
    shutil.rmtree(target_network_folder)


def prepare_post_demand_workflow_for_state(
    config: Configuration,
    timeline_name: str,
    year: int,
    state_years: list[int],
) -> list[dict[str, Any]]:
    """
    Prepare the post-demand part of the Step 4 workflow for one state year.

    This function:
    1. Reads the freshly generated demand outputs for the state
    2. Determines per-service district-network eligibility
    3. Finds and copies the latest previous network layout if available
    4. Builds the remaining per-state workflow:
       optional network-layout -> optional thermal-network -> emissions

    Args:
        config: Main configuration object pointing to the main scenario.
        timeline_name: Name of the timeline being processed.
        year: State year being prepared.
        state_years: All state years in the timeline, sorted ascending.

    Returns:
        Remaining workflow steps for this state:
            - `[emissions]` if no district services are needed
            - `[network-layout, thermal-network, emissions]` otherwise
    """
    main_locator = InputLocator(config.scenario)
    state_locator = InputLocator(
        main_locator.get_state_in_time_scenario_folder(
            timeline_name=timeline_name, year_of_state=year
        )
    )

    service_eligibility = get_state_service_eligibility(state_locator)
    required_services = [
        network_type
        for network_type in DISTRICT_SERVICES
        if service_eligibility[network_type]["eligible_buildings"]
    ]

    for network_type in DISTRICT_SERVICES:
        district_buildings = service_eligibility[network_type]["district_buildings"]
        eligible_buildings = service_eligibility[network_type]["eligible_buildings"]
        if eligible_buildings:
            service_name = SERVICE_LABELS[network_type]
            print(
                f"State {year}: {network_type} network required for "
                f"{len(eligible_buildings)} building(s) with district {service_name} and positive demand."
            )
        elif district_buildings:
            service_name = SERVICE_LABELS[network_type]
            print(
                f"State {year}: Skipping {network_type} network because no buildings have both "
                f"district {service_name} supply and positive demand."
            )

    workflow = []
    if not required_services:
        print(
            f"State {year}: No district thermal services required. "
            "Skipping network-layout and thermal-network."
        )
        workflow.append(deepcopy(EMISSIONS_STEP))
        return workflow

    cleanup_target_network_outputs(state_locator, year)

    previous_network_name, source_year = find_latest_network_folder(
        main_locator, timeline_name, year, state_years
    )

    if previous_network_name and source_year:
        print(
            f"State {year}: Found previous network '{previous_network_name}' "
            f"from state {source_year}. Copying layout files..."
        )

        source_state_locator = InputLocator(
            main_locator.get_state_in_time_scenario_folder(
                timeline_name=timeline_name, year_of_state=source_year
            )
        )

        source_network_folder = source_state_locator.get_thermal_network_folder_network_name_folder(
            previous_network_name
        )
        target_network_folder = state_locator.get_thermal_network_folder_network_name_folder(
            previous_network_name
        )
        
        try:
            copy_network_layout_files(source_network_folder, target_network_folder)
            print(f"State {year}: Successfully copied network layout from state {source_year}.")
        except Exception as exc:
            print(
                f"Warning: Failed to copy network from state {source_year}: {exc}. "
                f"Will generate new layout."
            )
            previous_network_name = None
    else:
        print(
            f"State {year}: No previous network found. "
            f"Will generate new layout from scratch."
        )

    workflow.append(
        build_network_layout_step(
            year=year,
            required_services=required_services,
            service_eligibility=service_eligibility,
            previous_network_name=previous_network_name,
        )
    )
    workflow.append(build_thermal_network_step(year, required_services))
    workflow.append(deepcopy(EMISSIONS_STEP))

    services_str = ", ".join(required_services)
    print(
        f"State {year}: Adding network-layout and thermal-network steps with services: {services_str}"
    )

    return workflow


def prepare_workflow_for_state(
    config: Configuration,
    timeline_name: str,
    year: int,
    state_years: list[int],
) -> list[dict[str, Any]]:
    """
    Prepare the full Step 4 workflow for a specific state year.

    This helper is useful when demand outputs already exist. The runtime execution path
    now uses `prepare_base_workflow_for_state(...)` first and only then calls
    `prepare_post_demand_workflow_for_state(...)` so service eligibility can use the
    current state's fresh `Total_demand.csv`.
    """
    workflow = prepare_base_workflow_for_state(
        config=config,
        timeline_name=timeline_name,
        year=year,
    )
    workflow.extend(
        prepare_post_demand_workflow_for_state(
            config=config,
            timeline_name=timeline_name,
            year=year,
            state_years=state_years,
        )
    )
    return workflow


def simulate_all_states(config: Configuration, timeline_name: str) -> None:
    """
    Simulate all state-in-time scenarios as per the district timeline log YAML file.

    Each state gets a customised workflow that includes network-layout and thermal-network
    only if the state has buildings using district heating/cooling with actual demand.
    Emissions always run last. This is the main orchestration function that prepares
    per-state workflows and executes simulations.

    Args:
        config: The configuration object pointing to the main scenario folder.
        timeline_name: Name of the timeline to simulate.
    
    Process:
        1. Loads timeline and validates state/log integrity
        2. Runs the base workflow through `demand` for each target state
        3. Prepares and runs the post-demand workflow (network steps if needed, then emissions)
        4. Updates timeline log with simulation metadata

    Notes:
        Step 4 always reruns all state years. Existing-network reuse makes the state
        sequence interdependent, so this wrapper no longer offers a pending-only mode.
    """
    timeline = DistrictEventTimeline(config, timeline_name=timeline_name)

    check_district_timeline_log_yaml_integrity(config, timeline_name)

    state_years = timeline.list_state_years_on_disk()
    if not state_years:
        raise ValueError(
            "No state-in-time scenarios found in the district timeline folder."
        )
    state_years.sort()

    years_to_simulate = list(state_years)

    print("\n" + "=" * 80)
    print("Starting state simulations for all state-in-time scenarios...")
    print("=" * 80)
    print(f"Found state years: {state_years}")
    print(f"Years to simulate: {years_to_simulate}\n")

    if not years_to_simulate:
        print("Nothing to simulate: all state years are up to date.")
        return

    simulated_years: list[int] = []
    skipped_years = [year for year in state_years if year not in set(years_to_simulate)]
    for year in years_to_simulate:
        base_workflow = prepare_base_workflow_for_state(
            config=config,
            timeline_name=timeline_name,
            year=int(year),
        )
        print(f"\n--- Simulating state {year}: base workflow ---")
        state = DistrictStateYear(
            timeline_name=timeline.timeline_name,
            year=int(year),
            modifications={},
            main_locator=timeline.main_locator,
        )
        state.simulate(config, workflow=base_workflow, mark_simulated=False)

        print(f"\n--- Simulating state {year}: post-demand workflow ---")
        post_demand_workflow = prepare_post_demand_workflow_for_state(
            config=config,
            timeline_name=timeline_name,
            year=int(year),
            state_years=state_years,
        )
        full_workflow = deepcopy(base_workflow) + deepcopy(post_demand_workflow)
        state.simulate(
            config,
            workflow=post_demand_workflow,
            recorded_workflow=full_workflow,
        )

        entry = timeline.log_data.get(int(year), {}) or {}
        entry["simulation_workflow"] = full_workflow
        entry["latest_simulated_at"] = str(pd.Timestamp.now())
        timeline.log_data[int(year)] = entry

        simulated_years.append(int(year))
        print(f"Simulation for state-in-time scenario year {year} completed.")

    timeline.save()

    print("State-in-time simulations finished.")
    print(f"Simulated: {len(simulated_years)} years")
    if simulated_years:
        print(f"Years simulated: {simulated_years}")
    print(f"Skipped: {len(skipped_years)} years")
    if skipped_years:
        print(f"Years skipped: {skipped_years}")


def main(config: Configuration) -> None:
    timeline_name = config.state_simulations.existing_timeline_name
    if not timeline_name:
        raise ValueError(
            "No existing timeline name provided. "
            "Please provide an existing timeline name to simulate all states from."
        )
    simulate_all_states(config, timeline_name=timeline_name)
    print("All state-in-time scenarios have been simulated.")
    df = create_district_material_timeline(config, timeline_variant_name=timeline_name)
    print(f"District material timeline saved with {len(df)} years.")

if __name__ == "__main__":
    main(Configuration())

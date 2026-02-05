from __future__ import annotations

import os
import shutil
from typing import Literal, Any
import pandas as pd

from cea.config import Configuration
from cea.inputlocator import InputLocator
from cea.datamanagement.district_level_states.state_scenario import DistrictEventTimeline
from cea.datamanagement.district_level_states.district_emission_timeline import create_district_material_timeline

default_workflow: list[dict[str, Any]] = [
    {"config": "."},  # use state-in-time scenario as base config
    {"script": "radiation"},
    {"script": "occupancy"},
    {"script": "demand"},
    {"script": "photovoltaic"},
    {
        "script": "emissions",
        "parameters": {
            "grid-decarbonise-reference-year": None, # apply decarbonisation after timeline being assembled
            "grid-decarbonise-target-year": None,
            "grid-decarbonise-target-emission-factor": None,
        },
    },
]


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
    required_services = []

    # Check both DC and DH
    for network_type in ['DC', 'DH']:
        try:
            # Check 1: Buildings configured for district service in supply.csv
            buildings_with_district_service = get_buildings_with_district_service(
                state_locator, network_type
            )
            
            if not buildings_with_district_service:
                continue
            
            # Check 2: Buildings with actual demand
            buildings_with_demand = get_buildings_with_demand_for_service(
                state_locator, network_type
            )
            
            if not buildings_with_demand:
                service_name = "cooling" if network_type == "DC" else "heating"
                print(
                    f"Warning: Buildings configured for district {service_name} "
                    f"but none have actual demand. Skipping {network_type} network."
                )
                continue
            
            # Check 3: Intersection - buildings that have both district service AND demand
            buildings_needing_network = set(buildings_with_district_service) & set(buildings_with_demand)
            
            if buildings_needing_network:
                required_services.append(network_type)
                service_name = "cooling" if network_type == "DC" else "heating"
                print(
                    f"State requires {network_type} network: "
                    f"{len(buildings_needing_network)} buildings with district {service_name}"
                )
        
        except FileNotFoundError as e:
            print(f"Warning: Could not check {network_type} requirements - {e}")
            continue
        except Exception as e:
            print(f"Warning: Error checking {network_type} requirements - {e}")
            continue
    
    return required_services


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
    Copy thermal network layout files from source to target, excluding DC/DH subfolders.

    Copies only the shapefile components (layout.shp, .dbf, .prj, .cpg, .shx) and any
    other files directly in the network folder, but skips the DC and DH subfolders
    to keep size manageable (those contain hourly simulation results which can be GBs).

    Args:
        source_network_folder: Absolute path to source network folder (from previous state).
            Example: "C:/scenario/district_timelines/timeline1/state_2025/outputs/data/thermal-network/thermal_network_2025"
        target_network_folder: Absolute path to target network folder (current state).
            Example: "C:/scenario/district_timelines/timeline1/state_2040/outputs/data/thermal-network/thermal_network_2025"
    
    Files copied:
        - layout.shp, layout.dbf, layout.prj, layout.cpg, layout.shx (shapefile components)
        - Any other files in the root of the network folder
    
    Files skipped:
        - DC/ subfolder (contains cooling network simulation results)
        - DH/ subfolder (contains heating network simulation results)
    """
    os.makedirs(target_network_folder, exist_ok=True)
    
    # Copy all files in the source folder (but not subfolders)
    for item in os.listdir(source_network_folder):
        source_item = os.path.join(source_network_folder, item)
        
        # Skip DC and DH subdirectories
        if os.path.isdir(source_item) and item in ['DC', 'DH']:
            continue
        
        target_item = os.path.join(target_network_folder, item)
        
        if os.path.isfile(source_item):
            shutil.copy2(source_item, target_item)
        elif os.path.isdir(source_item):
            # Copy other subdirectories if they exist
            shutil.copytree(source_item, target_item, dirs_exist_ok=True)


def prepare_workflow_for_state(
    config: Configuration,
    timeline_name: str,
    year: int,
    state_years: list[int],
) -> list[dict]:
    """
    Prepare workflow for a specific state year, with thermal network step if needed.

    This function:
    1. Determines if the state needs DC/DH networks (proactive check)
    2. Finds and copies the latest previous network layout if available
    3. Builds workflow dict with appropriate network-layout parameters

    Args:
        config: Main configuration object pointing to the main scenario.
            Example: Configuration() with scenario="C:/scenario"
        timeline_name: Name of the timeline being processed.
            Example: "baseline_scenario" or "test_timeline"
        year: State year to prepare workflow for.
            Example: 2040
        state_years: List of all state years in timeline (sorted ascending).
            Example: [2000, 2025, 2040, 2050]

    Returns:
        Workflow list for this specific state year. Either:
            - Default workflow if no district services needed
            - Default workflow + network-layout step if district services needed
        
        Example return with network:
            [
                {"config": "."},
                {"script": "radiation"},
                ...,
                {"script": "network-layout", "parameters": {
                    "network-name": "thermal_network_2040",
                    "include-services": ["DC", "DH"],
                    "overwrite-supply-settings": False,
                    "itemised-dh-services": ["space_heating", "domestic_hot_water"],
                    "existing-network": "thermal_network_2025"
                }}
            ]
    """
    main_locator = InputLocator(config.scenario)
    state_locator = InputLocator(
        main_locator.get_state_in_time_scenario_folder(
            timeline_name=timeline_name, year_of_state=year
        )
    )
    
    # Determine required services for this state
    required_services = determine_required_services_for_state(state_locator)
    
    if not required_services:
        print(f"State {year}: No district thermal services required. Skipping network-layout.")
        return list(default_workflow)
    
    # Find latest previous network
    previous_network_name, source_year = find_latest_network_folder(
        main_locator, timeline_name, year, state_years
    )
    
    # Prepare network-layout parameters
    network_name = f"thermal_network_{year}"
    network_params = {
        "network-name": network_name,
        "include-services": required_services,
        "overwrite-supply-settings": False,
        "itemised-dh-services": ["space_heating", "domestic_hot_water"],
    }
    
    # Handle existing network reference
    if previous_network_name and source_year:
        print(
            f"State {year}: Found previous network '{previous_network_name}' "
            f"from state {source_year}. Copying layout files..."
        )
        
        # Create locator for source state
        source_state_locator = InputLocator(
            main_locator.get_state_in_time_scenario_folder(
                timeline_name=timeline_name, year_of_state=source_year
            )
        )
        
        # Get source and target network folder paths using locator methods
        source_network_folder = source_state_locator.get_thermal_network_folder_network_name_folder(
            previous_network_name
        )
        target_network_folder = state_locator.get_thermal_network_folder_network_name_folder(
            previous_network_name
        )
        
        try:
            copy_network_layout_files(source_network_folder, target_network_folder)
            network_params["existing-network"] = previous_network_name
            print(f"State {year}: Successfully copied network layout from state {source_year}.")
        except Exception as e:
            print(
                f"Warning: Failed to copy network from state {source_year}: {e}. "
                f"Will generate new layout."
            )
    else:
        print(
            f"State {year}: No previous network found. "
            f"Will generate new layout from scratch."
        )
    
    # Build workflow with network-layout step
    workflow = list(default_workflow)
    workflow.append({
        "script": "network-layout",
        "parameters": network_params,
    })
    
    services_str = ", ".join(required_services)
    print(f"State {year}: Adding network-layout step with services: {services_str}")
    
    return workflow


def simulate_all_states(config: Configuration, timeline_name: str) -> None:
    """
    Simulate all state-in-time scenarios as per the district timeline log YAML file.

    Each state gets a customised workflow that includes network-layout only if the state
    has buildings using district heating/cooling with actual demand. This is the main
    orchestration function that prepares per-state workflows and executes simulations.

    Args:
        config: The configuration object pointing to the main scenario folder.
        timeline_name: Name of the timeline to simulate.
    
    Process:
        1. Loads timeline and gets all state years
        2. Prepares custom workflow for each state (with/without network-layout)
        3. Executes simulations in sequence (or only pending states)
        4. Updates timeline log with simulation metadata
    """
    timeline = DistrictEventTimeline(config, timeline_name=timeline_name)
    
    # Get all state years in the timeline
    state_years = sorted([state.year for state in timeline.state_years()])
    
    # Determine simulation mode
    simulation_mode: Literal["pending", "all"]
    if getattr(config.state_simulations, "simulation_mode", "all") == "pending":
        simulation_mode = "pending"
    else:
        simulation_mode = "all"
    
    # Prepare per-state workflows
    print("\n" + "="*80)
    print("Preparing workflows for all states...")
    print("="*80)
    
    state_workflows: dict[int, list[dict[str, Any]]] = {}
    for year in state_years:
        print(f"\n--- Preparing workflow for state {year} ---")
        workflow = prepare_workflow_for_state(
            config, timeline_name, year, state_years
        )
        state_workflows[year] = workflow
    
    print("\n" + "="*80)
    print("Starting state simulations...")
    print("="*80 + "\n")
    
    # Simulate states with customised workflows (per-state)
    timeline.simulate_states(
        simulation_mode=simulation_mode,
        workflow=list(default_workflow),  # Fallback workflow
        state_workflows=state_workflows,  # Custom workflows per state
    )


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

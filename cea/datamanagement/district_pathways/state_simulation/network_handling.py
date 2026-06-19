from __future__ import annotations

import os
import shutil

from cea.inputlocator import InputLocator


def find_previous_network(
    main_locator: InputLocator,
    pathway_name: str,
    year: int,
    state_years: list[int],
) -> tuple[str | None, int | None]:
    """Return the latest previous network name and source year with reusable layout files."""
    previous_years = sorted(
        (state_year for state_year in state_years if state_year < year),
        reverse=True,
    )

    for source_year in previous_years:
        source_state_locator = InputLocator(
            main_locator.get_state_in_time_scenario_folder(
                pathway_name=pathway_name, year_of_state=source_year
            )
        )
        thermal_network_folder = source_state_locator.get_thermal_network_folder()
        if not os.path.exists(thermal_network_folder):
            continue

        network_name = f"thermal_network_{source_year}"
        network_folder = source_state_locator.get_thermal_network_folder_network_name_folder(
            network_name
        )
        layout_shapefile = source_state_locator.get_network_layout_shapefile(network_name)
        if os.path.exists(network_folder) and os.path.exists(layout_shapefile):
            return network_name, source_year

    return None, None


def copy_previous_network_layout(
    source_network_folder: str,
    target_network_folder: str,
) -> None:
    """Copy the reusable network-layout artefacts for existing-network augment mode."""
    os.makedirs(target_network_folder, exist_ok=True)

    for item in os.listdir(source_network_folder):
        source_item = os.path.join(source_network_folder, item)

        if os.path.isdir(source_item) and item in ["DC", "DH"]:
            source_layout_folder = os.path.join(source_item, "layout")
            if os.path.isdir(source_layout_folder):
                target_layout_folder = os.path.join(target_network_folder, item, "layout")
                shutil.copytree(source_layout_folder, target_layout_folder, dirs_exist_ok=True)
            continue

        target_item = os.path.join(target_network_folder, item)
        if os.path.isfile(source_item):
            shutil.copy2(source_item, target_item)
        elif os.path.isdir(source_item):
            shutil.copytree(source_item, target_item, dirs_exist_ok=True)


def cleanup_current_network_outputs(state_locator: InputLocator, year: int) -> None:
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


def copy_previous_network_for_state(
    main_locator: InputLocator,
    state_locator: InputLocator,
    pathway_name: str,
    year: int,
    state_years: list[int],
) -> str | None:
    """Copy the latest previous network into the current state and return its network name."""
    previous_network_name, source_year = find_previous_network(
        main_locator=main_locator,
        pathway_name=pathway_name,
        year=year,
        state_years=state_years,
    )
    if previous_network_name is None or source_year is None:
        print(f"State {year}: No previous network found. Will generate new layout from scratch.")
        return None

    print(
        f"State {year}: Found previous network '{previous_network_name}' "
        f"from state {source_year}. Copying layout files..."
    )

    source_state_locator = InputLocator(
        main_locator.get_state_in_time_scenario_folder(
            pathway_name=pathway_name, year_of_state=source_year
        )
    )
    source_network_folder = source_state_locator.get_thermal_network_folder_network_name_folder(
        previous_network_name
    )
    target_network_folder = state_locator.get_thermal_network_folder_network_name_folder(
        previous_network_name
    )

    try:
        copy_previous_network_layout(source_network_folder, target_network_folder)
        print(f"State {year}: Successfully copied network layout from state {source_year}.")
        return previous_network_name
    except Exception as exc:
        print(
            f"Warning: Failed to copy network from state {source_year}: {exc}. "
            "Will generate new layout."
        )
        return None

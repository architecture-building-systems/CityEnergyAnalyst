from __future__ import annotations

from copy import deepcopy
from typing import Any

import geopandas as gpd
import pandas as pd

from cea.config import Configuration
from cea.datamanagement.utils import migrate_void_deck_data
from cea.datamanagement.district_level_states.state_simulation import network_handling
from cea.datamanagement.district_level_states.state_simulation import service_checks
from cea.inputlocator import InputLocator

EMISSIONS_STEP: dict[str, Any] = {
    "script": "emissions",
    "parameters": {
        "grid-decarbonise-reference-year": None,
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


def build_base_workflow(
    config: Configuration | None = None,
    *,
    use_crax_radiation: bool = False,
) -> list[dict[str, Any]]:
    """Build the Step 4 pre-network workflow for a state year."""
    workflow: list[dict[str, Any]] = [
        {"config": "."},
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
    """Prepare the pre-network workflow for one state year."""
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
        print(f"State {year}: Skipping photovoltaic because emissions.include-pv is False.")

    return build_base_workflow(config, use_crax_radiation=use_crax_radiation)


def build_network_layout_step(
    year: int,
    required_services: list[str],
    previous_network_name: str | None,
    dh_network_services: list[str] | None = None,
) -> dict[str, Any]:
    """Build the `network-layout` step for one state year."""
    network_name = f"thermal_network_{year}"
    parameters: dict[str, Any] = {
        "network-name": network_name,
        "include-services": required_services,
        "overwrite-supply-settings": False,
        "network-layout-mode": "augment",
        "auto-modify-network": True,
        "existing-network": previous_network_name,
    }

    if "DH" in required_services:
        if not dh_network_services:
            raise ValueError(
                f"State {year}: DH network requested but no district DH services were "
                "derived from the state's supply settings."
            )
        parameters["itemised-dh-services"] = list(dh_network_services)

    return {
        "script": "network-layout",
        "parameters": parameters,
    }


def build_thermal_network_step(year: int, required_services: list[str]) -> dict[str, Any]:
    """Build the single-phase `thermal-network` step for one state year."""
    network_name = f"thermal_network_{year}"
    return {
        "script": "thermal-network",
        "parameters": {
            "network-name": [network_name],
            "network-type": list(required_services),
            "multi-phase-mode": False,
        },
    }


def prepare_post_demand_workflow_for_state(
    config: Configuration,
    timeline_name: str,
    year: int,
    state_years: list[int],
) -> list[dict[str, Any]]:
    """Prepare the post-demand tail for one state year."""
    main_locator = InputLocator(config.scenario)
    state_locator = InputLocator(
        main_locator.get_state_in_time_scenario_folder(
            timeline_name=timeline_name, year_of_state=year
        )
    )

    service_eligibility = service_checks.get_state_service_eligibility(state_locator)
    required_services = service_checks.get_required_services(service_eligibility)
    service_checks.report_service_requirements(year, service_eligibility)

    if not required_services:
        print(
            f"State {year}: No district thermal services required. "
            "Skipping network-layout and thermal-network."
        )
        return [deepcopy(EMISSIONS_STEP)]

    network_handling.cleanup_current_network_outputs(state_locator, year)
    previous_network_name = network_handling.copy_previous_network_for_state(
        main_locator=main_locator,
        state_locator=state_locator,
        timeline_name=timeline_name,
        year=year,
        state_years=state_years,
    )
    dh_network_services: list[str] = []
    if "DH" in required_services:
        dh_network_services = service_checks.get_state_dh_network_services(state_locator)
        services_str = " -> ".join(dh_network_services)
        print(
            f"State {year}: DH service mix from supply settings: {services_str}"
        )

    workflow = [
        build_network_layout_step(
            year=year,
            required_services=required_services,
            previous_network_name=previous_network_name,
            dh_network_services=dh_network_services,
        ),
        build_thermal_network_step(year, required_services),
        deepcopy(EMISSIONS_STEP),
    ]

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
    """Prepare the full Step 4 workflow for one state year."""
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

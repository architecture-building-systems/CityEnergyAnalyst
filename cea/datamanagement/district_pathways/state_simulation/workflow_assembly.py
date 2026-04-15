from __future__ import annotations

import json
import os
from copy import deepcopy
from enum import Enum
from typing import Any

import geopandas as gpd
import pandas as pd

from cea.config import Configuration
from cea.datamanagement.utils import migrate_void_deck_data
from cea.datamanagement.district_pathways.state_simulation import network_handling
from cea.datamanagement.district_pathways.state_simulation import service_checks
from cea.inputlocator import InputLocator

FINAL_ENERGY_STEP: dict[str, Any] = {
    "script": "final-energy",
    "parameters": {
        "overwrite-supply-settings": False,
        "what-if-name": "default",
        "network-name": None,
    },
}

EMISSIONS_STEP: dict[str, Any] = {
    "script": "emissions",
    "parameters": {
        "what-if-name": "default",
        "year-end": None,
        "grid-decarbonise-reference-year": None,
        "grid-decarbonise-target-year": None,
        "grid-decarbonise-target-emission-factor": None,
    },
}


class NetworkPhaseMode(Enum):
    """Network phasing mode for pathway simulation."""
    NONE = "none"
    SINGLE_PHASE = "single_phase"
    MULTI_PHASE = "multi_phase"


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


# ---------------------------------------------------------------------------
# Network phase detection
# ---------------------------------------------------------------------------


def _load_connectivity(state_locator: InputLocator, year: int) -> dict[str, Any] | None:
    """Load connectivity.json for a state year's network, or return None if absent."""
    network_name = f"thermal_network_{year}"
    path = state_locator.get_network_connectivity_file(network_name)
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_connections(connectivity: dict[str, Any]) -> dict[str, list[str]]:
    """Extract sorted connected_buildings per network type from a connectivity.json payload.

    Returns e.g. ``{"DH": ["B1001", "B1002"], "DC": ["B1003"]}``
    """
    connections: dict[str, list[str]] = {}
    for network_type, info in connectivity.get("networks", {}).items():
        buildings = sorted(info.get("connected_buildings", []))
        if buildings:
            connections[network_type] = buildings
    return connections


def determine_network_phase_mode(
    main_locator: InputLocator,
    pathway_name: str,
    state_years: list[int],
) -> tuple[NetworkPhaseMode, dict[int, dict[str, list[str]]]]:
    """Compare connectivity.json across all state years to determine the network phase mode.

    Returns a tuple of ``(mode, connections_by_year)`` where *connections_by_year* maps each
    state year that has a connectivity.json to its ``{network_type: [buildings]}`` dict.

    Decision logic:
    - **NONE**: no state year has a connectivity.json  -> no network needed.
    - **SINGLE_PHASE**: every state year that has connectivity shares identical connections
      (same network types, same buildings per type).
    - **MULTI_PHASE**: at least two state years have connectivity that differs (buildings
      added/removed, or network types changed).
    """
    connections_by_year: dict[int, dict[str, list[str]]] = {}

    for year in state_years:
        state_locator = InputLocator(
            main_locator.get_state_in_time_scenario_folder(
                pathway_name=pathway_name, year_of_state=year,
            )
        )
        connectivity = _load_connectivity(state_locator, year)
        if connectivity is not None:
            connections = _extract_connections(connectivity)
            if connections:
                connections_by_year[year] = connections

    if not connections_by_year:
        return NetworkPhaseMode.NONE, connections_by_year

    # Compare all connection dicts — if identical, single-phase; otherwise multi-phase.
    reference = None
    for year, connections in connections_by_year.items():
        if reference is None:
            reference = connections
            continue
        if connections != reference:
            return NetworkPhaseMode.MULTI_PHASE, connections_by_year

    return NetworkPhaseMode.SINGLE_PHASE, connections_by_year


# ---------------------------------------------------------------------------
# Workflow building helpers
# ---------------------------------------------------------------------------


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
    pathway_name: str,
    year: int,
) -> list[dict[str, Any]]:
    """Prepare the pre-network workflow for one state year."""
    main_locator = InputLocator(config.scenario)
    state_locator = InputLocator(
        main_locator.get_state_in_time_scenario_folder(
            pathway_name=pathway_name, year_of_state=year
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
    network_layout_mode: str = "augment",
) -> dict[str, Any]:
    """Build the `network-layout` step for one state year.

    Args:
        network_layout_mode: "augment" for single-phase (additive),
            "filter" for multi-phase (exact match with add/remove).
    """
    network_name = f"thermal_network_{year}"
    parameters: dict[str, Any] = {
        "network-name": network_name,
        "include-services": required_services,
        "overwrite-supply-settings": False,
        "network-layout-mode": network_layout_mode,
        "auto-modify-network": True,
        "existing-network": previous_network_name,
    }

    return {
        "script": "network-layout",
        "parameters": parameters,
    }


def build_thermal_network_step(year: int, required_services: list[str]) -> dict[str, Any]:
    """Build the `thermal-network` step for one state year.

    dh-temperature-mode is not set here — it reads from the user's config
    (exposed in the Simulate Pathway form via thermal-network:dh-temperature-mode).
    """
    network_name = f"thermal_network_{year}"
    return {
        "script": "thermal-network",
        "parameters": {
            "network-name": [network_name],
            "network-type": list(required_services),
        },
    }


# ---------------------------------------------------------------------------
# Post-demand workflow: no network
# ---------------------------------------------------------------------------


def _build_no_network_post_demand(year: int) -> list[dict[str, Any]]:
    """Post-demand workflow when no district thermal services are required."""
    print(
        f"State {year}: No district thermal services required. "
        "Skipping network-layout and thermal-network."
    )
    return [deepcopy(FINAL_ENERGY_STEP), deepcopy(EMISSIONS_STEP)]


# ---------------------------------------------------------------------------
# Post-demand workflow: single-phase network
# ---------------------------------------------------------------------------


def _build_single_phase_post_demand(
    config: Configuration,
    pathway_name: str,
    year: int,
    state_years: list[int],
    required_services: list[str],
) -> list[dict[str, Any]]:
    """Post-demand workflow for single-phase network mode."""
    main_locator = InputLocator(config.scenario)
    state_locator = InputLocator(
        main_locator.get_state_in_time_scenario_folder(
            pathway_name=pathway_name, year_of_state=year
        )
    )

    network_handling.cleanup_current_network_outputs(state_locator, year)
    previous_network_name = network_handling.copy_previous_network_for_state(
        main_locator=main_locator,
        state_locator=state_locator,
        pathway_name=pathway_name,
        year=year,
        state_years=state_years,
    )
    # Always use filter mode: it reshapes the prior layout to match this
    # state's supply (adding buildings that now need service, removing those
    # that don't). When there is no prior network the mode is ignored —
    # `network-layout`'s main() short-circuits to `auto_layout_network`
    # whenever `existing-network` is empty.
    network_name = f"thermal_network_{year}"
    final_energy_step = deepcopy(FINAL_ENERGY_STEP)
    final_energy_step["parameters"]["network-name"] = network_name

    workflow = [
        build_network_layout_step(
            year=year,
            required_services=required_services,
            previous_network_name=previous_network_name,
            network_layout_mode="filter",
        ),
        build_thermal_network_step(year, required_services),
        final_energy_step,
        deepcopy(EMISSIONS_STEP),
    ]

    services_str = ", ".join(required_services)
    print(
        f"State {year}: Adding network-layout and thermal-network steps "
        f"(single-phase, mode=filter) with services: {services_str}"
    )
    return workflow


# ---------------------------------------------------------------------------
# Post-demand workflow: multi-phase network (placeholder)
# ---------------------------------------------------------------------------


def _build_multi_phase_post_demand(
    config: Configuration,
    pathway_name: str,
    year: int,
    state_years: list[int],
    required_services: list[str],
    connections_by_year: dict[int, dict[str, list[str]]],
) -> list[dict[str, Any]]:
    """Post-demand workflow for multi-phase network mode.

    Multi-phase differs from single-phase in network-layout mode:
    - First state (no predecessor with network): fresh layout, no existing-network.
    - Subsequent states: existing-network from previous state, mode=filter
      (adds missing buildings, removes extra ones to match this state's supply.csv).

    thermal-network runs identically to single-phase (one network per state).
    """
    main_locator = InputLocator(config.scenario)
    state_locator = InputLocator(
        main_locator.get_state_in_time_scenario_folder(
            pathway_name=pathway_name, year_of_state=year
        )
    )

    network_handling.cleanup_current_network_outputs(state_locator, year)

    # Determine if there is a previous state with network connectivity
    previous_network_years = sorted(
        (y for y in connections_by_year if y < year), reverse=True
    )

    if previous_network_years:
        # Second+ phase: copy previous network and use filter mode
        previous_network_name = network_handling.copy_previous_network_for_state(
            main_locator=main_locator,
            state_locator=state_locator,
            pathway_name=pathway_name,
            year=year,
            state_years=state_years,
        )
        layout_mode = "filter"
    else:
        # First phase: fresh layout from scratch
        previous_network_name = None
        layout_mode = "augment"

    network_name = f"thermal_network_{year}"
    final_energy_step = deepcopy(FINAL_ENERGY_STEP)
    final_energy_step["parameters"]["network-name"] = network_name

    workflow = [
        build_network_layout_step(
            year=year,
            required_services=required_services,
            previous_network_name=previous_network_name,
            network_layout_mode=layout_mode,
        ),
        build_thermal_network_step(year, required_services),
        final_energy_step,
        deepcopy(EMISSIONS_STEP),
    ]

    services_str = ", ".join(required_services)
    print(
        f"State {year}: Adding network-layout (mode={layout_mode}) and thermal-network steps "
        f"(multi-phase) with services: {services_str}"
    )
    return workflow


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def prepare_post_demand_workflow_for_state(
    config: Configuration,
    pathway_name: str,
    year: int,
    state_years: list[int],
    *,
    phase_mode: NetworkPhaseMode = NetworkPhaseMode.SINGLE_PHASE,
    connections_by_year: dict[int, dict[str, list[str]]] | None = None,
) -> list[dict[str, Any]]:
    """Prepare the post-demand tail for one state year.

    Args:
        phase_mode: Network phasing mode determined by ``determine_network_phase_mode``.
        connections_by_year: Per-year connectivity data (only needed for multi-phase).
    """
    main_locator = InputLocator(config.scenario)
    state_locator = InputLocator(
        main_locator.get_state_in_time_scenario_folder(
            pathway_name=pathway_name, year_of_state=year
        )
    )

    service_eligibility = service_checks.get_state_service_eligibility(state_locator)
    required_services = service_checks.get_required_services(service_eligibility)
    service_checks.report_service_requirements(year, service_eligibility)

    if not required_services:
        return _build_no_network_post_demand(year)

    if phase_mode == NetworkPhaseMode.MULTI_PHASE:
        return _build_multi_phase_post_demand(
            config=config,
            pathway_name=pathway_name,
            year=year,
            state_years=state_years,
            required_services=required_services,
            connections_by_year=connections_by_year or {},
        )

    return _build_single_phase_post_demand(
        config=config,
        pathway_name=pathway_name,
        year=year,
        state_years=state_years,
        required_services=required_services,
    )


def prepare_workflow_for_state(
    config: Configuration,
    pathway_name: str,
    year: int,
    state_years: list[int],
) -> list[dict[str, Any]]:
    """Prepare the full Step 4 workflow for one state year."""
    workflow = prepare_base_workflow_for_state(
        config=config,
        pathway_name=pathway_name,
        year=year,
    )
    workflow.extend(
        prepare_post_demand_workflow_for_state(
            config=config,
            pathway_name=pathway_name,
            year=year,
            state_years=state_years,
        )
    )
    return workflow

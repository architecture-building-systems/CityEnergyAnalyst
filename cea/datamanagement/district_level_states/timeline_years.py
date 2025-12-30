from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import os

import pandas as pd

import geopandas as gpd

from cea.config import Configuration
from cea.inputlocator import InputLocator
from cea.datamanagement.district_level_states.timeline_log import load_log_yaml, save_log_yaml
from cea.datamanagement.district_level_states.timeline_integrity import (
    compute_state_year_missing_modifications,
    merge_modify_recipes,
)
from cea.datamanagement.district_level_states.state_scenario import (
    _apply_state_construction_changes,
    _regenerate_building_properties_from_archetypes,
    create_state_in_time_scenario,
    delete_unexisting_buildings_from_event_scenario,
)


def list_state_years(main_locator: InputLocator) -> list[int]:
    """Return sorted list of state years present under `district_timeline_states/state_YYYY/`."""
    years: list[int] = []
    timeline_folder = main_locator.get_district_timeline_states_folder()
    if not os.path.exists(timeline_folder):
        return years
    for name in os.listdir(timeline_folder):
        if not name.startswith("state_"):
            continue
        try:
            years.append(int(name.replace("state_", "")))
        except ValueError:
            continue
    years.sort()
    return years


def get_building_construction_years(locator: InputLocator) -> dict[str, int]:
    """Return {building_name: construction_year} from `zone.shp`.

    Requires a `year` attribute in the geometry.
    """
    zone = gpd.read_file(locator.get_zone_geometry())
    if "name" not in zone.columns:
        raise ValueError("Zone geometry is missing required 'name' column.")
    if "year" not in zone.columns:
        raise ValueError("Zone geometry is missing required 'year' column.")

    out: dict[str, int] = {}
    for _, row in zone.iterrows():
        name = str(row["name"])
        y = row["year"]
        if y is None:
            continue
        try:
            out[name] = int(y)
        except Exception as e:
            raise ValueError(f"Invalid construction year for building '{name}': {y}") from e
    return out


def get_required_state_years(config: Configuration) -> list[int]:
    """Compute which years should have a `state_{year}` folder.

    Rules:
    - Always include all years present in YAML log.
    - Always include all distinct building construction years from `zone.shp`.

    This ensures operational timelines capture both policy/standard changes and building births.
    """
    main_locator = InputLocator(config.scenario)
    log_data = load_log_yaml(main_locator, allow_missing=True, allow_empty=True)
    years_from_log = set(int(y) for y in log_data.keys())

    years_from_buildings = set(get_building_construction_years(main_locator).values())

    years = sorted(years_from_log | years_from_buildings)
    return years


def ensure_state_years_exist(
    config: Configuration,
    years: Iterable[int],
    *,
    update_yaml: bool = True,
) -> dict[int, dict[str, Any]]:
    """Ensure `state_{year}` folders exist for all requested years.

    - Creates missing `state_{year}` folders by copying inputs.
    - Removes buildings not yet built in that year.
    - Ensures YAML entries exist (empty modifications by default).
    - Optionally logs `building_events.new_buildings` (derived from `zone.shp` construction years).

    Returns the (possibly updated) YAML log data in memory.
    """
    main_locator = InputLocator(config.scenario)
    log_data: dict[int, dict[str, Any]] = load_log_yaml(main_locator, allow_missing=True, allow_empty=True)

    # Use zone geometry construction years as the authoritative source for birth events.
    # This avoids depending on state-folder diffs for the first year (no previous state to compare to).
    construction_years = get_building_construction_years(main_locator)

    existing_years = set(list_state_years(main_locator))
    years_sorted = sorted(set(int(y) for y in years))

    prev_buildings: set[str] | None = None
    for year in years_sorted:
        if year not in existing_years:
            create_state_in_time_scenario(config, year, update_yaml=False)
            if update_yaml:
                log_data.setdefault(year, {"created_at": None, "modifications": {}})

        if update_yaml:
            entry = log_data.get(year, {}) or {}
            # Don't leave created_at empty (e.g., legacy year 2000 entries)
            if entry.get("created_at") in (None, "", "null"):
                entry["created_at"] = str(pd.Timestamp.now())
            entry.setdefault("modifications", {})
            log_data[year] = entry

        state_locator = InputLocator(main_locator.get_state_in_time_scenario_folder(year))
        delete_unexisting_buildings_from_event_scenario(config, year)
        _regenerate_building_properties_from_archetypes(state_locator)

        current_buildings = set(state_locator.get_zone_building_names())
        born = sorted(b for b in current_buildings if construction_years.get(b) == year)
        if prev_buildings is not None:
            demolished = sorted(prev_buildings - current_buildings)
        else:
            demolished = []

        if update_yaml:
            entry = log_data.get(year, {}) or {}
            building_events = entry.get("building_events", {}) or {}
            building_events.setdefault("new_buildings", [])
            # extend (deduplicated)
            existing_born = set(str(x) for x in building_events.get("new_buildings", []) or [])
            for b in born:
                if b not in existing_born:
                    building_events["new_buildings"].append(b)
            building_events.setdefault("demolished_buildings", [])
            existing_demolished = set(str(x) for x in building_events.get("demolished_buildings", []) or [])
            for b in demolished:
                if b not in existing_demolished:
                    building_events["demolished_buildings"].append(b)
            entry["building_events"] = building_events
            log_data[year] = entry

        prev_buildings = current_buildings

    if update_yaml:
        save_log_yaml(main_locator, log_data)

    return log_data


def reconcile_states_to_cumulative_modifications(
    config: Configuration,
    years: Iterable[int],
    *,
    log_data: dict[int, dict[str, Any]] | None = None,
) -> None:
    """Apply cumulative YAML modifications so each `state_{year}` reflects full history up to that year.

    This is the non-interactive equivalent of the "reconcile future years" logic.
    It uses `compute_state_year_missing_modifications` to detect drift and then applies only missing fields.

    NOTE: This does *not* change the YAML (it only mutates the state scenario databases).
    """
    main_locator = InputLocator(config.scenario)
    if log_data is None:
        log_data = load_log_yaml(main_locator, allow_missing=True, allow_empty=True)

    cumulative: dict[str, dict[str, dict[str, Any]]] = {}
    years_sorted = sorted(set(int(y) for y in years))

    for year in years_sorted:
        year_entry = log_data.get(year, {}) or {}
        delta = (year_entry.get("modifications", {}) or {})
        cumulative = merge_modify_recipes(cumulative, delta)

        missing_recipe, errors = compute_state_year_missing_modifications(config, year, cumulative)
        if errors:
            formatted = "\n".join(f"- {e}" for e in errors)
            raise ValueError(f"Errors while reconciling state_{year}:\n" + formatted)

        if missing_recipe:
            modified = _apply_state_construction_changes(
                config,
                year,
                missing_recipe,
                trigger_year=None,
            )
            if modified:
                state_locator = InputLocator(main_locator.get_state_in_time_scenario_folder(year))
                _regenerate_building_properties_from_archetypes(state_locator)

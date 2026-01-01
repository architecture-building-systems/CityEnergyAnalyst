from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import os

import geopandas as gpd

from cea.config import Configuration
from cea.inputlocator import InputLocator
from cea.datamanagement.district_level_states.timeline_log import load_log_yaml
from cea.datamanagement.district_level_states.timeline_integrity import (
    compute_state_year_missing_modifications,
    merge_modify_recipes,
)
from cea.datamanagement.district_level_states.state_scenario import (
    _apply_state_construction_changes,
    _regenerate_building_properties_from_archetypes,
    DistrictEventTimeline,
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
    timeline = DistrictEventTimeline(config)
    return timeline.required_state_years()


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
    timeline = DistrictEventTimeline(config)
    return timeline.ensure_state_years_exist(
        [int(y) for y in years],
        update_yaml=update_yaml,
        regenerate_building_properties=True,
        update_building_events=True,
    )


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

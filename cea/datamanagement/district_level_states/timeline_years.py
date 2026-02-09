from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import os

import geopandas as gpd

from cea.config import Configuration
from cea.inputlocator import InputLocator
from cea.datamanagement.district_level_states.state_scenario import DistrictEventTimeline


def list_state_years(main_locator: InputLocator, timeline_name: str) -> list[int]:
    """Return sorted list of state years present under `district_timeline_states/state_YYYY/`."""
    years: list[int] = []
    timeline_folder = main_locator.get_district_timeline_folder(timeline_name)
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


def get_required_state_years(config: Configuration, timeline_name: str) -> list[int]:
    """Compute which years should have a `state_{year}` folder.

    Rules:
    - Always include all years present in YAML log.
    - Always include all distinct building construction years from `zone.shp`.

    This ensures operational timelines capture both policy/standard changes and building births.
    """
    timeline = DistrictEventTimeline(config, timeline_name=timeline_name)
    return timeline.required_state_years()


def ensure_state_years_exist(
    config: Configuration,
    timeline_name: str,
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
    timeline = DistrictEventTimeline(config, timeline_name=timeline_name)
    return timeline.ensure_state_years_exist(
        [int(y) for y in years],
        update_yaml=update_yaml,
        update_building_events=True,
    )

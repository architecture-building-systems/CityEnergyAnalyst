import os
from typing import Any

import pandas as pd
import yaml

from cea.config import Configuration
from cea.inputlocator import InputLocator


def load_log_yaml(
    locator: InputLocator,
    *,
    allow_missing: bool = False,
    allow_empty: bool = False,
) -> dict[int, dict[str, Any]]:
    yml_path = locator.get_district_timeline_log_file()
    if not os.path.exists(yml_path):
        if allow_missing:
            return {}
        raise FileNotFoundError(
            f"District timeline log file '{yml_path}' does not exist."
        )
    with open(yml_path, "r") as f:
        raw_data: Any = yaml.safe_load(f) or {}
    if not raw_data:
        if allow_empty:
            return {}
        raise ValueError(f"District timeline log file '{yml_path}' is empty.")
    if not isinstance(raw_data, dict):
        raise ValueError(
            f"District timeline log file '{yml_path}' must contain a YAML mapping at the top level."
        )

    normalised: dict[int, dict[str, Any]] = {}
    for raw_year, entry in raw_data.items():
        if isinstance(raw_year, int):
            year = raw_year
        elif isinstance(raw_year, str):
            try:
                year = int(raw_year)
            except ValueError as e:
                raise ValueError(
                    f"District timeline log file '{yml_path}' contains a non-integer year key: {raw_year}"
                ) from e
        else:
            raise ValueError(
                f"District timeline log file '{yml_path}' contains an invalid year key type: {type(raw_year)}"
            )

        if entry is None:
            normalised[year] = {}
        elif isinstance(entry, dict):
            normalised[year] = entry
        else:
            raise ValueError(
                f"District timeline log file '{yml_path}' entry for year {year} must be a mapping."
            )

    return normalised


def save_log_yaml(locator: InputLocator, log_data: dict[int, dict[str, Any]]) -> None:
    yml_path = locator.get_district_timeline_log_file()
    os.makedirs(os.path.dirname(yml_path), exist_ok=True)
    with open(yml_path, "w") as f:
        yaml.dump(log_data, f)


def add_year_in_yaml(config: Configuration, year_of_state: int) -> None:
    """Add a new year entry in the district timeline log yaml file if it does not exist."""
    locator = InputLocator(config.scenario)
    log_data = load_log_yaml(locator, allow_missing=True, allow_empty=True)
    if year_of_state not in log_data:
        log_data[year_of_state] = {
            "created_at": str(pd.Timestamp.now()),
            "modifications": {},
        }
        save_log_yaml(locator, log_data)


def del_year_in_yaml(config: Configuration, year_of_state: int) -> None:
    """Delete a year entry in the district timeline log yaml file."""
    locator = InputLocator(config.scenario)
    log_data = load_log_yaml(locator, allow_missing=True, allow_empty=True)
    if not log_data:
        return
    if year_of_state in log_data:
        del log_data[year_of_state]
        save_log_yaml(locator, log_data)

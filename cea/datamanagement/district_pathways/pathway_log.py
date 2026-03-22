import os
from typing import Any

import pandas as pd
import yaml

from cea.config import Configuration
from cea.inputlocator import InputLocator


class _NoAliasSafeDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:  # noqa: ANN401
        return True


def load_pathway_log_yaml(
    locator: InputLocator,
    *,
    pathway_name: str,
    allow_missing: bool = False,
    allow_empty: bool = False,
) -> dict[int, dict[str, Any]]:
    yml_path = locator.get_district_pathway_log_file(pathway_name)
    if not os.path.exists(yml_path):
        if allow_missing:
            return {}
        raise FileNotFoundError(
            f"District pathway log file '{yml_path}' does not exist."
        )
    with open(yml_path, "r") as f:
        raw_data: Any = yaml.safe_load(f) or {}
    if not raw_data:
        if allow_empty:
            return {}
        raise ValueError(f"District pathway log file '{yml_path}' is empty.")
    if not isinstance(raw_data, dict):
        raise ValueError(
            f"District pathway log file '{yml_path}' must contain a YAML mapping at the top level."
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
                    f"District pathway log file '{yml_path}' contains a non-integer year key: {raw_year}"
                ) from e
        else:
            raise ValueError(
                f"District pathway log file '{yml_path}' contains an invalid year key type: {type(raw_year)}"
            )

        if entry is None:
            normalised[year] = {}
        elif isinstance(entry, dict):
            normalised[year] = entry
        else:
            raise ValueError(
                f"District pathway log file '{yml_path}' entry for year {year} must be a mapping."
            )

    return normalised


def save_pathway_log_yaml(
    main_locator: InputLocator,
    log_data: dict[int, dict[str, Any]],
    *,
    pathway_name: str,
) -> None:
    yml_path = main_locator.get_district_pathway_log_file(pathway_name)
    os.makedirs(os.path.dirname(yml_path), exist_ok=True)
    ordered_log_data: dict[int, dict[str, Any]] = {
        year: log_data[year] for year in sorted(log_data)
    }
    with open(yml_path, "w") as f:
        yaml.dump(
            ordered_log_data,
            f,
            Dumper=_NoAliasSafeDumper,
            sort_keys=False,
            default_flow_style=False,
        )


def add_year_in_pathway_yaml(
    config: Configuration,
    year_of_state: int,
    *,
    pathway_name: str,
) -> None:
    """Add a new year entry in the district pathway log YAML file if it does not exist."""
    locator = InputLocator(config.scenario)
    log_data = load_pathway_log_yaml(
        locator,
        allow_missing=True,
        allow_empty=True,
        pathway_name=pathway_name,
    )
    if year_of_state not in log_data:
        log_data[year_of_state] = {
            "created_at": str(pd.Timestamp.now()),
            "modifications": {},
        }
        save_pathway_log_yaml(locator, log_data, pathway_name=pathway_name)

def del_year_in_pathway_yaml(
    config: Configuration,
    year_of_state: int,
    *,
    pathway_name: str,
) -> None:
    """Delete a year entry in the district pathway log YAML file."""
    locator = InputLocator(config.scenario)
    log_data = load_pathway_log_yaml(
        locator,
        allow_missing=True,
        allow_empty=True,
        pathway_name=pathway_name,
    )
    if not log_data:
        return
    if year_of_state in log_data:
        del log_data[year_of_state]
        save_pathway_log_yaml(locator, log_data, pathway_name=pathway_name)

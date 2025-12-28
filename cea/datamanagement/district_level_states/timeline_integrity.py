import os
from copy import deepcopy
from typing import Any

import pandas as pd

from cea.config import Configuration
from cea.inputlocator import InputLocator
from cea.datamanagement.district_level_states.timeline_log import load_log_yaml


ModifyRecipe = dict[str, dict[str, dict[str, Any]]]


def check_district_timeline_log_yaml_integrity(main_config: Configuration) -> dict[int, dict[str, Any]]:
    """Check that the district timeline log is consistent with existing state-in-time scenarios.

    NOTE: `main_config` must point to the *main* scenario (the one containing the district timeline folder).
    Do not pass a state scenario config here.

    Modes:
    - basic: only checks that years in `state_{year}` folders match years in the YAML log
    - comprehensive: also checks that every logged modification is reflected in the state scenario databases

    The check mode is controlled via `district-events:timeline-integrity-check`.
    """
    main_locator = InputLocator(main_config.scenario)
    dict_from_yaml = load_log_yaml(main_locator)
    existing_years_in_yml = set(dict_from_yaml.keys())

    existing_years_in_folders = set()
    district_timeline_folder = main_locator.get_district_timeline_states_folder()
    if os.path.exists(district_timeline_folder):
        for folder_name in os.listdir(district_timeline_folder):
            if folder_name.startswith("state_"):
                year_str = folder_name.replace("state_", "")
                try:
                    year = int(year_str)
                    existing_years_in_folders.add(year)
                except ValueError:
                    print(
                        f"Warning: Invalid state-in-time folder name '{folder_name}' in district timeline folder."
                    )

    years_only_in_folders = existing_years_in_folders - existing_years_in_yml
    years_only_in_yml = existing_years_in_yml - existing_years_in_folders
    if years_only_in_folders:
        raise ValueError(
            "The following state-in-time years exist in folders but not in the district timeline log file: "
            f"{sorted(years_only_in_folders)}"
        )

    if years_only_in_yml:
        raise ValueError(
            "The following state-in-time years exist in the district timeline log file but not in folders: "
            f"{sorted(years_only_in_yml)}"
        )

    try:
        check_mode = main_config.district_events.timeline_integrity_check
    except AttributeError:
        check_mode = "basic"

    if check_mode == "basic":
        return dict_from_yaml
    if check_mode != "comprehensive":
        raise ValueError(
            f"Invalid district timeline integrity check mode: {check_mode}. "
            "Expected one of: basic, comprehensive"
        )

    cumulative_modifications: ModifyRecipe = {}
    errors: list[str] = []
    for year_of_state in sorted(existing_years_in_yml):
        year_entry = dict_from_yaml.get(year_of_state, {}) or {}
        year_modifications = (year_entry.get("modifications", {}) or {})
        cumulative_modifications = merge_modify_recipes(cumulative_modifications, year_modifications)

        errors.extend(
            check_state_year_comprehensive_integrity(
            main_config,
            year_of_state,
            cumulative_modifications,
            )
        )

    if errors:
        formatted = "\n".join(f"- {msg}" for msg in errors)
        raise ValueError(
            "District timeline integrity check failed (comprehensive mode).\n" + formatted
        )

    return dict_from_yaml


def merge_modify_recipes(base: ModifyRecipe, delta: ModifyRecipe) -> ModifyRecipe:
    """Deep-merge two modify recipes.

    - `delta` values overwrite `base` values at the leaf level.
    - Missing keys are preserved.
    - The result is a new dict (does not mutate inputs).
    """
    merged: ModifyRecipe = deepcopy(base)
    for archetype, components in (delta or {}).items():
        if archetype not in merged:
            merged[archetype] = {}
        for component, fields in (components or {}).items():
            if component not in merged[archetype]:
                merged[archetype][component] = {}
            merged[archetype][component].update(fields or {})
    return merged


def compute_state_year_missing_modifications(
    main_config: Configuration,
    year_of_state: int,
    expected_modifications: ModifyRecipe,
) -> tuple[ModifyRecipe, list[str]]:
    """Compute which modifications are still missing in a given `state_{year}` scenario.

    Returns:
    - missing_recipe: a modify-recipe dict containing only fields that do not match the expected values
    - errors: list of human-readable problems (missing files / columns / codes, etc)

    NOTE: `main_config` must point to the *main* scenario (not a `state_{year}` scenario).
    """
    errors: list[str] = []
    missing_recipe: ModifyRecipe = {}

    try:
        state_locator = InputLocator(
            InputLocator(main_config.scenario).get_state_in_time_scenario_folder(year_of_state)
        )
    except Exception as e:
        return {}, [
            f"year {year_of_state}: failed to create state locator from main scenario '{main_config.scenario}': {e}"
        ]

    archetype_path = state_locator.get_database_archetypes_construction_type()
    if not os.path.exists(archetype_path):
        return {}, [
            f"year {year_of_state}: missing construction type database: {archetype_path}"
        ]

    try:
        archetype_df = pd.read_csv(archetype_path, index_col="const_type")
    except Exception as e:
        return {}, [
            f"year {year_of_state}: failed to read construction type database '{archetype_path}': {e}"
        ]

    modifications = expected_modifications or {}
    for archetype, components in modifications.items():
        if archetype not in archetype_df.index:
            errors.append(
                f"year {year_of_state}: archetype '{archetype}' not present in construction types database"
            )
            continue

        for component, fields in (components or {}).items():
            envelope_component = _resolve_envelope_component(component)

            try:
                type_column = _resolve_archetype_type_column(archetype_df, component)
            except Exception as e:
                errors.append(
                    f"year {year_of_state}, archetype '{archetype}', component '{component}': {e}"
                )
                continue

            code_current = archetype_df.at[archetype, type_column]

            try:
                envelope_db_path = _get_envelope_db_path(state_locator, envelope_component)
            except Exception as e:
                errors.append(
                    f"year {year_of_state}, archetype '{archetype}', component '{component}': {e}"
                )
                continue

            if not os.path.exists(envelope_db_path):
                errors.append(
                    f"year {year_of_state}, archetype '{archetype}', component '{component}': missing envelope database: {envelope_db_path}"
                )
                continue

            try:
                envelope_df = pd.read_csv(envelope_db_path, index_col="code")
            except Exception as e:
                errors.append(
                    f"year {year_of_state}, archetype '{archetype}', component '{component}': failed to read envelope database '{envelope_db_path}': {e}"
                )
                continue

            if code_current not in envelope_df.index:
                errors.append(
                    f"year {year_of_state}, archetype '{archetype}', component '{component}': expected {type_column}={code_current}, but code is missing from {envelope_db_path}"
                )
                continue

            row = envelope_df.loc[code_current]
            for field, expected_value in (fields or {}).items():
                if expected_value is None:
                    continue

                col = _resolve_envelope_column_name(
                    envelope_component, field, envelope_df.columns
                )
                if col not in envelope_df.columns:
                    errors.append(
                        f"year {year_of_state}, archetype '{archetype}', component '{component}', field '{field}': resolved column '{col}' missing from {envelope_db_path}"
                    )
                    continue

                actual_value = row[col]
                if not _values_match(actual_value, expected_value):
                    missing_recipe.setdefault(archetype, {}).setdefault(component, {})[
                        field
                    ] = expected_value

    return missing_recipe, errors


def check_state_year_comprehensive_integrity(
    main_config: Configuration,
    year_of_state: int,
    expected_modifications: ModifyRecipe,
) -> list[str]:
    """Comprehensive integrity check for one state year.

    Validates that all modifications *up to and including* `year_of_state` are reflected in that
    `state_{year}` scenario.

    NOTE: `main_config` must point to the *main* scenario (the one containing the district timeline folder).
    Do not pass a state scenario config here.
    """
    errors: list[str] = []
    try:
        state_locator = InputLocator(
            InputLocator(main_config.scenario).get_state_in_time_scenario_folder(year_of_state)
        )
    except Exception as e:
        return [
            f"year {year_of_state}: failed to create state locator from main scenario '{main_config.scenario}': {e}"
        ]

    archetype_path = state_locator.get_database_archetypes_construction_type()
    if not os.path.exists(archetype_path):
        return [
            f"year {year_of_state}: missing construction type database: {archetype_path}"
        ]

    try:
        archetype_df = pd.read_csv(archetype_path, index_col="const_type")
    except Exception as e:
        return [
            f"year {year_of_state}: failed to read construction type database '{archetype_path}': {e}"
        ]
    modifications = expected_modifications or {}

    for archetype, components in modifications.items():
        if archetype not in archetype_df.index:
            errors.append(
                f"year {year_of_state}: archetype '{archetype}' not present in construction types database"
            )
            continue

        for component, fields in (components or {}).items():
            envelope_component = _resolve_envelope_component(component)

            try:
                type_column = _resolve_archetype_type_column(archetype_df, component)
            except Exception as e:
                errors.append(
                    f"year {year_of_state}, archetype '{archetype}', component '{component}': {e}"
                )
                continue

            code_current = archetype_df.at[archetype, type_column]

            try:
                envelope_db_path = _get_envelope_db_path(state_locator, envelope_component)
            except Exception as e:
                errors.append(
                    f"year {year_of_state}, archetype '{archetype}', component '{component}': {e}"
                )
                continue

            if not os.path.exists(envelope_db_path):
                errors.append(
                    f"year {year_of_state}, archetype '{archetype}', component '{component}': missing envelope database: {envelope_db_path}"
                )
                continue

            try:
                envelope_df = pd.read_csv(envelope_db_path, index_col="code")
            except Exception as e:
                errors.append(
                    f"year {year_of_state}, archetype '{archetype}', component '{component}': failed to read envelope database '{envelope_db_path}': {e}"
                )
                continue

            if code_current not in envelope_df.index:
                errors.append(
                    f"year {year_of_state}, archetype '{archetype}', component '{component}': expected {type_column}={code_current}, but code is missing from {envelope_db_path}"
                )
                continue

            row = envelope_df.loc[code_current]
            for field, expected_value in (fields or {}).items():
                if expected_value is None:
                    continue

                col = _resolve_envelope_column_name(
                    envelope_component, field, envelope_df.columns
                )
                if col not in envelope_df.columns:
                    errors.append(
                        f"year {year_of_state}, archetype '{archetype}', component '{component}', field '{field}': resolved column '{col}' missing from {envelope_db_path}"
                    )
                    continue

                actual_value = row[col]
                if not _values_match(actual_value, expected_value):
                    errors.append(
                        f"year {year_of_state}, archetype '{archetype}', component '{component}', field '{field}': expected {expected_value}, got {actual_value}"
                    )

    return errors


def _values_match(actual_value: Any, expected_value: Any) -> bool:
    if expected_value is None:
        return True

    if pd.isna(actual_value):
        return False

    if isinstance(expected_value, (int, float)):
        try:
            return abs(float(actual_value) - float(expected_value)) <= 1e-9
        except (TypeError, ValueError):
            return False

    return str(actual_value) == str(expected_value)


def _resolve_envelope_component(component: str) -> str:
    # Envelope DB uses "floor" while archetypes / logs may use "base".
    if component in {"base", "floor"}:
        return "floor"
    return component


def _resolve_archetype_type_column(archetype_df: pd.DataFrame, component: str) -> str:
    candidates = [f"type_{component}"]
    if component in {"base", "floor"}:
        candidates.extend(["type_base", "type_floor"])

    for candidate in candidates:
        if candidate in archetype_df.columns:
            return candidate

    raise ValueError(
        f"Could not find construction type column for component '{component}'. "
        f"Tried: {candidates}"
    )


def _resolve_envelope_column_name(envelope_component: str, field: str, columns: pd.Index) -> str:
    if field.startswith("material_name_") or field.startswith("thickness_"):
        return field

    if field == "Service_Life":
        return f"Service_Life_{envelope_component}"

    if field in columns:
        return field

    suffixed = f"{field}_{envelope_component}"
    if suffixed in columns:
        return suffixed

    return field


def _get_envelope_db_path(locator: InputLocator, envelope_component: str) -> str:
    if envelope_component == "wall":
        return locator.get_database_assemblies_envelope_wall()
    if envelope_component == "roof":
        return locator.get_database_assemblies_envelope_roof()
    if envelope_component == "floor":
        return locator.get_database_assemblies_envelope_floor()
    raise ValueError(
        f"Unsupported envelope component '{envelope_component}' for comprehensive timeline integrity check."
    )

import os
from copy import deepcopy
from typing import Any, cast

import pandas as pd

from cea.config import Configuration
from cea.inputlocator import InputLocator
from cea.datamanagement.district_pathways.envelope_topology import (
    validate_three_layer_topology,
)
from cea.datamanagement.district_pathways.pathway_log import (
    load_pathway_log_yaml,
)


ModifyRecipe = dict[str, dict[str, dict[str, Any]]]


def check_district_pathway_log_yaml_integrity(
    main_config: Configuration,
    pathway_name: str,
) -> dict[int, dict[str, Any]]:
    """Check that the district pathway log is consistent with existing pathway states.

    NOTE: `main_config` must point to the *main* scenario (the one containing the district pathway folder).
    Do not pass a state scenario config here.
    Checks that every logged modification is reflected in the state scenario databases
    """
    main_locator = InputLocator(main_config.scenario)
    dict_from_yaml = load_pathway_log_yaml(main_locator, pathway_name=pathway_name)
    from cea.datamanagement.district_pathways.pathway_state import (
        DistrictEvolutionPathway,
    )

    pathway = DistrictEvolutionPathway(main_config, pathway_name=pathway_name)
    expected_state_years = set(pathway.required_state_years())

    existing_years_in_folders = set()
    district_pathway_folder = main_locator.get_district_pathway_folder(pathway_name)
    if os.path.exists(district_pathway_folder):
        for folder_name in os.listdir(district_pathway_folder):
            if folder_name.startswith("state_"):
                year_str = folder_name.replace("state_", "")
                try:
                    year = int(year_str)
                    existing_years_in_folders.add(year)
                except ValueError:
                    print(
                        f"Warning: Invalid pathway-state folder name '{folder_name}' in district pathway folder."
                    )

    unexpected_folders = existing_years_in_folders - expected_state_years
    missing_folders = expected_state_years - existing_years_in_folders
    if unexpected_folders:
        raise ValueError(
            "The following pathway-state years exist in folders but are not required by the pathway definition: "
            f"{sorted(unexpected_folders)}"
        )

    if missing_folders:
        raise ValueError(
            "The following required pathway-state years do not exist in folders: "
            f"{sorted(missing_folders)}"
        )

    expected_active_buildings = pathway.get_active_buildings_by_year()

    cumulative_modifications: ModifyRecipe = {}
    errors: list[str] = []
    for year_of_state in sorted(expected_state_years):
        year_entry = dict_from_yaml.get(year_of_state, {}) or {}
        year_modifications = (year_entry.get("modifications", {}) or {})
        cumulative_modifications = merge_modify_recipes(cumulative_modifications, year_modifications)

        errors.extend(
            check_state_year_comprehensive_integrity(
            main_config,
            pathway_name,
            year_of_state,
            cumulative_modifications,
            )
        )
        try:
            state_locator = InputLocator(
                InputLocator(main_config.scenario).get_state_in_time_scenario_folder(
                    pathway_name, year_of_state
                )
            )
            actual_buildings = set(state_locator.get_zone_building_names())
            expected_buildings = set(expected_active_buildings.get(year_of_state, []))
            missing = sorted(expected_buildings - actual_buildings)
            extra = sorted(actual_buildings - expected_buildings)
            if missing:
                errors.append(
                    f"year {year_of_state}: missing buildings in baked state: {', '.join(missing)}"
                )
            if extra:
                errors.append(
                    f"year {year_of_state}: unexpected buildings in baked state: {', '.join(extra)}"
                )
        except Exception as exc:
            errors.append(
                f"year {year_of_state}: failed to inspect baked buildings: {exc}"
            )

    if errors:
        formatted = "\n".join(f"- {msg}" for msg in errors)
        raise ValueError(
            "District pathway integrity check failed (comprehensive mode).\n" + formatted
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


def check_state_year_comprehensive_integrity(
    main_config: Configuration,
    pathway_name: str,
    year_of_state: int,
    expected_modifications: ModifyRecipe,
) -> list[str]:
    """Comprehensive integrity check for one state year.

    Validates that all modifications *up to and including* `year_of_state` are reflected in that
    `state_{year}` scenario.

    NOTE: `main_config` must point to the *main* scenario (the one containing the district pathway folder).
    Do not pass a state scenario config here.
    """
    errors: list[str] = []
    try:
        state_locator = InputLocator(
            InputLocator(main_config.scenario).get_state_in_time_scenario_folder(pathway_name, year_of_state)
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
            if component == "construction_type":
                for field, expected_value in (fields or {}).items():
                    if expected_value is None:
                        continue
                    if field not in archetype_df.columns:
                        errors.append(
                            f"year {year_of_state}, archetype '{archetype}', component '{component}', field '{field}': column missing from construction types database"
                        )
                        continue
                    actual_value = archetype_df.at[archetype, field]
                    if not _values_match(actual_value, expected_value):
                        errors.append(
                            f"year {year_of_state}, archetype '{archetype}', component '{component}', field '{field}': expected {expected_value}, got {actual_value}"
                        )
                continue

            envelope_component = resolve_envelope_component(component)

            try:
                type_column = resolve_archetype_type_column(archetype_df, component)
            except Exception as e:
                errors.append(
                    f"year {year_of_state}, archetype '{archetype}', component '{component}': {e}"
                )
                continue

            code_current = archetype_df.at[archetype, type_column]

            try:
                envelope_db_path = get_envelope_db_path(state_locator, envelope_component)
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

            row = cast(pd.Series, envelope_df.loc[code_current])
            errors.extend(
                validate_three_layer_topology(
                    row,
                    year_of_state=year_of_state,
                    archetype=archetype,
                    component=component,
                    envelope_ref=envelope_db_path,
                )
            )
            for field, expected_value in (fields or {}).items():
                if expected_value is None:
                    continue

                col = resolve_envelope_column_name(
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


def resolve_envelope_component(component: str) -> str:
    # Envelope DB uses "floor" while archetypes / logs may use "base".
    if component in {"base", "floor"}:
        return "floor"
    # Partitions share the wall envelope database.
    if component == "part":
        return "wall"
    return component


def resolve_archetype_type_column(archetype_df: pd.DataFrame, component: str) -> str:
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


def resolve_envelope_column_name(envelope_component: str, field: str, columns: pd.Index) -> str:
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


def get_envelope_db_path(locator: InputLocator, envelope_component: str) -> str:
    if envelope_component in {"wall", "part"}:
        return locator.get_database_assemblies_envelope_wall()
    if envelope_component == "roof":
        return locator.get_database_assemblies_envelope_roof()
    if envelope_component == "floor":
        return locator.get_database_assemblies_envelope_floor()
    raise ValueError(
        f"Unsupported envelope component '{envelope_component}' for comprehensive pathway integrity check."
    )

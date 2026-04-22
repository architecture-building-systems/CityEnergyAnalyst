from __future__ import annotations

import os
from typing import Any, cast

import pandas as pd

from cea.config import Configuration
from cea.datamanagement.district_pathways.envelope_topology import (
    validate_three_layer_topology,
)
from cea.datamanagement.district_pathways.pathway_integrity import (
    check_state_year_comprehensive_integrity,
    get_envelope_db_path,
    resolve_archetype_type_column,
    resolve_envelope_column_name,
    resolve_envelope_component,
)
from cea.datamanagement.district_pathways.pathway_state import DistrictEvolutionPathway
from cea.inputlocator import InputLocator


def validate_pathway_log_data(
    *,
    config: Configuration,
    pathway_name: str,
    log_data: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    locator = InputLocator(config.scenario)
    issues_by_year: dict[int, list[str]] = {}
    global_issues: list[str] = []

    archetype_path = locator.get_database_archetypes_construction_type()
    if not os.path.exists(archetype_path):
        global_issues.append(
            f"Missing construction type database: {archetype_path}"
        )
        return _validation_payload(pathway_name, global_issues, issues_by_year)

    try:
        archetype_df = pd.read_csv(archetype_path, index_col="const_type")
    except Exception as exc:  # pragma: no cover - defensive I/O reporting
        global_issues.append(
            f"Failed to read construction type database '{archetype_path}': {exc}"
        )
        return _validation_payload(pathway_name, global_issues, issues_by_year)

    valid_buildings = set(
        DistrictEvolutionPathway(
            config,
            pathway_name=pathway_name,
        ).get_building_construction_years().keys()
    )

    for year in sorted(int(y) for y in log_data.keys()):
        entry = log_data.get(year, {}) or {}
        year_issues: list[str] = []

        modifications = entry.get("modifications", {}) or {}
        if not isinstance(modifications, dict):
            year_issues.append("Field 'modifications' must be a mapping.")
            modifications = {}

        building_events = entry.get("building_events", {}) or {}
        if not isinstance(building_events, dict):
            year_issues.append("Field 'building_events' must be a mapping.")
            building_events = {}

        cleaned_events = {
            "new_buildings": building_events.get("new_buildings", []) or [],
            "demolished_buildings": building_events.get("demolished_buildings", []) or [],
        }
        for field_name, values in cleaned_events.items():
            if not isinstance(values, list):
                year_issues.append(
                    f"Field 'building_events.{field_name}' must be a list."
                )
                continue
            unknown = sorted({str(value) for value in values} - valid_buildings)
            if unknown:
                year_issues.append(
                    f"Field 'building_events.{field_name}' contains unknown buildings: {', '.join(unknown)}"
                )

        # A building can appear in both new_buildings and demolished_buildings
        # for the same year — this represents a same-year demolish+rebuild.

        year_issues.extend(
            _validate_modification_recipe(
                locator=locator,
                archetype_df=archetype_df,
                year=int(year),
                modify_recipe=cast(dict[str, dict[str, dict[str, Any]]], modifications),
            )
        )

        if year_issues:
            issues_by_year[int(year)] = year_issues

    return _validation_payload(pathway_name, global_issues, issues_by_year)


def raise_if_invalid_pathway_log(
    *,
    config: Configuration,
    pathway_name: str,
    log_data: dict[int, dict[str, Any]],
) -> None:
    payload = validate_pathway_log_data(
        config=config,
        pathway_name=pathway_name,
        log_data=log_data,
    )
    if payload["is_valid"]:
        return

    parts = list(payload["issues"])
    for year, issues in payload["issues_by_year"].items():
        parts.extend(f"Year {year}: {issue}" for issue in issues)
    raise ValueError("\n".join(parts))


def validate_baked_state_issues(
    pathway: DistrictEvolutionPathway,
    year: int,
) -> list[str]:
    state_locator = InputLocator(
        pathway.main_locator.get_state_in_time_scenario_folder(pathway.pathway_name, int(year))
    )
    if not os.path.exists(state_locator.get_zone_geometry()):
        return [f"Missing baked state folder for year {int(year)}."]

    cumulative_modifications = pathway.cumulative_by_year().get(int(year), {})
    issues = check_state_year_comprehensive_integrity(
        pathway.config,
        pathway.pathway_name,
        int(year),
        cumulative_modifications,
    )

    expected_buildings = set(pathway.get_active_buildings_by_year().get(int(year), []))
    actual_buildings = set(state_locator.get_zone_building_names())
    if expected_buildings != actual_buildings:
        missing = sorted(expected_buildings - actual_buildings)
        extra = sorted(actual_buildings - expected_buildings)
        if missing:
            issues.append(
                f"Missing buildings in baked state: {', '.join(missing)}"
            )
        if extra:
            issues.append(
                f"Unexpected buildings in baked state: {', '.join(extra)}"
            )

    return issues


def _validation_payload(
    pathway_name: str,
    issues: list[str],
    issues_by_year: dict[int, list[str]],
) -> dict[str, Any]:
    return {
        "pathway_name": pathway_name,
        "is_valid": not issues and not issues_by_year,
        "issues": issues,
        "issues_by_year": {
            str(int(year)): messages for year, messages in sorted(issues_by_year.items())
        },
    }


def _validate_modification_recipe(
    *,
    locator: InputLocator,
    archetype_df: pd.DataFrame,
    year: int,
    modify_recipe: dict[str, dict[str, dict[str, Any]]],
) -> list[str]:
    issues: list[str] = []

    for archetype, components in (modify_recipe or {}).items():
        if not isinstance(components, dict):
            issues.append(
                f"Archetype '{archetype}' must map to a component mapping."
            )
            continue

        if archetype not in archetype_df.index:
            issues.append(
                f"Archetype '{archetype}' is not present in the construction type database."
            )
            continue

        for component, fields in components.items():
            if not isinstance(fields, dict):
                issues.append(
                    f"Year {year}, archetype '{archetype}', component '{component}': fields must be a mapping."
                )
                continue

            if component == "construction_type":
                for field_name, value in fields.items():
                    if field_name not in archetype_df.columns:
                        issues.append(
                            f"Year {year}, archetype '{archetype}': construction type field '{field_name}' does not exist."
                        )
                    if value is not None and str(value).strip() == "":
                        issues.append(
                            f"Year {year}, archetype '{archetype}': construction type field '{field_name}' cannot be an empty string."
                        )
                continue

            try:
                type_column = resolve_archetype_type_column(archetype_df, component)
            except ValueError as exc:
                issues.append(
                    f"Year {year}, archetype '{archetype}', component '{component}': {exc}"
                )
                continue

            code_current = archetype_df.at[archetype, type_column]
            envelope_component = resolve_envelope_component(component)

            try:
                envelope_db_path = get_envelope_db_path(locator, envelope_component)
            except ValueError as exc:
                issues.append(
                    f"Year {year}, archetype '{archetype}', component '{component}': {exc}"
                )
                continue

            if not os.path.exists(envelope_db_path):
                issues.append(
                    f"Year {year}, archetype '{archetype}', component '{component}': missing envelope database '{envelope_db_path}'."
                )
                continue

            try:
                envelope_df = pd.read_csv(envelope_db_path, index_col="code")
            except Exception as exc:  # pragma: no cover - defensive I/O reporting
                issues.append(
                    f"Year {year}, archetype '{archetype}', component '{component}': failed to read '{envelope_db_path}': {exc}"
                )
                continue

            if code_current not in envelope_df.index:
                issues.append(
                    f"Year {year}, archetype '{archetype}', component '{component}': code '{code_current}' is missing from '{envelope_db_path}'."
                )
                continue

            row = cast(pd.Series, envelope_df.loc[code_current].copy())

            for field_name, value in fields.items():
                if value is None:
                    continue
                column_name = resolve_envelope_column_name(
                    envelope_component,
                    field_name,
                    envelope_df.columns,
                )
                if column_name not in envelope_df.columns:
                    issues.append(
                        f"Year {year}, archetype '{archetype}', component '{component}': field '{field_name}' is not available in '{envelope_db_path}'."
                    )
                    continue
                row[column_name] = value

            issues.extend(
                validate_three_layer_topology(
                    row,
                    year_of_state=year,
                    archetype=archetype,
                    component=component,
                    envelope_ref=envelope_db_path,
                )
            )

    return issues

from __future__ import annotations

import os
import shutil
from copy import deepcopy
from typing import Any, cast

import pandas as pd
import yaml

from cea.config import Configuration
from cea.datamanagement.district_pathways.intervention_templates import (
    get_intervention_template_names,
    resolve_intervention_templates_to_recipe,
)
from cea.datamanagement.district_pathways.pathway_log import load_pathway_log_yaml
from cea.datamanagement.district_pathways.pathway_state import (
    DistrictEvolutionPathway,
    DistrictStateYear,
    validate_pathway_name,
)
from cea.datamanagement.district_pathways.pathway_status import (
    collect_state_phase_status,
    record_validated_state,
)
from cea.datamanagement.district_pathways.pathway_summary import build_pathway_year_row
from cea.datamanagement.district_pathways.pathway_validation import (
    raise_if_invalid_pathway_log,
    validate_baked_state_issues,
    validate_pathway_log_data,
)
from cea.inputlocator import InputLocator


class StockOnlyStateError(ValueError):
    """Raised when a stock-only state is targeted by a delete action."""


class YearRequiresEditError(ValueError):
    """Raised when a new year must be created through a real edit rather than a placeholder."""


class StockYearRequiresEditError(ValueError):
    """Raised when a stock year is promoted without any actual user-authored content."""


def _resolve_parent_scenario(scenario_path: str) -> str:
    """If scenario_path points to a child state folder (pathways/{name}/state_{year}),
    return the parent scenario path. Otherwise return as-is."""
    sep = os.sep + 'pathways' + os.sep
    idx = scenario_path.find(sep)
    if idx >= 0:
        return scenario_path[:idx]
    return scenario_path


def list_pathway_names(config: Configuration) -> list[str]:
    scenario = _resolve_parent_scenario(config.scenario)
    locator = InputLocator(scenario)
    container = locator.get_district_pathway_container_folder()
    if not os.path.isdir(container):
        return []
    return sorted(
        name
        for name in os.listdir(container)
        if os.path.isdir(os.path.join(container, name))
    )


def create_pathway(config: Configuration, pathway_name: str) -> dict[str, Any]:
    validated_name = validate_pathway_name(pathway_name)
    locator = InputLocator(config.scenario)
    pathway_folder = locator.get_district_pathway_folder(validated_name)
    if os.path.exists(pathway_folder):
        raise FileExistsError(f"Pathway '{validated_name}' already exists.")
    os.makedirs(pathway_folder, exist_ok=False)
    return {
        "pathway_name": validated_name,
        "pathway_folder": pathway_folder,
    }


def delete_pathway(config: Configuration, pathway_name: str) -> dict[str, Any]:
    validated_name = _require_existing_pathway(config, pathway_name)
    locator = InputLocator(config.scenario)
    pathway_folder = locator.get_district_pathway_folder(validated_name)
    shutil.rmtree(pathway_folder)
    return {
        "pathway_name": validated_name,
        "pathway_folder": pathway_folder,
        "action": "deleted_pathway",
        "message": f"Deleted pathway '{validated_name}'.",
        "messages": [
            "Removed the pathway log, intervention templates, baked states, simulation outputs, and saved state-status records.",
        ],
    }


def get_pathway_overview(config: Configuration) -> dict[str, Any]:
    # Auto-recover if config points to a child state folder
    parent = _resolve_parent_scenario(config.scenario)
    if parent != config.scenario:
        config.scenario = parent

    pathways: list[dict[str, Any]] = []
    all_years: list[int] = []
    for pathway_name in list_pathway_names(config):
        pathway = DistrictEvolutionPathway(config, pathway_name=pathway_name)
        years = pathway.required_state_years()
        all_years.extend(years)

        all_baked = bool(years)
        year_phases: dict[int, str] = {}
        for year in years:
            try:
                state = DistrictStateYear(
                    pathway_name=pathway_name,
                    year=int(year),
                    modifications=pathway.log_data.get(int(year), {}).get("modifications", {}) or {},
                    main_locator=pathway.main_locator,
                )
                signature = state.read_signature_record() or {}
                status = collect_state_phase_status(
                    pathway.main_locator,
                    pathway_name=pathway_name,
                    year=int(year),
                    source_log_hash=pathway.source_log_hash_for_year(int(year)),
                    signature=signature,
                )
                phase = status.get("primary_phase", "none")
                stale = status.get("has_stale_phase", False)
                year_phases[year] = phase
                if phase not in ("baked", "simulated") or stale:
                    all_baked = False
            except Exception:
                all_baked = False
                year_phases[year] = "none"

        pathways.append(
            {
                "pathway_name": pathway_name,
                "years": years,
                "state_count": len(years),
                "all_baked": all_baked,
                "year_phases": year_phases,
            }
        )

    return {
        "pathways": pathways,
        "span": {
            "start_year": min(all_years) if all_years else None,
            "end_year": max(all_years) if all_years else None,
        },
    }


def validate_pathway_log(config: Configuration, pathway_name: str) -> dict[str, Any]:
    validated_name = _require_existing_pathway(config, pathway_name)
    locator = InputLocator(config.scenario)
    log_data = load_pathway_log_yaml(
        locator,
        pathway_name=validated_name,
        allow_missing=True,
        allow_empty=True,
    )
    return validate_pathway_log_data(
        config=config,
        pathway_name=validated_name,
        log_data=log_data,
    )


def get_pathway_timeline(config: Configuration, pathway_name: str) -> dict[str, Any]:
    validated_name = _require_existing_pathway(config, pathway_name)
    pathway = DistrictEvolutionPathway(config, pathway_name=validated_name)
    validation = validate_pathway_log_data(
        config=config,
        pathway_name=validated_name,
        log_data=pathway.log_data,
    )
    overview = get_pathway_overview(config)

    rows = [
        build_pathway_year_row(
            pathway=pathway,
            year=int(year),
            issues=validation["issues_by_year"].get(str(int(year)), []),
        )
        for year in pathway.required_state_years()
    ]

    return {
        "pathway_name": validated_name,
        "years": rows,
        "validation": validation,
        "span": overview["span"],
    }


def create_pathway_year(
    config: Configuration,
    pathway_name: str,
    year: int,
) -> dict[str, Any]:
    validated_name = _require_existing_pathway(config, pathway_name)
    pathway = DistrictEvolutionPathway(config, pathway_name=validated_name)

    if int(year) in pathway.log_data:
        return _action_payload(
            pathway=pathway,
            year=int(year),
            action="state_year_ready",
            message=f"Year {int(year)} already exists in the pathway log.",
            messages=[
                "Select the year in the timeline and edit its saved content directly.",
            ],
        )

    row = build_pathway_year_row(pathway=pathway, year=int(year), issues=[])
    if int(year) in pathway.required_state_years() and row["state_kind"] == "stock":
        raise StockYearRequiresEditError(
            f"Year {int(year)} is a stock state. Open an editor and save a real change instead of creating an empty placeholder."
        )

    raise YearRequiresEditError(
        f"Year {int(year)} has not been saved yet. Open Building events, Apply templates, or Edit YAML and save a real change first."
    )


def delete_or_clear_state(config: Configuration, pathway_name: str, year: int) -> dict[str, Any]:
    validated_name = _require_existing_pathway(config, pathway_name)
    pathway = DistrictEvolutionPathway(config, pathway_name=validated_name)
    row = build_pathway_year_row(pathway=pathway, year=int(year), issues=[])

    if row["state_kind"] == "stock":
        raise StockOnlyStateError(
            f"Year {int(year)} is a stock-only state and cannot be deleted."
        )

    if row["state_kind"] == "manual":
        pathway.log_data.pop(int(year), None)
        pathway.save()
        _delete_state_artifacts(pathway.main_locator, validated_name, int(year))
        return _action_payload(
            pathway=pathway,
            year=int(year),
            action="deleted_state",
            message=f"Deleted explicit pathway state {int(year)}.",
            messages=[
                "Removed the year entry from the pathway log.",
                "Deleted the baked state folder if it existed.",
                "Deleted the saved state-status record if it existed.",
            ],
        )

    pathway.log_data.pop(int(year), None)
    pathway.save()
    _delete_state_artifacts(pathway.main_locator, validated_name, int(year))
    return _action_payload(
        pathway=pathway,
        year=int(year),
        action="cleared_manual_changes",
        message=f"Cleared manual changes for year {int(year)}.",
        messages=[
            "Removed the explicit pathway entry for this year.",
            "The stock-driven state remains available in the timeline.",
            "Deleted any baked state folder and saved state-status record for this year.",
        ],
    )


def get_year_editor_options(
    config: Configuration,
    pathway_name: str,
    year: int,
) -> dict[str, Any]:
    validated_name = _require_existing_pathway(config, pathway_name)
    pathway = DistrictEvolutionPathway(config, pathway_name=validated_name)
    entry = deepcopy(pathway.log_data.get(int(year), {}) or {})
    row = build_pathway_year_row(pathway=pathway, year=int(year), issues=[])
    available_buildings = sorted(pathway.get_building_construction_years().keys())

    return {
        "pathway_name": validated_name,
        "year": int(year),
        "available_new_buildings": available_buildings,
        "available_demolished_buildings": available_buildings,
        "available_templates": get_intervention_template_names(
            pathway.main_locator,
        ),
        "entry": entry,
        "yaml_preview": row["yaml_preview"],
    }


def update_year_building_events(
    config: Configuration,
    pathway_name: str,
    year: int,
    *,
    new_buildings: list[str],
    demolished_buildings: list[str],
) -> dict[str, Any]:
    validated_name = _require_existing_pathway(config, pathway_name)
    pathway = DistrictEvolutionPathway(config, pathway_name=validated_name)
    pathway.update_year_building_events(
        int(year),
        new_buildings=new_buildings,
        demolished_buildings=demolished_buildings,
    )
    raise_if_invalid_pathway_log(
        config=config,
        pathway_name=validated_name,
        log_data=pathway.log_data,
    )
    pathway.save()
    return _action_payload(
        pathway=pathway,
        year=int(year),
        action="updated_building_events",
        message=f"Saved building changes for year {int(year)}.",
        messages=[
            f"New buildings: {len(new_buildings)}",
            f"Demolished buildings: {len(demolished_buildings)}",
        ],
    )


def apply_templates_to_year(
    config: Configuration,
    pathway_name: str,
    year: int,
    *,
    template_names: list[str],
) -> dict[str, Any]:
    validated_name = _require_existing_pathway(config, pathway_name)
    if not template_names:
        raise ValueError("Select at least one intervention template.")

    pathway = DistrictEvolutionPathway(config, pathway_name=validated_name)
    merged_recipe = resolve_intervention_templates_to_recipe(
        locator=pathway.main_locator,
        template_names=template_names,
    )
    pathway.apply_year_modifications(int(year), merged_recipe)
    raise_if_invalid_pathway_log(
        config=config,
        pathway_name=validated_name,
        log_data=pathway.log_data,
    )
    pathway.save()
    return _action_payload(
        pathway=pathway,
        year=int(year),
        action="applied_templates",
        message=(
            f"Applied {len(template_names)} intervention template"
            f"{'' if len(template_names) == 1 else 's'} to year {int(year)}."
        ),
        messages=[
            f"Templates: {', '.join(template_names)}",
        ],
        templates=template_names,
    )


def update_year_yaml(
    config: Configuration,
    pathway_name: str,
    year: int,
    *,
    raw_yaml: str,
) -> dict[str, Any]:
    validated_name = _require_existing_pathway(config, pathway_name)
    pathway = DistrictEvolutionPathway(config, pathway_name=validated_name)
    parsed_entry = _parse_year_yaml(raw_yaml, int(year))

    if parsed_entry:
        parsed_entry.setdefault("created_at", str(pd.Timestamp.now()))
        parsed_entry.setdefault("modifications", parsed_entry.get("modifications", {}) or {})
        parsed_entry["latest_modified_at"] = str(pd.Timestamp.now())
        pathway.log_data[int(year)] = parsed_entry
    else:
        pathway.log_data.pop(int(year), None)

    raise_if_invalid_pathway_log(
        config=config,
        pathway_name=validated_name,
        log_data=pathway.log_data,
    )
    pathway.save()
    return _action_payload(
        pathway=pathway,
        year=int(year),
        action="saved_yaml",
        message=f"Saved YAML for year {int(year)}.",
        messages=[
            "Revalidated the pathway log after saving the explicit year entry.",
        ],
    )


def validate_baked_state(
    config: Configuration,
    pathway_name: str,
    year: int,
) -> dict[str, Any]:
    validated_name = _require_existing_pathway(config, pathway_name)
    pathway = DistrictEvolutionPathway(config, pathway_name=validated_name)
    return _validate_baked_state_payload(pathway, int(year))


def validate_all_baked_states(
    config: Configuration,
    pathway_name: str,
) -> dict[str, Any]:
    validated_name = _require_existing_pathway(config, pathway_name)
    pathway = DistrictEvolutionPathway(config, pathway_name=validated_name)

    results: list[dict[str, Any]] = []
    validated_years: list[int] = []
    invalid_years: list[int] = []
    issues_by_year: dict[int, list[str]] = {}

    for year in pathway.required_state_years():
        payload = _validate_baked_state_payload(pathway, int(year))
        results.append(payload)
        if payload.get("is_valid"):
            validated_years.append(int(year))
        else:
            invalid_years.append(int(year))
            issues_by_year[int(year)] = [
                str(issue)
                for issue in payload.get("issues", [])
                if str(issue).strip()
            ]

    return {
        "pathway_name": validated_name,
        "validated_years": validated_years,
        "invalid_years": invalid_years,
        "issues_by_year": issues_by_year,
        "results": results,
    }

def _require_existing_pathway(config: Configuration, pathway_name: str) -> str:
    validated_name = validate_pathway_name(pathway_name)
    locator = InputLocator(config.scenario)
    pathway_folder = locator.get_district_pathway_folder(validated_name)
    if not os.path.isdir(pathway_folder):
        raise FileNotFoundError(f"Pathway '{validated_name}' does not exist.")
    return validated_name


def _action_payload(
    *,
    pathway: DistrictEvolutionPathway,
    year: int,
    action: str,
    message: str,
    messages: list[str] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload = {
        "pathway_name": pathway.pathway_name,
        "year": int(year),
        "action": action,
        "message": message,
        "messages": messages or [],
        "log_file": pathway.main_locator.get_district_pathway_log_file(
            pathway_name=pathway.pathway_name
        ),
        "state_folder": pathway.main_locator.get_state_in_time_scenario_folder(
            pathway.pathway_name,
            int(year),
        ),
        "status_file": pathway.main_locator.get_district_pathway_state_status_file(
            pathway.pathway_name,
            int(year),
        ),
    }
    payload.update(extra)
    return payload


def _validate_baked_state_payload(
    pathway: DistrictEvolutionPathway,
    year: int,
) -> dict[str, Any]:
    issues = validate_baked_state_issues(pathway, int(year))
    if issues:
        return _action_payload(
            pathway=pathway,
            year=int(year),
            action="validated_state",
            message=f"Validation reported issues for year {int(year)}.",
            messages=[
                "The baked state does not currently match the pathway log.",
            ],
            is_valid=False,
            issues=issues,
        )

    validated_at = str(pd.Timestamp.now())
    record_validated_state(
        pathway.main_locator,
        pathway_name=pathway.pathway_name,
        year=int(year),
        validated_at=validated_at,
        source_log_hash=pathway.source_log_hash_for_year(int(year)),
    )
    return _action_payload(
        pathway=pathway,
        year=int(year),
        action="validated_state",
        message=f"Validated baked state year {int(year)}.",
        messages=[
            "Recorded a validation fingerprint for the current baked inputs.",
        ],
        is_valid=True,
        issues=[],
        validated_at=validated_at,
    )


def _parse_year_yaml(raw_yaml: str, year: int) -> dict[str, Any]:
    try:
        parsed = yaml.safe_load(raw_yaml) if raw_yaml.strip() else {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML: {exc}") from exc

    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise ValueError("Year YAML must be a mapping.")

    if len(parsed) == 1 and str(next(iter(parsed.keys()))) == str(int(year)):
        parsed = parsed[next(iter(parsed.keys()))]

    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise ValueError("Year YAML must decode to a mapping.")
    return cast(dict[str, Any], parsed)


def _delete_state_artifacts(locator: InputLocator, pathway_name: str, year: int) -> None:
    state_folder = locator.get_state_in_time_scenario_folder(pathway_name, int(year))
    shutil.rmtree(state_folder, ignore_errors=True)
    status_file = locator.get_district_pathway_state_status_file(pathway_name, int(year))
    if os.path.exists(status_file):
        os.remove(status_file)

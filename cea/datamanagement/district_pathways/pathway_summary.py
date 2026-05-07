from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal

import yaml

from cea.datamanagement.district_pathways.pathway_state import (
    DistrictEvolutionPathway,
    DistrictStateYear,
)
from cea.datamanagement.district_pathways.pathway_status import (
    collect_state_phase_status,
)

StateKind = Literal["manual", "stock", "mixed"]


def build_pathway_year_row(
    *,
    pathway: DistrictEvolutionPathway,
    year: int,
    issues: list[str],
) -> dict[str, Any]:
    entry_exists = int(year) in pathway.log_data
    entry = pathway.log_data.get(int(year), {}) or {}
    modifications = deepcopy(entry.get("modifications", {}) or {})
    explicit_building_events = pathway.get_explicit_building_events(int(year))
    building_events = pathway.get_combined_building_events(int(year))
    has_modifications = bool(modifications)
    has_explicit_building_events = any(explicit_building_events.values())
    has_stock_events = bool(pathway.get_derived_stock_new_buildings(int(year)))
    has_manual_content = has_modifications or has_explicit_building_events or (
        entry_exists and not has_stock_events
    )
    state_kind = _classify_state(
        has_manual_content=has_manual_content,
        has_stock_events=has_stock_events,
    )
    state = DistrictStateYear(
        pathway_name=pathway.pathway_name,
        year=int(year),
        modifications=modifications,
        main_locator=pathway.main_locator,
    )
    signature = state.read_signature_record() or {}
    status = collect_state_phase_status(
        pathway.main_locator,
        pathway_name=pathway.pathway_name,
        year=int(year),
        source_log_hash=pathway.source_log_hash_for_year(int(year)),
        signature=signature,
    )

    return {
        "year": int(year),
        "state_kind": state_kind,
        "has_modifications": has_modifications,
        "has_building_events": any(building_events.values()),
        "has_explicit_building_events": has_explicit_building_events,
        "exists_in_log": entry_exists,
        "modifications": modifications,
        "building_events": building_events,
        "explicit_building_events": explicit_building_events,
        "can_delete": state_kind == "manual",
        "can_clear_manual_changes": state_kind == "mixed",
        "has_state_folder": state.exists_on_disk(),
        "status": status,
        "latest_modified_at": entry.get("latest_modified_at"),
        "latest_confirmed_at": status.get("latest_confirmed_at"),
        "created_at": entry.get("created_at"),
        "yaml_preview": dump_year_yaml(entry),
        "summary": _summary_payload(
            state_kind=state_kind,
            has_manual_content=has_manual_content,
            modifications=modifications,
            building_events=building_events,
        ),
        "validation": {
            "status": "error" if issues else "ok",
            "issues": issues,
        },
    }


def dump_year_yaml(entry: dict[str, Any]) -> str:
    if not entry:
        return "# No explicit YAML entry for this year.\n"
    return yaml.safe_dump(entry, sort_keys=False)


def _classify_state(
    *,
    has_manual_content: bool,
    has_stock_events: bool,
) -> StateKind:
    if has_manual_content and has_stock_events:
        return "mixed"
    if has_manual_content:
        return "manual"
    return "stock"


def _summary_payload(
    *,
    state_kind: StateKind,
    has_manual_content: bool,
    modifications: dict[str, Any],
    building_events: dict[str, list[str]],
) -> dict[str, Any]:
    modification_count = _count_modification_fields(modifications)
    new_count = len(building_events.get("new_buildings", []) or [])
    demolished_count = len(building_events.get("demolished_buildings", []) or [])

    parts: list[str] = []
    if modification_count:
        parts.append(_pluralise(modification_count, "change"))
    elif has_manual_content:
        parts.append("Manual year")

    if new_count:
        parts.append(_pluralise(new_count, "new building"))
    if demolished_count:
        parts.append(_pluralise(demolished_count, "demolished building"))
    if not parts:
        parts.append("Baseline stock state")

    return {
        "text": ", ".join(parts),
        "state_kind": state_kind,
        "modification_count": modification_count,
        "new_buildings_count": new_count,
        "demolished_buildings_count": demolished_count,
    }


def _count_modification_fields(modifications: dict[str, Any]) -> int:
    count = 0
    for components in (modifications or {}).values():
        for fields in (components or {}).values():
            count += len(fields or {})
    return count


def _pluralise(count: int, noun: str) -> str:
    if count == 1:
        return f"1 {noun}"
    return f"{count} {noun}s"

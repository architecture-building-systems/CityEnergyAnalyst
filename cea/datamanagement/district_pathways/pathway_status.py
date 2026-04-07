from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from cea.inputlocator import InputLocator


def read_state_status(
    locator: InputLocator,
    *,
    pathway_name: str,
    year: int,
) -> dict[str, Any]:
    path = locator.get_district_pathway_state_status_file(pathway_name, int(year))
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_state_status(
    locator: InputLocator,
    *,
    pathway_name: str,
    year: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    path = locator.get_district_pathway_state_status_file(pathway_name, int(year))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    current = read_state_status(locator, pathway_name=pathway_name, year=year)
    current.update(payload)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(current, handle, indent=2, sort_keys=True)
    return current


def hash_folder(path: str) -> str:
    digest = hashlib.sha256()
    for root, _, files in os.walk(path):
        rel_root = os.path.relpath(root, path)
        digest.update(rel_root.replace("\\", "/").encode("utf-8"))
        for file_name in sorted(files):
            file_path = os.path.join(root, file_name)
            rel_path = os.path.relpath(file_path, path).replace("\\", "/")
            digest.update(rel_path.encode("utf-8"))
            with open(file_path, "rb") as handle:
                while True:
                    chunk = handle.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
    return digest.hexdigest()


def hash_state_inputs(
    locator: InputLocator,
    *,
    pathway_name: str,
    year: int,
) -> str | None:
    state_folder = locator.get_state_in_time_scenario_folder(pathway_name, int(year))
    inputs_folder = os.path.join(state_folder, "inputs")
    if not os.path.isdir(inputs_folder):
        return None
    return hash_folder(inputs_folder)


def hash_state_folder(
    locator: InputLocator,
    *,
    pathway_name: str,
    year: int,
) -> str | None:
    state_folder = locator.get_state_in_time_scenario_folder(pathway_name, int(year))
    if not os.path.isdir(state_folder):
        return None
    return hash_folder(state_folder)


def record_baked_state(
    locator: InputLocator,
    *,
    pathway_name: str,
    year: int,
    built_at: str,
    source_log_hash: str,
) -> dict[str, Any]:
    inputs_hash = hash_state_inputs(locator, pathway_name=pathway_name, year=year)
    if inputs_hash is None:
        raise FileNotFoundError(
            f"Cannot record baked state for missing inputs folder: {pathway_name} state_{int(year)}"
        )
    return write_state_status(
        locator,
        pathway_name=pathway_name,
        year=year,
        payload={
            "baked_inputs_hash": inputs_hash,
            "baked_source_log_hash": source_log_hash,
            "built_at": built_at,
        },
    )


def record_validated_state(
    locator: InputLocator,
    *,
    pathway_name: str,
    year: int,
    validated_at: str,
    source_log_hash: str,
) -> dict[str, Any]:
    inputs_hash = hash_state_inputs(locator, pathway_name=pathway_name, year=year)
    if inputs_hash is None:
        raise FileNotFoundError(
            f"Cannot record validation for missing inputs folder: {pathway_name} state_{int(year)}"
        )
    return write_state_status(
        locator,
        pathway_name=pathway_name,
        year=year,
        payload={
            "validated_inputs_hash": inputs_hash,
            "validated_source_log_hash": source_log_hash,
            "validated_at": validated_at,
        },
    )


def record_simulated_state(
    locator: InputLocator,
    *,
    pathway_name: str,
    year: int,
    simulated_at: str,
    source_log_hash: str,
    workflow: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    state_hash = hash_state_folder(locator, pathway_name=pathway_name, year=year)
    if state_hash is None:
        raise FileNotFoundError(
            f"Cannot record simulation for missing state folder: {pathway_name} state_{int(year)}"
        )
    return write_state_status(
        locator,
        pathway_name=pathway_name,
        year=year,
        payload={
            "simulated_state_hash": state_hash,
            "simulated_source_log_hash": source_log_hash,
            "simulated_at": simulated_at,
            "simulated_workflow": workflow or [],
        },
    )


def collect_state_phase_status(
    locator: InputLocator,
    *,
    pathway_name: str,
    year: int,
    source_log_hash: str,
    signature: dict[str, Any],
) -> dict[str, Any]:
    status_record = read_state_status(locator, pathway_name=pathway_name, year=year)
    inputs_hash = hash_state_inputs(locator, pathway_name=pathway_name, year=year)
    state_hash = None

    validation = _collect_validation_phase(
        status_record=status_record,
        inputs_hash=inputs_hash,
        source_log_hash=source_log_hash,
    )
    bake = _collect_bake_phase(
        status_record=status_record,
        signature=signature,
        inputs_hash=inputs_hash,
        source_log_hash=source_log_hash,
    )
    if status_record.get("simulated_state_hash"):
        state_hash = hash_state_folder(locator, pathway_name=pathway_name, year=year)
    simulation = _collect_simulation_phase(
        status_record=status_record,
        signature=signature,
        state_hash=state_hash,
        source_log_hash=source_log_hash,
        bake=bake,
    )

    latest_confirmed_at = max(
        [value for value in (validation["at"], bake["at"], simulation["at"]) if value],
        default=None,
    )
    has_stale_phase = any(
        phase["state"].startswith("changed_after_")
        for phase in (validation, bake, simulation)
    )
    primary_phase = "none"
    if simulation["state"] == "simulated":
        primary_phase = "simulated"
    elif bake["state"] == "baked":
        primary_phase = "baked"
    elif validation["state"] == "validated":
        primary_phase = "validated"

    return {
        "validation": validation,
        "bake": bake,
        "simulation": simulation,
        "latest_confirmed_at": latest_confirmed_at,
        "primary_phase": primary_phase,
        "has_stale_phase": has_stale_phase,
    }


def _collect_validation_phase(
    *,
    status_record: dict[str, Any],
    inputs_hash: str | None,
    source_log_hash: str,
) -> dict[str, Any]:
    validated_hash = status_record.get("validated_inputs_hash")
    validated_log_hash = status_record.get("validated_source_log_hash")
    validated_at = status_record.get("validated_at")

    if not validated_hash or not validated_at or inputs_hash is None:
        return _phase_payload("not_validated", "Not validated", validated_at)

    if validated_hash != inputs_hash or validated_log_hash != source_log_hash:
        return _phase_payload(
            "changed_after_validation",
            "Changed after validation",
            validated_at,
        )

    return _phase_payload("validated", "Validated", validated_at)


def _collect_bake_phase(
    *,
    status_record: dict[str, Any],
    signature: dict[str, Any],
    inputs_hash: str | None,
    source_log_hash: str,
) -> dict[str, Any]:
    baked_hash = status_record.get("baked_inputs_hash")
    baked_log_hash = status_record.get("baked_source_log_hash")
    built_at = status_record.get("built_at") or signature.get("built_at")

    if inputs_hash is None:
        return _phase_payload("not_baked", "Not baked", built_at)

    if baked_hash and built_at:
        if baked_hash != inputs_hash or baked_log_hash != source_log_hash:
            return _phase_payload(
                "changed_after_bake",
                "Changed after bake",
                built_at,
            )
        return _phase_payload("baked", "Baked", built_at)

    if built_at:
        if baked_log_hash and baked_log_hash != source_log_hash:
            return _phase_payload("changed_after_bake", "Changed after bake", built_at)
        return _phase_payload("baked", "Baked", built_at)

    return _phase_payload("not_baked", "Not baked", built_at)


def _collect_simulation_phase(
    *,
    status_record: dict[str, Any],
    signature: dict[str, Any],
    state_hash: str | None,
    source_log_hash: str,
    bake: dict[str, Any],
) -> dict[str, Any]:
    simulated_hash = status_record.get("simulated_state_hash")
    simulated_log_hash = status_record.get("simulated_source_log_hash")
    simulated_at = status_record.get("simulated_at") or signature.get("simulated_at")

    if simulated_hash and simulated_at:
        if (
            state_hash is None
            or simulated_hash != state_hash
            or simulated_log_hash != source_log_hash
            or bake["state"] == "changed_after_bake"
        ):
            return _phase_payload(
                "changed_after_simulation",
                "Changed after simulation",
                simulated_at,
            )
        return _phase_payload("simulated", "Simulated", simulated_at)

    if simulated_at:
        return _phase_payload("simulated", "Simulated", simulated_at)

    return _phase_payload("not_simulated", "Not simulated", simulated_at)


def _phase_payload(state: str, label: str, at: Any) -> dict[str, Any]:
    return {
        "state": state,
        "label": label,
        "at": at,
    }

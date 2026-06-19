"""Shared stdout formatting for district-pathway dashboard jobs."""

from __future__ import annotations

from typing import Any


def print_pathway_action_output(payload: dict[str, Any]) -> None:
    """Print a stable, human-readable summary for native dashboard job logs."""
    message = payload.get("message")
    if message:
        print(str(message), flush=True)

    for line in payload.get("messages", []) or []:
        if str(line).strip():
            print(f"- {line}", flush=True)

    templates = payload.get("templates") or []
    if templates:
        print(f"Templates: {', '.join(str(template) for template in templates)}", flush=True)

    if "is_valid" in payload:
        validity = "valid" if payload.get("is_valid") else "invalid"
        print(f"Validation result: {validity}", flush=True)

    validated_at = payload.get("validated_at")
    if validated_at:
        print(f"Validated at: {validated_at}", flush=True)

    issues = payload.get("issues") or []
    if issues:
        print("Issues:", flush=True)
        for issue in issues:
            print(f"- {issue}", flush=True)

    pathway_name = payload.get("pathway_name")
    year = payload.get("year")
    if pathway_name is not None:
        print(f"Pathway: {pathway_name}", flush=True)
    if year is not None:
        print(f"Year: {year}", flush=True)

    for label, key in (
        ("Log file", "log_file"),
        ("State folder", "state_folder"),
        ("Status file", "status_file"),
        ("Pathway folder", "pathway_folder"),
    ):
        value = payload.get(key)
        if value:
            print(f"{label}: {value}", flush=True)

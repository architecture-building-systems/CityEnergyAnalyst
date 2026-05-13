"""Materialise pathway states from the district pathway log.

This module exists as a dedicated CEA script entrypoint. The core implementation lives in
`cea.datamanagement.district_pathways.pathway_state`.
"""

from __future__ import annotations

from cea.config import Configuration
from cea.datamanagement.district_pathways.pathway_state import DistrictEvolutionPathway
from cea.datamanagement.district_pathways.pathway_timeline import (
    validate_all_baked_states,
)


def main(config: Configuration) -> None:
    pathway_name = config.bake_pathway_states.existing_pathway_name
    if not pathway_name:
        raise ValueError(
            "No existing pathway name provided. "
            "Please provide an existing pathway name to bake states from."
        )
    print("=" * 80, flush=True)
    print(
        f"Starting pathway state bake for '{pathway_name}'.",
        flush=True,
    )
    print(
        "Task hints will list each state year as it is materialised.",
        flush=True,
    )
    print("=" * 80, flush=True)
    pathway = DistrictEvolutionPathway(config, pathway_name=pathway_name)
    pathway.bake_states_from_log()

    # Refresh validation fingerprints for every baked state so the pathway
    # viewer does not show them as stale straight after a successful bake.
    print("Validating baked states...", flush=True)
    summary = validate_all_baked_states(config, pathway_name)
    validated_years = summary.get("validated_years") or []
    invalid_years = summary.get("invalid_years") or []
    if validated_years:
        print(f"Validated years: {validated_years}", flush=True)
    if invalid_years:
        issues_by_year = summary.get("issues_by_year") or {}
        print(
            f"Validation reported issues for years: {invalid_years}",
            flush=True,
        )
        for year, issues in issues_by_year.items():
            for issue in issues:
                print(f"  - state_{year}: {issue}", flush=True)

    print(
        f"Finished pathway state bake for '{pathway_name}'.",
        flush=True,
    )

"""Materialise pathway states from the district pathway log.

This module exists as a dedicated CEA script entrypoint. The core implementation lives in
`cea.datamanagement.district_pathways.pathway_state`.
"""

from __future__ import annotations

from cea.config import Configuration
from cea.datamanagement.district_pathways.pathway_state import DistrictEvolutionPathway


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
    print(
        f"Finished pathway state bake for '{pathway_name}'.",
        flush=True,
    )

"""Step 4 pathway simulation entrypoint.

This module keeps the high-level orchestration for pathway-state simulations in one place:

- validate that the baked `state_{year}` folders match the pathway log
- run each state in two passes
  - first the base workflow through demand
  - then the post-demand tail with optional network steps and emissions
- record the final workflow back into the pathway log
- build the pathway emissions timeline after all state years finish

The detailed decisions for workflow construction, service checks, and network carry-forward
live in sibling modules so that this file stays readable as the top-level runtime story.
"""

from __future__ import annotations

from copy import deepcopy

import pandas as pd

from cea.config import Configuration
from cea.datamanagement.district_level_states.district_emission_timeline import (
    create_district_pathway_emissions_timeline,
)
from cea.datamanagement.district_level_states.state_scenario import (
    DistrictEvolutionPathway,
    DistrictStateYear,
)
from cea.datamanagement.district_level_states.state_simulation import workflow_assembly
from cea.datamanagement.district_level_states.timeline_integrity import (
    check_district_pathway_log_yaml_integrity,
)


def simulate_all_states(config: Configuration, pathway_name: str) -> None:
    """Run Step 4 for every pathway state year in the selected pathway."""
    pathway = DistrictEvolutionPathway(config, pathway_name=pathway_name)

    check_district_pathway_log_yaml_integrity(config, pathway_name)

    state_years = pathway.list_state_years_on_disk()
    if not state_years:
        raise ValueError(
            "No pathway states found in the district pathway folder."
        )
    state_years.sort()

    print("\n" + "=" * 80)
    print("Starting state simulations for all pathway states...")
    print("=" * 80)
    print(f"Found state years: {state_years}")
    print(f"Years to simulate: {state_years}\n")

    simulated_years: list[int] = []
    for year in state_years:
        base_workflow = workflow_assembly.prepare_base_workflow_for_state(
            config=config,
            pathway_name=pathway_name,
            year=int(year),
        )
        print(f"\n--- Simulating state {year}: base workflow ---")
        state = DistrictStateYear(
            pathway_name=pathway.pathway_name,
            year=int(year),
            modifications={},
            main_locator=pathway.main_locator,
        )
        state.simulate(config, workflow=base_workflow, mark_simulated=False)

        print(f"\n--- Simulating state {year}: post-demand workflow ---")
        post_demand_workflow = workflow_assembly.prepare_post_demand_workflow_for_state(
            config=config,
            pathway_name=pathway_name,
            year=int(year),
            state_years=state_years,
        )
        full_workflow = deepcopy(base_workflow) + deepcopy(post_demand_workflow)
        state.simulate(
            config,
            workflow=post_demand_workflow,
            recorded_workflow=full_workflow,
        )

        entry = pathway.log_data.get(int(year), {}) or {}
        entry["simulation_workflow"] = full_workflow
        entry["latest_simulated_at"] = str(pd.Timestamp.now())
        pathway.log_data[int(year)] = entry

        simulated_years.append(int(year))
        print(f"Simulation for pathway state year {year} completed.")

    pathway.save()

    print("State-in-time simulations finished.")
    print(f"Simulated: {len(simulated_years)} years")
    if simulated_years:
        print(f"Years simulated: {simulated_years}")
    print("Skipped: 0 years")


def main(config: Configuration) -> None:
    pathway_name = config.pathway_simulations.existing_pathway_name
    if not pathway_name:
        raise ValueError(
            "No existing pathway name provided. "
            "Please provide an existing pathway name to simulate all states from."
        )

    simulate_all_states(config, pathway_name=pathway_name)
    print("All pathway states have been simulated.")
    df = create_district_pathway_emissions_timeline(
        config,
        pathway_name=pathway_name,
    )
    print(f"District pathway emissions timeline saved with {len(df)} years.")


if __name__ == "__main__":
    main(Configuration())

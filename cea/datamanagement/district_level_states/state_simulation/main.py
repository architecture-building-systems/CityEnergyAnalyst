"""Step 4 district timeline simulation entrypoint.

This module keeps the high-level orchestration for state timeline simulations in one place:

- validate that the baked `state_{year}` folders match the timeline log
- run each state in two passes
  - first the base workflow through demand
  - then the post-demand tail with optional network steps and emissions
- record the final workflow back into the timeline log
- build the district material timeline after all state years finish

The detailed decisions for workflow construction, service checks, and network carry-forward
live in sibling modules so that this file stays readable as the top-level runtime story.
"""

from __future__ import annotations

from copy import deepcopy

import pandas as pd

from cea.config import Configuration
from cea.datamanagement.district_level_states.district_emission_timeline import (
    create_district_material_timeline,
)
from cea.datamanagement.district_level_states.state_scenario import (
    DistrictEventTimeline,
    DistrictStateYear,
)
from cea.datamanagement.district_level_states.state_simulation import workflow_assembly
from cea.datamanagement.district_level_states.timeline_integrity import (
    check_district_timeline_log_yaml_integrity,
)


def simulate_all_states(config: Configuration, timeline_name: str) -> None:
    """Run Step 4 for every state year in the selected timeline."""
    timeline = DistrictEventTimeline(config, timeline_name=timeline_name)

    check_district_timeline_log_yaml_integrity(config, timeline_name)

    state_years = timeline.list_state_years_on_disk()
    if not state_years:
        raise ValueError(
            "No state-in-time scenarios found in the district timeline folder."
        )
    state_years.sort()

    print("\n" + "=" * 80)
    print("Starting state simulations for all state-in-time scenarios...")
    print("=" * 80)
    print(f"Found state years: {state_years}")
    print(f"Years to simulate: {state_years}\n")

    simulated_years: list[int] = []
    for year in state_years:
        base_workflow = workflow_assembly.prepare_base_workflow_for_state(
            config=config,
            timeline_name=timeline_name,
            year=int(year),
        )
        print(f"\n--- Simulating state {year}: base workflow ---")
        state = DistrictStateYear(
            timeline_name=timeline.timeline_name,
            year=int(year),
            modifications={},
            main_locator=timeline.main_locator,
        )
        state.simulate(config, workflow=base_workflow, mark_simulated=False)

        print(f"\n--- Simulating state {year}: post-demand workflow ---")
        post_demand_workflow = workflow_assembly.prepare_post_demand_workflow_for_state(
            config=config,
            timeline_name=timeline_name,
            year=int(year),
            state_years=state_years,
        )
        full_workflow = deepcopy(base_workflow) + deepcopy(post_demand_workflow)
        state.simulate(
            config,
            workflow=post_demand_workflow,
            recorded_workflow=full_workflow,
        )

        entry = timeline.log_data.get(int(year), {}) or {}
        entry["simulation_workflow"] = full_workflow
        entry["latest_simulated_at"] = str(pd.Timestamp.now())
        timeline.log_data[int(year)] = entry

        simulated_years.append(int(year))
        print(f"Simulation for state-in-time scenario year {year} completed.")

    timeline.save()

    print("State-in-time simulations finished.")
    print(f"Simulated: {len(simulated_years)} years")
    if simulated_years:
        print(f"Years simulated: {simulated_years}")
    print("Skipped: 0 years")


def main(config: Configuration) -> None:
    timeline_name = config.state_simulations.existing_timeline_name
    if not timeline_name:
        raise ValueError(
            "No existing timeline name provided. "
            "Please provide an existing timeline name to simulate all states from."
        )

    simulate_all_states(config, timeline_name=timeline_name)
    print("All state-in-time scenarios have been simulated.")
    df = create_district_material_timeline(config, timeline_variant_name=timeline_name)
    print(f"District material timeline saved with {len(df)} years.")


if __name__ == "__main__":
    main(Configuration())

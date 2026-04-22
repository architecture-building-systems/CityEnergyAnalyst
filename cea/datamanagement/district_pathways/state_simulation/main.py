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

import json
import os
from copy import deepcopy

import pandas as pd

from cea.config import Configuration
from cea.inputlocator import InputLocator
from cea.datamanagement.district_pathways.pathway_emissions_timeline import (
    create_district_pathway_emissions_timeline,
)
from cea.datamanagement.district_pathways.pathway_state import (
    DistrictEvolutionPathway,
    DistrictStateYear,
)
from cea.datamanagement.district_pathways.state_simulation import workflow_assembly
from cea.datamanagement.district_pathways.state_simulation.workflow_assembly import (
    determine_network_phase_mode,
    NetworkPhaseMode,
)
from cea.datamanagement.district_pathways.pathway_integrity import (
    check_district_pathway_log_yaml_integrity,
)
from cea.datamanagement.district_pathways.pathway_status import (
    collect_state_phase_status,
    read_state_status,
    record_simulated_state,
    write_pathway_metadata,
)
from cea.datamanagement.district_pathways.pathway_timeline import (
    validate_all_baked_states,
)


def _cleanup_state_outputs(state_locator: InputLocator, year: int) -> None:
    """Remove previous simulation outputs from a state folder to allow re-runs."""
    import os
    import shutil

    outputs_folder = os.path.join(state_locator.scenario, "outputs")
    if os.path.isdir(outputs_folder):
        print(f"State {year}: Cleaning previous outputs...", flush=True)
        shutil.rmtree(outputs_folder)


def simulate_all_states(config: Configuration, pathway_name: str) -> None:
    """Run Step 4 for every pathway state year in the selected pathway."""
    pathway = DistrictEvolutionPathway(config, pathway_name=pathway_name)

    check_district_pathway_log_yaml_integrity(config, pathway_name)

    # Validate all baked states before simulation
    print("Validating all baked states before simulation...", flush=True)
    summary = validate_all_baked_states(config, pathway_name)
    if summary.get("invalid_years"):
        invalid = summary["invalid_years"]
        issues_detail = []
        for year in invalid:
            issues = summary.get("issues_by_year", {}).get(year, [])
            issues_detail.append(f"  {year}: {'; '.join(issues) if issues else 'validation failed'}")
        raise ValueError(
            f"Cannot simulate — validation issues found in year(s): "
            f"{', '.join(str(y) for y in invalid)}\n"
            + "\n".join(issues_detail)
        )

    # Warn about custom states with stale simulation outputs
    state_years_on_disk = pathway.list_state_years_on_disk()
    stale_custom = []
    for year in state_years_on_disk:
        status_record = read_state_status(
            InputLocator(config.scenario),
            pathway_name=pathway_name,
            year=int(year),
        )
        if status_record.get("custom"):
            custom_at = status_record.get("custom_at")
            simulated_at = status_record.get("simulated_at")
            if custom_at and simulated_at and custom_at > simulated_at:
                stale_custom.append(int(year))
            elif custom_at and not simulated_at:
                stale_custom.append(int(year))
    if stale_custom:
        print(
            f"\n⚠ Warning: Custom state(s) {stale_custom} have stale or missing "
            f"simulation outputs (inputs were edited after the last simulation).\n"
            f"  These states will be re-simulated unless 'skip-custom-states' is enabled.\n"
            f"  If skipped, their outputs may not reflect the current inputs.",
            flush=True,
        )

    state_years = state_years_on_disk
    if not state_years:
        raise ValueError(
            "No pathway states found in the district pathway folder."
        )
    state_years.sort()

    # Determine network phase mode across all state years
    main_locator = InputLocator(config.scenario)
    phase_mode, connections_by_year = determine_network_phase_mode(
        main_locator=main_locator,
        pathway_name=pathway_name,
        state_years=state_years,
    )
    print(f"\nNetwork phase mode: {phase_mode.value}", flush=True)
    if connections_by_year:
        for yr, conns in sorted(connections_by_year.items()):
            print(f"  State {yr}: {conns}", flush=True)

    # Optionally skip years that are already fully simulated and not stale.
    # Stale-simulated (red-over-black) and baked-only (blue) years still run.
    # IMPORTANT: we only filter the *loop* years. `state_years` (the full
    # sorted list) is still passed to workflow assembly so that
    # `copy_previous_network_for_state` can find an earlier skipped year's
    # network and chain filter mode off of it. Otherwise the first eligible
    # year would be treated as "no predecessor" and rebuild the network from
    # scratch instead of filtering from the prior state.
    skip_already_simulated = bool(
        getattr(config.pathway_simulations, "skip_already_simulated_states", True)
    )
    skip_custom = bool(
        getattr(config.pathway_simulations, "skip_custom_states", False)
    )
    skipped_years: list[int] = []
    years_to_simulate: list[int] = list(state_years)
    if skip_already_simulated or skip_custom:
        eligible: list[int] = []
        for year in state_years:
            state = DistrictStateYear(
                pathway_name=pathway.pathway_name,
                year=int(year),
                modifications={},
                main_locator=pathway.main_locator,
            )
            signature = state.read_signature_record() or {}
            status = collect_state_phase_status(
                main_locator,
                pathway_name=pathway_name,
                year=int(year),
                source_log_hash=pathway.source_log_hash_for_year(int(year)),
                signature=signature,
            )
            phase = status.get("primary_phase")
            if skip_custom and phase == "custom":
                state_folder = main_locator.get_state_in_time_scenario_folder(
                    pathway_name=pathway_name, year_of_state=year
                )
                outputs_folder = os.path.join(state_folder, "outputs")
                if not os.path.isdir(outputs_folder):
                    raise ValueError(
                        f"Cannot skip custom state {year} — it has no simulation outputs.\n"
                        f"Either disable 'skip-custom-states' to let Simulate Pathway run it, "
                        f"or enter the state in sub-scenario mode and run the simulation manually."
                    )
                skipped_years.append(int(year))
            elif (
                skip_already_simulated
                and phase == "simulated"
                and not status.get("has_stale_phase")
            ):
                skipped_years.append(int(year))
            else:
                eligible.append(int(year))
        years_to_simulate = eligible

    print("\n" + "=" * 80, flush=True)
    print("Starting state simulations for all pathway states...", flush=True)
    print("=" * 80, flush=True)
    print(f"Years to simulate: {years_to_simulate}", flush=True)
    if skipped_years:
        print(
            f"Years skipped (already simulated, not stale): {skipped_years}",
            flush=True,
        )
    print("", flush=True)

    if not years_to_simulate:
        print(
            "All pathway states are already simulated and up to date. "
            "Nothing to do.",
            flush=True,
        )

    simulated_years: list[int] = []
    for year in years_to_simulate:
        # Clean previous simulation outputs to allow re-runs
        state_locator = InputLocator(
            main_locator.get_state_in_time_scenario_folder(
                pathway_name=pathway_name, year_of_state=year
            )
        )
        _cleanup_state_outputs(state_locator, year)

        print(json.dumps({
            "__cea_progress__": "pathway-state-started",
            "pathway_name": pathway_name,
            "year": int(year),
        }), flush=True)

        base_workflow = workflow_assembly.prepare_base_workflow_for_state(
            config=config,
            pathway_name=pathway_name,
            year=int(year),
        )
        print(f"\n--- Simulating state {year}: base workflow ---", flush=True)
        state = DistrictStateYear(
            pathway_name=pathway.pathway_name,
            year=int(year),
            modifications={},
            main_locator=pathway.main_locator,
        )
        state.simulate(config, workflow=base_workflow, mark_simulated=False)

        print(
            f"\n--- Simulating state {year}: post-demand workflow ---",
            flush=True,
        )
        post_demand_workflow = workflow_assembly.prepare_post_demand_workflow_for_state(
            config=config,
            pathway_name=pathway_name,
            year=int(year),
            state_years=state_years,
            phase_mode=phase_mode,
            connections_by_year=connections_by_year,
        )
        full_workflow = deepcopy(base_workflow) + deepcopy(post_demand_workflow)
        state.simulate(
            config,
            workflow=post_demand_workflow,
            recorded_workflow=full_workflow,
        )

        entry = pathway.log_data.get(int(year), {}) or {}
        entry["simulation_workflow"] = full_workflow
        simulated_at = str(pd.Timestamp.now())
        entry["latest_simulated_at"] = simulated_at
        pathway.log_data[int(year)] = entry
        record_simulated_state(
            pathway.main_locator,
            pathway_name=pathway_name,
            year=int(year),
            simulated_at=simulated_at,
            source_log_hash=pathway.source_log_hash_for_year(int(year)),
            workflow=full_workflow,
        )

        simulated_years.append(int(year))
        print(json.dumps({
            "__cea_progress__": "pathway-state-simulated",
            "pathway_name": pathway_name,
            "year": int(year),
        }), flush=True)
        print(f"Simulation for pathway state year {year} completed.", flush=True)

    pathway.save()

    write_pathway_metadata(
        InputLocator(config.scenario),
        pathway_name=pathway_name,
        payload={"pathway_simulated_at": str(pd.Timestamp.now())},
    )

    print("State-in-time simulations finished.", flush=True)
    print(f"Simulated: {len(simulated_years)} years", flush=True)
    if simulated_years:
        print(f"Years simulated: {simulated_years}", flush=True)
    print(f"Skipped: {len(skipped_years)} years", flush=True)
    if skipped_years:
        print(f"Years skipped: {skipped_years}", flush=True)


def main(config: Configuration) -> None:
    pathway_name = config.pathway_simulations.existing_pathway_name
    if not pathway_name:
        raise ValueError(
            "No existing pathway name provided. "
            "Please provide an existing pathway name to simulate all states from."
        )

    print("=" * 80, flush=True)
    print(
        f"Starting pathway simulation for '{pathway_name}'.",
        flush=True,
    )
    print(
        "Task hints will list each state year and workflow phase as it runs.",
        flush=True,
    )
    print("=" * 80, flush=True)
    simulate_all_states(config, pathway_name=pathway_name)
    print("All pathway states have been simulated.", flush=True)
    try:
        df = create_district_pathway_emissions_timeline(
            config,
            pathway_name=pathway_name,
        )
        print(
            f"District pathway emissions timeline saved with {len(df)} years.",
            flush=True,
        )
    except Exception as exc:
        print(
            f"Warning: Could not create pathway emissions timeline: {exc}\n"
            "State simulations completed successfully. "
            "The emissions timeline can be generated separately once the issue is resolved.",
            flush=True,
        )


if __name__ == "__main__":
    main(Configuration())

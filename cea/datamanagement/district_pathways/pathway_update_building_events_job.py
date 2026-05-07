"""Native dashboard job entry point for saving pathway-year building edits across one or more pathways."""

from cea.config import Configuration
from cea.datamanagement.district_pathways.job_output import print_pathway_action_output
from cea.datamanagement.district_pathways.pathway_timeline import update_year_building_events


def main(config: Configuration) -> dict:
    pathway_names = config.pathway_state_edit.existing_pathway_names
    year = config.pathway_state_edit.year_of_state
    new_buildings = config.pathway_state_edit.buildings_to_construct
    demolished_buildings = config.pathway_state_edit.buildings_to_demolish

    if not pathway_names:
        raise ValueError("No pathways selected.")

    payload = None
    for pathway_name in pathway_names:
        print(f"\n--- Updating building events for pathway '{pathway_name}' ---", flush=True)
        payload = update_year_building_events(
            config,
            pathway_name,
            year,
            new_buildings=new_buildings,
            demolished_buildings=demolished_buildings,
        )
        print_pathway_action_output(payload)

    print(
        f"\nUpdated building events for {len(pathway_names)} pathway(s).",
        flush=True,
    )
    return payload


if __name__ == "__main__":
    main(Configuration())

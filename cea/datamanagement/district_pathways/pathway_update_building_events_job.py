"""Native dashboard job entry point for saving pathway-year building edits."""

from cea.config import Configuration
from cea.datamanagement.district_pathways.job_output import print_pathway_action_output
from cea.datamanagement.district_pathways.pathway_timeline import update_year_building_events


def main(config: Configuration) -> dict:
    pathway_name = config.pathway_state_edit.existing_pathway_name
    year = config.pathway_state_edit.year_of_state
    payload = update_year_building_events(
        config,
        pathway_name,
        year,
        new_buildings=config.pathway_state_edit.new_buildings,
        demolished_buildings=config.pathway_state_edit.demolished_buildings,
    )
    print_pathway_action_output(payload)
    return payload


if __name__ == "__main__":
    main(Configuration())

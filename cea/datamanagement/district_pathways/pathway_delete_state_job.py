"""Native dashboard job entry point for deleting or clearing one pathway year."""

from cea.config import Configuration
from cea.datamanagement.district_pathways.job_output import print_pathway_action_output
from cea.datamanagement.district_pathways.pathway_timeline import delete_or_clear_state


def main(config: Configuration) -> dict:
    pathway_name = config.pathway_state_edit.existing_pathway_name
    year = config.pathway_state_edit.year_of_state
    payload = delete_or_clear_state(config, pathway_name, year)
    print_pathway_action_output(payload)
    return payload


if __name__ == "__main__":
    main(Configuration())

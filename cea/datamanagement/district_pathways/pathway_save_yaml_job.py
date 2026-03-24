"""Native dashboard job entry point for expert YAML edits of one pathway year."""

from cea.config import Configuration
from cea.datamanagement.district_pathways.job_output import print_pathway_action_output
from cea.datamanagement.district_pathways.pathway_timeline import update_year_yaml


def main(config: Configuration) -> dict:
    pathway_name = config.pathway_state_edit.existing_pathway_name
    year = config.pathway_state_edit.year_of_state
    payload = update_year_yaml(
        config,
        pathway_name,
        year,
        raw_yaml=config.pathway_state_edit.raw_yaml,
    )
    print_pathway_action_output(payload)
    return payload


if __name__ == "__main__":
    main(Configuration())

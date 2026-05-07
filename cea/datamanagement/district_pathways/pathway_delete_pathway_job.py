"""Native dashboard job entry point for deleting one district pathway."""

from cea.config import Configuration
from cea.datamanagement.district_pathways.job_output import print_pathway_action_output
from cea.datamanagement.district_pathways.pathway_timeline import delete_pathway


def main(config: Configuration) -> dict:
    pathway_name = config.pathway_state_workflow.existing_pathway_name
    payload = delete_pathway(config, pathway_name)
    print_pathway_action_output(payload)
    return payload


if __name__ == "__main__":
    main(Configuration())

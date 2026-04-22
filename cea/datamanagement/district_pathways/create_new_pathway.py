"""Step 0: Create a district evolution pathway."""

from cea.config import Configuration
from cea.datamanagement.district_pathways.job_output import print_pathway_action_output
from cea.datamanagement.district_pathways.pathway_timeline import create_pathway


def main(config: Configuration) -> None:
    pathway_name = config.create_new_pathway.new_pathway_name
    if not pathway_name:
        raise ValueError("Provide a new pathway name before starting this job.")

    payload = create_pathway(config, pathway_name)
    payload["message"] = f"Created pathway '{payload['pathway_name']}'."
    payload["messages"] = [
        "The pathway is ready for template definition, year edits, baking, and simulation.",
    ]
    print_pathway_action_output(payload)


if __name__ == '__main__':
    main(Configuration())

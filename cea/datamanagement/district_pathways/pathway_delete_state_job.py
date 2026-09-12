"""Native dashboard job entry point for clearing one pathway state year's data."""

from cea.config import Configuration
from cea.datamanagement.district_pathways.job_output import print_pathway_action_output
from cea.datamanagement.district_pathways.pathway_timeline import clear_state


def main(config: Configuration) -> dict:
    """CLI/job entry point: clear the selected pathway's selected state year (`clear_state`)
    using the `[pathway-state-edit]` config section, and log the result to Job Info."""
    names = config.pathway_state_edit.existing_pathway_names or []
    if not names:
        raise ValueError("Select an existing pathway before deleting a state year.")
    pathway_name = names[0]
    year = config.pathway_state_edit.year_of_state
    if year is None:
        raise ValueError("Provide a state year before deleting.")
    payload = clear_state(
        config,
        pathway_name,
        year,
        delete_inputs=config.pathway_state_edit.delete_inputs,
        delete_outputs=config.pathway_state_edit.delete_outputs,
    )
    print_pathway_action_output(payload)
    return payload


if __name__ == "__main__":
    main(Configuration())

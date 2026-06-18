"""Native dashboard job entry point for validating one baked pathway year."""

from cea.config import Configuration
from cea.datamanagement.district_pathways.job_output import print_pathway_action_output
from cea.datamanagement.district_pathways.pathway_timeline import validate_baked_state


def main(config: Configuration) -> dict:
    names = config.pathway_state_edit.existing_pathway_names or []
    if not names:
        raise ValueError("Select an existing pathway before validating state.")
    pathway_name = names[0]
    year = config.pathway_state_edit.year_of_state
    if year is None:
        raise ValueError("Provide a state year before validating.")
    payload = validate_baked_state(config, pathway_name, year)
    print_pathway_action_output(payload)
    if not payload.get("is_valid", True):
        raise ValueError(payload["message"])
    return payload


if __name__ == "__main__":
    main(Configuration())

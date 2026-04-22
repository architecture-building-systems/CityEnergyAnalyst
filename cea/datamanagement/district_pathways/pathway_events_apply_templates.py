"""Apply intervention templates to a specific year across one or more district evolution pathways."""
from cea.config import Configuration
from cea.datamanagement.district_pathways.job_output import print_pathway_action_output
from cea.datamanagement.district_pathways.pathway_timeline import apply_templates_to_year


def main(config: Configuration) -> None:
    """Apply selected intervention templates to a specific year across selected pathways."""
    pathway_names = config.pathway_events_apply_templates.existing_pathway_names

    if not pathway_names:
        raise ValueError(
            "No pathways selected. Please select at least one pathway."
        )

    year_of_state = config.pathway_events_apply_templates.year_of_state
    intervention_templates = (
        config.pathway_events_apply_templates.intervention_templates
    )

    if not year_of_state:
        raise ValueError("Year is required. Please specify which year to apply the pathway event to.")

    if not intervention_templates:
        raise ValueError(
            "No intervention templates selected. Please select at least one intervention template to apply."
        )

    for pathway_name in pathway_names:
        print(f"\n--- Applying to pathway '{pathway_name}' ---", flush=True)
        payload = apply_templates_to_year(
            config,
            pathway_name,
            year_of_state,
            template_names=intervention_templates,
        )
        print_pathway_action_output(payload)

    print(
        f"\nApplied intervention templates to {len(pathway_names)} pathway(s).",
        flush=True,
    )


if __name__ == '__main__':
    main(Configuration())

"""Apply intervention templates to a specific year in a district evolution pathway."""
from cea.config import Configuration
from cea.datamanagement.district_pathways.job_output import print_pathway_action_output
from cea.datamanagement.district_pathways.pathway_timeline import apply_templates_to_year


def main(config: Configuration) -> None:
    """Apply selected intervention templates to a specific year."""
    pathway_name = config.pathway_events_apply_templates.existing_pathway_name
    
    if not pathway_name:
        raise ValueError(
            "No pathway selected. Please complete Step 0 (Select Pathway) first:\n"
            "1. Go to 'Step 0: Create District Evolution Pathway'\n"
            "2. Select or create a pathway\n"
            "3. Return to this step and run it for the selected pathway"
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

    payload = apply_templates_to_year(
        config,
        pathway_name,
        year_of_state,
        template_names=intervention_templates,
    )
    print_pathway_action_output(payload)
    print("Next step: Use Step 3 (Bake Pathway States) to materialise state folders from the log.", flush=True)


if __name__ == '__main__':
    main(Configuration())

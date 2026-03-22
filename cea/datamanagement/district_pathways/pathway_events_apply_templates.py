"""Apply intervention templates to a specific year in a district evolution pathway."""
from cea.config import Configuration
from cea.datamanagement.district_pathways.intervention_templates import (
    resolve_intervention_templates_to_recipe,
)
from cea.datamanagement.district_pathways.pathway_state import (
    DistrictEvolutionPathway,
)


def main(config: Configuration) -> None:
    """Apply selected intervention templates to a specific year."""
    pathway_name = config.pathway_events_apply_templates.existing_pathway_name
    
    if not pathway_name:
        raise ValueError(
            "No pathway selected. Please complete Step 0 (Select Pathway) first:\n"
            "1. Go to 'Step 0: Create District Evolution Pathway'\n"
            "2. Select or create a pathway\n"
            "3. Click 'Save Settings'\n"
            "4. Then return to this step"
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
    
    print(
        f"Applying {len(intervention_templates)} intervention template(s) to year {year_of_state} in pathway '{pathway_name}'..."
    )
    
    # Resolve intervention templates to a single merged recipe for this pathway event.
    pathway = DistrictEvolutionPathway(config, pathway_name)
    try:
        merged_recipe = resolve_intervention_templates_to_recipe(
            locator=pathway.main_locator,
            pathway_name=pathway_name,
            template_names=intervention_templates,
        )
    except ValueError as e:
        print(f"Error: {e}")
        raise
    
    # Update the YAML log file only (does not materialise state folders)
    pathway.apply_year_modifications(year_of_state, merged_recipe)
    pathway.save()
    
    print(f"Successfully updated the pathway log for year {year_of_state}")
    print(f"Applied intervention templates: {', '.join(intervention_templates)}")
    print(
        f"Log file: {pathway.main_locator.get_district_pathway_log_file(pathway_name)}"
    )
    print("\nNext step: Use Step 3 (Bake Pathway States) to materialise state folders from the log.")


if __name__ == '__main__':
    main(Configuration())

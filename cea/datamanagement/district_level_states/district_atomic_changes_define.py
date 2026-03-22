"""Define intervention templates for district evolution pathways."""
from cea.config import Configuration
from cea.datamanagement.district_level_states.atomic_changes import (
    add_or_update_intervention_template,
)
from cea.datamanagement.district_level_states.state_scenario import create_modify_recipe


def main(config: Configuration) -> None:
    """Define or update an intervention template."""
    pathway_name = config.pathway_intervention_templates_define.existing_pathway_name
    
    if not pathway_name:
        raise ValueError(
            "No pathway selected. Please complete Step 0 (Select Pathway) first:\n"
            "1. Go to 'Step 0: Create District Evolution Pathway'\n"
            "2. Select or create a pathway\n"
            "3. Click 'Save Settings'\n"
            "4. Then return to this step"
        )
    
    template_name = (
        config.pathway_intervention_templates_define.intervention_template_name
    )
    description = (
        config.pathway_intervention_templates_define.intervention_template_description
    )
    
    if not template_name:
        raise ValueError("Intervention template name is required.")
    
    # Use the existing create_modify_recipe function to build the modifications
    # This reuses all the existing UI for defining building modifications
    modifications = create_modify_recipe(
        config,
        config_section_name='pathway_intervention_templates_define',
    )
    
    if not modifications:
        raise ValueError("No modifications defined. Please configure at least one modification.")
    
    add_or_update_intervention_template(
        config=config,
        pathway_name=pathway_name,
        template_name=template_name,
        description=description or f"Intervention template: {template_name}",
        modifications=modifications,
    )
    
    print(
        f"Successfully saved intervention template '{template_name}' to pathway '{pathway_name}'"
    )


if __name__ == '__main__':
    main(Configuration())

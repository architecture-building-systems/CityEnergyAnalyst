"""Define intervention templates for a scenario."""
from cea.config import Configuration
from cea.datamanagement.district_pathways.intervention_templates import (
    add_or_update_intervention_template,
)
from cea.datamanagement.district_pathways.pathway_state import create_modify_recipe


def main(config: Configuration) -> None:
    """Define or update an intervention template."""
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
        template_name=template_name,
        description=description or f"Intervention template: {template_name}",
        modifications=modifications,
    )

    print(
        f"Successfully saved intervention template '{template_name}'."
    )


if __name__ == '__main__':
    main(Configuration())

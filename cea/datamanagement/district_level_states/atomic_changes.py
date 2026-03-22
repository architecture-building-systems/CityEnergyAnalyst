"""Manage intervention-template definitions for district evolution pathways."""
import os
from typing import Any

import yaml

from cea.config import Configuration
from cea.inputlocator import InputLocator


class _NoAliasSafeDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:  # noqa: ANN401
        return True


def load_intervention_templates(
    locator: InputLocator,
    *,
    pathway_name: str,
    allow_missing: bool = False,
) -> dict[str, dict[str, Any]]:
    """
    Load intervention templates from YAML file.
    
    Returns:
        dict mapping template_name -> {description: str, modifications: ModifyRecipe}
    """
    yml_path = locator.get_district_pathway_intervention_templates_file(pathway_name)
    if not os.path.exists(yml_path):
        if allow_missing:
            return {}
        raise FileNotFoundError(
            f"Intervention-template file '{yml_path}' does not exist. Create it first."
        )
    
    with open(yml_path, 'r') as f:
        data: Any = yaml.safe_load(f) or {}
    
    if not isinstance(data, dict):
        raise ValueError(
            f"Intervention-template file '{yml_path}' must contain a YAML mapping at the top level."
        )
    
    return data


def save_intervention_templates(
    locator: InputLocator,
    intervention_templates: dict[str, dict[str, Any]],
    *,
    pathway_name: str,
) -> None:
    """Save intervention templates to YAML file."""
    yml_path = locator.get_district_pathway_intervention_templates_file(pathway_name)
    os.makedirs(os.path.dirname(yml_path), exist_ok=True)
    
    with open(yml_path, 'w') as f:
        yaml.dump(
            intervention_templates,
            f,
            Dumper=_NoAliasSafeDumper,
            sort_keys=True,
            default_flow_style=False,
        )


def add_or_update_intervention_template(
    config: Configuration,
    pathway_name: str,
    template_name: str,
    description: str,
    modifications: dict[str, dict[str, dict[str, Any]]],
) -> None:
    """Add or update an intervention-template definition."""
    locator = InputLocator(config.scenario)
    intervention_templates = load_intervention_templates(
        locator,
        pathway_name=pathway_name,
        allow_missing=True,
    )
    
    intervention_templates[template_name] = {
        'description': description,
        'modifications': modifications,
    }
    
    save_intervention_templates(
        locator,
        intervention_templates,
        pathway_name=pathway_name,
    )
    print(
        f"Intervention template '{template_name}' saved to pathway '{pathway_name}'"
    )


def delete_intervention_template(
    config: Configuration,
    pathway_name: str,
    template_name: str,
) -> None:
    """Delete an intervention-template definition."""
    locator = InputLocator(config.scenario)
    intervention_templates = load_intervention_templates(
        locator,
        pathway_name=pathway_name,
    )
    
    if template_name not in intervention_templates:
        raise ValueError(
            f"Intervention template '{template_name}' does not exist in pathway '{pathway_name}'"
        )
    
    del intervention_templates[template_name]
    save_intervention_templates(
        locator,
        intervention_templates,
        pathway_name=pathway_name,
    )
    print(
        f"Intervention template '{template_name}' deleted from pathway '{pathway_name}'"
    )


def get_intervention_template_names(
    locator: InputLocator,
    pathway_name: str,
) -> list[str]:
    """Get the list of intervention-template names in a pathway."""
    intervention_templates = load_intervention_templates(
        locator,
        pathway_name=pathway_name,
        allow_missing=True,
    )
    return sorted(intervention_templates.keys())


def resolve_intervention_templates_to_recipe(
    locator: InputLocator,
    pathway_name: str,
    template_names: list[str],
) -> dict[str, dict[str, dict[str, Any]]]:
    """
    Resolve a list of intervention-template names into a merged ModifyRecipe.
    Raises ValueError if there are conflicts.
    """
    from cea.datamanagement.district_level_states.conflict_detector import (
        detect_intervention_template_conflicts,
    )
    
    intervention_templates = load_intervention_templates(
        locator,
        pathway_name=pathway_name,
    )
    
    # Check all requested changes exist
    missing = [
        name for name in template_names if name not in intervention_templates
    ]
    if missing:
        raise ValueError(
            f"Intervention templates not found in pathway '{pathway_name}': {', '.join(missing)}"
        )
    
    # Check for conflicts
    conflicts = detect_intervention_template_conflicts(
        template_names,
        intervention_templates,
    )
    if conflicts:
        raise ValueError(
            "Cannot apply intervention templates due to conflicts:\n"
            + "\n".join(f"  - {c}" for c in conflicts)
        )
    
    # Merge modifications
    merged_recipe: dict[str, dict[str, dict[str, Any]]] = {}
    for template_name in template_names:
        modifications = intervention_templates[template_name]['modifications']
        for building, components in modifications.items():
            if building not in merged_recipe:
                merged_recipe[building] = {}
            for component, fields in components.items():
                if component not in merged_recipe[building]:
                    merged_recipe[building][component] = {}
                merged_recipe[building][component].update(fields)
    
    return merged_recipe

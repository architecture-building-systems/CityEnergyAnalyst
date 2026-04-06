"""Manage intervention-template definitions for a scenario."""
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
    allow_missing: bool = False,
) -> dict[str, dict[str, Any]]:
    """
    Load intervention templates from the scenario-level YAML file.

    Returns:
        dict mapping template_name -> {description: str, modifications: ModifyRecipe}
    """
    yml_path = locator.get_intervention_templates_file()
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
) -> None:
    """Save intervention templates to the scenario-level YAML file."""
    yml_path = locator.get_intervention_templates_file()
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
    template_name: str,
    description: str,
    modifications: dict[str, dict[str, dict[str, Any]]],
) -> None:
    """Add or update an intervention-template definition."""
    locator = InputLocator(config.scenario)
    intervention_templates = load_intervention_templates(
        locator,
        allow_missing=True,
    )

    intervention_templates[template_name] = {
        'description': description,
        'modifications': modifications,
    }

    save_intervention_templates(
        locator,
        intervention_templates,
    )
    print(
        f"Intervention template '{template_name}' saved."
    )


def delete_intervention_template(
    config: Configuration,
    template_name: str,
) -> None:
    """Delete an intervention-template definition."""
    locator = InputLocator(config.scenario)
    intervention_templates = load_intervention_templates(
        locator,
    )

    if template_name not in intervention_templates:
        raise ValueError(
            f"Intervention template '{template_name}' does not exist."
        )

    del intervention_templates[template_name]
    save_intervention_templates(
        locator,
        intervention_templates,
    )
    print(
        f"Intervention template '{template_name}' deleted."
    )


def get_intervention_template_names(
    locator: InputLocator,
) -> list[str]:
    """Get the list of intervention-template names for the scenario."""
    intervention_templates = load_intervention_templates(
        locator,
        allow_missing=True,
    )
    return sorted(intervention_templates.keys())


def resolve_intervention_templates_to_recipe(
    locator: InputLocator,
    template_names: list[str],
) -> dict[str, dict[str, dict[str, Any]]]:
    """
    Resolve a list of intervention-template names into a merged ModifyRecipe.
    Raises ValueError if there are conflicts.
    """
    from cea.datamanagement.district_pathways.intervention_template_conflicts import (
        detect_intervention_template_conflicts,
    )

    intervention_templates = load_intervention_templates(
        locator,
    )

    # Check all requested changes exist
    missing = [
        name for name in template_names if name not in intervention_templates
    ]
    if missing:
        raise ValueError(
            f"Intervention templates not found: {', '.join(missing)}"
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

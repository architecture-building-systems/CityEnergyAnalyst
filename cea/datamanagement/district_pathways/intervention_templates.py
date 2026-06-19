"""Manage intervention-template definitions for a scenario."""
import os
from typing import Any

import yaml

from cea.config import Configuration
from cea.datamanagement.district_pathways.envelope_topology import (
    validate_recipe_against_envelope,
)
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

    # Pre-flight: catch incomplete material interventions against direct-property source rows
    # *before* persisting the template, so the user discovers the issue at define time rather
    # than later when the pathway state is baked. The same rule is re-enforced at apply time
    # in pathway_state._apply_state_construction_changes against the state's database.
    recipe_errors = validate_recipe_against_envelope(locator, modifications)
    if recipe_errors:
        raise ValueError(
            f"Intervention template '{template_name}' cannot be saved:\n"
            + "\n".join(f"  - {e}" for e in recipe_errors)
        )

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


def _recipe_is_subset(sub: dict[str, Any], sup: dict[str, Any]) -> bool:
    """True if every archetype/component/field/value in `sub` also appears in `sup`."""
    for archetype, components in (sub or {}).items():
        sup_components = sup.get(archetype)
        if not isinstance(sup_components, dict):
            return False
        for component, fields in (components or {}).items():
            sup_fields = sup_components.get(component)
            if not isinstance(sup_fields, dict):
                return False
            for field, value in (fields or {}).items():
                if sup_fields.get(field) != value:
                    return False
    return True


def find_template_usage(
    config: Configuration,
    template_name: str,
) -> list[dict[str, Any]]:
    """Best-effort scan of every pathway log for years that contain this template's changes.

    Applying a template copies its modifications into the year with no stored link back to the
    template, so this is a structural subset match — not a guaranteed reference. It can miss
    usage when the template was edited after being applied, or when the year's changes were
    later overwritten/merged. Returns a list of ``{'pathway': str, 'year': int}``.
    """
    # Imported lazily to avoid an import cycle (pathway_timeline imports this module).
    from cea.datamanagement.district_pathways.pathway_timeline import list_pathway_names
    from cea.datamanagement.district_pathways.pathway_log import load_pathway_log_yaml

    locator = InputLocator(config.scenario)
    entry = load_intervention_templates(locator, allow_missing=True).get(template_name)
    template_mods = (entry or {}).get("modifications", {}) or {}
    if not template_mods:
        return []

    usage: list[dict[str, Any]] = []
    for pathway_name in list_pathway_names(config):
        try:
            log = load_pathway_log_yaml(
                locator, pathway_name=pathway_name, allow_missing=True, allow_empty=True
            )
        except Exception:
            continue  # A malformed/unreadable log must never block deletion.
        for year in sorted(log.keys()):
            year_mods = (log.get(year, {}) or {}).get("modifications", {}) or {}
            if _recipe_is_subset(template_mods, year_mods):
                usage.append({"pathway": pathway_name, "year": int(year)})
    return usage


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

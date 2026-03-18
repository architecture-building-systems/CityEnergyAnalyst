"""
Manage atomic change definitions for district timelines.
Atomic changes are reusable modification templates that can be applied to specific years.
"""
import os
from typing import Any

import yaml

from cea.config import Configuration
from cea.inputlocator import InputLocator


class _NoAliasSafeDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:  # noqa: ANN401
        return True


def load_atomic_changes(
    locator: InputLocator,
    *,
    timeline_name: str,
    allow_missing: bool = False,
) -> dict[str, dict[str, Any]]:
    """
    Load atomic changes from YAML file.
    
    Returns:
        dict mapping change_name -> {description: str, modifications: ModifyRecipe}
    """
    yml_path = locator.get_district_timeline_atomic_changes_file(timeline_name)
    if not os.path.exists(yml_path):
        if allow_missing:
            return {}
        raise FileNotFoundError(
            f"Atomic changes file '{yml_path}' does not exist. Create it first."
        )
    
    with open(yml_path, 'r') as f:
        data: Any = yaml.safe_load(f) or {}
    
    if not isinstance(data, dict):
        raise ValueError(
            f"Atomic changes file '{yml_path}' must contain a YAML mapping at the top level."
        )
    
    return data


def save_atomic_changes(
    locator: InputLocator,
    atomic_changes: dict[str, dict[str, Any]],
    *,
    timeline_name: str,
) -> None:
    """Save atomic changes to YAML file."""
    yml_path = locator.get_district_timeline_atomic_changes_file(timeline_name)
    os.makedirs(os.path.dirname(yml_path), exist_ok=True)
    
    with open(yml_path, 'w') as f:
        yaml.dump(
            atomic_changes,
            f,
            Dumper=_NoAliasSafeDumper,
            sort_keys=True,
            default_flow_style=False,
        )


def add_or_update_atomic_change(
    config: Configuration,
    timeline_name: str,
    change_name: str,
    description: str,
    modifications: dict[str, dict[str, dict[str, Any]]],
) -> None:
    """
    Add or update an atomic change definition.
    
    Args:
        config: CEA configuration
        timeline_name: Name of the timeline
        change_name: Unique identifier for this atomic change
        description: Human-readable description
        modifications: ModifyRecipe dict {building: {component: {field: value}}}
    """
    locator = InputLocator(config.scenario)
    atomic_changes = load_atomic_changes(locator, timeline_name=timeline_name, allow_missing=True)
    
    atomic_changes[change_name] = {
        'description': description,
        'modifications': modifications,
    }
    
    save_atomic_changes(locator, atomic_changes, timeline_name=timeline_name)
    print(f"Atomic change '{change_name}' saved to timeline '{timeline_name}'")


def delete_atomic_change(
    config: Configuration,
    timeline_name: str,
    change_name: str,
) -> None:
    """Delete an atomic change definition."""
    locator = InputLocator(config.scenario)
    atomic_changes = load_atomic_changes(locator, timeline_name=timeline_name)
    
    if change_name not in atomic_changes:
        raise ValueError(f"Atomic change '{change_name}' does not exist in timeline '{timeline_name}'")
    
    del atomic_changes[change_name]
    save_atomic_changes(locator, atomic_changes, timeline_name=timeline_name)
    print(f"Atomic change '{change_name}' deleted from timeline '{timeline_name}'")


def get_atomic_change_names(locator: InputLocator, timeline_name: str) -> list[str]:
    """Get list of all atomic change names in a timeline."""
    atomic_changes = load_atomic_changes(locator, timeline_name=timeline_name, allow_missing=True)
    return sorted(atomic_changes.keys())


def resolve_atomic_changes_to_recipe(
    locator: InputLocator,
    timeline_name: str,
    change_names: list[str],
) -> dict[str, dict[str, dict[str, Any]]]:
    """
    Resolve a list of atomic change names into a merged ModifyRecipe.
    Raises ValueError if there are conflicts.
    """
    from cea.datamanagement.district_level_states.conflict_detector import detect_conflicts
    
    atomic_changes = load_atomic_changes(locator, timeline_name=timeline_name)
    
    # Check all requested changes exist
    missing = [name for name in change_names if name not in atomic_changes]
    if missing:
        raise ValueError(
            f"Atomic changes not found in timeline '{timeline_name}': {', '.join(missing)}"
        )
    
    # Check for conflicts
    conflicts = detect_conflicts(change_names, atomic_changes)
    if conflicts:
        raise ValueError(
            "Cannot apply atomic changes due to conflicts:\n" + "\n".join(f"  - {c}" for c in conflicts)
        )
    
    # Merge modifications
    merged_recipe: dict[str, dict[str, dict[str, Any]]] = {}
    for change_name in change_names:
        modifications = atomic_changes[change_name]['modifications']
        for building, components in modifications.items():
            if building not in merged_recipe:
                merged_recipe[building] = {}
            for component, fields in components.items():
                if component not in merged_recipe[building]:
                    merged_recipe[building][component] = {}
                merged_recipe[building][component].update(fields)
    
    return merged_recipe

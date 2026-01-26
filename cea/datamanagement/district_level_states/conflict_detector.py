"""
Detect conflicts when applying multiple atomic changes.
A conflict occurs when two or more atomic changes modify the same field
of the same component in the same building.
"""
from typing import Any


def detect_conflicts(
    change_names: list[str],
    atomic_changes: dict[str, dict[str, Any]],
) -> list[str]:
    """
    Detect conflicts between atomic changes.
    
    Args:
        change_names: List of atomic change names to check
        atomic_changes: Dict of all atomic change definitions
    
    Returns:
        List of conflict descriptions (empty if no conflicts)
    """
    # Map: (building, component, field) -> list of change names that modify it
    field_map: dict[tuple[str, str, str], list[str]] = {}
    
    for change_name in change_names:
        if change_name not in atomic_changes:
            continue
        
        modifications = atomic_changes[change_name].get('modifications', {})
        for building, components in modifications.items():
            for component, fields in components.items():
                for field in fields:
                    key = (building, component, field)
                    if key not in field_map:
                        field_map[key] = []
                    field_map[key].append(change_name)
    
    # Find conflicts (same field modified by 2+ changes)
    conflicts = []
    for (building, component, field), changes in field_map.items():
        if len(changes) > 1:
            conflicts.append(
                f"Field '{building}.{component}.{field}' modified by multiple changes: {', '.join(changes)}"
            )
    
    return sorted(conflicts)

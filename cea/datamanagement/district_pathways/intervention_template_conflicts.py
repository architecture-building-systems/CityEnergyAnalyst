"""Detect conflicts when applying multiple intervention templates."""
from typing import Any


def detect_intervention_template_conflicts(
    template_names: list[str],
    intervention_templates: dict[str, dict[str, Any]],
) -> list[str]:
    """Detect conflicts between intervention templates."""
    # Map: (building, component, field) -> list of template names that modify it
    field_map: dict[tuple[str, str, str], list[str]] = {}
    
    for template_name in template_names:
        if template_name not in intervention_templates:
            continue
        
        modifications = intervention_templates[template_name].get('modifications', {})
        for building, components in modifications.items():
            for component, fields in components.items():
                for field in fields:
                    key = (building, component, field)
                    if key not in field_map:
                        field_map[key] = []
                    field_map[key].append(template_name)
    
    # Find conflicts where the same field is modified by two or more templates.
    conflicts = []
    for (building, component, field), templates in field_map.items():
        if len(templates) > 1:
            conflicts.append(
                f"Field '{building}.{component}.{field}' modified by multiple templates: {', '.join(templates)}"
            )
    
    return sorted(conflicts)

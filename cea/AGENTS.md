# CEA Core

## Main API
- `InputLocator` - Canonical path resolver for scenarios, databases, district pathways, and `state_status/` sidecars.
- `Configuration` - Typed config access for scripts and dashboard routes.
- `cea.api.<script_name>(...)` - Programmatic script entry points.
- `Parameter.decode(value) -> Any` - Lenient config-file parsing.
- `Parameter.encode(value) -> str` - Strict validation before saving.

## Key Patterns
### DO: Use `InputLocator` for all scenario-relative paths
```python
locator = InputLocator(config.scenario)
state_file = locator.get_district_pathway_state_status_file("demo", 2030)
```
- `Parameter.decode(value: str) → Any` - Parse value from config file (lenient)
- `Parameter.encode(value: Any) → str` - Validate value before saving (strict)
- `ChoiceParameterBase._choices → list[str]` - Available options (can be dynamic via `@property`)
- Use `isinstance(..., ChoiceParameter)` vs `isinstance(..., MultiChoiceParameter)` for choice cardinality

### DO: Keep config decode/encode responsibilities separate
```python
def decode(self, value):
    return value.strip()

def encode(self, value):
    if not value.strip():
        raise ValueError("Value required")
    return value.strip()
```

### DO: Regenerate `config.pyi` after changing config parameters
```bash
pixi run python cea/utilities/config_type_generator.py
```

### DO: Use dedicated config sections for plot scripts
```text
plot-pathway-emission-timeline -> plots-pathway-emission-timeline
```

### DO: Add scripts to `scripts.yml` even for dashboard-only job launches
```text
pathway-save-yaml -> cea.datamanagement.district_pathways.pathway_save_yaml_job
pathway-delete-pathway -> cea.datamanagement.district_pathways.pathway_delete_pathway_job
interfaces: [cli]
```

### DON'T: Hardcode scenario or database paths
```python
# Bad: os.path.join(config.scenario, "inputs", ...)
```

## Related Files
- `inputlocator.py` - Scenario and district-pathway path helpers.
- `config.py` - Parameter classes and configuration model.
- `config.pyi` - Generated typing stub for config sections.
- `default.config` - User-facing defaults and help text.
- `scripts.yml` - Script registry and interface metadata.

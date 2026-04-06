# CEA Source

## Core Architecture

**Scenario-Based Workflow**: Work organised around scenarios (folders with `/inputs/`, `/outputs/`)

**Key Components**:
- `InputLocator` (`inputlocator.py`) - File path resolution for scenarios
- `Configuration` (`config.py`) - Typed parameters (PathParameter, BooleanParameter, etc.)
- `scripts.yml` - Script registry with metadata

## Key Patterns

### Adding a New Script
1. Create `cea/<module>/script.py` with `main(config: Configuration)`
2. Add entry to `scripts.yml`

### Using Core APIs

```python
# InputLocator - always use for file paths
from cea.inputlocator import InputLocator
locator = InputLocator(config.scenario)
path = locator.get_zone_geometry()

# Configuration
from cea.config import Configuration
config = Configuration()
scenario = config.scenario
```

## Writing Conventions

**No emoticons in code**: Never add emoji or emoticons to code files, comments, or print statements.

**Physics function docstrings**: When writing physics-based functions (hydraulics, heat transfer, thermodynamics, fluid properties):
- **MUST follow** the docstring specification in `docs/developer/documenting-physics/docstring-specification.md`
- Verify standards citations are correct before referencing
- Include formulas with Unicode symbols
- All parameters and returns must have units in [square brackets]
- Use proper reference format: [Tag] Author (Year). Title. Journal, Volume, Pages

Common Pitfalls
- **File Paths**: Always use `InputLocator` methods, never hardcode
- **Test Location**: All test files in `cea/tests/` only
- **Config in Workers**: Don't modify `config` directly; use kwargs or create new instance
- **Multiprocessing**: Check `config.multiprocessing` before using `Pool`
- **British English**: Always use British English spelling
- **F-strings**: Only use f-strings when string contains variables (e.g., `f"Value: {x}"`).

# Configuration Parameters

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
python scripts/config_type_generator.py
```

## decode() vs encode()

`decode()` is called on every config load — keep it lenient (security checks only, no business rules or I/O). `encode()` is called on save — apply all validation there.

Use helpers to share security checks without duplicating:

```python
def _validate_security(self, value):
    """Security checks (used by encode AND decode)"""
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    if any(char in value for char in invalid_chars):
        raise ValueError("Invalid characters")

def _validate_business(self, value):
    """Business rules (used by encode ONLY)"""
    if self._resource_exists(value):
        raise ValueError("Already exists")

def decode(self, value):
    return self._validate_security(value.strip())

def encode(self, value):
    self._validate_security(value.strip())
    self._validate_business(value)
    return value
```

## Dynamic Choices

### DO: Use @property for dynamic choices

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

## Common Pitfalls

1. **Validating in decode()** → Fragile config loading
2. **No dependency declaration** → Dynamic choices don't update
3. **Caching without invalidation** → Stale options
4. **Mixing security/business validation** → Security checks in both, business in encode only

## Related Files

- `inputlocator.py` - Scenario and district-pathway path helpers.
- `config.py` - All parameter classes (PathParameter, ChoiceParameter, etc.)
- `config.pyi` - Type stubs (regenerate: `pixi run python scripts/config_type_generator.py`)
- `default.config` - Default values for all parameters
- `scripts.yml` - Script registry and interface metadata.
- `interfaces/dashboard/api/tools.py` - Validation API endpoints (`validate_field`, `get_parameter_metadata`)


## Module Documentation

- `databases/AGENTS.md` - Database structure, COMPONENTS vs ASSEMBLIES
- `analysis/costs/AGENTS.md` - Cost calculations, 4-case logic, 3-level fallback
- `analysis/heat/AGENTS.md` - Heat rejection (mirrors cost architecture)
- `demand/AGENTS.md` - Demand simulation, HVAC vs SUPPLY
- `interfaces/dashboard/AGENTS.md` - Job system, worker processes
- `technologies/network_layout/AGENTS.md` - Network connectivity

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

**Hard rules for decode()**:
- **Never substitute values**: return the stored value, `None` (nullable), or raise. Never fall back to `self._choices[0]` or "the most recent X" — silently running with a value the user didn't configure can change simulation results.
- **Never touch the disk**: no file writes, no writability probes (do those in `encode()` or the consuming script).

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

### DO: Keep parameter initialisation I/O-free
- Parameter `__init__` methods should not read files, scan directories, or load CSV/JSON.
- Class-level definitions in `config.py` should avoid filesystem access at import time.
- Use lazy properties/helpers for filesystem-backed choices and resolve them only when needed.

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

## Frontend vs Backend: Decide the Layer First

User requests are often phrased in UI terms ("the dropdown should show…", "default to the most recent…", "when nothing is selected…"). **Do not translate UI phrasing directly into `config.py` changes.** Before editing, decide which layer owns the behaviour:

| Concern | Owner |
|---|---|
| Value storage, types, validation, available choices (data) | `config.py` parameter classes |
| GUI payload normalisation, form metadata, pre-selection/fallback for forms | `interfaces/dashboard/api/tools.py` |
| Widgets, display labels, placeholders ("Nothing Selected"), ordering/presentation | `CityEnergyAnalyst-GUI` repo |

Rules of thumb:
- A "default shown in the form" is API/frontend behaviour — not a `decode()` fallback. Config stores what the user set; the form decides what to suggest.
- Placeholder/sentinel text the user sees must never become a value `config.py` parses or stores.
- If the request only changes what the user *sees* (labels, ordering, visibility), the change likely belongs entirely in the GUI repo — say so rather than approximating it in the backend.
- Remember `config.py` serves the CLI and `cea.api` too: any behaviour added for the dashboard's benefit must still make sense for a headless `cea` run.

## Writing Parameter Classes

- **Reuse before writing**: check `config.py` for an existing class/mixin first (e.g. `validate_filesystem_name`-style checks, `ColumnChoicesMixin`, `SubfolderChoiceParameter`). Never copy-paste an `invalid_chars` block or a near-identical class with a different noun in the error message.
- **Errors via `logging`, never `print()`**
- **No bare `except Exception: return []` in `_choices`**: catch the expected errors (`OSError`, `FileNotFoundError`, `KeyError`) and `logger.warning` anything caught — a typo'd locator method must not present as "no options available".
- **One null sentinel**: `''` on disk, `None` decoded. No new magic strings (`'(none)'`, `'null'`, `'Nothing Selected'`).
- **GUI payloads normalise at the API boundary** (`interfaces/dashboard/api/tools.py`), not inside `encode()` — no `isinstance(value, list)` unwrapping in parameter classes.
- **No second init path**: read dotted metadata options in `__init__`; don't add new `initialize(parser)` hooks.
- **No hardcoded section names**: cross-parameter checks like `getattr(config.network_layout, ...)` tie a class to one section — put script-level validation in `tools.py::check_tool_inputs` instead.
- **Write real docstrings**: don't copy one from a neighbouring class.

## Common Pitfalls

1. **Validating in decode()** → Fragile config loading
2. **No dependency declaration** → Dynamic choices don't update
3. **Caching without invalidation** → Stale options
4. **Mixing security/business validation** → Security checks in both, business in encode only
5. **Silent fallback in decode()** → Script runs with a value the user never set
6. **I/O at import or in `__init__`** → Every `Configuration()` (185 call sites) pays the cost

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

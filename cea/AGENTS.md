# Configuration Parameters

## Main API

- `Parameter.decode(value: str) → Any` - Parse value from config file (lenient)
- `Parameter.encode(value: Any) → str` - Validate value before saving (strict)
- `ChoiceParameter._choices → list[str]` - Available options (can be dynamic via `@property`)

## After Modifying config.py

**IMPORTANT**: After ANY changes to `config.py`, you MUST regenerate the type stub:

```bash
pixi run python cea/utilities/config_type_generator.py
```

This updates `config.pyi` with correct type hints for IDE autocompletion and type checking.

## Key Pattern: decode() vs encode()

### ✅ DO: Separate parsing from validation

```python
class MyParameter(Parameter):
    def decode(self, value):
        """Parse - security checks only"""
        if not value:
            return ""
        value = value.strip()

        # Only validate security concerns (path traversal, injection, etc.)
        if self._has_security_issue(value):
            raise ValueError("Security violation")

        return value  # Don't check business rules

    def encode(self, value):
        """Validate - all business rules"""
        if not value or not value.strip():
            raise ValueError("Value required")

        value = value.strip()

        # Security check
        if self._has_security_issue(value):
            raise ValueError("Security violation")

        # Business rule check
        if self._resource_exists(value):
            raise ValueError(f"Resource '{value}' already exists")

        return value
```

### ❌ DON'T: Validate business rules in decode()

```python
def decode(self, value):
    # ❌ Expensive I/O on every config load
    if not self._resource_exists(value):
        raise ValueError("Resource not found")

    # ❌ Breaks loading old configs when resources deleted
    if self._check_collision(value):
        raise ValueError("Already exists")

    return value
```

**Why**: decode() is called when loading config files - must be lenient and fast.

## Dynamic Choices

### ✅ DO: Use @property for dynamic choices

```python
class DynamicChoiceParameter(ChoiceParameter):
    def initialize(self, parser):
        self.depends_on = ['other-param']  # Declare dependencies

    @property
    def _choices(self):
        """Scan resources on each access"""
        return self._get_available_options()

    def _get_available_options(self):
        # Scan filesystem/database for available options
        if not self._can_scan():
            return []

        # Return list of valid choices
        return self._scan_resources()
```

## Validation Helpers

Extract shared validation into helpers:

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

## Common Pitfalls

1. **Validating in decode()** → Fragile config loading
2. **No dependency declaration** → Dynamic choices don't update
3. **Caching without invalidation** → Stale options
4. **Mixing security/business validation** → Security checks in both, business in encode only

## Related Files

- `config.py` - All parameter classes (PathParameter, ChoiceParameter, etc.)
- `config.pyi` - Type stubs (regenerate: `pixi run python cea/utilities/config_type_generator.py`)
- `default.config` - Default values for all parameters
- `interfaces/dashboard/api/tools.py` - Validation API endpoints (`validate_field`, `get_parameter_metadata`)

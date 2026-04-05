# Configuration Parameters

## Main API

- `Parameter.decode(value: str) → Any` - Parse value from config file (lenient)
- `Parameter.encode(value: Any) → str` - Validate value before saving (strict)
- `ChoiceParameterBase._choices → list[str]` - Available options (can be dynamic via `@property`)
- Use `isinstance(..., ChoiceParameter)` vs `isinstance(..., MultiChoiceParameter)` for choice cardinality

## After Modifying config.py

**IMPORTANT**: After ANY changes to `config.py`, you MUST regenerate the type stub:

```bash
python cea/utilities/config_type_generator.py
```

This updates `config.pyi` with correct type hints for IDE autocompletion and type checking.

## Common Pitfalls

1. **Validating in decode()** → Fragile config loading
2. **No dependency declaration** → Dynamic choices don't update
3. **Caching without invalidation** → Stale options
4. **Mixing security/business validation** → Security checks in both, business in encode only

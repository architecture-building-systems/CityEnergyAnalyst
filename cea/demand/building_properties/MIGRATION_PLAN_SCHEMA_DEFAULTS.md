# Migration Plan: Schema-Based Default Values (Option 3)

## Current State (Option 1 - Temporary Solution)

As of 2025-01-09, we implemented a temporary solution where default values for missing database fields are defined in the `DatabaseMapping` dataclass using the `field_defaults` parameter.

**Example:**
```python
DatabaseMapping(
    file_path=locator.get_database_assemblies_envelope_shading(),
    join_column='type_shade',
    fields=['rf_sh', 'shading_location', 'shading_setpoint_wm2'],
    field_defaults={
        'shading_location': 'interior',
        'shading_setpoint_wm2': 300
    }
)
```

**Location:**
- `cea/demand/building_properties/base.py` - DatabaseMapping dataclass
- `cea/demand/building_properties/building_envelope.py` - Shading defaults
- Future locations as more legacy fields are discovered

---

## Target State (Option 3 - Long-term Architecture)

Move default values to `schemas.yml` as the single source of truth for all data structure definitions.

### Benefits of Target State:
1. **Single Source of Truth**: All column metadata (type, description, constraints, defaults) in one place
2. **Better Tooling**: Documentation, validators, GUIs can all use defaults automatically
3. **Clearer Evolution**: Schema versioning shows when fields were added with what defaults
4. **Industry Standard**: Follows patterns from JSON Schema, OpenAPI, SQL DDL
5. **Better Separation**: Data structure concerns separate from application logic

---

## Migration Steps

### Phase 1: Add Default Support to schemas.yml ✅ (Completed in Option 1 Analysis)

**1.1 Update schemas.yml format**

Add `default` key to column definitions where needed:

```yaml
get_database_assemblies_envelope_shading:
  schema:
    columns:
      shading_location:
        description: Location of shading device ('interior' or 'exterior' only)
        type: string
        unit: '[-]'
        values: alphanumeric
        default: 'interior'  # ← NEW: Default for legacy databases

      shading_setpoint_wm2:
        description: Activation setpoint for shading in [W/m2]
        type: float
        unit: '[W/m2]'
        min: 0.0
        default: 300  # ← NEW: Default for legacy databases
```

**1.2 Document default policy**

Add to schemas.yml header:
```yaml
# Default Value Policy:
# - Defaults should be provided for fields added after initial release
# - Defaults enable backward compatibility with older database files
# - Defaults should represent safe, conservative values
# - Required fields without sensible defaults should not have defaults
```

---

### Phase 2: Update Schema Reading Infrastructure

**2.1 Extend `cea/schemas.py`**

Add utility function to extract defaults:

```python
def get_field_defaults(locator_method: str, schemas_dict: Dict = None) -> Dict[str, any]:
    """
    Extract default values for all columns in a schema.

    :param locator_method: Name of the locator method (e.g., 'get_database_assemblies_envelope_shading')
    :param schemas_dict: Optional pre-loaded schemas dictionary
    :return: Dictionary mapping column names to default values
    """
    if schemas_dict is None:
        schemas_dict = schemas()

    if locator_method not in schemas_dict:
        return {}

    schema_columns = schemas_dict[locator_method].get('schema', {}).get('columns', {})
    defaults = {}

    for column_name, column_info in schema_columns.items():
        if 'default' in column_info:
            defaults[column_name] = column_info['default']

    return defaults
```

**2.2 Add validation**

Ensure defaults match declared types:
```python
def validate_default_types(schemas_dict: Dict):
    """Validate that default values match declared column types"""
    # Implementation to check type consistency
    pass
```

---

### Phase 3: Update DatabaseMapping to Use Schema Defaults

**3.1 Modify `base.py` DatabaseMapping creation**

Add a factory method:

```python
@staticmethod
def from_schema(
    locator: InputLocator,
    building_properties_schema_name: str,
    join_column: str,
    fields: List[str],
    column_renames: Optional[Dict[str, str]] = None
) -> DatabaseMapping:
    """
    Create DatabaseMapping with defaults automatically loaded from schemas.yml.

    Example:
        >>> mapping = DatabaseMapping.from_schema(
        ...     locator,
        ...     'get_building_architecture',
        ...     'type_shade',
        ...     ['rf_sh', 'shading_location', 'shading_setpoint_wm2']
        ... )
    """
    from cea.schemas import schemas, get_field_defaults

    # Get database locator method from building properties schema
    schemas_dict = schemas()
    building_schema = schemas_dict[building_properties_schema_name]['schema']['columns']
    lookup_path = building_schema[join_column]['choice']['lookup']['path']

    # Get file path
    file_path = getattr(locator, lookup_path)()

    # Get defaults from schema
    field_defaults = get_field_defaults(lookup_path, schemas_dict)

    return DatabaseMapping(
        file_path=file_path,
        join_column=join_column,
        fields=fields,
        column_renames=column_renames,
        field_defaults=field_defaults if field_defaults else None
    )
```

**3.2 Update usage sites**

Replace manual DatabaseMapping creation:

```python
# OLD (Option 1 - temporary)
'envelope shading': DatabaseMapping(
    file_path=locator.get_database_assemblies_envelope_shading(),
    join_column='type_shade',
    fields=['rf_sh', 'shading_location', 'shading_setpoint_wm2'],
    field_defaults={'shading_location': 'interior', 'shading_setpoint_wm2': 300}
)

# NEW (Option 3 - from schema)
'envelope shading': DatabaseMapping.from_schema(
    locator,
    'get_building_architecture',
    'type_shade',
    ['rf_sh', 'shading_location', 'shading_setpoint_wm2']
)
```

---

### Phase 4: Systematic Schema Audit

**4.1 Identify all fields that need defaults**

Review database files for fields added after initial release:
- Check git history: `git log --all -- cea/databases/assemblies/`
- Interview domain experts about field evolution
- Check for other legacy handling code like `building_solar.py:121-138`

**4.2 Add defaults to schemas.yml**

For each identified field:
1. Determine appropriate default value (consult domain experts)
2. Add to schemas.yml with documentation
3. Add test case for legacy database handling

---

### Phase 5: Deprecate field_defaults Parameter

**5.1 Add deprecation warning**

```python
@dataclass
class DatabaseMapping:
    # ... existing fields ...
    field_defaults: Optional[Dict[str, any]] = None  # DEPRECATED: Use schemas.yml defaults

    def __post_init__(self):
        if self.field_defaults is not None:
            import warnings
            warnings.warn(
                "field_defaults parameter is deprecated. Define defaults in schemas.yml instead.",
                DeprecationWarning,
                stacklevel=2
            )
```

**5.2 Update documentation**

Mark as deprecated in docstrings and migration guide.

---

### Phase 6: Remove Temporary Code

After all usages migrated and tested:

1. Remove `field_defaults` parameter from DatabaseMapping
2. Remove fallback logic in `building_solar.py:121-138`
3. Update tests
4. Document in CHANGELOG

---

## Testing Strategy

### Unit Tests
```python
def test_schema_defaults_loaded():
    """Test that defaults are correctly loaded from schemas.yml"""
    from cea.schemas import get_field_defaults
    defaults = get_field_defaults('get_database_assemblies_envelope_shading')
    assert defaults['shading_location'] == 'interior'
    assert defaults['shading_setpoint_wm2'] == 300

def test_legacy_database_handling():
    """Test that old databases without new fields work correctly"""
    # Create test database without shading_location
    # Verify default is applied
    pass
```

### Integration Tests
```python
def test_building_envelope_with_legacy_database():
    """Test full workflow with legacy database files"""
    # Use fixture with old database format
    # Verify calculations complete successfully
    # Verify defaults were applied
    pass
```

---

## Rollback Plan

If issues arise during migration:

1. **Keep Option 1 code in place** until Option 3 is fully validated
2. **Feature flag**: Add config option to choose Option 1 vs Option 3
3. **Gradual migration**: Migrate one database at a time
4. **Monitoring**: Log when defaults are applied to detect issues

---

## Timeline Estimate

- **Phase 1**: 2-4 hours (add defaults to schemas.yml)
- **Phase 2**: 4-6 hours (extend schemas.py infrastructure)
- **Phase 3**: 3-4 hours (update DatabaseMapping)
- **Phase 4**: 8-16 hours (systematic audit - depends on number of fields)
- **Phase 5**: 2 hours (deprecation warnings)
- **Phase 6**: 2 hours (cleanup)

**Total: 21-34 hours** (approximately 3-5 days of development)

---

## Success Criteria

✅ All database fields have defaults defined in schemas.yml where appropriate
✅ Zero hardcoded default values in Python code
✅ Legacy databases work without errors
✅ All tests pass
✅ Documentation updated
✅ No deprecation warnings in test suite

---

## Related Files

- `cea/schemas.yml` - Target location for defaults
- `cea/schemas.py` - Schema reading infrastructure
- `cea/demand/building_properties/base.py` - DatabaseMapping implementation
- `cea/demand/building_properties/building_envelope.py` - Current usage
- `cea/demand/building_properties/building_solar.py` - Legacy handling example

---

## Questions for Discussion

1. Should we add schema version numbers to track evolution?
2. Should defaults be mandatory for all new fields going forward?
3. Do we need a migration tool to update user database files?
4. Should we validate that database CSV files match schemas during CI?

---

**Document Version**: 1.0
**Created**: 2025-01-09
**Status**: Planning Phase
**Author**: Architecture Review

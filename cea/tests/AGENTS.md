# Test Suite

## Main API
- `pytest cea/tests/test_pathway_api.py` - Regression coverage for the pathway overview/timeline API and editor routes.

## Key Patterns
### DO: Build fully isolated temporary scenarios
```python
config = Configuration(cea.config.DEFAULT_CONFIG)
config.project = str(project_root)
config.scenario_name = "baseline"
```

### DO: Seed only the files a pathway test needs
```python
_write_zone_shapefile(locator)
_write_minimal_pathway_databases(locator)
_write_demo_pathway(locator)
```

### DO: Assert hash-backed phase status transitions
```python
assert row["status"]["simulation"]["state"] == "changed_after_simulation"
```

### DO: Exercise dashboard job scripts through `cea.api` when they wrap pathway helpers
```python
cea.api.pathway_update_building_events(
    scenario=config.scenario,
    existing_pathway_name="demo",
    year_of_state=2035,
    new_buildings=["B2"],
)
```

### DO: Build valid baked state folders explicitly before testing aggregate validation jobs
```python
_create_state_folder(locator, "demo", 2040, ["B1", "B2"])
_set_state_wall_thickness(locator, "demo", 2040, 0.15)
cea.api.pathway_validate_all_states(...)
```

### DON'T: Depend on the developer's real projects or config
```python
# Bad: tests must create their own pathway folders and logs.
```

## Related Files
- `test_pathway_api.py` - API-level coverage for overview rows, stock/manual/mixed classification, editor endpoints, and stale-status detection.

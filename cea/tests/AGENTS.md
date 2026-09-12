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

### DO: Test dashboard middleware fallbacks with direct ASGI stubs when backend failures are the behaviour under test
```python
# Simulate cache.get / RedLock / cache.set failures without depending on Redis.
```

### DON'T: Depend on the developer's real projects or config
```python
# Bad: tests must create their own pathway folders and logs.
```

## Related Files
- `test_dashboard_bootstrap.py` - Dashboard preparation and launcher ordering coverage.
- `test_pathway_api.py` - API-level coverage for overview rows, stock/manual/mixed classification, editor endpoints, and stale-status detection.
- `test_pathway_envelope_bake.py` - Envelope row handling when baking a state from a template: the U/GHG cache must be dropped when material layers change (issue #4059), kept when they don't.
- `test_envelope_layer_rules.py` - When U/GHG may be blank: one material layer (name + thickness > 0)
  is enough; service life must always be positive; partial direct values are still cross-checked.
  Also covers `apply_material_derivation`: saving re-derives from edited layers, and a stored value
  that contradicts them is reported as a conflict rather than silently replaced.
- `test_use_stage_proportions.py` - B2 maintenance and B3 repair are RICS-recommended fractions
  of production, charged per installed generation; zero excludes the module.
- `test_technical_system_replacement.py` - Each supply component replaces on its own `LT_yr`;
  the blanket intensity is shared, not multiplied, so building totals are unchanged.
- `test_component_lca.py` - Component service life comes from `LT_yr` first, then a documented
  Green Mark reference, then a short fallback; every shipped component resolves from its own data.
- `test_materials_pre_rename_hint.py` - A MATERIALS.csv with the old `*_recycling` column
  names gets an actionable pointer, not a silent rewrite; a merely incomplete file does not.
- `test_envelope_emission_split.py` - `GHG_*_kgCO2m2` stays the lifecycle total; production
  and demolition split it, derived per row. One file can hold split and unsplit rows.
- `test_biogenic_sign_convention.py` - Biogenic carbon is negative at every level, and no consumer
  may negate it. Scans shipped databases and the source tree.
- `paths.py` - Shared repo/examples/workflows filesystem anchors; use instead of `__file__`-relative math.

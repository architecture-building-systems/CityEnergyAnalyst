# District Pathways

## Main API
- `DistrictEvolutionPathway.required_state_years() -> list[int]` - Shared source for timeline years and baked-state years.
- `DistrictEvolutionPathway.get_combined_building_events(year: int) -> dict[str, list[str]]` - Merge explicit YAML building edits with derived stock births.
- `DistrictEvolutionPathway.get_active_buildings_by_year() -> dict[int, list[str]]` - Compute cumulative building stock for each state year.
- `build_pathway_year_row(pathway, year, issues) -> dict[str, Any]` - Shared year-row projection used by timeline reads and editor preflight.
- `validate_pathway_log_data(config, pathway_name, log_data) -> dict[str, Any]` - Validate log/schema content without touching baked state folders.
- `create_pathway_year(config, pathway_name, year) -> dict` - Validate whether a year already exists; do not create empty placeholders.
- `get_pathway_overview(config) -> dict` - Lightweight multi-pathway lane data for the GUI.
- `get_pathway_timeline(config, pathway_name) -> dict` - Active-pathway timeline rows with status, YAML preview, and validation.
- `update_year_building_events(...) -> dict` - Save explicit building add/remove edits for one year.
- `apply_templates_to_year(...) -> dict` - Reuse Step 2 template merge logic for one selected year.
- `validate_baked_state(...) -> dict` - Run comprehensive baked-state validation and persist a validation hash.
- `print_pathway_action_output(payload: dict[str, Any]) -> None` - Format one mutation result for native dashboard job logs.
- `pathway_validate_all_states_job.main(config) -> dict` - Validate every required baked state year and fail the job if any state is out of sync.

## Key Patterns
### DO: Keep YAML focused on explicit user edits
```python
entry["modifications"] = {...}
entry["building_events"] = {"new_buildings": ["B2"]}
```

### DO: Derive stock-only years from zone construction years
```python
stock_years = pathway.get_effective_construction_years()
years = pathway.required_state_years()
```

### DO: Store bake, validation, and simulation confirmation in `state_status/`
```python
record_baked_state(locator, pathway_name="demo", year=2030, ...)
collect_state_phase_status(locator, pathway_name="demo", year=2030, ...)
```

### DO: Print flushed progress hints from long-running pathway entrypoints
```python
print(f"Starting pathway simulation for '{pathway_name}'.", flush=True)
print(f"- Building state_{year}...", flush=True)
```

### DO: Return structured mutation output from the core helpers
```python
return _action_payload(
    pathway=pathway,
    year=year,
    action="deleted_state",
    message="Deleted explicit pathway state 2030.",
    messages=["Removed the year entry from the pathway log."],
)
```

### DO: Split concerns by domain layer, not by button or editor mode
```python
# pathway_summary.py
row = build_pathway_year_row(pathway=pathway, year=2030, issues=[])

# pathway_validation.py
payload = validate_pathway_log_data(config=config, pathway_name=name, log_data=pathway.log_data)

# pathway_timeline.py
return {"years": rows, "validation": payload}
```

### DO: Route panel mutations through real CEA scripts when the GUI needs native Job Info
```python
payload = update_year_yaml(config, pathway_name, year, raw_yaml=raw_yaml)
print_pathway_action_output(payload)
```

### DO: Keep CEA-side config and job names domain-neutral
```text
pathway-state-edit
District Pathway: Save YAML
```

### DO: Use one aggregate validation job for the header-level "validate all states" action
```python
summary = validate_all_baked_states(config, pathway_name)
```

### DO: Treat all new years as edit-on-save in the GUI
```python
raise YearRequiresEditError(...)
# Save through building events, templates, or YAML instead.
```

### DON'T: Persist a `manual_state` flag in pathway YAML
```python
cleaned_entry.pop("manual_state", None)
```

### DON'T: Materialise `state_{year}` folders from timeline edits
```python
# Bad: timeline actions stay log-only until bake/simulate runs
```

## Related Files
- `pathway_state.py` - Core year mutation, active-building derivation, and bake/simulate helpers.
- `pathway_summary.py` - Shared year-row projection and YAML preview helpers.
- `pathway_validation.py` - Log/schema and baked-state validation helpers.
- `pathway_timeline.py` - Public pathway service facade for overview, timeline, and year actions.
- `pathway_status.py` - Hash-backed phase status sidecar records.
- `pathway_integrity.py` - Comprehensive baked-state validation.

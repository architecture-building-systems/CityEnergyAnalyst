# Special Visualisation Modules

## Main API
- create_pathway_emission_timeline_plot(config) -> plotly.graph_objs.Figure - Build a pathway-specific emission timeline figure.
- main(config) -> str - Return Plotly HTML for dashboard and CLI usage.

## Key Patterns
### DO: Keep pathway plotting independent from standard emission timeline wiring
```python
plot_config = config.sections["plots-pathway-emission-timeline"]
fig = create_pathway_emission_timeline_plot(config)
```

### DO: Prefer per-building pathway timeline aggregation for filtered building plots
```python
aggregated, missing = _aggregate_building_pathway_timelines(locator, pathway_name, selected_buildings)
```

### DO: Reuse EmissionTimelinePlot visual behaviour via config adapter
```python
plot_adapter = _TimelineConfigAdapter(plots_emission_timeline=plot_config)
plot_obj = EmissionTimelinePlot(plot_adapter, df_to_plotly, y_columns, ...)
```

### DO: Treat placeholder context period bounds (0, 0) as no filter
```python
period_start, period_end = _resolve_period_bounds(context)
```

### DO: Apply `cutoff_year` before plotting cumulative pathway emissions
```python
timeline_df = _apply_cutoff_year(timeline_df, cutoff_year)
period_start, period_end = _resolve_effective_year_bounds(context, cutoff_year)
```

### DON'T: Route pathway plots through plot_input_processor/result_summary export files
```python
# Avoid this for pathway plots:
# df_summary_data, df_architecture_data, plot_instance = plot_input_processor(...)
```

## Related Files
- pathway_emission_timeline.py - Dedicated pathway timeline plot entry.
- emission_timeline.py - Shared timeline figure behaviour and styling.
- ../../datamanagement/district_pathways/pathway_emissions_timeline.py - Pathway timeline CSV generation.

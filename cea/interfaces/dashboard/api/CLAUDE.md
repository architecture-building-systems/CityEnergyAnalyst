# Dashboard API

## Main API
- `GET /api/pathways/overview` - Shared span plus lightweight year lanes for all pathways.
- `GET /api/pathways/{pathway_name}/timeline` - Detailed active-pathway rows for the timeline panel.
- `POST /api/pathways/{pathway_name}/years/{year}` - Create a new explicit year only when it is not a stock-only state.
- `GET /api/pathways/{pathway_name}/years/{year}/editor-options` - Building/template choices for the year editors.
- `POST /api/pathways/{pathway_name}/years/{year}/building-events` - Save building add/remove edits.
- `POST /api/pathways/{pathway_name}/years/{year}/apply-templates` - Apply Step 2 templates directly from the panel.
- `PUT /api/pathways/{pathway_name}/years/{year}/yaml` - Expert-mode YAML save.
- `POST /api/pathways/{pathway_name}/years/{year}/validate-state` - Manual baked-state validation.

## Key Patterns
### DO: Keep routes thin and delegate to pathway domain helpers
```python
return await run_in_threadpool(get_pathway_timeline, config, pathway_name)
```

### DO: Treat any route that writes logs or status files as a normal authenticated write
```python
@router.post("/{pathway_name}/years/{year}/validate-state", dependencies=[CEASeverDemoAuthCheck])
```

### DO: Preserve structured 409 payloads for stock-only edit rules
```python
detail={"message": str(exc), "state_kind": "stock", "requires_edit": True}
```

### DO: Reserve `/api/pathways/*` for dashboard-specific pathway UX
```python
# Timeline/editor actions should not be routed through `/api/tools/*`.
```

### DON'T: Bake or simulate directly inside route handlers
```python
# Job launching stays in the GUI job sy
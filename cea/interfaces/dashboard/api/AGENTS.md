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

## Route Design Principles

Standard REST hygiene applies and isn't spelled out here: GET never mutates, writes don't return opportunistically-computed data, and errors raise a meaningful `HTTPException` instead of being swallowed (`except Exception: return {}`). The CEA-specific rules:

**Route independence** — each route does exactly one thing and is correct when called in isolation. No cascading side effects (launching jobs, invalidating caches, notifying other subsystems) and no assuming another route ran first or left state behind.
```python
# Bad: POST /scenarios creates scenario AND copies template AND sets it active
# Bad: POST /validate-and-save
# Good: separate routes; the client calls them in sequence
```

**Conflicts return 409** — `POST`/`PUT` create that hits an existing resource raises `409` (see `post_pathway`, `duplicate_pathway`); don't silently overwrite or duplicate. `PUT` to a known address is the idempotent update path (overwrite, return 200).

## Coordinating Sequential Steps

Choose the pattern based on the nature of the sequence:

| Sequence type | Pattern |
|---|---|
| Fast, independent steps | Client orchestrates — call routes in sequence from the frontend |
| Long-running or needs logs | Job system — one POST launches the job, client polls for status |
| Steps must be atomic | Service layer — one route calls one service function that wraps all steps |

**Client orchestration** (default for short synchronous flows): each route is independent, the client holds state between calls, the server has no knowledge of the sequence.

**Job system** (long-running): the sequence lives inside the job worker, not across routes.

**Service layer** (atomic):
```python
@router.post("/scenarios/clone")
async def clone_scenario(...):
    await run_in_threadpool(clone_scenario_service, config, name)
```

Never have a route call another route, or store intermediate state for another route to pick up.

## Key Patterns
### DO: Use CEAScenario / CEAScenarioLenient for any route that reads a scenario
`CEAScenario` handles header parsing (`X-CEA-Project`, `X-CEA-Scenario-Name`, `X-CEA-Child-Scenario`),
project-root boundary enforcement, and path sanitisation in one dependency. Never accept raw
`project: str` + `scenario: str` query params and call `resolve_scenario_path` manually — that
pattern bypasses the header contract and duplicates security logic.

Use `CEAScenario` when the scenario directory must exist; `CEAScenarioLenient` when it may not
(e.g. metadata/config endpoints). Both enforce path boundaries.

```python
# DO
async def get_data(scenario: CEAScenario):
    locator = cea.inputlocator.InputLocator(scenario)

# DON'T
async def get_data(project_root: CEAProjectRoot, project: str, scenario: str):
    scenario_path = resolve_scenario_path(project_root, project, scenario)
```

### DO: Keep routes thin and delegate to pathway domain helpers
```python
return await run_in_threadpool(get_pathway_timeline, config, pathway_name)
```

### DO: Treat any route that writes logs or status files as a normal authenticated write
```python
@router.post("/{pathway_name}/years/{year}/validate-state")
# No per-route auth annotation needed — require_authenticated runs app-wide.
# Add to _PUBLIC_ROUTES in dependencies.py only if the route must be publicly accessible.
```

### DO: Preserve structured 409 payloads for stock-only edit rules
```python
detail={"message": str(exc), "state_kind": "stock", "requires_edit": True}
```

### DO: Guard user-derived path segments before filesystem checks
```python
candidate = os.path.realpath(os.path.join(base_dir, user_value))
if os.path.commonpath((base_dir, candidate)) != base_dir:
	return []
```

### DO: Reserve `/api/pathways/*` for dashboard-specific pathway UX
```python
# Timeline/editor actions should not be routed through `/api/tools/*`.
```

### DO: Use InputLocator directly for CEAScenario-derived paths
```python
locator = cea.inputlocator.InputLocator(scenario)  # scenario: CEAScenario already sanitised
folder = secure_join_under_root(parent_folder, user_segment)
```

### DON'T: Bake or simulate directly inside route handlers
```python
# Job launching stays in the GUI job system.
```

## Related Files
- `pathways.py` - Dedicated pathway routes and payload models.
- `__init__.py` - Router registration.
- `../AGENTS.md` - Broader dashboard architecture and job-system notes.

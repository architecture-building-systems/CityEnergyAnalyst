"""
Public demo sub-app — anonymous, read-only, allowlist-scoped.

Mounted at /api/demo by app.py when public_demo_scenarios is configured.
This is a standalone FastAPI app and does NOT inherit the main app's
require_authenticated dependency — the anonymous boundary is structural.

Routes wrap the normal API routers (inputs, map-layers, canvas, reports,
tools, kpis, pathways) rather than duplicating their logic. The key mechanism is two
dependency_overrides that replace get_effective_scenario /
get_effective_scenario_lenient with require_public_demo_read, which reads
{demo_id} from the URL path and checks it against the configured allowlist.
This makes CEAScenario resolve to the allowlisted path instead of the
user's project root.

URL shape: /api/demo/scenarios/{demo_id}/<domain>/...

Write routes are excluded via _filter_routes. Canvas export is excluded
because it needs CEAConfig to re-render all plot cards. Reports /scenarios
is excluded because it uses CEAProjectRoot + project rather than CEAScenario.

To add a new demo resource:
  1. Add an entry to CEA_PUBLIC_DEMO_SCENARIOS (or Settings.public_demo_scenarios).
  2. Optionally extend the routes below to expose more data for that scenario.

Topology note: this sub-app can be extracted into a standalone service with
no code change — deploy it alone and gateway /api/demo/* to it.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.routing import APIRoute

import cea.scripts
import cea.interfaces.dashboard.api.canvas as canvas_module
import cea.interfaces.dashboard.api.inputs as inputs_module
import cea.interfaces.dashboard.api.kpis as kpis_module
import cea.interfaces.dashboard.api.map_layers as map_layers_module
import cea.interfaces.dashboard.api.pathways as pathways_module
import cea.interfaces.dashboard.api.reports as reports_module
import cea.interfaces.dashboard.api.tools as tools_module
from cea.interfaces.dashboard.api.tools import ToolProperties
from cea.interfaces.dashboard.api.utils import (
    get_effective_scenario,
    get_effective_scenario_lenient,
)
from cea.interfaces.dashboard.dependencies import CEAConfig, CEAServerSettings

# TODO: Cache responses for public demo scenarios (e.g. /scenarios/{demo_id}/inputs) to reduce load on the CEAConfig
app = FastAPI(title="CEA Demo", description="Public read-only demo scenarios.")


def require_public_demo_read(demo_id: str, settings: CEAServerSettings) -> str:
    """
    Resolve an allowlisted demo id to its scenario path.

    Used as both the router-level guard (_demo_guard) and the dependency override for
    get_effective_scenario / get_effective_scenario_lenient. {demo_id} comes from the URL
    path; normal routes resolve scenario via headers/query params relative to the user's
    project root (get_effective_scenario → CEAProjectRoot → CEAUserID) — this replaces
    that chain with a simple allowlist lookup, so no user context is needed.

    Raises 404 for unknown ids — no arbitrary filesystem paths are ever accepted.
    Never uses CEAScenario, CEAProjectRoot, or CEAUserID; safe for anonymous callers.
    """
    path = settings.public_demo_scenarios.get(demo_id)
    if path is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Demo scenario not found.")
    return path


app.dependency_overrides[get_effective_scenario] = require_public_demo_read
app.dependency_overrides[get_effective_scenario_lenient] = require_public_demo_read

# Router-level guard for routes that have no CEAScenario dependency (e.g. /features).
# Routes that do use CEAScenario are already guarded by the dependency_overrides above.
_demo_guard = [Depends(require_public_demo_read)]


def _filter_routes(
    router,
    *,
    allowed_methods: set | None = None,
    exclude_paths: set | None = None,
) -> APIRouter:
    """Return a new APIRouter with only routes whose method set intersects
    allowed_methods (default GET) and whose path is not in exclude_paths."""
    allowed_methods = allowed_methods or {"GET"}
    exclude_paths = exclude_paths or set()
    filtered = APIRouter()
    for route in router.routes:
        if not isinstance(route, APIRoute):
            continue
        if route.path in exclude_paths:
            continue
        if route.methods & allowed_methods:
            filtered.routes.append(route)
    return filtered


# ── Inputs ─────────────────────────────────────────────────────────────────
# All GET routes from inputs.router; PUT / POST (save, upload) excluded.

app.include_router(
    _filter_routes(inputs_module.router, allowed_methods={"GET"}),
    prefix="/scenarios/{demo_id}/inputs",
    dependencies=_demo_guard,
)


# ── Map layers ─────────────────────────────────────────────────────────────
# GET catalogue + POST-as-read parameter queries (choices, range, generate,
# check). choice/delete is a genuine write — excluded.

app.include_router(
    _filter_routes(
        map_layers_module.router,
        allowed_methods={"GET", "POST"},
        exclude_paths={"/{layer_category}/{layer_name}/{parameter}/choice/delete"},
    ),
    prefix="/scenarios/{demo_id}/map_layers",
    dependencies=_demo_guard,
)


# ── Canvas ─────────────────────────────────────────────────────────────────
# GET list and read. /{name}/export excluded: it re-renders all plot cards
# via capture_canvas_data(config, ...) which needs a full CEAConfig object.

app.include_router(
    _filter_routes(
        canvas_module.router,
        allowed_methods={"GET"},
        exclude_paths={"/{name}/export"},
    ),
    prefix="/scenarios/{demo_id}/canvas",
    dependencies=_demo_guard,
)


# ── Reports ────────────────────────────────────────────────────────────────
# GET routes only, plus POST /plot-custom: render_plot_html() (plot_dispatch.py)
# validates that the requested script is category="Visualisation",
# interfaces includes "dashboard", and module is under cea.visualisation.* —
# so an anonymous caller can only ever dispatch a genuine plot script, never
# an arbitrary registered CEA script.

app.include_router(
    _filter_routes(reports_module.router, allowed_methods={"GET", "POST"}),
    prefix="/scenarios/{demo_id}/reports",
    dependencies=_demo_guard,
)


# ── Tools ──────────────────────────────────────────────────────────────────
# GET / (the tool catalogue): static metadata from scripts.yml
# (name/label/description per dashboard-interface script), no config.scenario
# or config.project access, no per-parameter data - safe for every tool.
#
# GET /{tool_name}: label/description/category only (static, from
# scripts.yml) - parameters/categorical_parameters always forced empty for
# every tool, never resolved.

app.include_router(
    _filter_routes(tools_module.router, allowed_methods={"GET"}, exclude_paths={"/{tool_name}"}),
    prefix="/scenarios/{demo_id}/tools",
    dependencies=_demo_guard,
)


@app.get("/scenarios/{demo_id}/tools/{tool_name}", dependencies=_demo_guard)
async def get_demo_tool_properties(config: CEAConfig, tool_name: str) -> ToolProperties:
    try:
        script = cea.scripts.by_name(tool_name, plugins=config.plugins)
    except cea.ScriptNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found.",
        ) from exc
    return ToolProperties(
        name=tool_name,
        label=script.label,
        description=script.description,
        short_description=script.short_description,
        category=script.category,
        categorical_parameters={},
        parameters=[],
    )


# ── KPIs ───────────────────────────────────────────────────────────────────
# All GET routes: /registry (static catalogue), / (bulk KPI values),
# /{kpi_id}/parameters, /{kpi_id}/value — all resolved against the
# allowlisted scenario via CEAScenario. No write routes exist.

app.include_router(
    _filter_routes(kpis_module.router, allowed_methods={"GET"}),
    prefix="/scenarios/{demo_id}/kpis",
    dependencies=_demo_guard,
)


# ── Pathways ───────────────────────────────────────────────────────────────
# GET routes only: pathway/template listing, overview, timeline, geojson,
# editor options, building lifecycle. Write routes (create/duplicate
# pathway, post-year, building-events, apply-templates, yaml save, delete,
# validate) are excluded.

app.include_router(
    _filter_routes(pathways_module.router, allowed_methods={"GET"}),
    prefix="/scenarios/{demo_id}/pathways",
    dependencies=_demo_guard,
)


# ── Scenario list ──────────────────────────────────────────────────────────

@app.get("/scenarios")
async def list_demo_scenarios(settings: CEAServerSettings):
    """List all allowlisted demo scenario ids."""
    return {
        "scenarios": [{"id": demo_id, "name": demo_id} for demo_id in settings.public_demo_scenarios]
    }

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
Inputs /databases/download is excluded because it zips and reads back the
entire db4 folder on every call — real disk I/O anonymous callers could
trigger repeatedly against a scenario that never changes.

To add a new demo resource:
  1. Add an entry to CEA_PUBLIC_DEMO_SCENARIOS (or Settings.public_demo_scenarios).
  2. Optionally extend the routes below to expose more data for that scenario.

Topology note: this sub-app can be extracted into a standalone service with
no code change — deploy it alone and gateway /api/demo/* to it.
"""
from __future__ import annotations

import hashlib

from aiocache.lock import RedLock
from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.routing import APIRoute
from starlette.types import ASGIApp, Message, Receive, Scope, Send

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
from cea.interfaces.dashboard.lib.cache.provider import get_cache
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger

logger = getCEAServerLogger("cea-server-demo")

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
# /databases/download excluded: it zips and reads back the entire db4 folder
# on every call (see download_input_database in inputs.py) - real disk I/O an
# anonymous caller could trigger repeatedly for a scenario that never changes,
# with no cacheable benefit since the payload is a binary zip, not JSON.

app.include_router(
    _filter_routes(
        inputs_module.router,
        allowed_methods={"GET"},
        exclude_paths={"/databases/download"},
    ),
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


# ── Response cache ──────────────────────────────────────────────────────────
# Anonymous users land on a demo scenario by default on first app load, so the
# same handful of GET responses (notably /inputs/all-inputs and /map_layers/)
# get recomputed from disk for every visitor. Demo content is a fixed,
# read-only allowlist that never changes for the life of the process, so
# caching full responses here is safe in a way it wouldn't be for a live user
# scenario (no writes ever invalidate it) - TTL alone bounds staleness.
#
# Implemented as pure ASGI middleware (not BaseHTTPMiddleware) so non-GET
# requests pass straight through with zero buffering, and a cache hit can be
# served without ever calling the router. Non-JSON or oversized GET responses
# are still buffered up to MAX_CACHEABLE_BYTES before being discarded as
# uncacheable — routes expected to return large/binary payloads (e.g. the
# database zip download) are excluded from the demo mount entirely instead
# (see _filter_routes calls above) so anonymous callers can't trigger that
# I/O at all. Reuses the existing aiocache singleton (get_cache()) - Redis or
# SimpleMemoryCache depending on deployment - rather than a new mechanism.

class DemoResponseCache:
    """Caches GET responses from the demo sub-app in the shared aiocache instance.

    Non-GET requests and non-JSON/oversized responses pass through untouched.
    A RedLock around the miss path collapses a cold-cache thundering herd
    (many anonymous users hitting e.g. /all-inputs at once) into a single
    compute per process; waiters in the same process block on that one
    compute rather than each recomputing.

    Note on multi-worker deployments: aiocache's RedLock only fully blocks
    waiters within the process that lost the race - its wait mechanism keys
    off a process-local asyncio.Event, so a waiter in a different worker
    process can't see it, silently stops waiting, and computes independently
    (verified empirically: 5 workers hitting a cold key produced 5 computes,
    not 1). This still bounds the stampede to at most one compute per worker
    process rather than one per request, which is the meaningful win here.
    """

    CACHEABLE_CONTENT_TYPES = ("application/json", "application/geo+json")
    MAX_CACHEABLE_BYTES = 32 * 1024 * 1024  # generous cap; excludes pathological payloads
    CACHE_KEY_PREFIX = "demo:"
    CACHE_STATUS_HEADER = b"x-demo-cache"
    CACHE_REJECT_HEADERS = frozenset({b"set-cookie", b"vary"})
    # Public demo responses are read-only/static for the process lifetime (fixed
    # allowlist, no writes) - TTL alone bounds staleness, no content hash needed.
    CACHE_TTL = 3600  # 1 hour
    # /scenarios reflects settings.public_demo_scenarios (from CEA_PUBLIC_DEMO_SCENARIOS),
    # which can change across a redeploy - unlike scenario file content, it is not fixed
    # for the lifetime of the Redis-backed cache (which outlives any single process). It's
    # also a trivial in-memory dict iteration, so caching it has no performance upside.
    UNCACHEABLE_PATHS = frozenset({"/scenarios"})

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope["method"] != "GET"
            or scope["path"] in self.UNCACHEABLE_PATHS
        ):
            await self.app(scope, receive, send)
            return

        key = self._cache_key(scope)
        cache = get_cache()

        try:
            hit = await cache.get(key)
        except Exception:
            logger.warning("demo cache read failed key=%s; bypassing cache", key, exc_info=True)
            await self.app(scope, receive, send)
            return

        if hit is not None:
            logger.debug("demo cache HIT key=%s", key)
            await self._send_cached(send, hit, b"HIT")
            return

        lock = RedLock(cache, key, lease=60)
        try:
            await lock.__aenter__()
        except Exception:
            logger.warning("demo cache lock failed key=%s; bypassing cache", key, exc_info=True)
            await self.app(scope, receive, send)
            return

        exc_info = (None, None, None)
        try:
            # Re-check inside the lock: whoever held it may have just populated it.
            try:
                hit = await cache.get(key)
            except Exception:
                logger.warning(
                    "demo cache read failed inside lock key=%s; bypassing cache",
                    key,
                    exc_info=True,
                )
            else:
                if hit is not None:
                    logger.debug("demo cache HIT (post-lock) key=%s", key)
                    await self._send_cached(send, hit, b"HIT")
                    return

            start: dict = {}
            chunks: list = []
            # Determined from headers as soon as http.response.start arrives, and
            # revoked early if the body outgrows MAX_CACHEABLE_BYTES - so a
            # non-JSON or oversized response is never fully buffered just to be
            # discarded afterwards.
            cache_state = {"eligible": False, "size": 0}

            async def send_wrapper(message: Message) -> None:
                if message["type"] == "http.response.start":
                    start["status"] = message["status"]
                    start["headers"] = message["headers"]
                    cache_state["eligible"] = self._headers_cacheable(start)
                    message = {
                        **message,
                        "headers": [*message["headers"], (self.CACHE_STATUS_HEADER, b"MISS")],
                    }
                elif message["type"] == "http.response.body" and cache_state["eligible"]:
                    body = message.get("body", b"")
                    cache_state["size"] += len(body)
                    if cache_state["size"] > self.MAX_CACHEABLE_BYTES:
                        cache_state["eligible"] = False
                        chunks.clear()
                    else:
                        chunks.append(body)
                await send(message)

            await self.app(scope, receive, send_wrapper)

            if cache_state["eligible"]:
                logger.debug("demo cache MISS, storing key=%s", key)
                try:
                    await cache.set(key, self._pack(start, chunks), ttl=self.CACHE_TTL)
                except Exception:
                    logger.warning(
                        "demo cache write failed key=%s; response already sent",
                        key,
                        exc_info=True,
                    )
            else:
                logger.debug("demo cache MISS, not cacheable key=%s", key)
        except BaseException as exc:
            exc_info = (type(exc), exc, exc.__traceback__)
            raise
        finally:
            try:
                await lock.__aexit__(*exc_info)
            except Exception:
                # Response (or the original downstream exception) is already on
                # its way to the client by this point; a release failure here
                # (e.g. Redis blip) must not replace it - just log and move on.
                logger.warning("demo cache unlock failed key=%s", key, exc_info=True)

    @staticmethod
    def _cache_key(scope: Scope) -> str:
        """Build a cache key from method + path + query string.

        Headers are deliberately excluded: demo output depends only on the
        {demo_id} path segment and query params (require_public_demo_read never
        reads X-CEA-* headers/cookies), so two requests with the same path+query
        always produce the same response.
        """
        path = scope["path"]
        query = scope.get("query_string", b"").decode()
        raw = f"{scope['method']}:{path}?{query}"
        return DemoResponseCache.CACHE_KEY_PREFIX + hashlib.sha1(raw.encode()).hexdigest()

    @staticmethod
    def _header_value(headers: list, name: bytes) -> bytes:
        for key, value in headers:
            if key.lower() == name:
                return value
        return b""

    @staticmethod
    def _headers_cacheable(start: dict) -> bool:
        """Cacheability decided from http.response.start alone (status, headers,
        content-type) - before any body bytes exist. Size is bounded separately
        as the body streams in, since it isn't known at this point."""
        if start.get("status") != 200:
            return False
        if DemoResponseCache._cache_headers(start.get("headers", [])) is None:
            return False
        content_type = DemoResponseCache._header_value(
            start.get("headers", []), b"content-type"
        ).decode().lower()
        return content_type.startswith(DemoResponseCache.CACHEABLE_CONTENT_TYPES)

    @staticmethod
    def _pack(start: dict, chunks: list) -> dict:
        return {
            "headers": DemoResponseCache._cache_headers(start.get("headers", [])) or [],
            "body": b"".join(chunks),
        }

    @staticmethod
    def _cache_headers(headers: list) -> list | None:
        cached_headers = []
        for key, value in headers:
            lowered = key.lower()
            if lowered == DemoResponseCache.CACHE_STATUS_HEADER:
                continue
            if lowered in DemoResponseCache.CACHE_REJECT_HEADERS:
                return None
            if lowered == b"cache-control" and not DemoResponseCache._cache_control_allows(value):
                return None
            cached_headers.append((key, value))
        return cached_headers

    @staticmethod
    def _cache_control_allows(value: bytes) -> bool:
        directives = {part.strip().lower() for part in value.decode().split(",") if part.strip()}
        return "private" not in directives and "no-store" not in directives

    @staticmethod
    def _replay_headers(headers: list) -> list:
        return [
            (key, value)
            for key, value in headers
            if key.lower() not in DemoResponseCache.CACHE_REJECT_HEADERS
            and key.lower() != DemoResponseCache.CACHE_STATUS_HEADER
        ]

    @staticmethod
    async def _send_cached(send: Send, packed: dict, cache_status: bytes) -> None:
        headers = DemoResponseCache._replay_headers(packed.get("headers", []))
        headers = [*headers, (DemoResponseCache.CACHE_STATUS_HEADER, cache_status)]
        await send({"type": "http.response.start", "status": 200, "headers": headers})
        await send({"type": "http.response.body", "body": packed["body"]})


app.add_middleware(DemoResponseCache)

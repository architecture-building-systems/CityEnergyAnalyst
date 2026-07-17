"""Tests for the public demo sub-app."""
import pytest
from aiocache import SimpleMemoryCache
from aiocache.serializers import PickleSerializer
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock

import cea.interfaces.dashboard.lib.cache.provider as cache_provider
import cea.interfaces.dashboard.api.demo as demo_module
from cea.interfaces.dashboard.api.demo import require_public_demo_read
from cea.interfaces.dashboard.lib.cache.settings import CACHE_NAME
from cea.interfaces.dashboard.settings import Settings


@pytest.fixture(autouse=True)
def _reset_demo_cache():
    """DemoResponseCache reads/writes through the process-global cache singleton
    (get_cache()), which outlives any single test. Its key is path+query only, with
    no settings dimension, so a response cached under one test's settings override
    would otherwise leak into a later test that hits the same path with a different
    override.

    Force a fresh SimpleMemoryCache per test rather than resetting to None: get_cache()
    picks RedisCache whenever CEA_CACHE_HOST is set in the developer's ambient
    environment (e.g. .env.local), which these tests must not depend on (see
    cea/tests/AGENTS.md - don't depend on the developer's real config). Redis is also
    unsafe here regardless: aiocache's Redis connection binds to whichever asyncio event
    loop is running when first used, but each TestClient(demo_app) instantiation opens
    its own event loop, so a connection opened under one test's loop breaks when reused
    under a later test's (already-closed) loop.
    """
    cache_provider._cache_instance = SimpleMemoryCache(serializer=PickleSerializer(), namespace=CACHE_NAME)
    yield
    cache_provider._cache_instance = None

# ---------------------------------------------------------------------------
# Unit tests — require_public_demo_read (direct-call style, like test_dashboard_auth.py)
# ---------------------------------------------------------------------------

DEMO_SCENARIOS = {"city-a": "/data/scenarios/city_a", "city-b": "/data/scenarios/city_b"}
SETTINGS_WITH_DEMOS = Settings.model_construct(public_demo_scenarios=DEMO_SCENARIOS)
SETTINGS_EMPTY = Settings.model_construct(public_demo_scenarios={})


def test_known_demo_id_returns_path():
    path = require_public_demo_read("city-a", SETTINGS_WITH_DEMOS)
    assert path == "/data/scenarios/city_a"


def test_unknown_demo_id_raises_404():
    with pytest.raises(HTTPException) as exc_info:
        require_public_demo_read("unknown", SETTINGS_WITH_DEMOS)
    assert exc_info.value.status_code == 404


def test_empty_allowlist_raises_404():
    with pytest.raises(HTTPException) as exc_info:
        require_public_demo_read("city-a", SETTINGS_EMPTY)
    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Settings parsing — public_demo_scenarios field validator
# ---------------------------------------------------------------------------


def test_settings_parses_id_colon_path_format():
    Settings.model_construct()
    parsed = Settings.parse_demo_scenarios("demo1:/a/b,demo2:/c/d")
    assert parsed == {"demo1": "/a/b", "demo2": "/c/d"}


def test_settings_parses_empty_string_to_empty_dict():
    parsed = Settings.parse_demo_scenarios("")
    assert parsed == {}


def test_settings_parses_dict_passthrough():
    d = {"x": "/some/path"}
    assert Settings.parse_demo_scenarios(d) is d


def test_settings_raises_on_invalid_entry():
    with pytest.raises(ValueError, match="Expected format"):
        Settings.parse_demo_scenarios("no-colon-here")


# ---------------------------------------------------------------------------
# HTTP tests — demo sub-app (TestClient, like test_pathway_api.py)
# ---------------------------------------------------------------------------


def _make_demo_client(demo_scenarios: dict):
    """Build a TestClient for the demo sub-app with an injected allowlist.

    Only overrides get_settings (test-scoped). The module-level overrides
    for get_effective_scenario / get_effective_scenario_lenient are preserved
    by removing only the test-added key in teardown.
    """
    from cea.interfaces.dashboard.api.demo import app as demo_app
    from cea.interfaces.dashboard.settings import get_settings

    settings = Settings.model_construct(public_demo_scenarios=demo_scenarios)
    demo_app.dependency_overrides[get_settings] = lambda: settings
    client = TestClient(demo_app, raise_server_exceptions=True)
    return client, demo_app, get_settings


def test_list_demo_scenarios_returns_configured_ids():
    client, demo_app, get_settings_fn = _make_demo_client(
        {"city-a": "/data/city_a", "city-b": "/data/city_b"}
    )
    try:
        resp = client.get("/scenarios")
        assert resp.status_code == 200
        ids = {s["id"] for s in resp.json()["scenarios"]}
        assert ids == {"city-a", "city-b"}
    finally:
        demo_app.dependency_overrides.pop(get_settings_fn, None)


def test_list_demo_scenarios_empty_when_not_configured():
    client, demo_app, get_settings_fn = _make_demo_client({})
    try:
        resp = client.get("/scenarios")
        assert resp.status_code == 200
        assert resp.json()["scenarios"] == []
    finally:
        demo_app.dependency_overrides.pop(get_settings_fn, None)


def test_demo_cache_hits_real_route_on_second_request():
    """End-to-end wiring check: DemoResponseCache is installed via app.add_middleware
    on the real demo_app, so two requests through TestClient against a real, static
    route (reports/features - no CEAConfig/scenario needed) must transition
    MISS -> HIT through the process cache singleton that _reset_demo_cache installs.

    This is the one test that would catch a wiring mistake (middleware order, or the
    path the middleware sees not matching what it expects once mounted) that the
    unit tests above - which drive DemoResponseCache directly with stub ASGI apps -
    cannot catch.
    """
    client, demo_app, get_settings_fn = _make_demo_client({"city-a": "/data/city_a"})
    try:
        first = client.get("/scenarios/city-a/reports/features")
        assert first.status_code == 200
        assert first.headers["x-demo-cache"] == "MISS"

        second = client.get("/scenarios/city-a/reports/features")
        assert second.status_code == 200
        assert second.headers["x-demo-cache"] == "HIT"
        assert second.json() == first.json()
    finally:
        demo_app.dependency_overrides.pop(get_settings_fn, None)


class _NoopRedLock:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FailingRedLock:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        raise RuntimeError("lock failed")

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FailingExitRedLock:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        raise RuntimeError("unlock failed")


def _make_cached_scope(path: str = "/scenarios/demo/inputs/all-inputs"):
    return {
        "type": "http",
        "method": "GET",
        "path": path,
        "query_string": b"",
        "headers": [],
        "scheme": "http",
        "http_version": "1.1",
        "client": ("testclient", 123),
        "server": ("testserver", 80),
    }


async def _call_demo_cache(middleware, scope=None):
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    await middleware(scope or _make_cached_scope(), receive, send)
    return messages


def _make_json_demo_app(body: bytes = b'{"ok": true}', *, raise_after_start: bool = False):
    async def app(scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        if raise_after_start:
            raise ValueError("downstream failed")
        await send({"type": "http.response.body", "body": body})

    return app


def _make_cache(get_result=None, *, get_side_effect=None, set_side_effect=None):
    cache = Mock()
    cache.get = AsyncMock(side_effect=get_side_effect, return_value=get_result)
    cache.set = AsyncMock(side_effect=set_side_effect)
    return cache


@pytest.mark.anyio
async def test_demo_cache_hits_when_backend_succeeds(monkeypatch):
    cache = _make_cache(
        get_result={"headers": [(b"content-type", b"application/json")], "body": b'{"ok": true}'}
    )
    monkeypatch.setattr(demo_module, "get_cache", lambda: cache)
    monkeypatch.setattr(demo_module, "RedLock", _NoopRedLock)

    app_called = False

    async def app(scope, receive, send):
        nonlocal app_called
        app_called = True
        await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": b'{"miss": true}'})

    messages = await _call_demo_cache(demo_module.DemoResponseCache(app))

    assert app_called is False
    assert messages[0]["status"] == 200
    assert (b"x-demo-cache", b"HIT") in messages[0]["headers"]
    assert messages[1]["body"] == b'{"ok": true}'
    assert cache.set.await_count == 0


@pytest.mark.anyio
async def test_demo_cache_bypasses_when_initial_read_fails(monkeypatch):
    cache = _make_cache(get_side_effect=RuntimeError("read failed"))
    monkeypatch.setattr(demo_module, "get_cache", lambda: cache)

    app_called = False

    async def app(scope, receive, send):
        nonlocal app_called
        app_called = True
        await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": b'{"ok": true}'})

    messages = await _call_demo_cache(demo_module.DemoResponseCache(app))

    assert app_called is True
    assert messages[0]["status"] == 200
    assert (b"x-demo-cache", b"MISS") not in messages[0]["headers"]
    assert messages[1]["body"] == b'{"ok": true}'
    assert cache.set.await_count == 0


@pytest.mark.anyio
async def test_demo_cache_bypasses_when_lock_fails(monkeypatch):
    cache = _make_cache(get_result=None)
    monkeypatch.setattr(demo_module, "get_cache", lambda: cache)
    monkeypatch.setattr(demo_module, "RedLock", _FailingRedLock)

    app_called = False

    async def app(scope, receive, send):
        nonlocal app_called
        app_called = True
        await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": b'{"ok": true}'})

    messages = await _call_demo_cache(demo_module.DemoResponseCache(app))

    assert app_called is True
    assert messages[0]["status"] == 200
    assert messages[1]["body"] == b'{"ok": true}'
    assert cache.set.await_count == 0


@pytest.mark.anyio
async def test_demo_cache_swallows_set_failure_after_response(monkeypatch):
    cache = _make_cache(get_side_effect=[None, None], set_side_effect=RuntimeError("write failed"))
    monkeypatch.setattr(demo_module, "get_cache", lambda: cache)
    monkeypatch.setattr(demo_module, "RedLock", _NoopRedLock)

    messages = await _call_demo_cache(demo_module.DemoResponseCache(_make_json_demo_app()))

    assert messages[0]["status"] == 200
    assert (b"x-demo-cache", b"MISS") in messages[0]["headers"]
    assert messages[1]["body"] == b'{"ok": true}'
    assert cache.set.await_count == 1


@pytest.mark.anyio
@pytest.mark.parametrize(
    "headers",
    [
        [
            (b"content-type", b"application/json"),
            (b"vary", b"accept-encoding"),
        ],
        [
            (b"content-type", b"application/json"),
            (b"cache-control", b"private, max-age=60"),
        ],
        [
            (b"content-type", b"application/json"),
            (b"cache-control", b"no-store"),
        ],
    ],
)
async def test_demo_cache_rejects_vary_and_private_or_nostore_cache_control(monkeypatch, headers):
    cache = _make_cache(get_side_effect=[None, None])
    monkeypatch.setattr(demo_module, "get_cache", lambda: cache)
    monkeypatch.setattr(demo_module, "RedLock", _NoopRedLock)

    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": headers})
        await send({"type": "http.response.body", "body": b'{"ok": true}'})

    messages = await _call_demo_cache(demo_module.DemoResponseCache(app))

    assert messages[0]["status"] == 200
    assert (b"x-demo-cache", b"MISS") in messages[0]["headers"]
    assert cache.set.await_count == 0


@pytest.mark.anyio
async def test_demo_cache_replays_safe_response_headers(monkeypatch):
    cache = _make_cache(
        get_result={
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-encoding", b"gzip"),
                (b"cache-control", b"public, max-age=60"),
                (b"etag", b'"abc123"'),
            ],
            "body": b"compressed-body",
        }
    )
    monkeypatch.setattr(demo_module, "get_cache", lambda: cache)

    app_called = False

    async def app(scope, receive, send):
        nonlocal app_called
        app_called = True
        raise AssertionError("cache hit should not call downstream app")

    messages = await _call_demo_cache(demo_module.DemoResponseCache(app))

    assert app_called is False
    assert messages[0]["status"] == 200
    assert (b"content-type", b"application/json") in messages[0]["headers"]
    assert (b"content-encoding", b"gzip") in messages[0]["headers"]
    assert (b"cache-control", b"public, max-age=60") in messages[0]["headers"]
    assert (b"etag", b'"abc123"') in messages[0]["headers"]
    assert (b"x-demo-cache", b"HIT") in messages[0]["headers"]
    assert messages[1]["body"] == b"compressed-body"
    assert cache.set.await_count == 0


@pytest.mark.anyio
async def test_demo_cache_does_not_store_set_cookie_responses(monkeypatch):
    cache = _make_cache(get_side_effect=[None, None])
    monkeypatch.setattr(demo_module, "get_cache", lambda: cache)
    monkeypatch.setattr(demo_module, "RedLock", _NoopRedLock)

    async def app(scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"set-cookie", b"session=abc; HttpOnly"),
                    (b"cache-control", b"no-store"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": b'{"ok": true}'})

    messages = await _call_demo_cache(demo_module.DemoResponseCache(app))

    assert messages[0]["status"] == 200
    assert (b"set-cookie", b"session=abc; HttpOnly") in messages[0]["headers"]
    assert (b"x-demo-cache", b"MISS") in messages[0]["headers"]
    assert cache.set.await_count == 0


@pytest.mark.anyio
async def test_demo_cache_preserves_downstream_exceptions(monkeypatch):
    cache = _make_cache(get_side_effect=[None, None])
    monkeypatch.setattr(demo_module, "get_cache", lambda: cache)
    monkeypatch.setattr(demo_module, "RedLock", _NoopRedLock)

    app_called = 0

    async def app(scope, receive, send):
        nonlocal app_called
        app_called += 1
        raise ValueError("downstream failed")

    with pytest.raises(ValueError, match="downstream failed"):
        await _call_demo_cache(demo_module.DemoResponseCache(app))

    assert app_called == 1


@pytest.mark.anyio
async def test_demo_cache_logs_and_swallows_lock_release_failures(monkeypatch, caplog):
    """Unlock runs after the response is already fully sent, so a release
    failure (e.g. a Redis blip) must be logged and swallowed, not raised -
    raising here would replace a perfectly good response with a server error."""
    cache = _make_cache(get_side_effect=[None, None])
    monkeypatch.setattr(demo_module, "get_cache", lambda: cache)
    monkeypatch.setattr(demo_module, "RedLock", _FailingExitRedLock)

    app_called = 0

    async def app(scope, receive, send):
        nonlocal app_called
        app_called += 1
        await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": b'{"ok": true}'})

    with caplog.at_level("WARNING", logger=demo_module.logger.name):
        messages = await _call_demo_cache(demo_module.DemoResponseCache(app))

    assert app_called == 1
    assert messages[0]["status"] == 200
    assert messages[1]["body"] == b'{"ok": true}'
    assert cache.set.await_count == 1
    assert "unlock failed" in caplog.text


@pytest.mark.anyio
async def test_demo_cache_propagates_downstream_exception_over_unlock_failure(monkeypatch, caplog):
    """A genuine downstream failure must still win even if unlock also fails -
    the unlock failure is logged, not raised in its place."""
    cache = _make_cache(get_side_effect=[None, None])
    monkeypatch.setattr(demo_module, "get_cache", lambda: cache)
    monkeypatch.setattr(demo_module, "RedLock", _FailingExitRedLock)

    async def app(scope, receive, send):
        raise ValueError("downstream failed")

    with caplog.at_level("WARNING", logger=demo_module.logger.name):
        with pytest.raises(ValueError, match="downstream failed"):
            await _call_demo_cache(demo_module.DemoResponseCache(app))

    assert "unlock failed" in caplog.text


def test_demo_sub_app_excludes_database_download():
    """download_input_database (inputs.py) zips and reads back the entire db4
    folder on every call - real disk I/O, not just an uncacheable response.
    Anonymous callers must not be able to trigger it at all, so it's excluded
    from the demo mount entirely rather than merely left uncached."""
    from cea.interfaces.dashboard.api.demo import app as demo_app

    paths = {route.path for route in demo_app.routes if hasattr(route, "path")}
    assert "/scenarios/{demo_id}/inputs/databases/download" not in paths


@pytest.mark.anyio
async def test_demo_cache_stops_buffering_once_size_limit_exceeded(monkeypatch):
    """Cacheability is revoked as soon as the buffered body crosses
    MAX_CACHEABLE_BYTES, so later chunks are never retained for caching - only
    the check point moves; the client still receives the full body untouched."""
    cache = _make_cache(get_side_effect=[None, None])
    monkeypatch.setattr(demo_module, "get_cache", lambda: cache)
    monkeypatch.setattr(demo_module, "RedLock", _NoopRedLock)
    monkeypatch.setattr(demo_module.DemoResponseCache, "MAX_CACHEABLE_BYTES", 10)

    async def app(scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send({"type": "http.response.body", "body": b"0123456789", "more_body": True})
        await send({"type": "http.response.body", "body": b"overflow"})

    messages = await _call_demo_cache(demo_module.DemoResponseCache(app))

    body_messages = [m for m in messages if m["type"] == "http.response.body"]
    assert b"".join(m["body"] for m in body_messages) == b"0123456789overflow"
    assert cache.set.await_count == 0


def test_unknown_demo_id_returns_404_from_http():
    client, demo_app, get_settings_fn = _make_demo_client({"city-a": "/data/city_a"})
    try:
        # reports static route: guarded by _demo_guard (no CEAScenario dependency)
        resp = client.get("/scenarios/nonexistent/reports/features")
        assert resp.status_code == 404
        # inputs static route: also guarded by _demo_guard
        resp2 = client.get("/scenarios/nonexistent/inputs/")
        assert resp2.status_code == 404
        # inputs scenario route: guarded by get_effective_scenario override
        resp3 = client.get("/scenarios/nonexistent/inputs/geojson/zone")
        assert resp3.status_code == 404
    finally:
        demo_app.dependency_overrides.pop(get_settings_fn, None)


def test_demo_sub_app_has_no_write_routes():
    """No mutating verbs (PUT, PATCH, DELETE) in the demo sub-app.

    POST is allowed only for map-layer parameter queries (choices, range,
    generate, check) which use a request body for filter params — same
    pattern as the normal routes. canvas/export is excluded because it
    re-renders plot cards via CEAConfig. reports/plot-custom is allowed
    because plot_dispatch restricts it to genuine Visualisation-category
    dashboard scripts (see plot_dispatch.py). Any other POST is unexpected.
    """
    from cea.interfaces.dashboard.api.demo import app as demo_app

    mutating_methods = {"PUT", "PATCH", "DELETE"}
    allowed_post_paths = {
        "/scenarios/{demo_id}/map_layers/{layer_category}/{layer_name}/{parameter}/choices",
        "/scenarios/{demo_id}/map_layers/{layer_category}/{layer_name}/{parameter}/range",
        "/scenarios/{demo_id}/map_layers/{layer_category}/{layer_name}/generate",
        "/scenarios/{demo_id}/map_layers/{layer_category}/{layer_name}/check",
        "/scenarios/{demo_id}/reports/plot-custom",
    }

    bad_routes = []
    for route in demo_app.routes:
        if not hasattr(route, "methods"):
            continue
        if route.methods & mutating_methods:
            bad_routes.append(route)
        elif "POST" in route.methods and route.path not in allowed_post_paths:
            bad_routes.append(route)

    assert bad_routes == [], (
        f"Demo sub-app must not expose mutating routes; found: {bad_routes}"
    )


def test_global_auth_guard_not_weakened():
    """The main app's require_authenticated must still reject anonymous callers in
    non-local mode — mounting the demo sub-app must not affect this."""
    from fastapi import Request
    from fastapi.exceptions import HTTPException

    from cea.interfaces.dashboard.dependencies import require_authenticated
    from cea.interfaces.dashboard.lib.database.models import LOCAL_USER_ID

    non_local = Settings.model_construct(local=False)
    scope = {
        "type": "http", "method": "GET", "path": "/api/project/",
        "query_string": b"", "headers": [],
    }
    request = Request(scope)
    with pytest.raises(HTTPException) as exc_info:
        require_authenticated(request, LOCAL_USER_ID, non_local)
    assert exc_info.value.status_code == 401

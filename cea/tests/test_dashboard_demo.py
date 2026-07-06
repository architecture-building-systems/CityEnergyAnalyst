"""Tests for the public demo sub-app — no monkeypatching; Settings passed directly."""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from cea.interfaces.dashboard.api.demo import require_public_demo_read
from cea.interfaces.dashboard.settings import Settings

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
    re-renders plot cards via CEAConfig. Any other POST is unexpected.
    """
    from cea.interfaces.dashboard.api.demo import app as demo_app

    mutating_methods = {"PUT", "PATCH", "DELETE"}
    allowed_post_paths = {
        "/scenarios/{demo_id}/map_layers/{layer_category}/{layer_name}/{parameter}/choices",
        "/scenarios/{demo_id}/map_layers/{layer_category}/{layer_name}/{parameter}/range",
        "/scenarios/{demo_id}/map_layers/{layer_category}/{layer_name}/generate",
        "/scenarios/{demo_id}/map_layers/{layer_category}/{layer_name}/check",
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

"""Guards against the mount-prefix / auth-literal drift the /api prefix removal
was exposed to: _PUBLIC_ROUTES and _PUBLIC_ROUTE_PREFIXES in dependencies.py are
plain string literals matched against request.url.path in require_authenticated
(see app.py's app-level dependency). Nothing previously asserted these literals
actually resolve against the real route table built by app.py's include_router
calls - a prefix change there with no matching update here would silently
de-publish token refresh/logout (a lockout) or re-gate token-authenticated
downloads behind a session cookie they're designed not to need, and nothing
would fail until it broke in production.

This imports the real cea.interfaces.dashboard.app module for its route table
only - it does not start the app (no TestClient context manager, no lifespan).
"""
from fastapi.routing import APIRoute, iter_route_contexts

import cea.interfaces.dashboard.app as dashboard_app_module
from cea.interfaces.dashboard.dependencies import _PUBLIC_ROUTES, _PUBLIC_ROUTE_PREFIXES


def _real_route_paths() -> set[str]:
    """Must walk routes via iter_route_contexts, not a plain isinstance(route,
    APIRoute) scan over app.routes: fastapi>=0.137 stores each include_router()
    call as a single lazily-resolved _IncludedRouter wrapper rather than
    flattening its routes into app.routes, so a plain scan silently sees
    nothing (see cea.interfaces.dashboard.api.demo._demo_route_prefixes for
    the same fix applied to the demo sub-app)."""
    return {
        ctx.path
        for ctx in iter_route_contexts(dashboard_app_module.app.routes)
        if isinstance(ctx.original_route, APIRoute)
    }


def test_public_routes_resolve_against_real_app():
    """Every exact _PUBLIC_ROUTES entry must be a real, currently-mounted route."""
    real_paths = _real_route_paths()
    missing = _PUBLIC_ROUTES - real_paths
    assert not missing, (
        f"_PUBLIC_ROUTES entries with no matching route in app.routes: {sorted(missing)}. "
        "These paths are exempted from auth by dependencies.py but don't resolve to "
        "anything - either the route was removed/renamed, or the literal is stale "
        "(e.g. left over from a router mount-prefix change)."
    )


def test_public_route_prefixes_resolve_against_real_app():
    """Every _PUBLIC_ROUTE_PREFIXES entry must match at least one real route,
    otherwise the exemption is dead and gates nothing."""
    real_paths = _real_route_paths()
    for prefix in _PUBLIC_ROUTE_PREFIXES:
        matches = [p for p in real_paths if p.startswith(prefix)]
        assert matches, (
            f"_PUBLIC_ROUTE_PREFIXES entry {prefix!r} matches no route in app.routes - "
            "the exemption is dead. If the underlying router's mount prefix changed, "
            "update this literal to match."
        )

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from cea.interfaces.dashboard.dependencies import _PUBLIC_ROUTES, require_authenticated
from cea.interfaces.dashboard.lib.database.models import LOCAL_USER_ID


def _make_request(path: str) -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_requires_authentication_by_default_in_non_local_mode(monkeypatch):
    from cea.interfaces.dashboard import dependencies as deps

    monkeypatch.setattr(deps, "settings", SimpleNamespace(local=False))
    request = _make_request("/api/inputs/buildings")

    with pytest.raises(HTTPException) as exc_info:
        require_authenticated(request=request, user_id=LOCAL_USER_ID)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Authentication required."


def test_public_routes_explicitly_opt_out_of_auth_in_non_local_mode(monkeypatch):
    from cea.interfaces.dashboard import dependencies as deps

    monkeypatch.setattr(deps, "settings", SimpleNamespace(local=False))

    for path in _PUBLIC_ROUTES:
        request = _make_request(path)
        # Public allowlist routes should bypass the global auth gate.
        require_authenticated(request=request, user_id=LOCAL_USER_ID)


def test_local_mode_bypasses_authentication_guard(monkeypatch):
    from cea.interfaces.dashboard import dependencies as deps

    monkeypatch.setattr(deps, "settings", SimpleNamespace(local=True))
    request = _make_request("/api/inputs/buildings")

    require_authenticated(request=request, user_id=LOCAL_USER_ID)

"""Tests for require_authenticated — no monkeypatching; Settings passed directly."""
import pytest
from fastapi import Request
from fastapi.exceptions import HTTPException

from cea.interfaces.dashboard.dependencies import require_authenticated, _PUBLIC_ROUTES
from cea.interfaces.dashboard.lib.database.models import LOCAL_USER_ID
from cea.interfaces.dashboard.settings import Settings

LOCAL = Settings.model_construct(local=True)
NON_LOCAL = Settings.model_construct(local=False)
AUTHENTICATED_USER = "user_abc123"
PUBLIC_PATH = next(iter(_PUBLIC_ROUTES))
PROTECTED_PATH = "/api/project/"


def _make_request(path: str) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "query_string": b"",
        "headers": [],
    }
    return Request(scope)


def test_local_mode_always_passes():
    require_authenticated(_make_request(PROTECTED_PATH), LOCAL_USER_ID, LOCAL)


def test_non_local_authenticated_user_passes():
    require_authenticated(_make_request(PROTECTED_PATH), AUTHENTICATED_USER, NON_LOCAL)


def test_non_local_unauthenticated_on_protected_path_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        require_authenticated(_make_request(PROTECTED_PATH), LOCAL_USER_ID, NON_LOCAL)
    assert exc_info.value.status_code == 401


def test_non_local_unauthenticated_on_public_path_passes():
    require_authenticated(_make_request(PUBLIC_PATH), LOCAL_USER_ID, NON_LOCAL)

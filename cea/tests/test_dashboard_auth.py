"""Tests for require_authenticated and get_project_root — no monkeypatching; Settings passed directly."""
import os

import pytest
from fastapi import Request
from fastapi.exceptions import HTTPException

from cea.interfaces.dashboard.dependencies import require_authenticated, get_project_root, _PUBLIC_ROUTES
from cea.interfaces.dashboard.lib.database.models import LOCAL_USER_ID
from cea.interfaces.dashboard.settings import Settings

LOCAL = Settings.model_construct(local=True)
NON_LOCAL = Settings.model_construct(local=False)
NON_LOCAL_WITH_ROOT = Settings.model_construct(local=False, project_root="/data/projects")
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
        require_authenticated(_make_request(PROTECTED_PATH), None, NON_LOCAL)
    assert exc_info.value.status_code == 401


def test_non_local_unauthenticated_on_public_path_passes():
    require_authenticated(_make_request(PUBLIC_PATH), None, NON_LOCAL)


def test_get_project_root_rejects_no_session_in_non_local_mode():
    """Anonymous callers on auth-exempt prefixes (e.g. /api/downloads/) must get a
    clean 401 here, not a TypeError from os.path.join(root, None)."""
    with pytest.raises(HTTPException) as exc_info:
        get_project_root(None, NON_LOCAL_WITH_ROOT)
    assert exc_info.value.status_code == 401


def test_get_project_root_joins_user_id_in_non_local_mode():
    expected = os.path.join("/data/projects", "user_abc123")
    assert get_project_root(AUTHENTICATED_USER, NON_LOCAL_WITH_ROOT) == expected

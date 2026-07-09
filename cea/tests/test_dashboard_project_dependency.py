"""Tests for the CEAProject dependency (api/utils.py) — mirrors the direct-call,
no-monkeypatching-of-Settings style used in test_dashboard_auth.py.

secure_path itself is monkeypatched here so these tests isolate the new
join/absolute-path/fallback logic in _resolve_project_from_headers from the
pre-existing, shared secure_path/global-Settings containment machinery (which
CEAScenario already relies on and is out of scope for this change).
"""
import pytest
from fastapi import HTTPException

import cea.interfaces.dashboard.api.utils as api_utils
from cea.interfaces.dashboard.api.utils import CEAScenarioHeaders
from cea.interfaces.dashboard.dependencies import CEALocalConfig


def _headers(project=None):
    return CEAScenarioHeaders(x_cea_project=project)


def _fake_local_config(project_path):
    """A CEALocalConfig instance built without disk I/O (bypasses __init__).

    Configuration overrides __getattr__/__setattr__ to route through
    self.sections, which doesn't exist on a bypassed instance — write
    directly to __dict__ to set .project without triggering that machinery.
    """
    config = object.__new__(CEALocalConfig)
    config.__dict__["project"] = project_path
    return config


# ---------------------------------------------------------------------------
# _resolve_project_from_headers
# ---------------------------------------------------------------------------


def test_relative_project_joined_with_root(monkeypatch):
    captured = {}

    def fake_secure_path(path, root=None):
        captured["path"] = path
        captured["root"] = root
        return path

    monkeypatch.setattr(api_utils, "secure_path", fake_secure_path)

    result = api_utils._resolve_project_from_headers(
        _headers("my-project"), config=None, project_root="/data/projects"
    )

    assert captured["path"] == "/data/projects/my-project"
    assert captured["root"] == "/data/projects"
    assert result == "/data/projects/my-project"


def test_absolute_project_rejected_when_root_enforced():
    with pytest.raises(HTTPException) as exc_info:
        api_utils._resolve_project_from_headers(
            _headers("/abs/path"), config=None, project_root="/data/projects"
        )
    assert exc_info.value.status_code == 400


def test_absolute_project_allowed_when_no_root_enforced(monkeypatch):
    monkeypatch.setattr(api_utils, "secure_path", lambda path, root=None: path)

    result = api_utils._resolve_project_from_headers(
        _headers("/abs/path"), config=None, project_root=None
    )

    assert result == "/abs/path"


def test_header_absent_local_mode_falls_back_to_config_project(monkeypatch):
    monkeypatch.setattr(api_utils, "secure_path", lambda path, root=None: path)
    config = _fake_local_config("/home/user/projects/demo")

    result = api_utils._resolve_project_from_headers(_headers(None), config=config, project_root=None)

    assert result == "/home/user/projects/demo"


def test_header_absent_non_local_mode_raises_400():
    # Any config that isn't a CEALocalConfig instance represents non-local (stateless) mode.
    with pytest.raises(HTTPException) as exc_info:
        api_utils._resolve_project_from_headers(_headers(None), config=object(), project_root=None)
    assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# _get_effective_project / require_exists behaviour
# ---------------------------------------------------------------------------


def test_get_effective_project_returns_existing_directory(tmp_path, monkeypatch):
    existing = tmp_path / "exists"
    existing.mkdir()
    monkeypatch.setattr(api_utils, "_resolve_project_from_headers", lambda *a, **k: str(existing))

    result = api_utils._get_effective_project(
        config=None, project_root=None, require_exists=True, cea_headers=_headers()
    )

    assert result == str(existing)


def test_get_effective_project_missing_directory_raises_404(tmp_path, monkeypatch):
    missing = tmp_path / "missing"
    monkeypatch.setattr(api_utils, "_resolve_project_from_headers", lambda *a, **k: str(missing))

    with pytest.raises(HTTPException) as exc_info:
        api_utils._get_effective_project(
            config=None, project_root=None, require_exists=True, cea_headers=_headers()
        )
    assert exc_info.value.status_code == 404


def test_get_effective_project_lenient_allows_missing_directory(tmp_path, monkeypatch):
    missing = tmp_path / "missing"
    monkeypatch.setattr(api_utils, "_resolve_project_from_headers", lambda *a, **k: str(missing))

    result = api_utils._get_effective_project(
        config=None, project_root=None, require_exists=False, cea_headers=_headers()
    )

    assert result == str(missing)

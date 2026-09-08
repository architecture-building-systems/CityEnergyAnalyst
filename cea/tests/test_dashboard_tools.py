"""Tests for the /tools API, in particular that POST .../save-config returns the
rebuilt tool state (matching GET /{tool_name} and /{tool_name}/default) instead of
just a bare success string, so callers can adopt the saved state directly instead of
issuing a follow-up GET.
"""
from __future__ import annotations

import shutil
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import cea.config
import cea.interfaces.dashboard.utils as dashboard_utils
from cea.interfaces.dashboard.api.tools import router as tools_router
from cea.interfaces.dashboard.dependencies import CEALocalConfig, get_cea_config, require_authenticated
from cea.interfaces.dashboard.settings import Settings, get_settings
from cea.tests.paths import REPO_ROOT

# weather-helper: a lightweight tool for this test -- its parameters are an IntegerParameter
# (year) and two statically-choiced ChoiceParameters, none of which scan scenario output
# directories or require zone/database scaffolding to deconstruct. Its one WeatherPathParameter
# (weather) reads the CEA package's bundled weather database, not scenario files.
TOOL_NAME = "weather-helper"


def _find_param(body: dict, name: str) -> dict:
    """Look up a parameter dict by name across both the flat `parameters` list and
    every category under `categorical_parameters` -- `year` (used below) is grouped
    under a "Parameters for pyepwmorph" category, not top-level."""
    for p in body["parameters"]:
        if p["name"] == name:
            return p
    for params in body["categorical_parameters"].values():
        for p in params:
            if p["name"] == name:
                return p
    raise AssertionError(f"parameter {name!r} not found in response body")


@pytest.fixture
def tools_api_fixture(monkeypatch):
    # secure_path() reads settings via a module-level get_settings() call rather than
    # FastAPI DI, so the dependency_overrides below don't reach it -- needs its own patch.
    test_settings = Settings(local=True, project_root=None)
    monkeypatch.setattr(dashboard_utils, "get_settings", lambda: test_settings)

    project_root = REPO_ROOT / ".tmp-tools-api" / uuid4().hex
    scenario_name = "baseline"
    (project_root / scenario_name).mkdir(parents=True, exist_ok=True)

    config = CEALocalConfig(cea.config.DEFAULT_CONFIG)
    config.project = str(project_root)
    config.scenario_name = scenario_name

    app = FastAPI(dependencies=[Depends(require_authenticated)])
    app.include_router(tools_router, prefix="/tools")
    app.dependency_overrides[get_cea_config] = lambda: config
    app.dependency_overrides[require_authenticated] = lambda: None
    app.dependency_overrides[get_settings] = lambda: test_settings

    yield TestClient(app, headers={
        "X-CEA-Project": str(project_root),
        "X-CEA-Scenario-Name": scenario_name,
    })

    shutil.rmtree(project_root, ignore_errors=True)


def test_save_config_persists_values(tools_api_fixture):
    client = tools_api_fixture

    response = client.post(f"/tools/{TOOL_NAME}/save-config", json={"year": 2050})
    assert response.status_code == 200

    get_response = client.get(f"/tools/{TOOL_NAME}")
    assert get_response.status_code == 200
    assert _find_param(get_response.json(), "year")["value"] == 2050


def test_save_config_returns_saved_state(tools_api_fixture):
    client = tools_api_fixture

    response = client.post(f"/tools/{TOOL_NAME}/save-config", json={"year": 2045})
    assert response.status_code == 200

    body = response.json()
    assert body["name"] == TOOL_NAME
    assert isinstance(body["parameters"], list)
    assert _find_param(body, "year")["value"] == 2045


def test_save_config_response_matches_get(tools_api_fixture):
    """The guarantee that makes it safe for a client to adopt the POST response
    directly instead of issuing a follow-up GET."""
    client = tools_api_fixture

    save_response = client.post(f"/tools/{TOOL_NAME}/save-config", json={"year": 2040})
    assert save_response.status_code == 200

    get_response = client.get(f"/tools/{TOOL_NAME}")
    assert get_response.status_code == 200

    assert save_response.json() == get_response.json()


def test_save_config_validation_error_returns_400(tools_api_fixture):
    client = tools_api_fixture

    response = client.post(f"/tools/{TOOL_NAME}/save-config", json={"year": "not-a-year"})
    assert response.status_code == 400
    assert "year" in response.json()["detail"]["field_errors"]

    # Config must be left unmodified by a rejected save.
    get_response = client.get(f"/tools/{TOOL_NAME}")
    assert _find_param(get_response.json(), "year")["value"] != "not-a-year"

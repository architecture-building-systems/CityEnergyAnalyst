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
import cea.scripts
from cea.config import WhatIfNameMultiChoiceParameter
from cea.interfaces.dashboard.api.tools import parameters_for_script, router as tools_router
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


def test_stale_whatif_selection_dropped_after_scenario_switch(tools_api_fixture, monkeypatch):
    """`what-if-name` (WhatIfNameMultiChoiceParameter) lives in the shared, non-scenario-scoped
    ~/cea.config, but its `_choices` are scanned from the *active* scenario's
    outputs/data/analysis/ directory. Selecting a what-if run under one scenario and then
    switching the active scenario elsewhere in the GUI (same Tool form stays mounted, only the
    X-CEA-Scenario-Name header changes) must not leave a stale selection the new scenario's
    choices reject -- that surfaced as a "not a valid choice" form validation error.
    """
    client = tools_api_fixture
    tool = "system-costs"  # [what-ifs] section: just `what-if-name`, nothing else to scaffold.

    # Simulate scenario A: a completed what-if run named "scenario-a-run" is available.
    monkeypatch.setattr(
        WhatIfNameMultiChoiceParameter, "_choices", property(lambda self: ["scenario-a-run"])
    )
    save_response = client.post(f"/tools/{tool}/save-config", json={"what-if-name": ["scenario-a-run"]})
    assert save_response.status_code == 200
    assert _find_param(save_response.json(), "what-if-name")["value"] == ["scenario-a-run"]

    # Switch to scenario B (no save -- just a fresh GET, as if the GUI's active scenario
    # changed and the mounted Tool form refetched): scenario B has no such what-if run.
    monkeypatch.setattr(
        WhatIfNameMultiChoiceParameter, "_choices", property(lambda self: ["scenario-b-run"])
    )
    get_response = client.get(f"/tools/{tool}")
    assert get_response.status_code == 200

    what_if_param = _find_param(get_response.json(), "what-if-name")
    assert what_if_param["choices"] == ["scenario-b-run"]
    # The stale selection is dropped, not left dangling as an invalid choice.
    assert what_if_param["value"] == []


def _all_params(body: dict) -> list[dict]:
    return list(body["parameters"]) + [
        p for params in body["categorical_parameters"].values() for p in params
    ]


def _assert_multichoice_values_consistent(tool: str, body: dict) -> None:
    """`normalize_choice_value` is only applied to MultiChoiceParameter values in
    deconstruct_parameters (see the comment there for why single-choice is deliberately
    left untouched): every entry of a multi-choice parameter's `value` list must be a
    member of its own `choices`. `choices` given as a dict (WeatherPathParameter/
    DatabasePathParameter) never applies to a MultiChoiceParameter and is skipped."""
    for p in _all_params(body):
        value = p.get("value")
        choices = p.get("choices")
        if isinstance(value, list) and isinstance(choices, list):
            for v in value:
                assert v in choices, (
                    f"{tool}.{p['name']}: {v!r} not in choices {choices!r}"
                )


# Every tool registered for the dashboard interface -- the full real surface
# normalize_choice_value now runs against on every GET/save-config/default response,
# not just the two tools exercised by name above.
_ALL_DASHBOARD_TOOLS = [
    script.name
    for script in cea.scripts.for_interface("dashboard", plugins=[])
]


def test_build_tool_properties_smoke_all_dashboard_tools(tools_api_fixture):
    """No dashboard tool's GET may 500, and no multi-choice parameter may come back with
    a value outside its own choices, across every real tool definition in the app -- not
    just the couple of tools the targeted tests above happen to cover. A fresh, empty
    scenario (no zone/database/output files at all) is the worst case for `_choices`
    implementations that scan scenario-relative disk state, so this doubles as a
    robustness check independent of the normalize_choice_value change."""
    client = tools_api_fixture
    for tool in _ALL_DASHBOARD_TOOLS:
        response = client.get(f"/tools/{tool}")
        assert response.status_code == 200, f"{tool}: {response.text}"
        _assert_multichoice_values_consistent(tool, response.json())


def test_build_tool_properties_smoke_with_poisoned_choice_values(tools_api_fixture):
    """Simulate every choice-backed parameter, across every dashboard tool, holding a
    value left over from an unrelated context (bypassing `.set()`'s own `encode()`
    validation, the same way a value saved under a different scenario -- or an older,
    since-removed choice -- would arrive at decode time). No unhandled exception may
    result anywhere, and a poisoned MULTI-choice value must never surface (it's filtered).
    A poisoned SINGLE-choice value passing through untouched is expected, not a failure --
    see the comment in deconstruct_parameters for why single-choice values are
    deliberately left alone.
    """
    client = tools_api_fixture
    config = client.app.dependency_overrides[get_cea_config]()
    poison = "totally-invalid-value-should-never-surface"

    for tool in _ALL_DASHBOARD_TOOLS:
        for parameter in parameters_for_script(tool, config):
            if isinstance(parameter, cea.config.ChoiceParameterBase):
                config.user_config.set(parameter.section.name, parameter.name, poison)

    for tool in _ALL_DASHBOARD_TOOLS:
        response = client.get(f"/tools/{tool}")
        assert response.status_code == 200, f"{tool}: {response.text}"
        body = response.json()
        _assert_multichoice_values_consistent(tool, body)
        for p in _all_params(body):
            value = p.get("value")
            if isinstance(value, list):
                assert poison not in value, (
                    f"{tool}.{p['name']}: poisoned value leaked through a multi-choice field"
                )


def test_generation_parameter_no_choices_does_not_crash(tools_api_fixture):
    """GenerationParameter (non-nullable single ChoiceParameter, per default.config) has
    no choices at all on a fresh scenario -- no optimisation has run yet, and its own
    decode() returns None gracefully (no raise) in that case. Single-choice values are no
    longer passed through normalize_choice_value at all (see deconstruct_parameters), so
    this is really exercising deconstruct_parameters' own p.get() robustness -- confirms
    that stays true independent of the normalize_choice_value change.
    """
    client = tools_api_fixture
    # run-all-plots: cli/test-interface only, not GUI-reachable, but GET /tools/{tool}
    # doesn't gate by interface -- exercises the same [plots-optimization] section.
    response = client.get("/tools/run-all-plots")
    assert response.status_code == 200

    generation_param = _find_param(response.json(), "generation")
    assert generation_param["choices"] == []
    assert generation_param["value"] in (None, "")


def test_scenario_name_parameter_unlisted_value_not_corrupted(tools_api_fixture):
    """ScenarioNameParameter.decode() deliberately allows any string ("allow scenario
    name to be non-existing folder when reading from config file") -- its `choices` are a
    UI suggestion list (sibling scenarios found on disk), not an exhaustive valid set. A
    value referencing a real-but-currently-unlisted scenario (e.g. one in a different
    project) must survive a GET untouched, not get silently overwritten with an unrelated
    choices[0] -- the corruption risk that scoping normalize_choice_value to multi-choice
    only (in deconstruct_parameters) exists specifically to avoid.
    """
    client = tools_api_fixture
    tool = "import-from-rhino-gh"  # [from-rhino-gh] section: reference-scenario-name.

    config = client.app.dependency_overrides[get_cea_config]()
    param = next(
        p for p in parameters_for_script(tool, config) if p.name == "reference-scenario-name"
    )
    # Bypass encode()'s own (warning-only) check -- simulate a value saved while sibling
    # scenarios existed that have since been renamed/moved, or a cross-project reference.
    config.user_config.set(param.section.name, param.name, "a-legitimate-but-unlisted-scenario")

    response = client.get(f"/tools/{tool}")
    assert response.status_code == 200

    ref_param = _find_param(response.json(), "reference-scenario-name")
    assert ref_param["value"] == "a-legitimate-but-unlisted-scenario"

import os
from typing import Optional

import cea.config
import cea.inputlocator
from fastapi import Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Annotated

from cea.interfaces.dashboard.dependencies import CEAConfig, CEAProjectRoot
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
from cea.interfaces.dashboard.utils import secure_path

logger = getCEAServerLogger("cea-server-utils")


class ScenarioQuery(BaseModel):
    """
    Two mutually exclusive ways to identify a scenario for per-request override:
    - scenario_path: full absolute path (used for pathway child states)
    - project + scenario_name: normal scenario (must be provided together)
    If neither is provided the endpoint falls back to config.scenario.
    """
    model_config = {"extra": "forbid"}

    scenario_path: Optional[str] = Field(None, description="Full path to scenario (pathway mode)")
    project: Optional[str] = Field(None, description="Project directory; must be paired with scenario_name")
    scenario_name: Optional[str] = Field(None, description="Scenario name; must be paired with project")

    @model_validator(mode='after')
    def validate_groups(self) -> 'ScenarioQuery':
        if self.scenario_path is not None and (self.project is not None or self.scenario_name is not None):
            raise ValueError("scenario_path is mutually exclusive with project and scenario_name")
        if (self.project is None) != (self.scenario_name is None):
            raise ValueError("project and scenario_name must be provided together")
        return self

    def resolve(self, config, project_root=None) -> str:
        """Return the effective scenario path for this request.

        Priority: scenario_path > project+scenario_name > config.scenario.
        Never mutates config.
        """
        if self.scenario_path is not None:
            return secure_path(self.scenario_path)
        if self.project is not None and self.scenario_name is not None:
            p = self.project
            if project_root is not None and not p.startswith(project_root):
                p = os.path.join(project_root, p)
            return os.path.join(secure_path(p), validate_scenario_name(self.scenario_name))
        return str(config.scenario)


def validate_scenario_name(scenario_name: str) -> str:
    """Validate that scenario_name is a bare name with no path components."""
    scenario_name = os.path.normpath(scenario_name)
    if scenario_name == "." or scenario_name == ".." or os.path.basename(scenario_name) != scenario_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario name: {scenario_name}. Name should not contain path components.",
        )
    return scenario_name


def validate_scenario_name_or_subpath(scenario_name: str) -> str:
    """Validate that scenario_name is either a bare name or a project-
    relative sub-path (e.g. ``<scenario>/outputs/pathways/<name>/state_<year>``
    used by the canvas pathway-single columns). Rejects path traversal
    (``..``) and absolute paths but allows forward-slash separators so
    callers can target child scenarios that live inside a parent's
    ``outputs`` folder."""
    scenario_name = os.path.normpath(scenario_name)
    if (
        scenario_name == "."
        or scenario_name.startswith("..")
        or os.path.isabs(scenario_name)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario name: {scenario_name}. Path traversal not allowed.",
        )
    return scenario_name


def split_scenario_subpath(scenario_name: str, project: str) -> tuple:
    """If ``scenario_name`` is a project-relative sub-path, join it with
    ``project`` and split into ``(project_dir, basename)`` so callers
    can set ``config.project`` / ``config.scenario_name`` to bare
    values. Otherwise returns ``(project, scenario_name)`` unchanged.

    Used by endpoints that accept the canvas pathway-single columns'
    child-state paths (``<scenario>/outputs/pathways/<name>/state_<year>``)
    and need a bare scenario name downstream.
    """
    if scenario_name and os.sep in scenario_name:
        full_path = os.path.join(project, scenario_name)
        return os.path.dirname(full_path), os.path.basename(full_path)
    return project, scenario_name


def deconstruct_parameters(p: cea.config.Parameter, config=None):
    params = {'name': p.name, 'type': type(p).__name__, 'nullable': p.nullable, 'help': p.help}
    try:
        if isinstance(p, cea.config.BuildingsParameter):
            params['value'] = []
        else:
            params["value"] = p.get()
    except (cea.ConfigError, ValueError) as e:
        print(e)
        params["value"] = ""

    if isinstance(p, cea.config.ChoiceParameterBase):
        params['choices'] = p._choices

    if isinstance(p, cea.config.WeatherPathParameter):
        locator = cea.inputlocator.InputLocator(config.scenario)
        params['choices'] = {wn: locator.get_weather(
            wn) for wn in locator.get_weather_names()}

    elif isinstance(p, cea.config.DatabasePathParameter):
        params['choices'] = p._choices

    if hasattr(p, "_extensions") or hasattr(p, "extensions"):
        params["extensions"] = getattr(p, "_extensions", None) or getattr(p, "extensions")

    # Add GUI metadata hints
    params["needs_validation"] = _should_validate(p)

    # Add depends_on information (new semantic dependency system)
    if hasattr(p, 'depends_on') and p.depends_on:
        params["depends_on"] = p.depends_on
    else:
        params["depends_on"] = None

    return params


def _should_validate(p: cea.config.Parameter) -> bool:
    """
    Determine if a parameter needs backend validation on change.
    This is a GUI optimization hint - doesn't affect core validation logic.
    """
    # Parameters with filesystem collision checks
    if isinstance(p, cea.config.NetworkLayoutNameParameter):
        return True

    if isinstance(p, cea.config.WhatIfNameParameter):
        return True

    if isinstance(p, cea.config.PhasingPlanChoiceParameter):
        return True

    # Add more parameter types here as needed
    # if isinstance(p, cea.config.SomeOtherComplexParameter):
    #     return True

    # By default, no explicit validation needed
    return False


def get_effective_scenario(
    config: CEAConfig,
    project_root: CEAProjectRoot,
    scenario: Annotated[ScenarioQuery, Query()],
) -> str:
    logger.debug("Resolving scenario: %s", scenario.model_dump(exclude_none=True))
    path = scenario.resolve(config, project_root)
    if not os.path.isdir(path):
        logger.error("Scenario directory not found: %s", path)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scenario not found.",
        )
    return path


CEAScenario = Annotated[str, Depends(get_effective_scenario)]

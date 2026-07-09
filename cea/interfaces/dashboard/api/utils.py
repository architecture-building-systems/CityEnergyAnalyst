# Scenario/project context is passed via X-CEA-* request headers. Header names: X-CEA-Project,
# X-CEA-Scenario-Name, X-CEA-Child-Scenario (logical token "<pathway_name>/<year>"). If no
# header is supplied the endpoint falls back to config.scenario / config.project (local mode only).
# Future phase (separate plan): PUT /projects/{id}/scenarios/{name}/... — requires a projects
# table mapping project_id → path for both local and non-local modes. See AGENTS.md for details.

import os
from typing import Optional

import cea.config
import cea.inputlocator
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel
from typing_extensions import Annotated

from cea.interfaces.dashboard.dependencies import CEAConfig, CEALocalConfig, CEAProjectRoot
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
from cea.interfaces.dashboard.utils import secure_path

logger = getCEAServerLogger("cea-server-utils")

_CHILD_SCENARIO_SEP = "/"


def _parse_child_scenario_token(token: str) -> tuple:
    """Parse a logical child-scenario token ``<pathway_name>/<year>`` into its components.

    Returns ``(pathway_name, year_int)``. Raises ``ValueError`` on malformed input.
    """
    parts = token.split(_CHILD_SCENARIO_SEP, 1)
    if len(parts) != 2:
        raise ValueError(
            f"Invalid child_scenario '{token}': expected '<pathway_name>/<year>'."
        )
    pathway_name, year_str = parts
    if not pathway_name:
        raise ValueError(
            f"Invalid child_scenario '{token}': pathway_name must not be empty."
        )
    try:
        year = int(year_str)
    except ValueError:
        raise ValueError(
            f"Invalid child_scenario '{token}': year must be an integer, got '{year_str}'."
        )
    return pathway_name, year


def _resolve_scenario_from_headers(cea_headers: 'CEAScenarioHeaders', config, project_root) -> str:
    """Return the effective scenario path from X-CEA-* headers.

    Falls back to config.scenario in local mode only. Non-local mode requires
    explicit headers — config.scenario would resolve to DEFAULT_CONFIG's path
    which is meaningless in a stateless cloud context.
    """
    project = cea_headers.x_cea_project
    scenario_name = cea_headers.x_cea_scenario_name
    child_scenario = cea_headers.x_cea_child_scenario

    if project is not None and scenario_name is not None:
        p = project
        if project_root is not None:
            if os.path.isabs(p):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="project must be a relative path when project_root is enforced.",
                )
            p = os.path.join(project_root, p)
        project_path = secure_path(p, root=project_root)
        parent_path = os.path.join(project_path, validate_scenario_name(scenario_name))
        parent_path = secure_path(parent_path, root=project_root)

        if child_scenario is not None:
            try:
                pathway_name, year = _parse_child_scenario_token(child_scenario)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
                ) from exc
            from cea.datamanagement.district_pathways.pathway_state import validate_pathway_name
            try:
                pathway_name = validate_pathway_name(pathway_name)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
                ) from exc
            locator = cea.inputlocator.InputLocator(parent_path)
            child_path = locator.get_state_in_time_scenario_folder(pathway_name, year)
            return secure_path(child_path, root=project_root)

        return parent_path

    if not isinstance(config, CEALocalConfig):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scenario context required: send X-CEA-Project and X-CEA-Scenario-Name headers.",
        )
    return secure_path(str(config.scenario), root=project_root)


def _resolve_project_from_headers(cea_headers: 'CEAScenarioHeaders', config, project_root) -> str:
    """Return the effective project path from the X-CEA-Project header.

    Falls back to config.project in local mode only. Non-local mode requires
    an explicit header — config.project would resolve to DEFAULT_CONFIG's path
    which is meaningless in a stateless cloud context.
    """
    project = cea_headers.x_cea_project

    if project is not None:
        p = project
        if project_root is not None:
            if os.path.isabs(p):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="project must be a relative path when project_root is enforced.",
                )
            p = os.path.join(project_root, p)
        return secure_path(p, root=project_root)

    if not isinstance(config, CEALocalConfig):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project context required: send an X-CEA-Project header.",
        )
    return secure_path(str(config.project), root=project_root)


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


class CEAScenarioHeaders(BaseModel):
    x_cea_project: Optional[str] = None
    x_cea_scenario_name: Optional[str] = None
    x_cea_child_scenario: Optional[str] = None


def _get_effective_scenario(
    config: CEAConfig,
    project_root: CEAProjectRoot,
    require_exists: bool,
    cea_headers: CEAScenarioHeaders,
) -> str:
    path = _resolve_scenario_from_headers(cea_headers, config, project_root)
    logger.debug("Resolving scenario: %s", path)
    if require_exists and not os.path.isdir(path):
        logger.error("Scenario directory not found: %s", path)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found.",
        )
    return path


def get_effective_scenario(
    config: CEAConfig,
    project_root: CEAProjectRoot,
    cea_headers: Annotated[CEAScenarioHeaders, Header()],
) -> str:
    return _get_effective_scenario(config, project_root, require_exists=True, cea_headers=cea_headers)


def get_effective_scenario_lenient(
    config: CEAConfig,
    project_root: CEAProjectRoot,
    cea_headers: Annotated[CEAScenarioHeaders, Header()],
) -> str:
    return _get_effective_scenario(config, project_root, require_exists=False, cea_headers=cea_headers)


CEAScenario = Annotated[str, Depends(get_effective_scenario)]
CEAScenarioLenient = Annotated[str, Depends(get_effective_scenario_lenient)]


def _get_effective_project(
    config: CEAConfig,
    project_root: CEAProjectRoot,
    require_exists: bool,
    cea_headers: CEAScenarioHeaders,
) -> str:
    path = _resolve_project_from_headers(cea_headers, config, project_root)
    logger.debug("Resolving project: %s", path)
    if require_exists and not os.path.isdir(path):
        logger.error("Project directory not found: %s", path)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    return path


def get_effective_project(
    config: CEAConfig,
    project_root: CEAProjectRoot,
    cea_headers: Annotated[CEAScenarioHeaders, Header()],
) -> str:
    return _get_effective_project(config, project_root, require_exists=True, cea_headers=cea_headers)


def get_effective_project_lenient(
    config: CEAConfig,
    project_root: CEAProjectRoot,
    cea_headers: Annotated[CEAScenarioHeaders, Header()],
) -> str:
    return _get_effective_project(config, project_root, require_exists=False, cea_headers=cea_headers)


CEAProject = Annotated[str, Depends(get_effective_project)]
CEAProjectLenient = Annotated[str, Depends(get_effective_project_lenient)]

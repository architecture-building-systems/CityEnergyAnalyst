# Scenario/project context is passed via X-CEA-* request headers. Header names: X-CEA-Project,
# X-CEA-Scenario-Name, X-CEA-Child-Scenario (logical token "<pathway_name>/<year>"). If no
# header is supplied the endpoint falls back to config.scenario / config.project (local mode only).
# Future phase (separate plan): PUT /projects/{id}/scenarios/{name}/... — requires a projects
# table mapping project_id → path for both local and non-local modes. See AGENTS.md for details.

import configparser
import os
from typing import Any, Optional

import cea.config
import cea.inputlocator
import cea.scripts
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel
from typing_extensions import Annotated

from cea.interfaces.dashboard.dependencies import CEAConfig, CEALocalConfig, CEAProjectRoot, CEAUserID, \
    get_or_create_project_id
from cea.interfaces.dashboard.lib.database.session import SessionDep
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
        if os.path.isabs(p) and not isinstance(config, CEALocalConfig):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="project must be a relative path in non-local mode.",
            )
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
        if os.path.isabs(p) and not isinstance(config, CEALocalConfig):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="project must be a relative path in non-local mode.",
            )
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


def _missing_source_database(
    p: cea.config.Parameter, config, locator: cea.inputlocator.InputLocator | None = None
) -> str | None:
    """The database file this parameter needs, if it is absent from the scenario.

    Only `.requires-database` is checked here (inputs that are only meaningful when that
    database exists, e.g. a layer thickness beside a material dropdown) -- not `.locator`.
    `.locator` names the method `ChoiceParameterBase`/`ColumnChoicesMixin` calls to build
    a parameter's own choices, sometimes with required `.kwargs` (see `type-pvpanel`); it
    is not always a zero-argument call, and not always a file (e.g. a pathway container
    folder that legitimately does not exist yet on a fresh scenario). A choice parameter's
    own `_choices` failing is already reported by the caller below. A scenario whose
    `.requires-database` file is missing is a normal situation, not an error -- the form
    drops those inputs and says why, rather than failing to load at all.
    """
    if config is None:
        return None
    try:
        locator_name = p.config.default_config.get(
            p.section.name, f"{p.name}.requires-database"
        )
    except (configparser.NoSectionError, configparser.NoOptionError):
        return None
    if locator is None:
        locator = cea.inputlocator.InputLocator(config.scenario)
    method = getattr(locator, locator_name, None)
    if method is None:
        return None
    try:
        path = method()
    except Exception as e:
        logger.warning(
            "Could not resolve %s.requires-database (%s) for %s: %s",
            p.name, locator_name, p.fqname, e,
        )
        return None
    if not os.path.exists(path):
        return path
    return None


def normalize_choice_value(param: cea.config.ChoiceParameterBase, value: Any, choices: list[str]) -> Any:
    """Coerce a stored choice-parameter value against a freshly-computed `choices` list.

    `value` lives in the shared, non-scenario-scoped `~/cea.config` (see `Configuration.__init__`),
    while a scenario-relative parameter's `choices` (e.g. `WhatIfNameMultiChoiceParameter`, scanning
    `outputs/data/analysis/`) are recomputed per request from whichever scenario is currently active.
    Switching scenarios can therefore leave a value selected that the new scenario's choices no
    longer contain. Multi-choice values are silently filtered down to the valid subset; a single
    choice value falls back to the first available choice (or `None` if nullable).
    """
    valid_choices = set(choices)
    is_multi_choice = isinstance(param, cea.config.MultiChoiceParameter)

    def _raise_missing_choices_error(reason: str) -> None:
        message = f"No choices available for non-nullable parameter {param.fqname} while {reason}."
        logger.error(message)
        raise ValueError(message)

    if is_multi_choice:
        if value is None:
            return []

        if isinstance(value, list):
            raw_values = value
        elif isinstance(value, str):
            raw_values = [v.strip() for v in value.split(',') if v.strip()]
        else:
            raw_values = [value]

        return [str(v).strip() for v in raw_values if str(v).strip() in valid_choices]

    if value is None:
        if param.nullable:
            return None
        if not choices:
            _raise_missing_choices_error("normalising a missing value")
        return choices[0]

    normalized_value = str(value).strip()
    if param.nullable and normalized_value == '':
        return None

    if normalized_value in valid_choices:
        return normalized_value

    if not choices and not param.nullable:
        _raise_missing_choices_error(f"normalising value {normalized_value}")

    return choices[0] if choices else None


def deconstruct_parameters(
    p: cea.config.Parameter, config=None, locator: cea.inputlocator.InputLocator | None = None
):
    """Serialise one config Parameter into the GUI's parameter-metadata dict: current
    value, choices (if any), and an `unavailable` reason when its source database is
    missing or its choices failed to load. `locator`, if given, is reused for the
    `.requires-database` check instead of constructing a new one per parameter."""
    params = {'name': p.name, 'type': type(p).__name__, 'nullable': p.nullable, 'help': p.help}
    try:
        if isinstance(p, cea.config.BuildingsParameter):
            params['value'] = []
        else:
            params["value"] = p.get()
    except (cea.ConfigError, ValueError, OSError) as e:
        # OSError (e.g. FileNotFoundError): some ColumnChoicesMixin-backed multi-choice
        # parameters (empty_means_all=True) decode '' by evaluating their own `_choices`,
        # which reads a database CSV via the locator -- on a fresh scenario with no
        # database yet, that raises here rather than being caught by the `_choices`
        # try/except below (this happens inside decode(), before choices are even
        # requested for this parameter). Pre-existing gap, unrelated to choice-value
        # normalisation: this must not fail the whole tool-properties response either.
        logger.warning("Could not get value for %s: %s", p.fqname, e)
        params["value"] = ""

    missing_database = _missing_source_database(p, config, locator)
    if missing_database is not None:
        # The form hides these inputs and reports the missing file once, instead of the
        # whole tool-properties request failing on the first unreadable database. The path
        # is scenario-relative: it is sent to the browser, and an absolute server
        # filesystem path has no business there.
        relative_missing_database = (
            os.path.relpath(missing_database, config.scenario) if config else missing_database
        )
        params["unavailable"] = {
            "reason": f"{os.path.basename(missing_database)} is not in this scenario's database.",
            "missing_file": relative_missing_database,
        }

    if isinstance(p, cea.config.ChoiceParameterBase):
        if missing_database is not None:
            # Already explained above; reading the options would just fail again.
            params['choices'] = []
        else:
            try:
                params['choices'] = p._choices
            except Exception as e:
                logger.warning("Could not build choices for %s: %s", p.fqname, e)
                params['choices'] = []
                params["unavailable"] = {
                    "reason": f"Options for this input could not be read: {e}",
                    "missing_file": None,
                }

        # `value` may predate the choices just computed above -- e.g. a
        # WhatIfNameMultiChoiceParameter selection saved while a different scenario was
        # active. Multi-choice only: normalize_choice_value's multi-choice branch only ever
        # narrows the list to the currently-valid subset, which is always safe. Its
        # single-choice branch can fall back to `choices[0]` when the value doesn't match --
        # correct for POST .../parameter-metadata's original use (a value just invalidated
        # by the user's own live edit of a field it depends on), but wrong here: some single
        # ChoiceParameterBase subclasses (e.g. ScenarioNameParameter, whose decode()
        # deliberately allows any string -- "allow scenario name to be non-existing folder
        # when reading from config file") treat `choices` as a UI suggestion list, not an
        # exhaustive valid set. Applying the same fallback there would silently overwrite a
        # legitimate but currently-unlisted value with an unrelated `choices[0]` on every
        # GET, and a subsequent Save would persist that corruption.
        if isinstance(p, cea.config.MultiChoiceParameter):
            try:
                params['value'] = normalize_choice_value(p, params['value'], params['choices'])
            except ValueError as e:
                logger.warning("Could not normalise value for %s: %s", p.fqname, e)

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

    # WhatIfNameChoiceParameter / WhatIfNameMultiChoiceParameter (WhatIfNameChoicesMixin):
    # which what-if output this dropdown requires (final_energy/emissions/costs/
    # heat_rejection), so the GUI can name the right tool in its "no choices" message
    # instead of hardcoding "Run Final Energy first" for every mode.
    if isinstance(p, cea.config.WhatIfNameChoicesMixin):
        params["mode"] = p.mode

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


def script_takes_scenario_path(script_name: str, config: cea.config.Configuration) -> bool:
    """True if ``script_name`` declares a parameter named ``scenario`` that is a
    :py:class:`cea.config.ScenarioParameter` -- i.e. the reserved "current active
    scenario" path.

    Raises cea.ScriptNotFoundException for unknown script names.
    """
    script = cea.scripts.by_name(script_name, plugins=config.plugins)
    try:
        for _, parameter in config.matching_parameters(script.parameters):
            if parameter.name == "scenario":
                return isinstance(parameter, cea.config.ScenarioParameter)
    except KeyError:
        # scripts.yml (or a plugin's) references a section/parameter this config
        # doesn't know about -- treat as "no scenario parameter" and let the normal
        # parameter-validation path surface the real error.
        logger.warning("Could not expand parameters for script %s", script_name)
        return False
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


def get_effective_scenario_optional(
    config: CEAConfig,
    project_root: CEAProjectRoot,
    cea_headers: Annotated[CEAScenarioHeaders, Header()],
) -> Optional[str]:
    """Like ``get_effective_scenario_lenient``, but returns ``None`` instead of raising
    400 when the request carries no scenario context at all.

    For endpoints whose need for a scenario depends on the request payload rather than
    the route itself (POST /server/jobs/new: only scripts with a ScenarioParameter need
    one), so the caller can decide whether the absence is actually an error. Malformed
    context (an absolute project in non-local mode, a path-traversal attempt, a bad
    child-scenario token, ...) still raises 400 via `_resolve_scenario_from_headers` --
    only a *missing* project/scenario-name pair in non-local mode short-circuits to None.
    """
    if cea_headers.x_cea_project is None or cea_headers.x_cea_scenario_name is None:
        if not isinstance(config, CEALocalConfig):
            return None
    return _get_effective_scenario(config, project_root, require_exists=False, cea_headers=cea_headers)


CEAScenarioOptional = Annotated[Optional[str], Depends(get_effective_scenario_optional)]


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


async def get_project_id(
    project_path: CEAProjectLenient,
    owner_id: CEAUserID,
    session: SessionDep,
) -> str:
    """Resolve the DB project id for the request's effective project (X-CEA-Project header,
    falling back to config.project in local mode only — see _resolve_project_from_headers).
    Creates the Project row the first time this project path is seen."""
    return await get_or_create_project_id(project_path, owner_id, session)


CEAProjectID = Annotated[str, Depends(get_project_id)]

import os
from collections import defaultdict
from itertools import groupby
from typing import Dict, Any, List, Optional
import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

import cea.config
import cea.inputlocator
import cea.scripts
from cea.schemas import schemas
from .utils import deconstruct_parameters, validate_scenario_name
from cea.interfaces.dashboard.utils import secure_path
from cea.interfaces.dashboard.dependencies import CEAConfig, CEADatabaseConfig, CEASeverDemoAuthCheck, CEAProjectRoot

router = APIRouter()
logger = logging.getLogger(__name__)


def _normalize_choice_value(param: cea.config.ChoiceParameterBase, value: Any, choices: list[str]) -> Any:
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


def validate_parameter(parameter, value, parameter_name: str | None = None) -> tuple[bool, str | None]:
    """
    Validate a parameter value using its encode() method.

    Returns:
        tuple[bool, str | None]: (is_valid, error_message)
    """
    try:
        parameter.encode(value)
        return True, None
    except ValueError as e:
        error_message = str(e)
        logger.error(f"Validation failed for {parameter_name or parameter.name}: {error_message}")
        return False, error_message
    except Exception as e:
        error_message = f"Validation error: {str(e)}"
        logger.error(f"Unexpected validation error for {parameter_name or parameter.name}: {error_message}")
        return False, error_message


def validate_and_apply_parameters(
    candidates: list[tuple[cea.config.Parameter, Any]],
    set_empty: list | None = None,
) -> None:
    """
    Validate a list of (parameter, value) pairs and apply them atomically.

    Raises ValueError with a dict of field errors if any value fails validation.
    Only calls parameter.set() / parameter.set_empty() after all values pass.

    Args:
        candidates: List of (parameter, value) pairs to validate then set.
        set_empty: Optional list of parameters to call set_empty() on (no validation needed).
    """
    field_errors = {}
    to_set = []

    for parameter, value in candidates:
        is_valid, error_message = validate_parameter(parameter, value)
        if not is_valid:
            field_errors[parameter.name] = error_message
        else:
            to_set.append((parameter, value))

    if field_errors:
        raise ValueError(field_errors)

    for parameter in (set_empty or []):
        parameter.set_empty()
    for parameter, value in to_set:
        parameter.set(value)


class ToolDescription(BaseModel):
    name: str
    label: str
    description: str
    short_description: Optional[str] = None

class ToolProperties(ToolDescription):
    category: str
    categorical_parameters: Dict[str, List[Dict]]
    parameters: List[Dict]


@router.get('/')
async def get_tool_list(config: CEAConfig) -> Dict[str, List[ToolDescription]]:
    # TODO: Add plugin support
    tools = cea.scripts.for_interface('dashboard', plugins=config.plugins)
    result = dict()
    for category, group in groupby(tools, lambda t: t.category):
        result[category] = [
            ToolDescription(name=t.name, label=t.label, description=t.description, short_description=t.short_description) for t in group
        ]
    return result


@router.get('/{tool_name}')
async def get_tool_properties(config: CEAConfig, project_root: CEAProjectRoot, tool_name: str,
                               project: Optional[str] = None,
                               scenario_name: Optional[str] = None) -> ToolProperties:
    # TODO: Add plugin support

    # Set project and scenario on config to ensure parameters that depend
    # on them are constructed correctly. Skip BOTH overrides when the
    # pathway viewer is active — config.scenario already points to the
    # state folder (set by switchToChildScenario), and overriding either
    # config.project or config.scenario_name would break that path.
    in_child_scenario = cea.inputlocator.InputLocator.is_pathway_child_scenario(
        config.scenario,
    )
    if not in_child_scenario:
        if project is not None:
            if project_root is not None and not project.startswith(project_root):
                project = os.path.join(project_root, project)
            config.project = secure_path(project)
        if scenario_name is not None:
            config.scenario_name = validate_scenario_name(scenario_name)

    script = cea.scripts.by_name(tool_name, plugins=config.plugins)

    parameters = []
    categories = defaultdict(list)
    for _, parameter in config.matching_parameters(script.parameters):
        parameter_dict = deconstruct_parameters(parameter, config)

        if parameter.category:
            categories[parameter.category].append(parameter_dict)
        else:
            parameters.append(parameter_dict)

    out = ToolProperties(
        name=tool_name,
        label=script.label,
        description=script.description,
        short_description=script.short_description,
        category=script.category,
        categorical_parameters=categories,
        parameters=parameters,
    )

    return out


@router.post('/{tool_name}/default', dependencies=[CEASeverDemoAuthCheck])
async def restore_default_config(config: CEAConfig, tool_name: str):
    """Restore the default configuration values for the CEA"""
    default_config = cea.config.Configuration(config_file=cea.config.DEFAULT_CONFIG)
    # Ensure that parameters that depend on scenario files will be parsed correctly
    default_config.scenario = config.scenario

    candidates = []
    set_empty = []

    for parameter in parameters_for_script(tool_name, config):
        if parameter.name == 'scenario':
            continue

        default_value = default_config.sections[parameter.section.name].parameters[parameter.name].get()
        # Set empty string for non-nullable parameters with empty default values, bypassing validation
        if not default_value and default_value is not False and default_value != 0 and not parameter.nullable:
            set_empty.append(parameter)
        else:
            candidates.append((parameter, default_value))

    try:
        validate_and_apply_parameters(candidates, set_empty)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={'message': 'Validation failed', 'field_errors': e.args[0]})

    if isinstance(config, CEADatabaseConfig):
        await config.save()
    else:
        config.save()

    return 'Success'


@router.post('/{tool_name}/save-config', dependencies=[CEASeverDemoAuthCheck])
async def save_tool_config(config: CEAConfig, tool_name: str, payload: Dict[str, Any]):
    """
    Save the configuration for this tool to the configuration file.
    Validates all parameters before saving and returns field-level errors if validation fails.
    """
    field_errors = {}

    # Validate all parameters first
    for parameter in parameters_for_script(tool_name, config):
        if parameter.name != 'scenario' and parameter.name in payload:
            value = payload[parameter.name]
            is_valid, error_message = validate_parameter(parameter, value)
            if not is_valid:
                field_errors[parameter.name] = error_message

    # If there are validation errors, return them without saving
    if field_errors:
        logger.error(f'[save_tool_config] Validation failed with {len(field_errors)} errors')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'message': 'Validation failed',
                'field_errors': field_errors
            }
        )

    # All parameters valid - set them
    for parameter in parameters_for_script(tool_name, config):
        if parameter.name != 'scenario' and parameter.name in payload:
            value = payload[parameter.name]
            parameter.set(value)

    if isinstance(config, CEADatabaseConfig):
        await config.save()
    else:
        config.save()
    return 'Success'


@router.post('/{tool_name}/validate-field')
async def validate_field(config: CEAConfig, tool_name: str, payload: Dict[str, Any]):
    """
    Validate a single field value using the parameter's encode() method.

    Payload should contain:
    - parameter_name: the name of the parameter to validate
    - value: the value to validate
    - form_values: dict of current form values to set on config before validation
    """
    parameter_name = payload.get('parameter_name')
    value = payload.get('value')
    form_values = payload.get('form_values', {})

    if not parameter_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="parameter_name is required")

    # Temporarily set form values on config to provide context for validation
    for param in parameters_for_script(tool_name, config):
        if param.name in form_values and param.name != parameter_name:
            try:
                logger.debug(f"[validate_field] Setting {param.name} = {form_values[param.name]}")
                param.set(form_values[param.name])
            except Exception as e:
                logger.error(f"[validate_field] Failed to set {param.name}: {e}")

    # Find the parameter to validate
    target_parameter = None
    for param in parameters_for_script(tool_name, config):
        if param.name == parameter_name:
            target_parameter = param
            break

    if not target_parameter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Parameter '{parameter_name}' not found")

    # Validate using encode() method
    is_valid, error_message = validate_parameter(target_parameter, value, parameter_name)
    result = {"valid": is_valid, "error": error_message}

    if is_valid:
        warnings = _collect_field_warnings(tool_name, parameter_name, value, config)
        if warnings:
            result["warnings"] = warnings

    return result


@router.post('/{tool_name}/parameter-metadata')
async def get_parameter_metadata(config: CEAConfig, tool_name: str, payload: Dict[str, Any]):
    """
    Get updated parameter metadata based on current form values.
    Does NOT save to config - uses temporary in-memory config state.

    Useful for updating dependent parameters when their dependencies change.
    For example, when network-type changes, network-layout choices need to update.

    Payload should contain:
    - form_values: dict of current form values
    - affected_parameters: optional list of parameter names to get metadata for
    """
    form_values = payload.get('form_values', {})
    affected_parameters = payload.get('affected_parameters', None)

    # Temporarily set form values on config (in-memory only, don't save)
    for param in parameters_for_script(tool_name, config):
        if param.name in form_values:
            try:
                logger.debug(f"[get_parameter_metadata] Setting {param.name} = {form_values[param.name]}")
                param.set(form_values[param.name])
            except Exception as e:
                logger.error(f"[get_parameter_metadata] Failed to set {param.name}: {e}")

    # TODO: Add plugin support
    script = cea.scripts.by_name(tool_name, plugins=config.plugins)

    # Build response with updated metadata
    result = {}
    for _, param in config.matching_parameters(script.parameters):
        # If affected_parameters specified, only include those
        if affected_parameters and param.name not in affected_parameters:
            continue

        # For choice-backed parameters, get updated choices and normalise the current value
        if isinstance(param, cea.config.ChoiceParameterBase):
            try:
                choices = param._choices  # type: ignore[attr-defined]
                current_value = _normalize_choice_value(param, param.get(), choices)

                result[param.name] = {
                    'choices': choices,
                    'value': current_value,
                }
                logger.debug(f"[get_parameter_metadata] {param.name}: {len(choices)} choices, value={current_value}")
            except Exception as e:
                logger.error(f"[get_parameter_metadata] Error getting metadata for {param.name}: {e}")

    logger.debug(f"[get_parameter_metadata] Returning metadata for {len(result)} parameters")
    return {'parameters': result}


@router.post('/{tool_name}/check')
async def check_tool_inputs(config: CEAConfig, tool_name: str, payload: Dict[str, Any]):
    candidates = [
        (parameter, payload[parameter.name])
        for parameter in parameters_for_script(tool_name, config)
        if parameter.name in payload and parameter.name != 'scenario'
    ]
    try:
        validate_and_apply_parameters(candidates)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={'message': 'Validation failed', 'field_errors': e.args[0]})

    # TODO: Add plugin support
    script = cea.scripts.by_name(tool_name, plugins=config.plugins)
    schema_data = schemas(config.plugins)

    script_suggestions = set()

    for method_name, path in script.missing_input_files(config):
        _script_suggestions = schema_data[method_name]['created_by'] if 'created_by' in schema_data[
            method_name] else None

        if _script_suggestions is not None:
            script_suggestions.update(_script_suggestions)

    if script_suggestions:
        scripts = []
        for script_suggestion in script_suggestions:
            _script = cea.scripts.by_name(script_suggestion, plugins=config.plugins)
            scripts.append({"label": _script.label, "name": _script.name})

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"message": "Missing input files",
                                    "script_suggestions": list(scripts)})

    # Collision warnings from the check-inputs path (Run button confirmation)
    warnings = []
    for field_name in ('network-name', 'what-if-name'):
        if field_name in payload:
            warnings.extend(
                _collect_field_warnings(tool_name, field_name, payload[field_name], config)
            )
    return {"warnings": warnings} if warnings else None


def _collect_field_warnings(tool_name, parameter_name, value, config):
    """Return structured ``{field, message}`` warnings for a single field.

    Centralises collision detection so ``validate_field`` and
    ``check_tool_inputs`` share one code path.
    """
    if isinstance(value, list):
        return []
    v = (value or '').strip()
    if not v:
        return []
    locator = cea.inputlocator.InputLocator(config.scenario)

    if tool_name == 'network-layout' and parameter_name == 'network-name':
        folder = locator.get_thermal_network_folder_network_name_folder(v)
        if os.path.isdir(folder):
            return [{
                "field": "network-name",
                "message": (
                    f"Network '{v}' already exists. "
                    f"Running will delete the existing network and create a new one."
                ),
            }]

    if tool_name == 'final-energy' and parameter_name == 'what-if-name':
        folder = locator.get_analysis_folder(v)
        if os.path.isdir(folder):
            return [{
                "field": "what-if-name",
                "message": (
                    f"What-if Scenario '{v}' already exists. "
                    f"Running will delete the entire What-if Scenario folder, "
                    f"including any final-energy, costs, emissions, and heat-rejection results, "
                    f"and create a new one."
                ),
            }]

    return []


def parameters_for_script(script_name, config):
    """Return a list consisting of :py:class:`cea.config.Parameter` objects for each parameter of a script"""
    parameters = [p for _, p in config.matching_parameters(
        cea.scripts.by_name(script_name, plugins=config.plugins).parameters)]
    return parameters

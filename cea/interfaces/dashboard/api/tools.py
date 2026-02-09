from collections import defaultdict
from itertools import groupby
from typing import Dict, Any, List, Optional
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import cea.config
import cea.scripts
from cea.schemas import schemas
from .utils import deconstruct_parameters
from cea.interfaces.dashboard.dependencies import CEAConfig, CEADatabaseConfig, CEASeverDemoAuthCheck

router = APIRouter()
logger = logging.getLogger(__name__)


def validate_parameter(parameter, value, parameter_name: str = None) -> tuple[bool, str | None]:
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
async def get_tool_properties(config: CEAConfig, tool_name: str) -> ToolProperties:
    # TODO: Add plugin support
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

    # Set the parameters to their default values
    for parameter in parameters_for_script(tool_name, config):
        if parameter.name == 'scenario':
            continue
        
        default_value = default_config.sections[parameter.section.name].parameters[parameter.name].get()
        print(parameter.name, default_value, parameter.nullable)
        # Don't set parameters that are not nullable and have an empty default value
        if default_value == "" and not parameter.nullable:
            logger.debug(f"Skipping {parameter.name} since it has no default value")
            continue

        parameter.set(default_value)
    
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
            status_code=400,
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
        raise HTTPException(status_code=400, detail="parameter_name is required")

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
        raise HTTPException(status_code=404, detail=f"Parameter '{parameter_name}' not found")

    # Validate using encode() method
    is_valid, error_message = validate_parameter(target_parameter, value, parameter_name)
    return {"valid": is_valid, "error": error_message}


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

        # For ChoiceParameters, get updated choices
        if isinstance(param, cea.config.ChoiceParameter):
            try:
                choices = param._choices  # type: ignore[attr-defined]
                current_value = param.get()

                # If current value not in choices, use first choice or None
                if current_value not in choices:
                    current_value = choices[0] if choices else None

                result[param.name] = {
                    'choices': choices,
                    'value': current_value
                }
                logger.debug(f"[get_parameter_metadata] {param.name}: {len(choices)} choices, value={current_value}")
            except Exception as e:
                logger.error(f"[get_parameter_metadata] Error getting metadata for {param.name}: {e}")

    logger.debug(f"[get_parameter_metadata] Returning metadata for {len(result)} parameters")
    return {'parameters': result}


@router.post('/{tool_name}/check')
async def check_tool_inputs(config: CEAConfig, tool_name: str, payload: Dict[str, Any]):
    # Set config parameters
    for parameter in parameters_for_script(tool_name, config):
        if parameter.name in payload:
            value = payload[parameter.name]
            parameter.set(value)

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

        raise HTTPException(status_code=400,
                            detail={"message": "Missing input files",
                                    "script_suggestions": list(scripts)})


def parameters_for_script(script_name, config):
    """Return a list consisting of :py:class:`cea.config.Parameter` objects for each parameter of a script"""
    parameters = [p for _, p in config.matching_parameters(
        cea.scripts.by_name(script_name, plugins=config.plugins).parameters)]
    return parameters

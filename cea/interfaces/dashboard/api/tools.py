from collections import defaultdict
from itertools import groupby
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import cea.config
import cea.scripts
from cea.schemas import schemas
from .utils import deconstruct_parameters
from cea.interfaces.dashboard.dependencies import CEAConfig, CEADatabaseConfig, CEASeverDemoAuthCheck

router = APIRouter()


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
        # Don't set parameters that are not nullable and have an empty default value
        if default_value == "" and (not hasattr(parameter, "nullable") or not parameter.nullable):
            print(f"Skipping {parameter.name} since it has no default value")
            continue

        parameter.set(default_value)
    
    if isinstance(config, CEADatabaseConfig):
        await config.save()
    else:
        config.save()

    return 'Success'


@router.post('/{tool_name}/save-config', dependencies=[CEASeverDemoAuthCheck])
async def save_tool_config(config: CEAConfig, tool_name: str, payload: Dict[str, Any]):
    """Save the configuration for this tool to the configuration file"""
    for parameter in parameters_for_script(tool_name, config):
        if parameter.name != 'scenario' and parameter.name in payload:
            value = payload[parameter.name]
            print('%s: %s' % (parameter.name, value))
            parameter.set(value)
    
    if isinstance(config, CEADatabaseConfig):
        await config.save()
    else:
        config.save()
    return 'Success'


@router.post('/{tool_name}/parameter-choices')
async def get_parameter_choices(config: CEAConfig, tool_name: str, payload: Dict[str, Any]):
    """
    Get updated choices for a parameter based on current form values.
    Useful for parameters with dynamic choices that depend on other parameters.

    Payload should contain:
    - parameter_name: the name of the parameter to get choices for
    - form_values: dict of current form values to set on config before getting choices
    """
    parameter_name = payload.get('parameter_name')
    form_values = payload.get('form_values', {})

    print(f"\n[get_parameter_choices] tool_name={tool_name}, parameter_name={parameter_name}")
    print(f"[get_parameter_choices] form_values={form_values}")

    if not parameter_name:
        raise HTTPException(status_code=400, detail="parameter_name is required")

    # Temporarily set form values on config to get updated choices
    for param in parameters_for_script(tool_name, config):
        if param.name in form_values:
            try:
                print(f"[get_parameter_choices] Setting {param.name} = {form_values[param.name]}")
                param.set(form_values[param.name])
            except Exception as e:
                print(f"[get_parameter_choices] Failed to set {param.name}: {e}")

    # Find the parameter and get its choices
    target_parameter = None
    for param in parameters_for_script(tool_name, config):
        if param.name == parameter_name:
            target_parameter = param
            break

    if not target_parameter:
        raise HTTPException(status_code=404, detail=f"Parameter '{parameter_name}' not found")

    print(f"[get_parameter_choices] Found parameter: {target_parameter}, type: {type(target_parameter).__name__}")

    # Get the parameter's choices
    if isinstance(target_parameter, cea.config.ChoiceParameter):
        print("[get_parameter_choices] Getting choices...")
        choices = target_parameter._choices

        # Get the default/current value using decode()
        # For NetworkLayoutChoiceParameter, this will return the most recent network
        current_value = form_values.get(parameter_name, '')
        default_value = target_parameter.decode(current_value)

        print(f"[get_parameter_choices] current_value='{current_value}', default_value='{default_value}'")
        print(f"[get_parameter_choices] Returning {len(choices)} choices: {choices}")
        return {"choices": choices, "default": default_value}
    else:
        raise HTTPException(status_code=400, detail=f"Parameter '{parameter_name}' is not a choice parameter")


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

from typing import Dict, Any

from fastapi import APIRouter

import cea.config
import cea.scripts
from .utils import deconstruct_parameters
from cea.interfaces.dashboard.dependencies import CEAConfig

router = APIRouter()


# TOOL_DESCRIPTION_MODEL = api.model('Tool', {
#     'label': fields.String(description='Name of tool'),
#     'description': fields.String(description='Description of tool')
# })
#
# TOOL_LIST = api.model('ToolList', {'tools': fields.List})


@router.get('/')
async def get_tool_list(config: CEAConfig):
    from itertools import groupby

    tools = cea.scripts.for_interface('dashboard', plugins=config.plugins)
    result = dict()
    for category, group in groupby(tools, lambda t: t.category):
        result[category] = [
            {'name': t.name, 'label': t.label, 'description': t.description} for t in group]

    return result


@router.get('/{tool_name}')
async def get_tool_properties(config: CEAConfig, tool_name: str):
    script = cea.scripts.by_name(tool_name, plugins=config.plugins)

    parameters = []
    categories = {}
    for _, parameter in config.matching_parameters(script.parameters):
        if parameter.category:
            if parameter.category not in categories:
                categories[parameter.category] = []
            categories[parameter.category].append(
                deconstruct_parameters(parameter, config))
        else:
            parameters.append(deconstruct_parameters(parameter, config))

    out = {
        'category': script.category,
        'label': script.label,
        'description': script.description,
        'parameters': parameters,
        'categorical_parameters': categories,
    }

    return out


@router.post('/{tool_name}/default')
async def restore_default_config(config: CEAConfig, tool_name: str):
    """Restore the default configuration values for the CEA"""
    default_config = cea.config.Configuration(config_file=cea.config.DEFAULT_CONFIG)

    for parameter in parameters_for_script(tool_name, config):
        if parameter.name != 'scenario':
            parameter.set(
                default_config.sections[parameter.section.name].parameters[parameter.name].get())
    await config.save()
    return 'Success'


@router.post('/{tool_name}/save-config')
async def save_tool_config(config: CEAConfig, tool_name: str, payload: Dict[str, Any]):
    """Save the configuration for this tool to the configuration file"""
    for parameter in parameters_for_script(tool_name, config):
        if parameter.name != 'scenario' and parameter.name in payload:
            value = payload[parameter.name]
            print('%s: %s' % (parameter.name, value))
            parameter.set(value)
    config.save()
    return 'Success'


def parameters_for_script(script_name, config):
    """Return a list consisting of :py:class:`cea.config.Parameter` objects for each parameter of a script"""
    parameters = [p for _, p in config.matching_parameters(
        cea.scripts.by_name(script_name, plugins=config.plugins).parameters)]
    return parameters

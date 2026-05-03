import os
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from cea import MissingInputDataException
from cea.interfaces.dashboard.api.utils import validate_scenario_name
from cea.interfaces.dashboard.dependencies import CEAConfig, CEAProjectRoot
from cea.interfaces.dashboard.map_layers import get_layers_grouped_by_category, load_layer

router = APIRouter()


def _resolve_layer_scenario(config, params_project, params_scenario_name):
    """When the pathway viewer is active, config.scenario points to the
    state folder. Derive project/scenario_name from it so the map layer
    reads state-level results. Otherwise use the frontend-supplied values."""
    scenario_path = config.scenario
    if os.sep + 'outputs' + os.sep + 'pathways' + os.sep in scenario_path:
        return os.path.dirname(scenario_path), os.path.basename(scenario_path)
    return params_project, params_scenario_name


class LayerParams(BaseModel):
    project: str
    scenario_name: str
    parameters: dict

    @field_validator('scenario_name')
    @classmethod
    def _validate_scenario_name(cls, v):
        return validate_scenario_name(v)


class DeleteChoiceParams(BaseModel):
    project: str
    scenario_name: str
    value: str

    @field_validator('scenario_name')
    @classmethod
    def _validate_scenario_name(cls, v):
        return validate_scenario_name(v)


class LayerDescription(BaseModel):
    name: str
    label: str
    description: str
    parameters: dict


class LayerCategory(BaseModel):
    name: str
    label: str
    layers: List[LayerDescription]


class LayersList(BaseModel):
    categories: List[LayerCategory]


@router.get('/')
async def get_layers() -> LayersList:
    layers = get_layers_grouped_by_category()

    # Parse layer class to get name and description
    categories = []
    for category, layers in layers.items():
        category_label = category
        _layers = []
        for layer in layers:
            layer_description = layer.describe()
            category_label = layer_description["category"]["label"]
            _layers.append(LayerDescription(**layer_description))

        category_description = LayerCategory(name=category, label=category_label, layers=_layers)
        categories.append(category_description)

    return LayersList(categories=categories)


@router.post('/{layer_category}/{layer_name}/{parameter}/choices')
async def get_layer_parameter_choices(config: CEAConfig, project_root: CEAProjectRoot, params: LayerParams, layer_category: str, layer_name: str, parameter: str):
    layer_class = load_layer(layer_name, layer_category)

    project_path = params.project
    if project_root is not None and not project_path.startswith(project_root):
        project_path = os.path.join(project_root, project_path)

    eff_project, eff_scenario = _resolve_layer_scenario(config, project_path, params.scenario_name)
    try:
        layer = layer_class(project=eff_project, scenario_name=eff_scenario)
        choices = layer.get_parameter_choices(parameter, params.parameters)
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))

    return choices


@router.post('/{layer_category}/{layer_name}/{parameter}/choice/delete')
async def delete_layer_parameter_choice(
    config: CEAConfig,
    project_root: CEAProjectRoot,
    params: DeleteChoiceParams,
    layer_category: str,
    layer_name: str,
    parameter: str,
):
    layer_class = load_layer(layer_name, layer_category)

    project_path = params.project
    if project_root is not None and not project_path.startswith(project_root):
        project_path = os.path.join(project_root, project_path)

    eff_project, eff_scenario = _resolve_layer_scenario(config, project_path, params.scenario_name)
    try:
        layer = layer_class(project=eff_project, scenario_name=eff_scenario)
        layer.delete_parameter_choice(parameter, params.value)
    except NotImplementedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete: {e}")

    return {"success": True}


@router.post('/{layer_category}/{layer_name}/{parameter}/range')
async def get_layer_parameter_range(config: CEAConfig, project_root: CEAProjectRoot, params: LayerParams, layer_category: str, layer_name: str, parameter: str):
    layer_class = load_layer(layer_name, layer_category)

    project_path = params.project
    if project_root is not None and not project_path.startswith(project_root):
        project_path = os.path.join(project_root, project_path)

    eff_project, eff_scenario = _resolve_layer_scenario(config, project_path, params.scenario_name)
    try:
        layer = layer_class(project=eff_project, scenario_name=eff_scenario)
        range_values = layer.get_parameter_range(parameter, params.parameters)
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))

    return range_values


@router.post('/{layer_category}/{layer_name}/generate')
async def generate_map_layer(config: CEAConfig, project_root: CEAProjectRoot, params: LayerParams, layer_category: str, layer_name: str):
    layer_class = load_layer(layer_name, layer_category)

    project_path = params.project
    if project_root is not None and not project_path.startswith(project_root):
        project_path = os.path.join(project_root, project_path)

    eff_project, eff_scenario = _resolve_layer_scenario(config, project_path, params.scenario_name)
    try:
        layer = layer_class(project=eff_project, scenario_name=eff_scenario)
        output = layer.generate_output(params.parameters)
    except MissingInputDataException as e:
        print(e)
        raise HTTPException(status_code=400, detail="Missing input files")
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))

    return output


@router.post('/{layer_category}/{layer_name}/check')
async def check_map_layer(config: CEAConfig, project_root: CEAProjectRoot, params: LayerParams, layer_category: str, layer_name: str):
    layer_class = load_layer(layer_name, layer_category)

    project_path = params.project
    if project_root is not None and not project_path.startswith(project_root):
        project_path = os.path.join(project_root, project_path)

    eff_project, eff_scenario = _resolve_layer_scenario(config, project_path, params.scenario_name)
    try:
        layer = layer_class(project=eff_project, scenario_name=eff_scenario)
        layer.check_for_missing_input_files(params.parameters)
    except MissingInputDataException as e:
        print(e)
        raise HTTPException(status_code=400, detail="Missing input files")

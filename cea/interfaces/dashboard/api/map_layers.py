import os
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from cea import MissingInputDataException
from cea.interfaces.dashboard.dependencies import CEAProjectRoot
from cea.interfaces.dashboard.map_layers import get_layers_grouped_by_category, load_layer

router = APIRouter()


class LayerParams(BaseModel):
    project: str
    scenario_name: str
    parameters: dict


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
async def get_layer_parameter_choices(project_root: CEAProjectRoot, params: LayerParams, layer_category: str, layer_name: str, parameter: str):
    layer_class = load_layer(layer_name, layer_category)

    project_path = params.project
    if project_root is not None and not project_path.startswith(project_root):
        project_path = os.path.join(project_root, project_path)

    # Update params.project if there is project_root
    params.project = project_path
    try:
        layer = layer_class(project=params.project, scenario_name=params.scenario_name)
        choices = layer.get_parameter_choices(parameter, params.parameters)
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))

    return choices


@router.post('/{layer_category}/{layer_name}/{parameter}/range')
async def get_layer_parameter_range(project_root: CEAProjectRoot, params: LayerParams, layer_category: str, layer_name: str, parameter: str):
    layer_class = load_layer(layer_name, layer_category)

    project_path = params.project
    if project_root is not None and not project_path.startswith(project_root):
        project_path = os.path.join(project_root, project_path)

    # Update params.project if there is project_root
    params.project = project_path
    try:
        layer = layer_class(project=params.project, scenario_name=params.scenario_name)
        range_values = layer.get_parameter_range(parameter, params.parameters)
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))

    return range_values


@router.post('/{layer_category}/{layer_name}/generate')
async def generate_map_layer(project_root: CEAProjectRoot, params: LayerParams, layer_category: str, layer_name: str):
    layer_class = load_layer(layer_name, layer_category)

    project_path = params.project
    if project_root is not None and not project_path.startswith(project_root):
        project_path = os.path.join(project_root, project_path)

    # Update params.project if there is project_root
    params.project = project_path
    try:
        layer = layer_class(project=params.project, scenario_name=params.scenario_name)
        output = layer.generate_output(params.parameters)
    except MissingInputDataException as e:
        print(e)
        raise HTTPException(status_code=400, detail="Missing input files")
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))

    return output


@router.post('/{layer_category}/{layer_name}/check')
async def check_map_layer(project_root: CEAProjectRoot,params: LayerParams, layer_category: str, layer_name: str):
    layer_class = load_layer(layer_name, layer_category)

    project_path = params.project
    if project_root is not None and not project_path.startswith(project_root):
        project_path = os.path.join(project_root, project_path)

    # Update params.project if there is project_root
    params.project = project_path

    try:
        layer = layer_class(project=params.project, scenario_name=params.scenario_name)
        layer.check_for_missing_input_files(params.parameters)
    except MissingInputDataException as e:
        print(e)
        raise HTTPException(status_code=400, detail="Missing input files")

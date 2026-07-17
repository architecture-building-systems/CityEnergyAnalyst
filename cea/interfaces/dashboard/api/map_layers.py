import os
from typing import List

from fastapi import APIRouter, HTTPException, status

from cea import MissingInputDataException
from cea.interfaces.dashboard.api.utils import CEAScenario
from cea.interfaces.dashboard.map_layers import get_layers_grouped_by_category, load_layer
from pydantic import BaseModel

router = APIRouter()


class LayerParams(BaseModel):
    model_config = {"extra": "forbid"}

    parameters: dict


class DeleteChoiceParams(BaseModel):
    model_config = {"extra": "forbid"}

    value: str


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


@router.get('')
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
async def get_layer_parameter_choices(
    scenario: CEAScenario,
    params: LayerParams,
    layer_category: str,
    layer_name: str,
    parameter: str,
):
    layer_class = load_layer(layer_name, layer_category)
    try:
        layer = layer_class(project=os.path.dirname(scenario), scenario_name=os.path.basename(scenario))
        choices = layer.get_parameter_choices(parameter, params.parameters)
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return choices


@router.post('/{layer_category}/{layer_name}/{parameter}/choice/delete')
async def delete_layer_parameter_choice(
    scenario: CEAScenario,
    params: DeleteChoiceParams,
    layer_category: str,
    layer_name: str,
    parameter: str,
):
    layer_class = load_layer(layer_name, layer_category)
    try:
        layer = layer_class(project=os.path.dirname(scenario), scenario_name=os.path.basename(scenario))
        layer.delete_parameter_choice(parameter, params.value)
    except NotImplementedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete: {e}")

    return {"success": True}


@router.post('/{layer_category}/{layer_name}/{parameter}/range')
async def get_layer_parameter_range(
    scenario: CEAScenario,
    params: LayerParams,
    layer_category: str,
    layer_name: str,
    parameter: str,
):
    layer_class = load_layer(layer_name, layer_category)
    try:
        layer = layer_class(project=os.path.dirname(scenario), scenario_name=os.path.basename(scenario))
        range_values = layer.get_parameter_range(parameter, params.parameters)
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return range_values


@router.post('/{layer_category}/{layer_name}/generate')
async def generate_map_layer(
    scenario: CEAScenario,
    params: LayerParams,
    layer_category: str,
    layer_name: str,
):
    layer_class = load_layer(layer_name, layer_category)
    try:
        layer = layer_class(project=os.path.dirname(scenario), scenario_name=os.path.basename(scenario))
        output = layer.generate_output(params.parameters)
    except MissingInputDataException as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing input files")
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return output


@router.post('/{layer_category}/{layer_name}/check')
async def check_map_layer(
    scenario: CEAScenario,
    params: LayerParams,
    layer_category: str,
    layer_name: str,
):
    layer_class = load_layer(layer_name, layer_category)
    try:
        layer = layer_class(project=os.path.dirname(scenario), scenario_name=os.path.basename(scenario))
        layer.check_for_missing_input_files(params.parameters)
    except MissingInputDataException as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing input files")

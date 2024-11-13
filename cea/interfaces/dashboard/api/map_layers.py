from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from cea import MissingInputDataException
from cea.interfaces.dashboard.map_layers import get_layers_grouped_by_category, load_layer

router = APIRouter()


class LayerParams(BaseModel):
    project: str
    parameters: dict


class LayerDescription(BaseModel):
    name: str
    label: str
    description: str


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


@router.post('/{layer_category}/{layer_name}/generate')
async def generate_map_layer(params: LayerParams, layer_category: str, layer_name: str):
    layer_class = load_layer(layer_name, layer_category)

    try:
        layer = layer_class(project=params.project, parameters=params.parameters)
    except MissingInputDataException as e:
        print(e)
        raise HTTPException(status_code=400, detail="Missing input files")

    return layer.generate_output()


@router.post('/{layer_category}/{layer_name}/check')
async def check_map_layer(params: LayerParams, layer_category: str, layer_name: str):
    layer_class = load_layer(layer_name, layer_category)

    try:
        layer_class(project=params.project, parameters=params.parameters)
    except MissingInputDataException:
        raise HTTPException(status_code=400, detail="Missing input files")

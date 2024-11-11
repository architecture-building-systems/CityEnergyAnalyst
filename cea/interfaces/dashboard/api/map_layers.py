from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from cea import MissingInputDataException
from cea.interfaces.dashboard.map_layers import get_layers_grouped_by_category, load_layer

router = APIRouter()


class LayerParams(BaseModel):
    project: str
    parameters: dict


@router.get('/')
async def get_layers():
    layers = get_layers_grouped_by_category()

    # Parse layer class to get name and description
    out = {"categories": []}
    for category, layers in layers.items():
        category_description = {"name": category, "layers":[]}
        for layer in layers:
            layer_description = layer.describe()
            category_description["label"] = layer_description["category"]["label"]
            category_description["layers"].append(layer_description)
        out["categories"].append(category_description)

    print(out)
    return out

@router.post('/{layer_category}/{layer_name}/generate')
async def generate_map_layer(params: LayerParams, layer_category: str, layer_name: str):
    layer_class = load_layer(layer_name, layer_category)

    try:
        layer = layer_class(project=params.project, parameters=params.parameters)
    except MissingInputDataException:
        raise HTTPException(status_code=400, detail="Missing input files")

    return layer.generate_output()


@router.post('/{layer_category}/{layer_name}/check')
async def check_map_layer(params: LayerParams, layer_category: str, layer_name: str):
    layer_class = load_layer(layer_name, layer_category)

    try:
        layer = layer_class(project=params.project, parameters=params.parameters)
    except MissingInputDataException:
        raise HTTPException(status_code=400, detail="Missing input files")

import os
from collections import defaultdict

from typing import Dict, List, Type

from cea.interfaces.dashboard.map_layers.base import MapLayer
from cea.interfaces.dashboard.utils import find_subclasses_in_path


def get_layers() -> List[Type[MapLayer]]:
    """Returns a list of all layers"""
    layer_classes = find_subclasses_in_path(MapLayer, os.path.dirname(__file__))
    return layer_classes


def get_layers_grouped_by_category() -> Dict[str, List[Type[MapLayer]]]:
    """Returns a dictionary of all layers grouped by category"""
    layers = get_layers()
    layers_grouped_by_category = defaultdict(list)

    for layer in layers:
        layers_grouped_by_category[layer.category].append(layer)
    return dict(layers_grouped_by_category)


def load_layer(layer_name: str, layer_category: str) -> Type[MapLayer]:
    """Returns a MapLayer object if is_valid_category(category), else raises an exception"""
    for layer_class in get_layers_grouped_by_category()[layer_category]:
        if layer_class.name == layer_name:
            return layer_class

    raise Exception(f'Layer {layer_name} not found')

import os
from collections import defaultdict

from typing import Dict, List, Type, Tuple

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
        layers_grouped_by_category[layer.category.name].append(layer)
    return dict(layers_grouped_by_category)


def load_layer(layer_name: str, layer_category: str) -> Type[MapLayer]:
    """Returns a MapLayer object if is_valid_category(category), else raises an exception"""
    for layer_class in get_layers_grouped_by_category()[layer_category]:
        if layer_class.name == layer_name:
            return layer_class

    raise Exception(f'Layer {layer_name} not found')


def day_range_to_hour_range(nth_day_start: int, nth_day_end: int) -> Tuple[int, int]:
    """
    Converts a nth day range (e.g. 01-Jan is 1, 31-Dec is 365) to hour range (zero-indexed),
    where the first hour is the hour at the start of the "start day" and the second hour is the
    hour at the end of the "end day".

    e.g. day_range_to_hour_range(1, 1) returns 0, 23
    e.g. day_range_to_hour_range(1, 2) returns 0, 47
    e.g. day_range_to_hour_range(365, 1) returns 8736, 23
    """
    return (nth_day_start-1) * 24, nth_day_end * 24 -1

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import numpy as np

from cea.datamanagement.database.archetypes import Archetypes
from cea.datamanagement.database.assemblies import Assemblies
from cea.datamanagement.database.components import Components

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator

FILE_EXTENSIONS = ['.csv']
databases_folder_path = os.path.dirname(os.path.abspath(__file__))


def get_regions():
    return [folder for folder in os.listdir(databases_folder_path) if folder != "weather"
            and os.path.isdir(os.path.join(databases_folder_path, folder))
            and not folder.startswith('.')
            and not folder.startswith('__')]


def get_weather_files():
    weather_folder_path = os.path.join(databases_folder_path, 'weather')
    return [os.path.splitext(f)[0] for f in os.listdir(weather_folder_path) if f.endswith('.epw')]


def _replace_nan_with_none(obj):
    """Recursively replace NaN values with None for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _replace_nan_with_none(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_replace_nan_with_none(item) for item in obj]
    elif isinstance(obj, float) and np.isnan(obj):
        return None
    else:
        return obj


class CEADatabase:
    def __init__(self, locator: InputLocator):
        try:
            self.archetypes = Archetypes.init_database(locator)
            self.assemblies = Assemblies.init_database(locator)
            self.components = Components.init_database(locator)
        except Exception as e:
            # TODO: Use CEAException or a custom exception class
            raise RuntimeError(f"Failed to initialize CEA database: {e}")

    def to_dict(self) -> dict:
        data = {
            'archetypes': self.archetypes.to_dict(),
            'assemblies': self.assemblies.to_dict(),
            'components': self.components.to_dict(),
        }

        return _replace_nan_with_none(data)


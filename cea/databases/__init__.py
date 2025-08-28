from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import numpy as np

from cea import CEAException
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

def invert_nested_dict(d, path=[]):
      result = {}
      for key, value in d.items():
          current_path = path + [key]
          if isinstance(value, dict):
              result.update(invert_nested_dict(value, current_path))
          else:
              result[value] = current_path
      return result

class CEADatabaseException(CEAException):
    """Custom exception for CEA database errors."""

class CEADatabase:
    def __init__(self, locator: InputLocator):
        try:
            self.archetypes = Archetypes.init_database(locator)
            self.assemblies = Assemblies.init_database(locator)
            self.components = Components.init_database(locator)
        except Exception as e:
            raise CEADatabaseException(f"Failed to initialize CEA database: {e}")

    def to_dict(self) -> dict:
        data = {
            'archetypes': self.archetypes.to_dict(),
            'assemblies': self.assemblies.to_dict(),
            'components': self.components.to_dict(),
        }

        return _replace_nan_with_none(data)
    
    @classmethod
    def _locator_mappings(cls) -> dict[str, dict[str, Any]]:
        mappings = {
            'archetypes': Archetypes._locator_mappings(),
            'assemblies': Assemblies._locator_mappings(),
            'components': Components._locator_mappings(),
        }

        return mappings

    @classmethod
    def schema(cls, replace_locator_refs: bool = False) -> dict[str, dict[str, Any]]:
        schema: dict[str, dict[str, Any]] = {
            'archetypes': Archetypes.schema(),
            'assemblies': Assemblies.schema(),
            'components': Components.schema(),
        }

        if replace_locator_refs:
            flat_mapping = invert_nested_dict(cls._locator_mappings())

            def replace_paths_using_mapping(d, mapping: dict[str, list[str]]):
                if isinstance(d, dict):
                    for key, value in d.items():
                        if key == 'path' and isinstance(value, str) and value in mapping:
                            d[key] = mapping[value]
                        else:
                            replace_paths_using_mapping(value, mapping)

            replace_paths_using_mapping(schema, flat_mapping)

        return schema

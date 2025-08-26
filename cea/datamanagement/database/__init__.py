from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from typing import Any, Literal, Self, TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator

@dataclass
class BaseDatabase(ABC):

    @property
    @abstractmethod
    def _locator_mapping(self) -> dict[str, str]:
        """A mapping of locator names to their corresponding database fields."""

    @classmethod
    @abstractmethod
    def init_database(cls, locator: InputLocator) -> Self:
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        pass

    def dataclass_to_dict(self, orient: Literal['records', 'index'] = 'index') -> dict[str, Any]:
        """Convert a dataclass instance to a dictionary, handling nested DataFrames and other types."""
        result = {}
        for field in fields(self):
            value = getattr(self, field.name)

            if isinstance(value, dict):
                _orient = orient
                # Handle special case for '_library' field
                if field.name == '_library':
                    _orient = 'records'

                # Handle dict of DataFrames
                result[field.name] = {k: v.to_dict(orient=_orient) for k, v in value.items()}
            elif hasattr(value, 'to_dict'):
                # Handle single DataFrame
                if isinstance(value, pd.DataFrame):
                    result[field.name] = value.to_dict(orient=orient)
                else:
                    result[field.name] = value.to_dict()
            else:
                # Handle other types
                result[field.name] = value
        return result

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
import inspect
from typing import Any, Literal, Self, TYPE_CHECKING, get_type_hints

import pandas as pd

from cea.schemas import schemas

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


@dataclass
class Base(ABC):
    """Base class for database objects."""

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

@dataclass
class BaseDatabase(Base):
    """Base class for single database objects."""

    @classmethod
    @abstractmethod
    def _locator_mapping(cls) -> dict[str, str]:
        """A mapping of locator names to their corresponding database fields."""

    @classmethod
    def schema(cls) -> dict[str, Any]:
        """Return the database schema for the object."""
        schema = schemas()
        
        out = dict()
        type_hints = get_type_hints(cls)
        for field in fields(cls):
            # Check for nested BaseDatabase classes
            field_type = type_hints.get(field.name)
            if field_type is not None and inspect.isclass(field_type):
                # Now safe to use issubclass
                if issubclass(field_type, BaseDatabase):
                    out[field.name] = field_type.schema()
                    continue
            
            locator_method = cls._locator_mapping().get(field.name)
            if locator_method:
                out[field.name] = schema.get(locator_method, None)
                if out[field.name] is None:
                    print(f"Warning: No schema found for locator `{locator_method}` in class `{cls.__name__}`")
            else:
                print(f"Warning: No locator mapping found for field `{field.name}` in class `{cls.__name__}`")
        return out

@dataclass
class BaseDatabaseCollection(Base):
    """Base class for database object collections."""

    @classmethod
    def _locator_mappings(cls) -> dict[str, str]:
        """Return the locator mappings for the collection."""
        out = dict()
        for name, field in get_type_hints(cls).items():
            out[name] = field._locator_mapping()
        return out

    @classmethod
    def schema(cls) -> dict[str, Any]:
        """Return the database schema for the collection."""
        out = dict()
        for name, field_class in get_type_hints(cls).items():
            try:
                schema = field_class.schema()
                out[name] = schema
            except Exception as e:
                raise ValueError(f"Error getting schema for field `{name}`: {e}") 
        return out
        

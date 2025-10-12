from __future__ import annotations

import os.path
from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
import inspect
from typing import Any, Literal, TYPE_CHECKING, get_type_hints

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

import pandas as pd

from cea.schemas import schemas

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


@dataclass
class Base(ABC):
    """Base class for database objects."""

    @classmethod
    @abstractmethod
    def from_locator(cls, locator: InputLocator) -> Self:
        """Initialize the database object using the provided locator."""

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> Self:
        """Create an instance of the class from a dictionary."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""

    @abstractmethod
    def save(self, locator: InputLocator) -> None:
        """Save the database object using the provided locator."""

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
                    try:
                        result[field.name] = value.to_dict(orient=orient)
                    except ValueError:
                        # Deal with duplicates in index e.g. "Rsun"
                        if any(value.index.duplicated()):
                            print(f"Warning: Duplicated index found in DataFrame for field `{field.name}`")
                            value = value[~value.index.duplicated(keep='first')]
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

    def is_empty(self) -> bool:
        """Check if all database fields are empty."""
        for field in fields(self):
            value = getattr(self, field.name)

            # Skip private/special fields
            if field.name.startswith('_'):
                continue

            # Handle nested BaseDatabase objects
            if isinstance(value, BaseDatabase):
                if not value.is_empty():
                    return False
            # Handle DataFrames
            elif isinstance(value, pd.DataFrame):
                if not value.empty:
                    return False
            # Handle dictionaries (e.g., _library fields, or Conversion fields)
            elif isinstance(value, dict):
                if value:  # Non-empty dict
                    return False
            # Handle None values (considered empty)
            elif value is not None:
                # Any other non-None value is considered non-empty
                return False

        return True

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

    def save(self, locator: InputLocator) -> None:
        """Save the database object using the provided locator."""
        for field in fields(self):
            value = getattr(self, field.name)
            if value is None:
                print(f"Warning: Field `{field.name}` in `{self.__class__.__name__}` is None, skipping save.")
                continue

            if isinstance(value, pd.DataFrame):
                locator_method = self._locator_mapping().get(field.name)
                if locator_method is None:
                    raise ValueError(
                        f"No locator mapping found for field `{field.name}` in class `{self.__class__.__name__}`")
                try:
                    path = getattr(locator, locator_method)()
                except AttributeError:
                    raise ValueError(f"Locator method for {field.name} not found: {locator_method}")
                
                config = {}

                # Get columns from schema if available
                columns = self.schema().get(field.name, {}).get('columns', None)
                if columns and isinstance(columns, dict):
                    config['columns'] = list(columns.keys())
                
                os.makedirs(os.path.dirname(path), exist_ok=True)
                value.to_csv(path, **config)
            elif isinstance(value, dict):
                # Assume is _library with special index handling
                # e.g., Schedules and Feedstocks classes
                # the key is the name of the file, locator method gives the folder
                if field.name == '_library':
                    if not hasattr(self, '_library_index'):
                        raise AttributeError(
                            f"Unable to determine index for library DataFrame in field `{field.name}`.Ensure `_library_index` is defined.")

                    for k, df in value.items():
                        if not isinstance(df, pd.DataFrame):
                            raise ValueError(f"Field `{field.name}` contains a non-DataFrame value of type `{type(df)}`.")
                        folder_path = getattr(locator, self._locator_mapping().get(field.name))()
                        file_path = os.path.join(folder_path, f"{k}.csv")

                        out = df.set_index(self._library_index)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        out.to_csv(file_path)
                # Have to handle properties of Conversion separately due to dict format
                elif self.__class__.__name__ == 'Conversion':
                    file_path = getattr(locator, self._locator_mapping().get(field.name))()

                    data = []
                    for k, df in value.items():
                        if not isinstance(df, pd.DataFrame):
                            raise ValueError(f"Field `{field.name}` contains a non-DataFrame value of type `{type(df)}`.")
                        # Readd group name as index column
                        out = df.copy()
                        out[self._index] = k
                        data.append(out.set_index(self._index))

                    if not data:
                        print(f"Warning: No data to save for field `{field.name}` in `{self.__class__.__name__}`.")
                        continue
                        
                    combined_df = pd.concat(data)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    combined_df.to_csv(file_path)
                else:
                    raise ValueError(f"Field `{field.name}` is a dict but unable to decode format.")

            elif isinstance(value, BaseDatabase):
                value.save(locator)
            else:
                raise ValueError(f"Field `{field.name}` is of type `{type(value)}`, which is not a DataFrame or subclass of BaseDatabase.")

@dataclass
class BaseDatabaseCollection(Base, ABC):
    """Base class for database object collections."""

    def save(self, locator: InputLocator) -> None:
        """Save the database collection using the provided locator."""
        for field in fields(self):
            value = getattr(self, field.name)
            # properties of BaseDatabaseCollection must be BaseDatabase subclasses
            if isinstance(value, BaseDatabase):
                value.save(locator)
            else:
                raise ValueError(f"Field `{field.name}` is of type `{type(value)}`, which is not a subclass of Base.")

    def is_empty(self) -> bool:
        """Check if all database collections are empty."""
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, (BaseDatabase, BaseDatabaseCollection)):
                if not value.is_empty():
                    return False
        return True

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

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Create an instance of the collection from a dictionary."""
        init_args = {}
        type_hints = get_type_hints(cls)
        for field in fields(cls):
            field_data = data.get(field.name)
            field_type = type_hints.get(field.name)
            if field_data is not None and field_type is not None and inspect.isclass(field_type):
                if issubclass(field_type, BaseDatabase):
                    init_args[field.name] = field_type.from_dict(field_data)
                else:
                    raise ValueError(f"Field `{field.name}` is of type `{field_type}`, which is not a subclass of BaseDatabase.")
            else:
                init_args[field.name] = field_data
        return cls(**init_args)
        

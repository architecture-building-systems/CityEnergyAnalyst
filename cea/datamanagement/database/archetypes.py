from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from cea.datamanagement.database import BaseDatabase, BaseDatabaseCollection

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


@dataclass
class ConstructionType(BaseDatabase):
    _index = 'const_type'
    construction_types: pd.DataFrame | None

    @classmethod
    def init_database(cls, locator: InputLocator):
        try:
            construction_types = pd.read_csv(locator.get_database_archetypes_construction_type()).set_index(cls._index)
        except FileNotFoundError:
            construction_types = None
        
        return cls(construction_types)

    def to_dict(self):
        return self.dataclass_to_dict()


@dataclass
class Schedules(BaseDatabase):
    _index = 'use_type'

    monthly_multipliers: pd.DataFrame | None
    _library: dict[str, pd.DataFrame]

    @classmethod
    def init_database(cls, locator: InputLocator):
        try:
            monthly_multipliers = pd.read_csv(locator.get_database_archetypes_schedules_monthly_multiplier()).set_index(cls._index)
        except FileNotFoundError:
            monthly_multipliers = None
        
        _library = dict()
        for file in Path(locator.get_db4_archetypes_schedules_library_folder()).glob('*.csv'):
            _library[file.stem] = pd.read_csv(file)

        return cls(monthly_multipliers, _library)

    def to_dict(self):
        return {'monthly_multipliers': self.monthly_multipliers.to_dict(orient='index') if self.monthly_multipliers is not None else None,
                '_library': {k: v.to_dict(orient='records') for k, v in self._library.items()}}


@dataclass
class UseType(BaseDatabase):
    _index = 'use_type'

    use_types: pd.DataFrame | None
    schedules: Schedules

    @classmethod
    def init_database(cls, locator: InputLocator):
        try:
            use_types = pd.read_csv(locator.get_database_archetypes_use_type()).set_index(cls._index)
        except FileNotFoundError:
            use_types = None
        
        schedules = Schedules.init_database(locator)
        return cls(use_types, schedules)

    def to_dict(self):
        return {'use_types': self.use_types.to_dict(orient='index') if self.use_types is not None else None, 'schedules': self.schedules.to_dict()}


@dataclass
class Archetypes(BaseDatabaseCollection):
    construction: ConstructionType
    use: UseType

    @classmethod
    def init_database(cls, locator: InputLocator):
        construction = ConstructionType.init_database(locator)
        use = UseType.init_database(locator)
        return cls(construction, use)

    def to_dict(self):
        return {'construction': self.construction.to_dict(), 'use': self.use.to_dict()}

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


@dataclass
class Construction:
    _index = 'const_type'
    construction_types: pd.DataFrame

    @classmethod
    def init_database(cls, locator: InputLocator):
        construction_types = pd.read_csv(locator.get_database_archetypes_construction_type()).set_index(cls._index)
        return cls(construction_types)

    def to_dict(self):
        return {'construction_types': self.construction_types.to_dict(orient='index')}


@dataclass
class Schedules:
    _index = 'use_type'

    monthly_multipliers: pd.DataFrame
    _library: dict[str, pd.DataFrame]

    @classmethod
    def init_database(cls, locator: InputLocator):
        monthly_multipliers = pd.read_csv(locator.get_database_archetypes_schedules_monthly_multiplier()).set_index(cls._index)
        _library = dict()
        for file in Path(locator.get_db4_archetypes_schedules_library_folder()).glob('*.csv'):
            _library[file.stem] = pd.read_csv(file)

        return cls(monthly_multipliers, _library)

    def to_dict(self):
        return {'monthly_multipliers': self.monthly_multipliers.to_dict(orient='index'),
                '_library': {k: v.to_dict(orient='records') for k, v in self._library.items()}}


@dataclass
class Use:
    _index = 'use_type'

    use_types: pd.DataFrame
    schedules: Schedules

    @classmethod
    def init_database(cls, locator: InputLocator):
        use_types = pd.read_csv(locator.get_database_archetypes_use_type()).set_index(cls._index)
        schedules = Schedules.init_database(locator)
        return cls(use_types, schedules)

    def to_dict(self):
        return {'use_types': self.use_types.to_dict(orient='index'), 'schedules': self.schedules.to_dict()}


@dataclass
class Archetypes:
    construction: Construction
    use: Use

    @classmethod
    def init_database(cls, locator: InputLocator):
        construction = Construction.init_database(locator)
        use = Use.init_database(locator)
        return cls(construction, use)

    def to_dict(self):
        return {'construction': self.construction.to_dict(), 'use': self.use.to_dict()}

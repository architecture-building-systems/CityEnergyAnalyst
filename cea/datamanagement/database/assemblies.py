from __future__ import annotations

from dataclasses import dataclass, fields
from typing import TYPE_CHECKING

import pandas as pd

from cea.datamanagement.database import BaseDatabase, BaseDatabaseCollection

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


class BaseAssemblyDatabase(BaseDatabase):
    _index: str = 'code'
    
    @classmethod
    def from_locator(cls, locator: InputLocator):
        return cls(**cls._read_mapping(locator, cls._locator_mapping()))

    @classmethod
    def from_dict(cls, d: dict):
        init_args = dict()
        for field in fields(cls):
            value = d.get(field.name, None)
            df = pd.DataFrame.from_dict(value, orient='index')
            df.index.name = cls._index
            init_args[field.name] = df
        return cls(**init_args)

    def to_dict(self):
        return self.dataclass_to_dict()
    
    @classmethod
    def _read_mapping(cls, locator: InputLocator, mapping: dict[str, str]) -> dict[str, pd.DataFrame | None]:
        """
        Helper to read multiple CSVs using a mapping {attr_name: locator_method_name}.
        Returns a dict of {attr_name: DataFrame} ready to be passed to the dataclass constructor.
        """
        frames = {}
        for attr, locator_method in mapping.items():
            if isinstance(locator_method, str):
                try:
                    path = getattr(locator, locator_method)()
                except AttributeError:
                    raise ValueError(f"Locator method for {attr} not found: {locator_method}")
            else:
                raise ValueError(f"Locator method for {attr} must be a string label, got {type(locator_method)}")

            try:
                frames[attr] = pd.read_csv(path).set_index(cls._index)
            except FileNotFoundError:
                frames[attr] = None
        return frames


@dataclass
class Envelope(BaseAssemblyDatabase):
    floor: pd.DataFrame | None
    mass: pd.DataFrame | None
    roof: pd.DataFrame | None
    shading: pd.DataFrame | None
    tightness: pd.DataFrame | None
    wall: pd.DataFrame | None
    window: pd.DataFrame | None

    @classmethod
    def _locator_mapping(cls) -> dict[str, str]:
        return {
            "floor": "get_database_assemblies_envelope_floor",
            "mass": "get_database_assemblies_envelope_mass",
            "roof": "get_database_assemblies_envelope_roof",
            "shading": "get_database_assemblies_envelope_shading",
            "tightness": "get_database_assemblies_envelope_tightness",
            "wall": "get_database_assemblies_envelope_wall",
            "window": "get_database_assemblies_envelope_window",
        }

@dataclass
class HVAC(BaseAssemblyDatabase):
    controller: pd.DataFrame | None
    cooling: pd.DataFrame | None
    heating: pd.DataFrame | None
    hot_water: pd.DataFrame | None
    ventilation: pd.DataFrame | None

    @classmethod
    def _locator_mapping(cls) -> dict[str, str]:
        return {
            "controller": "get_database_assemblies_hvac_controller",
            "cooling": "get_database_assemblies_hvac_cooling",
            "heating": "get_database_assemblies_hvac_heating",
            "hot_water": "get_database_assemblies_hvac_hot_water",
            "ventilation": "get_database_assemblies_hvac_ventilation",
        }

@dataclass
class Supply(BaseAssemblyDatabase):
    cooling: pd.DataFrame | None
    heating: pd.DataFrame | None
    hot_water: pd.DataFrame | None
    electricity: pd.DataFrame | None

    @classmethod
    def _locator_mapping(cls) -> dict[str, str]:
        return {
            "cooling": "get_database_assemblies_supply_cooling",
            "heating": "get_database_assemblies_supply_heating",
            "hot_water": "get_database_assemblies_supply_hot_water",
            "electricity": "get_database_assemblies_supply_electricity",
        }

@dataclass
class Assemblies(BaseDatabaseCollection):
    envelope: Envelope
    hvac: HVAC
    supply: Supply

    @classmethod
    def from_locator(cls, locator: InputLocator):
        return cls(
            envelope=Envelope.from_locator(locator),
            hvac=HVAC.from_locator(locator),
            supply=Supply.from_locator(locator)
        )

    def to_dict(self):
        return self.dataclass_to_dict()

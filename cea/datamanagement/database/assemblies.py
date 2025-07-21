from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


@dataclass
class Envelope:
    _index = 'code'

    floor: pd.DataFrame
    mass: pd.DataFrame
    roof: pd.DataFrame
    shading: pd.DataFrame
    tightness: pd.DataFrame
    wall: pd.DataFrame
    window: pd.DataFrame

    @classmethod
    def init_database(cls, locator: InputLocator):
        floor = pd.read_csv(locator.get_database_assemblies_envelope_floor()).set_index(cls._index)
        mass = pd.read_csv(locator.get_database_assemblies_envelope_mass()).set_index(cls._index)
        roof = pd.read_csv(locator.get_database_assemblies_envelope_roof()).set_index(cls._index)
        shading = pd.read_csv(locator.get_database_assemblies_envelope_shading()).set_index(cls._index)
        tightness = pd.read_csv(locator.get_database_assemblies_envelope_tightness()).set_index(cls._index)
        wall = pd.read_csv(locator.get_database_assemblies_envelope_wall()).set_index(cls._index)
        window = pd.read_csv(locator.get_database_assemblies_envelope_window()).set_index(cls._index)
        return cls(floor, mass, roof, shading, tightness, wall, window)

    def to_dict(self):
        return {'floor': self.floor.to_dict(orient='index'),
                'mass': self.mass.to_dict(orient='index'),
                'roof': self.roof.to_dict(orient='index'),
                'shading': self.shading.to_dict(orient='index'),
                'tightness': self.tightness.to_dict(orient='index'),
                'wall': self.wall.to_dict(orient='index'),
                'window': self.window.to_dict(orient='index')}


@dataclass
class HVAC:
    _index = 'code'

    controller: pd.DataFrame
    cooling: pd.DataFrame
    heating: pd.DataFrame
    hot_water: pd.DataFrame
    ventilation: pd.DataFrame

    @classmethod
    def init_database(cls, locator: InputLocator):
        controller = pd.read_csv(locator.get_database_assemblies_hvac_controller()).set_index(cls._index)
        cooling = pd.read_csv(locator.get_database_assemblies_hvac_cooling()).set_index(cls._index)
        heating = pd.read_csv(locator.get_database_assemblies_hvac_heating()).set_index(cls._index)
        hot_water = pd.read_csv(locator.get_database_assemblies_hvac_hot_water()).set_index(cls._index)
        ventilation = pd.read_csv(locator.get_database_assemblies_hvac_ventilation()).set_index(cls._index)
        return cls(controller, cooling, heating, hot_water, ventilation)

    def to_dict(self):
        return {'controller': self.controller.to_dict(orient='index'),
                'cooling': self.cooling.to_dict(orient='index'),
                'heating': self.heating.to_dict(orient='index'),
                'hot_water': self.hot_water.to_dict(orient='index'),
                'ventilation': self.ventilation.to_dict(orient='index')}


@dataclass
class Supply:
    _index = 'code'

    cooling: pd.DataFrame
    heating: pd.DataFrame
    hot_water: pd.DataFrame
    electricity: pd.DataFrame

    @classmethod
    def init_database(cls, locator: InputLocator):
        cooling = pd.read_csv(locator.get_database_assemblies_supply_cooling()).set_index(cls._index)
        heating = pd.read_csv(locator.get_database_assemblies_supply_heating()).set_index(cls._index)
        hot_water = pd.read_csv(locator.get_database_assemblies_supply_hot_water()).set_index(cls._index)
        electricity = pd.read_csv(locator.get_database_assemblies_supply_electricity()).set_index(cls._index)
        return cls(cooling, heating, hot_water, electricity)

    def to_dict(self):
        return {'cooling': self.cooling.to_dict(orient='index'),
                'heating': self.heating.to_dict(orient='index'),
                'hot_water': self.hot_water.to_dict(orient='index'),
                'electricity': self.electricity.to_dict(orient='index')}


@dataclass
class Assemblies:
    envelope: Envelope
    hvac: HVAC
    supply: Supply

    @classmethod
    def init_database(cls, locator: InputLocator):
        return cls(
            envelope=Envelope.init_database(locator),
            hvac=HVAC.init_database(locator),
            supply=Supply.init_database(locator)
        )

    def to_dict(self):
        return {'envelope': self.envelope.to_dict(), 'hvac': self.hvac.to_dict(), 'supply': self.supply.to_dict()}

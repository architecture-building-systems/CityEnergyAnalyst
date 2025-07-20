from __future__ import annotations
from typing import TYPE_CHECKING

from dataclasses import dataclass

import pandas as pd

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator

@dataclass
class Envelope:
    floor: pd.DataFrame
    mass: pd.DataFrame
    roof: pd.DataFrame
    shading: pd.DataFrame
    tightness: pd.DataFrame
    wall: pd.DataFrame
    window: pd.DataFrame

    @classmethod
    def init_database(cls, locator: InputLocator):
        floor = pd.read_csv(locator.get_database_assemblies_envelope_floor())
        mass = pd.read_csv(locator.get_database_assemblies_envelope_mass())
        roof = pd.read_csv(locator.get_database_assemblies_envelope_roof())
        shading = pd.read_csv(locator.get_database_assemblies_envelope_shading())
        tightness = pd.read_csv(locator.get_database_assemblies_envelope_tightness())
        wall = pd.read_csv(locator.get_database_assemblies_envelope_wall())
        window = pd.read_csv(locator.get_database_assemblies_envelope_window())
        return cls(floor, mass, roof, shading, tightness, wall, window)

    def to_dict(self):
        return {'floor': self.floor.to_dict(), 'mass': self.mass.to_dict(), 'roof': self.roof.to_dict(),
                'shading': self.shading.to_dict(), 'tightness': self.tightness.to_dict(), 'wall': self.wall.to_dict(),
                'window': self.window.to_dict()}

@dataclass
class HVAC:
    controller: pd.DataFrame
    cooling: pd.DataFrame
    heating: pd.DataFrame
    hot_water: pd.DataFrame
    ventilation: pd.DataFrame

    @classmethod
    def init_database(cls, locator: InputLocator):
        controller = pd.read_csv(locator.get_database_assemblies_hvac_controller())
        cooling = pd.read_csv(locator.get_database_assemblies_hvac_cooling())
        heating = pd.read_csv(locator.get_database_assemblies_hvac_heating())
        hot_water = pd.read_csv(locator.get_database_assemblies_hvac_hot_water())
        ventilation = pd.read_csv(locator.get_database_assemblies_hvac_ventilation())
        return cls(controller, cooling, heating, hot_water, ventilation)
    
    def to_dict(self):
        return {'controller': self.controller.to_dict(), 'cooling': self.cooling.to_dict(), 'heating': self.heating.to_dict(),
                'hot_water': self.hot_water.to_dict(), 'ventilation': self.ventilation.to_dict()} 

@dataclass
class Supply:
    cooling: pd.DataFrame
    heating: pd.DataFrame
    hot_water: pd.DataFrame
    electricity: pd.DataFrame

    @classmethod
    def init_database(cls, locator: InputLocator):
        cooling = pd.read_csv(locator.get_database_assemblies_supply_cooling())
        heating = pd.read_csv(locator.get_database_assemblies_supply_heating())
        hot_water = pd.read_csv(locator.get_database_assemblies_supply_hot_water())
        electricity = pd.read_csv(locator.get_database_assemblies_supply_electricity())        
        return cls(cooling, heating, hot_water, electricity)

    def to_dict(self):
        return {'cooling': self.cooling.to_dict(), 'heating': self.heating.to_dict(), 'hot_water': self.hot_water.to_dict(),
                'electricity': self.electricity.to_dict()}

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

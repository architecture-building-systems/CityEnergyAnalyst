from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

from dataclasses import dataclass

import pandas as pd

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


@dataclass
class Conversion:
    absorption_chillers: pd.DataFrame
    boilers: pd.DataFrame
    bore_holes: pd.DataFrame
    cogeneration_plants: pd.DataFrame
    cooling_towers: pd.DataFrame
    fuel_cells: pd.DataFrame
    heat_exchangers: pd.DataFrame
    heat_pumps: pd.DataFrame
    hydraulic_pumps: pd.DataFrame
    photovoltaic_panels: pd.DataFrame
    photovoltaic_thermal_panels: pd.DataFrame
    power_transformers: pd.DataFrame
    solar_collectors: pd.DataFrame
    thermal_energy_storages: pd.DataFrame
    unitary_air_conditioners: pd.DataFrame
    vapor_compression_chillers: pd.DataFrame

    @classmethod
    def init_database(cls, locator: InputLocator):
        absorption_chillers = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv("ABSORPTION_CHILLERS"))
        boilers = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv("BOILERS"))
        bore_holes = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv("BORE_HOLES"))
        cogeneration_plants = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv("COGENERATION_PLANTS"))
        cooling_towers = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv("COOLING_TOWERS"))
        fuel_cells = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv("FUEL_CELLS"))
        heat_exchangers = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv("HEAT_EXCHANGERS"))
        heat_pumps = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv("HEAT_PUMPS"))
        hydraulic_pumps = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv("HYDRAULIC_PUMPS"))
        photovoltaic_panels = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv("PHOTOVOLTAIC_PANELS"))
        photovoltaic_thermal_panels = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv("PHOTOVOLTAIC_THERMAL_PANELS"))
        power_transformers = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv("POWER_TRANSFORMERS"))
        solar_collectors = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv("SOLAR_COLLECTORS"))
        thermal_energy_storages = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv("THERMAL_ENERGY_STORAGES"))
        unitary_air_conditioners = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv("UNITARY_AIR_CONDITIONERS"))
        vapor_compression_chillers = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv("VAPOR_COMPRESSION_CHILLERS"))
        return cls(absorption_chillers, boilers, bore_holes, cogeneration_plants, cooling_towers, fuel_cells, heat_exchangers,
                   heat_pumps, hydraulic_pumps, photovoltaic_panels, photovoltaic_thermal_panels,
                   power_transformers, solar_collectors, thermal_energy_storages, unitary_air_conditioners,
                   vapor_compression_chillers)
    
    def to_dict(self):
        return {'absorption_chillers': self.absorption_chillers.to_dict(), 'boilers': self.boilers.to_dict(),
                'bore_holes': self.bore_holes.to_dict(), 'cogeneration_plants': self.cogeneration_plants.to_dict(),
                'cooling_towers': self.cooling_towers.to_dict(), 'fuel_cells': self.fuel_cells.to_dict(),
                'heat_exchangers': self.heat_exchangers.to_dict(), 'heat_pumps': self.heat_pumps.to_dict(),
                'hydraulic_pumps': self.hydraulic_pumps.to_dict(),
                'photovoltaic_panels': self.photovoltaic_panels.to_dict(), 'photovoltaic_thermal_plants': self.photovoltaic_thermal_panels.to_dict(),
                'power_transformers': self.power_transformers.to_dict(), 'solar_collectors': self.solar_collectors.to_dict(),
                'thermal_energy_storages': self.thermal_energy_storages.to_dict(),
                'unitary_air_conditioners': self.unitary_air_conditioners.to_dict(), 'vapor_compression_chillers': self.vapor_compression_chillers.to_dict()}

@dataclass
class Distribution:
    thermal_grid: pd.DataFrame

    @classmethod
    def init_database(cls, locator: InputLocator):
        thermal_grid = pd.read_csv(locator.get_database_components_distribution_thermal_grid())
        return cls(thermal_grid)

    def to_dict(self):
        return {'thermal_grid': self.thermal_grid.to_dict()}


@dataclass
class Feedstocks:
    energy_carriers: pd.DataFrame
    _library: dict[str, pd.DataFrame]

    @classmethod
    def init_database(cls, locator: InputLocator):
        energy_carriers = pd.read_csv(locator.get_database_components_feedstocks_energy_carriers())
        _library = dict()
        for file in Path(locator.get_db4_components_feedstocks_library_folder()).glob('*.csv'):
            _library[file.stem] = pd.read_csv(file)

        return cls(energy_carriers, _library)

    def to_dict(self):
        return {'energy_carriers': self.energy_carriers.to_dict(), '_library': {k: v.to_dict() for k, v in self._library.items()}}


@dataclass
class Components:
    conversion: Conversion
    distribution: Distribution
    feedstocks: Feedstocks
    
    @classmethod
    def init_database(cls, locator: InputLocator):
        conversion = Conversion.init_database(locator)
        distribution = Distribution.init_database(locator)
        feedstocks = Feedstocks.init_database(locator)
        return cls(conversion, distribution, feedstocks)
    
    def to_dict(self):
        return {'conversion': self.conversion.to_dict(), 'distribution': self.distribution.to_dict(), 'feedstocks': self.feedstocks.to_dict()}


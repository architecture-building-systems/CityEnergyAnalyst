from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from cea.datamanagement.database import BaseDatabase, BaseDatabaseCollection

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


@dataclass
class Conversion(BaseDatabase):
    _index = "code"

    absorption_chillers: dict[str, pd.DataFrame] | None
    boilers: dict[str, pd.DataFrame] | None
    bore_holes: dict[str, pd.DataFrame] | None
    cogeneration_plants: dict[str, pd.DataFrame] | None
    cooling_towers: dict[str, pd.DataFrame] | None
    fuel_cells: dict[str, pd.DataFrame] | None
    heat_exchangers: dict[str, pd.DataFrame] | None
    heat_pumps: dict[str, pd.DataFrame] | None
    hydraulic_pumps: dict[str, pd.DataFrame] | None
    photovoltaic_panels: dict[str, pd.DataFrame] | None
    photovoltaic_thermal_panels: dict[str, pd.DataFrame] | None
    power_transformers: dict[str, pd.DataFrame] | None
    solar_collectors: dict[str, pd.DataFrame] | None
    thermal_energy_storages: dict[str, pd.DataFrame] | None
    unitary_air_conditioners: dict[str, pd.DataFrame] | None
    vapor_compression_chillers: dict[str, pd.DataFrame] | None

    @staticmethod
    def _load_and_group_csv(csv_path: str, index_column: str) -> dict[str, pd.DataFrame] | None:
        """Load CSV and group by index column, returning dict of DataFrames."""
        try:
            df = pd.read_csv(csv_path)
            return {str(code): group for code, group in df.groupby(index_column)}
        except FileNotFoundError as e:
            print(f"Error loading {csv_path}: {e}")
            return None
    
    @classmethod
    def _locator_mapping(cls) -> dict[str, str]:
        # Return empty since the mapping logic is not very straightforward
        return {
            "absorption_chillers": "get_database_components_conversion_absorption_chillers",
            "boilers": "get_database_components_conversion_boilers",
            "bore_holes": "get_database_components_conversion_bore_holes",
            "cogeneration_plants": "get_database_components_conversion_cogeneration_plants",
            "cooling_towers": "get_database_components_conversion_cooling_towers",
            "fuel_cells": "get_database_components_conversion_fuel_cells",
            "heat_exchangers": "get_database_components_conversion_heat_exchangers",
            "heat_pumps": "get_database_components_conversion_heat_pumps",
            "hydraulic_pumps": "get_database_components_conversion_hydraulic_pumps",
            "photovoltaic_panels": "get_database_components_conversion_photovoltaic_panels",
            "photovoltaic_thermal_panels": "get_database_components_conversion_photovoltaic_thermal_panels",
            "power_transformers": "get_database_components_conversion_power_transformers",
            "solar_collectors": "get_database_components_conversion_solar_collectors",
            "thermal_energy_storages": "get_database_components_conversion_thermal_energy_storages",
            "unitary_air_conditioners": "get_database_components_conversion_unitary_air_conditioners",
            "vapor_compression_chillers": "get_database_components_conversion_vapor_compression_chillers"
        }

    @classmethod
    def from_locator(cls, locator: InputLocator):
        # Define component names (must match the CSV file names)
        components = [
            "ABSORPTION_CHILLERS",
            "BOILERS",
            "BORE_HOLES",
            "COGENERATION_PLANTS",
            "COOLING_TOWERS",
            "FUEL_CELLS",
            "HEAT_EXCHANGERS",
            "HEAT_PUMPS",
            "HYDRAULIC_PUMPS",
            "PHOTOVOLTAIC_PANELS",
            "PHOTOVOLTAIC_THERMAL_PANELS",
            "POWER_TRANSFORMERS",
            "SOLAR_COLLECTORS",
            "THERMAL_ENERGY_STORAGES",
            "UNITARY_AIR_CONDITIONERS",
            "VAPOR_COMPRESSION_CHILLERS"
        ]

        # Load and group all components
        component_data = {}
        for component in components:
            component_data[component.lower()] = cls._load_and_group_csv(
                locator.get_db4_components_conversion_conversion_technology_csv(component), cls._index)

        return cls(**component_data)

    @classmethod
    def from_dict(cls, d: dict):
        component_data = {}
        for key in d:
            data = []
            for k, v in d[key].items():
                if isinstance(v, list):
                    # Readd group name as index column
                    v = pd.DataFrame(v)
                    v[cls._index] = k
                    data.append(v)
            component_data[key] = pd.concat(data)
        return cls(**component_data)

    def to_dict(self):
        return self.dataclass_to_dict("records")


@dataclass
class Distribution(BaseDatabase):
    _index = "code"

    thermal_grid: pd.DataFrame | None

    @classmethod
    def _locator_mapping(cls) -> dict[str, str]:
        return {
            "thermal_grid": "get_database_components_distribution_thermal_grid"
        }

    @classmethod
    def from_locator(cls, locator: InputLocator):
        try:
            thermal_grid = pd.read_csv(locator.get_database_components_distribution_thermal_grid()).set_index(cls._index)
        except FileNotFoundError:
            thermal_grid = None
        return cls(thermal_grid)

    @classmethod
    def from_dict(cls, d: dict):
        thermal_grid = pd.DataFrame.from_dict(d.get('thermal_grid', None), orient='index')
        return cls(thermal_grid)

    def to_dict(self):
        return self.dataclass_to_dict()


@dataclass
class Feedstocks(BaseDatabase):
    # FIXME: Ensure that there is a proper index for the DataFrame i.e. Rsun code
    _index = "code"

    energy_carriers: pd.DataFrame | None
    _library: dict[str, pd.DataFrame]

    @classmethod
    def _locator_mapping(cls) -> dict[str, str]:
        return {
            "energy_carriers": "get_database_components_feedstocks_energy_carriers",
            "_library": "get_db4_components_feedstocks_library_folder"
        }

    @classmethod
    def from_locator(cls, locator: InputLocator):
        try:
            energy_carriers = pd.read_csv(locator.get_database_components_feedstocks_energy_carriers()).set_index(cls._index)
        except FileNotFoundError:
            energy_carriers = None

        _library = dict()
        for file in Path(locator.get_db4_components_feedstocks_library_folder()).glob('*.csv'):
            _library[file.stem] = pd.read_csv(file)

        return cls(energy_carriers, _library)

    @classmethod
    def from_dict(cls, d: dict):
        energy_carriers = pd.DataFrame.from_dict(d.get('energy_carriers', None), orient='index')
        _library = {k: pd.DataFrame(v) for k, v in d.get('_library', {}).items()}
        return cls(energy_carriers, _library)

    def to_dict(self):
        return self.dataclass_to_dict()


@dataclass
class Components(BaseDatabaseCollection):
    conversion: Conversion
    distribution: Distribution
    feedstocks: Feedstocks

    @classmethod
    def from_locator(cls, locator: InputLocator):
        conversion = Conversion.from_locator(locator)
        distribution = Distribution.from_locator(locator)
        feedstocks = Feedstocks.from_locator(locator)
        return cls(conversion, distribution, feedstocks)

    def to_dict(self):
        return self.dataclass_to_dict()

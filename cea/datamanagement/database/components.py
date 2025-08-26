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
    def init_database(cls, locator: InputLocator):
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

    def to_dict(self):
        return self.dataclass_to_dict("records")


@dataclass
class Distribution(BaseDatabase):
    _index = "code"

    thermal_grid: pd.DataFrame | None

    @classmethod
    def init_database(cls, locator: InputLocator):
        try:
            thermal_grid = pd.read_csv(locator.get_database_components_distribution_thermal_grid()).set_index("code")
        except FileNotFoundError:
            thermal_grid = None
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
    def init_database(cls, locator: InputLocator):
        try:
            energy_carriers = pd.read_csv(locator.get_database_components_feedstocks_energy_carriers())
        except FileNotFoundError:
            energy_carriers = None

        _library = dict()
        for file in Path(locator.get_db4_components_feedstocks_library_folder()).glob('*.csv'):
            _library[file.stem] = pd.read_csv(file)

        return cls(energy_carriers, _library)

    def to_dict(self):
        # Temporarily add dummy index to DataFrame for serialization
        new_df = None
        if self.energy_carriers is not None:
            new_df = self.energy_carriers.copy()
            new_df['index'] = new_df['code'] + '_' + new_df['mean_qual']
            new_df.set_index('index', inplace=True)
        
        new_obj = Feedstocks(new_df, self._library)

        return new_obj.dataclass_to_dict()


@dataclass
class Components(BaseDatabaseCollection):
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
        return self.dataclass_to_dict()

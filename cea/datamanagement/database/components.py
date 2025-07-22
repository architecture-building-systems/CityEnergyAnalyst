from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import pandas as pd

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


def dataclass_to_dict(dataclass_instance, orient: Literal['records', 'index'] = 'index'):
    """Convert a dataclass instance to a dictionary, handling nested DataFrames and other types."""
    result = {}
    for field in fields(dataclass_instance):
        value = getattr(dataclass_instance, field.name)

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
class Conversion:
    _index = "code"

    absorption_chillers: dict[str, pd.DataFrame]
    boilers: dict[str, pd.DataFrame]
    bore_holes: dict[str, pd.DataFrame]
    cogeneration_plants: dict[str, pd.DataFrame]
    cooling_towers: dict[str, pd.DataFrame]
    fuel_cells: dict[str, pd.DataFrame]
    heat_exchangers: dict[str, pd.DataFrame]
    heat_pumps: dict[str, pd.DataFrame]
    hydraulic_pumps: dict[str, pd.DataFrame]
    photovoltaic_panels: dict[str, pd.DataFrame]
    photovoltaic_thermal_panels: dict[str, pd.DataFrame]
    power_transformers: dict[str, pd.DataFrame]
    solar_collectors: dict[str, pd.DataFrame]
    thermal_energy_storages: dict[str, pd.DataFrame]
    unitary_air_conditioners: dict[str, pd.DataFrame]
    vapor_compression_chillers: dict[str, pd.DataFrame]

    @staticmethod
    def _load_and_group_csv(csv_path: str, index_column: str) -> dict[str, pd.DataFrame]:
        """Load CSV and group by index column, returning dict of DataFrames."""
        df = pd.read_csv(csv_path)
        return {str(code): group for code, group in df.groupby(index_column)}

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

        return cls(
            absorption_chillers=component_data["absorption_chillers"],
            boilers=component_data["boilers"],
            bore_holes=component_data["bore_holes"],
            cogeneration_plants=component_data["cogeneration_plants"],
            cooling_towers=component_data["cooling_towers"],
            fuel_cells=component_data["fuel_cells"],
            heat_exchangers=component_data["heat_exchangers"],
            heat_pumps=component_data["heat_pumps"],
            hydraulic_pumps=component_data["hydraulic_pumps"],
            photovoltaic_panels=component_data["photovoltaic_panels"],
            photovoltaic_thermal_panels=component_data["photovoltaic_thermal_panels"],
            power_transformers=component_data["power_transformers"],
            solar_collectors=component_data["solar_collectors"],
            thermal_energy_storages=component_data["thermal_energy_storages"],
            unitary_air_conditioners=component_data["unitary_air_conditioners"],
            vapor_compression_chillers=component_data["vapor_compression_chillers"]
        )

    def to_dict(self):
        return dataclass_to_dict(self, "records")


@dataclass
class Distribution:
    _index = "code"

    thermal_grid: pd.DataFrame

    @classmethod
    def init_database(cls, locator: InputLocator):
        thermal_grid = pd.read_csv(locator.get_database_components_distribution_thermal_grid()).set_index("code")
        return cls(thermal_grid)

    def to_dict(self):
        return dataclass_to_dict(self)


@dataclass
class Feedstocks:
    # FIXME: Ensure that there is a proper index for the DataFrame i.e. Rsun code
    _index = "code"

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
        # Temporarily add dummy index to DataFrame for serialization
        new_df = self.energy_carriers.copy()
        new_df['index'] = new_df['code'] + '_' + new_df['mean_qual']
        new_obj = Feedstocks(new_df.set_index('index'), self._library)

        return dataclass_to_dict(new_obj)


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
        return dataclass_to_dict(self)

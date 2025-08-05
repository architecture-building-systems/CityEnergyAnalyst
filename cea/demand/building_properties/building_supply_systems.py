"""
Building supply systems properties
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from cea.demand.building_properties.base import BuildingPropertiesDatabase

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


class BuildingSupplySystems(BuildingPropertiesDatabase):
    """
    Groups building supply systems properties used for the calc-thermal-loads functions.
    """

    def __init__(self, locator: InputLocator, building_names: list[str]):
        """
        Read building supply systems properties from input files and construct a new BuildingSupplySystems object.

        :param locator: an InputLocator for locating the input files
        :param building_names: list of buildings to read properties for
        """
        prop_supply_systems_building = pd.read_csv(locator.get_building_supply()).set_index('name').loc[building_names]
        self._prop_supply_systems = self.get_properties_supply_systems(locator, prop_supply_systems_building)

    @staticmethod
    def get_properties_supply_systems(locator: InputLocator, properties_supply: pd.DataFrame):
        # Supply system mappings: (locator_method, join_column, column_renames, fields_to_extract)
        supply_mappings = {
            'supply heating': (
                locator.get_database_assemblies_supply_heating(),
                'supply_type_hs',
                {"feedstock": "source_hs", "scale": "scale_hs", "efficiency": "eff_hs"},
                ['source_hs', 'scale_hs', 'eff_hs']
            ),
            'supply cooling': (
                locator.get_database_assemblies_supply_cooling(),
                'supply_type_cs',
                {"feedstock": "source_cs", "scale": "scale_cs", "efficiency": "eff_cs"},
                ['source_cs', 'scale_cs', 'eff_cs']
            ),
            'supply dhw': (
                locator.get_database_assemblies_supply_hot_water(),
                'supply_type_dhw',
                {"feedstock": "source_dhw", "scale": "scale_dhw", "efficiency": "eff_dhw"},
                ['source_dhw', 'scale_dhw', 'eff_dhw']
            ),
            'supply electricity': (
                locator.get_database_assemblies_supply_electricity(),
                'supply_type_el',
                {"feedstock": "source_el", "scale": "scale_el", "efficiency": "eff_el"},
                ['source_el', 'scale_el', 'eff_el']
            )
        }

        return BuildingSupplySystems.map_database_properties(properties_supply, supply_mappings)

    def __getitem__(self, building_name: str) -> dict:
        """Get supply systems properties of a building by name"""
        if building_name not in self._prop_supply_systems.index:
            raise KeyError(f"Building supply systems properties for {building_name} not found")
        return self._prop_supply_systems.loc[building_name].to_dict()

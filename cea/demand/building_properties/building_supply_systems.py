"""
Building supply systems properties
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from cea.datamanagement.database.assemblies import Supply
from cea.demand.building_properties.base import BuildingPropertiesDatabase, DatabaseMapping

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
        # Supply system mappings using DatabaseMapping dataclass
        # NOTE: Only scale is extracted. Efficiency and feedstock calculations moved to final-energy module.
        supply_database = Supply.from_locator(locator)

        supply_mappings = {
            'supply heating': DatabaseMapping(
                data=supply_database.heating,
                join_column='supply_type_hs',
                fields=['scale_hs'],
                column_renames={"scale": "scale_hs"}
            ),
            'supply cooling': DatabaseMapping(
                data=supply_database.cooling,
                join_column='supply_type_cs',
                fields=['scale_cs'],
                column_renames={"scale": "scale_cs"}
            ),
            'supply dhw': DatabaseMapping(
                data=supply_database.hot_water,
                join_column='supply_type_dhw',
                fields=['scale_dhw'],
                column_renames={"scale": "scale_dhw"}
            ),
            'supply electricity': DatabaseMapping(
                data=supply_database.electricity,
                join_column='supply_type_el',
                fields=['scale_el'],
                column_renames={"scale": "scale_el"}
            )
        }

        return BuildingSupplySystems.map_database_properties(properties_supply, supply_mappings)

    def __getitem__(self, building_name: str) -> dict:
        """Get supply systems properties of a building by name"""
        if building_name not in self._prop_supply_systems.index:
            raise KeyError(f"Building supply systems properties for {building_name} not found")
        return self._prop_supply_systems.loc[building_name].to_dict()

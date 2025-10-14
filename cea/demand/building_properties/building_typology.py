"""
Building typology properties
"""
from __future__ import annotations
from geopandas import GeoDataFrame as Gdf

from cea.datamanagement.databases_verification import COLUMNS_ZONE_TYPOLOGY

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


class BuildingTypology:
    """
    Groups building typology properties used for the calc-thermal-loads functions.
    """

    def __init__(self, locator: InputLocator, building_names: list[str]):
        """
        Read building typology properties from input shape files and construct a new BuildingTypology object.

        :param locator: an InputLocator for locating the input files
        :param building_names: list of buildings to read properties for
        """
        self._prop_typology = Gdf.from_file(locator.get_zone_geometry())[COLUMNS_ZONE_TYPOLOGY].set_index('name').loc[building_names]
        # Drop 'REFERENCE' column if it exists
        if 'reference' in self._prop_typology:
            self._prop_typology.drop('reference', axis=1, inplace=True)

    def __getitem__(self, building_name: str) -> dict:
        """Get typology properties of a building by name"""
        if building_name not in self._prop_typology.index:
            raise KeyError(f"Building typology properties for {building_name} not found")
        return self._prop_typology.loc[building_name].to_dict()

    def list_uses(self):
        """get list of all uses (typology types)"""
        return list(set(self._prop_typology['USE'].values))

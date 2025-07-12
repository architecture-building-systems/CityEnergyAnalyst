"""
Building internal loads properties
"""
from __future__ import annotations
import pandas as pd

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


class BuildingInternalLoads:
    """
    Groups building internal loads properties used for the calc-thermal-loads functions.
    """

    def __init__(self, locator: InputLocator, building_names: list[str]):
        """
        Read building internal loads properties from input files and construct a new BuildingInternalLoads object.

        :param locator: an InputLocator for locating the input files
        :param building_names: list of buildings to read properties for
        """
        self._prop_internal_loads = pd.read_csv(locator.get_building_internal()).set_index('name').loc[building_names]

    def __getitem__(self, building_name: str) -> dict:
        """Get internal loads properties of a building by name"""
        if building_name not in self._prop_internal_loads.index:
            raise KeyError(f"Building internal loads properties for {building_name} not found")
        return self._prop_internal_loads.loc[building_name].to_dict()

"""
Building comfort properties
"""
from __future__ import annotations
import pandas as pd

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


class BuildingComfort:
    """
    Groups building comfort properties used for the calc-thermal-loads functions.
    """

    def __init__(self, locator: InputLocator, building_names: list[str]):
        """
        Read building comfort properties from input files and construct a new BuildingComfort object.

        :param locator: an InputLocator for locating the input files
        :param building_names: list of buildings to read properties for
        """
        self._prop_comfort = pd.read_csv(locator.get_building_comfort()).set_index('name').loc[building_names]

    def __getitem__(self, building_name: str) -> dict:
        """Get comfort properties of a building by name"""
        if building_name not in self._prop_comfort.index:
            raise KeyError(f"Building comfort properties for {building_name} not found")
        return self._prop_comfort.loc[building_name].to_dict()

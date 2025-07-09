"""
Building supply systems properties
"""
from __future__ import annotations
import pandas as pd

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


class BuildingSupplySystems:
    """
    Groups building supply systems properties used for the calc-thermal-loads functions.
    """

    def __init__(self, locator: InputLocator, building_names: list[str]):
        """
        Read building supply systems properties from input files and construct a new BuildingSupplySystems object.

        :param locator: an InputLocator for locating the input files
        :param building_names: list of buildings to read properties for
        """
        if building_names is None:
            building_names = locator.get_zone_building_names()

        prop_supply_systems_building = pd.read_csv(locator.get_building_supply())
        self._prop_supply_systems = self.get_properties_supply_sytems(locator, prop_supply_systems_building).set_index('name')

    @staticmethod
    def get_properties_supply_sytems(locator, properties_supply):
        supply_heating = pd.read_csv(locator.get_database_assemblies_supply_heating())
        supply_dhw = pd.read_csv(locator.get_database_assemblies_supply_hot_water())
        supply_cooling = pd.read_csv(locator.get_database_assemblies_supply_cooling())
        supply_electricity = pd.read_csv(locator.get_database_assemblies_supply_electricity())

        df_emission_heating = properties_supply.merge(supply_heating, left_on='supply_type_hs', right_on='code')
        df_emission_cooling = properties_supply.merge(supply_cooling, left_on='supply_type_cs', right_on='code')
        df_emission_dhw = properties_supply.merge(supply_dhw, left_on='supply_type_dhw', right_on='code')
        df_emission_electricity = properties_supply.merge(supply_electricity, left_on='supply_type_el', right_on='code')

        df_emission_heating.rename(columns={"feedstock": "source_hs", "scale": "scale_hs", "efficiency": "eff_hs"},
                                   inplace=True)
        df_emission_cooling.rename(columns={"feedstock": "source_cs", "scale": "scale_cs", "efficiency": "eff_cs"},
                                   inplace=True)
        df_emission_dhw.rename(columns={"feedstock": "source_dhw", "scale": "scale_dhw", "efficiency": "eff_dhw"},
                               inplace=True)
        df_emission_electricity.rename(columns={"feedstock": "source_el", "scale": "scale_el", "efficiency": "eff_el"},
                                       inplace=True)

        fields_emission_heating = ['name', 'supply_type_hs', 'supply_type_cs', 'supply_type_dhw', 'supply_type_el',
                                   'source_hs', 'scale_hs', 'eff_hs']
        fields_emission_cooling = ['name', 'source_cs', 'scale_cs', 'eff_cs']
        fields_emission_dhw = ['name', 'source_dhw', 'scale_dhw', 'eff_dhw']
        fields_emission_el = ['name', 'source_el', 'scale_el', 'eff_el']

        result = df_emission_heating[fields_emission_heating].merge(df_emission_cooling[fields_emission_cooling], on='name')\
            .merge(df_emission_dhw[fields_emission_dhw], on='name').merge(df_emission_electricity[fields_emission_el], on='name')

        return result

    def __getitem__(self, building_name: str) -> dict:
        """Get supply systems properties of a building by name"""
        return self._prop_supply_systems.loc[building_name].to_dict()

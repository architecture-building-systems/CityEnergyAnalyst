"""
Building envelope properties
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from cea.demand.building_properties.base import BuildingPropertiesDatabase

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


class BuildingEnvelope(BuildingPropertiesDatabase):
    """
    Groups building envelope properties used for the calc-thermal-loads functions.
    """

    def __init__(self, locator: InputLocator, building_names: list[str]):
        """
        Read building envelope properties from input shape files and construct a new BuildingEnvelope object.

        :param locator: an InputLocator for locating the input files
        :param building_names: list of buildings to read properties for
        """
        prop_envelope = pd.read_csv(locator.get_building_architecture()).set_index('name').loc[building_names]
        self._prop_envelope = self.get_envelope_properties(locator, prop_envelope)

    @staticmethod
    def get_envelope_properties(locator: InputLocator, prop_envelope: pd.DataFrame) -> pd.DataFrame:
        """
        Gets the building envelope properties from
        ``databases/Systems/emission_systems.csv``, including the following:

        - prop_roof: name, emissivity (e_roof), absorbtivity (a_roof), thermal resistance (U_roof), and fraction of
          heated space (Hs).
        - prop_wall: name, emissivity (e_wall), absorbtivity (a_wall), thermal resistance (U_wall & U_base),
          window to wall ratio of north, east, south, west walls (wwr_north, wwr_east, wwr_south, wwr_west).
        - prop_win: name, emissivity (e_win), solar factor (G_win), thermal resistance (U_win)
        - prop_shading: name, shading factor (rf_sh).
        - prop_construction: name, internal heat capacity (Cm_af), floor to ceiling voids (void_deck).
        - prop_leakage: name, exfiltration (n50).

        Creates a merged df containing aforementioned envelope properties called envelope_prop.

        :return: envelope_prop
        :rtype: DataFrame

        """
        # Database mappings: (locator_method, join_column_name, columns_to_extract)
        db_mappings = {
            'envelope construction': (
                locator.get_database_assemblies_envelope_mass,
                'type_mass',
                # TODO: Remove columns from building envelope properties from database filter
                ['Cm_Af', 'void_deck', 'Hs', 'Ns', 'Es', 'occupied_bg']
            ),
            'envelope leakage': (
                locator.get_database_assemblies_envelope_tightness,
                'type_leak',
                ['n50']
            ),
            'envelope roof': (
                locator.get_database_assemblies_envelope_roof,
                'type_roof',
                ['e_roof', 'a_roof', 'U_roof']
            ),
            'envelope wall': (
                locator.get_database_assemblies_envelope_wall,
                'type_wall',
                ['wwr_north', 'wwr_west', 'wwr_east', 'wwr_south', 'e_wall', 'a_wall', 'U_wall']),
            'envelope window': (
                locator.get_database_assemblies_envelope_window,
                'type_win',
                ['e_win', 'G_win', 'U_win', 'F_F']),
            'envelope shading':
                (locator.get_database_assemblies_envelope_shading,
                 'type_shade',
                 ['rf_sh']),
            'envelope floor': (
                locator.get_database_assemblies_envelope_floor,
                'type_base',
                ['U_base'])
        }

        return BuildingEnvelope.merge_database_properties(prop_envelope, db_mappings)

    def __getitem__(self, building_name: str) -> dict:
        """Get envelope properties of a building by name"""
        if building_name not in self._prop_envelope.index:
            raise KeyError(f"Building envelope properties for {building_name} not found")
        return self._prop_envelope.loc[building_name].to_dict()

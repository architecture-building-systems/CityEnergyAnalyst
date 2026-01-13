"""
Building envelope properties
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from cea.datamanagement.database.assemblies import Envelope
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
        - prop_construction: name, internal heat capacity (Cm_af).
        - prop_leakage: name, exfiltration (n50).

        Creates a merged df containing aforementioned envelope properties called envelope_prop.

        :return: envelope_prop
        :rtype: DataFrame

        """
        # TODO: Get mappings from schema or similar to avoid hardcoding
        # Database mappings: (db_dataframe, join_column_name, columns_to_extract)
        envelope_database = Envelope.from_locator(locator)
        db_mappings = {
            'envelope construction': (
                envelope_database.mass,
                'type_mass',
                None,
                ['Cm_Af']
            ),
            'envelope leakage': (
                envelope_database.tightness,
                'type_leak',
                None,
                ['n50']
            ),
            'envelope roof': (
                envelope_database.roof,
                'type_roof',
                None,
                ['e_roof', 'a_roof', 'U_roof']
            ),
            'envelope wall': (
                envelope_database.wall,
                'type_wall',
                None,
                ['e_wall', 'a_wall', 'U_wall']
            ),
            'envelope window': (
                envelope_database.window,
                'type_win',
                None,
                ['e_win', 'G_win', 'U_win', 'F_F']
            ),
            'envelope shading': (
                envelope_database.shading,
                'type_shade',
                None,
                ['rf_sh']
            ),
            'envelope floor': (
                envelope_database.floor,
                'type_base',
                None,
                ['U_base'])
        }

        return BuildingEnvelope.map_database_properties(prop_envelope, db_mappings)

    def __getitem__(self, building_name: str) -> dict:
        """Get envelope properties of a building by name"""
        if building_name not in self._prop_envelope.index:
            raise KeyError(f"Building envelope properties for {building_name} not found")
        return self._prop_envelope.loc[building_name].to_dict()

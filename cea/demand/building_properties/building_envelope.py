"""
Building envelope properties
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from cea.datamanagement.database.assemblies import Envelope
from cea.demand.building_properties.base import BuildingPropertiesDatabase, DatabaseMapping

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
        envelope_database = Envelope.from_locator(locator)

        db_mappings = {
            'envelope construction': DatabaseMapping(
                data=envelope_database.mass,
                join_column='type_mass',
                fields=['Cm_Af']
            ),
            'envelope leakage': DatabaseMapping(
                data=envelope_database.tightness,
                join_column='type_leak',
                fields=['n50']
            ),
            'envelope roof': DatabaseMapping(
                data=envelope_database.roof,
                join_column='type_roof',
                fields=['e_roof', 'a_roof', 'U_roof']
            ),
            'envelope wall': DatabaseMapping(
                data=envelope_database.wall,
                join_column='type_wall',
                fields=['e_wall', 'a_wall', 'U_wall']
            ),
            'envelope window': DatabaseMapping(
                data=envelope_database.window,
                join_column='type_win',
                fields=['e_win', 'G_win', 'U_win', 'F_F']
            ),
            'envelope shading': DatabaseMapping(
                data=envelope_database.shading,
                join_column='type_shade',
                fields=['rf_sh', 'shading_location', 'shading_setpoint_Wm2'],
                field_defaults={
                    'shading_location': 'interior',
                    'shading_setpoint_Wm2': 300
                }
            ),
            'envelope floor': DatabaseMapping(
                data=envelope_database.floor,
                join_column='type_base',
                fields=['U_base']
            )
        }

        return BuildingEnvelope.map_database_properties(prop_envelope, db_mappings)

    def __getitem__(self, building_name: str) -> dict:
        """Get envelope properties of a building by name"""
        if building_name not in self._prop_envelope.index:
            raise KeyError(f"Building envelope properties for {building_name} not found")
        return self._prop_envelope.loc[building_name].to_dict()

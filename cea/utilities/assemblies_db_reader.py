from __future__ import annotations
import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


class EnvelopeDBReader:
    def __init__(self, locator: InputLocator):
        self.locator = locator
        self.wall_db = pd.read_csv(self.locator.get_database_assemblies_envelope_wall())
        self.roof_db = pd.read_csv(self.locator.get_database_assemblies_envelope_roof())
        self.floor_db = pd.read_csv(self.locator.get_database_assemblies_envelope_floor())
        self.window_db = pd.read_csv(self.locator.get_database_assemblies_envelope_window())

    def get_item_value(self, code: str, col: str) -> float | int:
        """Get the value of a specific item from the envelope database.

        :param code: The code of the item to retrieve.
        :type code: str
        :param col: The column to retrieve the value from. Allowed values are (in string):

            - `U`
            - `GHG_kgCO2m2`
            - `GHG_biogenic_kgCO2m2`
            - `Service_Life`

        :type col: str
        :raises ValueError: _description_
        :return: _description_
        :rtype: float | int
        """
        # search code in all four databases
        allowed_cols = ["U", "GHG_kgCO2m2", "GHG_biogenic_kgCO2m2", "Service_Life"]
        if code in self.wall_db['code'].values:
            mapping_dict = {
                allowed_cols[0]: "U_wall",
                allowed_cols[1]: "GHG_wall_kgCO2m2", 
                allowed_cols[2]: "GHG_biogenic_wall_kgCO2m2",
                allowed_cols[3]: "Service_Life_wall",
            }
            value = self.wall_db.loc[self.wall_db['code'] == code, mapping_dict[col]].values[0]
        elif code in self.roof_db['code'].values:
            mapping_dict = {
                allowed_cols[0]: "U_roof",
                allowed_cols[1]: "GHG_roof_kgCO2m2",
                allowed_cols[2]: "GHG_biogenic_roof_kgCO2m2",
                allowed_cols[3]: "Service_Life_roof",
            }
            value = self.roof_db.loc[self.roof_db['code'] == code, mapping_dict[col]].values[0]
        elif code in self.floor_db['code'].values:
            mapping_dict = {
                allowed_cols[0]: "U_floor",
                allowed_cols[1]: "GHG_floor_kgCO2m2",
                allowed_cols[2]: "GHG_biogenic_floor_kgCO2m2",
                allowed_cols[3]: "Service_Life_floor",
            }
            value = self.floor_db.loc[self.floor_db['code'] == code, mapping_dict[col]].values[0]
        elif code in self.window_db['code'].values:
            mapping_dict = {
                allowed_cols[0]: "U_win",
                allowed_cols[1]: "GHG_win_kgCO2m2",
                allowed_cols[2]: "GHG_biogenic_win_kgCO2m2",
                allowed_cols[3]: "Service_Life_win",
            }
            value = self.window_db.loc[self.window_db['code'] == code, mapping_dict[col]].values[0]
        else:
            raise ValueError(f"Code '{code}' not found in any database.")

        if col == "Service_Life":
            return int(value) if value is not None else None
        return float(value) if value is not None else None

"""
Building envelope properties
"""
from __future__ import annotations
import pandas as pd

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


class BuildingEnvelope:
    """
    Groups building envelope properties used for the calc-thermal-loads functions.
    """

    def __init__(self, locator: InputLocator, building_names: list[str]):
        """
        Read building envelope properties from input shape files and construct a new BuildingEnvelope object.

        :param locator: an InputLocator for locating the input files
        :param building_names: list of buildings to read properties for
        """
        if building_names is None:
            building_names = locator.get_zone_building_names()

        prop_architectures = pd.read_csv(locator.get_building_architecture())
        self._prop_envelope = self.get_envelope_properties(locator, prop_architectures).set_index('name')

    @staticmethod
    def get_envelope_properties(locator: InputLocator, prop_architecture: pd.DataFrame) -> pd.DataFrame:
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

        def check_successful_merge(df_construction, df_leakage, df_roof, df_wall, df_win, df_shading, df_floor):
            if len(df_construction.loc[df_construction['code'].isna()]) > 0:
                raise ValueError(
                    'WARNING: Invalid construction type found in architecture inputs. The following buildings will not be modeled: {}.'.format(
                        list(df_construction.loc[df_shading['code'].isna()]['name'])))
            if len(df_leakage.loc[df_leakage['code'].isna()]) > 0:
                raise ValueError(
                    'WARNING: Invalid leakage type found in architecture inputs. The following buildings will not be modeled: {}.'.format(
                        list(df_leakage.loc[df_leakage['code'].isna()]['name'])))
            if len(df_roof[df_roof['code'].isna()]) > 0:
                raise ValueError(
                    'WARNING: Invalid roof type found in architecture inputs. The following buildings will not be modeled: {}.'.format(
                        list(df_roof.loc[df_roof['code'].isna()]['name'])))
            if len(df_wall.loc[df_wall['code'].isna()]) > 0:
                raise ValueError(
                    'WARNING: Invalid wall type found in architecture inputs. The following buildings will not be modeled: {}.'.format(
                        list(df_wall.loc[df_wall['code'].isna()]['name'])))
            if len(df_win.loc[df_win['code'].isna()]) > 0:
                raise ValueError(
                    'WARNING: Invalid window type found in architecture inputs. The following buildings will not be modeled: {}.'.format(
                        list(df_win.loc[df_win['code'].isna()]['name'])))
            if len(df_shading.loc[df_shading['code'].isna()]) > 0:
                raise ValueError(
                    'WARNING: Invalid shading type found in architecture inputs. The following buildings will not be modeled: {}.'.format(
                        list(df_shading.loc[df_shading['code'].isna()]['name'])))
            if len(df_floor.loc[df_floor['code'].isna()]) > 0:
                raise ValueError(
                    'WARNING: Invalid floor type found in architecture inputs. The following buildings will not be modeled: {}.'.format(
                        list(df_floor.loc[df_floor['code'].isna()]['name'])))

        prop_roof = pd.read_csv(locator.get_database_assemblies_envelope_roof())
        prop_wall = pd.read_csv(locator.get_database_assemblies_envelope_wall())
        prop_floor = pd.read_csv(locator.get_database_assemblies_envelope_floor())
        prop_win = pd.read_csv(locator.get_database_assemblies_envelope_window())
        prop_shading = pd.read_csv(locator.get_database_assemblies_envelope_shading())
        prop_construction = pd.read_csv(locator.get_database_assemblies_envelope_mass())
        prop_leakage = pd.read_csv(locator.get_database_assemblies_envelope_tightness())

        df_construction = prop_architecture.merge(prop_construction, left_on='type_mass', right_on='code', how='left')
        df_leakage = prop_architecture.merge(prop_leakage, left_on='type_leak', right_on='code', how='left')
        df_floor = prop_architecture.merge(prop_floor, left_on='type_base', right_on='code', how='left')
        df_roof = prop_architecture.merge(prop_roof, left_on='type_roof', right_on='code', how='left')
        df_wall = prop_architecture.merge(prop_wall, left_on='type_wall', right_on='code', how='left')
        df_win = prop_architecture.merge(prop_win, left_on='type_win', right_on='code', how='left')
        df_shading = prop_architecture.merge(prop_shading, left_on='type_shade', right_on='code', how='left')

        check_successful_merge(df_construction, df_leakage, df_roof, df_wall, df_win, df_shading, df_floor)

        fields_construction = ['name', 'Cm_Af', 'void_deck', 'Hs', 'Ns', 'Es', 'occupied_bg']
        fields_leakage = ['name', 'n50']
        fields_basement = ['name', 'U_base']
        fields_roof = ['name', 'e_roof', 'a_roof', 'U_roof']
        fields_wall = ['name', 'wwr_north', 'wwr_west', 'wwr_east', 'wwr_south', 'e_wall', 'a_wall', 'U_wall']
        fields_win = ['name', 'e_win', 'G_win', 'U_win', 'F_F']
        fields_shading = ['name', 'rf_sh']

        envelope_prop = df_roof[fields_roof].merge(df_wall[fields_wall], on='name').merge(df_win[fields_win],
                                                                                          on='name').merge(
            df_shading[fields_shading], on='name').merge(df_construction[fields_construction], on='name').merge(
            df_leakage[fields_leakage], on='name').merge(
            df_floor[fields_basement], on='name')

        return envelope_prop

    def __getitem__(self, building_name: str) -> dict:
        """Get envelope properties of a building by name"""
        return self._prop_envelope.loc[building_name].to_dict()

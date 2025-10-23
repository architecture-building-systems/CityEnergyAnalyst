"""
Building HVAC properties
"""
from __future__ import annotations

from collections import namedtuple
from datetime import datetime
from typing import TYPE_CHECKING

import pandas as pd

from cea.demand.building_properties.base import BuildingPropertiesDatabase

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


class BuildingHVAC(BuildingPropertiesDatabase):
    """
    Groups building HVAC properties used for the calc-thermal-loads functions.
    """

    def __init__(self, locator: InputLocator, building_names: list[str]):
        """
        Read building HVAC properties from input shape files and construct a new BuildingHVAC object.

        :param locator: an InputLocator for locating the input files
        :param building_names: list of buildings to read properties for
        """
        prop_hvac = pd.read_csv(locator.get_building_air_conditioning()).set_index('name').loc[building_names]
        # get temperatures of operation
        self._prop_hvac = self.get_properties_technical_systems(locator, prop_hvac)

    @staticmethod
    def get_properties_technical_systems(locator: InputLocator, prop_hvac: pd.DataFrame):
        """
        Return temperature data per building based on the HVAC systems of the building. Uses the `emission_systems.xls`
        file to look up properties

        :param locator: an InputLocator for locating the input files
        :type locator: cea.inputlocator.InputLocator

        :param prop_hvac: HVAC properties for each building (type of cooling system, control system, domestic hot water
                          system and heating system.
        :type prop_hvac: geopandas.GeoDataFrame

        Sample data (first 5 rows)::

                         name type_cs type_ctrl type_dhw type_hs type_vent
                0     B154862      T0        T1       T1      T1       T0
                1     B153604      T0        T1       T1      T1       T0
                2     B153831      T0        T1       T1      T1       T0
                3  B302022960      T0        T0       T0      T0       T0
                4  B302034063      T0        T0       T0      T0       T0

        :returns: A DataFrame containing temperature data for each building in the scenario. More information can be
        :rtype: DataFrame

        Each row contains the following fields:

        ==========    =======   ===========================================================================
        Column           e.g.   Description
        ==========    =======   ===========================================================================
        name          B154862   (building name)
        type_hs            T1   (copied from input, code for type of heating system)
        type_cs            T0   (copied from input, code for type of cooling system)
        type_dhw           T1   (copied from input, code for type of hot water system)
        type_ctrl          T1   (copied from input, code for type of controller for heating and cooling system)
        type_vent          T1   (copied from input, code for type of ventilation system)
        Tshs0_C            90   (heating system supply temperature at nominal conditions [C])
        dThs0_C            20   (delta of heating system temperature at nominal conditions [C])
        Qhsmax_Wm2        500   (maximum heating system power capacity per unit of gross built area [W/m2])
        dThs_C           0.15   (correction temperature of emission losses due to type of heating system [C])
        Tscs0_C             0   (cooling system supply temperature at nominal conditions [C])
        dTcs0_C             0   (delta of cooling system temperature at nominal conditions [C])
        Qcsmax_Wm2          0   (maximum cooling system power capacity per unit of gross built area [W/m2])
        dTcs_C            0.5   (correction temperature of emission losses due to type of cooling system [C])
        dT_Qhs            1.2   (correction temperature of emission losses due to control system of heating [C])
        dT_Qcs           -1.2   (correction temperature of emission losses due to control system of cooling[C])
        Tsww0_C            60   (dhw system supply temperature at nominal conditions [C])
        Qwwmax_Wm2        500   (maximum dwh system power capacity per unit of gross built area [W/m2])
        MECH_VENT        True   (copied from input, ventilation system configuration)
        WIN_VENT        False   (copied from input, ventilation system configuration)
        HEAT_REC         True   (copied from input, ventilation system configuration)
        NIGHT_FLSH       True   (copied from input, ventilation system control strategy)
        ECONOMIZER      False   (copied from input, ventilation system control strategy)
        ==========    =======   ===========================================================================

        Data is read from :py:meth:`cea.inputlocator.InputLocator.get_technical_emission_systems`
        (e.g.
        ``db/Systems/emission_systems.csv``)

        """

        # HVAC database mappings: (locator_method, join_column, column_renames, fields_to_extract)
        hvac_mappings = {
            'hvac heating': (
                locator.get_database_assemblies_hvac_heating(),
                'hvac_type_hs',
                None,
                # TODO: Remove columns from building hvac properties from database filter
                ['class_hs', 'convection_hs', 'Qhsmax_Wm2', 'dThs_C', 'Tshs0_ahu_C', 'dThs0_ahu_C', 'Th_sup_air_ahu_C',
                 'Tshs0_aru_C', 'dThs0_aru_C', 'Th_sup_air_aru_C', 'Tshs0_shu_C', 'dThs0_shu_C']
            ),
            'hvac cooling': (
                locator.get_database_assemblies_hvac_cooling(),
                'hvac_type_cs',
                None,
                ['Qcsmax_Wm2', 'dTcs_C', 'Tscs0_ahu_C', 'dTcs0_ahu_C', 'Tc_sup_air_ahu_C',
                 'Tscs0_aru_C', 'dTcs0_aru_C', 'Tc_sup_air_aru_C', 'Tscs0_scu_C', 'dTcs0_scu_C',
                 'class_cs', 'convection_cs']
            ),
            'hvac control': (
                locator.get_database_assemblies_hvac_controller(),
                'hvac_type_ctrl',
                None,
                ['dT_Qhs', 'dT_Qcs']
            ),
            'hvac dhw': (
                locator.get_database_assemblies_hvac_hot_water(),
                'hvac_type_dhw',
                None,
                ['class_dhw', 'Tsww0_C', 'Qwwmax_Wm2']
            ),
            'hvac ventilation': (
                locator.get_database_assemblies_hvac_ventilation(),
                'hvac_type_vent',
                None,
                ['MECH_VENT', 'WIN_VENT', 'HEAT_REC', 'NIGHT_FLSH', 'ECONOMIZER']
            )
        }

        result = BuildingHVAC.map_database_properties(prop_hvac, hvac_mappings)

        # verify hvac and ventilation combination
        verify_hvac_system_combination(result, locator)
        # read region-specific control parameters (identical for all buildings), i.e. heating and cooling season
        result['has-heating-season'] = result.apply(lambda x: verify_has_season(x.index,
                                                                                x['hvac_heat_starts'],
                                                                                x['hvac_heat_ends']), axis=1)
        result['has-cooling-season'] = result.apply(lambda x: verify_has_season(x.index,
                                                                                x['hvac_cool_starts'],
                                                                                x['hvac_cool_ends']), axis=1)

        # verify seasons do not overlap
        result['overlap-season'] = result.apply(lambda x: verify_overlap_season(x.index,
                                                                                x['has-heating-season'],
                                                                                x['has-cooling-season'],
                                                                                x['hvac_heat_starts'],
                                                                                x['hvac_heat_ends'],
                                                                                x['hvac_cool_starts'],
                                                                                x['hvac_cool_ends']), axis=1)
        return result

    def __getitem__(self, building_name: str) -> dict:
        """Get HVAC properties of a building by name"""
        if building_name not in self._prop_hvac.index:
            raise KeyError(f"Building HVAC properties for {building_name} not found")
        return self._prop_hvac.loc[building_name].to_dict()


def verify_overlap_season(building_name, has_heating_season, has_cooling_season, heat_start, heat_end, cool_start,
                          cool_end):
    if has_cooling_season and has_heating_season:
        Range = namedtuple('Range', ['start', 'end'])

        # for heating
        day1, month1 = map(int, heat_start.split('|'))
        day2, month2 = map(int, heat_end.split('|'))
        if month2 > month1:
            r1 = Range(start=datetime(2012, month1, day1), end=datetime(2012, month2, day2))
        else:
            r1 = Range(start=datetime(2012, month1, day1), end=datetime(2013, month2, day2))

        # for cooling
        day1, month1 = map(int, cool_start.split('|'))
        day2, month2 = map(int, cool_end.split('|'))
        if month2 > month1:
            r2 = Range(start=datetime(2012, month1, day1), end=datetime(2012, month2, day2))
        else:
            r2 = Range(start=datetime(2012, month1, day1), end=datetime(2013, month2, day2))

        latest_start = max(r1.start, r2.start)
        earliest_end = min(r1.end, r2.end)
        delta = (earliest_end - latest_start).days + 1
        overlap = max(0, delta)
        if overlap > 0:
            raise Exception(
                'invalid input found for building %s. heating and cooling seasons cannot overlap in CEA' % building_name)
        else:
            return False


# TODO: Remove building_name from function signature, not useful in function
def verify_has_season(building_name, start, end):
    def invalid_date(date):
        if len(date) != 5 or "|" not in date:
            return True
        elif "00" in date.split("|"):
            return True
        else:
            return False

    if start == '00|00' or end == '00|00':
        return False
    elif invalid_date(start) or invalid_date(end):
        raise Exception(
            'invalid input found for building %s. dates of season must comply to DD|MM format, DD|00 are values are not valid' % building_name)
    else:
        return True


def verify_hvac_system_combination(result, locator):
    """
    Verify that cooling systems requiring mechanical ventilation have it configured.

    CENTRAL_AC and HYBRID_AC systems require mechanical ventilation (MECH_VENT=True).
    If an invalid combination is found, raises ValueError with details.
    """
    # Find buildings with cooling systems that require mechanical ventilation
    needs_mech_vent = result['class_cs'].isin(['CENTRAL_AC', 'HYBRID_AC'])
    invalid_buildings = result[needs_mech_vent & ~result['MECH_VENT']]

    if invalid_buildings.empty:
        return

    # Load valid mechanical ventilation systems from database
    hvac_database = pd.read_csv(locator.get_database_assemblies_hvac_ventilation())
    mech_vent_systems = hvac_database.loc[hvac_database['MECH_VENT'], 'code'].tolist()

    # Build error messages for each invalid building
    error_messages = [
        f'\nBuilding {building_name} has cooling system {row.class_cs} '
        f'with ventilation system {row.hvac_type_vent}.'
        f'\nPlease re-assign a mechanical ventilation system from: {mech_vent_systems}'
        for building_name, row in invalid_buildings.iterrows()
    ]

    raise ValueError(
        'Invalid combination of cooling and ventilation systems selected. '
        'Please check the following buildings:\n' + '\n'.join(error_messages)
    )


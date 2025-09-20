"""
Building RC Model properties
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from cea.demand.constants import H_MS, H_IS, B_F, LAMBDA_AT
from cea.demand.building_properties.useful_areas import calc_useful_areas
from cea.demand.control_heating_cooling_systems import has_heating_system, has_cooling_system

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import geopandas as gpd
    from cea.inputlocator import InputLocator


class BuildingRCModel:
    """
    Groups building RC Model properties used for the calc-thermal-loads functions.
    """

    def __init__(self, locator: InputLocator, building_names: list[str],
                 typology: pd.DataFrame, envelope: pd.DataFrame, geometry: gpd.GeoDataFrame,
                 hvac_temperatures: pd.DataFrame):
        """
        Read building RC Model properties and construct a new BuildingRCModel object.

        :param locator: an InputLocator for locating the input files
        :param building_names: list of buildings to read properties for
        :param typology: Building typology properties
        :param envelope: Building envelope properties
        :param geometry: Building geometry properties
        :param hvac_temperatures: HVAC temperatures
        """
        self.building_names = building_names
        self._prop_rc_model = self.calc_prop_rc_model(locator, typology, envelope, geometry, hvac_temperatures)

    def __getitem__(self, building_name: str) -> dict:
        """Get RC model properties of a building by name"""
        return self._prop_rc_model.loc[building_name].to_dict()

    def calc_prop_rc_model(self,
                           locator: InputLocator,
                           typology: pd.DataFrame,
                           envelope: pd.DataFrame,
                           geometry: gpd.GeoDataFrame,
                           hvac_temperatures: pd.DataFrame) -> pd.DataFrame:
        """
        Return the RC model properties for all buildings. The RC model used is described in ISO 13790:2008, Annex C (Full
        set of equations for simple hourly method).

        :param locator: an InputLocator for locating the input files

        :param typology: The contents of the `typology.shp` file, indexed by building name. Each column is the name of an
            typology type (GYM, HOSPITAL, HOTEL, INDUSTRIAL, MULTI_RES, OFFICE, PARKING, etc.) except for the
            "PFloor" column which is a fraction of heated floor area.
            The typology types must add up to 1.0.

        :param envelope: The contents of the `architecture.shp` file, indexed by building name.
            It contains the following fields:

            - n50: Air tightness at 50 Pa [h^-1].
            - type_shade: shading system type.
            - win_wall: window to wall ratio.
            - U_base: U value of the floor construction [W/m2K]
            - U_roof: U value of roof construction [W/m2K]
            - U_wall: U value of wall construction [W/m2K]
            - U_win: U value of window construction [W/m2K]
            - Hs: Fraction of gross floor area that is heated/cooled {0 <= Hs <= 1}
            - Cm_Af: Internal heat capacity per unit of area [J/K.m2]

        :param geometry: The contents of the `zone.shp` file indexed by building name - the list of buildings, their floor
            counts, heights etc.
            Includes additional fields "footprint" and "perimeter" as calculated in `read_building_properties`.

        :param hvac_temperatures: The return value of `get_properties_technical_systems`.

        :returns: RC model properties per building

        Sample result data calculated or manipulated by this method:

        Name: B153767

        datatype: float64

        =========    ============   ================================================================================================
        Column        e.g.          Description
        =========    ============   ================================================================================================
        Atot         4.564827e+03   (area of all surfaces facing the building zone in [m2])
        Aw           4.527014e+02   (area of windows in [m2])
        Am           6.947967e+03   (effective mass area in [m2])
        Aef          2.171240e+03   (floor area with electricity in [m2])
        Af           2.171240e+03   (conditioned floor area (heated/cooled) in [m2])
        Cm           6.513719e+08   (internal heat capacity in [J/k])
        Htr_is       1.574865e+04   (thermal transmission coefficient between air and surface nodes in RC-model in [W/K])
        Htr_em       5.829963e+02   (thermal transmission coefficient between exterior and thermal mass nodes in RC-model in [W/K])
        Htr_ms       6.322650e+04   (thermal transmission coefficient between surface and thermal mass nodes in RC-model in [W/K])
        Htr_op       5.776698e+02   (thermal transmission coefficient for opaque surfaces in [W/K])
        Hg           2.857637e+02   (steady-state thermal transmission coefficient to the ground in [W/K])
        HD           2.919060e+02   (direct thermal transmission coefficient to the external environment in [W/K])
        Htr_w        1.403374e+03   (thermal transmission coefficient for windows and glazing in [W/K])
        =========    ============   ================================================================================================

        """

        # FIXME: Decide to use GFA from zone footprints or radiation geometry
        # (should be the same, but not always the case, since radiation geometry goes through simplification)

        # Calculate useful (electrified/conditioned/occupied) floor areas
        areas_df = calc_useful_areas(geometry, envelope)
        # calculate building geometry and update envelope areas
        self.geometry_reader_radiation_daysim(locator, envelope, geometry)

        df = pd.DataFrame(index=geometry.index)

        # df = df.merge(typology, left_index=True, right_index=True)

        for building in self.building_names:
            has_system_heating_flag = has_heating_system(hvac_temperatures.loc[building, 'class_hs'])
            has_system_cooling_flag = has_cooling_system(hvac_temperatures.loc[building, 'class_cs'])
            if not has_system_heating_flag and not has_system_cooling_flag and envelope.loc[building, 'Hs'] != 0.0:
                envelope.loc[building, 'Hs'] = 0.0
                print('Building {building} has no heating and cooling system, Hs corrected to 0.'.format(
                    building=building))

        # area of all surfaces facing the building zone
        df['Atot'] = areas_df['Af'] * LAMBDA_AT

        # if 'Cm_Af' in self.get_overrides_columns():
        #     # Internal heat capacity is not part of input, calculate [J/K]
        #     df['Cm'] = self._overrides['Cm_Af'] * df['Af']
        # else:
        df['Cm'] = envelope['Cm_Af'] * areas_df['Af']

        df['Am'] = envelope['Cm_Af'].apply(self.lookup_effective_mass_area_factor) * areas_df['Af']  # Effective mass area in [m2]

        # Steady-state Thermal transmittance coefficients and Internal heat Capacity
        # Thermal transmission coefficient for windows and glazing in [W/K]
        # Weigh area of windows with fraction of air-conditioned space, relationship of area and perimeter is squared
        df['Htr_w'] = envelope['Awin_ag'] * envelope['U_win'] * np.sqrt(areas_df['Hs_ag'])

        # check if buildings are completely above ground
        is_floating = (areas_df["void_deck"] > 0).astype(int)

        # direct thermal transmission coefficient to the external environment in [W/K]
        # Weigh area of with fraction of air-conditioned space, relationship of area and perimeter is squared
        df['HD'] = (envelope['Awall_ag'] * envelope['U_wall'] * np.sqrt(areas_df['Hs_ag']) # overall heat loss factor through vertical opaque facade
                    + envelope['Aroof'] * envelope['U_roof'] * areas_df['Hs_ag'] # overall heat loss factor through roof
                    + is_floating * envelope['Aunderside'] * envelope['U_base'] * areas_df['Hs_ag'] # overall heat loss factor through base above ground, 0 if building touches ground and base does not contact with air
                    )
        # steady-state Thermal transmission coefficient to the ground. in W/K
        # Aop_bg: opaque surface area below ground level;
        # U_base: basement U value, defined in envelope.csv
        # Hs_bg: Fraction of underground floor area air-conditioned.
        df['Hg'] = B_F * envelope['Aop_bg'] * envelope['U_base'] * areas_df['Hs_bg']

        # calculate RC model properties
        df['Htr_op'] = df['Hg'] + df['HD']
        df['Htr_ms'] = H_MS * df['Am']  # Coupling conductance 1 in W/K
        df['Htr_em'] = 1 / (1 / df['Htr_op'] - 1 / df['Htr_ms'])  # Coupling conductance 2 in W/K
        df['Htr_is'] = H_IS * df['Atot']
        
        return df


    def geometry_reader_radiation_daysim(self,
                                         locator: InputLocator,
                                         envelope: pd.DataFrame,
                                         geometry: pd.DataFrame) -> pd.DataFrame:
        """

        Reader which returns the radiation specific geometries from Daysim. Adjusts the imported data such that it is
        consistent with other imported geometry parameters.

        :param locator: an InputLocator for locating the input files

        :param envelope: The contents of the `envelope.csv` file indexed by building name.

        :param geometry: The contents of the `zone.shp` file indexed by building name.

        :return: Adjusted Daysim geometry data containing the following:

            - name: Name of building.
            - Awin_ag: Area of windows for each building (using mean window to wall ratio for building, excluding voids) [m2]
            - Awall_ag: Opaque wall areas above ground (excluding voids, windows and roof) [m2]
            - Aop_bg: Opaque areas below ground (including ground floor, excluding voids and windows) [m2]
            - Aroof: Area of the roof (considered flat and equal to the building footprint) [m2]
            - Aunderside: Area of the underside (only if building is floating, otherwise 0) [m2]
            # - GFA_m2: Gross floor area [m2]
            # - floors: Sum of floors below ground (floors_bg) and floors above ground (floors_ag) [m2]
            # - surface_volume: Surface to volume ratio [m^-1]

        :rtype: DataFrame

        Data is read from :py:meth:`cea.inputlocator.InputLocator.get_radiation_building`
        (e.g.
        ``C:/scenario/outputs/data/solar-radiation/{building_name}_radiation.csv``)

        Note: File generated by the radiation script. It contains the fields Name, Freeheight, FactorShade, height_ag and
        Shape_Leng. This data is used to calculate the wall and window areas.)

        """

        # add result columns to envelope df
        envelope['Awall_ag'] = np.nan
        envelope['Awin_ag'] = np.nan
        envelope['Aroof'] = np.nan
        envelope['Aunderside'] = np.nan

        # call all building geometry files in a loop
        for building_name in self.building_names:
            geometry_data = pd.read_csv(locator.get_radiation_building(building_name))
            envelope.loc[building_name, 'Awall_ag'] = geometry_data['walls_east_m2'][0] + \
                                                      geometry_data['walls_west_m2'][0] + \
                                                      geometry_data['walls_south_m2'][0] + \
                                                      geometry_data['walls_north_m2'][0]
            envelope.loc[building_name, 'Awin_ag'] = geometry_data['windows_east_m2'][0] + \
                                                     geometry_data['windows_west_m2'][0] + \
                                                     geometry_data['windows_south_m2'][0] + \
                                                     geometry_data['windows_north_m2'][0]
            envelope.loc[building_name, 'Aroof'] = geometry_data['roofs_top_m2'][0]
            if 'undersides_bottom_m2' not in geometry_data.columns:
                geometry_data['undersides_bottom_m2'] = 0
            envelope.loc[building_name, 'Aunderside'] = geometry_data['undersides_bottom_m2'][0]


        # adjust envelope areas with Void_deck
        envelope['Aop_bg'] = geometry['height_bg'] * geometry['perimeter'] + geometry['footprint']

        return envelope

    def lookup_effective_mass_area_factor(self, cm):
        """
        Look up the factor to multiply the conditioned floor area by to get the effective mass area by building
        construction type.
        This is used for the calculation of the effective mass area "Am" in `get_prop_RC_model`.
        Standard values can be found in the Annex G of ISO EN13790

        :param: cm: The internal heat capacity per unit of area [J/m2].

        :return: Effective mass area factor (0, 2.5 or 3.2 depending on cm value).

        """

        if cm == 0.0:
            return 0.0
        elif 0.0 < cm <= 165000.0:
            return 2.5
        else:
            return 3.2

"""
Classes of building properties
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from geopandas import GeoDataFrame as Gdf
from datetime import datetime
from collections import namedtuple
from cea.constants import HOURS_IN_YEAR
from cea.datamanagement.databases_verification import COLUMNS_ZONE_TYPOLOGY
from cea.demand import constants
from cea.demand.sensible_loads import calc_hr, calc_hc
from cea.technologies import blinds
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle", "Jimeno A. Fonseca", "Daren Thomas", "Jack Hawthorne", "Reynold Mok"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.utilities.standardize_coordinates import get_lat_lon_projected_shapefile, get_projected_coordinate_system

# import constants
H_MS = constants.H_MS
H_IS = constants.H_IS
B_F = constants.B_F
LAMBDA_AT = constants.LAMBDA_AT


class BuildingProperties(object):
    """
    Groups building properties used for the calc-thermal-loads functions. Stores the full DataFrame for each of the
    building properties and provides methods for indexing them by name.

    G. Happle   BuildingPropsThermalLoads   27.05.2016
    """

    def __init__(self, locator, weather_data, building_names=None):
        """
        Read building properties from input shape files and construct a new BuildingProperties object.

        :param locator: an InputLocator for locating the input files
        :type locator: cea.inputlocator.InputLocator

        :param List[str] building_names: list of buildings to read properties

        :returns: BuildingProperties
        :rtype: BuildingProperties
        """

        if building_names is None:
            building_names = locator.get_zone_building_names()

        self.building_names = building_names
        print("read input files")
        prop_geometry = Gdf.from_file(locator.get_zone_geometry())

        # reproject to projected coordinate system (in meters) to calculate area
        lat, lon = get_lat_lon_projected_shapefile(prop_geometry)
        target_crs = get_projected_coordinate_system(float(lat), float(lon))
        prop_geometry = prop_geometry.to_crs(target_crs)

        prop_geometry['footprint'] = prop_geometry.area
        prop_geometry['perimeter'] = prop_geometry.length
        prop_geometry['Blength'], prop_geometry['Bwidth'] = self.calc_bounding_box_geom(prop_geometry)
        prop_geometry = prop_geometry.drop('geometry', axis=1).set_index('name')
        prop_hvac = pd.read_csv(locator.get_building_air_conditioning())
        zone_gdf = Gdf.from_file(locator.get_zone_geometry())
        prop_typology = zone_gdf[COLUMNS_ZONE_TYPOLOGY].set_index('name')
        # Drop 'REFERENCE' column if it exists
        if 'reference' in prop_typology:
            prop_typology.drop('reference', axis=1, inplace=True)
        prop_architectures = pd.read_csv(locator.get_building_architecture())
        prop_comfort = pd.read_csv(locator.get_building_comfort()).set_index('name')
        prop_internal_loads = pd.read_csv(locator.get_building_internal()).set_index('name')
        prop_supply_systems_building = pd.read_csv(locator.get_building_supply())

        # GET SYSTEMS EFFICIENCIES
        prop_supply_systems = get_properties_supply_sytems(locator, prop_supply_systems_building).set_index('name')

        # get temperatures of operation
        prop_HVAC_result = get_properties_technical_systems(locator, prop_hvac).set_index('name')

        # get envelope properties
        prop_envelope = get_envelope_properties(locator, prop_architectures).set_index('name')

        # get properties of rc demand model
        prop_rc_model = self.calc_prop_rc_model(locator, prop_typology, prop_envelope,
                                                prop_geometry, prop_HVAC_result)

        # get solar properties
        solar = get_prop_solar(locator, building_names, prop_rc_model, prop_envelope, weather_data).set_index('name')

        # df_windows = geometry_reader.create_windows(surface_properties, prop_envelope)
        # TODO: to check if the Win_op and height of window is necessary.
        # TODO: maybe mergin branch i9 with CItyGML could help with this
        print("done")

        # save resulting data
        self._prop_supply_systems = prop_supply_systems
        self._prop_geometry = prop_geometry
        self._prop_envelope = prop_envelope
        self._prop_typology = prop_typology
        self._prop_HVAC_result = prop_HVAC_result
        self._prop_comfort = prop_comfort
        self._prop_internal_loads = prop_internal_loads
        self._prop_age = prop_typology[['year']]
        self._solar = solar
        self._prop_RC_model = prop_rc_model

    def calc_bounding_box_geom(self, gdf):
        """
        Calculate bounding box dimensions (length and width) for each geometry in the GeoDataFrame.

        Parameters:
        - gdf (GeoDataFrame): A GeoDataFrame containing building geometries.

        Returns:
        - Tuple[List[float], List[float]]: Two lists, one for bounding box lengths and another for widths.
        """
        bwidth = []
        blength = []

        for geom in gdf.geometry:
            if geom.is_empty:
                bwidth.append(0)
                blength.append(0)
                continue

            # Get bounding box (xmin, ymin, xmax, ymax)
            xmin, ymin, xmax, ymax = geom.bounds
            delta1 = abs(xmax - xmin)  # Horizontal length
            delta2 = abs(ymax - ymin)  # Vertical width

            # Determine which is length and which is width
            if delta1 >= delta2:
                bwidth.append(delta2)
                blength.append(delta1)
            else:
                bwidth.append(delta1)
                blength.append(delta2)

        return blength, bwidth

    def __len__(self):
        """return length of list_building_names"""
        return len(self.building_names)

    def list_building_names(self):
        """get list of all building names"""
        return self.building_names

    def list_uses(self):
        """get list of all uses (typology types)"""
        return list(set(self._prop_typology['USE'].values))

    def get_prop_supply_systems(self, name_building):
        """get geometry of a building by name"""
        return self._prop_supply_systems.loc[name_building].to_dict()

    def get_prop_geometry(self, name_building):
        """get geometry of a building by name"""
        return self._prop_geometry.loc[name_building].to_dict()

    def get_prop_envelope(self, name_building):
        """get the architecture and thermal properties of a building by name"""
        return self._prop_envelope.loc[name_building].to_dict()

    def get_prop_typology(self, name_building):
        """get the typology properties of a building by name"""
        return self._prop_typology.loc[name_building].to_dict()

    def get_prop_hvac(self, name_building):
        """get HVAC properties of a building by name"""
        return self._prop_HVAC_result.loc[name_building].to_dict()

    def get_prop_rc_model(self, name_building):
        """get RC-model properties of a building by name"""
        return self._prop_RC_model.loc[name_building].to_dict()

    def get_prop_comfort(self, name_building):
        """get comfort properties of a building by name"""
        return self._prop_comfort.loc[name_building].to_dict()

    def get_prop_internal_loads(self, name_building):
        """get internal loads properties of a building by name"""
        return self._prop_internal_loads.loc[name_building].to_dict()

    def get_prop_age(self, name_building):
        """get age properties of a building by name"""
        return self._prop_age.loc[name_building].to_dict()

    def get_solar(self, name_building):
        """get solar properties of a building by name"""
        return self._solar.loc[name_building]

    def calc_prop_rc_model(self, 
                           locator: InputLocator, 
                           typology: Gdf, 
                           envelope: Gdf, 
                           geometry: Gdf, 
                           hvac_temperatures: pd.DataFrame) -> pd.DataFrame:
        """
        Return the RC model properties for all buildings. The RC model used is described in ISO 13790:2008, Annex C (Full
        set of equations for simple hourly method).

        :param typology: The contents of the `typology.shp` file, indexed by building name. Each column is the name of an
            typology type (GYM, HOSPITAL, HOTEL, INDUSTRIAL, MULTI_RES, OFFICE, PARKING, etc.) except for the
            "PFloor" column which is a fraction of heated floor area.
            The typology types must add up to 1.0.
        :type typology: Gdf

        :param envelope: The contents of the `architecture.shp` file, indexed by building name.
            It contains the following fields:

            - n50: Air tightness at 50 Pa [h^-1].
            - type_shade: shading system type.
            - void_deck: Number of floors (from the ground up) with an open envelope.
            - win_wall: window to wall ratio.
            - U_base: U value of the floor construction [W/m2K]
            - U_roof: U value of roof construction [W/m2K]
            - U_wall: U value of wall construction [W/m2K]
            - U_win: U value of window construction [W/m2K]
            - Hs: Fraction of gross floor area that is heated/cooled {0 <= Hs <= 1}
            - Cm_Af: Internal heat capacity per unit of area [J/K.m2]

        :type envelope: Gdf

        :param geometry: The contents of the `zone.shp` file indexed by building name - the list of buildings, their floor
            counts, heights etc.
            Includes additional fields "footprint" and "perimeter" as calculated in `read_building_properties`.
        :type geometry: Gdf

        :param hvac_temperatures: The return value of `get_properties_technical_systems`.
        :type hvac_temperatures: DataFrame

        :returns: RC model properties per building
        :rtype: DataFrame



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

        # calculate building geometry
        df = self.geometry_reader_radiation_daysim(locator, envelope, geometry)
        df = df.merge(typology, left_index=True, right_index=True)
        df = df.merge(hvac_temperatures, left_index=True, right_index=True)

        from cea.demand.control_heating_cooling_systems import has_heating_system, has_cooling_system

        for building in self.building_names:
            has_system_heating_flag = has_heating_system(hvac_temperatures.loc[building, 'class_hs'])
            has_system_cooling_flag = has_cooling_system(hvac_temperatures.loc[building, 'class_cs'])
            if (not has_system_heating_flag and not has_system_cooling_flag and
                    df.loc[building, 'Hs'] != 0.0):
                df.loc[building, 'Hs'] = 0.0
                print('Building {building} has no heating and cooling system, Hs corrected to 0.'.format(
                    building=building))

        # Calculate useful (electrified/conditioned/occupied) floor areas
        df = calc_useful_areas(df)

        if 'Cm_Af' in self.get_overrides_columns():
            # Internal heat capacity is not part of input, calculate [J/K]
            df['Cm'] = self._overrides['Cm_Af'] * df['Af']
        else:
            df['Cm'] = df['Cm_Af'] * df['Af']

        df['Am'] = df['Cm_Af'].apply(self.lookup_effective_mass_area_factor) * df['Af']  # Effective mass area in [m2]

        # Steady-state Thermal transmittance coefficients and Internal heat Capacity
        # Thermal transmission coefficient for windows and glazing in [W/K]
        # Weigh area of windows with fraction of air-conditioned space, relationship of area and perimeter is squared
        df['Htr_w'] = df['Awin_ag'] * df['U_win'] * np.sqrt(df['Hs_ag'])

        # check if buildings are completely above ground
        is_floating = (df["void_deck"] > 0).astype(int)

        # direct thermal transmission coefficient to the external environment in [W/K]
        # Weigh area of with fraction of air-conditioned space, relationship of area and perimeter is squared
        df['HD'] = (df['Awall_ag'] * df['U_wall'] * np.sqrt(df['Hs_ag']) # overall heat loss factor through vertical opaque facade
                    + df['Aroof'] * df['U_roof'] * df['Hs_ag'] # overall heat loss factor through roof
                    + is_floating * df['Aunderside'] * df['U_base'] * df['Hs_ag'] # overall heat loss factor through base above ground, 0 if building touches ground and base does not contact with air
                    )
        # steady-state Thermal transmission coefficient to the ground. in W/K
        # Aop_bg: opaque surface area below ground level;
        # U_base: basement U value, defined in envelope.csv
        # Hs_bg: Fraction of underground floor area air-conditioned.
        # 1 - is_above_ground: 1 if building touches ground, 0 if building is floating (void_deck > 0)
        df['Hg'] = B_F * df['Aop_bg'] * df['U_base'] * df['Hs_bg']

        # calculate RC model properties
        df['Htr_op'] = df['Hg'] + df['HD']
        df['Htr_ms'] = H_MS * df['Am']  # Coupling conductance 1 in W/K
        df['Htr_em'] = 1 / (1 / df['Htr_op'] - 1 / df['Htr_ms'])  # Coupling conductance 2 in W/K
        df['Htr_is'] = H_IS * df['Atot']

        fields = ['Atot', 'Awin_ag', 'Am', 'Aef', 'Af', 'Cm', 'Htr_is', 'Htr_em', 'Htr_ms', 'Htr_op', 'Hg', 'HD',
                  'Aroof', 'Aunderside', 'U_wall', 'U_roof', 'U_win', 'U_base', 'Htr_w', 'GFA_m2', 'Aocc', 'Aop_bg', 'Awall_ag', 'footprint']
        result = df[fields]

        return result


    def geometry_reader_radiation_daysim(self, 
                                         locator: InputLocator, 
                                         envelope: Gdf, 
                                         geometry: Gdf) -> pd.DataFrame:
        """

        Reader which returns the radiation specific geometries from Daysim. Adjusts the imported data such that it is
        consistent with other imported geometry parameters.

        :param locator: an InputLocator for locating the input files

        :param envelope: The contents of the `architecture.shp` file, indexed by building name.

        :param geometry: The contents of the `zone.shp` file indexed by building name.

        :return: Adjusted Daysim geometry data containing the following:

            - name: Name of building.
            - Aw: Area of windows for each building (using mean window to wall ratio for building, excluding voids) [m2]
            - Awall_ag: Opaque wall areas above ground (excluding voids, windows and roof) [m2]
            - Aop_bg: Opaque areas below ground (including ground floor, excluding voids and windows) [m2]
            - Aroof: Area of the roof (considered flat and equal to the building footprint) [m2]
            - GFA_m2: Gross floor area [m2]
            - floors: Sum of floors below ground (floors_bg) and floors above ground (floors_ag) [m2]
            - surface_volume: Surface to volume ratio [m^-1]

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

        df = envelope.merge(geometry, left_index=True, right_index=True)


        # adjust envelope areas with Void_deck
        df['Aop_bg'] = df['height_bg'] * df['perimeter'] + df['footprint']

        # get other quantities.
        df['floors'] = df['floors_bg'] + df['floors_ag'] - df["void_deck"]
        df['GFA_m2'] = df['footprint'] * df['floors']  # gross floor area
        df['GFA_ag_m2'] = df['footprint'] * (df['floors_ag'] - df["void_deck"])
        df['GFA_bg_m2'] = df['footprint'] * df['floors_bg']

        return df

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

    def __getitem__(self, building_name):
        """return a (read-only) BuildingPropertiesRow for the building"""
        return BuildingPropertiesRow(name=building_name,
                                     geometry=self.get_prop_geometry(building_name),
                                     envelope=self.get_prop_envelope(building_name),
                                     typology=self.get_prop_typology(building_name),
                                     hvac=self.get_prop_hvac(building_name),
                                     rc_model=self.get_prop_rc_model(building_name),
                                     comfort=self.get_prop_comfort(building_name),
                                     internal_loads=self.get_prop_internal_loads(building_name),
                                     age=self.get_prop_age(building_name),
                                     solar=self.get_solar(building_name),
                                     supply=self.get_prop_supply_systems(building_name))

    def get_overrides_columns(self):
        """Return the list of column names in the `overrides.csv` file or an empty list if no such file
        is present."""

        if hasattr(self, '_overrides'):
            return list(self._overrides.columns)
        return []


def split_above_and_below_ground_shares(Hs, Ns, occupied_bg, floors_ag, floors_bg):
    '''
    Split conditioned (Hs) and occupied (Ns) shares of ground floor area based on whether the basement
    conditioned/occupied or not.
    For simplicity, the same share is assumed for all conditioned/occupied floors (whether above or below ground)
    '''
    share_ag = floors_ag / (floors_ag + floors_bg * occupied_bg)
    share_bg = 1 - share_ag
    Hs_ag = Hs * share_ag
    Hs_bg = Hs * share_bg
    Ns_ag = Ns * share_ag
    Ns_bg = Ns * share_bg

    return Hs_ag, Hs_bg, Ns_ag, Ns_bg


def calc_useful_areas(df):
    # Calculate share of above- and below-ground GFA that is conditioned/occupied (assume same share on all floors)
    df['Hs_ag'], df['Hs_bg'], df['Ns_ag'], df['Ns_bg'] = split_above_and_below_ground_shares(
        df['Hs'], df['Ns'], df['occupied_bg'], df['floors_ag'] - df['void_deck'], df['floors_bg'])
    # occupied floor area: all occupied areas in the building
    df['Aocc'] = df['GFA_ag_m2'] * df['Ns_ag'] + df['GFA_bg_m2'] * df['Ns_bg']
    # conditioned area: areas that are heated/cooled
    df['Af'] = df['GFA_ag_m2'] * df['Hs_ag'] + df['GFA_bg_m2'] * df['Hs_bg']
    # electrified area: share of gross floor area that is also electrified
    df['Aef'] = df['GFA_m2'] * df['Es']
    # area of all surfaces facing the building zone
    df['Atot'] = df['Af'] * LAMBDA_AT

    return df


class BuildingPropertiesRow(object):
    """Encapsulate the data of a single row in the DataSets of BuildingProperties. This class meant to be
    read-only."""

    def __init__(self, name, geometry, envelope, typology, hvac,
                 rc_model, comfort, internal_loads, age, solar, supply):
        """Create a new instance of BuildingPropertiesRow - meant to be called by BuildingProperties[building_name].
        Each of the arguments is a pandas Series object representing a row in the corresponding DataFrame."""

        self.name = name
        self.geometry = geometry
        self.geometry['floor_height'] = self.geometry['height_ag'] / self.geometry['floors_ag']
        envelope['Hs_ag'], envelope['Hs_bg'], envelope['Ns_ag'], envelope['Ns_bg'] = \
            split_above_and_below_ground_shares(
                envelope['Hs'], envelope['Ns'], envelope['occupied_bg'], geometry['floors_ag'], geometry['floors_bg'])
        self.architecture = EnvelopeProperties(envelope)
        self.typology = typology  # FIXME: rename to uses!
        self.hvac = hvac
        self.rc_model = rc_model
        self.comfort = comfort
        self.internal_loads = internal_loads
        self.age = age
        self.solar = SolarProperties(solar)
        self.supply = supply
        self.building_systems = self._get_properties_building_systems()

    def _get_properties_building_systems(self):

        """
        Method for defining the building system properties, specifically the nominal supply and return temperatures,
        equivalent pipe lengths and transmittance losses. The systems considered include an ahu (air
        handling unit, rsu(air recirculation unit), and scu/shu (sensible cooling / sensible heating unit).
        Note: it is assumed that building with less than a floor and less than 2 floors underground do not require
        heating and cooling, and are not considered when calculating the building system properties.

        :return: building_systems dict containing the following information:

            Pipe Lengths:

                - Lcww_dis: length of hot water piping in the distribution circuit (????) [m]
                - Lsww_dis: length of hot water piping in the distribution circuit (????) [m]
                - Lvww_dis: length of hot water piping in the distribution circuit (?????) [m]
                - Lvww_c: length of piping in the heating system circulation circuit (ventilated/recirc?) [m]
                - Lv: length vertical lines [m]

            Heating Supply Temperatures:

                - Ths_sup_ahu_0: heating supply temperature for AHU (C)
                - Ths_sup_aru_0: heating supply temperature for ARU (C)
                - Ths_sup_shu_0: heating supply temperature for SHU (C)

            Heating Return Temperatures:

                - Ths_re_ahu_0: heating return temperature for AHU (C)
                - Ths_re_aru_0: heating return temperature for ARU (C)
                - Ths_re_shu_0: heating return temperature for SHU (C)

            Cooling Supply Temperatures:

                - Tcs_sup_ahu_0: cooling supply temperature for AHU (C)
                - Tcs_sup_aru_0: cooling supply temperature for ARU (C)
                - Tcs_sup_scu_0: cooling supply temperature for SCU (C)

            Cooling Return Temperatures:

                - Tcs_re_ahu_0: cooling return temperature for AHU (C)
                - Tcs_re_aru_0: cooling return temperature for ARU (C)
                - Tcs_re_scu_0: cooling return temperature for SCU (C)

            Water supply temperature??:

                - Tww_sup_0: ?????

            Thermal losses in pipes:

                - Y: Linear trasmissivity coefficients of piping depending on year of construction [W/m.K]

            Form Factor Adjustment:

                - fforma: form factor comparison between real surface and rectangular ???

        :rtype: dict


        """

        # Refactored from CalcThermalLoads

        # geometry properties.

        Ll = self.geometry['Blength']
        Lw = self.geometry['Bwidth']
        nf_ag = self.geometry['floors_ag']
        nf_bg = self.geometry['floors_bg']
        phi_pipes = self._calculate_pipe_transmittance_values()

        # nominal temperatures
        Ths_sup_ahu_0 = float(self.hvac['Tshs0_ahu_C'])
        Ths_re_ahu_0 = float(Ths_sup_ahu_0 - self.hvac['dThs0_ahu_C'])
        Ths_sup_aru_0 = float(self.hvac['Tshs0_aru_C'])
        Ths_re_aru_0 = float(Ths_sup_aru_0 - self.hvac['dThs0_aru_C'])
        Ths_sup_shu_0 = float(self.hvac['Tshs0_shu_C'])
        Ths_re_shu_0 = float(Ths_sup_shu_0 - self.hvac['dThs0_shu_C'])
        Tcs_sup_ahu_0 = self.hvac['Tscs0_ahu_C']
        Tcs_re_ahu_0 = Tcs_sup_ahu_0 + self.hvac['dTcs0_ahu_C']
        Tcs_sup_aru_0 = self.hvac['Tscs0_aru_C']
        Tcs_re_aru_0 = Tcs_sup_aru_0 + self.hvac['dTcs0_aru_C']
        Tcs_sup_scu_0 = self.hvac['Tscs0_scu_C']
        Tcs_re_scu_0 = Tcs_sup_scu_0 + self.hvac['dTcs0_scu_C']

        Tww_sup_0 = self.hvac['Tsww0_C']
        # Identification of equivalent lengths
        fforma = self._calc_form()  # factor form comparison real surface and rectangular
        Lv = (2 * Ll + 0.0325 * Ll * Lw + 6) * fforma  # length vertical lines
        if nf_ag < 2 and nf_bg < 2:  # it is assumed that building with less than a floor and less than 2 floors udnerground do not have
            Lcww_dis = 0
            Lvww_c = 0
        else:
            Lcww_dis = 2 * (Ll + 2.5 + nf_ag * self.geometry['floor_height']) * fforma  # length hot water piping circulation circuit
            Lvww_c = (2 * Ll + 0.0125 * Ll * Lw) * fforma  # length piping heating system circulation circuit

        Lsww_dis = 0.038 * Ll * Lw * nf_ag * self.geometry['floor_height'] * fforma  # length hot water piping distribution circuit
        Lvww_dis = (Ll + 0.0625 * Ll * Lw) * fforma  # length piping heating system distribution circuit

        building_systems = pd.Series({'Lcww_dis': Lcww_dis,
                                      'Lsww_dis': Lsww_dis,
                                      'Lv': Lv,
                                      'Lvww_c': Lvww_c,
                                      'Lvww_dis': Lvww_dis,
                                      'Ths_sup_ahu_0': Ths_sup_ahu_0,
                                      'Ths_re_ahu_0': Ths_re_ahu_0,
                                      'Ths_sup_aru_0': Ths_sup_aru_0,
                                      'Ths_re_aru_0': Ths_re_aru_0,
                                      'Ths_sup_shu_0': Ths_sup_shu_0,
                                      'Ths_re_shu_0': Ths_re_shu_0,
                                      'Tcs_sup_ahu_0': Tcs_sup_ahu_0,
                                      'Tcs_re_ahu_0': Tcs_re_ahu_0,
                                      'Tcs_sup_aru_0': Tcs_sup_aru_0,
                                      'Tcs_re_aru_0': Tcs_re_aru_0,
                                      'Tcs_sup_scu_0': Tcs_sup_scu_0,
                                      'Tcs_re_scu_0': Tcs_re_scu_0,
                                      'Tww_sup_0': Tww_sup_0,
                                      'Y': phi_pipes,
                                      'fforma': fforma})
        return building_systems

    def _calculate_pipe_transmittance_values(self):
        """linear trasmissivity coefficients of piping W/(m.K)"""
        if self.age['year'] >= 1995:
            phi_pipes = [0.2, 0.3, 0.3]
        # elif 1985 <= self.age['built'] < 1995 and self.age['HVAC'] == 0:
        elif 1985 <= self.age['year'] < 1995:
            phi_pipes = [0.3, 0.4, 0.4]
        else:
            phi_pipes = [0.4, 0.4, 0.4]
        return phi_pipes

    def _calc_form(self):
        factor = self.geometry['footprint'] / (self.geometry['Bwidth'] * self.geometry['Blength'])
        return factor


def weird_division(n, d):
    return n / d if d else 0.0


class EnvelopeProperties(object):
    """Encapsulate a single row of the architecture input file for a building"""

    def __init__(self, envelope):
        self.A_op = envelope['Awin_ag'] + envelope['Awall_ag']
        self.a_roof = envelope['a_roof']
        self.n50 = envelope['n50']
        self.win_wall = weird_division(envelope['Awin_ag'], self.A_op)
        self.a_wall = envelope['a_wall']
        self.rf_sh = envelope['rf_sh']
        self.e_wall = envelope['e_wall']
        self.e_roof = envelope['e_roof']
        self.e_underside = 0.0 # dummy values for emissivity of underside (bottom surface) as 0.
        self.G_win = envelope['G_win']
        self.e_win = envelope['e_win']
        self.U_roof = envelope['U_roof']
        self.Hs_ag = envelope['Hs_ag']
        self.Hs_bg = envelope['Hs_bg']
        self.Ns_ag = envelope['Ns_ag']
        self.Ns_bg = envelope['Ns_bg']
        self.Es = envelope['Es']
        self.occupied_bg = envelope['occupied_bg']
        self.Cm_Af = envelope['Cm_Af']
        self.U_wall = envelope['U_wall']
        self.U_base = envelope['U_base']
        self.U_win = envelope['U_win']
        self.void_deck = envelope['void_deck']


class SolarProperties(object):
    """Encapsulates the solar properties of a building"""

    __slots__ = ['I_sol']

    def __init__(self, solar):
        self.I_sol = solar['I_sol']


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


def get_properties_technical_systems(locator, prop_hvac):
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

    prop_emission_heating = pd.read_csv(locator.get_database_assemblies_hvac_heating())
    prop_emission_cooling = pd.read_csv(locator.get_database_assemblies_hvac_cooling())
    prop_emission_dhw = pd.read_csv(locator.get_database_assemblies_hvac_hot_water())
    prop_emission_control_heating_and_cooling = pd.read_csv(locator.get_database_assemblies_hvac_controller())
    prop_ventilation_system_and_control = pd.read_csv(locator.get_database_assemblies_hvac_ventilation())
    df_emission_heating = prop_hvac.merge(prop_emission_heating, left_on='hvac_type_hs', right_on='code')
    df_emission_cooling = prop_hvac.merge(prop_emission_cooling, left_on='hvac_type_cs', right_on='code')
    df_emission_control_heating_and_cooling = prop_hvac.merge(prop_emission_control_heating_and_cooling,
                                                              left_on='hvac_type_ctrl', right_on='code')
    df_emission_dhw = prop_hvac.merge(prop_emission_dhw, left_on='hvac_type_dhw', right_on='code')
    df_ventilation_system_and_control = prop_hvac.merge(prop_ventilation_system_and_control, left_on='hvac_type_vent',
                                                        right_on='code')
    fields_emission_heating = ['name', 'hvac_type_hs', 'hvac_type_cs', 'hvac_type_dhw', 'hvac_type_ctrl', 'hvac_type_vent', 'hvac_heat_starts',
                               'hvac_heat_ends', 'hvac_cool_starts', 'hvac_cool_ends', 'class_hs', 'convection_hs',
                               'Qhsmax_Wm2', 'dThs_C', 'Tshs0_ahu_C', 'dThs0_ahu_C', 'Th_sup_air_ahu_C', 'Tshs0_aru_C',
                               'dThs0_aru_C', 'Th_sup_air_aru_C', 'Tshs0_shu_C', 'dThs0_shu_C']
    fields_emission_cooling = ['name', 'Qcsmax_Wm2', 'dTcs_C', 'Tscs0_ahu_C', 'dTcs0_ahu_C', 'Tc_sup_air_ahu_C',
                               'Tscs0_aru_C', 'dTcs0_aru_C', 'Tc_sup_air_aru_C', 'Tscs0_scu_C', 'dTcs0_scu_C',
                               'class_cs', 'convection_cs']
    fields_emission_control_heating_and_cooling = ['name', 'dT_Qhs', 'dT_Qcs']
    fields_emission_dhw = ['name', 'class_dhw', 'Tsww0_C', 'Qwwmax_Wm2']
    fields_system_ctrl_vent = ['name', 'MECH_VENT', 'WIN_VENT', 'HEAT_REC', 'NIGHT_FLSH', 'ECONOMIZER']

    result = df_emission_heating[fields_emission_heating].merge(df_emission_cooling[fields_emission_cooling],
                                                                on='name').merge(
        df_emission_control_heating_and_cooling[fields_emission_control_heating_and_cooling],
        on='name').merge(df_emission_dhw[fields_emission_dhw],
                         on='name').merge(df_ventilation_system_and_control[fields_system_ctrl_vent], on='name')
    # verify hvac and ventilation combination
    verify_hvac_system_combination(result, locator)
    # read region-specific control parameters (identical for all buildings), i.e. heating and cooling season
    result['has-heating-season'] = result.apply(lambda x: verify_has_season(x['name'],
                                                                            x['hvac_heat_starts'],
                                                                            x['hvac_heat_ends']), axis=1)
    result['has-cooling-season'] = result.apply(lambda x: verify_has_season(x['name'],
                                                                            x['hvac_cool_starts'],
                                                                            x['hvac_cool_ends']), axis=1)

    # verify seasons do not overlap
    result['overlap-season'] = result.apply(lambda x: verify_overlap_season(x['name'],
                                                                            x['has-heating-season'],
                                                                            x['has-cooling-season'],
                                                                            x['hvac_heat_starts'],
                                                                            x['hvac_heat_ends'],
                                                                            x['hvac_cool_starts'],
                                                                            x['hvac_cool_ends']), axis=1)
    return result


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


def get_prop_solar(locator, building_names, prop_rc_model, prop_envelope, weather_data):
    """
    Gets the sensible solar gains from calc_Isol_daysim and stores in a dataframe containing building 'name' and
    I_sol (incident solar gains).

    :param locator: an InputLocator for locating the input files
    :param building_names: List of buildings
    :param prop_rc_model: RC model properties of a building by name.
    :param prop_envelope: dataframe containing the building envelope properties.
    :return: dataframe containing the sensible solar gains for each building by name called result.
    :rtype: Dataframe
    """

    # create result data frame
    list_Isol = []

    # for every building
    for building_name in building_names:
        thermal_resistance_surface = dict(zip(['RSE_wall', 'RSE_roof', 'RSE_win', 'RSE_underside'],
                                              get_thermal_resistance_surface(prop_envelope.loc[building_name],
                                                                             weather_data)))
        I_sol = calc_Isol_daysim(building_name, locator, prop_envelope, prop_rc_model, thermal_resistance_surface)
        list_Isol.append(I_sol)

    result = pd.DataFrame({'name': list(building_names), 'I_sol': list_Isol})

    return result


def calc_Isol_daysim(building_name, locator: InputLocator, prop_envelope, prop_rc_model, thermal_resistance_surface):
    """
    Reads Daysim geometry and radiation results and calculates the sensible solar heat loads based on the surface area
    and building envelope properties.

    :param building_name: Name of the building (e.g. B154862)
    :param locator: an InputLocator for locating the input files
    :param prop_envelope: contains the building envelope properties.
    :param prop_rc_model: RC model properties of a building by name.
    :param thermal_resistance_surface: Thermal resistance of building element.

    :return: I_sol: numpy array containing the sensible solar heat loads for roof, walls and windows.
    :rtype: np.array

    """

    # read daysim radiation
    radiation_data = pd.read_csv(locator.get_radiation_building(building_name))

    # sum wall
    # solar incident on all walls [W]
    I_sol_wall = (radiation_data['walls_east_kW'] +
                  radiation_data['walls_west_kW'] +
                  radiation_data['walls_north_kW'] +
                  radiation_data['walls_south_kW']).values * 1000  # in W

    # sensible gain on all walls [W]
    I_sol_wall = I_sol_wall * \
                 prop_envelope.loc[building_name, 'a_wall'] * \
                 thermal_resistance_surface['RSE_wall'] * \
                 prop_rc_model.loc[building_name, 'U_wall']

    # sum roof
    # solar incident on all roofs [W]
    I_sol_roof = radiation_data['roofs_top_kW'].values * 1000  # in W

    # sensible gain on all roofs [W]
    I_sol_roof = I_sol_roof * \
                 prop_envelope.loc[building_name, 'a_roof'] * \
                 thermal_resistance_surface['RSE_roof'] * \
                 prop_rc_model.loc[building_name, 'U_roof']

    # sum window, considering shading
    I_sol_win = (radiation_data['windows_east_kW'] +
                 radiation_data['windows_west_kW'] +
                 radiation_data['windows_north_kW'] +
                 radiation_data['windows_south_kW']).values * 1000  # in W

    Fsh_win = np.vectorize(blinds.calc_blinds_activation)(I_sol_win,
                                                          prop_envelope.loc[building_name, 'G_win'],
                                                          prop_envelope.loc[building_name, 'rf_sh'])

    I_sol_win = I_sol_win * \
                Fsh_win * \
                (1 - prop_envelope.loc[building_name, 'F_F'])
    
    #dummy values for base because there's no radiation calculated for bottom-oriented surfaces yet.
    I_sol_underside = np.zeros_like(I_sol_win) * thermal_resistance_surface['RSE_underside'] 

    # sum
    I_sol = I_sol_wall + I_sol_roof + I_sol_win + I_sol_underside

    return I_sol


def get_thermal_resistance_surface(prop_envelope, weather_data):
    '''
    This function defines the surface resistance of external surfaces RSE according to ISO 6946 Eq. (A.1).
    '''

    # define surface thermal resistances according to ISO 6946
    h_c = np.vectorize(calc_hc)(weather_data['windspd_ms'].values)
    # generate an array of 0.5 * (sky_temp(t) + air_temp(t-1))
    theta_ss = 0.5 * (
            weather_data['skytemp_C'].values +
            np.array([weather_data['drybulb_C'].values[0]] +
                     list(weather_data['drybulb_C'].values[0:HOURS_IN_YEAR - 1])))
    thermal_resistance_surface_wall = (h_c + calc_hr(prop_envelope.e_wall, theta_ss)) ** -1
    thermal_resistance_surface_win = (h_c + calc_hr(prop_envelope.e_win, theta_ss)) ** -1
    thermal_resistance_surface_roof = (h_c + calc_hr(prop_envelope.e_roof, theta_ss)) ** -1
    thermal_resistance_surface_underside = np.zeros_like(h_c)

    return thermal_resistance_surface_wall, thermal_resistance_surface_roof, thermal_resistance_surface_win, thermal_resistance_surface_underside


def verify_hvac_system_combination(result, locator):
    '''
    This function verifies whether an infeasible combination of cooling and ventilation systems has been selected.
    If an infeasible combination is selected, a warning is printed and the simulation is stopped.
    '''

    needs_mech_vent = result.apply(lambda row: row.class_cs in ['CENTRAL_AC', 'HYBRID_AC'], axis=1)
    list_exceptions = []
    for idx in result.loc[needs_mech_vent & (~ result.MECH_VENT)].index:
        building_name = result.loc[idx, 'name']
        class_cs = result.loc[idx, 'class_cs']
        type_vent = result.loc[idx,'type_vent']
        hvac_database = pd.read_csv(locator.get_database_assemblies_hvac_ventilation())
        mechanical_ventilation_systems = list(hvac_database.loc[hvac_database['MECH_VENT'], 'code'])
        list_exceptions.append(Exception(
            f'\nBuilding {building_name} has a cooling system as {class_cs} with a ventilation system {type_vent}.'
            f'\nPlease re-assign a ventilation system from the technology database that includes mechanical ventilation: {mechanical_ventilation_systems}'))
    if len(list_exceptions) > 0:
        raise_multiple(list_exceptions)
    return

def raise_multiple(exceptions):
    '''
    This function raises multiple exceptions recursively. Exceptions in a list are raised one by one until the list
    is empty.
    '''

    if not exceptions:
        # if list of exceptions is empty, recursion ends
        return
    try:
        # raise one exception, then remove it from list
        raise exceptions.pop()
    finally:
        # repeat the process until list is empty
        raise_multiple(exceptions)

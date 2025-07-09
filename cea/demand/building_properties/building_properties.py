"""
Classes of building properties
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from geopandas import GeoDataFrame as Gdf

from typing import TYPE_CHECKING

from cea.demand.building_properties.building_comfort import BuildingComfort
from cea.demand.building_properties.building_internal_loads import BuildingInternalLoads
from cea.demand.building_properties.building_properties_row import BuildingPropertiesRow
from cea.demand.building_properties.building_supply_systems import BuildingSupplySystems
from cea.demand.building_properties.building_rc_model import BuildingRCModel
from cea.demand.building_properties.building_geometry import BuildingGeometry
from cea.demand.building_properties.building_envelope import BuildingEnvelope
from cea.demand.building_properties.building_hvac import BuildingHVAC
from cea.demand.building_properties.building_typology import BuildingTypology
from cea.demand.building_properties.building_solar import BuildingSolar
from cea.demand.constants import LAMBDA_AT

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



class BuildingProperties:
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
        
        self.geometry = BuildingGeometry(locator, building_names)
        prop_geometry = self.geometry._prop_geometry

        self.envelope = BuildingEnvelope(locator, building_names)
        prop_envelope = self.envelope._prop_envelope

        self.hvac = BuildingHVAC(locator, building_names)
        prop_hvac = self.hvac._prop_hvac

        self.typology = BuildingTypology(locator, building_names)
        prop_typology = self.typology._prop_typology

        self.comfort = BuildingComfort(locator, building_names)
        prop_comfort = self.comfort._prop_comfort

        self.internal_loads = BuildingInternalLoads(locator, building_names)
        prop_internal_loads = self.internal_loads._prop_internal_loads

        self.supply_systems = BuildingSupplySystems(locator, building_names)
        prop_supply_systems = self.supply_systems._prop_supply_systems

        self.rc_model = BuildingRCModel(locator, building_names, prop_typology, prop_envelope, prop_geometry, prop_hvac)
        prop_rc_model = self.rc_model._prop_rc_model

        self.solar = BuildingSolar(locator, building_names, prop_rc_model, prop_envelope, weather_data)
        prop_solar = self.solar._prop_solar

        # df_windows = geometry_reader.create_windows(surface_properties, prop_envelope)
        # TODO: to check if the Win_op and height of window is necessary.
        # TODO: maybe mergin branch i9 with CItyGML could help with this
        print("done")

        # save resulting data
        self._prop_supply_systems = prop_supply_systems
        self._prop_geometry = prop_geometry
        self._prop_envelope = prop_envelope
        self._prop_typology = prop_typology
        self._prop_HVAC_result = prop_hvac
        self._prop_comfort = prop_comfort
        self._prop_internal_loads = prop_internal_loads
        self._prop_age = prop_typology[['year']]
        self._solar = prop_solar
        self._prop_RC_model = prop_rc_model


    def __len__(self):
        """return length of list_building_names"""
        return len(self.building_names)

    def list_building_names(self):
        """get list of all building names"""
        return self.building_names

    def list_uses(self):
        """get list of all uses (typology types)"""
        return list(set(self._prop_typology['USE'].values))

    def get_prop_age(self, name_building):
        """get age properties of a building by name"""
        return self._prop_age.loc[name_building].to_dict()

    def get_solar(self, name_building):
        """get solar properties of a building by name"""
        return self._solar.loc[name_building]

    def __getitem__(self, building_name):
        """return a (read-only) BuildingPropertiesRow for the building"""
        return BuildingPropertiesRow(name=building_name,
                                     geometry=self.geometry[building_name],
                                     envelope=self.envelope[building_name],
                                     typology=self.typology[building_name],
                                     hvac=self.hvac[building_name],
                                     rc_model=self.rc_model[building_name],
                                     comfort=self.comfort[building_name],
                                     internal_loads=self.internal_loads[building_name],
                                     age=self.get_prop_age(building_name),
                                     solar=self.get_solar(building_name),
                                     supply=self.supply_systems[building_name])

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

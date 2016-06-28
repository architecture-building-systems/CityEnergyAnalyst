"""
===========================
Analytical energy demand model algorithm
===========================
File history and credits:
J. Fonseca  script development          24.08.15
D. Thomas   formatting, refactoring, debugging and cleaning
D. Thomas   integration in toolbox
J. Fonseca  refactoring to new properties file   22.03.16
G. Happle   BuildingPropsThermalLoads   27.05.2016
"""
from __future__ import division

import pandas as pd
import contributions.thermal_loads_new_ventilation.simple_window_generator as simple_window_generator
from geopandas import GeoDataFrame
import epwreader
import functions as f
import globalvar
import inputlocator
import maker as m

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas", "Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


reload(f)
reload(globalvar)


def demand_calculation(locator, weather_path, gv):
    """
    Algorithm to calculate the hourly demand of energy services in buildings
    using the integrated model of Fonseca et al. 2015. Applied energy.
    (http://dx.doi.org/10.1016/j.apenergy.2014.12.068)

    PARAMETERS
    ----------
    :param locator: An InputLocator to locate input files
    :type locator: inputlocator.InputLocator

    :param weather_path: A path to the EnergyPlus weather data file (.epw)
    :type weather_path: str

    :param gv: A GlobalVariable (context) instance
    :type gv: globalvar.GlobalVariable


    RETURNS
    -------

    :returns: None
    :rtype: NoneType


    INPUT / OUTPUT FILES
    --------------------

    - get_demand_results_folder: C:\reference-case\baseline\outputs\data\demand
    - get_temporary_folder: c:\users\darthoma\appdata\local\temp
    - get_temporary_file: c:\users\darthoma\appdata\local\temp\B153767T.csv (* for each building)
    - get_total_demand: C:\reference-case\baseline\outputs\data\demand\Total_demand.csv


    SIDE EFFECTS
    ------------

    Produces a demand file per building and a total demand file for the whole zone of interest.

    B153767T.csv: csv file for every building with hourly demand data
    Total_demand.csv: csv file of yearly demand data per buidling.
    """
    # local variables


    # initialize function inputs
    weather_data = epwreader.epw_reader(weather_path)[['drybulb_C', 'relhum_percent', 'windspd_ms']]
    building_properties = read_building_properties(locator, gv)
    # get list of uses
    list_uses = list(building_properties._prop_occupancy.drop('PFloor', axis=1).columns)
    # get date
    date = pd.date_range(gv.date_start, periods=8760, freq='H')

    gv.log("reading occupancy schedules")
    # get schedules
    schedules = m.schedule_maker(date, locator, list_uses)
    gv.log("done")

    # construct schedules dict for input to function
    usage_schedules = {'list_uses': list_uses,
                       'schedules': schedules}



    # get timeseries of demand
    num_buildings = len(building_properties.get_list_building_name())
    counter = 0

    for building in building_properties.get_list_building_name():
        gv.models['calc-thermal-loads'](building, building_properties, weather_data, usage_schedules, date, gv,
                                        locator.get_demand_results_folder(), locator.get_temporary_folder())

        gv.log('Building No. %(bno)i completed out of %(btot)i', bno=counter + 1, btot=num_buildings)
        counter += 1

    # get total file

    counter = 0
    for name in building_properties.get_list_building_name():
        temporary_file = locator.get_temporary_file('%(name)sT.csv' % locals())
        # TODO: check this logic
        if counter == 0:
            df = pd.read_csv(temporary_file)
            counter += 1
        else:
            df2 = pd.read_csv(temporary_file)
            df = df.append(df2, ignore_index=True)
    df.to_csv(locator.get_total_demand(), index=False, float_format='%.2f')

    gv.log('finished')


def get_temperatures(locator, prop_HVAC):
    """
    Return temperature data per building based on the HVAC systems of the building. Uses the `emission_systems.xls`
    file to look up the temperatures.

    PARAMETERS
    ----------

    :param locator:
    :type locator: LocatorDecorator

    :param prop_HVAC: HVAC properties for each building (type of cooling system, control system, domestic hot water
                      system and heating system.
                      The values can be looked up in the contributors manual:
                      https://architecture-building-systems.gitbooks.io/cea-toolbox-for-arcgis-manual/content/building_properties.html#mechanical-systems
    :type prop_HVAC: GeoDataFrame

    Sample data (first 5 rows):
                 Name type_cs type_ctrl type_dhw type_hs
    0     B154862      T0        T1       T1      T1
    1     B153604      T0        T1       T1      T1
    2     B153831      T0        T1       T1      T1
    3  B302022960      T0        T0       T0      T0
    4  B302034063      T0        T0       T0      T0


    RETURNS
    -------

    :returns: A DataFrame containing temperature data for each building in the scenario. More information can be
              found in the contributors manual:
              https://architecture-building-systems.gitbooks.io/cea-toolbox-for-arcgis-manual/content/delivery_technologies.html
    :rtype: DataFrame

    Each row contains the following fields:
    Name          B154862   (building name)
    type_hs            T1   (copied from input)
    type_cs            T0   (copied from input)
    type_dhw           T1   (copied from input)
    type_ctrl          T1   (copied from input)
    Tshs0_C            90   (heating system supply temperature at nominal conditions [C])
    dThs0_C            20   (delta of heating system temperature at nominal conditions [C])
    Qhsmax_Wm2        500   (maximum heating system power capacity per unit of gross built area [W/m2])
    Tscs0_C             0   (cooling system supply temperature at nominal conditions [C])
    dTcs0_C             0   (delta of cooling system temperature at nominal conditions [C])
    Qcsmax_Wm2          0   (maximum cooling system power capacity per unit of gross built area [W/m2])
    Tsww0_C            60   (dhw system supply temperature at nominal conditions [C])
    dTww0_C            50   (delta of dwh system temperature at nominal conditions [C])
    Qwwmax_Wm2        500   (maximum dwh system power capacity per unit of gross built area [W/m2])
    Name: 0, dtype: object

    INPUT / OUTPUT FILES
    --------------------

    - get_technical_emission_systems: cea\db\CH\Systems\emission_systems.xls
    """
    prop_emission_heating = pd.read_excel(locator.get_technical_emission_systems(), 'heating')
    prop_emission_cooling = pd.read_excel(locator.get_technical_emission_systems(), 'cooling')
    prop_emission_dhw = pd.read_excel(locator.get_technical_emission_systems(), 'dhw')

    df = prop_HVAC.merge(prop_emission_heating, left_on='type_hs', right_on='code')
    df2 = prop_HVAC.merge(prop_emission_cooling, left_on='type_cs', right_on='code')
    df3 = prop_HVAC.merge(prop_emission_dhw, left_on='type_dhw', right_on='code')

    fields = ['Name', 'type_hs', 'type_cs', 'type_dhw', 'type_ctrl', 'Tshs0_C', 'dThs0_C', 'Qhsmax_Wm2']
    fields2 = ['Name', 'Tscs0_C', 'dTcs0_C', 'Qcsmax_Wm2']
    fields3 = ['Name', 'Tsww0_C', 'dTww0_C', 'Qwwmax_Wm2']

    result = df[fields].merge(df2[fields2], on='Name').merge(df3[fields3], on='Name')
    return result


class BuildingProperties(object):
    """
    Groups building properties used for the calc-thermal-loads functions. Stores the full DataFrame for each of the
    building properties and provides methods for indexing them by name.

    G. Happle   BuildingPropsThermalLoads   27.05.2016
    """
    def __init__(self, prop_geometry=None, prop_architecture=None, prop_occupancy=None, prop_HVAC_result=None,
                 prop_RC_model=None, prop_comfort=None, prop_internal_loads=None, prop_age=None, solar=None,
                 prop_windows=None):
        self._prop_geometry = prop_geometry
        self._prop_architecture = prop_architecture
        self._prop_occupancy = prop_occupancy
        self._prop_HVAC_result = prop_HVAC_result
        self._prop_RC_model = prop_RC_model
        self._prop_comfort = prop_comfort
        self._prop_internal_loads = prop_internal_loads
        self._prop_age = prop_age
        self._solar = solar
        self._prop_windows = prop_windows

    def get_list_building_name(self):
        """get list of all building names"""
        return self._prop_RC_model.index

    def get_prop_geometry(self, name_building):
        """get geometry of a building by name"""
        return self._prop_geometry.ix[name_building]

    def get_prop_architecture(self, name_building):
        """get the architecture properties of a building by name"""
        return self._prop_architecture.ix[name_building]

    def get_prop_occupancy(self, name_building):
        """get the occupancy properties of a building by name"""
        return self._prop_occupancy.ix[name_building]

    def get_prop_hvac(self, name_building):
        """get HVAC properties of a building by name"""
        return self._prop_HVAC_result.ix[name_building]

    def get_prop_rc_model(self, name_building):
        """get RC-model properties of a building by name"""
        return self._prop_RC_model.ix[name_building]

    def get_prop_comfort(self, name_building):
        """get comfort properties of a building by name"""
        return self._prop_comfort.ix[name_building]

    def get_prop_internal_loads(self, name_building):
        """get internal loads properties of a building by name"""
        return self._prop_internal_loads.ix[name_building]

    def get_prop_age(self, name_building):
        """get age properties of a building by name"""
        return self._prop_age.ix[name_building]

    def get_solar(self, name_building):
        """get solar properties of a building by name"""
        return self._solar.ix[name_building]

    def get_prop_windows(self, name_building):
        """get windows and their properties of a building by name"""
        return self._prop_windows.loc[self._prop_windows['name_building'] == name_building].to_dict('list')


def read_building_properties(locator, gv):
    """
    Read building properties from input shape files.

    PARAMETERS
    ----------

    :param locator: an InputLocator for locating the input files
    :type locator: cea.inputlocator.InputLocator

    :param gv: contains the context (constants and models) for the calculation
    :type gv: cea.globalvar.GlobalVariables

    RETURNS
    -------

    :returns: object of type BuildingProperties
    :rtype: BuildingProperties

    INPUT / OUTPUT FILES
    --------------------

    - get_radiation: C:\reference-case\baseline\outputs\data\solar-radiation\radiation.csv
    - get_surface_properties: C:\reference-case\baseline\outputs\data\solar-radiation\properties_surfaces.csv
    - get_building_geometry: C:\reference-case\baseline\inputs\building-geometry\zone.shp
    - get_building_hvac: C:\reference-case\baseline\inputs\building-properties\technical_systems.shp
    - get_building_thermal: C:\reference-case\baseline\inputs\building-properties\thermal_properties.shp
    - get_building_occupancy: C:\reference-case\baseline\inputs\building-properties\occupancy.shp
    - get_building_architecture: C:\reference-case\baseline\inputs\building-properties\architecture.shp
    - get_building_age: C:\reference-case\baseline\inputs\building-properties\age.shp
    - get_building_comfort: C:\reference-case\baseline\inputs\building-properties\indoor_comfort.shp
    - get_building_internal: C:\reference-case\baseline\inputs\building-properties\internal_loads.shp
    """

    gv.log("reading input files")
    solar = pd.read_csv(locator.get_radiation()).set_index('Name')
    surface_properties = pd.read_csv(locator.get_surface_properties())
    prop_geometry = GeoDataFrame.from_file(locator.get_building_geometry())
    prop_geometry['footprint'] = prop_geometry.area
    prop_geometry['perimeter'] = prop_geometry.length
    prop_geometry = prop_geometry.drop('geometry', axis=1).set_index('Name')
    prop_HVAC = GeoDataFrame.from_file(locator.get_building_hvac()).drop('geometry', axis=1)
    prop_thermal = GeoDataFrame.from_file(locator.get_building_thermal()).drop('geometry', axis=1).set_index('Name')
    prop_occupancy_df = GeoDataFrame.from_file(locator.get_building_occupancy()).drop('geometry', axis=1).set_index('Name')
    prop_occupancy = prop_occupancy_df.loc[:, (prop_occupancy_df != 0).any(
        axis=0)]  # trick to erase occupancies that are not being used (it speeds up the code)
    prop_architecture = GeoDataFrame.from_file(locator.get_building_architecture()).drop('geometry', axis=1).set_index('Name')
    prop_age = GeoDataFrame.from_file(locator.get_building_age()).drop('geometry', axis=1).set_index('Name')
    prop_comfort = GeoDataFrame.from_file(locator.get_building_comfort()).drop('geometry', axis=1).set_index('Name')
    prop_internal_loads = GeoDataFrame.from_file(locator.get_building_internal()).drop('geometry', axis=1).set_index('Name')
    # get temperatures of operation
    prop_HVAC_result = get_temperatures(locator, prop_HVAC).set_index('Name')
    gv.log('done')

    gv.log("calculating thermal properties")
    prop_RC_model = get_prop_RC_model(prop_occupancy, prop_architecture, prop_thermal, prop_geometry,
                                      prop_HVAC_result, surface_properties, gv)
    gv.log("done")

    gv.log("creating windows")
    df_windows = simple_window_generator.create_windows(surface_properties, prop_architecture)
    gv.log("done")

    # construct function input object
    return BuildingProperties(prop_geometry=prop_geometry, prop_occupancy=prop_occupancy,
                              prop_architecture=prop_architecture, prop_age=prop_age,
                              prop_comfort=prop_comfort, prop_internal_loads=prop_internal_loads,
                              prop_HVAC_result=prop_HVAC_result, prop_RC_model=prop_RC_model,
                              solar=solar, prop_windows=df_windows)


def get_prop_RC_model(occupancy, architecture, thermal_properties, geometry, hvac_temperatures, surface_properties, gv):
    """
    Return the RC model properties for all buildings.


    PARAMETERS
    ----------

    :param occupancy: The contents of the `occupancy.shp` file, indexed by building name. Each column is the name of an
        occupancy type (GYM, HOSPITAL, HOTEL, INDUSTRIAL, MULTI_RES, OFFICE, PARKING, etc.) except for the
        "PFloor" column which is a fraction of heated floor area.
        The occupancy types must add up to 1.0.
    :type occupancy: GeoDataFrame

    :param architecture: The contents of the `architecture.shp` file, indexed by building name. It contains the
        following fields: Occ_m2p, f_cros, n50, type_shade, win_op, win_wall. Only `win_wall` (window to wall ratio) is
        used.
    :type architecture: GeoDataFrame

    :param thermal_properties: The contents of the `thermal_properties.shp` file, indexed by building name. It
        contains the following fields: Es, Hs, U_base, U_roof, U_wall, U_win, th_mass.
        - Es: fraction of gross floor area that has electricity {0 <= Es <= 1}
        - Hs: fraction of gross floor area that is heated/cooled {0 <= Hs <= 1}
        - th_mass: type of building construction {T1: light, T2: medium, T3: heavy}
    :type thermal_properties: GeoDataFrame

    :param geometry: The contents of the `zone.shp` file indexed by building name - the list of buildings, their floor
        counts, heights etc.
        Includes additional fields "footprint" and "perimeter" as calculated in `read_building_properties`.
    :type geometry: GeoDataFrame

    :param hvac_temperatures: The return value of `get_temperatures`.
    :type hvac_temperatures: DataFrame

    :param surface_properties: The contents of the `properties_surfaces.csv` file generated by the radiation script.
        It contains the fields Name, Freeheight, FactorShade, height_ag and Shape_Leng.
        This data is used to calculate the wall and window areas
    :type surface_properties: DataFrame

    :param gv: An instance of the GlobalVariables context.
    :type gv: GlobalVariables


    RETURNS
    -------

    :returns: RC model properties per building
    :rtype: DataFrame

    Sample result data:
    Awall_all    1.131753e+03   (total wall surface exposed to outside conditions in [m2])
    Atot         4.564827e+03   (total area of the building envelope in [m2], the roof is considered to be flat)
    Aw           4.527014e+02   (area of windows in [m2])
    Am           6.947967e+03   (effective mass area in [m2])
    Aef          2.171240e+03   (floor area with electricity in [m2])
    Af           2.171240e+03   (conditioned floor area (heated/cooled) in [m2])
    Cm           6.513719e+08   (internal heat capacity in [J/K])
    Htr_is       1.574865e+04   FIXME: some heat transfer coefficient
    Htr_em       5.829963e+02   FIXME: some heat transfer coefficient
    Htr_ms       6.322650e+04   FIXME: some heat transfer coefficient
    Htr_op       5.776698e+02   FIXME: some heat transfer coefficient
    Hg           2.857637e+02   (steady-state Thermal transmission coefficient to the ground in [W/K])
    HD           2.919060e+02   (direct thermal transmission coefficient to the external environment in [W/K])
    Htr_w        1.403374e+03   (thermal transmission coefficient for windows and glazing in [W/K])
    GFA_m2       2.412489e+03   (gross floor area [m2])
    Name: B153767, dtype: float64

    FIXME: finish documenting the result data...
    FIXME: rename Awall_all to something more sane...
    """

    # Areas above ground
    # get the area of each wall in the buildings
    surface_properties['Awall'] = (surface_properties['Shape_Leng'] * surface_properties['Freeheight'] *
                                   surface_properties['FactorShade'])
    df = pd.DataFrame({'Name': surface_properties['Name'],
                             'Awall_all': surface_properties['Awall']}).groupby(by='Name').sum()

    df = df.merge(architecture, left_index=True, right_index=True)
    df = df.merge(occupancy, left_index=True, right_index=True)

    # area of windows
    df['Aw'] = df['Awall_all'] * df['win_wall'] * df['PFloor']

    # opaque areas (PFloor represents a factor according to the amount of floors heated)
    df['Aop_sup'] = df['Awall_all']*df['PFloor']-df['Aw']

    # Areas below ground
    df = df.merge(thermal_properties, left_index=True, right_index=True)
    df = df.merge(geometry, left_index=True, right_index=True)
    df = df.merge(hvac_temperatures, left_index=True, right_index=True)
    df['floors'] = df['floors_bg'] + df['floors_ag']

    # opague areas in [m2] below ground including floor
    df['Aop_bel'] = df['height_bg'] * df['perimeter'] + df['footprint']

    # total area of the building envelope in [m2], the roof is considered to be flat
    df['Atot'] = df[['Aw', 'Aop_sup', 'footprint', 'Aop_bel']].sum(axis=1) + (df['footprint'] * (df['floors'] - 1))

    df['GFA_m2'] = df['footprint'] * df['floors']  # gross floor area
    df['Af'] = df['GFA_m2'] * df['Hs']  # conditioned area - areas not heated
    df['Aef'] = df['GFA_m2'] * df['Es']  # conditioned area only those for electricity
    df['Am'] = df['th_mass'].apply(lookup_effective_mass_area_factor) * df['Af']  # Effective mass area in [m2]

    # Steady-state Thermal transmittance coefficients and Internal heat Capacity
    df['Htr_w'] = df['Aw']*df['U_win']  # Thermal transmission coefficient for windows and glazing in [W/K]

    # direct thermal transmission coefficient to the external environment in [W/K]
    df['HD'] = df['Aop_sup'] * df['U_wall'] + df['footprint'] * df['U_roof']

    df['Hg'] = gv.Bf * df['Aop_bel'] * df['U_base']  # steady-state Thermal transmission coefficient to the ground. in W/K
    df['Htr_op'] = df ['Hg']+ df ['HD']
    df['Htr_ms'] = gv.hms*df ['Am']  # Coupling conductance 1 in W/K
    df['Htr_em'] = 1/(1/df['Htr_op']-1/df['Htr_ms'])  # Coupling conductance 2 in W/K
    df['Htr_is'] = gv.his*df ['Atot']
    df['Cm'] = df['th_mass'].apply(lookup_specific_heat_capacity) * df['Af']  # Internal heat capacity in J/K

    fields = ['Awall_all', 'Atot', 'Aw', 'Am', 'Aef', 'Af', 'Cm', 'Htr_is', 'Htr_em', 'Htr_ms', 'Htr_op', 'Hg', 'HD',
              'Htr_w', 'GFA_m2']
    result = df[fields]
    return result


def lookup_specific_heat_capacity(th_mass):
    """
    Look up the specific heat capacity in [J/K] for the building construction type. This is used for the calculation
    of the internal heat capacity "Cm" in `get_prop_RC_model`.

    `th_mass` is one of the following values:

    - T1: light
    - T2: medium (default)
    - T3: heavy

    :param th_mass: the type of building construction (origin: thermal_properties.shp)
    :return:
    """
    if th_mass == 'T1':
        return 110000.0
    elif th_mass == 'T3':
        return 300000.0
    else:
        return 165000.0


def lookup_effective_mass_area_factor(th_mass):
    """
    Look up the factor to multiply the conditioned floor area by to get the effective mass area by building construction
    type. This is used for the calculation of the effective mass area "Am" in `get_prop_RC_model`.

    `th_mass` is one of the following values:

    - T1: light
    - T2: medium (default)
    - T3: heavy

    :param th_mass: the type of building construction (origin: thermal_properties.shp)
    :return: effective mass area factor
    """
    if th_mass == 'T2':
        return 2.5
    elif th_mass == 'T3':
        return 3.2
    elif th_mass == 'T1':
        return 2.5
    else:
        return 2.5


def test_demand():
        locator = inputlocator.InputLocator(scenario_path=r'C:\reference-case\baseline')
        # for the interface, the user should pick a file out of of those in ...DB/Weather/...
        weather_path = locator.get_default_weather()
        gv = globalvar.GlobalVariables()
        demand_calculation(locator=locator, weather_path=weather_path, gv=gv)
        print "test_demand() succeeded"


if __name__ == '__main__':
    test_demand()


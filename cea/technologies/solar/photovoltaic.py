"""
Photovoltaic
"""

from __future__ import print_function
from __future__ import division
from cea.utilities.standardize_coordinates import get_lat_lon_projected_shapefile
from geopandas import GeoDataFrame as gdf
import os
import time
import numpy as np
import pandas as pd
from scipy import interpolate
import cea.globalvar
import cea.inputlocator
from math import *
from cea.utilities import epwreader
from cea.utilities import solar_equations
from cea.technologies.solar import constants
import cea.config

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca, Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_PV(locator, config, radiation_path, metadata_csv, latitude, longitude, weather_path, building_name):
    """
    This function first determines the surface area with sufficient solar radiation, and then calculates the optimal
    tilt angles of panels at each surface location. The panels are categorized into groups by their surface azimuths,
    tilt angles, and global irradiation. In the last, electricity generation from PV panels of each group is calculated.

    :param locator: An InputLocator to locate input files
    :type locator: cea.inputlocator.InputLocator
    :param radiation_path: solar insulation data on all surfaces of each building (path
    :type radiation_path: String
    :param metadata_csv: data of sensor points measuring solar insulation of each building
    :type metadata_csv: .csv
    :param latitude: latitude of the case study location
    :type latitude: float
    :param longitude: longitude of the case study location
    :type longitude: float
    :param weather_path: path to the weather data file of the case study location
    :type weather_path: .epw
    :param building_name: list of building names in the case study
    :type building_name: Series
    :return: Building_PV.csv with PV generation potential of each building, Building_sensors.csv with sensor data of
        each PV panel.

    """

    t0 = time.clock()

    # weather data
    weather_data = epwreader.epw_reader(weather_path)
    datetime_local = solar_equations.calc_datetime_local_from_weather_file(weather_data, latitude, longitude)
    print('reading weather data done')

    # solar properties
    solar_properties = solar_equations.calc_sun_properties(latitude, longitude, weather_data, datetime_local, config)
    print('calculating solar properties done')

    # calculate properties of PV panel
    panel_properties_PV = calc_properties_PV_db(locator.get_supply_systems(config.region), config)
    print('gathering properties of PV panel')

    # select sensor point with sufficient solar radiation
    max_annual_radiation, annual_radiation_threshold, sensors_rad_clean, sensors_metadata_clean = \
        solar_equations.filter_low_potential(radiation_path, metadata_csv, config)

    print('filtering low potential sensor points done')

    if not sensors_metadata_clean.empty:
        # calculate optimal angle and tilt for panels
        sensors_metadata_cat = solar_equations.optimal_angle_and_tilt(sensors_metadata_clean, latitude,
                                                                      solar_properties,
                                                                      max_annual_radiation, panel_properties_PV)
        print('calculating optimal tile angle and separation done')

        # group the sensors with the same tilt, surface azimuth, and total radiation
        sensor_groups = solar_equations.calc_groups(sensors_rad_clean, sensors_metadata_cat)

        print('generating groups of sensor points done')

        final = calc_pv_generation(sensor_groups, weather_data, datetime_local, solar_properties, latitude, panel_properties_PV)

        final.to_csv(locator.PV_results(building_name=building_name), index=True,
                     float_format='%.2f')  # print PV generation potential
        sensors_metadata_cat.to_csv(locator.PV_metadata_results(building_name=building_name), index=True,
                                    index_label='SURFACE',
                                    float_format='%.2f')  # print selected metadata of the selected sensors

        print(building_name, 'done - time elapsed: %.2f seconds' % (time.clock() - t0))
    else:  # This loop is activated when a building has not sufficient solar potential
        final = pd.DataFrame(
            {'PV_walls_north_E_kWh': 0, 'PV_walls_north_m2': 0, 'PV_walls_south_E_kWh': 0, 'PV_walls_south_m2': 0,
             'PV_walls_east_E_kWh': 0, 'PV_walls_east_m2': 0, 'PV_walls_west_E_kWh': 0, 'PV_walls_west_m2': 0,
             'PV_roofs_top_E_kWh': 0, 'PV_roofs_top_m2': 0,
             'E_PV_gen_kWh': 0, 'Area_PV_m2': 0, 'radiation_kWh': 0}, index=range(8760))
        final.to_csv(locator.PV_results(building_name=building_name), index=True, float_format='%.2f')
        sensors_metadata_cat = pd.DataFrame(
            {'SURFACE': 0, 'AREA_m2': 0, 'BUILDING': 0, 'TYPE': 0, 'Xcoor': 0, 'Xdir': 0, 'Ycoor': 0, 'Ydir': 0,
             'Zcoor': 0, 'Zdir': 0, 'orientation': 0, 'total_rad_Whm2': 0, 'tilt_deg': 0, 'B_deg': 0,
             'array_spacing_m': 0, 'surface_azimuth_deg': 0, 'area_installed_module_m2': 0,
             'CATteta_z': 0, 'CATB': 0, 'CATGB': 0, 'type_orientation': 0}, index=range(2))
        sensors_metadata_cat.to_csv(locator.PV_metadata_results(building_name=building_name), index=True,
                                    float_format='%.2f')

    return


# =========================
# PV electricity generation
# =========================

def calc_pv_generation(sensor_groups, weather_data, date_local, solar_properties, latitude, panel_properties_PV):
    """
    To calculate the electricity generated from PV panels.

    :param hourly_radiation: mean hourly radiation of sensors in each group [Wh/m2]
    :type hourly_radiation: dataframe
    :param number_groups: number of groups of sensor points
    :type number_groups: float
    :param number_points: number of sensor points in each group
    :type number_points: float
    :param prop_observers: mean values of sensor properties of each group of sensors
    :type prop_observers: dataframe
    :param weather_data: weather data read from the epw file
    :type weather_data: dataframe
    :param g: declination
    :type g: float
    :param Sz: zenith angle
    :type Sz: float
    :param Az: solar azimuth
    :param ha: hour angle
    :param latitude: latitude of the case study location
    :return:

    """

    # local variables
    number_groups = sensor_groups['number_groups']  # number of groups of sensor points
    prop_observers = sensor_groups['prop_observers']  # mean values of sensor properties of each group of sensors
    hourly_radiation = sensor_groups['hourlydata_groups']  # mean hourly radiation of sensors in each group [Wh/m2]

    # convert degree to radians
    lat = radians(latitude)
    g_rad = np.radians(solar_properties.g)
    ha_rad = np.radians(solar_properties.ha)
    Sz_rad = np.radians(solar_properties.Sz)
    Az_rad = np.radians(solar_properties.Az)

    # empty list to store results
    list_groups_area = [0 for i in range(number_groups)]
    total_el_output_PV_kWh = [0 for i in range(number_groups)]
    total_radiation_kWh = [0 for i in range(number_groups)]

    potential = pd.DataFrame(index=[range(8760)])
    panel_orientations = ['walls_south', 'walls_north', 'roofs_top', 'walls_east', 'walls_west']
    for panel_orientation in panel_orientations:
        potential['PV_' + panel_orientation + '_E_kWh'] = 0
        potential['PV_' + panel_orientation + '_m2'] = 0

    eff_nom = panel_properties_PV['PV_n']

    Bref = panel_properties_PV['PV_Bref']

    misc_losses = panel_properties_PV['misc_losses']  # cabling, resistances etc..

    for group in prop_observers.index.values:
        # calculate radiation types (direct/diffuse) in group
        radiation_Wperm2 = solar_equations.cal_radiation_type(group, hourly_radiation, weather_data)

        # read panel properties of each group
        teta_z_deg = prop_observers.loc[group, 'surface_azimuth_deg']
        tot_module_area_m2 = prop_observers.loc[group, 'area_installed_module_m2']
        tilt_angle_deg = prop_observers.loc[group, 'B_deg']  # tilt angle of panels
        # degree to radians
        tilt_rad = radians(tilt_angle_deg)  # tilt angle
        teta_z_deg = radians(teta_z_deg)  # surface azimuth

        # calculate effective indicent angles necessary
        teta_rad = np.vectorize(solar_equations.calc_angle_of_incidence)(g_rad, lat, ha_rad, tilt_rad, teta_z_deg)
        teta_ed_rad, teta_eg_rad = calc_diffuseground_comp(tilt_rad)

        absorbed_radiation_Wperm2 = np.vectorize(calc_absorbed_radiation_PV)(radiation_Wperm2.I_sol,
                                                                             radiation_Wperm2.I_direct,
                                                                             radiation_Wperm2.I_diffuse, tilt_rad,
                                                                             Sz_rad, teta_rad, teta_ed_rad,
                                                                             teta_eg_rad, panel_properties_PV)

        T_cell_C = np.vectorize(calc_cell_temperature)(absorbed_radiation_Wperm2, weather_data.drybulb_C,
                                                       panel_properties_PV)

        el_output_PV_kW = np.vectorize(calc_PV_power)(absorbed_radiation_Wperm2, T_cell_C, eff_nom, tot_module_area_m2,
                                                      Bref, misc_losses)

        # write results from each group
        panel_orientation = prop_observers.loc[group, 'type_orientation']
        potential['PV_' + panel_orientation + '_E_kWh'] = potential[
                                                              'PV_' + panel_orientation + '_E_kWh'] + el_output_PV_kW
        potential['PV_' + panel_orientation + '_m2'] = potential['PV_' + panel_orientation + '_m2'] + tot_module_area_m2

        # aggregate results from all modules
        list_groups_area[group] = tot_module_area_m2
        total_el_output_PV_kWh[group] = el_output_PV_kW
        total_radiation_kWh[group] = (radiation_Wperm2['I_sol'] * tot_module_area_m2 / 1000)  # kWh

    # check for missing groups and asign 0 as el_output_PV_kW
    # panel_orientations = ['walls_south', 'walls_north', 'roofs_top', 'walls_east', 'walls_west']
    # for panel_orientation in panel_orientations:
    #     if panel_orientation not in prop_observers['type_orientation'].values:
    #         potential['PV_' + panel_orientation + '_E_kWh'] = 0
    #         potential['PV_' + panel_orientation + '_m2'] = 0

    potential['E_PV_gen_kWh'] = sum(total_el_output_PV_kWh)
    potential['radiation_kWh'] = sum(total_radiation_kWh).values
    potential['Area_PV_m2'] = sum(list_groups_area)
    potential['Date'] = date_local
    potential = potential.set_index('Date')

    return potential


def calc_cell_temperature(absorbed_radiation_Wperm2, T_external_C, panel_properties_PV):
    """
    calculates cell temperatures based on the absorbed radiation

    :param absorbed_radiation_Wperm2: absorbed radiation on panel
    :type absorbed_radiation_Wperm2: np.array
    :param T_external_C: drybulb temperature from the weather file
    :type T_external_C: series
    :param panel_properties_PV: panel property from the supply system database
    :type panel_properties_PV: dataframe
    :return T_cell_C: cell temprature of PV panels
    :rtype T_cell_C: series
    """

    NOCT = panel_properties_PV['PV_noct']
    # temperature of cell
    T_cell_C = T_external_C + absorbed_radiation_Wperm2 * (NOCT - 20) / (
        800)  # assuming linear temperature rise vs radiation according to NOCT condition
    return T_cell_C


def calc_angle_of_incidence(g, lat, ha, tilt, teta_z):
    """
    To calculate angle of incidence from solar vector and surface normal vector.
    (Validated with Sandia pvlib.irrandiance.aoi)

    :param lat: latitude of the loacation of case study [radians]
    :param g: declination of the solar position [radians]
    :param ha: hour angle [radians]
    :param tilt: panel surface tilt angle [radians]
    :param teta_z: panel surface azimuth angle [radians]
    :type lat: float
    :type g: float
    :type ha: float
    :type tilt: float
    :type teta_z: float
    :return teta_B: angle of incidence [radians]
    :rtype teta_B: float

    .. [Sproul, A. B., 2017] Sproul, A.B. (2007). Derivation of the solar geometric relationships using vector analysis.
        Renewable Energy, 32(7), 1187-1205.

    """
    # surface normal vector
    n_E = sin(tilt) * sin(teta_z)
    n_N = sin(tilt) * cos(teta_z)
    n_Z = cos(tilt)
    # solar vector
    s_E = -cos(g) * sin(ha)
    s_N = sin(g) * cos(lat) - cos(g) * sin(lat) * cos(ha)
    s_Z = cos(g) * cos(lat) * cos(ha) + sin(g) * sin(lat)

    # angle of incidence
    teta_B = acos(n_E * s_E + n_N * s_N + n_Z * s_Z)
    return teta_B


def calc_diffuseground_comp(tilt_radians):
    """
    To calculate reflected radiation and diffuse radiation.
    :param tilt_radians:  surface tilt angle [rad]
    :type tilt_radians: float
    :return teta_ed: effective incidence angle from diffuse radiation [rad]
    :return teta_eg: effective incidence angle from ground-reflected radiation [rad]
    :rtype teta_ed: float
    :rtype teta_eg: float

    :References: Duffie, J. A. and Beckman, W. A. (2013) Radiation Transmission through Glazing: Absorbed Radiation, in
                 Solar Engineering of Thermal Processes, Fourth Edition, John Wiley & Sons, Inc., Hoboken, NJ, USA.
                 doi: 10.1002/9781118671603.ch5

    """
    tilt = degrees(tilt_radians)
    teta_ed = 59.68 - 0.1388 * tilt + 0.001497 * tilt ** 2  # [degrees] (5.4.2)
    teta_eG = 90 - 0.5788 * tilt + 0.002693 * tilt ** 2  # [degrees] (5.4.1)
    return radians(teta_ed), radians(teta_eG)


def calc_absorbed_radiation_PV(I_sol, I_direct, I_diffuse, tilt, Sz, teta, tetaed, tetaeg, panel_properties_PV):
    """
    :param I_sol: total solar radiation [Wh/m2]
    :param I_direct: direct solar radiation [Wh/m2]
    :param I_diffuse: diffuse solar radiation [Wh/m2]
    :param tilt: solar panel tilt angle [rad]
    :param Sz: solar zenith angle [rad]
    :param teta: angle of incidence [rad]
    :param tetaed: effective incidence angle from diffuse radiation [rad]
    :param tetaeg: effective incidence angle from ground-reflected radiation [rad]
    :type I_sol: float
    :type I_direct: float
    :type I_diffuse: float
    :type tilt: float
    :type Sz: float
    :type teta: float
    :type tetaed: float
    :type tetaeg: float
    :param panel_properties_PV: properties of the PV panel
    :type panel_properties_PV: dataframe
    :return:

    :References: Duffie, J. A. and Beckman, W. A. (2013) Radiation Transmission through Glazing: Absorbed Radiation, in
                 Solar Engineering of Thermal Processes, Fourth Edition, John Wiley & Sons, Inc., Hoboken, NJ, USA.
                 doi: 10.1002/9781118671603.ch5

    """

    # read variables
    n = constants.n  # refractive index of glass
    Pg = constants.Pg  # ground reflectance
    K = constants.K  # glazing extinction coefficient
    NOCT = panel_properties_PV['PV_noct']
    a0 = panel_properties_PV['PV_a0']
    a1 = panel_properties_PV['PV_a1']
    a2 = panel_properties_PV['PV_a2']
    a3 = panel_properties_PV['PV_a3']
    a4 = panel_properties_PV['PV_a4']
    L = panel_properties_PV['PV_th']

    # calcualte ratio of beam radiation on a tilted plane
    # to avoid inconvergence when I_sol = 0
    lim1 = radians(0)
    lim2 = radians(90)
    lim3 = radians(89.999)

    if teta < lim1:
        teta = min(lim3, abs(teta))
    if teta >= lim2:
        teta = lim3

    if Sz < lim1:
        Sz = min(lim3, abs(Sz))
    if Sz >= lim2:
        Sz = lim3

    # Rb: ratio of beam radiation of tilted surface to that on horizontal surface
    if Sz <= radians(85):  # Sz is Zenith angle   # TODO: FIND REFERENCE
        Rb = cos(teta) / cos(Sz)
    else:
        Rb = 0  # Assume there is no direct radiation when the sun is close to the horizon.

    # calculate air mass modifier
    m = 1 / cos(Sz)  # air mass
    M = a0 + a1 * m + a2 * m ** 2 + a3 * m ** 3 + a4 * m ** 4  # air mass modifier

    # incidence angle modifier for direct (beam) radiation
    teta_r = asin(sin(teta) / n)  # refraction angle in radians(aproximation accrding to Soteris A.) (5.1.4)
    Ta_n = exp(-K * L) * (1 - ((n - 1) / (n + 1)) ** 2)
    if teta < radians(90):  # 90 degrees in radians
        part1 = teta_r + teta
        part2 = teta_r - teta
        Ta_B = exp((-K * L) / cos(teta_r)) * (
            1 - 0.5 * ((sin(part2) ** 2) / (sin(part1) ** 2) + (tan(part2) ** 2) / (tan(part1) ** 2)))
        kteta_B = Ta_B / Ta_n
    else:
        kteta_B = 0

    # incidence angle modifier for diffuse radiation
    teta_r = asin(sin(tetaed) / n)  # refraction angle for diffuse radiation [rad]
    part1 = teta_r + tetaed
    part2 = teta_r - tetaed
    Ta_D = exp((-K * L) / cos(teta_r)) * (
        1 - 0.5 * ((sin(part2) ** 2) / (sin(part1) ** 2) + (tan(part2) ** 2) / (tan(part1) ** 2)))
    kteta_D = Ta_D / Ta_n

    # incidence angle modifier for ground-reflected radiation
    teta_r = asin(sin(tetaeg) / n)  # refraction angle for ground-reflected radiation [rad]
    part1 = teta_r + tetaeg
    part2 = teta_r - tetaeg
    Ta_eG = exp((-K * L) / cos(teta_r)) * (
        1 - 0.5 * ((sin(part2) ** 2) / (sin(part1) ** 2) + (tan(part2) ** 2) / (tan(part1) ** 2)))
    kteta_eG = Ta_eG / Ta_n

    # absorbed solar radiation
    absorbed_radiation_Wperm2 = M * Ta_n * (
        kteta_B * I_direct * Rb + kteta_D * I_diffuse * (1 + cos(tilt)) / 2 + kteta_eG * I_sol * Pg * (
            1 - cos(tilt)) / 2)  # [W/m2] (5.12.1)
    if absorbed_radiation_Wperm2 < 0:  # when points are 0 and too much losses
        #print ('the absorbed radiation', absorbed_radiation_Wperm2 ,'is negative, please check calc_absorbed_radiation_PVT')
        absorbed_radiation_Wperm2 = 0

    return absorbed_radiation_Wperm2


def calc_PV_power(absorbed_radiation_Wperm2, T_cell_C, eff_nom, tot_module_area_m2, Bref_perC, misc_losses):
    """
    To calculate the power production of PV panels.

    :param absorbed_radiation_Wperm2: absorbed radiation [W/m2]
    :type absorbed_radiation_Wperm2: float
    :param T_cell_C: cell temperature [degree]
    :param eff_nom: nominal efficiency of PV module [-]
    :type eff_nom: float
    :param tot_module_area_m2: total PV module area [m2]
    :type tot_module_area_m2: float
    :param Bref_perC: cell maximum power temperature coefficient [degree C^(-1)]
    :type Bref_perC: float
    :param misc_losses: expected system loss [-]
    :type misc_losses: float
    :return el_output_PV_kW: Power production [kW]
    :rtype el_output_PV_kW: float

    ..[Osterwald, C. R., 1986] Osterwald, C. R. (1986). Translation of device performance measurements to
    reference conditions. Solar Cells, 18, 269-279.

    """
    T_standard_C = 25  # temperature at the standard testing condition
    el_output_PV_kW = eff_nom * tot_module_area_m2 * absorbed_radiation_Wperm2 * \
                      (1 - Bref_perC * (T_cell_C - T_standard_C)) * (1 - misc_losses) / 1000
    return el_output_PV_kW


# ============================
# Optimal angle and tilt
# ============================

def optimal_angle_and_tilt(sensors_metadata_clean, latitude, worst_sh, worst_Az, transmissivity,
                           Max_Isol, module_length):
    """
    This function first determines the optimal tilt angle, row spacing and surface azimuth of panels installed at each
    sensor point. Secondly, the installed PV module areas at each sensor point are calculated. Lastly, all the modules
    are categorized with its surface azimuth, tilt angle, and yearly radiation. The output will then be used to
    calculate the absorbed radiation.

    :param sensors_metadata_clean: data of filtered sensor points measuring solar insulation of each building
    :type sensors_metadata_clean: dataframe
    :param latitude: latitude of the case study location
    :type latitude: float
    :param worst_sh: solar elevation at the worst hour [degree]
    :type worst_sh: float
    :param worst_Az: solar azimuth at the worst hour [degree]
    :type worst_Az: float
    :param transmissivity: transmissivity: clearness index [-]
    :type transmissivity: float
    :param module_length: length of the PV module [m]
    :type module_length: float
    :param Max_Isol: max radiation potential (equals to global horizontal radiation) [Wh/m2/year]
    :type Max_Isol: float
    :returns sensors_metadata_clean: data of filtered sensor points categorized with module tilt angle, array spacing,
     surface azimuth, installed PV module area of each sensor point and the categories
    :rtype sensors_metadata_clean: dataframe
    :Assumptions:
        1) Tilt angle: If the sensor is on tilted roof, the panel will have the same tilt as the roof. If the sensor is on
           a wall, the tilt angle is 90 degree. Tilt angles for flat roof is determined using the method from Quinn et al.
        2) Row spacing: Determine the row spacing by minimizing the shadow according to the solar elevation and azimuth at
           the worst hour of the year. The worst hour is a global variable defined by users.
        3) Surface azimuth (orientation) of panels: If the sensor is on a tilted roof, the orientation of the panel is the
           same as the roof. Sensors on flat roofs are all south facing.

    """
    # calculate panel tilt angle (B) for flat roofs (tilt < 5 degrees), slope roofs and walls.
    optimal_angle_flat = calc_optimal_angle(180, latitude,
                                            transmissivity)  # assume surface azimuth = 180 (N,E), south facing
    sensors_metadata_clean['tilt'] = np.vectorize(acos)(sensors_metadata_clean['Zdir'])  # surface tilt angle in rad
    sensors_metadata_clean['tilt'] = np.vectorize(degrees)(
        sensors_metadata_clean['tilt'])  # surface tilt angle in degrees
    sensors_metadata_clean['B'] = np.where(sensors_metadata_clean['tilt'] >= 5, sensors_metadata_clean['tilt'],
                                           degrees(optimal_angle_flat))  # panel tilt angle in degrees

    # calculate spacing and surface azimuth of the panels for flat roofs

    optimal_spacing_flat = calc_optimal_spacing(worst_sh, worst_Az, optimal_angle_flat, module_length)
    sensors_metadata_clean['array_s'] = np.where(sensors_metadata_clean['tilt'] >= 5, 0, optimal_spacing_flat)
    sensors_metadata_clean['surface_azimuth'] = np.vectorize(calc_surface_azimuth)(sensors_metadata_clean['Xdir'],
                                                                                   sensors_metadata_clean['Ydir'],
                                                                                   sensors_metadata_clean[
                                                                                       'B'])  # degrees

    # calculate the surface area required to install one pv panel on flat roofs with defined tilt angle and array spacing
    surface_area_flat = module_length * (
        sensors_metadata_clean.array_s / 2 + module_length * [cos(optimal_angle_flat)])

    # calculate the pv module area within the area of each sensor point
    sensors_metadata_clean['area_module'] = np.where(sensors_metadata_clean['tilt'] >= 5,
                                                     sensors_metadata_clean.AREA_m2,
                                                     module_length ** 2 * (
                                                         sensors_metadata_clean.AREA_m2 / surface_area_flat))

    # categorize the sensors by surface_azimuth, B, GB
    result = np.vectorize(solar_equations.calc_categoriesroof)(sensors_metadata_clean.surface_azimuth,
                                                               sensors_metadata_clean.B,
                                                               sensors_metadata_clean.total_rad_Whm2, Max_Isol)
    sensors_metadata_clean['CATteta_z'] = result[0]
    sensors_metadata_clean['CATB'] = result[1]
    sensors_metadata_clean['CATGB'] = result[2]
    return sensors_metadata_clean


def calc_optimal_angle(teta_z, latitude, transmissivity):
    """
    To calculate the optimal tilt angle of the solar panels.

    :param teta_z: surface azimuth, 0 degree south (east negative) or 0 degree north (east positive)
    :type teta_z: float
    :param latitude: latitude of the case study site
    :type latitude: float
    :param transmissivity: clearness index [-]
    :type transmissivity: float
    :return abs(b): optimal tilt angle [radians]
    :rtype abs(b): float

    ..[Quinn et al., 2013] S.W.Quinn, B.Lehman.A simple formula for estimating the optimum tilt angles of photovoltaic
    panels. 2013 IEEE 14th Work Control Model Electron, Jun, 2013, pp.1-8

    """
    if transmissivity <= 0.15:
        gKt = 0.977
    elif 0.15 < transmissivity <= 0.7:
        gKt = 1.237 - 1.361 * transmissivity
    else:
        gKt = 0.273
    Tad = 0.98  # transmittance-absorptance product of the diffuse radiation
    Tar = 0.97  # transmittance-absorptance product of the reflected radiation
    Pg = 0.2  # ground reflectance of 0.2
    l = radians(latitude)
    a = radians(teta_z)
    b = atan((cos(a) * tan(l)) * (1 / (1 + ((Tad * gKt - Tar * Pg) / (2 * (1 - gKt))))))  # eq.(11)
    return abs(b)


def calc_optimal_spacing(Sh, Az, tilt_angle, module_length):
    """
    To calculate the optimal spacing between each panel to avoid shading.

    :param Sh: Solar elevation at the worst hour [degree]
    :type Sh: float
    :param Az: Solar Azimuth [degree]
    :type Az: float
    :param tilt_angle: optimal tilt angle for panels on flat surfaces [degree]
    :type tilt_angle: float
    :param module_length: [m]
    :type module_length: float
    :return D: optimal distance in [m]
    :rtype D: float
    """
    h = module_length * sin(tilt_angle)
    D1 = h / tan(radians(Sh))
    D = max(D1 * cos(radians(180 - Az)), D1 * cos(radians(Az - 180)))
    return D


# def calc_categoriesroof(teta_z, B, GB, Max_Isol):
#     """
#     To categorize solar panels by the surface azimuth, tilt angle and yearly radiation.

#     :param teta_z: surface azimuth [degree], 0 degree north (east positive, west negative)
#     :type teta_z: float
#     :param B: solar panel tile angle [degree]
#     :type B: float
#     :param GB: yearly radiation of sensors [Wh/m2/year]
#     :type GB: float
#     :param Max_Isol: yearly global horizontal radiation [Wh/m2/year]
#     :type Max_Isol: float
#     :return CATteta_z: category of surface azimuth
#     :rtype CATteta_z: float
#     :return CATB: category of tilt angle
#     :rtype CATB: float
#     :return CATBG: category of yearly radiation
#     :rtype CATBG: float
#     """
#     if -122.5 < teta_z <= -67:
#         CATteta_z = 1
#     elif -67.0 < teta_z <= -22.5:
#         CATteta_z = 3
#     elif -22.5 < teta_z <= 22.5:
#         CATteta_z = 5
#     elif 22.5 < teta_z <= 67:
#         CATteta_z = 4
#     elif 67.0 <= teta_z <= 122.5:
#         CATteta_z = 2
#     else:
#         CATteta_z = 6
#     B = degrees(B)
#     if 0 < B <= 5:
#         CATB = 1  # flat roof
#     elif 5 < B <= 15:
#         CATB = 2  # tilted 5-15 degrees
#     elif 15 < B <= 25:
#         CATB = 3  # tilted 15-25 degrees
#     elif 25 < B <= 40:
#         CATB = 4  # tilted 25-40 degrees
#     elif 40 < B <= 60:
#         CATB = 5  # tilted 40-60 degrees
#     elif B > 60:
#         CATB = 6  # tilted >60 degrees
#     else:
#         CATB = None
#         print('B not in expected range')
#
#     GB_percent = GB / Max_Isol
#     if 0 < GB_percent <= 0.25:
#         CATGB = 1
#     elif 0.25 < GB_percent <= 0.50:
#         CATGB = 2
#     elif 0.50 < GB_percent <= 0.75:
#         CATGB = 3
#     elif 0.75 < GB_percent <= 0.90:
#         CATGB = 4
#     elif 0.90 < GB_percent:
#         CATGB = 5
#     else:
#         CATGB = None
#         print('GB not in expected range')
#
#     return CATteta_z, CATB, CATGB


def calc_surface_azimuth(xdir, ydir, B):
    """
    Calculate surface azimuth from the surface normal vector (x,y,z) and tilt angle (B).
    Following the geological sign convention, an azimuth of 0 and 360 degree represents north, 90 degree is east.

    :param xdir: surface normal vector x in (x,y,z) representing east-west direction
    :param ydir: surface normal vector y in (x,y,z) representing north-south direction
    :param B: surface tilt angle in degree
    :type xdir: float
    :type ydir: float
    :type B: float
    :returns surface azimuth: the azimuth of the surface of a solar panel in degree
    :rtype surface_azimuth: float
    """
    B = radians(B)
    teta_z = degrees(asin(xdir / sin(B)))
    # set the surface azimuth with on the sing convention (E,N)=(+,+)
    if xdir < 0:
        if ydir < 0:
            surface_azimuth = 180 + teta_z  # (xdir,ydir) = (-,-)
        else:
            surface_azimuth = 360 + teta_z  # (xdir,ydir) = (-,+)
    elif ydir < 0:
        surface_azimuth = 180 + teta_z  # (xdir,ydir) = (+,-)
    else:
        surface_azimuth = teta_z  # (xdir,ydir) = (+,+)
    return surface_azimuth  # degree


# ============================
# properties of module
# ============================
# TODO: Delete when done


def calc_properties_PV_db(database_path, config):
    """
    To assign PV module properties according to panel types.

    :param type_PVpanel: type of PV panel used
    :type type_PVpanel: string
    :return: dict with Properties of the panel taken form the database
    """
    type_PVpanel = config.solar.type_PVpanel
    data = pd.read_excel(database_path, sheetname="PV")
    panel_properties = data[data['code'] == type_PVpanel].reset_index().T.to_dict()[0]

    return panel_properties


# investment and maintenance costs
# FIXME: it looks like this function is never used!!! (REMOVE)
def calc_Cinv_pv(total_module_area_m2, locator, config, technology=0):
    """
    To calculate capital cost of PV modules, assuming 20 year system lifetime.
    :param P_peak: installed capacity of PV module [kW]
    :return InvCa: capital cost of the installed PV module [CHF/Y]
    """
    PV_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="PV")
    technology_code = list(set(PV_cost_data['code']))
    PV_cost_data[PV_cost_data['code'] == technology_code[technology]]
    nominal_efficiency = PV_cost_data[PV_cost_data['code'] == technology_code[technology]]['PV_n'].max()
    P_nominal_W = total_module_area_m2 * (constants.STC_RADIATION_Wperm2 * nominal_efficiency)
    # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
    # capacity for the corresponding technology from the database
    if P_nominal_W < PV_cost_data['cap_min'][0]:
        P_nominal_W = PV_cost_data['cap_min'][0]
    PV_cost_data = PV_cost_data[
        (PV_cost_data['cap_min'] <= P_nominal_W) & (PV_cost_data['cap_max'] > P_nominal_W)]
    Inv_a = PV_cost_data.iloc[0]['a']
    Inv_b = PV_cost_data.iloc[0]['b']
    Inv_c = PV_cost_data.iloc[0]['c']
    Inv_d = PV_cost_data.iloc[0]['d']
    Inv_e = PV_cost_data.iloc[0]['e']
    Inv_IR = (PV_cost_data.iloc[0]['IR_%']) / 100
    Inv_LT = PV_cost_data.iloc[0]['LT_yr']
    Inv_OM = PV_cost_data.iloc[0]['O&M_%'] / 100

    InvC = Inv_a + Inv_b * (P_nominal_W) ** Inv_c + (Inv_d + Inv_e * P_nominal_W) * log(P_nominal_W)

    Capex_a_PV_USD = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
    Opex_fixed_PV_USD = Capex_a_PV_USD * Inv_OM
    Capex_PV_USD = InvC

    return Capex_a_PV_USD, Opex_fixed_PV_USD, Capex_PV_USD


# remuneration scheme
def calc_Crem_pv(E_nom):
    """
    Calculates KEV (Kostendeckende Einspeise - Verguetung) for solar PV and PVT.
    Therefore, input the nominal capacity of EACH installation and get the according KEV as return in Rp/kWh

    :param E_nom: Nominal Capacity of solar panels (PV or PVT) [Wh]
    :type E_nom: float
    :return KEV_obtained_in_RpPerkWh: KEV remuneration [Rp/kWh]
    :rtype KEV_obtained_in_RpPerkWh: float
    """
    # TODO: change input argument to area_installed and then calculate the nominal capacity within this function, see calc_Cinv_pv
    KEV_regime = [0, 0, 20.4, 20.4, 20.4, 20.4, 20.4, 20.4, 19.7, 19.3, 19, 18.9, 18.7, 18.6, 18.5, 18.1, 17.9, 17.8,
                  17.8, 17.7, 17.7, 17.7, 17.6, 17.6]
    P_installed_in_kW = [0, 9.99, 10, 12, 15, 20, 29, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500, 750, 1000,
                         1500, 2000, 1000000]
    KEV_interpolated_kW = interpolate.interp1d(P_installed_in_kW, KEV_regime, kind="linear")
    KEV_obtained_in_RpPerkWh = 0
    if (E_nom / 1000) > P_installed_in_kW[-1]:
        number_of_installations = int(math.ceil(E_nom / P_installed_in_kW[-1]))
        E_nom_per_chiller = E_nom / number_of_installations
        for i in range(number_of_installations):
            KEV_obtained_in_RpPerkWh = KEV_obtained_in_RpPerkWh + KEV_interpolated_kW(E_nom_per_chiller / 1000.0)
    else:
        KEV_obtained_in_RpPerkWh = KEV_obtained_in_RpPerkWh + KEV_interpolated_kW(E_nom / 1000.0)
    return KEV_obtained_in_RpPerkWh


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    print('Running photovoltaic with scenario = %s' % config.scenario)
    print('Running photovoltaic with annual-radiation-threshold-kWh/m2 = %s' % config.solar.annual_radiation_threshold)
    print('Running photovoltaic with panel-on-roof = %s' % config.solar.panel_on_roof)
    print('Running photovoltaic with panel-on-wall = %s' % config.solar.panel_on_wall)
    print('Running photovoltaic with solar-window-solstice = %s' % config.solar.solar_window_solstice)
    print('Running photovoltaic with type-pvpanel = %s' % config.solar.type_pvpanel)

    list_buildings_names = locator.get_zone_building_names()

    hourly_results_per_building = gdf.from_file(locator.get_zone_geometry())
    latitude, longitude = get_lat_lon_projected_shapefile(hourly_results_per_building)

    # list_buildings_names =['B026', 'B036', 'B039', 'B043', 'B050'] for missing buildings
    for building in list_buildings_names:
        radiation_path = locator.get_radiation_building(building_name=building)
        radiation_metadata = locator.get_radiation_metadata(building_name=building)
        calc_PV(locator=locator, config=config, radiation_path=radiation_path, metadata_csv=radiation_metadata,
                latitude=latitude, longitude=longitude, weather_path=config.weather, building_name=building)

    # aggregate results from all buildings
    aggregated_annual_results = {}
    for i, building in enumerate(list_buildings_names):
        hourly_results_per_building = pd.read_csv(locator.PV_results(building))
        if i == 0:
            aggregated_hourly_results_df = hourly_results_per_building
        else:
            aggregated_hourly_results_df = aggregated_hourly_results_df + hourly_results_per_building

        annual_energy_production = hourly_results_per_building.filter(like='_kWh').sum()
        panel_area_per_building = hourly_results_per_building.filter(like='_m2').iloc[0]
        building_annual_results = annual_energy_production.append(panel_area_per_building)
        aggregated_annual_results[building] = building_annual_results

    # save hourly results
    aggregated_hourly_results_df = aggregated_hourly_results_df.set_index('Date')
    aggregated_hourly_results_df.to_csv(locator.PV_totals(), index=True, float_format='%.2f')
    # save annual results
    aggregated_annual_results_df = pd.DataFrame(aggregated_annual_results).T
    aggregated_annual_results_df.to_csv(locator.PV_total_buildings(), index=True, float_format='%.2f')



if __name__ == '__main__':
    main(cea.config.Configuration())

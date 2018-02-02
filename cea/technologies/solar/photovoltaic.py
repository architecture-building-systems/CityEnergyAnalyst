from __future__ import print_function

"""
photovoltaic
"""

from __future__ import division

import os
import time
import numpy as np
import pandas as pd
from scipy import interpolate
import fiona
import cea.globalvar
import cea.inputlocator
from math import *
from cea.utilities import epwreader
from cea.utilities import solar_equations
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
    settings = config.solar

    t0 = time.clock()

    # weather data
    weather_data = epwreader.epw_reader(weather_path)
    print('reading weather data done')

    # solar properties
    solar_properties = solar_equations.calc_sun_properties(latitude, longitude, weather_data, settings.date_start,
                                                           settings.solar_window_solstice)
    print('calculating solar properties done')

    # calculate properties of PV panel
    panel_properties = calc_properties_PV_db(locator.get_supply_systems(config.region), settings.type_pvpanel)
    print('gathering properties of PV panel')

    # select sensor point with sufficient solar radiation
    max_yearly_radiation, min_yearly_production, sensors_rad_clean, sensors_metadata_clean = \
        solar_equations.filter_low_potential(weather_data, radiation_path, metadata_csv, settings.min_radiation,
                                             settings.panel_on_roof, settings.panel_on_wall)

    print('filtering low potential sensor points done')

    if not sensors_metadata_clean.empty:
        # calculate optimal angle and tilt for panels
        sensors_metadata_cat = solar_equations.optimal_angle_and_tilt(sensors_metadata_clean, latitude,
                                                                      solar_properties,
                                                                      max_yearly_radiation, panel_properties)
        print('calculating optimal tile angle and separation done')

        # group the sensors with the same tilt, surface azimuth, and total radiation
        number_groups, hourlydata_groups, number_points, prop_observers = solar_equations.calc_groups(sensors_rad_clean,
                                                                                                      sensors_metadata_cat)

        print('generating groups of sensor points done')

        final = calc_pv_generation(hourlydata_groups, number_groups, number_points, prop_observers,
                                            weather_data, solar_properties, latitude, panel_properties)

        final.to_csv(locator.PV_results(building_name=building_name), index=True,
                     float_format='%.2f')  # print PV generation potential
        sensors_metadata_cat.to_csv(locator.PV_metadata_results(building_name=building_name), index=True,
                                    index_label='SURFACE',
                                    float_format='%.2f')  # print selected metadata of the selected sensors

        print('done - time elapsed: %.2f seconds' % (time.clock() - t0))
    else:  # This loop is activated when a building has not sufficient solar potential
        final = pd.DataFrame(
            {'E_PV_gen_kWh': 0, 'Area_PV_m2': 0, 'radiation_kWh': 0}, index=range(8760))
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

def calc_pv_generation(hourly_radiation, number_groups, number_points, prop_observers, weather_data, solar_properties,
                       latitude, panel_properties):
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

    # convert degree to radians
    lat = radians(latitude)
    g_rad = np.radians(solar_properties.g)
    ha_rad = np.radians(solar_properties.ha)
    Sz_rad = np.radians(solar_properties.Sz)
    Az_rad = np.radians(solar_properties.Az)

    list_groups_area = list(range(number_groups))
    Sum_PV_kWh = np.zeros(8760)
    Sum_radiation_kWh = np.zeros(8760)
    potential = pd.DataFrame(index=[range(8760)])

    n = 1.526  # refractive index of glass
    Pg = 0.2  # ground reflectance
    K = 0.4  # glazing extinction coefficient
    eff_nom = panel_properties['PV_n']
    NOCT = panel_properties['PV_noct']
    Bref = panel_properties['PV_Bref']
    a0 = panel_properties['PV_a0']
    a1 = panel_properties['PV_a1']
    a2 = panel_properties['PV_a2']
    a3 = panel_properties['PV_a3']
    a4 = panel_properties['PV_a4']
    L = panel_properties['PV_th']
    misc_losses = panel_properties['misc_losses']  # cabling, resistances etc..

    for group in range(number_groups):
        # read panel properties of each group
        teta_z_deg = prop_observers.loc[group, 'surface_azimuth_deg']
        area_per_group_m2 = prop_observers.loc[group, 'total_area_module_m2']
        tilt_angle_deg = prop_observers.loc[group, 'B_deg']
        # degree to radians
        tilt_rad = radians(tilt_angle_deg)  # tilt angle
        teta_z_deg = radians(teta_z_deg)  # surface azimuth

        # read radiation data of each group
        radiation = pd.DataFrame({'I_sol': hourly_radiation[group]})
        radiation['I_diffuse'] = weather_data.ratio_diffhout.fillna(0) * radiation.I_sol  # calculate diffuse radiation
        radiation['I_direct'] = radiation['I_sol'] - radiation['I_diffuse']  # calculat direct radaition

        # calculate effective indicent angles necessary
        teta_vector = np.vectorize(solar_equations.calc_angle_of_incidence)(g_rad, lat, ha_rad, tilt_rad, teta_z_deg)
        teta_ed, teta_eg = calc_diffuseground_comp(tilt_rad)

        absorbed_radiation = np.vectorize(calc_Sm_PV)(weather_data.drybulb_C, radiation.I_sol, radiation.I_direct,
                                                      radiation.I_diffuse, tilt_rad, Sz_rad, teta_vector, teta_ed,
                                                      teta_eg, n, Pg,
                                                      K, NOCT, a0, a1, a2, a3, a4, L)

        result = np.vectorize(calc_PV_power)(absorbed_radiation[0], absorbed_radiation[1], eff_nom, area_per_group_m2,
                                             Bref, misc_losses)

        # calculate results from each group
        name_group = prop_observers.loc[group, 'type_orientation']
        potential['PV_' + name_group + '_E_kWh'] = result
        potential['PV_' + name_group + '_m2'] = area_per_group_m2

        # aggregate results from all modules
        list_groups_area[group] = area_per_group_m2
        Sum_PV_kWh = Sum_PV_kWh + result
        Sum_radiation_kWh = Sum_radiation_kWh + radiation['I_sol'] * area_per_group_m2 / 1000  # kWh

    potential['E_PV_gen_kWh'] = Sum_PV_kWh
    potential['radiation_kWh'] = Sum_radiation_kWh
    potential['Area_PV_m2'] = sum(list_groups_area)

    return potential


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


def calc_Sm_PV(te, I_sol, I_direct, I_diffuse, tilt, Sz, teta, tetaed, tetaeg,
               n, Pg, K, NOCT, a0, a1, a2, a3, a4, L):
    """
    To calculate the absorbed solar radiation on tilted surface.

    :param te: dry bulb temperature [C]
    :param I_sol: total solar radiation [Wh/m2]
    :param I_direct: direct solar radiation [Wh/m2]
    :param I_diffuse: diffuse solar radiation [Wh/m2]
    :param tilt: solar panel tilt angle [rad]
    :param Sz: solar zenith angle [rad]
    :param teta: angle of incidence [rad]
    :param tetaed: effective incidence angle from diffuse radiation [rad]
    :param tetaeg: effective incidence angle from ground-reflected radiation [rad]
    :param n: refractive index of glass
    :param Pg: ground reflectance [-]
    :param K: glazing extinction coefficient
    :param NOCT: normal operting cell temperature [C]
    :param a0: constant for PV material
    :param a1: constant for PV material
    :param a2: constant for PV material
    :param a3: constant for PV material
    :param a4: constant for PV material
    :param L: glazing thickness [m]
    :type te: float
    :type I_sol: float
    :type I_direct: float
    :type I_diffuse: float
    :type tilt: float
    :type Sz: float
    :type teta: float
    :type tetaed: float
    :type tetaeg: float
    :type n: float
    :type Pg: float
    :type K: float
    :type NOCT: float
    :type a0: float
    :type a1: float
    :type a2: float
    :type a3: float
    :type a4: float
    :type L: float
    :return S: absorbed solar radiation [Wh/m2]
    :rtype S: float
    :return Tcell: cell temperature [C]
    :rtype Tcell: float

    :References: Duffie, J. A. and Beckman, W. A. (2013) Radiation Transmission through Glazing: Absorbed Radiation, in
                 Solar Engineering of Thermal Processes, Fourth Edition, John Wiley & Sons, Inc., Hoboken, NJ, USA.
                 doi: 10.1002/9781118671603.ch5
    """

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
    S_Wperm2 = M * Ta_n * (
    kteta_B * I_direct * Rb + kteta_D * I_diffuse * (1 + cos(tilt)) / 2 + kteta_eG * I_sol * Pg * (
        1 - cos(tilt)) / 2)  # [W/m2] (5.12.1)
    if S_Wperm2 <= 0:  # when points are 0 and too much losses
        S_Wperm2 = 0

    # temperature of cell
    Tcell_C = te + S_Wperm2 * (NOCT - 20) / (
    800)  # assuming linear temperature rise vs radiation according to NOCT condition

    return S_Wperm2, Tcell_C


def calc_PV_power(S, Tcell, eff_nom, areagroup, Bref, misc_losses):
    """
    To calculate the power production of PV panels.

    :param S: absorbed radiation [W/m2]
    :type S: float
    :param Tcell: cell temperature [degree]
    :param eff_nom: nominal efficiency of PV module [-]
    :type eff_nom: float
    :param areagroup: PV module area [m2]
    :type areagroup: float
    :param Bref: cell maximum power temperature coefficient [degree C^(-1)]
    :type Bref: float
    :param misc_losses: expected system loss [-]
    :type misc_losses: float
    :return P: Power production [kW]
    :rtype P: float

    ..[Osterwald, C. R., 1986] Osterwald, C. R. (1986). Translation of device performance measurements to
    reference conditions. Solar Cells, 18, 269-279.
    """
    P = eff_nom * areagroup * S * (1 - Bref * (Tcell - 25)) * (1 - misc_losses) / 1000
    return P


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
    result = np.vectorize(calc_categoriesroof)(sensors_metadata_clean.surface_azimuth, sensors_metadata_clean.B,
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


def calc_categoriesroof(teta_z, B, GB, Max_Isol):
    """
    To categorize solar panels by the surface azimuth, tilt angle and yearly radiation.

    :param teta_z: surface azimuth [degree], 0 degree north (east positive, west negative)
    :type teta_z: float
    :param B: solar panel tile angle [degree]
    :type B: float
    :param GB: yearly radiation of sensors [Wh/m2/year]
    :type GB: float
    :param Max_Isol: yearly global horizontal radiation [Wh/m2/year]
    :type Max_Isol: float
    :return CATteta_z: category of surface azimuth
    :rtype CATteta_z: float
    :return CATB: category of tilt angle
    :rtype CATB: float
    :return CATBG: category of yearly radiation
    :rtype CATBG: float
    """
    if -122.5 < teta_z <= -67:
        CATteta_z = 1
    elif -67.0 < teta_z <= -22.5:
        CATteta_z = 3
    elif -22.5 < teta_z <= 22.5:
        CATteta_z = 5
    elif 22.5 < teta_z <= 67:
        CATteta_z = 4
    elif 67.0 <= teta_z <= 122.5:
        CATteta_z = 2
    else:
        CATteta_z = 6
    B = degrees(B)
    if 0 < B <= 5:
        CATB = 1  # flat roof
    elif 5 < B <= 15:
        CATB = 2  # tilted 5-15 degrees
    elif 15 < B <= 25:
        CATB = 3  # tilted 15-25 degrees
    elif 25 < B <= 40:
        CATB = 4  # tilted 25-40 degrees
    elif 40 < B <= 60:
        CATB = 5  # tilted 40-60 degrees
    elif B > 60:
        CATB = 6  # tilted >60 degrees
    else:
        CATB = None
        print('B not in expected range')

    GB_percent = GB / Max_Isol
    if 0 < GB_percent <= 0.25:
        CATGB = 1
    elif 0.25 < GB_percent <= 0.50:
        CATGB = 2
    elif 0.50 < GB_percent <= 0.75:
        CATGB = 3
    elif 0.75 < GB_percent <= 0.90:
        CATGB = 4
    elif 0.90 < GB_percent:
        CATGB = 5
    else:
        CATGB = None
        print('GB not in expected range')

    return CATteta_z, CATB, CATGB


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



def calc_properties_PV_db(database_path, type_PVpanel):
    """
    To assign PV module properties according to panel types.

    :param type_PVpanel: type of PV panel used
    :type type_PVpanel: string
    :return: dict with Properties of the panel taken form the database
    """

    data = pd.read_excel(database_path, sheetname="PV")
    panel_properties = data[data['code'] == type_PVpanel].reset_index().T.to_dict()[0]

    return panel_properties


# investment and maintenance costs
# FIXME: it looks like this function is never used!!! (REMOVE)
def calc_Cinv_pv(P_peak_kW, locator, config, technology=0):
    """
    To calculate capital cost of PV modules, assuming 20 year system lifetime.
    :param P_peak: installed capacity of PV module [kW]
    :return InvCa: capital cost of the installed PV module [CHF/Y]
    """
    P_peak = P_peak_kW * 1000  # converting to W from kW
    PV_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="PV")
    technology_code = list(set(PV_cost_data['code']))
    PV_cost_data[PV_cost_data['code'] == technology_code[technology]]
    # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
    # capacity for the corresponding technology from the database
    if P_peak < PV_cost_data['cap_min'][0]:
        P_peak = PV_cost_data['cap_min'][0]
    PV_cost_data = PV_cost_data[
        (PV_cost_data['cap_min'] <= P_peak) & (PV_cost_data['cap_max'] > P_peak)]
    Inv_a = PV_cost_data.iloc[0]['a']
    Inv_b = PV_cost_data.iloc[0]['b']
    Inv_c = PV_cost_data.iloc[0]['c']
    Inv_d = PV_cost_data.iloc[0]['d']
    Inv_e = PV_cost_data.iloc[0]['e']
    Inv_IR = (PV_cost_data.iloc[0]['IR_%']) / 100
    Inv_LT = PV_cost_data.iloc[0]['LT_yr']
    Inv_OM = PV_cost_data.iloc[0]['O&M_%'] / 100

    InvC = Inv_a + Inv_b * (P_peak) ** Inv_c + (Inv_d + Inv_e * P_peak) * log(P_peak)

    Capex_a = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
    Opex_fixed = Capex_a * Inv_OM

    return Capex_a, Opex_fixed


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

    KEV_regime = [0,
                  0,
                  20.4,
                  20.4,
                  20.4,
                  20.4,
                  20.4,
                  20.4,
                  19.7,
                  19.3,
                  19,
                  18.9,
                  18.7,
                  18.6,
                  18.5,
                  18.1,
                  17.9,
                  17.8,
                  17.8,
                  17.7,
                  17.7,
                  17.7,
                  17.6,
                  17.6]
    P_installed_in_kW = [0,
                         9.99,
                         10,
                         12,
                         15,
                         20,
                         29,
                         30,
                         40,
                         50,
                         60,
                         70,
                         80,
                         90,
                         100,
                         200,
                         300,
                         400,
                         500,
                         750,
                         1000,
                         1500,
                         2000,
                         1000000]
    KEV_interpolated_kW = interpolate.interp1d(P_installed_in_kW, KEV_regime, kind="linear")
    KEV_obtained_in_RpPerkWh = KEV_interpolated_kW(E_nom / 1000.0)
    return KEV_obtained_in_RpPerkWh


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    print('Running photovoltaic with scenario = %s' % config.scenario)
    print('Running photovoltaic with date-start = %s' % config.solar.date_start)
    print('Running photovoltaic with dpl = %s' % config.solar.dpl)
    print('Running photovoltaic with eff-pumping = %s' % config.solar.eff_pumping)
    print('Running photovoltaic with fcr = %s' % config.solar.fcr)
    print('Running photovoltaic with k-msc-max = %s' % config.solar.k_msc_max)
    print('Running photovoltaic with min-radiation = %s' % config.solar.min_radiation)
    print('Running photovoltaic with panel-on-roof = %s' % config.solar.panel_on_roof)
    print('Running photovoltaic with panel-on-wall = %s' % config.solar.panel_on_wall)
    print('Running photovoltaic with ro = %s' % config.solar.ro)
    print('Running photovoltaic with solar-window-solstice = %s' % config.solar.solar_window_solstice)
    print('Running photovoltaic with t-in-pvt = %s' % config.solar.t_in_pvt)
    print('Running photovoltaic with t-in-sc = %s' % config.solar.t_in_sc)
    print('Running photovoltaic with type-pvpanel = %s' % config.solar.type_pvpanel)
    print('Running photovoltaic with type-scpanel = %s' % config.solar.type_scpanel)

    list_buildings_names = locator.get_zone_building_names()

    with fiona.open(locator.get_zone_geometry()) as shp:
        longitude = shp.crs['lon_0']
        latitude = shp.crs['lat_0']

    # list_buildings_names =['B026', 'B036', 'B039', 'B043', 'B050'] for missing buildings
    for building in list_buildings_names:
        radiation_path = locator.get_radiation_building(building_name=building)
        radiation_metadata = locator.get_radiation_metadata(building_name=building)
        calc_PV(locator=locator, config=config, radiation_path=radiation_path, metadata_csv=radiation_metadata,
                latitude=latitude,
                longitude=longitude, weather_path=config.weather, building_name=building, )

    for i, building in enumerate(list_buildings_names):
        data = pd.read_csv(locator.PV_results(building))
        if i == 0:
            df = data
        else:
            df = df + data
    del df[df.columns[0]]
    df.to_csv(locator.PV_totals(), index=True, float_format='%.2f')


if __name__ == '__main__':
    main(cea.config.Configuration())

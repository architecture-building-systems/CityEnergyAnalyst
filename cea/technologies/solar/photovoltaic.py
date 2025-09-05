"""
Photovoltaic
"""

import os
import time
from itertools import repeat
from math import radians, degrees, sin, acos, cos, tan, ceil, log
from multiprocessing.dummy import Pool

import numpy as np
import pandas as pd
import pvlib
from geopandas import GeoDataFrame as gdf
from scipy import interpolate

import cea.config
import cea.inputlocator
import cea.utilities.parallel
from cea.analysis.costs.equations import calc_capex_annualized
from cea.constants import HOURS_IN_YEAR
from cea.technologies.solar import constants
from cea.utilities import epwreader
from cea.utilities import solar_equations
from cea.utilities.standardize_coordinates import get_lat_lon_projected_shapefile

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca, Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def projected_lifetime_output(
    production_values,
    lifetime_years,
    max_performance=100,
    annual_factor=0.54,
    min_performance=80,
):
    """
    Model the projected lifetime output of a PV module using a linear derating system
    Authors:
    - Justin McCarty

    Args:
        production_values (np.array shape(n_time_steps,)): electricity produced during the first year
        lifetime_years (int): the expected lifetime of the module
        max_performance (int, optional): _description_. Defaults to 100.
        annual_factor (float, optional): _description_. Defaults to 0.54.
        min_performance (int, optional): _description_. Defaults to 80.

    Returns:
        np.array: array with shape (lifetime_years, n_time_steps)
    """
    derate_factors = np.linspace(
        max_performance, max_performance - (lifetime_years * annual_factor), num=lifetime_years
    ).reshape(-1, 1)
    derate_factors = np.clip(derate_factors, min_performance, None) / 100
    lifetime_production = production_values * derate_factors
    return lifetime_production

def calc_PV(locator, config, type_PVpanel, latitude, longitude, weather_data, datetime_local, building_name):
    """
    This function first determines the surface area with sufficient solar radiation, and then calculates the optimal
    tilt angles of panels at each surface location. The panels are categorized into groups by their surface azimuths,
    tilt angles, and global irradiation. In the last, electricity generation from PV panels of each group is calculated.

    :param locator: An InputLocator to locate input files
    :type locator: cea.inputlocator.InputLocator
    :param latitude: latitude of the case study location
    :type latitude: float
    :param longitude: longitude of the case study location
    :type longitude: float
    :param building_name: list of building names in the case study
    :type building_name: Series
    :return: Building_PV.csv with PV generation potential of each building, Building_sensors.csv with sensor data of
        each PV panel.

    """

    t0 = time.perf_counter()
    radiation_path = locator.get_radiation_building_sensors(building_name)
    metadata_csv_path = locator.get_radiation_metadata(building_name)

    # solar properties
    solar_properties = solar_equations.calc_sun_properties(latitude, longitude, weather_data, datetime_local, config)

    # calculate properties of PV panel
    panel_properties_PV = get_properties_PV_db(locator.get_db4_components_conversion_conversion_technology_csv('PHOTOVOLTAIC_PANELS'), type_PVpanel)
    # print('gathering properties of PV panel')

    # select sensor point with sufficient solar radiation
    max_annual_radiation, annual_radiation_threshold, sensors_rad_clean, sensors_metadata_clean = \
        solar_equations.filter_low_potential(radiation_path, metadata_csv_path, config)

    # set the maximum roof coverage
    max_roof_coverage = config.solar.max_roof_coverage

    if not sensors_metadata_clean.empty:
        if not config.solar.custom_tilt_angle:
            # calculate optimal angle and tilt for panels
            sensors_metadata_cat = solar_equations.optimal_angle_and_tilt(sensors_metadata_clean, latitude,
                                                                          solar_properties,
                                                                          max_annual_radiation, panel_properties_PV,
                                                                          max_roof_coverage)
        else:
            # calculate spacing required by user-supplied tilt angle for panels
            sensors_metadata_cat = solar_equations.calc_spacing_custom_angle(sensors_metadata_clean, solar_properties,
                                                                             max_annual_radiation, panel_properties_PV,
                                                                             config.solar.panel_tilt_angle,
                                                                             max_roof_coverage)

        # group the sensors with the same tilt, surface azimuth, and total radiation
        sensor_groups = solar_equations.calc_groups(sensors_rad_clean, sensors_metadata_cat)

        # print('generating groups of sensor points done')

        final = calc_pv_generation(sensor_groups, weather_data, datetime_local, solar_properties, latitude, longitude,
                                   panel_properties_PV)
        locator.ensure_parent_folder_exists(locator.PV_results(building=building_name, panel_type=type_PVpanel))
        final.to_csv(locator.PV_results(building=building_name, panel_type=type_PVpanel), index=True,
                     float_format='%.2f')  # print PV generation potential
        locator.ensure_parent_folder_exists(locator.PV_metadata_results(building=building_name))
        sensors_metadata_cat.to_csv(locator.PV_metadata_results(building=building_name), index=True,
                                    index_label='SURFACE',
                                    float_format='%.2f',
                                    na_rep='nan')  # print selected metadata of the selected sensors

        print(f'Building {building_name} done - time elapsed: {(time.perf_counter() - t0):.2f} seconds')
    else:  # This loop is activated when a building has not sufficient solar potential
        final = pd.DataFrame(
            {'date': datetime_local, 'PV_walls_north_E_kWh': 0, 'PV_walls_north_m2': 0, 'PV_walls_south_E_kWh': 0,
             'PV_walls_south_m2': 0,
             'PV_walls_east_E_kWh': 0, 'PV_walls_east_m2': 0, 'PV_walls_west_E_kWh': 0, 'PV_walls_west_m2': 0,
             'PV_roofs_top_E_kWh': 0, 'PV_roofs_top_m2': 0,
             'E_PV_gen_kWh': 0, 'area_PV_m2': 0, 'radiation_kWh': 0}, index=range(HOURS_IN_YEAR))
        locator.ensure_parent_folder_exists(locator.PV_results(building=building_name, panel_type=type_PVpanel))
        final.to_csv(locator.PV_results(building=building_name, panel_type=type_PVpanel), index=False, float_format='%.2f', na_rep='nan')
        sensors_metadata_cat = pd.DataFrame(
            {'SURFACE': 0, 'AREA_m2': 0, 'BUILDING': 0, 'TYPE': 0, 'Xcoor': 0, 'Xdir': 0, 'Ycoor': 0, 'Ydir': 0,
             'Zcoor': 0, 'Zdir': 0, 'orientation': 0, 'total_rad_Whm2': 0, 'tilt_deg': 0, 'B_deg': 0,
             'array_spacing_m': 0, 'surface_azimuth_deg': 0, 'area_installed_module_m2': 0,
             'CATteta_z': 0, 'CATB': 0, 'CATGB': 0, 'type_orientation': 0}, index=range(2))
        locator.ensure_parent_folder_exists(locator.PV_metadata_results(building=building_name))
        sensors_metadata_cat.to_csv(locator.PV_metadata_results(building=building_name), index=False,
                                    float_format='%.2f', na_rep='nan')


# =========================
# PV electricity generation
# =========================

def calc_pv_generation(sensor_groups, weather_data, date_local, solar_properties, latitude, longitude,
                       panel_properties_PV):
    """
    To calculate the electricity generated from PV panels.
    """

    # local variables
    number_groups = sensor_groups['number_groups']  # number of groups of sensor points
    prop_observers = sensor_groups['prop_observers']  # mean values of sensor properties of each group of sensors
    hourly_radiation = sensor_groups['hourlydata_groups']  # mean hourly radiation of sensors in each group [Wh/m2]

    # Adjust sign convention: in Duffie (2013) collector azimuth facing equator = 0◦ (p. xxxiii)
    if latitude >= 0:
        Az = solar_properties.Az - 180  # south is 0°, east is negative and west is positive (p. 13)
    else:
        Az = solar_properties.Az  # north is 0°

    # convert degree to radians
    Sz_rad = np.radians(solar_properties.Sz)

    # empty list to store results
    list_groups_area = [0 for i in range(number_groups)]
    total_el_output_PV_kWh = [0 for i in range(number_groups)]
    total_radiation_kWh = [0 for i in range(number_groups)]

    potential = pd.DataFrame(index=range(HOURS_IN_YEAR))
    panel_orientations = ['walls_south', 'walls_north', 'roofs_top', 'walls_east', 'walls_west']
    for panel_orientation in panel_orientations:
        potential['PV_' + panel_orientation + '_E_kWh'] = 0
        potential['PV_' + panel_orientation + '_m2'] = 0

    eff_nom = panel_properties_PV['PV_n']  # nominal efficiency

    Bref = panel_properties_PV['PV_Bref']  # cell maximum power temperature coefficient

    misc_losses = panel_properties_PV['misc_losses']  # cabling, resistances etc..
    for group in prop_observers.index.values:
        # calculate radiation types (direct/diffuse) in group
        radiation_Wperm2 = solar_equations.calc_radiation_type(group, hourly_radiation, weather_data)

        # read panel properties of each group
        teta_z_deg = prop_observers.loc[group, 'surface_azimuth_deg']
        tot_module_area_m2 = prop_observers.loc[group, 'area_installed_module_m2']
        tilt_angle_deg = prop_observers.loc[group, 'B_deg']  # tilt angle of panels
        tilt_rad = radians(tilt_angle_deg) # degree to radians

        # calculate effective incident angles necessary
        teta_deg = pvlib.irradiance.aoi(tilt_angle_deg, teta_z_deg, solar_properties.Sz, Az)
        teta_rad = [radians(x) for x in teta_deg]

        teta_ed_rad, teta_eg_rad = calc_diffuseground_comp(tilt_rad)

        absorbed_radiation_Wperm2 = calc_absorbed_radiation_PV(radiation_Wperm2.I_sol,
                                                            radiation_Wperm2.I_direct,
                                                            radiation_Wperm2.I_diffuse, tilt_rad,
                                                            Sz_rad, teta_rad, teta_ed_rad,
                                                            teta_eg_rad, panel_properties_PV,
                                                            latitude, longitude)

        T_cell_C = calc_cell_temperature(absorbed_radiation_Wperm2, weather_data.drybulb_C,panel_properties_PV)

        el_output_PV_kW = calc_PV_power(absorbed_radiation_Wperm2, T_cell_C, eff_nom, tot_module_area_m2, Bref, misc_losses)

        # write results from each group
        panel_orientation = prop_observers.loc[group, 'type_orientation']
        potential['PV_' + panel_orientation + '_E_kWh'] = potential[
                                                              'PV_' + panel_orientation + '_E_kWh'] + el_output_PV_kW
        potential['PV_' + panel_orientation + '_m2'] = potential['PV_' + panel_orientation + '_m2'] + tot_module_area_m2

        # aggregate results from all modules
        list_groups_area[group] = tot_module_area_m2
        total_el_output_PV_kWh[group] = el_output_PV_kW
        total_radiation_kWh[group] = (radiation_Wperm2['I_sol'] * tot_module_area_m2 / 1000)  # kWh

    # check for missing groups and assign 0 as el_output_PV_kW
    # panel_orientations = ['walls_south', 'walls_north', 'roofs_top', 'walls_east', 'walls_west']
    # for panel_orientation in panel_orientations:
    #     if panel_orientation not in prop_observers['type_orientation'].values:
    #         potential['PV_' + panel_orientation + '_E_kWh'] = 0
    #         potential['PV_' + panel_orientation + '_m2'] = 0

    potential['E_PV_gen_kWh'] = sum(total_el_output_PV_kWh)
    potential['radiation_kWh'] = sum(total_radiation_kWh).values
    potential['area_PV_m2'] = sum(list_groups_area)
    potential['date'] = date_local
    potential = potential.set_index('date')

    return potential


def calc_cell_temperature(absorbed_radiation_Wperm2, T_external_C, panel_properties_PV):
    """
    Calculates cell temperatures based on the absorbed radiation

    :param absorbed_radiation_Wperm2: absorbed radiation on panel
    :type absorbed_radiation_Wperm2: float or numpy.ndarray
    :param T_external_C: drybulb temperature from the weather file
    :type T_external_C: float or numpy.ndarray
    :param panel_properties_PV: panel property from the supply system database
    :type panel_properties_PV: dataframe
    :return T_cell_C: cell temperature of PV panels
    :rtype T_cell_C: float or numpy.ndarray
    """
    # Convert inputs to numpy arrays if they're not already
    absorbed_radiation_Wperm2 = np.asarray(absorbed_radiation_Wperm2)
    T_external_C = np.asarray(T_external_C)
    
    NOCT = panel_properties_PV['PV_noct']
    # temperature of cell
    T_cell_C = T_external_C + absorbed_radiation_Wperm2 * (NOCT - 20) / 800  # assuming linear temperature rise vs radiation according to NOCT condition
    
    # Return scalar if input was scalar
    if np.size(T_cell_C) == 1:
        return float(T_cell_C)
    return T_cell_C


def calc_angle_of_incidence(g, lat, ha, tilt, teta_z):
    """
    To calculate angle of incidence from solar vector and surface normal vector.
    (Validated with Sandia pvlib.irrandiance.aoi)

    :param lat: latitude of the location of case study [radians]
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
    teta_ed = 59.7 - 0.1388 * tilt + 0.001497 * tilt ** 2  # [degrees] (5.4.2)
    teta_eG = 90 - 0.5788 * tilt + 0.002693 * tilt ** 2  # [degrees] (5.4.1)
    return radians(teta_ed), radians(teta_eG)


def calc_absorbed_radiation_PV(I_sol, I_direct, I_diffuse, tilt, Sz, teta, tetaed, tetaeg, panel_properties_PV,
                               latitude, longitude):
    """
    :param I_sol: total solar radiation [Wh/m2]
    :param I_direct: direct solar radiation [Wh/m2]
    :param I_diffuse: diffuse solar radiation [Wh/m2]
    :param tilt: solar panel tilt angle [rad]
    :param Sz: solar zenith angle [rad]
    :param teta: angle of incidence [rad]
    :param tetaed: effective incidence angle from diffuse radiation [rad]
    :param tetaeg: effective incidence angle from ground-reflected radiation [rad]
    :type I_sol: float or numpy.ndarray
    :type I_direct: float or numpy.ndarray
    :type I_diffuse: float or numpy.ndarray
    :type tilt: float or numpy.ndarray
    :type Sz: float or numpy.ndarray
    :type teta: float or numpy.ndarray
    :type tetaed: float or numpy.ndarray
    :type tetaeg: float or numpy.ndarray
    :param panel_properties_PV: properties of the PV panel
    :type panel_properties_PV: dataframe
    :return: absorbed radiation [W/m2]
    :rtype: float or numpy.ndarray

    :References: Duffie, J. A. and Beckman, W. A. (2013) Radiation Transmission through Glazing: Absorbed Radiation, in
                 Solar Engineering of Thermal Processes, Fourth Edition, John Wiley & Sons, Inc., Hoboken, NJ, USA.
                 doi: 10.1002/9781118671603.ch5
    """
    # Convert inputs to numpy arrays if they're not already
    I_sol = np.asarray(I_sol)
    I_direct = np.asarray(I_direct)
    I_diffuse = np.asarray(I_diffuse)
    tilt = np.asarray(tilt)
    Sz = np.asarray(Sz)
    teta = np.asarray(teta)
    
    # read variables
    n = constants.n  # refractive index of glass
    Pg = constants.Pg  # ground reflectance
    K = constants.K  # glazing extinction coefficient
    a0 = panel_properties_PV['PV_a0']
    a1 = panel_properties_PV['PV_a1']
    a2 = panel_properties_PV['PV_a2']
    a3 = panel_properties_PV['PV_a3']
    a4 = panel_properties_PV['PV_a4']
    L = panel_properties_PV['PV_th']

    # calculate ratio of beam radiation on a tilted plane to avoid inconvergence when I_sol = 0
    lim1 = np.radians(0)
    lim2 = np.radians(90)
    lim3 = np.radians(89.999)

    # Handle bounds for teta and Sz
    teta = np.where(teta < lim1, np.minimum(lim3, np.abs(teta)), teta)
    teta = np.where(teta >= lim2, lim3, teta)
    
    Sz = np.where(Sz < lim1, np.minimum(lim3, np.abs(Sz)), Sz)
    Sz = np.where(Sz >= lim2, lim3, Sz)

    # Rb: ratio of beam radiation of tilted surface to that on horizontal surface
    Rb = np.where(Sz <= radians(85),
                  np.cos(teta) / np.cos(Sz),
                  0)  # Assume there is no direct radiation when the sun is close to the horizon.

    # calculate air mass modifier
    m = calc_air_mass(Sz, latitude, longitude)
    M = a0 + a1 * m + a2 * m ** 2 + a3 * m ** 3 + a4 * m ** 4  # air mass modifier
    M = np.clip(M, 0.001, 1.1)  # De Soto et al., 2006

    # transmittance-absorptance product at normal incidence
    Ta_n = np.exp(-K * L) * (1 - ((n - 1) / (n + 1)) ** 2)

    # incidence angle modifier for direct (beam) radiation
    teta_r = np.arcsin(np.sin(teta) / n)  # refraction angle in radians
    
    # Calculate beam radiation component
    kteta_B = np.zeros_like(teta)
    mask_below_90 = teta < radians(90)
    
    if np.any(mask_below_90):
        part1 = teta_r + teta
        part2 = teta_r - teta
        Ta_B = np.exp((-K * L) / np.cos(teta_r)) * (
                1 - 0.5 * ((np.sin(part2) ** 2) / (np.sin(part1) ** 2) + 
                           (np.tan(part2) ** 2) / (np.tan(part1) ** 2)))
        kteta_B = np.where(mask_below_90, Ta_B / Ta_n, 0)

    # incidence angle modifier for diffuse radiation
    teta_r_d = np.arcsin(np.sin(tetaed) / n)  # refraction angle for diffuse radiation
    part1_d = teta_r_d + tetaed
    part2_d = teta_r_d - tetaed
    Ta_D = np.exp((-K * L) / np.cos(teta_r_d)) * (
            1 - 0.5 * ((np.sin(part2_d) ** 2) / (np.sin(part1_d) ** 2) + 
                       (np.tan(part2_d) ** 2) / (np.tan(part1_d) ** 2)))
    kteta_D = Ta_D / Ta_n

    # incidence angle modifier for ground-reflected radiation
    teta_r_g = np.arcsin(np.sin(tetaeg) / n)  # refraction angle for ground-reflected radiation
    part1_g = teta_r_g + tetaeg
    part2_g = teta_r_g - tetaeg
    Ta_eG = np.exp((-K * L) / np.cos(teta_r_g)) * (
            1 - 0.5 * ((np.sin(part2_g) ** 2) / (np.sin(part1_g) ** 2) + 
                       (np.tan(part2_g) ** 2) / (np.tan(part1_g) ** 2)))
    kteta_eG = Ta_eG / Ta_n

    # absorbed solar radiation
    absorbed_radiation_Wperm2 = M * Ta_n * (
            kteta_B * I_direct * Rb + 
            kteta_D * I_diffuse * (1 + np.cos(tilt)) / 2 + 
            kteta_eG * (I_sol * Pg) * (1 - np.cos(tilt)) / 2)  # [W/m2] (5.12.1)
    
    # ensure no negative values
    absorbed_radiation_Wperm2 = np.maximum(absorbed_radiation_Wperm2, 0.0)

    # Return scalar if input was scalar
    if np.size(absorbed_radiation_Wperm2) == 1:
        return float(absorbed_radiation_Wperm2)
    return absorbed_radiation_Wperm2


def calc_air_mass(Sz, latitude, longitude):
    '''
    Calculate air mass according to Duffie & Beckmann, p. 10.
    For zenith angles from 0° to 70°, the air mass is calculated based on Equation 1.5.1.
    For zenith angles above that, the empirical equation in footnote 3 (taken from Kasten & Young, 1989) is used.

    :param Sz: solar zenith angle [rad]
    :type Sz: float or numpy.ndarray
    :param latitude: latitude of the location [degrees]
    :type latitude: float
    :param longitude: longitude of the location [degrees]
    :type longitude: float
    :return: air mass [-]
    :rtype: float or numpy.ndarray
    
    :References: Duffie, J. A. and Beckman, W. A. (2013) Radiation Transmission through Glazing: Absorbed Radiation, in
                 Solar Engineering of Thermal Processes, Fourth Edition, John Wiley & Sons, Inc., Hoboken, NJ, USA.
                 doi: 10.1002/9781118671603.ch5
    '''
    # Convert inputs to numpy arrays if they're not already
    Sz = np.asarray(Sz)
    
    h = pvlib.location.lookup_altitude(latitude, longitude)  # altitude (in m)
    
    # Apply the appropriate formula based on solar zenith angle
    m = np.where(np.abs(Sz) <= np.radians(70),
                1 / np.cos(Sz),  # air mass (1.5.1)
                np.exp(-0.0001184 * h) / (np.cos(Sz) + 0.5057 * (96.080 - np.degrees(Sz))**(-1.634)))  # air mass (footnote 3)
    
    # Return scalar if input was scalar
    if np.size(m) == 1:
        return float(m)
    return m

def calc_PV_power(absorbed_radiation_Wperm2, T_cell_C, eff_nom, tot_module_area_m2, Bref_perC, misc_losses):
    """
    To calculate the power production of PV panels.

    :param absorbed_radiation_Wperm2: absorbed radiation [W/m2]
    :type absorbed_radiation_Wperm2: float or numpy.ndarray
    :param T_cell_C: cell temperature [degree]
    :type T_cell_C: float or numpy.ndarray
    :param eff_nom: nominal efficiency of PV module [-]
    :type eff_nom: float
    :param tot_module_area_m2: total PV module area [m2]
    :type tot_module_area_m2: float
    :param Bref_perC: cell maximum power temperature coefficient [degree C^(-1)]
    :type Bref_perC: float
    :param misc_losses: expected system loss [-]
    :type misc_losses: float
    :return el_output_PV_kW: Power production [kW]
    :rtype el_output_PV_kW: float or numpy.ndarray

    ..[Osterwald, C. R., 1986] Osterwald, C. R. (1986). Translation of device performance measurements to
    reference conditions. Solar Cells, 18, 269-279.
    """
    # Convert inputs to numpy arrays if they're not already
    absorbed_radiation_Wperm2 = np.asarray(absorbed_radiation_Wperm2)
    T_cell_C = np.asarray(T_cell_C)
    
    T_standard_C = 25.0  # temperature at the standard testing condition
    el_output_PV_kW = eff_nom * tot_module_area_m2 * absorbed_radiation_Wperm2 * \
                     (1 - Bref_perC * (T_cell_C - T_standard_C)) * (1 - misc_losses) / 1000
    
    # Return scalar if input was scalar
    if np.size(el_output_PV_kW) == 1:
        return float(el_output_PV_kW)
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
        1) Tilt angle: If the sensor is on tilted roof, the panel will have the same tilt as the roof. If the sensor is
            on a wall, the tilt angle is 90 degree. Tilt angles for flat roof is determined using the method
            from Quinn et al.
        2) Row spacing: Determine the row spacing by minimizing the shadow according to the solar elevation and azimuth
            at the worst hour of the year. The worst hour is a global variable defined by users.
        3) Surface azimuth (orientation) of panels: If the sensor is on a tilted roof, the orientation of the panel is
            the same as the roof. Sensors on flat roofs are all south facing.

    """
    # calculate panel tilt angle (B) for flat roofs (tilt < 5 degrees), slope roofs and walls.
    optimal_angle_flat = solar_equations.calc_optimal_angle(0, latitude, transmissivity)
        # assume panels face the equator (the results for surface azimuth = 0 or 180 are the same)
    sensors_metadata_clean['tilt'] = np.vectorize(acos)(sensors_metadata_clean['Zdir'])  # surface tilt angle in rad
    sensors_metadata_clean['tilt'] = np.vectorize(degrees)(
        sensors_metadata_clean['tilt'])  # surface tilt angle in degrees
    sensors_metadata_clean['B'] = np.where(sensors_metadata_clean['tilt'] >= 5, sensors_metadata_clean['tilt'],
                                           degrees(optimal_angle_flat))  # panel tilt angle in degrees

    # calculate spacing and surface azimuth of the panels for flat roofs

    optimal_spacing_flat = calc_optimal_spacing(worst_sh, worst_Az, optimal_angle_flat, module_length)
    sensors_metadata_clean['array_s'] = np.where(sensors_metadata_clean['tilt'] >= 5, 0, optimal_spacing_flat)
    sensors_metadata_clean['surface_azimuth'] = np.vectorize(solar_equations.calc_surface_azimuth)(
        sensors_metadata_clean['Xdir'], sensors_metadata_clean['Ydir'], sensors_metadata_clean['B'])  # degrees

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



# ============================
# properties of module
# ============================
# TODO: Delete when done


def get_properties_PV_db(database_path, type_PVpanel):
    """
    To assign PV module properties according to panel types.

    :param type_PVpanel: type of PV panel used
    :type type_PVpanel: string
    :return: dict with Properties of the panel taken form the database
    """
    data = pd.read_csv(database_path)
    panel_properties = data[data['code'] == type_PVpanel].reset_index().T.to_dict()[0]

    return panel_properties


# investment and maintenance costs
# FIXME: it looks like this function is never used!!! (REMOVE)
def calc_Cinv_pv(total_module_area_m2, locator, technology=0):
    """
    To calculate capital cost of PV modules, assuming 20 year system lifetime.
    :param P_peak: installed capacity of PV module [kW]
    :return InvCa: capital cost of the installed PV module [CHF/Y]
    """
    PV_cost_data = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv('PHOTOVOLTAIC_PANELS'))
    technology_code = list(set(PV_cost_data['code']))
    PV_cost_data = PV_cost_data[PV_cost_data['code'] == technology_code[technology]]
    nominal_efficiency = PV_cost_data[PV_cost_data['code'] == technology_code[technology]]['PV_n'].max()
    P_nominal_W = total_module_area_m2 * (constants.STC_RADIATION_Wperm2 * nominal_efficiency)
    # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
    # capacity for the corresponding technology from the database
    if P_nominal_W < PV_cost_data['cap_min'].values[0]:
        P_nominal_W = PV_cost_data['cap_min'].values[0]
    PV_cost_data = PV_cost_data[
        (PV_cost_data['cap_min'] <= P_nominal_W) & (PV_cost_data['cap_max'] > P_nominal_W)]
    Inv_a = PV_cost_data.iloc[0]['a']
    Inv_b = PV_cost_data.iloc[0]['b']
    Inv_c = PV_cost_data.iloc[0]['c']
    Inv_d = PV_cost_data.iloc[0]['d']
    Inv_e = PV_cost_data.iloc[0]['e']
    Inv_IR = PV_cost_data.iloc[0]['IR_%']
    Inv_LT = PV_cost_data.iloc[0]['LT_yr']
    Inv_OM = PV_cost_data.iloc[0]['O&M_%'] / 100

    InvC = Inv_a + Inv_b * (P_nominal_W) ** Inv_c + (Inv_d + Inv_e * P_nominal_W) * log(P_nominal_W)

    Capex_a_PV_USD = calc_capex_annualized(InvC, Inv_IR, Inv_LT)
    Opex_fixed_PV_USD = InvC * Inv_OM
    Capex_PV_USD = InvC

    return Capex_a_PV_USD, Opex_fixed_PV_USD, Capex_PV_USD, P_nominal_W


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
        number_of_installations = int(ceil(E_nom / P_installed_in_kW[-1]))
        E_nom_per_chiller = E_nom / number_of_installations
        for i in range(number_of_installations):
            KEV_obtained_in_RpPerkWh = KEV_obtained_in_RpPerkWh + KEV_interpolated_kW(E_nom_per_chiller / 1000.0)
    else:
        KEV_obtained_in_RpPerkWh = KEV_obtained_in_RpPerkWh + KEV_interpolated_kW(E_nom / 1000.0)
    return KEV_obtained_in_RpPerkWh


def aggregate_results(locator, type_PVpanel, building_names):
    aggregated_hourly_results_df = pd.DataFrame()
    aggregated_annual_results = pd.DataFrame()

    for i, building in enumerate(building_names):
        hourly_results_per_building = pd.read_csv(locator.PV_results(building, type_PVpanel)).set_index('date')
        if i == 0:
            aggregated_hourly_results_df = hourly_results_per_building
        else:
            aggregated_hourly_results_df += hourly_results_per_building

        annual_energy_production = hourly_results_per_building.filter(like='_kWh').sum()
        panel_area_per_building = hourly_results_per_building.filter(like='_m2').iloc[0]
        building_annual_results = pd.concat([annual_energy_production, panel_area_per_building])
        aggregated_annual_results[building] = building_annual_results

    return aggregated_hourly_results_df, aggregated_annual_results


def aggregate_results_func(args):
    return aggregate_results(args[0], args[1], args[2])


def write_aggregate_results(locator, type_PVpanel, building_names):
    aggregated_hourly_results_df = pd.DataFrame()
    aggregated_annual_results = pd.DataFrame()

    num_process = 4
    with Pool(processes=num_process) as pool:
        args = [(locator, type_PVpanel, x) for x in np.array_split(building_names, num_process) if x.size != 0]
        for i, x in enumerate(pool.map(aggregate_results_func, args)):
            hourly_results_df, annual_results = x
            if i == 0:
                aggregated_hourly_results_df = hourly_results_df
                aggregated_annual_results = annual_results
            else:
                aggregated_hourly_results_df = aggregated_hourly_results_df + hourly_results_df
                aggregated_annual_results = pd.concat([aggregated_annual_results, annual_results], axis=1, sort=False)

    # save hourly results
    locator.ensure_parent_folder_exists(locator.PV_totals(panel_type=type_PVpanel))
    aggregated_hourly_results_df.to_csv(locator.PV_totals(panel_type=type_PVpanel), index=True, float_format='%.2f', na_rep='nan')
    # save annual results
    aggregated_annual_results_df = pd.DataFrame(aggregated_annual_results).T
    locator.ensure_parent_folder_exists(locator.PV_total_buildings(type_PVpanel))
    aggregated_annual_results_df.to_csv(locator.PV_total_buildings(type_PVpanel), index=True, index_label="name",
                                        float_format='%.2f', na_rep='nan')


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    list_types_PVpanel = config.solar.type_PVpanel

    print('Running photovoltaic with scenario = %s' % config.scenario)
    print('Running photovoltaic with annual-radiation-threshold-kWh/m2 = %s' % config.solar.annual_radiation_threshold)
    print('Running photovoltaic with panel-on-roof = %s' % config.solar.panel_on_roof)
    print('Running photovoltaic with panel-on-wall = %s' % config.solar.panel_on_wall)
    print('Running photovoltaic with solar-window-solstice = %s' % config.solar.solar_window_solstice)
    # print('Running photovoltaic with type-PVpanel = {types_PVpanel}'.format(types_PVpanel=', '.join(map(str, list_types_PVpanel))))
    if config.solar.custom_tilt_angle:
        print('Running photovoltaic with custom-tilt-angle = %s and panel-tilt-angle = %s' %
              (config.solar.custom_tilt_angle, config.solar.panel_tilt_angle))
    else:
        print('Running photovoltaic with custom-tilt-angle = %s' % config.solar.custom_tilt_angle)
    print('Running photovoltaic with maximum roof-coverage = %s' % config.solar.max_roof_coverage)

    # building_names = locator.get_zone_building_names()
    building_names = config.solar.buildings
    zone_geometry_df = gdf.from_file(locator.get_zone_geometry())
    latitude, longitude = get_lat_lon_projected_shapefile(zone_geometry_df)
    weather_data = epwreader.epw_reader(locator.get_weather_file())
    date_local = solar_equations.calc_datetime_local_from_weather_file(weather_data, latitude, longitude)

    num_process = config.get_number_of_processes()
    n = len(building_names)

    for type_PVpanel in list_types_PVpanel:
        print('Running photovoltaic with type-PVpanel = %s' % type_PVpanel)
        cea.utilities.parallel.vectorize(calc_PV, num_process)(repeat(locator, n),
                                                               repeat(config, n),
                                                               repeat(type_PVpanel, n),
                                                               repeat(latitude, n),
                                                               repeat(longitude, n),
                                                               repeat(weather_data, n),
                                                               repeat(date_local, n),
                                                               building_names)
        # aggregate results from all buildings
        write_aggregate_results(locator, type_PVpanel,building_names)


if __name__ == '__main__':
    main(cea.config.Configuration())

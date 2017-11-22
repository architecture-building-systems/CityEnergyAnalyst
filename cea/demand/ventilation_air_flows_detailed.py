# -*- coding: utf-8 -*-
"""
Ventilation according to [DIN-16798-7]_ and [ISO-9972]_

.. [DIN-16798-7]  Energieeffizienz von Gebäuden - Teil 7: Modul M5-1, M 5-5, M 5-6, M 5-8 –
    Berechnungsmethoden zur Bestimmung der Luftvolumenströme in Gebäuden inklusive Infiltration;
    Deutsche Fassung prEN 16798-7:2014


.. [ISO-9972] Wärmetechnisches Verhalten von Gebäuden –
    Bestimmung der Luftdurchlässigkeit von Gebäuden –
    Differenzdruckverfahren (ISO 9972:2015);
    Deutsche Fassung EN ISO 9972:2015

Convention: all temperature inputs in (°C)
"""

from __future__ import division

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from cea.geometry.geometry_reader import get_building_geometry_ventilation
from cea.utilities.physics import calc_rho_air

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# ventilation calculation


def calc_air_flows(temp_zone, u_wind, temp_ext, dict_props_nat_vent):
    """
    Minimization of variable air flows as a function of zone gauge

    :param temp_zone: zone indoor air temperature (°C)
    :param u_wind: wind velocity (m/s)
    :param temp_ext: exterior air temperature (°C)
    :param dict_props_nat_vent: dictionary containing natural ventilation properties of zone

    qm_sum_in : total air mass flow rates into zone (kg/h)
    qm_sum_out : total air mass flow rates out of zone (kg/h)
    """

    # Different solver options to try:
    # --------------------------------
    # solver_options_nelder_mead ={'disp': False, 'maxiter': 100, 'maxfev': None, 'xtol': 0.1, 'ftol': 0.1}
    # solver_options_cg ={'disp': False, 'gtol': 1e-05, 'eps': 1.4901161193847656e-08, 'return_all': False,
    #                     'maxiter': None, 'norm': -np.inf}
    # solver_options_powell = {'disp': True, 'maxiter': None, 'direc': None, 'maxfev': None,
    #            'xtol': 0.0001, 'ftol': 0.0001}
    # solver_options_tnc = {'disp': True, 'minfev': 0, 'scale': None, 'rescale': -1, 'offset': None, 'gtol': -1,
    #                       'eps': 1e-08, 'eta': -1, 'maxiter': None, 'maxCGit': -1, 'mesg_num': None,
    #                       'ftol': -1, 'xtol': -1, 'stepmx': 0, 'accuracy': 0}
    solver_options_cobyla = {'iprint': 1, 'disp': False, 'maxiter': 100, 'rhobeg': 1.0, 'tol': 0.001}

    # solve air flow mass balance via iteration
    p_zone_ref = 1  # (Pa) zone pressure, THE UNKNOWN VALUE
    res = minimize(calc_air_flow_mass_balance, p_zone_ref,
                   args=(temp_zone, u_wind, temp_ext, dict_props_nat_vent, 'minimize',),
                   method='COBYLA',
                   options=solver_options_cobyla)
    # print(res)
    # get zone pressure of air flow mass balance
    p_zone = res.x

    # calculate air flows at zone pressure
    qm_sum_in, qm_sum_out = calc_air_flow_mass_balance(p_zone, temp_zone, u_wind,
                                                       temp_ext, dict_props_nat_vent, 'calculate')

    return qm_sum_in, qm_sum_out


def get_properties_natural_ventilation(bpr, gv):
    """
    gdf_geometry_building : GeoDataFrame containing geometry properties of single building
    gdf_architecture_building : GeoDataFrame containing architecture props of single building
    :param gv: globalvars
    :param bpr: building propert row

    :returns: dictionary containing natural ventilation properties of zone
    """

    n50 = bpr.architecture.n50
    vol_building = bpr.geometry['footprint'] * bpr.geometry['height_ag']
    qv_delta_p_lea_ref_zone = calc_qv_delta_p_ref(n50, vol_building)
    area_facade_zone,\
    area_roof_zone,\
    height_zone,\
    slope_roof = get_building_geometry_ventilation(bpr.geometry)
    class_shielding = gv.shielding_class
#    factor_cros = bpr.architecture.f_cros
    factor_cros = 0  # TODO write dict function to look up, ZERO is for office and industrial functions
    area_vent_zone = 0  # (cm2) area of ventilation openings # TODO: get from buildings properties

    # calculate properties that remain constant in the minimization
    # (a) LEAKAGES
    coeff_lea_path,\
    height_lea_path,\
    orientation_lea_path = allocate_default_leakage_paths(calc_coeff_lea_zone(qv_delta_p_lea_ref_zone),
                                                          area_facade_zone, area_roof_zone, height_zone)

    coeff_wind_pressure_path_lea = lookup_coeff_wind_pressure(height_lea_path, class_shielding, orientation_lea_path,
                                                              slope_roof, factor_cros)

    # (b) VENTILATION OPENINGS
    coeff_vent_path,\
    height_vent_path,\
    orientation_vent_path = allocate_default_ventilation_openings(calc_coeff_vent_zone(area_vent_zone), height_zone)
    coeff_wind_pressure_path_vent = lookup_coeff_wind_pressure(height_vent_path, class_shielding, orientation_vent_path,
                                                               slope_roof, factor_cros)

    # make dict for output
    dict_props_nat_vent = {'coeff_lea_path': coeff_lea_path,
                           'height_lea_path': height_lea_path,
                           'coeff_wind_pressure_path_lea': coeff_wind_pressure_path_lea,
                           'coeff_vent_path': coeff_vent_path,
                           'height_vent_path': height_vent_path,
                           'coeff_wind_pressure_path_vent': coeff_wind_pressure_path_vent,
                           'factor_cros': factor_cros}

    return dict_props_nat_vent


# Wind pressure calculation

def calc_u_wind_site(u_wind_10):
    """
    Adjusts meteorological wind velocity to site surroundings according to 6.4.2.2 in [1]

    :param u_wind_10: meteorological wind velocity (m/s)

    :returns: u_wind_site, site wind velocity (m/s)
    """

    # terrain class of surroundings
    # 0 = open
    # 1 = rural
    # 2 = urban
    ter_class = 2  # TODO: move to globalvars

    # factors from Table B.11 in B.1.4.1 in [1]
    f_wnd = np.array([1.0, 0.9, 0.8])

    # Equation (2) in [1]
    return f_wnd[ter_class] * u_wind_10


def lookup_coeff_wind_pressure(height_path, class_shielding, orientation_path, slope_roof, factor_cros):
    """
    Lookup default wind pressure coefficients for air leakage paths according to B.1.3.3 in [1]

    :param height_path:
    :param class_shielding:
    :param orientation_path:
    :param slope_roof:
    :param factor_cros:

    :returns: wind pressure coefficients (-)

    Conventions:

    class_shielding = 0 : open terrain
    class_shielding = 1 : normal
    class_shielding = 2 : shielded

    orientation_path = 0 : facade facing wind
                       1 : facade not facing wind
                       2 : roof

    factor_cros = 0 : cross ventilation not possible
                = 1 : cross ventilation possible

    """

    # Table B.5 in [1]
    table_coeff_wind_pressure_cross_ventilation = np.array([[0.5, -0.7, -0.7, -0.6, -0.2],
                                                            [0.25, -0.5, -0.6, -0.5, -0.2],
                                                            [0.05, -0.3, -0.5, -0.4, -0.2],
                                                            [0.65, -0.7, -0.7, -0.6, -0.2],
                                                            [0.45, -0.5, -0.6, -0.5, -0.2],
                                                            [0.25, -0.3, -0.5, -0.4, -0.2],
                                                            [0.8, -0.7, -0.7, -0.6, -0.2]])

    # Table B.6 in [1]
    table_coeff_wind_pressure_non_cross_ventilation = np.array([0.05, -0.05, 0])

    num_paths = height_path.shape[0]
    coeff_wind_pressure = np.zeros(num_paths)

    for i in range(0, num_paths):

        if factor_cros == 1:

            if 0 <= height_path[i] < 15:
                index_row = 0
            elif 15 <= height_path[i] < 50:
                index_row = 3
            elif height_path[i] >= 50:
                index_row = 6
            else:
                #  default
                index_row = 6
                print('Warning: unsupported height')
                print(height_path[i])

            index_row = min(index_row + class_shielding, 6)

            if orientation_path[i] == 2:
                if 0 <= slope_roof < 10:
                    index_col = 0
                elif 10 <= slope_roof <= 30:
                    index_col = 1
                elif slope_roof > 30:
                    index_col = 2
                else:
                    # default
                    index_col = 0
                    print('Warning: unsupported roof slope')
                    print(slope_roof)

                index_col = index_col + orientation_path[i]

            elif orientation_path[i] == 0 or orientation_path[i] == 1:
                index_col = orientation_path[i]

            else:
                # default
                index_col = orientation_path[i]
                print('Warning: unsupported orientation')
                print(orientation_path[i])

            coeff_wind_pressure[i] = table_coeff_wind_pressure_cross_ventilation[index_row, index_col]

        elif factor_cros == 0:
            index_col = orientation_path[i]

            coeff_wind_pressure[i] = table_coeff_wind_pressure_non_cross_ventilation[index_col]

    return coeff_wind_pressure


def calc_delta_p_path(p_zone_ref, height_path, temp_zone, coeff_wind_pressure_path, u_wind_site, temp_ext):
    """
    Calculation of indoor-outdoor pressure difference at air path according to 6.4.2.4 in [1]

    :param p_zone_ref: zone reference pressure (Pa)
    :param height_path: height of ventilation path (m)
    :param temp_zone: air temperature of ventilation zone in (°C)
    :param coeff_wind_pressure_path: wind pressure coefficient of ventilation path (-)
    :param u_wind_site: wind velocity (m/s)
    :param temp_ext: external air temperature (°C)

    :returns: ``delta_p_path``, pressure difference across ventilation path (Pa)
    """

    # constants from Table 12 in [1]
    # TODO import from global variables
    g = 9.81  # (m/s2)
    rho_air_ref = 1.23  # (kg/m3)
    temp_ext_ref = 283  # (K)

    temp_zone += 273  # conversion to (K)
    temp_ext += 273  # conversion to (K)

    # Equation (5) in [1]
    p_zone_path = p_zone_ref - rho_air_ref * height_path * g * temp_ext_ref / temp_zone

    # Equation (4) in [1]
    p_ext_path = rho_air_ref * (
        0.5 * coeff_wind_pressure_path * u_wind_site ** 2 - height_path * g * temp_ext_ref / temp_ext)

    # Equation (3) in [1]
    delta_p_path = p_ext_path - p_zone_path

    return delta_p_path


# leakages through the envelope

def calc_qv_delta_p_ref(n_delta_p_ref, vol_building):
    """
    Calculate airflow at reference pressure according to 6.3.2 in [2]

    :param n_delta_p_ref: air changes at reference pressure [1/h]
    :param vol_building: building_volume [m3]

    :returns: qv_delta_p_ref : air volume flow rate at reference pressure (m3/h)
    """

    # Eq. (9) in [2]
    return n_delta_p_ref * vol_building


def calc_qv_lea_path(coeff_lea_path, delta_p_lea_path):
    """
    Calculate volume air flow of single leakage path according to 6.4.3.6.5 in [1]

    :param coeff_lea_path: coefficient of leakage path
    :param delta_p_lea_path: pressure difference across leakage path (Pa)

    :returns: qv_lea_path : volume flow rate across leakage path (m3/h)
    """
    # default values in [1]
    # TODO reference global variables
    n_lea = 0.667  # (-), B.1.3.15 in [1]

    # Equation (64) in [1]
    qv_lea_path = coeff_lea_path * np.sign(delta_p_lea_path) * np.abs(delta_p_lea_path) ** n_lea
    return qv_lea_path


def calc_coeff_lea_zone(qv_delta_p_lea_ref):
    """
    Calculate default leakage coefficient of zone according to B.1.3.16 in [1]

    :param qv_delta_p_lea_ref: air volume flow rate at reference pressure (m3/h)

    :returns: coeff_lea_zone : leakage coefficient of zone
    """
    # default values in [1]
    # TODO reference global variables
    delta_p_lea_ref = 50  # (Pa), B.1.3.14 in [1]
    n_lea = 0.667  # (-), B.1.3.15 in [1]

    # Eq. (B.5) in [1] # TODO: Formula assumed to be wrong in [1], corrected to match Eq. (8) in [2]
    coeff_lea_zone = qv_delta_p_lea_ref / (delta_p_lea_ref ** n_lea)

    return coeff_lea_zone


def allocate_default_leakage_paths(coeff_lea_zone, area_facade_zone, area_roof_zone, height_zone):
    """
    Allocate default leakage paths according to B.1.3.17 in [1]

    :param coeff_lea_zone: leakage coefficient of zone
    :param area_facade_zone: facade area of zone (m2)
    :param area_roof_zone: roof area of zone (m2)
    :param height_zone: height of zone (m)

    :returns: - coeff_lea_path : coefficients of default leakage paths
              - height_lea_path : heights of default leakage paths (m)
              - orientation_lea_path : orientation index of default leakage paths (-)
    """

    # Equation (B.6) in [1]
    coeff_lea_facade = coeff_lea_zone * area_facade_zone / (area_facade_zone + area_roof_zone)
    # Equation (B.7) in [1]
    coeff_lea_roof = coeff_lea_zone * area_roof_zone / (area_facade_zone + area_roof_zone)

    coeff_lea_path = np.zeros(5)
    height_lea_path = np.zeros(5)
    orientation_lea_path = [0, 1, 0, 1, 2]

    # Table B.10 in [1]
    # default leakage path 1
    coeff_lea_path[0] = 0.25 * coeff_lea_facade
    height_lea_path[0] = 0.25 * height_zone
    orientation_lea_path[0] = 0  # facade facing the wind

    # default leakage path 2
    coeff_lea_path[1] = 0.25 * coeff_lea_facade
    height_lea_path[1] = 0.25 * height_zone
    orientation_lea_path[1] = 1  # facade not facing the wind

    # default leakage path 3
    coeff_lea_path[2] = 0.25 * coeff_lea_facade
    height_lea_path[2] = 0.75 * height_zone
    orientation_lea_path[2] = 0  # facade facing the wind

    # default leakage path 4
    coeff_lea_path[3] = 0.25 * coeff_lea_facade
    height_lea_path[3] = 0.75 * height_zone
    orientation_lea_path[3] = 1  # facade not facing the wind

    # default leakage path 5
    coeff_lea_path[4] = coeff_lea_roof
    height_lea_path[4] = height_zone
    orientation_lea_path[4] = 2  # roof

    return coeff_lea_path, height_lea_path, orientation_lea_path


def calc_qm_lea(p_zone_ref, temp_zone, temp_ext, u_wind_site, dict_props_nat_vent):
    """
    Calculation of leakage infiltration and exfiltration air mass flow as a function of zone indoor reference pressure

    :param p_zone_ref: zone reference pressure (Pa)
    :param temp_zone: air temperature in ventilation zone (°C)
    :param temp_ext: exterior air temperature (°C)
    :param u_wind_site: wind velocity (m/s)
    :param dict_props_nat_vent: dictionary containing natural ventilation properties of zone

    :returns: - qm_lea_in : air mass flow rate into zone through leakages (kg/h)
              - qm_lea_out : air mass flow rate out of zone through leakages (kg/h)
    """

    # get default leakage paths from locals
    coeff_lea_path = dict_props_nat_vent['coeff_lea_path']
    height_lea_path = dict_props_nat_vent['height_lea_path']

    # lookup wind pressure coefficients for leakage paths from locals
    coeff_wind_pressure_path = dict_props_nat_vent['coeff_wind_pressure_path_lea']

    # calculation of pressure difference at leakage path
    delta_p_path = calc_delta_p_path(p_zone_ref, height_lea_path, temp_zone, coeff_wind_pressure_path, u_wind_site,
                                     temp_ext)

    # calculation of leakage air volume flow at path
    qv_lea_path = calc_qv_lea_path(coeff_lea_path, delta_p_path)

    # Eq. (65) in [1], infiltration is sum of air flows greater zero
    qv_lea_in = qv_lea_path[np.where(qv_lea_path > 0)].sum()

    # Eq. (66) in [1], exfiltration is sum of air flows smaller zero
    qv_lea_out = qv_lea_path[np.where(qv_lea_path < 0)].sum()

    # conversion to air mass flows according to 6.4.3.8 in [1]
    # Eq. (67) in [1]
    qm_lea_in = qv_lea_in * calc_rho_air(temp_ext)
    # Eq. (68) in [1]
    qm_lea_out = qv_lea_out * calc_rho_air(temp_zone)

    # print (qm_lea_in, qm_lea_out)

    return qm_lea_in, qm_lea_out


# operation of window openings

def calc_qv_vent_path(coeff_vent_path, delta_p_vent_path):
    """
    Calculate volume air flow of single ventilation opening path according to 6.4.3.6.4 in [1]

    :param coeff_vent_path : ventilation opening coefficient of air path
    :param delta_p_vent_path : pressure difference across air path (Pa)

    :returns: qv_vent_path : air volume flow rate across air path (m3/h)
    """
    # default values in [1]
    # TODO reference global variables
    n_vent = 0.5  # (-), B.1.2.2 in [1]

    # Equation (60) in [1]
    qv_vent_path = coeff_vent_path * np.sign(delta_p_vent_path) * np.abs(delta_p_vent_path) ** n_vent
    return qv_vent_path


def calc_coeff_vent_zone(area_vent_zone):
    """
    Calculate air volume flow coefficient of ventilation openings of zone according to 6.4.3.6.4 in [1]

    :param area_vent_zone : total area of ventilation openings of zone (cm2)

    :returns coeff_vent_zone : coefficient of ventilation openings of zone
    """

    # default values in [1]
    # TODO reference global variables
    n_vent = 0.5  # (-), B.1.2.2 in [1]
    coeff_d_vent = 0.6  # (-), B.1.2.1 in [1]
    delta_p_vent_ref = 50  # (Pa) FIXME no default value specified in standard
    # constants from Table 12 in [1]
    rho_air_ref = 1.23  # (kg/m3)

    # Eq. (61) in [1]
    coeff_vent_zone = 3600 / 10000 * coeff_d_vent * area_vent_zone * (2 / rho_air_ref) ** 0.5 * \
                      (1 / delta_p_vent_ref) ** (n_vent - 0.5)

    return coeff_vent_zone


def allocate_default_ventilation_openings(coeff_vent_zone, height_zone):
    """
    Allocate default ventilation openings according to B.1.3.13 in [1]

    :param coeff_vent_zone : coefficient of ventilation openings of zone
    :param height_zone : height of zone (m)

    :returns: - coeff_vent_path : coefficients of default ventilation opening paths
              - height_vent_path : heights of default ventilation opening paths (m)
              - orientation_vent_path : orientation index of default ventilation opening paths (-)
    """

    # initialize
    coeff_vent_path = np.zeros(4)
    height_vent_path = np.zeros(4)
    orientation_vent_path = [0, 1, 0, 1]

    # Table B.9 in [1]
    # default leakage path 1
    coeff_vent_path[0] = 0.25 * coeff_vent_zone
    height_vent_path[0] = 0.25 * height_zone
    orientation_vent_path[0] = 0  # facade facing the wind

    # default leakage path 2
    coeff_vent_path[1] = 0.25 * coeff_vent_zone
    height_vent_path[1] = 0.25 * height_zone
    orientation_vent_path[1] = 1  # facade not facing the wind

    # default leakage path 3
    coeff_vent_path[2] = 0.25 * coeff_vent_zone
    height_vent_path[2] = 0.75 * height_zone
    orientation_vent_path[2] = 0  # facade facing the wind

    # default leakage path 4
    coeff_vent_path[3] = 0.25 * coeff_vent_zone
    height_vent_path[3] = 0.75 * height_zone
    orientation_vent_path[3] = 1  # facade not facing the wind

    return coeff_vent_path, height_vent_path, orientation_vent_path


def calc_qm_vent(p_zone_ref, temp_zone, temp_ext, u_wind_site, dict_props_nat_vent):
    """
    Calculation of air flows through ventilation openings in the facade

    :param p_zone_ref : zone reference pressure (Pa)
    :param temp_zone : zone air temperature (°C)
    :param temp_ext : exterior air temperature (°C)
    :param u_wind_site : wind velocity (m/s)
    :param dict_props_nat_vent : dictionary containing natural ventilation properties of zone

    :returns: - qm_vent_in : air mass flow rate into zone through ventilation openings (kg/h)
              - qm_vent_out : air mass flow rate out of zone through ventilation openings (kg/h)
    """

    # get properties from locals()
    coeff_vent_path = dict_props_nat_vent['coeff_vent_path']
    height_vent_path = dict_props_nat_vent['height_vent_path']
    coeff_wind_pressure_path = dict_props_nat_vent['coeff_wind_pressure_path_vent']

    # calculation of pressure difference at leakage path
    delta_p_path = calc_delta_p_path(p_zone_ref, height_vent_path, temp_zone, coeff_wind_pressure_path, u_wind_site,
                                     temp_ext)

    # calculation of leakage air volume flow at path
    qv_vent_path = calc_qv_vent_path(coeff_vent_path, delta_p_path)

    # Eq. (62) in [1], air flow entering through ventilation openings is sum of air flows greater zero
    qv_vent_in = qv_vent_path[np.where(qv_vent_path > 0)].sum()

    # Eq. (63) in [1], air flow entering through ventilation openings is sum of air flows smaller zero
    qv_vent_out = qv_vent_path[np.where(qv_vent_path < 0)].sum()

    # conversion to air mass flows according to 6.4.3.8 in [1]
    # Eq. (67) in [1]
    qm_vent_in = qv_vent_in * calc_rho_air(temp_ext)
    # Eq. (68) in [1]
    qm_vent_out = qv_vent_out * calc_rho_air(temp_zone)

    # print (qm_lea_in, qm_lea_out)

    return qm_vent_in, qm_vent_out


# windows ventilation

def calc_area_window_free(area_window_max, r_window_arg):
    """
    Calculate free window opening area according to 6.4.3.5.2 in [1]

    :param area_window_max : area of single operable window (m2)
    :param r_window_arg : fraction of window opening (-)

    :returns: area_window_free : open area of window (m2)
    """
    # TODO: check final standard for area_window_max

    # default values
    # r_window_arg = 0.5  # (-), Tab 11 in [1]
    # TODO: this might be a dynamic parameter

    # Eq. (42) in [1]
    area_window_free = r_window_arg * area_window_max
    return area_window_free


def calc_area_window_tot(dict_windows_building, r_window_arg):
    """
    Calculation of total open window area according to 6.4.3.5.2 in [1]

    :param dict_windows_building : dictionary containing information of all windows in building
    :param r_window_arg : fraction of window opening (-)

    :returns: area_window_tot = total open area of windows in building (m2)
    """

    # Eq. (43) in [1]
    # TODO account only for operable windows and not total building window area
    area_window_tot = calc_area_window_free(sum(dict_windows_building['area_window']), r_window_arg)

    return area_window_tot


def calc_effective_stack_height(dict_windows_building):
    """
    Calculation of effective stack height for window ventilation according to 6.4.3.4.1 in [1]

    :param dict_windows_building : dictionary containing information of all windows in building

    :returns: height_window_stack : effective stack height of windows of building (m)
    """
    # TODO: maybe this formula is wrong --> check final edition of standard as soon as possible

    # first part of Eq. (46) in [1]
    height_window_stack_1 = dict_windows_building['height_window_in_zone'] + np.array(dict_windows_building[
                                                                                          'height_window_above_ground']) / 2
    # second part of Eq. (46) in [1]
    height_window_stack_2 = dict_windows_building['height_window_in_zone'] - np.array(dict_windows_building[
                                                                                          'height_window_above_ground']) / 2
    # Eq. (46) in [1]
    height_window_stack = max(height_window_stack_1) - min(height_window_stack_2)

    return height_window_stack


def calc_area_window_cros(dict_windows_building, r_window_arg):
    """
    Calculate cross-ventilation window area according to the procedure in 6.4.3.5.4.3 in [1]

    :param dict_windows_building : dictionary containing information of all windows in building
    :param r_window_arg : fraction of window opening (-)

    :returns: area_window_cros : effective window area for cross ventilation (m2)
    """

    # initialize results
    area_window_ori = np.zeros(4)
    area_window_cros = np.zeros(2)

    # area window tot
    area_window_tot = calc_area_window_tot(dict_windows_building, r_window_arg)

    for i in range(2):
        for j in range(4):

            # Eq. (51) in [1]
            alpha_ref = i * 45 + j * 90
            alpha_max = alpha_ref + 45
            alpha_min = alpha_ref - 45
            for k in range(len(dict_windows_building['name_building'])):
                if alpha_min <= dict_windows_building['orientation_window'][k] <= \
                        alpha_max and dict_windows_building['angle_window'][k] >= 60:
                    # Eq. (52) in [1]
                    area_window_free = calc_area_window_free(dict_windows_building['area_window'][k], r_window_arg)
                    area_window_ori[j] = area_window_ori[j] + area_window_free
        for j in range(4):
            if area_window_ori[j] > 0:
                # Eq. (53) in [1]
                area_window_cros[i] += 0.25 * 1 / (((1 / area_window_ori[j] ** 2) +
                                                    (1 / (area_window_tot - area_window_ori[j]) ** 2)) ** 0.5)

    # Eq. (54) in [1]
    return min(area_window_cros)


def calc_qm_arg(factor_cros, temp_ext, dict_windows_building, u_wind_10, temp_zone, r_window_arg):
    """
    Calculation of cross ventilated and non-cross ventilated window ventilation according to procedure in 6.4.3.5.4
    in [1]

    :param factor_cros : cross ventilation factor [0,1]
    :param temp_ext : exterior temperature (°C)
    :param dict_windows_building : dictionary containing information of all windows in building
    :param u_wind_10 : wind velocity (m/s)
    :param temp_zone : zone temperature (°C)
    :param r_window_arg : fraction of window opening (-)

    :returns: window ventilation air mass flows in (kg/h)
    """

    # initialize result
    q_v_arg_in = 0
    q_v_arg_out = 0
    qm_arg_in = qm_arg_out = 0  # this is the output for buildings without windows

    # if building has windows
    if dict_windows_building:

        # constants from Table 12 in [1]
        # TODO import from global variables
        rho_air_ref = 1.23  # (kg/m3)
        coeff_turb = 0.01  # (m/s)
        coeff_wind = 0.001  # (1/(m/s))
        coeff_stack = 0.0035  # ((m/s)/(mK))

        # default values from annex B in [1]
        coeff_d_window = 0.67  # (-), B.1.2.1 in [1]
        delta_c_p = 0.75  # (-), option 2 in B.1.3.4 in [1]

        # get necessary inputs
        rho_air_ext = calc_rho_air(temp_ext)
        rho_air_zone = calc_rho_air(temp_zone)
        area_window_tot = calc_area_window_tot(dict_windows_building, r_window_arg)
        h_window_stack = calc_effective_stack_height(dict_windows_building)
        # print(h_window_stack, area_window_tot)

        # volume flow rates of non-cross ventilated zone according to 6.4.3.5.4.2 in [1]
        if factor_cros == 0:

            # Eq. (47) in [1]
            # FIXME: this equation was modified from the version in the standard (possibly wrong in preliminary version)
            # TODO: check final edition of standard as soon as possible
            q_v_arg_in = 3600 * rho_air_ref / rho_air_ext * area_window_tot / 2 * (
                coeff_turb + coeff_wind * u_wind_10 ** 2 + coeff_stack * h_window_stack * abs(
                    temp_zone - temp_ext))  # ** 0.5
            # Eq. (48) in [1]
            q_v_arg_out = -3600 * rho_air_ref / rho_air_zone * area_window_tot / 2 * (
                coeff_turb + coeff_wind * u_wind_10 ** 2 + coeff_stack * h_window_stack * abs(
                    temp_zone - temp_ext))  # ** 0.5

            # print(coeff_turb + coeff_wind * u_wind_10 ** 2 + coeff_stack * h_window_stack * abs(temp_zone - temp_ext))

        elif factor_cros == 1:

            # get window area of cross-ventilation
            area_window_cros = calc_area_window_cros(dict_windows_building, r_window_arg)
            # print(area_window_cros)

            # Eq. (49) in [1]
            q_v_arg_in = 3600 * rho_air_ref / rho_air_ext * ((
                                                                 coeff_d_window * area_window_cros * u_wind_10 * delta_c_p ** 0.5) ** 2 + (
                                                                 area_window_tot / 2 * (
                                                                     coeff_stack * h_window_stack * abs(
                                                                         temp_zone - temp_ext))) ** 2) ** 0.5

            # Eq. (50) in [1]
            # TODO this formula was changed from the standard to use the air density in the zone
            # TODO adjusted from the standard to have consistent units
            # TODO check final edition of standard as soon as possible
            q_v_arg_out = -3600 * rho_air_ref / rho_air_zone * ((
                                                                    coeff_d_window * area_window_cros * u_wind_10 * delta_c_p ** 0.5) ** 2 + (
                                                                    area_window_tot / 2 * (
                                                                        coeff_stack * h_window_stack * abs(
                                                                            temp_zone - temp_ext))) ** 2) ** 0.5

        # conversion to air mass flows according to 6.4.3.8 in [1]
        # Eq. (67) in [1]
        qm_arg_in = q_v_arg_in * calc_rho_air(temp_ext)
        # Eq. (68) in [1]
        qm_arg_out = q_v_arg_out * calc_rho_air(temp_zone)

    return qm_arg_in, qm_arg_out


# mass balance

def calc_air_flow_mass_balance(p_zone_ref, temp_zone, u_wind_10, temp_ext, dict_props_nat_vent, option):
    """
    Air flow mass balance for iterative calculation according to 6.4.3.9 in [1]

    :param p_zone_ref : zone reference pressure (Pa)
    :param temp_zone : air temperature in ventilation zone (°C)
    :param u_wind_10 : meteorological wind velocity (m/s)
    :param temp_ext : exterior air temperature (°C)
    :param dict_props_nat_vent : dictionary containing natural ventilation properties of zone
    :param option : 'minimize' = returns sum of air mass flows, 'calculate' = returns air mass flows

    :returns: sum of air mass flows in and out of zone in (kg/h)
    """

    # adjust wind velocity
    u_wind_site = calc_u_wind_site(u_wind_10)

    qm_sup_dis = 0
    qm_eta_dis = 0
    qm_lea_sup_dis = 0
    qm_lea_eta_dis = 0
    qm_comb_in = 0
    qm_comb_out = 0
    qm_pdu_in = 0
    qm_pdu_out = 0

    qm_arg_in = 0  # removed to speed up code, as window ventilation is always balanced
    #  with the currently implemented method
    qm_arg_out = 0  #

    qm_vent_in, qm_vent_out = calc_qm_vent(p_zone_ref, temp_zone, temp_ext, u_wind_site, dict_props_nat_vent)
    qm_lea_in, qm_lea_out = calc_qm_lea(p_zone_ref, temp_zone, temp_ext, u_wind_site, dict_props_nat_vent)

    # print('iterate air flows')
    # print(qm_arg_in, qm_arg_out)
    # print(qm_vent_in, qm_vent_out)
    # print(qm_lea_in, qm_lea_out)

    # mass balance, Eq. (69) in [1]
    qm_balance = qm_sup_dis + qm_eta_dis + qm_lea_sup_dis + qm_lea_eta_dis + qm_comb_in + qm_comb_out + \
                 qm_pdu_in + qm_pdu_out + qm_arg_in + qm_arg_out + qm_vent_in + qm_vent_out + qm_lea_in + qm_lea_out
    qm_sum_in = qm_sup_dis + qm_lea_sup_dis + qm_comb_in + qm_pdu_in + qm_arg_in + qm_vent_in + qm_lea_in
    qm_sum_out = qm_eta_dis + qm_lea_eta_dis + qm_comb_out + qm_pdu_out + qm_arg_out + qm_vent_out + qm_lea_out

    # switch output according to selected option
    if option == 'minimize':
        return abs(qm_balance)  # for minimization the mass balance is the output
    elif option == 'calculate':
        return qm_sum_in, qm_sum_out  # for the calculation the total air mass flows are output


def testing():
    import geopandas
    import cea.globalvar
    gv = cea.globalvar.GlobalVariables()
    from cea import inputlocator
    import time
    import cea.geometry.geometry_reader

    # generate windows based on geometry of vertical surfaces in radiation file
    locator = inputlocator.InputLocator(scenario=r'C:\reference-case\baseline')

    surface_properties = pd.read_csv(locator.get_surface_properties())
    gdf_building_architecture = geopandas.GeoDataFrame.from_file(
        locator.get_building_architecture()).drop('geometry', axis=1).set_index('Name')
    prop_geometry = geopandas.GeoDataFrame.from_file(locator.get_zone_geometry())
    prop_geometry['footprint'] = prop_geometry.area
    prop_geometry['perimeter'] = prop_geometry.length
    prop_geometry = prop_geometry.drop('geometry', axis=1).set_index('Name')
    df_windows = cea.geometry.geometry_reader.simple_window_generator.create_windows(surface_properties, gdf_building_architecture)

    building_test = 'B153737'  # 'B154767' this building doesn't have windows
    # get building windows
    df_windows_building_test = df_windows.loc[df_windows['name_building'] == building_test].to_dict('list')
    # get building geometry
    gdf_building_test = prop_geometry.ix[building_test]
    gdf_building_architecture = gdf_building_architecture.ix[building_test]

    r_window_arg = 0.1
    temp_ext = 5
    temp_zone = 22
    u_wind = 0.5
    u_wind_10 = u_wind
    factor_cros = 1  # 1 = cross ventilation possible # TODO: get from building properties

    dict_props_nat_vent = get_properties_natural_ventilation(gdf_building_test, gdf_building_architecture, gv)
    qm_arg_in, qm_arg_out \
        = calc_qm_arg(factor_cros, temp_ext, df_windows_building_test, u_wind_10, temp_zone, r_window_arg)

    t0 = time.time()
    res = calc_air_flows(temp_zone, u_wind, temp_ext, dict_props_nat_vent)
    t1 = time.time()

    print(res)
    print(['time: ', t1 - t0])


if __name__ == '__main__':
    testing()

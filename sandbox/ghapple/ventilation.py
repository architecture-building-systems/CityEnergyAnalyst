# -*- coding: utf-8 -*-
"""
============================================
Ventilation according to DIN EN 16798-7:2015
============================================ 

Created on Tue Apr 12 18:04:04 2016

@author: happle@arch.ethz.ch

Reference:
[1] Energieeffizienz von Gebäuden - Teil 7: Modul M5-1, M 5-5, M 5-6, M 5-8 –
    Berechnungsmethoden zur Bestimmung der Luftvolumenströme in Gebäuden inklusive Infiltration;
    Deutsche Fassung prEN 16798-7:2014

"""

from __future__ import division
import numpy
import pandas
from scipy.optimize import minimize
from cea import inputlocator
import geopandas
from cea.functions import calc_HVAC
import cea.globalvar
gv = cea.globalvar.GlobalVariables()


# ++++ GEOMETRY ++++

# for now get geometric properties of exposed facades from the radiation file
def create_windows(dataframe_radiation, geodataframe_building_architecture):
    # TODO: documentation

    # sort dataframe for name of building for default orientation generation
    # FIXME remove this in the future
    dataframe_radiation.sort(['Name'])

    # default values
    # FIXME use real window angle in the future
    angle_window_default = 90  # (deg), 90° = vertical, 0° = horizontal

    # read relevant columns from dataframe
    freeheight = dataframe_radiation['Freeheight']
    height_ag = dataframe_radiation['height_ag']
    length_shape = dataframe_radiation['Shape_Leng']
    name = dataframe_radiation['Name']

    # calculate number of exposed floors per facade
    num_floors_freeheight = (freeheight / 3).astype('int')  # floor heigth is 3 m
    num_windows = num_floors_freeheight.sum()  # total number of windows in model, not used

    # initialize lists for results
    col_name_building = []
    col_area_window = []
    col_height_window_above_ground = []
    col_orientation_window = []
    col_angle_window = []
    col_height_window_in_zone = []

    # for all vertical exposed facades
    for i in range(name.size):

        # generate orientation
        # TODO in the future get real orientation
        # FIXME
        if i % 4 == 0:
            orientation_default = 0
        elif i % 4 == 1:
            orientation_default = 180
        elif i % 4 == 2:
            orientation_default = 90
        elif i % 4 == 3:
            orientation_default = 270
        else:
            orientation_default = 0

        # get window-wall ratio of building from architecture geodataframe
        win_wall_ratio = geodataframe_building_architecture.loc[geodataframe_building_architecture['Name'] == name[i]].iloc[0]['win_wall']

        # for all levels in a facade
        for j in range(num_floors_freeheight[i]):
            window_area = length_shape[i] * 3 * win_wall_ratio  # 3m = average floor height, 0.4 = window_wall fraction
            window_height_above_ground = height_ag[i] - freeheight[
                i] + j * 3 + 1.5  # 1.5m = window is placed in the middle of the floor height
            window_height_in_zone = window_height_above_ground  # for now the building is one ventilation zone

            col_name_building.append(name[i])
            col_area_window.append(window_area)
            col_height_window_above_ground.append(window_height_above_ground)
            col_orientation_window.append(orientation_default)
            col_angle_window.append(angle_window_default)
            col_height_window_in_zone.append(window_height_in_zone)

    # create pandas dataframe with table of all windows
    dataframe_windows = pandas.DataFrame({'name_building': col_name_building, 'area_window': col_area_window,
                                      'height_window_above_ground': col_height_window_above_ground,
                                      'orientation_window': col_orientation_window, 'angle_window': col_angle_window,
                                      'height_window_in_zone': col_height_window_in_zone})

    return dataframe_windows





# ++++ GENERAL ++++


# calculation of density of air according to 6.4.2.1 in [1]
def calc_rho_air(temp_air):
    # constants from Table 12 in [1]
    # TODO import from global variables
    rho_air_ref = 1.23  # (kg/m3)
    temp_air_ref = 283  # (K)

    # Equation (1) in [1]
    rho_air = temp_air_ref / temp_air * rho_air_ref
    return rho_air


# lookup default wind pressure coefficients for air leakage paths according to B.1.3.3 in [1]
def lookup_coeff_wind_pressure(height_path, class_shielding, orientation_path, slope_roof, factor_cros):
    # conventions
    # -----------
    #
    # class_shielding = 0 : open terrain
    # class_shielding = 1 : normal
    # class_shielding = 2 : shielded

    # orientation_path = 0 : facade facing wind
    #                    1 : facade not facing wind
    #                    2 : roof

    # factor_cros = 0 : cross ventilation not possible
    #             = 1 : cross ventilation possible

    # Table B.5 in [1]
    table_coeff_wind_pressure_cross_ventilation = numpy.array([[0.5, -0.7, -0.7, -0.6, -0.2],
                                                               [0.25, -0.5, -0.6, -0.5, -0.2],
                                                               [0.05, -0.3, -0.5, -0.4, -0.2],
                                                               [0.65, -0.7, -0.7, -0.6, -0.2],
                                                               [0.45, -0.5, -0.6, -0.5, -0.2],
                                                               [0.25, -0.3, -0.5, -0.4, -0.2],
                                                               [0.8, -0.7, -0.7, -0.6, -0.2]])

    # Table B.6 in [1]
    table_coeff_wind_pressure_non_cross_ventilation = numpy.array([0.05, -0.05, 0])

    num_paths = height_path.shape[0]
    coeff_wind_pressure = numpy.zeros(num_paths)

    for i in range(0, num_paths):

        if factor_cros == 1:

            if height_path[i] < 15:
                index_row = 0
            elif 15 <= height_path[i] < 50:
                index_row = 3
            elif height_path[i] >= 50:
                index_row = 6

            index_row = index_row + class_shielding

            if orientation_path[i] == 2:
                if slope_roof < 10:
                    index_col = 0
                elif 10 <= slope_roof <= 30:
                    index_col = 1
                elif slope_roof > 30:
                    index_col = 2
                index_col = index_col + orientation_path[i]
            elif orientation_path[i] == 0 or orientation_path[i] == 1:
                index_col = orientation_path[i]

            coeff_wind_pressure[i] = table_coeff_wind_pressure_cross_ventilation[index_row, index_col]

        elif factor_cros == 0:
            index_col = orientation_path[i]

            coeff_wind_pressure[i] = table_coeff_wind_pressure_non_cross_ventilation[index_col]

    return coeff_wind_pressure


# calculation of indoor-outdoor pressure difference at air path according to 6.4.2.4 in [1]
def calc_delta_p_path(p_zone_ref, height_path, temp_zone, coeff_wind_pressure_path, u_wind_site, temp_ext):
    # constants from Table 12 in [1]
    # TODO import from global variables
    g = 9.81  # (m/s2)
    rho_air_ref = 1.23  # (kg/m3)
    temp_ext_ref = 283  # (K)

    # Equation (5) in [1]
    p_zone_path = p_zone_ref - rho_air_ref * height_path * g * temp_ext_ref / temp_zone

    # Equation (4) in [1]
    p_ext_path = rho_air_ref * (
        0.5 * coeff_wind_pressure_path * u_wind_site ** 2 - height_path * g * temp_ext_ref / temp_ext)

    # Equation (3) in [1]
    delta_p_path = p_ext_path - p_zone_path

    return delta_p_path


# ++++ LEAKAGES ++++


#  calculate volume air flow of single leakage path according to 6.4.3.6.5 in [1]
def calc_qv_lea_path(coeff_lea_path, delta_p_lea_path):
    # default values in [1]
    # TODO reference global variables
    n_lea = 0.667  # (-), B.1.3.15 in [1]

    # Equation (64) in [1]
    qv_lea_path = coeff_lea_path * numpy.sign(delta_p_lea_path) * numpy.abs(delta_p_lea_path) ** n_lea
    return qv_lea_path


# calculate default leakage coefficient of zone according to B.1.3.16 in [1]
def calc_coeff_lea_zone(qv_delta_p_lea_ref, area_lea):
    # default values in [1]
    # TODO reference global variables
    delta_p_lea_ref = 50  # (Pa), B.1.3.14 in [1]
    n_lea = 0.667  # (-), B.1.3.15 in [1]

    # Eq. (B.5) in [1]
    coeff_lea_zone = qv_delta_p_lea_ref * area_lea / (delta_p_lea_ref ** n_lea)

    return coeff_lea_zone


# allocate default leakage paths according to B.1.3.17 in [1]
def allocate_default_leakage_paths(coeff_lea_zone, area_facade_zone, area_roof_zone, height_zone):
    # Equation (B.6) in [1]
    coeff_lea_facade = coeff_lea_zone * area_facade_zone / (area_facade_zone + area_roof_zone)
    # Equation (B.7) in [1]
    coeff_lea_roof = coeff_lea_zone * area_roof_zone / (area_facade_zone + area_roof_zone)

    coeff_lea_path = numpy.zeros(5)
    height_lea_path = numpy.zeros(5)
    orientation_lea_path = numpy.zeros(5)

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


# calculation of leakage infiltration and exfiltration air mass flow as a function of zone indoor reference pressure
def calc_qm_lea(qv_delta_p_lea_ref_zone, area_lea_zone, area_facade_zone, area_roof_zone, height_zone, class_shielding,
                slope_roof, factor_cros, p_zone_ref, temp_zone, u_wind_site, temp_ext):
    # calculate leakage coefficient of zone
    coeff_lea_zone = calc_coeff_lea_zone(qv_delta_p_lea_ref_zone, area_lea_zone)

    # allocate default leakage paths
    coeff_lea_path, height_lea_path, orientation_lea_path = allocate_default_leakage_paths(coeff_lea_zone,
                                                                                           area_facade_zone,
                                                                                           area_roof_zone, height_zone)

    # print(coeff_lea_path, height_lea_path, orientation_lea_path)

    # lookup wind pressure coefficients for leakage paths
    coeff_wind_pressure_path = lookup_coeff_wind_pressure(height_lea_path, class_shielding, orientation_lea_path,
                                                          slope_roof, factor_cros)

    # print(coeff_wind_pressure_path)

    # calculation of pressure difference at leakage path
    delta_p_path = calc_delta_p_path(p_zone_ref, height_lea_path, temp_zone, coeff_wind_pressure_path, u_wind_site,
                                     temp_ext)

    # print(delta_p_path)

    # calculation of leakage air volume flow at path
    qv_lea_path = calc_qv_lea_path(coeff_lea_path, delta_p_path)

    # print(qv_lea_path)

    # Eq. (65) in [1], infiltration is sum of air flows greater zero
    qv_lea_in = qv_lea_path[numpy.where(qv_lea_path > 0)].sum()

    # Eq. (66) in [1], exfiltration is sum of air flows smaller zero
    qv_lea_out = qv_lea_path[numpy.where(qv_lea_path < 0)].sum()

    # conversion to air mass flows according to 6.4.3.8 in [1]
    # Eq. (67) in [1]
    qm_lea_in = qv_lea_in * calc_rho_air(temp_ext)
    # Eq. (68) in [1]
    qm_lea_out = qv_lea_out * calc_rho_air(temp_zone)

    # print (qm_lea_in, qm_lea_out)

    return qm_lea_in, qm_lea_out


# ++++ VENTILATION OPENINGS ++++


# calculate volume air flow of single ventilation opening path according to 6.4.3.6.4 in [1]
def calc_qv_vent_path(coeff_vent_path, delta_p_vent_path):
    # default values in [1]
    # TODO reference global variables
    n_vent = 0.5  # (-), B.1.2.2 in [1]

    # Equation (60) in [1]
    qv_vent_path = coeff_vent_path * numpy.sign(delta_p_vent_path) * numpy.abs(delta_p_vent_path) ** n_vent
    return qv_vent_path


# calculate air volume flow coefficient of ventilation openings of zone according to 6.4.3.6.4 in [1]
def calc_coeff_vent_zone(area_vent_zone):
    # default values in [1]
    # TODO reference global variables
    n_vent = 0.5  # (-), B.1.2.2 in [1]
    coeff_d_vent = 0.6  # (-), B.1.2.1 in [1]
    delta_p_vent_ref = 50  # (Pa) FIXME no default value specified in standard
    # constants from Table 12 in [1]
    rho_air_ref = 1.23  # (kg/m3)

    # Eq. (61) in [1]
    coeff_vent_zone = 3600 / 10000 * coeff_d_vent * area_vent_zone * (2 / rho_air_ref) ** 0.5 * (
                                                                                                    1 / delta_p_vent_ref) ** (
                                                                                                    n_vent - 0.5)

    return coeff_vent_zone


# allocate default ventilation openings according to B.1.3.13 in [1]
def allocate_default_ventilation_openings(coeff_vent_zone, height_zone):
    # initialize
    coeff_vent_path = numpy.zeros(4)
    height_vent_path = numpy.zeros(4)
    orientation_vent_path = numpy.zeros(4)

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


# calculation of air flows through ventilation openings in the facade
def calc_qm_vent(area_vent_zone, height_zone, class_shielding, factor_cros, p_zone_ref, temp_zone, u_wind_site,
                 temp_ext):
    # calculate ventilation opening coefficient of zone
    coeff_vent_zone = calc_coeff_vent_zone(area_vent_zone)

    # allocate default leakage paths
    coeff_vent_path, height_vent_path, orientation_vent_path = allocate_default_ventilation_openings(coeff_vent_zone,
                                                                                                     height_zone)

    # lookup wind pressure coefficients for leakage paths
    coeff_wind_pressure_path = lookup_coeff_wind_pressure(height_vent_path, class_shielding, orientation_vent_path,
                                                          0, factor_cros)

    # calculation of pressure difference at leakage path
    delta_p_path = calc_delta_p_path(p_zone_ref, height_vent_path, temp_zone, coeff_wind_pressure_path, u_wind_site,
                                     temp_ext)

    # calculation of leakage air volume flow at path
    qv_vent_path = calc_qv_lea_path(coeff_vent_path, delta_p_path)

    # print(qv_vent_path)

    # Eq. (62) in [1], air flow entering through ventilation openings is sum of air flows greater zero
    qv_vent_in = qv_vent_path[numpy.where(qv_vent_path > 0)].sum()

    # Eq. (63) in [1], air flow entering through ventilation openings is sum of air flows smaller zero
    qv_vent_out = qv_vent_path[numpy.where(qv_vent_path < 0)].sum()

    # conversion to air mass flows according to 6.4.3.8 in [1]
    # Eq. (67) in [1]
    qm_vent_in = qv_vent_in * calc_rho_air(temp_ext)
    # Eq. (68) in [1]
    qm_vent_out = qv_vent_out * calc_rho_air(temp_zone)

    # print (qm_lea_in, qm_lea_out)

    return qm_vent_in, qm_vent_out


# ++++ WINDOW VENTILATION ++++

# calculate free window opening area according to 6.4.3.5.2 in [1]
def calc_area_window_free(area_window_max):

    # default values
    r_window_arg = 0.5  # (-), Tab 11 in [1]
    # TODO: this might be a dynamic parameter

    # Eq. (42) in [1]
    area_window_free = r_window_arg * area_window_max
    return area_window_free

# calculation of total open window area according to 6.4.3.5.2 in [1]
def calc_area_window_tot(dataframe_windows_building):

    # Eq. (43) in [1]
    area_window_tot = calc_area_window_free(sum(dataframe_windows_building['area_window']))

    return area_window_tot


# calculation of effective stack height for window ventilation according to 6.4.3.4.1 in [1]
def calc_effective_stack_height(dataframe_windows_building):
    # TODO: maybe this formula is wrong

    # first part of Eq. (46) in [1]
    height_window_stack_1 = dataframe_windows_building['height_window_in_zone'] + dataframe_windows_building[
                                                                                      'height_window_above_ground'] / 2
    # second part of Eq. (46) in [1]
    height_window_stack_2 = dataframe_windows_building['height_window_in_zone'] - dataframe_windows_building[
                                                                                      'height_window_above_ground'] / 2
    # Eq. (46) in [1]
    height_window_stack = max(height_window_stack_1) - min(height_window_stack_2)

    return height_window_stack

# calculate cross-ventilation window area according to the procedure in 6.4.3.5.4.3 in [1]
def calc_area_window_cros(dataframe_windows_building):

    # initialize results
    area_window_ori = numpy.zeros(4)
    area_window_cros = numpy.zeros(2)

    # area window tot
    area_window_tot = calc_area_window_tot(dataframe_windows_building)

    for i in range(2):
        for j in range(4):

            # Eq. (51) in [1]
            alpha_ref = i*45 + j*90
            alpha_max = alpha_ref + 45
            alpha_min = alpha_ref - 45
            for k in range(dataframe_windows_building['name_building'].size):
                if alpha_min <= dataframe_windows_building['orientation_window'].iloc[k] <= alpha_max and dataframe_windows_building['angle_window'].iloc[k] >= 60:
                    # Eq. (52) in [1]
                    area_window_free = calc_area_window_free(dataframe_windows_building['area_window'].iloc[k])
                    area_window_ori[j] = area_window_ori[j] + area_window_free
        for j in range(4):
            if area_window_ori[j] > 0:
                # Eq. (53) in [1]
                area_window_cros[i] = area_window_cros[i] + 0.25 * 1/(((1/area_window_ori[j]**2)+(1/(area_window_tot-area_window_ori[j])**2))**0.5)

    # Eq. (54) in [1]
    return min(area_window_cros)


# calculation of cross ventilated and non-cross ventilated window ventilation according to procedure in 6.4.3.5.4 in [1]
def calc_q_v_arg(factor_cros, temp_ext, dataframe_windows_building, u_wind_10, temp_zone):
    # initialize result
    q_v_arg_in = 0
    q_v_arg_out = 0

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
    area_window_tot = calc_area_window_tot(dataframe_windows_building)
    h_window_stack = calc_effective_stack_height(dataframe_windows_building)

    # volume flow rates of non-cross ventilated zone according to 6.4.3.5.4.2 in [1]
    if factor_cros == 0:

        # Eq. (47) in [1]
        q_v_arg_in = 3600 * rho_air_ref / rho_air_ext * area_window_tot / 2 * (
            coeff_turb + coeff_wind * u_wind_10 ** 2 + coeff_stack * h_window_stack * abs(temp_zone - temp_ext) ** 0.5)
        # Eq. (48) in [1]
        q_v_arg_out = -3600 * rho_air_ref / rho_air_zone * area_window_tot / 2 * (
            coeff_turb + coeff_wind * u_wind_10 ** 2 + coeff_stack * h_window_stack * abs(temp_zone - temp_ext) ** 0.5)

    elif factor_cros == 1:

        # get window area of cross-ventilation
        area_window_cros = calc_area_window_cros(dataframe_windows_building)
        print(area_window_cros)

        # Eq. (49) in [1]
        q_v_arg_in = 3600 * rho_air_ref / rho_air_ext * ((
                                                             coeff_d_window * area_window_cros * u_wind_10 * delta_c_p ** 0.5) ** 2 + (
                                                             area_window_tot / 2 * (coeff_stack * h_window_stack * abs(
                                                                 temp_zone - temp_ext)) ** 0.5) ** 2) ** 0.5

        # Eq. (50) in [1]
        # TODO this formula was changed from the standard to use the air density in the zone
        q_v_arg_out = -3600 * rho_air_ref / rho_air_zone * ((
                                                               coeff_d_window * area_window_cros * u_wind_10 * delta_c_p ** 0.5) ** 2 + (
                                                               area_window_tot / 2 * (
                                                               coeff_stack * h_window_stack * abs(
                                                                   temp_zone - temp_ext)) ** 0.5) ** 2) ** 0.5

    # conversion to air mass flows according to 6.4.3.8 in [1]
    # Eq. (67) in [1]
    qm_arg_in = q_v_arg_in * calc_rho_air(temp_ext)
    # Eq. (68) in [1]
    qm_arg_out = q_v_arg_out * calc_rho_air(temp_zone)

    return qm_arg_in, qm_arg_out

# ++++ MECHANICAL VENTILATION ++++
def calc_q_m_mech():

    # testing
    area_floor = 100
    q_ve_required_schedule = 2/3600*area_floor
    w_int_schedule = 5/(1000*3600)*area_floor # internal moisture gains
    rel_humidity_ext = 60
    temp_ext = 25
    temp_zone = 20
    q_sensible = 1
    t_zone_prev = 20

    res = calc_HVAC(0, 0, 0, rel_humidity_ext, temp_ext, temp_zone, q_ve_required_schedule, 0, q_sensible, t_zone_prev, w_int_schedule, gv)

    print(res)
    return

# ++++ MASS BALANCE ++++

# air flow mass balance for iterative calculation according to 6.4.3.9 in [1]
def calc_air_flow_mass_balance(p_zone_ref, geodataframe_geometry_building, dataframe_windows_building):
    # TODO the idea is that the inputs to this functions consist of handles (or similar) to a building geometry in the buildings file, to the climate file, etc.

    # for testing the scripts
    qv_delta_p_lea_ref_zone = 500  # (m3/h), 1 ACH
    area_lea_zone = 0.1  # (m2) ?
    # area_facade_zone = 200  # (m2)
    # area_roof_zone = 100  # (m2)
    # height_zone = 5  # (m)
    class_shielding = 0  # open
    # slope_roof = 10  # (deg)
    factor_cros = 1  # 1 = cross ventilation possible
    temp_zone = 293  # (K)
    u_wind_site = 5  # (m/s)
    u_wind_10 = 5
    temp_ext = 299  # (K)
    area_vent_zone = 50  # (cm2) area of ventilation openings

    area_facade_zone, area_roof_zone, height_zone, slope_roof = get_building_properties_ventilation(geodataframe_geometry_building)

    qm_sup_dis = 0
    qm_eta_dis = 0
    qm_lea_sup_dis = 0
    qm_lea_eta_dis = 0
    qm_comb_in = 0
    qm_comb_out = 0
    qm_pdu_in = 0
    qm_pdu_out = 0
    qm_arg_in, qm_arg_out = calc_q_v_arg(factor_cros, temp_ext, dataframe_windows_building, u_wind_10, temp_zone)
    qm_vent_in, qm_vent_out = calc_qm_vent(area_vent_zone, height_zone, class_shielding, factor_cros, p_zone_ref,
                                           temp_zone, u_wind_site, temp_ext)
    qm_lea_in, qm_lea_out = calc_qm_lea(qv_delta_p_lea_ref_zone, area_lea_zone, area_facade_zone, area_roof_zone,
                                        height_zone, class_shielding, slope_roof, factor_cros, p_zone_ref,
                                        temp_zone, u_wind_site, temp_ext)

    # mass balance, Eq. (69) in [1]
    qm_balance = qm_sup_dis + qm_eta_dis + qm_lea_sup_dis + qm_lea_eta_dis + qm_comb_in + qm_comb_out + qm_pdu_in + qm_pdu_out + qm_arg_in + qm_arg_out + qm_vent_in + qm_vent_out + qm_lea_in + qm_lea_out

    print(qm_arg_in, qm_arg_out)
    print(qm_vent_in, qm_vent_out)
    print(qm_lea_in, qm_lea_out)

    return abs(qm_balance)


# ++++ HELPERS ++++
def get_building_properties_ventilation(geodataframe_building_geometry):
    # geodataframe contains single building


    # TODO: get real slope of roof in the future
    slope_roof_default = 0

    # geometry = geodataframe_building_geometry.iloc[0]
    area_facade_zone = geodataframe_building_geometry.length.iloc[0] * geodataframe_building_geometry.iloc[0].height_ag
    area_roof_zone = geodataframe_building_geometry.area.iloc[0]
    height_zone = geodataframe_building_geometry.iloc[0].height_ag
    slope_roof = slope_roof_default

    return area_facade_zone, area_roof_zone, height_zone, slope_roof

def get_windows_of_building(dataframe_windows, name_building):
    return dataframe_windows.loc[dataframe_windows['name_building'] == name_building]


# TESTING
if __name__ == '__main__':

    calc_q_m_mech()


    # generate windows based on geometry of vertical surfaces in radiation file
    locator = inputlocator.InputLocator(scenario_path=r'C:\cea-reference-case\reference-case\baseline')
    dataframe_radiation = pandas.read_csv(locator.get_radiation())
    geodataframe_building_architecture = geopandas.GeoDataFrame.from_file(locator.get_building_architecture())
    # print(geodataframe_building_architecture)
    geodataframe_building_geometry = geopandas.GeoDataFrame.from_file(locator.get_building_geometry())
    # print(geodataframe_building_geometry)

    dataframe_windows = create_windows(dataframe_radiation, geodataframe_building_architecture)

    building_test = 'B302040213'

    # get building windows
    windows_building_test = get_windows_of_building(dataframe_windows, building_test)
    # get building geometry
    geometry_building_test = geodataframe_building_geometry.loc[geodataframe_building_geometry['Name'] == building_test]

    # print(type(windows_building_test))
    # print(windows_building_test)

    p_zone_ref = 5  # (Pa) zone pressure, THE UNKNOWN VALUE

    res = minimize(calc_air_flow_mass_balance, p_zone_ref, args=(geometry_building_test,windows_building_test,), method='Nelder-Mead')

    # this will be the function to minimize by a slover
    # qm_balance = calc_air_flow_mass_balance(p_zone_ref)


    print(res)

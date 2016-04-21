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


# ++++ GEOMETRY ++++

# for now get geometric properties of exposed facades from the radiation file
def create_windows(table_radiation, building_architecture):
    # TODO: documentation

    # default values
    angle_window_default = 90  # (deg), 90° = vertical, 0° = horizontal

    freeheight = table_radiation['Freeheight']
    height_ag = table_radiation['height_ag']
    height = table_radiation['height']
    length_shape = table_radiation['Shape_Leng']
    name = table_radiation['Name']

    num_floors_freeheight = (freeheight / 3).astype('int')  # floor heigth is 3 m
    num_windows = num_floors_freeheight.sum()
    print(num_windows)

    col_name_building = []
    col_area_window = []
    col_height_window_above_ground = []
    col_orientation_window = []
    col_angle_window = []
    col_height_window_in_zone = []
    # pandas.DataFrame(columns=['name_building','area_window','height_window','orientation_window'])

    # generate windows
    w = 0
    for i in range(name.size):

        for j in range(num_floors_freeheight[i]):
            window_area = length_shape[i] * 3 * 0.4  # 3m = average floor height, 0.4 = window_wall fraction
            window_height_above_ground = height_ag[i] - freeheight[
                i] + j * 3 + 1.5  # 1.5m = window is placed in the middle of the floor height
            window_height_in_zone = window_height_above_ground  # for now the building is one ventilation zone

            col_name_building.append(name[i])
            col_area_window.append(window_area)
            col_height_window_above_ground.append(window_height_above_ground)
            col_orientation_window.append(0)
            col_angle_window.append(angle_window_default)
            col_height_window_in_zone.append(window_height_in_zone)
            w = w + 1

    # create pandas dataframe with table of all windows
    table_windows = pandas.DataFrame({'name_building': col_name_building, 'area_window': col_area_window,
                                      'height_window_above_ground': col_height_window_above_ground,
                                      'orientation_window': col_orientation_window, 'angle_window': col_angle_window,
                                      'height_window_in_zone': col_height_window_in_zone})

    print(w, 'windows generated')
    # print(table_windows)


    return table_windows


def get_windows_of_building(table_windows, name_building):
    return table_windows.loc[table_windows['name_building'] == name_building]


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

# calculation of total open window area
def calc_area_window_tot(dataframe_windows_building):
    # TODO: reference standard

    # default values
    r_window_arg = 0.5

    area_window_tot = sum(dataframe_windows_building['height_window_in_zone']) * r_window_arg

    return area_window_tot


# calculation of effective stack height for window ventilation
def calc_effective_stack_height(dataframe_windows_building):
    # TODO: reference standard
    # TODO: maybe this formula is wrong

    height_window_stack_1 = dataframe_windows_building['height_window_in_zone'] + dataframe_windows_building[
                                                                                      'height_window_above_ground'] / 2
    height_window_stack_2 = dataframe_windows_building['height_window_in_zone'] - dataframe_windows_building[
                                                                                      'height_window_above_ground'] / 2

    height_window_stack = max(height_window_stack_1) - min(height_window_stack_2)

    return height_window_stack

# calculation of cross ventilated and non-cross ventilated window ventilation
def calc_q_v_arg(factor_cros, temp_ext, dataframe_windows_building, u_wind_10, temp_zone):

    q_v_arg_in = 0
    q_v_arg_out = 0

    # constants from Table 12 in [1]
    # TODO import from global variables
    rho_air_ref = 1.23  # (kg/m3)
    coeff_turb = 0.01 # (m/s)
    coeff_wind = 0.001 # (1/(m/s))
    coeff_stack = 0.0035 # ((m/s)/(mK))


    rho_air_ext = calc_rho_air(temp_ext)
    rho_air_zone = calc_rho_air(temp_zone)
    area_window_tot = calc_area_window_tot(dataframe_windows_building)
    h_window_stack = calc_effective_stack_height(dataframe_windows_building)


    if factor_cros == 0:

         q_v_arg_in = 3600*rho_air_ref/rho_air_ext*area_window_tot/2*(coeff_turb + coeff_wind*u_wind_10**2 + coeff_stack * h_window_stack*abs(temp_zone-temp_ext)**0.5)
         q_v_arg_out = -3600*rho_air_ref/rho_air_zone*area_window_tot/2*(coeff_turb + coeff_wind*u_wind_10**2 + coeff_stack * h_window_stack*abs(temp_zone-temp_ext)**0.5) # TODO check and reference

    # elif factor_cros == 1:

        # something


    return q_v_arg_in, q_v_arg_out


# ++++ MASS BALANCE ++++

# air flow mass balance for iterative calculation according to 6.4.3.9 in [1]
def calc_air_flow_mass_balance(p_zone_ref, dataframe_windows_building):
    # TODO the idea is that the inputs to this functions consist of handles (or similar) to a building geometry in the buildings file, to the climate file, etc.

    # for testing the scripts
    qv_delta_p_lea_ref_zone = 500  # (m3/h), 1 ACH
    area_lea_zone = 0.1  # (m2) ?
    area_facade_zone = 200  # (m2)
    area_roof_zone = 100  # (m2)
    height_zone = 5  # (m)
    class_shielding = 0  # open
    slope_roof = 10  # (deg)
    factor_cros = 0  # 1 = cross ventilation possible
    temp_zone = 293  # (K)
    u_wind_site = 5  # (m/s)
    u_wind_10 = 5
    temp_ext = 299  # (K)
    area_vent_zone = 50  # (cm2) area of ventilation openings


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

    return abs(qm_balance)


# TESTING
if __name__ == '__main__':

    # generate windows based on geometry of vertical surfaces in radiation file
    locator = inputlocator.InputLocator(scenario_path=r'C:\cea-reference-case\reference-case\baseline')
    table_radiation = pandas.read_csv(locator.get_radiation())
    table_windows = create_windows(table_radiation, 0)

    building_test = 'B302040213'

    windows_building_test = get_windows_of_building(table_windows, building_test)
    print(type(windows_building_test))
    print(windows_building_test)

    p_zone_ref = 5  # (Pa) zone pressure, THE UNKNOWN VALUE

    res = minimize(calc_air_flow_mass_balance, p_zone_ref, args=(windows_building_test,), method='Nelder-Mead')

    # this will be the function to minimize by a slover
    # qm_balance = calc_air_flow_mass_balance(p_zone_ref)


    print(res)


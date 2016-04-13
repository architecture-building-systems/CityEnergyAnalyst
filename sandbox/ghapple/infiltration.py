# -*- coding: utf-8 -*-
"""
============================================
Ventilation according to DIN EN 16798-7:2015
============================================ 

Created on Tue Apr 12 18:04:04 2016

@author: happle@arch.ethz.ch

Reference:
[1] Energieeffizienz von Gebäuden –xTeil 7: Modul M5-1, M 5-5, M 5-6, M 5-8 –
    Berechnungsmethoden zur Bestimmung der Luftvolumenströme in Gebäuden inklusive Infiltration;
    Deutsche Fassung prEN 16798-7:2014

"""

from __future__ import division
import numpy


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


# lookup default wind pressure coefficients for air leakage paths according to B.1.3.3 in [1]
def lookup_coeff_wind_pressure(height_path, class_shielding, orientation_path, slope_roof, id_cross_ventilation):
    # conventions
    # -----------
    #
    # class_shielding = 0 : open terrain
    # class_shielding = 1 : normal
    # class_shielding = 2 : shielded

    # orientation_path = 0 : facade facing wind
    #                    1 : facade not facing wind
    #                    2 : roof

    # id_cross_ventilation = 0 : cross ventilation possible
    #                      = 1 : cross ventilation not possible

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

        if id_cross_ventilation == 0:

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

        elif id_cross_ventilation == 1:
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


# calculation of density of air according to 6.4.2.1 in [1]
def calc_rho_air(temp_air):
    # constants from Table 12 in [1]
    # TODO import from global variables
    rho_air_ref = 1.23  # (kg/m3)
    temp_air_ref = 283  # (K)

    # Equation (1) in [1]
    rho_air = temp_air_ref / temp_air * rho_air_ref
    return rho_air


# calculation of leakage infiltration and exfiltration air mass flow as a function of zone indoor reference pressure
def calc_qm_lea(qv_delta_p_lea_ref_zone, area_lea_zone, area_facade_zone, area_roof_zone, height_zone, class_shielding,
                slope_roof, id_cross_ventilation, p_zone_ref, temp_zone, u_wind_site, temp_ext):
    # calculate leakage coefficient of zone
    coeff_lea_zone = calc_coeff_lea_zone(qv_delta_p_lea_ref_zone, area_lea_zone)

    # allocate default leakage paths
    coeff_lea_path, height_lea_path, orientation_lea_path = allocate_default_leakage_paths(coeff_lea_zone,
                                                                                           area_facade_zone,
                                                                                           area_roof_zone, height_zone)

    # print(coeff_lea_path, height_lea_path, orientation_lea_path)

    # lookup wind pressure coefficients for leakage paths
    coeff_wind_pressure_path = lookup_coeff_wind_pressure(height_lea_path, class_shielding, orientation_lea_path,
                                                          slope_roof, id_cross_ventilation)

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


# air flow mass balance for iterative calculation according to 6.4.3.9 in [1]
def calc_air_flow_mass_balance(p_zone_ref):
    # TODO the idea is that the inputs to this functions consist of handles (or similar) to a building geometry in the buildings file, to the climate file, etc.

    # for testing the scripts
    qv_delta_p_lea_ref_zone = 500  # (m3/h), 1 ACH
    area_lea_zone = 0.1  # (m2) ?
    area_facade_zone = 200  # (m2)
    area_roof_zone = 100  # (m2)
    height_zone = 5  # (m)
    class_shielding = 0  # open
    slope_roof = 10  # (deg)
    id_cross_ventilation = 0  # cross ventilation possible
    temp_zone = 293  # (K)
    u_wind_site = 5  # (m/s)
    temp_ext = 299  # (K)

    qm_sup_dis = 0
    qm_eta_dis = 0
    qm_lea_sup_dis = 0
    qm_lea_eta_dis = 0
    qm_comb_in = 0
    qm_comb_out = 0
    qm_pdu_in = 0
    qm_pdu_out = 0
    qm_arg_in = 0
    qm_arg_out = 0
    qm_vent_in = 0
    qm_vent_out = 0
    qm_lea_in, qm_lea_out = calc_qm_lea(qv_delta_p_lea_ref_zone, area_lea_zone, area_facade_zone, area_roof_zone,
                                        height_zone, class_shielding, slope_roof, id_cross_ventilation, p_zone_ref,
                                        temp_zone, u_wind_site, temp_ext)

    # mass balance, Eq. (69) in [1]
    qm_balance = qm_sup_dis + qm_eta_dis + qm_lea_sup_dis + qm_lea_eta_dis + qm_comb_in + qm_comb_out + qm_pdu_in + qm_pdu_out + qm_arg_in + qm_arg_out + qm_vent_in + qm_vent_out + qm_lea_in + qm_lea_out

    return qm_balance


# TESTING
if __name__ == '__main__':
    p_zone_ref = 3  # (Pa) zone pressure, THE UNKNOWN VALUE

    # this will be the function to minimize by a slover
    qm_balance = calc_air_flow_mass_balance(p_zone_ref)

    print(qm_balance)

# -*- coding: utf-8 -*-

from __future__ import division
import numpy as np
import math
from cea import globalvar

# constants in standards
p_atm = 101325  # (Pa) atmospheric pressure [section 6.3.6 in ISO 52016-1:2017]
rho_a = 1.204  # (kg/m3) density of air at 20°C and 0m height [section 6.3.6 in ISO 52016-1:2017]
h_we = 2466e3  # (J/kg) Latent heat of vaporization of water [section 6.3.6 in ISO 52016-1:2017]

# constants
delta_t = 3600  # (s)

# set points
phi_int_set_hu_ztc_t = 30  # (%) minimum indoor humidity [undocumented from aircon model]
phi_int_set_dhu_ztc_t = 70  # (%) maximum indoor humidity [undocumented from aircon model]

# import
floor_height = globalvar.GlobalVariables().Z


def calc_humidification_moisture_load(tsd, bpr, t):
    # (71) in ISO 52016-1:2017

    # get air flows
    m_ve_mech = tsd['m_ve_mech'][t]
    m_ve_inf = tsd['m_ve_inf'][t] + tsd['m_ve_window'][t]
    x_ve_mech = tsd['x_ve_mech'][t]
    x_ve_inf = tsd['x_ve_inf'][t]

    # get set points
    x_set_min_ztc_t = calc_min_moisture_set_point(tsd, t)

    # get internal gains
    g_int_ztc_t = tsd['w_int'][t]  # gains from occupancy

    # zone humidity at previous time step
    x_int_a_ztc_t_1 = tsd['x_int'][t - 1]

    # zone volume
    vol_int_a_ztc = bpr.rc_model['Af'] * floor_height

    # calculate
    g_hu_ld_ztc_t = m_ve_mech * (x_set_min_ztc_t - x_ve_mech) + m_ve_inf * (x_set_min_ztc_t - x_ve_inf) - g_int_ztc_t + \
                    (rho_a * vol_int_a_ztc) / delta_t * (x_set_min_ztc_t - x_int_a_ztc_t_1)

    g_hu_ld_ztc_t = np.max(g_hu_ld_ztc_t, 0)

    return g_hu_ld_ztc_t


def calc_dehumidification_moisture_load(tsd, bpr, t):
    # (72) in ISO 52016-1:2017

    # get air flows
    m_ve_mech = tsd['m_ve_mech'][t]
    m_ve_inf = tsd['m_ve_inf'][t] + tsd['m_ve_window'][t]
    x_ve_mech = tsd['x_ve_mech'][t]
    x_ve_inf = tsd['x_ve_inf'][t]

    # get set points
    x_set_max_ztc_t = calc_max_moisture_set_point(tsd, t)

    # get internal gains
    g_int_ztc_t = tsd['w_int'][t]  # gains from occupancy

    # zone humidity at previous time step
    x_int_a_ztc_t_1 = tsd['x_int'][t - 1]

    # zone volume
    vol_int_a_ztc = bpr.rc_model['Af'] * floor_height

    # calculate
    g_dhu_ld_ztc_t = -m_ve_mech * (x_set_max_ztc_t - x_ve_mech) - m_ve_inf * (x_set_max_ztc_t - x_ve_inf) + g_int_ztc_t - \
                     (rho_a * vol_int_a_ztc) / delta_t * (x_set_max_ztc_t - x_int_a_ztc_t_1)

    g_dhu_ld_ztc_t = np.max([g_dhu_ld_ztc_t, 0])

    # dehumidification load is positive value according to standard
    return g_dhu_ld_ztc_t


def calc_min_moisture_set_point(tsd, t):
    # (75) in ISO 52016-1:2017

    t_int = tsd['T_int'][t]

    p_sat_int_ztc_t = calc_saturation_pressure(t_int)

    x_set_min_ztc_t = 0.622 * (phi_int_set_hu_ztc_t / 100 * p_sat_int_ztc_t) / (
    p_atm - phi_int_set_hu_ztc_t / 100 * p_sat_int_ztc_t)

    return x_set_min_ztc_t


def calc_max_moisture_set_point(tsd, t):
    # (76) in ISO 52016-1:2017

    t_int = tsd['T_int'][t]

    p_sat_int_ztc_t = calc_saturation_pressure(t_int)

    x_set_max_ztc_t = 0.622 * (phi_int_set_dhu_ztc_t / 100 * p_sat_int_ztc_t) / (
        p_atm - phi_int_set_dhu_ztc_t / 100 * p_sat_int_ztc_t)

    return x_set_max_ztc_t


def calc_saturation_pressure(theta):
    # (77) in ISO 52016-1:2017

    p_sat_int_ztc_t = 611.2 * math.exp(17.62 * theta / (243.12 + theta))

    return p_sat_int_ztc_t


def calc_required_moisture_mech_vent_hu(tsd, t):
    # (78) in ISO 52016-1:2017

    x_a_e = tsd['x_ve_mech'][t]  # external air moisture content (after possible HEX)
    m_ve_mech = tsd['m_ve_mech'][t]


    x_a_sup_hu_req = x_a_e + g_hu_ld / m_ve_mech

    return x_a_sup_hu_req


def calc_required_moisture_mech_vent_dhu(tsd, t):
    # (79) in ISO 52016-1:2017

    x_a_e = tsd['x_ve_mech'][t]  # external air moisture content (after possible HEX)
    m_ve_mech = tsd['m_ve_mech'][t]

    x_a_sup_dhu_req = x_a_e - g_dhu_ld / m_ve_mech

    return x_a_sup_dhu_req


def calc_moisture_in_zone_central(bpr, tsd, t):

    # (80) in ISO 52016-1:2017

    # zone volume
    vol_int_a_ztc = bpr.rc_model['Af'] * floor_height

    # get air flows
    m_ve_mech = tsd['m_ve_mech'][t]
    m_ve_inf = tsd['m_ve_inf'][t] + tsd['m_ve_window'][t]
    x_ve_mech = tsd['x_ve_mech'][t]
    x_ve_mech_sup = tsd['x_ve_mech'][t] # TODO: THAT IS FIXED! get supply moisture >= required moisture ----> can not be lower than dew point moisture at 6C
    x_ve_inf = tsd['x_ve_inf'][t]

    # get internal gains
    g_int_ztc_t = tsd['w_int'][t]  # gains from occupancy

    # zone humidity at previous time step
    x_int_a_ztc_t_1 = tsd['x_int'][t - 1] if not np.isnan(tsd['x_int'][t - 1]) else\
        convert_rh_to_moisture_content(tsd['rh_ext'][t-1], tsd['T_ext'][t - 1])

    # get (de)humidification loads
    g_hu_ld_ztc_t = tsd['g_hu_ld'][t]
    g_dhu_ld_ztc_t = tsd['g_dhu_ld'][t]

    # sum ventilation moisture + (de)humidification
    x_int_a = (m_ve_mech * x_ve_mech_sup + m_ve_inf * x_ve_inf + g_int_ztc_t + (
        rho_a * vol_int_a_ztc) / delta_t * x_int_a_ztc_t_1) / \
        ((m_ve_mech + m_ve_inf) + (rho_a * vol_int_a_ztc) / delta_t)

    # (81) in ISO 52016-1:2017
    g_hu_dhu_central = m_ve_mech * (x_ve_mech_sup - x_ve_mech)

    g_hu_central = np.max(g_hu_dhu_central, 0)
    g_dhu_central = np.max(-g_hu_dhu_central, 0)

    # (82) in ISO 52016-1:2017
    phi_hu_ld_central = h_we * g_hu_central

    # (83) in ISO 52016-1:2017
    phi_dhu_ld_central = h_we * g_dhu_central

    # set results
    tsd['x_int'][t] = x_int_a
    tsd['qh_lat_central'][t] = phi_hu_ld_central
    tsd['qc_lat_central'][t] = phi_dhu_ld_central

    return


def calc_moisture_content_in_zone_local(bpr, tsd, t):
    # (84) in ISO 52016-1:2017

    # zone volume
    vol_int_a_ztc = bpr.rc_model['Af'] * floor_height

    # get air flows
    m_ve_mech = tsd['m_ve_mech'][t]
    m_ve_inf = tsd['m_ve_inf'][t] + tsd['m_ve_window'][t]
    x_ve_mech = tsd['x_ve_mech'][t]
    x_ve_inf = tsd['x_ve_inf'][t]

    # get internal gains
    g_int_ztc_t = tsd['w_int'][t]  # gains from occupancy

    # zone humidity at previous time step
    x_int_a_ztc_t_1 = tsd['x_int'][t - 1] if not np.isnan(tsd['x_int'][t - 1]) else\
        convert_rh_to_moisture_content(tsd['rh_ext'][t-1], tsd['T_ext'][t - 1])

    # get (de)humidification loads
    g_hu_ld_ztc_t = tsd['g_hu_ld'][t]
    g_dhu_ld_ztc_t = tsd['g_dhu_ld'][t]

    # sum ventilation moisture + (de)humidification
    x_int_a_t = (m_ve_mech * x_ve_mech + m_ve_inf * x_ve_inf +
        g_hu_ld_ztc_t + g_dhu_ld_ztc_t + g_int_ztc_t + (
        rho_a * vol_int_a_ztc) / delta_t * x_int_a_ztc_t_1) / \
        ((m_ve_mech + m_ve_inf) + (rho_a * vol_int_a_ztc) / delta_t)

    tsd['x_int'][t] = x_int_a_t
    return

def convert_rh_to_moisture_content(rh, theta):

    p_sat = calc_saturation_pressure(theta)

    x = 0.622 * rh/100 * p_sat / p_atm

    return x


def calc_moisture_content_airflows(tsd, t):

    rh_ext = tsd['rh_ext'][t]
    theta_ext = tsd['T_ext'][t]
    #theta_ve_mech = tsd['theta_ve_mech'][t]

    tsd['x_ve_inf'][t] = convert_rh_to_moisture_content(rh_ext, theta_ext)
    tsd['x_ve_mech'][t] = convert_rh_to_moisture_content(rh_ext, theta_ext)

    return
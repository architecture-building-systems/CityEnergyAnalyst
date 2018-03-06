# -*- coding: utf-8 -*-
"""

Space emission systems (heating and cooling)
EN 15316-2
prEN 15316-2:2014

"""


from __future__ import division
import numpy as np

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def calc_q_em_ls_cooling(bpr, tsd, t):
    """
    calculation procedure for space emissions losses in the cooling case [prEN 15316-2:2014]

    :param bpr: building properties row
    :type bpr: BuildingPropertiesRow object
    
    :param tsd: time step data
    :type tsd: dict
    
    :param t: hour of year (0..8759)
    :type t: int
    
    :return: emission losses of cooling system for time step [W]
    :rtype: double
    """
    __author__ = "Gabriel Happle"

    # get properties
    theta_e = tsd['T_ext'][t]
    theta_int_ini = tsd['T_int'][t]
    q_em_out = tsd['Qcs_sen_sys'][t]

    q_em_max = -bpr.hvac['Qcsmax_Wm2'] * bpr.rc_model['Af']

    delta_theta_int_inc = calc_delta_theta_int_inc_cooling(bpr)

    theta_int_inc = calc_theta_int_inc(theta_int_ini, delta_theta_int_inc)

    theta_e_comb = calc_theta_e_comb_cooling(theta_e, bpr)

    return calc_q_em_ls(q_em_out, delta_theta_int_inc, theta_int_inc, theta_e_comb, q_em_max)


def calc_q_em_ls_heating(bpr, tsd, hoy):
    """
    calculation procedure for space emissions losses in the heating case [prEN 15316-2:2014]

    :param bpr: building properties row
    :type bpr: BuildingPropertiesRow object
    
    :param tsd: time step data
    :type tsd: dict
    
    :param hoy: hour of year (0..8759)
    :type hoy: int
    
    :return: emission losses of heating system for time step [W]
    :rtype: double
    """
    __author__ = "Gabriel Happle"

    # get properties
    theta_e = tsd['T_ext'][hoy]
    theta_int_ini = tsd['T_int'][hoy]
    q_em_out = tsd['Qhs_sen_sys'][hoy]

    q_em_max = bpr.hvac['Qhsmax_Wm2'] * bpr.rc_model['Af']

    delta_theta_int_inc = calc_delta_theta_int_inc_heating(bpr)

    theta_int_inc = calc_theta_int_inc(theta_int_ini, delta_theta_int_inc)

    theta_e_comb = calc_theta_e_comb_heating(theta_e)

    return calc_q_em_ls(q_em_out, delta_theta_int_inc, theta_int_inc, theta_e_comb, q_em_max)


def calc_q_em_ls(q_em_out, delta_theta_int_inc, theta_int_inc, theta_e_comb, q_em_max):

    """
    Eq. (8) in [prEN 15316-2:2014]

    With modification of capping emission losses at system capacity [Happle 01/2017]

    :param q_em_out: heating power of emission system (W)
    :type q_em_out: double
    
    :param delta_theta_int_inc: delta temperature caused by all losses (K)
    :type delta_theta_int_inc: double
    
    :param theta_int_inc: equivalent room temperature (°C)
    :type theta_int_inc: double
    
    :param theta_e_comb: ?comb? outdoor temperature (°C)
    :type theta_e_comb: double
    
    :param q_em_max: maximum emission capacity of heating/cooling system [W]
    :type q_em_max: double
    
    :return: emission losses of heating/cooling system [W]
    :rtype: double
    """
    __author__ = "Gabriel Happle"

    if abs(theta_int_inc-theta_e_comb) < 1e-6:
        q_em_ls = 0.0  # prevent division by zero
    else:
        q_em_ls = q_em_out * (delta_theta_int_inc / (theta_int_inc-theta_e_comb))

        # cap emission losses at absolute capacity
        if abs(q_em_ls + q_em_out) > abs(q_em_max):
            q_em_ls = q_em_max - q_em_out

        if not np.sign(q_em_ls) == np.sign(q_em_out):
            q_em_ls = 0.0  # prevent form negative emission losses

    return q_em_ls


def calc_theta_int_inc(theta_int_ini, delta_theta_int_inc):
    """
    Eq. (1) in [prEN 15316-2:2014]

    :param theta_int_ini: temperature [C]
    :type theta_int_ini: double
    
    :param delta_theta_int_inc: temperature [C]
    :type delta_theta_int_inc: double
    
    :return: sum of temperatures [C]
    :rtype: double
    """

    return theta_int_ini + delta_theta_int_inc


def calc_theta_e_comb_heating(theta_e):
    """
    Eq. (9) in [prEN 15316-2:2014]
    
    :param theta_e: outdoor temperature [C]
    :type theta_e: double

    :return: temperature [C]
    :rtype: double
    """

    return theta_e


def calc_theta_e_comb_cooling(theta_e, bpr):
    """
    Eq. (10) in [prEN 15316-2:2014]
    
    :param theta_e: outdoor temperature [C]
    :type theta_e: double

    :param bpr: BuildingPropertiesRow 
    :type bpr: BuildingPropertiesRow object
    
    :return: temperature [C]
    :rtype: double
    """

    return theta_e + get_delta_theta_e_sol(bpr)


def get_delta_theta_e_sol(bpr):
    """
    Appendix B.7 in [prEN 15316-2:2014]

    delta_theta_e_sol = 8K -- for medium window fraction or internal loads (e.g. residential)
    delta_theta_e_sol = 12K -- for large window fraction or internal loads (e.g. office)

    :param bpr:
    :return:
    """

    if 0 <= bpr.architecture.win_wall < 0.5:  # TODO fix criteria
        delta_theta_e_sol = 8  # (K)
    elif 0.5 <= bpr.architecture.win_wall < 1.0:
        delta_theta_e_sol = 12  # (K)
    else:
        delta_theta_e_sol = np.nan()
        print('Error! Unknown window to wall ratio')

    return delta_theta_e_sol


def calc_delta_theta_int_inc_heating(bpr):
    """
    Model of losses in the emission and control system for space heating and cooling.

    Correction factor for the heating and cooling setpoints. Extracted from EN 15316-2

    (see cea\databases\CH\Systems\emission_systems.xls for valid values for the heating and cooling system values)

    T0 means there's no heating/cooling systems installed, therefore, also no control systems for heating/cooling.
    In short, when the input system is T0, the output set point correction should be 0.0.
    So if there is no cooling systems, the setpoint_correction_for_space_emission_systems function input: (T1, T0, T1) (type_hs, type_cs, type_ctrl),
    return should be (2.65, 0.0), the control system is only specified for the heating system.
    In another case with no heating systems: input: (T0, T3, T1) return: (0.0, -2.0), the control system is only
    specified for the heating system.

    :param bpr: BuildingPropertiesRow 
    :type bpr: BuildingPropertiesRow object

    :returns: delta T to correct the set point temperature for heating
    :rtype: double
    """
    __author__ = ["Shanshan Hsieh","Gabriel Happle"]
    __credits__ = ["Shanshan Hsieh", "Daren Thomas"]

    try:
        delta_theta_int_inc_heating = 0.0 if bpr.hvac['type_hs'] == 'T0' else (bpr.hvac['dT_Qhs'] + bpr.hvac['dThs_C'])

    except KeyError:
        raise ValueError(
            'Invalid system / control combination: %s, %s' % (bpr.hvac['type_hs'], bpr.hvac['type_ctrl']))

    return delta_theta_int_inc_heating


def calc_delta_theta_int_inc_cooling(bpr):
    """
    Model of losses in the emission and control system for space heating and cooling.

    Correction factor for the heating and cooling setpoints. Extracted from EN 15316-2

    (see cea\databases\CH\Systems\emission_systems.xls for valid values for the heating and cooling system values)

    T0 means there's no heating/cooling systems installed, therefore, also no control systems for heating/cooling.
    In short, when the input system is T0, the output set point correction should be 0.0.
    So if there is no cooling systems, the setpoint_correction_for_space_emission_systems function input: (T1, T0, T1) (type_hs, type_cs, type_ctrl),
    return should be (2.65, 0.0), the control system is only specified for the heating system.
    In another case with no heating systems: input: (T0, T3, T1) return: (0.0, -2.0), the control system is only
    specified for the heating system.

    :param bpr: BuildingPropertiesRow 
    :type bpr: BuildingPropertiesRow object

    :returns: delta T to correct the set point temperature for cooling
    :rtype: double
    """
    __author__ = ["Shanshan Hsieh","Gabriel Happle"]
    __credits__ = ["Shanshan Hsieh", "Daren Thomas"]

    try:

        delta_theta_int_inc_cooling = 0.0 if bpr.hvac['type_cs'] == 'T0' else (bpr.hvac['dT_Qcs'] + bpr.hvac['dTcs_C'])
    except KeyError:
        raise ValueError(
            'Invalid system / control combination: %s, %s' % (bpr.hvac['type_cs'], bpr.hvac['type_ctrl']))

    return delta_theta_int_inc_cooling

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


def calc_q_em_ls_cooling(bpr, tsd, hoy):
    """
    calculation procedure for space emissions losses in the cooling case [prEN 15316-2:2014]

    :return:
    """

    # get properties
    cooling_system = bpr.hvac['type_cs']
    control_system = bpr.hvac['type_ctrl']

    theta_e = tsd['T_ext'][hoy]
    theta_int_ini = tsd['theta_a'][hoy]
    q_em_out = tsd['Qcs_sen_sys'][hoy]

    q_em_max = -bpr.hvac['Qcsmax_Wm2'] * bpr.rc_model['Af']

    delta_theta_int_inc = calc_delta_theta_int_inc_cooling(cooling_system, control_system)

    theta_int_inc = calc_theta_int_inc(theta_int_ini, delta_theta_int_inc)

    theta_e_comb = calc_theta_e_comb_cooling(theta_e, bpr)

    return calc_q_em_ls(q_em_out, delta_theta_int_inc, theta_int_inc, theta_e_comb, q_em_max)


def calc_q_em_ls_heating(bpr, tsd, hoy):
    """
    calculation procedure for space emissions losses in the heating case [prEN 15316-2:2014]

    :return:
    """

    # get properties
    heating_system = bpr.hvac['type_hs']
    control_system = bpr.hvac['type_ctrl']

    theta_e = tsd['T_ext'][hoy]
    theta_int_ini = tsd['theta_a'][hoy]
    q_em_out = tsd['Qhs_sen_sys'][hoy]

    q_em_max = bpr.hvac['Qhsmax_Wm2'] * bpr.rc_model['Af']

    delta_theta_int_inc = calc_delta_theta_int_inc_heating(heating_system, control_system)

    theta_int_inc = calc_theta_int_inc(theta_int_ini, delta_theta_int_inc)

    theta_e_comb = calc_theta_e_comb_heating(theta_e)

    return calc_q_em_ls(q_em_out, delta_theta_int_inc, theta_int_inc, theta_e_comb, q_em_max)


def calc_q_em_ls(q_em_out, delta_theta_int_inc, theta_int_inc, theta_e_comb, q_em_max):

    """
    Eq. (8) in [prEN 15316-2:2014]

    With modification of capping emission losses at system capacity [Happle 01/2017]

    :param q_em_out: heating power of emission system (W)
    :param delta_theta_int_inc: delta temperature caused by all losses (K)
    :param theta_int_inc: equivalent room temperature (°C)
    :param theta_e_comb: ?comb? outdoor temperature (°C)
    :return:
    """

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

    :param theta_int_ini:
    :return:
    """

    return theta_int_ini + delta_theta_int_inc


def calc_theta_e_comb_heating(theta_e):
    """
    Eq. (9) in [prEN 15316-2:2014]

    :return:
    """

    return theta_e


def calc_theta_e_comb_cooling(theta_e, bpr):
    """
    Eq. (10) in [prEN 15316-2:2014]

    :return:
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


control_delta_heating = {'T1': 2.5, 'T2': 1.2, 'T3': 0.9, 'T4': 1.8}
control_delta_cooling = {'T1': -2.5, 'T2': -1.2, 'T3': -0.9, 'T4': -1.8}
system_delta_heating = {'T0': 0.0, 'T1': 0.15, 'T2': -0.1, 'T3': -1.1, 'T4': -0.9}
system_delta_cooling = {'T0': 0.0, 'T1': 0.5, 'T2': 0.7, 'T3': 0.5}


def calc_delta_theta_int_inc_heating(heating_system, control_system):
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

    :param heating_system: The heating system used. Valid values: T0, T1, T2, T3, T4
    :type heating_system: str

    :param cooling_system: The cooling system used. Valid values: T0, T1, T2, T3
    :type cooling_system: str

    :param control_system: The control system used. Valid values: T1, T2, T3, T4 - as defined in the
        contributors manual under Databases / Archetypes / Building Properties / Mechanical systems.
        T1 for none, T2 for PI control, T3 for PI control with optimum tuning, and T4 for room temperature control
        (electromagnetically/electronically).
    :type control_system: str

    :returns: two delta T to correct the set point temperature, dT_heating, dT_cooling
    :rtype: tuple(double, double)
    """
    __author__ = "Shanshan Hsieh"
    __credits__ = ["Shanshan Hsieh", "Daren Thomas"]

    try:
        delta_theta_int_inc_heating = 0.0 if heating_system == 'T0' else (control_delta_heating[control_system] +
                                                             system_delta_heating[heating_system])

    except KeyError:
        raise ValueError(
            'Invalid system / control combination: %s, %s' % (heating_system, control_system))

    return delta_theta_int_inc_heating


def calc_delta_theta_int_inc_cooling(cooling_system, control_system):
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

    :param heating_system: The heating system used. Valid values: T0, T1, T2, T3, T4
    :type heating_system: str

    :param cooling_system: The cooling system used. Valid values: T0, T1, T2, T3
    :type cooling_system: str

    :param control_system: The control system used. Valid values: T1, T2, T3, T4 - as defined in the
        contributors manual under Databases / Archetypes / Building Properties / Mechanical systems.
        T1 for none, T2 for PI control, T3 for PI control with optimum tuning, and T4 for room temperature control
        (electromagnetically/electronically).
    :type control_system: str

    :returns: two delta T to correct the set point temperature, dT_heating, dT_cooling
    :rtype: tuple(double, double)
    """
    __author__ = "Shanshan Hsieh"
    __credits__ = ["Shanshan Hsieh", "Daren Thomas"]

    try:

        delta_theta_int_inc_cooling = 0.0 if cooling_system == 'T0' else (control_delta_cooling[control_system] +
                                                             system_delta_cooling[cooling_system])
    except KeyError:
        raise ValueError(
            'Invalid system / control combination: %s, %s' % (cooling_system, control_system))

    return delta_theta_int_inc_cooling




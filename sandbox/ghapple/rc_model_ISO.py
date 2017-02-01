# -*- coding: utf-8 -*-


from __future__ import division
import numpy as np
from sandbox.ghapple import helpers as h
from cea.demand import sensible_loads as sl
from cea import globalvar
import control

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def calc_h_ve_adj(tsd, hoy, gv):
    """
    calculate Hve,adj according to ISO 13790

    Parameters
    ----------
    q_m_mech : air mass flow from mechanical ventilation (kg/s)
    q_m_nat : air mass flow from windows and leakages and other natural ventilation (kg/s)
    temp_ext : exterior air temperature (°C)
    temp_sup : ventilation system supply air temperature (°C), e.g. after HEX
    temp_zone_set : zone air temperature set point (°C)
    gv : globalvars

    Returns
    -------
    Hve,adj in (W/K)

    """

    # get parameters
    temp_ext = tsd['T_ext'][hoy]
    temp_sup = tsd['theta_ve_mech'][hoy]
    temp_zone_set = tsd['Ta'][hoy - 1] if not tsd['Ta'][hoy - 1] else tsd['T_ext'][hoy - 1]  # get zone set point
    q_m_mech = tsd['m_ve_mech'][hoy]
    q_m_nat = tsd['m_ve_inf_simple'][hoy] + tsd['m_ve_window'][hoy]


    c_p_air = gv.Cpa  # (kJ/(kg*K)) # TODO: maybe dynamic heat capacity of air f(temp)

    if abs(temp_sup - temp_ext) == 0:
        b_mech = 1

    elif (temp_zone_set - temp_ext) == 0:
        b_mech = 1 # prevent division by zero for room temperature = room temperature (heat recovery has no effect)

    else:
        eta_hru = (temp_sup - temp_ext) / (temp_zone_set - temp_ext)  # Eq. (28) in ISO 13970
        frac_hru = 1
        b_mech = (1 - frac_hru * eta_hru)  # Eq. (27) in ISO 13970

    tsd['h_ve_adj'][hoy] = (b_mech * q_m_mech + q_m_nat) * c_p_air * 1000  # (W/K), Eq. (21) in ISO 13970

    if np.isnan(tsd['h_ve_adj'][hoy]):
        tsd['h_ve_adj'][hoy]

    return

def calc_theta_m_t(theta_m_prev, c_m, h_tr_3, h_tr_em, phi_m_tot):

    # (C.4) in [C.3 ISO 13790]

    theta_m_t = ((theta_m_prev*((c_m/3600)-0.5*(h_tr_3+h_tr_em))) + phi_m_tot) / ((c_m/3600)+0.5*(h_tr_3+h_tr_em))

    return theta_m_t


def calc_phi_m_tot(phi_m, h_tr_em, theta_e, h_tr_3, phi_st, h_tr_w, h_tr_1, phi_ia, phi_hc_nd, h_ve_adj, h_tr_2 ):

    # (C.5) in [C.3 ISO 13790]
    # h_ve = h_ve_adj and theta_sup = theta_e [9.3.2 ISO 13790]

    phi_m_tot = phi_m + h_tr_em*theta_e + \
                h_tr_3*(phi_st + h_tr_w*theta_e+h_tr_1*(((phi_ia+phi_hc_nd)/h_ve_adj)+theta_e))/h_tr_2


    return phi_m_tot


def calc_h_tr_1(h_ve_adj, h_tr_is):

    # (C.6) in [C.3 ISO 13790]

    h_tr_1 = 1/(1/h_ve_adj + 1/h_tr_is)

    return h_tr_1


def calc_h_tr_2(h_tr_1, h_tr_w):

    # (C.7) in [C.3 ISO 13790]

    h_tr_2 = h_tr_1 + h_tr_w

    return h_tr_2


def calc_h_tr_3(h_tr_2, h_tr_ms):

    # (C.8) in [C.3 ISO 13790]

    h_tr_3 = 1/(1/h_tr_2 + 1/h_tr_ms)

    return h_tr_3


def calc_theta_m(theta_m_t, theta_m_prev):

    # (C.9) in [C.3 ISO 13790]
    theta_m = (theta_m_t+theta_m_prev)/2

    return theta_m


def calc_theta_s(h_tr_ms, theta_m, phi_st, h_tr_w, theta_e, h_tr_1, phi_ia, phi_hc_nd, h_ve_adj):

    # (C.10) in [C.3 ISO 13790]
    # h_ve = h_ve_adj and theta_sup = theta_e [9.3.2 ISO 13790]
    theta_s = (h_tr_ms*theta_m+phi_st+h_tr_w*theta_e+h_tr_1*(theta_e+(phi_ia+phi_hc_nd)/h_ve_adj)) / \
              (h_tr_ms+h_tr_w+h_tr_1)

    return theta_s


def calc_theta_air(h_tr_is, theta_s, h_ve_adj, theta_e, phi_ia, phi_hc_nd):
    # (C.11) in [C.3 ISO 13790]
    # h_ve = h_ve_adj and theta_sup = theta_e [9.3.2 ISO 13790]

    theta_air = (h_tr_is * theta_s + h_ve_adj * theta_e + phi_ia + phi_hc_nd) / (h_tr_is + h_ve_adj)

    return theta_air


def calc_theta_op(theta_air, theta_s):

    # (C.12) in [C.3 ISO 13790]
    theta_op = 0.3 * theta_air + 0.7 * theta_s

    return theta_op


def calc_temperatures_crank_nicholson( phi_hc_nd, bpr, tsd, hoy ):

    # calculates air temperature and operative temperature for a given heating/cooling load
    # section C.3 in [C.3 ISO 13790]

    # GET PROPERTIES
    #

    # building thermal properties at previous time step
    # +++++++++++++++++++++++++++++++++++++++++++++++++
    theta_m_prev = np.float64(tsd['Tm'][hoy - 1]) if not np.isnan(tsd['Tm'][hoy - 1]) else np.float64(
        tsd['T_ext'][hoy - 1])

    # environmental properties
    # ++++++++++++++++++++++++
    theta_e = np.float64(tsd['T_ext'][hoy])

    # R-C-model properties
    # ++++++++++++++++++++
    phi_m = np.float64(tsd['I_m'][hoy])
    phi_ia = np.float64(tsd['I_ia'][hoy])
    phi_st = np.float64(tsd['I_st'][hoy])

    c_m = np.float64(bpr.rc_model['Cm'])

    h_tr_em = np.float64(bpr.rc_model['Htr_em'])
    h_tr_w = np.float64(bpr.rc_model['Htr_w'])
    h_ve_adj = tsd['h_ve_adj'][hoy]
    h_tr_ms = np.float64(bpr.rc_model['Htr_ms'])
    h_tr_is = np.float64(bpr.rc_model['Htr_is'])

    h_tr_1 = calc_h_tr_1(h_ve_adj, h_tr_is)
    h_tr_2 = calc_h_tr_2(h_tr_1, h_tr_w)
    h_tr_3 = calc_h_tr_3(h_tr_2, h_tr_ms)

    #
    # CALCULATION PROCEDURE


    phi_m_tot = calc_phi_m_tot(phi_m, h_tr_em, theta_e, h_tr_3, phi_st, h_tr_w, h_tr_1, phi_ia, phi_hc_nd, h_ve_adj,
                               h_tr_2)

    theta_m_t = calc_theta_m_t(theta_m_prev, c_m, h_tr_3, h_tr_em, phi_m_tot)

    theta_m = calc_theta_m(theta_m_t, theta_m_prev)

    theta_s = calc_theta_s(h_tr_ms, theta_m, phi_st, h_tr_w, theta_e, h_tr_1, phi_ia, phi_hc_nd, h_ve_adj)

    theta_air = calc_theta_air(h_tr_is, theta_s, h_ve_adj, theta_e, phi_ia, phi_hc_nd)

    theta_op = calc_theta_op(theta_air, theta_s)

    if np.isnan(theta_m_t):
        theta_m_t

    return theta_m_t, theta_air, theta_op, theta_s




def has_heating_demand(bpr, tsd, hoy):

    # TODO get setpoints
    theta_int_h_set = np.float64(tsd['ta_hs_set'][hoy])  # TODO: rename

    # step 1 in section C.4.2 in [C.3 ISO 13790]

    # set heating cooling power to zero
    phi_hc_nd = 0

    # only air temperature is used for the check
    theta_air = calc_temperatures_crank_nicholson(phi_hc_nd, bpr, tsd, hoy)[1]

    if theta_int_h_set <= theta_air:
        return False

    elif theta_air < theta_int_h_set:
        return True


def has_cooling_demand(bpr, tsd, hoy):

    # TODO get setpoints
    theta_int_c_set = np.float64(tsd['ta_cs_set'][hoy])  # TODO: rename

    # step 1 in section C.4.2 in [C.3 ISO 13790]

    # set heating cooling power to zero
    phi_hc_nd = 0

    # only air temperature is used for the check
    theta_air = calc_temperatures_crank_nicholson(phi_hc_nd, bpr, tsd, hoy)[1]

    if theta_int_c_set >= theta_air:
        return False

    elif theta_air > theta_int_c_set:
        return True


def calc_phi_hc_nd_un(phi_hc_nd_10, theta_air_set, theta_air_0, theta_air_10):

    # calculates unrestricted heating power
    # (C.13) in [C.3 ISO 13790]

    phi_hc_nd_un = phi_hc_nd_10*(theta_air_set - theta_air_0)/(theta_air_10 - theta_air_0)

    return phi_hc_nd_un


def calc_phi_hc_ac_heating(bpr, tsd, hoy):

    # Crank-Nicholson calculation procedure if heating/cooling system is active
    # Step 1 - Step 4 in Section C.4.2 in [C.3 ISO 13790]

    # Step 1:
    phi_hc_nd_0 = 0
    temp_rc_0 = calc_temperatures_crank_nicholson(phi_hc_nd_0, bpr, tsd, hoy)
    theta_air_0 = temp_rc_0[1]

    # Step 2:
    theta_int_set = tsd['ta_hs_set'][hoy] # TODO: get setpoint
    af = bpr.rc_model['Af'] # TODO: get A_f, check wether Aef??

    theta_air_set = theta_int_set
    phi_hc_nd_10 = 10 * af

    temp_rc_10 = calc_temperatures_crank_nicholson(phi_hc_nd_10, bpr, tsd, hoy)
    theta_air_10 = temp_rc_10[1]
    phi_hc_nd_un = calc_phi_hc_nd_un(phi_hc_nd_10,theta_air_set, theta_air_0, theta_air_10)

    # Step 3:
    phi_h_max = bpr.hvac['Qhsmax_Wm2'] * af # TODO: get max heating power

    if phi_hc_nd_un <= phi_h_max:

        phi_hc_nd_ac = phi_hc_nd_un
        theta_air_ac = theta_air_set

    # Step 4:
    elif phi_hc_nd_un > phi_h_max: # necessary heating power exceeds maximum available power

        phi_hc_nd_ac = phi_h_max

    else: # unknown situation

        phi_hc_nd_ac = 0
        print('ERROR: unknown radiative heating/cooling system status')


    # calculate system temperatures for Step 3/Step 4
    temp_ac = calc_temperatures_crank_nicholson(phi_hc_nd_ac, bpr, tsd, hoy)

    theta_m_t_ac = temp_ac[0]
    theta_air_ac = temp_ac[1]  # should be the same as theta_air_set in the first case
    theta_op_ac = temp_ac[2]
    theta_s_ac = temp_ac[3]

    # exit calculation
    return theta_m_t_ac, theta_air_ac, theta_op_ac, theta_s_ac, phi_hc_nd_ac


def calc_phi_hc_ac_cooling(bpr, tsd, hoy):

    # Crank-Nicholson calculation procedure if cooling system is active
    # Step 1 - Step 4 in Section C.4.2 in [C.3 ISO 13790]

    # Step 1:
    phi_hc_nd_0 = 0
    temp_rc_0 = calc_temperatures_crank_nicholson(phi_hc_nd_0, bpr, tsd, hoy)
    theta_air_0 = temp_rc_0[1]

    # Step 2:
    theta_int_set = tsd['ta_cs_set'][hoy]
    af = bpr.rc_model['Af'] # TODO: get A_f, check wether Aef??

    theta_air_set = theta_int_set
    phi_hc_nd_10 = 10 * af

    temp_rc_10 = calc_temperatures_crank_nicholson(phi_hc_nd_10, bpr, tsd, hoy)
    theta_air_10 = temp_rc_10[1]
    phi_hc_nd_un = calc_phi_hc_nd_un(phi_hc_nd_10,theta_air_set, theta_air_0, theta_air_10)

    # Step 3:
    phi_c_max = -bpr.hvac['Qcsmax_Wm2'] * af # TODO: get max cooling power

    if phi_c_max <= phi_hc_nd_un:

        phi_hc_nd_ac = phi_hc_nd_un
        theta_air_ac = theta_air_set

    # Step 4:
    elif phi_hc_nd_un < phi_c_max: # necessary cooling power exceeds maximum available power

        phi_hc_nd_ac = phi_c_max

    else: # unknown situation

        phi_hc_nd_ac = 0
        print('ERROR: unknown radiative heating/cooling system status')

    # calculate system temperatures for Step 3/Step 4
    temp_ac = calc_temperatures_crank_nicholson(phi_hc_nd_ac, bpr, tsd, hoy)

    theta_m_t_ac = temp_ac[0]
    theta_air_ac = temp_ac[1]  # should be the same as theta_air_set in the first case
    theta_op_ac = temp_ac[2]
    theta_s_ac = temp_ac[3]

    # exit calculation
    return theta_m_t_ac, theta_air_ac, theta_op_ac, theta_s_ac, phi_hc_nd_ac






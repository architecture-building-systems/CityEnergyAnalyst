# -*- coding: utf-8 -*-


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

'''
RC model calculations according to sia 2044

Merkblatt 2044 Kilimatisierte Gebauede - Standard-Berechnungsverfahren fuer den Leistungs-und Energiebedarf
'''

# SIA 2044 constants
h_cv_i = 2.5 # (W/m2K) (4) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
h_r_i = 5.5 # (W/m2K) (5) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
h_ic  = 9.1 # (W/m2K) (6) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
f_sa = 0.1 # (-) section 2.1.4 in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
f_r_l = 0.7 # (-) section 2.1.4 in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
f_r_p = 0.5 # (-) section 2.1.4 in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
f_r_a = 0.2 # (-) section 2.1.4 in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011


def calc_h_mc():

    # (7) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011

    h_mc = h_ic * a_m

    return h_mc

def calc_h_ac():

    # (8) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011

    h_ac = a_t / (1/h_cv_i - 1/h_ic)

    return h_ac


def calc_h_op_m():

    # (9) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    h_op_m = a_j_m * u_j
    # TODO: this formula in the future should take specific properties of the location of the building into account
    # e.g. adiabatic building elements with U = 0

    return h_op_m


def calc_h_em():

    # (10) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    h_em = 1 / (1 / h_op_m - 1 / h_mc)

    return h_em


def calc_h_j_em():

    # (11) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    h_j_em = (h_em * a_j_m * u_j) / h_op_m

    # TODO: this formula in the future should take specific properties of the location of the building into account
    # e.g. adiabatic building elements with U = 0

    return h_j_em


def calc_h_ec():


    h_ec = a_j_l * u_j
    # TODO: this formula in the future should take specific properties of the location of the building into account
    # e.g. adiabatic building elements with U = 0
    # TODO: can incorporate point or linear thermal bridges



def calc_h_ea():

    # (13) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    # adapted for mass flows instead of volume flows
    h_ea = (m_v_sys + m_v_w + m_v_inf) * cp

    return h_ea


def calc_phi_a():

    # (14) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    # Gabriel Happle 01.12.2016

    # standard assumptions
    f_sa = 0.1
    f_r_l = 0.7
    f_r_p = 0.5
    f_r_a = 0.2

    phi_a = f_sa * phi_s + (1-f_r_l)*phi_i_l + (1-f_r_p) * phi_i_p +(1-f_r_a)*phi_i_a + phi_hc_cv

    return phi_a

def calc_phi_c():

    # (15) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    # Gabriel Happle 01.12.2016

    # standard assumptions
    f_sa = 0.1
    f_r_l = 0.7
    f_r_p = 0.5
    f_r_a = 0.2

    phi_c = f_ic * (f_r_l*phi_i_l+f_r_p*phi_i_p+f_r_a*phi_i_a + phi_hc_r) + (1-f_sa)*f_sc*phi_s

    return phi_c

def calc_phi_m():

    # (16) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    # Gabriel Happle 01.12.2016

    # standard assumption
    f_sa = 0.1
    f_r_l = 0.7
    f_r_p = 0.5
    f_r_a = 0.2
    phi_m = f_im * (f_r_l*phi_i_l+f_r_p*phi_i_p+f_r_a*phi_i_a + phi_hc_r) + (1-f_sa)*f_sm*phi_s

    return phi_m


def calc_f_ic(bpr):

    # (17) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    # Gabriel Happle 01.12.2016

    # get values from bpr
    a_t = bpr.rc_model['Atot']
    a_m = bpr.rc_model['Am']
    h_ec = bpr.rc_model['Htr_w']
    h_ic = 9.1  # in (W/m2K) from (8) in SIA 2044

    f_ic = (a_t - a_m - h_ec / h_ic) / a_t

    return f_ic


def calc_f_sc(bpr):

    # (18) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    # Gabriel Happle 01.12.2016

    # get values from bpr
    a_t = bpr.rc_model['Atot']
    a_m = bpr.rc_model['Am']
    a_w = bpr.rc_model['Aw']
    h_ec = bpr.rc_model['Htr_w']
    h_ic = 9.1  # in (W/m2K) from (8) in SIA 2044

    f_sc = (a_t-a_m-a_w-h_ec/h_ic) / (a_t - a_w)

    return f_sc


def calc_f_im(bpr):

    # (19) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    # Gabriel Happle 01.12.2016

    # get values from bpr
    a_t = bpr.rc_model['Atot']
    a_m = bpr.rc_model['Am']

    f_im = a_m / a_t

    return f_im

def calc_f_sm(bpr):

    # (20) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    # Gabriel Happle 01.12.2016

    # get values from bpr
    a_t = bpr.rc_model['Atot']
    a_m = bpr.rc_model['Am']
    a_w = bpr.rc_model['Aw']

    f_sm = a_m / (a_t - a_w)

    return f_sm


def calc_theta_ea():

    # (21) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    # adjusted for mass flows instead of volume flows and simplified by (rho*cp)/(rho*cp) = 1
    # Gabriel Happle 01.12.2016

    theta_ea = (m_v_sys * theta_v_sys + (m_v_w + m_v_inf) * theta_e) / (m_v_sys + m_v_w + m_v_inf)

    return theta_ea


def calc_theta_ec():

    # (22) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011

    theta_ec = a_j_l * u_j * theta_e_j / h_ec

    # TODO: this formula in the future should take specific properties of the location of the building into account
    # e.g. adiabatic building elements with U = 0

    # TODO: theta_e_j is depending on adjacent space to surface (outdoor, adiabatic, ground, etc.)

    return theta_ec


def calc_theta_em():

    # (23) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011

    theta_em = h_j_em * theta_e_j / h_em

    # TODO: this formula in the future should take specific properties of the location of the building into account
    # e.g. adiabatic building elements with U = 0

    # TODO: theta_e_j is depending on adjacent space to surface (outdoor, adiabatic, ground, etc.)

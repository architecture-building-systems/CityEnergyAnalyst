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

class SIA2044RCModel:

    ''' RC model calculations according to sia 2044
    Merkblatt 2044 Kilimatisierte Gebauede - Standard-Berechnungsverfahren fuer den Leistungs-und Energiebedarf '''


    def ___init___(self):

        # SIA 2044 constants
        self.h_cv_i = 2.5 # (W/m2K) (4) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
        self.h_r_i = 5.5 # (W/m2K) (5) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
        self.h_ic  = 9.1 # (W/m2K) (6) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
        self.f_sa = 0.1 # (-) section 2.1.4 in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
        self.f_r_l = 0.7 # (-) section 2.1.4 in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
        self.f_r_p = 0.5 # (-) section 2.1.4 in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
        self.f_r_a = 0.2 # (-) section 2.1.4 in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011

        # default values
        self.f_hc_cv = 1 # (-) convective fraction of heating system, section 3.1.8

        # calculate parameters
        self.h_mc = self.calc_h_mc()
        self.h_ac = self.calc_h_ac()
        self.h_op = self.calc_h_op()
        self.h_em = self.calc_h_em()

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # 2.1.3
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def calc_h_mc(self):

        # (7) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
        h_mc = self.h_ic * a_m
        return h_mc


    def calc_h_ac(self):

        # (8) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
        h_ac = a_t / (1 / self.h_cv_i - 1 / self.h_ic)
        return h_ac


    def calc_h_op_m(self):

        # (9) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
        h_op_m = a_j_m * u_j
        # TODO: this formula in the future should take specific properties of the location of the building into account
        # e.g. adiabatic building elements with U = 0

        return h_op_m


    def calc_h_em(self):

        # (10) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
        h_em = 1 / (1 / self.h_op_m - 1 / self.h_mc)
        return h_em


    def calc_h_j_em(self):

        # (11) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
        h_j_em = (self.h_em * a_j_m * u_j) / self.h_op_m

        # TODO: this formula in the future should take specific properties of the location of the building into account
        # e.g. adiabatic building elements with U = 0

        return h_j_em


    def calc_h_ec(self):

        h_ec = a_j_l * u_j
        # TODO: this formula in the future should take specific properties of the location of the building into account
        # e.g. adiabatic building elements with U = 0
        # TODO: can incorporate point or linear thermal bridges

        return h_ec

    def calc_h_ea(self):

        # (13) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
        # adapted for mass flows instead of volume flows
        h_ea = (m_v_sys + m_v_w + m_v_inf) * cp

        return h_ea


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# 2.1.4
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


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

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# 2.1.5
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


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

    return theta_em


def calc_theta_e_star():

    # (24) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    #

    # standard values for calculation
    h_e_load_and_temp = 13.5  # (W/m2K) for load and temperature calculation
    h_e_energy = 23  # (W/m2K) for energy demand calculation

    f_r_roof = 1  # (-)
    f_r_wall = 0.5  # (-)
    h_r = 5.5  # (-)
    delta_t_er = 11  # (K)

    if is_roof(surface):
        f_r = f_r_roof
    elif is_wall(surface):
        f_r = f_r_wall
    else:
        raise()

    if is_energy_calculation(calculation):
        h_e = h_e_energy
    elif is_load_or_temp_calculation(calculation):
        h_e = h_e_load_and_temp
    else:
        raise()


    theta_e_star = theta_e + (alpha_s * i_s_i) / h_e - (f_r * h_r * epsilon_0 * delta_t_er) / h_e

    return theta_e_star

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# 2.1.6
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def calc_theta_m_t():

    # (25) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011

    theta_m_t = (theta_m_t_1 * (c_m - 0.5 * (h_3 + h_em)) + phi_m_tot) / (c_m + 0.5 * (h_3 + h_em))

    return theta_m_t


def calc_h_1():

    # (26) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011

    h_1 = 1 / (1 / h_ea + 1 / h_ac)

    return h_1


def calc_h_2():

    # (27) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011

    h_2 = h_1 + h_ec

    return h_2


def calc_h_3():

    # (28) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011

    h_3 = 1 / (1 / h_2 + 1 / h_mc)

    return h_3


def calc_phi_m_tot():

    # (29) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011

    phi_m_tot = phi_m + h_em * theta_em + (h_3 * (phi_c + h_ec * theta_ec + h_1 * (phi_a / h_ea + theta_ea))) / h_2

    return phi_m_tot


def calc_theta_m():

    # (30) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011

    theta_m = (theta_m_t + theta_m_t_1) / 2

    return theta_m


def calc_theta_c():

    # (31) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011

    theta_c = (h_mc * theta_m + phi_c + h_ec * theta_ec + h_1 * (phi_a / h_ea + theta_ea)) / (h_mc + h_ec + h_1)

    return theta_c


def calc_theta_a():

    # (32) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011

    theta_a = (h_ac * theta_c + h_ea * theta_ea + phi_a) / (h_ac + h_ea)

    return theta_a


def calc_theta_o():

    # (33) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011

    theta_o = theta_a * 0.31 + theta_c * 0.69

    return theta_o

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# 2.2.7
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def calc_phi_hc_cv():

    # (58) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    phi_hc_cv = f_hc_cv * phi_hc

    return phi_hc_cv


def calc_phi_hc_r():

    # (59) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    phi_hc_r = (1 - f_hc_cv) * phi_hc

    return phi_hc_r


def calc_theta_tabs_su():

    # (60) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    theta_tabs_su = theta_tabs_su_max - (theta_tabs_su_max - theta_tabs_su_min) * (theta_e -  theta_e_min)/(theta_e_max - theta_e_min)

    return theta_tabs_su


def calc_phi_tabs():

    # (61) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    phi_tabs = h_tabs * (theta_tabs_su - theta_m_t_1)

    return phi_tabs


def calc_h_tabs():

    # (62) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011

    # typical values
    a_tabs = 0.8 * a_ngf
    r_tabs = 0.08  # (m2K/W)

    h_tabs = a_tabs / r_tabs

    return h_tabs


def calc_phi_m_tot_tabs():

    # (63) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011

    phi_m_tot = calc_phi_m_tot() + phi_tabs

    return phi_m_tot


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# 2.3.2
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def calc_rc_model_temperatures(phi_hc):



def has_heating_demand():



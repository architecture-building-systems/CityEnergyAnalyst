# -*- coding: utf-8 -*-


from __future__ import division
import numpy as np
from sandbox.ghapple import helpers as h
from cea.demand import sensible_loads as sl
from cea import globalvar
from sandbox.ghapple import control as c
from cea.utilities import physics as p

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


# THIS SCRIPT IS USED TO CALCULATE ALL VENTILATION PROPERTIES (AIR FLOWS AND THEIR TEMPERATURES)
# FOR CALCULATION OF THE VENTILATION HEAT TRANSFER H_VE USED IN THE ISO 13790 CALCULATION PROCEDURE


def calc_m_ve_mech(bpr, tsd, hoy):
    # input is schedule
    # if has mechanical ventilation and not night flushing : m_ve_mech = m_ve_schedule
    #
    # TODO: code
    # TODO: documentation

    if c.is_mech_ventilation_active() and not c.is_night_flushing_active(bpr, tsd, hoy):

        m_ve_mech = max(tsd['m_ve_required'][hoy] - tsd['m_ve_inf_simple'][hoy], 0)  # mechanical ventilation fulfills requirement (similar to CO2 sensor)
        # TODO: check mech ventilation rule - maybe: required + infiltration

    elif c.is_mech_ventilation_active() and c.is_night_flushing_active(bpr, tsd, hoy):

        # night flushing according to strategy
        m_ve_mech = (tsd['m_ve_required'][hoy] - tsd['m_ve_inf_simple'][hoy]) * 1.3  # TODO: some night flushing rule

    elif not c.is_mech_ventilation_active():

        # mechanical ventilation is turned off
        m_ve_mech = 0

    else:

        # unknown mechanical ventilation status
        m_ve_mech = np.nan()
        print('Warning! Unknown mechanical ventilation status')

    tsd['m_ve_mech'][hoy] = m_ve_mech

    return


def calc_m_ve_window(bpr, tsd, hoy):
    # input is schedule
    # if has window ventilation and not special control : m_ve_window = m_ve_schedule
    # TODO: code
    # TODO: documentation
    if c.is_window_ventilation_active() and not c.is_night_flushing_active(bpr, tsd, hoy):

        m_ve_window = max(tsd['m_ve_required'][hoy] - tsd['m_ve_inf_simple'][hoy], 0)  # window ventilation fulfills requirement (control by occupnats similar to CO2 sensor)

    elif c.is_window_ventilation_active() and c.is_night_flushing_active(bpr, tsd, hoy):

        m_ve_window = 999  # TODO: implement some night flushing rule

    elif not c.is_window_ventilation_active():

        m_ve_window = 0

    else:
        # unknown window ventilation status
        m_ve_window = np.nan()
        print('Warning! Unknown window ventilation status')

    tsd['m_ve_window'][hoy] = m_ve_window

    return


def calc_m_ve_leakage():
    # requires iteration
    # TODO: code
    # TODO: documentation
    return


def calc_m_ve_leakage_simple(bpr, tsd, gv):
    # TODO: code
    # TODO: documentation



    # 'flat rate' infiltration considered for all buildings

    # get properties
    n50 = bpr.architecture['n50']
    area_f = bpr.rc_model['Af']

    # estimation of infiltration air volume flow rate according to Eq. (3) in DIN 1946-6
    n_inf = 0.5 * n50 * (gv.delta_p_dim/50) ** (2/3)  # [air changes per hour] m3/h.m2
    infiltration = gv.hf * area_f * n_inf * 0.000277778  # m3/s

    tsd['m_ve_inf_simple'] = infiltration * p.calc_rho_air(tsd['T_ext'][:])  # (kg/s)

    return


def calc_theta_ve_mech(bpr, tsd, hoy):
    # if no heat recovery: theta_ve_mech = theta_ext
    # TODO: code
    # TODO: documentation
    if c.is_hex_active():

        theta_ve_mech = tsd['T_ext'][hoy] # TODO: some HEX formula

    elif not c.is_hex_active():

        theta_ve_mech = tsd['T_ext'][hoy]

    else:

        theta_ve_mech = np.nan
        print('Warning! Unknown HEX  status')

    tsd['theta_ve_mech'][hoy] = theta_ve_mech

    return


def calc_m_ve_required(bpr, tsd):

    tsd['m_ve_required'] = tsd['people'] * bpr.comfort['Ve_lps'] * p.calc_rho_air(tsd['T_ext'][:]) * 0.001  # kg/s

    return
# -*- coding: utf-8 -*-


from __future__ import division
import numpy as np
from sandbox.ghapple import helpers as h
from cea.demand import sensible_loads as sl
from cea import globalvar
from sandbox.ghapple import control as c

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

    if c.is_mech_ventilation_active() and not c.is_night_flushing_active(hoy, tsd, bpr):

        m_ve_mech = tsd['qm_ve_req'][hoy]  # mechanical ventilation fulfills requirement (similar to CO2 sensor) # TODO: remove infiltration from schedule

    elif c.is_mech_ventilation_active() and c.is_night_flushing_active(hoy, tsd, bpr):

        # night flushing according to strategy
        m_ve_mech = tsd['qm_ve_req'][hoy] * 1.3 # TODO: some night flushing rule

    elif not c.is_mech_ventilation_active():

        # mechanical ventilation is turned off
        m_ve_mech = 0

    else:

        # unknown mechanical ventilation status
        m_ve_mech = np.nan()
        print('Warning! Unknown mechanical ventilation status')

    tsd['m_ve_mech'][hoy] = m_ve_mech

    return


def calc_m_ve_window():
    # input is schedule
    # if has window ventilation and not special control : m_ve_window = m_ve_schedule
    # TODO: code
    # TODO: documentation
    return


def calc_m_ve_leakage():
    # requires iteration
    # TODO: code
    # TODO: documentation
    return


def calc_m_ve_leakage_simple():
    # TODO: code
    # TODO: documentation
    return


def calc_theta_ve_mech():
    # if no heat recovery: theta_ve_mech = theta_ext
    # TODO: code
    # TODO: documentation
    return
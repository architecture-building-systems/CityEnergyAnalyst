# -*- coding: utf-8 -*-


from __future__ import division
import numpy as np
from sandbox.ghapple import helpers as h

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"



def has_heating_system(bpr):
    """
    determines whether a building has a heating system installed or not

    bpr : building properties row object

    bool

    """

    if bpr.hvac['type_hs'] in {'T1', 'T2', 'T3', 'T4'}:
        return True
    elif bpr.hvac['type_hs'] in {'T0'}:
        return False
    else:
        print('Error: Unknown heating system')
        return False


def heating_system_is_ac(bpr):
    """
    determines whether a building's heating system is ac or not

    bpr : building properties row object

    bool

    """

    if bpr.hvac['type_hs'] in {'T3'}:  # central ac
        return True
    elif bpr.hvac['type_hs'] in {'T0', 'T1', 'T2', 'T4'}:
        return False
    else:
        print('Error: Unknown heating system')
        return False


def heating_system_is_radiative(bpr):
    """
    determines whether a building's heating system is radiative (radiators/floor heating) or not

    bpr : building properties row object

    bool
    """

    if bpr.hvac['type_hs'] in {'T1', 'T2'}:
        return True
    elif bpr.hvac['type_hs'] in {'T0', 'T3', 'T4'}:
        return False
    else:
        print('Error: Unknown heating system')
        return False


def heating_system_is_tabs(bpr):
    """


    :param bpr:
    :return:
    """

    if bpr.hvac['type_hs'] in {'T4'}:
        return True
    elif bpr.hvac['type_hs'] in {'T0', 'T1', 'T2', 'T3'}:
        return False
    else:
        raise ValueError('Error: Unknown heating system')




def has_cooling_system(bpr):
    """
    determines whether a building has a cooling system installed or not

    bpr : building properties row object

    bool
    """

    if bpr.hvac['type_cs'] in {'T1', 'T2', 'T3'}:
        return True
    elif bpr.hvac['type_cs'] in {'T0'}:
        return False
    else:
        print('Error: Unknown cooling system')
        return False


def cooling_system_is_ac(bpr):
    """
    determines whether a building's heating system is ac or not

    bpr : building properties row object

    bool
    """

    if bpr.hvac['type_cs'] in {'T2', 'T3'}:  # mini-split ac and central ac
        return True
    elif bpr.hvac['type_cs'] in {'T0', 'T1'}:
        return False
    else:
        print('Error: Unknown cooling system')
        return False


def cooling_system_is_radiative(bpr):
    """
    determines whether a building's heating system is radiative or not

    bpr : building properties row object

    bool
    """

    if bpr.hvac['type_cs'] in {'T1'}:
        return True
    elif bpr.hvac['type_cs'] in {'T0', 'T2', 'T3'}:
        return False
    else:
        print('Error: Unknown cooling system')
        return False


def is_heating_active(hoy, bpr):
    """
    determines whether the heating system of a building is active or not at a certain hour of the year

    hoy : hour of the year
    bpr : building properties row object

    bool
    """

    if has_heating_system(bpr):

        if h.is_heatingseason_hoy(hoy):
            return True
        else:
            return False
    else:
        return False


def is_cooling_active(bpr, tsd, hoy, gv):
    """
    determines whether the cooling system of a building is active or not at a certain hour of the year

    hoy : hour of the year
    bpr : building properties row object

    bool

    """

    if has_cooling_system(bpr):
        if h.is_coolingseason_hoy(hoy):
            if cooling_system_is_radiative(bpr):
                return True
            elif cooling_system_is_ac(bpr) and tsd['T_ext'][hoy] >= gv.temp_sup_cool_hvac + 2:  # TODO: HVAC control
                return True
            elif cooling_system_is_ac(bpr) and tsd['T_ext'][hoy] < gv.temp_sup_cool_hvac + 2:  # TODO: HVAC control
                return False

        else:
            return False
    else:
        return False


def has_mech_ventilation():

    # check building properties
    # TODO: code
    return True

def has_night_flushing():

    # check building properties
    # TODO: code
    return False

def has_window_ventilation():

    # check building properties
    # TODO: code
    return True

def has_hex():

    # check building properties
    # TODO: code
    return False


def is_mech_ventilation_active():

    if has_mech_ventilation():
        # check for clock time, season, temperature and occupancy constraints
        # TODO: code
        return True

    elif not has_mech_ventilation():
        return False


def is_night_flushing_active(bpr, tsd, hoy):
    """
    determines system status (active/inactive) of night flushing system

    hoy : hour of year
    tsd : data frame with thermal loads simulation results
    bpr : building properties row object

    bool
    """

    # TODO: get night flushing building property (bpr)
    # night_flushing = True

    # TODO: get control temperatures from ? (gv?)
    if has_night_flushing():

        # check for clock time, season, temperature and occupancy constraints
        if h.is_nighttime_hoy(hoy) and h.is_coolingseason_hoy(hoy):  # clocktime condition

            temp_zone_control = 28  # TODO: make dynamic
            temp_ext_control = 26 # TODO: make dynamic (as function of zone air temperature, e.g. Ta - 2°C)

            if tsd['Ta'][hoy] > temp_zone_control and tsd['T_ext'][hoy] < temp_ext_control:  # temperature condition

                return True
            else:
                return False
        else:
            return False

    elif not has_night_flushing():
        return False


def is_window_ventilation_active():

    if has_window_ventilation():

        # TODO: code
        # check for clock time, season, temperature and occupancy constraints
        return False

    elif not has_window_ventilation():
        return False


def is_hex_active():

    if has_hex():

        # check for clock time, season, temperature and occupancy constraints
        # TODO: code
        return False

    elif not has_hex():
        return False
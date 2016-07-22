# -*- coding: utf-8 -*-
"""
=========================================
controllers
=========================================

"""
from __future__ import division
import numpy as np

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


"""
=========================================
temperature controllers
=========================================
"""
def calc_simple_temp_control(tsd, prop_comfort, limit_inf_season, limit_sup_season, weekday):
    def get_hsetpoint(a, b, Thset, Thsetback, weekday):
        if (b < limit_inf_season or b >= limit_sup_season):
            if a > 0:
                if weekday >= 5:  # system is off on the weekend
                    return -30  # huge so the system will be off
                else:
                    return Thset
            else:
                return Thsetback
        else:
            return -30  # huge so the system will be off

    def get_csetpoint(a, b, Tcset, Tcsetback, weekday):
        if limit_inf_season <= b < limit_sup_season:
            if a > 0:
                if weekday >= 5:  # system is off on the weekend
                    return 50  # huge so the system will be off
                else:
                    return Tcset
            else:
                return Tcsetback
        else:
            return 50  # huge so the system will be off

    tsd['ve'] = tsd['people'] * prop_comfort['Ve_lps'] * 3.6  # in m3/h
    tsd['ta_hs_set'] = np.vectorize(get_hsetpoint)(tsd['people'], range(8760), prop_comfort['Ths_set_C'],
                                                   prop_comfort['Ths_setb_C'], weekday)
    tsd['ta_cs_set'] = np.vectorize(get_csetpoint)(tsd['people'], range(8760), prop_comfort['Tcs_set_C'],
                                                   prop_comfort['Tcs_setb_C'], weekday)

    return tsd


"""
=========================================
ventilation controllers
=========================================
"""
def calc_simple_ventilation_control(ve, people, Af, gv, hour_day, hour_year, n50):
    """
    Modified version of calc_simple_ventilation_control from functions.
    Fixed infiltration according to schedule is only considered for mechanically ventilated buildings.

    Parameters
    ----------
    ve : required ventilation rate according to schedule (?)
    people : occupancy schedules (pax?)
    Af : conditioned floor area (m2)
    gv : globalvars
    hour_day : hour of the day [0..23]
    hour_year : hour of the year [0..8760]
    n50 : building envelope leakiness from archetypes

    Returns
    -------
    q_req : required ventilation rate schedule (m3/s)
    """
    # TODO: check units

    # 'flat rate' infiltration considered for all buildings
    # estimation of infiltration air volume flow rate according to Eq. (3) in DIN 1946-6
    n_inf = 0.5 * n50 * (gv.delta_p_dim/50) ** (2/3)  # [air changes per hour]

    infiltration = gv.hf * n_inf  # m3/h.m2

    if (21 < hour_day or hour_day < 7) and not gv.is_heating_season(hour_year):
        q_req = (ve * 1.3 + (infiltration * Af)) / 3600
        # free cooling during summer nights (1.3x required ventilation rate per pax plus infiltration)

    else:
        q_req = (ve + (infiltration * Af)) / 3600  # required ventilation rate per pax and infiltration

    return q_req  # m3/s


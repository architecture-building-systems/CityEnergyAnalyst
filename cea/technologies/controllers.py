# -*- coding: utf-8 -*-
"""
controllers
"""
from __future__ import division
import numpy as np
from cea.utilities import helpers

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Gabriel Happle", "Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# temperature controllers

def calc_simple_temp_control(tsd, prop_comfort, limit_inf_season, limit_sup_season, weekday):
    def get_hsetpoint(a, b, Thset, Thsetback, weekday):
        if helpers.is_heatingseason_hoy(b):  # FIXME  # b < limit_inf_season or b >= limit_sup_season):
            if a == 0:
                if 5 <= weekday <= 6:  # system is off on the weekend
                    return np.nan  # huge so the system will be off
                else:
                    return Thsetback
            else:
                return Thset
        else:
            return np.nan  # huge so the system will be off

    def get_csetpoint(a, b, Tcset, Tcsetback, weekday):
        if helpers.is_coolingseason_hoy(b):  # FIXME  #limit_inf_season <= b < limit_sup_season:
            if a == 0:
                if 5 <= weekday <= 6:  # system is off on the weekend
                    return np.nan  # huge so the system will be off
                else:
                    return Tcsetback
            else:
                return Tcset
        else:
            return np.nan  # huge so the system will be off

    tsd['ta_hs_set'] = np.vectorize(get_hsetpoint)(tsd['people'], range(8760), prop_comfort['Ths_set_C'],
                                                   prop_comfort['Ths_setb_C'], weekday)
    tsd['ta_cs_set'] = np.vectorize(get_csetpoint)(tsd['people'], range(8760), prop_comfort['Tcs_set_C'],
                                                   prop_comfort['Tcs_setb_C'], weekday)

    return tsd



def temperature_control_tabs(bpr, tsd, hoy, gv, control):
    """
    Controls for TABS operating temperature based on the operating parameters defined by Koschenz and Lehmann
    "Thermoaktive Bauteilsysteme (TABS)" (2000), that is: maximum surface temperature and maximum temperature difference
    between TABS surface and air. If either of these is exceeded, they are set to the maximum and all temperatures are
    recalculated.
    The formulas below are simply reformulations of the calculations in the R-C model.
    """

    # TODO: add documentation of input
    # TODO: add credits
    # TODO: add source and numbers of equations in standard

    # get values from bpr
    Htr_ms = bpr.rc_model['Htr_ms']
    Htr_w = bpr.rc_model['Htr_w']
    Htr_em = bpr.rc_model['Htr_em']
    Htr_is = bpr.rc_model['Htr_is']
    Cm = bpr.rc_model['Cm']
    # get values from tsd
    Hve = tsd['h_ve_adj'][hoy]
    I_ia = tsd['I_ia'][hoy]
    I_st = tsd['I_st'][hoy]
    I_m = tsd['I_m'][hoy]
    te_t = tsd['T_ext'][hoy]
    tm_t0 = tsd['Tm'][hoy-1]  # assuming that tm_t0 means mass temperature at previous time step



    if control == 'max_ts':
        # if the calculated surface temperature exceeds the maximum, set ts = ts_max and calculate maximum power
        # and all other temperatures
        ts_max = gv.max_surface_temperature_tabs
        a = np.array([[(Hve + Htr_is), (-Htr_is), 0, (-0.5)],
                      [(-Htr_is), (Htr_w + Htr_ms + Htr_is), (-Htr_ms), (-0.5)],
                      [0, (-Htr_ms), ((Htr_ms + Htr_em) / 2 + Cm), (-0.5)],
                      [0, 1, 0, 0]])
        b = np.array([(Hve * te_t + I_ia), (Htr_w * te_t + I_st + Htr_ms / 2 * tm_t0),
                      (Htr_em * te_t + (-(Htr_ms + Htr_em) / 2 + Cm) * tm_t0 + I_m), ts_max])
        [ta, ts, tm_t, IH_max] = np.linalg.solve(a, b)
    if control == 'max_ts-ta':
        # if the calculated temperature difference between the surface and inside air exceeds the maximum,
        # set ts - ta = dt_max and calculate maximum power and other temperatures
        dt_max = gv.max_temperature_difference_tabs
        a = np.array([[(Hve + Htr_is), (-Htr_is), 0, (-0.5)],
                      [(-Htr_is), (Htr_w + Htr_ms + Htr_is), (-Htr_ms), (-0.5)],
                      [0, (-Htr_ms), ((Htr_ms + Htr_em) / 2 + Cm), (-0.5)],
                      [-1, 1, 0, 0]])
        b = np.array([(Hve * te_t + I_ia), (Htr_w * te_t + I_st + Htr_ms / 2 * tm_t0),
                      (Htr_em * te_t + (-(Htr_ms + Htr_em) / 2 + Cm) * tm_t0 + I_m), dt_max])
        [ta, ts, tm_t, IH_max] = np.linalg.solve(a, b)
    return ta, ts, tm_t, IH_max




# ventilation controllers


def calc_simple_ventilation_control(ve, people, Af, gv, hour_day, hour_year, n50):
    """
    Modified version of calc_simple_ventilation_control from functions.
    Fixed infiltration according to schedule is only considered for mechanically ventilated buildings.

    ve : required ventilation rate according to schedule (?)
    people : occupancy schedules (pax?)
    Af : conditioned floor area (m2)
    gv : globalvars
    hour_day : hour of the day [0..23]
    hour_year : hour of the year [0..8760]
    n50 : building envelope leakiness from archetypes

    q_req : required ventilation rate schedule (m3/s)
    """
    # TODO: check units

    # 'flat rate' infiltration considered for all buildings
    # estimation of infiltration air volume flow rate according to Eq. (3) in DIN 1946-6
    n_inf = 0.5 * n50 * (gv.delta_p_dim/50) ** (2/3)  # [air changes per hour] m3/h.m2
    infiltration = gv.hf * Af * n_inf * 0.000277778 # m3/s

    if (21 < hour_day or hour_day < 7) and not gv.is_heating_season(hour_year):

        q_req = max(ve * 0.000277778, infiltration) * 1.3  # m3/s
        # free cooling during summer nights (1.3x required ventilation rate per pax plus infiltration)
    else:

        q_req = max(ve * 0.000277778, infiltration)  # m3/s

    return q_req   # m3/s


def calc_ventialtion_HVAC_buildings(area_envelope, HVAC_on, Tin, Tout, ws, method):
    """
    infiltration according to energy plus, blast, or DOE2 tools

    """
    def calc_F_schedule(HVAC_on): #according to (SSPC 90.1 Envelope Subcommittee
        if HVAC_on:
            F_schedule = 0.25
        else:
            F_schedule = 1
        return F_schedule

    def calc_Idesign(ws, area_envelope):
        I_75pa = 0.00914400602372 * area_envelope # known leakage rate(1.8cfm/sf2) at 75pa per area of building envelope in m/s
        n = 0.65 # air flow exponent
        Cs = 0.1617  # average surface presure coefficient
        rho = 1.18  #kg/m3
        alpha_terrain = 0.22 # urban terrain constant
        I_design = (alpha_terrain+1)*I_75pa*(0.5*Cs*rho*(ws**2))**n # m3/s
        return I_design

    if method is "BLAST":
        A = 0.606
        B = 0.03636
        C = 0.1177
    elif method is "EPLUS":
        A = 1
        B = 0
        C = 0
    elif method is "DOE2":
        A = 1
        B = 0
        C = 0.224
    else:
        A = 1
        B = 0
        C = 0.224

    I_design = calc_Idesign(ws, area_envelope)
    F_schedule = calc_F_schedule(HVAC_on)
    ventilation = I_design + F_schedule *(A+B*abs(Tin-Tout)+C*ws)

    return ventilation


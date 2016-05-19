# -*- coding: utf-8 -*-
"""
    hvac_kaempf
    ===========
    contains debugged version of HVAC model of Kämpf [1]
    originally coded by J. Fonseca
    debugged and moved out of functions.py script by G. Happle
    Literature:
    [1] Kämpf, Jérôme Henri
        On the modelling and optimisation of urban energy fluxes
        http://dx.doi.org/10.5075/epfl-thesis-4548
"""

from __future__ import division
import math
import numpy as np


def calc_hvac(RH1, t1, tair, qv_req, Qsen, t5_1, wint, gv, temp_sup_heat, temp_sup_cool):
    """
    HVAC model of Kämpf [1]

    Parameters
    ----------
    RH1 : external relative humidity at time step t (%)
    t1 : external air temperature at time step t (°C)
    tair :
    qv_req : ventilation requirements at time step t according to the mixed occupancy schedule of the building (m3/s)
    Qsen : sensible heating or cooling load to be supplied by the HVAC system at time step t in [W]
    t5_1 : zone air temperature at time step t-1 (°C)
    wint : internal moisture gains at time step t according to the mixed occupancy schedule of the building
    gv : object of class globalvar
    temp_sup_heat : heating system supply temperature (°C)
    temp_sup_cool : cooling system supply temperature (°C)

    Returns
    -------

    """

    # State No. 5 # indoor air set point
    t5_prime = tair + 1  # accounding for an increase in temperature # TODO: where is this from? why use calculated tair and not the setpoint temperature? why +1? # FIXME: remove

    # state after heat exchanger
    t2, w2 = calc_hex(RH1, gv, qv_req, t1, t5_1)

    # print(t5_prime)
    if abs(Qsen) != 0:  # to account for the bug of possible -0.0
        # sensible and latent loads
        Qsen = Qsen * 0.001  # transform in kJ/s

        # State No. 3
        # Assuming that AHU does not modify the air humidity
        w3 = w2
        if Qsen > 0:  # if heating
            t3 = temp_sup_heat  # heating system supply temperature in (°C)
        elif Qsen < 0:  # if cooling
            t3 = temp_sup_cool  # cooling system supply temperature in (°C)

        # initial guess of mass flow rate
        h_t5_prime_w3 = calc_h(t5_prime, w3)  # for enthalpy change in first assumption, see Eq.(4.31) in [1]
        h_t3_w3 = calc_h(t3, w3)  # for enthalpy change in first assumption, see Eq.(4.31) in [1]
        # Eq. (4.34) in [1] for first prediction of mass flow rater in (kg/s)
        m1 = max(-Qsen / (h_t5_prime_w3 - h_t3_w3), (gv.Pair * qv_req))  # TODO: use dynamic air density

        # determine virtual state in the zone without moisture conditioning
        # moisture balance accounting for internal moisture load, see also Eq. (4.32) in [1]
        w5_prime = (wint + w3 * m1) / m1

        # room supply moisture content:
        if Qsen > 0:  # if heating
            # algorithm for heating case
            w3 = calc_w3_heating_case(t5_prime, w2, w5_prime, t3)
            ts = t3 + 0.5  # plus expected delta T drop in the ducts TODO: check and document value of temp increase
        elif Qsen < 0:  # if cooling
            # algorithm for cooling case
            w3 = calc_w3_cooling_case(t5_prime, w2, t3, w5_prime)
            ts = t3 - 0.5  # minus expected delta T rise in the ducts TODO: check and document value of temp decrease

        # State of Supply
        ws = w3

        # the new mass flow rate
        h_t5_prime_w3 = calc_h(t5_prime, w3)
        h_t3_w3 = calc_h(t3, w3)
        m = max(-Qsen / (h_t5_prime_w3 - h_t3_w3), (gv.Pair * qv_req))

        # TODO: now the energy of humidification and dehumidification can be calculated
        h_t2_ws = calc_h(t2, ws)
        h_t2_w2 = calc_h(t2, w2)
        q_hum_dehum = m * (h_t2_ws - h_t2_w2) * 1000  # TODO: document energy for (de)humidification

        if q_hum_dehum > 0:  # humidification
            Qhum = q_hum_dehum
            Qdhum = 0
        elif q_hum_dehum < 0:  # dehumidification
            Qhum = 0
            Qdhum = q_hum_dehum
        else:
            Qhum = 0
            Qdhum = 0

        # Total loads
        h_t2_w2 = calc_h(t2, w2)
        h_ts_ws = calc_h(ts, ws)
        Qtot = m * (h_ts_ws - h_t2_w2) * 1000  # TODO: document

        # Adiabatic humidifier - computation of electrical auxiliary loads
        if Qhum > 0:
            Ehum_aux = 15 / 3600 * m  # assuming a performance of 15 W por Kg/h of humidified air source: bertagnolo 2012
        else:
            Ehum_aux = 0

        if Qsen > 0:
            Qhs_sen = Qtot - Qhum
            ma_hs = m
            ts_hs = ts
            tr_hs = t2
            Qcs_sen = 0
            ma_cs = 0
            ts_cs = 0
            tr_cs = np.nan  # set unused temperatures to nan as they could potentially have the value 0
        elif Qsen < 0:
            Qcs_sen = Qtot - Qdhum
            ma_hs = 0
            ts_hs = np.nan  # set unused temperatures to nan as they could potentially have the value 0
            tr_hs = np.nan  # set unused temperatures to nan as they could potentially have the value 0
            ma_cs = m
            ts_cs = ts
            tr_cs = t2
            Qhs_sen = 0
    else:
        Qhum = 0
        Qdhum = 0
        Qtot = 0
        Qhs_sen = 0
        Qcs_sen = 0
        w1 = w2 = w3 = w5 = t3 = ts = m = 0
        Ehum_aux = 0
        ma_hs = ma_cs = 0
        ts_hs = ts_cs = np.nan  # set unused temperatures to nan as they could potentially have the value 0
        tr_cs = t2  # temperature after hex
        tr_hs = t2  # temperature after hex

        # TODO: return air mass flow rates
    t5 = t5_prime  # FIXME: this should not be input or output of this function

    return Qhs_sen, Qcs_sen, Qhum, Qdhum, Ehum_aux, ma_hs, ma_cs, ts_hs, ts_cs, tr_hs, tr_cs, w2, w3, t5


def calc_hex(rel_humidity_ext, gv, qv_req, temp_ext, temp_zone_prev):
    """
    Calculates air properties of mechanical ventilation system with heat exchanger

    Parameters
    ----------
    rel_humidity_ext : (%)
    gv : globalvar
    qv_req : required air volume flow (kg/s)
    temp_ext : external temperature at time t (°C)
    temp_zone_prev : ventilation zone air temperature at time t-1 (°C)

    Returns
    -------
    t2, w2 : temperature and moisture content of inlet air after heat exchanger

    """
    # TODO add literature

    # Properties of heat recovery and required air incl. Leakage
    qv = qv_req * 1.0184  # in m3/s corrected taking into account leakage # TODO: add source
    Veff = gv.Vmax * qv / qv_req  # max velocity effective # FIXME this does not make sense qv/qv_req = 1.0184 (see above)
    nrec = gv.nrec_N - gv.C1 * (Veff - 2)  # heat exchanger coefficient # TODO: add source

    # State No. 1
    w1 = calc_w(temp_ext, rel_humidity_ext)  # outdoor moisture (kg/kg)

    # State No. 2
    # inlet air temperature after HEX calculated from zone air temperature at time step t-1 (°C)
    t2 = temp_ext + nrec * (temp_zone_prev - temp_ext)
    w2 = min(w1, calc_w(t2, 100))  # inlet air moisture (kg/kg), Eq. (4.24) in [1]

    return t2, w2


def calc_w3_heating_case(t5, w2, w5, t3):
    """
    Algorithm 1 Determination of the room's supply moisture content (w3) for the heating case
     from Kaempf's HVAC model [1]

    Source:
    [1] Kämpf, Jérôme Henri
        On the modelling and optimisation of urban energy fluxes
        http://dx.doi.org/10.5075/epfl-thesis-4548


    Parameters
    ----------
    t5
    w2
    w5
    t3

    Returns
    -------

    """

    # get constants and properties
    temp_comf_max = 26  # limits of comfort in zone TODO: get from properties
    hum_comf_max = 70  # limits of comfort in zone TODO: get from properties

    w_liminf = calc_w(t5, 30)  # TODO: document
    w_limsup = calc_w(t5, 70)  # TODO: document
    w_comf_max = calc_w(temp_comf_max, hum_comf_max)  # moisture content at maximum comfortable state

    # Qhum = 0 TODO: remove
    # Qdhum = 0 TODO: remove
    if w5 < w_liminf:
        # humidification
        w3 = w_liminf - w5 + w2

    elif w5 > w_limsup and w5 < w_comf_max:
        # heating and no dehumidification
        # delta_HVAC = calc_t(w5,70)-t5
        w3 = w2

    elif w5 > w_comf_max:
        # dehumidification
        w3 = max(min(min(w_comf_max - w5 + w2, calc_w(t3, 100)), w_limsup - w5 + w2), 0)

    else:
        # no moisture control
        w3 = w2

    return w3


def calc_w3_cooling_case(t5, w2, t3, w5):
    """
    Algorithm 2 Determination of the room's supply moisture content (w3) for the cooling case from Kaempf's HVAC model
    for non-evaporative cooling

    Source:
    [1] Kämpf, Jérôme Henri
        On the modelling and optimisation of urban energy fluxes
        http://dx.doi.org/10.5075/epfl-thesis-4548


    Parameters
    ----------
    t5
    w2
    t3
    w5

    Returns
    -------

    """

    # get constants and properties
    w_liminf = calc_w(t5, 30)  # TODO: document
    w_limsup = calc_w(t5, 70)  # TODO: document

    if w5 > w_limsup:
        # dehumidification
        w3 = max(min(w_limsup - w5 + w2, calc_w(t3, 100)), 0)

    elif w5 < w_liminf:
        # humidification
        w3 = w_liminf - w5 + w2

    else:
        w3 = min(w2, calc_w(t3, 100))

    return w3


def calc_w(t, RH):
    """

    Parameters
    ----------
    t : temperature
    RH

    Returns
    -------

    """
    # Moisture content in kg/kg of dry air
    # TODO: add documentation and source of formula
    Pa = 100000  # Pa
    Ps = 610.78 * math.exp(t / (t + 238.3) * 17.2694)
    Pv = RH / 100 * Ps
    w = 0.62 * Pv / (Pa - Pv)
    return w


def calc_h(t, w):  # enthalpyh of most air in kJ/kg
    # TODO: add documentation and source of formula
    # source: thesis Kaempf Eq.(4.30) extended to temperatures below -10°
    if 0 < t < 60:
        h = (1.007 * t - 0.026) + w * (2501 + 1.84 * t)
    elif -100 < t <= 0:
        h = (1.005 * t) + w * (2501 + 1.84 * t)
        # else:
    #    h = (1.007*t-0.026)+w*(2501+1.84*t)
    return h

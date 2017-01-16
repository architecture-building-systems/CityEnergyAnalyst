# -*- coding: utf-8 -*-
"""
    hvac_kaempf
    ===========
    contains debugged version of HVAC model of Kämpf [1]
    originally coded by J. Fonseca
    debugged  by G. Happle
    Literature:
    [1] Kämpf, Jérôme Henri
        On the modelling and optimisation of urban energy fluxes
        http://dx.doi.org/10.5075/epfl-thesis-4548
"""

from __future__ import division
import numpy as np
from cea.utilities.physics import calc_h, calc_w, calc_t_from_h

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


"""
=========================================
ventilation demand controlled unit
=========================================
"""


def calc_hvac_cooling(tsd, hoy, gv):
    """


    """

    temp_zone_set = tsd['theta_a'][hoy]
    qe_sen = tsd['Qcs_sen'][hoy] # get the total sensible load from the RC model, in this case without any mechanical ventilation losses??? NO!
    m_ve_hvac_req = tsd['m_ve_mech'][hoy]   # mechanical ventilation flow rate according to ventilation control
    wint = tsd['w_int'][hoy]

    # sensible cooling load provided by conditioning of ventilation air
    #  = enthalpy difference in air mass flow between supply and room temperature
    q_cs_sen_ventilation = calc_hvac_sensible_cooling_ventilation_air(tsd, hoy, gv)

    # calculate the part of the sensible load that is supplied by conditioning the recirculation air
    # = additional load that has to be covered by conditioning room air through recirculation
    # additional load can not be smaller than 0, over cooling situation
    q_cs_sen_recirculation = min(qe_sen - q_cs_sen_ventilation, 0) / 1000  # (kW)

    # indoor air set point
    t5 = temp_zone_set

    # ventilation air properties after heat exchanger
    t2, w2 = calc_hex(tsd, hoy, gv)  # (°C), (kg/kg)

    # State No. 3
    # Assuming that AHU does not modify the air humidity
    w3v = w2  # virtual moisture content at state 3

    # determine virtual state in the zone without moisture conditioning
    # moisture balance accounting for internal moisture load, see also Eq. (4.32) in [1]
    w5_prime = (wint + w3v * m_ve_hvac_req) / m_ve_hvac_req

    # supply air condition
    t3 = gv.temp_sup_cool_hvac

    # room supply moisture content:
    # algorithm for cooling case
    w3 = calc_w3_cooling_case(t5, w2, t3, w5_prime)

    # State of Supply
    ts = t3  # minus expected delta T rise in the ducts TODO: check and document value of temp decrease
    ws = w3

    # actual room condition
    w5 = (wint + w3 * m_ve_hvac_req) / m_ve_hvac_req
    h_w5_t5 = calc_h(t5, w5)

    # TODO: now the energy of humidification and dehumidification can be calculated
    h_t2_ws = calc_h(t2, ws)
    h_t2_w2 = calc_h(t2, w2)
    qe_hum_dehum = m_ve_hvac_req * (h_t2_ws - h_t2_w2) # (kW) TODO: document energy for (de)humidification

    # TODO: could be replaced by min() and max() functions
    if qe_hum_dehum > 0:  # humidification
        qe_hum = qe_hum_dehum
        qe_dehum = 0
    elif qe_hum_dehum < 0:  # dehumidification
        qe_hum = 0
        qe_dehum = qe_hum_dehum
    else:
        qe_hum = 0
        qe_dehum = 0

    # Total loads
    h_t2_w2 = calc_h(t2, w2)
    # h_ts_ws = calc_h(ts, ws)
    h_ts_w2 = calc_h(ts, w2)
    # qe_tot_ventilation_air = m_ve_hvac_req * (h_ts_ws - h_t2_w2)  # TODO: document
    q_cs_sen_hvac = m_ve_hvac_req * (h_ts_w2 - h_t2_w2)

    h_ts_w5 = calc_h(ts, w5)
    m_ve_hvac_recirculation = q_cs_sen_recirculation / (h_ts_w5 - h_w5_t5)

    # Adiabatic humidifier - computation of electrical auxiliary loads
    if qe_hum > 0:
        pel_hum_aux = 15 / 3600 * m_ve_hvac_req  # assuming a performance of 15 W por Kg/h of humidified air source: bertagnolo 2012
    else:
        pel_hum_aux = 0


    q_cs_sen_hvac = (q_cs_sen_hvac + q_cs_sen_recirculation) * 1000
    q_cs_lat_hvac = qe_dehum * 1000
    ma_sup_cs = m_ve_hvac_req + m_ve_hvac_recirculation
    ta_sup_cs = ts
    ta_re_cs = (m_ve_hvac_req * t2 + m_ve_hvac_recirculation * t5) / ma_sup_cs  # temperature mixing proportional to mass flow rates


    air_con_model_loads_flows_temperatures = {'q_cs_sen_hvac': q_cs_sen_hvac, \
                                              'q_cs_lat_hvac' : q_cs_lat_hvac, \
                                              'ma_sup_cs' : ma_sup_cs, \
                                              'ta_sup_cs' : ta_sup_cs, 'ta_re_cs' : ta_re_cs}

    if m_ve_hvac_req + m_ve_hvac_recirculation < 0:
        raise ValueError

    return air_con_model_loads_flows_temperatures


def calc_hvac_sensible_cooling_ventilation_air(tsd, hoy, gv):


    temp_zone_set = tsd['theta_a'][hoy]
    m_ve_hvac_req = tsd['m_ve_mech'][hoy]  # mechanical ventilation flow rate according to ventilation control

    # State No. 5 # indoor air set point
    t5_prime = temp_zone_set

    # state after heat exchanger
    # TODO: temperature could come from ventilation heat exchanger...
    t2, w2 = calc_hex(tsd, hoy, gv)  # (°C), (kg/kg)

    # State No. 3
    # Assuming that AHU does not modify the air humidity
    w3v = w2  # virtual moisture content at state 3

    # MODIFICATIONS HAPPLE to the model
    # *******************************************************
    # first we guess the temperature of supply based on the sensible heating load and the required vetilation mass flow rate
    h_t5_prime_w3v = calc_h(t5_prime, w3v)  # for enthalpy change in first assumption, see Eq.(4.31) in [1]

    t3 = gv.temp_sup_cool_hvac
    h_t3_w3v = calc_h(t3, w3v)  # for enthalpy change in first assumption, see Eq.(4.31) in [1]

    # calculate the part of the sensible load that can be supplied by conditioning the ventilation air
    q_cs_sen_ventilation = -m_ve_hvac_req * (h_t5_prime_w3v - h_t3_w3v)

    return q_cs_sen_ventilation * 1000 # convert from (kW) back to (W)


def calc_hvac_sensible_heating_ventilation_air(tsd, hoy, gv):


    temp_zone_set = tsd['theta_a'][hoy]
    m_ve_hvac_req = tsd['m_ve_mech'][hoy]  # (kg/s) mechanical ventilation flow rate according to ventilation control

    # State No. 5 # indoor air set point
    t5_prime = temp_zone_set

    # state after heat exchanger
    # TODO: temperature could come from ventilation heat exchanger...
    t2, w2 = calc_hex(tsd, hoy, gv)  # (°C), (kg/kg)

    # State No. 3
    # Assuming that AHU does not modify the air humidity
    w3v = w2  # virtual moisture content at state 3

    # first we guess the temperature of supply based on the sensible heating load and the required vetilation mass flow rate
    h_t5_prime_w3v = calc_h(t5_prime, w3v)  # for enthalpy change in first assumption, see Eq.(4.31) in [1]

    t3 = gv.temp_sup_heat_hvac
    h_t3_w3v = calc_h(t3, w3v)  # for enthalpy change in first assumption, see Eq.(4.31) in [1]

    # calculate the part of the sensible load that can be supplied by conditioning the ventilation air
    q_hs_sen_ventilation = -m_ve_hvac_req * (h_t5_prime_w3v - h_t3_w3v)  # (kW)

    return q_hs_sen_ventilation * 1000 # convert from (kW) back to (W)


def calc_hvac_heating(tsd, hoy, gv):
    """


    """

    temp_zone_set = tsd['theta_a'][hoy]
    qe_sen = tsd['Qhs_sen'][hoy] # get the total sensible load from the RC model, in this case without any mechanical ventilation losses???
    m_ve_hvac_req = tsd['m_ve_mech'][hoy]   # (kg/s) mechanical ventilation flow rate according to ventilation control
    wint = tsd['w_int'][hoy]

    # sensible heating load provided by conditioning of ventilation air
    #  = enthalpy difference in air mass flow between supply and room temperature
    q_hs_sen_ventilation = calc_hvac_sensible_heating_ventilation_air(tsd, hoy, gv)

    # calculate the part of the sensible load that is supplied by conditioning the recirculation air
    # = additional load that has to be covered by conditioning room air through recirculation
    # additional load can not be smaller than 0, over cooling situation
    q_hs_sen_recirculation = max(qe_sen - q_hs_sen_ventilation, 0) / 1000

    # State No. 5 # indoor air set point
    t5 = temp_zone_set

    # state after heat exchanger
    t2, w2 = calc_hex(tsd, hoy, gv)  # (°C), (kg/kg)

    # State No. 3
    # Assuming that AHU does not modify the air humidity
    w3v = w2  # virtual moisture content at state 3

    # determine virtual state in the zone without moisture conditioning
    # moisture balance accounting for internal moisture load, see also Eq. (4.32) in [1]
    w5_prime = (wint + w3v * m_ve_hvac_req) / m_ve_hvac_req

    t3 = gv.temp_sup_heat_hvac

    # room supply moisture content:
    # algorithm for heating case
    w3 = calc_w3_heating_case(t5, w2, w5_prime, t3, gv)
    ts = t3 # minus expected delta T rise in the ducts TODO: check and document value of temp decrease

    # State of Supply
    ws = w3

    # actual room condition
    w5 = (wint + w3 * m_ve_hvac_req) / m_ve_hvac_req
    h_w5_t5 = calc_h(t5, w5)

    # TODO: now the energy of humidification and dehumidification can be calculated
    h_t2_ws = calc_h(t2, ws)
    h_t2_w2 = calc_h(t2, w2)
    qe_hum_dehum = m_ve_hvac_req * (h_t2_ws - h_t2_w2)  # (kW) TODO: document energy for (de)humidification

    # TODO: could be replaced by min() and max() functions
    if qe_hum_dehum > 0:  # humidification
        qe_hum = qe_hum_dehum
        qe_dehum = 0
    elif qe_hum_dehum < 0:  # dehumidification
        qe_hum = 0
        qe_dehum = qe_hum_dehum
    else:
        qe_hum = 0
        qe_dehum = 0

    # Total loads
    h_t2_w2 = calc_h(t2, w2)
    # h_ts_ws = calc_h(ts, ws)
    h_ts_w2 = calc_h(ts, w2)
    # qe_tot_ventilation_air = m_ve_hvac_req * (h_ts_ws - h_t2_w2)  # TODO: document
    q_hs_sen_hvac = m_ve_hvac_req * (h_ts_w2 - h_t2_w2)

    h_ts_w5 = calc_h(ts, w5)

    m_ve_hvac_recirculation = q_hs_sen_recirculation / (h_ts_w5 - h_w5_t5)

    # qe_free = - m * (h_t5_prime_w3 - calc_h(temp_1, calc_w(temp_1,rhum_1))) * 1000
    # q_sen_tot = qe_tot + qe_free - qe_hum_dehum

    # Adiabatic humidifier - computation of electrical auxiliary loads
    if qe_hum > 0:
        pel_hum_aux = 15 / 3600 * m_ve_hvac_req  # assuming a performance of 15 W por Kg/h of humidified air source: bertagnolo 2012
    else:
        pel_hum_aux = 0

    q_hs_sen_hvac = (q_hs_sen_hvac + q_hs_sen_recirculation) * 1000
    q_hs_lat_hvac = qe_hum * 1000
    ma_sup_hs = m_ve_hvac_req + m_ve_hvac_recirculation
    ta_sup_hs = ts
    ta_re_hs = (
               m_ve_hvac_req * t2 + m_ve_hvac_recirculation * t5) / ma_sup_hs  # temperature mixing proportional to mass flow rates

    air_con_model_loads_flows_temperatures = {'q_hs_sen_hvac': q_hs_sen_hvac, \
                                              'q_hs_lat_hvac': q_hs_lat_hvac, \
                                              'ma_sup_hs': ma_sup_hs, \
                                              'ta_sup_hs': ta_sup_hs, 'ta_re_hs': ta_re_hs, 'e_hs_lat_aux': pel_hum_aux}

    if m_ve_hvac_req + m_ve_hvac_recirculation < 0:
        raise ValueError

    return air_con_model_loads_flows_temperatures


"""
=========================================
air Heat exchanger unit
=========================================
"""
def calc_hex(tsd, hoy, gv):
    """
    Calculates air properties of mechanical ventilation system with heat exchanger
    Modeled after 2.4.2 in SIA 2044

    Parameters
    ----------
    rel_humidity_ext : (%)
    gv : globalvar
    qv_mech : required air volume flow (kg/s)
    temp_ext : external temperature at time t (°C)
    temp_zone_prev : ventilation zone air temperature at time t-1 (°C)

    Returns
    -------
    t2, w2 : temperature and moisture content of inlet air after heat exchanger

    """
    # TODO add literature

    rel_humidity_ext = tsd['rh_ext'][hoy]
    temp_ext = tsd['T_ext'][hoy]

    # FIXME: dynamic HEX efficiency
    # Properties of heat recovery and required air incl. Leakage
    # qv_mech = qv_mech * 1.0184  # in m3/s corrected taking into account leakage # TODO: add source
    # Veff = gv.Vmax * qv_mech / qv_mech_dim  # Eq. (85) in SIA 2044
    # nrec = gv.nrec_N - gv.C1 * (Veff - 2)  # heat exchanger coefficient # TODO: add source
    nrec = gv.nrec_N  # for now use constant efficiency for heat recovery

    # State No. 1
    w1 = calc_w(temp_ext, rel_humidity_ext)  # outdoor moisture (kg/kg)

    # State No. 2
    # inlet air temperature after HEX calculated from zone air temperature at time step t-1 (°C)
    t2 = tsd['theta_ve_mech'][hoy]
    w2 = min(w1, calc_w(t2, 100))  # inlet air moisture (kg/kg), Eq. (4.24) in [1]

    # TODO: document
    # bypass heat exchanger if use is not beneficial
    #if temp_zone_prev > temp_ext and not gv.is_heating_season(timestep):
        #t2 = temp_ext
        #w2 = w1
        # print('bypass HEX cooling')
    #elif temp_zone_prev < temp_ext and gv.is_heating_season(timestep):
        #t2 = temp_ext
        #w2 = w1
        # print('bypass HEX heating')

    return t2, w2


"""
=========================================
Moisture balance
=========================================
"""


def calc_w3_heating_case(t5, w2, w5, t3, gv):
    """
    Algorithm 1 Determination of the room's supply moisture content (w3) for the heating case
     from Kaempf's HVAC model [1]

    Source:
    [1] Kämpf, Jérôme Henri
        On the modelling and optimisation of urban energy fluxes
        http://dx.doi.org/10.5075/epfl-thesis-4548


    Parameters
    ----------
    t5 : temperature 5 in (°C)
    w2 : moisture content 2 in (kg/kg dry air)
    w5 : moisture content 5 in (kg/kg dry air)
    t3 : temperature 3 in (°C)
    gv : globalvar

    Returns
    -------
    w3 : moisture content of HVAC supply air in (kg/kg dry air)
    """

    # get constants and properties
    temp_comf_max = gv.temp_comf_max  # limits of comfort in zone TODO: get from properties
    hum_comf_max = gv.rhum_comf_max  # limits of comfort in zone TODO: get from properties

    w_liminf = calc_w(t5, 30)  # TODO: document
    w_limsup = calc_w(t5, 70)  # TODO: document
    w_comf_max = calc_w(temp_comf_max, hum_comf_max)  # moisture content at maximum comfortable state

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
    t5 : temperature 5 in (°C)
    w2 : moisture content 2 in (kg/kg dry air)
    t3 : temperature 3 in (°C)
    w5 : moisture content 5 in (kg/kg dry air)

    Returns
    -------
    w3 : moisture content of HVAC supply air in (kg/kg dry air)
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

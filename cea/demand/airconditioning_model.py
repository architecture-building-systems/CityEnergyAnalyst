# -*- coding: utf-8 -*-
"""
Contains debugged version of HVAC model from [Kämpf2009]_

- originally coded by J. Fonseca
- debugged  by G. Happle

.. note:: this is not really true anymore. The procedure now is just loosely based on [Kämpf2009]_.

.. [Kämpf2009] Kämpf, Jérôme Henri
   On the modelling and optimisation of urban energy fluxes
   http://dx.doi.org/10.5075/epfl-thesis-4548
"""


from __future__ import division
from cea.utilities.physics import calc_h, calc_w

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# constants refactored from gv
# ==============================================================================================================
# HVAC
# ==============================================================================================================
temp_sup_heat_hvac = 36  # (°C)
temp_sup_cool_hvac = 16  # (°C)

# ==============================================================================================================
# Comfort
# ==============================================================================================================
temp_comf_max = 26  # (°C) TODO: include to building properties and get from building properties
rhum_comf_max = 70  # (%)

# ==============================================================================================================
# Physics
# ==============================================================================================================
water_heat_of_vaporization = 0.6783  # Wh/kg @ 25 C
# https://www.engineeringtoolbox.com/water-properties-d_1573.html


# ventilation demand controlled unit

def calc_hvac_cooling(tsd, t):

    """
    Calculate AC air mass flows, energy demand and temperatures
    For the cooling case for AC systems with demand controlled ventilation air flows (mechanical ventilation) and
    conditioning of recirculated air (outdoor air flows are not modified)

    :param tsd: time series data dict
    :type tsd: Dict[str, numpy.ndarray[numpy.float64]]
    :param t: time step
    :type t: int
    :return: AC air mass flows, energy demand and temperatures for the cooling case
    :rtype: Dict[str, numpy.float64]
    """

    temp_zone_set = tsd['T_int'][t]  # zone set temperature according to scheduled set points
    qe_sen = tsd['Qcs_sen'][t] / 1000  # get the total sensible load from the RC model in [kW]
    m_ve_mech = tsd['m_ve_mech'][t]  # mechanical ventilation flow rate according to ventilation control
    wint = tsd['w_int'][t]  # internal moisture gains from occupancy
    rel_humidity_ext = tsd['rh_ext'][t]  # exterior relative humidity
    temp_ext = tsd['T_ext'][t]  # exterior air temperature
    temp_mech_vent = tsd['theta_ve_mech'][t]  # air temperature of mechanical ventilation air

    # calc latent people gain for building energy balance of air-con cooling
    q_cs_lat_peop = wint * 3600 * water_heat_of_vaporization  # kg/s * 3600 s/h * Wh/kg = Wh/h = W

    # indoor air set point
    t5 = temp_zone_set

    if m_ve_mech > 0:  # mechanical ventilation system is active, ventilation air and recirculation air gets conditioned

        # State No. 1
        w1 = calc_w(temp_ext, rel_humidity_ext)  # outdoor moisture (kg/kg)

        # ventilation air properties
        # State No. 2
        t2 = temp_mech_vent
        w2 = min(w1, calc_w(t2, 100))  # inlet air moisture (kg/kg), Eq. (4.24) in [1]

        # State No. 3
        # Assuming that AHU does not modify the air humidity
        w3v = w2  # virtual moisture content at state 3

        # determine virtual state in the zone without moisture conditioning
        # moisture balance accounting for internal moisture load, see also Eq. (4.32) in [1]
        w5_prime = (wint + w3v * m_ve_mech) / m_ve_mech

        # supply air condition
        t3 = temp_sup_cool_hvac

        # room supply moisture content:
        # algorithm for cooling case
        w3 = calc_w3_cooling_case(t5, w2, t3, w5_prime)

        # State of Supply
        ts = t3  # minus expected delta T rise in the ducts TODO: check and document value of temp decrease
        ws = w3

        # actual room condition
        w5 = (wint + w3 * m_ve_mech) / m_ve_mech
        h_w5_t5 = calc_h(t5, w5)

        # now the energy of dehumidification can be calculated
        h_t2_ws = calc_h(t2, ws)
        h_t2_w2 = calc_h(t2, w2)
        qe_dehum = m_ve_mech * (h_t2_ws - h_t2_w2)  # (kW) # (kW) energy for dehumidification / latent cooling demand

        # cooling load provided by conditioning ventilation air
        h_t2_w2 = calc_h(t2, w2)
        h_ts_w2 = calc_h(ts, w2)
        q_cs_sen_mech_vent = m_ve_mech * (h_ts_w2 - h_t2_w2)

    elif m_ve_mech == 0:  # mechanical ventilation system is not active, only recirculation air gets conditioned

        # supply air condition
        t3 = temp_sup_cool_hvac

        # State of Supply
        ts = t3  # minus expected delta T rise in the ducts TODO: check and document value of temp decrease
        w5 = wint
        h_w5_t5 = calc_h(t5, w5)

        # No dehumidification of recirculation air as there is no model yet for internal humidity assessment
        qe_dehum = 0
        q_cs_sen_mech_vent = 0
        t2 = temp_mech_vent

    else:
        raise

    # calculate the part of the sensible load that is supplied by conditioning the recirculation air
    # = additional load that has to be covered by conditioning room air through recirculation
    # additional load can not be smaller than 0, over cooling situation
    q_cs_sen_recirculation = min(qe_sen - q_cs_sen_mech_vent, 0)  # (kW)
    h_ts_w5 = calc_h(ts, w5)
    m_ve_hvac_recirculation = q_cs_sen_recirculation / (h_ts_w5 - h_w5_t5)

    # output parameters
    q_cs_sen_hvac = (q_cs_sen_mech_vent + q_cs_sen_recirculation) * 1000
    q_cs_lat_hvac = qe_dehum * 1000
    ma_sup_cs = m_ve_mech + m_ve_hvac_recirculation
    ta_sup_cs = ts
    ta_re_cs = (m_ve_mech * t2 + m_ve_hvac_recirculation * t5) / ma_sup_cs  # temperature mixing proportional to mass flow rates

    # construct output dict
    air_con_model_loads_flows_temperatures = {'q_cs_sen_hvac': q_cs_sen_hvac,
                                              'q_cs_lat_hvac': q_cs_lat_hvac,
                                              'ma_sup_cs': ma_sup_cs,
                                              'ta_sup_cs': ta_sup_cs,
                                              'ta_re_cs': ta_re_cs,
                                              'm_ve_hvac_recirculation' : m_ve_hvac_recirculation,
                                              'q_cs_lat_peop': q_cs_lat_peop}

    if m_ve_mech + m_ve_hvac_recirculation < 0:
        raise ValueError

    return air_con_model_loads_flows_temperatures


def calc_hvac_heating(tsd, t):
    """
    Calculate AC air mass flows, energy demand and temperatures for the heating case
    For AC system with demand controlled ventilation air flows (mechanical ventilation) and conditioning of recirculated
    air (outdoor air flows are not modified)

    :param tsd: time series data dict
    :type tsd: Dict[str, numpy.ndarray[numpy.float64]]

    :param t: time step
    :type t: int

    :param gv: global variables
    :type gv: cea.globalvar.GlobalVariables

    :return: AC air mass flows, energy demand and temperatures for the heating case
    :rtype: Dict[str, numpy.float64]
    """

    temp_zone_set = tsd['T_int'][t]  # zone set temperature according to scheduled set points
    qe_sen = tsd['Qhs_sen'][t] / 1000  # get the total sensible load from the RC model in [W]
    m_ve_mech = tsd['m_ve_mech'][t]  # (kg/s) mechanical ventilation flow rate according to ventilation control
    wint = tsd['w_int'][t]  # internal moisture gains from occupancy
    rel_humidity_ext = tsd['rh_ext'][t]  # exterior relative humidity
    temp_ext = tsd['T_ext'][t]  # exterior air temperature
    temp_mech_vent = tsd['theta_ve_mech'][t]  # air temperature of mechanical ventilation air

    # indoor air set point
    t5 = temp_zone_set

    if m_ve_mech > 0:  # mechanical ventilation system is active, ventilation air and recirculation air gets conditioned

        # ventilation air properties after heat exchanger
        # State No. 1
        w1 = calc_w(temp_ext, rel_humidity_ext)  # outdoor moisture (kg/kg)

        # State No. 2
        t2 = temp_mech_vent
        w2 = min(w1, calc_w(t2, 100))  # inlet air moisture (kg/kg), Eq. (4.24) in [1]

        # State No. 3
        # Assuming that AHU does not modify the air humidity
        w3v = w2  # virtual moisture content at state 3

        # determine virtual state in the zone without moisture conditioning
        # moisture balance accounting for internal moisture load, see also Eq. (4.32) in [1]
        w5_prime = (wint + w3v * m_ve_mech) / m_ve_mech

        # supply air condition
        t3 = temp_sup_heat_hvac

        # room supply moisture content:
        # algorithm for cooling case
        w3 = calc_w3_heating_case(t5, w2, w5_prime, t3)

        # State of Supply
        ts = t3  # minus expected delta T rise in the ducts TODO: check and document value of temp decrease
        ws = w3

        # actual room condition
        w5 = (wint + w3 * m_ve_mech) / m_ve_mech
        h_w5_t5 = calc_h(t5, w5)

        # Humidification of ventilation air
        h_t2_ws = calc_h(t2, ws)
        h_t2_w2 = calc_h(t2, w2)
        qe_hum = m_ve_mech * (h_t2_ws - h_t2_w2)  # (kW) energy for humidification / latent heating demand

        # Adiabatic humidifier - computation of electrical auxiliary loads
        e_hs_lat_aux = 15 / 3600 * m_ve_mech  # assuming a performance of 15 W por Kg/h of humidified air source: bertagnolo 2012

        # heating load provided by conditioning ventilation air
        h_t2_w2 = calc_h(t2, w2)
        h_ts_w2 = calc_h(ts, w2)
        q_hs_sen_mech_vent = m_ve_mech * (h_ts_w2 - h_t2_w2)

    elif m_ve_mech == 0:  # mechanical ventilation system is not active, only recirculation air gets conditioned

        # supply air condition
        t3 = temp_sup_heat_hvac

        # State of Supply
        ts = t3  # minus expected delta T rise in the ducts TODO: check and document value of temp decrease
        w5 = wint
        h_w5_t5 = calc_h(t5, w5)

        # No humidification of recirculation air as there is no model yet for internal humidity assessment
        qe_hum = 0
        q_hs_sen_mech_vent = 0
        e_hs_lat_aux = 0
        t2 = temp_mech_vent

    else:
        raise

    # calculate the part of the sensible load that is supplied by conditioning the recirculation air
    # = additional load that has to be covered by conditioning room air through recirculation
    # additional load can not be smaller than 0, over heating situation
    q_hs_sen_recirculation = max(qe_sen - q_hs_sen_mech_vent, 0)
    h_ts_w5 = calc_h(ts, w5)
    m_ve_hvac_recirculation = q_hs_sen_recirculation / (h_ts_w5 - h_w5_t5)

    # output parameters
    q_hs_sen_hvac = (q_hs_sen_mech_vent + q_hs_sen_recirculation) * 1000
    q_hs_lat_hvac = qe_hum * 1000
    ma_sup_hs = m_ve_mech + m_ve_hvac_recirculation
    ta_sup_hs = ts
    ta_re_hs = (
               m_ve_mech * t2 + m_ve_hvac_recirculation * t5) / ma_sup_hs  # temperature mixing proportional to mass flow rates

    air_con_model_loads_flows_temperatures = {'q_hs_sen_hvac': q_hs_sen_hvac,
                                              'q_hs_lat_hvac': q_hs_lat_hvac,
                                              'ma_sup_hs': ma_sup_hs,
                                              'ta_sup_hs': ta_sup_hs,
                                              'ta_re_hs': ta_re_hs,
                                              'e_hs_lat_aux': e_hs_lat_aux,
                                              'm_ve_hvac_recirculation': m_ve_hvac_recirculation}

    if m_ve_mech + m_ve_hvac_recirculation < 0:
        raise ValueError

    return air_con_model_loads_flows_temperatures


# Moisture balance

def calc_w3_heating_case(t5, w2, w5, t3):
    """
    Algorithm 1 Determination of the room's supply moisture content (w3) for the heating case from Kaempf's HVAC model
    [Kämpf2009]_

    :param t5: temperature 5 in (°C)
    :type t5: numpy.float64

    :param w2: moisture content 2 in (kg/kg dry air)
    :type w2: numpy.float64

    :param w5: moisture content 5 in (kg/kg dry air)
    :type w5: numpy.float64

    :param t3: temperature 3 in (°C)
    :type t3: numpy.float64

    :return: w3, moisture content of HVAC supply air in (kg/kg dry air)
    :rtype: numpy.float64
    """

    # get constants and properties
    t_comf_max = temp_comf_max  # limits of comfort in zone TODO: get from properties
    hum_comf_max = rhum_comf_max  # limits of comfort in zone TODO: get from properties

    w_liminf = calc_w(t5, 30)  # TODO: document
    w_limsup = calc_w(t5, 70)  # TODO: document
    w_comf_max = calc_w(t_comf_max, hum_comf_max)  # moisture content at maximum comfortable state

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

    Source: [Kämpf2009]_

    :param t5: temperature 5 in (°C)
    :type t5: numpy.float64

    :param w2 : moisture content 2 in (kg/kg dry air)
    :type w2: numpy.float64

    :param t3: temperature 3 in (°C)
    :type t3: numpy.float64

    :param w5: moisture content 5 in (kg/kg dry air)
    :type w5: numpy.float64

    :return: w3, moisture content of HVAC supply air in (kg/kg dry air)
    :rtype: numpy.float64
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

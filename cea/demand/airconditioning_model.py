# -*- coding: utf-8 -*-
"""
Air conditioning equipment component models

"""

from __future__ import division
import numpy as np
from cea.demand import control_heating_cooling_systems
from cea.demand.latent_loads import convert_rh_to_moisture_content

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# ventilation demand controlled unit
"""
        qe_hum = m_ve_mech * (h_t2_ws - h_t2_w2)  # (kW) energy for humidification / latent heating demand

        # Adiabatic humidifier - computation of electrical auxiliary loads
        e_hs_lat_aux = 15 / 3600 * m_ve_mech  # assuming a performance of 15 W por Kg/h of humidified air source: bertagnolo 2012

        # heating load provided by conditioning ventilation air
        h_t2_w2 = calc_h(t2, w2)
        h_ts_w2 = calc_h(ts, w2)
        q_hs_sen_mech_vent = m_ve_mech * (h_ts_w2 - h_t2_w2)

"""

# air conditioning component models

H_WE = 2466e3  # (J/kg) Latent heat of vaporization of water [section 6.3.6 in ISO 52016-1:2007]

C_A = 1006  # (J/(kg*K)) Specific heat of air at constant pressure [section 6.3.6 in ISO 52016-1:2007]


def central_air_handling_unit_cooling(m_ve_mech, t_ve_mech_after_hex, x_ve_mech, bpr):
    """
    the central air handling unit acts on the mechanical ventilation air stream
    it has a fixed coil and fixed supply temperature
    the input is the cooling load that should be achieved, however over-cooling is possible
    dehumidification/latent cooling is a by product as the ventilation air is supplied at the coil temperature dew point

    Gabriel Happle, Feb. 2018

    :param m_ve_mech:
    :param t_ve_mech_after_hex:
    :param x_ve_mech:
    :param bpr:
    :return:
    """

    # look up supply and coil temperatures according to system
    if control_heating_cooling_systems.has_3for2_cooling_system(bpr) \
            or control_heating_cooling_systems.has_central_ac_cooling_system(bpr):
        t_sup_c_ahu = bpr.hvac['Tc_sup_air_ahu_C']  # (C) supply temperature of central ahu
        t_coil_c_ahu = bpr.hvac['Tscs0_ahu_C']  # (C) coil temperature of central ahu

    else:
        raise Exception('Not enough parameters specified for cooling system: %s' % bpr.hvac['type_cs'])

    # check if system is operated or bypassed
    if t_ve_mech_after_hex <= t_sup_c_ahu:  # no operation if incoming air temperature is lower than supply
        qc_sen_ahu = 0  # no load because no operation
        qc_lat_ahu = 0  # no load because no operation
        x_sup_c_ahu = x_ve_mech

        # temperatures and mass flows
        ma_sup_cs_ahu = 0
        ta_sup_cs_ahu = np.nan
        ta_re_cs_ahu = np.nan

        # TODO: check potential 3for2 operation in non-humid climates. According to Lukas...
        #  AHU might only be operated when dehumidification is necessary
        #  i.e., it could even be possible to bypass the system with 30C hot outdoor air

    else:

        # calculate the max moisture content at the coil temperature
        x_sup_c_ahu_max = convert_rh_to_moisture_content(100, t_coil_c_ahu)

        # calculate the system sensible cooling power
        qc_sen_ahu = m_ve_mech * C_A * (t_sup_c_ahu - t_ve_mech_after_hex)

        # calculate the supply moisture content
        x_sup_c_ahu = np.min([x_ve_mech, x_sup_c_ahu_max])

        # calculate the latent load in terms of water removed
        g_dhu_ahu = m_ve_mech * (x_sup_c_ahu - x_ve_mech)

        # calculate the latent load in terms of energy
        qc_lat_ahu = g_dhu_ahu * H_WE

        # temperatures and mass flows
        ma_sup_cs_ahu = m_ve_mech
        ta_sup_cs_ahu = t_sup_c_ahu
        ta_re_cs_ahu = t_ve_mech_after_hex

    # construct return dict
    return {'qc_sen_ahu': qc_sen_ahu, 'qc_lat_ahu': qc_lat_ahu, 'x_sup_c_ahu': x_sup_c_ahu,
            'ma_sup_cs_ahu': ma_sup_cs_ahu, 'ta_sup_cs_ahu': ta_sup_cs_ahu, 'ta_re_cs_ahu': ta_re_cs_ahu}


def central_air_handling_unit_heating(m_ve_mech, t_ve_mech_after_hex, x_ve_mech, bpr):
    """
    the central air handling unit acts on the mechanical ventilation air stream
    it has a fixed coil and fixed supply temperature
    the input is the heating load that should be achieved, however over-heating is possible

    Gabriel Happle, Feb. 2018

    :param m_ve_mech:
    :param t_ve_mech_after_hex:
    :param x_ve_mech:
    :param bpr:
    :return:
    """

    # TODO: humidification and its electricity demand

    # get supply air temperature from system properties
    t_sup_h_ahu = bpr.hvac['Th_sup_air_ahu_C']  # (C) supply temperature of central ahu
    t_coil_h_ahu = bpr.hvac['Tshs0_ahu_C']  # (C) coil temperature of central ahu

    # check if system is operated or bypassed
    if t_ve_mech_after_hex >= t_sup_h_ahu:  # no operation if incoming air temperature is higher than supply
        qh_sen_ahu = 0  # no load because no operation
        qh_lat_ahu = 0  # no load because no operation
        x_sup_h_ahu = x_ve_mech
        ma_sup_hs_ahu = 0
        ta_re_hs_ahu = np.nan
        ta_sup_hs_ahu = np.nan

    else:

        # calculate the max moisture content at the coil temperature
        x_sup_h_ahu_max = convert_rh_to_moisture_content(100, t_coil_h_ahu)

        # calculate the system sensible cooling power
        qh_sen_ahu = m_ve_mech * C_A * (t_sup_h_ahu - t_ve_mech_after_hex)

        # calculate the supply moisture content
        x_sup_h_ahu = np.min([x_ve_mech, x_sup_h_ahu_max])

        # calculate the latent load in terms of water removed
        g_hu_ahu = m_ve_mech * (x_sup_h_ahu - x_ve_mech)

        # calculate the latent load in terms of energy
        qh_lat_ahu = g_hu_ahu * H_WE

        # temperatures and mass flows
        ma_sup_hs_ahu = m_ve_mech
        ta_sup_hs_ahu = t_sup_h_ahu
        ta_re_hs_ahu = t_ve_mech_after_hex

    # construct return dict
    return {'qh_sen_ahu': qh_sen_ahu, 'qh_lat_ahu': qh_lat_ahu, 'x_sup_h_ahu': x_sup_h_ahu,
            'ma_sup_hs_ahu' : ma_sup_hs_ahu, 'ta_sup_hs_ahu' : ta_sup_hs_ahu, 'ta_re_hs_ahu' : ta_re_hs_ahu}


def local_air_recirculation_unit_heating(qh_sen_demand_aru, t_int_prev, bpr):
    """
    the local air recirculation unit recirculates internal air
    it determines the mass flow of air according to the demand of sensible heating
    it has a fixed coil and fixed supply temperature

    Gabriel Happle, Feb. 2018

    :param qh_sen_demand_aru:
    :param t_int_prev:
    :param bpr:
    :return:
    """

    # TODO: humidification and its electricity demand

    # get supply air temperature from system properties
    t_sup_h_aru = bpr.hvac['Th_sup_air_aru_C']  # (C) supply temperature of central ahu

    # calculate air mass flow to attain sensible demand
    m_ve_rec_req_sen = qh_sen_demand_aru / (C_A * (t_sup_h_aru - t_int_prev))  # TODO: take zone temp of t ???? how?

    # control: required = behavior
    m_ve_rec = m_ve_rec_req_sen

    # determine and return actual behavior
    qh_sen_aru = m_ve_rec * C_A * (t_sup_h_aru - t_int_prev)

    # temperatures and mass flows
    ma_sup_hs_aru = m_ve_rec
    ta_sup_hs_aru = t_sup_h_aru
    ta_re_hs_aru = t_int_prev

    return {'qh_sen_aru': qh_sen_aru, 'ma_sup_hs_aru' : ma_sup_hs_aru, 'ta_sup_hs_aru': ta_sup_hs_aru,
            'ta_re_hs_aru': ta_re_hs_aru}


def local_air_recirculation_unit_cooling(qc_sen_demand_aru, g_dhu_demand_aru, t_int_prev, x_int_prev, bpr, t_control,
                                         x_control):
    """
    the local air recirculation unit recirculates internal air
    it determines the mass flow of air according to the demand of sensible or latent cooling
    the air flow can be controlled by sensible OR latent load
    it has a fixed coil and fixed supply temperature
    dehumidification/latent cooling is a by product as the ventilation air is supplied at the coil temperature dew point

    Gabriel Happle, Feb. 2018

    :param qc_sen_demand_aru:
    :param g_dhu_demand_aru:
    :param t_int_prev:
    :param x_int_prev:
    :param bpr:
    :param t_control:
    :param x_control:
    :return:
    """

    # get supply air temperature from system properties
    t_sup_c_aru = bpr.hvac['Tc_sup_air_aru_C']  # (C) supply temperature of central ahu
    t_coil_c_aru = bpr.hvac['Tscs0_aru_C']  # (C) coil temperature of central ahu

    # calculate air mass flow to attain sensible demand
    m_ve_rec_req_sen = qc_sen_demand_aru / (C_A * (t_sup_c_aru - t_int_prev))  # TODO: take zone temp of t ???? how?

    # calculate the max moisture content at the coil temperature
    x_sup_c_aru_max = convert_rh_to_moisture_content(100, t_coil_c_aru)

    # calculate air mass flow to attain latent load
    m_ve_rec_req_lat = -g_dhu_demand_aru / (x_sup_c_aru_max - x_int_prev)  # TODO: take zone x of t ??? how?

    # determine recirculation air mass flow according to control type
    if t_control and not x_control:

        m_ve_rec = m_ve_rec_req_sen

    elif x_control and not t_control:

        m_ve_rec = m_ve_rec_req_lat

    elif t_control and x_control:

        m_ve_rec = np.max([m_ve_rec_req_sen, m_ve_rec_req_lat])

    else:
        raise Exception('at least one control parameter has to be "True"')

    # determine and return actual behavior
    qc_sen_aru = m_ve_rec * C_A * (t_sup_c_aru - t_int_prev)
    x_sup_c_aru = np.min([x_sup_c_aru_max, x_int_prev])
    g_dhu_aru = m_ve_rec * (x_sup_c_aru - x_int_prev)
    qc_lat_aru = g_dhu_aru * H_WE

    # temperatures and mass flows
    ma_sup_cs_aru = m_ve_rec
    ta_sup_cs_aru = t_sup_c_aru
    ta_re_cs_aru = t_int_prev

    return {'qc_sen_aru': qc_sen_aru, 'qc_lat_aru': qc_lat_aru, 'g_dhu_aru': g_dhu_aru, 'ma_sup_cs_aru': ma_sup_cs_aru,
            'ta_sup_cs_aru': ta_sup_cs_aru, 'ta_re_cs_aru': ta_re_cs_aru}


def local_sensible_cooling_unit():
    return

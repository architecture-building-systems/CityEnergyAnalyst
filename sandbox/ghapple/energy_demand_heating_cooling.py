# -*- coding: utf-8 -*-
"""

Calculation procedure for space heating and cooling
based on:
ISO 13790 [DIN EN ISO 13790:2008-9]


"""


from __future__ import division
import numpy as np
from sandbox.ghapple import helpers as h
from sandbox.ghapple import control
from sandbox.ghapple import rc_model_iso13790 as rc
from sandbox.ghapple import ventilation_xx as v


__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"



def procedure_1(hoy, bpr, tsd):

    """

    :param hoy:
    :param bpr:
    :param tsd:
    :return:
    """

    # +++++++++++++++++++++++++++++++
    # VENTILATION FOR HOUR
    # +++++++++++++++++++++++++++++++
    v.calc_m_ve_mech(bpr, tsd, hoy)



    # +++++++++++++++++++++++++++++++
    # HEATING COOLING DEMAND FOR HOUR
    # +++++++++++++++++++++++++++++++

    # check demand
    # ++++++++++++
    if not rc.has_heating_demand(bpr, tsd, hoy) and not rc.has_cooling_demand(bpr, tsd, hoy):

        # no heating or cooling demand
        # calculate temperatures of building R-C-model and exit
        # --> rc_model_function_1(...)
        phi_hc_nd = 0
        temp_rc = rc.calc_temperatures_crank_nicholson( phi_hc_nd, bpr, tsd, hoy )

        theta_m_t = temp_rc[0]
        theta_air = temp_rc[1]
        theta_op = temp_rc[2]

        q_hs_sen_incl_em_loss = 0
        em_loss_hs = 0
        q_cs_sen_incl_em_loss = 0
        em_loss_cs = 0

        # write to tsd
        tsd['Tm'][hoy] = theta_m_t
        tsd['Ta'][hoy] = theta_air
        tsd['Top'][hoy] = theta_op
        tsd['Qhs_sen'][hoy] = 0
        tsd['Qhs_em_ls'][hoy] = 0

        # return
        print('Building has no heating or cooling demand at hour', hoy)
        return

    elif rc.has_heating_demand (bpr, tsd, hoy):

        # has heating demand
        print('Building has heating demand at hour', hoy)
        # check if heating system is turned on

        if not control.is_heating_active(hoy, bpr):

            # no heating
            # calculate temperatures of building R-C-model and exit
            # --> rc_model_function_1(...)
            phi_hc_nd = 0
            temp_rc = rc.calc_temperatures_crank_nicholson(phi_hc_nd, bpr, tsd, hoy)

            theta_m_t = temp_rc[0]
            theta_air = temp_rc[1]
            theta_op = temp_rc[2]

            q_hs_sen_incl_em_loss = 0
            em_loss_hs = 0
            q_cs_sen_incl_em_loss = 0
            em_loss_cs = 0

            # return # TODO: check speed with and without return here
            # return

        elif control.is_heating_active(hoy, bpr) and control.heating_system_is_ac(bpr):


            # heating with AC
            # calculate loads and enter AC calculation
            # --> r_c_model_function_3(...)
            # --> kaempf_ac(...)
            # --> (iteration of air flows)
            # TODO: HVAC model
            print('HVAC')

        elif control.is_heating_active(hoy, bpr) and control.heating_system_is_radiative(bpr):

            # heating with radiative system
            # calculate loads and emission losses
            # --> rc_model_function_2(...)
            theta_m_t_ac,\
            theta_air_ac,\
            theta_op_ac,\
            phi_hc_nd_ac = rc.calc_phi_hc_ac(bpr, tsd, hoy)

            # TODO: losses
            # TODO: how to calculate losses if phi_h_ac is phi_h_max ???

    elif rc.has_cooling_demand(bpr, tsd, hoy):

        # has cooling demand
        print('Building has cooling demand at hour', hoy)
        # check if cooling system is turned on

        if not control.is_cooling_active(hoy, bpr):

            # no cooling
            # calculate temperatures of R-C-model and exit
            # --> rc_model_function_1(...)
            phi_hc_nd = 0
            temp_rc = rc.calc_temperatures_crank_nicholson(phi_hc_nd, bpr, tsd, hoy)

            theta_m_t = temp_rc[0]
            theta_air = temp_rc[1]
            theta_op = temp_rc[2]

            q_hs_sen_incl_em_loss = 0
            em_loss_hs = 0
            q_cs_sen_incl_em_loss = 0
            em_loss_cs = 0

            # return # TODO: check speed with and without return here
            # return

        elif control.is_cooling_active(hoy, bpr) and control.cooling_system_is_ac(bpr):

            # cooling with AC
            # calculate load and enter AC calculation
            # --> r_c_model_function_3(...)
            # --> kaempf_ac(...)
            # --> (iteration of air flows)
            # TODO: HVAC model
            print('HVAC')

        elif control.is_cooling_active(hoy, bpr) and control.cooling_system_is_radiative(bpr):

            # cooling with radiative system
            # calculate loads and emission losses
            # --> rc_model_function_2(...)
            theta_m_t_ac, \
            theta_air_ac, \
            theta_op_ac, \
            phi_hc_nd_ac = rc.calc_phi_hc_ac(building_thermal_prop)

            # TODO: losses

    else:
        print('Error: Unknown HVAC system status')
        return

    return












# TODO: night flushing: 9.3.3.10 in ISO 13790
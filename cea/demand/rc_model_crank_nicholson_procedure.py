# -*- coding: utf-8 -*-


from __future__ import division
from cea.demand import airconditioning_model, rc_model_SIA, control_heating_cooling_systems, \
    space_emission_systems

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def calc_rc_model_demand_heating_cooling(bpr, tsd, t, gv):

    """
    Crank-Nicholson Procedure to calculate heating / cooling demand of buildings
    following the procedure in 2.3.2 in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011 / Korrigenda C2 zum Mekblatt SIA 2044:2011

    Special procedures for updating ventilation air AC-heated and AC-cooled buildings

    Author: Gabriel Happle
    Date: 01/2017

    :param bpr: building properties row object
    :param tsd: time series data dict
    :param t: time step / hour of year [0..8760]
    :param gv: globalvars
    :return: updates values in tsd
    """

    # following the procedure in 2.3.2 in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011
    #  / Korrigenda C2 zum Mekblatt SIA 2044:2011

    # ++++++++++++++++++++++++++++++
    # CASE 0 - NO HEATING OR COOLING
    # ++++++++++++++++++++++++++++++
    if not control_heating_cooling_systems.is_active_heating_system(bpr, tsd, t) \
            and not control_heating_cooling_systems.is_active_cooling_system(bpr, tsd, t):

        # STEP 1
        # ******
        # calculate temperatures
        rc_model_temperatures = rc_model_SIA.calc_rc_model_temperatures_no_heating_cooling(bpr, tsd, t)

        # write to tsd
        tsd['T_int'][t] = rc_model_temperatures['T_int']
        tsd['theta_m'][t] = rc_model_temperatures['theta_m']
        tsd['theta_c'][t] = rc_model_temperatures['theta_c']
        tsd['theta_o'][t] = rc_model_temperatures['theta_o']
        update_tsd_no_cooling(tsd, t)
        update_tsd_no_heating(tsd, t)
        tsd['system_status'][t] = 'systems off'

    # ++++++++++++++++
    # CASE 1 - HEATING
    # ++++++++++++++++
    elif control_heating_cooling_systems.is_active_heating_system(bpr, tsd, t):
        # case for heating
        tsd['system_status'][t] = 'Radiative heating'

        # STEP 1
        # ******
        # calculate temperatures with 0 heating power
        rc_model_temperatures_0 = rc_model_SIA.calc_rc_model_temperatures_no_heating_cooling(bpr, tsd, t)

        T_int_0 = rc_model_temperatures_0['T_int']

        # STEP 2
        # ******
        # calculate temperatures with 10 W/m2 heating power
        phi_hc_10 = 10 * bpr.rc_model['Af']
        rc_model_temperatures_10 = rc_model_SIA.calc_rc_model_temperatures_heating(phi_hc_10, bpr, tsd, t)

        T_int_10 = rc_model_temperatures_10['T_int']

        T_int_set = tsd['ta_hs_set'][t]

        # interpolate heating power
        # (64) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011 / Korrigenda C2 zum Mekblatt SIA 2044:2011
        phi_hc_ul = phi_hc_10*(T_int_set - T_int_0) / (T_int_10 - T_int_0)

        # STEP 3
        # ******
        # check if available power is sufficient
        phi_h_max = bpr.hvac['Qhsmax_Wm2'] * bpr.rc_model['Af']

        if 0 < phi_hc_ul <= phi_h_max:
            # case heating with phi_hc_ul
            # calculate temperatures with this power
            phi_h_act = phi_hc_ul

        elif 0 < phi_hc_ul > phi_h_max:
            # case heating with max power available
            # calculate temperatures with this power
            phi_h_act = phi_h_max

        else:
            raise

        # STEP 4
        # ******
        rc_model_temperatures = rc_model_SIA.calc_rc_model_temperatures_heating(phi_h_act, bpr, tsd, t)
        # write necessary parameters for AC calculation to tsd
        tsd['T_int'][t] = rc_model_temperatures['T_int']
        tsd['theta_m'][t] = rc_model_temperatures['theta_m']
        tsd['theta_c'][t] = rc_model_temperatures['theta_c']
        tsd['theta_o'][t] = rc_model_temperatures['theta_o']
        tsd['Qhs_sen'][t] = phi_h_act
        tsd['Qhs_sen_sys'][t] = phi_h_act
        tsd['Qhs_lat_sys'][t] = 0
        tsd['Ehs_lat_aux'][t] = 0
        tsd['ma_sup_hs'][t] = 0
        tsd['Ta_sup_hs'][t] = 0
        tsd['Ta_re_hs'][t] = 0
        tsd['m_ve_recirculation'][t] = 0

        # STEP 5 - latent and sensible heat demand of AC systems
        # ******
        if control_heating_cooling_systems.heating_system_is_ac(bpr):
            air_con_model_loads_flows_temperatures = airconditioning_model.calc_hvac_heating(tsd, t)

            tsd['system_status'][t] = 'AC heating'

            # update temperatures for over heating case
            if air_con_model_loads_flows_temperatures['q_hs_sen_hvac'] > phi_h_act:
                phi_h_act_over_heating = air_con_model_loads_flows_temperatures['q_hs_sen_hvac']
                rc_model_temperatures = rc_model_SIA.calc_rc_model_temperatures_heating(
                    phi_h_act_over_heating, bpr, tsd,
                    t)

                # update temperatures
                tsd['T_int'][t] = rc_model_temperatures['T_int']
                tsd['theta_m'][t] = rc_model_temperatures['theta_m']
                tsd['theta_c'][t] = rc_model_temperatures['theta_c']
                tsd['theta_o'][t] = rc_model_temperatures['theta_o']
                tsd['system_status'][t] = 'AC over heating'

            # update AC energy demand
            tsd['Qhs_sen_sys'][t] = air_con_model_loads_flows_temperatures['q_hs_sen_hvac']
            tsd['Qhs_lat_sys'][t] = air_con_model_loads_flows_temperatures['q_hs_lat_hvac']
            tsd['ma_sup_hs'][t] = air_con_model_loads_flows_temperatures['ma_sup_hs']
            tsd['Ta_sup_hs'][t] = air_con_model_loads_flows_temperatures['ta_sup_hs']
            tsd['Ta_re_hs'][t] = air_con_model_loads_flows_temperatures['ta_re_hs']
            tsd['Ehs_lat_aux'][t] = air_con_model_loads_flows_temperatures['e_hs_lat_aux']
            tsd['m_ve_recirculation'][t] = air_con_model_loads_flows_temperatures['m_ve_hvac_recirculation']

        # STEP 6 - emission system losses
        # ******
        q_em_ls_heating = space_emission_systems.calc_q_em_ls_heating(bpr, tsd, t)

        # set temperatures to tsd for heating
        tsd['T_int'][t] = rc_model_temperatures['T_int']
        tsd['theta_m'][t] = rc_model_temperatures['theta_m']
        tsd['theta_c'][t] = rc_model_temperatures['theta_c']
        tsd['theta_o'][t] = rc_model_temperatures['theta_o']
        tsd['Qhs_lat_sys'][t] = 0
        tsd['Qhs_em_ls'][t] = q_em_ls_heating
        tsd['Qhs_sen'][t] = phi_h_act
        tsd['Qhsf'][t] = 0
        tsd['Qhsf_lat'][t] = 0
        update_tsd_no_cooling(tsd, t)

    # ++++++++++++++++
    # CASE 2 - COOLING
    # ++++++++++++++++
    elif control_heating_cooling_systems.is_active_cooling_system(bpr, tsd, t):

        # case for cooling
        tsd['system_status'][t] = 'Radiative cooling'

        # STEP 1
        # ******
        # calculate temperatures with 0 heating power
        rc_model_temperatures_0 = rc_model_SIA.calc_rc_model_temperatures_no_heating_cooling(bpr, tsd, t)

        T_int_0 = rc_model_temperatures_0['T_int']

        # STEP 2
        # ******
        # calculate temperatures with 10 W/m2 cooling power
        phi_hc_10 = 10 * bpr.rc_model['Af']
        rc_model_temperatures_10 = rc_model_SIA.calc_rc_model_temperatures_cooling(phi_hc_10, bpr, tsd, t)

        T_int_10 = rc_model_temperatures_10['T_int']

        T_int_set = tsd['ta_cs_set'][t]

        # interpolate heating power
        # (64) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011 / Korrigenda C2 zum Mekblatt SIA 2044:2011
        phi_hc_ul = phi_hc_10 * (T_int_set - T_int_0) / (T_int_10 - T_int_0)

        # STEP 3
        # ******
        # check if available power is sufficient
        phi_c_max = -bpr.hvac['Qcsmax_Wm2'] * bpr.rc_model['Af']

        if 0 > phi_hc_ul >= phi_c_max:
            # case heating with phi_hc_ul
            # calculate temperatures with this power
            phi_c_act = phi_hc_ul

        elif 0 > phi_hc_ul < phi_c_max:
            # case heating with max power available
            # calculate temperatures with this power
            phi_c_act = phi_c_max

        else:
            raise

        # STEP 4
        # ******
        rc_model_temperatures = rc_model_SIA.calc_rc_model_temperatures_cooling(phi_c_act, bpr, tsd, t)

        # write necessary parameters for AC calculation to tsd
        tsd['T_int'][t] = rc_model_temperatures['T_int']
        tsd['theta_m'][t] = rc_model_temperatures['theta_m']
        tsd['theta_c'][t] = rc_model_temperatures['theta_c']
        tsd['theta_o'][t] = rc_model_temperatures['theta_o']
        tsd['Qcs_sen'][t] = phi_c_act
        tsd['Qcs_sen_sys'][t] = phi_c_act
        tsd['Qcs_lat_sys'][t] = 0
        tsd['ma_sup_cs'][t] = 0
        tsd['m_ve_recirculation'][t] = 0

        # STEP 5 - latent and sensible heat demand of AC systems
        # ******
        if control_heating_cooling_systems.cooling_system_is_ac(bpr):

            tsd['system_status'][t] = 'AC cooling'

            air_con_model_loads_flows_temperatures = airconditioning_model.calc_hvac_cooling(tsd, t)

            # update temperatures for over cooling case
            if air_con_model_loads_flows_temperatures['q_cs_sen_hvac'] < phi_c_act:

                phi_c_act_over_cooling = air_con_model_loads_flows_temperatures['q_cs_sen_hvac']
                rc_model_temperatures = rc_model_SIA.calc_rc_model_temperatures_cooling(phi_c_act_over_cooling, bpr, tsd,
                                                                                        t)
                # update temperatures
                tsd['T_int'][t] = rc_model_temperatures['T_int']
                tsd['theta_m'][t] = rc_model_temperatures['theta_m']
                tsd['theta_c'][t] = rc_model_temperatures['theta_c']
                tsd['theta_o'][t] = rc_model_temperatures['theta_o']
                tsd['system_status'][t] = 'AC over cooling'

            # update AC energy demand

            tsd['Qcs_sen_sys'][t] = air_con_model_loads_flows_temperatures['q_cs_sen_hvac']
            tsd['Qcs_lat_sys'][t] = air_con_model_loads_flows_temperatures['q_cs_lat_hvac']
            tsd['ma_sup_cs'][t] = air_con_model_loads_flows_temperatures['ma_sup_cs']
            tsd['Ta_sup_cs'][t] = air_con_model_loads_flows_temperatures['ta_sup_cs']
            tsd['Ta_re_cs'][t] = air_con_model_loads_flows_temperatures['ta_re_cs']
            tsd['m_ve_recirculation'][t] = air_con_model_loads_flows_temperatures['m_ve_hvac_recirculation']
            tsd['q_cs_lat_peop'][t] = air_con_model_loads_flows_temperatures['q_cs_lat_peop']

        # STEP 6 - emission system losses
        # ******
        q_em_ls_cooling = space_emission_systems.calc_q_em_ls_cooling(bpr, tsd, t)

        # set temperatures to tsd for cooling
        tsd['T_int'][t] = rc_model_temperatures['T_int']
        tsd['theta_m'][t] = rc_model_temperatures['theta_m']
        tsd['theta_c'][t] = rc_model_temperatures['theta_c']
        tsd['theta_o'][t] = rc_model_temperatures['theta_o']
        tsd['Qcs'][t] = 0
        tsd['Qcs_em_ls'][t] = q_em_ls_cooling
        tsd['Qcsf'][t] = 0
        tsd['Qcsf_lat'][t] = 0
        update_tsd_no_heating(tsd, t)

    detailed_thermal_balance_to_tsd(tsd, bpr, t, rc_model_temperatures, gv)

    return


def update_tsd_no_heating(tsd, t):
    """
    updates NaN values in tsd for case of no heating demand

    Author: Gabriel Happle
    Date: 01/2017

    :param tsd: time series data dict
    :param t: time step / hour of year [0..8760]
    :return: updates tsd values
    """

    tsd['Qhs_sen'][t] = 0
    tsd['Qhs_sen_sys'][t] = 0
    tsd['Qhs_lat_sys'][t] = 0
    tsd['Qhs_em_ls'][t] = 0
    tsd['ma_sup_hs'][t] = 0
    tsd['Ta_sup_hs'][t] = 0  # TODO: this is dangerous as there is no temperature needed, 0 is necessary for 'calc_temperatures_emission_systems' to work
    tsd['Ta_re_hs'][t] = 0  # TODO: this is dangerous as there is no temperature needed, 0 is necessary for 'calc_temperatures_emission_systems' to work
    tsd['Ehs_lat_aux'][t] = 0
    tsd['m_ve_recirculation'][t] = 0

    return


def update_tsd_no_cooling(tsd, t):
    """
    updates NaN values in tsd for case of no cooling demand

    Author: Gabriel Happle
    Date: 01/2017

    :param tsd: time series data dict
    :param t: time step / hour of year [0..8760]
    :return: updates tsd values
    """

    tsd['Qcs_sen'][t] = 0
    tsd['Qcs_sen_sys'][t] = 0
    tsd['Qcs_lat_sys'][t] = 0
    tsd['Qcs_em_ls'][t] = 0
    tsd['ma_sup_cs'][t] = 0
    tsd['Ta_sup_cs'][t] = 0  # TODO: this is dangerous as there is no temperature needed, 0 is necessary for 'calc_temperatures_emission_systems' to work
    tsd['Ta_re_cs'][t] = 0  # TODO: this is dangerous as there is no temperature needed, 0 is necessary for 'calc_temperatures_emission_systems' to work
    tsd['m_ve_recirculation'][t] = 0

    return


def detailed_thermal_balance_to_tsd(tsd, bpr, t, rc_model_temperatures, gv):

    # internal gains from lights
    tsd['Qgain_light'][t] = rc_model_SIA.calc_phi_i_l(tsd['Elf'][t])
    # internal gains from appliances, data centres and losses from refrigeration
    tsd['Qgain_app'][t] = rc_model_SIA.calc_phi_i_a(tsd['Eaf'][t], 0, 0)
    tsd['Qgain_data'][t] = tsd['Qcdataf'][t]
    tsd['Q_cool_ref'] = -tsd['Qcref'][t]
    # internal gains from people
    tsd['Qgain_pers'][t] = rc_model_SIA.calc_phi_i_p(tsd['Qs'][t])

    # losses / gains from ventilation
    #tsd['']

    # extract detailed rc model intermediate results
    h_em = rc_model_temperatures['h_em']
    h_op_m = rc_model_temperatures['h_op_m']
    theta_m = rc_model_temperatures['theta_m']
    theta_em = rc_model_temperatures['theta_em']
    h_ec = rc_model_temperatures['h_ec']
    theta_c = rc_model_temperatures['theta_c']
    theta_ec = rc_model_temperatures['theta_ec']
    h_ea = rc_model_temperatures['h_ea']
    T_int = rc_model_temperatures['T_int']
    theta_ea = rc_model_temperatures['theta_ea']

    # backwards calculate individual heat transfer coefficient
    h_wall_em = h_em * bpr.rc_model['Aop_sup'] * bpr.rc_model['U_wall'] / h_op_m
    h_base_em = h_em * bpr.rc_model['Aop_bel'] * gv.Bf * bpr.rc_model['U_base'] / h_op_m
    h_roof_em = h_em * bpr.rc_model['Aroof'] * bpr.rc_model['U_roof'] / h_op_m

    # calculate heat fluxes between mass and outside through opaque elements
    tsd['Qgain_wall'][t] = h_wall_em * (theta_em - theta_m)
    tsd['Qgain_base'][t] = h_base_em * (theta_em - theta_m)
    tsd['Qgain_roof'][t] = h_roof_em * (theta_em - theta_m)

    # calculate heat fluxes between central and outside through windows
    tsd['Qgain_wind'][t] = h_ec * (theta_ec - theta_c)

    # calculate heat between outside and inside air through ventilation
    tsd['Qgain_vent'][t] = h_ea * (theta_ea - T_int)

    return
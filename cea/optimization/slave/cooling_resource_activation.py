from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import numpy as np

import cea.technologies.chiller_absorption as chiller_absorption
import cea.technologies.chiller_vapor_compression as chiller_vapor_compression
import cea.technologies.cooling_tower as CTModel
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.optimization.constants import VCC_T_COOL_IN, DT_COOL, ACH_T_IN_FROM_CHP_K
from cea.technologies.constants import G_VALUE_CENTRALIZED  # this is where to differentiate chiller performances
from cea.technologies.pumps import calc_water_body_uptake_pumping
import cea.technologies.chiller_absorption
import pandas as pd

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Shanshan Hsieh", "Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_vcc_operation(Qc_from_VCC_W, T_DCN_re_K, T_DCN_sup_K, T_source_K, chiller_size, min_VCC_capacity, max_VCC_capacity, scale):
    g_value = G_VALUE_CENTRALIZED # get the isentropic efficiency of the district cooling
    Qc_from_VCC_W = min(Qc_from_VCC_W, chiller_size) # The chiller can not supply more cooling than the installed capacity allows
    VCC_operation = chiller_vapor_compression.calc_VCC(chiller_size, Qc_from_VCC_W, T_DCN_sup_K, T_DCN_re_K, T_source_K,
                                                       g_value, min_VCC_capacity, max_VCC_capacity, scale)

    # unpack outputs
    Qc_VCC_W = VCC_operation['q_chw_W']
    E_used_VCC_W = VCC_operation['wdot_W']

    return Qc_VCC_W, E_used_VCC_W


def calc_vcc_CT_operation(Qc_from_VCC_W,
                          T_DCN_re_K,
                          T_DCN_sup_K,
                          T_source_K,
                          size_chiller_CT,
                          min_VCC_capacity,
                          max_VCC_capacity,
                          scale):

    g_value = G_VALUE_CENTRALIZED
    VCC_operation = chiller_vapor_compression.calc_VCC(size_chiller_CT, Qc_from_VCC_W, T_DCN_sup_K, T_DCN_re_K, T_source_K,
                                                       g_value, min_VCC_capacity, max_VCC_capacity, scale)

    # unpack outputs
    Qc_CT_VCC_W = VCC_operation['q_cw_W']
    Qc_VCC_W = VCC_operation['q_chw_W']

    # calculate cooling tower
    wdot_CT_Wh = CTModel.calc_CT(Qc_CT_VCC_W, size_chiller_CT)

    # calcualte energy consumption and variable costs
    E_used_VCC_W = (VCC_operation['wdot_W'] + wdot_CT_Wh)

    return Qc_VCC_W, E_used_VCC_W


def calc_chiller_absorption_operation(Qc_ACH_req_W, T_DCN_re_K, T_DCN_sup_K, T_ACH_in_C, T_ground_K, chiller_prop,
                                      size_ACH_W):
    if T_DCN_re_K == T_DCN_sup_K:
        mdot_ACH_kgpers = 0
    else:
        mdot_ACH_kgpers = Qc_ACH_req_W / (
                (T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)  # required chw flow rate from ACH

    ACH_operation = chiller_absorption.calc_chiller_main(mdot_ACH_kgpers,
                                                         T_DCN_sup_K,
                                                         T_DCN_re_K,
                                                         T_ACH_in_C,
                                                         T_ground_K,
                                                         chiller_prop)

    Qc_CT_ACH_W = ACH_operation['q_cw_W']

    # calculate cooling tower
    wdot_CT_Wh = CTModel.calc_CT(Qc_CT_ACH_W, size_ACH_W)

    # calcualte energy consumption and variable costs
    Qh_CHP_ACH_W = ACH_operation['q_hw_W']
    E_used_ACH_W = ACH_operation['wdot_W'] + wdot_CT_Wh

    return Qc_CT_ACH_W, Qh_CHP_ACH_W, E_used_ACH_W


def cooling_resource_activator(Q_thermal_req,
                               T_district_cooling_supply_K,
                               T_district_cooling_return_K,
                               Q_therm_Lake_W,
                               T_source_average_Lake_K,
                               daily_storage_class,
                               T_ground_K,
                               master_to_slave_variables,
                               absorption_chiller,
                               CCGT_operation_data,
                               min_VCC_capacity,
                               max_VCC_capacity):
    """

    :param Q_thermal_req:
    :param T_district_cooling_supply_K:
    :param T_district_cooling_return_K:
    :param Q_therm_Lake_W:
    :param T_source_average_Lake_K:
    :param daily_storage_class:
    :param T_ground_K:
    :param master_to_slave_variables:
    :param cea.technologies.chiller_absorption.AbsorptionChiller absorption_chiller:
    :param CCGT_operation_data:
    :return:
    """
    scale = 'DISTRICT'
    ## initializing unmet cooling load and requirements from daily storage for this hour
    Q_cooling_unmet_W = Q_thermal_req
    Q_DailyStorage_gen_directload_W = 0.0

    ## ACTIVATE THE TRIGEN
    if master_to_slave_variables.NG_Trigen_on == 1 and Q_cooling_unmet_W > 0.0 and not np.isclose(
            T_district_cooling_supply_K,
            T_district_cooling_return_K):
        size_trigen_W = master_to_slave_variables.NG_Trigen_ACH_size_W
        if Q_cooling_unmet_W > size_trigen_W:
            Q_Trigen_gen_W = size_trigen_W
        else:
            Q_Trigen_gen_W = Q_cooling_unmet_W

        # GET THE ABSORPTION CHILLER PERFORMANCE
        T_ACH_in_C = ACH_T_IN_FROM_CHP_K - 273
        Qc_CT_ACH_W, \
        Qh_CCGT_req_W, \
        E_ACH_req_W = calc_chiller_absorption_operation(Q_Trigen_gen_W,
                                                        T_district_cooling_return_K,
                                                        T_district_cooling_supply_K,
                                                        T_ACH_in_C,
                                                        T_ground_K,
                                                        absorption_chiller,
                                                        size_trigen_W)

        # operation of the CCGT
        Q_used_prim_CC_fn_W = CCGT_operation_data['q_input_fn_q_output_W']
        q_output_CC_min_W = CCGT_operation_data['q_output_min_W']
        Q_output_CC_max_W = CCGT_operation_data['q_output_max_W']
        eta_elec_interpol = CCGT_operation_data['eta_el_fn_q_input']

        # TODO: CONFIRM THAT THIS WORKS AS INTENDED
        if Qh_CCGT_req_W >= q_output_CC_min_W:
            if Q_cooling_unmet_W > size_trigen_W:
                Q_Trigen_NG_gen_directload_W = size_trigen_W
                Qc_Trigen_gen_storage_W = 0.0
                Qc_from_storage_W = daily_storage_class.discharge_storage(Q_cooling_unmet_W - size_trigen_W)
                Q_Trigen_gen_W = Q_Trigen_NG_gen_directload_W + Qc_Trigen_gen_storage_W
            else:
                Q_Trigen_NG_gen_directload_W = Q_cooling_unmet_W
                Qc_Trigen_gen_storage_W = daily_storage_class.charge_storage(size_trigen_W - Q_cooling_unmet_W)
                Qc_from_storage_W = 0.0
                Q_Trigen_gen_W = Q_Trigen_NG_gen_directload_W + Qc_Trigen_gen_storage_W

            T_ACH_in_C = ACH_T_IN_FROM_CHP_K - 273
            Qc_CT_ACH_W, \
            Qh_CCGT_req_W, \
            E_ACH_req_W = calc_chiller_absorption_operation(Q_Trigen_gen_W,
                                                            T_district_cooling_return_K,
                                                            T_district_cooling_supply_K,
                                                            T_ACH_in_C,
                                                            T_ground_K,
                                                            absorption_chiller,
                                                            size_trigen_W)
            # operation Possible if above minimal load
            if Qh_CCGT_req_W <= Q_output_CC_max_W:  # Normal operation Possible within partload regime
                Q_CHP_gen_W = float(Qh_CCGT_req_W)
                NG_Trigen_req_W = Q_used_prim_CC_fn_W(Q_CHP_gen_W)
                E_Trigen_NG_gen_W = np.float(eta_elec_interpol(NG_Trigen_req_W)) * NG_Trigen_req_W

            else:  # Only part of the demand can be delivered as 100% load achieved
                Q_CHP_gen_W = Q_output_CC_max_W
                NG_Trigen_req_W = Q_used_prim_CC_fn_W(Q_CHP_gen_W)
                E_Trigen_NG_gen_W = np.float(eta_elec_interpol(NG_Trigen_req_W)) * NG_Trigen_req_W
        else:
            Q_Trigen_gen_W = 0.0
            NG_Trigen_req_W = 0.0
            E_Trigen_NG_gen_W = 0.0
            Q_Trigen_NG_gen_directload_W = 0.0
            Qc_from_storage_W = 0.0

        # update unmet cooling load
        Q_cooling_unmet_W = Q_cooling_unmet_W - Q_Trigen_NG_gen_directload_W - Qc_from_storage_W
        Q_DailyStorage_gen_directload_W += Qc_from_storage_W
    else:
        Q_Trigen_gen_W = 0.0
        NG_Trigen_req_W = 0.0
        E_Trigen_NG_gen_W = 0.0
        Q_Trigen_NG_gen_directload_W = 0.0

    # Base VCC water-source
    if master_to_slave_variables.WS_BaseVCC_on == 1 and Q_cooling_unmet_W > 0.0 and T_source_average_Lake_K < VCC_T_COOL_IN and not np.isclose(
            T_district_cooling_supply_K,
            T_district_cooling_return_K):
        # Free cooling possible from the lake
        size_WS_BaseVCC_W = master_to_slave_variables.WS_BaseVCC_size_W
        if Q_cooling_unmet_W > min(size_WS_BaseVCC_W, Q_therm_Lake_W): # min funtion to deal with both constraints at the same time, limiting  factors being the size and the temal capacity of lake
            Q_BaseVCC_WS_gen_directload_W = min(size_WS_BaseVCC_W, Q_therm_Lake_W)
            Qc_BaseVCC_WS_gen_storage_W = 0.0
            Qc_from_storage_W = daily_storage_class.discharge_storage(Q_cooling_unmet_W - min(size_WS_BaseVCC_W, Q_therm_Lake_W))
            Q_BaseVCC_WS_gen_W = Q_BaseVCC_WS_gen_directload_W + Qc_BaseVCC_WS_gen_storage_W
        else:
            Q_BaseVCC_WS_gen_directload_W = Q_cooling_unmet_W
            Qc_BaseVCC_WS_gen_storage_W = daily_storage_class.charge_storage(min(size_WS_BaseVCC_W, Q_therm_Lake_W) - Q_cooling_unmet_W)
            Qc_from_storage_W = 0.0
            Q_BaseVCC_WS_gen_W = Q_BaseVCC_WS_gen_directload_W + Qc_BaseVCC_WS_gen_storage_W
        if (T_district_cooling_supply_K - DT_COOL) < T_source_average_Lake_K < VCC_T_COOL_IN: # if lake temperature lower than CT source, use compression chillers with lake water as source
            WS_BaseVCC_capacity = master_to_slave_variables.WS_BaseVCC_size_W
            Q_BaseVCC_WS_gen_W, \
            E_BaseVCC_WS_req_W = calc_vcc_operation(Q_BaseVCC_WS_gen_W,
                                                    T_district_cooling_return_K,
                                                    T_district_cooling_supply_K,
                                                    T_source_average_Lake_K,
                                                    WS_BaseVCC_capacity,
                                                    min_VCC_capacity,
                                                    max_VCC_capacity,
                                                    scale)

            # Delta P from linearization after distribution optimization
            E_pump_WS_req_W = calc_water_body_uptake_pumping(Q_BaseVCC_WS_gen_W,
                                                             T_district_cooling_return_K,
                                                             T_district_cooling_supply_K)

            E_BaseVCC_WS_req_W += E_pump_WS_req_W


        elif T_source_average_Lake_K <= (T_district_cooling_supply_K - DT_COOL):  # bypass, do not use chiller but use heat exchange to cool the water directly
            E_pump_WS_req_W = calc_water_body_uptake_pumping(Q_BaseVCC_WS_gen_W,
                                                             T_district_cooling_return_K,
                                                             T_district_cooling_supply_K)
            E_BaseVCC_WS_req_W = E_pump_WS_req_W
        else:
            print("no lake water source baseload VCC was used")
        Q_therm_Lake_W -= Q_BaseVCC_WS_gen_W  # discount availability
        Q_cooling_unmet_W = Q_cooling_unmet_W - Q_BaseVCC_WS_gen_W - Qc_from_storage_W + Qc_BaseVCC_WS_gen_storage_W # the provided cooling equals the produced cooling plus the cooling from storage minus the stored cooling
        Q_DailyStorage_gen_directload_W += Qc_from_storage_W
    else:
        Q_BaseVCC_WS_gen_W = 0.0
        E_BaseVCC_WS_req_W = 0.0
        Q_BaseVCC_WS_gen_directload_W = 0.0

    # Peak VCC water-source
    if master_to_slave_variables.WS_PeakVCC_on == 1 and Q_cooling_unmet_W > 0.0 and T_source_average_Lake_K < VCC_T_COOL_IN and not np.isclose(
            T_district_cooling_supply_K,
            T_district_cooling_return_K):
        # Free cooling possible from the lake
        size_WS_PeakVCC_W = master_to_slave_variables.WS_PeakVCC_size_W
        if Q_cooling_unmet_W > min(size_WS_PeakVCC_W, Q_therm_Lake_W):
            Q_PeakVCC_WS_gen_directload_W = min(size_WS_PeakVCC_W, Q_therm_Lake_W)
            Qc_PeakVCC_WS_gen_storage_W = 0.0
            Qc_from_storage_W = daily_storage_class.discharge_storage(Q_cooling_unmet_W - min(size_WS_PeakVCC_W, Q_therm_Lake_W))
            Q_PeakVCC_WS_gen_W = Q_PeakVCC_WS_gen_directload_W + Qc_PeakVCC_WS_gen_storage_W
        else:
            Q_PeakVCC_WS_gen_directload_W = Q_cooling_unmet_W
            Qc_PeakVCC_WS_gen_storage_W = daily_storage_class.charge_storage(min(size_WS_PeakVCC_W, Q_therm_Lake_W) - Q_cooling_unmet_W)
            Qc_from_storage_W = 0.0
            Q_PeakVCC_WS_gen_W = Q_PeakVCC_WS_gen_directload_W + Qc_PeakVCC_WS_gen_storage_W

        if (T_district_cooling_supply_K - DT_COOL) < T_source_average_Lake_K < VCC_T_COOL_IN:
            WS_PeakVCC_capacity = master_to_slave_variables.WS_PeakVCC_size_W
            Q_PeakVCC_WS_gen_W, \
            E_PeakVCC_WS_req_W = calc_vcc_operation(Q_PeakVCC_WS_gen_W,
                                                    T_district_cooling_return_K,
                                                    T_district_cooling_supply_K,
                                                    T_source_average_Lake_K,
                                                    WS_PeakVCC_capacity,
                                                    min_VCC_capacity,
                                                    max_VCC_capacity,
                                                    scale)
            E_pump_WS_req_W = calc_water_body_uptake_pumping(Q_PeakVCC_WS_gen_W,
                                                             T_district_cooling_return_K,
                                                             T_district_cooling_supply_K)

            E_PeakVCC_WS_req_W += E_pump_WS_req_W

        elif T_source_average_Lake_K <= (T_district_cooling_supply_K - DT_COOL):  # bypass, do not use VCC but use heat exchange to cool the water directly
            E_pump_WS_req_W = calc_water_body_uptake_pumping(Q_PeakVCC_WS_gen_W,
                                                             T_district_cooling_return_K,
                                                             T_district_cooling_supply_K)
            E_PeakVCC_WS_req_W = E_pump_WS_req_W

        else:
            print("no lake water source baseload VCC was used")
        Q_therm_Lake_W -= Q_PeakVCC_WS_gen_W  # discount availability
        Q_cooling_unmet_W = Q_cooling_unmet_W - Q_PeakVCC_WS_gen_W - Qc_from_storage_W + Qc_PeakVCC_WS_gen_storage_W # the provided cooling equals the produced cooling plus the cooling from storage minus
        Q_DailyStorage_gen_directload_W += Qc_from_storage_W

    else:
        Q_PeakVCC_WS_gen_directload_W = 0.0
        Q_PeakVCC_WS_gen_W = 0.0
        E_PeakVCC_WS_req_W = 0.0

    # Base VCC air-source with a cooling tower
    if master_to_slave_variables.AS_BaseVCC_on == 1 and Q_cooling_unmet_W > 0.0 and not np.isclose(
            T_district_cooling_supply_K,
            T_district_cooling_return_K):
        size_AS_BaseVCC_W = master_to_slave_variables.AS_BaseVCC_size_W
        if Q_cooling_unmet_W > size_AS_BaseVCC_W:
            Q_BaseVCC_AS_gen_directload_W = size_AS_BaseVCC_W
            Q_BaseVCC_AS_gen_storage_W = 0.0
            Qc_from_storage_W = daily_storage_class.discharge_storage(Q_cooling_unmet_W - size_AS_BaseVCC_W)
            Q_BaseVCC_AS_gen_W = Q_BaseVCC_AS_gen_directload_W + Q_BaseVCC_AS_gen_storage_W
        else:
            Q_BaseVCC_AS_gen_directload_W = Q_cooling_unmet_W
            Q_BaseVCC_AS_gen_storage_W = daily_storage_class.charge_storage(size_AS_BaseVCC_W - Q_cooling_unmet_W)
            Qc_from_storage_W = 0.0
            Q_BaseVCC_AS_gen_W = Q_BaseVCC_AS_gen_directload_W + Q_BaseVCC_AS_gen_storage_W

        Q_BaseVCC_AS_gen_W, \
        E_BaseVCC_AS_req_W = calc_vcc_CT_operation(Q_BaseVCC_AS_gen_W,
                                                   T_district_cooling_return_K,
                                                   T_district_cooling_supply_K,
                                                   VCC_T_COOL_IN,
                                                   size_AS_BaseVCC_W,
                                                   min_VCC_capacity,
                                                   max_VCC_capacity,
                                                   scale)
        Q_cooling_unmet_W = Q_cooling_unmet_W - Q_BaseVCC_AS_gen_directload_W - Qc_from_storage_W
        Q_DailyStorage_gen_directload_W += Qc_from_storage_W
    else:
        Q_BaseVCC_AS_gen_W = 0.0
        E_BaseVCC_AS_req_W = 0.0
        Q_BaseVCC_AS_gen_directload_W = 0.0

    # Peak VCC air-source with a cooling tower
    if master_to_slave_variables.AS_PeakVCC_on == 1 and Q_cooling_unmet_W > 0.0 and not np.isclose(
            T_district_cooling_supply_K,
            T_district_cooling_return_K):
        size_AS_PeakVCC_W = master_to_slave_variables.AS_PeakVCC_size_W
        if Q_cooling_unmet_W > size_AS_PeakVCC_W:
            Q_PeakVCC_AS_gen_directload_W = size_AS_PeakVCC_W
            Q_PeakVCC_AS_gen_storage_W = 0.0
            Qc_from_storage_W = daily_storage_class.discharge_storage(Q_cooling_unmet_W - size_AS_PeakVCC_W)
            Q_PeakVCC_AS_gen_W = Q_PeakVCC_AS_gen_directload_W + Q_PeakVCC_AS_gen_storage_W
        else:
            Q_PeakVCC_AS_gen_directload_W = Q_cooling_unmet_W
            Q_PeakVCC_AS_gen_storage_W = daily_storage_class.charge_storage(size_AS_PeakVCC_W - Q_cooling_unmet_W)
            Qc_from_storage_W = 0.0
            Q_PeakVCC_AS_gen_W = Q_PeakVCC_AS_gen_directload_W + Q_PeakVCC_AS_gen_storage_W

        Q_PeakVCC_AS_gen_W, \
        E_PeakVCC_AS_req_W = calc_vcc_CT_operation(Q_PeakVCC_AS_gen_W,
                                                   T_district_cooling_return_K,
                                                   T_district_cooling_supply_K,
                                                   VCC_T_COOL_IN,
                                                   size_AS_PeakVCC_W,
                                                   min_VCC_capacity,
                                                   max_VCC_capacity,
                                                   scale)

        Q_cooling_unmet_W = Q_cooling_unmet_W - Q_PeakVCC_AS_gen_directload_W - Qc_from_storage_W
        Q_DailyStorage_gen_directload_W += Qc_from_storage_W
    else:
        Q_PeakVCC_AS_gen_W = 0.0
        E_PeakVCC_AS_req_W = 0.0
        Q_BaseVCC_AS_gen_directload_W = 0.0
        Q_PeakVCC_AS_gen_directload_W = 0.0

    if Q_cooling_unmet_W > 1.0E-3:
        Q_BackupVCC_AS_gen_W = Q_cooling_unmet_W  # this will become the back-up chiller
        Q_BackupVCC_AS_directload_W = Q_cooling_unmet_W
    else:
        Q_BackupVCC_AS_gen_W = 0.0
        Q_BackupVCC_AS_directload_W = 0.0

    ## writing outputs
    electricity_output = {
        'E_BaseVCC_WS_req_W': E_BaseVCC_WS_req_W,
        'E_PeakVCC_WS_req_W': E_PeakVCC_WS_req_W,
        'E_BaseVCC_AS_req_W': E_BaseVCC_AS_req_W,
        'E_PeakVCC_AS_req_W': E_PeakVCC_AS_req_W,
        'E_Trigen_NG_gen_W': E_Trigen_NG_gen_W
    }

    thermal_output = {
        # cooling total
        'Q_Trigen_NG_gen_W': Q_Trigen_gen_W,
        'Q_BaseVCC_WS_gen_W': Q_BaseVCC_WS_gen_W,
        'Q_PeakVCC_WS_gen_W': Q_PeakVCC_WS_gen_W,
        'Q_BaseVCC_AS_gen_W': Q_BaseVCC_AS_gen_W,
        'Q_PeakVCC_AS_gen_W': Q_PeakVCC_AS_gen_W,
        'Q_BackupVCC_AS_gen_W': Q_BackupVCC_AS_gen_W,

        # cooling to direct load
        'Q_DailyStorage_gen_directload_W': Q_DailyStorage_gen_directload_W,
        "Q_Trigen_NG_gen_directload_W": Q_Trigen_NG_gen_directload_W,
        "Q_BaseVCC_WS_gen_directload_W": Q_BaseVCC_WS_gen_directload_W,
        "Q_PeakVCC_WS_gen_directload_W": Q_PeakVCC_WS_gen_directload_W,
        "Q_BaseVCC_AS_gen_directload_W": Q_BaseVCC_AS_gen_directload_W,
        "Q_PeakVCC_AS_gen_directload_W": Q_PeakVCC_AS_gen_directload_W,
        "Q_BackupVCC_AS_directload_W": Q_BackupVCC_AS_directload_W,
    }

    gas_output = {
        'NG_Trigen_req_W': NG_Trigen_req_W
    }

    return daily_storage_class, thermal_output, electricity_output, gas_output

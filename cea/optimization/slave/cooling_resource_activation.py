from __future__ import division

import numpy as np

import cea.technologies.chiller_absorption as chiller_absorption
import cea.technologies.chiller_vapor_compression as chiller_vapor_compression
import cea.technologies.cooling_tower as CTModel
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.optimization.constants import ACH_T_IN_FROM_CHP
from cea.optimization.constants import VCC_T_COOL_IN
from cea.technologies.cogeneration import calc_cop_CCGT
from cea.technologies.constants import DT_COOL

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_vcc_operation(Qc_from_VCC_W, T_DCN_re_K, T_DCN_sup_K, T_source_K, lca, hour):
    from cea.technologies.constants import G_VALUE_CENTRALIZED  # this is where to differentiate chiller performances
    VCC_operation = chiller_vapor_compression.calc_VCC(Qc_from_VCC_W, T_DCN_sup_K, T_DCN_re_K, T_source_K,
                                                       G_VALUE_CENTRALIZED)

    # unpack outputs
    Qc_VCC_W = VCC_operation['q_chw_W']
    E_used_VCC_W = VCC_operation['wdot_W']

    # calculate variable costs
    opex_var_VCC_USD = E_used_VCC_W * lca.ELEC_PRICE[hour]

    return opex_var_VCC_USD, Qc_VCC_W, E_used_VCC_W


def calc_vcc_CT_operation(Qc_from_VCC_W, T_DCN_re_K, T_DCN_sup_K, T_source_K, lca, hour):
    from cea.technologies.constants import G_VALUE_CENTRALIZED  # this is where to differentiate chiller performances
    VCC_operation = chiller_vapor_compression.calc_VCC(Qc_from_VCC_W, T_DCN_sup_K, T_DCN_re_K, T_source_K,
                                                       G_VALUE_CENTRALIZED)

    # unpack outputs
    Qc_CT_VCC_W = VCC_operation['q_cw_W']
    Qc_VCC_W = VCC_operation['q_chw_W']

    # calculate cooling tower
    wdot_CT_Wh = CTModel.calc_CT(Qc_CT_VCC_W, Qc_CT_VCC_W)

    # calcualte energy consumption and variable costs
    E_used_VCC_W = (VCC_operation['wdot_W'] + wdot_CT_Wh)
    opex_var_VCC_USD = E_used_VCC_W * lca.ELEC_PRICE[hour]

    return opex_var_VCC_USD, Qc_VCC_W, E_used_VCC_W


def calc_chiller_absorption_operation(Qc_from_ACH_W, T_DCN_re_K, T_DCN_sup_K, T_ground_K, locator):
    ACH_type = 'double'

    if T_DCN_re_K == T_DCN_sup_K:
        mdot_ACH_kgpers = 0
    else:
        mdot_ACH_kgpers = Qc_from_ACH_W / (
                (T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)  # required chw flow rate from ACH

    ACH_operation = chiller_absorption.calc_chiller_main(mdot_ACH_kgpers, T_DCN_sup_K, T_DCN_re_K, ACH_T_IN_FROM_CHP,
                                                         T_ground_K, locator, ACH_type)

    Qc_CT_ACH_W = ACH_operation['q_cw_W']
    Qh_CHP_ACH_W = ACH_operation['q_hw_W']
    E_used_ACH_W = ACH_operation['wdot_W']

    return Qc_CT_ACH_W, Qh_CHP_ACH_W, E_used_ACH_W


def cooling_resource_activator(Q_thermal_req,
                               T_district_cooling_supply_K,
                               T_district_cooling_return_K,
                               Q_therm_Lake_W,
                               T_source_average_Lake_K,
                               daily_storage_class,
                               T_ground_K,
                               lca,
                               master_to_slave_variables,
                               hour,
                               prices,
                               locator):

    ## initializing unmet cooling load and requirements from daily storage for this hour
    Q_cooling_unmet_W = Q_thermal_req
    Q_DailyStorage_gen_W = 0.0

    ## ACTIVATE THE TRIGEN
    if master_to_slave_variables.NG_Trigen_on == 1 and Q_cooling_unmet_W > 0.0:
        size_trigen_W = master_to_slave_variables.NG_Trigen_ACH_size_W
        if Q_cooling_unmet_W > size_trigen_W:
            Qc_Trigen_gen_directload_W = size_trigen_W
            Qc_Trigen_gen_storage_W = 0.0
            Qc_from_storage_W = daily_storage_class.discharge_storage(Q_cooling_unmet_W - size_trigen_W)
            Q_Trigen_gen_W = Qc_Trigen_gen_directload_W + Qc_Trigen_gen_storage_W
        else:
            Qc_Trigen_gen_directload_W = Q_cooling_unmet_W
            Qc_Trigen_gen_storage_W = daily_storage_class.charge_storage(size_trigen_W - Q_cooling_unmet_W)
            Qc_from_storage_W = 0.0
            Q_Trigen_gen_W = Qc_Trigen_gen_directload_W + Qc_Trigen_gen_storage_W

        # GET THE ABSORPTION CHILLER PERFORMANCE
        Qc_CT_ACH_W, \
        Qh_Trigen_req_W, \
        E_ACH_req_W = calc_chiller_absorption_operation(Q_Trigen_gen_W, T_district_cooling_return_K,
                                                        T_district_cooling_supply_K, T_ground_K,
                                                        locator)

        # operation of the CCGT
        CC_op_cost_data = calc_cop_CCGT(master_to_slave_variables.NG_Trigen_CCGT_size_W,
                                        ACH_T_IN_FROM_CHP,
                                        "NG",
                                        prices,
                                        lca.ELEC_PRICE[hour])
        Q_used_prim_CC_fn_W = CC_op_cost_data['q_input_fn_q_output_W']
        cost_per_Wh_CC_fn = CC_op_cost_data['fuel_cost_per_Wh_th_fn_q_output_W']  # gets interpolated cost function
        q_output_CC_min_W = CC_op_cost_data['q_output_min_W']
        Q_output_CC_max_W = CC_op_cost_data['q_output_max_W']
        eta_elec_interpol = CC_op_cost_data['eta_el_fn_q_input']

        # TODO: CONFIRM THAT THIS WORKS AS INTENDED
        if Qh_Trigen_req_W >= q_output_CC_min_W:
            source_Trigen_NG = 1
            # operation Possible if above minimal load
            if Qh_Trigen_req_W <= Q_output_CC_max_W:  # Normal operation Possible within partload regime
                Q_CHP_gen_W = Qh_Trigen_req_W
                cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_CHP_gen_W)
                NG_Trigen_req_W = Q_used_prim_CC_fn_W(Q_CHP_gen_W)
                E_Trigen_NG_gen_W = np.float(eta_elec_interpol(NG_Trigen_req_W)) * NG_Trigen_req_W
                cost_Trigen_USD = cost_per_Wh_CC * Q_CHP_gen_W

            else:  # Only part of the demand can be delivered as 100% load achieved
                Q_CHP_gen_W = Q_output_CC_max_W
                cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_CHP_gen_W)
                NG_Trigen_req_W = Q_used_prim_CC_fn_W(Q_CHP_gen_W)
                E_Trigen_NG_gen_W = np.float(eta_elec_interpol(NG_Trigen_req_W)) * NG_Trigen_req_W
                cost_Trigen_USD = cost_per_Wh_CC * Q_CHP_gen_W
        else:
            source_Trigen_NG = 0
            Q_Trigen_gen_W = 0.0
            NG_Trigen_req_W = 0.0
            cost_Trigen_USD = 0.0
            E_Trigen_NG_gen_W = 0.0

        # update unmet cooling load
        Q_cooling_unmet_W = Q_cooling_unmet_W - Qc_Trigen_gen_directload_W - Qc_from_storage_W
        Q_DailyStorage_gen_W += Qc_from_storage_W
    else:
        source_Trigen_NG = 0
        Q_Trigen_gen_W = 0.0
        NG_Trigen_req_W = 0.0
        cost_Trigen_USD = 0.0
        E_Trigen_NG_gen_W = 0.0

    # Base VCC water-source
    if master_to_slave_variables.WS_BaseVCC_on == 1 and Q_cooling_unmet_W > 0.0:
        # Free cooling possible from the lake
        source_BaseVCC_WS = 1
        if Q_cooling_unmet_W > Q_therm_Lake_W:
            Qc_BaseVCC_WS_gen_directload_W = Q_therm_Lake_W
            Qc_BaseVCC_WS_gen_storage_W = 0.0
            Qc_from_storage_W = daily_storage_class.discharge_storage(Q_cooling_unmet_W - Q_therm_Lake_W)
            Q_BaseVCC_WS_gen_W = Qc_BaseVCC_WS_gen_directload_W + Qc_BaseVCC_WS_gen_storage_W
            Q_therm_Lake_W -= Q_BaseVCC_WS_gen_W  # discount availability
        else:
            Qc_BaseVCC_WS_gen_directload_W = Q_cooling_unmet_W
            Qc_BaseVCC_WS_gen_storage_W = daily_storage_class.charge_storage(Q_therm_Lake_W - Q_cooling_unmet_W)
            Qc_from_storage_W = 0.0
            Q_BaseVCC_WS_gen_W = Qc_BaseVCC_WS_gen_directload_W + Qc_BaseVCC_WS_gen_storage_W
            Q_therm_Lake_W -= Q_BaseVCC_WS_gen_W  # discount availability

        if T_source_average_Lake_K <= T_district_cooling_supply_K - DT_COOL:
            opex_BaseVCC_WS_USDperhr, \
            Q_BaseVCC_WS_gen_W, \
            E_BaseVCC_WS_req_W = calc_vcc_operation(Q_BaseVCC_WS_gen_W,
                                                    T_district_cooling_return_K,
                                                    T_district_cooling_supply_K,
                                                    T_source_average_Lake_K,
                                                    lca,
                                                    hour)
        else:  # bypass, do not use chiller
            opex_BaseVCC_WS_USDperhr = 0.0
            E_BaseVCC_WS_req_W = 0.0

        Q_cooling_unmet_W = Q_cooling_unmet_W - Qc_BaseVCC_WS_gen_directload_W - Qc_from_storage_W
        Q_DailyStorage_gen_W += Qc_from_storage_W
    else:
        source_BaseVCC_WS = 0
        opex_BaseVCC_WS_USDperhr = 0.0
        Q_BaseVCC_WS_gen_W = 0.0
        E_BaseVCC_WS_req_W = 0.0

    # Peak VCC water-source
    if master_to_slave_variables.WS_PeakVCC_on == 1 and Q_cooling_unmet_W > 0.0:
        # Free cooling possible from the lake
        source_PeakVCC_WS = 1
        if Q_cooling_unmet_W > Q_therm_Lake_W:
            Qc_PeakVCC_WS_gen_directload_W = Q_therm_Lake_W
            Qc_PeakVCC_WS_gen_storage_W = 0.0
            Qc_from_storage_W = daily_storage_class.discharge_storage(Q_cooling_unmet_W - Q_therm_Lake_W)
            Q_PeakVCC_WS_gen_W = Qc_PeakVCC_WS_gen_directload_W + Qc_PeakVCC_WS_gen_storage_W
            Q_therm_Lake_W -= Q_PeakVCC_WS_gen_W  # discount availability
        else:
            Qc_PeakVCC_WS_gen_directload_W = Q_cooling_unmet_W
            Qc_PeakVCC_WS_gen_storage_W = daily_storage_class.charge_storage(Q_therm_Lake_W - Q_cooling_unmet_W)
            Qc_from_storage_W = 0.0
            Q_PeakVCC_WS_gen_W = Qc_PeakVCC_WS_gen_directload_W + Qc_PeakVCC_WS_gen_storage_W
            Q_therm_Lake_W -= Q_PeakVCC_WS_gen_W  # discount availability

        if T_source_average_Lake_K <= T_district_cooling_supply_K - DT_COOL:
            opex_PeakVCC_WS_USDperhr, \
            Q_PeakVCC_WS_gen_W, \
            E_PeakVCC_WS_req_W = calc_vcc_operation(Q_PeakVCC_WS_gen_W,
                                                    T_district_cooling_return_K,
                                                    T_district_cooling_supply_K,
                                                    T_source_average_Lake_K,
                                                    lca,
                                                    hour)
        else:  # bypass, do not use chiller
            opex_PeakVCC_WS_USDperhr = 0.0
            E_PeakVCC_WS_req_W = 0.0

        Q_cooling_unmet_W = Q_cooling_unmet_W - Qc_PeakVCC_WS_gen_directload_W - Qc_from_storage_W
        Q_DailyStorage_gen_W += Qc_from_storage_W
    else:
        source_PeakVCC_WS = 0
        opex_PeakVCC_WS_USDperhr = 0.0
        Q_PeakVCC_WS_gen_W = 0.0
        E_PeakVCC_WS_req_W = 0.0

    # Base VCC air-source with a cooling tower
    if master_to_slave_variables.AS_BaseVCC_on == 1 and Q_cooling_unmet_W > 0.0:
        source_BaseVCC_AS = 1
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

        opex_BaseVCC_AS_USDperhr, \
        Q_BaseVCC_AS_gen_W, \
        E_BaseVCC_AS_req_W = calc_vcc_CT_operation(Q_BaseVCC_AS_gen_W,
                                                   T_district_cooling_return_K,
                                                   T_district_cooling_supply_K,
                                                   VCC_T_COOL_IN,
                                                   lca)

        Q_cooling_unmet_W = Q_cooling_unmet_W - Q_BaseVCC_AS_gen_directload_W - Qc_from_storage_W
        Q_DailyStorage_gen_W += Qc_from_storage_W
    else:
        source_BaseVCC_AS = 0
        opex_BaseVCC_AS_USDperhr = 0.0
        Q_BaseVCC_AS_gen_W = 0.0
        E_BaseVCC_AS_req_W = 0.0

    # Peak VCC air-source with a cooling tower
    if master_to_slave_variables.AS_PeakVCC_on == 1 and Q_cooling_unmet_W > 0.0:
        size_AS_PeakVCC_W = master_to_slave_variables.AS_PeakVCC_size_W
        source_PeakVCC_AS = 1
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

        opex_PeakVCC_AS_USDperhr, \
        Q_PeakVCC_AS_gen_W, \
        E_PeakVCC_AS_req_W = calc_vcc_CT_operation(Q_PeakVCC_AS_gen_W,
                                                   T_district_cooling_return_K,
                                                   T_district_cooling_supply_K,
                                                   VCC_T_COOL_IN,
                                                   lca)

        Q_cooling_unmet_W = Q_cooling_unmet_W - Q_PeakVCC_AS_gen_directload_W - Qc_from_storage_W
        Q_DailyStorage_gen_W += Qc_from_storage_W
    else:
        source_PeakVCC_AS = 0
        opex_PeakVCC_AS_USDperhr = 0.0
        Q_PeakVCC_AS_gen_W = 0.0
        E_PeakVCC_AS_req_W = 0.0

    if Q_cooling_unmet_W > 1.0E-3:
        Q_BackupVCC_AS_gen_W = Q_cooling_unmet_W  # this will become the back-up boiler
    else:
        Q_BackupVCC_AS_gen_W = 0.0

    ## writing outputs

    electricity_output = {
        'E_BaseVCC_WS_req_W': E_BaseVCC_WS_req_W,
        'E_PeakVCC_WS_req_W': E_PeakVCC_WS_req_W,
        'E_BaseVCC_AS_req_W': E_BaseVCC_AS_req_W,
        'E_PeakVCC_AS_req_W': E_PeakVCC_AS_req_W,
        'E_Trigen_NG_gen_W' : E_Trigen_NG_gen_W
    }

    thermal_output = {
        'Q_Trigen_gen_W': Q_Trigen_gen_W,
        'Q_BaseVCC_WS_gen_W': Q_BaseVCC_WS_gen_W,
        'Q_PeakVCC_WS_gen_W': Q_PeakVCC_WS_gen_W,
        'Q_BaseVCC_AS_gen_W': Q_BaseVCC_AS_gen_W,
        'Q_PeakVCC_AS_gen_W': Q_PeakVCC_AS_gen_W,
        'Q_BackupVCC_AS_gen_W': Q_BackupVCC_AS_gen_W,
        'Q_DailyStorage_WS_gen_W': Q_DailyStorage_gen_W,
    }

    activation_output = {
        "source_Trigen_NG": source_Trigen_NG,
        "source_BaseVCC_WS": source_BaseVCC_WS,
        "source_PeakVCC_WS": source_PeakVCC_WS,
        "source_BaseVCC_AS": source_BaseVCC_AS,
        'source_PeakVCC_AS': source_PeakVCC_AS,

    }

    gas_output = {'NG_Trigen_req_W': NG_Trigen_req_W}

    return daily_storage_class, activation_output, thermal_output, electricity_output, gas_output

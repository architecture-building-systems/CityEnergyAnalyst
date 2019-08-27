from __future__ import division

import numpy as np

import cea.technologies.chiller_absorption as chiller_absorption
import cea.technologies.chiller_vapor_compression as chiller_vapor_compression
import cea.technologies.cooling_tower as CTModel
import cea.technologies.storage_tank as storage_tank
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK, P_WATER_KGPERM3, J_TO_WH, WH_TO_J
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
    wdot_CT_Wh = CTModel.calc_CT(Qc_CT_VCC_W, Q_CT_nom_W)

    # calcualte energy consumption and variable costs
    E_used_VCC_W = (VCC_operation['wdot_W'] + wdot_CT_Wh)
    opex_var_VCC_USD = E_used_VCC_W * lca.ELEC_PRICE[hour]

    return opex_var_VCC_USD, Qc_VCC_W, E_used_VCC_W


def calc_vcc_backup_operation(Qc_from_VCC_backup_W, T_DCN_re_K, T_DCN_sup_K, T_source_K, lca, hour):
    from cea.technologies.constants import G_VALUE_CENTRALIZED  # this is where to differentiate chiller performances
    mdot_VCC_kgpers = Qc_from_VCC_backup_W / ((T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)
    VCC_operation = chiller_vapor_compression.calc_VCC(Qc_from_VCC_backup_W, T_DCN_sup_K, T_DCN_re_K, T_source_K,
                                                       G_VALUE_CENTRALIZED)
    # unpack outputs
    opex_var_VCC_backup_USD = VCC_operation['wdot_W'] * lca.ELEC_PRICE[hour]
    GHG_VCC_backup_tonCO2perhr = (VCC_operation['wdot_W'] * WH_TO_J / 1E6) * lca.EL_TO_CO2 / 1E3
    prim_energy_VCC_backup_MJoilperhr = (VCC_operation['wdot_W'] * WH_TO_J / 1E6) * lca.EL_TO_OIL_EQ
    Qc_CT_VCC_backup_W = VCC_operation['q_cw_W']
    E_used_VCC_backup_W = opex_var_VCC_backup_USD / lca.ELEC_PRICE[hour]
    return opex_var_VCC_backup_USD, GHG_VCC_backup_tonCO2perhr, prim_energy_VCC_backup_MJoilperhr, Qc_CT_VCC_backup_W, E_used_VCC_backup_W


def calc_chiller_absorption_operation(Qc_from_ACH_W, T_DCN_re_K, T_DCN_sup_K, T_ground_K, locator,
                                      min_chiller_size_W, max_chiller_size_W):
    ACH_type = 'double'

    if T_DCN_re_K == T_DCN_sup_K:
        mdot_ACH_kgpers = 0
    else:
        mdot_ACH_kgpers = Qc_from_ACH_W / (
                (T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)  # required chw flow rate from ACH

    ACH_operation = chiller_absorption.calc_chiller_main(mdot_ACH_kgpers,
                                                         T_DCN_sup_K,
                                                         T_DCN_re_K,
                                                         ACH_T_IN_FROM_CHP,
                                                         T_ground_K,
                                                         locator,
                                                         ACH_type,
                                                         min_chiller_size_W,
                                                         max_chiller_size_W)

    Qc_CT_ACH_W = ACH_operation['q_cw_W']
    Qh_CHP_ACH_W = ACH_operation['q_hw_W']
    E_used_ACH_W = ACH_operation['wdot_W']

    return Qc_CT_ACH_W, Qh_CHP_ACH_W, E_used_ACH_W


def cooling_resource_activator(Q_thermal_req,
                               mdot_DCN_kgpers,
                               T_district_cooling_supply_K,
                               T_district_cooling_return_K,
                               Q_therm_Lake_W,
                               T_source_average_Lake_K,
                               storage_tank_properties_previous_timestep,
                               T_ground_K,
                               lca,
                               master_to_slave_variables,
                               hour,
                               prices,
                               locator):
    # UNPACK VARIABLES OF TANK FOR LAST TIMESTEP
    V_tank_m3 = storage_tank_properties_previous_timestep['V_tank_m3']
    T_tank_C = storage_tank_properties_previous_timestep['T_tank_K'] - 273.0
    Qc_tank_charging_limit_W = storage_tank_properties_previous_timestep['Qc_tank_charging_limit_W']
    T_tank_fully_charged_C = storage_tank_properties_previous_timestep['T_tank_fully_charged_K'] - 273.0
    T_tank_fully_discharged_C = storage_tank_properties_previous_timestep['T_tank_fully_discharged_K'] - 273.0
    T_ground_C = T_ground_K - 273.0

    ## initializing unmet cooling load
    Q_cooling_unmet_W = Q_thermal_req

    ## ACTIVATE THE TRIGEN
    if master_to_slave_variables.NG_Trigen_on == 1 and Q_cooling_unmet_W > 0.0:
        if Q_cooling_unmet_W <= master_to_slave_variables.NG_Trigen_size:
            Qc_Trigen_gen_W = Q_cooling_unmet_W
        else:
            Qc_Trigen_gen_W = master_to_slave_variables.NG_Trigen_size

        # GET THE ABSORPTION CHILLER PERFORMANCE
        Qc_CT_ACH_W, \
        Qh_Trigen_req_W, \
        E_ACH_req_W = calc_chiller_absorption_operation(Qc_Trigen_gen_W, T_district_cooling_return_K,
                                                        T_district_cooling_supply_K, T_ground_K,
                                                        locator, min_ACH_unit_size_W, max_ACH_unit_size_W)

        # operation of the CCGT
        CC_op_cost_data = calc_cop_CCGT(master_to_slave_variables.NG_Trigen_size,
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
                E_Trigen_NG_req_W = np.float(eta_elec_interpol(NG_Trigen_req_W)) * NG_Trigen_req_W
                cost_Trigen_USD = cost_per_Wh_CC * Q_CHP_gen_W

            else:  # Only part of the demand can be delivered as 100% load achieved
                Q_CHP_gen_W = Q_output_CC_max_W
                cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_CHP_gen_W)
                NG_Trigen_req_W = Q_used_prim_CC_fn_W(Q_CHP_gen_W)
                E_Trigen_NG_req_W = np.float(eta_elec_interpol(Q_output_CC_max_W)) * NG_Trigen_req_W
                cost_Trigen_USD = cost_per_Wh_CC * Q_CHP_gen_W
        else:
            source_Trigen_NG = 0
            Qc_Trigen_gen_W = 0.0
            NG_Trigen_req_W = 0.0
            E_Trigen_NG_req_W = 0.0
            cost_Trigen_USD = 0.0

        # update unmet cooling load
        Q_cooling_unmet_W = Q_cooling_unmet_W - Qc_Trigen_gen_W

    else:
        source_Trigen_NG = 0
        Qc_Trigen_gen_W = 0.0
        NG_Trigen_req_W = 0.0
        E_Trigen_NG_req_W = 0.0
        cost_Trigen_USD = 0.0

    # Base VCC water-source
    if master_to_slave_variables.WS_BaseVCC_on == 1 and Q_cooling_unmet_W > 0.0:
        # Free cooling possible from the lake
        source_BaseVCC_WS = 1
        if Q_cooling_unmet_W > Q_therm_Lake_W:
            Q_BaseVCC_WS_gen_W = Q_therm_Lake_W
            Q_therm_Lake_W = - Q_therm_Lake_W  # discount availability
        else:
            Q_BaseVCC_WS_gen_W = Q_cooling_unmet_W

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

        Q_cooling_unmet_W = Q_cooling_unmet_W - Q_BaseVCC_WS_gen_W
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
            Q_PeakVCC_WS_gen_W = Q_therm_Lake_W
        else:
            Q_PeakVCC_WS_gen_W = Q_cooling_unmet_W

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

        Q_cooling_unmet_W = Q_cooling_unmet_W - Q_PeakVCC_WS_gen_W
    else:
        source_PeakVCC_WS = 0
        opex_PeakVCC_WS_USDperhr = 0.0
        Q_PeakVCC_WS_gen_W = 0.0
        E_PeakVCC_WS_req_W = 0.0

    # Base VCC air-source with a cooling tower
    if master_to_slave_variables.AS_BaseVCC_on == 1 and Q_cooling_unmet_W > 0.0:
        source_BaseVCC_AS = 1
        if Q_cooling_unmet_W > master_to_slave_variables.AS_BaseVCC_size_W:
            Q_BaseVCC_AS_gen_W = master_to_slave_variables.AS_BaseVCC_size_W
        else:
            Q_BaseVCC_AS_gen_W = Q_cooling_unmet_W

        opex_BaseVCC_AS_USDperhr, \
        Q_BaseVCC_AS_gen_W, \
        E_BaseVCC_AS_req_W = calc_vcc_CT_operation(Q_BaseVCC_AS_gen_W,
                                                   T_district_cooling_return_K,
                                                   T_district_cooling_supply_K,
                                                   VCC_T_COOL_IN,
                                                   lca)
    else:
        source_BaseVCC_AS = 0
        opex_BaseVCC_AS_USDperhr = 0.0
        Q_BaseVCC_AS_gen_W = 0.0
        E_BaseVCC_AS_req_W = 0.0

    # Peak VCC air-source with a cooling tower
    if master_to_slave_variables.AS_PeakVCC_on == 1 and Q_cooling_unmet_W > 0.0:
        source_PeakVCC_AS = 1
        if Q_cooling_unmet_W > master_to_slave_variables.AS_PeakVCC_size_W:
            Q_PeakVCC_AS_gen_W = master_to_slave_variables.AS_PeakVCC_size_W
        else:
            Q_PeakVCC_AS_gen_W = Q_cooling_unmet_W

        opex_PeakVCC_AS_USDperhr, \
        Q_PeakVCC_AS_gen_W, \
        E_PeakVCC_AS_req_W = calc_vcc_CT_operation(Q_PeakVCC_AS_gen_W,
                                                   T_district_cooling_return_K,
                                                   T_district_cooling_supply_K,
                                                   VCC_T_COOL_IN,
                                                   lca)
    else:
        source_PeakVCC_AS = 0
        opex_PeakVCC_AS_USDperhr = 0.0
        Q_PeakVCC_AS_gen_W = 0.0
        E_PeakVCC_AS_req_W = 0.0

    ## activate cold thermal storage (fully mixed water tank)
    if V_tank_m3 > 0:
        Tank_discharging_limit_C = T_district_cooling_supply_K - DT_COOL - 273.0  # Temperature required to cool the network at that timestep
        # Tank_charging_limit_C = T_tank_fully_charged_C + DT_CHARGING_BUFFER # todo: redundant

        # Discharge when T_tank_C is low enough to cool the network
        if Q_cooling_unmet_W > 0.0 and T_tank_C < Tank_discharging_limit_C:
            # Calculate the maximum Qc available to fully discharge the tank
            Qc_tank_discharging_limit_W = V_tank_m3 * P_WATER_KGPERM3 * HEAT_CAPACITY_OF_WATER_JPERKGK * (
                    T_tank_fully_discharged_C - T_tank_C) * J_TO_WH
            if Q_cooling_unmet_W < Qc_tank_discharging_limit_W:
                # Supply all Q_cooling_unmet_W
                Qc_from_Tank_W = Q_cooling_unmet_W
            else:
                # Supply Qc to the tank limit
                Qc_from_Tank_W = Qc_tank_discharging_limit_W
            Qc_to_tank_W = 0
            T_tank_C = storage_tank.calc_fully_mixed_tank(T_tank_C, T_ground_C, Qc_from_Tank_W, Qc_to_tank_W,
                                                          V_tank_m3, 'cold_water')
            # print ('discharging', T_tank_C)
            # update unmet cooling load
            Q_cooling_unmet_W = Q_cooling_unmet_W - Qc_from_Tank_W

        # Charging when T_tank_C is high and the tank is not discharging
        # FIXME: (Q_cooling_unmet_W <= 0.0) should be removed, because charging is possible when the tank is not discharging
        elif Q_cooling_unmet_W <= 0.0 and T_tank_C > T_tank_fully_charged_C:  # no-load, charge the storage
            # calculate the maximum Qc required to fully charge the tank
            Qc_to_tank_max_Wh = V_tank_m3 * P_WATER_KGPERM3 * HEAT_CAPACITY_OF_WATER_JPERKGK * (
                    T_tank_C - T_tank_fully_charged_C) * J_TO_WH  # available to charge
            # calculate the actual charging level
            Qc_to_tank_W = Qc_tank_charging_limit_W if Qc_to_tank_max_Wh > Qc_tank_charging_limit_W else Qc_to_tank_max_Wh
            Qc_from_Tank_W = 0
            T_tank_C = storage_tank.calc_fully_mixed_tank(T_tank_C, T_ground_C, Qc_from_Tank_W, Qc_to_tank_W,
                                                          V_tank_m3, 'cold_water')
            # print ('charging', T_tank_C)

        else:  # no charging/discharging
            Qc_from_Tank_W = 0
            Qc_to_tank_W = 0
            T_tank_C = storage_tank.calc_fully_mixed_tank(T_tank_C, T_ground_C, Qc_from_Tank_W, Qc_to_tank_W,
                                                          V_tank_m3, 'cold_water')
            # print ('no action', T_tank_C)
            # TODO: [NOTE] Qc_to_tank_W is being supplied in line 290, another way is to add it directly to Q_cooling_unmet_W

    if Q_cooling_unmet_W > 0 and master_to_slave_variables.VCC_on == 1:

        Source_Vapor_compression_chiller = 1

        # activate VCC
        if Q_cooling_unmet_W <= technology_capacities['Qc_VCC_nom_W']:
            Qc_from_VCC_W = Q_cooling_unmet_W
        else:
            Qc_from_VCC_W = technology_capacities['Qc_VCC_nom_W']

        opex_var_VCC_USDperhr, \
        Qc_CT_VCC_W, \
        E_used_VCC_W = calc_vcc_operation(Qc_from_VCC_W, T_DCN_re_K, T_DCN_sup_K, VCC_T_COOL_IN, lca, hour)

        # update unmet cooling load
        Q_cooling_unmet_W = Q_cooling_unmet_W - Qc_from_VCC_W

    if Q_cooling_unmet_W > 0:
        Source_back_up_Vapor_compression_chiller = 1

        # activate back-up VCC
        Qc_from_backup_VCC_W = Q_cooling_unmet_W
        opex_var_VCC_backup_USDperhr, GHG_VCC_backup_tonCO2perhr, \
        prim_energy_VCC_backup_MJoilperhr, Qc_CT_VCC_backup_W, \
        E_used_VCC_backup_W = calc_vcc_backup_operation(Qc_from_backup_VCC_W, T_DCN_re_K, T_DCN_sup_K, VCC_T_COOL_IN,
                                                        lca, hour)
        # update unmet cooling load
        Q_cooling_unmet_W = Q_cooling_unmet_W - Qc_from_backup_VCC_W

    if Q_cooling_unmet_W != 0:
        raise ValueError(
            'The cooling load is not met! Fix that calculation!')

    ## activate chillers to charge the thermal storage in order: VCC -> ACH -> VCC_backup
    if Qc_to_tank_W > 0:
        T_chiller_in_K = T_tank_C + 273.0  # temperature of a fully mixed tank
        T_chiller_out_K = (T_tank_fully_charged_C + 273.0) - DT_COOL

        if master_to_slave_variables.VCC_on == 1 and Qc_to_tank_W > 0.0:  # activate VCC to charge the tank
            if Qc_to_tank_W <= technology_capacities['Qc_VCC_nom_W']:
                Qc_from_VCC_to_tank_W = Qc_to_tank_W
            else:
                Qc_from_VCC_to_tank_W = technology_capacities['Qc_VCC_nom_W']

            opex_var_VCC_USDperhr, \
            GHG_VCC_tonCO2perhr, \
            prim_energy_VCC_MJoilperhr, \
            Qc_CT_VCC_W, \
            E_used_VCC_W = calc_vcc_operation(Qc_from_VCC_to_tank_W, T_chiller_in_K, T_chiller_out_K, VCC_T_COOL_IN,
                                              lca, hour)

            opex_var_VCC_USD.append(opex_var_VCC_USDperhr)
            GHG_VCC_tonCO2.append(GHG_VCC_tonCO2perhr)
            prim_energy_VCC_MJoil.append(prim_energy_VCC_MJoilperhr)
            Qc_CT_W.append(Qc_CT_VCC_W)
            Qc_to_tank_W -= Qc_from_VCC_to_tank_W

        if master_to_slave_variables.Absorption_Chiller_on == 1 and Qc_to_tank_W > 0.0:  # activate ACH to charge the tank
            if Qc_to_tank_W <= technology_capacities['Qc_ACH_nom_W']:
                Qc_from_ACH_to_tank_W = Qc_to_tank_W
            else:
                Qc_from_ACH_to_tank_W = technology_capacities['Qc_ACH_nom_W']
            opex_var_ACH_USDperhr, \
            GHG_ACH_tonCO2perhr, \
            prim_energy_MJoilperhr, \
            Qc_CT_ACH_W, \
            Qh_Trigen_gen_W, \
            E_ACH_req_W = calc_chiller_absorption_operation(Qc_from_ACH_to_tank_W, T_DCN_re_K, T_DCN_sup_K,
                                                            T_ground_K, lca, locator, hour, min_ACH_unit_size_W,
                                                            max_ACH_unit_size_W)
            opex_var_ACH_USD.append(opex_var_ACH_USDperhr)
            GHG_ACH_tonCO2.append(GHG_ACH_tonCO2perhr)
            prim_energy_ACH_MJoil.append(prim_energy_MJoilperhr)
            Qc_CT_W.append(Qc_CT_ACH_W)
            Qh_CHP_W.append(Qh_Trigen_gen_W)
            Qc_to_tank_W -= Qc_from_ACH_to_tank_W

        if Qc_to_tank_W > 0:
            raise ValueError(
                'There are no vapor compression chiller nor absorption chiller installed to charge the storage!')

    ## writing outputs

    storage_tank_properties_this_timestep = {
        "V_tank_m3": V_tank_m3,
        "T_tank_K": T_tank_C + 273.0,
        "Qc_tank_charging_limit_W": xxxx,
        "T_tank_fully_charged_K": vvvvv,
        "T_tank_fully_discharged_K": cccc,
    }

    opex_output = {
        'opex_var_Trigen_NG_USDhr': cost_Trigen_USD,
        'opex_var_BaseVCC_WS_USDperhr': opex_BaseVCC_WS_USDperhr,
        'opex_var_PeakVCC_WS_USDperhr': opex_PeakVCC_WS_USDperhr,
        'opex_var_BaseVCC_AS_USDperhr': opex_BaseVCC_AS_USDperhr,
        'opex_var_PeakVCC_AS_USDperhr': opex_PeakVCC_AS_USDperhr,
    }

    electricity_output = {
        'E_Trigen_NG_req_W': E_Trigen_NG_req_W,
        'E_BaseVCC_WS_req_W': E_BaseVCC_WS_req_W,
        'E_PeakVCC_WS_req_W': E_PeakVCC_WS_req_W,
        'E_BaseVCC_AS_req_W': E_BaseVCC_AS_req_W,
        'E_PeakVCC_AS_req_W': E_PeakVCC_AS_req_W
    }

    thermal_output = {
        'Qc_Trigen_gen_W': Qc_Trigen_gen_W,
        'Q_BaseVCC_WS_gen_W': Q_BaseVCC_WS_gen_W,
        'Q_PeakVCC_WS_gen_W': Q_PeakVCC_WS_gen_W,
        'Q_BaseVCC_AS_gen_W': Q_BaseVCC_AS_gen_W,
        'Q_PeakVCC_AS_gen_W': Q_PeakVCC_AS_gen_W,
        'Qc_from_Tank_W': Qc_from_Tank_W,

    }

    activation_output = {
        "source_Trigen_NG": source_Trigen_NG,
        "source_BaseVCC_WS": source_BaseVCC_WS,
        "source_PeakVCC_WS": source_PeakVCC_WS,
        "source_BaseVCC_AS": source_BaseVCC_AS,
        'source_PeakVCC_AS': source_PeakVCC_AS,

    }

    gas_output = {'NG_Trigen_req_W': NG_Trigen_req_W}

    return storage_tank_properties_this_timestep, opex_output, activation_output, thermal_output, electricity_output, gas_output

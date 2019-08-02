from __future__ import division

import numpy as np

import cea.config
import cea.globalvar
import cea.inputlocator
import cea.technologies.chiller_absorption as chiller_absorption
import cea.technologies.chiller_vapor_compression as chiller_vapor_compression
import cea.technologies.storage_tank as storage_tank
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK, P_WATER_KGPERM3, J_TO_WH, WH_TO_J
from cea.optimization.constants import DELTA_P_COEFF, DELTA_P_ORIGIN, PUMP_ETA, ACH_T_IN_FROM_CHP, DT_CHARGING_BUFFER
from cea.technologies.constants import DT_COOL

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_vcc_operation(Qc_from_VCC_W, T_DCN_re_K, T_DCN_sup_K, lca, limits, hour):
    mdot_VCC_kgpers = Qc_from_VCC_W / ((T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)
    VCC_operation = chiller_vapor_compression.calc_VCC(mdot_VCC_kgpers, T_DCN_sup_K, T_DCN_re_K, limits['Qnom_VCC_W'],
                                                       limits['number_of_VCC_chillers'])
    # unpack outputs
    opex_var_VCC_USD = VCC_operation['wdot_W'] * lca.ELEC_PRICE[hour]
    GHG_VCC_tonCO2perhr = (VCC_operation['wdot_W'] * WH_TO_J / 1E6) * lca.EL_TO_CO2 / 1E3
    prim_energy_VCC_MJoilperhr = (VCC_operation['wdot_W'] * WH_TO_J / 1E6) * lca.EL_TO_OIL_EQ
    Qc_CT_VCC_W = VCC_operation['q_cw_W']
    E_used_VCC_W = opex_var_VCC_USD / lca.ELEC_PRICE[hour]
    return opex_var_VCC_USD, GHG_VCC_tonCO2perhr, prim_energy_VCC_MJoilperhr, Qc_CT_VCC_W, E_used_VCC_W


def calc_vcc_backup_operation(Qc_from_VCC_backup_W, T_DCN_re_K, T_DCN_sup_K, prices, lca, limits, hour):
    mdot_VCC_kgpers = Qc_from_VCC_backup_W / ((T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)
    VCC_operation = chiller_vapor_compression.calc_VCC(mdot_VCC_kgpers, T_DCN_sup_K, T_DCN_re_K,
                                                       limits['Qnom_VCC_backup_W'],
                                                       limits['number_of_VCC_backup_chillers'])
    # unpack outputs
    opex_var_VCC_backup_USD = VCC_operation['wdot_W'] * lca.ELEC_PRICE[hour]
    GHG_VCC_backup_tonCO2perhr = (VCC_operation['wdot_W'] * WH_TO_J / 1E6) * lca.EL_TO_CO2 / 1E3
    prim_energy_VCC_backup_MJoilperhr = (VCC_operation['wdot_W'] * WH_TO_J / 1E6) * lca.EL_TO_OIL_EQ
    Qc_CT_VCC_backup_W = VCC_operation['q_cw_W']
    E_used_VCC_backup_W = opex_var_VCC_backup_USD / lca.ELEC_PRICE[hour]
    return opex_var_VCC_backup_USD, GHG_VCC_backup_tonCO2perhr, prim_energy_VCC_backup_MJoilperhr, Qc_CT_VCC_backup_W, E_used_VCC_backup_W


def calc_chiller_absorption_operation(Qc_from_ACH_W, T_DCN_re_K, T_DCN_sup_K, T_ground_K, prices, lca, config, limits,
                                      hour):
    ACH_type = 'double'
    opex_var_ACH_USD = 0
    GHG_ACH_tonCO2perhr = 0
    prim_energy_ACH_MJoilperhr = 0
    Qc_CT_ACH_W = 0
    Qh_CHP_ACH_W = 0
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)  # TODO: move out

    if Qc_from_ACH_W < limits['Qnom_ACH_W']:  # activate one unit of ACH
        # calculate ACH operation
        if T_DCN_re_K == T_DCN_sup_K:
            mdot_ACH_kgpers = 0
        else:
            mdot_ACH_kgpers = Qc_from_ACH_W / (
                    (T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)  # required chw flow rate from ACH
        ACH_operation = chiller_absorption.calc_chiller_main(mdot_ACH_kgpers, T_DCN_sup_K, T_DCN_re_K,
                                                             ACH_T_IN_FROM_CHP, T_ground_K, ACH_type,
                                                             locator, config)
        opex_var_ACH_USD = (ACH_operation['wdot_W']) * lca.ELEC_PRICE[hour]
        GHG_ACH_tonCO2perhr = (ACH_operation['wdot_W'] * WH_TO_J / 1E6) * (lca.EL_TO_CO2 / 1E3)
        prim_energy_ACH_MJoilperhr = (ACH_operation['wdot_W'] * WH_TO_J / 1E6) * lca.EL_TO_OIL_EQ
        Qc_CT_ACH_W = ACH_operation['q_cw_W']
        Qh_CHP_ACH_W = ACH_operation['q_hw_W']
    else:  # more than one unit of ACH are activated
        number_of_chillers = limits['number_of_ACH_chillers']
        if T_DCN_re_K == T_DCN_sup_K:
            mdot_ACH_kgpers = 0
        else:
            mdot_ACH_kgpers = Qc_from_ACH_W / (
                    (T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)  # required chw flow rate from ACH
        mdot_ACH_kgpers_per_chiller = mdot_ACH_kgpers / number_of_chillers
        for i in range(number_of_chillers):
            ACH_operation = chiller_absorption.calc_chiller_main(mdot_ACH_kgpers_per_chiller, T_DCN_sup_K, T_DCN_re_K,
                                                                 ACH_T_IN_FROM_CHP, T_ground_K, ACH_type, locator,
                                                                 config)
            if type(ACH_operation['wdot_W']) is int:
                opex_var_ACH_USD = opex_var_ACH_USD + (ACH_operation['wdot_W'] * lca.ELEC_PRICE[hour])
                GHG_ACH_tonCO2perhr = GHG_ACH_tonCO2perhr + (ACH_operation['wdot_W'] * WH_TO_J / 1E6 * lca.EL_TO_CO2 / 1E3)
                prim_energy_ACH_MJoilperhr = prim_energy_ACH_MJoilperhr + (ACH_operation['wdot_W'] * WH_TO_J / 1E6 * lca.EL_TO_OIL_EQ)
                Qc_CT_ACH_W = Qc_CT_ACH_W + ACH_operation['q_cw_W']
                Qh_CHP_ACH_W = Qh_CHP_ACH_W + ACH_operation['q_hw_W']
            else:
                opex_var_ACH_USD = opex_var_ACH_USD + (ACH_operation['wdot_W'] * lca.ELEC_PRICE[hour])
                GHG_ACH_tonCO2perhr = GHG_ACH_tonCO2perhr + (ACH_operation['wdot_W'] * WH_TO_J / 1E6 * lca.EL_TO_CO2 / 1E3)
                prim_energy_ACH_MJoilperhr = prim_energy_ACH_MJoilperhr + (ACH_operation['wdot_W'] * WH_TO_J / 1E6 * lca.EL_TO_OIL_EQ)
                Qc_CT_ACH_W = Qc_CT_ACH_W + ACH_operation['q_cw_W']
                Qh_CHP_ACH_W = Qh_CHP_ACH_W + ACH_operation['q_hw_W']

    E_used_ACH_W = opex_var_ACH_USD / lca.ELEC_PRICE[hour]

    return opex_var_ACH_USD, GHG_ACH_tonCO2perhr, prim_energy_ACH_MJoilperhr, Qc_CT_ACH_W, Qh_CHP_ACH_W, E_used_ACH_W


def cooling_resource_activator(mdot_kgpers, T_sup_K, T_re_K, limits, cooling_resource_potentials, T_ground_K, prices,
                               lca, master_to_slave_variables, config, Q_cooling_req, hour):
    """

    :param DCN_cooling:
    :param Qc_available_from_lake_W:
    :type Qc_available_from_lake_W: float
    :param Qc_from_lake_cumulative_W:
    :type Qc_from_lake_cumulative_W: float
    :param prices:
    :return:
    """

    # unpack variables
    T_tank_C = cooling_resource_potentials['T_tank_K'] - 273.0
    Qc_available_from_lake_W = cooling_resource_potentials['Qc_avail_from_lake_W']
    Qc_from_lake_cumulative_W = cooling_resource_potentials['Qc_from_lake_cumulative_W']

    # unpack variables
    V_tank_m3 = limits['V_tank_m3']
    Qc_tank_discharge_peak_W = limits['Qc_tank_discharge_peak_W']
    Qc_tank_charge_max_W = limits['Qc_tank_charge_max_W']
    T_tank_fully_charged_C = limits['T_tank_fully_charged_K'] - 273.0
    T_ground_C = T_ground_K - 273.0

    T_DCN_sup_K = T_sup_K
    T_DCN_re_K = T_re_K
    mdot_DCN_kgpers = mdot_kgpers

    opex_var_Lake_USD = 0
    GHG_output_Lake_tonCO2 = 0
    prim_output_Lake_MJoil = 0

    opex_var_VCC_USD = []
    GHG_VCC_tonCO2 = []
    prim_energy_VCC_MJoil = []

    opex_var_VCC_backup_USD = []
    GHG_VCC_backup_tonCO2 = []
    prim_energy_VCC_backup_MJoil = []

    opex_var_ACH_USD = []
    GHG_ACH_tonCO2 = []
    prim_energy_ACH_MJoil = []

    calfactor_output = 0

    Qc_from_Lake_W = 0
    Qc_from_VCC_W = 0
    Qc_from_ACH_W = 0
    Qc_from_Tank_W = 0
    Qc_from_backup_VCC_W = 0
    Qc_from_VCC_to_tank_W = 0
    Qc_to_tank_W = 0

    Qh_CHP_W = []
    Qc_CT_W = []

    E_used_VCC_W = []
    E_used_VCC_backup_W = []
    E_used_ACH_W = []
    E_used_Lake_W = []

    Source_Lake = 0
    Source_Absorption_Chiller = 0
    Source_Vapor_compression_chiller = 0
    Source_back_up_Vapor_compression_chiller = 0

    ## initializing unmet cooling load
    Qc_load_unmet_W = Q_cooling_req

    # LAKE COOLING (FREE COOLING)
    if Qc_load_unmet_W <= ( Qc_available_from_lake_W - Qc_from_lake_cumulative_W) and Qc_load_unmet_W > 0.0:
        # Free cooling possible from the lake

        Source_Lake = 1

        Qc_from_Lake_W = Qc_load_unmet_W
        Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_Lake_W
        Qc_from_lake_cumulative_W = Qc_from_lake_cumulative_W + Qc_from_Lake_W

        # Delta P from linearization after distribution optimization
        deltaP_Pa = 2 * (DELTA_P_COEFF * mdot_DCN_kgpers + DELTA_P_ORIGIN)
        Pump_electricity_W = deltaP_Pa * (mdot_DCN_kgpers / P_WATER_KGPERM3) / PUMP_ETA
        opex_var_Lake_USD = Pump_electricity_W * lca.ELEC_PRICE[hour]  # ELEC_PRICE is in USD/W

        GHG_output_Lake_tonCO2 = (Pump_electricity_W * WH_TO_J / 1E6) * (lca.EL_TO_CO2 / 1E3)
        prim_output_Lake_MJoil = (Pump_electricity_W * WH_TO_J / 1E6) * lca.EL_TO_OIL_EQ
        E_used_Lake_W = Pump_electricity_W

    ## activate cold thermal storage (fully mixed water tank)
    if V_tank_m3 > 0:
        Tank_discharging_limit_C = T_DCN_sup_K - DT_COOL - 273.0
        Tank_charging_limit_C = T_tank_fully_charged_C + DT_CHARGING_BUFFER
        if Qc_load_unmet_W > limits[
            'Qc_peak_load_W'] and T_tank_C < Tank_discharging_limit_C:  # peak hour, discharge the storage
            Qc_from_Tank_W = Qc_load_unmet_W if Qc_load_unmet_W <= Qc_tank_discharge_peak_W else Qc_tank_discharge_peak_W
            Qc_to_tank_W = 0
            T_tank_C = storage_tank.calc_fully_mixed_tank(T_tank_C, T_ground_C, Qc_from_Tank_W, Qc_to_tank_W,
                                                          V_tank_m3, 'cold_water')
            # print ('discharging', T_tank_C)
            # update unmet cooling load
            Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_Tank_W

        elif Qc_load_unmet_W <= 0 and T_tank_C > Tank_charging_limit_C:  # no-load, charge the storage
            Qc_to_tank_max_Wh = V_tank_m3 * P_WATER_KGPERM3 * HEAT_CAPACITY_OF_WATER_JPERKGK * (
                    T_tank_C - T_tank_fully_charged_C) * J_TO_WH  # available to charge
            Qc_to_tank_W = Qc_tank_charge_max_W if Qc_to_tank_max_Wh > Qc_tank_charge_max_W else Qc_to_tank_max_Wh
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

    ## activate ACH and VCC to satify the remaining cooling loads
    if Qc_load_unmet_W > 0 and master_to_slave_variables.Absorption_Chiller_on == 1:

        Source_Absorption_Chiller = 1

        # activate ACH
        Qc_from_ACH_W = Qc_load_unmet_W if Qc_load_unmet_W <= limits['Qc_ACH_max_W'] else limits['Qc_ACH_max_W']
        opex_var_ACH_USDperhr, GHG_ACH_tonCO2perhr, prim_energy_ACH_MJoilperhr, Qc_CT_ACH_W, Qh_CHP_ACH_W, E_used_ACH_W = calc_chiller_absorption_operation(
            Qc_from_ACH_W, T_DCN_re_K, T_DCN_sup_K, T_ground_K, prices, lca, config, limits, hour)
        opex_var_ACH_USD.append(opex_var_ACH_USDperhr)

        GHG_ACH_tonCO2.append(GHG_ACH_tonCO2perhr)
        prim_energy_ACH_MJoil.append(prim_energy_ACH_MJoilperhr)
        Qc_CT_W.append(Qc_CT_ACH_W)
        Qh_CHP_W.append(Qh_CHP_ACH_W)
        # update unmet cooling load
        Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_ACH_W

    if Qc_load_unmet_W > 0 and master_to_slave_variables.VCC_on == 1:

        Source_Vapor_compression_chiller = 1

        # activate VCC
        Qc_from_VCC_W = Qc_load_unmet_W if Qc_load_unmet_W <= limits['Qc_VCC_max_W'] else limits['Qc_VCC_max_W']
        opex_var_VCC_USDperhr, GHG_VCC_tonCO2perhr, prim_energy_VCC_MJoilperhr, Qc_CT_VCC_W, E_used_VCC_W = calc_vcc_operation(
            Qc_from_VCC_W, T_DCN_re_K,
            T_DCN_sup_K, lca, limits, hour)
        opex_var_VCC_USD.append(opex_var_VCC_USDperhr)
        GHG_VCC_tonCO2.append(GHG_VCC_tonCO2perhr)
        prim_energy_VCC_MJoil.append(prim_energy_VCC_MJoilperhr)
        Qc_CT_W.append(Qc_CT_VCC_W)
        # update unmet cooling load
        Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_VCC_W

    if Qc_load_unmet_W > 0:

        Source_back_up_Vapor_compression_chiller = 1

        # activate back-up VCC
        Qc_from_backup_VCC_W = Qc_load_unmet_W
        opex_var_VCC_backup_USDperhr, GHG_VCC_backup_tonCO2perhr, \
        prim_energy_VCC_backup_MJoilperhr, Qc_CT_VCC_backup_W, \
        E_used_VCC_backup_W = calc_vcc_backup_operation(Qc_from_backup_VCC_W, T_DCN_re_K,
                                                        T_DCN_sup_K, lca, limits, hour)
        opex_var_VCC_backup_USD.append(opex_var_VCC_backup_USDperhr)
        GHG_VCC_backup_tonCO2.append(GHG_VCC_backup_tonCO2perhr)
        prim_energy_VCC_backup_MJoil.append(prim_energy_VCC_backup_MJoilperhr)
        Qc_CT_W.append(Qc_CT_VCC_backup_W)
        # update unmet cooling load
        Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_backup_VCC_W

    if Qc_load_unmet_W != 0:
        raise ValueError(
            'The cooling load is not met! Fix that calculation!')

    ## activate chillers to charge the thermal storage in order: VCC -> ACH -> VCC_backup
    if Qc_to_tank_W > 0:
        T_chiller_in_K = T_tank_C + 273.0  # temperature of a fully mixed tank
        T_chiller_out_K = (T_tank_fully_charged_C + 273.0) - DT_COOL

        if master_to_slave_variables.VCC_on == 1 and Qc_to_tank_W > 0.0:  # activate VCC to charge the tank
            Qc_from_VCC_to_tank_W = Qc_to_tank_W if Qc_to_tank_W <= limits['Qc_VCC_max_W'] else limits['Qc_VCC_max_W']
            opex_var_VCC_USDperhr, GHG_VCC_tonCO2perhr, prim_energy_VCC_MJoilperhr, Qc_CT_VCC_W, E_used_VCC_W = calc_vcc_operation(
                Qc_from_VCC_to_tank_W, T_chiller_in_K,
                T_chiller_out_K, prices, lca, limits, hour)
            opex_var_VCC_USD.append(opex_var_VCC_USDperhr)
            GHG_VCC_tonCO2.append(GHG_VCC_tonCO2perhr)
            prim_energy_VCC_MJoil.append(prim_energy_VCC_MJoilperhr)
            Qc_CT_W.append(Qc_CT_VCC_W)
            Qc_to_tank_W -= Qc_from_VCC_to_tank_W

        if master_to_slave_variables.Absorption_Chiller_on == 1 and Qc_to_tank_W > 0.0:  # activate ACH to charge the tank
            Qc_from_ACH_to_tank_W = Qc_to_tank_W if Qc_to_tank_W <= limits['Qc_ACH_max_W'] else limits['Qc_ACH_max_W']
            opex_var_ACH_USDperhr, GHG_ACH_tonCO2perhr, prim_energy_MJoilperhr, Qc_CT_ACH_W, Qh_CHP_ACH_W, E_used_ACH_W = calc_chiller_absorption_operation(
                Qc_from_ACH_to_tank_W, T_DCN_re_K, T_DCN_sup_K, T_ground_K, prices, lca, config, limits, hour)
            opex_var_ACH_USD.append(opex_var_ACH_USDperhr)
            GHG_ACH_tonCO2.append(GHG_ACH_tonCO2perhr)
            prim_energy_ACH_MJoil.append(prim_energy_MJoilperhr)
            Qc_CT_W.append(Qc_CT_ACH_W)
            Qh_CHP_W.append(Qh_CHP_ACH_W)
            Qc_to_tank_W -= Qc_from_ACH_to_tank_W

        if Qc_to_tank_W > 0:
            raise ValueError(
                'There are no vapor compression chiller nor absorption chiller installed to charge the storage!')

    ## writing outputs
    performance_indicators_output = {'Opex_var_Lake_USD': opex_var_Lake_USD,
                                     'Opex_var_VCC_USD': np.sum(opex_var_VCC_USD),
                                     'Opex_var_ACH_USD': np.sum(opex_var_ACH_USD),
                                     'Opex_var_VCC_backup_USD': np.sum(opex_var_VCC_backup_USD),
                                     'GHG_Lake_tonCO2': GHG_output_Lake_tonCO2,
                                     'GHG_VCC_tonCO2': np.sum(GHG_VCC_tonCO2),
                                     'GHG_ACH_tonCO2': np.sum(GHG_ACH_tonCO2),
                                     'GHG_VCC_backup_tonCO2': np.sum(GHG_VCC_backup_tonCO2),
                                     'PEN_Lake_MJoil': prim_output_Lake_MJoil,
                                     'PEN_VCC_MJoil': np.sum(prim_energy_VCC_MJoil),
                                     'PEN_ACH_MJoil': np.sum(prim_energy_ACH_MJoil),
                                     'PEN_VCC_backup_MJoil': np.sum(prim_energy_VCC_backup_MJoil),
                                     'E_used_VCC_W': np.sum(E_used_VCC_W),
                                     'E_used_VCC_backup_W': np.sum(E_used_VCC_backup_W),
                                     'E_used_ACH_W': np.sum(E_used_ACH_W),
                                     'E_used_Lake_W': np.sum(E_used_Lake_W),
                                     'mdot_DCN_kgpers': mdot_DCN_kgpers,
                                     'deltaPmax': deltaP_Pa}

    Qc_supply_to_DCN = {'Qc_from_Lake_W': Qc_from_Lake_W,
                        'Qc_from_VCC_W': Qc_from_VCC_W,
                        'Qc_from_ACH_W': Qc_from_ACH_W,
                        'Qc_from_Tank_W': Qc_from_Tank_W,
                        'Qc_from_backup_VCC_W': Qc_from_backup_VCC_W}

    source_output = {"Lake_Status": Source_Lake,
                     "ACH_Status": Source_Absorption_Chiller,
                     "VCC_Status": Source_Vapor_compression_chiller,
                     "VCC_Backup_Status":Source_back_up_Vapor_compression_chiller}

    cooling_resource_potentials_output = {'T_tank_K': T_tank_C + 273.0,
                                          'Qc_avail_from_lake_W': Qc_available_from_lake_W,
                                          'Qc_from_lake_cumulative_W': Qc_from_lake_cumulative_W}

    Qc_CT_tot_W = sum(Qc_CT_W)

    Qh_CHP_tot_W = sum(Qh_CHP_W)

    return performance_indicators_output, Qc_supply_to_DCN, Qc_CT_tot_W, Qh_CHP_tot_W, cooling_resource_potentials_output, source_output

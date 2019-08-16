from __future__ import division

import numpy as np

import cea.technologies.chiller_absorption as chiller_absorption
import cea.technologies.chiller_vapor_compression as chiller_vapor_compression
import cea.technologies.storage_tank as storage_tank
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK, P_WATER_KGPERM3, J_TO_WH, WH_TO_J
from cea.optimization.constants import ACH_T_IN_FROM_CHP, DT_CHARGING_BUFFER
from cea.technologies.constants import DT_COOL
from cea.optimization.constants import VCC_T_COOL_IN

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_vcc_operation(Qc_from_VCC_W, T_DCN_re_K, T_DCN_sup_K, T_source_K, lca, max_VCC_unit_size_W, hour):

    mdot_VCC_kgpers = Qc_from_VCC_W / ((T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)
    VCC_operation = chiller_vapor_compression.calc_VCC(mdot_VCC_kgpers, T_DCN_sup_K, T_DCN_re_K, T_source_K, max_VCC_unit_size_W)

    # unpack outputs
    opex_var_VCC_USD = VCC_operation['wdot_W'] * lca.ELEC_PRICE[hour]
    GHG_VCC_tonCO2perhr = (VCC_operation['wdot_W'] * WH_TO_J / 1E6) * lca.EL_TO_CO2 / 1E3
    prim_energy_VCC_MJoilperhr = (VCC_operation['wdot_W'] * WH_TO_J / 1E6) * lca.EL_TO_OIL_EQ
    Qc_CT_VCC_W = VCC_operation['q_cw_W']
    E_used_VCC_W = opex_var_VCC_USD / lca.ELEC_PRICE[hour]
    return opex_var_VCC_USD, GHG_VCC_tonCO2perhr, prim_energy_VCC_MJoilperhr, Qc_CT_VCC_W, E_used_VCC_W


def calc_vcc_backup_operation(Qc_from_VCC_backup_W, T_DCN_re_K, T_DCN_sup_K, T_source_K, lca, max_VCC_unit_size_W, hour):
    mdot_VCC_kgpers = Qc_from_VCC_backup_W / ((T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)
    VCC_operation = chiller_vapor_compression.calc_VCC(mdot_VCC_kgpers, T_DCN_sup_K, T_DCN_re_K, T_source_K, max_VCC_unit_size_W)
    # unpack outputs
    opex_var_VCC_backup_USD = VCC_operation['wdot_W'] * lca.ELEC_PRICE[hour]
    GHG_VCC_backup_tonCO2perhr = (VCC_operation['wdot_W'] * WH_TO_J / 1E6) * lca.EL_TO_CO2 / 1E3
    prim_energy_VCC_backup_MJoilperhr = (VCC_operation['wdot_W'] * WH_TO_J / 1E6) * lca.EL_TO_OIL_EQ
    Qc_CT_VCC_backup_W = VCC_operation['q_cw_W']
    E_used_VCC_backup_W = opex_var_VCC_backup_USD / lca.ELEC_PRICE[hour]
    return opex_var_VCC_backup_USD, GHG_VCC_backup_tonCO2perhr, prim_energy_VCC_backup_MJoilperhr, Qc_CT_VCC_backup_W, E_used_VCC_backup_W


def calc_chiller_absorption_operation(Qc_from_ACH_W, T_DCN_re_K, T_DCN_sup_K, T_ground_K, lca, locator, hour,
                                      min_chiller_size_W, max_chiller_size_W):
    ACH_type = 'double'

    if T_DCN_re_K == T_DCN_sup_K:
        mdot_ACH_kgpers = 0
    else:
        mdot_ACH_kgpers = Qc_from_ACH_W / (
                (T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)  # required chw flow rate from ACH

    ACH_operation = chiller_absorption.calc_chiller_main(mdot_ACH_kgpers, T_DCN_sup_K, T_DCN_re_K,
                                                         ACH_T_IN_FROM_CHP, T_ground_K, ACH_type, locator,
                                                         min_chiller_size_W, max_chiller_size_W)

    opex_var_ACH_USD = ACH_operation['wdot_W'] * lca.ELEC_PRICE[hour]
    GHG_ACH_tonCO2perhr = ACH_operation['wdot_W'] * WH_TO_J / 1E6 * lca.EL_TO_CO2 / 1E3
    prim_energy_ACH_MJoilperhr = ACH_operation['wdot_W'] * WH_TO_J / 1E6 * lca.EL_TO_OIL_EQ
    Qc_CT_ACH_W = ACH_operation['q_cw_W']
    Qh_CHP_ACH_W = ACH_operation['q_hw_W']
    E_used_ACH_W = ACH_operation['wdot_W']

    return opex_var_ACH_USD, GHG_ACH_tonCO2perhr, prim_energy_ACH_MJoilperhr, Qc_CT_ACH_W, Qh_CHP_ACH_W, E_used_ACH_W


def cooling_resource_activator(mdot_kgpers, T_sup_K, T_re_K,
                               Q_therm_Lake_W,
                               T_source_average_Lake_K,
                               storage_tank_properties, cooling_resource_potentials,
                               T_ground_K, technology_capacities, lca, master_to_slave_variables,
                               Q_cooling_req, hour, locator):
    """

    :param DCN_cooling:
    :param Q_therm_Lake_W:
    :type Q_therm_Lake_W: float
    :param Qc_from_lake_cumulative_W:
    :type Qc_from_lake_cumulative_W: float
    :param prices:
    :return:
    """

    # unpack variables
    T_tank_C = cooling_resource_potentials['T_tank_K'] - 273.0

    # unpack variables
    V_tank_m3 = storage_tank_properties['V_tank_m3']
    # Qc_tank_discharging_limit_W = storage_tank_properties['Qc_tank_discharging_limit_W'] # TODO: redundant
    Qc_tank_charging_limit_W = storage_tank_properties['Qc_tank_charging_limit_W']
    T_tank_fully_charged_C = storage_tank_properties['T_tank_fully_charged_K'] - 273.0
    T_tank_fully_discharged_C = storage_tank_properties['T_tank_fully_discharged_K'] - 273.0
    T_ground_C = T_ground_K - 273.0

    # unpack variables
    max_VCC_unit_size_W = technology_capacities['max_VCC_unit_size_W']
    min_ACH_unit_size_W = technology_capacities['max_VCC_unit_size_W']
    max_ACH_unit_size_W = technology_capacities['max_ACH_unit_size_W']

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

    # calfactor_output = 0
    #
    # Q_lake_VCC_gen_W = 0
    # Qc_from_VCC_W = 0
    # Qc_from_ACH_W = 0
    # Qc_from_Tank_W = 0
    # Qc_from_backup_VCC_W = 0
    # Qc_from_VCC_to_tank_W = 0
    # Qc_to_tank_W = 0

    Qh_CHP_W = []
    Qc_CT_W = []

    E_used_VCC_W = []
    E_used_VCC_backup_W = []
    E_used_ACH_W = []
    E_used_Lake_W = []

    Source_Absorption_Chiller = 0
    Source_Vapor_compression_chiller = 0
    Source_back_up_Vapor_compression_chiller = 0

    ## initializing unmet cooling load
    Qc_load_unmet_W = Q_cooling_req

    # lake-source - vapour compresion chiller
    if master_to_slave_variables.Lake_cooling_on == 1 and Qc_load_unmet_W > 0.0:
        # Free cooling possible from the lake
        Source_Lake = 1
        if Qc_load_unmet_W > Q_therm_Lake_W:
            Q_lake_VCC_gen_W = Q_therm_Lake_W
        else:
            Q_lake_VCC_gen_W = Qc_load_unmet_W

        opex_var_lake_VCC_USDperhr, \
        GHG_lake_VCC_tonCO2perhr, \
        prim_energy_lake_VCC_MJoilperhr, \
        Q_lake_VCC_gen_W, E_used_lake_VCC_W = calc_vcc_operation(Q_lake_VCC_gen_W,
                                                                 T_DCN_re_K,
                                                                 T_DCN_sup_K,
                                                                 T_source_average_Lake_K,
                                                                 lca,
                                                                 max_VCC_unit_size_W,
                                                                 hour)

        Qc_load_unmet_W = Qc_load_unmet_W - Q_lake_VCC_gen_W
    else:
        Source_Free_cooling = 0
        opex_var_lake_VCC_USDperhr = 0.0
        prim_energy_lake_VCC_MJoilperhr = 0.0
        Q_lake_VCC_gen_W = 0.0
        E_used_lake_VCC_W = 0.0

    ## activate cold thermal storage (fully mixed water tank)
    if V_tank_m3 > 0:
        Tank_discharging_limit_C = T_DCN_sup_K - DT_COOL - 273.0  # Temperature required to cool the network at that timestep
        # Tank_charging_limit_C = T_tank_fully_charged_C + DT_CHARGING_BUFFER # todo: redundant

        # Discharge when T_tank_C is low enough to cool the network
        if Qc_load_unmet_W > 0.0 and T_tank_C < Tank_discharging_limit_C:
            # Calculate the maximum Qc available to fully discharge the tank
            Qc_tank_discharging_limit_W = V_tank_m3 * P_WATER_KGPERM3 * HEAT_CAPACITY_OF_WATER_JPERKGK * (
                    T_tank_fully_discharged_C - T_tank_C) * J_TO_WH
            if Qc_load_unmet_W < Qc_tank_discharging_limit_W:
                # Supply all Qc_load_unmet_W
                Qc_from_Tank_W = Qc_load_unmet_W
            else:
                # Supply Qc to the tank limit
                Qc_from_Tank_W = Qc_tank_discharging_limit_W
            Qc_to_tank_W = 0
            T_tank_C = storage_tank.calc_fully_mixed_tank(T_tank_C, T_ground_C, Qc_from_Tank_W, Qc_to_tank_W,
                                                          V_tank_m3, 'cold_water')
            # print ('discharging', T_tank_C)
            # update unmet cooling load
            Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_Tank_W

        # Charging when T_tank_C is high and the tank is not discharging
        # FIXME: (Qc_load_unmet_W <= 0.0) should be removed, because charging is possible when the tank is not discharging
        elif Qc_load_unmet_W <= 0.0 and T_tank_C > T_tank_fully_charged_C:  # no-load, charge the storage
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
            # TODO: [NOTE] Qc_to_tank_W is being supplied in line 290, another way is to add it directly to Qc_load_unmet_W

    ## activate ACH and VCC to satify the remaining cooling loads
    if Qc_load_unmet_W > 0 and master_to_slave_variables.Absorption_Chiller_on == 1:

        Source_Absorption_Chiller = 1

        # activate ACH
        if Qc_load_unmet_W <= technology_capacities['Qc_ACH_max_W']:
            Qc_from_ACH_W = Qc_load_unmet_W
        else:
            Qc_from_ACH_W = technology_capacities['Qc_ACH_max_W']
        opex_var_ACH_USDperhr, \
        GHG_ACH_tonCO2perhr, \
        prim_energy_ACH_MJoilperhr, \
        Qc_CT_ACH_W, \
        Qh_CHP_ACH_W, \
        E_used_ACH_W = calc_chiller_absorption_operation(Qc_from_ACH_W, T_DCN_re_K, T_DCN_sup_K, T_ground_K,
                                                         lca, locator, hour, min_ACH_unit_size_W, max_ACH_unit_size_W)
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
        if Qc_load_unmet_W <= technology_capacities['Qc_VCC_max_W']:
            Qc_from_VCC_W = Qc_load_unmet_W
        else:
            Qc_from_VCC_W = technology_capacities['Qc_VCC_max_W']

        opex_var_VCC_USDperhr, \
        GHG_VCC_tonCO2perhr, \
        prim_energy_VCC_MJoilperhr, \
        Qc_CT_VCC_W, E_used_VCC_W = calc_vcc_operation(Qc_from_VCC_W,
                                                       T_DCN_re_K,
                                                       T_DCN_sup_K,
                                                       VCC_T_COOL_IN,
                                                       lca,
                                                       max_VCC_unit_size_W,
                                                       hour)
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
        E_used_VCC_backup_W = calc_vcc_backup_operation(Qc_from_backup_VCC_W,
                                                        T_DCN_re_K,
                                                        T_DCN_sup_K,
                                                        VCC_T_COOL_IN,
                                                        lca,
                                                        max_VCC_unit_size_W,
                                                        hour)
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
            if Qc_to_tank_W <= technology_capacities['Qc_VCC_nom_W']:
                Qc_from_VCC_to_tank_W = Qc_to_tank_W
            else:
                Qc_from_VCC_to_tank_W = technology_capacities['Qc_VCC_nom_W']

            opex_var_VCC_USDperhr, \
            GHG_VCC_tonCO2perhr, \
            prim_energy_VCC_MJoilperhr, \
            Qc_CT_VCC_W, \
            E_used_VCC_W = calc_vcc_operation(Qc_from_VCC_to_tank_W,
                                              T_chiller_in_K,
                                              T_chiller_out_K,
                                              VCC_T_COOL_IN,
                                              lca,
                                              locator,
                                              hour)

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
            Qh_CHP_ACH_W, \
            E_used_ACH_W = calc_chiller_absorption_operation(Qc_from_ACH_to_tank_W, T_DCN_re_K, T_DCN_sup_K,
                                                             T_ground_K, lca, locator, hour, min_ACH_unit_size_W,
                                                             max_ACH_unit_size_W)
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

    Qc_supply_to_DCN = {'Q_lake_VCC_gen_W': Q_lake_VCC_gen_W,
                        'Qc_from_VCC_W': Qc_from_VCC_W,
                        'Qc_from_ACH_W': Qc_from_ACH_W,
                        'Qc_from_Tank_W': Qc_from_Tank_W,
                        'Qc_from_backup_VCC_W': Qc_from_backup_VCC_W}

    source_output = {"Lake_Status": Source_Lake,
                     "ACH_Status": Source_Absorption_Chiller,
                     "VCC_Status": Source_Vapor_compression_chiller,
                     "VCC_Backup_Status": Source_back_up_Vapor_compression_chiller}

    cooling_resource_potentials_output = {'T_tank_K': T_tank_C + 273.0,
                                          'Qc_avail_from_lake_W': Q_therm_Lake_W,
                                          'Qc_from_lake_cumulative_W': Qc_from_lake_cumulative_W}

    Qc_CT_tot_W = sum(Qc_CT_W)

    Qh_CHP_tot_W = sum(Qh_CHP_W)

    return performance_indicators_output, Qc_supply_to_DCN, Qc_CT_tot_W, Qh_CHP_tot_W, cooling_resource_potentials_output, source_output

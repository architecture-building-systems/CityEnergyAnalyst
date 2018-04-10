"""
=====================================
Operation for decentralized buildings
=====================================
"""
from __future__ import division

import cea.config
import cea.globalvar
import cea.inputlocator
import time
import numpy as np
import pandas as pd
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.optimization.constants import Q_MARGIN_DISCONNECTED, T_GENERATOR_IN_SINGLE_C, T_GENERATOR_IN_DOUBLE_C, \
    EL_TO_CO2, EL_TO_OIL_EQ, NG_BACKUPBOILER_TO_CO2_STD, NG_BACKUPBOILER_TO_OIL_STD, Q_LOSS_DISCONNECTED
import cea.technologies.chiller_vapor_compression as chiller_vapor_compression
import cea.technologies.chiller_absorption as chiller_absorption
import cea.technologies.cooling_tower as cooling_tower
import cea.technologies.boiler as boiler
import cea.technologies.substation as substation
import cea.technologies.solar.solar_collector as solar_collector
from cea.technologies.thermal_network.thermal_network_matrix import calculate_ground_temperature


def deconnected_buildings_cooling_main(locator, building_names, prices, config):
    """
    Computes the parameters for the operation of disconnected buildings output results in csv files.
    There is no optimization at this point. The different cooling energy supply system configurations are calculated
    and compared 1 to 1 to each other. it is a classical combinatorial problem.

    The four configurations include:
    (VCC: Vapor Compression Chiller, ACH: Absorption Chiller, CT: Cooling Tower, Boiler)
    (AHU: Air Handling Units, ARU: Air Recirculation Units, SCU: Sensible Cooling Units)
    - config 0: Direct Expansion / Mini-split units (NOTE: this configuration is not fully built yet)
    - config 1: VCC_to_AAS (AHU + ARU + SCU) + CT
    - config 2: VCC_to_AA (AHU + ARU) + VCC_to_S (SCU) + CT
    - config 3: VCC_to_AA (AHU + ARU) + single effect ACH_S (SCU) + CT + Boiler
    - config 4: single-effect ACH_to_AAS (AHU + ARU + SCU) + Boiler
    - config 5: double-effect ACH_to_AAS (AHU + ARU + SCU) + Boiler

    Note:
    1. Only cooling supply configurations are compared here. The demand for electricity is supplied from the grid,
    and the demand for domestic hot water is supplied from electric boilers.
    2. Single-effect chillers are coupled with flat-plate solar collectors, and the double-effect chillers are coupled
    with evacuated tube solar collectors.

    :param locator: locator class with paths to input/output files
    :param building_names: list with names of buildings
    :param gv: global variable class
    :param config: cea.config
    :param prices: prices class
    :return: one .csv file with results of operations of disconnected buildings; one .csv file with operation of the
    best configuration (Cost, CO2, Primary Energy)
    """

    t0 = time.clock()

    BestData = {}
    total_demand = pd.read_csv(locator.get_total_demand())

    for building_name in building_names:
        print building_name

        ## create empty matrices to store results
        number_config = 6
        result = np.zeros((number_config, 10))

        # assign cooling technologies (columns) to different configurations (rows)
        # technologies columns: [0] DX ; [1] VCC_to_AAS ; [2] VCC_to_AA; [3] VCC_to_S ; [4] ACH_to_S;
        #                       [5] single-effect ACH_to_AAS; [6] double-effect ACH_to_AAS
        # config 0: DX
        result[0][0] = 1
        # config 1: VCC_to_AAS
        result[1][1] = 1
        # config 2: VCC_to_AA + VCC_to_S
        result[2][2] = 1
        result[2][3] = 1
        # config 3: VCC_to_AA + ACH_S
        result[3][2] = 1
        result[3][4] = 1
        # config 4: single-effect ACH_to_AAS
        result[4][5] = 1
        # config 5: double-effect ACH_to_AAS
        result[5][6] = 1

        q_CT_1_W = np.zeros(8760)
        q_CT_2_W = np.zeros(8760)
        q_CT_3_W = np.zeros(8760)
        q_CT_4_W = np.zeros(8760)
        q_CT_5_W = np.zeros(8760)
        q_boiler_3_W = np.zeros(8760)
        q_boiler_4_W = np.zeros(8760)
        q_boiler_5_W = np.zeros(8760)
        T_re_boiler_3_K = np.zeros(8760)
        T_re_boiler_4_K = np.zeros(8760)
        T_re_boiler_5_K = np.zeros(8760)
        InvCosts = np.zeros((6, 1))

        ## Calculate cooling loads for different combinations

        # AAS (AHU + ARU + SCU): combine all loads
        substation.substation_main(locator, total_demand, building_names=[building_name], Flag=False,
                                   heating_configuration=7, cooling_configuration=7)
        loads_AAS = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                usecols=["T_supply_DC_result_K", "T_return_DC_result_K", "mdot_DC_result_kgpers"])
        Qc_load_combination_AAS_W = np.vectorize(calc_new_load)(loads_AAS["mdot_DC_result_kgpers"],
                                                                loads_AAS["T_supply_DC_result_K"],
                                                                loads_AAS["T_return_DC_result_K"])
        Qc_annual_combination_AAS_Wh = Qc_load_combination_AAS_W.sum()
        Qc_nom_combination_AAS_W = Qc_load_combination_AAS_W.max() * (
            1 + Q_MARGIN_DISCONNECTED)  # 20% reliability margin on installed capacity

        # read chilled water supply/return temperatures and mass flows from substation calculation
        T_re_AAS_K = loads_AAS["T_return_DC_result_K"].values
        T_sup_AAS_K = loads_AAS["T_supply_DC_result_K"].values
        mdot_AAS_kgpers = loads_AAS["mdot_DC_result_kgpers"].values

        # AA (AHU + ARU): combine loads from AHU and ARU
        substation.substation_main(locator, total_demand, building_names=[building_name], Flag=False,
                                   heating_configuration=7, cooling_configuration=4)
        loads_AA = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                               usecols=["T_supply_DC_result_K", "T_return_DC_result_K", "mdot_DC_result_kgpers"])
        Qc_load_combination_AA_W = np.vectorize(calc_new_load)(loads_AA["mdot_DC_result_kgpers"],
                                                               loads_AA["T_supply_DC_result_K"],
                                                               loads_AA["T_return_DC_result_K"])
        Qc_annual_combination_AA_Wh = Qc_load_combination_AA_W.sum()
        Qc_nom_combination_AA_W = Qc_load_combination_AA_W.max() * (
            1 + Q_MARGIN_DISCONNECTED)  # 20% reliability margin on installed capacity

        # read chilled water supply/return temperatures and mass flows from substation calculation
        T_re_AA_K = loads_AA["T_return_DC_result_K"].values
        T_sup_AA_K = loads_AA["T_supply_DC_result_K"].values
        mdot_AA_kgpers = loads_AA["mdot_DC_result_kgpers"].values

        # S (SCU): loads from SCU
        substation.substation_main(locator, total_demand, building_names=[building_name], Flag=False,
                                   heating_configuration=7, cooling_configuration=3)
        loads_S = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                              usecols=["T_supply_DC_result_K", "T_return_DC_result_K", "mdot_DC_result_kgpers"])
        Qc_load_combination_S_W = np.vectorize(calc_new_load)(loads_S["mdot_DC_result_kgpers"],
                                                              loads_S["T_supply_DC_result_K"],
                                                              loads_S["T_return_DC_result_K"])
        Qc_annual_combination_S_Wh = Qc_load_combination_S_W.sum()
        Qc_nom_combination_S_W = Qc_load_combination_S_W.max() * (
            1 + Q_MARGIN_DISCONNECTED)  # 20% reliability margin on installed capacity

        # read chilled water supply/return temperatures and mass flows from substation calculation
        T_re_S_K = loads_S["T_return_DC_result_K"].values
        T_sup_S_K = loads_S["T_supply_DC_result_K"].values
        mdot_S_kgpers = loads_S["mdot_DC_result_kgpers"].values

        ## calculate hot water supply conditions to absorption chillers from SC or boiler
        # config 4: Flate Plate Solar Collectors + single-effect absorption chillers
        SC_FP_data = pd.read_csv(locator.SC_results(building_name=building_name, panel_type='FP'),
                                 usecols=["T_SC_sup_C", "T_SC_re_C", "mcp_SC_kWperC", "Q_SC_gen_kWh", "Area_SC_m2"])
        q_sc_gen_FP_Wh = SC_FP_data['Q_SC_gen_kWh'] * 1000
        T_hw_in_FP_C = [x if x > T_GENERATOR_IN_SINGLE_C else T_GENERATOR_IN_SINGLE_C for x in SC_FP_data['T_SC_re_C']]

        # config 5: Evacuated Tube Solar Collectors + double-effect absorption chillers
        SC_ET_data = pd.read_csv(locator.SC_results(building_name=building_name, panel_type='ET'),
                                 usecols=["T_SC_sup_C", "T_SC_re_C", "mcp_SC_kWperC", "Q_SC_gen_kWh", "Area_SC_m2"])
        q_sc_gen_ET_Wh = SC_ET_data['Q_SC_gen_kWh'] * 1000
        T_hw_in_ET_C = [x if x > T_GENERATOR_IN_DOUBLE_C else T_GENERATOR_IN_DOUBLE_C for x in SC_ET_data['T_SC_re_C']]

        ## calculate ground temperatures to estimate cold water supply temperatures for absorption chiller
        T_ground_K = calculate_ground_temperature(locator)  # FIXME: cw is from cooling tower, this is redundant

        ## Calculate operation costs

        # 0: DX # FIXME: read from demand
        # DX_operation = chiller_vcc.calc_VCC(mdot_AAS_kgpers[hour], T_sup_AAS_K[hour], T_re_AAS_K[hour], gv)
        result[0][7] += 1E10  # FIXME: a dummy value to rule out this configuration  # CHF
        result[0][8] += 1E10  # FIXME: a dummy value to rule out this configuration  # kgCO2
        result[0][9] += 1E10  # FIXME: a dummy value to rule out this configuration  # MJ-oil-eq

        # chiller operations for config 1-5
        for hour in range(8760):  # TODO: vectorize
            # modify return temperatures when there is no load
            T_re_AAS_K[hour] = T_re_AAS_K[hour] if T_re_AAS_K[hour] > 0 else T_sup_AAS_K[hour]
            T_re_AA_K[hour] = T_re_AA_K[hour] if T_re_AA_K[hour] > 0 else T_sup_AA_K[hour]
            T_re_S_K[hour] = T_re_S_K[hour] if T_re_S_K[hour] > 0 else T_sup_S_K[hour]

            # 1: VCC (AHU + ARU + SCU) + CT
            VCC_to_AAS_operation = chiller_vapor_compression.calc_VCC(mdot_AAS_kgpers[hour], T_sup_AAS_K[hour],
                                                                      T_re_AAS_K[hour])
            result[1][7] += prices.ELEC_PRICE * VCC_to_AAS_operation['wdot_W']  # CHF
            result[1][8] += EL_TO_CO2 * VCC_to_AAS_operation['wdot_W'] * 3600E-6  # kgCO2
            result[1][9] += EL_TO_OIL_EQ * VCC_to_AAS_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
            q_CT_1_W[hour] = VCC_to_AAS_operation['q_cw_W']

            # 2: VCC (AHU + ARU) + VCC (SCU) + CT
            VCC_to_AA_operation = chiller_vapor_compression.calc_VCC(mdot_AA_kgpers[hour], T_sup_AA_K[hour],
                                                                     T_re_AA_K[hour])
            VCC_to_S_operation = chiller_vapor_compression.calc_VCC(mdot_S_kgpers[hour], T_sup_S_K[hour],
                                                                    T_re_S_K[hour])
            result[2][7] += prices.ELEC_PRICE * (VCC_to_AA_operation['wdot_W'] + VCC_to_S_operation['wdot_W'])  # CHF
            result[2][8] += EL_TO_CO2 * (
                VCC_to_AA_operation['wdot_W'] + VCC_to_S_operation['wdot_W']) * 3600E-6  # kgCO2
            result[2][9] += EL_TO_OIL_EQ * (
                VCC_to_AA_operation['wdot_W'] + VCC_to_S_operation['wdot_W']) * 3600E-6  # MJ-oil-eq
            q_CT_2_W[hour] = VCC_to_AA_operation['q_cw_W'] + VCC_to_S_operation['q_cw_W']

            # 3: VCC (AHU + ARU) + ACH (SCU) + CT
            ACH_type_single = 'single'
            ACH_to_S_operation = chiller_absorption.calc_chiller_main(mdot_S_kgpers[hour], T_sup_S_K[hour],
                                                                      T_re_S_K[hour], T_hw_in_FP_C[hour],
                                                                      T_ground_K[hour], ACH_type_single,
                                                                      Qc_nom_combination_S_W, locator, config)
            result[3][7] += prices.ELEC_PRICE * (VCC_to_AA_operation['wdot_W'] + ACH_to_S_operation['wdot_W'])  # CHF
            result[3][8] += EL_TO_CO2 * (
                VCC_to_AA_operation['wdot_W'] + ACH_to_S_operation['wdot_W']) * 3600E-6  # kgCO2
            result[3][9] += EL_TO_OIL_EQ * (
                VCC_to_AA_operation['wdot_W'] + ACH_to_S_operation['wdot_W']) * 3600E-6  # MJ-oil-eq
            q_CT_3_W[hour] = VCC_to_AA_operation['q_cw_W'] + ACH_to_S_operation['q_cw_W']  # calculate load for CT
            # calculate load for boiler
            q_boiler_3_W[hour] = ACH_to_S_operation['q_hw_W'] - q_sc_gen_FP_Wh[hour] if (q_sc_gen_FP_Wh[hour] >= 0) else \
                ACH_to_S_operation[
                    'q_hw_W']  # TODO: this is assuming the mdot in SC is higher than hot water in the generator
            T_re_boiler_3_K[hour] = ACH_to_S_operation['T_hw_out_C'] + 273.15

            # 4: single-effect ACH (AHU + ARU + SCU)
            ACH_to_AAS_operation_4 = chiller_absorption.calc_chiller_main(mdot_AAS_kgpers[hour], T_sup_AAS_K[hour],
                                                                          T_re_AAS_K[hour], T_hw_in_FP_C[hour],
                                                                          T_ground_K[hour], ACH_type_single,
                                                                          Qc_nom_combination_AAS_W, locator, config)
            result[4][7] += prices.ELEC_PRICE * ACH_to_AAS_operation_4['wdot_W']  # CHF
            result[4][8] += EL_TO_CO2 * ACH_to_AAS_operation_4['wdot_W'] * 3600E-6  # kgCO2
            result[4][9] += EL_TO_OIL_EQ * ACH_to_AAS_operation_4['wdot_W'] * 3600E-6  # MJ-oil-eq
            # calculate load for CT and boilers
            q_CT_4_W[hour] = ACH_to_AAS_operation_4['q_cw_W']
            q_boiler_4_W[hour] = ACH_to_AAS_operation_4['q_hw_W'] - q_sc_gen_FP_Wh[hour] if (
                q_sc_gen_FP_Wh[hour] >= 0) else ACH_to_AAS_operation_4['q_hw_W']
            # TODO: this is assuming the mdot in SC is higher than hot water in the generator
            T_re_boiler_4_K[hour] = ACH_to_AAS_operation_4['T_hw_out_C'] + 273.15

            # 5: double-effect ACH (AHU + ARU + SCU)
            ACH_type_double = 'double'
            ACH_to_AAS_operation_5 = chiller_absorption.calc_chiller_main(mdot_AAS_kgpers[hour], T_sup_AAS_K[hour],
                                                                          T_re_AAS_K[hour], T_hw_in_ET_C[hour],
                                                                          T_ground_K[hour], ACH_type_double,
                                                                          Qc_nom_combination_AAS_W, locator, config)
            result[5][7] += prices.ELEC_PRICE * ACH_to_AAS_operation_5['wdot_W']  # CHF
            result[5][8] += EL_TO_CO2 * ACH_to_AAS_operation_5['wdot_W'] * 3600E-6  # kgCO2
            result[5][9] += EL_TO_OIL_EQ * ACH_to_AAS_operation_5['wdot_W'] * 3600E-6  # MJ-oil-eq
            # calculate load for CT and boilers
            q_CT_5_W[hour] = ACH_to_AAS_operation_5['q_cw_W']
            q_boiler_5_W[hour] = ACH_to_AAS_operation_5['q_hw_W'] - q_sc_gen_ET_Wh[hour] if (
                q_sc_gen_ET_Wh[hour] >= 0) else ACH_to_AAS_operation_5['q_hw_W']
            # TODO: this is assuming the mdot in SC is higher than hot water in the generator
            T_re_boiler_5_K[hour] = ACH_to_AAS_operation_5['T_hw_out_C'] + 273.15

        print 'Finish calculation for cooling technologies'

        ## Calculate CT and boiler operation

        # sizing of CT
        CT_1_nom_size_W = np.max(q_CT_1_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_2_nom_size_W = np.max(q_CT_2_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_3_nom_size_W = np.max(q_CT_3_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_4_nom_size_W = np.max(q_CT_4_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_5_nom_size_W = np.max(q_CT_4_W) * (1 + Q_MARGIN_DISCONNECTED)

        # sizing of boilers
        boiler_3_nom_size_W = np.max(q_boiler_3_W) * (1 + Q_MARGIN_DISCONNECTED)
        boiler_4_nom_size_W = np.max(q_boiler_4_W) * (1 + Q_MARGIN_DISCONNECTED)
        boiler_5_nom_size_W = np.max(q_boiler_5_W) * (1 + Q_MARGIN_DISCONNECTED)

        for hour in range(8760):
            # 1: VCC (AHU + ARU + SCU) + CT
            wdot_W = cooling_tower.calc_CT(q_CT_1_W[hour], CT_1_nom_size_W)

            result[1][7] += prices.ELEC_PRICE * wdot_W  # CHF
            result[1][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
            result[1][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # 2: VCC (AHU + ARU) + VCC (SCU) + CT
            wdot_W = cooling_tower.calc_CT(q_CT_2_W[hour], CT_2_nom_size_W)

            result[2][7] += prices.ELEC_PRICE * wdot_W  # CHF
            result[2][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
            result[2][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # 3: VCC (AHU + ARU) + ACH (SCU) + CT
            wdot_W = cooling_tower.calc_CT(q_CT_3_W[hour], CT_3_nom_size_W)
            boiler_eff = boiler.calc_Cop_boiler(q_boiler_3_W[hour], boiler_3_nom_size_W, T_re_boiler_3_K[hour]) if \
                q_boiler_3_W[hour] > 0 else 0
            Q_gas_for_boiler_Wh = q_boiler_3_W[hour] / boiler_eff if boiler_eff > 0 else 0

            result[3][7] += prices.ELEC_PRICE * wdot_W + prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
            result[3][8] += (EL_TO_CO2 * wdot_W + NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
            result[3][9] += (
                                EL_TO_OIL_EQ * wdot_W + NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

            # 4: single-effect ACH (AHU + ARU + SCU) + CT
            wdot_W = cooling_tower.calc_CT(q_CT_4_W[hour], CT_4_nom_size_W)
            boiler_eff = boiler.calc_Cop_boiler(q_boiler_4_W[hour], boiler_4_nom_size_W, T_re_boiler_4_K[hour]) if \
                q_boiler_4_W[hour] > 0 else 0
            Q_gas_for_boiler_Wh = q_boiler_4_W[hour] / boiler_eff if boiler_eff > 0 else 0

            result[4][7] += prices.ELEC_PRICE * wdot_W + prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
            result[4][8] += (EL_TO_CO2 * wdot_W + NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
            result[4][9] += (
                                EL_TO_OIL_EQ * wdot_W + NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

            # 5: double-effect (AHU + ARU + SCU) + CT
            wdot_W = cooling_tower.calc_CT(q_CT_4_W[hour], CT_4_nom_size_W)
            boiler_eff = boiler.calc_Cop_boiler(q_boiler_4_W[hour], boiler_4_nom_size_W, T_re_boiler_4_K[hour]) if \
                q_boiler_4_W[hour] > 0 else 0
            Q_gas_for_boiler_Wh = q_boiler_4_W[hour] / boiler_eff if boiler_eff > 0 else 0

            result[5][7] += prices.ELEC_PRICE * wdot_W + prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
            result[5][8] += (EL_TO_CO2 * wdot_W + NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
            result[5][9] += (
                                EL_TO_OIL_EQ * wdot_W + NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

        print 'Finish calculation for auxiliary technologies'

        ## Calculate Capex/Opex
        # 1: VCC (AHU + ARU + SCU) + CT
        # Capex_a_DX, Opex_DX
        InvCosts[0][0] = 1E10  # FIXME: a dummy value to rule out this configuration

        # 1: VCC (AHU + ARU + SCU) + CT
        Capex_a_VCC, Opex_VCC = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_AAS_W, locator, config, technology=1)
        Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_1_nom_size_W, locator, config, technology=0)
        InvCosts[1][0] = Capex_a_CT + Opex_CT + Capex_a_VCC + Opex_VCC

        # 2: VCC (AHU + ARU) + VCC (SCU) + CT
        Capex_a_VCC_AA, Opex_VCC_AA = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_AA_W, locator, config,
                                                                              technology=1)
        Capex_a_VCC_S, Opex_VCC_S = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_S_W, locator, config,
                                                                            technology=1)
        Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_2_nom_size_W, locator, config, technology=0)
        InvCosts[2][0] = Capex_a_CT + Opex_CT + Capex_a_VCC_AA + Capex_a_VCC_S + Opex_VCC_AA + Opex_VCC_S

        # 3: VCC (AHU + ARU) + ACH (SCU) + CT + Boiler + SC_FP
        Capex_a_ACH_S, Opex_ACH_S = chiller_absorption.calc_Cinv(Qc_nom_combination_S_W, locator, ACH_type_single, config,
                                                                 technology=0)
        Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_3_nom_size_W, locator, config, technology=0)
        Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_3_nom_size_W, locator, config, technology=0)
        Capex_a_SC_FP, Opex_SC_FP = solar_collector.calc_Cinv_SC(SC_FP_data['Area_SC_m2'][0], locator, config,
                                                                 'FP')
        InvCosts[3][0] = Capex_a_CT + Opex_CT + Capex_a_VCC_AA + Opex_VCC_AA + \
                         Capex_a_ACH_S + Opex_ACH_S + Capex_a_boiler + Opex_boiler + Capex_a_SC_FP + Opex_SC_FP

        # 4: single-effect ACH (AHU + ARU + SCU) + CT + Boiler + SC_FP
        Capex_a_ACH_AAS, Opex_ACH_AAS = chiller_absorption.calc_Cinv(Qc_nom_combination_AAS_W, locator, ACH_type_single, config,
                                                                     technology=0)
        Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_4_nom_size_W, locator, config, technology=0)
        Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_4_nom_size_W, locator, config, technology=0)
        InvCosts[4][0] = Capex_a_CT + Opex_CT + \
                         Capex_a_ACH_AAS + Opex_ACH_AAS + Capex_a_boiler + Opex_boiler + Capex_a_SC_FP + Opex_SC_FP

        # 5: double-effect ACH (AHU + ARU + SCU) + CT + Boiler + SC_ET
        Capex_a_ACH_AAS, Opex_ACH_AAS = chiller_absorption.calc_Cinv(Qc_nom_combination_AAS_W, locator, ACH_type_double, config,
                                                                     technology=1)
        Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_5_nom_size_W, locator, config, technology=0)
        Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_5_nom_size_W, locator, config, technology=0)
        Capex_a_SC_ET, Opex_SC_ET = solar_collector.calc_Cinv_SC(SC_ET_data['Area_SC_m2'][0], locator, config,
                                                                 'ET')
        InvCosts[5][0] = Capex_a_CT + Opex_CT + \
                         Capex_a_ACH_AAS + Opex_ACH_AAS + Capex_a_boiler + Opex_boiler + Capex_a_SC_ET + Opex_SC_ET

        print 'Finish calculation for costs'

        # Best configuration
        Best = np.zeros((number_config, 1))
        indexBest = 0

        # write all results from the 4 configurations into TotalCosts, TotalCO2, TotalPrim
        TotalCosts = np.zeros((number_config, 2))
        TotalCO2 = np.zeros((number_config, 2))
        TotalPrim = np.zeros((number_config, 2))

        for i in range(number_config):
            TotalCosts[i][0] = TotalCO2[i][0] = TotalPrim[i][0] = i
            TotalCosts[i][1] = InvCosts[i][0] + result[i][7]
            TotalCO2[i][1] = result[i][8]
            TotalPrim[i][1] = result[i][9]

        # rank results
        CostsS = TotalCosts[np.argsort(TotalCosts[:, 1])]
        CO2S = TotalCO2[np.argsort(TotalCO2[:, 1])]
        PrimS = TotalPrim[np.argsort(TotalPrim[:, 1])]

        el = len(CostsS)
        rank = 0
        Bestfound = False
        optsearch = np.empty(el)
        optsearch.fill(3)
        indexBest = 0

        while not Bestfound and rank < el:

            optsearch[int(CostsS[rank][0])] -= 1
            optsearch[int(CO2S[rank][0])] -= 1
            optsearch[int(PrimS[rank][0])] -= 1

            if np.count_nonzero(optsearch) != el:
                Bestfound = True
                indexBest = np.where(optsearch == 0)[0][0]

            rank += 1

        # get the best option according to the ranking.
        Best[indexBest][0] = 1

        # Save results in csv file
        dico = {}
        # technologies used in the configurations
        # technologies columns: [0] DX ; [1] VCC_to_AAS ; [2] VCC_to_AA; [3] VCC_to_S ; [4] ACH_to_S;
        #                       [5] single-effect ACH_to_AAS; [6] double-effect ACH_to_AAS
        dico["DX Share"] = result[:, 0]
        dico["VCC_to_AAS Share"] = result[:, 1]
        dico["VCC_to_AA Share"] = result[:, 2]
        dico["VCC_to_S Share"] = result[:, 3]
        dico["single-effect ACH_to_S Share"] = result[:, 4]
        dico["single-effect ACH_to_AAS Share"] = result[:, 5]
        dico["double-effect ACH_to_AAS Share"] = result[:, 6]
        # performance indicators of the configurations
        dico["Operation Costs [CHF]"] = result[:, 7]
        dico["CO2 Emissions [kgCO2-eq]"] = result[:, 8]
        dico["Primary Energy Needs [MJoil-eq]"] = result[:, 9]
        dico["Annualized Investment Costs [CHF]"] = InvCosts[:, 0]
        dico["Total Costs [CHF]"] = TotalCosts[:, 1]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power DX"] = result[:, 0] * Qc_nom_combination_AAS_W
        dico["Nominal Power VCC_to_AAS"] = result[:, 1] * Qc_nom_combination_AAS_W
        dico["Nominal Power VCC_to_AA"] = result[:, 2] * Qc_nom_combination_AA_W
        dico["Nominal Power VCC_to_S"] = result[:, 3] * Qc_nom_combination_S_W
        dico["Nominal Power single-effect ACH_to_S"] = result[:, 4] * Qc_nom_combination_S_W
        dico["Nominal Power single-effect ACH_to_AAS"] = result[:, 5] * Qc_nom_combination_AAS_W
        dico["Nominal Power double-effect ACH_to_AAS"] = result[:, 6] * Qc_nom_combination_AAS_W

        dico_df = pd.DataFrame(dico)
        fName = locator.get_optimization_disconnected_folder_building_result_cooling(building_name)
        dico_df.to_csv(fName, sep=',')

        BestComb = {}
        BestComb["DX Share"] = result[indexBest, 0]
        BestComb["VCC_to_AAS Share"] = result[indexBest, 1]
        BestComb["VCC_to_AA Share"] = result[indexBest, 2]
        BestComb["VCC_to_S Share"] = result[indexBest, 3]
        BestComb["single-effect ACH_to_S Share"] = result[indexBest, 4]
        BestComb["single-effect ACH_to_AAS Share"] = result[indexBest, 5]
        BestComb["double-effect ACH_to_AAS Share"] = result[indexBest, 6]
        BestComb["Operation Costs [CHF]"] = result[indexBest, 7]
        BestComb["CO2 Emissions [kgCO2-eq]"] = result[indexBest, 8]
        BestComb["Primary Energy Needs [MJoil-eq]"] = result[indexBest, 9]
        BestComb["Annualized Investment Costs [CHF]"] = InvCosts[indexBest, 0]
        BestComb["Total Costs [CHF]"] = TotalCosts[indexBest, 1]
        BestComb["Best configuration"] = Best[indexBest, 0]
        BestComb["Nominal Power DX"] = result[indexBest, 0] * Qc_nom_combination_AAS_W
        BestComb["Nominal Power VCC_to_AAS"] = result[indexBest, 1] * Qc_nom_combination_AAS_W
        BestComb["Nominal Power VCC_to_AA"] = result[indexBest, 2] * Qc_nom_combination_AA_W
        BestComb["Nominal Power VCC_to_S"] = result[indexBest, 3] * Qc_nom_combination_S_W
        BestComb["Nominal Power single-effect ACH_to_S"] = result[indexBest, 4] * Qc_nom_combination_S_W
        BestComb["Nominal Power single-effect ACH_to_AAS"] = result[indexBest, 5] * Qc_nom_combination_AAS_W
        BestComb["Nominal Power double-effect ACH_to_AAS"] = result[indexBest, 6] * Qc_nom_combination_AAS_W

        BestData[building_name] = BestComb

    if 0:
        fName = locator.get_optimization_disconnected_folder_disc_op_summary_cooling()
        BestComb_df = pd.DataFrame(BestData)
        BestComb_df.to_csv(fName, sep=',')

    print time.clock() - t0, "seconds process time for the Disconnected Building Routine \n"


# ============================
# other functions
# ============================
def calc_new_load(mdot_kgpers, T_sup_K, T_re_K):
    """
    This function calculates the load distribution side of the district heating distribution.
    :param mdot_kgpers: mass flow
    :param T_sup_K: chilled water supply temperautre
    :param T_re_K: chilled water return temperature
    :type mdot_kgpers: float
    :type TsupDH: float
    :type T_re_K: float
    :return: Q_cooling_load: load of the distribution
    :rtype: float
    """
    if mdot_kgpers > 0:
        Q_cooling_load_W = mdot_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK * (T_re_K - T_sup_K) * (1 + Q_LOSS_DISCONNECTED)  # for cooling load
        if Q_cooling_load_W < 0:
            raise ValueError('Q_cooling_load less than zero, check temperatures!')
    else:
        Q_cooling_load_W = 0

    return Q_cooling_load_W


# ============================
# test
# ============================


def main(config):
    """
    run the whole preprocessing routine
    """
    from cea.optimization.prices import Prices as Prices
    gv = cea.globalvar.GlobalVariables()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name
    building_name = [building_names[6]]
    weather_file = config.weather
    prices = Prices(locator, config)
    deconnected_buildings_cooling_main(locator, building_names, gv, prices, config)

    print 'test_decentralized_buildings_cooling() succeeded'


if __name__ == '__main__':
    main(cea.config.Configuration())

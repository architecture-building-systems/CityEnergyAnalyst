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


def disconnected_buildings_cooling_main(locator, building_names, config, prices):

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

        ## Calculate cooling loads for different combinations
        substation.substation_main(locator, total_demand, building_names=[building_name], heating_configuration=1,
                                   cooling_configuration=1, Flag=False)
        loads_AHU = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                usecols=["T_supply_DC_result_K", "T_return_DC_result_K", "mdot_DC_result_kgpers"])

        substation.substation_main(locator, total_demand, building_names=[building_name], heating_configuration=2,
                                   cooling_configuration=2, Flag=False)
        loads_ARU = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                usecols=["T_supply_DC_result_K", "T_return_DC_result_K", "mdot_DC_result_kgpers"])

        substation.substation_main(locator, total_demand, building_names=[building_name], heating_configuration=3,
                                   cooling_configuration=3, Flag=False)
        loads_SCU = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                usecols=["T_supply_DC_result_K", "T_return_DC_result_K", "mdot_DC_result_kgpers"])

        substation.substation_main(locator, total_demand, building_names=[building_name], heating_configuration=4,
                                   cooling_configuration=4, Flag=False)
        loads_AHU_ARU = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                usecols=["T_supply_DC_result_K", "T_return_DC_result_K", "mdot_DC_result_kgpers"])

        substation.substation_main(locator, total_demand, building_names=[building_name], heating_configuration=5,
                                   cooling_configuration=5, Flag=False)
        loads_AHU_SCU = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                usecols=["T_supply_DC_result_K", "T_return_DC_result_K", "mdot_DC_result_kgpers"])

        substation.substation_main(locator, total_demand, building_names=[building_name], heating_configuration=6,
                                   cooling_configuration=6, Flag=False)
        loads_ARU_SCU = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                usecols=["T_supply_DC_result_K", "T_return_DC_result_K", "mdot_DC_result_kgpers"])

        substation.substation_main(locator, total_demand, building_names=[building_name], heating_configuration=7,
                                   cooling_configuration=7, Flag=False)
        loads_AHU_ARU_SCU = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                usecols=["T_supply_DC_result_K", "T_return_DC_result_K", "mdot_DC_result_kgpers"])

        Qc_load_combination_AHU_W = np.vectorize(calc_new_load)(loads_AHU["mdot_DC_result_kgpers"],
                                                                loads_AHU["T_supply_DC_result_K"],
                                                                loads_AHU["T_return_DC_result_K"])

        Qc_load_combination_ARU_W = np.vectorize(calc_new_load)(loads_ARU["mdot_DC_result_kgpers"],
                                                                loads_ARU["T_supply_DC_result_K"],
                                                                loads_ARU["T_return_DC_result_K"])

        Qc_load_combination_SCU_W = np.vectorize(calc_new_load)(loads_SCU["mdot_DC_result_kgpers"],
                                                                loads_SCU["T_supply_DC_result_K"],
                                                                loads_SCU["T_return_DC_result_K"])

        Qc_load_combination_AHU_ARU_W = np.vectorize(calc_new_load)(loads_AHU_ARU["mdot_DC_result_kgpers"],
                                                                loads_AHU_ARU["T_supply_DC_result_K"],
                                                                loads_AHU_ARU["T_return_DC_result_K"])

        Qc_load_combination_AHU_SCU_W = np.vectorize(calc_new_load)(loads_AHU_SCU["mdot_DC_result_kgpers"],
                                                                loads_AHU_SCU["T_supply_DC_result_K"],
                                                                loads_AHU_SCU["T_return_DC_result_K"])

        Qc_load_combination_ARU_SCU_W = np.vectorize(calc_new_load)(loads_ARU_SCU["mdot_DC_result_kgpers"],
                                                                loads_ARU_SCU["T_supply_DC_result_K"],
                                                                loads_ARU_SCU["T_return_DC_result_K"])

        Qc_load_combination_AHU_ARU_SCU_W = np.vectorize(calc_new_load)(loads_AHU_ARU_SCU["mdot_DC_result_kgpers"],
                                                                loads_AHU_ARU_SCU["T_supply_DC_result_K"],
                                                                loads_AHU_ARU_SCU["T_return_DC_result_K"])

        #
        # Qc_annual_combination_AHU_W = Qc_load_combination_AHU_W.sum()
        # Qc_annual_combination_ARU_W = Qc_load_combination_ARU_W.sum()
        # Qc_annual_combination_SCU_W = Qc_load_combination_SCU_W.sum()
        # Qc_annual_combination_AHU_ARU_W = Qc_load_combination_AHU_ARU_W.sum()
        # Qc_annual_combination_AHU_SCU_W = Qc_load_combination_AHU_SCU_W.sum()
        # Qc_annual_combination_ARU_SCU_W = Qc_load_combination_ARU_SCU_W.sum()
        # Qc_annual_combination_AHU_ARU_SCU_W = Qc_load_combination_AHU_ARU_SCU_W.sum()

        Qc_nom_combination_AHU_W = Qc_load_combination_AHU_W.max() * (1 + Q_MARGIN_DISCONNECTED)  # 20% reliability margin on installed capacity
        Qc_nom_combination_ARU_W = Qc_load_combination_ARU_W.max() * (1 + Q_MARGIN_DISCONNECTED)
        Qc_nom_combination_SCU_W = Qc_load_combination_SCU_W.max() * (1 + Q_MARGIN_DISCONNECTED)
        Qc_nom_combination_AHU_ARU_W = Qc_load_combination_AHU_ARU_W.max() * (1 + Q_MARGIN_DISCONNECTED)
        Qc_nom_combination_AHU_SCU_W = Qc_load_combination_AHU_SCU_W.max() * (1 + Q_MARGIN_DISCONNECTED)
        Qc_nom_combination_ARU_SCU_W = Qc_load_combination_ARU_SCU_W.max() * (1 + Q_MARGIN_DISCONNECTED)
        Qc_nom_combination_AHU_ARU_SCU_W = Qc_load_combination_AHU_ARU_SCU_W.max() * (1 + Q_MARGIN_DISCONNECTED)

        # read chilled water supply/return temperatures and mass flows from substation calculation
        T_re_AHU_K = loads_AHU["T_return_DC_result_K"].values
        T_sup_AHU_K = loads_AHU["T_supply_DC_result_K"].values
        mdot_AHU_kgpers = loads_AHU["mdot_DC_result_kgpers"].values

        T_re_ARU_K = loads_ARU["T_return_DC_result_K"].values
        T_sup_ARU_K = loads_ARU["T_supply_DC_result_K"].values
        mdot_ARU_kgpers = loads_ARU["mdot_DC_result_kgpers"].values

        T_re_SCU_K = loads_SCU["T_return_DC_result_K"].values
        T_sup_SCU_K = loads_SCU["T_supply_DC_result_K"].values
        mdot_SCU_kgpers = loads_SCU["mdot_DC_result_kgpers"].values

        T_re_AHU_ARU_K = loads_AHU_ARU["T_return_DC_result_K"].values
        T_sup_AHU_ARU_K = loads_AHU_ARU["T_supply_DC_result_K"].values
        mdot_AHU_ARU_kgpers = loads_AHU_ARU["mdot_DC_result_kgpers"].values

        T_re_AHU_SCU_K = loads_AHU_SCU["T_return_DC_result_K"].values
        T_sup_AHU_SCU_K = loads_AHU_SCU["T_supply_DC_result_K"].values
        mdot_AHU_SCU_kgpers = loads_AHU_SCU["mdot_DC_result_kgpers"].values

        T_re_ARU_SCU_K = loads_ARU_SCU["T_return_DC_result_K"].values
        T_sup_ARU_SCU_K = loads_ARU_SCU["T_supply_DC_result_K"].values
        mdot_ARU_SCU_kgpers = loads_ARU_SCU["mdot_DC_result_kgpers"].values

        T_re_AHU_ARU_SCU_K = loads_AHU_ARU_SCU["T_return_DC_result_K"].values
        T_sup_AHU_ARU_SCU_K = loads_AHU_ARU_SCU["T_supply_DC_result_K"].values
        mdot_AHU_ARU_SCU_kgpers = loads_AHU_ARU_SCU["mdot_DC_result_kgpers"].values

        ## calculate hot water supply conditions to absorption chillers from SC or boiler
        # Flate Plate Solar Collectors
        SC_FP_data = pd.read_csv(locator.SC_results(building_name=building_name, panel_type='FP'),
                                 usecols=["T_SC_sup_C", "T_SC_re_C", "mcp_SC_kWperC", "Q_SC_gen_kWh", "Area_SC_m2"])
        q_sc_gen_FP_Wh = SC_FP_data['Q_SC_gen_kWh'] * 1000
        T_hw_in_FP_C = [x if x > T_GENERATOR_IN_SINGLE_C else T_GENERATOR_IN_SINGLE_C for x in SC_FP_data['T_SC_re_C']]
        Capex_a_SC_FP, Opex_SC_FP = solar_collector.calc_Cinv_SC(SC_FP_data['Area_SC_m2'][0], locator, config,
                                                                 technology=0)
        # Evacuated Tube Solar Collectors
        SC_ET_data = pd.read_csv(locator.SC_results(building_name=building_name, panel_type='ET'),
                                 usecols=["T_SC_sup_C", "T_SC_re_C", "mcp_SC_kWperC", "Q_SC_gen_kWh", "Area_SC_m2"])
        q_sc_gen_ET_Wh = SC_ET_data['Q_SC_gen_kWh'] * 1000
        T_hw_in_ET_C = [x if x > T_GENERATOR_IN_DOUBLE_C else T_GENERATOR_IN_DOUBLE_C for x in SC_ET_data['T_SC_re_C']]
        Capex_a_SC_ET, Opex_SC_ET = solar_collector.calc_Cinv_SC(SC_ET_data['Area_SC_m2'][0], locator, config,
                                                                 technology=1)

        ## calculate ground temperatures to estimate cold water supply temperatures for absorption chiller
        T_ground_K = calculate_ground_temperature(locator)  # FIXME: cw is from cooling tower, this is redundant


        # Decentralized buildings with only AHU calculations
        result_AHU = np.zeros((4, 10))
        # config 0: DX
        result_AHU[0][0] = 1
        # config 1: VCC to AHU
        result_AHU[1][1] = 1
        # config 2: single-effect ACH to AHU
        result_AHU[2][2] = 1
        # config 3: double-effect ACH to AHU
        result_AHU[3][3] = 1

        q_CT_VCC_to_AHU_W = np.zeros(8760)
        q_CT_single_ACH_to_AHU_W = np.zeros(8760)
        q_boiler_single_ACH_to_AHU_W = np.zeros(8760)
        q_CT_double_ACH_to_AHU_W = np.zeros(8760)
        q_boiler_double_ACH_to_AHU_W = np.zeros(8760)
        T_re_boiler_single_ACH_to_AHU_K = np.zeros(8760)
        T_re_boiler_double_ACH_to_AHU_K = np.zeros(8760)


        result_AHU[0][7] += 1E10  # FIXME: a dummy value to rule out this configuration  # CHF
        result_AHU[0][8] += 1E10  # FIXME: a dummy value to rule out this configuration  # kgCO2
        result_AHU[0][9] += 1E10  # FIXME: a dummy value to rule out this configuration  # MJ-oil-eq

        ACH_type_single = 'single'
        ACH_type_double = 'double'

        if config.disconnected.AHUflag:
            # chiller operations for config 1-5
            for hour in range(8760):  # TODO: vectorize
                # modify return temperatures when there is no load
                T_re_AHU_K[hour] = T_re_AHU_K[hour] if T_re_AHU_K[hour] > 0 else T_sup_AHU_K[hour]


                # 1: VCC
                VCC_to_AHU_operation = chiller_vapor_compression.calc_VCC(mdot_AHU_kgpers[hour], T_sup_AHU_K[hour],
                                                                          T_re_AHU_K[hour])
                result_AHU[1][7] += prices.ELEC_PRICE * VCC_to_AHU_operation['wdot_W']  # CHF
                result_AHU[1][8] += EL_TO_CO2 * VCC_to_AHU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_AHU[1][9] += EL_TO_OIL_EQ * VCC_to_AHU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_AHU_W[hour] = VCC_to_AHU_operation['q_cw_W']


                # 2: single-effect ACH
                single_effect_ACH_to_AHU_operation = chiller_absorption.calc_chiller_main(mdot_AHU_kgpers[hour], T_sup_AHU_K[hour],
                                                                              T_re_AHU_K[hour], T_hw_in_FP_C[hour],
                                                                              T_ground_K[hour], ACH_type_single,
                                                                              Qc_nom_combination_AHU_W, locator, config)

                result_AHU[2][7] += prices.ELEC_PRICE * single_effect_ACH_to_AHU_operation['wdot_W']  # CHF
                result_AHU[2][8] += EL_TO_CO2 * single_effect_ACH_to_AHU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_AHU[2][9] += EL_TO_OIL_EQ * single_effect_ACH_to_AHU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                # calculate load for CT and boilers
                q_CT_single_ACH_to_AHU_W[hour] = single_effect_ACH_to_AHU_operation['q_cw_W']
                q_boiler_single_ACH_to_AHU_W[hour] = single_effect_ACH_to_AHU_operation['q_hw_W'] - q_sc_gen_FP_Wh[hour] if (
                    q_sc_gen_FP_Wh[hour] >= 0) else single_effect_ACH_to_AHU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_single_ACH_to_AHU_K[hour] = single_effect_ACH_to_AHU_operation['T_hw_out_C'] + 273.15

                # 3: double-effect ACH
                double_effect_ACH_to_AHU_operation = chiller_absorption.calc_chiller_main(mdot_AHU_kgpers[hour], T_sup_AHU_K[hour],
                                                                              T_re_AHU_K[hour], T_hw_in_ET_C[hour],
                                                                              T_ground_K[hour], ACH_type_double,
                                                                              Qc_nom_combination_AHU_W, locator, config)

                result_AHU[3][7] += prices.ELEC_PRICE * double_effect_ACH_to_AHU_operation['wdot_W']  # CHF
                result_AHU[3][8] += EL_TO_CO2 * double_effect_ACH_to_AHU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_AHU[3][9] += EL_TO_OIL_EQ * double_effect_ACH_to_AHU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                # calculate load for CT and boilers
                q_CT_double_ACH_to_AHU_W[hour] = double_effect_ACH_to_AHU_operation['q_cw_W']
                q_boiler_double_ACH_to_AHU_W[hour] = double_effect_ACH_to_AHU_operation['q_hw_W'] - q_sc_gen_ET_Wh[hour] if (
                    q_sc_gen_ET_Wh[hour] >= 0) else double_effect_ACH_to_AHU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_double_ACH_to_AHU_K[hour] = double_effect_ACH_to_AHU_operation['T_hw_out_C'] + 273.15
                print (hour)

        # Decentralized buildings with only ARU calculations
        result_ARU = np.zeros((4, 10))
        # config 0: DX
        result_ARU[0][0] = 1
        # config 1: VCC to AHU
        result_ARU[1][1] = 1
        # config 2: single-effect ACH to AHU
        result_ARU[2][2] = 1
        # config 3: double-effect ACH to AHU
        result_ARU[3][3] = 1

        q_CT_VCC_to_ARU_W = np.zeros(8760)
        q_CT_single_ACH_to_ARU_W = np.zeros(8760)
        q_boiler_single_ACH_to_ARU_W = np.zeros(8760)
        q_CT_double_ACH_to_ARU_W = np.zeros(8760)
        q_boiler_double_ACH_to_ARU_W = np.zeros(8760)
        T_re_boiler_single_ACH_to_ARU_K = np.zeros(8760)
        T_re_boiler_double_ACH_to_ARU_K = np.zeros(8760)

        result_ARU[0][7] += 1E10  # FIXME: a dummy value to rule out this configuration  # CHF
        result_ARU[0][8] += 1E10  # FIXME: a dummy value to rule out this configuration  # kgCO2
        result_ARU[0][9] += 1E10  # FIXME: a dummy value to rule out this configuration  # MJ-oil-eq

        if config.disconnected.ARUflag:

            # chiller operations for config 1-5
            for hour in range(8760):  # TODO: vectorize
                # modify return temperatures when there is no load
                T_re_ARU_K[hour] = T_re_ARU_K[hour] if T_re_ARU_K[hour] > 0 else T_sup_AHU_K[hour]

                # 1: VCC
                VCC_to_ARU_operation = chiller_vapor_compression.calc_VCC(mdot_ARU_kgpers[hour], T_sup_ARU_K[hour],
                                                                          T_re_ARU_K[hour])
                result_ARU[1][7] += prices.ELEC_PRICE * VCC_to_ARU_operation['wdot_W']  # CHF
                result_ARU[1][8] += EL_TO_CO2 * VCC_to_ARU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_ARU[1][9] += EL_TO_OIL_EQ * VCC_to_ARU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_ARU_W[hour] = VCC_to_ARU_operation['q_cw_W']

                # 2: single-effect ACH
                single_effect_ACH_to_ARU_operation = chiller_absorption.calc_chiller_main(mdot_ARU_kgpers[hour],
                                                                                          T_sup_ARU_K[hour],
                                                                                          T_re_ARU_K[hour],
                                                                                          T_hw_in_FP_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_type_single,
                                                                                          Qc_nom_combination_ARU_W,
                                                                                          locator, config)

                result_ARU[2][7] += prices.ELEC_PRICE * single_effect_ACH_to_ARU_operation['wdot_W']  # CHF
                result_ARU[2][8] += EL_TO_CO2 * single_effect_ACH_to_ARU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_ARU[2][9] += EL_TO_OIL_EQ * single_effect_ACH_to_ARU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                # calculate load for CT and boilers
                q_CT_single_ACH_to_ARU_W[hour] = single_effect_ACH_to_ARU_operation['q_cw_W']
                q_boiler_single_ACH_to_ARU_W[hour] = single_effect_ACH_to_ARU_operation['q_hw_W'] - q_sc_gen_FP_Wh[
                    hour] if (
                        q_sc_gen_FP_Wh[hour] >= 0) else single_effect_ACH_to_ARU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_single_ACH_to_ARU_K[hour] = single_effect_ACH_to_ARU_operation['T_hw_out_C'] + 273.15

                # 3: double-effect ACH
                double_effect_ACH_to_ARU_operation = chiller_absorption.calc_chiller_main(mdot_ARU_kgpers[hour],
                                                                                          T_sup_ARU_K[hour],
                                                                                          T_re_ARU_K[hour],
                                                                                          T_hw_in_ET_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_type_double,
                                                                                          Qc_nom_combination_ARU_W,
                                                                                          locator, config)

                result_ARU[3][7] += prices.ELEC_PRICE * double_effect_ACH_to_ARU_operation['wdot_W']  # CHF
                result_ARU[3][8] += EL_TO_CO2 * double_effect_ACH_to_ARU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_ARU[3][9] += EL_TO_OIL_EQ * double_effect_ACH_to_ARU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                # calculate load for CT and boilers
                q_CT_double_ACH_to_ARU_W[hour] = double_effect_ACH_to_ARU_operation['q_cw_W']
                q_boiler_double_ACH_to_ARU_W[hour] = double_effect_ACH_to_ARU_operation['q_hw_W'] - q_sc_gen_ET_Wh[
                    hour] if (
                        q_sc_gen_ET_Wh[hour] >= 0) else double_effect_ACH_to_ARU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_double_ACH_to_ARU_K[hour] = double_effect_ACH_to_ARU_operation['T_hw_out_C'] + 273.15
                print (hour)


        # Decentralized buildings with only SCU calculations
        result_SCU = np.zeros((4, 10))
        # config 0: DX
        result_SCU[0][0] = 1
        # config 1: VCC to AHU
        result_SCU[1][1] = 1
        # config 2: single-effect ACH to AHU
        result_SCU[2][2] = 1
        # config 3: double-effect ACH to AHU
        result_SCU[3][3] = 1

        q_CT_VCC_to_SCU_W = np.zeros(8760)
        q_CT_single_ACH_to_SCU_W = np.zeros(8760)
        q_boiler_single_ACH_to_SCU_W = np.zeros(8760)
        q_CT_double_ACH_to_SCU_W = np.zeros(8760)
        q_boiler_double_ACH_to_SCU_W = np.zeros(8760)
        T_re_boiler_single_ACH_to_SCU_K = np.zeros(8760)
        T_re_boiler_double_ACH_to_SCU_K = np.zeros(8760)

        result_SCU[0][7] += 1E10  # FIXME: a dummy value to rule out this configuration  # CHF
        result_SCU[0][8] += 1E10  # FIXME: a dummy value to rule out this configuration  # kgCO2
        result_SCU[0][9] += 1E10  # FIXME: a dummy value to rule out this configuration  # MJ-oil-eq


        if config.disconnected.SCUflag:

            # chiller operations for config 1-5
            for hour in range(8760):  # TODO: vectorize
                # modify return temperatures when there is no load
                T_re_SCU_K[hour] = T_re_SCU_K[hour] if T_re_SCU_K[hour] > 0 else T_sup_SCU_K[hour]

                # 1: VCC
                VCC_to_SCU_operation = chiller_vapor_compression.calc_VCC(mdot_SCU_kgpers[hour], T_sup_SCU_K[hour],
                                                                          T_re_SCU_K[hour])
                result_SCU[1][7] += prices.ELEC_PRICE * VCC_to_SCU_operation['wdot_W']  # CHF
                result_SCU[1][8] += EL_TO_CO2 * VCC_to_SCU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_SCU[1][9] += EL_TO_OIL_EQ * VCC_to_SCU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_SCU_W[hour] = VCC_to_SCU_operation['q_cw_W']

                # 2: single-effect ACH
                single_effect_ACH_to_SCU_operation = chiller_absorption.calc_chiller_main(mdot_SCU_kgpers[hour],
                                                                                          T_sup_SCU_K[hour],
                                                                                          T_re_SCU_K[hour],
                                                                                          T_hw_in_FP_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_type_single,
                                                                                          Qc_nom_combination_SCU_W,
                                                                                          locator, config)

                result_SCU[2][7] += prices.ELEC_PRICE * single_effect_ACH_to_SCU_operation['wdot_W']  # CHF
                result_SCU[2][8] += EL_TO_CO2 * single_effect_ACH_to_SCU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_SCU[2][9] += EL_TO_OIL_EQ * single_effect_ACH_to_SCU_operation[
                    'wdot_W'] * 3600E-6  # MJ-oil-eq
                # calculate load for CT and boilers
                q_CT_single_ACH_to_SCU_W[hour] = single_effect_ACH_to_SCU_operation['q_cw_W']
                q_boiler_single_ACH_to_SCU_W[hour] = single_effect_ACH_to_SCU_operation['q_hw_W'] - q_sc_gen_FP_Wh[
                    hour] if (
                        q_sc_gen_FP_Wh[hour] >= 0) else single_effect_ACH_to_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_single_ACH_to_SCU_K[hour] = single_effect_ACH_to_SCU_operation['T_hw_out_C'] + 273.15

                # 3: double-effect ACH
                double_effect_ACH_to_SCU_operation = chiller_absorption.calc_chiller_main(mdot_SCU_kgpers[hour],
                                                                                          T_sup_SCU_K[hour],
                                                                                          T_re_SCU_K[hour],
                                                                                          T_hw_in_ET_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_type_double,
                                                                                          Qc_nom_combination_SCU_W,
                                                                                          locator, config)

                result_SCU[3][7] += prices.ELEC_PRICE * double_effect_ACH_to_SCU_operation['wdot_W']  # CHF
                result_SCU[3][8] += EL_TO_CO2 * double_effect_ACH_to_SCU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_SCU[3][9] += EL_TO_OIL_EQ * double_effect_ACH_to_SCU_operation[
                    'wdot_W'] * 3600E-6  # MJ-oil-eq
                # calculate load for CT and boilers
                q_CT_double_ACH_to_SCU_W[hour] = double_effect_ACH_to_SCU_operation['q_cw_W']
                q_boiler_double_ACH_to_SCU_W[hour] = double_effect_ACH_to_SCU_operation['q_hw_W'] - q_sc_gen_ET_Wh[
                    hour] if (
                        q_sc_gen_ET_Wh[hour] >= 0) else double_effect_ACH_to_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_double_ACH_to_SCU_K[hour] = double_effect_ACH_to_SCU_operation['T_hw_out_C'] + 273.15
                print (hour)


        # Decentralized buildings with only AHU and ARU calculations
        result_AHU_ARU = np.zeros((4, 10))
        # config 0: DX
        result_AHU_ARU[0][0] = 1
        # config 1: VCC to AHU
        result_AHU_ARU[1][1] = 1
        # config 2: single-effect ACH to AHU
        result_AHU_ARU[2][2] = 1
        # config 3: double-effect ACH to AHU
        result_AHU_ARU[3][3] = 1

        q_CT_VCC_to_AHU_ARU_W = np.zeros(8760)
        q_CT_single_ACH_to_AHU_ARU_W = np.zeros(8760)
        q_boiler_single_ACH_to_AHU_ARU_W = np.zeros(8760)
        q_CT_double_ACH_to_AHU_ARU_W = np.zeros(8760)
        q_boiler_double_ACH_to_AHU_ARU_W = np.zeros(8760)
        T_re_boiler_single_ACH_to_AHU_ARU_K = np.zeros(8760)
        T_re_boiler_double_ACH_to_AHU_ARU_K = np.zeros(8760)

        result_AHU_ARU[0][7] += 1E10  # FIXME: a dummy value to rule out this configuration  # CHF
        result_AHU_ARU[0][8] += 1E10  # FIXME: a dummy value to rule out this configuration  # kgCO2
        result_AHU_ARU[0][9] += 1E10  # FIXME: a dummy value to rule out this configuration  # MJ-oil-eq

        if config.disconnected.AHUARUflag:

            # chiller operations for config 1-5
            for hour in range(8760):  # TODO: vectorize
                # modify return temperatures when there is no load
                T_re_AHU_ARU_K[hour] = T_re_AHU_ARU_K[hour] if T_re_AHU_ARU_K[hour] > 0 else T_sup_AHU_ARU_K[hour]

                # 1: VCC
                VCC_to_AHU_ARU_operation = chiller_vapor_compression.calc_VCC(mdot_AHU_ARU_kgpers[hour], T_sup_AHU_ARU_K[hour],
                                                                          T_re_AHU_ARU_K[hour])
                result_AHU_ARU[1][7] += prices.ELEC_PRICE * VCC_to_AHU_ARU_operation['wdot_W']  # CHF
                result_AHU_ARU[1][8] += EL_TO_CO2 * VCC_to_AHU_ARU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_AHU_ARU[1][9] += EL_TO_OIL_EQ * VCC_to_AHU_ARU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_AHU_ARU_W[hour] = VCC_to_AHU_ARU_operation['q_cw_W']

                # 2: single-effect ACH
                single_effect_ACH_to_AHU_ARU_operation = chiller_absorption.calc_chiller_main(mdot_AHU_ARU_kgpers[hour],
                                                                                          T_sup_AHU_ARU_K[hour],
                                                                                          T_re_AHU_ARU_K[hour],
                                                                                          T_hw_in_FP_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_type_single,
                                                                                          Qc_nom_combination_AHU_ARU_W,
                                                                                          locator, config)

                result_AHU_ARU[2][7] += prices.ELEC_PRICE * single_effect_ACH_to_AHU_ARU_operation['wdot_W']  # CHF
                result_AHU_ARU[2][8] += EL_TO_CO2 * single_effect_ACH_to_AHU_ARU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_AHU_ARU[2][9] += EL_TO_OIL_EQ * single_effect_ACH_to_AHU_ARU_operation[
                    'wdot_W'] * 3600E-6  # MJ-oil-eq
                # calculate load for CT and boilers
                q_CT_single_ACH_to_AHU_ARU_W[hour] = single_effect_ACH_to_AHU_ARU_operation['q_cw_W']
                q_boiler_single_ACH_to_AHU_ARU_W[hour] = single_effect_ACH_to_AHU_ARU_operation['q_hw_W'] - q_sc_gen_FP_Wh[
                    hour] if (
                        q_sc_gen_FP_Wh[hour] >= 0) else single_effect_ACH_to_AHU_ARU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_single_ACH_to_AHU_ARU_K[hour] = single_effect_ACH_to_AHU_ARU_operation['T_hw_out_C'] + 273.15

                # 3: double-effect ACH
                double_effect_ACH_to_AHU_ARU_operation = chiller_absorption.calc_chiller_main(mdot_AHU_ARU_kgpers[hour],
                                                                                          T_sup_AHU_ARU_K[hour],
                                                                                          T_re_AHU_ARU_K[hour],
                                                                                          T_hw_in_ET_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_type_double,
                                                                                          Qc_nom_combination_AHU_ARU_W,
                                                                                          locator, config)

                result_AHU_ARU[3][7] += prices.ELEC_PRICE * double_effect_ACH_to_AHU_ARU_operation['wdot_W']  # CHF
                result_AHU_ARU[3][8] += EL_TO_CO2 * double_effect_ACH_to_AHU_ARU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_AHU_ARU[3][9] += EL_TO_OIL_EQ * double_effect_ACH_to_AHU_ARU_operation[
                    'wdot_W'] * 3600E-6  # MJ-oil-eq
                # calculate load for CT and boilers
                q_CT_double_ACH_to_AHU_ARU_W[hour] = double_effect_ACH_to_AHU_ARU_operation['q_cw_W']
                q_boiler_double_ACH_to_AHU_ARU_W[hour] = double_effect_ACH_to_AHU_ARU_operation['q_hw_W'] - q_sc_gen_ET_Wh[
                    hour] if (
                        q_sc_gen_ET_Wh[hour] >= 0) else double_effect_ACH_to_AHU_ARU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_double_ACH_to_AHU_ARU_K[hour] = double_effect_ACH_to_AHU_ARU_operation['T_hw_out_C'] + 273.15
                print (hour)


        # Decentralized buildings with AHU AND SCU calculations
        result_AHU_SCU = np.zeros((4, 10))
        # config 0: DX
        result_AHU_SCU[0][0] = 1
        # config 1: VCC to AHU
        result_AHU_SCU[1][1] = 1
        # config 2: single-effect ACH to AHU
        result_AHU_SCU[2][2] = 1
        # config 3: double-effect ACH to AHU
        result_AHU_SCU[3][3] = 1

        q_CT_VCC_to_AHU_SCU_W = np.zeros(8760)
        q_CT_single_ACH_to_AHU_SCU_W = np.zeros(8760)
        q_boiler_single_ACH_to_AHU_SCU_W = np.zeros(8760)
        q_CT_double_ACH_to_AHU_SCU_W = np.zeros(8760)
        q_boiler_double_ACH_to_AHU_SCU_W = np.zeros(8760)
        T_re_boiler_single_ACH_to_AHU_SCU_K = np.zeros(8760)
        T_re_boiler_double_ACH_to_AHU_SCU_K = np.zeros(8760)

        result_AHU_SCU[0][7] += 1E10  # FIXME: a dummy value to rule out this configuration  # CHF
        result_AHU_SCU[0][8] += 1E10  # FIXME: a dummy value to rule out this configuration  # kgCO2
        result_AHU_SCU[0][9] += 1E10  # FIXME: a dummy value to rule out this configuration  # MJ-oil-eq

        if config.disconnected.AHUSCUflag:

            # chiller operations for config 1-5
            for hour in range(8760):  # TODO: vectorize
                # modify return temperatures when there is no load
                T_re_AHU_SCU_K[hour] = T_re_AHU_SCU_K[hour] if T_re_AHU_SCU_K[hour] > 0 else T_sup_AHU_SCU_K[hour]

                # 1: VCC
                VCC_to_AHU_SCU_operation = chiller_vapor_compression.calc_VCC(mdot_AHU_SCU_kgpers[hour], T_sup_AHU_SCU_K[hour],
                                                                          T_re_AHU_SCU_K[hour])
                result_AHU_SCU[1][7] += prices.ELEC_PRICE * VCC_to_AHU_SCU_operation['wdot_W']  # CHF
                result_AHU_SCU[1][8] += EL_TO_CO2 * VCC_to_AHU_SCU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_AHU_SCU[1][9] += EL_TO_OIL_EQ * VCC_to_AHU_SCU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_AHU_SCU_W[hour] = VCC_to_AHU_SCU_operation['q_cw_W']

                # 2: single-effect ACH
                single_effect_ACH_to_AHU_SCU_operation = chiller_absorption.calc_chiller_main(mdot_AHU_SCU_kgpers[hour],
                                                                                          T_sup_AHU_SCU_K[hour],
                                                                                          T_re_AHU_SCU_K[hour],
                                                                                          T_hw_in_FP_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_type_single,
                                                                                          Qc_nom_combination_AHU_SCU_W,
                                                                                          locator, config)

                result_AHU_SCU[2][7] += prices.ELEC_PRICE * single_effect_ACH_to_AHU_SCU_operation['wdot_W']  # CHF
                result_AHU_SCU[2][8] += EL_TO_CO2 * single_effect_ACH_to_AHU_SCU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_AHU_SCU[2][9] += EL_TO_OIL_EQ * single_effect_ACH_to_AHU_SCU_operation[
                    'wdot_W'] * 3600E-6  # MJ-oil-eq
                # calculate load for CT and boilers
                q_CT_single_ACH_to_AHU_SCU_W[hour] = single_effect_ACH_to_AHU_SCU_operation['q_cw_W']
                q_boiler_single_ACH_to_AHU_SCU_W[hour] = single_effect_ACH_to_AHU_SCU_operation['q_hw_W'] - q_sc_gen_FP_Wh[
                    hour] if (
                        q_sc_gen_FP_Wh[hour] >= 0) else single_effect_ACH_to_AHU_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_single_ACH_to_AHU_SCU_K[hour] = single_effect_ACH_to_AHU_SCU_operation['T_hw_out_C'] + 273.15

                # 3: double-effect ACH
                double_effect_ACH_to_AHU_SCU_operation = chiller_absorption.calc_chiller_main(mdot_AHU_SCU_kgpers[hour],
                                                                                          T_sup_AHU_SCU_K[hour],
                                                                                          T_re_AHU_SCU_K[hour],
                                                                                          T_hw_in_ET_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_type_double,
                                                                                          Qc_nom_combination_AHU_SCU_W,
                                                                                          locator, config)

                result_AHU_SCU[3][7] += prices.ELEC_PRICE * double_effect_ACH_to_AHU_SCU_operation['wdot_W']  # CHF
                result_AHU_SCU[3][8] += EL_TO_CO2 * double_effect_ACH_to_AHU_SCU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_AHU_SCU[3][9] += EL_TO_OIL_EQ * double_effect_ACH_to_AHU_SCU_operation[
                    'wdot_W'] * 3600E-6  # MJ-oil-eq
                # calculate load for CT and boilers
                q_CT_double_ACH_to_AHU_SCU_W[hour] = double_effect_ACH_to_AHU_SCU_operation['q_cw_W']
                q_boiler_double_ACH_to_AHU_SCU_W[hour] = double_effect_ACH_to_AHU_SCU_operation['q_hw_W'] - q_sc_gen_ET_Wh[
                    hour] if (
                        q_sc_gen_ET_Wh[hour] >= 0) else double_effect_ACH_to_AHU_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_double_ACH_to_AHU_SCU_K[hour] = double_effect_ACH_to_AHU_SCU_operation['T_hw_out_C'] + 273.15
                print (hour)


        # Decentralized buildings with only ARU AND SCU calculations
        result_ARU_SCU = np.zeros((4, 10))
        # config 0: DX
        result_ARU_SCU[0][0] = 1
        # config 1: VCC to AHU
        result_ARU_SCU[1][1] = 1
        # config 2: single-effect ACH to AHU
        result_ARU_SCU[2][2] = 1
        # config 3: double-effect ACH to AHU
        result_ARU_SCU[3][3] = 1

        q_CT_VCC_to_ARU_SCU_W = np.zeros(8760)
        q_CT_single_ACH_to_ARU_SCU_W = np.zeros(8760)
        q_boiler_single_ACH_to_ARU_SCU_W = np.zeros(8760)
        q_CT_double_ACH_to_ARU_SCU_W = np.zeros(8760)
        q_boiler_double_ACH_to_ARU_SCU_W = np.zeros(8760)
        T_re_boiler_single_ACH_to_ARU_SCU_K = np.zeros(8760)
        T_re_boiler_double_ACH_to_ARU_SCU_K = np.zeros(8760)

        result_ARU_SCU[0][7] += 1E10  # FIXME: a dummy value to rule out this configuration  # CHF
        result_ARU_SCU[0][8] += 1E10  # FIXME: a dummy value to rule out this configuration  # kgCO2
        result_ARU_SCU[0][9] += 1E10  # FIXME: a dummy value to rule out this configuration  # MJ-oil-eq

        if config.disconnected.ARUSCUflag:
            # chiller operations for config 1-5
            for hour in range(8760):  # TODO: vectorize
                # modify return temperatures when there is no load
                T_re_ARU_SCU_K[hour] = T_re_ARU_SCU_K[hour] if T_re_ARU_SCU_K[hour] > 0 else T_sup_ARU_SCU_K[hour]

                # 1: VCC
                VCC_to_ARU_SCU_operation = chiller_vapor_compression.calc_VCC(mdot_ARU_SCU_kgpers[hour], T_sup_ARU_SCU_K[hour],
                                                                          T_re_ARU_SCU_K[hour])
                result_ARU_SCU[1][7] += prices.ELEC_PRICE * VCC_to_ARU_SCU_operation['wdot_W']  # CHF
                result_ARU_SCU[1][8] += EL_TO_CO2 * VCC_to_ARU_SCU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_ARU_SCU[1][9] += EL_TO_OIL_EQ * VCC_to_ARU_SCU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_ARU_SCU_W[hour] = VCC_to_ARU_SCU_operation['q_cw_W']

                # 2: single-effect ACH
                single_effect_ACH_to_ARU_SCU_operation = chiller_absorption.calc_chiller_main(mdot_ARU_SCU_kgpers[hour],
                                                                                          T_sup_ARU_SCU_K[hour],
                                                                                          T_re_ARU_SCU_K[hour],
                                                                                          T_hw_in_FP_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_type_single,
                                                                                          Qc_nom_combination_ARU_SCU_W,
                                                                                          locator, config)

                result_ARU_SCU[2][7] += prices.ELEC_PRICE * single_effect_ACH_to_ARU_SCU_operation['wdot_W']  # CHF
                result_ARU_SCU[2][8] += EL_TO_CO2 * single_effect_ACH_to_ARU_SCU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_ARU_SCU[2][9] += EL_TO_OIL_EQ * single_effect_ACH_to_ARU_SCU_operation[
                    'wdot_W'] * 3600E-6  # MJ-oil-eq
                # calculate load for CT and boilers
                q_CT_single_ACH_to_ARU_SCU_W[hour] = single_effect_ACH_to_ARU_SCU_operation['q_cw_W']
                q_boiler_single_ACH_to_ARU_SCU_W[hour] = single_effect_ACH_to_ARU_SCU_operation['q_hw_W'] - q_sc_gen_FP_Wh[
                    hour] if (
                        q_sc_gen_FP_Wh[hour] >= 0) else single_effect_ACH_to_ARU_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_single_ACH_to_ARU_SCU_K[hour] = single_effect_ACH_to_ARU_SCU_operation['T_hw_out_C'] + 273.15

                # 3: double-effect ACH
                double_effect_ACH_to_ARU_SCU_operation = chiller_absorption.calc_chiller_main(mdot_ARU_SCU_kgpers[hour],
                                                                                          T_sup_ARU_SCU_K[hour],
                                                                                          T_re_ARU_SCU_K[hour],
                                                                                          T_hw_in_ET_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_type_double,
                                                                                          Qc_nom_combination_ARU_SCU_W,
                                                                                          locator, config)

                result_ARU_SCU[3][7] += prices.ELEC_PRICE * double_effect_ACH_to_ARU_SCU_operation['wdot_W']  # CHF
                result_ARU_SCU[3][8] += EL_TO_CO2 * double_effect_ACH_to_ARU_SCU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_ARU_SCU[3][9] += EL_TO_OIL_EQ * double_effect_ACH_to_SCU_operation[
                    'wdot_W'] * 3600E-6  # MJ-oil-eq
                # calculate load for CT and boilers
                q_CT_double_ACH_to_ARU_SCU_W[hour] = double_effect_ACH_to_ARU_SCU_operation['q_cw_W']
                q_boiler_double_ACH_to_ARU_SCU_W[hour] = double_effect_ACH_to_ARU_SCU_operation['q_hw_W'] - q_sc_gen_ET_Wh[
                    hour] if (
                        q_sc_gen_ET_Wh[hour] >= 0) else double_effect_ACH_to_ARU_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_double_ACH_to_ARU_SCU_K[hour] = double_effect_ACH_to_ARU_SCU_operation['T_hw_out_C'] + 273.15

                print (hour)

        # Decentralized buildings with only ARU AND SCU calculations
        result_AHU_ARU_SCU = np.zeros((6, 10))
        # config 0: DX
        result_AHU_ARU_SCU[0][0] = 1
        # config 1: VCC to AHU
        result_AHU_ARU_SCU[1][1] = 1
        # config 2: single-effect ACH to AHU
        result_AHU_ARU_SCU[2][2] = 1
        # config 3: double-effect ACH to AHU
        result_AHU_ARU_SCU[3][3] = 1
        # config 4: VCC to AHU + ARU and VCC to SCU
        result_AHU_ARU_SCU[4][4] = 1
        result_AHU_ARU_SCU[4][5] = 1
        # config 5: VCC to AHU + ARU and single effect ACH to SCU
        result_AHU_ARU_SCU[5][4] = 1
        result_AHU_ARU_SCU[5][6] = 1

        q_CT_VCC_to_AHU_ARU_SCU_W = np.zeros(8760)
        q_CT_VCC_to_AHU_ARU_and_VCC_to_SCU_W = np.zeros(8760)
        q_CT_VCC_to_AHU_ARU_and_single_ACH_to_SCU_W = np.zeros(8760)
        q_CT_single_ACH_to_AHU_ARU_SCU_W = np.zeros(8760)
        q_boiler_single_ACH_to_AHU_ARU_SCU_W = np.zeros(8760)
        q_CT_double_ACH_to_AHU_ARU_SCU_W = np.zeros(8760)
        q_boiler_double_ACH_to_AHU_ARU_SCU_W = np.zeros(8760)
        q_boiler_VCC_to_AHU_ARU_and_single_ACH_to_SCU_W = np.zeros(8760)
        T_re_boiler_single_ACH_to_AHU_ARU_SCU_K = np.zeros(8760)
        T_re_boiler_double_ACH_to_AHU_ARU_SCU_K = np.zeros(8760)
        T_re_boiler_VCC_to_AHU_ARU_and_single_ACH_to_SCU_K = np.zeros(8760)

        result_AHU_ARU_SCU[0][7] += 1E10  # FIXME: a dummy value to rule out this configuration  # CHF
        result_AHU_ARU_SCU[0][8] += 1E10  # FIXME: a dummy value to rule out this configuration  # kgCO2
        result_AHU_ARU_SCU[0][9] += 1E10  # FIXME: a dummy value to rule out this configuration  # MJ-oil-eq

        if config.disconnected.AHUARUSCUflag:

            # chiller operations for config 1-5
            for hour in range(8760):  # TODO: vectorize
                # modify return temperatures when there is no load
                T_re_AHU_ARU_SCU_K[hour] = T_re_AHU_ARU_SCU_K[hour] if T_re_AHU_ARU_SCU_K[hour] > 0 else T_sup_AHU_ARU_SCU_K[hour]

                # 1: VCC (AHU + ARU + SCU) + CT
                VCC_to_AHU_ARU_SCU_operation = chiller_vapor_compression.calc_VCC(mdot_AHU_ARU_SCU_kgpers[hour],
                                                                              T_sup_AHU_ARU_SCU_K[hour],
                                                                              T_re_AHU_ARU_SCU_K[hour])
                result_AHU_ARU_SCU[1][7] += prices.ELEC_PRICE * VCC_to_AHU_ARU_SCU_operation['wdot_W']  # CHF
                result_AHU_ARU_SCU[1][8] += EL_TO_CO2 * VCC_to_AHU_ARU_SCU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[1][9] += EL_TO_OIL_EQ * VCC_to_AHU_ARU_SCU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_AHU_ARU_SCU_W[hour] = VCC_to_AHU_ARU_SCU_operation['q_cw_W']

                # 2: single-effect ACH (AHU + ARU + SCU) + CT + Boiler + SC_FP
                single_effect_ACH_to_AHU_ARU_SCU_operation = chiller_absorption.calc_chiller_main(mdot_AHU_ARU_SCU_kgpers[hour],
                                                                                              T_sup_AHU_ARU_SCU_K[hour],
                                                                                              T_re_AHU_ARU_SCU_K[hour],
                                                                                              T_hw_in_FP_C[hour],
                                                                                              T_ground_K[hour],
                                                                                              ACH_type_single,
                                                                                              Qc_nom_combination_AHU_ARU_SCU_W,
                                                                                              locator, config)

                result_AHU_ARU_SCU[2][7] += prices.ELEC_PRICE * single_effect_ACH_to_AHU_ARU_SCU_operation['wdot_W']  # CHF
                result_AHU_ARU_SCU[2][8] += EL_TO_CO2 * single_effect_ACH_to_AHU_ARU_SCU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[2][9] += EL_TO_OIL_EQ * single_effect_ACH_to_AHU_ARU_SCU_operation[
                    'wdot_W'] * 3600E-6  # MJ-oil-eq
                # calculate load for CT and boilers
                q_CT_single_ACH_to_AHU_ARU_SCU_W[hour] = single_effect_ACH_to_AHU_ARU_SCU_operation['q_cw_W']
                q_boiler_single_ACH_to_AHU_ARU_SCU_W[hour] = single_effect_ACH_to_AHU_ARU_SCU_operation['q_hw_W'] - \
                                                         q_sc_gen_FP_Wh[
                                                             hour] if (
                        q_sc_gen_FP_Wh[hour] >= 0) else single_effect_ACH_to_AHU_ARU_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_single_ACH_to_AHU_ARU_SCU_K[hour] = single_effect_ACH_to_AHU_ARU_SCU_operation[
                                                                'T_hw_out_C'] + 273.15

                # 3: double-effect ACH (AHU + ARU + SCU) + CT + Boiler + SC_ET
                double_effect_ACH_to_AHU_ARU_SCU_operation = chiller_absorption.calc_chiller_main(mdot_AHU_ARU_SCU_kgpers[hour],
                                                                                              T_sup_AHU_ARU_SCU_K[hour],
                                                                                              T_re_AHU_ARU_SCU_K[hour],
                                                                                              T_hw_in_ET_C[hour],
                                                                                              T_ground_K[hour],
                                                                                              ACH_type_double,
                                                                                              Qc_nom_combination_AHU_ARU_SCU_W,
                                                                                              locator, config)

                result_AHU_ARU_SCU[3][7] += prices.ELEC_PRICE * double_effect_ACH_to_AHU_ARU_SCU_operation['wdot_W']  # CHF
                result_AHU_ARU_SCU[3][8] += EL_TO_CO2 * double_effect_ACH_to_AHU_ARU_SCU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[3][9] += EL_TO_OIL_EQ * double_effect_ACH_to_AHU_ARU_SCU_operation[
                    'wdot_W'] * 3600E-6  # MJ-oil-eq
                # calculate load for CT and boilers
                q_CT_double_ACH_to_AHU_ARU_SCU_W[hour] = double_effect_ACH_to_AHU_ARU_SCU_operation['q_cw_W']
                q_boiler_double_ACH_to_AHU_ARU_SCU_W[hour] = double_effect_ACH_to_AHU_ARU_SCU_operation['q_hw_W'] - \
                                                         q_sc_gen_ET_Wh[
                                                             hour] if (
                        q_sc_gen_ET_Wh[hour] >= 0) else double_effect_ACH_to_AHU_ARU_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_double_ACH_to_AHU_ARU_SCU_K[hour] = double_effect_ACH_to_AHU_ARU_SCU_operation[
                                                                'T_hw_out_C'] + 273.15

                # 4: VCC (AHU + ARU) + VCC (SCU) + CT

                result_AHU_ARU_SCU[4][7] += prices.ELEC_PRICE * (VCC_to_AHU_ARU_operation['wdot_W'] + VCC_to_SCU_operation['wdot_W'])  # CHF
                result_AHU_ARU_SCU[4][8] += EL_TO_CO2 * (VCC_to_AHU_ARU_operation['wdot_W'] + VCC_to_SCU_operation['wdot_W']) * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[4][9] += EL_TO_OIL_EQ * (VCC_to_AHU_ARU_operation['wdot_W'] + VCC_to_SCU_operation['wdot_W']) * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_AHU_ARU_and_VCC_to_SCU_W[hour] = (VCC_to_AHU_ARU_operation['q_cw_W'] + VCC_to_SCU_operation['q_cw_W'])

                # 5: VCC (AHU + ARU) + ACH (SCU) + CT

                result_AHU_ARU_SCU[5][7] += prices.ELEC_PRICE * (VCC_to_AHU_ARU_operation['wdot_W'] + single_effect_ACH_to_SCU_operation['wdot_W'])  # CHF
                result_AHU_ARU_SCU[5][8] += EL_TO_CO2 * (VCC_to_AHU_ARU_operation['wdot_W'] + single_effect_ACH_to_SCU_operation['wdot_W']) * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[5][9] += EL_TO_OIL_EQ * (VCC_to_AHU_ARU_operation['wdot_W'] + single_effect_ACH_to_SCU_operation['wdot_W']) * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_AHU_ARU_and_single_ACH_to_SCU_W[hour] = (VCC_to_AHU_ARU_operation['q_cw_W'] + single_effect_ACH_to_SCU_operation['q_cw_W'])
                # calculate load for CT and boilers
                q_boiler_VCC_to_AHU_ARU_and_single_ACH_to_SCU_W[hour] = single_effect_ACH_to_SCU_operation['q_hw_W'] - \
                                                         q_sc_gen_ET_Wh[
                                                             hour] if (
                        q_sc_gen_ET_Wh[hour] >= 0) else single_effect_ACH_to_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_VCC_to_AHU_ARU_and_single_ACH_to_SCU_K[hour] = single_effect_ACH_to_SCU_operation[
                                                                'T_hw_out_C'] + 273.15

        print (building_name)

        ## Calculate CT and boiler operation

        # sizing of CT
        CT_VCC_to_AHU_nom_size_W = np.max(q_CT_VCC_to_AHU_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_single_ACH_to_AHU_nom_size_W = np.max(q_CT_single_ACH_to_AHU_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_double_ACH_to_AHU_nom_size_W = np.max(q_CT_double_ACH_to_AHU_W) * (1 + Q_MARGIN_DISCONNECTED)

        CT_VCC_to_ARU_nom_size_W = np.max(q_CT_VCC_to_ARU_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_single_ACH_to_ARU_nom_size_W = np.max(q_CT_single_ACH_to_ARU_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_double_ACH_to_ARU_nom_size_W = np.max(q_CT_double_ACH_to_ARU_W) * (1 + Q_MARGIN_DISCONNECTED)

        CT_VCC_to_SCU_nom_size_W = np.max(q_CT_VCC_to_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_single_ACH_to_SCU_nom_size_W = np.max(q_CT_single_ACH_to_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_double_ACH_to_SCU_nom_size_W = np.max(q_CT_double_ACH_to_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)

        CT_VCC_to_AHU_ARU_nom_size_W = np.max(q_CT_VCC_to_AHU_ARU_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_single_ACH_to_AHU_ARU_nom_size_W = np.max(q_CT_single_ACH_to_AHU_ARU_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_double_ACH_to_AHU_ARU_nom_size_W = np.max(q_CT_double_ACH_to_AHU_ARU_W) * (1 + Q_MARGIN_DISCONNECTED)

        CT_VCC_to_AHU_SCU_nom_size_W = np.max(q_CT_VCC_to_AHU_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_single_ACH_to_AHU_SCU_nom_size_W = np.max(q_CT_single_ACH_to_AHU_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_double_ACH_to_AHU_SCU_nom_size_W = np.max(q_CT_double_ACH_to_AHU_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)

        CT_VCC_to_ARU_SCU_nom_size_W = np.max(q_CT_VCC_to_ARU_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_single_ACH_to_ARU_SCU_nom_size_W = np.max(q_CT_single_ACH_to_ARU_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_double_ACH_to_ARU_SCU_nom_size_W = np.max(q_CT_double_ACH_to_ARU_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)

        CT_VCC_to_AHU_ARU_SCU_nom_size_W = np.max(q_CT_VCC_to_AHU_ARU_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_single_ACH_to_AHU_ARU_SCU_nom_size_W = np.max(q_CT_single_ACH_to_AHU_ARU_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_double_ACH_to_AHU_ARU_SCU_nom_size_W = np.max(q_CT_double_ACH_to_AHU_ARU_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_VCC_to_AHU_ARU_and_VCC_to_SCU_nom_size_W = np.max(q_CT_VCC_to_AHU_ARU_and_VCC_to_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)
        CT_VCC_to_AHU_ARU_and_single_ACH_to_SCU_nom_size_W = np.max(q_CT_VCC_to_AHU_ARU_and_single_ACH_to_SCU_W)  * (1 + Q_MARGIN_DISCONNECTED)

        # sizing of boilers
        boiler_single_ACH_to_AHU_nom_size_W = np.max(q_boiler_single_ACH_to_AHU_W) * (1 + Q_MARGIN_DISCONNECTED)
        boiler_double_ACH_to_AHU_nom_size_W = np.max(q_boiler_double_ACH_to_AHU_W) * (1 + Q_MARGIN_DISCONNECTED)

        boiler_single_ACH_to_ARU_nom_size_W = np.max(q_boiler_single_ACH_to_ARU_W) * (1 + Q_MARGIN_DISCONNECTED)
        boiler_double_ACH_to_ARU_nom_size_W = np.max(q_boiler_double_ACH_to_ARU_W) * (1 + Q_MARGIN_DISCONNECTED)

        boiler_single_ACH_to_SCU_nom_size_W = np.max(q_boiler_single_ACH_to_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)
        boiler_double_ACH_to_SCU_nom_size_W = np.max(q_boiler_double_ACH_to_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)

        boiler_single_ACH_to_AHU_ARU_nom_size_W = np.max(q_boiler_single_ACH_to_AHU_ARU_W) * (1 + Q_MARGIN_DISCONNECTED)
        boiler_double_ACH_to_AHU_ARU_nom_size_W = np.max(q_boiler_double_ACH_to_AHU_ARU_W) * (1 + Q_MARGIN_DISCONNECTED)

        boiler_single_ACH_to_AHU_SCU_nom_size_W = np.max(q_boiler_single_ACH_to_AHU_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)
        boiler_double_ACH_to_AHU_SCU_nom_size_W = np.max(q_boiler_double_ACH_to_AHU_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)

        boiler_single_ACH_to_ARU_SCU_nom_size_W = np.max(q_boiler_single_ACH_to_ARU_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)
        boiler_double_ACH_to_ARU_SCU_nom_size_W = np.max(q_boiler_double_ACH_to_ARU_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)

        boiler_single_ACH_to_AHU_ARU_SCU_nom_size_W = np.max(q_boiler_single_ACH_to_AHU_ARU_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)
        boiler_double_ACH_to_AHU_ARU_SCU_nom_size_W = np.max(q_boiler_double_ACH_to_AHU_ARU_SCU_W) * (1 + Q_MARGIN_DISCONNECTED)

        boiler_VCC_to_AHU_ARU_and_single_ACH_to_SCU_nom_size_W = boiler_single_ACH_to_SCU_nom_size_W

        for hour in range(8760):
            # cooling towers
            # AHU
            if config.disconnected.AHUflag:

                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_AHU_W[hour], CT_VCC_to_AHU_nom_size_W)
                result_AHU[1][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_AHU[1][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU[1][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_single_ACH_to_AHU_W[hour], CT_single_ACH_to_AHU_nom_size_W)
                result_AHU[2][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_AHU[2][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU[2][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_double_ACH_to_AHU_W[hour], CT_double_ACH_to_AHU_nom_size_W)
                result_AHU[3][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_AHU[3][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU[3][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # ARU
            if config.disconnected.ARUflag:

                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_ARU_W[hour], CT_VCC_to_ARU_nom_size_W)
                result_ARU[1][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_ARU[1][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_ARU[1][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_single_ACH_to_ARU_W[hour], CT_single_ACH_to_ARU_nom_size_W)
                result_ARU[2][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_ARU[2][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_ARU[2][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_double_ACH_to_ARU_W[hour], CT_double_ACH_to_ARU_nom_size_W)
                result_ARU[3][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_ARU[3][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_ARU[3][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # SCU
            if config.disconnected.SCUflag:

                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_SCU_W[hour], CT_VCC_to_SCU_nom_size_W)
                result_SCU[1][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_SCU[1][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_SCU[1][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_single_ACH_to_SCU_W[hour], CT_single_ACH_to_SCU_nom_size_W)
                result_SCU[2][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_SCU[2][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_SCU[2][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_double_ACH_to_SCU_W[hour], CT_double_ACH_to_SCU_nom_size_W)
                result_SCU[3][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_SCU[3][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_SCU[3][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # AHU+ARU
            if config.disconnected.AHUARUflag:

                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_AHU_ARU_W[hour], CT_VCC_to_AHU_ARU_nom_size_W)
                result_AHU_ARU[1][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_AHU_ARU[1][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_ARU[1][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_single_ACH_to_AHU_ARU_W[hour], CT_single_ACH_to_AHU_ARU_nom_size_W)
                result_AHU_ARU[2][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_AHU_ARU[2][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_ARU[2][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_double_ACH_to_AHU_ARU_W[hour], CT_double_ACH_to_AHU_ARU_nom_size_W)
                result_AHU_ARU[3][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_AHU_ARU[3][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_ARU[3][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # AHU+SCU
            if config.disconnected.AHUSCUflag:

                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_AHU_SCU_W[hour], CT_VCC_to_AHU_SCU_nom_size_W)
                result_AHU_SCU[1][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_AHU_SCU[1][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_SCU[1][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_single_ACH_to_AHU_SCU_W[hour], CT_single_ACH_to_AHU_SCU_nom_size_W)
                result_AHU_SCU[2][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_AHU_SCU[2][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_SCU[2][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_double_ACH_to_AHU_SCU_W[hour], CT_double_ACH_to_AHU_SCU_nom_size_W)
                result_AHU_SCU[3][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_AHU_SCU[3][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_SCU[3][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # ARU+SCU
            if config.disconnected.ARUSCUflag:

                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_ARU_SCU_W[hour], CT_VCC_to_ARU_SCU_nom_size_W)
                result_ARU_SCU[1][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_ARU_SCU[1][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_ARU_SCU[1][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_single_ACH_to_ARU_SCU_W[hour], CT_single_ACH_to_ARU_SCU_nom_size_W)
                result_ARU_SCU[2][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_ARU_SCU[2][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_ARU_SCU[2][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_double_ACH_to_ARU_SCU_W[hour], CT_double_ACH_to_ARU_SCU_nom_size_W)
                result_ARU_SCU[3][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_ARU_SCU[3][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_ARU_SCU[3][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # AHU+ARU+SCU
            if config.disconnected.AHUARUSCUflag:

                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_AHU_ARU_SCU_W[hour], CT_VCC_to_AHU_ARU_SCU_nom_size_W)
                result_AHU_ARU_SCU[1][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_AHU_ARU_SCU[1][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[1][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_single_ACH_to_AHU_ARU_SCU_W[hour], CT_single_ACH_to_AHU_ARU_SCU_nom_size_W)
                result_AHU_ARU_SCU[2][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_AHU_ARU_SCU[2][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[2][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_double_ACH_to_AHU_ARU_SCU_W[hour], CT_double_ACH_to_AHU_ARU_SCU_nom_size_W)
                result_AHU_ARU_SCU[3][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_AHU_ARU_SCU[3][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[3][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_AHU_ARU_and_VCC_to_SCU_W[hour], CT_VCC_to_AHU_ARU_and_VCC_to_SCU_nom_size_W)
                result_AHU_ARU_SCU[4][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_AHU_ARU_SCU[4][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[4][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_AHU_ARU_and_single_ACH_to_SCU_W[hour], CT_VCC_to_AHU_ARU_and_single_ACH_to_SCU_nom_size_W)
                result_AHU_ARU_SCU[5][7] += prices.ELEC_PRICE * wdot_W  # CHF
                result_AHU_ARU_SCU[5][8] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[5][9] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # Boilers
            # AHU
            if config.disconnected.AHUflag:

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_single_ACH_to_AHU_W[hour], boiler_single_ACH_to_AHU_nom_size_W,
                                                    T_re_boiler_single_ACH_to_AHU_K[hour]) if q_boiler_single_ACH_to_AHU_W[hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_single_ACH_to_AHU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_AHU[2][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_AHU[2][8] += (NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_AHU[2][9] += (NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_double_ACH_to_AHU_W[hour], boiler_double_ACH_to_AHU_nom_size_W,
                                                    T_re_boiler_double_ACH_to_AHU_K[hour]) if q_boiler_double_ACH_to_AHU_W[hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_double_ACH_to_AHU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_AHU[3][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_AHU[3][8] += (NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_AHU[3][9] += (NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

            # ARU
            if config.disconnected.ARUflag:

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_single_ACH_to_ARU_W[hour], boiler_single_ACH_to_ARU_nom_size_W,
                                                    T_re_boiler_single_ACH_to_ARU_K[hour]) if q_boiler_single_ACH_to_ARU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_single_ACH_to_ARU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_ARU[2][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_ARU[2][8] += (NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_ARU[2][9] += (NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_double_ACH_to_ARU_W[hour], boiler_double_ACH_to_ARU_nom_size_W,
                                                    T_re_boiler_double_ACH_to_ARU_K[hour]) if q_boiler_double_ACH_to_ARU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_double_ACH_to_ARU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_ARU[3][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_ARU[3][8] += (NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_ARU[3][9] += (NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq


            # SCU
            if config.disconnected.SCUflag:

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_single_ACH_to_SCU_W[hour], boiler_single_ACH_to_SCU_nom_size_W,
                                                    T_re_boiler_single_ACH_to_SCU_K[hour]) if q_boiler_single_ACH_to_SCU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_single_ACH_to_SCU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_SCU[2][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_SCU[2][8] += (NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_SCU[2][9] += (NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_double_ACH_to_SCU_W[hour], boiler_double_ACH_to_SCU_nom_size_W,
                                                    T_re_boiler_double_ACH_to_SCU_K[hour]) if q_boiler_double_ACH_to_SCU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_double_ACH_to_SCU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_SCU[3][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_SCU[3][8] += (NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_SCU[3][9] += (NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

            # AHU + ARU
            if config.disconnected.AHUARUflag:

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_single_ACH_to_AHU_ARU_W[hour], boiler_single_ACH_to_AHU_ARU_nom_size_W,
                                                    T_re_boiler_single_ACH_to_AHU_ARU_K[hour]) if q_boiler_single_ACH_to_AHU_ARU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_single_ACH_to_AHU_ARU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_AHU_ARU[2][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_AHU_ARU[2][8] += (NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_AHU_ARU[2][9] += (NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_double_ACH_to_AHU_ARU_W[hour], boiler_double_ACH_to_AHU_ARU_nom_size_W,
                                                    T_re_boiler_double_ACH_to_AHU_ARU_K[hour]) if q_boiler_double_ACH_to_AHU_ARU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_double_ACH_to_AHU_ARU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_AHU_ARU[3][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_AHU_ARU[3][8] += (NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_AHU_ARU[3][9] += (NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq
            
            
            # AHU + SCU
            if config.disconnected.AHUSCUflag:

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_single_ACH_to_AHU_SCU_W[hour], boiler_single_ACH_to_AHU_SCU_nom_size_W,
                                                    T_re_boiler_single_ACH_to_AHU_SCU_K[hour]) if q_boiler_single_ACH_to_AHU_SCU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_single_ACH_to_AHU_SCU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_AHU_SCU[2][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_AHU_SCU[2][8] += (NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_AHU_SCU[2][9] += (NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_double_ACH_to_AHU_SCU_W[hour], boiler_double_ACH_to_AHU_SCU_nom_size_W,
                                                    T_re_boiler_double_ACH_to_AHU_SCU_K[hour]) if q_boiler_double_ACH_to_AHU_SCU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_double_ACH_to_AHU_SCU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_AHU_SCU[3][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_AHU_SCU[3][8] += (NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_AHU_SCU[3][9] += (NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq
            
            # ARU + SCU
            if config.disconnected.ARUSCUflag:

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_single_ACH_to_ARU_SCU_W[hour], boiler_single_ACH_to_ARU_SCU_nom_size_W,
                                                    T_re_boiler_single_ACH_to_ARU_SCU_K[hour]) if q_boiler_single_ACH_to_ARU_SCU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_single_ACH_to_ARU_SCU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_ARU_SCU[2][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_ARU_SCU[2][8] += (NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_ARU_SCU[2][9] += (NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_double_ACH_to_ARU_SCU_W[hour], boiler_double_ACH_to_ARU_SCU_nom_size_W,
                                                    T_re_boiler_double_ACH_to_ARU_SCU_K[hour]) if q_boiler_double_ACH_to_ARU_SCU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_double_ACH_to_ARU_SCU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_ARU_SCU[3][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_ARU_SCU[3][8] += (NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_ARU_SCU[3][9] += (NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq
            
            # AHU + ARU + SCU
            if config.disconnected.AHUARUSCUflag:

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_single_ACH_to_AHU_ARU_SCU_W[hour], boiler_single_ACH_to_AHU_ARU_SCU_nom_size_W,
                                                    T_re_boiler_single_ACH_to_AHU_ARU_SCU_K[hour]) if q_boiler_single_ACH_to_AHU_ARU_SCU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_single_ACH_to_AHU_ARU_SCU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_AHU_ARU_SCU[2][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_AHU_ARU_SCU[2][8] += (NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[2][9] += (NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_double_ACH_to_AHU_ARU_SCU_W[hour], boiler_double_ACH_to_AHU_ARU_SCU_nom_size_W,
                                                    T_re_boiler_double_ACH_to_AHU_ARU_SCU_K[hour]) if q_boiler_double_ACH_to_AHU_ARU_SCU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_double_ACH_to_AHU_ARU_SCU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_AHU_ARU_SCU[3][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_AHU_ARU_SCU[3][8] += (NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[3][9] += (NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

                # VCC to AHU + ARU and single effect ACH to SCU
                boiler_eff = boiler.calc_Cop_boiler(q_boiler_VCC_to_AHU_ARU_and_single_ACH_to_SCU_W[hour], boiler_VCC_to_AHU_ARU_and_single_ACH_to_SCU_nom_size_W,
                                                    T_re_boiler_VCC_to_AHU_ARU_and_single_ACH_to_SCU_K[hour]) if q_boiler_VCC_to_AHU_ARU_and_single_ACH_to_SCU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_VCC_to_AHU_ARU_and_single_ACH_to_SCU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_AHU_ARU_SCU[5][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_AHU_ARU_SCU[5][8] += (NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[5][9] += (NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq
            
        ## Calculate Capex/Opex
        # AHU
        Inv_Costs_AHU = np.zeros((4, 1))
        if config.disconnected.AHUflag:

            Inv_Costs_AHU[0][0] = 1E10  # FIXME: a dummy value to rule out this configuration

            Capex_a_VCC, Opex_VCC = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_AHU_W, locator, config, technology=1)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_VCC_to_AHU_nom_size_W, locator, config, technology=0)
            Inv_Costs_AHU[1][0] = Capex_a_CT + Opex_CT + Capex_a_VCC + Opex_VCC

            Capex_a_ACH, Opex_ACH = chiller_absorption.calc_Cinv(Qc_nom_combination_AHU_W, locator, ACH_type_single, config)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_single_ACH_to_AHU_nom_size_W, locator, config, technology=0)
            Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_single_ACH_to_AHU_nom_size_W, locator, config, technology=0)
            Inv_Costs_AHU[2][0] = Capex_a_CT + Opex_CT + \
                             Capex_a_ACH + Opex_ACH + Capex_a_boiler + Opex_boiler + Capex_a_SC_FP + Opex_SC_FP

            Capex_a_ACH, Opex_ACH = chiller_absorption.calc_Cinv(Qc_nom_combination_AHU_W, locator, ACH_type_double, config)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_double_ACH_to_AHU_nom_size_W, locator, config, technology=0)
            Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_double_ACH_to_AHU_nom_size_W, locator, config, technology=0)
            Inv_Costs_AHU[3][0] = Capex_a_CT + Opex_CT + \
                             Capex_a_ACH + Opex_ACH + Capex_a_boiler + Opex_boiler + Capex_a_SC_FP + Opex_SC_FP

        # ARU
        Inv_Costs_ARU = np.zeros((4, 1))
        if config.disconnected.ARUflag:

            Inv_Costs_ARU[0][0] = 1E10  # FIXME: a dummy value to rule out this configuration

            Capex_a_VCC, Opex_VCC = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_ARU_W, locator, config, technology=1)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_VCC_to_ARU_nom_size_W, locator, config, technology=0)
            Inv_Costs_ARU[1][0] = Capex_a_CT + Opex_CT + Capex_a_VCC + Opex_VCC

            Capex_a_ACH, Opex_ACH = chiller_absorption.calc_Cinv(Qc_nom_combination_ARU_W, locator, ACH_type_single, config)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_single_ACH_to_ARU_nom_size_W, locator, config, technology=0)
            Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_single_ACH_to_ARU_nom_size_W, locator, config, technology=0)
            Inv_Costs_ARU[2][0] = Capex_a_CT + Opex_CT + \
                             Capex_a_ACH + Opex_ACH + Capex_a_boiler + Opex_boiler + Capex_a_SC_FP + Opex_SC_FP

            Capex_a_ACH, Opex_ACH = chiller_absorption.calc_Cinv(Qc_nom_combination_ARU_W, locator, ACH_type_double, config)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_double_ACH_to_ARU_nom_size_W, locator, config, technology=0)
            Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_double_ACH_to_ARU_nom_size_W, locator, config, technology=0)
            Inv_Costs_ARU[3][0] = Capex_a_CT + Opex_CT + \
                             Capex_a_ACH + Opex_ACH + Capex_a_boiler + Opex_boiler + Capex_a_SC_FP + Opex_SC_FP

        # SCU
        Inv_Costs_SCU = np.zeros((4, 1))
        if config.disconnected.SCUflag:

            Inv_Costs_SCU[0][0] = 1E10  # FIXME: a dummy value to rule out this configuration

            Capex_a_VCC, Opex_VCC = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_SCU_W, locator, config, technology=1)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_VCC_to_SCU_nom_size_W, locator, config, technology=0)
            Inv_Costs_SCU[1][0] = Capex_a_CT + Opex_CT + Capex_a_VCC + Opex_VCC

            Capex_a_ACH, Opex_ACH = chiller_absorption.calc_Cinv(Qc_nom_combination_SCU_W, locator, ACH_type_single, config)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_single_ACH_to_SCU_nom_size_W, locator, config, technology=0)
            Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_single_ACH_to_SCU_nom_size_W, locator, config, technology=0)
            Inv_Costs_SCU[2][0] = Capex_a_CT + Opex_CT + \
                             Capex_a_ACH + Opex_ACH + Capex_a_boiler + Opex_boiler + Capex_a_SC_FP + Opex_SC_FP

            Capex_a_ACH, Opex_ACH = chiller_absorption.calc_Cinv(Qc_nom_combination_SCU_W, locator, ACH_type_double, config)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_double_ACH_to_SCU_nom_size_W, locator, config, technology=0)
            Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_double_ACH_to_SCU_nom_size_W, locator, config, technology=0)
            Inv_Costs_SCU[3][0] = Capex_a_CT + Opex_CT + \
                             Capex_a_ACH + Opex_ACH + Capex_a_boiler + Opex_boiler + Capex_a_SC_FP + Opex_SC_FP

        # AHU + ARU
        Inv_Costs_AHU_ARU = np.zeros((4, 1))
        if config.disconnected.AHUARUflag:

            Inv_Costs_AHU_ARU[0][0] = 1E10  # FIXME: a dummy value to rule out this configuration

            Capex_a_VCC, Opex_VCC = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_AHU_ARU_W, locator, config, technology=1)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_VCC_to_AHU_ARU_nom_size_W, locator, config, technology=0)
            Inv_Costs_AHU_ARU[1][0] = Capex_a_CT + Opex_CT + Capex_a_VCC + Opex_VCC

            Capex_a_ACH, Opex_ACH = chiller_absorption.calc_Cinv(Qc_nom_combination_AHU_ARU_W, locator, ACH_type_single, config)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_single_ACH_to_AHU_ARU_nom_size_W, locator, config, technology=0)
            Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_single_ACH_to_AHU_ARU_nom_size_W, locator, config, technology=0)
            Inv_Costs_AHU_ARU[2][0] = Capex_a_CT + Opex_CT + \
                             Capex_a_ACH + Opex_ACH + Capex_a_boiler + Opex_boiler + Capex_a_SC_FP + Opex_SC_FP

            Capex_a_ACH, Opex_ACH = chiller_absorption.calc_Cinv(Qc_nom_combination_AHU_ARU_W, locator, ACH_type_double, config)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_double_ACH_to_AHU_ARU_nom_size_W, locator, config, technology=0)
            Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_double_ACH_to_AHU_ARU_nom_size_W, locator, config, technology=0)
            Inv_Costs_AHU_ARU[3][0] = Capex_a_CT + Opex_CT + \
                             Capex_a_ACH + Opex_ACH + Capex_a_boiler + Opex_boiler + Capex_a_SC_FP + Opex_SC_FP

        # AHU + SCU
        Inv_Costs_AHU_SCU = np.zeros((4, 1))
        if config.disconnected.AHUSCUflag:

            Inv_Costs_AHU_SCU[0][0] = 1E10  # FIXME: a dummy value to rule out this configuration

            Capex_a_VCC, Opex_VCC = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_AHU_SCU_W, locator, config, technology=1)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_VCC_to_AHU_SCU_nom_size_W, locator, config, technology=0)
            Inv_Costs_AHU_SCU[1][0] = Capex_a_CT + Opex_CT + Capex_a_VCC + Opex_VCC

            Capex_a_ACH, Opex_ACH = chiller_absorption.calc_Cinv(Qc_nom_combination_AHU_SCU_W, locator, ACH_type_single, config)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_single_ACH_to_AHU_SCU_nom_size_W, locator, config, technology=0)
            Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_single_ACH_to_AHU_SCU_nom_size_W, locator, config, technology=0)
            Inv_Costs_AHU_SCU[2][0] = Capex_a_CT + Opex_CT + \
                             Capex_a_ACH + Opex_ACH + Capex_a_boiler + Opex_boiler + Capex_a_SC_FP + Opex_SC_FP

            Capex_a_ACH, Opex_ACH = chiller_absorption.calc_Cinv(Qc_nom_combination_AHU_SCU_W, locator, ACH_type_double, config)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_double_ACH_to_AHU_SCU_nom_size_W, locator, config, technology=0)
            Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_double_ACH_to_AHU_SCU_nom_size_W, locator, config, technology=0)
            Inv_Costs_AHU_SCU[3][0] = Capex_a_CT + Opex_CT + \
                             Capex_a_ACH + Opex_ACH + Capex_a_boiler + Opex_boiler + Capex_a_SC_FP + Opex_SC_FP

        # ARU + SCU
        Inv_Costs_ARU_SCU = np.zeros((4, 1))
        if config.disconnected.ARUSCUflag:

            Inv_Costs_ARU_SCU[0][0] = 1E10  # FIXME: a dummy value to rule out this configuration

            Capex_a_VCC, Opex_VCC = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_ARU_SCU_W, locator, config, technology=1)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_VCC_to_ARU_SCU_nom_size_W, locator, config, technology=0)
            Inv_Costs_ARU_SCU[1][0] = Capex_a_CT + Opex_CT + Capex_a_VCC + Opex_VCC

            Capex_a_ACH, Opex_ACH = chiller_absorption.calc_Cinv(Qc_nom_combination_ARU_SCU_W, locator, ACH_type_single, config)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_single_ACH_to_ARU_SCU_nom_size_W, locator, config, technology=0)
            Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_single_ACH_to_ARU_SCU_nom_size_W, locator, config, technology=0)
            Inv_Costs_ARU_SCU[2][0] = Capex_a_CT + Opex_CT + \
                             Capex_a_ACH + Opex_ACH + Capex_a_boiler + Opex_boiler + Capex_a_SC_FP + Opex_SC_FP

            Capex_a_ACH, Opex_ACH = chiller_absorption.calc_Cinv(Qc_nom_combination_ARU_SCU_W, locator, ACH_type_double, config)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_double_ACH_to_ARU_SCU_nom_size_W, locator, config, technology=0)
            Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_double_ACH_to_ARU_SCU_nom_size_W, locator, config, technology=0)
            Inv_Costs_ARU_SCU[3][0] = Capex_a_CT + Opex_CT + \
                             Capex_a_ACH + Opex_ACH + Capex_a_boiler + Opex_boiler + Capex_a_SC_FP + Opex_SC_FP

        # AHU + ARU + SCU
        Inv_Costs_AHU_ARU_SCU = np.zeros((6, 1))
        if config.disconnected.AHUARUSCUflag:

            Inv_Costs_AHU_ARU_SCU[0][0] = 1E10  # FIXME: a dummy value to rule out this configuration

            # VCC + CT
            Capex_a_VCC, Opex_VCC = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_AHU_ARU_SCU_W, locator, config, technology=1)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_VCC_to_AHU_ARU_SCU_nom_size_W, locator, config, technology=0)
            Inv_Costs_AHU_ARU_SCU[1][0] = Capex_a_CT + Opex_CT + Capex_a_VCC + Opex_VCC

            # single effect ACH + CT + Boiler + SC_FP
            Capex_a_ACH, Opex_ACH = chiller_absorption.calc_Cinv(Qc_nom_combination_AHU_ARU_SCU_W, locator, ACH_type_single, config)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_single_ACH_to_AHU_ARU_SCU_nom_size_W, locator, config, technology=0)
            Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_single_ACH_to_AHU_ARU_SCU_nom_size_W, locator, config, technology=0)
            Inv_Costs_AHU_ARU_SCU[2][0] = Capex_a_CT + Opex_CT + \
                             Capex_a_ACH + Opex_ACH + Capex_a_boiler + Opex_boiler + Capex_a_SC_FP + Opex_SC_FP

            # double effect ACH + CT + Boiler + SC_ET
            Capex_a_ACH, Opex_ACH = chiller_absorption.calc_Cinv(Qc_nom_combination_AHU_ARU_SCU_W, locator, ACH_type_double, config)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_double_ACH_to_AHU_ARU_SCU_nom_size_W, locator, config, technology=0)
            Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_double_ACH_to_ARU_SCU_nom_size_W, locator, config, technology=0)
            Inv_Costs_AHU_ARU_SCU[3][0] = Capex_a_CT + Opex_CT + \
                             Capex_a_ACH + Opex_ACH + Capex_a_boiler + Opex_boiler + Capex_a_SC_FP + Opex_SC_FP


            # VCC (AHU + ARU) + VCC (SCU) + CT
            Capex_a_VCC_AA, Opex_VCC_AA = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_AHU_ARU_W, locator, config,
                                                                                  technology=1)
            Capex_a_VCC_S, Opex_VCC_S = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_SCU_W, locator, config,
                                                                                technology=1)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_VCC_to_AHU_ARU_and_VCC_to_SCU_nom_size_W, locator, config, technology=0)
            Inv_Costs_AHU_ARU_SCU[4][0] = Capex_a_CT + Opex_CT + Capex_a_VCC_AA + Capex_a_VCC_S + Opex_VCC_AA + Opex_VCC_S

            # VCC (AHU + ARU) + ACH (SCU) + CT + Boiler + SC_FP
            Capex_a_ACH_S, Opex_ACH_S = chiller_absorption.calc_Cinv(Qc_nom_combination_SCU_W, locator, ACH_type_single, config)
            Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_VCC_to_AHU_ARU_and_single_ACH_to_SCU_nom_size_W, locator, config, technology=0)
            Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_VCC_to_AHU_ARU_and_single_ACH_to_SCU_nom_size_W, locator, config, technology=0)
            Capex_a_SC_FP, Opex_SC_FP = solar_collector.calc_Cinv_SC(SC_FP_data['Area_SC_m2'][0], locator, config,
                                                                     technology=0)
            Inv_Costs_AHU_ARU_SCU[5][0] = Capex_a_CT + Opex_CT + Capex_a_VCC_AA + Opex_VCC_AA + \
                             Capex_a_ACH_S + Opex_ACH_S + Capex_a_boiler + Opex_boiler + Capex_a_SC_FP + Opex_SC_FP


        # Best configuration AHU
        number_config = len(result_AHU)
        Best = np.zeros((number_config, 1))
        indexBest = 0

        # write all results from the configurations into TotalCosts, TotalCO2, TotalPrim
        TotalCosts = np.zeros((number_config, 2))
        TotalCO2 = np.zeros((number_config, 2))
        TotalPrim = np.zeros((number_config, 2))

        for i in range(number_config):
            TotalCosts[i][0] = TotalCO2[i][0] = TotalPrim[i][0] = i
            TotalCosts[i][1] = Inv_Costs_AHU[i][0] + result_AHU[i][7]
            TotalCO2[i][1] = result_AHU[i][8]
            TotalPrim[i][1] = result_AHU[i][9]

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

        dico["DX Share"] = result_AHU[:, 0]
        dico["VCC_to_AHU Share"] = result_AHU[:, 1]
        dico["single effect ACH_to_AHU Share"] = result_AHU[:, 2]
        dico["double effect ACH_to_AHU Share"] = result_AHU[:, 3]

        # performance indicators of the configurations
        dico["Operation Costs [CHF]"] = result_AHU[:, 7]
        dico["CO2 Emissions [kgCO2-eq]"] = result_AHU[:, 8]
        dico["Primary Energy Needs [MJoil-eq]"] = result_AHU[:, 9]
        dico["Annualized Investment Costs [CHF]"] = Inv_Costs_AHU[:, 0]
        dico["Total Costs [CHF]"] = TotalCosts[:, 1]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power DX"] = result_AHU[:, 0] * Qc_nom_combination_AHU_W
        dico["Nominal Power VCC"] = result_AHU[:, 1] * Qc_nom_combination_AHU_W
        dico["Nominal Power single-effect ACH_to_AAS"] = result_AHU[:, 2] * Qc_nom_combination_AHU_W
        dico["Nominal Power double-effect ACH_to_AAS"] = result_AHU[:, 3] * Qc_nom_combination_AHU_W


        dico_df = pd.DataFrame(dico)
        fName = locator.get_optimization_disconnected_folder_building_result_cooling(building_name, 'AHU')
        dico_df.to_csv(fName, sep=',')

        # Best configuration ARU
        number_config = len(result_ARU)
        Best = np.zeros((number_config, 1))
        indexBest = 0

        # write all results from the configurations into TotalCosts, TotalCO2, TotalPrim
        TotalCosts = np.zeros((number_config, 2))
        TotalCO2 = np.zeros((number_config, 2))
        TotalPrim = np.zeros((number_config, 2))

        for i in range(number_config):
            TotalCosts[i][0] = TotalCO2[i][0] = TotalPrim[i][0] = i
            TotalCosts[i][1] = Inv_Costs_ARU[i][0] + result_ARU[i][7]
            TotalCO2[i][1] = result_ARU[i][8]
            TotalPrim[i][1] = result_ARU[i][9]

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

        dico["DX Share"] = result_ARU[:, 0]
        dico["VCC_to_ARU Share"] = result_ARU[:, 1]
        dico["single effect ACH_to_ARU Share"] = result_ARU[:, 2]
        dico["double effect ACH_to_ARU Share"] = result_ARU[:, 3]

        # performance indicators of the configurations
        dico["Operation Costs [CHF]"] = result_ARU[:, 7]
        dico["CO2 Emissions [kgCO2-eq]"] = result_ARU[:, 8]
        dico["Primary Energy Needs [MJoil-eq]"] = result_ARU[:, 9]
        dico["Annualized Investment Costs [CHF]"] = Inv_Costs_ARU[:, 0]
        dico["Total Costs [CHF]"] = TotalCosts[:, 1]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power DX"] = result_ARU[:, 0] * Qc_nom_combination_ARU_W
        dico["Nominal Power VCC"] = result_ARU[:, 1] * Qc_nom_combination_ARU_W
        dico["Nominal Power single-effect ACH"] = result_ARU[:, 2] * Qc_nom_combination_ARU_W
        dico["Nominal Power double-effect ACH"] = result_ARU[:, 3] * Qc_nom_combination_ARU_W

        dico_df = pd.DataFrame(dico)
        fName = locator.get_optimization_disconnected_folder_building_result_cooling(building_name, 'ARU')
        dico_df.to_csv(fName, sep=',')

        # Best configuration SCU
        number_config = len(result_SCU)
        Best = np.zeros((number_config, 1))
        indexBest = 0

        # write all results from the configurations into TotalCosts, TotalCO2, TotalPrim
        TotalCosts = np.zeros((number_config, 2))
        TotalCO2 = np.zeros((number_config, 2))
        TotalPrim = np.zeros((number_config, 2))

        for i in range(number_config):
            TotalCosts[i][0] = TotalCO2[i][0] = TotalPrim[i][0] = i
            TotalCosts[i][1] = Inv_Costs_SCU[i][0] + result_SCU[i][7]
            TotalCO2[i][1] = result_SCU[i][8]
            TotalPrim[i][1] = result_SCU[i][9]

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

        dico["DX Share"] = result_SCU[:, 0]
        dico["VCC_to_SCU Share"] = result_SCU[:, 1]
        dico["single effect ACH_to_SCU Share"] = result_SCU[:, 2]
        dico["double effect ACH_to_SCU Share"] = result_SCU[:, 3]

        # performance indicators of the configurations
        dico["Operation Costs [CHF]"] = result_SCU[:, 7]
        dico["CO2 Emissions [kgCO2-eq]"] = result_SCU[:, 8]
        dico["Primary Energy Needs [MJoil-eq]"] = result_SCU[:, 9]
        dico["Annualized Investment Costs [CHF]"] = Inv_Costs_SCU[:, 0]
        dico["Total Costs [CHF]"] = TotalCosts[:, 1]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power DX"] = result_SCU[:, 0] * Qc_nom_combination_SCU_W
        dico["Nominal Power VCC"] = result_SCU[:, 1] * Qc_nom_combination_SCU_W
        dico["Nominal Power single-effect ACH"] = result_SCU[:, 2] * Qc_nom_combination_SCU_W
        dico["Nominal Power double-effect ACH"] = result_SCU[:, 3] * Qc_nom_combination_SCU_W

        dico_df = pd.DataFrame(dico)
        fName = locator.get_optimization_disconnected_folder_building_result_cooling(building_name, 'SCU')
        dico_df.to_csv(fName, sep=',')

        # Best configuration AHU + ARU
        number_config = len(result_AHU_ARU)
        Best = np.zeros((number_config, 1))
        indexBest = 0

        # write all results from the configurations into TotalCosts, TotalCO2, TotalPrim
        TotalCosts = np.zeros((number_config, 2))
        TotalCO2 = np.zeros((number_config, 2))
        TotalPrim = np.zeros((number_config, 2))

        for i in range(number_config):
            TotalCosts[i][0] = TotalCO2[i][0] = TotalPrim[i][0] = i
            TotalCosts[i][1] = Inv_Costs_AHU_ARU[i][0] + result_AHU_ARU[i][7]
            TotalCO2[i][1] = result_AHU_ARU[i][8]
            TotalPrim[i][1] = result_AHU_ARU[i][9]

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

        dico["DX Share"] = result_AHU_ARU[:, 0]
        dico["VCC_to_AHU_ARU Share"] = result_AHU_ARU[:, 1]
        dico["single effect ACH_to_AHU_ARU Share"] = result_AHU_ARU[:, 2]
        dico["double effect ACH_to_AHU_ARU Share"] = result_AHU_ARU[:, 3]

        # performance indicators of the configurations
        dico["Operation Costs [CHF]"] = result_AHU_ARU[:, 7]
        dico["CO2 Emissions [kgCO2-eq]"] = result_AHU_ARU[:, 8]
        dico["Primary Energy Needs [MJoil-eq]"] = result_AHU_ARU[:, 9]
        dico["Annualized Investment Costs [CHF]"] = Inv_Costs_AHU_ARU[:, 0]
        dico["Total Costs [CHF]"] = TotalCosts[:, 1]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power DX"] = result_AHU_ARU[:, 0] * Qc_nom_combination_AHU_ARU_W
        dico["Nominal Power VCC"] = result_AHU_ARU[:, 1] * Qc_nom_combination_AHU_ARU_W
        dico["Nominal Power single-effect ACH"] = result_AHU_ARU[:, 2] * Qc_nom_combination_AHU_ARU_W
        dico["Nominal Power double-effect ACH"] = result_AHU_ARU[:, 3] * Qc_nom_combination_AHU_ARU_W

        dico_df = pd.DataFrame(dico)
        fName = locator.get_optimization_disconnected_folder_building_result_cooling(building_name, 'AHU_ARU')
        dico_df.to_csv(fName, sep=',')

        # Best configuration AHU + SCU
        number_config = len(result_AHU_SCU)
        Best = np.zeros((number_config, 1))
        indexBest = 0

        # write all results from the configurations into TotalCosts, TotalCO2, TotalPrim
        TotalCosts = np.zeros((number_config, 2))
        TotalCO2 = np.zeros((number_config, 2))
        TotalPrim = np.zeros((number_config, 2))

        for i in range(number_config):
            TotalCosts[i][0] = TotalCO2[i][0] = TotalPrim[i][0] = i
            TotalCosts[i][1] = Inv_Costs_AHU_SCU[i][0] + result_AHU_SCU[i][7]
            TotalCO2[i][1] = result_AHU_SCU[i][8]
            TotalPrim[i][1] = result_AHU_SCU[i][9]

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

        dico["DX Share"] = result_AHU_SCU[:, 0]
        dico["VCC_to_AHU_SCU Share"] = result_AHU_SCU[:, 1]
        dico["single effect ACH_to_AHU_SCU Share"] = result_AHU_SCU[:, 2]
        dico["double effect ACH_to_AHU_SCU Share"] = result_AHU_SCU[:, 3]

        # performance indicators of the configurations
        dico["Operation Costs [CHF]"] = result_AHU_SCU[:, 7]
        dico["CO2 Emissions [kgCO2-eq]"] = result_AHU_SCU[:, 8]
        dico["Primary Energy Needs [MJoil-eq]"] = result_AHU_SCU[:, 9]
        dico["Annualized Investment Costs [CHF]"] = Inv_Costs_AHU_SCU[:, 0]
        dico["Total Costs [CHF]"] = TotalCosts[:, 1]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power DX"] = result_AHU_SCU[:, 0] * Qc_nom_combination_AHU_SCU_W
        dico["Nominal Power VCC"] = result_AHU_SCU[:, 1] * Qc_nom_combination_AHU_SCU_W
        dico["Nominal Power single-effect ACH_to_AAS"] = result_AHU_SCU[:, 2] * Qc_nom_combination_AHU_SCU_W
        dico["Nominal Power double-effect ACH_to_AAS"] = result_AHU_SCU[:, 3] * Qc_nom_combination_AHU_SCU_W

        dico_df = pd.DataFrame(dico)
        fName = locator.get_optimization_disconnected_folder_building_result_cooling(building_name, 'AHU_SCU')
        dico_df.to_csv(fName, sep=',')

        # Best configuration ARU + SCU
        number_config = len(result_ARU_SCU)
        Best = np.zeros((number_config, 1))
        indexBest = 0

        # write all results from the configurations into TotalCosts, TotalCO2, TotalPrim
        TotalCosts = np.zeros((number_config, 2))
        TotalCO2 = np.zeros((number_config, 2))
        TotalPrim = np.zeros((number_config, 2))

        for i in range(number_config):
            TotalCosts[i][0] = TotalCO2[i][0] = TotalPrim[i][0] = i
            TotalCosts[i][1] = Inv_Costs_ARU_SCU[i][0] + result_ARU_SCU[i][7]
            TotalCO2[i][1] = result_ARU_SCU[i][8]
            TotalPrim[i][1] = result_ARU_SCU[i][9]

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

        dico["DX Share"] = result_ARU_SCU[:, 0]
        dico["VCC_to_ARU_SCU Share"] = result_ARU_SCU[:, 1]
        dico["single effect ACH_to_ARU_SCU Share"] = result_ARU_SCU[:, 2]
        dico["double effect ACH_to_ARU_SCU Share"] = result_ARU_SCU[:, 3]

        # performance indicators of the configurations
        dico["Operation Costs [CHF]"] = result_ARU_SCU[:, 7]
        dico["CO2 Emissions [kgCO2-eq]"] = result_ARU_SCU[:, 8]
        dico["Primary Energy Needs [MJoil-eq]"] = result_ARU_SCU[:, 9]
        dico["Annualized Investment Costs [CHF]"] = Inv_Costs_ARU_SCU[:, 0]
        dico["Total Costs [CHF]"] = TotalCosts[:, 1]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power DX"] = result_ARU_SCU[:, 0] * Qc_nom_combination_ARU_SCU_W
        dico["Nominal Power VCC"] = result_ARU_SCU[:, 1] * Qc_nom_combination_ARU_SCU_W
        dico["Nominal Power single-effect ACH"] = result_ARU_SCU[:, 2] * Qc_nom_combination_ARU_SCU_W
        dico["Nominal Power double-effect ACH"] = result_ARU_SCU[:, 3] * Qc_nom_combination_ARU_SCU_W

        dico_df = pd.DataFrame(dico)
        fName = locator.get_optimization_disconnected_folder_building_result_cooling(building_name, 'ARU_SCU')
        dico_df.to_csv(fName, sep=',')

        # Best configuration AHU + ARU + SCU
        number_config = len(result_AHU_ARU_SCU)
        Best = np.zeros((number_config, 1))
        indexBest = 0

        # write all results from the configurations into TotalCosts, TotalCO2, TotalPrim
        TotalCosts = np.zeros((number_config, 2))
        TotalCO2 = np.zeros((number_config, 2))
        TotalPrim = np.zeros((number_config, 2))

        for i in range(number_config):
            TotalCosts[i][0] = TotalCO2[i][0] = TotalPrim[i][0] = i
            TotalCosts[i][1] = Inv_Costs_AHU_ARU_SCU[i][0] + result_AHU_ARU_SCU[i][7]
            TotalCO2[i][1] = result_AHU_ARU_SCU[i][8]
            TotalPrim[i][1] = result_AHU_ARU_SCU[i][9]

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

        dico["DX Share"] = result_AHU_ARU_SCU[:, 0]
        dico["VCC_to_AHU_ARU_SCU Share"] = result_AHU_ARU_SCU[:, 1]
        dico["single effect ACH_to_ARU_SCU Share"] = result_AHU_ARU_SCU[:, 2]
        dico["double effect ACH_to_ARU_SCU Share"] = result_AHU_ARU_SCU[:, 3]
        dico["VCC_to_AHU_ARU Share"] = result_AHU_ARU_SCU[:, 4]
        dico["VCC_to_SCU Share"] = result_AHU_ARU_SCU[:,5]
        dico["ACH_to_SCU Share"] = result_AHU_ARU_SCU[:,6]

        # performance indicators of the configurations
        dico["Operation Costs [CHF]"] = result_AHU_ARU_SCU[:, 7]
        dico["CO2 Emissions [kgCO2-eq]"] = result_AHU_ARU_SCU[:, 8]
        dico["Primary Energy Needs [MJoil-eq]"] = result_AHU_ARU_SCU[:, 9]
        dico["Annualized Investment Costs [CHF]"] = Inv_Costs_AHU_ARU_SCU[:, 0]
        dico["Total Costs [CHF]"] = TotalCosts[:, 1]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power DX"] = result_AHU_ARU_SCU[:, 0] * Qc_nom_combination_AHU_ARU_SCU_W
        dico["Nominal Power VCC"] = result_AHU_ARU_SCU[:, 1] * Qc_nom_combination_AHU_ARU_SCU_W
        dico["Nominal Power single-effect ACH"] = result_AHU_ARU_SCU[:, 2] * Qc_nom_combination_AHU_ARU_SCU_W
        dico["Nominal Power double-effect ACH"] = result_AHU_ARU_SCU[:, 3] * Qc_nom_combination_AHU_ARU_SCU_W
        dico["Nominal Power VCC_to_AA"] = result_AHU_ARU_SCU[:, 4] * Qc_nom_combination_AHU_ARU_W
        dico["Nominal Power VCC_to_S"] = result_AHU_ARU_SCU[:, 5] * Qc_nom_combination_SCU_W
        dico["Nominal Power single-effect ACH_to_S"] = result_AHU_ARU_SCU[:, 6] * Qc_nom_combination_SCU_W


        dico_df = pd.DataFrame(dico)
        fName = locator.get_optimization_disconnected_folder_building_result_cooling(building_name, 'AHU_ARU_SCU')
        dico_df.to_csv(fName, sep=',')

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
    disconnected_buildings_cooling_main(locator, building_names, config, prices)

    print 'test_decentralized_buildings_cooling() succeeded'


if __name__ == '__main__':
    main(cea.config.Configuration())

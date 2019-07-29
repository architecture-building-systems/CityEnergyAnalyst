"""
Operation for decentralized buildings
"""
from __future__ import division

import time
from math import ceil

import numpy as np
import pandas as pd

import cea.config
import cea.globalvar
import cea.inputlocator
import cea.technologies.boiler as boiler
import cea.technologies.burner as burner
import cea.technologies.chiller_absorption as chiller_absorption
import cea.technologies.chiller_vapor_compression as chiller_vapor_compression
import cea.technologies.cooling_tower as cooling_tower
import cea.technologies.direct_expansion_units as dx
import cea.technologies.solar.solar_collector as solar_collector
import cea.technologies.substation as substation
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK, WH_TO_J
from cea.constants import HOURS_IN_YEAR
from cea.optimization.constants import SIZING_MARGIN, T_GENERATOR_FROM_FP_C, T_GENERATOR_FROM_ET_C, \
    Q_LOSS_DISCONNECTED, ACH_TYPE_SINGLE
from cea.optimization.lca_calculations import LcaCalculations
from cea.technologies.thermal_network.thermal_network import calculate_ground_temperature


def disconnected_buildings_cooling_main(locator, building_names, config, prices, lca):
    """
    Computes the parameters for the operation of disconnected buildings output results in csv files.
    There is no optimization at this point. The different cooling energy supply system configurations are calculated
    and compared 1 to 1 to each other. it is a classical combinatorial problem.
    The six supply system configurations include:
    (VCC: Vapor Compression Chiller, ACH: Absorption Chiller, CT: Cooling Tower, Boiler)
    (AHU: Air Handling Units, ARU: Air Recirculation Units, SCU: Sensible Cooling Units)
    - config 0: Direct Expansion / Mini-split units (NOTE: this configuration is not fully built yet)
    - config 1: VCC_to_AAS (AHU + ARU + SCU) + CT
    - config 2: FP + single-effect ACH_to_AAS (AHU + ARU + SCU) + Boiler + CT
    - config 3: ET + single-effect ACH_to_AAS (AHU + ARU + SCU) + Boiler + CT
    - config 4: VCC_to_AA (AHU + ARU) + VCC_to_S (SCU) + CT
    - config 5: VCC_to_AA (AHU + ARU) + single effect ACH_S (SCU) + CT + Boiler

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

    substation.substation_main_cooling(locator, total_demand, building_names, cooling_configuration=['aru','ahu','scu'])

    for building_name in building_names:

        ## Calculate cooling loads for different combinations
        substation.substation_main_cooling(locator, total_demand, buildings_name_with_cooling=[building_name],
                                           cooling_configuration=['ahu'])
        loads_AHU = pd.read_csv(locator.get_optimization_substations_results_file(building_name, "DC", ""),
                                usecols=["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K",
                                         "T_return_DC_space_cooling_data_center_and_refrigeration_result_K",
                                         "mdot_space_cooling_data_center_and_refrigeration_result_kgpers"])

        substation.substation_main_cooling(locator, total_demand, buildings_name_with_cooling=[building_name],
                                           cooling_configuration=['aru'])
        loads_ARU = pd.read_csv(locator.get_optimization_substations_results_file(building_name, "DC", ""),
                                usecols=["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K",
                                         "T_return_DC_space_cooling_data_center_and_refrigeration_result_K",
                                         "mdot_space_cooling_data_center_and_refrigeration_result_kgpers"])

        substation.substation_main_cooling(locator, total_demand, buildings_name_with_cooling=[building_name],
                                           cooling_configuration=['scu'])
        loads_SCU = pd.read_csv(locator.get_optimization_substations_results_file(building_name, "DC", ""),
                                usecols=["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K",
                                         "T_return_DC_space_cooling_data_center_and_refrigeration_result_K",
                                         "mdot_space_cooling_data_center_and_refrigeration_result_kgpers"])

        substation.substation_main_cooling(locator, total_demand, buildings_name_with_cooling=[building_name],
                                           cooling_configuration=['aru','ahu'])
        loads_AHU_ARU = pd.read_csv(locator.get_optimization_substations_results_file(building_name, "DC", ""),
                                    usecols=["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K",
                                             "T_return_DC_space_cooling_data_center_and_refrigeration_result_K",
                                             "mdot_space_cooling_data_center_and_refrigeration_result_kgpers"])

        substation.substation_main_cooling(locator, total_demand, buildings_name_with_cooling=[building_name],
                                           cooling_configuration=['ahu','scu'])
        loads_AHU_SCU = pd.read_csv(locator.get_optimization_substations_results_file(building_name, "DC", ""),
                                    usecols=["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K",
                                             "T_return_DC_space_cooling_data_center_and_refrigeration_result_K",
                                             "mdot_space_cooling_data_center_and_refrigeration_result_kgpers"])

        substation.substation_main_cooling(locator, total_demand, buildings_name_with_cooling=[building_name],
                                           cooling_configuration=['aru','scu'])
        loads_ARU_SCU = pd.read_csv(locator.get_optimization_substations_results_file(building_name, "DC", ""),
                                    usecols=["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K",
                                             "T_return_DC_space_cooling_data_center_and_refrigeration_result_K",
                                             "mdot_space_cooling_data_center_and_refrigeration_result_kgpers"])

        substation.substation_main_cooling(locator, total_demand, buildings_name_with_cooling=[building_name],
                                           cooling_configuration=['aru','ahu','scu'])
        loads_AHU_ARU_SCU = pd.read_csv(locator.get_optimization_substations_results_file(building_name, "DC", ""),
                                        usecols=["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K",
                                                 "T_return_DC_space_cooling_data_center_and_refrigeration_result_K",
                                                 "mdot_space_cooling_data_center_and_refrigeration_result_kgpers"])

        Qc_load_combination_AHU_W = np.vectorize(calc_new_load)(
            loads_AHU["mdot_space_cooling_data_center_and_refrigeration_result_kgpers"],
            loads_AHU["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K"],
            loads_AHU["T_return_DC_space_cooling_data_center_and_refrigeration_result_K"])

        Qc_load_combination_ARU_W = np.vectorize(calc_new_load)(
            loads_ARU["mdot_space_cooling_data_center_and_refrigeration_result_kgpers"],
            loads_ARU["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K"],
            loads_ARU["T_return_DC_space_cooling_data_center_and_refrigeration_result_K"])

        Qc_load_combination_SCU_W = np.vectorize(calc_new_load)(
            loads_SCU["mdot_space_cooling_data_center_and_refrigeration_result_kgpers"],
            loads_SCU["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K"],
            loads_SCU["T_return_DC_space_cooling_data_center_and_refrigeration_result_K"])

        Qc_load_combination_AHU_ARU_W = np.vectorize(calc_new_load)(
            loads_AHU_ARU["mdot_space_cooling_data_center_and_refrigeration_result_kgpers"],
            loads_AHU_ARU["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K"],
            loads_AHU_ARU["T_return_DC_space_cooling_data_center_and_refrigeration_result_K"])

        Qc_load_combination_AHU_SCU_W = np.vectorize(calc_new_load)(
            loads_AHU_SCU["mdot_space_cooling_data_center_and_refrigeration_result_kgpers"],
            loads_AHU_SCU["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K"],
            loads_AHU_SCU["T_return_DC_space_cooling_data_center_and_refrigeration_result_K"])

        Qc_load_combination_ARU_SCU_W = np.vectorize(calc_new_load)(
            loads_ARU_SCU["mdot_space_cooling_data_center_and_refrigeration_result_kgpers"],
            loads_ARU_SCU["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K"],
            loads_ARU_SCU["T_return_DC_space_cooling_data_center_and_refrigeration_result_K"])

        Qc_load_combination_AHU_ARU_SCU_W = np.vectorize(calc_new_load)(
            loads_AHU_ARU_SCU["mdot_space_cooling_data_center_and_refrigeration_result_kgpers"],
            loads_AHU_ARU_SCU["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K"],
            loads_AHU_ARU_SCU["T_return_DC_space_cooling_data_center_and_refrigeration_result_K"])

        Qc_nom_combination_AHU_W = Qc_load_combination_AHU_W.max() * (
                1 + SIZING_MARGIN)  # 20% reliability margin on installed capacity
        Qc_nom_combination_ARU_W = Qc_load_combination_ARU_W.max() * (1 + SIZING_MARGIN)
        Qc_nom_combination_SCU_W = Qc_load_combination_SCU_W.max() * (1 + SIZING_MARGIN)
        Qc_nom_combination_AHU_ARU_W = Qc_load_combination_AHU_ARU_W.max() * (1 + SIZING_MARGIN)
        Qc_nom_combination_AHU_SCU_W = Qc_load_combination_AHU_SCU_W.max() * (1 + SIZING_MARGIN)
        Qc_nom_combination_ARU_SCU_W = Qc_load_combination_ARU_SCU_W.max() * (1 + SIZING_MARGIN)
        Qc_nom_combination_AHU_ARU_SCU_W = Qc_load_combination_AHU_ARU_SCU_W.max() * (1 + SIZING_MARGIN)

        # read chilled water supply/return temperatures and mass flows from substation calculation
        T_re_SCU_K = loads_SCU["T_return_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        T_sup_SCU_K = loads_SCU["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        mdot_SCU_kgpers = loads_SCU["mdot_space_cooling_data_center_and_refrigeration_result_kgpers"].values

        T_re_AHU_ARU_K = loads_AHU_ARU["T_return_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        T_sup_AHU_ARU_K = loads_AHU_ARU["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        mdot_AHU_ARU_kgpers = loads_AHU_ARU["mdot_space_cooling_data_center_and_refrigeration_result_kgpers"].values

        T_re_AHU_ARU_SCU_K = loads_AHU_ARU_SCU[
            "T_return_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        T_sup_AHU_ARU_SCU_K = loads_AHU_ARU_SCU[
            "T_supply_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        mdot_AHU_ARU_SCU_kgpers = loads_AHU_ARU_SCU[
            "mdot_space_cooling_data_center_and_refrigeration_result_kgpers"].values

        ## calculate hot water supply conditions to absorption chillers from SC or boiler
        # Flate Plate Solar Collectors
        SC_FP_data = pd.read_csv(locator.SC_results(building_name=building_name, panel_type='FP'),
                                 usecols=["T_SC_sup_C", "T_SC_re_C", "mcp_SC_kWperC", "Q_SC_gen_kWh", "Area_SC_m2",
                                          "Eaux_SC_kWh"])
        q_sc_gen_FP_Wh = SC_FP_data['Q_SC_gen_kWh'] * 1000
        q_sc_gen_FP_Wh = np.where(q_sc_gen_FP_Wh < 0.0, 0.0, q_sc_gen_FP_Wh)
        el_aux_SC_FP_Wh = SC_FP_data['Eaux_SC_kWh'] * 1000
        T_hw_in_FP_C = [x if x > T_GENERATOR_FROM_FP_C else T_GENERATOR_FROM_FP_C for x in SC_FP_data['T_SC_re_C']]

        Capex_a_SC_FP_USD, Opex_SC_FP_USD, Capex_SC_FP_USD = solar_collector.calc_Cinv_SC(SC_FP_data['Area_SC_m2'][0],
                                                                                          locator, config,
                                                                                          panel_type="FP")
        # Evacuated Tube Solar Collectors
        SC_ET_data = pd.read_csv(locator.SC_results(building_name=building_name, panel_type='ET'),
                                 usecols=["T_SC_sup_C", "T_SC_re_C", "mcp_SC_kWperC", "Q_SC_gen_kWh", "Area_SC_m2",
                                          "Eaux_SC_kWh"])
        q_sc_gen_ET_Wh = SC_ET_data['Q_SC_gen_kWh'] * 1000
        q_sc_gen_ET_Wh = np.where(q_sc_gen_ET_Wh < 0.0, 0.0, q_sc_gen_ET_Wh)
        el_aux_SC_ET_Wh = SC_ET_data['Eaux_SC_kWh'] * 1000
        T_hw_in_ET_C = [x if x > T_GENERATOR_FROM_ET_C else T_GENERATOR_FROM_ET_C for x in SC_ET_data['T_SC_re_C']]

        Capex_a_SC_ET_USD, Opex_SC_ET_USD, Capex_SC_ET_USD = solar_collector.calc_Cinv_SC(SC_ET_data['Area_SC_m2'][0],
                                                                                          locator, config,
                                                                                          panel_type="ET")

        ## calculate ground temperatures to estimate cold water supply temperatures for absorption chiller
        T_ground_K = calculate_ground_temperature(locator,
                                                  config)  # FIXME: change to outlet temperature from the cooling towers


        # Get chiller cost data
        # VCC
        VCC_cost_data = pd.read_excel(locator.get_supply_systems(), sheet_name="Chiller")
        VCC_cost_data = VCC_cost_data[VCC_cost_data['code'] == 'CH3']
        max_VCC_chiller_size_W = max(VCC_cost_data['cap_max'].values)
        # ACH
        Absorption_chiller_cost_data = pd.read_excel(locator.get_supply_systems(),
                                                     sheet_name="Absorption_chiller")
        Absorption_chiller_cost_data = Absorption_chiller_cost_data[
            Absorption_chiller_cost_data['type'] == ACH_TYPE_SINGLE]
        max_ACH_chiller_size_W = max(Absorption_chiller_cost_data['cap_max'].values)
        # # CT
        # CT_cost_data = pd.read_excel(locator.get_supply_systems(),sheet_name="CT")
        # CT_cost_data = CT_cost_data[Absorption_chiller_cost_data['code'] == 'CT1']
        # max_CT_size_W = max(CT_cost_data['cap_max'].values)
        # # Boiler
        # Boiler_cost_data = pd.read_excel(locator.get_supply_systems(),sheet_name="Boiler")
        # Boiler_cost_data = Boiler_cost_data[Absorption_chiller_cost_data['code'] == 'BO1']
        # max_Boiler_size_W = max(Boiler_cost_data['cap_max'].values)

        ## Decentralized supply systems supply to loads from AHU & ARU & SCU
        result_AHU_ARU_SCU = np.zeros((6, 10))
        # logging the supply technology used in each condiguration
        # config 0: DX
        result_AHU_ARU_SCU[0][0] = 1
        # config 1: VCC to AHU
        result_AHU_ARU_SCU[1][1] = 1
        # config 2: single-effect ACH with FP to AHU & ARU & SCU
        result_AHU_ARU_SCU[2][2] = 1
        # config 3: single-effect ACH with ET to AHU & ARU & SCU
        result_AHU_ARU_SCU[3][3] = 1
        # config 4: VCC to AHU + ARU and VCC to SCU
        result_AHU_ARU_SCU[4][4] = 1
        result_AHU_ARU_SCU[4][5] = 1
        # config 5: VCC to AHU + ARU and single effect ACH to SCU
        result_AHU_ARU_SCU[5][4] = 1
        result_AHU_ARU_SCU[5][6] = 1

        if True:  # for the case with AHU + ARU + SCU scenario. this should always be present

            print building_name, ' decentralized building simulation with configuration: AHU + ARU + SCU'

            ## HOURLY OPERATION
            T_re_AHU_ARU_SCU_K = np.where(T_re_AHU_ARU_SCU_K > 0.0, T_re_AHU_ARU_SCU_K, T_sup_AHU_ARU_SCU_K)
            ## 0. DX operation
            el_DX_hourly_Wh = np.vectorize(dx.calc_DX)(mdot_AHU_ARU_SCU_kgpers, T_sup_AHU_ARU_SCU_K, T_re_AHU_ARU_SCU_K)
            # add electricity costs, CO2, PE
            result_AHU_ARU_SCU[0][7] = sum(lca.ELEC_PRICE * el_DX_hourly_Wh)
            result_AHU_ARU_SCU[0][8] = sum(el_DX_hourly_Wh * WH_TO_J / 1E6 * lca.EL_TO_CO2 /1E3) # ton CO2
            result_AHU_ARU_SCU[0][9] = sum(el_DX_hourly_Wh * WH_TO_J / 1E6 * lca.EL_TO_OIL_EQ) # MJ oil

            ## 1. VCC (AHU + ARU + SCU) + CT
            # VCC operation
            Q_VCC_AHU_ARU_SCU_size_W, \
            number_of_VCC_AHU_ARU_SCU_chillers = get_tech_size_and_number(Qc_nom_combination_AHU_ARU_SCU_W,
                                                                          max_VCC_chiller_size_W)
            VCC_to_AHU_ARU_SCU_operation = np.vectorize(chiller_vapor_compression.calc_VCC)(mdot_AHU_ARU_SCU_kgpers,
                                                                                  T_sup_AHU_ARU_SCU_K,
                                                                                  T_re_AHU_ARU_SCU_K,
                                                                                  Q_VCC_AHU_ARU_SCU_size_W,
                                                                                  number_of_VCC_AHU_ARU_SCU_chillers)
            q_cw_Wh = np.asarray([x['q_cw_W'] for x in VCC_to_AHU_ARU_SCU_operation])
            el_VCC_Wh = np.asarray([x['wdot_W'] for x in VCC_to_AHU_ARU_SCU_operation])
            # CT operation
            q_CT_VCC_to_AHU_ARU_SCU_W = q_cw_Wh
            CT_VCC_to_AHU_ARU_SCU_nom_size_W = np.max(q_CT_VCC_to_AHU_ARU_SCU_W) * (1 + SIZING_MARGIN)
            el_CT_Wh = np.vectorize(cooling_tower.calc_CT)(q_CT_VCC_to_AHU_ARU_SCU_W, CT_VCC_to_AHU_ARU_SCU_nom_size_W)
            # add costs
            el_total_Wh = el_VCC_Wh + el_CT_Wh
            result_AHU_ARU_SCU[1][7] += sum(lca.ELEC_PRICE * el_total_Wh)  # CHF
            result_AHU_ARU_SCU[1][8] += sum(el_total_Wh * WH_TO_J / 1E6 * lca.EL_TO_CO2 / 1E3)  # ton CO2
            result_AHU_ARU_SCU[1][9] += sum(el_total_Wh * WH_TO_J / 1E6 * lca.EL_TO_OIL_EQ)  # MJ-oil-eq

            print 'done with config 1'

            # 2: SC_FP + single-effect ACH (AHU + ARU + SCU) + CT + Boiler + SC_FP
            # calculate single-effect ACH operation
            Q_ACH_AHU_ARU_SCU_size_W, \
            number_of_ACH_AHU_ARU_SCU_chillers = get_tech_size_and_number(Qc_nom_combination_AHU_ARU_SCU_W,
                                                                          max_ACH_chiller_size_W)
            SC_FP_to_single_ACH_to_AHU_ARU_SCU_operation = np.vectorize(chiller_absorption.calc_chiller_main)(
                mdot_AHU_ARU_SCU_kgpers,
                T_sup_AHU_ARU_SCU_K,
                T_re_AHU_ARU_SCU_K,
                T_hw_in_FP_C,
                T_ground_K,
                ACH_TYPE_SINGLE,
                Q_ACH_AHU_ARU_SCU_size_W,
                locator, config)
            el_single_ACH_Wh = np.asarray([x['wdot_W'] for x in SC_FP_to_single_ACH_to_AHU_ARU_SCU_operation])
            q_cw_single_ACH_Wh = np.asarray([x['q_cw_W'] for x in SC_FP_to_single_ACH_to_AHU_ARU_SCU_operation])
            q_hw_single_ACH_Wh = np.asarray([x['q_hw_W'] for x in SC_FP_to_single_ACH_to_AHU_ARU_SCU_operation])
            T_hw_out_single_ACH_K = np.asarray([x['T_hw_out_C'] + 273.15 for x in SC_FP_to_single_ACH_to_AHU_ARU_SCU_operation])
            el_for_FP_ACH_W = el_single_ACH_Wh + el_aux_SC_FP_Wh
            # CT operation
            q_CT_FP_to_single_ACH_to_AHU_ARU_SCU_W = q_cw_single_ACH_Wh
            CT_FP_to_single_ACH_to_AHU_ARU_SCU_nom_size_W = np.max(q_CT_FP_to_single_ACH_to_AHU_ARU_SCU_W) * (
                    1 + SIZING_MARGIN)
            el_CT_Wh = np.vectorize(cooling_tower.calc_CT)(q_CT_FP_to_single_ACH_to_AHU_ARU_SCU_W,
                                                           CT_FP_to_single_ACH_to_AHU_ARU_SCU_nom_size_W)

            # boiler operation
            if not np.isclose(Q_ACH_AHU_ARU_SCU_size_W, 0.0):
                q_boiler_FP_to_single_ACH_to_AHU_ARU_SCU_W = q_hw_single_ACH_Wh - q_sc_gen_FP_Wh
                boiler_FP_to_single_ACH_to_AHU_ARU_SCU_nom_size_W = np.max(q_boiler_FP_to_single_ACH_to_AHU_ARU_SCU_W) * (
                        1 + SIZING_MARGIN)
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_FP_to_single_ACH_to_AHU_ARU_SCU_K = T_hw_out_single_ACH_K
                boiler_eff = np.vectorize(boiler.calc_Cop_boiler)(q_boiler_FP_to_single_ACH_to_AHU_ARU_SCU_W,
                                                                  boiler_FP_to_single_ACH_to_AHU_ARU_SCU_nom_size_W,
                                                                  T_re_boiler_FP_to_single_ACH_to_AHU_ARU_SCU_K)
                Q_gas_for_boiler_Wh = np.divide(q_boiler_FP_to_single_ACH_to_AHU_ARU_SCU_W, boiler_eff,
                                                out=np.zeros_like(q_boiler_FP_to_single_ACH_to_AHU_ARU_SCU_W),
                                                where=boiler_eff!=0)
            else:
                boiler_FP_to_single_ACH_to_AHU_ARU_SCU_nom_size_W = 0.0
                Q_gas_for_boiler_Wh = np.zeros(len(el_single_ACH_Wh))

            # add electricity costs
            el_total_Wh = el_for_FP_ACH_W + el_CT_Wh
            result_AHU_ARU_SCU[2][7] = sum(lca.ELEC_PRICE * el_total_Wh)  # CHF
            result_AHU_ARU_SCU[2][8] = sum(el_total_Wh * WH_TO_J / 1E6 * lca.EL_TO_CO2 / 1E3)  # ton CO2
            result_AHU_ARU_SCU[2][9] = sum(el_total_Wh * WH_TO_J / 1E6 * lca.EL_TO_OIL_EQ)  # MJ-oil-eq
            # add gas costs
            result_AHU_ARU_SCU[2][7] += sum(prices.NG_PRICE * Q_gas_for_boiler_Wh)  # CHF
            result_AHU_ARU_SCU[2][8] += sum(Q_gas_for_boiler_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_CO2_STD / 1E3)  # ton CO2
            result_AHU_ARU_SCU[2][9] += sum(Q_gas_for_boiler_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_OIL_STD)  # MJ-oil-eq

            print 'done with config 2'

            # 3: SC_ET + single-effect ACH (AHU + ARU + SCU) + CT + Boiler + SC_ET
            ET_to_single_ACH_to_AHU_ARU_SCU_operation = np.vectorize(chiller_absorption.calc_chiller_main)(
                mdot_AHU_ARU_SCU_kgpers,
                T_sup_AHU_ARU_SCU_K,
                T_re_AHU_ARU_SCU_K,
                T_hw_in_ET_C,
                T_ground_K,
                ACH_TYPE_SINGLE,
                Q_ACH_AHU_ARU_SCU_size_W,
                locator, config)
            el_single_ACH_Wh = np.asarray([x['wdot_W'] for x in ET_to_single_ACH_to_AHU_ARU_SCU_operation])
            q_cw_single_ACH_Wh = np.asarray([x['q_cw_W'] for x in ET_to_single_ACH_to_AHU_ARU_SCU_operation])
            q_hw_single_ACH_Wh = np.asarray([x['q_hw_W'] for x in ET_to_single_ACH_to_AHU_ARU_SCU_operation])
            T_hw_out_single_ACH_K = np.asarray([x['T_hw_out_C'] + 273.15 for x in ET_to_single_ACH_to_AHU_ARU_SCU_operation])
            el_for_ET_ACH_W = el_single_ACH_Wh + el_aux_SC_ET_Wh

            # CT operation
            q_CT_ET_to_single_ACH_to_AHU_ARU_SCU_W = q_cw_single_ACH_Wh
            CT_ET_to_single_ACH_to_AHU_ARU_SCU_nom_size_W = np.max(q_CT_ET_to_single_ACH_to_AHU_ARU_SCU_W) * (
                    1 + SIZING_MARGIN)
            el_CT_Wh = np.vectorize(cooling_tower.calc_CT)(q_CT_ET_to_single_ACH_to_AHU_ARU_SCU_W,
            CT_ET_to_single_ACH_to_AHU_ARU_SCU_nom_size_W)

            # burner operation
            if not np.isclose(Q_ACH_AHU_ARU_SCU_size_W, 0.0):
                q_burner_ET_single_ACH_to_AHU_ARU_SCU_W = q_hw_single_ACH_Wh - q_sc_gen_ET_Wh
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_ET_to_single_ACH_to_AHU_ARU_SCU_K = T_hw_out_single_ACH_K
                burner_ET_to_single_ACH_to_AHU_ARU_SCU_nom_size_W = np.max(q_burner_ET_single_ACH_to_AHU_ARU_SCU_W) * (
                        1 + SIZING_MARGIN)

                burner_eff = np.vectorize(burner.calc_cop_burner)(q_burner_ET_single_ACH_to_AHU_ARU_SCU_W,
                                                                  burner_ET_to_single_ACH_to_AHU_ARU_SCU_nom_size_W)
                Q_gas_for_burner_Wh = q_burner_ET_single_ACH_to_AHU_ARU_SCU_W / burner_eff
            else:
                burner_ET_to_single_ACH_to_AHU_ARU_SCU_nom_size_W = 0.0
                Q_gas_for_burner_Wh = np.zeros(len(el_single_ACH_Wh))

            # add electricity costs
            el_total_Wh = el_for_ET_ACH_W + el_CT_Wh
            result_AHU_ARU_SCU[3][7] = sum(lca.ELEC_PRICE * el_total_Wh)  # CHF
            result_AHU_ARU_SCU[3][8] = sum(el_total_Wh * WH_TO_J / 1E6 * lca.EL_TO_CO2 / 1E3)  # ton CO2
            result_AHU_ARU_SCU[3][9] = sum(el_total_Wh * WH_TO_J / 1E6 * lca.EL_TO_OIL_EQ)  # MJ-oil-eq
            # add gas costs
            result_AHU_ARU_SCU[3][7] += sum(prices.NG_PRICE * Q_gas_for_burner_Wh)  # CHF
            result_AHU_ARU_SCU[3][8] += sum(Q_gas_for_burner_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_CO2_STD / 1E3)  # ton CO2
            result_AHU_ARU_SCU[3][9] += sum(Q_gas_for_burner_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_OIL_STD)  # MJ-oil-eq

            print 'done with config 3'

            # 4: VCC (AHU + ARU) + VCC (SCU) + CT
            # VCC (AHU + ARU) operation
            Q_VCC_AHU_ARU_size_W, \
            number_of_VCC_AHU_ARU_chillers = get_tech_size_and_number(Qc_nom_combination_AHU_ARU_W, max_VCC_chiller_size_W)
            VCC_to_AHU_ARU_operation = np.vectorize(chiller_vapor_compression.calc_VCC)(mdot_AHU_ARU_kgpers,
                                                                          T_sup_AHU_ARU_K,
                                                                          T_re_AHU_ARU_K, Q_VCC_AHU_ARU_size_W,
                                                                          number_of_VCC_AHU_ARU_chillers)
            el_VCC_to_AHU_ARU_Wh = np.asarray([x['wdot_W'] for x in VCC_to_AHU_ARU_operation])
            q_cw_VCC_to_AHU_ARU_Wh = np.asarray([x['q_cw_W'] for x in VCC_to_AHU_ARU_operation])
            # VCC(SCU) operation
            Q_VCC_SCU_size_W, \
            number_of_VCC_SCU_chillers = get_tech_size_and_number(Qc_nom_combination_SCU_W, max_VCC_chiller_size_W)
            VCC_to_SCU_operation = np.vectorize(chiller_vapor_compression.calc_VCC)(mdot_SCU_kgpers, T_sup_SCU_K,
                                                                      T_re_SCU_K, Q_VCC_SCU_size_W,
                                                                      number_of_VCC_SCU_chillers)
            el_VCC_to_SCU_Wh = np.asarray([x['wdot_W'] for x in VCC_to_SCU_operation])
            q_cw_VCC_to_SCU_Wh = np.asarray([x['q_cw_W'] for x in VCC_to_SCU_operation])

            el_VCC_total_Wh = el_VCC_to_AHU_ARU_Wh + el_VCC_to_SCU_Wh

            # CT operation
            q_CT_VCC_to_AHU_ARU_and_VCC_to_SCU_W = q_cw_VCC_to_AHU_ARU_Wh + q_cw_VCC_to_SCU_Wh
            CT_VCC_to_AHU_ARU_and_VCC_to_SCU_nom_size_W = np.max(q_CT_VCC_to_AHU_ARU_and_VCC_to_SCU_W) * (
                        1 + SIZING_MARGIN)
            el_CT_Wh = np.vectorize(cooling_tower.calc_CT)(q_CT_VCC_to_AHU_ARU_and_VCC_to_SCU_W,
                                                           CT_VCC_to_AHU_ARU_and_VCC_to_SCU_nom_size_W)

            # add el costs
            el_total_Wh = el_VCC_total_Wh + el_CT_Wh
            result_AHU_ARU_SCU[4][7] += sum(lca.ELEC_PRICE * el_total_Wh)  # CHF
            result_AHU_ARU_SCU[4][8] += sum(el_total_Wh * WH_TO_J / 1E6 * lca.EL_TO_CO2 / 1E3)  # ton CO2
            result_AHU_ARU_SCU[4][9] += sum(el_total_Wh * WH_TO_J / 1E6 * lca.EL_TO_OIL_EQ)  # MJ-oil-eq

            print 'done with config 4'

            # 5: VCC (AHU + ARU) + ACH (SCU) + CT
            # ACH (SCU) operation
            Qnom_ACH_SCU_W, \
            number_of_ACH_SCU_chillers = get_tech_size_and_number(Qc_nom_combination_SCU_W, max_ACH_chiller_size_W)
            FP_to_single_ACH_to_SCU_operation = np.vectorize(chiller_absorption.calc_chiller_main)(mdot_SCU_kgpers,
                                                                                     T_sup_SCU_K,
                                                                                     T_re_SCU_K,
                                                                                     T_hw_in_FP_C,
                                                                                     T_ground_K,
                                                                                     ACH_TYPE_SINGLE,
                                                                                     Qnom_ACH_SCU_W,
                                                                                     locator, config)
            el_FP_ACH_to_SCU_Wh = np.asarray([x['wdot_W'] for x in FP_to_single_ACH_to_SCU_operation])
            q_cw_FP_ACH_to_SCU_Wh = np.asarray([x['q_cw_W'] for x in FP_to_single_ACH_to_SCU_operation])
            q_hw_FP_ACH_to_SCU_Wh = np.asarray([x['q_hw_W'] for x in FP_to_single_ACH_to_SCU_operation])
            T_hw_FP_ACH_to_SCU_K = np.asarray([x['T_hw_out_C'] + 273.15 for x in FP_to_single_ACH_to_SCU_operation])

            # boiler operation
            if not np.isclose(Qnom_ACH_SCU_W, 0.0):
                # boiler operation
                q_boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_W = q_hw_FP_ACH_to_SCU_Wh - q_sc_gen_FP_Wh
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_K = T_hw_FP_ACH_to_SCU_K
                boiler_FP_to_single_ACH_to_SCU_nom_size_W = np.max(q_boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_W) * (
                            1 + SIZING_MARGIN)
                boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_nom_size_W = boiler_FP_to_single_ACH_to_SCU_nom_size_W  # fixme: redundant?

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_W,
                                                    boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_nom_size_W,
                                                    T_re_boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_K)
                Q_gas_for_boiler_Wh = np.divide(q_boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_W, boiler_eff,
                                                out=np.zeros_like(q_boiler_FP_to_single_ACH_to_AHU_ARU_SCU_W),
                                                where=boiler_eff != 0)
            else:
                boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_nom_size_W = 0.0
                Q_gas_for_boiler_Wh = np.zeros(len(el_FP_ACH_to_SCU_Wh))

            # CT operation
            q_CT_VCC_to_AHU_ARU_and_single_ACH_to_SCU_W = q_cw_VCC_to_AHU_ARU_Wh + q_cw_FP_ACH_to_SCU_Wh
            CT_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_nom_size_W = np.max(
                q_CT_VCC_to_AHU_ARU_and_single_ACH_to_SCU_W) * (1 + SIZING_MARGIN)
            el_CT_Wh = np.vectorize(cooling_tower.calc_CT)(q_CT_VCC_to_AHU_ARU_and_single_ACH_to_SCU_W,
                                                           CT_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_nom_size_W)

            # add electricity costs
            el_total_Wh = el_VCC_to_AHU_ARU_Wh + el_FP_ACH_to_SCU_Wh + el_aux_SC_FP_Wh + el_CT_Wh
            result_AHU_ARU_SCU[5][7] = sum(lca.ELEC_PRICE* el_total_Wh)  # CHF
            result_AHU_ARU_SCU[5][8] = sum(el_total_Wh * WH_TO_J / 1E6 * lca.EL_TO_CO2 / 1E3)  # ton CO2
            result_AHU_ARU_SCU[5][9] = sum(el_total_Wh * WH_TO_J / 1E6 * lca.EL_TO_OIL_EQ)  # MJ-oil-eq
            # add gas costs
            result_AHU_ARU_SCU[5][7] += sum(prices.NG_PRICE * Q_gas_for_boiler_Wh)  # CHF
            result_AHU_ARU_SCU[5][
                8] += sum(Q_gas_for_boiler_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_CO2_STD / 1E3)  # ton CO2
            result_AHU_ARU_SCU[5][
                9] += sum(Q_gas_for_boiler_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_OIL_STD)  # MJ-oil-eq

            print 'done with config 5'

        ## Calculate Capex/Opex
        # AHU
        Capex_a_AHU_USD = np.zeros((4, 1))
        Capex_total_AHU_USD = np.zeros((4, 1))
        Opex_a_fixed_AHU_USD = np.zeros((4, 1))

        # ARU
        Capex_a_ARU_USD = np.zeros((4, 1))
        Capex_total_ARU_USD = np.zeros((4, 1))
        Opex_a_fixed_ARU_USD = np.zeros((4, 1))

        # SCU
        Capex_a_SCU_USD = np.zeros((4, 1))
        Capex_total_SCU_USD = np.zeros((4, 1))
        Opex_a_fixed_SCU_USD = np.zeros((4, 1))

        # AHU + ARU
        Capex_a_AHU_ARU_USD = np.zeros((4, 1))
        Capex_total_AHU_ARU_USD = np.zeros((4, 1))
        Opex_a_fixed_AHU_ARU_USD = np.zeros((4, 1))

        # AHU + SCU
        Capex_a_AHU_SCU_USD = np.zeros((4, 1))
        Capex_total_AHU_SCU_USD = np.zeros((4, 1))
        Opex_a_fixed_AHU_SCU_USD = np.zeros((4, 1))

        # ARU + SCU
        Capex_a_ARU_SCU_USD = np.zeros((4, 1))
        Capex_total_ARU_SCU_USD = np.zeros((4, 1))
        Opex_a_fixed_ARU_SCU_USD = np.zeros((4, 1))

        # AHU + ARU + SCU
        Capex_a_AHU_ARU_SCU_USD = np.zeros((6, 1))
        Capex_total_AHU_ARU_SCU_USD = np.zeros((6, 1))
        Opex_a_fixed_AHU_ARU_SCU_USD = np.zeros((6, 1))
        if True:  # for the case with AHU + ARU + SCU scenario. this should always be present
            print 'decentralized building simulation with configuration: AHU + ARU + SCU cost calculations'
            # 0: DX
            print 'DX'
            Capex_a_DX_USD, Opex_fixed_DX_USD, Capex_DX_USD = dx.calc_Cinv_DX(Qc_nom_combination_AHU_ARU_SCU_W)
            Capex_a_AHU_ARU_SCU_USD[0][0] = Capex_a_DX_USD  # FIXME: a dummy value to rule out this configuration
            Capex_total_AHU_ARU_SCU_USD[0][0] = Capex_DX_USD  # FIXME: a dummy value to rule out this configuration
            Opex_a_fixed_AHU_ARU_SCU_USD[0][0] = Opex_fixed_DX_USD


            # 1: VCC + CT
            print 'VCC + CT'
            Capex_a_VCC_USD, Opex_fixed_VCC_USD, Capex_VCC_USD = chiller_vapor_compression.calc_Cinv_VCC(
                Qc_nom_combination_AHU_ARU_SCU_W, locator, config, 'CH3')
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(
                CT_VCC_to_AHU_ARU_SCU_nom_size_W, locator, config, 'CT1')

            Capex_a_AHU_ARU_SCU_USD[1][0] = Capex_a_CT_USD + Capex_a_VCC_USD
            Capex_total_AHU_ARU_SCU_USD[1][0] = Capex_CT_USD + Capex_VCC_USD
            Opex_a_fixed_AHU_ARU_SCU_USD[1][0] = Opex_fixed_CT_USD + Opex_fixed_VCC_USD


            # 2: single effect ACH + CT + Boiler + SC_FP
            print 'single effect ACH + CT + Boiler + SC_FP'
            Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(
                Qc_nom_combination_AHU_ARU_SCU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(
                CT_FP_to_single_ACH_to_AHU_ARU_SCU_nom_size_W, locator, config, 'CT1')
            Capex_a_boiler_USD, Opex_fixed_boiler_USD, Capex_boiler_USD = boiler.calc_Cinv_boiler(
                boiler_FP_to_single_ACH_to_AHU_ARU_SCU_nom_size_W, locator, config, 'BO1')
            Capex_a_AHU_ARU_SCU_USD[2][0] = Capex_a_CT_USD + Capex_a_ACH_USD + Capex_a_boiler_USD + Capex_a_SC_FP_USD
            Capex_total_AHU_ARU_SCU_USD[2][0] = Capex_CT_USD + Capex_ACH_USD + Capex_boiler_USD + Capex_SC_FP_USD
            Opex_a_fixed_AHU_ARU_SCU_USD[2][
                0] = Opex_fixed_CT_USD + Opex_fixed_ACH_USD + Opex_fixed_boiler_USD + Opex_SC_FP_USD

            # 3: double effect ACH + CT + Boiler + SC_ET
            print 'double effect ACH + CT + Boiler + SC_ET'
            Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(
                Qc_nom_combination_AHU_ARU_SCU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(
                CT_ET_to_single_ACH_to_AHU_ARU_SCU_nom_size_W, locator, config, 'CT1')
            Capex_a_burner_USD, Opex_fixed_burner_USD, Capex_burner_USD = burner.calc_Cinv_burner(
                burner_ET_to_single_ACH_to_AHU_ARU_SCU_nom_size_W, locator, config, 'BO1')
            Capex_a_AHU_ARU_SCU_USD[3][0] = Capex_a_CT_USD + Capex_a_ACH_USD + Capex_a_burner_USD + Capex_a_SC_ET_USD
            Capex_total_AHU_ARU_SCU_USD[3][0] = Capex_CT_USD + Capex_ACH_USD + Capex_burner_USD + Capex_SC_ET_USD
            Opex_a_fixed_AHU_ARU_SCU_USD[3][
                0] = Opex_fixed_CT_USD + Opex_fixed_ACH_USD + Opex_fixed_burner_USD + Opex_SC_ET_USD

            # 4: VCC (AHU + ARU) + VCC (SCU) + CT
            print 'VCC (AHU + ARU) + VCC (SCU) + CT'
            Capex_a_VCC_AA_USD, Opex_VCC_AA_USD, Capex_VCC_AA_USD = chiller_vapor_compression.calc_Cinv_VCC(
                Qc_nom_combination_AHU_ARU_W, locator, config, 'CH3')
            Capex_a_VCC_S_USD, Opex_VCC_S_USD, Capex_VCC_S_USD = chiller_vapor_compression.calc_Cinv_VCC(
                Qc_nom_combination_SCU_W, locator, config, 'CH3')
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(
                CT_VCC_to_AHU_ARU_and_VCC_to_SCU_nom_size_W, locator, config, 'CT1')
            Capex_a_AHU_ARU_SCU_USD[4][0] = Capex_a_CT_USD + Capex_a_VCC_AA_USD + Capex_a_VCC_S_USD
            Capex_total_AHU_ARU_SCU_USD[4][0] = Capex_CT_USD + Capex_VCC_AA_USD + Capex_VCC_S_USD
            Opex_a_fixed_AHU_ARU_SCU_USD[4][0] = Opex_fixed_CT_USD + Opex_VCC_AA_USD + Opex_VCC_S_USD

            # 5: VCC (AHU + ARU) + ACH (SCU) + CT + Boiler + SC_FP
            print 'VCC (AHU + ARU) + ACH (SCU) + CT + Boiler + SC_FP'
            Capex_a_ACH_S_USD, Opex_fixed_ACH_S_USD, Capex_ACH_S_USD = chiller_absorption.calc_Cinv_ACH(
                Qc_nom_combination_SCU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(
                CT_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_nom_size_W, locator, config, 'CT1')
            Capex_a_boiler_USD, Opex_fixed_boiler_USD, Capex_boiler_USD = boiler.calc_Cinv_boiler(
                boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_nom_size_W, locator, config, 'BO1')
            Capex_a_SC_FP_USD, Opex_SC_FP_USD, Capex_SC_FP_USD = solar_collector.calc_Cinv_SC(
                SC_FP_data['Area_SC_m2'][0], locator, config, panel_type="FP")
            Capex_a_AHU_ARU_SCU_USD[5][
                0] = Capex_a_CT_USD + Capex_a_VCC_AA_USD + Capex_a_ACH_S_USD + Capex_a_SC_FP_USD + Capex_a_boiler_USD
            Capex_total_AHU_ARU_SCU_USD[5][
                0] = Capex_CT_USD + Capex_VCC_AA_USD + Capex_ACH_S_USD + Capex_SC_FP_USD + Capex_boiler_USD
            Opex_a_fixed_AHU_ARU_SCU_USD[5][
                0] = Opex_fixed_CT_USD + Opex_VCC_AA_USD + Opex_fixed_ACH_S_USD + Opex_SC_FP_USD + Opex_fixed_boiler_USD


        # Best configuration AHU + ARU + SCU
        number_config = len(result_AHU_ARU_SCU)
        Best = np.zeros((number_config, 1))
        indexBest = 0

        # write all results from the configurations into TotalCosts, TotalCO2, TotalPrim
        TAC_USD = np.zeros((number_config, 2))
        TotalCO2 = np.zeros((number_config, 2))
        TotalPrim = np.zeros((number_config, 2))
        Opex_a_AHU_ARU_SCU_USD = np.zeros((number_config, 2))
        for i in range(number_config):
            TAC_USD[i][0] = TotalCO2[i][0] = TotalPrim[i][0] = Opex_a_AHU_ARU_SCU_USD[i][0] = i
            Opex_a_AHU_ARU_SCU_USD[i][1] = Opex_a_fixed_AHU_ARU_SCU_USD[i][0] + result_AHU_ARU_SCU[i][7]
            TAC_USD[i][1] = Capex_a_AHU_ARU_SCU_USD[i][0] + Opex_a_AHU_ARU_SCU_USD[i][1]
            TotalCO2[i][1] = result_AHU_ARU_SCU[i][8]
            TotalPrim[i][1] = result_AHU_ARU_SCU[i][9]

        # rank results
        CostsS = TAC_USD[np.argsort(TAC_USD[:, 1])]
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

        dico["DX to AHU_ARU_SCU Share"] = result_AHU_ARU_SCU[:, 0]
        dico["VCC to AHU_ARU_SCU Share"] = result_AHU_ARU_SCU[:, 1]
        dico["single effect ACH to AHU_ARU_SCU Share (FP)"] = result_AHU_ARU_SCU[:, 2]
        dico["single effect ACH to AHU_ARU_SCU Share (ET)"] = result_AHU_ARU_SCU[:, 3]
        dico["VCC to AHU_ARU Share"] = result_AHU_ARU_SCU[:, 4]
        dico["VCC to SCU Share"] = result_AHU_ARU_SCU[:, 5]
        dico["single effect ACH to SCU Share (FP)"] = result_AHU_ARU_SCU[:, 6]

        # performance indicators of the configurations
        dico["Capex_a_USD"] = Capex_a_AHU_ARU_SCU_USD[:, 0]
        dico["Capex_total_USD"] = Capex_total_AHU_ARU_SCU_USD[:, 0]
        dico["Opex_a_USD"] = Opex_a_AHU_ARU_SCU_USD[:, 1]
        dico["Opex_a_fixed_USD"] = Opex_a_fixed_AHU_ARU_SCU_USD[:, 0]
        dico["Opex_a_var_USD"] = result_AHU_ARU_SCU[:, 7]
        dico["GHG_tonCO2"] = result_AHU_ARU_SCU[:, 8]
        dico["PEN_MJoil"] = result_AHU_ARU_SCU[:, 9]
        dico["TAC_USD"] = TAC_USD[:, 1]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power DX to AHU_ARU_SCU [W]"] = result_AHU_ARU_SCU[:, 0] * Qc_nom_combination_AHU_ARU_SCU_W
        dico["Nominal Power VCC to AHU_ARU_SCU [W]"] = result_AHU_ARU_SCU[:, 1] * Qc_nom_combination_AHU_ARU_SCU_W
        dico["Nominal Power single effect ACH to AHU_ARU_SCU (FP) [W]"] = result_AHU_ARU_SCU[:,
                                                                          2] * Qc_nom_combination_AHU_ARU_SCU_W
        dico["Nominal Power single effect ACH to AHU_ARU_SCU (ET) [W]"] = result_AHU_ARU_SCU[:,
                                                                          3] * Qc_nom_combination_AHU_ARU_SCU_W
        dico["Nominal Power VCC to AHU_ARU [W]"] = result_AHU_ARU_SCU[:, 4] * Qc_nom_combination_AHU_ARU_W
        dico["Nominal Power VCC to SCU [W]"] = result_AHU_ARU_SCU[:, 5] * Qc_nom_combination_SCU_W
        dico["Nominal Power single effect ACH to SCU (FP) [W]"] = result_AHU_ARU_SCU[:, 6] * Qc_nom_combination_SCU_W

        dico_df = pd.DataFrame(dico)
        fName = locator.get_optimization_decentralized_folder_building_result_cooling(building_name, 'AHU_ARU_SCU')
        dico_df.to_csv(fName, sep=',')

    print time.clock() - t0, "seconds process time for the decentralized Building Routine \n"


def get_tech_size_and_number(Qc_nom_W, max_tech_size_W):
    if Qc_nom_W <= max_tech_size_W:
        Q_installed_W = Qc_nom_W
        number_of_installation = 1
    else:
        number_of_installation = int(ceil(Qc_nom_W / max_tech_size_W))
        Q_installed_W = Qc_nom_W / number_of_installation
    return Q_installed_W, number_of_installation


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
        Q_cooling_load_W = mdot_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK * (T_re_K - T_sup_K) * (
                1 + Q_LOSS_DISCONNECTED)  # for cooling load
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
    print('Running decentralized model for buildings with scenario = %s' % config.scenario)

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name
    prices = Prices(locator, config)
    lca = LcaCalculations(locator, config.optimization.detailed_electricity_pricing)
    disconnected_buildings_cooling_main(locator, building_names, config, prices, lca)

    print 'test_decentralized_buildings_cooling() succeeded'


if __name__ == '__main__':
    main(cea.config.Configuration())

"""
Operation for decentralized buildings
"""
from __future__ import division

import cea.config
import cea.globalvar
import cea.inputlocator
import time
import numpy as np
import pandas as pd
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK

from cea.optimization.constants import SIZING_MARGIN, T_GENERATOR_FROM_FP_C, T_GENERATOR_FROM_ET_C, \
    Q_LOSS_DISCONNECTED, ACH_TYPE_SINGLE, ACH_TYPE_DOUBLE
from cea.optimization.lca_calculations import lca_calculations
import cea.technologies.chiller_vapor_compression as chiller_vapor_compression
import cea.technologies.chiller_absorption as chiller_absorption
import cea.technologies.cooling_tower as cooling_tower
import cea.technologies.direct_expansion_units as dx
import cea.technologies.boiler as boiler
import cea.technologies.burner as burner
import cea.technologies.substation as substation
import cea.technologies.solar.solar_collector as solar_collector
from cea.technologies.thermal_network.thermal_network import calculate_ground_temperature
from math import ceil


def disconnected_buildings_cooling_main(locator, building_names, config, prices, lca):
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
                                usecols=["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K",
                                         "T_return_DC_space_cooling_data_center_and_refrigeration_result_K",
                                         "mdot_space_cooling_data_center_and_refrigeration_result_kgpers"])

        substation.substation_main(locator, total_demand, building_names=[building_name], heating_configuration=2,
                                   cooling_configuration=2, Flag=False)
        loads_ARU = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                usecols=["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K",
                                         "T_return_DC_space_cooling_data_center_and_refrigeration_result_K",
                                         "mdot_space_cooling_data_center_and_refrigeration_result_kgpers"])

        substation.substation_main(locator, total_demand, building_names=[building_name], heating_configuration=3,
                                   cooling_configuration=3, Flag=False)
        loads_SCU = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                usecols=["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K",
                                         "T_return_DC_space_cooling_data_center_and_refrigeration_result_K",
                                         "mdot_space_cooling_data_center_and_refrigeration_result_kgpers"])

        substation.substation_main(locator, total_demand, building_names=[building_name], heating_configuration=4,
                                   cooling_configuration=4, Flag=False)
        loads_AHU_ARU = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                    usecols=["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K",
                                             "T_return_DC_space_cooling_data_center_and_refrigeration_result_K",
                                             "mdot_space_cooling_data_center_and_refrigeration_result_kgpers"])

        substation.substation_main(locator, total_demand, building_names=[building_name], heating_configuration=5,
                                   cooling_configuration=5, Flag=False)
        loads_AHU_SCU = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                    usecols=["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K",
                                             "T_return_DC_space_cooling_data_center_and_refrigeration_result_K",
                                             "mdot_space_cooling_data_center_and_refrigeration_result_kgpers"])

        substation.substation_main(locator, total_demand, building_names=[building_name], heating_configuration=6,
                                   cooling_configuration=6, Flag=False)
        loads_ARU_SCU = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                    usecols=["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K",
                                             "T_return_DC_space_cooling_data_center_and_refrigeration_result_K",
                                             "mdot_space_cooling_data_center_and_refrigeration_result_kgpers"])

        substation.substation_main(locator, total_demand, building_names=[building_name], heating_configuration=7,
                                   cooling_configuration=7, Flag=False)
        loads_AHU_ARU_SCU = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
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
        T_re_AHU_K = loads_AHU["T_return_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        T_sup_AHU_K = loads_AHU["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        mdot_AHU_kgpers = loads_AHU["mdot_space_cooling_data_center_and_refrigeration_result_kgpers"].values

        T_re_ARU_K = loads_ARU["T_return_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        T_sup_ARU_K = loads_ARU["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        mdot_ARU_kgpers = loads_ARU["mdot_space_cooling_data_center_and_refrigeration_result_kgpers"].values

        T_re_SCU_K = loads_SCU["T_return_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        T_sup_SCU_K = loads_SCU["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        mdot_SCU_kgpers = loads_SCU["mdot_space_cooling_data_center_and_refrigeration_result_kgpers"].values

        T_re_AHU_ARU_K = loads_AHU_ARU["T_return_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        T_sup_AHU_ARU_K = loads_AHU_ARU["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        mdot_AHU_ARU_kgpers = loads_AHU_ARU["mdot_space_cooling_data_center_and_refrigeration_result_kgpers"].values

        T_re_AHU_SCU_K = loads_AHU_SCU["T_return_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        T_sup_AHU_SCU_K = loads_AHU_SCU["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        mdot_AHU_SCU_kgpers = loads_AHU_SCU["mdot_space_cooling_data_center_and_refrigeration_result_kgpers"].values

        T_re_ARU_SCU_K = loads_ARU_SCU["T_return_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        T_sup_ARU_SCU_K = loads_ARU_SCU["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K"].values
        mdot_ARU_SCU_kgpers = loads_ARU_SCU["mdot_space_cooling_data_center_and_refrigeration_result_kgpers"].values

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
        w_SC_FP_Wh = SC_FP_data['Q_SC_gen_kWh']* 1000
        T_hw_in_FP_C = [x if x > T_GENERATOR_FROM_FP_C else T_GENERATOR_FROM_FP_C for x in SC_FP_data['T_SC_re_C']]

        Capex_a_SC_FP_USD, Opex_SC_FP_USD, Capex_SC_FP_USD = solar_collector.calc_Cinv_SC(SC_FP_data['Area_SC_m2'][0], locator, config,
                                                                 technology=0)
        # Evacuated Tube Solar Collectors
        SC_ET_data = pd.read_csv(locator.SC_results(building_name=building_name, panel_type='ET'),
                                 usecols=["T_SC_sup_C", "T_SC_re_C", "mcp_SC_kWperC", "Q_SC_gen_kWh", "Area_SC_m2",
                                          "Eaux_SC_kWh"])
        q_sc_gen_ET_Wh = SC_ET_data['Q_SC_gen_kWh'] * 1000
        w_SC_ET_Wh = SC_ET_data['Eaux_SC_kWh']* 1000
        T_hw_in_ET_C = [x if x > T_GENERATOR_FROM_ET_C else T_GENERATOR_FROM_ET_C for x in SC_ET_data['T_SC_re_C']]

        Capex_a_SC_ET_USD, Opex_SC_ET_USD, Capex_SC_ET_USD = solar_collector.calc_Cinv_SC(SC_ET_data['Area_SC_m2'][0], locator, config,
                                                                 technology=1)

        ## calculate ground temperatures to estimate cold water supply temperatures for absorption chiller
        T_ground_K = calculate_ground_temperature(locator,
                                                  config)  # FIXME: change to outlet temperature from the cooling towers

        ## Decentralized supply systems only supply to loads from AHU
        result_AHU = np.zeros((4, 10))
        # config 0: DX
        result_AHU[0][0] = 1
        # config 1: VCC to AHU
        result_AHU[1][1] = 1
        # config 2: single-effect ACH with FP to AHU
        result_AHU[2][2] = 1
        # config 3: single-effect ACH with ET to AHU
        result_AHU[3][3] = 1

        q_CT_VCC_to_AHU_W = np.zeros(8760)
        q_CT_FP_to_single_ACH_to_AHU_W = np.zeros(8760)
        q_boiler_FP_to_single_ACH_to_AHU_W = np.zeros(8760)
        q_burner_ET_to_single_ACH_to_AHU_W = np.zeros(8760)
        q_CT_ET_to_single_ACH_to_AHU_W = np.zeros(8760)
        T_re_boiler_FP_to_single_ACH_to_AHU_K = np.zeros(8760)
        T_re_boiler_ET_to_single_ACH_to_AHU_K = np.zeros(8760)

        VCC_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="Chiller")
        VCC_cost_data = VCC_cost_data[VCC_cost_data['code'] == 'CH3']
        max_VCC_chiller_size = max(VCC_cost_data['cap_max'].values)

        Absorption_chiller_cost_data = pd.read_excel(locator.get_supply_systems(config.region),
                                                     sheetname="Absorption_chiller")
        Absorption_chiller_cost_data = Absorption_chiller_cost_data[
            Absorption_chiller_cost_data['type'] == ACH_TYPE_SINGLE]
        max_ACH_chiller_size = max(Absorption_chiller_cost_data['cap_max'].values)

        if config.decentralized.AHUflag:
            print building_name + ' decentralized building simulation with configuration: AHU'

            # chiller operations for config 1-5
            # deciding the number of chillers and the nominal size based on the maximum chiller size

            if Qc_nom_combination_AHU_W <= max_VCC_chiller_size:
                Qnom_VCC_W = Qc_nom_combination_AHU_W
                number_of_VCC_chillers = 1
            else:
                number_of_VCC_chillers = int(ceil(Qc_nom_combination_AHU_W / max_VCC_chiller_size))
                Qnom_VCC_W = Qc_nom_combination_AHU_W / number_of_VCC_chillers

            if Qc_nom_combination_AHU_W <= max_ACH_chiller_size:
                Qnom_ACH_W = Qc_nom_combination_AHU_W
                number_of_ACH_chillers = 1
            else:
                number_of_ACH_chillers = int(ceil(Qc_nom_combination_AHU_W / max_ACH_chiller_size))
                Qnom_ACH_W = Qc_nom_combination_AHU_W / number_of_ACH_chillers

            for hour in range(8760):  # TODO: vectorize
                # modify return temperatures when there is no load
                T_re_AHU_K[hour] = T_re_AHU_K[hour] if T_re_AHU_K[hour] > 0 else T_sup_AHU_K[hour]

                # 0: DX
                DX_operation = dx.calc_DX(mdot_AHU_kgpers[hour], T_sup_AHU_K[hour], T_re_AHU_K[hour])
                result_AHU[0][7] += lca.ELEC_PRICE[hour] * DX_operation  # FIXME: a dummy value to rule out this configuration  # CHF
                result_AHU[0][8] += lca.EL_TO_CO2 * DX_operation  # FIXME: a dummy value to rule out this configuration  # kgCO2
                result_AHU[0][9] += lca.EL_TO_OIL_EQ * DX_operation  # FIXME: a dummy value to rule out this configuration  # MJ-oil-eq

                # 1: VCC
                VCC_to_AHU_operation = chiller_vapor_compression.calc_VCC(mdot_AHU_kgpers[hour], T_sup_AHU_K[hour],
                                                                          T_re_AHU_K[hour], Qnom_VCC_W,
                                                                          number_of_VCC_chillers)
                result_AHU[1][7] += lca.ELEC_PRICE[hour] * VCC_to_AHU_operation['wdot_W']  # CHF
                result_AHU[1][8] += lca.EL_TO_CO2 * VCC_to_AHU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_AHU[1][9] += lca.EL_TO_OIL_EQ * VCC_to_AHU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_AHU_W[hour] = VCC_to_AHU_operation['q_cw_W']


                # 2: SC_FP + single-effect ACH
                FP_to_single_ACH_to_AHU_operation = chiller_absorption.calc_chiller_main(mdot_AHU_kgpers[hour], T_sup_AHU_K[hour],
                                                                              T_re_AHU_K[hour], T_hw_in_FP_C[hour],
                                                                              T_ground_K[hour], ACH_TYPE_SINGLE,
                                                                                          Qnom_ACH_W, locator, config)
                # add costs from electricity consumption
                el_for_FP_ACH_W = FP_to_single_ACH_to_AHU_operation['wdot_W'] + w_SC_FP_Wh[hour]
                result_AHU[2][7] += lca.ELEC_PRICE[hour] * el_for_FP_ACH_W  # CHF
                result_AHU[2][8] += lca.EL_TO_CO2 * el_for_FP_ACH_W * 3600E-6  # kgCO2
                result_AHU[2][9] += lca.EL_TO_OIL_EQ * el_for_FP_ACH_W * 3600E-6  # MJ-oil-eq

                # calculate load for CT and boilers
                q_CT_FP_to_single_ACH_to_AHU_W[hour] = FP_to_single_ACH_to_AHU_operation['q_cw_W']
                q_boiler_FP_to_single_ACH_to_AHU_W[hour] = (FP_to_single_ACH_to_AHU_operation['q_hw_W'] - q_sc_gen_FP_Wh[hour]) if (
                    q_sc_gen_FP_Wh[hour] >= 0) else FP_to_single_ACH_to_AHU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_FP_to_single_ACH_to_AHU_K[hour] = FP_to_single_ACH_to_AHU_operation['T_hw_out_C'] + 273.15

                # 3: SC_ET + single-effect ACH
                ET_to_single_ACH_to_AHU_operation = chiller_absorption.calc_chiller_main(mdot_AHU_kgpers[hour], T_sup_AHU_K[hour],
                                                                              T_re_AHU_K[hour], T_hw_in_ET_C[hour],
                                                                              T_ground_K[hour], ACH_TYPE_SINGLE,
                                                                                          Qnom_ACH_W, locator, config)
                # add costs from electricity consumption
                el_for_ET_ACH_W = ET_to_single_ACH_to_AHU_operation['wdot_W'] + w_SC_ET_Wh[hour]
                result_AHU[3][7] += lca.ELEC_PRICE[hour] * el_for_ET_ACH_W  # CHF
                result_AHU[3][8] += lca.EL_TO_CO2 * el_for_ET_ACH_W * 3600E-6  # kgCO2
                result_AHU[3][9] += lca.EL_TO_OIL_EQ * el_for_ET_ACH_W * 3600E-6  # MJ-oil-eq

                # calculate load for CT and boilers
                q_CT_ET_to_single_ACH_to_AHU_W[hour] = ET_to_single_ACH_to_AHU_operation['q_cw_W']
                q_burner_ET_to_single_ACH_to_AHU_W[hour] = ET_to_single_ACH_to_AHU_operation['q_hw_W'] - q_sc_gen_ET_Wh[hour] if (
                    q_sc_gen_ET_Wh[hour] >= 0) else ET_to_single_ACH_to_AHU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_ET_to_single_ACH_to_AHU_K[hour] = ET_to_single_ACH_to_AHU_operation['T_hw_out_C'] + 273.15

        ## Decentralized supply systems only supply to loads from ARU
        result_ARU = np.zeros((4, 10))
        # config 0: DX
        result_ARU[0][0] = 1
        # config 1: VCC to ARU
        result_ARU[1][1] = 1
        # config 2: single-effect ACH with FP to ARU
        result_ARU[2][2] = 1
        # config 3: single-effect ACH with ET to ARU
        result_ARU[3][3] = 1

        q_CT_VCC_to_ARU_W = np.zeros(8760)
        q_CT_FP_to_single_ACH_to_ARU_W = np.zeros(8760)
        q_boiler_FP_to_single_ACH_to_ARU_W = np.zeros(8760)
        q_burner_ET_to_single_ACH_to_ARU_W = np.zeros(8760)
        q_CT_ET_to_single_ACH_to_ARU_W = np.zeros(8760)
        T_re_boiler_FP_to_single_ACH_to_ARU_K = np.zeros(8760)
        T_re_boiler_ET_to_single_ACH_to_ARU_K = np.zeros(8760)

        if config.decentralized.ARUflag:
            print building_name, ' decentralized building simulation with configuration: ARU'

            if Qc_nom_combination_ARU_W <= max_VCC_chiller_size:
                Qnom_VCC_W = Qc_nom_combination_ARU_W
                number_of_VCC_chillers = 1
            else:
                number_of_VCC_chillers = int(ceil(Qc_nom_combination_ARU_W / max_VCC_chiller_size))
                Qnom_VCC_W = Qc_nom_combination_ARU_W / number_of_VCC_chillers

            if Qc_nom_combination_ARU_W <= max_ACH_chiller_size:
                Qnom_ACH_W = Qc_nom_combination_ARU_W
                number_of_ACH_chillers = 1
            else:
                number_of_ACH_chillers = int(ceil(Qc_nom_combination_ARU_W / max_ACH_chiller_size))
                Qnom_ACH_W = Qc_nom_combination_ARU_W / number_of_ACH_chillers

            # chiller operations for config 1-5
            for hour in range(8760):  # TODO: vectorize
                # modify return temperatures when there is no load
                T_re_ARU_K[hour] = T_re_ARU_K[hour] if T_re_ARU_K[hour] > 0 else T_sup_AHU_K[hour]

                # 0: DX
                DX_operation = dx.calc_DX(mdot_ARU_kgpers[hour], T_sup_ARU_K[hour], T_re_ARU_K[hour])
                result_ARU[0][7] += lca.ELEC_PRICE[hour] * DX_operation  # FIXME: a dummy value to rule out this configuration  # CHF
                result_ARU[0][8] += lca.EL_TO_CO2 * DX_operation  # FIXME: a dummy value to rule out this configuration  # kgCO2
                result_ARU[0][9] += lca.EL_TO_OIL_EQ * DX_operation  # FIXME: a dummy value to rule out this configuration  # MJ-oil-eq

                # 1: VCC
                VCC_to_ARU_operation = chiller_vapor_compression.calc_VCC(mdot_ARU_kgpers[hour], T_sup_ARU_K[hour],
                                                                          T_re_ARU_K[hour], Qnom_VCC_W,
                                                                          number_of_VCC_chillers)
                result_ARU[1][7] += lca.ELEC_PRICE[hour] * VCC_to_ARU_operation['wdot_W']  # CHF
                result_ARU[1][8] += lca.EL_TO_CO2 * VCC_to_ARU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_ARU[1][9] += lca.EL_TO_OIL_EQ * VCC_to_ARU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_ARU_W[hour] = VCC_to_ARU_operation['q_cw_W']

                # 2: SC_FP + single-effect ACH
                FP_to_single_ACH_to_ARU_operation = chiller_absorption.calc_chiller_main(mdot_ARU_kgpers[hour],
                                                                                          T_sup_ARU_K[hour],
                                                                                          T_re_ARU_K[hour],
                                                                                          T_hw_in_FP_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_TYPE_SINGLE,
                                                                                          Qnom_ACH_W,
                                                                                          locator, config)
                # add costs from electricity consumption
                el_for_FP_ACH_W = FP_to_single_ACH_to_ARU_operation['wdot_W'] + w_SC_FP_Wh[hour]
                result_ARU[2][7] += lca.ELEC_PRICE[hour] * el_for_FP_ACH_W  # CHF
                result_ARU[2][8] += lca.EL_TO_CO2 * el_for_FP_ACH_W * 3600E-6  # kgCO2
                result_ARU[2][9] += lca.EL_TO_OIL_EQ * el_for_FP_ACH_W * 3600E-6  # MJ-oil-eq

                # calculate load for CT and boilers
                q_CT_FP_to_single_ACH_to_ARU_W[hour] = FP_to_single_ACH_to_ARU_operation['q_cw_W']
                q_boiler_FP_to_single_ACH_to_ARU_W[hour] = FP_to_single_ACH_to_ARU_operation['q_hw_W'] - q_sc_gen_FP_Wh[
                    hour] if (
                        q_sc_gen_FP_Wh[hour] >= 0) else FP_to_single_ACH_to_ARU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_FP_to_single_ACH_to_ARU_K[hour] = FP_to_single_ACH_to_ARU_operation['T_hw_out_C'] + 273.15

                # 3: SC_ET + single-effect ACH
                ET_to_single_ACH_to_ARU_operation = chiller_absorption.calc_chiller_main(mdot_ARU_kgpers[hour],
                                                                                          T_sup_ARU_K[hour],
                                                                                          T_re_ARU_K[hour],
                                                                                          T_hw_in_ET_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_TYPE_SINGLE,
                                                                                          Qnom_ACH_W,
                                                                                          locator, config)
                # add costs from electricity consumption
                el_for_ET_ACH_W = ET_to_single_ACH_to_ARU_operation['wdot_W'] + w_SC_ET_Wh[hour]
                result_ARU[3][7] += lca.ELEC_PRICE[hour] * el_for_ET_ACH_W  # CHF
                result_ARU[3][8] += lca.EL_TO_CO2 * el_for_ET_ACH_W * 3600E-6  # kgCO2
                result_ARU[3][9] += lca.EL_TO_OIL_EQ * el_for_ET_ACH_W * 3600E-6  # MJ-oil-eq

                # calculate load for CT and boilers
                q_CT_ET_to_single_ACH_to_ARU_W[hour] = ET_to_single_ACH_to_ARU_operation['q_cw_W']
                q_burner_ET_to_single_ACH_to_ARU_W[hour] = ET_to_single_ACH_to_ARU_operation['q_hw_W'] - q_sc_gen_ET_Wh[
                    hour] if (
                        q_sc_gen_ET_Wh[hour] >= 0) else ET_to_single_ACH_to_ARU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_ET_to_single_ACH_to_ARU_K[hour] = ET_to_single_ACH_to_ARU_operation['T_hw_out_C'] + 273.15




        ## Decentralized supply systems only supply to loads from SCU
        result_SCU = np.zeros((4, 10))
        # config 0: DX
        result_SCU[0][0] = 1
        # config 1: VCC to SCU
        result_SCU[1][1] = 1
        # config 2: single-effect ACH with FP to SCU
        result_SCU[2][2] = 1
        # config 3: single-effect ACH with ET to SCU
        result_SCU[3][3] = 1

        q_CT_VCC_to_SCU_W = np.zeros(8760)
        q_CT_FP_to_single_ACH_to_SCU_W = np.zeros(8760)
        q_boiler_FP_to_single_ACH_to_SCU_W = np.zeros(8760)
        q_CT_ET_to_single_ACH_to_SCU_W = np.zeros(8760)
        q_burner_ET_to_single_ACH_to_SCU_W = np.zeros(8760)
        T_re_boiler_FP_to_single_ACH_to_SCU_K = np.zeros(8760)
        T_re_boiler_ET_to_single_ACH_to_SCU_K = np.zeros(8760)

        if config.decentralized.SCUflag:
            print building_name, ' decentralized building simulation with configuration: SCU'


            if Qc_nom_combination_SCU_W <= max_VCC_chiller_size:
                Qnom_VCC_W = Qc_nom_combination_SCU_W
                number_of_VCC_chillers = 1
            else:
                number_of_VCC_chillers = int(ceil(Qc_nom_combination_SCU_W / max_VCC_chiller_size))
                Qnom_VCC_W = Qc_nom_combination_SCU_W / number_of_VCC_chillers

            if Qc_nom_combination_SCU_W <= max_ACH_chiller_size:
                Qnom_ACH_W = Qc_nom_combination_SCU_W
                number_of_ACH_chillers = 1
            else:
                number_of_ACH_chillers = int(ceil(Qc_nom_combination_SCU_W / max_ACH_chiller_size))
                Qnom_ACH_W = Qc_nom_combination_SCU_W / number_of_ACH_chillers

            # chiller operations for config 1-5
            for hour in range(8760):  # TODO: vectorize
                # modify return temperatures when there is no load
                T_re_SCU_K[hour] = T_re_SCU_K[hour] if T_re_SCU_K[hour] > 0 else T_sup_SCU_K[hour]

                # 0: DX
                DX_operation = dx.calc_DX(mdot_SCU_kgpers[hour], T_sup_SCU_K[hour], T_re_SCU_K[hour])
                result_SCU[0][7] += lca.ELEC_PRICE[hour] * DX_operation  # FIXME: a dummy value to rule out this configuration  # CHF
                result_SCU[0][8] += lca.EL_TO_CO2 * DX_operation  # FIXME: a dummy value to rule out this configuration  # kgCO2
                result_SCU[0][9] += lca.EL_TO_OIL_EQ * DX_operation  # FIXME: a dummy value to rule out this configuration  # MJ-oil-eq

                # 1: VCC
                VCC_to_SCU_operation = chiller_vapor_compression.calc_VCC(mdot_SCU_kgpers[hour], T_sup_SCU_K[hour],
                                                                          T_re_SCU_K[hour], Qnom_VCC_W,
                                                                          number_of_VCC_chillers)
                result_SCU[1][7] += lca.ELEC_PRICE[hour] * VCC_to_SCU_operation['wdot_W']  # CHF
                result_SCU[1][8] += lca.EL_TO_CO2 * VCC_to_SCU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_SCU[1][9] += lca.EL_TO_OIL_EQ * VCC_to_SCU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_SCU_W[hour] = VCC_to_SCU_operation['q_cw_W']

                # 2: SC_FP + single-effect ACH
                FP_to_single_ACH_to_SCU_operation = chiller_absorption.calc_chiller_main(mdot_SCU_kgpers[hour],
                                                                                          T_sup_SCU_K[hour],
                                                                                          T_re_SCU_K[hour],
                                                                                          T_hw_in_FP_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_TYPE_SINGLE,
                                                                                          Qnom_ACH_W,
                                                                                          locator, config)
                # add costs from electricity consumption
                el_for_FP_ACH_W = FP_to_single_ACH_to_SCU_operation['wdot_W'] + w_SC_FP_Wh[hour]
                result_SCU[2][7] += lca.ELEC_PRICE[hour] * el_for_FP_ACH_W  # CHF
                result_SCU[2][8] += lca.EL_TO_CO2 * el_for_FP_ACH_W * 3600E-6  # kgCO2
                result_SCU[2][9] += lca.EL_TO_OIL_EQ * el_for_FP_ACH_W * 3600E-6  # MJ-oil-eq

                # calculate load for CT and boilers
                q_CT_FP_to_single_ACH_to_SCU_W[hour] = FP_to_single_ACH_to_SCU_operation['q_cw_W']
                q_boiler_FP_to_single_ACH_to_SCU_W[hour] = FP_to_single_ACH_to_SCU_operation['q_hw_W'] - q_sc_gen_FP_Wh[
                    hour] if (
                        q_sc_gen_FP_Wh[hour] >= 0) else FP_to_single_ACH_to_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_FP_to_single_ACH_to_SCU_K[hour] = FP_to_single_ACH_to_SCU_operation['T_hw_out_C'] + 273.15

                # 3: ET + single-effect ACH
                ET_to_single_ACH_to_SCU_operation = chiller_absorption.calc_chiller_main(mdot_SCU_kgpers[hour],
                                                                                          T_sup_SCU_K[hour],
                                                                                          T_re_SCU_K[hour],
                                                                                          T_hw_in_ET_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_TYPE_SINGLE,
                                                                                          Qnom_ACH_W,
                                                                                          locator, config)
                # add costs from electricity consumption
                el_for_ET_ACH_W = ET_to_single_ACH_to_SCU_operation['wdot_W'] + w_SC_ET_Wh[hour]
                result_SCU[3][7] += lca.ELEC_PRICE[hour] * el_for_ET_ACH_W  # CHF
                result_SCU[3][8] += lca.EL_TO_CO2 * el_for_ET_ACH_W * 3600E-6  # kgCO2
                result_SCU[3][9] += lca.EL_TO_OIL_EQ * el_for_ET_ACH_W * 3600E-6  # MJ-oil-eq

                # calculate load for CT and boilers
                q_CT_ET_to_single_ACH_to_SCU_W[hour] = ET_to_single_ACH_to_SCU_operation['q_cw_W']
                q_burner_ET_to_single_ACH_to_SCU_W[hour] = ET_to_single_ACH_to_SCU_operation['q_hw_W'] - q_sc_gen_ET_Wh[
                    hour] if (
                        q_sc_gen_ET_Wh[hour] >= 0) else ET_to_single_ACH_to_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_ET_to_single_ACH_to_SCU_K[hour] = ET_to_single_ACH_to_SCU_operation['T_hw_out_C'] + 273.15

        ## Decentralized supply systems only supply to loads from AHU & ARU
        result_AHU_ARU = np.zeros((4, 10))
        # config 0: DX
        result_AHU_ARU[0][0] = 1
        # config 1: VCC to AHU & ARU
        result_AHU_ARU[1][1] = 1
        # config 2: single-effect ACH with FP to AHU & ARU
        result_AHU_ARU[2][2] = 1
        # config 3: single-effect ACH with ET to AHU & ARU
        result_AHU_ARU[3][3] = 1

        q_CT_VCC_to_AHU_ARU_W = np.zeros(8760)
        q_CT_FP_to_single_ACH_to_AHU_ARU_W = np.zeros(8760)
        q_boiler_FP_to_single_ACH_to_AHU_ARU_W = np.zeros(8760)
        q_CT_ET_to_single_ACH_to_AHU_ARU_W = np.zeros(8760)
        q_burner_ET_to_single_ACH_to_AHU_ARU_W = np.zeros(8760)
        T_re_boiler_FP_to_single_ACH_to_AHU_ARU_K = np.zeros(8760)
        T_re_boiler_ET_to_single_ACH_to_AHU_ARU_K = np.zeros(8760)

        if config.decentralized.AHUARUflag:
            print building_name, ' decentralized building simulation with configuration: AHU + ARU'

            if Qc_nom_combination_AHU_ARU_W <= max_VCC_chiller_size:
                Qnom_VCC_W = Qc_nom_combination_AHU_ARU_W
                number_of_VCC_chillers = 1
            else:
                number_of_VCC_chillers = int(ceil(Qc_nom_combination_AHU_ARU_W / max_VCC_chiller_size))
                Qnom_VCC_W = Qc_nom_combination_AHU_ARU_W / number_of_VCC_chillers

            if Qc_nom_combination_AHU_ARU_W <= max_ACH_chiller_size:
                Qnom_ACH_W = Qc_nom_combination_AHU_ARU_W
                number_of_ACH_chillers = 1
            else:
                number_of_ACH_chillers = int(ceil(Qc_nom_combination_AHU_ARU_W / max_ACH_chiller_size))
                Qnom_ACH_W = Qc_nom_combination_AHU_ARU_W / number_of_ACH_chillers

            # chiller operations for config 1-5
            for hour in range(8760):  # TODO: vectorize
                # modify return temperatures when there is no load
                T_re_AHU_ARU_K[hour] = T_re_AHU_ARU_K[hour] if T_re_AHU_ARU_K[hour] > 0 else T_sup_AHU_ARU_K[hour]

                # 0: DX
                DX_operation = dx.calc_DX(mdot_AHU_ARU_kgpers[hour], T_sup_AHU_ARU_K[hour], T_re_AHU_ARU_K[hour])
                result_AHU_ARU[0][7] += lca.ELEC_PRICE[hour] * DX_operation  # FIXME: a dummy value to rule out this configuration  # CHF
                result_AHU_ARU[0][8] += lca.EL_TO_CO2 * DX_operation  # FIXME: a dummy value to rule out this configuration  # kgCO2
                result_AHU_ARU[0][9] += lca.EL_TO_OIL_EQ * DX_operation  # FIXME: a dummy value to rule out this configuration  # MJ-oil-eq

                # 1: VCC

                VCC_to_AHU_ARU_operation = chiller_vapor_compression.calc_VCC(mdot_AHU_ARU_kgpers[hour],
                                                                              T_sup_AHU_ARU_K[hour],
                                                                              T_re_AHU_ARU_K[hour], Qnom_VCC_W,
                                                                              number_of_VCC_chillers)
                result_AHU_ARU[1][7] += lca.ELEC_PRICE[hour] * VCC_to_AHU_ARU_operation['wdot_W']  # CHF
                result_AHU_ARU[1][8] += lca.EL_TO_CO2 * VCC_to_AHU_ARU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_AHU_ARU[1][9] += lca.EL_TO_OIL_EQ * VCC_to_AHU_ARU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_AHU_ARU_W[hour] = VCC_to_AHU_ARU_operation['q_cw_W']

                # 2: SC_FP + single-effect ACH
                FP_to_single_ACH_to_AHU_ARU_operation = chiller_absorption.calc_chiller_main(mdot_AHU_ARU_kgpers[hour],
                                                                                          T_sup_AHU_ARU_K[hour],
                                                                                          T_re_AHU_ARU_K[hour],
                                                                                          T_hw_in_FP_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_TYPE_SINGLE,
                                                                                              Qnom_ACH_W,
                                                                                              locator, config)
                # add costs from electricity consumption
                el_for_FP_ACH_W = FP_to_single_ACH_to_AHU_ARU_operation['wdot_W'] + w_SC_FP_Wh[hour]
                result_AHU_ARU[2][7] += lca.ELEC_PRICE[hour] * el_for_FP_ACH_W  # CHF
                result_AHU_ARU[2][8] += lca.EL_TO_CO2 * el_for_FP_ACH_W * 3600E-6  # kgCO2
                result_AHU_ARU[2][9] += lca.EL_TO_OIL_EQ * el_for_FP_ACH_W * 3600E-6  # MJ-oil-eq

                # calculate load for CT and boilers
                q_CT_FP_to_single_ACH_to_AHU_ARU_W[hour] = FP_to_single_ACH_to_AHU_ARU_operation['q_cw_W']
                q_boiler_FP_to_single_ACH_to_AHU_ARU_W[hour] = FP_to_single_ACH_to_AHU_ARU_operation['q_hw_W'] - q_sc_gen_FP_Wh[
                    hour] if (
                        q_sc_gen_FP_Wh[hour] >= 0) else FP_to_single_ACH_to_AHU_ARU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_FP_to_single_ACH_to_AHU_ARU_K[hour] = FP_to_single_ACH_to_AHU_ARU_operation['T_hw_out_C'] + 273.15

                # 3: SC_ET + single-effect ACH
                ET_to_single_ACH_to_AHU_ARU_operation = chiller_absorption.calc_chiller_main(mdot_AHU_ARU_kgpers[hour],
                                                                                          T_sup_AHU_ARU_K[hour],
                                                                                          T_re_AHU_ARU_K[hour],
                                                                                          T_hw_in_ET_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_TYPE_SINGLE,
                                                                                              Qnom_ACH_W,
                                                                                              locator, config)
                # add costs from electricity consumption
                el_for_ET_ACH_W = ET_to_single_ACH_to_AHU_ARU_operation['wdot_W'] + w_SC_ET_Wh[hour]
                result_AHU_ARU[3][7] += lca.ELEC_PRICE[hour] * el_for_ET_ACH_W  # CHF
                result_AHU_ARU[3][8] += lca.EL_TO_CO2 * el_for_ET_ACH_W * 3600E-6  # kgCO2
                result_AHU_ARU[3][9] += lca.EL_TO_OIL_EQ * el_for_ET_ACH_W * 3600E-6  # MJ-oil-eq

                # calculate load for CT and boilers
                q_CT_ET_to_single_ACH_to_AHU_ARU_W[hour] = ET_to_single_ACH_to_AHU_ARU_operation['q_cw_W']
                q_burner_ET_to_single_ACH_to_AHU_ARU_W[hour] = ET_to_single_ACH_to_AHU_ARU_operation['q_hw_W'] - q_sc_gen_ET_Wh[
                    hour] if (
                        q_sc_gen_ET_Wh[hour] >= 0) else ET_to_single_ACH_to_AHU_ARU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_ET_to_single_ACH_to_AHU_ARU_K[hour] = ET_to_single_ACH_to_AHU_ARU_operation['T_hw_out_C'] + 273.15

        ## Decentralized supply systems only supply to loads from AHU & SCU
        result_AHU_SCU = np.zeros((4, 10))
        # config 0: DX
        result_AHU_SCU[0][0] = 1
        # config 1: VCC to AHU & SCU
        result_AHU_SCU[1][1] = 1
        # config 2: single-effect ACH with FP to AHU & SCU
        result_AHU_SCU[2][2] = 1
        # config 3: single-effect ACH with ET to AHU & SCU
        result_AHU_SCU[3][3] = 1

        q_CT_VCC_to_AHU_SCU_W = np.zeros(8760)
        q_CT_FP_tosingle_ACH_to_AHU_SCU_W = np.zeros(8760)
        q_boiler_FP_to_single_ACH_to_AHU_SCU_W = np.zeros(8760)
        q_CT_ET_to_single_ACH_to_AHU_SCU_W = np.zeros(8760)
        q_burner_ET_to_single_ACH_to_AHU_SCU_W = np.zeros(8760)
        T_re_boiler_FP_to_single_ACH_to_AHU_SCU_K = np.zeros(8760)
        T_re_boiler_ET_to_single_ACH_to_AHU_SCU_K = np.zeros(8760)

        if config.decentralized.AHUSCUflag:
            print building_name, ' decentralized building simulation with configuration: AHU + SCU'


            if Qc_nom_combination_AHU_SCU_W <= max_VCC_chiller_size:
                Qnom_VCC_W = Qc_nom_combination_AHU_SCU_W
                number_of_VCC_chillers = 1
            else:
                number_of_VCC_chillers = int(ceil(Qc_nom_combination_AHU_SCU_W / max_VCC_chiller_size))
                Qnom_VCC_W = Qc_nom_combination_AHU_SCU_W / number_of_VCC_chillers

            if Qc_nom_combination_AHU_SCU_W <= max_ACH_chiller_size:
                Qnom_ACH_W = Qc_nom_combination_AHU_SCU_W
                number_of_ACH_chillers = 1
            else:
                number_of_ACH_chillers = int(ceil(Qc_nom_combination_AHU_SCU_W / max_ACH_chiller_size))
                Qnom_ACH_W = Qc_nom_combination_AHU_SCU_W / number_of_ACH_chillers

            # chiller operations for config 1-5
            for hour in range(8760):  # TODO: vectorize
                # modify return temperatures when there is no load
                T_re_AHU_SCU_K[hour] = T_re_AHU_SCU_K[hour] if T_re_AHU_SCU_K[hour] > 0 else T_sup_AHU_SCU_K[hour]

                # 0: DX
                DX_operation = dx.calc_DX(mdot_AHU_SCU_kgpers[hour], T_sup_AHU_SCU_K[hour], T_re_AHU_SCU_K[hour])
                result_AHU_SCU[0][7] += lca.ELEC_PRICE[hour] * DX_operation  # FIXME: a dummy value to rule out this configuration  # CHF
                result_AHU_SCU[0][8] += lca.EL_TO_CO2 * DX_operation  # FIXME: a dummy value to rule out this configuration  # kgCO2
                result_AHU_SCU[0][9] += lca.EL_TO_OIL_EQ * DX_operation  # FIXME: a dummy value to rule out this configuration  # MJ-oil-eq

                # 1: VCC
                VCC_to_AHU_SCU_operation = chiller_vapor_compression.calc_VCC(mdot_AHU_SCU_kgpers[hour],
                                                                              T_sup_AHU_SCU_K[hour],
                                                                              T_re_AHU_SCU_K[hour], Qnom_VCC_W,
                                                                              number_of_VCC_chillers)
                result_AHU_SCU[1][7] += lca.ELEC_PRICE[hour] * VCC_to_AHU_SCU_operation['wdot_W']  # CHF
                result_AHU_SCU[1][8] += lca.EL_TO_CO2 * VCC_to_AHU_SCU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_AHU_SCU[1][9] += lca.EL_TO_OIL_EQ * VCC_to_AHU_SCU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_AHU_SCU_W[hour] = VCC_to_AHU_SCU_operation['q_cw_W']

                # 2: SC_FP + single-effect ACH
                FP_to_single_ACH_to_AHU_SCU_operation = chiller_absorption.calc_chiller_main(mdot_AHU_SCU_kgpers[hour],
                                                                                          T_sup_AHU_SCU_K[hour],
                                                                                          T_re_AHU_SCU_K[hour],
                                                                                          T_hw_in_FP_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_TYPE_SINGLE,
                                                                                              Qnom_ACH_W,
                                                                                              locator, config)
                # add costs from electricity consumption
                el_for_FP_ACH_W = FP_to_single_ACH_to_AHU_SCU_operation['wdot_W'] + w_SC_FP_Wh[hour]
                result_AHU_SCU[2][7] += lca.ELEC_PRICE[hour] * el_for_FP_ACH_W  # CHF
                result_AHU_SCU[2][8] += lca.EL_TO_CO2 * el_for_FP_ACH_W * 3600E-6  # kgCO2
                result_AHU_SCU[2][9] += lca.EL_TO_OIL_EQ * el_for_FP_ACH_W * 3600E-6  # MJ-oil-eq

                # calculate load for CT and boilers
                q_CT_FP_tosingle_ACH_to_AHU_SCU_W[hour] = FP_to_single_ACH_to_AHU_SCU_operation['q_cw_W']
                q_boiler_FP_to_single_ACH_to_AHU_SCU_W[hour] = FP_to_single_ACH_to_AHU_SCU_operation['q_hw_W'] - q_sc_gen_FP_Wh[
                    hour] if (
                        q_sc_gen_FP_Wh[hour] >= 0) else FP_to_single_ACH_to_AHU_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_FP_to_single_ACH_to_AHU_SCU_K[hour] = FP_to_single_ACH_to_AHU_SCU_operation['T_hw_out_C'] + 273.15

                # 3: ET + single-effect ACH
                ET_to_single_effect_ACH_to_AHU_SCU_operation = chiller_absorption.calc_chiller_main(mdot_AHU_SCU_kgpers[hour],
                                                                                          T_sup_AHU_SCU_K[hour],
                                                                                          T_re_AHU_SCU_K[hour],
                                                                                          T_hw_in_ET_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_TYPE_SINGLE,
                                                                                              Qnom_ACH_W,
                                                                                              locator, config)
                # add costs from electricity consumption
                el_for_ET_ACH_W = ET_to_single_effect_ACH_to_AHU_SCU_operation['wdot_W'] + w_SC_ET_Wh[hour]
                result_AHU_SCU[3][7] += lca.ELEC_PRICE[hour] * el_for_ET_ACH_W  # CHF
                result_AHU_SCU[3][8] += lca.EL_TO_CO2 * el_for_ET_ACH_W * 3600E-6  # kgCO2
                result_AHU_SCU[3][9] += lca.EL_TO_OIL_EQ * el_for_ET_ACH_W * 3600E-6  # MJ-oil-eq

                # calculate load for CT and boilers
                q_CT_ET_to_single_ACH_to_AHU_SCU_W[hour] = ET_to_single_effect_ACH_to_AHU_SCU_operation['q_cw_W']
                q_burner_ET_to_single_ACH_to_AHU_SCU_W[hour] = ET_to_single_effect_ACH_to_AHU_SCU_operation['q_hw_W'] - q_sc_gen_ET_Wh[
                    hour] if (
                        q_sc_gen_ET_Wh[hour] >= 0) else ET_to_single_effect_ACH_to_AHU_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_ET_to_single_ACH_to_AHU_SCU_K[hour] = ET_to_single_effect_ACH_to_AHU_SCU_operation['T_hw_out_C'] + 273.15


        ## Decentralized supply systems only supply to loads from ARU & SCU
        result_ARU_SCU = np.zeros((4, 10))
        # config 0: DX to ARU & SCU
        result_ARU_SCU[0][0] = 1
        # config 1: VCC to ARU & SCU
        result_ARU_SCU[1][1] = 1
        # config 2: single-effect ACH with FP to ARU & SCU
        result_ARU_SCU[2][2] = 1
        # config 3: single-effect ACH with ET to ARU & SCU
        result_ARU_SCU[3][3] = 1

        q_CT_VCC_to_ARU_SCU_W = np.zeros(8760)
        q_CT_FP_to_single_ACH_to_ARU_SCU_W = np.zeros(8760)
        q_boiler_FP_to_single_ACH_to_ARU_SCU_W = np.zeros(8760)
        q_CT_ET_to_single_ACH_to_ARU_SCU_W = np.zeros(8760)
        q_burner_ET_to_single_ACH_to_ARU_SCU_W = np.zeros(8760)
        T_re_boiler_FP_to_single_ACH_to_ARU_SCU_K = np.zeros(8760)
        T_re_boiler_ET_to_single_ACH_to_ARU_SCU_K = np.zeros(8760)

        if config.decentralized.ARUSCUflag:
            print building_name, ' decentralized building simulation with configuration: ARU + SCU'

            if Qc_nom_combination_ARU_SCU_W <= max_VCC_chiller_size:
                Qnom_VCC_W = Qc_nom_combination_ARU_SCU_W
                number_of_VCC_chillers = 1
            else:
                number_of_VCC_chillers = int(ceil(Qc_nom_combination_ARU_SCU_W / max_VCC_chiller_size))
                Qnom_VCC_W = Qc_nom_combination_ARU_SCU_W / number_of_VCC_chillers

            if Qc_nom_combination_ARU_SCU_W <= max_ACH_chiller_size:
                Qnom_ACH_W = Qc_nom_combination_ARU_SCU_W
                number_of_ACH_chillers = 1
            else:
                number_of_ACH_chillers = int(ceil(Qc_nom_combination_ARU_SCU_W / max_ACH_chiller_size))
                Qnom_ACH_W = Qc_nom_combination_ARU_SCU_W / number_of_ACH_chillers
            # chiller operations for config 1-5
            for hour in range(8760):  # TODO: vectorize
                # modify return temperatures when there is no load
                T_re_ARU_SCU_K[hour] = T_re_ARU_SCU_K[hour] if T_re_ARU_SCU_K[hour] > 0 else T_sup_ARU_SCU_K[hour]

                # 0: DX
                DX_operation = dx.calc_DX(mdot_ARU_SCU_kgpers[hour], T_sup_ARU_SCU_K[hour], T_re_ARU_SCU_K[hour])
                result_ARU_SCU[0][7] += lca.ELEC_PRICE[hour] * DX_operation  # FIXME: a dummy value to rule out this configuration  # CHF
                result_ARU_SCU[0][8] += lca.EL_TO_CO2 * DX_operation  # FIXME: a dummy value to rule out this configuration  # kgCO2
                result_ARU_SCU[0][9] += lca.EL_TO_OIL_EQ * DX_operation  # FIXME: a dummy value to rule out this configuration  # MJ-oil-eq

                # 1: VCC
                VCC_to_ARU_SCU_operation = chiller_vapor_compression.calc_VCC(mdot_ARU_SCU_kgpers[hour],
                                                                              T_sup_ARU_SCU_K[hour],
                                                                              T_re_ARU_SCU_K[hour], Qnom_VCC_W,
                                                                              number_of_VCC_chillers)
                result_ARU_SCU[1][7] += lca.ELEC_PRICE[hour] * VCC_to_ARU_SCU_operation['wdot_W']  # CHF
                result_ARU_SCU[1][8] += lca.EL_TO_CO2 * VCC_to_ARU_SCU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_ARU_SCU[1][9] += lca.EL_TO_OIL_EQ * VCC_to_ARU_SCU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_ARU_SCU_W[hour] = VCC_to_ARU_SCU_operation['q_cw_W']

                # 2: SC_FP + single-effect ACH
                FP_to_single_ACH_to_ARU_SCU_operation = chiller_absorption.calc_chiller_main(mdot_ARU_SCU_kgpers[hour],
                                                                                          T_sup_ARU_SCU_K[hour],
                                                                                          T_re_ARU_SCU_K[hour],
                                                                                          T_hw_in_FP_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_TYPE_SINGLE,
                                                                                              Qnom_ACH_W,
                                                                                              locator, config)
                # add costs from electricity consumption
                el_for_FP_ACH_W = FP_to_single_ACH_to_ARU_SCU_operation['wdot_W'] + w_SC_FP_Wh[hour]
                result_ARU_SCU[2][7] += lca.ELEC_PRICE[hour] * el_for_FP_ACH_W  # CHF
                result_ARU_SCU[2][8] += lca.EL_TO_CO2 * el_for_FP_ACH_W * 3600E-6  # kgCO2
                result_ARU_SCU[2][9] += lca.EL_TO_OIL_EQ * el_for_FP_ACH_W * 3600E-6  # MJ-oil-eq

                # calculate load for CT and boilers
                q_CT_FP_to_single_ACH_to_ARU_SCU_W[hour] = FP_to_single_ACH_to_ARU_SCU_operation['q_cw_W']
                q_boiler_FP_to_single_ACH_to_ARU_SCU_W[hour] = FP_to_single_ACH_to_ARU_SCU_operation['q_hw_W'] - q_sc_gen_FP_Wh[
                    hour] if (
                        q_sc_gen_FP_Wh[hour] >= 0) else FP_to_single_ACH_to_ARU_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_FP_to_single_ACH_to_ARU_SCU_K[hour] = FP_to_single_ACH_to_ARU_SCU_operation['T_hw_out_C'] + 273.15

                # 3: ET + single-effect ACH
                ET_to_single_ACH_to_ARU_SCU_operation = chiller_absorption.calc_chiller_main(mdot_ARU_SCU_kgpers[hour],
                                                                                          T_sup_ARU_SCU_K[hour],
                                                                                          T_re_ARU_SCU_K[hour],
                                                                                          T_hw_in_ET_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_TYPE_SINGLE,
                                                                                              Qnom_ACH_W,
                                                                                              locator, config)
                # add costs from electricity consumption
                el_for_ET_ACH_W = ET_to_single_ACH_to_ARU_SCU_operation['wdot_W'] + w_SC_ET_Wh[hour]
                result_ARU_SCU[3][7] += lca.ELEC_PRICE[hour] * el_for_ET_ACH_W  # CHF
                result_ARU_SCU[3][8] += lca.EL_TO_CO2 * el_for_ET_ACH_W * 3600E-6  # kgCO2
                result_ARU_SCU[3][9] += lca.EL_TO_OIL_EQ * el_for_ET_ACH_W * 3600E-6  # MJ-oil-eq

                # calculate load for CT and boilers
                q_CT_ET_to_single_ACH_to_ARU_SCU_W[hour] = ET_to_single_ACH_to_ARU_SCU_operation['q_cw_W']
                q_burner_ET_to_single_ACH_to_ARU_SCU_W[hour] = ET_to_single_ACH_to_ARU_SCU_operation['q_hw_W'] - q_sc_gen_ET_Wh[
                    hour] if (
                        q_sc_gen_ET_Wh[hour] >= 0) else ET_to_single_ACH_to_ARU_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_ET_to_single_ACH_to_ARU_SCU_K[hour] = ET_to_single_ACH_to_ARU_SCU_operation['T_hw_out_C'] + 273.15

        ## Decentralized supply systems supply to loads from AHU & ARU & SCU
        result_AHU_ARU_SCU = np.zeros((6, 10))
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

        q_CT_VCC_to_AHU_ARU_SCU_W = np.zeros(8760)
        q_CT_VCC_to_AHU_ARU_and_VCC_to_SCU_W = np.zeros(8760)
        q_CT_VCC_to_AHU_ARU_and_single_ACH_to_SCU_W = np.zeros(8760)
        q_CT_FP_to_single_ACH_to_AHU_ARU_SCU_W = np.zeros(8760)
        q_boiler_FP_to_single_ACH_to_AHU_ARU_SCU_W = np.zeros(8760)
        q_CT_ET_to_single_ACH_to_AHU_ARU_SCU_W = np.zeros(8760)
        q_burner_ET_single_ACH_to_AHU_ARU_SCU_W = np.zeros(8760)
        q_boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_W = np.zeros(8760)
        T_re_boiler_FP_to_single_ACH_to_AHU_ARU_SCU_K = np.zeros(8760)
        T_re_boiler_ET_to_single_ACH_to_AHU_ARU_SCU_K = np.zeros(8760)
        T_re_boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_K = np.zeros(8760)

        if True:  # for the case with AHU + ARU + SCU scenario. this should always be present

            print building_name, ' decentralized building simulation with configuration: AHU + ARU + SCU'

            if Qc_nom_combination_AHU_ARU_SCU_W <= max_VCC_chiller_size:
                Qnom_VCC_AHU_ARU_SCU_W = Qc_nom_combination_AHU_ARU_SCU_W
                number_of_VCC_AHU_ARU_SCU_chillers = 1
            else:
                number_of_VCC_AHU_ARU_SCU_chillers = int(ceil(Qc_nom_combination_AHU_ARU_SCU_W / max_VCC_chiller_size))
                Qnom_VCC_AHU_ARU_SCU_W = Qc_nom_combination_AHU_ARU_SCU_W / number_of_VCC_AHU_ARU_SCU_chillers

            if Qc_nom_combination_AHU_ARU_SCU_W <= max_ACH_chiller_size:
                Qnom_ACH_AHU_ARU_SCU_W = Qc_nom_combination_AHU_ARU_SCU_W
                number_of_ACH_AHU_ARU_SCU_chillers = 1
            else:
                number_of_ACH_AHU_ARU_SCU_chillers = int(ceil(Qc_nom_combination_AHU_ARU_SCU_W / max_ACH_chiller_size))
                Qnom_ACH_AHU_ARU_SCU_W = Qc_nom_combination_AHU_ARU_SCU_W / number_of_ACH_AHU_ARU_SCU_chillers

            if Qc_nom_combination_SCU_W <= max_VCC_chiller_size:
                Qnom_VCC_SCU_W = Qc_nom_combination_SCU_W
                number_of_VCC_SCU_chillers = 1
            else:
                number_of_VCC_SCU_chillers = int(ceil(Qc_nom_combination_SCU_W / max_VCC_chiller_size))
                Qnom_VCC_SCU_W = Qc_nom_combination_SCU_W / number_of_VCC_SCU_chillers

            if Qc_nom_combination_SCU_W <= max_ACH_chiller_size:
                Qnom_ACH_SCU_W = Qc_nom_combination_SCU_W
                number_of_ACH_SCU_chillers = 1
            else:
                number_of_ACH_SCU_chillers = int(ceil(Qc_nom_combination_SCU_W / max_ACH_chiller_size))
                Qnom_ACH_SCU_W = Qc_nom_combination_SCU_W / number_of_ACH_SCU_chillers

            if Qc_nom_combination_AHU_ARU_W <= max_VCC_chiller_size:
                Qnom_VCC_AHU_ARU_W = Qc_nom_combination_AHU_ARU_W
                number_of_VCC_AHU_ARU_chillers = 1
            else:
                number_of_VCC_AHU_ARU_chillers = int(ceil(Qc_nom_combination_AHU_ARU_W / max_VCC_chiller_size))
                Qnom_VCC_AHU_ARU_W = Qc_nom_combination_AHU_ARU_W / number_of_VCC_AHU_ARU_chillers

            if Qc_nom_combination_AHU_ARU_W <= max_ACH_chiller_size:
                Qnom_ACH_AHU_ARU_W = Qc_nom_combination_AHU_ARU_W
                number_of_ACH_AHU_ARU_chillers = 1
            else:
                number_of_ACH_AHU_ARU_chillers = int(ceil(Qc_nom_combination_AHU_ARU_W / max_ACH_chiller_size))
                Qnom_ACH_AHU_ARU_W = Qc_nom_combination_AHU_ARU_W / number_of_ACH_AHU_ARU_chillers

            # chiller operations for config 1-5
            for hour in range(8760):  # TODO: vectorize
                # modify return temperatures when there is no load
                T_re_AHU_ARU_SCU_K[hour] = T_re_AHU_ARU_SCU_K[hour] if T_re_AHU_ARU_SCU_K[hour] > 0 else \
                T_sup_AHU_ARU_SCU_K[hour]

                # 0: DX
                DX_operation = dx.calc_DX(mdot_AHU_ARU_SCU_kgpers[hour], T_sup_AHU_ARU_SCU_K[hour], T_re_AHU_ARU_SCU_K[hour])
                result_AHU_ARU_SCU[0][7] += lca.ELEC_PRICE[hour] * DX_operation  # FIXME: a dummy value to rule out this configuration  # CHF
                result_AHU_ARU_SCU[0][8] += lca.EL_TO_CO2 * DX_operation  # FIXME: a dummy value to rule out this configuration  # kgCO2
                result_AHU_ARU_SCU[0][9] += lca.EL_TO_OIL_EQ * DX_operation  # FIXME: a dummy value to rule out this configuration  # MJ-oil-eq

                # 1: VCC (AHU + ARU + SCU) + CT
                VCC_to_AHU_ARU_SCU_operation = chiller_vapor_compression.calc_VCC(mdot_AHU_ARU_SCU_kgpers[hour],
                                                                                  T_sup_AHU_ARU_SCU_K[hour],
                                                                                  T_re_AHU_ARU_SCU_K[hour],
                                                                                  Qnom_VCC_AHU_ARU_SCU_W,
                                                                                  number_of_VCC_AHU_ARU_SCU_chillers)
                result_AHU_ARU_SCU[1][7] += lca.ELEC_PRICE[hour] * VCC_to_AHU_ARU_SCU_operation['wdot_W']  # CHF
                result_AHU_ARU_SCU[1][8] += lca.EL_TO_CO2 * VCC_to_AHU_ARU_SCU_operation['wdot_W'] * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[1][9] += lca.EL_TO_OIL_EQ * VCC_to_AHU_ARU_SCU_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_AHU_ARU_SCU_W[hour] = VCC_to_AHU_ARU_SCU_operation['q_cw_W']

                # 2: SC_FP + single-effect ACH (AHU + ARU + SCU) + CT + Boiler + SC_FP
                SC_FP_to_single_ACH_to_AHU_ARU_SCU_operation = chiller_absorption.calc_chiller_main(mdot_AHU_ARU_SCU_kgpers[hour],
                                                                                              T_sup_AHU_ARU_SCU_K[hour],
                                                                                              T_re_AHU_ARU_SCU_K[hour],
                                                                                              T_hw_in_FP_C[hour],
                                                                                              T_ground_K[hour],
                                                                                              ACH_TYPE_SINGLE,
                                                                                              Qnom_ACH_AHU_ARU_SCU_W,
                                                                                              locator, config)
                # add costs from electricity consumption
                el_for_FP_ACH_W = SC_FP_to_single_ACH_to_AHU_ARU_SCU_operation['wdot_W'] + w_SC_FP_Wh[hour]
                result_AHU_ARU_SCU[2][7] += lca.ELEC_PRICE[hour] * el_for_FP_ACH_W  # CHF
                result_AHU_ARU_SCU[2][8] += lca.EL_TO_CO2 * el_for_FP_ACH_W * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[2][9] += lca.EL_TO_OIL_EQ * el_for_FP_ACH_W * 3600E-6  # MJ-oil-eq

                # calculate load for CT and boilers
                q_CT_FP_to_single_ACH_to_AHU_ARU_SCU_W[hour] = SC_FP_to_single_ACH_to_AHU_ARU_SCU_operation['q_cw_W']
                q_boiler_FP_to_single_ACH_to_AHU_ARU_SCU_W[hour] = SC_FP_to_single_ACH_to_AHU_ARU_SCU_operation['q_hw_W'] - \
                                                         q_sc_gen_FP_Wh[
                                                             hour] if (
                        q_sc_gen_FP_Wh[hour] >= 0) else SC_FP_to_single_ACH_to_AHU_ARU_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_FP_to_single_ACH_to_AHU_ARU_SCU_K[hour] = SC_FP_to_single_ACH_to_AHU_ARU_SCU_operation[
                                                                'T_hw_out_C'] + 273.15

                # 3: SC_ET + single-effect ACH (AHU + ARU + SCU) + CT + Boiler + SC_ET
                ET_to_single_ACH_to_AHU_ARU_SCU_operation = chiller_absorption.calc_chiller_main(mdot_AHU_ARU_SCU_kgpers[hour],
                                                                                              T_sup_AHU_ARU_SCU_K[hour],
                                                                                              T_re_AHU_ARU_SCU_K[hour],
                                                                                              T_hw_in_ET_C[hour],
                                                                                              T_ground_K[hour],
                                                                                              ACH_TYPE_SINGLE,
                                                                                              Qnom_ACH_AHU_ARU_SCU_W,
                                                                                              locator, config)
                # add costs from electricity consumption
                el_for_ET_ACH_W = ET_to_single_ACH_to_AHU_ARU_SCU_operation['wdot_W'] + w_SC_ET_Wh[hour]
                result_AHU_ARU_SCU[3][7] += lca.ELEC_PRICE[hour] * el_for_ET_ACH_W  # CHF
                result_AHU_ARU_SCU[3][8] += lca.EL_TO_CO2 * el_for_ET_ACH_W * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[3][9] += lca.EL_TO_OIL_EQ * el_for_ET_ACH_W * 3600E-6  # MJ-oil-eq

                # calculate load for CT and burners
                q_CT_ET_to_single_ACH_to_AHU_ARU_SCU_W[hour] = ET_to_single_ACH_to_AHU_ARU_SCU_operation['q_cw_W']
                q_burner_ET_single_ACH_to_AHU_ARU_SCU_W[hour] = ET_to_single_ACH_to_AHU_ARU_SCU_operation['q_hw_W'] - \
                                                         q_sc_gen_ET_Wh[
                                                             hour] if (
                        q_sc_gen_ET_Wh[hour] >= 0) else ET_to_single_ACH_to_AHU_ARU_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_ET_to_single_ACH_to_AHU_ARU_SCU_K[hour] = ET_to_single_ACH_to_AHU_ARU_SCU_operation[
                                                                'T_hw_out_C'] + 273.15

                # 4: VCC (AHU + ARU) + VCC (SCU) + CT
                VCC_to_AHU_ARU_operation = chiller_vapor_compression.calc_VCC(mdot_AHU_ARU_kgpers[hour],
                                                                              T_sup_AHU_ARU_K[hour],
                                                                              T_re_AHU_ARU_K[hour], Qnom_VCC_AHU_ARU_W,
                                                                              number_of_VCC_AHU_ARU_chillers)
                VCC_to_SCU_operation = chiller_vapor_compression.calc_VCC(mdot_SCU_kgpers[hour], T_sup_SCU_K[hour],
                                                                          T_re_SCU_K[hour], Qnom_VCC_SCU_W,
                                                                          number_of_VCC_SCU_chillers)
                result_AHU_ARU_SCU[4][7] += lca.ELEC_PRICE[hour] * (
                            VCC_to_AHU_ARU_operation['wdot_W'] + VCC_to_SCU_operation['wdot_W'])  # CHF
                result_AHU_ARU_SCU[4][8] += lca.EL_TO_CO2 * (
                            VCC_to_AHU_ARU_operation['wdot_W'] + VCC_to_SCU_operation['wdot_W']) * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[4][9] += lca.EL_TO_OIL_EQ * (
                            VCC_to_AHU_ARU_operation['wdot_W'] + VCC_to_SCU_operation['wdot_W']) * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_AHU_ARU_and_VCC_to_SCU_W[hour] = (
                            VCC_to_AHU_ARU_operation['q_cw_W'] + VCC_to_SCU_operation['q_cw_W'])


                # 5: VCC (AHU + ARU) + ACH (SCU) + CT
                FP_to_single_ACH_to_SCU_operation = chiller_absorption.calc_chiller_main(mdot_SCU_kgpers[hour],
                                                                                          T_sup_SCU_K[hour],
                                                                                          T_re_SCU_K[hour],
                                                                                          T_hw_in_FP_C[hour],
                                                                                          T_ground_K[hour],
                                                                                          ACH_TYPE_SINGLE,
                                                                                          Qnom_ACH_SCU_W,
                                                                                          locator, config)

                el_for_FP_ACH_W = VCC_to_AHU_ARU_operation['wdot_W'] + FP_to_single_ACH_to_SCU_operation['wdot_W'] + w_SC_FP_Wh[hour]
                result_AHU_ARU_SCU[5][7] += lca.ELEC_PRICE[hour] * el_for_FP_ACH_W  # CHF
                result_AHU_ARU_SCU[5][8] += lca.EL_TO_CO2 * el_for_FP_ACH_W * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[5][9] += lca.EL_TO_OIL_EQ * el_for_FP_ACH_W * 3600E-6  # MJ-oil-eq
                q_CT_VCC_to_AHU_ARU_and_single_ACH_to_SCU_W[hour] = (VCC_to_AHU_ARU_operation['q_cw_W'] + FP_to_single_ACH_to_SCU_operation['q_cw_W'])
                # calculate load for CT and boilers
                q_boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_W[hour] = FP_to_single_ACH_to_SCU_operation['q_hw_W'] - \
                                                         q_sc_gen_FP_Wh[
                                                             hour] if (
                        q_sc_gen_FP_Wh[hour] >= 0) else FP_to_single_ACH_to_SCU_operation['q_hw_W']
                # TODO: this is assuming the mdot in SC is higher than hot water in the generator
                T_re_boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_K[hour] = FP_to_single_ACH_to_SCU_operation[
                                                                'T_hw_out_C'] + 273.15


        ## Calculate Cooling towers and Boilers operation

        # sizing of CT
        CT_VCC_to_AHU_nom_size_W = np.max(q_CT_VCC_to_AHU_W) * (1 + SIZING_MARGIN)
        CT_FP_to_single_ACH_to_AHU_nom_size_W = np.max(q_CT_FP_to_single_ACH_to_AHU_W) * (1 + SIZING_MARGIN)
        CT_ET_to_single_ACH_to_AHU_nom_size_W = np.max(q_CT_ET_to_single_ACH_to_AHU_W) * (1 + SIZING_MARGIN)

        CT_VCC_to_ARU_nom_size_W = np.max(q_CT_VCC_to_ARU_W) * (1 + SIZING_MARGIN)
        CT_FP_to_single_ACH_to_ARU_nom_size_W = np.max(q_CT_FP_to_single_ACH_to_ARU_W) * (1 + SIZING_MARGIN)
        CT_ET_to_single_ACH_to_ARU_nom_size_W = np.max(q_CT_ET_to_single_ACH_to_ARU_W) * (1 + SIZING_MARGIN)

        CT_VCC_to_SCU_nom_size_W = np.max(q_CT_VCC_to_SCU_W) * (1 + SIZING_MARGIN)
        CT_FP_to_single_ACH_to_SCU_nom_size_W = np.max(q_CT_FP_to_single_ACH_to_SCU_W) * (1 + SIZING_MARGIN)
        CT_ET_to_single_ACH_to_SCU_nom_size_W = np.max(q_CT_ET_to_single_ACH_to_SCU_W) * (1 + SIZING_MARGIN)

        CT_VCC_to_AHU_ARU_nom_size_W = np.max(q_CT_VCC_to_AHU_ARU_W) * (1 + SIZING_MARGIN)
        CT_FP_to_single_ACH_to_AHU_ARU_nom_size_W = np.max(q_CT_FP_to_single_ACH_to_AHU_ARU_W) * (1 + SIZING_MARGIN)
        CT_ET_to_single_ACH_to_AHU_ARU_nom_size_W = np.max(q_CT_ET_to_single_ACH_to_AHU_ARU_W) * (1 + SIZING_MARGIN)

        CT_VCC_to_AHU_SCU_nom_size_W = np.max(q_CT_VCC_to_AHU_SCU_W) * (1 + SIZING_MARGIN)
        CT_single_ACH_to_AHU_SCU_nom_size_W = np.max(q_CT_FP_tosingle_ACH_to_AHU_SCU_W) * (1 + SIZING_MARGIN)
        CT_ET_to_single_ACH_to_AHU_SCU_nom_size_W = np.max(q_CT_ET_to_single_ACH_to_AHU_SCU_W) * (1 + SIZING_MARGIN)

        CT_VCC_to_ARU_SCU_nom_size_W = np.max(q_CT_VCC_to_ARU_SCU_W) * (1 + SIZING_MARGIN)
        CT_FP_to_single_ACH_to_ARU_SCU_nom_size_W = np.max(q_CT_FP_to_single_ACH_to_ARU_SCU_W) * (1 + SIZING_MARGIN)
        CT_ET_to_single_ACH_to_ARU_SCU_nom_size_W = np.max(q_CT_ET_to_single_ACH_to_ARU_SCU_W) * (1 + SIZING_MARGIN)

        CT_VCC_to_AHU_ARU_SCU_nom_size_W = np.max(q_CT_VCC_to_AHU_ARU_SCU_W) * (1 + SIZING_MARGIN)
        CT_FP_to_single_ACH_to_AHU_ARU_SCU_nom_size_W = np.max(q_CT_FP_to_single_ACH_to_AHU_ARU_SCU_W) * (1 + SIZING_MARGIN)
        CT_ET_to_single_ACH_to_AHU_ARU_SCU_nom_size_W = np.max(q_CT_ET_to_single_ACH_to_AHU_ARU_SCU_W) * (1 + SIZING_MARGIN)
        CT_VCC_to_AHU_ARU_and_VCC_to_SCU_nom_size_W = np.max(q_CT_VCC_to_AHU_ARU_and_VCC_to_SCU_W) * (1 + SIZING_MARGIN)
        CT_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_nom_size_W = np.max(q_CT_VCC_to_AHU_ARU_and_single_ACH_to_SCU_W)  * (1 + SIZING_MARGIN)


        # sizing of boilers and burners
        boiler_FP_to_single_ACH_to_AHU_nom_size_W = np.max(q_boiler_FP_to_single_ACH_to_AHU_W) * (1 + SIZING_MARGIN)
        burner_ET_to_single_ACH_to_AHU_nom_size_W = np.max(q_burner_ET_to_single_ACH_to_AHU_W) * (1 + SIZING_MARGIN)

        boiler_FP_to_single_ACH_to_ARU_nom_size_W = np.max(q_boiler_FP_to_single_ACH_to_ARU_W) * (1 + SIZING_MARGIN)
        burner_ET_to_single_ACH_to_ARU_nom_size_W = np.max(q_burner_ET_to_single_ACH_to_ARU_W) * (1 + SIZING_MARGIN)

        boiler_FP_to_single_ACH_to_SCU_nom_size_W = np.max(q_boiler_FP_to_single_ACH_to_SCU_W) * (1 + SIZING_MARGIN)
        burner_ET_to_single_ACH_to_SCU_nom_size_W = np.max(q_burner_ET_to_single_ACH_to_SCU_W) * (1 + SIZING_MARGIN)

        boiler_FP_to_single_ACH_to_AHU_ARU_nom_size_W = np.max(q_boiler_FP_to_single_ACH_to_AHU_ARU_W) * (1 + SIZING_MARGIN)
        burner_ET_to_single_ACH_to_AHU_ARU_nom_size_W = np.max(q_burner_ET_to_single_ACH_to_AHU_ARU_W) * (1 + SIZING_MARGIN)

        boiler_FP_to_single_ACH_to_AHU_SCU_nom_size_W = np.max(q_boiler_FP_to_single_ACH_to_AHU_SCU_W) * (1 + SIZING_MARGIN)
        burner_ET_to_single_ACH_to_AHU_SCU_nom_size_W = np.max(q_burner_ET_to_single_ACH_to_AHU_SCU_W) * (1 + SIZING_MARGIN)

        boiler_FP_to_single_ACH_to_ARU_SCU_nom_size_W = np.max(q_boiler_FP_to_single_ACH_to_ARU_SCU_W) * (1 + SIZING_MARGIN)
        burner_ET_to_single_ACH_to_ARU_SCU_nom_size_W = np.max(q_burner_ET_to_single_ACH_to_ARU_SCU_W) * (1 + SIZING_MARGIN)

        boiler_FP_to_single_ACH_to_AHU_ARU_SCU_nom_size_W = np.max(q_boiler_FP_to_single_ACH_to_AHU_ARU_SCU_W) * (1 + SIZING_MARGIN)
        burner_ET_to_single_ACH_to_AHU_ARU_SCU_nom_size_W = np.max(q_burner_ET_single_ACH_to_AHU_ARU_SCU_W) * (1 + SIZING_MARGIN)

        boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_nom_size_W = boiler_FP_to_single_ACH_to_SCU_nom_size_W

        for hour in range(8760):
            # cooling towers operation
            # AHU
            if config.decentralized.AHUflag:
                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_AHU_W[hour], CT_VCC_to_AHU_nom_size_W)
                result_AHU[1][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_AHU[1][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU[1][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_FP_to_single_ACH_to_AHU_W[hour], CT_FP_to_single_ACH_to_AHU_nom_size_W)
                result_AHU[2][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_AHU[2][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU[2][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_ET_to_single_ACH_to_AHU_W[hour], CT_ET_to_single_ACH_to_AHU_nom_size_W)
                result_AHU[3][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_AHU[3][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU[3][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # ARU
            if config.decentralized.ARUflag:
                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_ARU_W[hour], CT_VCC_to_ARU_nom_size_W)
                result_ARU[1][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_ARU[1][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_ARU[1][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_FP_to_single_ACH_to_ARU_W[hour], CT_FP_to_single_ACH_to_ARU_nom_size_W)
                result_ARU[2][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_ARU[2][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_ARU[2][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_ET_to_single_ACH_to_ARU_W[hour], CT_ET_to_single_ACH_to_ARU_nom_size_W)
                result_ARU[3][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_ARU[3][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_ARU[3][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # SCU
            if config.decentralized.SCUflag:
                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_SCU_W[hour], CT_VCC_to_SCU_nom_size_W)
                result_SCU[1][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_SCU[1][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_SCU[1][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_FP_to_single_ACH_to_SCU_W[hour], CT_FP_to_single_ACH_to_SCU_nom_size_W)
                result_SCU[2][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_SCU[2][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_SCU[2][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_ET_to_single_ACH_to_SCU_W[hour], CT_ET_to_single_ACH_to_SCU_nom_size_W)
                result_SCU[3][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_SCU[3][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_SCU[3][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # AHU+ARU
            if config.decentralized.AHUARUflag:
                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_AHU_ARU_W[hour], CT_VCC_to_AHU_ARU_nom_size_W)
                result_AHU_ARU[1][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_AHU_ARU[1][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_ARU[1][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_FP_to_single_ACH_to_AHU_ARU_W[hour], CT_FP_to_single_ACH_to_AHU_ARU_nom_size_W)
                result_AHU_ARU[2][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_AHU_ARU[2][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_ARU[2][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_ET_to_single_ACH_to_AHU_ARU_W[hour], CT_ET_to_single_ACH_to_AHU_ARU_nom_size_W)
                result_AHU_ARU[3][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_AHU_ARU[3][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_ARU[3][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # AHU+SCU
            if config.decentralized.AHUSCUflag:
                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_AHU_SCU_W[hour], CT_VCC_to_AHU_SCU_nom_size_W)
                result_AHU_SCU[1][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_AHU_SCU[1][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_SCU[1][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_FP_tosingle_ACH_to_AHU_SCU_W[hour], CT_single_ACH_to_AHU_SCU_nom_size_W)
                result_AHU_SCU[2][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_AHU_SCU[2][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_SCU[2][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_ET_to_single_ACH_to_AHU_SCU_W[hour], CT_ET_to_single_ACH_to_AHU_SCU_nom_size_W)
                result_AHU_SCU[3][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_AHU_SCU[3][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_SCU[3][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # ARU+SCU
            if config.decentralized.ARUSCUflag:
                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_ARU_SCU_W[hour], CT_VCC_to_ARU_SCU_nom_size_W)
                result_ARU_SCU[1][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_ARU_SCU[1][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_ARU_SCU[1][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_FP_to_single_ACH_to_ARU_SCU_W[hour], CT_FP_to_single_ACH_to_ARU_SCU_nom_size_W)
                result_ARU_SCU[2][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_ARU_SCU[2][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_ARU_SCU[2][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_ET_to_single_ACH_to_ARU_SCU_W[hour], CT_ET_to_single_ACH_to_ARU_SCU_nom_size_W)
                result_ARU_SCU[3][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_ARU_SCU[3][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_ARU_SCU[3][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # AHU+ARU+SCU
            if True:  # for the case with AHU + ARU + SCU scenario. this should always be present

                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_AHU_ARU_SCU_W[hour], CT_VCC_to_AHU_ARU_SCU_nom_size_W)
                result_AHU_ARU_SCU[1][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_AHU_ARU_SCU[1][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[1][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_FP_to_single_ACH_to_AHU_ARU_SCU_W[hour], CT_FP_to_single_ACH_to_AHU_ARU_SCU_nom_size_W)
                result_AHU_ARU_SCU[2][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_AHU_ARU_SCU[2][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[2][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_ET_to_single_ACH_to_AHU_ARU_SCU_W[hour], CT_ET_to_single_ACH_to_AHU_ARU_SCU_nom_size_W)
                result_AHU_ARU_SCU[3][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_AHU_ARU_SCU[3][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[3][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_AHU_ARU_and_VCC_to_SCU_W[hour], CT_VCC_to_AHU_ARU_and_VCC_to_SCU_nom_size_W)
                result_AHU_ARU_SCU[4][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_AHU_ARU_SCU[4][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[4][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

                wdot_W = cooling_tower.calc_CT(q_CT_VCC_to_AHU_ARU_and_single_ACH_to_SCU_W[hour], CT_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_nom_size_W)
                result_AHU_ARU_SCU[5][7] += lca.ELEC_PRICE[hour] * wdot_W  # CHF
                result_AHU_ARU_SCU[5][8] += lca.EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[5][9] += lca.EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # Boilers
            # AHU
            if config.decentralized.AHUflag:

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_FP_to_single_ACH_to_AHU_W[hour], boiler_FP_to_single_ACH_to_AHU_nom_size_W,
                                                    T_re_boiler_FP_to_single_ACH_to_AHU_K[hour]) if q_boiler_FP_to_single_ACH_to_AHU_W[hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_FP_to_single_ACH_to_AHU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_AHU[2][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_AHU[2][8] += (lca.NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_AHU[2][9] += (lca.NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

                burner_eff = burner.calc_cop_burner(q_burner_ET_to_single_ACH_to_AHU_W[hour], burner_ET_to_single_ACH_to_AHU_nom_size_W) if q_burner_ET_to_single_ACH_to_AHU_W[hour] > 0 else 0
                Q_gas_for_burner_Wh = q_burner_ET_to_single_ACH_to_AHU_W[hour] / burner_eff if burner_eff > 0 else 0

                result_AHU[3][7] += prices.NG_PRICE * Q_gas_for_burner_Wh  # CHF
                result_AHU[3][8] += (lca.NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_burner_Wh) * 3600E-6  # kgCO2
                result_AHU[3][9] += (lca.NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_burner_Wh) * 3600E-6  # MJ-oil-eq

            # ARU
            if config.decentralized.ARUflag:

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_FP_to_single_ACH_to_ARU_W[hour], boiler_FP_to_single_ACH_to_ARU_nom_size_W,
                                                    T_re_boiler_FP_to_single_ACH_to_ARU_K[hour]) if q_boiler_FP_to_single_ACH_to_ARU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_FP_to_single_ACH_to_ARU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_ARU[2][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_ARU[2][8] += (lca.NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_ARU[2][9] += (lca.NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

                burner_eff = burner.calc_cop_burner(q_burner_ET_to_single_ACH_to_ARU_W[hour], burner_ET_to_single_ACH_to_ARU_nom_size_W) if q_burner_ET_to_single_ACH_to_ARU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_burner_Wh = q_burner_ET_to_single_ACH_to_ARU_W[hour] / burner_eff if burner_eff > 0 else 0


                result_ARU[3][7] += prices.NG_PRICE * Q_gas_for_burner_Wh  # CHF
                result_ARU[3][8] += (lca.NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_burner_Wh) * 3600E-6  # kgCO2
                result_ARU[3][9] += (lca.NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_burner_Wh) * 3600E-6  # MJ-oil-eq

            # SCU
            if config.decentralized.SCUflag:

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_FP_to_single_ACH_to_SCU_W[hour], boiler_FP_to_single_ACH_to_SCU_nom_size_W,
                                                    T_re_boiler_FP_to_single_ACH_to_SCU_K[hour]) if q_boiler_FP_to_single_ACH_to_SCU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_FP_to_single_ACH_to_SCU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_SCU[2][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_SCU[2][8] += (lca.NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_SCU[2][9] += (lca.NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

                burner_eff = burner.calc_cop_burner(q_burner_ET_to_single_ACH_to_SCU_W[hour], burner_ET_to_single_ACH_to_SCU_nom_size_W) if q_burner_ET_to_single_ACH_to_SCU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_burner_Wh = q_burner_ET_to_single_ACH_to_SCU_W[hour] / burner_eff if burner_eff > 0 else 0


                result_SCU[3][7] += prices.NG_PRICE * Q_gas_for_burner_Wh  # CHF
                result_SCU[3][8] += (lca.NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_burner_Wh) * 3600E-6  # kgCO2
                result_SCU[3][9] += (lca.NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_burner_Wh) * 3600E-6  # MJ-oil-eq

            # AHU + ARU
            if config.decentralized.AHUARUflag:

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_FP_to_single_ACH_to_AHU_ARU_W[hour], boiler_FP_to_single_ACH_to_AHU_ARU_nom_size_W,
                                                    T_re_boiler_FP_to_single_ACH_to_AHU_ARU_K[hour]) if q_boiler_FP_to_single_ACH_to_AHU_ARU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_FP_to_single_ACH_to_AHU_ARU_W[hour] / boiler_eff if boiler_eff > 0 else 0


                result_AHU_ARU[2][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_AHU_ARU[2][8] += (lca.NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_AHU_ARU[2][9] += (lca.NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

                burner_eff = burner.calc_cop_burner(q_burner_ET_to_single_ACH_to_AHU_ARU_W[hour], burner_ET_to_single_ACH_to_AHU_ARU_nom_size_W) if q_burner_ET_to_single_ACH_to_AHU_ARU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_burner_Wh = q_burner_ET_to_single_ACH_to_AHU_ARU_W[hour] / burner_eff if burner_eff > 0 else 0

                result_AHU_ARU[3][7] += prices.NG_PRICE * Q_gas_for_burner_Wh  # CHF
                result_AHU_ARU[3][8] += (lca.NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_burner_Wh) * 3600E-6  # kgCO2
                result_AHU_ARU[3][9] += (lca.NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_burner_Wh) * 3600E-6  # MJ-oil-eq


            # AHU + SCU
            if config.decentralized.AHUSCUflag:

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_FP_to_single_ACH_to_AHU_SCU_W[hour], boiler_FP_to_single_ACH_to_AHU_SCU_nom_size_W,
                                                    T_re_boiler_FP_to_single_ACH_to_AHU_SCU_K[hour]) if q_boiler_FP_to_single_ACH_to_AHU_SCU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_FP_to_single_ACH_to_AHU_SCU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_AHU_SCU[2][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_AHU_SCU[2][8] += (lca.NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_AHU_SCU[2][9] += (lca.NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

                burner_eff = burner.calc_cop_burner(q_burner_ET_to_single_ACH_to_AHU_SCU_W[hour], burner_ET_to_single_ACH_to_AHU_SCU_nom_size_W) if q_burner_ET_to_single_ACH_to_AHU_SCU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_burner_Wh = q_burner_ET_to_single_ACH_to_AHU_SCU_W[hour] / burner_eff if burner_eff > 0 else 0

                result_AHU_SCU[3][7] += prices.NG_PRICE * Q_gas_for_burner_Wh  # CHF
                result_AHU_SCU[3][8] += (lca.NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_burner_Wh) * 3600E-6  # kgCO2
                result_AHU_SCU[3][9] += (lca.NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_burner_Wh) * 3600E-6  # MJ-oil-eq

            # ARU + SCU
            if config.decentralized.ARUSCUflag:

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_FP_to_single_ACH_to_ARU_SCU_W[hour], boiler_FP_to_single_ACH_to_ARU_SCU_nom_size_W,
                                                    T_re_boiler_FP_to_single_ACH_to_ARU_SCU_K[hour]) if q_boiler_FP_to_single_ACH_to_ARU_SCU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_FP_to_single_ACH_to_ARU_SCU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_ARU_SCU[2][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_ARU_SCU[2][8] += (lca.NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_ARU_SCU[2][9] += (lca.NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

                burner_eff = burner.calc_cop_burner(q_burner_ET_to_single_ACH_to_ARU_SCU_W[hour], burner_ET_to_single_ACH_to_ARU_SCU_nom_size_W) if q_burner_ET_to_single_ACH_to_ARU_SCU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_burner_Wh = q_burner_ET_to_single_ACH_to_ARU_SCU_W[hour] / burner_eff if burner_eff > 0 else 0

                result_ARU_SCU[3][7] += prices.NG_PRICE * Q_gas_for_burner_Wh  # CHF
                result_ARU_SCU[3][8] += (lca.NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_burner_Wh) * 3600E-6  # kgCO2
                result_ARU_SCU[3][9] += (lca.NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_burner_Wh) * 3600E-6  # MJ-oil-eq

            # AHU + ARU + SCU
            if True:  # for the case with AHU + ARU + SCU scenario. this should always be present

                boiler_eff = boiler.calc_Cop_boiler(q_boiler_FP_to_single_ACH_to_AHU_ARU_SCU_W[hour], boiler_FP_to_single_ACH_to_AHU_ARU_SCU_nom_size_W,
                                                    T_re_boiler_FP_to_single_ACH_to_AHU_ARU_SCU_K[hour]) if q_boiler_FP_to_single_ACH_to_AHU_ARU_SCU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_FP_to_single_ACH_to_AHU_ARU_SCU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_AHU_ARU_SCU[2][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_AHU_ARU_SCU[2][8] += (lca.NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[2][9] += (lca.NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

                burner_eff = burner.calc_cop_burner(q_burner_ET_single_ACH_to_AHU_ARU_SCU_W[hour],
                                                    burner_ET_to_single_ACH_to_AHU_ARU_SCU_nom_size_W) \
                    if q_burner_ET_single_ACH_to_AHU_ARU_SCU_W[hour] > 0 else 0
                Q_gas_for_burner_Wh = q_burner_ET_single_ACH_to_AHU_ARU_SCU_W[hour] / burner_eff if burner_eff > 0 else 0


                result_AHU_ARU_SCU[3][7] += prices.NG_PRICE * Q_gas_for_burner_Wh  # CHF
                result_AHU_ARU_SCU[3][8] += (lca.NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_burner_Wh) * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[3][9] += (lca.NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_burner_Wh) * 3600E-6  # MJ-oil-eq

                # VCC to AHU + ARU and single effect ACH to SCU
                boiler_eff = boiler.calc_Cop_boiler(q_boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_W[hour], boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_nom_size_W,
                                                    T_re_boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_K[hour]) if q_boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_W[
                                                                                                  hour] > 0 else 0
                Q_gas_for_boiler_Wh = q_boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_W[hour] / boiler_eff if boiler_eff > 0 else 0

                result_AHU_ARU_SCU[5][7] += prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
                result_AHU_ARU_SCU[5][8] += (lca.NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
                result_AHU_ARU_SCU[5][9] += (lca.NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

        ## Calculate Capex/Opex
        # AHU
        Inv_Costs_AHU = np.zeros((4, 1))
        if config.decentralized.AHUflag:
            # 0
            Capex_a_DX_USD, Opex_fixed_DX_USD, Capex_DX_USD = dx.calc_Cinv_DX(Qc_nom_combination_AHU_W)
            Inv_Costs_AHU[0][0] = Capex_a_DX_USD + Opex_fixed_DX_USD  # FIXME: a dummy value to rule out this configuration
            # 1
            Capex_a_VCC_USD, Opex_fixed_VCC_USD, Capex_VCC_USD = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_AHU_W, locator, config, 'CH3')
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_VCC_to_AHU_nom_size_W, locator, config, 'CT1')
            Inv_Costs_AHU[1][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_VCC_USD + Opex_fixed_VCC_USD
            # 2
            Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Qc_nom_combination_AHU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_FP_to_single_ACH_to_AHU_nom_size_W, locator, config, 'CT1')
            Capex_a_boiler_USD, Opex_fixed_boiler_USD, Capex_boiler_USD = boiler.calc_Cinv_boiler(boiler_FP_to_single_ACH_to_AHU_nom_size_W, locator, config, 'BO1')
            Inv_Costs_AHU[2][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_ACH_USD + Opex_fixed_ACH_USD + Capex_a_boiler_USD + Opex_fixed_boiler_USD + Capex_a_SC_FP_USD + Opex_SC_FP_USD
            # 3
            Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Qc_nom_combination_AHU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_ET_to_single_ACH_to_AHU_nom_size_W, locator, config, 'CT1')
            Capex_a_burner_USD, Opex_fixed_burner_USD, Capex_burner_USD = burner.calc_Cinv_burner(burner_ET_to_single_ACH_to_AHU_nom_size_W, locator, config, 'BO1')
            Inv_Costs_AHU[3][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_ACH_USD + Opex_fixed_ACH_USD + Capex_a_burner_USD + Opex_fixed_burner_USD + Capex_a_SC_FP_USD + Opex_SC_FP_USD


        # ARU
        Inv_Costs_ARU = np.zeros((4, 1))
        if config.decentralized.ARUflag:
            # 0
            Capex_a_DX_USD, Opex_fixed_DX_USD, Capex_DX_USD = dx.calc_Cinv_DX(Qc_nom_combination_ARU_W)
            Inv_Costs_ARU[0][0] = Capex_a_DX_USD + Opex_fixed_DX_USD  # FIXME: a dummy value to rule out this configuration
            # 1
            Capex_a_VCC_USD, Opex_fixed_VCC_USD, Capex_VCC_USD = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_ARU_W, locator, config, 'CH3')
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_VCC_to_ARU_nom_size_W, locator, config, 'CT1')
            Inv_Costs_ARU[1][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_VCC_USD + Opex_fixed_VCC_USD
            # 2
            Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Qc_nom_combination_ARU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_FP_to_single_ACH_to_ARU_nom_size_W, locator, config, 'CT1')
            Capex_a_boiler_USD, Opex_fixed_boiler_USD, Capex_boiler_USD = boiler.calc_Cinv_boiler(boiler_FP_to_single_ACH_to_ARU_nom_size_W, locator, config, 'BO1')
            Inv_Costs_ARU[2][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_ACH_USD + Opex_fixed_ACH_USD + Capex_a_boiler_USD + Opex_fixed_boiler_USD + Capex_a_SC_FP_USD + Opex_SC_FP_USD
            # 3
            Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Qc_nom_combination_ARU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_ET_to_single_ACH_to_ARU_nom_size_W, locator, config, 'CT1')
            Capex_a_burner_USD, Opex_fixed_burner_USD, Capex_burner_USD = burner.calc_Cinv_burner(burner_ET_to_single_ACH_to_ARU_nom_size_W, locator, config, 'BO1')
            Inv_Costs_ARU[3][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_ACH_USD + Opex_fixed_ACH_USD + Capex_a_burner_USD + Opex_fixed_burner_USD + Capex_a_SC_FP_USD + Opex_SC_FP_USD

        # SCU
        Inv_Costs_SCU = np.zeros((4, 1))
        if config.decentralized.SCUflag:
            # 0
            Capex_a_DX_USD, Opex_fixed_DX_USD, Capex_DX_USD = dx.calc_Cinv_DX(Qc_nom_combination_SCU_W)
            Inv_Costs_SCU[0][0] = Capex_a_DX_USD + Opex_fixed_DX_USD  # FIXME: a dummy value to rule out this configuration
            # 1
            Capex_a_VCC_USD, Opex_fixed_VCC_USD, Capex_VCC_USD = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_SCU_W, locator, config, 'CH3')
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_VCC_to_SCU_nom_size_W, locator, config, 'CT1')
            Inv_Costs_SCU[1][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_VCC_USD + Opex_fixed_VCC_USD
            # 2
            Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Qc_nom_combination_SCU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_FP_to_single_ACH_to_SCU_nom_size_W, locator, config, 'CT1')
            Capex_a_boiler_USD, Opex_fixed_boiler_USD, Capex_boiler_USD = boiler.calc_Cinv_boiler(boiler_FP_to_single_ACH_to_SCU_nom_size_W, locator, config, 'BO1')
            Inv_Costs_SCU[2][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_ACH_USD + Opex_fixed_ACH_USD + Capex_a_boiler_USD + Opex_fixed_boiler_USD + Capex_a_SC_FP_USD + Opex_SC_FP_USD
            # 3
            Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Qc_nom_combination_SCU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_ET_to_single_ACH_to_SCU_nom_size_W, locator, config, 'CT1')
            Capex_a_burner_USD, Opex_fixed_burner_USD, Capex_burner_USD = burner.calc_Cinv_burner(burner_ET_to_single_ACH_to_SCU_nom_size_W, locator, config, 'BO1')
            Inv_Costs_SCU[3][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_ACH_USD + Opex_fixed_ACH_USD + Capex_a_burner_USD + Opex_fixed_burner_USD + Capex_a_SC_FP_USD + Opex_SC_FP_USD

        # AHU + ARU
        Inv_Costs_AHU_ARU = np.zeros((4, 1))
        if config.decentralized.AHUARUflag:
            # 0
            Capex_a_DX_USD, Opex_fixed_DX_USD, Capex_DX_USD = dx.calc_Cinv_DX(Qc_nom_combination_AHU_ARU_W)
            Inv_Costs_AHU_ARU[0][0] = Capex_a_DX_USD + Opex_fixed_DX_USD  # FIXME: a dummy value to rule out this configuration
            # 1
            Capex_a_VCC_USD, Opex_fixed_VCC_USD, Capex_VCC_USD = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_AHU_ARU_W, locator, config, 'CH3')
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_VCC_to_AHU_ARU_nom_size_W, locator, config, 'CT1')
            Inv_Costs_AHU_ARU[1][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_VCC_USD + Opex_fixed_VCC_USD
            # 2
            Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Qc_nom_combination_AHU_ARU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_FP_to_single_ACH_to_AHU_ARU_nom_size_W, locator, config, 'CT1')
            Capex_a_boiler_USD, Opex_fixed_boiler_USD, Capex_boiler_USD = boiler.calc_Cinv_boiler(boiler_FP_to_single_ACH_to_AHU_ARU_nom_size_W, locator, config, 'BO1')
            Inv_Costs_AHU_ARU[2][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_ACH_USD + Opex_fixed_ACH_USD + Capex_a_boiler_USD + Opex_fixed_boiler_USD + Capex_a_SC_FP_USD + Opex_SC_FP_USD
            # 3
            Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Qc_nom_combination_AHU_ARU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_ET_to_single_ACH_to_AHU_ARU_nom_size_W, locator, config, 'CT1')
            Capex_a_burner_USD, Opex_fixed_burner_USD, Capex_burner_USD = burner.calc_Cinv_burner(burner_ET_to_single_ACH_to_AHU_ARU_nom_size_W, locator, config, 'BO1')
            Inv_Costs_AHU_ARU[3][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_ACH_USD + Opex_fixed_ACH_USD + Capex_a_burner_USD + Opex_fixed_burner_USD + Capex_a_SC_FP_USD + Opex_SC_FP_USD

        # AHU + SCU
        Inv_Costs_AHU_SCU = np.zeros((4, 1))
        if config.decentralized.AHUSCUflag:
            # 0
            Capex_a_DX_USD, Opex_fixed_DX_USD, Capex_DX_USD = dx.calc_Cinv_DX(Qc_nom_combination_AHU_SCU_W)
            Inv_Costs_AHU_SCU[0][0] = Capex_a_DX_USD + Opex_fixed_DX_USD  # FIXME: a dummy value to rule out this configuration
            # 1
            Capex_a_VCC_USD, Opex_fixed_VCC_USD, Capex_VCC_USD = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_AHU_SCU_W, locator, config, 'CH3')
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_VCC_to_AHU_SCU_nom_size_W, locator, config, 'CT1')
            Inv_Costs_AHU_SCU[1][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_VCC_USD + Opex_fixed_VCC_USD
            # 2
            Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Qc_nom_combination_AHU_SCU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_single_ACH_to_AHU_SCU_nom_size_W, locator, config, 'CT1')
            Capex_a_boiler_USD, Opex_fixed_boiler_USD, Capex_boiler_USD = boiler.calc_Cinv_boiler(boiler_FP_to_single_ACH_to_AHU_SCU_nom_size_W, locator, config, 'BO1')
            Inv_Costs_AHU_SCU[2][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_ACH_USD + Opex_fixed_ACH_USD + Capex_a_boiler_USD + Opex_fixed_boiler_USD + Capex_a_SC_FP_USD + Opex_SC_FP_USD
            # 3
            Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Qc_nom_combination_AHU_SCU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_ET_to_single_ACH_to_AHU_SCU_nom_size_W, locator, config, 'CT1')
            Capex_a_burner_USD, Opex_fixed_burner_USD, Capex_burner_USD = burner.calc_Cinv_burner(burner_ET_to_single_ACH_to_AHU_SCU_nom_size_W, locator, config, 'BO1')
            Inv_Costs_AHU_SCU[3][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + \
                                      Capex_a_ACH_USD + Opex_fixed_ACH_USD + Capex_a_burner_USD + Opex_fixed_burner_USD + Capex_a_SC_FP_USD + Opex_SC_FP_USD

        # ARU + SCU
        Inv_Costs_ARU_SCU = np.zeros((4, 1))
        if config.decentralized.ARUSCUflag:
            # 0
            Capex_a_DX_USD, Opex_fixed_DX_USD, Capex_DX_USD = dx.calc_Cinv_DX(Qc_nom_combination_ARU_SCU_W)
            Inv_Costs_ARU_SCU[0][0] = Capex_a_DX_USD + Opex_fixed_DX_USD  # FIXME: a dummy value to rule out this configuration
            # 1
            Capex_a_VCC_USD, Opex_fixed_VCC_USD, Capex_VCC_USD = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_ARU_SCU_W, locator, config, 'CH3')
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_VCC_to_ARU_SCU_nom_size_W, locator, config, 'CT1')
            Inv_Costs_ARU_SCU[1][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_VCC_USD + Opex_fixed_VCC_USD
            # 2
            Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Qc_nom_combination_ARU_SCU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_FP_to_single_ACH_to_ARU_SCU_nom_size_W, locator, config, 'CT1')
            Capex_a_boiler_USD, Opex_fixed_boiler_USD, Capex_boiler_USD = boiler.calc_Cinv_boiler(boiler_FP_to_single_ACH_to_ARU_SCU_nom_size_W, locator, config, 'BO1')
            Inv_Costs_ARU_SCU[2][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_ACH_USD + Opex_fixed_ACH_USD + Capex_a_boiler_USD + Opex_fixed_boiler_USD + Capex_a_SC_FP_USD + Opex_SC_FP_USD
            # 3
            Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Qc_nom_combination_ARU_SCU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_ET_to_single_ACH_to_ARU_SCU_nom_size_W, locator, config, 'CT1')
            Capex_a_burner_USD, Opex_fixed_burner_USD, Capex_burner_USD = burner.calc_Cinv_burner(burner_ET_to_single_ACH_to_ARU_SCU_nom_size_W, locator, config, 'BO1')
            Inv_Costs_ARU_SCU[3][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + \
                                      Capex_a_ACH_USD + Opex_fixed_ACH_USD + Capex_a_burner_USD + Opex_fixed_burner_USD + Capex_a_SC_FP_USD + Opex_SC_FP_USD

        # AHU + ARU + SCU
        Inv_Costs_AHU_ARU_SCU = np.zeros((6, 1))
        if True:  # for the case with AHU + ARU + SCU scenario. this should always be present
            print 'decentralized building simulation with configuration: AHU + ARU + SCU cost calculations'
            # 0: DX
            Capex_a_DX_USD, Opex_fixed_DX_USD, Capex_DX_USD = dx.calc_Cinv_DX(Qc_nom_combination_AHU_ARU_SCU_W)
            Inv_Costs_AHU_ARU_SCU[0][0] = Capex_a_DX_USD + Opex_fixed_DX_USD  # FIXME: a dummy value to rule out this configuration

            # 1: VCC + CT
            Capex_a_VCC_USD, Opex_fixed_VCC_USD, Capex_VCC_USD = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_AHU_ARU_SCU_W, locator, config, 'CH3')
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_VCC_to_AHU_ARU_SCU_nom_size_W, locator, config, 'CT1')
            Inv_Costs_AHU_ARU_SCU[1][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_VCC_USD + Opex_fixed_VCC_USD

            # 2: single effect ACH + CT + Boiler + SC_FP
            Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Qc_nom_combination_AHU_ARU_SCU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_FP_to_single_ACH_to_AHU_ARU_SCU_nom_size_W, locator, config, 'CT1')
            Capex_a_boiler_USD, Opex_fixed_boiler_USD, Capex_boiler_USD = boiler.calc_Cinv_boiler(boiler_FP_to_single_ACH_to_AHU_ARU_SCU_nom_size_W, locator, config, 'BO1')
            Inv_Costs_AHU_ARU_SCU[2][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_ACH_USD + Opex_fixed_ACH_USD + Capex_a_boiler_USD + Opex_fixed_boiler_USD + Capex_a_SC_FP_USD + Opex_SC_FP_USD

            # 3: double effect ACH + CT + Boiler + SC_ET
            Capex_a_ACH_USD, Opex_fixed_ACH_USD, Capex_ACH_USD = chiller_absorption.calc_Cinv_ACH(Qc_nom_combination_AHU_ARU_SCU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_ET_to_single_ACH_to_AHU_ARU_SCU_nom_size_W, locator, config, 'CT1')
            Capex_a_burner_USD, Opex_fixed_burner_USD, Capex_burner_USD = burner.calc_Cinv_burner(burner_ET_to_single_ACH_to_ARU_SCU_nom_size_W, locator, config, 'BO1')
            Inv_Costs_AHU_ARU_SCU[3][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_ACH_USD + Opex_fixed_ACH_USD + Capex_a_burner_USD + Opex_fixed_burner_USD + Capex_a_SC_ET_USD + Opex_SC_ET_USD

            # 4: VCC (AHU + ARU) + VCC (SCU) + CT
            Capex_a_VCC_AA_USD, Opex_VCC_AA_USD, Capex_VCC_AA_USD = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_AHU_ARU_W, locator, config, 'CH3')
            Capex_a_VCC_S_USD, Opex_VCC_S_USD, Capex_VCC_S_USD = chiller_vapor_compression.calc_Cinv_VCC(Qc_nom_combination_SCU_W, locator, config, 'CH3')
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_VCC_to_AHU_ARU_and_VCC_to_SCU_nom_size_W, locator, config, 'CT1')
            Inv_Costs_AHU_ARU_SCU[4][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_VCC_AA_USD + Capex_a_VCC_S_USD + Opex_VCC_AA_USD + Opex_VCC_S_USD

            # 5: VCC (AHU + ARU) + ACH (SCU) + CT + Boiler + SC_FP
            Capex_a_ACH_S_USD, Opex_ACH_S_USD, Capex_ACH_S_USD = chiller_absorption.calc_Cinv_ACH(Qc_nom_combination_SCU_W, locator, ACH_TYPE_SINGLE, config)
            Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD = cooling_tower.calc_Cinv_CT(CT_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_nom_size_W, locator, config, 'CT1')
            Capex_a_boiler_USD, Opex_fixed_boiler_USD, Capex_boiler_USD = boiler.calc_Cinv_boiler(boiler_VCC_to_AHU_ARU_and_FP_to_single_ACH_to_SCU_nom_size_W, locator, config, 'BO1')
            Capex_a_SC_FP_USD, Opex_SC_FP_USD, Capex_SC_FP_USD = solar_collector.calc_Cinv_SC(SC_FP_data['Area_SC_m2'][0], locator, config, technology=0)
            Inv_Costs_AHU_ARU_SCU[5][0] = Capex_a_CT_USD + Opex_fixed_CT_USD + Capex_a_VCC_AA_USD + Opex_VCC_AA_USD + Capex_a_ACH_S_USD + Opex_ACH_S_USD + Capex_a_boiler_USD + Opex_fixed_boiler_USD + Capex_a_SC_FP_USD + Opex_SC_FP_USD

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

        dico["DX to AHU Share"] = result_AHU[:, 0]
        dico["VCC to AHU Share"] = result_AHU[:, 1]
        dico["single effect ACH to AHU Share (FP)"] = result_AHU[:, 2]
        dico["single effect ACH to AHU Share (ET)"] = result_AHU[:, 3]

        # performance indicators of the configurations
        dico["Operation Costs [CHF]"] = result_AHU[:, 7]
        dico["CO2 Emissions [kgCO2-eq]"] = result_AHU[:, 8]
        dico["Primary Energy Needs [MJoil-eq]"] = result_AHU[:, 9]
        dico["Annualized Investment Costs [CHF]"] = Inv_Costs_AHU[:, 0]
        dico["Total Costs [CHF]"] = TotalCosts[:, 1]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power DX to AHU [W]"] = result_AHU[:, 0] * Qc_nom_combination_AHU_W
        dico["Nominal Power VCC to AHU [W]"] = result_AHU[:, 1] * Qc_nom_combination_AHU_W
        dico["Nominal Power single effect ACH to AHU (FP) [W]"] = result_AHU[:, 2] * Qc_nom_combination_AHU_W
        dico["Nominal Power single effect ACH to AHU (ET) [W]"] = result_AHU[:, 3] * Qc_nom_combination_AHU_W

        dico_df = pd.DataFrame(dico)
        fName = locator.get_optimization_decentralized_folder_building_result_cooling(building_name, 'AHU')
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

        dico["DX to ARU Share"] = result_ARU[:, 0]
        dico["VCC to ARU Share"] = result_ARU[:, 1]
        dico["single effect ACH to ARU Share (FP)"] = result_ARU[:, 2]
        dico["single effect ACH to ARU Share (ET)"] = result_ARU[:, 3]

        # performance indicators of the configurations
        dico["Operation Costs [CHF]"] = result_ARU[:, 7]
        dico["CO2 Emissions [kgCO2-eq]"] = result_ARU[:, 8]
        dico["Primary Energy Needs [MJoil-eq]"] = result_ARU[:, 9]
        dico["Annualized Investment Costs [CHF]"] = Inv_Costs_ARU[:, 0]
        dico["Total Costs [CHF]"] = TotalCosts[:, 1]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power DX to ARU [W]"] = result_ARU[:, 0] * Qc_nom_combination_ARU_W
        dico["Nominal Power VCC to ARU [W]"] = result_ARU[:, 1] * Qc_nom_combination_ARU_W
        dico["Nominal Power single effect ACH to ARU (FP) [W]"] = result_ARU[:, 2] * Qc_nom_combination_ARU_W
        dico["Nominal Power single effect ACH to ARU (ET) [W]"] = result_ARU[:, 3] * Qc_nom_combination_ARU_W

        dico_df = pd.DataFrame(dico)
        fName = locator.get_optimization_decentralized_folder_building_result_cooling(building_name, 'ARU')
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

        dico["DX to SCU Share"] = result_SCU[:, 0]
        dico["VCC to SCU Share"] = result_SCU[:, 1]
        dico["single effect ACH to SCU Share (FP)"] = result_SCU[:, 2]
        dico["single effect ACH to SCU Share (ET)"] = result_SCU[:, 3]

        # performance indicators of the configurations
        dico["Operation Costs [CHF]"] = result_SCU[:, 7]
        dico["CO2 Emissions [kgCO2-eq]"] = result_SCU[:, 8]
        dico["Primary Energy Needs [MJoil-eq]"] = result_SCU[:, 9]
        dico["Annualized Investment Costs [CHF]"] = Inv_Costs_SCU[:, 0]
        dico["Total Costs [CHF]"] = TotalCosts[:, 1]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power DX to SCU [W]"] = result_SCU[:, 0] * Qc_nom_combination_SCU_W
        dico["Nominal Power VCC to SCU [W]"] = result_SCU[:, 1] * Qc_nom_combination_SCU_W
        dico["Nominal Power single effect ACH to SCU (FP) [W]"] = result_SCU[:, 2] * Qc_nom_combination_SCU_W
        dico["Nominal Power single effect ACH to SCU (ET) [W]"] = result_SCU[:, 3] * Qc_nom_combination_SCU_W

        dico_df = pd.DataFrame(dico)
        fName = locator.get_optimization_decentralized_folder_building_result_cooling(building_name, 'SCU')
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

        dico["DX to AHU_ARU Share"] = result_AHU_ARU[:, 0]
        dico["VCC to AHU_ARU Share"] = result_AHU_ARU[:, 1]
        dico["single effect ACH to AHU_ARU Share (FP)"] = result_AHU_ARU[:, 2]
        dico["single effect ACH to AHU_ARU Share (ET)"] = result_AHU_ARU[:, 3]

        # performance indicators of the configurations
        dico["Operation Costs [CHF]"] = result_AHU_ARU[:, 7]
        dico["CO2 Emissions [kgCO2-eq]"] = result_AHU_ARU[:, 8]
        dico["Primary Energy Needs [MJoil-eq]"] = result_AHU_ARU[:, 9]
        dico["Annualized Investment Costs [CHF]"] = Inv_Costs_AHU_ARU[:, 0]
        dico["Total Costs [CHF]"] = TotalCosts[:, 1]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power DX to AHU_ARU [W]"] = result_AHU_ARU[:, 0] * Qc_nom_combination_AHU_ARU_W
        dico["Nominal Power VCC to AHU_ARU [W]"] = result_AHU_ARU[:, 1] * Qc_nom_combination_AHU_ARU_W
        dico["Nominal Power single effect ACH to AHU_ARU (FP) [W]"] = result_AHU_ARU[:, 2] * Qc_nom_combination_AHU_ARU_W
        dico["Nominal Power single effect ACH to AHU_ARU (ET) [W]"] = result_AHU_ARU[:, 3] * Qc_nom_combination_AHU_ARU_W

        dico_df = pd.DataFrame(dico)
        fName = locator.get_optimization_decentralized_folder_building_result_cooling(building_name, 'AHU_ARU')
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

        dico["DX to AHU_SCU Share"] = result_AHU_SCU[:, 0]
        dico["VCC to AHU_SCU Share"] = result_AHU_SCU[:, 1]
        dico["single effect ACH to AHU_SCU Share (FP)"] = result_AHU_SCU[:, 2]
        dico["single effect ACH to AHU_SCU Share (ET)"] = result_AHU_SCU[:, 3]

        # performance indicators of the configurations
        dico["Operation Costs [CHF]"] = result_AHU_SCU[:, 7]
        dico["CO2 Emissions [kgCO2-eq]"] = result_AHU_SCU[:, 8]
        dico["Primary Energy Needs [MJoil-eq]"] = result_AHU_SCU[:, 9]
        dico["Annualized Investment Costs [CHF]"] = Inv_Costs_AHU_SCU[:, 0]
        dico["Total Costs [CHF]"] = TotalCosts[:, 1]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power DX to AHU_SCU [W]"] = result_AHU_SCU[:, 0] * Qc_nom_combination_AHU_SCU_W
        dico["Nominal Power VCC to AHU_SCU [W]"] = result_AHU_SCU[:, 1] * Qc_nom_combination_AHU_SCU_W
        dico["Nominal Power single effect ACH to AHU_SCU (FP) [W]"] = result_AHU_SCU[:, 2] * Qc_nom_combination_AHU_SCU_W
        dico["Nominal Power single effect ACH to AHU_SCU (ET) [W]"] = result_AHU_SCU[:, 3] * Qc_nom_combination_AHU_SCU_W

        dico_df = pd.DataFrame(dico)
        fName = locator.get_optimization_decentralized_folder_building_result_cooling(building_name, 'AHU_SCU')
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

        dico["DX to ARU_SCU Share"] = result_ARU_SCU[:, 0]
        dico["VCC to ARU_SCU Share"] = result_ARU_SCU[:, 1]
        dico["single effect ACH to ARU_SCU Share (FP)"] = result_ARU_SCU[:, 2]
        dico["single effect ACH to ARU_SCU Share (ET)"] = result_ARU_SCU[:, 3]

        # performance indicators of the configurations
        dico["Operation Costs [CHF]"] = result_ARU_SCU[:, 7]
        dico["CO2 Emissions [kgCO2-eq]"] = result_ARU_SCU[:, 8]
        dico["Primary Energy Needs [MJoil-eq]"] = result_ARU_SCU[:, 9]
        dico["Annualized Investment Costs [CHF]"] = Inv_Costs_ARU_SCU[:, 0]
        dico["Total Costs [CHF]"] = TotalCosts[:, 1]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power DX to ARU_SCU [W]"] = result_ARU_SCU[:, 0] * Qc_nom_combination_ARU_SCU_W
        dico["Nominal Power VCC to ARU_SCU [W]"] = result_ARU_SCU[:, 1] * Qc_nom_combination_ARU_SCU_W
        dico["Nominal Power single effect ACH to ARU_SCU (FP) [W]"] = result_ARU_SCU[:, 2] * Qc_nom_combination_ARU_SCU_W
        dico["Nominal Power single effect ACH to ARU_SCU (ET) [W]"] = result_ARU_SCU[:, 3] * Qc_nom_combination_ARU_SCU_W

        dico_df = pd.DataFrame(dico)
        fName = locator.get_optimization_decentralized_folder_building_result_cooling(building_name, 'ARU_SCU')
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

        dico["DX to AHU_ARU_SCU Share"] = result_AHU_ARU_SCU[:, 0]
        dico["VCC to AHU_ARU_SCU Share"] = result_AHU_ARU_SCU[:, 1]
        dico["single effect ACH to AHU_ARU_SCU Share (FP)"] = result_AHU_ARU_SCU[:, 2]
        dico["single effect ACH to AHU_ARU_SCU Share (ET)"] = result_AHU_ARU_SCU[:, 3]
        dico["VCC to AHU_ARU Share"] = result_AHU_ARU_SCU[:, 4]
        dico["VCC to SCU Share"] = result_AHU_ARU_SCU[:,5]
        dico["single effect ACH to SCU Share (FP)"] = result_AHU_ARU_SCU[:,6]


        # performance indicators of the configurations
        dico["Operation Costs [CHF]"] = result_AHU_ARU_SCU[:, 7]
        dico["CO2 Emissions [kgCO2-eq]"] = result_AHU_ARU_SCU[:, 8]
        dico["Primary Energy Needs [MJoil-eq]"] = result_AHU_ARU_SCU[:, 9]
        dico["Annualized Investment Costs [CHF]"] = Inv_Costs_AHU_ARU_SCU[:, 0]
        dico["Total Costs [CHF]"] = TotalCosts[:, 1]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power DX to AHU_ARU_SCU [W]"] = result_AHU_ARU_SCU[:, 0] * Qc_nom_combination_AHU_ARU_SCU_W
        dico["Nominal Power VCC to AHU_ARU_SCU [W]"] = result_AHU_ARU_SCU[:, 1] * Qc_nom_combination_AHU_ARU_SCU_W
        dico["Nominal Power single effect ACH to AHU_ARU_SCU (FP) [W]"] = result_AHU_ARU_SCU[:, 2] * Qc_nom_combination_AHU_ARU_SCU_W
        dico["Nominal Power single effect ACH to AHU_ARU_SCU (ET) [W]"] = result_AHU_ARU_SCU[:, 3] * Qc_nom_combination_AHU_ARU_SCU_W
        dico["Nominal Power VCC to AHU_ARU [W]"] = result_AHU_ARU_SCU[:, 4] * Qc_nom_combination_AHU_ARU_W
        dico["Nominal Power VCC to SCU [W]"] = result_AHU_ARU_SCU[:, 5] * Qc_nom_combination_SCU_W
        dico["Nominal Power single effect ACH to SCU (FP) [W]"] = result_AHU_ARU_SCU[:, 6] * Qc_nom_combination_SCU_W

        dico_df = pd.DataFrame(dico)
        fName = locator.get_optimization_decentralized_folder_building_result_cooling(building_name, 'AHU_ARU_SCU')
        dico_df.to_csv(fName, sep=',')

    print time.clock() - t0, "seconds process time for the decentralized Building Routine \n"


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
    building_name = [building_names[6]]
    weather_file = config.weather
    prices = Prices(locator, config)
    lca = lca_calculations(locator, config)
    disconnected_buildings_cooling_main(locator, building_names[0:1], config, prices, lca)


    print 'test_decentralized_buildings_cooling() succeeded'


if __name__ == '__main__':
    main(cea.config.Configuration())
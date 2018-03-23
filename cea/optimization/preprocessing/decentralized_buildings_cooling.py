"""
====================================
Operation for decentralized buildings
====================================
"""
from __future__ import division

import os
import cea.config
import cea.globalvar
import cea.inputlocator
import time
import numpy as np
import pandas as pd
from cea.optimization.constants import *
import cea.technologies.chiller_vcc as chiller_vcc
import cea.technologies.chiller_abs as chiller_abs
import cea.technologies.cooling_tower as cooling_tower
import cea.technologies.boiler as boiler
import cea.technologies.substation as substation
from cea.utilities import dbf
from geopandas import GeoDataFrame as Gdf
from cea.technologies.thermal_network.thermal_network_matrix import calculate_ground_temperature


def decentralized_cooling_main(locator, building_names, gv, config, prices):
    """
    Computes the parameters for the operation of disconnected buildings
    output results in csv files.
    There is no optimization at this point. The different technologies are calculated and compared 1 to 1 to
    each technology. it is a classical combinatorial problem.
    :param locator: locator class
    :param building_names: list with names of buildings
    :param gv: global variables class
    :type locator: class
    :type building_names: list
    :type gv: class
    :return: results of operation of buildings located in locator.get_optimization_disconnected_folder
    :rtype: Nonetype
    """
    t0 = time.clock()

    BestData = {}
    total_demand = pd.read_csv(locator.get_total_demand())

    ## There are four supply system configurations to meet cooling demand in disconnected buildings
    # VCC: Vapor Compression Chiller, ACH: Absorption Chiller, CT: Cooling Tower, Boiler
    # config 1: VCC_to_AAS (AHU + ARU + SCU) + CT
    # config 2: VCC_to_AA (AHU + ARU) + VCC_to_S (SCU) + CT
    # config 3: VCC_to_AA (AHU + ARU) + ACH_S (SCU) + CT + Boiler
    # config 4: ACH_to_AAS (AHU + ARU + SCU) + Boiler

    for building_name in building_names:
        print building_name

        # create empty matrices
        result = np.zeros((4, 8))

        # assign cooling technologies (columns) to different configurations (rows)
        # technologies columns: [0] VCC_to_AAS ; [1] VCC_to_AA; [2] VCC_to_S ; [3] ACH_to_S; [4] ACH_to_AAS
        # config 1: VCC_to_AAS
        result[0][0] = 1
        # config 2: VCC_to_AA + VCC_to_S
        result[1][1] = 1
        result[1][2] = 1
        # config 3: VCC_to_AA + ACH_S
        result[2][1] = 1
        result[2][3]
        # config 4: ACH_to_AAS
        result[3][4] = 1

        q_CT_1_W = np.zeros(8760)
        q_CT_2_W = np.zeros(8760)
        q_CT_3_W = np.zeros(8760)
        q_CT_4_W = np.zeros(8760)
        q_boiler_3_W = np.zeros(8760)
        q_boiler_4_W = np.zeros(8760)
        T_re_boiler_3_K = np.zeros(8760)
        T_re_boiler_4_K = np.zeros(8760)
        InvCosts = np.zeros((4, 1))
        resourcesRes = np.zeros((4, 4))

        ## Calculate cooling loads for different combinations

        # AAS (AHU + ARU + SCU): combine all loads
        substation.substation_main(locator, total_demand, building_names=[building_name], Flag=False,
                                   heating_configuration=7, cooling_configuration=7, gv=gv)
        loads_AAS = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                usecols=["T_supply_DC_result_K", "T_return_DC_result_K", "mdot_DC_result_kgpers"])
        Qc_load_combination_AAS_W = np.vectorize(calc_new_load)(loads_AAS["mdot_DC_result_kgpers"],
                                                                loads_AAS["T_supply_DC_result_K"],
                                                                loads_AAS["T_return_DC_result_K"], gv, config)
        Qc_annual_combination_AAS_Wh = Qc_load_combination_AAS_W.sum()
        Qc_nom_combination_AAS_W = Qc_load_combination_AAS_W.max() * (
            1 + Qmargin_Disc)  # 20% reliability margin on installed capacity

        # AA (AHU + ARU): combine loads from AHU and ARU
        substation.substation_main(locator, total_demand, building_names=[building_name], Flag=False,
                                   heating_configuration=7, cooling_configuration=4, gv=gv)
        loads_AA = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                               usecols=["T_supply_DC_result_K", "T_return_DC_result_K", "mdot_DC_result_kgpers"])
        Qc_load_combination_AA_W = np.vectorize(calc_new_load)(loads_AA["mdot_DC_result_kgpers"],
                                                               loads_AA["T_supply_DC_result_K"],
                                                               loads_AA["T_return_DC_result_K"], gv, config)
        Qc_annual_combination_AA_Wh = Qc_load_combination_AA_W.sum()
        Qc_nom_combination_AA_W = Qc_load_combination_AA_W.max() * (
            1 + Qmargin_Disc)  # 20% reliability margin on installed capacity

        # S (SCU): loads from SCU
        substation.substation_main(locator, total_demand, building_names=[building_name], Flag=False,
                                   heating_configuration=7, cooling_configuration=3, gv=gv)
        loads_S = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                              usecols=["T_supply_DC_result_K", "T_return_DC_result_K", "mdot_DC_result_kgpers"])
        Qc_load_combination_S_W = np.vectorize(calc_new_load)(loads_S["mdot_DC_result_kgpers"],
                                                              loads_S["T_supply_DC_result_K"],
                                                              loads_S["T_return_DC_result_K"], gv, config)
        Qc_annual_combination_S_Wh = Qc_load_combination_S_W.sum()
        Qc_nom_combination_S_W = Qc_load_combination_S_W.max() * (
            1 + Qmargin_Disc)  # 20% reliability margin on installed capacity

        # read chilled water supply/return temperatures and mass flows from substation results files
        # AAS (AHU + ARU + SCU)
        T_re_AAS_K = loads_AAS["T_return_DC_result_K"].values
        T_sup_AAS_K = loads_AAS["T_supply_DC_result_K"].values
        mdot_AAS_kgpers = loads_AAS["mdot_DC_result_kgpers"].values
        # AA (AHU + ARU)
        T_re_AA_K = loads_AA["T_return_DC_result_K"].values
        T_sup_AA_K = loads_AA["T_supply_DC_result_K"].values
        mdot_AA_kgpers = loads_AA["mdot_DC_result_kgpers"].values
        # S (SCU)
        T_re_S_K = loads_S["T_return_DC_result_K"].values
        T_sup_S_K = loads_S["T_supply_DC_result_K"].values
        mdot_S_kgpers = loads_S["mdot_DC_result_kgpers"].values

        # calculate hot water supply conditions from SC and boiler
        SC_data = pd.read_csv(locator.SC_results(building_name=building_name),
                              usecols=["T_SC_sup_C", "T_SC_re_C", "mcp_SC_kWperC", "Q_SC_gen_kWh"])
        T_hw_in_C = [x if x > T_GENERATOR_IN_C else T_GENERATOR_IN_C for x in SC_data['T_SC_re_C']]
        q_sc_gen_Wh = SC_data['Q_SC_gen_kWh'] * 1000

        # calculate ground temperatures to estimate cold water supply temperatures
        T_ground_K = calculate_ground_temperature(locator)

        ## Calculate chiller operations
        for hour in range(8760):  # TODO: vectorize
            # modify return temperatures when there is no load
            T_re_AAS_K[hour] = T_re_AAS_K[hour] if T_re_AAS_K[hour] > 0 else T_sup_AAS_K[hour]
            T_re_AA_K[hour] = T_re_AA_K[hour] if T_re_AA_K[hour] > 0 else T_sup_AA_K[hour]
            T_re_S_K[hour] = T_re_S_K[hour] if T_re_S_K[hour] > 0 else T_sup_S_K[hour]

            # 1: VCC (AHU + ARU + SCU) + CT
            VCC_to_AAS_operation = chiller_vcc.calc_VCC(mdot_AAS_kgpers[hour], T_sup_AAS_K[hour], T_re_AAS_K[hour], gv)
            result[0][5] += prices.ELEC_PRICE * VCC_to_AAS_operation['wdot_W']  # CHF
            result[0][6] += EL_TO_CO2 * VCC_to_AAS_operation['wdot_W'] * 3600E-6  # kgCO2
            result[0][7] += EL_TO_OIL_EQ * VCC_to_AAS_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
            resourcesRes[0][0] += Qc_load_combination_AAS_W[hour]
            q_CT_1_W[hour] = VCC_to_AAS_operation['q_cw_W']

            # 2: VCC (AHU + ARU) + VCC (SCU) + CT
            VCC_to_AA_operation = chiller_vcc.calc_VCC(mdot_AA_kgpers[hour], T_sup_AA_K[hour], T_re_AA_K[hour],
                                                       gv)
            VCC_to_S_operation = chiller_vcc.calc_VCC(mdot_S_kgpers[hour], T_sup_S_K[hour], T_re_S_K[hour],
                                                      gv)
            result[1][5] += prices.ELEC_PRICE * (VCC_to_AA_operation['wdot_W'] + VCC_to_S_operation['wdot_W'])  # CHF
            result[1][6] += EL_TO_CO2 * (
                VCC_to_AA_operation['wdot_W'] + VCC_to_S_operation['wdot_W']) * 3600E-6  # kgCO2
            result[1][7] += EL_TO_OIL_EQ * (
                VCC_to_AA_operation['wdot_W'] + VCC_to_S_operation['wdot_W']) * 3600E-6  # MJ-oil-eq
            resourcesRes[1][0] += Qc_load_combination_AA_W[hour] + Qc_load_combination_S_W[hour]
            q_CT_2_W[hour] = VCC_to_AA_operation['q_cw_W'] + VCC_to_S_operation['q_cw_W']

            # 3: VCC (AHU + ARU) + ACH (SCU) + CT
            ACH_to_S_operation = chiller_abs.calc_chiller_abs_main(mdot_S_kgpers[hour], T_sup_S_K[hour], T_re_S_K[hour],
                                                                   T_hw_in_C[hour], T_ground_K[hour], Qc_nom_combination_S_W, locator, gv)
            result[2][5] += prices.ELEC_PRICE * (VCC_to_AA_operation['wdot_W'] + ACH_to_S_operation['wdot_W'])  # CHF
            result[2][6] += EL_TO_CO2 * (
                VCC_to_AA_operation['wdot_W'] + ACH_to_S_operation['wdot_W']) * 3600E-6  # kgCO2
            result[2][7] += EL_TO_OIL_EQ * (
                VCC_to_AA_operation['wdot_W'] + ACH_to_S_operation['wdot_W']) * 3600E-6  # MJ-oil-eq
            resourcesRes[2][0] += Qc_load_combination_AA_W[hour] + Qc_load_combination_S_W[hour]
            # calculate load for CT
            q_CT_3_W[hour] = VCC_to_AA_operation['q_cw_W'] + ACH_to_S_operation['q_cw_W']
            # calculate load for boiler
            q_boiler_3_W[hour] = ACH_to_S_operation['q_hw_W'] - q_sc_gen_Wh[hour] if (q_sc_gen_Wh[hour] >= 0) else \
                ACH_to_S_operation[
                    'q_hw_W']  # FIXME: this is assuming the mdot in SC is higher than hot water in the generator
            T_re_boiler_3_K[hour] = ACH_to_S_operation['T_hw_out_C'] + 273.15

            # 4: ACH (AHU + ARU + SCU)
            ACH_to_AAS_operation = chiller_abs.calc_chiller_abs_main(mdot_AAS_kgpers[hour], T_sup_AAS_K[hour],
                                                                     T_re_AAS_K[hour], T_hw_in_C[hour], T_ground_K[hour],
                                                                     Qc_nom_combination_AAS_W, locator, gv)
            result[3][4] += prices.ELEC_PRICE * ACH_to_AAS_operation['wdot_W']  # CHF
            result[3][5] += EL_TO_CO2 * ACH_to_AAS_operation['wdot_W'] * 3600E-6  # kgCO2
            result[3][6] += EL_TO_OIL_EQ * ACH_to_AAS_operation['wdot_W'] * 3600E-6  # MJ-oil-eq
            resourcesRes[3][0] += Qc_load_combination_AAS_W[hour]
            # calculate load for CT and boilers
            q_CT_4_W[hour] = ACH_to_AAS_operation['q_cw_W']
            q_boiler_4_W[hour] = ACH_to_AAS_operation['q_hw_W'] - q_sc_gen_Wh[hour] if (q_sc_gen_Wh[hour] >= 0) else \
                ACH_to_AAS_operation[
                    'q_hw_W']  # FIXME: this is assuming the mdot in SC is higher than hot water in the generator
            T_re_boiler_4_K[hour] = ACH_to_AAS_operation['T_hw_out_C'] + 273.15

        print 'Finish calculation for cooling technologies'

        ## Calculate CT and boiler operation

        # sizing of CT
        CT_1_nom_size_W = np.max(q_CT_1_W) * (1 + Qmargin_Disc)
        CT_2_nom_size_W = np.max(q_CT_2_W) * (1 + Qmargin_Disc)
        CT_3_nom_size_W = np.max(q_CT_3_W) * (1 + Qmargin_Disc)
        CT_4_nom_size_W = np.max(q_CT_4_W) * (1 + Qmargin_Disc)

        # sizing of boilers
        boiler_3_nom_size_W = np.max(q_boiler_3_W) * (1 + Qmargin_Disc)
        boiler_4_nom_size_W = np.max(q_boiler_4_W) * (1 + Qmargin_Disc)

        for hour in range(8760):
            # 1: VCC (AHU + ARU + SCU) + CT
            wdot_W = cooling_tower.calc_CT(q_CT_1_W[hour], CT_1_nom_size_W, gv)

            result[0][4] += prices.ELEC_PRICE * wdot_W  # CHF
            result[0][5] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
            result[0][6] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # 2: VCC (AHU + ARU) + VCC (SCU) + CT
            wdot_W = cooling_tower.calc_CT(q_CT_2_W[hour], CT_2_nom_size_W, gv)

            result[1][4] += prices.ELEC_PRICE * wdot_W  # CHF
            result[1][5] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
            result[1][6] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

            # 3: VCC (AHU + ARU) + ACH (SCU) + CT
            wdot_W = cooling_tower.calc_CT(q_CT_3_W[hour], CT_3_nom_size_W, gv)
            boiler_eff = boiler.calc_Cop_boiler(q_boiler_3_W[hour], boiler_3_nom_size_W, T_re_boiler_3_K[hour]) if \
            q_boiler_3_W[hour] > 0 else 0
            Q_gas_for_boiler_Wh = q_boiler_3_W[hour] / boiler_eff if boiler_eff > 0 else 0

            result[2][4] += prices.ELEC_PRICE * wdot_W + prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
            result[2][5] += (EL_TO_CO2 * wdot_W + NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
            result[2][6] += (
                                EL_TO_OIL_EQ * wdot_W + NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

            # 4: VCC (AHU + ARU + SCU) + CT
            wdot_W = cooling_tower.calc_CT(q_CT_4_W[hour], CT_4_nom_size_W, gv)
            boiler_eff = boiler.calc_Cop_boiler(q_boiler_4_W[hour], boiler_4_nom_size_W, T_re_boiler_4_K[hour]) if \
            q_boiler_4_W[hour] > 0 else 0
            Q_gas_for_boiler_Wh = q_boiler_4_W[hour] / boiler_eff if boiler_eff > 0 else 0

            result[3][4] += prices.ELEC_PRICE * wdot_W + prices.NG_PRICE * Q_gas_for_boiler_Wh  # CHF
            result[3][5] += (EL_TO_CO2 * wdot_W + NG_BACKUPBOILER_TO_CO2_STD * Q_gas_for_boiler_Wh) * 3600E-6  # kgCO2
            result[3][6] += (
                                EL_TO_OIL_EQ * wdot_W + NG_BACKUPBOILER_TO_OIL_STD * Q_gas_for_boiler_Wh) * 3600E-6  # MJ-oil-eq

        print 'Finish calculation for auxiliary technologies'

        ## Calculate Capex/Opex
        # 1: VCC (AHU + ARU + SCU) + CT
        Capex_a_VCC, Opex_VCC = chiller_vcc.calc_Cinv_VCC(Qc_nom_combination_AAS_W, gv, locator, technology=1)
        Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_1_nom_size_W, gv, locator, technology=0)
        InvCosts[0][0] = Capex_a_CT + Opex_CT + Capex_a_VCC + Opex_VCC

        # 2: VCC (AHU + ARU) + VCC (SCU) + CT
        Capex_a_VCC_AA, Opex_VCC_AA = chiller_vcc.calc_Cinv_VCC(Qc_nom_combination_AA_W, gv, locator, technology=1)
        Capex_a_VCC_S, Opex_VCC_S = chiller_vcc.calc_Cinv_VCC(Qc_nom_combination_S_W, gv, locator, technology=1)
        Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_2_nom_size_W, gv, locator, technology=0)
        InvCosts[1][0] = Capex_a_CT + Opex_CT + Capex_a_VCC_AA + Capex_a_VCC_S + Opex_VCC_AA + Opex_VCC_S

        # 3: VCC (AHU + ARU) + ACH (SCU) + CT + Boiler
        Capex_a_ACH_S, Opex_ACH_S = chiller_abs.calc_Cinv_chiller_abs(Qc_nom_combination_S_W, gv, locator, technology=0)
        Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_3_nom_size_W, gv, locator, technology=0)
        Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_3_nom_size_W, locator, config, technology=0)
        InvCosts[2][0] = Capex_a_CT + Opex_CT + \
                         Capex_a_VCC_AA + Opex_VCC_AA + \
                         Capex_a_ACH_S + Opex_ACH_S + \
                         Capex_a_boiler + Opex_boiler

        # 4: ACH (AHU + ARU + SCU) + CT + Boiler
        Capex_a_ACH_AAS, Opex_ACH_AAS = chiller_abs.calc_Cinv_chiller_abs(Qc_nom_combination_AAS_W, gv, locator,
                                                                          technology=0)
        Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_4_nom_size_W, gv, locator, technology=0)
        Capex_a_boiler, Opex_boiler = boiler.calc_Cinv_boiler(boiler_4_nom_size_W, locator, config, technology=0)
        InvCosts[3][0] = Capex_a_CT + Opex_CT + \
                         Capex_a_ACH_AAS + Opex_ACH_AAS + \
                         Capex_a_boiler + Opex_boiler

        print 'Finish calculation for costs'

        # Best configuration
        Best = np.zeros((4, 1))
        indexBest = 0

        TotalCosts = np.zeros((4, 2))
        TotalCO2 = np.zeros((4, 2))
        TotalPrim = np.zeros((4, 2))

        for i in range(4):
            TotalCosts[i][0] = TotalCO2[i][0] = TotalPrim[i][0] = i
            TotalCosts[i][1] = InvCosts[i][0] + result[i][5]
            TotalCO2[i][1] = result[i][6]
            TotalPrim[i][1] = result[i][7]

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
        Qnom = np.zeros((4, 5))
        Qnom_array = np.zeros(len(Best[:, 0])) * Qc_nom_combination_AAS_W
        Qnom_VCC = np.zeros()

        # Save results in csv file
        dico = {}
        dico["VCC Share"] = result[:, 0]
        dico["Abs_chiller Share"] = result[:, 1]
        dico["BoilerNG Share"] = result[:, 2]
        dico["GHP Share"] = result[:, 3]
        dico["Abs_AAS Share"] = result[:, 4]
        dico["Operation Costs [CHF]"] = result[:, 5]
        dico["CO2 Emissions [kgCO2-eq]"] = result[:, 6]
        dico["Primary Energy Needs [MJoil-eq]"] = result[:, 7]
        dico["Annualized Investment Costs [CHF]"] = InvCosts[:, 0]
        dico["Total Costs [CHF]"] = TotalCosts[:, 1]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power VCC_to_AAS"] = Qnom_array  # TODO: add different technologies
        dico["Nominal Power"] = Qnom_array
        dico["Nominal Power"] = Qnom_array
        dico["Nominal Power"] = Qnom_array
        dico["Nominal Power"] = Qnom_array
        dico["QfromNG"] = resourcesRes[:, 0]
        dico["QfromBG"] = resourcesRes[:, 1]
        dico["EforGHP"] = resourcesRes[:, 2]
        dico["QfromGHP"] = resourcesRes[:, 3]

        results_to_csv = pd.DataFrame(dico)
        fName_result = locator.get_optimization_disconnected_folder_building_result(building_name)
        results_to_csv.to_csv(fName_result, sep=',')

        BestComb = {}
        BestComb["BoilerNG Share"] = result[indexBest, 0]
        BestComb["BoilerBG Share"] = result[indexBest, 1]
        BestComb["FC Share"] = result[indexBest, 2]
        BestComb["GHP Share"] = result[indexBest, 3]
        BestComb["Operation Costs [CHF]"] = result[indexBest, 4]
        BestComb["CO2 Emissions [kgCO2-eq]"] = result[indexBest, 5]
        BestComb["Primary Energy Needs [MJoil-eq]"] = result[indexBest, 6]
        BestComb["Annualized Investment Costs [CHF]"] = InvCosts[indexBest, 0]
        BestComb["Total Costs [CHF]"] = TotalCosts[indexBest, 1]
        BestComb["Best configuration"] = Best[indexBest, 0]
        BestComb["Nominal Power VCC (aru) "] = Q_cooling_nom_W
        BestComb["Nominal Power VCC (aru) "] = Q_cooling_nom_W
        BestComb["Nominal Power VCC (aru) "] = Q_cooling_nom_W
        BestComb["Nominal Power VCC (aru) "] = Q_cooling_nom_W
        BestComb["Nominal Power VCC (aru) "] = Q_cooling_nom_W

        BestData[building_name] = BestComb

    if 0:
        fName = locator.get_optimization_disconnected_folder_disc_op_summary()
        results_to_csv = pd.DataFrame(BestData)
        results_to_csv.to_csv(fName, sep=',')

    print time.clock() - t0, "seconds process time for the Disconnected Building Routine \n"


# ============================
# other functions
# ============================
def calc_new_load(mdot_kgpers, T_sup_K, T_re_K, gv, config):
    """
    This function calculates the load distribution side of the district heating distribution.
    :param mdot_kgpers: mass flow
    :param T_sup_K: chilled water supply temperautre
    :param T_re_K: chilled water return temperature
    :param gv: global variables class
    :type mdot_kgpers: float
    :type TsupDH: float
    :type T_re_K: float
    :type gv: class
    :return: Q_cooling_load: load of the distribution
    :rtype: float
    """
    if mdot_kgpers > 0:
        Q_cooling_load_W = mdot_kgpers * gv.cp * (T_re_K - T_sup_K) * (1 + Qloss_Disc)  # for cooling load
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
    building_names = [building_names[6]]
    weather_file = config.weather
    prices = Prices(locator, config)
    decentralized_cooling_main(locator, building_names, gv, config, prices)

    print 'test_decentralized_buildings_cooling() succeeded'


if __name__ == '__main__':
    main(cea.config.Configuration())

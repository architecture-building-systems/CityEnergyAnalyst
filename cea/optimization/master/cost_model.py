# -*- coding: utf-8 -*-
"""
Extra costs to an individual

"""
from __future__ import division

import os

import cea.technologies.solar.photovoltaic as pv
import cea.technologies.solar.photovoltaic_thermal as pvt
import cea.technologies.solar.solar_collector as stc
import numpy as np
import pandas as pd
from cea.optimization.constants import N_PV, N_PVT, ETA_AREA_TO_PEAK
from cea.constants import DAYS_IN_YEAR, HOURS_IN_DAY, WH_TO_J
import cea.resources.natural_gas as ngas
import cea.technologies.boiler as boiler
import cea.technologies.cogeneration as chp
import cea.technologies.furnace as furnace
import cea.technologies.heat_exchangers as hex
import cea.technologies.thermal_network.thermal_network as network
import cea.technologies.heatpumps as hp
import cea.technologies.pumps as pumps
import cea.technologies.thermal_storage as storage
from cea.technologies.solar.photovoltaic import calc_Crem_pv


__author__ = "Tim Vollrath"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Tim Vollrath", "Thuy-An Nguyen", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def addCosts(DHN_barcode, DCN_barcode, buildList, locator, master_to_slave_vars, Q_uncovered_design_W,
             Q_uncovered_annual_W,
             solarFeat, ntwFeat, gv, config, prices, lca):
    """
    Computes additional costs / GHG emisions / primary energy needs
    for the individual
    addCosts = additional costs
    addCO2 = GHG emissions
    addPrm = primary energy needs
    :param DHN_barcode: parameter indicating if the building is connected or not
    :param buildList: list of buildings in the district
    :param locator: input locator set to scenario
    :param master_to_slave_vars: class containing the features of a specific individual
    :param Q_uncovered_design_W: hourly max of the heating uncovered demand
    :param Q_uncovered_annual_W: total heating uncovered
    :param solarFeat: solar features
    :param ntwFeat: network features
    :param gv: global variables
    :type indCombi: string
    :type buildList: list
    :type locator: string
    :type master_to_slave_vars: class
    :type Q_uncovered_design_W: float
    :type Q_uncovered_annual_W: float
    :type solarFeat: class
    :type ntwFeat: class
    :type gv: class

    :return: returns the objectives addCosts, addCO2, addPrim
    :rtype: tuple
    """
    addcosts_Capex_a = 0
    addcosts_Opex_fixed = 0
    addCO2 = 0
    addPrim = 0
    nBuildinNtw = 0
    
    # Add the features from the disconnected buildings
    CostDiscBuild = 0
    CO2DiscBuild = 0
    PrimDiscBuild = 0
    Capex_Disconnected = 0
    Opex_Disconnected = 0
    Capex_a_furnace = 0
    Capex_a_CHP = 0
    Capex_a_Boiler = 0
    Capex_a_Boiler_peak = 0
    Capex_a_Lake = 0
    Capex_a_Sewage = 0
    Capex_a_GHP = 0
    Capex_a_PV = 0
    Capex_a_SC = 0
    Capex_a_PVT = 0
    Capex_a_Boiler_backup = 0
    Capex_a_HEX = 0
    Capex_a_storage_HP = 0
    Capex_a_HP_storage = 0
    Opex_fixed_SC = 0
    Opex_fixed_PVT = 0
    Opex_fixed_HP_PVT = 0
    Opex_fixed_furnace = 0
    Opex_fixed_CHP = 0
    Opex_fixed_Boiler = 0
    Opex_fixed_Boiler_peak = 0
    Opex_fixed_Boiler_backup = 0
    Opex_fixed_Lake = 0
    Opex_fixed_wasteserver_HEX = 0
    Opex_fixed_wasteserver_HP = 0
    Opex_fixed_PV = 0
    Opex_fixed_GHP = 0
    Opex_fixed_storage = 0
    Opex_fixed_Sewage = 0
    Opex_fixed_HP_storage = 0
    StorageInvC = 0
    NetworkCost = 0
    SubstHEXCost_capex = 0
    SubstHEXCost_opex = 0
    PVTHEXCost_Capex = 0
    PVTHEXCost_Opex = 0
    SCHEXCost_Capex = 0
    SCHEXCost_Opex = 0
    pumpCosts = 0
    GasConnectionInvCost = 0
    cost_PV_disconnected = 0
    CO2_PV_disconnected = 0
    Eprim_PV_disconnected = 0

    if config.optimization.isheating:
        for (index, building_name) in zip(DHN_barcode, buildList):
            if index == "0":
                df = pd.read_csv(locator.get_optimization_disconnected_folder_building_result_heating(building_name))
                dfBest = df[df["Best configuration"] == 1]
                CostDiscBuild += dfBest["Total Costs [CHF]"].iloc[0] # [CHF]
                CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0] # [kg CO2]
                PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0] # [MJ-oil-eq]
                Capex_Disconnected += dfBest["Annualized Investment Costs [CHF]"].iloc[0]
                Opex_Disconnected += dfBest["Operation Costs [CHF]"].iloc[0]
            else:
                nBuildinNtw += 1
    if config.optimization.iscooling:
        PV_barcode = ''
        for (index, building_name) in zip(DCN_barcode, buildList):
            if index == "0":
                df = pd.read_csv(locator.get_optimization_disconnected_folder_building_result_cooling(building_name, configuration = 'AHU_ARU_SCU'))
                dfBest = df[df["Best configuration"] == 1]
                CostDiscBuild += dfBest["Total Costs [CHF]"].iloc[0] # [CHF]
                CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0] # [kg CO2]
                PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0] # [MJ-oil-eq]
                Capex_Disconnected += dfBest["Annualized Investment Costs [CHF]"].iloc[0]
                Opex_Disconnected += dfBest["Operation Costs [CHF]"].iloc[0]
                to_PV = 1
                if dfBest["single effect ACH to AHU_ARU_SCU Share (FP)"].iloc[0] == 1:
                    to_PV = 0
                if dfBest["single effect ACH to AHU_ARU_SCU Share (ET)"].iloc[0] == 1:
                    to_PV = 0
                if dfBest["single effect ACH to SCU Share (FP)"].iloc[0] == 1:
                    to_PV = 0


            else: # adding costs for buildings in which the centralized plant provides a part of the load requirements
                DCN_unit_configuration = master_to_slave_vars.DCN_supplyunits
                if DCN_unit_configuration == 1:  # corresponds to AHU in the central plant, so remaining load need to be provided by decentralized plant
                    decentralized_configuration = 'ARU_SCU'
                    df = pd.read_csv(
                        locator.get_optimization_disconnected_folder_building_result_cooling(building_name, decentralized_configuration))
                    dfBest = df[df["Best configuration"] == 1]
                    CostDiscBuild += dfBest["Total Costs [CHF]"].iloc[0] # [CHF]
                    CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0] # [kg CO2]
                    PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0] # [MJ-oil-eq]
                    Capex_Disconnected += dfBest["Annualized Investment Costs [CHF]"].iloc[0]
                    Opex_Disconnected += dfBest["Operation Costs [CHF]"].iloc[0]
                    to_PV = 1
                    if dfBest["single effect ACH to ARU_SCU Share (FP)"].iloc[0] == 1:
                        to_PV = 0
                    if dfBest["single effect ACH to ARU_SCU Share (ET)"].iloc[0] == 1:
                        to_PV = 0


                if DCN_unit_configuration == 2:  # corresponds to ARU in the central plant, so remaining load need to be provided by decentralized plant
                    decentralized_configuration = 'AHU_SCU'
                    df = pd.read_csv(
                        locator.get_optimization_disconnected_folder_building_result_cooling(building_name, decentralized_configuration))
                    dfBest = df[df["Best configuration"] == 1]
                    CostDiscBuild += dfBest["Total Costs [CHF]"].iloc[0] # [CHF]
                    CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0] # [kg CO2]
                    PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0] # [MJ-oil-eq]
                    Capex_Disconnected += dfBest["Annualized Investment Costs [CHF]"].iloc[0]
                    Opex_Disconnected += dfBest["Operation Costs [CHF]"].iloc[0]
                    to_PV = 1
                    if dfBest["single effect ACH to AHU_SCU Share (FP)"].iloc[0] == 1:
                        to_PV = 0
                    if dfBest["single effect ACH to AHU_SCU Share (ET)"].iloc[0] == 1:
                        to_PV = 0

                if DCN_unit_configuration == 3:  # corresponds to SCU in the central plant, so remaining load need to be provided by decentralized plant
                    decentralized_configuration = 'AHU_ARU'
                    df = pd.read_csv(
                        locator.get_optimization_disconnected_folder_building_result_cooling(building_name, decentralized_configuration))
                    dfBest = df[df["Best configuration"] == 1]
                    CostDiscBuild += dfBest["Total Costs [CHF]"].iloc[0] # [CHF]
                    CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0] # [kg CO2]
                    PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0] # [MJ-oil-eq]
                    Capex_Disconnected += dfBest["Annualized Investment Costs [CHF]"].iloc[0]
                    Opex_Disconnected += dfBest["Operation Costs [CHF]"].iloc[0]
                    to_PV = 1
                    if dfBest["single effect ACH to AHU_ARU Share (FP)"].iloc[0] == 1:
                        to_PV = 0
                    if dfBest["single effect ACH to AHU_ARU Share (ET)"].iloc[0] == 1:
                        to_PV = 0

                if DCN_unit_configuration == 4:  # corresponds to AHU + ARU in the central plant, so remaining load need to be provided by decentralized plant
                    decentralized_configuration = 'SCU'
                    df = pd.read_csv(
                        locator.get_optimization_disconnected_folder_building_result_cooling(building_name, decentralized_configuration))
                    dfBest = df[df["Best configuration"] == 1]
                    CostDiscBuild += dfBest["Total Costs [CHF]"].iloc[0] # [CHF]
                    CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0] # [kg CO2]
                    PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0] # [MJ-oil-eq]
                    Capex_Disconnected += dfBest["Annualized Investment Costs [CHF]"].iloc[0]
                    Opex_Disconnected += dfBest["Operation Costs [CHF]"].iloc[0]
                    to_PV = 1
                    if dfBest["single effect ACH to SCU Share (FP)"].iloc[0] == 1:
                        to_PV = 0
                    if dfBest["single effect ACH to SCU Share (ET)"].iloc[0] == 1:
                        to_PV = 0

                if DCN_unit_configuration == 5:  # corresponds to AHU + SCU in the central plant, so remaining load need to be provided by decentralized plant
                    decentralized_configuration = 'ARU'
                    df = pd.read_csv(
                        locator.get_optimization_disconnected_folder_building_result_cooling(building_name, decentralized_configuration))
                    dfBest = df[df["Best configuration"] == 1]
                    CostDiscBuild += dfBest["Total Costs [CHF]"].iloc[0] # [CHF]
                    CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0] # [kg CO2]
                    PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0] # [MJ-oil-eq]
                    Capex_Disconnected += dfBest["Annualized Investment Costs [CHF]"].iloc[0]
                    Opex_Disconnected += dfBest["Operation Costs [CHF]"].iloc[0]
                    to_PV = 1
                    if dfBest["single effect ACH to ARU Share (FP)"].iloc[0] == 1:
                        to_PV = 0
                    if dfBest["single effect ACH to ARU Share (ET)"].iloc[0] == 1:
                        to_PV = 0

                if DCN_unit_configuration == 6:  # corresponds to ARU + SCU in the central plant, so remaining load need to be provided by decentralized plant
                    decentralized_configuration = 'AHU'
                    df = pd.read_csv(
                        locator.get_optimization_disconnected_folder_building_result_cooling(building_name, decentralized_configuration))
                    dfBest = df[df["Best configuration"] == 1]
                    CostDiscBuild += dfBest["Total Costs [CHF]"].iloc[0] # [CHF]
                    CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0] # [kg CO2]
                    PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0] # [MJ-oil-eq]
                    Capex_Disconnected += dfBest["Annualized Investment Costs [CHF]"].iloc[0]
                    Opex_Disconnected += dfBest["Operation Costs [CHF]"].iloc[0]
                    to_PV = 1
                    if dfBest["single effect ACH to AHU Share (FP)"].iloc[0] == 1:
                        to_PV = 0
                    if dfBest["single effect ACH to AHU Share (ET)"].iloc[0] == 1:
                        to_PV = 0

                if DCN_unit_configuration == 7: # corresponds to AHU + ARU + SCU from central plant
                    to_PV = 1

                nBuildinNtw += 1
            PV_barcode = PV_barcode + str(to_PV)


    addcosts_Capex_a += CostDiscBuild
    addCO2 += CO2DiscBuild
    addPrim += PrimDiscBuild

    if not config.optimization.isheating:
        if PV_barcode.count("1") > 0:
            df1 = pd.DataFrame({'A': []})
            for (i, index) in enumerate(PV_barcode):
                if index == str(1):
                    if df1.empty:
                        data = pd.read_csv(locator.PV_results(buildList[i]))
                        df1 = data
                    else:
                        data = pd.read_csv(locator.PV_results(buildList[i]))
                        df1 = df1 + data
            if not df1.empty:
                df1.to_csv(locator.PV_network(PV_barcode), index=True, float_format='%.2f')

            solar_data = pd.read_csv(locator.PV_network(PV_barcode), usecols=['E_PV_gen_kWh', 'Area_PV_m2'], nrows=8760)
            E_PV_sum_kW = np.sum(solar_data['E_PV_gen_kWh'])
            E_PV_W = solar_data['E_PV_gen_kWh'] * 1000
            Area_AvailablePV_m2 = np.max(solar_data['Area_PV_m2'])
            Q_PowerPeakAvailablePV_kW = Area_AvailablePV_m2 * ETA_AREA_TO_PEAK
            KEV_RpPerkWhPV = calc_Crem_pv(Q_PowerPeakAvailablePV_kW * 1000.0)
            KEV_total = KEV_RpPerkWhPV / 100 * np.sum(E_PV_sum_kW)

            addcosts_Capex_a = addcosts_Capex_a - KEV_total
            addCO2 = addCO2 - (E_PV_sum_kW * 1000 * (lca.EL_PV_TO_CO2 - lca.EL_TO_CO2_GREEN) * WH_TO_J / 1.0E6)
            addPrim = addPrim - (E_PV_sum_kW * 1000 * (lca.EL_PV_TO_OIL_EQ - lca.EL_TO_OIL_EQ_GREEN) * WH_TO_J / 1.0E6)

            cost_PV_disconnected = KEV_total
            CO2_PV_disconnected = (E_PV_sum_kW * 1000 * (lca.EL_PV_TO_CO2 - lca.EL_TO_CO2_GREEN) * WH_TO_J / 1.0E6)
            Eprim_PV_disconnected = (E_PV_sum_kW * 1000 * (lca.EL_PV_TO_OIL_EQ - lca.EL_TO_OIL_EQ_GREEN) * WH_TO_J / 1.0E6)

            network_data = pd.read_csv(
                locator.get_optimization_network_data_folder(master_to_slave_vars.network_data_file_cooling))

            E_total_req_W = np.array(network_data['Electr_netw_total_W'])
            cooling_data = pd.read_csv(locator.get_optimization_slave_cooling_activation_pattern(master_to_slave_vars.individual_number,
                                                                                     master_to_slave_vars.generation_number))

            E_from_CHP_W = np.array(cooling_data['E_gen_CCGT_associated_with_absorption_chillers_W'])
            E_CHP_to_directload_W = np.zeros(8760)
            E_CHP_to_grid_W = np.zeros(8760)
            E_PV_to_directload_W = np.zeros(8760)
            E_PV_to_grid_W = np.zeros(8760)
            E_from_grid_W = np.zeros(8760)

            for hour in range(8760):
                E_hour_W = E_total_req_W[hour]
                if E_hour_W > 0:
                    if E_PV_W[hour] > E_hour_W:
                        E_PV_to_directload_W[hour] = E_hour_W
                        E_PV_to_grid_W[hour] = E_PV_W[hour] - E_total_req_W[hour]
                        E_hour_W = 0
                    else:
                        E_hour_W = E_hour_W - E_PV_W[hour]
                        E_PV_to_directload_W[hour] = E_PV_W[hour]

                    if E_from_CHP_W[hour] > E_hour_W:
                        E_CHP_to_directload_W[hour] = E_hour_W
                        E_CHP_to_grid_W[hour] = E_from_CHP_W[hour] - E_hour_W
                        E_hour_W = 0
                    else:
                        E_hour_W = E_hour_W - E_from_CHP_W[hour]
                        E_CHP_to_directload_W[hour] = E_from_CHP_W[hour]

                    E_from_grid_W[hour] = E_hour_W


            date = network_data.DATE.values
            results = pd.DataFrame({"DATE": date,
                                    "E_total_req_W": E_total_req_W,
                                    "E_PV_W": solar_data['E_PV_gen_kWh'] * 1000,
                                    "Area_PV_m2": solar_data['Area_PV_m2'],
                                    "KEV": KEV_RpPerkWhPV/100 * solar_data['E_PV_gen_kWh'],
                                    "E_from_grid_W": E_from_grid_W,
                                    "E_PV_to_directload_W": E_PV_to_directload_W,
                                    "E_CHP_to_directload_W": E_CHP_to_directload_W,
                                    "E_CHP_to_grid_W": E_CHP_to_grid_W,
                                    "E_PV_to_grid_W": E_PV_to_grid_W
                                    })

            results.to_csv(locator.get_optimization_slave_electricity_activation_pattern_cooling(master_to_slave_vars.individual_number,
                                                                                     master_to_slave_vars.generation_number), index=False)


    # Add the features for the distribution

    if DHN_barcode.count("1") > 0 and config.optimization.isheating:
        os.chdir(locator.get_optimization_slave_results_folder(master_to_slave_vars.generation_number))
        # Add the investment costs of the energy systems
        # Furnace
        if master_to_slave_vars.Furnace_on == 1:
            P_design_W = master_to_slave_vars.Furnace_Q_max

            fNameSlavePP = locator.get_optimization_slave_heating_activation_pattern_heating(master_to_slave_vars.configKey,
                                                                                     master_to_slave_vars.individual_number,
                                                                                     master_to_slave_vars.generation_number)
            dfFurnace = pd.read_csv(fNameSlavePP, usecols=["Q_Furnace_W"])
            arrayFurnace_W = np.array(dfFurnace)

            Q_annual_W = 0
            for i in range(int(np.shape(arrayFurnace_W)[0])):
                Q_annual_W += arrayFurnace_W[i][0]

            Capex_a_furnace, Opex_fixed_furnace = furnace.calc_Cinv_furnace(P_design_W, Q_annual_W, config, locator, 'FU1')
            addcosts_Capex_a += Capex_a_furnace
            addcosts_Opex_fixed += Opex_fixed_furnace

        # CC
        if master_to_slave_vars.CC_on == 1:
            CC_size_W = master_to_slave_vars.CC_GT_SIZE
            Capex_a_CHP, Opex_fixed_CHP = chp.calc_Cinv_CCGT(CC_size_W, locator, config)
            addcosts_Capex_a += Capex_a_CHP
            addcosts_Opex_fixed += Opex_fixed_CHP

        # Boiler Base
        if master_to_slave_vars.Boiler_on == 1:
            Q_design_W = master_to_slave_vars.Boiler_Q_max

            fNameSlavePP = locator.get_optimization_slave_heating_activation_pattern(
                master_to_slave_vars.individual_number,
                master_to_slave_vars.generation_number)
            dfBoilerBase = pd.read_csv(fNameSlavePP, usecols=["Q_BaseBoiler_W"])
            arrayBoilerBase_W = np.array(dfBoilerBase)

            Q_annual_W = 0
            for i in range(int(np.shape(arrayBoilerBase_W)[0])):
                Q_annual_W += arrayBoilerBase_W[i][0]

            Capex_a_Boiler, Opex_fixed_Boiler = boiler.calc_Cinv_boiler(Q_design_W, locator, config, 'BO1')
            addcosts_Capex_a += Capex_a_Boiler
            addcosts_Opex_fixed += Opex_fixed_Boiler

        # Boiler Peak
        if master_to_slave_vars.BoilerPeak_on == 1:
            Q_design_W = master_to_slave_vars.BoilerPeak_Q_max

            fNameSlavePP = locator.get_optimization_slave_heating_activation_pattern(
                master_to_slave_vars.individual_number,
                master_to_slave_vars.generation_number)
            dfBoilerPeak = pd.read_csv(fNameSlavePP, usecols=["Q_PeakBoiler_W"])
            arrayBoilerPeak_W = np.array(dfBoilerPeak)

            Q_annual_W = 0
            for i in range(int(np.shape(arrayBoilerPeak_W)[0])):
                Q_annual_W += arrayBoilerPeak_W[i][0]
            Capex_a_Boiler_peak, Opex_fixed_Boiler_peak = boiler.calc_Cinv_boiler(Q_design_W, locator, config, 'BO1')
            addcosts_Capex_a += Capex_a_Boiler_peak
            addcosts_Opex_fixed += Opex_fixed_Boiler_peak

        # HP Lake
        if master_to_slave_vars.HP_Lake_on == 1:
            HP_Size_W = master_to_slave_vars.HPLake_maxSize
            Capex_a_Lake, Opex_fixed_Lake = hp.calc_Cinv_HP(HP_Size_W, locator, config, 'HP2')
            addcosts_Capex_a += Capex_a_Lake
            addcosts_Opex_fixed += Opex_fixed_Lake

        # HP Sewage
        if master_to_slave_vars.HP_Sew_on == 1:
            HP_Size_W = master_to_slave_vars.HPSew_maxSize
            Capex_a_Sewage, Opex_fixed_Sewage = hp.calc_Cinv_HP(HP_Size_W, locator, config, 'HP2')
            addcosts_Capex_a += Capex_a_Sewage
            addcosts_Opex_fixed += Opex_fixed_Sewage

        # GHP
        if master_to_slave_vars.GHP_on == 1:
            fNameSlavePP = locator.get_optimization_slave_electricity_activation_pattern_heating(
                master_to_slave_vars.individual_number,
                master_to_slave_vars.generation_number)
            dfGHP = pd.read_csv(fNameSlavePP, usecols=["E_GHP_req_W"])
            arrayGHP_W = np.array(dfGHP)

            GHP_Enom_W = np.amax(arrayGHP_W)
            Capex_a_GHP, Opex_fixed_GHP = hp.calc_Cinv_GHP(GHP_Enom_W, locator, config)
            addcosts_Capex_a += Capex_a_GHP * prices.EURO_TO_CHF
            addcosts_Opex_fixed += Opex_fixed_GHP * prices.EURO_TO_CHF

        # Solar technologies

        PV_installed_area_m2 = master_to_slave_vars.SOLAR_PART_PV * solarFeat.A_PV_m2 #kW
        Capex_a_PV, Opex_fixed_PV = pv.calc_Cinv_pv(PV_installed_area_m2, locator, config)
        addcosts_Capex_a += Capex_a_PV
        addcosts_Opex_fixed += Opex_fixed_PV

        SC_ET_area_m2 = master_to_slave_vars.SOLAR_PART_SC_ET * solarFeat.A_SC_ET_m2
        Capex_a_SC_ET, Opex_fixed_SC_ET = stc.calc_Cinv_SC(SC_ET_area_m2, locator, config, 'ET')
        addcosts_Capex_a += Capex_a_SC_ET
        addcosts_Opex_fixed += Opex_fixed_SC_ET

        SC_FP_area_m2 = master_to_slave_vars.SOLAR_PART_SC_FP * solarFeat.A_SC_FP_m2
        Capex_a_SC_FP, Opex_fixed_SC_FP = stc.calc_Cinv_SC(SC_FP_area_m2, locator, config, 'FP')
        addcosts_Capex_a += Capex_a_SC_FP
        addcosts_Opex_fixed += Opex_fixed_SC_FP

        PVT_peak_kW = master_to_slave_vars.SOLAR_PART_PVT * solarFeat.A_PVT_m2 * N_PVT #kW
        Capex_a_PVT, Opex_fixed_PVT = pvt.calc_Cinv_PVT(PVT_peak_kW, locator, config)
        addcosts_Capex_a += Capex_a_PVT
        addcosts_Opex_fixed += Opex_fixed_PVT

        # Back-up boiler
        Capex_a_Boiler_backup, Opex_fixed_Boiler_backup = boiler.calc_Cinv_boiler(Q_uncovered_design_W, locator, config, 'BO1')
        addcosts_Capex_a += Capex_a_Boiler_backup
        addcosts_Opex_fixed += Opex_fixed_Boiler_backup

        # Hex and HP for Heat recovery
        if master_to_slave_vars.WasteServersHeatRecovery == 1:
            df = pd.read_csv(
                os.path.join(locator.get_optimization_network_results_folder(), master_to_slave_vars.network_data_file_heating),
                usecols=["Qcdata_netw_total_kWh"])
            array = np.array(df)
            Q_HEX_max_kWh = np.amax(array)
            Capex_a_wasteserver_HEX, Opex_fixed_wasteserver_HEX = hex.calc_Cinv_HEX(Q_HEX_max_kWh, locator, config, 'HEX1')
            addcosts_Capex_a += (Capex_a_wasteserver_HEX)
            addcosts_Opex_fixed += Opex_fixed_wasteserver_HEX

            df = pd.read_csv(
                locator.get_optimization_slave_storage_operation_data(master_to_slave_vars.individual_number,
                                                                      master_to_slave_vars.generation_number),
                usecols=["HPServerHeatDesignArray_kWh"])
            array = np.array(df)
            Q_HP_max_kWh = np.amax(array)
            Capex_a_wasteserver_HP, Opex_fixed_wasteserver_HP = hp.calc_Cinv_HP(Q_HP_max_kWh, locator, config, 'HP2')
            addcosts_Capex_a += (Capex_a_wasteserver_HP)
            addcosts_Opex_fixed += Opex_fixed_wasteserver_HP

        # if master_to_slave_vars.WasteCompressorHeatRecovery == 1:
        #     df = pd.read_csv(
        #         os.path.join(locator.get_optimization_network_results_folder(), master_to_slave_vars.network_data_file_heating),
        #         usecols=["Ecaf_netw_total_kWh"])
        #     array = np.array(df)
        #     Q_HEX_max_kWh = np.amax(array)
        #
        #     Capex_a_wastecompressor_HEX, Opex_fixed_wastecompressor_HEX = hex.calc_Cinv_HEX(Q_HEX_max_kWh, locator,
        #                                                                                     config, 'HEX1')
        #     addcosts_Capex_a += (Capex_a_wastecompressor_HEX)
        #     addcosts_Opex_fixed += Opex_fixed_wastecompressor_HEX
        #     df = pd.read_csv(
        #         locator.get_optimization_slave_storage_operation_data(master_to_slave_vars.individual_number,
        #                                                               master_to_slave_vars.generation_number),
        #         usecols=["HPCompAirDesignArray_kWh"])
        #     array = np.array(df)
        #     Q_HP_max_kWh = np.amax(array)
        #     Capex_a_wastecompressor_HP, Opex_fixed_wastecompressor_HP = hp.calc_Cinv_HP(Q_HP_max_kWh, locator, config, 'HP2')
        #     addcosts_Capex_a += (Capex_a_wastecompressor_HP)
        #     addcosts_Opex_fixed += Opex_fixed_wastecompressor_HP

        # Heat pump from solar to DH
        df = pd.read_csv(locator.get_optimization_slave_storage_operation_data(master_to_slave_vars.individual_number,
                                                                               master_to_slave_vars.generation_number),
                         usecols=["HPScDesignArray_Wh", "HPpvt_designArray_Wh"])
        array = np.array(df)
        Q_HP_max_PVT_wh = np.amax(array[:, 1])
        Q_HP_max_SC_Wh = np.amax(array[:, 0])
        Capex_a_HP_PVT, Opex_fixed_HP_PVT = hp.calc_Cinv_HP(Q_HP_max_PVT_wh, locator, config, 'HP2')
        Capex_a_storage_HP += (Capex_a_HP_PVT)
        addcosts_Opex_fixed += Opex_fixed_HP_PVT

        Capex_a_HP_SC, Opex_fixed_HP_SC = hp.calc_Cinv_HP(Q_HP_max_SC_Wh, locator, config, 'HP2')
        Capex_a_storage_HP += (Capex_a_HP_SC)
        addcosts_Opex_fixed += Opex_fixed_HP_SC

        # HP for storage operation for charging from solar and discharging to DH
        df = pd.read_csv(locator.get_optimization_slave_storage_operation_data(master_to_slave_vars.individual_number,
                                                                               master_to_slave_vars.generation_number),
                         usecols=["E_aux_ch_W", "E_aux_dech_W", "Q_from_storage_used_W", "Q_to_storage_W"])
        array = np.array(df)
        Q_HP_max_storage_W = 0
        for i in range(DAYS_IN_YEAR * HOURS_IN_DAY):
            if array[i][0] > 0:
                Q_HP_max_storage_W = max(Q_HP_max_storage_W, array[i][3] + array[i][0])
            elif array[i][1] > 0:
                Q_HP_max_storage_W = max(Q_HP_max_storage_W, array[i][2] + array[i][1])

        Capex_a_HP_storage, Opex_fixed_HP_storage = hp.calc_Cinv_HP(Q_HP_max_storage_W, locator, config, 'HP2')
        addcosts_Capex_a += (Capex_a_HP_storage)
        addcosts_Opex_fixed += Opex_fixed_HP_storage

        # Storage
        df = pd.read_csv(locator.get_optimization_slave_storage_operation_data(master_to_slave_vars.individual_number,
                                                                               master_to_slave_vars.generation_number),
                         usecols=["Storage_Size_m3"], nrows=1)
        StorageVol_m3 = np.array(df)[0][0]
        Capex_a_storage, Opex_fixed_storage = storage.calc_Cinv_storage(StorageVol_m3, locator, config, 'TES2')
        addcosts_Capex_a += Capex_a_storage
        addcosts_Opex_fixed += Opex_fixed_storage

        # Costs from distribution configuration
        if gv.ZernezFlag == 1:
            NetworkCost += network.calc_Cinv_network_linear(gv.NetworkLengthZernez, gv) * nBuildinNtw / len(buildList)
        else:
            NetworkCost += ntwFeat.pipesCosts_DHN * nBuildinNtw / len(buildList)
        addcosts_Capex_a += NetworkCost

        # HEX (1 per building in ntw)
        for (index, building_name) in zip(DHN_barcode, buildList):
            if index == "1":
                df = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                 usecols=["Q_dhw_W", "Q_heating_W"])
                subsArray = np.array(df)

                Q_max_W = np.amax(subsArray[:, 0] + subsArray[:, 1])
                Capex_a_HEX_building, Opex_fixed_HEX_building = hex.calc_Cinv_HEX(Q_max_W, locator, config, 'HEX1')
                addcosts_Capex_a += Capex_a_HEX_building
                addcosts_Opex_fixed += Opex_fixed_HEX_building

        # HEX for solar
        roof_area_m2 = np.array(pd.read_csv(locator.get_total_demand(), usecols=["Aroof_m2"]))

        areaAvail = 0
        for i in range(len(DHN_barcode)):
            index = DHN_barcode[i]
            if index == "1":
                areaAvail += roof_area_m2[i][0]

        for i in range(len(DHN_barcode)):
            index = DHN_barcode[i]
            if index == "1":
                share = roof_area_m2[i][0] / areaAvail
                #print share, "solar area share", buildList[i]
                
                Q_max_SC_ET_Wh = solarFeat.Q_nom_SC_ET_Wh * master_to_slave_vars.SOLAR_PART_SC_ET * share
                Capex_a_HEX_SC_ET, Opex_fixed_HEX_SC_ET = hex.calc_Cinv_HEX(Q_max_SC_ET_Wh, locator, config, 'HEX1')
                addcosts_Capex_a += Capex_a_HEX_SC_ET
                addcosts_Opex_fixed += Opex_fixed_HEX_SC_ET

                Q_max_SC_FP_Wh = solarFeat.Q_nom_SC_FP_Wh * master_to_slave_vars.SOLAR_PART_SC_FP * share
                Capex_a_HEX_SC_FP, Opex_fixed_HEX_SC_FP = hex.calc_Cinv_HEX(Q_max_SC_FP_Wh, locator, config, 'HEX1')
                addcosts_Capex_a += Capex_a_HEX_SC_FP
                addcosts_Opex_fixed += Opex_fixed_HEX_SC_FP

                Q_max_PVT_Wh = solarFeat.Q_nom_PVT_Wh * master_to_slave_vars.SOLAR_PART_PVT * share
                Capex_a_HEX_PVT, Opex_fixed_HEX_PVT = hex.calc_Cinv_HEX(Q_max_PVT_Wh, locator, config, 'HEX1')
                addcosts_Capex_a += Capex_a_HEX_PVT
                addcosts_Opex_fixed += Opex_fixed_HEX_PVT

    # Pump operation costs
    Capex_a_pump, Opex_fixed_pump, Opex_var_pump = pumps.calc_Ctot_pump(master_to_slave_vars, ntwFeat, gv, locator, lca, config)
    addcosts_Capex_a += Capex_a_pump
    addcosts_Opex_fixed += Opex_fixed_pump

    # import gas consumption data from:
    if DHN_barcode.count("1") > 0 and config.optimization.isheating:
        # import gas consumption data from:
        EgasPrimaryDataframe_W = pd.read_csv(
            locator.get_optimization_slave_cost_prime_primary_energy_data(master_to_slave_vars.individual_number,
                                                                          master_to_slave_vars.generation_number),
            usecols=["E_gas_PrimaryPeakPower_W"])
        E_gas_primary_peak_power_W = float(np.array(EgasPrimaryDataframe_W))
        GasConnectionInvCost = ngas.calc_Cinv_gas(E_gas_primary_peak_power_W, gv)
    else:
        GasConnectionInvCost = 0.0

    addcosts_Capex_a += GasConnectionInvCost
    # Save data
    results = pd.DataFrame({
        "Capex_a_SC": [Capex_a_SC],
        "Opex_fixed_SC": [Opex_fixed_SC],
        "Capex_a_PVT": [Capex_a_PVT],
        "Opex_fixed_PVT": [Opex_fixed_PVT],
        "Capex_a_Boiler_backup": [Capex_a_Boiler_backup],
        "Opex_fixed_Boiler_backup": [Opex_fixed_Boiler_backup],
        "Capex_a_storage_HEX": [Capex_a_HP_storage],
        "Opex_fixed_storage_HEX": [Opex_fixed_HP_storage],
        "Capex_a_storage_HP": [Capex_a_storage_HP],
        "Capex_a_CHP": [Capex_a_CHP],
        "Opex_fixed_CHP": [Opex_fixed_CHP],
        "StorageInvC": [StorageInvC],
        "StorageCostSum": [StorageInvC + Capex_a_storage_HP + Capex_a_HEX],
        "NetworkCost": [NetworkCost],
        "SubstHEXCost": [SubstHEXCost_capex],
        "DHNInvestCost": [addcosts_Capex_a - CostDiscBuild],
        "PVTHEXCost_Capex": [PVTHEXCost_Capex],
        "CostDiscBuild": [CostDiscBuild],
        "CO2DiscBuild": [CO2DiscBuild],
        "PrimDiscBuild": [PrimDiscBuild],
        "Capex_a_furnace": [Capex_a_furnace],
        "Opex_fixed_furnace": [Opex_fixed_furnace],
        "Capex_a_Boiler": [Capex_a_Boiler],
        "Opex_fixed_Boiler": [Opex_fixed_Boiler],
        "Capex_a_Boiler_peak": [Capex_a_Boiler_peak],
        "Opex_fixed_Boiler_peak": [Opex_fixed_Boiler_peak],
        "Capex_Disconnected": [Capex_Disconnected],
        "Opex_Disconnected": [Opex_Disconnected],
        "Capex_a_Lake": [Capex_a_Lake],
        "Opex_fixed_Lake":[Opex_fixed_Lake],
        "Capex_a_Sewage": [Capex_a_Sewage],
        "Opex_fixed_Sewage": [Opex_fixed_Sewage],
        "SCHEXCost_Capex": [SCHEXCost_Capex],
        "Capex_a_pump": [Capex_a_pump],
        "Opex_fixed_pump": [Opex_fixed_pump],
        "Opex_var_pump": [Opex_var_pump],
        "Sum_CAPEX": [addcosts_Capex_a],
        "Sum_OPEX_fixed": [addcosts_Opex_fixed],
        "GasConnectionInvCa": [GasConnectionInvCost],
        "CO2_PV_disconnected": [CO2_PV_disconnected],
        "cost_PV_disconnected": [cost_PV_disconnected],
        "Eprim_PV_disconnected": [Eprim_PV_disconnected]
    })
    results.to_csv(locator.get_optimization_slave_investment_cost_detailed(master_to_slave_vars.individual_number,
                                                                           master_to_slave_vars.generation_number),
                   sep=',')
    return (addcosts_Capex_a + addcosts_Opex_fixed, addCO2, addPrim)
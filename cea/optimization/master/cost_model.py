# -*- coding: utf-8 -*-
"""
Extra costs to an individual

"""
from __future__ import division
import os

import numpy as np
import pandas as pd
from cea.optimization.constants import N_PV, N_PVT, ETA_AREA_TO_PEAK, PIPELIFETIME, PIPEINTERESTRATE
from cea.constants import DAYS_IN_YEAR, HOURS_IN_DAY, WH_TO_J
import cea.resources.natural_gas as ngas
import cea.technologies.boiler as boiler
import cea.technologies.cogeneration as chp
import cea.technologies.furnace as furnace
import cea.technologies.heat_exchangers as hex
import cea.technologies.thermal_network.thermal_network as network
import cea.technologies.heatpumps as hp
import cea.technologies.pumps as pumps
import cea.technologies.solar.photovoltaic as pv
import cea.technologies.solar.photovoltaic_thermal as pvt
import cea.technologies.solar.solar_collector as stc
import cea.technologies.thermal_storage as storage

__author__ = "Tim Vollrath"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Tim Vollrath", "Thuy-An Nguyen", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def addCosts(buildList, locator, master_to_slave_vars, Q_uncovered_design_W,
             Q_uncovered_annual_W, solar_features, network_features, gv, config, prices, lca):

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
    :param solar_features: solar features
    :param network_features: network features
    :param gv: global variables
    :type indCombi: string
    :type buildList: list
    :type locator: string
    :type master_to_slave_vars: class
    :type Q_uncovered_design_W: float
    :type Q_uncovered_annual_W: float
    :type solar_features: class
    :type network_features: class
    :type gv: class

    :return: returns the objectives addCosts, addCO2, addPrim
    :rtype: tuple
    """
    DHN_barcode = master_to_slave_vars.DHN_barcode
    DCN_barcode = master_to_slave_vars.DCN_barcode
    addcosts_Capex_a_USD = 0
    addcosts_Opex_fixed_USD = 0
    addcosts_Capex_USD = 0
    addCO2 = 0
    addPrim = 0
    nBuildinNtw = 0
    
    # Add the features from the disconnected buildings
    CostDiscBuild = 0
    CO2DiscBuild = 0
    PrimDiscBuild = 0
    Capex_Disconnected = 0
    Opex_Disconnected = 0
    Capex_a_furnace_USD = 0
    Capex_a_CHP_USD = 0
    Capex_a_Boiler_USD = 0
    Capex_a_Boiler_peak_USD = 0
    Capex_a_Lake_USD = 0
    Capex_a_Sewage_USD = 0
    Capex_a_GHP_USD = 0
    Capex_a_PV_USD = 0
    Capex_a_SC_ET_USD = 0
    Capex_a_SC_FP_USD = 0
    Capex_a_PVT_USD = 0
    Capex_a_Boiler_backup_USD = 0
    Capex_a_HEX = 0
    Capex_a_storage_HP = 0
    Capex_a_HP_storage_USD = 0
    Opex_fixed_SC = 0
    Opex_fixed_PVT_USD = 0
    Opex_fixed_HP_PVT_USD = 0
    Opex_fixed_furnace_USD = 0
    Opex_fixed_CHP_USD = 0
    Opex_fixed_Boiler_USD = 0
    Opex_fixed_Boiler_peak_USD = 0
    Opex_fixed_Boiler_backup_USD = 0
    Opex_fixed_Lake_USD = 0
    Opex_fixed_wasteserver_HEX_USD = 0
    Opex_fixed_wasteserver_HP_USD = 0
    Opex_fixed_PV_USD = 0
    Opex_fixed_GHP_USD = 0
    Opex_fixed_storage_USD = 0
    Opex_fixed_Sewage_USD = 0
    Opex_fixed_HP_storage_USD = 0
    StorageInvC = 0
    NetworkCost_a_USD = 0
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
    Capex_furnace_USD = 0
    Capex_CHP_USD = 0
    Capex_Boiler_USD = 0
    Capex_Boiler_peak_USD = 0
    Capex_Lake_USD = 0
    Capex_Sewage_USD = 0
    Capex_GHP = 0
    Capex_PV_USD = 0
    Capex_SC = 0
    Capex_PVT_USD = 0
    Capex_Boiler_backup_USD = 0
    Capex_HEX = 0
    Capex_storage_HP = 0
    Capex_HP_storage = 0
    Capex_SC_ET_USD = 0
    Capex_SC_FP_USD = 0
    Capex_PVT_USD = 0
    Capex_Boiler_backup_USD = 0
    Capex_HP_storage_USD = 0
    Capex_storage_HP = 0
    Capex_CHP_USD = 0
    Capex_furnace_USD = 0
    Capex_Boiler_USD = 0
    Capex_Boiler_peak_USD = 0
    Capex_Lake_USD = 0
    Capex_Sewage_USD = 0
    Capex_pump_USD = 0

    if config.district_heating_network:
        for (index, building_name) in zip(DHN_barcode, buildList):
            if index == "0":
                df = pd.read_csv(locator.get_optimization_decentralized_folder_building_result_heating(building_name))
                dfBest = df[df["Best configuration"] == 1]
                CostDiscBuild += dfBest["Total Costs [CHF]"].iloc[0] # [CHF]
                CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0] # [kg CO2]
                PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0] # [MJ-oil-eq]
                Capex_Disconnected += dfBest["Annualized Investment Costs [CHF]"].iloc[0]
                Opex_Disconnected += dfBest["Operation Costs [CHF]"].iloc[0]
            else:
                nBuildinNtw += 1
    if config.district_cooling_network:
        PV_barcode = ''
        for (index, building_name) in zip(DCN_barcode, buildList):
            if index == "0": # choose the best decentralized configuration
                df = pd.read_csv(locator.get_optimization_decentralized_folder_building_result_cooling(building_name, configuration = 'AHU_ARU_SCU'))
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
                        locator.get_optimization_decentralized_folder_building_result_cooling(building_name, decentralized_configuration))
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
                        locator.get_optimization_decentralized_folder_building_result_cooling(building_name, decentralized_configuration))
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
                        locator.get_optimization_decentralized_folder_building_result_cooling(building_name, decentralized_configuration))
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
                        locator.get_optimization_decentralized_folder_building_result_cooling(building_name, decentralized_configuration))
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
                        locator.get_optimization_decentralized_folder_building_result_cooling(building_name, decentralized_configuration))
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
                        locator.get_optimization_decentralized_folder_building_result_cooling(building_name, decentralized_configuration))
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


    addcosts_Capex_a_USD += CostDiscBuild
    addCO2 += CO2DiscBuild
    addPrim += PrimDiscBuild

    # Solar technologies

    PV_installed_area_m2 = master_to_slave_vars.SOLAR_PART_PV * solar_features.A_PV_m2  # kW
    Capex_a_PV_USD, Opex_fixed_PV_USD, Capex_PV_USD = pv.calc_Cinv_pv(PV_installed_area_m2, locator, config)
    addcosts_Capex_a_USD += Capex_a_PV_USD
    addcosts_Opex_fixed_USD += Opex_fixed_PV_USD
    addcosts_Capex_USD += Capex_PV_USD

    SC_ET_area_m2 = master_to_slave_vars.SOLAR_PART_SC_ET * solar_features.A_SC_ET_m2
    Capex_a_SC_ET_USD, Opex_fixed_SC_ET_USD, Capex_SC_ET_USD = stc.calc_Cinv_SC(SC_ET_area_m2, locator, config, 'ET')
    addcosts_Capex_a_USD += Capex_a_SC_ET_USD
    addcosts_Opex_fixed_USD += Opex_fixed_SC_ET_USD
    addcosts_Capex_USD += Capex_SC_ET_USD

    SC_FP_area_m2 = master_to_slave_vars.SOLAR_PART_SC_FP * solar_features.A_SC_FP_m2
    Capex_a_SC_FP_USD, Opex_fixed_SC_FP_USD, Capex_SC_FP_USD = stc.calc_Cinv_SC(SC_FP_area_m2, locator, config, 'FP')
    addcosts_Capex_a_USD += Capex_a_SC_FP_USD
    addcosts_Opex_fixed_USD += Opex_fixed_SC_FP_USD
    addcosts_Capex_USD += Capex_SC_FP_USD

    PVT_peak_kW = master_to_slave_vars.SOLAR_PART_PVT * solar_features.A_PVT_m2 * N_PVT  # kW
    Capex_a_PVT_USD, Opex_fixed_PVT_USD, Capex_PVT_USD = pvt.calc_Cinv_PVT(PVT_peak_kW, locator, config)
    addcosts_Capex_a_USD += Capex_a_PVT_USD
    addcosts_Opex_fixed_USD += Opex_fixed_PVT_USD
    addcosts_Capex_USD += Capex_PVT_USD

    # Add the features for the distribution

    if DHN_barcode.count("1") > 0 and config.district_heating_network:
        os.chdir(locator.get_optimization_slave_results_folder(master_to_slave_vars.generation_number))
        # Add the investment costs of the energy systems
        # Furnace
        if master_to_slave_vars.Furnace_on == 1:
            P_design_W = master_to_slave_vars.Furnace_Q_max_W

            fNameSlavePP = locator.get_optimization_slave_heating_activation_pattern_heating(master_to_slave_vars.configKey,
                                                                                     master_to_slave_vars.individual_number,
                                                                                     master_to_slave_vars.generation_number)
            dfFurnace = pd.read_csv(fNameSlavePP, usecols=["Q_Furnace_W"])
            arrayFurnace_W = np.array(dfFurnace)

            Q_annual_W = 0
            for i in range(int(np.shape(arrayFurnace_W)[0])):
                Q_annual_W += arrayFurnace_W[i][0]

            Capex_a_furnace_USD, Opex_fixed_furnace_USD, Capex_furnace_USD = furnace.calc_Cinv_furnace(P_design_W, Q_annual_W, config, locator, 'FU1')
            addcosts_Capex_a_USD += Capex_a_furnace_USD
            addcosts_Opex_fixed_USD += Opex_fixed_furnace_USD
            addcosts_Capex_USD += Capex_furnace_USD

        # CC
        if master_to_slave_vars.CC_on == 1:
            CC_size_W = master_to_slave_vars.CC_GT_SIZE_W
            Capex_a_CHP_USD, Opex_fixed_CHP_USD, Capex_CHP_USD = chp.calc_Cinv_CCGT(CC_size_W, locator, config)
            addcosts_Capex_a_USD += Capex_a_CHP_USD
            addcosts_Opex_fixed_USD += Opex_fixed_CHP_USD
            addcosts_Capex_USD += Capex_CHP_USD

        # Boiler Base
        if master_to_slave_vars.Boiler_on == 1:
            Q_design_W = master_to_slave_vars.Boiler_Q_max_W

            fNameSlavePP = locator.get_optimization_slave_heating_activation_pattern(
                master_to_slave_vars.individual_number,
                master_to_slave_vars.generation_number)
            dfBoilerBase = pd.read_csv(fNameSlavePP, usecols=["Q_BaseBoiler_W"])
            arrayBoilerBase_W = np.array(dfBoilerBase)

            Q_annual_W = 0
            for i in range(int(np.shape(arrayBoilerBase_W)[0])):
                Q_annual_W += arrayBoilerBase_W[i][0]

            Capex_a_Boiler_USD, Opex_fixed_Boiler_USD, Capex_Boiler_USD = boiler.calc_Cinv_boiler(Q_design_W, locator, config, 'BO1')
            addcosts_Capex_a_USD += Capex_a_Boiler_USD
            addcosts_Opex_fixed_USD += Opex_fixed_Boiler_USD
            addcosts_Capex_USD += Capex_Boiler_USD

        # Boiler Peak
        if master_to_slave_vars.BoilerPeak_on == 1:
            Q_design_W = master_to_slave_vars.BoilerPeak_Q_max_W

            fNameSlavePP = locator.get_optimization_slave_heating_activation_pattern(
                master_to_slave_vars.individual_number,
                master_to_slave_vars.generation_number)
            dfBoilerPeak = pd.read_csv(fNameSlavePP, usecols=["Q_PeakBoiler_W"])
            arrayBoilerPeak_W = np.array(dfBoilerPeak)

            Q_annual_W = 0
            for i in range(int(np.shape(arrayBoilerPeak_W)[0])):
                Q_annual_W += arrayBoilerPeak_W[i][0]
            Capex_a_Boiler_peak_USD, Opex_fixed_Boiler_peak_USD, Capex_Boiler_peak_USD = boiler.calc_Cinv_boiler(Q_design_W, locator, config, 'BO1')
            addcosts_Capex_a_USD += Capex_a_Boiler_peak_USD
            addcosts_Opex_fixed_USD += Opex_fixed_Boiler_peak_USD
            addcosts_Capex_USD += Capex_Boiler_peak_USD

        # HP Lake
        if master_to_slave_vars.HP_Lake_on == 1:
            HP_Size_W = master_to_slave_vars.HPLake_maxSize_W
            Capex_a_Lake_USD, Opex_fixed_Lake_USD, Capex_Lake_USD = hp.calc_Cinv_HP(HP_Size_W, locator, config, 'HP2')
            addcosts_Capex_a_USD += Capex_a_Lake_USD
            addcosts_Opex_fixed_USD += Opex_fixed_Lake_USD
            addcosts_Capex_USD += Capex_Lake_USD

        # HP Sewage
        if master_to_slave_vars.HP_Sew_on == 1:
            HP_Size_W = master_to_slave_vars.HPSew_maxSize_W
            Capex_a_Sewage_USD, Opex_fixed_Sewage_USD, Capex_Sewage_USD = hp.calc_Cinv_HP(HP_Size_W, locator, config, 'HP2')
            addcosts_Capex_a_USD += Capex_a_Sewage_USD
            addcosts_Opex_fixed_USD += Opex_fixed_Sewage_USD
            addcosts_Capex_USD += Capex_Sewage_USD

        # GHP
        if master_to_slave_vars.GHP_on == 1:
            fNameSlavePP = locator.get_optimization_slave_electricity_activation_pattern_heating(
                master_to_slave_vars.individual_number,
                master_to_slave_vars.generation_number)
            dfGHP = pd.read_csv(fNameSlavePP, usecols=["E_used_GHP_W"])
            arrayGHP_W = np.array(dfGHP)

            GHP_Enom_W = np.amax(arrayGHP_W)
            Capex_a_GHP_USD, Opex_fixed_GHP_USD, Capex_GHP_USD = hp.calc_Cinv_GHP(GHP_Enom_W, locator, config)
            addcosts_Capex_a_USD += Capex_a_GHP_USD * prices.EURO_TO_CHF
            addcosts_Opex_fixed_USD += Opex_fixed_GHP_USD * prices.EURO_TO_CHF
            addcosts_Capex_USD += Capex_GHP_USD

        # Back-up boiler
        Capex_a_Boiler_backup_USD, Opex_fixed_Boiler_backup_USD, Capex_Boiler_backup_USD = boiler.calc_Cinv_boiler(Q_uncovered_design_W, locator, config, 'BO1')
        addcosts_Capex_a_USD += Capex_a_Boiler_backup_USD
        addcosts_Opex_fixed_USD += Opex_fixed_Boiler_backup_USD
        addcosts_Capex_USD += Capex_Boiler_backup_USD
        master_to_slave_vars.BoilerBackup_Q_max_W = Q_uncovered_design_W

        # Hex and HP for Heat recovery
        if master_to_slave_vars.WasteServersHeatRecovery == 1:
            df = pd.read_csv(
                os.path.join(locator.get_optimization_network_results_folder(), master_to_slave_vars.network_data_file_heating),
                usecols=["Qcdata_netw_total_kWh"])
            array = np.array(df)
            Q_HEX_max_kWh = np.amax(array)
            Capex_a_wasteserver_HEX_USD, Opex_fixed_wasteserver_HEX_USD, Capex_wasteserver_HEX_USD = hex.calc_Cinv_HEX(Q_HEX_max_kWh, locator, config, 'HEX1')
            addcosts_Capex_a_USD += (Capex_a_wasteserver_HEX_USD)
            addcosts_Opex_fixed_USD += Opex_fixed_wasteserver_HEX_USD
            addcosts_Capex_USD += Capex_wasteserver_HEX_USD

            df = pd.read_csv(
                locator.get_optimization_slave_storage_operation_data(master_to_slave_vars.individual_number,
                                                                      master_to_slave_vars.generation_number),
                usecols=["HPServerHeatDesignArray_kWh"])
            array = np.array(df)
            Q_HP_max_kWh = np.amax(array)
            Capex_a_wasteserver_HP_USD, Opex_fixed_wasteserver_HP_USD, Capex_wasteserver_HP_USD = hp.calc_Cinv_HP(Q_HP_max_kWh, locator, config, 'HP2')
            addcosts_Capex_a_USD += (Capex_a_wasteserver_HP_USD)
            addcosts_Opex_fixed_USD += Opex_fixed_wasteserver_HP_USD
            addcosts_Capex_USD += Capex_wasteserver_HP_USD

        # Heat pump from solar to DH
        df = pd.read_csv(locator.get_optimization_slave_storage_operation_data(master_to_slave_vars.individual_number,
                                                                               master_to_slave_vars.generation_number),
                         usecols=["HPScDesignArray_Wh", "HPpvt_designArray_Wh"])
        array = np.array(df)
        Q_HP_max_PVT_wh = np.amax(array[:, 1])
        Q_HP_max_SC_Wh = np.amax(array[:, 0])
        Capex_a_HP_PVT_USD, Opex_fixed_HP_PVT_USD, Capex_HP_PVT_USD = hp.calc_Cinv_HP(Q_HP_max_PVT_wh, locator, config, 'HP2')
        Capex_a_storage_HP += (Capex_a_HP_PVT_USD)
        addcosts_Opex_fixed_USD += Opex_fixed_HP_PVT_USD
        addcosts_Capex_USD += Capex_HP_PVT_USD

        Capex_a_HP_SC_USD, Opex_fixed_HP_SC_USD, Capex_HP_SC_USD = hp.calc_Cinv_HP(Q_HP_max_SC_Wh, locator, config, 'HP2')
        Capex_a_storage_HP += (Capex_a_HP_SC_USD)
        addcosts_Opex_fixed_USD += Opex_fixed_HP_SC_USD
        addcosts_Capex_USD += Capex_HP_SC_USD

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

        Capex_a_HP_storage_USD, Opex_fixed_HP_storage_USD, Capex_HP_storage_USD = hp.calc_Cinv_HP(Q_HP_max_storage_W, locator, config, 'HP2')
        addcosts_Capex_a_USD += (Capex_a_HP_storage_USD)
        addcosts_Opex_fixed_USD += Opex_fixed_HP_storage_USD
        addcosts_Capex_USD += Capex_HP_storage_USD

        # Storage
        df = pd.read_csv(locator.get_optimization_slave_storage_operation_data(master_to_slave_vars.individual_number,
                                                                               master_to_slave_vars.generation_number),
                         usecols=["Storage_Size_m3"], nrows=1)
        StorageVol_m3 = np.array(df)[0][0]
        Capex_a_storage_USD, Opex_fixed_storage_USD, Capex_storage_USD = storage.calc_Cinv_storage(StorageVol_m3, locator, config, 'TES2')
        addcosts_Capex_a_USD += Capex_a_storage_USD
        addcosts_Opex_fixed_USD += Opex_fixed_storage_USD
        addcosts_Capex_USD += Capex_storage_USD

        # Costs from distribution configuration
        NetworkCost_USD = network_features.pipesCosts_DHN_USD
        NetworkCost_USD = NetworkCost_USD * nBuildinNtw / len(buildList)
        NetworkCost_a_USD = NetworkCost_USD * PIPEINTERESTRATE * (1+ PIPEINTERESTRATE) ** PIPELIFETIME / ((1+PIPEINTERESTRATE) ** PIPELIFETIME - 1)
        addcosts_Capex_a_USD += NetworkCost_a_USD
        addcosts_Capex_USD += NetworkCost_USD

        # HEX (1 per building in ntw)
        for (index, building_name) in zip(DHN_barcode, buildList):
            if index == "1":
                df = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                 usecols=["Q_dhw_W", "Q_heating_W"])
                subsArray = np.array(df)

                Q_max_W = np.amax(subsArray[:, 0] + subsArray[:, 1])
                Capex_a_HEX_building_USD, Opex_fixed_HEX_building_USD, Capex_HEX_building_USD = hex.calc_Cinv_HEX(Q_max_W, locator, config, 'HEX1')
                addcosts_Capex_a_USD += Capex_a_HEX_building_USD
                addcosts_Opex_fixed_USD += Opex_fixed_HEX_building_USD
                addcosts_Capex_USD += Capex_HEX_building_USD

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
                
                Q_max_SC_ET_Wh = solar_features.Q_nom_SC_ET_Wh * master_to_slave_vars.SOLAR_PART_SC_ET * share
                Capex_a_HEX_SC_ET_USD, Opex_fixed_HEX_SC_ET_USD, Capex_HEX_SC_ET_USD = hex.calc_Cinv_HEX(Q_max_SC_ET_Wh, locator, config, 'HEX1')
                addcosts_Capex_a_USD += Capex_a_HEX_SC_ET_USD
                addcosts_Opex_fixed_USD += Opex_fixed_HEX_SC_ET_USD
                addcosts_Capex_USD += Capex_HEX_SC_ET_USD

                Q_max_SC_FP_Wh = solar_features.Q_nom_SC_FP_Wh * master_to_slave_vars.SOLAR_PART_SC_FP * share
                Capex_a_HEX_SC_FP_USD, Opex_fixed_HEX_SC_FP_USD, Capex_HEX_SC_FP_USD = hex.calc_Cinv_HEX(Q_max_SC_FP_Wh, locator, config, 'HEX1')
                addcosts_Capex_a_USD += Capex_a_HEX_SC_FP_USD
                addcosts_Opex_fixed_USD += Opex_fixed_HEX_SC_FP_USD
                addcosts_Capex_USD += Capex_HEX_SC_FP_USD

                Q_max_PVT_Wh = solar_features.Q_nom_PVT_Wh * master_to_slave_vars.SOLAR_PART_PVT * share
                Capex_a_HEX_PVT_USD, Opex_fixed_HEX_PVT_USD, Capex_HEX_PVT_USD = hex.calc_Cinv_HEX(Q_max_PVT_Wh, locator, config, 'HEX1')
                addcosts_Capex_a_USD += Capex_a_HEX_PVT_USD
                addcosts_Opex_fixed_USD += Opex_fixed_HEX_PVT_USD
                addcosts_Capex_USD += Capex_HEX_PVT_USD

    # Pump operation costs
    Capex_a_pump_USD, Opex_fixed_pump_USD, Opex_var_pump_USD, Capex_pump_USD = pumps.calc_Ctot_pump(master_to_slave_vars, network_features, locator, lca, config)
    addcosts_Capex_a_USD += Capex_a_pump_USD
    addcosts_Opex_fixed_USD += Opex_fixed_pump_USD
    addcosts_Capex_USD += Capex_pump_USD

    # import gas consumption data from:
    if DHN_barcode.count("1") > 0 and config.district_heating_network:
        # import gas consumption data from:
        EgasPrimaryDataframe_W = pd.read_csv(
            locator.get_optimization_slave_natural_gas_imports(master_to_slave_vars.individual_number,
                                                                          master_to_slave_vars.generation_number))
        E_gas_primary_peak_power_W = np.amax(EgasPrimaryDataframe_W['NG_total_W'])
        GasConnectionInvCost = ngas.calc_Cinv_gas(E_gas_primary_peak_power_W, gv)
    elif DCN_barcode.count("1") > 0 and config.district_cooling_network:
        EgasPrimaryDataframe_W = pd.read_csv(
            locator.get_optimization_slave_natural_gas_imports(master_to_slave_vars.individual_number,
                                                                          master_to_slave_vars.generation_number))
        E_gas_primary_peak_power_W = np.amax(EgasPrimaryDataframe_W['NG_total_W'])
        GasConnectionInvCost = ngas.calc_Cinv_gas(E_gas_primary_peak_power_W, gv)
    else:
        GasConnectionInvCost = 0.0

    addcosts_Capex_a_USD += GasConnectionInvCost
    # Save data
    results = pd.DataFrame({
        "Capex_a_SC_ET_USD": [Capex_a_SC_ET_USD],
        "Capex_a_SC_FP_USD":[Capex_a_SC_FP_USD],
        "Opex_fixed_SC": [Opex_fixed_SC],
        "Capex_a_PVT": [Capex_a_PVT_USD],
        "Opex_fixed_PVT": [Opex_fixed_PVT_USD],
        "Capex_a_PV": [Capex_a_PV_USD],
        "Opex_fixed_PV": [Opex_fixed_PV_USD],
        "Capex_a_Boiler_backup": [Capex_a_Boiler_backup_USD],
        "Opex_fixed_Boiler_backup": [Opex_fixed_Boiler_backup_USD],
        "Capex_a_storage_HEX": [Capex_a_HP_storage_USD],
        "Opex_fixed_storage_HEX": [Opex_fixed_HP_storage_USD],
        "Capex_a_storage_HP": [Capex_a_storage_HP],
        "Capex_a_CHP": [Capex_a_CHP_USD],
        "Opex_fixed_CHP": [Opex_fixed_CHP_USD],
        "StorageInvC": [StorageInvC],
        "StorageCostSum": [StorageInvC + Capex_a_storage_HP + Capex_a_HEX],
        "NetworkCost": [NetworkCost_a_USD],
        "SubstHEXCost": [SubstHEXCost_capex],
        "DHNInvestCost": [addcosts_Capex_a_USD - CostDiscBuild],
        "PVTHEXCost_Capex": [PVTHEXCost_Capex],
        "CostDiscBuild": [CostDiscBuild],
        "CO2DiscBuild": [CO2DiscBuild],
        "PrimDiscBuild": [PrimDiscBuild],
        "Capex_a_furnace": [Capex_a_furnace_USD],
        "Opex_fixed_furnace": [Opex_fixed_furnace_USD],
        "Capex_a_Boiler": [Capex_a_Boiler_USD],
        "Opex_fixed_Boiler": [Opex_fixed_Boiler_USD],
        "Capex_a_Boiler_peak": [Capex_a_Boiler_peak_USD],
        "Opex_fixed_Boiler_peak": [Opex_fixed_Boiler_peak_USD],
        "Capex_Disconnected": [Capex_Disconnected],
        "Opex_Disconnected": [Opex_Disconnected],
        "Capex_a_Lake": [Capex_a_Lake_USD],
        "Opex_fixed_Lake":[Opex_fixed_Lake_USD],
        "Capex_a_Sewage": [Capex_a_Sewage_USD],
        "Opex_fixed_Sewage": [Opex_fixed_Sewage_USD],
        "SCHEXCost_Capex": [SCHEXCost_Capex],
        "Capex_a_pump": [Capex_a_pump_USD],
        "Opex_fixed_pump": [Opex_fixed_pump_USD],
        "Opex_var_pump": [Opex_var_pump_USD],
        "Sum_CAPEX": [addcosts_Capex_a_USD],
        "Sum_OPEX_fixed": [addcosts_Opex_fixed_USD],
        "GasConnectionInvCa": [GasConnectionInvCost],
        "CO2_PV_disconnected": [CO2_PV_disconnected],
        "cost_PV_disconnected": [cost_PV_disconnected],
        "Eprim_PV_disconnected": [Eprim_PV_disconnected],
        "Capex_SC_ET_USD": [Capex_SC_ET_USD],
        "Capex_SC_FP_USD": [Capex_SC_FP_USD],
        "Capex_PVT": [Capex_PVT_USD],
        "Capex_PV": [Capex_PV_USD],
        "Capex_Boiler_backup": [Capex_Boiler_backup_USD],
        "Capex_storage_HEX": [Capex_HP_storage_USD],
        "Capex_storage_HP": [Capex_storage_HP],
        "Capex_CHP": [Capex_CHP_USD],
        "Capex_furnace": [Capex_furnace_USD],
        "Capex_Boiler_base": [Capex_Boiler_USD],
        "Capex_Boiler_peak": [Capex_Boiler_peak_USD],
        "Capex_Lake": [Capex_Lake_USD],
        "Capex_Sewage": [Capex_Sewage_USD],
        "Capex_pump": [Capex_pump_USD],

    })
    results.to_csv(locator.get_optimization_slave_investment_cost_detailed(master_to_slave_vars.individual_number,
                                                                           master_to_slave_vars.generation_number),
                   sep=',')
    return (addcosts_Capex_a_USD + addcosts_Opex_fixed_USD, addCO2, addPrim)
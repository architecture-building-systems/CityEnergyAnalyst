# -*- coding: utf-8 -*-
"""
============================
Extra costs to an individual
============================

"""
from __future__ import division

import os

import numpy as np
import pandas as pd

import cea.resources.natural_gas as ngas
import cea.technologies.photovoltaic as pv
import cea.technologies.heatpumps as hp
import cea.technologies.furnace as furnace
import cea.technologies.cogeneration as chp
import cea.technologies.solar_collector as stc
import cea.technologies.boilers as boiler
import cea.technologies.photovoltaic_thermal as pvt
import cea.technologies.heat_exchangers as hex
import cea.technologies.thermal_storage as storage
import cea.technologies.thermal_network as network
import cea.technologies.pumps as pumps

def addCosts(indCombi, buildList, locator, dicoSupply, QUncoveredDesign, QUncoveredAnnual, solarFeat, ntwFeat, gv):
    """
    Computes additional costs / GHG emisions / primary energy needs
    for the individual
    
    Parameters
    ----------
    indCombi : string
        with 0 if disconnected building, 1 if connected
    buildList : list
        list of buildings in the district
    locator : string
        path to folders
    dicoSupply : class context
        with the features of the specific individual
    QuncoveredDesign : float
        hourly max of the heating uncovered demand
    QuncoveredAnnual : float
        total heating uncovered
    solarFeat / ntwFeat : class solarFeatures / ntwFeatures
    
    Returns
    -------
    (addCosts, addCO2, addPrim) : tuple
    
    """
    addCosts = 0
    addCO2 = 0
    addPrim = 0
    nBuildinNtw = 0
    
    # Add the features from the disconnected buildings
    print "\n COSTS FROM DISCONNECTED BUILDINGS"
    os.chdir(locator.pathDiscRes)
    CostDiscBuild = 0
    CO2DiscBuild = 0
    PrimDiscBuild = 0
    FurnaceInvCost = 0
    CCInvCost = 0
    BoilerBInvCost = 0
    BoilerPInvCost = 0 
    HPLakeInvC = 0
    HPSewInvC = 0
    GHPInvC = 0
    PVInvC = 0
    SCInvC = 0
    PVTInvC = 0
    BoilerAddInvC = 0
    StorageHEXCost = 0
    StorageHPCost = 0
    StorageInvC = 0
    NetworkCost = 0
    SubstHEXCost = 0
    PVTHEXCost = 0
    SCHEXCost = 0
    pumpCosts = 0
    GasConnectionInvCost = 0 
    
    for (index, buildName) in zip(indCombi, buildList):
        if index == "0":
            discFileName = "DiscOp_" + buildName + "_result.csv"
            df = pd.read_csv(discFileName)
            dfBest = df[df["Best configuration"] == 1]
            CostDiscBuild += dfBest["Total Costs [CHF]"].iloc[0] # [CHF]
            CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0] # [kg CO2]
            PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0] # [MJ-oil-eq]

            print  dfBest["Total Costs [CHF]"].iloc[0], buildName, "disconnected"

        else:
            nBuildinNtw += 1
    
    addCosts += CostDiscBuild
    addCO2 += CO2DiscBuild
    addPrim += PrimDiscBuild
    
    # Add the features for the network

    if indCombi.count("1") > 0:
        os.chdir(locator.pathSlaveRes)
        
        print " \n MACHINERY COSTS"
        # Add the investment costs of the energy systems
        # Furnace
        if dicoSupply.Furnace_on == 1:
            P_design = dicoSupply.Furnace_Q_max
            
            fNameSlavePP = dicoSupply.configKey + "PPActivationPattern.csv"
            dfFurnace = pd.read_csv(fNameSlavePP, usecols=["Q_Furnace"])
            arrayFurnace = np.array(dfFurnace)
            
            Q_annual =  0
            for i in range(int(np.shape(arrayFurnace)[0])):
                Q_annual += arrayFurnace[i][0]
            
            FurnaceInvCost = furnace.calc_Cinv_furnace(P_design, Q_annual, gv)
            addCosts += FurnaceInvCost
            
            print furnace.calc_Cinv_furnace(P_design, Q_annual, gv), " Furnace"
        
        # CC
        if dicoSupply.CC_on == 1:
            CC_size = dicoSupply.CC_GT_SIZE 
            CCInvCost = chp.calc_Cinv_CCT(CC_size, gv)
            addCosts += CCInvCost
            print chp.calc_Cinv_CCT(CC_size, gv), " CC"
    
        # Boiler Base
        if dicoSupply.Boiler_on == 1:
            Q_design = dicoSupply.Boiler_Q_max
            
            fNameSlavePP = dicoSupply.configKey + "PPActivationPattern.csv"
            dfBoilerBase = pd.read_csv(fNameSlavePP, usecols=["Q_BoilerBase"])
            arrayBoilerBase = np.array(dfBoilerBase)
            
            Q_annual =  0
            for i in range(int(np.shape(arrayBoilerBase)[0])):
                Q_annual += arrayBoilerBase[i][0]
                
            BoilerBInvCost = boiler.calc_Cinv_boiler(Q_design, Q_annual, gv)
            addCosts += BoilerBInvCost
            print boiler.calc_Cinv_boiler(Q_design, Q_annual, gv), " Boiler Base "
        
        # Boiler Peak
        if dicoSupply.BoilerPeak_on == 1:
            Q_design = dicoSupply.BoilerPeak_Q_max
    
            fNameSlavePP = dicoSupply.configKey + "PPActivationPattern.csv"
            dfBoilerPeak = pd.read_csv(fNameSlavePP, usecols=["Q_BoilerPeak"])
            arrayBoilerPeak = np.array(dfBoilerPeak)
            
            Q_annual =  0
            for i in range(int(np.shape(arrayBoilerPeak)[0])):
                Q_annual += arrayBoilerPeak[i][0]
            BoilerPInvCost = boiler.calc_Cinv_boiler(Q_design, Q_annual, gv)
            addCosts += BoilerPInvCost
            print boiler.calc_Cinv_boiler(Q_design, Q_annual, gv), " Boiler Peak"

        
        # HP Lake
        if dicoSupply.HP_Lake_on == 1:
            HP_Size = dicoSupply.HPLake_maxSize
            HPLakeInvC = hp.calc_Cinv_HP(HP_Size, gv)
            addCosts += HPLakeInvC
            print hp.calc_Cinv_HP(HP_Size, gv), " HP Lake"
            
        # HP Sewage
        if dicoSupply.HP_Sew_on == 1:
            HP_Size = dicoSupply.HPSew_maxSize
            HPSewInvC = hp.calc_Cinv_HP(HP_Size, gv)
            addCosts += HPSewInvC
            print hp.calc_Cinv_HP(HP_Size, gv), "HP Sewage"
            
        # GHP
        if dicoSupply.GHP_on == 1:
            fNameSlavePP = dicoSupply.configKey + "PPActivationPattern.csv"
            dfGHP = pd.read_csv(fNameSlavePP, usecols=["E_GHP"])
            arrayGHP = np.array(dfGHP)
            
            GHP_Enom = np.amax(arrayGHP)
            GHPInvC = hp.calc_Cinv_GHP(GHP_Enom, gv) * gv.EURO_TO_CHF
            addCosts += GHPInvC
            print hp.calc_Cinv_GHP(GHP_Enom, gv) * gv.EURO_TO_CHF, " GHP"
            
        # Solar technologies

        PV_peak = dicoSupply.SOLAR_PART_PV * solarFeat.SolarAreaPV * gv.nPV #kW
        PVInvC = pv.calc_Cinv_PV(PV_peak)
        addCosts += PVInvC
        print pv.calc_Cinv_PV(PV_peak), "PV peak"
        
        SC_area = dicoSupply.SOLAR_PART_SC * solarFeat.SolarAreaSC
        SCInvC = stc.calc_Cinv_SC(SC_area)
        addCosts += SCInvC
        print stc.calc_Cinv_SC(SC_area), "SC area"
        

        PVT_peak = dicoSupply.SOLAR_PART_PVT * solarFeat.SolarAreaPVT * gv.nPVT #kW
        PVTInvC = pvt.calc_Cinv_PVT(PVT_peak)
        addCosts += PVTInvC
        print pvt.calc_Cinv_PVT(PVT_peak), "PVT peak"
        
        # Back-up boiler
        BoilerAddInvC = boiler.calc_Cinv_boiler(QUncoveredDesign, QUncoveredAnnual, gv)
        addCosts += BoilerAddInvC
        print boiler.calc_Cinv_boiler(QUncoveredDesign, QUncoveredAnnual, gv), "backup boiler"
        
    
        # Hex and HP for Heat recovery
        print "\n STORAGE PART COSTS"
        if dicoSupply.WasteServersHeatRecovery == 1:
            df = pd.read_csv(locator.pathNtwRes + "/" + dicoSupply.NETWORK_DATA_FILE, usecols = ["Qcdata_netw_total"])
            array = np.array(df)
            QhexMax = np.amax(array)
            StorageHEXCost += hex.calc_Cinv_HEX(QhexMax, gv)
            
            print hex.calc_Cinv_HEX(QhexMax, gv), "Hex for data center"
            
            df = pd.read_csv(locator.pathSlaveRes + "/" + dicoSupply.configKey + "StorageOperationData.csv", usecols = ["HPServerHeatDesignArray"])
            array = np.array(df)
            QhpMax = np.amax(array)
            StorageHEXCost += hp.calc_Cinv_HP(QhpMax, gv)
            print hp.calc_Cinv_HP(QhpMax, gv), "HP for data center"
            
        if dicoSupply.WasteCompressorHeatRecovery == 1:
            df = pd.read_csv(locator.pathNtwRes + "/" + dicoSupply.NETWORK_DATA_FILE, usecols = ["Ecaf_netw_total"])
            array = np.array(df)
            QhexMax = np.amax(array)
        
            StorageHEXCost += hex.calc_Cinv_HEX(QhexMax, gv)
            print hex.calc_Cinv_HEX(QhexMax, gv), "Hex for compressed air"
            
            df = pd.read_csv(locator.pathSlaveRes + "/" + dicoSupply.configKey + "StorageOperationData.csv", usecols = ["HPCompAirDesignArray"])
            array = np.array(df)
            QhpMax = np.amax(array)

            StorageHEXCost += hp.calc_Cinv_HP(QhpMax, gv)
            print hp.calc_Cinv_HP(QhpMax, gv), "HP for compressed air"
        addCosts += StorageHEXCost
        
        # Heat pump solar to storage
        df = pd.read_csv(locator.pathSlaveRes + "/" + dicoSupply.configKey + "StorageOperationData.csv", usecols = ["HPScDesignArray", "HPpvt_designArray"])
        array = np.array(df)
        QhpMax_PVT = np.amax(array[:,1])
        QhpMax_SC = np.amax(array[:,0])
        
        StorageHPCost += hp.calc_Cinv_HP(QhpMax_PVT, gv)
        print hp.calc_Cinv_HP(QhpMax_PVT, gv), "HP for PVT"

        StorageHPCost += hp.calc_Cinv_HP(QhpMax_SC, gv)
        print hp.calc_Cinv_HP(QhpMax_SC, gv), "HP for SC"
        
        # HP for storage operation
        df = pd.read_csv(locator.pathSlaveRes + "/" + dicoSupply.configKey + "StorageOperationData.csv", usecols = ["E_aux_ch", "E_aux_dech", "Q_from_storage_used", "Q_to_storage"])
        array = np.array(df)
        QmaxHPStorage = 0
        for i in range(gv.DAYS_IN_YEAR * gv.HOURS_IN_DAY):
            if array[i][0] > 0:
                QmaxHPStorage = max(QmaxHPStorage, array[i][3] + array[i][0])
            elif array[i][1] > 0:
                QmaxHPStorage = max(QmaxHPStorage, array[i][2] + array[i][1])
        
        StorageHPCost += hp.calc_Cinv_HP(QmaxHPStorage, gv)
        addCosts += StorageHPCost

        print hp.calc_Cinv_HP(QmaxHPStorage, gv), "HP for storage"
        
        
        # Storage
        df = pd.read_csv(locator.pathSlaveRes + "/" + dicoSupply.configKey + "StorageOperationData.csv", usecols = ["Storage_Size"], nrows = 1)
        StorageVol = np.array(df)[0][0]
        StorageInvC += storage.calc_Cinv_storage(StorageVol, gv)
        addCosts += StorageInvC
        print storage.calc_Cinv_storage(StorageVol, gv), "Storage Costs"
        
        
        # Costs from network configuration
        print "\n COSTS FROM NETWORK CONFIGURATION"
        if gv.ZernezFlag == 1:
            NetworkCost += network.calc_Cinv_network_linear(gv.NetworkLengthZernez, gv) * nBuildinNtw / len(buildList)
        else:
            NetworkCost += ntwFeat.pipesCosts_DHN * nBuildinNtw / len(buildList)
        addCosts += NetworkCost
        print ntwFeat.pipesCosts_DHN * nBuildinNtw / len(buildList), "Pipes Costs"
    
        # HEX (1 per building in ntw)
        for (index, buildName) in zip(indCombi, buildList):
            if index == "1":
                
                subsFileName = buildName + "_result.csv"
                df = pd.read_csv(locator.pathSubsRes + "/" + subsFileName, usecols = ["Q_dhw", "Q_heating"])
                subsArray = np.array(df)
                
                Qmax = np.amax( subsArray[:,0] + subsArray[:,1] )
                SubstHEXCost += hex.calc_Cinv_HEX(Qmax, gv)
                print hex.calc_Cinv_HEX(Qmax, gv), "Hex", buildName
        addCosts += SubstHEXCost

        # HEX for solar
        roof_area = np.array(pd.read_csv(locator.get_total_demand(), usecols=["Aroof_m2"]))

        areaAvail = 0
        for i in range( len(indCombi) ):
            index = indCombi[i]
            if index == "1":
                areaAvail += roof_area[i][0]
                
        for i in range( len(indCombi) ):
            index = indCombi[i]
            if index == "1":
                share = roof_area[i][0] / areaAvail
                #print share, "solar area share", buildList[i]
                
                SC_Qmax = solarFeat.SC_Qnom * dicoSupply.SOLAR_PART_SC * share
                SCHEXCost += hex.calc_Cinv_HEX(SC_Qmax, gv)
                print hex.calc_Cinv_HEX(SC_Qmax, gv), "Hex SC", buildList[i]
                
                PVT_Qmax = solarFeat.PVT_Qnom * dicoSupply.SOLAR_PART_PVT * share
                PVTHEXCost += hex.calc_Cinv_HEX(PVT_Qmax, gv)
                print hex.calc_Cinv_HEX(PVT_Qmax, gv), "Hex PVT", buildList[i]
        addCosts += SCHEXCost
        addCosts += PVTHEXCost
        
        print addCosts,"addCosts in extraCostsMain"
        # Pump operation costs
        pumpCosts = pumps.calc_Ctot_pump(dicoSupply, buildList, locator.pathNtwRes, ntwFeat, gv)
        addCosts += pumpCosts
        print pumpCosts, "Pump Operation costs in extraCostsMain\n"
    
    # import gas consumption data from:

    if indCombi.count("1") > 0:
        # import gas consumption data from:
        
        FileName = locator.pathSlaveRes + "/" + dicoSupply.configKey + "PrimaryEnergyBySource.csv"
        colName = "EgasPrimaryPeakPower"
        EgasPrimaryDataframe = pd.read_csv(FileName, usecols=[colName])
        #print EgasPrimaryDataframe
        #print np.array(EgasPrimaryDataframe)
        
        #print float(np.array(EgasPrimaryDataframe))
        
        EgasPrimaryPeakPower = float(np.array(EgasPrimaryDataframe))
        GasConnectionInvCost = ngas.calc_Cinv_gas(EgasPrimaryPeakPower, gv)
    else:
        GasConnectionInvCost = 0.0
        
    addCosts += GasConnectionInvCost
    # Save data
    results = pd.DataFrame({
                            "SCInvC":[SCInvC],
                            "PVTInvC":[PVTInvC],
                            "BoilerAddInvC":[BoilerAddInvC],
                            "StorageHEXCost":[StorageHEXCost],
                            "StorageHPCost":[StorageHPCost],
                            "StorageInvC":[StorageInvC],
                            "StorageCostSum":[StorageInvC+StorageHPCost+StorageHEXCost],
                            "NetworkCost":[NetworkCost],
                            "SubstHEXCost":[SubstHEXCost],
                            "DHNInvestCost":[addCosts - CostDiscBuild],
                            "PVTHEXCost":[PVTHEXCost],
                            "CostDiscBuild":[CostDiscBuild],
                            "CO2DiscBuild":[CO2DiscBuild],
                            "PrimDiscBuild":[PrimDiscBuild],
                            "FurnaceInvCost":[FurnaceInvCost],
                            "BoilerBInvCost":[BoilerBInvCost],
                            "BoilerPInvCost":[BoilerPInvCost],
                            "HPLakeInvC":[HPLakeInvC],
                            "HPSewInvC":[HPSewInvC],
                            "SCHEXCost":[SCHEXCost],
                            "pumpCosts":[pumpCosts],
                            "SumInvestCost":[addCosts],
                            "GasConnectionInvCa":[GasConnectionInvCost]
                            })
    Name = "/" + dicoSupply.configKey + "_InvestmentCostDetailed.csv"
    results.to_csv(locator.pathSlaveRes + Name, sep=',')
     
      
    return (addCosts, addCO2, addPrim)

"""
====================================
Evaluation function of an individual
====================================

"""
from __future__ import division

import contributions.Legacy.MOO.optimization.slave.slave_main as sM
import numpy as np
import pandas as pd

import constrCheck as cCheck
import contributions.Legacy.MOO.optimization.master.cost_model as eM
import contributions.Legacy.MOO.optimization.master.summarize_network_main as nM
import contributions.Legacy.MOO.optimization.preprocessing.cooling_network as coolMain
import contributions.Legacy.MOO.optimization.supportFn as sFn
import contributions.Legacy.MOO.technologies.substation as sMain
from contributions.Legacy.MOO.optimization.master import master_to_slave as MSVar

def readInd(individual, Qmax, pathRaw, gV):
    """
    Reads the list encoding a configuration and implementes the corresponding
    for the slave routine's to use
    
    Parameters
    ----------
    individual : list
        configuration from the Master routine
    Qmax : float
        peak heating demand
    pathRaw : string
        path to raw files
    
    Returns
    -------
    dicoSupply : class MasterSlaveVariables
    
    """
    dicoSupply = MSVar.MasterSlaveVariables()
    dicoSupply.configKey = "".join(str(e)[0:4] for e in individual)
    
    indCombi = sFn.readCombi(individual, gV)
    dicoSupply.nBuildingsConnected = indCombi.count("1") # counting the number of buildings connected
    
    Qnom = Qmax * (1+gV.Qmargin_ntw)
    
    # Heating systems
    
    #CHP units with NG & furnace with biomass wet
    if individual[0] == 1 or individual[0] == 3:
        if gV.Furnace_allowed == 1:
            dicoSupply.Furnace_on = 1
            dicoSupply.Furnace_Q_max = max(individual[1] * Qnom, gV.QminShare * Qnom)
            print dicoSupply.Furnace_Q_max, "Furnace wet"
            dicoSupply.Furn_Moist_type = "wet"
        elif gV.CC_allowed == 1:
            dicoSupply.CC_on = 1
            dicoSupply.CC_GT_SIZE = max(individual[1] * Qnom * 1.3, gV.QminShare * Qnom * 1.3)
            #1.3 is the conversion factor between the GT_Elec_size NG and Q_DHN
            print dicoSupply.CC_GT_SIZE, "CC NG"
            dicoSupply.gt_fuel = "NG"
     
    #CHP units with BG& furnace with biomass dry       
    if individual[0] == 2 or individual[0] == 4:
        if gV.Furnace_allowed == 1:
            dicoSupply.Furnace_on = 1
            dicoSupply.Furnace_Q_max = max(individual[1] * Qnom, gV.QminShare * Qnom)
            print dicoSupply.Furnace_Q_max, "Furnace dry"
            dicoSupply.Furn_Moist_type = "dry"
        elif gV.CC_allowed == 1:
            dicoSupply.CC_on = 1
            dicoSupply.CC_GT_SIZE = max(individual[1] * Qnom * 1.5, gV.QminShare * Qnom * 1.5)
            #1.5 is the conversion factor between the GT_Elec_size BG and Q_DHN
            print dicoSupply.CC_GT_SIZE, "CC BG"
            dicoSupply.gt_fuel = "BG"

    # Base boiler NG 
    if individual[2] == 1:
        dicoSupply.Boiler_on = 1
        dicoSupply.Boiler_Q_max = max(individual[3] * Qnom, gV.QminShare * Qnom)
        print dicoSupply.Boiler_Q_max, "Boiler base NG"
        dicoSupply.BoilerType = "NG"
    
    # Base boiler BG    
    if individual[2] == 2:
        dicoSupply.Boiler_on = 1
        dicoSupply.Boiler_Q_max = max(individual[3] * Qnom, gV.QminShare * Qnom)
        print dicoSupply.Boiler_Q_max, "Boiler base BG"
        dicoSupply.BoilerType = "BG"
    
    # peak boiler NG         
    if individual[4] == 1:
        dicoSupply.BoilerPeak_on = 1
        dicoSupply.BoilerPeak_Q_max = max(individual[5] * Qnom, gV.QminShare * Qnom)
        print dicoSupply.BoilerPeak_Q_max, "Boiler peak NG"
        dicoSupply.BoilerPeakType = "NG"
    
    # peak boiler BG   
    if individual[4] == 2:
        dicoSupply.BoilerPeak_on = 1
        dicoSupply.BoilerPeak_Q_max = max(individual[5] * Qnom, gV.QminShare * Qnom)
        print dicoSupply.BoilerPeak_Q_max, "Boiler peak BG"
        dicoSupply.BoilerPeakType = "BG"
    
    # lake - heat pump
    if individual[6] == 1  and gV.HPLake_allowed == 1:
        dicoSupply.HP_Lake_on = 1
        dicoSupply.HPLake_maxSize = max(individual[7] * Qnom, gV.QminShare * Qnom)
        print dicoSupply.HPLake_maxSize, "Lake"
    
    # sewage - heatpump    
    if individual[8] == 1 and gV.HPSew_allowed == 1:
        dicoSupply.HP_Sew_on = 1
        dicoSupply.HPSew_maxSize = max(individual[9] * Qnom, gV.QminShare * Qnom)
        print dicoSupply.HPSew_maxSize, "Sewage"
    
    # Gwound source- heatpump
    if individual[10] == 1 and gV.GHP_allowed == 1:
        dicoSupply.GHP_on = 1
        GHP_Qmax = max(individual[11] * Qnom, gV.QminShare * Qnom)
        dicoSupply.GHP_number = GHP_Qmax / gV.GHP_HmaxSize
        print GHP_Qmax, "GHP"
    
    # heat recovery servers and compresor
    irank = gV.nHeat * 2
    dicoSupply.WasteServersHeatRecovery = individual[irank]
    dicoSupply.WasteCompressorHeatRecovery = individual[irank + 1]
    
    # Solar systems
    
    area = np.array( pd.read_csv(pathRaw + "/Total.csv", usecols=["Af"]) )
    floors = np.array( pd.read_csv(pathRaw + "/Total.csv", usecols=["Floors"]) )
    
    areaAvail = 0
    totalArea = 0
    for i in range( len(indCombi) ):
        index = indCombi[i]
        if index == "1":
            areaAvail += area[i][0] / (0.9 * floors[i][0])
        totalArea += area[i][0] / (0.9 * floors[i][0])
    
    shareAvail = areaAvail / totalArea    
    
    irank = gV.nHeat * 2 + gV.nHR
    dicoSupply.SOLAR_PART_PV = max(individual[irank] * individual[irank + 1] * individual[irank + 6] * shareAvail,0)
    print dicoSupply.SOLAR_PART_PV, "PV"
    dicoSupply.SOLAR_PART_PVT = max(individual[irank + 2] * individual[irank + 3] * individual[irank + 6] * shareAvail,0)
    print dicoSupply.SOLAR_PART_PVT, "PVT"
    dicoSupply.SOLAR_PART_SC = max(individual[irank + 4] * individual[irank + 5] * individual[irank + 6] * shareAvail,0)
    print dicoSupply.SOLAR_PART_SC, "SC"
    
    return dicoSupply


def checkNtw(individual, ntwList, pathX, gV):
    """
    Calls the network routine if necessary
    
    Parameters
    ----------
    individual : list
        configuration considered
    ntwList : list
        list of DHN configuration previously encountered in the EA
    pathX : string
        path to folders
    
    """
    indCombi = sFn.readCombi(individual, gV)
    print(indCombi)
    
    if not (indCombi in ntwList) and indCombi.count("1") > 0:
        ntwList.append(indCombi)
        
        if indCombi.count("1") == 1:
            fName_TotaltoNtw = "Total_" + indCombi + ".csv"
            print "Direct launch of network summary routine for", indCombi
            nM.Network_Summary(pathX.pathRaw, pathX.pathSubsRes, pathX.pathNtwRes, fName_TotaltoNtw, gV)
 
        else:
            fName_TotaltoNtw = sFn.createTotalNtwCsv(indCombi, pathX.pathRaw, pathX.pathTotalNtw)
            
            # Run the substation and network routines
            print "Re-run the substation routine for new network configuration", indCombi
            sMain.subsMain(pathX.pathRaw, pathX.pathTotalNtw, pathX.pathTotalNtw, fName_TotaltoNtw, 0, gV)
            
            print "Launch network summary routine"
            nM.Network_Summary(pathX.pathRaw,pathX.pathTotalNtw, pathX.pathTotalNtw, pathX.pathNtwRes, pathX.pathNtwLayout, fName_TotaltoNtw, gV)
        
        
def evalInd(individual, buildList, pathX, extraCosts, extraCO2, extraPrim, solarFeat, ntwFeat, gV):
    """
    Evaluates an individual
    
    Parameters
    ----------
    individual : list
    buildList : list of buildings in the district
    pahthX : string
    extraX : float
        parameters previously computed
    solarFeat / ntwFeat : class solarFeatures / ntwFeatures
    
    Returns
    -------
    (costs, CO2, Prim) : tuple of floats
    
    """
    print "Evaluate an individual"
    print individual, "\n"
    
    print "Check the individual"
    nBuildings = len(buildList)
    cCheck.controlCheck(individual, nBuildings, gV)
    
    indCombi = sFn.readCombi(individual, gV)
    costs = extraCosts
    CO2 = extraCO2
    prim = extraPrim
    QUncoveredDesign = 0
    QUncoveredAnnual = 0
    
    if indCombi.count("0") == 0:
        fNameNtw = "Network_summary_result_all.csv"
    else:
        fNameNtw = "Network_summary_result_" + indCombi + ".csv"
    
    if indCombi.count("1") > 0:    
        Qheatmax = sFn.calcQmax(fNameNtw, pathX.pathNtwRes, gV)
    else:
        Qheatmax = 0
    
    print Qheatmax, "Qheatmax in network"
    Qnom = Qheatmax * (1+gV.Qmargin_ntw)
    
    # Modify the individual with the extra GHP constraint
    try:
        cCheck.GHPCheck(individual, pathX.pathRaw, Qnom, gV)
        print "GHP constraint checked \n"
    except:
        print "No GHP constraint check possible \n"

    
    # Export to context
    dicoSupply = readInd(individual, Qheatmax, pathX.pathRaw, gV)
    dicoSupply.NETWORK_DATA_FILE = fNameNtw
    
    
    if dicoSupply.nBuildingsConnected > 1:
        if indCombi.count("0") == 0:
            dicoSupply.fNameTotalCSV = pathX.pathRaw + "/Total.csv"
        else:
            dicoSupply.fNameTotalCSV = pathX.pathTotalNtw + "/Total_" + indCombi + ".csv"
    else:
        dicoSupply.fNameTotalCSV = pathX.pathSubsRes + "/Total_" + indCombi + ".csv"
    
    if indCombi.count("1") > 0:
        #print "Dummy evaluation of", dicoSupply.configKey
        #(slavePrim, slaveCO2, slaveCosts, QUncoveredDesign, QUncoveredAnnual) = sFn.dummyevaluate(individual)
        
        print "Slave routine on", dicoSupply.configKey
        (slavePrim, slaveCO2, slaveCosts, QUncoveredDesign, QUncoveredAnnual) = sM.slaveMain(pathX, fNameNtw, dicoSupply, solarFeat, gV)
        print slaveCosts, slaveCO2, slavePrim, "slaveCosts, slaveCO2, slavePrim \n"
        
        costs += slaveCosts
        CO2 += slaveCO2
        prim += slavePrim
    
    else:
        print "No buildings connected to network \n"


    print "Add extra costs"
    (addCosts, addCO2, addPrim) = eM.addCosts(indCombi, buildList, pathX, dicoSupply, QUncoveredDesign, QUncoveredAnnual, solarFeat, ntwFeat, gV)
    print addCosts, addCO2, addPrim, "addCosts, addCO2, addPrim \n"
    
    if gV.ZernezFlag == 1:
         coolCosts, coolCO2, coolPrim = 0,0,0
    else:
        (coolCosts, coolCO2, coolPrim) = coolMain.coolingMain(pathX, dicoSupply.configKey, ntwFeat, dicoSupply.WasteServersHeatRecovery, gV)
        
    print coolCosts, coolCO2, coolPrim, "coolCosts, coolCO2, coolPrim \n"
    
    costs += addCosts + coolCosts
    CO2 += addCO2 + coolCO2
    prim += addPrim + coolPrim
    
    
    print "Evaluation of", dicoSupply.configKey, "done"
    print costs, CO2, prim, " = costs, CO2, prim \n"
    return (costs, CO2, prim)


def epsIndicator(frontOld, frontNew):
    """
    Computes the epsilon indicator
    
    Parameters
    ----------
    frontOld : list
        old Pareto front
    frontNew : list
        new Pareto front
    
    Returns
    -------
    epsInd : float
        epsilon indicator between frontOld and frontNew
    
    """
    epsInd = 0
    firstValueAll = True
    
    for indNew in frontNew:
        tempEpsInd = 0
        firstValue = True
        
        for indOld in frontOld:
            (aOld, bOld, cOld) = indOld.fitness.values
            (aNew, bNew, cNew) = indNew.fitness.values
            compare = max(aOld-aNew, bOld-bNew, cOld-cNew)
            
            if firstValue:
                tempEpsInd = compare
                firstValue = False
            
            if compare < tempEpsInd:
                tempEpsInd = compare
        
        if firstValueAll:
            epsInd = tempEpsInd
            firstValueAll = False
            
        if tempEpsInd > epsInd:
            epsInd = tempEpsInd
            
    return epsInd











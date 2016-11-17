"""
====================================
Evaluation function of an individual
====================================

"""
from __future__ import division

import cea.optimization.conversion_storage.slave.slave_main as sM
import cea.optimization.conversion_storage.master.summarize_network as nM
import numpy as np
import pandas as pd

from cea.optimization.conversion_storage import master_to_slave as MSVar
import cea.optimization.conversion_storage.master.generation as generation

import cea.optimization.conversion_storage.master.cost_model as eM
import cea.optimization.preprocessing.other_networks.cooling_network as coolMain
import cea.optimization.supportFn as sFn
import cea.technologies.substation as sMain
import check as cCheck


# +++++++++++++++++++++++++++++++++++++
# Main objective function evaluation
# ++++++++++++++++++++++++++++++++++++++

def evaluation_main(individual, building_names, locator, extraCosts, extraCO2, extraPrim, solar_features,
                    network_features, gv):
    """
    This function evaluates an individual

    :param individual: list with values of the individual
    :param building_names: list with names of buildings
    :param locator: locator class
    :param extra_costs: costs calculated before optimization ofr specific energy services
     (process heat and electricity)
    :param extra_CO2: green house gas emissions calculated before optimization ofr specific energy services
     (process heat and electricity)
    :param extra_primary_energy: primary energy calculated before optimization ofr specific energy services
     (process heat and electricity)
    :param solar_features: solar features call to class
    :param network_features: network features call to class
    :param gv: global variables class
    :return:
        Resulting values of the objective function. costs, CO2, prim

    """
    # Check the consistency of the individual or create a new one
    reject_invalid(individual, len(building_names), gv)

    # Create the string representation of the individual
    indCombi = sFn.individual_to_barcode(individual, gv)

    # Initialize objective functions costs, CO2 and primary energy
    costs = extraCosts
    CO2 = extraCO2
    prim = extraPrim


    QUncoveredDesign = 0
    QUncoveredAnnual = 0

    print indCombi.count("0")
    print indCombi.count("1")

    if indCombi.count("0") == 0:
        fNameNtw = "Network_summary_result_all.csv"
    else:
        fNameNtw = "Network_summary_result_" + indCombi + ".csv"

    if indCombi.count("1") > 0:
        Qheatmax = sFn.calcQmax(fNameNtw, locator.pathNtwRes, gv)
    else:
        Qheatmax = 0

    print Qheatmax, "Qheatmax in distribution"
    Qnom = Qheatmax * (1 + gv.Qmargin_ntw)

    # Modify the individual with the extra GHP constraint
    try:
        cCheck.GHPCheck(individual, locator, Qnom, gv)
        print "GHP constraint checked \n"
    except:
        print "No GHP constraint check possible \n"

    # Export to context
    dicoSupply = readInd(individual, Qheatmax, locator, gv)
    dicoSupply.NETWORK_DATA_FILE = fNameNtw

    if dicoSupply.nBuildingsConnected > 1:
        if indCombi.count("0") == 0:
            dicoSupply.fNameTotalCSV = locator.pathRaw + "/Total.csv"
        else:
            dicoSupply.fNameTotalCSV = locator.pathTotalNtw + "/Total_" + indCombi + ".csv"
    else:
        dicoSupply.fNameTotalCSV = locator.pathSubsRes + "/Total_" + indCombi + ".csv"

    if indCombi.count("1") > 0:
        # print "Dummy evaluation of", dicoSupply.configKey
        # (slavePrim, slaveCO2, slaveCosts, QUncoveredDesign, QUncoveredAnnual) = sFn.dummyevaluate(individual)

        print "Slave routine on", dicoSupply.configKey
        (slavePrim, slaveCO2, slaveCosts, QUncoveredDesign, QUncoveredAnnual) = sM.slaveMain(locator, fNameNtw,
                                                                                             dicoSupply, solar_features,
                                                                                             gv)
        print slaveCosts, slaveCO2, slavePrim, "slaveCosts, slaveCO2, slavePrim \n"

        costs += slaveCosts
        CO2 += slaveCO2
        prim += slavePrim

    else:
        print "No buildings connected to distribution \n"

    print "Add extra costs"
    (addCosts, addCO2, addPrim) = eM.addCosts(indCombi, building_names, locator, dicoSupply, QUncoveredDesign,
                                              QUncoveredAnnual, solar_features, network_features, gv)
    print addCosts, addCO2, addPrim, "addCosts, addCO2, addPrim \n"

    if gv.ZernezFlag == 1:
        coolCosts, coolCO2, coolPrim = 0, 0, 0
    else:
        (coolCosts, coolCO2, coolPrim) = coolMain.coolingMain(locator, dicoSupply.configKey, network_features,
                                                              dicoSupply.WasteServersHeatRecovery, gv)

    print coolCosts, coolCO2, coolPrim, "coolCosts, coolCO2, coolPrim \n"

    costs += addCosts + coolCosts
    CO2 += addCO2 + coolCO2
    prim += addPrim + coolPrim

    print "Evaluation of", dicoSupply.configKey, "done"
    print costs, CO2, prim, " = costs, CO2, prim \n"

    return costs, CO2, prim

#+++++++++++++++++++++++++++++++++++
# Boundary conditions
#+++++++++++++++++++++++++++++


def reject_invalid(individual, nBuildings, gv):
    """
    This function rejects individuals out of the bounds of the problem

    :param individual: individual
    :param nBuildings: number of buildings
    :param gv: global variables class
    :return:
        new individual if necessary
    """
    valid = True

    for i in range(gv.nHeat):
        if individual[2 * i] > 0 and individual[2 * i + 1] < 0.01:
            print "Share too low : modified"
            oldValue = individual[2 * i + 1]
            shareGain = oldValue - 0.01
            individual[2 * i + 1] = 0.01

            for rank in range(gv.nHeat):
                if individual[2 * rank] > 0 and i != rank:
                    individual[2 * rank + 1] += individual[2 * rank + 1] / (1 - oldValue) * shareGain

    frank = gv.nHeat * 2 + gv.nHR
    for i in range(gv.nSolar):
        if individual[frank + 2 * i + 1] < 0:
            print individual[frank + 2 * i + 1], "Negative solar share ! Modified"
            individual[frank + 2 * i + 1] = 0

    sharePlants = 0
    for i in range(gv.nHeat):
        sharePlants += individual[2 * i + 1]
    if abs(sharePlants - 1) > 1E-3:
        print "Wrong plant share !", sharePlants
        valid = False

    shareSolar = 0
    nSol = 0
    for i in range(gv.nSolar):
        nSol += individual[frank + 2 * i]
        shareSolar += individual[frank + 2 * i + 1]
    if nSol > 0 and abs(shareSolar - 1) > 1E-3:
        print "Wrong solar share !", shareSolar
        valid = False

    if not valid:
        print "Non valid individual ! Replace by new one. \n"
        newInd = generation.generate_main(nBuildings, gv)

        L = (gv.nHeat + gv.nSolar) * 2 + gv.nHR
        for i in range(L):
            individual[i] = newInd[i]


def readInd(individual, Qmax, locator, gv):
    """
    Reads the list encoding a configuration and implementes the corresponding
    for the slave routine's to use
    
    Parameters
    ----------
    individual : list
        configuration from the Master routine
    Qmax : float
        peak heating demand
    locator : string
        path to raw files
    
    Returns
    -------
    dicoSupply : class MasterSlaveVariables
    
    """
    dicoSupply = MSVar.MasterSlaveVariables()
    dicoSupply.configKey = "".join(str(e)[0:4] for e in individual)
    
    indCombi = sFn.individual_to_barcode(individual, gv)
    dicoSupply.nBuildingsConnected = indCombi.count("1") # counting the number of buildings connected
    
    Qnom = Qmax * (1+gv.Qmargin_ntw)
    
    # Heating systems
    
    #CHP units with NG & furnace with biomass wet
    if individual[0] == 1 or individual[0] == 3:
        if gv.Furnace_allowed == 1:
            dicoSupply.Furnace_on = 1
            dicoSupply.Furnace_Q_max = max(individual[1] * Qnom, gv.QminShare * Qnom)
            print dicoSupply.Furnace_Q_max, "Furnace wet"
            dicoSupply.Furn_Moist_type = "wet"
        elif gv.CC_allowed == 1:
            dicoSupply.CC_on = 1
            dicoSupply.CC_GT_SIZE = max(individual[1] * Qnom * 1.3, gv.QminShare * Qnom * 1.3)
            #1.3 is the conversion factor between the GT_Elec_size NG and Q_DHN
            print dicoSupply.CC_GT_SIZE, "CC NG"
            dicoSupply.gt_fuel = "NG"
     
    #CHP units with BG& furnace with biomass dry       
    if individual[0] == 2 or individual[0] == 4:
        if gv.Furnace_allowed == 1:
            dicoSupply.Furnace_on = 1
            dicoSupply.Furnace_Q_max = max(individual[1] * Qnom, gv.QminShare * Qnom)
            print dicoSupply.Furnace_Q_max, "Furnace dry"
            dicoSupply.Furn_Moist_type = "dry"
        elif gv.CC_allowed == 1:
            dicoSupply.CC_on = 1
            dicoSupply.CC_GT_SIZE = max(individual[1] * Qnom * 1.5, gv.QminShare * Qnom * 1.5)
            #1.5 is the conversion factor between the GT_Elec_size BG and Q_DHN
            print dicoSupply.CC_GT_SIZE, "CC BG"
            dicoSupply.gt_fuel = "BG"

    # Base boiler NG 
    if individual[2] == 1:
        dicoSupply.Boiler_on = 1
        dicoSupply.Boiler_Q_max = max(individual[3] * Qnom, gv.QminShare * Qnom)
        print dicoSupply.Boiler_Q_max, "Boiler base NG"
        dicoSupply.BoilerType = "NG"
    
    # Base boiler BG    
    if individual[2] == 2:
        dicoSupply.Boiler_on = 1
        dicoSupply.Boiler_Q_max = max(individual[3] * Qnom, gv.QminShare * Qnom)
        print dicoSupply.Boiler_Q_max, "Boiler base BG"
        dicoSupply.BoilerType = "BG"
    
    # peak boiler NG         
    if individual[4] == 1:
        dicoSupply.BoilerPeak_on = 1
        dicoSupply.BoilerPeak_Q_max = max(individual[5] * Qnom, gv.QminShare * Qnom)
        print dicoSupply.BoilerPeak_Q_max, "Boiler peak NG"
        dicoSupply.BoilerPeakType = "NG"
    
    # peak boiler BG   
    if individual[4] == 2:
        dicoSupply.BoilerPeak_on = 1
        dicoSupply.BoilerPeak_Q_max = max(individual[5] * Qnom, gv.QminShare * Qnom)
        print dicoSupply.BoilerPeak_Q_max, "Boiler peak BG"
        dicoSupply.BoilerPeakType = "BG"
    
    # lake - heat pump
    if individual[6] == 1  and gv.HPLake_allowed == 1:
        dicoSupply.HP_Lake_on = 1
        dicoSupply.HPLake_maxSize = max(individual[7] * Qnom, gv.QminShare * Qnom)
        print dicoSupply.HPLake_maxSize, "Lake"
    
    # sewage - heatpump    
    if individual[8] == 1 and gv.HPSew_allowed == 1:
        dicoSupply.HP_Sew_on = 1
        dicoSupply.HPSew_maxSize = max(individual[9] * Qnom, gv.QminShare * Qnom)
        print dicoSupply.HPSew_maxSize, "Sewage"
    
    # Gwound source- heatpump
    if individual[10] == 1 and gv.GHP_allowed == 1:
        dicoSupply.GHP_on = 1
        GHP_Qmax = max(individual[11] * Qnom, gv.QminShare * Qnom)
        dicoSupply.GHP_number = GHP_Qmax / gv.GHP_HmaxSize
        print GHP_Qmax, "GHP"
    
    # heat recovery servers and compresor
    irank = gv.nHeat * 2
    dicoSupply.WasteServersHeatRecovery = individual[irank]
    dicoSupply.WasteCompressorHeatRecovery = individual[irank + 1]
    
    # Solar systems
    roof_area = np.array(pd.read_csv(locator.get_total_demand(), usecols=["Aroof_m2"]))
    
    areaAvail = 0
    totalArea = 0
    for i in range( len(indCombi) ):
        index = indCombi[i]
        if index == "1":
            areaAvail += roof_area[i][0]
        totalArea += roof_area[i][0]

    shareAvail = areaAvail / totalArea    
    
    irank = gv.nHeat * 2 + gv.nHR
    dicoSupply.SOLAR_PART_PV = max(individual[irank] * individual[irank + 1] * individual[irank + 6] * shareAvail,0)
    print dicoSupply.SOLAR_PART_PV, "PV"
    dicoSupply.SOLAR_PART_PVT = max(individual[irank + 2] * individual[irank + 3] * individual[irank + 6] * shareAvail,0)
    print dicoSupply.SOLAR_PART_PVT, "PVT"
    dicoSupply.SOLAR_PART_SC = max(individual[irank + 4] * individual[irank + 5] * individual[irank + 6] * shareAvail,0)
    print dicoSupply.SOLAR_PART_SC, "SC"
    
    return dicoSupply


def checkNtw(individual, ntwList, locator, gv):
    """
    Calls the distribution routine if necessary
    
    Parameters
    ----------
    individual : list
        configuration considered
    ntwList : list
        list of DHN configuration previously encountered in the master
    locator : string
        path to folders
    
    """
    indCombi = sFn.individual_to_barcode(individual, gv)
    print(indCombi)
    
    if not (indCombi in ntwList) and indCombi.count("1") > 0:
        ntwList.append(indCombi)
        
        if indCombi.count("1") == 1:
            total_demand = pd.read_csv(locator.pathNtwRes + "//" +  "Total_" + indCombi + ".csv")
            building_names = total_demand.Name.values
            print "Direct launch of distribution summary routine for", indCombi
            nM.network_main(locator, total_demand, building_names, gv, indCombi)

        else:
            total_demand = sFn.createTotalNtwCsv(indCombi, locator)
            building_names = total_demand.Name.values

            # Run the substation and distribution routines
            print "Re-run the substation routine for new distribution configuration", indCombi
            sMain.substation_main(locator, total_demand, building_names, gv, indCombi)
            
            print "Launch distribution summary routine"
            nM.network_main(locator, total_demand, building_names, gv, indCombi)


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











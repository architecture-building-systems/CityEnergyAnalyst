"""
====================================
Evaluation function of an individual
====================================

"""
from __future__ import division

import os

import cea.optimization.master.generation as generation
import cea.optimization.master.summarize_network as nM
import numpy as np
import pandas as pd

import cea.optimization.master.cost_model as eM
import cea.optimization.preprocessing.cooling_net as coolMain
import cea.optimization.slave.slave_main as sM
import cea.optimization.supportFn as sFn
import cea.technologies.substation as sMain
import check as cCheck
from cea.optimization import slave_data


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
    :param extraCosts: costs calculated before optimization of specific energy services
     (process heat and electricity)
    :param extraCO2: green house gas emissions calculated before optimization of specific energy services
     (process heat and electricity)
    :param extraPrim: primary energy calculated before optimization ofr specific energy services
     (process heat and electricity)
    :param solar_features: solar features call to class
    :param network_features: network features call to class
    :param gv: global variables class
    :type individual: list
    :type building_names: list
    :type locator: string
    :type extraCosts: float
    :type extraCO2: float
    :type extraPrim: float
    :type solar_features: class
    :type network_features: class
    :type gv: class
    :return: Resulting values of the objective function. costs, CO2, prim
    :rtype: tuple

    """
    # Check the consistency of the individual or create a new one
    individual = check_invalid(individual, len(building_names), gv)

    # Initialize objective functions costs, CO2 and primary energy
    costs = extraCosts
    CO2 = extraCO2
    prim = extraPrim
    QUncoveredDesign = 0
    QUncoveredAnnual = 0

    # Create the string representation of the individual
    individual_barcode = sFn.individual_to_barcode(individual, gv)

    if individual_barcode.count("0") == 0:
        network_file_name = "Network_summary_result_all.csv"
    else:
        network_file_name = "Network_summary_result_" + hex(int(str(individual_barcode), 2)) + ".csv"

    if individual_barcode.count("1") > 0:
        Qheatmax = sFn.calcQmax(network_file_name, locator.get_optimization_network_results_folder(), gv)
    else:
        Qheatmax = 0

    Qnom = Qheatmax * (1 + gv.Qmargin_ntw)

    # Modify the individual with the extra GHP constraint
    try:
        cCheck.GHPCheck(individual, locator, Qnom, gv)
        print "GHP constraint checked \n"
    except:
        print "No GHP constraint check possible \n"

    # Export to context
    master_to_slave_vars = calc_master_to_slave_variables(individual, Qheatmax, locator, gv)
    master_to_slave_vars.NETWORK_DATA_FILE = network_file_name

    if master_to_slave_vars.nBuildingsConnected > 1:
        if individual_barcode.count("0") == 0:
            master_to_slave_vars.fNameTotalCSV = locator.get_total_demand()
        else:
            master_to_slave_vars.fNameTotalCSV = os.path.join(locator.get_optimization_network_totals_folder(),
                                                              "Total_%(individual_barcode)s.csv" % locals())
    else:
        master_to_slave_vars.fNameTotalCSV = locator.get_optimization_substations_total_file(individual_barcode)

    if individual_barcode.count("1") > 0:

        (slavePrim, slaveCO2, slaveCosts, QUncoveredDesign, QUncoveredAnnual) = sM.slave_main(locator,
                                                                                              master_to_slave_vars,
                                                                                              solar_features, gv)
        costs += slaveCosts
        CO2 += slaveCO2
        prim += slavePrim

    else:
        print "No buildings connected to distribution \n"

    print "Add extra costs"
    (addCosts, addCO2, addPrim) = eM.addCosts(individual_barcode, building_names, locator, master_to_slave_vars, QUncoveredDesign,
                                              QUncoveredAnnual, solar_features, network_features, gv)
    print addCosts, addCO2, addPrim, "addCosts, addCO2, addPrim \n"

    if gv.ZernezFlag == 1:
        coolCosts, coolCO2, coolPrim = 0, 0, 0
    else:
        (coolCosts, coolCO2, coolPrim) = coolMain.coolingMain(locator, master_to_slave_vars.configKey, network_features,
                                                              master_to_slave_vars.WasteServersHeatRecovery, gv)

    print coolCosts, coolCO2, coolPrim, "coolCosts, coolCO2, coolPrim \n"

    costs += addCosts + coolCosts
    CO2 += addCO2 + coolCO2
    prim += addPrim + coolPrim

    print "Evaluation of", master_to_slave_vars.configKey, "done"
    print costs, CO2, prim, " = costs, CO2, prim \n"

    return costs, CO2, prim

#+++++++++++++++++++++++++++++++++++
# Boundary conditions
#+++++++++++++++++++++++++++++


def check_invalid(individual, nBuildings, gv):
    """
    This function rejects individuals out of the bounds of the problem
    It can also generate a new individual, to replace the rejected individual

    :param individual: individual sent for checking
    :param nBuildings: number of buildings
    :param gv: global variables class
    :type individual: list
    :type nBuildings: int
    :type gv: class
    :return: new individual if necessary
    :rtype: list
    """
    valid = True

    for i in range(gv.nHeat):
        if individual[2 * i] > 0 and individual[2 * i + 1] < 0.01:
            oldValue = individual[2 * i + 1]
            shareGain = oldValue - 0.01
            individual[2 * i + 1] = 0.01

            for rank in range(gv.nHeat):
                if individual[2 * rank] > 0 and i != rank:
                    individual[2 * rank + 1] += individual[2 * rank + 1] / (1 - oldValue) * shareGain

    frank = gv.nHeat * 2 + gv.nHR
    for i in range(gv.nSolar):
        if individual[frank + 2 * i + 1] < 0:
            individual[frank + 2 * i + 1] = 0

    sharePlants = 0
    for i in range(gv.nHeat):
        sharePlants += individual[2 * i + 1]
    if abs(sharePlants - 1) > 1E-3:
        valid = False

    shareSolar = 0
    nSol = 0
    for i in range(gv.nSolar):
        nSol += individual[frank + 2 * i]
        shareSolar += individual[frank + 2 * i + 1]
    if nSol > 0 and abs(shareSolar - 1) > 1E-3:
        valid = False

    if not valid:
        newInd = generation.generate_main(nBuildings, gv)

        L = (gv.nHeat + gv.nSolar) * 2 + gv.nHR
        for i in range(L):
            individual[i] = newInd[i]

    return individual


def calc_master_to_slave_variables(individual, Qmax, locator, gv):
    """
    This function reads the list encoding a configuration and implements the corresponding
    for the slave routine's to use

    :param individual: list with inidividual
    :param Qmax:  peak heating demand
    :param locator: locator class
    :param gv: global variables class
    :type individual: list
    :type Qmax: float
    :type locator: string
    :type gv: class
    :return: master_to_slave_vars : class MasterSlaveVariables
    :rtype: class
    """
    # initialise class storing dynamic variables transfered from master to slave optimization
    master_to_slave_vars = slave_data.SlaveData()
    master_to_slave_vars.configKey = "".join(str(e)[0:4] for e in individual)
    
    individual_barcode = sFn.individual_to_barcode(individual, gv)
    master_to_slave_vars.nBuildingsConnected = individual_barcode.count("1") # counting the number of buildings connected
    
    Qnom = Qmax * (1+gv.Qmargin_ntw)
    
    # Heating systems
    
    #CHP units with NG & furnace with biomass wet
    if individual[0] == 1 or individual[0] == 3:
        if gv.Furnace_allowed == 1:
            master_to_slave_vars.Furnace_on = 1
            master_to_slave_vars.Furnace_Q_max = max(individual[1] * Qnom, gv.QminShare * Qnom)
            master_to_slave_vars.Furn_Moist_type = "wet"
        elif gv.CC_allowed == 1:
            master_to_slave_vars.CC_on = 1
            master_to_slave_vars.CC_GT_SIZE = max(individual[1] * Qnom * 1.3, gv.QminShare * Qnom * 1.3)
            #1.3 is the conversion factor between the GT_Elec_size NG and Q_DHN
            master_to_slave_vars.gt_fuel = "NG"
     
    #CHP units with BG& furnace with biomass dry       
    if individual[0] == 2 or individual[0] == 4:
        if gv.Furnace_allowed == 1:
            master_to_slave_vars.Furnace_on = 1
            master_to_slave_vars.Furnace_Q_max = max(individual[1] * Qnom, gv.QminShare * Qnom)
            master_to_slave_vars.Furn_Moist_type = "dry"
        elif gv.CC_allowed == 1:
            master_to_slave_vars.CC_on = 1
            master_to_slave_vars.CC_GT_SIZE = max(individual[1] * Qnom * 1.5, gv.QminShare * Qnom * 1.5)
            #1.5 is the conversion factor between the GT_Elec_size BG and Q_DHN
            master_to_slave_vars.gt_fuel = "BG"

    # Base boiler NG 
    if individual[2] == 1:
        master_to_slave_vars.Boiler_on = 1
        master_to_slave_vars.Boiler_Q_max = max(individual[3] * Qnom, gv.QminShare * Qnom)
        master_to_slave_vars.BoilerType = "NG"
    
    # Base boiler BG    
    if individual[2] == 2:
        master_to_slave_vars.Boiler_on = 1
        master_to_slave_vars.Boiler_Q_max = max(individual[3] * Qnom, gv.QminShare * Qnom)
        master_to_slave_vars.BoilerType = "BG"
    
    # peak boiler NG         
    if individual[4] == 1:
        master_to_slave_vars.BoilerPeak_on = 1
        master_to_slave_vars.BoilerPeak_Q_max = max(individual[5] * Qnom, gv.QminShare * Qnom)
        master_to_slave_vars.BoilerPeakType = "NG"
    
    # peak boiler BG   
    if individual[4] == 2:
        master_to_slave_vars.BoilerPeak_on = 1
        master_to_slave_vars.BoilerPeak_Q_max = max(individual[5] * Qnom, gv.QminShare * Qnom)
        master_to_slave_vars.BoilerPeakType = "BG"
    
    # lake - heat pump
    if individual[6] == 1  and gv.HPLake_allowed == 1:
        master_to_slave_vars.HP_Lake_on = 1
        master_to_slave_vars.HPLake_maxSize = max(individual[7] * Qnom, gv.QminShare * Qnom)

    # sewage - heatpump    
    if individual[8] == 1 and gv.HPSew_allowed == 1:
        master_to_slave_vars.HP_Sew_on = 1
        master_to_slave_vars.HPSew_maxSize = max(individual[9] * Qnom, gv.QminShare * Qnom)

    # Gwound source- heatpump
    if individual[10] == 1 and gv.GHP_allowed == 1:
        master_to_slave_vars.GHP_on = 1
        GHP_Qmax = max(individual[11] * Qnom, gv.QminShare * Qnom)
        master_to_slave_vars.GHP_number = GHP_Qmax / gv.GHP_HmaxSize

    # heat recovery servers and compresor
    irank = gv.nHeat * 2
    master_to_slave_vars.WasteServersHeatRecovery = individual[irank]
    master_to_slave_vars.WasteCompressorHeatRecovery = individual[irank + 1]
    
    # Solar systems
    roof_area = np.array(pd.read_csv(locator.get_total_demand(), usecols=["Aroof_m2"]))
    
    areaAvail = 0
    totalArea = 0
    for i in range( len(individual_barcode) ):
        index = individual_barcode[i]
        if index == "1":
            areaAvail += roof_area[i][0]
        totalArea += roof_area[i][0]

    shareAvail = areaAvail / totalArea    
    
    irank = gv.nHeat * 2 + gv.nHR
    master_to_slave_vars.SOLAR_PART_PV = max(individual[irank] * individual[irank + 1] * individual[irank + 6] * shareAvail,0)
    master_to_slave_vars.SOLAR_PART_PVT = max(individual[irank + 2] * individual[irank + 3] * individual[irank + 6] * shareAvail,0)
    master_to_slave_vars.SOLAR_PART_SC = max(individual[irank + 4] * individual[irank + 5] * individual[irank + 6] * shareAvail,0)

    return master_to_slave_vars


def checkNtw(individual, ntwList, locator, gv):
    """
    This function calls the distribution routine if necessary
    
    :param individual: network configuration considered
    :param ntwList: list of DHN configurations previously encounterd in the master
    :param locator: path to the folder
    :type individual: list
    :type ntwList: list
    :type locator: string
    :return: None
    :rtype: Nonetype
    """
    indCombi = sFn.individual_to_barcode(individual, gv)

    if not (indCombi in ntwList) and indCombi.count("1") > 0:
        ntwList.append(indCombi)
        
        total_demand = sFn.createTotalNtwCsv(indCombi, locator)
        building_names = total_demand.Name.values

        # Run the substation and distribution routines
        sMain.substation_main(locator, total_demand, building_names, gv, indCombi)

        nM.network_main(locator, total_demand, building_names, gv, indCombi)


def epsIndicator(frontOld, frontNew):
    """
    This function computes the epsilon indicator
    
    :param frontOld: Old Pareto front
    :param frontNew: New Pareto front
    :type frontOld: list
    :type frontNew:list
    :return: epsilon indicator between the old and new Pareto fronts
    :rtype: float
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











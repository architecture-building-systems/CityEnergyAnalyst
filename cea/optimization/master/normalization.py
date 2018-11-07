"""
Normalize results

"""
#import Rep3D as rep
from deap import base

import cea.optimization.supportFn as sFn
from cea.optimization.master import evaluation as eI

reload(sFn)
#reload(rep)
reload(eI)
toolbox = base.Toolbox()



def normalizePop(locator, Generation):
    """
    Normalizes the population with the min / max IN THAT GENERATION
    All 3 objectives are normalized to [0,1] 

    :param locator: inputlocator set to scenario
    :param Generation: generation to extract
    :type locator: string
    :type Generation: int
    :return: normalized population
    :rtype: list
    """
    popFinal, eps, testedPop, ntwList, fitness = sFn.readCheckPoint(locator, Generation, storeData = 0)

    maxCosts =0
    minCosts =0
    
    maxCO2 =0
    minCO2 =0
    
    maxPrim =0
    minPrim =0
    
    popNorm = toolbox.clone(popFinal)
    
    for ind in popFinal:
        if ind.fitness.values[0] < minCosts:
            minCosts = ind.fitness.values[0]
        if ind.fitness.values[0]  > maxCosts:
            maxCosts = ind.fitness.values[0]
            
        if ind.fitness.values[1] < minCO2:
            minCO2 = ind.fitness.values[1]
        if ind.fitness.values[1] > maxCO2:
            maxCO2 = ind.fitness.values[1]
            
        if ind.fitness.values[2] < minPrim:
            minPrim = ind.fitness.values[2]
        if ind.fitness.values[2] > maxPrim:
            maxPrim = ind.fitness.values[2]
    
    
    for i in range( len( popFinal ) ):
        ind = popFinal[i]
        NormCost = (ind.fitness.values[0] - minCosts) / (maxCosts - minCosts)
        NormCO2 = (ind.fitness.values[1] - minCO2) / (maxCO2 - minCO2)
        NormPrim = (ind.fitness.values[2] - minPrim) / (maxPrim - minPrim)
        
        popNorm[i].fitness.values = (NormCost, NormCO2, NormPrim)
            
    return popFinal



def normalize_epsIndicator(locator, generation):
    """
    Calculates the normalized epsilon indicator
    For all generations, the population are normalized with regards to the
    min / max over ALL generations

    :param locator: inputlocator set to scenario
    :param generation: generation up to which data are extracted
    :type locator: string
    :type generation: int
    :return: epsAll, normalized epsilon indicator from the beginning of the master to generation
    :rtype: list
    """
    epsAll = []
    allPop = []
    allPopNorm = []
    
    # Load the population
    i = 1
    while i < generation+1:
        pop, eps, testedPop, ntwList, fitness = sFn.readCheckPoint(locator, i, storeData = 0)
        i+=1
        allPop.append(pop)
        
    # Find the max and min
    maxCosts =0
    minCosts =0
    
    maxCO2 =0
    minCO2 =0
    
    maxPrim =0
    minPrim =0
    
    for i in range(generation):
        popScaned = allPop[i]
        
        for ind in popScaned:
            if ind.fitness.values[0] < minCosts:
                minCosts = ind.fitness.values[0]
            if ind.fitness.values[0]  > maxCosts:
                maxCosts = ind.fitness.values[0]
                
            if ind.fitness.values[1] < minCO2:
                minCO2 = ind.fitness.values[1]
            if ind.fitness.values[1] > maxCO2:
                maxCO2 = ind.fitness.values[1]
                
            if ind.fitness.values[2] < minPrim:
                minPrim = ind.fitness.values[2]
            if ind.fitness.values[2] > maxPrim:
                maxPrim = ind.fitness.values[2]
    
    # Normalize
    for k in range(generation):
        popScaned = allPop[k]
        popNorm = toolbox.clone(popScaned)
    
        for i in range( len( popScaned ) ):
            ind = popScaned[i]
            NormCost = (ind.fitness.values[0] - minCosts) / (maxCosts - minCosts)
            NormCO2 = (ind.fitness.values[1] - minCO2) / (maxCO2 - minCO2)
            NormPrim = (ind.fitness.values[2] - minPrim) / (maxPrim - minPrim)
            
            popNorm[i].fitness.values = (NormCost, NormCO2, NormPrim)
        
        allPopNorm.append(popNorm)
    
    # Compute the eps indicator
    for i in range(generation-1):
        frontOld = allPopNorm[i]
        frontNew = allPopNorm[i+1]
        epsAll.append(eI.epsIndicator(frontOld, frontNew))
    
    return epsAll



def decentralizeCosts(individual, locator, gV):
    """
    :param individual: list of all parameters corresponding to an individual configuration
    :param locator: locator set to the scenario
    :param gV: global variables
    :type individual: list
    :type locator: string
    :type gV: class
    :return: costsDisc
    :rtype: float
    """
    indCombi = sFn.individual_to_barcode(individual, gV)
    buildList = sFn.extract_building_names_from_csv(locator.pathRaw + "/Total.csv")
    costsDisc = 0

    for i in range(len(indCombi)):
        if indCombi[i] == "0": # Decentralized building
            building_name = buildList[i]
            df = pd.read_csv(locator.get_optimization_decentralized_result_file(building_name))
            dfBest = df[df["Best configuration"] == 1]
            costsDisc += dfBest["Annualized Investment Costs [CHF]"].iloc[0]

    print costsDisc, "costsDisc"
    return costsDisc


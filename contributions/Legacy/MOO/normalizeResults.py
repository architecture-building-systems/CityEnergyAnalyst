"""
==============================
Normalize the results and plot
==============================

"""
from deap import base
import numpy as np
import matplotlib.pyplot as plt
import supportFn as sFn
import Rep3D as rep
import evaluateInd as eI
reload(sFn)
reload(rep)
reload(eI)


toolbox = base.Toolbox()


def normalizePop(pathX, Generation):
    """
    Normalizes the population with the min / max IN THAT GENERATION
    All 3 objectives are normalized to [0,1] 
    
    Parameters
    ----------
    pathMasterRes : string
        path to folder where checkpoints are stored
    Generation : int
        generation to extract
    pathNtwRes : string
        path to ntw result folder
    
    Returns
    -------
    popFinal : list
        normalized population
    
    """
    popFinal, eps, testedPop = sFn.readCheckPoint(pathX, Generation, storeData = 0)

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


def plotScatter(pathX, Generation, IndicatorToShowPlot):
    """
    Plots Pareto front as scattered points
    
    """
    popNorm = normalizePop(pathX, Generation)
    rep.rep3Dscatter(popNorm, IndicatorToShowPlot)

def plotSurf(pathX, Generation):
    """
    Plots Pareto front as a surface
    
    """
    popNorm = normalizePop(pathX, Generation)
    rep.rep3Dsurf(popNorm)
    

def epsIndicator(pathX, generation):
    """
    Calculates the normalized epsilon indicator
    For all generations, the populations are normalized with regards to the
    min / max over ALL generations
    
    Parameters
    ----------
    pathMasterRes : string
        path to folder where checkpoints are stored
    generation : int
        generation up to which data are extracted
    pathNtwRes : string
        path to ntw result folder
    
    Returns
    -------
    epsAll : list
        normalized epsilon indicator from the beginning of the EA to generation
    
    """
    epsAll = []
    allPop = []
    allPopNorm = []
    
    # Load the populations
    i = 1
    while i < generation+1:
        pop, eps, testedPop = sFn.readCheckPoint(pathX, i, storeData = 0)
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
    
    # Plotting
    #fig = plt.figure()
    #ax = fig.add_subplot(111, xlim = (2,generation))
    #xList = [ 2 + x for x in range(len(epsAll)) ]
    #ax.plot(xList, epsAll)
    #ax.set_ylabel('Normalized epsilon indicator')
    #ax.set_xlabel('Generation')
    #ax.set_xticks(np.arange(2,generation+1,2))
    #plt.show()
    
    return epsAll
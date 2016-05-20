"""
=================
Mutation routines
=================

"""
from __future__ import division
import random
import EA_globalVar as gV
from deap import base

toolbox = base.Toolbox()


def mutFlip(individual, proba):
    """
    For all integer parameters of individual except the connection integers, 
    flip the value with probability *proba*
    
    Parameters
    ----------
    individual : list
    proba : float
    
    Return
    ------
    mutant : list
    
    """
    mutant = toolbox.clone(individual)
    
    # Flip the CHP
    if individual[0] > 0:
        if random.random() < proba:
            CHPList = [1,2,3,4]
            CHPList.remove(individual[0])
            mutant[0] = random.choice(CHPList)
    
    # Flip the HR units
    for HR in [0,1]:
        if random.random() < proba:
            mutant[gV.nHeat * 2 + HR] = (individual[gV.nHeat * 2 + HR]+1) % 2

    # Flip the buildings' connection
    frank = (gV.nHeat + gV.nSolar + gV.nCool) * 2 + gV.nHR + 1
    nBuildings = len(individual) - frank - 1
    for building in range(nBuildings):
        if random.random() < proba:
            mutant[frank + building] = (individual[frank + building]+1) % 2
    
    del mutant.fitness.values
    
    return mutant


def mutShuffle(individual, proba):
    """
    Swap with probability *proba*
    
    Parameters
    ----------
    individual : list
    proba : float
    
    Return
    ------
    mutant : list
    
    """       
    mutant = toolbox.clone(individual)
    
    # Swap function
    def swap(nPlant, frank):
        for i in xrange(nPlant):
            if random.random() < proba:
                iswap = random.randint(0, nPlant - 2)
                if iswap >= i:
                    iswap += 1
                rank = frank + 2*i
                irank = frank + 2*iswap
                mutant[rank:rank+2], mutant[irank:irank+2] = \
                    mutant[irank:irank+2], mutant[rank:rank+2]
    
    # Swap
    swap(gV.nHeat,0)
    swap(gV.nSolar, gV.nHeat * 2 + gV.nHR)
    swap(gV.nCool, (gV.nHeat + gV.nSolar) * 2 + gV.nHR + 1)

    # Swap buildings
    frank = (gV.nHeat + gV.nSolar + gV.nCool) * 2 + gV.nHR + 1
    nBuildings = len(individual) - frank - 1
    
    for i in xrange(nBuildings):
        if random.random() < proba:
            iswap = random.randint(0, nBuildings - 2)
            if iswap >= i:
                iswap += 1
            rank = frank + i
            irank = frank + iswap
            mutant[rank], mutant[irank] = mutant[irank], mutant[rank]

    del mutant.fitness.values
    
    return mutant   


def mutGaussCap(individual, sigmap):
    """
    Change the continuous variables with a gaussian distribution of mean the
    old value and so that there is 95% change (-2 to 2 sigma) to stay within
    a band of *sigmap* (percentage) of the entire band.
    
    Parameters
    ----------
    individual : list
    sigmap : float
        between 0 and 1 (excluded)
    
    Returns
    -------
    mutant : list
    
    """
    assert (0 < sigmap) and (sigmap < 1)
    mutant = toolbox.clone(individual)
    
    # Gauss fluctuation
    sigma = sigmap / 2
    def deltaGauss(s):
        deltap = random.gauss(0, s)
        if deltap < -1:
            deltap = -0.95
        elif deltap > 1:
            deltap = 0.95
        return -abs(deltap)
    
    # Share fluctuation
    def shareFluct(nPlant, irank):
        for i in xrange(nPlant):
            if mutant[irank + 2*i + 1] == 1:
                break
            
            if mutant[irank + 2*i] > 0:
                oldShare = mutant[irank + 2*i + 1]
                ShareChange = deltaGauss(sigma) * mutant[irank + 2*i + 1]
                mutant[irank + 2*i + 1] += ShareChange
                
                for rank in range(nPlant):
                    if individual[irank + 2*rank] > 0 and i != rank:
                        mutant[irank + 2*rank + 1] += - mutant[irank + 2*rank + 1] / (1-oldShare) * ShareChange

    # Modify the shares
    shareFluct(gV.nHeat, 0)
    shareFluct(gV.nSolar, gV.nHeat * 2 + gV.nHR)
    shareFluct(gV.nCool, (gV.nHeat+gV.nSolar) * 2 + gV.nHR + 1)
    
    # Gauss on the overall solar
    sigma = sigmap / 4
    newOS = random.gauss( individual[(gV.nHeat+gV.nSolar) * 2 + gV.nHR], sigma )
    if newOS < 0:
        newOS = 0
    elif newOS > 1:
        newOS = 1
    mutant[(gV.nHeat+gV.nSolar) * 2 + gV.nHR] = newOS
    
    # Gauss on the CO2 factor
    sigma = sigmap * (gV.CO2Min - gV.CO2Max)/ 4
    newOS = random.gauss( individual[ len(individual)-1 ], sigma )
    if newOS < gV.CO2Min:
        newOS = gV.CO2Min
    elif newOS > gV.CO2Max:
        newOS = gV.CO2Max
    mutant[len(individual)-1] = newOS

    del mutant.fitness.values
    
    return mutant


def mutUniformCap(individual):
    """
    Change the continuous variables with a uniform distribution
    
    Parameters
    ----------
    individual : list
    
    Returns
    -------
    mutant : list
    
    """    
    mutant = toolbox.clone(individual)
    
    # Share fluctuation
    def shareFluct(nPlant, irank):
        for i in xrange(nPlant):
            if mutant[irank + 2*i + 1] == 1:
                break
            
            if mutant[irank + 2*i] > 0:
                oldShare = mutant[irank + 2*i + 1]
                ShareChange = random.uniform(-0.95, 0) * mutant[irank + 2*i + 1]
                mutant[irank + 2*i + 1] += ShareChange
                
                for rank in range(nPlant):
                    if individual[irank + 2*rank] > 0 and i != rank:
                        mutant[irank + 2*rank + 1] -= \
                        mutant[irank + 2*rank + 1] / (1-oldShare) * ShareChange

    # Modify the shares
    shareFluct(gV.nHeat, 0)
    shareFluct(gV.nSolar, gV.nHeat * 2 + gV.nHR)
    shareFluct(gV.nCool, (gV.nHeat+gV.nSolar) * 2 + gV.nHR +1)

    # Change of Overall Solar
    oldValue = individual[(gV.nHeat+gV.nSolar) * 2 + gV.nHR]
    deltaS = random.uniform(- oldValue, 1 - oldValue)
    mutant[(gV.nHeat+gV.nSolar) * 2 + gV.nHR] += deltaS
    
    # Change of CO2 factor
    oldValue = individual[len(individual)-1]
    deltaS = random.uniform(gV.CO2Min - oldValue, gV.CO2Max - oldValue)
    mutant[len(individual)-1] += deltaS

    del mutant.fitness.values
    
    return mutant


def mutGU(individual, proba):
    """
    Flip the presence of the Generation units with probability *proba*
    
    Parameters
    ----------
    individual : list
    proba : float
    
    Return
    ------
    mutant : list
    
    """
    mutant = toolbox.clone(individual)

    def flip(nPlants, irank):
        for rank in range(nPlants):
            if random.random() < proba:
                digit = mutant[irank + 2*rank]
    
                if digit > 0:
                    ShareLoss = mutant[irank + 2*rank + 1]
                    if ShareLoss == 1:
                        pass
                    else:    
                        mutant[irank + 2*rank] = 0
                        mutant[irank + 2*rank + 1] = 0
                        
                        for i in range(nPlants):
                            if mutant[irank + 2*i] > 0 and i != rank:
                                mutant[irank + 2*i + 1] += \
                                mutant[irank + 2*i + 1] / (1-ShareLoss) * ShareLoss
                            
                else:
                    mutant[irank + 2*rank] = 1
                    share = random.uniform(0.05,0.95)
                    mutant[irank + 2*rank + 1] = share
                    
                    for i in range(nPlants):
                        if mutant[irank + 2*i] > 0 and i != rank:
                            mutant[irank + 2*i + 1] = mutant[irank + 2*i + 1] *(1-share)
    
    flip(gV.nHeat, 0)
    flip(gV.nSolar, gV.nHeat * 2 + gV.nHR)
    flip(gV.nCool, (gV.nHeat+gV.nSolar) * 2 + gV.nHR +1)
    
    del mutant.fitness.values
    
    return mutant





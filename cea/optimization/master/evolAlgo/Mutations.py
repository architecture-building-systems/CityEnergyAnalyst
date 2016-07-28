"""
=================
Mutation routines
=================

"""
from __future__ import division
import random
from deap import base

toolbox = base.Toolbox()


def mutFlip(individual, proba, gv):
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
	
    # Flip the Boiler NG/BG
    indexList = [2,4]
    for i in indexList:
        if individual[i] == 1:
            if random.random() < proba:
                individual[i] = 2
        if individual[i] == 2:
            if random.random() < proba:
                individual[i] = 1
    
    # Flip the HR units
    for HR in [0,1]:
        if random.random() < proba:
            mutant[gv.nHeat * 2 + HR] = (individual[gv.nHeat * 2 + HR]+1) % 2

    # Flip the buildings' connection
    frank = (gv.nHeat + gv.nSolar) * 2 + gv.nHR + 1
    nBuildings = len(individual) - frank
    for building in range(nBuildings):
        if random.random() < proba:
            mutant[frank + building] = (individual[frank + building]+1) % 2
    
    del mutant.fitness.values
    
    return mutant


def mutShuffle(individual, proba, gv):
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
    swap(gv.nHeat,0)
    swap(gv.nSolar, gv.nHeat * 2 + gv.nHR)

    # Swap buildings
    frank = (gv.nHeat + gv.nSolar) * 2 + gv.nHR + 1
    nBuildings = len(individual) - frank
    
    for i in xrange(nBuildings):
        if random.random() < proba:
            iswap = random.randint(0, nBuildings - 2)
            if iswap >= i:
                iswap += 1
            rank = frank + i
            irank = frank + iswap
            mutant[rank], mutant[irank] = mutant[irank], mutant[rank]
    
    # Repair the system types
    for i in range(gv.nHeat):
        if i == 0:
            pass
        elif i == 1 or i == 2:
            if mutant[2*i] > 2:
                mutant[2*i] = random.randint(1,2)
        else:
            if mutant[2*i] > 1:
                mutant[2*i] = 1

    del mutant.fitness.values
    
    return mutant   


def mutGaussCap(individual, sigmap, gv):
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
    shareFluct(gv.nHeat, 0)
    shareFluct(gv.nSolar, gv.nHeat * 2 + gv.nHR)
    
    # Gauss on the overall solar
    sigma = sigmap / 4
    newOS = random.gauss( individual[(gv.nHeat+gv.nSolar) * 2 + gv.nHR], sigma )
    if newOS < 0:
        newOS = 0
    elif newOS > 1:
        newOS = 1
    mutant[(gv.nHeat+gv.nSolar) * 2 + gv.nHR] = newOS


    del mutant.fitness.values
    
    return mutant


def mutUniformCap(individual, gv):
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
    shareFluct(gv.nHeat, 0)
    shareFluct(gv.nSolar, gv.nHeat * 2 + gv.nHR)

    # Change of Overall Solar
    oldValue = individual[(gv.nHeat+gv.nSolar) * 2 + gv.nHR]
    deltaS = random.uniform(- oldValue, 1 - oldValue)
    mutant[(gv.nHeat+gv.nSolar) * 2 + gv.nHR] += deltaS


    del mutant.fitness.values
    
    return mutant


def mutGU(individual, proba, gv):
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
					
                    # Modification possible for CHP and Boiler NG/BG
                    if irank + 2*rank == 0:
                        choice_CHP = random.randint(1,4)
                        mutant[irank + 2*rank] = choice_CHP
                    if irank + 2*rank == 2:
                        choice_Boiler = random.randint(1,2)
                        mutant[irank + 2*rank] = choice_Boiler
                    if irank + 2*rank == 4:
                        choice_Boiler = random.randint(1,2)
                        mutant[irank + 2*rank] = choice_Boiler
						
                    share = random.uniform(0.05,0.95)
                    mutant[irank + 2*rank + 1] = share
                    
                    for i in range(nPlants):
                        if mutant[irank + 2*i] > 0 and i != rank:
                            mutant[irank + 2*i + 1] = mutant[irank + 2*i + 1] *(1-share)
    
    flip(gv.nHeat, 0)
    flip(gv.nSolar, gv.nHeat * 2 + gv.nHR)
    
    del mutant.fitness.values
    
    return mutant





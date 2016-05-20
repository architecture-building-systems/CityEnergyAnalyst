"""
==================
Create individuals
==================

"""
from __future__ import division
import random
from numpy.random import random_sample
from itertools import izip
import EA_globalVar as gV


def generateInd(nBuildings):
    """
    Creates an individual for the evolutionary algorithm
    
    Parameters
    ----------
    nBuildings : int
        Number of buildings in the district
    
    Returns
    -------
    individual : list
    
    """
    # Individual represented as a list
    individual = [0] * ( (gV.nHeat + gV.nSolar + gV.nCool) * 2 + gV.nHR + nBuildings + 2 )

    # Count the number of GUs
    countDHN = 0
    countDCN = 0
    countSolar = 0
    
    # Choice of the GUs for the DHN
    while countDHN == 0:
        index = 0

        # First GU to choose is the CHP
        choice_CHP = random.randint(0,1)
        if choice_CHP == 1:
            choice_CHP = random.randint(1,4)
            countDHN += 1
        individual[index] = choice_CHP
        index += 2
        
        # Other GUs for the DHN
        for GU in range(1,gV.nHeat):
            choice_GU = random.randint(0,1)
            if choice_GU == 1:
                countDHN += 1
            individual[index] = choice_GU
            index += 2
    
    # Heat Recovery units
    for HR in range(gV.nHR):
        choice_HR = random.randint(0,1)
        individual[index] = choice_HR
        index += 1
    
    # Solar units
    for Solar in range(gV.nSolar):
        choice_Solar = random.randint(0,1)
        if choice_Solar == 1:
            countSolar += 1
        individual[index] = choice_Solar
        index += 2
    
    # Overall solar availability
    solarAv = random.uniform(0,1)
    individual[index] = solarAv
    index += 1
    
    # Choice of the GUs for the DCN
    while countDCN == 0:
        index = (gV.nHeat + gV.nSolar) * 2 + gV.nHR + 1
        
        for GU in range(gV.nCool):
            choice_GU = random.randint(0,1)
            if choice_GU == 1:
                countDCN += 1
            individual[index] = choice_GU
            index += 2    
    
    # Allocation of Shares
    def cuts(ind, nPlants, irank):
        cuts = sorted(random_sample(nPlants - 1) * 0.99 + 0.01)    
        edge = [0] + cuts + [1]
        share = [(b - a) for a, b in izip(edge, edge[1:])]
        
        n = len(share)
        sharetoallocate = 0
        rank = irank
        while sharetoallocate < n:
            if ind[rank] > 0:
                ind[rank+1] = share[sharetoallocate]
                sharetoallocate += 1
            rank += 2
    
    cuts(individual, countDHN, 0)
    cuts(individual, countDCN, (gV.nHeat + gV.nSolar) * 2 + gV.nHR + 1)

    if countSolar > 0:
        cuts(individual, countSolar, gV.nHeat * 2 + gV.nHR)

    # Connection of the buildings
    for building in range(nBuildings):
        choice_buildCon = random.randint(0,1)
        individual[index] = choice_buildCon
        index += 1

    # CO2 factor
    choiceFactor = random.uniform(0,1)
    CO2Fact = gV.CO2Min + choiceFactor * (gV.CO2Max - gV.CO2Min)
    individual[index] = CO2Fact
    
    return individual







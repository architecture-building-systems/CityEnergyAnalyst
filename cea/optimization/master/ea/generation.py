"""
==================
Create individuals
==================

"""
from __future__ import division
import random
from numpy.random import random_sample
from itertools import izip


def generateInd(nBuildings, gv):
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
    individual = [0] * ( (gv.nHeat + gv.nSolar) * 2 + gv.nHR + nBuildings + 1 )

    # Count the number of GUs (makes sure there's at least one heating system in the central hub)
    countDHN = 0
    countSolar = 0
    
    if gv.nHeat == 0:
        countDHN = 1
    
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
        for GU in range(1,gv.nHeat):
            choice_GU = random.randint(0,1)
            if choice_GU == 1:
                countDHN += 1
            individual[index] = choice_GU
            index += 2
            
        # Boiler NG or BG
        if individual[2] == 1:
            choice_GU = random.randint(1,2)
            individual[2] = choice_GU
        if individual[4] == 1:
            choice_GU = random.randint(1,2)
            individual[4] = choice_GU
    
    # Heat Recovery units
    for HR in range(gv.nHR):
        choice_HR = random.randint(0,1)
        individual[index] = choice_HR
        index += 1
    
    # Solar units
    for Solar in range(gv.nSolar):
        choice_Solar = random.randint(0,1)
        if choice_Solar == 1:
            countSolar += 1
        individual[index] = choice_Solar
        index += 2
    
    # Overall solar availability
    if countSolar > 0:
        solarAv = random.uniform(0,1)
        individual[index] = solarAv
    index += 1
 
    
    # Allocation of Shares
    def cuts(ind, nPlants, irank):
        cuts = sorted(random_sample(nPlants - 1) * 0.99 + 0.009)    
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

    if countSolar > 0:
        cuts(individual, countSolar, gv.nHeat * 2 + gv.nHR)

    # Connection of the buildings
    for building in range(nBuildings):
        choice_buildCon = random.randint(0,1)
        individual[index] = choice_buildCon
        index += 1

    
    return individual







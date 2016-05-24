"""
===================================
Associate plant size to individuals
===================================

"""
from __future__ import division
from numpy.random import random_sample
from itertools import izip
import EA_globalVar as gV


def setPlantSize(individual, buildList, Qmax_dico, QmaxCombi_dico):
    """
    Allocates nominal heating capacity to the plants in the district (in WATTS)
    
    For Disconnected Buildings : nominal capacity is the maximum heating demand
    with a safety margin (the latter is defined in EA_globalVar.py)
    
    For Connected Buildings : the sum of all the nominal capacities is the
    maximum heating demand with a safety margin (same as before)
    The repartition of the capacities between plants is made randomly
    
    Parameters
    ----------
    individual : deap.creator.Individual (list)
        individual
    buildList : list
        List of buildings name
    Qmax_dico : dictionary
        Dictionary with Qmax per building (see QConstraints)
    QmaxCombi_dico : dictionary
        Dictionary with Qmax per combination (see QConstraints)
    
    Returns
    -------
    Nothing, modifies the individual

    """
    nBuildings = len(buildList)
    combi = ""
    for checkDisc in individual[4::4]:
        combi += str(checkDisc)
    
    nDP_Con = 0

    # Define plants' capacity for disconnected buildings
    for rank in range( nBuildings ):
        digit = int( combi[rank] )
        
        if digit == 0:
            building = buildList[rank]
            sizeplant = (1 + gV.margin) * Qmax_dico[building]
            individual[4 * rank + 6] = sizeplant
        
        if digit == 1:
            if individual[4 * rank + 5] != 0:
                nDP_Con += 1
    
    # Define plants' capacity for CP and DP in connected buildings
    Qmax_combi = QmaxCombi_dico[combi] * (1 + gV.margin)
    nPlants = nDP_Con + 1

    cuts = sorted(random_sample(nPlants - 1) * 0.99 + 0.01)    
    edge = [0] + cuts + [1]
    
    intervals = [(b - a) for a, b in izip(edge, edge[1:])]
    plSize = [inter * Qmax_combi for inter in intervals]

    individual[1] = plSize[0]
    planttoallocate = 1
    for rank in range( nBuildings ):
        digit = int( combi[rank] )
        if digit == 1 and individual[4 * rank + 5] != 0:
            individual[4 * rank + 6] = plSize[planttoallocate]
            planttoallocate += 1


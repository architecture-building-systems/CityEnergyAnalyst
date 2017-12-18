"""
=================
CrossOver routine
=================

"""
from __future__ import division
import random
from deap import base
from cea.optimization.constants import *

toolbox = base.Toolbox()


def cxUniform(ind1, ind2, proba):
    """
    Performs a uniform crossover between the two parents.
    Each segments is swapped with probability *proba*
    
    :param ind1: a list containing the parameters of the parent 1
    :param ind2: a list containing the parameters of the parent 2
    :param proba: Crossover probability
    :type ind1: list
    :type ind2: list
    :type proba: float

    :return: child1, child2
    :rtype: list, list
    """
    child1 = toolbox.clone(ind1)
    child2 = toolbox.clone(ind2)
    
    # Swap functions
    def swap(inda, indb, n):
        inda[n], indb[n] = indb[n], inda[n]
    
    def recharge(ind, nPlants, rank, irank, oldvalue):
        for i in range( nPlants ):
            digit = ind[irank + 2*i]            
            if (digit > 0) and (i != rank):
                ind[irank + 2*i + 1] += ind[irank + 2*i + 1] / (1 - oldvalue) \
                    * (oldvalue - ind[irank + 2*rank + 1])
    
    def cross(inda, indb, nPlants, irank):
        # The new arrivant keeps his share
        for rank in range( nPlants ):
            if random.random() < proba:
                digit1 = inda[irank + 2*rank]
                digit2 = indb[irank + 2*rank]
                
                if (digit1 == 0) and (digit2 == 0) :
                    pass
                    
                else :
                    if inda[irank + 2*rank + 1] == 1 or \
                    indb[irank + 2*rank + 1] == 1:
                        pass
                    
                    else:
                        swap(inda, indb, irank + 2*rank)
                        swap(inda, indb, irank + 2*rank + 1)
                        
                        recharge(indb, nPlants, rank, irank, inda[irank + 2*rank + 1])
                        recharge(inda, nPlants, rank, irank, indb[irank + 2*rank + 1])

    def crossInt(inda, indb, nPlants, irank):
        for i in range(nPlants):
            if random.random() < proba:
                swap(inda, indb, irank + i)
    
    # Swap
    cross(child1, child2, nHeat, 0)
    cross(child1, child2, nSolar, nHeat * 2 + nHR)
    
    crossInt(child1, child2, nHR, nHeat * 2)
    crossInt(child1, child2, 1, (nHeat + nSolar) * 2 + nHR)
    
    frank = (nHeat + nSolar) * 2 + nHR + 1
    nBuildings = len(ind1) - frank
    crossInt(child1, child2, nBuildings, frank)
     
    del child1.fitness.values
    del child2.fitness.values
    
    return child1, child2











"""
=================
CrossOver routine
=================

"""
from __future__ import division
import random
from deap import base

toolbox = base.Toolbox()


def cxUniform(ind1, ind2, proba, gV):
    """
    Performs a uniform crossover between the two parents.
    Each segments is swaped with probability *proba*
    
    Parameters
    ----------
    ind1 : list
    ind2 : list
    proba : float
    
    Returns
    -------
    child1 : list
    child2 : list
    
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
    cross(child1, child2, gV.nHeat, 0)
    cross(child1, child2, gV.nSolar, gV.nHeat * 2 + gV.nHR)
    
    crossInt(child1, child2, gV.nHR, gV.nHeat * 2)
    crossInt(child1, child2, 1, (gV.nHeat + gV.nSolar) * 2 + gV.nHR)
    
    frank = (gV.nHeat + gV.nSolar) * 2 + gV.nHR + 1
    nBuildings = len(ind1) - frank
    crossInt(child1, child2, nBuildings, frank)
     
    del child1.fitness.values
    del child2.fitness.values
    
    return child1, child2











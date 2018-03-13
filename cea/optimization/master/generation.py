"""
==================
Create individuals
==================

"""
from __future__ import division
import random
from numpy.random import random_sample
from itertools import izip
from cea.optimization.constants import *


__author__ =  "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def generate_main(nBuildings):
    """
    Creates an individual configuration for the evolutionary algorithm

    :param nBuildings: number of buildings
    :param gv: global variables class
    :type nBuildings: int
    :type gv: class
    :return: individual: representation of values taken by the individual
    :rtype: list
    """

    # create list to store values of inidividual
    individual = [0] * ( (nHeat + nSolar) * 2 + nHR + nBuildings + 1 )
    # Count the number of GUs (makes sure there's at least one heating system in the central hub)
    countDHN = 0
    countSolar = 0
    
    if nHeat == 0:
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
        for GU in range(1,nHeat):
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
    for HR in range(nHR):
        choice_HR = random.randint(0,1)
        individual[index] = choice_HR
        index += 1
    
    # Solar units
    for Solar in range(nSolar):
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
        cuts(individual, countSolar, nHeat * 2 + nHR)

    # Connection of the buildings
    for building in range(nBuildings):
        choice_buildCon = random.randint(0,1)
        individual[index] = choice_buildCon
        index += 1

    
    return individual







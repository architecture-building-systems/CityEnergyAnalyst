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
    Creates an individual configuration for the evolutionary algorithm.
    The individual is divided into four parts namely Heating technologies, Cooling Technologies, Heating Network
    and Cooling Network

    Heating Technologies: This block consists of heating technologies associated with % of the peak capacity each
    technology is going to supply, i.e. 10.1520.2030, which translates into technology 1 corresponding to 15% of peak
    capacity, technology 2 corresponding to 20% and technology 3 corresponding to 0%. 0% can also be just done by replacing
    3 with 0. The technologies block is then followed by supply temperature of the DHN and the number of units it is
    supplied to among AHU, ARU, SHU. So if it is 6 degrees C supplied by DHN to AHU and ARU, it is represented as 6.02.
    The temperature is represented with 1 decimal point.

    Cooling Technologies: This follows the same syntax as heating technologies, but will be represented with cooling
    technologies. The block length of heating and cooling can be different.

    Heating Network: Network of buildings connected to centralized heating

    Cooling Network: Network of buildings connected to centralized cooling. Both these networks can be different, and will
    always have a fixed length corresponding to the total number of buildings in the neighborhood


    :param nBuildings: number of buildings
    :param gv: global variables class
    :type nBuildings: int
    :type gv: class
    :return: individual: representation of values taken by the individual
    :rtype: list
    """

    # heating block
    # create list to store values of inidividual
    heating_block = [0] * ( nHeat * 2 + nHR + nSolar * 2 + 2 ) # nHeat is each technology and is associated with 2 values
    # in the individual, one corresponding to the ON/OFF of technology and second corresponding to the size
    # nHR is the ON/OFF of the recovery technologies, no sizing for these
    # nSolar corresponds to the solar technologies and the associated area in the total solar area
    # 2 corresponds to the temperature and the number of the units supplied to among AHU/ARU/SHU
    # the order of heating technologies is CHP/Furnace, Base Boiler, Peak Boiler, HP Lake, HP Sewage, GHP
    # don't get confused with the order of activation of the technologies, that order is given in heating_resource_activation

    if IS_HEATING:

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
            heating_block[index] = choice_CHP
            index += 2

            # Other GUs for the DHN
            for GU in range(1,nHeat):
                choice_GU = random.randint(0,1)
                if choice_GU == 1:
                    countDHN += 1
                heating_block[index] = choice_GU
                index += 2

            # Boiler NG or BG
            if heating_block[2] == 1:
                choice_GU = random.randint(1,2)
                heating_block[2] = choice_GU
            if heating_block[4] == 1:
                choice_GU = random.randint(1,2)
                heating_block[4] = choice_GU

        # Heat Recovery units
        for HR in range(nHR):
            choice_HR = random.randint(0,1)
            heating_block[index] = choice_HR
            index += 1

        # Solar units
        for Solar in range(nSolar):
            choice_Solar = random.randint(0,1)
            if choice_Solar == 1:
                countSolar += 1
            heating_block[index] = choice_Solar
            index += 2

        # Overall solar availability
        if countSolar > 0:
            solarAv = random.uniform(0,1)
            heating_block[index] = solarAv
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

        cuts(heating_block, countDHN, 0)

        if countSolar > 0:
            cuts(heating_block, countSolar, nHeat * 2 + nHR)

    cooling_block = [0] * ( nCool * 2 + 2) # nCool is each technology and is associated with 2 values
    # the order of cooling technologies is Lake, VCC, Absorption Chiller, Storage
    # 2 corresponds to the temperature and the number of the units supplied to among AHU/ARU/SHU

    if IS_COOLING:
        # Count the number of GUs (makes sure there's at least one heating system in the central hub)
        countDCN = 0

        if nCool == 0:
            countDCN = 1

        # Choice of the GUs for the DHN
        while countDCN == 0:
            index = 0

            # Other GUs for the DHN
            for GU in range(0, nCool):
                choice_GU = random.randint(0, 1)
                if choice_GU == 1:
                    countDCN += 1
                cooling_block[index] = choice_GU
                index += 2

            # Boiler NG or BG
            if cooling_block[2] == 1:
                choice_GU = random.randint(1, 4) # 1 corresponds to heating from CHP, 2 from NG Boiler
                # 3 corresponds to heating from BG Boiler, 4 from Solar Collector
                cooling_block[2] = choice_GU

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
                    ind[rank + 1] = share[sharetoallocate]
                    sharetoallocate += 1
                rank += 2

        cuts(cooling_block, countDCN, 0)


    # DHN
    heating_network_block = [0] * nBuildings
    for i in range(nBuildings):
        choice_buildCon = random.randint(0,1)
        heating_network_block[i] = choice_buildCon

    # DCN
    cooling_network_block = [0] * nBuildings
    for j in range(nBuildings):
        choice_buildCon = random.randint(0,1)
        cooling_network_block[j] = choice_buildCon

    individual = heating_block + cooling_block + heating_network_block + cooling_network_block

    return individual







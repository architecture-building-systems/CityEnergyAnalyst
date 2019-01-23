"""
Mutation routines

"""
from __future__ import division
import random
from deap import base
from cea.optimization.constants import N_HR, N_HEAT, N_SOLAR, N_COOL, INDICES_CORRESPONDING_TO_DCN, INDICES_CORRESPONDING_TO_DHN

toolbox = base.Toolbox()


def mutFlip(individual, proba, nBuildings, config):
    """
    For all integer parameters of individual except the connection integers,
    flip the value with probability *proba*
    :param individual: list of all parameters corresponding to an individual configuration
    :param proba: mutation probability
    :param gv: global variables class
    :type individual: list
    :type proba: float
    :type gv: class
    :return: mutant list
    :rtype: list
    """
    mutant = toolbox.clone(individual)

    if config.district_heating_network:
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
        for HR in range(N_HR):
            if random.random() < proba:
                mutant[N_HEAT * 2 + HR] = (individual[N_HEAT * 2 + HR]+1) % 2
    heating_block = (N_HEAT + N_SOLAR) * 2 + N_HR + INDICES_CORRESPONDING_TO_DHN

    if config.district_cooling_network:

        # Flip the cooling absorption chiller technology
        if individual[heating_block + 4] > 0:
            if random.random() < proba:
                AC_List = [1,2,3,4]
                AC_List.remove(individual[heating_block + 4])
                mutant[heating_block + 4] = random.choice(AC_List)

    # Flip the buildings' connection
    network_block_starting_index = (N_HEAT + N_SOLAR) * 2 + N_HR + INDICES_CORRESPONDING_TO_DHN + N_COOL * 2 + INDICES_CORRESPONDING_TO_DCN
    if config.district_heating_network:
        for building in range(nBuildings):
            if random.random() < proba:
                mutant[network_block_starting_index + building] = (individual[network_block_starting_index + building]+1) % 2

    network_block_starting_index = (N_HEAT + N_SOLAR) * 2 + N_HR + INDICES_CORRESPONDING_TO_DHN + N_COOL * 2 + INDICES_CORRESPONDING_TO_DCN + nBuildings
    if config.district_cooling_network:
        for building in range(nBuildings):
            if random.random() < proba:
                mutant[network_block_starting_index + building] = (individual[network_block_starting_index + building]+1) % 2

    del mutant.fitness.values

    return mutant


def mutShuffle(individual, proba, nBuildings, config):
    """
    Swap with probability *proba*
    :param individual: list of all parameters corresponding to an individual configuration
    :param proba: mutation probability
    :type individual: list
    :type proba: float
    :return: mutant list
    :rtype: list
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
    if config.district_heating_network:
        swap(N_HEAT,0)
    swap(N_SOLAR, N_HEAT * 2 + N_HR)
    if config.district_cooling_network:
        swap(N_COOL, (N_HEAT + N_SOLAR) * 2 + N_HR + INDICES_CORRESPONDING_TO_DHN)

    # Swap buildings
    network_block_starting_index = (N_HEAT + N_SOLAR) * 2 + N_HR + INDICES_CORRESPONDING_TO_DHN + N_COOL * 2 + INDICES_CORRESPONDING_TO_DCN

    if config.district_heating_network:
        for i in range(nBuildings):
            if random.random() < proba:
                iswap = random.randint(0, nBuildings - 2)
                if iswap >= i:
                    iswap += 1
                rank = network_block_starting_index + i
                irank = network_block_starting_index + iswap
                mutant[rank], mutant[irank] = mutant[irank], mutant[rank]

    network_block_starting_index = (N_HEAT + N_SOLAR) * 2 + N_HR + INDICES_CORRESPONDING_TO_DHN + N_COOL * 2 + INDICES_CORRESPONDING_TO_DCN + nBuildings

    if config.district_cooling_network:
        for i in range(nBuildings):
            if random.random() < proba:
                iswap = random.randint(0, nBuildings - 2)
                if iswap >= i:
                    iswap += 1
                rank = network_block_starting_index + i
                irank = network_block_starting_index + iswap
                mutant[rank], mutant[irank] = mutant[irank], mutant[rank]


    # Repair the system types
    for i in range(N_HEAT):
        if i == 0:
            pass
        elif i == 1 or i == 2:
            if mutant[2*i] > 2:
                mutant[2*i] = random.randint(1,2)
        else:
            if mutant[2*i] > 1:
                mutant[2*i] = 1

    # Repair the cooling system types
    for i in range(N_COOL):
        if i == 2:
            pass

        else:
            if mutant[(N_HEAT + N_SOLAR) * 2 + N_HR + INDICES_CORRESPONDING_TO_DHN + 2*i] > 1:
                mutant[(N_HEAT + N_SOLAR) * 2 + N_HR + INDICES_CORRESPONDING_TO_DHN + 2*i] = 1

    del mutant.fitness.values

    return mutant


def mutGaussCap(individual, sigmap):
    """
    Change the continuous variables with a gaussian distribution of mean of the
    old value and so that there is 95% chance (-2 to 2 sigma) to stay within
    a band of *sigmap* (percentage) of the entire band.
    :param individual: list of all parameters corresponding to an individual configuration
    :param sigmap: random value between 0 and 1 (1 is excluded )
    :type individual: list
    :type sigmap: float
    :return: mutant list
    :rtype: list
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
    shareFluct(N_HEAT, 0)
    shareFluct(N_SOLAR, N_HEAT * 2 + N_HR)
    
    # Gauss on the overall solar
    sigma = sigmap / 4
    newOS = random.gauss(individual[(N_HEAT + N_SOLAR) * 2 + N_HR], sigma)
    if newOS < 0:
        newOS = 0
    elif newOS > 1:
        newOS = 1
    mutant[(N_HEAT + N_SOLAR) * 2 + N_HR] = newOS


    del mutant.fitness.values

    return mutant


def mutUniformCap(individual):
    """
    Change the continuous variables with a uniform distribution
    :param individual: list of all parameters corresponding to an individual configuration
    :param gv: global variables class
    :type individual: list
    :type gv: class
    :return: mutant list
    :rtype:list
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
    shareFluct(N_HEAT, 0)
    shareFluct(N_SOLAR, N_HEAT * 2 + N_HR)

    # Change of Overall Solar
    oldValue = individual[(N_HEAT + N_SOLAR) * 2 + N_HR]
    deltaS = random.uniform(- oldValue, 1 - oldValue)
    mutant[(N_HEAT + N_SOLAR) * 2 + N_HR] += deltaS


    del mutant.fitness.values

    return mutant


def mutGU(individual, proba, config):
    """
    Flip the presence of the Generation units with probability *proba*
    :param individual: list of all parameters corresponding to an individual configuration
    :param proba: mutation probability
    :type individual: list
    :type proba: float
    :return: mutant list
    :rtype: list
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
    if config.district_heating_network:
        flip(N_HEAT, 0)
    flip(N_SOLAR, N_HEAT * 2 + N_HR)
    if config.district_cooling_network:
        flip(N_COOL, (N_HEAT + N_SOLAR) * 2 + N_HR + INDICES_CORRESPONDING_TO_DHN)

    
    del mutant.fitness.values
    
    return mutant

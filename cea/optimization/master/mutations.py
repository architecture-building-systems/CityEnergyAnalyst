"""
Mutation routines

"""
from __future__ import division

import random

from deap import tools, base

from cea.optimization.constants import N_HR, N_HEAT, N_SOLAR, N_COOL, INDICES_CORRESPONDING_TO_DCN, \
    INDICES_CORRESPONDING_TO_DHN

from cea.optimization.master.validation import validation_main


def mutation_main(individual, indpb,
                  column_names,
                  heating_unit_names,
                  cooling_unit_names,
                  heating_unit_names_share,
                  cooling_unit_names_share,
                  column_names_buildings_heating,
                  column_names_buildings_cooling,
                  district_heating_network,
                  district_cooling_network
                  ):
    # create dict of individual with his/her name
    individual_with_name_dict = dict(zip(column_names, individual))

    if district_heating_network:
        # MUTATE BUILDINGS CONNECTED
        buildings_heating = [individual_with_name_dict[column] for column in column_names_buildings_heating]
        # apply mutations
        buildings_heating_mutated = tools.mutFlipBit(buildings_heating, indpb)[0]
        # takeback to teh individual
        for column, mutated_value in zip(column_names_buildings_heating, buildings_heating_mutated):
            individual_with_name_dict[column] = mutated_value

        # MUTATE SUPPLY SYSTEM UNITS
        heating_units = [individual_with_name_dict[column] for column in heating_unit_names]
        # apply mutations
        heating_units_mutated = tools.mutFlipBit(heating_units, indpb)[0]
        # takeback to teh individual
        for column, mutated_value in zip(heating_unit_names, heating_units_mutated):
            individual_with_name_dict[column] = mutated_value

        # MUTATE SUPPLY SYSTEM UNITS SHARE
        heating_units_share = [individual_with_name_dict[column] for column in heating_unit_names_share]
        # apply mutations
        heating_units_share_mutated = tools.mutFlipBit(heating_units_share, indpb)[0]
        # takeback to teh individual
        for column, mutated_value in zip(heating_unit_names_share, heating_units_share_mutated):
            individual_with_name_dict[column] = mutated_value


    if district_cooling_network:

        # MUTATE BUILDINGS CONNECTED
        buildings_cooling = [individual_with_name_dict[column] for column in column_names_buildings_cooling]
        # apply mutations
        buildings_cooling_mutated = tools.mutFlipBit(buildings_cooling, indpb)[0]
        # take back to teh individual
        for column, mutated_value in zip(column_names_buildings_cooling, buildings_cooling_mutated):
            individual_with_name_dict[column] = mutated_value

        # MUTATE SUPPLY SYSTEM UNITS
        cooling_units = [individual_with_name_dict[column] for column in cooling_unit_names]
        # apply mutations
        cooling_units_mutated = tools.mutFlipBit(cooling_units, indpb)[0]
        # takeback to teh individual
        for column, mutated_value in zip(cooling_unit_names, cooling_units_mutated):
            individual_with_name_dict[column] = mutated_value

        # MUTATE SUPPLY SYSTEM UNITS SHARE
        cooling_units_share = [individual_with_name_dict[column] for column in cooling_unit_names_share]
        # apply mutations
        cooling_units_share_mutated = tools.mutFlipBit(cooling_units_share, indpb)[0]
        # takeback to teh individual
        for column, mutated_value in zip(cooling_unit_names_share, cooling_units_share_mutated):
            individual_with_name_dict[column] = mutated_value

    #now validate individual
    individual_with_name_dict = validation_main(individual_with_name_dict,
                                               heating_unit_names,
                                               cooling_unit_names,
                                               heating_unit_names_share,
                                               cooling_unit_names_share,
                                               column_names_buildings_heating,
                                               column_names_buildings_cooling,
                                               district_heating_network,
                                               district_cooling_network
                                               )

    #now pass all the values mutated to the original individual
    for i, column in enumerate(column_names):
        individual[i] = individual_with_name_dict[column]

    return individual, #add the, because deap needs this


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
    # local variables
    district_heating_network = config.optimization.district_heating_network
    district_cooling_network = config.optimization.district_cooling_network

    # Swap function
    def swap(nPlant, frank):
        for i in xrange(nPlant):
            if random.random() < proba:
                iswap = random.randint(0, nPlant - 2)
                if iswap >= i:
                    iswap += 1
                rank = frank + 2 * i
                irank = frank + 2 * iswap
                mutant[rank:rank + 2], mutant[irank:irank + 2] = \
                    mutant[irank:irank + 2], mutant[rank:rank + 2]

    # Swap
    if district_heating_network:
        swap(N_HEAT, 0)
    swap(N_SOLAR, N_HEAT * 2 + N_HR)
    if district_cooling_network:
        swap(N_COOL, (N_HEAT + N_SOLAR) * 2 + N_HR + INDICES_CORRESPONDING_TO_DHN)

    # Swap buildings
    network_block_starting_index = (
                                           N_HEAT + N_SOLAR) * 2 + N_HR + INDICES_CORRESPONDING_TO_DHN + N_COOL * 2 + INDICES_CORRESPONDING_TO_DCN

    if district_heating_network:
        for i in range(nBuildings):
            if random.random() < proba:
                iswap = random.randint(0, nBuildings - 2)
                if iswap >= i:
                    iswap += 1
                rank = network_block_starting_index + i
                irank = network_block_starting_index + iswap
                mutant[rank], mutant[irank] = mutant[irank], mutant[rank]

    network_block_starting_index = (
                                           N_HEAT + N_SOLAR) * 2 + N_HR + INDICES_CORRESPONDING_TO_DHN + N_COOL * 2 + INDICES_CORRESPONDING_TO_DCN + nBuildings

    if district_cooling_network:
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
            if mutant[2 * i] > 2:
                mutant[2 * i] = random.randint(1, 2)
        else:
            if mutant[2 * i] > 1:
                mutant[2 * i] = 1

    # Repair the cooling system types
    for i in range(N_COOL):
        if i == 2:
            pass

        else:
            if mutant[(N_HEAT + N_SOLAR) * 2 + N_HR + INDICES_CORRESPONDING_TO_DHN + 2 * i] > 1:
                mutant[(N_HEAT + N_SOLAR) * 2 + N_HR + INDICES_CORRESPONDING_TO_DHN + 2 * i] = 1

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
            if mutant[irank + 2 * i + 1] == 1:
                break

            if mutant[irank + 2 * i] > 0:
                oldShare = mutant[irank + 2 * i + 1]
                ShareChange = deltaGauss(sigma) * mutant[irank + 2 * i + 1]
                mutant[irank + 2 * i + 1] += ShareChange

                for rank in range(nPlant):
                    if individual[irank + 2 * rank] > 0 and i != rank:
                        mutant[irank + 2 * rank + 1] += - mutant[irank + 2 * rank + 1] / (1 - oldShare) * ShareChange

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
            if mutant[irank + 2 * i + 1] == 1:
                break

            if mutant[irank + 2 * i] > 0:
                oldShare = mutant[irank + 2 * i + 1]
                ShareChange = random.uniform(-0.95, 0) * mutant[irank + 2 * i + 1]
                mutant[irank + 2 * i + 1] += ShareChange

                for rank in range(nPlant):
                    if individual[irank + 2 * rank] > 0 and i != rank:
                        mutant[irank + 2 * rank + 1] -= \
                            mutant[irank + 2 * rank + 1] / (1 - oldShare) * ShareChange

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
    # local variables
    district_heating_network = config.optimization.district_heating_network
    district_cooling_network = config.optimization.district_cooling_network

    def flip(nPlants, irank):
        for rank in range(nPlants):
            if random.random() < proba:
                digit = mutant[irank + 2 * rank]

                if digit > 0:
                    ShareLoss = mutant[irank + 2 * rank + 1]
                    if ShareLoss == 1:
                        pass
                    else:
                        mutant[irank + 2 * rank] = 0
                        mutant[irank + 2 * rank + 1] = 0

                        for i in range(nPlants):
                            if mutant[irank + 2 * i] > 0 and i != rank:
                                mutant[irank + 2 * i + 1] += \
                                    mutant[irank + 2 * i + 1] / (1 - ShareLoss) * ShareLoss

                else:
                    mutant[irank + 2 * rank] = 1

                    # Modification possible for CHP and Boiler NG/BG
                    if irank + 2 * rank == 0:
                        choice_CHP = random.randint(1, 4)
                        mutant[irank + 2 * rank] = choice_CHP
                    if irank + 2 * rank == 2:
                        choice_Boiler = random.randint(1, 2)
                        mutant[irank + 2 * rank] = choice_Boiler
                    if irank + 2 * rank == 4:
                        choice_Boiler = random.randint(1, 2)
                        mutant[irank + 2 * rank] = choice_Boiler

                    share = random.uniform(0.05, 0.95)
                    mutant[irank + 2 * rank + 1] = share

                    for i in range(nPlants):
                        if mutant[irank + 2 * i] > 0 and i != rank:
                            mutant[irank + 2 * i + 1] = mutant[irank + 2 * i + 1] * (1 - share)

    if district_heating_network:
        flip(N_HEAT, 0)
    flip(N_SOLAR, N_HEAT * 2 + N_HR)
    if district_cooling_network:
        flip(N_COOL, (N_HEAT + N_SOLAR) * 2 + N_HR + INDICES_CORRESPONDING_TO_DHN)

    del mutant.fitness.values

    return mutant

from __future__ import division

import json
import multiprocessing
import random
import time
import warnings
from itertools import repeat, izip

from math import factorial
import numpy as np
import pandas as pd
from deap import tools, creator, base

from cea.optimization import supportFn
from cea.optimization.constants import CXPB, MUTPB, NAMES_TECHNOLOGY_OF_INDIVIDUAL
from cea.optimization.master import crossover
from cea.optimization.master import evaluation
from cea.optimization.master import mutations
from cea.optimization.master.generation import generate_main

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

warnings.filterwarnings("ignore")
NOBJ = 3  # number of objectives
creator.create("FitnessMin", base.Fitness, weights=(-1.0,) * NOBJ)
creator.create("Individual", list, typecode='d', fitness=creator.FitnessMin)


def objective_function(individual, individual_number, generation, building_names, locator,
                       network_features, config, prices, lca):
    """
    Objective function is used to calculate the costs, CO2, primary energy and the variables corresponding to the
    individual
    :param individual: Input individual
    :type individual: list
    :return: returns costs, CO2, primary energy and the master_to_slave_vars
    """
    print('cea optimization progress: individual ' + str(individual_number) + ' and generation ' + str(
        generation) + '/' + str(config.optimization.ngen))
    costs_USD, CO2_ton, prim_MJ, master_to_slave_vars, valid_individual = evaluation.evaluation_main(individual,
                                                                                                     building_names,
                                                                                                     locator,
                                                                                                     network_features,
                                                                                                     config,
                                                                                                     prices, lca,
                                                                                                     individual_number,
                                                                                                     generation)

    return costs_USD, CO2_ton, prim_MJ


def objective_function_wrapper(args):
    """
    Wrap arguments because multiprocessing only accepts one argument for the function"""
    return objective_function(*args)


def non_dominated_sorting_genetic_algorithm(locator, building_names,
                                            network_features, config, prices, lca):
    t0 = time.clock()

    # initiating hall of fame size and the function evaluations
    euclidean_distance = 0
    spread = 0
    random.seed(config.optimization.random_seed)
    np.random.seed(config.optimization.random_seed)

    # get number of buildings
    nBuildings = len(building_names)

    # SET-UP EVOLUTIONARY ALGORITHM
    # Hyperparameters
    NOBJ = 3  # number of objectives
    NGEN = config.optimization.ngen   # number of individuals
    MU = config.optimization.initialind #int(H + (4 - H % 4)) # number of individuals to select

    K = config.optimization.initialind  # number of individuals to select
    # NDIM = NOBJ + K - 1  # number of problem dimensions
    P = [2, 1]
    P2 = 12
    SCALES = [1, 0.5]
    H = factorial(NOBJ + P2 - 1) / (factorial(P2) * factorial(NOBJ - 1))
    # BOUND_LOW, BOUND_UP = 0.0, 1.0

    # classes and tools
    # reference points
    ref_points = [tools.uniform_reference_points(NOBJ, p, s) for p, s in zip(P, SCALES)]
    ref_points = np.concatenate(ref_points)
    _, uniques = np.unique(ref_points, axis=0, return_index=True)
    ref_points = ref_points[uniques]
    toolbox = base.Toolbox()
    toolbox.register("generate", generate_main, nBuildings, config)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.generate)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", objective_function_wrapper)
    # toolbox.register("mate", tools.cxSimulatedBinaryBounded, low=BOUND_LOW, up=BOUND_UP, eta=30.0)
    # toolbox.register("mutate", tools.mutPolynomialBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0, indpb=1.0 / NDIM)
    toolbox.register("select", tools.selNSGA3, ref_points=ref_points)

    # configure multiprocessing
    if config.multiprocessing:
        pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
        toolbox.register("map", pool.map)

    # Initialize statistics object
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean, axis=0)
    stats.register("std", np.std, axis=0)
    stats.register("min", np.min, axis=0)
    stats.register("max", np.max, axis=0)

    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "std", "min", "avg", "max"

    pop = toolbox.population(n=MU)

    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in pop if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, izip(invalid_ind, range(len(invalid_ind)), repeat(0, len(invalid_ind)),
                                         repeat(building_names, len(invalid_ind)),
                                         repeat(locator, len(invalid_ind)),
                                         repeat(network_features, len(invalid_ind)),
                                         repeat(config, len(invalid_ind)),
                                         repeat(prices, len(invalid_ind)), repeat(lca, len(invalid_ind))))
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    # Compile statistics about the population
    record = stats.compile(pop)
    logbook.record(gen=0, evals=len(invalid_ind), **record)

    print(logbook.stream)

    # Begin the generational process
    # Initialization of variables
    DHN_network_list = []
    DCN_network_list = []
    halloffame = []
    halloffame_fitness = []
    epsInd = []
    # this will help when we save the results (to know what the individual has inside
    columns_of_saved_files = initialize_column_names_of_individual(building_names)
    for gen in range(1, NGEN+1):
        print ("Evaluating Generation %s{} of %s{} generations", gen)
        # Select and clone the next generation individuals
        pop_cloned = map(toolbox.clone, toolbox.select(pop, len(pop)))

        # Apply crossover and mutation on the pop
        offspring = []
        for child1, child2 in zip(pop_cloned[::2], pop_cloned[1::2]):
            child1, child2 = crossover.cxUniform(child1, child2, CXPB, nBuildings, config)
            del child1.fitness.values
            del child2.fitness.values
            offspring += [child1, child2]

        # Apply mutation
        for mutant in pop_cloned:
            mutant = mutations.mutFlip(mutant, MUTPB, nBuildings, config)
            mutant = mutations.mutShuffle(mutant, MUTPB, nBuildings, config)
            offspring.append(mutations.mutGU(mutant, MUTPB, config))

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate,
                                    izip(invalid_ind, range(len(invalid_ind)), repeat(gen, len(invalid_ind)),
                                         repeat(building_names, len(invalid_ind)),
                                         repeat(locator, len(invalid_ind)),
                                         repeat(network_features, len(invalid_ind)),
                                         repeat(config, len(invalid_ind)),
                                         repeat(prices, len(invalid_ind)), repeat(lca, len(invalid_ind))))
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # Select the next generation population from parents and offspring
        pop = toolbox.select(pop + offspring, MU)

        # Compile statistics about the new population
        record = stats.compile(pop)
        logbook.record(gen=gen, evals=len(invalid_ind), **record)
        print(logbook.stream)

        DCN_network_list_selected = []
        DHN_network_list_selected = []
        for individual in pop:
            DHN_barcode, DCN_barcode, DHN_configuration, DCN_configuration = supportFn.individual_to_barcode(individual,
                                                                                                             building_names)
            DCN_network_list_selected.append(DCN_barcode)
            DHN_network_list_selected.append(DHN_barcode)

        DHN_network_list_tested = []
        DCN_network_list_tested = []
        for individual in invalid_ind:
            DHN_barcode, DCN_barcode, DHN_configuration, DCN_configuration = supportFn.individual_to_barcode(individual,
                                                                                                             building_names)
            DCN_network_list_tested.append(DCN_barcode)
            DHN_network_list_tested.append(DHN_barcode)

        print "Save population \n"
        save_generation_dataframes(gen, invalid_ind, locator, DCN_network_list_tested, DHN_network_list_tested)
        save_generation_individuals(columns_of_saved_files, gen, invalid_ind, locator)

        # Create Checkpoint if necessary
        print "Create CheckPoint", gen, "\n"
        with open(locator.get_optimization_checkpoint(gen), "wb") as fp:
            cp = dict(selected_population=pop,
                      generation=gen,
                      all_population_DHN_network_barcode=DHN_network_list,
                      all_population_DCN_network_barcode=DCN_network_list,
                      tested_population_DHN_network_barcode=DHN_network_list_tested,
                      tested_population_DCN_network_barcode=DCN_network_list_tested,
                      selected_population_DHN_network_barcode=DHN_network_list_selected,
                      selected_population_DCN_network_barcode=DCN_network_list_selected,
                      tested_population=invalid_ind,
                      tested_population_fitness=fitnesses,
                      epsIndicator=epsInd,
                      halloffame=halloffame,
                      halloffame_fitness=halloffame_fitness,
                      euclidean_distance=euclidean_distance,
                      spread=spread,
                      detailed_electricity_pricing=config.optimization.detailed_electricity_pricing,
                      district_heating_network=config.optimization.district_heating_network,
                      district_cooling_network=config.optimization.district_cooling_network
                      )
            json.dump(cp, fp)

    print("save totals for generation")
    print "Master Work Complete \n"
    # print ("Number of function evaluations = " + str(function_evals))
    t1 = time.clock()
    print (t1 - t0)
    if config.multiprocessing:
        pool.close()

    return pop, logbook


def save_generation_dataframes(generation, slected_individuals, locator, DCN_network_list_selected,
                               DHN_network_list_selected):
    individual_list = range(len(slected_individuals))
    individual_name_list = ["Option " + str(x) for x in individual_list]
    performance_distributed = pd.DataFrame()
    performance_cooling = pd.DataFrame()
    performance_heating = pd.DataFrame()
    performance_electricity = pd.DataFrame()
    performance_totals = pd.DataFrame()
    for ind, DCN_barcode, DHN_barcode in zip(individual_list, DCN_network_list_selected, DHN_network_list_selected):
        if DHN_barcode.count("1") > 0:
            performance_heating = pd.concat([performance_heating,
                                             pd.read_csv(
                                                 locator.get_optimization_slave_heating_performance(ind, generation))],
                                            ignore_index=True)
        if DCN_barcode.count("1") > 0:
            performance_cooling = pd.concat([performance_cooling,
                                             pd.read_csv(
                                                 locator.get_optimization_slave_cooling_performance(ind, generation))],
                                            ignore_index=True)

        performance_distributed = pd.concat([performance_distributed, pd.read_csv(
            locator.get_optimization_slave_disconnected_performance(ind, generation))], ignore_index=True)
        performance_electricity = pd.concat([performance_electricity, pd.read_csv(
            locator.get_optimization_slave_electricity_performance(ind, generation))], ignore_index=True)
        performance_totals = pd.concat([performance_totals,
                                        pd.read_csv(
                                            locator.get_optimization_slave_total_performance(ind, generation))],
                                       ignore_index=True)

    performance_distributed['individual'] = individual_list
    performance_cooling['individual'] = individual_list
    performance_heating['individual'] = individual_list
    performance_electricity['individual'] = individual_list
    performance_totals['individual'] = individual_list
    performance_distributed['individual_name'] = individual_name_list
    performance_cooling['individual_name'] = individual_name_list
    performance_heating['individual_name'] = individual_name_list
    performance_electricity['individual_name'] = individual_name_list
    performance_totals['individual_name'] = individual_name_list
    performance_distributed['generation'] = generation
    performance_cooling['generation'] = generation
    performance_heating['generation'] = generation
    performance_electricity['generation'] = generation
    performance_totals['generation'] = generation

    # save all results to disk
    performance_distributed.to_csv(locator.get_optimization_generation_disconnected_performance(generation))
    performance_cooling.to_csv(locator.get_optimization_generation_cooling_performance(generation))
    performance_heating.to_csv(locator.get_optimization_generation_heating_performance(generation))
    performance_electricity.to_csv(locator.get_optimization_generation_electricity_performance(generation))
    performance_totals.to_csv(locator.get_optimization_generation_total_performance(generation))


def save_generation_individuals(columns_of_saved_files, generation, invalid_ind, locator):
    # now get information about individuals and save to disk
    individual_list = range(len(invalid_ind))
    individuals_info = pd.DataFrame()
    for ind in invalid_ind:
        infividual_dict = pd.DataFrame(dict(zip(columns_of_saved_files, [[x] for x in ind])))
        individuals_info = pd.concat([infividual_dict, individuals_info], ignore_index=True)

    individuals_info['individual'] = individual_list
    individuals_info['generation'] = generation
    individuals_info.to_csv(locator.get_optimization_individuals_in_generation(generation))


def initialize_column_names_of_individual(building_names):
    # here we take the names of technologies we consider for each individual
    # and expanded to the potential connections of buildings to the district heating and cooling networks.
    Name_of_entries_of_individual = NAMES_TECHNOLOGY_OF_INDIVIDUAL
    for i in building_names:  # DHN
        Name_of_entries_of_individual.append(str(i) + ' DHN')
    for i in building_names:  # DCN
        Name_of_entries_of_individual.append(str(i) + ' DCN')

    return Name_of_entries_of_individual


def convergence_metric(old_front, new_front, normalization):
    #  This function calculates the metrics corresponding to a Pareto-front
    #  combined_euclidean_distance calculates the euclidean distance between the current front and the previous one
    #  it is done by locating the choosing a point on current front and the closest point in the previous front and
    #  calculating normalized euclidean distance

    #  Spread discusses on the spread of the Pareto-front, i.e. how evenly the Pareto front is spaced. This is calculated
    #  by identifying the closest neighbour to a point on the Pareto-front. Distance to each closest neighbour is then
    #  subtracted by the mean distance for all the points on the Pareto-front (i.e. closest neighbors for all points).
    #  The ideal value for this is to be 'zero'

    combined_euclidean_distance = 0

    for indNew in new_front:

        (aNew, bNew, cNew) = indNew.fitness.values
        distance = []
        for i, indOld in enumerate(old_front):
            (aOld, bOld, cOld) = indOld.fitness.values
            distance_mix = ((aNew - aOld) / normalization[0]) ** 2 + ((bNew - bOld) / normalization[1]) ** 2 + (
                    (cNew - cOld) / normalization[2]) ** 2
            distance_mix = round(distance_mix, 5)
            distance.append(np.sqrt(distance_mix))

        combined_euclidean_distance = combined_euclidean_distance + min(distance)

    combined_euclidean_distance = (combined_euclidean_distance) / (len(new_front))

    spread = []
    nearest_neighbor = []

    for i, ind_i in enumerate(new_front):
        spread_i = []
        (cost_i, co2_i, eprim_i) = ind_i.fitness.values
        for j, ind_j in enumerate(new_front):
            (cost_j, co2_j, eprim_j) = ind_j.fitness.values
            if i != j:
                spread_mix = ((cost_i - cost_j) / normalization[0]) ** 2 + ((co2_i - co2_j) / normalization[1]) ** 2 + (
                        (eprim_i - eprim_j) / normalization[2]) ** 2
                spread_mix = round(spread_mix, 5)
                spread.append(np.sqrt(spread_mix))
                spread_i.append(np.sqrt(spread_mix))

        nearest_neighbor.append(min(spread_i))
    average_spread = np.mean(spread)

    nearest_neighbor = [abs(x - average_spread) for x in nearest_neighbor]

    spread_final = np.sum(nearest_neighbor)

    print ('combined euclidean distance = ' + str(combined_euclidean_distance))
    print ('spread = ' + str(spread_final))

    return combined_euclidean_distance, spread_final


if __name__ == "__main__":
    x = 'no_testing_todo'

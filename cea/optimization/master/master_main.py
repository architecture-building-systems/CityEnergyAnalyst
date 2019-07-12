from __future__ import division

import json
import multiprocessing
import random
import time
import warnings
from itertools import repeat, izip

import numpy as np
import pandas as pd
from deap import base
from deap import creator
from deap import tools

import cea.config
from cea.optimization import supportFn
from cea.optimization.constants import PROBA, SIGMAP, NAMES_TECHNOLOGY_OF_INDIVIDUAL
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
creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0, -1.0))
creator.create("Individual", list, typecode='d', fitness=creator.FitnessMin)
config = cea.config.Configuration()
random.seed(config.optimization.random_seed)
np.random.seed(config.optimization.random_seed)


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

    genCP = config.optimization.recoverycheckpoint
    # initiating hall of fame size and the function evaluations
    halloffame_size = config.optimization.halloffame
    function_evals = 0
    euclidean_distance = 0
    spread = 0
    proba, sigmap = PROBA, SIGMAP

    # get number of buildings
    nBuildings = len(building_names)

    # SET-UP EVOLUTIONARY ALGORITHM
    # Contains 3 minimization objectives : Costs, CO2 emissions, Primary Energy Needs
    # this part of the script sets up the optimization algorithm in the same syntax of DEAP toolbox
    toolbox = base.Toolbox()
    toolbox.register("generate", generate_main, nBuildings, config)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.generate)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", objective_function_wrapper)
    toolbox.register("select", tools.selNSGA2)

    # configure multiprocessing
    if config.multiprocessing:
        pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
        toolbox.register("map", pool.map)

    # Initialization of variables
    DHN_network_list = []
    DCN_network_list = []
    halloffame = []
    halloffame_fitness = []
    epsInd = []

    #this will help when we save the results (to know what the individual has inside
    columns_of_saved_files = initialize_column_names_of_individual(building_names)

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("min", np.min, axis=0)
    stats.register("max", np.max, axis=0)

    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "std", "min", "avg", "max"

    if genCP is 0:

        pop = toolbox.population(n=config.optimization.initialind)

        for ind in pop:
            DHN_network_list, DCN_network_list = evaluation.checkNtw(ind, DHN_network_list, DCN_network_list, locator,
                                                                     config, building_names)

        # Evaluate the initial population
        print "Evaluate initial population"

        # Evaluate the individuals with an invalid fitness
        tested_population = [ind for ind in pop if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate,
                                izip(tested_population, range(len(tested_population)), repeat(genCP, len(tested_population)),
                                     repeat(building_names, len(tested_population)),
                                     repeat(locator, len(tested_population)),
                                     repeat(network_features, len(tested_population)),
                                     repeat(config, len(tested_population)),
                                     repeat(prices, len(tested_population)), repeat(lca, len(tested_population))))

        function_evals = function_evals + len(tested_population)  # keeping track of number of function evaluations
        # linking every individual with the corresponding fitness, this also keeps a track of the number of function
        # evaluations. This can further be used as a stopping criteria in future
        for ind, fit in zip(tested_population, fitnesses):
            ind.fitness.values = fit

        pop = toolbox.select(pop, len(pop))  # assigning crowding distance

        # halloffame is the best individuals that are observed in all generations
        # the size of the halloffame is linked to the number of initial individuals
        if len(halloffame) <= halloffame_size:
            halloffame.extend(pop)

        #get only the DHN and DCN list for selected individuals
        DCN_network_list_selected = []
        DHN_network_list_selected = []
        for individual in pop:
            DHN_barcode, DCN_barcode, DHN_configuration, DCN_configuration = supportFn.individual_to_barcode(individual,
                                                                                                             building_names)
            DCN_network_list_selected.append(DCN_barcode)
            DHN_network_list_selected.append(DHN_barcode)


        DHN_network_list_tested = []
        DCN_network_list_tested = []
        for individual in tested_population:
            DHN_barcode, DCN_barcode, DHN_configuration, DCN_configuration = supportFn.individual_to_barcode(individual,
                                                                                                             building_names)
            DCN_network_list_tested.append(DCN_barcode)
            DHN_network_list_tested.append(DHN_barcode)

        print "Save Initial population \n"
        save_generation_dataframes(genCP, tested_population, locator, DCN_network_list_tested,
                                   DHN_network_list_tested)
        save_generation_individuals(columns_of_saved_files, genCP, tested_population, locator)

        with open(locator.get_optimization_checkpoint_initial(), "wb") as fp:
            cp = dict(nsga_selected_population=pop,
                      generation=0,
                      all_population_DHN_network_barcode=DHN_network_list,
                      all_population_DCN_network_barcode=DCN_network_list,
                      tested_population_DHN_network_barcode=DHN_network_list_tested,
                      tested_population_DCN_network_barcode=DCN_network_list_tested,
                      selected_population_DHN_network_barcode=DHN_network_list_selected,
                      selected_population_DCN_network_barcode=DCN_network_list_selected,
                      tested_population=tested_population,
                      tested_population_fitness=fitnesses,
                      epsIndicator=epsInd,
                      halloffame=halloffame,
                      halloffame_fitness=halloffame_fitness,
                      euclidean_distance=euclidean_distance,
                      spread=spread,
                      detailed_electricity_pricing=config.optimization.detailed_electricity_pricing,
                      district_heating_network=config.optimization.district_heating_network,
                      district_cooling_network=config.optimization.district_cooling_network)
            json.dump(cp, fp)
    else:
        print "Recover from CP " + str(genCP) + "\n"
        # import the checkpoint based on the genCP
        with open(locator.get_optimization_checkpoint(genCP), "rb") as fp:
            cp = json.load(fp)
            pop = toolbox.population(n=config.optimization.initialind)
            for i in xrange(len(pop)):
                for j in xrange(len(pop[i])):
                    pop[i][j] = cp['nsga_selected_population'][i][j]
            DHN_network_list = cp['DHN_network_list']
            DCN_network_list = cp['DCN_network_list']

            for ind in pop:
                DHN_network_list, DCN_network_list = evaluation.checkNtw(ind, DHN_network_list, DCN_network_list,
                                                                         locator, config, building_names)

            # Evaluate the individuals with an invalid fitness
            tested_population = [ind for ind in pop if not ind.fitness.valid]


            fitnesses = toolbox.map(toolbox.evaluate,
                                    izip(tested_population, range(len(tested_population)), repeat(genCP, len(tested_population)),
                                         repeat(building_names, len(tested_population)),
                                         repeat(locator, len(tested_population)),
                                         repeat(network_features, len(tested_population)),
                                         repeat(config, len(tested_population)),
                                         repeat(prices, len(tested_population)), repeat(lca, len(tested_population))))

            function_evals = function_evals + len(tested_population)  # keeping track of number of function evaluations
            # linking every individual with the corresponding fitness, this also keeps a track of the number of function
            # evaluations. This can further be used as a stopping criteria in future
            for ind, fit in zip(pop, fitnesses):
                ind.fitness.values = fit

            pop = toolbox.select(pop, len(pop))  # assigning crowding distance

    # Evolution starts !

    g = genCP
    stopCrit = False  # Threshold for the Epsilon indicator, Not used
    xs = [((objectives[0])) for objectives in fitnesses]  # Costs
    ys = [((objectives[1])) for objectives in fitnesses]  # GHG emissions
    zs = [((objectives[2])) for objectives in fitnesses]  # MJ

    # normalization is used for optimization metrics as the objectives are all present in different scales
    # to have a consistent value for normalization, the values of the objectives of the initial generation are taken
    normalization = [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)]

    # Initialization of variables
    while g < config.optimization.ngen and not stopCrit and (time.clock() - t0) < config.optimization.maxtime:
        g += 1
        print "Generation", g
        offspring = list(pop)
        # Apply crossover and mutation on the pop
        for ind1, ind2 in zip(pop[::2], pop[1::2]):
            child1, child2 = crossover.cxUniform(ind1, ind2, proba, nBuildings, config)
            offspring += [child1, child2]

        for mutant in pop:
            mutant = mutations.mutFlip(mutant, proba, nBuildings, config)
            mutant = mutations.mutShuffle(mutant, proba, nBuildings, config)
            offspring.append(mutations.mutGU(mutant, proba, config))

        tested_population = [ind for ind in offspring if not ind.fitness.valid]

        for ind in tested_population:
            DHN_network_list, DCN_network_list, evaluation.checkNtw(ind, DHN_network_list, DCN_network_list, locator,
                                                                    config, building_names)

        # Evaluate the individuals with an invalid fitness
        fitnesses = toolbox.map(toolbox.evaluate,
                                izip(tested_population, range(len(tested_population)), repeat(g, len(tested_population)),
                                     repeat(building_names, len(tested_population)),
                                     repeat(locator, len(tested_population)),
                                     repeat(network_features, len(tested_population)),
                                     repeat(config, len(tested_population)),
                                     repeat(prices, len(tested_population)), repeat(lca, len(tested_population))))

        function_evals = function_evals + len(tested_population)  # keeping track of number of function evaluations
        # linking every individual with the corresponding fitness, this also keeps a track of the number of function
        # evaluations. This can further be used as a stopping criteria in future
        for ind, fit in zip(tested_population, fitnesses):
            ind.fitness.values = fit

        selection = toolbox.select(pop + tested_population, config.optimization.initialind)  # assigning crowding distance

        if len(halloffame) <= halloffame_size:
            halloffame.extend(selection)
        else:
            halloffame.extend(selection)
            halloffame = toolbox.select(halloffame, halloffame_size)

        halloffame_fitness = []
        for ind in halloffame:
            halloffame_fitness.append(ind.fitness.values)

        # Compute the epsilon criteria [and check the stopping criteria]
        epsInd.append(evaluation.epsIndicator(pop, selection))
        # compute the optimization metrics for every front apart from generation 0
        euclidean_distance, spread = convergence_metric(pop, selection, normalization)

        pop[:] = selection

        DCN_network_list_selected = []
        DHN_network_list_selected = []
        for individual in pop:
            DHN_barcode, DCN_barcode, DHN_configuration, DCN_configuration = supportFn.individual_to_barcode(individual,
                                                                                                             building_names)
            DCN_network_list_selected.append(DCN_barcode)
            DHN_network_list_selected.append(DHN_barcode)

        DHN_network_list_tested = []
        DCN_network_list_tested = []
        for individual in tested_population:
            DHN_barcode, DCN_barcode, DHN_configuration, DCN_configuration = supportFn.individual_to_barcode(individual,
                                                                                                             building_names)
            DCN_network_list_tested.append(DCN_barcode)
            DHN_network_list_tested.append(DHN_barcode)

        print "Save population \n"
        save_generation_dataframes(g, tested_population, locator, DCN_network_list_tested, DHN_network_list_tested)
        save_generation_individuals(columns_of_saved_files, g, tested_population, locator)

        # Create Checkpoint if necessary
        # The networks created for all the tested population is bigger than the selected population, as this is being
        # used in plots scripts, they are exclusively separated with two variables, which are further used
        if g % config.optimization.fcheckpoint == 0:
            print "Create CheckPoint", g, "\n"
            with open(locator.get_optimization_checkpoint(g), "wb") as fp:
                cp = dict(selected_population=pop,
                          generation=g,
                          all_population_DHN_network_barcode=DHN_network_list,
                          all_population_DCN_network_barcode=DCN_network_list,
                          tested_population_DHN_network_barcode=DHN_network_list_tested,
                          tested_population_DCN_network_barcode=DCN_network_list_tested,
                          selected_population_DHN_network_barcode=DHN_network_list_selected,
                          selected_population_DCN_network_barcode=DCN_network_list_selected,
                          tested_population=tested_population,
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

    if g == config.optimization.ngen:
        print "Final Generation reached"
    else:
        print "Stopping criteria reached"

    # Dataframe with all the individuals whose objective functions are calculated, gathering all the results from
    # multiple generations
    df = pd.read_csv(locator.get_optimization_individuals_in_generation(0))
    for i in range(config.optimization.ngen):
        df = df.append(pd.read_csv(locator.get_optimization_individuals_in_generation(i + 1)),ignore_index=True)
    df.to_csv(locator.get_optimization_all_individuals())
    # # Saving the final results
    # print "Save final results. " + str(len(pop)) + " individuals in final population"
    with open(locator.get_optimization_checkpoint_final(), "wb") as fp:
        cp = dict(selected_population=pop,
                  generation=g,
                  all_population_DHN_network_barcode=DHN_network_list,
                  all_population_DCN_network_barcode=DCN_network_list,
                  tested_population_DHN_network_barcode=DHN_network_list_tested,
                  tested_population_DCN_network_barcode=DCN_network_list_tested,
                  selected_population_DHN_network_barcode=DHN_network_list_selected,
                  selected_population_DCN_network_barcode=DCN_network_list_selected,
                  tested_population=tested_population,
                  tested_population_fitness=fitnesses,
                  epsIndicator=epsInd,
                  halloffame=halloffame,
                  halloffame_fitness=halloffame_fitness,
                  euclidean_distance=euclidean_distance,
                  spread=spread,
                  detailed_electricity_pricing=config.optimization.detailed_electricity_pricing,
                  district_heating_network=config.optimization.district_heating_network,
                  district_cooling_network=config.optimization.district_cooling_network)
        json.dump(cp, fp)

    print("save totals for generation")
    print "Master Work Complete \n"
    print ("Number of function evaluations = " + str(function_evals))
    t1 = time.clock()
    print (t1 - t0)
    if config.multiprocessing:
        pool.close()

    return pop, logbook


def save_generation_dataframes(generation, slected_individuals, locator, DCN_network_list_selected, DHN_network_list_selected):

    individual_list = range(len(slected_individuals))
    performance_distributed = pd.DataFrame()
    performance_cooling = pd.DataFrame()
    performance_heating = pd.DataFrame()
    performance_electricity = pd.DataFrame()
    performance_totals = pd.DataFrame()
    for ind, DCN_barcode, DHN_barcode in zip(individual_list,DCN_network_list_selected,DHN_network_list_selected) :
        if DHN_barcode.count("1") > 0:
            performance_heating = pd.concat([performance_heating,
                                             pd.read_csv(
                                                 locator.get_optimization_slave_heating_performance(ind, generation))],
                                            ignore_index=True)
        if DCN_barcode.count("1") > 0:
            performance_cooling = pd.concat([performance_cooling,
                                             pd.read_csv(locator.get_optimization_slave_cooling_performance(ind, generation))],
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
    performance_distributed['generation'] = generation
    performance_cooling['generation'] = generation
    performance_heating['generation'] = generation
    performance_electricity['generation'] = generation
    performance_totals['generation'] = generation

    #save all results to disk
    performance_distributed.to_csv(locator.get_optimization_generation_disconnected_performance(generation))
    performance_cooling.to_csv(locator.get_optimization_generation_cooling_performance(generation))
    performance_heating.to_csv(locator.get_optimization_generation_heating_performance(generation))
    performance_electricity.to_csv(locator.get_optimization_generation_electricity_performance(generation))
    performance_totals.to_csv(locator.get_optimization_generation_total_performance(generation))



def save_generation_individuals(columns_of_saved_files, generation, invalid_ind, locator):

    #now get information about individuals and save to disk
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

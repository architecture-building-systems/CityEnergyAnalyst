from __future__ import division

from cea.optimization.constants import PROBA, SIGMAP, NAMES_TECHNOLOGY_OF_INDIVIDUAL
import random
from cea.optimization.master import crossover
from cea.optimization.master import mutations
import cea.config
import cea.globalvar
import cea.inputlocator
from cea.optimization.prices import Prices as Prices
from cea.optimization.distribution.network_optimization_features import NetworkOptimizationFeatures
from cea.optimization.preprocessing.preprocessing_main import preproccessing
from cea.optimization.lca_calculations import LcaCalculations
import json
import cea
import pandas as pd
import multiprocessing
import time
import numpy as np
from deap import base
from deap import creator
from deap import tools
from cea.optimization.master.generation import generate_main
from cea.optimization.master import evaluation
from itertools import repeat, izip
from cea.optimization import supportFn

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0, -1.0))
creator.create("Individual", list, typecode='d', fitness=creator.FitnessMin)
config = cea.config.Configuration()
random.seed(config.optimization.random_seed)
np.random.seed(config.optimization.random_seed)


def objective_function(individual, individual_number, generation, building_names, locator, solar_features,
                       network_features, gv, config, prices, lca):
    """
    Objective function is used to calculate the costs, CO2, primary energy and the variables corresponding to the
    individual
    :param individual: Input individual
    :type individual: list
    :return: returns costs, CO2, primary energy and the master_to_slave_vars
    """
    print ('cea optimization progress: individual ' + str(individual_number) + ' and generation ' + str(
        generation) + '/' + str(config.optimization.ngen))
    costs, CO2, prim, master_to_slave_vars, valid_individual = evaluation.evaluation_main(individual, building_names,
                                                                                          locator, solar_features,
                                                                                          network_features, gv, config,
                                                                                          prices, lca,
                                                                                          individual_number, generation)
    return costs, CO2, prim


def objective_function_wrapper(args):
    """
    Wrap arguments because multiprocessing only accepts one argument for the function"""
    return objective_function(*args)


def non_dominated_sorting_genetic_algorithm(locator, building_names, solar_features,
                                            network_features, gv, config, prices, lca):
    t0 = time.clock()

    genCP = config.optimization.recoverycheckpoint

    # genCP = 2
    # NDIM = 30
    # MU = 500

    # initiating hall of fame size and the function evaluations
    halloffame_size = config.optimization.halloffame
    function_evals = 0
    euclidean_distance = 0
    spread = 0

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
    DHN_network_list = ["1" * nBuildings]
    DCN_network_list = ["1" * nBuildings]
    halloffame = []
    halloffame_fitness = []
    epsInd = []

    columns_of_saved_files= initialize_column_names_of_individual(building_names)

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("min", np.min, axis=0)
    stats.register("max", np.max, axis=0)

    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "std", "min", "avg", "max"

    if genCP is 0:

        pop = toolbox.population(n=config.optimization.initialind)

        for ind in pop:
            evaluation.checkNtw(ind, DHN_network_list, DCN_network_list, locator, gv, config, building_names)

        # Evaluate the initial population
        print "Evaluate initial population"
        DHN_network_list = DHN_network_list[
                           1:]  # done this to remove the first individual in the ntwList as it is an initial value
        DCN_network_list = DCN_network_list[1:]

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in pop if not ind.fitness.valid]

        fitnesses = toolbox.map(toolbox.evaluate,
                                izip(invalid_ind, range(len(invalid_ind)), repeat(genCP, len(invalid_ind)),
                                     repeat(building_names, len(invalid_ind)),
                                     repeat(locator, len(invalid_ind)), repeat(solar_features, len(invalid_ind)),
                                     repeat(network_features, len(invalid_ind)), repeat(gv, len(invalid_ind)),
                                     repeat(config, len(invalid_ind)),
                                     repeat(prices, len(invalid_ind)), repeat(lca, len(invalid_ind))))

        function_evals = function_evals + len(invalid_ind)  # keeping track of number of function evaluations
        # linking every individual with the corresponding fitness, this also keeps a track of the number of function
        # evaluations. This can further be used as a stopping criteria in future
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        pop = toolbox.select(pop, len(pop))  # assigning crowding distance

        # halloffame is the best individuals that are observed in all generations
        # the size of the halloffame is linked to the number of initial individuals
        if len(halloffame) <= halloffame_size:
            halloffame.extend(pop)

        print "Save Initial population \n"
        save_generation_dataframe(columns_of_saved_files, genCP, invalid_ind, locator)

        with open(locator.get_optimization_checkpoint_initial(), "wb") as fp:
            cp = dict(nsga_selected_population=pop, generation=0, DHN_List=DHN_network_list, DCN_list=DCN_network_list,
                      tested_population=[],
                      tested_population_fitness=fitnesses, halloffame=halloffame, halloffame_fitness=halloffame_fitness)
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
            DHN_network_list = DHN_network_list
            DCN_network_list = DCN_network_list

            for ind in pop:
                evaluation.checkNtw(ind, DHN_network_list, DCN_network_list, locator, gv, config, building_names)

            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in pop if not ind.fitness.valid]

            fitnesses = toolbox.map(toolbox.evaluate,
                                    izip(invalid_ind, range(len(invalid_ind)), repeat(genCP, len(invalid_ind)),
                                         repeat(building_names, len(invalid_ind)),
                                         repeat(locator, len(invalid_ind)), repeat(solar_features, len(invalid_ind)),
                                         repeat(network_features, len(invalid_ind)), repeat(gv, len(invalid_ind)),
                                         repeat(config, len(invalid_ind)),
                                         repeat(prices, len(invalid_ind)), repeat(lca, len(invalid_ind))))

            function_evals = function_evals + len(invalid_ind)  # keeping track of number of function evaluations
            # linking every individual with the corresponding fitness, this also keeps a track of the number of function
            # evaluations. This can further be used as a stopping criteria in future
            for ind, fit in zip(pop, fitnesses):
                ind.fitness.values = fit

            pop = toolbox.select(pop, len(pop))  # assigning crowding distance

    proba, sigmap = PROBA, SIGMAP

    # variables used for generating graphs
    # graphs are being generated for every generation, it is shown in 2D plot with colorscheme for the 3rd objective
    xs = [((objectives[0])) for objectives in fitnesses]  # Costs
    ys = [((objectives[1])) for objectives in fitnesses]  # GHG emissions
    zs = [((objectives[2])) for objectives in fitnesses]  # MJ

    # normalization is used for optimization metrics as the objectives are all present in different scales
    # to have a consistent value for normalization, the values of the objectives of the initial generation are taken
    normalization = [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)]

    xs = [a / 10 ** 6 for a in xs]
    ys = [a / 10 ** 6 for a in ys]
    zs = [a / 10 ** 6 for a in zs]

    # Evolution starts !

    g = genCP
    stopCrit = False  # Threshold for the Epsilon indicator, Not used

    while g < config.optimization.ngen and not stopCrit and (time.clock() - t0) < config.optimization.maxtime:

        # Initialization of variables
        DHN_network_list = []
        DCN_network_list = []

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

        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]

        for ind in invalid_ind:
            evaluation.checkNtw(ind, DHN_network_list, DCN_network_list, locator, gv, config, building_names)

        # Evaluate the individuals with an invalid fitness
        fitnesses = toolbox.map(toolbox.evaluate,
                                izip(invalid_ind, range(len(invalid_ind)), repeat(g, len(invalid_ind)),
                                     repeat(building_names, len(invalid_ind)),
                                     repeat(locator, len(invalid_ind)), repeat(solar_features, len(invalid_ind)),
                                     repeat(network_features, len(invalid_ind)), repeat(gv, len(invalid_ind)),
                                     repeat(config, len(invalid_ind)),
                                     repeat(prices, len(invalid_ind)), repeat(lca, len(invalid_ind))))

        function_evals = function_evals + len(invalid_ind)  # keeping track of number of function evaluations
        # linking every individual with the corresponding fitness, this also keeps a track of the number of function
        # evaluations. This can further be used as a stopping criteria in future
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        print "Save population \n"
        save_generation_dataframe(columns_of_saved_files, g, invalid_ind, locator)

        selection = toolbox.select(pop + invalid_ind, config.optimization.initialind)  # assigning crowding distance

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

        # Create Checkpoint if necessary
        # The networks created for all the tested population is bigger than the selected population, as this is being
        # used in plots scripts, they are exclusively separated with two variables, which are further used
        if g % config.optimization.fcheckpoint == 0:
            print "Create CheckPoint", g, "\n"
            with open(locator.get_optimization_checkpoint(g), "wb") as fp:
                cp = dict(nsga_selected_population=pop, generation=g, DHN_list_All=DHN_network_list,
                          DCN_list_All=DCN_network_list,
                          DHN_list_selected=DHN_network_list_selected, DCN_list_selected=DCN_network_list_selected,
                          tested_population=invalid_ind, tested_population_fitness=fitnesses, epsIndicator=epsInd,
                          halloffame=halloffame, halloffame_fitness=halloffame_fitness,
                          euclidean_distance=euclidean_distance, spread=spread)
                json.dump(cp, fp)

    if g == config.optimization.ngen:
        print "Final Generation reached"
    else:
        print "Stopping criteria reached"

    # Dataframe with all the individuals whose objective functions are calculated, gathering all the results from
    # multiple generations
    df = pd.read_csv(locator.get_optimization_individuals_in_generation(0))
    for i in range(config.optimization.ngen):
        df = df.append(pd.read_csv(locator.get_optimization_individuals_in_generation(i + 1)))
    df.to_csv(locator.get_optimization_all_individuals())
    # Saving the final results
    print "Save final results. " + str(len(pop)) + " individuals in final population"
    with open(locator.get_optimization_checkpoint_final(), "wb") as fp:
        cp = dict(nsga_selected_population=pop, generation=g, DHN_List=DHN_network_list, DCN_list=DCN_network_list,
                  tested_population=invalid_ind, tested_population_fitness=fitnesses, epsIndicator=epsInd,
                  halloffame=halloffame, halloffame_fitness=halloffame_fitness,
                  euclidean_distance=euclidean_distance, spread=spread)
        json.dump(cp, fp)

    print "Master Work Complete \n"
    print ("Number of function evaluations = " + str(function_evals))
    t1 = time.clock()
    print (t1 - t0)
    if config.multiprocessing:
        pool.close()

    return pop, logbook


def save_generation_dataframe(columns_of_saved_files, genCP, invalid_ind, locator):
    saved_dataframe_for_each_generation = pd.DataFrame()
    for i, ind in enumerate(invalid_ind):
        # the next code splits the information form teh individual in everyone of
        # the prescribed columns_of_saved_files
        output_individual = {}
        for k, configuration in enumerate(ind):
            output_individual[columns_of_saved_files[k]] = configuration
        # now we append more values to that dict
        output_individual['individual'] = i
        output_individual['generation'] = genCP
        output_individual['TAC'] = ind.fitness.values[0]
        output_individual['CO2 emissions'] = ind.fitness.values[1]
        output_individual['Primary Energy'] = ind.fitness.values[2]

        # then we save it to the dataframe
        saved_dataframe_for_each_generation = saved_dataframe_for_each_generation.append(output_individual,
                                                                                         ignore_index=True)
    saved_dataframe_for_each_generation.to_csv(locator.get_optimization_individuals_in_generation(genCP))


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
    config = cea.config.Configuration()
    gv = cea.globalvar.GlobalVariables()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    weather_file = config.weather
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    gv.num_tot_buildings = total_demand.Name.count()
    lca = LcaCalculations(locator, config.detailed_electricity_pricing)
    prices = Prices(locator, config)
    solar_features = preproccessing(locator, total_demand, building_names,weather_file, gv, config,
                                                                                  prices, lca)

    # optimize the distribution and linearize the results(at the moment, there is only a linearization of values in Zug)
    print "NETWORK OPTIMIZATION"
    nBuildings = len(building_names)

    network_features = network_opt_main.network_opt_main(config, locator)
    #network_features = NetworkOptimizationFeatures(config, locator)

    non_dominated_sorting_genetic_algorithm(locator, building_names,
                                            solar_features,
                                            network_features, gv, config, prices, lca)

from __future__ import division

import json
import random
import time
from itertools import repeat, izip

import numpy as np
import pandas as pd
from deap import base
from deap import creator
from deap import tools

import cea
import cea.config
import cea.inputlocator
from cea.optimization.flexibility_model.electric_and_thermal_grid_planning.electrical_grid_calculations import \
    electric_network_optimization
from cea.optimization.flexibility_model.electric_and_thermal_grid_planning.optimization_generation import generate_main
from cea.optimization.flexibility_model.electric_and_thermal_grid_planning.thermal_network_calculations import \
    thermal_network_calculations

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Thanh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

# create fitness function for minimization
creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
creator.create("Individual", list, typecode='d', fitness=creator.FitnessMin)
config = cea.config.Configuration()
# the optimization will start from the same set of individuals if random_seed is specified
random.seed(config.electrical_thermal_optimization.random_seed)
np.random.seed(config.electrical_thermal_optimization.random_seed)


def objective_function(individual, individual_number, locator, config, building_names, generation):
    """
    Objective function is used to calculate the costs, CO2, primary energy and the variables corresponding to the
    individual
    :param individual: Input individual
    :type individual: list
    :return: returns costs, CO2, primary energy and the master_to_slave_vars
    """
    print ('cea optimization progress: individual ' + str(individual_number))

    # run optimization for electric network (all buildings connected)
    m, dict_connected = electric_network_optimization(locator, building_names, config, generation, individual,
                                                      network_number=individual_number)

    total_annual_cost, total_annual_capex, total_annual_opex = thermal_network_calculations(m, dict_connected, locator,
                                                                                            individual, config,
                                                                                            individual_number,
                                                                                            building_names, generation)
    return total_annual_capex, total_annual_opex


def objective_function_wrapper(args):
    """
    Wrap arguments because multiprocessing only accepts one argument for the function"""
    return objective_function(*args)


def non_dominated_sorting_genetic_algorithm(locator, building_names, config):
    t0 = time.clock()

    genCP = config.electrical_thermal_optimization.recoverycheckpoint
    CXPB = config.electrical_thermal_optimization.crossoverprobability
    MUTPB = config.electrical_thermal_optimization.mutationprobability

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

    toolbox.register("generate", generate_main, nBuildings)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.generate)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", objective_function_wrapper)
    toolbox.register("select", tools.selNSGA2) # default function from deap toolbox
    toolbox.register("mate", tools.cxTwoPoint) # default function from deap toolbox
    toolbox.register("mutate", tools.mutFlipBit, indpb=0.05) # default function from deap toolbox

    # Initialization of variables
    DHN_network_list = ["1" * nBuildings]
    DCN_network_list = ["1" * nBuildings]
    halloffame = []
    halloffame_fitness = []
    epsInd = []

    columns_of_saved_files = ['generation', 'individual']

    # for i in building_names: #DHN
    #     columns_of_saved_files.append(str(i) + ' DHN')

    for i in building_names:  # DCN
        columns_of_saved_files.append(str(i) + ' DCN')

    columns_of_saved_files.append('CAPEX Total')
    columns_of_saved_files.append('OPEX Total')

    # gathers some stats for future analysis
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    # stats.register("avg", numpy.mean, axis=0)
    # stats.register("std", numpy.std, axis=0)
    stats.register("min", np.min, axis=0)
    stats.register("max", np.max, axis=0)

    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "std", "min", "avg", "max"

    if genCP is 0:

        pop = toolbox.population(n=config.optimization.initialind)

        # Evaluate the initial population
        print "Evaluate initial population"
        DHN_network_list = DHN_network_list[
                           1:]  # done this to remove the first individual in the ntwList as it is an initial value
        DCN_network_list = DCN_network_list[1:]

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in pop if not ind.fitness.valid]

        fitnesses = toolbox.map(toolbox.evaluate,
                                izip(invalid_ind, range(len(invalid_ind)),
                                     repeat(locator, len(invalid_ind)),
                                     repeat(config, len(invalid_ind)), repeat(building_names, len(invalid_ind)),
                                     repeat(genCP, len(invalid_ind))))

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

        zero_data = np.zeros(shape=(len(invalid_ind), len(columns_of_saved_files)))
        saved_dataframe_for_each_generation = pd.DataFrame(zero_data, columns=columns_of_saved_files)

        for i, ind in enumerate(invalid_ind):
            saved_dataframe_for_each_generation['individual'][i] = i
            saved_dataframe_for_each_generation['generation'][i] = genCP
            for j in range(len(columns_of_saved_files) - 4):
                saved_dataframe_for_each_generation[columns_of_saved_files[j + 2]][i] = ind[j]
            saved_dataframe_for_each_generation['CAPEX Total'][i] = ind.fitness.values[0]
            saved_dataframe_for_each_generation['OPEX Total'][i] = ind.fitness.values[1]

        saved_dataframe_for_each_generation.to_csv(
            locator.get_electrical_and_thermal_network_optimization_individuals_in_generation(genCP))

        with open(locator.get_electrical_and_thermal_network_optimization_checkpoint_initial(), "wb") as fp:
            cp = dict(nsga_selected_population=pop, generation=0, DHN_List=DHN_network_list, DCN_list=DCN_network_list,
                      tested_population=[],
                      tested_population_fitness=fitnesses, halloffame=halloffame, halloffame_fitness=halloffame_fitness)
            json.dump(cp, fp)

    else:
        print "Recover from CP " + str(genCP) + "\n"
        # import the checkpoint based on the genCP
        with open(locator.get_electrical_and_thermal_network_optimization_checkpoint(genCP), "rb") as fp:
            cp = json.load(fp)
            pop = toolbox.population(n=config.optimization.initialind)
            for i in xrange(len(pop)):
                for j in xrange(len(pop[i])):
                    pop[i][j] = cp['population'][i][j]
            DHN_network_list = DHN_network_list
            DCN_network_list = DCN_network_list
            epsInd = cp["epsIndicator"]

            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in pop if not ind.fitness.valid]

            fitnesses = toolbox.map(toolbox.evaluate,
                                    izip(invalid_ind, range(len(invalid_ind)),
                                         repeat(locator, len(invalid_ind)),
                                         repeat(config, len(invalid_ind)), repeat(building_names, len(invalid_ind)),
                                         repeat(genCP, len(invalid_ind))))

            function_evals = function_evals + len(invalid_ind)  # keeping track of number of function evaluations
            # linking every individual with the corresponding fitness, this also keeps a track of the number of function
            # evaluations. This can further be used as a stopping criteria in future
            for ind, fit in zip(pop, fitnesses):
                ind.fitness.values = fit

            pop = toolbox.select(pop, len(pop))  # assigning crowding distance

    # Evolution starts !

    g = genCP
    stopCrit = False  # Threshold for the Epsilon indicator, Not used

    while g < config.optimization.ngen and not stopCrit and (time.clock() - t0) < config.optimization.maxtime:

        # Initialization of variables
        DHN_network_list = ["1" * nBuildings]

        g += 1
        print "Generation", g
        offspring = list(pop)
        # Apply crossover and mutation on the pop
        for ind1, ind2 in zip(pop[::2], pop[1::2]):
            if random.random() < CXPB:
                child1, child2 = toolbox.mate(ind1, ind2)
                del child1.fitness.values
                del child2.fitness.values
                offspring += [child1, child2]

        for mutant in pop:
            if random.random() < MUTPB:
                toolbox.mutate(mutant)
                del mutant.fitness.values
                offspring += [mutant]

        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]

        # Evaluate the individuals with an invalid fitness
        fitnesses = toolbox.map(toolbox.evaluate,
                                izip(invalid_ind, range(len(invalid_ind)),
                                     repeat(locator, len(invalid_ind)),
                                     repeat(config, len(invalid_ind)), repeat(building_names, len(invalid_ind)),
                                     repeat(genCP, len(invalid_ind))))

        function_evals = function_evals + len(invalid_ind)  # keeping track of number of function evaluations
        # linking every individual with the corresponding fitness, this also keeps a track of the number of function
        # evaluations. This can further be used as a stopping criteria in future
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        zero_data = np.zeros(shape=(len(invalid_ind), len(columns_of_saved_files)))
        saved_dataframe_for_each_generation = pd.DataFrame(zero_data, columns=columns_of_saved_files)

        for i, ind in enumerate(invalid_ind):
            saved_dataframe_for_each_generation['individual'][i] = i
            saved_dataframe_for_each_generation['generation'][i] = g
            saved_dataframe_for_each_generation['CAPEX Total'][i] = ind.fitness.values[0]
            saved_dataframe_for_each_generation['OPEX Total'][i] = ind.fitness.values[1]

        saved_dataframe_for_each_generation.to_csv(
            locator.get_electrical_and_thermal_network_optimization_individuals_in_generation(g))

        selection = toolbox.select(pop + invalid_ind, config.optimization.initialind)  # assigning crowding distance

        if len(halloffame) <= halloffame_size:
            halloffame.extend(selection)
        else:
            halloffame.extend(selection)
            halloffame = toolbox.select(halloffame, halloffame_size)

        halloffame_fitness = []
        for ind in halloffame:
            halloffame_fitness.append(ind.fitness.values)

        pop[:] = selection

        # Create Checkpoint if necessary
        if g % config.optimization.fcheckpoint == 0:
            print "Create CheckPoint", g, "\n"
            with open(locator.get_electrical_and_thermal_network_optimization_checkpoint(g), "wb") as fp:
                cp = dict(nsga_selected_population=pop, generation=g, DHN_List=DHN_network_list,
                          DCN_list=DCN_network_list,
                          tested_population=invalid_ind, tested_population_fitness=fitnesses, epsIndicator=epsInd,
                          halloffame=halloffame, halloffame_fitness=halloffame_fitness)
                json.dump(cp, fp)

    if g == config.optimization.ngen:
        print "Final Generation reached"
    else:
        print "Stopping criteria reached"

    # Dataframe with all the individuals whose objective functions are calculated, gathering all the results from
    # multiple generations
    df = pd.read_csv(locator.get_electrical_and_thermal_network_optimization_individuals_in_generation(0))
    for i in range(config.optimization.ngen):
        df = df.append(
            pd.read_csv(locator.get_electrical_and_thermal_network_optimization_individuals_in_generation(i + 1)))
    df.to_csv(locator.get_electrical_and_thermal_network_optimization_all_individuals())
    # Saving the final results
    print "Save final results. " + str(len(pop)) + " individuals in final population"
    with open(locator.get_electrical_and_thermal_network_optimization_checkpoint_final(), "wb") as fp:
        cp = dict(nsga_selected_population=pop, generation=g, DHN_List=DHN_network_list, DCN_list=DCN_network_list,
                  tested_population=invalid_ind, tested_population_fitness=fitnesses, epsIndicator=epsInd,
                  halloffame=halloffame, halloffame_fitness=halloffame_fitness)
        json.dump(cp, fp)

    print "Master Work Complete \n"
    print ("Number of function evaluations = " + str(function_evals))
    t1 = time.clock()
    print (t1 - t0)

    return pop, logbook


def main(config):
    t0 = time.clock()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values

    non_dominated_sorting_genetic_algorithm(locator, building_names, config)
    print 'main() succeeded'
    print 'total time: ', time.clock() - t0


if __name__ == '__main__':
    main(cea.config.Configuration())

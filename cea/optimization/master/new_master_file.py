from __future__ import division

from cea.optimization.constants import PROBA, SIGMAP, GHP_HMAX_SIZE, N_HR, N_HEAT, N_PV, N_PVT
import cea.optimization.master.crossover as cx
import cea.optimization.master.mutations as mut
import cea.optimization.master.selection as sel
import cea.optimization.supportFn as sFn
import cea.config
import cea.globalvar
import cea.inputlocator
from cea.optimization.prices import Prices as Prices
import cea.optimization.distribution.network_opt_main as network_opt
from cea.optimization.preprocessing.preprocessing_main import preproccessing
from cea.optimization.lca_calculations import lca_calculations
import json
import cea
import pandas as pd
import multiprocessing
import time
import numpy as np
from deap import base
from deap import benchmarks
from deap.benchmarks.tools import diversity, convergence, hypervolume
from deap import creator
from deap import tools
from cea.optimization.master.generation import generate_main
import cea.optimization.master.evaluation as evaluation

__author__ =  "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0, -1.0))
creator.create("Individual", list, typecode='d', fitness=creator.FitnessMin)

def objective_function(generation, building_names, locator, solar_features, network_features, gv, config, prices, lca, individual_list):
    """
    Objective function is used to calculate the costs, CO2, primary energy and the variables corresponding to the
    individual
    :param individual: Input individual
    :type individual: list
    :return: returns costs, CO2, primary energy and the master_to_slave_vars
    """
    individual_number = individual_list[-1]
    individual = individual_list[:-1]
    print ('cea optimization progress: individual ' + str(individual_number) + ' and generation ' + str(
        generation) + '/' + str(config.optimization.ngen))
    costs, CO2, prim, master_to_slave_vars, valid_individual = evaluation.evaluation_main(individual, building_names,
                                                                                          locator, solar_features,
                                                                                          network_features, gv, config,
                                                                                          prices, lca,
                                                                                          individual_number, generation)
    return costs, CO2, prim

def objective_function_1(individual):
    """
    Objective function is used to calculate the costs, CO2, primary energy and the variables corresponding to the
    individual
    :param individual: Input individual
    :type individual: list
    :return: returns costs, CO2, primary energy and the master_to_slave_vars
    """
    individual_number = 1
    print (individual)

def new_master_main(locator, building_names, extra_costs, extra_CO2, extra_primary_energy, solar_features,
                                  network_features, gv, config, prices, lca):

    t0 = time.clock()

    np.random.seed(config.optimization.random_seed)
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
    toolbox.register("evaluate", objective_function, genCP, building_names, locator, solar_features, network_features, gv, config, prices, lca)
    toolbox.register("select", tools.selNSGA2)


    if config.multiprocessing:
        pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
        toolbox.register("map", pool.map)

    # Initialization of variables
    DHN_network_list = ["1"*nBuildings]
    DCN_network_list = ["1"*nBuildings]
    halloffame = []
    halloffame_fitness = []


    columns_of_saved_files = ['generation', 'individual', 'CHP/Furnace', 'CHP/Furnace Share', 'Base Boiler', 'Base Boiler Share', 'Peak Boiler', 'Peak Boiler Share',
               'Heating Lake', 'Heating Lake Share', 'Heating Sewage', 'Heating Sewage Share', 'GHP', 'GHP Share',
               'Data Centre', 'Compressed Air', 'PV', 'PV Area Share', 'PVT', 'PVT Area Share', 'SC_ET', 'SC_ET Area Share',
               'SC_FP', 'SC_FP Area Share', 'DHN Temperature', 'DHN unit configuration', 'Lake Cooling', 'Lake Cooling Share', 'VCC Cooling', 'VCC Cooling Share',
               'Absorption Chiller', 'Absorption Chiller Share', 'Storage', 'Storage Share', 'DCN Temperature', 'DCN unit configuration']
    for i in building_names: #DHN
        columns_of_saved_files.append(str(i) + ' DHN')

    for i in building_names: #DCN
        columns_of_saved_files.append(str(i) + ' DCN')

    columns_of_saved_files.append('TAC')
    columns_of_saved_files.append('CO2 emissions')
    columns_of_saved_files.append('Primary Energy')

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    # stats.register("avg", numpy.mean, axis=0)
    # stats.register("std", numpy.std, axis=0)
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
        for i in range(len(invalid_ind)):
            invalid_ind[i].append(i)

        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        function_evals = function_evals + len(invalid_ind)   # keeping track of number of function evaluations
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

        with open(locator.get_optimization_checkpoint_initial(),"wb") as fp:
            cp = dict(population=pop, generation=0, networkList=DHN_network_list, epsIndicator=[], testedPop=[],
                      population_fitness=fitnesses, halloffame=halloffame, halloffame_fitness=halloffame_fitness)
            json.dump(cp, fp)

    else:
        print "Recover from CP " + str(genCP) + "\n"
        # import the checkpoint based on the genCP
        with open(locator.get_optimization_checkpoint(genCP), "rb") as fp:
            cp = json.load(fp)
            pop = toolbox.population(n=config.optimization.initialind)
            for i in xrange(len(pop)):
                for j in xrange(len(pop[i])):
                    pop[i][j] = cp['population'][i][j]
            DHN_network_list = DHN_network_list
            DCN_network_list = DCN_network_list
            epsInd = cp["epsIndicator"]

            for ind in pop:
                evaluation.checkNtw(ind, DHN_network_list, DCN_network_list, locator, gv, config, building_names)

            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in pop if not ind.fitness.valid]
            for i in range(len(invalid_ind)):
                invalid_ind[i].append(i)

            fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)

            # linking every individual with the corresponding fitness, this also keeps a track of the number of function
            # evaluations. This can further be used as a stopping criteria in future
            for ind, fit in zip(pop, fitnesses):
                ind.fitness.values = fit

            pop = toolbox.select(pop, len(pop))  # assigning crowding distance

    proba, sigmap = PROBA, SIGMAP

    # Evolution starts !

    g = genCP
    stopCrit = False # Threshold for the Epsilon indicator, Not used

    while g < config.optimization.ngen and not stopCrit and (time.clock() - t0) < config.optimization.maxtime:

        # Initialization of variables
        DHN_network_list = ["1" * nBuildings]

        g += 1
        print "Generation", g
        offspring = list(pop)
        # Apply crossover and mutation on the pop
        for ind1, ind2 in zip(pop[::2], pop[1::2]):
            child1, child2 = cx.cxUniform(ind1, ind2, proba, nBuildings)
            offspring += [child1, child2]

        for mutant in pop:
            mutant = mut.mutFlip(mutant, proba, nBuildings)
            mutant = mut.mutShuffle(mutant, proba, nBuildings)
            offspring.append(mut.mutGU(mutant, proba))

        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]

        for ind in invalid_ind:
            evaluation.checkNtw(ind, DHN_network_list, DCN_network_list, locator, gv, config, building_names)

        # Evaluate the individuals with an invalid fitness
        for i in range(len(invalid_ind)):
            invalid_ind[i].append(i)

        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        # linking every individual with the corresponding fitness, this also keeps a track of the number of function
        # evaluations. This can further be used as a stopping criteria in future
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit

        pop = toolbox.select(pop + invalid_ind, config.optimization.initialind) # assigning crowding distance




    print ("done")
    t1 = time.clock()
    print (t1-t0)

    return pop, logbook


if __name__ == "__main__":
    config = cea.config.Configuration()
    gv = cea.globalvar.GlobalVariables()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    weather_file = config.weather
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    gv.num_tot_buildings = total_demand.Name.count()
    lca = lca_calculations(locator, config)
    prices = Prices(locator, config)
    extra_costs, extra_CO2, extra_primary_energy, solar_features = preproccessing(locator, total_demand, building_names,
                                                                             weather_file, gv, config,
                                                                             prices, lca)

    # optimize the distribution and linearize the results(at the moment, there is only a linearization of values in Zug)
    print "NETWORK OPTIMIZATION"
    nBuildings = len(building_names)


    network_features = network_opt.network_opt_main(config, locator)


    new_master_main(locator, building_names, extra_costs, extra_CO2, extra_primary_energy, solar_features,
                                  network_features, gv, config, prices, lca)

from __future__ import division
import os
import pandas as pd
import cea.config
import cea.globalvar
import cea.inputlocator
from cea.optimization.prices import Prices as Prices
import cea.optimization.distribution.network_opt_main as network_opt
import cea.optimization.master.master_main as master
from cea.optimization.preprocessing.preprocessing_main import preproccessing
from cea.optimization.lca_calculations import lca_calculations
import array
import random
import json
import cea
import pandas as pd
import multiprocessing
import time
from scoop import futures

import numpy as np

from math import sqrt

from deap import algorithms
from deap import base
from deap import benchmarks
from deap.benchmarks.tools import diversity, convergence, hypervolume
from deap import creator
from deap import tools
from cea.optimization.master.generation import generate_main
import cea.optimization.master.evaluation as evaluation

creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0, -1.0))
creator.create("Individual", array.array, typecode='d', fitness=creator.FitnessMin)

def objective_function(generation, building_names, locator, solar_features, network_features, gv, config, prices, lca, individual_tuple):
    """
    Objective function is used to calculate the costs, CO2, primary energy and the variables corresponding to the
    individual
    :param individual: Input individual
    :type individual: list
    :return: returns costs, CO2, primary energy and the master_to_slave_vars
    """
    individual = individual_tuple[0]
    individual_number = individual_tuple[1]
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
    np.random.seed(config.optimization.random_seed)
    gv = cea.globalvar.GlobalVariables()

    total_demand = pd.read_csv(locator.get_total_demand())
    gv.num_tot_buildings = total_demand.Name.count()
    lca = lca_calculations(locator, config)
    prices = Prices(locator, config)

    t0 = time.clock()
    genCP = config.optimization.recoverycheckpoint

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
    genCP = config.optimization.recoverycheckpoint

    toolbox.register("generate", generate_main, nBuildings, config)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.generate)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", objective_function, genCP, building_names, locator, solar_features, network_features, gv, config, prices, lca)
    toolbox.register("select", tools.selNSGA2)



    # Problem definition
    # Functions zdt1, zdt2, zdt3, zdt6 have bounds [0, 1]
    BOUND_LOW, BOUND_UP = 0.0, 1.0

    # Functions zdt4 has bounds x1 = [0, 1], xn = [-5, 5], with n = 2, ..., 10
    # BOUND_LOW, BOUND_UP = [0.0] + [-5.0]*9, [1.0] + [5.0]*9

    # Functions zdt1, zdt2, zdt3 have 30 dimensions, zdt4 and zdt6 have 10
    NDIM = 30
    genCP = 0
    MU = 5

    # Initialization of variables
    DHN_network_list = ["1"*nBuildings]
    DCN_network_list = ["1"*nBuildings]
    epsInd = []
    invalid_ind = []
    halloffame = []
    halloffame_fitness = []
    costs_list = []
    co2_list = []
    prim_list = []
    valid_pop = []
    slavedata_list = []
    fitnesses = []
    capacities = []
    disconnected_capacities = []
    Furnace_wet = 0
    Furnace_wet_capacity_W = 0
    Furnace_dry = 0
    Furnace_dry_capacity_W = 0
    CHP_NG = 0
    CHP_NG_capacity_W = 0
    CHP_BG = 0
    CHP_BG_capacity_W = 0
    Base_boiler_BG = 0
    Base_boiler_BG_capacity_W = 0
    Base_boiler_NG = 0
    Base_boiler_NG_capacity_W = 0
    Peak_boiler_BG = 0
    Peak_boiler_BG_capacity_W = 0
    Peak_boiler_NG = 0
    Peak_boiler_NG_capacity_W = 0
    cooling_all_units = 'AHU_ARU_SCU'
    heating_all_units = 'AHU_ARU_SHU'

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

    pool = multiprocessing.Pool(processes=5)
    # # toolbox.register("map", futures.map)
    toolbox.register("map", pool.map)


    t0 = time.clock()

    pop = toolbox.population(n=MU)

    for ind in pop:
        evaluation.checkNtw(ind, DHN_network_list, DCN_network_list, locator, gv, config, building_names)

    # Evaluate the initial population
    print "Evaluate initial population"
    DHN_network_list = DHN_network_list[
                       1:]  # done this to remove the first individual in the ntwList as it is an initial value
    DCN_network_list = DCN_network_list[1:]

    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in pop if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, (invalid_ind, range(len(invalid_ind))))
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    print ("done")

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

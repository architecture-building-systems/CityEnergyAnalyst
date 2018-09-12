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

import numpy

from math import sqrt

from deap import algorithms
from deap import base
from deap import benchmarks
from deap.benchmarks.tools import diversity, convergence, hypervolume
from deap import creator
from deap import tools
from cea.optimization.master.generation import generate_main
import cea.optimization.master.evaluation as evaluation


def objective_function( generation, building_names, locator, solar_features, network_features, gv, config, prices, lca, individual_number, individual):
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

def main(config):
    random.seed(config.optimization.random_seed)
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    gv = cea.globalvar.GlobalVariables()

    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    nBuildings = len(building_names)
    gv.num_tot_buildings = total_demand.Name.count()
    lca = lca_calculations(locator, config)
    prices = Prices(locator, config)
    weather_file = config.weather


    # pre-process information regarding resources and technologies (they are treated before the optimization)
    # optimize best systems for every individual building (they will compete against a district distribution solution)
    print "PRE-PROCESSING"
    extra_costs, extra_CO2, extra_primary_energy, solar_features = preproccessing(locator, total_demand, building_names,
                                                                             weather_file, gv, config,
                                                                             prices, lca)

    # optimize the distribution and linearize the results(at the moment, there is only a linearization of values in Zug)
    print "NETWORK OPTIMIZATION"
    network_features = network_opt.network_opt_main(config, locator)


    creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0, -1.0))
    creator.create("Individual", array.array, typecode='d', fitness=creator.FitnessMin)

    toolbox = base.Toolbox()

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


    toolbox.register("generate", generate_main, nBuildings, config)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.generate)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register("evaluate", objective_function, genCP, building_names, locator, solar_features, network_features, gv, config, prices, lca)
    toolbox.register("mate", tools.cxSimulatedBinaryBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0)
    toolbox.register("mutate", tools.mutPolynomialBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0, indpb=1.0 / NDIM)
    toolbox.register("select", tools.selNSGA2)


    stats = tools.Statistics(lambda ind: ind.fitness.values)
    # stats.register("avg", numpy.mean, axis=0)
    # stats.register("std", numpy.std, axis=0)
    stats.register("min", numpy.min, axis=0)
    stats.register("max", numpy.max, axis=0)

    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "std", "min", "avg", "max"

    pool = multiprocessing.Pool(processes=5)
    toolbox.register("map", pool.map)

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
    individual_numbers = range(len(invalid_ind))
    fitnesses = toolbox.map(toolbox.evaluate, individual_numbers, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    pool.close()
    # This is just to assign the crowding distance to the individuals
    # no actual selection is done
    pop = toolbox.select(pop, len(pop))

    record = stats.compile(pop)
    logbook.record(gen=0, evals=len(invalid_ind), **record)
    print(logbook.stream)

    # Begin the generational process
    for gen in range(1, NGEN):
        # Vary the population
        offspring = tools.selTournamentDCD(pop, len(pop))
        offspring = [toolbox.clone(ind) for ind in offspring]

        for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
            if random.random() <= CXPB:
                toolbox.mate(ind1, ind2)

            toolbox.mutate(ind1)
            toolbox.mutate(ind2)
            del ind1.fitness.values, ind2.fitness.values

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # Select the next generation population
        pop = toolbox.select(pop + offspring, MU)
        record = stats.compile(pop)
        logbook.record(gen=gen, evals=len(invalid_ind), **record)
        print(logbook.stream)

    print("Final population hypervolume is %f" % hypervolume(pop, [11.0, 11.0]))

    return pop, logbook


if __name__ == "__main__":
    main(cea.config.Configuration())

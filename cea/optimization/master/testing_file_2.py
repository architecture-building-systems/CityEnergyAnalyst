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
import cea.technologies.solar.solar_collector as solar_collector
import time
import json
from cea.optimization.constants import PROBA, SIGMAP, GHP_HMAX_SIZE, N_HR, N_HEAT, N_PV, N_PVT
import cea.optimization.master.crossover as cx
import cea.optimization.master.evaluation as evaluation
import random
from deap import base
from deap import creator
from deap import tools
import cea.optimization.master.generation as generation
import cea.optimization.master.mutations as mut
import cea.optimization.master.selection as sel
import numpy as np
import pandas as pd
import cea.optimization.supportFn as sFn
import itertools
import multiprocessing

def objective_function_trial(big_tuple):
    """
    Objective function is used to calculate the costs, CO2, primary energy and the variables corresponding to the
    individual
    :param individual: Input individual
    :type individual: list
    :return: returns costs, CO2, primary energy and the master_to_slave_vars
    """

    individual_number = big_tuple[0]
    individual = big_tuple[1]
    generation = big_tuple[2]
    building_names = big_tuple[3]
    locator = big_tuple[4]
    solar_features = big_tuple[5]
    network_features = big_tuple[6]
    gv = big_tuple[7]
    config = big_tuple[8]
    prices = big_tuple[9]
    lca = big_tuple[10]

    print ('cea optimization progress: individual ' + str(individual_number) + ' and generation ' + str(
        generation) + '/' + str(config.optimization.ngen))
    costs, CO2, prim, master_to_slave_vars, valid_individual = evaluation.evaluation_main(individual, building_names,
                                                                                          locator, solar_features,
                                                                                          network_features, gv, config,
                                                                                          prices, lca,
                                                                                          individual_number, generation)
    return costs, CO2, prim, master_to_slave_vars, valid_individual


def main():
    config = cea.config.Configuration()
    gv = cea.globalvar.GlobalVariables()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    weather_file = config.weather

    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    gv.num_tot_buildings = total_demand.Name.count()
    lca = lca_calculations(locator, config)
    prices = Prices(locator, config)

    # pre-process information regarding resources and technologies (they are treated before the optimization)
    # optimize best systems for every individual building (they will compete against a district distribution solution)
    print "PRE-PROCESSING"
    extra_costs, extra_CO2, extra_primary_energy, solar_features = preproccessing(locator, total_demand, building_names,
                                                                                  weather_file, gv, config,
                                                                                  prices, lca)

    # optimize the distribution and linearize the results(at the moment, there is only a linearization of values in Zug)
    print "NETWORK OPTIMIZATION"
    network_features = network_opt.network_opt_main(config, locator)



    t0 = time.clock()
    genCP = config.optimization.recoverycheckpoint

    # initiating hall of fame size and the function evaluations
    halloffame_size = config.optimization.halloffame
    function_evals = 0
    euclidean_distance = 0
    spread = 0
    random.seed(config.optimization.random_seed)
    np.random.seed(config.optimization.random_seed)

    # get number of buildings
    nBuildings = len(building_names)
    # SET-UP EVOLUTIONARY ALGORITHM
    # Contains 3 minimization objectives : Costs, CO2 emissions, Primary Energy Needs
    # this part of the script sets up the optimization algorithm in the same syntax of DEAP toolbox
    creator.create("Fitness", base.Fitness,
                   weights=(-1.0, -1.0, -1.0))  # weights of -1 for minimization, +1 for maximization
    creator.create("Individual", list, fitness=creator.Fitness)
    toolbox = base.Toolbox()
    toolbox.register("generate", generation.generate_main, nBuildings, config)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.generate)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # Initialization of variables
    DHN_network_list = ["1" * nBuildings]
    DCN_network_list = ["1" * nBuildings]
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

    columns_of_saved_files = ['generation', 'individual', 'CHP/Furnace', 'CHP/Furnace Share', 'Base Boiler',
                              'Base Boiler Share', 'Peak Boiler', 'Peak Boiler Share',
                              'Heating Lake', 'Heating Lake Share', 'Heating Sewage', 'Heating Sewage Share', 'GHP',
                              'GHP Share',
                              'Data Centre', 'Compressed Air', 'PV', 'PV Area Share', 'PVT', 'PVT Area Share', 'SC_ET',
                              'SC_ET Area Share',
                              'SC_FP', 'SC_FP Area Share', 'DHN Temperature', 'DHN unit configuration', 'Lake Cooling',
                              'Lake Cooling Share', 'VCC Cooling', 'VCC Cooling Share',
                              'Absorption Chiller', 'Absorption Chiller Share', 'Storage', 'Storage Share',
                              'DCN Temperature', 'DCN unit configuration']
    for i in building_names:  # DHN
        columns_of_saved_files.append(str(i) + ' DHN')

    for i in building_names:  # DCN
        columns_of_saved_files.append(str(i) + ' DCN')

    columns_of_saved_files.append('TAC')
    columns_of_saved_files.append('CO2 emissions')
    columns_of_saved_files.append('Primary Energy')
    pop = toolbox.population(n=config.optimization.initialind)

    # Check the network and update ntwList. ntwList size keeps changing as the following loop runs
    for ind in pop:
        evaluation.checkNtw(ind, DHN_network_list, DCN_network_list, locator, gv, config, building_names)

    # Evaluate the initial population
    print "Evaluate initial population"
    DHN_network_list = DHN_network_list[
                       1:]  # done this to remove the first individual in the ntwList as it is an initial value
    DCN_network_list = DCN_network_list[
                       1:]  # done this to remove the first individual in the ntwList as it is an initial value
    # costs_list updates the costs involved in every individual
    # co2_list updates the GHG emissions in terms of CO2
    # prim_list updates the primary energy  corresponding to every individual
    # slavedata_list updates the master_to_slave variables corresponding to every individual. This is used in
    # calculating the capacities of both the centralized and the decentralized system


    t0 = time.clock()
    # pool = multiprocessing.Pool(3)
    print ('multiprocessing started')
    multi_processing_input = []

    for i in range(len(pop)):
        multi_processing_input.append([i, pop[i], genCP, building_names, locator, solar_features, network_features, gv, config, prices, lca])

    objective_function_trial(multi_processing_input[0])
    objective_function_trial(multi_processing_input[1])
    objective_function_trial(multi_processing_input[2])

    pool = multiprocessing.Pool(5)
    joblist = []
    for ind in multi_processing_input:
        print (ind)
        job = pool.apply_async(objective_function_trial, ind)
        joblist.append(job)
    for i, job in enumerate(joblist):
        job.get(240)
        print('Building No. %i completed out of %i' % (i + 1))
    pool.close()

if __name__ == '__main__':
    main()
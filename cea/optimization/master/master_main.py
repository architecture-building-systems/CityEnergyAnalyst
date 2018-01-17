"""
===========================
Evolutionary algorithm main
===========================

"""
from __future__ import division

import time
import json
from cea.optimization.constants import *
import cea.optimization.master.crossover as cx
import cea.optimization.master.evaluation as evaluation
from deap import base
from deap import creator
from deap import tools
import cea.optimization.master.generation as generation
import mutations as mut
import selection as sel
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.cm as cmx
import os
import numpy as np


__author__ =  "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Sreepathi Bhargava Krishna", "Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def evolutionary_algo_main(locator, building_names, extra_costs, extra_CO2, extra_primary_energy, solar_features,
                           network_features, gv, config, prices, genCP=00):
    """
    Evolutionary algorithm to optimize the district energy system's design.
    This algorithm optimizes the size and operation of technologies for a district heating network.
    electrical network are not considered but their burdens in terms electricity costs, efficiency and emissions
    is added on top of the optimization.
    The equipment for cooling networks is not optimized as it is assumed that all customers with cooling needs will be
    connected to a lake. in case there is not enough capacity from the lake, a chiller and cooling tower is used to
    cover the extra needs.

    :param locator: locator class
    :param building_names: vector with building names
    :param extra_costs: costs calculated before optimization of specific energy services
     (process heat and electricity)
    :param extra_CO2: green house gas emissions calculated before optimization of specific energy services
     (process heat and electricity)
    :param extra_primary_energy: primary energy calculated before optimization of specific energy services
     (process heat and electricity)
    :param solar_features: object class with vectors and values of interest for the integration of solar potentials
    :param network_features: object class with linear coefficients of the network obtained after its optimization
    :param gv: global variables class
    :param genCP: 0
    :type locator: class
    :type building_names: array
    :type extra_costs: float
    :type extra_CO2: float
    :type extra_primary_energy: float
    :type solar_features: class
    :type network_features: class
    :type gv: class
    :type genCP: int
    :return: for every generation 'g': it stores the results of every generation of the genetic algorithm in the
     subfolders locator.get_optimization_master_results_folder() as a python pickle file.
    :rtype: pickled file
    """
    t0 = time.clock()

    # initiating hall of fame size and the function evaluations
    halloffame_size = 100
    function_evals = 0
    euclidean_distance = 0
    spread = 0

    # get number of buildings
    nBuildings = len(building_names)

    # DEFINE OBJECTIVE FUNCTION
    def objective_function(ind):
        (costs, CO2, prim) = evaluation.evaluation_main(ind, building_names, locator, extra_costs, extra_CO2, extra_primary_energy, solar_features,
                                                        network_features, gv, config, prices)
        return (costs, CO2, prim)

    # SET-UP EVOLUTIONARY ALGORITHM
    # Contains 3 minimization objectives : Costs, CO2 emissions, Primary Energy Needs
    creator.create("Fitness", base.Fitness, weights=(-1.0, -1.0, -1.0))
    creator.create("Individual", list, fitness=creator.Fitness)
    toolbox = base.Toolbox()
    toolbox.register("generate", generation.generate_main, nBuildings)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.generate)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", objective_function)

    ntwList = ["1"*nBuildings]
    epsInd = []
    invalid_ind = []
    halloffame = []
    halloffame_fitness = []
    # Evolutionary strategy
    if genCP is 0:
        # create population
        pop = toolbox.population(n=config.optimization.initialind)

        # Check distribution
        for ind in pop:
            evaluation.checkNtw(ind, ntwList, locator, gv, config)

        # Evaluate the initial population
        print "Evaluate initial population"
        fitnesses = map(toolbox.evaluate, pop)

        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit
            function_evals = function_evals + 1  # keeping track of number of function evaluations

        # Save initial population
        print "Save Initial population \n"

        with open(locator.get_optimization_checkpoint_initial(),"wb") as fp:
            cp = dict(population=pop, generation=0, networkList=ntwList, epsIndicator=[], testedPop=[], population_fitness=fitnesses)
            json.dump(cp, fp)

    else:
        print "Recover from CP " + str(genCP) + "\n"

        with open(locator.get_optimization_checkpoint(genCP), "rb") as fp:
            cp = json.load(fp)
            pop = toolbox.population(n=config.optimization.initialind)
            for i in xrange(len(pop)):
                for j in xrange(len(pop[i])):
                    pop[i][j] = cp['population'][i][j]
            ntwList = ntwList
            epsInd = cp["epsIndicator"]

            for ind in pop:
                evaluation.checkNtw(ind, ntwList, locator, gv, config)
            fitnesses = cp['population_fitness']
            for ind, fit in zip(pop, fitnesses):
                ind.fitness.values = fit
                function_evals = function_evals + 1  # keeping track of number of function evaluations

    proba, sigmap = PROBA, SIGMAP

    xs = [((objectives[0])) for objectives in fitnesses]  # Costs
    ys = [((objectives[1])) for objectives in fitnesses]  # GHG emissions
    zs = [((objectives[2])) for objectives in fitnesses]  # MJ

    normalization = [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)]

    xs = [a / 10**6 for a in xs]
    ys = [a / 10**6 for a in ys]
    zs = [a / 10**6 for a in zs]
    # plot showing the Pareto front of every generation
    fig = plt.figure()
    ax = fig.add_subplot(111)
    cm = plt.get_cmap('jet')
    cNorm = matplotlib.colors.Normalize(vmin=min(zs), vmax=max(zs))
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)
    ax.scatter(xs, ys, c=scalarMap.to_rgba(zs), s=50, alpha=0.8)
    ax.set_xlabel('TAC [$ Mio/yr]')
    ax.set_ylabel('GHG emissions [x 10^3 ton CO2-eq]')
    scalarMap.set_array(zs)
    fig.colorbar(scalarMap, label='Primary Energy [x 10^3 GJ]')
    plt.grid(True)
    plt.rcParams['figure.figsize'] = (20, 10)
    plt.rcParams.update({'font.size': 12})
    plt.gcf().subplots_adjust(bottom=0.15)
    plt.savefig(os.path.join(locator.get_optimization_plots_folder(), "pareto_" + str(genCP) + ".png"))
    plt.clf()

    # Evolution starts !

    g = genCP
    stopCrit = False # Threshold for the Epsilon indicator, Not used

    while g < config.optimization.ngen and not stopCrit and ( time.clock() - t0 ) < config.optimization.maxtime :

        g += 1
        print "Generation", g
        offspring = list(pop)

        # Apply crossover and mutation on the pop
        for ind1, ind2 in zip(pop[::2], pop[1::2]):
            child1, child2 = cx.cxUniform(ind1, ind2, proba)
            offspring += [child1, child2]

        for mutant in pop:
            mutant = mut.mutFlip(mutant, proba)
            mutant = mut.mutShuffle(mutant, proba)
            offspring.append(mut.mutGU(mutant, proba))

        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        for ind in invalid_ind:
            evaluation.checkNtw(ind, ntwList, locator, gv, config)

        fitnesses = map(toolbox.evaluate, invalid_ind)

        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
            function_evals = function_evals + 1  # keeping track of number of function evaluations

        # Select the Pareto Optimal individuals
        selection = sel.selectPareto(offspring, config.optimization.initialind)

        print (len(halloffame))
        if len(halloffame) <= halloffame_size:
            halloffame.extend(selection)
        else:
            halloffame.extend(selection)
            halloffame = sel.selectPareto(halloffame, halloffame_size)
            print (halloffame)

        for ind in halloffame:
            halloffame_fitness.append(ind.fitness.values)

        # Compute the epsilon criteria [and check the stopping criteria]
        epsInd.append(evaluation.epsIndicator(pop, selection))
        euclidean_distance, spread = convergence_metric(pop, selection, normalization)
        #if len(epsInd) >1:
        #    eta = (epsInd[-1] - epsInd[-2]) / epsInd[-2]
        #    if eta < gv.epsMargin:
        #        stopCrit = True

        # The population is entirely replaced by the best individuals

        pop[:] = selection

        xs = [((objectives[0]) / 10 ** 6) for objectives in fitnesses]  # Costs
        ys = [((objectives[1]) / 10 ** 6) for objectives in fitnesses]  # GHG emissions
        zs = [((objectives[2]) / 10 ** 6) for objectives in fitnesses]  # MJ

        # plot showing the Pareto front of every generation

        fig = plt.figure()
        ax = fig.add_subplot(111)
        cm = plt.get_cmap('jet')
        cNorm = matplotlib.colors.Normalize(vmin=min(zs), vmax=max(zs))
        scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)
        ax.scatter(xs, ys, c=scalarMap.to_rgba(zs), s=50, alpha=0.8)
        ax.set_xlabel('TAC [$ Mio/yr]')
        ax.set_ylabel('GHG emissions [x 10^3 ton CO2-eq]')
        scalarMap.set_array(zs)
        fig.colorbar(scalarMap, label='Primary Energy [x 10^3 GJ]')
        plt.grid(True)
        plt.rcParams['figure.figsize'] = (20, 10)
        plt.rcParams.update({'font.size': 12})
        plt.gcf().subplots_adjust(bottom=0.15)
        plt.savefig(os.path.join(locator.get_optimization_plots_folder(), "pareto_" + str(g) + ".png"))
        plt.clf()

        # Create Checkpoint if necessary
        if g % config.optimization.fcheckpoint == 0:
            print "Create CheckPoint", g, "\n"
            fitnesses = map(toolbox.evaluate, pop)
            with open(locator.get_optimization_checkpoint(g), "wb") as fp:
                cp = dict(population=pop, generation=g, networkList=ntwList, epsIndicator=epsInd, testedPop=invalid_ind,
                          population_fitness=fitnesses, halloffame=halloffame, halloffame_fitness=halloffame_fitness,
                          euclidean_distance=euclidean_distance, spread=spread)
                json.dump(cp, fp)

    if g == config.optimization.ngen:
        print "Final Generation reached"
    else:
        print "Stopping criteria reached"

    # Saving the final results
    print "Save final results. " + str(len(pop)) + " individuals in final population"
    print "Epsilon indicator", epsInd, "\n"
    fitnesses = map(toolbox.evaluate, pop)
    with open(locator.get_optimization_checkpoint_final(), "wb") as fp:
        cp = dict(population=pop, generation=g, networkList=ntwList, epsIndicator=epsInd, testedPop=invalid_ind,
                  population_fitness=fitnesses, halloffame=halloffame, halloffame_fitness=halloffame_fitness,
                  euclidean_distance=euclidean_distance, spread=spread)
        json.dump(cp, fp)

    print "Master Work Complete \n"
    print ("Number of function evaluations = " + str(function_evals))
    
    return pop, epsInd

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
            distance.append(np.sqrt(((aNew - aOld) / normalization[0])**2 + ((bNew - bOld) / normalization[1])**2 +
                                    ((cNew - cOld) / normalization[2])**2))

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
                spread.append(np.sqrt(((cost_i - cost_j) / normalization[0])**2 + ((co2_i - co2_j) / normalization[1])**2 +
                                    ((eprim_i - eprim_j) / normalization[2])**2))
                spread_i.append(np.sqrt(((cost_i - cost_j) / normalization[0]) ** 2 + ((co2_i - co2_j) / normalization[1]) ** 2 +
                            ((eprim_i - eprim_j) / normalization[2]) ** 2))

        nearest_neighbor.append(min(spread_i))
    average_spread = np.mean(spread)

    nearest_neighbor = [abs(x - average_spread) for x in nearest_neighbor]

    spread_final = np.sum(nearest_neighbor)

    print ('combined euclidean distance = ' + str(combined_euclidean_distance))
    print ('spread = ' + str(spread_final))

    return combined_euclidean_distance, spread_final




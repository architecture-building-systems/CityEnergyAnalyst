"""
===========================
Evolutionary algorithm main
===========================

"""
from __future__ import division

import os
import time
from pickle import Pickler, Unpickler
import csv
import json

import cea.optimization.master.crossover as cx
import cea.optimization.master.evaluation as evaluation
from deap import base
from deap import creator
from deap import tools

import cea.optimization.master.generation as generation
import mutations as mut
import selection as sel

__author__ =  "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Sreepathi Bhargava Krishna", "Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def evolutionary_algo_main(locator, building_names, extra_costs, extra_CO2, extra_primary_energy, solar_features,
                           network_features, gv, genCP=0):
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

    # get number of buildings
    nBuildings = len(building_names)

    # DEFINE OBJECTIVE FUNCTION
    def objective_function(ind):
        (costs, CO2, prim) = evaluation.evaluation_main(ind, building_names, locator, extra_costs, extra_CO2, extra_primary_energy, solar_features,
                                                        network_features, gv)
        return (costs, CO2, prim)

    # SET-UP EVOLUTIONARY ALGORITHM
    # Contains 3 minimization objectives : Costs, CO2 emissions, Primary Energy Needs
    creator.create("Fitness", base.Fitness, weights=(-1.0, -1.0, -1.0))
    creator.create("Individual", list, fitness=creator.Fitness)
    toolbox = base.Toolbox()
    toolbox.register("generate", generation.generate_main, nBuildings, gv)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.generate)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", objective_function)

    ntwList = ["1"*nBuildings]
    epsInd = []
    invalid_ind = []

    # Evolutionary strategy
    if genCP is 0:
        # create population
        pop = toolbox.population(n=gv.initialInd)

        # Check distribution
        for ind in pop:
            evaluation.checkNtw(ind, ntwList, locator, gv)

        # Evaluate the initial population
        print "Evaluate initial population"
        fitnesses = map(toolbox.evaluate, pop)

        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit
            print ind.fitness.values, "fit"

        # Save initial population
        print "Save Initial population \n"

        with open(locator.get_optimization_checkpoint_initial(),"wb") as fp:
            cp = dict(population=pop, generation=0, networkList=ntwList, epsIndicator=[], testedPop=[], population_fitness=fitnesses)
            json.dump(cp, fp)

    else:
        print "Recover from CP " + str(genCP) + "\n"

        with open(locator.get_optimization_checkpoint(genCP), "rb") as CPread:
            CPunpick = Unpickler(CPread)
            cp = CPunpick.load()
            pop = cp["population"]
            ntwList = cp["networkList"]
            epsInd = cp["epsIndicator"]

    PROBA, SIGMAP = gv.PROBA, gv.SIGMAP

    # Evolution starts !
    g = genCP
    stopCrit = False # Threshold for the Epsilon indicator, Not used

    while g < gv.NGEN and not stopCrit and ( time.clock() - t0 ) < gv.maxTime :

        g += 1
        print "Generation", g

        offspring = list(pop)

        # Apply crossover and mutation on the pop
        print "CrossOver"
        for ind1, ind2 in zip(pop[::2], pop[1::2]):
            child1, child2 = cx.cxUniform(ind1, ind2, PROBA, gv)
            offspring += [child1, child2]

        # First half of the master: create new un-correlated configurations
        if g < gv.NGEN/2:
            for mutant in pop:
                print "Mutation Flip"
                offspring.append(mut.mutFlip(mutant, PROBA, gv))
                print "Mutation Shuffle"
                offspring.append(mut.mutShuffle(mutant, PROBA, gv))
                print "Mutation GU \n"
                offspring.append(mut.mutGU(mutant, PROBA, gv))

        # Third quarter of the master: keep the good individuals but modify the shares uniformly
        elif g < gv.NGEN * 3/4:
            for mutant in pop:
                print "Mutation Uniform"
                offspring.append(mut.mutUniformCap(mutant, gv))

        # Last quarter: keep the very good individuals and modify the shares with Gauss distribution
        else:
            for mutant in pop:
                print "Mutation Gauss"
                offspring.append(mut.mutGaussCap(mutant, SIGMAP, gv))


        # Evaluate the individuals with an invalid fitness
        # NB: every generation leads to the reevaluation of (n/2) / (n/4) / (n/4) individuals
        # (n being the number of individuals in the previous generation)
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]

        print "Update Network list \n"
        for ind in invalid_ind:
            evaluation.checkNtw(ind, ntwList, locator, gv)

        print "Re-evaluate the population"
        fitnesses = map(toolbox.evaluate, invalid_ind)

        print "......................................."
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
            print ind.fitness.values, "new fit"
        print "....................................... \n"

        # Select the Pareto Optimal individuals
        selection = sel.selectPareto(offspring,gv)

        # Compute the epsilon criteria [and check the stopping criteria]
        epsInd.append(evaluation.epsIndicator(pop, selection))
        #if len(epsInd) >1:
        #    eta = (epsInd[-1] - epsInd[-2]) / epsInd[-2]
        #    if eta < gv.epsMargin:
        #        stopCrit = True

        # The population is entirely replaced by the best individuals
        print "Replace the population \n"
        pop[:] = selection

        print "....................................... \n GENERATION ", g
        for ind in pop:
            print ind.fitness.values, "selected fit"
        print "....................................... \n"

        # Create Checkpoint if necessary
        if g % gv.fCheckPoint == 0:
            print "Create CheckPoint", g, "\n"
            fitnesses = map(toolbox.evaluate, pop)
            with open(locator.get_optimization_checkpoint(g), "wb") as fp:
                cp = dict(population=pop, generation=g, networkList=ntwList, epsIndicator=epsInd, testedPop=invalid_ind,
                          population_fitness=fitnesses)
                json.dump(cp, fp)

    if g == gv.NGEN:
        print "Final Generation reached"
    else:
        print "Stopping criteria reached"

    # Saving the final results
    print "Save final results. " + str(len(pop)) + " individuals in final population"
    print "Epsilon indicator", epsInd, "\n"
    fitnesses = map(toolbox.evaluate, pop)
    with open(locator.get_optimization_checkpoint_final(), "wb") as fp:
        cp = dict(population=pop, generation=g, networkList=ntwList, epsIndicator=epsInd, testedPop=invalid_ind,
                  population_fitness=fitnesses)
        json.dump(cp, fp)

    print "Master Work Complete \n"
    
    return pop, epsInd




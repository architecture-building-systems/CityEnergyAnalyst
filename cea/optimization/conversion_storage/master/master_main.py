"""
===========================
Evolutionary algorithm main
===========================

"""
from __future__ import division

import os
import time
from pickle import Pickler, Unpickler

import cea.optimization.conversion_storage.master.evaluation as evaluation_function
import cea.optimization.conversion_storage.master.generation as generation_function
import mutations as mut
import selection as sel
from deap import base
from deap import creator
from deap import tools

import cea.optimization.conversion_storage.master.crossover as cx


__author__ =  "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def evolutionary_algo_main(locator, building_names, extra_costs, extra_CO2, extra_primary_energy, solar_features,
                           network_features, gv, genCP = 0):
    """
    Evolutionary algorithm to optimize the district energy system's design.
    This algortihm optimizes the size and operation of technologies for a district heating netowrk.
    electrical netowrk are not considered but their burdens in terms electricity costs, efficiency and emissions
    is added on top of the optimization
    The equipment for Cooling networks is not optimized as it is assumed that all customer with cooling needs will be
    connected to a lake. in case there is not enough cvapacity form the lake a chiller and cooling tower is used to cover
    the extra needs.

    :param locator: locator class
    :param building_names: vector with building names
    :param extra_costs: costs calculated before optimization ofr specific energy services
     (process heat and electricity)
    :param extra_CO2: green house gas emissions calculated before optimization ofr specific energy services
     (process heat and electricity)
    :param extra_primary_energy: primary energy calculated before optimization ofr specific energy services
     (process heat and electricity)
    :param solar_features: object class with vectors and values of interest for the integration of solar potentials
    :param network_features: object class with linear coefficients of the netowrk obtained after its optimization
    :param gv: global variables class
    :param genCP:
    :return:
        for every generation 'g': it stores the results of every generation of the genetic algorithm in the subfolders
        locator.get_optimization_master_results_folder() as a python pickle file.

    """
    t0 = time.clock()

    # get number of buildings
    nBuildings = len(building_names)

    # DEFINE OBJECTIVE FUNCTION
    def objective_function(ind):
        (costs, CO2, prim) = evaluation_function.evaluation_main(ind, building_names, locator, extra_costs, extra_CO2, extra_primary_energy, solar_features,
                                                                 network_features, gv)
        return (costs, CO2, prim)

    # SET-UP EVOLUTIONARY ALGORITHM
    # Contains 3 minimization objectives : Costs, CO2 emissions, Primary Energy Needs
    creator.create("Fitness", base.Fitness, weights=(-1.0, -1.0, -1.0))
    creator.create("Individual", list, fitness=creator.Fitness)
    toolbox = base.Toolbox()
    toolbox.register("generate", generation_function.generate_main, nBuildings, gv)
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
            evaluation_function.checkNtw(ind, ntwList, locator, gv)
        
        # Evaluate the initial population
        print "Evaluate initial population"
        fitnesses = map(toolbox.evaluate, pop)

        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit
            print ind.fitness.values, "fit"
        
        # Save initial population
        print "Save Initial population \n"
        os.chdir(locator.get_optimization_master_results_folder())
        with open("CheckPointInitial","wb") as CPwrite:
            CPpickle = Pickler(CPwrite)
            cp = dict(population=pop, generation=0, networkList = ntwList, epsIndicator = [], testedPop = [])
            CPpickle.dump(cp)
    else:
        print "Recover from CP " + str(genCP) + "\n"
        os.chdir(locator.get_optimization_master_results_folder())

        with open("CheckPoint" + str(genCP), "rb") as CPread:
            CPunpick = Unpickler(CPread)
            cp = CPunpick.load()
            pop = cp["population"]
            ntwList = cp["networkList"]
            epsInd = cp["epsIndicator"]
    
    PROBA, SIGMAP = gv.PROBA, gv.SIGMAP
    
    # Evolution starts !
    g = genCP
    stopCrit = False # Threshold for the Epsilon indictor, Not used
	
    while g < gv.NGEN and not stopCrit and ( time.clock() - t0 ) < gv.maxTime :
        
        g += 1
        print "Generation", g
        
        offspring = list(pop)
        
        # Apply crossover and mutation on the pop
        print "CrossOver"
        for ind1, ind2 in zip(pop[::2], pop[1::2]):
            child1, child2 = cx.cxUniform(ind1, ind2, PROBA, gv)
            offspring += [child1, child2]

        # First half of the master: create new un-collerated configurations
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
        # NB: every generation leads to the reevaluation of 4n / 2n / 2n individuals
        # (n being the number of individuals in the previous generation)
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        
        print "Update Network list \n"
        for ind in invalid_ind:
            evaluation_function.checkNtw(ind, ntwList, locator, gv)
        
        print "Re-evaluate the population" 
        fitnesses = map(toolbox.evaluate, invalid_ind)
        
        print "......................................."
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
            print ind.fitness.values, "new fit"
        print "....................................... \n"
        
        # Select the Pareto Optimal individuals
        print "Pareto Selection"
        selection = sel.selectPareto(offspring)
        
        # Compute the epsilon criteria [and check the stopping criteria]
        epsInd.append(evaluation_function.epsIndicator(pop, selection))
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
            os.chdir(locator.get_optimization_master_results_folder())
            
            print "Create CheckPoint", g, "\n"
            with open("CheckPoint" + str(g),"wb") as CPwrite:
                CPpickle = Pickler(CPwrite)
                cp = dict(population=pop, generation=g, networkList = ntwList, epsIndicator = epsInd, testedPop = invalid_ind)
                CPpickle.dump(cp)


    if g == gv.NGEN:
        print "Final Generation reached"
    else:
        print "Stopping criteria reached"
	
    # Saving the final results
    print "Save final results. " + str(len(pop)) + " individuals in final population"
    print "Epsilon indicator", epsInd, "\n"
    os.chdir(locator.get_optimization_master_results_folder())
    
    with open("CheckPointFinal","wb") as CPwrite:
        CPpickle = Pickler(CPwrite)
        cp = dict(population=pop, generation=g, networkList = ntwList, epsIndicator = epsInd, testedPop = invalid_ind)
        CPpickle.dump(cp)
        
    print "Master Work Complete \n"
    
    return pop, epsInd




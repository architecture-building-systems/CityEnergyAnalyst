"""
===========================
Evolutionary algorithm main
===========================

"""
from __future__ import division

import os
import time
from pickle import Pickler, Unpickler

import cea.optimization.master.evolAlgo.CreateInd as ci
import cea.optimization.master.evolAlgo.CrossOver as cx
import evolAlgo.Mutations as mut
import evolAlgo.Selection as sel
from deap import base
from deap import creator
from deap import tools

import cea.optimization.supportFn as sFn
import cea.optimization.master.evolAlgo.evaluateInd as eI
from cea.optimization.master.evolAlgo import constrCheck as cCheck


def calc_ea_setup(nBuildings, gv):
    """
    This sets-up the evolutionary algorithm of the library DEAp in python
    :return:
    """
    # import evaluation routine

    # Contains 3 Fitnesses : Costs, CO2 emissions, Primary Energy Needs
    creator.create("Fitness", base.Fitness, weights=(-1.0, -1.0, -1.0))
    creator.create("Individual", list, fitness=creator.Fitness)
    toolbox = base.Toolbox()
    toolbox.register("generate", ci.generateInd, nBuildings, gv)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.generate)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    return creator, toolbox

def EA_Main(locator, building_names, extraCosts, extraCO2, extraPrim, solarFeat, ntwFeat, gv, genCP = 0):
    """
    Evolutionary algorithm to optimize the district energy system's design
    
    Parameters
    ----------
    locator : string
        paths to folders
    finances / CO2 / Prim : float
        costs [CHF] / emissions [kg CO2-eq] / primary energy needs [MJ oil] 
        previously calculated
    solarFeat : class solarFeatures
        includes data from solar files
    ntwFeat : class ntwFeatures
        includes data from the ntw optimization
    genCP : int
        generation to start the EA from (eg if there was a crash of the code)
    
    Returns
    -------
    
    """
    t0 = time.clock()

    # get number of buildings
    nBuildings = len(building_names)

    # set-up toolbox of DEAp library in python (containing the evolutionary algotirhtm
    creator, toolbox = calc_ea_setup(nBuildings, gv)

    # define objective function and register into toolbox
    def evalConfig(ind):
        (costs, CO2, prim) = eI.evalInd(ind, building_names, locator, extraCosts, extraCO2, extraPrim, solarFeat,
                                        ntwFeat, gv)
        return (costs, CO2, prim)

    toolbox.register("evaluate", evalConfig)

    ntwList = ["1"*nBuildings]
    epsInd = []
    invalid_ind = []

    # Evolutionary strategy
    if genCP is 0:
        # create population
        pop = toolbox.population(n=gv.initialInd)

        # Check network
        for ind in pop:
            eI.checkNtw(ind, ntwList, locator, gv)
        
        # Evaluate the initial population
        print "Evaluate initial population"
        fitnesses = map(toolbox.evaluate, pop)

        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit
            print ind.fitness.values, "fit"
        
        # Save initial population
        print "Save Initial population \n"
        os.chdir(locator.pathMasterRes)
        with open("CheckPointInitial","wb") as CPwrite:
            CPpickle = Pickler(CPwrite)
            cp = dict(population=pop, generation=0, networkList = ntwList, epsIndicator = [], testedPop = [])
            CPpickle.dump(cp)
    else:
        print "Recover from CP " + str(genCP) + "\n"
        os.chdir(locator.pathMasterRes)

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

        # First half of the EA: create new un-collerated configurations
        if g < gv.NGEN/2:
            for mutant in pop:
                print "Mutation Flip"
                offspring.append(mut.mutFlip(mutant, PROBA, gv))
                print "Mutation Shuffle"
                offspring.append(mut.mutShuffle(mutant, PROBA, gv))
                print "Mutation GU \n"
                offspring.append(mut.mutGU(mutant, PROBA, gv))
                
        # Third quarter of the EA: keep the good individuals but modify the shares uniformly
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
            eI.checkNtw(ind, ntwList, locator, gv)
        
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
        epsInd.append(eI.epsIndicator(pop, selection))
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
            os.chdir(locator.pathMasterRes)
            
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
    os.chdir(locator.pathMasterRes)
    
    with open("CheckPointFinal","wb") as CPwrite:
        CPpickle = Pickler(CPwrite)
        cp = dict(population=pop, generation=g, networkList = ntwList, epsIndicator = epsInd, testedPop = invalid_ind)
        CPpickle.dump(cp)
        
    print "Master Work Complete \n"
    
    return pop, epsInd




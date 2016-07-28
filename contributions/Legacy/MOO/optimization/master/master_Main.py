"""
===========================
Evolutionary algorithm main
===========================

"""
from __future__ import division

import os
import time
from pickle import Pickler, Unpickler

import contributions.Legacy.MOO.optimization.evolAlgo.CreateInd as ci
import contributions.Legacy.MOO.optimization.evolAlgo.CrossOver as cx
import evolAlgo.Mutations as mut
import evolAlgo.Selection as sel
from deap import base
from deap import creator
from deap import tools

import contributions.Legacy.MOO.optimization.supportFn as sFn
import contributions.Legacy.MOO.optimization.master.evolAlgo.evaluateInd as eI
from contributions.Legacy.MOO.optimization.master.evolAlgo import constrCheck as cCheck


def EA_Main(pathX, extraCosts, extraCO2, extraPrim, solarFeat, ntwFeat, gV, genCP = 0, manualCheck = 0):
    """
    Evolutionary algorithm to optimize the district energy system's design
    
    Parameters
    ----------
    pathX : string
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
    print("Master / Slave optimization ready")
    t0 = time.clock()
    
    # Extract the names of the buildings present in the district
    buildList = sFn.extractList(pathX.pathRaw+'//'+"Total.csv")
    nBuildings = len(buildList)
    
    # Set the DEAP toolbox
    creator.create("Fitness", base.Fitness, weights=(-1.0, -1.0, -1.0))
    # Contains 3 Fitnesses : Costs, CO2 emissions, Primary Energy Needs
    creator.create("Individual", list, fitness=creator.Fitness)
    
    toolbox = base.Toolbox()
    toolbox.register("generate", ci.generateInd, nBuildings, gV)
    toolbox.register("individual", tools.initIterate, creator.Individual,
                    toolbox.generate)
    
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    ntwList = ["1"*nBuildings]
    epsInd = []
    invalid_ind = []
    
    def evalConfig(ind):
        (costs, CO2, prim) = eI.evalInd(ind, buildList, pathX, extraCosts, extraCO2, extraPrim, solarFeat, ntwFeat, gV)
        return (costs, CO2, prim)
        
    toolbox.register("evaluate", evalConfig)
    
    # Evolutionary strategy
    # Recover from the last checkpoint or start from scratch

    if genCP > 0:
        print "Recover from CP "+ str(genCP) + "\n"
        os.chdir(pathX.pathMasterRes)
    
        with open("CheckPoint" + str(genCP),"rb") as CPread:
            CPunpick = Unpickler(CPread)
            cp = CPunpick.load()
            pop = cp["population"]
            ntwList = cp["networkList"]
            epsInd = cp["epsIndicator"]
        
    else:
        
        if manualCheck == 1:
            print "Manual Check \n"
            pop = toolbox.population(n=1)
            gV.NGEN = 0
            map(cCheck.putToRef, pop)
            #map(cCheck.manualCheck, pop)
            #map(cCheck.manualCheck2, pop)
            
        else:
            print "Creation of a population \n"
            pop = toolbox.population(n=gV.initialInd)

        # Check network
        print "Update Network list \n"
        for ind in pop:
            eI.checkNtw(ind, ntwList, pathX, gV)
        
        # Evaluate the initial population
        print "Evaluate initial population \n"
        fitnesses = map(toolbox.evaluate, pop)
        
        print "......................................."       
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit
            print ind.fitness.values, "fit"
        print "....................................... \n"
        
        # Save initial population
        print "Save Initial population \n"
        os.chdir(pathX.pathMasterRes)
        with open("CheckPointInitial","wb") as CPwrite:
            CPpickle = Pickler(CPwrite)
            cp = dict(population=pop, generation=0, networkList = ntwList, epsIndicator = epsInd, testedPop = invalid_ind)
            CPpickle.dump(cp)
    
    
    PROBA, SIGMAP = gV.PROBA, gV.SIGMAP
    
    # Evolution starts !
    g = genCP
    stopCrit = False # Threshold for the Epsilon indictor, Not used
	
    while g < gV.NGEN and not stopCrit and ( time.clock() - t0 ) < gV.maxTime :
        
        g += 1
        print "Generation", g
        
        offspring = list(pop)
        
        # Apply crossover and mutation on the pop
        print "CrossOver"
        for ind1, ind2 in zip(pop[::2], pop[1::2]):
            child1, child2 = cx.cxUniform(ind1, ind2, PROBA, gV)
            offspring += [child1, child2]

        # First half of the EA: create new un-collerated configurations
        if g < gV.NGEN/2:
            for mutant in pop:
                print "Mutation Flip"
                offspring.append(mut.mutFlip(mutant, PROBA, gV))
                print "Mutation Shuffle"
                offspring.append(mut.mutShuffle(mutant, PROBA, gV))
                print "Mutation GU \n"
                offspring.append(mut.mutGU(mutant, PROBA, gV))
                
        # Third quarter of the EA: keep the good individuals but modify the shares uniformly
        elif g < gV.NGEN * 3/4:
            for mutant in pop:
                print "Mutation Uniform"
                offspring.append(mut.mutUniformCap(mutant, gV))
        
        # Last quarter: keep the very good individuals and modify the shares with Gauss distribution
        else:
            for mutant in pop:
                print "Mutation Gauss"
                offspring.append(mut.mutGaussCap(mutant, SIGMAP, gV))


        # Evaluate the individuals with an invalid fitness
        # NB: every generation leads to the reevaluation of 4n / 2n / 2n individuals
        # (n being the number of individuals in the previous generation)
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        
        print "Update Network list \n"
        for ind in invalid_ind:
            eI.checkNtw(ind, ntwList, pathX, gV)
        
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
        #    if eta < gV.epsMargin:
        #        stopCrit = True

        # The population is entirely replaced by the best individuals
        print "Replace the population \n"
        pop[:] = selection
        
        print "....................................... \n GENERATION ", g
        for ind in pop:
            print ind.fitness.values, "selected fit"
        print "....................................... \n"
        
        # Create Checkpoint if necessary
        if g % gV.fCheckPoint == 0:
            os.chdir(pathX.pathMasterRes)
            
            print "Create CheckPoint", g, "\n"
            with open("CheckPoint" + str(g),"wb") as CPwrite:
                CPpickle = Pickler(CPwrite)
                cp = dict(population=pop, generation=g, networkList = ntwList, epsIndicator = epsInd, testedPop = invalid_ind)
                CPpickle.dump(cp)


    if g == gV.NGEN:
        print "Final Generation reached"
    else:
        print "Stopping criteria reached"
	
    # Saving the final results
    print "Save final results. " + str(len(pop)) + " individuals in final population"
    print "Epsilon indicator", epsInd, "\n"
    os.chdir(pathX.pathMasterRes)
    
    with open("CheckPointFinal","wb") as CPwrite:
        CPpickle = Pickler(CPwrite)
        cp = dict(population=pop, generation=g, networkList = ntwList, epsIndicator = epsInd, testedPop = invalid_ind)
        CPpickle.dump(cp)
        
    print "Master Work Complete \n"
    
    return pop, epsInd




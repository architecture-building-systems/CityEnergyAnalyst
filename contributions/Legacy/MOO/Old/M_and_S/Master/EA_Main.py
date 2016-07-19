"""
===========================
Evolutionary algorithm main
===========================

"""
from __future__ import division
import os

from deap import base
from deap import creator
from deap import tools
from numpy.random import random_sample

pathmodules = "C:/Users/Thuy-An/Documents/GitHub/urben/Masterarbeit/M_and_S/Master"
os.chdir(pathmodules)

import EA_globalVar as gV
import CreateInd as ci
import Mutations as mut
import CrossOver as cx
import SupportFn as sFn
import Rep3D as rep
import Selection as sel

reload(gV)
reload(ci)
reload(mut)
reload(cx)
reload(sFn)
reload(rep)
reload(sel)


#import QConstraints as qc
#import AssociatePlantSize as aps
#reload(qc)
#reload(aps)



pathdata = "C:/Users/Thuy-An/Documents/ETH/Arch Master Thesis/Python results/EA extract"
os.chdir(pathdata)


# Pre-treatment of the data :
# Extract the names of the buildings present in the district
# and Calculate the constraints on the heating dem

buildList = sFn.extractList(gV.buildListFile)
nBuildings = len(buildList)

#Qmax_dico = qc.Qmax_perBuild(pathdata, buildList)
#QmaxCombi_dico = qc.Qmax_perCombi(pathdata, buildList)


# Create individuals

creator.create("Fitness", base.Fitness, weights=(-1.0, -1.0, 1.0))
# Contains 3 Fitnesses : Costs, CO2 emissions, Efficiency
creator.create("Individual", list, fitness=creator.Fitness)

toolbox = base.Toolbox()
toolbox.register("generate", ci.generateInd, nBuildings)
toolbox.register("individual", tools.initIterate, creator.Individual,
                 toolbox.generate)

# Create a population

toolbox.register("population", tools.initRepeat, list, toolbox.individual)


# Evaluate the population

def dummyevaluate(individual):
    [costs, CO2, eff] = random_sample(3)
    return (costs, CO2, eff)

toolbox.register("evaluate", dummyevaluate)


# Evolutionary strategy

def main():
    print "Creation of a population"
    pop = toolbox.population(n=gV.nInd)
    PROBA, SIGMAP, NGEN = 0.5, 0.2, 2

    # Evaluate the entire population
    print "Evaluate the population"
    fitnesses = map(toolbox.evaluate, pop)
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
    
    print "3D scatter of entire population"
    rep.rep3Dscatter(pop)

    for g in range(NGEN):
        print "Generation", g
        
        offspring = list(pop)
        
        # Apply crossover and mutation on the pop
        print "CrossOver"
        for ind1, ind2 in zip(pop[::2], pop[1::2]):
            child1, child2 = cx.cxUniform(ind1, ind2, PROBA)
            offspring += [child1, child2]

        for mutant in pop:
            print "Mutation Flip"
            offspring.append(mut.mutFlip(mutant, PROBA))
            print "Mutation Shuffle"
            offspring.append(mut.mutShuffle(mutant, PROBA))
            print "Mutation Gauss"
            offspring.append(mut.mutGaussCap(mutant, SIGMAP))
            print "Mutation Uniform"
            offspring.append(mut.mutUniformCap(mutant))
            print "Mutation GU"
            offspring.append(mut.mutGU(mutant, PROBA))

        # Evaluate the individuals with an invalid fitness
        print "Reevaluate the population"
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        
        # Select the Pareto Optimal individuals
        print "Pareto Selection"
        selection = sel.selectPareto(offspring)
        
        print "3D of Pareto Frontier"
        rep.rep3Dsurf(selection)

        # The population is entirely replaced by the pop
        print "Replace the population"
        pop[:] = selection

    return pop

pop = main()


def dummyGenerate(n):
    [item] = random_sample(1)
    return [item]

toolbox.register("generate", dummyGenerate, nBuildings)

pop = toolbox.population(n=2000)
fitnesses = map(toolbox.evaluate, pop)
for ind, fit in zip(pop, fitnesses):
    ind.fitness.values = fit
selection = sel.selectPareto(pop)

rep.rep3Dscatter(selection)
rep.rep3Dsurf(selection)


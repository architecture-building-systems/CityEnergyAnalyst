import array
import multiprocessing
import random
import sys
import numpy as np

if sys.version_info < (2, 7):
    print("mpga_onemax example requires Python >= 2.7.")
    exit(1)

import numpy

from deap import algorithms
from deap import base
from deap import creator
from deap import tools

def create_individual():

    # initiate the individual
    individual = [0] * 3

    # type_leak
    individual[0] = round(1.0 + random.randint(1, 60) * (0.1), 1)

    # type_win
    individual[1] = round(1.0 + random.randint(1, 60) * (0.1), 1)

    individual[2] = round(1.0 + random.randint(1, 60) * (0.1), 1)

    return individual

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, typecode='d', fitness=creator.FitnessMin)

toolbox = base.Toolbox()

# Attribute generator
toolbox.register("attr_bool", random.randint, 0, 1)

# Structure initializers
toolbox.register("generate", create_individual)
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.generate, 1)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

x = range(200)
y = range(200)

for i in range(len(x)): # equation to generate data
    y[i] = 5 * x[i]**2 + 6*x[i] + 4


def evalOneMax(individual): # objective function
    z = range(200)

    for i in range(len(x)):
        z[i] = individual[0] * x[i]**2 + individual[1]*x[i] + individual[2]

    sum_ind = 0
    for i in range(len(z)):
        sum_ind = sum_ind + (z[i] - y[i])**2
    return np.sqrt(sum_ind),

lower_bound = [1.0, 1.0, 1.0]
upper_bound = [6.0, 6.0, 6.0]
toolbox.register("evaluate", evalOneMax)
toolbox.register("mate", tools.cxUniform, indpb=0.1)
toolbox.register("mutate", tools.mutPolynomialBounded, low=lower_bound, up=upper_bound, eta=20.0, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)

if __name__ == "__main__":
    random.seed(64)

    # Process Pool of 4 workers
    # pool = multiprocessing.Pool(processes=4)

    pop = toolbox.population(n=1000)
    # CXPB  is the probability with which two individuals
    #       are crossed
    #
    # MUTPB is the probability for mutating an individual
    CXPB, MUTPB = 0.7, 0.8

    # Evaluate the entire population
    # fitnesses = list(map(toolbox.evaluate, pop))
    # for ind, fit in zip(pop, fitnesses):
    #     ind.fitness.values = fit


    for ind in pop:
        fit = evalOneMax(ind[0])
        ind.fitness.values = fit

    print("  Evaluated %i individuals" % len(pop))

    # Extracting all the fitnesses of
    fits = [ind.fitness.values[0] for ind in pop]

    # Variable keeping track of the number of generations
    g = 0

    # Begin the evolution
    while min(fits) > 0.0001 and g < 1000:
        # A new generation
        g = g + 1
        print("-- Generation %i --" % g)

        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))

        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):

            # cross two individuals with probability CXPB
            if random.random() < CXPB:
                toolbox.mate(child1[0], child2[0])

                # fitness values of the children
                # must be recalculated later
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offspring:

            # mutate an individual with probability MUTPB
            if random.random() < MUTPB:
                toolbox.mutate(mutant[0])
                del mutant.fitness.values

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        for ind in invalid_ind:
            fit = evalOneMax(ind[0])
            ind.fitness.values = fit

        print("  Evaluated %i individuals" % len(invalid_ind))

        # The population is entirely replaced by the offspring
        pop[:] = offspring

        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]
        print (min(fits))

    print("-- End of (successful) evolution --")

    best_ind = tools.selBest(pop, 1)[0]
    print("Best individual is %s, %s" % (best_ind, best_ind.fitness.values))

"""
===========================
Clustering
This script clusters typical days for a building
using SAX method for timeseries.

===========================
J. Fonseca  script development          27.10.16


"""
from __future__ import division

from cea.demand.calibration.sax import SAX
import pandas as pd

import numpy as np
from numpy import random
import time

from deap import algorithms, base, benchmarks, creator, tools
from deap.benchmarks.tools import diversity, convergence

from sklearn.metrics import silhouette_score
from sklearn import metrics

import matplotlib.pyplot as plt

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def clustering(locator, gv, wordSize, alphabetSize, building_name, building_load):
    t0 = time.clock()

    # import data
    data = pd.read_csv(locator.get_demand_results_file(building_name),
                       usecols=['DATE', building_load], index_col='DATE')
    data.set_index(pd.to_datetime(data.index), inplace=True)
    data['day'] = data.index.dayofyear

    # transform into dicts where key = day and value = 24 h array
    groups = data.groupby(data.day)
    arrays = [group[1][building_load].values for group in groups]

    # set optimization problem for wordzise and alpha number
    pop, stats = my_mo_problem(arrays)


    gv.log('done - time elapsed: %(time_elapsed).2f seconds', time_elapsed=time.clock() - t0)



# calculate dict with data per hour for the whole year and create groups per pattern
# array_hours = range(24)
# array_days = range(365)
# arrays_T = [list(x) for x in zip(*arrays)]
# dict_data = dict((group,x) for group, x in zip(array_hours, arrays_T))
# dict_data.update({'sax': sax, 'day': array_days})
#
# # create group by pattern
# grouped_sax = pd.DataFrame(dict_data).groupby('sax')
#
# for name, group in grouped_sax:
#     transpose = group.T.drop(['sax', 'day'], axis=0)
#     transpose.plot()
#     plt.show()


# print grouped_sax.describe()
def my_mo_problem(arrays):
    """
    A multi-objective problem.

    """

    #set-up deap library for optimization with 2 objectives to be maximized
    creator.create("Fitness", base.Fitness, weights=(1.0, 1.0)) # maximize shilluette and calinski
    creator.create("Individual", set, fitness=creator.Fitness)
    toolbox = base.Toolbox()

    #set-up problem
    BOUND_LOW, BOUND_UP = 3, 12
    NDIM = 2
    toolbox.register("attr_float", random.randrange, BOUND_LOW, BOUND_UP, NDIM, arrays)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_float)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    def evaluation(individual):
        s = SAX(individual[0], individual[1])
        sax = [s.to_letter_rep(array)[0] for array in arrays]
        f1 = silhouette_score(arrays, sax)
        f2 = metrics.calinski_harabaz_score(arrays, sax)
        return f1, f2

    toolbox.register("evaluate", evaluation)
    toolbox.register("mate", tools.cxSimulatedBinaryBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0)
    toolbox.register("mutate", tools.mutPolynomialBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0, indpb=1.0 / NDIM)
    toolbox.register("select", tools.selNSGA2)

    def main_opt(seed=None):
        random.seed(seed)

        NGEN = 250
        MU = 100
        CXPB = 0.9

        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean, axis=0)
        stats.register("std", np.std, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)

        logbook = tools.Logbook()
        logbook.header = "gen", "evals", "std", "min", "avg", "max"

        pop = toolbox.population(n=MU)

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in pop if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

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
        return pop, stats
    return main_opt()

def run_as_script():
    """"""
    import cea.globalvar as gv
    import cea.inputlocator as inputlocator
    gv = gv.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    clustering(locator=locator, gv=gv, wordSize=6, alphabetSize=4, building_name='B01', building_load='Qhsf_kWh')

if __name__ == '__main__':
    run_as_script()

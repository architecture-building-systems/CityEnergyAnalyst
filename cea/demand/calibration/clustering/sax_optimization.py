"""
Multi-objective optimization of the variables ``word_size`` and ``alphabet_size`` for SAX in
:py:mod:`~cea.demand.calibration.clustering.clustering_main`.

Step required to get the right number of clusters in a semi - non-supervised manner.
"""
from __future__ import division

import math
import pickle

import os
import matplotlib
import matplotlib.cm as cmx

import matplotlib.pyplot as plt
import numpy as np
import deap.base
import deap.creator
import deap.tools
import deap.benchmarks.tools
from numpy import random
from sklearn.metrics import silhouette_score

from cea.demand.calibration.clustering.sax import SAX

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def sax_optimization(locator, data, time_series_len, BOUND_LOW, BOUND_UP, NGEN, MU, CXPB, start_gen, building_name):
    """
    A multi-objective problem set for three objectives to maximize using the DEAP library and NSGAII algorithm:
    1. Compound function of accurracy, complexity and compression based on the work of
    D. Garcia-Lopez1 and H. Acosta-Mesa 2009
    2. Classic Shiluette and
    3. Carlinski indicators of clustering_main.

    The variables to maximize are wordsize and alphabet size.

    :param data: list of lists containing the real values of the discretized timeseries (hourly values for every day).
    :param time_series_len: length of discretized timeseries.
    :param BOUND_LOW: lower bound
    :param BOUND_UP: upper bound
    :param NGEN: maximum number of generation
    :param MU: initial number of individuals (it has to be a multiple of 4 for this problem)
    :param CXPB: confidence
    :return: Plot with pareto front
    """
    # set-up deap library for optimization with 1 objective to minimize and 2 objectives to be maximized
    deap.creator.create("Fitness", deap.base.Fitness, weights=(1.0, 1.0, 1.0))  # maximize shilluette and calinski
    deap.creator.create("Individual", list, fitness=deap.creator.Fitness)

    # set-up problem
    NDIM = 2

    def generation(low, up, size=None):
        """
        This function creates a random distribution of the individuals
        :param low: low bound
        :param up: up bound
        :param size: none
        :return: vector with random generation of the individuals
        """
        try:
            return [random.randint(a, b) for a, b, in zip(low, up)]
        except TypeError:
            return [random.randint(a, b) for a, b, in zip([low] * size, [up] * size)]

    toolbox = deap.base.Toolbox()
    toolbox.register("attr_float", generation, BOUND_LOW, BOUND_UP, NDIM)
    toolbox.register("individual", deap.tools.initIterate, deap.creator.Individual, toolbox.attr_float)
    toolbox.register("population", deap.tools.initRepeat, list, toolbox.individual)

    def evaluation(ind):
        """
        This function evaluates each individual according to each objective function f1...fn

        :param ind: individual
        :return: resulting fitness value for the three objectives of the analysis.
        """
        s = SAX(ind[0], ind[1])
        sax = [s.to_letter_representation(array)[0] for array in data]
        accurracy = calc_accuracy(sax)
        complexity = calc_complexity(sax)
        compression = calc_compression(ind[0], time_series_len)
        f1 = accurracy#0.7 * accurracy + 0.17 * complexity + 0.13 * compression #information objective to maximize
        f2 = complexity #silhouette_score(np.array(data), np.array(sax))  # metrics.silhuette score_score(data, sax)
        f3 = compression#silhouette_score(np.array(data), np.array(sax))#len(set(sax)) # number of clusters to minimize

        return f1, f2, f3

    toolbox.register("evaluate", evaluation)
    toolbox.register("mate", deap.tools.cxTwoPoint)
    toolbox.register("mutate", deap.tools.mutUniformInt, low=BOUND_LOW, up=BOUND_UP, indpb=1.0 / NDIM)
    toolbox.register("select", deap.tools.selNSGA2)

    # run optimization
    def main(seed=None):
        random.seed(seed)
        if start_gen:
            # A file name has been given, then load the data from the file
            cp = pickle.load(open(locator.get_calibration_cluster_opt_checkpoint(start_gen), "rb"))
            pop = cp["population"]
            start_generation = cp["generation"]
            halloffame = cp["halloffame"]
            paretofrontier = cp["paretofrontier"]
            log_book = cp["log_book"]  # this registers
            random.set_state(cp["rndstate"])
        else:
            # Start a new evolution
            pop = toolbox.population(n=MU)
            start_generation = 1
            halloffame = deap.tools.HallOfFame(maxsize=3)
            paretofrontier = deap.tools.ParetoFront()
            log_book = deap.tools.Logbook()
            log_book.header = "gen", "evals", "std", "min", "avg", "max"

        stats = deap.tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean, axis=0)
        stats.register("std", np.std, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)

        # Evaluate the individuals with an invalid fitness
        invalid_individuals = [ind for ind in pop if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_individuals)
        for ind, fit in zip(invalid_individuals, fitnesses):
            ind.fitness.values = fit

        # This is just to assign the crowding distance to the individuals
        # no actual selection is done
        #deap.tools.emo.assignCrowdingDist(pop)
        pop = toolbox.select(pop, len(pop))

        record = stats.compile(pop)
        log_book.record(gen=0, evals=len(invalid_individuals), **record)
        print(log_book.stream)

        # Begin the generational process
        for generation in range(start_generation, NGEN + 1):
            # Vary the population
            offspring = deap.tools.selTournamentDCD(pop, len(pop))
            offspring = [toolbox.clone(ind) for ind in offspring]

            for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
                if random.random() <= CXPB:
                    toolbox.mate(ind1, ind2)

                toolbox.mutate(ind1)
                toolbox.mutate(ind2)
                del ind1.fitness.values, ind2.fitness.values

            # Evaluate the individuals with an invalid fitness
            invalid_individuals = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = toolbox.map(toolbox.evaluate, invalid_individuals)
            for ind, fit in zip(invalid_individuals, fitnesses):
                ind.fitness.values = fit

            # Select the next generation population
            #deap.tools.emo.assignCrowdingDist(pop+offspring)
            pop = toolbox.select(pop + offspring, MU)
            record = stats.compile(pop)

            # update the hall of fame and pareto
            halloffame.update(pop)
            paretofrontier.update(pop)
            log_book.record(gen=generation, evals=len(invalid_individuals), **record)
            print(log_book.stream)

            #calculate benchmarks
            diversity = deap.benchmarks.tools.diversity(paretofrontier, paretofrontier[0], paretofrontier[-1])

            FREQ = 1  # frequence of storage
            if generation % FREQ == 0:
                # Fill the dictionary using the dict(key=value[, ...]) constructor
                cp = dict(population=pop, generation=generation, halloffame=halloffame, paretofrontier=paretofrontier,
                          logbook=log_book, diversity=diversity, rndstate=random.get_state())

                with open(locator.get_calibration_cluster_opt_checkpoint(generation, building_name), "wb") as cp_file:
                    pickle.dump(cp, cp_file)

    main()
# ++++++++++++++++++++++++++++
# Evaluation functions
# ++++++++++++++++++++++++++++

def calc_complexity(names_of_clusters):
    """
    Calculated according to 'Application of time series discretization using evolutionary programming for classification
    of precancerous cervical lesions' by H. Acosta-Mesa et al., 2014
    :param names_of_clusters: list containing a word which clusters the time series. e.g., ['abcffs', dddddd'...'svfdab']
    :return: level of complexity which penalizes the objective function
    """
    single_words_length = len(list(set(names_of_clusters)))
    len_timeseries = len(names_of_clusters)  # number of observations
    result = 1- (single_words_length/ len_timeseries)
    return result


def calc_compression(word_size, time_series_len=24):
    """
    Calculated according to 'Application of time series discretization using evolutionary programming for classification
    of precancerous cervical lesions' by H. Acosta-Mesa et al., 2014
    :param word_size: wordsize chosen for the SAX algorithm. integer.
    :param time_series_len: length of time_series group. integer
    :return: level of compression which penalizes the objective function
    """
    result = 1- (word_size / time_series_len)  # 24 hours
    return result

def calc_accuracy(names_of_clusters):
    """
    Calculated according to 'Application of time series discretization using evolutionary programming for classification
    of precancerous cervical lesions' by H. Acosta-Mesa et al., 2014
    :param names_of_clusters: list containing a word which clusters the time series. e.g., ['abcffs', dddddd'...'svfdab']
    :return:
    """
    single_words = list(set(names_of_clusters))
    len_timeseries = len(names_of_clusters)
    entropy = 0
    for single_word in single_words:
        pi = names_of_clusters.count(single_word) / len_timeseries
        entropy += pi * math.log(pi,2)
    return - entropy/ math.log(len_timeseries,2)

# ++++++++++++++++++++++++++
# Printing option
# ++++++++++++++++++++++++++


def print_pareto(locator, generation, what_to_plot, building_name, labelx, labely, labelz,
                 show_benchmarks, show_fitness,  show_in_screen, save_to_disc):
    """
    plot front and pareto-optimal forntier
    :param pop: population of generation to check
    :param paretoprontier:
    :return:
    """
    # set-up deap library for optimization with 1 objective to minimize and 2 objectives to be maximized
    deap.creator.create("Fitness", deap.base.Fitness, weights=(1.0, 1.0, 1.0 ))  # maximize shilluette and calinski
    deap.creator.create("Individual", list, fitness=deap.creator.Fitness)

    #read_checkpoint
    cp = pickle.load(open(locator.get_calibration_cluster_opt_checkpoint(generation, building_name), "r"))
    frontier = cp[what_to_plot]


    # create figure
    fig = plt.figure()
    xs, ys, zs= map(np.array, zip(*[ind.fitness.values for ind in frontier]))

    scalarMap = cmx.ScalarMappable(norm=matplotlib.colors.Normalize(vmin=min(zs), vmax=max(zs)), cmap=plt.get_cmap('jet'))
    scalarMap.set_array(zs)
    fig.colorbar(scalarMap, label=labelz)

    ax = fig.add_subplot(111)
    ax.scatter(xs, ys, c=scalarMap.to_rgba(zs), s=50, alpha=0.8, vmin=0.0, vmax=1.0)
    ax.set_xlabel(labelx)
    ax.set_ylabel(labely)

    individuals = [str(ind) for ind in frontier]
    if show_fitness:
        for i, txt in enumerate(individuals):
            ax.annotate(txt, xy=(xs[i], ys[i]))

    if show_benchmarks:
        number_individuals = len(individuals )
        #convergence = cp['convergence']
        diversity = round(cp['diversity'],3)
        plt.title("No. individuals: "+str(number_individuals)+" Diversity: "+str(diversity))

    # get formatting
    plt.grid(True)
    #ax.set_xlim([0, 1])
    #ax.set_ylim([0, 1])
    plt.rcParams.update({'font.size': 16})
    plt.gcf().subplots_adjust(bottom=0.15)
    if save_to_disc:
        plt.savefig(os.path.join(locator.get_calibration_clustering_folder(),
                                 "plot_gen_"+str(generation)+"_building_name_"+building_name+".png"))
    if show_in_screen:
        plt.show()
    plt.clf()
    return

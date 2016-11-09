"""
===========================
Symbolic Aggregate approXimation in python.
Based on the paper A Symbolic Representation of Time Series, with Implications for Streaming Algorithms
Adapted from work og N. Hoffman published under MIT license.
===========================

"""
from __future__ import division

import math
import scipy.stats as stats

import numpy as np
from numpy import random

from deap import base, creator, tools
from sklearn.metrics import silhouette_score
from sklearn import metrics

import matplotlib.pyplot as plt

__author__ = "Nathan Hoffman"
__copyright__ = "Copyright (c) 2013 Nathan Hoffman"
__credits__ = ["Nathan Hoffman", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class SAX(object):
    """
    This class is for computing common things with the Symbolic
    Aggregate approXimation method.  In short, this translates
    a series of data to a string, which can then be compared with other
    such strings using a lookup table.
    """

    def __init__(self, wordSize = 8, alphabetSize = 7, epsilon = 1e-6):

        if alphabetSize < 3:
            raise "do not do that"
        self.aOffset = ord('a')
        self.wordSize = wordSize
        self.alphabetSize = alphabetSize
        self.eps = epsilon
        self.beta = list(stats.norm().ppf(np.linspace(0.01, 0.99, self.alphabetSize+1))[1:-1])
        self.build_letter_compare_dict()
        self.scalingFactor = 1

    def to_letter_rep(self, x):
        """
        Function takes a series of data, x, and transforms it to a string representation
        """
        (paaX, indices) = self.to_PAA(self.normalize(x))
        self.scalingFactor = np.sqrt((len(x) * 1.0) / (self.wordSize * 1.0))
        return self.alphabetize(paaX), indices

    def normalize(self, x):
        """
        Function will normalize an array (give it a mean of 0, and a
        standard deviation of 1) unless it's standard deviation is below
        epsilon, in which case it returns an array of zeros the length
        of the original array.
        """
        X = np.asanyarray(x)
        if X.std() < self.eps:
            return [0 for entry in X]
        return (X-X.mean())/X.std()

    def to_PAA(self, x):
        """
        Function performs Piecewise Aggregate Approximation on data set, reducing
        the dimension of the dataset x to w discrete levels. returns the reduced
        dimension data set, as well as the indicies corresponding to the original
        data for each reduced dimension
        """
        n = len(x)
        stepFloat = n/float(self.wordSize)
        step = int(math.ceil(stepFloat))
        frameStart = 0
        approximation = []
        indices = []
        i = 0
        while frameStart <= n-step:
            thisFrame = np.array(x[frameStart:int(frameStart + step)])
            approximation.append(np.mean(thisFrame))
            indices.append((frameStart, int(frameStart + step)))
            i += 1
            frameStart = int(i*stepFloat)
        return (np.array(approximation), indices)

    def alphabetize(self,paaX):
        """
        Converts the Piecewise Aggregate Approximation of x to a series of letters.
        """
        alphabetizedX = ''
        for i in range(0, len(paaX)):
            letterFound = False
            for j in range(0, len(self.beta)):
                if paaX[i] < self.beta[j]:
                    alphabetizedX += chr(self.aOffset + j)
                    letterFound = True
                    break
            if not letterFound:
                alphabetizedX += chr(self.aOffset + len(self.beta))
        return alphabetizedX

    def compare_strings(self, sA, sB):
        """
        Compares two strings based on individual letter distance
        Requires that both strings are the same length
        """
        if len(sA) != len(sB):
            raise StringsAreDifferentLength()
        list_letters_a = [x for x in sA]
        list_letters_b = [x for x in sB]
        mindist = 0.0
        for i in range(0, len(list_letters_a)):
            mindist += self.compare_letters(list_letters_a[i], list_letters_b[i])**2
        mindist = self.scalingFactor* np.sqrt(mindist)
        return mindist

    def compare_letters(self, la, lb):
        """
        Compare two letters based on letter distance return distance between
        """
        return self.compareDict[la+lb]

    def build_letter_compare_dict(self):
        """
        Builds up the lookup table to determine numeric distance between two letters
        given an alphabet size.  Entries for both 'ab' and 'ba' will be created
        and will have identical values.
        """

        number_rep = range(0,int(self.alphabetSize))
        letters = [chr(x + self.aOffset) for x in number_rep]
        self.compareDict = {}
        for i in range(0, len(letters)):
            for j in range(0, len(letters)):
                if np.abs(number_rep[i]-number_rep[j]) <=1:
                    self.compareDict[letters[i]+letters[j]] = 0
                else:
                    high_num = np.max([number_rep[i], number_rep[j]])-1
                    low_num = np.min([number_rep[i], number_rep[j]])
                    self.compareDict[letters[i]+letters[j]] = self.beta[high_num] - self.beta[low_num]

    def sliding_window(self, x, numSubsequences = None, overlappingFraction = None):
        if not numSubsequences:
            numSubsequences = 20
        self.windowSize = int(len(x)/numSubsequences)
        if not overlappingFraction:
            overlappingFraction = 0.9
        overlap = self.windowSize*overlappingFraction
        moveSize = int(self.windowSize - overlap)
        if moveSize < 1:
            raise OverlapSpecifiedIsNotSmallerThanWindowSize()
        ptr = 0
        n = len(x)
        windowIndices = []
        stringRep = []
        while ptr < n-self.windowSize+1:
            thisSubRange = x[ptr:ptr+self.windowSize]
            (thisStringRep,indices) = self.to_letter_rep(thisSubRange)
            stringRep.append(thisStringRep)
            windowIndices.append((ptr, ptr+self.windowSize))
            ptr += moveSize
        return (stringRep,windowIndices)

    def batch_compare(self, xStrings, refString):
        return [self.compare_strings(x, refString) for x in xStrings]

    def set_scaling_factor(self, scalingFactor):
        self.scalingFactor = scalingFactor

    def set_window_size(self, windowSize):
        self.windowSize = windowSize

def SAX_opt(data, time_series_len, BOUND_LOW, BOUND_UP, NGEN, MU, CXPB):
    """
    A multi-objective problem set for three objectives to maximize using the DEAP library and NSGAII algorithm:
    1. Compound function of accurracy, complexity and compression based on the work of
    D. Garcia-Lopez1 and H. Acosta-Mesa 2009
    2. Classic Shiluette and
    3. Carlinski indicators of clustering.

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
    creator.create("Fitness", base.Fitness, weights=(1.0, 1.0, 1.0))  # maximize shilluette and calinski
    creator.create("Individual", list, fitness=creator.Fitness)

    # set-up problem
    NDIM = 2

    def discrete_uniform(low, up, size=None):
        """
        This function creates a random distribution of the individuals
        :param low: low bound
        :param up: up bound
        :param size: none
        :return: vector with random generation of the individuals
        """
        try:
            return [random.randint(a, b) for a, b in zip(low, up)]
        except TypeError:
            return [random.randint(a, b) for a, b in zip([low] * size, [up] * size)]

    toolbox = base.Toolbox()
    toolbox.register("attr_float", discrete_uniform, BOUND_LOW, BOUND_UP, NDIM)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.attr_float)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    def evaluation(ind):
        """
        Evaluation Function for optimization
        :param ind: individual
        :return: resulting fitness value for the three objectives of the analysis.
        """
        s = SAX(ind[0], ind[1])
        sax = [s.to_letter_rep(array)[0] for array in data]
        accurracy = calc_gain(sax)
        complexity = calc_complexity(sax)
        compression = calc_num_cutpoints(ind[0], time_series_len)
        f1 = 0.9009*accurracy - 0.09*complexity - 0.0009*compression
        f2 = silhouette_score(data, sax)
        f3 = metrics.calinski_harabaz_score(data, sax)
        return f1, f2, f3

    toolbox.register("evaluate", evaluation)
    toolbox.register("mate", tools.cxTwoPoint)#tools.cxSimulatedBinaryBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0)
    toolbox.register("mutate", tools.mutUniformInt ,low=BOUND_LOW, up=BOUND_UP, indpb=1.0/NDIM)#tools.mutPolynomialBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0, indpb=1.0/NDIM)
    toolbox.register("select", tools.selNSGA2)

    # run optimization
    pop, stats = main_opt(toolbox, NGEN, MU, CXPB)

    # plot pareto curve
    optimal_front = np.array([list(ind.fitness.values) for ind in pop])
    n = [str(ind) for ind in pop]
    print len(n)
    print n, optimal_front
    fig, ax = plt.subplots()
    ax.scatter(optimal_front[:, 0], optimal_front[:, 1], c="r")
    for i, txt in enumerate(n):
        ax.annotate(txt, (optimal_front[i][0], optimal_front[i][1]))
    plt.axis("tight")
    plt.show()

    return


def main_opt(toolbox, NGEN = 100, MU = 100, CXPB = 0.9, seed=None):
    """
    main optimization call which provides the cross-over and mutation generation after generation
    this script is based on the example of the library DEAP of python and the algortighm NSGA-II
    :param toolbox: toolbox generated with evaluation, selection, mutation and crossover functions
    :param NGEN: number of maximum generations
    :param MU: number of initial individuals
    :param CXPB: level of confidence
    :param seed: seed.
    :return: pop = population with fitness values and individuals, stats = statistics of the population for the last
                    generation
    """

    random.seed(seed)
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

    return pop, stats

def calc_complexity(clusters_names):
    """
    Calculated according to 'Application of time series discretization using evolutionary programming for classification
    of precancerous cervical lesions' by H. Acosta-Mesa et al., 2014
    :param clusters_names: list containing a word which clusters the time series. e.g., ['abcffs', dddddd'...'svfdab']
    :return: level of complexity which penalizes the objective function
    """
    single_words_length = len(set(clusters_names))
    m = len(clusters_names) # number of observations
    C = 1 # number of classes is 1
    result = (single_words_length - C)/ (m+ C)
    return result

def calc_num_cutpoints(wordSize, time_series_len=24):
    """
    Calculated according to 'Application of time series discretization using evolutionary programming for classification
    of precancerous cervical lesions' by H. Acosta-Mesa et al., 2014
    :param wordSize: wordsize chossen for the SAX algorithm. integer.
    :param time_series_len: length of time_series group. integer
    :return: level of compression which penalizes the objective function
    """
    result = wordSize/(2*time_series_len) # 24 hours
    return result

def calc_entropy(clusters_names):
    """
    Calculated according to 'Application of time series discretization using evolutionary programming for classification
    of precancerous cervical lesions' by H. Acosta-Mesa et al., 2014
    :param clusters_names: list containing a word which clusters the time series. e.g., ['abcffs', dddddd'...'svfdab']
    :return:
    """
    single_words = list(set(clusters_names))
    n_clusters = len(clusters_names)
    entropy = 0
    for single_word in single_words:
        pi = clusters_names.count(single_word)/n_clusters
        entropy += -pi*math.log(pi, 2)
    return entropy

def calc_gain(clusters_names):
    """
    Calculated according to the value of information gain of "Discretization of Time Series Dataset
    with a Genetic Search' by D. Garcia-Lopez1 and H. Acosta-Mesa 2009.
    :param clusters_names: list containing a word which clusters the time series. e.g., ['abcffs', dddddd'...'svfdab']
    :return: gain = information gain [real]
    """
    single_words = list(set(clusters_names))
    n_clusters = len(clusters_names)
    entropy = 0

    for single_word in single_words:
        pi = clusters_names.count(single_word)/n_clusters
        entropy += -pi*math.log(pi, 2)

    entropy_values = 0
    all_values = ''.join(clusters_names)
    all_values_len = len(all_values)
    single_letters = list(set(all_values))

    for value in single_letters:
        value_in_clusters = len([s for s in clusters_names if value in s])
        pi = all_values.count(value)/ all_values_len
        entropy_values +=  value_in_clusters/n_clusters * -pi*math.log(pi, 2)
    gain = entropy - entropy_values
    return gain
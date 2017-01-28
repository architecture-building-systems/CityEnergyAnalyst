"""
=======================================
Selection of Pareto Optimal individuals
=======================================

"""

from __future__ import division
from deap import tools
import random
import numpy as np

from functools import partial
from operator import attrgetter

__author__ =  "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def assignCrowdingDist(individuals):
    """Assign a crowding distance to each individual's fitness. The
    crowding distance can be retrieve via the :attr:`crowding_dist`
    attribute of each individual's fitness.
    """
    if len(individuals) == 0:
        return

    distances = [0.0] * len(individuals)
    crowd = [(ind.fitness.values, i) for i, ind in enumerate(individuals)]

    nobj = len(individuals[0].fitness.values)

    for i in xrange(nobj):
        crowd.sort(key=lambda element: element[0][i])
        distances[crowd[0][1]] = float("inf")
        distances[crowd[-1][1]] = float("inf")
        if crowd[-1][0][i] == crowd[0][0][i]:
            continue
        norm = nobj * float(crowd[-1][0][i] - crowd[0][0][i])
        for prev, cur, next in zip(crowd[:-2], crowd[1:-1], crowd[2:]):
            distances[cur[1]] += (next[0][i] - prev[0][i]) / norm

    for i, dist in enumerate(distances):
        individuals[i].fitness.crowding_dist = dist

    return individuals


def tourn(ind1, ind2):
    if ind1.fitness.dominates(ind2.fitness):
        return ind1
    elif ind2.fitness.dominates(ind1.fitness):
        return ind2

    if ind1.fitness.crowding_dist < ind2.fitness.crowding_dist:
        return ind2
    elif ind1.fitness.crowding_dist > ind2.fitness.crowding_dist:
        return ind1

    if random.random() <= 0.5:
        return ind1
    return ind2



def selectPareto(pop,gv):
    """
    Select Pareto Optimal individuals in the population
    An individual is considered Pareto optimal if there exist no other
    individual by whom it is dominated.

    Parameters
    ----------
    pop : list
        List of individuals
    
    Returns
    -------
    selectedInd : list
        list of selected individuals

    """
    selectedInd = []
    # individuals_1 = []
    # individuals_2 = []
    a = gv.initialInd
    # selectedInd = assignCrowdingDist(pop)
    # print "selected ind \n"
    # print selectedInd
    #
    # for i in range(0, a, 1):
    #     if random.random() <= 0.5:
    #         individuals_1.append(selectedInd[i])
    #     else:
    #         individuals_2.append(selectedInd[i])
    #
    # # if random.random() <= 0.5:
    # #     individuals_1.append()
    # #
    # # individuals_1 = random.sample(selectedInd, a/2)
    # # individuals_2 = random.sample(selectedInd, a/2)
    # print individuals_1
    # print individuals_2
    # chosen = []
    # for i in xrange(0, a-1, 4):
    #     chosen.append(tourn(individuals_1[i],   individuals_1[i+1]))
    #     chosen.append(tourn(individuals_1[i+2], individuals_1[i+3]))
    #     chosen.append(tourn(individuals_2[i],   individuals_2[i+1]))
    #     chosen.append(tourn(individuals_2[i+2], individuals_2[i+3]))


    selectedInd = tools.selNSGA2(pop,a)

    # for i in xrange(a):
    #     aspirants = [random.choice(pop) for i in xrange(a)]
    #     selectedInd.append(max(aspirants, key=attrgetter("fitness")))

    return selectedInd
                














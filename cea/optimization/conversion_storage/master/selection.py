"""
=======================================
Selection of Pareto Optimal individuals
=======================================

"""

__author__ =  "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def selectPareto(pop):
    """
    Select Pareto Optimal individuals in the population
    An individual is considered Pareto optimal if there exist no other
    individual by whom it is dominated in any of the objective functions.

    Parameters
    ----------
    :param pop: list of individuals
    :type pop: list
    :return: list of selected individuals
    :rtype: list
    """
    selectedInd = list(pop)
    for ind in pop:
        if (ind in selectedInd):
            otherList = [el for el in selectedInd if el != ind]
            for other in otherList:
                if ind.fitness.dominates(other.fitness):
                    selectedInd.remove(other)
    
    return selectedInd
                














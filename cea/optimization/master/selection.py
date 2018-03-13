"""
=======================================
Selection of Pareto Optimal individuals
=======================================

"""

from __future__ import division
from deap import tools

__author__ =  "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Sreepathi Bhargava Krishna", "Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def selectPareto(pop, initialind):
    """
    Select Pareto Optimal individuals in the population
    An individual is considered Pareto optimal if there exist no other
    individual by whom it is dominated in any of the objective functions.

    :param pop: list of individuals
    :param gv: global variables
    :type pop: list
    :type gv: class
    :return: list of selected individuals
    :rtype: list
    """
    selectedInd = []
    selectedInd = tools.selNSGA2(pop,initialind)


    return selectedInd
                














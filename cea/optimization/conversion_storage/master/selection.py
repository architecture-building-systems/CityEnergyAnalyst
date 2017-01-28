"""
=======================================
Selection of Pareto Optimal individuals
=======================================

"""

from __future__ import division
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
    a = gv.initialInd

    for i in xrange(a):
        aspirants = [random.choice(pop) for i in xrange(a)]
        selectedInd.append(max(aspirants, key=attrgetter("fitness")))

    return selectedInd
                














"""
This class defines how the fitness of an individual of the optimisation algorithm is evaluated. This is a copy of
the deap.base.Fitness class.
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2023, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"

from deap import base

class Fitness(base.Fitness):
    weights = ()

    @staticmethod
    def initialize_class_variables(domain):
        Fitness.weights = (-1.0,) * len(domain.config.optimization_new.objective_functions)
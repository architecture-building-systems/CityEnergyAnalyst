"""
This class contains the most important information on the optimisation algorithm, such as the type of algorithm that
is used, the population size etc.
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2023, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"

from math import factorial


class Algorithm(object):
    objectives = []

    @staticmethod
    def initialize_class_variables(domain):
        Algorithm.objectives = domain.config.optimization_new.objective_functions


class GeneticAlgorithm(Algorithm):

    def __init__(self, selection=None, mutation='UniformBounded', crossover='TwoPoint', population_size=None,
                 number_of_generations=None, mut_probability=0.1, cx_probability=0.3, mut_eta=0.5):
        self.nbr_objectives = len(Algorithm.objectives)
        self.selection = selection
        self.mutation = mutation
        self.crossover = crossover

        self.population = population_size
        self.generations = number_of_generations

        self.mut_prob = mut_probability
        self.cx_prob = cx_probability
        self.mut_eta = mut_eta

    @property
    def population(self):
        return self._population

    @population.setter
    def population(self, new_population_size):
        """
        Set the population size depending on the chosen genetic algorithm or user input
        """
        if new_population_size:
            population = new_population_size
        elif self.selection == 'NSGAIII':
            NOBJ = self.nbr_objectives
            P = 12
            H = factorial(NOBJ + P - 1) / (factorial(P) * factorial(NOBJ - 1))
            population = int(H + (4 - H % 4))
        elif not self.selection:
            population = 1
        else:
            raise ValueError("The optimisation algorithm is not set to a non-dominated-sorting genetic algorithm "
                             "(NSGAIII). The population size therefore can't be calculated automatically and needs to "
                             "be set in the advanced settings.")

        self._population = population

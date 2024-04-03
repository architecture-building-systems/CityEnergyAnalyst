# -*- coding: utf-8 -*-
"""
The class in this script offers a container structure for energy system configurations that are tested in the
genetic optimisation algorithm using the deap-library.
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2023, Architecture and Buildings Systems - ETH Zurich"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"


from deap.base import Fitness

from cea.constants import DH_ACRONYM, DC_ACRONYM


class Individual(list):

    def __init__(self, system_encoding):

        super().__init__(system_encoding)
        self.typecode = 'd'
        self.fitness = FitnessMin()


class FitnessMin(Fitness):

    objective_function_selection = []
    nbr_of_objectives = 0

    def __init__(self):

        self.weights = (-1.0, ) * FitnessMin.nbr_of_objectives
        super().__init__()


    @staticmethod
    def set_objective_function_selection(cea_config):
        objective_function_selection = []
        if cea_config.optimization.network_type == DC_ACRONYM:
            objective_function_selection = cea_config.optimization.objective_functions_DC
        elif cea_config.optimization.network_type == DH_ACRONYM:
            objective_function_selection = ['cost', 'GHG_emissions']

        FitnessMin.objective_function_selection = objective_function_selection
        FitnessMin.nbr_of_objectives = len(objective_function_selection)

        return objective_function_selection

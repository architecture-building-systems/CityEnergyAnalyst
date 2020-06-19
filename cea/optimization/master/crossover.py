"""
Crossover routines

"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

from deap import tools

from cea.optimization.master.validation import validation_main
from cea.optimization.master.individual import IndividualList, IndividualBlueprint, IndividualDict
from typing import Tuple

class CrossOverMethodsInteger(object):
    """
    mutation methods for integers
    """

    def __init__(self, crossover_method):
        self.method = crossover_method

    def crossover(self, individual_1, individual_2, probability):
        if self.method == 'Uniform':
            return tools.cxUniform(individual_1,
                                   individual_2,
                                   probability)
        elif self.method == 'TwoPoint':
            return tools.cxESTwoPoint(individual_1,
                                      individual_2)
        elif self.method == 'PartialyMatched':
            return tools.cxPartialyMatched(individual_1,
                                           individual_2)
        elif self.method == 'UniformPartialyMatched':
            return tools.cxUniformPartialyMatched(individual_1, individual_2, probability)

class CrossOverMethodsContinuous(object):
    """
        mutation methods for integers
      """

    def __init__(self, crossover_method):
        self.method = crossover_method

    def crossover(self, individual_1, individual_2, probability):
        if self.method == 'Uniform':
            return tools.cxUniform(individual_1,
                                   individual_2,
                                   probability)
        elif self.method == 'TwoPoint':
            return tools.cxESTwoPoint(individual_1,
                                      individual_2)


def crossover_main(ind1: IndividualList,
                   ind2: IndividualList,
                   cx_prob: float,
                   blueprint: IndividualBlueprint,
                   crossover_method_integer,
                   crossover_method_continuous
                   ) -> Tuple[IndividualList, IndividualList]:
    crossover_integer = CrossOverMethodsInteger(crossover_method_integer)
    crossover_continuous = CrossOverMethodsContinuous(crossover_method_continuous)

    # create dict of individual with his/her name
    ind1_with_name_dict = IndividualDict.from_individual_list(ind1, blueprint)
    ind2_with_name_dict = IndividualDict.from_individual_list(ind2, blueprint)

    # MUTATE BUILDINGS CONNECTED
    connections_ind1 = [ind1_with_name_dict[column] for column in blueprint.buildings]
    connections_ind2 = [ind2_with_name_dict[column] for column in blueprint.buildings]
    connections_ind1, connections_ind2 = crossover_integer.crossover(connections_ind1, connections_ind2, cx_prob)

    # apply back to the individual
    for i, building in enumerate(blueprint.buildings):
        ind1_with_name_dict[building] = connections_ind1[i]
        ind2_with_name_dict[building] = connections_ind2[i]

    # MUTATE SUPPLY SYSTEM UNITS SHARE
    tech_share_ind1 = [ind1_with_name_dict[column] for column in blueprint.tech_names_share]
    tech_share_ind2 = [ind2_with_name_dict[column] for column in blueprint.tech_names_share]
    tech_share_ind1, tech_share_ind2 = crossover_continuous.crossover(tech_share_ind1, tech_share_ind2, cx_prob)

    # apply back to the individual
    for i, tech in enumerate(blueprint.tech_names_share):
        ind1_with_name_dict[tech] = tech_share_ind1[i]
        ind2_with_name_dict[tech] = tech_share_ind2[i]

    # validate the individuals
    ind1_with_name_dict = validation_main(ind1_with_name_dict, blueprint)
    ind2_with_name_dict = validation_main(ind2_with_name_dict, blueprint)

    # now pass all the values mutated to the original individual
    # NOTE: ind1 is actually of type "toolbox.Individual" (or similar) and not strictly an IndividualList...
    ind1 = ind1_with_name_dict.to_individual_list(blueprint, ind1)
    ind2 = ind2_with_name_dict.to_individual_list(blueprint, ind2)
    return ind1, ind2

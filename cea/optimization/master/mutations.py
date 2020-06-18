"""
Mutation routines

"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

from deap import tools

from cea.optimization.master.validation import validation_main
from optimization.master.individual import IndividualList, IndividualBlueprint, IndividualDict
from typing import Tuple


class MutationMethodInteger(object):
    """
        mutation methods for integers
      """

    def __init__(self, mutation_method):
        self.method = mutation_method

    def mutate(self, individual, probability):
        if self.method == 'Shuffle':
            return tools.mutShuffleIndexes(individual, probability)[0]
        elif self.method == 'Flipbit':
            return tools.mutFlipBit(individual, probability)[0]

class MutationMethodContinuos(object):
    """
        mutation methods for continuos variables
      """
    def __init__(self, mutation_method):
        self.method = mutation_method

    def mutate(self, individual, probability):
        if self.method == 'Polynomial':
            return tools.mutPolynomialBounded(individual, eta=20.0, low=0.0, up=1.0, indpb=1 / len(individual))[0]
        elif self.method == 'Shuffle':
            return tools.mutShuffleIndexes(individual, probability)[0]


def mutation_main(individual: IndividualList,
                  mut_prob: float,
                  blueprint: IndividualBlueprint,
                  mutation_method_integer: str,
                  mutation_method_continuous: str) -> Tuple[IndividualList]:
    mutation_integer = MutationMethodInteger(mutation_method_integer)
    mutation_continuous = MutationMethodContinuos(mutation_method_continuous)

    # create dict of individual with his/her name
    individual_dict = IndividualDict.from_individual_list(individual, blueprint)

    # MUTATE BUILDINGS CONNECTED
    connections = [individual_dict[column] for column in blueprint.buildings]
    connections_mutated = mutation_integer.mutate(connections, mut_prob)
    for building, mutated_value in zip(blueprint.buildings, connections_mutated):
        individual_dict[building] = mutated_value

    # MUTATE SUPPLY SYSTEM UNITS SHARE
    tech_share = [individual_dict[tech] for tech in blueprint.tech_names_share]
    tech_share_mutated = mutation_continuous.mutate(tech_share, mut_prob)
    for tech, mutated_value in zip(blueprint.tech_names_share, tech_share_mutated):
        individual_dict[tech] = mutated_value

    # now validate individual
    individual_dict = validation_main(individual_dict, blueprint)

    # now pass all the values mutated to the original individual
    individual = individual_dict.to_individual_list(blueprint)
    return (individual,)  # add the, because deap needs this (deap requires a tuple result)

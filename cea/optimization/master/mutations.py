"""
Mutation routines

"""




from deap import tools

from cea.optimization.master.validation import validation_main


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
        mutation methods for continuous variables
      """
    def __init__(self, mutation_method):
        self.method = mutation_method

    def mutate(self, individual, probability):
        if self.method == 'Polynomial':
            return tools.mutPolynomialBounded(individual, eta=20.0, low=0.0, up=1.0, indpb=1 / len(individual))[0]
        elif self.method == 'Shuffle':
            return tools.mutShuffleIndexes(individual, probability)[0]


def mutation_main(individual,
                  indpb,
                  column_names,
                  heating_unit_names_share,
                  cooling_unit_names_share,
                  column_names_buildings_heating,
                  column_names_buildings_cooling,
                  district_heating_network,
                  district_cooling_network,
                  technologies_heating_allowed,
                  technologies_cooling_allowed,
                  mutation_method_integer,
                  mutation_method_continuous
                  ):
    mutation_integer = MutationMethodInteger(mutation_method_integer)
    mutation_continuous = MutationMethodContinuos(mutation_method_continuous)
    # create dict of individual with his/her name
    individual_with_name_dict = dict(zip(column_names, individual))

    if district_heating_network:

        # MUTATE BUILDINGS CONNECTED
        buildings_heating = [individual_with_name_dict[column] for column in column_names_buildings_heating]
        # apply mutations
        buildings_heating_mutated = mutation_integer.mutate(buildings_heating, indpb)
        # take back to the individual
        for column, mutated_value in zip(column_names_buildings_heating, buildings_heating_mutated):
            individual_with_name_dict[column] = mutated_value

        # MUTATE SUPPLY SYSTEM UNITS SHARE
        heating_units_share = [individual_with_name_dict[column] for column in heating_unit_names_share]
        # apply mutations
        heating_units_share_mutated = mutation_continuous.mutate(heating_units_share, indpb)
        # takeback to the individual
        for column, mutated_value in zip(heating_unit_names_share, heating_units_share_mutated):
            individual_with_name_dict[column] = mutated_value

    if district_cooling_network:

        # MUTATE BUILDINGS CONNECTED
        buildings_cooling = [individual_with_name_dict[column] for column in column_names_buildings_cooling]
        # apply mutations
        buildings_cooling_mutated = mutation_integer.mutate(buildings_cooling, indpb)
        # take back to the individual
        for column, mutated_value in zip(column_names_buildings_cooling, buildings_cooling_mutated):
            individual_with_name_dict[column] = mutated_value

        # MUTATE SUPPLY SYSTEM UNITS SHARE
        cooling_units_share = [individual_with_name_dict[column] for column in cooling_unit_names_share]
        # NDIM = len(cooling_units_share)
        # apply mutations
        cooling_units_share_mutated = mutation_continuous.mutate(cooling_units_share, indpb)
        # takeback to the individual
        for column, mutated_value in zip(cooling_unit_names_share, cooling_units_share_mutated):
            individual_with_name_dict[column] = mutated_value

    # now validate individual
    individual_with_name_dict = validation_main(individual_with_name_dict,
                                                column_names_buildings_heating,
                                                column_names_buildings_cooling,
                                                district_heating_network,
                                                district_cooling_network,
                                                technologies_heating_allowed,
                                                technologies_cooling_allowed,
                                                )

    # now pass all the values mutated to the original individual
    for i, column in enumerate(column_names):
        individual[i] = individual_with_name_dict[column]

    return individual,  # add the, because deap needs this

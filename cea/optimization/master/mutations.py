"""
Mutation routines

"""
from __future__ import division

from deap import tools

from cea.optimization.master.validation import validation_main


def mutation_main(individual, indpb,
                  column_names,
                  heating_unit_names_share,
                  cooling_unit_names_share,
                  column_names_buildings_heating,
                  column_names_buildings_cooling,
                  district_heating_network,
                  district_cooling_network
                  ):
    # create dict of individual with his/her name
    individual_with_name_dict = dict(zip(column_names, individual))

    if district_heating_network:

        # MUTATE BUILDINGS CONNECTED
        buildings_heating = [individual_with_name_dict[column] for column in column_names_buildings_heating]
        # apply mutations
        buildings_heating_mutated = tools.mutFlipBit(buildings_heating, indpb)[0]
        # take back to the individual
        for column, mutated_value in zip(column_names_buildings_heating, buildings_heating_mutated):
            individual_with_name_dict[column] = mutated_value

        # MUTATE SUPPLY SYSTEM UNITS SHARE
        heating_units_share = [individual_with_name_dict[column] for column in heating_unit_names_share]
        # apply mutations
        heating_units_share_mutated = tools.mutShuffleIndexes(heating_units_share, indpb=indpb)[0]
        # takeback to teh individual
        for column, mutated_value in zip(heating_unit_names_share, heating_units_share_mutated):
            individual_with_name_dict[column] = mutated_value

    if district_cooling_network:

        # MUTATE BUILDINGS CONNECTED
        buildings_cooling = [individual_with_name_dict[column] for column in column_names_buildings_cooling]
        # apply mutations
        buildings_cooling_mutated = tools.mutFlipBit(buildings_cooling, indpb)[0]
        # take back to teh individual
        for column, mutated_value in zip(column_names_buildings_cooling, buildings_cooling_mutated):
            individual_with_name_dict[column] = mutated_value

        # MUTATE SUPPLY SYSTEM UNITS SHARE
        cooling_units_share = [individual_with_name_dict[column] for column in cooling_unit_names_share]
        # apply mutations
        cooling_units_share_mutated = tools.mutShuffleIndexes(cooling_units_share, indpb)[0]
        # takeback to teh individual
        for column, mutated_value in zip(cooling_unit_names_share, cooling_units_share_mutated):
            individual_with_name_dict[column] = mutated_value

    # now validate individual
    individual_with_name_dict = validation_main(individual_with_name_dict,
                                                column_names_buildings_heating,
                                                column_names_buildings_cooling,
                                                district_heating_network,
                                                district_cooling_network
                                                )

    # now pass all the values mutated to the original individual
    for i, column in enumerate(column_names):
        individual[i] = individual_with_name_dict[column]

    return individual,  # add the, because deap needs this

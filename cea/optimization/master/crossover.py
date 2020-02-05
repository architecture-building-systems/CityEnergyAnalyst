"""
Crossover routines

"""
from __future__ import division

from deap import tools

from cea.optimization.master.validation import validation_main


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

def crossover_main(ind1, ind2, indpb,
                   column_names,
                   heating_unit_names_share,
                   cooling_unit_names_share,
                   column_names_buildings_heating,
                   column_names_buildings_cooling,
                   district_heating_network,
                   district_cooling_network,
                   technologies_heating_allowed,
                   technologies_cooling_allowed,
                   crossover_method_integer,
                   crossover_method_continuous
                   ):
    crossover_integer = CrossOverMethodsInteger(crossover_method_integer)
    crossover_continuous = CrossOverMethodsContinuous(crossover_method_continuous)

    # create dict of individual with his/her name
    ind1_with_name_dict = dict(zip(column_names, ind1))
    ind2_with_name_dict = dict(zip(column_names, ind2))

    if district_heating_network:

        # MUTATE BUILDINGS CONNECTED
        buildings_heating_ind1 = [ind1_with_name_dict[column] for column in column_names_buildings_heating]
        buildings_heating_ind2 = [ind2_with_name_dict[column] for column in column_names_buildings_heating]
        # apply crossover
        buildings_heating_ind1, \
        buildings_heating_ind2 = crossover_integer.crossover(buildings_heating_ind1,
                                                             buildings_heating_ind2,
                                                             indpb)
        # take back to the individual
        for column, cross_over_value in zip(column_names_buildings_heating, buildings_heating_ind1):
            ind1_with_name_dict[column] = cross_over_value
        for column, cross_over_value in zip(column_names_buildings_heating, buildings_heating_ind2):
            ind2_with_name_dict[column] = cross_over_value

        # MUTATE SUPPLY SYSTEM UNITS SHARE
        heating_units_share_ind1 = [ind1_with_name_dict[column] for column in heating_unit_names_share]
        heating_units_share_ind2 = [ind2_with_name_dict[column] for column in heating_unit_names_share]
        # apply crossover
        heating_units_share_ind1, \
        heating_units_share_ind2 = crossover_continuous.crossover(heating_units_share_ind1,
                                                                  heating_units_share_ind2,
                                                                  indpb)
        # takeback to the individual
        for column, cross_over_value in zip(heating_unit_names_share, heating_units_share_ind1):
            ind1_with_name_dict[column] = cross_over_value
        for column, cross_over_value in zip(heating_unit_names_share, heating_units_share_ind2):
            ind2_with_name_dict[column] = cross_over_value

    if district_cooling_network:

        # CROSSOVER BUILDINGS CONNECTED
        buildings_cooling_ind1 = [ind1_with_name_dict[column] for column in column_names_buildings_cooling]
        buildings_cooling_ind2 = [ind2_with_name_dict[column] for column in column_names_buildings_cooling]
        # apply crossover
        buildings_cooling_ind1, \
        buildings_cooling_ind2 = crossover_integer.crossover(buildings_cooling_ind1,
                                                             buildings_cooling_ind2,
                                                             indpb)
        # take back to teh individual
        for column, cross_over_value in zip(column_names_buildings_cooling, buildings_cooling_ind1):
            ind1_with_name_dict[column] = cross_over_value
        for column, cross_over_value in zip(column_names_buildings_cooling, buildings_cooling_ind2):
            ind2_with_name_dict[column] = cross_over_value

        # CROSSOVER SUPPLY SYSTEM UNITS SHARE
        cooling_units_share_ind1 = [ind1_with_name_dict[column] for column in cooling_unit_names_share]
        cooling_units_share_ind2 = [ind2_with_name_dict[column] for column in cooling_unit_names_share]
        # apply crossover
        cooling_units_share_ind1, \
        cooling_units_share_ind2 = crossover_continuous.crossover(cooling_units_share_ind1,
                                                                  cooling_units_share_ind2,
                                                                  indpb)
        # takeback to teh individual
        for column, cross_over_value in zip(cooling_unit_names_share, cooling_units_share_ind1):
            ind1_with_name_dict[column] = cross_over_value
        for column, cross_over_value in zip(cooling_unit_names_share, cooling_units_share_ind2):
            ind2_with_name_dict[column] = cross_over_value

    # now validate individual
    # now validate individual
    ind1_with_name_dict = validation_main(ind1_with_name_dict,
                                          column_names_buildings_heating,
                                          column_names_buildings_cooling,
                                          district_heating_network,
                                          district_cooling_network,
                                          technologies_heating_allowed,
                                          technologies_cooling_allowed,
                                          )

    ind2_with_name_dict = validation_main(ind2_with_name_dict,
                                          column_names_buildings_heating,
                                          column_names_buildings_cooling,
                                          district_heating_network,
                                          district_cooling_network,
                                          technologies_heating_allowed,
                                          technologies_cooling_allowed,
                                          )

    # now pass all the values mutated to the original individual
    for i, column in enumerate(column_names):
        ind1[i] = ind1_with_name_dict[column]

    for i, column in enumerate(column_names):
        ind2[i] = ind2_with_name_dict[column]

    return ind1, ind2

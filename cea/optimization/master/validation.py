"""
Validation

"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import random

from cea.optimization.constants import (DH_CONVERSION_TECHNOLOGIES_WITH_SPACE_RESTRICTIONS,
                                        DH_CONVERSION_TECHNOLOGIES_SHARE, DC_CONVERSION_TECHNOLOGIES_SHARE,
                                        DC_CONVERSION_TECHNOLOGIES_WITH_SPACE_RESTRICTIONS)
from typing import Dict, Union, List
from .master_main import IndividualBlueprint, IndividualDict


def validation_main(individual_with_name_dict: IndividualDict,
                    column_names_individual: IndividualBlueprint) -> IndividualDict:
    validate_buildings_value(individual_with_name_dict, column_names_individual.buildings)
    validate_network_connections(individual_with_name_dict,
                                 column_names_individual.buildings)

    validate_minimum_limit(individual_with_name_dict, column_names_individual)
    validate_sum_technology_shares(individual_with_name_dict, column_names_individual)
    return individual_with_name_dict


def validate_sum_technology_shares(individual_with_name_dict: IndividualDict,
                                   column_names_individual: IndividualBlueprint):
    """
    Make sure the sum of the solar technology shares is not greater than 1.0

    :param individual_with_name_dict:
    :param column_names_individual:
    :return:
    """
    # FOR SUPPLY SYSTEMS SHARE - The share of solar technologies should be 1 (because they share the same area)
    unit_name, unit_share = [], []
    for technology_name, limits in column_names_individual.conversion_technologies.items():
        if technology_name in column_names_individual.tech_names_share:
            minimum = limits["minimum"]
            if individual_with_name_dict[
                technology_name] >= minimum and technology_name in column_names_individual.conversion_technologies_with_space_restrictions:  # only if the unit is activated
                unit_name.append(technology_name)
                unit_share.append(individual_with_name_dict[technology_name])
    sum_shares = sum(unit_share)
    if sum_shares > 1.0:  # only i the case that the sum of shares is more than the maximum of 1.0
        normalized_shares = [round(i / sum_shares, 2) for i in unit_share]
        for column, share in zip(unit_name, normalized_shares):
            individual_with_name_dict[column] = share


def validate_minimum_limit(individual_with_name_dict: IndividualDict,
                           column_names_individual: IndividualBlueprint):
    # FOR SUPPLY SYSTEMS SHARE - turn off if they are below the minimum (trick to avoid strings with on - off
    # behavior
    for technology_name, limits in column_names_individual.conversion_technologies.items():
        if technology_name in column_names_individual.tech_names_share:
            minimum = limits["minimum"]
            if individual_with_name_dict[technology_name] < minimum:
                individual_with_name_dict[technology_name] = 0.0  # 0.0 denotes off
            else:
                individual_with_name_dict[technology_name] = round(individual_with_name_dict[technology_name], 2)


def validate_network_connections(individual_with_name_dict: IndividualDict,
                                 column_names_buildings: List[str]):
    """
    Ensure that at least two buildings are connected to the network.

    NOTE: This function exploits the fact that we use {0, 1} to denote the connections

    :param individual_with_name_dict: The individual to validate (modified!)
    :param column_names_buildings: the names of the genes that represent building connections
    """
    assert len(column_names_buildings) >= 2, "Can't create a network with less than 2 buildings"

    # FOR BUILDINGS CONNECTIONS - constrains that at least 2 buildings should be connected to the network
    lim_inf = 0
    lim_sup = 1
    connections = [individual_with_name_dict[building_name] for building_name in column_names_buildings]
    if sum(connections) < 2:
        # connect a random unconnected building
        unconnected_buildings = [building_name for building_name in column_names_buildings
                                 if individual_with_name_dict[building_name] == 0]
        the_chosen_one = random.choice(unconnected_buildings)
        individual_with_name_dict[the_chosen_one] = 1

    # logically, this should always be true
    assert sum([individual_with_name_dict[building_name] for building_name in column_names_buildings]) >= 2


def validate_buildings_value(individual_with_name_dict: IndividualDict,
                             column_names_buildings: List[str]):
    """
    Ensure that the values for buildings in the individual are either 0 (disconnected) or 1 (connected)
    :param individual_with_name_dict: maps "gene" names to "gene" values
    :param column_names_buildings: The column names for building genes in the individual dict
    :return:
    """
    # FOR BUILDINGS CONNECTIONS - they should be inside the range
    valid_values = {0, 1}
    for building_name in column_names_buildings:
        if not individual_with_name_dict[building_name] in valid_values:
            individual_with_name_dict[building_name] = random.choice(list(valid_values))
"""
Create individuals

"""
from __future__ import division

import random

from cea.optimization.constants import DH_CONVERSION_TECHNOLOGIES_NAMES, \
    DH_CONVERSION_TECHNOLOGIES_NAMES_SHARE, \
    DC_CONVERSION_TECHNOLOGIES_NAMES, \
    DC_CONVERSION_TECHNOLOGIES_NAMES_SHARE, \
    DH_TECHNOLOGIES_SHARING_SPACE, DC_TECHNOLOGIES_SHARING_SPACE
from cea.optimization.master.validation import validation_main

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def generate_main(individual_with_names_dict,
                  column_names,
                  heating_unit_names,
                  cooling_unit_names,
                  heating_unit_names_share,
                  cooling_unit_names_share,
                  column_names_buildings_heating,
                  column_names_buildings_cooling,
                  district_heating_network,
                  district_cooling_network):
    """
    Creates an individual configuration for the evolutionary algorithm.
    The individual is divided into four parts namely Heating technologies, Cooling Technologies, Heating Network
    and Cooling Network
    Heating Technologies: This block consists of heating technologies associated with % of the peak capacity each
    technology is going to supply, i.e. 10.1520.2030, which translates into technology 1 corresponding to 15% of peak
    capacity, technology 2 corresponding to 20% and technology 3 corresponding to 0%. 0% can also be just done by replacing
    3 with 0. The technologies block is then followed by supply temperature of the DHN and the number of units it is
    supplied to among AHU, ARU, SHU. So if it is 6 degrees C supplied by DHN to AHU and ARU, it is represented as 6.02.
    The temperature is represented with 1 decimal point.
    Cooling Technologies: This follows the same syntax as heating technologies, but will be represented with cooling
    technologies. The block length of heating and cooling can be different.
    Heating Network: Network of buildings connected to centralized heating
    Cooling Network: Network of buildings connected to centralized cooling. Both these networks can be different, and will
    always have a fixed length corresponding to the total number of buildings in the neighborhood
    :param nBuildings: number of buildings
    :param gv: global variables class
    :type nBuildings: int
    :type gv: class
    :return: individual: representation of values taken by the individual
    :rtype: list
    """

    # POPULATE INDIVIDUAL WE KEEP A DATAFRAME SO IT IS EASIER FOR THE PROGRAMMER TO KNOW WHAT IS GOING ON
    if district_heating_network and district_cooling_network:
        populated_individual_with_name_dict = populate_individual(individual_with_names_dict,
                                                      DH_CONVERSION_TECHNOLOGIES_NAMES,
                                                      DH_CONVERSION_TECHNOLOGIES_NAMES_SHARE,
                                                      column_names_buildings_heating)

        populated_individual_with_name_dict = populate_individual(populated_individual_with_name_dict,
                                                      DC_CONVERSION_TECHNOLOGIES_NAMES,
                                                      DC_CONVERSION_TECHNOLOGIES_NAMES_SHARE,
                                                      column_names_buildings_cooling)
    elif district_heating_network:
        populated_individual_with_name_dict = populate_individual(individual_with_names_dict,
                                                      DH_CONVERSION_TECHNOLOGIES_NAMES,
                                                      DH_CONVERSION_TECHNOLOGIES_NAMES_SHARE,
                                                      column_names_buildings_heating)
    elif district_cooling_network:
        populated_individual_with_name_dict = populate_individual(individual_with_names_dict,
                                                      DC_CONVERSION_TECHNOLOGIES_NAMES,
                                                      DC_CONVERSION_TECHNOLOGIES_NAMES_SHARE,
                                                      column_names_buildings_cooling)

    populated_individual_with_name_dict = validation_main(populated_individual_with_name_dict,
                                              heating_unit_names,
                                              cooling_unit_names,
                                              heating_unit_names_share,
                                              cooling_unit_names_share,
                                              column_names_buildings_heating,
                                              column_names_buildings_cooling,
                                              district_heating_network,
                                              district_cooling_network
                                              )

    # CONVERT BACK INTO AN INDIVIDUAL STRING IMPORTANT TO USE column_names to keep the order
    individual = []
    for column in column_names:
        individual.append(populated_individual_with_name_dict[column])

    return individual


def populate_individual(empty_individual_with_names_dict,
                        name_conversion_technologies,
                        name_share_conversion_technologies,
                        columns_buildings_name):

    # do it for units that are activated
    for column, limits in name_conversion_technologies:
        lim_inf = limits[0]
        lim_sup = limits[1]
        empty_individual_with_names_dict[column] = random.randint(lim_inf, lim_sup)

    # do it for the share of the units that are activated
    for column, limits in name_share_conversion_technologies:
        lim_inf = limits[0]
        lim_sup = limits[1]
        empty_individual_with_names_dict[column] = random.uniform(lim_inf, lim_sup)

    # do it for the buildings
    for column in columns_buildings_name:
        empty_individual_with_names_dict[column] = random.randint(0, 1)

    return empty_individual_with_names_dict

def individual_to_barcode(individual, column_names, column_names_buildings_heating,
                          column_names_buildings_cooling):
    """
    Reads the 0-1 combination of connected/disconnected buildings
    and creates a list of strings type barcode i.e. ("12311111123012")
    :param individual: list containing the combination of connected/disconnected buildings
    :type individual: list
    :return: indCombi: list of strings
    :rtype: list
    """
    # pair individual values with their names
    individual_with_name_dict = dict(zip(column_names, individual))
    DHN_barcode = ""
    for name in column_names_buildings_heating:
        if name in individual_with_name_dict.keys():
            DHN_barcode += str(int(individual_with_name_dict[name]))

    DCN_barcode = ""
    for name in column_names_buildings_cooling:
        if name in individual_with_name_dict.keys():
            DCN_barcode += str(int(individual_with_name_dict[name]))

    return DHN_barcode, DCN_barcode, individual_with_name_dict


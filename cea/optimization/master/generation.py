"""
Create individuals

"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import random

from cea.optimization.constants import DH_CONVERSION_TECHNOLOGIES_SHARE, DC_CONVERSION_TECHNOLOGIES_SHARE
from cea.optimization.master.validation import validation_main
from cea.optimization.master.master_main import IndividualBlueprint, IndividualDict, IndividualList
from typing import Dict, Union, List, Any

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def generate_main(individual_dict: IndividualDict,
                  blueprint: IndividualBlueprint) -> IndividualList:
    """
    Creates an individual configuration for the evolutionary algorithm.
    The individual is divided into four parts namely Heating technologies, Cooling Technologies, Heating Network
    and Cooling Network

    FIXME: This description below seems to be outdated - from an era when we used strings to represent the individuals
    It looks like we now just have a list of floats and ints, with floats representing the ratios and the ints
    representing building connections to the network.

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
    :type nBuildings: int
    :return: individual: representation of values taken by the individual
    :rtype: list
    """

    # POPULATE INDIVIDUAL WE KEEP A DATAFRAME SO IT IS EASIER FOR THE PROGRAMMER TO KNOW WHAT IS GOING ON
    populated_individual_dict = populate_individual(individual_dict, blueprint)
    populated_individual_dict = validation_main(populated_individual_dict, blueprint)

    # CONVERT BACK INTO AN INDIVIDUAL STRING IMPORTANT TO USE column_names to keep the order
    return populated_individual_dict.to_individual_list(blueprint)


def populate_individual(empty_individual_with_names_dict: IndividualDict,
                        column_names_individual: IndividualBlueprint, ) -> IndividualDict:
    # do it for the share of the units that are activated
    for tech in column_names_individual.tech_names_share:
        empty_individual_with_names_dict[tech] = round(random.uniform(0.0, 1.0), 2)

    # do it for the buildings
    for building in column_names_individual.buildings:
        empty_individual_with_names_dict[building] = random.randint(0, 1)

    return empty_individual_with_names_dict


def individual_to_barcode(individual: IndividualList,
                          blueprint: IndividualBlueprint,
                          building_names_all,
                          building_names_heating,
                          building_names_cooling):
    """
    Reads the 0-1 combination of connected/disconnected buildings
    and creates a list of strings type barcode i.e. ("12311111123012")
    :param individual: list containing the combination of connected/disconnected buildings
    :type individual: list
    :return: indCombi: list of strings
    :rtype: list
    """
    # pair individual values with their names
    individual_dict = IndividualDict.from_individual_list(individual, blueprint)

    # FIXME: remove the network distinction - we only ever do one type of network!
    if blueprint.district_heating_network:
        DHN_barcode = "".join(str(individual_dict[building]) for building in blueprint.buildings)
        DCN_barcode = ""
    else:
        DHN_barcode = ""
        DCN_barcode = "".join(str(individual_dict[building]) for building in blueprint.buildings)

    # calc building connectivity
    building_connectivity_dict = calc_building_connectivity_dict(building_names_all,
                                                                 building_names_heating,
                                                                 building_names_cooling,
                                                                 DHN_barcode,
                                                                 DCN_barcode)

    return DHN_barcode, DCN_barcode, individual_dict, building_connectivity_dict


def calc_building_connectivity_dict(building_names_all,
                                    building_names_heating,
                                    building_names_cooling,
                                    DHN_barcode,
                                    DCN_barcode):
    data_heating_connections = []
    data_cooling_connections = []
    data_connectivity_heating = dict(zip(building_names_heating, DHN_barcode))
    data_connectivity_cooling = dict(zip(building_names_cooling, DCN_barcode))
    for building in building_names_all:
        if building in data_connectivity_heating.keys():
            data_heating_connections.append(data_connectivity_heating[building])
        else:
            data_heating_connections.append('0') #if it is not inside the network then it is disconnected

        if building in data_connectivity_cooling.keys():
            data_cooling_connections.append(data_connectivity_cooling[building])
        else:
            data_cooling_connections.append('0') #if it is not inside the network then it is disconnected

    building_connectivity_dict = {
        "Name": building_names_all,
        "DH_connectivity": data_heating_connections,
        "DC_connectivity": data_cooling_connections,
    }

    return building_connectivity_dict

"""
Create individuals

"""
from __future__ import division

import random

from cea.optimization.constants import DH_CONVERSION_TECHNOLOGIES_NAMES, \
    DH_CONVERSION_TECHNOLOGIES_NAMES_SHARE, \
    DC_CONVERSION_TECHNOLOGIES_NAMES,\
    DC_CONVERSION_TECHNOLOGIES_NAMES_SHARE, \
    DH_TECHNOLOGIES_SHARING_SPACE, DC_TECHNOLOGIES_SHARING_SPACE

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def generate_main(empty_individual_df, column_names, column_names_buildings_heating,
                     column_names_buildings_cooling, district_heating_network,
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
        populated_individual_df = populate_individual(empty_individual_df,
                                                      DH_CONVERSION_TECHNOLOGIES_NAMES,
                                                      DH_CONVERSION_TECHNOLOGIES_NAMES_SHARE,
                                                      DH_TECHNOLOGIES_SHARING_SPACE,
                                                      column_names_buildings_heating)

        populated_individual_df = populate_individual(populated_individual_df,
                                                      DC_CONVERSION_TECHNOLOGIES_NAMES,
                                                      DC_CONVERSION_TECHNOLOGIES_NAMES_SHARE,
                                                      DC_TECHNOLOGIES_SHARING_SPACE,
                                                      column_names_buildings_cooling)
    elif district_heating_network:
        populated_individual_df = populate_individual(empty_individual_df,
                                                      DH_CONVERSION_TECHNOLOGIES_NAMES,
                                                      DH_CONVERSION_TECHNOLOGIES_NAMES_SHARE,
                                                      DH_TECHNOLOGIES_SHARING_SPACE,
                                                      column_names_buildings_heating)
    elif district_cooling_network:
        populated_individual_df = populate_individual(empty_individual_df,
                                                      DC_CONVERSION_TECHNOLOGIES_NAMES,
                                                      DC_CONVERSION_TECHNOLOGIES_NAMES_SHARE,
                                                      DC_TECHNOLOGIES_SHARING_SPACE,
                                                      column_names_buildings_cooling)

    # CONVERT BACK INTO AN INDIVIDUAL STRING IMPORTANT TO USE column_names to keep the order
    individual = []
    for column in column_names:
        individual.append(populated_individual_df[column].values[0])

    return individual


def populate_individual(empty_individual_df,
                        name_conversion_technologies,
                        name_share_conversion_technologies,
                        name_technologies_sharing_space,
                        columns_buildings_name):

    # do it for units that are activated
    columns_activation = [x[0] for x in name_conversion_technologies]
    lim_inf_activation = [x[1][0] for x in name_conversion_technologies]
    lim_sup_activation = [x[1][1] for x in name_conversion_technologies]
    for column, lim_inf, lim_sup in zip(columns_activation, lim_inf_activation, lim_sup_activation):
        empty_individual_df[column] = random.randint(lim_inf, lim_sup)

    # do it for the share of the units that are activated
    columns_share = [x[0] for x in name_share_conversion_technologies]
    lim_inf_share = [x[1][0] for x in name_share_conversion_technologies]
    lim_sup_share = [x[1][1] for x in name_share_conversion_technologies]
    for column_activation, column_share, lim_inf, lim_sup in zip(columns_activation, columns_share, lim_inf_share, lim_sup_share):
         empty_individual_df[column_share] = random.uniform(lim_inf, lim_sup)

    # do it for the buildings
    for column in columns_buildings_name:
        empty_individual_df[column] = random.randint(0, 1)

    #constrain that only activated units can be more than 0
    for column_activation, column_share, lim_inf, lim_sup in zip(columns_activation, columns_share, lim_inf_share, lim_sup_share):
        if empty_individual_df[column_activation].values == 0: # only if the unit is not activated
            empty_individual_df[column_share] = 0.0

    # contrain that some technologies share space so the total must be 1
    unit_name, unit_share = [], []
    for column_activation, column_share in zip(columns_activation, columns_share):
        if empty_individual_df[column_activation].values >= 1 and column_activation in name_technologies_sharing_space: # only if the unit is activated
            unit_name.append(column_share)
            unit_share.append(empty_individual_df[column_share])
    sum_shares = sum(unit_share)
    normalized_shares = [i / sum_shares for i in unit_share]
    for column, share in zip(unit_name, normalized_shares):
        empty_individual_df[column] = share

    return empty_individual_df

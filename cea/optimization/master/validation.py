"""
Validation

"""
from __future__ import division

import random

from cea.optimization.constants import DH_CONVERSION_TECHNOLOGIES_WITH_SPACE_RESTRICTIONS, \
    DH_CONVERSION_TECHNOLOGIES_SHARE, DC_CONVERSION_TECHNOLOGIES_SHARE, DC_CONVERSION_TECHNOLOGIES_WITH_SPACE_RESTRICTIONS


def validation_main(individual_with_name_dict,
                    column_names_buildings_heating,
                    column_names_buildings_cooling,
                    district_heating_network,
                    district_cooling_network
                    ):
    if district_heating_network:

        # FOR BUILDINGS CONNECTIONS - they should be inside the range
        for building_name in column_names_buildings_heating:
            lim_inf = 0
            lim_sup = 1
            while individual_with_name_dict[building_name] > lim_sup:
                individual_with_name_dict[building_name] = random.randint(lim_inf, lim_sup)

        # FOR BUILDINGS CONNECTIONS - constrains that at least 2 buildings should be connected to the network
        lim_inf = 0
        lim_sup = 1
        candidate = ''
        while candidate.count('1') < 2:
            candidate = ''.join(str(individual_with_name_dict[building_name]) for building_name in column_names_buildings_heating)
            if candidate.count('1') < 2:  #there are at least two buildings connected
                for building_name in column_names_buildings_heating:
                        individual_with_name_dict[building_name] = random.randint(lim_inf, lim_sup)


        # FOR SUPPLY SYSTEMS SHARE - turn off if they are below the minimum (trick to avoid strings with on - off behavior
        for technology_name, limits in DH_CONVERSION_TECHNOLOGIES_SHARE.iteritems():
            minimum = limits["minimum"]
            if individual_with_name_dict[technology_name] < minimum:
                individual_with_name_dict[technology_name] = 0.0 #0.0 denotes off

        # FOR SUPPLY SYSTEMS SHARE - The share of solar technologies should be 1 (because they share the same area)
        unit_name, unit_share = [], []
        for technology_name, limits in DH_CONVERSION_TECHNOLOGIES_SHARE.iteritems():
            minimum = limits["minimum"]
            if individual_with_name_dict[technology_name] >= minimum and technology_name in DH_CONVERSION_TECHNOLOGIES_WITH_SPACE_RESTRICTIONS:  # only if the unit is activated
                unit_name.append(technology_name)
                unit_share.append(individual_with_name_dict[technology_name])
        sum_shares = sum(unit_share)
        if sum_shares > 1.0: #only i the case that the sum of shares is more than the maximum of 1.0
            normalized_shares = [i / sum_shares for i in unit_share]
            for column, share in zip(unit_name, normalized_shares):
                individual_with_name_dict[column] = share

    if district_cooling_network:

        # FOR BUILDINGS CONNECTIONS
        for building_name in column_names_buildings_cooling:
            lim_inf = 0
            lim_sup = 1
            while individual_with_name_dict[building_name] > lim_sup:
                individual_with_name_dict[building_name] = random.randint(lim_inf, lim_sup)

        #FOR BUILDINGS CONNECTIONS - constrains that at least 2 buildings should be connected to the network
        lim_inf = 0
        lim_sup = 1
        candidate = ''
        while candidate.count('1') < 2:
            candidate = ''.join(str(individual_with_name_dict[building_name]) for building_name in column_names_buildings_cooling)
            if candidate.count('1') < 2:  #there are at least two buildings connected
                for building_name in column_names_buildings_cooling:
                        individual_with_name_dict[building_name] = random.randint(lim_inf, lim_sup)

        # FOR SUPPLY SYSTEMS SHARE - turn off if they are below the minimum (trick to avoid strings with on - off behavior
        for technology_name, limits in DC_CONVERSION_TECHNOLOGIES_SHARE.iteritems():
            minimum = limits["minimum"]
            if individual_with_name_dict[technology_name] < minimum:
                individual_with_name_dict[technology_name] = 0.0 #0.0 denotes off

        # FOR SUPPLY SYSTEMS SHARE - The share of solar technologies should be 1 (because they share the same area)
        unit_name, unit_share = [], []
        for technology_name, limits in DC_CONVERSION_TECHNOLOGIES_SHARE.iteritems():
            minimum = limits["minimum"]
            if individual_with_name_dict[technology_name] >= minimum and technology_name in DC_CONVERSION_TECHNOLOGIES_WITH_SPACE_RESTRICTIONS:  # only if the unit is activated
                unit_name.append(technology_name)
                unit_share.append(individual_with_name_dict[technology_name])
        sum_shares = sum(unit_share)
        normalized_shares = [i / sum_shares for i in unit_share]
        for column, share in zip(unit_name, normalized_shares):
            individual_with_name_dict[column] = share

    return individual_with_name_dict

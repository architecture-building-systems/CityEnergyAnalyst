"""
Validation

"""
from __future__ import division

import random

from cea.optimization.constants import DH_CONVERSION_TECHNOLOGIES_CAPACITY, \
    DH_CONVERSION_TECHNOLOGIES_WITH_SPACE_RESTRICTIONS, \
    DH_CONVERSION_TECHNOLOGIES_SHARE, \
    DC_CONVERSION_TECHNOLOGIES_CAPACITIES, DC_CONVERSION_TECHNOLOGIES_SHARE, \
    Q_MIN_SHARE


def validation_main(individual_with_name_dict,
                    heating_unit_names,
                    cooling_unit_names,
                    heating_unit_names_share,
                    cooling_unit_names_share,
                    column_names_buildings_heating,
                    column_names_buildings_cooling,
                    district_heating_network,
                    district_cooling_network
                    ):
    if district_heating_network:

        # FOR BUILDINGS CONNECTIONS
        for building_name in column_names_buildings_heating:
            lim_inf = 0
            lim_sup = 1
            while individual_with_name_dict[building_name] > lim_sup:
                individual_with_name_dict[building_name] = random.randint(lim_inf, lim_sup)

        # FOR SUPPLY SYSTEMS
        for technology_name, limits in DH_CONVERSION_TECHNOLOGIES_CAPACITY:
            lim_inf = limits[0]
            lim_sup = limits[1]
            while individual_with_name_dict[technology_name] > lim_sup:
                individual_with_name_dict[technology_name] = random.randint(lim_inf, lim_sup)

        # FOR SUPPLY SYSTEMS SHARE
        for technology_name, limits in DH_CONVERSION_TECHNOLOGIES_SHARE:
            lim_inf = limits[0]
            lim_sup = limits[1]
            while individual_with_name_dict[technology_name] > lim_sup:
                individual_with_name_dict[technology_name] = random.uniform(lim_inf, lim_sup)

        # constrain that units not activated should be 0.0
        for column_activation, column_share in zip(heating_unit_names, heating_unit_names_share):
            if individual_with_name_dict[column_activation] == 0 and individual_with_name_dict[
                column_share] > 0.0:  # only if the unit is not activated
                individual_with_name_dict[column_share] = 0.0

        # constrain that units activated should be more than 0.0
        for column_activation, columnshare_and_limits in zip(heating_unit_names, DH_CONVERSION_TECHNOLOGIES_SHARE):
            column_share, limits = columnshare_and_limits
            lim_inf = limits[0]
            lim_sup = limits[1]
            while individual_with_name_dict[column_activation] >= 1 and individual_with_name_dict[
                column_share] == 0.0:  # only if the unit is activated
                individual_with_name_dict[column_share] = random.uniform(lim_inf, lim_sup)

        # contrain that some technologies share space so the total must be 1
        unit_name, unit_share = [], []
        for column_activation, column_share in zip(heating_unit_names, heating_unit_names_share):
            if individual_with_name_dict[
                column_activation] >= 1 and column_activation in DH_CONVERSION_TECHNOLOGIES_WITH_SPACE_RESTRICTIONS:  # only if the unit is activated
                unit_name.append(column_share)
                unit_share.append(individual_with_name_dict[column_share])
        sum_shares = sum(unit_share)
        normalized_shares = [i / sum_shares for i in unit_share]
        for column, share in zip(unit_name, normalized_shares):
            individual_with_name_dict[column] = share

        #constrains that at least 2 buildings should be connected to the network
        lim_inf = 0
        lim_sup = 1
        candidate = ''
        while candidate.count('1') < 2:
            candidate = ''.join(str(individual_with_name_dict[building_name]) for building_name in column_names_buildings_heating)
            if candidate.count('1') < 2:  #there are at least two buildings connected
                for building_name in column_names_buildings_heating:
                        individual_with_name_dict[building_name] = random.randint(lim_inf, lim_sup)


    if district_cooling_network:

        # FOR BUILDINGS CONNECTIONS
        for building_name in column_names_buildings_cooling:
            lim_inf = 0
            lim_sup = 1
            while individual_with_name_dict[building_name] > lim_sup:
                individual_with_name_dict[building_name] = random.randint(lim_inf, lim_sup)

        # FOR SUPPLY SYSTEMS
        for technology_name, limits in DC_CONVERSION_TECHNOLOGIES_CAPACITIES:
            lim_inf = limits[0]
            lim_sup = limits[1]
            while individual_with_name_dict[technology_name] > lim_sup:
                individual_with_name_dict[technology_name] = random.randint(lim_inf, lim_sup)

        # FOR SUPPLY SYSTEMS SHARE
        for technology_name, limits in DC_CONVERSION_TECHNOLOGIES_SHARE:
            lim_inf = limits[0]
            lim_sup = limits[1]
            while individual_with_name_dict[technology_name] > lim_sup:
                individual_with_name_dict[technology_name] = random.uniform(lim_inf, lim_sup)

        # constrain that only activated units can be more than 0.0
        for column_activation, column_share in zip(cooling_unit_names, cooling_unit_names_share):
            if individual_with_name_dict[column_activation] == 0:  # only if the unit is not activated
                individual_with_name_dict[column_share] = 0.0

        # constrain that units activated should be more than 0.0
        for column_activation, columnshare_and_limits in zip(heating_unit_names, DH_CONVERSION_TECHNOLOGIES_SHARE):
            column_share, limits = columnshare_and_limits
            lim_inf = limits[0]
            lim_sup = limits[1]
            while individual_with_name_dict[column_activation] >= 1 and individual_with_name_dict[
                column_share] == 0.0:  # only if the unit is activated
                individual_with_name_dict[column_share] = random.uniform(lim_inf, lim_sup)

        #constrains that at least 2 buildings should be connected to the network
        lim_inf = 0
        lim_sup = 1
        candidate = ''
        while candidate.count('1') < 2:
            candidate = ''.join(str(individual_with_name_dict[building_name]) for building_name in column_names_buildings_cooling)
            if candidate.count('1') < 2:  #there are at least two buildings connected
                for building_name in column_names_buildings_cooling:
                        individual_with_name_dict[building_name] = random.randint(lim_inf, lim_sup)

    return individual_with_name_dict

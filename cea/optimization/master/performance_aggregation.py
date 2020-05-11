from __future__ import division
from __future__ import print_function

import numpy as np


def summarize_results_individual(buildings_district_scale_costs,
                                 buildings_district_scale_emissions,
                                 buildings_building_scale_costs,
                                 buildings_building_scale_emissions):
    # initialize values
    Capex_total_sys_district_scale_USD = 0.0
    Capex_a_sys_district_scale_USD = 0.0
    Opex_a_sys_district_scale_USD = 0.0
    TAC_sys_district_scale_USD = 0.0
    GHG_sys_district_scale_tonCO2 = 0.0

    Opex_a_sys_building_scale_USD = 0.0
    Capex_a_sys_building_scale_USD = 0.0
    Capex_total_sys_building_scale_USD = 0.0
    TAC_sys_building_scale_USD = 0.0
    GHG_sys_building_scale_tonCO2 = 0.0

    # FOR CONNECTED BUILDINGS
    for column in buildings_district_scale_costs.keys():
        if "Capex_total_" in column and "district_scale_USD" in column:
            Capex_total_sys_district_scale_USD += buildings_district_scale_costs[column]
        if "Capex_a_" in column and "district_scale_USD" in column:
            Capex_a_sys_district_scale_USD += buildings_district_scale_costs[column]
            TAC_sys_district_scale_USD += buildings_district_scale_costs[column]
        if "Opex_var_" in column and "district_scale_USD" in column:
            Opex_a_sys_district_scale_USD += buildings_district_scale_costs[column]
            TAC_sys_district_scale_USD += buildings_district_scale_costs[column]
        if "Opex_fixed_" in column and "district_scale_USD" in column:
            Opex_a_sys_district_scale_USD += buildings_district_scale_costs[column]
            TAC_sys_district_scale_USD += buildings_district_scale_costs[column]

    for column in buildings_district_scale_emissions.keys():
        if "GHG_" in column and "district_scale_tonCO2" in column:
            GHG_sys_district_scale_tonCO2 += buildings_district_scale_emissions[column]

    # FOR DISCONNECTED BUILDINGS
    for column in buildings_building_scale_costs.keys():
        if "Capex_total_" in column and "building_scale_USD" in column:
            Capex_total_sys_building_scale_USD += buildings_building_scale_costs[column]
        if "Capex_a_" in column and "building_scale_USD" in column:
            Capex_a_sys_building_scale_USD += buildings_building_scale_costs[column]
            TAC_sys_building_scale_USD += buildings_building_scale_costs[column]
        if "Opex_var_" in column and "building_scale_USD" in column:
            Opex_a_sys_building_scale_USD += buildings_building_scale_costs[column]
            TAC_sys_building_scale_USD += buildings_building_scale_costs[column]
        if "Opex_fixed_" in column and "building_scale_USD" in column:
            Opex_a_sys_building_scale_USD += buildings_building_scale_costs[column]
            TAC_sys_building_scale_USD += buildings_building_scale_costs[column]

    for column in buildings_building_scale_emissions.keys():
        if "GHG_" in column and "building_scale_tonCO2" in column:
            GHG_sys_building_scale_tonCO2 += buildings_building_scale_emissions[column]

    Opex_a_sys_USD = Opex_a_sys_district_scale_USD + Opex_a_sys_building_scale_USD
    Capex_a_sys_USD = Capex_a_sys_district_scale_USD + Capex_a_sys_building_scale_USD
    Capex_total_sys_USD = Capex_total_sys_district_scale_USD + Capex_total_sys_building_scale_USD
    TAC_sys_USD = TAC_sys_district_scale_USD + TAC_sys_building_scale_USD
    GHG_sys_tonCO2 = GHG_sys_district_scale_tonCO2 + GHG_sys_building_scale_tonCO2

    performance_totals = {
        # Total costs (We use all this info to make graphs)

        "Capex_total_sys_USD": Capex_total_sys_USD,
        "Capex_total_sys_district_scale_USD": Capex_total_sys_district_scale_USD,
        "Capex_total_sys_building_scale_USD": Capex_total_sys_building_scale_USD,

        "Capex_a_sys_USD": Capex_a_sys_USD,
        "Capex_a_sys_district_scale_USD": Capex_a_sys_district_scale_USD,
        "Capex_a_sys_building_scale_USD": Capex_a_sys_building_scale_USD,

        "Opex_a_sys_USD": Opex_a_sys_USD,
        "Opex_a_sys_district_scale_USD": Opex_a_sys_district_scale_USD,
        "Opex_a_sys_building_scale_USD": Opex_a_sys_building_scale_USD,

        "TAC_sys_USD": TAC_sys_USD,
        "TAC_sys_district_scale_USD": TAC_sys_district_scale_USD,
        "TAC_sys_building_scale_USD": TAC_sys_building_scale_USD,

        "GHG_sys_tonCO2": GHG_sys_tonCO2,
        "GHG_sys_district_scale_tonCO2": GHG_sys_district_scale_tonCO2,
        "GHG_sys_building_scale_tonCO2": GHG_sys_building_scale_tonCO2,
    }

    # return objectives and perfromance totals dict
    TAC_sys_USD = np.float64(TAC_sys_USD)
    GHG_sys_tonCO2 = np.float64(GHG_sys_tonCO2)

    return TAC_sys_USD, GHG_sys_tonCO2, performance_totals


from __future__ import division
from __future__ import print_function
import numpy as np

def summarize_results_individual(master_to_slave_vars,
                                 buildings_connected_costs,
                                 buildings_connected_emissions,
                                 buildings_disconnected_costs,
                                 buildings_disconnected_emissions):

    #initialize values
    Capex_total_sys_connected_USD = 0.0
    Capex_a_sys_connected_USD = 0.0
    Opex_a_sys_connected_USD = 0.0
    TAC_sys_connected_USD = 0.0
    GHG_sys_connected_tonCO2 = 0.0
    PEN_sys_connected_MJoil = 0.0

    Opex_a_sys_disconnected_USD = 0.0
    Capex_a_sys_disconnected_USD = 0.0
    Capex_total_sys_disconnected_USD = 0.0
    TAC_sys_disconnected_USD = 0.0
    GHG_sys_disconnected_tonCO2 = 0.0
    PEN_sys_disconnected_MJoil = 0.0

    # FOR CONNECTED BUILDINGS
    for column in buildings_connected_costs.keys():
        if "Capex_total_" in column and "connected_USD" in column:
            Capex_total_sys_connected_USD += buildings_connected_costs[column]
        if "Capex_a_" in column and "connected_USD" in column:
            Capex_a_sys_connected_USD += buildings_connected_costs[column]
            TAC_sys_connected_USD += buildings_connected_costs[column]
        if "Opex_var_" in column and "connected_USD" in column:
            Opex_a_sys_connected_USD  += buildings_connected_costs[column]
            TAC_sys_connected_USD += buildings_connected_costs[column]
        if "Opex_fixed_" in column and "connected_USD" in column:
            Opex_a_sys_connected_USD  += buildings_connected_costs[column]
            TAC_sys_connected_USD += buildings_connected_costs[column]

    for column in buildings_connected_emissions.keys():
        if "GHG_" in column and "connected_tonCO2" in column:
            GHG_sys_connected_tonCO2 += buildings_connected_emissions[column]
        if "PEN_" in column and "connected_MJoil" in column:
            PEN_sys_connected_MJoil += buildings_connected_emissions[column]

    # FOR DISCONNECTED BUILDINGS
    for column in buildings_disconnected_costs.keys():
        if "Capex_total_" in column and "disconnected_USD" in column:
            Capex_total_sys_disconnected_USD += buildings_disconnected_costs[column]
        if "Capex_a_" in column and "disconnected_USD" in column:
            Capex_a_sys_disconnected_USD += buildings_disconnected_costs[column]
            TAC_sys_disconnected_USD += buildings_disconnected_costs[column]
        if "Opex_var_" in column and "disconnected_USD" in column:
            Opex_a_sys_disconnected_USD += buildings_disconnected_costs[column]
            TAC_sys_disconnected_USD += buildings_disconnected_costs[column]
        if "Opex_fixed_" in column and "disconnected_USD" in column:
            Opex_a_sys_disconnected_USD += buildings_disconnected_costs[column]
            TAC_sys_disconnected_USD += buildings_disconnected_costs[column]

    for column in buildings_disconnected_emissions.keys():
        if "GHG_" in column and "disconnected_tonCO2" in column:
            GHG_sys_disconnected_tonCO2 += buildings_disconnected_emissions[column]
        if "PEN_" in column and "disconnected_MJoil" in column:
            PEN_sys_disconnected_MJoil += buildings_disconnected_emissions[column]

    Opex_a_sys_USD = Opex_a_sys_connected_USD + Opex_a_sys_disconnected_USD
    Capex_a_sys_USD = Capex_a_sys_connected_USD + Capex_a_sys_disconnected_USD
    Capex_total_sys_USD = Capex_total_sys_connected_USD + Capex_total_sys_disconnected_USD
    TAC_sys_USD = TAC_sys_connected_USD + TAC_sys_disconnected_USD
    GHG_sys_tonCO2 = GHG_sys_connected_tonCO2 + GHG_sys_disconnected_tonCO2
    PEN_sys_MJoil = PEN_sys_connected_MJoil + PEN_sys_disconnected_MJoil


    performance_totals={
        #Total costs (We use all this info to make graphs)

        "Capex_total_sys_USD":Capex_total_sys_USD,
        "Capex_total_sys_connected_USD":Capex_total_sys_connected_USD,
        "Capex_total_sys_disconnected_USD":Capex_total_sys_disconnected_USD,

        "Capex_a_sys_USD": Capex_a_sys_USD,
        "Capex_a_sys_connected_USD": Capex_a_sys_connected_USD,
        "Capex_a_sys_disconnected_USD": Capex_a_sys_disconnected_USD,

        "Opex_a_sys_USD":Opex_a_sys_USD,
        "Opex_a_sys_connected_USD":Opex_a_sys_connected_USD,
        "Opex_a_sys_disconnected_USD":Opex_a_sys_disconnected_USD,

        "TAC_sys_USD":TAC_sys_USD,
        "TAC_sys_connected_USD":TAC_sys_connected_USD,
        "TAC_sys_disconnected_USD":TAC_sys_disconnected_USD,

        "GHG_sys_tonCO2":GHG_sys_tonCO2,
        "GHG_sys_connected_tonCO2":GHG_sys_connected_tonCO2,
        "GHG_sys_disconnected_tonCO2":GHG_sys_disconnected_tonCO2,

        "PEN_sys_MJoil":PEN_sys_MJoil,
        "PEN_sys_connected_MJoil":PEN_sys_connected_MJoil,
        "PEN_sys_disconnected_MJoil":PEN_sys_disconnected_MJoil,
    }

    #return objectives and perfromance totals dict
    TAC_sys_USD = np.float64(TAC_sys_USD)
    GHG_sys_tonCO2 = np.float64(GHG_sys_tonCO2)
    PEN_sys_MJoil = np.float64(PEN_sys_MJoil)


    return TAC_sys_USD, GHG_sys_tonCO2, PEN_sys_MJoil, performance_totals


from __future__ import division
from __future__ import print_function
import numpy as np

def summarize_results_individual(master_to_slave_vars,
                                 performance_storage,
                                 performance_heating,
                                 performance_cooling,
                                 performance_disconnected,
                                 performance_electricity):

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

    # FOR HEATING NETWORK
    if master_to_slave_vars.DHN_exists:
        for column in performance_heating.keys():
            if "Capex_total_" in column and "connected_USD" in column:
                Capex_total_sys_connected_USD += performance_heating[column]
            if "Capex_a_" in column and "connected_USD" in column:
                Capex_a_sys_connected_USD += performance_heating[column]
                TAC_sys_connected_USD += performance_heating[column]
            if "Opex_a_" in column and "connected_USD" in column:
                TAC_sys_connected_USD += performance_heating[column]
                Opex_a_sys_connected_USD  += performance_heating[column]
            if "GHG_" in column and "connected_tonCO2" in column:
                GHG_sys_connected_tonCO2 += performance_heating[column]
            if "PEN_" in column and "connected_MJoil" in column:
                PEN_sys_connected_MJoil += performance_heating[column]

    #FOR COOLING NETWORK
    if master_to_slave_vars.DCN_exists:
        for column in performance_cooling.keys():
            if "Capex_total_" in column and "connected_USD" in column:
                Capex_total_sys_connected_USD += performance_cooling[column]
            if "Capex_a_" in column and "connected_USD" in column:
                Capex_a_sys_connected_USD += performance_cooling[column]
                TAC_sys_connected_USD += performance_cooling[column]
            if "Opex_a_" in column and "connected_USD" in column:
                TAC_sys_connected_USD += performance_cooling[column]
                Opex_a_sys_connected_USD += performance_cooling[column]
            if "GHG_" in column and "connected_tonCO2" in column:
                GHG_sys_connected_tonCO2 += performance_cooling[column]
            if "PEN_" in column and "connected_MJoil" in column:
                PEN_sys_connected_MJoil += performance_cooling[column]

    #FOR ELECTRICAL NETWORK
    for column in performance_electricity.keys():
        if "Capex_total_" in column and "connected_USD" in column:
            Capex_total_sys_connected_USD += performance_electricity[column]
        if "Capex_a_" in column and "connected_USD" in column:
            Capex_a_sys_connected_USD += performance_electricity[column]
            TAC_sys_connected_USD += performance_electricity[column]
        if "Opex_a_" in column and "connected_USD" in column:
            TAC_sys_connected_USD += performance_electricity[column]
            Opex_a_sys_connected_USD += performance_electricity[column]
        if "GHG_" in column and "connected_tonCO2" in column:
            GHG_sys_connected_tonCO2 += performance_electricity[column]
        if "PEN_" in column and "connected_MJoil" in column:
            PEN_sys_connected_MJoil += performance_electricity[column]

    #FOR STORAGEBUILDINGS
    for column in performance_storage.keys():
        if "Capex_total_" in column and "connected_USD" in column:
            Capex_total_sys_connected_USD += performance_storage[column]
        if "Capex_a_" in column and "connected_USD" in column:
            Capex_a_sys_connected_USD += performance_storage[column]
            TAC_sys_connected_USD += performance_storage[column]
        if "Opex_a_" in column and "connected_USD" in column:
            TAC_sys_connected_USD += performance_storage[column]
            Opex_a_sys_connected_USD += performance_storage[column]
        if "GHG_" in column and "connected_tonCO2" in column:
            GHG_sys_connected_tonCO2 += performance_storage[column]
        if "PEN_" in column and "connected_MJoil" in column:
            PEN_sys_connected_MJoil += performance_storage[column]

    #FOR DISCONNECTED BUILDINGS
    for column in performance_disconnected.keys():
        if "Capex_total_" in column and "disconnected_USD" in column:
            Capex_total_sys_disconnected_USD += performance_disconnected[column]
        if "Capex_a_" in column and "disconnected_USD" in column:
            Capex_a_sys_disconnected_USD += performance_disconnected[column]
            TAC_sys_disconnected_USD += performance_disconnected[column]
        if "Opex_a_" in column and "disconnected_USD" in column:
            TAC_sys_disconnected_USD += performance_disconnected[column]
            Opex_a_sys_disconnected_USD += performance_disconnected[column]
        if "GHG_" in column and "disconnected_tonCO2" in column:
            GHG_sys_disconnected_tonCO2 += performance_disconnected[column]
        if "PEN_" in column and "disconnected_MJoil" in column:
            PEN_sys_disconnected_MJoil += performance_disconnected[column]

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

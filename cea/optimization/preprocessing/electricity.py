"""
Electricity Operation


All buildings are connected to the grid which completely cover their needs
(as the buying / selling electricity prices are the same and are independent 
from the hour in the day / the day in the year)

"""
import os
import numpy as np
import pandas as pd
from cea.optimization.constants import *


def calc_pareto_electricity(locator, lca, config, building_names):
    """
    This function computes the parameters for the electrical demand contributing to the pareto optimal alternatives.
    in the future, this aspect should be included in the optimization itself.

    :param locator: locator class
    :param gv: global variables class
    :type locator: class
    :type gv: class
    :return: elecCosts, elecCO2, elecPrim
    :rtype: tuple
    """
    df = pd.read_csv(locator.get_total_demand(), usecols=["E_sys_MWhyr"])
    arrayTotal = np.array(df) * 1E6
    totalElec = np.sum(arrayTotal)  # [Wh]

    if config.detailed_electricity_pricing:
        elecCosts = 0
        for name in building_names:
            df = pd.read_csv(locator.get_demand_results_file(name), usecols=["E_sys_kWh"])
            array_individual = np.array(df) * 1000  # [Wh]

            for i in range(len(array_individual)):
                elecCosts = elecCosts + (array_individual[i][0] * lca.ELEC_PRICE[i])  # [USD]
        print (elecCosts)
    else:
        elecCosts = 0
        for i in range(len(arrayTotal)):
            elecCosts = elecCosts + (arrayTotal[i][0] * lca.ELEC_PRICE[i])  # [USD]

    elecCO2 = totalElec * lca.EL_TO_CO2 * 3600E-6 # [kg CO2]
    elecPrim = totalElec * lca.EL_TO_OIL_EQ * 3600E-6 # [MJoil-eq]
    
    return elecCosts, elecCO2, elecPrim
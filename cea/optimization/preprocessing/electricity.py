"""
=====================
Electricity Operation
=====================

All buildings are connected to the grid which completely cover their needs
(as the buying / selling electricity prices are the same and are independent 
from the hour in the day / the day in the year)

"""
import os
import numpy as np
import pandas as pd
from cea.optimization.constants import *


def calc_pareto_electricity(locator, prices):
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
    df = pd.read_csv(locator.get_total_demand(), usecols=["Ef_MWhyr"])
    arrayTotal = np.array(df)
    totalElec = np.sum(arrayTotal) * 1E6 # [Wh]
    
    elecCosts = totalElec * prices.ELEC_PRICE # [CHF]
    elecCO2 = totalElec * EL_TO_CO2 * 3600E-6 # [kg CO2]
    elecPrim = totalElec * EL_TO_OIL_EQ * 3600E-6 # [MJoil-eq]
    
    return elecCosts, elecCO2, elecPrim
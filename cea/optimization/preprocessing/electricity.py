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


def calc_pareto_electricity(pathX, gV):
    """
    Computes the parameters for the electrical demand
    
    Parameters
    ----------
    pathRaw : string
        path to raw foldes
    
    Returns
    -------
    (elecCosts, elecCO2, elecPrim) : tuple
    
    """
    os.chdir(pathX.pathRaw)
    df = pd.read_csv("Total.csv", usecols=["Ealf", "Eauxf", "Ecaf", "Edataf", "Epf"])
    arrayTotal = np.array(df)
    totalElec = np.sum(arrayTotal) * 1E6 # [Wh]
    print totalElec, "totalElec"
    
    elecCosts = totalElec * gV.ELEC_PRICE # [CHF]
    elecCO2 = totalElec * gV.EL_TO_CO2 * 3600E-6 # [kg CO2]
    elecPrim = totalElec * gV.EL_TO_OIL_EQ * 3600E-6 # [MJoil-eq]
    
    return elecCosts, elecCO2, elecPrim
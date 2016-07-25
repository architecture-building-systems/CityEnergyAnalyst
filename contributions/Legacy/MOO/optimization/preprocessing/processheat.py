"""
========================================
Boiler Pre-treatment for Heat Processing
========================================

"""
from __future__ import division

import os

import numpy as np
import pandas as pd

from contributions.Legacy.MOO import technologies


def calc_pareto_Qhp(pathX, gV):
    """
    Computes the triplet for the process heat demand
    
    Parameters
    ----------
    pathRaw : string
        path to raw folder
    
    Returns
    -------
    hpCosts, hpCO2, hpPrim : tuple
    
    """
    hpCosts = 0
    hpCO2 = 0
    hpPrim = 0
    
    os.chdir(pathX.pathRaw)
    dfTotal = pd.read_csv("Total.csv", usecols=["Name", "Qhpf"])
    arrayTotal = np.array(dfTotal)
    nBuild = int(np.shape(arrayTotal)[0])
    
    for i in range(nBuild):
        if arrayTotal[i][1] > 0:
            
            # Extract process heat needs
            buildName = arrayTotal[i][0]
            print buildName
            df = pd.read_csv(buildName + ".csv", usecols=["Qhpf"])
            arrayBuild = np.array(df)
    
            Qnom = 0    
            Qannual = 0
            
            # Operation costs / CO2 / Prim
            for i in range( np.shape(arrayBuild)[0] ):
                Qgas = arrayBuild[i][0] * 1E3 / gV.Boiler_eta_hp # [Wh] Assumed 0.9 efficiency
                
                if Qgas < Qnom:
                    Qnom = Qgas * (1+gV.Qmargin_Disc)
                Qannual += Qgas
                
                hpCosts += Qgas * gV.NG_PRICE # [CHF]
                hpCO2 += Qgas * 3600E-6 * gV.NG_BACKUPBOILER_TO_CO2_STD # [kg CO2]
                hpPrim += Qgas * 3600E-6 * gV.NG_BACKUPBOILER_TO_OIL_STD # [MJ-oil-eq]
            
            # Investment costs
            hpCosts += technologies.boilers.calc_Cinv_boiler(Qnom, Qannual, gV)
    
    return hpCosts, hpCO2, hpPrim












"""
========================================
Boiler Pre-treatment for Heat Processing
========================================

"""
from __future__ import division

import os

import numpy as np
import pandas as pd

from cea import technologies


def calc_pareto_Qhp(locator, total_demand, gv):
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



    if total_demand["Qhprof_MWhyr"].sum()>0:
        df = total_demand[total_demand.Qhprof_kWh != 0]

        for name in df.Name :
            # Extract process heat needs
            Qhprof = pd.read_csv(locator.get_demand_results_file(name), usecols=["Qhprof_kWh"]).Qhprof_kWh.values

            Qnom = 0
            Qannual = 0
            # Operation costs / CO2 / Prim
            for i in range(8760):
                Qgas = Qhprof[i] * 1E3 / gv.Boiler_eta_hp # [Wh] Assumed 0.9 efficiency

                if Qgas < Qnom:
                    Qnom = Qgas * (1+gv.Qmargin_Disc)

                Qannual += Qgas
                hpCosts += Qgas * gv.NG_PRICE # [CHF]
                hpCO2 += Qgas * 3600E-6 * gv.NG_BACKUPBOILER_TO_CO2_STD # [kg CO2]
                hpPrim += Qgas * 3600E-6 * gv.NG_BACKUPBOILER_TO_OIL_STD # [MJ-oil-eq]

            # Investment costs
            hpCosts += technologies.boilers.calc_Cinv_boiler(Qnom, Qannual, gv)
    else:
        hpCosts = hpCO2 = hpPrim = 0
    return hpCosts, hpCO2, hpPrim












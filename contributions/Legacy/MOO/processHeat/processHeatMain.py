"""
========================================
Boiler Pre-treatment for Heat Processing
========================================

"""
from __future__ import division
import os
import numpy as np
import pandas as pd


def Cond_Boiler_InvCost(Q_design, Q_annual, gV):
    """
    Calculates the annual cost of a boiler (based on A+W cost of oil boilers) [CHF / a]
    and Faz. 2012 data
    
    Parameters
    ----------
    Q_design : float
        Design Load of Boiler [W_th]
    
    Q_annual : float
        Annual thermal load required from Boiler [Wh]
        
    Returns
    -------
    InvCa : float
        annualized investment costs in [CHF/a] including Maintainance Cost
        
    """
    InvC = 28000 # after A+W 
    
    if Q_design <= 90000 and Q_design >= 28000:
        InvC_exkl_MWST = 28000 + 0.275 * (Q_design - 28000) # linear interpolation of A+W data
        InvC = (gV.MWST + 1) * InvC_exkl_MWST
        
    elif Q_design > 90000 and Q_design  <= 320000: # 320kW = maximum Power of conventional Gas Boiler, 
        InvC = 45000 + 0.11 * (Q_design - 90000) 
    
    InvCa =  InvC * gV.Boiler_i * (1+ gV.Boiler_i) ** gV.Boiler_n / ((1+gV.Boiler_i) ** gV.Boiler_n - 1) 
             
    if Q_design > 320000: # 320kW = maximum Power of conventional Gas Boiler 
        InvCa = gV.EURO_TO_CHF * (84000 + 14 * Q_design / 1000) # after Faz.2012
    
    Maint_C_annual = gV.Boiler_C_maintainance_faz * Q_annual / 1E6 * gV.EURO_TO_CHF # 3.5 euro per MWh_th FAZ 2013
    Labour_C = gV.Boiler_C_labour * Q_annual / 1E6 * gV.EURO_TO_CHF # approx 4 euro per MWh_th
    
    InvCa += Maint_C_annual + Labour_C #CHF
    
    return InvCa


def processHeatOp(pathX, gV):
    """
    Computes the triplet for the process heat dem
    
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
            hpCosts += Cond_Boiler_InvCost(Qnom, Qannual, gV)
    
    return hpCosts, hpCO2, hpPrim












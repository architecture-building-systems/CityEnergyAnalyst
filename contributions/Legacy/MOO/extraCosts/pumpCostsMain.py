# -*- coding: utf-8 -*-
"""
============================
Operation costs for the pump
============================
to compensate for the pressure losses in the network

"""
from __future__ import division
import os
import numpy as np
import pandas as pd
from math import sqrt

import globalVar as gV
import investCosts as iC
reload(gV)
reload(iC)


def pumpCosts(dicoSupply, buildList, pathNtwRes, ntwFeat, gV):
    """
    Computes the pumping costs
    
    Parameters
    ----------
    dicoSupply : class context
    buildList : list
        list of buildings in the district
    pathNtwRes : string
        path to ntw results folder
    ntwFeat : class ntwFeatures
    
    Returns
    -------
    pumpCosts : float
    
    """    
    pumpCosts = 0
    #nBuild = dicoSupply.nBuildingsConnected
    #ntot = len(buildList)
    
    os.chdir(pathNtwRes)
    """
    # Approximation developed for Zernez, not used here.
    
    if gV.ZernezFlag == :
        df = pd.read_csv(dicoSupply.NETWORK_DATA_FILE, usecols=["Q_DH_building_netw_total"])
        Q_DH_building_netw_total = np.array(df)
        mdotdf = pd.read_csv(dicoSupply.NETWORK_DATA_FILE, usecols=["mdot_heat_netw_total"])
    
        mdotnMax =np.amax(np.array(mdotdf))
        print mdotnMax
        #mdot0Max = np.amax( np.array( pd.read_csv("Network_summary_result_all.csv", usecols=["mdot_heat_netw_total"]) ) )
        
            
        for i in range(int(np.shape(Q_DH_building_netw_total)[0])):
            #deltaP = 2* (gV.a * mdotA[i][0] + gV.b)        
            #pumpCosts += deltaP * mdotA[i][0] / 1000 * gV.ELEC_PRICE / gV.etaPump
            Epump = Q_DH_building_netw_total[i][0] * gV.PumpEnergyShare
            pumpCosts += Epump * gV.ELEC_PRICE
    
        deltaPmax = np.max(Epump) / gV.etaPump * (1 + gV.PumpReliabilityMargin)
        print deltaPmax, "deltaPmax"
        investCosts = iC.Pump_Cost(deltaPmax, mdotnMax, gV.etaPump)
        print investCosts, "investCosts from pumpCostsMain.py"
        pumpCosts += investCosts
    else:
    """
    if 1:
        pumpCosts = 0
        #nBuild = dicoSupply.nBuildingsConnected
        #ntot = len(buildList)
        
        os.chdir(pathNtwRes)
        df = pd.read_csv(dicoSupply.NETWORK_DATA_FILE, usecols=["mdot_DH_netw_total"])
        mdotA = np.array(df)
        mdotnMax = np.amax(mdotA)
        
        #mdot0Max = np.amax( np.array( pd.read_csv("Network_summary_result_all.csv", usecols=["mdot_heat_netw_total"]) ) )
        
        for i in range(int(np.shape(mdotA)[0])):
            deltaP = 2* (104.81 * mdotA[i][0] + 59016)  
            
            if gV.ZernezFlag == 1:
                deltaP = deltaP * gV.NetworkLengthZernez / gV.NetworkLengthReference # scale by network length total (Reference = Zug) 
                
            pumpCosts += deltaP * mdotA[i][0] / 1000 * gV.ELEC_PRICE / gV.etaPump
        
        if gV.ZernezFlag == 1:
            deltaPmax = ntwFeat.DeltaP_DHN * gV.NetworkLengthZernez / gV.NetworkLengthReference 
        else: 
            deltaPmax = ntwFeat.DeltaP_DHN
            
        investCosts = iC.calc_Cinv_pump(deltaPmax, mdotnMax, gV.etaPump, gV) # investment of Machinery
        pumpCosts += investCosts
        
    print pumpCosts, " CHF - pump costs in pumpCostsMain.py"
    
    return pumpCosts


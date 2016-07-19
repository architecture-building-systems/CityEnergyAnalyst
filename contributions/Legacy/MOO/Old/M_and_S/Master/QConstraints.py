"""
===============================
Calculates the constraints on Q
===============================

"""
from __future__ import division
import os
import numpy as np

import EA_globalVar as gV
import SupportFn as sFn


def Qmax_perBuild (pathdata, buildList):
    """
    Calculates Qmax per building

    Parameters
    ----------
    pathdata : string
        Path to folder where data are stored (csv files)
        WARNING : the name of the file with the data is 
        "BuildingName_result.csv"
    buildList : list
        List of the buildings' name
    
    Returns
    -------
    Qmax_dico : dictionary
        Keys are the buildings names and Values the maximum heating dem
    
    """
    os.chdir(pathdata)
    Qmax_dico = {}

    for building in buildList:
        buildFile = building + "_result.csv"
        buildDemand = sFn.extractDemand(buildFile, gV.HeatfeatureList, gV.nDay)
        
        Qmax = 0
        for hour in range( len(buildDemand) ):
            Qcurrent = buildDemand[hour][2] * \
                       (buildDemand[hour][1] - buildDemand[hour][0])
            if Qcurrent > Qmax:
                Qmax = Qcurrent
        
        Qmax_dico[building] = Qmax
    
    return Qmax_dico
    

def Qmax_perCombi (pathdata, buildList):
    """
    Calculates Qmax per combination of connected / disconnected buildings
    
    Parameters
    ----------
    pathdata : string
        Path to folder where data are stored (csv files)
        WARNING : the name of the file with the data is 
        "BuildingName_result.csv"
    buildList : list
        List of the buildings' name
    
    Returns
    -------
    QmaxCombi_dico : dictionary
        Keys are strings "00011101010" to represent the combination
        Values are the maximum heating dem
    
    """
    os.chdir(pathdata)

    nBuildings = len(buildList)
    maxcombi = 0
    for i in range(nBuildings):
        maxcombi += 2 ** i
    
    Qmax_dico = {}
    Qmax_dico["0"*nBuildings] = 0
        
    for combi in range(1, maxcombi + 1):
        binCombi = np.binary_repr(combi, width = nBuildings)
        demandtotreat = []
        
        for rank in range(nBuildings):
            digit = int( binCombi[rank] )
            if digit == 1:
                buildFile = buildList[ rank ] + "_result.csv"
                buildDemand = sFn.extractDemand(buildFile, gV.HeatfeatureList, gV.nDay)
                demandtotreat.append(buildDemand)
        
        Qmax = 0
        for hour in range( len(buildDemand) ):
            Qcurrent = 0
            for building in demandtotreat:
                Qcurrent += building[hour][2] * \
                            (building[hour][1] - building[hour][0])
            if Qcurrent > Qmax:
                Qmax = Qcurrent
        Qmax_dico[binCombi] = Qmax
    
    return Qmax_dico
            
        






















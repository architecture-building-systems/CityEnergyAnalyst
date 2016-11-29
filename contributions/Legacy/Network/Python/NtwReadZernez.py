"""
========================================
Bridge to FM's Network Optimization Code
========================================

"""
from __future__ import division
import pandas as pd
import numpy as np


Header = '/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/UESM/UESM Data/'
CodePath = '/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/UESM/UESM Code/'


def modifyLayout(ld):
    
    Nodesdf = pd.read_csv(Header + "Raw2/NodesData.csv")
    NodesArray = np.array(Nodesdf)
    
    Edgesdf = pd.read_csv(Header + "Raw2/PipesData.csv")
    EdgesArray = np.array(Edgesdf)
    
    nNodes = int(np.shape(NodesArray)[0])
    nEdges = int(np.shape(EdgesArray)[0])
    
    ld.c["N"] = nNodes
    ld.c["E"] = nEdges

    ld.c["sSpp_e"] = np.zeros((nEdges,2))
    for i in range(nEdges):
        ld.c["sSpp_e"][i][0] = int(EdgesArray[i][2][1:])
        ld.c["sSpp_e"][i][1] = int(EdgesArray[i][3][1:])

    ld.c['sRtn_e'] = np.fliplr(ld.c['sSpp_e'])
    ld.c["nPl"] = int(Nodesdf[(Nodesdf.Plant == 1)].iloc[0]["DC_ID"][1:])

    
def modifyHydraulicBuild(hd, ld):

    Nodesdf = pd.read_csv(Header + "Raw2/NodesData.csv")
    NodesArray = np.array(Nodesdf)
    nNodes = int(np.shape(NodesArray)[0])
    
    for i in range(nNodes):
        
        if NodesArray[i][3] != "<Null>" and NodesArray[i][0] != 1L:
            nodeNb = int(NodesArray[i][2][1:])
            
            hd.c["pRq_n"][nodeNb][0] = 119.9E3/2

            buildName = NodesArray[i][3]
            subsFileName = buildName + "_result.csv"
            buildSubsdf = pd.read_csv(Header + "TotalNtw/" + subsFileName, usecols=["mdot_DH_result"])
            buildSubsArray = np.array(buildSubsdf)
            mdotMax = np.amax(buildSubsArray)
            
            hd.c['vDotRq_n'][nodeNb][0] = - mdotMax / 1000

    hd.c['vDotPl'] = -sum(hd.c['vDotRq_n'][np.array(range(ld.c['N']))!=ld.c['nPl']*np.ones(ld.c['N']),0]);
    
    Edgesdf = pd.read_csv(Header + "Raw2/PipesData.csv")
    EdgesArray = np.array(Edgesdf)
    nEdges = int(np.shape(EdgesArray)[0])

    for i in range(nEdges):
        hd.c['L_e'][i][0] = EdgesArray[i][1]


def modifyHydraulicNtw(hd, ld):

    Nodesdf = pd.read_csv(Header + "Raw2/NodesData.csv")
    NodesArray = np.array(Nodesdf)
    nNodes = int(np.shape(NodesArray)[0])
    
    ntwAlldf = pd.read_csv(Header + "NtwRes/Network_summary_result_all.csv", usecols=["mdot_heat_netw_total"])
    indexMax = ntwAlldf["mdot_heat_netw_total"].argmax()
    
    for i in range(nNodes):
        
        if NodesArray[i][3] != "<Null>" and NodesArray[i][0] != 1L:
            nodeNb = int(NodesArray[i][2][1:])
            
            hd.c["pRq_n"][nodeNb][0] = 119.9E3/2

            buildName = NodesArray[i][3]
            subsFileName = buildName + "_result.csv"
            buildSubsdf = pd.read_csv(Header + "TotalNtw/" + subsFileName, usecols=["mdot_DH_result"])
            buildSubsArray = np.array(buildSubsdf)
            
            hd.c['vDotRq_n'][nodeNb][0] = - buildSubsArray[indexMax][0] / 1000

    hd.c['vDotPl'] = -sum(hd.c['vDotRq_n'][np.array(range(ld.c['N']))!=ld.c['nPl']*np.ones(ld.c['N']),0]);
           
    Edgesdf = pd.read_csv(Header + "Raw2/PipesData.csv")
    EdgesArray = np.array(Edgesdf)
    nEdges = int(np.shape(EdgesArray)[0])    
    
    for i in range(nEdges):
        hd.c['L_e'][i][0] = EdgesArray[i][1]


def InvCostsPipes(ld, hd, hsBuild, hsNtw):
    fCosts = 0
    
    nNodes = ld.c["N"]
    nEdges = ld.c["E"]
    nPipes = hd.c["I"]

    Nodesdf = pd.read_csv(Header + "Raw2/NodesData.csv")
    NodesArray = np.array(Nodesdf)
    
    indexBuild = []
    for i in range(nNodes):
        if NodesArray[i][3] != "<Null>" and NodesArray[i][0] != 1L:
            indexBuild.append(int(NodesArray[i][2][1:]))
    
    for i in range(nEdges):
        nodeA = ld.c['sSpp_e'][i][0]
        nodeB = ld.c['sSpp_e'][i][1]

        if nodeA in indexBuild or nodeB in indexBuild:
            for j in range(nPipes):
                fCosts += hsBuild.c["x_i_e"][j][i] * hd.c["c_i"][j][0] * hd.c['L_e'][i][0]
        else:
            for j in range(nPipes):
                fCosts += hsNtw.c["x_i_e"][j][i] * hd.c["c_i"][j][0] * hd.c['L_e'][i][0]
    
    return fCosts


def modifyHydraulicTime(hd, ld, h):
    
    Nodesdf = pd.read_csv(Header + "Raw2/NodesData.csv")
    NodesArray = np.array(Nodesdf)
    nNodes = int(np.shape(NodesArray)[0])
    
    for i in range(nNodes):
        
        if NodesArray[i][3] != "<Null>" and NodesArray[i][0] != 1L:
            nodeNb = int(NodesArray[i][2][1:])
            
            hd.c["pRq_n"][nodeNb][0] = 119.9E3/2

            buildName = NodesArray[i][3]
            subsFileName = buildName + "_result.csv"
            buildSubsdf = pd.read_csv(Header + "TotalNtw/" + subsFileName, usecols=["mdot_DH_result"])
            buildSubsArray = np.array(buildSubsdf)
            
            hd.c['vDotRq_n'][nodeNb][0] = - buildSubsArray[h][0] / 1000

    hd.c['vDotPl'] = -sum(hd.c['vDotRq_n'][np.array(range(ld.c['N']))!=ld.c['nPl']*np.ones(ld.c['N']),0]);
           
    Edgesdf = pd.read_csv(Header + "Raw2/PipesData.csv")
    EdgesArray = np.array(Edgesdf)
    nEdges = int(np.shape(EdgesArray)[0])    
    
    for i in range(nEdges):
        hd.c['L_e'][i][0] = EdgesArray[i][1]


def modifyReducedHyd(rhd, ld, hsBuild):
    
    nNodes = ld.c["N"]
    nEdges = ld.c["E"]

    Nodesdf = pd.read_csv(Header + "Raw2/NodesData.csv")
    NodesArray = np.array(Nodesdf)  
    
    indexBuild = []
    for i in range(nNodes):
        if NodesArray[i][3] != "<Null>" and NodesArray[i][0] != 1L:
            indexBuild.append(int(NodesArray[i][2][1:]))
    
    for i in range(nEdges):
        nodeA = ld.c['sSpp_e'][i][0]
        nodeB = ld.c['sSpp_e'][i][1]

        if nodeA in indexBuild or nodeB in indexBuild:
            rhd.c['i_e'][i] = np.nonzero(np.round(hsBuild.c['x_i_e'][:,i]))


"""
========================================
Bridge to FM's Network Optimization Code
========================================

"""
from __future__ import division
import pandas as pd
import numpy as np



def modifyLayout(ld, Header, Ntw):
    
    Nodesdf = pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["DC_ID", "Plant"])
    
    EdgesIn = np.array(pd.read_csv(Header + "NtwLayout/PipesData_" + Ntw + ".csv", usecols = ["NODE1"]))
    EdgesOut = np.array(pd.read_csv(Header + "NtwLayout/PipesData_" + Ntw + ".csv", usecols = ["NODE2"]))
    
    nNodes = Nodesdf.Plant.count()
    nEdges = int(np.shape(EdgesIn)[0])
    
    ld.c["N"] = nNodes
    ld.c["E"] = nEdges

    ld.c["sSpp_e"] = np.zeros((nEdges,2))
    for i in range(nEdges):
        ld.c["sSpp_e"][i][0] = int(EdgesIn[i][0][1:])
        ld.c["sSpp_e"][i][1] = int(EdgesOut[i][0][1:])

    ld.c['sRtn_e'] = np.fliplr(ld.c['sSpp_e'])
    ld.c["nPl"] = int(Nodesdf[(Nodesdf.Plant == 1)].iloc[0]["DC_ID"][1:])

    
def modifyHydraulicBuild(hd, ld, Header, Ntw):

    NodesName = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["Name"] ) )
    NodesID = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["DC_ID"] ) )
    NodesPlant = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["Plant"] ) )
    
    nNodes = int(np.shape(NodesName)[0])
    
    for i in range(nNodes):
        
        if NodesName[i][0] != "<Null>" and NodesName[i][0] != " " and NodesPlant[i][0] != 1:
            nodeNb = int(NodesID[i][0][1:])
            
            hd.c["pRq_n"][nodeNb][0] = 119.9E3/2

            buildName = NodesName[i][0]
            subsFileName = buildName + "_result.csv"
            buildSubsdf = pd.read_csv(Header + "SubsRes/" + subsFileName, usecols=["mdot_"+Ntw+"_result"])
            buildSubsArray = np.array(buildSubsdf)
            mdotMax = np.amax(buildSubsArray)
            
            hd.c['vDotRq_n'][nodeNb][0] = - mdotMax / 1000

    hd.c['vDotPl'] = -sum(hd.c['vDotRq_n'][np.array(range(ld.c['N']))!=ld.c['nPl']*np.ones(ld.c['N']),0]);
    
    Edgesdf = pd.read_csv(Header + "NtwLayout/PipesData_" + Ntw + ".csv", usecols = ["LENGTH"])
    EdgesArray = np.array(Edgesdf)
    nEdges = int(np.shape(EdgesArray)[0])

    for i in range(nEdges):
        hd.c['L_e'][i][0] = EdgesArray[i][0]


def modifyHydraulicNtw(hd, ld, Header, Ntw):

    NodesName = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["Name"] ) )
    NodesID = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["DC_ID"] ) )
    NodesPlant = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["Plant"] ) )
    
    nNodes = int(np.shape(NodesName)[0])
    
    if Ntw == "DH":
        colName = "mdot_DH_netw_total"
    else:
        colName = "mdot_cool_netw_total"
    
    ntwAlldf = pd.read_csv(Header + "NtwRes/Network_summary_result_all.csv", usecols=[colName])
    indexMax = ntwAlldf[colName].argmax()
    
    for i in range(nNodes):
        
        if NodesName[i][0] != "<Null>" and NodesName[i][0] != " " and NodesPlant[i][0] != 1:
            nodeNb = int(NodesID[i][0][1:])
            
            hd.c["pRq_n"][nodeNb][0] = 119.9E3/2

            buildName = NodesName[i][0]
            subsFileName = buildName + "_result.csv"
            buildSubsdf = pd.read_csv(Header + "SubsRes/" + subsFileName, usecols=["mdot_"+Ntw+"_result"])
            buildSubsArray = np.array(buildSubsdf)
            
            hd.c['vDotRq_n'][nodeNb][0] = - buildSubsArray[indexMax][0] / 1000

    hd.c['vDotPl'] = -sum(hd.c['vDotRq_n'][np.array(range(ld.c['N']))!=ld.c['nPl']*np.ones(ld.c['N']),0]);
           
    Edgesdf = pd.read_csv(Header + "NtwLayout/PipesData_" + Ntw + ".csv", usecols = ["LENGTH"])
    EdgesArray = np.array(Edgesdf)
    nEdges = int(np.shape(EdgesArray)[0])

    for i in range(nEdges):
        hd.c['L_e'][i][0] = EdgesArray[i][0]


def InvCostsPipes(ld, hd, hsBuild, hsNtw, Header, Ntw):
    fCosts = 0
    
    nNodes = ld.c["N"]
    nEdges = ld.c["E"]
    nPipes = hd.c["I"]

    NodesName = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["Name"] ) )
    NodesID = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["DC_ID"] ) )
    NodesPlant = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["Plant"] ) )
    
    indexBuild = []
    for i in range(nNodes):
        if NodesName[i][0] != "<Null>" and NodesName[i][0] != " " and NodesPlant[i][0] != 1:
            indexBuild.append(int(NodesID[i][0][1:]))
    
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


def modifyHydraulicTime(hd, ld, h, Header, Ntw):
    
    NodesName = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["Name"] ) )
    NodesID = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["DC_ID"] ) )
    NodesPlant = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["Plant"] ) )
    
    nNodes = int(np.shape(NodesName)[0])
    
    for i in range(nNodes):
        
        if NodesName[i][0] != "<Null>" and NodesName[i][0] != " " and NodesPlant[i][0] != 1:
            nodeNb = int(NodesID[i][0][1:])
            
            hd.c["pRq_n"][nodeNb][0] = 119.9E3/2

            buildName = NodesName[i][0]
            subsFileName = buildName + "_result.csv"
            buildSubsdf = pd.read_csv(Header + "TotalNtw/" + subsFileName, usecols=["mdot_"+Ntw+"_result"])
            buildSubsArray = np.array(buildSubsdf)
            
            hd.c['vDotRq_n'][nodeNb][0] = - buildSubsArray[h][0] / 1000

    hd.c['vDotPl'] = -sum(hd.c['vDotRq_n'][np.array(range(ld.c['N']))!=ld.c['nPl']*np.ones(ld.c['N']),0]);
           
    Edgesdf = pd.read_csv(Header + "NtwLayout/PipesData_" + Ntw + ".csv", usecols = ["LENGTH"])
    EdgesArray = np.array(Edgesdf)
    nEdges = int(np.shape(EdgesArray)[0])

    for i in range(nEdges):
        hd.c['L_e'][i][0] = EdgesArray[i][0]


def modifyReducedHyd(rhd, ld, hsBuild, Header, Ntw):
    
    nNodes = ld.c["N"]
    nEdges = ld.c["E"]

    NodesName = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["Name"] ) )
    NodesID = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["DC_ID"] ) )
    NodesPlant = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["Plant"] ) )  
    
    indexBuild = []
    for i in range(nNodes):
        if NodesName[i][0] != "<Null>" and NodesName[i][0] != " " and NodesPlant[i][0] != 1:
            indexBuild.append(int(NodesID[i][0][1:]))
    
    for i in range(nEdges):
        nodeA = ld.c['sSpp_e'][i][0]
        nodeB = ld.c['sSpp_e'][i][1]

        if nodeA in indexBuild or nodeB in indexBuild:
            rhd.c['i_e'][i] = np.nonzero(np.round(hsBuild.c['x_i_e'][:,i]))


def modifyTemp(td, Header, Ntw):
    
    NodesName = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["Name"] ) )
    NodesID = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["DC_ID"] ) )
    NodesPlant = np.array( pd.read_csv(Header + "NtwLayout/NodesData_" + Ntw + ".csv", usecols = ["Plant"] ) )
    
    nNodes = int(np.shape(NodesName)[0])

    if Ntw == "DH":
        colName = "mdot_DH_netw_total"
    else:
        colName = "mdot_cool_netw_total"

    ntwAlldf = pd.read_csv(Header + "NtwRes/Network_summary_result_all.csv", usecols=[colName])
    indexMax = ntwAlldf[colName].argmax()
    
    for i in range(nNodes):
        
        if NodesName[i][0] != "<Null>" and NodesName[i][0] != " " and NodesPlant[i][0] != 1:
            nodeNb = int(NodesID[i][0][1:])

            buildName = NodesName[i][0]
            subsFileName = buildName + "_result.csv"
            buildSubsdf = pd.read_csv(Header + "SubsRes/" + subsFileName, usecols=["T_return_"+Ntw+"_result", "T_supply_"+Ntw+"_result"])
            buildSubsArray = np.array(buildSubsdf)

            td.c['TRq_n'][nodeNb][0] = buildSubsArray[indexMax][1]
            td.c['dT_n'][nodeNb][0] = buildSubsArray[indexMax][1] - buildSubsArray[indexMax][0]


















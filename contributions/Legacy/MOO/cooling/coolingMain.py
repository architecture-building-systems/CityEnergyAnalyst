"""
================
Cooling function
================

Use free cooling from lake as long as possible (Qmax lake from gV and HP Lake operation from slave)
If lake exhausted, use VCC + CT operation

"""
from __future__ import division
import pandas as pd
import numpy as np
import os

import globalVar as gV
import coolingModel.Model_CT as CTModel
import coolingModel.Model_VCC as VCCModel
import coolingModel.Model_Pump as PumpModel

reload(gV)
reload(CTModel)
reload(VCCModel)
reload(PumpModel)



def coolingMain(pathX, configKey, ntwFeat, HRdata, gV):
    """
    Computes the parameters for the cooling of the complete DCN
    
    Parameters
    ----------
    pathX : string
        path to res folder
    configKey : string
        configuration key for the DHN
    ntwFeat : class ntwFeatures
    HRdata : inf
        0 if no data heat recovery, 1 if so
    
    Returns
    -------
    (costs, co2, prim) : tuple
    
    """
    
    ############# Recover the cooling needs
    
    # Space cooling previously aggregated in the substation routine
    df = pd.read_csv(pathX.pathNtwRes + "/Network_summary_result_all.csv", usecols=["T_sst_cool_return_netw_total", "mdot_cool_netw_total"])
    coolArray = np.nan_to_num( np.array(df) )
    TsupCool = gV.TsupCool
    
    # Data center cooling, (treated separately for each building)
    df = pd.read_csv(pathX.pathRaw + "/Total.csv", usecols=["Name", "Qcdataf"])
    arrayData = np.array(df)
    
    # Process cooling, (treated separately for each building)
    df = pd.read_csv(pathX.pathRaw + "/Total.csv", usecols=["Name", "Qcpf"])
    arrayQcp = np.array(df)
    
    # Ice hockey rings, (treated separately for each building)
    df = pd.read_csv(pathX.pathRaw + "/Total.csv", usecols=["Name", "Qcicef"])
    arrayQice = np.array(df)
    
    
    ############# Recover the heat already taken from the lake by the heat pumps
    try:
        os.chdir(pathX.pathSlaveRes)
        fNameSlaveRes = configKey + "PPActivationPattern.csv"
        
        dfSlave = pd.read_csv(fNameSlaveRes, usecols=["Qcold_HPLake"])
        
        QlakeArray = np.array(dfSlave)
        Qlake = np.sum(QlakeArray)
        
    except:
        Qlake = 0
    
    Qavail = gV.DeltaU + Qlake
    print Qavail, "Qavail"
    
    
    ############# Output results
    costs = ntwFeat.pipesCosts_DCN
    CO2 = 0
    prim = 0
    
    nBuild = int( np.shape(arrayData)[0] )
    nHour = int( np.shape(coolArray)[0] )
    CTLoad = np.zeros(nHour)
    VCCnom = 0
    
    calFactor = 0
    TotalCool = 0
    
    
    ############ Function for cooling operation
    def coolOperation(dataArray, el, QavailIni, TempSup = 0):
        toTotalCool = 0
        toCalfactor = 0
        toCosts = 0
        toCO2 = 0
        toPrim = 0
        
        QavailCopy = QavailIni
        VCCnomIni = 0
        
        for i in range(el):
            
            if TempSup > 0:
                Tsup = TempSup
                Tret = dataArray[i][-2]
                mdot = abs ( dataArray[i][-1] )
            else:
                Tsup = dataArray[i][-3] + 273
                Tret = dataArray[i][-2] + 273
                mdot = abs ( dataArray[i][-1] * 1E3 / gV.cp )
            
            Qneed = abs( mdot * gV.cp * (Tret - Tsup) )                
            toTotalCool += Qneed
            
            if QavailCopy - Qneed >= 0: # Free cooling possible from the lake
                QavailCopy -= Qneed
                
                # Delta P from linearization after network optimization
                deltaP = 2* (gV.DeltaP_Coeff * mdot + gV.DeltaP_Origin)
                
                toCalfactor += deltaP * mdot / 1000 / gV.etaPump
                toCosts += deltaP * mdot / 1000 * gV.ELEC_PRICE / gV.etaPump
                toCO2 += deltaP * mdot / 1000 * gV.EL_TO_CO2 / gV.etaPump * 0.0036
                toPrim += deltaP * mdot / 1000 * gV.EL_TO_OIL_EQ / gV.etaPump * 0.0036
                
            else:
                print "Lake exhausted !"
                wdot, qhotdot = VCCModel.VCC_Op(mdot, Tsup, Tret, gV)
                if Qneed > VCCnomIni:
                    VCCnomIni = Qneed * (1+gV.Qmargin_Disc)
                
                toCosts += wdot * gV.ELEC_PRICE
                toCO2 += wdot * gV.EL_TO_CO2 * 3600E-6
                toPrim += wdot * gV.EL_TO_OIL_EQ * 3600E-6
                
                CTLoad[i] += qhotdot
    
        return toCosts, toCO2, toPrim, toCalfactor, toTotalCool, QavailCopy, VCCnomIni
    
    
    ########## Cooling operation with Circulating pump and VCC
    
    print "Space cooling operation"
    toCosts, toCO2, toPrim, toCalfactor, toTotalCool, QavailCopy, VCCnomIni = coolOperation(coolArray, nHour, Qavail, TempSup = TsupCool)
    costs += toCosts
    CO2 += toCO2
    prim += toPrim
    calFactor += toCalfactor
    TotalCool += toTotalCool
    VCCnom = max(VCCnom, VCCnomIni)
    Qavail = QavailCopy
    print Qavail, "Qavail after space cooling"

    mdotMax = np.amax(coolArray[:,1])
    costs += PumpModel.Pump_Cost(2*ntwFeat.DeltaP_DCN, mdotMax, gV.etaPump, gV)
    
    if HRdata == 0:
        print "Data centers cooling operation"
        for i in range(nBuild):
            if arrayData[i][1] > 0:
                buildName = arrayData[i][0]
                print buildName
                df = pd.read_csv(pathX.pathRaw + "/" + buildName + ".csv", usecols=["tsdata", "trdata", "mcpdata"])
                arrayBuild = np.array(df)
                
                mdotMaxData = abs( np.amax(arrayBuild[:,-1]) / gV.cp * 1E3)
                costs += PumpModel.Pump_Cost(2*ntwFeat.DeltaP_DCN, mdotMaxData, gV.etaPump, gV)
            
                toCosts, toCO2, toPrim, toCalfactor, toTotalCool, QavailCopy, VCCnomIni = coolOperation(arrayBuild, nHour, Qavail)
                costs += toCosts
                CO2 += toCO2
                prim += toPrim
                calFactor += toCalfactor
                TotalCool += toTotalCool
                VCCnom = max(VCCnom, VCCnomIni)
                Qavail = QavailCopy
                print Qavail, "Qavail after data center"

    print "Process cooling operation"
    for i in range(nBuild):
        if arrayQcp[i][1] > 0:
            buildName = arrayQcp[i][0]
            print buildName
            df = pd.read_csv(pathX.pathRaw + "/" + buildName + ".csv", usecols=["tscp", "trcp", "mcpcp"])
            arrayBuild = np.array(df)

            mdotMaxcp = abs( np.amax(arrayBuild[:,-1]) / gV.cp * 1E3)
            costs += PumpModel.Pump_Cost(2*ntwFeat.DeltaP_DCN, mdotMaxcp, gV.etaPump, gV)
        
            toCosts, toCO2, toPrim, toCalfactor, toTotalCool, QavailCopy, VCCnomIni = coolOperation(arrayBuild, nHour, Qavail)
            costs += toCosts
            CO2 += toCO2
            prim += toPrim
            calFactor += toCalfactor
            TotalCool += toTotalCool
            VCCnom = max(VCCnom, VCCnomIni)
            Qavail = QavailCopy
            print Qavail, "Qavail after cp"
    
    print "Ice rinks cooling operation"
    for i in range(nBuild):
        if arrayQice[i][1] > 0:
            buildName = arrayQice[i][0]
            print buildName
            df = pd.read_csv(pathX.pathRaw + "/" + buildName + ".csv", usecols=["tsice", "trice", "mcpice"])
            arrayBuild = np.array(df)

            mdotMaxice = abs( np.amax(arrayBuild[:,-1]) / gV.cp * 1E3)
            costs += PumpModel.Pump_Cost(2*ntwFeat.DeltaP_DCN, mdotMaxice, gV.etaPump, gV)
        
            toCosts, toCO2, toPrim, toCalfactor, toTotalCool, QavailCopy, VCCnomIni = coolOperation(arrayBuild, nHour, Qavail)
            costs += toCosts
            CO2 += toCO2
            prim += toPrim
            calFactor += toCalfactor
            TotalCool += toTotalCool
            VCCnom = max(VCCnom, VCCnomIni)
            Qavail = QavailCopy
            print Qavail, "Qavail after ice"
    
    
    print costs, CO2, prim, "operation for cooling"
    print TotalCool, "TotalCool"
    
    
    ########## Operation of the cooling tower
    CTnom = np.amax(CTLoad)
    costCopy = costs
    if CTnom > 0 :
        for i in range(nHour):
            wdot = CTModel.CT_Op( CTLoad[i], CTnom, gV )
            
            costs += wdot * gV.ELEC_PRICE
            CO2 += wdot * gV.EL_TO_CO2 * 3600E-6
            prim += wdot * gV.EL_TO_OIL_EQ * 3600E-6
            
        print costs - costCopy, "costs after operation of CT"
    
    
    ########## Add investment costs  
    
    costs += VCCModel.VCC_InvC(VCCnom, gV)
    print VCCModel.VCC_InvC(VCCnom, gV), "InvC VCC"
    costs += CTModel.CT_InvC(CTnom, gV)
    print CTModel.CT_InvC(CTnom, gV), "InvC CT"
    

    ########### Adjust and add the pumps for filtering and pre-treatment of the water
    calibration = calFactor / 50976000
    print calibration, "adjusting factor"
    
    extraElec = (127865400 + 85243600) * calibration
    costs += extraElec * gV.ELEC_PRICE
    CO2 += extraElec * gV.EL_TO_CO2 * 3600E-6
    prim += extraElec * gV.EL_TO_OIL_EQ * 3600E-6
    
    
    return (costs, CO2, prim)
    
    
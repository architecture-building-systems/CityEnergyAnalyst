"""
================
Lake-cooling network connected to chiller and cooling tower
================

Use free cooling from lake as long as possible (Qmax lake from gv and HP Lake operation from slave)
If lake exhausted, use VCC + CT operation

"""
from __future__ import division

import os

import numpy as np
import pandas as pd

import cea.technologies.cooling_tower as CTModel
import cea.technologies.chillers as VCCModel
import cea.technologies.pumps as PumpModel


__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

"""
============================
technical model
============================

"""

def coolingMain(locator, configKey, ntwFeat, HRdata, gv):
    """
    Computes the parameters for the cooling of the complete DCN
    
    Parameters
    ----------
    locator : string
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
    df = pd.read_csv(locator.pathNtwRes + "/Network_summary_result_all.csv", usecols=["T_sst_cool_return_netw_total", "mdot_cool_netw_total"])
    coolArray = np.nan_to_num( np.array(df) )
    TsupCool = gv.TsupCool
    
    # Data center cooling, (treated separately for each building)
    df = pd.read_csv(locator.get_total_demand(), usecols=["Name", "Qcdataf_MWhyr"])
    arrayData = np.array(df)
    
    # Ice hockey rings, (treated separately for each building)
    df = pd.read_csv(locator.get_total_demand(), usecols=["Name", "Qcref_MWhyr"])
    arrayQice = np.array(df)
    
    
    ############# Recover the heat already taken from the lake by the heat pumps
    try:
        os.chdir(locator.pathSlaveRes)
        fNameSlaveRes = configKey + "PPActivationPattern.csv"
        
        dfSlave = pd.read_csv(fNameSlaveRes, usecols=["Qcold_HPLake"])
        
        QlakeArray = np.array(dfSlave)
        Qlake = np.sum(QlakeArray)
        
    except:
        Qlake = 0
    
    Qavail = gv.DeltaU + Qlake
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
                mdot = abs ( dataArray[i][-1] * 1E3 / gv.cp )
            
            Qneed = abs( mdot * gv.cp * (Tret - Tsup) )
            toTotalCool += Qneed
            
            if QavailCopy - Qneed >= 0: # Free cooling possible from the lake
                QavailCopy -= Qneed
                
                # Delta P from linearization after network optimization
                deltaP = 2* (gv.DeltaP_Coeff * mdot + gv.DeltaP_Origin)
                
                toCalfactor += deltaP * mdot / 1000 / gv.etaPump
                toCosts += deltaP * mdot / 1000 * gv.ELEC_PRICE / gv.etaPump
                toCO2 += deltaP * mdot / 1000 * gv.EL_TO_CO2 / gv.etaPump * 0.0036
                toPrim += deltaP * mdot / 1000 * gv.EL_TO_OIL_EQ / gv.etaPump * 0.0036
                
            else:
                print "Lake exhausted !"
                wdot, qhotdot = VCCModel.calc_VCC(mdot, Tsup, Tret, gv)
                if Qneed > VCCnomIni:
                    VCCnomIni = Qneed * (1+gv.Qmargin_Disc)
                
                toCosts += wdot * gv.ELEC_PRICE
                toCO2 += wdot * gv.EL_TO_CO2 * 3600E-6
                toPrim += wdot * gv.EL_TO_OIL_EQ * 3600E-6
                
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
    costs += PumpModel.Pump_Cost(2*ntwFeat.DeltaP_DCN, mdotMax, gv.etaPump, gv)
    
    if HRdata == 0:
        print "Data centers cooling operation"
        for i in range(nBuild):
            if arrayData[i][1] > 0:
                buildName = arrayData[i][0]
                print buildName
                df = pd.read_csv(locator.get_demand_results_file(buildName), usecols=["Tsdata_C", "Trdata_C", "mcpdata_kWC"])
                arrayBuild = np.array(df)
                
                mdotMaxData = abs( np.amax(arrayBuild[:,-1]) / gv.cp * 1E3)
                costs += PumpModel.Pump_Cost(2*ntwFeat.DeltaP_DCN, mdotMaxData, gv.etaPump, gv)
            
                toCosts, toCO2, toPrim, toCalfactor, toTotalCool, QavailCopy, VCCnomIni = coolOperation(arrayBuild, nHour, Qavail)
                costs += toCosts
                CO2 += toCO2
                prim += toPrim
                calFactor += toCalfactor
                TotalCool += toTotalCool
                VCCnom = max(VCCnom, VCCnomIni)
                Qavail = QavailCopy
                print Qavail, "Qavail after data center"

    print "refrigeration cooling operation"
    for i in range(nBuild):
        if arrayQice[i][1] > 0:
            buildName = arrayQice[i][0]
            print buildName
            df = pd.read_csv(locator.pathRaw + "/" + buildName + ".csv", usecols=["Tsref_C", "Trref_C", "mcpref_kWC"])
            arrayBuild = np.array(df)

            mdotMaxice = abs( np.amax(arrayBuild[:,-1]) / gv.cp * 1E3)
            costs += PumpModel.Pump_Cost(2*ntwFeat.DeltaP_DCN, mdotMaxice, gv.etaPump, gv)
        
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
            wdot = CTModel.calc_CT(CTLoad[i], CTnom, gv)
            
            costs += wdot * gv.ELEC_PRICE
            CO2 += wdot * gv.EL_TO_CO2 * 3600E-6
            prim += wdot * gv.EL_TO_OIL_EQ * 3600E-6
            
        print costs - costCopy, "costs after operation of CT"
    
    
    ########## Add investment costs  
    
    costs += VCCModel.calc_Cinv_VCC(VCCnom, gv)
    print VCCModel.calc_Cinv_VCC(VCCnom, gv), "InvC VCC"
    costs += CTModel.calc_Cinv_CT(CTnom, gv)
    print CTModel.calc_Cinv_CT(CTnom, gv), "InvC CT"
    

    ########### Adjust and add the pumps for filtering and pre-treatment of the water
    calibration = calFactor / 50976000
    print calibration, "adjusting factor"
    
    extraElec = (127865400 + 85243600) * calibration
    costs += extraElec * gv.ELEC_PRICE
    CO2 += extraElec * gv.EL_TO_CO2 * 3600E-6
    prim += extraElec * gv.EL_TO_OIL_EQ * 3600E-6
    
    
    return (costs, CO2, prim)
    
    
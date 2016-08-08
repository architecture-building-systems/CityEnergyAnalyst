"""
====================================
Operation for disconnected buildings
====================================

"""
from __future__ import division
import os
import pandas as pd
import numpy as np
import time

import supportFn as sFn
reload(sFn)

import cea.technologies.boilers as Boiler
import cea.technologies.cogeneration as FC
import cea.technologies.heatpumps as HP
reload(Boiler)
reload(FC)
reload(HP)


def discBuildOp(locator, building_names, gv):
    """
    Computes the parameters for the operation of disconnected buildings
    output results in csv files
    
    Parameters
    ----------
    locator : string
        path to folders    
    
    """
    print "Start Disconnected Building Routine \n"
    t0 = time.clock()
    geothermal_potential = pd.read_csv(locator.get_geothermal_potential, index_col="Name")
    BestData = {}

    def calc_new_load(mdot, TsupDH, Tret, gv):
        Qload = mdot * gv.cp * (TsupDH - Tret) * (1 + gv.Qloss_Disc)
        if Qload < 0:
            Qload = 0
        if Qload < -1E-5:
            print "Error in discBuildMain, negative heat requirement at hour", hour, buildName
        return Qload

    for buildName in building_names:
        fName = locator.pathSubsRes + "/" + buildName + "_result.csv"

        loads = pd.read_csv(fName, usecols=["T_supply_DH_result", "T_return_DH_result", "mdot_DH_result"])
        Qload = np.vectorize(calc_new_load)(loads["mdot_DH_result"], loads["T_supply_DH_result"], loads["T_return_DH_result"], gv)
        Qannual = Qload.sum()
        Qnom = Qload.max()* (1+gv.Qmargin_Disc) # 1% reliability margin on installed capacity

        # Create empty matrices
        result = np.zeros((13,7))
        result[0][0] = 1
        result[1][1] = 1
        result[2][2] = 1
        InvCosts = np.zeros((13,1))
        resourcesRes = np.zeros((13,4))
        QannualB_GHP = np.zeros((10,1)) # For the investment costs of the boiler used with GHP
        Wel_GHP = np.zeros((10,1)) # For the investment costs of the GHP
        
        # Supply with the Boiler / FC / GHP
        print "Operation with the Boiler / FC / GHP"

        Tret = loads["T_return_DH_result"].values
        TsupDH = loads["T_supply_DH_result"].values
        mdot = loads["mdot_DH_result"].values
        for hour in range(8760):

            if Tret[hour] == 0:
                Tret[hour] = TsupDH[hour]
                
            # Boiler NG
            BoilerEff = Boiler.calc_Cop_boiler(Qload[hour], Qnom, Tret[hour])
            
            Qgas = Qload[hour] / BoilerEff
            
            result[0][4] += gv.NG_PRICE * Qgas # CHF
            result[0][5] += gv.NG_BACKUPBOILER_TO_CO2_STD * Qgas * 3600E-6 # kgCO2
            result[0][6] += gv.NG_BACKUPBOILER_TO_OIL_STD * Qgas * 3600E-6 # MJ-oil-eq
            resourcesRes[0][0] += Qload[hour]
            
            if gv.DiscBioGasFlag == 1:
                result[0][4] += gv.BG_PRICE * Qgas # CHF
                result[0][5] += gv.BG_BACKUPBOILER_TO_CO2_STD * Qgas * 3600E-6 # kgCO2
                result[0][6] += gv.BG_BACKUPBOILER_TO_OIL_STD * Qgas * 3600E-6 # MJ-oil-eq
                
            # Boiler BG
            result[1][4] += gv.BG_PRICE * Qgas # CHF
            result[1][5] += gv.BG_BACKUPBOILER_TO_CO2_STD * Qgas * 3600E-6 # kgCO2
            result[1][6] += gv.BG_BACKUPBOILER_TO_OIL_STD * Qgas * 3600E-6 # MJ-oil-eq
            resourcesRes[1][1] += Qload[hour]
                
            # FC
            (FC_Effel, FC_Effth) = FC.calc_eta_FC(Qload[hour], Qnom, 1, "B")
            Qgas = Qload[hour] / (FC_Effth+FC_Effel)
            Qelec = Qgas * FC_Effel            
            
            result[2][4] += gv.NG_PRICE * Qgas - gv.ELEC_PRICE * Qelec # CHF, extra electricity sold to grid
            result[2][5] += 0.0874 * Qgas * 3600E-6 + 773 * 0.45 * Qelec * 1E-6 - gv.EL_TO_CO2 * Qelec * 3600E-6 # kgCO2
            # Bloom box emissions within the FC: 773 lbs / MWh_el (and 1 lbs = 0.45 kg)
            # http://www.carbonlighthouse.com/2011/09/16/bloom-box/
            result[2][6] += 1.51 * Qgas * 3600E-6 - gv.EL_TO_OIL_EQ * Qelec * 3600E-6 # MJ-oil-eq
            
            resourcesRes[2][0] += Qload[hour]
            resourcesRes[2][2] += Qelec
            
            # GHP
            for i in range(10):
                
                QnomBoiler = i/10 * Qnom
                QnomGHP = Qnom - QnomBoiler
                
                if Qload[hour] <= QnomGHP:
                
                    (wdot_el, qcolddot, qhotdot_missing, tsup2) = HP.calc_Cop_GHP(mdot[hour], TsupDH[hour], Tret[hour], gv.TGround, gv)
                    
                    if Wel_GHP[i][0] < wdot_el:
                        Wel_GHP[i][0] = wdot_el
                    
                    result[3+i][4] += gv.ELEC_PRICE * wdot_el   # CHF
                    result[3+i][5] += gv.SMALL_GHP_TO_CO2_STD  * wdot_el   * 3600E-6 # kgCO2
                    result[3+i][6] += gv.SMALL_GHP_TO_OIL_STD  * wdot_el   * 3600E-6 # MJ-oil-eq
                    
                    resourcesRes[3+i][2] -= wdot_el
                    resourcesRes[3+i][3] += Qload[hour] - qhotdot_missing
                    
                    if qhotdot_missing > 0:
                        print "GHP unable to cover the whole demand, boiler activated!"
                        BoilerEff = Boiler.calc_Cop_boiler(qhotdot_missing, QnomBoiler, tsup2)
                        Qgas = qhotdot_missing / BoilerEff
                        
                        result[3+i][4] += gv.NG_PRICE * Qgas   # CHF
                        result[3+i][5] += gv.NG_BACKUPBOILER_TO_CO2_STD * Qgas   * 3600E-6 # kgCO2
                        result[3+i][6] += gv.NG_BACKUPBOILER_TO_OIL_STD * Qgas   * 3600E-6 # MJ-oil-eq
                        
                        QannualB_GHP[i][0] += qhotdot_missing
                        resourcesRes[3+i][0] += qhotdot_missing
    
                else:
                    #print "Boiler activated to compensate GHP", i
                    #if gv.DiscGHPFlag == 0:
                    #    print QnomGHP
                    #   QnomGHP = 0 
                    #   print "GHP not allowed 2, set QnomGHP to zero"
                        
                    TexitGHP = QnomGHP / (mdot[hour] * gv.cp) + Tret[hour]
                    (wdot_el, qcolddot, qhotdot_missing, tsup2) = HP.calc_Cop_GHP(mdot[hour], TexitGHP, Tret[hour], gv.TGround, gv)
                    
                    if Wel_GHP[i][0] < wdot_el:
                        Wel_GHP[i][0] = wdot_el
                        
                    result[3+i][4] += gv.ELEC_PRICE * wdot_el   # CHF
                    result[3+i][5] += gv.SMALL_GHP_TO_CO2_STD  * wdot_el   * 3600E-6 # kgCO2
                    result[3+i][6] += gv.SMALL_GHP_TO_OIL_STD  * wdot_el   * 3600E-6 # MJ-oil-eq
                    
                    resourcesRes[3+i][2] -= wdot_el
                    resourcesRes[3+i][3] += QnomGHP - qhotdot_missing
                    
                    if qhotdot_missing > 0:
                        print "GHP unable to cover the whole demand, boiler activated!"
                        BoilerEff = Boiler.calc_Cop_boiler(qhotdot_missing, QnomBoiler, tsup2)
                        Qgas = qhotdot_missing / BoilerEff
                        
                        result[3+i][4] += gv.NG_PRICE * Qgas   # CHF
                        result[3+i][5] += gv.NG_BACKUPBOILER_TO_CO2_STD * Qgas   * 3600E-6 # kgCO2
                        result[3+i][6] += gv.NG_BACKUPBOILER_TO_OIL_STD * Qgas   * 3600E-6 # MJ-oil-eq
                        
                        QannualB_GHP[i][0] += qhotdot_missing
                        resourcesRes[3+i][0] += qhotdot_missing
                        
                    QtoBoiler = Qload[hour] - QnomGHP
                    QannualB_GHP[i][0] += QtoBoiler
                    
                    BoilerEff = Boiler.calc_Cop_boiler(QtoBoiler, QnomBoiler, TexitGHP)
                    Qgas = QtoBoiler / BoilerEff
                    
                    result[3+i][4] += gv.NG_PRICE * Qgas   # CHF
                    result[3+i][5] += gv.NG_BACKUPBOILER_TO_CO2_STD * Qgas   * 3600E-6 # kgCO2
                    result[3+i][6] += gv.NG_BACKUPBOILER_TO_OIL_STD * Qgas   * 3600E-6 # MJ-oil-eq
                    resourcesRes[3+i][0] += QtoBoiler

        print time.clock() - t0, "seconds process time for the operation \n"
        
        # Investment Costs / CO2 / Prim
        InvCaBoiler = Boiler.calc_Cinv_boiler(Qnom, Qannual, gv)
        InvCosts[0][0] = InvCaBoiler
        InvCosts[1][0] = InvCaBoiler
        
        InvCosts[2][0] = FC.calc_Cinv_FC(Qnom, gv)
        
        for i in range(10):
            result[3+i][0] = i/10
            result[3+i][3] = 1-i/10

            QnomBoiler = i/10 * Qnom
            
            InvCaBoiler = Boiler.calc_Cinv_boiler(QnomBoiler, QannualB_GHP[i][0], gv)
            InvCosts[3+i][0] = InvCaBoiler
            
            InvCaGHP = HP.GHP_InvCost( Wel_GHP[i][0] , gv)
            InvCosts[3+i][0] += InvCaGHP * gv.EURO_TO_CHF
        

        # Best configuration
        print "Find the best configuration"
        
        Best = np.zeros((13,1))
        indexBest = 0

        TotalCosts = np.zeros((13,2))
        TotalCO2 = np.zeros((13,2))
        TotalPrim = np.zeros((13,2))
        
        for i in range(13):
            TotalCosts[i][0] = TotalCO2[i][0] = TotalPrim[i][0] = i

            TotalCosts[i][1] = InvCosts[i][0] + result[i][4]
            TotalCO2[i][1] = result[i][5]
            TotalPrim[i][1] = result[i][6]
        
        CostsS = TotalCosts[np.argsort(TotalCosts[:,1])]
        CO2S = TotalCO2[np.argsort(TotalCO2[:,1])]
        PrimS = TotalPrim[np.argsort(TotalPrim[:,1])]
        
        el = len(CostsS)
        rank = 0
        Bestfound = False
        
        optsearch = np.empty(el)
        optsearch.fill(3)
        indexBest = 0
        
        # Check the GHP area constraint
        for i in range(10):
            QGHP = (1-i/10) * Qnom
            areaAvail = geothermal_potential.ix[buildName,"Area_geo"]
            Qallowed = np.ceil(areaAvail/gv.GHP_A) * gv.GHP_HmaxSize #[W_th]
            
            if Qallowed < QGHP:
                optsearch[i+3] += 1
                Best[i+3][0] = -1
        
        while not Bestfound and rank<el:
            
            optsearch[CostsS[rank][0]] -= 1
            optsearch[CO2S[rank][0]] -= 1
            optsearch[PrimS[rank][0]] -= 1
            
            if np.count_nonzero(optsearch) != el:
                Bestfound = True
                indexBest = np.where(optsearch == 0)[0][0]
                
            rank += 1

        Best[indexBest][0] = 1
        print indexBest, "Best"
        Qnom_array = np.ones(len(Best[:,0])) * Qnom

        # Save results in csv file
        print "Save the results for", buildName, "\n"
        
        dico = {}
        dico[ "BoilerNG Share" ] = result[:,0]
        dico[ "BoilerBG Share" ] = result[:,1]
        dico[ "FC Share" ] = result[:,2]
        dico[ "GHP Share" ] = result[:,3]
        dico[ "Operation Costs [CHF]" ] = result[:,4]
        dico[ "CO2 Emissions [kgCO2-eq]" ] = result[:,5]
        dico[ "Primary Energy Needs [MJoil-eq]" ] = result[:,6]
        dico[ "Annualized Investment Costs [CHF]" ] = InvCosts[:,0]
        dico[ "Total Costs [CHF]" ] = TotalCosts[:,1]
        dico[ "Best configuration" ] = Best[:,0]
        dico[ "Nominal Power" ] = Qnom_array
        dico[ "QfromNG" ] = resourcesRes[:,0]
        dico[ "QfromBG" ] = resourcesRes[:,1]
        dico[ "EforGHP" ] = resourcesRes[:,2]
        dico[ "QfromGHP" ] = resourcesRes[:,3]

        os.chdir(locator.pathDiscRes)
        fName = buildName + "_result.csv"
        results_to_csv = pd.DataFrame(dico)
        fName_result = "DiscOp_" + fName[0:(len(fName)-4)] + ".csv"
        results_to_csv.to_csv(fName_result, sep= ',')
        
    
        BestComb = {}
        BestComb[ "BoilerNG Share" ] = result[indexBest,0]
        BestComb[ "BoilerBG Share" ] = result[indexBest,1]
        BestComb[ "FC Share" ] = result[indexBest,2]
        BestComb[ "GHP Share" ] = result[indexBest,3]
        BestComb[ "Operation Costs [CHF]" ] = result[indexBest,4]
        BestComb[ "CO2 Emissions [kgCO2-eq]" ] = result[indexBest,5]
        BestComb[ "Primary Energy Needs [MJoil-eq]" ] = result[indexBest,6]
        BestComb[ "Annualized Investment Costs [CHF]" ] = InvCosts[indexBest,0]
        BestComb[ "Total Costs [CHF]" ] = TotalCosts[indexBest,1]
        BestComb[ "Best configuration" ] = Best[indexBest,0]
        BestComb[ "Nominal Power" ] = Qnom
        
        BestData[buildName] = BestComb

    if 0:
        os.chdir(locator.pathDiscRes)
        fName = "DiscOpSummary.csv"
        results_to_csv = pd.DataFrame(BestData)
        results_to_csv.to_csv(fName, sep= ',')
        
        
    print "Disconnected Building Routine Completed"
    print time.clock() - t0, "seconds process time for the Disconnected Building Routine \n"
    #print BestData
    #Store summary to CSV



def extractList(fName):
    """
    Extract the names of the buildings in the area

    Parameters
    ----------
    fName : string
        csv file with the names of the buildings

    Returns
    -------
    namesList : list
        List of strings with the names of the buildings

    """
    df = pd.read_csv(fName, usecols=["Name"])
    namesList = df['Name'].values.tolist()

    return namesList


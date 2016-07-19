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

import clustering.clusterMain as cM
reload (cM)

import globalVar as gV
import systModel.modelBoiler as Boiler
import systModel.modelFC as FC
import systModel.modelHP as HP
reload(gV)
reload(Boiler)
reload(FC)
reload(HP)


def discBuildOp(pathRaw, pathSubsRes, pathClustRes, pathDiscRes):
    """
    Computes the parameters for the operation of disconnected buildings
    Output results in csv files
    
    Parameters
    ----------
    pathX : string
    
    """
    print "Start Disconnected Building Routine \n"
    t0 = time.clock()
    
    os.chdir(pathRaw)
    buildList = sFn.extractList("Total.csv")
    
    colNameList = ["T_return_DH_result", "mdot_DH_result"]
    
    for buildName in buildList:
        os.chdir(pathSubsRes)
        fName = buildName + "_result.csv"

        # Extract the data and cluster
        TsupDH = np.array( pd.read_csv( fName, usecols=["T_supply_DH_result"], nrows=1 ) ) [0][0]
        t0cluster = time.clock()
        (fileList, clusterDayRes, occListDay) = cM.clusterMain(pathSubsRes, pathClustRes, fNameList = [fName], featureList = colNameList)
        print time.clock() - t0cluster, "seconds process time for the clustering \n"
        

        # Find the maximum heating load
        Qmax = 0
        Qannual = 0

        for (combi,occ) in occListDay:
            combiT = combi[0]
            combimdot = combi[1]
            
            for hour in range(24):
                mdot = clusterDayRes[1][0][combimdot][hour]
                Tret = min( clusterDayRes[0][0][combiT][hour], TsupDH )
                if Tret == 0: # prevent for upstream errors
                    Tret = TsupDH
                
                Qnew = mdot * gV.cp * (TsupDH - Tret) * (1 + gV.Qloss_Disc)
                Qannual += Qnew * occ
                if Qnew > Qmax:
                    Qmax = Qnew

        Qnom = Qmax * (1+gV.Qmargin_Disc)
        
        # Results
        result = np.zeros((13,7))
        result[0][0] = 1
        result[1][1] = 1
        result[2][2] = 1

        InvCosts = np.zeros((13,1))
                        
        # Qgroundused = np.zeros((10,1))
        # Ground is used all year long but with a temperature penalty of -1.5 K
        
        QannualB_GHP = np.zeros((10,1)) # For the investment costs of the boiler used with GHP
        Wel_GHP = np.zeros((10,1)) # For the investment costs of the GHP
        # PmaxFC = 0 # For the investment costs of the FC [discarded]
        
        # Supply with the Boiler / FC / GHP
        t0operation = time.clock()
        print "Operation with the Boiler / FC / GHP"
        
        for (combi,occ) in occListDay:
            combiT = combi[0]
            combimdot = combi[1]
            
            for hour in range(24):
                mdot = clusterDayRes[1][0][combimdot][hour]
                Tret = min( clusterDayRes[0][0][combiT][hour], TsupDH )
                if Tret == 0:
                    Tret = TsupDH
                
                Qload = mdot * gV.cp * (TsupDH - Tret) * (1 + gV.Qloss_Disc) # [Wh]
                
                # Boiler NG
                BoilerEff = Boiler.Cond_Boiler_operation(Qload, Qnom, Tret)
                Qgas = Qload / BoilerEff
                
                result[0][4] += gV.NG_PRICE * Qgas * occ # CHF
                result[0][5] += gV.NG_BACKUPBOILER_TO_CO2_STD * Qgas * occ * 3600E-6 # kgCO2
                result[0][6] += gV.NG_BACKUPBOILER_TO_OIL_STD * Qgas * occ * 3600E-6 # MJ-oil-eq              
                
                # Boiler BG
                result[1][4] += gV.BG_PRICE * Qgas * occ # CHF
                result[1][5] += gV.BG_BACKUPBOILER_TO_CO2_STD * Qgas * occ * 3600E-6 # kgCO2
                result[1][6] += gV.BG_BACKUPBOILER_TO_OIL_STD * Qgas * occ * 3600E-6 # MJ-oil-eq 

                    
                # FC
                (FC_Effel, FC_Effth) = FC.FC_operation(Qload, Qnom, 1,"B")
                Qgas = Qload / FC_Effth
                Qelec = Qgas * FC_Effel
                
                #if PmaxFC < Qelec:
                #    PmaxFC = Qelec
                
                result[2][4] += gV.NG_PRICE * Qgas * occ - gV.ELEC_PRICE * Qelec * occ # CHF, extra electricity sold to grid
                result[2][5] += 0.0874 * Qgas * occ * 3600E-6 + 773 * 0.45 * Qelec * occ * 1E-6 - gV.EL_TO_CO2 * Qelec * occ * 3600E-6 # kgCO2
                # Bloom box emissions within the FC: 773 lbs / MWh_el (and 1 lbs = 0.45 kg)
                # http://www.carbonlighthouse.com/2011/09/16/bloom-box/
                result[2][6] += 1.51 * Qgas * occ * 3600E-6 - gV.EL_TO_OIL_EQ * Qelec * occ * 3600E-6 # MJ-oil-eq 
                
                # GHP
                for i in range(10):
                    
                    QnomBoiler = i/10 * Qnom
                    QnomGHP = Qnom - QnomBoiler
                    
                    if Qload <= QnomGHP:
                    
                        (wdot_el, qcolddot, qhotdot_missing, tsup2) = HP.GHP_Op(mdot, TsupDH, Tret, gV.TGround)
                        
                        if Wel_GHP[i][0] < wdot_el:
                            Wel_GHP[i][0] = wdot_el
                        
                        result[3+i][4] += gV.ELEC_PRICE * wdot_el * occ # CHF
                        result[3+i][5] += gV.EL_TO_CO2 * wdot_el * occ * 3600E-6 # kgCO2
                        result[3+i][6] += gV.EL_TO_OIL_EQ * wdot_el * occ * 3600E-6 # MJ-oil-eq 
                        
                        #Qgroundused[i][0] += qcolddot
                        # WHAT TO DO WITH THE GROUND HEAT DEPLEATION ?
                        # 6 months / 6 months ? 
                        
                        if qhotdot_missing > 0:
                            print "GHP unable to cover the whole dem, boiler activated!"
                            BoilerEff = Boiler.Cond_Boiler_operation(qhotdot_missing, QnomBoiler, tsup2)
                            Qgas = qhotdot_missing / BoilerEff
                            
                            result[3+i][4] += gV.NG_PRICE * Qgas * occ # CHF
                            result[3+i][5] += gV.NG_BACKUPBOILER_TO_CO2_STD * Qgas * occ * 3600E-6 # kgCO2
                            result[3+i][6] += gV.NG_BACKUPBOILER_TO_OIL_STD * Qgas * occ * 3600E-6 # MJ-oil-eq   
                            
                            QannualB_GHP[i][0] += qhotdot_missing
        
                    else:
                        #print "Boiler activated to compensate GHP", i
                        TexitGHP = QnomGHP / (mdot * gV.cp) + Tret
                        (wdot_el, qcolddot, qhotdot_missing, tsup2) = HP.GHP_Op(mdot, TexitGHP, Tret, gV.TGround)
                        
                        if Wel_GHP[i][0] < wdot_el:
                            Wel_GHP[i][0] = wdot_el
                            
                        result[3+i][4] += gV.ELEC_PRICE * wdot_el * occ # CHF
                        result[3+i][5] += gV.EL_TO_CO2 * wdot_el * occ * 3600E-6 # kgCO2
                        result[3+i][6] += gV.EL_TO_OIL_EQ * wdot_el * occ * 3600E-6 # MJ-oil-eq 
                        
                        #Qgroundused[i][0] += qcolddot
                        # WHAT TO DO WITH THE GROUND HEAT DEPLEATION ?
                        # 6 months / 6 months ? 
                        
                        if qhotdot_missing > 0:
                            print "GHP unable to cover the whole dem, boiler activated!"
                            BoilerEff = Boiler.Cond_Boiler_operation(qhotdot_missing, QnomBoiler, tsup2)
                            Qgas = qhotdot_missing / BoilerEff
                            
                            result[3+i][4] += gV.NG_PRICE * Qgas * occ # CHF
                            result[3+i][5] += gV.NG_BACKUPBOILER_TO_CO2_STD * Qgas * occ * 3600E-6 # kgCO2
                            result[3+i][6] += gV.NG_BACKUPBOILER_TO_OIL_STD * Qgas * occ * 3600E-6 # MJ-oil-eq 
                            
                            QannualB_GHP[i][0] += qhotdot_missing
                        
                        QtoBoiler = Qload - QnomGHP
                        QannualB_GHP[i][0] += QtoBoiler
                        
                        BoilerEff = Boiler.Cond_Boiler_operation(QtoBoiler, QnomBoiler, TexitGHP)
                        Qgas = QtoBoiler / BoilerEff
                        
                        result[3+i][4] += gV.NG_PRICE * Qgas * occ # CHF
                        result[3+i][5] += gV.NG_BACKUPBOILER_TO_CO2_STD * Qgas * occ * 3600E-6 # kgCO2
                        result[3+i][6] += gV.NG_BACKUPBOILER_TO_OIL_STD * Qgas * occ * 3600E-6 # MJ-oil-eq 

        print time.clock() - t0operation, "seconds process time for the operation \n"
        
        # Investment Costs / CO2 / Prim
        InvCaBoiler = Boiler.Cond_Boiler_InvCost(Qnom, Qannual)
        
        InvCosts[0][0] = InvCaBoiler
        InvCosts[1][0] = InvCaBoiler
        
        InvCosts[2][0] = FC.FuelCell_Cost(Qnom)
        
        for i in range(10):
            result[3+i][0] = i/10
            result[3+i][3] = 1-i/10

            QnomBoiler = i/10 * Qnom
            
            InvCaBoiler = Boiler.Cond_Boiler_InvCost(QnomBoiler, QannualB_GHP[i][0])
            InvCosts[3+i][0] = InvCaBoiler
            
            InvCaGHP = HP.GHP_InvCost( Wel_GHP[i][0] )
            InvCosts[3+i][0] += InvCaGHP * gV.EURO_TO_CHF        
        

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
        
        os.chdir(pathDiscRes)
        results_to_csv = pd.DataFrame(dico)
        fName_result = "DiscOp_" + fName[0:(len(fName)-4)] + ".csv"
        results_to_csv.to_csv(fName_result, sep= ',')
    
    print "Disconnected Building Routine Completed"
    print time.clock() - t0, "seconds process time for the Disconnected Building Routine \n"



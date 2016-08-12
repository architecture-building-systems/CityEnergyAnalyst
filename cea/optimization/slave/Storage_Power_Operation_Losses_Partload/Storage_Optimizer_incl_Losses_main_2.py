# -*- coding: utf-8 -*-
""" Storage SIZING"""

"""

This script sizes the storage and in a second part, it will plot the results of iteration. 
Finally, the storage operation is performed with the parameters found in the storage optimization

All results are saved in the folder of "pathSlaveRes".
- Data_with_Storage_applied.csv : Hourly Operation of Storage, especially Q_missing and E_aux is important for further usage
- Storage_Sizing_Parameters.csv : Saves the parameters found in the storage optimization

IMPORTANT : Storage is used for solar thermal energy ONLY!

It is possible to turn off the plots by setting Tempplot = 0 and Qplot = 0 

"""


save_file = 1
import os

import numpy as np
import pandas as pd
import pylab as plt

import cea.optimization.slave.Storage_Power_Operation_Losses_Partload.Storage_Design_And_Operation_2 as StDesOp
reload(StDesOp)

def Storage_Optimization(pathX, fName_NetworkData, context, gV):
    """
    This Function performs the storage optimization and stores the results in the designated folders
     
    
    Parameters
    ----------
    pathNtwRes : string
         path where the network data is saved
    
    pathSlaveRes : string
        path where all slave results should be saved
    
    pathSolarRaw : string
        path where the raw solar data is saved
        
    fName_NetworkData : string
        name of network data file (in pathNtwRes)

    
    Returns
    -------
    - NONE - 
    the function saves all files when it's done
        
    """
    print "Storage Optimization Ready"
    MS_Var = context
    
    CSV_NAME = MS_Var.NETWORK_DATA_FILE
   # SOLCOL_TYPE = MS_Var.SOLCOL_TYPE
    SOLCOL_TYPE = "NONE"
    T_storage_old = MS_Var.T_storage_zero
    Q_in_storage_old = MS_Var.Q_in_storage_zero
    Tempplot = 0
    Qplot = 0
    
    # start with initial size:
    T_ST_MAX = MS_Var.T_ST_MAX
    T_ST_MIN = MS_Var.T_ST_MIN
    
    # initial storage size
    V_storage_initial = MS_Var.STORAGE_SIZE
    V0 = V_storage_initial
    STORE_DATA = "no"
    Q_stored_max0, Q_rejected_fin, Q_disc_seasonstart, T_st_max, T_st_min, Q_storage_content_fin, T_storage_fin, Q_loss0, mdot_DH_fin0, \
        Q_uncontrollable_fin = StDesOp.Storage_Design(CSV_NAME, SOLCOL_TYPE, T_storage_old, Q_in_storage_old, pathX.pathNtwRes, pathX.pathSolarRaw, pathX.pathSlaveRes,\
                                    V_storage_initial, STORE_DATA, context, 1e12, gV)
    
    # Design HP for storage uptake - limit the maximum thermal power, Criterial: 2000h operation average of a year 
    # --> Oral Recommandation of Antonio (former Leibundgut Group)
    P_HP_max = np.sum(Q_uncontrollable_fin) / 2000.0
    print "P_HP_max", np.round(P_HP_max), "W"
    # second Round optimization

    if T_st_max <= T_ST_MAX or T_st_min >= T_ST_MIN or 1: # Start optimizing the storage 
        # first Round optimization
        V_storage_possible_needed = (Q_stored_max0 + Q_loss0) * gV.Wh_to_J / (gV.rho_60 * gV.cp * (T_ST_MAX - T_ST_MIN))
        V1 = V_storage_possible_needed
        Q_initial = min(Q_stored_max0 / 2.0, Q_storage_content_fin[-1])
        T_initial = T_ST_MIN + Q_initial * gV.Wh_to_J / (gV.rho_60 * gV.cp * V_storage_initial)
    
        # assume unlimited uptake to storage during first round optimisation (P_HP_max = 1e12)
        Optimized_Data = StDesOp.Storage_Design(CSV_NAME, SOLCOL_TYPE, T_initial, Q_initial, pathX.pathNtwRes, pathX.pathSolarRaw, pathX.pathSlaveRes,\
                                                                V_storage_possible_needed, STORE_DATA, context, P_HP_max, gV)
        Q_stored_max_opt, Q_rejected_fin_opt,Q_disc_seasonstart_opt, T_st_max_op, T_st_min_op, Q_storage_content_fin_op, \
                                                                T_storage_fin_op, Q_loss1, mdot_DH_fin1, Q_uncontrollable_fin = Optimized_Data
        
        # Design HP for storage uptake - limit the maximum thermal power, Criterial: 2000h operation average of a year 
        # --> Oral Recommandation of Antonio (former Leibundgut Group)
        P_HP_max = np.sum(Q_uncontrollable_fin) / 2000.0
        print "P_HP_max", np.round(P_HP_max), "W"
        # second Round optimization
    
        Q_stored_max_needed = np.amax(Q_storage_content_fin_op) - np.amin(Q_storage_content_fin_op)
        V_storage_possible_needed = Q_stored_max_needed * gV.Wh_to_J / (gV.rho_60 * gV.cp * (T_ST_MAX - T_ST_MIN))
        V2 = V_storage_possible_needed
        Q_initial = min(Q_disc_seasonstart_opt[0],Q_storage_content_fin_op[-1])
        T_initial =  T_ST_MIN + Q_initial * gV.Wh_to_J / (gV.rho_60 * gV.cp * V_storage_possible_needed)
        Optimized_Data2 = StDesOp.Storage_Design(CSV_NAME, SOLCOL_TYPE, T_initial, Q_initial, pathX.pathNtwRes, pathX.pathSolarRaw, pathX.pathSlaveRes,\
                                                                V_storage_possible_needed, STORE_DATA, context, P_HP_max, gV)
        Q_stored_max_opt2, Q_rejected_fin_opt2,Q_disc_seasonstart_opt2, T_st_max_op2, T_st_min_op2, \
                                                        Q_storage_content_fin_op2, T_storage_fin_op2, Q_loss2, mdot_DH_fin2,\
                                                        Q_uncontrollable_fin = Optimized_Data2
    
        # third Round optimization
        Q_stored_max_needed_3 = np.amax(Q_storage_content_fin_op2) - np.amin(Q_storage_content_fin_op2)
        V_storage_possible_needed = Q_stored_max_needed_3 * gV.Wh_to_J / (gV.rho_60 * gV.cp * (T_ST_MAX - T_ST_MIN))
        V3 = V_storage_possible_needed
        
        Q_initial = min(Q_disc_seasonstart_opt2[0],Q_storage_content_fin_op2[-1])
                
        T_initial =  T_ST_MIN + Q_initial * gV.Wh_to_J / (gV.rho_60 * gV.cp * V_storage_initial)
    
        Optimized_Data3 = StDesOp.Storage_Design(CSV_NAME, SOLCOL_TYPE, T_initial, Q_initial, pathX.pathNtwRes, pathX.pathSolarRaw, pathX.pathSlaveRes,\
                                                        V_storage_possible_needed, STORE_DATA, context, P_HP_max, gV)
        Q_stored_max_opt3, Q_rejected_fin_opt3,Q_disc_seasonstart_opt3, T_st_max_op3, T_st_min_op3, \
                                    Q_storage_content_fin_op3, T_storage_fin_op3, Q_loss3, mdot_DH_fin3, Q_uncontrollable_fin = Optimized_Data3
    
    
        # fourth Round optimization - reduce end temperature by rejecting earlier (minimize volume)
        Q_stored_max_needed_4 = Q_stored_max_needed_3 - (Q_storage_content_fin_op3[-1] -Q_storage_content_fin_op3[0])
        V_storage_possible_needed = Q_stored_max_needed_4 * gV.Wh_to_J / (gV.rho_60 * gV.cp * (T_ST_MAX - T_ST_MIN))
        V4 = V_storage_possible_needed
        Q_initial = min(Q_disc_seasonstart_opt3[0],Q_storage_content_fin_op3[-1])
        T_initial =  T_ST_MIN + Q_initial * gV.Wh_to_J / (gV.rho_60 * gV.cp * V_storage_initial)
    
        Optimized_Data4 = StDesOp.Storage_Design(CSV_NAME, SOLCOL_TYPE, T_initial, Q_initial, pathX.pathNtwRes, pathX.pathSolarRaw, pathX.pathSlaveRes,\
                                                        V_storage_possible_needed, STORE_DATA, context, P_HP_max, gV)
        Q_stored_max_opt4, Q_rejected_fin_opt4,Q_disc_seasonstart_opt4, T_st_max_op4, T_st_min_op4,\
                                    Q_storage_content_fin_op4, T_storage_fin_op4, Q_loss4, mdot_DH_fin4, Q_uncontrollable_fin = Optimized_Data4
    
        # fifth Round optimization - minimize volume more so the temperature reaches a T_min + dT_margin
        
        Q_stored_max_needed_5 = Q_stored_max_needed_4 - (Q_storage_content_fin_op4[-1] -Q_storage_content_fin_op4[0])
        V_storage_possible_needed = Q_stored_max_needed_5* gV.Wh_to_J / (gV.rho_60 * gV.cp * (T_ST_MAX - T_ST_MIN))
        V5 = V_storage_possible_needed
        Q_initial = min(Q_disc_seasonstart_opt4[0],Q_storage_content_fin_op4[-1])
        if Q_initial != 0:
            Q_initial_min = Q_disc_seasonstart_opt4 - min(Q_storage_content_fin_op4) #assuming the minimum at the end of the season
            Q_buffer = gV.rho_60 * gV.cp * V_storage_possible_needed * MS_Var.dT_buffer / gV.Wh_to_J
            Q_initial = Q_initial_min + Q_buffer     
            T_initial_real =  T_ST_MIN + Q_initial_min * gV.Wh_to_J / (gV.rho_60 * gV.cp * V_storage_possible_needed)
            T_initial =  MS_Var.dT_buffer + T_initial_real
        else:
            T_initial =  T_ST_MIN + Q_initial * gV.Wh_to_J / (gV.rho_60 * gV.cp * V_storage_initial)
    
        
        STORE_DATA = "yes"
        Optimized_Data5 = StDesOp.Storage_Design(CSV_NAME, SOLCOL_TYPE, T_initial, Q_initial, pathX.pathNtwRes, pathX.pathSolarRaw, pathX.pathSlaveRes,\
                                                                V_storage_possible_needed, STORE_DATA, context, P_HP_max, gV)
        Q_stored_max_opt5, Q_rejected_fin_opt5,Q_disc_seasonstart_opt5, T_st_max_op5, T_st_min_op5, \
                                    Q_storage_content_fin_op5, T_storage_fin_op5, Q_loss5, mdot_DH_fin5, Q_uncontrollable_fin = Optimized_Data5
                                                
        # Attempt for debugging
        #   Issue:    1 file showed miss-match of final to initial storage content of 30%, all others had deviations of 0.5 % max
        #   Idea:     check the final to initial storage content with an allowed margin of 5%.
        #             If this happens, a new storage optimization run will be performed (sixth round) 
        #
        #             If the 5% margin is still not maintined after round 6, cover / fill 
        #             the storage with a conventional boiler up to it's final value. As this re-filling can happen during hours of low
        #             consumption, no extra machinery will be required. 
             
        InitialStorageContent = float(Q_storage_content_fin_op5[0]) 
        FinalStorageContent = float(Q_storage_content_fin_op5[-1]) 
        
        if InitialStorageContent == 0 or FinalStorageContent == 0: # catch error in advance of having 0 / 0
            storageDeviation5 = 0
        else:
            storageDeviation5 = (abs(InitialStorageContent - FinalStorageContent ) / FinalStorageContent)
            
        if storageDeviation5 > 0.01:
            print "occured storage deviation", storageDeviation5
            print "---------------------------------------------------------------"
            print "\n ---------------------------------------------------------------" 
            print " STORAGE EVALUATION NEEDED 6th ROUND" 
            Q_initial = min(Q_disc_seasonstart_opt5[0],Q_storage_content_fin_op5[-1])
    
            Q_stored_max_needed_6 = float(Q_stored_max_needed_5 - (Q_storage_content_fin_op5[-1] -Q_storage_content_fin_op5[0]))
            V_storage_possible_needed = Q_stored_max_needed_6* gV.Wh_to_J / (gV.rho_60 * gV.cp * (T_ST_MAX - T_ST_MIN))
            V5 = V_storage_possible_needed # overwrite V5 on purpose as this is given back in case of a change
            
            # leave initial values as we adjust the final outcome only, give back values from 5th round
            
            
            Optimized_Data6 = StDesOp.Storage_Design(CSV_NAME, SOLCOL_TYPE, T_initial, Q_initial, pathX.pathNtwRes, pathX.pathSolarRaw, pathX.pathSlaveRes,\
                                                        V_storage_possible_needed, STORE_DATA, context, P_HP_max, gV)
            Q_stored_max_opt5, Q_rejected_fin_opt5,Q_disc_seasonstart_opt5, T_st_max_op5, T_st_min_op5, Q_storage_content_fin_op5, \
                                                T_storage_fin_op5, Q_loss5, mdot_DH_fin5,Q_uncontrollable_fin = Optimized_Data6
                
            
            InitialStorageContent   = float(Q_storage_content_fin_op5[0]) 
            FinalStorageContent     = float(Q_storage_content_fin_op5[-1]) 
            
            if InitialStorageContent == 0 or FinalStorageContent == 0: # catch error in advance of having 0 / 0
                storageDeviation6 = 0
            else:
                storageDeviation6 = (abs(InitialStorageContent - FinalStorageContent ) / FinalStorageContent)
            
            print "new storage deviation: ", storageDeviation6
            print "\n --------------- ------------------" 
            

            if 0.05 < InitialStorageContent / abs(InitialStorageContent -FinalStorageContent):
                result = pd.DataFrame([storageDeviation6,InitialStorageContent, FinalStorageContent ])
                result.to_csv(pathX.pathSlaveRes + "/" + MS_Var.configKey + "_StorageFlag.csv", sep= ',')
                
    """ EVALUATION AND FURTHER PROCESSING """
    
    if Tempplot == 1:
            
        fig = plt.figure()
        initial = plt.plot(T_storage_fin-273, label = "Initial Run") 
        first = plt.plot(T_storage_fin_op-273, label = "Initial Run") 
        second = plt.plot(T_storage_fin_op2-273, label = "Initial Run") 
        third = plt.plot(T_storage_fin_op3-273, label = "Initial Run") 
        fourth = plt.plot(T_storage_fin_op4-273, label = "Initial Run") 
        fifth = plt.plot(T_storage_fin_op5-273, label = "Initial Run") 
        plt.xlabel('Hour in Year')
        plt.ylabel('Temperature in degC')
        fig.suptitle('Storage Optimization Runs', fontsize=15)
        plt.legend(["initial", "first", "second", "third", "fourth", "fifth"], loc = "best")
        
        plt.show()
    
    if Qplot == 1:
        Q_storage_content_fin
        fig = plt.figure()
        initial = plt.plot(Q_storage_content_fin/10E6, label = "Initial Run") 
        first = plt.plot(Q_storage_content_fin_op/10E6, label = "Initial Run") 
        second = plt.plot(Q_storage_content_fin_op2/10E6, label = "Initial Run") 
        third = plt.plot(Q_storage_content_fin_op3/10E6, label = "Initial Run") 
        fourth = plt.plot(Q_storage_content_fin_op4/10E6, label = "Initial Run") 
        fifth = plt.plot(Q_storage_content_fin_op5/10E6, label = "Initial Run") 
        plt.xlabel('Hour in Year')
        plt.ylabel('Energy in Storage MWh')
        fig.suptitle('Storage Optimization Runs', fontsize=15)
        plt.legend(["initial", "first", "second", "third", "fourth", "fifth"], loc = "best")
        
        plt.show()
        
    
    
    
    
    # Save Files
    if save_file == 1:
    
        results = pd.DataFrame({"Storage_Size_opt":[V5],"T_initial":[T_initial], "Q_initial":[Q_initial]})
        Name = MS_Var.configKey + "Storage_Sizing_Parameters.csv"
        os.chdir(pathX.pathSlaveRes)
        results.to_csv(Name, sep= ',')
        print "results saved in : ", pathX.pathSlaveRes
        print " as : ", Name, "\n"

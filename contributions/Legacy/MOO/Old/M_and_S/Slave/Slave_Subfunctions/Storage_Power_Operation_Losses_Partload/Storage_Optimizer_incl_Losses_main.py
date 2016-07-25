# -*- coding: utf-8 -*-
""" Storage SIZING"""

"""

This script sizes the storage and in a second part, it will plot the results of iteration. 
Finally, the storage operation is performed with the parameters found in the storage optimization

All results are saved in the folder of "SolarPowerHandler_Results_Path".
- Data_with_Storage_applied.csv : Hourly Operation of Storage, especially Q_missing and Q_aux is important for further usage
- Storage_Sizing_Parameters.csv : Saves the parameters found in the storage optimization

IMPORTANT : Storage is used for solar thermal energy ONLY!

It is possible to turn off the plots by setting Tempplot = 0 and Qplot = 0 

"""

M_to_S_Var_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave"
SolarPowerHandler_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave/Slave_Subfunctions"
Energy_Models_path ="/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/EnergySystem_Models"

# Functions Path
Functions_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/\
M_and_S/Slave/Slave_Subfunctions/Storage_Power_Operation_Losses_Partload/Functions"

# Data Path
Network_Data_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Results/Network_loads"
Building_Data_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Python_Testcases/"
Solar_Data_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/Solar_potential/"
substation_results_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Tools/NewNew"
SolarPowerHandler_Results_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/\
Masterarbeit/M_and_S/Slave/Slave_Subfunctions/Results_from_Subfunctions"
# Results Path
results_path = M_to_S_Var_path

print "Storage Optimization Started"


save_file = 1
import pandas as pd
import os
import numpy as np
import pylab as plt

os.chdir(Functions_Path)

from contributions.Legacy.MOO.optimization.slave.Slave_Subfunctions.Find_Least_Cost_Source import \
    Import_Network_Data_functions as fn

import Storage_Design_And_Operation_2 as StDesOp
os.chdir(Functions_Path)
reload(StDesOp)

import SolarPowerHandler_incl_Losses as SPH_fn
os.chdir(M_to_S_Var_path)
import Master_to_Slave_Variables as MS_Var
reload(MS_Var)

os.chdir(Energy_Models_path)
import globalVar as gV
#os.chdir(SolarPowerHandler_Path)
os.chdir(Functions_Path)
reload(fn)
reload(SPH_fn) 

CSV_NAME = MS_Var.NETWORK_DATA_FILE
SOLCOL_TYPE = MS_Var.SOLCOL_TYPE
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
STORE_DATA = "yes"
Q_stored_max0, Q_rejected_fin, Q_disc_seasonstart, T_st_max, T_st_min, Q_storage_content_fin, T_storage_fin, Q_loss0, mdot_DH_fin0 \
    = StDesOp.Storage_Design(CSV_NAME, SOLCOL_TYPE, T_storage_old, Q_in_storage_old, Network_Data_Path, V_storage_initial, STORE_DATA)


if T_st_max <= T_ST_MAX or T_st_min >= T_ST_MIN: # Start optimizing the storage if there is potential
    # first Round optimization
    V_storage_possible_needed = (Q_stored_max0 + Q_loss0) * gV.Wh_to_J / (gV.rho_60 * gV.cp * (T_ST_MAX - T_ST_MIN))
    V1 = V_storage_possible_needed
    Q_initial = min(Q_stored_max0 / 2.0, Q_storage_content_fin[-1])
    T_initial = T_ST_MIN + Q_initial * gV.Wh_to_J / (gV.rho_60 * gV.cp * V_storage_initial)

    Optimized_Data = StDesOp.Storage_Design(CSV_NAME, SOLCOL_TYPE, T_initial, Q_initial, Network_Data_Path,\
                                                            V_storage_possible_needed, STORE_DATA)
    Q_stored_max_opt, Q_rejected_fin_opt,Q_disc_seasonstart_opt, T_st_max_op, T_st_min_op, Q_storage_content_fin_op, \
                                                            T_storage_fin_op, Q_loss1, mdot_DH_fin1 = Optimized_Data
    
    # second Round optimization

    Q_stored_max_needed = np.amax(Q_storage_content_fin_op) - np.amin(Q_storage_content_fin_op)
    V_storage_possible_needed = Q_stored_max_needed * gV.Wh_to_J / (gV.rho_60 * gV.cp * (T_ST_MAX - T_ST_MIN))
    V2 = V_storage_possible_needed
    Q_initial = min(Q_disc_seasonstart_opt[0],Q_storage_content_fin_op[-1])
    T_initial =  T_ST_MIN + Q_initial * gV.Wh_to_J / (gV.rho_60 * gV.cp * V_storage_possible_needed)
    Optimized_Data2 = StDesOp.Storage_Design(CSV_NAME, SOLCOL_TYPE, T_initial, Q_initial, Network_Data_Path, \
                                                            V_storage_possible_needed, STORE_DATA)
    Q_stored_max_opt2, Q_rejected_fin_opt2,Q_disc_seasonstart_opt2, T_st_max_op2, T_st_min_op2, \
                                                    Q_storage_content_fin_op2, T_storage_fin_op2, Q_loss2, mdot_DH_fin2 = Optimized_Data2

    # third Round optimization
    Q_stored_max_needed_3 = np.amax(Q_storage_content_fin_op2) - np.amin(Q_storage_content_fin_op2)
    V_storage_possible_needed = Q_stored_max_needed_3 * gV.Wh_to_J / (gV.rho_60 * gV.cp * (T_ST_MAX - T_ST_MIN))
    V3 = V_storage_possible_needed
    Q_initial = min(Q_disc_seasonstart_opt2[0],Q_storage_content_fin_op2[-1])
    T_initial =  T_ST_MIN + Q_initial * gV.Wh_to_J / (gV.rho_60 * gV.cp * V_storage_initial)

    Optimized_Data3 = StDesOp.Storage_Design(CSV_NAME, SOLCOL_TYPE, T_initial, Q_initial, Network_Data_Path, \
                                                    V_storage_possible_needed, STORE_DATA)
    Q_stored_max_opt3, Q_rejected_fin_opt3,Q_disc_seasonstart_opt3, T_st_max_op3, T_st_min_op3, \
                                                Q_storage_content_fin_op3, T_storage_fin_op3, Q_loss3, mdot_DH_fin3 = Optimized_Data3


    # fourth Round optimization - reduce end temperature by rejecting earlier (minimize volume)
    Q_stored_max_needed_4 = Q_stored_max_needed_3 - (Q_storage_content_fin_op3[-1] -Q_storage_content_fin_op3[0])
    V_storage_possible_needed = Q_stored_max_needed_4 * gV.Wh_to_J / (gV.rho_60 * gV.cp * (T_ST_MAX - T_ST_MIN))
    V4 = V_storage_possible_needed
    Q_initial = min(Q_disc_seasonstart_opt3[0],Q_storage_content_fin_op3[-1])
    T_initial =  T_ST_MIN + Q_initial * gV.Wh_to_J / (gV.rho_60 * gV.cp * V_storage_initial)

    Optimized_Data4 = StDesOp.Storage_Design(CSV_NAME, SOLCOL_TYPE, T_initial, Q_initial, Network_Data_Path, \
                                                    V_storage_possible_needed, STORE_DATA)
    Q_stored_max_opt4, Q_rejected_fin_opt4,Q_disc_seasonstart_opt4, T_st_max_op4, T_st_min_op4,\
                                            Q_storage_content_fin_op4, T_storage_fin_op4, Q_loss4, mdot_DH_fin4 = Optimized_Data4

    # fifth Round optimization - minimize volume more so the temperature reaches a T_min + dT_margin
    
    Q_stored_max_needed_5 = Q_stored_max_needed_4 - (Q_storage_content_fin_op4[-1] -Q_storage_content_fin_op4[0])
    V_storage_possible_needed = Q_stored_max_needed_5* gV.Wh_to_J / (gV.rho_60 * gV.cp * (T_ST_MAX - T_ST_MIN))
    V5 = V_storage_possible_needed
    Q_initial = min(Q_disc_seasonstart_opt3[0],Q_storage_content_fin_op3[-1])
    if Q_initial != 0:
        Q_initial_min = Q_disc_seasonstart_opt4 - min(Q_storage_content_fin_op4) #assuming the minimum at the end of the season
        Q_buffer = gV.rho_60 * gV.cp * V_storage_possible_needed * MS_Var.dT_buffer / gV.Wh_to_J
        Q_initial = Q_initial_min + Q_buffer     
        T_initial_real =  T_ST_MIN + Q_initial_min * gV.Wh_to_J / (gV.rho_60 * gV.cp * V_storage_possible_needed)
        T_initial =  MS_Var.dT_buffer + T_initial_real
    else:
        T_initial =  T_ST_MIN + Q_initial * gV.Wh_to_J / (gV.rho_60 * gV.cp * V_storage_initial)

    
    STORE_DATA = "yes"
    Optimized_Data5 = StDesOp.Storage_Design(CSV_NAME, SOLCOL_TYPE, T_initial, Q_initial, Network_Data_Path, \
                                                            V_storage_possible_needed, STORE_DATA)
    Q_stored_max_opt5, Q_rejected_fin_opt5,Q_disc_seasonstart_opt5, T_st_max_op5, T_st_min_op5, \
                                            Q_storage_content_fin_op5, T_storage_fin_op5, Q_loss5, mdot_DH_fin5 = Optimized_Data5


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

    results = pd.DataFrame({"Storage_Size_opt":[V5],"T_initial":T_initial, "Q_initial":Q_initial})
    Name = "Storage_Sizing_Parameters.csv"
    os.chdir(SolarPowerHandler_Results_Path)
    results.to_csv(Name, sep= ',')
    print "results saved in : ", SolarPowerHandler_Results_Path
    print " as : ", Name


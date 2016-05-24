""" Storage SIZING"""

"""

This script sizes the storage

"""

M_to_S_Var_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave"
SolarPowerHandler_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave/Slave_Subfunctions"
Energy_Models_path ="/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/EnergySystem_Models"

# Data Path
Network_Data_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Results/Network_loads"
Building_Data_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Python_Testcases/"
Solar_Data_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/Solar_potential/"
substation_results_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Tools/NewNew"

# Results Path
results_path = M_to_S_Var_path



import pandas as pd
import os
import numpy as np
import pylab as plt
import Import_Network_Data_functions as fn
import Storage_Design_And_Operation as StDesOp
os.chdir(SolarPowerHandler_Path)
import SolarPowerHandler_V5 as SPH_fn
os.chdir(M_to_S_Var_path)
import Master_to_Slave_Variables as MS_Var
reload(MS_Var)

os.chdir(Energy_Models_path)
import globalVar as gV
os.chdir(SolarPowerHandler_Path)


reload(fn)
reload(SPH_fn) 
reload(StDesOp)

CSV_NAME = MS_Var.NETWORK_DATA_FILE
SOLCOL_TYPE = MS_Var.SOLCOL_TYPE
T_storage_old = MS_Var.T_storage_zero
Q_in_storage_old = MS_Var.Q_in_storage_zero


# start with initial size:
T_ST_MAX = MS_Var.T_ST_MAX
T_ST_MIN = MS_Var.T_ST_MIN

# initial storage size
V_storage_initial = MS_Var.STORAGE_SIZE

Q_stored_max, Q_rejected_fin, Q_disc_seasonstart, T_st_max, T_st_min, Q_storage_content_fin, T_storage_fin = StDesOp.Storage_Design(CSV_NAME, SOLCOL_TYPE, T_storage_old, Q_in_storage_old, Network_Data_Path, V_storage_initial)


if T_st_max <= T_ST_MAX or T_st_min >= T_ST_MIN: # STart optimizing

    V_storage_possible_needed = Q_stored_max * gV.Wh_to_J / (gV.rho_60 * gV.cp * (T_ST_MAX - T_ST_MIN))
    Q_initial = Q_stored_max / 2.0
    T_initial =  T_ST_MIN + Q_initial * gV.Wh_to_J / (gV.rho_60 * gV.cp * V_storage_initial)
    
    print "yes"
    #deltaT_disc_seasonstart = T_st_min + Q_disc_seasonstart * gV.Wh_to_J / (gV.rho_60 * gV.cp * V_storage_initial)
    #T1 = (T_storage_fin[-1] - deltaT_disc_seasonstart[0])
    #T2 = T_ST_MIN
    #T_storage_old = max(T1,T2)
    #Q_in_storage_old_op = Q_storage_content_fin[-1] - min(Q_storage_content_fin)
    #T_storage_old_op = T_storage_fin[-1] - min(Q_storage_content_fin) * 1 / gV.Wh_to_J / ( gV.rho_60 * gV.cp * V_storage_initial)
    #Q_in_storage_old = V_storage_possible * gV.rho_60 * gV.cp * (T_storage_old - T_ST_MIN) / gV.Wh_to_J
    
    Optimized_Data = StDesOp.Storage_Design(CSV_NAME, SOLCOL_TYPE, T_initial, Q_initial, Network_Data_Path, V_storage_possible_needed)
    Q_stored_max_opt, Q_rejected_fin_opt,Q_disc_seasonstart_opt, T_st_max_op, T_st_min_op, Q_storage_content_fin_op, T_storage_fin_op = Optimized_Data
    
    Q_stored_max_needed = np.amax(Q_storage_content_fin_op) - np.amin(Q_storage_content_fin_op)
    
    V_needed_2 = Q_stored_max_needed * gV.Wh_to_J / (gV.rho_60 * gV.cp * (T_ST_MAX - T_ST_MIN))
    
    #V_storage_opt2 = Q_stored_max_opt * gV.Wh_to_J / (gV.rho_60 * gV.cp * (T_st_max_op - T_st_min_op))
    T_disc_seasonstart =  T_storage_fin_op[0] - min(T_storage_fin_op) 
    Q_in_storage_old = Q_storage_content_fin_op[0] - min(Q_storage_content_fin_op)
    T_disc_seasonstart = 273.0+10
    Q_in_storage_old = 0
    Optimized_Data2 = StDesOp.Storage_Design(CSV_NAME, SOLCOL_TYPE, T_disc_seasonstart, Q_in_storage_old, Network_Data_Path, V_needed_2)
    Q_stored_max_opt2, Q_rejected_fin_opt2, Q_disc_seasonstart_opt2, T_st_max_op2, T_st_min_op2, Q_storage_content_fin_op2, T_storage_fin_op2 = Optimized_Data
    
    
    
plt.plot(Q_storage_content_fin-273) 
plt.plot(Q_storage_content_fin_op-273) 
plt.plot(Q_storage_content_fin_op2-273) 
plt.show()
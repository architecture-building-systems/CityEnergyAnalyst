    # -*- coding: utf-8 -*-
""" 

Import Network Data:
  
    This File reads all relevant thermal data for further analysis in the Slave Routine
            
"""
#STORE DATA?:

STORE_DATA = "yes"

# Modules Path
M_to_S_Var_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave"
SolarPowerHandler_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave/Slave_Subfunctions"

# Data Path
Network_Data_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Results/Network_loads"
Building_Data_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Python_Testcases/"
SolarPowerHandler_Results_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave/Slave_Subfunctions/Results_from_Subfunctions"
Solar_Data_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/Solar_potential/"
substation_results_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Tools/NewNew"

# Results Path
results_path = M_to_S_Var_path

import pandas as pd
import os
import numpy as np
import Import_Network_Data_functions_Backup as fn
os.chdir(SolarPowerHandler_Path)
import SolarPowerHandler as SPH_fn
os.chdir(M_to_S_Var_path)
import Master_to_Slave_Variables as MS_Var

reload(fn)
reload(MS_Var)
reload(SPH_fn) 


HOURS_IN_DAY = 24
DAYS_IN_YEAR = 365

CSV_NAME = MS_Var.NETWORK_DATA_FILE
SOLCOL_TYPE = MS_Var.SOLCOL_TYPE

# Import Data from Storage Optimization
os.chdir(SolarPowerHandler_Results_Path)

Q_in_storage_old = np.array(pd.read_csv("Storage_Sizing_Parameters.csv", usecols=["Q_initial"], nrows=24*DAYS_IN_YEAR))
STORAGE_SIZE= np.array(pd.read_csv("Storage_Sizing_Parameters.csv", usecols=["Storage_Size_opt"], nrows=24*DAYS_IN_YEAR))
T_storage_old  = np.array(pd.read_csv("Storage_Sizing_Parameters.csv", usecols=["T_initial"], nrows=24*DAYS_IN_YEAR))


# Import Network Data
os.chdir(Network_Data_Path)
Network_Data = fn.import_network_data(CSV_NAME, DAYS_IN_YEAR, HOURS_IN_DAY)

# recover Network  Data:
mdot_heat_netw_total = Network_Data[0]
mdot_cool_netw_total = Network_Data[1]
Q_DH_networkload = Network_Data[2]
Q_DC_networkload = Network_Data[3]
T_DH_return_array = Network_Data[4]
T_DC_return_array = Network_Data[5]

# Import Solar Data
os.chdir(Solar_Data_Path)
Solar_Data  = fn.import_solar_data(SOLCOL_TYPE, DAYS_IN_YEAR, HOURS_IN_DAY)

# Recover Solar Data
Solar_Area = Solar_Data[0]
Solar_E_aux_W = Solar_Data[1] * 1000
Solar_Q_th_W = Solar_Data[2] * 1000
Solar_Tscs_th = Solar_Data[3] + 273.0
Solar_mcp_W_C = Solar_Data[4] * 1000

#iterate over this loop: 
HOUR = 0
Q_to_storage_avail = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
Q_from_storage = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
to_storage = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
Q_storage_content_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
T_storage_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
Q_from_storage_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
Q_to_storage_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
Q_aux_ch_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
Q_aux_dech_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
Q_aux_solar = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
Q_missing_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
Q_from_storage_used_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)
Q_rejected_fin = np.zeros(HOURS_IN_DAY*DAYS_IN_YEAR)

T_amb = 10 + 273.0 # K
T_storage_min = MS_Var.T_ST_MAX
Q_disc_seasonstart = 0 
while HOUR < HOURS_IN_DAY*DAYS_IN_YEAR:
    Q_solar_available = Solar_Q_th_W[HOUR]
    Q_network_demand = Q_DH_networkload[HOUR]
    Q_to_storage_avail[HOUR], Q_from_storage[HOUR], to_storage[HOUR] = SPH_fn.StorageGateway(Q_solar_available, Q_network_demand)
    
    T_DH_sup = 65 + 273.0
    T_DH_return = T_DH_return_array[HOUR]
    mdot_DH = mdot_heat_netw_total[HOUR]
    
    Storage_Data = SPH_fn.Storage_Operator(Q_solar_available, Q_network_demand, T_storage_old, T_DH_sup, T_amb, Q_in_storage_old, T_DH_return, mdot_DH, STORAGE_SIZE)

    Q_in_storage_new = Storage_Data[0]
    T_storage_new = Storage_Data[1]
    Q_to_storage_final = Storage_Data[3]
    Q_from_storage_req_final = Storage_Data[2]
    Q_aux_ch = Storage_Data[4]
    Q_aux_dech = Storage_Data[5]
    Q_missing = Storage_Data[6]
    Q_from_storage_used_fin[HOUR] = Storage_Data[7]

    if Q_in_storage_new < 1:
        Q_in_storage_new = 0

    
    if T_storage_new >= MS_Var.T_ST_MAX-0.001: # no more charging possible - reject energy
        Q_in_storage_new = Q_in_storage_old
        Q_to_storage_final = Storage_Data[3]
        Q_rejected_fin[HOUR] = Q_to_storage_final
        T_storage_new = T_storage_old
        Q_aux_ch = 0
        

        
    Q_storage_content_fin[HOUR] = Q_in_storage_new
    Q_in_storage_old = Q_in_storage_new
    
    T_storage_fin[HOUR] = T_storage_new
    T_storage_old = T_storage_new
    
    if T_storage_old < T_amb-1: # chatch an error
        print "ERROR!"
        break
    
    Q_from_storage_fin[HOUR] = Q_from_storage_req_final
    Q_to_storage_fin[HOUR] = Q_to_storage_final
    Q_aux_ch_fin[HOUR] = Q_aux_ch
    Q_aux_dech_fin[HOUR] = Q_aux_dech
    Q_aux_solar[HOUR] = Solar_E_aux_W[HOUR]
    Q_missing_fin[HOUR] = Q_missing
    
    Q_from_storage_fin[HOUR] = Q_DH_networkload[HOUR,0] - Q_missing
    
    if T_storage_new <= T_storage_min:
        T_storage_min = T_storage_new
        Q_disc_seasonstart += Q_from_storage_req_final
        
    
    HOUR += 1
    
    
    """ STORE DATA """
if STORE_DATA == "yes":
    
    results = pd.DataFrame({"Q_storage_content_Wh":Q_storage_content_fin, "Q_DH_networkload":Q_DH_networkload[:,0], "Solar_Q_th_W":Solar_Q_th_W[:,0], "Q_to_storage":Q_to_storage_fin, "Q_from_storage_used":Q_from_storage_used_fin,"Q_aux_ch":Q_aux_ch_fin, "Q_aux_dech":Q_aux_dech_fin, "Q_missing":Q_missing_fin})
    Name = "Data_with_Storage_applied.csv"
    os.chdir(results_path)
    results.to_csv(Name, sep= ',')
    
    print "Results saved in :", results_path


Q_stored_max = np.amax(Q_storage_content_fin)
T_st_max = np.amax(T_storage_fin)
T_st_min = np.amin(T_storage_fin)

        
""" DESCRIPTION FOR FUTHER USAGE"""
# Q_missing_fin  : has to be replaced by other means, like a HP
# Q_from_storage_fin : What is used from Storage
# Q_aus_fin : how much energy was spent on Auxillary power !! NOT WORKING PROPERLY !!
# Q_from_storage_fin : How much energy was used from the storage !! NOT WORKING PROPERLY !!
# Q_missing_fin : How much energy is missing



""" # TESTING 

Q_to_storage_test = 0
Q_from_storage_test = 0
it = 0
Q_in_storage_test = np.zeros(len(to_storage)) 

while it < len(to_storage):
    if to_storage[it] == 1:
        Q_to_storage_test += Q_to_storage_fin[it]
    else:
        Q_from_storage_test += Q_from_storage_fin[it]
        
    if Q_in_storage_test[it] > 0:
        Q_in_storage_test[it] += Q_to_storage_fin[it] - Q_from_storage_fin[it]
    
    else:
        Q_in_storage_test[it] += Q_to_storage_fin[it]
    it += 1
"""

""" 

Network Summary:
    this file summarizes the network demands and will give them as:
        - absolute values (design values = extreme values)
        - hourly operation scheme of input/output of network
            
"""


import numpy as np
import pandas as pd
import summarize_network_functions as fn
reload(fn)
import os
import csv
import sys

reload(fn)

print "Network Summary Ready"

def Network_Summary():
        
    HOURS_IN_DAY = 24
    DAYS_IN_YEAR = 365
    
    substation_results_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Python_Testcases/ZONE_3_B/Results"
    data_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Python_Testcases/"
    results_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Results/Network_loads"
    
    os.chdir(data_path)
    
    # Recover building list 
    
    building_list_dataframe = pd.read_csv("Total.csv", sep=",", usecols=["Name"])
    building_list_array_helper = np.array(building_list_dataframe) 
    building_list_array = building_list_array_helper[:]  + "_result.csv"
    building_list = np.array(building_list_array[:,0]).tolist() #transfer building array to list
        
    
    os.chdir(substation_results_path)
    
    print "start reading data from:", substation_results_path
    
    
    #create empty arrays to save data in it in a later step - zeroth entry for building ID (= fName)
    
    mdot_heat_netw_all = np.zeros((DAYS_IN_YEAR * HOURS_IN_DAY, len(building_list_array)))
    mdot_cool_netw_all = np.zeros((DAYS_IN_YEAR * HOURS_IN_DAY, len(building_list_array)))
    T_sst_heat_return_netw_all = np.zeros((DAYS_IN_YEAR * HOURS_IN_DAY, len(building_list_array)))
    T_sst_heat_supply_netw_all = np.zeros((DAYS_IN_YEAR * HOURS_IN_DAY, len(building_list_array)))
    T_sst_cool_return_netw_all = np.zeros((DAYS_IN_YEAR * HOURS_IN_DAY, len(building_list_array)))
    Q_DH_building_netw_all = np.zeros((DAYS_IN_YEAR * HOURS_IN_DAY, len(building_list_array)))
    Q_DC_building_netw_all = np.zeros((DAYS_IN_YEAR * HOURS_IN_DAY, len(building_list_array)))
    
    Q_DH_building_max_netw_all = np.zeros((len(building_list_array)))
    Q_DC_building_max_netw_all = np.zeros((len(building_list_array)))
    T_sst_heat_supply_ofmaxQh_netw_all = np.zeros((len(building_list_array)))
    T_sst_heat_return_ofmaxQh_netw_all = np.zeros((len(building_list_array)))
    T_sst_cool_return_ofmaxQc_netw_all = np.zeros((len(building_list_array)))
    
    mdot_heat_netw_total = np.zeros((DAYS_IN_YEAR * HOURS_IN_DAY))
    mdot_cool_netw_total = np.zeros((DAYS_IN_YEAR * HOURS_IN_DAY))
    T_sst_heat_return_netw_total = np.zeros((DAYS_IN_YEAR * HOURS_IN_DAY))
    T_sst_heat_supply_netw_total = np.zeros((DAYS_IN_YEAR * HOURS_IN_DAY))
    T_sst_cool_return_netw_total = np.zeros((DAYS_IN_YEAR * HOURS_IN_DAY))
    Q_DH_building_netw_total = np.zeros((DAYS_IN_YEAR * HOURS_IN_DAY))
    Q_DC_building_netw_total = np.zeros((DAYS_IN_YEAR * HOURS_IN_DAY))
    sum_mdot_T_heat = np.zeros((DAYS_IN_YEAR * HOURS_IN_DAY))
    sum_mdot_T_cool = np.zeros((DAYS_IN_YEAR * HOURS_IN_DAY))
    
    
    
    #summarize the data of all buildings in one array
    for i in range(len(building_list_array)):
        fName = building_list_array[i,0]
        substation_data = fn.import_substation_data(fName, DAYS_IN_YEAR, HOURS_IN_DAY)
    
        # recover substation data
        mdot_heat_netw_all[:,i] = np.ravel(substation_data[0])
        mdot_cool_netw_all[:,i] = np.ravel(substation_data[1])
        T_sst_heat_return_netw_all[:,i] = np.ravel(substation_data[2])
        T_sst_heat_supply_netw_all[:,i] = np.ravel(substation_data[3])
        T_sst_cool_return_netw_all[:,i] = np.ravel(substation_data[4])
        Q_DH_building_netw_all[:,i] = np.ravel(substation_data[5])
        Q_DC_building_netw_all[:,i] = np.ravel(substation_data[6])
        
        Q_DH_building_max_netw_all[i] = np.ravel(substation_data[7])
        Q_DC_building_max_netw_all[i] = np.ravel(substation_data[8])
        T_sst_heat_supply_ofmaxQh_netw_all[i] = np.ravel(substation_data[9])
        T_sst_heat_return_ofmaxQh_netw_all[i] = np.ravel(substation_data[10])
        T_sst_cool_return_ofmaxQc_netw_all[i] = np.ravel(substation_data[11])
        
        
    # evaluate mdot_max
    for i in range(DAYS_IN_YEAR * HOURS_IN_DAY):
        
        mdot_heat_netw_total[i] = sum(mdot_heat_netw_all[i,:]) # Hourly massflow in system
        mdot_cool_netw_total[i] = sum(mdot_cool_netw_all[i,:])
        Q_DH_building_netw_total[i] = sum(Q_DH_building_netw_all[i,:])
        Q_DC_building_netw_total[i] = sum(Q_DC_building_netw_all[i,:])
        
        for k in range(len(building_list)):
            sum_mdot_T_heat[i] += T_sst_heat_return_netw_all[i,k] * mdot_heat_netw_all[i,k]
            sum_mdot_T_cool[i] += T_sst_cool_return_netw_all[i,k] * mdot_cool_netw_all[i,k]
    
        T_sst_heat_return_netw_total[i] = sum_mdot_T_heat[i] / mdot_heat_netw_total[i] # assume perfect mixing of fluids in return pipe
        T_sst_cool_return_netw_total[i] = sum_mdot_T_cool[i] / mdot_cool_netw_total[i]
    
        
    T_sst_heat_supply_netw_total = np.array(pd.read_csv(fName, usecols=["T_supply_DH_result"], nrows=24*DAYS_IN_YEAR))
    
    mdot_heat_netw_max = np.amax(mdot_heat_netw_total)
    mdot_cool_netw_max = np.amax(mdot_cool_netw_total)
    
    day_of_max_heatmassflow = fn.find_index_of_max(mdot_heat_netw_total)
    day_of_max_coolmassflow = fn.find_index_of_max(mdot_cool_netw_total)
    
    T_sst_heat_return_netw_total_max = T_sst_heat_return_netw_total[day_of_max_heatmassflow]
    T_sst_cool_return_netw_total_max = T_sst_cool_return_netw_total[day_of_max_coolmassflow]
    
    #print T_sst_cool_return_netw_total_max
    #print day_of_max_coolmassflow
    #print T_sst_cool_return_netw_total
    
    results = pd.DataFrame({"mdot_heat_netw_total":mdot_heat_netw_total,"mdot_cool_netw_total":mdot_cool_netw_total, \
                "Q_DH_building_netw_total":Q_DH_building_netw_total,"Q_DC_building_netw_total":Q_DC_building_netw_total,\
                "T_sst_heat_return_netw_total":T_sst_heat_return_netw_total,"T_sst_cool_return_netw_total":\
                T_sst_cool_return_netw_total,#"mdot_heat_netw_max":mdot_heat_netw_max,"mdot_cool_netw_max":[mdot_cool_netw_max],\
                "T_sst_heat_supply_netw_total":T_sst_heat_supply_netw_total[:,0],
                #"day_of_max_heatmassflow":[day_of_max_heatmassflow], "T_sst_heat_return_netw_total_max":T_sst_heat_return_netw_total_max,\
                #"T_sst_cool_return_netw_total_max":[T_sst_cool_return_netw_total_max],"day_of_max_coolmassflow":[day_of_max_coolmassflow]\
                })
    fName_result = "Network_summary_result_new_loads_6_11_2014.csv"
    os.chdir(results_path)
    results.to_csv(fName_result, sep= ',')
    os.chdir(data_path)
    
    print "Results saved in :", results_path
    
    print "DONE"
    
        
        
        

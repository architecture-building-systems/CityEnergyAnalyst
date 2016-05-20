# -*- coding: utf-8 -*-




""" User inputs - Global Variables """

hex_type = "MT" # heat exchanger type
U = 2000 # U-value of the heat exchanger
CP_WATER = 4185.5 # J/KgK
cp = CP_WATER
HOURS_IN_DAY = 24
DAYS_IN_YEAR = 365
mdot_step_counter = [0.05, 0.1, 0.15 ,0.3, 0.4, 0.5 , 0.6, 1] # scheme for massflow in DH in % 



# specify the path where all files are located!

import csv
import os
import scipy
from scipy import optimize
from scipy import log
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import substation_cooling_functions as fn

reload(fn)


os.chdir("/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Python_Testcases")


""" CODE STARTS HERE """

# import data
building_list_dataframe = pd.read_csv("Total.csv", sep=",", usecols=["Name"])
building_list_array_helper = np.array(building_list_dataframe) 
building_list_array = building_list_array_helper[:]  + ".csv"
building_list = np.array(building_list_array[:,0]).tolist() #transfer building array to list

# ... gives maximum supply temperature to building = T_s2 after Palsson et al
T_supply_max_all_buildings = fn.find_max_temp_of_buildings(building_list, "tshs", DAYS_IN_YEAR, HOURS_IN_DAY)
# ... gives maximum return temperature to building = T_r2 after Palsson et al
T_return_min_all_buildings = fn.find_max_temp_of_buildings(building_list, "tshs", DAYS_IN_YEAR, HOURS_IN_DAY)


# performing the main loop :
for i in range(len(building_list_array)):
    fName = building_list_array[i,0]
    print "currently working on :", fName
    
    thermal_data = fn.import_thermal_data(fName, DAYS_IN_YEAR, HOURS_IN_DAY)
    Q_finalheat_array = thermal_data[0]
    Q_heating_array = thermal_data[1]
    Q_dhw_array = thermal_data[2]
    Q_cool_array = thermal_data[3]
    Electr_array = thermal_data[4]
    T_supply_array = thermal_data[5]
    T_return_array = thermal_data[6]
    T_amb_array = thermal_data[7]
    T_return_min_global = thermal_data[8]
    T_supply_max_global = thermal_data[9]
    T_amb_max = thermal_data[10]
    Q_cool_max = thermal_data[11]
    Q_heating_design = thermal_data[12]
    Q_dhw_design = thermal_data[13]
    Q_finalheat_design = thermal_data[14]
    mdot_internal_dhw_array = thermal_data[15]
    mdot_internal_dhw_design = thermal_data[16]
    mdot_internal_heating_array = thermal_data[17]
    mdot_internal_heating_design = thermal_data[18]
        
        
    
    # summarize temperature inputs
    temperature_data = T_amb_array, T_supply_max_all_buildings, T_return_min_all_buildings 
    
    # calculating the heat-exchanger design data
    hex_design_data = fn.design_inhouse_exchangers(Q_heating_design, Q_dhw_design, T_return_min_global, T_supply_max_global, mdot_internal_dhw_design, mdot_internal_heating_design, hex_type, U, cp)
    
    # calculate the demands
    result_arrays = fn.translate_J_plus_to_DH_requirements(DAYS_IN_YEAR, HOURS_IN_DAY, thermal_data, hex_design_data, hex_type, temperature_data, U, cp, mdot_step_counter)
    
    # unpack the results
    mdot_DH_result = result_arrays[0]
    T_return_DH_result = result_arrays[1]
    T_supply_DH_result = result_arrays[2]
    mdot_heating_reslt = result_arrays[3]
    mdot_dhw_result = result_arrays[4]
    T_r1_dhw_result = result_arrays[5]
    T_r1_heating_result = result_arrays[6]
    A_hex_heating_design = result_arrays[7]
    A_hex_dhw_design = result_arrays[8]

    # creating flat arrays from 365x 24h format for further processing: 
    mdot_DH_result_flat = mdot_DH_result.ravel(0)
    T_return_DH_result_flat = T_return_DH_result.ravel(0)
    T_supply_DH_result_flat = T_supply_DH_result.ravel(0)
    mdot_heating_result_flat = mdot_heating_reslt.ravel(0)
    mdot_dhw_result_flat =  mdot_dhw_result.ravel(0)
    T_r1_dhw_result_flat = T_r1_dhw_result.ravel(0)
    T_r1_heating_result_flat = T_r1_heating_result.ravel(0)
    Q_heating_array_flat = Q_heating_array.ravel(0)
    Q_dhw_array_flat = Q_dhw_array.ravel(0)
    
    
    # save the results into a .csv file
    results = pd.DataFrame({"mdot_DH_result":mdot_DH_result_flat,"T_return_DH_result":T_return_DH_result_flat,"T_supply_DH_result":T_supply_DH_result_flat, "mdot_heating_result":mdot_heating_result_flat,"mdot_dhw_result":mdot_dhw_result_flat, "T_r1_dhw_result":T_r1_dhw_result_flat,"T_r1_heating_result":T_r1_heating_result_flat,"A_hex_heating_design":A_hex_heating_design, "A_hex_dhw_design":A_hex_dhw_design, "Q_heating":Q_heating_array_flat, "Q_dhw":Q_dhw_array_flat})
    fName_result = building_list_array[i,0] + "_result.csv"
    os.chdir("/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Results/current")
    results.to_csv(fName_result, sep= ',')
    os.chdir("/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Python_Testcases")
    
print "Results saved in :", "/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Results"

print "DONE"


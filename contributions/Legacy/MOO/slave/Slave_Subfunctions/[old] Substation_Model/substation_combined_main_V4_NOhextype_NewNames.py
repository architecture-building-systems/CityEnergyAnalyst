# -*- coding: utf-8 -*-

""" 

SUBSTATION MODEL:
    
Using the substation model, one can identify the mass flows as well as temperatures 
of supply and return in the district network for heating and cooling. At the same time, 
the required heat exchanger area for the operation is calculated.

    ! always use this file in combination with the substation_combined_functions.py !
    
"""



""" User inputs - Global Variables """

#hex_type = "MT" # heat exchanger type
#U = 840 # U-value of the heat exchanger (for heating purposes)
#U_cool = 840 # U-Value of the cooling heat-exchanger
#CP_WATER = 4185.5 # J/KgK
#cp = CP_WATER
#HOURS_IN_DAY = 24
#DAYS_IN_YEAR = 365
mdot_step_counter = [0.05, 0.1, 0.15 ,0.3, 0.4, 0.5 , 0.6, 1] # scheme for massflow in DH in % 
mdot_cool_step_counter = [0, 0.2, 0.5, 0.8, 1] # scheme for massflow in cooling network, in %
T_cool_supply_min_global = 4 + 273.0 # Design supply temperature for cooling network
T_cool_return_max_global = 11 + 273.0 # Design return temperature for cooling network

    
"""Name the path, where the data should be taken from and results should be stored!"""

pathRaw = "/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Python_Testcases/ZONE_3_B/ZONE_3"
pathSlaveRes = "/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Python_Testcases/ZONE_3_B/Results"
Energy_Models_path ="/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/EnergySystem_Models"


# specify the path where all files are located!

import csv
import os
import scipy
from scipy import optimize
from scipy import log
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import substation_combined_functions_V4_NOhextype_NewName as fn
reload(fn)
#os.chdir(Energy_Models_path)
from slave import globalVar as gV
reload(gV)
os.chdir(pathRaw)

print "Substation Model Ready"

""" CODE STARTS HERE """

def Substation_Calculation(pathRaw):
    os.chdir(pathRaw)
    # import data
    building_list_dataframe = pd.read_csv("Total.csv", sep=",", usecols=["Name"])
    building_list_array_helper = np.array(building_list_dataframe) 
    building_list_array = building_list_array_helper[:]  + ".csv"
    building_list = np.array(building_list_array[:,0]).tolist() #transfer building array to list
    
    # ... gives maximum supply temperature to building = T_s2 after Palsson et al
    T_heating_sup_max_all_buildings = np.array(fn.find_max_temp_of_buildings(building_list, "tsh", gV.DAYS_IN_YEAR, gV.HOURS_IN_DAY))
    # ... gives maximum return temperature to building = T_r2 after Palsson et al
    T_return_max_all_buildings = fn.find_max_temp_of_buildings(building_list, "trh", gV.DAYS_IN_YEAR, gV.HOURS_IN_DAY)
    
    T_hotwater_max_all_buildings = fn.find_max_temp_of_buildings(building_list, "tsww", gV.DAYS_IN_YEAR, gV.HOURS_IN_DAY)
    T_hotwater_design = np.amax(T_hotwater_max_all_buildings)
    
    T_supply_max_all_buildings = np.zeros((gV.DAYS_IN_YEAR, gV.HOURS_IN_DAY))
    
    for day in range(gV.DAYS_IN_YEAR):
        for hour in range(gV.HOURS_IN_DAY):
            T_supply_max_all_buildings[day, hour] = max(T_hotwater_max_all_buildings[day, hour],T_heating_sup_max_all_buildings[day, hour])
            
            
    
    print "start reading data from:", pathRaw 
    
    # performing the main loop :
    for i in range(len(building_list_array)):
        fName = building_list_array[i,0]
        print "importing data from file :", fName
        
        thermal_data = fn.import_thermal_data(fName, gV.DAYS_IN_YEAR, gV.HOURS_IN_DAY)
        
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
        mdot_internal_cool_array = thermal_data[19]
        mdot_internal_cool_design = thermal_data[20]
        T_cool_internal_supply_array = thermal_data[21]
        T_cool_internal_return_array = thermal_data[22]
        T_cool_internal_supply_min_global = thermal_data[23]
        T_cool_internal_return_max_global = thermal_data[24]
    
        
        # summarize temperature inputs
        temperature_data = T_amb_array, T_supply_max_all_buildings, T_return_max_all_buildings 
        
        #find maximum temperature of all costumers, design heat exchanger for that purpose
        
        
        # calculating the heat-exchanger design data
        hex_design_data = fn.design_inhouse_exchangers(Q_heating_design, Q_dhw_design, T_hotwater_design, T_return_min_global, T_supply_max_global, mdot_internal_dhw_design, mdot_internal_heating_design, Q_cool_max, T_cool_return_max_global, T_cool_supply_min_global, mdot_internal_cool_design, gV.U_cool, gV.U_heat, gV.cp)
        #hex_design_data = fn.design_inhouse_exchangers(Q_heating_design, Q_dhw_design, T_return_min_global, T_supply_max_global, mdot_internal_dhw_design, mdot_internal_heating_design, Q_cool_max, T_cool_return_max_global, T_cool_supply_min_global, mdot_internal_cool_design, gV.U_cool, """hex_type,""" gV.U_heat, gV.cp)
                            
        # calculate the demands
        result_arrays = fn.translate_J_plus_to_DH_requirements(gV.DAYS_IN_YEAR, gV.HOURS_IN_DAY, thermal_data, hex_design_data, temperature_data, gV.U_heat, gV.U_cool, gV.cp, mdot_step_counter, mdot_cool_step_counter, T_cool_return_max_global, T_cool_supply_min_global)
        #result_arrays = fn.translate_J_plus_to_DH_requirements(gV.DAYS_IN_YEAR, gV.HOURS_IN_DAY, thermal_data, hex_design_data, """hex_type""", temperature_data, gV.U_heat, gV.U_cool, gV.cp, mdot_step_counter, mdot_cool_step_counter, T_cool_return_max_global, T_cool_supply_min_global)
        
        # unpack the results
        mdot_DH_result = result_arrays[0]
        T_return_DH_result = result_arrays[1]
        T_supply_DH_result = result_arrays[2]
        mdot_heating_reslt = result_arrays[3]
        mdot_dhw_result = result_arrays[4]
        mdot_cool_result = result_arrays[5]
        T_r1_dhw_result = result_arrays[6]
        T_r1_heating_result = result_arrays[7]
        T_r1_cool_result = result_arrays[8]
        A_hex_heating_design = result_arrays[9]
        A_hex_dhw_design = result_arrays[10]
        A_hex_cool_design = result_arrays[11]
        
    
    
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
        Q_cool_array_flat = Q_cool_array.ravel(0)
        mdot_cool_result_flat = mdot_cool_result.ravel(0)
        T_r1_cool_result_flat = T_r1_cool_result.ravel(0)
        T_supply_max_all_buildings_flat = T_supply_max_all_buildings.ravel(0)
        T_hotwater_max_all_buildings_flat = T_hotwater_max_all_buildings.ravel(0)
        T_heating_sup_max_all_buildings_flat = T_heating_sup_max_all_buildings.ravel(0)
            
        
    
        
        # save the results into a .csv file
        results = pd.DataFrame({"mdot_DH_result":mdot_DH_result_flat,"T_return_DH_result":T_return_DH_result_flat,\
                    "T_supply_DH_result":T_supply_DH_result_flat, "mdot_heating_result":mdot_heating_result_flat,\
                    "mdot_dhw_result":mdot_dhw_result_flat, "mdot_DC_result":mdot_cool_result_flat, "T_r1_dhw_result":\
                    T_r1_dhw_result_flat,"T_r1_heating_result":T_r1_heating_result_flat, "T_return_DC_result":\
                    T_r1_cool_result_flat, "A_hex_heating_design":A_hex_heating_design, "A_hex_dhw_design":A_hex_dhw_design, \
                    "A_hex_cool_design":A_hex_cool_design, "Q_heating":Q_heating_array_flat, "Q_dhw":Q_dhw_array_flat, \
                    "Q_cool":Q_cool_array_flat, "T_total_supply_max_all_buildings_intern":T_supply_max_all_buildings_flat,\
                    "T_hotwater_max_all_buildings_intern":T_hotwater_max_all_buildings_flat, \
                    "T_heating_max_all_buildings_intern":T_heating_sup_max_all_buildings_flat})
        fName_result = building_list_array[i,0][ 0 : len(building_list_array[i,0]) - 4 ] + "_result.csv"
        os.chdir(pathSlaveRes)
        results.to_csv(fName_result, sep= ',')
        os.chdir(pathRaw)
        
    print "Results saved in :", pathSlaveRes
    
    print "DONE"
    
    return

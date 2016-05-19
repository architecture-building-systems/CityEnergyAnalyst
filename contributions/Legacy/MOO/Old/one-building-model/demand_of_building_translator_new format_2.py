# -*- coding: utf-8 -*-


## Name the buildings of your network:

fName = "TH03.csv"
fName2 = "AA16.csv"
fName3 = "AA01.csv"
fName4 = "AA02.csv"
fName5 = "AA03.csv"
fName6 = "AA04.csv"
fName7 = "AA05.csv"
fName8 = "AA06.csv"
fName9 = "AA07.csv"
fName10 = "AA08.csv"
fName11 = "AA09.csv"
fName12 = "AA10.csv"
fName13 = "AA11.csv"
fName14 = "AA12.csv"
fName16 = "AA14.csv"
fName17 = "AA15.csv"
fName18 = "AA17.csv"
fName19 = "DA16.csv"
fName20 = "DA18.csv"
fName21 = "DA19.csv"
fName22 = "DA20.csv"
fName23 = "DA21.csv"
fName24 = "GU22.csv"
fName25 = "LG01.csv"
fName26 = "LG03.csv"
fName27 = "NS02.csv"
fName28 = "TH01.csv"
fName29 = "TH02.csv"
fName30 = "ZW04.csv"
fName31 = "ZW06.csv"
fName32 = "ZW08.csv"
fName33 = "ZW10.csv"
fName34 = "ZW11.csv"
fName35 = "ZW12.csv"
fName36 = "ZW14.csv"
fName37 = "ZW39.csv"


building_list = (fName, fName2, fName3, fName4, fName5,fName6,fName7,fName8,fName9,
                 fName10,fName11,fName12,fName13,fName14,fName16,fName17,fName18,fName19,
                 fName20,fName21,fName22,fName23,fName24,fName25,fName26,fName27,fName28,fName29,
                 fName30,fName31,fName32,fName33,fName34,fName35,fName36,fName37)


import csv
import os
import scipy
import matplotlib.pyplot as plt

# tell, where the files are:

os.chdir("/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Python_Testcases")



# Global variables

hex_type  = "MT" # heat exchanger type
U = 840
CP_WATER = 4185.5 # J/KgK
T_ground = 10 + 273 # ground temperature, currently not used
HOURS_IN_DAY = 24
DAYS_IN_YEAR = 365
cp = CP_WATER




""" importing and preparing raw data for analysis  of every single building """

thermal_building_data = Thermal_BuildingData(fName)

class ThermalBuildingData(object):
    def __init__(self, fName):
        # loading the dataframe
        Q_finalheat_dataframe = extract_csv(fName, "Qh", DAYS_IN_YEAR)
        Q_cool_dataframe = extract_csv(fName, "Qc", DAYS_IN_YEAR)
        Electr_dataframe = extract_csv(fName, "E", DAYS_IN_YEAR)
        T_supply_dataframe = extract_csv(fName, "tshs", DAYS_IN_YEAR)
        T_return_dataframe = extract_csv(fName, "trhs", DAYS_IN_YEAR)
        Q_dhw_dataframe = extract_csv(fName, "Qwwf", DAYS_IN_YEAR)
        # T_amb_dataframe = TO BE INCLUDED
                
        # Convert from dataframe to array:
        self.Q_finalheat_array = toarray(Q_finalheat_dataframe) * 1000 # Convert from kW to W
        self.Q_cool_array = toarray(Q_cool_dataframe) * 1000 # Convert from kW to W
        self.Q_dhw_array = toarray(Q_dhw_dataframe) * 1000 # Convert from kW to W
        self.Q_heating_array = Q_finalheat_array - Q_dhw_array # Extract heating part only
        
        self.Electr_array = toarray(Electr_dataframe) * 1000 # Convert from kW to W
        self.T_supply_array = toarray(T_supply_dataframe) + 273 # Convert from Â°C to K
        T_return_array = toarray(T_return_dataframe) + 273 # Convert from Â°C to K
        
        # T_amb_array = TO BE INCLUDED - while not - set 20°C as ambient temperature
        T_amb_array = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
        T_amb_array[:,:] = 20 + 273
             
        # search for maximum values (needed for design) 
        
        Q_finalheat_max = np.maximum(Q_finalheat_array)
        Q_cool_max = np.maximum(Q_cool_array)  
        Q_heating_max = np.maximum(Q_heating_array)
        Q_dhw_max = np.maximum(Q_dhw_array)
        T_amb_max = np.maximum(T_amb_array)
        T_supply_max_global = T_supply_array[(find_index_of_max(Q_finalheat_array))] 
        T_return_min_global = T_return_array[(find_index_of_max(Q_finalheat_array))] 
                
        # set design conditions for heat loads 
        Q_heating_design = Q_heating_max
        Q_dhw_design = Q_dhw_max
        Q_finalheat_design = Q_finalheat_max
                
        
        #find maximum temperatures needed for all buildings in the network ...
        
            # ... gives maximum supply temperature to building = T_s2 after PÃ¡lsson et al
        T_supply_max_all_buildings = find_max_temp_of_buildings(building_list, "tshs")
        
            # ... gives maximum return temperature to building = T_r2 after PÃ¡lsson et al
        T_return_min_all_buildings = find_max_temp_of_buildings(building_list, "trhs")
        
        
        
        #define empty arrays for ...
        
            # ... Distric heating results
        T_supply_DH_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
        T_return_DH_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
        mdot_DH_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
        
            # ... Bulding internal loop results
        mdot_bld_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
        T_r2_bld_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
        
            # ... heating and dhw massflow
        mdot_dhw_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
        mdot_heating_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))



# # #  Define object, containing all the heat exchanger design data # # # 
exchanger_design_data = ExchangerDesignData(fName)

class ExchangerDesignData(object):
    def __init__(self, fName):
        
        hex_design_results = design_inhouse_exchangers(Q_heating_design, Q_dhw_design, Q_finalheat_max, T_amb_max, T_return_min_global, T_supply_max_global, hex_type)

        A_hex_heating_design = hex_design_results[0]
        mdot_heating_design = hex_design_results[1]
        A_hex_dhw_design = hex_design_results[2]
        mdot_dhw_design = hex_design_results[3]
        A_hex_interface_design =hex_design_results[4]
        mdot_interface_design = hex_design_results[5]
                
                
"""   
# call by:
building_data.mdot_dwh_result
building_data.T_supply_max_all_buildings

"""


""" designing the in-house heat exchangers """

# call the design of the heat exchangers:

hex_design_results = design_inhouse_exchangers(Q_heating_design, Q_dhw_design, Q_finalheat_max, T_amb_max, T_return_min_global, T_supply_max_global, hex_type)

A_hex_heating_design = hex_design_results[0]
mdot_heating_design = hex_design_results[1]
A_hex_dhw_design = hex_design_results[2]
mdot_dhw_design = hex_design_results[3]
A_hex_interface_design =hex_design_results[4]
mdot_interface_design = hex_design_results[5]




"""evaluation loop"""

def translate_Jplus_to_DH_requirements(thermal_building_data, exchanger_data)
    """
    
    
    Returns
    -------
    FORMAT of ".._result" :  = [day,hour]
    
    mdot_DH_result : array
        massflow of District Heating network for every day and hour of the year 
    
    T_return_DH_result : array
        Return Temperature of District Heating network for every day and hour of the year 
    
    T_supply_DH_result : array
        Supply Temperature of District Heating network for every day and hour of the year 
    
    mdot_bld_result : array
        massflow of building internal loop for every day and hour of the year
    
    T_r2_bld_result : array
        temperature of building internal loop for every day and hour of the year
    
    mdot_heating_result : array
        massflow of supply to heating loop for every day and hour of the year
    
    mdot_dhw_result : array
         massflow of supply to hot wate loop for every day and hour of the year
    
    """
    print "translation started"   
    
    for k in range(DAYS_IN_YEAR):
        for j in range(HOURS_IN_DAY):
            Q_dhw = Q_dhw_array[k,j]
            Q_heating = Q_heating_array[k,j]
            Q_finalheat = Q_finalheat_array[k,j]
            T_r2_heating = T_return_array[k,j]
            T_s2_heating = T_supply_array[k,j]
            T_r1_dhw, mdot_dhw = dhw_hex_operation(Q_dhw, hex_type, A_hex_dhw_design)
            T_r1_heating, mdot_heating = heating_hex_operation(Q_heating, T_r2_heating, T_s2_heating, hex_type, A_hex_heating_design, mdot_heating_design, T_amb)
            
            mdot_dhw_result[k,j] = mdot_dhw
            mdot_heating_result[k,j] = mdot_heating
            
            mdot_bld, T_r2_bld = mixing_process(mdot_dhw, T_r1_dhw, mdot_heating, T_r1_heating)
            mdot_bld_result[k,j] = mdot_bld
            T_r2_bld_result[k,j] = T_r2_bld
            
            T_r1_DH, T_s1_DH, mdot_DH = interface_hex_operation(Q_finalheat,T_r2_bld, T_supply_max_all_buildings[k,j], hex_type, mdot_DH_design*0.1, A_hex_interface_design)
            mdot_DH_result[k,j] = mdot_DH
            T_return_DH_result[k,j] = T_r1_DH
            T_supply_DH_result[k,j] = T_s1_DH
            
    print "translation completet - no errors occured!"   
    
    return mdot_DH_result, T_return_DH_result, T_supply_DH_result, mdot_bld_result, T_r2_bld_result, mdot_heating_result,  mdot_dhw_result

""" visualize the results """

subplot(3,2,1)
plot(load_curve(mdot_DH_result))
subplot(3,2,2)
plot(T_supply_DH_result- 273)

subplot(3,2,3) 
plot(T_return_DH_result-273)
#plot(load_curve(T_return_DH_result)-273)

subplot(3,2,4) 
plot(mdot_dhw_result)

subplot(3,2,5)
plot(mdot_heating_result)

subplot(3,2,6)
plot(T_r2_bld_result-273)



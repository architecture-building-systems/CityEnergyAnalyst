# -*- coding: utf-8 -*-
""" Functions used for substation model """
# SEE DOCUMENTATION FOR MORE DETAIL



import csv
import os
import scipy
from scipy import optimize
from scipy import log
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd



def extract_csv(fName, colName, DAYS_IN_YEAR):
    """
    Extract data from one column of a csv file to a pandas.DataFrame
    
    Parameters
    ----------
    fName : string
        Name of the csv file.
    colName : string
        Name of the column from whom to extract data.
    DAYS_IN_YEAR : int
        Number of days to consider.
        
    Returns
    -------
    result : pandas.DataFrame
        Contains the hour of the day in the first column and the data 
        of the selected column in the second.   
    
    """
    result = pd.read_csv(fName, usecols=["DATE", colName], nrows=24*DAYS_IN_YEAR)
    return result

        
def toarray(df):
    """
    Takes a DataFrame and transposes it to an array useable for the 
    Python built-in kmeans function. Each row of the array represents 
    a day and each column a feature.
    
    Parameters
    ----------
    df : DataFrame
        From km_extract.
    
    Returns
    -------
    result : ndarray
    
    """
    df_to_array = np.array(df)
    result = np.zeros((len(df_to_array)//24,24))

    i=0
    j=0
    for k in range(len(df_to_array)):
        result[i,j] = df_to_array[k,1]
        j+=1
        if j==24:
            j=0
            i+=1
    return result




def find_index_of_max(array):
    """ 
    
    Attention! can be applied for values above zero only, otherwise zero will be returned (i.e. (0,0))    
    
    Parameters
    ----------
    array : ndarray
        Array of observations. Each row represents a day and each column the hourly data of that day
       

    Returns
    -------
    max_index_day : integer
        max_index_day  : tells on what day it is 
            
    max_index_hour : integer
        max_index_hour : tells on what hour it happens
    
    to use: e.g. data_array[max_index_hour,max_index_day] will give the maximum data of the year
    
    """
    
    max_value = 0
    max_index_hour = 0
    max_index_day = 0
    for j in range(24):
        for k in range(len(array)):
            if array[k,j] > max_value:
                max_value = array[k,j]
                max_index_day = j
                max_index_hour = k
                
            
    return  max_index_hour, max_index_day




def find_max_temp_of_buildings(building_list, feature, nCol, nRow):
    """

    Finds the maximum return temperature of list of buildings (building_list). 
    --> Example: ("AA16.csv", "tshs")

    Parameters
    ----------
    building_list : tuple of strings
        contains the file names of the buildings, which should be compared
        condition: has to be in CSV format, filled with 8760 entries. Otherwise adjust code
        
    feature : string
        gives the type of that, which should be extracted from the file ( = look for this header)
        
    nCol : integer
        number of coloms in the list of "feature" (typically 365)
        
    nRow : integer
        number of rows in the list of "feature" (typically 24)

        
    Returns
    -------
    T_supply_max_all_buildings : array (365,24)
        gives maximum temperature of all buildings return temperatures in a resolution of 1h for the whole year
    
    """
    DAYS_IN_YEAR = nCol
    HOURS_IN_DAY = nRow

    
    T_supply_array_all_buildings = np.zeros((len(building_list),DAYS_IN_YEAR,HOURS_IN_DAY))
    T_supply_max_all_buildings = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))

    for i in range(len(building_list)):
        T_supply_dataframe = extract_csv(building_list[i], feature, DAYS_IN_YEAR)
        T_supply_array = toarray(T_supply_dataframe) + 273
        # using the array in the type of: [buidling number, day, hour]
        T_supply_array_all_buildings[i,:,:] = T_supply_array
    

        #find max Temp of all Buildings at every timestep

    for k in range(DAYS_IN_YEAR):
        for j in range(HOURS_IN_DAY):
    # using the array in the type of: [buidling number, day, hour]
            T_supply_max_all_buildings[k,j] = max(T_supply_array_all_buildings[:,k,j])
    
    return T_supply_max_all_buildings




def cooling_hex_design(Q_cool_max, T_cool_return_min_global, T_cool_supply_max_global, mdot_internal_cool_design, U , cp) :
        
    """
    
    Designs the domestic heating-loop supply heat 
    exchanger on behalf of the Nominal Load (Q_heating_max) 
    and Ambient Temperature (T_return_min_global) 
    
    In addition, an exchanger-type (hex_type) can be defined (either "HT" or "LT")
        
                
    Parameters
    ----------
    Q_heating_max : float
        Maximum heat demand for space heating [W]
        
    T_return_min_global : float
        lowest return temperature possible
        
    T_supply_max_global : float
        highest return temperature possible
        
    mdot_internal_heating_design : float
        mass flow in heating circuit in kg/s (values from J+) 
        
    hex_type : string
        define heat-exchanger type ("LT" or "MT")
        
    U : float
        U - Value of Heat Exchanger
        
    cp : float
        heat capacity of water 
        
        
    Returns
    -------
    A_hex_heating_design : float
        design Area in [m^2]
        
    mdot_heating_design : float
        massflow at design conditions [kg/s]
        
    k_heating_design : float
        k-value from design conditions (after Palsson et al. 1999)

    
    Assumptions:
     
     
    Name convention as Palsson et al. 1999)
    Temperatures after Guidelines for LTDH-final_rev1.pdf and
    Annex 51 
     
     

     
     
     T_s2 :  Warm Water Target Temp
      - for "HT" design
         T_s2 = 60 °C 
      - for "LT" design
         T_s2 = 50 °C

    T_s1 : DH network supply temperature
        - for "LT" : 70°C
        - for "MT" : 55°C
        
    T_r1 : DH network return temperature
        - for "LT" : 25°C
        - for "MT" : 40°C
     
    """ 


    T_s1 = 3.3 + 273.0 # from IEA, AHU values
    T_r1 = 11 + 273.0 # from IEA, AHU values

    T_r2 = 12 + 273.0 # return from cooling loop (J+)
    T_s2 = 6 + 273.0 # Supply to cooling loop (by J+) 
    
    
    Q_design = Q_cool_max
    
    mdot_cool_design = Q_design / (cp * ( T_s1 - T_r1 ))
    
    k_cool_des = U * ( mdot_internal_cool_design ** (-0.8) + mdot_cool_design ** (-0.8)) 
    
    T_log_mean = ( ( (T_s1 - T_s2) - (T_r1 - T_r2) ) / ( scipy.log(T_s1 - T_s2) - scipy.log(T_r1 - T_r2) ))

    A_hex_cool_design = Q_design / ( U * T_log_mean)
        
        
    return A_hex_cool_design, mdot_cool_design, k_cool_des
    

def cool_hex_operation(Q_cool, T_cool_internal_supply, T_cool_internal_return, T_cool_DH_supply, T_cool_DH_return, A_hex_cool_design, mdot_cool_design, mdot_internal_cool, U, cp, k_cool_design, mdot_step_cool):
    """
    gives return temperature and massflow of building to the interface - heat-exchanger
    
    
    Parameters
    ----------    
    
    Q_heating : float
        Load required for domestic hot water production (defined by J+)
    
    T_r2_heating : float
        return temperature from heating circuit (defined by J+)
    
    T_s2_heating : float
        supply temperature required for heating circuit (defined by J+)
 
    hex_type : string
        heat exchanger type, either "LT" or "MT" (standard = "MT")
        
    A_hex_heating_design : float
        Design Area, can be calculated by heating_hex_design( ) - function
        
    mdot_heating_design : float
        nominal massflow of heating circuit, can be calculated by heating_hex_design( ) - function
        
    mdot_internal_heating : float
        mass flow if internal heating circuit
    
    U : float
        U-Value of heat exchanger ( = 840 W/m^2*K)
    
    cp : float 
        heat capacity of water / fluid
        
    k_heating_design : float
        k-value from design conditions (after Palsson et al. 1999)
    
    mdot_DH_to_heating : float
        mass flow from District heating to space heating heat exchanger 
        (used in step-wise operation scheme)
               
    Returns
    -------
    T_r1 : float
        return temperature of heating-circuit heat exchanger
    
    mdot_heating : float
        massflow for operation of heating-circuit heat exchanger
        
    T_s1_DH : float
        required supply temperature from DH network
    
    A_hex_heating_design : float
        Area, which is required for the operation at these conditions
        (needed further on for checking if the physical properties are satisfied)
    
    Assumptions:
        - no losses
        - lower the massflow as much as possible according to the DH mass flow operation scheme
     
    """ 
    # values from J+ :
    T_s2 = T_cool_internal_supply
    T_r2 = T_cool_internal_return
    
    T_s1 = T_cool_DH_supply
    T_r1_min = T_cool_DH_return

    mdot_cool = mdot_step_cool * mdot_cool_design
    
    T_r1 = T_s1 - Q_cool /(mdot_cool * cp)
    
    if T_r1 < T_r1_min:
        T_r1 = T_r1_min
        mdot_cool = Q_cool /( cp * (T_s1 - T_r1)) 
         

    if mdot_cool >= mdot_cool_design* 1.01:
        print "ERROR AT cooling MASSFlOW (OPERATION)"
    
    q= 0.8 
    
    U_iteration_new = k_cool_design / ( mdot_cool**(-q) + mdot_internal_cool ** (-q))
    
    ## U can go to zero, leading to a nan in A_iteration. This is no issue as massflow is zero!    
    LMTD = ((T_s1 - T_s2) - (T_r1 - T_r2) ) / ( scipy.log((T_s1 - T_s2)/(T_r1 - T_r2)))
    
        
    A_iteration = Q_cool / (U_iteration_new * LMTD) 
    
    if mdot_internal_cool == 0:
        A_iteration = 0
            
    if A_iteration > A_hex_cool_design: 
        A_hex_cool_design = A_iteration 
        print "area CHANGED at cooling!"
  
    if mdot_cool > mdot_cool_design*1.01:
        print "ERROR at massflow (cooling operation)"
        print "delta-Temperatures:", T_s1 - T_r1

        
    return T_r1, mdot_cool, A_hex_cool_design




def import_thermal_data(fName, DAYS_IN_YEAR, HOURS_IN_DAY):
    ''' 
    
    importing and preparing raw data for analysis of every single building 
    
        
    Parameters
    ----------
    fName : string
        name of the building (has to be the same as the csv file, e.g. "AA16.csv" 
        
    DAYS_IN_YEAR : integer
        numer of days in a year (usually 365)
    
    HOURS_IN_DAY : interger
        number of hours in day (usually 24)
    
    
    Returns
    -------
    all thermal data for the building required for design and operation of the thermal system
   
    Q_finalheat_array : array
        thermal load of the entire building as an array, hourly data for one year
        
    Q_heating_array : array
        thermal load of space heating as an array, hourly data for one year
    
    Q_dhw_array : array
        thermal load of domestic hot water (dhw) production as an array, hourly data for one year
    
    Q_cool_array : array
        thermal load of space cooling as an array, hourly data for one year
        
    Electr_array : array
        electrical load of the entire building as an array, hourly data for one year
    
    T_supply_array : array
        Supply temperature to heating building circuit as an array, hourly data for one year
    
    T_return_array : array
        return temperature of heating building circuit as an array, hourly data for one year
    
    T_amb_array : array
        ambient temperature as an array, hourly data for one year (currently: constant!)
    
    T_return_min_global : float
        lowest return temperature of heating building circuit (=return Temp @ design load)
    
    T_supply_max_global : float
        highest supply temperature to heating building circuit (=supply Temp @ design load)
        
    T_amb_max : float
        highest ambient temperature
        
    Q_cool_max : float
        maximum cooling load
    
    Q_heating_design : float
        maximum space heating load
        
    Q_dhw_design : float
        maximum load for domestic hot water production
        
    Q_finalheat_design : float
        maximum load of entire building (incl. space heating and dhw-production) 
    
    mdot_internal_dhw_array : array
        mass flow building hot water circuit as an array, hourly data for one year

    mdot_internal_dhw_design : float
        nominal massflow of building hot water circuit (NOT to DH circuit!)
    
    mdot_internal_heating_array : array
        mass flow building heating circuit as an array, hourly data for one year
    
    mdot_internal_heating_design : float
        nominal massflow of heating circuit (NOT to DH circuit!)

    '''
    
    # loading the dataframe
    Q_finalheat_dataframe = extract_csv(fName, "Qh", DAYS_IN_YEAR)
    Q_cool_dataframe = extract_csv(fName, "Qc", DAYS_IN_YEAR)
    Electr_dataframe = extract_csv(fName, "E", DAYS_IN_YEAR)
    T_supply_dataframe = extract_csv(fName, "tshs", DAYS_IN_YEAR)
    T_return_dataframe = extract_csv(fName, "trhs", DAYS_IN_YEAR)
    Q_dhw_dataframe = extract_csv(fName, "Qwwf", DAYS_IN_YEAR)
    mdotcp_internal_dhw_dataframe = extract_csv(fName, "Qwwf", DAYS_IN_YEAR)
    mdotcp_internal_heating_dataframe = extract_csv(fName, "Qwwf", DAYS_IN_YEAR)
    # T_amb_dataframe = TO BE INCLUDED
    
    
    # Convert from dataframe to array:
    Q_finalheat_array = toarray(Q_finalheat_dataframe) * 1000 # Convert from kW to W
    Q_cool_array = toarray(Q_cool_dataframe) * 1000 # Convert from kW to W
    Q_dhw_array = toarray(Q_dhw_dataframe) * 1000 # Convert from kW to W
    Q_heating_array = Q_finalheat_array - Q_dhw_array # Extract heating part only
    mdot_internal_dhw_array = toarray(mdotcp_internal_dhw_dataframe) * 1 / 4.185 # from kW/degC to kg/s 
    mdot_internal_heating_array = toarray(mdotcp_internal_heating_dataframe) * 1 / 4.185 # from kW/degC to kg/s 
    
    Electr_array = toarray(Electr_dataframe) * 1000 # Convert from kW to W
    T_supply_array = toarray(T_supply_dataframe) + 273 # Convert from Â°C to K
    T_return_array = toarray(T_return_dataframe) + 273 # Convert from Â°C to K
    
    # T_amb_array = TO BE INCLUDED - while not - set 20°C as ambient temperature
    T_amb_array = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
    T_amb_array[:,:] = 20 + 273
    
    
    # search for maximum values (needed for design) 
    Q_finalheat_max = np.amax(Q_finalheat_array)
    Q_cool_max = np.amax(Q_cool_array)  
    Q_heating_max = np.amax(Q_heating_array)
    Q_dhw_max = np.amax(Q_dhw_array)
    T_amb_max = np.amax(T_amb_array)
    T_supply_max_global = T_supply_array[(find_index_of_max(Q_finalheat_array))] 
    T_return_min_global = T_return_array[(find_index_of_max(Q_finalheat_array))] 
    mdot_internal_dhw_design = mdot_internal_dhw_array[(find_index_of_max(Q_finalheat_array))] 
    mdot_internal_heating_design = mdot_internal_heating_array[(find_index_of_max(Q_finalheat_array))] 
    
    # set design conditions for heat loads 
    Q_heating_design = Q_heating_max
    Q_dhw_design = Q_dhw_max
    Q_finalheat_design = Q_finalheat_max

    
    
    return Q_finalheat_array, Q_heating_array, Q_dhw_array, Q_cool_array, Electr_array, T_supply_array, T_return_array, T_amb_array, T_return_min_global, T_supply_max_global, T_amb_max, Q_cool_max, Q_heating_design, Q_dhw_design, Q_finalheat_design, mdot_internal_dhw_array, mdot_internal_dhw_design, mdot_internal_heating_array, mdot_internal_heating_design
    
    
        
def translate_J_plus_to_DH_requirements(DAYS_IN_YEAR, HOURS_IN_DAY, thermal_data, hex_design_data, hex_type, temperature_data, U, cp, mdot_step_counter):
        
    """
    
    Translating building loads into a massflows and temperatures of District Heating (DH) network. 
    This function also provides building internal flows. 
    
    
        
    Parameters
    ----------
        
    DAYS_IN_YEAR : integer
        numer of days in a year (usually 365)
    
    HOURS_IN_DAY : interger
        number of hours in day (usually 24)
        
    thermal_data : tuple
        results from import_thermal_data( ) funciton, contains loads and temperatures of a building
        on 24h basis for 1 year (one value per hour, from J+)
    
    hex_design_data : tuple
        results from heat-exchanger design function: design_inhouse_exchangers( ) function,
        contains nominal Area and massflow of each heat exchanger
    
    hex_type : string
        define the heat exchanger type, either "LT" or "MT" for low- / medium temperature design
        
    temperature_data : tuple
        summary of temperatures:
            - T_amb_array : ambient temperature array
            - T_supply_max_all_buildings : Maximum supply temperature over all buildings
            - T_return_min_all_buildings : minimum return temperature over all buildings
                (see: find_max_temp_of_buildings( ) funciton) 
        
    U : float
        U-Value of heat-exchanger (use  U = 840 W/m^2K, similar to EPFL Th. 5287)
    
    cp : float 
        heat capacity of water / fluid
        
    mdot_step_counter : array
        Array containing the step-wise operation profile of the DH-massflow
        provide in absolute numbers (e.g. 20% --> 0.2)
    
    Returns
    -------
        FORMAT of ".._result" : Array = [day,hour]
    
    mdot_DH_result : array
        massflow of District Heating network for every day and hour of the year 
    
    T_return_DH_result : array
        Return Temperature of District Heating network for every day and hour of the year 
    
    T_supply_DH_result : array
        Supply Temperature of District Heating network for every day and hour of the year 
    
    mdot_heating_result : array
        massflow of space heating branch (DH side) for every day and hour of the year
    
    mdot_dhw_result : array
        massflow of Dom. Hot Water branch (DH side) for every day and hour of the year

    T_r1_dhw_result : array
        temperature of Dom.Hot Water branch (DH side) or every day and hour of the year
    
    T_r1_heating_result : array
        temperature of space heating branch (DH side) or every day and hour of the year

    A_hex_heating_design : float
        final area of heat exchanger for space heating (after checking the physical feasibility)
    
    A_hex_dhw_design : float
        final area of heat exchanger for domestic hot water (after checking the physical feasibility)
    
    """
   
    
    print "translation started"   


    #Unpack data from thermal_data
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
        
        
    # unpack data from heat exchanger design
    A_hex_heating_design = hex_design_data[0]
    mdot_heating_design = hex_design_data[1]
    k_heating_design = hex_design_data[2]
    A_hex_dhw_design = hex_design_data[3]
    mdot_dhw_design = hex_design_data[4]
    k_dhw_design = hex_design_data[5]
    
    
    mdot_DH_design = mdot_dhw_design + mdot_heating_design
    
    
    
    # unpack temperature data
    T_amb_array = temperature_data[0]
    T_supply_max_all_buildings = temperature_data[1]
    T_return_min_all_buildings = temperature_data[2]
        
        
    ''' define empty arrays for ...  results'''
        # ... Distric heating results
    T_supply_DH_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
    T_return_DH_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
    mdot_DH_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
    
    
        # ... heating and dhw massflow results
    mdot_dhw_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
    mdot_heating_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
    T_r1_dhw_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
    T_r1_heating_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
    
    
    
    #iter_counter_heating = 0
    iter_counter_dhw = 0
    
    loopcheck_dhw = 0
    loopcheck_heating = 0
    
    while loopcheck_dhw < 1 and loopcheck_heating < 1:
        for k in range(DAYS_IN_YEAR):
            for j in range(HOURS_IN_DAY):
                for mdot_stepper in range(len(mdot_step_counter)): # loop for massflow iteration
                    mdot_step = mdot_DH_design  * mdot_step_counter[mdot_stepper]
                   
                    # assign data into loop
                    Q_dhw = Q_dhw_array[k,j]
                    Q_heating = Q_heating_array[k,j]
                    T_r2_heating = T_return_array[k,j]
                    T_s2_heating = T_supply_array[k,j]
                    T_amb = T_amb_array[k,j]
                    mdot_internal_dhw = mdot_internal_dhw_array[k,j] 
                    mdot_internal_heating = mdot_internal_heating_array[k,j] 
         
                    T_r1_dhw, mdot_dhw, A_hex_dhw_check = dhw_hex_operation(Q_dhw, hex_type, A_hex_dhw_design, mdot_dhw_design, mdot_internal_dhw, U, cp, k_dhw_design, mdot_step)
                    
                    
                    
                    if A_hex_dhw_check > A_hex_dhw_design: # check if the area is sufficient, if not - restart the loop
                        A_hex_dhw_design = A_hex_dhw_check
                        print A_hex_dhw_check," CHANGED! ! ! "
                        print " -----------------------------"
                        loopcheck_dhw = 0
                        print k
                        k = 0
                        k_dhw_design = U * (mdot_dhw**(-0.8) + mdot_internal_dhw**(-0.8))
                        break
            
                        
                    if mdot_dhw >= mdot_step: # if hot water supply of DH is not sufficient, go back to the for loop and increase the massflow
                        continue
                    
                    mdot_DH_to_heating = mdot_step - mdot_dhw
                    
                    T_r1_heating, mdot_heating_req, T_s1_DH, A_hex_heating_check = heating_hex_operation(Q_heating, T_r2_heating, T_s2_heating, hex_type, A_hex_heating_design, mdot_heating_design, mdot_internal_heating, U, cp, k_heating_design, mdot_DH_to_heating)
                    mdot_dhw_result[k,j] = mdot_dhw
                    mdot_heating_result[k,j] = mdot_heating_req
                    
                    
                    
                    if A_hex_heating_check > A_hex_heating_design: # check if the area is sufficient, if not - restart the loop
                        A_hex_heating_design = A_hex_heating_check
                        print A_hex_heating_check,"."
                        print " -----------------------------"
                        loopcheck_heating = 0
                        print "day in year which requires redesigning the area of heating-hex : ", k
                        k = 0
                        k_heating_design = U * (mdot_heating_req**(-0.8) + mdot_internal_heating*(-0.8))
                                
                    
                    
                    
                    
                    
                    mdot_DH, T_r1_DH = mixing_process(mdot_dhw, T_r1_dhw, mdot_heating_req, T_r1_heating)
        
                    mdot_DH_result[k,j] = mdot_DH
                    T_return_DH_result[k,j] = T_r1_DH
                    T_supply_DH_result[k,j] = T_s1_DH
                    T_r1_dhw_result[k,j] = T_r1_dhw
                    T_r1_heating_result[k,j] = T_r1_heating
                    
                    
                    
                    if mdot_DH_to_heating < mdot_heating_req: # heating requires more massflow than it is provided, increase DH massflow
                        continue
                        
                    else:
                        break    
                
            loopcheck_dhw = 1
            loopcheck_heating = 1
           
    return mdot_DH_result, T_return_DH_result, T_supply_DH_result, mdot_heating_result,  mdot_dhw_result, T_r1_dhw_result, T_r1_heating_result, A_hex_heating_design, A_hex_dhw_design


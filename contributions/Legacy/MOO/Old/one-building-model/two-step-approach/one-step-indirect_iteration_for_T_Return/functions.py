# -*- coding: utf-8 -*-

import csv
import os
import scipy
from scipy import optimize
from scipy import log
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

os.chdir("/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Python_Testcases")


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




def find_max_temp_of_buildings(building_list, feature):
    """

    Finds the maximum return temperature of list of buildings (building_list). 
    

        Parameters
    ----------
    building_list : tuple of strings
        contains the file names of the buildings, which should be compared
        condition: has to be in CSV format, filled with 8760 entries. Otherwise adjust code
        
        Example: ("AA16.csv", "tshs")
        
    feature : string
        gives the type of that, which should be extracted from the file ( = look for this header)
        
        
    Returns
    
    -------
    T_supply_max_all_buildings : array (365,24)
        gives maximum temperature of all buildings return temperatures in a resolution of 1h for the whole year
    
    """
    
    HOURS_IN_DAY = 24
    DAYS_IN_YEAR = 365
    
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




def heating_hex_design(Q_heating_design, T_return_min_global, T_supply_max_global, mdot_internal_heating_design, hex_type, U , cp) :
    
        
    """
    
    Designs the domestic heating-loop supply heat 
    exchanger on behalf of the Nominal Load (Q_heating_max) 
    and Ambient Temperature (T_return_min_global) 
    
    In addition, an exchanger-type (hex_type) can be defined (either "HT" or "LT")
    
    
    Parameters
    ----------
    Q_heating_max : float
        Maximum heat dem for space heating [W]
        
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
     
     
    HT-Design as standard (if not specified as LT)
     --> Name convention as Palsson et al. 1999)
     
     
     Assuming that the Ambient temperature is not restricting the return temperature 1 (T_r1)
     as the maximum load occurs during cold days 
     --> T_r1 = max ( T_r2 + deltaT, T_dhw_target + deltaT)
     
     
     T_s2 :  Warm Water Target Temp
      - for "HT" design
         T_s2 = 60 °C 
      - for "LT" design
         T_s2 = 50 °C
         
     T_s1 = T_s2 + 5 °C
    
                
     
    """ 

    if hex_type == "LT":
        T_s1 = 55 + 273
        T_r1 = 25 + 273
    
    else:
        T_s1 = 70 + 273
        T_r1 = 40 + 273

    T_r2 = T_return_min_global
    T_s2 = T_supply_max_global
    
    
    Q_design = Q_heating_design
    
    mdot_DH_i_des = Q_design / (cp * ( T_s1 - T_r1 ))
    
    k_heating_des = U * ( mdot_internal_heating_design ** (-0.8) + mdot_DH_i_des ** (-0.8)) 
    
    T_log_mean = ( ( (T_s1 - T_s2) - (T_r1 - T_r2) ) / ( scipy.log(T_s1 - T_s2) - scipy.log(T_r1 - T_r2) ))

    A_hex_heating_design = Q_design / ( U * T_log_mean)
    
    mdot_heating_design = mdot_DH_i_des
    


    return A_hex_heating_design, mdot_heating_design, k_heating_des
    
    
    
    
    
def dhw_hex_design(Q_dhw_max, mdot_internal_dhw_design, T_amb_max, hex_type, U, cp) :
    
    """
    
    Designs the Domestic Hot Water heat exchanger on behalf of the Nominal Load (Q_design) and Ambient Temperature (T_amb_max)
    In addition, an exchanger-type (hex_type) can be defined (either "HT" or "LT")
    
    
    Parameters
    ----------
    Q_dhw_max : float
        Maximum heat dem for domestic hot water [W]
        
    T_amb_max : float
        maximum ambient temperature in [K]
        
    U : float
        U-Value of the heat-exchangers (use: 840W/m^2*K)
        
        
    Returns
    -------
    A_hex_dhw_design : float
        design Area in [m^2]
        
    mdot_dhw_design : float
        massflow at design conditions [kg/s]

    
    Assumptions:
     U = 840 W/m^2*K
     
     Assuming HT-Design if not specified as LT
     
     (Name convention as Palsson et al. 1999, Temperatures by Annex 51)
     
     T_s2 :  Warm Water Target Temp
     
      - for "HT" design
         T_s2 = 60 °C 
         T_s1 = 70 °C
         T_r1 = 40 °C
         
      - for "LT" design
         T_s2 = 50 °C
         T_s1 = 55 °C
         T_r1 = 25 °C
         
     T_r2 : cold Water input Temp, to be heated 
      - T_r2 = 10 °C (for "LT" and "HT")
                
     
    """ 
    # U = 840 # W/m^2*K --> take new from function call


   
    if hex_type == "LT":
        T_s2 = 50 + 273
        T_s1 = 55 + 273
        T_r1 = 25 + 273
    
    else:
        T_s2 = 60 + 273
        T_s1 = 70 + 273
        T_r1 = 40 + 273

    T_r2 = 10 + 273
    
    
    Q_design = Q_dhw_max
    
    mdot_DH_i_des = Q_design / (cp * ( T_s1 - T_r1 ))
    
    k_dhw_des = U * ( mdot_internal_dhw_design ** (-0.8) + mdot_DH_i_des ** (-0.8)) 
    
    T_log_mean = ( ( (T_s1 - T_s2) - (T_r1 - T_r2) ) / ( scipy.log(T_s1 - T_s2) - scipy.log(T_r1 - T_r2) ))

    A_hex_dhw_design = Q_dhw_max / ( U * T_log_mean)
    
    mdot_dhw_design = mdot_DH_i_des
    


    return A_hex_dhw_design, mdot_dhw_design, k_dhw_des



def mixing_process(mdot_dhw, T_r1_dhw, mdot_heating, T_r1_heating):
    
    """
    gives return temperature and massflow of building to the interface - heat-exchanger
    
    
    Parameters
    ----------
    mdot_dhw : float
        required massflow for domestic hot water production
    
    T_r1_dhw : float
        temperature of massflow coming from domestic hot water production
        
    mdot_heating : float
        required massflow for space heating
    
    T_r1_heating : float
        temperature of massflow coming from domestic heating heat-exchanger
        
            
    Returns
    -------
    mdot_bld : float
        massflow of building circuit, circulating between DH - heat-exchanger and in-house
        costumers  (Dom. hot water and space heating) 
    
    T_r2_bld : float
        temperature of massflow going to the interface heat-exchanger
    
    
    Assumptions:
        no losses
     
    """ 
   
    
    mdot_DH = mdot_dhw + mdot_heating
    T_r2_DH = ( T_r1_dhw * mdot_dhw + T_r1_heating * mdot_heating) / mdot_DH
    
    if mdot_dhw == 0:
        mdot_DH= mdot_heating
        T_r2_DH = T_r1_heating
        
    
    if mdot_heating == 0:
        mdot_DH = mdot_dhw
        T_r2_DH = T_r1_dhw
        
    
    return mdot_DH, T_r2_DH
    
    
    
def design_inhouse_exchangers(Q_heating_design, Q_dhw_design, T_amb_max, T_return_min_global, T_supply_max_global, mdot_internal_dhw_design, mdot_internal_heating_design, hex_type, U, cp):
    
    """
    This function sums up all the designing process of heat exchangers. It returns the nominal area and massflow of three heat exchangers:
        - dhw : Domestic hot water heat exchanger
        - heating : heating circuit heat exchanger
        - interface : building and district heating interface heat exchanger
        
        
    Parameters
    ----------
    Q_heating_design : float
        nominal load for heating
        
    Q_dhw_design : float
        nominal load for hot water production
        

    T_amb_max : float
        highest ambient temperature, where the hot water production need to work
        
    T_return_min_global : float
        return temperature to heating circuit at nominal load of heating circuit
        
    T_supply_max_global : float
        supply temperature to heating circuit at nominal load of heating circuit
    
    hex_type : string
        give the heat exchanger type (either "LT" or "MT")
        
    U : float
        U-Value of heat exchanger

    cp : float
        heat capacity of water
        
    
    Returns
    -------
    A_hex_heating_design : float
        design area for heating-circuit heat exchanger
    
    mdot_heating_design : float
        design massflow for heating-circuit heat exchanger
        
    A_hex_dhw_design : float
        design area for domestic hot water heat exchanger
    
    mdot_dhw_design : float
        design massflow for domestic hot water heat exchanger
        
    A_hex_interface_design : float
        design area for interface (building / DH-network) heat exchanger
    
    mdot_interface_design : float
        design massflow for in DH network branch to building
    
    
    """
    
    A_hex_heating_design, mdot_heating_design, k_heating_design = heating_hex_design(Q_heating_design, T_return_min_global, T_supply_max_global, mdot_internal_heating_design, hex_type, U , cp)
 #   A_hex_dhw_design, mdot_dhw_design = dhw_hex_design(Q_dhw_design, T_amb_max, hex_type, U, cp) 
    A_hex_dhw_design, mdot_dhw_design, k_dhw_design = dhw_hex_design(Q_dhw_design, mdot_internal_dhw_design, T_amb_max, hex_type, U, cp)
    
    
    
    return A_hex_heating_design, mdot_heating_design, k_heating_design, A_hex_dhw_design, mdot_dhw_design, k_dhw_design

    
def dhw_hex_operation(Q_dhw, hex_type, A_hex_dhw_design, mdot_dhw_design, mdot_internal_dhw, U, cp, k_dhw_design):
    """
    
    gives return temperature and massflow to the building-system 
    of domestic hot water heat-exchanger 
    
    
    Parameters
    ----------
    Q_dhw : float
        Load required forr domestic hot water production
    
    hex_type : string
        heat exchanger type, either "LT" or "MT" (standard = "MT")
        
    A_hex_dhw_design : float
        Design Area, can be calculated by dhw_hex_design-function
        
    T_amb : float
        Ambient temperature at timestep
        
    mdot_dhw_design : float
        nominal massflow of domestic hot water heat exchanger
    
    U : float
        U-Value of heat exchanger ( = 840 W/m^2*K)
    
    cp : float
        heat capacity of water / fluid
        
            
    Returns
    -------
    T_r1_dhw : float
        return temperature of hot water heat exchanger 
    
    mdot_dhw : float
        massflow required for operation of this heat exchanger
    
    Assumptions:
        - no losses
        - lower the massflow as long as possible, no minimum massflow required
        - target temperature of hot water in building (@LT = 50 °C, @MT = 60 °C)
        - Supply Temperatue from DH is set (=70°C @ MT, = 55°C @ LT)
     
    """ 
   
    T_s1 = 70 + 273
    T_s2 = 60 + 273 # Target temp of hot water @ MT design
    
    if hex_type == "LT":
        T_s1 = 55 + 273
        T_s2 = 50 + 273 # Target temp of hot water @ LT design = 50 °C
    
    T_r2 = 10 + 273 
    
    q = 0.8
    Q = Q_dhw
    
    A_iteration = A_hex_dhw_design
    A_iteration_old = 0.5
    A_iteration_old_old = 0.5
    
    iteration_counter = 0
    
    while abs((A_iteration - A_iteration_old_old)/A_iteration) > 0.01:
        iteration_counter += 1
        A_iteration_old_old = A_iteration_old
        A_iteration_old = A_iteration
        
        c1 = k_dhw_design  * A_iteration * (T_s1 - T_s2) / (T_s2 - T_r2)**q 
        c2 = (T_s1 - T_s2) / (T_s2 - T_r2) 

        def fh(x):
            Eq = c1 * (x -1) / ( 1+ (1 - c2 *( x-1))**q * scipy.log(x)) - Q**(1-q)
            return Eq
        
        alpha = scipy.optimize.brentq(fh, -1,100)

        T_r1_calc = T_r2  + alpha * (T_s1 - T_s2)
        T_r1 = np.maximum(T_r1_calc,40 + 273) 
        #print T_r1 - 273, T_r1_calc - 273
        
        mdot_dhw = Q  / ( cp* (T_s1 - T_r1) ) 
        
        if mdot_dhw == mdot_dhw_design:
            print "design point achieved"
            
        if mdot_dhw >= mdot_dhw_design* 1.01:
            print "ERROR AT DHW MASSFlOW (OPERATION)"
        
        U_iteration_new = k_dhw_design / ( mdot_dhw**(-q) + mdot_internal_dhw ** (-q))
    
        LMTD = ((T_s1 - T_s2) - (T_r1 - T_r2) ) / ( scipy.log((T_s1 - T_s2)/(T_r1 - T_r2)))

        A_iteration = Q_dhw / (U_iteration_new * LMTD) 
    
        print "A_iteration = ", A_iteration
        print "A_iteration_old = ", A_iteration_old
        #print ".",
    
    
    print "loop done!"
    
    #print  "U operation = ", U_operation
    #print " U desing = ", U
    #A_hex_check = Q_dhw / ( U_iteration_new * LMTD)
    
    # print A_check, A_dhw_design
    #if A_hex_check > A_hex_dhw_design*1.01:
        #print "ERROR at area of dhw (operation) !"
        #print "required area:", A_hex_check
        #print "actual area:", A_hex_dhw_design
    
    if mdot_dhw > mdot_dhw_design*1.01:
        print "ERROR at massflow (dhw operation)"
        print "delta-Temperatures:", T_s1 - T_r1

        
    return T_r1, mdot_dhw, A_iteration
        


def heating_hex_operation(Q_heating, T_r2_heating, T_s2_heating, hex_type, A_hex_heating_design, mdot_heating_design, T_amb, U, cp):
    
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
    
    T_amb : float
        Ambient temperature at timestep
    
    U : float
        U-Value of heat exchanger ( = 840 W/m^2*K)
               
    Returns
    -------
    T_r1_heating : float
        return temperature of heating-circuit heat exchanger
    
    mdot_heating : float
        massflow required for operation of heating-circuit heat exchanger
        
    T_s1_DH : float
        required supply temperature from DH network
    
    Assumptions:
        - no losses
        - lower the massflow as much as possible, no minimum massflow required
     
    """ 
    # values from J+ :
    T_s2 = T_s2_heating 
    T_r2 = T_r2_heating 
    
    T_s1 = np.maximum(60 + 5 + 273, T_s2_heating + 5) 
    T_r1 = T_r2 + 5 # maintain 5°C Temp gap

    
    if hex_type == "LT":
        T_s1 = np.maximum(45 + 5 + 273, T_s2_heating + 5)
    
    T_s1_DH = T_s1
    
        
    mdot_heating = Q_heating / (cp * (T_s1 - T_r1))
    
    LMTD =((T_s1 - T_s2) - (T_r1 - T_r2) ) / ( scipy.log((T_s1 - T_s2)/(T_r1 - T_r2)))
    
    A_hex_check = Q_heating / ( U * LMTD)
    

    if A_hex_check > A_hex_heating_design * 1.01:
        print "ERROR at area (heating)", A_hex_check, A_hex_heating_design
        
    elif mdot_heating > mdot_heating_design * 1.05:
        print "ERROR at massflow (heating)"
        print cp, " = cp; ", T_s1, "= T_s1 ;", T_r1, " =T_r1"
        print Q_heating, " = Q_heating"
    

        
    return T_r1, mdot_heating, T_s1_DH





fName = "AA16.csv"



hex_type = "MT" # heat exchanger type
U = 840
CP_WATER = 4185.5 # J/KgK
cp = CP_WATER
T_ground = 10 + 273 # ground temperature, currently not used
HOURS_IN_DAY = 24
DAYS_IN_YEAR = 365



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
    
    
        
def translate_J_plus_to_DH_requirements(DAYS_IN_YEAR, HOURS_IN_DAY, thermal_data, hex_design_data, hex_type, temperature_data, U, cp):
        
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
    
    Returns
    -------
        FORMAT of ".._result" : Array = [day,hour]
    
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
    

    """ unpack data """

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
    iter_counter_heating = 0
    iter_counter_dhw = 0
    
    for k in range(DAYS_IN_YEAR):
        for j in range(HOURS_IN_DAY):
            Q_dhw = Q_dhw_array[k,j]
            Q_heating = Q_heating_array[k,j]
            T_r2_heating = T_return_array[k,j]
            T_s2_heating = T_supply_array[k,j]
            T_amb = T_amb_array[k,j]
            mdot_internal_dhw = mdot_internal_dhw_array[k,j] 
            mdot_internal_heating = mdot_internal_heating_array[k,j] 
            T_r1_dhw, mdot_dhw, A_hex_dhw_check = dhw_hex_operation(Q_dhw, hex_type, A_hex_dhw_design, mdot_dhw_design, mdot_internal_dhw, U, cp, k_dhw_design)
            T_r1_heating, mdot_heating, T_s1_DH = heating_hex_operation(Q_heating, T_r2_heating, T_s2_heating, hex_type, A_hex_heating_design, mdot_heating_design, T_amb, U, cp)
            mdot_dhw_result[k,j] = mdot_dhw
            mdot_heating_result[k,j] = mdot_heating
            
            mdot_DH, T_r1_DH = mixing_process(mdot_dhw, T_r1_dhw, mdot_heating, T_r1_heating)

            mdot_DH_result[k,j] = mdot_DH
            T_return_DH_result[k,j] = T_r1_DH
            T_supply_DH_result[k,j] = T_s1_DH
            
            if A_hex_dhw_check > A_hex_dhw_design: # check if the area is sufficient, if not - restart the loop
                A_hex_dhw_design = A_hex_dhw_check
                print A_hex_dhw_check,"."
                k = 0
                k_dhw_design = U * (mdot_dhw**(-0.8) + mdot_internal_dhw**(-0.8))
                iter_counter_dhw += 1
            
            #if A_hex_heating_check > A_hex_heating_design:
            #    A_hex_heating_design = A_hex_heating_check
            #    print k,"."
            #    k = 0
            #    print ".", A_hex_dhw_design
            #    iter_counter_heating += 1                
                                                
        #print iter_counter
            
    print k
    
    print "required Area for dhw of Building", fName, "is :", A_hex_dhw_design
    print "the design area for dhw is :", A_hex_dhw_design
    print "this has taken ",j, " iterations"
    
    max_Area = [A_hex_dhw_design, fName]
    
    print "translation completet - no errors occured!"   
    
    return mdot_DH_result, T_return_DH_result, T_supply_DH_result, mdot_heating_result,  mdot_dhw_result








# import data


building_list_dataframe = pd.read_csv("Total.csv", sep=",", usecols=["Name"])
building_list_array_helper = np.array(building_list_dataframe) 
building_list_array = building_list_array_helper[:]  + ".csv"




building_list = np.array(building_list_array[:,0]).tolist() #transfer building array to list

#thermal_data = import_thermal_data(fName, DAYS_IN_YEAR, HOURS_IN_DAY)
       
#Q_finalheat_array = thermal_data[0]
#Q_heating_array = thermal_data[1]
#Q_dhw_array = thermal_data[2]
#Q_cool_array = thermal_data[3]
#Electr_array = thermal_data[4]
#T_supply_array = thermal_data[5]
#T_return_array = thermal_data[6]
#T_amb_array = thermal_data[7]
#T_return_min_global = thermal_data[8]
#T_supply_max_global = thermal_data[9]
#T_amb_max = thermal_data[10]
#Q_cool_max = thermal_data[11]
#Q_heating_design = thermal_data[12]
#Q_dhw_design = thermal_data[13]




# ... gives maximum supply temperature to building = T_s2 after PÃ¡lsson et al
T_supply_max_all_buildings = find_max_temp_of_buildings(building_list, "tshs")

# ... gives maximum return temperature to building = T_r2 after PÃ¡lsson et alT_return_min_all_buildings = find_max_temp_of_buildings(building_list, "trhs")
T_return_min_all_buildings = find_max_temp_of_buildings(building_list, "trhs")

"""
# summarize temperature inputs
temperature_data = T_amb_array, T_supply_max_all_buildings, T_return_min_all_buildings 

# call the design of the heat exchangers:
hex_design_data = design_inhouse_exchangers(Q_heating_design, Q_dhw_design, T_amb_max, T_return_min_global, T_supply_max_global, hex_type, U, cp)

"""

# performing the loop :

for i in range(len(building_list_array)):
    fName = building_list_array[i,0]
    print "currently working on :", fName
    
    thermal_data = import_thermal_data(fName, DAYS_IN_YEAR, HOURS_IN_DAY)
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

    hex_design_data = design_inhouse_exchangers(Q_heating_design, Q_dhw_design, T_amb_max, T_return_min_global, T_supply_max_global, mdot_internal_dhw_design, mdot_internal_heating_design, hex_type, U, cp)

    print hex_design_data[0], " = A_hex_heating_design", hex_design_data[1], "= mdot_heating_design", hex_design_data[2], " = A_hex_dhw_design", hex_design_data[3], "= mdot_dhw_design"
    result_arrays = translate_J_plus_to_DH_requirements(DAYS_IN_YEAR, HOURS_IN_DAY, thermal_data, hex_design_data, hex_type, temperature_data, U, cp)
    mdot_DH_result = result_arrays[0]
    T_return_DH_result = result_arrays[1]
    T_supply_DH_result = result_arrays[2]
    mdot_heating_reslt = result_arrays[3]
    mdot_dhw_result = result_arrays[4]

    # creating flat arrays from 365x 24h format for further processing: 
    
    mdot_DH_result_flat = mdot_DH_result.ravel(0)
    T_return_DH_result_flat = T_return_DH_result.ravel(0)
    T_supply_DH_result_flat = T_supply_DH_result.ravel(0)
    mdot_heating_result_flat = mdot_heating_reslt.ravel(0)
    mdot_dhw_result_flat =  mdot_dhw_result.ravel(0)
    
    
    results = pd.DataFrame({"mdot_DH_result":mdot_DH_result_flat,"T_return_DH_result":T_return_DH_result_flat,"T_supply_DH_result":T_supply_DH_result_flat, "mdot_heating_result":mdot_heating_result_flat,"mdot_dhw_result":mdot_dhw_result_flat})
    fName_result = building_list_array[i,0] + "_result.csv"
    os.chdir("/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Results")
    results.to_csv(fName_result, sep= ',')
    os.chdir("/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Python_Testcases")
    



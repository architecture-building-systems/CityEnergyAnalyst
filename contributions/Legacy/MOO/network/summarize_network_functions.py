# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

def extract_csv(fName, colName, DAYS_IN_YEAR):
    """
    Extract data from one column of a csv file to a pandas.DataFrame
    
    Parameters
    ----------
    fName : string
        Name of the csv file.
    colName : stringT_
        Name of the column from whom to extract data.
    DAYS_IN_YEAR : int
        Number of days to consider.
        
    Returns
    -------
    result : pandas.DataFrame
        Contains the hour of the day in the first column and the data 
        of the selected column in the second.   
    
    """
    result = pd.read_csv(fName, usecols=[colName], nrows=24*DAYS_IN_YEAR)
    return result

    
def toarray(df):
    """
    Takes a DataFrame and transposes it to an array useable for further processing. Each row of the array represents 
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
    Returns the index of an array on which the maximum value is at.
        
    Parameters
    ----------
    array : ndarray
        Array of observations. Each row represents a day and each column the hourly data of that day
       

    Returns
    -------

    max_index_hour : integer
        max_index_hour : tells on what hour it happens (hour of the year)
    
    to use: e.g. data_array[max_index_hour] will give the maximum data of the year
    
    """
    
    max_value = -abs(np.amax(array))
    
    max_index_hour = 0
    
    for k in range(len(array)):
        if array[k] > max_value:
            max_value = array[k]
            max_index_hour = k
                
            
    return  max_index_hour


def import_substation_data(fName, DAYS_IN_YEAR, HOURS_IN_DAY):
    ''' 
    
    importing and preparing raw data for analysis of every single building 
    returns all thermal data for the building required for design and operation of the thermal system

        
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
    Arrays containing all relevant data for further processing:
            
        mdot_sst_heat, mdot_sst_cool, T_sst_heat_return, T_sst_heat_supply, T_sst_cool_return, 
        Q_DH_building, Q_DC_building, Q_DH_building_max, Q_DC_bulding_max, T_sst_heat_supply_ofmaxQh, 
        T_sst_heat_return_ofmaxQh, T_sst_cool_return_ofmaxQc
    
    
    '''
    
    
    """     import dataframes    """
    # mass flows
    mdot_sst_heat_dataframe = extract_csv(fName, "mdot_DH_result", DAYS_IN_YEAR)
    mdot_sst_cool_dataframe = extract_csv(fName, "mdot_DC_result", DAYS_IN_YEAR)
    
    # temperatures : Supply = what goes to substation, Retrun = what comes from substation to network
    T_sst_heat_return_dataframe = extract_csv(fName, "T_return_DH_result", DAYS_IN_YEAR)
    T_sst_heat_supply_dataframe = extract_csv(fName, "T_supply_DH_result",DAYS_IN_YEAR)
    
    T_sst_cool_return_dataframe_it = extract_csv(fName, "T_return_DC_result", DAYS_IN_YEAR)
    T_sst_cool_return_dataframe = T_sst_cool_return_dataframe_it.fillna(0)
    # T_sst_cool_supply = 4 + 273, set as constant from DC network assumptions
    
    # loads    
    Q_DH_building_heating_dataframe = extract_csv(fName, "Q_heating", DAYS_IN_YEAR)
    Q_DH_building_dhw_dataframe = extract_csv(fName, "Q_dhw", DAYS_IN_YEAR)
    Q_DH_building_cool_dataframe = extract_csv(fName, "Q_cool", DAYS_IN_YEAR)
    Electr_array_dataframe = extract_csv(fName, "Electr_array_all_flat", DAYS_IN_YEAR)
    """      Transfer to arrays    """
    
    mdot_sst_heat = np.array(mdot_sst_heat_dataframe)
    mdot_sst_cool = np.array(mdot_sst_cool_dataframe)
    
    # temperatures : Supply = what goes to substation, Retrun = what comes from substation to network
    T_sst_heat_return = np.array(T_sst_heat_return_dataframe)
    T_sst_heat_supply = np.array(T_sst_heat_supply_dataframe)
    T_sst_cool_return = np.array(T_sst_cool_return_dataframe)

    # T_sst_cool_supply = 4 + 273, set as constant from DC network assumptions
    

    # loads    
    Q_DH_building_heating = np.array(Q_DH_building_heating_dataframe)
    Q_DH_building_dhw = np.array(Q_DH_building_dhw_dataframe)
    Q_DC_building = np.array(Q_DH_building_cool_dataframe)
    Q_DH_building = Q_DH_building_heating + Q_DH_building_dhw
    
    # Electricity
    Electr_array = np.array(Electr_array_dataframe)
    """     determining the extreme values     """
    Q_DC_bulding_max = np.amax(Q_DC_building)
    Q_DH_building_max = np.amax(Q_DH_building)
    
    
    max_index_heat = find_index_of_max(Q_DH_building)
    max_index_cool = find_index_of_max(Q_DC_building)
    T_sst_heat_supply_ofmaxQh = T_sst_heat_supply[max_index_heat] # supply temperature at maximum heat load
    T_sst_heat_return_ofmaxQh = T_sst_heat_return[max_index_heat] # return temperature at maximum heat load
    T_sst_cool_return_ofmaxQc = T_sst_cool_return[max_index_cool] # return temperature at maximum cooling load
    
    
    return mdot_sst_heat, mdot_sst_cool, T_sst_heat_return, T_sst_heat_supply, T_sst_cool_return, \
            Q_DH_building, Q_DC_building, Q_DH_building_max, Q_DC_bulding_max, T_sst_heat_supply_ofmaxQh,\
            T_sst_heat_return_ofmaxQh, T_sst_cool_return_ofmaxQc, Electr_array


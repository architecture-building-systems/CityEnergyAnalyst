""" 

Import Network Data:
  
    This File reads all relevant thermal data for further analysis in the Slave Routine, 
    Namely : Thermal (J+) and Solar Data (J+) 
            
"""
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



def import_network_data(fName, DAYS_IN_YEAR, HOURS_IN_DAY):
    ''' 
    
    importing and preparing raw data for analysis of the district network 

        
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
        
        
    mdot_heat_netw_total = np.array(extract_csv(fName, "mdot_heat_netw_total", DAYS_IN_YEAR))
    mdot_cool_netw_total = np.array(extract_csv(fName, "mdot_cool_netw_total", DAYS_IN_YEAR))
    
    
    Q_DH_building_netw_total = np.array(extract_csv(fName, "Q_DH_building_netw_total", DAYS_IN_YEAR))
    Q_DC_building_netw_total = np.array(extract_csv(fName, "Q_DC_building_netw_total", DAYS_IN_YEAR))
    T_sst_heat_return_netw_total = np.array(extract_csv(fName, "T_sst_heat_return_netw_total", DAYS_IN_YEAR))
    T_sst_cool_return_netw_total = np.array(extract_csv(fName, "T_sst_cool_return_netw_total", DAYS_IN_YEAR))


    
    return mdot_heat_netw_total, mdot_cool_netw_total, Q_DH_building_netw_total,Q_DC_building_netw_total,T_sst_heat_return_netw_total, T_sst_cool_return_netw_total
    
def import_solar_data(fName, DAYS_IN_YEAR, HOURS_IN_DAY):
    ''' 
    
    importing and preparing raw data for analysis of the district network 

        
    Parameters
    ----------
    fName : string
        Name of File where solar data is stored in
        
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

        
        
    Solar_Area_Array = np.array(extract_csv(fName, "Area", DAYS_IN_YEAR))
    Solar_Area = Solar_Area_Array[0]
    Solar_E_aux_kW = np.array(extract_csv(fName, "Eaux_kW", DAYS_IN_YEAR))
    Solar_Q_th_kW = np.array(extract_csv(fName, "Qsc_Kw", DAYS_IN_YEAR))
    
    Solar_Tscs_th = np.array(extract_csv(fName, "Tscs", DAYS_IN_YEAR))
    
    Solar_mcp_kW_C = np.array(extract_csv(fName, "mcp_kW/C", DAYS_IN_YEAR))
    
    
    return Solar_Area, Solar_E_aux_kW, Solar_Q_th_kW, Solar_Tscs_th, Solar_mcp_kW_C
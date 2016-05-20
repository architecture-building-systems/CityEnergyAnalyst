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

def import_CentralizedPlant_data(fName, DAYS_IN_YEAR, HOURS_IN_DAY):
    ''' 
    
    importing and preparing raw data for analysis of the Centralized Plant Choice 
        
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
    
        
    Q_DH_networkload = np.array(extract_csv(fName, "Q_DH_networkload", DAYS_IN_YEAR))
    Q_aux_ch = np.array(extract_csv(fName, "Q_aux_ch", DAYS_IN_YEAR))
    
    
    Q_aux_dech = np.array(extract_csv(fName, "Q_aux_dech", DAYS_IN_YEAR))
    Q_missing = np.array(extract_csv(fName, "Q_missing", DAYS_IN_YEAR))
    Q_storage_content_Wh = np.array(extract_csv(fName, "Q_storage_content_Wh", DAYS_IN_YEAR))
    Q_to_storage = np.array(extract_csv(fName, "Q_to_storage", DAYS_IN_YEAR))
    Solar_Q_th_W = np.array(extract_csv(fName, "Solar_Q_th_W", DAYS_IN_YEAR))

    
    return Q_DH_networkload, Q_aux_ch,Q_aux_dech, Q_missing, Q_storage_content_Wh, Q_to_storage, Solar_Q_th_W
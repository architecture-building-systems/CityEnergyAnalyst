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
    result = pd.read_csv(fName, usecols=[colName], nrows=24*DAYS_IN_YEAR)
    return result

def import_CentralizedPlant_data(fName, DAYS_IN_YEAR, HOURS_IN_DAY):
    ''' 
    
    importing and preparing network data for analysis of the Centralized Plant Choice 
        
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
            
    Q_DH_networkload, E_aux_ch,E_aux_dech, Q_missing, Q_storage_content_Wh, Q_to_storage, Solar_Q_th_W
    
    '''
    
    
    """     import dataframes    """
    # mass flows
    
    #print fName
    Q_DH_networkload = np.array(extract_csv(fName, "Q_DH_networkload", DAYS_IN_YEAR))
    E_aux_ch = np.array(extract_csv(fName, "E_aux_ch", DAYS_IN_YEAR))
    
    
    E_aux_dech = np.array(extract_csv(fName, "E_aux_dech", DAYS_IN_YEAR))
    Q_missing = np.array(extract_csv(fName, "Q_missing", DAYS_IN_YEAR))
    Q_storage_content_Wh = np.array(extract_csv(fName, "Q_storage_content_Wh", DAYS_IN_YEAR))
    Q_to_storage = np.array(extract_csv(fName, "Q_to_storage", DAYS_IN_YEAR))
    Q_from_storage = np.array(extract_csv(fName, "Q_from_storage_used", DAYS_IN_YEAR))
    Q_uncontrollable = np.array(extract_csv(fName, "Q_uncontrollable_hot", DAYS_IN_YEAR))
    E_PV_Wh = np.array(extract_csv(fName, "E_PV_Wh", DAYS_IN_YEAR)) 
    E_PVT_Wh = np.array(extract_csv(fName, "E_PVT_Wh", DAYS_IN_YEAR)) 
    #print " \n ----------- "
    #print "E_PVT_Wh Sum in Import netw. data functions: ", np.sum(E_PVT_Wh)
    
    
    E_aux_HP_uncontrollable = np.array(extract_csv(fName, "E_aux_HP_uncontrollable", DAYS_IN_YEAR)) 
    Q_SCandPVT = np.array(extract_csv(fName, "Q_SCandPVT_coldstream", DAYS_IN_YEAR)) 
    HPServerHeatDesignArray = np.array(extract_csv(fName, "HPServerHeatDesignArray", DAYS_IN_YEAR))
    HPpvt_designArray = np.array(extract_csv(fName, "HPpvt_designArray", DAYS_IN_YEAR))
    HPCompAirDesignArray = np.array(extract_csv(fName, "HPCompAirDesignArray", DAYS_IN_YEAR))
    HPScDesignArray = np.array(extract_csv(fName, "HPScDesignArray", DAYS_IN_YEAR)) 
    E_produced_solarAndHPforSolar = np.array(extract_csv(fName, "E_produced_total", DAYS_IN_YEAR)) 
    E_consumed_without_buildingdemand_solarAndHPforSolar = np.array(extract_csv(fName, "E_consumed_total_without_buildingdemand", DAYS_IN_YEAR)) 

    
    return Q_DH_networkload, E_aux_ch,E_aux_dech, Q_missing, Q_storage_content_Wh, Q_to_storage, Q_from_storage,\
                Q_uncontrollable, E_PV_Wh, E_PVT_Wh, E_aux_HP_uncontrollable, Q_SCandPVT, HPServerHeatDesignArray,\
                HPpvt_designArray, HPCompAirDesignArray, HPScDesignArray, E_produced_solarAndHPforSolar,\
                E_consumed_without_buildingdemand_solarAndHPforSolar
                
def import_solar_PeakPower(fNameTotalCSV, nBuildingsConnected, gv):
    
    AreaAllowed = np.array(extract_csv(fNameTotalCSV, "Af", nBuildingsConnected)) 
    nFloors = np.array(extract_csv(fNameTotalCSV, "Floors", nBuildingsConnected)) 
    
    AreaRoof = np.zeros(nBuildingsConnected)
    
    for building in range(nBuildingsConnected):
        AreaRoof[building] = AreaAllowed[building] / (nFloors[building] * 0.9) 
        
    PeakPowerAvgkW = np.sum(AreaRoof) * gv.eta_area_to_peak / nBuildingsConnected
    
    if nBuildingsConnected == 0:
        PeakPowerAvgkW = 0
        
    print "\n PeakPowerAvgkW \n", PeakPowerAvgkW
    
    return PeakPowerAvgkW
    
    
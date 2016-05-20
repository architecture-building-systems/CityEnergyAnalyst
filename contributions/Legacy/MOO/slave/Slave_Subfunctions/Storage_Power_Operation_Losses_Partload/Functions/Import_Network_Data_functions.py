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
        T_sst_heat_return_ofmaxQh, T_sst_cool_return_ofmaxQc, Q_wasteheat_netw_total, Q_serverheat_netw_total
    
    
    '''
    
    
    """     import dataframes    """
    # mass flows
        
        
    mdot_heat_netw_total = np.array(extract_csv(fName, "mdot_DH_netw_total", DAYS_IN_YEAR))
    mdot_cool_netw_total = 0 #np.array(extract_csv(fName, "mdot_cool_netw_total", DAYS_IN_YEAR))
    
    
    Q_DH_building_netw_total = np.array(extract_csv(fName, "Q_DH_building_netw_total", DAYS_IN_YEAR))
    Q_DC_building_netw_total = 0 #np.array(extract_csv(fName, "Q_DC_building_netw_total", DAYS_IN_YEAR))
    T_sst_heat_return_netw_total = np.array(extract_csv(fName, "T_sst_heat_return_netw_total", DAYS_IN_YEAR))
    T_sst_heat_supply_netw_total = np.array(extract_csv(fName, "T_sst_heat_supply_netw_total", DAYS_IN_YEAR))
    T_sst_cool_return_netw_total =  0 #np.array(extract_csv(fName, "T_sst_cool_return_netw_total", DAYS_IN_YEAR))
    
    Q_wasteheat_netw_total = np.array(extract_csv(fName, "Qcdata_netw_total", DAYS_IN_YEAR))
    #print "sum of Qcdata_netw_total", Q_wasteheat_netw_total
    Q_serverheat_netw_total = np.array(extract_csv(fName, "Ecaf_netw_total", DAYS_IN_YEAR))


    
    return mdot_heat_netw_total, mdot_cool_netw_total, Q_DH_building_netw_total,Q_DC_building_netw_total,T_sst_heat_return_netw_total,\
                        T_sst_cool_return_netw_total, T_sst_heat_supply_netw_total, Q_wasteheat_netw_total, Q_serverheat_netw_total
    
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

    if fName == "Pv.csv":
        Pv_kWh_PV_import = np.array(extract_csv(fName, "PV_kWh", DAYS_IN_YEAR))
        Pv_kWh_PV = Pv_kWh_PV_import[:,0]
        PV_kWh_PVT = np.zeros(24*DAYS_IN_YEAR)
        Solar_Area = np.zeros(24*DAYS_IN_YEAR)
        Solar_E_aux_kW = np.zeros(24*DAYS_IN_YEAR)
        Solar_Q_th_kW = np.zeros(24*DAYS_IN_YEAR)
        Solar_Tscs_th = np.zeros(24*DAYS_IN_YEAR)
        Solar_Tscr_th = np.zeros(24*DAYS_IN_YEAR)
        Solar_mcp_kW_C = np.zeros(24*DAYS_IN_YEAR)
        #print "PV"
    
    elif fName == "PVT_35.csv":
        Pv_kWh_PV = np.zeros(24*DAYS_IN_YEAR)
        PV_kWh_PVT_import = np.array(extract_csv(fName, "PV_kWh", DAYS_IN_YEAR))
        PV_kWh_PVT = PV_kWh_PVT_import[:,0]
        Solar_Area_Array = np.array(extract_csv(fName, "Area", DAYS_IN_YEAR))
        Solar_Area = Solar_Area_Array[0]
        Solar_E_aux_kW = np.array(extract_csv(fName, "Eaux_kWh", DAYS_IN_YEAR))
        Solar_Q_th_kW = np.array(extract_csv(fName, "Qsc_KWh", DAYS_IN_YEAR)) + 0.0
        #Solar_Tscs_th = np.array(extract_csv(fName, "Tscs", DAYS_IN_YEAR))
        Solar_Tscs_th = np.zeros(24*DAYS_IN_YEAR)
        Solar_Tscr_th = np.array(extract_csv(fName, "Tscr", DAYS_IN_YEAR)) + 273.0
        Solar_mcp_kW_C = np.array(extract_csv(fName, "mcp_kW/C", DAYS_IN_YEAR))
        #print "PVT 35"
        
        # Replace by 0 if negative values
        Tscs = np.array( pd.read_csv( fName, usecols=["Tscs"], nrows=1 ) ) [0][0]
        
        for i in range(DAYS_IN_YEAR * HOURS_IN_DAY):
            if Solar_Q_th_kW[i][0] < 0:
                Solar_Q_th_kW[i][0] = 0
                Solar_E_aux_kW[i][0] = 0
                Solar_Tscr_th[0] = Tscs + 273
                Solar_mcp_kW_C[i][0] = 0
    
    else:
        Solar_Area_Array = np.array(extract_csv(fName, "Area", DAYS_IN_YEAR))
        Solar_Area = Solar_Area_Array[0]
        Solar_E_aux_kW = np.array(extract_csv(fName, "Eaux_kW", DAYS_IN_YEAR))
        Solar_Q_th_kW = np.array(extract_csv(fName, "Qsc_Kw", DAYS_IN_YEAR)) + 0.0 
        Solar_Tscr_th = np.array(extract_csv(fName, "Tscr", DAYS_IN_YEAR)) + 273.0
        #Solar_Tscs_th = np.array(extract_csv(fName, "Tscs", DAYS_IN_YEAR))
        Solar_Tscs_th = np.zeros(24*DAYS_IN_YEAR)
        
        Solar_mcp_kW_C = np.array(extract_csv(fName, "mcp_kW/C", DAYS_IN_YEAR))
        Pv_kWh_PV = np.zeros(24*DAYS_IN_YEAR)
        PV_kWh_PVT = np.zeros(24*DAYS_IN_YEAR)
        
        # Replace by 0 if negative values
        Tscs = np.array( pd.read_csv( fName, usecols=["Tscs"], nrows=1 ) ) [0][0]
        
        for i in range(DAYS_IN_YEAR * HOURS_IN_DAY):
            if Solar_Q_th_kW[i][0] < 0:
                Solar_Q_th_kW[i][0] = 0
                Solar_E_aux_kW[i][0] = 0
                Solar_Tscr_th[0] = Tscs + 273
                Solar_mcp_kW_C[i][0] = 0
        
        #print "SC"
    #print "PV_kWh_PVT", np.shape(PV_kWh_PVT)
    #print "Pv_kWh_PV", np.shape(Pv_kWh_PV)
    PV_kWh = PV_kWh_PVT + Pv_kWh_PV
    #print "PV_kWh", np.shape(PV_kWh)
    #print PV_kWh_PVT
    #print Solar_Q_th_kW[:,0]
    return Solar_Area, Solar_E_aux_kW, Solar_Q_th_kW, Solar_Tscs_th, Solar_mcp_kW_C, PV_kWh, Solar_Tscr_th
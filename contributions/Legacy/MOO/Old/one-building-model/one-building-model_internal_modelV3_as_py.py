# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <headingcell level=5>

# Appraoch C  as seperate code

# <codecell>

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
# has to be completed manually!!

import csv

import os
import scipy
import matplotlib.pyplot as plt
os.chdir("/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Python_Testcases")

# <codecell>

exch_type  = "MT"
A_design = 0
U = 840
cp = 4185
k_design = 0
nDay = 365

# <codecell>

"""
==================
K-means clustering
==================

Provides routines for k-means clustering

"""
from __future__ import division
import numpy as np
import pandas as pd
from scipy.cluster.vq import kmeans,vq,whiten
from sklearn import metrics


def extract_csv(fName, colName, nDay):
    """
    Extract data from one column of a csv file to a pandas.DataFrame
    
    Parameters
    ----------
    fName : string
        Name of the csv file.
    colName : string
        Name of the column from whom to extract data.
    nDay : int
        Number of days to consider.
        
    Returns
    -------
    result : pandas.DataFrame
        Contains the hour of the day in the first column and the data 
        of the selected column in the second.   
    
    """
    result = pd.read_csv(fName, usecols=["DATE", colName], nrows=24*nDay)
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


def cluster(obs,nPeriod):
    """
    Takes an array of observations and the desired number of typical
    days. Returns the array of typical days and an array which assigns
    each day to a typical day.
    
    Parameters
    ----------
    obs : ndarray
        Array of observations. Each row represents a day and each column
        a feature.
    nPeriod : int
        Desired number of typical periods to obtain.
    
    Returns
    -------
    typical_days : ndarray
        Each row represents a typical day and each column a feature.
    distorsion : float
        The square error between the observations and the centroids.
    codebook : ndarray
        Assigns to each day of obs, the corresponding typical day.
        
    """
    obs_wh = whiten(obs)
    obs_km = kmeans(obs_wh, nPeriod)
    obs_vq = vq(obs_wh, obs_km[0])

    typical_days = obs_km[0]*np.std(obs,axis =0)
    distorsion = obs_km[1]
    codebook = obs_vq[0]
    
    return typical_days, distorsion, codebook


def strip(array):
    """
    Strips out the columns, at the beginning and the end of the array,
    where there are only 0.
    
    Parameters
    ----------
    array : ndarray
    
    Returns
    -------
    result : ndarray
        Stripped array
    front : int
        Number of columns stripped at the beginning of the array
    back : int
        Number of columns stripped at the end of the array
        
    """
    stop = False
    front = 0
    back_rk = int(array.shape[1])-1
    
    while not stop:
        if np.count_nonzero(array[:,front]) == 0:
            front += 1
        else:
            stop = True
    
    stop = False
    while not stop:
        if np.count_nonzero(array[:,back_rk]) == 0:
            back_rk -= 1
        else:
            stop = True

    result = array[:,front:(back_rk+1)]
    back = int(array.shape[1]) - back_rk - 1
    
    return result, front, back


def unstrip(array, front, back):
    """
    Takes an array and adds 0 columns at the front and at the back.
    
    Parameters
    ----------
    array : ndarray
    front : int
        Number of columns to add at the front
    back : int
        Number of columns to add at the back
    
    Returns
    -------
    result : ndarray
        Array with 0 columns added
        
    """
    length = int(array.shape[0])
    front_array = np.zeros((length,front))
    back_array = np.zeros((length,back))
    
    result = np.concatenate((front_array.T,array.T,back_array.T))
    
    return result.T


def silhouette(obs, cb):
    """
    Parameters
    ----------
    obs : ndarray
        Array of observations. Each row represents a day and each column
        a feature.
    cb : ndarray
        Codebook
        
    Returns
    -------
    silhouette : float
        Silhouette Score

    """
    obs_norm = (obs - obs.mean()) / (obs.max() - obs.min()) # normalized
    obs_matrix = np.matrix(obs_norm) # create matrix form    
    
    #Calc Silhouette Coeff Score (for global use)
    silhouette = metrics.silhouette_score(obs_matrix, cb, metric='euclidean')
    
    return silhouette



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
        T_supply_dataframe = extract_csv(building_list[i], feature, nDay)
        T_supply_array = toarray(T_supply_dataframe) + 273
        # using the array in the type of: [buidling number, day, hour]
        T_supply_array_all_buildings[i,:,:] = T_supply_array
    

        #find max Temp of all Buildings at every timestep

    for k in range(DAYS_IN_YEAR):
        for j in range(HOURS_IN_DAY):
    # using the array in the type of: [buidling number, day, hour]
            T_supply_max_all_buildings[k-1,j-1] = max(T_supply_array_all_buildings[:,k-1,j-1])
    
    return T_supply_max_all_buildings

            
def load_curve(array):
    """
    creates a load curve from an input array
    
    Parameters
    ----------
    array : ndarray
        input of data, from which a load curve should be returned
    
    Returns
    -------
        
    load_curve : ndarray
        gives load curve of the input array
        
    """
    
    load_duration = np.sort(array, axis=0)
    load_duration_sorted = load_duration[::-1]
    
    return load_duration_sorted      

def dhw_hex_design(Q_dhw_max, T_amb_max, hex_type) :
    
    """
    
    Designs the Domestic Hot Water heat exchanger on behalf of the Nominal Load (Q_design) and Ambient Temperature (T_amb_max)
    In addition, an exchanger-type (hex_type) can be defined (either "HT" or "LT")
    
    
    Parameters
    ----------
    Q_dhw_max : float
        Maximum heat dem for domestic hot water [W]
        
    T_amb_max : float
        maximum ambient temperature in [K]
        
    Returns
    -------
    A_hex_dhw_design : float
        design Area in [m^2]
        
    mdot_dhw_design : float
        massflow at design conditions [kg/s]

    
    Assumptions:
     U = 840 W/m^2*K
     
     Assuming HT-Design if not specified as LT
     
     (Name convention as Palsson et al. 1999)
     
     T_s2 :  Warm Water Target Temp
     
      - for "HT" design
         T_s2 = 60Â°C 
         
      - for "LT" design
         T_s2 = 50Â°C
         
     T_r2 : cold Water input Temp, to be heated 
      - T_r2 = 10Â°C (for "LT" and "HT")
     
     T_s1 = T_s2 + 5Â°C
    
     T_r1 = T_amb_max + 5Â°C
                
     
    """ 
    U = 840 # W/m^2*K
    
    if hex_type == "LT":
        T_s2 = 50 + 273
    
    else:
        T_s2 = 60 + 273
        
    T_r2 = 10 + 273
    T_s1 = T_s2 + 5
    T_r1 = T_amb_max + 5
    
    T_log_mean = ( ( (T_s1 - T_s2) - (T_r1 - T_r2) ) / ( scipy.log(T_s1 - T_s2) - scipy.log(T_r1 - T_r2) ))
    
    A_hex_dhw_design = Q_dhw_max / ( U * T_log_mean)
    
    mdot_dhw_design = Q_dhw_max / ( (T_s1 - T_r1) * cp)
    
    return A_hex_dhw_design, mdot_dhw_design



def heating_hex_design(Q_heating_max, T_return_min_global, T_supply_max_global, hex_type) :
    
        
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
        
    Returns
    -------
    A_hex_heating_design : float
        design Area in [m^2]
        
    mdot_heating_design : float
        massflow at design conditions [kg/s]

    
    Assumptions:
     U = 840 W/m^2*K
     
     Assuming that the Ambient temperature is not restricting the return temperature 1 (T_r1)
     as the maximum load occurs during cold days --> T_r1 = T_r2 + deltaT 
     
     Assuming HT-Design if not specified as LT
     
     --> Name convention as Palsson et al. 1999)
     
     T_s2 :  Warm Water Target Temp
     
      - for "HT" design
         T_s2 = 60Â°C 
         
      - for "LT" design
         T_s2 = 50Â°C
         
     T_r2 : cold Water input Temp, to be heated 
      - T_r2 = 10Â°C (for "LT" and "HT")
     
     T_s1 = T_s2 + 5Â°C
    
     T_r1 = T_amb_max + 5Â°C
                
     
    """ 
    U = 840 # W/m^2*K
    
    if hex_type == "LT":
        T_s1 = 50 + 273 + 5
    
    else:
        T_s1 = 60 + 273 + 5
        
    T_r2 = T_return_min_global
    T_s2 = T_supply_max_global
    T_r1 = T_r2 + 5
    
   # print "T_s1 = ", T_s1-273, "; T_s2 = ", T_s2-273, "; T_r1 = ", T_r1-273, "; T_r2 =", T_r2-273
    
    T_log_mean = ( ( (T_s1 - T_s2) - (T_r1 - T_r2) ) / ( scipy.log(T_s1 - T_s2) - scipy.log(T_r1 - T_r2) ))
    
    A_hex_heating_design = Q_heating_max / ( U * T_log_mean)
    
    mdot_heating_design = Q_heating_max / ( (T_s1 -  T_r1) * cp)
    
    return A_hex_heating_design, mdot_heating_design


def mixing_process(mdot_dhw, T_r1_dhw, mdot_heating,T_r1_heating):
    
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
   
   
    mdot_bld = mdot_dhw + mdot_heating
    T_r2_bld = ( T_r1_dhw * mdot_dhw + T_r1_heating * mdot_heating) / mdot_bld
    
    if mdot_dhw == 0:
        mdot_bld = mdot_heating
        T_r2_bld = T_r1_heating
        
    
    if mdot_heating == 0:
        mdot_bld = mdot_dhw
        T_r2_bld = T_r1_dhw
        
    
    return mdot_bld, T_r2_bld
    
    
def dhw_hex_operation(Q_dhw, hex_type, A_hex_dhw_design):
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
            
    Returns
    -------
    T_r1_dhw : float
        return temperature of hot water heat exchanger
    
    mdot_dhw : float
        massflow required for operation of this heat exchanger
    
    Assumptions:
        - no losses
        - lower the massflow as long as possible, no minimum massflow required
        - target temperature of hot water in building (@LT = 45Â°C, @MT = 60Â°C)
     
    """ 
   
    T_s1 = 65 + 273
    T_s2 = 60 + 273 # Target temp of hot water @ LT design
    
    if hex_type == "LT":
        T_s1 = 50 + 273
        T_s2 = 45 + 273 # Target temp of hot water @ LT design
    
    T_r2 = 10 + 273 
    T_r1_dhw = np.maximum(T_r2 + 5, T_amb + 5)
   
    
    U = 840 
    cp = 4185
    
    #def fh(x):
        #Eq = ( (T_s1 - T_s2) - (x - T_r2) ) / ( scipy.log( (T_s1 - T_s2)/(x - T_r2) ) ) - Q_dhw / (A_dhw_design * U)
        #return Eq
    
    #T_r1_dhw = scipy.optimize.brentq(fh, 0, 298)
    #rint "calculated T_r1_dhw", T_r1_dhw-273

        
    #else:
    mdot_dhw = Q_dhw / (cp * (T_s1 - T_r1_dhw))
    if mdot_dhw == mdot_dhw_design:
        print "design point achieved"
    
    #print mdot_dhw, mdot_dhw_design
    
    LMTD =((T_s1 - T_s2) - (T_r1_dhw - T_r2) ) / ( scipy.log((T_s1 - T_s2)/(T_r1_dhw - T_r2)))
    
    A_hex_check = Q_dhw / ( U * LMTD)
    # print A_check, A_dhw_design
    if A_hex_check > A_hex_dhw_design*1.01:
        print "ERROR!", A_hex_check, A_hex_dhw_design
    elif mdot_dhw > mdot_dhw_design*1.01:
        print "ERROR at massflow"
        print "mdot_dhw is equal to", mdot_dhw
        
    return T_r1_dhw, mdot_dhw
        


def heating_hex_operation(Q_heating, T_r2_heating, T_s2_heating, hex_type, A_hex_heating_design, mdot_heating_design, T_amb):
    
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
        massflow at design conditions, can be calculated by heating_hex_design( ) - function
    
               
    Returns
    -------
    T_r1_heating : float
        return temperature of heating-circuit heat exchanger
    
    mdot_heating : float
        massflow required for operation of heating-circuit heat exchanger
    
    Assumptions:
        - no losses
        - lower the massflow as much as possible, no minimum massflow required
     
    """ 
    # values from J+ :
    T_s2 = T_s2_heating 
    T_r2 = T_r2_heating 
    
    T_s1 = 65 + 273 # T_DHW_supply + % 5Â°C 
    T_r1 = T_r2 + 5 # maintain 5Â°C Temp gap

    
    if hex_type == "LT":
        T_s1 = 50 + 273
    

    #U = 840 
    #cp = 4185
    
    def fh(x):
        Eq = ( (T_s1 - T_s2) - (x - T_r2) ) / ( scipy.log( (T_s1 - T_s2)/(x - T_r2) ) ) - Q_heating_max / (A_hex_heating_design * U)
        return Eq
    
    T_r1_calc = scipy.optimize.brentq(fh, 0, 350)
    #print "calculated T_r1_heating", T_r1_calc - 273
    #print "T_r1 heating design", T_r1 - 273
   
    
    if  T_r1_calc < T_r2 + 5: # Check if 5Â°C temp drop is maintained
        T_r1 = np.maximum(T_r2 + 5, T_amb)
    #    print "T_r1 heating adjusted"
        
    else:
        T_r1 = T_r1_calc
    #    print "T_r1 is set to T_r1_calc"
        
    mdot_heating = Q_heating / (cp * (T_s1 - T_r1))
    
    #print "massflows (operation, Design) :", mdot_heating, mdot_heating_design
    
    LMTD =((T_s1 - T_s2) - (T_r1 - T_r2) ) / ( scipy.log((T_s1 - T_s2)/(T_r1 - T_r2)))
    
    A_hex_check = Q_heating / ( U * LMTD)
    
    #print A_check, A_heating_design
    if A_hex_check > A_hex_heating_design * 1.01:
        print "ERROR at area", A_hex_check, A_hex_heating_design
        
    elif mdot_heating > mdot_heating_design * 1.05:
        print "ERROR at massflow"
        
        
    #print "actual return temp 1", T_r1 - 273
    
    return T_r1, mdot_heating
        
  # Q_finalheat_array is given = total heating dem
def interface_hex_design(Q_finalheat_max, T_return_min_global, T_supply_max_global, hextype):
    """
   
    Designs the district heating / building interface heat exchanger 
    on behalf of the Nominal Load (Q_finalheating_max) and minimum 
    return temperature of the building (T_return_min_global)
    
    The maximum supply temperature is set by the maximum temperature of 
    the heating requirement (J+) or hot water dem
    @ LT: 45Â°C + deltaT; @ HT: 60Â°C + deltaT 
    
    In addition, an exchanger-type (hex_type) can be defined (either "HT" or "LT")
    
    
    Parameters
    ----------
    Q_finalheat_max : float
        Maximum heat dem for of the entire building [W]
        
    T_return_min_global : float
        lowest return temperature at maximum load [K]
    
    T_supply_max_global : float
        highest temperature required by the heating system at maximum load [K]
        
        
    Returns
    -------
    
    A_hex_DH_design : float
        design Area of interface heat exchanger in [m^2]
        
    mdot_HD_design : float
        massflow of DH system to building at design conditions [kg/s]

    
    
    Assumptions:
     U = 840 W/m^2*K
     
     Assuming HT-Design if not specified as LT
     
     (Name convention as Palsson et al. 1999)
     
     T_s2 :  Minimum Supply Temperature required by the building
     
      - for "HT" design
         T_s2 = 60Â°C 
         
      - for "LT" design
         T_s2 = 50Â°C
         
      - if T_supply_max_global > T_s2 
         --> use T_supply_max_global as design Temp of T_s2
      
     T_r2 : Return Temperature @ Q_finalheat_max
      - T_r2 is set to T_return_min_global + deltaT 
        ( = highest return temperature at max load)
      
     
     T_s1 = T_s2 + 6Â°C
    
     T_r1 = T_r2 + 5Â°C
                
     
    """ 
    
    
    
    
    T_s2 = 60 + 5 + 273 # = Temp Hot water + design temp.diff of 5Â°C
    
    if hex_type == "LT":
        T_s2 = 45 + 5 + 273 # lower temp of hot water @ LT design 
    
    T_s1 = T_s2 + 6 # minimum temperature lift 
    T_r2 = T_return_min_global + 5 # minimum return Temp + delta_T over first heat-exchanger
    T_r1 = T_r2 + 5
    
    mdot_DH_design = Q_finalheat_max / ((T_s1 - T_r1) * cp )
    
    
    #check for Area
    LMTD =((T_s1 - T_s2) - (T_r1 - T_r2) ) / ( scipy.log((T_s1 - T_s2)/(T_r1 - T_r2)))
    A_hex_DH_design = Q_finalheat_max / (U * LMTD)
    
    return A_hex_DH_design, mdot_DH_design
        


def interface_hex_operation(Q_finalheat, T_r2_bld, T_supply_max_all_buildings, hextype, mdot_DH_min, A_hex_interface_design):
    
    """
    
    gives return temperature and massflow of interface to the district heating
    
    
    Parameters
    ----------
    Q_finalheat : float
        Thermal load of building (inlc. hot water and all services) (defined by J+)
    
    T_r2_bld : float
        return temperature after mixing
        
    T_supply_max_all_buildings : float
        maximum temperature required of all buildings, prediscribes the max. temp of supply
    
    hex_type : string
        heat exchanger type, either "LT" or "MT" (standard = "MT")
        
    mdot_DH_min : float
        minimum massflow in DH system 
       
    A_hex_interface_design : float
        Design Area, can be calculated by heating_hex_design( ) - function
        
               
    Returns
    -------
    T_r1_DH : float
        return temperature of interface heat-exchanger to DH network
    
    T_s1_DH : float
        supply temperature required from district heating
    
    mdot_DH : float
        massflow required in DH pipe for operation of interface heat exchanger
    
    Assumptions:
        - no losses
        - lower the massflow as much as possible, no minimum massflow required
     
    """ 
    
    T_s2 = 60 + 5 + 273 # = Temp Hot water + design temp.diff of 5Â°C
    
    if hex_type == "LT":
        T_s2 = 45 + 5 + 273 # lower temp of hot water @ LT design 
    
    T_s1 = np.maximum(T_supply_max_all_buildings + 6, T_s2 + 6)
    T_r2 = T_r2_bld # return Temp after mixing
    T_r1 = T_r2 + 5
    
    mdot_DH =  Q_finalheat / ((T_s1 - T_r1) * cp)
    
    if Q_finalheat == 0:
        mdot_DH = mdot_DH_min
        T_r1 = T_s1
    
    if mdot_DH < mdot_DH_min: # maintain minimum flow, adjust return temperature in case of too low flow
        mdot_DH = mdot_DH_min
        T_r1 = T_s1 - Q_finalheat / (mdot_DH_min * cp) 
    
    #check for Area
    LMTD =( (T_s1 - T_s2) - (T_r1 - T_r2) ) / ( scipy.log((T_s1 - T_s2)/(T_r1 - T_r2)))
    A_hex_check = Q_finalheat / ( U * LMTD)
    
    # print A_check, A_dhw_design
    if A_hex_check > A_hex_interface_design*1.01:
        print "ERROR!", A_hex_check, A_hex_dhw_design
    
    if mdot_DH > mdot_DH_design*1.01:
        print "ERROR at massflow"
        print "mdot_dhw is equal to", mdot_dhw
        
    return  T_r1, T_s1, mdot_DH
        
        
    
 

# <codecell>


# <codecell>


# <codecell>


# <codecell>

Q_finalheat_dataframe = extract_csv(fName, "Qh", nDay)
Q_cool_dataframe = extract_csv(fName, "Qc", nDay)
Electr_dataframe = extract_csv(fName, "E", nDay)
T_supply_dataframe = extract_csv(fName, "tshs", nDay)
T_return_dataframe = extract_csv(fName, "trhs", nDay)
Q_dhw_dataframe = extract_csv(fName, "Qwwf", nDay)
# T_amb_dataframe = TO BE INCLUDED

Q_finalheat_array = toarray(Q_finalheat_dataframe) * 1000 # Convert from kW to W
Q_cool_array = toarray(Q_cool_dataframe) * 1000 # Convert from kW to W
Q_dhw_array = toarray(Q_dhw_dataframe) * 1000 # Convert from kW to W
Q_heating_array = Q_finalheat_array - Q_dhw_array # Extract heating part only

Electr_array = toarray(Electr_dataframe) * 1000 # Convert from kW to W
T_supply_array = toarray(T_supply_dataframe) + 273 # Convert from Â°C to K
T_return_array = toarray(T_return_dataframe) + 273 # Convert from Â°C to K
# T_amb_array = TO BE INCLUDED
T_amb_array = 20 + 273 # Convert from Â°C to K
    
Q_finalheat_max = np.max(Q_finalheat_array)
Q_cool_max = np.max(Q_cool_array)  
Q_heating_max = np.max(Q_heating_array)
Q_dhw_max = np.max(Q_dhw_array)
T_amb_max = np.max(T_amb_array)

T_supply_max_global = T_supply_array[(find_index_of_max(Q_finalheat_array))] 
T_return_min_global = T_return_array[(find_index_of_max(Q_finalheat_array))] 



#gives maximum supply temperature to building = T_s2 after PÃ¡lsson et al
feature = "tshs"
T_supply_max_all_buildings = find_max_temp_of_buildings(building_list, feature)

#gives maximum return temperature to building = T_r2 after PÃ¡lsson et al
feature = "trhs"
T_return_min_all_buildings = find_max_temp_of_buildings(building_list, feature)



# <codecell>


cp = 4185.5 # J/KgK


#building a loop around this part 
HOURS_IN_DAY = 24
DAYS_IN_YEAR = 365

#define empty arrays
T_supply_DH_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
T_return_DH_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
mdot_DH_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))

mdot_bld_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
T_r2_bld_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))


mdot_dhw_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))
mdot_heating_result = np.zeros((DAYS_IN_YEAR,HOURS_IN_DAY))

#define operating conditions

hex_type = "MT"
T_amb = 20 + 273
T_amb_max = 20 + 273
T_ground = 10 + 273
Q_heating_design = Q_heating_max
Q_dhw_design = Q_dhw_max
Q_finalheat_design = Q_finalheat_max


#designing the in-house heat exchangers
A_hex_heating_design, mdot_heating_design = heating_hex_design(Q_heating_design, T_return_min_global, T_supply_max_global, hex_type)
A_hex_dhw_design, mdot_dhw_design = dhw_hex_design(Q_dhw_design, T_amb_max, hex_type)
A_hex_interface_design, mdot_interface_design = interface_hex_design(Q_finalheat_max, T_return_min_global, T_supply_max_global, "MT")

print "loop is running"

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
        
        
print "Completet - no errors occured"   

# <codecell>

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

# <codecell>

import this

# <codecell>



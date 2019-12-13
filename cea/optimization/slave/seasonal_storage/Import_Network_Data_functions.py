""" 

Import Network Data:
  
    This File reads all relevant thermal data for further analysis in the Slave Routine, 
    Namely : Thermal (J+) and Solar Data (J+) 
            
"""
import pandas as pd
import numpy as np
from cea.constants import HOURS_IN_YEAR

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Thuy-an Ngugen", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def import_solar_thermal_data(fName):
    """
    importing and preparing raw data for analysis of the district distribution

    :param fName: name of file where solar data is stored in
    :return: Arrays containing all relevant data for further processing:
        mdot_sst_heat, mdot_sst_cool, T_sst_heat_return, T_sst_heat_supply, T_sst_cool_return,
        Q_DH_building, Q_DC_building, Q_DH_building_max, Q_DC_bulding_max, T_sst_heat_supply_ofmaxQh,
        T_sst_heat_return_ofmaxQh, T_sst_cool_return_ofmaxQc
    :rtype: list
    """

    if fName == "PVT_total.csv":
        solar_data = pd.read_csv(fName, nrows=HOURS_IN_YEAR)
        PV_kWh = np.zeros(HOURS_IN_YEAR)
        PV_PVT_import_kWh = np.array(solar_data['E_PVT_gen_kWh'])
        PVT_kWh = PV_PVT_import_kWh
        Solar_Area_Array = np.array(solar_data['Area_PVT_m2'])
        Solar_Area_m2 = Solar_Area_Array[0]
        Solar_E_aux_kWh = np.array(solar_data['Eaux_PVT_kWh'])
        Solar_Q_th_kWh = np.array(solar_data['Q_PVT_gen_kWh']) + 0.0
        Solar_Tscs_th = np.zeros(HOURS_IN_YEAR)
        Solar_Tscr_th_K = np.array(solar_data['T_PVT_re_C']) + 273.15
        Solar_mcp_kWperC = np.array(solar_data['mcp_PVT_kWperC'])
        #print "PVT 35"
        
        # Replace by 0 if negative values
        Tscs = np.array( pd.read_csv( fName, usecols=["T_PVT_sup_C"], nrows=1 ) ) [0][0]
        
        for i in range(HOURS_IN_YEAR):
            if Solar_Q_th_kWh[i] < 0:
                Solar_Q_th_kWh[i] = 0
                Solar_E_aux_kWh[i] = 0
                Solar_Tscr_th_K[0] = Tscs + 273.15
                Solar_mcp_kWperC[i] = 0
    
    else:
        solar_data = pd.read_csv(fName, nrows=HOURS_IN_YEAR)
        Solar_Area_Array = np.array(solar_data['Area_SC_m2'])
        Solar_Area_m2 = Solar_Area_Array[0]
        Solar_E_aux_kWh = np.array(solar_data['Eaux_SC_kWh'])
        Solar_Q_th_kWh = np.array(solar_data['Q_SC_gen_kWh']) + 0.0
        Solar_Tscr_th_K = np.array(solar_data['T_SC_re_C']) + 273.15
        Solar_Tscs_th = np.zeros(HOURS_IN_YEAR)

        Solar_mcp_kWperC = np.array(solar_data['mcp_SC_kWperC'])
        PV_kWh = np.zeros(HOURS_IN_YEAR)
        PVT_kWh = np.zeros(HOURS_IN_YEAR)

        # Replace by 0 if negative values
        Tscs = np.array( pd.read_csv( fName, usecols=["T_SC_sup_C"], nrows=1 ) ) [0][0]
        
        for i in range(HOURS_IN_YEAR):
            if Solar_Q_th_kWh[i] < 0:
                Solar_Q_th_kWh[i] = 0
                Solar_E_aux_kWh[i] = 0
                Solar_Tscr_th_K[0] = Tscs + 273.15
                Solar_mcp_kWperC[i] = 0

    PV_kWh = PVT_kWh + PV_kWh

    return Solar_Area_m2, Solar_E_aux_kWh, Solar_Q_th_kWh, Solar_Tscs_th, Solar_mcp_kWperC, PV_kWh, Solar_Tscr_th_K
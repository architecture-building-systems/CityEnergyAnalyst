"""Data required for Slave from Master"""

"""
This File sets all variables for the slave optimization, that have to be set by the Master
"""
import os
Energy_Models_path ="/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/EnergySystem_Models"

os.chdir(Energy_Models_path)
import globalVar as gV
import numpy as np

reload(gV)

# Furnace
Furnace_P_max = 10.0E6 
Furn_Moist_type = gV.Furn_Moist_type # set the moisture content of wood chips, either "dry" or "wet"

# GAS TURBINE VARIABLES
gt_size = 1.0E6 # in Watt
gt_fuel = "NG"

# Boiler
Boiler_P_max = 10.0E6

# Cooling Tower :
CT_Qdesign = 10.0E6

# Storage
STORAGE_SIZE = 30000.0 # in m^3 - size of hot water storage tank (up to now a random variable)
STORAGE_HEIGHT = 15.0  # in m - height of hot water storage tank
A_storage_outside = STORAGE_SIZE/STORAGE_HEIGHT + 2 * np.pi * (STORAGE_SIZE/STORAGE_HEIGHT / np.pi)**0.5 #neglecting ground for heat losses
alpha_loss = 0.293542 # = 0.005 / (math.log10(26/25.0), from Vassilis-Storage Optimization Code
Storage_conv_loss = 0.1 # losses due to energy conversion from and to storage
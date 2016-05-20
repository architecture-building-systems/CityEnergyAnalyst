"""Data required for Slave from Master"""

"""
This File sets all variables for the slave optimization, that have to be set by the Master
"""
import os
Energy_Models_path ="/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/EnergySystem_Models"
Network_Raw_Data_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Results/Network_loads"
os.chdir(Energy_Models_path)
import globalVar as gV
import numpy as np

reload(gV)

# Name the file which should be loaded:
NETWORK_DATA_FILE = "Network_summary_result_new_loads_6_11_2014.csv"

# Ground Temperature
T_ground = 8 + 273.0 # K 

Network_Supply_Temp = 70 + 273.0

# Electricity_Type:
EL_TYPE = 'normal' # type normal or green (=green power) 


# Geothermal Heat Pump, 
GHP_max_i = gV.GHP_Cmax_Size_th # [W] Heat power (thermal output)
GHP_number = 5.0 # number of probes
GHP_max = GHP_number * GHP_max_i
GHP_SEASON_ON = 2190 # Hour in Year, when to switch on GHP
GHP_SEASON_OFF = 6570 # Hour in Year, when to switch off GHP

# Sewage Heat Pump
HPSew_maxSize = gV.HP_maxSize

# Lake Heat Pump
HPLake_maxSize = gV.HP_maxSize / 50.0
T_Lake = 8 + 273.0 # K 

# Furnace
Furnace_P_max = 1.0E7
Furn_Moist_type = "wet" #gV.Furn_Moist_type # set the moisture content of wood chips, either "dry" or "wet"

# GAS TURBINE VARIABLES
gt_size = 1.0E6 # in Watt
gt_fuel = "NG"


# Boiler - Thermal output power!
Boiler_P_max = 3.0E6 
Boiler_SIZE = Boiler_P_max/2.0
BoilerPeak_SIZE = 1.0E6

# Cooling Tower :
CT_Qdesign = 10.0E6

# Storage
STORAGE_SIZE = 1000000.0 # in m^3 - size of hot water storage tank (up to now a random variable)
STORAGE_HEIGHT = 3.0  # in m - height of hot water storage tank
A_storage_outside = STORAGE_SIZE/STORAGE_HEIGHT + 2 * np.pi * (STORAGE_SIZE/STORAGE_HEIGHT / np.pi)**0.5 #neglecting ground area for heat losses
alpha_loss = 0.0111 # EnergyPRO: 0.3 * 0.037 ; Saplamidis: 0.293542 # Wh / h= 0( .005 / (math.log10(26/25.0) ) , from Vassilis-Storage Optimization Code ** ACHTUNG !! CHANGE - SCALES WITH SIZE (?!)

Storage_conv_loss = 0.0111 # losses due to energy conversion from and to storage
T_storage_initial = 10 + 273.0 # initial Storage Temperature
T_storage_zero = 10 + 273.0 # Storage initial Temperature (Reference Temperature Storage) 
Q_in_storage_zero = STORAGE_SIZE *  1/ gV.Wh_to_J * gV.rho_60 * gV.cp * ( T_storage_zero - T_storage_initial)
dT_buffer = 5 # maintain a buffer for "uncertainties", never go below this temperature 
# Storage is initially empty

T_ST_MAX = 90 + 273.0 # Maximum Temperature of storage allowed
T_ST_MIN = 10 + 273.0

# Solar
SOLCOL_TYPE = "SC_ET50.csv" # type of collectors
SOLAR_PART = 0.1 # How much of the total area is available 


# declare, which power plants will be used : USED = 1  ; NOT USED = 0 
Boiler_on = 1
BoilerPeak_on = 1
Furnace_on = 1
GHP_on = 1
HP_Lake_on = 1
HP_Sew_on = 0
CHP_on = 0
CHP_GT_SIZE = 8.0E6

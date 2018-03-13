# -*- coding: utf-8 -*-
"""
Data required for Slave from Master
This File sets all variables for the slave optimization, that have to be set by the Master
"""
from __future__ import division
import numpy as np

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"



class SlaveData(object):
    def __init__(self):            
        
        # Name the file which should be loaded:
        self.configKey = ""
        self.NETWORK_DATA_FILE = ""
        self.nBuildingsConnected = 0
        self.fNameTotalCSV = ""

        
        #self.Network_Supply_Temp = 70 + 273.0
        
        # Electricity_Type:
        self.EL_TYPE = 'normal' # type normal or green (=green power) 
        
        
        # Geothermal Heat Pump, 
        #self.GHP_max_i = gV.GHP_Cmax_Size_th # [W] Heat power (thermal output)
        self.GHP_number = 0.0 # number of probes
        #self.GHP_max = self.GHP_number * self.GHP_max_i
        self.GHP_SEASON_ON = 0 # Hour in Year, when to switch on GHP
        self.GHP_SEASON_OFF = 8760 # Hour in Year, when to switch off GHP
        
        # Sewage Heat Pump
        self.HPSew_maxSize = 0
        
        # Lake Heat Pump
        self.HPLake_maxSize = 0
        
        # Furnace
        self.Furnace_Q_max = 0
        self.Furn_Moist_type = "wet" #gV.Furn_Moist_type # set the moisture content of wood chips, either "dry" or "wet"
        
        # GAS TURBINE VARIABLES
        #self.gt_size = 1.0E6 # in Watt
        self.CC_GT_SIZE = 0
        self.gt_fuel = "NG"
        
        
        # Boiler - Thermal output power!

        # add BG / NG Story for both peak and normal boilers
        self.Boiler_Q_max = 0
        self.BoilerPeak_Q_max = 0
        self.BoilerType = "NG"         #Choose "NG" or "BG" 
        self.BoilerPeakType = "NG"     #Choose "NG" or "BG" 
        self.BoilerBackupType = "NG"   #Choose "NG" or "BG" 
 
        # Cooling Tower :
        #self.CT_Qdesign = 0
        
        # Storage
        self.STORAGE_SIZE = 1000000.0 # in m^3 - size of hot water storage tank (up to now a random variable)
        self.STORAGE_HEIGHT = 3.0  # in m - height of hot water storage tank
        self.A_storage_outside = self.STORAGE_SIZE/self.STORAGE_HEIGHT + 2 * np.pi * \
                        (self.STORAGE_SIZE/self.STORAGE_HEIGHT / np.pi)**0.5 #neglecting ground area for heat losses
        self.alpha_loss = 0.0111 # EnergyPRO: 0.3 * 0.037 ; \
                                    # Saplamidis: 0.293542 # Wh / h= 0( .005 / (math.log10(26/25.0) ) , 
                                    # from Vassilis-Storage Optimization Code ** ACHTUNG !! CHANGE - SCALES WITH SIZE (?!)
        self.Storage_conv_loss = 0.0111 # losses due to energy conversion from and to storage
        self.T_storage_initial = 10 + 273.0 # initial Storage Temperature
        self.T_storage_zero = 10 + 273.0 # Reference Temperature Storage
        self.Q_in_storage_zero = self.STORAGE_SIZE *  1/ 3600 * 983.21 * 4185 * (self.T_storage_zero - self.T_storage_initial)
        self.dT_buffer = 5 # maintain a buffer for "uncertainties", never go below this temperature 
        # Storage is initially empty
        
        self.T_ST_MAX = 90 + 273.0 # Maximum Temperature of storage allowed
        self.T_ST_MIN = 10 + 273.0
        
        # Solar
        self.SOLCOL_TYPE_PVT     = "PVT_total.csv" # file used as PVT type of collectors
        self.SOLCOL_TYPE_SC      = "SC_total.csv"
        self.SOLCOL_TYPE_PV      = "PV_total.csv"
        self.SOLAR_PART_PVT      = 0.0  # [%] How much of the total area is available for PVT
        self.SOLAR_PART_SC       = 0.0  # How much of the total area is available for Solar Collectors
        self.SOLAR_PART_PV       = 0.0  # How much of the total area is available for PV (no thermal output, selling electricity)
        self.nPVT_installations  = 2    # number of PVT installations, required for PVT average size, which goes into KEV remuneration
        self.nPV_installations   = 2    # number of PVT installations, required for PVT average size, which goes into KEV remuneration
        
        # declare, which power plants will be used : USED = 1  ; NOT USED = 0 
        self.Boiler_on = 0
        self.BoilerPeak_on = 0
        self.Furnace_on = 0
        self.GHP_on = 0
        self.HP_Lake_on = 0
        self.HP_Sew_on = 0
        self.CC_on = 0
        self.WasteServersHeatRecovery = 0 # server heat
        self.WasteCompressorHeatRecovery = 0

        

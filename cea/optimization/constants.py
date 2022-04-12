# -*- coding: utf-8 -*-
"""
This file contains the constants used in objective function calculation in optimization
"""




__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# Length of entries of an individual and the name of every entry
# this is the first part of the individual and only considers technologies
# in the optimization algorithm we add more entries to specify network connections to buildings.
DH_CONVERSION_TECHNOLOGIES_WITH_SPACE_RESTRICTIONS = ["PVT", "SC_ET", "SC_FP", "PV"]
DH_CONVERSION_TECHNOLOGIES_WITH_SIZE_AGGREAGTION_NEEDED = ["NG_Cogen", "WB_Cogen", "DB_Cogen", "NG_BaseBoiler",
                                                           "NG_PeakBoiler", "WS_HP", "SS_HP", "GS_HP", "DS_HP"]
DC_CONVERSION_TECHNOLOGIES_WITH_SPACE_RESTRICTIONS = []

DH_CONVERSION_TECHNOLOGIES_SHARE = {"NG_Cogen": {"minimum": 0.2},
                                    "WB_Cogen": {"minimum": 0.2},
                                    "DB_Cogen": {"minimum": 0.2},
                                    "NG_BaseBoiler": {"minimum": 0.1},
                                    "NG_PeakBoiler": {"minimum": 0.1},
                                    "WS_HP": {"minimum": 0.1},
                                    "SS_HP": {"minimum": 0.1},
                                    "GS_HP": {"minimum": 0.1},
                                    "DS_HP": {"minimum": 0.1},
                                    "PVT": {"minimum": 0.05},
                                    "SC_ET": {"minimum": 0.05},
                                    "SC_FP": {"minimum": 0.05},
                                    "PV": {"minimum": 0.05}
                                    }

DC_CONVERSION_TECHNOLOGIES_SHARE = {"NG_Trigen": {"minimum": 0.2},
                                    "WS_BaseVCC": {"minimum": 0.1},
                                    "WS_PeakVCC": {"minimum": 0.1},
                                    "AS_BaseVCC": {"minimum": 0.1},
                                    "AS_PeakVCC": {"minimum": 0.1},
                                    "Storage": {"minimum": 0.2},
                                    "PV": {"minimum": 0.05}
                                    }
DC_TECHNOLOGIES_SHARING_SPACE = []

DH_ACRONYM = "DH"
DC_ACRONYM = "DC"

# Losses and margins
DC_NETWORK_LOSS = 0.05  # Cooling ntw losses (10% --> 0.1)
DH_NETWORK_LOSS = 0.12  # Heating ntw losses
Q_MARGIN_FOR_NETWORK = 0.01  # Reliability margin for the system nominal capacity in the hub
Q_LOSS_DISCONNECTED = 0.05  # Heat losses within a disconnected building
Q_MIN_SHARE = 0.1  # Minimum percentage for the installed capacity
STORAGE_COOLING_SHARE_RESTRICTION = 0.3  # Maximum percentage of the nominal cooling load that is allowed
K_DH = 0.25  # linear heat loss coefficient district heating network twin pipes groundfoss
# Svendsen (2012) "Energy and exergy analysis of low temperature district heating network")

# pipes location properties
Z0 = 1.5  # location of pipe underground in m
PSL = 1600  # heat capacity of ground in kg/m3 => should be density?
CSL = 1300  # heat capacity of ground in J/kg K
BSL = 1.5  # thermal conductivity of ground in W/m.K

# Heat Exchangers
U_COOL = 2500.0  # W/m2K
U_HEAT = 2500.0  # W/m2K
DT_HEAT = 5.0  # K - pinch delta at design conditions
DT_COOL = 2.0  # K - pinch delta at design conditions

# Heat pump
HP_MAX_SIZE = 20.0E6  # max thermal design size [Wth]
HP_MIN_SIZE = 1.0E6  # min thermal design size [Wth]
HP_ETA_EX = 0.6  # exergetic efficiency of WSHP [L. Girardin et al., 2010]_
HP_ETA_EX_COOL = 0.3  # https://www.sciencedirect.com/science/article/pii/S1164023502000833
HP_DELTA_T_COND = 2.0  # pinch for condenser [K]
HP_DELTA_T_EVAP = 2.0  # pinch for evaporator [K]
HP_MAX_T_COND = 140 + 273.0  # max temperature at condenser [K]
HP_AUXRATIO = 0.83  # Wdot_comp / Wdot_total (circulating pumps)
HP_COP_MAX = 8.5  # maximum achieved by 3for2 21.05.18
HP_COP_MIN = 2.7  # COP of typical air-to-air unit

# Solar area to Wpeak
ETA_AREA_TO_PEAK = 0.16  # Peak Capacity - Efficiency, how much kW per area there are, valid for PV and PVT (after Jimeno's J+)

# Pressure losses
# DeltaP_DCN = 1.0 #Pa - change
# DeltaP_DHN = 84.8E3 / 10.0 #Pa  - change

PUMP_ENERGY_SHARE = 0.01  # assume 1% of energy required for pumping, after 4DH
PUMP_RELIABILITY_MARGIN = 0.05  # assume 5% reliability margin

# Circulating Pump
PUMP_ETA = 0.8

# Sewage resource

SEW_MIN_T = 10 + 273.0  # minimum temperature at the sewage exit [K]

# Lake resources
DELTA_U = (12500.0E6)  # [Wh], maximum change in the lake energy content at the end of the year (positive or negative)
T_LAKE = 5 + 273.0  # K

COP_SCALING_FACTOR_GROUND_WATER = 3.4 / 3.9  # Scaling factor according to EcoBau, take GroundWater Heat pump into account

GHP_CMAX_SIZE = 2E3  # max cooling design size [Wc] FOR ONE PROBE
GHP_CMAX_SIZE_TH = 2E3  # Wh/m per probe
GHP_CMAX_LENGTH = 40  # depth of exploration taken into account

GHP_HMAX_SIZE = 2E3  # max heating design size [Wth] FOR ONE PROBE
GHP_WMAX_SIZE = 1E3  # max electrical design size [Wel] FOR ONE PROBE

GHP_ETA_EX = 0.677  # exergetic efficiency [O. Ozgener et al., 2005]_
GHP_AUXRATIO = 0.83  # Wdot_comp / Wdot_total (circulating pumps)

GHP_A = 25  # [m^2] area occupancy of one borehole Gultekin et al. 5 m separation at a penalty of 10% less efficeincy

# Combined cycle

GT_MAX_SIZE = 50.00000001E6  # max electrical design size in W = 50MW (NOT THERMAL capacity)
GT_MIN_SIZE = 0.2E6  # min electrical design size in W = 0.2 MW (NOT THERMAL capacity)
GT_MIN_PART_LOAD = 0.1 * 0.999  # min load (part load regime)

CC_EXIT_T_NG = 986.0  # exit temperature of the gas turbine if NG
CC_EXIT_T_BG = 1053.0  # exit temperature of the gas turbine if BG
CC_AIRRATIO = 2.0  # air to fuel mass ratio

ST_DELTA_T = 4.0  # pinch for HRSG
ST_DELTA_P = 5.0E5  # pressure loss between steam turbine and DHN
CC_DELTA_T_DH = 5.0  # pinch for condenser

ST_GEN_ETA = 0.9  # generator efficiency after steam turbine

BIOGAS_FROM_AGRICULTURE_FLAG = False  # True = Biogas from Agriculture, False = Biogas normal
HP_SEW_ALLOWED = True
HP_LAKE_ALLOWED = True
DATACENTER_HEAT_RECOVERY_ALLOWED = True
HYBRID_HEATING_COOLING_ALLOWED = False  # False the configuration of decentralized buildings with hybrid technologies is not enabled.
GHP_ALLOWED = True
CC_ALLOWED = True
FURNACE_ALLOWED = True
DISC_GHP_FLAG = True  # Is geothermal allowed in disconnected buildings? False = NO ; True = YES
DISC_BIOGAS_FLAG = False  # True = use Biogas only in Disconnected Buildings, no Natural Gas; False = both possible
LAKE_COOLING_ALLOWED = True
VCC_ALLOWED = True
ABSORPTION_CHILLER_ALLOWED = True
STORAGE_COOLING_ALLOWED = True

# Vapor compressor chiller
VCC_T_COOL_IN = 30 + 273.0  # entering condenser water temperature [K]
VCC_MIN_LOAD = 0.1  # min load for cooling power
VCC_CODE_CENTRALIZED = 'CH1'
VCC_CODE_DECENTRALIZED = 'CH3'

# Absorption chiller
ACH_T_IN_FROM_CHP_K = 150.0 + 273.0  # hot water from CHP to the generator of ACH
ACH_TYPE_SINGLE = 'single'  # single effect absorption chiller
ACH_TYPE_DOUBLE = 'double'  # double effect absorption chiller

T_GENERATOR_FROM_FP_C = 75  # fixme: this number is set corresponding to the flat plate solar thermal collector operation
T_GENERATOR_FROM_ET_C = 100  # fixme: this number is set corresponding to the evacuated tube solar thermal collector operation

## Thermal Energy Storage
# Fully mixed cold water tank
T_TANK_FULLY_CHARGED_K = 4 + 273.0
T_TANK_FULLY_DISCHARGED_K = 14 + 273.0

# Seasonal Storage
STORAGE_MAX_UPTAKE_LIMIT_FLAG = 1  # set a maximum for the HP Power for storage charging / discharging

# Server Waste Heat recovery
ETA_SERVER_TO_HEAT = 0.8  # [-]
T_FROM_SERVER = 60 + 273.0  # K
T_TO_SERVER = 55 + 273.0  # K

# solar PV and PVT
N_PV = 0.16
N_PVT = 0.16
N_SC_FP = 0.775
N_SC_ET = 0.721

# Low heating values
LHV_NG = 45.4E6  # [J/kg]
LHV_BG = 21.4E6  # [J/kg]
ZERO_DEGREES_CELSIUS_IN_KELVIN = 273.0  # Use this value, where the default temperature is assigned as 0 degree C

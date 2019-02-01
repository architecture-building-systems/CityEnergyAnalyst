# -*- coding: utf-8 -*-
"""
This file contains the constants used in objective function calculation in optimization
"""
from __future__ import absolute_import
__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# Losses and margins
DC_NETWORK_LOSS = 0.05  # Cooling ntw losses (10% --> 0.1)
DH_NETWORK_LOSS = 0.12  # Heating ntw losses
Q_MARGIN_FOR_NETWORK = 0.01  # Reliability margin for the system nominal capacity in the hub
Q_LOSS_DISCONNECTED = 0.05  # Heat losses within a disconnected building
SIZING_MARGIN = 0.20  # Reliability margin for the system nominal capacity
Q_MIN_SHARE = 0.0  # Minimum percentage for the installed capacity
STORAGE_COOLING_SHARE_RESTRICTION = 0.3 # Maximum percentage of the nominal cooling load that is allowed
K_DH = 0.25  # linear heat loss coefficient district heting network twin pipes groundfoss
# Svendsen (2012) "Energy and exergy analysis of low temperature district heating network")

# pipes location properties
Z0 = 1.5  # location of pipe underground in m
PSL = 1600  # heat capacity of ground in kg/m3 => should be density?
CSL = 1300  # heat capacity of ground in J/kg K
BSL = 1.5  # thermal conductivity of ground in W/m.K

# Heat Exchangers
U_COOL = 2500.0  # W/m2K
U_HEAT = 2500.0  # W/m2K
DT_HEAT = 5.0    # K - pinch delta at design conditions
DT_COOL = 2.0    # K - pinch delta at design conditions

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

# Boiler
# Operating figures, quality parameters and investment costs for district heating systems (AFO)

# ELCO-Loesungsbeispiel-Huber.pdf

BOILER_C_FUEL = 20.0  # € / MWh_therm_bought(for LHV), AFO
BOILER_P_AUX = 0.026  # 0.026 Wh/Wh_th_sold = 26 kWh_el / MWh_th_sold, bioenergy 2020
BOILER_MIN = 0.05  # minimum Part Load of Boiler
BOILER_EQU_RATIO = 0.2  # 20% own capital required (equity ratio)
BOILER_ETA_HP = 0.9

# Furnace
FURNACE_FUEL_COST_WET = 0.057 * 1E-3  # CHF / Wh = 5.7 Rp / kWh for wet (50wt%) Wood Chips, after
FURNACE_FUEL_COST_DRY = 0.07 * 1E-3  # CHF / Wh = 7 Rp / kWh for dry (30wt%) Wood Chips,
FURNACE_MIN_LOAD = 0.2  # Minimum load possible (does not affect Model itself!)
FURNACE_MIN_ELECTRIC = 0.3  # Minimum load for electricity generation in furnace plant

BIOGAS_FROM_AGRICULTURE_FLAG = False  # True = Biogas from Agriculture, False = Biogas normal
HP_SEW_ALLOWED = True
HP_LAKE_ALLOWED = True
GHP_ALLOWED = True
CC_ALLOWED = True
FURNACE_ALLOWED = False
DISC_GHP_FLAG = True  # Is geothermal allowed in disconnected buildings? False = NO ; True = YES
DISC_BIOGAS_FLAG = False  # True = use Biogas only in Disconnected Buildings, no Natural Gas; False = both possible

LAKE_COOLING_ALLOWED = True
VCC_ALLOWED = True
ABSORPTION_CHILLER_ALLOWED = True
STORAGE_COOLING_ALLOWED = True


# Vapor compressor chiller
VCC_T_COOL_IN = 30 + 273.0  # entering condenser water temperature [K]
VCC_MIN_LOAD = 0.1  # min load for cooling power

# Absorption chiller
ACH_T_IN_FROM_CHP = 150 + 273.0 # hot water from CHP to the generator of ACH
ACH_TYPE_SINGLE = 'single' # single effect absorption chiller
ACH_TYPE_DOUBLE = 'double' # double effect absorption chiller

T_GENERATOR_FROM_FP_C = 75 # fixme: this number is set corresponding to the flat plate solar thermal collector operation
T_GENERATOR_FROM_ET_C = 100 # fixme: this number is set corresponding to the evacuated tube solar thermal collector operation

# Cooling tower
CT_MAX_SIZE = 10.0E6  # cooling power design size [W]

## Thermal Energy Storage
# Fully mixed cold water tank
T_TANK_FULLY_CHARGED_K = 4 + 273.0
T_TANK_FULLY_DISCHARGED_K = 14 + 273.0
DT_CHARGING_BUFFER = 0.5
TANK_SIZE_MULTIPLIER = 5  # TODO [issue]: assumption, need more research on tank sizing
PEAK_LOAD_RATIO = 0.6  # TODO: assumption, threshold to discharge storage

# Seasonal Storage
T_STORAGE_MIN = 10 + 273.0  # K  - Minimum Storage Temperature
STORAGE_MAX_UPTAKE_LIMIT_FLAG = 1  # set a maximum for the HP Power for storage charging / discharging
Q_TO_STORAGE_MAX = 1e6  # 100kW maximum peak

# Activation Order of Power Plants
# solar sources are treated first
ACT_FIRST = 'HP'  # accounts for all kind of HP's as only one will be in the system.
ACT_SECOND = 'CHP'  # accounts for ORC and NG-RC (produce electricity!)
ACT_THIRD = 'BoilerBase'  # all conventional boilers are considered to be backups.
ACT_FOURTH = 'BoilerPeak'  # additional Peak Boiler

# Data for Evolutionary algorithm
N_COOL = 4  # number of cooling technologies
N_HEAT = 6  # number of heating
N_HR = 2  # number of heat recovery options
N_SOLAR = 4  # number of solar technologies PV, PVT, SC_ET, SC_FP

INDICES_CORRESPONDING_TO_DHN = 2 # one index for temperature and one for the number of AHU/ARU/SHU the DHN is supplying
DHN_temperature_lower_bound = 30 # Lower bound of the temperature that can be supplied by DHN
DHN_temperature_upper_bound = 120 # Upper bound of the temperature that can be supplied by DHN
INDICES_CORRESPONDING_TO_DCN = 2 # one index for temperature and one for the number of AHU/ARU/SCU the DCN is supplying
DCN_temperature_lower_bound = 6 # Lower bound of the temperature that can be supplied by DCN
DCN_temperature_upper_bound = 18 # Upper bound of the temperature that can be supplied by DCN

#  variable corresponding to the consideration of DHN temperature in the optimization,
# if this is True, the temperature of the DHN is generated between the lower and upper bounds and considered as the
# operation temperature of the DHN. In this case, the excess temperature requirement is provided by installing
# decentralised units. If it is False, it calculates the DHN supply temperature based on the demand of the buildings
# connected in the network. The same goes for DCN temperature
DHN_temperature_considered = False
DCN_temperature_considered = False

PROBA = 0.5
SIGMAP = 0.2
EPS_MARGIN = 0.001

# Heat Recovery

# compressed Air recovery
ETA_EL_TO_HEAT = 0.75  # [-]
T_EL_TO_HEAT_SUP = 80 + 273.0  # K
T_EL_TO_HEAT_RE = 70 + 273.0  # K

# Server Waste Heat recovery
ETA_SERVER_TO_HEAT = 0.8  # [-]
T_FROM_SERVER = 60 + 273.0  # K
T_TO_SERVER = 55 + 273.0  # K

# Solar Thermal: information of return temperature
T_SUP_PVT_35 = 35 + 273.0  # K
T_SUP_SC_75 = 75 + 273.0  # K
T_SUP_SC_ET50 = 50 + 273.0  # K
T_SUP_SC_ET80 = 80 + 273.0  # K

# solar PV and PVT
N_PV = 0.16
N_PVT = 0.16
# ==============================================================================================================
# solar thermal collector # FIXME: redundant???
# ==============================================================================================================

T_IN = 75  # average temeperature
MODULE_LENGTH_SC = 2  # m # 1 for PV and 2 for solar collectors
MIN_PRODUCTION = 0.75  # points are selected with at least a minimum production of this % from the maximum in the area.
GRID_SIDE = 2  # in a rectangular grid of points, one side of the square. this cannot be changed if the solra potential was made with this.
ANGLE_NORTH = 122.5
TYPE_SC_PANEL = 1  # Flatplate collector

# ==============================================================================================================
# sewage potential
# ==============================================================================================================

SW_RATIO = 0.95  # ratio of waste water to fresh water production.
WIDTH_HEX = 0.40  # in m
VEL_FLOW = 3  # in m/s
MIN_FLOW = 9  # in lps
T_MIN = 8  # tmin of extraction
H0 = 1.5  # kW/m2K # heat trasnfer coefficient/
AT_HEX = 5
AT_MIN = 2

# Low heating values
LHV_NG = 45.4E6  # [J/kg]
LHV_BG = 21.4E6  # [J/kg]

# DCN
T_SUP_COOL = 6 + 273
T_RE_COOL_MAX = 12 + 273.0

# Values for the calculation of Delta P (from F. Muller network optimization code)
# WARNING : current = values for Inducity SQ
DELTA_P_COEFF = 104.81
DELTA_P_ORIGIN = 59016

PIPELIFETIME = 40.0  # years, Data from A&W
PIPEINTERESTRATE = 0.05  # 5% interest rate

SUBSTATION_N = 20  # Lifetime after A+W default 20

ZERO_DEGREES_CELSIUS_IN_KELVIN = 273.0  # Use this value, where the default temperature is assigned as 0 degree C
# -*- coding: utf-8 -*-
"""
This file contains the constants used in many folders in CEA. IF few constants are only used in a subfolder,
it is highly recommended to keep those constants in a separate file in the subfolder. This is to make sure we
declare the constants closest to the point of usage.
"""




__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# Shapefiles precision of decimals
SHAPEFILE_TOLERANCE = 6  # this is precision in millimeters
SNAP_TOLERANCE = 0.1  # this is precision in meters increase if having problems.

HEAT_CAPACITY_OF_WATER_VAPOR_JPERKGK = 1859  # specific heat capacity of water vapor in KJ/kgK
ASPECT_RATIO = 3.3  # tank height aspect ratio h/D -> H=(4*V*AR^2/pi)^(1/3); taken from com. tank geometry (jenni.ch)
LATENT_HEAT_OF_AIR_KJPERKG = 2257  # latent heat of air kJ/kg

# grey emissions
CONVERSION_AREA_TO_FLOOR_AREA_RATIO = 1.5  # conversion component's area to floor area
EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS_HEATING_GHG_kgm2 = 12 #kg COs/m2 gross floor area according to SIA 2032 anhang D (2021)
EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS_COOLING_GHG_kgm2 = 10 #kg COs/m2 gross floor area according to SIA 2032 anhang D (2021)
EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS_ELECTRICITY_GHG_kgm2 = 18.0 #kg COs/m2 gross floor area according to SIA 2032 anhang D (2021) average office and residential
EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS_WATER_GHG_kgm2 = 11.36 #kg COs/m2 gross floor area according to SIA 2032 anhang D (2021)
EMISSIONS_EMBODIED_EXCAVATIONS_GHG_kgm3 = 18 # average of excavation with and without grundwasser accroding to SIA 2032
EMISSIONS_EMBODIED_PV_GHG_kgm2 = 324.8 # average of PV according to SIA 2032
EMISSIONS_EMBODIED_SC_GHG_kgm2 = 155 # average of PV according to SIA 2032

# Date data
DAYS_IN_YEAR = 365
HOURS_IN_DAY = 24
HOURS_IN_YEAR = 8760
MONTHS_IN_YEAR = 12
HOURS_PRE_CONDITIONING = 720  # number of hours that the building will be thermally pre-conditioned,
                                # the results of these hours will be overwritten

# Specific heat
HEAT_CAPACITY_OF_WATER_JPERKGK = 4185  # [J/kg K]
DENSITY_OF_WATER_AT_60_DEGREES_KGPERM3 = 983.21  # [kg/m^3] density of Water @ 60°C
P_WATER_KGPERM3 = 998.0  # water density kg/m3
P_SEWAGEWATER_KGPERM3 = 1400  # sewagewater density kg/m3
WH_TO_J = 3600.0
J_TO_WH = 0.000277

# ==============================================================================================================
# sewage potential
# ==============================================================================================================

HEX_WIDTH_M = 0.40  # in m
AT_HEX_K = 5  # rule of thumb, Approach temperature of a heat exchanger
AT_MIN_K = 2  # rule of thumb, Minimum approach temperature of a heat exchanger
CT_MAX_SIZE_W = 10000000

# ??
VEL_FLOW_MPERS = 3  # in m/s got from Rabtherm technology
MIN_FLOW_LPERS = 9  # in lps got from Rabtherm technology
T_MIN = 8  # tmin of extraction got from Rabtherm technology
H0_KWPERM2K = 1.5  # kW/m2K # heat transfer coefficient/ got from Rabtherm technology

#ground temperature values
SOIL_Cp_JkgK = 2000 # _[A. Kecebas et al., 2011]
SOIL_lambda_WmK = 1.6
SOIL_rho_kgm3 = 1600

#insulation of pipes
PUR_lambda_WmK = 0.023
STEEL_lambda_WmK = 76

#unit conversion
FT_WATER_TO_PA = 2989.0669 # assumption at 4C water
M_WATER_TO_PA = 9804
FT_TO_M = 0.3048

# PHYSICAL CONSTANTS
# stefan-boltzmann constant
BOLTZMANN = 0.000000056697  # W/m2K4

# KELVIN TO DEGREE CELSIUS CONVERSION
KELVIN_OFFSET = 273.0

# ==============================================================================================================
# DATA MANAGEMENT
# ==============================================================================================================
# OSM building category converters
OSM_BUILDING_CATEGORIES = {
    'residential': 'MULTI_RES',
    'apartments': 'MULTI_RES',
    'dormitory': 'MULTI_RES',
    'terrace': 'MULTI_RES',
    'nursing_home': 'MULTI_RES',
    'social_facility': 'MULTI_RES',
    'house': 'SINGLE_RES',
    'bungalow': 'SINGLE_RES',
    'cabin': 'SINGLE_RES',
    'detached': 'SINGLE_RES',
    'farm': 'SINGLE_RES',
    'ger': 'SINGLE_RES',
    'houseboat': 'SINGLE_RES',
    'semidetached_house': 'SINGLE_RES',
    'static_caravan': 'SINGLE_RES',
    'hotel': 'HOTEL',
    'office': 'OFFICE',
    'civic': 'OFFICE',
    'commercial': 'OFFICE',
    'government': 'OFFICE',
    'bureau_de_change': 'OFFICE',
    'courthouse': 'OFFICE',
    'embassy': 'OFFICE',
    'post_office': 'OFFICE',
    'townhall': 'OFFICE',
    'industrial': 'INDUSTRIAL',
    'retail': 'RETAIL',
    'kiosk': 'RETAIL',
    'bank': 'RETAIL', 'pharmacy':
    'RETAIL', 'marketplace': 'RETAIL',
    'supermarket': 'FOODSTORE',
    'restaurant': 'RESTAURANT',
    'fast_food': 'RESTAURANT',
    'food_court': 'RESTAURANT',
    'bar': 'RESTAURANT',
    'biergarten': 'RESTAURANT',
    'cafe': 'RESTAURANT',
    'ice_cream': 'RESTAURANT',
    'pub': 'RESTAURANT',
    'hospital': 'HOSPITAL',
    'clinic': 'HOSPITAL',
    'dentist': 'HOSPITAL',
    'doctors': 'HOSPITAL',
    'veterinary': 'HOSPITAL',
    'school': 'SCHOOL',
    'kindergarten': 'SCHOOL',
    'childcare': 'SCHOOL',
    'driving_school': 'SCHOOL',
    'language_school': 'SCHOOL',
    'music_school': 'SCHOOL',
    'university': 'UNIVERSITY',
    'college': 'UNIVERSITY',
    'library': 'LIBRARY',
    'toy_library': 'LIBRARY',
    'gym': 'GYM',
    'sports_hall': 'GYM',
    'pavilion': 'GYM',
    'arts_centre': 'MUSEUM',
    'cinema': 'MUSEUM',
    'theatre': 'MUSEUM',
    'parking': 'PARKING',
    'carport': 'PARKING',
    'garage': 'PARKING',
    'garages': 'PARKING',
    'hangar': 'PARKING',
    'bicycle_parking': 'PARKING',
    'charging_station': 'PARKING',
    'motorcycle_parking': 'PARKING',
    'parking_entrance': 'PARKING',
    'parking_space': 'PARKING',
    'taxi': 'PARKING'}
    # most common OSM amenity and building categories according to wiki.openstreetmap.org converted to CEA building
    # use types the "yes" category is excluded so that the default CEA assumption is used instead

OTHER_OSM_CATEGORIES_UNCONDITIONED = ['warehouse', 'roof', 'transportation', 'train_station', 'hut', 'shed', 'service',
                                 'transformer_tower', 'water_tower', 'bridge', 'bus_station', 'ferry_terminal', 'fuel',
                                 'shelter']
    # other unheated use types that don't have a specific CEA use type will be assigned as 'PARKING'

# parameters for grid division used to accelerate OSM operations
GRID_SIZE_M = 500  # meters
EARTH_RADIUS_M = 6.3781e6  # meters

# ==============================================================================================================
# DEMAND
# ==============================================================================================================
# all values are refactored from legacy Globalvars unless stated otherwise

# DEFAULT BUILDING GEOMETRY
H_F = 3.0  # average height per floor in m
D = 20.0  # in mm the diameter of the pipe to calculate losses

# HVAC SYSTEMS & VENTILATION
ETA_REC = 0.75  # constant efficiency of Heat recovery
DELTA_P_DIM = 5.0  # (Pa) dimensioning differential pressure for multi-storey building shielded from wind,
                 # according to DIN 1946-6
P_FAN = 0.55  # specific fan consumption in W/m3/h

TEMPERATURE_ZONE_CONTROL_NIGHT_FLUSHING = 26  # (°C) night flushing only if temperature is higher than 26 # TODO review and make dynamic
DELTA_T_NIGHT_FLUSHING = 2  # (°C) night flushing only if outdoor temperature is two degrees lower than indoor according to SIA 382/1
SHIELDING_CLASS = 2  # according to ISO 16798-7, 0 = open terrain, 1 = partly shielded from wind,
        #  2 = fully shielded from wind
TER_CLASS = 2  # terrain class of surroundings according to ISO 16798-7: 0 = open, 1 = rural,  2 = urban
RHO_AIR_REF = 1.23  # (kg/m3) constant from Table 12 in DIN 16798-7
TEMP_EXT_REF = 283  # (K) constant from Table 12 in DIN 16798-7
COEFF_TURB = 0.01  # (m/s) constant from Table 12 in DIN 16798-7
COEFF_WIND = 0.001  # (1/(m/s)) constant from Table 12 in DIN 16798-7
COEFF_STACK = 0.0035  # ((m/s)/(mK)) constant from Table 12 in DIN 16798-7
COEFF_D_WINDOW = 0.67  # (-), B.1.2.1 from annex B in DIN 16798-7 [1]
COEFF_D_VENT = 0.6  # flow coefficient for ventilation openings, B.1.2.1 in [1]
DELTA_C_P = 0.75  # (-), option 2 in B.1.3.4 from annex B in DIN 16798-7 [1]
DELTA_P_LEA_REF = 50  # air tightness index of the building envelope at reference pressure (Pa), B.1.3.14 in DIN 16798-7
DELTA_P_VENT_REF = 50  # air tightness index of the building envelope at reference pressure (Pa)
                       # FIXME no default value specified in standard
N_LEA = 0.667    # volumetric flow rate exponential due for leakage calculation, B.1.3.15 in DIN 16798-7
N_VENT = 0.5  # volumetric flow rate exponential due for ventilation calculation, B.1.2.2 in DIN 16798-7

# pumps ?
# TODO: Document
DELTA_P_1 = 0.1  # delta of pressure
F_SR = 0.3  # factor for pressure calculation
HOURS_OP = 5  # assuming around 2000 hours of operation per year. It is charged to the electrical system from 11 am to 4 pm
EFFI = 0.6  # efficiency of pumps
MIN_HEIGHT_THAT_REQUIRES_PUMPING = 15 # m pumping required for buildings above 15 m

# WATER
FLOWTAP = 0.036  # in m3 == 12 l/min during 3 min every tap opening
TWW_SETPOINT = 60  # dhw tank set point temperature in C

# PHYSICAL
H_WE = 2466e3  # (J/kg) Latent heat of vaporization of water [section 6.3.6 in ISO 52016-1:2007]
C_A = 1006  # (J/(kg*K)) Specific heat of air at constant pressure [section 6.3.6 in ISO 52016-1:2007]
GR = 9.81  # m/s2 gravity
KG_PER_GRAM = 0.001
# constants in standards
P_ATM = 101325  # (Pa) atmospheric pressure [section 6.3.6 in ISO 52016-1:2017]
RHO_A = 1.204  # (kg/m3) density of air at 20°C and 0m height [section 6.3.6 in ISO 52016-1:2017]

# constants
DELTA_T = 3600  # (s/h)

# Time
HOURS_PER_SEC = 1 / 3600

# RC-MODEL
B_F = 0.7  # it calculates the coefficient of reduction in transmittance for surfaces in contact with the ground according to values of SIA 380/1
H_IS = 3.45  # heat transfer coefficient between air and the surfacein W/(m2K)
H_MS = 9.1  # heat transfer coefficient between nodes m and s in W/m2K
LAMBDA_AT = 4.5 # dimensionless ratio between the internal surfaces area and the floor area from ISO 13790 Eq. 9

# RC-MODEL TEMPERATURE BOUNDS
T_WARNING_LOW = -30.0
T_WARNING_HIGH = 50.0

# SUPPLY AND RETURN TEMPERATURES OF REFRIGERATION SYSTEM
T_C_REF_SUP_0 = 1  # (°C) refactored from refrigeration loads, without original source
T_C_REF_RE_0 = 5  # (°C) refactored from refrigeration loads, without original source

# SUPPLY AND RETURN TEMPERATURES OF DATA CENTER COOLING SYSTEM
T_C_DATA_RE_0 = 15  # (°C) refactored from data center loads, without original source
T_C_DATA_SUP_0 = 7  # (°C) refactored from data center loads, without original source

VARIABLE_CEA_SCHEDULE_RELATION = {'Occ_m2p': 'OCCUPANCY',
                                  'Qs_Wp': 'OCCUPANCY',
                                  'X_ghp': 'OCCUPANCY',
                                  'Ve_lsp': 'OCCUPANCY',
                                  'Ea_Wm2': 'APPLIANCES',
                                  'El_Wm2': 'LIGHTING',
                                  'Ed_Wm2': 'SERVERS',
                                  'Vww_ldp': 'WATER',
                                  'Vw_ldp': 'WATER',
                                  'Ths_set_C': 'HEATING',
                                  'Tcs_set_C': 'COOLING',
                                  'Qcre_Wm2': 'PROCESSES',
                                  'Qhpro_Wm2': 'PROCESSES',
                                  'Qcpro_Wm2': 'PROCESSES',
                                  'Epro_Wm2': 'PROCESSES',
                                  'Ev_kWveh': 'ELECTROMOBILITY',
                                  }

TEMPERATURE_VARIABLES = ['HEATING', 'COOLING']
PEOPLE_DEPENDENT_VARIABLES = ['OCCUPANCY', 'WATER']
AREA_DEPENDENT_VARIABLES = ['APPLIANCES', 'LIGHTING', 'PROCESSES', 'SERVERS']

# ==============================================================================================================
# OPTIMIZATION
# ==============================================================================================================

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
Q_MARGIN_FOR_NETWORK = 0.01  # Reliability margin for the system nominal capacity in the hub
Q_LOSS_DISCONNECTED = 0.05  # Heat losses within a disconnected building
K_DH = 0.25  # linear heat loss coefficient district heating network twin pipes groundfoss
# Svendsen (2012) "Energy and exergy analysis of low temperature district heating network")

# pipes location properties
Z0 = 1.5  # location of pipe underground in m
PSL = 1600  # heat capacity of ground in kg/m3 => should be density?
CSL = 1300  # heat capacity of ground in J/kg K
BSL = 1.5  # thermal conductivity of ground in W/m.K






# ==============================================================================================================
# TECHNOLOGIES
# ==============================================================================================================

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

GHP_A = 25  # [m^2] area occupancy of one borehole Gultekin et al. 5 m separation at a penalty of 10% less efficiency

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

# Direct expansion unit
DX_COP = 2.3  # [-]
PRICE_DX_PER_W = 1.6  # USD

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

# Heat Exchangers
DT_INTERNAL_HEX = 2.0           # K - minimum difference between cold side outflow and hot side inflow temperatures
HEAT_EX_EFFECTIVENESS = 0.9     # assume starting value for heat exchanger effectiveness (exergy)
MAX_NODE_FLOW = 22.0   # kg/s


# Substation data
ROUGHNESS = 0.02 / 1000  # roughness coefficient for heating network pipe in m (for a steel pipe, from Li &
NETWORK_DEPTH = 1  # m

# Initial Diameter guess
REDUCED_TIME_STEPS = 50 # number of time steps of maximum demand which are evaluated as an initial guess of the edge diameters
MAX_INITIAL_DIAMETER_ITERATIONS = 20 #number of initial guess iterations for pipe diameters

# Cogeneration (CCGT)
SPEC_VOLUME_STEAM = 0.0010  # m3/kg

# Storage tank
TANK_HEX_EFFECTIVENESS = 0.9 # assuming 90% effectiveness
# tank insulation heat transfer coefficient in W/m2-K, value taken from SIA 385
U_DHWTANK = 0.225

#Chiller
G_VALUE_CENTRALIZED = 0.47
G_VALUE_DECENTRALIZED = 0.4 # calculated from ESP4401_Part-2 Air conditioning system_AY2016_17.pdf assuming singapore wet bulb temp and 7.5degC at cold side
T_EVAP_AHU = 280.5 #K form CEA demand calculation
T_EVAP_ARU = 280.5 #K form CEA demand calculation
T_EVAP_SCU = 291 #K form CEA demand calculation
DT_NETWORK_CENTRALIZED = 2 # Assumption for network losses. This value is based on a sample calculation with all loads supplied by the network.
CHILLER_DELTA_T_APPROACH = 2.8 # K , ESP4401_Part-2 Air conditioning system_AY2016_17.pdf
CHILLER_DELTA_T_HEX_CT = 1.5 # K , Approximation,  approach temperature of the HEX b/t the condenser loop and CT
CENTRALIZED_AUX_PERCENTAGE = 38 # % , Power needed by auxiliary Chiller and CT, calculation based on UTown plant
DECENTRALIZED_AUX_PERCENTAGE = 27 # % , Power needed by auxiliary Chiller and CT, backwards calculation based on Clark D (CUNDALL). Chiller energy efficiency 2013.

COMPRESSOR_TYPE_LIMIT_LOW = 1055056  # in W, according to ASHRAE 90.1 Appendix G. below this limit (300 RT), one water-cooled screw chiller should be implemented
COMPRESSOR_TYPE_LIMIT_HIGH = 2110112  # in W, according to ASHRAE 90.1 Appendix G. below this limit (600 RT), two water-cooled screw chiller should be implemented, while above 2 centrifugal water source chllers hall be implemented, not larger then 800 RT (2813 kW)
ASHRAE_CAPACITY_LIMIT = 2813482 # in W, according to ASHRAE 90.1 Appendix G, chiller shall notbe larger than 800 RT

# Cooling Towers
CT_MIN_PARTLOAD_RATIO = 0.15 # from Grahovac, M. et al. (2012). VC CHILLERS AND PV PANELS: A GENERIC PLANNING TOOL PROVIDING THE OPTIMAL DIMENSIONS TO MINIMIZE COSTS OR EMISSIONS.


#Furnace
FURNACE_MIN_LOAD = 0.2  # Minimum load possible (does not affect Model itself!)
FURNACE_MIN_ELECTRIC = 0.3  # Minimum load for electricity generation in furnace plant
FURNACE_FUEL_COST_WET = 0.057 * 1E-3  # CHF / Wh = 5.7 Rp / kWh for wet (50wt%) Wood Chips, after
FURNACE_FUEL_COST_DRY = 0.07 * 1E-3  # CHF / Wh = 7 Rp / kWh for dry (30wt%) Wood Chips,

# Boiler
# Operating figures, quality parameters and investment costs for district heating systems (AFO)

# ELCO-Loesungsbeispiel-Huber.pdf
BOILER_C_FUEL = 20.0  # eu / MWh_therm_bought(for LHV), AFO
BOILER_P_AUX = 0.026  # 0.026 Wh/Wh_th_sold = 26 kWh_el / MWh_th_sold, bioenergy 2020
BOILER_MIN = 0.05  # minimum Part Load of Boiler
BOILER_EQU_RATIO = 0.2  # 20% own capital required (equity ratio)
BOILER_ETA_HP = 0.9
BOILER_ETA_HP = 0.9

#natural gas connection
GAS_CONNECTION_COST = 15.5 / 1000  # CHF / W, from  Energie360 15.5 CHF / kW

# Thermal Network# Pipe material default
PIPE_DIAMETER_DEFAULT = 150
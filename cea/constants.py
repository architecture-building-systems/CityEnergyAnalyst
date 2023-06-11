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
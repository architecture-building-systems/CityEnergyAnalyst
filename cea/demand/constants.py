# -*- coding: utf-8 -*-
"""
This file contains the constants used in the building energy demand calculations
"""



__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


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

VARIABLE_CEA_SCHEDULE_RELATION = {'Occ_m2p': 'occupancy',
                                  'Qs_Wp': 'occupancy',
                                  'X_ghp': 'occupancy',
                                  'Ve_lsp': 'occupancy',
                                  'Ea_Wm2': 'appliances',
                                  'El_Wm2': 'lighting',
                                  'Ed_Wm2': 'servers',
                                  'Vww_ldp': 'hot_water',
                                  'Vw_ldp': 'hot_water',
                                  'Ths_set_C': 'heating',
                                  'Tcs_set_C': 'cooling',
                                  'Qcre_Wm2': 'processes',
                                  'Qhpro_Wm2': 'processes',
                                  'Qcpro_Wm2': 'processes',
                                  'Epro_Wm2': 'processes',
                                  'Ev_kWveh': 'electromobility',
                                  }

TEMPERATURE_VARIABLES = ['heating', 'cooling']
PEOPLE_DEPENDENT_VARIABLES = ['occupancy', 'hot_water']
AREA_DEPENDENT_VARIABLES = ['appliances', 'lighting', 'processes', 'servers']

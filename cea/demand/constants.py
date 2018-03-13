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
H_F = 3  # average height per floor in m
E_S = 0.9  # franction of GFA that has electricity in every building
D = 20  # in mm the diameter of the pipe to calculate losses

# SOLAR
RSE = 0.04  # thermal resistance of external surfaces according to ISO 6946
F_F = 0.2  # Frame area faction coefficient

# HVAC SYSTEMS & VENTILATION
ETA_REC = 0.75  # constant efficiency of Heat recovery
DELTA_P_DIM = 5  # (Pa) dimensioning differential pressure for multi-storey building shielded from wind,
                 # according to DIN 1946-6
SHIELDING_CLASS = 2  # according to ISO 16798-7, 0 = open terrain, 1 = partly shielded from wind,
        #  2 = fully shielded from wind
P_FAN = 0.55  # specific fan consumption in W/m3/h

# pumps ?
# TODO: Document
DELTA_P_1 = 0.1  # delta of pressure
F_SR = 0.3  # factor for pressure calculation
HOURS_OP = 5  # assuming around 2000 hours of operation per year. It is charged to the electrical system from 11 am to 4 pm
GR = 9.81  # m/s2 gravity
EFFI = 0.6  # efficiency of pumps

# WATER
P_WATER = 998.0  # water density kg/m3
FLOWTAP = 0.036  # in m3 == 12 l/min during 3 min every tap opening
C_P_W = 4.184  # heat capacity of water in kJ/kgK
TWW_SETPOINT = 60  # dhw tank set point temperature in C



# PHYSICAL
H_WE = 2466e3  # (J/kg) Latent heat of vaporization of water [section 6.3.6 in ISO 52016-1:2007]
C_A = 1006  # (J/(kg*K)) Specific heat of air at constant pressure [section 6.3.6 in ISO 52016-1:2007]

C_P_A = 1.008  # specific heat capacity of air in KJ/kgK

# RC-MODEL
B_F = 0.7  # it calculates the coefficient of reduction in transmittance for surfaces in contact with the ground according to values of SIA 380/1
H_IS = 3.45  # heat transfer coefficient between air and the surfacein W/(m2K)
H_MS = 9.1  # heat transfer coefficient between nodes m and s in W/m2K
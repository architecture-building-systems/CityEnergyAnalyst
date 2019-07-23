# -*- coding: utf-8 -*-
"""
This file contains the constants used in many folders in CEA. IF few constants are only used in a subfolder,
it is highly recommended to keep those constants in a separate file in the subfolder. This is to make sure we
declare the constants closest to the point of usage.
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

HEAT_CAPACITY_OF_WATER_VAPOR_JPERKGK = 1859  # specific heat capacity of water vapor in KJ/kgK
ASPECT_RATIO = 3.3  # tank height aspect ratio, H=(4*V*AR^2/pi)^(1/3), taken from commercial tank geometry (jenni.ch)
LATENT_HEAT_OF_AIR_KJPERKG = 2257  # latent heat of air kJ/kg

# grey emissions
CONVERSION_AREA_TO_FLOOR_AREA_RATIO = 1.5  # conversion component's area to floor area
SERVICE_LIFE_OF_BUILDINGS = 60  # service life of standard building components and materials SIA2032
SERVICE_LIFE_OF_TECHNICAL_SYSTEMS = 25  # service life of technical installations Average of SIA2032 (20 - 40)

# Date data
DAYS_IN_YEAR = 365
HOURS_IN_DAY = 24
HOURS_IN_YEAR = 8760

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
H0_KWPERM2K = 1.5  # kW/m2K # heat trasnfer coefficient/ got from Rabtherm technology

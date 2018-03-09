# -*- coding: utf-8 -*-
"""
This file contains the constants used in many folders in CEA. IF few constants are only used in a subfolder,
it is highly recommended to keep those constants in a separate file in the subfolder. This is make sure we
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

HEAT_CAPACITY_OF_WATER_VAPOR = 1.859  # specific heat capacity of water vapor in KJ/kgK
ASPECT_RATIO = 3.3  # tank height aspect ratio, H=(4*V*AR^2/pi)^(1/3), taken from commercial tank geometry (jenni.ch)
LATENT_HEAT_OF_AIR = 2257  # latent heat of air kJ/kg

# grey emissions
CONVERSION_AREA_TO_FLOOR_AREA_RATIO = 1.5  # conversion component's area to floor area
SERVICE_LIFE_OF_BUILDINGS = 60  # service life of standard building components and materials
SERVICE_LIFE_OF_TECHNICAL_SYSTEMS = 40  # service life of technical installations

# Date data
DAYS_IN_YEAR = 365
HOURS_IN_DAY = 24

# Specific heat
HEAT_CAPACITY_OF_WATER = 4185  # [J/kg K]
DENSITY_OF_WATER = 983.21  # [kg/m^3] density of Water @ 60°C
WH_TO_J = 3600.0

# ==============================================================================================================
# sewage potential
# ==============================================================================================================

width_HEX = 0.40  # in m
Vel_flow = 3  # in m/s got from Rabtherm technology
min_flow = 9  # in lps got from Rabtherm technology
tmin = 8  # tmin of extraction got from Rabtherm technology
h0 = 1.5  # kW/m2K # heat trasnfer coefficient/ got from Rabtherm technology
AT_HEX = 5  # rule of thumb
ATmin = 2  # rule of thumb
CT_maxSize = 10000000

# -*- coding: utf-8 -*-
"""
This file contains the constants used in many folders in CEA. IF few constants are only used in a subfolder,
it is highly recommended to keep those constants in a separate file in the subfolder. This is to make sure we
declare the constants closest to the point of usage.
"""




__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# Shapefile precision constants
SHAPEFILE_TOLERANCE = 6
"""Shapefile coordinate precision in decimal places for normalization."""

SNAP_TOLERANCE = 0.1
"""Snap precision in meters."""

# Thermodynamic properties
HEAT_CAPACITY_OF_WATER_VAPOR_JPERKGK = 1859
"""Specific heat capacity of water vapor in J/(kg·K)."""

ASPECT_RATIO = 3.3
"""Tank height aspect ratio h/D -> H=(4*V*AR^2/pi)^(1/3). Taken from commercial tank geometry (jenni.ch)."""

LATENT_HEAT_OF_AIR_KJPERKG = 2257
"""Latent heat of air in kJ/kg."""

# Grey emissions
CONVERSION_AREA_TO_FLOOR_AREA_RATIO = 1.5
"""Conversion ratio from component's area to floor area."""

SERVICE_LIFE_OF_BUILDINGS = 60
"""Service life of standard building components and materials in years (SIA2032)."""

SERVICE_LIFE_OF_TECHNICAL_SYSTEMS = 25
"""Service life of technical installations in years. Average of SIA2032 (20-40 years)."""

EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS = 35
"""Embodied emissions of technical systems in kg CO2/m² gross floor area."""

# Time constants
DAYS_IN_YEAR = 365
"""Number of days in a year."""

HOURS_IN_DAY = 24
"""Number of hours in a day."""

HOURS_IN_YEAR = 8760
"""Number of hours in a year (365 * 24)."""

MONTHS_IN_YEAR = 12
"""Number of months in a year."""

HOURS_PRE_CONDITIONING = 720
"""Number of hours that the building will be thermally pre-conditioned.
The results of these hours will be overwritten."""

# Water and energy properties
HEAT_CAPACITY_OF_WATER_JPERKGK = 4185
"""Specific heat capacity of water in J/(kg·K)."""

DENSITY_OF_WATER_AT_60_DEGREES_KGPERM3 = 983.21
"""Density of water at 60°C in kg/m³."""

P_WATER_KGPERM3 = 998.0
"""Water density at standard conditions in kg/m³."""

P_SEWAGEWATER_KGPERM3 = 1400
"""Sewage water density in kg/m³."""

WH_TO_J = 3600.0
"""Conversion factor from Wh to J."""

J_TO_WH = 0.000277
"""Conversion factor from J to Wh."""

# Sewage potential constants
HEX_WIDTH_M = 0.40
"""Heat exchanger width in meters."""

AT_HEX_K = 5
"""Approach temperature of a heat exchanger in K (rule of thumb)."""

AT_MIN_K = 2
"""Minimum approach temperature of a heat exchanger in K (rule of thumb)."""

CT_MAX_SIZE_W = 10000000
"""Maximum cooling tower size in W."""

# Rabtherm technology parameters
VEL_FLOW_MPERS = 3
"""Flow velocity in m/s (from Rabtherm technology)."""

MIN_FLOW_LPERS = 9
"""Minimum flow rate in L/s (from Rabtherm technology)."""

T_MIN = 8
"""Minimum extraction temperature in °C (from Rabtherm technology)."""

H0_KWPERM2K = 1.5
"""Heat transfer coefficient in kW/(m²·K) (from Rabtherm technology)."""

# Ground/soil properties
SOIL_Cp_JkgK = 2000
"""Soil specific heat capacity in J/(kg·K). Reference: A. Kecebas et al., 2011."""

SOIL_lambda_WmK = 1.6
"""Soil thermal conductivity in W/(m·K)."""

SOIL_rho_kgm3 = 1600
"""Soil density in kg/m³."""

# Pipe material properties
PUR_lambda_WmK = 0.023
"""Polyurethane (PUR) insulation thermal conductivity in W/(m·K)."""

STEEL_lambda_WmK = 76
"""Steel thermal conductivity in W/(m·K)."""

# Unit conversion factors
FT_WATER_TO_PA = 2989.0669
"""Conversion from feet of water to Pascals (assuming 4°C water)."""

M_WATER_TO_PA = 9804
"""Conversion from meters of water to Pascals."""

FT_TO_M = 0.3048
"""Conversion from feet to meters."""

# Physical constants
BOLTZMANN = 0.000000056697
"""Stefan-Boltzmann constant in W/(m²·K⁴)."""

KELVIN_OFFSET = 273.0
"""Kelvin to degree Celsius conversion offset."""

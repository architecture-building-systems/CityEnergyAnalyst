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


# Shapefiles precision of decimals

SHAPEFILE_TOLERANCE = 6  # this is precision in millimeters
SNAP_TOLERANCE = 0.1  # this is precision in meters increase if having problems.

HEAT_CAPACITY_OF_WATER_VAPOR_JPERKGK = 1859  # specific heat capacity of water vapor in KJ/kgK
ASPECT_RATIO = 3.3  # tank height aspect ratio h/D -> H=(4*V*AR^2/pi)^(1/3); taken from com. tank geometry (jenni.ch)
LATENT_HEAT_OF_AIR_KJPERKG = 2257  # latent heat of air kJ/kg

# grey emissions
CONVERSION_AREA_TO_FLOOR_AREA_RATIO = 1.5  # conversion component's area to floor area
SERVICE_LIFE_OF_BUILDINGS = 60  # service life of standard building components and materials SIA2032
SERVICE_LIFE_OF_TECHNICAL_SYSTEMS = 25  # service life of technical installations Average of SIA2032 (20 - 40)
EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS = 35 #kg COs/m2 gross floor area

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

# Temperature difference tolerances for numerical stability
# Used to avoid division by near-zero in heat transfer and mass flow calculations
MIN_TEMP_DIFF_FOR_MASS_FLOW_K = 0.001  # Minimum temperature difference for mass flow calculation [K or °C]
# Physical basis: Below 1 millikelvin, water flow becomes negligible and pump energy ≈ 0
# Used in: electrical_loads.py (pump auxiliary energy), substation.py (heat exchanger calculations)
# Note: Temperature differences in K and °C are equivalent (ΔT_K = ΔT_°C)

MIN_TEMP_DIFF_FOR_HEX_LMTD_K = 0.001  # Minimum temperature difference for LMTD calculation [K]
# Used in: substation.py calc_dTm_HEX() to avoid log(1) = 0 when dT1 ≈ dT2

# Thermodynamic limits for heat pump and chiller operation
MIN_TEMP_DIFF_FOR_HEAT_PUMP_OPERATION_K = 1.0  # Minimum temperature difference for heat pump/chiller operation [K]
# Physical basis: Below 1 K difference, thermodynamic cycle becomes impractical (COP → ∞ or COP → 0)
# Used in: chiller_vapor_compression.py, heatpumps.py - validates T_cond vs T_evap
# Typical operating range: 5-40 K for heat pumps, 20-40 K for chillers

# Convergence tolerances for iterative calculations
THERMAL_NETWORK_TEMPERATURE_CONVERGENCE_K = 1.0  # Convergence criterion for thermal network temperature iterations [K]
# Used in: thermal_network.py - iterative solver for network supply temperatures
# Network is considered converged when max node temperature difference < this value

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

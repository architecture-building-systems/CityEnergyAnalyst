"""
Constants used throughout the cea.technologies package.

History lesson: This is a first step at removing the `cea.globalvars.GlobalVariables` object.
"""

# Heat Exchangers
U_COOL = 2500.0  # W/m2K
U_HEAT = 2500.0  # W/m2K
DT_HEAT = 5.0    # K - pinch delta at design conditions
DT_COOL = 2.0    # K - pinch delta at design conditions

# Heat pump
HP_MAX_SIZE = 20.0E6  # max thermal design size [Wth]
HP_MIN_SIZE = 1.0E6  # min thermal design size [Wth]
HP_ETA_EX = 0.6  # exergetic efficiency of WSHP [L. Girardin et al., 2010]_
HP_DELTA_T_COND = 2.0  # pinch for condenser [K]
HP_DELTA_T_EVAP = 2.0  # pinch for evaporator [K]
HP_MAX_T_COND = 140 + 273.0  # max temperature at condenser [K]
HP_AUXRATIO = 0.83  # Wdot_comp / Wdot_total (circulating pumps)
# Substation data
ROUGHNESS = 0.02 / 1000  # roughness coefficient for heating network pipe in m (for a steel pipe, from Li &
NETWORK_DEPTH = 1  # m

# Initial Diameter guess
REDUCED_TIME_STEPS = 50 # number of time steps of maximum demand which are evaluated as an initial guess of the edge diameters
MAX_INITIAL_DIAMETER_ITERATIONS = 15 #number of initial guess iterations for pipe diameters

# Loop Network Diameter iterations
FULL_COOLING_SYSTEMS_LIST = ['cs_ahu', 'cs_aru', 'cs_scu', 'cs_data', 'cs_ref']
FULL_HEATING_SYSTEMS_LIST = ['hs_ahu', 'hs_aru', 'hs_shu', 'hs_ww']

# Cogeneration (CCGT)
SPEC_VOLUME_STEAM = 0.0010  # m3/kg

# Storage tank
TANK_HEX_EFFECTIVENESS = 0.9 # assuming 90% effectiveness

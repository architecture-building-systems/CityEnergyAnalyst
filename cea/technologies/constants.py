"""
Constants used throughout the cea.technologies package.

History lesson: This is a first step at removing the `cea.globalvars.GlobalVariables` object.
"""

# Heat Exchangers
U_COOL = 2500.0  # W/m2K
U_HEAT = 2500.0  # W/m2K
DT_HEAT = 5.0    # K - pinch delta at design conditions
DT_COOL = 2.0    # K - pinch delta at design conditions
DT_INTERNAL_HEX = 2.0           # K - minimum difference between cold side outflow and hot side inflow temperatures
HEAT_EX_EFFECTIVENESS = 0.9     # assume starting value for heat exchanger effectiveness (exergy)
MAX_NODE_FLOW = 22.0   # kg/s

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
MAX_INITIAL_DIAMETER_ITERATIONS = 20 #number of initial guess iterations for pipe diameters

# Cogeneration (CCGT)
SPEC_VOLUME_STEAM = 0.0010  # m3/kg

# Storage tank
TANK_HEX_EFFECTIVENESS = 0.9 # assuming 90% effectiveness

#Chiller
G_VALUE_CENTRALIZED = 0.47
G_VALUE_DECENTRALIZED = 0.4 # calculated from ESP4401_Part-2 Air conditioning system_AY2016_17.pdf assuming singapore wet bulb temp and 7.5degC at cold side
T_EVAP_AHU = 280.5 #K form CEA demand calculation
T_EVAP_ARU = 280.5 #K form CEA demand calculation
T_EVAP_SCU = 291 #K form CEA demand calculation
DT_NETWORK_CENTRALIZED = 2 # Assumption for network losses. This value is based on a sample calculation with all loads supplied by the newtork.
CHILLER_DELTA_T_APPROACH = 2.8 # K , ESP4401_Part-2 Air conditioning system_AY2016_17.pdf
CHILLER_DELTA_T_HEX_CT = 1.5 # K , Approximation,  approach temperature of the HEX b/t the condenser loop and CT
CENTRALIZED_AUX_PERCENTAGE = 38 # % , Power needed by auxiliary Chiller and CT, calculation based on UTown plant
DECENTRALIZED_AUX_PERCENTAGE = 27 # % , Power needed by auxiliary Chiller and CT, backwards calulation based on Clark D (CUNDALL). Chiller energy efficiency 2013.


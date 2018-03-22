"""
Constants used throughout the cea.technologies package.

History lesson: This is a first step at removing the `cea.globalvars.GlobalVariables` object.
"""

# Heat Exchangers
U_cool = 2500.0  # W/m2K
U_heat = 2500.0  # W/m2K
dT_heat = 5.0    # K - pinch delta at design conditions
dT_cool = 2.0    # K - pinch delta at design conditions

# Heat pump
HP_maxSize = 20.0E6  # max thermal design size [Wth]
HP_minSize = 1.0E6  # min thermal design size [Wth]
HP_etaex = 0.6  # exergetic efficiency of WSHP [L. Girardin et al., 2010]_
HP_deltaT_cond = 2.0  # pinch for condenser [K]
HP_deltaT_evap = 2.0  # pinch for evaporator [K]
HP_maxT_cond = 140 + 273.0  # max temperature at condenser [K]
HP_Auxratio = 0.83  # Wdot_comp / Wdot_total (circulating pumps)
# Substation data
roughness = 0.02 / 1000  # roughness coefficient for heating network pipe in m (for a steel pipe, from Li &
NetworkDepth = 1  # m

# Initial Diameter guess
REDUCED_TIME_STEPS = 50 # number of time steps of maximum demand which are evaluated as an initial guess of the edge diameters
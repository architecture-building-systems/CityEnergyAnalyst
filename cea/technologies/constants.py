"""
Constants used throughout the cea.technologies package.

History lesson: This is a first step at removing the `cea.globalvars.GlobalVariables` object.
"""

# Heat Exchangers
U_cool = 2500.0  # W/m2K
U_heat = 2500.0  # W/m2K
dT_heat = 5.0    # K - pinch delta at design conditions
dT_cool = 2.0    # K - pinch delta at design conditions

# Specific heat
rho_W = 998.0  # [kg/m^3] density of Water
cp = 4185.0      # [J/kg K]


# Substation data
roughness = 0.02 / 1000  # roughness coefficient for heating network pipe in m (for a steel pipe, from Li &
NetworkDepth = 1  # m

# Initial Diameter guess
REDUCED_TIME_STEPS = 50 # number of time steps of maximum demand which are evaluated as an initial guess of the edge diameters
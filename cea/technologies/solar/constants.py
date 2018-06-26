
"""
Parameters used for solar technologies
"""

# pressure losses in building pipes connecting to SC/PVT
dpl_Paperm = 200
fcr = 1.3
Ro_kgperm3 = 1000
eff_pumping = 0.6
k_msc_max_WpermK = 0.217

# glazing properties for PV
n = 1.526  # refractive index of glass
K = 0.4  # glazing extinction coefficient

# environmental properties
Pg = 0.2  # ground reflectance

# operation temperatures
T_IN_SC_FP = 75
T_IN_SC_ET = 100
T_IN_PVT = 35

# standard testing condition (STC)
STC_RADIATION_Wperm2 = 1000
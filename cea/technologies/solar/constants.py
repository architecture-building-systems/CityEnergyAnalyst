
"""
Parameters used for solar technologies

:References: Duffie, J. A. and Beckman, W. A. (2013) Radiation Transmission through Glazing: Absorbed Radiation, in
             Solar Engineering of Thermal Processes, Fourth Edition, John Wiley & Sons, Inc., Hoboken, NJ, USA.
             doi: 10.1002/9781118671603.ch5
"""




# pressure losses in building pipes connecting to SC/PVT
dpl_Paperm = 200
fcr = 1.3
Ro_kgperm3 = 1000
eff_pumping = 0.6
k_msc_max_WpermK = 0.217

# glazing properties for PV
n = 1.526  # refractive index of glass
K = 4  # glazing extinction coefficient
L = 0.004  # typical BIPV glazing thickness in meters 

# environmental properties
Pg = 0.2  # ground reflectance

# operation temperatures
T_IN_SC_FP = 60
T_IN_SC_ET = 75
T_IN_PVT = 35

# standard testing condition (STC)
STC_RADIATION_Wperm2 = 1000

# Loss factor from Figure 4 in https://doi.org/10.1016/j.enbuild.2019.109623, roughly mean reflectance across PV spectrum (crystalline)
front_cover_loss_factors = {
    "clear": 0.0,
    "gold": 0.128,
    "purple": 0.111,
    "pure_white": 0.452,
    "basic_white": 0.347,
    "medium_green": 0.152,
    "terracotta": 0.094,
    "dark_green": 0.091,
    "light_grey": 0.118
}
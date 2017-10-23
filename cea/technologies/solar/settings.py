# -*- coding: utf-8 -*-
"""
Parameters used for solar technologies
"""

## USER INPUTS

# site specific input
date_start = '2016-01-01'  # format: yyyy-mm-dd

# type of panels
# for PVT, please choose type_PVpanel = 'PV1', type_SCpanel = 'SC1'
type_PVpanel = 'PV1'  # PV1: monocrystalline, PV2: poly, PV3: amorphous. please refer to supply system database.
type_SCpanel = 'SC1'  # SC1: flat plat collectors, SC2: evacuated tubes

# installed locations
panel_on_roof = True  # flag for considering panels on roof
panel_on_wall = True  # flag for considering panels on wall
min_radiation = 0.01  # filtering criteria: at least a minimum production of this % from the maximum in the area.

# panel spacing
solar_window_solstice = 4 # desired hours of solar window on the solstice

# panel specific inputs
T_in_SC = 75  # inlet temperature of solar collectors [C]
T_in_PVT = 35 # inlet temperature of PVT panels [C]


## INTERNAL PARAMETERS

# solar collectors pumping requirements
dpl_Paperm = 200 # pressure losses per length of pipe according to Solar District Heating Guidelines, [Pa/m]
fcr = 1.3 # additional loss factor due to accessories
Ro_kgperm3 = 1000 # water density [kg/m3]
eff_pumping = 0.6 # pump efficiency

# solar collectors heat losses
k_msc_max_WpermK = 0.217 # linear heat transmittance coefficient of piping (2*pi*k/ln(Do/Di))) [W/mK]







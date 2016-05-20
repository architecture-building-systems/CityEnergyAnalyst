# -*- coding: utf-8 -*-
"""
================
Global variables
================

"""


# Date data
DAYS_IN_YEAR = 365
HOURS_IN_DAY = 24

# Specific heat
cp = 4185.5 # [J/kg K]
rho_60 = 983.21 # kg/m^3, density of Water @ 60°C
Wh_to_J = 3600.0 # 

# Emission Data (Table 2.2 Share Latex)
# MJ_Oil_eq / MJ_final
NG_TO_OIL_EQ = 1.06 
BG_TO_OIL_EQ = 0.308
EL_TO_OIL_EQ = 1.8
EL_TO_OIL_EQ_GREEN = 0
WOOD_TO_OIL_EQ = 0.2

# kg_CO2 /MJ_final
NG_TO_CO2 = 0.0633 
BG_TO_CO2 = 0.0366
EL_TO_CO2 = 0.00766
EL_TO_CO2_GREEN = 0
WOOD_TO_CO2 = 0.00959


# Financial Data
EURO_TO_CHF = 1.2
CHF_TO_EURO = 1.0/EURO_TO_CHF
USD_TO_CHF = 0.96 
MWST = 0.08 # 8% MWST assumed, used in A+W data
    
# electricity Price
ELEC_PRICE = 0.104 * EURO_TO_CHF / 1000.0 # 0.0001 € /  Wh = 0.1 € / kWh (Thuy-An Excel, OECD Values) 
NG_PRICE = 0.057 * EURO_TO_CHF / 1000.0 #  € / Wh = 0.10 € /kWh; Thuy-An Excel, OECD Values
BG_PRICE = 0.078

# Heat Exchangers
U_cool = 840 # W/m2K
U_heat = 840 # W/m2K
dT_heat = 5 # K - Temperature difference at design conditions

# Heat pump
HP_maxSize = 20.0E6 # max thermal design size [Wth]
HP_minSize = 1.0E6 # min thermal design size [Wth]
HP_n = 20.0 # lifetime [years]

HP_etaex = 0.6 # exergetic efficiency
HP_deltaT_cond = 2.0 # pinch for condenser [K]
HP_deltaT_evap = 2.0 # pinch for evaporator [K]
HP_maxT_cond = 90+273.0 # max temperature at condenser [K]

HP_Auxratio = 0.83 # Wdot_comp / Wdot_total (circulating pumps)

HP_i = 0.05 # interest rate

# Sewage resource
Sew_minT = 10+273.0 # minimum temperature at the sewage exit [K]

# Lake resources
DeltaU = 12500.0E6 * 3600 # [J], maximum change in the lake energy content at the end of the year (positive or negative)
Vdotmax = 1000.0 / 3600 # [m3/s] if water is pumped for cooling purposes
Qcoldmax = 6.0E6 # max cooling power if water is pumped for cooling purposes [W]
DelaT = 3 # Max temperature increase if water is pumped for cooling purposes 

# Geothermal heat pump
GHP_CmaxSize = 20.0E3 # max cooling design size [Wc] FOR ONE PROBE
GHP_Cmax_Size_th = 30.5E3 # Wth per probe

GHP_HmaxSize = 30.5E3 # max heating design size [Wth] FOR ONE PROBE
GHP_WmaxSize = 10.5E3 # max electrical design size [Wel] FOR ONE PROBE

GHP_nBH = 50.0 # [years] for a borehole
GHP_nHP = 20.0 # for the geothermal heat pump

GHP_etaex = 0.677 # exergetic efficiency
GHP_Auxratio = 0.83 # Wdot_comp / Wdot_total (circulating pumps)

GHP_i = 0.06 # interest rate
GHP_A = 64 # [m^2] area occupancy of one borehole 

# Combined cycle

CC_n = 25.0 # lifetime
CC_i = 0.06

GT_maxSize = 50.00000001E6 # max electrical design size in W = 50MW (NOT THERMAL capacity)
GT_minSize = 0.2E6 # min electrical design size in W = 0.2 MW (NOT THERMAL capacity)
GT_minload = 0.1 * 0.999 # min load (part load regime)

CC_exitT_NG = 986.0 # exit temperature of the gas turbine if NG
CC_exitT_BG = 1053.0 # exit temperature of the gas turbine if BG
CC_airratio = 2.0 # air to fuel mass ratio

ST_deltaT = 4.0 # pinch for HRSG
ST_deltaP = 5.0E5 # pressure loss between steam turbine and DHN
CC_deltaT_DH = 5.0 # pinch for condenser

STGen_eta = 0.9 # generator efficiency after steam turbine


# Boiler
    # Operating figures, quality parameters and investment costs for district heating systems (AFO)

Boiler_n = 20.0 # lifetime, after A+W, confirmed by average of 15-25y range after http://www.elco.ch/pdf/Solutions/ \ 
                # ELCO-Loesungsbeispiel-Huber.pdf
Boiler_i = 0.05 # interest rate
Boiler_C_fuel = 20.0 # € / MWh_therm_bought(for LHV), AFO
Boiler_C_labour = 4.0 # € /MWh_therm_sold
Boiler_P_aux = 0.026 # 0.026 Wh/Wh_th_sold = 26 kWh_el / MWh_th_sold, bioenergy 2020
Boiler_min = 0.05  # minimum Part Load of Boiler
Boiler_equ_ratio = 0.2 # 20% own capital required (equity ratio) 
Boiler_C_maintainance = 0.05 # 5 % of capital cost (3% boiler, 2% techn. facilities) by AFO
Boiler_C_maintainance_faz = 3.5 /1E6 * EURO_TO_CHF #3.5 # Euro /MW_th 


# Furnace
Furn_FuelCost_wet = 0.057 *1E-3  # CHF / Wh = 5.7 Rp / kWh for wet (50wt%) Wood Chips, after 
#        http://www.wvs.ch/fileadmin/user_upload/Holzmarkt/Preisempfehlungen/Energieholzpreise/2013_-_14_Energieholz_Preisempfehlungen.pdf
Furn_FuelCost_dry = 0.07 * 1E-3 # CHF / Wh = 7 Rp / kWh for dry (30wt%) Wood Chips, 
#after http://www.wvs.ch/fileadmin/user_upload/Holzmarkt/Preisempfehlungen/Energieholzpreise/2013_-_14_Energieholz_Preisempfehlungen.pdf
Furn_Moist_type = "wet" # "dry" or "wet", depending on the fuel input
Furn_min_Load = 0.2  # Minimum load possible (does not affect Model itself!)
Furn_min_electric = 0.3 # Minimum load for electricity generation in furnace plant

# Substation Heat Exchangers
Subst_n = 25.0 # Lifetime after A+W
Subst_i = 0.05

# Fuel Cells
FC_OP_HOURS_PER_YEAR = 4000.0 # hours / year
FC_LIFETIME = 40000.0  # hours of operation
FC_n = FC_LIFETIME / FC_OP_HOURS_PER_YEAR # years of operation
FC_i = 0.05
FC_stack_cost = 55000.0 # CHF /kW_th for a Hexis 1000 N
FC_overhead = 0.1 # 10 % higher cost due to final installation 


# Low heating values

LHV_NG = 45.4E6 # [J/kg]
LHV_BG = 21.4E6 # [J/kg]


# Vapor compressor chiller

VCC_maxSize = 3500.0E3 # cooling power design size [W]
VCC_n = 20.0

VCC_tcoolin = 30 + 273.0 # entering condenser water temperature [K]

VCC_LCOE = 0.0418 # coefficient for levelized cost  [US$ / kWh cooling]
VCC_minload = 0.1 # min load for cooling power


# Cooling tower

CT_maxSize = 10.0E6 # cooling power desin size [W]
CT_n = 20.0
CT_a = 0.15 # annuity factor

# Storage
T_storage_min = 10 + 273.0 # K  - Minimum Storage Temperature

# Activation Order of Power Plants
# solar sources are treated first
act_first = 'HP' # accounts for all kind of HP's as only one will be in the system. 
act_second = 'CC' #accounts for ORC and NG-RC (produce electricity!)
act_third = 'Boiler' # all conventional boilers are considered to be backups.
act_fourth = 'BoilerPeak' # additional Peak Boiler

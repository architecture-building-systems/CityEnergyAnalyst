# -*- coding: utf-8 -*-
"""
This file contains the constants used in objective function calculation in optimization
"""
from __future__ import absolute_import
__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# Losses and margins
DCNetworkLoss = 0.05  # Cooling ntw losses (10% --> 0.1)
DHNetworkLoss = 0.12  # Heating ntw losses
Qmargin_ntw = 0.01  # Reliability margin for the system nominal capacity in the hub
Qloss_Disc = 0.05  # Heat losses within a disconnected building
Qmargin_Disc = 0.20  # Reliability margin for the system nominal capacity for decentralized systems
QminShare = 0.10  # Minimum percentage for the installed capacity
K_DH = 0.25  # linear heat loss coefficient district heting network twin pipes groundfoss
roughness = 0.02 / 1000  # roughness coefficient for heating network pipe in m (for a steel pipe, from Li &
# Svendsen (2012) "Energy and exergy analysis of low temperature district heating network")

# pipes location properties
Z0 = 1.5  # location of pipe underground in m
Psl = 1600  # heat capacity of ground in kg/m3 => should be density?
Csl = 1300  # heat capacity of ground in J/kg K
Bsl = 1.5  # thermal conductivity of ground in W/m.K


######### LOCAL PLANT : factor with regard to USEFUL ENERGY

NG_BACKUPBOILER_TO_CO2_STD = 0.0691 * 0.87  # kg_CO2 / MJ_useful
BG_BACKUPBOILER_TO_CO2_STD = 0.04 * 0.87  # kg_CO2 / MJ_useful
SMALL_GHP_TO_CO2_STD = 0.0153 * 3.9  # kg_CO2 / MJ_useful
# SMALL_LAKEHP_TO_CO2_STD    = 0.0211 * 2.8    # kg_CO2 / MJ_useful
SOLARCOLLECTORS_TO_CO2 = 0.00911  # kg_CO2 / MJ_useful

NG_BACKUPBOILER_TO_OIL_STD = 1.16 * 0.87  # MJ_oil / MJ_useful
BG_BACKUPBOILER_TO_OIL_STD = 0.339 * 0.87  # MJ_oil / MJ_useful
SMALL_GHP_TO_OIL_STD = 0.709 * 3.9  # MJ_oil / MJ_useful
# SMALL_LAKEHP_TO_OIL_STD    = 0.969 * 2.8     # MJ_oil / MJ_useful
SOLARCOLLECTORS_TO_OIL = 0.201  # MJ_oil / MJ_useful



EL_PV_TO_OIL_EQ = 0.345  # MJ_oil / MJ_final
EL_PV_TO_CO2 = 0.02640  # kg_CO2 / MJ_final

# Solar area to Wpeak
eta_area_to_peak = 0.16  # Peak Capacity - Efficiency, how much kW per area there are, valid for PV and PVT (after Jimeno's J+)

# Pressure losses
# DeltaP_DCN = 1.0 #Pa - change
# DeltaP_DHN = 84.8E3 / 10.0 #Pa  - change

PumpEnergyShare = 0.01  # assume 1% of energy required for pumping, after 4DH
PumpReliabilityMargin = 0.05  # assume 5% reliability margin

# Circulating Pump
etaPump = 0.8

# Heat Exchangers
U_cool = 2500  # W/m2K
U_heat = 2500  # W/m2K
dT_heat = 5  # K - pinch delta at design conditions
dT_cool = 1  # K - pinch delta at design conditions
# Heat pump
HP_maxSize = 20.0E6  # max thermal design size [Wth]
HP_minSize = 1.0E6  # min thermal design size [Wth]

HP_etaex = 0.6  # exergetic efficiency of WSHP [L. Girardin et al., 2010]_
HP_deltaT_cond = 2.0  # pinch for condenser [K]
HP_deltaT_evap = 2.0  # pinch for evaporator [K]
HP_maxT_cond = 140 + 273.0  # max temperature at condenser [K]
HP_Auxratio = 0.83  # Wdot_comp / Wdot_total (circulating pumps)

# Sewage resource

Sew_minT = 10 + 273.0  # minimum temperature at the sewage exit [K]

# Lake resources
DeltaU = 12500.0E6  # [Wh], maximum change in the lake energy content at the end of the year (positive or negative)
TLake = 5 + 273.0  # K

# Geothermal heat pump

TGround = 6.5 + 273.0

COPScalingFactorGroundWater = 3.4 / 3.9  # Scaling factor according to EcoBau, take GroundWater Heat pump into account

GHP_CmaxSize = 2E3  # max cooling design size [Wc] FOR ONE PROBE
GHP_Cmax_Size_th = 2E3  # Wh/m per probe
GHP_Cmax_Length = 40  # depth of exploration taken into account

GHP_HmaxSize = 2E3  # max heating design size [Wth] FOR ONE PROBE
GHP_WmaxSize = 1E3  # max electrical design size [Wel] FOR ONE PROBE

GHP_etaex = 0.677  # exergetic efficiency [O. Ozgener et al., 2005]_
GHP_Auxratio = 0.83  # Wdot_comp / Wdot_total (circulating pumps)

GHP_A = 25  # [m^2] area occupancy of one borehole Gultekin et al. 5 m separation at a penalty of 10% less efficeincy

# Combined cycle

GT_maxSize = 50.00000001E6  # max electrical design size in W = 50MW (NOT THERMAL capacity)
GT_minSize = 0.2E6  # min electrical design size in W = 0.2 MW (NOT THERMAL capacity)
GT_minload = 0.1 * 0.999  # min load (part load regime)

CC_exitT_NG = 986.0  # exit temperature of the gas turbine if NG
CC_exitT_BG = 1053.0  # exit temperature of the gas turbine if BG
CC_airratio = 2.0  # air to fuel mass ratio

ST_deltaT = 4.0  # pinch for HRSG
ST_deltaP = 5.0E5  # pressure loss between steam turbine and DHN
CC_deltaT_DH = 5.0  # pinch for condenser

STGen_eta = 0.9  # generator efficiency after steam turbine

# Boiler
# Operating figures, quality parameters and investment costs for district heating systems (AFO)

# ELCO-Loesungsbeispiel-Huber.pdf

Boiler_C_fuel = 20.0  # € / MWh_therm_bought(for LHV), AFO
Boiler_P_aux = 0.026  # 0.026 Wh/Wh_th_sold = 26 kWh_el / MWh_th_sold, bioenergy 2020
Boiler_min = 0.05  # minimum Part Load of Boiler
Boiler_equ_ratio = 0.2  # 20% own capital required (equity ratio)
Boiler_eta_hp = 0.9

# Furnace
Furn_FuelCost_wet = 0.057 * 1E-3  # CHF / Wh = 5.7 Rp / kWh for wet (50wt%) Wood Chips, after
Furn_FuelCost_dry = 0.07 * 1E-3  # CHF / Wh = 7 Rp / kWh for dry (30wt%) Wood Chips,
Furn_min_Load = 0.2  # Minimum load possible (does not affect Model itself!)
Furn_min_electric = 0.3  # Minimum load for electricity generation in furnace plant

ZernezFlag = False
FlagBioGasFromAgriculture = False  # True = Biogas from Agriculture, False = Biogas normal
HPSew_allowed = True
HPLake_allowed = True
GHP_allowed = True
CC_allowed = True
Furnace_allowed = False
DiscGHPFlag = True  # Is geothermal allowed in disconnected buildings? False = NO ; True = YES
DiscBioGasFlag = False  # True = use Biogas only in Disconnected Buildings, no Natural Gas; False = both possible

# Emission and Primary energy factors

######### Biogas to Agric. Bio Gas emissions
NormalBGToAgriBG_CO2 = 0.127 / 0.754  # Values from Electricity used for comparison
NormalBGToAgriBG_Eprim = 0.0431 / 0.101  # Values from Electricity used for comparison

######### CENTRAL HUB PLANT : factor with regard to FINAL ENERGY

# normalized on their efficiency, including all CO2 emissions (Primary, grey, electricity etc. until exit of Hub)
# usage : divide by system efficiency and Hub to building-efficiency
ETA_FINAL_TO_USEFUL = 0.9  # assume 90% system efficiency in terms of CO2 emissions and overhead emissions (\

######### ELECTRICITY
CC_EL_TO_TOTAL = 4 / 9

EL_TO_OIL_EQ = 2.69  # MJ_oil / MJ_final
EL_TO_CO2 = 0.0385  # kg_CO2 / MJ_final - CH Verbrauchermix nach EcoBau

EL_TO_OIL_EQ_GREEN = 0.0339  # MJ_oil / MJ_final
EL_TO_CO2_GREEN = 0.00398  # kg_CO2 / MJ_final

EL_NGCC_TO_OIL_EQ_STD = 2.94 * 0.78 * CC_EL_TO_TOTAL  # MJ_oil / MJ_final
EL_NGCC_TO_CO2_STD = 0.186 * 0.78 * CC_EL_TO_TOTAL  # kg_CO2 / MJ_final

if FlagBioGasFromAgriculture == 1:  # Use Biogas from Agriculture
    EL_BGCC_TO_OIL_EQ_STD = 0.156 * 0.78 * CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
    EL_BGCC_TO_CO2_STD = 0.0495 * 0.78 * CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
else:
    EL_BGCC_TO_OIL_EQ_STD = 0.851 * 0.78 * CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
    EL_BGCC_TO_CO2_STD = 0.114 * 0.78 * CC_EL_TO_TOTAL  # kg_CO2 / MJ_final

EL_FURNACE_TO_OIL_EQ_STD = 0.141 * 0.78 * CC_EL_TO_TOTAL  # MJ_oil / MJ_final
EL_FURNACE_TO_CO2_STD = 0.0285 * 0.78 * CC_EL_TO_TOTAL  # kg_CO2 / MJ_final

# Combined Cycle
CC_sigma = 4 / 5

NG_CC_TO_CO2_STD = (0.0353 + 0.186) * 0.78 / ETA_FINAL_TO_USEFUL * (
        1 + CC_sigma)  # kg_CO2 / MJ_useful
NG_CC_TO_OIL_STD = (0.6 + 2.94) * 0.78 / ETA_FINAL_TO_USEFUL * (
        1 + CC_sigma)  # MJ_oil / MJ_useful

if FlagBioGasFromAgriculture == 1:
    BG_CC_TO_CO2_STD = (0.00592 + 0.0495) * 0.78 / ETA_FINAL_TO_USEFUL * (
            1 + CC_sigma)  # kg_CO2 / MJ_useful
    BG_CC_TO_OIL_STD = (0.0703 + 0.156) * 0.78 / ETA_FINAL_TO_USEFUL * (
            1 + CC_sigma)  # MJ_oil / MJ_useful

else:
    BG_CC_TO_CO2_STD = (0.0223 + 0.114) * 0.78 / ETA_FINAL_TO_USEFUL * (
            1 + CC_sigma)  # kg_CO2 / MJ_useful
    BG_CC_TO_OIL_STD = (0.214 + 0.851) * 0.78 / ETA_FINAL_TO_USEFUL * (
            1 + CC_sigma)  # kg_CO2 / MJ_useful

# Furnace
FURNACE_TO_CO2_STD = (0.0104 + 0.0285) * 0.78 / ETA_FINAL_TO_USEFUL * (
        1 + CC_sigma)  # kg_CO2 / MJ_useful
FURNACE_TO_OIL_STD = (0.0956 + 0.141) * 0.78 / ETA_FINAL_TO_USEFUL * (
        1 + CC_sigma)  # MJ_oil / MJ_useful

# Boiler
NG_BOILER_TO_CO2_STD = 0.0874 * 0.87 / ETA_FINAL_TO_USEFUL  # kg_CO2 / MJ_useful
NG_BOILER_TO_OIL_STD = 1.51 * 0.87 / ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful

if FlagBioGasFromAgriculture == 1:
    BG_BOILER_TO_CO2_STD = 0.339 * 0.87 * NormalBGToAgriBG_CO2 / (
            1 + DHNetworkLoss) / ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful
    BG_BOILER_TO_OIL_STD = 0.04 * 0.87 * NormalBGToAgriBG_Eprim / (
            1 + DHNetworkLoss) / ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful

else:
    BG_BOILER_TO_CO2_STD = NG_BOILER_TO_CO2_STD * 0.04 / 0.0691  # kg_CO2 / MJ_useful
    BG_BOILER_TO_OIL_STD = NG_BOILER_TO_OIL_STD * 0.339 / 1.16  # MJ_oil / MJ_useful

# HP Lake
LAKEHP_TO_CO2_STD = 0.0262 * 2.8 / ETA_FINAL_TO_USEFUL  # kg_CO2 / MJ_useful
LAKEHP_TO_OIL_STD = 1.22 * 2.8 / ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful

# HP Sewage
SEWAGEHP_TO_CO2_STD = 0.0192 * 3.4 / ETA_FINAL_TO_USEFUL  # kg_CO2 / MJ_useful
SEWAGEHP_TO_OIL_STD = 0.904 * 3.4 / ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful

# GHP
GHP_TO_CO2_STD = 0.0210 * 3.9 / ETA_FINAL_TO_USEFUL  # kg_CO2 / MJ_useful
GHP_TO_OIL_STD = 1.03 * 3.9 / ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful

# Substation Heat Exchangers


# Vapor compressor chiller
VCC_tcoolin = 30 + 273.0  # entering condenser water temperature [K]
VCC_minload = 0.1  # min load for cooling power

# Storage
T_storage_min = 10 + 273.0  # K  - Minimum Storage Temperature
StorageMaxUptakeLimitFlag = 1  # set a maximum for the HP Power for storage charging / decharging
QtoStorageMax = 1e6  # 100kW maximum peak

# Activation Order of Power Plants
# solar sources are treated first
act_first = 'HP'  # accounts for all kind of HP's as only one will be in the system.
act_second = 'CHP'  # accounts for ORC and NG-RC (produce electricity!)
act_third = 'BoilerBase'  # all conventional boilers are considered to be backups.
act_fourth = 'BoilerPeak'  # additional Peak Boiler

# Data for Evolutionary algorithm
nHeat = 6  # number of heating
nHR = 2  # number of heat recovery options
nSolar = 3  # number of solar technologies

PROBA = 0.5
SIGMAP = 0.2
epsMargin = 0.001

# Heat Recovery

# compressed Air recovery
etaElToHeat = 0.75  # [-]
TElToHeatSup = 80 + 273.0  # K
TElToHeatRet = 70 + 273.0  # K

# Server Waste Heat recovery
etaServerToHeat = 0.8  # [-]
TfromServer = 60 + 273.0  # K
TtoServer = 55 + 273.0  # K

# Solar Thermal: information of return temperature
TsupplyPVT_35 = 35 + 273.0  # K
TsupplySC_80 = 75 + 273.0  # K
TsupplySC_ET50 = 50 + 273.0  # K
TsupplySC_ET80 = 80 + 273.0  # K

# solar PV and PVT
nPV = 0.16
nPVT = 0.16
# ==============================================================================================================
# solar thermal collector
# ==============================================================================================================

Tin = 75  # average temeperature
module_lenght_SC = 2  # m # 1 for PV and 2 for solar collectors
min_production = 0.75  # points are selected with at least a minimum production of this % from the maximum in the area.
grid_side = 2  # in a rectangular grid of points, one side of the square. this cannot be changed if the solra potential was made with this.
angle_north = 122.5
type_SCpanel = 1  # Flatplate collector

# ==============================================================================================================
# sewage potential
# ==============================================================================================================

SW_ratio = 0.95  # ratio of waste water to fresh water production.
width_HEX = 0.40  # in m
Vel_flow = 3  # in m/s
min_flow = 9  # in lps
tmin = 8  # tmin of extraction
h0 = 1.5  # kW/m2K # heat trasnfer coefficient/
AT_HEX = 5
ATmin = 2

# Low heating values
LHV_NG = 45.4E6  # [J/kg]
LHV_BG = 21.4E6  # [J/kg]

# DCN
TsupCool = 6 + 273
TretCoolMax = 12 + 273.0

# Values for the calculation of Delta P (from F. Muller network optimization code)
# WARNING : current = values for Inducity SQ
DeltaP_Coeff = 104.81
DeltaP_Origin = 59016

Subst_n = 20  # Lifetime after A+W default 20

ZERO_DEGREES_CELSIUS_IN_KELVIN = 273.15  # Use this value, where the default temperature is assigned as 0 degree C
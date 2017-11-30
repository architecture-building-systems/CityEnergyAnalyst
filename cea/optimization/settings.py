# -*- coding: utf-8 -*-
"""
Parameters used for optimization and objective function calculation
"""

## USER INPUTS
initialInd = 2  # number of initial individuals
NGEN = 5  # number of total generations
fCheckPoint = 1  # frequency for the saving of checkpoints
maxTime = 7 * 24 * 3600  # maximum computational time [seconds]

ZernezFlag = 0
FlagBioGasFromAgriculture = 0  # 1 = Biogas from Agriculture, 0 = Biogas normal
HPSew_allowed = 1
HPLake_allowed = 1
GHP_allowed = 1
CC_allowed = 1
Furnace_allowed = 0
DiscGHPFlag = 1  # Is geothermal allowed in disconnected buildings? 0 = NO ; 1 = YES
DiscBioGasFlag = 0  # 1 = use Biogas only in Disconnected Buildings, no Natural Gas; 0so = both possible

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

# Emission and Primary energy factors

######### Biogas to Agric. Bio Gas emissions
NormalBGToAgriBG_CO2 = 0.127 / 0.754  # Values from Electricity used for comparison
NormalBGToAgriBG_Eprim = 0.0431 / 0.101  # Values from Electricity used for comparison

######### CENTRAL HUB PLANT : factor with regard to FINAL ENERGY

# normalized on their efficiency, including all CO2 emissions (Primary, grey, electricity etc. until exit of Hub)
# usage : divide by system efficiency and Hub to building-efficiency
ETA_FINAL_TO_USEFUL = 0.9  # assume 90% system efficiency in terms of CO2 emissions and overhead emissions (\
# after Heating systems in buildings %E2%80%94 Method for calculation of system\
# energy requirements and system efficiencies %E2%80%94 Part 4-5 Space heating \
# generation systems, the performance and quality)


# using HP values, divide by COP and multiply by factor
# susing other systems, divide final energy (what comes out of the pipe) by efficiency multiply by factor
# Furnace: All emissions allocated to the thermal energy, get CO2 of electricity back!

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

EL_PV_TO_OIL_EQ = 0.345  # MJ_oil / MJ_final
EL_PV_TO_CO2 = 0.02640  # kg_CO2 / MJ_final



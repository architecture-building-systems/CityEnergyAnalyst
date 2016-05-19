# -*- coding: utf-8 -*-
"""
================
Global variables
================

"""
#################e########## User inputs


# Commands for the evolutionary algorithm
initialInd = 43         # number of initial individuals
NGEN = 20            # number of total generations
fCheckPoint = 1             # frequency for the saving of checkpoints
maxTime = 200 * 3600         # maximum computional time [seconds]



# Set Flags for different system setup preferences

NetworkLengthZernez = 864.0 #meters network length of maximum network, \
                            #then scaled by number of costumers (Zernez Specific), from J.Fonseca's PipsesData

ZernezFlag = 1
FlagBioGasFromAgriculture = 1 # 1 = Biogas from Agriculture, 0 = Biogas normal 
HPSew_allowed = 0 
HPLake_allowed = 0
GHP_allowed = 1
CC_allowed = 0
Furnace_allowed = 1
DiscGHPFlag = 1 # Is geothermal allowed in disconnected buildings? 0 = NO ; 1 = YES
DiscBioGasFlag = 1 # 1 = use Biogas only in Disconnected Buildings, no Natural Gas; 0so = both possible

########################### Model parameters

# Date data
DAYS_IN_YEAR = 365
HOURS_IN_DAY = 24

# Specific heat
cp = 4185                # [J/kg K]
rho_60 = 983.21          # [kg/m^3] density of Water @ 60°C
Wh_to_J = 3600.0

# Low heating values
LHV_NG = 45.4E6 # [J/kg]
LHV_BG = 21.4E6 # [J/kg]


# Losses and margins
DCNetworkLoss = 0.12     # Cooling ntw losses (10% --> 0.1) 
DHNetworkLoss = 0.12     # Heating ntw losses
Qmargin_ntw = 0.01       # Reliability margin for the system nominal capacity in the hub
Qloss_Disc = 0.05        # Heat losses within a disconnected building
Qmargin_Disc = 0.01      # Reliability margin for the system nominal capacity for decentralized systems


# Emission and Primary energy factors

    ######### Biogas to Agric. Bio Gas emissions
NormalBGToAgriBG_CO2     = 0.127 / 0.754  # Values from Electricity used for comparison
NormalBGToAgriBG_Eprim   = 0.0431 / 0.101 # Values from Electricity used for comparison

    ######### CENTRAL HUB PLANT : factor with regard to FINAL ENERGY
    
#normalized on their efficiency, including all CO2 emissions (Primary, grey, electricity etc. until exit of Hub)
#usage : divide by system efficiency and Hub to building-efficiency
ETA_FINAL_TO_USEFUL  =  0.9 # assume 90% system efficiency in terms of CO2 emissions and overhead emissions (\
                            # after Heating systems in buildings %E2%80%94 Method for calculation of system\
                            # energy requirements and system efficiencies %E2%80%94 Part 4-5 Space heating \
                            # generation systems, the performance and quality)
                            
                            # using HP values, divide by COP and multiply by factor
                            # susing other systems, divide final energy (what comes out of the pipe) by efficiency multiply by factor
                            # Furnace: All emissions allocated to the thermal energy, get CO2 of electricity back!

# Combined Cycle                            
CC_sigma     = 4/5

NG_CC_TO_CO2_STD     = (0.0353 + 0.186) * 0.78 / ETA_FINAL_TO_USEFUL * (1+CC_sigma)         # kg_CO2 / MJ_useful
NG_CC_TO_OIL_STD     = (0.6 + 2.94) * 0.78  / ETA_FINAL_TO_USEFUL * (1+CC_sigma)            # MJ_oil / MJ_useful

if FlagBioGasFromAgriculture == 1:
    BG_CC_TO_CO2_STD  = (0.00592 + 0.0495)  * 0.78 / ETA_FINAL_TO_USEFUL * (1+CC_sigma)      # kg_CO2 / MJ_useful
    BG_CC_TO_OIL_STD  = (0.0703 + 0.156)  * 0.78  / ETA_FINAL_TO_USEFUL * (1+CC_sigma)      # MJ_oil / MJ_useful

else:
    BG_CC_TO_CO2_STD  = (0.0223 + 0.114) * 0.78 / ETA_FINAL_TO_USEFUL * (1+CC_sigma)         # kg_CO2 / MJ_useful
    BG_CC_TO_OIL_STD  = (0.214 + 0.851)  * 0.78 / ETA_FINAL_TO_USEFUL * (1+CC_sigma)        # kg_CO2 / MJ_useful


# Furnace
FURNACE_TO_CO2_STD   = (0.0104 + 0.0285) * 0.78 / ETA_FINAL_TO_USEFUL * (1+CC_sigma)           # kg_CO2 / MJ_useful
FURNACE_TO_OIL_STD   = (0.0956 + 0.141) * 0.78  / ETA_FINAL_TO_USEFUL * (1+CC_sigma)           # MJ_oil / MJ_useful


# Boiler
NG_BOILER_TO_CO2_STD  = 0.0874 * 0.87 / ETA_FINAL_TO_USEFUL               # kg_CO2 / MJ_useful   
NG_BOILER_TO_OIL_STD  = 1.51 * 0.87  / ETA_FINAL_TO_USEFUL                # MJ_oil / MJ_useful   

if FlagBioGasFromAgriculture == 1:
    BG_BOILER_TO_CO2_STD      = 0.339    * 0.87 * NormalBGToAgriBG_CO2 / (1+DHNetworkLoss) / ETA_FINAL_TO_USEFUL # MJ_oil / MJ_useful   
    BG_BOILER_TO_OIL_STD      = 0.04   * 0.87 * NormalBGToAgriBG_Eprim / (1+DHNetworkLoss) / ETA_FINAL_TO_USEFUL # MJ_oil / MJ_useful   

else:
    BG_BOILER_TO_CO2_STD      = NG_BOILER_TO_CO2_STD * 0.04 / 0.0691   # kg_CO2 / MJ_useful 
    BG_BOILER_TO_OIL_STD      = NG_BOILER_TO_OIL_STD * 0.339 / 1.16      # MJ_oil / MJ_useful  


# HP Lake
LAKEHP_TO_CO2_STD    = 0.0262 * 2.8 / ETA_FINAL_TO_USEFUL                   # kg_CO2 / MJ_useful
LAKEHP_TO_OIL_STD    = 1.22 * 2.8  / ETA_FINAL_TO_USEFUL                 # MJ_oil / MJ_useful

# HP Sewage
SEWAGEHP_TO_CO2_STD  = 0.0192 * 3.4 / ETA_FINAL_TO_USEFUL                   # kg_CO2 / MJ_useful
SEWAGEHP_TO_OIL_STD  = 0.904 * 3.4 / ETA_FINAL_TO_USEFUL                 # MJ_oil / MJ_useful

# GHP
GHP_TO_CO2_STD       = 0.0210 * 3.9 / ETA_FINAL_TO_USEFUL                   # kg_CO2 / MJ_useful
GHP_TO_OIL_STD       = 1.03 * 3.9 / ETA_FINAL_TO_USEFUL                   # MJ_oil / MJ_useful


    ######### LOCAL PLANT : factor with regard to USEFUL ENERGY

NG_BACKUPBOILER_TO_CO2_STD = 0.0691 * 0.87   # kg_CO2 / MJ_useful
BG_BACKUPBOILER_TO_CO2_STD = 0.04 * 0.87     # kg_CO2 / MJ_useful
SMALL_GHP_TO_CO2_STD       = 0.0153 * 3.9    # kg_CO2 / MJ_useful
#SMALL_LAKEHP_TO_CO2_STD    = 0.0211 * 2.8    # kg_CO2 / MJ_useful
SOLARCOLLECTORS_TO_CO2     = 0.00911          # kg_CO2 / MJ_useful

NG_BACKUPBOILER_TO_OIL_STD = 1.16 * 0.87     # MJ_oil / MJ_useful
BG_BACKUPBOILER_TO_OIL_STD = 0.339 * 0.87    # MJ_oil / MJ_useful
SMALL_GHP_TO_OIL_STD       = 0.709 * 3.9     # MJ_oil / MJ_useful
#SMALL_LAKEHP_TO_OIL_STD    = 0.969 * 2.8     # MJ_oil / MJ_useful
SOLARCOLLECTORS_TO_OIL     = 0.201           # MJ_oil / MJ_useful



    ######### ELECTRICITY
CC_EL_TO_TOTAL = 4/9

EL_TO_OIL_EQ               = 2.69                            # MJ_oil / MJ_final   
EL_TO_CO2               = 0.0385                         # kg_CO2 / MJ_final - CH Verbrauchermix nach EcoBau

EL_TO_OIL_EQ_GREEN         = 0.0339                          # MJ_oil / MJ_final   
EL_TO_CO2_GREEN         = 0.00398                        # kg_CO2 / MJ_final

EL_NGCC_TO_OIL_EQ_STD      = 2.94 * 0.78 * CC_EL_TO_TOTAL             # MJ_oil / MJ_final   
EL_NGCC_TO_CO2_STD          = 0.186 * 0.78     * CC_EL_TO_TOTAL  # kg_CO2 / MJ_final

if FlagBioGasFromAgriculture == 1: # Use Biogas from Agriculture
    EL_BGCC_TO_OIL_EQ_STD      = 0.156 * 0.78    * CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
    EL_BGCC_TO_CO2_STD      = 0.0495 * 0.78    * CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
else:
    EL_BGCC_TO_OIL_EQ_STD      = 0.851 * 0.78     * CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
    EL_BGCC_TO_CO2_STD      = 0.114 * 0.78     * CC_EL_TO_TOTAL  # kg_CO2 / MJ_final

EL_FURNACE_TO_OIL_EQ_STD   = 0.141 * 0.78 * CC_EL_TO_TOTAL   # MJ_oil / MJ_final   
EL_FURNACE_TO_CO2_STD       = 0.0285 * 0.78    * CC_EL_TO_TOTAL  # kg_CO2 / MJ_final

EL_PV_TO_OIL_EQ            = 0.345                           # MJ_oil / MJ_final   
EL_PV_TO_CO2                = 0.02640                            # kg_CO2 / MJ_final


# Financial Data
EURO_TO_CHF = 1.2
CHF_TO_EURO = 1.0 / EURO_TO_CHF
USD_TO_CHF = 0.96 
MWST = 0.08 # 8% MWST assumed, used in A+W data


# Resource prices
ELEC_PRICE = 0.104 * EURO_TO_CHF / 1000.0 # [CHF / wh] 
#ELEC_PRICE_KEV = 1.5 * ELEC_PRICE # MAKE RESEARCH ABOUT A PROPER PRICE AND DOCUMENT THAT! 
#ELEC_PRICE_GREEN = 1.5 * ELEC_PRICE
NG_PRICE = 0.057 * EURO_TO_CHF / 1000.0 # [CHF / wh]
BG_PRICE = 0.078 * EURO_TO_CHF / 1000.0 # [CHF / wh]

GasConnectionCost = 15.5 / 1000.0 # CHF / W, from  Energie360 15.5 CHF / kW

if ZernezFlag == 1:
    NG_PRICE = 0.0756 / 1000.0 # [CHF / wh] from  Energie360
    BG_PRICE = 0.162 / 1000.0  # [CHF / wh] from  Energie360
    


# DCN
TsupCool = 4 + 273
TretCoolMax = 11 + 273.0

# Substation data
mdot_step_counter_heating = [0.05, 0.1, 0.15 ,0.3, 0.4, 0.5 , 0.6, 1]
mdot_step_counter_cooling = [0, 0.2, 0.5, 0.8, 1]

# Pipes costs from FM's optimization code
class NetworkFeatureData:
    pipesCosts_DHN = 58682
    pipesCosts_DCN = 0.00001
    DeltaP_DHN = 77158
    DeltaP_DCN = 0.00001

NetworkLengthReference = 1745.0 #meters of network length of max network. (Reference = Zug Case Study) , from J. Fonseca's Pipes Data
PipeCostPerMeterInv = 660.0 #CHF /m 
PipeLifeTime = 40.0 # years, Data from A&W
PipeInterestRate = 0.05 # 5% interest rate
PipeCostPerMeterAnnual = PipeCostPerMeterInv / PipeLifeTime
# Solar

PV_Peak = 817.62 # [kW_el] - change 
SolarArea = 5436 # [m2] - change

PVT_Peak = 3793 # [kW_el] - change 
PVT_Qnom = 41 * 1000.0# [W_th] - change 
SC80_Qnom = 2795 * 1000.0 # [W_th] - change

# Solar area to Wpeak
eta_area_to_peak = 0.16 # Peak Capacity - Efficisency, how much kW per area there are, valid for PV and PVT (after Jimeno's J+) 

# Pressure losses
DeltaP_DCN = 1.0 #Pa - change 
DeltaP_DHN = 84.8E3 / 10.0 #Pa  - change
#cPump = 1E-3 * 0.25 * 24. * 365.#e lectricit y cost - check new numbers! 
cPump = ELEC_PRICE * 24. * 365.# coupled to electricity cost 
PumpEnergyShare = 0.01 #assume 1% of energy required for pumping, after 4DH
PumpReliabilityMargin = 0.05 # assume 5% reliability margin

# Circulating Pump
etaPump = 0.8


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
DeltaU = 12500.0E6 # [Wh], maximum change in the lake energy content at the end of the year (positive or negative)
#Vdotmax = 1000.0 / 3600 # [m3/s] if water is pumped for cooling purposes
#Qcoldmax = 6.0E6 # max cooling power if water is pumped for cooling purposes [W]
#DelaT = 3 # Max temperature increase if water is pumped for cooling purposes 
TLake = 5 + 273.0 #K 

# Geothermal heat pump
if ZernezFlag == 1:
    TGround = 8.0 + 273.0

else:
    TGround = 6.5 + 273.0
    
COPScalingFactorGroundWater = 3.4 / 3.9 # Scaling factor according to EcoBau, take GroundWater Heat pump into account

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
CC_Maintenance_per_kWhel = 0.03 * EURO_TO_CHF # 0.03 € / kWh_el after Weber 2008, used in Slave Cost Calculation


# Boiler
    # Operating figures, quality parameters and investment costs for district heating systems (AFO)

Boiler_n = 20.0 # lifetime, after A+W, confirmed by average of 15-25y range after http://www.elco.ch/pdf/Solutions/ \ 
                # ELCO-Loesungsbeispiel-Huber.pdf
Boiler_i = 0.05 # interest rate
Boiler_C_fuel = 20.0 # € / MWh_therm_bought(for LHV), AFO
Boiler_C_labour = 4.0 # [€ /MWh_therm_sold]
Boiler_P_aux = 0.026 # 0.026 Wh/Wh_th_sold = 26 kWh_el / MWh_th_sold, bioenergy 2020
Boiler_min = 0.05  # minimum Part Load of Boiler
Boiler_equ_ratio = 0.2 # 20% own capital required (equity ratio) 
Boiler_C_maintainance = 0.05 # 5 % of capital cost (3% boiler, 2% techn. facilities) by AFO, currently not used
#Boiler_C_maintainance_fazNG = 3.5  /1E6 * EURO_TO_CHF # 3.5 Euro  /MWh_th 
#Boiler_C_maintainance_fazBG = 10.4 /1E6 * EURO_TO_CHF # 10.4 Euro /MWh_th 
Boiler_C_maintainance_faz = 3.5
Boiler_eta_hp = 0.9


# Furnace
Furn_FuelCost_wet = 0.057 *1E-3  # CHF / Wh = 5.7 Rp / kWh for wet (50wt%) Wood Chips, after 
#        http://www.wvs.ch/fileadmin/user_upload/Holzmarkt/Preisempfehlungen/Energieholzpreise/2013_-_14_Energieholz_Preisempfehlungen.pdf
Furn_FuelCost_dry = 0.07 * 1E-3 # CHF / Wh = 7 Rp / kWh for dry (30wt%) Wood Chips, 
#after http://www.wvs.ch/fileadmin/user_upload/Holzmarkt/Preisempfehlungen/Energieholzpreise/2013_-_14_Energieholz_Preisempfehlungen.pdf
#Furn_Moist_type = "wet" # "dry" or "wet", depending on the fuel input
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


# Vapor compressor chiller
VCC_maxSize = 3500.0E3 # cooling power design size [W]
VCC_n = 25.0
VCC_tcoolin = 30 + 273.0 # entering condenser water temperature [K]
VCC_minload = 0.1 # min load for cooling power


# Cooling tower
CT_maxSize = 10.0E6 # cooling power desin size [W]
CT_n = 20.0
CT_a = 0.15 # annuity factor

# Storage
T_storage_min = 10 + 273.0 # K  - Minimum Storage Temperature
StorageMaxUptakeLimitFlag = 1 #set a maximum for the HP Power for storage charging / decharging
QtoStorageMax = 1e6 #100kW maximum peak 
# Activation Order of Power Plants
# solar sources are treated first
act_first = 'HP' # accounts for all kind of HP's as only one will be in the system. 
act_second = 'CHP' #accounts for ORC and NG-RC (produce electricity!)
act_third = 'BoilerBase' # all conventional boilers are considered to be backups.
act_fourth = 'BoilerPeak' # additional Peak Boiler

# Data for Evolutionary algorithm
nHeat = 6
nHR = 2
nSolar = 3


Qmargin_ntw = 0.01 # Reliability margin for the system nominal capacity


fCheckPoint = 1

PROBA = 0.5
SIGMAP = 0.2

epsMargin = 0.001




# Data for clustering
nPeriodMin = 2
nPeriodMax = 15
gam = 0.2
threshErr = 0.2


# Heat Recovery

    # compressed Air recovery 
etaElToHeat = 0.75 # [-]
TElToHeatSup = 80 + 273.0 #K
TElToHeatRet = 70 + 273.0 #K

    # Server Waste Heat recovery
etaServerToHeat = 0.8 # [-]
TfromServer = 60 + 273.0 #K
TtoServer = 55 + 273.0 #K


# Solar Thermal: information of return temperature
TsupplyPVT_35 = 35 + 273.0 # K 
TsupplySC_80 = 75 + 273.0 # K
TsupplySC_ET50 = 50 + 273.0 # K
TsupplySC_ET80  = 80 + 273.0 # K 



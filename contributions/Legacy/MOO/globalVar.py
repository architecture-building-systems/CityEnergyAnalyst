# -*- coding: utf-8 -*-
"""
================
Global variables
================

"""

from contributions.Legacy.MOO.resources.geothermal import calc_ground_temperature
import contributions.Legacy.MOO.optimization.supportFn as sFn

class globalVariables(object):
    def __init__(self):

        Header = "C:\ArcGIS\ESMdata\DataFinal\MOO\HEB/"
        self.pathX = sFn.pathX(Header)
        self.Tg = calc_ground_temperature(self.pathX.pathRaw, self)
        self.num_tot_buildings = sFn.calc_num_buildings(self.pathX.pathRaw, "Total.csv")
        self.sensibilityStep = 2
        ########################### User inputs
        
        # Commands for the evolutionary algorithm
        
        self.initialInd = 3         # number of initial individuals
        self.NGEN = 3000            # number of total generations
        self.fCheckPoint = 1             # frequency for the saving of checkpoints
        self.maxTime = 7*24 * 3600         # maximum computional time [seconds]
        
        # Set Flags for different system setup preferences
        
        # self.NetworkLengthZernez = 864.0 #meters network length of maximum network, \
                                    #then scaled by number of costumers (Zernez Specific), from J.Fonseca's PipsesData
        
        self.ZernezFlag = 0
        self.FlagBioGasFromAgriculture = 0 # 1 = Biogas from Agriculture, 0 = Biogas normal 
        self.HPSew_allowed = 1 
        self.HPLake_allowed = 1
        self.GHP_allowed = 1
        self.CC_allowed = 1
        self.Furnace_allowed = 0
        self.DiscGHPFlag = 1 # Is geothermal allowed in disconnected buildings? 0 = NO ; 1 = YES
        self.DiscBioGasFlag = 0 # 1 = use Biogas only in Disconnected Buildings, no Natural Gas; 0so = both possible
        
        
        # Values for the calculation of Delta P (from F. Muller network optimization code)
        # WARNING : current = values for Inducity SQ
        self.DeltaP_Coeff = 104.81
        self.DeltaP_Origin = 59016
        
        
        ########################### Model parameters
        
        # Date data
        self.DAYS_IN_YEAR = 365
        self.HOURS_IN_DAY = 24
        
        # Specific heat
        self.cp = 4185                # [J/kg K]
        self.rho_60 = 983.21          # [kg/m^3] density of Water @ 60°C
        self.Wh_to_J = 3600.0
        
        # Low heating values
        self.LHV_NG = 45.4E6 # [J/kg]
        self.LHV_BG = 21.4E6 # [J/kg]
        
        
        # Losses and margins
        self.DCNetworkLoss = 0.05     # Cooling ntw losses (10% --> 0.1) 
        self.DHNetworkLoss = 0.12     # Heating ntw losses
        self.Qmargin_ntw = 0.01       # Reliability margin for the system nominal capacity in the hub
        self.Qloss_Disc = 0.05        # Heat losses within a disconnected building
        self.Qmargin_Disc = 0.20      # Reliability margin for the system nominal capacity for decentralized systems
        self.QminShare = 0.10         # Minimum percentage for the installed capacity
        self.K_DH = 0.25         # linear heat loss coefficient district heting network twin pipes groundfoss
        
        # pipes location properties
        self.Z0 = 1.5         # location of pipe underground in m
        self.Psl = 1600         # heat capacity of ground in kg/m3
        self.Csl = 1300         # heat capacity of ground in J/kg K
        self.Bsl = 1.5         # thermal conductivity of ground in W/m.K    
            
        # Emission and Primary energy factors
        
            ######### Biogas to Agric. Bio Gas emissions
        self.NormalBGToAgriBG_CO2     = 0.127 / 0.754  # Values from Electricity used for comparison
        self.NormalBGToAgriBG_Eprim   = 0.0431 / 0.101 # Values from Electricity used for comparison
        
            ######### CENTRAL HUB PLANT : factor with regard to FINAL ENERGY
            
        #normalized on their efficiency, including all CO2 emissions (Primary, grey, electricity etc. until exit of Hub)
        #usage : divide by system efficiency and Hub to building-efficiency
        self.ETA_FINAL_TO_USEFUL  =  0.9 # assume 90% system efficiency in terms of CO2 emissions and overhead emissions (\
                                    # after Heating systems in buildings %E2%80%94 Method for calculation of system\
                                    # energy requirements and system efficiencies %E2%80%94 Part 4-5 Space heating \
                                    # generation systems, the performance and quality)
                                    
                                    # using HP values, divide by COP and multiply by factor
                                    # susing other systems, divide final energy (what comes out of the pipe) by efficiency multiply by factor
                                    # Furnace: All emissions allocated to the thermal energy, get CO2 of electricity back!
        
        # Combined Cycle                            
        self.CC_sigma     = 4/5
        
        self.NG_CC_TO_CO2_STD     = (0.0353 + 0.186) * 0.78 / self.ETA_FINAL_TO_USEFUL * (1+self.CC_sigma)         # kg_CO2 / MJ_useful
        self.NG_CC_TO_OIL_STD     = (0.6 + 2.94) * 0.78  / self.ETA_FINAL_TO_USEFUL * (1+self.CC_sigma)            # MJ_oil / MJ_useful
        
        if self.FlagBioGasFromAgriculture == 1:
            self.BG_CC_TO_CO2_STD  = (0.00592 + 0.0495)  * 0.78 / self.ETA_FINAL_TO_USEFUL * (1+self.CC_sigma)      # kg_CO2 / MJ_useful
            self.BG_CC_TO_OIL_STD  = (0.0703 + 0.156)  * 0.78  / self.ETA_FINAL_TO_USEFUL * (1+self.CC_sigma)      # MJ_oil / MJ_useful
        
        else:
            self.BG_CC_TO_CO2_STD  = (0.0223 + 0.114) * 0.78 / self.ETA_FINAL_TO_USEFUL * (1+self.CC_sigma)         # kg_CO2 / MJ_useful
            self.BG_CC_TO_OIL_STD  = (0.214 + 0.851)  * 0.78 / self.ETA_FINAL_TO_USEFUL * (1+self.CC_sigma)        # kg_CO2 / MJ_useful
        
        
        # Furnace
        self.FURNACE_TO_CO2_STD   = (0.0104 + 0.0285) * 0.78 / self.ETA_FINAL_TO_USEFUL * (1+self.CC_sigma)           # kg_CO2 / MJ_useful
        self.FURNACE_TO_OIL_STD   = (0.0956 + 0.141) * 0.78  / self.ETA_FINAL_TO_USEFUL * (1+self.CC_sigma)           # MJ_oil / MJ_useful
        
        
        # Boiler
        self.NG_BOILER_TO_CO2_STD  = 0.0874 * 0.87 / self.ETA_FINAL_TO_USEFUL               # kg_CO2 / MJ_useful   
        self.NG_BOILER_TO_OIL_STD  = 1.51 * 0.87  / self.ETA_FINAL_TO_USEFUL                # MJ_oil / MJ_useful   
        
        if self.FlagBioGasFromAgriculture == 1:
            self.BG_BOILER_TO_CO2_STD      = 0.339    * 0.87 * self.NormalBGToAgriBG_CO2 / (1+self.DHNetworkLoss) / self.ETA_FINAL_TO_USEFUL # MJ_oil / MJ_useful   
            self.BG_BOILER_TO_OIL_STD      = 0.04   * 0.87 * self.NormalBGToAgriBG_Eprim / (1+self.DHNetworkLoss) / self.ETA_FINAL_TO_USEFUL # MJ_oil / MJ_useful   
        
        else:
            self.BG_BOILER_TO_CO2_STD      = self.NG_BOILER_TO_CO2_STD * 0.04 / 0.0691   # kg_CO2 / MJ_useful 
            self.BG_BOILER_TO_OIL_STD      = self.NG_BOILER_TO_OIL_STD * 0.339 / 1.16      # MJ_oil / MJ_useful  
        
        
        # HP Lake
        self.LAKEHP_TO_CO2_STD    = 0.0262 * 2.8 / self.ETA_FINAL_TO_USEFUL                   # kg_CO2 / MJ_useful
        self.LAKEHP_TO_OIL_STD    = 1.22 * 2.8  / self.ETA_FINAL_TO_USEFUL                 # MJ_oil / MJ_useful
        
        # HP Sewage
        self.SEWAGEHP_TO_CO2_STD  = 0.0192 * 3.4 / self.ETA_FINAL_TO_USEFUL                   # kg_CO2 / MJ_useful
        self.SEWAGEHP_TO_OIL_STD  = 0.904 * 3.4 / self.ETA_FINAL_TO_USEFUL                 # MJ_oil / MJ_useful
        
        # GHP
        self.GHP_TO_CO2_STD       = 0.0210 * 3.9 / self.ETA_FINAL_TO_USEFUL                   # kg_CO2 / MJ_useful
        self.GHP_TO_OIL_STD       = 1.03 * 3.9 / self.ETA_FINAL_TO_USEFUL                   # MJ_oil / MJ_useful
        
        
            ######### LOCAL PLANT : factor with regard to USEFUL ENERGY
        
        self.NG_BACKUPBOILER_TO_CO2_STD = 0.0691 * 0.87   # kg_CO2 / MJ_useful
        self.BG_BACKUPBOILER_TO_CO2_STD = 0.04 * 0.87     # kg_CO2 / MJ_useful
        self.SMALL_GHP_TO_CO2_STD       = 0.0153 * 3.9    # kg_CO2 / MJ_useful
        #self.SMALL_LAKEHP_TO_CO2_STD    = 0.0211 * 2.8    # kg_CO2 / MJ_useful
        self.SOLARCOLLECTORS_TO_CO2     = 0.00911          # kg_CO2 / MJ_useful
        
        self.NG_BACKUPBOILER_TO_OIL_STD = 1.16 * 0.87     # MJ_oil / MJ_useful
        self.BG_BACKUPBOILER_TO_OIL_STD = 0.339 * 0.87    # MJ_oil / MJ_useful
        self.SMALL_GHP_TO_OIL_STD       = 0.709 * 3.9     # MJ_oil / MJ_useful
        #self.SMALL_LAKEHP_TO_OIL_STD    = 0.969 * 2.8     # MJ_oil / MJ_useful
        self.SOLARCOLLECTORS_TO_OIL     = 0.201           # MJ_oil / MJ_useful
        
        
        
            ######### ELECTRICITY
        self.CC_EL_TO_TOTAL = 4/9
        
        self.EL_TO_OIL_EQ               = 2.69                            # MJ_oil / MJ_final   
        self.EL_TO_CO2               = 0.0385                         # kg_CO2 / MJ_final - CH Verbrauchermix nach EcoBau
        
        self.EL_TO_OIL_EQ_GREEN         = 0.0339                          # MJ_oil / MJ_final   
        self.EL_TO_CO2_GREEN         = 0.00398                        # kg_CO2 / MJ_final
        
        self.EL_NGCC_TO_OIL_EQ_STD      = 2.94 * 0.78 * self.CC_EL_TO_TOTAL             # MJ_oil / MJ_final   
        self.EL_NGCC_TO_CO2_STD          = 0.186 * 0.78     * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
        
        if self.FlagBioGasFromAgriculture == 1: # Use Biogas from Agriculture
            self.EL_BGCC_TO_OIL_EQ_STD      = 0.156 * 0.78    * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
            self.EL_BGCC_TO_CO2_STD      = 0.0495 * 0.78    * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
        else:
            self.EL_BGCC_TO_OIL_EQ_STD      = 0.851 * 0.78     * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
            self.EL_BGCC_TO_CO2_STD      = 0.114 * 0.78     * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
        
        self.EL_FURNACE_TO_OIL_EQ_STD   = 0.141 * 0.78 * self.CC_EL_TO_TOTAL   # MJ_oil / MJ_final   
        self.EL_FURNACE_TO_CO2_STD       = 0.0285 * 0.78    * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
        
        self.EL_PV_TO_OIL_EQ            = 0.345                           # MJ_oil / MJ_final   
        self.EL_PV_TO_CO2                = 0.02640                            # kg_CO2 / MJ_final
        
        
        # Financial Data
        self.EURO_TO_CHF = 1.2
        self.CHF_TO_EURO = 1.0 / self.EURO_TO_CHF
        self.USD_TO_CHF = 0.96 
        self.MWST = 0.08 # 8% MWST assumed, used in A+W data
        
        
        # Resource prices
        self.ELEC_PRICE = 0.104 * self.EURO_TO_CHF / 1000.0  # = 15 Rp/kWh   or  0.104 * EURO_TO_CHF / 1000.0 # [CHF / wh] 
        #self.ELEC_PRICE_KEV = 1.5 * ELEC_PRICE # MAKE RESEARCH ABOUT A PROPER PRICE AND DOCUMENT THAT! 
        #self.ELEC_PRICE_GREEN = 1.5 * ELEC_PRICE
        self.NG_PRICE = 0.057 * self.EURO_TO_CHF / 1000.0 # [CHF / wh]
        self.BG_PRICE = 0.078 * self.EURO_TO_CHF / 1000.0 # [CHF / wh]
        
        self.GasConnectionCost = 15.5 / 1000.0 # CHF / W, from  Energie360 15.5 CHF / kW
        
        if self.ZernezFlag == 1:
            self.NG_PRICE = 0.0756 / 1000.0 # [CHF / wh] from  Energie360
            self.BG_PRICE = 0.162 / 1000.0  # [CHF / wh] from  Energie360
            
        # DCN
        self.TsupCool = 6 + 273
        self.TretCoolMax = 12 + 273.0
        
        # Substation data
        self.mdot_step_counter_heating = [0.05, 0.1, 0.15 ,0.3, 0.4, 0.5 , 0.6, 1]
        self.mdot_step_counter_cooling = [0, 0.2, 0.5, 0.8, 1] 
        self.NetworkLengthReference = 1745.0 #meters of network length of max network. (Reference = Zug Case Study) , from J. Fonseca's Pipes Data
        self.PipeCostPerMeterInv = 660.0 #CHF /m 
        self.PipeLifeTime = 40.0 # years, Data from A&W
        self.PipeInterestRate = 0.05 # 5% interest rate
        self.PipeCostPerMeterAnnual = self.PipeCostPerMeterInv / self.PipeLifeTime

        # Solar area to Wpeak
        self.eta_area_to_peak = 0.16 # Peak Capacity - Efficisency, how much kW per area there are, valid for PV and PVT (after Jimeno's J+) 
        
        # Pressure losses
        #self.DeltaP_DCN = 1.0 #Pa - change 
        #self.DeltaP_DHN = 84.8E3 / 10.0 #Pa  - change
        self.cPump = self.ELEC_PRICE * 24. * 365.# coupled to electricity cost 
        self.PumpEnergyShare = 0.01 #assume 1% of energy required for pumping, after 4DH
        self.PumpReliabilityMargin = 0.05 # assume 5% reliability margin
        
        # Circulating Pump
        self.etaPump = 0.8
        
        # Heat Exchangers
        self.U_cool = 2500 # W/m2K
        self.U_heat = 2500 # W/m2K
        self.dT_heat = 5 # K - pinchdelta at design conditions
        self.dT_cool = 1 # K - pinchdelta at design conditions
        
        # Heat pump
        self.HP_maxSize = 20.0E6 # max thermal design size [Wth]
        self.HP_minSize = 1.0E6 # min thermal design size [Wth]
        self.HP_n = 20.0 # lifetime [years]
        
        self.HP_etaex = 0.6 # exergetic efficiency
        self.HP_deltaT_cond = 2.0 # pinch for condenser [K]
        self.HP_deltaT_evap = 2.0 # pinch for evaporator [K]
        self.HP_maxT_cond = 140+273.0 # max temperature at condenser [K]
        
        self.HP_Auxratio = 0.83 # Wdot_comp / Wdot_total (circulating pumps)
        self.HP_i = 0.05 # interest rate
        
        # Sewage resource
        
        self.Sew_minT = 10+273.0 # minimum temperature at the sewage exit [K]
        
        # Lake resources
        self.DeltaU = 12500.0E6 # [Wh], maximum change in the lake energy content at the end of the year (positive or negative)
        self.TLake = 5 + 273.0 #K 
        
        # Geothermal heat pump
        if self.ZernezFlag == 1:
            self.TGround = 8.0 + 273.0
        
        else:
            self.TGround = 6.5 + 273.0
            
        self.COPScalingFactorGroundWater = 3.4 / 3.9 # Scaling factor according to EcoBau, take GroundWater Heat pump into account
        
        self.GHP_CmaxSize = 2E3 # max cooling design size [Wc] FOR ONE PROBE
        self.GHP_Cmax_Size_th = 2E3 # Wth/m per probe
        self.GHP_Cmax_Length = 40 # depth of exploration taken into account
        
        self.GHP_HmaxSize = 2E3 # max heating design size [Wth] FOR ONE PROBE
        self.GHP_WmaxSize = 1E3 # max electrical design size [Wel] FOR ONE PROBE
        
        self.GHP_nBH = 50.0 # [years] for a borehole
        self.GHP_nHP = 20.0 # for the geothermal heat pump
        
        self.GHP_etaex = 0.677 # exergetic efficiency
        self.GHP_Auxratio = 0.83 # Wdot_comp / Wdot_total (circulating pumps)
        
        self.GHP_i = 0.06 # interest rate
        self.GHP_A = 25 # [m^2] area occupancy of one borehole Gultekin et al. 5 m separation at a penalty of 10% less efficeincy
        
        
        # Combined cycle
        self.CC_n = 25.0 # lifetime
        self.CC_i = 0.06
        
        self.GT_maxSize = 50.00000001E6 # max electrical design size in W = 50MW (NOT THERMAL capacity)
        self.GT_minSize = 0.2E6 # min electrical design size in W = 0.2 MW (NOT THERMAL capacity)
        self.GT_minload = 0.1 * 0.999 # min load (part load regime)
        
        self.CC_exitT_NG = 986.0 # exit temperature of the gas turbine if NG
        self.CC_exitT_BG = 1053.0 # exit temperature of the gas turbine if BG
        self.CC_airratio = 2.0 # air to fuel mass ratio
        
        self.ST_deltaT = 4.0 # pinch for HRSG
        self.ST_deltaP = 5.0E5 # pressure loss between steam turbine and DHN
        self.CC_deltaT_DH = 5.0 # pinch for condenser
        
        self.STGen_eta = 0.9 # generator efficiency after steam turbine
        self.CC_Maintenance_per_kWhel = 0.03 * self.EURO_TO_CHF # 0.03 € / kWh_el after Weber 2008, used in Slave Cost Calculation
        
        
        # Boiler
            # Operating figures, quality parameters and investment costs for district heating systems (AFO)
        
        self.Boiler_n = 20.0 # lifetime, after A+W, confirmed by average of 15-25y range after http://www.elco.ch/pdf/Solutions/ \ 
                        # ELCO-Loesungsbeispiel-Huber.pdf
        self.Boiler_i = 0.05 # interest rate
        self.Boiler_C_fuel = 20.0 # € / MWh_therm_bought(for LHV), AFO
        self.Boiler_C_labour = 4.0 # [€ /MWh_therm_sold]
        self.Boiler_P_aux = 0.026 # 0.026 Wh/Wh_th_sold = 26 kWh_el / MWh_th_sold, bioenergy 2020
        self.Boiler_min = 0.05  # minimum Part Load of Boiler
        self.Boiler_equ_ratio = 0.2 # 20% own capital required (equity ratio) 
        self.Boiler_C_maintainance = 0.05 # 5 % of capital cost (3% boiler, 2% techn. facilities) by AFO, currently not used
        #Boiler_C_maintainance_fazNG = 3.5  /1E6 * EURO_TO_CHF # 3.5 Euro  /MWh_th 
        #Boiler_C_maintainance_fazBG = 10.4 /1E6 * EURO_TO_CHF # 10.4 Euro /MWh_th 
        self.Boiler_C_maintainance_faz = 3.5
        self.Boiler_eta_hp = 0.9
        
        
        # Furnace
        self.Furn_FuelCost_wet = 0.057 *1E-3  # CHF / Wh = 5.7 Rp / kWh for wet (50wt%) Wood Chips, after 
        self.Furn_FuelCost_dry = 0.07 * 1E-3 # CHF / Wh = 7 Rp / kWh for dry (30wt%) Wood Chips, 
        self.Furn_min_Load = 0.2  # Minimum load possible (does not affect Model itself!)
        self.Furn_min_electric = 0.3 # Minimum load for electricity generation in furnace plant
        
        # Substation Heat Exchangers
        self.Subst_n = 25.0 # Lifetime after A+W
        self.Subst_i = 0.05
        
        # Fuel Cells
        self.FC_OP_HOURS_PER_YEAR = 4000.0 # hours / year
        self.FC_LIFETIME = 40000.0  # hours of operation
        self.FC_n = 10 # years of operation
        self.FC_i = 0.05 # interest rate
        self.FC_stack_cost = 55000.0 # CHF /kW_th for a Hexis 1000 N 1kWe/1.8kWth
        self.FC_overhead = 0.1 # 10 % higher cost due to final installation 
        
        # Vapor compressor chiller
        self.VCC_maxSize = 3500.0E3 # maximum size [W]
        self.VCC_n = 25.0 # service life
        self.VCC_tcoolin = 30 + 273.0 # entering condenser water temperature [K]
        self.VCC_minload = 0.1 # min load for cooling power
        
        
        # Cooling tower
        self.CT_maxSize = 10.0E6 # cooling power desin size [W]
        self.CT_n = 20.0
        self.CT_a = 0.15 # annuity factor
        
        # Storage
        self.T_storage_min = 10 + 273.0 # K  - Minimum Storage Temperature
        self.StorageMaxUptakeLimitFlag = 1 #set a maximum for the HP Power for storage charging / decharging
        self.QtoStorageMax = 1e6 #100kW maximum peak 
        
        # Activation Order of Power Plants
        # solar sources are treated first
        self.act_first = 'HP' # accounts for all kind of HP's as only one will be in the system. 
        self.act_second = 'CHP' #accounts for ORC and NG-RC (produce electricity!)
        self.act_third = 'BoilerBase' # all conventional boilers are considered to be backups.
        self.act_fourth = 'BoilerPeak' # additional Peak Boiler
        
        # Data for Evolutionary algorithm
        self.nHeat = 6 # number of heating 
        self.nHR = 2
        self.nSolar = 3
        
        self.PROBA = 0.5
        self.SIGMAP = 0.2
        self.epsMargin = 0.001     
        
        
        # Data for clustering
        self.nPeriodMin = 2
        self.nPeriodMax = 15
        self.gam = 0.2
        self.threshErr = 0.2
        
        
        # Heat Recovery
        
            # compressed Air recovery 
        self.etaElToHeat = 0.75 # [-]
        self.TElToHeatSup = 80 + 273.0 #K
        self.TElToHeatRet = 70 + 273.0 #K
        
            # Server Waste Heat recovery
        self.etaServerToHeat = 0.8 # [-]
        self.TfromServer = 60 + 273.0 #K
        self.TtoServer = 55 + 273.0 #K
        
        
        # Solar Thermal: information of return temperature
        self.TsupplyPVT_35 = 35 + 273.0 # K 
        self.TsupplySC_80 = 75 + 273.0 # K
        self.TsupplySC_ET50 = 50 + 273.0 # K
        self.TsupplySC_ET80  = 80 + 273.0 # K 

        # solar PV and PVT
        self.nPV = 0.16
        self.nPVT = 0.16
        
    

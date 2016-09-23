# -*- coding: utf-8 -*-
"""
================
Global variables
================

"""

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

class GlobalVariables(object):
    def __init__(self):
        self.scenario_reference = r'c:\reference-case-zug\baseline'
        self.date_start = '2010-01-01'  # format: yyyy-mm-dd
        self.seasonhours = [3216, 6192]
        self.multiprocessing = True # use multiprocessing / parallel execution if possible
        self.Z = 3  # height of basement for every building in m
        self.Bf = 0.7  # it calculates the coefficient of reduction in transmittance for surfaces in contact with the ground according to values of SIA 380/1
        self.his = 3.45  # heat transfer coefficient between air and the surfacein W/(m2K)
        self.hms = 9.1  # heat transfer coefficient between nodes m and s in W/m2K
        self.g_gl = 0.9 * 0.75  # solar energy transmittance assuming a reduction factor of 0.9 and most of the windows due to double glazing (0.75)
        self.F_f = 0.3  # Frame area faction coefficient
        self.D = 20  # in mm the diameter of the pipe to calculate losses
        self.hf = 3  # average height per floor in m
        self.Pwater = 998  # water density kg/m3
        self.PaCa = 1200  # Air constant J/m3K 
        self.Cpw = 4.184  # heat capacity of water in kJ/kgK
        self.Flowtap = 0.036  # in m3/min == 12 l/min during 3 min every tap opening
        # constant values for HVAC
        self.nrec_N = 0.75  # possilbe recovery
        self.NACH_inf_non_occ = 0.2  # num air exchanges due to infiltration when no occupied
        self.NACH_inf_occ = 0.5  # num air exchanges due to infiltration when occupied
        self.C1 = 0.054  # assumed a flat plate heat exchanger (-)
        self.Vmax = 3  # maximum estimated flow in m3/s
        self.Pair = 1.2  # air density in kg/m3
        self.Cpv = 1.859  # specific heat capacity of water vapor in KJ/kgK
        self.Cpa = 1.008  # specific heat capacity of air in KJ/kgK
        self.U_dhwtank = 0.225  # tank insulation heat transfer coefficient in W/m2-K, value taken from SIA 385
        self.AR = 3.3  # tank height aspect ratio, H=(4*V*AR^2/pi)^(1/3), taken from commercial tank geometry (jenni.ch)
        self.lvapor = 2257  # latent heat of air kJ/kg
        self.Tww_setpoint = 60  # dhw tank set point temperature in C
        # constant variables for pumping operation
        self.hoursop = 5  # assuming around 2000 hours of operation per year. It is charged to the electrical system from 11 am to 4 pm
        self.gr = 9.81  # m/s2 gravity
        self.effi = 0.6  # efficiency of pumps
        self.deltaP_l = 0.1  # delta of pressure
        self.fsr = 0.3  # factor for pressure calculation
        # grey emssions
        self.fwratio = 1.5  # conversion component's area to floor area
        self.sl_materials = 60  # service life of standard building components and materials
        self.sl_services = 40  # service life of technical instalations
        # constant variables for air conditioning fan
        self.Pfan = 0.55 # specific fan consumption in W/m3/h

        # ==============================================================================================================
        # optimization
        # ==============================================================================================================

        self.sensibilityStep = 2 #the more, the longer the sensitibility analysis
        ########################### User inputs

        # Commands for the evolutionary algorithm

        self.initialInd = 3  # number of initial individuals
        self.NGEN = 3000  # number of total generations
        self.fCheckPoint = 1  # frequency for the saving of checkpoints
        self.maxTime = 7 * 24 * 3600  # maximum computional time [seconds]

        # Set Flags for different system setup preferences

        # self.NetworkLengthZernez = 864.0 #meters network length of maximum network, \
        # then scaled by number of costumers (Zernez Specific), from J.Fonseca's PipsesData

        self.ZernezFlag = 0
        self.FlagBioGasFromAgriculture = 0  # 1 = Biogas from Agriculture, 0 = Biogas normal
        self.HPSew_allowed = 1
        self.HPLake_allowed = 1
        self.GHP_allowed = 1
        self.CC_allowed = 1
        self.Furnace_allowed = 0
        self.DiscGHPFlag = 1  # Is geothermal allowed in disconnected buildings? 0 = NO ; 1 = YES
        self.DiscBioGasFlag = 0  # 1 = use Biogas only in Disconnected Buildings, no Natural Gas; 0so = both possible

        # Values for the calculation of Delta P (from F. Muller network optimization code)
        # WARNING : current = values for Inducity SQ
        self.DeltaP_Coeff = 104.81
        self.DeltaP_Origin = 59016

        ########################### Model parameters

        # Date data
        self.DAYS_IN_YEAR = 365
        self.HOURS_IN_DAY = 24

        # Specific heat
        self.cp = 4185  # [J/kg K]
        self.rho_60 = 983.21  # [kg/m^3] density of Water @ 60°C
        self.Wh_to_J = 3600.0

        # Low heating values
        self.LHV_NG = 45.4E6  # [J/kg]
        self.LHV_BG = 21.4E6  # [J/kg]

        # Losses and margins
        self.DCNetworkLoss = 0.05  # Cooling ntw losses (10% --> 0.1)
        self.DHNetworkLoss = 0.12  # Heating ntw losses
        self.Qmargin_ntw = 0.01  # Reliability margin for the system nominal capacity in the hub
        self.Qloss_Disc = 0.05  # Heat losses within a disconnected building
        self.Qmargin_Disc = 0.20  # Reliability margin for the system nominal capacity for decentralized systems
        self.QminShare = 0.10  # Minimum percentage for the installed capacity
        self.K_DH = 0.25  # linear heat loss coefficient district heting network twin pipes groundfoss

        # pipes location properties
        self.Z0 = 1.5  # location of pipe underground in m
        self.Psl = 1600  # heat capacity of ground in kg/m3
        self.Csl = 1300  # heat capacity of ground in J/kg K
        self.Bsl = 1.5  # thermal conductivity of ground in W/m.K

        # Emission and Primary energy factors

        ######### Biogas to Agric. Bio Gas emissions
        self.NormalBGToAgriBG_CO2 = 0.127 / 0.754  # Values from Electricity used for comparison
        self.NormalBGToAgriBG_Eprim = 0.0431 / 0.101  # Values from Electricity used for comparison

        ######### CENTRAL HUB PLANT : factor with regard to FINAL ENERGY

        # normalized on their efficiency, including all CO2 emissions (Primary, grey, electricity etc. until exit of Hub)
        # usage : divide by system efficiency and Hub to building-efficiency
        self.ETA_FINAL_TO_USEFUL = 0.9  # assume 90% system efficiency in terms of CO2 emissions and overhead emissions (\
        # after Heating systems in buildings %E2%80%94 Method for calculation of system\
        # energy requirements and system efficiencies %E2%80%94 Part 4-5 Space heating \
        # generation systems, the performance and quality)

        # using HP values, divide by COP and multiply by factor
        # susing other systems, divide final energy (what comes out of the pipe) by efficiency multiply by factor
        # Furnace: All emissions allocated to the thermal energy, get CO2 of electricity back!

        # Combined Cycle
        self.CC_sigma = 4 / 5

        self.NG_CC_TO_CO2_STD = (0.0353 + 0.186) * 0.78 / self.ETA_FINAL_TO_USEFUL * (
        1 + self.CC_sigma)  # kg_CO2 / MJ_useful
        self.NG_CC_TO_OIL_STD = (0.6 + 2.94) * 0.78 / self.ETA_FINAL_TO_USEFUL * (
        1 + self.CC_sigma)  # MJ_oil / MJ_useful

        if self.FlagBioGasFromAgriculture == 1:
            self.BG_CC_TO_CO2_STD = (0.00592 + 0.0495) * 0.78 / self.ETA_FINAL_TO_USEFUL * (
            1 + self.CC_sigma)  # kg_CO2 / MJ_useful
            self.BG_CC_TO_OIL_STD = (0.0703 + 0.156) * 0.78 / self.ETA_FINAL_TO_USEFUL * (
            1 + self.CC_sigma)  # MJ_oil / MJ_useful

        else:
            self.BG_CC_TO_CO2_STD = (0.0223 + 0.114) * 0.78 / self.ETA_FINAL_TO_USEFUL * (
            1 + self.CC_sigma)  # kg_CO2 / MJ_useful
            self.BG_CC_TO_OIL_STD = (0.214 + 0.851) * 0.78 / self.ETA_FINAL_TO_USEFUL * (
            1 + self.CC_sigma)  # kg_CO2 / MJ_useful

        # Furnace
        self.FURNACE_TO_CO2_STD = (0.0104 + 0.0285) * 0.78 / self.ETA_FINAL_TO_USEFUL * (
        1 + self.CC_sigma)  # kg_CO2 / MJ_useful
        self.FURNACE_TO_OIL_STD = (0.0956 + 0.141) * 0.78 / self.ETA_FINAL_TO_USEFUL * (
        1 + self.CC_sigma)  # MJ_oil / MJ_useful

        # Boiler
        self.NG_BOILER_TO_CO2_STD = 0.0874 * 0.87 / self.ETA_FINAL_TO_USEFUL  # kg_CO2 / MJ_useful
        self.NG_BOILER_TO_OIL_STD = 1.51 * 0.87 / self.ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful

        if self.FlagBioGasFromAgriculture == 1:
            self.BG_BOILER_TO_CO2_STD = 0.339 * 0.87 * self.NormalBGToAgriBG_CO2 / (
            1 + self.DHNetworkLoss) / self.ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful
            self.BG_BOILER_TO_OIL_STD = 0.04 * 0.87 * self.NormalBGToAgriBG_Eprim / (
            1 + self.DHNetworkLoss) / self.ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful

        else:
            self.BG_BOILER_TO_CO2_STD = self.NG_BOILER_TO_CO2_STD * 0.04 / 0.0691  # kg_CO2 / MJ_useful
            self.BG_BOILER_TO_OIL_STD = self.NG_BOILER_TO_OIL_STD * 0.339 / 1.16  # MJ_oil / MJ_useful

        # HP Lake
        self.LAKEHP_TO_CO2_STD = 0.0262 * 2.8 / self.ETA_FINAL_TO_USEFUL  # kg_CO2 / MJ_useful
        self.LAKEHP_TO_OIL_STD = 1.22 * 2.8 / self.ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful

        # HP Sewage
        self.SEWAGEHP_TO_CO2_STD = 0.0192 * 3.4 / self.ETA_FINAL_TO_USEFUL  # kg_CO2 / MJ_useful
        self.SEWAGEHP_TO_OIL_STD = 0.904 * 3.4 / self.ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful

        # GHP
        self.GHP_TO_CO2_STD = 0.0210 * 3.9 / self.ETA_FINAL_TO_USEFUL  # kg_CO2 / MJ_useful
        self.GHP_TO_OIL_STD = 1.03 * 3.9 / self.ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful

        ######### LOCAL PLANT : factor with regard to USEFUL ENERGY

        self.NG_BACKUPBOILER_TO_CO2_STD = 0.0691 * 0.87  # kg_CO2 / MJ_useful
        self.BG_BACKUPBOILER_TO_CO2_STD = 0.04 * 0.87  # kg_CO2 / MJ_useful
        self.SMALL_GHP_TO_CO2_STD = 0.0153 * 3.9  # kg_CO2 / MJ_useful
        # self.SMALL_LAKEHP_TO_CO2_STD    = 0.0211 * 2.8    # kg_CO2 / MJ_useful
        self.SOLARCOLLECTORS_TO_CO2 = 0.00911  # kg_CO2 / MJ_useful

        self.NG_BACKUPBOILER_TO_OIL_STD = 1.16 * 0.87  # MJ_oil / MJ_useful
        self.BG_BACKUPBOILER_TO_OIL_STD = 0.339 * 0.87  # MJ_oil / MJ_useful
        self.SMALL_GHP_TO_OIL_STD = 0.709 * 3.9  # MJ_oil / MJ_useful
        # self.SMALL_LAKEHP_TO_OIL_STD    = 0.969 * 2.8     # MJ_oil / MJ_useful
        self.SOLARCOLLECTORS_TO_OIL = 0.201  # MJ_oil / MJ_useful

        ######### ELECTRICITY
        self.CC_EL_TO_TOTAL = 4 / 9

        self.EL_TO_OIL_EQ = 2.69  # MJ_oil / MJ_final
        self.EL_TO_CO2 = 0.0385  # kg_CO2 / MJ_final - CH Verbrauchermix nach EcoBau

        self.EL_TO_OIL_EQ_GREEN = 0.0339  # MJ_oil / MJ_final
        self.EL_TO_CO2_GREEN = 0.00398  # kg_CO2 / MJ_final

        self.EL_NGCC_TO_OIL_EQ_STD = 2.94 * 0.78 * self.CC_EL_TO_TOTAL  # MJ_oil / MJ_final
        self.EL_NGCC_TO_CO2_STD = 0.186 * 0.78 * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final

        if self.FlagBioGasFromAgriculture == 1:  # Use Biogas from Agriculture
            self.EL_BGCC_TO_OIL_EQ_STD = 0.156 * 0.78 * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
            self.EL_BGCC_TO_CO2_STD = 0.0495 * 0.78 * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
        else:
            self.EL_BGCC_TO_OIL_EQ_STD = 0.851 * 0.78 * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
            self.EL_BGCC_TO_CO2_STD = 0.114 * 0.78 * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final

        self.EL_FURNACE_TO_OIL_EQ_STD = 0.141 * 0.78 * self.CC_EL_TO_TOTAL  # MJ_oil / MJ_final
        self.EL_FURNACE_TO_CO2_STD = 0.0285 * 0.78 * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final

        self.EL_PV_TO_OIL_EQ = 0.345  # MJ_oil / MJ_final
        self.EL_PV_TO_CO2 = 0.02640  # kg_CO2 / MJ_final

        # Financial Data
        self.EURO_TO_CHF = 1.2
        self.CHF_TO_EURO = 1.0 / self.EURO_TO_CHF
        self.USD_TO_CHF = 0.96
        self.MWST = 0.08  # 8% MWST assumed, used in A+W data

        # Resource prices
        self.ELEC_PRICE = 0.104 * self.EURO_TO_CHF / 1000.0  # = 15 Rp/kWh   or  0.104 * EURO_TO_CHF / 1000.0 # [CHF / wh]
        # self.ELEC_PRICE_KEV = 1.5 * ELEC_PRICE # MAKE RESEARCH ABOUT A PROPER PRICE AND DOCUMENT THAT!
        # self.ELEC_PRICE_GREEN = 1.5 * ELEC_PRICE
        self.NG_PRICE = 0.057 * self.EURO_TO_CHF / 1000.0  # [CHF / wh]
        self.BG_PRICE = 0.078 * self.EURO_TO_CHF / 1000.0  # [CHF / wh]

        self.GasConnectionCost = 15.5 / 1000.0  # CHF / W, from  Energie360 15.5 CHF / kW

        if self.ZernezFlag == 1:
            self.NG_PRICE = 0.0756 / 1000.0  # [CHF / wh] from  Energie360
            self.BG_PRICE = 0.162 / 1000.0  # [CHF / wh] from  Energie360

        # DCN
        self.TsupCool = 6 + 273
        self.TretCoolMax = 12 + 273.0

        # Substation data
        self.mdot_step_counter_heating = [0.05, 0.1, 0.15, 0.3, 0.4, 0.5, 0.6, 1]
        self.mdot_step_counter_cooling = [0, 0.2, 0.5, 0.8, 1]
        self.NetworkLengthReference = 1745.0  # meters of network length of max network. (Reference = Zug Case Study) , from J. Fonseca's Pipes Data
        self.PipeCostPerMeterInv = 660.0  # CHF /m
        self.PipeLifeTime = 40.0  # years, Data from A&W
        self.PipeInterestRate = 0.05  # 5% interest rate
        self.PipeCostPerMeterAnnual = self.PipeCostPerMeterInv / self.PipeLifeTime

        # Solar area to Wpeak
        self.eta_area_to_peak = 0.16  # Peak Capacity - Efficisency, how much kW per area there are, valid for PV and PVT (after Jimeno's J+)

        # Pressure losses
        # self.DeltaP_DCN = 1.0 #Pa - change
        # self.DeltaP_DHN = 84.8E3 / 10.0 #Pa  - change
        self.cPump = self.ELEC_PRICE * 24. * 365.  # coupled to electricity cost
        self.PumpEnergyShare = 0.01  # assume 1% of energy required for pumping, after 4DH
        self.PumpReliabilityMargin = 0.05  # assume 5% reliability margin

        # Circulating Pump
        self.etaPump = 0.8

        # Heat Exchangers
        self.U_cool = 2500  # W/m2K
        self.U_heat = 2500  # W/m2K
        self.dT_heat = 5  # K - pinchdelta at design conditions
        self.dT_cool = 1  # K - pinchdelta at design conditions

        # Heat pump
        self.HP_maxSize = 20.0E6  # max thermal design size [Wth]
        self.HP_minSize = 1.0E6  # min thermal design size [Wth]
        self.HP_n = 20.0  # lifetime [years]

        self.HP_etaex = 0.6  # exergetic efficiency
        self.HP_deltaT_cond = 2.0  # pinch for condenser [K]
        self.HP_deltaT_evap = 2.0  # pinch for evaporator [K]
        self.HP_maxT_cond = 140 + 273.0  # max temperature at condenser [K]

        self.HP_Auxratio = 0.83  # Wdot_comp / Wdot_total (circulating pumps)
        self.HP_i = 0.05  # interest rate

        # Sewage resource

        self.Sew_minT = 10 + 273.0  # minimum temperature at the sewage exit [K]

        # Lake resources
        self.DeltaU = 12500.0E6  # [Wh], maximum change in the lake energy content at the end of the year (positive or negative)
        self.TLake = 5 + 273.0  # K

        # Geothermal heat pump

        self.TGround = 6.5 + 273.0

        self.COPScalingFactorGroundWater = 3.4 / 3.9  # Scaling factor according to EcoBau, take GroundWater Heat pump into account

        self.GHP_CmaxSize = 2E3  # max cooling design size [Wc] FOR ONE PROBE
        self.GHP_Cmax_Size_th = 2E3  # Wth/m per probe
        self.GHP_Cmax_Length = 40  # depth of exploration taken into account

        self.GHP_HmaxSize = 2E3  # max heating design size [Wth] FOR ONE PROBE
        self.GHP_WmaxSize = 1E3  # max electrical design size [Wel] FOR ONE PROBE

        self.GHP_nBH = 50.0  # [years] for a borehole
        self.GHP_nHP = 20.0  # for the geothermal heat pump

        self.GHP_etaex = 0.677  # exergetic efficiency
        self.GHP_Auxratio = 0.83  # Wdot_comp / Wdot_total (circulating pumps)

        self.GHP_i = 0.06  # interest rate
        self.GHP_A = 25  # [m^2] area occupancy of one borehole Gultekin et al. 5 m separation at a penalty of 10% less efficeincy

        # Combined cycle
        self.CC_n = 25.0  # lifetime
        self.CC_i = 0.06

        self.GT_maxSize = 50.00000001E6  # max electrical design size in W = 50MW (NOT THERMAL capacity)
        self.GT_minSize = 0.2E6  # min electrical design size in W = 0.2 MW (NOT THERMAL capacity)
        self.GT_minload = 0.1 * 0.999  # min load (part load regime)

        self.CC_exitT_NG = 986.0  # exit temperature of the gas turbine if NG
        self.CC_exitT_BG = 1053.0  # exit temperature of the gas turbine if BG
        self.CC_airratio = 2.0  # air to fuel mass ratio

        self.ST_deltaT = 4.0  # pinch for HRSG
        self.ST_deltaP = 5.0E5  # pressure loss between steam turbine and DHN
        self.CC_deltaT_DH = 5.0  # pinch for condenser

        self.STGen_eta = 0.9  # generator efficiency after steam turbine
        self.CC_Maintenance_per_kWhel = 0.03 * self.EURO_TO_CHF  # 0.03 € / kWh_el after Weber 2008, used in Slave Cost Calculation

        # Boiler
        # Operating figures, quality parameters and investment costs for district heating systems (AFO)

        self.Boiler_n = 20.0  # lifetime, after A+W, confirmed by average of 15-25y range after http://www.elco.ch/pdf/Solutions/ \
        # ELCO-Loesungsbeispiel-Huber.pdf
        self.Boiler_i = 0.05  # interest rate
        self.Boiler_C_fuel = 20.0  # € / MWh_therm_bought(for LHV), AFO
        self.Boiler_C_labour = 4.0  # [€ /MWh_therm_sold]
        self.Boiler_P_aux = 0.026  # 0.026 Wh/Wh_th_sold = 26 kWh_el / MWh_th_sold, bioenergy 2020
        self.Boiler_min = 0.05  # minimum Part Load of Boiler
        self.Boiler_equ_ratio = 0.2  # 20% own capital required (equity ratio)
        self.Boiler_C_maintainance = 0.05  # 5 % of capital cost (3% boiler, 2% techn. facilities) by AFO, currently not used
        # Boiler_C_maintainance_fazNG = 3.5  /1E6 * EURO_TO_CHF # 3.5 Euro  /MWh_th
        # Boiler_C_maintainance_fazBG = 10.4 /1E6 * EURO_TO_CHF # 10.4 Euro /MWh_th
        self.Boiler_C_maintainance_faz = 3.5
        self.Boiler_eta_hp = 0.9

        # Furnace
        self.Furn_FuelCost_wet = 0.057 * 1E-3  # CHF / Wh = 5.7 Rp / kWh for wet (50wt%) Wood Chips, after
        self.Furn_FuelCost_dry = 0.07 * 1E-3  # CHF / Wh = 7 Rp / kWh for dry (30wt%) Wood Chips,
        self.Furn_min_Load = 0.2  # Minimum load possible (does not affect Model itself!)
        self.Furn_min_electric = 0.3  # Minimum load for electricity generation in furnace plant

        # Substation Heat Exchangers
        self.Subst_n = 25.0  # Lifetime after A+W
        self.Subst_i = 0.05

        # Fuel Cells
        self.FC_OP_HOURS_PER_YEAR = 4000.0  # hours / year
        self.FC_LIFETIME = 40000.0  # hours of operation
        self.FC_n = 10  # years of operation
        self.FC_i = 0.05  # interest rate
        self.FC_stack_cost = 55000.0  # CHF /kW_th for a Hexis 1000 N 1kWe/1.8kWth
        self.FC_overhead = 0.1  # 10 % higher cost due to final installation

        # Vapor compressor chiller
        self.VCC_maxSize = 3500.0E3  # maximum size [W]
        self.VCC_n = 25.0  # service life
        self.VCC_tcoolin = 30 + 273.0  # entering condenser water temperature [K]
        self.VCC_minload = 0.1  # min load for cooling power

        # Cooling tower
        self.CT_maxSize = 10.0E6  # cooling power desin size [W]
        self.CT_n = 20.0
        self.CT_a = 0.15  # annuity factor

        # Storage
        self.T_storage_min = 10 + 273.0  # K  - Minimum Storage Temperature
        self.StorageMaxUptakeLimitFlag = 1  # set a maximum for the HP Power for storage charging / decharging
        self.QtoStorageMax = 1e6  # 100kW maximum peak

        # Activation Order of Power Plants
        # solar sources are treated first
        self.act_first = 'HP'  # accounts for all kind of HP's as only one will be in the system.
        self.act_second = 'CHP'  # accounts for ORC and NG-RC (produce electricity!)
        self.act_third = 'BoilerBase'  # all conventional boilers are considered to be backups.
        self.act_fourth = 'BoilerPeak'  # additional Peak Boiler

        # Data for Evolutionary algorithm
        self.nHeat = 6  # number of heating
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
        self.etaElToHeat = 0.75  # [-]
        self.TElToHeatSup = 80 + 273.0  # K
        self.TElToHeatRet = 70 + 273.0  # K

        # Server Waste Heat recovery
        self.etaServerToHeat = 0.8  # [-]
        self.TfromServer = 60 + 273.0  # K
        self.TtoServer = 55 + 273.0  # K

        # Solar Thermal: information of return temperature
        self.TsupplyPVT_35 = 35 + 273.0  # K
        self.TsupplySC_80 = 75 + 273.0  # K
        self.TsupplySC_ET50 = 50 + 273.0  # K
        self.TsupplySC_ET80 = 80 + 273.0  # K

        # solar PV and PVT
        self.nPV = 0.16
        self.nPVT = 0.16

        # ==============================================================================================================
        # solar thermal collector
        # ==============================================================================================================

        self.Tin = 75  # average temeperature
        self.module_lenght_SC = 2  # m # 1 for PV and 2 for solar collectors
        self.min_production = 0.75  # points are selected with at least a minimum production of this % from the maximum in the area.
        self.grid_side = 2  # in a rectangular grid of points, one side of the square. this cannot be changed if the solra potential was made with this.
        self.worst_hour = 8744  # first hour of sun on the solar solstice
        self.angle_north = 122.5
        self.type_SCpanel = 1  # Flatplate collector

        # ==============================================================================================================
        # PV panel
        # ==============================================================================================================

        self.module_lenght_PV = 1 # m # 1 for PV and 2 for solar collectors
        self.min_production = 0.75  # points are selected with at least a minimum production of this % from the maximum in the area.
        self.type_PVpanel = 1  # monocrystalline
        self.misc_losses = 0.1 #cabling, resistances etc..

        # ==============================================================================================================
        # sewage potential
        # ==============================================================================================================

        self.SW_ratio = 0.95  # ratio of waste water to fresh water production.
        self.width_HEX = 0.40  # in m
        self.Vel_flow = 3  # in m/s
        self.min_flow = 9  # in lps
        self.tmin = 8  # tmin of extraction
        self.h0 = 1.5  # kW/m2K # heat trasnfer coefficient/
        self.AT_HEX = 5
        self.ATmin = 2

        # ==============================================================================================================
        # ventilation
        # ==============================================================================================================
        self.shielding_class = 2  # according to ISO 16798-7, 0 = open terrain, 1 = partly shielded from wind,
        #  2 = fully shielded from wind
        self.delta_p_dim = 5  # (Pa) dimensioning differential pressure for multi-storey building shielded from wind,
        # according to DIN 1946-6

        # ==============================================================================================================
        # HVAC
        # ==============================================================================================================
        self.temp_sup_heat_hvac = 36  # (°C)
        self.temp_sup_cool_hvac = 16  # (°C)

        # ==============================================================================================================
        # Comfort
        # ==============================================================================================================
        self.temp_comf_max = 26  # (°C) TODO: include to building properties and get from building properties
        self.rhum_comf_max = 70  # (%)

        # ==============================================================================================================
        # Initial temperatures for demand calculation
        # ==============================================================================================================
        self.initial_temp_air_prev = 21
        self.initial_temp_m_prev = 16

        # ==============================================================================================================
        # Columns to write for the demand calculation
        # ==============================================================================================================
        self.demand_totals_csv_columns = ['Name', 'Af_m2', 'Aroof_m2', 'GFA_m2', 'occ_pax', 'QHf_MWhyr', 'QCf_MWhyr',
                                          'Ef_MWhyr', 'Qhsf0_kW', 'Qhsf_MWhyr', 'Qhs_MWhyr', 'Qhs_lat_MWhyr', 'Qwwf0_kW', 'Qwwf_MWhyr',
                                          'Qww_MWhyr', 'Qhprof_MWhyr', 'Qcsf0_kW', 'Qcsf_MWhyr', 'Qcs_MWhyr', 'Qcs_lat_MWhyr',
                                          'Qcref_MWhyr', 'Qcdataf_MWhyr', 'Ealf0_kW', 'Ealf_MWhyr', 'Eauxf_MWhyr',
                                          'Ecaf_MWhyr', 'Edataf_MWhyr', 'Eprof_MWhyr', 'Tshs0_C', 'Trhs0_C', 'Tscs0_C',
                                          'Trcs0_C', 'Tsww0_C', 'Vw_m3yr', 'Vww0_m3', 'Vww_m3yr', 'mcphs0_kWC',
                                          'mcpww0_kWC', 'mcpcs0_kWC']
        self.demand_building_csv_columns = ['DATE', 'Name', 'occ_pax', 'QHf_kWh', 'QCf_kWh', 'Ef_kWh', 'Qhsf_kWh',
                                            'Qhs_kWh', 'Qhs_lat_kWh', 'Qhprof_kWh', 'Qwwf_kWh', 'Qww_kWh',
                                            'Qcsf_kWh', 'Qcs_kWh', 'Qcs_lat_kWh', 'Qcref_kWh', 'Qcdataf_kWh', 'Ealf_kWh', 'Eauxf_kWh',
                                            'Ecaf_kWh', 'Edataf_kWh', 'Eprof_kWh', 'Tshs_C', 'Trhs_C', 'Tscs_C',
                                            'Trcs_C', 'Tsww_C', 'Trww_C', 'Tsref_C', 'Trref_C',
                                            'Tsdata_C', 'Trdata_C', 'Vw_m3', 'mcphs_kWC', 'mcpww_kWC', 'mcpcs_kWC',
                                            'mcpref_kWC', 'mcpdata_kWC']
        # here is where we decide whether full excel reports of the calculations are generated
        self.testing = False  # if true: reports are generated, if false: not


        self.report_variables = {
            'calc-thermal-loads': {
                'Building properties':
                    ['Name',                'Af',                   'Aef',          'sys_e_heating',
                     'sys_e_cooling',       'Occupants',            'Am',           'Atot',
                     'Awall_all',           'Cm',                   'Ll',           'Lw',
                     'Retrofit',            'Sh_typ',               'Year',         'footprint',
                     'nf_ag',               'nfp',                  'Lcww_dis',     'Lsww_dis',
                     'Lv',                  'Lvww_dis',             'Tcs_re_0',     'Tcs_sup_0',
                     'Ths_re_0',            'Ths_sup_0',            'Tww_re_0',     'Tww_sup_0',
                     'Y',                   'fforma'],
                'Thermal loads hourly':
                    ['ta_hs_set',           'ta_cs_set',            'people',       've',
                     'q_int',               'Eal_nove',             'Eprof',        'Edata',
                     'Qcdataf',             'Qcrefrif',             'vww',          'vw',
                     'Qcdata',              'Qcrefri',              'qv_req',       'Hve',
                     'Htr_is',              'Htr_ms',               'Htr_w',        'Htr_em',
                     'Htr_1',               'Htr_2',                'Htr_3',        'I_sol',
                     'I_int_sen',           'w_int',                'I_ia',         'I_m',
                     'I_st',                'uncomfort',            'Ta',           'Tm',
                     'Qhs_sen',             'Qcs_sen',              'Qhs_lat',      'Qcs_lat',
                     'Qhs_em_ls',           'Qcs_em_ls',            'QHC_sen',      'ma_sup_hs',
                     'Ta_sup_hs',           'Ta_re_hs',             'ma_sup_cs',    'Ta_sup_cs',
                     'Ta_re_cs',            'w_sup',                'w_re',         'Ehs_lat_aux',
                     'Qhs_sen_incl_em_ls',  'Qcs_sen_incl_em_ls',   't5',           'Tww_re',
                     'Top',                 'Im_tot',               'tHset_corr',   'tCset_corr',
                     'Tcs_re',              'Tcs_sup','Ths_re',     'Ths_sup',      'mcpcs',
                     'mcphs',               'Mww',                  'Qww',          'Qww_ls_st',
                     'Qwwf',                'Tww_st',               'Vw',           'Vww',
                     'mcpww',               'Eaux_cs',              'Eaux_fw',      'Eaux_ve',
                     'Eaux_ww',             'Eauxf',                'Occupancy',    'Waterconsumption']},
            'other-module-that-needs-logging': {'worksheet1': ['v1', 'v2', 'v3'],
                                                #'worksheet2': [('v4', 'm'), ('v5', 'Mwh'), ('v6', 'MJ')]}}
                                                'worksheet2': ['v4', 'v5', 'v6']}}

    def report(self, template, variables, output_folder, basename):
        """Use vars to fill worksheets in an excel file $destination_template based on the template.
        The template references self.report_variables. The destination_template may contain date format codes that
        will be updated with the current datetime."""
        if self.testing:
            from cea.utilities import reporting
            reporting.full_report_to_xls(template, variables, output_folder, basename, self)



    def log(self, msg, **kwargs):
        print msg % kwargs


    def is_heating_season(self, timestep):

        if self.seasonhours[0]+1 <= timestep < self.seasonhours[1]:
            return False
        else:
            return True

# -*- coding: utf-8 -*-
"""
This file contains the constants used in objective function calculation in optimization
"""
from __future__ import absolute_import
import cea.config
__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

class optimization_constants(object):
    def __init__(self):

        # Losses and margins
        self.DCNetworkLoss = 0.05  # Cooling ntw losses (10% --> 0.1)
        self.DHNetworkLoss = 0.12  # Heating ntw losses
        self.Qmargin_ntw = 0.01  # Reliability margin for the system nominal capacity in the hub
        self.Qloss_Disc = 0.05  # Heat losses within a disconnected building
        self.Qmargin_Disc = 0.20  # Reliability margin for the system nominal capacity for decentralized systems
        self.QminShare = 0.10  # Minimum percentage for the installed capacity
        self.K_DH = 0.25  # linear heat loss coefficient district heting network twin pipes groundfoss
        self.roughness = 0.02 / 1000  # roughness coefficient for heating network pipe in m (for a steel pipe, from Li &
        # Svendsen (2012) "Energy and exergy analysis of low temperature district heating network")

        # pipes location properties
        self.Z0 = 1.5  # location of pipe underground in m
        self.Psl = 1600  # heat capacity of ground in kg/m3 => should be density?
        self.Csl = 1300  # heat capacity of ground in J/kg K
        self.Bsl = 1.5  # thermal conductivity of ground in W/m.K


        ######### LOCAL PLANT : factor with regard to USEFUL ENERGY

        self.NG_BACKUPBOILER_TO_CO2_STD = 0.0691 * 0.87  # kg_CO2 / MJ_useful
        self.BG_BACKUPBOILER_TO_CO2_STD = 0.04 * 0.87  # kg_CO2 / MJ_useful
        self.SMALL_GHP_TO_CO2_STD = 0.0153 * 3.9  # kg_CO2 / MJ_useful
        # SMALL_LAKEHP_TO_CO2_STD    = 0.0211 * 2.8    # kg_CO2 / MJ_useful
        self.SOLARCOLLECTORS_TO_CO2 = 0.00911  # kg_CO2 / MJ_useful

        self.NG_BACKUPBOILER_TO_OIL_STD = 1.16 * 0.87  # MJ_oil / MJ_useful
        self.BG_BACKUPBOILER_TO_OIL_STD = 0.339 * 0.87  # MJ_oil / MJ_useful
        self.SMALL_GHP_TO_OIL_STD = 0.709 * 3.9  # MJ_oil / MJ_useful
        # SMALL_LAKEHP_TO_OIL_STD    = 0.969 * 2.8     # MJ_oil / MJ_useful
        self.SOLARCOLLECTORS_TO_OIL = 0.201  # MJ_oil / MJ_useful



        self.EL_PV_TO_OIL_EQ = 0.345  # MJ_oil / MJ_final
        self.EL_PV_TO_CO2 = 0.02640  # kg_CO2 / MJ_final

        # Solar area to Wpeak
        self.eta_area_to_peak = 0.16  # Peak Capacity - Efficiency, how much kW per area there are, valid for PV and PVT (after Jimeno's J+)

        # Pressure losses
        # DeltaP_DCN = 1.0 #Pa - change
        # DeltaP_DHN = 84.8E3 / 10.0 #Pa  - change

        self.PumpEnergyShare = 0.01  # assume 1% of energy required for pumping, after 4DH
        self.PumpReliabilityMargin = 0.05  # assume 5% reliability margin

        # Circulating Pump
        self.etaPump = 0.8

        # Heat Exchangers
        self.U_cool = 2500  # W/m2K
        self.U_heat = 2500  # W/m2K
        self.dT_heat = 5  # K - pinch delta at design conditions
        self.dT_cool = 1  # K - pinch delta at design conditions
        # Heat pump
        self.HP_maxSize = 20.0E6  # max thermal design size [Wth]
        self.HP_minSize = 1.0E6  # min thermal design size [Wth]

        self.HP_etaex = 0.6  # exergetic efficiency of WSHP [L. Girardin et al., 2010]_
        self.HP_deltaT_cond = 2.0  # pinch for condenser [K]
        self.HP_deltaT_evap = 2.0  # pinch for evaporator [K]
        self.HP_maxT_cond = 140 + 273.0  # max temperature at condenser [K]
        self.HP_Auxratio = 0.83  # Wdot_comp / Wdot_total (circulating pumps)

        # Sewage resource

        self.Sew_minT = 10 + 273.0  # minimum temperature at the sewage exit [K]

        # Lake resources
        self.DeltaU = 12500.0E6  # [Wh], maximum change in the lake energy content at the end of the year (positive or negative)
        self.TLake = 5 + 273.0  # K

        # Geothermal heat pump

        self.TGround = 6.5 + 273.0

        self.COPScalingFactorGroundWater = 3.4 / 3.9  # Scaling factor according to EcoBau, take GroundWater Heat pump into account

        self.GHP_CmaxSize = 2E3  # max cooling design size [Wc] FOR ONE PROBE
        self.GHP_Cmax_Size_th = 2E3  # Wh/m per probe
        self.GHP_Cmax_Length = 40  # depth of exploration taken into account

        self.GHP_HmaxSize = 2E3  # max heating design size [Wth] FOR ONE PROBE
        self.GHP_WmaxSize = 1E3  # max electrical design size [Wel] FOR ONE PROBE

        self.GHP_etaex = 0.677  # exergetic efficiency [O. Ozgener et al., 2005]_
        self.GHP_Auxratio = 0.83  # Wdot_comp / Wdot_total (circulating pumps)

        self.GHP_A = 25  # [m^2] area occupancy of one borehole Gultekin et al. 5 m separation at a penalty of 10% less efficeincy

        # Combined cycle

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

        # Boiler
        # Operating figures, quality parameters and investment costs for district heating systems (AFO)

        # ELCO-Loesungsbeispiel-Huber.pdf

        self.Boiler_C_fuel = 20.0  # € / MWh_therm_bought(for LHV), AFO
        self.Boiler_P_aux = 0.026  # 0.026 Wh/Wh_th_sold = 26 kWh_el / MWh_th_sold, bioenergy 2020
        self.Boiler_min = 0.05  # minimum Part Load of Boiler
        self.Boiler_equ_ratio = 0.2  # 20% own capital required (equity ratio)
        self.Boiler_eta_hp = 0.9

        # Furnace
        self.Furn_FuelCost_wet = 0.057 * 1E-3  # CHF / Wh = 5.7 Rp / kWh for wet (50wt%) Wood Chips, after
        self.Furn_FuelCost_dry = 0.07 * 1E-3  # CHF / Wh = 7 Rp / kWh for dry (30wt%) Wood Chips,
        self.Furn_min_Load = 0.2  # Minimum load possible (does not affect Model itself!)
        self.Furn_min_electric = 0.3  # Minimum load for electricity generation in furnace plant

        # Substation Heat Exchangers


        # Vapor compressor chiller
        self.VCC_tcoolin = 30 + 273.0  # entering condenser water temperature [K]
        self.VCC_minload = 0.1  # min load for cooling power

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
        self.nHR = 2  # number of heat recovery options
        self.nSolar = 3  # number of solar technologies

        self.PROBA = 0.5
        self.SIGMAP = 0.2
        self.epsMargin = 0.001

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
        self.angle_north = 122.5
        self.type_SCpanel = 1  # Flatplate collector

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

        # Low heating values
        self.LHV_NG = 45.4E6  # [J/kg]
        self.LHV_BG = 21.4E6  # [J/kg]

        # DCN
        self.TsupCool = 6 + 273
        self.TretCoolMax = 12 + 273.0

        # Values for the calculation of Delta P (from F. Muller network optimization code)
        # WARNING : current = values for Inducity SQ
        self.DeltaP_Coeff = 104.81
        self.DeltaP_Origin = 59016

        self.Subst_n = 20  # Lifetime after A+W default 20
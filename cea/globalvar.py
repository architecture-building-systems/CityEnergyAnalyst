# -*- coding: utf-8 -*-
"""
Global variables - this object contains context information and is expected to be refactored away in future.
"""
from __future__ import absolute_import
import cea.config
__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class GlobalVariables(object):
    def __init__(self):
        self.config = cea.config.Configuration()  # FIXME: this needs to be refactored away when we refactor gv->config
        self.print_partial = 'hourly'  # hourly or monthly for the demand script
        self.print_totals = True  # print yearly values
        self.print_yearly_peak = True  # print peak values
        self.simulate_building_list = None  # fill it with a list of names of buildings in case not all the data set needs to be run
        self.date_start = '2015-01-01'  # format: yyyy-mm-dd
        self.seasonhours = [3216, 6192]
        self.Z = 3  # height of basement for every building in m
        self.Bf = 0.7  # it calculates the coefficient of reduction in transmittance for surfaces in contact with the ground according to values of SIA 380/1
        self.his = 3.45  # heat transfer coefficient between air and the surfacein W/(m2K)
        self.hms = 9.1  # heat transfer coefficient between nodes m and s in W/m2K
        self.theta_ss = 10  # difference between surface of building and sky temperature in C. 10 for temperate climates
        self.F_f = 0.2  # Frame area faction coefficient
        self.Rse = 0.04  # thermal resistance of external surfaces according to ISO 6946
        self.D = 20  # in mm the diameter of the pipe to calculate losses
        self.hf = 3  # average height per floor in m
        self.Pwater = 998.0  # water density kg/m3
        self.PaCa = 1200  # Air constant J/m3K 
        self.Cpw = 4.184  # heat capacity of water in kJ/kgK
        self.Flowtap = 0.036  # in m3 == 12 l/min during 3 min every tap opening
        self.Es = 0.9  # franction of GFA that has electricity in every building
        # constant values for HVAC
        self.nrec_N = 0.75  # possible recovery
        #self.NACH_inf_non_occ = 0.2  # num air exchanges due to infiltration when no occupied
        #self.NACH_inf_occ = 0.5  # num air exchanges due to infiltration when occupied
        self.C1 = 0.054  # assumed a flat plate heat exchanger (-)
        #self.Vmax = 3  # maximum estimated flow in m3/s
        #self.Pair = 1.2  # air density in kg/m3
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
        # grey emissions
        self.fwratio = 1.5  # conversion component's area to floor area
        self.sl_materials = 60  # service life of standard building components and materials
        self.sl_services = 40  # service life of technical installations
        # constant variables for air conditioning fan
        self.Pfan = 0.55  # specific fan consumption in W/m3/h

        # ==============================================================================================================
        # optimization
        # ==============================================================================================================

        self.sensibilityStep = 2  # the more, the longer the sensibility analysis

        ########################### User inputs
        self.ZernezFlag = 0

        self.roughness = 0.02 / 1000  # roughness coefficient for heating network pipe in m (for a steel pipe, from Li &

        ########################### Model parameters

        # Date data
        self.DAYS_IN_YEAR = 365
        self.HOURS_IN_DAY = 24

        # Specific heat
        self.cp = 4185  # [J/kg K]
        self.rho_60 = 983.21  # [kg/m^3] density of Water @ 60°C
        self.Wh_to_J = 3600.0

        # Data for clustering_sax
        nPeriodMin = 2
        nPeriodMax = 15
        gam = 0.2
        threshErr = 0.2



        # Resource prices

        self.GasConnectionCost = 15.5 / 1000.0  # CHF / W, from  Energie360 15.5 CHF / kW

        # Substation data
        self.mdot_step_counter_heating = [0.05, 0.1, 0.15, 0.3, 0.4, 0.5, 0.6, 1]
        self.mdot_step_counter_cooling = [0, 0.2, 0.5, 0.8, 1]
        self.NetworkLengthReference = 1745.0  # meters of network length of max network. (Reference = Zug Case Study) , from J. Fonseca's Pipes Data
        self.PipeCostPerMeterInv = 660.0  # CHF /m
        self.PipeLifeTime = 40.0  # years, Data from A&W
        self.PipeInterestRate = 0.05  # 5% interest rate
        self.PipeCostPerMeterAnnual = self.PipeCostPerMeterInv / self.PipeLifeTime
        self.NetworkDepth = 1  # m

        self.Subst_i = 0.05  # default 0.05

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
        # TABS
        # ==============================================================================================================
        self.max_temperature_difference_tabs = 9  # (°C) from Koschenz & Lehmann "Thermoaktive Bauteilsysteme (TABS)"
        self.max_surface_temperature_tabs = 27  # (°C) from Koschenz & Lehmann "Thermoaktive Bauteilsysteme (TABS)"

        # ==============================================================================================================
        # Columns to write for the demand calculation
        # ==============================================================================================================
        # here is where we decide whether full excel reports of the calculations are generated
        self.testing = False  # if true: reports are generated, if false: not

    def report(self, tsd, output_folder, basename):
        """Use vars to fill worksheets in an excel file $destination_template based on the template.
        The template references self.report_variables. The destination_template may contain date format codes that
        will be updated with the current datetime."""
        if self.testing:
            from cea.utilities import reporting
            reporting.full_report_to_xls(tsd, output_folder, basename, self)

    def log(self, msg, **kwargs):
        print msg % kwargs

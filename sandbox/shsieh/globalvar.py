"""
================
Global variables
================

"""


class GlobalVariables(object):
    def __init__(self):
        self.list_uses = ['ADMIN', 'SR', 'INDUS', 'REST', 'RESTS', 'DEPO', 'COM', 'MDU', 'SDU',
                          'EDU', 'CR', 'HEALTH', 'SPORT', 'SWIM', 'PUBLIC', 'SUPER', 'ICE', 'HOT']
        self.seasonhours = [3216, 6192]
        self.main_use = 'ADMIN'
        self.shading_type = "T1"
        self.window_to_wall_ratio = 0.4
        self.generation_heating = 3
        self.generation_hotwater = 3
        self.generation_cooling = 2
        self.generation_electricity = 1
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
        self.lvapor = 2257  # latent heat of air kJ/kg
        # constant variables for pumping operation
        self.hoursop = 5  # assuming around 2000 hours of operation per year. It is charged to the electrical system from 11 am to 4 pm
        self.gr = 9.81  # m/s2 gravity
        self.effi = 0.6  # efficiency of pumps
        self.deltaP_l = 0.1  # delta of pressure
        self.fsr = 0.3  # factor for pressure calculation
        # grey emssions
        self.fwratio = 1.5  # conversion component's area to floor area
        self.sl_materials = 60  # service life of standard building components and materials
        self.sl_installations = 40  # service life of technical instalations
        # constant variables for air conditioning fan
        self.Pfan = 0.55 # specific fan consumption in W/m3/h

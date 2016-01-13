"""
================
Global variables
================

"""


class GlobalVariables(object):

    def __init__(self):
        self.list_uses = ['ADMIN','SR','INDUS','REST','RESTS','DEPO','COM','MDU','SDU',
                    'EDU','CR','HEALTH','SPORT','SWIM','PUBLIC','SUPER','ICE','HOT']
        self.seasonhours = [3216,6192] 
        self.main_use = 'ADMIN'
        self.shading_type = 1
        self.shading_position = 1 
        self.window_to_wall_ratio = 0.4
        self.generation_heating = 3
        self.generation_hotwater = 3
        self.generation_cooling =  2
        self.generation_electricity= 1 
        self.Z = 3 # height of basement for every building in m
        self.Bf = 0.7 # It calculates the coefficient of reduction in transmittance for surfaces in contact with the ground according to values of  SIA 380/1
        self.his = 3.45 #heat transfer coefficient between air and the surfacein W/(m2K)
        self.hms = 9.1 # Heat transfer coeddicient between nodes m and s in W/m2K 
        self.g_gl = 0.9*0.75 # solar energy transmittance assuming a reduction factor of 0.9 and most of the windows to be double glazing (0.75)
        self.F_f = 0.3 # Frame area faction coefficient
        self.D = 20 #in mm the diameter of the pipe to calculate losses
        self.hf = 3 # average height per floor in m
        self.Pwater = 998 # water density kg/m3
        self.PaCa = 1200  # Air constant J/m3K 
        self.Cpw= 4.184 # heat capacity of water in kJ/kgK
        self.Flowtap = 0.036 # in m3/min ==  12 l/min during 3 min every tap opening 
        # constants
        self.deltaP_l = 0.1 #delta of pressure
        self.fsr = 0.3 # factor for pressure calculation
        #constant values for HVAC
        self.nrec_N = 0.75  #possilbe recovery
        self.C1 = 0.054 # assumed a flat plate heat exchanger
        self.Vmax = 3 # maximum estimated flow i m3/s
        self.Pair = 1.2 #kg/m3
        self.Cpv = 1.859 # in KJ/kgK specific heat capacity of water vapor
        self.Cpa = 1.008 # in KJ/kgK specific heat capacity of air
        self.lvapor = 2257 #kJ/kg
        # constan variables for pumping operation
        self.hoursop = 5 # assuming around 2000 hour of operation per day. charged from 11 am to 4 pm
        self.gr = 9.81 # m/s2 gravity
        self.effi = 0.6 # efficiency of pumps
        self.equivalentlength = 0.6
        #grey emssions
        self.fwratio = 1.5 # conversion component's area to floor area   
        self.sl_materials = 60 # service life of standard building components and materials  
        self.sl_installations = 40 # service life of technical instalations 
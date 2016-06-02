#-----------------
# Florian Mueller
# December 2014
#-----------------

# see report.pdf, section 6.1



import Data
import numpy
import math



class ThermalData(Data.Data):



    scalarFields = ['zeroBasedIndexing','cp','etaHeat','cHeat']
    indexFields  = []


    def setZernez(self,ld,hd,rhd,rhs):


        self.c['cp']      = 4185.5
        self.c['etaHeat'] = 0.8
        self.c['cHeat']   = 1.e-3*0.25*24.*365.
        self.c['TRq_n']   = 80.*numpy.ones((ld.c['N'],1))
        self.c['dT_n']    = 20.*numpy.ones((ld.c['N'],1))
        h_i               = 13.9*math.pi*hd.c['d_i']
        i_e = numpy.reshape(rhd.c['i_e'],(ld.c['E']))
        self.c['h_e']     = h_i[i_e]
        self.c['vDot_e']  = rhs.c['vDot_e']



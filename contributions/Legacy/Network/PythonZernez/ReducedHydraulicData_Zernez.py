#-----------------
# Florian Mueller
# December 2014
#-----------------

# see report.pdf, section 5.1



import Data
import numpy



class ReducedHydraulicData(Data.Data):



    scalarFields = ['zeroBasedIndexing']
    indexFields  = ['i_e']



    def setZernez(self,ld,hd,hs):

        self.c['i_e'] = numpy.zeros((ld.c['E'],1),dtype=numpy.int64)
        H        = numpy.reshape(numpy.round(hs.c['x'][0:hd.c['I']*ld.c['E']]),(hd.c['I'],ld.c['E']),order='F')
        for e in range(ld.c['E']):
            self.c['i_e'][e] = numpy.nonzero(H[:,e])

        i_e = numpy.reshape(self.c['i_e'],(ld.c['E']))

        self.c['vDotMin_e'] = hd.c['vDotMin_i'][i_e]
        self.c['vDotMax_e'] = hd.c['vDotMax_i'][i_e]
       
        self.c['a_k_e'] = hd.c['a_k_i'][:,i_e]
        self.c['b_k_e'] = hd.c['b_k_i'][:,i_e]


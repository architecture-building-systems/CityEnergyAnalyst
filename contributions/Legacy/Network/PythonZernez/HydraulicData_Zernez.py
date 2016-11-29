#-----------------
# Florian Mueller
# December 2014
#-----------------

# see report.pdf, section 4.1



import Data
import numpy
import math

def assignImportToCodeIndex(inputarray):
            """
            assigns inport-index to coding-index (for Zernez Base Scenario)
            
            """
            outputarray = numpy.zeros((75,1))
            outputarray[14] = inputarray[0]
            outputarray[16] = inputarray[1]
            outputarray[12] = inputarray[2]
            outputarray[11] = inputarray[3]
            outputarray[9]  = inputarray[4]
            outputarray[61] = inputarray[5]
            outputarray[63] = inputarray[6]
            outputarray[33] = inputarray[7]
            outputarray[34] = inputarray[8]
            outputarray[64] = inputarray[9]
            outputarray[65] = inputarray[10]
            outputarray[36] = inputarray[11]
            outputarray[37] = inputarray[12]
            outputarray[39] = inputarray[13]
            outputarray[66] = inputarray[14]
            outputarray[67] = inputarray[15]
            outputarray[68] = inputarray[16]
            outputarray[43] = inputarray[17]
            outputarray[45] = inputarray[18]
            outputarray[46] = inputarray[19]
            outputarray[47] = inputarray[20]
            outputarray[48] = inputarray[21]
            outputarray[72] = inputarray[22]
            outputarray[74] = inputarray[23]
            outputarray[73] = inputarray[24]
            outputarray[70] = inputarray[25]
            outputarray[69] = inputarray[26]
            outputarray[71] = inputarray[27]
            outputarray[17] = inputarray[28]
            outputarray[15] = inputarray[29]
            outputarray[13] = inputarray[30]
            outputarray[10] = inputarray[31]
            outputarray[38] = inputarray[32]
            outputarray[35] = inputarray[33]
            outputarray[40] = inputarray[34]
            outputarray[41] = inputarray[35]
            outputarray[44] = inputarray[36]
            outputarray[42] = inputarray[37]
            
            return outputarray


class HydraulicData(Data.Data):



    scalarFields = ['zeroBasedIndexing','rho','nu','etaPump','cPump','vDotPl','I','K']
    indexFields  = []

    def setZernez(self,ld):

        self.c['rho']         = 1000.;
        self.c['nu']          = 1.e-6;
        self.c['etaPump']     = 0.8;
        self.c['cPump']       = 1.e-3*0.25*24.*365.;
        
        
        pRq_n                 = 120000.0 * numpy.ones(ld.c['N'])
        self.c['pRq_n']       = assignImportToCodeIndex(pRq_n)# numpy.zeros((ld.c['N'],1));
               
               # read in massflows here, convert to m^3/S
        self.c['vDotRq_n']    = -numpy.array([[0.],[2.61647694],[2.61647694],[2.49754617],[2.49754617],[2.49754617],[2.49754617],[2.49754617],[4.81386450],[0.02831685],[4.81386450],[3.31590314],[3.31590314],[2.61647694],[2.61647694],[4.81386450],[1.62821888],[3.31590314],[3.31590314],[4.81386450]])
        
        self.c['vDotRq_n']    = self.c['vDotRq_n']/1000.0;
        self.c['vDotPl']      = 0 #-sum(self.c['vDotRq_n'][numpy.array(range(ld.c['N']))!=ld.c['nPl']*numpy.ones(ld.c['N']),0]);
  
        self.c['L_e']         = numpy.array([[3535.69],[6035.06],[2225.05],[2529.85],[2621.29],[5821.70],[2926.09],[3810.01],[2926.09],[3413.77],[4419.61],[3718.57],[7345.70],[6431.30],[4724.42],[8046.75],[9509.79],[7315.22],[4389.13],[11704.36],[8046.75]])
   
        self.c['I']           = 15;
        self.c['d_i']         = numpy.array([[0.02  ],[0.025 ],[0.032 ],[0.040 ],[0.050 ],[0.065 ],[0.08  ],[0.1   ],[0.125 ],[0.15  ],[0.2   ],[0.25  ],[0.3   ],[0.35   ],[0.4  ]])
        self.c['c_i']         = numpy.array([[73.   ],[80.   ],[92.   ],[127.  ],[165.  ],[254.  ],[370.  ],[567.  ],[882.  ],[1250. ],[1500. ],[2500. ],[3000. ],[3500.  ],[4000 ]])/60.
        self.c['r_i']         = numpy.array([[0.0018],[0.0018],[0.0018],[0.0018],[0.0018],[0.0018],[0.0018],[0.0018],[0.0018],[0.0018],[0.0048],[0.0048],[0.0048],[0.0048],[0.0048]])
        o_i                   = numpy.array([[26.9  ],[33.7  ],[43.4  ],[48.4  ],[ 60.3 ],[76.1  ],[88.9  ],[114.3 ],[139.7 ],[168.3 ],[219.1 ],[273   ],[323.9 ],[355.6  ],[406.4]])
        w_i                   = numpy.array([[2.6   ],[2.6   ],[2.6   ],[2.6   ],[2.9   ],[2.9   ],[3.2   ],[3.6   ],[4.6   ],[4     ],[4.5   ],[5     ],[5.6   ],[5.6    ],[6.3  ]])
        vMin_i                = 0.000000001*numpy.ones((self.c['I'],1)) # MAYBE SET TO ZERO for convertion of code
        vMax_i                = 0.4066*(o_i-w_i)**0.412;
        self.c['vDotMin_i']   = vMin_i*self.c['d_i']**2./4.*math.pi;
        self.c['vDotMax_i']   = vMax_i*self.c['d_i']**2./4.*math.pi;

        self.c['K']      = 10
        vDotLin_k_i = numpy.zeros((self.c['K'],self.c['I']))
        for i in range(self.c['I']):
            vDotLin_k_i[:,i] = numpy.transpose(numpy.linspace(self.c['vDotMin_i'][i],self.c['vDotMax_i'][i],self.c['K']))

        self.c['a_k_i'] = numpy.zeros((self.c['K'],self.c['I']))
        self.c['b_k_i'] = numpy.zeros((self.c['K'],self.c['I']))
        for i in range(self.c['I']):
            for k in range(self.c['K']):
                phi1     = 0.25/self.c['d_i'][i]*self.c['rho']/2.
                phi2     = (1./math.log(10.)*math.log(self.c['r_i'][i]/(3.7*self.c['d_i'][i])+5.74*(4.*vDotLin_k_i[k,i]/(self.c['d_i'][i]*math.pi*self.c['nu']))**(-0.9)))**(-2.)
                phi3     = (4.*vDotLin_k_i[k,i]/(self.c['d_i'][i]**2.*math.pi))**2.
                phi      = (phi1*phi2*phi3)
                dphi2    = (-2.*(1./math.log(10.)*math.log(self.c['r_i'][i]/(3.7*self.c['d_i'][i])+5.74 *(4.*vDotLin_k_i[k,i]/(self.c['d_i'][i]*math.pi*self.c['nu']))**(-0.9)))**(-3.)*1./math.log(10.)*1./(self.c['r_i'][i]/(3.7*self.c['d_i'][i])+5.74* (4.*vDotLin_k_i[k,i]/(self.c['d_i'][i]*math.pi*self.c['nu']))**(-0.9))*(-0.9)*5.74   *(4.*vDotLin_k_i[k,i]/(self.c['d_i'][i]*math.pi*self.c['nu']))**(-1.9) *4./(self.c['d_i'][i]*math.pi*self.c['nu']))    
                dphi3    = (2.*(16.*vDotLin_k_i[k,i]/(self.c['d_i'][i]**4.*math.pi**2.)))
                dphi     = (phi1*(dphi2*phi3+phi2*dphi3))

                self.c['a_k_i'][k,i] = dphi
                self.c['b_k_i'][k,i] = phi-self.c['a_k_i'][k,i]*vDotLin_k_i[k,i]



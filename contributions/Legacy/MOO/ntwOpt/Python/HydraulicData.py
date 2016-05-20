#-----------------
# Florian Mueller
# December 2014
#-----------------

# see report.pdf, section 4.1



import Data
import numpy
import math



class HydraulicData(Data.Data):



    scalarFields = ['zeroBasedIndexing','rho','nu','etaPump','cPump','vDotPl','I','K']
    indexFields  = []



    def setNewYork(self,ld):

        self.c['rho']         = 1000.;
        self.c['nu']          = 1.e-6;
        self.c['etaPump']     = 0.8;
        self.c['cPump']       = 1.e-3*0.25*24.*365.;
        self.c['pRq_n']       = numpy.zeros((ld.c['N'],1));
       
        #self.c['vDotRq_n']    = -numpy.array([[0.],[2.61647694],[2.61647694],[2.49754617],[2.49754617],[2.49754617],[2.49754617],[2.49754617],[4.81386450],[0.02831685],[4.81386450],[3.31590314],[3.31590314],[2.61647694],[2.61647694],[4.81386450],[1.62821888],[3.31590314],[3.31590314],[4.81386450]])
        self.c['vDotRq_n']    = numpy.zeros((ld.c['N'],1));
        
        #self.c['vDotRq_n']    = self.c['vDotRq_n']/1000.;
        self.c['vDotPl']      = -sum(self.c['vDotRq_n'][numpy.array(range(ld.c['N']))!=ld.c['nPl']*numpy.ones(ld.c['N']),0]);
          
        #self.c['L_e']         = numpy.array([[3535.69],[6035.06],[2225.05],[2529.85],[2621.29],[5821.70],[2926.09],[3810.01],[2926.09],[3413.77],[4419.61],[3718.57],[7345.70],[6431.30],[4724.42],[8046.75],[9509.79],[7315.22],[4389.13],[11704.36],[8046.75]])
        self.c['L_e']         = numpy.zeros((ld.c['E'],1));
   
        self.c['I']           = 15;
        self.c['d_i']         = numpy.array([[0.02  ],[0.025 ],[0.032 ],[0.040 ],[0.050 ],[0.065 ],[0.08  ],[0.1   ],[0.125 ],[0.15  ],[0.2   ],[0.25  ],[0.3   ],[0.35   ],[0.4  ]])
        self.c['c_i']         = numpy.array([[73.   ],[80.   ],[92.   ],[127.  ],[165.  ],[254.  ],[370.  ],[567.  ],[882.  ],[1250. ],[1500. ],[2500. ],[3000. ],[3500.  ],[4000 ]])/60.
        self.c['r_i']         = numpy.array([[0.0018],[0.0018],[0.0018],[0.0018],[0.0018],[0.0018],[0.0018],[0.0018],[0.0018],[0.0018],[0.0048],[0.0048],[0.0048],[0.0048],[0.0048]])
        o_i                   = numpy.array([[26.9  ],[33.7  ],[43.4  ],[48.4  ],[ 60.3 ],[76.1  ],[88.9  ],[114.3 ],[139.7 ],[168.3 ],[219.1 ],[273   ],[323.9 ],[355.6  ],[406.4]])
        w_i                   = numpy.array([[2.6   ],[2.6   ],[2.6   ],[2.6   ],[2.9   ],[2.9   ],[3.2   ],[3.6   ],[4.6   ],[4     ],[4.5   ],[5     ],[5.6   ],[5.6    ],[6.3  ]])
        
        #vMin_i                = 0.3*numpy.ones((self.c['I'],1))
        vMin_i                = 0.3*numpy.ones((self.c['I'],1))
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



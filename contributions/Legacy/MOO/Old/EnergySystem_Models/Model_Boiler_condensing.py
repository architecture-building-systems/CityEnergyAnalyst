# -*- coding: utf-8 -*-
"""Model_Boiler_Condensing"""


from scipy.interpolate import interp1d
import numpy as np

import globalVar as gV

reload (gV)


def Cond_Boiler_InvCost(Q_design, Q_annual):
    """
    Calculates the annual cost of a boiler (based on A+W cost of oil boilers) [CHF / a]
    and Faz. 2012 data
    
    
    
    Parameters
    ----------
    Q_design : float
        Design Load of Boiler
    
    Q_annual : float
        Annual thermal load required from Boiler
    Returns
    -------
    InvCa : float
        annualized investment costs in CHF including Maintainance Cost
        
    """
    InvC = 28000 # after A+W 
    
    if Q_design <= 90000 and Q_design >= 28000:
        InvC_exkl_MWST = 28000 + 0.275 * (Q_design - 280000) # linear interpolation of A+W data
        InvC = (gV.MWST + 1) * InvC_exkl_MWST
        
    elif Q_design  <= 320000: # 320kW = maximum Power of conventional Gas Boiler, 
        InvC = 45000 + 0.11 * (Q_design - 45000) 
    
    InvCa =  InvC * gV.Boiler_i * (1+ gV.Boiler_i) ** gV.Boiler_n / ((1+gV.Boiler_i) ** gV.Boiler_n - 1) 

    if Q_design > 320000: # 320kW = maximum Power of conventional Gas Boiler 
        InvCa = gV.EURO_TO_CHF * 84000 + 14 * Q_design / 1000 # after Faz.2012
    
    
    Maint_C_annual = gV.Boiler_C_maintainance_faz * Q_annual / 1000000.0 * gV.EURO_TO_CHF # 3.5 euro per MWh_th FAZ 2013
    if Q_annual > 0:
        Labour_C = gV.Boiler_C_labour / Q_annual / 1000000.0 * gV.EURO_TO_CHF # approx 4 euro per MWh_th
    else:
        Labour_C = 0
    
    InvCa += Maint_C_annual + Labour_C
    
    return InvCa



def Cond_Boiler_operation(Q_load, Q_design, T_return_to_boiler):

    """
    Efficiency for operation of condensing Boilers
    
    Efficiencies based on LHV ! 
    
    operational efficiency after:
        http://www.greenshootscontrols.net/?p=153
    
    Parameters
    ----------
    Q_load : float
        Load of time step
        
    Q_max : float
        Design Load of Boiler
        
    T_return_to_boiler : float
        Return Temperature of the network to the boiler [K]
     
    Returns
    -------
    eta_boiler : float
        efficiency of Boiler (Lower Heating Value), in abs. numbers
        accounts for boiler efficiency only (not plant efficiency!)
    
    """
    
    #Implement Curves provided by http://www.greenshootscontrols.net/?p=153
    x = [0,15.5, 21, 26.7, 32.2, 37.7, 43.3, 49, 54.4, 60, 65.6, 71.1, 100] # Return Temperature Dependency
    y = [96.8,96.8, 96.2, 95.5, 94.7, 93.2, 91.2, 88.9, 87.3, 86.3, 86.0, 85.9, 85.8] # Return Temperature Dependency
    #x1 = [0.05, 0.25, 0.5, 0.75, 1] # Load Point dependency
    #y1 = [99.3, 98.3, 97.6, 97.1, 96.8] # Load Point Dependency
    
    x1 = [0, 0.05, 0.25, 0.5, 0.75, 1] # Load Point dependency
    y1 = [99.5, 99.3, 98.3, 97.6, 97.1, 96.8] # Load Point Dependency
    
     # do the interpolation 
    eff_of_T_return = interp1d(x, y, kind='linear')
    eff_of_phi = interp1d(x1, y1, kind='cubic')
    
    # get input variables
    phi = float(Q_load) / float(Q_design)
    
    #if phi < gV.Boiler_min:
    #    print "Boiler at too low part load, see Model_Boiler_condensing, line 100"
        
        #raise model error!!
        
        
    T_return = T_return_to_boiler - 273
    eff_score = eff_of_phi(phi) / eff_of_phi(1)
    
    boiler_eff = (eff_score * eff_of_T_return(T_return) )/ 100.0 
    
    return boiler_eff
    

""" for Plots !! """
"""
x = [0,15.5, 21, 26.7, 32.2, 37.7, 43.3, 49, 54.4, 60, 65.6, 71.1, 100]
y = [96.8,96.8, 96.2, 95.5, 94.7, 93.2, 91.2, 88.9, 87.3, 86.3, 86.0, 85.9, 85.8]
x1 = [0.05, 0.25, 0.5, 0.75, 1]
y1 = [99.3, 98.3, 97.6, 97.1, 96.8]

f2 = interp1d(x1, y1, kind='cubic')


f2 = interp1d(x, y, kind='linear')
xnew = np.linspace(np.amin(x), np.amax(x), 100)
import matplotlib.pyplot as plt

#plt.plot(xnew, f(xnew), label='linear')
plt.plot(xnew , f2(xnew), label='cubic')
plt.legend([' Efficiency = f(T_return)'], loc='best')
plt.xlabel("Temperature in deg C ")
plt.ylabel("Maximum Efficiency @ Full Load in % ") 
plt.show()
"""
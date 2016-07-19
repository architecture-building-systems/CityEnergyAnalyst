# -*- coding: utf-8 -*-

"""
==========================
System Modeling: Boiler
==========================

"""

import globalVar as gV
reload (gV)

""" 

used for Condensing boilers, as they are state of the art and no specification is made, which kind of boiler they assume.


def Boiler_InvCost(Q_design):
"""
"""
    Calculates the cost of a boiler (based on A+W cost of oil boilers) [CHF / a]
    
    
    
    Parameters
    ----------
    Q_design : float
        Design Load of Boiler
    
    Returns
    -------  
    InvC_return : float
        total investment Cost 
    
    InvCa : float
        annualized investment costs in CHF
        
"""
"""
    InvC = 28000 # after A+W 
    
    if Q_design <= 90000 and Q_design >= 28000:
        InvC_exkl_MWST = 28000 + 0.275 * (Q_design - 280000) # linear interpolation of A+W data
        InvC = (gV.MWST + 1) * InvC_exkl_MWST
        
    if Q_design  <= 320000: # 320kW = maximum Power of conventional Gas Boiler, 
        InvC = 45000 + 0.11 * (Q_design - 45000) 
    
    InvCa =  InvC * gV.Boiler_i * (1+ gV.Boiler_i) ** gV.Boiler_n / ((1+gV.Boiler_i) ** gV.Boiler_n - 1) 
             
    if Q_design > 320000: # 320kW = maximum Power of conventional Gas Boiler 
        InvCa = gV.EURO_TO_CHF * 84000 + 14 * Q_design / 1000 # after Faz.2012
    
    return InvCa

"""

def Boiler_operation(Q_load, Q_max, boiler_type):

    """
    Efficiency for operation of non-condensing Boilers.
    
    Efficiencies based on LHV ! (
    
    operational efficiency after:
        http://www.energieverbraucher.de/files/download/file/0/1/0/183.pdf
    
    Parameters
    ----------
    Q_load : float
        Load of time step
        
    Q_max : float
        Design Load of Boiler
        
    boiler_type : string
        state if the boiler is used for hot water production only ("HOTWATER")
     
    Returns
    -------
    eta_boiler : float
        efficiency of Boiler (Lower Heating Value), in abs. numbers
    
    Q_fuel : float
        Heat dem from fuel (in Watt)
    
    
    
    """
    
    
    phi = Q_load / Q_max
    if boiler_type == "HOTWATER":
            
        if Q_max < 20000: # W
            eta = 0.39
            
            if phi  > 0.06:
                eta = 0.65
            
            if phi > 0.2:
                eta = 0.79
            
            if phi > 0.5:
                eta = 0.83
        
        elif Q_max < 37000: # W
            eta_score = 0.65
            
            if phi  > 0.06:
                eta_score = 0.80
            
            if phi > 0.2:
                eta_score = 0.84
            
            if phi > 0.5:
                eta_score = 0.86
        
    elif Q_max < 50000: # use boiler for thermal needs
        eta = 0.48
        
        if phi  > 0.06:
            eta = 0.72
        
        if phi > 0.2:
            eta = 0.82
        
        if phi > 0.5:
            eta = 0.85
        
    elif Q_max > 50000 and Q_max < 120000: 
        eta = 0.53
        
        if phi  > 0.06:
            eta = 0.76
        
        if phi > 0.2:
            eta = 0.82
        
        if phi > 0.5:
            eta = 0.87
    
    elif Q_max > 120 and Q_max < 350000: 
        eta = 0.67
        
        if phi  > 0.06:
            eta = 0.82
        
        if phi > 0.2:
            eta = 0.87
        
        if phi > 0.5:
            eta = 0.89
             
    elif Q_max > 350000 and Q_max < 1200000: 
        eta = 0.67
        
        if phi > 0.06:
            eta = 0.82
            
        if phi > 0.2:
            eta = 0.87
        
        if phi > 0.5:
            eta = 0.89
            
    else:
        eta = 0.8 # according to Faz. 2012
    
    Q_fuel = Q_load / eta
    
    return eta, Q_fuel
    

"""

import numpy as np
import matplotlib.pyplot as plt

Q_load = np.linspace(0,1000000, 1000)
Q_max = np.amax(Q_load)
boiler_type = "HT"
InvCa_result = np.zeros(len(Q_load)) 
Q_fuel = np.zeros(len(Q_load)) 


for k in range(len(Q_load)):
    Q_load_in = Q_load[k]
    InvCa_result[k], Q_fuel[k] = Boiler_operation(Q_load_in, Q_max, boiler_type)
    print InvCa_result[k]
    
plt.plot(Q_fuel/1000)

plt.ylabel('Annual Cost of Heat Exchanger Cost in kCHF')
plt.xlabel('Q_design')
plt.show()"""
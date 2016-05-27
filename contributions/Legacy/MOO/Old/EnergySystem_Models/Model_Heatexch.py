# -*- coding: utf-8 -*-

"""
==========================
System Modeling: Heat Exch.
==========================

Gives Cost of Heat Exchangers (by nominal load) 

EFFICIENCY = 100 %  -- >   A + W  DATA¨

Design and operation in Substation model
"""

import os
os.chdir("/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/Clustering")
import globalVar as gV

reload (gV)

def Heatexch_Cost(Q_design):
    """
    Calculates the cost of a heat exchanger (based on A+W cost of oil boilers) [CHF / a]
    
    
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
    InvC = 3000 # after A+W 

    if Q_design >= 50000 and Q_design <= 80000:
        InvC = 3000 + 2.0/30 * (Q_design - 50000) # linear interpolation of A+W data
        
    if Q_design  >= 80000 and Q_design < 100000:
        InvC = 5000.0
        print "A"
    
    if Q_design > 100000: 
        InvC = 80 * Q_design / 1000.0
        print "B"


    InvCa =  InvC * gV.Subst_i * (1+ gV.Subst_i) ** gV.Subst_n / ((1+gV.Subst_i) ** gV.Subst_n - 1) 
             
       
    return InvCa
    
    

""" 
    #    USED FOR PLOTS:
#    
"""
import numpy as np
import matplotlib.pyplot as plt

Q_load = np.linspace(0,1000000, 1000)

InvCa_result = np.zeros(len(Q_load)) 


for k in range(len(Q_load)):
    Q_load_in = Q_load[k]
    InvCa_result[k] = Heatexch_Cost(Q_load_in)
    print InvCa_result[k]
    
plt.plot(InvCa_result/1000)
plt.ylabel('Annual Cost of Heat Exchanger Cost in kCHF')
plt.xlabel('Q_design')
plt.show()
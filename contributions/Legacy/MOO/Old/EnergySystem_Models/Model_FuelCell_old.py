# -*- coding: utf-8 -*-

"""
==========================
System Modeling: Fuel Cell
==========================



"""

import os
os.chdir("/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/Clustering")
import globalVar as gV
import numpy as np
import matplotlib.pyplot as plt


reload (gV)

def FuelCell_Cost(Q_design):
    """
    Calculates the cost of a Fuel Cell in CHF
    
    TO BE UPDATED! 
    Parameters
    ----------
    Q_design : float
        Design Load of Fuel Cell
    
    Returns
    -------
    InvC_return : float
        total investment Cost 
    
    InvCa : float
        annualized investment costs in CHF
        
    """
    
    InvC_USD = 550 * Q_design / 1000 # 550 $ / kW
    InvC = gV.USD_TO_CHF * InvC_USD
    
    InvCa =  InvC * gV.FC_i * (1+ gV.FC_i) ** gV.FC_n / ((1+gV.FC_i) ** gV.FC_n - 1) 
    
    return InvC, InvCa



def FC_operation(Q_load, Q_design, phi_threshold):

    """
    VALID FOR Q in range of 1-10kW_el !
    
    Efficiency for operation of a SOFC (based on LHV of nat. gas)
    
    Includes all auxillary losses
    
    Fuel = Natural Gas 
    
    Modeled after: 
        http://energy.gov/eere/fuelcells/distributedstationary-fuel-cell-systems
        and
        NREL : p.5  of http://www.nrel.gov/vehiclesandfuels/energystorage/pdfs/36169.pdf
    
    
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
    eta_el : float
        electric efficiency of FC (Lower Heating Value), in abs. numbers
    
    Q_fuel : float
        Heat dem from fuel (in Watt)
    
    
    
    """
    phi = 0.0
    phi = Q_load / Q_design
    eta_max = 0.425 # from energy.gov
    
    print phi
    print phi_threshold
    
    if phi >= phi_threshold: # from NREL-Shape
        eta_el = eta_max - ((1/6.0 * eta_max)/ (1.0-phi_threshold) )* abs(phi-phi_threshold)

    
    if phi < phi_threshold:
        if phi <= 0.25 * phi_threshold:
            eta_el = (0.5 * eta_max) / ((1/4.0) * (phi_threshold)) * abs(phi)
            print "A"
        
        if phi <= 0.5 * phi_threshold and phi >= 0.25 * phi_threshold:
            eta_el = 0.5 * eta_max + (5.0 * eta_max)/ (3.0 * phi_threshold) * abs(phi-0.25*phi_threshold)
            print "b"
            
        if phi > 0.5  * phi_threshold:
            eta_el = eta_max * 55/60.0 + (1/12.0 * eta_max) / (0.5 * phi_threshold) * abs(phi-0.5*phi_threshold)
            print "C"
            
        print "yes 2" 
    
    eta_therm = 0.45 # constant, after energy.gov
    

    
    
    
    return eta_el, eta_therm
    
Q_load = np.linspace(0,10, 10000)

eta_result = np.zeros(len(Q_load)) 
Q_max = 10
phi_thr = 0.1

for k in range(len(Q_load)):
    Q_load_in = Q_load[k]
    eta_result[k], eta_2 = FC_operation(Q_load_in, Q_max, phi_thr)

plt.plot(eta_result)
plt.show()


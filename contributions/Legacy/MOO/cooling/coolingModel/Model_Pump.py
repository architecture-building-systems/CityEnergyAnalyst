# -*- coding: utf-8 -*-

"""
==========================
System Modeling: Pump
==========================



"""
import os
import globalVar as gV
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from math import ceil
reload (gV)


def Pump_Cost(deltaP, mdot, eta_pumping, gV):
    """
    calculates the cost of a pumping device. 
    if the nominal load (electric) is above 375kW, a second pump is assumed
    if the nominal load (electric) is below 500W, a pump with Pel_design = 500W is assumed
    
    Investement costs are calculated upon the life time of a GHP ( 20y) and a GHP- related interest rate of 6%
    
    Parameters
    ----------
    deltaP : float
        Pressure drop that has to be overcome with the pump (nominal)
        
    mdot : float
        mass flow (nominal)
    
    eta_pumping : float
        pump efficiency (set 0.8 as standard value, eta = E_pumping / E_elec)
    
    Returns
    -------
    InvC_return : float
        total investment Cost in CHF
    
    InvCa : float
        annualized investment costs in CHF/year
        
    """

    E_pumping_required = mdot * deltaP /gV.rho_60 
    P_motor_tot = E_pumping_required / eta_pumping

    PmaxPumpkW = 375.0
    PpumpMinkW = 0.5
    
    nPumps = int(ceil(P_motor_tot / 1000.0 / PmaxPumpkW))
    
    PpumpArray = np.zeros((nPumps))
    PpumpRemain = P_motor_tot
    
    #if PpumpRemain < PpumpMinkW * 1000:
     #   PpumpRemain = PpumpMinkW * 1000
        

    x = [0.4999, 0.75, 1.1, 1.5, 2.2, 3, 4, 5.5, 7.5, 11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200, 220, 260, 315, 335, 375] # Nominal load in kW
    y = [630, 580, 500, 420, 350, 315, 285, 260, 240, 220, 210, 205, 195, 190, 185, 182, 180, 176, 175, 174, 173, 170, 169, 168, 167, 165, 162, 161.9] # efficiency in % 
        # do the interpolation 
    x1 = [0.4999, 0.75, 1.1, 1.5, 2.2, 3, 4, 5.5, 7.5, 11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200, 220, 260, 315, 335, 375] # Nominal load in kW
    y1 = [720, 680, 585, 425, 330, 275, 220, 195, 180, 150, 145, 143, 135, 120, 115, 114, 110, 100, 90, 88, 85, 80, 75, 74, 74, 73, 72, 71.9] # efficiency in % 
    InvC_mot= interp1d(x, y, kind='cubic')
    InvC_VFC = interp1d(x1, y1, kind='cubic')
    
    InvC = 0.0
    InvCa = 0.0
    
    for pump_i in range(nPumps):
        # calculate pump nominal capacity
        
        PpumpArray[pump_i] =  min(PpumpRemain, PmaxPumpkW*1000)
        if PpumpArray[pump_i] < PpumpMinkW * 1000:
            PpumpArray[pump_i] = PpumpMinkW * 1000
        PpumpRemain -= PpumpArray[pump_i] 
        
        # Calculate cost
        InvC += InvC_mot(PpumpArray[pump_i]/1000.0) + InvC_VFC(PpumpArray[pump_i]/1000.0)
        InvCa +=  InvC * gV.GHP_i * (1+ gV.GHP_i) ** gV.GHP_nHP / ((1+gV.GHP_i) ** gV.GHP_nHP - 1) 

    return InvCa



def Pump_operation(P_design):

    """
    Modeled after:
        05_merkblatt_wirtschaftlichkeit_14.pdf
        23_merkblatt_pumpen_web.pdf
        ER_2010_11_Heizungspumpen.pdf
        MerkblattPreiseFU2010_2011.pdf
        MerkblattPreiseMotoren2010_2011.pdf
    
    Parameters
    ----------
    P_design : float
        Load of time step
        
    Returns
    -------
    eta_el : float
        electric efficiency of Pumping operation in abs. numbers (e.g. 0.93) 

    
    
    
    """
    
    x = [0.5, 0.75, 1.1, 1.5, 2.2, 3, 4, 5.5, 7.5, 11, 15, 18, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200, 220] # Nominal load in kW
    y = [83, 83.5, 84, 85.2, 86.8, 87.8, 88.8, 89.5, 90.5, 91.5, 92.2, 92.6, 93, 93.6, 93.9, 94.3, 94.6, 95, 95.2, 95.4, 95.6, 95.9, 96,96] # efficiency in % 
        # do the interpolation 
    eff_of_Pmax = interp1d(x, y, kind='cubic')
    eta_motor = eff_of_Pmax(float(P_design) / float(100))
    eta_pump_fluid = 0.8
    eta_pumping = eta_pump_fluid * eta_motor
    return eta_pumping, eta_pump_fluid, eta_motor

""" 
    #    USED FOR PLOTS:
    


Q_load = np.linspace(0.5,375, 10000)
 
eta_result_el = np.zeros(len(Q_load)) 
eta_result_th = np.zeros(len(Q_load))
eta_result_tot = np.zeros(len(Q_load))
Q_max = max(Q_load) 
x = [0.5, 0.75, 1.1, 1.5, 2.2, 3, 4, 5.5, 7.5, 11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200, 220, 260, 315, 335, 375] # Nominal load in kW
y = [680, 630, 580, 500, 420, 350, 315, 285, 260, 235, 220, 210, 205, 195, 190, 185, 182, 180, 176, 175, 174, 173, 170, 169, 168, 167, 165, 162] # efficiency in % 
    # do the interpolation 

x1 = [0.5, 0.75, 1.1, 1.5, 2.2, 3, 4, 5.5, 7.5, 11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200, 220, 260, 315, 335, 375] # Nominal load in kW
y1 = [720, 680, 585, 425, 330, 275, 220, 195, 180, 160, 150, 143, 135, 120, 115, 114, 110, 100, 90, 88, 85, 80, 75, 74, 74, 73, 72,72] # efficiency in % 



InvC_VFC = interp1d(x1, y1, kind='cubic')
InvC = interp1d(x, y, kind='cubic')
for k in range(len(Q_load)):
    Q_load_in = Q_load / 1000
    

    
eta_el, = plt.plot(Q_load, InvC(Q_load), 'r-', label="InvC_motor")
eta_th, = plt.plot(Q_load, InvC_VFC(Q_load) , 'b-', label="InvC_VFC")
eta_tot, = plt.plot(Q_load, InvC_VFC(Q_load) + 2*InvC(Q_load) , 'g-', label="InvC_tot")
#eta_tot, = plt.plot(eta_result_tot, 'g-', label="eta_tot")
plt.legend([eta_tot, eta_el,eta_th],["Total Pump Investment Cost","Investement Cost Motor","Investment Cost VFC"], loc='best')

plt.ylabel('Investment Cost in CHF/kW')
plt.xlabel('Nominal Power of Motor in kW')
plt.xlim([-1,375])
#plt.ylim([0,1])
plt.show()
"""
# -*- coding: utf-8 -*-
"""
==================================================
Investment costs of the energy system tech
==================================================

"""
from __future__ import division
from math import floor, log, ceil
import globalVar as gV
reload(gV)
from scipy.interpolate import interp1d
import numpy as np


def StorageCosts(vol, gV):
    """
    vol in m3
    50y lifetime
    """
    if vol>0:
        InvCa = 7224.8 * vol ** (-0.522) * vol * gV.EURO_TO_CHF / 50 
    else:
        InvCa = 0

    return InvCa # CHF/a


def Heatexch_Cost(Q_design, gV):
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
        annualized investment costs in CHF/y
        
    """
    if Q_design > 0:
        InvC = 3000 # after A+W 
    
        if Q_design >= 50000 and Q_design <= 80000:
            InvC = 3000 + 2.0/30 * (Q_design - 50000) # linear interpolation of A+W data
            
        if Q_design  >= 80000 and Q_design < 100000:
            InvC = 5000.0
            #print "A"
        
        if Q_design > 100000: 
            InvC = 80 * Q_design / 1000.0 - 3000
            #print "B"

        InvCa =  InvC * gV.Subst_i * (1+ gV.Subst_i) ** gV.Subst_n / ((1+gV.Subst_i) ** gV.Subst_n - 1) 
             
    else:
        InvCa = 0
        
    return InvCa
    

def Cond_Boiler_InvCost(Q_design, Q_annual, gV):
    """
    Calculates the annual cost of a boiler (based on A+W cost of oil boilers) [CHF / a]
    and Faz. 2012 data
    
    Parameters
    ----------
    Q_design : float
        Design Load of Boiler in WATT
    
    Q_annual : float
        Annual thermal load required from Boiler in WATT HOUR
    Returns
    -------
    InvCa : float
        annualized investment costs in CHF/a including Maintainance Cost
        
    """
    if Q_design >0:
        InvC = 28000 # after A+W 
        
        if Q_design <= 90000 and Q_design >= 28000:
            InvC_exkl_MWST = 28000 + 0.275 * (Q_design - 28000) # linear interpolation of A+W data
            InvC = (gV.MWST + 1) * InvC_exkl_MWST
            
        elif Q_design > 90000 and Q_design  <= 320000: # 320kW = maximum Power of conventional Gas Boiler, 
            InvC = 45000 + 0.11 * (Q_design - 90000) 
        
        InvCa =  InvC * gV.Boiler_i * (1+ gV.Boiler_i) ** gV.Boiler_n / ((1+gV.Boiler_i) ** gV.Boiler_n - 1) 
                
        if Q_design > 320000: # 320kW = maximum Power of conventional Gas Boiler 
            InvCa = gV.EURO_TO_CHF * (84000 + 14 * Q_design / 1000) # after Faz.2012
        
        Maint_C_annual = gV.Boiler_C_maintainance_faz * Q_annual / 1E6 * gV.EURO_TO_CHF # 3.5 euro per MWh_th FAZ 2013
        #Labour_C = gV.Boiler_C_labour * Q_annual / 1E6 * gV.EURO_TO_CHF # approx 4 euro per MWh_th
        
        InvCa += Maint_C_annual #+ Labour_C
        
    else:
        InvCa = 0
    
    return InvCa


def CC_InvC(CC_size, gV):
    """
    Annualized investment costs for the Combined cycle
    
    Parameters
    ----------
    CC_size : float
        Electrical size of the CC
        
    Returns
    -------
    InvCa : float
        annualized investment costs in CHF
    
    """
    InvC = 32978 * (CC_size * 1E-3) ** 0.5946
    InvCa = InvC * gV.CC_i * (1+ gV.CC_i) ** gV.CC_n / \
            ((1+gV.CC_i) ** gV.CC_n - 1)

    return InvCa


def Furnace_InVCost(P_design, Q_annual, gV):
    """
    Calculates the cost of a Furnace
    based on Bioenergy 2020 (AFO) and POLYCITY Ostfildern 
    
    Excludes Operating and Labour Costs!
    
    
    Parameters
    ----------
    P_design : float
        Design Power of Furnace Plant (Boiler Thermal power!!) [W]
        
    Q_annual : float
        annual thermal Power output [Wh]
    
    Returns
    -------
    InvC_return : float
        total investment Cost for building the plant
    
    InvCa : float
        annualized investment costs in CHF including labour, operation and maintainance
        
    """
    InvC = 0.670 * gV.EURO_TO_CHF * P_design # 670 € /kW therm(Boiler) = 800 CHF /kW (A+W data) 

    Ca_invest =  (InvC * gV.Boiler_i * (1+ gV.Boiler_i) ** gV.Boiler_n / ((1+gV.Boiler_i) ** gV.Boiler_n - 1)) 
    Ca_maint = Ca_invest * gV.Boiler_C_maintainance
    Ca_labour =  gV.Boiler_C_labour / 1000000.0 * gV.EURO_TO_CHF * Q_annual 

    InvCa = Ca_invest + Ca_maint + Ca_labour
    
    return InvCa


def HP_InvCost(HP_Size, gV):
    """
    Calculates the annualized investment costs for the heat pump
    
    Parameters
    ----------
    HP_Size : float
        Design THERMAL size of the heat pump in WATT THERMAL
    
    Returns
    -------
    InvCa : float
        annualized investment costs in CHF/a
        
    """
    if HP_Size > 0:
        InvC = (-493.53 * log(HP_Size * 1E-3) + 5484) * (HP_Size * 1E-3)
        InvCa = InvC * gV.HP_i * (1+ gV.HP_i) ** gV.HP_n / \
                ((1+gV.HP_i) ** gV.HP_n - 1)
                
    else:
        InvCa = 0
    
    return InvCa


def GHP_InvCost(GHP_Size, gV):
    """
    Calculates the annualized investment costs for the geothermal heat pump
    
    Parameters
    ----------
    GHP_Size : float
        Design ELECTRICAL size of the heat pump in WATT ELECTRICAL
    
    Returns
    -------
    InvCa : float
        annualized investment costs in EUROS/a
        
    """
    nProbe = floor(GHP_Size / gV.GHP_WmaxSize)
    roundProbe = GHP_Size / gV.GHP_WmaxSize - nProbe
    
    InvC_HP = 0
    InvC_BH = 0
    
    InvC_HP += nProbe * 5247.5 * (gV.GHP_WmaxSize * 1E-3) ** 0.49
    InvC_BH += nProbe * 7100 * (gV.GHP_WmaxSize * 1E-3) ** 0.74
    
    InvC_HP += 5247.5 * (roundProbe * gV.GHP_WmaxSize * 1E-3) ** 0.49
    InvC_BH += 7100 * (roundProbe * gV.GHP_WmaxSize * 1E-3) ** 0.74
	
    InvCa = InvC_HP * gV.GHP_i * (1+ gV.GHP_i) ** gV.GHP_nHP / \
            ((1+gV.GHP_i) ** gV.GHP_nHP - 1) + \
            InvC_BH * gV.GHP_i * (1+ gV.GHP_i) ** gV.GHP_nBH / \
            ((1+gV.GHP_i) ** gV.GHP_nBH - 1)

    return InvCa
    

def Pump_Cost(deltaP, mdot, eta_pumping, gV):
    """
    calculates the cost of a pumping device. 
    if the nominal load (electric) is above 375kW, a second pump is assumed
    if the nominal load (electric) is below 500W, a pump with Pel_design = 500W is assumed
    
    Investement costs are calculated upon the life time of a GHP ( 20y) and a GHP- related interest rate of 6%
    
    ParametersF
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
    print P_motor_tot
    print PmaxPumpkW
    nPumps = int(ceil(P_motor_tot / 1000.0 / PmaxPumpkW))
    
    print nPumps," nPumps"

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



def PV_InvC(P_peak):
    """
    P_peak in kW
    result in CHF
    Lifetime 20 y
    """
    if P_peak < 10:
        InvCa = 3500.07 * P_peak /20
    else:
        InvCa = 2500.07 * P_peak /20
    
    return InvCa # [CHF/y]


def SC_InvC(Area):
    """
    Lifetime 35 years
    """
    InvCa = 2050 * Area /35 # [CHF/y]
    
    return InvCa


def PVT_InvC(P_peak):
    """
    P_peak in kW
    result in CHF
    """
    InvCa = 5000 * P_peak /20 # CHF/y
    # 2sol
    
    return InvCa
    
def NetworkInvCost(LengthNetwork, gV):
    """
    Length Network in meters of total length of network
    """
    InvC = 0
    InvC = LengthNetwork * gV.PipeCostPerMeterInv
    InvCa =  InvC * gV.PipeInterestRate * (1+ gV.PipeInterestRate) ** gV.PipeLifeTime / ((1+gV.PipeInterestRate) ** gV.PipeLifeTime - 1) 
    
    return InvCa
    
def GasConnectionCost(PnomGas, gV):
    """
    PnomGas in Watt Peak Capacity of Gas supply
    """
    InvCa = 0
    InvCa = gV.GasConnectionCost * PnomGas # from Energie360 - Zurich
    
    return InvCa
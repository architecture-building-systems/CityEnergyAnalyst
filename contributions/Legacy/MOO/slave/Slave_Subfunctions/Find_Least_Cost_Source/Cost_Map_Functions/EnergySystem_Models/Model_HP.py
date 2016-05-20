"""
==========================
System Modeling: Heat pump
==========================

"""
from __future__ import division
from math import log
#import os

#Energy_Models_path ="/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/EnergySystem_Models"
#os.chdir(Energy_Models_path)
#MS_Var_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave"

import globalVar as gV
#reload (gV)

#os.chdir(MS_Var_Path)
#import Master_to_Slave_Variables as MS_Var
#reload(MS_Var)



class ModelError(Exception):
    pass


def HPLake_Op(mdot, tsup, tret, tlake, gV):
    """
    For the operation of a Heat pump
    between a district heating network and a lake
    
    Parameters
    ----------
    mdot : float
        mass flow rate in the district heating network
    tsup : float
        temperature of supply for the DHN (hot)
    tret : float
        temperature of return for the DHN (cold)
    tlake : float
        temperature of the lake
    
    Returns
    -------
    wdot_el : float
        total electric power needed (compressor and auxiliary)
    qcolddot : float
        cold power needed
    
    """
    tcond = tsup + gV.HP_deltaT_cond
    if tcond > gV.HP_maxT_cond:
        raise ModelError
    
    tevap = tlake - gV.HP_deltaT_evap
    COP = gV.HP_etaex / (1- tevap/tcond)
    qhotdot = mdot * gV.cp * (tsup - tret)
    
    if qhotdot > gV.HP_maxSize:
        print "Qhot above max size on the market !"
    
    wdot = qhotdot / COP 
    wdot_el = wdot / gV.HP_Auxratio

    qcolddot =  qhotdot - wdot

    return wdot_el, qcolddot



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
    InvC = (-493.53 * log(HP_Size * 1E-3) + 5484) * (HP_Size * 1E-3)
    InvCa = InvC * gV.HP_i * (1+ gV.HP_i) ** gV.HP_n / \
            ((1+gV.HP_i) ** gV.HP_n - 1)
    
    return InvCa


#def HPSew_Op(mdot, tsup, tret, Qcold, tretsew, gV):

#    COP = 0.65*(tsup+gV.HP_deltaT_cond)/((tsup+gV.HP_deltaT_cond)-tretsew)
#    Qgen = QmaxSW/(1-(1/COP))

#    return wdot_el, qcolddot, tsup_calc, qhotdot_missing



def GHP_Op_max(tsup, tground, nProbes, gV):
    
    qcoldot = nProbes*gV.GHP_Cmax_Size_th
    COP = gV.HP_etaex*(tsup+gV.HP_deltaT_cond)/((tsup+gV.HP_deltaT_cond)-tground)
    qhotdot = qcoldot /(1-(1/COP))
    
    return qhotdot, COP


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
    InvC_HP = 5247.5 * (GHP_Size * 1E-3) ** 0.49
    InvC_BH = 7100 * (GHP_Size * 1E-3) ** 0.74
	
    InvCa = InvC_HP * gV.GHP_i * (1+ gV.GHP_i) ** gV.GHP_nHP / \
            ((1+gV.GHP_i) ** gV.GHP_nHP - 1) + \
            InvC_BH * gV.GHP_i * (1+ gV.GHP_i) ** gV.GHP_nBH / \
            ((1+gV.GHP_i) ** gV.GHP_nBH - 1)

    return InvCa


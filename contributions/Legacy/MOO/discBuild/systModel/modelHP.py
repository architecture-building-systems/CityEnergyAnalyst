"""
==========================
System Modeling: Heat pump
==========================

"""
from __future__ import division
from math import log, floor
import os


class ModelError(Exception):
    pass


def GHP_Op(mdot, tsup, tret, tground, gV):
    """
    For the operation of a Geothermal Heat pump
    
    Parameters
    ----------
    mdot : float
        mass flow rate in the district heating network
    tsup : float
        temperature of supply to the DHN (hot)
    tret : float
        temperature of return from the DHN (cold)
    tground : float
        temperature of the ground
    
    Returns
    -------
    wdot_el : float
        total electric power needed (compressor and auxiliary)
    qcolddot : float
        cold power needed
    qhotdot_missing : float
        heating energy which cannot be provided by the HP
    tsup2 : supply temperature after HP (to DHN) 
    
    """
    tsup2 = tsup
    
    tcond = tsup + gV.HP_deltaT_cond
    if tcond > gV.HP_maxT_cond:
        #raise ModelError
        tcond = gV.HP_maxT_cond
        tsup2 = tcond - gV.HP_deltaT_cond  # lower the supply temp if necessairy
        
    
    tevap = tground - gV.HP_deltaT_evap
    COP = gV.GHP_etaex / (1- tevap/tcond)
    
    qhotdot = mdot * gV.cp * (tsup2 - tret)  # tsup2 = tsup, if all load can be provided by the HP 
                                             #  else: tsup2 < tsup if max load is not enough
    
    qhotdot_missing = mdot * gV.cp * (tsup - tsup2) #calculate the missing energy if needed
    
    wdot = qhotdot / COP 
    wdot_el = wdot / gV.GHP_Auxratio

    qcolddot =  qhotdot - wdot
    
    #if qcolddot > gV.GHP_CmaxSize:
    #    raise ModelError
    

    return wdot_el, qcolddot, qhotdot_missing, tsup2


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


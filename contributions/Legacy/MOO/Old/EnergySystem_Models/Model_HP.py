"""
==========================
System Modeling: Heat pump
==========================

"""
from __future__ import division
from math import log
import os

Energy_Models_path ="/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/EnergySystem_Models"
os.chdir(Energy_Models_path)
MS_Var_Path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave"

import globalVar as gV
reload (gV)

os.chdir(MS_Var_Path)
import Master_to_Slave_Variables as MS_Var
reload(MS_Var)



class ModelError(Exception):
    pass


def HPLake_Op(mdot, tsup, tret, tlake):
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
        raise ModelError
    
    wdot = qhotdot / COP 
    wdot_el = wdot / gV.HP_Auxratio

    qcolddot =  qhotdot - wdot

    return wdot_el, qcolddot



def HP_InvCost(HP_Size):
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


def HPSew_Op(mdot, tsup, tret, mdotsew, tsupsew):
    """
    For the operation of a Heat pump
    between a district heating network and a sewage
    
    Parameters
    ----------
    mdot : float
        mass flow rate in the district heating network
    tsup : float
        temperature of supply for the DHN (hot)
    tret : float
        temperature of return for the DHN (cold)
    mdotsew : float
        mass flow rate in the sewage
    tsupsew : float
        temperature of supply of the sewage (hot)
    
    Returns
    -------
    wdot_el : float
        total electric power needed (compressor and auxiliary)
        
    qcolddot : float
        cold power needed
        
    tsup_partload : float
        temperature of supply at part load, lower than target temp(!)
        
    qhotdot_missing : float
        missing energy, which could not be produced (At part load)
    
    
    """
    tcond = tsup + gV.HP_deltaT_cond
    if tcond > gV.HP_maxT_cond:
        raise ModelError	
    
    tretsew = (mdotsew * tsupsew - mdot * (tsup - tret) + \
              mdot * (tsup-tret) / gV.HP_etaex * (1 + \
              gV.HP_deltaT_evap / tcond)) / \
              (mdotsew + mdot * (tsup - tret) / gV.HP_etaex / tcond)
    
    
    #if tretsew < gV.Sew_minT: # TIM CHANGED
     #   raise ModelError
       
    
    #TIM CHANGED
    
    mdot_DH = mdot
    
    if tretsew < gV.Sew_minT: # filter too low values for Sewage operation
        tretsew = gV.Sew_minT
        
        mdot_treated = mdotsew * (tsupsew - tretsew) / \
               ((tsup-tret) * ( 1 - 1/gV.HP_etaex * \
               ( 1- tret/tsup) ))
        mdot = mdot_treated
        
    
    tevap = tretsew - gV.HP_deltaT_evap
    COP = gV.HP_etaex / (1- tevap/tcond)
    qhotdot = mdot * gV.cp * (tsup - tret) # W
    
    if qhotdot > gV.HP_maxSize:
        raise ModelError
    
    wdot = qhotdot / COP
    wdot_el = wdot / gV.HP_Auxratio  # electricity needed
    qcolddot =  qhotdot - wdot # cooling energy needed
    
    # Tim EDIT :
    
    tsup_calc = tret  + qhotdot / (mdot_DH * gV.cp) 
    
    qhotdot_missing = max(qhotdot - mdot * gV.cp * (tsup_calc - tret), 0) 
    

    return wdot_el, qcolddot, tsup_calc, qhotdot_missing



def GHP_Op(mdot, tsup, tret, tground):
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
    
    if qcolddot > MS_Var.GHP_max:
        print "ERROR AT GHP SIZE", qcolddot, "Wh Required"
        print "this is ", qcolddot - MS_Var.GHP_max, "Wh more than available"
        print COP 
        print mdot* gV.cp*( tsup -tret)
        #raise ModelError
    

    return wdot_el, qcolddot, qhotdot_missing, tsup2


def GHP_InvCost(GHP_Size):
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


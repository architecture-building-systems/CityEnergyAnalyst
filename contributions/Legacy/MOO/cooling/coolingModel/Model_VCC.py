"""
=========================================
System Modeling: Vapor-compressor chiller
=========================================

"""
from __future__ import division
import globalVar as gV
reload (gV)


class ModelError(Exception):
    pass


def VCC_Op(mdot, tsup, tret, gV):
    """
    For the operation of a Vapor-compressor chiller
    between a district cooling network and a condenser with fresh water
    to a cooling tower
    
    Parameters
    ----------
    mdot : float
        mass flow rate in the district cooling network
    tsup : float
        temperature of supply for the DCN (cold)
    tret : float
        temperature of return for the DCN (hot)
    
    Returns
    -------
    wdot : float
        electric power needed
    qhotdot : float
        heating power to condenser
        
    """
    qcolddot = mdot * gV.cp * (tret - tsup)    
    tcoolin = gV.VCC_tcoolin
    
    if qcolddot == 0:
        wdot = 0
        
    else: 
        #Tim Change:
        #COP = (tret / tcoolin - 0.0201E-3 * qcolddot / tcoolin) \
        #  (0.1980E3 * tret / qcolddot + 168.1846E3 * (tcoolin - tret) / (tcoolin * qcolddot) \
        #  + 0.0201E-3 * qcolddot / tcoolin + 1 - tret / tcoolin)
        
        A = 0.0201E-3 * qcolddot / tcoolin 
        B = tret / tcoolin
        C = 0.1980E3 * tret / qcolddot + 168.1846E3 * (tcoolin - tret) / (tcoolin * qcolddot)
        
        COP = 1 /( (1+C) / (B-A) -1 )
        #print COP, "=COP"
        
        wdot = qcolddot / COP
         
    qhotdot = wdot + qcolddot
    
    return wdot, qhotdot


def VCC_InvC(qcold, gV):
    """
    Annualized investment costs for the vapor compressor chiller
    
    Parameters
    ----------
    qcolddot : float
        COOLING PEAK dem in WATT-HOUR
    
    Returns
    -------
    InvCa in CHF/a
    
    """
    InvCa = 0.65 * 23E6 * gV.USD_TO_CHF * qcold / 37E6 / 25
    
    return InvCa















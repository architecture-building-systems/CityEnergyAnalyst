"""
=========================================
Vapor-compressor chiller
=========================================

"""
from __future__ import division


__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

"""
============================
technical model
============================

"""

def calc_VCC(mdot, tsup, tret, gV):
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


"""
============================
Investment costs
============================

"""


def calc_Cinv_VCC(qcold, gV):
    """
    Annualized investment costs for the vapor compressor chiller
    
    Parameters
    ----------
    qcolddot : float
        COOLING PEAK demand in WATT-HOUR
    
    Returns
    -------
    InvCa in CHF/a
    
    """
    InvCa = 0.65 * 23E6 * gV.USD_TO_CHF * qcold / 37E6 / 25
    
    return InvCa















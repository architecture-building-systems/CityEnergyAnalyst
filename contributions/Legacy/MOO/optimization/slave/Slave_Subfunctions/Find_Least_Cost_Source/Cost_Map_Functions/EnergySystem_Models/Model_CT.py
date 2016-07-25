"""
==============================
System Modeling: Cooling tower
==============================

"""
from __future__ import division
import os
#os.chdir("C:/Users/Thuy-An/Documents/GitHub/urben/Masterarbeit/Clustering")
import globalVar as gV

#reload (gV)


class ModelError(Exception):
    pass


def CT_Op(qhotdot, Qdesign):
    """
    For the operation of a water condenser + direct cooling tower
    
    Parameters
    ----------
    qhotdot : float
        heating power to condenser, From Model_VCC
    Qdesign : float
        Max cooling power
    
    Returns
    -------
    wdot : float
        electric power needed for the variable speed drive fan
        
    """
    assert qhotdot < gV.CT_maxSize
    qpartload = qhotdot / Qdesign

    wdesign_fan = 0.011 * Qdesign
    wpartload = 0.8603 * qpartload ** 3 + 0.2045 * qpartload ** 2 - 0.0623 * \
                qpartload +0.0026
    
    wdot = wpartload * wdesign_fan
    
    return wdot
    

def CT_InvC(CT_size):
    """
    Annualized investment costs for the Combined cycle
    
    Parameters
    ----------
    CT_size : float
        Cooling size of the Cooling tower in WATT
        
    Returns
    -------
    InvCa : float
        annualized investment costs in DOLLARS
    
    """
    InvC = (0.0161 * CT_size * 1E-3 + 1457.3) * 1E3
    InvCa = InvC * gV.CT_a

    return InvCa















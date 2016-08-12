"""
==============================
System Modeling: Cooling tower
==============================

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
def calc_CT(qhotdot, Qdesign, gV):
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
    if qhotdot < gV.CT_maxSize:
        print "Error in CT model, over the max capacity"
    qpartload = qhotdot / Qdesign

    wdesign_fan = 0.011 * Qdesign
    wpartload = 0.8603 * qpartload ** 3 + 0.2045 * qpartload ** 2 - 0.0623 * \
                qpartload +0.0026
    
    wdot = wpartload * wdesign_fan
    
    return wdot
    

"""
============================
Investment costs
============================

"""

def calc_Cinv_CT(CT_size, gV):
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
    if CT_size > 0:
        InvC = (0.0161 * CT_size * 1E-3 + 1457.3) * 1E3
        InvCa = InvC * gV.CT_a
    else:
        InvCa = 0

    return InvCa















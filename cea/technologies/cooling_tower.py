"""
System Modeling: Cooling tower
"""
from __future__ import division


__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# technical model

def calc_CT(qhotdot, Qdesign, gV):
    """
    For the operation of a water condenser + direct cooling tower based on [B. Stephane, 2012]_
    
    :type qhotdot : float
    :param qhotdot: heating power to condenser, From Model_VCC
    :type Qdesign : float
    :param Qdesign: Max cooling power
    

    :type wdot : float
    :param wdot: electric power needed for the variable speed drive fan

    ..[B. Stephane, 2012] B. Stephane (2012), Evidence-Based Model Calibration for Efficient Building Energy Services.
    PhD Thesis, University de Liege, Belgium
    """
    if qhotdot < gV.CT_maxSize:
        print "Error in CT model, over the max capacity"
    qpartload = qhotdot / Qdesign

    wdesign_fan = 0.011 * Qdesign
    wpartload = 0.8603 * qpartload ** 3 + 0.2045 * qpartload ** 2 - 0.0623 * \
                qpartload + 0.0026
    
    wdot = wpartload * wdesign_fan
    
    return wdot
    

# Investment costs

def calc_Cinv_CT(CT_size, gV):
    """
    Annualized investment costs for the Combined cycle

    :type CT_size : float
    :param CT_size: Size of the Cooling tower in [W]

    :rtype InvCa : float
    :returns InvCa: annualized investment costs in Dollars
    """
    if CT_size > 0:
        InvC = (0.0161 * CT_size * 1E-3 + 1457.3) * 1E3
        InvCa = InvC * gV.CT_a
    else:
        InvCa = 0

    return InvCa















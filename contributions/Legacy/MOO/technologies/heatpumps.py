"""
==================================================
heatpumps
==================================================

"""


from __future__ import division
from math import floor, log


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
investment and maintenance costs
============================

"""

def calc_Cinv_GHP(GHP_Size, gV):
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


def calc_Cinv_HP(HP_Size, gV):
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


"""
==================================================
heat exchangers
==================================================

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
investment and maintenance costs
============================

"""


def calc_Cinv_HEX(Q_design, gV):
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

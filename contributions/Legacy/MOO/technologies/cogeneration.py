"""
==================================================
cogeneration (combined heat and power)
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

def calc_Cinv_CCT(CC_size, gV):
    """
    Annualized investment costs for the Combined cycle

    Parameters
    ----------
    CC_size : float
        Electrical size of the CC

    Returns
    -------
    InvCa : float
        annualized investment costs in CHF

    """
    InvC = 32978 * (CC_size * 1E-3) ** 0.5946
    InvCa = InvC * gV.CC_i * (1+ gV.CC_i) ** gV.CC_n / \
            ((1+gV.CC_i) ** gV.CC_n - 1)

    return InvCa


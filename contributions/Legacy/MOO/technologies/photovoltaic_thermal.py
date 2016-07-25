"""
==================================================
Photovoltaic thermal panels
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


def calc_Cinv_PVT(P_peak):
    """
    P_peak in kW
    result in CHF
    """
    InvCa = 5000 * P_peak /20 # CHF/y
    # 2sol

    return InvCa


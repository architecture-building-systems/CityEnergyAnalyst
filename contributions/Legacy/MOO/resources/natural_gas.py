"""
==================================================
natural gas
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

def calc_Cinv_gas(PnomGas, gV):
    """
    PnomGas in Watt Peak Capacity of Gas supply for connection to gas
    """
    InvCa = 0
    InvCa = gV.GasConnectionCost * PnomGas # from Energie360 - Zurich

    return InvCa

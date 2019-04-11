"""
natural gas
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

# investment and maintenance costs

def calc_Cinv_gas(PnomGas, gv):
    """
    Calculate investment cost of natural gas connections.

    :param PnomGas: peak natural gas supply in [W]
    :type PnomGas: float
    :param gv: globalvar.py

    :returns InvCa:
    :rtype InvCa:

    """

    InvCa = 0
    InvCa = gv.GasConnectionCost * PnomGas # from Energie360 - Zurich

    return InvCa

"""
hydraulic network
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

def calc_Cinv_network_linear(LengthNetwork, gV):
    """
    calculate annualised network investment cost with a linearized function.

    :param LengthNetwork: total length of the network in [m]
    :pram gV: globalvar.py

    :returns InvCa: annualised investment cost of the thermal network
    :rtype InvCa: float

    """

    InvC = 0
    InvC = LengthNetwork * gV.PipeCostPerMeterInv
    InvCa = InvC * gV.PipeInterestRate * (1+ gV.PipeInterestRate) ** gV.PipeLifeTime / ((1+gV.PipeInterestRate) ** gV.PipeLifeTime - 1)

    return InvCa


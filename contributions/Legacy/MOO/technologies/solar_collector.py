"""
==================================================
solar collectors
==================================================

"""


from __future__ import division
from math import floor, log, ceil

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

def calc_Cinv_SC(Area):
    """
    Lifetime 35 years
    """
    InvCa = 2050 * Area /35 # [CHF/y]

    return InvCa


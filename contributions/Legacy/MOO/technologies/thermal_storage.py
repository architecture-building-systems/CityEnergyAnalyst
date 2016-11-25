"""
==================================================
thermal storage
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


def calc_Cinv_storage(vol, gV):
    """
    vol in m3
    50y lifetime
    """
    if vol>0:
        InvCa = 7224.8 * vol ** (-0.522) * vol * gV.EURO_TO_CHF / 50
    else:
        InvCa = 0

    return InvCa # CHF/a


# -*- coding: utf-8 -*-
"""
=========================================
datacenter loads
=========================================

"""
from __future__ import division

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


"""
=========================================
final datacenter loads
=========================================
"""

def calc_Qcdataf(Edataf):
    if Edataf > 0:
        Tcdataf_re_0 = 15
        Tcdataf_sup_0 = 7
        Qcdataf = Edataf * 0.9
        mcpref = Qcdataf/(Tcdataf_re_0-Tcdataf_sup_0)
    else:
        Qcdataf  = 0
        Tcdataf_re_0 = 0
        Tcdataf_sup_0 = 0
        mcpref = 0
    return Qcdataf, mcpref, Tcdataf_re_0, Tcdataf_sup_0

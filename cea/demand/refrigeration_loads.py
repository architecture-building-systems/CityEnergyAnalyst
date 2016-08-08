# -*- coding: utf-8 -*-
"""
=========================================
refrigeration loads
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
final refrigeration loads
=========================================
"""

def calc_Qcref(Eref):
    if Eref > 0:
        COP = 2.7
        Tcref_re_0 = 5
        Tcref_sup_0 = 1
        Qcref = Eref*(COP)
        mcpref = Qcref/(Tcref_re_0-Tcref_sup_0)
    else:
        Qcref = 0
        mcpref = 0
        Tcref_re_0 = 0
        Tcref_sup_0 = 0

    return Qcref, mcpref, Tcref_re_0, Tcref_sup_0

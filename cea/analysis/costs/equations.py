
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import numpy as np

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# Calculates the EQUIVALENT ANNUAL COSTS (1. Step PRESENT VALUE OF COSTS (PVC), 2. Step EQUIVALENT ANNUAL COSTS)
def calc_opex_annualized(OpC_USDyr, Inv_IR_perc, Inv_LT_yr):
    Inv_IR = Inv_IR_perc / 100
    opex_list = [0.0]
    opex_list.extend(Inv_LT_yr * [OpC_USDyr])
    opexnpv = np.npv(Inv_IR, opex_list)
    EAC = ((opexnpv * Inv_IR) / (1 - (1 + Inv_IR) ** (-Inv_LT_yr)))  # calculate positive EAC
    return EAC

def calc_capex_annualized(InvC_USD, Inv_IR_perc, Inv_LT_yr):
    Inv_IR = Inv_IR_perc / 100
    return -((-InvC_USD * Inv_IR) / (1 - (1 + Inv_IR) ** (-Inv_LT_yr)))

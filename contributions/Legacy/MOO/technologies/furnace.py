# -*- coding: utf-8 -*-
"""
==================================================
furnaces
==================================================

"""
from __future__ import division

import globalVar as gV
reload(gV)

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

def calc_Cinv_furnace(P_design, Q_annual, gV):
    """
    Calculates the cost of a Furnace
    based on Bioenergy 2020 (AFO) and POLYCITY Ostfildern 

    
    Parameters
    ----------
    P_design : float
        Design Power of Furnace Plant (Boiler Thermal power!!) [W]
        
    Q_annual : float
        annual thermal Power output [Wh]
    
    Returns
    -------
    InvC_return : float
        total investment Cost for building the plant
    
    InvCa : float
        annualized investment costs in CHF including labour, operation and maintainance
        
    """
    InvC = 0.670 * gV.EURO_TO_CHF * P_design # 670 € /kW therm(Boiler) = 800 CHF /kW (A+W data) 

    Ca_invest =  (InvC * gV.Boiler_i * (1+ gV.Boiler_i) ** gV.Boiler_n / ((1+gV.Boiler_i) ** gV.Boiler_n - 1)) 
    Ca_maint = Ca_invest * gV.Boiler_C_maintainance
    Ca_labour =  gV.Boiler_C_labour / 1000000.0 * gV.EURO_TO_CHF * Q_annual 

    InvCa = Ca_invest + Ca_maint + Ca_labour
    
    return InvCa


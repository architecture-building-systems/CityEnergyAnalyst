"""
==================================================
Boilers
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

def calc_Cinv_boiler(Q_design, Q_annual, gV):
    """
    Calculates the annual cost of a boiler (based on A+W cost of oil boilers) [CHF / a]
    and Faz. 2012 data

    Parameters
    ----------
    Q_design : float
        Design Load of Boiler in WATT

    Q_annual : float
        Annual thermal load required from Boiler in WATT HOUR
    Returns
    -------
    InvCa : float
        annualized investment costs in CHF/a including Maintainance Cost

    """
    if Q_design >0:
        InvC = 28000 # after A+W

        if Q_design <= 90000 and Q_design >= 28000:
            InvC_exkl_MWST = 28000 + 0.275 * (Q_design - 28000) # linear interpolation of A+W data
            InvC = (gV.MWST + 1) * InvC_exkl_MWST

        elif Q_design > 90000 and Q_design  <= 320000: # 320kW = maximum Power of conventional Gas Boiler,
            InvC = 45000 + 0.11 * (Q_design - 90000)

        InvCa =  InvC * gV.Boiler_i * (1+ gV.Boiler_i) ** gV.Boiler_n / ((1+gV.Boiler_i) ** gV.Boiler_n - 1)

        if Q_design > 320000: # 320kW = maximum Power of conventional Gas Boiler
            InvCa = gV.EURO_TO_CHF * (84000 + 14 * Q_design / 1000) # after Faz.2012

        Maint_C_annual = gV.Boiler_C_maintainance_faz * Q_annual / 1E6 * gV.EURO_TO_CHF # 3.5 euro per MWh_th FAZ 2013
        #Labour_C = gV.Boiler_C_labour * Q_annual / 1E6 * gV.EURO_TO_CHF # approx 4 euro per MWh_th

        InvCa += Maint_C_annual #+ Labour_C

    else:
        InvCa = 0

    return InvCa


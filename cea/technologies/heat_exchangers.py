"""
heat exchangers
"""


from __future__ import division
from math import log, ceil
import pandas as pd
import numpy as np
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.technologies.constants import MAX_NODE_FLOW

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# investment and maintenance costs

def calc_Cinv_HEX(Q_design_W, locator, config, technology_type):
    """
    Calculates the cost of a heat exchanger (based on A+W cost of oil boilers) [CHF / a]

    :type Q_design_W : float
    :param Q_design_W: Design Load of Boiler

    :param gv: globalvar.py

    :rtype InvC_return : float
    :returns InvC_return: total investment Cost in [CHF]

    :rtype InvCa : float
    :returns InvCa: annualized investment costs in [CHF/a]

    """
    if Q_design_W > 0:
        HEX_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="HEX")
        HEX_cost_data = HEX_cost_data[HEX_cost_data['code'] == technology_type]
        # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
        # capacity for the corresponding technology from the database
        if Q_design_W < HEX_cost_data.iloc[0]['cap_min']:
            Q_design_W = HEX_cost_data.iloc[0]['cap_min']
        HEX_cost_data = HEX_cost_data[
            (HEX_cost_data['cap_min'] <= Q_design_W) & (HEX_cost_data['cap_max'] > Q_design_W)]

        Inv_a = HEX_cost_data.iloc[0]['a']
        Inv_b = HEX_cost_data.iloc[0]['b']
        Inv_c = HEX_cost_data.iloc[0]['c']
        Inv_d = HEX_cost_data.iloc[0]['d']
        Inv_e = HEX_cost_data.iloc[0]['e']
        Inv_IR = (HEX_cost_data.iloc[0]['IR_%']) / 100
        Inv_LT = HEX_cost_data.iloc[0]['LT_yr']
        Inv_OM = HEX_cost_data.iloc[0]['O&M_%'] / 100

        InvC = Inv_a + Inv_b * (Q_design_W) ** Inv_c + (Inv_d + Inv_e * Q_design_W) * log(Q_design_W)

        Capex_a_HEX_USD = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
        Opex_fixed_HEX_USD = Capex_a_HEX_USD * Inv_OM
        Capex_HEX_USD = InvC

    else:
        Capex_a_HEX_USD = 0
        Opex_fixed_HEX_USD = 0
        Capex_HEX_USD = 0

    return Capex_a_HEX_USD, Opex_fixed_HEX_USD, Capex_HEX_USD

"""
thermal storage
"""


from __future__ import division
import pandas as pd
from math import log

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# investment and maintenance costs

def calc_Cinv_storage(vol, gv, locator, technology=0):
    """
    calculate the annualized investment cost of a thermal storage tank

    :param vol: storage tank volume
    :type vol: float
    :param gv: global.var

    :returns InvCa:

    """
    if vol>0:
        storage_cost_data = pd.read_excel(locator.get_supply_systems(gv.config.region), sheetname="TES")
        technology_code = list(set(storage_cost_data['code']))
        storage_cost_data[storage_cost_data['code'] == technology_code[technology]]
        # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
        # capacity for the corresponding technology from the database
        if vol < storage_cost_data['cap_min'][0]:
            vol = storage_cost_data['cap_min'][0]
        storage_cost_data = storage_cost_data[
            (storage_cost_data['cap_min'] <= vol) & (storage_cost_data['cap_max'] > vol)]

        Inv_a = storage_cost_data.iloc[0]['a']
        Inv_b = storage_cost_data.iloc[0]['b']
        Inv_c = storage_cost_data.iloc[0]['c']
        Inv_d = storage_cost_data.iloc[0]['d']
        Inv_e = storage_cost_data.iloc[0]['e']
        Inv_IR = (storage_cost_data.iloc[0]['IR_%']) / 100
        Inv_LT = storage_cost_data.iloc[0]['LT_yr']
        Inv_OM = storage_cost_data.iloc[0]['O&M_%'] / 100

        InvC = Inv_a + Inv_b * (vol) ** Inv_c + (Inv_d + Inv_e * vol) * log(vol)

        Capex_a = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
        Opex_fixed = Capex_a * Inv_OM
  # TODO: make sure the cost of heat pump is added
    else:
        Capex_a = 0
        Opex_fixed = 0

    return Capex_a, Opex_fixed


# -*- coding: utf-8 -*-
"""
This file imports the price details from the cost database as a class. This helps in preventing multiple importing
of the corresponding values in individual files.
"""
from __future__ import division
import pandas as pd
import numpy as np
from cea.constants import HOURS_IN_YEAR

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


class Prices(object):
    def __init__(self, locator, detailed_electricity_pricing):
        electricity_costs = pd.read_excel(locator.get_electricity_costs(), sheet_name="ELECTRICITY")
        pricing = pd.read_excel(locator.get_supply_systems(), sheet_name="Pricing")
        resources_lca = pd.read_excel(locator.get_life_cycle_inventory_supply_systems(), sheet_name="RESOURCES")

        self.NG_PRICE = pricing[pricing['Description'] == 'ng_price'].iloc[0]['value'] # in USD/Wh
        self.BG_PRICE = pricing[pricing['Description'] == 'bg_price'].iloc[0]['value'] # in USD/Wh
        self.CPUMP = pricing[pricing['Description'] == 'cpump'].iloc[0]['value']
        self.CC_MAINTENANCE_PER_KWHEL = pricing[pricing['Description'] == 'cc_maintenance_per_kWhel'].iloc[0]['value']
        self.EURO_TO_CHF = pricing[pricing['Description'] == 'euro_to_chf'].iloc[0]['value']
        self.USD_TO_CHF = pricing[pricing['Description'] == 'usd_to_chf'].iloc[0]['value']
        self.MWST = pricing[pricing['Description'] == 'mwst'].iloc[0]['value']


        if detailed_electricity_pricing:
            self.ELEC_PRICE = electricity_costs['cost_kWh'].values / 1000  # in USD_2015 per Wh
            self.ELEC_PRICE_EXPORT = electricity_costs['cost_sell_kWh'].values / 1000  # in USD_2015 per Wh
        else:
            average_electricity_price = resources_lca[resources_lca['Description'] == 'Electricity'].iloc[0][
                                            'costs_kWh'] / 1000

            average_electricity_selling_price = resources_lca[resources_lca['Description'] == 'Electricity'].iloc[0][
                                                    'costs_kWh'] / 1000
            self.ELEC_PRICE = np.ones(HOURS_IN_YEAR) * average_electricity_price  # in USD_2015 per Wh
            self.ELEC_PRICE_EXPORT = np.ones(HOURS_IN_YEAR) * average_electricity_selling_price  # in USD_2015 per Wh


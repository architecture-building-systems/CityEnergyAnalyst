# -*- coding: utf-8 -*-
"""
This file imports the price details from the cost database as a class. This helps in preventing multiple importing
of the corresponding values in individual files.
"""
from __future__ import division
import pandas as pd
import numpy as np
from cea.constants import HOURS_IN_YEAR

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


class Prices(object):
    def __init__(self, locator, detailed_electricity_pricing):
        pricing = pd.read_excel(locator.get_database_supply_systems(), sheet_name="FEEDSTOCKS")
        self.NG_PRICE = pricing[pricing['Code'] == 'NATURALGAS'].iloc[0]['Opex_var_buy_USD2015perkWh'] / 1000 # in USD/Wh
        self.BG_PRICE = pricing[pricing['Code'] == 'BIOGAS'].iloc[0]['Opex_var_buy_USD2015perkWh']  / 1000# in USD/Wh
        self.WB_PRICE = pricing[pricing['Code'] == 'WASTE'].iloc[0]['Opex_var_buy_USD2015perkWh']  / 1000# in USD/Wh
        self.DB_PRICE = pricing[pricing['Code'] == 'WOOD'].iloc[0]['Opex_var_buy_USD2015perkWh'] / 1000 # in USD/Wh
        self.SOLAR_PRICE = pricing[pricing['Code'] == 'SOLAR'].iloc[0]['Opex_var_buy_USD2015perkWh']  / 1000# in USD/Wh
        self.SOLAR_PRICE_EXPORT = pricing[pricing['Code'] == 'SOLAR'].iloc[0]['Opex_var_sell_USD2015perkWh'] / 1000 # in USD/Wh

        if detailed_electricity_pricing:
            electricity_costs = pd.read_excel(locator.get_database_supply_systems(), sheet_name="DETAILED_ELEC_COSTS")
            self.ELEC_PRICE = electricity_costs['Opex_var_buy_USD2015perkWh'].values / 1000  # in USD_2015 per Wh
            self.ELEC_PRICE_EXPORT = electricity_costs['Opex_var_sell_USD2015perkWh'].values / 1000  # in USD_2015 per Wh
        else:
            average_electricity_price = pricing[pricing['Code'] == 'GRID'].iloc[0]['Opex_var_buy_USD2015perkWh'] / 1000
            average_electricity_selling_price = pricing[pricing['Code'] == 'GRID'].iloc[0]['Opex_var_sell_USD2015perkWh'] / 1000
            self.ELEC_PRICE = np.ones(HOURS_IN_YEAR) * average_electricity_price  # in USD_2015 per Wh
            self.ELEC_PRICE_EXPORT = np.ones(HOURS_IN_YEAR) * average_electricity_selling_price  # in USD_2015 per Wh


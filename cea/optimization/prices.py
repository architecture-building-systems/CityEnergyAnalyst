# -*- coding: utf-8 -*-
"""
This file imports the price details from the cost database as a class. This helps in preventing multiple importing
of the corresponding values in individual files.
"""
from __future__ import division
import numpy as np

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


class Prices(object):
    def __init__(self, supply_systems):
        pricing = supply_systems.FEEDSTOCKS
        self.NG_PRICE = np.tile(
            pricing['NATURALGAS']['Opex_var_buy_USD2015kWh'].values / 1000,  365)  # in USD/Wh for every hour of a year
        self.BG_PRICE = np.tile(
            pricing['BIOGAS']['Opex_var_buy_USD2015kWh'].values / 1000,  365)   # in USD/Wh for every hour of a year
        self.WB_PRICE = np.tile(
            pricing['WETBIOMASS']['Opex_var_buy_USD2015kWh'].values / 1000,  365)   # in USD/Wh for every hour of a year
        self.DB_PRICE = np.tile(
            pricing['DRYBIOMASS']['Opex_var_buy_USD2015kWh'].values / 1000,  365)   # in USD/Wh for every hour of a year
        self.SOLAR_PRICE = np.tile(
            pricing['SOLAR']['Opex_var_buy_USD2015kWh'].values / 1000,  365)  # in USD/Wh for every hour of a year
        self.SOLAR_PRICE_EXPORT = np.tile(
            pricing['SOLAR']['Opex_var_sell_USD2015kWh'].values / 1000,  365)   # in USD/Wh for every hour of a year
        self.ELEC_PRICE = np.tile(
            pricing['GRID']['Opex_var_buy_USD2015kWh'].values / 1000,  365)   # in USD/Wh for every hour of a year
        self.ELEC_PRICE_EXPORT = np.tile(
            pricing['GRID']['Opex_var_sell_USD2015kWh'].values / 1000,  365)  # in USD/Wh for every hour of a year

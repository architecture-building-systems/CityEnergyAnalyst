# -*- coding: utf-8 -*-
"""
This file imports the price details from the cost database as a class. This helps in preventing multiple importing
of the corresponding values in individual files.
"""
from __future__ import division

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
        self.NG_PRICE = list(
            pricing['NATURALGAS']['Opex_var_buy_USD2015perkWh'] / 1000) * 365  # in USD/Wh for every hour of a year
        self.BG_PRICE = list(
            pricing['BIOGAS']['Opex_var_buy_USD2015perkWh'] / 1000) * 365  # in USD/Wh for every hour of a year
        self.WB_PRICE = list(
            pricing['WETBIOMASS']['Opex_var_buy_USD2015perkWh'] / 1000) * 365  # in USD/Wh for every hour of a year
        self.DB_PRICE = list(
            pricing['DRYBIOMASS']['Opex_var_buy_USD2015perkWh'] / 1000) * 365  # in USD/Wh for every hour of a year
        self.SOLAR_PRICE = list(
            pricing['SOLAR']['Opex_var_buy_USD2015perkWh'] / 1000) * 365  # in USD/Wh for every hour of a year
        self.SOLAR_PRICE_EXPORT = list(
            pricing['SOLAR']['Opex_var_sell_USD2015perkWh']) * 365  # in USD/Wh for every hour of a year
        self.ELEC_PRICE = list(
            pricing['GRID']['Opex_var_buy_USD2015perkWh'] / 1000) * 365  # in USD/Wh for every hour of a year
        self.ELEC_PRICE_EXPORT = list(
            pricing['GRID']['Opex_var_sell_USD2015perkWh'] / 1000) * 365  # in USD/Wh for every hour of a year

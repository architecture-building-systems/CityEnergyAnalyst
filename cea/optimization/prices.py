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
    def __init__(self, supply_systems):
        pricing = supply_systems.FEEDSTOCKS
        self.NG_PRICE = pricing['NATURALGAS']['Opex_var_buy_USD2015perkWh'] / 1000 # in USD/Wh
        self.BG_PRICE = pricing['BIOGAS']['Opex_var_buy_USD2015perkWh']  / 1000# in USD/Wh
        self.WB_PRICE = pricing['WETBIOMASS']['Opex_var_buy_USD2015perkWh']  / 1000# in USD/Wh
        self.DB_PRICE = pricing['DRYBIOMASS']['Opex_var_buy_USD2015perkWh'] / 1000 # in USD/Wh
        self.SOLAR_PRICE = pricing['SOLAR']['Opex_var_buy_USD2015perkWh']  / 1000# in USD/Wh
        self.SOLAR_PRICE_EXPORT = pricing['SOLAR']['Opex_var_sell_USD2015perkWh'] / 1000 # in USD/Wh
        self.ELEC_PRICE = pricing['GRID']['Opex_var_buy_USD2015perkWh'].values / 1000  # in USD_2015 per Wh
        self.ELEC_PRICE_EXPORT = pricing['GRID']['Opex_var_sell_USD2015perkWh'].values / 1000  # in USD_2015 per Wh



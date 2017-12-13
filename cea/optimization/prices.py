# -*- coding: utf-8 -*-
"""
This file imports the price details from the cost database as a class. This helps in preventing multiple importing
of the corresponding values in individual files.
"""
from __future__ import division
import pandas as pd

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


class Prices(object):
    def __init__(self, locator, config):
        pricing = pd.read_excel(locator.get_supply_systems(config.region), sheetname="Pricing")
        self.NG_PRICE = pricing[pricing['Description'] == 'ng_price'].iloc[0]['value']
        self.BG_PRICE = pricing[pricing['Description'] == 'bg_price'].iloc[0]['value']
        self.NG_PRICE_zernez = pricing[pricing['Description'] == 'ng_price_zernez'].iloc[0]['value']
        self.BG_PRICE_zernez = pricing[pricing['Description'] == 'bg_price_zernez'].iloc[0]['value']
        self.ELEC_PRICE = pricing[pricing['Description'] == 'elec_price'].iloc[0]['value']
        self.CPUMP = pricing[pricing['Description'] == 'cpump'].iloc[0]['value']
        self.CC_MAINTENANCE_PER_KWHEL = pricing[pricing['Description'] == 'cc_maintenance_per_kWhel'].iloc[0]['value']
        self.EURO_TO_CHF = pricing[pricing['Description'] == 'euro_to_chf'].iloc[0]['value']
        self.USD_TO_CHF = pricing[pricing['Description'] == 'usd_to_chf'].iloc[0]['value']
        self.MWST = pricing[pricing['Description'] == 'mwst'].iloc[0]['value']


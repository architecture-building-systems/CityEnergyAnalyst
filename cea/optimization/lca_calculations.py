# -*- coding: utf-8 -*-
"""
This file imports the price details from the cost database as a class. This helps in preventing multiple importing
of the corresponding values in individual files.
"""
from __future__ import division

import warnings

import pandas as pd

warnings.filterwarnings("ignore")

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


class LcaCalculations(object):
    def __init__(self, locator):
        resources_lca = pd.read_excel(locator.get_database_supply_systems(), sheet_name="FEEDSTOCKS")
        resources_lca.set_index('code', inplace=True)

        # Natural gas
        self.NG_TO_CO2_EQ = resources_lca.loc['NATURALGAS']['CO2']

        # Drybiomass
        self.DRYBIOMASS_TO_CO2_EQ = resources_lca.loc['DRYBIOMASS']['CO2']

        # WetBiomass
        self.WETBIOMASS_TO_CO2_EQ = resources_lca.loc['WETBIOMASS']['CO2']

        # Electricity MJ/MJoil and kg/MJ
        self.EL_TO_CO2_EQ = resources_lca.loc['GRID']['CO2']

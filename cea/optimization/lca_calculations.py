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
        resources_lca = pd.read_excel(locator.get_life_cycle_inventory_supply_systems(), sheet_name="RESOURCES")
        resources_lca.set_index('code', inplace=True)

        # Natural gas
        self.NG_TO_CO2_EQ = resources_lca.loc['NATURALGAS']['CO2']
        self.NG_TO_OIL_EQ = resources_lca.loc['NATURALGAS']['PEN']

        # Drybiomass
        self.DRYBIOMASS_TO_CO2_EQ = resources_lca.loc['WOOD']['CO2']
        self.DRYBIOMASS_TO_OIL_EQ = resources_lca.loc['WOOD']['PEN']

        # WetBiomass
        self.WETBIOMASS_TO_CO2_EQ = resources_lca.loc['WASTE']['CO2']
        self.WETBIOMASS_TO_OIL_EQ = resources_lca.loc['WASTE']['PEN']

        # Electricity MJ/MJoil and kg/MJ
        self.EL_TO_CO2_EQ = resources_lca.loc['GRID']['CO2']
        self.EL_TO_OIL_EQ = resources_lca.loc['GRID']['CO2']


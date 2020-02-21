# -*- coding: utf-8 -*-
"""
This file imports the price details from the cost database as a class. This helps in preventing multiple importing
of the corresponding values in individual files.
"""
from __future__ import division

import warnings

import numpy as np

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
    def __init__(self, supply_systems):
        feedstocks = supply_systems.FEEDSTOCKS
        self.NG_TO_CO2_EQ = np.tile(feedstocks['NATURALGAS']['GHG_kgCO2MJ'].values, 365)  # in kgCo2/MJ for every hour of a year
        self.WETBIOMASS_TO_CO2_EQ = np.tile(feedstocks['WETBIOMASS']['GHG_kgCO2MJ'].values, 365) # in kgCo2/MJ for every hour of a year
        self.DRYBIOMASS_TO_CO2_EQ = np.tile(feedstocks['DRYBIOMASS']['GHG_kgCO2MJ'].values, 365) # in kgCo2/MJ for every hour of a year
        self.EL_TO_CO2_EQ = np.tile(feedstocks['GRID']['GHG_kgCO2MJ'].values, 365) # in kgCo2/MJ for every hour of a year

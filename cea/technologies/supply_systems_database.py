"""
This module provides an interface to the "supply_systems.xls" file (locator.get_database_supply_systems()) - the point
is to avoid reading this data (which is constant during the lifetime of a script) again and again.
"""
from __future__ import print_function
from __future__ import division

import pandas as pd
import cea.inputlocator

# keep track of locators previously seen so we don't re-read excel files twice
_locators = {}


class SupplySystemsDatabase(object):
    """
    Expose the worksheets in supply_systems.xls as pandas.Dataframes.
    """
    def __init__(self, locator):
        """        
        :param cea.inputlocator.InputLocator locator: provides the path to the
        """

        all_worksheets = self.read_excel(locator)

        self.ALL_IN_ONE_SYSTEMS = all_worksheets["ALL_IN_ONE_SYSTEMS"]
        self.FEEDSTOCKS = all_worksheets["FEEDSTOCKS"]
        self.PV = all_worksheets["PV"]
        self.SC = all_worksheets["SC"]
        self.PVT = all_worksheets["PVT"]
        self.Boiler = all_worksheets["Boiler"]
        self.Furnace = all_worksheets["Furnace"]
        self.FC = all_worksheets["FC"]
        self.CCGT = all_worksheets["CCGT"]
        self.Chiller = all_worksheets["Chiller"]
        self.Absorption_chiller = all_worksheets["Absorption_chiller"]
        self.CT = all_worksheets["CT"]
        self.HEX = all_worksheets["HEX"]
        self.BH = all_worksheets["BH"]
        self.HP = all_worksheets["HP"]
        self.TES = all_worksheets["TES"]
        self.Pump = all_worksheets["Pump"]
        self.PIPING = all_worksheets["PIPING"]
        self.DETAILED_ELEC_COSTS = all_worksheets["DETAILED_ELEC_COSTS"]

    def read_excel(self, locator):
        """Read in the excel file, using the cache _locators"""
        global _locators
        if locator in _locators:
            all_worksheets = _locators[locator]
        else:
            all_worksheets = pd.read_excel(locator.get_database_supply_systems(), sheet_name=None)
            _locators[locator] = all_worksheets
        return all_worksheets
"""
This module provides an interface to the "supply_systems.xls" file (locator.get_database_supply_systems()) - the point
is to avoid reading this data (which is constant during the lifetime of a script) again and again.
"""




import pandas as pd

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

        conversion_systems_worksheets,\
        distribution_systems_worksheets,\
        feedstocks_worksheets,\
        energy_carriers_worksheet = self.read_excel(locator)

        self.ENERGY_CARRIERS = energy_carriers_worksheet
        self.FEEDSTOCKS = feedstocks_worksheets
        self.PIPING = distribution_systems_worksheets["THERMAL_GRID"]
        self.PV = conversion_systems_worksheets["PV"]
        self.SC = conversion_systems_worksheets["SC"]
        self.PVT = conversion_systems_worksheets["PVT"]
        self.Boiler = conversion_systems_worksheets["Boiler"]
        self.Furnace = conversion_systems_worksheets["Furnace"]
        self.FC = conversion_systems_worksheets["FC"]
        self.CCGT = conversion_systems_worksheets["CCGT"]
        self.Chiller = conversion_systems_worksheets["Chiller"]
        self.Absorption_chiller = conversion_systems_worksheets["Absorption_chiller"]
        self.CT = conversion_systems_worksheets["CT"]
        self.HEX = conversion_systems_worksheets["HEX"]
        self.BH = conversion_systems_worksheets["BH"]
        self.HP = conversion_systems_worksheets["HP"]
        self.TES = conversion_systems_worksheets["TES"]
        self.Pump = conversion_systems_worksheets["Pump"]

    def read_excel(self, locator):
        """Read in the excel file, using the cache _locators"""
        global _locators
        if locator in _locators:
            conversion_systems_worksheets, distribution_systems_worksheets, feedstocks_worksheets, energy_carriers_worksheet = _locators[locator]
        else:
            conversion_systems_worksheets = pd.read_excel(locator.get_database_conversion_systems(), sheet_name=None)
            distribution_systems_worksheets = pd.read_excel(locator.get_database_distribution_systems(), sheet_name=None)
            feedstocks_worksheets = pd.read_excel(locator.get_database_feedstocks(), sheet_name=None)
            energy_carriers_worksheet = pd.read_excel(locator.get_database_energy_carriers(), sheet_name=None)
            _locators[locator] = conversion_systems_worksheets, distribution_systems_worksheets, feedstocks_worksheets, energy_carriers_worksheet
        return conversion_systems_worksheets, distribution_systems_worksheets, feedstocks_worksheets, energy_carriers_worksheet

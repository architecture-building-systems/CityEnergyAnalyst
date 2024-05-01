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
        self.PHOTOVOLTAIC_PANELS = conversion_systems_worksheets["PHOTOVOLTAIC_PANELS"]
        self.SOLAR_THERMAL_PANELS = conversion_systems_worksheets["SOLAR_THERMAL_PANELS"]
        self.PHOTOVOLTAIC_THERMAL_PANELS = conversion_systems_worksheets["PHOTOVOLTAIC_THERMAL_PANELS"]
        self.BOILERS = conversion_systems_worksheets["BOILERS"]
        self.COGENERATION_PLANTS = conversion_systems_worksheets["COGENERATION_PLANTS"]
        self.HEAT_EXCHANGERS = conversion_systems_worksheets["HEAT_EXCHANGERS"]
        self.VAPOR_COMPRESSION_CHILLERS = conversion_systems_worksheets["VAPOR_COMPRESSION_CHILLERS"]
        self.ABSORPTION_CHILLERS = conversion_systems_worksheets["ABSORPTION_CHILLERS"]
        self.COOLING_TOWERS = conversion_systems_worksheets["COOLING_TOWERS"]
        self.FUEL_CELLS = conversion_systems_worksheets["FUEL_CELLS"]
        self.UNITARY_AIR_CONDITIONERS = conversion_systems_worksheets["UNITARY_AIR_CONDITIONERS"]
        self.HEAT_PUMPS = conversion_systems_worksheets["HEAT_PUMPS"]
        self.THERMAL_ENERGY_STORAGES = conversion_systems_worksheets["THERMAL_ENERGY_STORAGES"]
        self.POWER_TRANSFORMERS = conversion_systems_worksheets["POWER_TRANSFORMERS"]
        self.HYDRAULIC_PUMPS = conversion_systems_worksheets["HYDRAULIC_PUMPS"]
        self.BORE_HOLES = conversion_systems_worksheets["BORE_HOLES"]



    def read_excel(self, locator):
        """Read in the excel file, using the cache _locators"""
        global _locators
        if locator in _locators:
            conversion_systems_worksheets, distribution_systems_worksheets, feedstocks_worksheets, energy_carriers_worksheet = _locators[locator]
        else:
            conversion_systems_worksheets = pd.read_excel(locator.get_database_conversion_systems(), sheet_name=None)
            distribution_systems_worksheets = pd.read_excel(locator.get_database_distribution_systems(), sheet_name=None)
            feedstocks_worksheets = pd.read_excel(locator.get_database_feedstocks(), sheet_name=None)
            energy_carriers_worksheet = pd.read_excel(locator.get_database_feedstocks(), sheet_name='ENERGY_CARRIERS')
            _locators[locator] = conversion_systems_worksheets, distribution_systems_worksheets, feedstocks_worksheets, energy_carriers_worksheet
        return conversion_systems_worksheets, distribution_systems_worksheets, feedstocks_worksheets, energy_carriers_worksheet

"""
This module provides an interface to the "supply_systems.xls" file (locator.get_database_supply_systems()) - the point
is to avoid reading this data (which is constant during the lifetime of a script) again and again.
"""




import pandas as pd
import os

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
        energy_carriers_worksheet = self.read_csv(locator)

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



    def read_csv(self, locator):
        """Read in the excel file, using the cache _locators"""
        global _locators
        if locator in _locators:
            conversion_systems_worksheets, distribution_systems_worksheets, feedstocks_worksheets, energy_carriers_worksheet = _locators[locator]
        else:
            conversion_systems_worksheets = {}
            conversion_names = get_csv_filenames(locator.get_db4_components_conversion_folder())
            for conversion_name in conversion_names:
                conversion_systems_worksheets[conversion_name] = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv(conversion_technology=conversion_name))

            distribution_systems_worksheets = {}
            distribution_names = get_csv_filenames(locator.get_db4_components_distribution_folder())
            for distribution_name in distribution_names:
                distribution_systems_worksheets[distribution_name] = pd.read_csv(locator.get_db4_components_distribution_distribution_csv(distribution=distribution_name))

            feedstocks_worksheets = {}
            feedstocks_names = get_csv_filenames(locator.get_db4_components_feedstocks_folder())
            feedstocks_names = [x for x in feedstocks_names if x != 'ENERGY_CARRIERS']
            for feedstocks_name in feedstocks_names:
                feedstocks_worksheets[feedstocks_name] = pd.read_csv(locator.get_db4_components_feedstocks_feedstocks_csv(feedstocks=feedstocks_name))

            energy_carriers_worksheet = {}
            energy_carriers_worksheet['ENERGY_CARRIERS'] = pd.read_csv(locator.get_db4_components_feedstocks_feedstocks_csv(feedstocks='ENERGY_CARRIERS'))

            _locators[locator] = conversion_systems_worksheets, distribution_systems_worksheets, feedstocks_worksheets, energy_carriers_worksheet
        return conversion_systems_worksheets, distribution_systems_worksheets, feedstocks_worksheets, energy_carriers_worksheet


def get_csv_filenames(directory):
    """
    Get all .csv file names (without extensions) under a given directory.

    Parameters:
    - directory (str): Path to the directory.

    Returns:
    - List[str]: List of CSV file names without extensions.
    """
    return [os.path.splitext(file)[0] for file in os.listdir(directory) if file.endswith('.csv')]

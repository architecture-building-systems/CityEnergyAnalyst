"""
Tests to make sure the schemas.yml file is structurally sound.
"""

import unittest

import cea.config
import cea.inputlocator
import cea.scripts

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class TestSchemas(unittest.TestCase):

    def test_all_locator_methods_described(self):
        schemas = cea.scripts.schemas()
        config = cea.config.Configuration()
        locator = cea.inputlocator.InputLocator(config.scenario)

        for method in self.extract_locator_methods(locator):
            self.assertIn(method, schemas.keys())

    def extract_locator_methods(self, locator):
        """Return the list of locator methods that point to files"""
        ignore = {
            "ensure_parent_folder_exists",
            "get_plant_nodes",
            "get_temporary_file",
            "get_weather_names",
            "get_zone_building_names",
            "verify_database_template",
            "get_optimization_network_all_individuals_results_file",  # TODO: remove this when we know how
            "get_optimization_network_generation_individuals_results_file",  # TODO: remove this when we know how
            "get_optimization_network_individual_results_file",  # TODO: remove this when we know how
            "get_optimization_network_layout_costs_file",  # TODO: remove this when we know how
            "get_predefined_hourly_setpoints",  # TODO: remove this when we know how
            "get_timeseries_plots_file",  # TODO: remove this when we know how
        }
        for m in dir(locator):
            if not callable(getattr(locator, m)):
                # normal attributes (fields) are not locator methods
                continue
            if m.startswith("_"):
                # these are private methods, ignore
                continue
            if m in ignore:
                # keep a list of special methods to ignore
                continue
            if m.endswith("_folder"):
                # not interested in folders
                continue
            yield m


if __name__ == '__main__':
    unittest.main()

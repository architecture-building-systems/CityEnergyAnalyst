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

        self.assertEqual(True, False)

    def extract_locator_methods(self, locator):
        """Return the list of locator methods that point to files"""
        ignore = {"scenario"}
        for m in dir(locator):
            if m.startswith("_"):
                continue
            if m in ignore:
                continue
            yield m

if __name__ == '__main__':
    unittest.main()

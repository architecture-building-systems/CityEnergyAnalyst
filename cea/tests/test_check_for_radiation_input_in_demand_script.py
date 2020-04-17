import os
import shutil
import tempfile
import unittest
import cea.config
import cea.inputlocator

class TestCheckForRadiationInputInDemandScript(unittest.TestCase):
    """
    Tests to make sure the demand script raises a `ValueError` if applied to a reference case that does not have
    the radiation script output.

    This fixes the issue #222
    """

    def test_demand_checks_radiation_daysim_script(self):
        import cea.demand.demand_main

        locator = cea.inputlocator.ReferenceCaseOpenLocator()
        building_name = locator.get_zone_building_names()[0]
        if os.path.exists(locator.get_radiation_metadata(building_name)):
            # scenario contains radiation.csv, remove it for test
            os.remove(locator.get_radiation_metadata(building_name))
        if os.path.exists(locator.get_radiation_building(building_name)):
            # scenario contains properties_surfaces.csv, remove it for test
            os.remove(locator.get_radiation_building(building_name))

        config = cea.config.Configuration(config_file=cea.config.DEFAULT_CONFIG)
        config.scenario = locator.scenario
        self.assertRaises(ValueError, cea.demand.demand_main.main, config=config)
        cea.inputlocator.ReferenceCaseOpenLocator.already_extracted = False

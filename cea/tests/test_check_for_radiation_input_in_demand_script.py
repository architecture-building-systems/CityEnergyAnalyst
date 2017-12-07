import os
import shutil
import tempfile
import unittest
import cea.config

class TestCheckForRadiationInputInDemandScript(unittest.TestCase):
    """
    Tests to make sure the demand script raises a `ValueError` if applied to a reference case that does not have
    the radiation script output.

    This fixes the issue #222
    """

    @classmethod
    def setUpClass(cls):
        """
        Create a copy of the ninecubes reference case in the temp folder. The ninecubes reference case is
        in the `../examples` folder as a zip file (`ninecubes.zip`) and has to be extracted first.
        """
        import zipfile
        import cea.examples
        import tempfile
        archive = zipfile.ZipFile(os.path.join(os.path.dirname(cea.examples.__file__), 'reference-case-open.zip'))
        archive.extractall(tempfile.gettempdir())
        cls.reference_case = os.path.join(tempfile.gettempdir(), 'reference-case-open', 'baseline')

    @classmethod
    def tearDownClass(cls):
        """delete the ninecubes stuff from the temp directory"""
        shutil.rmtree(os.path.join(tempfile.gettempdir(), 'reference-case-open'))

    def test_ninecubes_copied(self):
        """sanity check on `setUpClass`"""
        self.assertTrue(os.path.exists(os.path.join(tempfile.gettempdir(), 'reference-case-open')))

    def test_demand_checks_radiation_script(self):
        import cea.demand.demand_main
        import cea.globalvar

        locator = cea.inputlocator.InputLocator(os.path.join(tempfile.gettempdir(), 'reference-case-open'))
        if os.path.exists(locator.get_radiation()):
            # scenario contains radiation.csv, remove it for test
            os.remove(locator.get_radiation())
        if os.path.exists(locator.get_surface_properties()):
            # scenario contains properties_surfaces.csv, remove it for test
            os.remove(locator.get_surface_properties())
        gv = cea.globalvar.GlobalVariables()
        weather_path = locator.get_weather('Zug')

        from os.path import dirname as up
        two_up = up(up(__file__))
        DEFAULT_CONFIG = os.path.join(two_up, 'default.config')
        config = cea.config.Configuration(config_file=DEFAULT_CONFIG)
        self.assertRaises(ValueError, cea.demand.demand_main.demand_calculation, locator=locator,
                        gv=gv, config = config)

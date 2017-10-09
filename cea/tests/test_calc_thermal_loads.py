import ConfigParser
import os
import unittest
import json

import pandas as pd

from cea.demand.occupancy_model import schedule_maker
from cea.demand.thermal_loads import calc_thermal_loads, BuildingProperties
from cea.globalvar import GlobalVariables
from cea.inputlocator import InputLocator
from cea.utilities import epwreader


class TestCalcThermalLoads(unittest.TestCase):
    """
    This test case contains the two tests :py:meth`test_calc_thermal_loads` and
    :py:meth:`test_calc_thermal_loads_other_buildings`. They are not stricty unit tests, but rather test the whole
    thermal loads calculation (for the built-in reference case) against a set of known results, stored in the file
    ``test_calc_thermal_loads.config`` - if the results should change and the change has been verified, you can use
    the script ``create_unittest_data.py`` to update the config file with the new results.
    """

    @classmethod
    def setUpClass(cls):
        import zipfile
        import tempfile
        import cea.examples
        archive = zipfile.ZipFile(os.path.join(os.path.dirname(cea.examples.__file__), 'reference-case-open.zip'))
        archive.extractall(tempfile.gettempdir())
        reference_case = os.path.join(tempfile.gettempdir(), 'reference-case-open', 'baseline')
        cls.locator = InputLocator(reference_case)
        cls.gv = GlobalVariables()
        weather_path = cls.locator.get_default_weather()
        cls.weather_data = epwreader.epw_reader(weather_path)[
            ['drybulb_C', 'wetbulb_C', 'relhum_percent', 'windspd_ms', 'skytemp_C']]
        cls.config = ConfigParser.SafeConfigParser()
        cls.config.read(os.path.join(os.path.dirname(__file__), 'test_calc_thermal_loads.config'))

        # run properties script
        import cea.demand.preprocessing.properties
        cea.demand.preprocessing.properties.properties(cls.locator, True, True, True, True)

        cls.building_properties = BuildingProperties(cls.locator, cls.gv)
        cls.date = pd.date_range(cls.gv.date_start, periods=8760, freq='H')
        cls.list_uses = cls.building_properties.list_uses()
        cls.archetype_schedules, cls.archetype_values = schedule_maker(cls.date, cls.locator, cls.list_uses)
        cls.occupancy_densities = cls.archetype_values['people']
        cls.usage_schedules = {'list_uses': cls.list_uses, 'archetype_schedules': cls.archetype_schedules,
                               'occupancy_densities': cls.occupancy_densities, 'archetype_values': cls.archetype_values}

    def test_calc_thermal_loads(self):
        bpr = self.building_properties['B01']
        result = calc_thermal_loads('B01', bpr, self.weather_data,
                                    self.usage_schedules, self.date, self.gv, self.locator)
        self.assertIsNone(result)
        self.assertTrue(os.path.exists(self.locator.get_demand_results_file('B01')), 'Building csv not produced')
        self.assertTrue(os.path.exists(self.locator.get_temporary_file('B01T.csv')),
                        'Building temp file not produced')

        # test the building csv file (output of the `calc_thermal_loads` call above)
        df = pd.read_csv(self.locator.get_demand_results_file('B01'))


        value_columns = json.loads(self.config.get('test_calc_thermal_loads', 'value_columns'))
        values = json.loads(self.config.get('test_calc_thermal_loads', 'values'))

        for i, column in enumerate(value_columns):
            self.assertAlmostEqual(values[i], df[column].sum(), msg='Sum of column %s differs, %f != %f' % (
                column, values[i], df[column].sum()), places=3)


    def test_calc_thermal_loads_other_buildings(self):
        """Test some other buildings just to make sure we have the proper data"""
        # randomly selected except for B302006716, which has `Af == 0`

        buildings = json.loads(self.config.get('test_calc_thermal_loads_other_buildings', 'results'))
        for building in buildings.keys():
            bpr = self.building_properties[building]
            b, qcf_kwh, qhf_kwh = run_for_single_building(building, bpr, self.weather_data, self.usage_schedules,
                                                          self.date, self.gv, self.locator)
            b0 = buildings[b][0]
            b1 = buildings[b][1]
            self.assertAlmostEqual(b0, qcf_kwh,
                                   msg="qcf_kwh for %(b)s should be: %(qcf_kwh).5f, was %(b0).5f" % locals(),
                                   places=3)
            self.assertAlmostEqual(b1, qhf_kwh,
                                   msg="qhf_kwh for %(b)s should be: %(qhf_kwh).5f, was %(b1).5f" % locals(),
                                   places=3)


def run_for_single_building(building, bpr, weather_data, usage_schedules, date, gv, locator):
    calc_thermal_loads(building, bpr, weather_data, usage_schedules, date, gv, locator)
    df = pd.read_csv(locator.get_demand_results_file(building))
    return building, df['QCf_kWh'].sum(), df['QHf_kWh'].sum()


if __name__ == "__main__":
    unittest.main()

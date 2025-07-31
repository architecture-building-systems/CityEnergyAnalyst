


import configparser
import json
import os
import unittest

import pandas as pd

from cea.demand.occupancy_helper import occupancy_helper_main
from cea.demand.building_properties import BuildingProperties
from cea.demand.thermal_loads import calc_thermal_loads
from cea.utilities.date import get_date_range_hours_from_year
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
        import cea.examples
        cls.locator = cea.inputlocator.ReferenceCaseOpenLocator()
        cls.config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        cls.config.scenario = cls.locator.scenario
        weather_path = cls.locator.get_weather('Zug_inducity_2009')
        cls.weather_data = epwreader.epw_reader(weather_path)[
            ['year', 'drybulb_C', 'wetbulb_C', 'relhum_percent', 'windspd_ms', 'skytemp_C']]
        year = cls.weather_data['year'][0]
        cls.date_range = get_date_range_hours_from_year(year)
        cls.test_config = configparser.ConfigParser()
        cls.test_config.read(os.path.join(os.path.dirname(__file__), 'test_calc_thermal_loads.config'))

        # reinit database to ensure updated databases are loaded
        from cea.datamanagement.database_helper import main as database_helper
        cls.config.database_helper.databases_path = "CH"
        cls.config.database_helper.databases = ["archetypes", "assemblies", "components"]
        database_helper(cls.config)

        # run properties script
        import cea.datamanagement.archetypes_mapper
        cea.datamanagement.archetypes_mapper.archetypes_mapper(cls.locator, True, True, True, True, True, True,
                                                         cls.locator.get_zone_building_names())

        cls.building_properties = BuildingProperties(cls.locator, epwreader.epw_reader(cls.locator.get_weather_file()))

        cls.use_dynamic_infiltration_calculation = cls.config.demand.use_dynamic_infiltration_calculation
        cls.resolution_output = cls.config.demand.resolution_output
        cls.loads_output = cls.config.demand.loads_output
        cls.massflows_output = cls.config.demand.massflows_output
        cls.temperatures_output = cls.config.demand.temperatures_output
        cls.debug = cls.config.debug

    def test_calc_thermal_loads(self):
        bpr = self.building_properties['B1011']
        self.config.general.multiprocessing = False
        self.config.occupancy_helper.occupancy_model = "deterministic"
        occupancy_helper_main(self.locator, self.config, building='B1011')

        result = calc_thermal_loads('B1011', bpr, self.weather_data, self.date_range, self.locator,
                                    self.use_dynamic_infiltration_calculation, self.resolution_output,
                                    self.loads_output, self.massflows_output, self.temperatures_output,
                                    self.config, self.debug)
        self.assertIsNone(result)
        self.assertTrue(os.path.exists(self.locator.get_demand_results_file('B1011')),
                        'Building csv not produced')
        self.assertTrue(os.path.exists(self.locator.get_temporary_file('B1011T.csv')),
                        'Building temp file not produced')

        # test the building csv file (output of the `calc_thermal_loads` call above)
        df = pd.read_csv(self.locator.get_demand_results_file('B1011'))

        value_columns = json.loads(self.test_config.get('test_calc_thermal_loads', 'value_columns'))
        values = json.loads(self.test_config.get('test_calc_thermal_loads', 'values'))

        for i, column in enumerate(value_columns):
            self.assertAlmostEqual(values[i], df[column].sum(), msg='Sum of column %s differs, %f != %f' % (
                column, values[i], df[column].sum()), places=3)

    def test_calc_thermal_loads_other_buildings(self):
        """Test some other buildings just to make sure we have the proper data"""
        # randomly selected except for B302006716, which has `Af == 0`

        buildings = json.loads(self.test_config.get('test_calc_thermal_loads_other_buildings', 'results'))
        for building in buildings.keys():
            bpr = self.building_properties[building]
            b, qhs_sys_kwh, qcs_sys_kwh, qww_sys_kwh = run_for_single_building(building, bpr, self.weather_data,
                                                                               self.date_range, self.locator,
                                                                               self.use_dynamic_infiltration_calculation,
                                                                               self.resolution_output,
                                                                               self.loads_output,
                                                                               self.massflows_output,
                                                                               self.temperatures_output,
                                                                               self.config, self.debug)
            expected_qhs_sys_kwh = buildings[b][0]
            expected_qcs_sys_kwh = buildings[b][1]
            expected_qww_sys_kwh = buildings[b][2]
            print("qhs_sys_kwh for %s: %f, expected: %f" % (b, qhs_sys_kwh, expected_qhs_sys_kwh))
            self.assertAlmostEqual(expected_qhs_sys_kwh, qhs_sys_kwh,
                                   msg="qhs_sys_kwh for %(b)s should be: %(qhs_sys_kwh).5f, was %(expected_qhs_sys_kwh).5f" % locals(),
                                   places=3)
            self.assertAlmostEqual(expected_qcs_sys_kwh, qcs_sys_kwh,
                                   msg="qcs_sys_kwh for %(b)s should be: %(qcs_sys_kwh).5f, was %(expected_qcs_sys_kwh).5f" % locals(),
                                   places=3)
            self.assertAlmostEqual(expected_qww_sys_kwh, qww_sys_kwh,
                                   msg="qww_sys_kwh for %(b)s should be: %(qww_sys_kwh).5f, was %(expected_qww_sys_kwh).5f" % locals(),
                                   places=3)


def run_for_single_building(building, bpr, weather_data, date, locator,
                            use_dynamic_infiltration_calculation, resolution_output, loads_output,
                            massflows_output, temperatures_output, config, debug):

    config.general.multiprocessing = False
    occupancy_helper_main(locator, config, building=building)
    calc_thermal_loads(building, bpr, weather_data, date, locator,
                       use_dynamic_infiltration_calculation, resolution_output, loads_output,
                       massflows_output, temperatures_output, config, debug)
    df = pd.read_csv(locator.get_demand_results_file(building))
    return building, float(df['Qhs_sys_kWh'].sum()), df['Qcs_sys_kWh'].sum(), float(df['Qww_sys_kWh'].sum())


if __name__ == "__main__":
    unittest.main()

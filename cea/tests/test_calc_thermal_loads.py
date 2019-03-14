import ConfigParser
import os
import unittest
import json

import pandas as pd

import cea.config
import cea.inputlocator
from cea.demand.demand_main import properties_and_schedule
from cea.demand.thermal_loads import calc_thermal_loads
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
        cls.locator = cea.inputlocator.ReferenceCaseOpenLocator()
        cls.config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        weather_path = cls.locator.get_weather('Zug')
        cls.weather_data = epwreader.epw_reader(weather_path)[
            ['year', 'drybulb_C', 'wetbulb_C', 'relhum_percent', 'windspd_ms', 'skytemp_C']]
        year = cls.weather_data['year'][0]
        cls.region = cls.config.region
        cls.test_config = ConfigParser.SafeConfigParser()
        cls.test_config.read(os.path.join(os.path.dirname(__file__), 'test_calc_thermal_loads.config'))

        # run properties script
        import cea.datamanagement.data_helper
        cea.datamanagement.data_helper.data_helper(cls.locator, cls.config, True, True, True, True, True, True)

        use_daysim_radiation = cls.config.demand.use_daysim_radiation
        cls.building_properties, cls.usage_schedules, cls.date = properties_and_schedule(cls.locator, cls.region,
                                                                                         year, use_daysim_radiation)

        cls.use_dynamic_infiltration_calculation = cls.config.demand.use_dynamic_infiltration_calculation
        cls.use_stochastic_occupancy = cls.config.demand.use_stochastic_occupancy
        cls.resolution_output = cls.config.demand.resolution_output
        cls.loads_output = cls.config.demand.loads_output
        cls.massflows_output = cls.config.demand.massflows_output
        cls.temperatures_output = cls.config.demand.temperatures_output
        cls.format_output = cls.config.demand.format_output
        cls.write_detailed_output = cls.config.demand.write_detailed_output
        cls.debug = cls.config.debug

    def test_calc_thermal_loads(self):
        bpr = self.building_properties['B01']
        result = calc_thermal_loads('B01', bpr, self.weather_data, self.usage_schedules, self.date, self.locator, self.use_stochastic_occupancy,
                                    self.use_dynamic_infiltration_calculation, self.resolution_output,
                                    self.loads_output, self.massflows_output, self.temperatures_output,
                                    self.format_output, self.config, self.region, self.write_detailed_output, self.config)
        self.assertIsNone(result)
        self.assertTrue(os.path.exists(self.locator.get_demand_results_file('B01',self.format_output)), 'Building csv not produced')
        self.assertTrue(os.path.exists(self.locator.get_temporary_file('B01T.csv')),
                        'Building temp file not produced')

        # test the building csv file (output of the `calc_thermal_loads` call above)
        df = pd.read_csv(self.locator.get_demand_results_file('B01', self.format_output))

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
                                                                               self.usage_schedules,
                                                                               self.date, self.locator,
                                                                               self.use_stochastic_occupancy,
                                                                               self.use_dynamic_infiltration_calculation,
                                                                               self.resolution_output, self.loads_output,
                                                                               self.massflows_output,
                                                                               self.temperatures_output,
                                                                               self.format_output, self.config,
                                                                               self.region,
                                                                               self.write_detailed_output, self.debug)
            expected_qhs_sys_kwh = buildings[b][0]
            expected_qcs_sys_kwh = buildings[b][1]
            expected_qww_sys_kwh = buildings[b][2]
            self.assertAlmostEqual(expected_qhs_sys_kwh, qhs_sys_kwh,
                                   msg="qhs_sys_kwh for %(b)s should be: %(qhs_sys_kwh).5f, was %(expected_qhs_sys_kwh).5f" % locals(),
                                   places=3)
            self.assertAlmostEqual(expected_qcs_sys_kwh, qcs_sys_kwh,
                                   msg="qcs_sys_kwh for %(b)s should be: %(qcs_sys_kwh).5f, was %(expected_qcs_sys_kwh).5f" % locals(),
                                   places=3)
            self.assertAlmostEqual(expected_qww_sys_kwh, qww_sys_kwh,
                                   msg="qww_sys_kwh for %(b)s should be: %(qww_sys_kwh).5f, was %(expected_qww_sys_kwh).5f" % locals(),
                                   places=3)


def run_for_single_building(building, bpr, weather_data, usage_schedules, date, locator, use_stochastic_occupancy,
                            use_dynamic_infiltration_calculation, resolution_output, loads_output,
                            massflows_output, temperatures_output, format_output, config, region, write_detailed_output, debug):
    calc_thermal_loads(building, bpr, weather_data, usage_schedules, date, locator, use_stochastic_occupancy,
                       use_dynamic_infiltration_calculation, resolution_output, loads_output,
                       massflows_output, temperatures_output, format_output, config, region, write_detailed_output, debug)
    df = pd.read_csv(locator.get_demand_results_file(building, format_output))
    return building, float(df['Qhs_sys_kWh'].sum()), df['Qcs_sys_kWh'].sum(), float(df['Qww_sys_kWh'].sum())


if __name__ == "__main__":
    unittest.main()

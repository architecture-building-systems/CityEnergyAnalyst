import os
from unittest import TestCase

from cea import epwreader
from cea.demand import BuildingProperties
from cea.thermal_loads import calc_thermal_loads_new_ventilation
from cea.inputlocator import InputLocator
from cea.globalvar import GlobalVariables
from cea.maker import schedule_maker

import pandas as pd


class TestCalcThermalLoadsNewVentilation(TestCase):
    def setUp(self):
        self.locator = InputLocator(r'C:\reference-case\baseline')
        self.gv = GlobalVariables()

        weather_path = self.locator.get_default_weather()
        self.weather_data = epwreader.epw_reader(weather_path)[['drybulb_C', 'relhum_percent', 'windspd_ms']]

        self.building_properties = BuildingProperties(self.locator, self.gv)
        self.date = pd.date_range(self.gv.date_start, periods=8760, freq='H')
        self.list_uses = self.building_properties.list_uses()
        self.schedules = schedule_maker(self.date, self.locator, self.list_uses)
        self.usage_schedules = {'list_uses': self.list_uses,
                                'schedules': self.schedules}

    def test_calc_thermal_loads_new_ventilation(self):
        # FIXME: the usage_schedules bit needs to be fixed!!
        result = calc_thermal_loads_new_ventilation('B140577', self.building_properties, self.weather_data,
                                                    self.usage_schedules, self.date, self.gv,
                                                    self.locator.get_temporary_folder(),
                                                    self.locator.get_temporary_folder())
        self.assertIsNone(result)
        self.assertTrue(os.path.exists(self.locator.get_temporary_file('B140577.csv')), 'Building csv not produced')
        self.assertTrue(os.path.exists(self.locator.get_temporary_file('B140577T.csv')),
                        'Building temp file not produced')

        # test the building csv file
        df = pd.read_csv(self.locator.get_temporary_file('B140577.csv'))

        #
        expected_columns = [u'DATE', u'Ealf_kWh', u'Eauxf_kWh', u'Edataf_kWh', u'Ef_kWh', u'Epro_kWh', u'Name',
                            u'QCf_kWh', u'QHf_kWh', u'Qcdataf_kWh', u'Qcref_kWh', u'Qcs_kWh', u'Qcsf_kWh', u'Qhs_kWh',
                            u'Qhsf_kWh', u'Qww_kWh', u'Qww_tankloss_kWh', u'Qwwf_kWh', u'Trcs_C', u'Trhs_C', u'Trww_C',
                            u'Tscs_C', u'Tshs_C', u'Tsww_C', u'Tww_tank_C', u'Vw_m3', u'mcpcs_kWC', u'mcphs_kWC',
                            u'mcpww_kWC', u'occ_pax']
        self.assertEqual(set(expected_columns), set(df.columns), 'Column list of building csv does not match')
        self.assertEqual(df.shape[0], 8760, 'Expected one row per hour in the year')

        value_columns = [u'Ealf_kWh', u'Eauxf_kWh', u'Edataf_kWh', u'Ef_kWh', u'Epro_kWh', u'QCf_kWh', u'QHf_kWh',
                         u'Qcdataf_kWh', u'Qcref_kWh', u'Qcs_kWh', u'Qcsf_kWh', u'Qhs_kWh', u'Qhsf_kWh', u'Qww_kWh',
                         u'Qww_tankloss_kWh', u'Qwwf_kWh', u'Trcs_C', u'Trhs_C', u'Trww_C', u'Tscs_C', u'Tshs_C',
                         u'Tsww_C', u'Tww_tank_C', u'Vw_m3', u'mcpcs_kWC', u'mcphs_kWC', u'mcpww_kWC', u'occ_pax']
        values = [2335522.029999916, 51283.209999999264, 0.0, 2386803.5299999011, 0.0, 1600579.3699999989,
                  10583959.84999999, 0.0, 0.0, 969342.64000000141, 1600579.3699999989, 917820.5499999997,
                  1598211.1199999996, 8964857.8500000071, 9976.2799999999643, 8985748.6999999825, 16116, 52842, 99500.0,
                  11376, 63853, 525600, 525426.29999996931, 476000.19000000018, 319634, 148190, 184502.95000000024,
                  6827181.0]
        for i, column in enumerate(value_columns):
            self.assertAlmostEqual(values[i], df[column].sum(), 'Sum of column %s differs' % column)

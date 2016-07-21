import os
import unittest

import pandas as pd

from cea.demand.occupancy_model import schedule_maker
from cea.demand.thermal_loads import calc_thermal_loads_new_ventilation, BuildingProperties
from cea.globalvar import GlobalVariables
from cea.inputlocator import InputLocator
from cea.utils import epwreader


class TestCalcThermalLoadsNewVentilation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.locator = InputLocator(r'C:\reference-case\baseline')
        cls.gv = GlobalVariables()

        weather_path = cls.locator.get_default_weather()
        cls.weather_data = epwreader.epw_reader(weather_path)[['drybulb_C', 'relhum_percent', 'windspd_ms']]

        cls.building_properties = BuildingProperties(cls.locator, cls.gv)
        cls.date = pd.date_range(cls.gv.date_start, periods=8760, freq='H')
        cls.list_uses = cls.building_properties.list_uses()
        cls.schedules = schedule_maker(cls.date, cls.locator, cls.list_uses)
        cls.usage_schedules = {'list_uses': cls.list_uses,
                                'schedules': cls.schedules}

    def test_calc_thermal_loads_new_ventilation(self):
        # FIXME: the usage_schedules bit needs to be fixed!!
        bpr = self.building_properties['B140577']
        result = calc_thermal_loads_new_ventilation('B140577', bpr, self.weather_data,
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
            try:
                self.assertAlmostEqual(values[i], df[column].sum(), msg='Sum of column %s differs' % column)
            except:
                raise

    def test_calc_thermal_loads_other_buildings(self):
        """Test some other buildings just to make sure we have the proper data"""
        import multiprocessing as mp
        pool = mp.Pool()
        # randomly selected except for B302006716, which has `Af == 0`
        buildings = {'B140571': (87082.27, 173418.77),
                     'B140557': (67011.74, 141896.5),
                     'B140577': (1600579.37, 10583959.85),
                     'B302040335': (1525.49, 8443.68),
                     'B2372467': (33608.18, 76675.11),
                     'B302006716': (0.0, 0.0)}
        if self.gv.multiprocessing:
            joblist = []
            for building in buildings.keys():
                bpr = self.building_properties[building]
                job = pool.apply_async(run_for_single_building,
                                       [building, bpr, self.weather_data, self.usage_schedules, self.date, self.gv,
                                        self.locator.get_temporary_folder(),
                                        self.locator.get_temporary_file('%s.csv' % building)])
                joblist.append(job)
            for job in joblist:
                b, qcf_kwh, qhf_kwh = job.get(20)
                self.assertAlmostEqual(buildings[b][0], qcf_kwh)
                self.assertAlmostEqual(buildings[b][1], qhf_kwh)
        else:
            for building in buildings.keys():
                bpr = self.building_properties[building]
                b, qcf_kwh, qhf_kwh = run_for_single_building(building, bpr, self.weather_data, self.usage_schedules,
                                                              self.date, self.gv,
                                                              self.locator.get_temporary_folder(),
                                                              self.locator.get_temporary_file('%s.csv' % building))
                self.assertAlmostEqual(buildings[b][0], qcf_kwh)
                self.assertAlmostEqual(buildings[b][1], qhf_kwh)


def run_for_single_building(building, bpr, weather_data, usage_schedules, date, gv, temporary_folder, temporary_file):
    calc_thermal_loads_new_ventilation(building, bpr, weather_data,
                                       usage_schedules, date, gv,
                                       temporary_folder,
                                       temporary_folder)
    df = pd.read_csv(temporary_file)
    return building, df['QCf_kWh'].sum(), df['QHf_kWh'].sum()

if __name__ == "__main__":
    unittest.main()



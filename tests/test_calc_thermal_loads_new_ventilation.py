import os
import unittest

import pandas as pd

from cea.demand.occupancy_model import schedule_maker
from cea.demand.thermal_loads import calc_thermal_loads, BuildingProperties
from cea.globalvar import GlobalVariables
from cea.inputlocator import InputLocator
from cea.utilities import epwreader


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
        result = calc_thermal_loads('B140577', bpr, self.weather_data,
                                                    self.usage_schedules, self.date, self.gv,
                                                    self.locator.get_temporary_folder(),
                                                    self.locator.get_temporary_folder())
        self.assertIsNone(result)
        self.assertTrue(os.path.exists(self.locator.get_temporary_file('B140577.csv')), 'Building csv not produced')
        self.assertTrue(os.path.exists(self.locator.get_temporary_file('B140577T.csv')),
                        'Building temp file not produced')

        # test the building csv file
        df = pd.read_csv(self.locator.get_temporary_file('B140577.csv'))

        expected_columns = expected_columns = ['DATE', 'Ealf_kWh', 'Eauxf_kWh', 'Ecaf_kWh', 'Edataf_kWh', 'Ef_kWh',
                                               'Epro_kWh', 'Name', 'QCf_kWh', 'QHf_kWh', 'Qcdataf_kWh', 'Qcref_kWh',
                                               'Qcs_kWh', 'Qcsf_kWh', 'Qhprof_kWh', 'Qhs_kWh', 'Qhsf_kWh', 'Qww_kWh',
                                               'Qww_tankloss_kWh', 'Qwwf_kWh', 'Trcs_C', 'Trdata_C', 'Trhs_C',
                                               'Trref_C', 'Trww_C', 'Tscs_C', 'Tsdata_C', 'Tshs_C', 'Tsref_C', 'Tsww_C',
                                               'Tww_tank_C', 'Vw_m3', 'Vww_m3', 'mcpcs_kWC', 'mcpdata_kWC', 'mcphs_kWC',
                                               'mcpref_kWC', 'mcpww_kWC', 'occ_pax']
        self.assertEqual(set(expected_columns), set(df.columns),
                         'Column list of building csv does not match: ' + str(
                             set(expected_columns).symmetric_difference(set(df.columns))))
        self.assertEqual(df.shape[0], 8760, 'Expected one row per hour in the year')

        value_columns = [u'Ealf_kWh', u'Eauxf_kWh', u'Edataf_kWh', u'Ef_kWh', u'Epro_kWh', u'QCf_kWh', u'QHf_kWh',
                         u'Qcdataf_kWh', u'Qcref_kWh', u'Qcs_kWh', u'Qcsf_kWh', u'Qhs_kWh', u'Qhsf_kWh', u'Qww_kWh',
                         u'Qww_tankloss_kWh', u'Qwwf_kWh', u'Trcs_C', u'Trhs_C', u'Trww_C', u'Tscs_C', u'Tshs_C',
                         u'Tsww_C', u'Tww_tank_C', u'Vw_m3', u'mcpcs_kWC', u'mcphs_kWC', u'mcpww_kWC', u'occ_pax']
        values = [1922835.4550000001, 15731.976999999997, 0.0, 1938567.872, 0.0, 702758.23200000008, 1701735.5929999999,
                  0.0, 0.0, 443536.64399999997, 702758.23200000008, 551522.93500000006, 1230763.581, 461305.10200000001,
                  1742.3009999999999, 470971.99499999994, 7308, 48833, 99496.0, 5158, 57313, 525600, 524374.49099999992,
                  16328.606, 140551.42799999999, 155476.35000000003, 9676.5699999999997, 4897049.0]
        for i, column in enumerate(value_columns):
            try:
                self.assertAlmostEqual(values[i], df[column].sum(), msg='Sum of column %s differs' % column, places=3)
            except:
                raise

    def test_calc_thermal_loads_other_buildings(self):
        """Test some other buildings just to make sure we have the proper data"""
        import multiprocessing as mp
        pool = mp.Pool()
        # randomly selected except for B302006716, which has `Af == 0`
        buildings = {'B302006716': (0.00000, 0.00000),
                     'B140557': (34021.10900, 102784.97300),
                     'B140577': (702758.23200, 1701735.59300),
                     'B2372467': (19642.20900, 52134.43700),
                     'B302040335': (1011.03300, 4258.15800),
                     'B140571': (45059.22600, 122634.75000),}
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
                self.assertAlmostEqual(buildings[b][0], qcf_kwh,
                                       msg="qcf_kwh for %(b)s should be: %(qcf_kwh).5f" % locals(), places=3)
                self.assertAlmostEqual(buildings[b][1], qhf_kwh,
                                       msg="qhf_kwh for %(b)s should be: %(qhf_kwh).5f" % locals(), places=3)
        else:
            for building in buildings.keys():
                bpr = self.building_properties[building]
                b, qcf_kwh, qhf_kwh = run_for_single_building(building, bpr, self.weather_data, self.usage_schedules,
                                                              self.date, self.gv,
                                                              self.locator.get_temporary_folder(),
                                                              self.locator.get_temporary_file('%s.csv' % building))
                self.assertAlmostEqual(buildings[b][0], qcf_kwh,
                                       msg="qcf_kwh for %(b)s should be: %(qcf_kwh).5f" % locals(), places=3)
                self.assertAlmostEqual(buildings[b][1], qhf_kwh,
                                       msg="qhf_kwh for %(b)s should be: %(qhf_kwh).5f" % locals(), places=3)


def run_for_single_building(building, bpr, weather_data, usage_schedules, date, gv, temporary_folder, temporary_file):
    calc_thermal_loads(building, bpr, weather_data,
                                       usage_schedules, date, gv,
                                       temporary_folder,
                                       temporary_folder)
    df = pd.read_csv(temporary_file)
    return building, df['QCf_kWh'].sum(), df['QHf_kWh'].sum()

if __name__ == "__main__":
    unittest.main()



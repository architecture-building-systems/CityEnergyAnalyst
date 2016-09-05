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
                                                    self.usage_schedules, self.date, self.gv, self.locator)
        self.assertIsNone(result)
        self.assertTrue(os.path.exists(self.locator.get_demand_results_file('B140577')), 'Building csv not produced')
        self.assertTrue(os.path.exists(self.locator.get_temporary_file('B140577T.csv')),
                        'Building temp file not produced')

        # test the building csv file
        df = pd.read_csv(self.locator.get_demand_results_file('B140577'))

        expected_columns = self.gv.demand_building_csv_columns
        self.assertEqual(set(expected_columns), set(df.columns),
                         'Column list of building csv does not match: ' + str(
                             set(expected_columns).symmetric_difference(set(df.columns))))
        self.assertEqual(df.shape[0], 8760, 'Expected one row per hour in the year')

        value_columns = [u'Ealf_kWh', u'Eauxf_kWh', u'Edataf_kWh', u'Ef_kWh', u'QCf_kWh', u'QHf_kWh',
                         u'Qcdataf_kWh', u'Qcref_kWh', u'Qcs_kWh', u'Qcsf_kWh', u'Qhs_kWh', u'Qhsf_kWh', u'Qww_kWh',
                         u'Qwwf_kWh', u'Trcs_C', u'Trhs_C', u'Trww_C', u'Tscs_C', u'Tshs_C',
                         u'Tsww_C', u'Vw_m3', u'mcpcs_kWC', u'mcphs_kWC', u'mcpww_kWC', u'occ_pax']
        values = [1922835.4550000001, 15731.608999999999, 0.0, 1938567.5050000001, 702758.23200000008,
                  1697665.7930000001, 0.0, 0.0, 443536.64399999997, 702758.23200000008, 550670.00699999998, 1226702.186,
                  461305.10200000001, 470963.58999999991, 7308, 48631, 99496.0, 5158, 57083, 525600, 16328.606,
                  140551.42799999999, 154749.82500000001, 9676.4099999999999, 4897049.0]
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
                     'B140557': (34021.10900, 102499.92500),
                     'B140577': (702758.23200, 1697665.79300),
                     'B2372467': (19642.20900, 52082.64500),
                     'B302040335': (1011.03300, 4257.88100),
                     'B140571': (45059.22600, 122441.17700),}
        if self.gv.multiprocessing:
            joblist = []
            for building in buildings.keys():
                bpr = self.building_properties[building]
                job = pool.apply_async(run_for_single_building,
                                       [building, bpr, self.weather_data, self.usage_schedules, self.date, self.gv,
                                        self.locator])
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
                                                              self.date, self.gv, self.locator)
                self.assertAlmostEqual(buildings[b][0], qcf_kwh,
                                       msg="qcf_kwh for %(b)s should be: %(qcf_kwh).5f" % locals(), places=3)
                self.assertAlmostEqual(buildings[b][1], qhf_kwh,
                                       msg="qhf_kwh for %(b)s should be: %(qhf_kwh).5f" % locals(), places=3)


def run_for_single_building(building, bpr, weather_data, usage_schedules, date, gv, locator):
    calc_thermal_loads(building, bpr, weather_data, usage_schedules, date, gv, locator)
    df = pd.read_csv(locator.get_demand_results_file(building))
    return building, df['QCf_kWh'].sum(), df['QHf_kWh'].sum()

if __name__ == "__main__":
    unittest.main()



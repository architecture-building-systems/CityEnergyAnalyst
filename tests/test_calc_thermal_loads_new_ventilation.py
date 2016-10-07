import os
import unittest

import pandas as pd

from cea.demand.occupancy_model import schedule_maker
from cea.demand.thermal_loads import calc_thermal_loads, BuildingProperties
from cea.globalvar import GlobalVariables
from cea.inputlocator import InputLocator
from cea.utilities import epwreader

REFERENCE_CASE = r'C:\reference-case\baseline'


class TestCalcThermalLoadsNewVentilation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.locator = InputLocator(REFERENCE_CASE)
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
        values = [1922835.4550000001, 31467.024000000001, 0.0, 1954302.8670000001, 630724.96699999995,
                  1198505.6850000001, 0.0, 0.0, 475514.23900000006, 630724.96699999995, 550669.00800000003,
                  727555.96100000001, 461305.10200000001, 470949.73299999995, 15006, 42106, 99496.0, 10586, 47946,
                  525600, 16328.606, 126144.56199999999, 132545.64000000001, 9676.1020000000008, 4897049.0]
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
                     'B140557': (29135.67200, 73340.08100),
                     'B140577': (630724.96700, 1198505.68500),
                     'B2372467': (17589.66500, 39710.08500),
                     'B302040335': (816.02400, 3339.33600),
                     'B140571': (39940.50300, 89749.36800), }
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
                b0 = buildings[b][0]
                b1 = buildings[b][1]
                self.assertAlmostEqual(b0, qcf_kwh,
                                       msg="qcf_kwh for %(b)s should be: %(qcf_kwh).5f, was %(b0).5f" % locals(),
                                       places=3)
                self.assertAlmostEqual(b1, qhf_kwh,
                                       msg="qhf_kwh for %(b)s should be: %(qhf_kwh).5f, was %(b1).5f" % locals(),
                                       places=3)
        else:
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

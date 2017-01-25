import os
import unittest

import pandas as pd

from cea.demand.occupancy_model import schedule_maker
from cea.demand.thermal_loads import calc_thermal_loads, BuildingProperties
from cea.globalvar import GlobalVariables
from cea.inputlocator import InputLocator
from cea.utilities import epwreader

REFERENCE_CASE = r'C:\reference-case-open\baseline'


class TestCalcThermalLoads(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if 'REFERENCE_CASE' in os.environ:
            cls.locator = InputLocator(os.environ['REFERENCE_CASE'])
        else:
            cls.locator = InputLocator(REFERENCE_CASE)
        cls.gv = GlobalVariables()

        weather_path = cls.locator.get_default_weather()
        cls.weather_data = epwreader.epw_reader(weather_path)[['drybulb_C', 'relhum_percent', 'windspd_ms', 'skytemp_C']]

        cls.building_properties = BuildingProperties(cls.locator, cls.gv)
        cls.date = pd.date_range(cls.gv.date_start, periods=8760, freq='H')
        cls.list_uses = cls.building_properties.list_uses()
        cls.schedules = schedule_maker(cls.date, cls.locator, cls.list_uses)
        cls.usage_schedules = {'list_uses': cls.list_uses,
                               'schedules': cls.schedules}

    def test_calc_thermal_loads(self):
        # FIXME: the usage_schedules bit needs to be fixed!!
        bpr = self.building_properties['B01']
        result = calc_thermal_loads('B01', bpr, self.weather_data,
                                    self.usage_schedules, self.date, self.gv, self.locator)
        self.assertIsNone(result)
        self.assertTrue(os.path.exists(self.locator.get_demand_results_file('B01')), 'Building csv not produced')
        self.assertTrue(os.path.exists(self.locator.get_temporary_file('B01T.csv')),
                        'Building temp file not produced')

        # test the building csv file
        df = pd.read_csv(self.locator.get_demand_results_file('B01'))
        #
        # expected_columns = self.gv.demand_building_csv_columns
        # print expected_columns
        # set(expected_columns)
        # self.assertEqual(set(expected_columns), set(df.columns),
        #                  'Column list of building csv does not match: ' + str(
        #                      set(expected_columns).symmetric_difference(set(df.columns))))
        # self.assertEqual(df.shape[0], 8760, 'Expected one row per hour in the year')

        value_columns = [u'Ealf_kWh', u'Eauxf_kWh', u'Edataf_kWh', u'Ef_kWh', u'QCf_kWh', u'QHf_kWh',
                         u'Qcdataf_kWh', u'Qcref_kWh', u'Qcs_kWh', u'Qcsf_kWh', u'Qhs_kWh', u'Qhsf_kWh', u'Qww_kWh',
                         u'Qwwf_kWh', u'Tcsf_re_C', u'Thsf_re_C', u'Twwf_re_C', u'Tcsf_sup_C', u'Thsf_sup_C',
                         u'Twwf_sup_C']
        values = [155102.61600000001, 1030.7850000000001, 0.0, 156133.40099999998, 33986.971000000005,
                  148714.23499999999, 0, 0, 32163.004999999997, 33986.971000000005, 102867.459, 108846.057,
                  37198.886999999995, 39868.184999999998, 3230.0, 44968.809999999998, 99496.0, 2280.0, 51691.519,
                  525600]
        for i, column in enumerate(value_columns):
            try:
                self.assertAlmostEqual(values[i], df[column].sum(), msg='Sum of column %s differs, %f != %f' % (
                    column, values[i], df[column].sum()), places=3)
            except:
                print 'values:', [df[column].sum() for column in value_columns]  # make it easier to update changes
                raise

    def test_calc_thermal_loads_other_buildings(self):
        """Test some other buildings just to make sure we have the proper data"""
        # randomly selected except for B302006716, which has `Af == 0`
        buildings = {'B01': (33986.97100, 148714.23500),
                     'B03': (33999.27700, 148764.56500),
                     'B02': (34425.99600, 148859.40300),
                     'B05': (35039.29500, 149073.43000),
                     'B04': (34486.24100, 148848.03700),
                     'B07': (33881.14000, 148737.39100),
                     'B06': (0.00000, 0.00000),
                     'B09': (35283.86100, 149082.61900),
                     'B08': (37307.33200, 149185.62700), }
        if self.gv.multiprocessing:
            import multiprocessing as mp
            pool = mp.Pool()
            joblist = []
            for building in buildings.keys():
                bpr = self.building_properties[building]
                job = pool.apply_async(run_for_single_building,
                                       [building, bpr, self.weather_data, self.usage_schedules, self.date, self.gv,
                                        self.locator])
                joblist.append(job)
            for job in joblist:
                b, qcf_kwh, qhf_kwh = job.get(120)
                b0 = buildings[b][0]
                b1 = buildings[b][1]
                self.assertAlmostEqual(b0, qcf_kwh,
                                       msg="qcf_kwh for %(b)s should be: %(qcf_kwh).5f, was %(b0).5f" % locals(),
                                       places=3)
                self.assertAlmostEqual(b1, qhf_kwh,
                                       msg="qhf_kwh for %(b)s should be: %(qhf_kwh).5f, was %(b1).5f" % locals(),
                                       places=3)
            pool.close()
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

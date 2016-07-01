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
    def test_calc_thermal_loads_new_ventilation(self):

        locator = InputLocator(r'C:\reference-case\baseline')
        gv = GlobalVariables()
        building_properties = BuildingProperties(locator, gv)

        weather_path = locator.get_default_weather()
        weather_data = epwreader.epw_reader(weather_path)[['drybulb_C', 'relhum_percent', 'windspd_ms']]

        list_uses = list(building_properties._prop_occupancy.drop('PFloor', axis=1).columns)

        # FIXME: the usage_schedules bit needs to be fixed!!
        date = pd.date_range(gv.date_start, periods=8760, freq='H')
        schedules = schedule_maker(date, locator, list_uses)
        usage_schedules = {'list_uses': list_uses,
                           'schedules': schedules}

        result = calc_thermal_loads_new_ventilation('B140577', building_properties, weather_data, usage_schedules, date,
                                                    gv, locator.get_temporary_folder(),
                                                    locator.get_temporary_folder())
        self.assertIsNone(result)
        self.assertTrue(os.path.exists(locator.get_temporary_file('B140577.csv')), 'Building csv not produced')
        self.assertTrue(os.path.exists(locator.get_temporary_file('B140577T.csv')), 'Building temp file not produced')

        # test the building csv file
        df = pd.read_csv(locator.get_temporary_file('B140577.csv'))

        #
        expected_columns = [u'DATE', u'Ealf_kWh', u'Eauxf_kWh', u'Edataf_kWh', u'Ef_kWh', u'Epro_kWh', u'Name',
                            u'QCf_kWh', u'QHf_kWh', u'Qcdataf_kWh', u'Qcref_kWh', u'Qcs_kWh', u'Qcsf_kWh', u'Qhs_kWh',
                            u'Qhsf_kWh', u'Qww_kWh', u'Qww_tankloss_kWh', u'Qwwf_kWh', u'Trcs_C', u'Trhs_C', u'Trww_C',
                            u'Tscs_C', u'Tshs_C', u'Tsww_C', u'Tww_tank_C', u'Vw_m3', u'mcpcs_kWC', u'mcphs_kWC',
                            u'mcpww_kWC', u'occ_pax']
        self.assertEqual(set(expected_columns), set(df.columns), 'Column list of building csv does not match')
        self.assertEqual(df.shape[0], 8760, 'Expected one row per hour in the year')



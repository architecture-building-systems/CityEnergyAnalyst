"""
Create the data for tests/test_calc_thermal_loads_new_ventilation.py

This test-data changes when the core algorithms get updated. This script spits out the data used.
"""
import pandas as pd

from cea.demand.occupancy_model import schedule_maker
from cea.demand.thermal_loads import calc_thermal_loads, BuildingProperties
from cea.globalvar import GlobalVariables
from cea.inputlocator import InputLocator
from cea.utilities import epwreader


REFERENCE_CASE = r'C:\reference-case-open\baseline'

def main():
    locator = InputLocator(REFERENCE_CASE)
    gv = GlobalVariables()
    weather_path = locator.get_default_weather()
    weather_data = epwreader.epw_reader(weather_path)[['drybulb_C', 'relhum_percent', 'windspd_ms', 'skytemp_C']]

    building_properties = BuildingProperties(locator, gv)
    date = pd.date_range(gv.date_start, periods=8760, freq='H')
    list_uses = building_properties.list_uses()
    schedules = schedule_maker(date, locator, list_uses)
    usage_schedules = {'list_uses': list_uses,
                            'schedules': schedules}

    print("data for test_calc_thermal_loads_new_ventilation:")
    print building_properties.list_building_names()

    bpr = building_properties['B01']
    result = calc_thermal_loads('B01', bpr, weather_data, usage_schedules, date, gv, locator)

    # test the building csv file
    df = pd.read_csv(locator.get_demand_results_file('B01'))

    expected_columns = list(df.columns)
    print("expected_columns = %s" % repr(expected_columns))

    value_columns = [u'Ealf_kWh', u'Eauxf_kWh', u'Edataf_kWh', u'Ef_kWh', u'QCf_kWh', u'QHf_kWh',
                     u'Qcdataf_kWh', u'Qcref_kWh', u'Qcs_kWh', u'Qcsf_kWh', u'Qhs_kWh', u'Qhsf_kWh', u'Qww_kWh',
                     u'Qwwf_kWh', u'Tcsf_re_C', u'Thsf_re_C', u'Twwf_re_C', u'Tcsf_sup_C', u'Thsf_sup_C',
                     u'Twwf_sup_C']

    print("values = %s " % repr([df[column].sum() for column in value_columns]))

    print("data for test_calc_thermal_loads_other_buildings:")
    # randomly selected except for B302006716, which has `Af == 0`
    buildings = {'B01': (81124.39400, 150471.05200),
                 'B03': (81255.09200, 150520.01000),
                 'B02': (82176.15300, 150604.85100),
                 'B05': (84058.72400, 150841.56200),
                 'B04': (82356.22600, 150598.43400),
                 'B07': (81052.19000, 150490.94800),
                 'B06': (83108.45600, 150657.24900),
                 'B09': (84491.58100, 150853.54000),
                 'B08': (88572.59000, 151020.09300), }

    for building in buildings.keys():
        bpr = building_properties[building]
        b, qcf_kwh, qhf_kwh = run_for_single_building(building, bpr, weather_data, usage_schedules,
                                                      date, gv, locator)
        print("'%(b)s': (%(qcf_kwh).5f, %(qhf_kwh).5f)," % locals())


def run_for_single_building(building, bpr, weather_data, usage_schedules, date, gv, locator):
    calc_thermal_loads(building, bpr, weather_data, usage_schedules, date, gv, locator)
    df = pd.read_csv(locator.get_demand_results_file(building))
    return building, df['QCf_kWh'].sum(), df['QHf_kWh'].sum()

if __name__ == "__main__":
    main()



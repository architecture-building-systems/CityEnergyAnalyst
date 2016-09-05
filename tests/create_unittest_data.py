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


def main():
    locator = InputLocator(r'C:\reference-case\baseline')
    gv = GlobalVariables()
    weather_path = locator.get_default_weather()
    weather_data = epwreader.epw_reader(weather_path)[['drybulb_C', 'relhum_percent', 'windspd_ms']]

    building_properties = BuildingProperties(locator, gv)
    date = pd.date_range(gv.date_start, periods=8760, freq='H')
    list_uses = building_properties.list_uses()
    schedules = schedule_maker(date, locator, list_uses)
    usage_schedules = {'list_uses': list_uses,
                            'schedules': schedules}

    print("data for test_calc_thermal_loads_new_ventilation:")

    bpr = building_properties['B140577']
    result = calc_thermal_loads('B140577', bpr, weather_data, usage_schedules, date, gv, locator)

    # test the building csv file
    df = pd.read_csv(locator.get_demand_results_file('B140577'))

    expected_columns = list(df.columns)
    print("expected_columns = %s" % repr(expected_columns))

    value_columns = [u'Ealf_kWh', u'Eauxf_kWh', u'Edataf_kWh', u'Ef_kWh', u'QCf_kWh', u'QHf_kWh',
                     u'Qcdataf_kWh', u'Qcref_kWh', u'Qcs_kWh', u'Qcsf_kWh', u'Qhs_kWh', u'Qhsf_kWh', u'Qww_kWh',
                     u'Qwwf_kWh', u'Trcs_C', u'Trhs_C', u'Trww_C', u'Tscs_C', u'Tshs_C',
                     u'Tsww_C', u'Vw_m3', u'mcpcs_kWC', u'mcphs_kWC', u'mcpww_kWC', u'occ_pax']

    print("values = %s " % repr([df[column].sum() for column in value_columns]))

    print("data for test_calc_thermal_loads_other_buildings:")
    import multiprocessing as mp
    pool = mp.Pool()
    # randomly selected except for B302006716, which has `Af == 0`
    buildings = {'B302006716': (0.00, 0.00),
                 'B140557': (34678.07500, 101548.65300),
                 'B140577': (723364.82000, 1677242.60300),
                 'B2372467': (19957.19600, 51728.88700),
                 'B302040335': (1016.90100, 4241.73800),
                 'B140571': (46064.14000, 121390.19900)}

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



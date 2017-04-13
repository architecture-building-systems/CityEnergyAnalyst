"""
Create the data for tests/test_calc_thermal_loads_new_ventilation.py

This test-data changes when the core algorithms get updated. This script spits out the data used.
"""
import os

import pandas as pd

from cea.demand.occupancy_model import schedule_maker
from cea.demand.thermal_loads import calc_thermal_loads, BuildingProperties
from cea.globalvar import GlobalVariables
from cea.inputlocator import InputLocator
from cea.utilities import epwreader


def main():
    import zipfile
    import cea.examples
    import tempfile
    archive = zipfile.ZipFile(os.path.join(os.path.dirname(cea.examples.__file__), 'reference-case-open.zip'))
    archive.extractall(tempfile.gettempdir())
    reference_case = os.path.join(tempfile.gettempdir(), 'reference-case-open', 'baseline')
    locator = InputLocator(reference_case)
    gv = GlobalVariables()
    weather_path = locator.get_default_weather()
    weather_data = epwreader.epw_reader(weather_path)[
        ['drybulb_C', 'relhum_percent', 'windspd_ms', 'skytemp_C']]

    # run properties script
    import cea.demand.preprocessing.properties
    cea.demand.preprocessing.properties.properties(locator, True, True, True, True)

    building_properties = BuildingProperties(locator, gv)
    date = pd.date_range(gv.date_start, periods=8760, freq='H')
    list_uses = building_properties.list_uses()
    schedules, occupancy_densities = schedule_maker(date, locator, list_uses)
    usage_schedules = {'list_uses': list_uses, 'schedules': schedules, 'occupancy_densities': occupancy_densities}

    print("data for test_calc_thermal_loads:")
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
    buildings = ['B01', 'B03', 'B02', 'B05', 'B04','B07','B06','B09',
                 'B08']

    for building in buildings:
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



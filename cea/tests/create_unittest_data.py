"""
Create the data for cea/tests/test_calc_thermal_loads.py

Run this script when the core algorithms get updated and the unittests in ``test_calc_thermal_loads.py`` stop working.
The script overwrites the file ``cea/tests/test_calc_thermal_loads.config`` which contains the data used for the
unit tests. You can safely ignore the output printed to STDOUT - it is used for debugging purposes only.

NOTE: Check first to make sure the core algorithms are correct, i.e. the changes to the outputs behave as expected.
"""
import os
import zipfile
import tempfile
import ConfigParser
import json
import pandas as pd

from cea.demand.occupancy_model import schedule_maker
from cea.demand.thermal_loads import calc_thermal_loads
from cea.demand.demand_main import properties_and_schedule
from cea.globalvar import GlobalVariables
from cea.inputlocator import InputLocator
import cea.config
from cea.utilities import epwreader


def main(output_file):
    import cea.examples
    archive = zipfile.ZipFile(os.path.join(os.path.dirname(cea.examples.__file__), 'reference-case-open.zip'))
    archive.extractall(tempfile.gettempdir())
    reference_case = os.path.join(tempfile.gettempdir(), 'reference-case-open', 'baseline')

    locator = InputLocator(reference_case)
    config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    gv = GlobalVariables()
    gv.config = config

    weather_path = locator.get_weather('Zug')
    weather_data = epwreader.epw_reader(weather_path)[
        ['year', 'drybulb_C', 'wetbulb_C', 'relhum_percent', 'windspd_ms', 'skytemp_C']]

    # run properties script
    import cea.demand.preprocessing.data_helper
    cea.demand.preprocessing.data_helper.data_helper(locator, config, True, True, True, True, True, True)

    region = config.region
    year = weather_data['year'][0]
    use_daysim_radiation = config.demand.use_daysim_radiation
    resolution_outputs = config.demand.resolution_output
    loads_output = config.demand.loads_output
    massflows_output = config.demand.massflows_output
    temperatures_output = config.demand.temperatures_output
    format_output = config.demand.format_output
    use_dynamic_infiltration_calculation =  config.demand.use_dynamic_infiltration_calculation
    building_properties, schedules_dict, date = properties_and_schedule(gv, locator, region, year, use_daysim_radiation)

    print("data for test_calc_thermal_loads:")
    print(building_properties.list_building_names())

    bpr = building_properties['B01']
    result = calc_thermal_loads('B01', bpr, weather_data, schedules_dict, date, gv, locator,
                                use_dynamic_infiltration_calculation,
                                resolution_outputs, loads_output, massflows_output,
                                temperatures_output, format_output)

    # test the building csv file
    df = pd.read_csv(locator.get_demand_results_file('B01'))

    expected_columns = list(df.columns)
    print("expected_columns = %s" % repr(expected_columns))

    test_config = ConfigParser.SafeConfigParser()
    test_config.read(output_file)

    value_columns = [u'Ealf_kWh', u'Eauxf_kWh', u'Edataf_kWh', u'Ef_kWh', u'QCf_kWh', u'QHf_kWh',
                     u'Qcdataf_kWh', u'Qcref_kWh', u'Qcs_kWh', u'Qcsf_kWh', u'Qhs_kWh', u'Qhsf_kWh', u'Qww_kWh',
                     u'Qwwf_kWh', u'Tcsf_re_C', u'Thsf_re_C', u'Twwf_re_C', u'Tcsf_sup_C', u'Thsf_sup_C',
                     u'Twwf_sup_C']

    values = [float(df[column].sum()) for column in value_columns]
    print("values = %s " % repr(values))

    if not test_config.has_section("test_calc_thermal_loads"):
        test_config.add_section("test_calc_thermal_loads")
    test_config.set("test_calc_thermal_loads", "value_columns", json.dumps(value_columns))
    print values
    test_config.set("test_calc_thermal_loads", "values", json.dumps(values))

    print("data for test_calc_thermal_loads_other_buildings:")
    buildings = ['B01', 'B03', 'B02', 'B05', 'B04', 'B07', 'B06', 'B09',
                 'B08']

    results = {}
    for building in buildings:
        bpr = building_properties[building]
        b, qcf_kwh, qhf_kwh = run_for_single_building(building, bpr, weather_data, schedules_dict,
                                                      date, gv, locator,
                                use_dynamic_infiltration_calculation,
                                resolution_outputs, loads_output, massflows_output,
                                temperatures_output, format_output)
        print("'%(b)s': (%(qcf_kwh).5f, %(qhf_kwh).5f)," % locals())
        results[building] = (qcf_kwh, qhf_kwh)

    if not test_config.has_section("test_calc_thermal_loads_other_buildings"):
        test_config.add_section("test_calc_thermal_loads_other_buildings")
    test_config.set("test_calc_thermal_loads_other_buildings", "results", json.dumps(results))
    with open(output_file, 'w') as f:
        test_config.write(f)
    print("Wrote output to %(output_file)s" % locals())


def run_for_single_building(building, bpr, weather_data, usage_schedules, date, gv, locator,
                                use_dynamic_infiltration_calculation,
                                resolution_outputs, loads_output, massflows_output,
                                temperatures_output, format_output):
    calc_thermal_loads(building, bpr, weather_data, usage_schedules, date, gv, locator,
                                use_dynamic_infiltration_calculation,
                                resolution_outputs, loads_output, massflows_output,
                                temperatures_output, format_output)
    df = pd.read_csv(locator.get_demand_results_file(building))
    return building, float(df['QCf_kWh'].sum()), float(df['QHf_kWh'].sum())


if __name__ == "__main__":
    output_file = os.path.join(os.path.dirname(__file__), 'test_calc_thermal_loads.config')
    main(output_file)

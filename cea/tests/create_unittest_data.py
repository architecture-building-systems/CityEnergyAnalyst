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

from cea.demand.schedule_maker.schedule_maker import schedule_maker_main
from cea.demand.thermal_loads import calc_thermal_loads
from cea.demand.building_properties import BuildingProperties
from cea.utilities.date import get_dates_from_year
from cea.inputlocator import InputLocator
from cea.utilities import epwreader


def main(output_file):
    import cea.examples
    archive = zipfile.ZipFile(os.path.join(os.path.dirname(cea.examples.__file__), 'reference-case-open.zip'))
    archive.extractall(tempfile.gettempdir())
    reference_case = os.path.join(tempfile.gettempdir(), 'reference-case-open', 'baseline')

    locator = InputLocator(reference_case)
    config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)

    weather_path = locator.get_weather('Zug-inducity_1990_2010_TMY')
    weather_data = epwreader.epw_reader(weather_path)[
        ['year', 'drybulb_C', 'wetbulb_C', 'relhum_percent', 'windspd_ms', 'skytemp_C']]

    # run properties script
    import cea.datamanagement.archetypes_mapper
    cea.datamanagement.archetypes_mapper.archetypes_mapper(locator, True, True, True, True, True, True, [])

    year = weather_data['year'][0]
    date_range = get_dates_from_year(year)
    resolution_outputs = config.demand.resolution_output
    loads_output = config.demand.loads_output
    massflows_output = config.demand.massflows_output
    temperatures_output = config.demand.temperatures_output
    use_dynamic_infiltration_calculation = config.demand.use_dynamic_infiltration_calculation
    debug = config.debug
    building_properties = BuildingProperties(locator, config.demand.override_variables)

    print("data for test_calc_thermal_loads:")
    print(building_properties.list_building_names())

    schedule_maker_main(locator, config, building=None)

    bpr = building_properties['B01']
    result = calc_thermal_loads('B01', bpr, weather_data, date_range, locator,
                                use_dynamic_infiltration_calculation, resolution_outputs, loads_output,
                                massflows_output, temperatures_output, config,
                                debug)

    # test the building csv file
    df = pd.read_csv(locator.get_demand_results_file('B01'))

    expected_columns = list(df.columns)
    print("expected_columns = %s" % repr(expected_columns))

    test_config = ConfigParser.SafeConfigParser()
    test_config.read(output_file)

    value_columns = [u"E_sys_kWh", u"Qcdata_sys_kWh", u"Qcre_sys_kWh", u"Qcs_sys_kWh", u"Qhs_sys_kWh", u"Qww_sys_kWh",
                     u"Tcs_sys_re_C", u"Ths_sys_re_C", u"Tww_sys_re_C", u"Tcs_sys_sup_C", u"Ths_sys_sup_C", u"Tww_sys_sup_C"]

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
        b, qhs_sys_kwh, qcs_sys_kwh, qww_sys_kwh = run_for_single_building(building, bpr, weather_data,
                                                                           date_range, locator,
                                                                           use_dynamic_infiltration_calculation,
                                                                           resolution_outputs, loads_output,
                                                                           massflows_output, temperatures_output,
                                                                           config,
                                                                           debug)
        print("'%(b)s': (%(qhs_sys_kwh).5f, %(qcs_sys_kwh).5f, %(qww_sys_kwh).5f)," % locals())
        results[building] = (qhs_sys_kwh, qcs_sys_kwh, qww_sys_kwh)

    if not test_config.has_section("test_calc_thermal_loads_other_buildings"):
        test_config.add_section("test_calc_thermal_loads_other_buildings")
    test_config.set("test_calc_thermal_loads_other_buildings", "results", json.dumps(results))
    with open(output_file, 'w') as f:
        test_config.write(f)
    print("Wrote output to %(output_file)s" % locals())


def run_for_single_building(building, bpr, weather_data, date_range, locator,
                            use_dynamic_infiltration_calculation, resolution_outputs, loads_output,
                            massflows_output, temperatures_output, config, debug):
    calc_thermal_loads(building, bpr, weather_data, date_range, locator,
                       use_dynamic_infiltration_calculation, resolution_outputs, loads_output, massflows_output,
                       temperatures_output, config, debug)
    df = pd.read_csv(locator.get_demand_results_file(building))
    return building, float(df['Qhs_sys_kWh'].sum()), df['Qcs_sys_kWh'].sum(), float(df['Qww_sys_kWh'].sum())


if __name__ == "__main__":
    output_file = os.path.join(os.path.dirname(__file__), 'test_calc_thermal_loads.config')
    main(output_file)

"""
Create the data for cea/tests/test_calc_thermal_loads.py

Run this script when the core algorithms get updated and the unittests in ``test_calc_thermal_loads.py`` stop working.
The script overwrites the file ``cea/tests/test_calc_thermal_loads.config`` which contains the data used for the
unit tests. You can safely ignore the output printed to STDOUT - it is used for debugging purposes only.

NOTE: Check first to make sure the core algorithms are correct, i.e. the changes to the outputs behave as expected.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

import configparser
import json
import os

import pandas as pd

from cea.config import Configuration, DEFAULT_CONFIG
from cea.demand.building_properties import BuildingProperties
from cea.demand.occupancy_helper import occupancy_helper_main
from cea.demand.thermal_loads import calc_thermal_loads
from cea.inputlocator import ReferenceCaseOpenLocator
from cea.utilities import epwreader
from cea.utilities.date import get_date_range_hours_from_year

if TYPE_CHECKING:
    from cea.demand.building_properties.building_properties_row import BuildingPropertiesRow


# FIXME: Duplicated code with cea/tests/test_calc_thermal_loads.py
def main(output_file):
    config = Configuration(DEFAULT_CONFIG)
    locator = ReferenceCaseOpenLocator()

    config.project = locator.project_path
    config.scenario = locator.scenario

    weather_path = locator.get_weather('Zug_inducity_2009')
    weather_data = epwreader.epw_reader(weather_path)[
        ['year', 'drybulb_C', 'wetbulb_C', 'relhum_percent', 'windspd_ms', 'skytemp_C']]

    year = weather_data['year'][0]
    date_range = get_date_range_hours_from_year(year)
    resolution_outputs = config.demand.resolution_output
    loads_output = config.demand.loads_output
    massflows_output = config.demand.massflows_output
    temperatures_output = config.demand.temperatures_output
    use_dynamic_infiltration_calculation = config.demand.use_dynamic_infiltration_calculation
    debug = config.debug
    building_properties = BuildingProperties(locator, epwreader.epw_reader(locator.get_weather_file()))

    print("data for test_calc_thermal_loads:")
    print(building_properties.list_building_names())

    occupancy_helper_main(locator, config, building='B1011')

    bpr = building_properties['B1011']
    result = calc_thermal_loads('B1011', bpr, weather_data, date_range, locator,
                                use_dynamic_infiltration_calculation, resolution_outputs, loads_output,
                                massflows_output, temperatures_output, config,
                                debug)

    # test the building csv file
    df = pd.read_csv(locator.get_demand_results_file('B1011'))

    expected_columns = list(df.columns)
    print("expected_columns = %s" % repr(expected_columns))

    test_config = configparser.ConfigParser()
    test_config.read(output_file)

    value_columns = [u"E_sys_kWh", u"Qcdata_sys_kWh", u"Qcre_sys_kWh", u"Qcs_sys_kWh", u"Qhs_sys_kWh", u"Qww_sys_kWh",
                     u"Tcs_sys_re_C", u"Ths_sys_re_C", u"Tww_sys_re_C", u"Tcs_sys_sup_C", u"Ths_sys_sup_C",
                     u"Tww_sys_sup_C"]

    values = [float(df[column].sum()) for column in value_columns]
    print("values = %s " % repr(values))

    if not test_config.has_section("test_calc_thermal_loads"):
        test_config.add_section("test_calc_thermal_loads")
    test_config.set("test_calc_thermal_loads", "value_columns", json.dumps(value_columns))
    print(values)
    test_config.set("test_calc_thermal_loads", "values", json.dumps(values))

    print("data for test_calc_thermal_loads_other_buildings:")
    buildings = ['B1013', 'B1012',
                 'B1010',
                 'B1000',
                 'B1009',
                 'B1011',
                 'B1006',
                 'B1003',
                 'B1004',
                 'B1001',
                 'B1002',
                 'B1005',
                 'B1008',
                 'B1007',
                 'B1014'
                 ]

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


def run_for_single_building(building, bpr: BuildingPropertiesRow, weather_data, date_range, locator,
                            use_dynamic_infiltration_calculation, resolution_outputs, loads_output,
                            massflows_output, temperatures_output, config, debug):
    config.multiprocessing = False
    occupancy_helper_main(locator, config, building=building)
    calc_thermal_loads(building, bpr, weather_data, date_range, locator,
                       use_dynamic_infiltration_calculation, resolution_outputs, loads_output, massflows_output,
                       temperatures_output, config, debug)
    df = pd.read_csv(locator.get_demand_results_file(building))
    return building, float(df['Qhs_sys_kWh'].sum()), df['Qcs_sys_kWh'].sum(), float(df['Qww_sys_kWh'].sum())


if __name__ == "__main__":
    output_file = os.path.join(os.path.dirname(__file__), 'test_calc_thermal_loads.config')
    main(output_file)

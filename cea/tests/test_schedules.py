"""
This module contains unit tests for the schedules used by the CEA. The schedule code is tested against data in the
file `test_schedules.config` that can be created by running this file. Note, however, that this will overwrite the
test data - you should only do this if you are sure that the new data is correct.
"""

import ConfigParser
import json
import os
import unittest

import pandas as pd

import cea.config
from cea.constants import HOURS_IN_YEAR
from cea.datamanagement.archetypes_mapper import calculate_average_multiuse
from cea.demand.building_properties import BuildingProperties
from cea.demand.schedule_maker.schedule_maker import schedule_maker_main
from cea.inputlocator import ReferenceCaseOpenLocator
from cea.utilities import epwreader

REFERENCE_TIME = 3456


class TestBuildingPreprocessing(unittest.TestCase):
    def test_mixed_use_archetype_values(self):
        # test if a sample mixed use building gets standard results
        locator = ReferenceCaseOpenLocator()
        config = ConfigParser.SafeConfigParser()
        config.read(get_test_config_path())

        calculated_results = calculate_mixed_use_archetype_values_results(locator).to_dict()
        print(calculated_results)
        # compare to reference values
        expected_results = json.loads(config.get('test_mixed_use_archetype_values', 'expected_results'))
        for column, rows in expected_results.items():
            self.assertIn(column, calculated_results)
            for building, value in rows.items():
                self.assertIn(building, calculated_results[column])
                self.assertAlmostEqual(value, calculated_results[column][building], 4)


class TestScheduleCreation(unittest.TestCase):
    def test_mixed_use_schedules(self):
        locator = ReferenceCaseOpenLocator()
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.scenario = locator.scenario

        building_properties = BuildingProperties(locator, False)
        bpr = building_properties['B01']
        bpr.occupancy = {'OFFICE': 0.5, 'INDUSTRIAL': 0.5}
        bpr.comfort['mainuse'] = 'OFFICE'

        # calculate schedules
        schedule_maker_main(locator, config)
        calculated_schedules = pd.read_csv(locator.get_schedule_model_file('B01')).set_index('DATE')

        config = ConfigParser.SafeConfigParser()
        config.read(get_test_config_path())
        reference_results = json.loads(config.get('test_mixed_use_schedules', 'reference_results'))

        for schedule in reference_results:
            if (isinstance(calculated_schedules[schedule][REFERENCE_TIME], str)) and (isinstance(
                    reference_results[schedule], unicode)):
                self.assertEqual(calculated_schedules[schedule][REFERENCE_TIME], reference_results[schedule],
                                 msg="Schedule '{}' at time {}, {} != {}".format(schedule, str(REFERENCE_TIME),
                                                                                 calculated_schedules[schedule][
                                                                                     REFERENCE_TIME],
                                                                                 reference_results[schedule]))
            else:
                self.assertAlmostEqual(calculated_schedules[schedule][REFERENCE_TIME], reference_results[schedule],
                                       places=4,
                                       msg="Schedule '{}' at time {}, {} != {}".format(schedule, str(REFERENCE_TIME),
                                                                                       calculated_schedules[schedule][
                                                                                           REFERENCE_TIME],
                                                                                       reference_results[schedule]))


def get_test_config_path():
    """return the path to the test data configuration file (``cea/tests/test_schedules.config``)"""
    return os.path.join(os.path.dirname(__file__), 'test_schedules.config')


def calculate_mixed_use_archetype_values_results(locator):
    """calculate the results for the test - refactored, so we can also use it to write the results to the
    config file."""

    occ_densities = pd.read_excel(locator.get_database_use_types_properties(), 'INTERNAL_LOADS').set_index('code')
    office_occ = float(occ_densities.ix['OFFICE', 'Occ_m2pax'])
    gym_occ = float(occ_densities.ix['GYM', 'Occ_m2pax'])
    calculated_results = calculate_average_multiuse(
        fields=['X_ghpax', 'El_Wm2'],
        properties_df=pd.DataFrame(data=[['B1', 'OFFICE', 0.5, 'NONE', 0.5, 'NONE', 0.0, 0.0, 0.0, 0.0], ['B2', 'GYM', 0.75, 'OFFICE', 0.25, 'NONE', 0.0, 0.0, 0.0, 0.0]],
                                   columns=['Name', "1ST_USE", "1ST_USE_R", '2ND_USE', '2ND_USE_R', '3RD_USE', '3RD_USE_R', 'X_ghpax', 'El_Wm2', 'Occ_m2pax']),
        occupant_densities={'OFFICE': 1 / office_occ, 'GYM': 1 / gym_occ},
        list_uses=['OFFICE', 'GYM'],
        properties_DB=pd.read_excel(locator.get_database_use_types_properties(), 'INTERNAL_LOADS')).set_index('Name')

    return calculated_results


def create_data():
    """Create test data to compare against - run this the first time you make changes that affect the results. Note,
    this will overwrite the previous test data."""
    test_config = ConfigParser.SafeConfigParser()
    test_config.read(get_test_config_path())
    if not test_config.has_section('test_mixed_use_archetype_values'):
        test_config.add_section('test_mixed_use_archetype_values')
    locator = ReferenceCaseOpenLocator()
    expected_results = calculate_mixed_use_archetype_values_results(locator)
    test_config.set('test_mixed_use_archetype_values', 'expected_results', expected_results.to_json())

    config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    locator = ReferenceCaseOpenLocator()

    # calculate schedules
    building_properties = BuildingProperties(locator, False)
    bpr = building_properties['B01']
    list_uses = ['OFFICE', 'INDUSTRIAL']
    bpr.occupancy = {'OFFICE': 0.5, 'INDUSTRIAL': 0.5}
    # get year from weather file
    weather_path = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_path)[['year']]
    year = weather_data['year'][0]
    date = pd.date_range(str(year) + '/01/01', periods=HOURS_IN_YEAR, freq='H')

    calculated_schedules = schedule_maker_main(locator, config)
    if not test_config.has_section('test_mixed_use_schedules'):
        test_config.add_section('test_mixed_use_schedules')
    test_config.set('test_mixed_use_schedules', 'reference_results', json.dumps(
        {schedule: calculated_schedules[schedule][REFERENCE_TIME] for schedule in calculated_schedules.keys()}))

    with open(get_test_config_path(), 'w') as f:
        test_config.write(f)


if __name__ == '__main__':
    create_data()

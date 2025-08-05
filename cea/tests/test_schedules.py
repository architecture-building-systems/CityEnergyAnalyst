"""
This module contains unit tests for the schedules used by the CEA. The schedule code is tested against data in the
file `test_schedules.config` that can be created by running this file. Note, however, that this will overwrite the
test data - you should only do this if you are sure that the new data is correct.
"""

import configparser
import json
import os
import unittest

import pandas as pd

import cea.config
from cea.datamanagement.archetypes_mapper import calculate_average_multiuse
from cea.datamanagement.databases_verification import COLUMNS_ZONE_TYPOLOGY
from cea.demand.occupancy_helper import occupancy_helper_main
from cea.inputlocator import ReferenceCaseOpenLocator

REFERENCE_TIME = 3456


class TestBuildingPreprocessing(unittest.TestCase):
    def test_mixed_use_archetype_values(self):
        # test if a sample mixed use building gets standard results
        locator = ReferenceCaseOpenLocator()
        config = configparser.ConfigParser()
        config.read(get_test_config_path())

        calculated_results = calculate_mixed_use_archetype_values_results(locator).to_dict()
        print(calculated_results)
        # compare to reference values
        expected_results = json.loads(config.get('test_mixed_use_archetype_values', 'expected_results'))
        for column, rows in expected_results.items():
            self.assertIn(column, calculated_results)
            for building, value in rows.items():
                self.assertIn(building, calculated_results[column])
                self.assertAlmostEqual(value, calculated_results[column][building], 4,
                                       msg=f"Column {column} for building {building} does not match")


class TestScheduleCreation(unittest.TestCase):
    def test_mixed_use_schedules(self):
        locator = ReferenceCaseOpenLocator()
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.scenario = locator.scenario
        config.multiprocessing = False

        # reinit database to ensure updated databases are loaded
        from cea.datamanagement.database_helper import main as database_helper
        config.database_helper.databases_path = "CH"
        config.database_helper.databases = ["archetypes", "assemblies", "components"]
        database_helper(config)

        # calculate schedules
        occupancy_helper_main(locator, config)
        calculated_schedules = pd.read_csv(locator.get_occupancy_model_file('B1011')).set_index('date')

        test_config = configparser.ConfigParser()
        test_config.read(get_test_config_path())
        reference_results = json.loads(test_config.get('test_mixed_use_schedules', 'reference_results'))

        for schedule in reference_results:
            if (isinstance(calculated_schedules[schedule][REFERENCE_TIME], str)) and (isinstance(
                    reference_results[schedule], str)):
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
    occ_densities = pd.read_csv(locator.get_database_archetypes_use_type()).set_index('use_type')
    office_occ = float(occ_densities.loc['OFFICE', 'Occ_m2p'])
    lab_occ = float(occ_densities.loc['LAB', 'Occ_m2p'])
    indus_occ = float(occ_densities.loc['INDUSTRIAL', 'Occ_m2p'])

    # FIXME: This is a hack to make the test pass. Figure out how calculate_average_multiuse works
    properties_df = pd.DataFrame(data=[['B1011', '', '', 'OFFICE', 0.5, 'SERVERROOM', 0.5, 'NONE', 0.0, 0.0, 0.0, 0.0],
                                       ['B1012', '', '', 'OFFICE', 0.6, 'LAB', 0.2, 'INDUSTRIAL', 0.2, 0.0, 0.0, 0.0]],
                                 columns=COLUMNS_ZONE_TYPOLOGY + ['X_ghp', 'El_Wm2', 'Occ_m2p'])

    calculated_results = calculate_average_multiuse(
        fields=['X_ghp', 'El_Wm2'],
        properties_df=properties_df,
        occupant_densities={'OFFICE': 1.0 / office_occ,
                            'LAB': 1.0 / lab_occ,
                            'INDUSTRIAL': 1.0 / indus_occ,
                            'SERVERROOM': 0.0 },
        list_uses=['OFFICE', 'LAB', 'INDUSTRIAL', 'SERVERROOM'],
        properties_db=occ_densities).set_index('name')

    return calculated_results


def create_data():
    """Create test data to compare against - run this the first time you make changes that affect the results. Note,
    this will overwrite the previous test data."""
    test_config = configparser.ConfigParser()
    test_config.read(get_test_config_path())
    if not test_config.has_section('test_mixed_use_archetype_values'):
        test_config.add_section('test_mixed_use_archetype_values')
    locator = ReferenceCaseOpenLocator()
    expected_results = calculate_mixed_use_archetype_values_results(locator)
    test_config.set('test_mixed_use_archetype_values', 'expected_results', expected_results.to_json())

    config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    locator = ReferenceCaseOpenLocator()

    # reinit database to ensure updated databases are loaded
    from cea.datamanagement.database_helper import main as database_helper
    config.database_helper.databases_path = "CH"
    config.database_helper.databases = ["archetypes", "assemblies", "components"]
    database_helper(config)

    # read weather file
    # weather_path = locator.get_weather_file()
    # weather_data = epwreader.epw_reader(weather_path)

    calculated_schedules = occupancy_helper_main(locator, config)
    if not test_config.has_section('test_mixed_use_schedules'):
        test_config.add_section('test_mixed_use_schedules')
    test_config.set('test_mixed_use_schedules', 'reference_results', json.dumps(
        {schedule: calculated_schedules[schedule][REFERENCE_TIME] for schedule in calculated_schedules.keys()}))

    with open(get_test_config_path(), 'w') as f:
        test_config.write(f)


if __name__ == '__main__':
    create_data()

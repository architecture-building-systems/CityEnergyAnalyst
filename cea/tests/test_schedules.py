"""
This module contains unit tests for the schedules used by the CEA. The schedule code is tested against data in the
file `test_schedules.config` that can be created by running this file. Note, however, that this will overwrite the
test data - you should only do this if you are sure that the new data is correct.
"""

import ConfigParser
import json
import os
import unittest

import numpy as np
import pandas as pd

import cea.config
from cea.constants import HOURS_IN_YEAR
from cea.datamanagement.data_helper import calculate_average_multiuse, correct_archetype_areas, data_helper
from cea.datamanagement.schedule_helper import calc_mixed_schedule
from cea.demand.building_properties import BuildingProperties
from cea.demand.schedule_maker.schedule_maker import schedule_maker_main
from cea.inputlocator import ReferenceCaseOpenLocator
from cea.utilities import epwreader
from cea.utilities.dbf import dbf_to_dataframe

REFERENCE_TIME = 3456


class TestSavingLoadingSchedules(unittest.TestCase):
    """Make sure that the schedules loaded from disk are the same as those loaded if they're not present."""

    def test_get_building_schedules(self):
        """Make sure running get_building_schedules for same case returns the same value"""
        test_building = 'B01'
        config = cea.config.Configuration()
        config.schedule_maker.schedule_model = 'deterministic'
        config.schedule_maker.buildings = [test_building]
        config.demand.use_stochastic_occupancy = False
        locator = ReferenceCaseOpenLocator()

        # create archetypal schedules in scenario inputs
        data_helper(locator, region='CH', overwrite_technology_folder=True,
                    update_architecture_dbf=True, update_HVAC_systems_dbf=True, update_indoor_comfort_dbf=True,
                    update_internal_loads_dbf=True, update_supply_systems_dbf=True,
                    update_schedule_operation_cea=True, schedule_model='CH-SIA-2014',
                    buildings=config.schedule_maker.buildings)

        # run get_building_schedules on clean folder - they're created from scratch
        if os.path.exists(locator.get_occupancy_model_file(test_building)):
            os.remove(locator.get_occupancy_model_file(test_building))
        schedule_maker_main(locator, config)
        fresh_schedules = pd.read_csv(locator.get_occupancy_model_file(test_building)).set_index('DATE')

        # run again to get the frozen version
        schedule_maker_main(locator, config)
        frozen_schedules = pd.read_csv(locator.get_occupancy_model_file(test_building)).set_index('DATE')

        self.assertEqual(sorted(fresh_schedules.keys()), sorted(frozen_schedules.keys()))
        for schedule in fresh_schedules:
            for i in range(len(fresh_schedules[schedule])):
                fresh = fresh_schedules[schedule][i]
                frozen = frozen_schedules[schedule][i]
                if (not isinstance(fresh, str)) and (not isinstance(frozen, str)):
                    if np.isnan(fresh) and np.isnan(frozen):
                        pass
                    else:
                        self.assertEqual(fresh, frozen)
                else:
                    self.assertEqual(fresh, frozen)
            self.assertIsNone(np.testing.assert_array_equal(fresh_schedules[schedule], frozen_schedules[schedule]))


class TestBuildingPreprocessing(unittest.TestCase):
    def test_mixed_use_archetype_values(self):
        # test if a sample mixed use building gets standard results
        locator = ReferenceCaseOpenLocator()
        config = ConfigParser.SafeConfigParser()
        config.read(get_test_config_path())

        calculated_results = calculate_mixed_use_archetype_values_results(locator).to_dict()

        # compare to reference values
        expected_results = json.loads(config.get('test_mixed_use_archetype_values', 'expected_results'))
        for column, rows in expected_results.items():
            self.assertIn(column, calculated_results)
            for building, value in rows.items():
                self.assertIn(building, calculated_results[column])
                self.assertAlmostEqual(value, calculated_results[column][building], 4)

        architecture_DB = pd.read_excel(locator.get_archetypes_properties(), 'ARCHITECTURE')
        architecture_DB['Code'] = architecture_DB.apply(lambda x: x['building_use'] + str(x['year_start']) +
                                                                  str(x['year_end']) + x['standard'], axis=1)

        self.assertEqual(correct_archetype_areas(
            prop_architecture_df=pd.DataFrame(
                data=[['B1', 0.5, 0.5, 0.0, 2006, 2020, 'C'], ['B2', 0.2, 0.8, 0.0, 1000, 1920, 'R']],
                columns=['Name', 'SERVERROOM', 'PARKING', 'Hs', 'year_start', 'year_end', 'standard']),
            architecture_DB=architecture_DB,
            list_uses=['SERVERROOM', 'PARKING']),
            ([0.5, 0.2], [0.5, 0.2], [0.95, 0.9200000000000002]))


class TestScheduleCreation(unittest.TestCase):
    def test_mixed_use_schedules(self):
        locator = ReferenceCaseOpenLocator()
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.scenario = locator.scenario
        stochastic_occupancy = config.demand.use_stochastic_occupancy

        # get year from weather file
        weather_path = locator.get_weather_file()
        weather_data = epwreader.epw_reader(weather_path)[['year']]
        year = weather_data['year'][0]
        date = pd.date_range(str(year) + '/01/01', periods=HOURS_IN_YEAR, freq='H')

        building_properties = BuildingProperties(locator, False)
        bpr = building_properties['B01']
        list_uses = ['OFFICE', 'INDUSTRIAL']
        bpr.occupancy = {'OFFICE': 0.5, 'INDUSTRIAL': 0.5}
        bpr.comfort['mainuse'] = 'OFFICE'

        # calculate schedules
        calculated_schedules = schedule_maker_main(locator, config)

        config = ConfigParser.SafeConfigParser()
        config.read(get_test_config_path())
        reference_results = json.loads(config.get('test_mixed_use_schedules', 'reference_results'))

        for schedule in reference_results:
            self.assertAlmostEqual(calculated_schedules[schedule][REFERENCE_TIME], reference_results[schedule],
                                   places=4, msg="Schedule '%s' at time %s, %f != %f" % (
                    schedule, str(REFERENCE_TIME), calculated_schedules[schedule][
                        REFERENCE_TIME],
                    reference_results[schedule]))


def get_test_config_path():
    """return the path to the test data configuration file (``cea/tests/test_schedules.config``)"""
    return os.path.join(os.path.dirname(__file__), 'test_schedules.config')


def calculate_mixed_use_archetype_values_results(locator):
    """calculate the results for the test - refactored, so we can also use it to write the results to the
    config file."""

    occ_densities = pd.read_excel(locator.get_archetypes_properties(), 'INTERNAL_LOADS').set_index('Code')
    office_occ = float(occ_densities.ix['OFFICE', 'Occ_m2pax'])
    gym_occ = float(occ_densities.ix['GYM', 'Occ_m2pax'])
    calculated_results = calculate_average_multiuse(
        fields=['X_ghp', 'El_Wm2'],
        properties_df=pd.DataFrame(data=[['B1', 0.5, 0.5, 0.0, 0.0, 0.0], ['B2', 0.25, 0.75, 0.0, 0.0, 0.0]],
                                   columns=['Name', 'OFFICE', 'GYM', 'X_ghpax', 'El_Wm2', 'Occ_m2pax']),
        occupant_densities={'OFFICE': 1 / office_occ, 'GYM': 1 / gym_occ},
        list_uses=['OFFICE', 'GYM'],
        properties_DB=pd.read_excel(locator.get_archetypes_properties(), 'INTERNAL_LOADS')).set_index('Name')

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

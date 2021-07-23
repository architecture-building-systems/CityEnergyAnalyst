"""
Test cea.technologies
"""




import unittest
import numpy as np
import pandas as pd
import configparser
import json
import os
import cea.config
from cea.technologies.cooling_tower import calc_CT_partload_factor, calc_CT
from cea.technologies.storage_tank_pcm import Storage_tank_PCM

class TestColdPcmThermalStorage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # importing default config of CEA
        cls.config = configparser.ConfigParser().read(get_test_config_path())
        cls.config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)

        # importing test config for this test
        cls.test_config = configparser.ConfigParser()
        cls.test_config.read(get_test_config_path())

        # extracting configuration for this test (input parameters and expected results)
        cls.size_storage_Wh = cls.test_config.size_storage_Wh # the size of the storage to test
        cls.T_ambient_K = cls.test_config.T_ambient_K # the outdoor temperature of the storage
        cls.days_to_test = cls.test_config.days_to_test # the number of days to test the storage
        cls.charging_rate_per_hour_perc = cls.test_config.charging_rate_per_hour_perc # the rate of charge per hour as a function of the size
        cls.discharging_rate_per_hour_perc = cls.test_config.discharging_rate_per_hour_perc # the rate of discharge per hour as a function of the size
        cls.hourly_operation_schedule_day = cls.test_config.hourly_operation_schedule_day # vector with tuples describing whether the storage is charging, balanced, or discharging and for how long. This is only for one day.
        cls.expected_results = cls.test_config.expected_results # vector storing the results expected of the test

        #getting the number of storage systems available


    def test_cold_pcm_thermal_storage(self):
         = self.building_properties['B1011']
        self.config.general.multiprocessing = False
        self.config.schedule_maker.schedule_model = "deterministic"
        schedule_maker_main(self.locator, self.config, building='B1011')

    def test_CT_partload_factor(self):
        """Make sure the partload factor is always positive."""
        partload_ratios = np.arange(0.0, 1.1, 0.1)
        partload_factors = np.vectorize(calc_CT_partload_factor)(partload_ratios)
        self.assertGreaterEqual(partload_factors.all(), 0.0)

    def test_calc_CT(self):
        """Make sure the calculation method remains the same."""
        q_hot_Wh = np.arange(0.0, 1E6, 1E5)
        Q_nom_W = max(q_hot_Wh)
        el_W = np.vectorize(calc_CT)(q_hot_Wh, Q_nom_W)

        # read reference results:
        config = configparser.ConfigParser()
        config.read(get_test_config_path())
        reference_results = json.loads(config.get('test_storage_tank', 'expected_results'))

        #comapare results with tests
        np.testing.assert_allclose(el_W, reference_results)


class TestCoolingTower(unittest.TestCase):
    def test_CT_partload_factor(self):
        """Make sure the partload factor is always positive."""
        partload_ratios = np.arange(0.0, 1.1, 0.1)
        partload_factors = np.vectorize(calc_CT_partload_factor)(partload_ratios)
        self.assertGreaterEqual(partload_factors.all(), 0.0)

    def test_calc_CT(self):
        """Make sure the calculation method remains the same."""
        q_hot_Wh = np.arange(0.0, 1E6, 1E5)
        Q_nom_W = max(q_hot_Wh)
        el_W = np.vectorize(calc_CT)(q_hot_Wh, Q_nom_W)

        config = configparser.ConfigParser()
        config.read(get_test_config_path())
        reference_results = json.loads(config.get('test_cooling_tower', 'expected_results'))
        np.testing.assert_allclose(el_W, reference_results)

def get_test_config_path():
    """return the path to the test data configuration file (``cea/tests/test_schedules.config``)"""
    return os.path.join(os.path.dirname(__file__), 'test_technologies.config')


if __name__ == "__main__":
    unittest.main()
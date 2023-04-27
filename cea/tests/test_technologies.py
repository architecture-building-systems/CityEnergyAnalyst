"""
Test cea.technologies
"""

import unittest
import numpy as np
import pandas as pd
import configparser
import json
import itertools
import os
import cea.inputlocator
import cea.examples
import cea.config
from cea.technologies.cooling_tower import calc_CT_partload_factor, calc_CT
from cea.technologies.storage_tank_pcm import Storage_tank_PCM


class TestColdPcmThermalStorage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # define folder location of reference case of CEA
        cls.locator = cea.inputlocator.ReferenceCaseOpenLocator()

        # importing default config of CEA
        cls.config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)

        # importing test config for this test
        cls.test_config = configparser.ConfigParser()
        cls.test_config.read(get_test_config_path())

        # extracting configuration for this test (input parameters and expected results)
        cls.size_storage_Wh = json.loads(cls.test_config.get("test_storage_tank", "size_storage_Wh"))  # the size of the storage to test
        cls.T_ambient_K = json.loads(cls.test_config.get("test_storage_tank", "T_ambient_K"))  # the outdoor temperature of the storage
        cls.days_to_test = json.loads(cls.test_config.get("test_storage_tank", "days_to_test"))  # the number of days to test the storage
        cls.charging_rate_per_hour_perc = json.loads(cls.test_config.get("test_storage_tank", "charging_fraction_per_hour_perc"))  # the rate of charge per hour as a function of the size
        cls.discharging_rate_per_hour_perc = json.loads(cls.test_config.get("test_storage_tank", "discharging_fraction_per_hour_perc"))  # the rate of discharge per hour as a function of the size
        cls.hourly_operation_schedule_day = json.loads(cls.test_config.get("test_storage_tank", "hourly_operation_schedule_day"))  # vector with tuples describing whether the storage is charging, balanced, or discharging and for how long. This is only for one day.
        cls.expected_results = json.loads(cls.test_config.get("test_storage_tank", "expected_results"))  # vector storing the results expected of the test
        cls.expected_results_costs = json.loads(cls.test_config.get("test_storage_tank", "expected_results_costs"))

        # getting the number of storage systems available
        cls.storage_properties = pd.read_excel(cls.locator.get_database_conversion_systems(), sheet_name="TES")
        cls.type_storage_list = cls.locator.get_database_conversion_systems_cold_thermal_storage_names()
        cls.type_storage = cls.type_storage_list[0]

    def test_cold_pcm_thermal_storage(self, checkResults=False):

        # initialize tank
        tank = Storage_tank_PCM(size_Wh=self.size_storage_Wh,
                                database_model_parameters=self.storage_properties,
                                T_ambient_K=self.T_ambient_K,
                                type_storage=self.type_storage)

        # prepare dataframe for testing
        data = pd.DataFrame({"Q_DailyStorage_gen_directLoad_W": np.zeros(self.days_to_test * 24),
                             "Q_DailyStorage_to_storage_W": np.zeros(self.days_to_test * 24),
                             "Q_DailyStorage_content_W": np.zeros(self.days_to_test * 24),
                             "T_DailyStorage_C": np.zeros(self.days_to_test * 24),
                             })

        # and input boundary conditions for the tank
        hours = list(range(self.days_to_test * 24))
        load = [self.charging_rate_per_hour_perc * self.size_storage_Wh] * self.days_to_test * 24
        unload = [self.discharging_rate_per_hour_perc * self.size_storage_Wh] * self.days_to_test * 24
        schedule = list(itertools.chain.from_iterable([[x[0]] * x[1] for x in self.hourly_operation_schedule_day] * self.days_to_test))

        # run simulation
        print("Initiating simulation....")
        for hour, x, y, z in zip(hours, load, unload, schedule):
            load_proposed_to_storage_Wh = x
            load_proposed_from_storage_Wh = y
            operation_mode = z
            if operation_mode == "charge":
                print("...Charging at hour {}...".format(hour))
                load_to_storage_Wh, new_storage_capacity_wh = tank.charge_storage(load_proposed_to_storage_Wh)
                data.loc[hour, "Q_DailyStorage_gen_directLoad_W"] = 0.0
                data.loc[hour, "Q_DailyStorage_to_storage_W"] = load_to_storage_Wh
                data.loc[hour, "Q_DailyStorage_content_W"] = new_storage_capacity_wh
            elif operation_mode == "discharge":
                print("...Discharging at hour {}...".format(hour))
                load_from_storage_Wh, new_storage_capacity_wh = tank.discharge_storage(
                    load_proposed_from_storage_Wh)
                data.loc[hour, "Q_DailyStorage_gen_directLoad_W"] = - load_from_storage_Wh
                data.loc[hour, "Q_DailyStorage_to_storage_W"] = 0.0
                data.loc[hour, "Q_DailyStorage_content_W"] = new_storage_capacity_wh
            else:
                print("...Balancing at hour {}...".format(hour))
                new_storage_capacity_wh = tank.balance_storage()
                data.loc[hour, "Q_DailyStorage_gen_directLoad_W"] = 0.0
                data.loc[hour, "Q_DailyStorage_to_storage_W"] = 0.0
                data.loc[hour, "Q_DailyStorage_content_W"] = new_storage_capacity_wh

            data.loc[hour, "T_DailyStorage_C"] = tank.T_tank_K - 273.0

        # calculate results to assert
        results = data.sum().values
        # Just for the result comparison - check assertion
        if checkResults:
            np.testing.assert_allclose(results, self.expected_results)

        return results, data, tank.description

    def test_cold_pcm_thermal_storage_costs(self, checkResults=False):
        # initialize tank
        tank = Storage_tank_PCM(size_Wh=self.size_storage_Wh,
                                database_model_parameters=self.storage_properties,
                                T_ambient_K=self.T_ambient_K,
                                type_storage=self.type_storage)
        Capex_a_storage_USD, Opex_fixed_storage_USD, Capex_total_USD = tank.costs_storage()

        # calculate results to assert
        results = [tank.V_tank_m3, Capex_a_storage_USD, Opex_fixed_storage_USD, Capex_total_USD]
        # Just for the result comparison - check assertion
        if checkResults:
            np.testing.assert_allclose(results, self.expected_results_costs)

        return results


class TestCoolingTower(unittest.TestCase):
    def test_CT_part_load_factor(self):
        """Make sure the part load factor is always positive."""
        part_load_ratios = np.arange(0.0, 1.1, 0.1)
        part_load_factors = np.vectorize(calc_CT_partload_factor)(part_load_ratios)
        self.assertGreaterEqual(part_load_factors.all(), 0.0)

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

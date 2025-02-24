"""
Test cea.optimization.slave.cooling_main.py, which calculates district cooling operation for an individual
of the genetic optimization algorithm and outputs the relevant objective functions.
"""

import unittest
import configparser
import os
import json
import numpy as np

import cea.inputlocator
import cea.config
import cea.optimization.preprocessing.preprocessing_main as preprocessing_main
import cea.optimization.distribution.network_optimization_features as network_optimization_features
import cea.optimization.slave_data
import cea.optimization.master.summarize_network as summarize_network
import cea.optimization.slave.cooling_main as cooling_main


class TestDistrictCooling(unittest.TestCase):
    # set debugging variable. Set to True if you wish to analyse details of the district cooling activation script
    debug = False

    @classmethod
    def setUpClass(cls):
        cls.test_config = configparser.ConfigParser()
        cls.test_config.read(os.path.join(os.path.dirname(__file__), 'test_district_cooling.config'))

    def setUp(self):
        # get locator and config variables for the reference case, which will also be used to test the
        # district cooling operation functions
        self.locator = cea.inputlocator.ReferenceCaseOpenLocator()
        self.config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)

        self.config.project = self.locator.project_path
        self.config.scenario = self.locator.scenario

        # assign all network feature variables used to evaluate district cooling operation (i.e. ground_temp)
        weather_file = self.locator.get_weather_file()
        self.weather_features = preprocessing_main.WeatherFeatures(weather_file)

        # assign all network feature variables used to evaluate district cooling operation
        DHN_exists = False
        DCN_exists = True
        self.network_features = network_optimization_features.NetworkOptimizationFeatures(DHN_exists,
                                                                                          DCN_exists,
                                                                                          self.locator)

        # assign all the variables used to define an individual (in the genetic optimization algorithm)
        # to the 'TestDistrictCooling' class and set them to the values specified in 'test_district_cooling.config'
        self.slave_variables = cea.optimization.slave_data.SlaveData()

        # GENERAL
        # Setting the slave variable debug variable equal to cls.debug allows testing of specific functionalities within
        # the cooling_main script
        self.slave_variables.debug = self.debug

        # DISTRICT COOLING
        # buildings connected
        self.slave_variables.num_total_buildings = \
            json.loads(self.test_config.get("input_district_cooling_network", "num_total_buildings"))
        self.slave_variables.number_of_buildings_district_scale_cooling = \
            json.loads(
                self.test_config.get("input_district_cooling_network", "number_of_buildings_district_scale_cooling"))
        self.slave_variables.DCN_barcode = \
            json.loads(self.test_config.get("input_district_cooling_network", "DCN_barcode"))
        self.slave_variables.building_names_cooling = \
            json.loads(self.test_config.get("input_district_cooling_network", "building_names_cooling"))

        # total cooling demand
        self.slave_variables.Q_cooling_nom_W = \
            json.loads(self.test_config.get("input_district_cooling_network", "Q_cooling_nom_W"))

        # Network
        self.slave_variables.DHN_exists = DHN_exists
        self.slave_variables.DCN_exists = DCN_exists
        self.slave_variables.DC_network_summary_individual = summarize_network.network_main(self.locator,
                                                                                            self.slave_variables.building_names_cooling,
                                                                                            self.weather_features.ground_temp,
                                                                                            self.slave_variables.num_total_buildings,
                                                                                            'DC',
                                                                                            self.slave_variables.DCN_barcode)

        # HEATING TECHNOLOGIES
        # data-centre source waste heat
        self.slave_variables.WasteServersHeatRecovery = \
            json.loads(self.test_config.get("input_heating_technologies", "WasteServersHeatRecovery"))

        # COOLING TECHNOLOGIES
        # NG-fired trigen
        self.slave_variables.NG_Trigen_on = \
            json.loads(self.test_config.get("input_cooling_technologies", "NG_Trigen_on"))
        self.slave_variables.NG_Trigen_ACH_size_W = \
            json.loads(self.test_config.get("input_cooling_technologies", "NG_Trigen_ACH_size_W"))
        self.slave_variables.NG_Trigen_CCGT_size_thermal_W = \
            json.loads(self.test_config.get("input_cooling_technologies", "NG_Trigen_CCGT_size_thermal_W"))
        self.slave_variables.NG_Trigen_CCGT_size_electrical_W = \
            json.loads(self.test_config.get("input_cooling_technologies", "NG_Trigen_CCGT_size_electrical_W"))

        # Water-source vapour compression chillers
        self.slave_variables.WS_BaseVCC_on = \
            json.loads(self.test_config.get("input_cooling_technologies", "WS_BaseVCC_on"))
        self.slave_variables.WS_BaseVCC_size_W = \
            json.loads(self.test_config.get("input_cooling_technologies", "WS_BaseVCC_size_W"))

        self.slave_variables.WS_PeakVCC_on = \
            json.loads(self.test_config.get("input_cooling_technologies", "WS_PeakVCC_on"))
        self.slave_variables.WS_PeakVCC_size_W = \
            json.loads(self.test_config.get("input_cooling_technologies", "WS_PeakVCC_size_W"))

        # Air-source vapour compression chiller
        self.slave_variables.AS_BaseVCC_on = \
            json.loads(self.test_config.get("input_cooling_technologies", "AS_BaseVCC_on"))
        self.slave_variables.AS_BaseVCC_size_W = \
            json.loads(self.test_config.get("input_cooling_technologies", "AS_BaseVCC_size_W"))

        self.slave_variables.AS_PeakVCC_on = \
            json.loads(self.test_config.get("input_cooling_technologies", "AS_PeakVCC_on"))
        self.slave_variables.AS_PeakVCC_size_W = \
            json.loads(self.test_config.get("input_cooling_technologies", "AS_PeakVCC_size_W"))

        self.slave_variables.AS_BackupVCC_on = \
            json.loads(self.test_config.get("input_cooling_technologies", "AS_BackupVCC_on"))
        self.slave_variables.AS_BackupVCC_size_W = \
            json.loads(self.test_config.get("input_cooling_technologies", "AS_BackupVCC_size_W"))

        # Storage Cooling
        self.slave_variables.Storage_cooling_on = \
            json.loads(self.test_config.get("input_storage", "Storage_cooling_on"))
        self.slave_variables.Storage_cooling_size_W = \
            json.loads(self.test_config.get("input_storage", "Storage_cooling_size_W"))

    def test_cooling_main(self):
        # run district cooling activation script (and calculate all the costs, capacities and energy demands)
        district_cooling_fixed_costs, \
        district_cooling_generation_dispatch, \
        district_cooling_electricity_requirements_dispatch, \
        district_cooling_fuel_requirements_dispatch, \
        district_cooling_heat_release, \
        district_cooling_capacity_installed = cooling_main.district_cooling_network(self.locator,
                                                                                    self.config,
                                                                                    self.slave_variables,
                                                                                    self.network_features,
                                                                                    self.weather_features)

        # aggregate dispatch curves to obtain annual values (simplifying the comparison of values)
        district_cooling_generation_dispatch = {k: v.sum() for k, v in district_cooling_generation_dispatch.items()}
        district_cooling_electricity_requirements_dispatch = \
            {k: v.sum() for k, v in district_cooling_electricity_requirements_dispatch.items()}
        district_cooling_fuel_requirements_dispatch = \
            {k: v.sum() for k, v in district_cooling_fuel_requirements_dispatch.items()}
        district_cooling_heat_release = {k: v.sum() for k, v in district_cooling_heat_release.items()}

        # fetch stored data for comparison
        expected_district_cooling_fixed_costs = \
            json.loads(self.test_config.get("output_expected", "expected_district_cooling_fixed_costs"))
        expected_district_cooling_generation_dispatch = \
            json.loads(self.test_config.get("output_expected", "expected_district_cooling_generation_dispatch"))
        expected_district_cooling_electricity_requirements_dispatch = \
            json.loads(
                self.test_config.get("output_expected", "expected_district_cooling_electricity_requirements_dispatch"))
        expected_district_cooling_fuel_requirements_dispatch = \
            json.loads(self.test_config.get("output_expected", "expected_district_cooling_fuel_requirements_dispatch"))
        expected_district_cooling_heat_release = \
            json.loads(self.test_config.get("output_expected", "expected_district_cooling_heat_release"))
        expected_district_cooling_capacity_installed = \
            json.loads(self.test_config.get("output_expected", "expected_district_cooling_capacity_installed"))

        # perform unit tests
        test_value_dictionaries = [district_cooling_fixed_costs,
                                   district_cooling_generation_dispatch,
                                   district_cooling_electricity_requirements_dispatch,
                                   district_cooling_fuel_requirements_dispatch,
                                   district_cooling_heat_release,
                                   district_cooling_capacity_installed]

        expected_value_dictionaries = [expected_district_cooling_fixed_costs,
                                       expected_district_cooling_generation_dispatch,
                                       expected_district_cooling_electricity_requirements_dispatch,
                                       expected_district_cooling_fuel_requirements_dispatch,
                                       expected_district_cooling_heat_release,
                                       expected_district_cooling_capacity_installed]

        for test_value_dict, expected_value_dict in zip(test_value_dictionaries, expected_value_dictionaries):
            test_values = []
            expected_values = []
            for key in test_value_dict.keys():
                test_values.append(test_value_dict[key])
                expected_values.append(expected_value_dict[key])
            if self.slave_variables.debug is True:
                print(test_values)
                print(expected_values)
            np.testing.assert_allclose(test_values, expected_values)


if __name__ == "__main__":
    unittest.main()

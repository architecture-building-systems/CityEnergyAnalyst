"""Test the cea.config.Configuration()"""

import unittest
import pickle
import os
import tempfile
import cea.config


class TestConfiguration(unittest.TestCase):
    def test_can_be_pickled(self):
        config = cea.config.Configuration()
        config = pickle.loads(pickle.dumps(config))
        self.assertIsNotNone(config)

    def test_changing_scenario(self):
        config = cea.config.Configuration()
        config.scenario = os.path.dirname(__file__)
        self.assertEquals(config.scenario, config.general.scenario)

    def test_pickling_parameters(self):
        config = cea.config.Configuration()
        config.scenario = os.path.dirname(__file__)
        config = pickle.loads(pickle.dumps(config))
        self.assertEquals(config.scenario, config.general.scenario)
        self.assertEquals(config.scenario, os.path.dirname(__file__))

    def test_update_parameter_value(self):
        config = cea.config.Configuration()
        config.general.parameters['multiprocessing'].set(False)
        self.assertEquals(config.multiprocessing, False)
        config.general.parameters['multiprocessing'].set(True)
        self.assertEquals(config.multiprocessing, True)

    def test_update_parameter_values_after_pickling(self):
        config = cea.config.Configuration()
        config.general.parameters['multiprocessing'].set(False)
        config = pickle.loads(pickle.dumps(config))
        self.assertEquals(config.multiprocessing, False)
        config.general.parameters['multiprocessing'].set(True)
        config = pickle.loads(pickle.dumps(config))
        self.assertEquals(config.multiprocessing, True)

    def test_applying_parameters(self):
        config = cea.config.Configuration()
        scenario = os.path.normpath(os.path.join(tempfile.gettempdir().replace('\\', '/'), 'baseline'))
        if not os.path.exists(scenario):
            os.mkdir(scenario)
        config.apply_command_line_args(['--scenario', scenario], ['general'])
        self.assertEquals(config.scenario, scenario)
        self.assertEquals(config.scenario, config.general.scenario)
        config = pickle.loads(pickle.dumps(config))
        self.assertEquals(config.scenario, config.general.scenario)

    def test_setting_weather(self):
        config = cea.config.Configuration()
        self.assertEquals(config.weather, config.general.weather)
        config.weather = 'Brussels_1990_2010_TMY'
        self.assertEquals(config.weather, config.general.weather)
        self.assert_(config.weather.endswith('Brussels_1990_2010_TMY.epw'), config.weather)

    def test_setting_weather_pickling(self):
        config = cea.config.Configuration()
        self.assertEquals(config.weather, config.general.weather)
        config.weather = 'Brussels_1990_2010_TMY'
        config = pickle.loads(pickle.dumps(config))
        self.assertEquals(config.weather, config.general.weather)
        self.assert_(config.weather.endswith('Brussels_1990_2010_TMY.epw'))

    def test_weather_apply_parameters(self):
        config = cea.config.Configuration()
        self.assertEquals(config.weather, config.general.weather)
        config.apply_command_line_args(['--weather', 'Brussels_1990_2010_TMY'], ['general'])
        self.assertEquals(config.weather, config.general.weather)
        self.assert_(config.weather.endswith('Brussels_1990_2010_TMY.epw'))
        config = pickle.loads(pickle.dumps(config))
        self.assertEquals(config.weather, config.general.weather)

    def test_weather_apply_parameters_pickle_first(self):
        config = cea.config.Configuration()
        self.assertEquals(config.weather, config.general.weather)
        config = pickle.loads(pickle.dumps(config))
        config.apply_command_line_args(['--weather', 'Brussels_1990_2010_TMY'], ['general'])
        self.assertEquals(config.weather, config.general.weather)
        self.assert_(config.weather.endswith('Brussels_1990_2010_TMY.epw'))
        self.assertEquals(config.weather, config.general.weather)


if __name__ == "__main__":
    unittest.main()
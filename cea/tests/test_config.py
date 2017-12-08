"""Test the cea.config.Configuration()"""

import unittest
import pickle
import os
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
        config.general.parameters['scenario'].set('C:/test')
        self.assertEquals(config.scenario, r'C:\test')

    def test_update_parameter_values_after_pickling(self):
        config = cea.config.Configuration()
        config.general.parameters['scenario'].set('C:/test')
        config = pickle.loads(pickle.dumps(config))
        self.assertEquals(config.scenario, r'C:\test')

    def test_applying_parameters(self):
        config = cea.config.Configuration()
        config.apply_command_line_args(['--scenario', 'C:/test'], ['general'])
        self.assertEquals(config.scenario, r'C:\test')
        self.assertEquals(config.scenario, config.general.scenario)
        self.assertEquals(config.scenario, config.general.scenario)
        config = pickle.loads(pickle.dumps(config))
        config.scenario = 'foo'
        self.assertEquals(config.scenario, config.general.scenario)

    def test_setting_weather(self):
        config = cea.config.Configuration()
        self.assertEquals(config.weather, config.general.weather)
        config.weather = 'Brussels'
        self.assertEquals(config.weather, config.general.weather)
        self.assert_(config.weather.endswith('Brussels.epw'), config.weather)

    def test_setting_weather_pickling(self):
        config = cea.config.Configuration()
        self.assertEquals(config.weather, config.general.weather)
        config.weather = 'Brussels'
        config = pickle.loads(pickle.dumps(config))
        self.assertEquals(config.weather, config.general.weather)
        self.assert_(config.weather.endswith('Brussels.epw'))

    def test_weather_apply_parameters(self):
        config = cea.config.Configuration()
        self.assertEquals(config.weather, config.general.weather)
        config.apply_command_line_args(['--weather', 'Brussels'], ['general'])
        self.assertEquals(config.weather, config.general.weather)
        self.assert_(config.weather.endswith('Brussels.epw'))
        config = pickle.loads(pickle.dumps(config))
        self.assertEquals(config.weather, config.general.weather)

    def test_weather_apply_parameters_pickle_first(self):
        config = cea.config.Configuration()
        self.assertEquals(config.weather, config.general.weather)
        config = pickle.loads(pickle.dumps(config))
        config.apply_command_line_args(['--weather', 'Brussels'], ['general'])
        self.assertEquals(config.weather, config.general.weather)
        self.assert_(config.weather.endswith('Brussels.epw'))
        self.assertEquals(config.weather, config.general.weather)

if __name__ == "__main__":
    unittest.main()
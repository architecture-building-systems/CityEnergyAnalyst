"""Test the cea.config.Configuration()"""

import unittest
import cea.config


class TestConfiguration(unittest.TestCase):
    def test_parameter_names_are_unique(self):
        config = cea.config.Configuration()
        parameter_set = set()
        for section in config._sections.values():
            for parameter in section._parameters.values():
                self.assertNotIn(parameter.name, parameter_set)
                parameter_set.add(parameter.name)

    def test_can_be_pickled(self):
        config = cea.config.Configuration()
        import pickle
        config = pickle.loads(pickle.dumps(config))
        self.assertIsNotNone(config)

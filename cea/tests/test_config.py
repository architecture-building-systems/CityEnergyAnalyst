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
        self.assertEqual(config.scenario, config.general.scenario)

    def test_pickling_parameters(self):
        config = cea.config.Configuration()
        config.scenario = os.path.dirname(__file__)
        config = pickle.loads(pickle.dumps(config))
        self.assertEqual(config.scenario, config.general.scenario)
        self.assertEqual(config.scenario, os.path.dirname(__file__))

    def test_update_parameter_value(self):
        config = cea.config.Configuration()
        config.general.parameters['multiprocessing'].set(False)
        self.assertEqual(config.multiprocessing, False)
        config.general.parameters['multiprocessing'].set(True)
        self.assertEqual(config.multiprocessing, True)

    def test_update_parameter_values_after_pickling(self):
        config = cea.config.Configuration()
        config.general.parameters['multiprocessing'].set(False)
        config = pickle.loads(pickle.dumps(config))
        self.assertEqual(config.multiprocessing, False)
        config.general.parameters['multiprocessing'].set(True)
        config = pickle.loads(pickle.dumps(config))
        self.assertEqual(config.multiprocessing, True)

    def test_applying_parameters(self):
        config = cea.config.Configuration()
        scenario = os.path.normpath(os.path.join(tempfile.gettempdir().replace('\\', '/'), 'baseline'))
        if not os.path.exists(scenario):
            os.mkdir(scenario)
        config.apply_command_line_args(['--scenario', scenario], ['general'])
        self.assertEqual(config.scenario, scenario)
        self.assertEqual(config.scenario, config.general.scenario)
        config = pickle.loads(pickle.dumps(config))
        self.assertEqual(config.scenario, config.general.scenario)

    def test_decode_fileparameter(self):
        config = cea.config.Configuration()
        scenario = config.general.scenario
        expected_output = f"{scenario}/inputs/building-geometry/zone.shp"
        self.assertEqual(os.path.normcase(os.path.expanduser(config.create_new_scenario.zone)),
                         os.path.normcase(os.path.expanduser(expected_output)))


if __name__ == "__main__":
    unittest.main()
"""Test the cea.config.Configuration()"""




import unittest
import pickle
import os
import tempfile
import cea.config
import cea.inputlocator


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
        expected_output = f"{scenario}/outputs/trace_inputlocator.output.yml"
        self.assertEqual(os.path.normcase(os.path.expanduser(config.trace_inputlocator.meta_output_file)),
                         os.path.normcase(os.path.expanduser(expected_output)))

    def test_choice_parameter_is_single_choice(self):
        config = cea.config.Configuration()
        parameter = config.get_parameter('test:type')

        self.assertIsInstance(parameter, cea.config.ChoiceParameterBase)
        self.assertIsInstance(parameter, cea.config.ChoiceParameter)
        self.assertNotIsInstance(parameter, cea.config.MultiChoiceParameter)

    def test_multi_choice_parameter_is_multi_choice(self):
        config = cea.config.Configuration()
        parameter = config.get_parameter('database-helper:databases')

        self.assertIsInstance(parameter, cea.config.ChoiceParameterBase)
        self.assertIsInstance(parameter, cea.config.MultiChoiceParameter)

    def test_multi_choice_specialisations_are_multi_choice(self):
        config = cea.config.Configuration()

        thermal_network_parameter = config.get_parameter('thermal-network:network-name')
        solar_parameter = config.get_parameter('result-summary:solar-technologies')

        self.assertIsInstance(thermal_network_parameter, cea.config.NetworkLayoutMultiChoiceParameter)
        self.assertIsInstance(thermal_network_parameter, cea.config.MultiChoiceParameter)
        self.assertIsInstance(solar_parameter, cea.config.MultiChoiceParameter)

    def test_export_folder_name_rejects_path_traversal(self):
        # The value is joined into scenario/export/results/{name}-{timestamp}
        # (InputLocator.get_export_results_summary_folder) -- path separators must be
        # rejected so it cannot escape the scenario's export folder.
        config = cea.config.Configuration()
        parameter = config.get_parameter('result-summary:folder-name-to-save-exported-results')
        self.assertIsInstance(parameter, cea.config.ExportFolderNameParameter)

        with self.assertRaises(ValueError):
            parameter.encode('../../escape')
        with self.assertRaises(ValueError):
            parameter.decode('../../escape')

        self.assertEqual(parameter.encode('my-summary'), 'my-summary')
        self.assertEqual(parameter.encode(''), '')
        self.assertEqual(parameter.decode(''), '')

    def test_whatif_choice_parameter_filters_by_every_mode(self):
        """WhatIfNameChoiceParameter (the single-choice what-if selector) used to filter
        `_choices` only for mode='final_energy' -- every other mode returned every
        outputs/data/analysis/ subfolder unfiltered, regardless of whether that mode's
        output actually existed. Its sibling WhatIfNameMultiChoiceParameter already
        filtered correctly for all four modes; both now share
        WhatIfNameChoicesMixin._mode_output_path_fn. Not currently declared by any
        built-in tool (only the multi-choice variant is), but constructible directly --
        e.g. for a plugin -- so it's tested directly rather than through a config section.
        """
        config = cea.config.Configuration()
        scenario = os.path.join(tempfile.mkdtemp(), 'baseline')
        os.makedirs(scenario, exist_ok=True)
        config.scenario = scenario
        locator = cea.inputlocator.InputLocator(scenario)

        # 'complete': has every mode's output file. 'partial': the analysis folder
        # exists (a what-if run happened) but none of the mode-specific outputs do.
        for output_file_fn in (
            locator.get_final_energy_buildings_file,
            locator.get_emissions_whatif_buildings_file,
            locator.get_costs_whatif_buildings_file,
            locator.get_heat_rejection_whatif_buildings_file,
        ):
            path = output_file_fn('complete')
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, 'w').close()
        os.makedirs(locator.get_analysis_folder('partial'), exist_ok=True)

        # [result-summary] declares one WhatIfNameMultiChoiceParameter per mode; reuse
        # those section:name pairs to construct the singular class directly -- `.mode`
        # resolves from `{section}:{name}.mode` in default.config regardless of the
        # `.type` that was actually declared there.
        section = config.sections['result-summary']
        mode_by_param_name = {
            'what-if-name-final-energy': 'final_energy',
            'what-if-name-emissions': 'emissions',
            'what-if-name-costs': 'costs',
            'what-if-name-heat-rejection': 'heat_rejection',
        }
        for param_name, expected_mode in mode_by_param_name.items():
            parameter = cea.config.WhatIfNameChoiceParameter(param_name, section, config)
            self.assertEqual(parameter.mode, expected_mode)
            self.assertEqual(parameter._choices, ['complete'], f"mode={expected_mode}")


if __name__ == "__main__":
    unittest.main()
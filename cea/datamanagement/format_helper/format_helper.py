"""
Main script of the formate helper that activates the verification and migration as needed.

"""

import os
import cea.config
import time
from cea.datamanagement.format_helper.cea4_verify import cea4_verify, print_verification_results_4
from cea.datamanagement.format_helper.cea4_migrate import migrate_cea3_to_cea4

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def exec_cea_format_helper(config, cea_scenario):
    # auto-migrate from CEA-3 to CEA-4
    bool_migrate = config.format_helper.migrate_from_cea_3
    scenario_name = os.path.basename(cea_scenario)

    if not bool_migrate:
        # subprocess.run(['cea', 'cea4_migrate', '--scenario', cea_scenario], env=my_env, check=True,capture_output=True)
        dict_missing = cea4_verify(cea_scenario, print_results=True)
        print_verification_results_4(scenario_name, dict_missing)

    else:
        # subprocess.run(['cea', 'cea4_verify', '--scenario', cea_scenario], env=my_env, check=True, capture_output=True)
        migrate_cea3_to_cea4(cea_scenario)
        dict_missing = cea4_verify(cea_scenario)
        print_verification_results_4(scenario_name, dict_missing)


## --------------------------------------------------------------------------------------------------------------------
## Main function
## --------------------------------------------------------------------------------------------------------------------

def main(config):
    """
    Batch processing all selected scenarios under a project.

    :param config: the configuration object to use
    :type config: cea.config.Configuration
    :return:
    """

    # Start the timer
    t0 = time.perf_counter()

    assert os.path.exists(config.general.project), 'input file not found: %s' % config.general.project

    project_path = config.general.project
    scenarios_list = config.format_helper.scenarios_to_verify_and_migrate

    print('+' * 60)
    print(f'Format Helper is batch-processing the data verification and migration for Scenarios: {scenarios_list}.')

    # Loop over one or all selected scenarios under the project
    for scenario in scenarios_list:
        # Ignore hidden directories
        if scenario.startswith('.') or os.path.isfile(os.path.join(project_path, scenario)):
            continue

        # Print: Start
        div_len = 37 - len(scenario)
        print('+' * 60)
        print("-" * 1 + ' Scenario: {scenario} '.format(scenario=scenario) + "-" * div_len)

        cea_scenario = os.path.join(project_path, scenario)
        # executing CEA commands
        exec_cea_format_helper(config, cea_scenario)

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('+' * 60)
    print(
        'The entire batch processing of data format verification (and migration) for CEA-4 is now completed - time elapsed: %.2f seconds' % time_elapsed)


if __name__ == '__main__':
    main(cea.config.Configuration())

"""
Main script of the formate helper that activates the verification and migration as needed.

"""

import cea.config
import os
import subprocess
import sys
import cea.config
import time

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


## --------------------------------------------------------------------------------------------------------------------
## Get the environment and set up the subprocess
## --------------------------------------------------------------------------------------------------------------------


# adding CEA to the environment
# Fix for running in PyCharm for users using micromamba
my_env = os.environ.copy()
my_env['PATH'] = f"{os.path.dirname(sys.executable)}:{my_env['PATH']}"

def exec_cea_format_helper(config, cea_scenario):
    # auto-migrate from CEA-3 to CEA-4
    bool_migrate = config.format_helper.migrate_from_cea_3
    if bool_migrate:
        subprocess.run(['cea', 'cea4_migrate', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)
    else:
        subprocess.run(['cea', 'cea4_verify', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)


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

    assert os.path.exists(config.general.project), 'input file not found: %s' % config.project

    project_path = config.general.project
    scenario_name = config.general.scenario_name
    scenarios_list = config.format_helper.scenarios_to_verify_and_migrate
    bool_migrate = config.format_helper.migrate_from_cea_3

    # Loop over one or all selected scenarios under the project
    for scenario in scenarios_list:
        # Ignore hidden directories
        if scenario.startswith('.') or os.path.isfile(os.path.join(project_path, scenario)):
            continue

        cea_scenario = os.path.join(project_path, scenario)
        if bool_migrate:
            print(f'Executing CEA input data verification and migration on {cea_scenario}.')
        else:
            print(f'Executing CEA input data verification on {cea_scenario}.')

        try:
            # executing CEA commands
            exec_cea_format_helper(config, cea_scenario)
        except subprocess.CalledProcessError as e:
            print(f"CEA input data verification and migration failed at `{scenario_name}`")
            err_msg = e.stderr
            if err_msg is not None:
                print(err_msg.decode())
            raise e

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire batch processing of data format verification (and migration) for CEA-4 is now completed - time elapsed: %d.2 seconds' % time_elapsed)


if __name__ == '__main__':
    main(cea.config.Configuration())

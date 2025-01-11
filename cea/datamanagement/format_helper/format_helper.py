"""
Main script of the formate helper that activates the verification and migration as needed.

"""

import cea.inputlocator
import os
import cea.config
import time
import geopandas as gpd


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


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
    scenarios_list = config.batch_process_workflow.scenarios_to_simulate

    # Loop over one or all scenarios under the project
    for scenario in scenarios_list:
        # Ignore hidden directories
        if scenario.startswith('.') or os.path.isfile(os.path.join(project_path, scenario)):
            continue

        cea_scenario = os.path.join(project_path, scenario)
        print(f'Executing CEA simulations on {cea_scenario}.')
        try:
            # executing CEA commands
            exec_cea_commands(config, cea_scenario)
        except subprocess.CalledProcessError as e:
            print(f"CEA simulation for scenario `{scenario_name}` failed at script: {e.cmd[1]}")
            err_msg = e.stderr
            if err_msg is not None:
                print(err_msg.decode())
            raise e

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire batch processing sequence is now completed - time elapsed: %d.2 seconds' % time_elapsed)


if __name__ == '__main__':
    main(cea.config.Configuration())

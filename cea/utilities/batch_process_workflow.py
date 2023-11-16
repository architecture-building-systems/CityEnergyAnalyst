"""
Batch processing CEA commands over all scenarios in a project.
This is a first exploration for the ETH MiBS IDP 2023.
"""

import os
import subprocess
import cea.config
import time

__author__ = "Zhongming Shi, Mathias Niffeler"
__copyright__ = "Copyright 2023, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Mathias Niffeler, Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main(config):
    """
    Batch processing all scenarios under a project.

    :param config: the configuration object to use
    :type config: cea.config.Configuration
    :return:
    """


    # Start the timer
    t0 = time.perf_counter()

    assert os.path.exists(config.general.project), 'input file not found: %s' % config.project

    project_path = config.general.project
    scenario_path = config.general.scenario

    # adding CEA to the environment
    my_env = os.environ.copy()
    # my_env['PATH'] = f"/Users/zshi/micromamba/envs/cea/bin:{my_env['PATH']}"  #todo: un-hard-coded the path for PyCharm, and it is working on CEA Dashboard now.

    #loop over all scenarios under the project
    for filename in os.listdir(project_path):
        cea_scenario = os.path.join(project_path, '{scenario}'.format(scenario=filename))
        print('Executing CEA simulations on {cea_scenario}.'.format(cea_scenario=cea_scenario))
        # executing CEA commands
        subprocess.run(['cea', 'workflow', '--workflow', 'idp-23-md', '--scenario', '{cea_scenario}'.format(cea_scenario=cea_scenario)], env=my_env)

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire batch processing sequence is now completed - time elapsed: %d.2 seconds' % time_elapsed)

if __name__ == '__main__':
    main(cea.config.Configuration())

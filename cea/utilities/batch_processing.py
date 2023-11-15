"""
Batch processing CEA commands over all scenarios in a project.
This is a first exploration for the ETH MiBS IDP 2023.
"""

import os
import subprocess

__author__ = "Mathias Niffeler, Zhongming Shi"
__copyright__ = "Copyright 2023, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Mathias Niffeler, Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


#project directory, for example, /Users/zshi/Dropbox/CEA2/batch
cea_project = r'/Users/zshi/Dropbox/CEA2/batch'

#loop over all scenarios under the project
for filename in os.listdir(cea_project)[1:]:
    cea_scenario = os.path.join(cea_project, '{scenario}'.format(scenario=filename))
    print('Executing CEA simulations on {cea_scenario}.'.format(cea_scenario=cea_scenario))

    # adding CEA to the environment
    my_env = os.environ.copy()
    my_env['PATH'] = f"/Users/zshi/micromamba/envs/cea/bin:{my_env['PATH']}"  #todo: un-hard-coded the path

    # executing CEA commands
    subprocess.run(['cea', 'demand', '--scenario', '{cea_scenario}'.format(cea_scenario=cea_scenario)], env=my_env)

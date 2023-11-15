"""
Batch processing CEA commands over all scenarios in a project.
"""

import os
import pandas as pd
import cea.config
import cea.inputlocator
import subprocess


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2023, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


#project directory
cea_project = r'/Users/zshi/Dropbox/CEA2/batch'

#loop over all scenarios under the project
for filename in os.listdir(cea_project):
    cea_scenario = os.path.join(cea_project, '{scenario}'.format(scenario=filename))
    print('Executing CEA simulations on {cea_scenario}.'.format(cea_scenario=cea_scenario))

    # subprocess.run(["git", cea_scenario, f":cea/datamanagement/archetypes_mapper.py"])
    # subprocess.run(['ls','sensitivity_analysis_sampler.py'])


     # callthecommandhere(blablahbla, filename, foo)

"""
===========================
Clustering
This script clusters typical days for a building and for a

===========================
J. Fonseca  script development          27.10.16


"""
from __future__ import division

import pandas as pd
import numpy as np

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def clustering(locator, building_name, building_load, how):

    # import data
    data = pd.read_csv(locator.get_demand_results_file(building_name))[building_load]
    print data
   if how is 'daily': # cluster daily



def run_as_script():
    import cea.globalvar as gv
    import cea.inputlocator as inputlocator
    gv = gv.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    clustering(locator, building_name = 'B01', building_load = 'Qhsf_kWh', how='daily')

if __name__ == '__main__':
    run_as_script()
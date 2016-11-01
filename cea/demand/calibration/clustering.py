"""
===========================
Clustering
This script clusters typical days for a building
using SAX method for timeseries.

===========================
J. Fonseca  script development          27.10.16


"""
from __future__ import division

import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def clustering(locator, gv, building_name, building_load):
    t0 = time.clock()
    # import data
    data = pd.read_csv(locator.get_demand_results_file(building_name), usecols=['DATE', building_load], index_col='DATE')
    data.set_index(pd.to_datetime(data.index), inplace=True)

    # transform into arrays of 24h
    groups = data.groupby(data.index.dayofyear)
    arrays = [group[1][building_load] for group in groups]
    data['day'] = data.index.dayofweeky
    print data.loc[data.day <= 4].loc[(data != 0).any(1)][building_load].hist(bins=10, figsize=(15, 5))
    #data2.plot()
    #plt.show()


    gv.log('done - time elapsed: %(time_elapsed).2f seconds', time_elapsed=time.clock() - t0)

def run_as_script():
    import cea.globalvar as gv
    import cea.inputlocator as inputlocator
    gv = gv.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    clustering(locator=locator, gv=gv, building_name = 'B01', building_load = 'Ef_kWh')

if __name__ == '__main__':
    run_as_script()
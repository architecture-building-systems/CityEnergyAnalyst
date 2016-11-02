"""
===========================
Clustering
This script clusters typical days for a building
using SAX method for timeseries.

===========================
J. Fonseca  script development          27.10.16


"""
from __future__ import division

from cea.demand.calibration.sax import SAX
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
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def clustering(locator, gv, wordSize, alphabetSize, building_name, building_load):
    t0 = time.clock()

    # import data
    data = pd.read_csv(locator.get_demand_results_file(building_name), usecols=['DATE', building_load], index_col='DATE')
    data.set_index(pd.to_datetime(data.index), inplace=True)

    # transform into dicts where key = day and value = 24 h array
    groups = data.groupby(data.index.dayofyear)
    arrays = [group[1][building_load].values  for group in groups]

    # calculate and store into string dictionary
    s = SAX(wordSize, alphabetSize)
    pieces = [s.to_letter_rep(array)[0] for array in arrays]
    #data = pd.DataFrame((x + '_MWhyr', [tsd[x].sum() / 1000000) for piece in pieces)
    print pieces[100:]

    plt.show()
    print

    gv.log('done - time elapsed: %(time_elapsed).2f seconds', time_elapsed=time.clock() - t0)

def run_as_script():
    """"""
    import cea.globalvar as gv
    import cea.inputlocator as inputlocator
    gv = gv.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    clustering(locator=locator, gv=gv, wordSize=8, alphabetSize=7, building_name = 'B01', building_load = 'Qhsf_kWh')

if __name__ == '__main__':
    run_as_script()
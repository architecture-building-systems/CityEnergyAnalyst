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
from sklearn.metrics import silhouette_score
from sklearn import metrics
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
    data['day'] = data.index.dayofyear

    # transform into dicts where key = day and value = 24 h array
    groups = data.groupby(data.day)
    arrays = [group[1][building_load].values for group in groups]#[[group[0], group[1][building_load].values] for group in groups]

    # calculate sax alphabet per every day
    alphabets = range(3,30)
    for alphabetSize in alphabets:
        s = SAX(wordSize, alphabetSize)
        sax = [s.to_letter_rep(array)[0] for array in arrays]
        silhouette_avg = silhouette_score(arrays, sax)
        calinski = metrics.calinski_harabaz_score(arrays, sax)
        print alphabetSize, silhouette_avg, calinski

    wordsizes = [3, 6, 8, 12]
    alphabetSize = 4
    for wordSize in wordsizes:
        s = SAX(wordSize, alphabetSize)
        sax = [s.to_letter_rep(array)[0] for array in arrays]
        silhouette_avg = silhouette_score(arrays, sax)
        calinski = metrics.calinski_harabaz_score(arrays, sax)
        print wordSize, silhouette_avg, calinski

    # calculate dict with data per hour for the whole year and create groups per pattern
    # array_hours = range(24)
    # array_days = range(365)
    # arrays_T = [list(x) for x in zip(*arrays)]
    # dict_data = dict((group,x) for group, x in zip(array_hours, arrays_T))
    # dict_data.update({'sax': sax, 'day': array_days})
    #
    # # create group by pattern
    # grouped_sax = pd.DataFrame(dict_data).groupby('sax')
    #
    # for name, group in grouped_sax:
    #     transpose = group.T.drop(['sax', 'day'], axis=0)
    #     transpose.plot()
    #     plt.show()


    # print grouped_sax.describe()



    gv.log('done - time elapsed: %(time_elapsed).2f seconds', time_elapsed=time.clock() - t0)

def run_as_script():
    """"""
    import cea.globalvar as gv
    import cea.inputlocator as inputlocator
    gv = gv.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    clustering(locator=locator, gv=gv, wordSize=6, alphabetSize=4, building_name = 'B01', building_load = 'Qhsf_kWh')

if __name__ == '__main__':
    run_as_script()
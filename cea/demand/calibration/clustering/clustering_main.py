# -*- coding: utf-8 -*-
"""
===========================
Clustering
This script clusters typical days for a building
using SAX method for timeseries.

===========================
J. Fonseca  script development          27.10.16


"""
from __future__ import division

import time

import matplotlib.pyplot as plt
import pandas as pd

from cea.demand.calibration.clustering.sax import SAX
from cea.demand.calibration.clustering.sax_optimization import SAX_opt, print_pareto

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def clustering(locator, gv, wordSize, alphabetSize, building_name, building_load, optimize, plot_clusters):
    """
    Function to cluster different days of the year following the SAX method (see class for more info)
    :param locator: locator class
    :param gv: global variables class
    :param wordSize: estimated wordsize, after optimization
    :param alphabetSize: estimated alphabet size. after optimization
    :param building_name: building name to make the cluster of its time series
    :param building_load: name of time_series to use form the building demand i.e., Qhsf_kWh, Qcsf_kWh, Qwwf_kWh etc.
    :param optimize: Boolan: true to run the optimization. you will first run the optimization,
    choose the wordsize and alphabetsize. from there, run the program with the optimize = flase
    :param plot_clusters: when optimize if false, decide weather you would like to see the data in each defined cluster
    :return: timeseries per cluster  in locator.get_clustering_calibration_file(cluster_name). .csv file
        dataframe with ID of every cluster per day of the year in locator.get_clustering_calibration_sax_names_file()

    """
    t0 = time.clock()

    # import data
    data = pd.read_csv(locator.get_demand_results_file(building_name),
                       usecols=['DATE', building_load], index_col='DATE')
    data.set_index(pd.to_datetime(data.index), inplace=True)
    data['day'] = data.index.dayofyear

    # transform into dicts where key = day and value = 24 h array
    groups = data.groupby(data.day)
    arrays = [group[1][building_load].values for group in groups]

    # set optimization problem for wordzise and alpha number
    if optimize:
        pop, halloffame, paretofrontier, stats = SAX_opt(locator, arrays, time_series_len=24, BOUND_LOW = 4,
                                                         BOUND_UP = 24, NGEN = 50, MU = 8, CXPB = 0.9,
                                                         start_gen = None)
        if plot_clusters:
            print_pareto(pop, paretofrontier)
    else:
        s = SAX(wordSize, alphabetSize)
        sax = [s.to_letter_rep(array)[0] for array in arrays]

        # calculate dict with data per hour for the whole year and create groups per pattern
        array_hours = range(24)
        array_days = range(365)
        arrays_T = [list(x) for x in zip(*arrays)]
        dict_data = dict((group, x) for group, x in zip(array_hours, arrays_T))
        dict_data.update({'sax': sax, 'day': array_days})

        # save all names and days of occurrence of each profile
        df = pd.DataFrame(dict_data)
        df[['sax', 'day']].to_csv(locator.get_calibration_clusters_names())

        # save individual results to disk # create group by pattern
        grouped_sax = df.groupby('sax')
        for name, group in grouped_sax:
            result = group.T.drop(['sax', 'day'], axis=0)
            result.to_csv(locator.get_calibration_cluster(name))
            if plot_clusters:
                result.plot()
                plt.show()
        print

    gv.log('done - time elapsed: %(time_elapsed).2f seconds', time_elapsed=time.clock() - t0)

def run_as_script():
    import cea.globalvar as gv
    import cea.inputlocator as inputlocator
    gv = gv.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    clustering(locator=locator, gv=gv, wordSize=4, alphabetSize=24, building_name='B01', building_load='Qhsf_kWh',
               optimize=True, plot_clusters = True)

if __name__ == '__main__':
    run_as_script()

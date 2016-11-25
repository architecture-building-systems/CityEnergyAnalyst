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


def clustering(locator, gv, word_size, alphabet_size, building_name, building_load, optimize, plot_clusters):
    """
    Function to cluster different days of the year following the SAX method (see class for more info)
    :param locator: locator class
    :param gv: global variables class
    :param word_size: estimated wordsize, after optimization
    :param alphabet_size: estimated alphabet size. after optimization
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
    list_of_timeseries = [group[1][building_load].values for group in groups]


    if optimize:
        # set optimization problem for wordzise and alpha number
        pop, hall_of_fame, pareto_frontier, stats = SAX_opt(locator, list_of_timeseries, time_series_len=24, BOUND_LOW = 4,
                                                         BOUND_UP = 24, NGEN = 50, MU = 8, CXPB = 0.9,
                                                         start_gen = None)
        if plot_clusters:
            print_pareto(pop, pareto_frontier)
    else:
        # calculate sax for timesieries data
        s = SAX(word_size, alphabet_size)
        sax = [s.to_letter_representation(x)[0] for x in list_of_timeseries]

        # calculate dict with data per hour for the whole year and create groups per pattern
        hours_of_day = range(24)
        days_of_year = range(365)
        list_of_timeseries_transposed = [list(x) for x in zip(*list_of_timeseries)]
        dict_data = dict((group, x) for group, x in zip(hours_of_day, list_of_timeseries_transposed))
        dict_data.update({'sax': sax, 'day': days_of_year})

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
    clustering(locator=locator, gv=gv, word_size=4, alphabet_size=24, building_name='B01', building_load='Qhsf_kWh',
               optimize=True, plot_clusters = True)

if __name__ == '__main__':
    run_as_script()

# -*- coding: utf-8 -*-
"""
Clustering
This script clusters typical days for a building
using SAX method for timeseries.

J. Fonseca  script development          27.10.16

"""
from __future__ import division

import time

import matplotlib.pyplot as plt
import pandas as pd

import os, csv

from cea.demand.calibration.clustering.sax import SAX
from cea.demand.calibration.clustering.sax_optimization import sax_optimization
from cea.plots.pareto_frontier_plot import frontier_2D_3OB
from cea.analysis.mcda import mcda_cluster_main

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def clustering_main(locator, data,  word_size, alphabet_size, gv):
    """
    Function to cluster different days of the year following the SAX method (see class for more info)
    :param locator: locator class
    :param gv: global variables class
    :param word_size: estimated word size, after optimization
    :param alphabet_size: estimated alphabet size. after optimization
    :param building_name: building name to make the cluster of its time series
    :param building_load: name of time_series to use form the building demand i.e., Qhsf_kWh, Qcsf_kWh, Qwwf_kWh etc.
    :param optimize: Boolean: true to run the optimization. you will first run the optimization,
    choose the word size and alphabet size. from there, run the program with the optimize = false
    :param plot_clusters: when optimize is false, decide whether you would like to see the data in each defined cluster
    :return: timeseries per cluster  in locator.get_clustering_calibration_file(cluster_name).

    INPUT / OUTPUT FILES:

    -  .csv file: dataframe with ID of every cluster per day of the year in locator.get_calibration_cluster(name)
    """
    t0 = time.clock()

    # calculate sax for timesieries data
    s = SAX(word_size, alphabet_size)
    sax = [s.to_letter_representation(x)[0] for x in data]

    # calculate dict with data per hour for the whole year and create groups per pattern
    hours_of_day = range(24)
    days_of_year = range(365)
    list_of_timeseries_transposed = [list(x) for x in zip(*data)]
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
        result.plot()
        plt.show()
    print

    gv.log('done - time elapsed: %(time_elapsed).2f seconds', time_elapsed=time.clock() - t0)

def optimization_clustering_main(locator, data, start_generation, number_individuals,
                                 number_generations, building_name, gv):
    t0 = time.clock()

    # set optimization problem for wordzise and alpha number
    sax_optimization(locator, data, time_series_len=24, BOUND_LOW=3, BOUND_UP=24,
                     NGEN=number_generations, MU=number_individuals, CXPB=0.9, start_gen=start_generation,
                     building_name=building_name)

    gv.log('done - time elapsed: %(time_elapsed).2f seconds', time_elapsed=time.clock() - t0)


def demand_CEA_reader(locator, building_name, building_load):
    """
    Algorithm to read hourly data of a building load and transform it
    into an array of 24h sequences.

    :param locator:
    :type locator: cea.inputlocator.InputLocator

    :param building_name:buidling name as stored in locator.get_demand_results_file()
    :type

    :param building_load: name of building load to consider. It must exist
    :return:

    :returns: array with 
    :rtype: array of arrays
    """
    # import data
    data = pd.read_csv(locator.get_demand_results_file(building_name),
                       usecols=['DATE', building_load], index_col='DATE')
    data.set_index(pd.to_datetime(data.index), inplace=True)
    data['day'] = data.index.dayofyear

    # transform into dicts where key = day and value = 24 h array
    groups = data.groupby(data.day)
    list_of_timeseries = [group[1][building_load].values for group in groups]

    return list_of_timeseries

def run_as_script():
    import cea.globalvar as gv
    import cea.inputlocator as inputlocator
    gv = gv.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)

    #Options
    optimize = False
    clustering = True
    plot_pareto = False
    multicriteria = False
    building_names = ['B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B09']
    building_load = 'Ef_kWh'

    if optimize:
        for name in building_names:
            data = demand_CEA_reader(locator=locator, building_name=name, building_load=building_load)
            start_generation = None  # or the number of generation to start from
            number_individuals = 8
            number_generations = 100
            optimization_clustering_main(locator=locator, data=data, start_generation=start_generation,
                                         number_individuals=number_individuals, number_generations=number_generations,
                                         building_name=name, gv=gv)
    if multicriteria:
        for i,name in enumerate(building_names):
            generation = 100
            weight_fitness1 = 80
            weight_fitness2 = 20
            weight_fitness3 = 10
            what_to_plot = "paretofrontier"
            output_path = locator.get_calibration_cluster_mcda(generation)

            # read_checkpoint
            input_path = locator.get_calibration_cluster_opt_checkpoint(generation, name)
            result = mcda_cluster_main(input_path=input_path, what_to_plot=what_to_plot,
                                       weight_fitness1=weight_fitness1, weight_fitness2=weight_fitness2,
                                       weight_fitness3=weight_fitness3)
            result["name"] = name
            if i ==0:
               result_final = pd.DataFrame(result).T
            else:
               result_final = result_final.append(pd.DataFrame(result).T, ignore_index=True)

        result_final.to_csv(output_path)

    if plot_pareto:
        for name in building_names:
            generation_to_plot = 100
            annotate_benchmarks = True
            annotate_fitness = True
            show_in_screen = False
            save_to_disc = True
            what_to_plot = "paretofrontier" #paretofrontier, halloffame, or population
            labelx = 'Accurracy [-]'
            labely = 'Inv-complexity[-]'
            labelz = 'Compression [-]'
            output = os.path.join(locator.get_calibration_clustering_folder(),
                                 "plot_gen_"+str(generation_to_plot)+"_building_name_"+name+".png")

            # read_checkpoint
            input_path = locator.get_calibration_cluster_opt_checkpoint(generation_to_plot, name)
            frontier_2D_3OB(input_path=input_path, what_to_plot = what_to_plot, output_path=output,
                            labelx= labelx,
                            labely = labely, labelz = labelz, show_benchmarks= annotate_benchmarks,
                            show_fitness=annotate_fitness,
                            show_in_screen = show_in_screen,
                            save_to_disc=save_to_disc)
    if clustering:
        name = 'B01'
        data = demand_CEA_reader(locator=locator, building_name=name, building_load=building_load)
        word_size = 7
        alphabet_size = 24
        clustering_main(locator=locator, data=data, word_size=word_size, alphabet_size=alphabet_size, gv=gv)

if __name__ == '__main__':
    run_as_script()

# -*- coding: utf-8 -*-
"""
Clustering
This script clusters typical days for a building
using SAX method for timeseries.

J. Fonseca  script development          27.10.16

"""
from __future__ import division

import os
import time

import pandas as pd

from cea.analysis.clustering.sax import SAX
from cea.analysis.clustering.sax.sax_optimization import sax_optimization
from cea.analysis.mcda import mcda_cluster_main
from cea.plots.clusters_plot import plot_day
from cea.plots.pareto_frontier_plot import frontier_2D_3OB

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def clustering_sax(locator, data, word_size, alphabet_size, gv):
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

    # calculate clustering for timesieries data
    s = SAX(word_size, alphabet_size)
    sax = [s.to_letter_representation(x)[0] for x in data]

    # calculate dict with data per hour for the whole year and create groups per pattern
    hours_of_day = range(data[0].size)
    days_of_year = range(len(data))
    print 'the days of the year evaluated are:', len(data)
    list_of_timeseries_transposed = [list(x) for x in zip(*data)]
    dict_data = dict((group, x) for group, x in zip(hours_of_day, list_of_timeseries_transposed))
    dict_data.update({'clustering': sax, 'day': days_of_year})

    # save all names and days of occurrence of each profile
    df = pd.DataFrame(dict_data)
    df[['clustering', 'day']].to_csv(locator.get_calibration_clusters_names())

    # save individual results to disk # create group by pattern
    grouped_sax = df.groupby('clustering')
    means = pd.DataFrame()
    counter = 0
    for name, group in grouped_sax:
        # total of time series and every clustering
        result = group.T.drop(['day','clustering'], axis=0)
        result.to_csv(locator.get_calibration_cluster(name))

        # calculate mean
        mean_df = result.mean(axis=1)

        if counter == 0:
            means = pd.DataFrame({name:mean_df.values})
        else:
            means = means.join(pd.DataFrame({name:mean_df.values}))
        counter +=1

    # print means
    means.to_csv(locator.get_calibration_cluster('clusters_mean'), index=False)

    # print names of clusters
    pd.DataFrame({"SAX":means.columns.values}).to_csv(locator.get_calibration_cluster('clusters_sax'), index=False)

    gv.log('done - time elapsed: %(time_elapsed).2f seconds', time_elapsed=time.clock() - t0)

def optimization_clustering_main(locator, data, start_generation, number_individuals,
                                 number_generations, building_name, gv):
    t0 = time.clock()

    # set optimization problem for wordzise and alpha number
    sax_optimization(locator, data, time_series_len=24, BOUND_LOW=3, BOUND_UP=24,
                     NGEN=number_generations, MU=number_individuals, CXPB=0.9, start_gen=start_generation,
                     building_name=building_name)

    gv.log('done - time elapsed: %(time_elapsed).2f seconds', time_elapsed=time.clock() - t0)


def demand_CEA_reader(locator, building_name, building_load, type="simulated"):
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
    #location of data
    if type == 'simulation':
        data = pd.read_csv(locator.get_demand_results_file(building_name),
                           usecols=['DATE', building_load], index_col='DATE')
    elif type== 'measured':
        data = pd.read_csv(locator.get_demand_measured_file(building_name),
                           usecols=['DATE', building_load], index_col='DATE')
    else:
        print 'Error: Make sure you select type equal to either "measured" or "simulated'

    data.set_index(pd.to_datetime(data.index), inplace=True)

    data['day'] = [str(x)+str(y) for x,y in zip(data.index.dayofyear, data.index.year)]
    # transform into dicts where key = day and value = 24 h array
    groups = data.groupby(data.day)
    list_of_timeseries = [group[1][building_load].values for group in groups]

    return list_of_timeseries

def run_as_script():
    import cea.globalvar as gv
    import cea.inputlocator as inputlocator
    gv = gv.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario=scenario_path)

    #Options
    optimize = False
    raw_data_plot = True
    multicriteria = False
    plot_pareto = False
    clustering = True
    cluster_plot = True
    building_names = ['dorm', 'lab', 'office'] #['B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B09']#['B01']#['B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B09']
    building_load = 'Ef_kWh'
    type_data = 'measured'

    if optimize:
        for name in building_names:
            data = demand_CEA_reader(locator=locator, building_name=name, building_load=building_load,
                                     type=type_data)
            start_generation = None  # or the number of generation to start from
            number_individuals = 16
            number_generations = 50
            optimization_clustering_main(locator=locator, data=data, start_generation=start_generation,
                                         number_individuals=number_individuals, number_generations=number_generations,
                                         building_name=name, gv=gv)
    if multicriteria:
        for i,name in enumerate(building_names):
            generation = 50
            weight_fitness1 = 100 # accurracy
            weight_fitness2 = 100 # complexity
            weight_fitness3 = 70 # compression
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
        for name in building_names[:1]:
            data = demand_CEA_reader(locator=locator, building_name=name, building_load=building_load,
                                     type=type_data)
            days_of_analysis = len(data)
            generation_to_plot = 50
            annotate_benchmarks = True
            annotate_fitness = False
            show_in_screen = False
            save_to_disc = True
            what_to_plot = "paretofrontier" #paretofrontier, halloffame, or population
            optimal_individual = pd.read_csv(locator.get_calibration_cluster_mcda(generation_to_plot))
            optimal_individual = optimal_individual.loc[optimal_individual["name"]==name]
            labelx = 'Accurracy (A) [-]'
            labely = 'Complexity (B) [-]'
            labelz = r'Compression ($\Gamma$) [-]'
            output = os.path.join(locator.get_calibration_clustering_plots_folder(),
                                 "plot_gen_"+str(generation_to_plot)+"_building_name_"+name+".png")

            # read_checkpoint
            input_path = locator.get_calibration_cluster_opt_checkpoint(generation_to_plot, name)
            frontier_2D_3OB(input_path=input_path, what_to_plot = what_to_plot, output_path=output,
                            labelx= labelx,
                            labely = labely, labelz = labelz,
                            days_of_analysis=days_of_analysis,
                            show_benchmarks= annotate_benchmarks,
                            show_fitness=annotate_fitness,
                            show_in_screen = show_in_screen,
                            save_to_disc=save_to_disc,
                            optimal_individual= optimal_individual,
                            )
    if clustering:
        name = 'lab'
        data = demand_CEA_reader(locator=locator, building_name=name, building_load=building_load,
                                 type=type_data)
        word_size = 4
        alphabet_size = 17

        clustering_sax(locator=locator, data=data, word_size=word_size, alphabet_size=alphabet_size, gv=gv)

        if cluster_plot:
            show_benchmark = True
            save_to_disc = True
            show_in_screen = False
            show_legend = False
            labelx = "Hour of the day"
            labely = "Electrical load [kW]"

            input_path = locator.get_calibration_cluster('clusters_mean')
            data = pd.read_csv(input_path)
            output_path = os.path.join(locator.get_calibration_clustering_plots_folder(),
                                 "w_a_"+str(word_size)+"_"+str(alphabet_size)+"_building_name_"+name+".png")

            plot_day(data=data, output_path=output_path, labelx=labelx,
                     labely=labely, save_to_disc=save_to_disc, show_in_screen=show_in_screen,
                     show_legend=show_legend)#, show_benchmark=show_benchmark)

    if raw_data_plot:
        name = 'lab'
        show_benchmark = True
        save_to_disc = True
        show_in_screen = False
        show_legend = True
        labelx = "Hour of the day"
        labely = "Electrical load [kW]"
        data = demand_CEA_reader(locator=locator, building_name=name, building_load=building_load,
                                     type=type_data)

        data = pd.DataFrame(dict((str(key), value) for (key, value) in enumerate(data)))

        # input_path = locator.get_calibration_cluster('clusters_mean')
        output_path = os.path.join(locator.get_calibration_clustering_plots_folder(), "raw_building_name_" + name + ".png")

        plot_day(data=data, output_path=output_path, labelx=labelx,
                 labely=labely, save_to_disc=save_to_disc, show_in_screen=show_in_screen,
                 show_legend=show_legend)  # , show_benchmark=show_benchmark)

if __name__ == '__main__':
    run_as_script()

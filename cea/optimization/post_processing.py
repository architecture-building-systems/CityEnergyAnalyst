"""
File aims to compile all the post-processing steps to be done after optimization. This include
1. Combining the population from various generations
2. Generate plots corresponding to various generations
3. Combine files from various runs and generations
Note: There will be few hard coded file names and paths, which vary with case.
"""

from __future__ import division
from cea.optimization.constants import *
import pandas as pd
import cea.config
import cea.globalvar
import cea.inputlocator
from cea.optimization.prices import Prices as Prices
import cea.optimization.distribution.network_opt_main as network_opt
import cea.optimization.master.generation as generation
from cea.optimization.preprocessing.preprocessing_main import preproccessing
import time
import json
import cea.optimization.master.evaluation as evaluation
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.cm as cmx
import os
import numpy as np
import pandas as pd

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def combining_population_of_various_generations(data_path):
    population = []
    objectives = []
    for i in range(204):
        path = data_path + '\CheckPoint_' + str(i+1)
        with open(path, "rb") as fp:
            data = json.load(fp)
            # print (data)
            # objectives.append(data['population_fitness'])
            # population.append(data['population'])
            for j in range(len(data['population_fitness'])):
                objectives.append(data['population_fitness'][j])
                population.append(data['population'][j])

    df = pd.DataFrame({'objectives': objectives, 'population': population})
    df.to_csv(data_path + '\compiled.csv')

def individual_calculation(individual, config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    gv = cea.globalvar.GlobalVariables()
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    gv.num_tot_buildings = total_demand.Name.count()
    ntwList = ["1" * total_demand.Name.count()]

    t0 = time.clock()

    prices = Prices(locator, config)

    extra_costs, extra_CO2, extra_primary_energy, solarFeat = preproccessing(locator, total_demand, building_names,
                                                                             config.weather, gv, config, prices)
    network_features = network_opt.network_opt_main()

    evaluation.checkNtw(individual, ntwList, locator, gv, config)
    (costs, CO2, prim, master_to_slave_vars) = evaluation.evaluation_main(individual, building_names, locator, extra_costs, extra_CO2,
                                                    extra_primary_energy, solarFeat,
                                                    network_features, gv, config, prices)

    print (costs, CO2, prim, master_to_slave_vars)

def final_generation(data_path, config):
    population = []
    objectives = []
    path = data_path + '\CheckPoint_' + str(183)
    with open(path, "rb") as fp:
        data = json.load(fp)
    population = data['population']
    objectives = data['population_fitness']

    # locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    # gv = cea.globalvar.GlobalVariables()
    # total_demand = pd.read_csv(locator.get_total_demand())
    # building_names = total_demand.Name.values
    #
    # for ind in population:
    #     individual_calculation(ind, config)


    df = pd.DataFrame({'objectives': objectives, 'population': population})
    df.to_csv(data_path + '\compiled_last.csv')


    xs = [((objective[0])) for objective in objectives]  # Costs
    ys = [((objective[1])) for objective in objectives]  # GHG emissions
    zs = [((objective[2])) for objective in objectives]  # MJ

    # normalization is used for optimization metrics as the objectives are all present in different scales
    # to have a consistent value for normalization, the values of the objectives of the initial generation are taken
    normalization = [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)]

    xs = [a / 10**6 for a in xs]
    ys = [a / 10**6 for a in ys]
    zs = [a / 10**6 for a in zs]

    # plot showing the Pareto front of every generation
    # parameters corresponding to Pareto front
    fig = plt.figure()
    ax = fig.add_subplot(111)
    cm = plt.get_cmap('jet')
    cNorm = matplotlib.colors.Normalize(vmin=min(zs), vmax=max(zs))
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)
    ax.scatter(xs, ys, c=scalarMap.to_rgba(zs), s=50, alpha=0.8)
    ax.set_xlabel('TAC [$ Mio/yr]')
    ax.set_ylabel('GHG emissions [x 10^3 ton CO2-eq]')
    scalarMap.set_array(zs)
    fig.colorbar(scalarMap, label='Primary Energy [x 10^3 GJ]')
    plt.grid(True)
    plt.rcParams['figure.figsize'] = (20, 10)
    plt.rcParams.update({'font.size': 12})
    plt.gcf().subplots_adjust(bottom=0.15)
    plt.savefig(data_path + '\Pareto_final.png')
    plt.clf()

def graph_plot(data_path):

    data = pd.read_excel(data_path + '\For Python.xlsx')
    xs = data['TAC'].values
    ys = data['CO2'].values
    zs = data['Eprim'].values

    xs = [a / 10 ** 6 for a in xs]
    ys = [a / 10 ** 6 for a in ys]
    zs = [a / 10 ** 6 for a in zs]

    # plot showing the Pareto front of every generation
    # parameters corresponding to Pareto front
    fig = plt.figure()
    ax = fig.add_subplot(111)
    cm = plt.get_cmap('jet')
    cNorm = matplotlib.colors.Normalize(vmin=min(zs), vmax=max(zs))
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)
    ax.scatter(xs, ys, c=scalarMap.to_rgba(zs), s=50, alpha=0.8)
    ax.set_xlabel('TAC [$ Mio/yr]')
    ax.set_ylabel('GHG emissions [x 10^3 ton CO2-eq]')
    scalarMap.set_array(zs)
    fig.colorbar(scalarMap, label='Primary Energy [x 10^3 GJ]')
    plt.grid(True)
    plt.rcParams['figure.figsize'] = (20, 10)
    plt.rcParams.update({'font.size': 12})
    plt.gcf().subplots_adjust(bottom=0.15)
    plt.savefig(data_path + '\Pareto.png')
    plt.clf()

def main(config):
    """
    run the whole optimization routine
    """
    gv = cea.globalvar.GlobalVariables()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    data_path = 'C:\Users\Bhargava\OneDrive\MUSES\Phase Development Optimization\Results\scenario 1\master'
    # combining_population_of_various_generations(data_path)
    # individual = []
    # individual_calculation(individual, config)
    final_generation(data_path, config)
    # data_path = 'C:\Users\Bhargava\OneDrive\MUSES\Phase Development Optimization\Results\scenario 2.2\post processing'
    # graph_plot(data_path)


if __name__ == '__main__':
    main(cea.config.Configuration())
from __future__ import division

import multiprocessing as mp
import os

import pandas as pd
import time
import numpy as np

import cea.globalvar
import cea.inputlocator
import cea.config
import cea.optimization.master.generation as generation
import cea.optimization.master.evaluation as evaluation
import cea.optimization.distribution.network_opt_main as network_opt
from cea.optimization.preprocessing.preprocessing_main import preproccessing
from cea.optimization.prices import Prices as Prices



__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas", "Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

import cea

def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    gv = cea.globalvar.GlobalVariables()
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    gv.num_tot_buildings = total_demand.Name.count()
    ntwList = ["1"*total_demand.Name.count()]

    t0 = time.clock()

    prices = Prices(locator, config)

    extra_costs, extra_CO2, extra_primary_energy, solarFeat = preproccessing(locator, total_demand, building_names,
                                                                   config.weather, gv, config, prices)
    network_features = network_opt.network_opt_main()

    number_samples = 500

    input_data = pd.DataFrame(range(number_samples), columns=['index'])
    input_data_individual = []
    output_costs = []
    output_CO2 = []
    output_prim = []
    print (input_data)

    for i in range(number_samples):

        individual = generation.generate_main(len(building_names))
        individual = evaluation.check_invalid(individual, len(building_names), gv)
        # individual = [10.610020.21000010.161110.0510.0110.920.200xc36a0a_PPActivationPattern]
        # individual = [1, 0.61, 0, 0, 2, 0.21, 0, 0, 0, 0, 1, 0.16, 1, 1, 1, 0.05, 1, 0.01, 1, 0.92, 0.20, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0]
        # individual = [2, 0.07782607228696607, 1, 0.1530469116519292, 1, 0.11673503132454824, 1, 0.05021933164704283, 0, 0, 1,
        #  0.5826643581289432, 1, 1, 0, 0, 1, 1.0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1,
        #  1, 1, 0]
        # individual = [1, 0.3113446240855483, 1, 0.688655375914452, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1,
        #               0.05183938869996774, 1, 0.9481606113000323, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1,
        #               1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1]


        evaluation.checkNtw(individual, ntwList, locator, gv, config)

        (costs, CO2, prim) = evaluation.evaluation_main(individual, building_names, locator, extra_costs, extra_CO2, extra_primary_energy, solarFeat,
                                                        network_features, gv, config, prices)
        print (individual)

        input_data_individual.append(individual)
        output_costs.append(costs)
        output_CO2.append(CO2)
        output_prim.append(prim)
        print (i)

    time_elapsed = time.clock() - t0
    print (time_elapsed)
    input_data['individual'] = input_data_individual
    input_data['costs'] = output_costs
    input_data['CO2'] = output_CO2
    input_data['prim'] = output_prim
    input_data.to_csv('C:\Users\krish\Desktop/input_data.csv')



if __name__ == '__main__':
    main(cea.config.Configuration())
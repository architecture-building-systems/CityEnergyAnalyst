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
    for i in range(100):
        path = data_path + '\CheckPoint_' + str(1)
        with open(path, "rb") as fp:
            data = json.load(fp)
            print (data)
            for i in range(len(data['population_fitness'])):
                objectives.append(data['population_fitness'][i])
                population.append(data['population'][i])

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
    (costs, CO2, prim) = evaluation.evaluation_main(individual, building_names, locator, extra_costs, extra_CO2,
                                                    extra_primary_energy, solarFeat,
                                                    network_features, gv, config, prices)

    print (costs, CO2, prim)


def main(config):
    """
    run the whole optimization routine
    """
    gv = cea.globalvar.GlobalVariables()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    data_path = 'C:\Users\Bhargava\Desktop\Results\Scenario-2\Phase-1\Partial-1'
    combining_population_of_various_generations(data_path=data_path)
    individual = []
    individual_calculation(individual, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
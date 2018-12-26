"""
This file helps in evaluating individual generation. This will be useful when you need to change the global variables
and see how the objective function value changes.

Do ensure you have the uncertainty.csv which will be obtained by running uncertainty_parameters.py

This is part of the uncertainty analysis
"""
from __future__ import division

import cea.inputlocator
import pandas as pd
import cea.optimization.distribution.network_opt_main as network_opt
import cea.optimization.master.evaluation as evaluation
import json
import csv
from cea.optimization.lca_calculations import lca_calculations
from cea.optimization.prices import Prices as Prices


__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def individual_evaluation(generation, level, size, variable_groups):
    """
    :param generation: Generation of the optimization in which the individual evaluation is to be done
    :type generation: int
    :param level: Number of the uncertain scenario. For each scenario, the objectives are calculated
    :type level: int
    :param size: Total uncertain scenarios developed. See 'uncertainty.csv'
    :type size: int
    :return: Function saves the new objectives in a json file
    """

    from cea.optimization.preprocessing.preprocessing_main import preproccessing
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path)
    config = cea.config.Configuration()
    weather_file = locator.get_default_weather()

    with open(locator.get_optimization_master_results_folder() + "\CheckPoint_" + str(generation), "rb") as fp:
        data = json.load(fp)

    pop = data['population']
    ntwList = data['networkList']

    # # Uncertainty Part
    row = []
    with open(locator.get_uncertainty_results_folder() + '\uncertainty.csv') as f:
        reader = csv.reader(f)
        for i in xrange(size+1):
            row.append(next(reader))

    j = level + 1

    for i in xrange(len(row[0])-1):
        setattr(gv, row[0][i+1], float(row[j][i+1]))

    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    gv.num_tot_buildings = total_demand.Name.count()
    lca = lca_calculations(locator, config)
    prices = Prices(locator, config)

    extra_costs, extra_CO2, extra_primary_energy, solarFeat = preproccessing(locator, total_demand,
                                                                                     building_names,
                                                                                     weather_file, gv)
    network_features = network_opt.network_opt_main()
    def objective_function(ind, ind_num):
        (costs, CO2, prim) = evaluation.evaluation_main(ind, building_names, locator, solarFeat, network_features, gv,
                                                        config, prices, lca,
                                                        ind_num, generation
                                                        )
        # print (costs, CO2, prim)
        return (costs, CO2, prim)

    fitness = []
    for i in xrange(gv.initialInd):
        evaluation.checkNtw(pop[i], ntwList, locator, gv)
        fitness.append(objective_function(pop[i], i))

    with open(locator.get_uncertainty_checkpoint(level), "wb") as fp:
        cp = dict(population=pop, uncertainty_level=level, population_fitness=fitness)
        json.dump(cp, fp)

if __name__ == '__main__':
    generation = 50  # generation which you are interested in testing
    size = 1000  # number of uncertain scenarios being tested

    for i in xrange(size):
        individual_evaluation(generation, i, size, variable_groups=('ECONOMIC',))
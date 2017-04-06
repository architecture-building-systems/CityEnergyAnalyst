"""
This file helps in evaluating individual generation. This will be useful when you need to change the global variables
and see how the objective function value changes. This can accept both pickle files and csv files. Pickle files are
the preferred mode as they keep intact the type of the variables being passed, where as the csv files convert everything
into string format. So this will only useful to see the results but not much further

This is part of the uncertainty analysis
"""
__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def individual_evaluation(generation, level, filetype):
    import cea.optimization.supportFn as sFn
    import cea.inputlocator
    import pandas as pd
    import cea.optimization.distribution.network_opt_main as network_opt
    import cea.optimization.master.evaluation as evaluation
    import os
    import re
    import csv
    import json
    from cea.optimization.preprocessing.preprocessing_main import preproccessing
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path)
    weather_file = locator.get_default_weather()
    os.chdir(locator.get_optimization_master_results_folder())
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    gv.num_tot_buildings = total_demand.Name.count()

    with open("CheckPointInitialjson", "rb") as fp:
        data = json.load(fp)
    print ((data['population']))
    if filetype == 'pickle':
        pop, eps, testedPop, ntwList, fitness = sFn.readCheckPoint(locator, generation, 0)
    elif filetype == 'csv':
        pop, eps, testedPop, ntwList, fitness = sFn.readCheckPoint(locator, generation, 0)
        with open("CheckPointcsv" + str(generation), "rb") as csv_file:
            pop = []
            ntwList =[]
            reader = csv.reader(csv_file)
            mydict = dict(reader)
            population = mydict['population']
            population = re.findall(r'\d+(?:\.\d+)?', population)
            # print (population)
            popfloat = [float(x) for x in population]

            for i in xrange(len(popfloat)):
                if popfloat[i] - int(popfloat[i]) == 0:
                    popfloat[i] = int(popfloat[i])

            for i in xrange(len(popfloat)/45):
                pop.append(popfloat[i*45:(((i+1)*45))])

            network = mydict['networkList']
            network = re.findall(r'\d+', network)
            for i in xrange(len(network)):
                ntwList.append(long(network[i]))
            print (ntwList)

    # print (len(pop))
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    gv.num_tot_buildings = total_demand.Name.count()

    extra_costs, extra_CO2, extra_primary_energy, solarFeat = preproccessing(locator, total_demand,
                                                                                     building_names,
                                                                                     weather_file, gv)



    network_features = network_opt.network_opt_main()

    def objective_function(ind):
        (costs, CO2, prim) = evaluation.evaluation_main(ind, building_names, locator, extra_costs, extra_CO2, extra_primary_energy, solarFeat,
                                                        network_features, gv)
        # print (costs, CO2, prim)
        return (costs, CO2, prim)

    fitness = []
    for i in xrange(gv.initialInd):
        # print (i)
        # print (pop[i])
        evaluation.checkNtw(pop[i], ntwList, locator, gv)
        fitness.append(objective_function(pop[i]))

    os.chdir(locator.get_optimization_master_results_folder())
    with open("CheckPointTesting_uncertainty_" + str(level), "wb") as csv_file:
        writer = csv.writer(csv_file)
        cp = dict(population=pop, generation=generation, population_fitness=fitness)
        for key, value in cp.items():
            writer.writerow([key, value])

if __name__ == '__main__':
    generation = 3
    level = 99  # specifying parameters of which level need to be used in uncertainty analysis
    filetype = 'csv'  # file type can be either pickle or csv

    individual_evaluation(generation, level, filetype)


def individual_evaluation(generation, level, filetype):
    import cea.globalvar
    from pickle import Pickler, Unpickler
    from deap import base, tools, algorithms
    import cea.optimization.supportFn as sFn
    import cea.inputlocator
    import pandas as pd
    import cea.optimization.distribution.network_opt_main as network_opt
    import cea.optimization.master.evaluation as evaluation
    import os
    import re
    import csv
    from cea.optimization.preprocessing.preprocessing_main import preproccessing
    j = level
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path)
    weather_file = locator.get_default_weather()
    scenario_path = r'c:\reference-case-zug\baseline'
    locator = cea.inputlocator.InputLocator(scenario_path)
    os.chdir(locator.get_optimization_master_results_folder())

    pareto = []
    xs = []
    ys = []
    zs = []
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    gv.num_tot_buildings = total_demand.Name.count()

    if filetype == 'pickle':
        pop, eps, testedPop, ntwList = sFn.readCheckPoint(locator, generation, 0)
    elif filetype == 'csv':
        with open("CheckPointcsv" + str(generation), "rb") as csv_file:
            pop = []
            popfloat = []
            reader = csv.reader(csv_file)
            mydict = dict(reader)
            nBuildings = len(building_names)
            ntwList = ["1" * nBuildings]
            population = mydict['population']
            population = re.findall(r'\d+(?:\.\d+)?', population)
            # print (population)
            popfloat = [float(x) for x in population]

            for i in xrange(len(popfloat)):
                if popfloat[i] - int(popfloat[i]) == 0:
                    popfloat[i] = int(popfloat[i])

            for i in xrange(len(popfloat)/45):
                pop.append(popfloat[i*45:(((i+1)*45)-1)])

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

    nBuildings = len(building_names)
    # ntwList = ["1" * nBuildings]
    fitness = []
    for i in xrange(4):
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
    generation = 2
    level = 99
    filetype = 'pickle'  # file type can be either pickle or csv

    individual_evaluation(generation, level, filetype)

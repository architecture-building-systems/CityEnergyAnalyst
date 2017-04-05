
def individual_evaluation(generation, level):
    import cea.globalvar
    import cea.inputlocator
    import csv
    import pandas as pd
    import cea.optimization.distribution.network_opt_main as network_opt
    import cea.optimization.master.master_main as master
    import cea.optimization.master.evaluation as evaluation
    import matplotlib
    import matplotlib.cm as cmx
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    import os
    import re
    from cea.optimization.preprocessing.preprocessing_main import preproccessing
    j = level
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path)
    weather_file = locator.get_default_weather()
    os.chdir(locator.get_optimization_master_results_folder())

    import csv
    scenario_path = r'c:\reference-case-zug\baseline'
    locator = cea.inputlocator.InputLocator(scenario_path)
    os.path.join(locator.get_optimization_master_results_folder())

    pareto = []
    xs = []
    ys = []
    zs = []

    with open("CheckPoint" + str(generation), "rb") as csv_file:
        pop = []
        popfloat = []
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
    ntwList = ["1" * nBuildings]
    fitness = []
    for i in xrange(20):
        # print (i)
        # print (pop[i])
        evaluation.checkNtw(pop[i], ntwList, locator, gv)
        fitness.append(objective_function(pop[i]))

    os.path.join(locator.get_optimization_master_results_folder())
    with open("CheckPointTesting_uncertainty_" + str(level), "wb") as csv_file:
        writer = csv.writer(csv_file)
        cp = dict(population=pop, generation=generation, objective_function_values=fitness)
        for key, value in cp.items():
            writer.writerow([key, value])

if __name__ == '__main__':
    generation = 50
    level = 99

    individual_evaluation(generation, level)

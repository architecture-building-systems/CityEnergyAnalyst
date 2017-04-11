"""
This file helps in evaluating individual generation. This will be useful when you need to change the global variables
and see how the objective function value changes. 

Do ensure you have the uncertainty.csv which will be obtained by running uncertainty_parameters.py

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

def individual_evaluation(generation, level, size):

    import cea.inputlocator
    import pandas as pd
    import cea.optimization.distribution.network_opt_main as network_opt
    import cea.optimization.master.evaluation as evaluation
    import os
    import json
    import csv
    from cea.optimization.preprocessing.preprocessing_main import preproccessing
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path)
    weather_file = locator.get_default_weather()
    os.chdir(locator.get_optimization_master_results_folder())

    with open("CheckPoint" + str(generation), "rb") as fp:
        data = json.load(fp)

    pop = data['population']
    ntwList = data['networkList']

    # # Uncertainty Part
    row = []
    with open('uncertainty1000.csv') as f:
        reader = csv.reader(f)
        for i in xrange(size+1):
            row.append(next(reader))

    j = level + 1
    # Uncertainty Parameters
    HP_n = float(row[j][1])  # lifetime [years] default 20
    GHP_nHP = float(row[j][2])  # for the geothermal heat pump default 20
    Boiler_n = float(row[j][3])  # lifetime, after A+W, default 20
    CC_n = float(row[j][4])  # lifetime default 25
    FC_n = float(row[j][5])  # years of operation default 10
    PVT_n = float(row[j][6])  # years of operation default 20
    SC_n = PVT_n  # years of operation default 20
    CT_a = (float(row[j][7]))  # annuity factor default 0.15
    Subst_n = float(row[j][8])  # Lifetime after A+W default 20
    ELEC_PRICE = float(row[j][9]) * gv.EURO_TO_CHF / 1000.0  # default 0.2
    cPump = ELEC_PRICE * 24. * 365.  # coupled to electricity cost
    NG_PRICE = float(row[j][10]) * gv.EURO_TO_CHF / 1000.0  # [CHF / wh] # default 0.068
    BG_PRICE = float(row[j][11]) * gv.EURO_TO_CHF / 1000.0  # [CHF / wh] # default 0.076
    Subst_i = float(row[j][12])/100 # default 0.05
    FC_i = float(row[j][13]) /100 # interest rate default 0.05
    HP_i = float(row[j][14])/100  # interest rate default 0.05
    Boiler_i = float(row[j][15])/100  # interest rate default 0.05

    # changing the parameters based on the uncertainty distribution
    setattr(gv, 'HP_n', HP_n)
    setattr(gv, 'GHP_nHP', GHP_nHP)
    setattr(gv, 'Boiler_n', Boiler_n)
    setattr(gv, 'CC_n', CC_n)
    setattr(gv, 'FC_n', FC_n)
    setattr(gv, 'PVT_n', PVT_n)
    setattr(gv, 'SC_n', SC_n)
    setattr(gv, 'CT_a', CT_a)
    setattr(gv, 'Subst_n', Subst_n)
    setattr(gv, 'ELEC_PRICE', ELEC_PRICE)
    setattr(gv, 'cPump', cPump)
    setattr(gv, 'NG_PRICE', NG_PRICE)
    setattr(gv, 'BG_PRICE', BG_PRICE)
    setattr(gv, 'Subst_i', Subst_i)
    setattr(gv, 'FC_i', FC_i)
    setattr(gv, 'HP_i', HP_i)
    setattr(gv, 'Boiler_i', Boiler_i)

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
        evaluation.checkNtw(pop[i], ntwList, locator, gv)
        fitness.append(objective_function(pop[i]))

    os.chdir(locator.get_optimization_master_results_folder())
    with open("CheckPointTesting_uncertainty_" + str(level), "wb") as fp:
        cp = dict(population=pop, generation=generation, population_fitness=fitness)
        json.dump(cp, fp)

    x = pd.read_excel(locator.get_uncertainty_db(), 'ECONOMIC')

    HP_n = x[x['name'] == 'HP_n']['default'].max()  # lifetime [years] default 20
    GHP_nHP = x[x['name'] == 'GHP_nHP']['default'].max()  # for the geothermal heat pump default 20
    Boiler_n = x[x['name'] == 'Boiler_n']['default'].max()  # lifetime, after A+W, default 20
    CC_n = x[x['name'] == 'CC_n']['default'].max()  # lifetime default 25
    FC_n = x[x['name'] == 'FC_n']['default'].max()  # years of operation default 10
    PVT_n = x[x['name'] == 'PVT_n']['default'].max()  # years of operation default 20
    SC_n = PVT_n  # years of operation default 20
    CT_a = x[x['name'] == 'CT_a']['default'].max()  # annuity factor default 0.15
    Subst_n = x[x['name'] == 'Subst_n']['default'].max()  # Lifetime after A+W default 20
    ELEC_PRICE = x[x['name'] == 'ELEC_PRICE']['default'].max() * gv.EURO_TO_CHF / 1000.0  # default 0.2
    cPump = ELEC_PRICE * 24. * 365.  # coupled to electricity cost
    NG_PRICE = x[x['name'] == 'NG_PRICE'][
                        'default'].max() * gv.EURO_TO_CHF / 1000.0  # [CHF / wh] # default 0.068
    BG_PRICE = x[x['name'] == 'BG_PRICE'][
                        'default'].max() * gv.EURO_TO_CHF / 1000.0  # [CHF / wh] # default 0.076
    Subst_i = x[x['name'] == 'Subst_i']['default'].max() / 100  # default 0.05
    FC_i = x[x['name'] == 'FC_i']['default'].max() / 100  # interest rate default 0.05
    HP_i = x[x['name'] == 'HP_i']['default'].max() / 100  # interest rate default 0.05
    Boiler_i = x[x['name'] == 'Boiler_i']['default'].max() / 100  # interest rate default 0.05

    # defaulting the parameters
    setattr(gv, 'HP_n', HP_n)
    setattr(gv, 'GHP_nHP', GHP_nHP)
    setattr(gv, 'Boiler_n', Boiler_n)
    setattr(gv, 'CC_n', CC_n)
    setattr(gv, 'FC_n', FC_n)
    setattr(gv, 'PVT_n', PVT_n)
    setattr(gv, 'SC_n', SC_n)
    setattr(gv, 'CT_a', CT_a)
    setattr(gv, 'Subst_n', Subst_n)
    setattr(gv, 'ELEC_PRICE', ELEC_PRICE)
    setattr(gv, 'cPump', cPump)
    setattr(gv, 'NG_PRICE', NG_PRICE)
    setattr(gv, 'BG_PRICE', BG_PRICE)
    setattr(gv, 'Subst_i', Subst_i)
    setattr(gv, 'FC_i', FC_i)
    setattr(gv, 'HP_i', HP_i)
    setattr(gv, 'Boiler_i', Boiler_i)


if __name__ == '__main__':
    generation = 50  # generation which you are interested in testing
    level = 5  # specifying parameters of which level need to be used in uncertainty analysis
    size = 1000  # number of uncertain scenarios being tested

    for i in xrange(750):
        i = i + 253
        individual_evaluation(generation, i, size)

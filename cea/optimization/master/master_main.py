"""
===========================
Evolutionary algorithm main
===========================

"""
from __future__ import division

import time
import json
from cea.optimization.constants import *
import cea.optimization.master.crossover as cx
import cea.optimization.master.evaluation as evaluation
from deap import base
from deap import creator
from deap import tools
import cea.optimization.master.generation as generation
import mutations as mut
import selection as sel
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.cm as cmx
import os
import numpy as np
import pandas as pd
import cea.optimization.supportFn as sFn



__author__ =  "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Sreepathi Bhargava Krishna", "Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def evolutionary_algo_main(locator, building_names, extra_costs, extra_CO2, extra_primary_energy, solar_features,
                           network_features, gv, config, prices, genCP=00):
    """
    Evolutionary algorithm to optimize the district energy system's design.
    This algorithm optimizes the size and operation of technologies for a district heating network.
    electrical network are not considered but their burdens in terms electricity costs, efficiency and emissions
    is added on top of the optimization.
    The equipment for cooling networks is not optimized as it is assumed that all customers with cooling needs will be
    connected to a lake. in case there is not enough capacity from the lake, a chiller and cooling tower is used to
    cover the extra needs.

    genCP is defaulted to '0' when the entire optimization is run. For running from the intermediate generations, key in
    the generation from which the optimization should continue.

    :param locator: locator class
    :param building_names: vector with building names
    :param extra_costs: costs calculated before optimization of specific energy services
     (process heat and electricity)
    :param extra_CO2: green house gas emissions calculated before optimization of specific energy services
     (process heat and electricity)
    :param extra_primary_energy: primary energy calculated before optimization of specific energy services
     (process heat and electricity)
    :param solar_features: object class with vectors and values of interest for the integration of solar potentials
    :param network_features: object class with linear coefficients of the network obtained after its optimization
    :param gv: global variables class
    :param genCP: 0
    :type locator: class
    :type building_names: array
    :type extra_costs: float
    :type extra_CO2: float
    :type extra_primary_energy: float
    :type solar_features: class
    :type network_features: class
    :type gv: class
    :type genCP: int
    :return: for every generation 'g': it stores the results of every generation of the genetic algorithm in the
     subfolders locator.get_optimization_master_results_folder() as a python pickle file.
    :rtype: pickled file
    """
    t0 = time.clock()

    # initiating hall of fame size and the function evaluations
    halloffame_size = config.optimization.halloffame
    function_evals = 0
    euclidean_distance = 0
    spread = 0

    # get number of buildings
    nBuildings = len(building_names)

    # DEFINE OBJECTIVE FUNCTION
    def objective_function(ind):
        """
        Objective function is used to calculate the costs, CO2, primary energy and the variables corresponding to the
        individual
        :param ind: Input individual
        :type ind: list
        :return: returns costs, CO2, primary energy and the master_to_slave_vars
        """
        costs, CO2, prim, master_to_slave_vars = evaluation.evaluation_main(ind, building_names, locator, extra_costs, extra_CO2, extra_primary_energy, solar_features,
                                                        network_features, gv, config, prices)
        return costs, CO2, prim, master_to_slave_vars

    # SET-UP EVOLUTIONARY ALGORITHM
    # Contains 3 minimization objectives : Costs, CO2 emissions, Primary Energy Needs
    # this part of the script sets up the optimization algorithm in the same syntax of DEAP toolbox
    creator.create("Fitness", base.Fitness, weights=(-1.0, -1.0, -1.0)) # weights of -1 for minimization, +1 for maximization
    creator.create("Individual", list, fitness=creator.Fitness)
    toolbox = base.Toolbox()
    toolbox.register("generate", generation.generate_main, nBuildings)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.generate)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", objective_function)

    # Initialization of variables
    ntwList = ["1"*nBuildings]
    epsInd = []
    invalid_ind = []
    halloffame = []
    halloffame_fitness = []
    costs_list = []
    co2_list = []
    prim_list = []
    slavedata_list = []
    fitnesses = []
    capacities = []
    disconnected_capacities = []
    Furnace_wet = 0
    Furnace_wet_capacity_W = 0
    Furnace_dry = 0
    Furnace_dry_capacity_W = 0
    CHP_NG = 0
    CHP_NG_capacity_W = 0
    CHP_BG = 0
    CHP_BG_capacity_W = 0
    Base_boiler_BG = 0
    Base_boiler_BG_capacity_W = 0
    Base_boiler_NG = 0
    Base_boiler_NG_capacity_W = 0
    Peak_boiler_BG = 0
    Peak_boiler_BG_capacity_W = 0
    Peak_boiler_NG = 0
    Peak_boiler_NG_capacity_W = 0
    HP_Lake = 0
    HP_Lake_capacity_W = 0
    HP_Sewage = 0
    HP_Sewage_capacity_W = 0
    GHP = 0
    GHP_capacity_W = 0
    PV = 0
    PV_capacity_W = 0
    PVT = 0
    PVT_capacity_W = 0
    SC = 0
    SC_capacity_W = 0

    # Evolutionary strategy
    if genCP is 0:
        # create population based on the number of individuals in the config file
        pop = toolbox.population(n=config.optimization.initialind)

        # Check the network and update ntwList. ntwList size keeps changing as the following loop runs
        for ind in pop:
            evaluation.checkNtw(ind, ntwList, locator, gv, config)

        # Evaluate the initial population
        print "Evaluate initial population"
        ntwList = ntwList[1:]  # done this to remove the first individual in the ntwList as it is an initial value
        # costs_list updates the costs involved in every individual
        # co2_list updates the GHG emissions in terms of CO2
        # prim_list updates the primary energy  corresponding to every individual
        # slavedata_list updates the master_to_slave variables corresponding to every individual. This is used in
        # calculating the capacities of both the centralized and the decentralized system
        for i, ind in enumerate(pop):
            a = objective_function(ind)
            costs_list.append(a[0])
            co2_list.append(a[1])
            prim_list.append(a[2])
            slavedata_list.append(a[3])

        # fitnesses appends the costs, co2 and primary energy corresponding to each individual
        # the main reason of doing the following is to follow the syntax provided by DEAP toolbox as it works on the
        # fitness class in every individual
        for i in range(len(costs_list)):
            fitnesses.append([costs_list[i], co2_list[i], prim_list[i]])

        # linking every individual with the corresponding fitness, this also keeps a track of the number of function
        # evaluations. This can further be used as a stopping criteria in future
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit
            function_evals = function_evals + 1  # keeping track of number of function evaluations

        # halloffame is the best individuals that are observed in all generations
        # the size of the halloffame is linked to the number of initial individuals
        if len(halloffame) <= halloffame_size:
            halloffame.extend(pop)

        # halloffame_fitness appends the fitness values corresponding to the individuals in the halloffame
        for ind in halloffame:
            halloffame_fitness.append(ind.fitness.values)

        # disconnected building capacity is calculated from the networklist of every individual
        # disconnected building have four energy technologies namely Bio-gas Boiler, Natural-gas Boiler, Fuel Cell
        # and Geothermal heat pumps
        # These values are already calculated in 'decentralized_main.py'. This piece of script gets these values from
        # the already created csv files
        for (index, network) in enumerate(ntwList):
            intermediate_capacities = []
            for i in range(len(network)):
                # if a building is connected, which corresponds to '1' then the disconnected shares are '0'
                # if a building is disconnected, which corresponds to '0' then disconnected shares are imported from csv files
                Disconnected_Boiler_BG_share = 0
                Disconnected_Boiler_BG_capacity_W = 0
                Disconnected_Boiler_NG_share = 0
                Disconnected_Boiler_NG_capacity_W = 0
                Disconnected_FC_share = 0
                Disconnected_FC_capacity_W = 0
                Disconnected_GHP_share = 0
                Disconnected_GHP_capacity_W = 0

                if network[i] == "0":
                    df = pd.read_csv(locator.get_optimization_disconnected_folder_building_result(building_names[i]))
                    dfBest = df[df["Best configuration"] == 1]
                    Disconnected_Boiler_BG_share = dfBest["BoilerBG Share"].iloc[0]
                    Disconnected_Boiler_NG_share = dfBest["BoilerNG Share"].iloc[0]
                    Disconnected_FC_share = dfBest["FC Share"].iloc[0]
                    Disconnected_GHP_share = dfBest["GHP Share"].iloc[0]

                    if Disconnected_Boiler_BG_share == 1:
                        Disconnected_Boiler_BG_capacity_W = dfBest["Nominal Power"].iloc[0]

                    if Disconnected_Boiler_NG_share == 1:
                        Disconnected_Boiler_NG_capacity_W = dfBest["Nominal Power"].iloc[0]

                    if Disconnected_FC_share == 1:
                        Disconnected_FC_capacity_W = dfBest["Nominal Power"].iloc[0]

                    if Disconnected_GHP_share == 1:
                        Disconnected_GHP_capacity_W = dfBest["Nominal Power"].iloc[0]

                    if (Disconnected_FC_share == 0 and Disconnected_Boiler_BG_share == 0 and Disconnected_GHP_share != 0 and Disconnected_Boiler_NG_share != 0):
                        Disconnected_Boiler_NG_capacity_W = dfBest["Nominal Power"].iloc[0] / Disconnected_Boiler_NG_share
                        Disconnected_GHP_capacity_W = dfBest["Nominal Power"].iloc[0] / Disconnected_GHP_share

                    disconnected_capacity = dict(building_name=building_names[i],
                                                 Disconnected_Boiler_BG_share=Disconnected_Boiler_BG_share,
                                                 Disconnected_Boiler_BG_capacity_W=Disconnected_Boiler_BG_capacity_W,
                                                 Disconnected_Boiler_NG_share=Disconnected_Boiler_NG_share,
                                                 Disconnected_Boiler_NG_capacity_W=Disconnected_Boiler_NG_capacity_W,
                                                 Disconnected_FC_share=Disconnected_FC_share,
                                                 Disconnected_FC_capacity_W=Disconnected_FC_capacity_W,
                                                 Disconnected_GHP_share=Disconnected_GHP_share,
                                                 Disconnected_GHP_capacity_W=Disconnected_GHP_capacity_W)
                else:
                    disconnected_capacity = dict(building_name=building_names[i],
                                                 Disconnected_Boiler_BG_share=Disconnected_Boiler_BG_share,
                                                 Disconnected_Boiler_BG_capacity_W=Disconnected_Boiler_BG_capacity_W,
                                                 Disconnected_Boiler_NG_share=Disconnected_Boiler_NG_share,
                                                 Disconnected_Boiler_NG_capacity_W=Disconnected_Boiler_NG_capacity_W,
                                                 Disconnected_FC_share=Disconnected_FC_share,
                                                 Disconnected_FC_capacity_W=Disconnected_FC_capacity_W,
                                                 Disconnected_GHP_share=Disconnected_GHP_share,
                                                 Disconnected_GHP_capacity_W=Disconnected_GHP_capacity_W)

                intermediate_capacities.append(disconnected_capacity)
            disconnected_capacities.append(dict(network=network, disconnected_capacity=intermediate_capacities))

        # Based on the slave data, capacities corresponding to the centralized network are calculated in the following
        # script. Note that irrespective of the number of technologies used in an individual, the length of the dict
        # is constant
        for i, ind in enumerate(slavedata_list):
            if ind.Furn_Moist_type == "wet":
                Furnace_wet = ind.Furnace_on
                Furnace_wet_capacity_W = ind.Furnace_Q_max
            elif ind.Furn_Moist_type == "dry":
                Furnace_dry = ind.Furnace_on
                Furnace_dry_capacity_W = ind.Furnace_Q_max
            if ind.gt_fuel == "NG":
                CHP_NG = ind.CC_on
                CHP_NG_capacity_W = ind.CC_GT_SIZE
                Base_boiler_NG = ind.Boiler_on
                Base_boiler_NG_capacity_W = ind.Boiler_Q_max
                Peak_boiler_NG = ind.BoilerPeak_on
                Peak_boiler_NG_capacity_W = ind.BoilerPeak_Q_max
            elif ind.gt_fuel == "BG":
                CHP_BG = ind.CC_on
                CHP_BG_capacity_W = ind.CC_GT_SIZE
                Base_boiler_BG = ind.Boiler_on
                Base_boiler_BG_capacity_W = ind.Boiler_Q_max
                Peak_boiler_BG = ind.BoilerPeak_on
                Peak_boiler_BG_capacity_W = ind.BoilerPeak_Q_max

            HP_Lake = ind.HP_Lake_on
            HP_Lake_capacity_W = ind.HPLake_maxSize
            HP_Sewage = ind.HP_Sew_on
            HP_Sewage_capacity_W = ind.HPSew_maxSize
            GHP = ind.GHP_on
            GHP_capacity_W = ind.GHP_number * GHP_HmaxSize
            PV = pop[i][nHeat * 2 + nHR]
            PV_capacity_W = ind.SOLAR_PART_PV * solar_features.A_PV_m2 * nPV * 1000
            PVT = pop[i][nHeat * 2 + nHR + 2]
            PVT_capacity_W = ind.SOLAR_PART_PVT * solar_features.A_PVT_m2 * nPVT * 1000
            SC = pop[i][nHeat * 2 + nHR + 4]
            SC_capacity_W = ind.SOLAR_PART_SC * solar_features.A_SC_m2 * 1000
            print (1)
            capacity = dict(ind=i, generation=genCP,
                            Furnace_wet=Furnace_wet, Furnace_wet_capacity_W=Furnace_wet_capacity_W,
                            Furnace_dry=Furnace_dry, Furnace_dry_capacity_W=Furnace_dry_capacity_W,
                            CHP_NG=CHP_NG, CHP_NG_capacity_W=CHP_NG_capacity_W,
                            CHP_BG=CHP_BG, CHP_BG_capacity_W=CHP_BG_capacity_W,
                            Base_boiler_BG=Base_boiler_BG, Base_boiler_BG_capacity_W=Base_boiler_BG_capacity_W,
                            Base_boiler_NG=Base_boiler_NG, Base_boiler_NG_capacity_W=Base_boiler_NG_capacity_W,
                            Peak_boiler_BG=Peak_boiler_BG, Peak_boiler_BG_capacity_W=Peak_boiler_BG_capacity_W,
                            Peak_boiler_NG=Peak_boiler_NG, Peak_boiler_NG_capacity_W=Peak_boiler_NG_capacity_W,
                            HP_Lake=HP_Lake, HP_Lake_capacity_W=HP_Lake_capacity_W,
                            HP_Sewage=HP_Sewage, HP_Sewage_capacity_W=HP_Sewage_capacity_W,
                            GHP=GHP, GHP_capacity_W=GHP_capacity_W,
                            PV=PV, PV_capacity_W=PV_capacity_W,
                            PVT=PVT, PVT_capacity_W=PVT_capacity_W,
                            SC=SC, SC_capacity_W=SC_capacity_W)
            capacities.append(capacity)
        # Save initial population
        print "Save Initial population \n"

        with open(locator.get_optimization_checkpoint_initial(),"wb") as fp:
            cp = dict(population=pop, generation=0, networkList=ntwList, epsIndicator=[], testedPop=[],
                      population_fitness=fitnesses, capacities=capacities, disconnected_capacities=disconnected_capacities,
                      halloffame=halloffame, halloffame_fitness=halloffame_fitness)
            json.dump(cp, fp)

    else:
        print "Recover from CP " + str(genCP) + "\n"
        # import the checkpoint based on the genCP
        with open(locator.get_optimization_checkpoint(genCP), "rb") as fp:
            cp = json.load(fp)
            pop = toolbox.population(n=config.optimization.initialind)
            for i in xrange(len(pop)):
                for j in xrange(len(pop[i])):
                    pop[i][j] = cp['population'][i][j]
            ntwList = ntwList
            epsInd = cp["epsIndicator"]

            for ind in pop:
                evaluation.checkNtw(ind, ntwList, locator, gv, config)

            for i, ind in enumerate(pop):
                a = objective_function(ind)
                costs_list.append(a[0])
                co2_list.append(a[1])
                prim_list.append(a[2])
                slavedata_list.append(a[3])

            for i in range(len(costs_list)):
                fitnesses.append([costs_list[i], co2_list[i], prim_list[i]])

            # linking every individual with the corresponding fitness, this also keeps a track of the number of function
            # evaluations. This can further be used as a stopping criteria in future
            for ind, fit in zip(pop, fitnesses):
                ind.fitness.values = fit
                function_evals = function_evals + 1  # keeping track of number of function evaluations

    proba, sigmap = PROBA, SIGMAP

    # variables used for generating graphs
    # graphs are being generated for every generation, it is shown in 2D plot with colorscheme for the 3rd objective
    xs = [((objectives[0])) for objectives in fitnesses]  # Costs
    ys = [((objectives[1])) for objectives in fitnesses]  # GHG emissions
    zs = [((objectives[2])) for objectives in fitnesses]  # MJ

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
    plt.savefig(os.path.join(locator.get_plots_folder(), "pareto_" + str(genCP) + ".png"))
    plt.clf()

    # Evolution starts !

    g = genCP
    stopCrit = False # Threshold for the Epsilon indicator, Not used

    while g < config.optimization.ngen and not stopCrit and ( time.clock() - t0 ) < config.optimization.maxtime :

        # Initialization of variables
        ntwList = ["1" * nBuildings]
        costs_list = []
        co2_list = []
        prim_list = []
        costs_list_invalid_ind = []
        co2_list_invalid_ind = []
        prim_list_invalid_ind = []
        slavedata_list_invalid_ind = []
        fitnesses_invalid_ind = []
        capacities = []
        disconnected_capacities = []
        Furnace_wet = 0
        Furnace_wet_capacity_W = 0
        Furnace_dry = 0
        Furnace_dry_capacity_W = 0
        CHP_NG = 0
        CHP_NG_capacity_W = 0
        CHP_BG = 0
        CHP_BG_capacity_W = 0
        Base_boiler_BG = 0
        Base_boiler_BG_capacity_W = 0
        Base_boiler_NG = 0
        Base_boiler_NG_capacity_W = 0
        Peak_boiler_BG = 0
        Peak_boiler_BG_capacity_W = 0
        Peak_boiler_NG = 0
        Peak_boiler_NG_capacity_W = 0
        HP_Lake = 0
        HP_Lake_capacity_W = 0
        HP_Sewage = 0
        HP_Sewage_capacity_W = 0
        GHP = 0
        GHP_capacity_W = 0
        PV = 0
        PV_capacity_W = 0
        PVT = 0
        PVT_capacity_W = 0
        SC = 0
        SC_capacity_W = 0

        g += 1
        print "Generation", g
        offspring = list(pop)

        # costs_list updates the costs involved in every individual
        # co2_list updates the GHG emissions in terms of CO2
        # prim_list updates the primary energy  corresponding to every individual
        # slavedata_list updates the master_to_slave variables corresponding to every individual. This is used in
        # calculating the capacities of both the centralized and the decentralized system
        for i, ind in enumerate(pop):
            a = ind.fitness.values
            costs_list.append(a[0])
            co2_list.append(a[1])
            prim_list.append(a[2])

        # slavedata_list is initiated at the generation 0 or regenerated when started from a checkpoint
        # this is further used in the first generation from genCP. For the second generation, the slave data of the
        # selected individuals is to be used and this piece of code does this
        if len(slavedata_list) == 0:
            slavedata_list = slavedata_selected

        # Apply crossover and mutation on the pop
        for ind1, ind2 in zip(pop[::2], pop[1::2]):
            child1, child2 = cx.cxUniform(ind1, ind2, proba)
            offspring += [child1, child2]

        for mutant in pop:
            mutant = mut.mutFlip(mutant, proba)
            mutant = mut.mutShuffle(mutant, proba)
            offspring.append(mut.mutGU(mutant, proba))

        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        for ind in invalid_ind:
            evaluation.checkNtw(ind, ntwList, locator, gv, config)

        for i, ind in enumerate(invalid_ind):
            a = objective_function(ind)
            costs_list_invalid_ind.append(a[0])
            co2_list_invalid_ind.append(a[1])
            prim_list_invalid_ind.append(a[2])
            slavedata_list_invalid_ind.append(a[3])

        for i in range(len(invalid_ind)):
            fitnesses_invalid_ind.append([costs_list_invalid_ind[i], co2_list_invalid_ind[i], prim_list_invalid_ind[i]])

        for ind, fit in zip(invalid_ind, fitnesses_invalid_ind):
            ind.fitness.values = fit
            function_evals = function_evals + 1  # keeping track of number of function evaluations

        pop_compiled = pop
        for i in range(len(invalid_ind)):
            pop_compiled.append(invalid_ind[i])
        slavedata_compiled = slavedata_list
        for i in range(len(slavedata_list_invalid_ind)):
            slavedata_compiled.append(slavedata_list_invalid_ind[i])
        slavedata_selected = []

        # Select the Pareto Optimal individuals
        selection = sel.selectPareto(offspring, config.optimization.initialind)
        fitnesses = []
        for ind in selection:
            fitnesses.append(ind.fitness.values)
        for ind in selection:
            for i in range(len(pop_compiled)):
                if ind == pop_compiled[i]:
                    slavedata_selected.append(slavedata_compiled[i])

        if len(halloffame) <= halloffame_size:
            halloffame.extend(selection)
        else:
            halloffame.extend(selection)
            halloffame = sel.selectPareto(halloffame, halloffame_size)

        for ind in halloffame:
            halloffame_fitness.append(ind.fitness.values)

        # Compute the epsilon criteria [and check the stopping criteria]
        epsInd.append(evaluation.epsIndicator(pop, selection))
        # compute the optimization metrics for every front apart from generation 0
        euclidean_distance, spread = convergence_metric(pop, selection, normalization)
        #if len(epsInd) >1:
        #    eta = (epsInd[-1] - epsInd[-2]) / epsInd[-2]
        #    if eta < gv.epsMargin:
        #        stopCrit = True

        # The population is entirely replaced by the best individuals

        pop[:] = selection

        # this is done to ensure the ntwList has the same list as the selected pop instead of tested pop
        ntwList = ["1" * nBuildings]
        for ind in pop:
            indCombi = sFn.individual_to_barcode(ind)
            ntwList.append(indCombi)

        ntwList = ntwList[1:]  # done to remove the first individual, which is used for initiation

        # disconnected building capacity is calculated from the networklist of every individual
        # disconnected building have four energy technologies namely Bio-gas Boiler, Natural-gas Boiler, Fuel Cell
        # and Geothermal heat pumps
        # These values are already calculated in 'decentralized_main.py'. This piece of script gets these values from
        # the already created csv files
        for (index, network) in enumerate(ntwList):
            intermediate_capacities = []
            for i in range(len(network)):

                Disconnected_Boiler_BG_share = 0
                Disconnected_Boiler_BG_capacity_W = 0
                Disconnected_Boiler_NG_share = 0
                Disconnected_Boiler_NG_capacity_W = 0
                Disconnected_FC_share = 0
                Disconnected_FC_capacity_W = 0
                Disconnected_GHP_share = 0
                Disconnected_GHP_capacity_W = 0

                if network[i] == "0":
                    df = pd.read_csv(locator.get_optimization_disconnected_folder_building_result(building_names[i]))
                    dfBest = df[df["Best configuration"] == 1]
                    Disconnected_Boiler_BG_share = dfBest["BoilerBG Share"].iloc[0]
                    Disconnected_Boiler_NG_share = dfBest["BoilerNG Share"].iloc[0]
                    Disconnected_FC_share = dfBest["FC Share"].iloc[0]
                    Disconnected_GHP_share = dfBest["GHP Share"].iloc[0]

                    if Disconnected_Boiler_BG_share == 1:
                        Disconnected_Boiler_BG_capacity_W = dfBest["Nominal Power"].iloc[0]

                    if Disconnected_Boiler_NG_share == 1:
                        Disconnected_Boiler_NG_capacity_W = dfBest["Nominal Power"].iloc[0]

                    if Disconnected_FC_share == 1:
                        Disconnected_FC_capacity_W = dfBest["Nominal Power"].iloc[0]

                    if Disconnected_GHP_share == 1:
                        Disconnected_GHP_capacity_W = dfBest["Nominal Power"].iloc[0]

                    if (Disconnected_FC_share == 0 and Disconnected_Boiler_BG_share == 0 and Disconnected_GHP_share != 0 and Disconnected_Boiler_NG_share != 0):
                        Disconnected_Boiler_NG_capacity_W = dfBest["Nominal Power"].iloc[0] / Disconnected_Boiler_NG_share
                        Disconnected_GHP_capacity_W = dfBest["Nominal Power"].iloc[0] / Disconnected_GHP_share

                    disconnected_capacity = dict(building_name=building_names[i],
                                                 Disconnected_Boiler_BG_share=Disconnected_Boiler_BG_share,
                                                 Disconnected_Boiler_BG_capacity_W=Disconnected_Boiler_BG_capacity_W,
                                                 Disconnected_Boiler_NG_share=Disconnected_Boiler_NG_share,
                                                 Disconnected_Boiler_NG_capacity_W=Disconnected_Boiler_NG_capacity_W,
                                                 Disconnected_FC_share=Disconnected_FC_share,
                                                 Disconnected_FC_capacity_W=Disconnected_FC_capacity_W,
                                                 Disconnected_GHP_share=Disconnected_GHP_share,
                                                 Disconnected_GHP_capacity_W=Disconnected_GHP_capacity_W)
                else:
                    disconnected_capacity = dict(building_name=building_names[i],
                                                 Disconnected_Boiler_BG_share=Disconnected_Boiler_BG_share,
                                                 Disconnected_Boiler_BG_capacity_W=Disconnected_Boiler_BG_capacity_W,
                                                 Disconnected_Boiler_NG_share=Disconnected_Boiler_NG_share,
                                                 Disconnected_Boiler_NG_capacity_W=Disconnected_Boiler_NG_capacity_W,
                                                 Disconnected_FC_share=Disconnected_FC_share,
                                                 Disconnected_FC_capacity_W=Disconnected_FC_capacity_W,
                                                 Disconnected_GHP_share=Disconnected_GHP_share,
                                                 Disconnected_GHP_capacity_W=Disconnected_GHP_capacity_W)

                intermediate_capacities.append(disconnected_capacity)
            disconnected_capacities.append(dict(network=network, disconnected_capacity=intermediate_capacities))

        # Based on the slave data, capacities corresponding to the centralized network are calculated in the following
        # script. Note that irrespective of the number of technologies used in an individual, the length of the dict
        # is constant
        for i, ind in enumerate(slavedata_selected):
            if ind.Furn_Moist_type == "wet":
                Furnace_wet = ind.Furnace_on
                Furnace_wet_capacity_W = ind.Furnace_Q_max
            elif ind.Furn_Moist_type == "dry":
                Furnace_dry = ind.Furnace_on
                Furnace_dry_capacity_W = ind.Furnace_Q_max
            if ind.gt_fuel == "NG":
                CHP_NG = ind.CC_on
                CHP_NG_capacity_W = ind.CC_GT_SIZE
                Base_boiler_NG = ind.Boiler_on
                Base_boiler_NG_capacity_W = ind.Boiler_Q_max
                Peak_boiler_NG = ind.BoilerPeak_on
                Peak_boiler_NG_capacity_W = ind.BoilerPeak_Q_max
            elif ind.gt_fuel == "BG":
                CHP_BG = ind.CC_on
                CHP_BG_capacity_W = ind.CC_GT_SIZE
                Base_boiler_BG = ind.Boiler_on
                Base_boiler_BG_capacity_W = ind.Boiler_Q_max
                Peak_boiler_BG = ind.BoilerPeak_on
                Peak_boiler_BG_capacity_W = ind.BoilerPeak_Q_max

            HP_Lake = ind.HP_Lake_on
            HP_Lake_capacity_W = ind.HPLake_maxSize
            HP_Sewage = ind.HP_Sew_on
            HP_Sewage_capacity_W = ind.HPSew_maxSize
            GHP = ind.GHP_on
            GHP_capacity_W = ind.GHP_number * GHP_HmaxSize
            PV = invalid_ind[i][nHeat * 2 + nHR]
            PV_capacity_W = ind.SOLAR_PART_PV * solar_features.A_PV_m2 * nPV * 1000
            PVT = invalid_ind[i][nHeat * 2 + nHR + 2]
            PVT_capacity_W = ind.SOLAR_PART_PVT * solar_features.A_PVT_m2 * nPVT * 1000
            SC = invalid_ind[i][nHeat * 2 + nHR + 4]
            SC_capacity_W = ind.SOLAR_PART_SC * solar_features.A_SC_m2 * 1000
            capacity = dict(ind=i, generation=genCP,
                            Furnace_wet=Furnace_wet, Furnace_wet_capacity_W=Furnace_wet_capacity_W,
                            Furnace_dry=Furnace_dry, Furnace_dry_capacity_W=Furnace_dry_capacity_W,
                            CHP_NG=CHP_NG, CHP_NG_capacity_W=CHP_NG_capacity_W,
                            CHP_BG=CHP_BG, CHP_BG_capacity_W=CHP_BG_capacity_W,
                            Base_boiler_BG=Base_boiler_BG, Base_boiler_BG_capacity_W=Base_boiler_BG_capacity_W,
                            Base_boiler_NG=Base_boiler_NG, Base_boiler_NG_capacity_W=Base_boiler_NG_capacity_W,
                            Peak_boiler_BG=Peak_boiler_BG, Peak_boiler_BG_capacity_W=Peak_boiler_BG_capacity_W,
                            Peak_boiler_NG=Peak_boiler_NG, Peak_boiler_NG_capacity_W=Peak_boiler_NG_capacity_W,
                            HP_Lake=HP_Lake, HP_Lake_capacity_W=HP_Lake_capacity_W,
                            HP_Sewage=HP_Sewage, HP_Sewage_capacity_W=HP_Sewage_capacity_W,
                            GHP=GHP, GHP_capacity_W=GHP_capacity_W,
                            PV=PV, PV_capacity_W=PV_capacity_W,
                            PVT=PVT, PVT_capacity_W=PVT_capacity_W,
                            SC=SC, SC_capacity_W=SC_capacity_W)
            capacities.append(capacity)

        xs = [((objectives[0]) / 10 ** 6) for objectives in fitnesses]  # Costs
        ys = [((objectives[1]) / 10 ** 6) for objectives in fitnesses]  # GHG emissions
        zs = [((objectives[2]) / 10 ** 6) for objectives in fitnesses]  # MJ

        # plot showing the Pareto front of every generation

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
        plt.savefig(os.path.join(locator.get_plots_folder(), "pareto_" + str(g) + ".png"))
        plt.clf()

        # Create Checkpoint if necessary
        if g % config.optimization.fcheckpoint == 0:
            print "Create CheckPoint", g, "\n"
            with open(locator.get_optimization_checkpoint(g), "wb") as fp:
                cp = dict(population=pop, generation=g, networkList=ntwList, epsIndicator=epsInd, testedPop=invalid_ind,
                          population_fitness=fitnesses, capacities=capacities, disconnected_capacities=disconnected_capacities,
                          halloffame=halloffame, halloffame_fitness=halloffame_fitness,
                          euclidean_distance=euclidean_distance, spread=spread)
                json.dump(cp, fp)
        slavedata_list = [] # reinitializing to avoid really long lists, as this keeps appending

    if g == config.optimization.ngen:
        print "Final Generation reached"
    else:
        print "Stopping criteria reached"

    # Saving the final results
    print "Save final results. " + str(len(pop)) + " individuals in final population"
    print "Epsilon indicator", epsInd, "\n"
    with open(locator.get_optimization_checkpoint_final(), "wb") as fp:
        cp = dict(population=pop, generation=g, networkList=ntwList, epsIndicator=epsInd, testedPop=invalid_ind,
                  population_fitness=fitnesses, capacities=capacities, disconnected_capacities=disconnected_capacities,
                  halloffame=halloffame, halloffame_fitness=halloffame_fitness,
                  euclidean_distance=euclidean_distance, spread=spread)
        json.dump(cp, fp)

    print "Master Work Complete \n"
    print ("Number of function evaluations = " + str(function_evals))
    
    return pop, epsInd

def convergence_metric(old_front, new_front, normalization):
    #  This function calculates the metrics corresponding to a Pareto-front
    #  combined_euclidean_distance calculates the euclidean distance between the current front and the previous one
    #  it is done by locating the choosing a point on current front and the closest point in the previous front and
    #  calculating normalized euclidean distance

    #  Spread discusses on the spread of the Pareto-front, i.e. how evenly the Pareto front is spaced. This is calculated
    #  by identifying the closest neighbour to a point on the Pareto-front. Distance to each closest neighbour is then
    #  subtracted by the mean distance for all the points on the Pareto-front (i.e. closest neighbors for all points).
    #  The ideal value for this is to be 'zero'

    combined_euclidean_distance = 0

    for indNew in new_front:

        (aNew, bNew, cNew) = indNew.fitness.values
        distance = []
        for i, indOld in enumerate(old_front):
            (aOld, bOld, cOld) = indOld.fitness.values
            distance.append(np.sqrt(((aNew - aOld) / normalization[0])**2 + ((bNew - bOld) / normalization[1])**2 +
                                    ((cNew - cOld) / normalization[2])**2))

        combined_euclidean_distance = combined_euclidean_distance + min(distance)

    combined_euclidean_distance = (combined_euclidean_distance) / (len(new_front))

    spread = []
    nearest_neighbor = []

    for i, ind_i in enumerate(new_front):
        spread_i = []
        (cost_i, co2_i, eprim_i) = ind_i.fitness.values
        for j, ind_j in enumerate(new_front):
            (cost_j, co2_j, eprim_j) = ind_j.fitness.values
            if i != j:
                spread.append(np.sqrt(((cost_i - cost_j) / normalization[0])**2 + ((co2_i - co2_j) / normalization[1])**2 +
                                    ((eprim_i - eprim_j) / normalization[2])**2))
                spread_i.append(np.sqrt(((cost_i - cost_j) / normalization[0]) ** 2 + ((co2_i - co2_j) / normalization[1]) ** 2 +
                            ((eprim_i - eprim_j) / normalization[2]) ** 2))

        nearest_neighbor.append(min(spread_i))
    average_spread = np.mean(spread)

    nearest_neighbor = [abs(x - average_spread) for x in nearest_neighbor]

    spread_final = np.sum(nearest_neighbor)

    print ('combined euclidean distance = ' + str(combined_euclidean_distance))
    print ('spread = ' + str(spread_final))

    return combined_euclidean_distance, spread_final




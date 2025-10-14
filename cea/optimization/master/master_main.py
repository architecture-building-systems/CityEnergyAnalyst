import json
import multiprocessing
import random
import warnings
from itertools import repeat
from math import factorial
from math import sqrt

import numpy as np
import pandas as pd
from deap import algorithms
from deap import tools, base

from cea.optimization.constants import DH_CONVERSION_TECHNOLOGIES_SHARE, DC_CONVERSION_TECHNOLOGIES_SHARE, DH_ACRONYM, \
    DC_ACRONYM
from cea.optimization.master import evaluation
from cea.optimization.master.crossover import crossover_main
from cea.optimization.master.data_saver import save_results
from cea.optimization.master.generation import generate_main
from cea.optimization.master.generation import individual_to_barcode
from cea.optimization.master.mutations import mutation_main
from cea.optimization.master.normalization import scaler_for_normalization, normalize_fitnesses
from cea.optimization.master.optimisation_individual import Individual, FitnessMin

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

warnings.filterwarnings("ignore")


def objective_function(individual,
                       individual_number,
                       generation_number,
                       objective_function_selection,
                       building_names_all,
                       column_names_buildings_heating,
                       column_names_buildings_cooling,
                       building_names_heating,
                       building_names_cooling,
                       building_names_electricity,
                       locator,
                       network_features,
                       weather_features,
                       config,
                       prices,
                       lca,
                       district_heating_network,
                       district_cooling_network,
                       technologies_heating_allowed,
                       technologies_cooling_allowed,
                       column_names,
                       print_final_results=False):
    """
    Objective function is used to calculate and return the costs, CO2, system energy demand and heat release and
    simultaneously store all other variables corresponding to the individual.

    :param individual: Input individual
    :param individual_number: unique identifier of the individual in that generation
    :param generation_number: unique identifier of the generation in this optimization run
    :param building_names_all: names of buildings in the analysed district
    :param column_names_buildings_heating: names of all buildings that are connected to a district heating system
    :param column_names_buildings_cooling: names of all buildings that are connected to a district cooling system
    :param building_names_heating: names of all buildings that have a heating load (space heat, hot water etc.)
    :param building_names_cooling: names of all buildings that have a cooling load
    :param building_names_electricity: names of all buildings that have an electricity load
    :param locator: paths to cea input files
    :param network_features: characteristic parameters (pumping energy, mass flow rate, thermal losses & piping cost)
                             of the district cooling/heating network
    :param weather_features: weather data for the selected location (ambient temperature, ground temperature etc.)
    :param config: configurations of cea
    :param prices: catalogue of energy prices (e.g. for natural gas, electricity, biomass etc.)
    :param lca: catalogue of emission intensities of energy carriers
    :param district_heating_network: indicator defining if district heating networks should be analyzed
    :param district_cooling_network: indicator defining if district heating networks should be analyzed
    :param technologies_heating_allowed: district heating technologies to be considered in the optimization
    :param technologies_cooling_allowed: district cooling technologies to be considered in the optimization
    :param column_names: description of the parameter list in the individual
    :param print_final_results: indicator defining if evaluation results for the individual should be saved

    :type individual: list
    :type individual_number: int
    :type generation_number: int
    :type building_names_all: list of str
    :type column_names_buildings_heating: list of str
    :type column_names_buildings_cooling: list of str
    :type building_names_heating: list of str
    :type building_names_cooling: list of str
    :type building_names_electricity: list of str
    :type locator: cea.inputlocator.InputLocator class object
    :type network_features: cea.optimization.distribution.network_optimization_features.NetworkOptimizationFeatures
                            class object
    :type weather_features: cea.optimization.preprocessing.preprocessing_main.WeatherFeatures class object
    :type config: cea.config.Configuration class object
    :type prices: cea.optimization.prices.Prices class object
    :type lca: cea.optimization.lca_calculations.LcaCalculations class object
    :type district_heating_network: bool
    :type district_cooling_network: bool
    :type technologies_heating_allowed: list of str
    :type technologies_cooling_allowed: list of str
    :type column_names: list of str
    :type print_final_results: bool

    :return dict objective_function_results
    """
    print('cea optimization progress: individual ' + str(individual_number) + ' and generation ' + str(
        generation_number) + '/' + str(config.optimization.number_of_generations))

    TAC_sys_USD, \
    GHG_sys_tonCO2, \
    HR_sys_MWh, \
    SED_sys_MWh, \
    buildings_district_scale_costs, \
    buildings_district_scale_emissions, \
    buildings_district_scale_heat, \
    buildings_district_scale_sed, \
    buildings_building_scale_costs, \
    buildings_building_scale_emissions, \
    buildings_building_scale_heat, \
    buildings_building_scale_sed, \
    district_heating_generation_dispatch, \
    district_cooling_generation_dispatch, \
    district_electricity_dispatch, \
    district_electricity_demands, \
    performance_totals, \
    building_connectivity_dict, \
    district_heating_capacity_installed, \
    district_cooling_capacity_installed, \
    district_electricity_capacity_installed, \
    buildings_building_scale_heating_capacities, \
    buildings_building_scale_cooling_capacities = evaluation.evaluation_main(individual,
                                                                             building_names_all,
                                                                             locator,
                                                                             network_features,
                                                                             weather_features,
                                                                             config,
                                                                             prices, lca,
                                                                             individual_number,
                                                                             generation_number,
                                                                             column_names,
                                                                             column_names_buildings_heating,
                                                                             column_names_buildings_cooling,
                                                                             building_names_heating,
                                                                             building_names_cooling,
                                                                             building_names_electricity,
                                                                             district_heating_network,
                                                                             district_cooling_network,
                                                                             technologies_heating_allowed,
                                                                             technologies_cooling_allowed,
                                                                             )

    objective_function_results = []
    objective_function_handles = ["cost", "GHG_emissions", "system_energy_demand", "anthropogenic_heat"]

    if objective_function_handles[0] in objective_function_selection:
        objective_function_results.append(TAC_sys_USD)
    if objective_function_handles[1] in objective_function_selection:
        objective_function_results.append(GHG_sys_tonCO2)
    if objective_function_handles[2] in objective_function_selection:
        objective_function_results.append(HR_sys_MWh)
    if objective_function_handles[3] in objective_function_selection:
        objective_function_results.append(SED_sys_MWh)

    if config.debug or print_final_results:  # print for the last generation and
        print("SAVING RESULTS TO DISK")
        save_results(locator,
                     weather_features.date,
                     individual_number,
                     generation_number,
                     buildings_district_scale_costs,
                     buildings_district_scale_emissions,
                     buildings_district_scale_heat,
                     buildings_district_scale_sed,
                     buildings_building_scale_costs,
                     buildings_building_scale_emissions,
                     buildings_building_scale_heat,
                     buildings_building_scale_sed,
                     district_heating_generation_dispatch,
                     district_cooling_generation_dispatch,
                     district_electricity_dispatch,
                     district_electricity_demands,
                     performance_totals,
                     building_connectivity_dict,
                     district_heating_capacity_installed,
                     district_cooling_capacity_installed,
                     district_electricity_capacity_installed,
                     buildings_building_scale_heating_capacities,
                     buildings_building_scale_cooling_capacities)

    return objective_function_results


def objective_function_wrapper(args):
    """
    Wrap arguments because multiprocessing only accepts one argument for the function"""
    return objective_function(*args)


def calc_dictionary_of_all_individuals_tested(dictionary_individuals, gen, invalid_ind):
    dictionary_individuals['generation'].extend([gen] * len(invalid_ind))
    dictionary_individuals['individual_id'].extend(range(len(invalid_ind)))
    dictionary_individuals['individual_code'].extend(invalid_ind)
    return dictionary_individuals


def non_dominated_sorting_genetic_algorithm(locator,
                                            building_names_all,
                                            district_heating_network,
                                            district_cooling_network,
                                            building_names_heating,
                                            building_names_cooling,
                                            building_names_electricity,
                                            network_features,
                                            weather_features,
                                            config,
                                            prices,
                                            lca):
    # LOCAL VARIABLES
    NGEN = config.optimization.number_of_generations  # number of generations
    MU = config.optimization.population_size  # int(H + (4 - H % 4)) # number of individuals to select
    RANDOM_SEED = config.optimization.random_seed
    CXPB = config.optimization.crossover_prob
    MUTPB = config.optimization.mutation_prob
    technologies_heating_allowed = config.optimization.technologies_DH
    technologies_cooling_allowed = config.optimization.technologies_DC
    mutation_method_integer = config.optimization.mutation_method_integer
    mutation_method_continuous = config.optimization.mutation_method_continuous
    crossover_method_integer = config.optimization.crossover_method_integer
    crossover_method_continuous = config.optimization.crossover_method_continuous

    # SET-UP EVOLUTIONARY ALGORITHM
    # Adapt the conversion classes to the current config (for cases where dashboard is used)
    FitnessMin.set_objective_function_selection(config)
    NOBJ = FitnessMin.nbr_of_objectives
    objective_function_selection = FitnessMin.objective_function_selection
    # Hyperparameters
    P = 12
    ref_points = tools.uniform_reference_points(NOBJ, P)
    if MU is None:
        H = factorial(NOBJ + P - 1) / (factorial(P) * factorial(NOBJ - 1))
        MU = int(H + (4 - H % 4))
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    # SET-UP INDIVIDUAL STRUCTURE INCLUDING HOW EVERY POINT IS CALLED (COLUM_NAMES)
    column_names, \
    heating_unit_names_share, \
    cooling_unit_names_share, \
    column_names_buildings_heating, \
    column_names_buildings_cooling = get_column_names_individual(district_heating_network,
                                                                 district_cooling_network,
                                                                 building_names_heating,
                                                                 building_names_cooling,
                                                                 technologies_heating_allowed,
                                                                 technologies_cooling_allowed,
                                                                 )
    individual_with_names_dict = create_empty_individual(column_names,
                                                         column_names_buildings_heating,
                                                         column_names_buildings_cooling,
                                                         district_heating_network,
                                                         district_cooling_network,
                                                         technologies_heating_allowed,
                                                         technologies_cooling_allowed,
                                                         )

    # DEAP LIBRARY REFERENCE_POINT CLASSES AND TOOLS
    # reference points
    toolbox = base.Toolbox()
    toolbox.register("generate",
                     generate_main,
                     individual_with_names_dict=individual_with_names_dict,
                     column_names=column_names,
                     column_names_buildings_heating=column_names_buildings_heating,
                     column_names_buildings_cooling=column_names_buildings_cooling,
                     district_heating_network=district_heating_network,
                     district_cooling_network=district_cooling_network,
                     technologies_heating_allowed=technologies_heating_allowed,
                     technologies_cooling_allowed=technologies_cooling_allowed,
                     )
    toolbox.register("individual",
                     tools.initIterate,
                     Individual,
                     toolbox.generate)
    toolbox.register("population",
                     tools.initRepeat,
                     list,
                     toolbox.individual)
    toolbox.register("mate",
                     crossover_main,
                     indpb=CXPB,
                     column_names=column_names,
                     heating_unit_names_share=heating_unit_names_share,
                     cooling_unit_names_share=cooling_unit_names_share,
                     column_names_buildings_heating=column_names_buildings_heating,
                     column_names_buildings_cooling=column_names_buildings_cooling,
                     district_heating_network=district_heating_network,
                     district_cooling_network=district_cooling_network,
                     technologies_heating_allowed=technologies_heating_allowed,
                     technologies_cooling_allowed=technologies_cooling_allowed,
                     crossover_method_integer=crossover_method_integer,
                     crossover_method_continuous=crossover_method_continuous)
    toolbox.register("mutate",
                     mutation_main,
                     indpb=MUTPB,
                     column_names=column_names,
                     heating_unit_names_share=heating_unit_names_share,
                     cooling_unit_names_share=cooling_unit_names_share,
                     column_names_buildings_heating=column_names_buildings_heating,
                     column_names_buildings_cooling=column_names_buildings_cooling,
                     district_heating_network=district_heating_network,
                     district_cooling_network=district_cooling_network,
                     technologies_heating_allowed=technologies_heating_allowed,
                     technologies_cooling_allowed=technologies_cooling_allowed,
                     mutation_method_integer=mutation_method_integer,
                     mutation_method_continuous=mutation_method_continuous
                     )
    toolbox.register("evaluate",
                     objective_function_wrapper)
    toolbox.register("select",
                     tools.selNSGA3WithMemory(ref_points))

    # configure multiprocessing
    if config.multiprocessing:
        pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
        toolbox.register("map", pool.map)

    # Initialize statistics object
    paretofrontier = tools.ParetoFront()
    generational_distances = []
    difference_generational_distances = []
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean, axis=0)
    stats.register("std", np.std, axis=0)
    stats.register("min", np.min, axis=0)
    stats.register("max", np.max, axis=0)

    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "std", "min", "avg", "max"

    pop = toolbox.population(n=MU)

    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in pop if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, zip(invalid_ind,
                                                  range(len(invalid_ind)),
                                                  repeat(0, len(invalid_ind)),
                                                  repeat(objective_function_selection, len(invalid_ind)),
                                                  repeat(building_names_all, len(invalid_ind)),
                                                  repeat(column_names_buildings_heating, len(invalid_ind)),
                                                  repeat(column_names_buildings_cooling, len(invalid_ind)),
                                                  repeat(building_names_heating, len(invalid_ind)),
                                                  repeat(building_names_cooling, len(invalid_ind)),
                                                  repeat(building_names_electricity, len(invalid_ind)),
                                                  repeat(locator, len(invalid_ind)),
                                                  repeat(network_features, len(invalid_ind)),
                                                  repeat(weather_features, len(invalid_ind)),
                                                  repeat(config, len(invalid_ind)),
                                                  repeat(prices, len(invalid_ind)),
                                                  repeat(lca, len(invalid_ind)),
                                                  repeat(district_heating_network, len(invalid_ind)),
                                                  repeat(district_cooling_network, len(invalid_ind)),
                                                  repeat(technologies_heating_allowed, len(invalid_ind)),
                                                  repeat(technologies_cooling_allowed, len(invalid_ind)),
                                                  repeat(column_names, len(invalid_ind))))

    # normalization of the first generation
    fitnesses = list(fitnesses)  # fitnesses is a map object - store a copy for iterating over multiple times
    scaler_dict = scaler_for_normalization(NOBJ, fitnesses)
    fitnesses = normalize_fitnesses(scaler_dict, fitnesses)

    # add fitnesses to population individuals
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    # Compile statistics about the population
    record = stats.compile(pop)
    paretofrontier.update(pop)
    performance_metrics = calc_performance_metrics(0.0, paretofrontier)
    generational_distances.append(performance_metrics[0])
    difference_generational_distances.append(performance_metrics[1])
    logbook.record(gen=0, evals=len(invalid_ind), **record)

    # create a dictionary to store which individuals that are being calculated
    record_individuals_tested = {'generation': [], "individual_id": [], "individual_code": []}
    record_individuals_tested = calc_dictionary_of_all_individuals_tested(record_individuals_tested, gen=0,
                                                                          invalid_ind=invalid_ind)
    print(logbook.stream)

    # Begin the generational process
    # Initialization of variables
    for gen in range(1, NGEN + 1):
        print("Evaluating Generation %s of %s generations" % (gen, NGEN + 1))
        # Select and clone the next generation individuals
        offspring = algorithms.varAnd(pop, toolbox, CXPB, MUTPB)

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        invalid_ind = [ind for ind in invalid_ind if ind not in pop]
        fitnesses = toolbox.map(toolbox.evaluate,
                                zip(invalid_ind,
                                    range(len(invalid_ind)),
                                    repeat(gen, len(invalid_ind)),
                                    repeat(objective_function_selection, len(invalid_ind)),
                                    repeat(building_names_all, len(invalid_ind)),
                                    repeat(column_names_buildings_heating, len(invalid_ind)),
                                    repeat(column_names_buildings_cooling, len(invalid_ind)),
                                    repeat(building_names_heating, len(invalid_ind)),
                                    repeat(building_names_cooling, len(invalid_ind)),
                                    repeat(building_names_electricity, len(invalid_ind)),
                                    repeat(locator, len(invalid_ind)),
                                    repeat(network_features, len(invalid_ind)),
                                    repeat(weather_features, len(invalid_ind)),
                                    repeat(config, len(invalid_ind)),
                                    repeat(prices, len(invalid_ind)),
                                    repeat(lca, len(invalid_ind)),
                                    repeat(district_heating_network, len(invalid_ind)),
                                    repeat(district_cooling_network, len(invalid_ind)),
                                    repeat(technologies_heating_allowed, len(invalid_ind)),
                                    repeat(technologies_cooling_allowed, len(invalid_ind)),
                                    repeat(column_names, len(invalid_ind))))
        # normalization of the second generation on
        fitnesses = list(fitnesses)  # fitnesses is a map object - store a copy for iterating over multiple times
        fitnesses = normalize_fitnesses(scaler_dict, fitnesses)

        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # Select the next generation population from parents and offspring
        pop = toolbox.select(pop + invalid_ind, MU)

        # get paretofront and update dictionary of individuals evaluated
        paretofrontier.update(pop)
        record_individuals_tested = calc_dictionary_of_all_individuals_tested(record_individuals_tested, gen=gen,
                                                                              invalid_ind=invalid_ind)

        # Compile statistics about the new population
        record = stats.compile(pop)
        performance_metrics = calc_performance_metrics(generational_distances[-1], paretofrontier)
        generational_distances.append(performance_metrics[0])
        difference_generational_distances.append(performance_metrics[1])
        logbook.record(gen=gen, evals=len(invalid_ind), **record)
        print(logbook.stream)

        DHN_network_list_tested = []
        DCN_network_list_tested = []
        for individual in invalid_ind:
            DHN_barcode, DCN_barcode, \
            individual_with_name_dict, _ = individual_to_barcode(individual,
                                                                 building_names_all,
                                                                 building_names_heating,
                                                                 building_names_cooling,
                                                                 column_names,
                                                                 column_names_buildings_heating,
                                                                 column_names_buildings_cooling)
            DCN_network_list_tested.append(DCN_barcode)
            DHN_network_list_tested.append(DHN_barcode)

        if config.debug:
            print("Saving results for generation", gen, "\n")
            valid_generation = [gen]
            save_generation_dataframes(gen, invalid_ind, locator, DCN_network_list_tested, DHN_network_list_tested)
            save_generation_individuals(column_names, gen, invalid_ind, locator)
            systems_name_list = save_generation_pareto_individuals(locator, gen, record_individuals_tested,
                                                                   paretofrontier)
        else:
            systems_name_list = []
            valid_generation = []

        if gen == NGEN and config.debug is False:  # final generation re-evaluate paretofront
            print("Saving results for generation", gen, "\n")
            valid_generation = [gen]
            systems_name_list = save_final_generation_pareto_individuals(toolbox,
                                                                         locator,
                                                                         gen,
                                                                         objective_function_selection,
                                                                         record_individuals_tested,
                                                                         paretofrontier,
                                                                         building_names_all,
                                                                         column_names_buildings_heating,
                                                                         column_names_buildings_cooling,
                                                                         building_names_heating,
                                                                         building_names_cooling,
                                                                         building_names_electricity,
                                                                         network_features,
                                                                         weather_features,
                                                                         config,
                                                                         prices,
                                                                         lca,
                                                                         district_heating_network,
                                                                         district_cooling_network,
                                                                         technologies_heating_allowed,
                                                                         technologies_cooling_allowed,
                                                                         column_names)

        # Create Checkpoint if necessary
        print("Creating CheckPoint", gen, "\n")
        with open(locator.get_optimization_checkpoint(gen), "w") as fp:
            cp = dict(generation=gen,
                      selected_population=pop,
                      tested_population=invalid_ind,
                      generational_distances=generational_distances,
                      difference_generational_distances=difference_generational_distances,
                      systems_to_show=systems_name_list,
                      generation_to_show=valid_generation,
                      )
            json.dump(cp, fp)
    if config.multiprocessing:
        pool.close()

    return pop, logbook


def save_final_generation_pareto_individuals(toolbox,
                                             locator,
                                             generation,
                                             objective_function_selection,
                                             record_individuals_tested,
                                             paretofrontier,
                                             building_names_all,
                                             column_names_buildings_heating,
                                             column_names_buildings_cooling,
                                             building_names_heating,
                                             building_names_cooling,
                                             building_names_electricity,
                                             network_features,
                                             weather_features,
                                             config,
                                             prices,
                                             lca,
                                             district_heating_network,
                                             district_cooling_network,
                                             technologies_heating_allowed,
                                             technologies_cooling_allowed,
                                             column_names):
    # local variables
    performance_totals_pareto = pd.DataFrame()
    individual_number_list = []
    generation_number_list = []
    individual_in_pareto_list = []
    for i, record in enumerate(record_individuals_tested['individual_code']):
        if record in paretofrontier:
            individual_number = record_individuals_tested['individual_id'][i]
            generation_number = record_individuals_tested['generation'][i]
            individual = record_individuals_tested['individual_code'][i]
            individual_number_list.append(individual_number)
            generation_number_list.append(generation_number)
            individual_in_pareto_list.append(individual)

    save_generation_individuals(column_names, generation, individual_in_pareto_list, locator)

    # evaluate once again and print results for the pareto curve
    print_final_results = True
    fitnesses = toolbox.map(toolbox.evaluate, zip(individual_in_pareto_list,
                                                  individual_number_list,
                                                  generation_number_list,
                                                  repeat(objective_function_selection, len(individual_in_pareto_list)),
                                                  repeat(building_names_all, len(individual_in_pareto_list)),
                                                  repeat(column_names_buildings_heating,
                                                         len(individual_in_pareto_list)),
                                                  repeat(column_names_buildings_cooling,
                                                         len(individual_in_pareto_list)),
                                                  repeat(building_names_heating, len(individual_in_pareto_list)),
                                                  repeat(building_names_cooling, len(individual_in_pareto_list)),
                                                  repeat(building_names_electricity, len(individual_in_pareto_list)),
                                                  repeat(locator, len(individual_in_pareto_list)),
                                                  repeat(network_features, len(individual_in_pareto_list)),
                                                  repeat(weather_features, len(individual_in_pareto_list)),
                                                  repeat(config, len(individual_in_pareto_list)),
                                                  repeat(prices, len(individual_in_pareto_list)),
                                                  repeat(lca, len(individual_in_pareto_list)),
                                                  repeat(district_heating_network, len(individual_in_pareto_list)),
                                                  repeat(district_cooling_network, len(individual_in_pareto_list)),
                                                  repeat(technologies_heating_allowed, len(individual_in_pareto_list)),
                                                  repeat(technologies_cooling_allowed, len(individual_in_pareto_list)),
                                                  repeat(column_names, len(individual_in_pareto_list)),
                                                  repeat(print_final_results, len(individual_in_pareto_list))))

    # fitnesses is a map object of lazy results - iterate over it to actually evaluate
    fitnesses = list(fitnesses)

    for individual_number, generation_number in zip(individual_number_list, generation_number_list):
        performance_totals_pareto = pd.concat([performance_totals_pareto,
                                               pd.read_csv(
                                                   locator.get_optimization_slave_total_performance(
                                                       individual_number, generation_number))],
                                              ignore_index=True)

    systems_name_list = ["sys_" + str(genNum) + "_" + str(indNum) for
                         indNum, genNum in
                         zip(individual_number_list, generation_number_list)]
    performance_totals_pareto['individual'] = individual_number_list
    performance_totals_pareto['individual_name'] = systems_name_list
    performance_totals_pareto['generation'] = generation_number_list
    locator.ensure_parent_folder_exists(locator.get_optimization_generation_total_performance_pareto(generation))
    performance_totals_pareto.to_csv(locator.get_optimization_generation_total_performance_pareto(generation),
                                     index=False)

    return systems_name_list


def save_generation_pareto_individuals(locator, generation, record_individuals_tested, paretofrontier):
    performance_totals_pareto = pd.DataFrame()
    individual_list = []
    generation_list = []

    for i, record in enumerate(record_individuals_tested['individual_code']):
        if record in paretofrontier:
            ind = record_individuals_tested['individual_id'][i]
            gen = record_individuals_tested['generation'][i]
            individual_list.append(ind)
            generation_list.append(gen)
            performance_totals_pareto = pd.concat([performance_totals_pareto,
                                                   pd.read_csv(
                                                       locator.get_optimization_slave_total_performance(ind, gen))],
                                                  ignore_index=True)

    systems_name_list = ["sys_" + str(genNum) + "_" + str(indNum) 
                         for indNum, genNum 
                         in zip(individual_list, generation_list)]
    performance_totals_pareto['individual'] = individual_list
    performance_totals_pareto['individual_name'] = systems_name_list
    performance_totals_pareto['generation'] = generation_list
    locator.ensure_parent_folder_exists(locator.get_optimization_generation_total_performance_pareto(generation))
    performance_totals_pareto.to_csv(locator.get_optimization_generation_total_performance_pareto(generation),
                                     index=False)

    return systems_name_list


def save_generation_dataframes(generation,
                               slected_individuals,
                               locator,
                               DCN_network_list_selected,
                               DHN_network_list_selected):
    individual_list = range(len(slected_individuals))
    individual_name_list = ["sys_" + str(generation) + "_" + str(indNum) for indNum in individual_list]
    performance_disconnected = pd.DataFrame()
    performance_connected = pd.DataFrame()
    performance_totals = pd.DataFrame()
    for ind, DCN_barcode, DHN_barcode in zip(individual_list, DCN_network_list_selected, DHN_network_list_selected):
        performance_connected = pd.concat([performance_connected,
                                           pd.read_csv(
                                               locator.get_optimization_slave_district_scale_performance(ind,
                                                                                                         generation))],
                                          ignore_index=True)

        performance_disconnected = pd.concat([performance_disconnected, pd.read_csv(
            locator.get_optimization_slave_building_scale_performance(ind, generation))], ignore_index=True)
        performance_totals = pd.concat([performance_totals,
                                        pd.read_csv(
                                            locator.get_optimization_slave_total_performance(ind, generation))],
                                       ignore_index=True)

    performance_disconnected['individual'] = individual_list
    performance_connected['individual'] = individual_list
    performance_totals['individual'] = individual_list
    performance_disconnected['individual_name'] = individual_name_list
    performance_connected['individual_name'] = individual_name_list
    performance_totals['individual_name'] = individual_name_list
    performance_disconnected['generation'] = generation
    performance_connected['generation'] = generation
    performance_totals['generation'] = generation

    # save all results to disk
    locator.ensure_parent_folder_exists(locator.get_optimization_slave_generation_results_folder(generation))
    performance_disconnected.to_csv(locator.get_optimization_generation_building_scale_performance(generation),
                                    index=False)
    performance_connected.to_csv(locator.get_optimization_generation_district_scale_performance(generation),
                                 index=False)
    performance_totals.to_csv(locator.get_optimization_generation_total_performance(generation), index=False)


def save_generation_individuals(columns_of_saved_files, generation, invalid_ind, locator):
    # now get information about individuals and save to disk
    individual_list = range(len(invalid_ind))
    individuals_info = pd.DataFrame()
    for ind in invalid_ind:
        individual_dict = pd.DataFrame(dict(zip(columns_of_saved_files, [[x] for x in ind])))
        individuals_info = pd.concat([individual_dict, individuals_info], ignore_index=True)

    individuals_info['individual'] = individual_list
    individuals_info['generation'] = generation
    locator.ensure_parent_folder_exists(locator.get_optimization_individuals_in_generation(generation))
    individuals_info.to_csv(locator.get_optimization_individuals_in_generation(generation), index=False)


def create_empty_individual(column_names,
                            column_names_buildings_heating,
                            column_names_buildings_cooling,
                            district_heating_network,
                            district_cooling_network,
                            technologies_heating_allowed,
                            technologies_cooling_allowed,
                            ):
    # local variables
    heating_unit_names_share = [tech[0] for tech in DH_CONVERSION_TECHNOLOGIES_SHARE.items() if
                                tech[0] in technologies_heating_allowed]
    cooling_unit_names_share = [tech[0] for tech in DC_CONVERSION_TECHNOLOGIES_SHARE.items() if
                                tech[0] in technologies_cooling_allowed]

    heating_unit_share_float = [0.0] * len(heating_unit_names_share)
    cooling_unit_share_float = [0.0] * len(cooling_unit_names_share)

    DH_buildings_district_scale_int = [0] * len(column_names_buildings_heating)
    DC_buildings_district_scale_int = [0] * len(column_names_buildings_cooling)

    # 1 cases are possible
    if district_heating_network:
        individual = heating_unit_share_float + \
                     DH_buildings_district_scale_int
    elif district_cooling_network:
        individual = cooling_unit_share_float + \
                     DC_buildings_district_scale_int
    else:
        raise Exception('option not available')

    individual_with_names_dict = dict(zip(column_names, individual))

    return individual_with_names_dict


def get_column_names_individual(district_heating_network,
                                district_cooling_network,
                                building_names_heating,
                                building_names_cooling,
                                technologies_heating_allowed,
                                technologies_cooling_allowed,
                                ):
    # 2 cases are possible
    if district_heating_network:
        # local variables
        heating_unit_names_share = [tech[0] for tech in DH_CONVERSION_TECHNOLOGIES_SHARE.items() if
                                    tech[0] in technologies_heating_allowed]
        column_names_buildings_heating = [build + "_" + DH_ACRONYM for build in building_names_heating]
        cooling_unit_names_share = []
        column_names_buildings_cooling = []
        column_names = heating_unit_names_share + \
                       column_names_buildings_heating
    elif district_cooling_network:
        # local variables
        cooling_unit_names_share = [tech[0] for tech in DC_CONVERSION_TECHNOLOGIES_SHARE.items() if
                                    tech[0] in technologies_cooling_allowed]
        column_names_buildings_cooling = [build + "_" + DC_ACRONYM for build in building_names_cooling]
        heating_unit_names_share = []
        column_names_buildings_heating = []
        column_names = cooling_unit_names_share + \
                       column_names_buildings_cooling
    else:
        raise Exception('One or more attributes where not selected')

    return column_names, \
           heating_unit_names_share, \
           cooling_unit_names_share, \
           column_names_buildings_heating, \
           column_names_buildings_cooling


def calc_euclidean_distance(x2, y2):
    x1, y1 = 0.0, 0.0
    euclidean_distance = sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return euclidean_distance


def calc_gd(n, X2, Y2):
    gd = 1 / n * sqrt(sum([calc_euclidean_distance(x2, y2) for x2, y2 in zip(X2, Y2)]))
    return gd


def calc_performance_metrics(generational_distance_n_minus_1, paretofrontier):
    number_of_individuals = len([paretofrontier])
    X2 = [paretofrontier[ndInd].fitness.values[0] for ndInd in range(number_of_individuals)]
    Y2 = [paretofrontier[ndInd].fitness.values[1] for ndInd in range(number_of_individuals)]

    generational_distance = calc_gd(number_of_individuals, X2, Y2)
    difference_generational_distance = abs(generational_distance_n_minus_1 - generational_distance)

    return generational_distance, difference_generational_distance,


if __name__ == "__main__":
    x = 'no_testing_todo'

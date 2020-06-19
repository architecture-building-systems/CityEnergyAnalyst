from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import multiprocessing
import random
import warnings
from itertools import repeat
from math import factorial
from math import sqrt
from typing import List

import numpy as np
import pandas as pd
from deap import algorithms
from deap import tools, creator, base

import cea.inputlocator
import cea.config

from cea.optimization.master import evaluation
from cea.optimization.master.crossover import crossover_main
from cea.optimization.master.data_saver import save_results
from cea.optimization.master.generation import generate_main, calc_building_connectivity_dict
from cea.optimization.master.generation import individual_to_barcode
from cea.optimization.master.mutations import mutation_main
from cea.optimization.master.normalization import scaler_for_normalization, normalize_fitnesses
from cea.optimization.master.individual import IndividualList, IndividualBlueprint, IndividualDict, create_empty_individual, \
    create_individual_blueprint
from optimization.preprocessing.preprocessing_main import PreprocessingResult

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

warnings.filterwarnings("always")

NOBJ = 2  # number of objectives
creator.create("FitnessMin", base.Fitness, weights=(-1.0,) * NOBJ)
creator.create("Individual", list, typecode='d', fitness=creator.FitnessMin)


def objective_function(individual: IndividualList,
                       individual_number: int,
                       generation_number: int,
                       blueprint: IndividualBlueprint,
                       building_names_all,
                       building_names_heating,
                       building_names_cooling,
                       building_names_electricity,
                       locator: cea.inputlocator.InputLocator,
                       preprocessing_result: PreprocessingResult,
                       config: cea.config.Configuration,
                       district_heating_network: bool,
                       district_cooling_network: bool,
                       technologies_heating_allowed: List[str],
                       technologies_cooling_allowed: List[str],
                       print_final_results=False):
    """
    Objective function is used to calculate the costs, CO2, primary energy and the variables corresponding to the
    individual
    :param individual: Input individual
    :type individual: list
    :return: returns costs, CO2, primary energy and the master_to_slave_vars
    """
    print('cea optimization progress: individual ' + str(individual_number) + ' and generation ' + str(
        generation_number) + '/' + str(config.optimization.number_of_generations))

    TAC_sys_USD, \
    GHG_sys_tonCO2, \
    buildings_district_scale_costs, \
    buildings_district_scale_emissions, \
    buildings_building_scale_costs, \
    buildings_building_scale_emissions, \
    district_heating_generation_dispatch, \
    district_cooling_generation_dispatch, \
    district_electricity_dispatch, \
    district_electricity_demands, \
    performance_totals, \
    district_heating_capacity_installed, \
    district_cooling_capacity_installed, \
    district_electricity_capacity_installed, \
    buildings_building_scale_heating_capacities, \
    buildings_building_scale_cooling_capacities = evaluation.evaluation_main(individual,
                                                                             blueprint,
                                                                             building_names_all,
                                                                             locator,
                                                                             preprocessing_result,
                                                                             config,
                                                                             individual_number,
                                                                             generation_number,
                                                                             building_names_heating,
                                                                             building_names_cooling,
                                                                             building_names_electricity,
                                                                             district_heating_network,
                                                                             district_cooling_network,
                                                                             technologies_heating_allowed,
                                                                             technologies_cooling_allowed)

    if config.debug or print_final_results:  # print for the last generation and
        print("SAVING RESULTS TO DISK")
        individual_dict = IndividualDict.from_individual_list(individual, blueprint)
        save_results(locator,
                     preprocessing_result.weather_features.date,
                     individual_number,
                     generation_number,
                     buildings_district_scale_costs,
                     buildings_district_scale_emissions,
                     buildings_building_scale_costs,
                     buildings_building_scale_emissions,
                     district_heating_generation_dispatch,
                     district_cooling_generation_dispatch,
                     district_electricity_dispatch,
                     district_electricity_demands,
                     performance_totals,
                     calc_building_connectivity_dict(individual_dict, blueprint),
                     district_heating_capacity_installed,
                     district_cooling_capacity_installed,
                     district_electricity_capacity_installed,
                     buildings_building_scale_heating_capacities,
                     buildings_building_scale_cooling_capacities)

    return TAC_sys_USD, GHG_sys_tonCO2


def objective_function_wrapper(args):
    """
    Wrap arguments because multiprocessing only accepts one argument for the function"""
    return objective_function(*args)


def calc_dictionary_of_all_individuals_tested(dictionary_individuals, gen, invalid_ind):
    dictionary_individuals['generation'].extend([gen] * len(invalid_ind))
    dictionary_individuals['individual_id'].extend(range(len(invalid_ind)))
    dictionary_individuals['individual_code'].extend(invalid_ind)
    return dictionary_individuals


def non_dominated_sorting_genetic_algorithm(config, locator, building_names_all, district_heating_network,
                                            district_cooling_network, building_names_heating, building_names_cooling,
                                            building_names_electricity,
                                            preprocessing_result: PreprocessingResult):
    # LOCAL VARIABLES
    NGEN: int = config.optimization.number_of_generations  # number of generations
    MU: int = config.optimization.population_size  # int(H + (4 - H % 4)) # number of individuals to select
    RANDOM_SEED: int = config.optimization.random_seed
    CXPB: float = config.optimization.crossover_prob
    MUTPB: float = config.optimization.mutation_prob
    technologies_heating_allowed: List[str] = config.optimization.technologies_DH
    technologies_cooling_allowed: List[str] = config.optimization.technologies_DC
    mutation_method_integer: str = config.optimization.mutation_method_integer
    mutation_method_continuous: str = config.optimization.mutation_method_continuous
    crossover_method_integer: str = config.optimization.crossover_method_integer
    crossover_method_continuous: str = config.optimization.crossover_method_continuous

    # SET-UP EVOLUTIONARY ALGORITHM
    # Hyperparameters
    P = 12
    ref_points = tools.uniform_reference_points(NOBJ, P)
    if MU is None:
        H = factorial(NOBJ + P - 1) / (factorial(P) * factorial(NOBJ - 1))
        MU = int(H + (4 - H % 4))
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    # SET-UP INDIVIDUAL STRUCTURE INCLUDING HOW EVERY POINT IS CALLED (COLUMN_NAMES)
    blueprint = create_individual_blueprint(district_heating_network,
                                            district_cooling_network,
                                            building_names_heating,
                                            building_names_cooling,
                                            technologies_heating_allowed,
                                            technologies_cooling_allowed)
    individual_with_names_dict = create_empty_individual(blueprint,
                                                         district_heating_network,
                                                         district_cooling_network)

    # DEAP LIBRARY REFERENCE_POINT CLASSES AND TOOLS
    # reference points
    toolbox = base.Toolbox()
    toolbox.register("generate",
                     generate_main,
                     individual_dict=individual_with_names_dict,
                     blueprint=blueprint)
    toolbox.register("individual",
                     tools.initIterate,
                     creator.Individual,
                     toolbox.generate)
    toolbox.register("population",
                     tools.initRepeat,
                     list,
                     toolbox.individual)
    toolbox.register("mate",
                     crossover_main,
                     cx_prob=CXPB,
                     blueprint=blueprint,
                     crossover_method_integer=crossover_method_integer,
                     crossover_method_continuous=crossover_method_continuous)
    toolbox.register("mutate",
                     mutation_main,
                     mut_prob=MUTPB,
                     blueprint=blueprint,
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
    pareto_frontier = tools.ParetoFront()
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
    invalid_individuals = [ind for ind in pop if not ind.fitness.valid]
    n_times = len(invalid_individuals)
    fitnesses = toolbox.map(toolbox.evaluate, zip(invalid_individuals,  # individual
                                                  range(n_times),  # individual_number
                                                  repeat(0, n_times),  # generation_number
                                                  repeat(blueprint, n_times),
                                                  repeat(building_names_all, n_times),  # building_names_all
                                                  repeat(building_names_heating, n_times),
                                                  repeat(building_names_cooling, n_times),
                                                  repeat(building_names_electricity, n_times),
                                                  repeat(locator, n_times),
                                                  repeat(preprocessing_result, n_times),
                                                  repeat(config, n_times),
                                                  repeat(district_heating_network, n_times),
                                                  repeat(district_cooling_network, n_times),
                                                  repeat(technologies_heating_allowed, n_times),
                                                  repeat(technologies_cooling_allowed, n_times)))
    fitnesses = list(fitnesses)
    # normalization of the first generation
    scaler_dict = scaler_for_normalization(NOBJ, fitnesses)
    fitnesses = normalize_fitnesses(scaler_dict, fitnesses)

    # add fitnesses to population individuals
    for ind, fit in zip(invalid_individuals, fitnesses):
        ind.fitness.values = fit

    # Compile statistics about the population
    record = stats.compile(pop)
    pareto_frontier.update(pop)
    performance_metrics = calc_performance_metrics(0.0, pareto_frontier)
    generational_distances.append(performance_metrics[0])
    difference_generational_distances.append(performance_metrics[1])
    logbook.record(gen=0, evals=n_times, **record)

    # create a dictionary to store which individuals that are being calculated
    record_individuals_tested = {'generation': [], "individual_id": [], "individual_code": []}
    record_individuals_tested = calc_dictionary_of_all_individuals_tested(record_individuals_tested, gen=0,
                                                                          invalid_ind=invalid_individuals)
    print(logbook.stream)

    # Begin the generational process
    # Initialization of variables
    for gen in range(1, NGEN + 1):
        print("Evaluating Generation %s of %s generations" % (gen, NGEN + 1))
        # Select and clone the next generation individuals
        offspring = algorithms.varAnd(pop, toolbox, CXPB, MUTPB)

        # Evaluate the individuals with an invalid fitness
        invalid_individuals = [ind for ind in offspring if not ind.fitness.valid]
        invalid_individuals = [ind for ind in invalid_individuals if ind not in pop]
        n_times = len(invalid_individuals)
        fitnesses = toolbox.map(toolbox.evaluate,
                                zip(invalid_individuals,
                                    range(n_times),  # individual_number
                                    repeat(gen, n_times),  # generation_number
                                    repeat(blueprint, n_times),
                                    repeat(building_names_all, n_times),
                                    repeat(building_names_heating, n_times),
                                    repeat(building_names_cooling, n_times),
                                    repeat(building_names_electricity, n_times),
                                    repeat(locator, n_times),
                                    repeat(preprocessing_result, n_times),
                                    repeat(config, n_times),
                                    repeat(district_heating_network, n_times),
                                    repeat(district_cooling_network, n_times),
                                    repeat(technologies_heating_allowed, n_times),
                                    repeat(technologies_cooling_allowed, n_times)))
        # normalization of the second generation on
        fitnesses = normalize_fitnesses(scaler_dict, fitnesses)

        for ind, fit in zip(invalid_individuals, fitnesses):
            ind.fitness.values = fit

        # Select the next generation population from parents and offspring
        pop = toolbox.select(pop + invalid_individuals, MU)

        # get paretofront and update dictionary of individuals evaluated
        pareto_frontier.update(pop)
        record_individuals_tested = calc_dictionary_of_all_individuals_tested(record_individuals_tested, gen=gen,
                                                                              invalid_ind=invalid_individuals)

        # Compile statistics about the new population
        record = stats.compile(pop)
        performance_metrics = calc_performance_metrics(generational_distances[-1], pareto_frontier)
        generational_distances.append(performance_metrics[0])
        difference_generational_distances.append(performance_metrics[1])
        logbook.record(gen=gen, evals=n_times, **record)
        print(logbook.stream)

        DHN_network_list_tested = []
        DCN_network_list_tested = []

        for individual in invalid_individuals:
            individual_dict = IndividualDict.from_individual_list(individual, blueprint)
            DHN_barcode, DCN_barcode, = individual_to_barcode(individual_dict, blueprint)

            DCN_network_list_tested.append(DCN_barcode)
            DHN_network_list_tested.append(DHN_barcode)

        if config.debug:
            print("Saving results for generation", gen, "\n")
            valid_generation = [gen]
            save_generation_dataframes(gen, invalid_individuals, locator, DCN_network_list_tested, DHN_network_list_tested)
            save_generation_individuals(blueprint.column_names, gen, invalid_individuals, locator)
            systems_name_list = save_generation_pareto_individuals(locator, gen, record_individuals_tested, pareto_frontier)
        else:
            systems_name_list = []
            valid_generation = []

        if gen == NGEN and not config.debug:  # final generation re-evaluate paretofront
            print("Saving results for generation", gen, "\n")
            valid_generation = [gen]
            systems_name_list = save_final_generation_pareto_individuals(
                toolbox,
                locator,
                gen,
                record_individuals_tested,
                pareto_frontier,
                blueprint,
                preprocessing_result,
                building_names_all,
                building_names_heating,
                building_names_cooling,
                building_names_electricity,
                config,
                district_heating_network,
                district_cooling_network,
                technologies_heating_allowed,
                technologies_cooling_allowed)

        # Create Checkpoint if necessary
        print("Creating CheckPoint", gen, "\n")
        with open(locator.get_optimization_checkpoint(gen), "w") as fp:
            cp = dict(generation=gen,
                      selected_population=pop,
                      tested_population=invalid_individuals,
                      generational_distances=generational_distances,
                      difference_generational_distances = difference_generational_distances,
                      systems_to_show=systems_name_list,
                      generation_to_show=valid_generation,
                      )
            json.dump(cp, fp)
    if config.multiprocessing:
        pool.close()

    return pop, logbook


def save_final_generation_pareto_individuals(toolbox,
                                             locator: cea.inputlocator.InputLocator,
                                             generation,
                                             record_individuals_tested,
                                             pareto_frontier,
                                             blueprint: IndividualBlueprint,
                                             preprocessing_result: PreprocessingResult,
                                             building_names_all,
                                             building_names_heating,
                                             building_names_cooling,
                                             building_names_electricity,
                                             config: cea.config.Configuration,
                                             district_heating_network,
                                             district_cooling_network,
                                             technologies_heating_allowed,
                                             technologies_cooling_allowed):
    performance_totals_pareto = pd.DataFrame()
    individual_number_list = []
    generation_number_list = []
    individuals_in_pareto_list = []
    for i, record in enumerate(record_individuals_tested['individual_code']):
        if record in pareto_frontier:
            individual_number = record_individuals_tested['individual_id'][i]
            generation_number = record_individuals_tested['generation'][i]
            individual = record_individuals_tested['individual_code'][i]
            individual_number_list.append(individual_number)
            generation_number_list.append(generation_number)
            individuals_in_pareto_list.append(individual)

    save_generation_individuals(blueprint.column_names, generation, individuals_in_pareto_list, locator)

    # evaluate once again and print results for the pareto curve
    print_final_results = True
    n_times = len(individuals_in_pareto_list)
    toolbox.map(toolbox.evaluate, zip(individuals_in_pareto_list,
                                      individual_number_list,
                                      generation_number_list,
                                      repeat(blueprint, n_times),
                                      repeat(building_names_all, n_times),
                                      repeat(building_names_heating, n_times),
                                      repeat(building_names_cooling, n_times),
                                      repeat(building_names_electricity, n_times),
                                      repeat(locator, n_times),
                                      repeat(preprocessing_result, n_times),
                                      repeat(config, n_times),
                                      repeat(district_heating_network, n_times),
                                      repeat(district_cooling_network, n_times),
                                      repeat(technologies_heating_allowed, n_times),
                                      repeat(technologies_cooling_allowed, n_times),
                                      repeat(print_final_results, n_times)))

    for individual_number, generation_number in zip(individual_number_list, generation_number_list):
        performance_totals_pareto = pd.concat([performance_totals_pareto,
                                                   pd.read_csv(
                                                       locator.get_optimization_slave_total_performance(
                                                           individual_number, generation_number))],
                                                  ignore_index=True)

    systems_name_list = ["sys_" + str(y) + "_" + str(x) for x, y in zip(individual_number_list, generation_number_list)]
    performance_totals_pareto['individual'] = individual_number_list
    performance_totals_pareto['individual_name'] = systems_name_list
    performance_totals_pareto['generation'] = generation_number_list
    performance_totals_pareto.to_csv(locator.get_optimization_generation_total_performance_pareto(generation), index=False)

    return systems_name_list


def save_generation_pareto_individuals(locator, generation, record_individuals_tested, pareto_frontier):
    performance_totals_pareto = pd.DataFrame()
    individual_list = []
    generation_list = []

    for i, record in enumerate(record_individuals_tested['individual_code']):
        if record in pareto_frontier:
            ind = record_individuals_tested['individual_id'][i]
            gen = record_individuals_tested['generation'][i]
            individual_list.append(ind)
            generation_list.append(gen)
            performance_totals_pareto = pd.concat([performance_totals_pareto,
                                                   pd.read_csv(
                                                       locator.get_optimization_slave_total_performance(ind, gen))],
                                                  ignore_index=True)

    systems_name_list = ["sys_" + str(y) + "_" + str(x) for x, y in zip(individual_list, generation_list)]
    performance_totals_pareto['individual'] = individual_list
    performance_totals_pareto['individual_name'] = systems_name_list
    performance_totals_pareto['generation'] = generation_list
    performance_totals_pareto.to_csv(locator.get_optimization_generation_total_performance_pareto(generation), index=False)

    return systems_name_list


def save_generation_dataframes(generation,
                               slected_individuals,
                               locator,
                               DCN_network_list_selected,
                               DHN_network_list_selected):
    individual_list = range(len(slected_individuals))
    individual_name_list = ["sys_" + str(generation) + "_" + str(x) for x in individual_list]
    performance_disconnected = pd.DataFrame()
    performance_connected = pd.DataFrame()
    performance_totals = pd.DataFrame()
    for ind, DCN_barcode, DHN_barcode in zip(individual_list, DCN_network_list_selected, DHN_network_list_selected):
        performance_connected = pd.concat([performance_connected,
                                           pd.read_csv(
                                               locator.get_optimization_slave_district_scale_performance(ind, generation))],
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
    performance_disconnected.to_csv(locator.get_optimization_generation_building_scale_performance(generation), index=False)
    performance_connected.to_csv(locator.get_optimization_generation_district_scale_performance(generation), index=False)
    performance_totals.to_csv(locator.get_optimization_generation_total_performance(generation), index=False)


def save_generation_individuals(columns_of_saved_files, generation, invalid_ind, locator):
    # now get information about individuals and save to disk
    individual_list = range(len(invalid_ind))
    individuals_info = pd.DataFrame()
    for ind in invalid_ind:
        infividual_dict = pd.DataFrame(dict(zip(columns_of_saved_files, [[x] for x in ind])))
        individuals_info = pd.concat([infividual_dict, individuals_info], ignore_index=True)

    individuals_info['individual'] = individual_list
    individuals_info['generation'] = generation
    individuals_info.to_csv(locator.get_optimization_individuals_in_generation(generation), index=False)


def calc_euclidean_distance(x2, y2):
    x1, y1 = 0.0, 0.0
    euclidean_distance = sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return euclidean_distance


def calc_gd(n, X2, Y2):
    gd = 1 / n * sqrt(sum([calc_euclidean_distance(x2, y2) for x2, y2 in zip(X2, Y2)]))
    return gd


def calc_performance_metrics(generational_distance_n_minus_1, pareto_frontier):
    number_of_individuals = len([pareto_frontier])
    X2 = [pareto_frontier[x].fitness.values[0] for x in range(number_of_individuals)]
    Y2 = [pareto_frontier[x].fitness.values[1] for x in range(number_of_individuals)]

    generational_distance = calc_gd(number_of_individuals, X2, Y2)
    difference_generational_distance = abs(generational_distance_n_minus_1 - generational_distance)

    return generational_distance, difference_generational_distance,


if __name__ == "__main__":
    x = 'no_testing_todo'

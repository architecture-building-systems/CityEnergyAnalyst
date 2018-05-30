"""
hydraulic network
"""

from __future__ import division
import cea.technologies.thermal_network.thermal_network_matrix as thermal_network_matrix
from cea.technologies.thermal_network.network_layout.main import network_layout as network_layout
import cea.optimization.distribution.network_opt_main as network_opt
import cea.technologies.pumps as pumps
from cea.optimization.prices import Prices as Prices
import cea.config
import cea.globalvar
import cea.inputlocator
from cea.optimization.constants import PUMP_ETA

import pandas as pd
import numpy as np
import time
import operator
import random

__author__ = "Lennart Rogenhofer"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Lennart Rogenhofer"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class Optimize_Network(object):
    """
    Storage of information for the network currently being calcuted.
    """

    def __init__(self, locator, config, network_type, gv):
        self.locator = locator
        self.config = config
        self.network_type = network_type

        self.network_name = ''
        self.cost_storage = None
        self.building_names = None
        self.number_of_buildings = 0
        self.gv = gv
        self.prices = None
        self.network_features = None
        self.layout = 0
        self.has_loop = 0
        self.populations = {}
        self.all_individuals = None
        self.generation_number = 0


def calc_Ctot_pump_netw(optimal_plant_loc):
    """
    Computes the total pump investment and operational cost
    :type dicoSupply : class context
    :type ntwFeat : class ntwFeatures
    :rtype pumpCosts : float
    :returns pumpCosts: pumping cost
    """
    network_type = optimal_plant_loc.config.thermal_network.network_type

    # read in node mass flows
    df = pd.read_csv(optimal_plant_loc.locator.get_node_mass_flow_csv_file(network_type, ''), index_col=0)
    mdotA_kgpers = np.array(df)
    mdotnMax_kgpers = np.amax(mdotA_kgpers)  # find highest mass flow of all nodes at all timesteps (should be at plant)

    # read in total pressure loss in kW
    deltaP_kW = pd.read_csv(optimal_plant_loc.locator.get_ploss('', network_type))
    deltaP_kW = deltaP_kW['pressure_loss_total_kW'].sum()
    pumpCosts = deltaP_kW * optimal_plant_loc.prices.ELEC_PRICE

    if optimal_plant_loc.config.thermal_network.network_type == 'DH':
        deltaPmax = np.max(optimal_plant_loc.network_features.DeltaP_DHN)
    else:
        deltaPmax = np.max(optimal_plant_loc.network_features.DeltaP_DCN)

    Capex_a, Opex_fixed = pumps.calc_Cinv_pump(2 * deltaPmax, mdotnMax_kgpers, PUMP_ETA, optimal_plant_loc.gv,
                                               optimal_plant_loc.locator, 'PU1')  # investment of Machinery
    pumpCosts += Opex_fixed

    return Capex_a, pumpCosts


def plant_location_cost_calculation(newMutadedGen, optimal_plant_loc):
    """
    Main function which calculates opex and capex costs of the network. This is the value to be minimized.
    :param building_index: A value between 0 and the total number of buildings, indicating next to which building the plant is placed
    :param optimal_plant_loc: Object containing information of current network
    :return: Total cost, value to be minimized
    """

    population_performance = {}
    individual_number = 0
    outputs=pd.DataFrame(np.zeros((optimal_plant_loc.config.thermal_network.number_of_individuals,4)))
    outputs.columns = ['individual', 'capex', 'opex', 'total']
    for individual in newMutadedGen:
        if not str(individual) in optimal_plant_loc.populations.keys():
            optimal_plant_loc.populations[str(individual)]={}
            # evaluate fitness
            building_index = [i for i, x in enumerate(individual) if x == 1]
            print 'Individual number: ', individual_number
            print 'With ', int(sum(individual)), ' plant(s) at building(s): '
            for building in building_index:
                print optimal_plant_loc.building_names[building]

            total_cost, capex, opex = fitness_func(optimal_plant_loc, building_index, individual_number)

            population_performance[total_cost] = individual

            # store values
            optimal_plant_loc.populations[str(individual)]['total'] = total_cost
            optimal_plant_loc.populations[str(individual)]['capex'] = capex
            optimal_plant_loc.populations[str(individual)]['opex'] = opex
        else:
            total_cost = optimal_plant_loc.populations[str(individual)]['total']
            population_performance[total_cost] = individual

        outputs.ix[individual_number]['capex'] = optimal_plant_loc.populations[str(individual)]['capex']
        outputs.ix[individual_number]['opex'] = optimal_plant_loc.populations[str(individual)]['opex']
        outputs.ix[individual_number]['total'] = optimal_plant_loc.populations[str(individual)]['total']

        individual_number += 1

    individual_number = 0
    for individual in newMutadedGen:
        outputs.ix[individual_number]['individual'] = individual_number
        individual_number  += 1
    outputs['individual'] = outputs['individual'].astype(str)
    individual_number = 0
    for individual in newMutadedGen:
        outputs.replace(str(float(individual_number)), str(individual), inplace=True)
        individual_number += 1
    # write cost storage to csv
    # output results file to csv
    outputs.to_csv(
        optimal_plant_loc.locator.get_optimization_network_generation_results_file(optimal_plant_loc.network_type,
                                                                                   optimal_plant_loc.generation_number))
    optimal_plant_loc.generation_number += 1
    return sorted(population_performance.items(), key=operator.itemgetter(0))


def fitness_func(optimal_plant_loc, building_index, individual_number):
    building_names = []
    for building in building_index:
        building_names.append(optimal_plant_loc.building_names[building])
    network_layout(optimal_plant_loc.config, optimal_plant_loc.locator, building_names, optimization_flag=True)
    thermal_network_matrix.main(optimal_plant_loc.config)

    ## Cost calculations
    optimal_plant_loc.prices = Prices(optimal_plant_loc.locator, optimal_plant_loc.config)
    optimal_plant_loc.network_features = network_opt.network_opt_main(optimal_plant_loc.config,
                                                                      optimal_plant_loc.locator)
    # calculate Network costs
    # OPEX neglected, see Documentation Master Thesis Lennart Rogenhofer
    if optimal_plant_loc.network_type == 'DH':
        Capex_a_netw = optimal_plant_loc.network_features.pipesCosts_DHN
    else:
        Capex_a_netw = optimal_plant_loc.network_features.pipesCosts_DCN
    # calculate Pressure loss and Pump costs
    Capex_a_pump, Opex_fixed_pump = calc_Ctot_pump_netw(optimal_plant_loc)
    # calculate Heat loss costs
    if optimal_plant_loc.network_type == 'DH':
        # Assume a COP of 1.5 e.g. in CHP plant
        Opex_heat = optimal_plant_loc.network_features.thermallosses_DHN/1.5 * optimal_plant_loc.prices.ELEC_PRICE
    else:
        # Assume a COp of 4 e.g. brine centrifugal chiller @ Marina Bay
        # [1] Hida Y, Shibutani S, Amano M, Maehara N. District Cooling Plant with High Efficiency Chiller and Ice
        # Storage System. Mitsubishi Heavy Ind Ltd Tech Rev 2008;45:37 to 44.
        Opex_heat = optimal_plant_loc.network_features.thermallosses_DCN / 3.3 * optimal_plant_loc.prices.ELEC_PRICE

    optimal_plant_loc.cost_storage.ix['capex'][individual_number] = Capex_a_netw + Capex_a_pump
    optimal_plant_loc.cost_storage.ix['opex'][individual_number] = Opex_fixed_pump + Opex_heat
    optimal_plant_loc.cost_storage.ix['total'][individual_number] = Capex_a_netw + Capex_a_pump + \
                                                                    Opex_fixed_pump + Opex_heat

    return optimal_plant_loc.cost_storage.ix['total'][individual_number], \
           optimal_plant_loc.cost_storage.ix['capex'][individual_number], \
           optimal_plant_loc.cost_storage.ix['opex'][individual_number]


def selectFromPrevPop(sortedPrevPop, optimal_plant_loc):
    next_Generation = []
    for i in range(optimal_plant_loc.config.thermal_network.number_of_individuals - optimal_plant_loc.config.thermal_network.lucky_few):
        next_Generation.append(sortedPrevPop[i][1])
    while len(next_Generation) < optimal_plant_loc.config.thermal_network.number_of_individuals:
        lucky_individual = random.choice(generateInitialPopulation(optimal_plant_loc))
        if lucky_individual not in next_Generation:
            next_Generation.append(lucky_individual)
    random.shuffle(next_Generation)
    return next_Generation


def breedNewGeneration(selectedInd, optimal_plant_loc):
    newGeneration = []
    while len(newGeneration) < optimal_plant_loc.config.thermal_network.number_of_individuals:
        first_parent = random.choice(selectedInd)
        second_parent = random.choice(selectedInd)
        child = np.zeros(len(first_parent))
        for j in range(len(first_parent)):
            if int(first_parent[j]) == int(second_parent[j]):
                child[j] = float(first_parent[j])
            else:
                which_parent = np.random.random_integers(low=0, high=1)
                if which_parent == 0:
                    child[j] = float(first_parent[j])
                else:
                    child[j] = float(second_parent[j])
        # make sure that we do not have too many plants now
        while sum(child) > optimal_plant_loc.config.thermal_network.max_number_of_plants:
            plant_indices = np.where(child == 1)[0]
            random_plant = random.choice(list(plant_indices))
            child[int(random_plant)] = 0.0
        # make sure we still have a non-zero amount of plants
        while sum(child) < optimal_plant_loc.config.thermal_network.min_number_of_plants:
            # Add one plant
            indices = [i for i, x in enumerate(child) if x == 0]
            index = int(random.choice(indices))
            child[index] = 1.0
        if list(child) not in newGeneration:
            newGeneration.append(list(child))
    return newGeneration


def generate_plants(optimal_plant_loc):
    """
    Generates the number of plants given in the config files at random building locations.
    :param optimal_plant_loc: Object containg network information.
    """
    has_plant = np.zeros(optimal_plant_loc.number_of_buildings)
    random_index = admissible_plant_location(optimal_plant_loc)
    has_plant[random_index] = 1.0
    number_of_plants_to_add = np.random.random_integers(low=optimal_plant_loc.config.thermal_network.min_number_of_plants - 1, high=(
            optimal_plant_loc.config.thermal_network.max_number_of_plants - 1))
    while sum(has_plant) < number_of_plants_to_add + 1:
        random_index = admissible_plant_location(optimal_plant_loc)
        has_plant[random_index] = 1.0
    return list(has_plant)


def admissible_plant_location(optimal_plant_loc):
    admissible_plant_location = False
    while not admissible_plant_location:
        random_index = np.random.random_integers(low=0, high=(optimal_plant_loc.number_of_buildings - 1))
        if optimal_plant_loc.building_names[random_index] in optimal_plant_loc.config.thermal_network.possible_plant_sites:
            admissible_plant_location=True
    return random_index


def generateInitialPopulation(optimal_plant_loc):
    """
    Generates the initial population for network optimization.
    :param optimal_plant_loc:
    :return:
    """
    initialPop = []
    while len(initialPop) < optimal_plant_loc.config.thermal_network.number_of_individuals:
        new_individual = generate_plants(optimal_plant_loc)
        if new_individual not in initialPop:
            initialPop.append(new_individual)
    return list(initialPop)


def mutateLocation(individual, optimal_plant_loc):
    individual = list(individual)
    if optimal_plant_loc.config.thermal_network.max_number_of_plants != 1:
        if sum(individual) >= optimal_plant_loc.config.thermal_network.max_number_of_plants:
            # remove one plant
            indices = [i for i, x in enumerate(individual) if x == 1]
            index = int(random.choice(indices))
            individual[index] = 0.0
            # individual[index] = 1
        elif sum(individual) <= optimal_plant_loc.config.thermal_network.min_number_of_plants:
            while sum(individual) <= optimal_plant_loc.config.thermal_network.min_number_of_plants:
                # Add one plant
                index = admissible_plant_location(optimal_plant_loc)
                individual[index] = 1.0
        else:
            add_or_remove = np.random.random_integers(low=0, high=1)
            if add_or_remove == 0:  # remove a plant
                indices = [i for i, x in enumerate(individual) if x == 1]
                index = int(random.choice(indices))
                individual[index] = 0.0
            else:  # add a plant
                original_sum = sum(individual)
                while sum(individual) == original_sum: # make sure we actually add a new one and don't just overwrite an existing plant
                    index = admissible_plant_location(optimal_plant_loc)
                    individual[index] = 1.0
    else:
        # remove the plant
        index = [i for i, x in enumerate(individual) if x == 1]
        individual[int(index[0])] = 0.0
        # add a new one
        index = admissible_plant_location(optimal_plant_loc)
        individual[index] = 1.0
    return list(individual)


def mutateGeneration(newGen, optimal_plant_loc):
    for i in range(len(newGen)):
        random.seed()
        if random.random() * 100 < optimal_plant_loc.config.thermal_network.chance_of_mutation:
            mutated_element_flag = False
            while not mutated_element_flag:
                mutated_individual = list(
                    mutateLocation(newGen[i], optimal_plant_loc))
                if mutated_individual not in newGen:
                    mutated_element_flag = True
                    newGen[i] = mutated_individual
    return newGen


# ============================
# test
# ============================


def main(config):
    """
    runs an optimization calculation for the plant location in the thermal network.
    """
    print('Running thermal_network plant location optimization for scenario %s' % config.scenario)
    print 'Number of individuals: ', config.thermal_network.number_of_individuals
    print 'Number of generations: ', config.thermal_network.number_of_generations
    print 'Number of lucky few individuals: ', config.thermal_network.lucky_few
    print 'Percentage chance of mutation: ', config.thermal_network.chance_of_mutation
    print 'Number of plants between ', config.thermal_network.min_number_of_plants, ' and ', config.thermal_network.max_number_of_plants
    if config.thermal_network.possible_plant_sites:
        print 'Possible plant locations: ', config.thermal_network.possible_plant_sites
    else:
        print 'Possible plant locations: all'

    start = time.time()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    gv = cea.globalvar.GlobalVariables()
    network_type = config.thermal_network.network_type

    optimal_plant_loc = Optimize_Network(locator, config, network_type, gv)

    total_demand = pd.read_csv(locator.get_total_demand())
    optimal_plant_loc.building_names = total_demand.Name.values
    optimal_plant_loc.number_of_buildings = total_demand.Name.count()

    # list of possible plant location sites
    if not config.thermal_network.possible_plant_sites:
        config.thermal_network.possible_plant_sites = optimal_plant_loc.building_names

    optimal_plant_loc.cost_storage = pd.DataFrame(np.zeros((3, optimal_plant_loc.config.thermal_network.number_of_individuals)))
    optimal_plant_loc.cost_storage.index = ['capex', 'opex', 'total']

    newMutadedGen = generateInitialPopulation(optimal_plant_loc)
    for generation_number in range(optimal_plant_loc.config.thermal_network.number_of_generations):
        print 'Running optimization for generation number ', generation_number
        sortedPop = plant_location_cost_calculation(newMutadedGen, optimal_plant_loc)
        print 'Lowest cost individual: ', sortedPop[0], '\n'
        if generation_number < optimal_plant_loc.config.thermal_network.number_of_generations - 1:
            selectedPop = selectFromPrevPop(sortedPop, optimal_plant_loc)
            newGen = breedNewGeneration(selectedPop, optimal_plant_loc)
            newMutadedGen = mutateGeneration(newGen, optimal_plant_loc)

    # write values into storage dataframe and ouput results
    # setup data frame with generations, individual, opex, capex and total cost
    optimal_plant_loc.all_individuals = pd.DataFrame(np.zeros((
        len(optimal_plant_loc.populations.keys()), 4)))
    optimal_plant_loc.all_individuals.columns = ['individual', 'opex', 'capex', 'total cost']
    row_number = 0
    for individual in optimal_plant_loc.populations.keys():
        optimal_plant_loc.all_individuals.ix[row_number]['opex'] = optimal_plant_loc.populations[str(individual)][
            'opex']
        optimal_plant_loc.all_individuals.ix[row_number]['capex'] = optimal_plant_loc.populations[str(individual)][
            'capex']
        optimal_plant_loc.all_individuals.ix[row_number]['total cost'] = \
        optimal_plant_loc.populations[str(individual)]['total']
        row_number += 1
    row_number = 0
    for individual in optimal_plant_loc.populations.keys():
        optimal_plant_loc.all_individuals.ix[row_number]['individual'] = row_number
        row_number += 1
    row_number = 0
    optimal_plant_loc.all_individuals['individual'] = \
        optimal_plant_loc.all_individuals['individual'].astype(str)
    for individual in optimal_plant_loc.populations.keys():
        optimal_plant_loc.all_individuals.replace(str(float(row_number)), str(individual), inplace=True)
        row_number += 1

    optimal_plant_loc.all_individuals.to_csv(
        optimal_plant_loc.locator.get_optimization_network_all_individuals_results_file(optimal_plant_loc.network_type), index='False')

    print('thermal_network_optimization_main() succeeded')
    print('total time: ', time.time() - start)


if __name__ == '__main__':
    main(cea.config.Configuration())

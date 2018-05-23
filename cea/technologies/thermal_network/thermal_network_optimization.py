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
    for individual in newMutadedGen:
        building_index = individual.index(1)
        print 'Running analysis for', optimal_plant_loc.number_of_buildings, ' plant(s) at building(s): '
        for building in building_index:
            print optimal_plant_loc.building_names[building]

        total_cost = fitness_func(optimal_plant_loc, building_index, individual_number)

        population_performance[individual] = total_cost
        individual_number += 1

    # write cost storage to csv
    optimal_plant_loc.cost_storage.to_csv(optimal_plant_loc.locator.get_optimization_network_generation_results_file(optimal_plant_loc.network_type,
                                                                                                                     optimal_plant_loc.generation_number))

    return sorted(population_performance.items(), key=operator.itemgetter(1), reverse=True)


def fitness_func(optimal_plant_loc, building_index, individual_number):
    building_names = []
    for building in building_index:
        building_names.append(optimal_plant_loc.cost_storage.columns[building])
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
        # Assume a COP of 1 e.g. in CHP plant
        Opex_heat = optimal_plant_loc.network_features.thermallosses_DHN * optimal_plant_loc.prices.ELEC_PRICE
    else:
        # Assume a COp of 4 e.g.
        Opex_heat = optimal_plant_loc.network_features.thermallosses_DCN / 4 * optimal_plant_loc.prices.ELEC_PRICE

    optimal_plant_loc.cost_storage.ix[individual_number]['Capex_total'] = Capex_a_netw + Capex_a_pump
    optimal_plant_loc.cost_storage.ix[individual_number]['Opex_total'] = Opex_fixed_pump + Opex_heat
    optimal_plant_loc.cost_storage.ix[individual_number][
        'Cost_total'] = Capex_a_netw + Capex_a_pump + Opex_fixed_pump + Opex_heat

    return optimal_plant_loc.cost_storage['Cost_total']


def selectFromPrevPop(sortedPrevPop, optimal_plant_loc):
    next_Generation = []
    for i in range(optimal_plant_loc.config.thermal_network.best_sample):
        next_Generation.append(sortedPrevPop[i][0])
    for i in range(optimal_plant_loc.config.thermal_network.lucky_few):
        next_Generation.append(random.choice(sortedPrevPop)[0])
    random.shuffle(next_Generation)
    return next_Generation


def breedNewGeneration(selectedInd, optimal_plant_loc):
    newGeneration = []
    for i in range(len(selectedInd)):
        first_parent = random.choice(selectedInd)[0]
        second_parent = random.choice(selectedInd)[0]
        child = np.zeros(len(first_parent))
        for j in range(len(first_parent)):
            if first_parent[j] == second_parent[j]:
                child[j] = first_parent[j]
            else:
                which_parent = np.random.random_integers(low=0, high=1)
                if which_parent == 0:
                    child[j] = first_parent[j]
                else:
                    child[j] = second_parent[j]
        # make sure that we do not have too many plants now
        while sum(child) > optimal_plant_loc.config.thermal_network.max_number_of_plants:
            plant_indices = child[np.where(child == 1)]
            random_plant = random.choice(plant_indices)
            child[random_plant] = 0
        newGeneration.append(list(child))
    return newGeneration


def generate_plants(optimal_plant_loc):
    """
    Generates the number of plants given in the config files at random building locations.
    :param optimal_plant_loc: Object containg network information.
    """
    has_plant = np.zeros(optimal_plant_loc.number_of_buildings)
    number_of_plants_to_add = np.random.random_integers(low=0, high=(
                optimal_plant_loc.config.thermal_network.max_number_of_plants - 1))
    while sum(has_plant) < number_of_plants_to_add:
        random_index = np.random.random_integers(low=0, high=(optimal_plant_loc.number_of_buildings - 1))
        has_plant[random_index] = 1
    return list(has_plant)


def generateInitialPopulation(optimal_plant_loc):
    """
    Generates the initial population for network optimization.
    :param optimal_plant_loc:
    :return:
    """
    while len(optimal_plant_loc.population) < optimal_plant_loc.config.thermal_network.initialind:
        new_individual = generate_plants(optimal_plant_loc)
        if new_individual not in optimal_plant_loc.population:
            optimal_plant_loc.population.append(new_individual)


def mutateLocation(individual, optimal_plant_loc):
    if sum(individual) >= optimal_plant_loc.config.thermal_network.max_number_of_plants:
        # remove one plant
        indices = np.where(individual == 1)
        index = random.choice(indices)
        individual[index] = 0
        # individual[index] = 1
    elif sum(individual) <= 1:
        # Add one plant
        indices = np.where(individual == 0)
        index = random.choice(indices)
        individual[index] = 1
    else:
        add_or_remove = np.random.random_integers(low=0, high=1)
        if add_or_remove == 0:  # remove a plant
            indices = np.where(individual == 1)
            index = random.choice(indices)
            individual[index] = 0
        else:  # add a plant
            indices = np.where(individual == 0)
            index = random.choice(indices)
            individual[index] = 1
    return individual


def mutateGeneration(newGen, optimal_plant_loc):
    for i in range(len(newGen)):
        if random.random() * 100 < optimal_plant_loc.config.thermal_network.chance_of_mutation:
            newGen[i] = mutateLocation(newGen[i], optimal_plant_loc)
    return optimal_plant_loc.population


# ============================
# test
# ============================


def main(config):
    """
    runs an optimization calculation for the plant location in the thermal network.
    """
    print('Running thermal_network plant location optimization for scenario %s' % config.scenario)
    start = time.time()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    gv = cea.globalvar.GlobalVariables()
    network_type = config.thermal_network.network_type

    optimal_plant_loc = Optimize_Network(locator, config, network_type, gv)

    total_demand = pd.read_csv(locator.get_total_demand())
    optimal_plant_loc.building_names = total_demand.Name.values
    optimal_plant_loc.number_of_buildings = total_demand.Name.count()

    optimal_plant_loc.cost_storage = pd.DataFrame(np.zeros((3, optimal_plant_loc.config.thermal_network.initialind)))
    optimal_plant_loc.cost_storage.columns = optimal_plant_loc.building_names
    optimal_plant_loc.cost_storage.index = ['Capex_total', 'Opex_total', 'Cost_total']

    newMutadedGen = generateInitialPopulation(optimal_plant_loc)
    for generation_number in range(len(optimal_plant_loc.config.number_of_generations)):
        print 'Running optimization for generation number ', generation_number
        sortedPop = plant_location_cost_calculation(newMutadedGen, optimal_plant_loc)
        print 'Lowest cost individual: ', sortedPop[0], '\n'
        print 'Cost = ', sortedPop[0], '\n'
        print 'Generating next generation.'
        selectedPop = selectFromPrevPop(sortedPop, optimal_plant_loc)
        newGen = breedNewGeneration(selectedPop, optimal_plant_loc)
        newMutadedGen = mutateGeneration(newGen, optimal_plant_loc)

    # output results file to csv
    # Sort values for easier evaluation
    optimal_plant_loc.cost_storage = optimal_plant_loc.cost_storage.reindex_axis(
        sorted(optimal_plant_loc.cost_storage.columns, key=lambda x: float(x[1:])), axis=1)
    optimal_plant_loc.cost_storage.to_csv(
        optimal_plant_loc.locator.get_optimization_network_plant_location_results_file(optimal_plant_loc.network_type))

    print('thermal_network_optimization_main() succeeded')
    print('total time: ', time.time() - start)


if __name__ == '__main__':
    main(cea.config.Configuration())

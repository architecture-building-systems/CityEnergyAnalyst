"""
hydraulic network
"""

from __future__ import division
import cea.config
import cea.globalvar
import cea.inputlocator
import cea.technologies.thermal_network.thermal_network_costs
from cea.technologies.thermal_network import thermal_network_matrix as thermal_network_matrix
from cea.technologies.thermal_network.network_layout.main import network_layout as network_layout
import cea.technologies.thermal_network.thermal_network_costs as network_costs
import os
import pandas as pd
import numpy as np
import time
import operator
import random

from cea.technologies.thermal_network.thermal_network_costs import calc_network_size

__author__ = "Lennart Rogenhofer"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Lennart Rogenhofer", "Sreepathi Bhargava Krishna", "Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class Network_info(object):
    """
    Storage of information for the network currently being calculated.
    """

    def __init__(self, locator, config, network_type, gv):
        # sotre key variables
        self.locator = locator
        self.config = config
        self.network_type = network_type
        self.network_name = config.thermal_network_optimization.network_name
        # initialize optimization storage variables and dictionaries
        self.cost_storage = None
        self.building_names = None
        self.number_of_buildings_in_district = 0
        self.gv = gv
        self.prices = None
        self.network_features = None
        self.layout = 0
        self.has_loops = None
        self.populations = {}
        self.all_individuals = None
        self.generation_number = 0
        self.plant_building_index = []
        self.disconnected_buildings_index = []
        # list of all possible heating or cooling systems. used to compare which ones are centralized / decentralized
        self.full_heating_systems = ['ahu', 'aru', 'shu', 'ww']
        self.full_cooling_systems = ['ahu', 'aru',
                                     'scu']  # Todo: add 'data', 're' here once the are available disconnectedly


def network_cost_calculation(newMutadedGen, network_info, config):
    """
    Main function which calls the objective function and stores values
    :param newMutadedGen: List containing all individuals of this generation
    :param network_info: Object storing network information.
    :return: List of sorted tuples, lowest cost first. Each tuple consists of the cost, followed by the individual as a string.
    """
    # initialize datastorage and counter
    population_performance = {}
    individual_number = 0
    # prepare datastorage for outputs
    outputs = pd.DataFrame(np.zeros((config.thermal_network_optimization.number_of_individuals, 25)))
    outputs.columns = ['individual', 'opex', 'capex', 'opex_plant', 'opex_pump', 'opex_dis_loads', 'opex_dis_build',
                       'opex_chiller', 'opex_hex', 'capex_network', 'capex_hex', 'capex_pump',
                       'capex_dis_loads', 'capex_dis_build', 'capex_chiller', 'capex_CT', 'total',
                       'plant_buildings', 'number_of_plants', 'supplied_loads', 'disconnected_buildings', 'has_loops',
                       'length', 'avg_diam', 'opex_CT']
    cost_columns = ['opex', 'capex', 'opex_plant', 'opex_pump', 'opex_dis_loads', 'opex_dis_build', 'opex_chiller',
                    'opex_hex', 'capex_hex', 'capex_network', 'capex_pump', 'capex_dis_loads',
                    'capex_dis_build', 'capex_chiller', 'capex_CT', 'total', 'length', 'avg_diam', 'opex_CT']
    # iterate through all individuals
    for individual in newMutadedGen:
        # verify that we have not previously evaluated this individual, saves time!
        if not os.path.exists(network_info.locator.get_optimization_network_individual_results_file(config.network_layout.network_type, individual)):
            # initialize disctionary for this individual
            population_individual = pd.DataFrame(np.zeros((config.thermal_network_optimization.number_of_individuals, 25)))
            population_individual.columns = ['individual', 'opex', 'capex', 'opex_plant', 'opex_pump', 'opex_dis_loads',
                               'opex_dis_build',
                               'opex_chiller', 'opex_hex', 'capex_network', 'capex_hex', 'capex_pump',
                               'capex_dis_loads', 'capex_dis_build', 'capex_chiller', 'capex_CT', 'total',
                               'plant_buildings', 'number_of_plants', 'supplied_loads', 'disconnected_buildings',
                               'has_loops',
                               'length', 'avg_diam', 'opex_CT']
            # translate barcode individual
            building_plants, disconnected_buildings = translate_individual(network_info, individual)
            # evaluate fitness function
            Capex_total, Opex_total, Costs_total, cost_storage = objective_function(network_info)

            # write result costs values to file
            total_cost = Costs_total
            opex = Opex_total
            capex = Capex_total

            # calculate network total length and average diameter
            length, average_diameter = calc_network_size(network_info)

            # save total cost to dictionary
            population_performance[total_cost] = individual

            # store all values
            if network_info.config.thermal_network.network_type == 'DH':
                load_string = network_info.config.thermal_network.substation_heating_systems
            else:
                load_string = network_info.config.thermal_network.substation_cooling_systems
            # store values
            population_individual['total'] = total_cost
            population_individual['capex'] = capex
            population_individual['opex'] = opex
            population_individual['opex_plant'] = cost_storage.ix['opex_plant'][individual_number]
            population_individual['opex_pump'] = cost_storage.ix['opex_pump'][individual_number]
            population_individual['opex_hex'] = cost_storage.ix['opex_hex'][individual_number]
            population_individual['opex_dis_loads'] = cost_storage.ix['opex_dis_loads'][individual_number]
            population_individual['opex_dis_build'] = cost_storage.ix['opex_dis_build'][individual_number]
            population_individual['opex_chiller'] = cost_storage.ix['opex_chiller'][individual_number]
            population_individual['opex_CT'] = cost_storage.ix['opex_CT'][individual_number]
            population_individual['capex_network'] = cost_storage.ix['capex_network'][individual_number]
            population_individual['capex_pump'] = cost_storage.ix['capex_pump'][individual_number]
            population_individual['capex_hex'] = cost_storage.ix['capex_hex'][individual_number]
            population_individual['capex_dis_loads'] = cost_storage.ix['capex_dis_loads'][individual_number]
            population_individual['capex_dis_build'] = cost_storage.ix['capex_dis_build'][individual_number]
            population_individual['capex_chiller'] = cost_storage.ix['capex_chiller'][individual_number]
            population_individual['capex_CT'] = cost_storage.ix['capex_CT'][individual_number]
            population_individual['number_of_plants'] = individual[6:].count(1.0)
            population_individual['has_loops'] = individual[5]
            print (building_plants)
            print (disconnected_buildings)
            population_individual['plant_buildings'] = building_plants
            population_individual['disconnected_buildings'] = disconnected_buildings
            population_individual['supplied_loads'] = load_string
            population_individual['length'] = length
            population_individual['avg_diam'] = average_diameter
            population_individual['number_of_plants'] = individual[6:].count(1.0)
            population_individual['has_loops'] = individual[5]
        else:
            # we have previously evaluated this individual so we can just read in the total cost
            total_cost = network_info.populations[str(individual)]['total']
            while total_cost in population_performance.keys():  # make sure we keep correct number of individuals in the extremely unlikely event that two individuals have the same cost
                total_cost = total_cost + 0.01
            population_performance[total_cost] = individual


        population_individual.to_csv(
            network_info.locator.get_optimization_network_individual_results_file(config.network_layout.network_type, individual))

        for column in cost_columns:
            outputs.ix[individual_number][column] = population_individual[column]
        # iterate to next individual
        individual_number += 1

    outputs.to_csv(network_info.config.get_optimization_network_generation_individuals_results_file(
        config.network_layout.network_type, network_info.generation_number))
    network_info.generation_number += 1
    # return individuals of this generation sorted from lowest cost to highest
    return sorted(population_performance.items(), key=operator.itemgetter(0))


def translate_individual(network_info, individual):
    """
    Translates individual to prepare cost evaluation
    :param network_info: Object storing network information.
    :return:
    """
    # find which buildings have plants in this individual
    network_info.plant_building_index = [i for i, x in enumerate(individual[6:]) if x == 1]
    # find diconnected buildings
    network_info.disconnected_buildings_index = [i for i, x in enumerate(individual[6:]) if x == 2]
    # output information on individual to be evaluated, translate individual
    print 'Individual: ', individual
    print 'With ', int(individual[6:].count(1.0)), ' plant(s) at building(s): '
    building_plants = []
    for building in network_info.plant_building_index:
        building_plants.append(network_info.building_names[building])
        print network_info.building_names[building]
    print 'With ', int(individual[6:].count(2.0)), ' disconnected building(s): '
    disconnected_buildings = []
    for building in network_info.disconnected_buildings_index:
        disconnected_buildings.append(network_info.building_names[building])
        print network_info.building_names[building]
    # check if we have loops or not
    if individual[5] == 1:
        network_info.has_loops = True
        print 'Network has loops.'
    else:
        network_info.has_loops = False
        print 'Network does not have loops.'
    if network_info.config.thermal_network_optimization.optimize_network_loads:
        # we are optimizing which loads to supply
        # supplied demands
        heating_systems = []
        cooling_systems = []
        if network_info.config.thermal_network.network_type == 'DH':
            heating_systems = network_info.config.thermal_network.substation_heating_systems  # placeholder until DH disconnected is available
        #    for index in range(5):
        #        if individual[int(index)] == 1:
        #            heating_systems.append(optimal_network.full_heating_systems[int(index)])
        else:  # DC mode
            for index in range(5):
                if individual[int(index)] == 1.0:  # we are supplying this cooling load
                    cooling_systems.append(network_info.full_cooling_systems[int(index)])
        network_info.config.thermal_network.substation_heating_systems = heating_systems  # save to object
        network_info.config.thermal_network.substation_cooling_systems = cooling_systems

    return building_plants, disconnected_buildings


def objective_function(network_info):
    """
    Calculates the cost of the given individual by generating a network and simulating it.
    :param network_info: Object storing network information.
    :return: total cost, opex and capex of my individual
    """
    # convert indices into building names of plant buildings and disconnected buildings
    plant_building_names = []
    disconnected_building_names = []
    for building in network_info.plant_building_index:  # translate building indexes to names
        plant_building_names.append(network_info.building_names[building])
    # translate disconnected building indexes to building names
    for building in network_info.disconnected_buildings_index:
        disconnected_building_names.append(network_info.building_names[building])
    # if we want to optimize whether or not we will use loops, we need to overwrite this flag of the config file
    if network_info.config.thermal_network_optimization.optimize_loop_branch:
        if network_info.has_loops:  # we have loops, so we need to tell the network generation script this
            network_info.config.network_layout.allow_looped_networks = True
        else:  # we don't have loops, so we need to tell the network generation script this
            network_info.config.network_layout.allow_looped_networks = False

    if len(disconnected_building_names) >= len(network_info.building_names) - 1:  # all buildings disconnected
        print 'All buildings disconnected'
        network_info.config.thermal_network.disconnected_buildings = []
        # we need to create a network and run the thermal network matrix to maintain the workflow.
        # But no buildings are connected so this will make problems.
        # So we fake that buildings are connected but no loads are supplied to make 0 costs
        # save originals so that we can revert this later
        original_heating_systems = network_info.config.thermal_network.substation_heating_systems
        original_cooling_systems = network_info.config.thermal_network.substation_cooling_systems
        # set all loads to 0 to make sure that we have no cost for the network
        network_info.config.thermal_network.substation_heating_systems = []
        network_info.config.thermal_network.substation_cooling_systems = []
        # generate a network with all buildings connected but no loads
        network_layout(network_info.config, network_info.locator, network_info.building_names,
                       optimization_flag=True)
        # simulate the network with 0 loads, very fast, 0 cost, but necessary to generate the excel output files
        thermal_network_matrix.main(network_info.config)
        # set all buildings to disconnected
        network_info.config.thermal_network.disconnected_buildings = network_info.building_names
        # set all indexes as disconnected
        network_info.disconnected_buildings_index = [i for i in range(len(network_info.building_names))]
        # revert cooling and heating systems to original
        network_info.config.thermal_network.substation_heating_systems = original_heating_systems
        network_info.config.thermal_network.substation_cooling_systems = original_cooling_systems
    else:
        print 'We have at least one connected building.'
        # save which buildings are disconnected
        network_info.config.thermal_network.disconnected_buildings = disconnected_building_names
        # create the network specified by the individual
        network_layout(network_info.config, network_info.locator, plant_building_names,
                       optimization_flag=True)
        # run the thermal_network_matrix simulation with the generated network
        thermal_network_matrix.main(network_info.config)

    ## Cost calculations
    Capex_total, Opex_total, Costs_total, cost_storage = network_costs.calc_Ctot_cs_district (network_info)


    return Capex_total, Opex_total, Costs_total, cost_storage


def selectFromPrevPop(sortedPrevPop, network_info):
    """
    Selects individuals from the previous generation for breeding and adds a predefined number of new "lucky"
    individuals which are new individuals added the gene pool.
    :param sortedPrevPop: List of tuples of individuals from previous generation, sorted by increasing cost
    :param network_info: Object storing network information.
    :return: list of individuals to breed
    """
    next_Generation = []
    # pick the individuals with the lowest cost
    for i in range(0,
                   (network_info.config.thermal_network_optimization.number_of_individuals -
                    network_info.config.thermal_network_optimization.lucky_few)):
        next_Generation.append(sortedPrevPop[i][1])
    # add a predefined amount of 'fresh' individuals to the mix
    while len(next_Generation) < network_info.config.thermal_network_optimization.number_of_individuals:
        lucky_individual = random.choice(generateInitialPopulation(network_info))
        # make sure we don't have duplicates
        if lucky_individual not in next_Generation:
            next_Generation.append(lucky_individual)
    # randomize order before breeding
    random.shuffle(next_Generation)
    return next_Generation


def breedNewGeneration(selectedInd, optimal_network):
    """
    Breeds new generation for genetic algorithm. Here we don't assure that each parent is chosen at least once, but the expected value
    is that each parent should be chosen twice.
    E.g. we have N individuals. The chance of being parent 1 is 1/N, the chance of being parent 2 is (1-1/N)*1/(N-1).
    So the probability of being one of the two parents of any child is 1/N + (1-1/N)*1/(N-1) = 2/N. Since there are N children,
    the expected value is 2.
    :param selectedInd: list of individuals to breed
    :param optimal_network: Object sotring network information
    :return: newly breeded generation
    """
    newGeneration = []
    # make sure we have the correct amount of individuals
    while len(newGeneration) < optimal_network.config.thermal_network_optimization.number_of_individuals:
        # choose random parents
        first_parent = random.choice(selectedInd)
        second_parent = random.choice(selectedInd)
        # assure that both parents are not the same individual
        while second_parent == first_parent:
            second_parent = random.choice(selectedInd)
        # setup storage for child
        child = np.zeros(len(first_parent))
        # iterate through parent individuals
        for j in range(len(first_parent)):
            # if both parents have the same value, it is passed on to the child
            if int(first_parent[j]) == int(second_parent[j]):
                child[j] = float(first_parent[j])
            else:  # both parents do not have the same value
                # we randomly chose from which parent we inherit
                which_parent = np.random.random_integers(low=0, high=1)
                if which_parent == 0:
                    child[j] = float(first_parent[j])
                else:
                    child[j] = float(second_parent[j])
        # make sure that we do not have too many plants now
        while list(child[6:]).count(1.0) > optimal_network.config.thermal_network_optimization.max_number_of_plants:
            # we have too many plants
            # find all plant indices
            plant_indices = [i for i, x in enumerate(child) if x == 1.0]
            # chose a random one
            random_plant = random.choice(list(plant_indices))
            if optimal_network.config.thermal_network_optimization.use_rule_based_approximation:
                anchor_building_index = calc_anchor_load_building(optimal_network)  # find the anchor index
            # make sure we are not overwriting the values of network layout information or the anchor buliding plant
            while random_plant < 6:  # these values are network information, not plant location
                random_plant = random.choice(list(plant_indices))  # find a new index
                if optimal_network.config.thermal_network_optimization.use_rule_based_approximation:
                    while random_plant == anchor_building_index:
                        random_plant = random.choice(list(
                            plant_indices))  # we chose the anchor load, but want to keep this one. So chose a new random index

            if optimal_network.config.thermal_network_optimization.optimize_building_connections:
                # we are optimizing which buildings to connect
                random_choice = np.random.random_integers(low=0,
                                                          high=1)  # either remove a plant or disconnect the building completely
            else:
                random_choice = 0  # we are not disocnnecting buildings, so always remove a plant, never disconnect
            if random_choice == 0:  # remove a plant
                child[int(random_plant)] = 0.0
            else:  # disconnect a building
                child[int(random_plant)] = 2.0
        # make sure we still have the necessary minimum amount of plants
        while list(child[6:]).count(1.0) < optimal_network.config.thermal_network_optimization.min_number_of_plants:
            # we don't have enough plants
            # Add one plant
            # find all non plant indices
            if optimal_network.config.thermal_network_optimization.optimize_building_connections:
                random_choice = np.random.random_integers(low=0,
                                                          high=1)  # either we put a plant at a previously disconnected building or at a building already in the network
            else:
                random_choice = 0
            if random_choice == 0:
                # find all connected buildings without a plant
                indices = [i for i, x in enumerate(child) if np.isclose(x, 0.0)]
            else:
                # find all disconnected buildings
                indices = [i for i, x in enumerate(child) if np.isclose(x, 2.0)]
            if len(indices) > 0:  # we have some buildings to chose from
                index = int(random.choice(indices))  # chose a random one
                while index < 6:  # apply only to fields which save plant information
                    index = random.choice(list(indices))
                child[index] = 1.0  # set a plant here
        # apply rule based approximation to network loads
        if optimal_network.config.thermal_network_optimization.use_rule_based_approximation == True:
            child[1] = child[0]  # supply both of ahu and aru or none of the two
        # make sure we don't have duplicates
        if list(child) not in newGeneration:
            newGeneration.append(list(child))
    return newGeneration


def generate_plants(optimal_network, new_plants):
    """
    Generates the number of plants given in the config files at random, permissible, building locations.
    :param optimal_network: Object containing network information.
    :return: list of plant locations
    """

    disconnected_buildings_index = [i for i, x in enumerate(new_plants) if x == 2.0]  # count all disconnected buildings
    if not len(disconnected_buildings_index) == len(
            new_plants):  # we have at least one connected building so we need a plant
        if optimal_network.config.thermal_network_optimization.use_rule_based_approximation:
            # if this is set we are using a rule based approximation, so the first plant is at the load anchor
            anchor_building_index = calc_anchor_load_building(optimal_network)  # find anchor load building
            # setting the value 1.0 means we have a plant here
            new_plants[anchor_building_index] = 1.0
        else:
            # no rule based approach so just add a plant somewhere random, but check if this is an acceptable plant location
            random_index = admissible_plant_location(
                optimal_network) - 6  # -6 necessary to make sure our index is at the right place
            new_plants[random_index] = 1.0
        # check how many more plants we need to add (we already added one)
        if optimal_network.config.thermal_network_optimization.min_number_of_plants != optimal_network.config.thermal_network_optimization.max_number_of_plants:
            # if our minimum and maximum number of plants is the same, we have a fixed amount of plants to add.
            # this is not the case here, so we add a random amount within our constraints
            number_of_plants_to_add = np.random.random_integers(
                low=optimal_network.config.thermal_network_optimization.min_number_of_plants - 1, high=(
                        optimal_network.config.thermal_network_optimization.max_number_of_plants - 1))  # minus 1 because we already added one
        else:
            # add the number of plants defined from the config file
            number_of_plants_to_add = optimal_network.config.thermal_network_optimization.min_number_of_plants - 1  # minus 1 because we already added one
        while list(new_plants).count(1.0) < number_of_plants_to_add + 1:  # while we still need to add plants
            random_index = admissible_plant_location(optimal_network) - 6  # chose a random place to add the plant
            new_plants[random_index] = 1.0  # set to a plant
    return list(new_plants)


def calc_anchor_load_building(network_info):
    """

    :param network_info: Object storing network information.
    :return: building index of system load anchor
    """

    #TODO: adapt this function to only include loads that are connected to the network for load anchor calculation

    # read in building demands
    total_demand = pd.read_csv(network_info.locator.get_total_demand())
    if network_info.network_type == "DH":
        field = "QH_sys_MWhyr"
    elif network_info.network_type == "DC":
        field = "QC_sys_MWhyr"
    max_value = total_demand[field].max()  # find maximum value
    building_series = total_demand['Name'][total_demand[field] == max_value].values[0]
    # find building index at which the demand is the maximum value
    building_index = np.where(network_info.building_names == building_series)[0]
    return int(building_index)


def disconnect_buildings(network_info):
    """
    Disconnects a random amount of buildings from the network. Setting the value '2' means the building is disconnected.
    :param network_info: Object containing network information.
    :param new_plants: list of plants.
    :return: list of plant locations
    """
    # initialize storage of plants and disconneted buildings
    new_buildings = np.zeros(network_info.number_of_buildings_in_district)
    # choose random amount, choose random locations, start disconnecting buildings
    random_amount = np.random.random_integers(low=0, high=(network_info.number_of_buildings_in_district - 1))
    # disconnect a random amount of buildings
    for i in range(random_amount):
        # chose a random location / index to disconnect
        random_index = np.random.random_integers(low=0, high=(network_info.number_of_buildings_in_district - 1))
        while new_buildings[random_index] == 2.0:
            # if this building is already disconnected, chose a different index
            random_index = np.random.random_integers(low=0, high=(network_info.number_of_buildings_in_district - 1))
        new_buildings[random_index] = 2.0
    # return list of disconnected buildings
    return list(new_buildings)


def admissible_plant_location(optimal_network):
    """
    This function returns a random index within the individual at which a plant is permissible.
    :param optimal_network: Object storing network information
    :return: permissible index of plant within an individual
    """
    # flag to indicate if we have found an admissible plant location
    admissible_plant_location = False
    while not admissible_plant_location:
        # generate a random index within our individual
        random_index = np.random.random_integers(low=6, high=(optimal_network.number_of_buildings_in_district + 5))
        # check if the building at this index is in our permitted building list
        if optimal_network.building_names[
            random_index - 6] in optimal_network.config.thermal_network_optimization.possible_plant_sites:
            # if yes, we have a suitable location
            admissible_plant_location = True
    return random_index


def generateInitialPopulation(network_info):
    """
    Generates the initial population for network optimization.
    :param network_info: Object storing network information
    :return: returns list of individuals as initial population for genetic algorithm
    """
    # initialize list of initial population
    initialPop = []
    while len(
            initialPop) < network_info.config.thermal_network_optimization.number_of_individuals:  # assure we have the correct amount of individuals
        # generate list of where our plants are
        if network_info.config.thermal_network_optimization.optimize_building_connections:
            # if this option is set, we are optimizing which buildings to connect, so we need to disconnect some buildings
            new_plants = disconnect_buildings(network_info)
        else:
            # we are not optimizing which buildings to connect, so start with a clean slate of all zeros
            new_plants = np.zeros(network_info.number_of_buildings_in_district)
            # read in the list of disconnected buildings from config file, if any are given
            for building in network_info.config.thermal_network.disconnected_buildings:
                for index, building_name in enumerate(network_info.building_names):
                    if str(building) == str(building_name):
                        new_plants[index] = 2.0
        # add plants to our network
        new_plants = generate_plants(network_info, new_plants)
        if network_info.config.thermal_network_optimization.optimize_loop_branch:
            # we are optimizing if we have a loop or not, set randomly to eithre 0 or 1
            loop_no_loop_binary = np.random.random_integers(low=0, high=1)  # 1 means loops, 0 means no loops
        else:  # we are not optimizing loops or not, so read from config file input
            if network_info.config.network_layout.allow_looped_networks:  # allow loop networks is true
                loop_no_loop_binary = 1.0  # we have a loop
            else:  # branched networks only
                loop_no_loop_binary = 0.0
        # list of integers indicaitong which loads are connected, 0 is disconnected, 1 is connected
        # for DH: ahu, aru, shu, ww, 0.0
        # for DC: ahu, aru, scu, data, re
        load_type = [0.0, 0.0, 0.0, 0.0, 0.0]
        if network_info.config.thermal_network_optimization.optimize_network_loads:
            # we are optimizing which to connect
            for i in range(
                    3):  # only the first three since currently the network simulation only allows disconnected loads of AHU, ARU, SCU
                load_type[i] = float(np.random.random_integers(low=0,
                                                               high=1))  # create a random list of 0 or 1, indicating if heat load is supplied by network or not
            if network_info.config.thermal_network_optimization.use_rule_based_approximation == True:  # apply rule based approcimation to network loads, AHU and ARU supplied together always
                load_type[1] = load_type[0]  # supply both of ahu and aru or none of the two
        # create individual, but together the load type, network type (branch/loop) and plant locations and connected buildings
        new_individual = load_type + [float(loop_no_loop_binary)] + new_plants
        if new_individual not in initialPop:  # add individual to list, avoid duplicates
            initialPop.append(new_individual)
    return list(initialPop)


def mutateConnections(individual, network_info):
    """
    Mutates an individuals plant location and number of plants, making sure not to violate any constraints.
    :param individual: List containing individual information
    :param network_info: Object storing network information
    :return: list of mutated individual information
    """
    # make sure we have a list type
    individual = list(individual)
    # do we connect or discconect a building
    add_or_remove = np.random.randint(low=0, high=2)
    # split individual into building information and other information storage
    building_individual = individual[6:]
    other_individual = individual[0:6]
    if network_info.config.thermal_network_optimization.use_rule_based_approximation:
        # make sure we keep the anchor load plant
        anchor_building_index = calc_anchor_load_building(network_info)
    if add_or_remove == 0:  # disconnect a building
        random_int = np.random.randint(low=0, high=2)  # disconnect a plant or a building
        index = [i for i, x in enumerate(building_individual) if x == float(random_int)]
        if index:
            if len(index) > 1:  # we have connected buildings
                random_index = np.random.randint(low=0, high=len(index))  # chose  a random one
                building_individual[random_index] = 2.0
            else:  # only one building left
                random_index = index[0]
                building_individual[random_index] = 2.0
    else:  # connect a disconnected building
        index = [i for i, x in enumerate(building_individual) if x == 2.0]  # all disconnected buildings
        if index:
            if len(index) > 0:
                random_index = np.random.randint(low=0, high=len(index))  # chose a random one
                building_individual[random_index] = 0.0
            else:
                if isinstance(index, list):
                    random_index = index[0]
                building_individual[random_index] = 0.0
    if network_info.config.thermal_network_optimization.use_rule_based_approximation:
        disconnected_buildings_index = [i for i, x in enumerate(building_individual) if
                                        x == 2.0]  # count all disconnected buildings
        if not len(disconnected_buildings_index) == len(
                building_individual):  # we have at least one connected building so we need a plant, this should be at the anchor load
            building_individual[anchor_building_index] = 1.0
    # put parts of individual back together
    individual = other_individual + building_individual
    print individual
    return list(individual)


def mutateLocation(individual, network_info):
    """
    Mutates an individuals plant location and number of plants, making sure not to violate any constraints.
    :param individual: List containing individual information
    :param network_info: Object storing network information
    :return: list of mutated individual information
    """
    # make sure we have a list type
    individual = list(individual)
    if network_info.config.thermal_network_optimization.use_rule_based_approximation:
        anchor_building_index = calc_anchor_load_building(network_info)  # keep anchor load
    # if we only have one plant, we need mutation to behave differently
    if network_info.config.thermal_network_optimization.max_number_of_plants != 1:
        # check if we have too many plants
        if list(individual[6:]).count(
                1.0) > network_info.config.thermal_network_optimization.max_number_of_plants:
            # remove one random plant
            indices = [i for i, x in enumerate(individual) if x == 1]
            while list(individual[6:]).count(
                    1.0) > network_info.config.thermal_network_optimization.max_number_of_plants:
                index = int(random.choice(indices))
                # make sure we don't overwrite values that don't store plant location information
                while index < 6:
                    index = int(random.choice(indices))
                    if network_info.config.thermal_network_optimization.use_rule_based_approximation:
                        while index == anchor_building_index:
                            index = int(random.choice(indices))
                individual[index] = 0.0
        # check if we have too few plants
        elif list(individual[6:]).count(
                1.0) < network_info.config.thermal_network_optimization.min_number_of_plants:
            while list(individual[6:]).count(
                    1.0) < network_info.config.thermal_network_optimization.min_number_of_plants:
                # Add one plant
                index = admissible_plant_location(network_info)
                individual[index] = 1.0
        else:  # not too few or too many plants
            # add or remove a plant, choose randomly
            add_or_remove = np.random.random_integers(low=0, high=1)
            if add_or_remove == 0:  # remove a plant
                indices = [i for i, x in enumerate(individual) if x == 1]
                index = int(random.choice(indices))
                # make sure we don't overwrite values that don't store plant location information
                while index < 6:
                    index = int(random.choice(indices))
                    if network_info.config.thermal_network_optimization.use_rule_based_approximation:
                        while index == anchor_building_index:
                            index = int(random.choice(indices))
                individual[index] = 0.0
            else:  # add a plant
                original_sum = sum(individual[6:])
                while sum(individual[
                          6:]) == original_sum:  # make sure we actually add a new one and don't just overwrite an existing plant
                    index = admissible_plant_location(network_info)
                    individual[index] = 1.0
            # assure we have enough plants and not too many
            while list(individual[6:]).count(
                    1.0) < network_info.config.thermal_network_optimization.min_number_of_plants:
                # Add one plant
                index = admissible_plant_location(network_info)
                individual[index] = 1.0

            while list(individual[6:]).count(
                    1.0) > network_info.config.thermal_network_optimization.max_number_of_plants:
                indices = [i for i, x in enumerate(individual) if x == 1]
                index = int(random.choice(indices))
                # make sure we don't overwrite values that don't store plant location information
                while index < 6:
                    index = int(random.choice(indices))
                    if network_info.config.thermal_network_optimization.use_rule_based_approximation:
                        while index == anchor_building_index:
                            index = int(random.choice(indices))
                individual[index] = 0.0

    else:
        # we only have one plant so we will mutate this
        if not network_info.config.thermal_network_optimization.use_rule_based_approximation:  # if we use the ruled based approach with only one plant, it stays at the load anchor.
            # remove the plant
            plant_individual = individual[6:]
            other_individual = individual[0:6]
            index = [i for i, x in enumerate(plant_individual) if x == 1.0]
            if len(index) > 0:
                plant_individual[int(index[0])] = 0.0
            individual = other_individual + plant_individual
            # add a new one
            index = admissible_plant_location(network_info)
            individual[index] = 1.0
    return list(individual)


def mutateLoad(individual, network_info):
    """
    Mutates an individuals type of heat loads covered by the network, making sure not to violate any constraints.
    :param individual: List containing individual information
    :param network_info: Object storing network information
    :return: list of mutated individual information
    """
    # make sure we have a list type
    individual = list(individual)
    # invert one random byte
    if network_info.network_type == 'DH':
        random_choice = np.random.random_integers(low=0, high=0)  # no disconnected cost information available
    else:
        random_choice = np.random.random_integers(low=0,
                                                  high=2)  # once disconnected cost information for data and re available increase to 4
    if individual[random_choice] == 1.0:
        individual[random_choice] = 0.0
    else:
        individual[random_choice] = 1.0
    if network_info.config.thermal_network_optimization.use_rule_based_approximation and network_info.config.thermal_network_optimization.optimize_network_loads:  # apply rule based approcimation to network loads
        individual[1] = individual[0]  # supply both of ahu and aru or none of the two
    return list(individual)


def mutateLoop(individual):
    """
    Mutates an individuals loop/branch information, making sure not to violate any constraints.
    :param individual: List containing individual information
    :return: list of mutated individual information
    """
    # make sure we have a list type
    individual = list(individual)
    # keep our loop or not
    keep_or_remove = np.random.random_integers(low=0, high=1)
    if keep_or_remove == 1:  # switch value
        if individual[5] == 1.0:  # loops are activated
            individual[5] = 0.0  # turn off
        else:  # branches only
            individual[5] = 1.0  # turn on loops
    return list(individual)


def mutateGeneration(newGen, network_info):
    """
    Checks if an individual should be mutated and calls the corresponding functions.
    :param newGen: Generation to mutate
    :param network_info: Object storing network information
    :return: Mutated generation
    """
    # iterate through individuals of this generation
    for i in range(len(newGen)):
        random.seed()
        # check if we should mutate
        if random.random() * 100 < network_info.config.thermal_network_optimization.chance_of_mutation:
            # we have mutation
            mutated_element_flag = False
            while not mutated_element_flag:
                mutated_individual = list(newGen[i])
                # mutate which buildings are connected
                if network_info.config.thermal_network_optimization.optimize_building_connections:
                    mutated_individual = list(mutateConnections(mutated_individual, network_info))
                # apply mutation to plant location
                mutated_individual = list(
                    mutateLocation(mutated_individual, network_info))
                # if we optimize loop/branch layout, apply mutation here
                if network_info.config.thermal_network_optimization.optimize_loop_branch:
                    mutated_individual = list(mutateLoop(mutated_individual))
                # if we optimize connected loads, aply mutation
                if network_info.config.thermal_network_optimization.optimize_network_loads:
                    mutated_individual = list(mutateLoad(mutated_individual, network_info))
                # overwrite old individual with mutated one, but make sure we didn't generate a duplicate
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
    # output configuration information
    print('Running thermal_network optimization for scenario %s' % config.scenario)
    print 'Number of individuals: ', config.thermal_network_optimization.number_of_individuals
    print 'Number of generations: ', config.thermal_network_optimization.number_of_generations
    print 'Number of lucky few individuals: ', config.thermal_network_optimization.lucky_few
    print 'Percentage chance of mutation: ', config.thermal_network_optimization.chance_of_mutation
    print 'Number of plants between ', config.thermal_network_optimization.min_number_of_plants, ' and ', config.thermal_network_optimization.max_number_of_plants
    if config.thermal_network_optimization.possible_plant_sites:
        print 'Possible plant locations: ', config.thermal_network_optimization.possible_plant_sites
    else:
        print 'Possible plant locations: all'
    print 'Optimize loop / no loops is set to: ', config.thermal_network_optimization.optimize_loop_branch
    print 'Optimize supplied thermal loads is set to: ', config.thermal_network_optimization.optimize_network_loads
    print 'Optimize which buildings are connected is set to: ', config.thermal_network_optimization.optimize_building_connections
    if config.thermal_network_optimization.use_rule_based_approximation:
        print 'Using rule based approximations.'
    # check if a net if a network name is given, else set it to an empty string
    if not config.thermal_network_optimization.network_name:
        config.thermal_network_optimization.network_name = ""
    # initialize timer
    start = time.time()
    # intitalize key variables
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    gv = cea.globalvar.GlobalVariables()
    network_type = config.thermal_network.network_type
    # overwrite config network_layout network type to make it match the network type, since we need to generate and simulate networks in this optimization
    config.network_layout.network_type = network_type
    # initialize object
    network_info = Network_info(locator, config, network_type, gv)
    # read in basic information and save to object, e.g. building demand, names, total number of buildings
    total_demand = pd.read_csv(locator.get_total_demand())
    network_info.building_names = total_demand.Name.values
    network_info.number_of_buildings_in_district = total_demand.Name.count()

    # list of possible plant location sites
    if not config.thermal_network_optimization.possible_plant_sites:
        # if there is no input from the config file as to which sites are potential plant locations, set all as possible locations
        config.thermal_network_optimization.possible_plant_sites = network_info.building_names

    # initialize data storage for later output to file
    network_info.cost_storage = pd.DataFrame(
        np.zeros((18, config.thermal_network_optimization.number_of_individuals)))
    network_info.cost_storage.index = ['capex', 'opex', 'total', 'opex_plant', 'opex_pump', 'opex_dis_loads',
                                       'opex_dis_build', 'opex_chiller', 'opex_hex', 'capex_hex',
                                       'capex_network',
                                       'capex_pump', 'capex_dis_loads', 'capex_dis_build', 'capex_chiller',
                                       'capex_CT', 'length', 'avg_diam']

    # create initial population
    print 'Creating initial population.'
    newMutadedGen = generateInitialPopulation(network_info)
    # iterate through number of generations
    for generation_number in range(config.thermal_network_optimization.number_of_generations):
        print 'Running optimization for generation number ', generation_number
        # calculate network cost for each individual and sort by increasing cost
        sortedPop = network_cost_calculation(newMutadedGen, network_info, config)
        print 'Lowest cost individual: ', sortedPop[0], '\n'
        # setup next generation
        if generation_number < config.thermal_network_optimization.number_of_generations - 1:
            # select individuals for next generation
            selectedPop = selectFromPrevPop(sortedPop, network_info)
            # breed next generation
            newGen = breedNewGeneration(selectedPop, network_info)
            # add mutations
            newMutadedGen = mutateGeneration(newGen, network_info)
            print 'Finished mutation.'

    # write values into storage dataframe and ouput results
    # setup data frame with generations, individual, opex, capex and total cost
    network_info.all_individuals = pd.DataFrame(np.zeros((
        len(network_info.populations.keys()), 24)))
    network_info.all_individuals.columns = ['individual', 'opex', 'capex', 'opex_plant', 'opex_pump',
                                            'opex_dis_loads', 'opex_dis_build', 'opex_chiller',
                                            'opex_hex', 'capex_network',
                                            'capex_pump', 'capex_dis_loads', 'capex_dis_build', 'capex_chiller',
                                            'capex_CT', 'capex_hex',
                                            'total', 'plant'
                                                     '_buildings',
                                            'number_of_plants', 'supplied_loads', 'disconnected_buildings',
                                            'has_loops', 'length', 'avg_diam']
    cost_columns = ['opex', 'capex', 'opex_plant', 'opex_pump',
                    'opex_dis_loads', 'opex_dis_build', 'opex_chiller', 'opex_hex', 'capex_network',
                    'capex_pump', 'capex_dis_loads', 'capex_dis_build', 'capex_chiller', 'capex_CT', 'capex_hex',
                    'total', 'number_of_plants', 'has_loops', 'length', 'avg_diam']
    row_number = 0
    for individual in network_info.populations.keys():
        for column in cost_columns:
            if column != 'individual':
                network_info.all_individuals.ix[row_number][column] = \
                    network_info.populations[str(individual)][column]
        row_number += 1
    # the following is a tedious workaround necessary to write string values into the dataframe and to csv..
    # todo: improve this
    row_number = 0
    for individual in network_info.populations.keys():
        network_info.all_individuals.ix[row_number]['individual'] = row_number
        network_info.all_individuals.ix[row_number]['plant_buildings'] = row_number + 100.0
        network_info.all_individuals.ix[row_number]['disconnected_buildings'] = row_number + 200.0
        network_info.all_individuals.ix[row_number]['supplied_loads'] = row_number + 300.0
        row_number += 1
    row_number = 0
    network_info.all_individuals['individual'] = \
        network_info.all_individuals['individual'].astype(str)
    network_info.all_individuals['plant_buildings'] = \
        network_info.all_individuals['plant_buildings'].astype(str)
    network_info.all_individuals['disconnected_buildings'] = \
        network_info.all_individuals['disconnected_buildings'].astype(str)
    network_info.all_individuals['supplied_loads'] = \
        network_info.all_individuals['supplied_loads'].astype(str)
    for individual in network_info.populations.keys():
        network_info.all_individuals.replace(str(float(row_number + 100)),
                                             ''.join(network_info.populations[str(individual)][
                                                         'plant_buildings']), inplace=True)
        network_info.all_individuals.replace(str(float(row_number + 200)),
                                             ''.join(network_info.populations[str(individual)][
                                                         'disconnected_buildings']), inplace=True)
        network_info.all_individuals.replace(str(float(row_number + 300)),
                                             ''.join(network_info.populations[str(individual)][
                                                         'supplied_loads']), inplace=True)
        network_info.all_individuals.replace(str(float(row_number)), str(individual), inplace=True)
        row_number += 1

    network_info.all_individuals.to_csv(locator.get_optimization_network_all_individuals_results_file(network_info.network_type),
        index='False')

    print('thermal_network_optimization_main() succeeded')
    print('total time: ', time.time() - start)


if __name__ == '__main__':
    main(cea.config.Configuration())

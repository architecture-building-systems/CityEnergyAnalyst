"""
hydraulic network
"""





import cea.config
import cea.inputlocator
import cea.technologies.thermal_network.thermal_network_costs
from cea.technologies.thermal_network.thermal_network import ThermalNetwork, thermal_network_main
from cea.technologies.network_layout.main import layout_network, NetworkLayout
from cea.utilities import epwreader
from cea.technologies.supply_systems_database import SupplySystemsDatabase
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

random.seed()

# some constants used

# structure of an individual for optimization:
# LOAD_HEADER, LOOPS, BUILDINGS
# LOAD_HEADER: list of {LOAD_CONNECTED, LOAD_DISCONNECTED} for each load (LEN_ALL_LOADS in total)
#


INDIVIDUAL_CONNECTED = 0
INDIVIDUAL_PLANT = 1
INDIVIDUAL_DISCONNECTED = 2

LOAD_CONNECTED = 1
LOAD_DISCONNECTED = 0

NETWORK_HAS_LOOPS = 1
NETWORK_HAS_NO_LOOPS = 0

DH_LOAD_TYPE_NAMES = ["ahu", "aru", "shu", "ww", None]
DC_LOAD_TYPE_NAMES = ["ahu", "aru", "scu", "data", "re"]
LEN_ALL_LOADS = len(DC_LOAD_TYPE_NAMES)
LEN_ADDITIONAL_INFO = 1  # one bit for whether the network has a loop or not
LEN_INDIVIDUAL_HEADER = LEN_ALL_LOADS + LEN_ADDITIONAL_INFO
POSSIBLE_DISCONNECTED_LOADS = {"ahu", "aru", "scu"}
LOAD_INDEX_AHU = 0
LOAD_INDEX_ARU = 1
LOOPS_INDEX = LEN_ALL_LOADS


class NetworkInfo(object):
    """
    Storage of information for the network currently being calculated.
    """

    def __init__(self, locator, config):
        """
        :type config: cea.config.Configuration
        :type locator: cea.inputlocator.InputLocator
        """
        # store key variables
        self.locator = locator

        # copy from config
        self.network_type = config.thermal_network_optimization.network_type
        self.network_name = config.thermal_network_optimization.network_name
        self.network_names = config.thermal_network_optimization.network_names
        self.use_representative_week_per_month = config.thermal_network_optimization.use_representative_week_per_month
        self.optimize_network_loads = config.thermal_network_optimization.optimize_network_loads
        self.possible_plant_sites = config.thermal_network_optimization.possible_plant_sites
        self.number_of_individuals = config.thermal_network_optimization.number_of_individuals
        self.substation_cooling_systems = config.thermal_network_optimization.substation_cooling_systems
        self.substation_heating_systems = config.thermal_network_optimization.substation_heating_systems
        self.use_rule_based_approximation = config.thermal_network_optimization.use_rule_based_approximation
        self.chance_of_mutation = config.thermal_network_optimization.chance_of_mutation
        self.optimize_building_connections = config.thermal_network_optimization.optimize_building_connections
        self.optimize_loop_branch = config.thermal_network_optimization.optimize_loop_branch
        self.min_number_of_plants = config.thermal_network_optimization.min_number_of_plants
        self.max_number_of_plants = config.thermal_network_optimization.max_number_of_plants
        self.lucky_few = config.thermal_network_optimization.lucky_few
        self.yearly_cost_calculations = config.thermal_network_optimization.yearly_cost_calculations
        self.supply_systems = SupplySystemsDatabase(locator)

        self.full_heating_systems = ['ahu', 'aru', 'shu', 'ww']
        self.full_cooling_systems = ['ahu', 'aru',
                                     'scu']  # Todo: add 'data', 're' here once the are available disconnectedly

        # disconnected buildings as per config file for thermal-network-optimization
        self.disconnected_buildings = config.thermal_network_optimization.disconnected_buildings
        self.start_t = config.thermal_network_optimization.start_t
        self.stop_t = config.thermal_network_optimization.stop_t
        self.multiprocessing = config.multiprocessing

        # initialize optimization storage variables and dictionaries
        self.cost_info = ['capex', 'opex', 'total', 'el_network_MWh',
                          'opex_plant', 'opex_pump', 'opex_dis_loads', 'opex_dis_build', 'opex_hex',
                          'capex_chiller', 'capex_CT', 'capex_pump', 'capex_dis_loads', 'capex_dis_build', 'capex_hex',
                          'capex_network', 'network_length_m', 'avg_diam_m']
        self.generation_info = ['individual', 'plant_buildings', 'number_of_plants', 'supplied_loads',
                                'disconnected_buildings', 'has_loops']
        self.cost_storage = None
        self.building_names = None
        self.number_of_buildings_in_district = 0
        self.prices = None
        self.network_features = None
        self.layout = 0
        self.has_loops = None
        self.populations = {}
        self.generation_number = 0
        self.plant_building_index = []
        self.disconnected_buildings_index = []

        # write buildings names to object
        total_demand = pd.read_csv(locator.get_total_demand())
        self.building_names = total_demand.name.values
        self.number_of_buildings_in_district = total_demand.name.count()

        self.__weather_data = None

        # write possible plant location sites to object
        if not self.possible_plant_sites:
            # if there is no input from the config file as to which sites are potential plant locations,
            # set all as possible locations
            self.possible_plant_sites = self.building_names

    def locate_individual_results(self, individual):
        return self.locator.get_optimization_network_individual_results_file(self.network_type, individual)

    @property
    def weather_data(self):
        if self.__weather_data is None:
            weather_path = self.locator.get_weather_file()
            self.__weather_data = epwreader.epw_reader(weather_path)[['year', 'drybulb_C', 'wetbulb_C']]
        return self.__weather_data


def thermal_network_optimization(config, locator):
    # initialize timer
    start = time.time()

    # initialize object
    network_info = NetworkInfo(locator, config)

    network_layout = NetworkLayout()
    network_layout.disconnected_buildings = network_info.disconnected_buildings
    network_layout.network_type = network_info.network_type

    if network_info.network_type == 'DH':
        raise ValueError('This optimization procedure is not ready for district heating yet!')

    # create initial population
    print("Creating initial population.")
    population = generate_initial_population(network_info, network_layout)

    # iterate through number of generations
    for generation_number in range(config.thermal_network_optimization.number_of_generations):
        print("Running optimization for generation number {generation}".format(generation=generation_number))
        # calculate network cost for each individual and sort by increasing cost
        sorted_population = network_cost_calculation(population, network_info, network_layout)
        print("Lowest cost individual: {winner}".format(winner=sorted_population[0]))
        print()

        # setup next generation
        # select individuals for next generation
        selected_population = select_from_previous_population(sorted_population, network_info, network_layout)
        # breed next generation
        new_generation = breed_new_generation(selected_population, network_info)
        # add mutations
        population = mutate_generation(new_generation, network_info)
        print('Finished mutation.')

    # write values into all_individuals_list and output results
    output_results_of_all_individuals(config, locator, network_info)
    print('thermal_network_optimization_main() succeeded')
    print('total time: ', time.time() - start)


def output_results_of_all_individuals(config, locator, network_info):
    """
    This function gathers all individuals evaluated and output results in one file.
    :param config:
    :type locator: cea.inputlocator.InputLocator
    :param NetworkInfo network_info: Object storing network information.
    :return:
    """
    all_individuals_list = []
    for individual in network_info.populations.keys():
        # read results from each individual
        individual_df = pd.read_csv(network_info.locate_individual_results(individual), index_col=None, header=0)
        all_individuals_list.append(individual_df.as_matrix())
    all_individuals_array = np.vstack(all_individuals_list)
    all_individuals_df = pd.DataFrame(all_individuals_array).drop(columns=[0])
    all_individuals_df.columns = network_info.generation_info + network_info.cost_info
    all_individuals_df = all_individuals_df.sort_values(by=['total'])
    locator.ensure_parent_folder_exists(locator.get_optimization_network_all_individuals_results_file(network_info.network_type))
    all_individuals_df.to_csv(locator.get_optimization_network_all_individuals_results_file(network_info.network_type),
                              index=False)
    return np.nan


def network_cost_calculation(population, network_info, network_layout):
    """
    Main function which calls the objective function and stores values
    :param NetworkLayout network_layout:
    :param population: List containing all individuals of this generation
    :param NetworkInfo network_info: Object storing network information.
    :return: List of sorted tuples, lowest cost first. Each tuple consists of the cost, followed by the individual as a string.
    """
    # initialize data storage and counter
    population_performance = {}
    individual_number = 0
    # prepare data storage for generation_outputs_df
    generation_outputs_df = pd.DataFrame(index=list(range(network_info.number_of_individuals)),
                                         columns=network_info.generation_info + network_info.cost_info)

    # iterate through all individuals
    for individual in population:
        thermal_network = ThermalNetwork(network_info.locator, "", network_info)
        # verify that we have not previously evaluated this individual, saves time!
        if not os.path.exists(network_info.locate_individual_results(individual)):
            # initialize a dataframe for this individual
            individual_outputs_df = pd.DataFrame(index=[0], columns=generation_outputs_df.columns)
            # translate barcode individual
            building_plants, disconnected_buildings = translate_individual(network_info, individual)
            # evaluate fitness function
            capex_total, opex_total, total_cost, cost_storage_df = objective_function(network_info, network_layout,
                                                                                      thermal_network)

            # calculate network total network_length_m and average diameter
            network_length_m, average_pipe_diameter_m = calc_network_size(network_info)

            # save total cost to dictionary
            population_performance[total_cost] = individual
            print('population performance ', population_performance)

            # list supplied loads
            # FIXME: @shanshanhsieh make sure that this is being optimized for!
            if network_info.network_type == 'DH':
                list_of_supplied_loads = thermal_network.substation_heating_systems
            else:
                list_of_supplied_loads = thermal_network.substation_cooling_systems

            # store values
            individual_outputs_df['total'] = total_cost
            individual_outputs_df['capex'] = capex_total
            individual_outputs_df['opex'] = opex_total
            individual_outputs_df['el_network_MWh'] = cost_storage_df.loc['el_network_MWh'][0]
            individual_outputs_df['opex_plant'] = cost_storage_df.loc['opex_plant'][0]
            individual_outputs_df['opex_pump'] = cost_storage_df.loc['opex_pump'][0]
            individual_outputs_df['opex_hex'] = cost_storage_df.loc['opex_hex'][0]
            individual_outputs_df['opex_dis_loads'] = cost_storage_df.loc['opex_dis_loads'][0]
            individual_outputs_df['opex_dis_build'] = cost_storage_df.loc['opex_dis_build'][0]
            individual_outputs_df['capex_network'] = cost_storage_df.loc['capex_network'][0]
            individual_outputs_df['capex_pump'] = cost_storage_df.loc['capex_pump'][0]
            individual_outputs_df['capex_hex'] = cost_storage_df.loc['capex_hex'][0]
            individual_outputs_df['capex_dis_loads'] = cost_storage_df.loc['capex_dis_loads'][0]
            individual_outputs_df['capex_dis_build'] = cost_storage_df.loc['capex_dis_build'][0]
            individual_outputs_df['capex_chiller'] = cost_storage_df.loc['capex_chiller'][0]
            individual_outputs_df['capex_CT'] = cost_storage_df.loc['capex_CT'][0]
            individual_outputs_df['individual'] = str(individual)
            individual_outputs_df['number_of_plants'] = individual[LEN_INDIVIDUAL_HEADER:].count(INDIVIDUAL_PLANT)
            individual_outputs_df['has_loops'] = individual[LOOPS_INDEX]
            individual_outputs_df['plant_buildings'] = str(building_plants)
            individual_outputs_df['disconnected_buildings'] = str(
                disconnected_buildings) if disconnected_buildings != [] else 0
            individual_outputs_df['supplied_loads'] = ', '.join(list_of_supplied_loads)
            individual_outputs_df['network_length_m'] = network_length_m
            individual_outputs_df['avg_diam_m'] = average_pipe_diameter_m

            # save results of an unique individual
            individual_outputs_df.to_csv(network_info.locate_individual_results(individual))
            # add unique individual and its total costs to the populations
            network_info.populations[str(individual)] = total_cost
        else:
            # read total cost of the individual that has been evaluated
            individual_outputs_df = pd.read_csv(network_info.locate_individual_results(individual))
            total_cost = individual_outputs_df['total'][0]
            while total_cost in population_performance.keys():  # make sure we keep correct number of individuals in the extremely unlikely event that two individuals have the same cost
                total_cost = total_cost + 0.01
            population_performance[total_cost] = individual
            if str(individual) not in network_info.populations.keys():
                network_info.populations[str(individual)] = total_cost

        for column in generation_outputs_df.columns:
            generation_outputs_df.iloc[individual_number][column] = individual_outputs_df[column][0]
        # iterate to next individual
        individual_number += 1
    generation_outputs_df.to_csv(network_info.locator.get_optimization_network_generation_individuals_results_file(
        network_info.network_type, network_info.generation_number))
    network_info.generation_number += 1
    # return individuals of this generation sorted from lowest cost to highest
    return sorted(population_performance.items(), key=operator.itemgetter(0))


def translate_individual(network_info, individual):
    """
    Translates individual to prepare cost evaluation

    Extract building plant locations (building names) and a list of disconnected buildings from the individual

    :param individual: the individual to extract the information (coded as genes) from
    :param NetworkInfo network_info: Object storing network information.
    :return:
    """
    # find which buildings have plants in this individual
    network_info.plant_building_index = [i for i, x in enumerate(individual[LEN_INDIVIDUAL_HEADER:]) if x == INDIVIDUAL_PLANT]
    # find disconnected buildings
    network_info.disconnected_buildings_index = [i for i, x in enumerate(individual[LEN_INDIVIDUAL_HEADER:]) if x == INDIVIDUAL_DISCONNECTED]
    # output information on individual to be evaluated, translate individual
    print('Individual: ', individual)
    print('With ', int(individual[LEN_INDIVIDUAL_HEADER:].count(INDIVIDUAL_PLANT)), ' plant(s) at building(s): ')
    building_plants = []
    for building in network_info.plant_building_index:
        building_plants.append(network_info.building_names[building])
        print(network_info.building_names[building])
    print()
    'With ', int(individual[LEN_INDIVIDUAL_HEADER:].count(INDIVIDUAL_DISCONNECTED)), ' disconnected building(s): '
    disconnected_buildings = []
    for building in network_info.disconnected_buildings_index:
        disconnected_buildings.append(network_info.building_names[building])
        print(network_info.building_names[building])
    # check if we have loops or not
    if individual[LOOPS_INDEX] == NETWORK_HAS_LOOPS:
        network_info.has_loops = True
        print('Network has loops.')
    else:
        network_info.has_loops = False
        print('Network does not have loops.')

    if network_info.optimize_network_loads:
        # we are optimizing which loads to supply
        # supplied demands
        heating_systems = []
        cooling_systems = []
        if network_info.network_type == 'DH':
            heating_systems = network_info.substation_heating_systems  # placeholder until DH disconnected is available
        #    for index in range(5):
        #        if individual[int(index)] == 1:
        #            heating_systems.append(network_info.full_heating_systems[int(index)])
        else:  # DC mode
            for index in range(LEN_ALL_LOADS):
                if individual[int(index)] == LOAD_CONNECTED:  # we are supplying this cooling load
                    cooling_systems.append(network_info.full_cooling_systems[int(index)])
        network_info.substation_heating_systems = heating_systems  # save to object
        network_info.substation_cooling_systems = cooling_systems

    return building_plants, disconnected_buildings


def objective_function(network_info, network_layout, thermal_network):
    """
    Calculates the cost of the given individual by generating a network and simulating it.
    :param NetworkInfo network_info: Object storing network information.
    :return: total cost, opex and capex of the given individual
    """
    # convert indices into building names of plant buildings and disconnected buildings
    plant_building_names = []
    disconnected_building_names = []
    # translate building indexes to names
    for building in network_info.plant_building_index:
        plant_building_names.append(network_info.building_names[building])
    for building in network_info.disconnected_buildings_index:
        disconnected_building_names.append(network_info.building_names[building])
    # if we want to optimize whether or not we will use loops, we need to overwrite this flag of the config file
    if network_info.optimize_loop_branch:
        if network_info.has_loops:  # we have loops, so we need to tell the network generation script this
            network_layout.allow_looped_networks = True
        else:  # we don't have loops, so we need to tell the network generation script this
            network_layout.allow_looped_networks = False

    if len(disconnected_building_names) >= len(network_info.building_names) - 1:  # all buildings disconnected
        print('All buildings disconnected')
        network_layout.disconnected_buildings = []
        # we need to create a network and run the thermal network matrix to maintain the workflow.
        # But no buildings are connected so this will make problems.
        # So we fake that buildings are connected but no loads are supplied to make 0 costs
        # save originals so that we can revert this later
        original_heating_systems = thermal_network.substation_heating_systems
        original_cooling_systems = thermal_network.substation_cooling_systems
        # set all loads to 0 to make sure that we have no cost for the network
        thermal_network.substation_heating_systems = []
        thermal_network.substation_cooling_systems = []

        # generate a network with all buildings connected but no loads
        # NOTE: this changes the nodes.shp and edges.shp file and they need to be re-loaded!
        network_layout = NetworkLayout(network_info)
        layout_network(network_layout, network_info.locator, network_info.building_names, optimization_flag=True)
        thermal_network.get_thermal_network_from_shapefile()

        # simulate the network with 0 loads, very fast, 0 cost, but necessary to generate the excel output files
        # thermal_network = ThermalNetwork(network_info.locator, "", )
        thermal_network_main(network_info.locator, thermal_network, processes=1)

        # set all buildings to disconnected
        network_layout.disconnected_buildings = network_info.building_names
        # set all indexes as disconnected
        network_info.disconnected_buildings_index = [i for i in range(len(network_info.building_names))]
        # revert cooling and heating systems to original
        thermal_network.substation_heating_systems = original_heating_systems
        thermal_network.substation_cooling_systems = original_cooling_systems
    else:
        print('We have at least one connected building.')
        # create the network specified by the individual
        network_layout = NetworkLayout(network_info)
        # save which buildings are disconnected
        network_layout.disconnected_buildings = disconnected_building_names
        layout_network(network_layout, network_info.locator, plant_building_names, optimization_flag=True)
        thermal_network.get_thermal_network_from_shapefile()

        # run the thermal_network simulation with the generated network
        thermal_network_main(network_info.locator, thermal_network, processes=1)

    ## Cost calculations
    Capex_total, Opex_total, Costs_total, cost_storage = network_costs.calc_Ctot_cs_district(network_info)

    return Capex_total, Opex_total, Costs_total, cost_storage


def select_from_previous_population(sorted_previous_population, network_info, network_layout):
    """
    Selects individuals from the previous generation for breeding and adds a predefined number of new "lucky"
    individuals which are new individuals added the gene pool.
    :param sorted_previous_population: List of tuples of individuals from previous generation, sorted by increasing cost
    :param network_info: Object storing network information.
    :return: list of individuals to breed
    """
    next_generation = []
    # pick the individuals with the lowest cost
    for i in range(0, (network_info.number_of_individuals - network_info.lucky_few)):
        next_generation.append(sorted_previous_population[i][1])
    # add a predefined amount of 'fresh' individuals to the mix
    while len(next_generation) < network_info.number_of_individuals:
        lucky_individual = random.choice(generate_initial_population(network_info, network_layout))
        # make sure we don't have duplicates
        if lucky_individual not in next_generation:
            next_generation.append(lucky_individual)
    # randomize order before breeding
    random.shuffle(next_generation)
    return next_generation


def breed_new_generation(selected_individuals, network_info):
    """
    Breeds new generation for genetic algorithm. Here we don't assure that each parent is chosen at least once, but the expected value
    is that each parent should be chosen twice.
    E.g. we have N individuals. The chance of being parent 1 is 1/N, the chance of being parent 2 is (1-1/N)*1/(N-1).
    So the probability of being one of the two parents of any child is 1/N + (1-1/N)*1/(N-1) = 2/N. Since there are N children,
    the expected value is 2.
    :param selected_individuals: list of individuals to breed
    :param NetworkInfo network_info: Object storing network information.
    :return: newly bred generation
    """
    newGeneration = []
    # make sure we have the correct amount of individuals
    while len(newGeneration) < network_info.number_of_individuals:
        # choose random parents
        first_parent = random.choice(selected_individuals)
        second_parent = random.choice(selected_individuals)
        # assure that both parents are not the same individual
        while second_parent == first_parent:
            second_parent = random.choice(selected_individuals)
        # setup storage for child
        child = [INDIVIDUAL_CONNECTED] * len(first_parent)
        # iterate through parent individuals
        for j in range(len(first_parent)):
            # if both parents have the same value, it is passed on to the child
            if int(first_parent[j]) == int(second_parent[j]):
                child[j] = first_parent[j]
            else:  # both parents do not have the same value
                # we randomly chose from which parent we inherit
                child[j] = random.choice((first_parent[j], second_parent[j]))
        # make sure that we do not have too many plants now
        while list(child[LEN_INDIVIDUAL_HEADER:]).count(INDIVIDUAL_PLANT) > network_info.max_number_of_plants:
            # we have too many plants
            # find all plant indices
            plant_indices = [i for i, x in enumerate(child) if x == INDIVIDUAL_PLANT]
            # chose a random one
            random_plant = random.choice(plant_indices)
            if network_info.use_rule_based_approximation:
                anchor_building_index = calc_anchor_load_building(network_info)  # find the anchor index
            else:
                anchor_building_index = None  # we're not using rule based approximation
            # make sure we are not overwriting the values of network layout information or the anchor building plant
            while random_plant < LEN_INDIVIDUAL_HEADER:  # these values are network information, not plant location
                random_plant = random.choice(plant_indices)  # find a new index
                if network_info.use_rule_based_approximation:
                    while random_plant == anchor_building_index:
                        # we chose the anchor load, but want to keep this one. So chose a new random index
                        random_plant = random.choice(plant_indices)

            if network_info.optimize_building_connections:
                # we are optimizing which buildings to connect
                random_choice = np.random.random_integers(low=0,
                                                          high=1)  # either remove a plant or disconnect the building completely
            else:
                random_choice = 0  # we are not disconnecting buildings, so always remove a plant, never disconnect
            if random_choice == 0:  # remove a plant
                child[int(random_plant)] = INDIVIDUAL_CONNECTED
            else:  # disconnect a building
                child[int(random_plant)] = INDIVIDUAL_DISCONNECTED
        # make sure we still have the necessary minimum amount of plants
        while list(child[LEN_INDIVIDUAL_HEADER:]).count(INDIVIDUAL_PLANT) < network_info.min_number_of_plants:
            # we don't have enough plants
            # Add one plant
            # find all non plant indices
            if network_info.optimize_building_connections:
                random_choice = np.random.random_integers(low=0,
                                                          high=1)  # either we put a plant at a previously disconnected building or at a building already in the network
            else:
                random_choice = 0
            if random_choice == 0:
                # find all connected buildings without a plant
                indices = [i for i, x in enumerate(child) if x == INDIVIDUAL_PLANT]
            else:
                # find all disconnected buildings
                indices = [i for i, x in enumerate(child) if x == INDIVIDUAL_DISCONNECTED]
            if len(indices) > 0:  # we have some buildings to chose from
                index = int(random.choice(indices))  # chose a random one
                while index < LEN_INDIVIDUAL_HEADER:  # apply only to fields which save plant information
                    index = random.choice(list(indices))
                child[index] = INDIVIDUAL_PLANT  # set a plant here
        # apply rule based approximation to network loads
        if network_info.use_rule_based_approximation:
            child[LOAD_INDEX_ARU] = child[LOAD_INDEX_AHU]  # supply both of ahu and aru or none of the two
        # make sure we don't have duplicates
        if list(child) not in newGeneration:
            newGeneration.append(list(child))
    return newGeneration


def generate_plants(network_info, new_plants):
    """
    Generates the number of plants given in the config files at random, permissible, building locations.
    :param NetworkInfo network_info: Object storing network information.
    :return: list of plant locations
    """

    disconnected_buildings_index = [i for i, x in enumerate(new_plants) if x == INDIVIDUAL_DISCONNECTED]  # count all disconnected buildings
    if not len(disconnected_buildings_index) == len(
            new_plants):  # we have at least one connected building so we need a plant
        # assign plant with or without rule-based approximation
        if network_info.use_rule_based_approximation:
            # if this is set we are using a rule based approximation, so the first plant is at the load anchor
            anchor_building_index = calc_anchor_load_building(network_info)  # find anchor load building
            # setting the value 1.0 means we have a plant here
            new_plants[anchor_building_index] = INDIVIDUAL_PLANT
        else:
            # no rule based approach so just add a plant somewhere random, but check if this is an acceptable plant location
            random_index = admissible_plant_location(network_info)
            new_plants[random_index] = INDIVIDUAL_PLANT

        # assign more plants if needed
        # check how many more plants we need to add (we already added one)
        if network_info.min_number_of_plants != network_info.max_number_of_plants:
            # if our minimum and maximum number of plants is the same, we have a fixed amount of plants to add.
            # this is not the case here, so we add a random amount within our constraints
            number_of_plants_to_add = np.random.randint(
                low=network_info.min_number_of_plants - 1, # minus 1 because we already added one
                high=(network_info.max_number_of_plants))
        else:
            # add the number of plants defined from the config file
            number_of_plants_to_add = network_info.min_number_of_plants - 1  # minus 1 because we already added one
        while list(new_plants).count(INDIVIDUAL_PLANT) < number_of_plants_to_add + 1:  # while we still need to add plants
            random_index = admissible_plant_location(network_info)  # chose a random place to add the plant
            new_plants[random_index] = INDIVIDUAL_PLANT  # set to a plant
    return list(new_plants)


def calc_anchor_load_building(network_info):
    """
    Finds the building with the highest load.
    :param network_info: Object storing network information.
    :return: building index of system load anchor
    """

    # TODO: adapt this function to only include loads that are connected to the network for load anchor calculation

    # read in building demands
    total_demand = pd.read_csv(network_info.locator.get_total_demand())
    if network_info.network_type == "DH":
        field = "QH_sys_MWhyr"
    else:
        assert network_info.network_type == "DC"
        field = "QC_sys_MWhyr"
    max_value = total_demand[field].max()  # find maximum value
    building_series = total_demand['name'][total_demand[field] == max_value].values[0]
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
    # initialize storage of plants and disconnected buildings
    new_buildings = [INDIVIDUAL_PLANT] * network_info.number_of_buildings_in_district
    # choose random amount, choose random locations, start disconnecting buildings
    random_amount = np.random.random_integers(low=0, high=(network_info.number_of_buildings_in_district - 1))
    # disconnect a random amount of buildings
    for i in range(random_amount):
        # chose a random location / index to disconnect
        random_index = np.random.random_integers(low=0, high=(network_info.number_of_buildings_in_district - 1))
        while new_buildings[random_index] == INDIVIDUAL_DISCONNECTED:
            # if this building is already disconnected, chose a different index
            random_index = np.random.random_integers(low=0, high=(network_info.number_of_buildings_in_district - 1))
        new_buildings[random_index] = INDIVIDUAL_DISCONNECTED
    # return list of disconnected buildings
    return list(new_buildings)


def admissible_plant_location(network_info):
    """
    This function returns a random index within the individual at which a plant is permissible.
    :param NetworkInfo network_info: Object storing network information.
    :return: permissible index of plant within an individual
    """
    plant_name = np.random.choice(network_info.possible_plant_sites)
    plant_index = list(network_info.building_names).index(plant_name)
    return plant_index


def generate_initial_population(network_info, network_layout):
    """
    Generates the initial population for network optimization.

    :param NetworkInfo network_info: Object storing global network information (information about the whole
                                     optimization)

    :param NetworkLayout network_layout: Stores information about the specific network layout of an individual
    :return: returns list of individuals as initial population for genetic algorithm
    """
    # initialize list of initial population
    population = []
    while len(population) < network_info.number_of_individuals:
        # assure we have the correct amount of individuals by creating a (random) new individual and appending it to the
        # population if it's not already present - we stop when we have created the required amount of (unique)
        # individuals

        # list of where our plants are
        if network_info.optimize_building_connections:
            # if this option is set, we are optimizing which buildings to connect,
            # so we need to disconnect some buildings
            buildings_connectivities = disconnect_buildings(network_info)
        else:
            # we are not optimizing which buildings to connect, so start with a clean slate of all zeros
            buildings_connectivities = [INDIVIDUAL_CONNECTED] * network_info.number_of_buildings_in_district
            # read in the list of disconnected buildings from config file, if any are given
            for building in network_layout.disconnected_buildings:
                for index, building_name in enumerate(network_info.building_names):
                    if str(building) == str(building_name):
                        buildings_connectivities[index] = INDIVIDUAL_DISCONNECTED
        buildings_connectivities = generate_plants(network_info, buildings_connectivities)
        # network layout: loop or branch
        if network_info.optimize_loop_branch:
            # we are optimizing if we have a loop or not, set randomly to eithre 0 or 1
            loop_no_loop_binary = np.random.choice((NETWORK_HAS_NO_LOOPS, NETWORK_HAS_LOOPS))  # 1 means loops, 0 means no loops
        else:  # we are not optimizing loops or not, so read from config file input
            if network_layout.allow_looped_networks:  # allow loop networks is true
                loop_no_loop_binary = NETWORK_HAS_LOOPS  # we have a loop
            else:  # branched networks only
                loop_no_loop_binary = NETWORK_HAS_NO_LOOPS
        # list of integers indicating which loads are connected, 0 is disconnected, 1 is connected
        # for DH: ahu, aru, shu, ww, 0.0
        # for DC: ahu, aru, scu, data, re
        load_type = [LOAD_DISCONNECTED] * LEN_ALL_LOADS
        if network_info.optimize_network_loads:
            # we are optimizing which to connect
            for i in range(len(POSSIBLE_DISCONNECTED_LOADS)):
                # create a random list of 0 or 1, indicating if heat load is supplied by network or not
                load_type[i] = np.random.choice([LOAD_DISCONNECTED, LOAD_CONNECTED])
            if network_info.use_rule_based_approximation:
                # apply rule based approximation: AHU and ARU supplied together if connected to networks
                load_type[LOAD_INDEX_ARU] = load_type[LOAD_INDEX_AHU]  # supply both of ahu and aru or none of the two
        # create individual, put together the load type, network type (branch/loop) and plant locations / connected buildings
        new_individual = load_type + [loop_no_loop_binary] + buildings_connectivities
        # add individual to list, avoid duplicates
        if new_individual not in population:
            population.append(new_individual)
    return population


def mutate_connections(individual, network_info):
    """
    Mutates an individuals plant location and number of plants, making sure not to violate any constraints.
    :param individual: List containing individual information
    :param network_info: Object storing network information
    :return: list of mutated individual information
    """
    # make sure we have a list type
    individual = list(individual)
    # do we connect or disconnect a building
    disconnect_building = np.random.choice((True, False))
    # split individual into building information and other information storage
    individual_buildings = individual[LEN_INDIVIDUAL_HEADER:]
    individual_header = individual[0:LEN_INDIVIDUAL_HEADER]

    if disconnect_building:  # disconnect a building
        type_to_disconnect = np.random.choice((INDIVIDUAL_CONNECTED, INDIVIDUAL_PLANT))  # disconnect a plant or a building
        index = [i for i, x in enumerate(individual_buildings) if x == type_to_disconnect]
        if index:
            index_to_disconnect = np.random.choice(index)
            individual_buildings[index_to_disconnect] = INDIVIDUAL_DISCONNECTED
    else:  # connect a disconnected building
        index = [i for i, x in enumerate(individual_buildings) if x == INDIVIDUAL_DISCONNECTED]  # all disconnected buildings
        if index:
            index_to_connect = np.random.choice(index)
            individual_buildings[index_to_connect] = INDIVIDUAL_CONNECTED
    if network_info.use_rule_based_approximation:
        disconnected_buildings_index = [i for i, x in enumerate(individual_buildings) if
                                        x == INDIVIDUAL_DISCONNECTED]  # count all disconnected buildings
        if not len(disconnected_buildings_index) == len(
                individual_buildings):  # we have at least one connected building so we need a plant, this should be at the anchor load
            # make sure we keep the anchor load plant
            anchor_building_index = calc_anchor_load_building(network_info)
            individual_buildings[anchor_building_index] = INDIVIDUAL_PLANT
    # put parts of individual back together
    individual = individual_header + individual_buildings
    print("Individual after mutating connections:", individual)
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

    # split up individual into header (we don't care about that here) and buildings (what we're going to work on)
    individual_header = individual[:LEN_INDIVIDUAL_HEADER]
    individual_buildings = individual[LEN_INDIVIDUAL_HEADER:]

    # if we only have one plant, we need mutation to behave differently
    if network_info.max_number_of_plants != 1:
        # check if we have too many plants
        if individual_buildings.count(INDIVIDUAL_PLANT) > network_info.max_number_of_plants:
            while individual_buildings.count(INDIVIDUAL_PLANT) > network_info.max_number_of_plants:
                remove_one_random_plant(individual_buildings, network_info)
        # check if we have too few plants
        elif individual_buildings.count(INDIVIDUAL_PLANT) < network_info.min_number_of_plants:
            while individual_buildings.count(INDIVIDUAL_PLANT) < network_info.min_number_of_plants:
                add_one_random_plant(individual_buildings, network_info)
        else:  # not too few or too many plants
            # add or remove a plant, choose randomly
            remove_plant = np.random.choice((True, False))
            if remove_plant:  # remove a plant
                remove_one_random_plant(individual_buildings, network_info)
            else:  # add a plant, making sure we actually change something (sum will be different)
                original_sum = sum(individual_buildings)
                while sum(individual_buildings) == original_sum:
                    add_one_random_plant(individual_buildings, network_info)
            # assure we have enough plants and not too many
            while individual_buildings.count(INDIVIDUAL_PLANT) < network_info.min_number_of_plants:
                add_one_random_plant(individual_buildings, network_info)
            while individual_buildings.count(INDIVIDUAL_PLANT) > network_info.max_number_of_plants:
                remove_one_random_plant(individual_buildings, network_info)
    else:
        # we only have one plant so we will mutate this
        if not network_info.use_rule_based_approximation:  # if we use the ruled based approach with only one plant, it stays at the load anchor.
            # remove the plant
            index = [i for i, x in enumerate(individual_buildings) if x == INDIVIDUAL_PLANT]
            if index:
                individual_buildings[index[0]] = INDIVIDUAL_CONNECTED
            add_one_random_plant(individual_buildings, network_info)
    return list(individual_header + individual_buildings)


def add_one_random_plant(individual_buildings, network_info):
    # Add one plant
    index = admissible_plant_location(network_info)
    individual_buildings[index] = INDIVIDUAL_PLANT


def remove_one_random_plant(individual_buildings, network_info):
    # remove one random plant
    indices = [i for i, x in enumerate(individual_buildings) if x == INDIVIDUAL_PLANT]
    if network_info.use_rule_based_approximation:
        # keep anchor load by excluding it from the possible list of plants to remove
        anchor_building_index = calc_anchor_load_building(network_info)
        indices = [i for i in indices if i != anchor_building_index]
    index = int(random.choice(indices))
    # make sure we don't overwrite values that don't store plant location information
    individual_buildings[index] = INDIVIDUAL_CONNECTED


def mutate_load(individual, network_info):
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
    if individual[random_choice] == LOAD_CONNECTED:
        individual[random_choice] = LOAD_DISCONNECTED
    else:
        individual[random_choice] = LOAD_CONNECTED
    if network_info.use_rule_based_approximation and network_info.optimize_network_loads:
        # apply rule based approcimation to network loads
        individual[LOAD_INDEX_ARU] = individual[LOAD_INDEX_AHU]  # supply both of ahu and aru or none of the two
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
        if individual[LOOPS_INDEX] == NETWORK_HAS_LOOPS:  # loops are activated
            individual[LOOPS_INDEX] = NETWORK_HAS_NO_LOOPS  # turn off
        else:  # branches only
            individual[LOOPS_INDEX] = NETWORK_HAS_LOOPS  # turn on loops
    return list(individual)


def mutate_generation(new_generation, network_info):
    """
    Checks if an individual should be mutated and calls the corresponding functions.
    :param new_generation: Generation to mutate
    :param NetworkInfo network_info: Object storing network information
    :return: Mutated generation
    """
    # iterate through individuals of this generation
    for i in range(len(new_generation)):
        # check if we should mutate
        if random.random() * 100 < network_info.chance_of_mutation:
            # we have mutation
            mutated_element_flag = False
            while not mutated_element_flag:
                mutated_individual = list(new_generation[i])
                # mutate which buildings are connected
                if network_info.optimize_building_connections:
                    mutated_individual = list(mutate_connections(mutated_individual, network_info))
                # apply mutation to plant location
                mutated_individual = list(
                    mutateLocation(mutated_individual, network_info))
                # if we optimize loop/branch layout, apply mutation here
                if network_info.optimize_loop_branch:
                    mutated_individual = list(mutateLoop(mutated_individual))
                # if we optimize connected loads, apply mutation
                if network_info.optimize_network_loads:
                    mutated_individual = list(mutate_load(mutated_individual, network_info))
                # overwrite old individual with mutated one, but make sure we didn't generate a duplicate
                if mutated_individual not in new_generation:
                    mutated_element_flag = True
                    new_generation[i] = mutated_individual
    return new_generation


# ============================
# test
# ============================

def main(config):
    """
    runs an optimization calculation for the plant location in the thermal network.
    """
    ## output configuration information
    print('Running thermal_network optimization for scenario %s' % config.scenario)
    print('Number of individuals: ', config.thermal_network_optimization.number_of_individuals)
    print('Number of generations: ', config.thermal_network_optimization.number_of_generations)
    print('Number of lucky few individuals: ', config.thermal_network_optimization.lucky_few)
    print('Percentage chance of mutation: ', config.thermal_network_optimization.chance_of_mutation)
    print('Number of plants between ', config.thermal_network_optimization.min_number_of_plants, ' and ',
          config.thermal_network_optimization.max_number_of_plants)
    if config.thermal_network_optimization.possible_plant_sites:
        print('Possible plant locations: ', config.thermal_network_optimization.possible_plant_sites)
    else:
        print('Possible plant locations: all')
    print('Optimize loop / no loops is set to: ', config.thermal_network_optimization.optimize_loop_branch)
    print('Optimize supplied thermal loads is set to: ', config.thermal_network_optimization.optimize_network_loads)
    print('Optimize which buildings are connected is set to: ',
           config.thermal_network_optimization.optimize_building_connections)
    if config.thermal_network_optimization.use_rule_based_approximation:
        print('Using rule based approximations.')
    # check if a net if a network name is given, else set it to an empty string
    if not config.thermal_network_optimization.network_name:
        config.thermal_network_optimization.network_name = ""

    # the optimization procedure is only working for region = SG at the moment
    print('The current optimization is only working for DC networks in tropical regions (SG),',
          'future updates are on the way!')

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    # start optimization
    thermal_network_optimization(config, locator)

    return np.nan


if __name__ == '__main__':
    main(cea.config.Configuration())

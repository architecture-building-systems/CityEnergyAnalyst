from __future__ import print_function

"""
Hydraulic - thermal network
"""

from __future__ import division
import time
import numpy as np
import pandas as pd
import cea.technologies.thermal_network.substation_matrix as substation_matrix
import math
from cea.utilities import epwreader
from cea.resources import geothermal
import collections
import geopandas as gpd
import cea.config
import cea.globalvar
import cea.inputlocator
import os
import random
import networkx as nx
from itertools import repeat, izip
import multiprocessing
from math import ceil

from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK, P_WATER_KGPERM3, HOURS_IN_YEAR
from cea.technologies.constants import ROUGHNESS, NETWORK_DEPTH, REDUCED_TIME_STEPS, MAX_INITIAL_DIAMETER_ITERATIONS, \
    MAX_NODE_FLOW
from cea.optimization.constants import PUMP_ETA

__author__ = "Martin Mosteiro Romero, Shanshan Hsieh, Lennart Rogenhofer"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Martin Mosteiro Romero", "Shanshan Hsieh", "Lennart Rogenhofer", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


# Some types to group parameters in (see here for more information on named tuples:
# https://docs.python.org/2/library/collections.html#collections.namedtuple)

class ThermalNetwork(object):
    """
    A thermal network instance contains information about the edges, nodes and buildings of a thermal network
    as produced by :py:func:`get_thermal_network_from_csv` or :py:func:`get_thermal_network_from_shapefile`.

    :ivar DataFrame edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0. E.g. a plant will only have exiting flows,
                        so only negative values    (n x e)
    :ivar DataFrame all_nodes_df: DataFrame that contains all nodes, whether a node is a consumer, plant, or neither,
                                  and, if it is a consumer or plant, the name of the corresponding building (2 x n)
    :ivar DataFrame edge_df:
    """

    def __init__(self, locator, network_type, network_name, file_type, config):
        self.network_type = network_type
        self.network_name = network_name
        self.config = config
        self.locator = locator
        self.file_type = file_type

        # these fields get set later on in the thermal_network_main function
        self.T_ground_K = None  # to be filled later
        self.buildings_demands = None  # to be filled by substation_matrix.determine_building_supply_temperatures
        self.substations_HEX_specs = None  # to be filled by substation_matrix.substation_HEX_design_main
        self.t_target_supply_C = None  # to be filled from buildings_demands properties
        self.t_target_supply_df = None  # to be filled from all_nodes_df

        self.edge_mass_flow_df = None
        self.node_mass_flow_df = None
        self.thermal_demand = None
        self.pipe_properties = None

        # get the thermal network description from either csv files or shapefile
        self.edge_node_df = None
        self.all_nodes_df = None
        self.edge_df = None
        self.building_names = None
        self.pressure_loss_coeff = None

        # fields to be filled later for minimum mass flow calculations
        self.delta_cap_mass_flow = {}
        self.nodes = {}
        self.cc_old = {}
        self.ch_old = {}
        self.cc_value = {}
        self.ch_value = {}

        # flag for diameter convergence
        self.no_convergence_flag = False  # True only if network diameters do not converge
        self.problematic_edges = {}  # list of edges with low mass flows

        if file_type == 'csv':
            self.get_thermal_network_from_csv(locator, network_type, network_name)
        else:
            self.get_thermal_network_from_shapefile(locator, network_type, network_name, config)

    def clone(self):
        """Create a copy of the thermal network. Assumes the fields have all been set."""
        mini_me = ThermalNetwork(self.locator, self.network_type, self.network_name, self.file_type, self.config)
        mini_me.T_ground_K = list(self.T_ground_K)
        mini_me.buildings_demands = self.buildings_demands.copy()
        mini_me.substations_HEX_specs = self.substations_HEX_specs.copy()
        mini_me.t_target_supply_C = self.t_target_supply_C.copy()
        mini_me.t_target_supply_df = self.t_target_supply_df.copy()

        mini_me.edge_mass_flow_df = self.edge_mass_flow_df
        mini_me.node_mass_flow_df = self.node_mass_flow_df
        mini_me.thermal_demand = self.thermal_demand
        mini_me.pipe_properties = self.pipe_properties

        # get the thermal network description from either csv files or shapefile
        mini_me.edge_node_df = self.edge_node_df.copy()
        mini_me.all_nodes_df = self.all_nodes_df.copy()
        mini_me.edge_df = self.edge_df.copy()
        mini_me.building_names = self.building_names.copy()

        # fields to be filled later for minimum mass flow calculations
        mini_me.delta_cap_mass_flow = {}
        mini_me.nodes = {}
        mini_me.cc_old = {}
        mini_me.ch_old = {}
        mini_me.cc_value = {}
        mini_me.ch_value = {}

        return mini_me

    def get_thermal_network_from_csv(self, locator, network_type, network_name):
        """
        This function reads the existing node and pipe network from csv files (as provided for the Zug reference case) and
        produces an edge-node incidence matrix (as defined by Oppelt et al., 2016) as well as the length of each edge.

        :param locator: an InputLocator instance set to the scenario to work on
        :param network_type: a string that defines whether the network is a district heating ('DH') or cooling ('DC')
                             network
        :type locator: InputLocator
        :type network_type: str

        :return edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0. E.g. a plant will only have exiting flows,
                        so only negative values                                                             (n x e)
        :return all_nodes_df: DataFrame that contains all nodes, whether a node is a consumer, plant, or neither,
                            and, if it is a consumer or plant, the name of the corresponding building               (2 x n)
        :return pipe_data_df['LENGTH']: vector containing the length of each edge in the network                    (1 x e)
        :rtype edge_node_df: DataFrame
        :rtype all_nodes_df: DataFrame
        :rtype pipe_data_df['LENGTH']: array

        The following files are created by this script:
            - DH_EdgeNode: csv file containing edge_node_df stored in locator.get_optimization_network_layout_folder()
            - DH_AllNodes: csv file containing all_nodes_df stored in locator.get_optimization_network_layout_folder()

        ..[Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
        Applied Thermal Engineering, 2016.

        """

        t0 = time.clock()

        # get node and pipe data
        node_df = pd.read_csv(locator.get_network_layout_nodes_csv_file(network_type)).set_index('DC_ID')
        edge_df = pd.read_csv(locator.get_network_layout_pipes_csv_file(network_type)).set_index('DC_ID')
        edge_df.rename(columns={'LENGTH': 'pipe length'},
                       inplace=True)  # todo: could be removed when the input format of .csv is fixed

        # sort dataframe with node/edge numbers
        node_sorted_index = node_df.index.to_series().str.split('J', expand=True)[1].apply(int).sort_values(
            ascending=True)
        node_df = node_df.reindex(index=node_sorted_index.index)
        edge_sorted_index = edge_df.index.to_series().str.split('PIPE', expand=True)[1].apply(int).sort_values(
            ascending=True)
        edge_df = edge_df.reindex(index=edge_sorted_index.index)

        # create consumer and plant node vectors from node data
        for column in ['Plant', 'Sink']:
            if type(node_df[column][0]) != int:
                node_df[column] = node_df[column].astype(int)
        node_names = node_df.index.values
        consumer_nodes = np.vstack((node_names, (node_df['Sink'] * node_df['Name']).values))
        plant_nodes = np.vstack((node_names, (node_df['Plant'] * node_df['Name']).values))

        # create edge-node matrix from pipe data
        list_edges = edge_df.index.values
        list_nodes = node_df.index.values
        edge_node_matrix = np.zeros((len(list_nodes), len(list_edges)))
        for j in range(len(list_edges)):
            for i in range(len(list_nodes)):
                if edge_df['NODE2'][j] == list_nodes[i]:
                    edge_node_matrix[i][j] = 1
                elif edge_df['NODE1'][j] == list_nodes[i]:
                    edge_node_matrix[i][j] = -1
        edge_node_df = pd.DataFrame(data=edge_node_matrix, index=list_nodes, columns=list_edges)
        edge_node_df.to_csv(locator.get_optimization_network_edge_node_matrix_file(network_type, network_name))

        all_nodes_df = pd.DataFrame(index=list_nodes, columns=['Building', 'Type'])
        for i in range(len(list_nodes)):
            if consumer_nodes[1][i] != '':
                all_nodes_df.loc[list_nodes[i], 'Building'] = consumer_nodes[1][i]
                all_nodes_df.loc[list_nodes[i], 'Type'] = 'CONSUMER'
            elif plant_nodes[1][i] != '':
                all_nodes_df.loc[list_nodes[i], 'Building'] = plant_nodes[1][i]
                all_nodes_df.loc[list_nodes[i], 'Type'] = 'PLANT'
            else:
                all_nodes_df.loc[list_nodes[i], 'Building'] = 'NONE'
                all_nodes_df.loc[list_nodes[i], 'Type'] = 'NONE'
        all_nodes_df.to_csv(locator.get_optimization_network_node_list_file(network_type, network_name))

        print(time.clock() - t0, "seconds process time for Network Summary\n")

        building_names = pd.read_csv(locator.get_total_demand())['Name'].values

        self.edge_node_df = edge_node_df.copy()
        self.all_nodes_df = all_nodes_df
        self.edge_df = edge_df
        self.building_names = building_names

    def get_thermal_network_from_shapefile(self, locator, network_type, network_name, config):
        """
        This function reads the existing node and pipe network from a shapefile and produces an edge-node incidence matrix
        (as defined by Oppelt et al., 2016) as well as the edge properties (length, start node, and end node) and node
        coordinates.

        :param locator: an InputLocator instance set to the scenario to work on
        :param network_type: a string that defines whether the network is a district heating ('DH') or cooling ('DC')
                             network
        :type locator: InputLocator
        :type network_type: str

        :return edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0. E.g. a plant will only have exiting flows,
                        so only negative values                                                           (n x e)
        :return all_nodes_df: DataFrame that contains all nodes, whether a node is a consumer, plant, or neither,
                            and, if it is a consumer or plant, the name of the corresponding building               (2 x n)
        :return edge_df['pipe length']: vector containing the length of each edge in the network                    (1 x e)
        :rtype edge_node_df: DataFrame
        :rtype all_nodes_df: DataFrame
        :rtype edge_df['pipe length']: array

        The following files are created by this script:
            - DH_EdgeNode: csv file containing edge_node_df stored in locator.get_optimization_network_layout_folder()
            - DH_Node_DF: csv file containing all_nodes_df stored in locator.get_optimization_network_layout_folder()
            - DH_Pipe_DF: csv file containing edge_df stored in locator.get_optimization_network_layout_folder()

        ..[Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
        Applied Thermal Engineering, 2016.

        """

        t0 = time.clock()

        # import shapefiles containing the network's edges and nodes
        network_edges_df = gpd.read_file(locator.get_network_layout_edges_shapefile(network_type, network_name))
        network_nodes_df = gpd.read_file(locator.get_network_layout_nodes_shapefile(network_type, network_name))

        # check duplicated NODE/PIPE IDs
        duplicated_nodes = network_nodes_df[network_nodes_df.Name.duplicated(keep=False)]
        duplicated_edges = network_edges_df[network_edges_df.Name.duplicated(keep=False)]
        if duplicated_nodes.size > 0:
            raise ValueError('There are duplicated NODE IDs:', duplicated_nodes)
        if duplicated_edges.size > 0:
            raise ValueError('There are duplicated PIPE IDs:', duplicated_nodes)

        # get node and pipe information
        node_df, edge_df = extract_network_from_shapefile(network_edges_df, network_nodes_df)

        # create node catalogue indicating which nodes are plants and which consumers

        node_df.coordinates = pd.Series(node_df.coordinates)
        all_nodes_df = node_df[['Type', 'Building', 'coordinates']]
        all_nodes_df.to_csv(locator.get_optimization_network_node_list_file(network_type, network_name))
        # extract the list of buildings in the current network
        building_names = all_nodes_df.Building[all_nodes_df.Type == 'CONSUMER'].reset_index(drop=True)

        # create first edge-node matrix
        list_pipes = edge_df.index.values
        list_nodes = node_df.index.values
        edge_node_matrix = np.zeros((len(list_nodes), len(list_pipes)))
        for j in range(len(list_pipes)):  # TODO: find ways to accelerate
            for i in range(len(list_nodes)):
                if edge_df['end node'][j] == list_nodes[i]:
                    edge_node_matrix[i][j] = 1
                elif edge_df['start node'][j] == list_nodes[i]:
                    edge_node_matrix[i][j] = -1
        edge_node_df = pd.DataFrame(data=edge_node_matrix, index=list_nodes,
                                    columns=list_pipes)  # first edge-node matrix

        ## An edge node matrix is generated as a first guess and then virtual substation mass flows are imposed to
        ## calculate mass flows in each edge (mass_flow_guess).
        node_mass_flows_df = pd.DataFrame(data=np.zeros([1, len(edge_node_df.index)]), columns=edge_node_df.index)
        total_flow = 0
        number_of_plants = sum(all_nodes_df['Type'] == 'PLANT')

        for node, row in all_nodes_df.iterrows():
            if row['Type'] == 'CONSUMER':
                node_mass_flows_df[node] = 1  # virtual consumer mass flow requirement
                total_flow += 1
        for node, row in all_nodes_df.iterrows():
            if row['Type'] == 'PLANT':
                node_mass_flows_df[node] = - total_flow / number_of_plants  # virtual plant supply mass flow

        # The direction of flow is then corrected
        # keep track if there was a change for the iterative process
        changed = [True] * node_mass_flows_df.shape[1]
        while any(changed):
            for i in range(node_mass_flows_df.shape[1]):
                # we have a plant with incoming mass flows, or we don't have a plant but only exiting mass flows
                if ((node_mass_flows_df[node_mass_flows_df.columns[i]].min() < 0) and (
                        edge_node_df.iloc[i].max() > 0)) or \
                        ((node_mass_flows_df[node_mass_flows_df.columns[i]].min() >= 0) and (
                                edge_node_df.iloc[i].max() <= 0)):
                    j = np.nonzero(edge_node_df.iloc[i])[0]
                    if len(j) > 1:  # valid if e.g. if more than one flow and all flows incoming. Only need to flip one.
                        j = random.choice(j)
                    edge_node_df[edge_node_df.columns[j]] = -edge_node_df[edge_node_df.columns[j]]
                    new_nodes = [edge_df['end node'][j], edge_df['start node'][j]]
                    edge_df['start node'][j] = new_nodes[0]
                    edge_df['end node'][j] = new_nodes[1]
                    changed[i] = True
                else:
                    changed[i] = False

        # make sure there are no NONE-node at dead ends before proceeding
        plant_counter = 0
        for i in range(edge_node_df.shape[0]):
            if np.count_nonzero(
                    edge_node_df.iloc[
                        i] == 1) == 0:  # Check if only has outflowing values, if yes, it is a plant
                plant_counter += 1
        if number_of_plants != plant_counter:
            raise ValueError('Please erase ', (plant_counter - number_of_plants),
                             ' end node(s) that are neither buildings nor plants.')

        print(time.clock() - t0, "seconds process time for Network Summary\n")

        if config.thermal_network.load_max_edge_flowrate_from_previous_run:
            self.edge_node_df = pd.read_csv(
                self.locator.get_optimization_network_edge_node_matrix_file(self.network_type,
                                                                            self.network_name),
                index_col=0)
        else:
            edge_node_df.to_csv(locator.get_optimization_network_edge_node_matrix_file(network_type, network_name))
            self.edge_node_df = edge_node_df.copy()
        self.all_nodes_df = all_nodes_df
        self.edge_df = edge_df
        self.building_names = building_names


# collect the results of each call to hourly_thermal_calculation in a record
HourlyThermalResults = collections.namedtuple('HourlyThermalResults',
                                              ['T_supply_nodes', 'T_return_nodes', 'q_loss_supply_edges',
                                               'plant_heat_requirement', 'pressure_loss_system_Pa',
                                               'pressure_loss_system_kW',
                                               'pressure_loss_substations_kW', 'edge_mass_flows',
                                               'q_loss_system', 'p_loss_system_edges'])


def thermal_network_main(locator, network_type, network_name, file_type, set_diameter, config, substation_systems):
    """
    This function performs thermal and hydraulic calculation of a "well-defined" network, namely, the plant/consumer
    substations, piping routes and the pipe properties (length/diameter/heat transfer coefficient) are already 
    specified.

    The hydraulic calculation is based on Oppelt, T., et al., 2016 for the case with no loops. Firstly, the consumer
    substation heat exchanger designs are calculated according to the consumer demands at each substation. Secondly,
    the piping network is imported as a node-edge matrix (NxE), which indicates the connections of all nodes and edges
    and the direction of flow between them following graph theory. Nodes represent points in the network, which could
    be the consumers, plants or joint points. Edges represent the pipes in the network. For example, (n1,e1) = 1 denotes
    the flow enters edge "e1" at node "n1", while when (n2,e2) = -1 denotes the flow leave edge "e2" at node "n2".
    Following, a steady-state hydraulic calculation is carried out at each time-step to solve for the edge mass flow
    rates according to mass conservation equations. With the maximum mass flow calculated from each edge, the property
    of each pipe is assigned.

    Thirdly, the hydraulic thermal calculation for each time-steps over a year is based on a heat balance for each
    edge (heat at the pipe inlet equals heat at the outlet minus heat losses through the pipe). Finally, the pressure
    loss calculation is carried out based on Todini et al. (1987)

    :param locator: an InputLocator instance set to the scenario to work on
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling ('DC')
                         network
    :param file_type: string that defines the type of source file for the network to be imported ('csv' or shapefile 'shp')

    :type locator: InputLocator
    :type network_type: str
    :type file_type: str

    The following files are created by this script, depending on the network type defined in the inputs:

    - DH_EdgeNode or DC_EdgeNode: .csv, edge-node matrix for the defined network
    - DH_AllNodes or DC_AllNodes: .csv, list of plant nodes and consumer nodes and their corresponding building names
    - DH_MassFlow or DC_MassFlow: .csv, mass flow rates at each edge for each time step
    - DH_T_Supply or DC_T_Supply: .csv, describes the supply temperatures at each node at each type step
    - DH_T_Return or DC_T_Return: .csv, describes the return temperatures at each node at each type step
    - DH_Plant_heat_requirement or DC_Plant_heat_requirement: .csv, heat requirement from the plants in a district
      heating or cooling network
    - DH_P_Supply or DC_P_Supply: .csv, supply side pressure for each node in a district heating or cooling network at
      each time step
    - DH_P_Return or DC_P_Return: .csv, return side pressure for each node in a district heating or cooling network at
      each time step
    - DH_P_DeltaP or DC_P_DeltaP.csv, pressure drop over an entire district heating or cooling network at each time step

    .. [Todini & Pilati, 1987] Todini & Pilati. "A gradient method for the analysis of pipe networks," in Computer
       Applications in Water Supply Volume 1 - Systems Analysis and Simulation, 1987.

    .. [Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
       Applied Thermal Engineering, 2016.

    .. [Ikonen, E., et al, 2016] Ikonen, E., et al. Examination of Operational Optimization at Kemi District Heating
       Network. Thermal Science. 2016, Vol. 20, No.2, pp.667-678.
    """

    # # prepare data for calculation
    print('Initialize network')
    # initiate class, and get edge-node matrix from defined network
    thermal_network = ThermalNetwork(locator, network_type, network_name, file_type, config)

    # calculate ground temperature
    thermal_network.T_ground_K = calculate_ground_temperature(locator, config)
    print('Running substation design')
    # substation HEX design
    thermal_network.buildings_demands = substation_matrix.determine_building_supply_temperatures(
        thermal_network.building_names, locator, substation_systems)
    thermal_network.substations_HEX_specs, substation_HEX_Q = substation_matrix.substation_HEX_design_main(
        thermal_network.buildings_demands, substation_systems, thermal_network)

    # Output substation HEX node data
    output_hex_specs_at_nodes(substation_HEX_Q, thermal_network)

    # get hourly heat requirement and target supply temperature from each substation
    thermal_network.t_target_supply_C = read_properties_from_buildings(thermal_network.buildings_demands,
                                                                       'T_sup_target_' + network_type)
    thermal_network.t_target_supply_df = write_substation_temperatures_to_nodes_df(thermal_network.all_nodes_df,
                                                                                   thermal_network.t_target_supply_C)  # (1 x n)

    if config.thermal_network_optimization.use_representative_week_per_month:
        # we run the predefined schedule of the first week of each month for the year
        start_t = 0
        stop_t = 2016  # 24 hours x 7 days x 12 months
        prepare_inputs_of_representative_weeks(thermal_network)
    else:
        # for debugging purposes, the first and (one-past) last t for hourly calculations can be set in the config file
        start_t = config.thermal_network.start_t
        stop_t = config.thermal_network.stop_t

    print('Calculating edge mass flows')
    if config.thermal_network.load_max_edge_flowrate_from_previous_run:
        thermal_network.edge_mass_flow_df = load_max_edge_flowrate_from_previous_run(thermal_network)
        thermal_network.node_mass_flow_df = load_node_flowrate_from_previous_run(thermal_network)
    else:
        # calculate maximum edge mass flow
        thermal_network.edge_mass_flow_df = calc_max_edge_flowrate(thermal_network, set_diameter,
                                                                   start_t, stop_t, substation_systems, config,
                                                                   use_multiprocessing=config.multiprocessing)

        # save results to file
        if config.thermal_network_optimization.use_representative_week_per_month:
            # need to repeat lines to make sure our outputs have 8760 timesteps. Otherwise plots
            # and network optimization will fail as they expect 8760 timesteps.
            edge_mass_flow_for_csv = pd.DataFrame(thermal_network.edge_mass_flow_df)
            # we need to extrapolate 8760 datapoints from 2016 points from our representative weeks.
            # To do this, the initial dataset is repeated 4 times, the remaining values are filled with the average values of all above.
            edge_mass_flow_for_csv = pd.concat([edge_mass_flow_for_csv] * 4, ignore_index=True)
            while len(edge_mass_flow_for_csv.index) < HOURS_IN_YEAR:
                edge_mass_flow_for_csv = edge_mass_flow_for_csv.append(edge_mass_flow_for_csv.mean(), ignore_index=True)
            edge_mass_flow_for_csv.to_csv(
                thermal_network.locator.get_edge_mass_flow_csv_file(thermal_network.network_type,
                                                                    thermal_network.network_name))
        else:
            thermal_network.edge_mass_flow_df.to_csv(
                thermal_network.locator.get_edge_mass_flow_csv_file(thermal_network.network_type,
                                                                    thermal_network.network_name))

    # assign pipe id/od according to maximum edge mass flow
    thermal_network.pipe_properties = assign_pipes_to_edges(thermal_network, set_diameter)

    # merge pipe properties to edge_df and then output as .csv
    thermal_network.edge_df = thermal_network.edge_df.merge(thermal_network.pipe_properties.T, left_index=True,
                                                            right_index=True)
    thermal_network.edge_df.to_csv(
        thermal_network.locator.get_optimization_network_edge_list_file(network_type, network_name))

    # read in HEX pressure loss values from database
    HEX_prices = pd.read_excel(thermal_network.locator.get_supply_systems(thermal_network.config.region),
                               sheetname='HEX', index_col=0)
    a_p = HEX_prices['a']['District substation heat exchanger']
    b_p = HEX_prices['b']['District substation heat exchanger']
    c_p = HEX_prices['c']['District substation heat exchanger']
    d_p = HEX_prices['d']['District substation heat exchanger']
    e_p = HEX_prices['e'][
        'District substation heat exchanger']  # make this into list, add readout in pressure loss calc
    thermal_network.pressure_loss_coeff = [a_p, b_p, c_p, d_p, e_p]

    print('Solving hydraulic and thermal network')
    ## Start solving hydraulic and thermal equations at each time-step
    number_of_processes = config.get_number_of_processes()
    if number_of_processes > 1:
        print("Using %i CPU's" % number_of_processes)
        pool = multiprocessing.Pool(number_of_processes)
        hourly_thermal_results = pool.map(hourly_thermal_calculation_wrapper,
                                          izip(range(start_t, stop_t),
                                               repeat(thermal_network, times=(stop_t - start_t)),
                                               repeat(thermal_network.config.region, times=(stop_t - start_t))))
        pool.close()
        pool.join()
    else:
        hourly_thermal_results = map(hourly_thermal_calculation, range(start_t, stop_t),
                                     repeat(thermal_network, times=(stop_t - start_t)),
                                     repeat(thermal_network.config.region, times=(stop_t - start_t)))

    # save results of hourly values over full year, write to csv
    # edge flow rates (flow direction corresponding to edge_node_df)
    csv_outputs = {field: [getattr(htr, field) for htr in hourly_thermal_results]
                   for field in HourlyThermalResults._fields}
    save_all_results_to_csv(csv_outputs, thermal_network)

    # identify all plants
    plant_indexes = np.where(thermal_network.all_nodes_df['Type'] == 'PLANT')[0]
    # read in all node df
    all_nodes_df_output = pd.read_csv(
        thermal_network.locator.get_optimization_network_node_list_file(thermal_network.network_type,
                                                                        thermal_network.network_name))
    # add new column to dataframe
    all_nodes_df_output = all_nodes_df_output.assign(Q_hex_plant_kW=pd.Series(np.zeros(len(all_nodes_df_output.index))))
    # calculate maximum plant heat demand
    for index_number, plant_index in enumerate(plant_indexes):
        if len(plant_indexes) > 1:
            max_demand = abs(max(csv_outputs['plant_heat_requirement'][index_number]))
        else:
            max_demand = abs(max(csv_outputs['plant_heat_requirement'], key=abs))
        # add plant heat demand to node.csv file
        ID = np.where(all_nodes_df_output['Name'] == 'NODE' + str(plant_index))[0][0]
        all_nodes_df_output['Q_hex_plant_kW'][ID] = max_demand
    # Output substation HEX node data
    all_nodes_df_output.to_csv(
        thermal_network.locator.get_optimization_network_node_list_file(thermal_network.network_type,
                                                                        thermal_network.network_name))

    print("Completed thermal-hydraulic calculation.\n")

    if thermal_network.no_convergence_flag == True:  # no convergence of network diameters
        print('Results are to be treated with caution since network diameters did not converge. \n')
        if len(thermal_network.problematic_edges) > 0:
            print(
                'Revision of network design is proposed, especially the edges with their corresponding minimum mass flows prnted below: \n \n')
            for key in thermal_network.problematic_edges:
                print(key, thermal_network.problematic_edges[key])
    else:
        if len(thermal_network.problematic_edges) > 0:
            print('The following edges with corresponding minimum mass flows showed high thermal losses: \n \n')
            for key in thermal_network.problematic_edges:
                print(key, thermal_network.problematic_edges[key])


def output_hex_specs_at_nodes(substation_HEX_Q, thermal_network):
    # merge with nodes df
    substation_HEX_Q['Building'] = substation_HEX_Q.index
    all_nodes_df_output = pd.DataFrame(thermal_network.all_nodes_df.sort_values(by=['coordinates'], ascending='True'))
    all_nodes_index = all_nodes_df_output.index
    all_nodes_df_output = pd.merge(all_nodes_df_output, substation_HEX_Q, on='Building', how='outer')
    all_nodes_df_output = all_nodes_df_output.sort_values(by=['coordinates'], ascending='True')
    all_nodes_df_output.index = all_nodes_index
    all_nodes_df_output.to_csv(
        thermal_network.locator.get_optimization_network_node_list_file(thermal_network.network_type,
                                                                        thermal_network.network_name))
    return np.nan


def prepare_inputs_of_representative_weeks(thermal_network):
    hours_list = range(0, 168) + range(744, 912) + range(1416, 1584) + range(2160, 2328) + range(2880, 3048) + \
                 range(3624, 3792) + range(4344, 4512) + range(5088, 5256) + range(5832,6000) + range(6522, 6690) + \
                 range(7296, 7464) + range(8016, 8184)
    # cut out relevant parts of all dataframes
    thermal_network.T_ground_K = [value for index, value in enumerate(thermal_network.T_ground_K) if
                                  index in hours_list]
    for building in thermal_network.buildings_demands.keys():
        thermal_network.buildings_demands[building] = thermal_network.buildings_demands[building].ix[hours_list]
        thermal_network.buildings_demands[building].index = range(0, 2016)
    thermal_network.t_target_supply_C = thermal_network.t_target_supply_C.ix[hours_list]
    thermal_network.t_target_supply_C.index = range(0, 2016)
    thermal_network.t_target_supply_df = thermal_network.t_target_supply_df.ix[hours_list]
    thermal_network.t_target_supply_df.index = range(0, 2016)
    return np.nan


def save_all_results_to_csv(csv_outputs, thermal_network):
    if thermal_network.config.thermal_network_optimization.use_representative_week_per_month:
        # Flag indicating that we are running the representative week option, important for the creation of a subfolder with original results below
        representative_week = True
        # need to repeat lines to make sure our outputs have 8760 timesteps. Otherwise plots
        # and network optimization will fail as they expect 8760 timesteps.
        edge_mass_flows_for_csv = pd.DataFrame(csv_outputs['edge_mass_flows'])
        T_supply_nodes_for_csv = pd.DataFrame(csv_outputs['T_supply_nodes'])
        T_return_nodes_for_csv = pd.DataFrame(csv_outputs['T_return_nodes'])
        plant_heat_requirement_for_csv = pd.DataFrame(csv_outputs['plant_heat_requirement'])
        q_loss_system_for_csv = pd.DataFrame(csv_outputs['q_loss_system'])
        pressure_loss_system_Pa_for_csv = pd.DataFrame(csv_outputs['pressure_loss_system_Pa'])
        pressure_loss_system_kW_for_csv = pd.DataFrame(csv_outputs['pressure_loss_system_kW'])
        pressure_loss_substations_kW_for_csv = pd.DataFrame(csv_outputs['pressure_loss_substations_kW'])
        p_loss_system_edges_to_csv = pd.DataFrame(csv_outputs['p_loss_system_edges'])

        # we need to extrapolate 8760 datapoints from 2016 points from our representative weeks.
        # To do this, the initial dataset is repeated 4 times, the remaining values are filled with the average values of all above.
        edge_mass_flows_for_csv = pd.concat([edge_mass_flows_for_csv] * 4, ignore_index=True)
        while len(edge_mass_flows_for_csv.index) < HOURS_IN_YEAR:
            edge_mass_flows_for_csv = edge_mass_flows_for_csv.append(edge_mass_flows_for_csv.mean(), ignore_index=True)

        T_supply_nodes_for_csv = pd.concat([T_supply_nodes_for_csv] * 4, ignore_index=True)
        while len(T_supply_nodes_for_csv.index) < HOURS_IN_YEAR:
            T_supply_nodes_for_csv = T_supply_nodes_for_csv.append(T_supply_nodes_for_csv.mean(), ignore_index=True)

        T_return_nodes_for_csv = pd.concat([T_return_nodes_for_csv] * 4, ignore_index=True)
        while len(T_return_nodes_for_csv.index) < HOURS_IN_YEAR:
            T_return_nodes_for_csv = T_return_nodes_for_csv.append(T_return_nodes_for_csv.mean(), ignore_index=True)

        plant_heat_requirement_for_csv = pd.concat([plant_heat_requirement_for_csv] * 4, ignore_index=True)
        while len(plant_heat_requirement_for_csv.index) < HOURS_IN_YEAR:
            plant_heat_requirement_for_csv = plant_heat_requirement_for_csv.append(
                plant_heat_requirement_for_csv.mean(), ignore_index=True)

        q_loss_system_for_csv = pd.concat([q_loss_system_for_csv] * 4, ignore_index=True)
        while len(q_loss_system_for_csv.index) < HOURS_IN_YEAR:
            q_loss_system_for_csv = q_loss_system_for_csv.append(q_loss_system_for_csv.mean(), ignore_index=True)

        pressure_loss_system_kW_for_csv = pd.concat([pressure_loss_system_kW_for_csv] * 4, ignore_index=True)
        while len(pressure_loss_system_kW_for_csv.index) < HOURS_IN_YEAR:
            pressure_loss_system_kW_for_csv = pressure_loss_system_kW_for_csv.append(
                pressure_loss_system_kW_for_csv.mean(), ignore_index=True)

        pressure_loss_system_Pa_for_csv = pd.concat([pressure_loss_system_Pa_for_csv] * 4, ignore_index=True)
        while len(pressure_loss_system_Pa_for_csv.index) < HOURS_IN_YEAR:
            pressure_loss_system_Pa_for_csv = pressure_loss_system_Pa_for_csv.append(
                pressure_loss_system_Pa_for_csv.mean(), ignore_index=True)

        pressure_loss_substations_kW_for_csv = pd.concat([pressure_loss_substations_kW_for_csv] * 4, ignore_index=True)
        while len(pressure_loss_substations_kW_for_csv.index) < HOURS_IN_YEAR:
            pressure_loss_substations_kW_for_csv = pressure_loss_substations_kW_for_csv.append(
                pressure_loss_substations_kW_for_csv.mean(), ignore_index=True)

        p_loss_system_edges_to_csv = pd.concat([p_loss_system_edges_to_csv] * 4, ignore_index=True)
        while len(p_loss_system_edges_to_csv.index) < HOURS_IN_YEAR:
            p_loss_system_edges_to_csv = p_loss_system_edges_to_csv.append(p_loss_system_edges_to_csv.mean(),
                                                                           ignore_index=True)

        #Output values
        # Edge Mass Flows
        edge_mass_flows_for_csv.columns = thermal_network.edge_node_df.columns
        edge_mass_flows_for_csv.to_csv(
            thermal_network.locator.get_optimization_network_layout_massflow_file(thermal_network.network_type,
                                                                                  thermal_network.network_name), #, representative_week),
            na_rep='NaN', index=False, float_format='%.3f')

        # pressure losses over entire network in Pa
        pressure_loss_system_Pa_for_csv.columns = ['pressure_loss_supply_Pa', 'pressure_loss_return_Pa',
                                                   'pressure_loss_substations_Pa', 'pressure_loss_total_Pa']
        pressure_loss_system_Pa_for_csv.to_csv(
            thermal_network.locator.get_optimization_network_layout_pressure_drop_file(thermal_network.network_type,
                                                                                       thermal_network.network_name), #, representative_week),
            index=False, float_format='%.3f')

        # pressure losses over entire network in kW
        pressure_loss_system_kW_for_csv.columns = ['pressure_loss_supply_kW', 'pressure_loss_return_kW',
                                                   'pressure_loss_substations_kW',
                                                   'pressure_loss_total_kW']
        pressure_loss_system_kW_for_csv.to_csv(
            thermal_network.locator.get_optimization_network_layout_pressure_drop_kw_file(thermal_network.network_type,
                                                                                          thermal_network.network_name), # representative_week),
            index=False, float_format='%.3f')

        # pressure losses over substations of network
        pressure_loss_substations_kW_for_csv.columns = thermal_network.building_names
        pressure_loss_substations_kW_for_csv.to_csv(
            thermal_network.locator.get_optimization_network_substation_ploss_file(thermal_network.network_type,
                                                                                   thermal_network.network_name), #, representative_week),
            index=False,
            float_format='%.3f')

        # pressure losses over entire network in Pa
        pressure_loss_system_Pa_for_csv.columns = ['pressure_loss_supply_Pa', 'pressure_loss_return_Pa',
                                                   'pressure_loss_substations_Pa', 'pressure_loss_total_Pa']
        pressure_loss_system_Pa_for_csv.to_csv(
            thermal_network.locator.get_optimization_network_layout_pressure_drop_file(thermal_network.network_type,
                                                                                       thermal_network.network_name),
            index=False,
            float_format='%.3f')

        # heat losses over entire network
        q_loss_system_for_csv.columns = thermal_network.edge_node_df.columns
        pd.DataFrame(q_loss_system_for_csv).to_csv(
            thermal_network.locator.get_optimization_network_layout_qloss_system_file(thermal_network.network_type,
                                                                                      thermal_network.network_name),
            index=False,
            float_format='%.3f')

        # pressure losses over entire network
        p_loss_system_edges_to_csv.columns = thermal_network.edge_node_df.columns
        pd.DataFrame(p_loss_system_edges_to_csv).to_csv(
            thermal_network.locator.get_optimization_network_layout_ploss_system_edges_file(
                thermal_network.network_type,
                thermal_network.network_name),
            index=False,
            float_format='%.3f')

        # plant heat requirements
        plant_heat_requirement_for_csv.columns = filter(None, thermal_network.all_nodes_df[
            thermal_network.all_nodes_df.Type == 'PLANT'].Building.values)
        plant_heat_requirement_for_csv.to_csv(
            thermal_network.locator.get_optimization_network_layout_plant_heat_requirement_file(
                thermal_network.network_type,
                thermal_network.network_name), index=False,
            float_format='%.3f')

        # node temperatures
        T_supply_nodes_for_csv.columns = thermal_network.edge_node_df.index
        T_supply_nodes_for_csv.to_csv(
            thermal_network.locator.get_optimization_network_layout_supply_temperature_file(
                thermal_network.network_type,
                thermal_network.network_name),
            na_rep='NaN', index=False, float_format='%.3f')

        T_return_nodes_for_csv.columns = thermal_network.edge_node_df.index
        T_return_nodes_for_csv.to_csv(
            thermal_network.locator.get_optimization_network_layout_return_temperature_file(
                thermal_network.network_type,
                thermal_network.network_name),
            na_rep='NaN', index=False, float_format='%.3f')



    else:
        representative_week = False

        # Edge Mass Flows
        pd.DataFrame(csv_outputs['edge_mass_flows'], columns=thermal_network.edge_node_df.columns).to_csv(
            thermal_network.locator.get_optimization_network_layout_massflow_file(thermal_network.network_type,
                                                                                  thermal_network.network_name,
                                                                                  representative_week),
            na_rep='NaN', index=False, float_format='%.3f')

        # pressure losses over entire network in Pa
        pd.DataFrame(csv_outputs['pressure_loss_system_Pa'],
                     columns=['pressure_loss_supply_Pa', 'pressure_loss_return_Pa',
                              'pressure_loss_substations_Pa', 'pressure_loss_total_Pa']).to_csv(
            thermal_network.locator.get_optimization_network_layout_pressure_drop_file(thermal_network.network_type,
                                                                                       thermal_network.network_name,
                                                                                       representative_week),
            index=False,
            float_format='%.3f')

        # pressure losses over entire network in kW
        pd.DataFrame(csv_outputs['pressure_loss_system_kW'],
                     columns=['pressure_loss_supply_kW', 'pressure_loss_return_kW',
                              'pressure_loss_substations_kW', 'pressure_loss_total_kW']).to_csv(
            thermal_network.locator.get_optimization_network_layout_pressure_drop_kw_file(thermal_network.network_type,
                                                                                          thermal_network.network_name,
                                                                                          representative_week),
            index=False,
            float_format='%.3f')

        # pressure losses over substations of network
        pd.DataFrame(csv_outputs['pressure_loss_substations_kW'], columns=thermal_network.building_names).to_csv(
            thermal_network.locator.get_optimization_network_substation_ploss_file(thermal_network.network_type,
                                                                                   thermal_network.network_name,
                                                                                   representative_week),
            index=False,
            float_format='%.3f')

        # heat losses over entire network
        pd.DataFrame(csv_outputs['q_loss_system'], columns=thermal_network.edge_node_df.columns).to_csv(
            thermal_network.locator.get_optimization_network_layout_qloss_system_file(thermal_network.network_type,
                                                                                      thermal_network.network_name,
                                                                                      representative_week),
            index=False,
            float_format='%.3f')

        # pressure losses over entire network per edge
        pd.DataFrame(csv_outputs['p_loss_system_edges'], columns=thermal_network.edge_node_df.columns).to_csv(
            thermal_network.locator.get_optimization_network_layout_ploss_system_edges_file(
                thermal_network.network_type,
                thermal_network.network_name, representative_week),
            index=False,
            float_format='%.3f')

        # plant heat requirements
        pd.DataFrame(csv_outputs['plant_heat_requirement'],
                     columns=filter(None, thermal_network.all_nodes_df[
                         thermal_network.all_nodes_df.Type == 'PLANT'].Building.values)).to_csv(
            thermal_network.locator.get_optimization_network_layout_plant_heat_requirement_file(
                thermal_network.network_type,
                thermal_network.network_name, representative_week), index=False,
            float_format='%.3f')

        # node temperatures
        pd.DataFrame(csv_outputs['T_supply_nodes'], columns=thermal_network.edge_node_df.index).to_csv(
            thermal_network.locator.get_optimization_network_layout_supply_temperature_file(
                thermal_network.network_type,
                thermal_network.network_name, representative_week),
            na_rep='NaN', index=False, float_format='%.3f')
        pd.DataFrame(csv_outputs['T_return_nodes'], columns=thermal_network.edge_node_df.index).to_csv(
            thermal_network.locator.get_optimization_network_layout_return_temperature_file(
                thermal_network.network_type,
                thermal_network.network_name, representative_week),
            na_rep='NaN', index=False, float_format='%.3f')


def calculate_ground_temperature(locator, config):
    """
    calculate ground temperatures.

    :param locator:
    :return: list of ground temperatures, one for each hour of the year
    :rtype: list[np.float64]
    """
    weather_file = config.weather
    T_ambient_C = epwreader.epw_reader(weather_file)['drybulb_C']
    network_depth_m = NETWORK_DEPTH  # [m]
    T_ground_K = geothermal.calc_ground_temperature(locator, config, T_ambient_C.values, network_depth_m)
    return T_ground_K


def hourly_thermal_calculation_wrapper(args):
    """Wrap hourly_thermal_calculation to accept a tuple of args because multiprocessing.Pool.map only accepts one
    argument for the function."""
    return hourly_thermal_calculation(*args)


def hourly_thermal_calculation(t, thermal_network, region):
    """
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling ('DC')
                         network
    :param network_name: 'Dh' or 'DC' indicating district heating or cooling
    :param t: time step
    :param locator: an InputLocator instance set to the scenario to work on
    :param T_ground_K: Ground Temperature in Kelvin
    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0. E.g. a plant will only have exiting flows,
                        so only negative values
    :param all_nodes_df: list of plant nodes and consumer nodes and their corresponding building names
    :param edge_mass_flow_df_kgs: Mass flow over every edge
    :param t_target_supply_df: Target supply temperature of each node
    :param buildings_demands: DataFrame of building demands
    :param substations_HEX_specs: DataFrame with substation heat exchanger specs at each building
    :param edge_df: list of edges and their corresponding lengths and start and end nodes
    :param pipe_properties_df: DataFrame containing the pipe properties for each edge in the network
    :param csv_outputs: Dictionary collecting all variables which are stored for all 8760 timesteps and
        later written to csv files

    :return csv_outputs: DataFrame with calculated values
    :return edge_mass_flow_df_kgs: updated edge mass flows
    """
    locator = thermal_network.locator

    print('calculating thermal hydraulic properties of', thermal_network.network_type, 'network',
          thermal_network.network_name, '...  time step', t)

    ## solve network temperatures
    T_supply_nodes_K, \
    T_return_nodes_K, \
    plant_heat_requirement_kW, \
    thermal_network.edge_mass_flow_df.ix[t], \
    q_loss_supply_edges_kW, \
    total_heat_loss_kW = solve_network_temperatures(thermal_network, t)

    # calculate pressure at each node and pressure drop throughout the entire network
    P_supply_nodes_Pa, \
    P_return_nodes_Pa, \
    delta_P_network_Pa, \
    pressure_loss_system_kW, \
    pressure_loss_edges_kW, \
    pressure_loss_substations_kW = calc_pressure_nodes(T_supply_nodes_K, T_return_nodes_K, thermal_network, t)

    # store node temperatures and pressures, as well as plant heat requirement and overall pressure drop at each
    # time step
    hourly_thermal_results = HourlyThermalResults(
        T_supply_nodes=T_supply_nodes_K,
        T_return_nodes=T_return_nodes_K,
        q_loss_supply_edges=q_loss_supply_edges_kW,
        plant_heat_requirement=plant_heat_requirement_kW,
        pressure_loss_system_Pa=delta_P_network_Pa,
        pressure_loss_system_kW=pressure_loss_system_kW,
        pressure_loss_substations_kW=pressure_loss_substations_kW,
        edge_mass_flows=thermal_network.edge_mass_flow_df.ix[t],
        q_loss_system=total_heat_loss_kW,
        p_loss_system_edges=pressure_loss_edges_kW
    )

    return hourly_thermal_results


# ===========================
# Hydraulic calculation
# ===========================

def calc_mass_flow_edges(edge_node_df, mass_flow_substation_df, all_nodes_df, pipe_diameter_m, pipe_length_m,
                         T_edge_K):
    """
    This function carries out the steady-state mass flow rate calculation for a predefined network with predefined mass
    flow rates at each substation based on the method from Todini et al. (1987), Ikonen et al. (2016), Oppelt et al.
    (2016), etc.

    :param all_nodes_df: DataFrame containing all nodes and whether a node n is a consumer or plant node
                        (and if so, which building that node corresponds to), or neither.
    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0. E.g. a plant will only have exiting flows,
                        so only negative values                                      (n x e)
    :param mass_flow_substation_df: DataFrame containing the mass flow rate at each node n at each time
                                     of the year t
    :param pipe_diameter_m: vector containing the pipe diameter in m for each edge e in the network      (e x 1)
    :param pipe_length_m: vector containing the length in m of each edge e in the network                (e x 1)
    :param T_edge_K: matrix containing the temperature of the water in each edge e at time t             (t x e)

    :type all_nodes_df: DataFrame(t x n)
    :type edge_node_df: DataFrame
    :type mass_flow_substation_df: DataFrame
    :type pipe_diameter_m: ndarray
    :type pipe_length_m: ndarray
    :type T_edge_K: ndarray

    :return mass_flow_edge: matrix specifying the mass flow rate at each edge e at the given time step t
    :rtype mass_flow_edge: numpy.ndarray

    .. [Todini & Pilati, 1987] Todini & Pilati. "A gradient method for the analysis of pipe networks," in Computer
       Applications in Water Supply Volume 1 - Systems Analysis and Simulation, 1987.

    .. [Ikonen, E., et al, 2016] Ikonen, E., et al. Examination of Operational Optimization at Kemi District Heating
       Network. Thermal Science. 2016, Vol. 20, No.2, pp.667-678.

    .. [Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
       Applied Thermal Engineering, 2016.
    """
    edge_node_df = edge_node_df.copy()
    loops, graph = find_loops(edge_node_df)  # identifies all linear independent loops
    if loops:
        # print('Fundamental loops in the network:', loops) #returns nodes that define loop, useful for visiual verification in testing phase,

        sum_delta_m_num = np.zeros((1, len(loops)))[0]

        # if loops exist:
        # 1. calculate initial guess solution of matrix A
        # delete first plant on an edge of matrix and solution space b as these are redundant
        A = edge_node_df.drop(edge_node_df.index[0], 0)  # solution matrix A without loop equations (kirchhoff 2)
        b_init = np.nan_to_num(mass_flow_substation_df.drop(mass_flow_substation_df.columns[0], 1).transpose())
        # solution vector b of node demands
        mass_flow_edge = np.linalg.lstsq(A, b_init)[0].transpose()[0]  # solve system

        # setup iterations for implicit matrix solver
        tolerance = 0.01  # tolerance for mass flow convergence
        m_old = mass_flow_edge - mass_flow_edge  # initialize m_old vector

        # begin iterations
        iterations = 0
        while (abs(mass_flow_edge - m_old) > tolerance).any():  # while difference of mass flow on any  edge > tolerance
            m_old = np.array(mass_flow_edge)  # iterate over massflow

            # calculate value similar to Hardy Cross correction factor
            # uses Hardy Cross method but a different variation for calculating the mass flow
            delta_m_num = calc_pressure_loss_pipe(pipe_diameter_m, pipe_length_m, m_old, T_edge_K,
                                                  2) * np.sign(m_old)  # calculate pressure losses
            delta_m_den = abs(calc_pressure_loss_pipe(pipe_diameter_m, pipe_length_m, m_old, T_edge_K,
                                                      1))  # calculate derivatives of pressure losses
            delta_m_num = delta_m_num.transpose()

            sum_delta_m_num = np.zeros((1, len(loops)))[0]
            sum_delta_m_den = np.zeros((1, len(loops)))[0]

            for i in range(len(loops)):
                # calculate the mass flow correction for each loop
                # iterate over loops
                # save the edge number connecting the nodes of the loops into the variable index
                for j in range(len(loops[i])):
                    if j == len(loops[i]) - 1:
                        value = loops[i][0]
                    else:
                        value = loops[i][j + 1]
                    index = graph.get_edge_data(loops[i][j], value)
                    # check if nodes  defined in clockwise loop, to keep sign convention for Hardy Cross Method
                    if not (edge_node_df.iloc[loops[i][j]][index['edge_number']] == 1) & \
                           (edge_node_df.iloc[value][index['edge_number']] == -1):
                        clockwise = -1
                    else:
                        clockwise = 1
                    sum_delta_m_num[i] = sum_delta_m_num[i] + delta_m_num[index["edge_number"]] * clockwise
                    sum_delta_m_den[i] = sum_delta_m_den[i] + delta_m_den[index["edge_number"]]
                # calculate flow correction for each loop
                if np.isclose(sum_delta_m_den[i], 0):
                    delta_m = 0
                else:
                    delta_m = -sum_delta_m_num[i] / sum_delta_m_den[i]

                # apply mass flow correction to all edges of each loop
                for j in range(len(loops[i])):
                    if j == len(loops[i]) - 1:
                        value = loops[i][0]
                    else:
                        value = loops[i][j + 1]
                    index = graph.get_edge_data(loops[i][j], value)
                    # check if nodes  defined in clockwise loop
                    if not (edge_node_df.iloc[loops[i][j]][index['edge_number']] == 1) & \
                           (edge_node_df.iloc[value][index['edge_number']] == -1):
                        clockwise = -1
                    else:
                        clockwise = 1
                    # apply loop correction
                    mass_flow_edge[index["edge_number"]] = mass_flow_edge[index["edge_number"]] + delta_m * clockwise
            iterations = iterations + 1

            # adapt tolerance to reduce total amount of iterations
            if iterations < 20:
                tolerance = 0.01
            elif iterations < 40:
                tolerance = 0.02
            elif iterations < 80:
                tolerance = 0.04
            else:
                print('No convergence of looped massflows after ', iterations, ' iterations with a remaining '
                                                                               'difference of',
                      max(abs(mass_flow_edge - m_old)), '.')
                break
        # print('Looped massflows converged after ', iterations, ' iterations.')

    else:  # no loops
        ## remove one equation (at plant node) to build a well-determined matrix, A.
        plant_index = np.where(all_nodes_df['Type'] == 'PLANT')[0][0]  # find index of the first plant node
        A = edge_node_df.drop(edge_node_df.index[plant_index])
        b = np.nan_to_num(mass_flow_substation_df.T)
        b = np.delete(b, plant_index)
        mass_flow_edge = np.linalg.solve(A.values, b)

    # verify calculated solution
    plant_index = np.where(all_nodes_df['Type'] == 'PLANT')[0][0]  # find index of the first plant node
    A = edge_node_df.drop(edge_node_df.index[plant_index])
    b_verification = A.dot(mass_flow_edge)
    b_original = np.nan_to_num(mass_flow_substation_df.T)
    b_original = np.delete(b_original, plant_index)
    if max(abs(b_original - b_verification)) > 0.01:
        print('Error in the defined mass flows, deviation of ', max(abs(b_original - b_verification)),
              ' from node demands.')
    if loops:
        if (abs(sum_delta_m_num) > 15000).any():  # 5 kPa is sufficiently small
            print('Error in the defined mass flows, deviation of ', max(abs(sum_delta_m_num)),
                  ' from 0 pressure in loop. Most likely due to low edge flows within the loop.')

    mass_flow_edge = np.round(mass_flow_edge, decimals=5)
    return mass_flow_edge


def find_loops(edge_node_df):
    """
    This function converts the input matrix into a networkx type graph and identifies all fundamental loops
    of the network. The group of fundamental loops is defined as the series of linear independent loops which
    can be combined to form all other loops.

    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0. E.g. a plant will only have exiting flows,
                        so only negative values                               (n x e)

    :type edge_node_df: DataFrame

    :return: loops: list of all fundamental loops in the network
    :return: graph: networkx dictionary type graph of network

    :rtype: loops: list
    :rtype: graph: dictionary
    """
    edge_node_df_t = np.transpose(edge_node_df)  # transpose matrix to more intuitively setup graph

    graph = nx.Graph()  # set up networkx type graph

    for i in range(edge_node_df_t.shape[0]):
        new_edge = [0, 0]
        for j in range(0, edge_node_df_t.shape[1]):
            if edge_node_df_t.iloc[i][edge_node_df_t.columns[j]] == 1:
                new_edge[0] = j
            elif edge_node_df_t.iloc[i][edge_node_df_t.columns[j]] == -1:
                new_edge[1] = j
        graph.add_edge(new_edge[0], new_edge[1], edge_number=i)  # add edges to graph
        # edge number necessary to later identify which edges are in loop since graph is a dictionary

    loops = nx.cycle_basis(graph, 0)  # identifies all linear independent loops

    return loops, graph


def assign_pipes_to_edges(thermal_network, set_diameter):
    """
    This function assigns pipes from the catalog to the network for a network with unspecified pipe properties.
    Pipes are assigned based on each edge's minimum and maximum required flow rate. Assuming max velocity for pipe
    DN450-550 is 3 m/s; for DN600 is 3.5 m/s. min velocity for all pipes are 0.3 m/s.

    :param ThermalNetwork thermal_network: thermal network object
    :param mass_flow_df: DataFrame containing the mass flow rate for each edge e at each time of the year t
    :param locator: an InputLocator instance set to the scenario to work on
    :type mass_flow_df: DataFrame
    :type locator: InputLocator

    :return pipe_properties_df: DataFrame containing the pipe properties for each edge in the network


    """
    max_edge_mass_flow_df = pd.DataFrame(data=[(thermal_network.edge_mass_flow_df.abs()).max(axis=0)])
    max_edge_mass_flow_df.columns = thermal_network.edge_node_df.columns

    # import pipe catalog from Excel file
    pipe_catalog = pd.read_excel(thermal_network.locator.get_thermal_networks(thermal_network.config.region), sheetname=['PIPING CATALOG'])[
        'PIPING CATALOG']
    pipe_catalog['mdot_min_kgs'] = pipe_catalog['Vdot_min_m3s'] * P_WATER_KGPERM3
    pipe_catalog['mdot_max_kgs'] = pipe_catalog['Vdot_max_m3s'] * P_WATER_KGPERM3
    pipe_properties_df = pd.DataFrame(data=None, index=pipe_catalog.columns.values,
                                      columns=max_edge_mass_flow_df.columns.values)
    if set_diameter:
        # Set the pipe diameters according to the maximum flow in each edge.
        # Find the minimum pipe diameter which allows for a mass flow of this magnitude.
        for pipe in max_edge_mass_flow_df:
            pipe_found = False
            i = 0
            while pipe_found == False:
                if np.amax(np.absolute(max_edge_mass_flow_df[pipe].values)) <= pipe_catalog['mdot_max_kgs'][i]:
                    pipe_properties_df[pipe] = np.transpose(pipe_catalog[:][i:i + 1].values)
                    pipe_found = True
                elif i == (len(pipe_catalog) - 1):
                    pipe_properties_df[pipe] = np.transpose(pipe_catalog[:][i:i + 1].values)
                    pipe_found = True
                    print(pipe, 'with maximum flow rate of', max_edge_mass_flow_df[pipe].values, '[kg/s] ',
                          'requires a bigger pipe than provided in the database.', '\n',
                          'Please add a pipe with adequate pipe ',
                          'size to the Piping Catalog under ..cea/database/system/thermal_networks.xls', '\n')
                else:
                    i += 1
        # at the end save back the edges dataframe in the shapefile with the new pipe diameters
        if os.path.exists(
                thermal_network.locator.get_network_layout_edges_shapefile(thermal_network.network_type,
                                                                           thermal_network.network_name)):
            network_edges = gpd.read_file(
                thermal_network.locator.get_network_layout_edges_shapefile(thermal_network.network_type,
                                                                           thermal_network.network_name))
            network_edges['Pipe_DN'] = pipe_properties_df.loc['Pipe_DN'].values
            network_edges.to_file(
                thermal_network.locator.get_network_layout_edges_shapefile(thermal_network.network_type,
                                                                           thermal_network.network_name))
    else:
        # Find the pipe properties of the pipes from the .shp file
        # The shape file pipe DN is stored in edge_df
        for pipe, row in thermal_network.edge_df.iterrows():
            # find matching pipe DN in the pipe catalog
            index = pipe_catalog.Pipe_DN[pipe_catalog.Pipe_DN == row['Pipe_DN']].index
            if len(index) == 0:  # there is no match in the pipe catalog
                raise ValueError(
                    'A very specific bad thing happened!: One or more of the pipes diameters you indicated' '\n'
                    'are not in the pipe catalog!, please make sure your input network match the piping catalog,' '\n'
                    'otherwise :P')
            # assign pipe properties from the catalog, matching the Pipe DN of the .shp files
            pipe_properties_df[pipe] = np.transpose(pipe_catalog.loc[index].values)

    return pipe_properties_df


def calc_pressure_nodes(t_supply_node__k, t_return_node__k, thermal_network, t):
    """
    Calculates the pressure at each node based on Eq. 1 in Todini & Pilati (1987). For the pressure drop through a pipe,
    the Darcy-Weisbach equation was used as in Oppelt et al. (2016) instead of the Hazen-Williams method used by Todini
    & Pilati. Since the pressure is calculated after the mass flow rate (rather than concurrently) this is only a first
    step towards implementing the Gradient Method from Todini & Pilati used by EPANET et al.

    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0. E.g. a plant will only have exiting flows,
                        so only negative values                                                                          (n x e)
    :param pipe_diameter: vector containing the pipe diameter in m for each edge e in the network      (e x 1)
    :param pipe_length: vector containing the length in m of each edge e in the network                (e x 1)
    :param edge_mass_flow: matrix containing the mass flow rate in each edge e at time t               (1 x e)
    :param t_supply_node__k: array containing the temperature in each supply node n                       (1 x n)
    :param t_return_node__k: array containing the temperature in each return node n                       (1 x n)
    :type edge_node_df: DataFrame
    :type pipe_diameter: ndarray
    :type pipe_length: ndarray
    :type edge_mass_flow: ndarray
    :type t_supply_node__k: list
    :type t_return_node__k: list

    :return pressure_loss_nodes_supply: array containing the pressure loss at each supply node         (1 x n)
    :return pressure_loss_nodes_return: array containing the pressure loss at each return node         (1 x n)
    :return pressure_loss_system: pressure loss over the entire network
    :rtype pressure_loss_nodes_supply: ndarray
    :rtype pressure_loss_nodes_return: ndarray
    :rtype pressure_loss_system: float

    .. [Todini & Pilati, 1987] Todini & Pilati. "A gradient method for the analysis of pipe networks," in Computer
       Applications in Water Supply Volume 1 - Systems Analysis and Simulation, 1987.

    .. [Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
       Applied Thermal Engineering, 2016.
    """

    edge_node_df = thermal_network.edge_node_df.copy()
    pipe_diameter = thermal_network.pipe_properties[:]['D_int_m':'D_int_m'].values
    pipe_length = thermal_network.edge_df['pipe length'].values
    edge_mass_flow = thermal_network.edge_mass_flow_df.ix[t].values
    node_mass_flow = thermal_network.node_mass_flow_df.ix[t].values

    # get the temperatures at each supply and return edge
    temperature_supply_edges__k = calc_edge_temperatures(t_supply_node__k, edge_node_df)
    temperature_return_edges__k = calc_edge_temperatures(t_return_node__k, edge_node_df)

    # get the pressure drop through each edge
    pressure_loss_pipe_supply__pa = calc_pressure_loss_pipe(pipe_diameter, pipe_length, edge_mass_flow,
                                                            temperature_supply_edges__k, 2)
    pressure_loss_pipe_return__pa = calc_pressure_loss_pipe(pipe_diameter, pipe_length, edge_mass_flow,
                                                            temperature_return_edges__k, 2)

    pressure_loss_nodes_pa = calc_pressure_loss_substations(thermal_network, t_supply_node__k, t)
    # Add 20% to pressure losses for turns in the network
    # TODO: Improve this
    pressure_loss_pipe_supply__pa = pressure_loss_pipe_supply__pa * 1.2
    pressure_loss_pipe_return__pa = pressure_loss_pipe_return__pa * 1.2

    # TODO: here 70% pump efficiency assumed, better estimate according to massflows
    pressure_loss_pipe_supply_kW = pressure_loss_pipe_supply__pa * edge_mass_flow / P_WATER_KGPERM3 / 1000 / PUMP_ETA
    pressure_loss_pipe_return_kW = pressure_loss_pipe_return__pa * edge_mass_flow / P_WATER_KGPERM3 / 1000 / PUMP_ETA
    pressure_loss_nodes_kW = pressure_loss_nodes_pa * node_mass_flow / P_WATER_KGPERM3 / 1000 / PUMP_ETA

    pressure_loss_substations_pa = []
    pressure_loss_substations_kW = []
    # remove non buildings, match this to buildings_names list from Pa and kW values
    for building in thermal_network.building_names:
        for index, name in enumerate(thermal_network.all_nodes_df.Building):
            if name == building:
                # add value from this node-index to the list
                # TODO: Fix for ecocampus case, not all buildings in network

                pressure_loss_substations_pa.append(pressure_loss_nodes_pa[index])
                pressure_loss_substations_kW.append(pressure_loss_nodes_kW[index])

    # total pressure loss in the system
    # # pressure losses at the supply plant are assumed to be included in the pipe losses as done by Oppelt et al., 2016
    # pressure_loss_system = sum(np.nan_to_num(pressure_loss_pipe_supply)[0]) + sum(
    #     np.nan_to_num(pressure_loss_pipe_return)[0])
    pressure_loss_system__pa = calc_pressure_loss_system(pressure_loss_pipe_supply__pa, pressure_loss_pipe_return__pa,
                                                         pressure_loss_substations_pa)
    pressure_loss_total_kw = calc_pressure_loss_system(pressure_loss_pipe_supply_kW, pressure_loss_pipe_return_kW,
                                                       pressure_loss_substations_kW)

    pressure_loss_pipes_pa = pressure_loss_pipe_supply__pa + pressure_loss_pipe_return__pa
    pressure_loss_pipes_kW = pressure_loss_pipe_supply_kW + pressure_loss_pipe_return_kW

    # solve for the pressure at each node based on Eq. 1 in Todini & Pilati for no = 0 (no nodes with fixed head):
    # A12 * H + F(Q) = -A10 * H0 = 0
    # edge_node_transpose * pressure_nodes = - (pressure_loss_pipe) (Ax = b)
    # ToDo: does not apply for looped networks
    edge_node_transpose = np.transpose(edge_node_df.values)
    pressure_nodes_supply__pa = np.round(
        np.transpose(np.linalg.lstsq(edge_node_transpose, np.transpose(pressure_loss_pipe_supply__pa) * (-1))[0]),
        decimals=5)
    pressure_nodes_return__pa = np.round(
        np.transpose(np.linalg.lstsq(-edge_node_transpose, np.transpose(pressure_loss_pipe_return__pa) * (-1))[0]),
        decimals=5)
    return pressure_nodes_supply__pa, pressure_nodes_return__pa, pressure_loss_system__pa, \
           pressure_loss_total_kw, pressure_loss_pipes_kW[0], pressure_loss_substations_kW


def calc_pressure_loss_substations(thermal_network, supply_temperature, t):
    """
    This function calculates the pressure losses in substations assuming each substation to be modeled by a valve and HEX
    for each supplied heating or cooling load.
    :param node_mass_flow:
    :param thermal_network:
    :return:


    Pope, J. E. (1997). Rules of thumb for mechanical engineers : a manual of quick, accurate solutions to everyday
    mechanical engineering problems. Gulf Pub. Co.

    Behind the Walls: Valves in Building Systems. (n.d.). Retrieved May 10, 2018, from
    http://www.valvemagazine.com/magazine/sections/where-valves-are-used/4864-behind-the-walls-valves-in-building-systems.html?showall=&start=1
    """
    a_p = thermal_network.pressure_loss_coeff[0]
    b_p = thermal_network.pressure_loss_coeff[1]
    c_p = thermal_network.pressure_loss_coeff[2]
    d_p = thermal_network.pressure_loss_coeff[3]
    e_p = thermal_network.pressure_loss_coeff[4]

    consumer_building_names = thermal_network.all_nodes_df.loc[
        thermal_network.all_nodes_df['Type'] == 'CONSUMER', 'Building'].values
    plant_indexes = np.where(thermal_network.all_nodes_df['Type'] == 'PLANT')[0]
    all_buildings = thermal_network.all_nodes_df['Building'].values
    valve_losses = {}
    hex_losses = {}
    total_losses = {}
    if thermal_network.network_type == 'DH':
        cap_mass_flow = thermal_network.ch_value
    else:
        cap_mass_flow = thermal_network.cc_value
    for name in consumer_building_names:
        # building_ID = thermal_network.all_nodes_df[name]
        aggregated_valve = 0
        aggregated_hex = 0
        for type in cap_mass_flow.keys():
            # iterate through all heating/cooling types
            if t in cap_mass_flow[type].keys():
                if isinstance(cap_mass_flow[type][t], pd.DataFrame):
                    if name in cap_mass_flow[type][t].keys():
                        if any(cap_mass_flow[type][t][name] > 0):
                            node_flow = cap_mass_flow[type][t][name].values / HEAT_CAPACITY_OF_WATER_JPERKGK
                            ## calculate valve pressure loss
                            # find out diameter of building. This is assumed to be the same as the edge connecting to that building
                            # find assigned node of building
                            building_index = np.where(thermal_network.all_nodes_df.Building == name)[0][0]
                            building_node = thermal_network.all_nodes_df.index[building_index]
                            building_edge = thermal_network.edge_node_df.columns[
                                np.where(thermal_network.edge_node_df.ix[building_node] == 1)][0]
                            building_diameter = thermal_network.pipe_properties[:]['D_int_m':'D_int_m'][building_edge][0]
                            # calculate equivalent length for valve
                            valve_eq_length = building_diameter * 9  # Pope, J. E. (1997). Rules of thumb for mechanical engineers
                            aggregated_valve = aggregated_valve + calc_pressure_loss_pipe([building_diameter],
                                                                                          [valve_eq_length],
                                                                                          [node_flow],
                                                                                          [supply_temperature[
                                                                                               building_index]], 0)

                            if node_flow <= MAX_NODE_FLOW:
                                ## calculate HEX losses
                                mcp_sub = node_flow * HEAT_CAPACITY_OF_WATER_JPERKGK
                                if np.isclose(aggregated_hex, 0):
                                    aggregated_hex = a_p + b_p * mcp_sub ** c_p + d_p * np.log(
                                        mcp_sub) + e_p * mcp_sub * np.log(mcp_sub)
                                else:
                                    aggregated_hex = aggregated_hex + b_p * mcp_sub ** c_p + d_p * np.log(
                                        mcp_sub) + e_p * mcp_sub * np.log(mcp_sub)

                            else:
                                number_of_HEXs = int(ceil(node_flow / MAX_NODE_FLOW))
                                nodeflow_nom = node_flow / number_of_HEXs
                                for i in range(number_of_HEXs):
                                    ## calculate HEX losses
                                    mcp_sub = nodeflow_nom * HEAT_CAPACITY_OF_WATER_JPERKGK
                                    if np.isclose(aggregated_hex, 0):
                                        aggregated_hex = a_p + b_p * mcp_sub ** c_p + d_p * np.log(
                                            mcp_sub) + e_p * mcp_sub * np.log(mcp_sub)
                                    else:
                                        aggregated_hex = aggregated_hex + b_p * mcp_sub ** c_p + d_p * np.log(
                                            mcp_sub) + e_p * mcp_sub * np.log(mcp_sub)
        valve_losses[name] = aggregated_valve
        hex_losses[name] = aggregated_hex
        total_losses[name] = aggregated_valve + aggregated_hex

    # calculate plant pressure losses
    total_plant_losses = np.zeros(len(all_buildings))
    aggregated_valve = 0
    aggregated_hex = 0
    for index in plant_indexes:
        node_flow = thermal_network.node_mass_flow_df['NODE' + str(index)].abs().max()
        building_index = index
        building_node = thermal_network.all_nodes_df.index[building_index]
        building_edge = \
            thermal_network.edge_node_df.columns[np.where(thermal_network.edge_node_df.ix[building_node] == -1)][0]
        building_diameter = thermal_network.pipe_properties[:]['D_int_m':'D_int_m'][building_edge][0]
        # calculate equivalent length for valve
        valve_eq_length = building_diameter * 9  # Pope, J. E. (1997). Rules of thumb for mechanical engineers
        aggregated_valve = aggregated_valve + calc_pressure_loss_pipe([building_diameter], [valve_eq_length],
                                                                      [node_flow],
                                                                      [supply_temperature[building_index]], 0)

        if node_flow <= MAX_NODE_FLOW:
            ## calculate HEX losses
            mcp_sub = node_flow * HEAT_CAPACITY_OF_WATER_JPERKGK
            if aggregated_hex == 0:
                aggregated_hex = a_p + b_p * mcp_sub ** c_p + d_p * np.log(mcp_sub) + e_p * mcp_sub * np.log(mcp_sub)
            else:
                aggregated_hex = aggregated_hex + b_p * mcp_sub ** c_p + d_p * np.log(mcp_sub) + e_p * mcp_sub * np.log(
                    mcp_sub)

        else:
            number_of_HEXs = int(ceil(node_flow / MAX_NODE_FLOW))
            nodeflow_nom = node_flow / number_of_HEXs
            for i in range(number_of_HEXs):
                ## calculate HEX losses
                mcp_sub = nodeflow_nom * HEAT_CAPACITY_OF_WATER_JPERKGK
                if aggregated_hex == 0:
                    aggregated_hex = a_p + b_p * mcp_sub ** c_p + d_p * np.log(mcp_sub) + e_p * mcp_sub * np.log(
                        mcp_sub)
                else:
                    aggregated_hex = aggregated_hex + b_p * mcp_sub ** c_p + d_p * np.log(
                        mcp_sub) + e_p * mcp_sub * np.log(mcp_sub)
        total_plant_losses[index] = aggregated_hex + aggregated_valve

    # convert total_losses into a ndarray in the order or node numbering, with 0 values for NONE nodes
    total_losses_array = np.zeros(len(all_buildings))
    # add building losses
    for index, name in enumerate(thermal_network.all_nodes_df.Building):
        if name in total_losses.keys():  # this is a consumer building
            total_losses_array[index] = total_losses[str(name)]
    # add plant losses
    for index in plant_indexes:
        total_losses_array[index] = total_plant_losses[index]
    return total_losses_array


def change_to_edge_node_matrix_t(edge_mass_flow, edge_node_df):
    """
    The function changes the flow directions in edge_node_df to align with flow directions at each time-step, this way
    all the mass flows are positive.

    :param edge_mass_flow: Current mass flows on each edge
    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                         and indicating the direction of flow of each edge e at node n: if e points to n,
                         value is 1; if e leaves node n, -1; else, 0. E.g. a plant will only have exiting flows,
                         so only negative values

    :return edge_mass_flow:
    :return edge_node_df: Updated edge_node_df matrix set to match positive flow directions of edge_mass_flows
    """
    edge_mass_flow = np.round(edge_mass_flow, decimals=5)  # round to avoid very low near 0 mass flows
    while edge_mass_flow.min() < 0:
        for i in range(len(edge_mass_flow)):
            if edge_mass_flow[i] < 0:
                edge_mass_flow[i] = abs(edge_mass_flow[i])
                edge_node_df[edge_node_df.columns[i]] = -edge_node_df[edge_node_df.columns[i]]
    return edge_mass_flow, edge_node_df


def calc_pressure_loss_pipe(pipe_diameter_m, pipe_length_m, mass_flow_rate_kgs, t_edge__k, loop_type):
    """
    Calculates the pressure losses throughout a pipe based on the Darcy-Weisbach equation and the Swamee-Jain
    solution for the Darcy friction factor [Oppelt et al., 2016].

    :param pipe_diameter_m: vector containing the pipe diameter in m for each edge e in the network           (e x 1)
    :param pipe_length_m: vector containing the length in m of each edge e in the network                     (e x 1)
    :param mass_flow_rate_kgs: matrix containing the mass flow rate in each edge e at time t                  (t x e)
    :param t_edge__k: matrix containing the temperature of the water in each edge e at time t                 (t x e)
    :param loop_type: int indicating if function is called from loop calculation or not, or is derivate is necessary
                        (1 = derivative of Loop, 2 = branch)
    :type pipe_diameter_m: ndarray
    :type pipe_length_m: ndarray
    :type mass_flow_rate_kgs: ndarray
    :type t_edge__k: list
    :type loop_type: binary

    :return pressure_loss_edge: pressure loss through each edge e at each time t                            (t x e)
    :rtype pressure_loss_edge: ndarray

    ..[Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
    Applied Thermal Engineering, 2016.

    """
    mass_flow_rate_kgs = np.array(mass_flow_rate_kgs)
    pipe_length_m = np.array(pipe_length_m)
    pipe_diameter_m = np.array(pipe_diameter_m)
    reynolds = calc_reynolds(mass_flow_rate_kgs, t_edge__k, pipe_diameter_m)

    darcy = calc_darcy(pipe_diameter_m, reynolds, ROUGHNESS)

    if loop_type == 1:  # dp/dm parital derivative of edge pressure loss equation
        pressure_loss_edge_Pa = darcy * 16 * mass_flow_rate_kgs * pipe_length_m / (
                math.pi ** 2 * pipe_diameter_m ** 5 * P_WATER_KGPERM3)
    else:
        # calculate the pressure losses through a pipe using the Darcy-Weisbach equation
        pressure_loss_edge_Pa = darcy * 8 * mass_flow_rate_kgs ** 2 * pipe_length_m / (
                math.pi ** 2 * pipe_diameter_m ** 5 * P_WATER_KGPERM3)
    return pressure_loss_edge_Pa


def calc_pressure_loss_system(pressure_loss_pipe_supply, pressure_loss_pipe_return, pressure_loss_substation):
    pressure_loss_system = np.full(4, np.nan)
    pressure_loss_system[0] = sum(np.nan_to_num(pressure_loss_pipe_supply)[0])
    pressure_loss_system[1] = sum(np.nan_to_num(pressure_loss_pipe_return)[0])
    pressure_loss_system[2] = sum(np.nan_to_num(pressure_loss_substation))
    pressure_loss_system[3] = pressure_loss_system[0] + pressure_loss_system[1] + pressure_loss_system[2]
    return pressure_loss_system


def calc_darcy(pipe_diameter_m, reynolds, pipe_roughness_m):
    """
    Calculates the Darcy friction factor [Oppelt et al., 2016].

    :param pipe_diameter_m: vector containing the pipe diameter in m for each edge e in the network           (e x 1)
    :param reynolds: vector containing the reynolds number of flows in each edge in that timestep	      (e x 1)
    :param pipe roughness_m: float with pipe roughness
    :type pipe_diameter_m: ndarray
    :type reynolds: ndarray
    :type pipe_roughness_m: float

    :return darcy: calculated darcy friction factor for flow in each edge		(ex1)
    :rtype darcy: ndarray

    ..[Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
      Applied Thermal Engineering, 2016.

    .. Incropera, F. P., DeWitt, D. P., Bergman, T. L., & Lavine, A. S. (2007). Fundamentals of Heat and Mass Transfer.
       Fundamentals of Heat and Mass Transfer. https://doi.org/10.1016/j.applthermaleng.2011.03.022
    """

    darcy = np.zeros(reynolds.size)
    # necessary to make sure pipe_diameter is 1D vector as input formats can vary
    if hasattr(pipe_diameter_m[0], '__len__'):
        pipe_diameter_m = pipe_diameter_m[0]
    for rey in range(reynolds.size):
        if reynolds[rey] <= 1:
            darcy[rey] = 0
        elif reynolds[rey] <= 2300:
            # calculate the Darcy-Weisbach friction factor for laminar flow
            darcy[rey] = 64 / reynolds[rey]
        elif reynolds[rey] <= 5000:
            # calculate the Darcy-Weisbach friction factor for transient flow (for pipe roughness of e/D=0.0002,
            # @low reynolds numbers lines for smooth pipe nearl identical in Moody Diagram) so smooth pipe approximation used
            darcy[rey] = 0.316 * reynolds[rey] ** -0.25
        else:
            # calculate the Darcy-Weisbach friction factor using the Swamee-Jain equation, applicable for Reynolds= 5000 - 10E8; pipe_roughness=10E-6 - 0.05
            darcy[rey] = 1.325 * np.log(
                pipe_roughness_m / (3.7 * pipe_diameter_m[rey]) + 5.74 / reynolds[rey] ** 0.9) ** (-2)

    return darcy


def calc_reynolds(mass_flow_rate_kgs, temperature__k, pipe_diameter_m):
    """
    Calculates the reynolds number of the internal flow inside the pipes.

    :param pipe_diameter_m: vector containing the pipe diameter in m for each edge e in the network           (e x 1)
    :param mass_flow_rate_kgs: matrix containing the mass flow rate in each edge e at time t                    (t x e)
    :param temperature__k: matrix containing the temperature of the water in each edge e at time t             (t x e)
    :type pipe_diameter_m: ndarray
    :type mass_flow_rate_kgs: ndarray
    :type temperature__k: list
    """
    kinematic_viscosity_m2s = calc_kinematic_viscosity(temperature__k)  # m2/s

    reynolds = np.nan_to_num(
        4 * (abs(mass_flow_rate_kgs) / P_WATER_KGPERM3) / (math.pi * kinematic_viscosity_m2s * pipe_diameter_m))
    # necessary if statement to make sure ouput is an array type, as input formats of files can vary
    if hasattr(reynolds[0], '__len__'):
        reynolds = reynolds[0]
    return reynolds


def calc_prandtl(temperature__k):
    """
    Calculates the prandtl number of the internal flow inside the pipes.

    :param temperature__k: matrix containing the temperature of the water in each edge e at time t             (t x e)
    :type temperature__k: list
    """
    kinematic_viscosity_m2s = calc_kinematic_viscosity(temperature__k)  # m2/s
    thermal_conductivity = calc_thermal_conductivity(temperature__k)  # W/(m*K)

    return np.nan_to_num(
        kinematic_viscosity_m2s * P_WATER_KGPERM3 * HEAT_CAPACITY_OF_WATER_JPERKGK / thermal_conductivity)


def calc_kinematic_viscosity(temperature):
    """
    Calculates the kinematic viscosity of water as a function of temperature based on a simple fit from data from the
    engineering toolbox.

    :param temperature: in K
    :return: kinematic viscosity in m2/s
    """
    # check if list type, this can cause problems
    if isinstance(temperature, (list,)):
        temperature = np.array(temperature)
    return 2.652623e-8 * math.e ** (557.5447 * (temperature - 140) ** -1)


def calc_thermal_conductivity(temperature):
    """
    Calculates the thermal conductivity of water as a function of temperature based on a fit proposed in:

    :param temperature: in K
    :return: thermal conductivity in W/(m*K)

    ... Standard Reference Data for the Thermal Conductivity of Water
    Ramires, Nagasaka, et al.
    1994

    """

    return 0.6065 * (-1.48445 + 4.12292 * temperature / 298.15 - 1.63866 * (temperature / 298.15) ** 2)


def calc_max_edge_flowrate(thermal_network, set_diameter, start_t, stop_t, substation_systems, config,
                           use_multiprocessing=True):
    """
    Calculates the maximum flow rate in the network in order to assign the pipe diameter required at each edge. This is
    done by calculating the mass flow rate required at each substation to supply the calculated demand at the target
    supply temperature for each time step, finding the maximum for each node throughout the year and calculating the
    resulting necessary mass flow rate at each edge to satisfy this demand.

    :param ThermalNetwork thermal_network: contains information about the thermal network
    :param all_nodes_df: DataFrame containing all nodes and whether a node n is a consumer or plant node
                        (and if so, which building that node corresponds to), or neither.                   (2 x n)
    :param buildings_demands: demand of each building in the scenario
    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0. E.g. a plant will only have exiting flows,
                        so only negative values                                        (n x e)
    :param locator: an InputLocator instance set to the scenario to work on
    :param substations_hex_specs: DataFrame with substation heat exchanger specs at each building.
    :param t_target_supply_C: target supply temperature at each substation
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling
                         ('DC') network
    :param pipe_length: vector containing the length of each edge in the network
    :type all_nodes_df: DataFrame
    :type locator: InputLocator
    :type substations_hex_specs: DataFrame
    :type network_type: str
    :type pipe_length: array

    :return edge_mass_flow_df: mass flow rate at each edge throughout the year
    :return max_edge_mass_flow_df: maximum mass flow at each edge to be used for pipe sizing
    :rtype edge_mass_flow_df: DataFrame
    :rtype max_edge_mass_flow_df: DataFrame

    """

    region = config.region
    # create empty DataFrames to store results
    if config.thermal_network_optimization.use_representative_week_per_month:
        thermal_network.edge_mass_flow_df = pd.DataFrame(
            data=np.zeros((2016, len(thermal_network.edge_node_df.columns.values))),
            columns=thermal_network.edge_node_df.columns.values)  # stores values for 2016 timesteps

        thermal_network.node_mass_flow_df = pd.DataFrame(
            data=np.zeros((2016, len(thermal_network.edge_node_df.index))),
            columns=thermal_network.edge_node_df.index.values)  # stores values for 2016 timestep

        thermal_network.thermal_demand = pd.DataFrame(
            data=np.zeros((2016, len(thermal_network.building_names))),
            columns=thermal_network.building_names.values)  # stores values for 8760 timesteps

    else:
        thermal_network.edge_mass_flow_df = pd.DataFrame(
            data=np.zeros((HOURS_IN_YEAR, len(thermal_network.edge_node_df.columns.values))),
            columns=thermal_network.edge_node_df.columns.values)  # stores values for 8760 timesteps

        thermal_network.node_mass_flow_df = pd.DataFrame(
            data=np.zeros((HOURS_IN_YEAR, len(thermal_network.edge_node_df.index))),
            columns=thermal_network.edge_node_df.index.values)  # stores values for 8760 timesteps

        thermal_network.thermal_demand = pd.DataFrame(
            data=np.zeros((HOURS_IN_YEAR, len(thermal_network.building_names))),
            columns=thermal_network.building_names.values)  # stores values for 8760 timesteps

    loops, graph = find_loops(thermal_network.edge_node_df)

    if loops:
        print('Fundamental loops in network: ', loops)
        # initial guess of pipe diameter
        diameter_guess = initial_diameter_guess(thermal_network, set_diameter, substation_systems, config)
    else:
        # no iteration necessary
        # read in diameters from shp file
        diameter_guess = read_in_diameters_from_shapefile(thermal_network)

    print('start calculating mass flows in edges...')
    iterations = 0
    # t0 = time.clock()
    converged = False
    # Iterate over diameter of pipes since m = f(delta_p), delta_p = f(diameter) and diameter = f(m)
    while not converged:
        print('\n Diameter iteration number ', iterations)
        diameter_guess_old = diameter_guess

        # hourly_mass_flow_calculation
        t = range(start_t, stop_t)
        nhours = stop_t - start_t

        number_of_processes = config.get_number_of_processes()
        if number_of_processes > 1:
            print("Using %i CPU's" % number_of_processes)
            pool = multiprocessing.Pool(number_of_processes)
            mass_flows = pool.map(hourly_mass_flow_calculation_wrapper,
                                  izip(t, repeat(diameter_guess, nhours), repeat(thermal_network, nhours)))
            pool.close()
            pool.join()
        else:
            mass_flows = map(hourly_mass_flow_calculation, t,
                             repeat(diameter_guess, nhours), repeat(thermal_network, nhours))

        # write mass flows to the dataframes
        thermal_network.edge_mass_flow_df.iloc[range(start_t, stop_t)] = [mfe[0] for mfe in mass_flows]
        thermal_network.node_mass_flow_df.iloc[range(start_t, stop_t)] = [mfe[1] for mfe in mass_flows]
        thermal_network.thermal_demand.iloc[range(start_t, stop_t)] = [mfe[2] for mfe in mass_flows]

        # update diameter guess for iteration
        pipe_properties_df = assign_pipes_to_edges(thermal_network, set_diameter)
        diameter_guess = pipe_properties_df[:]['D_int_m':'D_int_m'].values[0]

        # exit condition for diameter iteration while statement
        if not loops:  # no loops, so no iteration necessary
            converged = True
            thermal_network.no_convergence_flag = False
        elif iterations == thermal_network.config.thermal_network.diameter_iteration_limit:  # Too many iterations
            converged = True
            print(
                '\n No convergence of pipe diameters in loop calculation, possibly due to large amounts of low mass flows. '
                '\n Please retry with alternate network design.')
            thermal_network.no_convergence_flag = True
        elif (abs(diameter_guess_old - diameter_guess) > 0.005).any():
            # 0.005 is the smallest diameter change of the catalogue, so at least one diameter value has changed
            converged = False
            # we are half way through the total amount of iterations without convergence
            # the flag below triggers a reduction in the acceptable minimum mass flow to (hopefully) allow for convergence
            if iterations == int(
                    thermal_network.config.thermal_network.diameter_iteration_limit / 2):  # int() cast necessary because iterations variable takes int values
                thermal_network.no_convergence_flag = True

            # reset all minimum mass flow calculation values
            thermal_network.delta_cap_mass_flow = {}
            thermal_network.nodes = {}
            thermal_network.cc_old = {}
            thermal_network.ch_old = {}
            thermal_network.cc_value = {}
            thermal_network.ch_value = {}

        else:  # no change of diameters
            converged = True
            thermal_network.no_convergence_flag = False

        iterations += 1

    # output csv files with node mass flows
    if config.thermal_network_optimization.use_representative_week_per_month:
        # need to repeat lines to make sure our outputs have 8760 timesteps. Otherwise plots
        # and network optimization will fail as they expect 8760 timesteps.
        node_mass_flow_for_csv = pd.DataFrame(thermal_network.node_mass_flow_df)
        thermal_demand_for_csv = pd.DataFrame(thermal_network.thermal_demand)
        # we need to extrapolate 8760 datapoints from 2016 points from our representative weeks.
        # To do this, the initial dataset is repeated 4 times, the remaining values are filled with the average values of all above.
        node_mass_flow_for_csv = pd.concat([node_mass_flow_for_csv] * 4, ignore_index=True)
        thermal_demand_for_csv = pd.concat([thermal_demand_for_csv] * 4, ignore_index=True)
        while len(node_mass_flow_for_csv.index) < HOURS_IN_YEAR:
            node_mass_flow_for_csv = node_mass_flow_for_csv.append(node_mass_flow_for_csv.mean(), ignore_index=True)
        while len(thermal_demand_for_csv.index) < HOURS_IN_YEAR:
            thermal_demand_for_csv = thermal_demand_for_csv.append(thermal_demand_for_csv.mean(), ignore_index=True)

        node_mass_flow_for_csv.to_csv(
            thermal_network.locator.get_node_mass_flow_csv_file(thermal_network.network_type,
                                                                thermal_network.network_name))
        # output csv files with aggregated demand
        thermal_demand_for_csv.to_csv(
            thermal_network.locator.get_thermal_demand_csv_file(thermal_network.network_type,
                                                                thermal_network.network_name),
            columns=thermal_network.building_names)

    else:
        thermal_network.node_mass_flow_df.to_csv(
            thermal_network.locator.get_node_mass_flow_csv_file(thermal_network.network_type,
                                                                thermal_network.network_name))

        # output csv files with aggregated demand
        thermal_network.thermal_demand.to_csv(
            thermal_network.locator.get_thermal_demand_csv_file(thermal_network.network_type,
                                                                thermal_network.network_name),
            columns=thermal_network.building_names)

    return thermal_network.edge_mass_flow_df


def load_max_edge_flowrate_from_previous_run(thermal_network):
    """Bypass the calculation of calc_max_edge_flowrate and use the results form the previous run"""
    edge_mass_flow_df = pd.read_csv(
        thermal_network.locator.get_edge_mass_flow_csv_file(thermal_network.network_type, thermal_network.network_name))
    del edge_mass_flow_df['Unnamed: 0']
    # max_edge_mass_flow_df = pd.DataFrame(data=[(edge_mass_flow_df.abs()).max(axis=0)],
    #                                     columns=thermal_network.edge_node_df.columns)
    return edge_mass_flow_df


def load_node_flowrate_from_previous_run(thermal_network):
    """Bypass the calculation of calc_max_edge_flowrate and use the results form the previous run"""
    node_mass_flow_df = pd.read_csv(
        thermal_network.locator.get_node_mass_flow_csv_file(thermal_network.network_type, thermal_network.network_name))
    del node_mass_flow_df['Unnamed: 0']
    # max_edge_mass_flow_df = pd.DataFrame(data=[(edge_mass_flow_df.abs()).max(axis=0)],
    #                                     columns=thermal_network.edge_node_df.columns)
    return node_mass_flow_df


def read_in_diameters_from_shapefile(thermal_network):
    network_edges = gpd.read_file(
        thermal_network.locator.get_network_layout_edges_shapefile(thermal_network.network_type,
                                                                   thermal_network.network_name))
    diameter_guess = network_edges['Pipe_DN']
    return diameter_guess


def hourly_mass_flow_calculation_wrapper(args):
    """A wrapper around hourly_mass_flow_calculation because multiprocessing.Pool.map only allows one argument"""
    return hourly_mass_flow_calculation(*args)


def hourly_mass_flow_calculation(t, diameter_guess, thermal_network):
    """
    This function calculates the edge mass flows and node mass flows of each hour of the year.

    :param ThermalNetwork thermal_network: object holding all the information about the thermal network
    :param t: timestep
    :param t_target_supply_C: target temperature of nodes
    :param network_type: 'DH' or 'DC'
    :param locator: InputLocator
    :param buildings_demands: DataFrame of Building demands
    :param substations_hex_specs: DataFrame with substation heat exchanger specs at each building.
    :param all_nodes_df: DataFrame containing all nodes and whether a node n is a consumer or plant node
                        (and if so, which building that node corresponds to), or neither.                   (2 x n)
    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0. E.g. a plant will only have exiting flows,
                        so only negative values                                       (n x e)
    :param edge_mass_flow_df: Storage for edge mass flows of all hours of the year
    :param diameter_guess: Pipe diameter values
    :param pipe_length:  Length of each edge

    :param node_mass_flow_df:  Storage for node mass flows of all hours of the year
    :return edge_mass_flow_df: Storage for edge mass flows of all hours of the year
    :return node_mass_flow_df: Storage for node mass flows of all hours of the year
    """

    print('calculating mass flows in edges... time step', t)

    if thermal_network.network_type == 'DH':
        # set to the highest value in the network and assume no loss within the network
        T_substation_supply_K = np.array(
            [float(thermal_network.t_target_supply_C.ix[t].max()) + 273.15] * len(
                thermal_network.buildings_demands.keys())).reshape(
            1, len(thermal_network.buildings_demands.keys()))  # in [K]
    else:
        # set to the highest value in the network and assume no loss within the network
        T_substation_supply_K = np.array(
            [float(thermal_network.t_target_supply_C.ix[t].min()) + 273.15] * len(
                thermal_network.buildings_demands.keys())).reshape(
            1, len(thermal_network.buildings_demands.keys()))  # in [K]

    T_substation_supply_K = pd.DataFrame(T_substation_supply_K,
                                         columns=thermal_network.buildings_demands.keys(), index=['T_supply'])

    min_edge_flow_flag = False
    if not t in thermal_network.delta_cap_mass_flow.keys():
        thermal_network.delta_cap_mass_flow[t] = 0
    iteration = 0
    reset_min_mass_flow_variables(thermal_network, t)
    while min_edge_flow_flag == False:  # too low edge mass flows
        reset_min_mass_flow_variables(thermal_network, t)  # reset storage variables
        # calculate substation flow rates and return temperatures
        if thermal_network.network_type == 'DH' or (
                thermal_network.network_type == 'DC' and math.isnan(T_substation_supply_K.values[0][0]) == False):
            _, mdot_all, thermal_demand_for_t = substation_matrix.substation_return_model_main(thermal_network,
                                                                                               T_substation_supply_K, t,
                                                                                               thermal_network.building_names)
        else:
            mdot_all = pd.DataFrame(data=np.zeros(len(thermal_network.buildings_demands.keys())),
                                    index=thermal_network.buildings_demands.keys()).T
            for key in thermal_network.config.thermal_network.substation_heating_systems:
                key = 'hs_' + key
                thermal_network.ch_value[key][t] = 0
            for key in thermal_network.config.thermal_network.substation_cooling_systems:
                key = 'cs_' + key
                thermal_network.cc_value[key][t] = 0
            thermal_demand_for_t = np.zeros(len(thermal_network.building_names))
        # write consumer substation required flow rate to nodes
        required_flow_rate_df = write_substation_values_to_nodes_df(thermal_network.all_nodes_df, mdot_all)
        # (1 x n)

        # initial guess temperature
        T_edge_K_initial = np.array([T_substation_supply_K.values[0][0]] * thermal_network.edge_node_df.shape[1])

        if required_flow_rate_df.abs().max(axis=1)[0] > 0:  # non 0 demand
            # solve mass flow rates on edges
            mass_flow_edges_for_t = calc_mass_flow_edges(thermal_network.edge_node_df.copy(), required_flow_rate_df,
                                                         thermal_network.all_nodes_df, diameter_guess,
                                                         thermal_network.edge_df['pipe length'], T_edge_K_initial)
        else:
            mass_flow_edges_for_t = np.zeros(len(thermal_network.edge_node_df.columns))

        mass_flow_nodes_for_t = required_flow_rate_df.values[0]

        iteration, \
        min_edge_flow_flag = edge_mass_flow_iteration(thermal_network,
                                                      mass_flow_edges_for_t, iteration, t)
    thermal_demand_for_t = thermal_demand_for_t.reshape((len(thermal_network.building_names),))
    return mass_flow_edges_for_t, mass_flow_nodes_for_t, thermal_demand_for_t


def edge_mass_flow_iteration(thermal_network, edge_mass_flow_df, min_iteration, t):
    """

    :param network_type: string with network type, DH or DC
    :param edge_mass_flow_df: edge mass flows                       (1 x e)
    :param min_iteration: iteration counter
    :param cc_value_sh: capacity mass flow for space heating        (1 x e)
    :param ch_value: capacity mass flow for cooling                 (1 x e)
    :param cc_value_dhw: capacity mass flow for warm water          (1 x e)

    :return:
    """
    if thermal_network.no_convergence_flag == True:
        pipe_min_mass_flow = thermal_network.config.thermal_network.minimum_edge_mass_flow / 2  # there are problems with convergence so reduce the minium edge mass flow
    else:
        pipe_min_mass_flow = thermal_network.config.thermal_network.minimum_edge_mass_flow  # minimum acceptable mass flow defined in our constants file
    if isinstance(edge_mass_flow_df, pd.DataFrame):  # make sure we have a pd Dataframe
        test_edge_flow = edge_mass_flow_df
    else:
        test_edge_flow = pd.DataFrame(edge_mass_flow_df)
    test_edge_flow = test_edge_flow.abs()
    test_edge_flow[
        np.isclose(test_edge_flow,
                   0)] = np.nan  # remove zero values as we are only interested in edges which have mass flows
    if np.isnan(test_edge_flow).values.all():
        min_edge_flow_flag = True  # no mass flows
    elif (
            test_edge_flow - pipe_min_mass_flow < -pipe_min_mass_flow / 2).values.any():  # some edges have too low mass flows, 0.01 is tolerance
        if min_iteration < int(
                thermal_network.config.thermal_network.minimum_mass_flow_iteration_limit / 5):  # identify buildings connected to edges with low mass flows, but only within the first iteration steps
            # read in all nodes file
            node_type = \
                pd.read_csv(thermal_network.locator.get_network_node_types_csv_file(thermal_network.network_type,
                                                                                    thermal_network.network_name))[
                    'Building']
            # identify which edges
            edges = np.where((test_edge_flow - pipe_min_mass_flow < -pipe_min_mass_flow / 2).values)[1]
            if len(edges) < len(
                    thermal_network.building_names) / 2:  # time intensive calculation. Only worth it if only isolated edges have low mass flows
                # identify which nodes, pass these on
                for i in edges:
                    pipe_name = str(thermal_network.edge_node_df.columns.values[i])
                    node = np.where(thermal_network.edge_node_df[pipe_name] == 1)[0][0]
                    # check if node is a building
                    # if not, identify closest  building
                    steps = 0
                    while (not any(node_type[node] in s for s in thermal_network.building_names)) and steps < 5:
                        # our node is not a bulding so we find an edge connected to our node
                        node_name = str(thermal_network.edge_node_df.index.values[node])
                        if len(np.where(thermal_network.edge_node_df.ix[node_name] == -1)[
                                   0]) > 1:  # we have more than one flow and all flows are incoming! Chose one randomly
                            new_edge = random.choice(np.where(thermal_network.edge_node_df.ix[node_name] == -1)[0])
                        else:
                            if np.where(thermal_network.edge_node_df.ix[node_name] == -1)[0]:
                                new_edge = np.where(thermal_network.edge_node_df.ix[node_name] == -1)[0][0]
                            else:  # our node is at a dead end
                                min_iteration = 5  # exit for loop
                                break
                        pipe_name = str(thermal_network.edge_node_df.columns.values[new_edge])
                        if len(np.where(thermal_network.edge_node_df[pipe_name] == 1)[
                                   0]) > 1:  # this shouldn't happen. we have more than one node that this edge flows to
                            node = random.choice(np.where(thermal_network.edge_node_df[pipe_name] == 1)[0])
                        else:
                            node = np.where(thermal_network.edge_node_df[pipe_name] == 1)[0][0]
                        steps = steps + 1  # we have taken one step away from the edge we want to increase
                    node = node_type[node]
                    thermal_network.nodes[t].append(node)
            else:  # more than 5 iterations completed - just increase all building demands
                thermal_network.nodes[t] = thermal_network.building_names
        else:  # many edges with low mass flows, increase all building demands
            thermal_network.nodes[t] = thermal_network.building_names

        thermal_network.delta_cap_mass_flow[t] = abs(np.nanmin(
            (test_edge_flow.abs() - pipe_min_mass_flow).values))  # deviation from minimum mass flow
        min_edge_flow_flag = False  # need to iterate
        if thermal_network.network_type == 'DH':
            for key in thermal_network.config.thermal_network.substation_heating_systems:
                key = 'hs_' + key
                thermal_network.ch_old[key][t] = thermal_network.ch_value[key][t]
        else:
            for key in thermal_network.config.thermal_network.substation_cooling_systems:
                key = 'cs_' + key
                thermal_network.cc_old[key][t] = thermal_network.cc_value[key][t]
        min_iteration = min_iteration + 1
    else:  # all edge mass flows ok
        min_edge_flow_flag = True

    # exit condition
    if min_iteration > thermal_network.config.thermal_network.minimum_mass_flow_iteration_limit:
        print('Stopped minimum edge mass flow iterations at: ', min_iteration)
        min_edge_flow_flag = True
    return min_iteration, min_edge_flow_flag


def initial_diameter_guess(thermal_network, set_diameter, substation_systems, config):
    """
    This function calculates an initial guess for the pipe diameter in looped networks based on the time steps with the
    50 highest demands of the year. These pipe diameters are iterated until they converge, and this result is passed as
    an initial guess for the iteration over all time steps in an attempt to reduce total runtime.

    :param ThermalNetwork thermal_network: object containing all the data of the thermal network.
    :param all_nodes_df: DataFrame containing all nodes and whether a node n is a consumer or plant node
                        (and if so, which building that node corresponds to), or neither.                   (2 x n)
    :param buildings_demands: demand of each building in the scenario
    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0. E.g. a plant will only have exiting flows,
                        so only negative values
    :param locator: an InputLocator instance set to the scenario to work on
    :param substations_hex_specs: DataFrame with substation heat exchanger specs at each building.
    :param t_target_supply: target supply temperature at each substation
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling
                         ('DC') network
    :param network_name: string with name of network
    :param edge_df: list of edges and their corresponding lengths and start and end nodes
    :param set_diameter: boolean if diameter needs to be set
    :type all_nodes_df: DataFrame
    :type buildings_demands: dict
    :type edge_node_df: DataFrame
    :type locator: InputLocator
    :type substations_hex_specs: DataFrame
    :type t_target_supply: list
    :type network_type: str
    :type network_name: str
    :type edge_df: DataFrame
    :type set_diameter: bool

    :return pipe_properties_df[:]['D_int_m':'D_int_m'].values: initial guess pipe diameters for all edges
    :rtype pipe_properties_df[:]['D_int_m':'D_int_m'].values: array
    """

    # Identify time steps of highest 50 demands
    region = config.region
    if thermal_network.network_type == 'DH':
        if config.thermal_network_optimization.use_representative_week_per_month:
            heating_sum = np.zeros(2016)
        else:
            heating_sum = np.zeros(HOURS_IN_YEAR)
        for building in thermal_network.buildings_demands.keys():
            for system in substation_systems['heating']:
                if system == 'ww':
                    heating_sum = heating_sum + thermal_network.buildings_demands[building].Qww_sys_kWh
                else:
                    heating_sum = heating_sum + thermal_network.buildings_demands[building][
                        'Qhs_sys_' + system + '_kWh']
        timesteps_top_demand = np.argsort(heating_sum)[-50:]  # identifies 50 time steps with largest demand
    else:
        if config.thermal_network_optimization.use_representative_week_per_month:
            cooling_sum = np.zeros(2016)
        else:
            cooling_sum = np.zeros(HOURS_IN_YEAR)
        for building in thermal_network.buildings_demands.keys():  # sum up cooling demands of all buildings to create (1xt) array
            for system in substation_systems['cooling']:
                if system == 'data':
                    cooling_sum = cooling_sum + abs(thermal_network.buildings_demands[building].Qcdata_sys_kWh)
                elif system == 're':
                    cooling_sum = cooling_sum + abs(thermal_network.buildings_demands[building].Qcre_sys_kWh)
                else:
                    cooling_sum = cooling_sum + abs(
                        thermal_network.buildings_demands[building]['Qcs_sys_' + system + '_kWh'])
        timesteps_top_demand = np.argsort(cooling_sum)[-50:]  # identifies 50 time steps with largest demand

    # initialize reduced copy of target temperatures
    t_target_supply_reduced_C = pd.DataFrame(thermal_network.t_target_supply_C)
    # Cut out relevant parts of data matching top 50 time steps
    t_target_supply_reduced_C = t_target_supply_reduced_C.iloc[timesteps_top_demand].sort_index()
    # re-index dataframe
    t_target_supply_reduced_C = t_target_supply_reduced_C.reset_index(drop=True)

    # initialize reduced copy of building demands
    buildings_demands_reduced = dict(thermal_network.buildings_demands)
    # Cut out relevant parts of data matching top 50 time steps
    for building in thermal_network.buildings_demands.keys():
        buildings_demands_reduced[building] = buildings_demands_reduced[building].iloc[
            timesteps_top_demand].sort_index()
        buildings_demands_reduced[building] = buildings_demands_reduced[building].reset_index(drop=True)

    # setup other dictionary entries of top 50 timesteps only
    thermal_network_reduced = thermal_network.clone()
    thermal_network_reduced.buildings_demands = buildings_demands_reduced
    thermal_network_reduced.network_type = thermal_network.network_type
    thermal_network_reduced.substations_HEX_specs = thermal_network.substations_HEX_specs

    # initialize mass flows to calculate maximum edge mass flow
    thermal_network_reduced.edge_mass_flow_df = pd.DataFrame(
        data=np.zeros((REDUCED_TIME_STEPS, len(thermal_network.edge_node_df.columns.values))),
        columns=thermal_network.edge_node_df.columns.values)

    thermal_network_reduced.node_mass_flow_df = pd.DataFrame(
        data=np.zeros((REDUCED_TIME_STEPS, len(thermal_network.edge_node_df.index))),
        columns=thermal_network.edge_node_df.index.values)  # input parameters for validation

    print('start calculating mass flows in edges for initial guess...')
    # initial guess of pipe diameter and edge temperatures
    diameter_guess = np.array(
        [0.05] * thermal_network.edge_node_df.shape[1])
    # large enough for most applications
    # larger causes more iterations, smaller can cause high pressure losses in some edges

    # initialize diameter guess
    diameter_guess_old = np.array([0] * thermal_network.edge_node_df.shape[1])

    iterations = 0
    # t0 = time.clock()
    while (abs(
            diameter_guess_old - diameter_guess) > 0.005).any():
        # 0.005 is the smallest diameter change of the catalogue
        print('\n Initial Diameter iteration number ', iterations)
        diameter_guess_old = diameter_guess
        for t in range(REDUCED_TIME_STEPS):
            min_edge_flow_flag = False
            iteration = 0
            if not t in thermal_network_reduced.delta_cap_mass_flow.keys():
                thermal_network_reduced.delta_cap_mass_flow[t] = 0
            reset_min_mass_flow_variables(thermal_network_reduced, t)
            print('\n calculating mass flows in edges... time step', t)
            while not min_edge_flow_flag:  # too low edge mass flows
                reset_min_mass_flow_variables(thermal_network, t)  # reset storage variables
                if thermal_network.network_type == 'DH':
                    # set to the highest value in the network and assume no loss within the network
                    t_substation_supply_K = np.array(
                        [float(t_target_supply_reduced_C.ix[t].max()) + 273.15] * len(
                            thermal_network_reduced.building_names)).reshape(
                        1, len(thermal_network_reduced.building_names))  # in [K]
                else:
                    # set to the lowest value in the network and assume no loss within the network
                    t_substation_supply_K = np.array(
                        [float(t_target_supply_reduced_C.ix[t].min()) + 273.15] * len(
                            thermal_network_reduced.building_names)).reshape(
                        1, len(thermal_network_reduced.building_names))  # in [K]

                t_substation_supply_K = pd.DataFrame(t_substation_supply_K,
                                                     columns=thermal_network_reduced.building_names,
                                                     index=['T_supply'])

                # calculate substation flow rates and return temperatures
                if thermal_network_reduced.network_type == 'DH' or (
                        thermal_network_reduced.network_type == 'DC' and math.isnan(
                    t_substation_supply_K.values[0][0]) == False):
                    _, mdot_all, _ = substation_matrix.substation_return_model_main(thermal_network_reduced,
                                                                                    t_substation_supply_K, t,
                                                                                    thermal_network_reduced.building_names)
                    # t_flag = True: same temperature for all nodes
                else:
                    mdot_all = pd.DataFrame(data=np.zeros(len(thermal_network_reduced.buildings_demands.keys())),
                                            index=thermal_network_reduced.buildings_demands.keys()).T

                # write consumer substation required flow rate to nodes
                required_flow_rate_df = write_substation_values_to_nodes_df(thermal_network_reduced.all_nodes_df,
                                                                            mdot_all)
                # (1 x n)

                # initialize edge temperatures

                T_edge_initial_K = np.array(
                    [t_substation_supply_K.values[0][0]] * thermal_network_reduced.edge_node_df.shape[1])

                if required_flow_rate_df.abs().max(axis=1)[0] > 0:  # non 0 demand
                    # solve mass flow rates on edges
                    thermal_network_reduced.edge_mass_flow_df[:][t:t + 1] = [
                        calc_mass_flow_edges(thermal_network_reduced.edge_node_df.copy(), required_flow_rate_df,
                                             thermal_network_reduced.all_nodes_df,
                                             diameter_guess, thermal_network_reduced.edge_df['pipe length'].values,
                                             T_edge_initial_K)]
                    thermal_network_reduced.node_mass_flow_df[:][t:t + 1] = required_flow_rate_df.values

                iteration, \
                min_edge_flow_flag = edge_mass_flow_iteration(thermal_network_reduced,
                                                              thermal_network_reduced.edge_mass_flow_df[:][t:t + 1],
                                                              iteration, t)

        # assign pipe id/od according to maximum edge mass flow
        pipe_properties_df = assign_pipes_to_edges(thermal_network_reduced, set_diameter)
        # update diameter guess
        diameter_guess = pipe_properties_df[:]['D_int_m':'D_int_m'].values[0]
        iterations += 1

        if iterations > MAX_INITIAL_DIAMETER_ITERATIONS:
            print('No convergence of initial diameter guess after ', MAX_INITIAL_DIAMETER_ITERATIONS,
                  ' iterations. Continuing with main calculation.')
            diameter_guess_old = diameter_guess  # break from loop

    # return converged diameter based on top 50 demand time steps
    return pipe_properties_df[:]['D_int_m':'D_int_m'].values[0]


def calc_edge_temperatures(temperature_node, edge_node):
    """
    Calculates the temperature at each edge assuming the average temperature in the edge is equal to the average of the
    temperatures at its start and end node as done, for example, by Wang et al. (2016), that is::

        T_edge = (T_node_1 + T_node_2)/2

    :param temperature_node: array containing the temperature in each node n                                (1 x n)
    :param edge_node: matrix consisting of n rows (number of nodes) and e columns (number of edges) and
                      indicating the direction of flow of each edge e at node n: if e points to n, value
                      is 1; if e leaves node n, -1; else, 0.                                                (n x e)

    :return temperature_edge: array containing the temperature in each edge e                               (1 x n)

    ..[Wang et al., 2016] Wang et al. "A method for the steady-state thermal simulation of district heating systems and
    model parameters calibration," in Energy Conversion and Management Vol. 120, 2016, pp. 294-305.
    """

    # necessary to avoid nan propagation in edge temperature vector.
    # E.g. if node 1 = 300 K, node 2 = nan: T_edge = 150K -> nan.
    # solution is to replace nan with the mean temperature of all nodes
    temperature_node_mean = np.nanmean(temperature_node)
    temperature_node[np.isnan(temperature_node)] = temperature_node_mean

    # in order to calculate the edge temperatures, node temperature values of 'nan' were not acceptable
    # so these were converted to 0 and then converted back to 'nan'
    temperature_edge = np.dot(np.nan_to_num(temperature_node), abs(edge_node) / 2)
    if (
            temperature_edge < 273.15).any():  # this can happen if we have 0 mass flow, or if we fail to meet cooling demands
        temperature_edge[temperature_edge < 273.15] = 273.15
    # todo: could be updated with more accurate exponential temperature profile of edges for mean pipe temperature,
    # or mean value of that function to avoid spacial component
    return temperature_edge


# ===========================
# Thermal calculation
# ===========================


def solve_network_temperatures(thermal_network, t):
    """
    This function calculates the node temperatures at time-step t accounting for heat losses throughout the network.
    There is one iteration to determine weather the substation supply temperature and the substation mass flow are
    cohesive. It is done as follow: The substation supply temperatures (T_substation_supply) are calculated based on the
    nominal edge flow rate (see `calc_max_edge_flowrate`), and then the substation mass flow requirements
    (mass_flow_substation_nodes_df) and pipe mass flows (edge_mass_flow_df_2) are updated accordingly. Following, the
    substation supply temperatures(T_substation_supply_2) are recalcuated with the updated pipe mass flow.

    The iteration continues until the substation supply temperatures converged.

    Lastly, the plant heat requirements are calculated base on the plant supply/return temperatures and flow rates.

    :param locator: an InputLocator instance set to the scenario to work on
    :param t_ground: vector with ground temperatures in K
    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0. E.g. a plant will only have exiting flows,
                        so only negative values                                          (n x e)
    :param all_nodes_df: DataFrame containing all nodes and whether a node n is a consumer or plant node
                        (and if so, which building that node corresponds to), or neither.                   (2 x n)
    :param edge_mass_flow_df: mass flow rate at each edge throughout the year
    :param t_target_supply_df: target supply temperature at each substation
    :param buildings_demands: demand of each building in the scenario
    :param substations_hex_specs: DataFrame with substation heat exchanger specs at each building.
    :param t: current time step
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling
                        ('DC') network
    :param edge_df: list of edges and their corresponding lengths and start and end nodes
    :param pipe_properties_df: DataFrame containing the pipe properties for each edge in the network

    :param ThermalNetwork thermal_network: A container for all the thermal network data

    :type locator: InputLocator
    :type edge_node_df: DataFrame
    :type all_nodes_df: DataFrame
    :type edge_mass_flow_df: DataFrame
    :type locator: InputLocator
    :type substations_hex_specs: DataFrame
    :type network_type: str
    :type t_target_supply_df: DataFrame
    :type edge_df: DataFrame
    :type pipe_properties_df: DataFrame

    :returns T_supply_nodes: list of supply line node temperatures (nx1)
    :rtype T_supply_nodes: list of arrays
    :returns T_return_nodes: list of return line node temperatures (nx1)
    :rtype T_return_nodes: list of arrays
    :returns plant_heat_requirement: list of plant heat requirement
    :rtype plant_heat_requirement: list of arrays

    """
    # initialize
    if not t in thermal_network.delta_cap_mass_flow.keys():
        thermal_network.delta_cap_mass_flow[t] = 0
    if np.absolute(thermal_network.edge_mass_flow_df.ix[t].values).sum() != 0:
        edge_mass_flow_df, \
        edge_node_df = change_to_edge_node_matrix_t(thermal_network.edge_mass_flow_df.ix[t].values,
                                                    thermal_network.edge_node_df.copy())

        # initialize target temperatures in Kelvin as initial value for K_value calculation
        initial_guess_temp = np.asarray(thermal_network.t_target_supply_df.loc[t] + 273.15, order='C')
        t_edge__k = calc_edge_temperatures(initial_guess_temp, edge_node_df.copy())

        # initialization of K_value
        k = calc_aggregated_heat_conduction_coefficient(edge_mass_flow_df,
                                                        thermal_network.locator, thermal_network.edge_df,
                                                        thermal_network.pipe_properties, t_edge__k,
                                                        thermal_network.network_type,
                                                        thermal_network.config.region)  # [kW/K]

        ## calculate node temperatures on the supply network accounting losses in the network.
        t_supply_nodes__k, \
        plant_node, q_loss_edges_kw = calc_supply_temperatures(thermal_network.T_ground_K[t],
                                                               edge_node_df.copy(),
                                                               edge_mass_flow_df, k,
                                                               thermal_network.t_target_supply_df.loc[t],
                                                               thermal_network.network_type,
                                                               thermal_network.all_nodes_df, thermal_network)

        # write supply temperatures to substation nodes
        t_substation_supply__k = write_nodes_values_to_substations(t_supply_nodes__k, thermal_network.all_nodes_df)

        ## iterations to find out the corresponding node supply temperature and substation mass flow
        flag = 0
        iteration = 0
        min_edge_flow_flag = False
        min_iteration = 0
        reset_min_mass_flow_variables(thermal_network, t)
        while flag == 0:
            # calculate substation return temperatures according to supply temperatures
            while min_edge_flow_flag == False:
                reset_min_mass_flow_variables(thermal_network, t)  # reset storage variables
                consumer_building_names = thermal_network.all_nodes_df.loc[
                    thermal_network.all_nodes_df['Type'] == 'CONSUMER', 'Building'].values
                _, mdot_all_kgs, _ = substation_matrix.substation_return_model_main(thermal_network,
                                                                                    t_substation_supply__k, t,
                                                                                    consumer_building_names)

                if mdot_all_kgs.values.max() == np.nan:
                    print('Error in edge mass flow! Check edge_mass_flow_df')

                # write consumer substation return T and required flow rate to nodes
                mass_flow_substations_nodes_df = write_substation_values_to_nodes_df(thermal_network.all_nodes_df,
                                                                                     mdot_all_kgs)

                # solve for the required mass flow rate on each pipe
                edge_mass_flow_df_2_kgs = calc_mass_flow_edges(edge_node_df.copy(),
                                                               mass_flow_substations_nodes_df,
                                                               thermal_network.all_nodes_df,
                                                               thermal_network.pipe_properties[:][
                                                               'D_int_m':'D_int_m'].values[0],
                                                               thermal_network.edge_df['pipe length'], t_edge__k)

                # make sure all mass flows are positive and edge node matrix is updated
                edge_mass_flow_df_2_kgs, \
                edge_node_df = change_to_edge_node_matrix_t(edge_mass_flow_df_2_kgs,
                                                            edge_node_df.copy())
                min_iteration, \
                min_edge_flow_flag = edge_mass_flow_iteration(thermal_network,
                                                              edge_mass_flow_df_2_kgs, min_iteration, t)

                # calculate updated pipe aggregated heat conduction coefficient with new mass flows
                k = calc_aggregated_heat_conduction_coefficient(edge_mass_flow_df_2_kgs, thermal_network.locator,
                                                                thermal_network.edge_df,
                                                                thermal_network.pipe_properties, t_edge__k,
                                                                thermal_network.network_type,
                                                                thermal_network.config.region)  # [kW/K]

            # calculate updated node temperatures on the supply network with updated edge mass flow
            t_supply_nodes_2__k, plant_node, q_loss_edges_2_supply_kW = calc_supply_temperatures(
                thermal_network.T_ground_K[t],
                edge_node_df.copy(),
                edge_mass_flow_df_2_kgs, k,
                thermal_network.t_target_supply_df.loc[t],
                thermal_network.network_type,
                thermal_network.all_nodes_df, thermal_network)
            # calculate edge temperature for heat transfer coefficient within iteration
            t_edge__k = calc_edge_temperatures(t_supply_nodes_2__k, edge_node_df.copy())

            # write supply temperatures to substation nodes
            t_substation_supply_2 = write_nodes_values_to_substations(t_supply_nodes_2__k, thermal_network.all_nodes_df)

            # check if the supply temperature at substations converged
            node_dt = t_substation_supply_2 - t_substation_supply__k
            if node_dt.dropna(axis=1).empty == True:
                max_node_dt = 0
            else:
                max_node_dt = max(abs(node_dt).dropna(axis=1).values[0])
                # max supply node temperature difference

            if max_node_dt > 1 and iteration < 10:
                # update the substation supply temperature and re-enter the iteration
                t_substation_supply__k = t_substation_supply_2
                # print(iteration, 'iteration. Maximum node temperature difference:', max_node_dT)
                iteration += 1
            elif max_node_dt > 10 and 20 > iteration >= 10:
                # FIXME: This is to avoid endless iteration, other design strategies should be implemented.
                # update the substation supply temperature and re-enter the iteration
                t_substation_supply__k = t_substation_supply_2
                # print(iteration, 'iteration. Maximum node temperature difference:', max_node_dT)
                iteration += 1
            else:
                min_iteration = 0
                # do not increase mass flows further, already converged
                thermal_network.delta_cap_mass_flow[t] = 0
                # calculate substation return temperatures according to supply temperatures
                t_return_all_2, \
                mdot_all_2, _ = substation_matrix.substation_return_model_main(thermal_network,
                                                                               t_substation_supply_2, t,
                                                                               thermal_network.building_names)
                # write consumer substation return T and required flow rate to nodes
                t_substation_return_df_2 = write_substation_temperatures_to_nodes_df(thermal_network.all_nodes_df,
                                                                                     t_return_all_2)  # (1xn)
                mass_flow_substations_nodes_df_2 = write_substation_values_to_nodes_df(thermal_network.all_nodes_df,
                                                                                       mdot_all_2)

                # exit iteration
                flag = 1
                if not max_node_dt < 1:
                    # print('supply temperature converged after', iteration, 'iterations.', 'dT:', max_node_dT)
                    # else:
                    print('Warning: supply temperature did not converge after', iteration, 'iterations at timestep', t,
                          '. dT:', max_node_dt)

                # calculate node temperatures on the return network
                # calculate final edge temperature and heat transfer coefficient
                # todo: suboptimal because using supply temperatures (limited effect since effects only water conductivity). Could be solved by iteration.
                k = calc_aggregated_heat_conduction_coefficient(edge_mass_flow_df_2_kgs,
                                                                thermal_network.locator,
                                                                thermal_network.edge_df,
                                                                thermal_network.pipe_properties, t_edge__k,
                                                                thermal_network.network_type,
                                                                thermal_network.config.region)  # [kW/K]

                t_return_nodes_2__k, \
                q_loss_edges_2_return_kW = calc_return_temperatures(thermal_network.T_ground_K[t],
                                                                    edge_node_df.copy(),
                                                                    edge_mass_flow_df_2_kgs,
                                                                    mass_flow_substations_nodes_df_2, k,
                                                                    t_substation_return_df_2, thermal_network)

        total_heat_loss_kW = q_loss_edges_2_return_kW + q_loss_edges_2_supply_kW

        # calculate plant heat requirements according to plant supply/return temperatures
        plant_heat_requirement_kw = calc_plant_heat_requirement(plant_node, t_supply_nodes_2__k, t_return_nodes_2__k,
                                                                mass_flow_substations_nodes_df_2)

    else:
        t_supply_nodes_2__k = np.full(thermal_network.edge_node_df.shape[0], np.nan)
        t_return_nodes_2__k = np.full(thermal_network.edge_node_df.shape[0], np.nan)
        q_loss_edges_2_supply_kW = np.full(thermal_network.edge_node_df.shape[1], 0)
        edge_mass_flow_df_2_kgs = thermal_network.edge_mass_flow_df.ix[t]
        plant_heat_requirement_kw = np.full(sum(thermal_network.all_nodes_df['Type'] == 'PLANT'), 0)
        total_heat_loss_kW = np.full(thermal_network.edge_node_df.shape[1], 0)

    return t_supply_nodes_2__k, t_return_nodes_2__k, plant_heat_requirement_kw, edge_mass_flow_df_2_kgs, \
           q_loss_edges_2_supply_kW, total_heat_loss_kW


def reset_min_mass_flow_variables(thermal_network, t):
    '''
    This function resets the parameters used for data storage for the minimum mass flow iteration
    :param thermal_network:
    :return:
    '''
    for key in thermal_network.config.thermal_network.substation_cooling_systems:
        key = 'cs_' + key
        if not key in thermal_network.cc_old.keys():
            thermal_network.cc_old[key] = {}
        if not t in thermal_network.cc_old[key].keys():
            thermal_network.cc_old[key][t] = pd.DataFrame(index=['0'])
        if not key in thermal_network.cc_value.keys():
            thermal_network.cc_value[key] = {}
        if t not in thermal_network.cc_value[key].keys():
            thermal_network.cc_value[key][t] = pd.DataFrame(index=['0'])
    for key in thermal_network.config.thermal_network.substation_heating_systems:
        key = 'hs_' + key
        if not key in thermal_network.ch_old.keys():
            thermal_network.ch_old[key] = {}
        if not t in thermal_network.ch_old[key].keys():
            thermal_network.ch_old[key][t] = pd.DataFrame(index=['0'])
        if not key in thermal_network.ch_value.keys():
            thermal_network.ch_value[key] = {}
        if t not in thermal_network.ch_value[key].keys():
            thermal_network.ch_value[key][t] = pd.DataFrame(index=['0'])
    thermal_network.nodes[t] = []


def calc_plant_heat_requirement(plant_node, t_supply_nodes, t_return_nodes, mass_flow_substations_nodes_df):
    """
    calculate plant heat requirements according to plant supply/return temperatures and flow rate
    :param plant_node: list of plant nodes
    :param t_supply_nodes: node temperatures on the supply network
    :param t_return_nodes: node temperatures on the return network
    :param mass_flow_substations_nodes_df: substation mass flows
    :type plant_node: ndarray
    :type t_supply_nodes: ndarray
    :type t_return_nodes: ndarray
    :type mass_flow_substations_nodes_df: pandas dataframe
    :return:
    """
    plant_heat_requirement_kw = np.full(plant_node.size, np.nan)
    for i in range(plant_node.size):
        node = plant_node[i]
        heat_requirement = HEAT_CAPACITY_OF_WATER_JPERKGK / 1000 * (t_supply_nodes[node] - t_return_nodes[node]) * abs(
            mass_flow_substations_nodes_df.iloc[0, node])
        plant_heat_requirement_kw[i] = heat_requirement
    return plant_heat_requirement_kw


def write_nodes_values_to_substations(t_supply_nodes, all_nodes_df):
    """
    This function writes node values to the corresponding building substations.

    :param t_supply_nodes: DataFrame of supply line node temperatures (nx1)
    :param all_nodes_df: DataFrame that contains all nodes, whether a node is a consumer, plant, or neither,
                        and, if it is a consumer or plant, the name of the corresponding building               (2 x n)

    :type t_supply_nodes: DataFrame
    :type all_nodes_df: DataFrame

    :return T_substation_supply: dataframe with node values matched to building substations
    :rtype T_substation_supply: DataFrame
    """
    all_nodes_df['T_supply'] = t_supply_nodes
    if 'coordinates' in all_nodes_df.columns:
        # drop column with coordinates fom all_nodes_df
        all_nodes_df = all_nodes_df.drop('coordinates', axis=1)
    t_substation_supply = all_nodes_df[all_nodes_df.Building != 'NONE'].set_index(['Building'])
    t_substation_supply = t_substation_supply.drop('Type', axis=1)
    return t_substation_supply.T


def calc_supply_temperatures(t_ground__k, edge_node_df, mass_flow_df, k, t_target_supply__c, network_type,
                             all_nodes_df, thermal_network):
    """
    This function calculate the node temperatures considering heat losses in the supply network.
    Starting from the plant supply node, the function go through the edge-node index to search for the outlet node, and
    calculate the outlet node temperature after heat loss. And starting from the outlet node, the function calculates
    the node temperature at the corresponding pipe outlet, and the calculation goes on until all the node temperatures
    are solved. At nodes connecting to multiple pipes, the mixing temperature is calculated.

    :param t_ground__k: vector with ground temperatures in K
    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0. E.g. a plant will only have exiting flows,
                        so only negative values                                          (n x e)
    :param mass_flow_df: DataFrame containing the mass flow rate for each edge e at each time of the year t (1 x e)
    :param k: aggregated heat conduction coefficient for each pipe                                          (1 x e)
    :param t_target_supply__c: target supply temperature at each substation
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling ('DC')
                         network

    :type edge_node_df: DataFrame
    :type mass_flow_df: DataFrame
    :type network_type: str

    :return t_node.T: list of node temperatures (nx1)
    :return plant_node: the index of the plant node
    :rtype t_node.T: list
    :rtype plant_node: numpy array

    """
    z = np.asarray(edge_node_df.copy())  # (nxe) edge-node matrix
    z_pipe_out = z.clip(min=0)  # pipe outlet matrix
    z_pipe_in = z.clip(max=0)  # pipe inlet matrix

    m_d = np.zeros((z.shape[1], z.shape[1]))  # (exe) pipe mass flow rate matrix
    np.fill_diagonal(m_d, mass_flow_df)

    # matrices to store results
    t_e_out = z_pipe_out.copy()
    t_e_in = z_pipe_in.copy().dot(-1)
    t_node = np.zeros(z.shape[0])
    z_note = z.copy()  # matrix to store information of solved nodes

    # start node temperature calculation
    flag = 0
    # set initial supply temperature guess to the target substation supply temperature
    t_plant_sup_0 = 273.15 + t_target_supply__c.max() if network_type == 'DH' else 273.15 + t_target_supply__c.min()
    t_plant_sup = t_plant_sup_0
    iteration = 0
    while flag == 0:
        # not_stuck variable is necessary because of looped networks. Here it is possible that we have only a closed
        # loop remaining and no obvious place to start. In this case, iteration with an initial value is necessary
        not_stuck = np.array([True] * z.shape[0])
        # count number of iterations
        temp_iter = 0
        # tolerance for convergence of temperature
        temp_tolerance = 1
        # initialize delta to some value above the tolerance
        delta_temp_0 = 2
        # iterate over temperatures for loop networks
        while delta_temp_0 >= temp_tolerance:
            t_e_out_old = np.array(t_e_out)
            # reset_matrixes
            z_note = z.copy()
            t_e_out = z_pipe_out.copy()
            t_e_in = z_pipe_in.copy().dot(-1)
            t_node = np.zeros(z.shape[0])

            # # calculate the pipe outlet temperature from the plant node
            for i in range(z.shape[0]):
                if all_nodes_df.iloc[i]['Type'] == 'PLANT':  # find plant node
                    # write plant inlet temperature
                    t_node[i] = t_plant_sup  # assume plant inlet temperature
                    edge = np.where(t_e_in[i] != 0)[0]  # find edge index
                    t_e_in[i] = t_e_in[i] * t_node[i]
                    # calculate pipe outlet temperature
                    calc_t_out(i, edge, k, m_d, z, t_e_in, t_e_out, t_ground__k, z_note, thermal_network)
            plant_node = t_node.nonzero()[0]  # the node indices of the plant nodes in the edge-node index


            # Identify all nodes with no in or outflows and delete those values from the z matrixes
            # This is necessary to avoid getting stuck in a loop network with no mass flows inside the loop
            for i in range(z_note.shape[0]):
                if np.isclose(sum(np.dot(m_d, z_pipe_out[i])),0) and np.isclose(sum(np.dot(m_d, z_pipe_in[i])),0):
                    t_node[i] = np.nan
                    # no in our outflows, clear in and outflows at this node
                    # and clear node incoming flows from the corresponding edges
                    outflowing_edges = [a for a, x in enumerate(z_note[i]) if np.isclose(x, 1.0)]
                    if outflowing_edges:
                        for edge in outflowing_edges:  # delete values where we were supposed to flow to
                            target_node = np.where(z_note[:, edge] == -1)[0]
                            z_note[target_node, edge] = 0.0
                            z_pipe_in[target_node, edge] = 0.0
                            t_e_in[target_node, edge] = 0.0
                    outflowing_edges = [a for a, x in enumerate(z_note[i]) if np.isclose(x, -1.0)]
                    if outflowing_edges:
                        for edge in outflowing_edges:  # delete values where we were supposed to flow to
                            target_node = np.where(z_note[:, edge] == 1)[0]
                            z_note[target_node, edge] = 0.0
                            z_pipe_out[target_node, edge] = 0.0
                            t_e_out[target_node, edge] = 0.0
                    target_edges = [a for a, x in enumerate(z_note[i]) if not np.isclose(x, 0.0)]
                    if target_edges:
                        for target_edge in target_edges:
                            z_note[i, target_edge] = 0.0
                            z_pipe_in[i, target_edge] = 0.0
                            z_pipe_out[i, target_edge] = 0.0
                            t_e_in[i, target_edge] = 0.0
                            t_e_out[i, target_edge] = 0.0

            # # calculate pipe outlet temperature and node temperature for the rest
            while np.count_nonzero(np.isclose(t_node, 0)) > 0:
                if not_stuck.any():  # if there are no changes for all elements but we have not yet solved the system
                    z, z_note, m_d, t_e_out, z_pipe_out, t_node, t_e_in, t_ground__k, not_stuck = calculate_outflow_temp(
                        z,
                        z_note,
                        m_d,
                        t_e_out,
                        z_pipe_out,
                        t_node,
                        t_e_in,
                        t_ground__k,
                        not_stuck,
                        k, thermal_network)
                else:  # stuck! this can happen with loops
                    for i in range(np.shape(t_e_out)[1]):
                        #check if we have a mass flow on this edge
                        if np.any(t_e_out[:, i] == 1):
                            z_note[np.where(t_e_out[:, i] == 1), i] = 0  # remove inflow value from z_note
                            if temp_iter < 1:  # do this in first iteration only, since there is no previous value
                                t_e_out[np.where(t_e_out[:, i] == 1), i] = t_node[
                                    t_node.nonzero()].mean()  # assume some node temperature
                            else:
                                t_e_out[np.where(t_e_out[:, i] == 1), i] = t_e_out_old[np.where(t_e_out[:, i] == 1), i]
                            break
                    not_stuck = np.array([True] * z.shape[0])

            delta_temp_0 = np.max(abs(t_e_out_old - t_e_out))
            temp_iter = temp_iter + 1

        # # iterate the plant supply temperature until all the node temperature reaches the target temperatures
        if network_type == 'DH':
            # calculate the difference between node temperature and the target supply temperature at substations
            # [K] temperature differences b/t node supply and target supply
            d_t = (t_node - (t_target_supply__c + 273.15)).dropna()
            # enter iteration if the node supply temperature is lower than the target supply temperature
            # (0.1 is the tolerance)
            if all(d_t > -0.1) == False and iteration <= 30:
                # increase plant supply temperature and re-iterate the node supply temperature calculation
                # increase by the maximum amount of temperature deficit at nodes
                t_plant_sup = t_plant_sup + abs(d_t.min())
                # check if this term is positive, looping causes t_e_out to sink instead of rise.

                # reset the matrices for supply network temperature calculation
                z_note = z.copy()
                t_e_out = z_pipe_out.copy()
                t_e_in = z_pipe_in.copy().dot(-1)
                t_node = np.zeros(z.shape[0])
                iteration += 1

            elif all(d_t > -0.1) == False and iteration > 30:
                # end iteration if too many iterations
                print('cannot fulfill substation supply node temperature requirement after iterations:',
                      iteration, abs(d_t).min())
                node_insufficient = d_t[d_t < 0].index.values
                for node in range(node_insufficient.size):
                    index_insufficient = np.argwhere(edge_node_df.index == node_insufficient[node])[0]
                    t_node[index_insufficient] = t_target_supply__c[index_insufficient] + 273.15
                    # force setting node temperature to target to avoid substation HEX calculation error.
                    # However, it might potentially cause error at mass flow iteration.
                flag = 1
            else:
                flag = 1
        else:  # when network type == 'DC'
            # calculate the difference between node temperature and the target supply temperature at substations
            # [K] temperature differences b/t node supply and target supply
            d_t = (t_node - (t_target_supply__c + 273.15)).dropna()

            # enter iteration if the node supply temperature is higher than the target supply temperature
            # (0.1 is the tolerance)
            if all(d_t < 0.1) == False and iteration <= 30:
                # increase plant supply temperature and re-iterate the node supply temperature calculation
                # increase by the maximum amount of temperature deficit at nodes
                t_plant_sup = t_plant_sup - abs(d_t.max())
                z_note = z.copy()
                t_e_out = z_pipe_out.copy()
                t_e_in = z_pipe_in.copy().dot(-1)
                t_node = np.zeros(z.shape[0])
                iteration += 1
            elif all(d_t < 0.1) == False and iteration > 30:
                # end iteration if too many iterations
                print('cannot fulfill substation supply node temperature requirement after iterations:',
                      iteration, d_t.min())
                node_insufficient = d_t[d_t > 0].index.values
                for node in range(node_insufficient.size):
                    index_insufficient = np.argwhere(edge_node_df.index == node_insufficient[node])[0]
                    t_node[index_insufficient] = t_target_supply__c[index_insufficient] + 273.15
                    # force setting node temperature to target to avoid substation HEX calculation error.
                    # However, it might potentially cause error at mass flow iteration.
                    flag = 1
            else:
                flag = 1

    # calculate pipe heat losses
    q_loss_edges_kw = np.zeros(z_note.shape[1])
    for edge in range(z_note.shape[1]):
        if m_d[edge, edge] > 0:
            dT_edge = np.nanmax(t_e_in[:, edge]) - np.nanmax(t_e_out[:, edge])
            q_loss_edges_kw[edge] = m_d[edge, edge] * HEAT_CAPACITY_OF_WATER_JPERKGK / 1000 * dT_edge  # kW

    return t_node.T, plant_node, q_loss_edges_kw


def calculate_outflow_temp(z, z_note, m_d, t_e_out, z_pipe_out, t_node, t_e_in, t_ground_k, not_stuck, k,
                           thermal_network):
    """
    calculates outflow temperature of nodes based on incoming mass flows and temperatures.

    :param z: copy of edge-node matrix (n x e)
    :param z_note: copy of z matrix (n x e)
    :param m_d: pipe mass flow rate matrix (e x e)
    :param t_e_out: storage for outflow temperatures (n x e)
    :param z_pipe_out: matrix storing only outflow index (n x e)
    :param t_node: node temperature vector (n x 1)
    :param t_e_in: storage for inflow temperatures (n x e)
    :param t_ground_k: ground temperature over time
    :param not_stuck: vector indicating if we are stuck in a looped network and need iteration (1 x e)
    :param k: thermal coefficient for heat transfer (1 x e)

    :type z: dataframe (n x e)
    :type z_note: dataframe(n x e)
    :type m_d: dataframe(e x e)
    :type t_e_out: dataframe (n x e)
    :type z_pipe_out: dataframe (n x e)
    :type t_node: ndarray (n x 1)
    :type t_e_in: dataframe (n x e)
    :type t_ground_k: dataframe
    :type not_stuck: ndarray (1 x e)
    :type k: ndarray (1 x e)

    :return z: copy of edge-node matrix (n x e)
    :return z_note: copy of z matrix (n x e)
    :return m_d: pipe mass flow rate matrix (e x e)
    :return t_e_out: storage for outflow temperatures (n x e)
    :return z_pipe_out: matrix storing only outflow index (n x e)
    :return t_node: node temperature vector (n x 1)
    :return t_e_in: storage for inflow temperatures (n x e)
    :return t_ground_k: ground temperature over time
    :return not_stuck: vector indicating if we are stuck in a looped network and need iteration (1 x e)

    :rtype z: dataframe (n x e)
    :rtype z_note: dataframe(n x e)
    :rtype m_d: dataframe(e x e)
    :rtype t_e_out: dataframe (n x e)
    :rtype z_pipe_out: dataframe (n x e)
    :rtype t_node: ndarray (n x 1)
    :rtype t_e_in: dataframe (n x e)
    :rtype t_ground_k: dataframe
    :rtype not_stuck: ndarray (1 x e)

    """
    for j in range(z.shape[0]):
        # check if all inlet flow info towards node j are known (only -1 left in row Z_note[j])
        if np.count_nonzero(z_note[j] == 1) == 0 and np.count_nonzero(z_note[j] == 0) != z.shape[1]:
            # calculate node temperature with merging flows from pipes
            part1 = np.dot(m_d, np.nan_to_num(t_e_out[j])).sum()  # sum of massflows entering node * Entry Temperature
            part2 = np.dot(m_d, z_pipe_out[j]).sum()  # total massflow leaving node
            t_node[j] = part1 / part2
            if np.isnan(t_node[j]):
                raise ValueError('There are no flow entering/existing node', j,
                                 '. Please check if the edge_node_df make sense.')
            # write the node temperature to the corresponding pipe inlet
            t_e_in[j] = t_e_in[j] * t_node[j]

            # calculate pipe outlet temperatures entering from node j
            for edge in range(z_note.shape[1]):
                # find the pipes with water flow leaving from node j
                if t_e_in[j, edge] != 0:
                    # calculate the pipe outlet temperature entering from node j
                    calc_t_out(j, edge, k, m_d, z, t_e_in, t_e_out, t_ground_k, z_note, thermal_network)
            not_stuck[j] = True
        # fill in temperatures for nodes at network branch ends
        elif np.isclose(t_node[j], 0) and t_e_out[j].max() != 1:
            t_node[j] = np.nan if np.isnan(t_e_out[j]).any() else t_e_out[j].max()
            not_stuck[j] = True
        # elif t_e_out[j].min() < 0:
        #    print('negative node temperature!')
        #    not_stuck[j] = True
        else:
            not_stuck[j] = False

    return z, z_note, m_d, t_e_out, z_pipe_out, t_node, t_e_in, t_ground_k, not_stuck


def calc_return_temperatures(t_ground, edge_node_df, mass_flow_df, mass_flow_substation_df, k, t_return,
                             thermal_network):
    """
    This function calculates the node temperatures considering heat losses in the return line.
    Starting from the substations at the end branches, the function goes through the edge-node index to search for the
    outlet node, and calculates the outlet node temperature after heat loss. Starting from that outlet node, the function
    calculates the node temperature at the corresponding pipe outlet, and the calculation goes on until all the node
    temperatures are solved. At nodes connecting to multiple pipes, the mixing temperature is calculated.

    :param t_ground: vector with ground temperatures in K
    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0. E.g. a plant will only have exiting flows,
                        so only negative values
    :param mass_flow_df: DataFrame containing the mass flow rate for each edge e at each t
    :param mass_flow_substation_df: DataFrame containing the mass flow rate for each substation at each t
    :param k: aggregated heat conduction coefficient for each pipe
    :param t_return: return temperatures at the substations

    :return t_node.T: list of node temperatures (nx1)
    :rtype t_node.T: list

    """

    z = np.asarray(edge_node_df.copy()) * (-1)  # (n x e) edge-node matrix
    z_pipe_out = z.clip(min=0)  # pipe outlet matrix
    z_pipe_in = z.clip(max=0)  # pipe inlet matrix

    m_sub = np.zeros((z.shape[0], z.shape[0]))  # (nxn) substation flow rate matrix
    np.fill_diagonal(m_sub, mass_flow_substation_df)

    m_d = np.zeros((z.shape[1], z.shape[1]))  # (exe) pipe mass flow rate matrix
    np.fill_diagonal(m_d, mass_flow_df)

    # matrices to store results
    t_e_out = z_pipe_out.copy()
    t_node = np.zeros(z.shape[0])

    # same as for supply temperatures this vector stores information on if we are stuck while calculating looped
    # networks and need to begin iteration with an initial guess
    not_stuck = np.array([True] * z.shape[0])
    # count iterations
    temp_iter = 0
    # temperature tolerance for convergence
    temp_tolerance = 1
    # some initial value larger than the tolerance
    delta_temp_0 = 2

    while delta_temp_0 >= temp_tolerance:
        t_e_out_old = np.array(t_e_out)
        # reset_matrixes
        z_note = z.copy()
        t_e_out = z_pipe_out.copy()
        t_e_in = z_pipe_in.copy().dot(-1)
        t_node = np.zeros(z.shape[0])
        m_sub = np.zeros((z.shape[0], z.shape[0]))  # (nxn) substation flow rate matrix
        np.fill_diagonal(m_sub, mass_flow_substation_df)

        # Identify all nodes with no in or outflows and delete those values from the z matrixes
        # This is necessary to avoid getting stuck in a loop network with no mass flows inside the loop
        for i in range(z_note.shape[0]):
            if np.isclose(sum(np.dot(m_d, z_pipe_out[i])), 0) and np.isclose(sum(np.dot(m_d, z_pipe_in[i])), 0):
                t_node[i] = np.nan
                # no in our outflows, clear in and outflows at this node
                # and clear node incoming flows from the corresponding edges
                outflowing_edges = [a for a, x in enumerate(z_note[i]) if np.isclose(x, 1.0)]
                if outflowing_edges:
                    for edge in outflowing_edges:  # delete values where we were supposed to flow to
                        target_node = np.where(z_note[:, edge] == -1)[0]
                        z_note[target_node, edge] = 0.0
                        z_pipe_in[target_node, edge] = 0.0
                        t_e_in[target_node, edge] = 0.0
                outflowing_edges = [a for a, x in enumerate(z_note[i]) if np.isclose(x, -1.0)]
                if outflowing_edges:
                    for edge in outflowing_edges:  # delete values where we were supposed to flow to
                        target_node = np.where(z_note[:, edge] == 1)[0]
                        z_note[target_node, edge] = 0.0
                        z_pipe_out[target_node, edge] = 0.0
                        t_e_out[target_node, edge] = 0.0
                target_edges = [a for a, x in enumerate(z_note[i]) if not np.isclose(x, 0.0)]
                if target_edges:
                    for target_edge in target_edges:
                        z_note[i, target_edge] = 0.0
                        z_pipe_in[i, target_edge] = 0.0
                        z_pipe_out[i, target_edge] = 0.0
                        t_e_in[i, target_edge] = 0.0
                        t_e_out[i, target_edge] = 0.0

        # calculate the return pipe node temperature of substations locating at the end of the branch
        for i in range(z.shape[0]):
            # choose the consumer nodes locating at the end of the branches
            if np.count_nonzero(np.isclose(z_note[i], 1)) == 0 and np.count_nonzero(np.isclose(z_note[i], 0)) != z.shape[1]:
                t_node[i] = t_return.values[0, i]
                # t_node[i] = map(list, t_return.values)[0][i]
                if not np.isnan(t_node[i]):
                    for edge in range(z_note.shape[1]):
                        if t_e_in[i, edge] != 0:
                            t_e_in[i, edge] = map(list, t_return.values)[0][i]
                        # calculate pipe outlet
                        calc_t_out(i, edge, k, m_d, z, t_e_in, t_e_out, t_ground, z_note, thermal_network)

        while z_note.max() >= 1:
            if not_stuck.any():
                for j in range(z.shape[0]):
                    if np.count_nonzero(np.isclose(z_note[j], 1)) == 0 and np.count_nonzero(np.isclose(z_note[j], 0)) != \
                            z.shape[
                                1]:  # only -1 values in z_note
                        # calculate node temperature with merging flows from pipes
                        t_node[j] = calc_return_node_temperature(j, m_d, t_e_out, t_return, z_pipe_out, m_sub)
                        for edge in range(z_note.shape[1]):
                            if t_e_in[j, edge] != 0:
                                t_e_in[j, edge] = t_node[j]
                                # calculate pipe outlet
                                calc_t_out(j, edge, k, m_d, z, t_e_in, t_e_out, t_ground, z_note, thermal_network)
                        not_stuck[j] = True
                    elif np.argwhere(np.isclose(z_note[j], 0)).size == z.shape[1] and np.isclose(t_node[j],
                                                                                                 0):  # all 0 values
                        t_node[j] = calc_return_node_temperature(j, m_d, t_e_out, t_return, z_pipe_out, m_sub)
                        not_stuck[j] = False
                    else:
                        not_stuck[j] = False

            else:  # we got stuck because we have loops, we need an initial value
                for q in range(np.shape(t_e_out)[1]):
                    if np.any(t_e_out[:, q] == 1):
                        z_note[np.where(t_e_out[:, q] == 1), q] = 0  # remove inflow value from Z_note
                        if temp_iter < 1:
                            t_e_out[np.where(t_e_out[:, q] == 1), q] = t_return.values[
                                0, q]  # assume some node temperature
                        else:
                            t_e_out[np.where(t_e_out[:, q] == 1), q] = t_e_out_old[
                                np.where(t_e_out[:, q] == 1), q]  # iterate
                        break
                not_stuck = np.array([True] * z.shape[0])

        # calculate temperature with merging flows from pipes at the plant node
        if len(np.where(np.isclose(t_node, 0))[0]) != 0:
            node_index = np.where(np.isclose(t_node, 0))[0][0]
            m_sub[node_index] = 0
            t_node[node_index] = calc_return_node_temperature(node_index, m_d, t_e_out, t_return,
                                                              z_pipe_out, m_sub)

        # calculate pipe heat losses
        q_loss_edges_kW = np.zeros(z_note.shape[1])
        for edge in range(z_note.shape[1]):
            if m_d[edge, edge] > 0:
                dT_edge = np.nanmax(t_e_in[:, edge]) - np.nanmax(t_e_out[:, edge])
                q_loss_edges_kW[edge] = m_d[edge, edge] * HEAT_CAPACITY_OF_WATER_JPERKGK / 1000 * dT_edge  # kW

        delta_temp_0 = np.max(abs(t_e_out_old - t_e_out))
        temp_iter = temp_iter + 1

    return t_node, q_loss_edges_kW


def calc_return_node_temperature(index, m_d, t_e_out, t_return, z_pipe_out, m_sub):
    """
    The function calculates the node temperature with merging flows from pipes in the return line.

    :param index: node index
    :param m_d: pipe mass flow matrix (exe)
    :param t_e_out: pipe outlet temperatures in edge node matrix (nxe)
    :param t_return: list of substation return temperatures
    :param z_pipe_out: pipe outlet matrix (nxe)
    :param m_sub: DataFrame substation flow rate

    :type index: floatT_return_all_2
    :type m_d: DataFrame
    :type t_e_out: DataFrame
    :type t_return: list
    :type z_pipe_out: DataFrame
    :type m_sub: DataFrame

    :returns t_node: node temperature with merging flows in the return line
    :rtype t_node: float

    """
    total_mass_flow_to_node = np.dot(m_d, z_pipe_out[index]).sum() + m_sub[index].max()
    if np.isclose(total_mass_flow_to_node, 0):
        # set node temperature to nan if no flow to node
        t_node = np.nan
    else:
        total_mcp_from_edges = np.dot(m_d, np.nan_to_num(t_e_out[index])).sum()
        total_mcp_from_substations = 0 if np.isclose(m_sub[index].max(), 0) else np.dot(m_sub[index].max(),
                                                                                        t_return.values[0, index])
        t_node = (total_mcp_from_edges + total_mcp_from_substations) / total_mass_flow_to_node
    return t_node


def calc_t_out(node, edge, k_old, m_d, z, t_e_in, t_e_out, t_ground, z_note, thermal_network):
    """
    Given the pipe inlet temperature, this function calculate the outlet temperature of the pipe.
    Following the reference of [Wang et al., 2016]_.

    :param node: node index
    :param edge: edge indices
    :param k: DataFrame of aggregated heat conduction coefficient for each pipe (exe)
    :param m_d: DataFrame of pipe flow rate (exe)
    :param z: DataFrame of  edge_node_matrix (nxe)
    :param t_e_in: DataFrame of pipe inlet temperatures [K] in edge_node_matrix (nxe)
    :param t_e_out: DataFrame of  pipe outlet temperatures [K] in edge_node_matrix (nxe)
    :param t_ground: vector with ground temperatures in [K]
    :param z_note: DataFrame of the matrix to store information of solved nodes

    :type node: float
    :type edge: np array
    :type k: DataFrame
    :type m_d: DataFrame
    :type z: DataFrame
    :type t_e_in: DataFrame
    :type t_e_out: DataFrame
    :type t_ground: list
    :type z_note: DataFrame

    :returns The calculated pipe outlet temperatures are directly written to T_e_out

    ..[Wang et al, 2016] Wang J., Zhou, Z., Zhao, J. (2016). A method for the steady-state thermal simulation of
    district heating systems and model parameters calibration. Energy Conversion and Management, 120, 294-305.
    """
    # calculate pipe outlet temperature
    if isinstance(edge, np.ndarray) == False:
        edge = np.array([edge])

    m_d = np.round(m_d, decimals=5)  # round to avoid errors at very very low massflows

    for i in range(edge.size):
        e = edge[i]
        k = k_old[e, e]
        m = m_d[e, e]
        out_node_index = np.where(z[:, e] == 1)[0].max()
        if np.isclose(abs(m), 0) and np.isclose(z_note[node, e], -1):
            # set outlet temperature to nan if no flow is going out from node to connected edges
            t_e_out[out_node_index, e] = np.nan
            z_note[:, e] = 0

        elif np.isclose(z_note[node, e], -1):
            # calculate outlet temperature if flow goes from node to out_node through edge
            t_e_out[out_node_index, e] = (t_e_in[node, e] * (
                    k / 2 - m * HEAT_CAPACITY_OF_WATER_JPERKGK / 1000) - k * t_ground) / (
                                                 -m * HEAT_CAPACITY_OF_WATER_JPERKGK / 1000 - k / 2)  # [K]
            dT = t_e_in[node, e] - t_e_out[out_node_index, e]
            if abs(dT) > 30:
                print('High temperature loss on edge', e, '. Loss:', abs(dT))
                #Store value
                if not str(
                        e) in thermal_network.problematic_edges.keys():  # add problematic edge and corresponding mass flow to the dictionary
                    thermal_network.problematic_edges[str(e)] = m
                elif thermal_network.problematic_edges[str(
                            e)] > m:  # if the mass flow saved at this edge is smaller than the current mass flow, save the smaller value
                        thermal_network.problematic_edges[str(e)] = m

                if (k / 2 - m * HEAT_CAPACITY_OF_WATER_JPERKGK / 1000) > 0:
                    print(
                        'Exit temperature decreasing at entry temperature increase. Possible at low massflows. Massflow:',
                        m, ' on edge: ', e)
                if thermal_network.network_type == 'DH':
                    t_e_out[out_node_index, e] = t_e_in[node, e] - 30  # assumes maximum 30 K temperature loss
                else:
                    t_e_out[out_node_index, e] = t_e_in[node, e] + 30  # assumes maximum 30 K temperature loss
                # Induces some error but necessary to avoid spiraling to negative temperatures
                # Todo: find better method which allows loss calculation at low massflows
            z_note[:, e] = 0.0


def calc_aggregated_heat_conduction_coefficient(mass_flow, locator, edge_df, pipe_properties_df, temperature__k,
                                                network_type, region):
    """
    This function calculates the aggregated heat conduction coefficients of all the pipes.
    Following the reference from [Wang et al., 2016].
    The pipe material properties are referenced from _[A. Kecabas et al., 2011], and the pipe catalogs are referenced
    from _[J.A. Fonseca et al., 2016] and _[isoplus].

    :param mass_flow: Vector with mass flows of each edge                           (e x 1)
    :param locator: an InputLocator instance set to the scenario to work on
    :param pipe_properties_df: DataFrame containing the pipe properties for each edge in the network
    :param temperature__k: matrix containing the temperature of the water in each edge e at time t             (t x e)
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling ('DC')
                         network
    :param edge_df: list of edges and their corresponding lengths and start and end nodes

    :type temperature__k: list
    :type network_type: str
    :type mass_flow: DataFrame
    :type locator: InputLocator
    :type pipe_properties_df: DataFrame
    :type edge_df: DataFrame

    :return k_all: DataFrame of aggregated heat conduction coefficients (1 x e) for all edges

    ..[Wang et al, 2016] Wang J., Zhou, Z., Zhao, J. (2016). A method for the steady-state thermal simulation of
      district heating systems and model parameters calibration. Eenergy Conversion and Management, 120, 294-305.

    ..[A. Kecebas et al., 2011] A. Kecebas et al. Thermo-economic analysis of pipe insulation for district heating
      piping systems. Applied Thermal Engineering, 2011.

    ..[J.A. Fonseca et al., 2016] J.A. Fonseca et al. City Energy Analyst (CEA): Integrated framework for analysis and
      optimization of building energy systems in neighborhoods and city districts. Energy and Buildings. 2016

    ..[isoplus] isoplus piping systems. http://en.isoplus.dk/download-centre

    .. Incropera, F. P., DeWitt, D. P., Bergman, T. L., & Lavine, A. S. (2007). Fundamentals of Heat and Mass
       Transfer. Fundamentals of Heat and Mass Transfer. https://doi.org/10.1016/j.applthermaleng.2011.03.022
    """

    L_pipe = edge_df['pipe length']
    material_properties = pd.read_excel(locator.get_thermal_networks(region), sheetname=['MATERIAL PROPERTIES'])[
        'MATERIAL PROPERTIES']
    material_properties = material_properties.set_index(material_properties['material'].values)
    conductivity_pipe = material_properties.ix['Steel', 'lambda_WmK']  # _[A. Kecebas et al., 2011]
    conductivity_insulation = material_properties.ix['PUR', 'lambda_WmK']  # _[A. Kecebas et al., 2011]
    conductivity_ground = material_properties.ix['Soil', 'lambda_WmK']  # _[A. Kecebas et al., 2011]
    network_depth = NETWORK_DEPTH  # [m]
    extra_heat_transfer_coef = 0.2  # _[Wang et al, 2016] to represent heat losses from valves and other attachments

    # calculate nusselt number
    nusselt = calc_nusselt(mass_flow, temperature__k, pipe_properties_df[:]['D_int_m':'D_int_m'].values[0],
                           network_type)
    # calculate thermal conductivity of water
    thermal_conductivity = calc_thermal_conductivity(temperature__k)
    # evaluate thermal heat transfer coefficient
    alpha_th = thermal_conductivity * nusselt / pipe_properties_df[:]['D_int_m':'D_int_m'].values[0]  # W/(m^2 * K)

    k_all = []
    for pipe_number, pipe in enumerate(L_pipe.index):
        # calculate heat resistances, equation (3) in Wang et al., 2016
        R_pipe = np.log(pipe_properties_df.loc['D_ext_m', pipe] / pipe_properties_df.loc['D_int_m', pipe]) / (
                2 * math.pi * conductivity_pipe)  # [m*K/W]
        if network_type == 'DC':
            D_ins = 0.25 * pipe_properties_df.loc[
                'D_ins_m', pipe]  # approximation based on COOLMANT CLM 2.0 Pipe catalogue
        else:
            D_ins = pipe_properties_df.loc['D_ins_m', pipe]
        R_insulation = np.log((D_ins+pipe_properties_df.loc['D_ext_m', pipe]) / pipe_properties_df.loc['D_ext_m', pipe]) / (
                2 * math.pi * conductivity_insulation)  # [m*K/W]
        a = 2 * network_depth / (pipe_properties_df.loc['D_ins_m', pipe])
        R_ground = np.log(a + (a ** 2 - 1) ** 0.5) / (2 * math.pi * conductivity_ground)  # [m*K/W]
        # calculate convection heat transfer resistance
        if np.isclose(alpha_th[pipe_number], 0):
            R_conv = 0.2  # case with no massflow, avoids divide by 0 error
        else:
            R_conv = 1 / (
                    alpha_th[pipe_number] * math.pi * pipe_properties_df[:]['D_int_m':'D_int_m'].values[0][pipe_number])
        # calculate the aggregated heat conduction coefficient, equation (4) in Wang et al., 2016
        k = L_pipe[pipe] * (1 + extra_heat_transfer_coef) / (R_pipe + R_insulation + R_ground + R_conv) / 1000  # [kW/K]
        k_all.append(k)
    k_all = abs(np.diag(k_all))
    return k_all


def calc_nusselt(mass_flow_rate_kgs, temperature_K, pipe_diameter_m, network_type):
    """
    Calculates the nusselt number of the internal flow inside the pipes.

    :param pipe_diameter_m: vector containing the pipe diameter in m for each edge e in the network           (e x 1)
    :param mass_flow_rate_kgs: matrix containing the mass flow rate in each edge e at time t                    (t x e)
    :param temperature_K: matrix containing the temperature of the water in each edge e at time t             (t x e)
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling ('DC')
                         network
    :type pipe_diameter_m: ndarray
    :type mass_flow_rate_kgs: ndarray
    :type temperature_K: list
    :type network_type: str

    :return nusselt: calculated nusselt number for flow in each edge		(ex1)
    :rtype nusselt: ndarray

	.. Incropera, F. P., DeWitt, D. P., Bergman, T. L., & Lavine, A. S. (2007).
	    Fundamentals of Heat and Mass Transfer. Fundamentals of Heat and Mass Transfer.
	    https://doi.org/10.1016/j.applthermaleng.2011.03.022
    """

    # calculate variable values necessary for nusselt number evaluation
    reynolds = calc_reynolds(mass_flow_rate_kgs, temperature_K, pipe_diameter_m)
    prandtl = calc_prandtl(temperature_K)
    darcy = calc_darcy(pipe_diameter_m, reynolds, ROUGHNESS)

    nusselt = np.zeros(reynolds.size)
    for rey in range(reynolds.size):
        if reynolds[rey] <= 1:
            # calculate nusselt number only if mass is flowing
            nusselt[rey] = 0
        elif reynolds[rey] <= 2300:
            # calculate the Nusselt number for laminar flow
            nusselt[rey] = 3.66
        elif reynolds[rey] <= 10000:
            # calculate the Nusselt for transient flow
            nusselt[rey] = darcy[rey] / 8 * (reynolds[rey] - 1000) * prandtl[rey] / (
                    1 + 12.7 * (darcy[rey] / 8) ** 0.5 * (prandtl[rey] ** 0.67 - 1))
        else:
            # calculate the Nusselt number for turbulent flow
            # identify if heating or cooling case
            if network_type == 'DH':  # warm fluid, so ground is cooling fluid in pipe, cooling case from view of thermodynamic flow
                nusselt[rey] = 0.023 * reynolds[rey] ** 0.8 * prandtl[rey] ** 0.3
            else:
                # cold fluid, so ground is heating fluid in pipe, heating case from view of thermodynamic flow
                nusselt[rey] = 0.023 * reynolds[rey] ** 0.8 * prandtl[rey] ** 0.4

    return nusselt


# ============================
# Other functions
# ============================


def extract_network_from_shapefile(edge_shapefile_df, node_shapefile_df):
    """
    Extracts network data into DataFrames for pipes and nodes in the network

    :param edge_shapefile_df: DataFrame containing all data imported from the edge shapefile
    :param node_shapefile_df: DataFrame containing all data imported from the node shapefile
    :type edge_shapefile_df: DataFrame
    :type node_shapefile_df: DataFrame
    :return node_df: DataFrame containing all nodes and their corresponding coordinates
    :return edge_df: list of edges and their corresponding lengths and start and end nodes
    :rtype node_df: DataFrame
    :rtype edge_df: DataFrame

    """
    # set precision of coordinates
    decimals = 6
    # create node dictionary with plant and consumer nodes
    node_dict = {}
    node_shapefile_df.set_index("Name", inplace=True)
    node_shapefile_df = node_shapefile_df.astype('object')
    node_shapefile_df['coordinates'] = node_shapefile_df['geometry'].apply(lambda x: x.coords[0])
    # sort node_df by index number
    node_sorted_index = node_shapefile_df.index.to_series().str.split('NODE', expand=True)[1].apply(int).sort_values(
        ascending=True)
    node_shapefile_df = node_shapefile_df.reindex(index=node_sorted_index.index)
    # assign node properties (plant/consumer/none)
    node_shapefile_df['plant'] = ''
    node_shapefile_df['consumer'] = ''
    node_shapefile_df['none'] = ''

    for node, row in node_shapefile_df.iterrows():
        coord_node = row['geometry'].coords[0]
        if row['Type'] == "PLANT":
            node_shapefile_df.loc[node, 'plant'] = node
        elif row['Type'] == "CONSUMER":  # TODO: add 'PROSUMER' by splitting nodes
            node_shapefile_df.loc[node, 'consumer'] = node
        else:
            node_shapefile_df.loc[node, 'none'] = node
        coord_node_round = (round(coord_node[0], decimals), round(coord_node[1], decimals))
        node_dict[coord_node_round] = node

    # create edge dictionary with pipe lengths and start and end nodes
    # complete node dictionary with missing nodes (i.e., joints)
    edge_shapefile_df.set_index("Name", inplace=True)
    edge_shapefile_df = edge_shapefile_df.astype('object')
    edge_shapefile_df['coordinates'] = edge_shapefile_df['geometry'].apply(lambda x: x.coords[0])
    # sort edge_df by index number
    edge_sorted_index = edge_shapefile_df.index.to_series().str.split('PIPE', expand=True)[1].apply(int).sort_values(
        ascending=True)
    edge_shapefile_df = edge_shapefile_df.reindex(index=edge_sorted_index.index)
    # assign edge properties
    edge_shapefile_df['pipe length'] = 0
    edge_shapefile_df['start node'] = ''
    edge_shapefile_df['end node'] = ''

    for pipe, row in edge_shapefile_df.iterrows():
        # get the length of the pipe and add to dataframe
        edge_shapefile_df.loc[pipe, 'pipe length'] = row['geometry'].length
        # get the start and end notes and add to dataframe
        edge_coords = row['geometry'].coords
        start_node = (round(edge_coords[0][0], decimals), round(edge_coords[0][1], decimals))
        end_node = (round(edge_coords[1][0], decimals), round(edge_coords[1][1], decimals))
        if start_node in node_dict.keys():
            edge_shapefile_df.loc[pipe, 'start node'] = node_dict[start_node]
        else:
            print('The start node of ', pipe, 'has no match in node_dict, check precision of the coordinates.')
        if end_node in node_dict.keys():
            edge_shapefile_df.loc[pipe, 'end node'] = node_dict[end_node]
        else:
            print('The end node of ', pipe, 'has no match in node_dict, check precision of the coordinates.')

    # # If a consumer node is not connected to the network, find the closest node and connect them with a new edge
    # # this part of the code was developed for a case in which the node and edge shapefiles were not defined
    # # consistently. This has not been a problem after all, but it could eventually be a useful feature.
    # for node in node_dict:
    #     if node not in pipe_nodes:
    #         min_dist = 1000
    #         closest_node = pipe_nodes[0]
    #         for pipe_node in pipe_nodes:
    #             dist = ((node[0] - pipe_node[0])**2 + (node[1] - pipe_node[1])**2)**.5
    #             if dist < min_dist:
    #                 min_dist = dist
    #                 closest_node = pipe_node
    #         j += 1
    #         edge_dict['EDGE' + str(j)] = [min_dist, node_dict[closest_node][0], node_dict[node][0]]

    return node_shapefile_df, edge_shapefile_df


def write_substation_values_to_nodes_df(all_nodes_df, df_value):
    """
    The function writes values (temperatures or mass flows) from each substations to the corresponding nodes in the
    edge node matrix.

    :param all_nodes_df: DataFrame containing all nodes and whether a node n is a consumer or plant node
                        (and if so, which building that node corresponds to), or neither.                   (2 x n)
    :param df_value: DataFrame of value of each substation
    :param flag: flag == True if the values are temperatures ; flag == False if the value is mass flow

    :return nodes_df: DataFrame with values at each node (1xn)
    :rtype nodes_df: DataFrame

    """

    nodes_df = pd.DataFrame(index=[0], columns=all_nodes_df.index)
    # it is assumed that if there is more than one plant, they all supply the same amount of heat at each time step
    # (i.e., the amount supplied by each plant is not optimized)
    number_of_plants = sum(all_nodes_df['Type'] == 'PLANT')
    consumer_list = all_nodes_df.loc[all_nodes_df['Type'] == 'CONSUMER', 'Building'].values
    plant_mass_flow = df_value[consumer_list].loc[0].sum() / number_of_plants

    # write all flow rates into nodes DataFrame
    ''' NOTE:
            for each node, (mass incoming edges) + (mass supplied) = (mass outgoing edges) + (mass demand)
                           (mass incoming edges) - (mass outgoing edges) = (mass demand) - (mass supplied)
            which equals   (edge node matrix) * (mass flow edge) = (mass demand) - (mass supplied)
                           (edge node matrix) * (mass flow edge) = (mass flow node)

            so mass_flow_node[node] = mass_flow_demand[node] for consumer nodes and
               mass_flow_node[node] = - mass_flow_supply[node] for plant nodes
            (i.e., mass flow is positive if it's a consumer node, negative if it's a supply node)

            assuming only one plant node, the mass flow on the supply side needs to equal the mass flow from consumers
            so mass_flow_supply = - sum(mass_flow_demand[node]) for all nodes

            for the case where there is more than one supply plant, it is assumed for now that all plants supply the
            same share of the total demand of the network
            so mass_flow_supply = - sum(mass_flow_demand)/(number of plants)
        '''

    # assure only mass flow at network consumer substations are counted
    for node, row in all_nodes_df.iterrows():
        if row['Type'] == 'CONSUMER':
            nodes_df[node] = df_value[row['Building']]
            if df_value[row['Building']].any() < 0:
                print('Error, Building trying to be a plant!')
        elif row['Type'] == 'PLANT':
            nodes_df[node] = - plant_mass_flow
        else:
            nodes_df[node] = 0
    return nodes_df


def write_substation_temperatures_to_nodes_df(all_nodes_df, df_value):
    """
    The function writes values (temperatures or mass flows) from each substations to the corresponding nodes in the
    edge node matrix.

    :param all_nodes_df: DataFrame containing all nodes and whether a node n is a consumer or plant node
                        (and if so, which building that node corresponds to), or neither.                   (2 x n)
    :param df_value: DataFrame of value of each substation
    :param flag: flag == True if the values are temperatures ; flag == False if the value is mass flow

    :return nodes_df: DataFrame with values at each node (1xn)
    :rtype nodes_df: DataFrame

    """

    nodes_df = pd.DataFrame()
    # write temperature into nodes DataFrame
    for node, row in all_nodes_df.iterrows():
        if row['Type'] == 'CONSUMER':
            nodes_df[node] = df_value[row['Building']]
        else:
            nodes_df[node] = np.nan  # set temperature value to nan for non-substation nodes

    return nodes_df


def read_properties_from_buildings(buildings_demands, property):
    """
    The function reads certain property from each building and output as a DataFrame.

    :param buildings_demands: demand of each building in the scenario
    :param property: certain property from the building demand file. e.g. T_supply_target

    :return property_df: DataFrame of the particular property at each building.
    :rtype property_df: DataFrame

    """

    property_df = pd.DataFrame(index=range(HOURS_IN_YEAR), columns=buildings_demands.keys())
    for name in buildings_demands.keys():
        property_per_building = buildings_demands[name][property]
        property_df[name] = property_per_building
    return property_df


# ============================
# test
# ============================


def main(config):
    """
    run the whole network summary routine
    """
    start = time.time()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    # add options for data sources: heating or cooling network, csv or shp
    network_type = config.thermal_network.network_type  # set to either 'DH' or 'DC'
    file_type = config.thermal_network.file_type  # set to csv or shp

    # this does a rule of max and min flow to set a diameter. if false it takes the input diameters
    set_diameter = config.thermal_network.set_diameter  # boolean
    network_names = config.thermal_network.network_names

    if network_type == 'DC':
        substation_cooling_systems = config.thermal_network.substation_cooling_systems  # list of cooling demand types supplied by network to substation
        substation_heating_systems = []
    else:
        substation_cooling_systems = []
        substation_heating_systems = config.thermal_network.substation_heating_systems  # list of heating demand types supplied by network to substation

    # combine into a dictionary to pass fewer arguments
    substation_systems = {'heating': substation_heating_systems, 'cooling': substation_cooling_systems}

    print('Running thermal_network for scenario %s' % config.scenario)
    print('Running thermal_network for network type %s' % network_type)
    print('Running thermal_network for file type %s' % file_type)
    print('Running thermal_network for networks %s' % network_names)
    if config.thermal_network_optimization.use_representative_week_per_month:
        print('Running thermal_network with representative week per month.')
    else:
        print('Running thermal_network with start-t %s' % config.thermal_network.start_t)
        print('Running thermal_network with stop-t %s' % config.thermal_network.stop_t)
    if network_type == 'DH':
        print('Running thermal_network with heating loads: %s' % substation_heating_systems)
    else:
        print('Running thermal_network with cooling loads: %s' % substation_cooling_systems)

    if len(network_names) == 0:
        network_names = ['']

    for network_name in network_names:
        thermal_network_main(locator, network_type, network_name, file_type, set_diameter, config, substation_systems)

    print('test thermal_network_main() succeeded')
    print('total time: ', time.time() - start)


if __name__ == '__main__':
    main(cea.config.Configuration())

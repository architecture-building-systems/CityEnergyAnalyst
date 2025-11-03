"""
Network Class:
defines the properties of a thermal network, including:
- Its layout (graph)
- The location of its substation
- The length of its segments
- The pipe types used for each of its segments
- The thermal losses incurred across the network
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2022, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"


import tempfile

import pandas as pd
import numpy as np
from geopandas import GeoDataFrame as Gdf
import networkx as nx
from networkx.algorithms.approximation.steinertree import steiner_tree
from shapely import LineString, Point
import wntr
import random

import cea.utilities
import cea.technologies.substation as substation
from cea.technologies.network_layout.steiner_spanning_tree import add_loops_to_network
from cea.optimization.preprocessing.preprocessing_main import get_building_names_with_load
from cea.technologies.network_layout.connectivity_potential import calc_connectivity_network
from cea.technologies.network_layout.utility import from_numpy_matrix
from cea.technologies.thermal_network.simplified_thermal_network import calculate_ground_temperature, \
    calc_linear_thermal_loss_coefficient, calc_thermal_loss_per_pipe, calc_max_diameter
from cea.constants import P_WATER_KGPERM3, FT_WATER_TO_PA, FT_TO_M, M_WATER_TO_PA, SHAPEFILE_TOLERANCE
from cea.technologies.constants import TYPE_MAT_DEFAULT, PIPE_DIAMETER_DEFAULT
from cea.optimization.constants import PUMP_ETA
from cea.optimization_new.building import Building
from cea.datamanagement.graph_helper import GraphCorrector

class Network(object):
    _coordinate_reference_system = None
    _domain_potential_network_graph = nx.Graph()
    _domain_potential_network_terminals_df = pd.DataFrame()
    _domain_buildings_flow_rate_m3pers = pd.DataFrame()
    _domain_buildings_supply_temp_K = pd.DataFrame()
    _domain_buildings_return_temp_K = pd.DataFrame()
    _domain_locator = None
    _pipe_catalog = pd.DataFrame()
    configuration_defaults = {'network_type': None,
                              'thermal_transfer_unit_design_head_m': 0.0,
                              'hazen_williams_friction_coefficient': 0.0,
                              'peak_load_velocity_ms': 0.0,
                              'equivalent_length_factor': 0.0,
                              'peak_load_percentage': 0.0,
                              'network_lifetime_yrs': 20}

    def __init__(self,  connected_buildings: list[str | Building], network_id: str):
        self.identifier = network_id
        self.connected_buildings = connected_buildings
        self.plant_terminal = None
        self.network_graph = nx.Graph()
        self.network_edges = Gdf()
        self.network_nodes = Gdf()
        self.network_piping = pd.DataFrame()
        self.network_losses = pd.Series()
        self.annual_piping_cost = 0.0

    @property
    def connected_buildings(self) -> list[str | Building]:
        return self._connected_buildings

    @connected_buildings.setter
    def connected_buildings(self, new_connected_buildings: list[str | Building]):
        """
        Sets the connected buildings for the network.

        param connected_buildings: list of building names or list of <Building>-objects
        """
        if all(isinstance(building, str) for building in new_connected_buildings):
            self._connected_buildings = new_connected_buildings
        elif all(isinstance(building, Building) for building in new_connected_buildings):
            self._connected_buildings = [building.identifier for building in new_connected_buildings]
        else:
            raise ValueError("connected_buildings must be a list of building names or Building-objects")

    @classmethod
    def build_network(cls, network_id, building_ids, connectivity, generate_dataframes=False):
        """
        Build a network for a given network_id and connectivity of the domain. This means creating a graph that connects
        all buildings in a designated network in the most efficient possible manner (i.e. Steiner tree).

        Factory method that creates and returns an instance of the calling class (supports subclassing).

        :param network_id: ID of the network to be built
        :type network_id: int
        :building_ids: list of building identifiers in the domain
        :type building_ids: list of str
        :connectivity: connectivity vector holding information about the network connections of the buildings
        :type connectivity: <ConnectivityVector>-object or list of <Connection>-objects
        :generate_dataframes: boolean indicator for whether dataframes with explicit information about graph nodes and
                              edges should be created
        :type generate_dataframes: bool
        """
        # identify the buildings in the domain that are connected to the network
        if isinstance(connectivity, list):
            buildings_are_connected_to_network = [connection.network_connection == network_id
                                                  for connection in connectivity]
        else:
            buildings_are_connected_to_network = [connection == network_id for connection in connectivity]
        connected_buildings = [building_id for [building_id, is_connected]
                               in zip(building_ids, buildings_are_connected_to_network)
                               if is_connected]

        # create a network identifier
        full_network_identifier = 'N' + str(1000 + network_id)

        # create the network object
        network = cls(connected_buildings, full_network_identifier)
        network.run_steiner_tree_optimisation(generate_graph_dataframes=generate_dataframes)

        return network

    def generate_condensed_graph(self, method:str='remove_connector_nodes'):
        """
        Generates a graph object with fewer intermediary nodes between the building nodes. The method dictates how
        the simplified graph is derived exactly.

        If 'method' = 'remove_connector_nodes':
            Nodes that are not part of the building nodes and have exactly two edges attached to them are removed from
            the network. The two edges are replaced by a single one, connecting the original nodes neighbours.
            This reduces node density in certain areas of the network while keeping the network structure intact.

        If 'method' = 'shortest_path_between_buildings':
            All connecting nodes are removed from the network and only the building nodes retained. Edges connect each
            building node in the domain to each other building node in the domain. Edge weights are equal to the
            shortest path between the two nodes in the detailed network.
            This removes all "unnecessary" nodes from the network, but also massively reduces information about the
            network structure.

        param method: str, method to simplify the network graph
        """
        # Generate the shortest network connecting the specified buildings, this network includes all relevant nodes of
        # the potential network graph (i.e. typically crossings in the roads network of the domain)
        detailed_network = self.run_steiner_tree_optimisation(generate_graph_dataframes=False)

        if method == 'remove_connector_nodes':

            condensed_graph = detailed_network.copy()

            # Remove all nodes with degree 2 from the detailed network
            while any(degree == 2 for _, degree in condensed_graph.degree):

                # Create a copy of the network that can be modified while iterating over the nodes
                # simply changing condensed_network itself would cause error `dictionary changed size during iteration`
                modifiable_graph = condensed_graph.copy()
                for node, degree in condensed_graph.degree():

                    if degree == 2:
                        # Get the two edges connected to the node
                        adjacent_edges = condensed_graph.edges(node)
                        adjacent_edges = list(adjacent_edges.__iter__())
                        node_0a, node_0b = adjacent_edges[0]
                        node_1a, node_1b = adjacent_edges[1]

                        # Get the nodes that are not the current node
                        node_0 = node_0a if node_0a != node else node_0b
                        node_1 = node_1a if node_1a != node else node_1b

                        # Calculate the new edge weight
                        edge_weight = condensed_graph[node][node_0]['weight'] \
                                      + condensed_graph[node][node_1]['weight']

                        # Remove the node and add the new edge
                        modifiable_graph.remove_node(node)
                        modifiable_graph.add_edge(node_0, node_1, weight=edge_weight)

                condensed_graph = modifiable_graph

        elif method == 'shortest_path_between_buildings':
            # Calculate the shortest paths between all nodes in the detailed network
            shortest_paths = dict(nx.all_pairs_dijkstra_path_length(detailed_network, weight='weight'))

            # Convert the shortest paths dictionary to a matrix
            nodes = [node for building, node
                    in zip(self._domain_potential_network_terminals_df['building'],
                           self._domain_potential_network_terminals_df['coordinates'])
                     if building in self.connected_buildings]
            node_labels = {node: i for i, node in enumerate(nodes)}
            shortest_path_matrix = np.zeros((len(nodes), len(nodes)))

            for i, start_node in enumerate(nodes):
                for j, end_node in enumerate(nodes):
                    shortest_path_matrix[i, j] = shortest_paths[start_node][end_node]

            # Generate a graph object from the shortest path matrix, this network only includes the relevant building nodes
            condensed_graph = from_numpy_matrix(shortest_path_matrix)
            nx.relabel_nodes(condensed_graph, node_labels, copy=False)
        else:
            raise ValueError("method for condensing the network structure must be either 'remove_connector_nodes' or "
                             "'shortest_path_between_buildings'")

        # Add the building names as labels to the nodes
        building_codes = self._domain_potential_network_terminals_df['building']
        building_coordinates = self._domain_potential_network_terminals_df['coordinates']
        building_nodes = {node: building_code for node, building_code in zip(building_coordinates, building_codes)}
        labels = {node: building_nodes[node] if node in building_nodes.keys() else 'connector'
                  for node in list(condensed_graph.nodes)}
        nx.set_node_attributes(condensed_graph, labels, 'label')

        return condensed_graph


    def run_steiner_tree_optimisation(self, generate_graph_dataframes=True):
        """
        Finds the shortest possible network for a given selection of connected buildings using the steiner tree
        optimisation algorithm.

        :param generate_graph_dataframes: indicator for whether the network graph dataframes should be generated
        :type generate_graph_dataframes: bool
        :type return_graph: bool
        """
        is_connected = self._domain_potential_network_terminals_df['building'].isin(self.connected_buildings).to_list()
        connected_terminals = self._domain_potential_network_terminals_df[is_connected]
        connected_terminal_coord = connected_terminals['coordinates'].tolist()

        # Validate graph is ready for Steiner tree with terminal nodes
        is_ready, message = GraphCorrector.validate_steiner_tree_ready(self._domain_potential_network_graph,
                                                                       connected_terminal_coord)
        if not is_ready:
            raise ValueError(f'Graph validation failed before Steiner tree: {message}. '
                           f'This should not happen after corrections in _load_pot_network(). '
                           f'Please report this issue.')

        # calculate steiner spanning tree of undirected potential_network_graph
        try:
            self.network_graph = nx.Graph(steiner_tree(self._domain_potential_network_graph, connected_terminal_coord))
            self.network_edges = Gdf([[LineString([edge_start, edge_end]), data.get('weight')]
                                      for edge_start, edge_end, data in self.network_graph.edges(data=True)],
                                     columns=['geometry', 'length_m'], crs=Network._coordinate_reference_system)
            self.network_nodes = Gdf([Point(node) for node in self.network_graph.nodes()],
                                     columns=['geometry'], crs=Network._coordinate_reference_system)
        except Exception as e:
            raise ValueError('There was an error while creating the Steiner tree despite graph corrections. '
                           'This is an unexpected error. Please report this issue.') from e

        # complete edge and node dataframes with connected terminals and domain buildings
        if generate_graph_dataframes:
            self.complete_graph_dataframes(connected_terminals)

        return self.network_graph

    def complete_graph_dataframes(self,  connected_terminals, allow_looped_networks=False):
        """
        Completes the edge and node dataframes with the connected terminals and domain buildings.

        :param connected_terminals: dataframe containing all connected terminals (buildings and plants)
        :type connected_terminals: pd.DataFrame
        :param allow_looped_networks: indicator for whether the network should close loops back where possible
        :type allow_looped_networks: bool
        """
        # extract the coordinates of the connected terminals (i.e. building nodes)
        connected_terminal_coord = connected_terminals['coordinates'].tolist()

        # build edge and node dataframes
        domain_buildings_list = self._domain_potential_network_terminals_df['building'].to_list()
        domain_buildings_coordinates_list = self._domain_potential_network_terminals_df['coordinates'].to_list()
        self._complete_graph_dataframes(connected_terminal_coord,
                                        domain_buildings_list,
                                        domain_buildings_coordinates_list)
        if self.plant_terminal is None:
            max_demand = connected_terminals['demand'].max()
            building_anchor = connected_terminals['building'][connected_terminals['demand'] == max_demand].iloc[0]
        else:
            building_anchor = self.plant_terminal
        self._set_plant_next_to_building(building_anchor)

        if allow_looped_networks:
            # add loops to the network by connecting None nodes that exist in the potential network
            self.network_edges, self.network_nodes = add_loops_to_network(self._domain_potential_network_graph,
                                                                          self.network_graph,
                                                                          self.network_edges,
                                                                          self.network_nodes,
                                                                          TYPE_MAT_DEFAULT,
                                                                          PIPE_DIAMETER_DEFAULT)
            # mst_edges.drop(['weight'], inplace=True, axis=1)

        return self.network_nodes, self.network_edges

    def calculate_operational_conditions(self, connectivity_string_for_files):
        """
        Calculate operational conditions for the network, i.e. mass flow rates for the network edges, pressure and
        thermal losses and derive the corresponding pipe types that need to be installed.

        Remark: This script is essentially a copy of the thermal_network_simplified functions from
                <cea.technologies.thermal_network.simplified_thermal_network>.
                Parameters that are not relevant for the optimisation have been removed.

        :return self.network_losses: total pressure and thermal losses across the network for each time step
        :rtype self.network_losses: pd.Series
        :return self.network_piping: aggregated length each pipe type installed in the network
        :rtype self.network_piping: pd.DataFrame
        """
        wnm_results, wnm_pipe_diameters = self._run_water_network_model(connectivity_string_for_files)

        # read pressure/hear losses per time-step for each pipe...
        # ...at the pipes
        unitary_head_loss_supply_network_ftperkft = wnm_results.link['headloss'].abs()
        linear_pressure_loss_Paperm = unitary_head_loss_supply_network_ftperkft * FT_WATER_TO_PA / (FT_TO_M * 1000)
        head_loss_supply_network_Pa = linear_pressure_loss_Paperm.copy()
        for column in head_loss_supply_network_Pa.columns.values:
            length_m = self.network_edges.loc[column]['length_m']
            head_loss_supply_network_Pa[column] = head_loss_supply_network_Pa[column] * length_m

        # ...at the substations
        consumer_nodes = self.network_nodes[self.network_nodes['type'] == 'CONSUMER'].index.to_list()
        head_loss_substations_ft = wnm_results.node['head'][consumer_nodes].abs()
        head_loss_substations_Pa = head_loss_substations_ft * FT_WATER_TO_PA

        # read mass flow rates for each pipe
        flow_rate_supply_m3s = wnm_results.link['flowrate'].abs()
        massflow_supply_kgs = flow_rate_supply_m3s * P_WATER_KGPERM3

        # derive thermal losses from mass flow, thermal insulation and ground temperature for...
        # ... the supply pipes
        pipe_names = self.network_edges.index.values
        thermal_losses_supply_kWh = wnm_results.link['headloss'].copy()
        thermal_losses_supply_kWh.reset_index(inplace=True, drop=True)
        temperature_of_the_ground_K = calculate_ground_temperature(self._domain_locator)
        thermal_coefficient_WperKm = pd.Series(
            np.vectorize(calc_linear_thermal_loss_coefficient)(wnm_pipe_diameters['D_ext_m'],
                                                               wnm_pipe_diameters['D_int_m'],
                                                               wnm_pipe_diameters['D_ins_m']),
            pipe_names)
        average_temperature_supply_K = self._domain_buildings_supply_temp_K[self.connected_buildings].mean(axis=1)
        for pipe in pipe_names:
            length_m = self.network_edges.loc[pipe]['length_m']
            massflow_kgs = massflow_supply_kgs[pipe]
            k_WperKm_pipe = thermal_coefficient_WperKm[pipe]
            k_kWperK = k_WperKm_pipe * length_m / 1000
            thermal_losses_supply_kWh[pipe] = np.vectorize(calc_thermal_loss_per_pipe)(
                average_temperature_supply_K.values,
                massflow_kgs.values,
                temperature_of_the_ground_K,
                k_kWperK,
            )
        # ... the return pipes
        average_temperature_return_K = self._domain_buildings_return_temp_K[self.connected_buildings].mean(axis=1)
        thermal_losses_return_kWh = wnm_results.link['headloss'].copy()
        thermal_losses_return_kWh.reset_index(inplace=True, drop=True)
        for pipe in pipe_names:
            length_m = self.network_edges.loc[pipe]['length_m']
            massflow_kgs = massflow_supply_kgs[pipe]
            k_WperKm_pipe = thermal_coefficient_WperKm[pipe]
            k_kWperK = k_WperKm_pipe * length_m / 1000
            thermal_losses_return_kWh[pipe] = np.vectorize(calc_thermal_loss_per_pipe)(
                average_temperature_return_K.values,
                massflow_kgs.values,
                temperature_of_the_ground_K,
                k_kWperK,
            )

        # accumulate pressure across the network for each timestep
        flow_rate_substations_m3s = wnm_results.node['demand'][consumer_nodes].abs()
        pressure_loss_supply_edge_kW = (head_loss_supply_network_Pa * (flow_rate_supply_m3s * 3600)) / (
                3.6E6 * PUMP_ETA)
        head_loss_return_kW = pressure_loss_supply_edge_kW.copy()
        head_loss_substations_kW = (head_loss_substations_Pa * (flow_rate_substations_m3s * 3600)) / (3.6E6 * PUMP_ETA)
        accumulated_head_loss_supply_kW = pressure_loss_supply_edge_kW.sum(axis=1)
        accumulated_head_loss_return_kW = head_loss_return_kW.sum(axis=1)
        accumulated_head_loss_substations_kW = head_loss_substations_kW.sum(axis=1)
        accumulated_head_loss_total_kW = accumulated_head_loss_supply_kW + \
                                         accumulated_head_loss_return_kW + \
                                         accumulated_head_loss_substations_kW

        # calculate total network losses (2 x thermal losses of supply to account for return pipes)
        self.network_losses = thermal_losses_supply_kWh.sum(axis=1) * 2 - accumulated_head_loss_total_kW.values

        # aggregate network piping information
        self.network_piping = self.network_edges[['type_mat', 'pipe_DN']].drop_duplicates()
        self.network_piping.reset_index(inplace=True, drop=True)
        self.network_piping['length_m'] = 0.0
        for index, pipe_type in self.network_piping.iterrows():
            using_type = self.network_edges.apply(lambda row: row['type_mat'] == pipe_type['type_mat'] and
                                                              row['pipe_DN'] == pipe_type['pipe_DN'], axis=1)
            self.network_piping['length_m'][index] = self.network_edges['length_m'][using_type].sum()
        self._calculate_piping_cost()

        return self.network_losses, self.network_piping

    @classmethod
    def initialize_class_variables(cls, domain):
        # Clear class variables before reinitializing to prevent state persistence across runs
        cls._domain_potential_network_graph = nx.Graph()
        cls._domain_potential_network_terminals_df = pd.DataFrame()
        cls._domain_buildings_flow_rate_m3pers = pd.DataFrame()
        cls._domain_buildings_supply_temp_K = pd.DataFrame()
        cls._domain_buildings_return_temp_K = pd.DataFrame()

        cls._configure_network_defaults(domain)
        cls._load_pot_network(domain)
        cls._set_potential_network_terminals(domain)
        cls._set_building_operation_parameters(domain)
        cls._pipe_catalog = pd.read_csv(cls._domain_locator.get_database_components_distribution_thermal_grid('THERMAL_GRID'))

    @classmethod
    def _load_pot_network(cls, domain):
        """
        Create potential network graph based on streets network .shp-file and the location of the buildings in the
        domain.

        :return domain.potential_network_graph: Graph of potential network paths including roads and links to buildings.
        :rtype domain.potential_network_graph: <networkx.Graph>-object
        """
        if not domain.buildings:
            return nx.Graph()

        # join building locations (shapely.POINTS) and the corresponding identifiers in a DataFrame
        building_identifiers = [building.identifier for building in domain.buildings]
        building_locations = [building.location for building in domain.buildings]
        buildings_df = Gdf(list(zip(building_locations, building_identifiers)), columns=['geometry', 'name'],
                           crs=domain.buildings[0].crs, geometry="geometry")
        
        streets_network_df = Gdf.from_file(domain.locator.get_street_network())

        # create a potential network grid with orthogonal connections between buildings and their closest street
        network_grid_shp = calc_connectivity_network(streets_network_df, buildings_df)

        # store projected coordinate reference system of network
        cls._coordinate_reference_system = network_grid_shp.crs

        # convert the GeoDataFrame network grid to a Graph
        for (line_string, length) in network_grid_shp.itertuples(index=False):
            line_start = line_string.coords[0]
            line_end = line_string.coords[-1]
            edge_start = (round(line_start[0], SHAPEFILE_TOLERANCE), round(line_start[1], SHAPEFILE_TOLERANCE))
            edge_end = (round(line_end[0], SHAPEFILE_TOLERANCE), round(line_end[1], SHAPEFILE_TOLERANCE))
            cls._domain_potential_network_graph.add_edge(edge_start, edge_end, weight=length)

        # FIXME: Use node property instead of building terminal coordinates to identify "protected" nodes. This would prevent rounding issues.
        # Extract transformed building terminal coordinates with proper rounding
        building_terminal_nodes = [
            (
                round(node.coords[0][0], SHAPEFILE_TOLERANCE),
                round(node.coords[0][1], SHAPEFILE_TOLERANCE),
            )
            for node in buildings_df.geometry
        ]

        # Apply graph corrections to fix connectivity issues
        # Pass building terminals as protected nodes so they are not merged
        print("\nApplying graph corrections to domain potential network...")
        corrector = GraphCorrector(cls._domain_potential_network_graph, protected_nodes=building_terminal_nodes)

        cls._domain_potential_network_graph = corrector.apply_corrections()

        return cls._domain_potential_network_graph

    @staticmethod
    def identify_overlapping_networks(network_graphs):
        """
        Identify overlapping networks from a given set of network graphs.

        :param network_graphs: A dictionary of network graphs.
        :type network_graphs: dict of networkx.Graph objects with network IDs as keys.
        """
        overlapping_networks = {}
        for network_id_1, network_graph_1 in network_graphs.items():
            overlaps = {}
            for network_id_2, network_graph_2 in network_graphs.items():
                if network_id_1 != network_id_2:
                    overlapping_nodes = set(network_graph_1.nodes()).intersection(
                        set(network_graph_2.nodes()))
                    if overlapping_nodes:
                        overlaps[network_id_2] = overlapping_nodes
            if overlaps:
                overlapping_networks[network_id_1] = overlaps
        return overlapping_networks

    @staticmethod
    def merge_networks(network_graphs, network_to_retain, networks_to_merge):
        """
        Merge networks into a single network. This method is set up for overlapping networks only and would
        need to be modified for merging non-overlapping networks.

        :param network_graphs: A dictionary of network graphs.
        :type network_graphs: dict of networkx.Graph objects with network IDs as keys.
        :param network_to_retain: The network ID to retain after merging.
        :type network_to_retain: str
        :param networks_to_merge: The network IDs to merge into the retained network.
        :type networks_to_merge: list of str
        """
        for network_to_merge in networks_to_merge:
            merged_network_graph = nx.compose(network_graphs[network_to_retain],
                                              network_graphs[network_to_merge])
            network_graphs[network_to_retain] = merged_network_graph
            network_graphs.pop(network_to_merge)

        return network_graphs

    @staticmethod
    def delete_networks(network_graphs, networks_to_delete):
        """
        Delete networks from a dictionary of network graphs.

        :param network_graphs: A dictionary of network graphs.
        :type network_graphs: dict of networkx.Graph objects with network IDs as keys.
        :param networks_to_delete: The network IDs to delete.
        :type networks_to_delete: list of str
        """
        for network_to_delete in networks_to_delete:
            network_graphs.pop(network_to_delete)

        return network_graphs

    @staticmethod
    def cut_networks_on_overlap(network_graphs, overlapping_networks, network_to_retain, building_nodes):
        """
        Based on a given group of network-graphs, cut all but the designated network wherever they overlap with the
        designated network. After the cuts have been done select a random subgraph from the cut networks to retain.

        Before the selection of subgraphs, if a given subgraph contains none or only a single building node, the
        subgraph is preemptively discarded.

        :param network_graphs: A dictionary of network graphs.
        :type network_graphs: dict of networkx.Graph objects with network IDs as keys.
        :param overlapping_networks: A dictionary listing which networks overlap with which and in which nodes.
        :type overlapping_networks: dict of dicts - {network_id: {network_id: [overlapping_nodes]}}
        :param network_to_retain: The network ID to retain after cutting.
        :type network_to_retain: str
        :param building_nodes: A dictionary of building nodes.
        :type building_nodes: dict of {node_id: building_id}
        """
        # Identify the networks that need to be cut
        networks_to_cut = list(overlapping_networks[network_to_retain].keys())

        # For each network to cut:
        for network_to_cut in networks_to_cut:
            network_graph_copy = network_graphs[network_to_cut].copy()

            # i. remove the overlapping nodes
            network_graph_copy.remove_nodes_from(overlapping_networks[network_to_retain][network_to_cut])

            # ii. identify the subgraphs that remain after the cut
            components = nx.connected_components(network_graph_copy)
            subgraphs = []
            for component in components:
                subgraph = network_graphs[network_to_cut].subgraph(component).copy()
                building_nodes_in_subgraph = set(building_nodes.keys()).intersection(
                    set(subgraph.nodes()))
                # iii. eliminate subgraphs with no or only one building node
                if len(building_nodes_in_subgraph) >= 2:
                    subgraphs.append(subgraph)

            # and iv. select a random subgraph to retain
            if subgraphs:
                network_graphs[network_to_cut] = random.choice(subgraphs)
            else:
                network_graphs.pop(network_to_cut)

        return network_graphs

    @classmethod
    def _configure_network_defaults(cls, domain):
        """
        Gets the network related configurations from the domain's configs and stores them in class variables
        (accessible by all instances).
        """
        if (domain is None) & (None in cls.configuration_defaults):
            raise ValueError("The network calculation needs configuration before it can analyse any networks.")
        elif domain is not None:
            cls._domain_locator = domain.locator
            network_type = domain.config.optimization_new.network_type
            min_head_substation_kPa = domain.config.optimization_new.min_head_substation
            thermal_transfer_unit_design_head_m = min_head_substation_kPa * 1000 / M_WATER_TO_PA
            hazen_williams_friction_coefficient = domain.config.optimization_new.hw_friction_coefficient
            peak_load_velocity_ms = domain.config.optimization_new.peak_load_velocity
            equivalent_length_factor = domain.config.optimization_new.equivalent_length_factor
            peak_load_percentage = domain.config.optimization_new.peak_load_percentage
            network_lifetime = domain.config.optimization_new.network_lifetime
            cls.configuration_defaults = {'network_type': network_type,
                                          'thermal_transfer_unit_design_head_m': thermal_transfer_unit_design_head_m,
                                          'hazen_williams_friction_coefficient': hazen_williams_friction_coefficient,
                                          'peak_load_velocity_ms': peak_load_velocity_ms,
                                          'equivalent_length_factor': equivalent_length_factor,
                                          'peak_load_percentage': peak_load_percentage,
                                          'network_lifetime_yrs': network_lifetime}

    @classmethod
    def _set_potential_network_terminals(cls, domain):
        """
        Gets the potential network graph from domain and stores the important information in class variables
        (accessible by all instances).
        """
        if (domain is None) & (nx.is_empty(cls._domain_potential_network_graph)):
            raise ValueError("The network object requires a potential network graph for the domain to be set.")
        elif domain is not None:
            # Extract building terminal coordinates with proper rounding
            # (already in correct CRS since network CRS = buildings CRS from _load_pot_network)
            network_terminal_coordinates = [
                (
                    round(building.location.coords[0][0], SHAPEFILE_TOLERANCE),
                    round(building.location.coords[0][1], SHAPEFILE_TOLERANCE),
                )
                for building in domain.buildings
            ]
            network_terminal_identifier = [building.identifier for building in domain.buildings]
            network_terminal_demand = [building.demand_flow.profile.sum() for building in domain.buildings]
            cls._domain_potential_network_terminals_df = pd.DataFrame(list(zip(network_terminal_identifier,
                                                                                   network_terminal_coordinates,
                                                                                   network_terminal_demand)),
                                                                          columns=['building', 'coordinates', 'demand'])

    @classmethod
    def _set_building_operation_parameters(cls, domain):
        """
        Calculates required mass flow rate and supply temperatures (+return temperature) for each building in the domain
        and stores this information in class variables (accessible by all instances).
        """
        if (domain is None) and (any([cls._domain_buildings_flow_rate_m3pers.empty,
                                      cls._domain_buildings_supply_temp_K.empty,
                                      cls._domain_buildings_return_temp_K.empty])):
            raise ValueError("The supply and return temperatures as well as the mass flows required by each building "
                             "need to be calculates before analysing any possible network options.")
        elif domain is not None:

            # GET INFORMATION ABOUT THE DEMAND OF BUILDINGS AND CONNECT TO THE NODE INFO
            # calculate substations for all buildings
            # local variables
            total_demand = pd.read_csv(cls._domain_locator.get_total_demand())
            network_type = domain.config.optimization_new.network_type

            if network_type == "DH":
                buildings_name_with_heating = get_building_names_with_load(total_demand, load_name='QH_sys_MWhyr')
                buildings_name_with_space_heating = get_building_names_with_load(total_demand,
                                                                                 load_name='Qhs_sys_MWhyr')
                if buildings_name_with_heating and buildings_name_with_space_heating:
                    building_names = [building for building in buildings_name_with_heating]
                    substation.substation_main_heating(cls._domain_locator, total_demand, building_names,
                                                       DHN_barcode="0")
                else:
                    raise Exception('There is no heating demand from any building. Please check the input files.')

                for building_name in building_names:
                    substation_results = pd.read_csv(
                        cls._domain_locator.get_optimization_substations_results_file(building_name, "DH", "0"))
                    cls._domain_buildings_flow_rate_m3pers[building_name] = \
                        substation_results["mdot_DH_result_kgpers"] / P_WATER_KGPERM3
                    cls._domain_buildings_supply_temp_K[building_name] = substation_results["T_supply_DH_result_K"]
                    cls._domain_buildings_return_temp_K[building_name] = \
                        np.where(substation_results["T_return_DH_result_K"] > 273.15,
                                 substation_results["T_return_DH_result_K"], np.nan)

            if network_type == "DC":
                buildings_name_with_cooling = get_building_names_with_load(total_demand, load_name='QC_sys_MWhyr')
                if buildings_name_with_cooling:
                    building_names = [building for building in buildings_name_with_cooling]
                    substation.substation_main_cooling(cls._domain_locator, total_demand, building_names,
                                                       DCN_barcode="0")
                else:
                    raise Exception('There is no cooling demand for any building. Please check the input files.')

                for building_name in building_names:
                    substation_results = pd.read_csv(
                        cls._domain_locator.get_optimization_substations_results_file(building_name, "DC", "0"))
                    cls._domain_buildings_flow_rate_m3pers[building_name] = \
                        substation_results[
                            "mdot_space_cooling_data_center_and_refrigeration_result_kgpers"] / P_WATER_KGPERM3
                    cls._domain_buildings_supply_temp_K[building_name] = \
                        substation_results["T_supply_DC_space_cooling_data_center_and_refrigeration_result_K"]
                    cls._domain_buildings_return_temp_K[building_name] = \
                        substation_results["T_return_DC_space_cooling_data_center_and_refrigeration_result_K"]

    def _complete_graph_dataframes(self, connected_buildings_coords_list, buildings_list, building_coordinates_list):
        """
        Complete the GeoDataFrames of the graph's edges and nodes, so that they can be used for the calculation of the
        thermal network operation (simplified_thermal_network.py).

        :return self.network_edges: GeoDataFrame structure for thermal network edges.
                                    ['geometry', 'length', 'type_mat'(dummy), 'pipe_DN'(dummy), 'start_node', 'end_node']
                                    index: PIPEi
        :return self.network_nodes: GeoDataFrame structure for nodes of the thermal network.
                                    ['geometry', 'coordinates', 'building', 'type']
                                    index: NODEi
        """
        def populate_fields(coordinate):
            if coordinate in connected_buildings_coords_list:
                return buildings_list[building_coordinates_list.index(coordinate)]
            else:
                return "NONE"

        self.network_nodes['coordinates'] = self.network_nodes['geometry'].apply(
            lambda x: (x.coords[0][0], x.coords[0][1]))
        self.network_nodes['building'] = self.network_nodes['coordinates'].apply(lambda x: populate_fields(x))
        self.network_nodes['type'] = self.network_nodes['building'].apply(
            lambda x: 'CONSUMER' if x != "NONE" else "NONE")
        self.network_nodes = self.network_nodes.rename(index=lambda x: "NODE" + str(x))

        # do some checks to see that the building names was not compromised
        if len(connected_buildings_coords_list) != (len(self.network_nodes['building'].unique()) - 1):
            raise ValueError('There was an error while populating the nodes fields. '
                             'One or more buildings could not be matched to nodes of the network. '
                             'Try changing the constant SNAP_TOLERANCE in cea/constants.py to try to fix this')

        # POPULATE FIELDS IN EDGES
        self.network_edges.loc[:, 'type_mat'] = TYPE_MAT_DEFAULT
        self.network_edges.loc[:, 'pipe_DN'] = PIPE_DIAMETER_DEFAULT
        self.network_edges = self.network_edges.rename(index=lambda x: "PIPE" + str(x))
        # assign edge properties
        self.network_edges['start node'] = ''
        self.network_edges['end node'] = ''

        for pipe, row in self.network_edges.iterrows():
            # get the length of the pipe and add to dataframe
            edge_coords = row['geometry'].coords
            start_node = (round(edge_coords[0][0], SHAPEFILE_TOLERANCE), round(edge_coords[0][1], SHAPEFILE_TOLERANCE))
            end_node = (round(edge_coords[1][0], SHAPEFILE_TOLERANCE), round(edge_coords[1][1], SHAPEFILE_TOLERANCE))
            try:
                self.network_edges.loc[pipe, 'start node'] = \
                    self.network_nodes[self.network_nodes['coordinates'] == start_node].index[0]
            except IndexError:
                print(f"The start node of {pipe} has no match in node_dict, check precision of the coordinates.")
            try:
                self.network_edges.loc[pipe, 'end node'] = \
                    self.network_nodes[self.network_nodes['coordinates'] == end_node].index[0]
            except IndexError:
                print(f"The end node of {pipe} has no match in node_dict, check precision of the coordinates.")

    def _set_plant_next_to_building(self, anchor_building):
        """
        Finds the street node through which the anchor building is connected with the network and creates a new plant
        node next to that street node (offset by +1m horizontally and +1m vertically in the current CRS)
        and adds it to the network along with the edge connecting the plant node to the street node.

        :param anchor_building: name of the chosen anchor building
        :type anchor_building: str (e.g. 'B1022')
        """
        # create new node
        building_node = self.network_nodes[self.network_nodes['building'] == anchor_building].index[0]
        network_connection = self.network_edges[self.network_edges['start node'] == building_node]
        if network_connection.empty:
            network_connection = self.network_edges[self.network_edges['end node'] == building_node]
            network_anchor_node = network_connection['start node'][0]
        else:
            network_anchor_node = network_connection['end node'][0]

        network_anchor = self.network_nodes[self.network_nodes.index == network_anchor_node]
        plant_terminal = network_anchor.copy()
        plant_terminal['geometry'] = network_anchor.translate(xoff=1, yoff=1)
        plant_terminal['coordinates'][0] = (plant_terminal.geometry[0].x, plant_terminal.geometry[0].y)
        plant_terminal_node = "NODE" + str(len(self.network_nodes.index))
        plant_terminal = plant_terminal.rename({plant_terminal.index[0]: plant_terminal_node})
        plant_terminal['type'][0] = "PLANT"

        self.network_nodes = pd.concat([self.network_nodes, plant_terminal])

        # create new edge
        point1 = (plant_terminal.geometry[0].x, plant_terminal.geometry[0].y)
        point2 = (network_anchor.geometry[0].x, network_anchor.geometry[0].y)
        line = LineString((point1, point2))
        plant_to_network = Gdf({'geometry': line, 'length_m': line.length, 'type_mat': TYPE_MAT_DEFAULT,
                                'pipe_DN': PIPE_DIAMETER_DEFAULT, 'start node': network_anchor_node,
                                'end node': plant_terminal_node},
                               index=['PIPE' + str(len(self.network_edges.index))],
                               crs=Network._coordinate_reference_system)
        self.network_edges = pd.concat([self.network_edges, plant_to_network])

    def _run_water_network_model(self, connectivity_string_for_files):
        """
        Run an epanet simulation by:
        I.  Use the information on the network's edges, nodes and required flow rates to set up an epanet water network.
        II. Simulate steady state operating conditions in three steps:
            1. run simulation to get flow rates through each pipe
            2. change pipe diameters according to flow rates and rerun the simulation
            3. calculate head losses across the network for each time step and force them on the plant node, effectively
               simulating a hydraulic pump at the plant. Then rerun the simulation.

        :return wnm_results: epanet water network model results
        :rtype wnm_results: <wntr.sim.results.SimulationResults>-object
        :return wnm_pipe_diameters: interior, exterior and insulation diameters of the network pipes
        :rtype wnm_pipe_diameters: pd.DataFrame
        """
        # BUILD WATER NETWORK
        # thermal_network_folder = self._domain_locator.get_thermal_network_folder()

        # Change working directory to temporary directory for wntr simulation
        with tempfile.TemporaryDirectory() as tmpdir, cea.utilities.pushd(tmpdir):
            # Create a water network model instance
            wn = wntr.network.WaterNetworkModel()

            # add loads
            building_base_demand_m3s = {}
            demand_pattern_map = {}

            def generate_demand_pattern(building_name: str) -> str:
                """
                Epanet demand patterns cannot have spaces and ?(has a 30-character limit).
                Otherwise, simulation will throw "EPANET 200" error.

                Returns a hash to create a unique code based on the building name
                Stores mapping to building name in demand_pattern_map
                """
                import hashlib
                _hash = hashlib.sha1(building_name.encode()).hexdigest()[:30]
                demand_pattern_map[_hash] = building_name
                return _hash

            for building in self.connected_buildings:
                # Make sure that building names have no whitespaces when adding demand pattern to wn
                demand_pattern = generate_demand_pattern(building)
                building_base_demand_m3s[demand_pattern] = self._domain_buildings_flow_rate_m3pers[building].max()
                pattern_demand = (self._domain_buildings_flow_rate_m3pers[building].values /
                                  building_base_demand_m3s[demand_pattern]).tolist()
                wn.add_pattern(demand_pattern, pattern_demand)

            # add nodes
            consumer_nodes = []
            for node_name, node in self.network_nodes.iterrows():
                if node["type"] == "CONSUMER":
                    demand_pattern = generate_demand_pattern(node['building'])
                    base_demand_m3s = building_base_demand_m3s[demand_pattern]
                    consumer_nodes.append(node_name)
                    wn.add_junction(str(node_name),
                                    base_demand=base_demand_m3s,
                                    demand_pattern=demand_pattern,
                                    elevation=self.configuration_defaults['thermal_transfer_unit_design_head_m'],
                                    coordinates=node["coordinates"])
                elif node["type"] == "PLANT":
                    base_head = int(self.configuration_defaults['thermal_transfer_unit_design_head_m'] * 1.2)
                    start_node = str(node_name)
                    name_node_plant = start_node
                    wn.add_reservoir(start_node,
                                     base_head=base_head,
                                     coordinates=node["coordinates"])
                else:
                    wn.add_junction(str(node_name),
                                    elevation=0,
                                    coordinates=node["coordinates"])

            # add pipes
            for edge_name, edge in self.network_edges.iterrows():
                length_m = edge["length_m"]
                wn.add_pipe(str(edge_name), edge["start node"],
                            edge["end node"],
                            length=length_m * (1 + self.configuration_defaults['equivalent_length_factor']),
                            roughness=self.configuration_defaults['hazen_williams_friction_coefficient'],
                            minor_loss=0.0,
                            initial_status='OPEN')

            # add options
            nbr_time_steps = len(self._domain_buildings_flow_rate_m3pers)
            wn.options.time.duration = (nbr_time_steps - 1) * 3600  # this indicates epanet to do one year simulation
            wn.options.time.hydraulic_timestep = 60 * 60
            wn.options.time.pattern_timestep = 60 * 60
            wn.options.hydraulic.accuracy = 0.01
            wn.options.hydraulic.trials = 100

            # RUN WATER NETWORK SIMULATIONS
            # 1st ITERATION GET MASS FLOWS AND CALCULATE DIAMETER
            sim = wntr.sim.EpanetSimulator(wn)
            wnm_results = sim.run_sim()
            max_volume_flow_rates_m3s = wnm_results.link['flowrate'].abs().max()
            pipe_names = max_volume_flow_rates_m3s.index.values
            pipe_DN, D_ext_m, D_int_m, D_ins_m = zip(*[calc_max_diameter(flow, Network._pipe_catalog,
                                                                         velocity_ms=self.configuration_defaults[
                                                                             'peak_load_velocity_ms'],
                                                                         peak_load_percentage=
                                                                         self.configuration_defaults[
                                                                             'peak_load_percentage'])
                                                       for flow in max_volume_flow_rates_m3s])
            pipe_dn = pd.Series(pipe_DN, pipe_names)
            wnm_pipe_diameters = pd.DataFrame({'D_int_m': D_int_m, 'D_ext_m': D_ext_m, 'D_ins_m': D_ins_m},
                                              index=pipe_names)

            # 2nd ITERATION GET PRESSURE POINTS AND MASS FLOWS FOR SIZING PUMPING NEEDS - this could be for all the year
            # modify diameter and run simulations
            self.network_edges['pipe_DN'] = pipe_dn
            self.network_edges['D_int_m'] = D_int_m
            for edge_name, edge in self.network_edges.iterrows():
                pipe = wn.get_link(str(edge_name))
                pipe.diameter = wnm_pipe_diameters['D_int_m'][edge_name]
            sim = wntr.sim.EpanetSimulator(wn)
            wnm_results = sim.run_sim()

            # 3rd ITERATION GET FINAL UTILIZATION OF THE GRID (SUPPLY SIDE)
            # get accumulated head loss per hour
            unitary_head_ftperkft = wnm_results.link['headloss'].abs()
            unitary_head_mperm = unitary_head_ftperkft * FT_TO_M / (FT_TO_M * 1000)
            head_loss_m = unitary_head_mperm.copy()
            for column in head_loss_m.columns.values:
                length_m = self.network_edges.loc[column]['length_m']
                head_loss_m[column] = head_loss_m[column] * length_m
            reservoir_head_loss_m = head_loss_m.sum(axis=1) + \
                                    self.configuration_defaults[
                                        'thermal_transfer_unit_design_head_m'] * 1.2  # fixme: only one thermal_transfer_unit_design_head_m from one substation?
            # @lguilhermers, @shanshanhsieh --- please review the 3 lines above ---

            # apply this pattern to the reservoir and get results
            base_head = reservoir_head_loss_m.max()
            pattern_head_m = (reservoir_head_loss_m.values / base_head).tolist()
            wn.add_pattern('reservoir', pattern_head_m)
            reservoir = wn.get_node(name_node_plant)
            reservoir.head_timeseries.base_value = int(base_head)
            reservoir.head_timeseries._pattern = 'reservoir'
            sim = wntr.sim.EpanetSimulator(wn)
            wnm_results = sim.run_sim()

        return wnm_results, wnm_pipe_diameters

    def _calculate_piping_cost(self):
        """
        Calculate piping cost for a fully built network.
        """
        piping_unit_cost_dict = {pipe_type['pipe_DN']: pipe_type['Inv_USD2015perm']
                                 for ind, pipe_type in Network._pipe_catalog.iterrows()}
        piping_cost_aggregated = sum([piping_unit_cost_dict[pipe_segment['pipe_DN']] * pipe_segment['length_m']
                                      for ind, pipe_segment in self.network_piping.iterrows()])
        annualised_piping_cost = piping_cost_aggregated / self.configuration_defaults['network_lifetime_yrs']

        self.annual_piping_cost = annualised_piping_cost

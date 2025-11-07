"""
This script calculates the minimum spanning tree of a shapefile network
"""
import math
import os
from enum import StrEnum

import networkx as nx
import pandas as pd
from geopandas import GeoDataFrame as gdf
from networkx.algorithms.approximation.steinertree import steiner_tree
from shapely import LineString

from cea.constants import SHAPEFILE_TOLERANCE
from cea.technologies.network_layout.utility import read_shp, write_shp
from cea.datamanagement.graph_helper import GraphCorrector

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class SteinerAlgorithm(StrEnum):
    """
    Enum for the different algorithms that can be used to calculate the Steiner tree.

    This is based on the available algorithms for NetworkX Steiner tree function.
    Reference:
    https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.approximation.steinertree.steiner_tree.html
    """

    Kou = 'kou'
    """
    Kou algorithm: Higher quality Steiner tree approximation with better weight optimization.
    - Runtime: O(|S| |V|²) - slower for large networks
    - Memory: High consumption, can be excessive for large graphs
    - Quality: More optimal network layouts, better weight minimization
    - Use when: Network optimization quality is critical and computational resources are sufficient
    - Algorithm: Computes minimum spanning tree of the metric closure subgraph induced by terminal nodes
    """
    
    Mehlhorn = 'mehlhorn'
    """
    Mehlhorn algorithm: Fast Steiner tree approximation optimized for speed and memory efficiency.
    - Runtime: O(|E| + |V|log|V|) - very fast, scales well with network size
    - Memory: Minimal usage, suitable for large networks
    - Quality: Good approximation but sometimes noticeably suboptimal compared to Kou
    - Use when: Speed is prioritized over perfect optimization, or working with very large networks
    - Algorithm: Modified Kou approach that finds closest terminal node for each non-terminal first
    """

    def __str__(self):
        return self.value


def calc_steiner_spanning_tree(crs_projected,
                               temp_path_potential_network_shp,
                               output_network_folder,
                               temp_path_building_centroids_shp,
                               path_output_edges_shp,
                               path_output_nodes_shp,
                               weight_field,
                               type_mat_default,
                               pipe_diameter_default,
                               type_network,
                               total_demand_location,
                               allow_looped_networks,
                               optimization_flag,
                               plant_building_names,
                               disconnected_building_names,
                               method: str = SteinerAlgorithm.Kou):
    """
    Calculate the minimum spanning tree of the network. Note that this function can't be run in parallel in it's
    present form.

    :param str crs_projected: e.g. "+proj=utm +zone=48N +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
    :param str temp_path_potential_network_shp: e.g. "TEMP/potential_network.shp"
    :param str output_network_folder: "{general:scenario}/inputs/networks/DC"
    :param str temp_path_building_centroids_shp: e.g. "%TEMP%/nodes_buildings.shp"
    :param str path_output_edges_shp: "{general:scenario}/inputs/networks/DC/edges.shp"
    :param str path_output_nodes_shp: "{general:scenario}/inputs/networks/DC/nodes.shp"
    :param str weight_field: e.g. "Shape_Leng"
    :param str type_mat_default: e.g. "T1"
    :param float pipe_diameter_default: e.g. 150
    :param str type_network: "DC" or "DH"
    :param str total_demand_location: "{general:scenario}/outputs/data/demand/Total_demand.csv"
    :param bool create_plant: e.g. True
    :param bool allow_looped_networks:
    :param bool optimization_flag:
    :param List[str] plant_building_names: e.g. ``['B001']``
    :param List[str] disconnected_building_names: e.g. ``['B002', 'B010', 'B004', 'B005', 'B009']``
    :param method: The algorithm to use for calculating the Steiner tree. Default is Kou.
    :return: ``(mst_edges, mst_nodes)``
    """
    steiner_algorithm = SteinerAlgorithm(method)

    # TODO: Ensure CRS is used properly throughout the function (currently not applied)
    # read shapefile into networkx format into a directed potential_network_graph, this is the potential network
    potential_network_graph = read_shp(temp_path_potential_network_shp)
    building_nodes_graph = read_shp(temp_path_building_centroids_shp)

    if potential_network_graph is None or building_nodes_graph is None:
        raise ValueError('Could not read potential network or building centroids shapefiles. '
                         'Please check the files exist and are valid shapefiles.')

    # transform to an undirected potential_network_graph
    # Note: Graph corrections are now applied in calc_connectivity_network BEFORE
    # building terminals are connected, to ensure terminal nodes are not affected
    iterator_edges = potential_network_graph.edges(data=True)
    G = nx.Graph()
    for (x, y, data) in iterator_edges:
        x = (round(x[0], SHAPEFILE_TOLERANCE), round(x[1], SHAPEFILE_TOLERANCE))
        y = (round(y[0], SHAPEFILE_TOLERANCE), round(y[1], SHAPEFILE_TOLERANCE))
        G.add_edge(x, y, weight=data[weight_field])

    # get the building nodes and coordinates
    iterator_nodes = building_nodes_graph.nodes
    terminal_nodes_coordinates = []
    terminal_nodes_names = []
    for coordinates, data in iterator_nodes.data():
        building_name = data['name']
        if building_name in disconnected_building_names:
            print("Building {} is considered to be disconnected and it is not included".format(building_name))
        else:
            terminal_nodes_coordinates.append(
                (round(coordinates[0], SHAPEFILE_TOLERANCE), round(coordinates[1], SHAPEFILE_TOLERANCE)))
            terminal_nodes_names.append(data['name'])

    # Validate graph is ready for Steiner tree with terminal nodes
    is_ready, message = GraphCorrector.validate_steiner_tree_ready(G, terminal_nodes_coordinates)
    if not is_ready:
        raise ValueError(f'Graph validation failed before Steiner tree: {message}. '
                        f'This should not happen after corrections. Please report this issue.')

    # calculate steiner spanning tree of undirected potential_network_graph
    try:
        steiner_result = steiner_tree(G, terminal_nodes_coordinates, method=steiner_algorithm)
        mst_non_directed = nx.minimum_spanning_tree(steiner_result)
    except Exception as e:
        raise ValueError('There was an error while creating the Steiner tree despite graph corrections. '
                        'This is an unexpected error. Please report this issue with your streets.shp file.') from e

    # Ensure output folder exists before writing
    os.makedirs(output_network_folder, exist_ok=True)
    write_shp(mst_non_directed, output_network_folder)  # need to write to disk and then import again
    mst_nodes = gdf.from_file(path_output_nodes_shp)
    mst_edges = gdf.from_file(path_output_edges_shp)

    # POPULATE FIELDS IN NODES
    pointer_coordinates_building_names = dict(zip(terminal_nodes_coordinates, terminal_nodes_names))

    def populate_fields(coordinate):
        if coordinate in terminal_nodes_coordinates:
            return pointer_coordinates_building_names[coordinate]
        else:
            return "NONE"

    mst_nodes['coordinates'] = mst_nodes['geometry'].apply(
        lambda x: (round(x.coords[0][0], SHAPEFILE_TOLERANCE), round(x.coords[0][1], SHAPEFILE_TOLERANCE)))
    mst_nodes['building'] = mst_nodes['coordinates'].apply(lambda x: populate_fields(x))
    mst_nodes['name'] = mst_nodes['FID'].apply(lambda x: "NODE" + str(x))
    mst_nodes['type'] = mst_nodes['building'].apply(lambda x: 'CONSUMER' if x != "NONE" else "NONE")

    # do some checks to see that the building names was not compromised
    if len(terminal_nodes_names) != (len(mst_nodes['building'].unique()) - 1):
        raise ValueError('There was an error while populating the nodes fields. '
                         'One or more buildings could not be matched to nodes of the network. '
                         'Try changing the constant SNAP_TOLERANCE in cea/constants.py to try to fix this')

    # POPULATE FIELDS IN EDGES
    mst_edges.loc[:, 'type_mat'] = type_mat_default
    mst_edges.loc[:, 'pipe_DN'] = pipe_diameter_default
    mst_edges.loc[:, 'name'] = ["PIPE" + str(x) for x in mst_edges.index]

    if allow_looped_networks:
        # add loops to the network by connecting None nodes that exist in the potential network
        mst_edges, mst_nodes = add_loops_to_network(G,
                                                    mst_non_directed,
                                                    mst_nodes,
                                                    mst_edges,
                                                    type_mat_default,
                                                    pipe_diameter_default)
        # mst_edges.drop(['weight'], inplace=True, axis=1)

    if optimization_flag:
        for building in plant_building_names:
            building_anchor = building_node_from_name(building, mst_nodes)
            mst_nodes, mst_edges = add_plant_close_to_anchor(building_anchor, mst_nodes, mst_edges,
                                                             type_mat_default, pipe_diameter_default)
    elif os.path.exists(total_demand_location):
        if len(plant_building_names) > 0:
            building_anchor = mst_nodes[mst_nodes['building'].isin(plant_building_names)]
        else:
            building_anchor = calc_coord_anchor(total_demand_location, mst_nodes, type_network)
        mst_nodes, mst_edges = add_plant_close_to_anchor(building_anchor, mst_nodes, mst_edges,
                                                         type_mat_default, pipe_diameter_default)

    # GET COORDINATE AND SAVE FINAL VERSION TO DISK
    mst_edges.crs = crs_projected
    mst_nodes.crs = crs_projected
    mst_edges['length_m'] = mst_edges['weight']
    mst_edges[['geometry', 'length_m', 'type_mat', 'name', 'pipe_DN']].to_file(path_output_edges_shp,
                                                                               driver='ESRI Shapefile')
    mst_nodes[['geometry', 'building', 'name', 'type']].to_file(path_output_nodes_shp, driver='ESRI Shapefile')


def _get_missing_neighbours(node_coords, potential_graph: nx.Graph, steiner_graph: nx.Graph):
    """
    Find neighbours that exist in potential network but not in steiner network.

    :param node_coords: Coordinates of the node to check
    :param potential_graph: Full potential network graph
    :param steiner_graph: Current steiner tree graph
    :return: List of missing neighbour coordinates
    """
    potential_neighbours = set(potential_graph[node_coords].keys())
    steiner_neighbours = set(steiner_graph[node_coords].keys())
    return list(potential_neighbours - steiner_neighbours)


def _make_edge_key(coord1, coord2):
    """
    Create a unique edge key from two coordinates.
    Uses frozenset to make edges undirected (A->B == B->A).

    :param coord1: First coordinate tuple
    :param coord2: Second coordinate tuple
    :return: frozenset edge key
    """
    return frozenset([tuple(coord1), tuple(coord2)])


def _add_edge_to_network(mst_edges: gdf, start_coords, end_coords, pipe_dn, type_mat, existing_edges: set) -> gdf:
    """
    Add an edge to the network if it doesn't already exist.

    :param mst_edges: Current edges GeoDataFrame
    :param start_coords: Start point coordinates
    :param end_coords: End point coordinates
    :param pipe_dn: Pipe diameter
    :param type_mat: Pipe material type
    :param existing_edges: Set of existing edge keys (frozensets of coordinate tuples)
    :return: Updated edges GeoDataFrame
    """
    edge_key = _make_edge_key(start_coords, end_coords)

    if edge_key not in existing_edges:
        line = LineString((start_coords, end_coords))
        # Calculate weight from line length
        edge_weight = line.length
        new_edge = pd.DataFrame([{
            "geometry": line,
            "pipe_DN": pipe_dn,
            "type_mat": type_mat,
            "name": f"PIPE{mst_edges.name.count()}",
            "weight": edge_weight
        }])
        mst_edges = gdf(
            pd.concat([mst_edges, new_edge], ignore_index=True),
            crs=mst_edges.crs
        )
        # Add to existing edges set
        existing_edges.add(edge_key)

    return mst_edges


def add_loops_to_network(G: nx.Graph, mst_non_directed: nx.Graph, new_mst_nodes: gdf, mst_edges: gdf, type_mat, pipe_dn) -> tuple[gdf, gdf]:
    added_a_loop = False

    # Initialize set of existing edges from current mst_edges
    existing_edges = set()
    for geom in mst_edges.geometry:
        coords = list(geom.coords)
        if len(coords) >= 2:
            edge_key = _make_edge_key(coords[0], coords[-1])
            existing_edges.add(edge_key)

    # Filter to only NONE type nodes
    none_nodes = new_mst_nodes[new_mst_nodes['type'] == 'NONE']
    none_coords = set(tuple(row.coordinates) for row in none_nodes.itertuples())

    # Identify all NONE type nodes in the steiner tree
    for row in none_nodes.itertuples():
        node_coords = row.coordinates

        # Find neighbours missing from steiner network
        missing_neighbours = _get_missing_neighbours(node_coords, G, mst_non_directed)

        # Check if the missing neighbour is also a NONE type node
        for new_neighbour in missing_neighbours:
            if tuple(new_neighbour) in none_coords:
                # Add edge between the two NONE nodes
                mst_edges = _add_edge_to_network(mst_edges, node_coords, new_neighbour, pipe_dn, type_mat, existing_edges)
                added_a_loop = True
    
    if not added_a_loop:
        print('No first degree loop added. Trying two nodes apart.')

        # Rebuild sets in case new_mst_nodes was modified in first loop
        none_nodes = new_mst_nodes[new_mst_nodes['type'] == 'NONE']
        none_coords = set(tuple(row.coordinates) for row in none_nodes.itertuples())

        # Create set of all node coordinates (for checking if intermediate node exists)
        all_coords = set(tuple(row.coordinates) for row in new_mst_nodes.itertuples())

        # Identify all NONE type nodes in the steiner tree
        for row in none_nodes.itertuples():
            node_coords = row.coordinates

            # Find neighbours missing from steiner network
            missing_neighbours = _get_missing_neighbours(node_coords, G, mst_non_directed)

            # Check if missing neighbour does NOT exist in steiner (need to go two hops)
            for new_neighbour in missing_neighbours:
                if tuple(new_neighbour) not in all_coords:
                    # Find neighbours of that intermediate node (two hops away)
                    second_degree_pot_neigh = list(G[new_neighbour].keys())
                    for potential_second_deg_neighbour in second_degree_pot_neigh:
                        if potential_second_deg_neighbour != node_coords:
                            if tuple(potential_second_deg_neighbour) in none_coords:
                                # Add first edge (to intermediate node)
                                mst_edges = _add_edge_to_network(mst_edges, node_coords, new_neighbour, pipe_dn, type_mat, existing_edges)

                                # Add new intermediate node from potential network to steiner tree
                                copy_of_new_mst_nodes = new_mst_nodes.copy()
                                x_distance = new_neighbour[0] - node_coords[0]
                                y_distance = new_neighbour[1] - node_coords[1]
                                copy_of_new_mst_nodes.geometry = copy_of_new_mst_nodes.translate(
                                    xoff=x_distance, yoff=y_distance)
                                selected_node = copy_of_new_mst_nodes[
                                    copy_of_new_mst_nodes["coordinates"] == node_coords]
                                selected_node["name"] = "NODE" + str(new_mst_nodes.name.count())
                                selected_node["type"] = "NONE"
                                geom = selected_node.geometry.values[0]
                                normalized_coords = (round(geom.coords[0][0], SHAPEFILE_TOLERANCE),
                                                     round(geom.coords[0][1], SHAPEFILE_TOLERANCE))
                                selected_node["coordinates"] = normalized_coords
                                if normalized_coords not in all_coords:
                                    new_mst_nodes = gdf(
                                        pd.concat([new_mst_nodes, selected_node], ignore_index=True),
                                        crs=new_mst_nodes.crs
                                    )
                                    # Update all_coords set
                                    all_coords.add(normalized_coords)

                                # Add second edge (from intermediate to second degree neighbour)
                                mst_edges = _add_edge_to_network(mst_edges, new_neighbour, potential_second_deg_neighbour, pipe_dn, type_mat, existing_edges)
                                added_a_loop = True
    if not added_a_loop:
        print('No loops added.')
    return mst_edges, new_mst_nodes


def calc_coord_anchor(total_demand_location, nodes_df, type_network):
    total_demand = pd.read_csv(total_demand_location)
    nodes_names_demand = nodes_df.merge(total_demand, left_on="building", right_on="name", how="inner")
    if type_network == "DH":
        field = "QH_sys_MWhyr"
    elif type_network == "DC":
        field = "QC_sys_MWhyr"
    else:
        raise ValueError("Invalid value for variable 'type_network': {type_network}".format(type_network=type_network))

    max_value = nodes_names_demand[field].max()
    building_series = nodes_names_demand[nodes_names_demand[field] == max_value]

    return building_series


def building_node_from_name(building_name, nodes_df):
    building_series = nodes_df[nodes_df['building'] == building_name]
    return building_series


def add_plant_close_to_anchor(building_anchor, new_mst_nodes: gdf, mst_edges: gdf, type_mat, pipe_dn):
    # find closest node
    copy_of_new_mst_nodes = new_mst_nodes.copy()
    building_coordinates = building_anchor.geometry.values[0].coords
    x1 = building_coordinates[0][0]
    y1 = building_coordinates[0][1]
    delta = 10E24  # big number
    node_id = None

    for node in copy_of_new_mst_nodes.iterrows():
        if node[1]['type'] == 'NONE':
            x2 = node[1].geometry.coords[0][0]
            y2 = node[1].geometry.coords[0][1]
            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if 0 < distance < delta:
                delta = distance
                node_id = node[1]['name']

    if node_id is None:
        raise ValueError("Could not find closest node.")

    # create copy of selected node and add to list of all nodes
    copy_of_new_mst_nodes.geometry = copy_of_new_mst_nodes.translate(xoff=1, yoff=1)
    selected_node = copy_of_new_mst_nodes[copy_of_new_mst_nodes["name"] == node_id].iloc[[0]]
    selected_node["name"] = "NODE" + str(new_mst_nodes.name.count())
    selected_node["type"] = "PLANT"
    new_mst_nodes = gdf(
        pd.concat([new_mst_nodes, selected_node], ignore_index=True),
        crs=new_mst_nodes.crs
    )

    # create new edge
    point1 = (selected_node.iloc[0].geometry.x, selected_node.iloc[0].geometry.y)
    point2 = (new_mst_nodes[new_mst_nodes["name"] == node_id].iloc[0].geometry.x,
              new_mst_nodes[new_mst_nodes["name"] == node_id].iloc[0].geometry.y)
    line = LineString((point1, point2))
    edge_weight = line.length
    mst_edges = gdf(
        pd.concat(
            [mst_edges,
            pd.DataFrame([{"geometry": line, "pipe_DN": pipe_dn, "type_mat": type_mat,
                          "name": "PIPE" + str(mst_edges.name.count()), "weight": edge_weight}])],
            ignore_index=True
        ),
        crs=mst_edges.crs
    )
    return new_mst_nodes, mst_edges

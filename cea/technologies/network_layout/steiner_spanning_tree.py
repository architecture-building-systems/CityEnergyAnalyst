"""
This script calculates the minimum spanning tree of a shapefile network
"""




import math
import os

import networkx as nx
import pandas as pd
from geopandas import GeoDataFrame as gdf
from networkx.algorithms.approximation.steinertree import steiner_tree
from shapely.geometry import LineString
from typing import List

import cea.config
import cea.inputlocator
from cea.constants import SHAPEFILE_TOLERANCE

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


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
                               disconnected_building_names):
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
    :return: ``(mst_edges, mst_nodes)``
    """
    # read shapefile into networkx format into a directed potential_network_graph, this is the potential network
    potential_network_graph = nx.read_shp(temp_path_potential_network_shp)
    building_nodes_graph = nx.read_shp(temp_path_building_centroids_shp)

    # transform to an undirected potential_network_graph
    iterator_edges = potential_network_graph.edges(data=True)
    G = nx.Graph()
    for (x, y, data) in iterator_edges:
        x = (round(x[0], SHAPEFILE_TOLERANCE), round(x[1], SHAPEFILE_TOLERANCE))
        y = (round(y[0], SHAPEFILE_TOLERANCE), round(y[1], SHAPEFILE_TOLERANCE))
        G.add_edge(x, y, weight=data[weight_field])

    # get the building nodes and coordinates
    iterator_nodes = building_nodes_graph.nodes(data=True)
    terminal_nodes_coordinates = []
    terminal_nodes_names = []
    for coordinates, data in iterator_nodes._nodes.items():
        building_name = data['Name']
        if building_name in disconnected_building_names:
            print("Building {} is considered to be disconnected and it is not included".format(building_name))
        else:
            terminal_nodes_coordinates.append(
                (round(coordinates[0], SHAPEFILE_TOLERANCE), round(coordinates[1], SHAPEFILE_TOLERANCE)))
            terminal_nodes_names.append(data['Name'])

    # calculate steiner spanning tree of undirected potential_network_graph
    try:
        mst_non_directed = nx.Graph(steiner_tree(G, terminal_nodes_coordinates))
        nx.write_shp(mst_non_directed, output_network_folder)  # need to write to disk and then import again
        mst_nodes = gdf.from_file(path_output_nodes_shp)
        mst_edges = gdf.from_file(path_output_edges_shp)
    except:
        raise ValueError('There was an error while creating the Steiner tree. '
                         'Check the streets.shp for isolated/disconnected streets (lines) and erase them, '
                         'the Steiner tree does not support disconnected graphs. '
                         'If no disconnected streets can be found, try increasing the SHAPEFILE_TOLERANCE in cea.constants and run again. '
                         'Otherwise, try using the Feature to Line tool of ArcMap with a tolerance of around 10m to solve the issue.')

    # POPULATE FIELDS IN NODES
    pointer_coordinates_building_names = dict(zip(terminal_nodes_coordinates, terminal_nodes_names))

    def populate_fields(coordinate):
        if coordinate in terminal_nodes_coordinates:
            return pointer_coordinates_building_names[coordinate]
        else:
            return "NONE"

    mst_nodes['coordinates'] = mst_nodes['geometry'].apply(
        lambda x: (round(x.coords[0][0], SHAPEFILE_TOLERANCE), round(x.coords[0][1], SHAPEFILE_TOLERANCE)))
    mst_nodes['Building'] = mst_nodes['coordinates'].apply(lambda x: populate_fields(x))
    mst_nodes['Name'] = mst_nodes['FID'].apply(lambda x: "NODE" + str(x))
    mst_nodes['Type'] = mst_nodes['Building'].apply(lambda x: 'CONSUMER' if x != "NONE" else "NONE")

    # do some checks to see that the building names was not compromised
    if len(terminal_nodes_names) != (len(mst_nodes['Building'].unique()) - 1):
        raise ValueError('There was an error while populating the nodes fields. '
                         'One or more buildings could not be matched to nodes of the network. '
                         'Try changing the constant SNAP_TOLERANCE in cea/constants.py to try to fix this')

    # POPULATE FIELDS IN EDGES
    mst_edges.loc[:, 'Type_mat'] = type_mat_default
    mst_edges.loc[:, 'Pipe_DN'] = pipe_diameter_default
    mst_edges.loc[:, 'Name'] = ["PIPE" + str(x) for x in mst_edges.index]

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
        building_anchor = calc_coord_anchor(total_demand_location, mst_nodes, type_network)
        mst_nodes, mst_edges = add_plant_close_to_anchor(building_anchor, mst_nodes, mst_edges,
                                                         type_mat_default, pipe_diameter_default)

    # GET COORDINATE AND SAVE FINAL VERSION TO DISK
    print(crs_projected)
    mst_edges.crs = crs_projected
    mst_nodes.crs = crs_projected
    mst_edges['length_m'] = mst_edges['weight']
    mst_edges[['geometry','length_m', 'Type_mat', 'Name', 'Pipe_DN']].to_file(path_output_edges_shp, driver='ESRI Shapefile')
    mst_nodes[['geometry', 'Building', 'Name', 'Type']].to_file(path_output_nodes_shp, driver='ESRI Shapefile')


def add_loops_to_network(G, mst_non_directed, new_mst_nodes, mst_edges, type_mat, pipe_dn):
    added_a_loop = False
    # Identify all NONE type nodes in the steiner tree
    for node_number, node_coords in zip(new_mst_nodes.index, new_mst_nodes['coordinates']):
        if new_mst_nodes['Type'][node_number] == 'NONE':
            # find neighbours of nodes in the potential network and steiner network
            potential_neighbours = G[node_coords]
            steiner_neighbours = mst_non_directed[node_coords]
            # check if there are differences, if yes, an edge was deleted here
            if not set(potential_neighbours.keys()) == set(steiner_neighbours.keys()):
                new_neighbour_list = []
                for a in potential_neighbours.keys():
                    if a not in steiner_neighbours.keys():
                        new_neighbour_list.append(a)
                # check if the node that is additional in the potential network also exists in the steiner network
                for new_neighbour in new_neighbour_list:
                    if new_neighbour in list(new_mst_nodes['coordinates'].values):
                        # check if it is a none type
                        # write out index of this node
                        node_index = list(new_mst_nodes['coordinates'].values).index(new_neighbour)
                        if new_mst_nodes['Type'][node_index] == 'NONE':
                            # create new edge
                            line = LineString((node_coords, new_neighbour))
                            if not line in mst_edges['geometry']:
                                mst_edges = mst_edges.append(
                                    {"geometry": line, "Pipe_DN": pipe_dn, "Type_mat": type_mat,
                                     "Name": "PIPE" + str(mst_edges.Name.count())},
                                    ignore_index=True)
                                added_a_loop = True
                            mst_edges.reset_index(inplace=True, drop=True)
    if not added_a_loop:
        print('No first degree loop added. Trying two nodes apart.')
        # Identify all NONE type nodes in the steiner tree
        for node_number, node_coords in zip(new_mst_nodes.index, new_mst_nodes['coordinates']):
            if new_mst_nodes['Type'][node_number] == 'NONE':
                # find neighbours of nodes in the potential network and steiner network
                potential_neighbours = G[node_coords]
                steiner_neighbours = mst_non_directed[node_coords]
                # check if there are differences, if yes, an edge was deleted here
                if not set(potential_neighbours.keys()) == set(steiner_neighbours.keys()):
                    new_neighbour_list = []
                    for a in potential_neighbours.keys():
                        if a not in steiner_neighbours.keys():
                            new_neighbour_list.append(a)
                    # check if the node that is additional in the potential network does not exist in the steiner network
                    for new_neighbour in new_neighbour_list:
                        if new_neighbour not in list(new_mst_nodes['coordinates'].values):
                            # find neighbours of that node
                            second_degree_pot_neigh = list(G[new_neighbour].keys())
                            for potential_second_deg_neighbour in second_degree_pot_neigh:
                                if potential_second_deg_neighbour in list(new_mst_nodes[
                                                                              'coordinates'].values) and potential_second_deg_neighbour != node_coords:
                                    # check if it is a none type
                                    # write out index of this node
                                    node_index = list(new_mst_nodes['coordinates'].values).index(
                                        potential_second_deg_neighbour)
                                    if new_mst_nodes['Type'][node_index] == 'NONE':
                                        # create new edge
                                        line = LineString((node_coords, new_neighbour))
                                        if line not in mst_edges['geometry']:
                                            mst_edges = mst_edges.append(
                                                {"geometry": line, "Pipe_DN": pipe_dn, "Type_mat": type_mat,
                                                 "Name": "PIPE" + str(mst_edges.Name.count())},
                                                ignore_index=True)
                                        # Add new node from potential network to steiner tree
                                        # create copy of selected node and add to list of all nodes
                                        copy_of_new_mst_nodes = new_mst_nodes.copy()
                                        x_distance = new_neighbour[0] - node_coords[0]
                                        y_distance = new_neighbour[1] - node_coords[1]
                                        copy_of_new_mst_nodes.geometry = copy_of_new_mst_nodes.translate(
                                            xoff=x_distance, yoff=y_distance)
                                        selected_node = copy_of_new_mst_nodes[
                                            copy_of_new_mst_nodes["coordinates"] == node_coords]
                                        selected_node.loc[:, "Name"] = "NODE" + str(new_mst_nodes.Name.count())
                                        selected_node.loc[:, "Type"] = "NONE"
                                        selected_node["coordinates"] = selected_node.geometry.values[0].coords
                                        if selected_node["coordinates"].values not in new_mst_nodes[
                                            "coordinates"].values:
                                            new_mst_nodes = new_mst_nodes.append(selected_node)
                                        new_mst_nodes.reset_index(inplace=True, drop=True)

                                        line2 = LineString((new_neighbour, potential_second_deg_neighbour))
                                        if line2 not in mst_edges['geometry']:
                                            mst_edges = mst_edges.append(
                                                {"geometry": line2, "Pipe_DN": pipe_dn, "Type_mat": type_mat,
                                                 "Name": "PIPE" + str(mst_edges.Name.count())},
                                                ignore_index=True)
                                            added_a_loop = True
                                        mst_edges.reset_index(inplace=True, drop=True)
    if not added_a_loop:
        print('No loops added.')
    return mst_edges, new_mst_nodes


def calc_coord_anchor(total_demand_location, nodes_df, type_network):
    total_demand = pd.read_csv(total_demand_location)
    nodes_names_demand = nodes_df.merge(total_demand, left_on="Building", right_on="Name", how="inner")
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
    building_series = nodes_df[nodes_df['Building'] == building_name]
    return building_series


def add_plant_close_to_anchor(building_anchor, new_mst_nodes, mst_edges, type_mat, pipe_dn):
    # find closest node
    copy_of_new_mst_nodes = new_mst_nodes.copy()
    building_coordinates = building_anchor.geometry.values[0].coords
    x1 = building_coordinates[0][0]
    y1 = building_coordinates[0][1]
    delta = 10E24  # big number
    for node in copy_of_new_mst_nodes.iterrows():
        if node[1]['Type'] == 'NONE':
            x2 = node[1].geometry.coords[0][0]
            y2 = node[1].geometry.coords[0][1]
            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if 0 < distance < delta:
                delta = distance
                node_id = node[1].Name
    pd.options.mode.chained_assignment = None  # avoid warning
    # create copy of selected node and add to list of all nodes
    copy_of_new_mst_nodes.geometry = copy_of_new_mst_nodes.translate(xoff=1, yoff=1)
    selected_node = copy_of_new_mst_nodes[copy_of_new_mst_nodes["Name"] == node_id]
    selected_node.loc[:, "Name"] = "NODE" + str(new_mst_nodes.Name.count())
    selected_node.loc[:, "Type"] = "PLANT"
    new_mst_nodes = new_mst_nodes.append(selected_node)
    new_mst_nodes.reset_index(inplace=True, drop=True)

    # create new edge
    point1 = (selected_node.geometry.x, selected_node.geometry.y)
    point2 = (new_mst_nodes[new_mst_nodes["Name"] == node_id].geometry.x,
              new_mst_nodes[new_mst_nodes["Name"] == node_id].geometry.y)
    line = LineString((point1, point2))
    mst_edges = mst_edges.append({"geometry": line, "Pipe_DN": pipe_dn, "Type_mat": type_mat,
                                  "Name": "PIPE" + str(mst_edges.Name.count())
                                  }, ignore_index=True)
    mst_edges.reset_index(inplace=True, drop=True)
    return new_mst_nodes, mst_edges


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    weight_field = 'Shape_Leng'
    type_mat_default = config.network_layout.type_mat
    pipe_diameter_default = config.network_layout.pipe_diameter
    type_network = config.network_layout.network_type
    create_plant = config.network_layout.create_plant
    output_substations_shp = locator.get_temporary_file("nodes_buildings.shp")
    path_potential_network = locator.get_temporary_file("potential_network.shp")  # shapefile, location of output.
    output_edges = locator.get_network_layout_edges_shapefile(type_network, '')
    output_nodes = locator.get_network_layout_nodes_shapefile(type_network, '')
    output_network_folder = locator.get_input_network_folder(type_network, '')
    total_demand_location = locator.get_total_demand()
    calc_steiner_spanning_tree(path_potential_network, output_network_folder, output_substations_shp, output_edges,
                               output_nodes, weight_field, type_mat_default, pipe_diameter_default, type_network,
                               total_demand_location, create_plant)


if __name__ == '__main__':
    main(cea.config.Configuration())

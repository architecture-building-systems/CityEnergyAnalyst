"""
This script calculates the minimum spanning tree of a shapefile network
"""

import math
import os

import networkx as nx
import numpy as np
import pandas as pd
from geopandas import GeoDataFrame as gdf
from networkx.algorithms.approximation.steinertree import steiner_tree
from shapely.geometry import LineString

import cea.config
import cea.globalvar
import cea.inputlocator

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_steiner_spanning_tree(input_network_shp, output_network_folder, building_nodes_shp, output_edges, output_nodes,
                               weight_field, type_mat_default, pipe_diameter_default, type_network,
                               total_demand_location, create_plant, allow_looped_networks, optimization_flag,
                               plant_building_names, disconnected_building_names):
    # read shapefile into networkx format into a directed graph, this is the potential network
    graph = nx.read_shp(input_network_shp)
    nodes_graph = nx.read_shp(building_nodes_shp)

    # tolerance
    tolerance = 6

    # transform to an undirected graph
    iterator_edges = graph.edges(data=True)

    # get graph
    G = nx.Graph()
    for (x, y, data) in iterator_edges:
        x = (round(x[0], tolerance), round(x[1], tolerance))
        y = (round(y[0], tolerance), round(y[1], tolerance))
        G.add_edge(x, y, weight=data[weight_field])

    # get nodes
    iterator_nodes = nodes_graph.nodes(data=False)
    terminal_nodes = [(round(node[0], tolerance), round(node[1], tolerance)) for node in iterator_nodes]
    if len(disconnected_building_names) > 0:
        # identify coordinates of disconnected buildings and remove form terminal nodes list
        all_buiding_nodes_df = gdf.from_file(building_nodes_shp)
        all_buiding_nodes_df.loc[:, 'coordinates'] = all_buiding_nodes_df['geometry'].apply(
            lambda x: (round(x.coords[0][0], tolerance), round(x.coords[0][1], tolerance)))
        disconnected_building_coordinates = []
        for building in disconnected_building_names:
            index = np.where(all_buiding_nodes_df['Name'] == building)[0]
            disconnected_building_coordinates.append(all_buiding_nodes_df['coordinates'].values[index][0])
        for disconnected_building in disconnected_building_coordinates:
            terminal_nodes = [i for i in terminal_nodes if i != disconnected_building]

    # calculate steiner spanning tree of undirected graph
    mst_non_directed = nx.Graph(steiner_tree(G, terminal_nodes))
    nx.write_shp(mst_non_directed, output_network_folder)

    # populate fields Building, Type, Name
    mst_nodes = gdf.from_file(output_nodes)
    building_nodes_df = gdf.from_file(building_nodes_shp)
    building_nodes_df.loc[:, 'coordinates'] = building_nodes_df['geometry'].apply(
        lambda x: (round(x.coords[0][0], tolerance), round(x.coords[0][1], tolerance)))
    if len(disconnected_building_names) > 0:
        for disconnected_building in disconnected_building_coordinates:
            building_id = int(np.where(building_nodes_df['coordinates'] == disconnected_building)[0])
            building_nodes_df = building_nodes_df.drop(building_nodes_df.index[building_id])
    mst_nodes.loc[:, 'coordinates'] = mst_nodes['geometry'].apply(
        lambda x: (round(x.coords[0][0], tolerance), round(x.coords[0][1], tolerance)))
    names_temporary = ["NODE" + str(x) for x in mst_nodes['FID']]
    new_mst_nodes = mst_nodes.merge(building_nodes_df, suffixes=['', '_y'], on="coordinates", how='outer')
    new_mst_nodes.fillna(value="NONE", inplace=True)
    new_mst_nodes.loc[:, 'Building'] = new_mst_nodes['Name']
    new_mst_nodes.loc[:, 'Name'] = names_temporary
    new_mst_nodes.loc[:, 'Type'] = new_mst_nodes['Building'].apply(lambda x: 'CONSUMER' if x != "NONE" else x)

    # populate fields Type_mat, Name, Pipe_Dn
    mst_edges = gdf.from_file(output_edges)
    mst_edges.loc[:, 'Type_mat'] = type_mat_default
    mst_edges.loc[:, 'Pipe_DN'] = pipe_diameter_default
    mst_edges.loc[:, 'Name'] = ["PIPE" + str(x) for x in mst_edges.index]

    if allow_looped_networks == True:
        # add loops to the network by connecting None nodes that exist in the potential network
        mst_edges, new_mst_nodes = add_loops_to_network(G, mst_non_directed, new_mst_nodes, mst_edges, type_mat_default,
                                                        pipe_diameter_default)
        mst_edges.drop(['weight'], inplace=True, axis=1)
    if create_plant:
        if optimization_flag == False:
            building_anchor = calc_coord_anchor(total_demand_location, new_mst_nodes, type_network)
            new_mst_nodes, mst_edges = add_plant_close_to_anchor(building_anchor, new_mst_nodes, mst_edges,
                                                                 type_mat_default, pipe_diameter_default)
        else:
            for building in plant_building_names:
                building_anchor = building_node_from_name(building, new_mst_nodes)
                new_mst_nodes, mst_edges = add_plant_close_to_anchor(building_anchor, new_mst_nodes, mst_edges,
                                                                     type_mat_default, pipe_diameter_default)

    new_mst_nodes.drop(["FID", "coordinates", 'floors_bg', 'floors_ag', 'height_bg', 'height_ag', 'geometry_y'],
                       axis=1,
                       inplace=True)

    nx.write_shp(mst_non_directed, output_network_folder)

    # get coordinate system and reproject to UTM
    mst_edges.to_file(output_edges, driver='ESRI Shapefile')
    new_mst_nodes.to_file(output_nodes, driver='ESRI Shapefile')


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
        print 'No first degree loop added. Trying two nodes apart.'
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
        print 'No loops added.'
    return mst_edges, new_mst_nodes


def calc_coord_anchor(total_demand_location, nodes_df, type_network):
    total_demand = pd.read_csv(total_demand_location)
    nodes_names_demand = nodes_df.merge(total_demand, left_on="Building", right_on="Name", how="inner")
    if type_network == "DH":
        field = "QH_sys_MWhyr"
    elif type_network == "DC":
        field = "QC_sys_MWhyr"
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

"""
This script calculates the minimum spanning tree of a shapefile network
"""

import networkx as nx
import cea.globalvar
import cea.inputlocator
from geopandas import GeoDataFrame as gdf
import cea.config
import os


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_minimum_spanning_tree(input_network_shp, output_network_folder, building_nodes_shp, output_edges, output_nodes,
                               weight_field, type_mat_default, pipe_diameter_default):
    # read shapefile into networkx format into a directed graph
    graph = nx.read_shp(input_network_shp)

    # transform to an undirected graph
    iterator_edges = graph.edges(data=True)

    G = nx.Graph()
    # plant = (11660.95859999981, 37003.7689999986)
    for (x, y, data) in iterator_edges:
        G.add_edge(x, y, weight=data[weight_field])
    # calculate minimum spanning tree of undirected graph

    mst_non_directed = nx.minimum_spanning_edges(G, data=False)

    # transform back directed graph and save:
    mst_directed = nx.DiGraph()
    mst_directed.add_edges_from(mst_non_directed)
    nx.write_shp(mst_directed, output_network_folder)

    # populate fields Type_mat, Name, Pipe_Dn
    mst_edges = gdf.from_file(output_edges)
    mst_edges['Type_mat'] = type_mat_default
    mst_edges['Pipe_DN'] = pipe_diameter_default
    mst_edges['Name'] = ["PIPE" + str(x) for x in mst_edges['FID']]
    mst_edges.drop("FID", axis=1, inplace=True)
    mst_edges.crs = gdf.from_file(input_network_shp).crs  # to add coordinate system
    mst_edges.to_file(output_edges, driver='ESRI Shapefile')

    # populate fields Building, Type, Name
    mst_nodes = gdf.from_file(output_nodes)

    buiding_nodes_df = gdf.from_file(building_nodes_shp)
    mst_nodes.crs = buiding_nodes_df.crs  # to add same coordinate system
    buiding_nodes_df['coordinates'] = buiding_nodes_df['geometry'].apply(
        lambda x: (round(x.coords[0][0], 4), round(x.coords[0][1], 4)))
    mst_nodes['coordinates'] = mst_nodes['geometry'].apply(
        lambda x: (round(x.coords[0][0], 4), round(x.coords[0][1], 4)))
    names_temporary = ["NODE" + str(x) for x in mst_nodes['FID']]

    new_mst_nodes = mst_nodes.merge(buiding_nodes_df, suffixes=['', '_y'], on="coordinates", how='outer')
    new_mst_nodes.fillna(value="NONE", inplace=True)
    new_mst_nodes['Building'] = new_mst_nodes['Name']

    new_mst_nodes['Name'] = names_temporary
    new_mst_nodes['Type'] = new_mst_nodes['Building'].apply(lambda x: 'CONSUMER' if x != "NONE" else x)
    new_mst_nodes.drop(["FID", "coordinates", 'floors_bg', 'floors_ag', 'height_bg', 'height_ag', 'geometry_y'], axis=1,
                       inplace=True)
    new_mst_nodes.to_file(output_nodes, driver='ESRI Shapefile')


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    input_network_shp = locator.get_connectivity_potential()  # shapefile, location of output.
    type_mat_default = "T1"
    pipe_diameter_default = 150
    weight_field = 'Shape_Leng'
    type_network = 'DH'  # DC or DH
    building_nodes = locator.get_connection_point()
    output_edges = locator.get_network_layout_edges_shapefile(type_network,'')
    output_nodes = locator.get_network_layout_nodes_shapefile(type_network,'')
    output_network_folder = locator.get_input_network_folder(type_network)
    calc_minimum_spanning_tree(input_network_shp, output_network_folder, building_nodes, output_edges,
                               output_nodes, weight_field, type_mat_default, pipe_diameter_default)


if __name__ == '__main__':
    main(cea.config.Configuration())

"""
This script caclulates the minimum spanning tree of a shapefile network
"""

import networkx as nx
import cea.globalvar
import cea.inputlocator
from geopandas import GeoDataFrame as gdf

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_minimum_spanning_tree(input_network_shp, output_network_folder, output_edges, output_nodes,
                               weight_field, type_mat_default, pipe_diameter_default):
    # read shapefile into networxk format
    graph = nx.read_shp(input_network_shp)
    iterator_edges = graph.edges_iter(data=True)

    # get minimum spanning tree
    G = nx.Graph()
    for (x, y, data) in iterator_edges:
        G.add_edge(x, y, weight=data[weight_field])

    mst = nx.minimum_spanning_edges(G, data=False)  # a generator of MST edges
    mst_non_directed = sorted(list(mst))

    # transform into directed graph and save:
    mst_directed = nx.DiGraph()
    mst_directed.add_edges_from(mst_non_directed)
    nx.write_shp(mst_directed, output_network_folder)

    # populate fields Type_mat, Name, Pipe_Dn
    mst = gdf.from_file(output_edges)
    mst['Type_mat'] = type_mat_default
    mst['Pipe_DN'] = pipe_diameter_default
    mst['Name'] = ["PIPE" + str(x) for x in mst['FID']]
    mst.drop("FID", axis=1, inplace=True)
    mst.crs = gdf.from_file(input_network_shp).crs
    mst.to_file(output_edges, driver='ESRI Shapefile')


def run_as_script():
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    input_network_shp = locator.get_connectivity_potential()  # shapefile, location of output.
    type_mat_default = "T1"
    pipe_diameter_default = 150
    weight_field = 'Shape_Leng'
    type_network = 'DC'  # DC or DH
    output_edges = locator.get_network_layout_edges_shapefile(type_network)
    output_nodes = locator.get_network_layout_nodes_shapefile(type_network)
    output_network_folder = locator.get_input_network_folder(type_network)
    calc_minimum_spanning_tree(input_network_shp, output_network_folder, output_edges,
                               output_nodes, weight_field, type_mat_default, pipe_diameter_default)


if __name__ == '__main__':
    run_as_script()

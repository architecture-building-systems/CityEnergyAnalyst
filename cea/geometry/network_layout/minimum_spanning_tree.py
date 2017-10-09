"""
This script caclulates the minimum spanning tree of a shapefile network
"""


import networkx as nx
import cea.globalvar
import cea.inputlocator



def calc_minimum_spanning_tree(network_shp):

    graph = nx.read_shp(network_shp)
    graph.edge



def run_as_script():
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    network_shp = locator.get_connectivity_potential()  # shapefile, location of output.
    calc_minimum_spanning_tree(network_shp)

if __name__ == '__main__':
    run_as_script()
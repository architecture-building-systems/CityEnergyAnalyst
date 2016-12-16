"""
============================
Hydraulic - thermal network
============================

"""
from __future__ import division
import time
import numpy as np
import pandas as pd
import math
import cea.globalvar as gv
import geopandas as gpd
import os


__author__ = "Martin Mosteiro"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Martin Mosteiro" ]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def get_thermal_network_from_shapefile(locator):
    """
    This function reads the existing node and pipe network from a shapefile (using a road shapefile from the Zurich
    reference case as a template) and produces an edge-node incidence matrix (as defined by Oppelt et al. "Dynamic
    thermo-hydraulic model of district cooling networks," Applied Thermal Engineering, 2016) as well as the pipe
    properties (length, start node, and end node) and node coordinates.

    :param locator: locator class

    :return:
        edge_node_matrix: matrix consisting of n rows (number of nodes) and e columns (number of edges)
        csv file stored in locator.pathNtwRes + '//' + EdgeNode_DH

    """

    t0 = time.clock()

    # import network properties from shapefile
    network_edges_df = gpd.read_file(locator.get_heating_network_edges())
    network_nodes_df = gpd.read_file(locator.get_heating_network_nodes())

    # get node and pipe information
    node_df, pipe_df = extract_network(network_edges_df, network_nodes_df)

    # create consumer and plant node vectors
    node_names = node_df.index.values
    consumer_nodes = [] #np.zeros(len(node_names))#np.vstack((node_names, (node_df['consumer'] * node_df['Node']).values))
    plant_nodes = [] #np.zeros(len(node_names))#np.vstack((node_names, (node_df['plant'] * node_df['Node']).values))
    for node in node_names:
        if node_df['consumer'][node] == 1:
            consumer_nodes.append(node)
        else:
            consumer_nodes.append('')
        if node_df['plant'][node] == 1:
            plant_nodes.append(node)
        else:
            plant_nodes.append('')

    # create edge-node matrix
    list_pipes = pipe_df.index.values
    list_nodes = sorted(set(pipe_df['start node']).union(set(pipe_df['end node'])))
    edge_node_matrix = np.zeros((len(list_nodes), len(list_pipes)))
    for j in range(len(list_pipes)):
        for i in range(len(list_nodes)):
            if pipe_df['end node'][j] == list_nodes[i]:
                edge_node_matrix[i][j] = 1
            elif pipe_df['start node'][j] == list_nodes[i]:
                edge_node_matrix[i][j] = -1
    edge_node_df = pd.DataFrame(data=edge_node_matrix, index=list_nodes, columns=list_pipes)

    edge_node_df.to_csv(os.path.join(locator.get_optimization_network_layout_folder(), "EdgeNode_DH.csv"))
    node_df.to_csv(locator.get_optimization_network_layout_folder() + '//' + 'Node_DF_DH.csv')
    pipe_df.to_csv(locator.get_optimization_network_layout_folder() + '//' + 'Pipe_DF_DH.csv')

    print time.clock() - t0, "seconds process time for Network summary\n"

#=============================
# Utility
#=============================

def extract_network(edges_df, nodes_df):
    '''
    extracts network data into dataframes for pipes and nodes in the network
    :param shapefile: network shapefile
    :return: node_df: list of nodes and their corresponding coordinates
             pipe_df: list of pipes and their corresponding lengths and start and end nodes
    '''
    import numpy as np
    import os

    # import consumer and plant nodes
    end_nodes = []
    for node in nodes_df['geometry']:
        end_nodes.append(node.coords[0])
    nodes_df['geometry'] = end_nodes
    nodes_df['consumer'] = np.ones(len(nodes_df['Plant'])) - nodes_df['Plant'].values

    # create node dictionary with plant and consumer nodes
    node_dict = {}
    node_columns = ['Node', 'Name', 'plant', 'consumer', 'coordinates']
    for i in range(len(nodes_df)):
        node_dict[nodes_df['geometry'][i]] = ['NODE'+str(i), nodes_df['Name'][i], nodes_df['Plant'][i],
                                              nodes_df['consumer'][i], nodes_df['geometry'][i]]

    # create edge dictionary with pipe lengths and start and end nodes
    # complete node dictionary with missing nodes (i.e., tees)
    edge_dict = {}
    edge_columns = ['pipe length', 'start node', 'end node']
    for j in range(len(edges_df)):
        pipe = edges_df['geometry'][j]
        start_node = pipe.coords[0]
        end_node = pipe.coords[1]
        if start_node not in node_dict.keys():
            i += 1
            node_dict[start_node] = ['NODE'+str(i), 'TEE' + str(i - len(nodes_df)), 0, 0, start_node]
        if end_node not in node_dict.keys():
            i += 1
            node_dict[end_node] = ['NODE'+str(i), 'TEE' + str(i - len(nodes_df)), 0, 0, end_node]
        edge_dict['EDGE' + str(j)] = [edges_df['Shape_Leng'][j], node_dict[start_node][0], node_dict[end_node][0]]

    # create dataframes containing all nodes and edges
    node_df = pd.DataFrame.from_dict(node_dict, orient='index')
    node_df.columns = node_columns
    node_df = node_df.set_index(node_df['Node']).drop(['Node'], axis = 1)
    edge_df = pd.DataFrame.from_dict(edge_dict, orient='index')
    edge_df.columns = edge_columns

    # TODO: remove these tests as soon as it's confirmed it works
    node_df.to_csv(os.path.expandvars(r'%TEMP%\Node_DF_DH.csv'))
    edge_df.to_csv(os.path.expandvars(r'%TEMP%\Pipe_DF_DH.csv'))

    return node_df, edge_df

#============================
#test
#============================


def run_as_script(scenario_path=None):
    """
    run the whole network summary routine
    """
    import cea.globalvar
    import cea.inputlocator as inputlocator
    from geopandas import GeoDataFrame as gpdf
    from cea.utilities import epwreader
    from cea.resources import geothermal

    gv = cea.globalvar.GlobalVariables()

    if scenario_path is None:
        scenario_path = gv.scenario_reference

    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    building_names = pd.read_csv(locator.get_total_demand())['Name']
    weather_file = locator.get_default_weather()
    # add geothermal part of preprocessing
    T_ambient = epwreader.epw_reader(weather_file)['drybulb_C']
    gv.ground_temperature = geothermal.calc_ground_temperature(T_ambient.values, gv)

    get_thermal_network_from_shapefile(locator)

    print 'test get_thermal_network_from_shapefile() succeeded'

if __name__ == '__main__':
    run_as_script()


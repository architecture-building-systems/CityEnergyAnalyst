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
    node_df, pipe_df = extract_network(network_edges_df, network_nodes_df, locator)

    # create edge and node connection matrix
    # this matrix specifies which edges are connected to which nodes, NOT the direction of flow
    edge_node_connections = np.zeros((len(node_df),len(pipe_df)))
    node_names = []
    pipe_names = []
    for j in range(len(pipe_df)):
        edge_node_connections[pipe_df['end node'][j]][j] = 1
        edge_node_connections[pipe_df['start node'][j]][j] = 1
        pipe_names.append('Pipe'+str(j))
    for i in range(len(node_df)):
        node_names.append('Node'+str(i))
    connections_df = pd.DataFrame(data=edge_node_connections, index = node_names, columns = pipe_names)

    network_nodes_df.to_csv(locator.pathNtwLayout + '//' + 'Node_DF_DH_2.csv')
    node_df.to_csv(locator.pathNtwLayout + '//' + 'Node_DF_DH.csv')
    pipe_df.to_csv(locator.pathNtwLayout + '//' + 'Pipe_DF_DH.csv')
    connections_df.to_csv(locator.pathNtwLayout + '//' + 'EdgeNode_Connection_DH.csv')

    print time.clock() - t0, "seconds process time for Network summary\n"

#=============================
# Utility
#=============================

def extract_network(edges_df, nodes_df, locator):
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
    nodes_df = nodes_df.drop(['Af','AncillaryR','Enabled','Floors','Hs','ID','Qc','Qh','Year','height'],axis=1)
    nodes_df['consumer'] = np.ones(len(nodes_df['Plant']))-nodes_df['Plant'].values
    #nodes_df = nodes_df.set_index(nodes_df['geometry'])

    end_node_set = set(nodes_df['geometry'])

    # import network shapefile and extract all edge and node information
    nodes = []
    node_names = []
    counter = 0
    start_node = []
    end_node = []
    for pipe in edges_df['geometry']:
        if pipe.coords[0] not in nodes:
            nodes.append(pipe.coords[0])
            node_names.append('NODE' + str(counter))
            counter +=1
        if pipe.coords[1] not in nodes:
            nodes.append(pipe.coords[1])
            node_names.append('NODE' + str(counter))
            counter +=1
        start_node.append(pipe.coords[0])
        end_node.append(pipe.coords[1])
        '''
        for i in range(len(nodes)):
            if pipe.coords[0] == nodes[i]:
                start_node.append(i)
            if pipe.coords[1] == nodes[i]:
                end_node.append(i)
        '''
    for node in end_node_set:
        if node not in nodes:
            nodes.append(node)
            node_names.append('NODE'+str(counter))
    '''
    node_df = pd.DataFrame(data = np.zeros([len(nodes),len(end_nodes_df.columns)]), columns = end_nodes_df.columns)# nodes, columns=['coordinates'])#, index=nodes)
    node_df['geometry'] = nodes
    end_nodes_df = end_nodes_df.merge(total_demand[['Name','QHf_MWhyr']], left_on = 'Name', right_on = 'Name')
    '''
    for node in nodes:
        if node not in end_node_set:
            nodes_df.loc[len(nodes_df)] = [0,0,node,0]
    nodes_df.to_csv(os.path.expandvars(r'%TEMP%\Node_DF_DH.csv'))


    node_df = pd.DataFrame(data = None, columns = None, index = nodes)

    '''i = 0
    for node in nodes:
        if node in end_nodes_df['geometry'].values:
            print len(node_df[:][i])
            print len(end_nodes_df[:][i:i+1])
    #print node_df
    '''

    node_df['coordinates'] = nodes

    total_demand = pd.read_csv(locator.get_total_demand())

    #nodes_df = nodes_df.set_index(nodes_df['geometry'])



    tee = 0
    for i in range(len(nodes)):
        node_df['geometry'][i] = nodes[i]
        if nodes[i] not in nodes_df['geometry']:
            node_df['Name'][i] = 'TEE'+str(tee)
            node_df['Plant'][i] = 0
            node_df['']
            tee += 1
    print node_df
    pipe_df = pd.DataFrame(data=np.column_stack((edges_df['Shape_Leng'].tolist(),start_node,end_node)), columns = ['pipe length','start node','end node'])

    return node_df, pipe_df

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


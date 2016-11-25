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


def network_shapefile_main(locator):
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
    network_df = gpd.read_file(locator.pathNtwLayout + '//' + 'roads.shp')

    # get node and pipe information
    node_df, pipe_df = extract_network(network_df)

    # create edge-node matrix
    edge_node_matrix = np.zeros((len(node_df),len(pipe_df)))
    node_names = []
    pipe_names = []
    for j in range(len(pipe_df)):
        edge_node_matrix[pipe_df['end node'][j]][j] = 1
        edge_node_matrix[pipe_df['start node'][j]][j] = -1
        pipe_names.append('Pipe'+str(j))
    for i in range(len(node_df)):
        node_names.append('Node'+str(i))
    edge_node_df = pd.DataFrame(data=edge_node_matrix, index = node_names, columns = pipe_names)

    node_df.to_csv(locator.pathNtwLayout + '//' + 'Node_DF_DH.csv')
    pipe_df.to_csv(locator.pathNtwLayout + '//' + 'Pipe_DF_DH.csv')
    edge_node_df.to_csv(locator.pathNtwLayout + '//' + 'EdgeNode_DH.csv')

    print time.clock() - t0, "seconds process time for Network summary\n"

#=============================
# Utility
#=============================

def extract_network(shapefile):
    '''
    extracts network data into dataframes for pipes and nodes in the network
    :param shapefile: network shapefile
    :return: node_df: list of nodes and their corresponding coordinates
             pipe_df: list of pipes and their corresponding lengths and start and end nodes
    '''
    import numpy as np

    nodes = []
    start_node = []
    end_node = []
    for pipe in shapefile['geometry']:
        if [pipe.coords[0]] not in nodes:
            nodes.append([pipe.coords[0]])
        if [pipe.coords[1]] not in nodes:
            nodes.append([pipe.coords[1]])
        for i in range(len(nodes)):
            if [pipe.coords[0]] == nodes[i]:
                start_node.append(i)
            if [pipe.coords[1]] == nodes[i]:
                end_node.append(i)

    node_df = pd.DataFrame(data=nodes, columns=['coordinates'])
    pipe_df = pd.DataFrame(data=np.column_stack((shapefile['DB2GSE_Sde'].tolist(),start_node,end_node)), columns = ['pipe length','start node','end node'])

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
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = pd.read_csv(locator.get_total_demand())['Name']
    weather_file = locator.get_default_weather()
    # add geothermal part of preprocessing
    T_ambient = epwreader.epw_reader(weather_file)['drybulb_C']
    gv.ground_temperature = geothermal.calc_ground_temperature(T_ambient.values, gv)

    network_shapefile_main(locator)

    print 'test_network_shapefile_main() succeeded'

if __name__ == '__main__':
    run_as_script()


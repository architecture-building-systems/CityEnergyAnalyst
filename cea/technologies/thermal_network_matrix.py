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

__author__ = "Martin Mosteiro"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Martin Mosteiro" ]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def network_matrix_main(locator):
    """
    This function reads the existing node and pipe network from csv files (as provided for the Zug reference case) and
    produces an edge-node incidence matrix (as defined by Oppelt et al. "Dynamic thermo-hydraulic model of district
    cooling networks," Applied Thermal Engineering, 2016) as well as the length of each edge.

    :param locator: locator class

    :return:
        edge_node_matrix: matrix consisting of n rows (number of nodes) and e columns (number of edges)
        csv file stored in locator.pathNtwRes + '//' + EdgeNode_DH

    """

    t0 = time.clock()

    # import properties of distribution
    pipe_data = pd.read_csv(locator.get_pipes_DH_network)
    list_pipes = pipe_data['DC_ID']
    list_nodes = sorted(set(pipe_data['NODE1']).union(set(pipe_data['NODE2'])))
    edge_node_matrix = np.zeros((len(list_nodes),len(list_pipes)))
    for j in range(len(list_pipes)):
        for i in range(len(list_nodes)):
            if pipe_data['NODE2'][j] == list_nodes[i]:
                edge_node_matrix[i][j] = 1
            elif pipe_data['NODE1'][j] == list_nodes[i]:
                edge_node_matrix[i][j] = -1
    edge_node_df = pd.DataFrame(data=edge_node_matrix, index = list_nodes, columns = list_pipes)

    edge_node_df.to_csv(locator.pathNtwLayout + '//' + 'EdgeNode_DH.csv')


    print time.clock() - t0, "seconds process time for Network summary\n"

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

    key = 'all'
    network_matrix_main(locator)

    print 'test_network_matrix_main() succeeded'

if __name__ == '__main__':
    run_as_script()


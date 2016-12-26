import cea.inputlocator
import pandas as pd
import os
import numpy as np

def calc_mass_flow_edges(locator):

    # get mass flow matrix from substation.py
    edge_node_df, all_nodes_df, pipe_length_df = get_thermal_network_from_csv(locator)
    '''
        #
        # edge_node_matrix needs to be expanded to include return pipes
        for pipe in edge_node_df:
            edge_node_df['-'+pipe] = -edge_node_df[pipe]
        #
    '''

    # get substation flow vector
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand['Name']
    mass_flow_substation_df = pd.read_csv(os.path.expandvars(r'%TEMP%\mass_flow_substations.csv'))
    mass_flow_substation_df['J58'] = -np.sum(mass_flow_substation_df.values)
    edge_node_df.to_csv(os.path.expandvars(r'%TEMP%\edge_node_df.csv'))

    mass_flow = np.transpose(np.linalg.lstsq(edge_node_df.values, np.transpose(mass_flow_substation_df.values))[0])

    pd.DataFrame(data = mass_flow).to_csv(os.path.expandvars(r'%TEMP%\MassFlow_2.csv'))


def get_thermal_network_from_csv(locator):
    """
    This function reads the existing node and pipe network from csv files (as provided for the Zug reference case) and
    produces an edge-node incidence matrix (as defined by Oppelt et al. "Dynamic thermo-hydraulic model of district
    cooling networks," Applied Thermal Engineering, 2016) as well as the length of each edge.

    :param locator: locator class

    :return:
        edge_node_matrix: matrix consisting of n rows (number of nodes) and e columns (number of edges) and indicating
        direction of flow of each edge e at node n: if e points to n, value is 1; if e leaves node n, -1; else, 0.
        consumer_nodes: vector that defines which vectors correspond to consumers (if node n is a consumer node,
         then consumer_nodes[n] = (Name), else consumer_nodes[n] = 0)
        plant_nodes: vector that defines which vectors correspond to plants (if node n is a plant node, then
         plant_nodes[n] = (Name), else plant_nodes[n] = 0)
        csv file stored in locator.pathNtwRes + '//' + EdgeNode_DH

    """


    # get node data and create consumer and plant node vectors
    node_data_df = pd.read_csv(locator.get_optimization_network_layout_nodes_file())
    node_names = node_data_df['DC_ID'].values
    consumer_nodes = np.vstack((node_names,(node_data_df['Sink']*node_data_df['Name']).values))
    plant_nodes = np.vstack((node_names,(node_data_df['Plant']*node_data_df['Name']).values))

    # get pipe data and create edge-node matrix
    pipe_data_df = pd.read_csv(locator.get_optimization_network_layout_pipes_file())
    pipe_data_df = pipe_data_df.set_index(pipe_data_df['DC_ID'].values, drop=True)
    list_pipes = pipe_data_df['DC_ID']
    list_nodes = sorted(set(pipe_data_df['NODE1']).union(set(pipe_data_df['NODE2'])))
    edge_node_matrix = np.zeros((len(list_nodes),len(list_pipes)))
    for j in range(len(list_pipes)):
        for i in range(len(list_nodes)):
            if pipe_data_df['NODE2'][j] == list_nodes[i]:
                edge_node_matrix[i][j] = 1
            elif pipe_data_df['NODE1'][j] == list_nodes[i]:
                edge_node_matrix[i][j] = -1
    edge_node_df = pd.DataFrame(data=edge_node_matrix, index = list_nodes, columns = list_pipes)

    edge_node_df.to_csv(os.path.join(locator.get_optimization_network_layout_folder(), "EdgeNode_DH.csv"))


    return edge_node_df, pd.DataFrame(data=[consumer_nodes[1][:], plant_nodes[1][:]], index = ['consumer','plant'], columns = consumer_nodes[0][:]),pipe_data_df['LENGTH']

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
    #substation_main(locator, total_demand, total_demand['Name'], gv, False)

    #calc_hydraulic_network(locator, gv)
    # print 'test calc_hydraulic_network() succeeded'

    calc_mass_flow_edges(locator)
    print 'test thermal_network_main() succeeded'

if __name__ == '__main__':
    run_as_script()

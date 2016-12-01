"""
============================
Hydraulic - thermal network
============================

"""
from __future__ import division
import time
import numpy as np
import pandas as pd
from cea.technologies.substation import substation_main
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

def calc_hydraulic_network(locator, gv):
    '''
    This function carries out the steady-state hydraulic calculation for a predefined network with predefined mass flow
    rate on each edge.

    :param locator: locator class
    :param mass_flow_substation: mass flow rate enter/exit from the supply side at each substation

    :return: mass_flow: vector specifying the mass flow rate at each edge e
    '''

    # get mass flow matrix from substation.py
    edge_node_df, all_nodes_df, pipe_length_df = get_thermal_network_from_csv(locator)
    '''# edge_node_matrix needs to be expanded to include return pipes
    for pipe in edge_node_df:
        edge_node_df['-'+pipe] = -edge_node_df[pipe]'''
    # get substation flow vector
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand['Name']
    mass_flow_substation_df = pd.DataFrame()
    iteration = 0
    for node in all_nodes_df:   #consumer_nodes+plant_nodes:    #name in building_names:
        if (all_nodes_df[node]['consumer']+all_nodes_df[node]['plant']) != '':
            mass_flow_substation_df[node] = pd.read_csv(locator.pathSubsRes + '//' + (all_nodes_df[node]['consumer']+all_nodes_df[node]['plant']) + "_result.csv", usecols=['mdot_DH_result'])  #name] = pd.read_csv(locator.pathSubsRes + '//' + name + "_result.csv", usecols=['mdot_DH_result'])
        else:
            mass_flow_substation_df[node] = np.zeros(8760)

    '''
    t0 = time.clock()
    mass_flow_df = pd.DataFrame(data=None, index=range(8760), columns=edge_node_df.columns.values)
    for i in range(len(mass_flow_substation_df)):
        mass_flow_df[:][i:i+1] = np.transpose(np.linalg.lstsq(edge_node_df.values, np.transpose(-mass_flow_substation_df[:][i:i + 1].values))[0])
    print time.clock() - t0, "seconds process time for total mass flow calculation\n"
    mass_flow_df.to_csv(locator.pathNtwLayout + '//' + 'MassFlow_DH.csv')
    '''
    mass_flow_df = pd.read_csv(locator.pathNtwLayout + '//' + 'MassFlow_DH.csv', usecols=edge_node_df.columns.values)
    mass_flow_df = np.absolute(mass_flow_df)    # added this hack to make sure code runs TODO: make sure you don't get negative flows!
    pipe_properties_df = assign_pipes_to_edges(mass_flow_df, locator, gv)
    temperature_matrix = np.ones([8760,len(edge_node_df.columns)])*323   # assigning a dummy temperature to each edge for now

    pressure_loss_pipes = pd.DataFrame(data=calc_pressure_loss_pipe(pipe_properties_df[:]['DN':'DN'].values, pipe_length_df.values,
                                    mass_flow_df.values, temperature_matrix, gv), index = range(8760), columns = mass_flow_df.columns.values)

    pressure_loss_pump = calc_pressure_loss_pump

    print pressure_loss_pipes


def get_thermal_network_from_csv(locator):
    """
    This function reads the existing node and pipe network from csv files (as provided for the Zug reference case) and
    produces an edge-node incidence matrix (as defined by Oppelt et al. "Dynamic thermo-hydraulic model of district
    cooling networks," Applied Thermal Engineering, 2016) as well as the length of each edge.

    :param locator: locator class

    :return:
        edge_node_matrix: matrix consisting of n rows (number of nodes) and e columns (number of edges) and indicating
        direction of flow of each edge e at node n
        consumer_nodes: vector that defines which vectors correspond to consumers (if node n is a consumer node,
         then consumer_nodes[n] = (Name), else consumer_nodes[n] = 0)
        plant_nodes: vector that defines which vectors correspond to plants (if node n is a plant node, then
         plant_nodes[n] = (Name), else plant_nodes[n] = 0)
        csv file stored in locator.pathNtwRes + '//' + EdgeNode_DH

    """

    t0 = time.clock()

    # get node data and create consumer and plant node vectors
    node_data_df = pd.read_csv(locator.get_nodes_DH_network)
    node_names = node_data_df['DC_ID'].values
    consumer_nodes = np.vstack((node_names,(node_data_df['Sink']*node_data_df['Name']).values))
    plant_nodes = np.vstack((node_names,(node_data_df['Plant']*node_data_df['Name']).values))

    # get pipe data and create edge-node matrix
    pipe_data_df = pd.read_csv(locator.get_pipes_DH_network)
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

    edge_node_df.to_csv(locator.pathNtwLayout + '//' + 'EdgeNode_DH.csv')

    print time.clock() - t0, "seconds process time for Network summary\n"

    return edge_node_df, pd.DataFrame(data=[consumer_nodes[1][:], plant_nodes[1][:]], index = ['consumer','plant'], columns = consumer_nodes[0][:]),pipe_data_df['LENGTH']

def assign_pipes_to_edges(mass_flow_df, locator, gv):
    '''
    This function assigns pipes from the catalog to the network for a network with unspecified pipe properties.
    Pipes are assigned based on each edge's minimum and maximum required flow rate (for now)

    :param mass_flow_df: dataframe containing the mass flow rate for each pipe at each moment of the year

    :return: pipe_properties_df: dataframe containing the pipe properties for each edge in the network
    '''

    # import pipe catalog from Excel file (catalog based on Fonseca et al. 2016)
    pipe_catalog = pd.read_excel(locator.get_thermal_networks())
    pipe_catalog['Vdot_min'] = pipe_catalog['Vdot_min'] * gv.Pwater
    pipe_catalog['Vdot_max'] = pipe_catalog['Vdot_max'] * gv.Pwater
    pipe_properties_df = pd.DataFrame(data=None,index=pipe_catalog.columns.values, columns = mass_flow_df.columns.values)
    for pipe in mass_flow_df:
        pipe_found = False
        i = 0
        t0 = time.clock()
        while pipe_found == False:
            if np.amax(np.absolute(mass_flow_df[pipe].values)) <= pipe_catalog['Vdot_max'][i] or i == len(pipe_catalog):
                pipe_properties_df[pipe] = np.transpose(pipe_catalog[:][i:i+1].values)
                pipe_found = True
            else:
                i += 1

    return pipe_properties_df

def calc_pressure_loss_pipe(pipe_diameter, pipe_length, mass_flow_rate, temperature, gv):
    kinematic_viscosity = calc_kinematic_viscosity(temperature)
    reynolds = 4*mass_flow_rate/(math.pi * kinematic_viscosity * pipe_diameter)
    pipe_roughness = 0.02    # assumed from Li & Svendsen for now
    darcy = 1.325 * np.log(pipe_roughness / (3.7 * pipe_diameter) + 5.74 / reynolds ** 0.9) ** (-2)  # Swamee-Jain equation to calculate the Darcy-Weisbach friction factor
    pressure_loss_edge = darcy*8/(math.pi*gv.gr)*kinematic_viscosity**2/pipe_diameter**5*pipe_length

    return pressure_loss_edge

def calc_kinematic_viscosity(temperature):
    return 2.652623e-8*math.e**(557.5447*(temperature-140)**-1)


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

    calc_hydraulic_network(locator, gv)

    print 'test calc_hydraulic_network() succeeded'

if __name__ == '__main__':
    run_as_script()


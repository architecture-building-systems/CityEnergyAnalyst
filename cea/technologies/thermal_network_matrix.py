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
import cea.technologies.substation_matrix as substation
import math
import cea.globalvar as gv
from cea.utilities import epwreader
from cea.resources import geothermal

__author__ = "Martin Mosteiro, Shanshan Hsieh"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Martin Mosteiro", "Shanshan Hsieh" ]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def thermal_network_main(locator,gv):
    """
    See Thermo-hydraulic modelling procedures for DHC Networks
    :param locator:
    :param gv:
    :return:
    """

    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand['Name']
    weather_file = locator.get_default_weather()


    # substation HEX design
    substations_HEX_specs, buildings = substation.substation_HEX_design_main(locator, total_demand, building_names, gv)

    # get edge-node matrix from defined network
    edge_node_df, all_nodes = get_thermal_network_from_csv(locator)

    # set initial substation mass flow for all consumers
    T_return_all_0, mass_flow_substations_0 = substation.substation_return_model_main(locator, building_names, gv, buildings,
                                                                       substations_HEX_specs, T_DH=60, t=0)
    # substation_mass_flow_matrix = match_substation_to_nodes(all_nodes, building_names, mass_flow_substation_0)
    # FIXME: assign substation mass flow at each building to the corresponding node


    # Start solving hydraulic and thermal equations at each time-steps
    # FIXME: Make sure all variables are in matrix form
    for t in range(8760):
        if t == 0:
            T_node = buildings.T_supply_DC   # assume substation target supply T as initial supply temperature in the network
            T_return_all, mass_flow_substations = substation.substation_return_model_main(locator, building_names, gv, buildings,
                                                                       substations_HEX_specs, T_node, t)

            # solve hydraulic equations
            calc_hydraulic_network()

            # solve thermal equations, with mass_flow_df from hydraulic calculation as input
            T_node = pipe_thermal_calculation(locator, gv, weather_file, edge_node_df, mass_flow_df, mass_flow_substations)
            # FIXME: save T_node at each time-step

        else:
            # with the temperature of previous time-step, solve for substation flow rates at current time-step
            T_node = T_node[t-1]
            T_return_all, mass_flow_substations = substation.substation_return_model_main(locator, building_names, gv, buildings,
                                                                       substations_HEX_specs, T_node, t)

            # solve hydraulic equations
            calc_hydraulic_network()

            # solve thermal equations, with mass_flow_df from hydraulic calculation as input
            T_node = pipe_thermal_calculation(locator, gv, weather_file, edge_node_df, mass_flow_df, mass_flow_substations)


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
            consumer_nodes = np.vstack((node_names, (node_data_df['Sink'] * node_data_df['Name']).values))
            plant_nodes = np.vstack((node_names, (node_data_df['Plant'] * node_data_df['Name']).values))

            # get pipe data and create edge-node matrix
            pipe_data_df = pd.read_csv(locator.get_pipes_DH_network)
            list_pipes = pipe_data_df['DC_ID']
            list_nodes = sorted(set(pipe_data_df['NODE1']).union(set(pipe_data_df['NODE2'])))
            edge_node_matrix = np.zeros((len(list_nodes), len(list_pipes)))
            for j in range(len(list_pipes)):
                for i in range(len(list_nodes)):
                    if pipe_data_df['NODE2'][j] == list_nodes[i]:
                        edge_node_matrix[i][j] = 1
                    elif pipe_data_df['NODE1'][j] == list_nodes[i]:
                        edge_node_matrix[i][j] = -1
            edge_node_df = pd.DataFrame(data=edge_node_matrix, index=list_nodes, columns=list_pipes)

            edge_node_df.to_csv(locator.pathNtwLayout + '//' + 'EdgeNode_DH.csv')

            print time.clock() - t0, "seconds process time for Network summary\n"

            return edge_node_df, pd.DataFrame(data=[consumer_nodes[1][:], plant_nodes[1][:]],
                                              index=['consumer', 'plant'], columns=consumer_nodes[0][:])

#===========================
# Hydraulic calculation
#===========================

def calc_hydraulic_network(locator, gv):
    '''
    This function carries out the steady-state hydraulic calculation for a predefined network with predefined mass flow
    rate on each edge.

    :param locator: locator class
    :param gv: globalvariables class

    :return: mass_flow: (t x e) matrix specifying the mass flow rate at each edge e at each time step t
    :return: pressure_loss_node: (t x n) matrix specifying the mass flow rate at each edge e at each time step t
    :return: pressure_loss_system: vector specifying the total pressure losses in the system at each time step t
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
    temperature_matrix = np.ones(mass_flow_df.shape)*323   # assigning a dummy temperature to each edge for now

    pressure_loss_nodes_df = pd.DataFrame(data=calc_pressure_loss_nodes(edge_node_df.values, pipe_properties_df[:]['DN':'DN'].values,
                                       pipe_length_df.values, mass_flow_df.values, temperature_matrix, gv),
                                       index = range(8760), columns = edge_node_df.index.values)

    pressure_loss_system = 2 * [sum(pressure_loss_nodes_df.values[i] for i in range(len(pressure_loss_nodes_df.values[0])))]

    return mass_flow_df, pressure_loss_system



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

    :param: mass_flow_df: dataframe containing the mass flow rate for each edge e at each time of the year t
    :param: locator: locator class
    :param: gv: globalvars

    :return: pipe_properties_df: dataframe containing the pipe properties for each edge in the network
    '''

    # import pipe catalog from Excel file
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

def calc_pressure_loss_nodes(edge_node, pipe_diameter, pipe_length, mass_flow_rate, temperature, gv):
    ''' calculates the pressure losses at each node as the sum of the pressure losses in all edges that point to each
     node
        edge_node: matrix consisting of n rows (number of nodes) and e columns (number of edges) and indicating
direction of flow of each edge e at node n: if e points to n, value is 1; if e leaves node n, -1; else, 0.  (n x e)
        :param: pipe_diameter: vector containing the pipe diameter in m for each edge e in the network      (e x 1)
        :param: pipe_length: vector containing the length in m of each edge e in the network                (e x 1)
        :param: mass_flow_rate: matrix containing the mass flow rate in each edge e at time t               (t x e)
        :param: temperature: matrix containing the temperature of the water in each edge e at time t        (t x e)
        :param: gv: globalvars

     :return: pressure loss at each node for each time t                                                    (t x n)
     '''

    # get the pressure through each edge
    pressure_loss_pipe = calc_pressure_loss_pipe(pipe_diameter, pipe_length, mass_flow_rate, temperature, gv)

    # get a matrix showing which edges point to each node n
    edge_node = edge_node.transpose()
    for i in range(len(edge_node)):
        for j in range(len(edge_node[0])):
            if edge_node[i][j] < 0:
                edge_node[i][j] = 0

    # the pressure losses at time t are calculated as the sum of the pressure losses from all edges pointing to node n
    return np.dot(pressure_loss_pipe, edge_node)


def calc_pressure_loss_pipe(pipe_diameter, pipe_length, mass_flow_rate, temperature, gv):
    ''' calculates the pressure losses throughout a pipe based on the Darcy-Weisbach equation and the Swamee-Jain
    solution for the Darcy friction factor

     :param: pipe_diameter: vector containing the pipe diameter in m for each edge e in the network (e x 1)
     :param: pipe_length: vector containing the length in m of each edge e in the network           (e x 1)
     :param: mass_flow_rate: matrix containing the mass flow rate in each edge e at time t          (t x e)
     :param: temperature: matrix containing the temperature of the water in each edge e at time t   (t x e)
     :param: gv: globalvars

     :return: pressure loss through each edge
     '''

    kinematic_viscosity = calc_kinematic_viscosity(temperature)
    reynolds = 4*mass_flow_rate/(math.pi * kinematic_viscosity * pipe_diameter)
    pipe_roughness = 0.02    # assumed from Li & Svendsen for now
    darcy = 1.325 * np.log(pipe_roughness / (3.7 * pipe_diameter) + 5.74 / reynolds ** 0.9) ** (-2)  # Swamee-Jain equation to calculate the Darcy-Weisbach friction factor
    pressure_loss_edge = darcy*8/(math.pi*gv.gr)*kinematic_viscosity**2/pipe_diameter**5*pipe_length

    return pressure_loss_edge

def calc_kinematic_viscosity(temperature):
    ''' calculates the kinematic viscosity of water as a function of temperature based on a simple fit from data from the
     engineering toolbox
     :param: temperature: in K

     :return: kinematic viscosity in m2/s
     '''
    return 2.652623e-8*math.e**(557.5447*(temperature-140)**-1)


#===========================
# Thermal calculation
#===========================

def pipe_thermal_calculation(locator, gv, weather_file, edge_node_df, mass_flow_df, substation_mass_flow_df):
    """
    This function solve for the node temperature with known mass flow rate in pipes and substation mass flow rate

    :param locator:
    :param gv:
    :param weather_file:
    :param edge_node_df:
    :param mass_flow_df:
    :param substation_mass_flow_df:
    :return:

    Reference
    ==========
    J. Wang, A method for the steady-state thermal simulation of district heating systems and model parameters
    calibration. Energy Conversion and Management, 2016
    """
    Z = edge_node_df.as_matrix()   #edge-node matrix
    Z_minus = -Z
    Z_minus_T = Z_minus.transpose()
    M_d = np.diag(mass_flow_df[1])  #mass flow diagonal matrix
    K = calc_aggregated_heat_conduction_coefficient(locator,gv,L_pipe=10)  # aggregated heat condumtion coef matrix #TODO: [SH] import pipe property (length and diameter)
    M_sub = substation_mass_flow_df     # substation mass flow matrix

    T_ambient = epwreader.epw_reader(weather_file)['drybulb_C']
    T_ground = geothermal.calc_ground_temperature(T_ambient.values, gv)
    network_depth = 1 #TODO: [SH] add to gv

    T_in, T_out = calc_pipe_temperature(Z, M_d, K, Z_minus, Z_minus_T, M_sub, T_ground, network_depth)

    return T_out

def calc_pipe_temperature(Z, M_d, K, Z_minus, Z_minus_T, M_sub, T_ground, network_depth):

    a1 = (gv.Cpw*Z*M_d)/(gv.Cpw*M_d + K/2)
    a2 = gv.Cpw*M_d*Z_minus_T-K*Z_minus_T/2
    a3 = gv.Cpw*Z_minus*M_d*Z_minus_T
    a4 = M_sub - a1*K*T_ground - network_depth
    T_node = a4/(a1+a2+a3)

    b1 = 1/(gv.Cpw*M_d + K/2)
    b2 = a2*T_node + K*T_ground
    T_out = b1*b2

    T_in = Z_minus_T*T_node
    return T_in, T_out

def calc_aggregated_heat_conduction_coefficient(locator, gv, L_pipe):
    thermal_conductivity_pipe = 0.001
    thermal_conductivity_ground = 0.0001
    network_depth = 1
    pipe_id = 0.02
    pipe_od = 0.023
    extra_heat_transfer_coef = 0.002

    R_pipe = np.log(pipe_od/pipe_id)/(2*math.pi*thermal_conductivity_pipe)
    a = 2*network_depth/pipe_od
    R_ground = np.log(a+(a^2-1)^0.5)/(2*math.pi*thermal_conductivity_pipe)

    k = L_pipe*(1+extra_heat_transfer_coef)/(R_pipe+R_ground)
    return k

def match_substation_to_nodes(all_nodes, building_names, bui_df):
    node_df = pd.DataFrame()
    for node in all_nodes:  # consumer_nodes+plant_nodes:    #name in building_names:
        a = all_nodes[node]['consumer']
        if all_nodes['%s'%node].ix['consumer'] != '':
            bui_name = list(building_names).index(all_nodes[node]['consumer'])
            node_df[node] = bui_df[bui_name]
        elif all_nodes['%s'%node].ix['plant'] != '':
            node_df[node] = bui_df[list(building_names).index(all_nodes['%s'%node].ix['plant'])]
        else:
            node_df[node] = 0
    return node_df

# TODO: [SH] do the pipe thermal calculation for return line

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


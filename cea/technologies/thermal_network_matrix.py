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
import os
from scipy.linalg import block_diag
import scipy


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
    # calculate ground temperature
    weather_file = locator.get_default_weather()
    T_ambient = epwreader.epw_reader(weather_file)['drybulb_C']
    T_ground = geothermal.calc_ground_temperature(T_ambient.values, gv)

    # substation HEX design
    substations_HEX_specs, buildings = substation.substation_HEX_design_main(locator, total_demand, building_names, gv)

    # get edge-node matrix from defined network
    edge_node_df, all_nodes_df, pipe_length_df = get_thermal_network_from_csv(locator)

    # Start solving hydraulic and thermal equations at each time-steps

    # TODO: [SH] Implement flexible time-steps
    # max_time_step = min(pipe_length_df)/v_max # determine the calculation time-step according to the shortest pipe and the maximum allowable speed
    # annual_time_step = 8760*3600/max_time_step  #

    consumer_heat_requirement = read_from_buildings(building_names, buildings, 'Q_substation_heating')   # [kWh]
    consumer_heat_requirement_nodes_df = write_df_to_consumer_nodes_df(all_nodes_df, consumer_heat_requirement, flag = False)
    t_target_supply = read_from_buildings(building_names, buildings, 'T_sup_target_DH')

    mass_flow_substations_nodes_df = []
    T_DH_return_nodes_df = []

    for t in range(8760):   # TODO: [SH] change to annual total time-steps
        if t == 0:
            # set initial substation mass flow for all consumers
            T_DH_0 = t_target_supply.ix[t]
            T_DH_return_all, mdot_DH_all = substation.substation_return_model_main(locator, building_names, gv,
                                                                                   buildings, substations_HEX_specs,
                                                                                   T_DH_0, t=0)  #[C], [kg/s]

            # write consumer substation return T and required flow to nodes
            T_DH_return_nodes_df = write_df_to_consumer_nodes_df(all_nodes_df, T_DH_return_all, flag = True)  # (1xn)
            mass_flow_substations_nodes_df = write_df_to_consumer_nodes_df(all_nodes_df, mdot_DH_all, flag = False)  # (1xn)
            # write plant substation required flow to nodes
            mass_flow_substations_nodes_df[(all_nodes_df.ix['plant']!= '').argmax()]= mass_flow_substations_nodes_df.sum(axis=1)  # (1xn) # assume only one plant supply all consumer flow rate #FIXME: 1] all the flow rates are positive now, feel free to adjust

            # solve hydraulic equations # FIXME? calc_mass_flow_edges now consists of just one line of code! should we just move it here?
            mass_flow_df = pd.DataFrame(data=np.zeros((8760,len(edge_node_df.columns.values))), columns=edge_node_df.columns.values)
            mass_flow_df[:][t:t+1] = calc_mass_flow_edges(edge_node_df, mass_flow_substations_nodes_df)

            #mass_flow_df = np.absolute(mass_flow_df)  # added this hack to make sure code runs

            # solve thermal equations, with mass_flow_df from hydraulic calculation as input
            T_node = pipe_thermal_calculation(locator, gv, T_ground[t], edge_node_df, all_nodes_df, mass_flow_df.ix[t],
                                              consumer_heat_requirement_nodes_df.ix[t], mass_flow_substations_nodes_df,
                                              pipe_length_df, t_target_supply.ix[t])

            # TODO: [SH] save T_node at each time-step

        else:
            # with the temperature of previous time-step, solve for substation flow rates at current time-step
            T_supply_consumer = T_node[t-1]
            T_return_all, mass_flow_substations = substation.substation_return_model_main(locator, building_names, gv, buildings,
                                                                       substations_HEX_specs, T_supply_consumer, t)

            # solve hydraulic equations
            mass_flow_df[:][t:t+1] = calc_mass_flow_edges(edge_node_df, all_nodes_df, pipe_length_df, mass_flow_substations_nodes_df, locator, gv)

            # solve thermal equations, with mass_flow_df from hydraulic calculation as input
            T_node = pipe_thermal_calculation(locator, gv, weather_file, edge_node_df, mass_flow_df, mass_flow_substations)

    # this was included in the calc_hydraulic_network in order to check the results. its use in the future optional, though.
    mass_flow_df.to_csv(locator.pathNtwLayout + '//' + 'MassFlow_DH.csv')

    # assign pipe properties to each edge in the network (since we don't have this information for the current network at the moment)
    pipe_properties_df = assign_pipes_to_edges(mass_flow_df, locator, gv)

    # assigning a dummy temperature matrix that defines the temperature at each edge at each timestem #TODO: incorporate results of real temperature calculation
    temperature_matrix_supply = np.ones(mass_flow_df.shape)*323   # assigning a dummy temperature to each edge for now
    temperature_matrix_return = np.ones(mass_flow_df.shape) * 303  # assigning a dummy temperature to each edge for now

    # calculate pressure losses at each node
    pressure_loss_nodes_supply_df = pd.DataFrame(
        data=calc_pressure_loss_nodes(edge_node_df.values, pipe_properties_df[:]['DN':'DN'].values,
                                      pipe_length_df.values, mass_flow_df.values, temperature_matrix, gv),
        index=range(8760), columns=edge_node_df.index.values)
    pressure_loss_nodes_return_df = pd.DataFrame(
        data=calc_pressure_loss_nodes(-(edge_node_df.values), pipe_properties_df[:]['DN':'DN'].values,
                                      pipe_length_df.values, mass_flow_df.values, temperature_matrix, gv),
        index=range(8760), columns=edge_node_df.index.values)

    #calculate total pressure loss in the system
    pressure_loss_system = [sum(pressure_loss_nodes_supply_df.values[i] for i in range(len(pressure_loss_nodes_supply_df.values[0])))] + \
                           [sum(pressure_loss_nodes_return_df.values[i] for i in range(len(pressure_loss_nodes_return_df.values[0])))]

def write_df_to_consumer_nodes_df(all_nodes_df, df_value, flag):
    nodes_df = pd.DataFrame()
    for node in all_nodes_df:  # consumer_nodes+plant_nodes:    #name in building_names:
        if all_nodes_df[node]['consumer'] != '':
            nodes_df[node] = df_value[all_nodes_df[node]['consumer']]
        # elif all_nodes_df[node]['plant'] != '':
        #     nodes_df[node] = df_value[all_nodes_df[node]['plant']]
        else:
            if flag== True:
                nodes_df[node] = np.nan
            else:
                nodes_df[node] = 0
    return nodes_df

#===========================
# Hydraulic calculation
#===========================
def calc_mass_flow_edges(edge_node_df, mass_flow_substation_df):
    '''
    This function carries out the steady-state mass flow rate calculation for a predefined network with predefined mass
    flow rates at each substation.

    :param locator: locator class
    :param gv: globalvariables class

    :return: mass_flow: (1 x e) vector specifying the mass flow rate at each edge e at the given time step t
    '''

    '''
    ============
    This part of the code is obsolete since the edge_node_matrix is already imported before the time step calculation.
    Preserved since I cannot test the function now, but could be deleted as soon as I can verify this.
    ============

    # get mass flow matrix from substation.py
    edge_node_df, all_nodes_df, pipe_length_df = get_thermal_network_from_csv(locator)
        #
        # edge_node_matrix needs to be expanded to include return pipes
        for pipe in edge_node_df:
            edge_node_df['-'+pipe] = -edge_node_df[pipe]
        #
    '''

    '''
    ============
    This part of the code is obsolete since we now have the correct edge flow calculation.
    Preserved since I cannot test the function now, but could be deleted as soon as I can verify this.
    ============
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

    # t0 = time.clock()
    mass_flow = np.transpose(np.linalg.lstsq(edge_node_df.values, np.transpose(-mass_flow_substation_df.values))[0])
    # print time.clock() - t0, "seconds process time for total mass flow calculation\n"

    '''
    ============
    This part of the code imports previously exported results in order to speed up the calculation during testing.
    Preserved in case we need it again for testing later, but can be deleted otherwise.
    ============
    mass_flow_df = pd.read_csv(locator.pathNtwLayout + '//' + 'MassFlow_DH.csv', usecols=edge_node_df.columns.values)
    mass_flow_df = np.absolute(mass_flow_df)    # added this hack to make sure code runs TODO: make sure you don't get negative flows!
    '''

    return mass_flow

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

def pipe_thermal_calculation(locator, gv, T_ground, edge_node_df, all_nodes_df, mass_flow_df, consumer_heat_requiremt, mass_flow_substation_df, pipe_length_df, t_target_supply):
    """
    This function solve for the node temperature with known mass flow rate in pipes and substation mass flow rate at each time-step.

    :param locator:
    :param gv:
    :param weather_file:
    :param edge_node_df: matrix consisting of n rows (number of nodes) and e columns (number of edges) and indicating
direction of flow of each edge e at node n: if e points to n, value is 1; if e leaves node n, -1; else, 0.  (n x e)
    :param mass_flow_df: matrix containing the mass flow rate in each edge e at time t               (1 x e)
    :param mass_flow_substation_df: mass flow rate through each node (1 x n)
    :return:

    Reference
    ==========
    J. Wang, A method for the steady-state thermal simulation of district heating systems and model parameters
    calibration. Energy Conversion and Management, 2016
    """
    Z = edge_node_df.as_matrix()   # (nxe) edge-node matrix
    Z_pipe_out = np.dot(-1,Z.clip(max=0))
    Z_pipe_in = Z.clip(min=0)
    Z_pipe_out_T = np.transpose(Z_pipe_out)
    M_sub = np.diag(mass_flow_substation_df.as_matrix()[0])  # (nxn)  [kg/s] # substation mass flow rate matrix
    M_sub_cp = np.dot(gv.Cpw, M_sub)   #[kW/K]

    consumer_node = np.where(all_nodes_df.ix['consumer']!='', 1, 0)      # make (n x 1) consumer node matrix
    plant_node = np.where(all_nodes_df.ix['plant'] != '', 1, 0)      # make (n x 1) plant node matrix

    M_d = np.diag(mass_flow_df.as_matrix())  # (exe) pipe mass flow diagonal matrix #TODO: check unit is [kg/s]
    K = calc_aggregated_heat_conduction_coefficient(locator,gv, pipe_length_df)/1000 # (exe) # aggregated heat condumtion coef matrix [kW/K] #TODO: [SH] import pipe property (length and diameter)

    T_ground_matrix = pd.Series([i*0+T_ground for i in range(len(pipe_length_df))])  # (ex1) [K]
    T_required = np.dot(273 + 65, consumer_node)    # (nx1) [K]

    # preparing matrices for calculation
    # Z_out_in = np.hstack((Z_pipe_out, Z_pipe_in))
    # M_d_2 = block_diag(M_d*gv.Cpw , M_d*gv.Cpw)  # (2e x 2e) [kW/K]
    # Z_M_d_2 = np.dot(Z_out_in,M_d_2)   # (n x 2e) [kW/K]
    U = consumer_heat_requiremt/3600   #(nx1) [kW]   #TODO: maybe don't fix?
    # M_d_cp_1 = np.dot(M_d, gv.Cpw)- np.dot(K,1/2)   # (exe)  [kW/K]
    # M_d_cp_2 = -1*(np.dot(M_d, gv.Cpw) + np.dot(K, 1 / 2))  # (exe)  [kW/K]
    # M_d_cp_K = np.hstack((M_d_cp_1, M_d_cp_2))  # (e x 2e) [kW/K]
    # T_g_K = (np.dot(T_ground_matrix,K).dot(-1))
    # # substation = (U - H).values
    # # b = np.hstack((substation,T_g_K)).T # (n+e)x1


    # preparing matrices for calculation
    # M_d_cp = M_d_cp*gv.Cpw  # (e x e)
    # Zout_mcp = np.dot(Z_pipe_out,M_d_cp)    # (n x e)
    # Zin_mcp = np.dot(Z_pipe_in,M_d_cp)  # (n x e)
    # Zout_Zin = np.hstack((Zout_mcp,Zin_mcp))    # (n x 2e)
    # Zout_Zin_M_sub = np.hstack((Zout_Zin, M_sub_cp))  #(n x (2e+n))
    #
    # Md_cp_K_1 = M_d_cp-K/2  # (e x e)
    # Md_cp_K_2 = (-1)*( M_d_cp + K / 2)  # (e x e)
    # Md_cp_K = np.hstack((Md_cp_K_1, Md_cp_K_2)) # (e x 2e)
    # zeros = np.zeros((edge_node_df.shape[1], edge_node_df.shape[0]))
    # Md_cp_K_zeros = np.hstack((Md_cp_K, zeros)) # (e x (2e+n))
    #
    # zeros = np.zeros((edge_node_df.shape[1], edge_node_df.shape[1]))
    # I = np.zeros((edge_node_df.shape[1], edge_node_df.shape[1]))
    # np.fill_diagonal(I,1)
    # Z_pipe_in_T = Z_pipe_in.T
    # zeros_I = np.hstack((zeros, I))
    # zeros_I_Zpipe_in = np.hstack((zeros_I, Z_pipe_in_T))
    #
    # zeros_array = np.zeros((edge_node_df.shape[1]))
    # T_g_K = (np.dot(T_ground_matrix, K).dot(-1))

    # start solving node and pipe outlet temperatures
    print 'start calculating T_node...'
    flag = 0
    T_H = max(t_target_supply)+273 #[K] # determine min T_source

    while flag == 0:
        H = np.dot(M_sub_cp, plant_node).dot(T_H).dot(-1)  #(n x 1)# calculate heat input matrix [kW]
        # cp* Z_pipe_out * M_d * T_pipe_out + H = cp* Z_pipe_in * M_d * T_pipe_in + U

        T_node = calc_pipe_temperature(gv, Z_pipe_in, M_d, K, Z_pipe_out, Z_pipe_out_T, U, H, T_ground_matrix )
        # check if matrix is linear independent
        # pl, u =  scipy.linalg.lu(a, permute_l=True)

        # T_all = np.linalg.solve(a,b) #FIXME: [SH] error singular matrix
        # T_all = scipy.sparse.linalg.spsolve(a,b) # another solver

        # try to solve with least square method
        # T_out_in, residual, rank, s = np.linalg.lstsq(a, b)
        if T_node[:]:
            T_H = T_H + 0.1
        else:
            flag = 1
    return T_node

def calc_pipe_temperature(gv, Z_pipe_in, M_d, K, Z_pipe_out, Z_pipe_out_T, U, H, T_ground):
    '''
    Calculates the node temperature based on Wang et al. equation 12
    T_Node = [c * Z_pipe_in * M_d * (c * M_d + K/2)^-1 * (c * M_d * Z_pipe_out_T - K/2 * Z_pipe_out_T) - c * Z_pipe_out * M_d * Z_pipe_out_T]^-1
                * [U - c * Z_pipe_in * M_d * (c * M_d + K/2)^-1 * K * T_ground - H]
    a1 = c * Z_pipe_in * M_d * (c * M_d + K/2)^-1
    a2 = c * M_d * Z_pipe_out_T - K/2 * Z_pipe_out_T
    a3 = c * Z_pipe_out * M_d * Z_pipe_out_T
    a4 = U - c * Z_pipe_in * M_d * (c * M_d + K/2)^-1 * K * T_ground - H

    T_Node = [(a1 * a2) - a3]^-1 * a4
    '''

    a1 = np.dot(gv.Cpw, Z_pipe_in).dot(M_d).dot(np.linalg.inv(np.dot(gv.Cpw, M_d) + np.dot( K, 1/2 )))
    a2 = np.dot(gv.Cpw, M_d).dot(Z_pipe_out_T) - np.dot( K, 1/2 ).dot(Z_pipe_out_T)
    a3 = np.dot(gv.Cpw,Z_pipe_out).dot(M_d).dot(Z_pipe_out_T)
    a4 = U - np.dot(a1, K).dot(T_ground) - H
    T_node = np.dot(np.linalg.inv(np.dot(a1, a2) - a3), a4)  #FIXME: The inverse is singular matrix

    # b1 = 1/(gv.Cpw*M_d + K/2)
    # b2 = a2*T_node + K*T_ground
    # T_out = b1*b2
    #
    # T_in = Z_minus_T*T_node
    return T_node

def calc_aggregated_heat_conduction_coefficient(locator, gv, L_pipe):
    """

    :param locator:
    :param gv:
    :param L_pipe:
    :return:
     K matrix (1 x e) for all edges
    """
    # TODO [SH]: load pipe id, od, thermal conductivity, and ground thermal conductivity, and define network_depth, extra_heat_transfer_coef in gv
    thermal_conductivity_pipe = 0.025     # [W/mC]
    thermal_conductivity_ground = 1.75    # [W/mC]
    network_depth = 1                     # [m]
    pipe_id = 0.1107                      # [m]
    pipe_od = 0.1143                      # [m]
    extra_heat_transfer_coef = 0.2

    K_all = []
    for edge in range(len(L_pipe)):
        R_pipe = np.log(pipe_od/pipe_id)/(2*math.pi*thermal_conductivity_pipe)     #[mC/W]
        a= 2*network_depth/pipe_od
        R_ground = np.log(a+(a**2-1)**0.5)/(2*math.pi*thermal_conductivity_ground) #[mC/W]
        k = L_pipe[edge]*(1+extra_heat_transfer_coef)/(R_pipe+R_ground)   #[W/C]
        K_all.append(k)
        edge += 1

    K_all = np.diag(K_all)
    return K_all

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

def read_from_buildings(building_names, buildings, column):
    property_df = pd.DataFrame(index=range(8760), columns= building_names)
    for name in building_names:
        property = buildings[(building_names == name).argmax()][column]
        property_df[name] = property
    return property_df

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

    #calc_hydraulic_network(locator, gv)
    # print 'test calc_hydraulic_network() succeeded'

    thermal_network_main(locator,gv)
    print 'test thermal_network_main() succeeded'

if __name__ == '__main__':
    run_as_script()


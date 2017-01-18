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
import geopandas as gpd


__author__ = "Martin Mosteiro, Shanshan Hsieh"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Martin Mosteiro", "Shanshan Hsieh" ]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def thermal_network_main(locator, gv, shapefile_flag):
    """
    See Thermo-hydraulic modelling procedures for DHC Networks
    :param locator:
    :param gv:
    :param shapefile_flag: Boolean set to True if the source for the data is a shapefile, False if it is a csv
    :return:
    """

    ## prepare data for calculation

    # read building names
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand['Name']

    # calculate ground temperature
    weather_file = locator.get_default_weather()
    T_ambient = epwreader.epw_reader(weather_file)['drybulb_C']
    T_ground = geothermal.calc_ground_temperature(T_ambient.values, gv)

    # substation HEX design
    substations_HEX_specs, buildings_demands = substation.substation_HEX_design_main(locator, total_demand,
                                                                                     building_names, gv)

    # get hourly heat requirement and target supply temperature from each substation
    t_target_supply = read_properties_from_buildings(building_names, buildings_demands, 'T_sup_target_DH')

    # get edge-node matrix from defined network
    if shapefile_flag == False:
        edge_node_df, all_nodes_df, pipe_length_df = get_thermal_network_from_csv(locator)
    else:
        edge_node_df, all_nodes_df, pipe_length_df = get_thermal_network_from_shapefile(locator, gv, t_target_supply,
                                                            building_names, buildings_demands, substations_HEX_specs)

    # create target supply temperature dataframe
    t_target_supply_df = write_substations_to_nodes_df(all_nodes_df, t_target_supply, flag= True)  #(1xn)


    ## assign pipe properties

    # calculate maximum edge mass flow
    edge_mass_flow_df, max_edge_mass_flow_df = calc_max_edge_flowrate(all_nodes_df, building_names, buildings_demands,
                                                                      edge_node_df, gv, locator, substations_HEX_specs,
                                                                      t_target_supply)

    # assign pipe id/od according to maximum edge mass flow
    pipe_properties_df = assign_pipes_to_edges(max_edge_mass_flow_df, locator, gv)

    # calculate pipe aggregated heat conduction coefficient
    K = calc_aggregated_heat_conduction_coefficient(locator, gv, pipe_length_df, pipe_properties_df)#(exe) [kW/K]


    ## Start solving hydraulic and thermal equations at each time-step
    t0 = time.clock()
    # create empty lists to write results
    T_DH_return_nodes = []
    T_DH_supply_nodes = []
    plant_heat_requiremnts = []

    for t in range(8760):
        print('calculating network thermal hydraulic properties... timestep'),t
        timer = time.clock()

        ## solve network temperatures
        T_supply_nodes, \
        T_return_nodes, \
        plant_heat_requirement = solve_network_temperatures(locator, gv, T_ground, edge_node_df, all_nodes_df,
                                                             edge_mass_flow_df.loc[t], K, t_target_supply_df,
                                                             building_names, buildings_demands, substations_HEX_specs, t)

        # store node temperatures and plant heat requirement at each time-step
        T_DH_supply_nodes.append(T_supply_nodes)
        T_DH_return_nodes.append(T_return_nodes)
        plant_heat_requiremnts.append(plant_heat_requirement)

        print time.clock() - timer, "seconds process time for timestep \n",t

    # save results
    pd.DataFrame(T_DH_supply_nodes, columns=edge_node_df.index).\
        to_csv(locator.get_optimization_network_layout_supply_temperature_file(), index=False, float_format='%.3f')
    pd.DataFrame(T_DH_return_nodes, columns=edge_node_df.index).\
        to_csv(locator.get_optimization_network_layout_return_temperature_file(), index=False, float_format='%.3f')
    # pd.DataFrame(plant_heat_requiremnts).\
    #     to_csv(locator.get_optimization_network_layout_plant_heat_requirement_file(), index=False, float_format='%.3f') #FIXME[SH]: save to csv

    # calculate pressure losses
    ## pressure losses at each node
    pressure_loss_nodes_supply_df, pressure_loss_nodes_return_df = calc_pressure_loss_nodes(edge_node_df,
                                    pipe_properties_df[:]['DN':'DN'].values, pipe_length_df.values,
                                    edge_mass_flow_df.values, T_DH_supply_nodes, T_DH_return_nodes, gv)

    ## total pressure loss in the system # TODO[MM, SH]: how should we output these results in our script?
    pressure_loss_system = [sum(pressure_loss_nodes_supply_df.values[i] for i in range(len(pressure_loss_nodes_supply_df.values[0])))] + \
                           [sum(pressure_loss_nodes_return_df.values[i] for i in range(len(pressure_loss_nodes_return_df.values[0])))]

    print time.clock() - t0, "seconds process time for network thermal-hydraulic calculation \n"


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
    mass_flow_edge = np.round(np.transpose(np.linalg.lstsq(edge_node_df.values, np.transpose(mass_flow_substation_df.values))[0]), decimals = 9)
    # print time.clock() - t0, "seconds process time for total mass flow calculation\n"

    '''
    ============
    This part of the code imports previously exported results in order to speed up the calculation during testing.
    Preserved in case we need it again for testing later, but can be deleted otherwise.
    ============
    mass_flow_df = pd.read_csv(locator.pathNtwLayout + '//' + 'MassFlow_DH.csv', usecols=edge_node_df.columns.values)
    mass_flow_df = np.absolute(mass_flow_df)    # added this hack to make sure code runs TODO: make sure you don't get negative flows!
    '''

    return mass_flow_edge

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
    pipe_properties_df = pd.DataFrame( data = None, index = pipe_catalog.columns.values, columns = mass_flow_df.columns.values)
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

def calc_pressure_loss_nodes(edge_node_df, pipe_diameter, pipe_length, mass_flow_rate, T_supply_node, T_return_node, gv):
    ''' calculates the pressure losses at each node as the sum of the pressure losses in all edges that point to each
     node
        edge_node_df: dataframe consisting of n rows (number of nodes) and e columns (number of edges) and indicating
direction of flow of each edge e at node n: if e points to n, value is 1; if e leaves node n, -1; else, 0.  (n x e)
        :param: pipe_diameter: vector containing the pipe diameter in m for each edge e in the network      (e x 1)
        :param: pipe_length: vector containing the length in m of each edge e in the network                (e x 1)
        :param: mass_flow_rate: matrix containing the mass flow rate in each edge e at time t               (t x e)
        :param: T_supply_node: matrix containing the temperature in each supply node e at time t            (t x e)
        :param: T_return_node: matrix containing the temperature in each return node e at time t            (t x e)
        :param: gv: globalvars

     :return: pressure loss at each supply and return node for each time t                                  (t x n)
     '''

    # get the temperatures at each supply and return edge
    temperature_supply_edges = calc_edge_temperatures(T_supply_node, edge_node_df.values)
    temperature_return_edges = calc_edge_temperatures(T_return_node, edge_node_df.values)

    # get the pressure through each edge
    pressure_loss_pipe_supply = calc_pressure_loss_pipe(pipe_diameter, pipe_length, mass_flow_rate, temperature_supply_edges, gv)
    pressure_loss_pipe_return = calc_pressure_loss_pipe(pipe_diameter, pipe_length, mass_flow_rate, temperature_return_edges, gv)

    # get a matrix showing which edges point to each node n
    edge_node = edge_node_df.values.transpose()
    for i in range(len(edge_node)):
        for j in range(len(edge_node[0])):
            if edge_node[i][j] < 0:
                edge_node[i][j] = 0

    # the pressure losses at time t are calculated as the sum of the pressure losses from all edges pointing to node n
    pressure_loss_nodes_supply_df = pd.DataFrame(np.dot(pressure_loss_pipe_supply, edge_node), index=range(8760), columns=edge_node_df.index.values)
    pressure_loss_nodes_return_df = pd.DataFrame(np.dot(pressure_loss_pipe_return, -edge_node), index=range(8760), columns=edge_node_df.index.values)

    return pressure_loss_nodes_supply_df, pressure_loss_nodes_return_df

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

def calc_max_edge_flowrate(all_nodes_df, building_names, buildings_demands, edge_node_df, gv, locator,
                           substations_HEX_specs, t_target_supply):
    # create empty dataframes to store results
    edge_mass_flow_df = pd.DataFrame(data=np.zeros((8760, len(edge_node_df.columns.values))),
                                     columns=edge_node_df.columns.values)
    print('start calculating edge mass flow...')
    t0 = time.clock()
    for t in range(8760):
        print('calculating edge mass flow... timestep'), t

        # solve mass flow rates on edges
        edge_mass_flow_df[:][t:t + 1] = calc_one_timestep(t_target_supply,locator, gv, building_names, buildings_demands,
                                              substations_HEX_specs, t, all_nodes_df, edge_node_df)

    edge_mass_flow_df.to_csv(locator.get_optimization_network_layout_folder() + '//' + 'NominalEdgeMassFlow_DH.csv')
    edge_mass_flow_df = pd.read_csv(
        locator.get_optimization_network_layout_folder() + '//' + 'NominalEdgeMassFlow_DH.csv')
    print time.clock() - t0, "seconds process time for edge mass flow calculation\n"
    # assign pipe properties based on max flow on edges
    max_edge_mass_flow = edge_mass_flow_df.max(asix=0)
    max_edge_mass_flow_df = pd.DataFrame(data=[max_edge_mass_flow], columns=edge_node_df.columns)

    return edge_mass_flow_df, max_edge_mass_flow_df

def calc_one_timestep(t_target_supply,locator, gv, building_names, buildings_demands, substations_HEX_specs, t,
                      all_nodes_df, edge_node_df):
    # set to the highest value in the network and assume no loss within the network
    T_substation_supply = t_target_supply.ix[t].max() + 273.15  # in [K]

    # calculate substation flow rates and return temperatures
    T_DH_return_all, \
    mdot_DH_all = substation.substation_return_model_main(locator, gv, building_names, buildings_demands,
                                                          substations_HEX_specs, T_substation_supply, t,
                                                          flag=True)  # flag = True: same temperature for all nodes

    # write consumer substation required flow rate to nodes
    df = write_substations_to_nodes_df(all_nodes_df, mdot_DH_all,
                                       flag=False)  # (1xn) #flag = True: writing temperature

    # solve mass flow rates on edges
    edge_mass_flow = calc_mass_flow_edges(edge_node_df, df)

    return edge_mass_flow

#===========================
# Thermal calculation
#===========================

def solve_network_temperatures(locator, gv, T_ground, edge_node_df, all_nodes_df, edge_mass_flow_df, K, t_target_supply_df,
                               building_names, buildings_demands, substations_HEX_specs, t):

    # # delete neglegible flowrates dur to inaccuracy of least square solver
    # edge_mass_flow_df[edge_mass_flow_df < 0.00001] = 0
    # NOTE: this is now done as part of the edge_mas_flow_df calculation

    if edge_mass_flow_df.values.sum()!= 0:
        T_supply_nodes, plant_node = calc_supply_temperatures(locator, gv, T_ground[t], edge_node_df, edge_mass_flow_df, K,
                                                              t_target_supply_df.loc[t])

        # write node supply temperatures to substations
        T_substation_supply = all_nodes_df.copy().drop('plant')
        T_substation_supply.loc['T_supply'] = T_supply_nodes
        T_substation_supply.columns = T_substation_supply.loc['consumer']
        T_substation_supply = T_substation_supply.drop('consumer')
        T_substation_supply = T_substation_supply.drop('', axis=1)
        plant_building = all_nodes_df.ix['plant', plant_node]
        T_substation_supply.loc['T_supply', plant_building]= T_supply_nodes[plant_node]

        # calculate substation return temperatures according to supply temperatures
        T_DH_return_all, \
        mdot_DH_all = substation.substation_return_model_main(locator, gv, building_names, buildings_demands,
                                                              substations_HEX_specs, T_substation_supply, t, flag = False)

        # write consumer substation return T and required flow rate to nodes
        T_DH_substation_return_df = write_substations_to_nodes_df(all_nodes_df, T_DH_return_all, flag=True)  # (1xn)
        mass_flow_substations_nodes_df = write_substations_to_nodes_df(all_nodes_df, mdot_DH_all, flag=False)
        # FIXME[SH]: iteration required to find the correct node and edge mass flow
        T_return_nodes = calc_return_temperatures(locator, gv, T_ground[t], edge_node_df, edge_mass_flow_df,
                                                   mass_flow_substations_nodes_df, K, T_DH_substation_return_df)
        # FIXME[SH]: testing required (check plant node return temperature at t=32)
        # TODO[SH]: change edge_mass_flow_df according to the updated node_mass_flow

        plant_heat_requiremnt = gv.Cpw * (T_supply_nodes[plant_node] - T_return_nodes[plant_node]) \
                                * abs(mass_flow_substations_nodes_df.values.T[plant_node])
    else:
        T_supply_nodes = []
        T_return_nodes = []
        plant_heat_requiremnt = 0

    return T_supply_nodes, T_return_nodes, plant_heat_requiremnt

def calc_supply_temperatures(locator, gv, T_ground, edge_node_df, mass_flow_df, K, t_target_supply):
    Z = np.asarray(edge_node_df)   # (nxe) edge-node matrix
    Z_pipe_out = Z.clip(min=0)     # pipe outlet matrix
    Z_pipe_in = Z.clip(max=0)      # pipe inlet matrix

    # M_sub = np.zeros((Z.shape[0],Z.shape[0]))    # (nxn) substation flow rate matrix
    # np.fill_diagonal(M_sub, mass_flow_substation_df)

    M_d = np.zeros((Z.shape[1],Z.shape[1]))   # (exe) pipe mass flow rate matrix
    np.fill_diagonal(M_d,mass_flow_df)

    #K = calc_aggregated_heat_conduction_coefficient(locator, gv, pipe_length_df, pipe_properties_df)/1000# (exe) # aggregated heat conduction coef matrix [kW/K]

    # matrices to store results
    T_e_out = Z_pipe_out.copy()
    T_e_in = Z_pipe_in.copy().dot(-1)
    T_node = np.zeros(Z.shape[0])
    Z_note = Z.copy()   # matrix to store information of solved nodes

    # start node temperature calculation
    flag = 0
    T_H_0 = 273 + t_target_supply.max()  # set initial supply temperature guess to the minimum required temperature at node
    T_H = T_H_0
    iteration = 0
    while flag == 0:
        # calculate the pipe outlet temperature from the plant node
        for i in range(Z.shape[0]):
            if np.count_nonzero(Z_note[i]==0) == (Z.shape[1]-1) and Z[i].sum() == -1:  # find plant node
                    # write plant inlet temperature
                    T_node[i] = T_H   # assume plant inlet temperature
                    edge = np.where(T_e_in[i]!=0)[0]   # find edge index
                    T_e_in[i] = T_e_in[i]*T_node[i]
                    # calculate pipe outlet temperature
                    calc_t_out(i, edge, K, M_d, Z, T_e_in, T_e_out, T_ground, Z_note, gv)
        plant_node = T_node.argmax()

        # calculate pipe outlet temperature and node temperature for the rest
        while np.count_nonzero(T_node==0) > 0:  #Z_note.max() >= 1:
            for j in range(Z.shape[0]):
                # check if all inlet flow info towards node j are known (only -1 left in row Z_note[j])
                if np.count_nonzero(Z_note[j] == 1) == 0 and np.count_nonzero(Z_note[j] == 0) != Z.shape[1]:
                    # calculate node temperature with merging flows from pipes
                    part1 = np.dot(M_d, T_e_out[j]).sum()
                    part2 = np.dot(M_d, Z_pipe_out[j]).sum()
                    T_node[j] = part1 / part2
                    # write the node temperature to the corresponding pipe inlet
                    T_e_in[j] = T_e_in[j] * T_node[j]
                    # calculate pipe outlet temperatures entering from node j
                    for edge in range(Z_note.shape[1]):
                        # find the pipes with water flow leaving from node j
                        if T_e_in[j, edge] != 0:
                            # calculate the pipe outlet temperature entering from node j
                            calc_t_out(j, edge, K, M_d, Z, T_e_in, T_e_out, T_ground, Z_note, gv)

                # fill in temperatures for nodes at network branch ends
                elif T_node[j] == 0 and T_e_out[j].max() != 1:
                    T_node[j] = T_e_out[j].max()
                elif T_e_out[j].min() < 0:
                    print('negative node temperature!')

        # evaluate if all node supply temperature reach the targets
        dT = (T_node - (t_target_supply + 273.15)).dropna()  # [K] temperature differences b/t node supply and target supply
        if all(dT > 0) is False and iteration < 40:
                # increase plant supply temperature and re-iterate the node supply temperature calculation
                T_H = T_H + 1  # TODO[SH]: add to global variable
                Z_note = Z.copy()
                T_e_out = Z_pipe_out.copy()
                T_e_in = Z_pipe_in.copy().dot(-1)
                T_node = np.zeros(Z.shape[0])
                iteration += 1
        elif all(dT > 0) is False and iteration >= 40: #FIXME[SH]:decide the method
            print ('cannot fulfill temperature requirement after iterations:'), iteration, dT
            node_insufficient = dT[dT<0].index.values
            for node in range(node_insufficient.size):
                index_insufficient = np.argwhere(edge_node_df.index == node_insufficient[node])[0]
                T_node[index_insufficient] = t_target_supply[index_insufficient] + 273.15
            flag = 1
        else:
            flag = 1
    return T_node.T, plant_node

def calc_return_temperatures(locator, gv, T_ground, edge_node_df, mass_flow_df, mass_flow_substation_df, K, t_return):
    Z = np.asarray(edge_node_df) *(-1)  # (nxe) edge-node matrix
    Z_pipe_out = Z.clip(min=0)     # pipe outlet matrix
    Z_pipe_in = Z.clip(max=0)      # pipe inlet matrix

    M_sub = np.zeros((Z.shape[0],Z.shape[0]))    # (nxn) substation flow rate matrix
    np.fill_diagonal(M_sub, mass_flow_substation_df)

    M_d = np.zeros((Z.shape[1],Z.shape[1]))   # (exe) pipe mass flow rate matrix
    np.fill_diagonal(M_d,mass_flow_df)

    #K = calc_aggregated_heat_conduction_coefficient(locator,gv, pipe_length_df)/1000 # (exe) # aggregated heat condumtion coef matrix [kW/K]

    # matrices to store results
    T_e_out = Z_pipe_out.copy()
    T_e_in = Z_pipe_in.copy().dot(-1)
    T_node = np.zeros(Z.shape[0])
    Z_note = Z.copy()   # matrix to store information of solved nodes

    # calculate the return pipe node temperature of substations locating at the end of the branch
    for i in range(Z.shape[0]):
            # choose the nodes locating at the end of the branches
            if np.count_nonzero(Z[i] == 1) == 0 and np.count_nonzero(Z[i] == 0) != Z.shape[1]:
                T_node[i] = t_return.values[0,i]
                #T_node[i] = map(list, t_return.values)[0][i]
                for edge in range(Z_note.shape[1]):
                    if T_e_in[i, edge] != 0:
                        T_e_in[i, edge] = map(list, t_return.values)[0][i]
                        # calculate pipe outlet
                        calc_t_out(i, edge, K, M_d, Z, T_e_in, T_e_out, T_ground, Z_note, gv)

    while Z_note.max() >= 1:
            for j in range(Z.shape[0]):
                if np.count_nonzero(Z_note[j] == 1) == 0 and np.count_nonzero(Z_note[j]==0) != Z.shape[1]:
                    # calculate node temperature with merging flows from pipes
                    T_node[j] = calc_return_node_temperature(j, M_d, T_e_out, t_return, Z_pipe_out, M_sub)
                    for edge in range(Z_note.shape[1]):
                        if T_e_in[j, edge]!=0:
                            T_e_in[j, edge]=T_node[j]
                            # calculate pipe outlet
                            calc_t_out(j, edge, K, M_d, Z, T_e_in, T_e_out, T_ground, Z_note, gv)

    # calculate temperature with merging flows from pipes at the plant node
    node_index = np.where(T_node == 0)[0].max()

    M_sub[node_index] = 0
    T_node[node_index] = calc_return_node_temperature(node_index, M_d, T_e_out, t_return, Z_pipe_out, M_sub)

    return T_node

def calc_return_node_temperature(index, M_d, T_e_out, t_return, Z_pipe_out, M_sub):
    # calculate node temperature with merging flows from pipes
    part1 = np.dot(M_d, T_e_out[index]).sum()
    part2 = 0 if M_sub[index].max()==0 else np.dot(M_sub[index].sum(), t_return.values[0,index])
    part3 = np.dot(M_d, Z_pipe_out[index]).sum() + M_sub[index].sum()
    T_node = (part1 + part2) / part3
    return T_node

def calc_t_out(node, edge, K, M_d, Z, T_e_in, T_e_out, T_ground, Z_note, gv):
    # calculate pipe outlet temperature
    k = K[edge, edge]
    m = M_d[edge, edge]
    out_node_index = np.where(Z[:, edge] == 1)[0].max()
    if m <= 0 and Z[node,edge] == -1:
        # set outlet temperature to nan if no flow is going out from node to connected edges
        T_e_out[out_node_index, edge] = np.nan
        Z_note[:, edge] = 0

    elif Z[node,edge] == -1:
        # calculate outlet temperature if flow goes from node to out_node through edge
        T_e_out[out_node_index, edge] = (T_e_in[node, edge] * (k / 2 - m * gv.Cpw) - k * T_ground) / (-m * gv.Cpw - k / 2)  # [K]
        dT = T_e_in[node,edge]-T_e_out[out_node_index,edge]
        if dT > 30:
            print ('High temperature loss on edge'), edge
        Z_note[:, edge] = 0

def calc_aggregated_heat_conduction_coefficient(locator, gv, L_pipe, pipe_properties_df):
    """

    :param locator:
    :param gv:
    :param L_pipe:
    :return:
     K matrix (1 x e) for all edges
    """
    # TODO [SH]: load thermal conductivity, and ground thermal conductivity from database, and define network_depth, extra_heat_transfer_coef in gv
    thermal_conductivity_pipe = 0.025     # [W/mC]
    thermal_conductivity_ground = 1.75    # [W/mC]
    network_depth = 1                     # [m]
    extra_heat_transfer_coef = 0.2

    K_all = []
    for pipe in L_pipe.index:
        R_pipe = np.log(pipe_properties_df.loc['D_ext', pipe]/pipe_properties_df.loc['D_ext', pipe])/(2*math.pi*thermal_conductivity_pipe)     #[mC/W]
        a= 2*network_depth/pipe_properties_df.loc['D_ext', pipe]
        R_ground = np.log(a+(a**2-1)**0.5)/(2*math.pi*thermal_conductivity_ground) #[mC/W]
        k = L_pipe[pipe]*(1+extra_heat_transfer_coef)/(R_pipe+R_ground)/1000   #[kW/C]
        K_all.append(k)

    K_all = np.diag(K_all)
    return K_all

def calc_edge_temperatures(temperature_node, edge_node):
    '''
    calculates the temperature at each edge assuming T_edge = (T_node_1 + T_node_2)/2 as done, for example, by Wang et al.
    '''
    temperature_edge = np.dot(temperature_node,abs(edge_node)/2)
    return temperature_edge

#============================
# other functions
#============================

def get_thermal_network_from_csv(locator):
    """
    This function reads the existing node and pipe network from csv files (as provided for the Zug reference case) and
    produces an edge-node incidence matrix (as defined by Oppelt et al. "Dynamic thermo-hydraulic model of district
    cooling networks," Applied Thermal Engineering, 2016) as well as the length of each edge.

    :param locator: locator class

    :return:
        edge_node_df: dataframe consisting of n rows (number of nodes) and e columns (number of edges) and indicating
    direction of flow of each edge e at node n: if e points to n, value is 1; if e leaves node n, -1; else, 0.  (n x e)
        all_nodes_df: dataframe that contains all nodes and whether a node is a consumer, plant or neither      (2 x n)
        pipe_data_df['LENGTH']: vector containing the length of each edge in the network                             (1 x e)

        csv files stored in:
            -edge_node_df:  locator.get_optimization_network_layout_folder() + '//' + 'EdgeNode_DH.csv'
            -all_nodes_df:       locator.get_optimization_network_layout_folder() + '//' + 'AllNodes_DH.csv'
    """

    t0 = time.clock()

    # get node data and create consumer and plant node vectors
    node_data_df = pd.read_csv(locator.get_optimization_network_layout_nodes_file())
    conflict_nodes=[]
    for node in node_data_df.index:
        if node_data_df['Plant'][node] == 1:
            if node_data_df['Sink'][node] == 1:
                node_data_df['Plant'][node] = 0
                node_data_df.loc[node_data_df.index.max()+1] = [node_data_df['DC_ID'][node]+'_plant',node_data_df['Name'][node]+'_plant', 1, 0]
                conflict_nodes.append(node_data_df['DC_ID'][node])
    node_names = node_data_df['DC_ID'].values
    consumer_nodes = np.vstack((node_names,(node_data_df['Sink']*node_data_df['Name']).values))
    plant_nodes = np.vstack((node_names,(node_data_df['Plant']*node_data_df['Name']).values))

    # get pipe data and create edge-node matrix
    pipe_data_df = pd.read_csv(locator.get_optimization_network_layout_pipes_file())
    for node in conflict_nodes:
        for pipe in pipe_data_df.index:
            if pipe_data_df['NODE2'][pipe] == node:
                pipe_data_df['NODE2'][pipe] == node+'_plant'
        pipe_data_df.loc[pipe_data_df.index.max()+1] = ['PIPE'+node, 0, node+'_plant', node]
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

    edge_node_df.to_csv(locator.get_optimization_network_layout_folder() + '//' + 'EdgeNode_DH.csv')
    all_nodes_df = pd.DataFrame(data=[consumer_nodes[1][:], plant_nodes[1][:]], index = ['consumer','plant'], columns = consumer_nodes[0][:])
    all_nodes_df = all_nodes_df[edge_node_df.index.tolist()]
    all_nodes_df.to_csv(locator.get_optimization_network_layout_folder() + '//' + 'AllNodes_DH.csv')

    print time.clock() - t0, "seconds process time for Network summary\n"

    return edge_node_df, all_nodes_df, pipe_data_df['LENGTH']

def get_thermal_network_from_shapefile(locator, gv, t_target_supply, building_names, buildings_demands,
    substations_HEX_specs):
    """
    This function reads the existing node and pipe network from a shapefile (using a road shapefile from the Zurich
    reference case as a template) and produces an edge-node incidence matrix (as defined by Oppelt et al. "Dynamic
    thermo-hydraulic model of district cooling networks," Applied Thermal Engineering, 2016) as well as the pipe
    properties (length, start node, and end node) and node coordinates.

    :param locator: locator class

    :return:
        edge_node_df: dataframe consisting of n rows (number of nodes) and e columns (number of edges) and indicating
    direction of flow of each edge e at node n: if e points to n, value is 1; if e leaves node n, -1; else, 0.  (n x e)
        all_nodes_df: dataframe that contains all nodes and whether a node is a consumer, plant or neither      (2 x n)
        pipe_df: dataframe containing the length, start node and end node of each edge in the network           (1 x e)

        csv files stored in:
            -edge_node_df:  locator.get_optimization_network_layout_folder() + '//' + 'EdgeNode_DH.csv'
            -node_df:       locator.get_optimization_network_layout_folder() + '//' + 'Node_DF_DH.csv'
            -pipe_df:       locator.get_optimization_network_layout_folder() + '//' + 'Pipe_DF_DH.csv'
    """

    t0 = time.clock()

    # import network properties from shapefile
    network_edges_df = gpd.read_file(locator.get_heating_network_edges())
    network_nodes_df = gpd.read_file(locator.get_heating_network_nodes())

    # get node and pipe information
    node_df, pipe_df = extract_network_from_shapefile(network_edges_df, network_nodes_df)

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

    # create node catalogue indicating which nodes are plants and which consumers
    all_nodes_df = pd.DataFrame(data=[node_df['consumer'], node_df['plant']], index = ['consumer','plant'], columns = node_df.index)
    for node in all_nodes_df:
        if all_nodes_df[node]['consumer'] == 1:
            all_nodes_df[node]['consumer'] = node_df['Name'][node]
        else:
            all_nodes_df[node]['consumer'] = ''
        if all_nodes_df[node]['plant'] == 1:
            all_nodes_df[node]['plant'] = node_df['Name'][node]
        else:
            all_nodes_df[node]['plant'] = ''
    all_nodes_df.to_csv(locator.get_optimization_network_layout_folder() + '//' + 'Node_DF_DH.csv')

    # create first edge-node matrix
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

    # Since dataframe doesn't indicate the direction of flow, an edge node matrix is generated as a first guess and
    # the mass flow at t = 0 is calculated with it. The direction of flow is then corrected by inverting negative flows.
    t = 0
    mass_flow_guess = calc_one_timestep(t_target_supply, locator, gv, building_names, buildings_demands,
                                        substations_HEX_specs, t, all_nodes_df, edge_node_df)
    for i in range(len(mass_flow_guess)):
        if mass_flow_guess[0][i] < 0:
            mass_flow_guess[0][i] = abs(mass_flow_guess[0][i])
            edge_node_df[edge_node_df.columns[i]] = -edge_node_df[edge_node_df.columns[i]]
            new_nodes = [pipe_df['end node'][i], pipe_df['start node'][i]]
            pipe_df['start node'][i] = new_nodes[0]
            pipe_df['end node'][i] = new_nodes[1]

    edge_node_df.to_csv(locator.get_optimization_network_layout_folder() + '//' + "EdgeNode_DH.csv")
    pipe_df.to_csv(locator.get_optimization_network_layout_folder() + '//' + 'Pipe_DF_DH.csv')

    print time.clock() - t0, "seconds process time for Network summary\n"

    return edge_node_df, all_nodes_df, pipe_df['pipe length']

def extract_network_from_shapefile(edges_df, nodes_df):
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
    nodes_df['consumer'] = np.ones(len(nodes_df['Plant'])) - nodes_df['Plant'].values   #TODO:PLANT+CONSUMER

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
    pipe_nodes = []
    for j in range(len(edges_df)):
        pipe = edges_df['geometry'][j]
        start_node = pipe.coords[0]
        end_node = pipe.coords[len(pipe.coords)-1]
        pipe_nodes.append(pipe.coords[0])
        pipe_nodes.append(pipe.coords[len(pipe.coords)-1])
        if start_node not in node_dict.keys():
            i += 1
            node_dict[start_node] = ['NODE'+str(i), 'TEE' + str(i - len(nodes_df)), 0, 0, start_node]
        if end_node not in node_dict.keys():
            i += 1
            node_dict[end_node] = ['NODE'+str(i), 'TEE' + str(i - len(nodes_df)), 0, 0, end_node]
        edge_dict['EDGE' + str(j)] = [edges_df['Shape_Leng'][j], node_dict[start_node][0], node_dict[end_node][0]]

    # # if a consumer node is not connected to the network, find the closes node and connect them with a new edge
    # for node in node_dict:
    #     if node not in pipe_nodes:
    #         min_dist = 1000
    #         closest_node = pipe_nodes[0]
    #         for pipe_node in pipe_nodes:
    #             dist = ((node[0] - pipe_node[0])**2 + (node[1] - pipe_node[1])**2)**.5
    #             if dist < min_dist:
    #                 min_dist = dist
    #                 closest_node = pipe_node
    #         j += 1
    #         edge_dict['EDGE' + str(j)] = [min_dist, node_dict[closest_node][0], node_dict[node][0]]

    # create dataframes containing all nodes and edges
    node_df = pd.DataFrame.from_dict(node_dict, orient='index')
    node_df.columns = node_columns
    node_df = node_df.set_index(node_df['Node']).drop(['Node'], axis=1)
    edge_df = pd.DataFrame.from_dict(edge_dict, orient='index')
    edge_df.columns = edge_columns

    return node_df, edge_df

def write_substations_to_nodes_df(all_nodes_df, df_value, flag):
    nodes_df = pd.DataFrame()

    if flag == True:
        #write temperature into nodes dataframe
        for node in all_nodes_df:
            if all_nodes_df[node]['consumer'] != '':
                nodes_df[node] = df_value[all_nodes_df[node]['consumer']]
            else:
                nodes_df[node] = np.nan  # set temperature value to nan for non-substation nodes

    else:
        # calculate mass flow and write all flow rates into nodes dataframe
        for node in all_nodes_df:
            # Assuming only one plant node, the plant needs to supply the flow rate required at all other substations.
            # So mass_flow_rate[plant] = - sum(mass_flow_rate[consumer]) for all consumer nodes
            if all_nodes_df[node]['consumer'] != '':
                nodes_df[node] = df_value[all_nodes_df[node]['consumer']]
            elif all_nodes_df[node]['plant'] != '':
                nodes_df[node] = - (df_value.sum(axis=1) - df_value[all_nodes_df[node]['plant']])
                # nodes_df[node] = - df_value.sum(axis=1)
            else:
                nodes_df[node] = 0
    return nodes_df

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

def read_properties_from_buildings(building_names, buildings, column):
    property_df = pd.DataFrame(index=range(8760), columns= building_names)
    for name in building_names:
        property = buildings[(building_names == name).argmax()][column]
        property_df[name] = property
    return property_df

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
    weather_file = locator.get_default_weather()

    # add geothermal part of preprocessing
    T_ambient = epwreader.epw_reader(weather_file)['drybulb_C']
    gv.ground_temperature = geothermal.calc_ground_temperature(T_ambient.values, gv)

    # add a way to test for either a csv source for the network or a shapefile
    ## shapefile_flag is true if source of data is a shapefile, false if it is a csv
    shapefile_flag = True

    thermal_network_main(locator, gv, shapefile_flag)
    print 'test thermal_network_main() succeeded'

if __name__ == '__main__':
    run_as_script()


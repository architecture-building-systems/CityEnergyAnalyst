from __future__ import print_function

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

def thermal_network_main(locator, gv, network_type, source):
    """
    This function performs thermal and hydraulic calculation of a "well-defined" network, namely, the plant/consumer
    substations, piping routes and the pipe properties (length/diameter/heat transfer coefficient) are already specified.

    Firstly, the consumer substation heat exchanger designs are calculated according to the consumer demands at each
    substation. Secondly, the piping network is imported as a node-edge matrix (NxE), which indicates the connections
    of all nodes and edges and the direction of flow between them following graph theory [Ikonen, E., et al, 2016]_ .
    Nodes represent points in the network, which could be the consumers, plants or joint points. Edges represent the
    pipes in the network. For example, (n1,e1) = 1 denotes the flow enters edge "e1" at node "n1", while when
    (n2,e2) = -1 denotes the flow leave edge "e2" at node "n2". Following, a steady-state hydraulic calculation is
    carried out at each time-step to solve for the edge mass flow rates according to mass conservation equations.

    Finally, we enter the hydraulic thermal calculation routine.

    :param locator:
    :param gv:
    :param shapefile_flag: Boolean set to True if the source for the data is a shapefile, False if it is a csv.
    :return:

    ..[Ikonen, E., et al, 2016] Ikonen, E., et al. Examination of Operational Optimization at Kemi District Heating Network.
    Thermal Science. 2016, Vol. 20, No.2, pp.667-678.


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

    # get edge-node matrix from defined network
    if source == 'csv':
        edge_node_df, all_nodes_df, pipe_length_df = get_thermal_network_from_csv(locator, network_type)
    else:
        edge_node_df, all_nodes_df, pipe_length_df = get_thermal_network_from_shapefile(locator, network_type)

    # get hourly heat requirement and target supply temperature from each substation
    t_target_supply = read_properties_from_buildings(building_names, buildings_demands, 'T_sup_target_'+network_type)
    t_target_supply_df = write_substations_to_nodes_df(all_nodes_df, t_target_supply, flag= True)  #(1xn)

    # assign pipe properties
    ## calculate maximum edge mass flow
    edge_mass_flow_df, max_edge_mass_flow_df = calc_max_edge_flowrate(all_nodes_df, building_names, buildings_demands,
                                                                      edge_node_df, gv, locator, substations_HEX_specs,
                                                                      t_target_supply, network_type)

    # # TODO: This is a temporary function to read from file and save run time for 'calc_max_edge_flowrate'
    # edge_mass_flow_df, max_edge_mass_flow_df = read_max_edge_flowrate(edge_node_df, locator, network_type)

    # assign pipe id/od according to maximum edge mass flow
    pipe_properties_df = assign_pipes_to_edges(max_edge_mass_flow_df, locator, gv) # TODO[SH]: Find bigger pipes for DC

    # calculate pipe aggregated heat conduction coefficient
    K_pipe = calc_aggregated_heat_conduction_coefficient(locator, gv, pipe_length_df, pipe_properties_df)#(exe) [kW/K]

    ## Start solving hydraulic and thermal equations at each time-step
    t0 = time.clock()
    # create empty lists to write results
    T_return_nodes_list = []
    T_supply_nodes_list = []
    plant_heat_requirements = []

    for t in range(8760):
        print('calculating network thermal hydraulic properties... timestep',t)
        timer = time.clock()

        ## solve network temperatures
        T_supply_nodes, \
        T_return_nodes, \
        plant_heat_requirement = solve_network_temperatures(locator, gv, T_ground, edge_node_df, all_nodes_df,
                                                            edge_mass_flow_df.ix[t], K_pipe, t_target_supply_df,
                                                            building_names, buildings_demands, substations_HEX_specs, t,
                                                            network_type)

        # store node temperatures and plant heat requirement at each time-step
        T_supply_nodes_list.append(T_supply_nodes)
        T_return_nodes_list.append(T_return_nodes)
        plant_heat_requirements.append(plant_heat_requirement)

        print (time.clock() - timer, 'seconds process time for timestep',t)

    # save results
    pd.DataFrame(T_supply_nodes_list, columns=edge_node_df.index).\
        to_csv(locator.get_optimization_network_layout_supply_temperature_file(network_type), index=False, float_format='%.3f')
    pd.DataFrame(T_return_nodes_list, columns=edge_node_df.index).\
        to_csv(locator.get_optimization_network_layout_return_temperature_file(network_type), index=False, float_format='%.3f')
    # pd.DataFrame(plant_heat_requirements).\
    #     to_csv(locator.get_optimization_network_layout_plant_heat_requirement_file(network_type), index=False, float_format='%.3f') #FIXME[SH]: save to csv

    # # skip calculation, import csv TODO: get rid of this after testing
    # T_supply_nodes_list = pd.read_csv(locator.get_optimization_network_layout_supply_temperature_file(network_type)).values.tolist()
    # T_return_nodes_list = pd.read_csv(locator.get_optimization_network_layout_return_temperature_file(network_type)).values.tolist()
    # # plant_heat_requirements = pd.read_csv(locator.get_optimization_network_layout_plant_heat_requirement_file(network_type))


    # calculate pressure at each node and pressure drop throughout the entire network
    pressure_nodes_supply, pressure_nodes_return, pressure_loss_system = calc_pressure_nodes(edge_node_df,
                                                    pipe_properties_df[:]['D_int':'D_int'].values, pipe_length_df.values,
                                                    edge_mass_flow_df.values, T_supply_nodes_list, T_return_nodes_list, gv)
    pd.DataFrame(pressure_nodes_supply, columns=edge_node_df.index). \
            to_csv(locator.get_optimization_network_layout_supply_pressure_file(network_type), index=False, float_format='%.3f')
    pd.DataFrame(pressure_nodes_return, columns=edge_node_df.index).\
        to_csv(locator.get_optimization_network_layout_return_pressure_file(network_type), index=False, float_format='%.3f')
    pd.DataFrame(pressure_loss_system, columns=['pressure_drop_Pa']). \
        to_csv(locator.get_optimization_network_layout_pressure_drop_file(network_type), index=False, float_format='%.3f')

    print (time.clock() - t0, "seconds process time for network thermal-hydraulic calculation \n")


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
            mass_flow_substation_df[node] = pd.read_csv(locator.pathSubsRes + '//' + (all_nodes_df[node]['consumer']+all_nodes_df[node]['plant']) + "_result.csv", usecols=['mdot_result'])  #name] = pd.read_csv(locator.pathSubsRes + '//' + name + "_result.csv", usecols=['mdot_result'])
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
    pipe_catalog = pd.read_excel(locator.get_thermal_networks(),sheetname=['PIPING CATALOG'])['PIPING CATALOG']
    pipe_catalog['Vdot_min'] = pipe_catalog['Vdot_min'] * gv.Pwater
    pipe_catalog['Vdot_max'] = pipe_catalog['Vdot_max'] * gv.Pwater
    pipe_properties_df = pd.DataFrame(data = None, index = pipe_catalog.columns.values, columns = mass_flow_df.columns.values)
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

def calc_pressure_nodes(edge_node_df, pipe_diameter, pipe_length, mass_flow_rate, T_supply_node, T_return_node, gv):
    ''' calculates the pressure at each node based on Eq. 1 in Todini & Pilati (1987) "A gradient method for the analysis
of pipe networks," in Computer Applications in Water Supply Volume 1 - Systems Analysis and Simulation. Since the
pressure is calculated after the mass flow rate (rather than concurrently) this is only a first step towards implementing
 the Gradient Method from Todini & Pilati used by EPANET et al.
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
    temperature_supply_edges = calc_edge_temperatures(T_supply_node, edge_node_df)
    temperature_return_edges = calc_edge_temperatures(T_return_node, edge_node_df)

    # get the pressure through each edge
    pressure_loss_pipe_supply = calc_pressure_loss_pipe(pipe_diameter, pipe_length, mass_flow_rate, temperature_supply_edges, gv)
    pressure_loss_pipe_return = calc_pressure_loss_pipe(pipe_diameter, pipe_length, mass_flow_rate, temperature_return_edges, gv)

    # total pressure loss in the system
    pressure_loss_system = np.transpose(np.array([sum(np.nan_to_num(pressure_loss_pipe_supply)[i] for i in
                            range(len(pressure_loss_pipe_supply[0])))]) + np.array([sum(np.nan_to_num(
                            pressure_loss_pipe_return)[i] for i in range(len(pressure_loss_pipe_return[0])))]))

    # calculate the pressure at each node based on Eq. 1 in Todini & Pilati for no = 0 (no nodes with fixed head):
    # A12 * H + F(Q) = -A10 * H0 = 0
    # edge_node_transpose * pressure_nodes + pressure_loss_pipe = 0
    edge_node_transpose = np.transpose(edge_node_df.values)
    pressure_nodes_supply = np.round(
        np.transpose(np.linalg.lstsq(edge_node_transpose, np.transpose(pressure_loss_pipe_supply))[0]), decimals=9)
    pressure_nodes_return = np.round(
        np.transpose(np.linalg.lstsq(-edge_node_transpose, np.transpose(pressure_loss_pipe_return))[0]), decimals=9)

    # # get a matrix showing which edges point to each node n
    # edge_node = edge_node_df.values.transpose()
    # for i in range(len(edge_node)):
    #     for j in range(len(edge_node[0])):
    #         if edge_node[i][j] < 0:
    #             edge_node[i][j] = 0
    #
    # # the pressure losses at time t are calculated as the sum of the pressure losses from all edges pointing to node n
    # pressure_loss_nodes_supply_df = pd.DataFrame(np.dot(pressure_loss_pipe_supply, edge_node), index=range(8760), columns=edge_node_df.index.values)
    # pressure_loss_nodes_return_df = pd.DataFrame(np.dot(pressure_loss_pipe_return, -edge_node), index=range(8760), columns=edge_node_df.index.values)

    return pressure_nodes_supply, pressure_nodes_return, pressure_loss_system

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

    kinematic_viscosity = calc_kinematic_viscosity(temperature) # m2/s
    reynolds = 4*(mass_flow_rate/gv.Pwater)/(math.pi * kinematic_viscosity * pipe_diameter)
    pipe_roughness = gv.roughness    # assumed from Li & Svendsen for now
    darcy = 1.325 * np.log(pipe_roughness / (3.7 * pipe_diameter) + 5.74 / reynolds ** 0.9) ** (-2)  # Swamee-Jain equation to calculate the Darcy-Weisbach friction factor
    pressure_loss_edge = darcy * 8 * mass_flow_rate**2 * pipe_length/(math.pi**2 * pipe_diameter**5 * gv.Pwater) #darcy*8/(math.pi*gv.gr)*kinematic_viscosity**2/pipe_diameter**5*pipe_length

    return pressure_loss_edge

def calc_kinematic_viscosity(temperature):
    ''' calculates the kinematic viscosity of water as a function of temperature based on a simple fit from data from the
     engineering toolbox
     :param: temperature: in K

     :return: kinematic viscosity in m2/s
     '''
    return 2.652623e-8*math.e**(557.5447*(temperature-140)**-1)

def calc_max_edge_flowrate(all_nodes_df, building_names, buildings_demands, edge_node_df, gv, locator,
                           substations_HEX_specs, t_target_supply, network_type):
    # create empty dataframes to store results
    edge_mass_flow_df = pd.DataFrame(data=np.zeros((8760, len(edge_node_df.columns.values))),
                                     columns=edge_node_df.columns.values)

    print('start calculating edge mass flow...')
    t0 = time.clock()
    for t in range(8760):
        print('\n calculating edge mass flow... timestep', t)

        # set to the highest value in the network and assume no loss within the network
        T_substation_supply = t_target_supply.ix[t].max() + 273.15  # in [K]

        # calculate substation flow rates and return temperatures
        if network_type == 'DH' or (network_type == 'DC' and  math.isnan(T_substation_supply) is False):
            T_return_all, \
            mdot_all = substation.substation_return_model_main(locator, gv, building_names, buildings_demands,
                                                                substations_HEX_specs, T_substation_supply, t, network_type,
                                                                t_flag = True)
                                                                # t_flag = True: same temperature for all nodes
        else:
            T_return_all = np.full(building_names.size,T_substation_supply).T
            mdot_all = pd.DataFrame(data=np.zeros(24), index=building_names.values).T

        # write consumer substation required flow rate to nodes
        required_flow_rate_df = write_substations_to_nodes_df(all_nodes_df, mdot_all, flag=False)  # (1xn) #flag = True: writing temperature
        # FIXME[Question to MM]: what should we fill in for the plant mass flow before entering calc_mass_flow_edges?

        # solve mass flow rates on edges
        edge_mass_flow_df[:][t:t + 1] = calc_mass_flow_edges(edge_node_df, required_flow_rate_df)

    edge_mass_flow_df.to_csv(locator.get_optimization_network_layout_folder() + '//' + 'NominalEdgeMassFlow_'+network_type+'.csv')
    print (time.clock() - t0, "seconds process time for edge mass flow calculation\n")

    edge_mass_flow_df = pd.read_csv(locator.get_optimization_network_layout_folder() + '//' + 'NominalEdgeMassFlow_'+network_type+'.csv')

    # assign pipe properties based on max flow on edges
    max_edge_mass_flow = edge_mass_flow_df.max(axis=0)
    max_edge_mass_flow_df = pd.DataFrame(data=[max_edge_mass_flow], columns=edge_node_df.columns)

    return edge_mass_flow_df, max_edge_mass_flow_df

def read_max_edge_flowrate(edge_node_df, locator, network_type):

    edge_mass_flow_df = pd.read_csv(locator.get_optimization_network_layout_folder() + '//' + 'NominalEdgeMassFlow_'+network_type+'.csv')
    del edge_mass_flow_df['Unnamed: 0']
    # assign pipe properties based on max flow on edges
    max_edge_mass_flow = edge_mass_flow_df.max(axis=0)
    max_edge_mass_flow_df = pd.DataFrame(data=[max_edge_mass_flow], columns=edge_node_df.columns)

    return edge_mass_flow_df, max_edge_mass_flow_df

#===========================
# Thermal calculation
#===========================
def solve_network_temperatures(locator, gv, T_ground, edge_node_df, all_nodes_df, edge_mass_flow_df, K, t_target_supply_df,
                               building_names, buildings_demands, substations_HEX_specs, t, network_type):
    """
    This function calculates the node temperatures at time-step t accounting for heat losses throughout the network.

    Parameters
    ----------
    locator
    gv
    T_ground
    edge_node_df
    all_nodes_df
    edge_mass_flow_df
    K
    t_target_supply_df
    building_names
    buildings_demands
    substations_HEX_specs
    t

    Returns
    -------

    """

    if edge_mass_flow_df.values.sum()!= 0:

        # calculate node temperatures on the supply network accounting losses in the network.
        T_supply_nodes, plant_node = calc_supply_temperatures(gv, T_ground[t], edge_node_df, edge_mass_flow_df, K,
                                                              t_target_supply_df.loc[t])

        # write supply temperatures to substation nodes
        T_substation_supply = write_nodes_to_substations(T_supply_nodes, all_nodes_df, plant_node)

        # TODO[SH]: remove when iteration is stable
        # # calculate substation return temperatures according to supply temperatures
        # T_return_all, \
        # mdot_all = substation.substation_return_model_main(locator, gv, building_names, buildings_demands,
        #                                                       substations_HEX_specs, T_substation_supply, t, network_type,
        #                                                       t_flag = False)
        #
        # # write consumer substation return T and required flow rate to nodes
        # T_substation_return_df = write_substations_to_nodes_df(all_nodes_df, T_return_all, flag=True)  # (1xn)
        # mass_flow_substations_nodes_df = write_substations_to_nodes_df(all_nodes_df, mdot_all, flag=False)

        ## Iterations to find out the corresponding node supply temperature and substation mass flow
        flag = 0
        iteration = 0
        while flag == 0:
            # calculate substation return temperatures according to supply temperatures
            T_return_all, \
            mdot_all = substation.substation_return_model_main(locator, gv, building_names, buildings_demands,
                                                              substations_HEX_specs, T_substation_supply, t, network_type,
                                                              t_flag = False)
            if mdot_all.values.max() is np.nan:
                print ('Error in edge mass flow! Check edge_mass_flow_df')

            # write consumer substation return T and required flow rate to nodes
            T_substation_return_df = write_substations_to_nodes_df(all_nodes_df, T_return_all, flag=True)  # (1xn)
            mass_flow_substations_nodes_df = write_substations_to_nodes_df(all_nodes_df, mdot_all, flag=False)

            # solve for the required mass flow rate on each pipe
            edge_mass_flow_df_2 = calc_mass_flow_edges(edge_node_df, mass_flow_substations_nodes_df)

            # calculate updated node temperatures on the supply network with updated edge mass flow
            T_supply_nodes_2, plant_node = calc_supply_temperatures(gv, T_ground[t], edge_node_df,
                                                              edge_mass_flow_df_2, K, t_target_supply_df.loc[t])
            # write supply temperatures to substation nodes
            T_substation_supply_2 = write_nodes_to_substations(T_supply_nodes_2, all_nodes_df, plant_node)

            # check if the supply temperature at substations converged
            max_node_dT = max(list((T_substation_supply-T_substation_supply_2).dropna(axis=1).values[0]))  # max supply node temperature difference
            if max_node_dT > 1 and iteration < 10:
                # update the substation supply temperature and re-enter the iteration
                T_substation_supply = T_substation_supply_2
                print (iteration,'iteration. Maximum node temperature difference:', max_node_dT)
                iteration += 1
            elif max_node_dT > 10 and 20 > iteration >= 10:   #FIXME[SH]: justify the criteria
                # update the substation supply temperature and re-enter the iteration
                T_substation_supply = T_substation_supply_2
                print (iteration,'iteration. Maximum node temperature difference:', max_node_dT)
                iteration += 1
            else:
                # calculate substation return temperatures according to supply temperatures
                T_return_all, \
                mdot_all = substation.substation_return_model_main(locator, gv, building_names, buildings_demands,
                                                                    substations_HEX_specs, T_substation_supply_2, t,
                                                                    network_type, t_flag=False)
                # write consumer substation return T and required flow rate to nodes
                T_substation_return_df = write_substations_to_nodes_df(all_nodes_df, T_return_all, flag = True)  # (1xn)
                mass_flow_substations_nodes_df = write_substations_to_nodes_df(all_nodes_df, mdot_all, flag = False)
                # solve for the required mass flow rate on each pipe
                edge_mass_flow_df = calc_mass_flow_edges(edge_node_df, mass_flow_substations_nodes_df)
                flag = 1
                if max_node_dT < 1:
                    print('supply temperature converged after', iteration, 'iterations', 'dT:', max_node_dT)
                else:
                    print('Warning: supply temperature did not converge after', iteration, 'iterations at timestep', t,
                          'dT:', max_node_dT)

        # calculate node temperatures on the return network
        T_return_nodes = calc_return_temperatures(gv, T_ground[t], edge_node_df, edge_mass_flow_df,
                                                   mass_flow_substations_nodes_df, K, T_substation_return_df)

        plant_heat_requiremnt = gv.Cpw * (T_supply_nodes[plant_node] - T_return_nodes[plant_node]) \
                                * abs(mass_flow_substations_nodes_df.values.T[plant_node])
    else:
        T_supply_nodes = []
        T_return_nodes = []
        plant_heat_requiremnt = 0

    return T_supply_nodes, T_return_nodes, plant_heat_requiremnt


def write_nodes_to_substations(T_supply_nodes, all_nodes_df, plant_node):
    T_substation_supply = all_nodes_df.copy().drop('plant')   # add building names to corresponding nodes
    T_substation_supply.loc['T_supply'] = T_supply_nodes      # add consumer node supply temperatures
    T_substation_supply.columns = T_substation_supply.loc['consumer']   # set building names as column names
    T_substation_supply = T_substation_supply.drop('consumer')          # drop row with building names
    T_substation_supply = T_substation_supply.drop('', axis=1)          # only keep nodes at consumer buildings
    plant_building = all_nodes_df.ix['plant', plant_node]               # find plant building name
    T_substation_supply.loc['T_supply', plant_building] = T_supply_nodes[plant_node]   # add plant temperature to df
    return T_substation_supply


def calc_supply_temperatures(gv, T_ground, edge_node_df, mass_flow_df, K, t_target_supply):
    Z = np.asarray(edge_node_df)   # (nxe) edge-node matrix
    Z_pipe_out = Z.clip(min=0)     # pipe outlet matrix
    Z_pipe_in = Z.clip(max=0)      # pipe inlet matrix

    M_d = np.zeros((Z.shape[1],Z.shape[1]))   # (exe) pipe mass flow rate matrix
    np.fill_diagonal(M_d,mass_flow_df)

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
        if all(dT > -0.1) is False and (T_H-T_H_0) < 60:
                # increase plant supply temperature and re-iterate the node supply temperature calculation
                T_H = T_H + abs(dT.min())  # increase by the maximum amount of temperature deficit at nodes
                Z_note = Z.copy()
                T_e_out = Z_pipe_out.copy()
                T_e_in = Z_pipe_in.copy().dot(-1)
                T_node = np.zeros(Z.shape[0])
                iteration += 1
        elif all(dT > -0.1) is False and (T_H-T_H_0) >= 60:
            # end iteration if total network temperature drop is higher than 60 K
            print ('cannot fulfill substation supply node temperature requirement after iterations:', iteration, dT.min())
            node_insufficient = dT[dT<0].index.values
            for node in range(node_insufficient.size):
                index_insufficient = np.argwhere(edge_node_df.index == node_insufficient[node])[0]
                T_node[index_insufficient] = t_target_supply[index_insufficient] + 273.15
                # force setting node temperature to target to avoid substation HEX calculation error
                # FIXME[SH]: causing error at mass flow iteration, the supply temperature will not converge...
            flag = 1
        else:
            flag = 1
    return T_node.T, plant_node

def calc_return_temperatures(gv, T_ground, edge_node_df, mass_flow_df, mass_flow_substation_df, K, t_return):
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
    total_mass_flow_to_node = np.dot(M_d, Z_pipe_out[index]).sum() + M_sub[index].sum()
    if total_mass_flow_to_node == 0:
        # set node temperature to nan if no flow to node
        T_node = np.nan
    else:
        total_mcp_from_edges = np.dot(M_d, np.nan_to_num(T_e_out[index])).sum()
        total_mcp_from_substations = 0 if M_sub[index].max()==0 else np.dot(M_sub[index].sum(), t_return.values[0,index])
        T_node = (total_mcp_from_edges + total_mcp_from_substations) / total_mass_flow_to_node
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
            print ('High temperature loss on edge', edge, '. Loss:', dT)
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
    material_properties = pd.read_excel(locator.get_thermal_networks(), sheetname=['MATERIAL PROPERTIES'])['MATERIAL PROPERTIES']
    material_properties = material_properties.set_index(material_properties['material'].values)
    conductivity_pipe = material_properties.ix['Steel','lamda']     # [W/mC]
    conductivity_insulation = material_properties.ix['PUR','lamda'] # [W/mC]
    conductivity_ground = material_properties.ix['Soil','lamda']    # [W/mC]
    network_depth = gv.NetworkDepth       # [m]
    extra_heat_transfer_coef = 0.2


    K_all = []
    for pipe in L_pipe.index:
        R_pipe = np.log(pipe_properties_df.loc['D_ext', pipe]/pipe_properties_df.loc['D_int', pipe])/(2*math.pi*conductivity_pipe)     #[mC/W]
        R_insulation = np.log((pipe_properties_df.loc['D_ins', pipe])/pipe_properties_df.loc['D_ext', pipe])/(2*math.pi*conductivity_insulation)
        a= 2*network_depth/(pipe_properties_df.loc['D_ins', pipe])
        R_ground = np.log(a+(a**2-1)**0.5)/(2*math.pi*conductivity_ground) #[mC/W]
        k = L_pipe[pipe]*( 1 +  extra_heat_transfer_coef)/(R_pipe + R_insulation + R_ground)/1000   #[kW/C]
        K_all.append(k)

    K_all = np.diag(K_all)
    return K_all

def calc_edge_temperatures(temperature_node, edge_node):
    '''
    calculates the temperature at each edge assuming T_edge = (T_node_1 + T_node_2)/2 as done, for example, by Wang et al.
    '''
    temperature_edge = np.dot(np.nan_to_num(temperature_node),abs(edge_node)/2)
    # since many nodes have no assigned temperature, the temperatures in many of the edges were unreasonable (< 273K)
    # these are set to zero here # TODO [MM, SH]: does this make sense? can we set the node temperatures somehow?
    # TODO[Answer to MM]: if one of the node temperature is 'nan' meaning there is no flow on that edge, therefore, you probably don't need the temperature from that edge...
    for i in range(temperature_edge.shape[0]):
        for j in range(temperature_edge.shape[1]):
            if temperature_edge[i][j] < 273:
                temperature_edge[i][j] = 0

    return temperature_edge

#============================
#other functions
#============================

def get_thermal_network_from_csv(locator, network_type):
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
            -edge_node_df:  locator.get_optimization_network_layout_folder() + '//' + 'DH_EdgeNode.csv'
            -all_nodes_df:       locator.get_optimization_network_layout_folder() + '//' + 'DH_AllNodes.csv'
    """

    t0 = time.clock()

    # get node and pipe data
    node_data_df = pd.read_csv(locator.get_optimization_network_layout_nodes_file(network_type))
    pipe_data_df = pd.read_csv(locator.get_optimization_network_layout_pipes_file(network_type))

    # create consumer and plant node vectors from node data
    for column in ['Plant','Sink']:
        if type(node_data_df[column][0]) != int:
           node_data_df[column] = node_data_df[column].astype(int)
    node_names = node_data_df['DC_ID'].values
    consumer_nodes = np.vstack((node_names,(node_data_df['Sink']*node_data_df['Name']).values))
    plant_nodes = np.vstack((node_names,(node_data_df['Plant']*node_data_df['Name']).values))

    # create edge-node matrix from pipe data
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

    edge_node_df.to_csv(locator.get_optimization_network_edge_node_matrix_file(network_type))
    all_nodes_df = pd.DataFrame(data=[consumer_nodes[1][:], plant_nodes[1][:]], index = ['consumer','plant'], columns = consumer_nodes[0][:])
    all_nodes_df = all_nodes_df[edge_node_df.index.tolist()]
    all_nodes_df.to_csv(locator.get_optimization_network_node_list_file(network_type))

    print (time.clock() - t0, "seconds process time for Network summary\n")

    return edge_node_df, all_nodes_df, pipe_data_df['LENGTH']

def get_thermal_network_from_shapefile(locator, network_type):
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
            -edge_node_df:  locator.get_optimization_network_layout_folder() + '//' + 'DH_EdgeNode.csv'
            -node_df:       locator.get_optimization_network_layout_folder() + '//' + 'DH_Node_DF.csv'
            -pipe_df:       locator.get_optimization_network_layout_folder() + '//' + 'DH_Pipe_DF.csv'
    """

    t0 = time.clock()

    # import network properties from shapefile
    network_edges_df = gpd.read_file(locator.get_network_edges_shapefile(network_type))
    network_nodes_df = gpd.read_file(locator.get_network_nodes_shapefile(network_type))

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
    all_nodes_df.to_csv(locator.get_optimization_network_node_list_file(network_type))

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
    substation_mass_flows_df = pd.DataFrame(data = np.zeros([1,len(edge_node_df.index)]), columns = edge_node_df.index)
    total_flow = 0
    for node in consumer_nodes:
        if node != '':
            substation_mass_flows_df[node] = 1
            total_flow += 1
    for plant in plant_nodes:
        if plant != '':
            substation_mass_flows_df[plant] = -total_flow
    mass_flow_guess = calc_mass_flow_edges(edge_node_df, substation_mass_flows_df)[0]

    for i in range(len(mass_flow_guess)):
        if mass_flow_guess[i] < 0:
            mass_flow_guess[i] = abs(mass_flow_guess[i])
            edge_node_df[edge_node_df.columns[i]] = -edge_node_df[edge_node_df.columns[i]]
            new_nodes = [pipe_df['end node'][i], pipe_df['start node'][i]]
            pipe_df['start node'][i] = new_nodes[0]
            pipe_df['end node'][i] = new_nodes[1]


    edge_node_df.to_csv(locator.get_optimization_network_edge_node_matrix_file(network_type))
    pipe_df.to_csv(locator.get_optimization_network_edge_list_file(network_type))

    print (time.clock() - t0, "seconds process time for Network summary\n")

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
    nodes_df['consumer'] = np.zeros(len(nodes_df['Plant']))
    for node in range(len(nodes_df['consumer'])):
        if nodes_df['Qh'][node] > 0:
            nodes_df['consumer'][node] = 1

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

    # # if a consumer node is not connected to the network, find the closest node and connect them with a new edge
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
    node_df = node_df.set_index(node_df['Node']).drop(['Node'], axis = 1)
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
            '''
            for each node, mass_edge_in + mass_supply = mass_edge_out + mass_demand
                           mass_edge_in - mass_edge_out = mass_demand - mass_supply
                           edge_node * mass_flow_edge = mass_demand - mass_supply
                           edge_node * mass_flow_edge = mass_flow_node
            so mass_flow_node[node] = mass_flow_demand[node] for consumer nodes and
               mass_flow_node[node] = mass_flow_demand[node] - mass_flow_supply[node] for plant nodes
            assuming only one plant node, the mass flow on the supply side needs to equal the mass flow from consumers
            so mass_flow_supply = sum(mass_flow_deman[node]) for all nodes
            '''

            if all_nodes_df[node]['consumer'] != '':
                nodes_df[node] = df_value[all_nodes_df[node]['consumer']]
            elif all_nodes_df[node]['plant'] != '':
                # nodes_df[node] = df_value[all_nodes_df[node]['plant']] - (df_value.sum(axis=1) - df_value[all_nodes_df[node]['plant']])
                nodes_df[node] = - (df_value.sum(axis=1) - df_value[all_nodes_df[node]['plant']])
                # FIXME[MM]: shall we delete this? are we ignoring the consumer requirement at the plant node, and only treating the plant node as a plant now?
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

    # add options for data sources: heating or cooling network, csv or shapefile
    network_type = ['DH', 'DC'] # set to either 'DH' or 'DC'
    source = ['csv', 'shapefile'] # set to csv or shapefile

    thermal_network_main(locator, gv, network_type[0], source[0])
    print ('test thermal_network_main() succeeded')

if __name__ == '__main__':
    run_as_script()


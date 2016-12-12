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

building_names[building_names=='Bau A'].index[0]

def pipe_thermal_calculation(locator, gv, T_ground, edge_node_df, mass_flow_df, consumer_heat_requiremt, mass_flow_substation_df, pipe_length_df):
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
    Z = edge_node_df #.as_matrix()   #edge-node matrix
    Z_minus = np.dot(-1,Z)
    Z_minus_T = np.transpose(Z_minus)
    M_d = np.diag(mass_flow_df)  # e x e #  mass_flow_df[1]   #pipe mass flow diagonal matrix
    K = calc_aggregated_heat_conduction_coefficient(locator,gv, pipe_length_df) # e x e # aggregated heat condumtion coef matrix (e x e) #TODO: [SH] import pipe property (length and diameter)
    M_sub = np.diag(mass_flow_substation_df)  # n x n   # mass flow rate matrix, positive at cosumer substation, negative at plant substation
    M_sub_cp = np.dot(gv.Cpw, M_sub)
    U = consumer_heat_requiremt
    T_ground_matrix = [i*0+T_ground for i in range(len(pipe_length_df))]  # e x 1

    plant_node =np.transpose([-1, 0, 0])
    consumer_node = np.transpose([0, 1, 1])
    T_required = np.dot(273 + 65, consumer_node)


    a = 0
    T_H = 273 + 60    # TODO: pick the maximum T_supply requirement
    while a == 0:
        H = np.dot(M_sub_cp, plant_node).dot(T_H)     #(n x 1)# calculate heat input matrix
        T_node = calc_pipe_temperature(gv, Z, M_d, K, Z_minus, Z_minus_T, U, H, T_ground_matrix)
        if all(T_node <= T_required) is True:
            T_H = T_H + 1
        else:
            a = 1
            return T_node

    return T_node

def calc_pipe_temperature(gv, Z, M_d, K, Z_minus, Z_minus_T, U, H, T_ground):

    a1 = np.dot(gv.Cpw, Z).dot(M_d).dot(np.linalg.inv(np.dot(gv.Cpw, M_d) + np.dot( K, 1/2 )))
    a2 = np.dot(gv.Cpw, M_d).dot(Z_minus_T) - np.dot( np.dot( K, 1/2 ), Z_minus_T)
    a3 = np.dot(gv.Cpw,Z_minus).dot(M_d).dot(Z_minus_T)
    a4 = U - np.dot(a1, K).dot(T_ground) - H
    T_node = np.dot(np.linalg.inv(np.dot(a1, a2) - a3), a4)

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
    # TODO [SH]: load pipe id, od, thermal conductivity, and ground thermal conductivity
    thermal_conductivity_pipe = 0.02   # TODO [SH]: load pipe id * od
    thermal_conductivity_ground = 0.01
    network_depth = 1   # TODO [SH]: define in gv
    pipe_id = 0.02
    pipe_od = 0.023
    extra_heat_transfer_coef = 0.002   # TODO: [SH] defined in gv

    K_all = []
    for edge in range(len(L_pipe)):
        R_pipe = np.log(pipe_od/pipe_id)/(2*math.pi*thermal_conductivity_pipe)
        a= 2*network_depth/pipe_od
        R_ground = np.log(a+(a**2-1)**0.5)/(2*math.pi*thermal_conductivity_ground)
        k = L_pipe[edge]*(1+extra_heat_transfer_coef)/(R_pipe+R_ground)
        K_all.append(k)
        edge += 1

    K_all = np.diag(K_all)
    return K_all

def write_value_to_nodes(all_nodes_df, building_names, value_list):
     nodes_df = pd.DataFrame()
     for node in all_nodes_df:  # consumer_nodes+plant_nodes:    #name in building_names:
         if all_nodes_df[node]['consumer'] != '':
             nodes_df[node] = [value_list[(building_names == all_nodes_df[node].consumer).argmax()]]
         elif all_nodes_df[node]['plant'] != '':
             nodes_df[node] = [value_list[(building_names == all_nodes_df[node].plant).argmax()]]
         else:
             nodes_df[node] = np.nan
     return nodes_df
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
    T_ground = geothermal.calc_ground_temperature(T_ambient.values, gv)
    #substation_main(locator, total_demand, total_demand['Name'], gv, False)

    edge_node_df = [[-1,0],[1,-1],[0,1]]
    mass_flow_df = [3,2]
    mass_flow_substation_df = [-3,1,2]
    pipe_length_df = [1,2]
    consumer_heat_requiremt = [0, 10, 20]
    t = 500
    pipe_thermal_calculation(locator, gv, T_ground[t], edge_node_df, mass_flow_df, consumer_heat_requiremt, mass_flow_substation_df, pipe_length_df)

    print 'test calc_hydraulic_network() succeeded'

if __name__ == '__main__':
    run_as_script()
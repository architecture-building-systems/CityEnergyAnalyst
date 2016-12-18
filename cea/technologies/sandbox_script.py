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


# trial 1=========================================================
# building_names[building_names=='Bau A'].index[0]
#
# def pipe_thermal_calculation(locator, gv, T_ground, edge_node_df, mass_flow_df, consumer_heat_requiremt, mass_flow_substation_df, pipe_length_df):
#     """
#     This function solve for the node temperature with known mass flow rate in pipes and substation mass flow rate at each time-step.
#
#     :param locator:
#     :param gv:
#     :param weather_file:
#     :param edge_node_df: matrix consisting of n rows (number of nodes) and e columns (number of edges) and indicating
# direction of flow of each edge e at node n: if e points to n, value is 1; if e leaves node n, -1; else, 0.  (n x e)
#     :param mass_flow_df: matrix containing the mass flow rate in each edge e at time t               (1 x e)
#     :param mass_flow_substation_df: mass flow rate through each node (1 x n)
#     :return:
#
#     Reference
#     ==========
#     J. Wang, A method for the steady-state thermal simulation of district heating systems and model parameters
#     calibration. Energy Conversion and Management, 2016
#     """
#     Z = edge_node_df #.as_matrix()   #edge-node matrix
#     Z_minus = np.dot(-1,Z)
#     Z_minus_T = np.transpose(Z_minus)
#     M_d = np.diag(mass_flow_df)  # e x e #  mass_flow_df[1]   #pipe mass flow diagonal matrix
#     K = calc_aggregated_heat_conduction_coefficient(locator,gv, pipe_length_df) # e x e # aggregated heat condumtion coef matrix (e x e) #TODO: [SH] import pipe property (length and diameter)
#     M_sub = np.diag(mass_flow_substation_df)  # n x n   # mass flow rate matrix, positive at cosumer substation, negative at plant substation
#     M_sub_cp = np.dot(gv.Cpw*1000, M_sub)
#     U = consumer_heat_requiremt
#
#     T_ground_matrix = [i*0+T_ground-273 for i in range(len(pipe_length_df))]  # e x 1
#
#     plant_node =np.transpose([-1, 0, 0])
#     consumer_node = np.transpose([0, 1, 1])
#     T_required = np.dot(273 + 65, consumer_node)
#     U = np.dot(M_sub_cp, consumer_node).dot(60)
#
#     a = 0
#     T_H = 60    # TODO: pick the maximum T_supply requirement
#     while a == 0:
#         H = np.dot(M_sub_cp, plant_node).dot(T_H)     #(n x 1)# calculate heat input matrix
#         T_node = calc_pipe_temperature(gv, Z, M_d, K, Z_minus, Z_minus_T, U, H, T_ground_matrix)
#         if all(T_node <= T_required) is True:
#             T_H = T_H + 1
#         else:
#             a = 1
#             return T_node
#
#     return T_node
#
# def calc_pipe_temperature(gv, Z, M_d, K, Z_minus, Z_minus_T, U, H, T_ground):
#
#     a1 = np.dot(gv.Cpw*1000, Z).dot(M_d).dot(np.linalg.inv(np.dot(gv.Cpw*1000, M_d) + np.dot( K, 1/2 )))
#     a2 = np.dot(gv.Cpw*1000, M_d).dot(Z_minus_T) - np.dot( K/2, Z_minus_T)
#     a3 = np.dot(gv.Cpw*1000,Z_minus).dot(M_d).dot(Z_minus_T)
#     a4 = U - np.dot(a1, K).dot(T_ground) - H
#     T_node_1 = np.dot(a1, a2)
#     T_node_1_1 = np.dot(a1, a2) - a3
#     T_node_1_2 = np.dot(a1, a2) + a3
#     x = np.linalg.inv(T_node_1_1)
#     T_node_2 = np.linalg.inv(np.dot(a1, a2) - a3)
#     T_node = np.dot(np.linalg.inv(np.dot(a1, a2) - a3), a4)
#
#     # b1 = 1/(gv.Cpw*M_d + K/2)
#     # b2 = a2*T_node + K*T_ground
#     # T_out = b1*b2
#     #
#     # T_in = Z_minus_T*T_node
#     return T_node
#
# def calc_aggregated_heat_conduction_coefficient(locator, gv, L_pipe):
#     """
#
#     :param locator:
#     :param gv:
#     :param L_pipe:
#     :return:
#      K matrix (1 x e) for all edges
#     """
#     # TODO [SH]: load pipe id, od, thermal conductivity, and ground thermal conductivity
#     thermal_conductivity_pipe = 0.025     # [W/mC]
#     thermal_conductivity_ground = 1.75    # [W/mC]
#     network_depth = 1                     # [m]
#     pipe_id = 0.1107                      # [m]
#     pipe_od = 0.1143                      # [m]
#     extra_heat_transfer_coef = 0.2
#
#     K_all = []
#     for edge in range(len(L_pipe)):
#         R_pipe = np.log(pipe_od/pipe_id)/(2*math.pi*thermal_conductivity_pipe)
#         a= 2*network_depth/pipe_od
#         R_ground = np.log(a+(a**2-1)**0.5)/(2*math.pi*thermal_conductivity_ground)
#         k = L_pipe[edge]*(1+extra_heat_transfer_coef)/(R_pipe+R_ground)
#         K_all.append(k)
#         edge += 1
#
#     K_all = np.diag(K_all)
#     return K_all
#
# def write_value_to_nodes(all_nodes_df, building_names, value_list):
#      nodes_df = pd.DataFrame()
#      for node in all_nodes_df:  # consumer_nodes+plant_nodes:    #name in building_names:
#          if all_nodes_df[node]['consumer'] != '':
#              nodes_df[node] = [value_list[(building_names == all_nodes_df[node].consumer).argmax()]]
#          elif all_nodes_df[node]['plant'] != '':
#              nodes_df[node] = [value_list[(building_names == all_nodes_df[node].plant).argmax()]]
#          else:
#              nodes_df[node] = np.nan
#      return nodes_df


#trail2==================================================================
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
    Z_out = Z[Z<0]=0
    Z_minus = np.dot(-1,Z)
    Z_minus_T = np.transpose(Z_minus)
    M_d = np.diag(mass_flow_df)  # e x e #  mass_flow_df[1]   #pipe mass flow diagonal matrix
    K = calc_aggregated_heat_conduction_coefficient(locator,gv, pipe_length_df) # e x e # aggregated heat condumtion coef matrix (e x e) #TODO: [SH] import pipe property (length and diameter)
    M_sub = np.diag(mass_flow_substation_df)  # n x n   # mass flow rate matrix, positive at cosumer substation, negative at plant substation
    M_sub_cp = np.dot(gv.Cpw*1000, M_sub)
    U = consumer_heat_requiremt

    T_ground_matrix = [i*0+T_ground-273 for i in range(len(pipe_length_df))]  # e x 1

    plant_node =np.transpose([-1, 0, 0])
    consumer_node = np.transpose([0, 1, 1])
    T_required = np.dot(273 + 65, consumer_node)
    U = np.dot(M_sub_cp, consumer_node).dot(60)

    a = 0
    T_H = 60    # TODO: pick the maximum T_supply requirement
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

    a1 = np.dot(gv.Cpw*1000, Z).dot(M_d).dot(np.linalg.inv(np.dot(gv.Cpw*1000, M_d) + np.dot( K, 1/2 )))
    a2 = np.dot(gv.Cpw*1000, M_d).dot(Z_minus_T) - np.dot( K/2, Z_minus_T)
    a3 = np.dot(gv.Cpw*1000,Z_minus).dot(M_d).dot(Z_minus_T)
    a4 = U - np.dot(a1, K).dot(T_ground) - H
    T_node_1 = np.dot(a1, a2)
    T_node_1_1 = np.dot(a1, a2) - a3
    T_node_1_2 = np.dot(a1, a2) + a3
    x = np.linalg.inv(T_node_1_1)
    T_node_2 = np.linalg.inv(np.dot(a1, a2) - a3)
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
    thermal_conductivity_pipe = 0.025     # [W/mC]
    thermal_conductivity_ground = 1.75    # [W/mC]
    network_depth = 1                     # [m]
    pipe_id = 0.1107                      # [m]
    pipe_od = 0.1143                      # [m]
    extra_heat_transfer_coef = 0.2

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

# Z_out_in = np.hstack((Z_pipe_out, Z_pipe_in))
# M_d_2 = block_diag(M_d*gv.Cpw , M_d*gv.Cpw)  # (2e x 2e) [kW/K]
# Z_M_d_2 = np.dot(Z_out_in,M_d_2)   # (n x 2e) [kW/K]
# U = consumer_heat_requiremt/3600   #(nx1) [kW]   #TODO: maybe don't fix?
# M_d_cp_1 = np.dot(M_d, gv.Cpw)- np.dot(K,1/2)   # (exe)  [kW/K]
# M_d_cp_2 = -1*(np.dot(M_d, gv.Cpw) + np.dot(K, 1 / 2))  # (exe)  [kW/K]
# M_d_cp_K = np.hstack((M_d_cp_1, M_d_cp_2))  # (e x 2e) [kW/K]
# T_g_K = (np.dot(T_ground_matrix,K).dot(-1))
# # substation = (U - H).values
# # b = np.hstack((substation,T_g_K)).T # (n+e)x1

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
    Z_pipe_out = Z.clip(min=0)
    # Z_pipe_in = np.dot(-1,Z.clip(max=0)) #TODO: [SH] check if this is correct: I added a negative sign to this because I think based on Wang both matrices need to be greater than 0, no?
    Z_pipe_in = Z.clip(max=0)
    # Z_minus = np.dot(-1,Z)         # (nxe)
    # Z_minus_T = np.transpose(Z_minus)  # (exn)
    M_sub = np.diag(mass_flow_substation_df.as_matrix()[0])  # (nxn)  [kg/s] # substation mass flow rate matrix
    M_sub_cp = np.dot(gv.Cpw, M_sub)   #[kW/K]

    consumer_node = np.where(all_nodes_df.ix['consumer']!='', 1, 0)      # make (n x 1) consumer node matrix
    plant_node = np.where(all_nodes_df.ix['plant'] != '', 1, 0)      # make (n x 1) plant node matrix

    M_d_cp = np.diag(mass_flow_df.as_matrix())  # (exe) pipe mass flow diagonal matrix #TODO: check unit is [kg/s]
    K = calc_aggregated_heat_conduction_coefficient(locator,gv, pipe_length_df)/1000 # (exe) # aggregated heat condumtion coef matrix [kW/K] #TODO: [SH] import pipe property (length and diameter)

    T_ground_matrix = pd.Series([i*0+T_ground for i in range(len(pipe_length_df))])  # (ex1) [K]
    T_required = np.dot(273 + 65, consumer_node)    # (nx1) [K]

    # preparing matrices for calculation
    M_d_cp = M_d_cp*gv.Cpw  # (e x e)
    Zout_mcp = np.dot(Z_pipe_out,M_d_cp)    # (n x e)
    Zin_mcp = np.dot(Z_pipe_in,M_d_cp)  # (n x e)
    Zout_Zin = np.hstack((Zout_mcp,Zin_mcp))    # (n x 2e)
    Zout_Zin_M_sub = np.hstack((Zout_Zin, M_sub_cp))  #(n x (2e+n))

    Md_cp_K_1 = M_d_cp-K/2  # (e x e)
    Md_cp_K_2 = (-1)*( M_d_cp + K / 2)  # (e x e)
    Md_cp_K = np.hstack((Md_cp_K_1, Md_cp_K_2)) # (e x 2e)
    zeros = np.zeros((edge_node_df.shape[1], edge_node_df.shape[0]))
    Md_cp_K_zeros = np.hstack((Md_cp_K, zeros)) # (e x (2e+n))

    zeros = np.zeros((edge_node_df.shape[1], edge_node_df.shape[1]))
    I = np.zeros((edge_node_df.shape[1], edge_node_df.shape[1]))
    np.fill_diagonal(I,1)
    Z_pipe_in_T = Z_pipe_in.T
    zeros_I = np.hstack((zeros, I))
    zeros_I_Zpipe_in = np.hstack((zeros_I, Z_pipe_in_T))

    zeros_array = np.zeros((edge_node_df.shape[1]))
    T_g_K = (np.dot(T_ground_matrix, K).dot(-1))

    # start solving node and pipe outlet temperatures
    print 'start calculating T_node...'
    flag = 0
    T_H = max(t_target_supply)+273 #[K] # determine min T_source
    while flag == 0:
        H = np.dot(M_sub_cp, plant_node).dot(T_H).dot(-1)  #(n x 1)# calculate heat input matrix [kW]
        # cp* Z_pipe_out * M_d * T_pipe_out + H = cp* Z_pipe_in * M_d * T_pipe_in + U

        a_12 = np.vstack((Zout_Zin_M_sub, Md_cp_K_zeros))
        a = np.vstack((a_12, zeros_I_Zpipe_in))
        b_12 = np.hstack((H, T_g_K))
        b = np.hstack((b_12, zeros_array)).T
        # check if matrix is linear independent
        pl, u =  scipy.linalg.lu(a, permute_l=True)

        # T_all = np.linalg.solve(a,b) #FIXME: [SH] error singular matrix
        # T_all = scipy.sparse.linalg.spsolve(a,b) # another solver

        # try to solve with least square method
        T_out_in, residual, rank, s = np.linalg.lstsq(a, b)
        if T_out_in[:] <= 338*199:
            T_H = T_H + 0.1
        else:
            flag = 1
            return T_out_in


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
    mass_flow_df = [0.3,0.2]
    mass_flow_substation_df = [-0.3,0.1,0.2]
    pipe_length_df = [1,2]
    consumer_heat_requiremt = [0, 100, 200]
    t = 500
    pipe_thermal_calculation(locator, gv, T_ground[t], edge_node_df, mass_flow_df, consumer_heat_requiremt, mass_flow_substation_df, pipe_length_df)

    print 'test calc_hydraulic_network() succeeded'

if __name__ == '__main__':
    run_as_script()
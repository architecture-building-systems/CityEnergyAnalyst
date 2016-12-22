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
import scipy
from sympy import *
from sympy.tensor.array import Array
from sympy.physics.quantum import TensorProduct


# trial 1=========================================================



#trail 2 system of equations==================================================================

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

def pipe_thermal_calculation_2(locator, gv, T_ground, edge_node_df, mass_flow_df, consumer_heat_requiremt, mass_flow_substation_df, pipe_length_df, t_target_supply):
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
    Z = np.asarray(edge_node_df)   # (nxe) edge-node matrix
    Z_pipe_out = Z.clip(min=0)
    # Z_pipe_in = np.dot(-1,Z.clip(max=0))
    Z_pipe_in = Z.clip(max=0)
    # Z_minus = np.dot(-1,Z)         # (nxe)
    # Z_minus_T = np.transpose(Z_minus)  # (exn)
    M_sub_d = mass_flow_substation_df
    M_sub = np.zeros((7,7))
    np.fill_diagonal(M_sub, M_sub_d)
    # M_sub = np.diag(M_sub_d[0])  # (nxn)  [kg/s] # substation mass flow rate matrix
    M_sub_cp = np.dot(gv.Cpw, M_sub).dot(-1)   #[kW/K]

    # consumer_node = np.where(all_nodes_df.ix['consumer']!='', 1, 0)      # make (n x 1) consumer node matrix
    # plant_node = np.where(all_nodes_df.ix['plant'] != '', 1, 0)      # make (n x 1) plant node matrix

    pipe = mass_flow_df
    M_d = np.zeros((6,6))
    np.fill_diagonal(M_d,pipe)
    # M_d_cp = np.diag(mass_flow_df.as_matrix())  # (exe) pipe mass flow diagonal matrix #TODO: check unit is [kg/s]
    K = calc_aggregated_heat_conduction_coefficient(locator,gv, pipe_length_df)/1000 # (exe) # aggregated heat condumtion coef matrix [kW/K] #TODO: [SH] import pipe property (length and diameter)

    T_ground_matrix = [T_ground, T_ground, T_ground, T_ground, T_ground, T_ground]
    # T_ground_matrix = pd.Series([i*0+T_ground for i in range(len(pipe_length_df))])  # (ex1) [K]
    # T_required = np.dot(273 + 65, consumer_node)    # (nx1) [K]

    # preparing matrices for calculation
    M_d_cp = M_d*gv.Cpw  # (e x e)
    Zout_mcp = np.dot(Z_pipe_out,M_d_cp)    # (n x e)
    Zin_mcp = np.dot(Z_pipe_in,M_d_cp)  # (n x e)
    Zout_Zin = np.hstack((Zout_mcp,Zin_mcp))    # (n x 2e)
    Zout_Zin_M_sub = np.hstack((Zout_Zin, M_sub_cp))  #(n x (2e+n))

    Md_cp_K_1 = M_d_cp-K/2  # (e x e)
    Md_cp_K_2 = (-1)*( M_d_cp + K / 2)  # (e x e)
    Md_cp_K = np.hstack((Md_cp_K_1, Md_cp_K_2)) # (e x 2e)
    zeros = np.zeros((Z.shape[1], Z.shape[0]))
    Md_cp_K_zeros = np.hstack((Md_cp_K, zeros)) # (e x (2e+n))

    zeros = np.zeros((Z.shape[1], Z.shape[1]))
    I = np.zeros((Z.shape[1], Z.shape[1]))
    np.fill_diagonal(I,1)
    Z_pipe_in_T = Z_pipe_in.T
    zeros_I = np.hstack((zeros, I))
    zeros_I_Zpipe_in = np.hstack((zeros_I, Z_pipe_in_T))

    zeros_array_edge = np.zeros((Z.shape[1]))
    zeros_array_node = np.zeros((Z.shape[0]))
    T_g_K = (np.dot(T_ground_matrix, K).dot(-1))

    # start solving node and pipe outlet temperatures
    print 'start calculating T_node...'
    flag = 0
    # T_H = max(t_target_supply)+273 #[K] # determine min T_source
    while flag == 0:
        # H = np.dot(M_sub_cp, plant_node).dot(T_H).dot(-1)  #(n x 1)# calculate heat input matrix [kW]
        # cp* Z_pipe_out * M_d * T_pipe_out + H = cp* Z_pipe_in * M_d * T_pipe_in + U

        a_12 = np.vstack((Zout_Zin_M_sub, Md_cp_K_zeros))
        a = np.vstack((a_12, zeros_I_Zpipe_in))
        b_12 = np.hstack((zeros_array_node, T_g_K))
        b = np.hstack((b_12, zeros_array_edge)).T
        # check if matrix is linear independent
        pl, u =  scipy.linalg.lu(a, permute_l=True)

        T_all = np.linalg.solve(a,b) #FIXME: [SH] error singular matrix
        print T_all
        # T_all = scipy.sparse.linalg.spsolve(a,b) # another solver

        # try to solve with least square method
        T_out_in, residual, rank, s = np.linalg.lstsq(a, b)
        if T_out_in[:] <= 338*199:
            T_H = T_H + 0.1
        else:
            flag = 1
            return T_out_in



#trail3 pipe by pipe===================================================================

def pipe_supply(locator, gv, T_ground, edge_node_df, mass_flow_df, consumer_heat_requiremt, mass_flow_substation_df, pipe_length_df, t_target_supply):
    Z = np.asarray(edge_node_df)   # (nxe) edge-node matrix
    Z_pipe_out = Z.clip(min=0)     # pipe outlet matrix
    Z_pipe_in = Z.clip(max=0)      # pipe inlet matrix

    # M_sub_d = mass_flow_substation_df
    M_sub = np.zeros((7,7))
    np.fill_diagonal(M_sub, mass_flow_substation_df)   #TODO: Check order of nodes
    # M_sub = np.diag(M_sub_d[0])  # (nxn)  [kg/s] # substation mass flow rate matrix
    M_sub_cp = np.dot(gv.Cpw, M_sub).dot(-1)   #[kW/K]

    M_d = np.zeros((6,6))
    np.fill_diagonal(M_d,mass_flow_df)     #TODO: Check order of pipes
    K = calc_aggregated_heat_conduction_coefficient(locator,gv, pipe_length_df)/1000 # (exe) # aggregated heat condumtion coef matrix [kW/K] #TODO: [SH] import pipe property (length and diameter)

    T_ground_matrix = [T_ground, T_ground, T_ground, T_ground, T_ground, T_ground]
    # T_ground_matrix = pd.Series([i*0+T_ground for i in range(len(pipe_length_df))])  # (ex1) [K]
    # T_required = np.dot(273 + 65, consumer_node)    # (nx1) [K]

    # matrices to store results
    T_e_out = Z_pipe_out.copy()
    T_e_in = Z_pipe_in.copy().dot(-1)
    T_node = np.zeros(Z.shape[0])
    Z_new = Z.copy()   # matrix to store information of solved nodes


    flag = 0
    T_H = 273 + 64
    while flag == 0:
        for i in range(Z.shape[0]):
            if np.count_nonzero(Z_new[i]==0) == (Z.shape[1]-1) and Z[i].sum() == -1:
                    # write plant inlet temperature
                    T_node[i] = T_H   # assume plant inlet temperature
                    e_index = np.argmax(np.where(T_e_in[i]!=0))    # find edge index
                    T_e_in[i] = T_e_in[i]*T_node[i]

                    calc_t_out(e_index, K, M_d, Z, T_e_in, T_e_out, T_ground, Z_new, gv)

                    # # calculate pipe outlet temperature
                    # k = K[e_index][e_index]
                    # m = M_d[e_index][e_index]
                    # out_node_index = np.where(Z[:,e_index]==1)     # find node index
                    # T_e_out[out_node_index,e_index] = (T_e_in[i][e_index]*(k/2-m*gv.Cpw)-k*T_ground)/(-m*gv.Cpw-k/2)
                    # Z_new[:,e_index]=0

        x = 0  #
        while Z_new.max()>=1:
            for j in range(Z.shape[0]):
                if np.count_nonzero(Z_new[j] == 1) == 0 and np.count_nonzero(Z_new[j]==0) != Z.shape[1]:
                    # calculate node temperature with merging flows from pipes
                    part1 = np.dot(M_d, T_e_out[j]).sum()
                    part2 = np.dot(M_d, Z_pipe_out[j]).sum()
                    T_node[j] = part1 / part2
                    # write the node temperature to the corresponding pipe inlet
                    T_e_in[j] = T_e_in[j] * T_node[j]
                    for edge in range(Z_new.shape[1]):
                        if T_e_in[j, edge]!=0:
                            # calculate pipe outlet
                            # calc_t_out(edge, K, M_d, Z, T_e_in, T_e_out, T_ground, Z_new, gv)
                            k = K[edge, edge]
                            m = M_d[edge, edge]
                            out_node_index = np.where(Z[:, edge] == 1)
                            T_e_out[out_node_index, edge] = (T_e_in[j, edge] * (k / 2 - m * gv.Cpw) - k * T_ground) / (-m * gv.Cpw - k / 2)
                            Z_new[:, edge] = 0
                elif T_node[j]<=0:
                    T_node[j] = T_e_out[j].max()
        if T_node.min() <= t_target_supply:
                T_H = T_H + 1  # TODO: global variable
                Z_new = Z.copy()
                T_e_out = Z_pipe_out.copy()
                T_e_in = Z_pipe_in.copy().dot(-1)
                T_node = np.zeros(Z.shape[0])
        else:
                print T_node
                flag = 1


def calc_t_out(index, K, M_d, Z, T_e_in, T_e_out, T_ground, Z_new, gv):
    # calculate pipe outlet
    k = K[index, index]
    m = M_d[index, index]
    out_node_index = np.where(Z[:,index]==1)[0]
    T_e_out[out_node_index, index] = (T_e_in[index, index] * (k / 2 - m * gv.Cpw) - k * T_ground) / (-m * gv.Cpw - k / 2)
    Z_new[:, index] = 0

def pipe_return(locator, gv, T_ground, edge_node_df, mass_flow_df, consumer_heat_requiremt, mass_flow_substation_df, pipe_length_df, t_return):
    Z = np.asarray(edge_node_df) *(-1)  # (nxe) edge-node matrix
    Z_pipe_out = Z.clip(min=0)     # pipe outlet matrix
    Z_pipe_in = Z.clip(max=0)      # pipe inlet matrix

    # M_sub_d = mass_flow_substation_df
    # M_sub = np.zeros((7,7))
    # np.fill_diagonal(M_sub, mass_flow_substation_df)   #TODO: Check order of nodes
    M_sub = mass_flow_substation_df
    # M_sub = np.diag(M_sub_d[0])  # (nxn)  [kg/s] # substation mass flow rate matrix
    M_sub_cp = np.dot(gv.Cpw, M_sub).dot(-1)   #[kW/K]

    M_d = np.zeros((6,6))
    np.fill_diagonal(M_d,mass_flow_df)     #TODO: take new flow rate
    K = calc_aggregated_heat_conduction_coefficient(locator,gv, pipe_length_df)/1000 # (exe) # aggregated heat condumtion coef matrix [kW/K] #TODO: [SH] import pipe property (length and diameter)

    T_ground_matrix = [T_ground, T_ground, T_ground, T_ground, T_ground, T_ground]
    # T_ground_matrix = pd.Series([i*0+T_ground for i in range(len(pipe_length_df))])  # (ex1) [K]
    # T_required = np.dot(273 + 65, consumer_node)    # (nx1) [K]

    # matrices to store results
    T_e_out = Z_pipe_out.copy()
    T_e_in = Z_pipe_in.copy().dot(-1)
    T_node = np.zeros(Z.shape[0])
    Z_new = Z.copy()   # matrix to store information of solved nodes

    for i in range(Z.shape[0]):
            if np.count_nonzero(Z_new[i] == 1) == 0 and np.count_nonzero(Z_new[i] == 0) != Z.shape[1]:
                T_node[i] = t_return[i]
                for edge in range(Z_new.shape[1]):
                    if T_e_in[i, edge] != 0:
                        T_e_in[i, edge] = t_return[i]
                        # calculate pipe outlet
                        k = K[edge, edge]
                        m = M_d[edge, edge]
                        out_node_index = np.where(Z[:, edge] == 1)
                        T_e_out[out_node_index, edge] = (T_e_in[i, edge] * (k / 2 - m * gv.Cpw) - k * T_ground) / (
                        -m * gv.Cpw - k / 2)
                        Z_new[:, edge] = 0

    while Z_new.max()>=1:
            for j in range(Z.shape[0]):
                if np.count_nonzero(Z_new[j] == 1) == 0 and np.count_nonzero(Z_new[j]==0) != Z.shape[1]:
                    # calculate node temperature with merging flows from pipes
                    T_node[j]=calc_node_temperature(j, M_d, T_e_out, t_return, Z_pipe_out, M_sub)
                    for edge in range(Z_new.shape[1]):
                        if T_e_in[j, edge]!=0:
                            T_e_in[j, edge]=T_node[j]
                            # calculate pipe outlet
                            k = K[edge, edge]
                            m = M_d[edge, edge]
                            out_node_index = np.where(Z[:, edge] == 1)
                            T_e_out[out_node_index, edge] = (T_e_in[j, edge] * (k / 2 - m * gv.Cpw) - k * T_ground) / (-m * gv.Cpw - k / 2)
                            Z_new[:, edge] = 0


    node_index = np.where(T_node == 0)[0].max()
    # calculate node temperature with merging flows from pipes
    M_sub[node_index]=0   # todo: check M_sub format
    T_node[node_index] = calc_node_temperature(node_index, M_d, T_e_out, t_return, Z_pipe_out, M_sub)
    print T_node



def calc_node_temperature(index, M_d, T_e_out, t_return, Z_pipe_out, M_sub):
    # calculate node temperature with merging flows from pipes
    part1 = np.dot(M_d, T_e_out[index]).sum()
    part2 = np.dot(M_sub[index], t_return[index])
    part3 = np.dot(M_d, Z_pipe_out[index]).sum() + M_sub[index]
    T_node = (part1 + part2) / part3
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

    T_ground = 283
    edge_node_df = [[-1,0,0,0,0,0],[1,-1,0,0,0,0],[0,1,-1,-1,0,0],[0,0,1,0,0,0],[0,0,0,1,-1,-1],[0,0,0,0,0,1],[0,0,0,0,1,0]]
    mass_flow_df = [7,6,1,4,1,2]
    mass_flow_substation_df = [-7,1,1,1,1,2,1]
    pipe_length_df = [1,1,1,1,1,1]
    consumer_heat_requiremt = [0, 100, 200]
    t_target_supply = 273 + 65
    T_return = [0, 332, 331, 330, 330, 329, 329]  #todo: make sure T_return from plant is zero
    # pipe_thermal_calculation(locator, gv, T_ground[t], edge_node_df, mass_flow_df, consumer_heat_requiremt, mass_flow_substation_df, pipe_length_df)
    # pipe_thermal_calculation_2(locator, gv, T_ground, edge_node_df, mass_flow_df, consumer_heat_requiremt,
    #                             mass_flow_substation_df, pipe_length_df, t_target_supply)

    # pipe_supply(locator, gv, T_ground, edge_node_df, mass_flow_df, consumer_heat_requiremt,
    #                            mass_flow_substation_df, pipe_length_df, t_target_supply)

    pipe_return(locator, gv, T_ground, edge_node_df, mass_flow_df, consumer_heat_requiremt,
                               mass_flow_substation_df, pipe_length_df, T_return)


print 'test calc_hydraulic_network() succeeded'

if __name__ == '__main__':
    run_as_script()








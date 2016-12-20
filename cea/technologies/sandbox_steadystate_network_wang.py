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



def pipe_thermal_calculation(locator, gv, T_ground, A_in, A_out, m, U, H, pipe_length):
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

    A_in_T = np.transpose(A_in)
    T_ground_matrix = [T_ground, T_ground, T_ground, T_ground, T_ground, T_ground]

    ## Matrices for sympy calculation

    # M_d = diag(*m)   # pipe flow rate
    # k = symbols('ka kb kc kd ke kf')
    # K = diag(*k)

    ## Matrices for numerica
    pipe_flow_rate = m
    M_d = np.zeros((6,6))
    np.fill_diagonal(M_d,pipe_flow_rate)
    K = calc_aggregated_heat_conduction_coefficient(locator,gv, pipe_length)/1000 # (exe) # aggregated heat condumtion coef matrix [kW/K]


    # start solving node and pipe outlet temperatures
    print 'start calculating T_node...'

    t_required = 273 + 65

    flag = 0
    while flag == 0:
        T_node = calc_pipe_temperature(gv, A_out, M_d, K, A_in, A_in_T, U, H, T_ground_matrix)
        #T_node = calc_pipe_temperature_sympy(gv, A_out, M_d, K, A_in, A_in_T, U, H, T_ground_matrix)

        if T_node.min() <= t_required:
            H[0] = H[0] + 0.1
        else:
            flag = 1
            print T_node
    return T_node


def calc_pipe_temperature(gv, A_out, M_d, K, A_in, A_in_T, U, H, T_ground):

    a1 = np.dot(gv.Cpw * 1000, A_out).dot(M_d).dot(np.linalg.inv(np.dot(gv.Cpw * 1000, M_d) + np.dot(K, 1/2)))
    a2 = np.dot(gv.Cpw * 1000, M_d).dot(A_in_T) - np.dot(K/2, A_in_T)
    a3 = np.dot(gv.Cpw * 1000, A_in).dot(M_d).dot(A_in_T)
    a4 = U - np.dot(a1, K).dot(T_ground) - H

    T_node = np.dot(np.linalg.inv(np.dot(a1, a2) - a3), a4)

    b1 = np.linalg.inv(np.dot(gv.Cpw * 1000, M_d) + np.dot(K, 1/2))
    b2 = np.dot(a2,T_node)+np.dot(K,T_ground)
    T_out = np.dot(b1,b2)

    T_in = A_in_T*T_node
    return T_node

def calc_pipe_temperature_sympy(gv, A_out, M_d, K, A_in, A_in_T, U, H, T_ground):

    Cpw = Symbol('Cpw')
    a0 = (Cpw*M_d + K/2).inv()
    a1 = Cpw*A_out*M_d*a0
    a2 = Cpw*M_d*A_in_T- (K/2)*A_in_T
    a3 = Cpw*A_in*M_d*A_in_T
    U_matrix = Matrix(U)
    H_matrix = Matrix(H)
    a4 = a1*K
    Tg_matrix = Matrix(T_ground)
    a5 = U_matrix -a4*Tg_matrix- H_matrix

    x = (a1*a2-a3).inv()
    T_node = x*a5

    T_out = a0*(a2*T_node+K*Tg_matrix)
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

def run_as_script(scenario_path=None):
    """
    run pipe_thermal_calculation_wang
    """
    import cea.globalvar
    import cea.inputlocator as inputlocator
    gv = cea.globalvar.GlobalVariables()

    if scenario_path is None:
        scenario_path = gv.scenario_reference

    locator = inputlocator.InputLocator(scenario_path=scenario_path)


    ## Matrices for Sympy calculation

    T_ground = Symbol('Tg')
    A_in = np.array(
        [[0, 0, 0, 0, 0, 1], [1, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0], [0, 0, 0, 1, 1, 0]])  # (5x6)
    A_out = np.array(
        [[1, 0, 0, 0, 0, 0], [0, 1, 1, 0, 0, 0], [0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 1]])
    # m = symbols('M_a M_b M_c M_d M_e M_f')
    # L_pipe = Symbol('L_pipe')
    # pipe_length = [L_pipe, L_pipe, L_pipe, L_pipe, L_pipe, L_pipe]
    # U_1 = Symbol('U_1')
    # U_2 = Symbol('U_2')
    # U_3 = Symbol('U_3')
    # U_4 = Symbol('U_4')
    # U_2_star = Symbol('U_2_star')
    # U = [U_1, U_2, U_3, U_4, U_2_star]
    # H_1 = Symbol('H_1')
    # H_2 = Symbol('H_2')
    # H_3 = Symbol('H_3')
    # H_4 = Symbol('H_4')
    # H_2_star = Symbol('H_2_star')
    # H = [H_1, H_2, H_3, H_4, H_2_star]  # assumption

    # m = symbols('M_a M_b M_c M_d M_e M_f')
    # L_pipe = Symbol('L_pipe')
    # pipe_length = [L_pipe, L_pipe, L_pipe, L_pipe, L_pipe, L_pipe]
    # U_1 = Symbol('U_1')
    # U_2 = Symbol('U_2')
    # U_3 = Symbol('U_3')
    # U_4 = Symbol('U_4')
    # U_2_star = Symbol('U_2_star')
    # U = [0, 0, U_3, U_4, 0]
    # H_1 = Symbol('H_1')
    # H_2 = Symbol('H_2')
    # H_3 = Symbol('H_3')
    # H_4 = Symbol('H_4')
    # H_2_star = Symbol('H_2_star')
    # H = [H_1, 0, 0, 0, 0]


    ## matrices for numerical calculation

    T_ground = 283 - 273
    A_out = np.array(
        [[0, 0, 0, 0, 0, 1], [1, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0], [0, 0, 0, 1, 1, 0]])  # (5x6)
    A_in = np.array(
        [[1, 0, 0, 0, 0, 0], [0, 1, 1, 0, 0, 0], [0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 1]])
    m = [6, 3, 3, 3, 3, 6]   # pipe flow rate
    pipe_length = [1, 1, 1, 1, 1, 1]
    U = [0, 0, 400, 400, 0]
    H = [801, 0, 0, 0, 0]  # assumption


    pipe_thermal_calculation(locator, gv, T_ground, A_in, A_out, m, U, H, pipe_length)



if __name__ == '__main__':
    run_as_script()
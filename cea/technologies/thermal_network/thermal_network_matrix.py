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
import cea.technologies.substation_matrix as substation
import math
from cea.utilities import epwreader
from cea.resources import geothermal
import geopandas as gpd
import cea.config
import cea.globalvar
import cea.inputlocator
import os
import networkx as nx

__author__ = "Martin Mosteiro Romero, Shanshan Hsieh"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Martin Mosteiro Romero", "Shanshan Hsieh", "Lennart Rogenhofer"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def thermal_network_main(locator, gv, network_type, network_name, source, set_diameter):
    """
    This function performs thermal and hydraulic calculation of a "well-defined" network, namely, the plant/consumer
    substations, piping routes and the pipe properties (length/diameter/heat transfer coefficient) are already 
    specified.

    The hydraulic calculation is based on Oppelt, T., et al., 2016 for the case with no loops. Firstly, the consumer
    substation heat exchanger designs are calculated according to the consumer demands at each substation. Secondly,
    the piping network is imported as a node-edge matrix (NxE), which indicates the connections of all nodes and edges
    and the direction of flow between them following graph theory. Nodes represent points in the network, which could
    be the consumers, plants or joint points. Edges represent the pipes in the network. For example, (n1,e1) = 1 denotes
    the flow enters edge "e1" at node "n1", while when (n2,e2) = -1 denotes the flow leave edge "e2" at node "n2".
    Following, a steady-state hydraulic calculation is carried out at each time-step to solve for the edge mass flow
    rates according to mass conservation equations. With the maximum mass flow calculated from each edge, the property
    of each pipe is assigned.

    Thirdly, the hydraulic thermal calculation for each time-steps over a year is based on a heat balance for each
    edge (heat at the pipe inlet equals heat at the outlet minus heat losses through the pipe). Finally, the pressure
    loss calculation is carried out based on Todini et al. (1987)

    :param locator: an InputLocator instance set to the scenario to work on
    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling ('DC')
                         network
    :param source: string that defines the type of source file for the network to be imported ('csv' or shapefile 'shp')

    :type locator: InputLocator
    :type gv: GlobalVariables
    :type network_type: str
    :type source: str

    The following files are created by this script, depending on the network type defined in the inputs:

    - DH_EdgeNode or DC_EdgeNode: .csv, edge-node matrix for the defined network
    - DH_AllNodes or DC_AllNodes: .csv, list of plant nodes and consumer nodes and their corresponding building names
    - DH_MassFlow or DC_MassFlow: .csv, mass flow rates at each edge for each time step
    - DH_T_Supply or DC_T_Supply: .csv, describes the supply temperatures at each node at each type step
    - DH_T_Return or DC_T_Return: .csv, describes the return temperatures at each node at each type step
    - DH_Plant_heat_requirement or DC_Plant_heat_requirement: .csv, heat requirement from the plants in a district
      heating or cooling network
    - DH_P_Supply or DC_P_Supply: .csv, supply side pressure for each node in a district heating or cooling network at
      each time step
    - DH_P_Return or DC_P_Return: .csv, return side pressure for each node in a district heating or cooling network at
      each time step
    - DH_P_DeltaP or DC_P_DeltaP.csv, pressure drop over an entire district heating or cooling network at each time step

    .. [Todini & Pilati, 1987] Todini & Pilati. "A gradient method for the analysis of pipe networks," in Computer
       Applications in Water Supply Volume 1 - Systems Analysis and Simulation, 1987.

    .. [Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
       Applied Thermal Engineering, 2016.

    .. [Ikonen, E., et al, 2016] Ikonen, E., et al. Examination of Operational Optimization at Kemi District Heating
       Network. Thermal Science. 2016, Vol. 20, No.2, pp.667-678.
    """

    # # prepare data for calculation

    # read building names from the entire district
    building_names = pd.read_csv(locator.get_total_demand())['Name'].values

    # get edge-node matrix from defined network, the input formats are either .csv or .shp
    if source == 'csv':
        edge_node_df, all_nodes_df, edge_df = get_thermal_network_from_csv(locator, network_type, network_name)
    else:
        edge_node_df, all_nodes_df, edge_df, building_names = get_thermal_network_from_shapefile(locator, network_type,
                                                                                                 network_name)

    # calculate ground temperature
    weather_file = locator.get_default_weather()
    T_ambient_C = epwreader.epw_reader(weather_file)['drybulb_C']
    network_depth_m = gv.NetworkDepth  # [m]
    T_ground_K = geothermal.calc_ground_temperature(locator, T_ambient_C.values, network_depth_m)

    # substation HEX design
    substations_HEX_specs, buildings_demands = substation.substation_HEX_design_main(locator, building_names, gv)

    # get hourly heat requirement and target supply temperature from each substation
    t_target_supply_C = read_properties_from_buildings(building_names, buildings_demands,
                                                       'T_sup_target_' + network_type)
    t_target_supply_df = write_substation_temperatures_to_nodes_df(all_nodes_df, t_target_supply_C)  # (1 x n)

    ## assign pipe properties
    # calculate maximum edge mass flow
    edge_mass_flow_df_kgs, max_edge_mass_flow_df_kgs = calc_max_edge_flowrate(all_nodes_df, building_names,
                                                                              buildings_demands,
                                                                              edge_node_df, gv, locator,
                                                                              substations_HEX_specs,
                                                                              t_target_supply_C, network_type,
                                                                              network_name)

    # assign pipe id/od according to maximum edge mass flow
    pipe_properties_df = assign_pipes_to_edges(max_edge_mass_flow_df_kgs, locator, gv, set_diameter, edge_df,
                                               network_type, network_name)
    # merge pipe properties to edge_df and then output as .csv
    edge_df = edge_df.merge(pipe_properties_df.T, left_index=True, right_index=True)
    edge_df.to_csv(locator.get_optimization_network_edge_list_file(network_type, network_name))

    ## Start solving hydraulic and thermal equations at each time-step
    t0 = time.clock()
    # create empty lists to write results
    T_return_nodes_list = []
    T_supply_nodes_list = []
    q_loss_supply_edges_list = []
    plant_heat_requirements = []
    pressure_nodes_supply = []
    pressure_nodes_return = []
    pressure_loss_system = []

    for t in range(8760):
        print('calculating thermal hydraulic properties of', network_type, 'network', network_name,
              '...  time step', t)
        timer = time.clock()

        ## solve network temperatures
        T_supply_nodes_K, \
        T_return_nodes_K, \
        plant_heat_requirement_kW, \
        edge_mass_flow_df_kgs.ix[t], \
        q_loss_supply_edges_kW = solve_network_temperatures(locator, gv, T_ground_K, edge_node_df, all_nodes_df,
                                                            edge_mass_flow_df_kgs.ix[t], t_target_supply_df,
                                                            building_names, buildings_demands, substations_HEX_specs,
                                                            t, network_type, edge_df, pipe_properties_df)

        # calculate pressure at each node and pressure drop throughout the entire network
        P_supply_nodes_Pa, P_return_nodes_Pa, delta_P_network_Pa = calc_pressure_nodes(edge_node_df,
                                                                                       pipe_properties_df[:][
                                                                                       'D_int_m':'D_int_m'].
                                                                                       values,
                                                                                       edge_df['pipe length'].values,
                                                                                       edge_mass_flow_df_kgs.ix[
                                                                                           t].values,
                                                                                       T_supply_nodes_K,
                                                                                       T_return_nodes_K, gv)

        # store node temperatures and pressures, as well as plant heat requirement and overall pressure drop at each
        # time step
        T_supply_nodes_list.append(T_supply_nodes_K)
        T_return_nodes_list.append(T_return_nodes_K)
        q_loss_supply_edges_list.append(q_loss_supply_edges_kW)
        plant_heat_requirements.append(plant_heat_requirement_kW)
        pressure_nodes_supply.append(P_supply_nodes_Pa[0])
        pressure_nodes_return.append(P_return_nodes_Pa[0])
        pressure_loss_system.append(delta_P_network_Pa)

        print(time.clock() - timer, 'seconds process time for time step', t)

    # save results
    # edge flow rates (flow direction corresponding to edge_node_df)
    pd.DataFrame(edge_mass_flow_df_kgs, columns=edge_node_df.columns).to_csv(
        locator.get_optimization_network_layout_massflow_file(network_type, network_name),
        na_rep='NaN', index=False, float_format='%.3f')
    # node temperatures
    pd.DataFrame(T_supply_nodes_list, columns=edge_node_df.index).to_csv(
        locator.get_optimization_network_layout_supply_temperature_file(network_type, network_name),
        na_rep='NaN', index=False, float_format='%.3f')
    pd.DataFrame(T_return_nodes_list, columns=edge_node_df.index).to_csv(
        locator.get_optimization_network_layout_return_temperature_file(network_type, network_name),
        na_rep='NaN', index=False, float_format='%.3f')

    # save edge heat losses in the supply line
    pd.DataFrame(q_loss_supply_edges_list, columns=edge_node_df.columns).to_csv(
        locator.get_optimization_network_layout_qloss_file(network_type, network_name),
        na_rep='NaN', index=False, float_format='%.3f')

    # plant heat requirements
    pd.DataFrame(plant_heat_requirements,
                 columns=filter(None, all_nodes_df[all_nodes_df.Type == 'PLANT'].Building.values)).to_csv(
        locator.get_optimization_network_layout_plant_heat_requirement_file(network_type, network_name), index=False,
        float_format='%.3f')
    # node pressures
    pd.DataFrame(pressure_nodes_supply, columns=edge_node_df.index).to_csv(
        locator.get_optimization_network_layout_supply_pressure_file(network_type, network_name), index=False,
        float_format='%.3f')
    pd.DataFrame(pressure_nodes_return, columns=edge_node_df.index).to_csv(
        locator.get_optimization_network_layout_return_pressure_file(network_type, network_name), index=False,
        float_format='%.3f')
    # pressure losses over entire network
    pd.DataFrame(pressure_loss_system, columns=['pressure_loss_supply_Pa', 'pressure_loss_return_Pa',
                                                'pressure_loss_total_Pa']).to_csv(
        locator.get_optimization_network_layout_pressure_drop_file(network_type, network_name), index=False,
        float_format='%.3f')

    print("\n", time.clock() - t0, "seconds process time for thermal-hydraulic calculation of", network_type,
          " network ",
          network_name, "\n")


# ===========================
# Hydraulic calculation
# ===========================

def calc_mass_flow_edges(edge_node_df, mass_flow_substation_df, all_nodes_df):
    """
    This function carries out the steady-state mass flow rate calculation for a predefined network with predefined mass
    flow rates at each substation based on the method from Todini et al. (1987), Ikonen et al. (2016), Oppelt et al.
    (2016), etc.

    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                         and indicating the direction of flow of each edge e at node n: if e points to n,
                         value is 1; if e leaves node n, -1; else, 0.                                       (n x e)
    :param mass_flow_substation_df: DataFrame containing the mass flow rate at each node n at each time
                                     of the year t                                                          (t x n)
    :type edge_node_df: DataFrame
    :type mass_flow_substation_df: DataFrame

    :return mass_flow_edge: matrix specifying the mass flow rate at each edge e at the given time step t
    :rtype mass_flow_edge: numpy.ndarray

    .. [Todini & Pilati, 1987] Todini & Pilati. "A gradient method for the analysis of pipe networks," in Computer
       Applications in Water Supply Volume 1 - Systems Analysis and Simulation, 1987.

    .. [Ikonen, E., et al, 2016] Ikonen, E., et al. Examination of Operational Optimization at Kemi District Heating
       Network. Thermal Science. 2016, Vol. 20, No.2, pp.667-678.

    .. [Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
       Applied Thermal Engineering, 2016.
    """

    ## remove one equation (at plant node) to build a well-determined matrix, A.
    plant_index = np.where(all_nodes_df['Type'] == 'PLANT')[0][0]  # find index of the first plant node
    A = edge_node_df.drop(edge_node_df.index[plant_index])
    b = mass_flow_substation_df.T
    b.drop(b.index[plant_index], inplace=True)
    solution = np.linalg.solve(A.values, b.values)
    round_solution = np.round(solution, decimals=5)
    mass_flow_edge = np.transpose(round_solution)

    return mass_flow_edge


def assign_pipes_to_edges(mass_flow_df, locator, gv, set_diameter, edge_df, network_type, network_name):
    """
    This function assigns pipes from the catalog to the network for a network with unspecified pipe properties.
    Pipes are assigned based on each edge's minimum and maximum required flow rate. Assuming max velocity for pipe
    DN450-550 is 3 m/s; for DN600 is 3.5 m/s. min velocity for all pipes are 0.3 m/s.

    :param mass_flow_df: DataFrame containing the mass flow rate for each edge e at each time of the year t
    :param locator: an InputLocator instance set to the scenario to work on
    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)
    :type mass_flow_df: DataFrame
    :type locator: InputLocator
    :type gv: GlobalVariables

    :return pipe_properties_df: DataFrame containing the pipe properties for each edge in the network


    """

    # import pipe catalog from Excel file
    pipe_catalog = pd.read_excel(locator.get_thermal_networks(), sheetname=['PIPING CATALOG'])['PIPING CATALOG']
    pipe_catalog['mdot_min_kgs'] = pipe_catalog['Vdot_min_m3s'] * gv.Pwater
    pipe_catalog['mdot_max_kgs'] = pipe_catalog['Vdot_max_m3s'] * gv.Pwater
    pipe_properties_df = pd.DataFrame(data=None, index=pipe_catalog.columns.values, columns=mass_flow_df.columns.values)
    if set_diameter:
        for pipe in mass_flow_df:
            pipe_found = False
            i = 0
            while pipe_found == False:
                if np.amax(np.absolute(mass_flow_df[pipe].values)) <= pipe_catalog['mdot_max_kgs'][i]:
                    pipe_properties_df[pipe] = np.transpose(pipe_catalog[:][i:i + 1].values)
                    pipe_found = True
                elif i == (len(pipe_catalog) - 1):
                    pipe_properties_df[pipe] = np.transpose(pipe_catalog[:][i:i + 1].values)
                    pipe_found = True
                    print(pipe, 'with maximum flow rate of', mass_flow_df[pipe].values, '[kg/s] '
                                                                                        'requires a bigger pipe than provided in the database.' '\n' 'Please add a pipe with adequate pipe '
                                                                                        'size to the Piping Catalog under ..cea/database/system/thermal_networks.xls' '\n')
                else:
                    i += 1
        # at the end save back the edges dataframe in the shapefile with the new pipe diameters
        if os.path.exists(locator.get_network_layout_edges_shapefile(network_type, network_name)):
            network_edges = gpd.read_file(locator.get_network_layout_edges_shapefile(network_type, network_name))
            network_edges['Pipe_DN'] = pipe_properties_df.loc['Pipe_DN'].values
            network_edges.to_file(locator.get_network_layout_edges_shapefile(network_type, network_name))
    else:
        for pipe, row in edge_df.iterrows():
            index = pipe_catalog.Pipe_DN[pipe_catalog.Pipe_DN == row['Pipe_DN']].index
            if len(index) == 0:  # there is no match in the pipe catalog
                raise ValueError(
                    'A very specific bad thing happened!: One or more of the pipes diameters you indicated' '\n'
                    'are not in the pipe catalog!, please make sure your input network match the piping catalog,' '\n'
                    'otherwise :P')
            pipe_properties_df[pipe] = np.transpose(pipe_catalog.loc[index].values)

    return pipe_properties_df


def calc_pressure_nodes(edge_node_df, pipe_diameter, pipe_length, edge_mass_flow, T_supply_node_K, T_return_node_K, gv):
    """
    Calculates the pressure at each node based on Eq. 1 in Todini & Pilati (1987). For the pressure drop through a pipe,
    the Darcy-Weisbach equation was used as in Oppelt et al. (2016) instead of the Hazen-Williams method used by Todini
    & Pilati. Since the pressure is calculated after the mass flow rate (rather than concurrently) this is only a first
    step towards implementing the Gradient Method from Todini & Pilati used by EPANET et al.

    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges) and
            indicating the direction of flow of each edge e at node n: if e points to n, value is 1; if e leaves
            node n, -1; else, 0.                                                                        (n x e)
    :param pipe_diameter: vector containing the pipe diameter in m for each edge e in the network      (e x 1)
    :param pipe_length: vector containing the length in m of each edge e in the network                (e x 1)
    :param edge_mass_flow: matrix containing the mass flow rate in each edge e at time t               (1 x e)
    :param T_supply_node_K: array containing the temperature in each supply node n                       (1 x n)
    :param T_return_node_K: array containing the temperature in each return node n                       (1 x n)
    :param gv: globalvars
    :type edge_node_df: DataFrame
    :type pipe_diameter: ndarray
    :type pipe_length: ndarray
    :type edge_mass_flow: ndarray
    :type T_supply_node_K: list
    :type T_return_node_K: list

    :return pressure_loss_nodes_supply: array containing the pressure loss at each supply node         (1 x n)
    :return pressure_loss_nodes_return: array containing the pressure loss at each return node         (1 x n)
    :return pressure_loss_system: pressure loss over the entire network
    :rtype pressure_loss_nodes_supply: ndarray
    :rtype pressure_loss_nodes_return: ndarray
    :rtype pressure_loss_system: float

    .. [Todini & Pilati, 1987] Todini & Pilati. "A gradient method for the analysis of pipe networks," in Computer
       Applications in Water Supply Volume 1 - Systems Analysis and Simulation, 1987.

    .. [Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
       Applied Thermal Engineering, 2016.
    """
    ## change pipe flow directions in the edge_node_df_t according to the flow conditions
    change_to_edge_node_matrix_t(edge_mass_flow, edge_node_df)

    # get the temperatures at each supply and return edge
    temperature_supply_edges_K = calc_edge_temperatures(T_supply_node_K, edge_node_df)
    temperature_return_edges_K = calc_edge_temperatures(T_return_node_K, edge_node_df)

    # get the pressure drop through each edge
    pressure_loss_pipe_supply_Pa = calc_pressure_loss_pipe(pipe_diameter, pipe_length, edge_mass_flow,
                                                           temperature_supply_edges_K, gv)
    pressure_loss_pipe_return_Pa = calc_pressure_loss_pipe(pipe_diameter, pipe_length, edge_mass_flow,
                                                           temperature_return_edges_K, gv)

    # total pressure loss in the system
    # # pressure losses at the supply plant are assumed to be included in the pipe losses as done by Oppelt et al., 2016
    # pressure_loss_system = sum(np.nan_to_num(pressure_loss_pipe_supply)[0]) + sum(
    #     np.nan_to_num(pressure_loss_pipe_return)[0])
    pressure_loss_system_Pa = calc_pressure_loss_system(pressure_loss_pipe_supply_Pa, pressure_loss_pipe_return_Pa)

    # solve for the pressure at each node based on Eq. 1 in Todini & Pilati for no = 0 (no nodes with fixed head):
    # A12 * H + F(Q) = -A10 * H0 = 0
    # edge_node_transpose * pressure_nodes = - (pressure_loss_pipe) (Ax = b)
    edge_node_transpose = np.transpose(edge_node_df.values)
    pressure_nodes_supply_Pa = np.round(
        np.transpose(np.linalg.lstsq(edge_node_transpose, np.transpose(pressure_loss_pipe_supply_Pa) * (-1))[0]),
        decimals=9)
    pressure_nodes_return_Pa = np.round(
        np.transpose(np.linalg.lstsq(-edge_node_transpose, np.transpose(pressure_loss_pipe_return_Pa) * (-1))[0]),
        decimals=9)
    return pressure_nodes_supply_Pa, pressure_nodes_return_Pa, pressure_loss_system_Pa


def change_to_edge_node_matrix_t(edge_mass_flow, edge_node_df):
    """
    The function change the flow directions in edge_node_df to align with flow directions at each time-step, this way
    all the mass flows are positive.
    :param edge_mass_flow:
    :param edge_node_df: edge node matrix
    :return:
    """
    while edge_mass_flow.min() < 0:
        for i in range(len(edge_mass_flow)):
            if edge_mass_flow[i] < 0:
                edge_mass_flow[i] = abs(edge_mass_flow[i])
                edge_node_df[edge_node_df.columns[i]] = -edge_node_df[edge_node_df.columns[i]]


def calc_pressure_loss_pipe(pipe_diameter_m, pipe_length_m, mass_flow_rate_kgs, temperature_K, gv):
    """
    Calculates the pressure losses throughout a pipe based on the Darcy-Weisbach equation and the Swamee-Jain
    solution for the Darcy friction factor [Oppelt et al., 2016].

    :param pipe_diameter_m: vector containing the pipe diameter in m for each edge e in the network           (e x 1)
    :param pipe_length_m: vector containing the length in m of each edge e in the network                     (e x 1)
    :param mass_flow_rate_kgs: matrix containing the mass flow rate in each edge e at time t                    (t x e)
    :param temperature_K: matrix containing the temperature of the water in each edge e at time t             (t x e)
    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)
    :type pipe_diameter_m: ndarray
    :type pipe_length_m: ndarray
    :type mass_flow_rate_kgs: ndarray
    :type temperature_K: list
    :type gv: GlobalVariables

    :return pressure_loss_edge: pressure loss through each edge e at each time t                            (t x e)
    :rtype pressure_loss_edge: ndarray

    ..[Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
    Applied Thermal Engineering, 2016.

    """
    reynolds = calc_reynolds(mass_flow_rate_kgs, gv, temperature_K, pipe_diameter_m)

    darcy = calc_darcy(pipe_diameter_m, reynolds, gv.roughness)

    # calculate the pressure losses through a pipe using the Darcy-Weisbach equation
    pressure_loss_edge_Pa = darcy * 8 * mass_flow_rate_kgs ** 2 * pipe_length_m / (
        math.pi ** 2 * pipe_diameter_m ** 5 * gv.Pwater)
    # todo: add pressure loss in valves, corners, etc., e.g. equivalent length method, or K Method
    return pressure_loss_edge_Pa


def calc_pressure_loss_system(pressure_loss_pipe_supply, pressure_loss_pipe_return):
    pressure_loss_system = np.full(3, np.nan)
    pressure_loss_system[0] = sum(np.nan_to_num(pressure_loss_pipe_supply)[0])
    pressure_loss_system[1] = sum(np.nan_to_num(pressure_loss_pipe_return)[0])
    pressure_loss_system[2] = pressure_loss_system[0] + pressure_loss_system[1]
    return pressure_loss_system


def calc_darcy(pipe_diameter_m, reynolds, pipe_roughness_m):
    """
    Calculates the Darcy friction factor [Oppelt et al., 2016].

    :param pipe_diameter_m: vector containing the pipe diameter in m for each edge e in the network           (e x 1)
    :param reynolds: vector containing the reynolds number of flows in each edge in that timestep	      (e x 1)
    :param pipe roughness_m: float with pipe roughness
    :type pipe_diameter_m: ndarray
    :type reynolds: ndarray
    :type pipe_roughness_m: float

    :return nusselt: calculated darcy friction factor for flow in each edge		(ex1)
    :rtype nusselt: ndarray

        ..[Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
    Applied Thermal Engineering, 2016.

	.. Incropera, F. P., DeWitt, D. P., Bergman, T. L., & Lavine, A. S. (2007). Fundamentals of Heat and Mass Transfer. Fundamentals of Heat and Mass Transfer. https://doi.org/10.1016/j.applthermaleng.2011.03.022

    """

    darcy = np.zeros(reynolds.size)
    # necessary to make sure pipe_diameter is 1D vector as input formats can vary
    if hasattr(pipe_diameter_m[0], '__len__'):
        pipe_diameter_m = pipe_diameter_m[0]
    for rey in range(reynolds.size):
        if reynolds[rey] <= 1:
            darcy[rey] = 0
        elif reynolds[rey] <= 2300:
            # calculate the Darcy-Weisbach friction factor for laminar flow
            darcy[rey] = 64 / reynolds[rey]
        elif reynolds[rey] <= 5000:
            # calculate the Darcy-Weisbach friction factor for transient flow (for pipe roughness of e/D=0.0002,
            # @low reynolds numbers lines for smooth pipe nearl identical in Moody Diagram) so smooth pipe approximation used
            darcy[rey] = 0.316 * reynolds[rey] ** -0.25
        else:
            # calculate the Darcy-Weisbach friction factor using the Swamee-Jain equation, applicable for Reynolds= 5000 - 10E8; pipe_roughness=10E-6 - 0.05
            darcy[rey] = 1.325 * np.log(
                pipe_roughness_m / (3.7 * pipe_diameter_m[rey]) + 5.74 / reynolds[rey] ** 0.9) ** (-2)

    return darcy


def calc_reynolds(mass_flow_rate_kgs, gv, temperature_K, pipe_diameter_m):
    """
    Calculates the reynolds number of the internal flow inside the pipes.

    :param pipe_diameter_m: vector containing the pipe diameter in m for each edge e in the network           (e x 1)
    :param mass_flow_rate_kgs: matrix containing the mass flow rate in each edge e at time t                    (t x e)
    :param temperature_K: matrix containing the temperature of the water in each edge e at time t             (t x e)
    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)
    :type pipe_diameter_m: ndarray
    :type mass_flow_rate_kgs: ndarray
    :type temperature_K: list
    :type gv: GlobalVariables
    """
    kinematic_viscosity_m2s = calc_kinematic_viscosity(temperature_K)  # m2/s
    reynolds = np.nan_to_num(
        4 * (abs(mass_flow_rate_kgs) / gv.Pwater) / (math.pi * kinematic_viscosity_m2s * pipe_diameter_m))
    # necessary if statement to make sure ouput is an array type, as input formats of files can vary
    if hasattr(reynolds[0], '__len__'):
        reynolds = reynolds[0]
    return reynolds


def calc_prandtl(gv, temperature_K):
    """
    Calculates the prandtl number of the internal flow inside the pipes.

    :param temperature_K: matrix containing the temperature of the water in each edge e at time t             (t x e)
    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)
    :type temperature_K: list
    :type gv: GlobalVariables
    """
    kinematic_viscosity_m2s = calc_kinematic_viscosity(temperature_K)  # m2/s
    thermal_conductivity = calc_thermal_conductivity(temperature_K)  # W/(m*K)

    return np.nan_to_num(kinematic_viscosity_m2s * gv.Pwater * gv.Cpw * 1000 / thermal_conductivity)


def calc_kinematic_viscosity(temperature):
    """
    Calculates the kinematic viscosity of water as a function of temperature based on a simple fit from data from the
    engineering toolbox.

    :param temperature: in K
    :return: kinematic viscosity in m2/s
    """

    return 2.652623e-8 * math.e ** (557.5447 * (temperature - 140) ** -1)


def calc_thermal_conductivity(temperature):
    """
    Calculates the thermal conductivity of water as a function of temperature based on a fit proposed in:

    :param temperature: in K
    :return: thermal conductivity in W/(m*K)

    ... Standard Reference Data for the Thermal Conductivity of Water
    Ramires, Nagasaka, et al.
    1994

    """

    return 0.6065 * (-1.48445 + 4.12292 * temperature / 298.15 - 1.63866 * (temperature / 298.15) ** 2)


def calc_max_edge_flowrate(all_nodes_df, building_names, buildings_demands, edge_node_df, gv, locator,
                           substations_HEX_specs, t_target_supply, network_type, network_name):
    """
    Calculates the maximum flow rate in the network in order to assign the pipe diameter required at each edge. This is
    done by calculating the mass flow rate required at each substation to supply the calculated demand at the target
    supply temperature for each time step, finding the maximum for each node throughout the year and calculating the
    resulting necessary mass flow rate at each edge to satisfy this demand.

    :param all_nodes_df: DataFrame containing all nodes and whether a node n is a consumer or plant node
                        (and if so, which building that node corresponds to), or neither.                   (2 x n)
    :param building_names: list of building names in the scenario
    :param buildings_demands: demand of each building in the scenario
    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0.                                        (n x e)
    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)
    :param locator: an InputLocator instance set to the scenario to work on
    :param substations_HEX_specs: DataFrame with substation heat exchanger specs at each building.
    :param t_target_supply: target supply temperature at each substation
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling
                         ('DC') network
    :type all_nodes_df: DataFrame
    :type gv: GlobalVariables
    :type locator: InputLocator
    :type substations_HEX_specs: DataFrame
    :type network_type: str

    :return edge_mass_flow_df: mass flow rate at each edge throughout the year
    :return max_edge_mass_flow_df: maximum mass flow at each edge to be used for pipe sizing
    :rtype edge_mass_flow_df: DataFrame
    :rtype max_edge_mass_flow_df: DataFrame

    """

    # create empty DataFrames to store results
    edge_mass_flow_df = pd.DataFrame(data=np.zeros((8760, len(edge_node_df.columns.values))),
                                     columns=edge_node_df.columns.values)

    node_mass_flow_df = pd.DataFrame(data=np.zeros((8760, len(edge_node_df.index))),
                                     columns=edge_node_df.index.values)  # input parameters for validation

    print('start calculating mass flows in edges...')

    t0 = time.clock()
    for t in range(8760):
        print('\n calculating mass flows in edges... time step', t)

        # set to the highest value in the network and assume no loss within the network
        T_substation_supply = t_target_supply.ix[t].max() + 273.15  # in [K]

        # calculate substation flow rates and return temperatures
        if network_type == 'DH' or (network_type == 'DC' and math.isnan(T_substation_supply) == False):
            T_return_all, \
            mdot_all = substation.substation_return_model_main(locator, gv, building_names, buildings_demands,
                                                               substations_HEX_specs, T_substation_supply, t,
                                                               network_type,
                                                               t_flag=True)
            # t_flag = True: same temperature for all nodes
        else:
            T_return_all = np.full(building_names.size, T_substation_supply).T
            mdot_all = pd.DataFrame(data=np.zeros(len(building_names)), index=building_names.values).T

        # write consumer substation required flow rate to nodes
        required_flow_rate_df = write_substation_values_to_nodes_df(all_nodes_df, mdot_all)
        # (1 x n)

        # solve mass flow rates on edges
        edge_mass_flow_df[:][t:t + 1] = calc_mass_flow_edges(edge_node_df, required_flow_rate_df, all_nodes_df)
        node_mass_flow_df[:][t:t + 1] = required_flow_rate_df.values

    edge_mass_flow_df.to_csv(locator.get_edge_mass_flow_csv_file(network_type, network_name))
    node_mass_flow_df.to_csv(locator.get_node_mass_flow_csv_file(network_type, network_name))
    print(time.clock() - t0, "seconds process time for edge mass flow calculation\n")

    ## The script below is to bypass the calculation from line 457-490, if the above calculation has been done once.
    # edge_mass_flow_df = pd.read_csv(locator.get_edge_mass_flow_csv_file(network_type, network_name))
    # del edge_mass_flow_df['Unnamed: 0']

    # assign pipe properties based on max flow on edges
    max_edge_mass_flow_df = pd.DataFrame(data=[(edge_mass_flow_df.abs()).max(axis=0)], columns=edge_node_df.columns)

    return edge_mass_flow_df, max_edge_mass_flow_df


def read_max_edge_flowrate(edge_node_df, locator, network_type):
    """
    This is a temporary function to read from file and save run time for 'calc_max_edge_flowrate'.

    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0.                                        (n x e)
    :param locator: an InputLocator instance set to the scenario to work on
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling
                        ('DC') network
    :type edge_node_df: DataFrame
    :type locator: InputLocator
    :type network_type: str

    :return edge_mass_flow_df: mass flow rate at each edge throughout the year
    :return max_edge_mass_flow_df: maximum mass flow at each edge to be used for pipe sizing
    :rtype edge_mass_flow_df: DataFrame
    :rtype max_edge_mass_flow_df: DataFrame
    """

    edge_mass_flow_df = pd.read_csv(locator.get_optimization_network_layout_folder() + '//' + 'NominalEdgeMassFlow_' +
                                    network_type + '.csv')
    del edge_mass_flow_df['Unnamed: 0']

    # find maximum mass flow rate on each edges in order to assign pipe properties
    max_edge_mass_flow = edge_mass_flow_df.max(axis=0)
    max_edge_mass_flow_df = pd.DataFrame(data=[max_edge_mass_flow], columns=edge_node_df.columns)

    return edge_mass_flow_df, max_edge_mass_flow_df


def calc_edge_temperatures(temperature_node, edge_node):
    """
    Calculates the temperature at each edge assuming the average temperature in the edge is equal to the average of the
    temperatures at its start and end node as done, for example, by Wang et al. (2016), that is::

        T_edge = (T_node_1 + T_node_2)/2

    :param temperature_node: array containing the temperature in each node n                                (1 x n)
    :param edge_node: matrix consisting of n rows (number of nodes) and e columns (number of edges) and
                      indicating the direction of flow of each edge e at node n: if e points to n, value
                      is 1; if e leaves node n, -1; else, 0.                                                (n x e)

    :return temperature_edge: array containing the temperature in each edge e                               (1 x n)

    ..[Wang et al., 2016] Wang et al. "A method for the steady-state thermal simulation of district heating systems and
    model parameters calibration," in Energy Conversion and Management Vol. 120, 2016, pp. 294-305.
    """

    # necessary to avoid nan propagation in edge temperature vector. E.g. if node 1 = 300 K, node 2 = nan: T_edge = 150K -> nan.
    # solution is to replace nan with the mean temperature of all nodes
    tempareture_node_mean = np.nanmean(temperature_node)
    temperature_node[np.isnan(temperature_node)] = tempareture_node_mean

    # in order to calculate the edge temperatures, node temperature values of 'nan' were not acceptable
    # so these were converted to 0 and then converted back to 'nan'
    temperature_edge = np.dot(np.nan_to_num(temperature_node), abs(edge_node) / 2)
    temperature_edge[temperature_edge < 273.15] = np.nan
    # todo: could be updated with more accurate exponential temperature profile of edges for mean pipe temperature, or mean value of that function to avoid spacial component
    return temperature_edge


# ===========================
# Thermal calculation
# ===========================


def solve_network_temperatures(locator, gv, T_ground, edge_node_df, all_nodes_df, edge_mass_flow_df,
                               t_target_supply_df, building_names, buildings_demands, substations_HEX_specs, t,
                               network_type, edge_df, pipe_properties_df):
    """
    This function calculates the node temperatures at time-step t accounting for heat losses throughout the network.
    There is one iteration to determine weather the substation supply temperature and the substation mass flow are
    cohesive. It is done as follow: The substation supply temperatures (T_substation_supply) are calculated based on the
    nominal edge flow rate (see `calc_max_edge_flowrate`), and then the substation mass flow requirements
    (mass_flow_substation_nodes_df) and pipe mass flows (edge_mass_flow_df_2) are updated accordingly. Following, the
    substation supply temperatures(T_substation_supply_2) are recalcuated with the updated pipe mass flow.

    The iteration continues until the substation supply temperatures converged.

    Lastly, the plant heat requirements are calculated base on the plant supply/return temperatures and flow rates.

    :param locator: an InputLocator instance set to the scenario to work on
    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)
    :param T_ground: vector with ground temperatures in K
    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0.                                        (n x e)
    :param all_nodes_df: DataFrame containing all nodes and whether a node n is a consumer or plant node
                        (and if so, which building that node corresponds to), or neither.                   (2 x n)
    :param edge_mass_flow_df: mass flow rate at each edge throughout the year
    :param t_target_supply_df: target supply temperature at each substation
    :param building_names: list of building names in the scenario
    :param buildings_demands: demand of each building in the scenario
    :param substations_HEX_specs: DataFrame with substation heat exchanger specs at each building.
    :param t: current time step
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling
                        ('DC') network
    :param edge_df: list of edges and their corresponding lengths and start and end nodes
    :param pipe_properties_df: DataFrame containing the pipe properties for each edge in the network

    :type locator: InputLocator
    :type gv: GlobalVariables
    :type edge_node_df: DataFrame
    :type all_nodes_df: DataFrame
    :type edge_mass_flow_df: DataFrame
    :type locator: InputLocator
    :type substations_HEX_specs: DataFrame
    :type network_type: str
    :type t_target_supply_df: DataFrame
    :type edge_df: DataFrame
    :type pipe_properties_df: DataFrame

    :returns T_supply_nodes: list of supply line node temperatures (nx1)
    :rtype T_supply_nodes: list of arrays
    :returns T_return_nodes: list of return line node temperatures (nx1)
    :rtype T_return_nodes: list of arrays
    :returns plant_heat_requirement: list of plant heat requirement
    :rtype plant_heat_requirement: list of arrays

    """

    if edge_mass_flow_df.values.sum() != 0:
        ## change pipe flow directions in the edge_node_df_t according to the flow conditions
        change_to_edge_node_matrix_t(edge_mass_flow_df, edge_node_df)

        # initialize target temperatures in Kelvin as initial value for K_value calculation
        initial_guess_temp = np.asarray(t_target_supply_df.loc[t] + 273.15, order='C')
        T_edge_K = calc_edge_temperatures(initial_guess_temp, edge_node_df)
        # initialization of K_value
        K = calc_aggregated_heat_conduction_coefficient(edge_mass_flow_df, locator, gv, edge_df,
                                                        pipe_properties_df, T_edge_K, network_type)  # [kW/K]

        ## calculate node temperatures on the supply network accounting losses in the network.
        T_supply_nodes_K, plant_node, q_loss_edges_kW = calc_supply_temperatures(gv, T_ground[t], edge_node_df,
                                                                                 edge_mass_flow_df, K,
                                                                                 t_target_supply_df.loc[t],
                                                                                 network_type)

        # write supply temperatures to substation nodes
        T_substation_supply_K = write_nodes_values_to_substations(T_supply_nodes_K, all_nodes_df, plant_node)

        ## iterations to find out the corresponding node supply temperature and substation mass flow
        flag = 0
        iteration = 0
        while flag == 0:
            # calculate substation return temperatures according to supply temperatures
            consumer_building_names = all_nodes_df.loc[all_nodes_df['Type'] == 'CONSUMER', 'Building'].values
            T_return_all_K, \
            mdot_all_kgs = substation.substation_return_model_main(locator, gv, consumer_building_names,
                                                                   buildings_demands,
                                                                   substations_HEX_specs, T_substation_supply_K, t,
                                                                   network_type, t_flag=False)
            if mdot_all_kgs.values.max() == np.nan:
                print('Error in edge mass flow! Check edge_mass_flow_df')

            # write consumer substation return T and required flow rate to nodes
            # T_substation_return_df = write_substation_temperatures_to_nodes_df(all_nodes_df, T_return_all_K)  # (1 x n) #todo:potentially redundant
            mass_flow_substations_nodes_df = write_substation_values_to_nodes_df(all_nodes_df, mdot_all_kgs)

            # solve for the required mass flow rate on each pipe
            edge_mass_flow_df_2_kgs = calc_mass_flow_edges(edge_node_df, mass_flow_substations_nodes_df, all_nodes_df)
            edge_node_df_2 = edge_node_df.copy()
            while edge_mass_flow_df_2_kgs.min() < 0:
                for i in range(len(edge_mass_flow_df_2_kgs[0])):
                    if edge_mass_flow_df_2_kgs[0][i] < 0:
                        edge_mass_flow_df_2_kgs[0][i] = abs(edge_mass_flow_df_2_kgs[0][i])
                        edge_node_df_2[edge_node_df_2.columns[i]] = -edge_node_df_2[edge_node_df_2.columns[i]]
                edge_mass_flow_df_2_kgs = calc_mass_flow_edges(edge_node_df_2, mass_flow_substations_nodes_df,
                                                               all_nodes_df)

            # calculate updated pipe aggregated heat conduction coefficient with new mass flows
            K = calc_aggregated_heat_conduction_coefficient(edge_mass_flow_df_2_kgs, locator, gv, edge_df,
                                                            pipe_properties_df, T_edge_K, network_type)  # [kW/K]

            # calculate updated node temperatures on the supply network with updated edge mass flow
            T_supply_nodes_2_K, plant_node, q_loss_edges_2_kW = calc_supply_temperatures(gv, T_ground[t],
                                                                                         edge_node_df_2,
                                                                                         edge_mass_flow_df_2_kgs, K,
                                                                                         t_target_supply_df.loc[t],
                                                                                         network_type)
            # calculate edge temperature for heat transfer coefficient within loop iteration
            T_edge_K = calc_edge_temperatures(T_supply_nodes_2_K, edge_node_df_2)

            # write supply temperatures to substation nodes
            T_substation_supply_2 = write_nodes_values_to_substations(T_supply_nodes_2_K, all_nodes_df, plant_node)

            # check if the supply temperature at substations converged
            node_dT = T_substation_supply_2 - T_substation_supply_K
            if len(abs(node_dT).dropna(axis=1)) == 0:
                max_node_dT = 0
            else:
                max_node_dT = max(abs(node_dT).dropna(axis=1).values[0])
                # max supply node temperature difference

            if max_node_dT > 1 and iteration < 10:
                # update the substation supply temperature and re-enter the iteration
                T_substation_supply_K = T_substation_supply_2
                print(iteration, 'iteration. Maximum node temperature difference:', max_node_dT)
                iteration += 1
            elif max_node_dT > 10 and 20 > iteration >= 10:
                # FIXME: This is to avoid endless iteration, other design strategies should be implemented.
                # update the substation supply temperature and re-enter the iteration
                T_substation_supply_K = T_substation_supply_2
                print(iteration, 'iteration. Maximum node temperature difference:', max_node_dT)
                iteration += 1
            else:
                # calculate substation return temperatures according to supply temperatures
                T_return_all_2, \
                mdot_all_2 = substation.substation_return_model_main(locator, gv, building_names, buildings_demands,
                                                                     substations_HEX_specs, T_substation_supply_2, t,
                                                                     network_type, t_flag=False)
                # write consumer substation return T and required flow rate to nodes
                T_substation_return_df_2 = write_substation_temperatures_to_nodes_df(all_nodes_df,
                                                                                     T_return_all_2)  # (1xn)
                mass_flow_substations_nodes_df_2 = write_substation_values_to_nodes_df(all_nodes_df, mdot_all_2)
                # solve for the required mass flow rate on each pipe, using the nominal edge node matrix
                edge_mass_flow_df_2_kgs = calc_mass_flow_edges(edge_node_df_2, mass_flow_substations_nodes_df_2,
                                                               all_nodes_df)

                # make sure that all mass flows are still positive after last calculation
                while edge_mass_flow_df_2_kgs.min() < 0:
                    for i in range(len(edge_mass_flow_df_2_kgs[0])):
                        if edge_mass_flow_df_2_kgs[0][i] < 0:
                            edge_mass_flow_df_2_kgs[0][i] = abs(edge_mass_flow_df_2_kgs[0][i])
                            edge_node_df_2[edge_node_df_2.columns[i]] = -edge_node_df_2[edge_node_df_2.columns[i]]
                    edge_mass_flow_df_2_kgs = calc_mass_flow_edges(edge_node_df_2, mass_flow_substations_nodes_df_2,
                                                                   all_nodes_df)

                # exit iteration
                flag = 1
                if max_node_dT < 1:
                    print('supply temperature converged after', iteration, 'iterations.', 'dT:', max_node_dT)
                else:
                    print('Warning: supply temperature did not converge after', iteration, 'iterations at timestep', t,
                          '. dT:', max_node_dT)

        # calculate node temperatures on the return network
        edge_mass_flow_df_t = calc_mass_flow_edges(edge_node_df_2, mass_flow_substations_nodes_df_2,
                                                   all_nodes_df)  # edge-node matrix with no negative flow at the current time-step
        # make sure all mass flows are positive
        while edge_mass_flow_df_t.min() < 0:
            for i in range(len(edge_mass_flow_df_t[0])):
                if edge_mass_flow_df_t[0][i] < 0:
                    edge_mass_flow_df_t[0][i] = abs(edge_mass_flow_df_t[0][i])
                    edge_node_df_2[edge_node_df_2.columns[i]] = -edge_node_df_2[edge_node_df_2.columns[i]]
                edge_mass_flow_df_t = calc_mass_flow_edges(edge_node_df_2, mass_flow_substations_nodes_df_2,
                                                           all_nodes_df)

        # calculate final edge temperature and heat transfer coefficient
        # todo: suboptimal because using supply temperatures (limited effect since effects only water conductivity). Could be solved by iteration.
        K = calc_aggregated_heat_conduction_coefficient(edge_mass_flow_df_2_kgs, locator, gv, edge_df,
                                                        pipe_properties_df, T_edge_K, network_type)  # [kW/K]

        T_return_nodes_2_K = calc_return_temperatures(gv, T_ground[t], edge_node_df_2, edge_mass_flow_df_t,
                                                      mass_flow_substations_nodes_df_2, K, T_substation_return_df_2)

        # calculate plant heat requirements according to plant supply/return temperatures
        plant_heat_requirement_kW = calc_plant_heat_requirement(plant_node, T_supply_nodes_2_K, T_return_nodes_2_K,
                                                                mass_flow_substations_nodes_df_2, gv)

    else:
        T_supply_nodes_2_K = np.full(edge_node_df.shape[0], np.nan)
        T_return_nodes_2_K = np.full(edge_node_df.shape[0], np.nan)
        q_loss_edges_2_kW = np.full(edge_node_df.shape[1], 0)
        edge_mass_flow_df_2_kgs = edge_mass_flow_df
        plant_heat_requirement_kW = np.full(sum(all_nodes_df['Type'] == 'PLANT'), 0)

    return T_supply_nodes_2_K, T_return_nodes_2_K, plant_heat_requirement_kW, edge_mass_flow_df_2_kgs, q_loss_edges_2_kW


def calc_plant_heat_requirement(plant_node, T_supply_nodes, T_return_nodes, mass_flow_substations_nodes_df, gv):
    """
    calculate plant heat requirements according to plant supply/return temperatures and flow rate
    :param plant_node: list of plant nodes
    :param T_supply_nodes: node temperatures on the supply network
    :param T_return_nodes: node temperatures on the return network
    :param mass_flow_substations_nodes_df: substation mass flows
    :param gv: global variable
    :type plant_node: ndarray
    :type T_supply_nodes: ndarray
    :type T_return_nodes: ndarray
    :type mass_flow_substations_nodes_df: pandas dataframe
    :return:
    """
    plant_heat_requirement_kW = np.full(plant_node.size, np.nan)
    for i in range(plant_node.size):
        node = plant_node[i]
        heat_requirement = gv.Cpw * (T_supply_nodes[node] - T_return_nodes[node]) * abs(
            mass_flow_substations_nodes_df.iloc[0, node])
        plant_heat_requirement_kW[i] = heat_requirement
    return plant_heat_requirement_kW


def write_nodes_values_to_substations(T_supply_nodes, all_nodes_df, plant_node):
    """
    This function writes node values to the corresponding building substations.

    :param T_supply_nodes: DataFrame of supply line node temperatures (nx1)
    :param all_nodes_df: DataFrame that contains all nodes, whether a node is a consumer, plant, or neither,
                        and, if it is a consumer or plant, the name of the corresponding building               (2 x n)
    :param plant_node: the indices of the plant node(s)

    :type T_supply_nodes: DataFrame
    :type all_nodes_df: DataFrame
    :type plant_node: numpy array

    :return T_substation_supply: dataframe with node values matched to building substations
    :rtype T_substation_supply: DataFrame
    """
    all_nodes_df['T_supply'] = T_supply_nodes
    T_substation_supply = all_nodes_df[all_nodes_df.Building != 'NONE'].set_index(['Building'])
    T_substation_supply = T_substation_supply.drop('Type', axis=1)
    return T_substation_supply.T


def calc_supply_temperatures(gv, T_ground_K, edge_node_df, mass_flow_df, K, t_target_supply_C, network_type):
    """
    This function calculate the node temperatures considering heat losses in the supply network.
    Starting from the plant supply node, the function go through the edge-node index to search for the outlet node, and
    calculate the outlet node temperature after heat loss. And starting from the outlet node, the function calculates
    the node temperature at the corresponding pipe outlet, and the calculation goes on until all the node temperatures
    are solved. At nodes connecting to multiple pipes, the mixing temperature is calculated.

    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)
    :param T_ground_K: vector with ground temperatures in K
    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0.                                        (n x e)
    :param mass_flow_df: DataFrame containing the mass flow rate for each edge e at each time of the year t (1 x e)
    :param K: aggregated heat conduction coefficient for each pipe                                          (1 x e)
    :param t_target_supply_C: target supply temperature at each substation
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling ('DC')
                         network

    :type gv: GlobalVariables
    :type edge_node_df: DataFrame
    :type mass_flow_df: DataFrame
    :type network_type: str

    :return T_node.T: list of node temperatures (nx1)
    :return plant_node: the index of the plant node
    :rtype T_node.T: list
    :rtype plant_node: numpy array

    """
    Z = np.asarray(edge_node_df)  # (nxe) edge-node matrix
    Z_pipe_out = Z.clip(min=0)  # pipe outlet matrix
    Z_pipe_in = Z.clip(max=0)  # pipe inlet matrix

    M_d = np.zeros((Z.shape[1], Z.shape[1]))  # (exe) pipe mass flow rate matrix
    np.fill_diagonal(M_d, mass_flow_df)

    # matrices to store results
    T_e_out = Z_pipe_out.copy()
    T_e_in = Z_pipe_in.copy().dot(-1)
    T_node = np.zeros(Z.shape[0])
    Z_note = Z.copy()  # matrix to store information of solved nodes

    # start node temperature calculation
    flag = 0
    # set initial supply temperature guess to the target substation supply temperature
    T_plant_sup_0 = 273.15 + t_target_supply_C.max() if network_type == 'DH' else 273.15 + t_target_supply_C.min()
    T_plant_sup = T_plant_sup_0
    iteration = 0
    while flag == 0:
        # # calculate the pipe outlet temperature from the plant node
        for i in range(Z.shape[0]):
            if np.argwhere(Z[i] == 1).size == 0:  # find plant node
                # write plant inlet temperature
                T_node[i] = T_plant_sup  # assume plant inlet temperature
                edge = np.where(T_e_in[i] != 0)[0]  # find edge index
                T_e_in[i] = T_e_in[i] * T_node[i]
                # calculate pipe outlet temperature
                calc_t_out(i, edge, K, M_d, Z, T_e_in, T_e_out, T_ground_K, Z_note, gv)
        plant_node = T_node.nonzero()[0]  # the node indices of the plant nodes in the edge-node index

        # # calculate pipe outlet temperature and node temperature for the rest
        while np.count_nonzero(T_node == 0) > 0:
            for j in range(Z.shape[0]):
                # check if all inlet flow info towards node j are known (only -1 left in row Z_note[j])
                if np.count_nonzero(Z_note[j] == 1) == 0 and np.count_nonzero(Z_note[j] == 0) != Z.shape[1]:
                    # calculate node temperature with merging flows from pipes
                    part1 = np.dot(M_d, T_e_out[j]).sum()
                    part2 = np.dot(M_d, Z_pipe_out[j]).sum()
                    T_node[j] = part1 / part2
                    if T_node[j] == np.nan:
                        raise ValueError('The are no flow entering/existing ', edge_node_df.index[j],
                                         '. Please check if the edge_node_df make sense.')
                    # write the node temperature to the corresponding pipe inlet
                    T_e_in[j] = T_e_in[j] * T_node[j]

                    # calculate pipe outlet temperatures entering from node j
                    for edge in range(Z_note.shape[1]):
                        # find the pipes with water flow leaving from node j
                        if T_e_in[j, edge] != 0:
                            # calculate the pipe outlet temperature entering from node j
                            calc_t_out(j, edge, K, M_d, Z, T_e_in, T_e_out, T_ground_K, Z_note, gv)

                # fill in temperatures for nodes at network branch ends
                elif T_node[j] == 0 and T_e_out[j].max() != 1:
                    T_node[j] = np.nan if np.isnan(T_e_out[j]).any() else T_e_out[j].max()
                elif T_e_out[j].min() < 0:
                    print('negative node temperature!')

        # # iterate the plant supply temperature until all the node temperature reaches the target temperatures
        if network_type == 'DH':
            # calculate the difference between node temperature and the target supply temperature at substations
            # [K] temperature differences b/t node supply and target supply
            dT = (T_node - (t_target_supply_C + 273.15)).dropna()
            # enter iteration if the node supply temperature is lower than the target supply temperature
            # (0.1 is the tolerance)
            if all(dT > -0.1) == False and (T_plant_sup - T_plant_sup_0) < 60:
                # increase plant supply temperature and re-iterate the node supply temperature calculation
                # increase by the maximum amount of temperature deficit at nodes
                T_plant_sup = T_plant_sup + abs(dT.min())
                # check if this term is positive, looping causes T_e_out to sink instead of rise.

                # reset the matrices for supply network temperature calculation
                Z_note = Z.copy()
                T_e_out = Z_pipe_out.copy()
                T_e_in = Z_pipe_in.copy().dot(-1)
                T_node = np.zeros(Z.shape[0])
                iteration += 1

            elif all(dT > -0.1) == False and (T_plant_sup - T_plant_sup_0) >= 60:
                # end iteration if total network temperature drop is higher than 60 K
                print('cannot fulfill substation supply node temperature requirement after iterations:',
                      iteration, dT.min())
                node_insufficient = dT[dT < 0].index.values
                for node in range(node_insufficient.size):
                    index_insufficient = np.argwhere(edge_node_df.index == node_insufficient[node])[0]
                    T_node[index_insufficient] = t_target_supply_C[index_insufficient] + 273.15
                    # force setting node temperature to target to avoid substation HEX calculation error.
                    # However, it might potentially cause error at mass flow iteration.
                flag = 1
            else:
                flag = 1
        else:  # when network type == 'DC'
            # calculate the difference between node temperature and the target supply temperature at substations
            # [K] temperature differences b/t node supply and target supply
            dT = (T_node - (t_target_supply_C + 273.15)).dropna()

            # enter iteration if the node supply temperature is higher than the target supply temperature
            # (0.1 is the tolerance)
            if all(dT < 0.1) == False and (T_plant_sup_0 - T_plant_sup) < 10:
                # increase plant supply temperature and re-iterate the node supply temperature calculation
                # increase by the maximum amount of temperature deficit at nodes
                T_plant_sup = T_plant_sup - abs(dT.max())
                Z_note = Z.copy()
                T_e_out = Z_pipe_out.copy()
                T_e_in = Z_pipe_in.copy().dot(-1)
                T_node = np.zeros(Z.shape[0])
                iteration += 1
            elif all(dT < 0.1) == False and (T_plant_sup_0 - T_plant_sup) >= 10:
                # end iteration if total network temperature rise is higher than 10 K
                print('cannot fulfill substation supply node temperature requirement after iterations:',
                      iteration, dT.min())
                node_insufficient = dT[dT > 0].index.values
                for node in range(node_insufficient.size):
                    index_insufficient = np.argwhere(edge_node_df.index == node_insufficient[node])[0]
                    T_node[index_insufficient] = t_target_supply_C[index_insufficient] + 273.15
                    # force setting node temperature to target to avoid substation HEX calculation error.
                    # However, it might potentially cause error at mass flow iteration.
                    flag = 1
            else:
                flag = 1

    # calculate pipe heat losses
    q_loss_edges_kW = np.zeros(Z_note.shape[1])
    for edge in range(Z_note.shape[1]):
        if M_d[edge, edge] > 0:
            dT_edge = np.nanmax(T_e_in[:, edge]) - np.nanmax(T_e_out[:, edge])
            q_loss_edges_kW[edge] = M_d[edge, edge] * gv.Cpw * dT_edge  # kW

    return T_node.T, plant_node, q_loss_edges_kW


def calc_return_temperatures(gv, T_ground, edge_node_df, mass_flow_df, mass_flow_substation_df, K, t_return):
    """
    This function calculates the node temperatures considering heat losses in the return line.
    Starting from the substations at the end branches, the function goes through the edge-node index to search for the
    outlet node, and calculates the outlet node temperature after heat loss. Starting from that outlet node, the function
    calculates the node temperature at the corresponding pipe outlet, and the calculation goes on until all the node
    temperatures are solved. At nodes connecting to multiple pipes, the mixing temperature is calculated.

    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)
    :param T_ground: vector with ground temperatures in K
    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0.
    :param mass_flow_df: DataFrame containing the mass flow rate for each edge e at each t
    :param mass_flow_substation_df: DataFrame containing the mass flow rate for each substation at each t
    :param K: aggregated heat conduction coefficient for each pipe
    :param t_return: return temperatures at the substations

    :return T_node.T: list of node temperatures (nx1)
    :rtype T_node.T: list

    """

    Z = np.asarray(edge_node_df) * (-1)  # (n x e) edge-node matrix
    Z_pipe_out = Z.clip(min=0)  # pipe outlet matrix
    Z_pipe_in = Z.clip(max=0)  # pipe inlet matrix

    M_sub = np.zeros((Z.shape[0], Z.shape[0]))  # (nxn) substation flow rate matrix
    np.fill_diagonal(M_sub, mass_flow_substation_df)

    M_d = np.zeros((Z.shape[1], Z.shape[1]))  # (exe) pipe mass flow rate matrix
    np.fill_diagonal(M_d, mass_flow_df)

    # matrices to store results
    T_e_out = Z_pipe_out.copy()
    T_e_in = Z_pipe_in.copy().dot(-1)
    T_node = np.zeros(Z.shape[0])
    Z_note = Z.copy()  # matrix to store information of solved nodes

    # calculate the return pipe node temperature of substations locating at the end of the branch
    for i in range(Z.shape[0]):
        # choose the consumer nodes locating at the end of the branches
        if np.count_nonzero(Z[i] == 1) == 0 and np.count_nonzero(Z[i] == 0) != Z.shape[1]:
            T_node[i] = t_return.values[0, i]
            # T_node[i] = map(list, t_return.values)[0][i]
            for edge in range(Z_note.shape[1]):
                if T_e_in[i, edge] != 0:
                    T_e_in[i, edge] = map(list, t_return.values)[0][i]
                    # calculate pipe outlet
                    calc_t_out(i, edge, K, M_d, Z, T_e_in, T_e_out, T_ground, Z_note, gv)

    while Z_note.max() >= 1:
        for j in range(Z.shape[0]):
            if (np.count_nonzero(Z_note[j] == 1) == 0 and np.count_nonzero(Z_note[j] == 0) != Z.shape[1]):
                # calculate node temperature with merging flows from pipes
                T_node[j] = calc_return_node_temperature(j, M_d, T_e_out, t_return, Z_pipe_out, M_sub)
                for edge in range(Z_note.shape[1]):
                    if T_e_in[j, edge] != 0:
                        T_e_in[j, edge] = T_node[j]
                        # calculate pipe outlet
                        calc_t_out(j, edge, K, M_d, Z, T_e_in, T_e_out, T_ground, Z_note, gv)
            if np.argwhere(Z_note[j] == 0).size == Z.shape[1] and T_node[j] == 0:
                T_node[j] = calc_return_node_temperature(j, M_d, T_e_out, t_return, Z_pipe_out, M_sub)

    # calculate temperature with merging flows from pipes at the plant node
    if len(np.where(T_node == 0)[0]) != 0:
        node_index = np.where(T_node == 0)[0][0]
        M_sub[node_index] = 0
        T_node[node_index] = calc_return_node_temperature(node_index, M_d, T_e_out, t_return, Z_pipe_out, M_sub)

    return T_node


def calc_return_node_temperature(index, M_d, T_e_out, t_return, Z_pipe_out, M_sub):
    """
    The function calculates the node temperature with merging flows from pipes in the return line.

    :param index: node index
    :param M_d: pipe mass flow matrix (exe)
    :param T_e_out: pipe outlet temperatures in edge node matrix (nxe)
    :param t_return: list of substation return temperatures
    :param Z_pipe_out: pipe outlet matrix (nxe)
    :param M_sub: DataFrame substation flow rate

    :type index: floatT_return_all_2
    :type M_d: DataFrame
    :type T_e_out: DataFrame
    :type t_return: list
    :type Z_pipe_out: DataFrame
    :type M_sub: DataFrame

    :returns T_node: node temperature with merging flows in the return line
    :rtype T_node: float

    """
    total_mass_flow_to_node = np.dot(M_d, Z_pipe_out[index]).sum() + M_sub[index].max()
    if total_mass_flow_to_node == 0:
        # set node temperature to nan if no flow to node
        T_node = np.nan
    else:
        total_mcp_from_edges = np.dot(M_d, np.nan_to_num(T_e_out[index])).sum()
        total_mcp_from_substations = 0 if M_sub[index].max() == 0 else np.dot(M_sub[index].max(), t_return.values[0,
                                                                                                                  index])
        T_node = (total_mcp_from_edges + total_mcp_from_substations) / total_mass_flow_to_node
    return T_node


def calc_t_out(node, edge, K, M_d, Z, T_e_in, T_e_out, T_ground, Z_note, gv):
    """
    Given the pipe inlet temperature, this function calculate the outlet temperature of the pipe.
    Following the reference of [Wang et al., 2016]_.

    :param node: node index
    :param edge: edge indices
    :param K: DataFrame of aggregated heat conduction coefficient for each pipe (exe)
    :param M_d: DataFrame of pipe flow rate (exe)
    :param Z: DataFrame of  edge_node_matrix (nxe)
    :param T_e_in: DataFrame of pipe inlet temperatures [K] in edge_node_matrix (nxe)
    :param T_e_out: DataFrame of  pipe outlet temperatures [K] in edge_node_matrix (nxe)
    :param T_ground: vector with ground temperatures in [K]
    :param Z_note: DataFrame of the matrix to store information of solved nodes
    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)

    :type node: float
    :type edge: np array
    :type K: DataFrame
    :type M_d: DataFrame
    :type Z: DataFrame
    :type T_e_in: DataFrame
    :type T_e_out: DataFrame
    :type T_ground: list
    :type Z_note: DataFrame
    :type gv: GlobalVariables

    :returns The calculated pipe outlet temperatures are directly written to T_e_out

    ..[Wang et al, 2016] Wang J., Zhou, Z., Zhao, J. (2016). A method for the steady-state thermal simulation of
    district heating systems and model parameters calibration. Eenergy Conversion and Management, 120, 294-305.
    """
    # calculate pipe outlet temperature
    if isinstance(edge, np.ndarray) == False:
        edge = np.array([edge])

    for i in range(edge.size):
        e = edge[i]
        k = K[e, e]
        m = M_d[e, e]
        out_node_index = np.where(Z[:, e] == 1)[0].max()
        if abs(m) == 0 and Z[node, e] == -1:
            # set outlet temperature to nan if no flow is going out from node to connected edges
            T_e_out[out_node_index, e] = np.nan
            Z_note[:, e] = 0

        elif Z[node, e] == -1:
            # calculate outlet temperature if flow goes from node to out_node through edge
            T_e_out[out_node_index, e] = (T_e_in[node, e] * (k / 2 - m * gv.Cpw) - k * T_ground) / (
                -m * gv.Cpw - k / 2)  # [K]
            dT = T_e_in[node, e] - T_e_out[out_node_index, e]
            if abs(dT) > 30:
                print('High temperature loss on edge', e, '. Loss:', abs(dT))
                if (k / 2 - m * gv.Cpw) > 0:
                    print(
                        'Exit temperature decreasing at entry temperature increase. Possible at low massflows. Massflow:',
                        m, ' on edge: ', e)
                    T_e_out[out_node_index, e] = T_e_in[node, e] - 30  # assumes maximum 30 K temperature loss
                    # Induces some error but necessary to avoid spiraling to negative temperatures
                    # Todo: find better method which allows loss calculation at low massflows
            Z_note[:, e] = 0


def calc_aggregated_heat_conduction_coefficient(mass_flow, locator, gv, edge_df, pipe_properties_df, temperature_K,
                                                network_type):
    """
    This function calculates the aggregated heat conduction coefficients of all the pipes.
    Following the reference from [Wang et al., 2016].
    The pipe material properties are referenced from _[A. Kecabas et al., 2011], and the pipe catalogs are referenced
    from _[J.A. Fonseca et al., 2016] and _[isoplus].

    :param mass_flow: Vector with mass flows of each edge                           (e x 1)
    :param locator: an InputLocator instance set to the scenario to work on
    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)
    :param pipe_properties_df: DataFrame containing the pipe properties for each edge in the network
    :param temperature_K: matrix containing the temperature of the water in each edge e at time t             (t x e)
    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling ('DC')
                         network
    :param edge_df: list of edges and their corresponding lengths and start and end nodes

    :type temperature_K: list
    :type gv: GlobalVariables
    :type network_type: str
    :type mass_flow: DataFrame
    :type locator: InputLocator
    :type gv: GlobalVariables
    :type pipe_properties_df: DataFrame
    :type edge_df: DataFrame

    :return K_all: DataFrame of aggregated heat conduction coefficients (1 x e) for all edges

    ..[Wang et al, 2016] Wang J., Zhou, Z., Zhao, J. (2016). A method for the steady-state thermal simulation of
    district heating systems and model parameters calibration. Eenergy Conversion and Management, 120, 294-305.

    ..[A. Kecebas et al., 2011] A. Kecebas et al. Thermo-economic analysis of pipe insulation for district heating
    piping systems. Applied Thermal Engineering, 2011.

    ..[J.A. Fonseca et al., 2016] J.A. Fonseca et al. City Energy Analyst (CEA): Integrated framework for analysis and
    optimization of building energy systems in neighborhoods and city districts. Energy and Buildings. 2016

    ..[isoplus] isoplus piping systems. http://en.isoplus.dk/download-centre

    	.. Incropera, F. P., DeWitt, D. P., Bergman, T. L., & Lavine, A. S. (2007). Fundamentals of Heat and Mass
    	Transfer. Fundamentals of Heat and Mass Transfer. https://doi.org/10.1016/j.applthermaleng.2011.03.022
    """

    L_pipe = edge_df['pipe length']
    material_properties = pd.read_excel(locator.get_thermal_networks(), sheetname=['MATERIAL PROPERTIES'])[
        'MATERIAL PROPERTIES']
    material_properties = material_properties.set_index(material_properties['material'].values)
    conductivity_pipe = material_properties.ix['Steel', 'lamda_WmK']  # _[A. Kecebas et al., 2011]
    conductivity_insulation = material_properties.ix['PUR', 'lamda_WmK']  # _[A. Kecebas et al., 2011]
    conductivity_ground = material_properties.ix['Soil', 'lamda_WmK']  # _[A. Kecebas et al., 2011]
    network_depth = gv.NetworkDepth  # [m]
    extra_heat_transfer_coef = 0.2  # _[Wang et al, 2016] to represent heat losses from valves and other attachments

    # calculate nusselt number
    nusselt = calc_nusselt(mass_flow, gv, temperature_K, pipe_properties_df[:]['D_int_m':'D_int_m'].values[0],
                           network_type)
    # calculate thermal conductivity of water
    thermal_conductivity = calc_thermal_conductivity(temperature_K)
    # evaluate thermal heat transfer coefficient
    alpha_th = thermal_conductivity * nusselt / pipe_properties_df[:]['D_int_m':'D_int_m'].values[0]  # W/(m^2 * K)

    K_all = []
    for pipe_number, pipe in enumerate(L_pipe.index):
        # calculate heat resistances, equation (3) in Wang et al., 2016
        R_pipe = np.log(pipe_properties_df.loc['D_ext_m', pipe] / pipe_properties_df.loc['D_int_m', pipe]) / (
            2 * math.pi * conductivity_pipe)  # [m*K/W]
        R_insulation = np.log((pipe_properties_df.loc['D_ins_m', pipe]) / pipe_properties_df.loc['D_ext_m', pipe]) / (
            2 * math.pi * conductivity_insulation)  # [m*K/W]
        a = 2 * network_depth / (pipe_properties_df.loc['D_ins_m', pipe])
        R_ground = np.log(a + (a ** 2 - 1) ** 0.5) / (2 * math.pi * conductivity_ground)  # [m*K/W]
        # calculate convection heat transfer resistance
        if alpha_th[pipe_number] == 0:
            R_conv = 0.2  # case with no massflow, avoids divide by 0 error
        else:
            R_conv = 1 / (
            alpha_th[pipe_number] * math.pi * pipe_properties_df[:]['D_int_m':'D_int_m'].values[0][pipe_number])
        # calculate the aggregated heat conduction coefficient, equation (4) in Wang et al., 2016
        k = L_pipe[pipe] * (1 + extra_heat_transfer_coef) / (R_pipe + R_insulation + R_ground + R_conv) / 1000  # [kW/K]
        K_all.append(k)
    K_all = np.diag(K_all)
    return K_all


def calc_nusselt(mass_flow_rate_kgs, gv, temperature_K, pipe_diameter_m, network_type):
    """
    Calculates the nusselt number of the internal flow inside the pipes.

    :param pipe_diameter_m: vector containing the pipe diameter in m for each edge e in the network           (e x 1)
    :param mass_flow_rate_kgs: matrix containing the mass flow rate in each edge e at time t                    (t x e)
    :param temperature_K: matrix containing the temperature of the water in each edge e at time t             (t x e)
    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling ('DC')
                         network
    :type pipe_diameter_m: ndarray
    :type mass_flow_rate_kgs: ndarray
    :type temperature_K: list
    :type gv: GlobalVariables
    :type network_type: str

    :return nusselt: calculated nusselt number for flow in each edge		(ex1)
    :rtype nusselt: ndarray

	.. Incropera, F. P., DeWitt, D. P., Bergman, T. L., & Lavine, A. S. (2007). Fundamentals of Heat and Mass Transfer. Fundamentals of Heat and Mass Transfer. https://doi.org/10.1016/j.applthermaleng.2011.03.022
    """
    # calculate variable values necessary for nusselt number evaluation
    reynolds = calc_reynolds(mass_flow_rate_kgs, gv, temperature_K, pipe_diameter_m)
    prandtl = calc_prandtl(gv, temperature_K)
    darcy = calc_darcy(pipe_diameter_m, reynolds, gv.roughness)

    nusselt = np.zeros(reynolds.size)
    for rey in range(reynolds.size):
        if reynolds[rey] <= 1:
            # calculate nusselt number only if mass is flowing
            nusselt[rey] = 0
        elif reynolds[rey] <= 2300:
            # calculate the Nusselt number for laminar flow
            nusselt[rey] = 3.66
        elif reynolds[rey] <= 10000:
            # calculate the Nusselt for transient flow
            nusselt[rey] = darcy[rey] / 8 * (reynolds[rey] - 1000) * prandtl[rey] / (
            1 + 12.7 * (darcy[rey] / 8) ** 0.5 * (prandtl[rey] ** 0.67 - 1))
        else:
            # calculate the Nusselt number for turbulent flow
            # identify if heating or cooling case
            if network_type == 'DH':  # warm fluid, so ground is cooling fluid in pipe, cooling case from view of thermodynamic flow
                nusselt[rey] = 0.023 * reynolds[rey] ** 0.8 * prandtl[rey] ** 0.3
            else:
                # cold fluid, so ground is heating fluid in pipe, heating case from view of thermodynamic flow
                nusselt[rey] = 0.023 * reynolds[rey] ** 0.8 * prandtl[rey] ** 0.4

    return nusselt


# ============================
# Other functions
# ============================


def get_thermal_network_from_csv(locator, network_type, network_name):
    """
    This function reads the existing node and pipe network from csv files (as provided for the Zug reference case) and
    produces an edge-node incidence matrix (as defined by Oppelt et al., 2016) as well as the length of each edge.

    :param locator: an InputLocator instance set to the scenario to work on
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling ('DC')
                         network
    :type locator: InputLocator
    :type network_type: str

    :return edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges) and
                        indicating direction of flow of each edge e at node n: if e points to n, value is 1; if
                        e leaves node n, -1; else, 0.                                                           (n x e)
    :return all_nodes_df: DataFrame that contains all nodes, whether a node is a consumer, plant, or neither,
                        and, if it is a consumer or plant, the name of the corresponding building               (2 x n)
    :return pipe_data_df['LENGTH']: vector containing the length of each edge in the network                    (1 x e)
    :rtype edge_node_df: DataFrame
    :rtype all_nodes_df: DataFrame
    :rtype pipe_data_df['LENGTH']: array

    The following files are created by this script:
        - DH_EdgeNode: csv file containing edge_node_df stored in locator.get_optimization_network_layout_folder()
        - DH_AllNodes: csv file containing all_nodes_df stored in locator.get_optimization_network_layout_folder()

    ..[Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
    Applied Thermal Engineering, 2016.

    """

    t0 = time.clock()

    # get node and pipe data
    node_df = pd.read_csv(locator.get_network_layout_nodes_csv_file(network_type)).set_index('DC_ID')
    edge_df = pd.read_csv(locator.get_network_layout_pipes_csv_file(network_type)).set_index('DC_ID')
    edge_df.rename(columns={'LENGTH': 'pipe length'},
                   inplace=True)  # todo: could be removed when the input format of .csv is fixed

    # sort dataframe with node/edge numbers
    node_sorted_index = node_df.index.to_series().str.split('J', expand=True)[1].apply(int).sort_values(
        ascending=True)
    node_df = node_df.reindex(index=node_sorted_index.index)
    edge_sorted_index = edge_df.index.to_series().str.split('PIPE', expand=True)[1].apply(int).sort_values(
        ascending=True)
    edge_df = edge_df.reindex(index=edge_sorted_index.index)

    # create consumer and plant node vectors from node data
    for column in ['Plant', 'Sink']:
        if type(node_df[column][0]) != int:
            node_df[column] = node_df[column].astype(int)
    node_names = node_df.index.values
    consumer_nodes = np.vstack((node_names, (node_df['Sink'] * node_df['Name']).values))
    plant_nodes = np.vstack((node_names, (node_df['Plant'] * node_df['Name']).values))

    # create edge-node matrix from pipe data
    list_edges = edge_df.index.values
    list_nodes = node_df.index.values
    edge_node_matrix = np.zeros((len(list_nodes), len(list_edges)))
    for j in range(len(list_edges)):
        for i in range(len(list_nodes)):
            if edge_df['NODE2'][j] == list_nodes[i]:
                edge_node_matrix[i][j] = 1
            elif edge_df['NODE1'][j] == list_nodes[i]:
                edge_node_matrix[i][j] = -1
    edge_node_df = pd.DataFrame(data=edge_node_matrix, index=list_nodes, columns=list_edges)
    edge_node_df.to_csv(locator.get_optimization_network_edge_node_matrix_file(network_type, network_name))

    all_nodes_df = pd.DataFrame(index=list_nodes, columns=['Building', 'Type'])
    for i in range(len(list_nodes)):
        if consumer_nodes[1][i] != '':
            all_nodes_df.loc[list_nodes[i], 'Building'] = consumer_nodes[1][i]
            all_nodes_df.loc[list_nodes[i], 'Type'] = 'CONSUMER'
        elif plant_nodes[1][i] != '':
            all_nodes_df.loc[list_nodes[i], 'Building'] = plant_nodes[1][i]
            all_nodes_df.loc[list_nodes[i], 'Type'] = 'PLANT'
        else:
            all_nodes_df.loc[list_nodes[i], 'Building'] = 'NONE'
            all_nodes_df.loc[list_nodes[i], 'Type'] = 'NONE'
    all_nodes_df.to_csv(locator.get_optimization_network_node_list_file(network_type, network_name))

    print(time.clock() - t0, "seconds process time for Network Summary\n")

    return edge_node_df, all_nodes_df, edge_df


def get_thermal_network_from_shapefile(locator, network_type, network_name):
    """
    This function reads the existing node and pipe network from a shapefile and produces an edge-node incidence matrix
    (as defined by Oppelt et al., 2016) as well as the edge properties (length, start node, and end node) and node
    coordinates.

    :param locator: an InputLocator instance set to the scenario to work on
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling ('DC')
                         network
    :type locator: InputLocator
    :type network_type: str

    :return edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges) and
                        indicating direction of flow of each edge e at node n: if e points to n, value is 1; if
                        e leaves node n, -1; else, 0.                                                           (n x e)
    :return all_nodes_df: DataFrame that contains all nodes, whether a node is a consumer, plant, or neither,
                        and, if it is a consumer or plant, the name of the corresponding building               (2 x n)
    :return edge_df['pipe length']: vector containing the length of each edge in the network                    (1 x e)
    :rtype edge_node_df: DataFrame
    :rtype all_nodes_df: DataFrame
    :rtype edge_df['pipe length']: array

    The following files are created by this script:
        - DH_EdgeNode: csv file containing edge_node_df stored in locator.get_optimization_network_layout_folder()
        - DH_Node_DF: csv file containing all_nodes_df stored in locator.get_optimization_network_layout_folder()
        - DH_Pipe_DF: csv file containing edge_df stored in locator.get_optimization_network_layout_folder()

    ..[Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
    Applied Thermal Engineering, 2016.

    """

    t0 = time.clock()

    # import shapefiles containing the network's edges and nodes
    network_edges_df = gpd.read_file(locator.get_network_layout_edges_shapefile(network_type, network_name))
    network_nodes_df = gpd.read_file(locator.get_network_layout_nodes_shapefile(network_type, network_name))

    # check duplicated NODE/PIPE IDs
    duplicated_nodes = network_nodes_df[network_nodes_df.Name.duplicated(keep=False)]
    duplicated_edges = network_edges_df[network_edges_df.Name.duplicated(keep=False)]
    if duplicated_nodes.size > 0:
        raise ValueError('There are duplicated NODE IDs:', duplicated_nodes)
    if duplicated_edges.size > 0:
        raise ValueError('There are duplicated PIPE IDs:', duplicated_nodes)

    # get node and pipe information
    node_df, edge_df = extract_network_from_shapefile(network_edges_df, network_nodes_df)

    # create node catalogue indicating which nodes are plants and which consumers
    all_nodes_df = node_df[['Type', 'Building']]
    all_nodes_df.to_csv(locator.get_optimization_network_node_list_file(network_type, network_name))
    # extract the list of buildings in the current network
    building_names = all_nodes_df.Building[all_nodes_df.Type == 'CONSUMER'].reset_index(drop=True)

    # create first edge-node matrix
    list_pipes = edge_df.index.values
    list_nodes = node_df.index.values
    edge_node_matrix = np.zeros((len(list_nodes), len(list_pipes)))
    for j in range(len(list_pipes)):  # TODO: find ways to accelerate
        for i in range(len(list_nodes)):
            if edge_df['end node'][j] == list_nodes[i]:
                edge_node_matrix[i][j] = 1
            elif edge_df['start node'][j] == list_nodes[i]:
                edge_node_matrix[i][j] = -1
    edge_node_df = pd.DataFrame(data=edge_node_matrix, index=list_nodes, columns=list_pipes)  # first edge-node matrix

    ## An edge node matrix is generated as a first guess and then virtual substation mass flows are imposed to
    ## calculate mass flows in each edge (mass_flow_guess).
    node_mass_flows_df = pd.DataFrame(data=np.zeros([1, len(edge_node_df.index)]), columns=edge_node_df.index)
    total_flow = 0
    number_of_plants = sum(all_nodes_df['Type'] == 'PLANT')

    for node, row in all_nodes_df.iterrows():
        if row['Type'] == 'CONSUMER':
            node_mass_flows_df[node] = 1  # virtual consumer mass flow requirement
            total_flow += 1
    for node, row in all_nodes_df.iterrows():
        if row['Type'] == 'PLANT':
            node_mass_flows_df[node] = - total_flow / number_of_plants  # virtual plant supply mass flow
    mass_flow_guess = calc_mass_flow_edges(edge_node_df, node_mass_flows_df, all_nodes_df)[0]

    # The direction of flow is then corrected by inverting negative flows in mass_flow_guess.
    counter = 0
    while mass_flow_guess.min() < 0:
        for i in range(len(mass_flow_guess)):
            if mass_flow_guess[i] < 0:
                mass_flow_guess[i] = abs(mass_flow_guess[i])
                edge_node_df[edge_node_df.columns[i]] = -edge_node_df[edge_node_df.columns[i]]
                new_nodes = [edge_df['end node'][i], edge_df['start node'][i]]
                edge_df['start node'][i] = new_nodes[0]
                edge_df['end node'][i] = new_nodes[1]
        mass_flow_guess = calc_mass_flow_edges(edge_node_df, node_mass_flows_df, all_nodes_df)[0]
        counter += 1

    # make sure there are no NONE-node at dead ends before proceeding
    plant_counter = 0
    for i in range(edge_node_df.shape[0]):
        if np.count_nonzero(edge_node_df.iloc[i] == 1) == 0:
            plant_counter += 1
    if number_of_plants != plant_counter:
        raise ValueError('Please erase ', (plant_counter - number_of_plants),
                         ' end node(s) that are neither buildings nor plants.')

    edge_node_df.to_csv(locator.get_optimization_network_edge_node_matrix_file(network_type, network_name))
    print(time.clock() - t0, "seconds process time for Network Summary\n")

    return edge_node_df, all_nodes_df, edge_df, building_names


def extract_network_from_shapefile(edge_shapefile_df, node_shapefile_df):
    """
    Extracts network data into DataFrames for pipes and nodes in the network

    :param edge_shapefile_df: DataFrame containing all data imported from the edge shapefile
    :param node_shapefile_df: DataFrame containing all data imported from the node shapefile
    :type edge_shapefile_df: DataFrame
    :type node_shapefile_df: DataFrame
    :return node_df: DataFrame containing all nodes and their corresponding coordinates
    :return edge_df: list of edges and their corresponding lengths and start and end nodes
    :rtype node_df: DataFrame
    :rtype edge_df: DataFrame

    """
    # set precision of coordinates
    decimals = 6
    # create node dictionary with plant and consumer nodes
    node_dict = {}
    node_shapefile_df.set_index("Name", inplace=True)
    node_shapefile_df = node_shapefile_df.astype('object')
    node_shapefile_df['coordinates'] = node_shapefile_df['geometry'].apply(lambda x: x.coords[0])
    # sort node_df by index number
    node_sorted_index = node_shapefile_df.index.to_series().str.split('NODE', expand=True)[1].apply(int).sort_values(
        ascending=True)
    node_shapefile_df = node_shapefile_df.reindex(index=node_sorted_index.index)
    # assign node properties (plant/consumer/none)
    node_shapefile_df['plant'] = ''
    node_shapefile_df['consumer'] = ''
    node_shapefile_df['none'] = ''

    for node, row in node_shapefile_df.iterrows():
        coord_node = row['geometry'].coords[0]
        if row['Type'] == "PLANT":
            node_shapefile_df.loc[node, 'plant'] = node
        elif row['Type'] == "CONSUMER":  # TODO: add 'PROSUMER' by splitting nodes
            node_shapefile_df.loc[node, 'consumer'] = node
        else:
            node_shapefile_df.loc[node, 'none'] = node
        coord_node_round = (round(coord_node[0], decimals), round(coord_node[1], decimals))
        node_dict[coord_node_round] = node

    # create edge dictionary with pipe lengths and start and end nodes
    # complete node dictionary with missing nodes (i.e., joints)
    edge_shapefile_df.set_index("Name", inplace=True)
    edge_shapefile_df = edge_shapefile_df.astype('object')
    edge_shapefile_df['coordinates'] = edge_shapefile_df['geometry'].apply(lambda x: x.coords[0])
    # sort edge_df by index number
    edge_sorted_index = edge_shapefile_df.index.to_series().str.split('PIPE', expand=True)[1].apply(int).sort_values(
        ascending=True)
    edge_shapefile_df = edge_shapefile_df.reindex(index=edge_sorted_index.index)
    # assign edge properties
    edge_shapefile_df['pipe length'] = 0
    edge_shapefile_df['start node'] = ''
    edge_shapefile_df['end node'] = ''

    for pipe, row in edge_shapefile_df.iterrows():
        # get the length of the pipe and add to dataframe
        edge_shapefile_df.loc[pipe, 'pipe length'] = row['geometry'].length
        # get the start and end notes and add to dataframe
        edge_coords = row['geometry'].coords
        start_node = (round(edge_coords[0][0], decimals), round(edge_coords[0][1], decimals))
        end_node = (round(edge_coords[1][0], decimals), round(edge_coords[1][1], decimals))
        if start_node in node_dict.keys():
            edge_shapefile_df.loc[pipe, 'start node'] = node_dict[start_node]
        else:
            print('The start node of ', pipe, 'has no match in node_dict, check precision of the coordinates.')
        if end_node in node_dict.keys():
            edge_shapefile_df.loc[pipe, 'end node'] = node_dict[end_node]
        else:
            print('The end node of ', pipe, 'has no match in node_dict, check precision of the coordinates.')

    # # If a consumer node is not connected to the network, find the closest node and connect them with a new edge
    # # this part of the code was developed for a case in which the node and edge shapefiles were not defined
    # # consistently. This has not been a problem after all, but it could eventually be a useful feature.
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

    return node_shapefile_df, edge_shapefile_df


def write_substation_values_to_nodes_df(all_nodes_df, df_value):
    """
    The function writes values (temperatures or mass flows) from each substations to the corresponding nodes in the
    edge node matrix.

    :param all_nodes_df: DataFrame containing all nodes and whether a node n is a consumer or plant node
                        (and if so, which building that node corresponds to), or neither.                   (2 x n)
    :param df_value: DataFrame of value of each substation
    :param flag: flag == True if the values are temperatures ; flag == False if the value is mass flow

    :return nodes_df: DataFrame with values at each node (1xn)
    :rtype nodes_df: DataFrame

    """

    nodes_df = pd.DataFrame(index=[0], columns=all_nodes_df.index)
    # it is assumed that if there is more than one plant, they all supply the same amount of heat at each time step
    # (i.e., the amount supplied by each plant is not optimized)
    number_of_plants = sum(all_nodes_df['Type'] == 'PLANT')
    consumer_list = all_nodes_df.loc[all_nodes_df['Type'] == 'CONSUMER', 'Building'].values
    plant_mass_flow = df_value[consumer_list].loc[0].sum() / number_of_plants

    # write all flow rates into nodes DataFrame
    ''' NOTE:
            for each node, (mass incoming edges) + (mass supplied) = (mass outgoing edges) + (mass demand)
                           (mass incoming edges) - (mass outgoing edges) = (mass demand) - (mass supplied)
            which equals   (edge node matrix) * (mass flow edge) = (mass demand) - (mass supplied)
                           (edge node matrix) * (mass flow edge) = (mass flow node)

            so mass_flow_node[node] = mass_flow_demand[node] for consumer nodes and
               mass_flow_node[node] = - mass_flow_supply[node] for plant nodes
            (i.e., mass flow is positive if it's a consumer node, negative if it's a supply node)

            assuming only one plant node, the mass flow on the supply side needs to equal the mass flow from consumers
            so mass_flow_supply = - sum(mass_flow_demand[node]) for all nodes

            for the case where there is more than one supply plant, it is assumed for now that all plants supply the
            same share of the total demand of the network
            so mass_flow_supply = - sum(mass_flow_demand)/(number of plants)
        '''

    # assure only mass flow at network consumer substations are counted
    for node, row in all_nodes_df.iterrows():
        if row['Type'] == 'CONSUMER':
            nodes_df[node] = df_value[row['Building']]
        elif row['Type'] == 'PLANT':
            nodes_df[node] = - plant_mass_flow
        else:
            nodes_df[node] = 0
    return nodes_df


def write_substation_temperatures_to_nodes_df(all_nodes_df, df_value):
    """
    The function writes values (temperatures or mass flows) from each substations to the corresponding nodes in the
    edge node matrix.

    :param all_nodes_df: DataFrame containing all nodes and whether a node n is a consumer or plant node
                        (and if so, which building that node corresponds to), or neither.                   (2 x n)
    :param df_value: DataFrame of value of each substation
    :param flag: flag == True if the values are temperatures ; flag == False if the value is mass flow

    :return nodes_df: DataFrame with values at each node (1xn)
    :rtype nodes_df: DataFrame

    """

    nodes_df = pd.DataFrame()
    # write temperature into nodes DataFrame
    for node, row in all_nodes_df.iterrows():
        if row['Type'] == 'CONSUMER':
            nodes_df[node] = df_value[row['Building']]
        else:
            nodes_df[node] = np.nan  # set temperature value to nan for non-substation nodes

    return nodes_df


def read_properties_from_buildings(building_names, buildings_demands, property):
    """
    The function reads certain property from each building and output as a DataFrame.

    :param building_names: list of building names in the scenario
    :param buildings_demands: demand of each building in the scenario
    :param property: certain property from the building demand file. e.g. T_supply_target

    :return property_df: DataFrame of the particular property at each building.
    :rtype property_df: DataFrame

    """

    property_df = pd.DataFrame(index=range(8760), columns=building_names)
    for name in building_names:
        property_per_building = buildings_demands[(building_names == name).argmax()][property]
        property_df[name] = property_per_building
    return property_df


# ============================
# test
# ============================


def main(config):
    """
    run the whole network summary routine
    """
    gv = cea.globalvar.GlobalVariables()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    # add options for data sources: heating or cooling network, csv or shapefile
    network_type = config.thermal_network.network_type  # set to either 'DH' or 'DC'
    file_type = config.thermal_network.file_type  # set to csv or shapefile
    set_diameter = config.thermal_network.set_diameter  # this does a rule of max and min flow to set a diameter. if false it takes the input diameters
    list_network_name = config.thermal_network.network_name

    print('Running thermal_network for scenario %s' % config.scenario)
    print('Running thermal_network for network type %s' % network_type)
    print('Running thermal_network for file type %s' % file_type)
    print('Running thermal_network for network %s' % list_network_name)

    if len(list_network_name) == 0:
        network_name = ''
        thermal_network_main(locator, gv, network_type, network_name, file_type, set_diameter)
    else:
        for network_name in list_network_name:
            thermal_network_main(locator, gv, network_type, network_name, file_type, set_diameter)
    print('test thermal_network_main() succeeded')


if __name__ == '__main__':
    main(cea.config.Configuration())

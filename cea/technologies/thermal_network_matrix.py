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


__author__ = "Martin Mosteiro Romero, Shanshan Hsieh"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Martin Mosteiro Romero", "Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def thermal_network_main(locator, gv, network_type, source):
    """
    This function performs thermal and hydraulic calculation of a "well-defined" network, namely, the plant/consumer
    substations, piping routes and the pipe properties (length/diameter/heat transfer coefficient) are already 
    specified.

    Firstly, the consumer substation heat exchanger designs are calculated according to the consumer demands at each
    substation.

    Secondly, the piping network is imported as a node-edge matrix (NxE), which indicates the connections
    of all nodes and edges and the direction of flow between them following graph theory [Ikonen, E., et al, 2016]_ .
    Nodes represent points in the network, which could be the consumers, plants or joint points. Edges represent the
    pipes in the network. For example, (n1,e1) = 1 denotes the flow enters edge "e1" at node "n1", while when
    (n2,e2) = -1 denotes the flow leave edge "e2" at node "n2". Following, a steady-state hydraulic calculation is
    carried out at each time-step to solve for the edge mass flow rates according to mass conservation equations.

    Thirdly, with the maximum mass flow calculated from each edge, the property of each pipe is assigned.

    Finally, we enter the hydraulic thermal calculation routine for each time-steps over a year.
    The network temperature on the supply and return temperatures accounting for temperature loss.
    The hydraulic calculation is based on Oppelt, T., et al., 2016 for the case with no loops. Firstly, the consumer
    substation heat exchanger designs are calculated according to the consumer demands at each substation. Secondly,
    the piping network is imported as a node-edge matrix (NxE), which indicates the connections of all nodes and edges
    and the direction of flow between them following graph theory. Nodes represent points in the network, which could
    be the consumers, plants or joint points. Edges represent the pipes in the network. For example, (n1,e1) = 1 denotes
    the flow enters edge "e1" at node "n1", while when (n2,e2) = -1 denotes the flow leave edge "e2" at node "n2".
    Following, a steady-state hydraulic calculation is carried out at each time-step to solve for the edge mass flow
    rates according to mass conservation equations.

    The hydraulic thermal calculation is based on a heat balance for each edge (heat at the pipe inlet equals heat at
    the outlet minus heat losses through the pipe). Finally, the pressure loss calculation is carried out based on
    Todini et al. (1987)

    :param locator: an InputLocator instance set to the scenario to work on
    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling ('DC')
                         network
    :param source: string that defines the type of source file for the network to be imported ('csv' or 'shapefile')

    :type locator: InputLocator
    :type gv: GlobalVariables
    :type network_type: str
    :type source: str

    The following files are created by this script, depending on the network type defined in the inputs:
    - DH_EdgeNode or DC_EdgeNode: .csv
        edge-node matrix for the defined network
    - DH_AllNodes or DC_AllNodes: .csv
        list of plant nodes and consumer nodes and their corresponding building names
    - DH_MassFlow or DC_MassFlow: .csv
        mass flow rates at each edge for each time step
    - DH_T_Supply or DC_T_Supply: .csv
        describes the supply temperatures at each node at each type step
    - DH_T_Return or DC_T_Return: .csv
        describes the return temperatures at each node at each type step
    - DH_Plant_heat_requirement or DC_Plant_heat_requirement: .csv
        heat requirement at from the plants in a district heating or cooling network
    - DH_P_Supply or DC_P_Supply: .csv
        supply side pressure for each node in a district heating or cooling network at each time step
    - DH_P_Return or DC_P_Return: .csv
        supply side pressure for each node in a district heating or cooling network at each time step
    - DH_P_DeltaP or DC_P_DeltaP.csv
        pressure drop over an entire district heating or cooling network at each time step

    ..[Todini & Pilati, 1987] Todini & Pilati. "A gradient method for the analysis of pipe networks," in Computer
    Applications in Water Supply Volume 1 - Systems Analysis and Simulation, 1987.
    ..[Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
    Applied Thermal Engineering, 2016.
    ..[Ikonen, E., et al, 2016] Ikonen, E., et al. Examination of Operational Optimization at Kemi District Heating 
    Network. Thermal Science. 2016, Vol. 20, No.2, pp.667-678.

    """

    # # prepare data for calculation

    # read building names
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand['Name']

    # calculate ground temperature
    weather_file = locator.get_default_weather()
    T_ambient = epwreader.epw_reader(weather_file)['drybulb_C']
    T_ground = geothermal.calc_ground_temperature(T_ambient.values, gv)

    # substation HEX design
    substations_HEX_specs, buildings_demands = substation.substation_HEX_design_main(locator, building_names, gv)

    # get edge-node matrix from defined network
    if source == 'csv':
        edge_node_df, all_nodes_df, pipe_length_df = get_thermal_network_from_csv(locator, network_type)
    else:
        edge_node_df, all_nodes_df, pipe_length_df = get_thermal_network_from_shapefile(locator, network_type)

    # get hourly heat requirement and target supply temperature from each substation
    t_target_supply = read_properties_from_buildings(building_names, buildings_demands, 'T_sup_target_' + network_type)
    t_target_supply_df = write_substation_temperatures_to_nodes_df(all_nodes_df, t_target_supply)  # (1 x n)

    ## assign pipe properties
    # calculate maximum edge mass flow
    edge_mass_flow_df, max_edge_mass_flow_df = calc_max_edge_flowrate(all_nodes_df, building_names, buildings_demands,
                                                                      edge_node_df, gv, locator, substations_HEX_specs,
                                                                      t_target_supply, network_type)


    # assign pipe id/od according to maximum edge mass flow
    pipe_properties_df = assign_pipes_to_edges(max_edge_mass_flow_df, locator, gv)

    # calculate pipe aggregated heat conduction coefficient
    K_pipe = calc_aggregated_heat_conduction_coefficient(locator, gv, pipe_length_df, pipe_properties_df)  # (exe)[kW/K]

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

        print('calculating network thermal hydraulic properties... time step', t)
        timer = time.clock()

        ## solve network temperatures
        T_supply_nodes, \
        T_return_nodes, \
        plant_heat_requirement, \
        edge_mass_flow_df.ix[t],\
        q_loss_supply_edges = solve_network_temperatures(locator, gv, T_ground, edge_node_df, all_nodes_df,
                                                                 edge_mass_flow_df.ix[t], K_pipe, t_target_supply_df,
                                                                 building_names, buildings_demands,
                                                                 substations_HEX_specs, t, network_type)

        # calculate pressure at each node and pressure drop throughout the entire network
        P_supply_nodes, P_return_nodes, delta_P_network = calc_pressure_nodes(edge_node_df,
                                                                              pipe_properties_df[:]['D_int':'D_int'].
                                                                              values, pipe_length_df.values,
                                                                              edge_mass_flow_df.ix[t].values,
                                                                              T_supply_nodes, T_return_nodes, gv)

        # store node temperatures and pressures, as well as plant heat requirement and overall pressure drop at each
        # time step
        T_supply_nodes_list.append(T_supply_nodes)
        T_return_nodes_list.append(T_return_nodes)
        q_loss_supply_edges_list.append(q_loss_supply_edges)
        plant_heat_requirements.append(plant_heat_requirement)
        pressure_nodes_supply.append(P_supply_nodes[0])
        pressure_nodes_return.append(P_return_nodes[0])
        pressure_loss_system.append(delta_P_network)

        print (time.clock() - timer, 'seconds process time for time step', t)

    # save results
    # node temperatures
    pd.DataFrame(T_supply_nodes_list, columns=edge_node_df.index).to_csv(
        locator.get_optimization_network_layout_supply_temperature_file(network_type),
        na_rep='NaN', index=False, float_format='%.3f')
    pd.DataFrame(T_return_nodes_list, columns=edge_node_df.index).to_csv(
        locator.get_optimization_network_layout_return_temperature_file(network_type),
        na_rep='NaN', index=False, float_format='%.3f')

    # save edge heat losses in the supply line
    pd.DataFrame(q_loss_supply_edges_list, columns=edge_node_df.columns).to_csv(
        locator.get_optimization_network_layout_qloss_file(network_type),
        na_rep='NaN', index=False, float_format='%.3f')

    # plant heat requirements
    pd.DataFrame(plant_heat_requirements, columns=filter(None,all_nodes_df.loc['plant'].values)).to_csv(
        locator.get_optimization_network_layout_plant_heat_requirement_file(network_type), index=False,
        float_format='%.3f')
    # node pressures
    pd.DataFrame(pressure_nodes_supply, columns=edge_node_df.index).to_csv(
        locator.get_optimization_network_layout_supply_pressure_file(network_type), index=False, float_format='%.3f')
    pd.DataFrame(pressure_nodes_return, columns=edge_node_df.index).to_csv(
        locator.get_optimization_network_layout_return_pressure_file(network_type), index=False, float_format='%.3f')
    # pressure losses over entire network
    pd.DataFrame(pressure_loss_system, columns=['pressure_loss_supply_Pa','pressure_loss_return_Pa',
                                                'pressure_loss_total_Pa']).to_csv(
        locator.get_optimization_network_layout_pressure_drop_file(network_type), index=False, float_format='%.3f')

    print (time.clock() - t0, "seconds process time for network thermal-hydraulic calculation \n")


# ===========================
# Hydraulic calculation
# ===========================

def calc_mass_flow_edges(edge_node_df, mass_flow_substation_df):
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

    ..[Todini & Pilati, 1987] Todini & Pilati. "A gradient method for the analysis of pipe networks," in Computer
     Applications in Water Supply Volume 1 - Systems Analysis and Simulation, 1987.
    ..[Ikonen, E., et al, 2016] Ikonen, E., et al. Examination of Operational Optimization at Kemi District Heating
    Network. Thermal Science. 2016, Vol. 20, No.2, pp.667-678.
    ..[Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
    Applied Thermal Engineering, 2016.

    """
    mass_flow_substation_df = mass_flow_substation_df.sort_index(axis=1)
    # t0 = time.clock()
    mass_flow_edge = np.round(np.transpose(np.linalg.lstsq(edge_node_df.values, np.transpose(
        mass_flow_substation_df.values))[0]), decimals = 9)  # FIXME
    # print time.clock() - t0, "seconds process time for total mass flow calculation\n"

    return mass_flow_edge


def assign_pipes_to_edges(mass_flow_df, locator, gv):
    """
    This function assigns pipes from the catalog to the network for a network with unspecified pipe properties.
    Pipes are assigned based on each edge's minimum and maximum required flow rate (for now).

    :param mass_flow_df: DataFrame containing the mass flow rate for each edge e at each time of the year t
    :param locator: an InputLocator instance set to the scenario to work on
    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)
    :type mass_flow_df: DataFrame
    :type locator: InputLocator
    :type gv: GlobalVariables

    :return pipe_properties_df: DataFrame containing the pipe properties for each edge in the network

    Sources of the pipe_catalog could be found in the excel file
    """

    # import pipe catalog from Excel file
    pipe_catalog = pd.read_excel(locator.get_thermal_networks(),sheetname=['PIPING CATALOG'])['PIPING CATALOG']
    pipe_catalog['Vdot_min'] = pipe_catalog['Vdot_min'] * gv.Pwater
    pipe_catalog['Vdot_max'] = pipe_catalog['Vdot_max'] * gv.Pwater
    pipe_properties_df = pd.DataFrame(data=None, index=pipe_catalog.columns.values, columns=mass_flow_df.columns.values)
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
    :param mass_flow_rate: matrix containing the mass flow rate in each edge e at time t               (1 x e)
    :param T_supply_node: array containing the temperature in each supply node n                       (1 x n)
    :param T_return_node: array containing the temperature in each return node n                       (1 x n)
    :param gv: globalvars
    :type edge_node_df: DataFrame
    :type pipe_diameter: ndarray
    :type pipe_length: ndarray
    :type mass_flow_rate: ndarray
    :type T_supply_node: list
    :type T_return_node: list

    :return pressure_loss_nodes_supply: array containing the pressure loss at each supply node         (1 x n)
    :return pressure_loss_nodes_return: array containing the pressure loss at each return node         (1 x n)
    :return pressure_loss_system: pressure loss over the entire network
    :rtype pressure_loss_nodes_supply: ndarray
    :rtype pressure_loss_nodes_return: ndarray
    :rtype pressure_loss_system: float

    ..[Todini & Pilati, 1987] Todini & Pilati. "A gradient method for the analysis of pipe networks," in Computer
     Applications in Water Supply Volume 1 - Systems Analysis and Simulation, 1987.
    ..[Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
    Applied Thermal Engineering, 2016.

    """

    # get the temperatures at each supply and return edge
    temperature_supply_edges = calc_edge_temperatures(T_supply_node, edge_node_df)
    temperature_return_edges = calc_edge_temperatures(T_return_node, edge_node_df)

    # get the pressure drop through each edge
    pressure_loss_pipe_supply = calc_pressure_loss_pipe(pipe_diameter, pipe_length, mass_flow_rate,
                                                        temperature_supply_edges, gv)
    pressure_loss_pipe_return = calc_pressure_loss_pipe(pipe_diameter, pipe_length, mass_flow_rate,
                                                        temperature_return_edges, gv)

    # total pressure loss in the system
    # # pressure losses at the supply plant are assumed to be included in the pipe losses as done by Oppelt et al., 2016
    # pressure_loss_system = sum(np.nan_to_num(pressure_loss_pipe_supply)[0]) + sum(
    #     np.nan_to_num(pressure_loss_pipe_return)[0])
    pressure_loss_system = calc_pressure_loss_system(pressure_loss_pipe_supply, pressure_loss_pipe_return)

    # solve for the pressure at each node based on Eq. 1 in Todini & Pilati for no = 0 (no nodes with fixed head):
    # A12 * H + F(Q) = -A10 * H0 = 0
    # edge_node_transpose * pressure_nodes = - (pressure_loss_pipe) (Ax = b)
    edge_node_transpose = np.transpose(edge_node_df.values)
    pressure_nodes_supply = np.round(
        np.transpose(np.linalg.lstsq(edge_node_transpose, np.transpose(pressure_loss_pipe_supply)*(-1))[0]), decimals=9)  # FIXME
    pressure_nodes_return = np.round(
        np.transpose(np.linalg.lstsq(-edge_node_transpose, np.transpose(pressure_loss_pipe_return)*(-1))[0]), decimals=9)  # FIXME

    return pressure_nodes_supply, pressure_nodes_return, pressure_loss_system


def calc_pressure_loss_pipe(pipe_diameter, pipe_length, mass_flow_rate, temperature, gv):
    """
    Calculates the pressure losses throughout a pipe based on the Darcy-Weisbach equation and the Swamee-Jain
    solution for the Darcy friction factor [Oppelt et al., 2016].

    :param pipe_diameter: vector containing the pipe diameter in m for each edge e in the network           (e x 1)
    :param pipe_length: vector containing the length in m of each edge e in the network                     (e x 1)
    :param mass_flow_rate: matrix containing the mass flow rate in each edge e at time t                    (t x e)
    :param temperature: matrix containing the temperature of the water in each edge e at time t             (t x e)
    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)
    :type pipe_diameter: ndarray
    :type pipe_length: ndarray
    :type mass_flow_rate: ndarray
    :type temperature: list
    :type gv: GlobalVariables

    :return pressure_loss_edge: pressure loss through each edge e at each time t                            (t x e)
    :rtype pressure_loss_edge: ndarray

    ..[Oppelt, T., et al., 2016] Oppelt, T., et al. Dynamic thermo-hydraulic model of district cooling networks.
    Applied Thermal Engineering, 2016.

    """

    # calculate the properties of water flowing in the pipes at the given temperature
    kinematic_viscosity = calc_kinematic_viscosity(temperature)  # m2/s
    reynolds = 4*(mass_flow_rate/gv.Pwater)/(math.pi * kinematic_viscosity * pipe_diameter)  # FIXME
    pipe_roughness = gv.roughness

    # calculate the Darcy-Weisbach friction factor using the Swamee-Jain equation
    darcy = 1.325 * np.log(pipe_roughness / (3.7 * pipe_diameter) + 5.74 / reynolds ** 0.9) ** (-2)  # FIXME

    # calculate the pressure losses through a pipe using the Darcy-Weisbach equation
    pressure_loss_edge = darcy * 8 * mass_flow_rate**2 * pipe_length/(math.pi**2 * pipe_diameter**5 * gv.Pwater)  # FIXME

    return pressure_loss_edge

def calc_pressure_loss_system(pressure_loss_pipe_supply, pressure_loss_pipe_return):
    pressure_loss_system = np.full(3, np.nan)
    pressure_loss_system[0] = sum(np.nan_to_num(pressure_loss_pipe_supply)[0])
    pressure_loss_system[1] = sum(np.nan_to_num(pressure_loss_pipe_return)[0])
    pressure_loss_system[2] = pressure_loss_system[0] + pressure_loss_system[1]
    return pressure_loss_system


def calc_kinematic_viscosity(temperature):
    """
    Calculates the kinematic viscosity of water as a function of temperature based on a simple fit from data from the
    engineering toolbox

    :param temperature: in K
    :return kinematic viscosity in m2/s

    """

    return 2.652623e-8*math.e**(557.5447*(temperature-140)**-1)  # FIXME


def calc_max_edge_flowrate(all_nodes_df, building_names, buildings_demands, edge_node_df, gv, locator,
                           substations_HEX_specs, t_target_supply, network_type):
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
                                     columns=edge_node_df.index.values) #TODO: for test case validation, delete when done

    print('start calculating edge mass flow...')

    t0 = time.clock()
    for t in range(8760):
        print('\n calculating edge mass flow... time step', t)

        # set to the highest value in the network and assume no loss within the network
        T_substation_supply = t_target_supply.ix[t].max() + 273.15  # in [K] # FIXME

        # calculate substation flow rates and return temperatures
        if network_type == 'DH' or (network_type == 'DC' and math.isnan(T_substation_supply) is False):
            T_return_all, \
                mdot_all = substation.substation_return_model_main(locator, gv, building_names, buildings_demands,
                                                                   substations_HEX_specs, T_substation_supply, t,
                                                                   network_type,
                                                                   t_flag = True)
            # t_flag = True: same temperature for all nodes
        else:
            T_return_all = np.full(building_names.size,T_substation_supply).T
            mdot_all = pd.DataFrame(data=np.zeros(len(building_names)), index=building_names.values).T

        # write consumer substation required flow rate to nodes
        required_flow_rate_df = write_substation_massflows_to_nodes_df(all_nodes_df, mdot_all)
        # (1 x n)

        # solve mass flow rates on edges
        edge_mass_flow_df[:][t:t + 1] = calc_mass_flow_edges(edge_node_df, required_flow_rate_df)

        node_mass_flow_df[:][t:t + 1] = required_flow_rate_df.values  #TODO: for test case validation, delete when done

    # create csv file to store the nominal edge mass flow results
    edge_mass_flow_df.to_csv(locator.get_optimization_network_layout_folder() + '//' + 'NominalEdgeMassFlow_' +
                             network_type + '.csv')
    node_mass_flow_df.to_csv(locator.get_optimization_network_layout_folder() + '//' + 'Node_MassFlow_' +
                             network_type + '.csv')
    print (time.clock() - t0, "seconds process time for edge mass flow calculation\n")

    # edge_mass_flow_df = pd.read_csv(locator.get_edge_mass_flow_csv_file(network_type))  #TODO: delete when finish testing
    # del edge_mass_flow_df['Unnamed: 0']

    # assign pipe properties based on max flow on edges
    max_edge_mass_flow = edge_mass_flow_df.max(axis=0)
    max_edge_mass_flow_df = pd.DataFrame(data=[max_edge_mass_flow], columns=edge_node_df.columns)

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
    temperatures at its start and end node as done, for example, by Wang et al. (2016), that is:
        T_edge = (T_node_1 + T_node_2)/2

    :param temperature_node: array containing the temperature in each node n                                (1 x n)
    :param edge_node: matrix consisting of n rows (number of nodes) and e columns (number of edges) and
                      indicating the direction of flow of each edge e at node n: if e points to n, value
                      is 1; if e leaves node n, -1; else, 0.                                                (n x e)

    :return temperature_edge: array containing the temperature in each edge e                               (1 x n)

    ..[Wang et al., 2016] Wang et al. "A method for the steady-state thermal simulation of district heating systems and
    model parameters calibration," in Energy Conversion and Management Vol. 120, 2016, pp. 294-305.
    """

    # in order to calculate the edge temperatures, node temperature values of 'nan' were not acceptable
    # so these were converted to 0 and then converted back to 'nan'
    temperature_edge = np.dot(np.nan_to_num(temperature_node),abs(edge_node)/2)
    for i in range(len(temperature_edge)):
        if temperature_edge[i] < 273:
            temperature_edge[i] = np.nan

    return temperature_edge


# ===========================
# Thermal calculation
# ===========================


def solve_network_temperatures(locator, gv, T_ground, edge_node_df, all_nodes_df, edge_mass_flow_df, K,
                               t_target_supply_df, building_names, buildings_demands, substations_HEX_specs, t,
                               network_type):
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
    :param K: aggregated heat conduction coefficient for each pipe                                          (1 x e)
    :param t_target_supply_df: target supply temperature at each substation
    :param building_names: list of building names in the scenario
    :param buildings_demands: demand of each building in the scenario
    :param substations_HEX_specs: DataFrame with substation heat exchanger specs at each building.
    :param t: current time step
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling
                        ('DC') network

    :type locator: InputLocator
    :type gv: GlobalVariables
    :type edge_node_df: DataFrame
    :type all_nodes_df: DataFrame
    :type edge_mass_flow_df: DataFrame
    :type locator: InputLocator
    :type substations_HEX_specs: DataFrame
    :type network_type: str
    :type t_target_supply_df: DataFrame

    :returns T_supply_nodes: list of supply line node temperatures (nx1)
    :rtype T_supply_nodes: list of arrays
    :returns T_return_nodes: list of return line node temperatures (nx1)
    :rtype T_return_nodes: list of arrays
    :returns plant_heat_requirement: list of plant heat requirement
    :rtype plant_heat_requirement: list of arrays

    """

    if edge_mass_flow_df.values.sum() != 0:

        # calculate node temperatures on the supply network accounting losses in the network.
        T_supply_nodes, plant_node, q_loss_edges = calc_supply_temperatures(gv, T_ground[t], edge_node_df, edge_mass_flow_df, K,
                                                              t_target_supply_df.loc[t], network_type)

        # write supply temperatures to substation nodes
        T_substation_supply = write_nodes_to_substations(T_supply_nodes, all_nodes_df, plant_node)

        # # Iterations to find out the corresponding node supply temperature and substation mass flow
        flag = 0
        iteration = 0
        while flag == 0:
            # calculate substation return temperatures according to supply temperatures
            T_return_all, \
                mdot_all = substation.substation_return_model_main(locator, gv, building_names, buildings_demands,
                                                                   substations_HEX_specs, T_substation_supply, t,
                                                                   network_type, t_flag=False)
            if mdot_all.values.max() is np.nan:
                print ('Error in edge mass flow! Check edge_mass_flow_df')

            # write consumer substation return T and required flow rate to nodes
            T_substation_return_df = write_substation_temperatures_to_nodes_df(all_nodes_df, T_return_all)  # (1 x n)
            mass_flow_substations_nodes_df = write_substation_massflows_to_nodes_df(all_nodes_df, mdot_all)

            # solve for the required mass flow rate on each pipe
            edge_mass_flow_df_2 = calc_mass_flow_edges(edge_node_df, mass_flow_substations_nodes_df)

            # calculate updated node temperatures on the supply network with updated edge mass flow
            T_supply_nodes_2, plant_node, q_loss_edges_2 = calc_supply_temperatures(gv, T_ground[t], edge_node_df, edge_mass_flow_df_2,
                                                                    K, t_target_supply_df.loc[t], network_type)
            # write supply temperatures to substation nodes
            T_substation_supply_2 = write_nodes_to_substations(T_supply_nodes_2, all_nodes_df, plant_node)

            # check if the supply temperature at substations converged
            node_dT = T_substation_supply_2 - T_substation_supply
            # if all(np.isnan(T_substation_supply)) and all(np.isnan(T_substation_supply_2)) is False:
            if len(abs(node_dT).dropna(axis=1)) == 0:
                max_node_dT = 0
            else:
                max_node_dT = max(abs(node_dT).dropna(axis=1).values[0])
                # max supply node temperature difference

            if max_node_dT > 1 and iteration < 10:
                # update the substation supply temperature and re-enter the iteration
                T_substation_supply = T_substation_supply_2
                print (iteration, 'iteration. Maximum node temperature difference:', max_node_dT)
                iteration += 1
            elif max_node_dT > 10 and 20 > iteration >= 10:
                # FIXME: This is to avoid endless iteration, other design strategies should be implemented.
                # update the substation supply temperature and re-enter the iteration
                T_substation_supply = T_substation_supply_2
                print (iteration, 'iteration. Maximum node temperature difference:', max_node_dT)
                iteration += 1
            else:
                # calculate substation return temperatures according to supply temperatures
                T_return_all_2, \
                    mdot_all_2 = substation.substation_return_model_main(locator, gv, building_names, buildings_demands,
                                                                       substations_HEX_specs, T_substation_supply_2, t,
                                                                       network_type, t_flag=False)
                # write consumer substation return T and required flow rate to nodes
                T_substation_return_df_2 = write_substation_temperatures_to_nodes_df(all_nodes_df, T_return_all_2)  # (1xn)
                mass_flow_substations_nodes_df_2 = write_substation_massflows_to_nodes_df(all_nodes_df, mdot_all_2)
                # solve for the required mass flow rate on each pipe
                edge_mass_flow_df_2 = calc_mass_flow_edges(edge_node_df, mass_flow_substations_nodes_df_2)
                # exit iteration
                flag = 1
                if max_node_dT < 1:
                    print('supply temperature converged after', iteration, 'iterations', 'dT:', max_node_dT)
                else:
                    print('Warning: supply temperature did not converge after', iteration, 'iterations at timestep', t,
                          'dT:', max_node_dT)

        # calculate node temperatures on the return network
        T_return_nodes_2 = calc_return_temperatures(gv, T_ground[t], edge_node_df, edge_mass_flow_df_2,
                                                  mass_flow_substations_nodes_df_2, K, T_substation_return_df_2)


        plant_heat_requirement = calc_plant_heat_requirement(plant_node, T_supply_nodes_2, T_return_nodes_2,
                                                             mass_flow_substations_nodes_df_2, gv)

    else:
        T_supply_nodes_2 = np.full(edge_node_df.shape[0], np.nan)
        T_return_nodes_2 = np.full(edge_node_df.shape[0], np.nan)
        q_loss_edges_2 = np.full(edge_node_df.shape[1], 0)
        edge_mass_flow_df_2 = edge_mass_flow_df
        plant_heat_requirement = np.full(np.argwhere(all_nodes_df.ix['plant']!='').size, 0)


    return T_supply_nodes_2, T_return_nodes_2, plant_heat_requirement, edge_mass_flow_df_2, q_loss_edges_2

def calc_plant_heat_requirement(plant_node, T_supply_nodes, T_return_nodes, mass_flow_substations_nodes_df, gv):
    plant_heat_requirement = np.full(plant_node.size, np.nan)
    for i in range(plant_node.size):
        node = plant_node[i]
        heat_requirement = gv.Cpw * (T_supply_nodes[node] - T_return_nodes[node]) * abs(
            mass_flow_substations_nodes_df.iloc[0, node])
        plant_heat_requirement[i] = heat_requirement
    return plant_heat_requirement

def write_nodes_to_substations(T_supply_nodes, all_nodes_df, plant_node):
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
    T_substation_supply = all_nodes_df.copy().sort_index(axis=1)
    T_substation_supply.columns = all_nodes_df.sort_index(axis=1).sum()
    T_substation_supply.loc['T_supply'] = T_supply_nodes
    T_substation_supply = T_substation_supply.drop('consumer')
    T_substation_supply = T_substation_supply.drop('plant')

    return T_substation_supply

def write_nodes_to_substations_1(T_supply_nodes, all_nodes_df, plant_node):
    """
    This function writes node values to the corresponding building substations.

    :param T_supply_nodes: DataFrame of supply line node temperatures (nx1)
    :param all_nodes_df: DataFrame that contains all nodes, whether a node is a consumer, plant, or neither,
                        and, if it is a consumer or plant, the name of the corresponding building               (2 x n)
    :param plant_node: the indices of the plant node(s)

    :type T_supply_nodes: DataFrame
    :type all_nodes_df: DataFrame
    :type plant_node: numpy array

    :return T_substation_supply
    :rtype T_substation_supply: float
    """
    T_substation_supply = all_nodes_df.copy().sort_index(axis=1)
    T_substation_supply.columns = all_nodes_df.sort_index(axis=1).sum()
    T_substation_supply.loc['T_supply'] = T_supply_nodes

    return T_substation_supply.astype(float)



def calc_supply_temperatures(gv, T_ground, edge_node_df, mass_flow_df, K, t_target_supply, network_type):
    """
    This function calculate the node temperatures considering heat losses in the supply network.
    Starting from the plant supply node, the function go through the edge-node index to search for the outlet node, and
    calculate the outlet node temperature after heat loss. And starting from the outlet node, the function calculates
    the node temperature at the corresponding pipe outlet, and the calculation goes on until all the node temperatures
    are solved. At nodes connecting to multiple pipes, the mixing temperature is calculated.

    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)
    :param T_ground: vector with ground temperatures in K
    :param edge_node_df: DataFrame consisting of n rows (number of nodes) and e columns (number of edges)
                        and indicating the direction of flow of each edge e at node n: if e points to n,
                        value is 1; if e leaves node n, -1; else, 0.                                        (n x e)
    :param mass_flow_df: DataFrame containing the mass flow rate for each edge e at each time of the year t (1 x e)
    :param K: aggregated heat conduction coefficient for each pipe                                          (1 x e)
    :param t_target_supply: target supply temperature at each substation
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
    Z = np.asarray(edge_node_df)   # (nxe) edge-node matrix
    Z_pipe_out = Z.clip(min=0)     # pipe outlet matrix
    Z_pipe_in = Z.clip(max=0)      # pipe inlet matrix

    M_d = np.zeros((Z.shape[1], Z.shape[1]))   # (exe) pipe mass flow rate matrix
    np.fill_diagonal(M_d, mass_flow_df)

    # matrices to store results
    T_e_out = Z_pipe_out.copy()
    T_e_in = Z_pipe_in.copy().dot(-1)
    T_node = np.zeros(Z.shape[0])
    Z_note = Z.copy()   # matrix to store information of solved nodes

    # start node temperature calculation
    flag = 0
    # set initial supply temperature guess to the target substation supply temperature
    T_plant_sup_0 = 273 + t_target_supply.max()
    T_plant_sup = T_plant_sup_0
    iteration = 0
    while flag == 0:
        # # calculate the pipe outlet temperature from the plant node
        for i in range(Z.shape[0]):
            if np.argwhere(Z[i]==1).size == 0:  # find plant node
                    # write plant inlet temperature
                    T_node[i] = T_plant_sup   # assume plant inlet temperature
                    edge = np.where(T_e_in[i]!=0)[0]   # find edge index
                    T_e_in[i] = T_e_in[i]*T_node[i]
                    # calculate pipe outlet temperature
                    calc_t_out(i, edge, K, M_d, Z, T_e_in, T_e_out, T_ground, Z_note, gv)
        plant_node = T_node.nonzero()[0]   # the node indices of the plant nodes in the edge-node index

        # # calculate pipe outlet temperature and node temperature for the rest
        while np.count_nonzero(T_node == 0) > 0:
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
                    T_node[j] = np.nan if np.isnan(T_e_out[3]).any() else T_e_out[j].max()
                elif T_e_out[j].min() < 0:
                    print('negative node temperature!')

        # # iterate the plant supply temperature until all the node temperature reaches the target temperatures
        if network_type is 'DH':
            # calculate the difference between node temperature and the target supply temperature at substations
            # [K] temperature differences b/t node supply and target supply
            dT = (T_node - (t_target_supply + 273.15)).dropna()
            # enter iteration if the node supply temperature is lower than the target supply temperature
            # (0.1 is the tolerance)
            if all(dT > -0.1) is False and (T_plant_sup - T_plant_sup_0) < 60:
                    # increase plant supply temperature and re-iterate the node supply temperature calculation
                    # increase by the maximum amount of temperature deficit at nodes
                    T_plant_sup = T_plant_sup + abs(dT.min())

                    # reset the matrices for supply network temperature calculation
                    Z_note = Z.copy()
                    T_e_out = Z_pipe_out.copy()
                    T_e_in = Z_pipe_in.copy().dot(-1)
                    T_node = np.zeros(Z.shape[0])
                    iteration += 1

            elif all(dT > -0.1) is False and (T_plant_sup - T_plant_sup_0) >= 60:  # FIXME
                # end iteration if total network temperature drop is higher than 60 K
                print ('cannot fulfill substation supply node temperature requirement after iterations:',
                       iteration, dT.min())
                node_insufficient = dT[dT < 0].index.values
                for node in range(node_insufficient.size):
                    index_insufficient = np.argwhere(edge_node_df.index == node_insufficient[node])[0]
                    T_node[index_insufficient] = t_target_supply[index_insufficient] + 273.15
                    # force setting node temperature to target to avoid substation HEX calculation error.
                    # However, it might potentially cause error at mass flow iteration.
                flag = 1
            else:
                flag = 1
        else:  # when network type == 'DC'
            # calculate the difference between node temperature and the target supply temperature at substations
            # [K] temperature differences b/t node supply and target supply
            dT = (T_node - (t_target_supply + 273.15)).dropna()

            # enter iteration if the node supply temperature is higher than the target supply temperature
            # (0.1 is the tolerance)
            if all(dT < 0.1) is False and (T_plant_sup_0 - T_plant_sup) < 10:
                # increase plant supply temperature and re-iterate the node supply temperature calculation
                # increase by the maximum amount of temperature deficit at nodes
                T_plant_sup = T_plant_sup - abs(dT.max())
                Z_note = Z.copy()
                T_e_out = Z_pipe_out.copy()
                T_e_in = Z_pipe_in.copy().dot(-1)
                T_node = np.zeros(Z.shape[0])
                iteration += 1
            elif all(dT < 0.1) is False and (T_plant_sup_0 - T_plant_sup) >= 10:
                # end iteration if total network temperature rise is higher than 10 K
                print('cannot fulfill substation supply node temperature requirement after iterations:',
                      iteration, dT.min())
                node_insufficient = dT[dT > 0].index.values
                for node in range(node_insufficient.size):
                    index_insufficient = np.argwhere(edge_node_df.index == node_insufficient[node])[0]
                    T_node[index_insufficient] = t_target_supply[index_insufficient] + 273.15
                    # force setting node temperature to target to avoid substation HEX calculation error.
                    # However, it might potentially cause error at mass flow iteration.
                    flag = 1
            else:
                flag = 1

    # calculate pipe heat losses
    q_loss_edges = np.zeros(Z_note.shape[1])
    for edge in range(Z_note.shape[1]):
        if M_d[edge,edge] > 0:
            dT_edge = T_e_in[:, edge].max() - T_e_out[:,edge].max()
            q_loss_edges[edge] = M_d[edge,edge] * gv.Cpw * dT_edge  # kW


    return T_node.T, plant_node, q_loss_edges


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
    Z_pipe_out = Z.clip(min=0)     # pipe outlet matrix
    Z_pipe_in = Z.clip(max=0)      # pipe inlet matrix

    M_sub = np.zeros((Z.shape[0], Z.shape[0]))    # (nxn) substation flow rate matrix
    np.fill_diagonal(M_sub, mass_flow_substation_df)

    M_d = np.zeros((Z.shape[1], Z.shape[1]))   # (exe) pipe mass flow rate matrix
    np.fill_diagonal(M_d, mass_flow_df)

    # matrices to store results
    T_e_out = Z_pipe_out.copy()
    T_e_in = Z_pipe_in.copy().dot(-1)
    T_node = np.zeros(Z.shape[0])
    Z_note = Z.copy()   # matrix to store information of solved nodes

    # calculate the return pipe node temperature of substations locating at the end of the branch
    for i in range(Z.shape[0]):
            # choose the consumer nodes locating at the end of the branches
            if np.count_nonzero(Z[i] == 1) == 0 and np.count_nonzero(Z[i] == 0) != Z.shape[1]:
                T_node[i] = t_return.values[0,i]
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
                        if T_e_in[j, edge]!=0:
                            T_e_in[j, edge]=T_node[j]
                            # calculate pipe outlet
                            calc_t_out(j, edge, K, M_d, Z, T_e_in, T_e_out, T_ground, Z_note, gv)
                if np.argwhere(Z_note[j]==0).size == Z.shape[1] and T_node[j]==0:
                    T_node[j] = calc_return_node_temperature(j, M_d, T_e_out, t_return, Z_pipe_out, M_sub)

    # calculate temperature with merging flows from pipes at the plant node
    node_index = np.where(T_node == 0)[0].max()

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

    :type index: float
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
        total_mcp_from_substations = 0 if M_sub[index].max()==0 else np.dot(M_sub[index].max(), t_return.values[0,
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
    if isinstance(edge, np.ndarray) is False:
        edge = np.array([edge])

    for i in range(edge.size):
        e = edge[i]
        k = K[e, e]
        m = M_d[e, e]
        out_node_index = np.where(Z[:, e] == 1)[0].max()
        if m <= 0 and Z[node, e] == -1:
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
            Z_note[:, e] = 0



def calc_aggregated_heat_conduction_coefficient(locator, gv, L_pipe, pipe_properties_df):
    """
    This function calculates the aggregated heat conduction coefficients of all the pipes.
    Following the reference from [Wang et al., 2016].

    :param locator: an InputLocator instance set to the scenario to work on
    :param gv: an instance of globalvar.GlobalVariables with the constants  to use (like `list_uses` etc.)
    :param L_pipe: vector with the pipe length on each edge (1xe)
    :param pipe_properties_df: DataFrame containing the pipe properties for each edge in the network
    :type locator: InputLocator
    :type gv: GlobalVariables
    :type L_pipe: DataFrame
    :type pipe_properties_df: DataFrame

    :return K_all: DataFrame of aggregated heat conduction coefficients (1 x e) for all edges


    ..[Wang et al, 2016] Wang J., Zhou, Z., Zhao, J. (2016). A method for the steady-state thermal simulation of
    district heating systems and model parameters calibration. Eenergy Conversion and Management, 120, 294-305.
    """
    material_properties = pd.read_excel(locator.get_thermal_networks(), sheetname=['MATERIAL PROPERTIES'])['MATERIAL PROPERTIES']
    material_properties = material_properties.set_index(material_properties['material'].values)
    conductivity_pipe = material_properties.ix['Steel','lamda']     # [W/mC]
    conductivity_insulation = material_properties.ix['PUR','lamda'] # [W/mC]
    conductivity_ground = material_properties.ix['Soil','lamda']    # [W/mC]
    network_depth = gv.NetworkDepth       # [m]
    extra_heat_transfer_coef = 0.2   # TODO: find equation in the paper

    K_all = []
    for pipe in L_pipe.index:
        # calculate heat resistances, equation (3) in Wang et al., 2016
        R_pipe = np.log(pipe_properties_df.loc['D_ext', pipe]/pipe_properties_df.loc['D_int', pipe])/(2*math.pi*conductivity_pipe)     #[mC/W]
        R_insulation = np.log((pipe_properties_df.loc['D_ins', pipe])/pipe_properties_df.loc['D_ext', pipe])/(2*math.pi*conductivity_insulation)
        a= 2*network_depth/(pipe_properties_df.loc['D_ins', pipe])
        R_ground = np.log(a+(a**2-1)**0.5)/(2*math.pi*conductivity_ground) #[mC/W]  # FIXME: find equation in paper
        # calculate the aggregated heat conduction coefficient, equation (4) in Wang et al., 2016
        k = L_pipe[pipe]*(1 + extra_heat_transfer_coef)/(R_pipe + R_insulation + R_ground)/1000   #[kW/C]
        K_all.append(k)

    K_all = np.diag(K_all)
    return K_all



# ============================
# Other functions
# ============================


def get_thermal_network_from_csv(locator, network_type):
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
    node_data_df = pd.read_csv(locator.get_network_layout_nodes_csv_file(network_type))
    pipe_data_df = pd.read_csv(locator.get_network_layout_pipes_csv_file(network_type))

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
    edge_node_df = pd.DataFrame(data=edge_node_matrix, index=list_nodes, columns=list_pipes)

    edge_node_df.to_csv(locator.get_optimization_network_edge_node_matrix_file(network_type))
    all_nodes_df = pd.DataFrame(data=[consumer_nodes[1][:], plant_nodes[1][:]], index=['consumer', 'plant'],
                                columns=consumer_nodes[0][:])
    all_nodes_df = all_nodes_df[edge_node_df.index.tolist()]   #TODO: check node orders for zug
    all_nodes_df.to_csv(locator.get_optimization_network_node_list_file(network_type))

    print (time.clock() - t0, "seconds process time for Network summary\n")

    return edge_node_df, all_nodes_df, pipe_data_df['LENGTH']


def get_thermal_network_from_shapefile(locator, network_type):
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
    network_edges_df = gpd.read_file(locator.get_network_layout_edges_shapefile(network_type))
    network_nodes_df = gpd.read_file(locator.get_network_layout_nodes_shapefile(network_type))

    # get node and pipe information
    node_df, edge_df = extract_network_from_shapefile(network_edges_df, network_nodes_df)

    # create consumer and plant node vectors
    node_names = node_df.index.values
    consumer_nodes = []
    plant_nodes = []
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
    all_nodes_df = pd.DataFrame(data=[node_df['consumer'], node_df['plant']], index=['consumer', 'plant'],
                                columns=node_df.index)
    for node in all_nodes_df:
        if all_nodes_df[node]['consumer'] == 1:
            all_nodes_df[node]['consumer'] = node_df['Name'][node]
        else:
            all_nodes_df[node]['consumer'] = ''
        if all_nodes_df[node]['plant'] == 1:
            all_nodes_df[node]['plant'] = node_df['Name'][node]
        else:
            all_nodes_df[node]['plant'] = ''
    all_nodes_df = all_nodes_df.sort_index(axis=1)  # sort columns by node numbers
    all_nodes_df.to_csv(locator.get_optimization_network_node_list_file(network_type))

    # create first edge-node matrix
    list_pipes = edge_df.index.values
    list_nodes = sorted(set(edge_df['start node']).union(set(edge_df['end node'])))
    edge_node_matrix = np.zeros((len(list_nodes), len(list_pipes)))
    for j in range(len(list_pipes)):
        for i in range(len(list_nodes)):
            if edge_df['end node'][j] == list_nodes[i]:
                edge_node_matrix[i][j] = 1
            elif edge_df['start node'][j] == list_nodes[i]:
                edge_node_matrix[i][j] = -1
    edge_node_df = pd.DataFrame(data=edge_node_matrix, index=list_nodes, columns=list_pipes)

    # Since DataFrame doesn't indicate the direction of flow, an edge node matrix is generated as a first guess and
    # the mass flow at t = 0 is calculated with it. The direction of flow is then corrected by inverting negative flows.
    substation_mass_flows_df = pd.DataFrame(data=np.zeros([1,len(edge_node_df.index)]), columns=edge_node_df.index)
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
            new_nodes = [edge_df['end node'][i], edge_df['start node'][i]]
            edge_df['start node'][i] = new_nodes[0]
            edge_df['end node'][i] = new_nodes[1]

    edge_node_df.to_csv(locator.get_optimization_network_edge_node_matrix_file(network_type))
    edge_df.to_csv(locator.get_optimization_network_edge_list_file(network_type))

    print (time.clock() - t0, "seconds process time for Network summary\n")

    return edge_node_df, all_nodes_df, edge_df['pipe length']


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

    # import consumer and plant nodes
    end_nodes = []
    for node in node_shapefile_df['geometry']:
        end_nodes.append(node.coords[0])
    node_shapefile_df['geometry'] = end_nodes
    node_shapefile_df['consumer'] = np.zeros(len(node_shapefile_df['Plant']))
    for node in range(len(node_shapefile_df['consumer'])):
        if node_shapefile_df['Qh'][node] > 0:
            node_shapefile_df['consumer'][node] = 1

    # create node dictionary with plant and consumer nodes
    node_dict = {}
    node_columns = ['Node', 'Name', 'plant', 'consumer', 'coordinates']
    for i in range(len(node_shapefile_df)):
        node_dict[node_shapefile_df['geometry'][i]] = ['NODE'+str(i), node_shapefile_df['Name'][i],
                                                       node_shapefile_df['Plant'][i], node_shapefile_df['consumer'][i],
                                                       node_shapefile_df['geometry'][i]]

    # create edge dictionary with pipe lengths and start and end nodes
    # complete node dictionary with missing nodes (i.e., joints)
    edge_dict = {}
    edge_columns = ['pipe length', 'start node', 'end node']
    pipe_nodes = []
    for j in range(len(edge_shapefile_df)):
        pipe = edge_shapefile_df['geometry'][j]
        start_node = pipe.coords[0]
        end_node = pipe.coords[len(pipe.coords)-1]
        pipe_nodes.append(pipe.coords[0])
        pipe_nodes.append(pipe.coords[len(pipe.coords)-1])
        if start_node not in node_dict.keys():
            i += 1
            node_dict[start_node] = ['NODE'+str(i), 'TEE' + str(i - len(node_shapefile_df)), 0, 0, start_node]
        if end_node not in node_dict.keys():
            i += 1
            node_dict[end_node] = ['NODE'+str(i), 'TEE' + str(i - len(node_shapefile_df)), 0, 0, end_node]
        edge_dict['EDGE' + str(j)] = [edge_shapefile_df['Shape_Leng'][j], node_dict[start_node][0],
                                      node_dict[end_node][0]]

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

    # create DataFrames containing all nodes and edges
    node_df = pd.DataFrame.from_dict(node_dict, orient='index')
    node_df.columns = node_columns
    node_df = node_df.set_index(node_df['Node']).drop(['Node'], axis = 1)
    edge_df = pd.DataFrame.from_dict(edge_dict, orient='index')
    edge_df.columns = edge_columns

    return node_df, edge_df


def write_substation_massflows_to_nodes_df(all_nodes_df, df_value):
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

    # it is assumed that if there is more than one plant, they all supply the same amount of heat at each time step
    # (i.e., the amount supplied by each plant is not optimized)
    number_of_plants = 0

    for node in all_nodes_df:
        if all_nodes_df[node]['plant'] != '':
            number_of_plants += 1

    # calculate mass flow and write all flow rates into nodes DataFrame
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
    for building in df_value.columns:
        if not building in all_nodes_df.loc['consumer'].values:
            df_value[building] = 0

    for node in all_nodes_df:
        if all_nodes_df[node]['consumer'] != '':
            nodes_df[node] = df_value[all_nodes_df[node]['consumer']]
        elif all_nodes_df[node]['plant'] != '':
            nodes_df[node] = - df_value.sum(axis=1)/number_of_plants
        else:
            nodes_df[node] = 0
    nodes_df = nodes_df.sort_index(axis=1)  # sort dataframe columns by node numbers
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
    for node in all_nodes_df:
        if all_nodes_df[node]['consumer'] != '':
            nodes_df[node] = df_value[all_nodes_df[node]['consumer']]
        else:
            nodes_df[node] = np.nan  # set temperature value to nan for non-substation nodes

    nodes_df = nodes_df.sort_index(axis=1)  # sort dataframe columns by node numbers
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

    property_df = pd.DataFrame(index=range(8760), columns= building_names)
    for name in building_names:
        property_per_building = buildings_demands[(building_names == name).argmax()][property]
        property_df[name] = property_per_building
    return property_df


# ============================
# test
# ============================


def run_as_script(scenario_path=None):
    """
    run the whole network summary routine
    """
    import cea.globalvar
    import cea.inputlocator as inputlocator
    from cea.utilities import epwreader
    from cea.resources import geothermal

    gv = cea.globalvar.GlobalVariables()

    if scenario_path is None:
        scenario_path = gv.scenario_reference

    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    weather_file = locator.get_default_weather()

    # add geothermal part of pre-processing
    T_ambient = epwreader.epw_reader(weather_file)['drybulb_C']
    gv.ground_temperature = geothermal.calc_ground_temperature(T_ambient.values, gv)

    # add options for data sources: heating or cooling network, csv or shapefile
    network_type = ['DH', 'DC'] # set to either 'DH' or 'DC'
    source = ['csv', 'shapefile'] # set to csv or shapefile

    thermal_network_main(locator, gv, network_type[0], source[1])
    print ('test thermal_network_main() succeeded')

if __name__ == '__main__':
    run_as_script()


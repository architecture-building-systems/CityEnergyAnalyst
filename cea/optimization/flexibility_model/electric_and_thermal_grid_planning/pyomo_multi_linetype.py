from __future__ import division

import time

import numpy as np
import pandas as pd
from pyomo.environ import *

import get_initial_network as gia
from cea.technologies.network_layout.substations_location import calc_substation_location
from concept_parameters import *

# ============================
# Auxiliary functions for LP
# ============================

__author__ = "Thanh"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Thanh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def initial_network(config, locator):
    """
    Initiate data of main problem (not all the dict_length is included in this case)

    :returns:
        - **points_on_line** : information about every node in study case
        - **tranches** : tranches
        - **dict_length** : dictionary containing lengths
        - **dict_path** : dictionary containing paths
    :rtype: geodf, geodf, dict, dict

    """

    # localfiles
    input_buildings_shp = locator.get_electric_substation_input_location()
    output_substations_shp = locator.get_electric_substation_output_location()
    input_streets_shp = locator.get_street_network()

    # calcualte and save file with location
    building_points, _ = calc_substation_location(input_buildings_shp, output_substations_shp, [])
    points_on_line, tranches = gia.connect_building_to_grid(building_points, input_streets_shp)
    points_on_line_processed = gia.process_network(points_on_line, config, locator)
    dict_length, dict_path = gia.create_length_dict(points_on_line_processed, tranches)

    return points_on_line_processed, tranches, dict_length, dict_path


def annuity_factor(n, i):
    """
    Calculates the annuity factor derived by formula (1+i)**n * i / ((1+i)**n - 1)

    :param n: depreciation period (40 = 40 years)
    :type n: int
    :param i: interest rate (0.06 = 6%)
    :type i: float
    :returns:
        - **a**: annuity factor
    :rtype: float

    """

    a = (1 + i) ** n * i / ((1 + i) ** n - 1)

    return a


def get_peak_electric_demand(points_on_line):
    """
    Initialize Power Demand

    :param points_on_line: information about every node in study case
    :type points_on_line: GeoDataFrame
    :returns:
        - **dict_peak_el**: Value is the ELECTRIC peak demand depending on thermally connected or disconnected.
    :rtype: dict[node index][thermally connected bool]

    """

    dict_peak_el = {}
    dict_peak_el['thermally_conn_peak_el'] = {}
    dict_peak_el['thermally_disconn_peak_el'] = {}

    for idx_node, node in points_on_line.iterrows():
        if not np.isnan(node['GRID0_kW']):
            thermally_conn_peak_el = (node['Eal0_kW']
                                      + node['Edata0_kW']
                                      + node['Epro0_kW']
                                      + node['Eaux0_kW']
                                      + node['E_ww0_kW'])

            thermally_disconn_peak_el = (thermally_conn_peak_el
                                         + node['E_hs0_kW']
                                         + node['E_cs0_kW'])

            dict_peak_el['thermally_conn_peak_el'][idx_node] = thermally_conn_peak_el / (S_BASE * 10 ** 3)  # kW/MW
            dict_peak_el['thermally_disconn_peak_el'][idx_node] = thermally_disconn_peak_el / (
                        S_BASE * 10 ** 3)  # kW / MW

    return dict_peak_el


# ============================
# Objective function for LP
# ============================


def cost_rule(m, cost_type):
    """
    Cost rules of objective function. Calculation is depending on type cost

    :param m: complete pyomo model
    :type m: pyomo model
    :param cost_type: - 'inv_electric' investment costs for electric network
        - 'om_electric' operation and maintenance cost for electric network
        - 'losses' cost for power losses in lines
    :type cost_type: string
    :returns:
        - **pyomo equality function**: pyomo rule
    :rtype: function

    """

    if cost_type == 'inv_electric':
        c_inv_electric = 0.0
        for (i, j) in m.set_edge:
            for t in m.set_linetypes:
                c_inv_electric += 2.0 * (m.var_x[i, j, t] * m.dict_length[i, j]) \
                                  * m.dict_line_tech[t]['price_sgd_per_m'] * m.dict_line_tech[t]['annuity_factor']
        return m.var_costs['inv_electric'] == c_inv_electric

    elif cost_type == 'om_electric':
        # c_om = 0.0
        # for (i, j) in m.set_edge:
        #     for t in m.set_linetypes:
        #         c_om += 2 * (m.var_x[i, j, t] * m.dict_length[i, j])\
        #                 * m.dict_line_tech[t]['c_invest'] * m.dict_line_tech[t]['annuity_factor']\
        #                 * m.dict_line_tech[t]['om_factor']

        # each om factor is the same
        return m.var_costs['om_electric'] == m.var_costs['inv_electric'] * m.dict_line_tech[0][
            'om_factor']  # TODO Differentiation of types

    elif cost_type == 'losses':
        c_losses = 0.0
        for (i, j) in m.set_edge:
            for t in m.set_linetypes:
                c_losses += (m.var_power_over_line[i, j, t] * I_BASE) ** 2 \
                            * m.dict_length[i, j] * (m.dict_line_tech[t]['r_ohm_per_km'] / 1000.0) \
                            * APPROX_LOSS_HOURS \
                            * (ELECTRICITY_COST * (10 ** (-3)))

        return m.var_costs['losses'] == c_losses

    else:
        raise NotImplementedError("Unknown cost type!")


def obj_rule(m):
    return sum(m.var_costs[cost_type] for cost_type in m.set_cost_type)


# ============================
# Constraint rules
# ============================


def power_balance_rule(m, i):
    """
    Power balance of network. p_node_in of node equals to p_node_out.

    :param m: complete pyomo model
    :type m: pyomo model
    :param i: node index of set_nodes
    :type i: int
    :returns:
        - **pyomo equality function**: pyomo rule
    :rtype: function

    """

    p_node_in = 0.0
    p_node_out = 0.0

    if i in m.set_nodes_sub:
        p_node_in += m.var_power_sub[i]

    p_node_out += m.dict_connected[i] * float(m.dict_peak_el['thermally_conn_peak_el'][i])
    p_node_out += (1 - m.dict_connected[i]) * float(m.dict_peak_el['thermally_disconn_peak_el'][i])

    for j in m.set_nodes:
        if i != j and i < j:
            for t in m.set_linetypes:
                p_node_in += m.var_power_over_line[i, j, t]

    for j in m.set_nodes:
        if i != j and i > j:
            for t in m.set_linetypes:
                p_node_in -= m.var_power_over_line[j, i, t]

    return p_node_out == p_node_in


def power_over_line_rule(m, i, j, t):
    """
    Calculation of power over line with linear DC POWER FLOW MODEL.

    :param m: complete pyomo model
    :type m: pyomo model
    :param i: startnode index of set_edge
    :type i: int
    :param j: endnode index of set_edge
    :type j: int
    :param t: type index of set_linetypes
    :type t: int
    :returns:
        - **pyomo equality function**: pyomo rule
    :rtype: function

    """

    power_over_line = ((
                               ((m.var_theta[i] - m.var_theta[j]) * np.pi / 180)  # rad to degree
                               / (m.dict_length[i, j] * m.dict_line_tech[t]['x_ohm_per_km'] / 1000)
                       )
                       + m.var_slack[i, j, t])
    return m.var_power_over_line[i, j, t] == power_over_line


def slack_voltage_angle_rule(m, i):
    """
    Set the voltage angle of Substation node to zero

    :param m: complete pyomo model
    :type m: pyomo model
    :param i: node index of set_nodes_sub
    :type i: int
    :returns:
        - **pyomo equality function**: pyomo rule
    :rtype: function

    """

    return m.var_theta[i] == 0.0  # Voltage angle of slack has to be zero


def slack_pos_rule(m, i, j, t):
    """
    If decision variable m.var_x[i, j, t] is set to FALSE, the positive slack varibale var_slack[i, j, t] is nonzero

    :param m: complete pyomo model
    :type m: pyomo model
    :param i: startnode index of set_edge
    :type i: int
    :param j: endnode index of set_edge
    :type j: int
    :param t: type index of set_linetypes
    :type t: int
    :returns:
        - **pyomo equality function**: pyomo rule
    :rtype: function

    """

    return (m.var_slack[i, j, t]) <= (1 - m.var_x[i, j, t]) * 1000000


def slack_neg_rule(m, i, j, t):
    """
    If decision variable m.var_x[i, j, t] is set to FALSE, the negative slack varibale var_slack[i, j, t] is nonzero

    :param m: complete pyomo model
    :type m: pyomo model
    :param i: startnode index of set_edge
    :type i: int
    :param j: endnode index of set_edge
    :type j: int
    :param t: type index of set_linetypes
    :type t: int
    :returns:
        - **pyomo equality function**: pyomo rule
    :rtype: function

    """

    return (m.var_slack[i, j, t]) >= (-1) * (1 - m.var_x[i, j, t]) * 1000000


def power_over_line_rule_pos_rule(m, i, j, t):
    """
    If decision variable m.var_x[i, j, t] is set to TRUE, the positive power over the line var_power_over_line is
    limited by power_line_limit

    :param m: complete pyomo model
    :type m: pyomo model
    :param i: startnode index of set_edge
    :type i: int
    :param j: endnode index of set_edge
    :type j: int
    :param t: type index of set_linetypes
    :type t: int
    :returns:
        - **pyomo equality function**: pyomo rule
    :rtype: function

    """

    power_line_limit = m.var_x[i, j, t] \
                       * (m.dict_line_tech[t]['I_max_A'] * V_BASE * 10 ** 3) \
                       / (S_BASE * 10 ** 6)
    return m.var_power_over_line[i, j, t] <= power_line_limit


def power_over_line_rule_neg_rule(m, i, j, t):
    """
    If decision variable m.var_x[i, j, t] is set to TRUE, the negative power over the line var_power_over_line is
    limited by power_line_limit

    :param m: complete pyomo model
    :type m: pyomo model
    :param i: startnode index of set_edge
    :type i: int
    :param j: endnode index of set_edge
    :type j: int
    :param t: type index of set_linetypes
    :type t: int
    :returns:
        - **pyomo equality function**: pyomo rule
    :rtype: function

    """

    power_line_limit = (-1) * m.var_x[i, j, t] \
                       * (m.dict_line_tech[t]['I_max_A'] * V_BASE * 10 ** 3) \
                       / (S_BASE * 10 ** 6)
    return m.var_power_over_line[i, j, t] >= power_line_limit


def radial_rule(m):
    """
    To generate a cost efficient radial grid structure, the summation of the number of lines in the network is
    limited to the "number of nodes" - "number of substations"

    :param m: complete pyomo model
    :type m: pyomo model
    :returns:
        - **pyomo equality function**: pyomo rule
    :rtype: function
    """

    return summation(m.var_x) == (len(m.set_nodes) - len(m.set_nodes_sub))


def one_linetype_rule(m, i, j):
    """
    To decrease computational time, the number of line types is limited to a maximum one between two nodes

    :param m: complete pyomo model
    :type m: pyomo model
    :param i: startnode index of set_edge
    :type i: int
    :param j: endnode index of set_edge
    :type j: int
    :returns:
        - **pyomo equality function**: pyomo rule
    :rtype: function

    """

    number_of_linetypes = 0
    for t in m.set_linetypes:
        number_of_linetypes += m.var_x[i, j, t]
    return number_of_linetypes <= 1


def main(dict_connected, config, locator):
    """
    Main function of electric grid optimization tool. Generates pyomo model of grid problem

    :param dict_connected: key is node index. Value is binary and indicates if building is connected to thermal network
    :type dict_connected: dictionary
    :returns:
        - **m**: complete pyomo model
    :rtype: pyomo model

    """

    # ===========================================
    # Initialize Data
    # ===========================================

    # Street network and Buildings
    points_on_line, tranches, dict_length, dict_path = initial_network(config, locator)

    #for visualizing only
    # points_on_line.to_file(locator.get_network_layout_nodes_shapefile("EL", ""))
    # tranches.to_file(locator.get_network_layout_edges_shapefile("EL", ""))

    # Line Parameters
    df_line_parameter = pd.read_excel(locator.get_electrical_networks(), "CABLING CATALOG")
    dict_line_tech = dict(df_line_parameter.T)  # dict transposed dataframe

    # annuity factor (years, interest)
    for idx_line in dict_line_tech:
        dict_line_tech[idx_line]['annuity_factor'] = annuity_factor(40, INTEREST_RATE)

    # Cost types
    cost_types = [
        # Select cost types that you wish to include in the objective function
        'inv_electric',  # annual investment costs of electric lines, substations, and transformers
        'om_electric',  # operation and maintenance cost for electric network
        'losses',  # cost for power losses in lines
    ]

    # ============================
    # Index data
    # ============================

    idx_nodes_sub = points_on_line[points_on_line['Type'] == 'PLANT'].index
    idx_nodes_consum = points_on_line[points_on_line['Type'] == 'CONSUMER'].index
    idx_nodes = idx_nodes_sub.append(idx_nodes_consum)

    # Diagonal edge index matrix
    idx_edge = []
    for i in idx_nodes:
        for j in idx_nodes:
            if i != j and i < j:
                idx_edge.append((i, j))

    idx_linetypes = range(len(dict_line_tech))

    # ============================
    # Preprocess data
    # ============================
    dict_peak_el = get_peak_electric_demand(points_on_line)

    # Initialize Line Length
    dict_length_processed = {}
    for idx_node1, node1 in dict_length.iteritems():
        for idx_node2, length in node1.iteritems():
            dict_length_processed[idx_node1, idx_node2] = length

    # ============================
    # Model Problem
    # ============================

    m = ConcreteModel()
    m.name = 'CONCEPT - Electrical Network Opt'

    # Create Sets
    m.set_nodes = Set(initialize=idx_nodes)
    m.set_nodes_sub = Set(initialize=idx_nodes_sub)
    m.set_nodes_consum = Set(initialize=idx_nodes_consum)
    m.set_edge = Set(initialize=idx_edge)
    m.set_linetypes = Set(initialize=idx_linetypes)
    m.set_cost_type = Set(initialize=cost_types)

    # Create Constants
    m.dict_length = dict_length_processed.copy()
    m.dict_peak_el = dict_peak_el.copy()
    m.dict_line_tech = dict_line_tech.copy()
    m.dict_path = dict_path.copy()
    m.dict_connected = dict_connected.copy()

    # Create variables
    m.var_x = Var(m.set_edge, m.set_linetypes, within=Binary)  # decision variable for lines
    m.var_theta = Var(m.set_nodes, within=Reals, bounds=(-30.0, 30.0))  # in degree
    m.var_power_sub = Var(m.set_nodes_sub, within=NonNegativeReals)
    m.var_power_over_line = Var(m.set_edge, m.set_linetypes, within=Reals)
    m.var_slack = Var(m.set_edge, m.set_linetypes, within=Reals)
    m.var_costs = Var(m.set_cost_type, within=Reals)

    # Declare constraint functions
    m.power_balance_rule_constraint = Constraint(m.set_nodes, rule=power_balance_rule)
    m.power_over_line_constraint = Constraint(m.set_edge, m.set_linetypes, rule=power_over_line_rule)
    m.slack_voltage_angle_constraint = Constraint(m.set_nodes_sub, rule=slack_voltage_angle_rule)

    m.slack_neg_constraint = Constraint(m.set_edge, m.set_linetypes, rule=slack_neg_rule)
    m.slack_pos_constraint = Constraint(m.set_edge, m.set_linetypes, rule=slack_pos_rule)
    m.power_over_line_rule_neg_constraint = Constraint(m.set_edge, m.set_linetypes, rule=power_over_line_rule_neg_rule)
    m.power_over_line_rule_pos_constraint = Constraint(m.set_edge, m.set_linetypes, rule=power_over_line_rule_pos_rule)

    m.radial_constraint = Constraint(rule=radial_rule)
    m.one_linetype = Constraint(m.set_edge, rule=one_linetype_rule)

    # Declare objective function
    m.def_costs = Constraint(
        m.set_cost_type,
        doc='Cost definitions by type',
        rule=cost_rule)
    m.obj = Objective(
        sense=minimize,
        doc='Minimize costs = investment + om + power_losses',
        rule=obj_rule)

    return m


if __name__ == '__main__':
    t0 = time.clock()
    main()
    print 'pyomo_test succeeded'
    print('total time: ', time.clock() - t0)

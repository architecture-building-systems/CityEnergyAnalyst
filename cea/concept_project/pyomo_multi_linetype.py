from __future__ import division
import time
import get_initial_network as gia
import pandas as pd
import numpy as np
from pyomo.environ import *
from config import *


# ============================
# Auxiliary functions for LP
# ============================


def initial_network():
    gia.calc_substation_location()
    points_on_line, tranches = gia.connect_building_to_grid()
    points_on_line_processed = gia.process_network(points_on_line)
    dict_length, dict_path = gia.create_length_dict(points_on_line_processed, tranches)
    return points_on_line_processed, tranches, dict_length, dict_path


def get_line_parameters():
    df_line_parameter = pd.read_csv(LOCATOR + '\\electric_line_data.csv')
    return df_line_parameter


def annuity_factor(n, i):
    """calculate annuity factor

    Args:
        n: depreciation period (40 = 40 years)
        i: interest rate (0.06 = 6%)
    Returns:
        annuity factor derived by formula (1+i)**n * i / ((1+i)**n - 1)
    """
    return (1 + i) ** n * i / ((1 + i) ** n - 1)


# ============================
# Objective function for LP
# ============================

def cost_rule(m, cost_type):
    if cost_type == 'investment':
        c_inv = 0.0
        for (i, j) in m.set_edge:
            for t in m.set_linetypes:
                c_inv += 2.0 * (m.var_x[i, j, t]
                              * m.dict_length[i, j]) \
                         * m.dict_line_tech[t]['price_sgd_per_m'] \
                         * m.dict_line_tech[t]['annuity_factor']
        return m.var_costs['investment'] == c_inv
    elif cost_type == 'om':
        # c_om = 0.0
        # for (i, j) in m.set_edge:
        #     for t in m.set_linetypes:
        #         c_om += 2 * (m.var_x[i, j, t] * m.dict_length[i, j])\
        #                 * m.dict_line_tech[t]['c_invest'] * m.dict_line_tech[t]['annuity_factor']\
        #                 * m.dict_line_tech[t]['om_factor']

        # each om factor is the same
        return m.var_costs['om'] == m.var_costs['investment'] * m.dict_line_tech[0]['om_factor']  # TODO Differentiation of types
    elif cost_type == 'losses':
        c_losses = 0.0
        for (i, j) in m.set_edge:
            for t in m.set_linetypes:
                c_losses += (m.var_power_over_line[i, j, t] * I_BASE) ** 2 \
                            * m.dict_length[i, j] * (m.dict_line_tech[t]['r_ohm_per_km'] / 1000.0) \
                            * APPROX_LOSS_HOURS \
                            * (ELECTRICITY_COST * (10**(-3)))

        return m.var_costs['losses'] == c_losses
    else:
        raise NotImplementedError("Unknown cost type!")


def obj_rule(m):
    return sum(m.var_costs[cost_type] for cost_type in m.set_cost_type)


# ============================
# Constraint rules
# ============================


def power_balance_rule(m, i):
    p_node_out = float(m.dict_power_demand[i])
    p_node_in = 0.0

    if i in m.set_nodes_sub:
        p_node_in += m.var_power_sub[i]

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
    power_over_line = ((
                        ((m.var_theta[i] - m.var_theta[j])*np.pi/180)  # rad to degree
                        / (m.dict_length[i, j] * m.dict_line_tech[t]['x_ohm_per_km'] / 1000)
                        )
                       + m.var_slack[i, j, t])
    return m.var_power_over_line[i, j, t] == power_over_line


def slack_voltage_angle_rule(m, i):
    return m.var_theta[i] == 0.0   # Voltage angle of slack has to be zero


def slack_pos_rule(m, i, j, t):
    return (m.var_slack[i, j, t]) <= (1 - m.var_x[i, j, t]) * 1000000


def slack_neg_rule(m, i, j, t):
    return (m.var_slack[i, j, t]) >= (-1) * (1 - m.var_x[i, j, t]) * 1000000


def power_over_line_rule_pos_rule(m, i, j, t):
    power_line_limit = m.var_x[i, j, t]\
                       * (m.dict_line_tech[t]['I_max_A'] * V_BASE*10**3) \
                       / (S_BASE*10**6)
    return m.var_power_over_line[i, j, t] <= power_line_limit


def power_over_line_rule_neg_rule(m, i, j, t):
    power_line_limit = (-1) * m.var_x[i, j, t]\
                       * (m.dict_line_tech[t]['I_max_A'] * V_BASE*10**3) \
                       / (S_BASE*10**6)
    return m.var_power_over_line[i, j, t] >= power_line_limit


def radial_rule(m):
    return summation(m.var_x) == (len(m.set_nodes) - len(m.set_nodes_sub))


def one_linetype_rule(m, i, j):
    number_of_linetypes = 0
    for t in m.set_linetypes:
        number_of_linetypes += m.var_x[i, j, t]
    return number_of_linetypes <= 1


def main():
    # ===========================================
    # Initialize Data
    # ===========================================

    # Street network and Buildings
    points_on_line, tranches, dict_length, dict_path = initial_network()
    df_nodes = pd.DataFrame(points_on_line).drop(['geometry', 'Building', 'Name'], axis=1)
    del tranches, points_on_line

    # Line Parameters
    df_line_parameter = get_line_parameters()
    dict_line_tech_params = dict(df_line_parameter.T)  # dict transposed dataframe

    # annuity factor (years, interest)
    for idx_line in dict_line_tech_params:
        dict_line_tech_params[idx_line]['annuity_factor'] = annuity_factor(40, INTEREST_RATE)

    # Cost types
    cost_types = [
        'investment',  # investment costs
        'om',  # operation and maintenance cost
        # 'losses',  # cost for power losses in lines
        ]

    # ============================
    # Index data
    # ============================

    idx_nodes_sub = df_nodes[df_nodes['Type'] == 'PLANT'].index
    idx_nodes_consum = df_nodes[df_nodes['Type'] == 'CONSUMER'].index
    idx_nodes = idx_nodes_sub.append(idx_nodes_consum)

    # Diagonal edge index matrix
    idx_edge = []
    for i in idx_nodes:
        for j in idx_nodes:
            if i != j and i < j:
                idx_edge.append((i, j))

    idx_linetypes = range(len(dict_line_tech_params))

    # ============================
    # Preprocess data
    # ============================

    dict_power_demand = {}
    for idx_node, node in df_nodes.iterrows():
        if not np.isnan(node['GRID0_kW']):
            dict_power_demand[idx_node] = (node['GRID0_kW']*10**3) \
                                          / (S_BASE*10**6)  # kW / MW


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

    # Create Parameters
    m.dict_length = dict_length_processed.copy()
    m.dict_line_tech = dict_line_tech_params.copy()
    m.dict_power_demand = dict_power_demand.copy()

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

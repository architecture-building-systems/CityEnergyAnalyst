from __future__ import division
import time
import get_initial_network as gia
import pandas as pd
import numpy as np
from pyomo.environ import *
from lp_op_config import *
import concept.algorithm_operation.main_thermal_operations as main_thermal_operations

# Import constraints for operation problem
from concept.algorithm_operation.optimisation_district import (
    initial_state_condition_constraint_rule,
    minimal_maximal_output_constraint_rule,
    setback_controls_constraint_rule,
    state_space_equation_output_constraint_rule,
    state_space_equation_state_constraint_rule,
    temperatures_absolute_value_constraint_rule,
    maximal_emission_capacity_rule
)

'''
========================================================
# Auxiliary functions for LP
========================================================
'''

def initial_network():
    gia.calc_substation_location()
    points_on_line, tranches = gia.connect_building_to_grid()
    points_on_line_processed = gia.process_network(points_on_line)
    hourly_demand_per_building = gia.get_hourly_power_demand_per_building(points_on_line_processed)
    dict_length, dict_path = gia.create_length_dict(points_on_line_processed, tranches)
    return points_on_line_processed, tranches, dict_length, dict_path, hourly_demand_per_building


def get_line_parameters():
    df_line_parameter = pd.read_csv(LOCATOR + '/electric_line_data.csv')
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


'''
========================================================
# Objective function for LP
========================================================
'''


def obj_rule(m):
    return sum(m.var_costs[cost_type] for cost_type in m.set_cost_type)


def cost_rule(m, cost_type):
    if cost_type == 'investment_line':
        c_inv = 0.0
        for (i, j) in m.set_edge:
            for k in m.set_linetypes:
                c_inv += (
                        3.0  # three phases
                        * 2.0  # earthworks + cable costs
                        * (m.var_x[i, j, k] * m.dict_length[i, j])
                        * m.dict_line_tech[k]['price_sgd_per_m']
                        * m.dict_line_tech[k]['annuity_factor']
                )
        return m.var_costs['investment_line'] == c_inv
    elif cost_type == 'investment_sub':
        c_inv = 0.0
        for i in m.set_nodes_sub:
            c_inv += (
                    m.var_power_sub_max[i] / (10**3)  # in kW
                    / POWER_FACTOR
                    * m.dict_line_tech[0]['sub_price_sgd_per_kva']
                    * m.dict_line_tech[0]['annuity_factor']
            )
        return m.var_costs['investment_sub'] == c_inv
    elif cost_type == 'investment_build':
        c_inv = 0.0
        for building in m.buildings_names:
            c_inv += (
                    m.var_power_build_max[building] / (10**3)  # in kW
                    / POWER_FACTOR
                    * m.dict_line_tech[0]['build_price_sgd_per_kva']
                    * m.dict_line_tech[0]['annuity_factor']
            )
        return m.var_costs['investment_build'] == c_inv
    elif cost_type == 'om':
        return m.var_costs['om'] == (
                m.var_costs['investment_line']
                + m.var_costs['investment_sub']
                + m.var_costs['investment_build']
        ) * m.dict_line_tech[0]['om_factor']
    elif cost_type == 'losses':
        c_losses = 0.0
        for (i, j) in m.set_edge:
            for k in m.set_linetypes:
                c_losses += (
                        (m.var_power_over_line[i, j, k] ** 2)
                        * m.dict_length[i, j] * (m.dict_line_tech[k]['r_ohm_per_km'] / 1000.0)
                        * APPROX_LOSS_HOURS
                        * (m.price_vector['PRICE ($/MWh)'].mean() * (10 ** (-6)))
                )
        return m.var_costs['losses'] == c_losses
    elif cost_type == 'electricity_price':
        # Operation: Objective function part related to the price-based flexibility
        obj_price = 0
        for time in m.date_and_time_prediction:
            power_t = 0
            for building in m.buildings_names:
                for output in m.buildings_dic[building].i_outputs.index:
                    if '_electric_power' in str(output):
                        power_t += m.outputs_variable[building, output, time]
            # Convert prices from $/MWh to $/Wh
            obj_price += m.price_vector.loc[time]['PRICE ($/MWh)'] * power_t * (10 ** (-6))
        return m.var_costs['electricity_price'] == ALPHA * obj_price
    elif cost_type == 'set_temperature':
        # Operation: Objective function part related to the set outputs
        obj_set = 0
        for time in m.date_and_time_prediction:
            for building in m.buildings_names:
                for output in m.buildings_dic[building].i_outputs.index:
                    if '_temperature' in str(output):
                        obj_set += (
                            m.output_delta_plus[building, output, time]
                            + m.output_delta_minus[building, output, time]
                        )
        return m.var_costs['set_temperature'] == BETA * obj_set
    else:
        raise NotImplementedError("Unknown cost type!")


'''
# ========================================================
# Constraint rules
# ========================================================
'''
# =========================================== Electric Constraints ===========================================


def power_balance_rule(m, i):
    power_node_out = m.var_power_build_max[m.buildings_names[i]]
    power_node_in = 0.0

    if i in m.set_nodes_sub:
        power_node_in += m.var_power_sub_max[i]

    for j in m.set_nodes:
        if i != j and i < j:
            for k in m.set_linetypes:
                power_node_in += m.var_power_over_line[i, j, k]

    for j in m.set_nodes:
        if i != j and i > j:
            for k in m.set_linetypes:
                power_node_in -= m.var_power_over_line[j, i, k]

    return power_node_out == power_node_in


def power_over_line_rule(m, i, j, k):
    power_over_line = (
            (
                (VOLTAGE_NOMINAL ** 2)
                * ((m.var_theta[i] - m.var_theta[j]) * np.pi / 180)
                / (m.dict_length[i, j] * m.dict_line_tech[k]['x_ohm_per_km'] / 1000)
            )
            + m.var_slack[i, j, k]
    )
    return m.var_power_over_line[i, j, k] == power_over_line


def sub_voltage_angle_rule(m, i):
    return m.var_theta[i] == 0.0  # Voltage angle at substation is zero


def slack_pos_rule(m, i, j, k):
    return (m.var_slack[i, j, k]) <= (1 - m.var_x[i, j, k]) * (10 ** 12)  # Large constant


def slack_neg_rule(m, i, j, k):
    return (m.var_slack[i, j, k]) >= (-1) * (1 - m.var_x[i, j, k]) * (10 ** 12)  # Large constant


def building_max_rule(m, i, t):
    return (m.var_per_building_electric_load[i, t]) <= (m.var_power_build_max[i])


def power_over_line_rule_pos_rule(m, i, j, k):
    power_line_limit = (
            m.var_x[i, j, k]
            * (m.dict_line_tech[k]['I_max_A'] * VOLTAGE_NOMINAL)
            * (3 ** 0.5)
    )
    return m.var_power_over_line[i, j, k] <= power_line_limit


def power_over_line_rule_neg_rule(m, i, j, k):
    power_line_limit = (
            (-1)
            * m.var_x[i, j, k]
            * (m.dict_line_tech[k]['I_max_A'] * VOLTAGE_NOMINAL)
            * (3 ** 0.5)
    )
    return m.var_power_over_line[i, j, k] >= power_line_limit


def radial_rule(m):
    return summation(m.var_x) == (len(m.set_nodes) - len(m.set_nodes_sub))


def one_linetype_rule(m, i, j):
    number_of_linetypes = 0
    for k in m.set_linetypes:
        number_of_linetypes += m.var_x[i, j, k]
    return number_of_linetypes <= 1


# =========================================== Operation Constraints ===========================================

# Most constraints are imported from main_thermal_operations

def total_electric_load_per_building_rule(m, building, time):
    # Rule to get the sum of electric loads for each building and each time step
    return m.var_per_building_electric_load[building, time] == (
            LOAD_FACTOR *
            (
                sum([
                    m.outputs_variable[building, output, time]
                    for output in m.buildings_dic[building].i_outputs.index if '_electric_power' in str(output)
                ])
                + m.dict_hourly_power_demand[building][time] * (10 ** 3)  # kW in W
            )
    )

def main():
    # ===========================================
    # Initialize Data
    # ===========================================
    (
        results_path,
        alpha,
        beta,
        prediction_horizon,
        date_and_time_prediction,
        date_and_time_prediction_plus_1,
        time_step,
        buildings_dic,
        buildings_names,
        buildings_cardinal,
        states_index,
        controls_index,
        outputs_index,
        temperatures_index,
        cool_index,
        heating_boolean,
        cooling_boolean,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        set_temperatures_dic,
        initial_state_dic,
        minimum_output_dic,
        maximum_output_dic,
        em_efficiency_mean_dic,
        Qcsmax_Wm2_dic,
        gross_floor_area_m2,
        price_vector,
        electricity_prices_MWh,
        T_int_cea_dic,
        thermal_room_load_cea_dic,
        thermal_between_generation_emission_cea_dic
    ) = main_thermal_operations.get_optimisation_inputs()

    # Street network and Buildings
    points_on_line, tranches, dict_length, dict_path, hourly_demand_per_building = initial_network()
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
        'investment_line',  # investment costs lines
        'investment_sub',  # investment costs substaton
        'investment_build',  # investment costs building transformer
        'om',  # operation and maintenance cost
        'losses',  # cost for power losses in lines
        'electricity_price',  # Objective function part related to the price-based flexibility
        'set_temperature',  # related to the set outputs
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

    dict_hourly_power_demand = {}
    for building in hourly_demand_per_building:
        dict_hourly_power_demand[building] = {}
        for time in date_and_time_prediction:
            df = hourly_demand_per_building[building][hourly_demand_per_building[building].DATE == str(time)]
            dict_hourly_power_demand[building][time] = float(
                    df['Eal_kWh']
                    + df['Edata_kWh']
                    + df['Epro_kWh']
                    + df['Eaux_kWh']
                    + df['E_ww_kWh']
            )

    # dict_power_demand = {}
    # for idx_node, node in df_nodes.iterrows():
    #     if not np.isnan(node['GRID0_kW']):
    #         dict_power_demand[idx_node] = node['GRID0_kW']

    dict_length_processed = {}
    for idx_node1, node1 in dict_length.iteritems():
        for idx_node2, length in node1.iteritems():
            dict_length_processed[idx_node1, idx_node2] = length

    # ============================
    # Model Problem
    # ============================

    m = ConcreteModel()
    m.name = 'CONCEPT - Optimizing electrical network and operation'

    '''Create Sets'''
    # Planning:
    m.set_nodes = Set(initialize=idx_nodes)
    m.set_nodes_sub = Set(initialize=idx_nodes_sub)
    m.set_nodes_consum = Set(initialize=idx_nodes_consum)
    m.set_edge = Set(initialize=idx_edge)
    m.set_linetypes = Set(initialize=idx_linetypes)
    m.set_cost_type = Set(initialize=cost_types)

    '''Create Parameters'''
    # Planning:
    m.dict_length = dict_length_processed.copy()
    m.dict_line_tech = dict_line_tech_params.copy()

    # Operation:
    m.results_path = results_path
    m.alpha = alpha
    m.beta = beta
    m.prediction_horizon = prediction_horizon
    m.date_and_time_prediction = date_and_time_prediction
    m.date_and_time_prediction_plus_1 = date_and_time_prediction_plus_1
    m.time_step = time_step
    m.buildings_dic = buildings_dic
    m.buildings_names = buildings_names
    m.buildings_cardinal = buildings_cardinal
    m.states_index = states_index
    m.controls_index = controls_index
    m.outputs_index = outputs_index
    m.temperatures_index = temperatures_index
    m.cool_index = cool_index
    m.initial_state_dic = initial_state_dic
    m.heating_boolean = heating_boolean
    m.cooling_boolean = cooling_boolean
    m.occupancy_per_building_cardinal = occupancy_per_building_cardinal
    m.occupancy_per_building_list = occupancy_per_building_list
    m.set_temperatures_dic = set_temperatures_dic
    m.minimum_output_dic = minimum_output_dic
    m.maximum_output_dic = maximum_output_dic
    m.em_efficiency_mean_dic = em_efficiency_mean_dic
    m.Qcsmax_Wm2_dic = Qcsmax_Wm2_dic
    m.gross_floor_area_m2 = gross_floor_area_m2
    m.price_vector = price_vector
    m.T_int_cea_dic = T_int_cea_dic
    m.thermal_room_load_cea_dic = thermal_room_load_cea_dic
    m.thermal_between_generation_emission_cea_dic = thermal_between_generation_emission_cea_dic

    # Planning - Operation connection:
    m.dict_hourly_power_demand = dict_hourly_power_demand.copy()
    
    '''Create variables'''
    # Planning:
    m.var_x = Var(
        m.set_edge,
        m.set_linetypes,
        within=Binary
    )  # decision variable for lines
    m.var_theta = Var(
        m.set_nodes,
        within=Reals,
        bounds=(-30.0, 30.0)
    )  # in degree
    m.var_power_sub_max = Var(
        m.set_nodes_sub,
        within=NonNegativeReals
    )
    m.var_power_build_max = Var(
        m.buildings_names,
        within=NonNegativeReals
    )
    m.var_power_over_line = Var(
        m.set_edge,
        m.set_linetypes,
        within=Reals
    )
    m.var_slack = Var(
        m.set_edge,
        m.set_linetypes,
        within=Reals
    )
    m.var_costs = Var(
        m.set_cost_type,
        within=Reals
    )

    # Operation:
    m.states_variable = Var(
        m.buildings_names,
        m.states_index,
        m.date_and_time_prediction_plus_1
    )
    m.controls_variable = Var(
        m.buildings_names,
        m.controls_index,
        m.date_and_time_prediction,
        bounds=(0.0, None)
    )
    m.outputs_variable = Var(
        m.buildings_names,
        m.outputs_index,
        m.date_and_time_prediction
    )

    # Operation: Variables that are useful for absolute values expressions
    m.output_delta_plus = Var(
        m.buildings_names,
        m.temperatures_index,
        m.date_and_time_prediction,
        bounds=(0.0, None)
    )
    m.output_delta_minus = Var(
        m.buildings_names,
        m.temperatures_index,
        m.date_and_time_prediction,
        bounds=(0.0, None)
    )

    # Planning - Operation connection variable
    m.var_per_building_electric_load = Var(
        m.buildings_names,
        m.date_and_time_prediction
    )

    '''Declare constraint functions'''
    # Planning:
    m.power_balance_rule_constraint = Constraint(
        m.set_nodes,
        rule=power_balance_rule
    )
    m.power_over_line_constraint = Constraint(
        m.set_edge,
        m.set_linetypes,
        rule=power_over_line_rule
    )
    m.sub_voltage_angle_constraint = Constraint(
        m.set_nodes_sub,
        rule=sub_voltage_angle_rule
    )
    m.slack_neg_constraint = Constraint(
        m.set_edge,
        m.set_linetypes,
        rule=slack_neg_rule
    )
    m.slack_pos_constraint = Constraint(
        m.set_edge,
        m.set_linetypes,
        rule=slack_pos_rule
    )
    m.building_max_constraint = Constraint(
        m.buildings_names,
        m.date_and_time_prediction,
        rule=building_max_rule
    )
    m.power_over_line_rule_neg_constraint = Constraint(
        m.set_edge,
        m.set_linetypes,
        rule=power_over_line_rule_neg_rule
    )
    m.power_over_line_rule_pos_constraint = Constraint(
        m.set_edge,
        m.set_linetypes,
        rule=power_over_line_rule_pos_rule
    )

    m.radial_constraint = Constraint(
        rule=radial_rule
    )
    m.one_linetype = Constraint(
        m.set_edge,
        rule=one_linetype_rule
    )

    # Create equality constraints
    m.state_space_equation_state_constraint = Constraint(
        m.buildings_names,
        m.states_index,
        m.date_and_time_prediction,
        rule=state_space_equation_state_constraint_rule
    )
    m.state_space_equation_output_constraint = Constraint(
        m.buildings_names,
        m.outputs_index,
        m.date_and_time_prediction,
        rule=state_space_equation_output_constraint_rule
    )
    m.initial_state_condition_constraint = Constraint(
        m.buildings_names,
        m.states_index,
        rule=initial_state_condition_constraint_rule
    )
    m.setback_controls_constraint = Constraint(
        m.buildings_names,
        m.outputs_index,
        m.date_and_time_prediction,
        rule=setback_controls_constraint_rule
    )

    # Create absolute values constraints
    m.temperatures_absolute_value_constraint = Constraint(
        m.buildings_names,
        m.temperatures_index,
        m.date_and_time_prediction,
        rule=temperatures_absolute_value_constraint_rule
    )

    # Create inequality constraints
    m.minimal_maximal_output_constraint = Constraint(
        m.buildings_names,
        m.outputs_index,
        m.date_and_time_prediction,
        rule=minimal_maximal_output_constraint_rule
    )

    # TODO: Include this maximal_emission_capacity_constraint
    # m.maximal_emission_capacity_constraint = Constraint(
    #     m.buildings_names,
    #     m.date_and_time_prediction,
    #     rule=maximal_emission_capacity_rule
    # )

    # Planning - Operation connection
    m.total_electric_load_per_building_constraint = Constraint(
        m.buildings_names,
        m.date_and_time_prediction,
        rule=total_electric_load_per_building_rule
    )

    '''Declare objective function'''
    m.def_costs = Constraint(
        m.set_cost_type,
        rule=cost_rule
    )
    m.obj = Objective(
        sense=minimize,
        rule=obj_rule
    )

    return m


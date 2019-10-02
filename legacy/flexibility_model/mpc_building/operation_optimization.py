from __future__ import division
from pyomo.environ import *

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def main(
        alpha,
        beta,
        date_and_time_prediction,
        date_and_time_prediction_plus_1,
        time_step,
        buildings_dic,
        buildings_names,
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
        price_vector
):

    # Initialize the model
    m = ConcreteModel()

    # Get parameters
    m.alpha = alpha
    m.beta = beta
    m.date_and_time_prediction = date_and_time_prediction
    m.date_and_time_prediction_plus_1 = date_and_time_prediction_plus_1
    m.time_step = time_step
    m.buildings_dic = buildings_dic
    m.buildings_names = buildings_names
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

    # Initialize variables
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

    # Initialize variables that are useful for absolute values expressions
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

    # Create objective function
    m.objective_function = Objective(
        rule=objective_function_full,
        sense=minimize
    )

    return m


def state_space_equation_state_constraint_rule(m, building, state, time):
    # Rule for the constraint reflecting the state part of the state space equation
    if state in m.buildings_dic[building].index_states:
        states_factor = sum(
            m.buildings_dic[building].state_matrix.loc[state][other_state]
            * m.states_variable[building, other_state, time]
            for other_state in m.buildings_dic[building].index_states
        )
        controls_factors = sum(
            m.buildings_dic[building].control_matrix.loc[state][control]
            * m.controls_variable[building, control, time]
            for control in m.buildings_dic[building].index_controls
        )
        disturbances_factor = sum(
            m.buildings_dic[building].disturbance_matrix.loc[state][disturbance]
            * m.buildings_dic[building].disturbance_timeseries.loc[disturbance][time]
            for disturbance in m.buildings_dic[building].index_disturbances
        )
        return (
            m.states_variable[building, state, time + m.time_step]
            == states_factor + controls_factors + disturbances_factor
        )
    else:
        return Constraint.Skip


def state_space_equation_output_constraint_rule(m, building, output, time):
    # Rule for the constraint reflecting the output part of the state space equation
    if output in m.buildings_dic[building].index_outputs:
        states_factor = sum(
            m.buildings_dic[building].state_output_matrix.loc[output][state]
            * m.states_variable[building, state, time]
            for state in m.buildings_dic[building].index_states
        )
        controls_factors = sum(
            m.buildings_dic[building].control_output_matrix.loc[output, control]
            * m.controls_variable[building, control, time]
            for control in m.buildings_dic[building].index_controls
        )
        disturbances_factor = sum(
            m.buildings_dic[building].disturbance_output_matrix.loc[output][disturbance]
            * m.buildings_dic[building].disturbance_timeseries.loc[disturbance][time]
            for disturbance in m.buildings_dic[building].index_disturbances
        )
        return (
            m.outputs_variable[building, output, time]
            == states_factor + controls_factors + disturbances_factor
        )
    else:
        return Constraint.Skip


def initial_state_condition_constraint_rule(m, building, state):
    # Rule for initial condition on state
    if state in m.buildings_dic[building].index_states:
        return (
            m.states_variable[building, state, m.date_and_time_prediction[0]]
            == m.initial_state_dic[building][state]
        )
    else:
        return Constraint.Skip


def setback_controls_constraint_rule(m, building, output, time):
    # Rule to forbid heating during cooling season, and cooling during heating season
    if output in m.buildings_dic[building].index_outputs:
        if m.heating_boolean[time] == 1:
            if 'cool' in str(output):
                return m.outputs_variable[building, output, time] == 0
            else:
                return Constraint.Skip
        elif m.cooling_boolean[time] == 1:
            if 'heat' in str(output):
                return m.outputs_variable[building, output, time] == 0
            else:
                return Constraint.Skip
        else:
            return Constraint.Skip
    else:
        return Constraint.Skip


def temperatures_absolute_value_constraint_rule(m, building, temperature, time):
    # Rule to get the absolute value of the difference between the set temperatures and the actual temperatures
    if temperature in m.buildings_dic[building].index_outputs:
        for occupancy in m.occupancy_per_building_list[building]:
            if occupancy in str(temperature):
                return (
                    (
                            m.outputs_variable[building, temperature, time]
                            - m.set_temperatures_dic[building].loc[occupancy][time]
                    )
                    == (
                            m.output_delta_plus[building, temperature, time]
                            - m.output_delta_minus[building, temperature, time]
                    )
                )
    else:
        return Constraint.Skip


def minimal_maximal_output_constraint_rule(m, building, output, time):
    # Rule for minimal and maximal accepted values of outputs
    if output in m.buildings_dic[building].index_outputs:
        return (
            m.minimum_output_dic[building].loc[output][time],
            m.outputs_variable[building, output, time],
            m.maximum_output_dic[building].loc[output][time]
        )
    else:
        return Constraint.Skip

def maximal_emission_capacity_rule(m, building, time):
    # Rule to ensure the emission capacity is not exceeded
    return sum(m.controls_variable[building, cooling, time] for cooling in m.cool_index[building]) \
           <= m.em_efficiency_mean_dic[building] * m.Qcsmax_Wm2_dic[building] * m.gross_floor_area_m2[building]


def objective_function_electricity_price(m):
    # Objective function part related to the electricity cost
    obj_price = 0
    for time in m.date_and_time_prediction:
        power_t = 0
        for building in m.buildings_names:
            for output in m.buildings_dic[building].index_outputs:
                if '_electric_power' in str(output):
                    power_t += m.outputs_variable[building, output, time]
        # Convert prices from $/MWh to $/Wh
        obj_price += m.price_vector.loc[time]['PRICE ($/MWh)'] * power_t * (10 ** (-6))
    return obj_price


def objective_function_set_temperature(m):
    # Objective function part related to the distance to the set outputs
    obj_set = 0
    for time in m.date_and_time_prediction:
        for building in m.buildings_names:
            for output in m.buildings_dic[building].index_outputs:
                if '_temperature' in str(output):
                    obj_set += m.output_delta_plus[building, output, time] + m.output_delta_minus[
                        building, output, time]
    return obj_set


def objective_function_full(m):
    obj_price = objective_function_electricity_price(m)
    obj_set = objective_function_set_temperature(m)
    obj_full = m.alpha * obj_price + m.beta * obj_set
    return obj_full

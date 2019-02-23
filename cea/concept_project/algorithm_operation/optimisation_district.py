from __future__ import division
from pyomo.environ import *
from pyomo.opt import SolverFactory
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def main_optimisation_district(
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
):

    m = optimisation_solving(
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
        T_int_cea_dic,
        thermal_room_load_cea_dic,
        thermal_between_generation_emission_cea_dic
    )
    electricity_cost = electricity_cost_calculation(m, electricity_prices_MWh)
    m = save_results(m)
    m = aggregate_results(m)
    # TODO
    # comparisons_with_cea(m)
    # plot_results(m)

    return m


def optimisation_solving(
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
        T_int_cea_dic,
        thermal_room_load_cea_dic,
        thermal_between_generation_emission_cea_dic
):

    # Initialize the model
    m = ConcreteModel()

    # Get parameters
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

    # Optimisation problem solving
    opt = SolverFactory('gurobi')  # Create a solver
    # opt = SolverFactory('cplex')  # Create a solver
    results = opt.solve(m)  # Solve the optimization problem
    # m.display()  # Display the results

    return m


def electricity_cost_calculation(m, electricity_prices_MWh):
    # Cost calculations, using the actual electricity prices
    electricity_cost = 0
    for time in m.date_and_time_prediction:
        power_t = 0
        for building in m.buildings_names:
            for output in m.buildings_dic[building].i_outputs.index:
                if '_electric_power' in str(output):
                    power_t += m.outputs_variable[building, output, time].value

        # Convert prices from $/MWh to $/Wh
        electricity_cost += electricity_prices_MWh.loc[time]['PRICE ($/MWh)'] * power_t * (10 ** (-6))

    print('electricity_cost=')
    print(electricity_cost)

    return electricity_cost


def save_results(m):
    # Save results in CSV files and return them
    m.outputs_dic = {}
    m.controls_dic = {}
    m.states_dic = {}
    for building in m.buildings_names:
        outputs_build = pd.DataFrame(
            np.zeros((m.prediction_horizon, m.buildings_dic[building].n_outputs)),
            m.date_and_time_prediction,
            m.buildings_dic[building].i_outputs.index
        )
        for time in m.date_and_time_prediction:
            for output in m.buildings_dic[building].i_outputs.index:
                outputs_build.loc[time, output] = m.outputs_variable[building, output, time].value
        m.outputs_dic[building] = outputs_build
        outputs_build.to_csv(m.results_path + '/outputs_' + building + '.csv')

        controls_build = pd.DataFrame(
            np.zeros((m.prediction_horizon, m.buildings_dic[building].n_controls)),
            m.date_and_time_prediction,
            m.buildings_dic[building].i_controls.index
        )
        for time in m.date_and_time_prediction:
            for control in m.buildings_dic[building].i_controls.index:
                controls_build.loc[time, control] = m.controls_variable[building, control, time].value
        m.controls_dic[building] = controls_build
        controls_build.to_csv(m.results_path + '/controls_' + building + '.csv')

        states_build = pd.DataFrame(
            np.zeros((m.prediction_horizon + 1, m.buildings_dic[building].n_states)),
            m.date_and_time_prediction_plus_1,
            m.buildings_dic[building].i_states.index
        )
        for time in m.date_and_time_prediction_plus_1:
            for state in m.buildings_dic[building].i_states.index:
                states_build.loc[time, state] = m.states_variable[building, state, time].value
        m.states_dic[building] = states_build
        states_build.to_csv(m.results_path + '/states_' + building + '.csv')

        m.minimum_output_dic[building].to_csv(m.results_path + '/outputs_minimum_' + building + '.csv')
        m.maximum_output_dic[building].to_csv(m.results_path + '/outputs_maximum_' + building + '.csv')

    return m


def aggregate_results(m):
    # Aggregating the temperatures and loads of all the buildings

    # Temperatures
    mean_predicted_temperature_df = pd.DataFrame(
        np.zeros((m.prediction_horizon, m.buildings_cardinal)),
        m.date_and_time_prediction,
        m.buildings_names
    )
    mean_set_temperature_df = pd.DataFrame(
        np.zeros((m.prediction_horizon, m.buildings_cardinal)),
        m.date_and_time_prediction,
        m.buildings_names
    )
    mean_minimal_temperature_df = pd.DataFrame(
        np.zeros((m.prediction_horizon, m.buildings_cardinal)),
        m.date_and_time_prediction,
        m.buildings_names
    )
    mean_maximal_temperature_df = pd.DataFrame(
        np.zeros((m.prediction_horizon, m.buildings_cardinal)),
        m.date_and_time_prediction,
        m.buildings_names
    )
    mean_cea_temperature_df = pd.DataFrame(
        np.zeros((m.prediction_horizon, m.buildings_cardinal)),
        m.date_and_time_prediction,
        m.buildings_names
    )
    for building in m.buildings_names:
        for time in m.date_and_time_prediction:
            predicted_temperature_build_t = 0
            set_temperature_build_t = 0
            minimal_temperature_build_t = 0
            maximal_temperature_build_t = 0
            for occupancy in m.occupancy_per_building_list[building]:
                predicted_temperature_build_t += m.outputs_dic[building].loc[time][occupancy + '_temperature']
                set_temperature_build_t += m.set_temperatures_dic[building].loc[occupancy][time]
                minimal_temperature_build_t += m.minimum_output_dic[building].loc[occupancy + '_temperature'][time]
                maximal_temperature_build_t += m.maximum_output_dic[building].loc[occupancy + '_temperature'][time]

            mean_predicted_temperature_df.loc[time][building] = (
                    predicted_temperature_build_t
                    / int(m.occupancy_per_building_cardinal[building])
            )
            mean_set_temperature_df.loc[time][building] = (
                    set_temperature_build_t
                    / int(m.occupancy_per_building_cardinal[building])
            )
            mean_minimal_temperature_df.loc[time][building] = (
                    minimal_temperature_build_t
                    / int(m.occupancy_per_building_cardinal[building])
            )
            mean_maximal_temperature_df.loc[time][building] = (
                    maximal_temperature_build_t
                    / int(m.occupancy_per_building_cardinal[building])
            )
            mean_cea_temperature_df.loc[time][building] = m.T_int_cea_dic[building][time]

    mean_predicted_temperature_df = mean_predicted_temperature_df.mean(axis=0, skipna=False)
    mean_set_temperature_df = mean_set_temperature_df.mean(axis=0, skipna=False)
    mean_minimal_temperature_df = mean_minimal_temperature_df.mean(axis=0, skipna=False)
    mean_maximal_temperature_df = mean_maximal_temperature_df.mean(axis=0, skipna=False)
    mean_cea_temperature_df = mean_cea_temperature_df.mean(axis=0, skipna=False)

    m.mean_predicted_temperature_df = mean_predicted_temperature_df
    m.mean_set_temperature_df = mean_set_temperature_df
    m.mean_minimal_temperature_df = mean_minimal_temperature_df
    m.mean_maximal_temperature_df = mean_maximal_temperature_df
    m.mean_cea_temperature_df = mean_cea_temperature_df

    mean_predicted_temperature_df.to_csv(m.results_path + '/mean_predicted_temperature.csv')
    mean_set_temperature_df.to_csv(m.results_path + '/mean_set_temperature.csv')
    mean_minimal_temperature_df.to_csv(m.results_path + '/mean_minimal_temperature.csv')
    mean_maximal_temperature_df.to_csv(m.results_path + '/mean_maximal_temperature.csv')
    mean_cea_temperature_df.to_csv(m.results_path + '/mean_cea_temperature.csv')

    # Thermal room loads
    m.aggregated_sum_thermal_powers_df = pd.DataFrame(
        np.zeros((m.prediction_horizon, m.buildings_cardinal)),
        m.date_and_time_prediction,
        m.buildings_names
    )
    for building in m.buildings_names:
        sum_thermal_powers = m.controls_dic[building].sum(axis=1)
        m.aggregated_sum_thermal_powers_df[:][building] = sum_thermal_powers
    m.aggregated_sum_thermal_powers_df.sum(axis=1)
    m.aggregated_sum_thermal_powers_df.to_csv(m.results_path + '/aggregated_sum_thermal_powers.csv')

    m.aggregated_sum_cea_thermal_powers_df = pd.DataFrame(
        np.zeros((m.prediction_horizon, m.buildings_cardinal)),
        m.date_and_time_prediction,
        m.buildings_names
    )
    for building in m.buildings_names:
        m.aggregated_sum_cea_thermal_powers_df[:][building] = m.thermal_room_load_cea_dic[building]
    m.aggregated_sum_cea_thermal_powers_df = np.sum(m.aggregated_sum_cea_thermal_powers_df, axis=1)
    m.aggregated_sum_cea_thermal_powers_df.to_csv(m.results_path + '/aggregated_sum_cea_thermal_powers.csv')

    # Thermal between generation/conversion and emission/distribution loads
    aggregated_sum_between_generation_emission_powers_df = pd.DataFrame(
        np.zeros((m.prediction_horizon, m.buildings_cardinal)),
        m.date_and_time_prediction,
        m.buildings_names
    )
    for building in m.buildings_names:
        sum_between_generation_emission_powers = (
            m.outputs_dic[building].T[['power' in x for x in m.outputs_dic[building].columns]].T.sum(axis=1)  # TODO: this might be wrong
        )
        aggregated_sum_between_generation_emission_powers_df[:][building] = sum_between_generation_emission_powers
    aggregated_sum_between_generation_emission_powers_df = (
        aggregated_sum_between_generation_emission_powers_df.sum(axis=1)
    )
    aggregated_sum_between_generation_emission_powers_df.to_csv(
        m.results_path + '/aggregated_sum_between_generation_emission_powers.csv'
    )

    aggregated_sum_cea_between_generation_emission_powers_df = pd.DataFrame(
        np.zeros((m.prediction_horizon, m.buildings_cardinal)),
        m.date_and_time_prediction,
        m.buildings_names
    )
    for building in m.buildings_names:
        aggregated_sum_cea_between_generation_emission_powers_df[:][building] = (
            m.thermal_between_generation_emission_cea_dic[building]
        )
    aggregated_sum_cea_between_generation_emission_powers_df = (
        aggregated_sum_cea_between_generation_emission_powers_df.sum(axis=1)
    )
    aggregated_sum_cea_between_generation_emission_powers_df.to_csv(
        m.results_path + '/aggregated_sum_cea_between_generation_emission_powers.csv'
    )

    # Electric grid loads
    aggregated_sum_electric_powers_df = pd.DataFrame(
        np.zeros((m.prediction_horizon, m.buildings_cardinal)),
        m.date_and_time_prediction,
        m.buildings_names
    )
    for building in m.buildings_names:
        aggregated_sum_electric_powers_df[:][building] = (
            m.outputs_dic[building].T[['electric_power' in x for x in m.outputs_dic[building].columns]].T.sum(axis=1)
        )
    aggregated_sum_electric_powers_df = (
        aggregated_sum_electric_powers_df.sum(axis=1)
    )
    aggregated_sum_electric_powers_df.to_csv(
        m.results_path + '/aggregated_sum_electric_powers.csv'
    )

    # aggregated_sum_cea_electric_powers_matrix = np.zeros((buildings_cardinal, prediction_horizon))
    # for m in range(buildings_cardinal):
    #     aggregated_sum_cea_electric_powers_matrix[m, :] = electric_grid_load_cea_all[m]
    # aggregated_sum_cea_electric_powers = np.sum(aggregated_sum_cea_electric_powers_matrix, axis=0)
    # np.savetxt('aggregated_sum_cea_electric_powers.csv', aggregated_sum_cea_electric_powers, delimiter=",")

    # Peak load per building
    peak_loads_per_building = []
    for building in m.buildings_names:
        peak_loads_per_building.append(
            max(m.outputs_dic[building].T[['electric_power' in x for x in m.outputs_dic[building].columns]].T.sum(axis=1))
        )
    peak_loads_per_building_df = pd.DataFrame({
        'Name': m.buildings_names,
        'Peak load over a prediction horizon of ' + str(m.prediction_horizon) + ' hours (W)': peak_loads_per_building
    })
    peak_loads_per_building_df.to_csv(
        m.results_path + '/peak_loads_per_building.csv'
    )
    m.peak_loads_per_building_df = peak_loads_per_building_df

    return m

def plot_results(m):
    # Initialize the graph
    plt.figure(1)
    # plt.gcf().subplots_adjust(left=0.3, bottom=0.3, right=0.7, top=0.7, wspace=0, hspace=2)
    plt.gcf().subplots_adjust(hspace=0.5)

    # Plot the energy prices
    plt.subplot(3, 1, 1)
    plt.step(buildings_all[0].time_vector, price_vector, color='g', linewidth=0.75, where='post')
    plt.xlim(buildings_all[0].time_vector[0], buildings_all[0].time_vector[-1])
    plt.xlabel('Time')
    plt.ylabel('Electricity price ($/Wh)')

    # Plot the temperatures
    plt.subplot(3, 1, 2)
    plt.plot(buildings_all[0].time_vector, mean_set_temperature, linewidth=0.75, linestyle='--',
             label='Mean set room temperature on all buildings')
    plt.plot(buildings_all[0].time_vector, mean_predicted_temperature, color='yellowgreen', linewidth=1, linestyle='-',
             label='Mean predicted room temperature on all buildings')
    plt.plot(buildings_all[0].time_vector, mean_min_output, color='r', linewidth=0.75,
             linestyle='-.', label='Minimal temperature')  # Plot minimal value for output
    plt.plot(buildings_all[0].time_vector, mean_max_output, color='r', linewidth=0.75,
             linestyle='-.', label='Maximal temperature')  # Plot maximal value for output
    plt.plot(buildings_all[0].time_vector, mean_cea_temperature, linewidth=1, linestyle=':', color='k',
             label='Mean CEA room temperature on all buildings')
    # plt.plot(buildings_all[0].time_vector, T_ext, linewidth=0.75, linestyle='-', label='CEA ambient temperature')
    ambient_air_temperature = disturbance_timeseries_all[0][ambient_air_temperature_index, :]
    plt.plot(buildings_all[0].time_vector, ambient_air_temperature, color='steelblue', linewidth=0.75, linestyle='-.',
             label='Outdoor air temperature')  # Plot ambient air temperature
    plt.xlim(buildings_all[0].time_vector[0], buildings_all[0].time_vector[-1])
    plt.legend(loc='upper right')
    plt.xlabel('Time')
    plt.ylabel('Temperature (' + u'\N{DEGREE SIGN}' + 'C)')

    # Plot the room thermal loads
    plt.subplot(4, 1, 2)
    plt.step(buildings_all[0].time_vector, aggregated_sum_thermal_powers, linewidth=0.75, where='post',
             label='Aggregated summed up room thermal loads')
    plt.step(buildings_all[0].time_vector, aggregated_sum_cea_thermal_powers, linewidth=0.75, where='post',
             label='Aggregated summed up room thermal load CEA')
    plt.xlim(buildings_all[0].time_vector[0], buildings_all[0].time_vector[-1])
    plt.legend(loc='upper right')
    plt.xlabel('Time')
    plt.ylabel('Thermal Load (W)')

    # Plot the between generation/conversion and distribution/emission thermal loads
    plt.subplot(4, 1, 3)
    plt.step(buildings_all[0].time_vector, aggregated_sum_between_generation_emission_powers, linewidth=0.75,
             where='post',
             label='Aggregated summed up intermediate thermal loads')
    plt.step(buildings_all[0].time_vector, aggregated_sum_cea_between_generation_emission_powers, linewidth=0.75,
             where='post',
             label='Aggregated summed up intermediate thermal loads CEA')
    plt.xlim(buildings_all[0].time_vector[0], buildings_all[0].time_vector[-1])
    plt.legend(loc='upper right')
    plt.xlabel('Time')
    plt.ylabel('Intermediate Load (W)')

    # Plot the electric grid loads
    plt.subplot(3, 1, 3)
    plt.step(buildings_all[0].time_vector, aggregated_sum_electric_powers, linewidth=0.75, where='post',
             label='Aggregated summed up electric grid loads')
    plt.step(buildings_all[0].time_vector, aggregated_sum_cea_electric_powers, linewidth=0.75, where='post',
             label='Aggregated summed up electric grid load CEA')
    plt.xlim(buildings_all[0].time_vector[0], buildings_all[0].time_vector[-1])
    plt.legend(loc='upper right')
    plt.xlabel('Time')
    plt.ylabel('Electric Load (W)')

    m = 9
    # Plot the temperatures
    plt.subplot(3, 1, 2)
    plt.plot(buildings_all[0].time_vector, set_outputs_matrix_all[m][0], linewidth=0.75, linestyle='--',
             label='Mean set room temperature on all buildings')
    plt.plot(buildings_all[0].time_vector, outputs_all[m][0], color='yellowgreen', linewidth=1, linestyle='-',
             label='Mean predicted room temperature on all buildings')
    plt.plot(buildings_all[0].time_vector, min_output_all[m][0], color='r', linewidth=0.75,
             linestyle='-.', label='Minimal temperature')  # Plot minimal value for output
    plt.plot(buildings_all[0].time_vector, max_output_all[m][0], color='r', linewidth=0.75,
             linestyle='-.', label='Maximal temperature')  # Plot maximal value for output
    plt.plot(buildings_all[0].time_vector, T_int_all[m], linewidth=1, linestyle=':', color='k',
             label='Mean CEA room temperature on all buildings')
    # plt.plot(buildings_all[0].time_vector, T_ext, linewidth=0.75, linestyle='-', label='CEA ambient temperature')
    ambient_air_temperature = disturbance_timeseries_all[0][ambient_air_temperature_index, :]
    plt.plot(buildings_all[0].time_vector, ambient_air_temperature, color='steelblue', linewidth=0.75,
             linestyle='-.',
             label='Outdoor air temperature')  # Plot ambient air temperature
    plt.xlim(buildings_all[0].time_vector[0], buildings_all[0].time_vector[-1])
    plt.legend(loc='upper right')
    plt.xlabel('Time')
    plt.ylabel('Temperature (' + u'\N{DEGREE SIGN}' + 'C)')

    # Plot the electric grid loads
    plt.subplot(3, 1, 3)
    plt.step(buildings_all[0].time_vector, aggregated_sum_electric_powers_matrix[m, :], linewidth=0.75,
             where='post',
             label='Aggregated summed up electric grid loads')
    plt.step(buildings_all[0].time_vector, electric_grid_load_cea_all[m], linewidth=0.75, where='post',
             label='Aggregated summed up electric grid load CEA')
    plt.xlim(buildings_all[0].time_vector[0], buildings_all[0].time_vector[-1])
    plt.legend(loc='upper right')
    plt.xlabel('Time')
    plt.ylabel('Electric Load (W)')

    plt.show()


def comparisons_with_cea(m):
    # Comparisons
    difference_thermal_loads = []
    for t in range(prediction_horizon):
        diff_thermal_t = abs(aggregated_sum_thermal_powers[t] - aggregated_sum_cea_thermal_powers[t]) \
                         / abs(aggregated_sum_cea_thermal_powers[t])
        difference_thermal_loads.append(diff_thermal_t)
    comparison_thermal_loads = sum(difference_thermal_loads) / prediction_horizon

    difference_thermal_between_loads = []
    for t in range(prediction_horizon):
        diff_thermal_between_t = abs(aggregated_sum_between_generation_emission_powers[t] -
                                     aggregated_sum_cea_between_generation_emission_powers[t]) \
                                 / abs(aggregated_sum_cea_between_generation_emission_powers[t])
        difference_thermal_between_loads.append(diff_thermal_between_t)
    comparison_thermal_between_loads = sum(difference_thermal_between_loads) / prediction_horizon

    difference_electric_loads = []
    for t in range(prediction_horizon):
        diff_electric_t = abs(aggregated_sum_electric_powers[t] - aggregated_sum_cea_electric_powers[t]) \
                          / abs(aggregated_sum_cea_electric_powers[t])
        difference_electric_loads.append(diff_electric_t)
    comparison_electric_loads = sum(difference_electric_loads) / prediction_horizon

    # print('comparison_thermal_loads =')
    # print(comparison_thermal_loads)
    # print('comparison_thermal_between_loads=')
    # print(comparison_thermal_between_loads)
    # print('comparison_electric_loads=')
    # print(comparison_electric_loads)


def state_space_equation_state_constraint_rule(m, building, state, time):
    # Rule for the constraint reflecting the state part of the state space equation
    if state in m.buildings_dic[building].i_states.index:
        states_factor = sum(
            m.buildings_dic[building].state_matrix.loc[state][other_state]
            * m.states_variable[building, other_state, time]
            for other_state in m.buildings_dic[building].i_states.index
        )
        controls_factors = sum(
            m.buildings_dic[building].control_matrix.loc[state][control]
            * m.controls_variable[building, control, time]
            for control in m.buildings_dic[building].i_controls.index
        )
        disturbances_factor = sum(
            m.buildings_dic[building].disturbance_matrix.loc[state][disturbance]
            * m.buildings_dic[building].disturbance_timeseries.loc[disturbance][time]
            for disturbance in m.buildings_dic[building].i_disturbances.index
        )
        return (
            m.states_variable[building, state, time + m.time_step]
            == states_factor + controls_factors + disturbances_factor
        )
    else:
        return Constraint.Skip


def state_space_equation_output_constraint_rule(m, building, output, time):
    # Rule for the constraint reflecting the output part of the state space equation
    if output in m.buildings_dic[building].i_outputs.index:
        states_factor = sum(
            m.buildings_dic[building].state_output_matrix.loc[output][state]
            * m.states_variable[building, state, time]
            for state in m.buildings_dic[building].i_states.index
        )
        controls_factors = sum(
            m.buildings_dic[building].control_output_matrix.loc[output, control]
            * m.controls_variable[building, control, time]
            for control in m.buildings_dic[building].i_controls.index
        )
        disturbances_factor = sum(
            m.buildings_dic[building].disturbance_output_matrix.loc[output][disturbance]
            * m.buildings_dic[building].disturbance_timeseries.loc[disturbance][time]
            for disturbance in m.buildings_dic[building].i_disturbances.index
        )
        return (
            m.outputs_variable[building, output, time]
            == states_factor + controls_factors + disturbances_factor
        )
    else:
        return Constraint.Skip


def initial_state_condition_constraint_rule(m, building, state):
    # Rule for initial condition on state
    if state in m.buildings_dic[building].i_states.index:
        return (
            m.states_variable[building, state, m.date_and_time_prediction[0]]
            == m.initial_state_dic[building][state]
        )
    else:
        return Constraint.Skip


def setback_controls_constraint_rule(m, building, output, time):
    # Rule to forbid heating during cooling season, and cooling during heating season
    if output in m.buildings_dic[building].i_outputs.index:
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
    if temperature in m.buildings_dic[building].i_outputs.index:
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
    if output in m.buildings_dic[building].i_outputs.index:
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
            for output in m.buildings_dic[building].i_outputs.index:
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
            for output in m.buildings_dic[building].i_outputs.index:
                if '_temperature' in str(output):
                    obj_set += m.output_delta_plus[building, output, time] + m.output_delta_minus[
                        building, output, time]
    return obj_set


def objective_function_full(m):
    obj_price = objective_function_electricity_price(m)
    obj_set = objective_function_set_temperature(m)
    obj_full = m.alpha * obj_price + m.beta * obj_set
    return obj_full

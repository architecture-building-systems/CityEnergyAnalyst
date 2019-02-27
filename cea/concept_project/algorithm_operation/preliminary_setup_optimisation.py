import numpy as np
import pandas as pd
from concept.algorithm_operation.minimal_maximal_outputs import main_minimum_maximum_outputs

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main_preliminary_setup_optimisation(
        case_goal,
        pricing_scheme,
        constant_price,
        min_max_source,
        min_constant_temperature,
        max_constant_temperature,
        prediction_horizon,
        date_and_time_prediction,
        time_start,
        delta_set,
        delta_setback,
        buildings_names,
        buildings_cardinal,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        center_interval_temperatures_dic,
        setback_boolean_dic,
        gross_floor_area_m2,
        indoor_comfort_df,
        occupancy_density_m2_p,
        occupancy_probability_df,
        buildings_dic,
        electricity_prices_MWh,
        set_temperatures_dic
):

    # Define the initial state (to the set temperature)
    initial_state_dic = {}
    for building in buildings_names:
        initial_state_build_dic = {}
        for occupancy in occupancy_per_building_list[building]:
            initial_state_build_dic[occupancy + '_temperature'] = (
                set_temperatures_dic[building].loc[occupancy][time_start]
            )
        initial_state_dic[building] = initial_state_build_dic

    # Electricity price vector ($/MWh)
    if pricing_scheme == 'constant_prices':
        price_vector = pd.DataFrame(
            np.zeros((prediction_horizon, 1)),
            date_and_time_prediction,
            ['PRICE ($/MWh)']
        )
        for time in date_and_time_prediction:
            price_vector.loc[time]['PRICE ($/MWh)'] = constant_price  # Return a constant electricity price
    elif pricing_scheme == 'dynamic_prices':
        price_vector = electricity_prices_MWh
    else:
        print('Error: no valid pricing_scheme is defined.')
        quit()

    # Contributions of the electricity consumption and the distance to the set outputs in the objective function
    if case_goal == 'set_temperature_tracking':
        alpha = 10**(-10)  # This makes the electricity consumption secondary to being as close as possible to the
        # set temperature, but still something that should be minimised when 2 equivalent ways of producing energy
        # are considered
        beta = 1  # Giving more weight to being as close as possible to the set temperature
    elif case_goal == 'price_based_flexibility':
        alpha = 1  # Giving more weight to using as less electricity as possible
        beta = 0
    else:
        print('Error: no valid case_goal is defined.')
        quit()

    # Define the minimal and maximal accepted values for the outputs
    if min_max_source == 'from building.py':
        minimum_output_dic = {}
        maximum_output_dic = {}
        for building in buildings_names:
            minimum_output_dic[building] = buildings_dic[building].output_constraint_timeseries_minimum
            maximum_output_dic[building] = buildings_dic[building].output_constraint_timeseries_maximum
    elif min_max_source == 'from occupancy variations' or min_max_source == 'constants':
        minimum_output_dic, maximum_output_dic = main_minimum_maximum_outputs(
            min_max_source,
            min_constant_temperature,
            max_constant_temperature,
            buildings_names,
            prediction_horizon,
            date_and_time_prediction,
            delta_set,
            delta_setback,
            occupancy_per_building_cardinal,
            occupancy_per_building_list,
            center_interval_temperatures_dic,
            setback_boolean_dic,
            gross_floor_area_m2,
            indoor_comfort_df,
            occupancy_density_m2_p,
            occupancy_probability_df,
            buildings_dic
        )
    else:
        print('Error: no valid min_max_source is defined.')
        quit()

    # Define the indexes used in the optimisation
    states_index_all = buildings_dic[buildings_names[0]].i_states.index.get_values()
    controls_index_all = buildings_dic[buildings_names[0]].i_controls.index.get_values()
    outputs_index_all = buildings_dic[buildings_names[0]].i_outputs.index.get_values()
    for i in range(1, buildings_cardinal):
        states_index_all = np.concatenate(
            (
                states_index_all,
                buildings_dic[buildings_names[i]].i_states.index.get_values()
            ),
            axis=0
        )
        controls_index_all = np.concatenate(
            (
                controls_index_all,
                buildings_dic[buildings_names[i]].i_controls.index.get_values()
            ),
            axis=0
        )
        outputs_index_all = np.concatenate(
            (
                outputs_index_all,
                buildings_dic[buildings_names[i]].i_outputs.index.get_values()
            ),
            axis=0
        )

    states_index = np.unique(states_index_all)
    controls_index = np.unique(controls_index_all)
    outputs_index = np.unique(outputs_index_all)

    temperatures_index = []
    for output in outputs_index:
        if '_temperature' in output:
            temperatures_index.append(output)

    cool_index = {}
    for building in buildings_names:
        cool_index_build = []
        for control in buildings_dic[building].i_controls.index:
            if 'cool' in str(control):
                cool_index_build.append(control)
        cool_index[building] = cool_index_build

    # Return parameters
    return (
        initial_state_dic,
        price_vector,
        alpha,
        beta,
        minimum_output_dic,
        maximum_output_dic,
        states_index,
        controls_index,
        outputs_index,
        temperatures_index,
        cool_index
    )

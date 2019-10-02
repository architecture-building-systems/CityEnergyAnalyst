from __future__ import division
import numpy as np
import pandas as pd

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def main(
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
        raise ValueError('No valid pricing_scheme defined')

    # Define the minimal and maximal accepted values for the outputs
    if min_max_source == 'from building.py':
        minimum_output_dic = {}
        maximum_output_dic = {}
        for building in buildings_names:
            minimum_output_dic[building] = buildings_dic[building].output_constraint_timeseries_minimum
            maximum_output_dic[building] = buildings_dic[building].output_constraint_timeseries_maximum
    elif min_max_source == 'from occupancy variations' or min_max_source == 'constants':
        (
            minimum_output_dic,
            maximum_output_dic
        ) = minimum_maximum_outputs(
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
        raise ValueError('No valid min_max_source defined')

    # Define the indexes used in the optimisation
    states_index_all = buildings_dic[buildings_names[0]].index_states.get_values()
    controls_index_all = buildings_dic[buildings_names[0]].index_controls.get_values()
    outputs_index_all = buildings_dic[buildings_names[0]].index_outputs.get_values()
    for i in range(1, buildings_cardinal):
        states_index_all = np.concatenate(
            (
                states_index_all,
                buildings_dic[buildings_names[i]].index_states.get_values()
            ),
            axis=0
        )
        controls_index_all = np.concatenate(
            (
                controls_index_all,
                buildings_dic[buildings_names[i]].index_controls.get_values()
            ),
            axis=0
        )
        outputs_index_all = np.concatenate(
            (
                outputs_index_all,
                buildings_dic[buildings_names[i]].index_outputs.get_values()
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
        for control in buildings_dic[building].index_controls:
            if 'cool' in str(control):
                cool_index_build.append(control)
        cool_index[building] = cool_index_build

    # Return parameters
    return (
        initial_state_dic,
        price_vector,
        minimum_output_dic,
        maximum_output_dic,
        states_index,
        controls_index,
        outputs_index,
        temperatures_index,
        cool_index
    )


def minimum_maximum_outputs(
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
):
    # Get the minimum and maximum values allowed for the temperatures, and the minimum value
    # allowed for the total fresh air flows
    (
        minimum_temperature_dic,
        maximum_temperature_dic
    ) = minimum_maximum_temperatures(
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
        setback_boolean_dic
    )

    minimum_ventilation_dic = minimum_ventilation(
        prediction_horizon,
        date_and_time_prediction,
        buildings_names,
        indoor_comfort_df,
        gross_floor_area_m2,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        occupancy_density_m2_p,
        occupancy_probability_df
    )

    # Write the data frames of all the minimum and maximum output values
    minimum_output_dic = {}
    maximum_output_dic = {}
    for building in buildings_names:
        minimum_output_df = pd.DataFrame(
            np.zeros((buildings_dic[building].index_outputs.shape[0], prediction_horizon)),
            buildings_dic[building].index_outputs,
            date_and_time_prediction
        )
        maximum_output_df = pd.DataFrame(
            np.zeros((buildings_dic[building].index_outputs.shape[0], prediction_horizon)),
            buildings_dic[building].index_outputs,
            date_and_time_prediction
        )

        for output in buildings_dic[building].index_outputs:
            for occupancy in occupancy_per_building_list[building]:
                if occupancy in output:
                    if '_temperature' in output:
                        for time in date_and_time_prediction:
                            minimum_output_df.loc[output][time] = minimum_temperature_dic[building].loc[occupancy][time]
                            maximum_output_df.loc[output][time] = maximum_temperature_dic[building].loc[occupancy][time]
                    elif '_total_fresh_air_flow' in output:
                        for time in date_and_time_prediction:
                            minimum_output_df.loc[output][time] = minimum_ventilation_dic[building].loc[occupancy][time]
                            maximum_output_df.loc[output][time] = float('inf')
                    elif '_window_fresh_air_flow' in output:
                        minimum_output_df.loc[output][:] = 0
                        maximum_output_df.loc[output][:] = float('inf')
                    elif '_electric_power' in output:
                        minimum_output_df.loc[output][:] = 0
                        maximum_output_df.loc[output][:] = float('inf')
                    else:
                        # All additional outputs shall not be constrained (translates to constraining by infinity)
                        minimum_output_df.loc[output][:] = -float('inf')
                        maximum_output_df.loc[output][:] = float('inf')

        minimum_output_dic[building] = minimum_output_df
        maximum_output_dic[building] = maximum_output_df

    return (
        minimum_output_dic,
        maximum_output_dic
    )


def minimum_maximum_temperatures(
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
        setback_boolean_dic
):
    # Calculate minimum and maximum temperatures
    minimum_temperature_dic = {}
    maximum_temperature_dic = {}
    for building in buildings_names:
        minimum_temperature_df = pd.DataFrame(
            np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
            occupancy_per_building_list[building],
            date_and_time_prediction
        )
        maximum_temperature_df = pd.DataFrame(
            np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
            occupancy_per_building_list[building],
            date_and_time_prediction
        )

        for occupancy in occupancy_per_building_list[building]:
            for time in date_and_time_prediction:
                if min_max_source == 'constants':
                    minimum_temperature_df.loc[occupancy][time] = min_constant_temperature
                    maximum_temperature_df.loc[occupancy][time] = max_constant_temperature
                elif min_max_source == 'from occupancy variations':
                    if setback_boolean_dic[building].loc[occupancy][time] == 0:
                        minimum_temperature_df.loc[occupancy][time] = (
                                center_interval_temperatures_dic[building].loc[occupancy][time]
                                - delta_set
                        )
                        maximum_temperature_df.loc[occupancy][time] = (
                                center_interval_temperatures_dic[building].loc[occupancy][time]

                        )
                    elif setback_boolean_dic[building].loc[occupancy][time] == 1:
                        minimum_temperature_df.loc[occupancy][time] = (
                                center_interval_temperatures_dic[building].loc[occupancy][time]
                                - delta_setback
                        )
                        maximum_temperature_df.loc[occupancy][time] = (
                                center_interval_temperatures_dic[building].loc[occupancy][time]

                        )
                    else:
                        raise ValueError(
                            'Setback_boolean_dic of building ' + building + ' for occupancy type '
                            + occupancy + ' for time step ' + time + 'is not equal to 0 nor 1'
                        )
                else:
                    raise ValueError('No valid min_max_source defined')
        minimum_temperature_dic[building] = minimum_temperature_df
        maximum_temperature_dic[building] = maximum_temperature_df

    return (
        minimum_temperature_dic,
        maximum_temperature_dic
    )


def minimum_ventilation(
        prediction_horizon,
        date_and_time_prediction,
        buildings_names,
        indoor_comfort_df,
        gross_floor_area_m2,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        occupancy_density_m2_p,
        occupancy_probability_df
):
    # Calculate minimum ventilation air flow
    minimum_ventilation_dic = {}
    for building in buildings_names:
        minimum_ventilation_df = pd.DataFrame(
            np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
            occupancy_per_building_list[building],
            date_and_time_prediction
        )
        for occupancy in occupancy_per_building_list[building]:
            Ve_occ = (
                    indoor_comfort_df.loc[occupancy]['Ve_lps']
                    * (10 ** (-3))
            )  # from L/s/person to m3/s/person
            occupancy_density_inv_occ = (
                1
                / occupancy_density_m2_p[occupancy]
            )  # from m2/person to person/m2
            for time in date_and_time_prediction:
                minimum_ventilation_df.loc[occupancy][time] = (
                        Ve_occ
                        * occupancy_probability_df.loc[occupancy][time]
                        * occupancy_density_inv_occ
                        * gross_floor_area_m2[building]
                )

        minimum_ventilation_dic[building] = minimum_ventilation_df

    return minimum_ventilation_dic

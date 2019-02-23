import pandas as pd
import numpy as np


def main_minimum_maximum_outputs(min_max_source, min_constant_temperature, max_constant_temperature,
                                 buildings_names, prediction_horizon, date_and_time_prediction, delta_set,
                                 delta_setback, occupancy_per_building_cardinal, occupancy_per_building_list,
                                 center_interval_temperatures_dic, setback_boolean_dic, gross_floor_area_m2,
                                 indoor_comfort_df, occupancy_density_m2_p, occupancy_probability_df,
                                 buildings_dic):
    # Get the minimum and maximum values allowed for the temperatures, and the minimum value
    # allowed for the total fresh air flows
    minimum_temperature_dic, maximum_temperature_dic = minimum_maximum_temperatures(
        min_max_source, min_constant_temperature, max_constant_temperature, buildings_names, prediction_horizon,
        date_and_time_prediction, delta_set, delta_setback, occupancy_per_building_cardinal,
        occupancy_per_building_list, center_interval_temperatures_dic, setback_boolean_dic)

    minimum_ventilation_dic = minimum_ventilation(
        prediction_horizon, date_and_time_prediction, buildings_names, indoor_comfort_df, gross_floor_area_m2,
        occupancy_per_building_cardinal, occupancy_per_building_list, occupancy_density_m2_p, occupancy_probability_df)

    # Write the data frames of all the minimum and maximum output values
    minimum_output_dic = {}
    maximum_output_dic = {}
    for building in buildings_names:
        minimum_output_df = pd.DataFrame(
            np.zeros((buildings_dic[building].i_outputs.shape[0], prediction_horizon)),
            buildings_dic[building].i_outputs.index, date_and_time_prediction)
        maximum_output_df = pd.DataFrame(
            np.zeros((buildings_dic[building].i_outputs.shape[0], prediction_horizon)),
            buildings_dic[building].i_outputs.index, date_and_time_prediction)

        for output in buildings_dic[building].i_outputs.index:
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
                        for time in date_and_time_prediction:
                            minimum_output_df.loc[output][time] = 0
                            maximum_output_df.loc[output][time] = float('inf')
                    elif '_electric_power' in output:
                        for time in date_and_time_prediction:
                            minimum_output_df.loc[output][time] = 0
                            maximum_output_df.loc[output][time] = float('inf')
                    else:
                        print('Error: The output ' + output + ' does not have any minimum nor maximum defined.')
                        quit()

        minimum_output_dic[building] = minimum_output_df
        maximum_output_dic[building] = maximum_output_df

    return minimum_output_dic, maximum_output_dic


def minimum_maximum_temperatures(min_max_source, min_constant_temperature, max_constant_temperature, buildings_names,
                                 prediction_horizon, date_and_time_prediction, delta_set,
                                 delta_setback, occupancy_per_building_cardinal, occupancy_per_building_list,
                                 center_interval_temperatures_dic, setback_boolean_dic):
    # Calculate minimum and maximum temperatures
    minimum_temperature_dic = {}
    maximum_temperature_dic = {}
    for building in buildings_names:
        minimum_temperature_df = pd.DataFrame(
            np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
            occupancy_per_building_list[building], date_and_time_prediction)
        maximum_temperature_df = pd.DataFrame(
            np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
            occupancy_per_building_list[building], date_and_time_prediction)

        for occupancy in occupancy_per_building_list[building]:
            for time in date_and_time_prediction:
                if min_max_source == 'constants':
                    minimum_temperature_df.loc[occupancy][time] = min_constant_temperature
                    maximum_temperature_df.loc[occupancy][time] = max_constant_temperature
                elif min_max_source == 'from occupancy variations':
                    if setback_boolean_dic[building].loc[occupancy][time] == 0:
                        minimum_temperature_df.loc[occupancy][time] = \
                            center_interval_temperatures_dic[building].loc[occupancy][time] - delta_set
                        maximum_temperature_df.loc[occupancy][time] = \
                            center_interval_temperatures_dic[building].loc[occupancy][time] + delta_set
                    elif setback_boolean_dic[building].loc[occupancy][time] == 1:
                        minimum_temperature_df.loc[occupancy][time] = \
                            center_interval_temperatures_dic[building].loc[occupancy][time] - delta_setback
                        maximum_temperature_df.loc[occupancy][time] = \
                            center_interval_temperatures_dic[building].loc[occupancy][time] + delta_setback
                    else:
                        print('Error: setback_boolean_dic of building ' + building + ' for occupancy type '
                              + occupancy + ' for time step ' + time + 'is not equal to 0 nor 1')
                        quit()
                else:
                    print('Error: no valid min_max_source is defined.')
                    quit()
        minimum_temperature_dic[building] = minimum_temperature_df
        maximum_temperature_dic[building] = maximum_temperature_df

    return minimum_temperature_dic, maximum_temperature_dic


def minimum_ventilation(prediction_horizon, date_and_time_prediction, buildings_names, indoor_comfort_df,
                        gross_floor_area_m2, occupancy_per_building_cardinal, occupancy_per_building_list,
                        occupancy_density_m2_p, occupancy_probability_df):
    # Calculate minimum ventilation air flow
    minimum_ventilation_dic = {}
    for building in buildings_names:
        minimum_ventilation_df = pd.DataFrame(
            np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
            occupancy_per_building_list[building], date_and_time_prediction)
        for occupancy in occupancy_per_building_list[building]:
            Ve_occ = indoor_comfort_df.loc[occupancy]['Ve_lps'] * 10 ** (
                -3)  # from L.s^-1.person^-1 to m^3.s^-1.person^-1
            occupancy_density_inv_occ = 1 / occupancy_density_m2_p[occupancy]  # from m^2.person-1 to person/m^-2
            for time in date_and_time_prediction:
                minimum_ventilation_df.loc[occupancy][time] = Ve_occ * occupancy_probability_df.loc[occupancy][
                    time] * occupancy_density_inv_occ * gross_floor_area_m2[building]

        minimum_ventilation_dic[building] = minimum_ventilation_df

    return minimum_ventilation_dic

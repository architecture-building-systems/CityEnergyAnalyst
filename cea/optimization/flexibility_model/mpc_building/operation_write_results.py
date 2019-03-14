from __future__ import division

import os

import pandas as pd

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def main(locator,
         m, output_folder):
    # State space vectors
    outputs_dic = {}
    controls_dic = {}
    states_dic = {}
    for building in m.buildings_names:
        outputs = pd.DataFrame(
            0,
            m.date_and_time_prediction,
            m.buildings_dic[building].index_outputs
        )
        for time in m.date_and_time_prediction:
            for output in m.buildings_dic[building].index_outputs:
                outputs.loc[time, output] = m.outputs_variable[building, output, time].value
        outputs_dic[building] = outputs
        outputs.to_csv(locator.get_mpc_results_outputs(building, output_folder))

        controls = pd.DataFrame(
            0,
            m.date_and_time_prediction,
            m.buildings_dic[building].index_controls
        )
        for time in m.date_and_time_prediction:
            for control in m.buildings_dic[building].index_controls:
                controls.loc[time, control] = m.controls_variable[building, control, time].value
        controls_dic[building] = controls
        controls.to_csv(locator.get_mpc_results_controls(building, output_folder))

        states = pd.DataFrame(
            0,
            m.date_and_time_prediction_plus_1,
            m.buildings_dic[building].index_states
        )
        for time in m.date_and_time_prediction_plus_1:
            for state in m.buildings_dic[building].index_states:
                states.loc[time, state] = m.states_variable[building, state, time].value
        states_dic[building] = states
        states.to_csv(locator.get_mpc_results_states(building, output_folder))

        m.minimum_output_dic[building].to_csv(locator.get_mpc_results_min_outputs(building, output_folder))
        m.maximum_output_dic[building].to_csv(locator.get_mpc_results_max_outputs(building, output_folder))

    # Aggregations
    predicted_temperature_df = pd.DataFrame(
        0,
        m.date_and_time_prediction,
        m.buildings_names
    )
    set_temperature_df = pd.DataFrame(
        0,
        m.date_and_time_prediction,
        m.buildings_names
    )
    minimum_temperature_df = pd.DataFrame(
        0,
        m.date_and_time_prediction,
        m.buildings_names
    )
    maximum_temperature_df = pd.DataFrame(
        0,
        m.date_and_time_prediction,
        m.buildings_names
    )
    cea_temperature_df = pd.DataFrame(
        0,
        m.date_and_time_prediction,
        m.buildings_names
    )
    for building in m.buildings_names:
        for time in m.date_and_time_prediction:
            predicted_temperature = 0
            set_temperature = 0
            minimum_temperature = 0
            maximum_temperature = 0
            for occupancy in m.occupancy_per_building_list[building]:
                predicted_temperature += outputs_dic[building].loc[time][occupancy + '_temperature']
                set_temperature += m.set_temperatures_dic[building].loc[occupancy][time]
                minimum_temperature += m.minimum_output_dic[building].loc[occupancy + '_temperature'][time]
                maximum_temperature += m.maximum_output_dic[building].loc[occupancy + '_temperature'][time]

            predicted_temperature_df.loc[time][building] = (
                    predicted_temperature
                    / int(m.occupancy_per_building_cardinal[building])
            )
            set_temperature_df.loc[time][building] = (
                    set_temperature
                    / int(m.occupancy_per_building_cardinal[building])
            )
            minimum_temperature_df.loc[time][building] = (
                    minimum_temperature
                    / int(m.occupancy_per_building_cardinal[building])
            )
            maximum_temperature_df.loc[time][building] = (
                    maximum_temperature
                    / int(m.occupancy_per_building_cardinal[building])
            )
    predicted_temperature_df.to_csv(locator.get_mpc_results_predicted_temperature(output_folder))
    set_temperature_df.to_csv(locator.get_mpc_results_set_temperature(output_folder))
    minimum_temperature_df.to_csv(locator.get_mpc_results_min_temperature(output_folder))
    maximum_temperature_df.to_csv(locator.get_mpc_results_max_temperature(output_folder))

    electric_power_df = pd.DataFrame(
        0,
        m.date_and_time_prediction,
        m.buildings_names
    )
    for building in m.buildings_names:
        electric_power_df[:][building] = (
            outputs_dic[building].T[['electric_power' in x for x in outputs_dic[building].columns]].T.sum(axis=1)
        )
    electric_power_df.to_csv(locator.get_mpc_results_electric_power(output_folder))

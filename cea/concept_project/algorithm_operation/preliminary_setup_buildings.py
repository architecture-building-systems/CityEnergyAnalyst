import numpy as np
import pandas as pd
from datetime import datetime
from concept.algorithm_operation.set_temperatures import main_set_temperatures

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main_preliminary_setup_buildings(date_and_time_prediction, time_step, set_temperature_goal,
                                     constant_temperature, buildings_names, system_controls_df,
                                     occupancy_per_building_cardinal, occupancy_per_building_list,
                                     occupancy_probability_df, indoor_comfort_df, T_int_cea_dic):

    # Determine the parameters linked to time
    prediction_horizon = int((date_and_time_prediction[-1] - date_and_time_prediction[0]) / time_step) + 1

    # Define the set temperatures
    center_interval_temperatures_dic, set_setback_temperatures_dic, setback_boolean_dic, heating_boolean, \
        cooling_boolean = main_set_temperatures(
            date_and_time_prediction, prediction_horizon, buildings_names, system_controls_df,
            occupancy_per_building_cardinal, occupancy_per_building_list, occupancy_probability_df, indoor_comfort_df)

    if set_temperature_goal == 'follow_cea':
        set_temperatures_dic = {}
        for building in buildings_names:
            set_temperatures_df = pd.DataFrame(
                np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
                occupancy_per_building_list[building], date_and_time_prediction)
            for time in date_and_time_prediction:
                for occupancy in occupancy_per_building_list[building]:
                    string_object_time = datetime.strftime(time, '%Y-%m-%d %H:%M:%S')
                    set_temperatures_df.loc[occupancy][time] = T_int_cea_dic[building].loc[string_object_time]
            set_temperatures_dic[building] = set_temperatures_df

    elif set_temperature_goal == 'constant_temperature':
        set_temperatures_dic = {}
        for building in buildings_names:
            set_temperatures_df = pd.DataFrame(
                np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
                occupancy_per_building_list[building], date_and_time_prediction)
            for time in date_and_time_prediction:
                for occupancy in occupancy_per_building_list[building]:
                    set_temperatures_df.loc[occupancy][time] = constant_temperature
            set_temperatures_dic[building] = set_temperatures_df

    elif set_temperature_goal == 'set_setback_temperature':
        set_temperatures_dic = set_setback_temperatures_dic

    else:
        print('Error: no valid set_temperature_goal is defined.')
        quit()

    # Return parameters
    return prediction_horizon, center_interval_temperatures_dic, set_setback_temperatures_dic, setback_boolean_dic, \
        heating_boolean, cooling_boolean, set_temperatures_dic

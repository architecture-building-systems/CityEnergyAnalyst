"""
MIT License

Copyright (c) 2019 TUMCREATE <https://tum-create.edu.sg/>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from __future__ import division
import numpy as np
import pandas as pd
import datetime

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def main(
        date_and_time_prediction,
        time_step, set_temperature_goal,
        constant_temperature,
        buildings_names,
        system_controls_df,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        occupancy_probability_df,
        indoor_comfort_df,
        T_int_cea_dic
):

    # Determine the parameters linked to time
    prediction_horizon = int((date_and_time_prediction[-1] - date_and_time_prediction[0]) / time_step) + 1

    # Define the set temperatures
    (
        center_interval_temperatures_dic,
        set_setback_temperatures_dic,
        setback_boolean_dic,
        heating_boolean,
        cooling_boolean
    ) = get_set_temperatures(
        date_and_time_prediction,
        prediction_horizon,
        buildings_names,
        system_controls_df,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        occupancy_probability_df,
        indoor_comfort_df
    )

    if set_temperature_goal == 'follow_cea':
        set_temperatures_dic = {}
        for building in buildings_names:
            set_temperatures_df = pd.DataFrame(
                np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
                occupancy_per_building_list[building],
                date_and_time_prediction
            )
            for time in date_and_time_prediction:
                for occupancy in occupancy_per_building_list[building]:
                    string_object_time = datetime.datetime.strftime(time, '%Y-%m-%d %H:%M:%S')
                    set_temperatures_df.loc[occupancy][time] = T_int_cea_dic[building].loc[string_object_time]
            set_temperatures_dic[building] = set_temperatures_df

    elif set_temperature_goal == 'constant_temperature':
        set_temperatures_dic = {}
        for building in buildings_names:
            set_temperatures_df = pd.DataFrame(
                np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
                occupancy_per_building_list[building],
                date_and_time_prediction
            )
            for time in date_and_time_prediction:
                for occupancy in occupancy_per_building_list[building]:
                    set_temperatures_df.loc[occupancy][time] = constant_temperature
            set_temperatures_dic[building] = set_temperatures_df

    elif set_temperature_goal == 'set_setback_temperature':
        set_temperatures_dic = set_setback_temperatures_dic

    else:
        raise ValueError('No valid set_temperature_goal defined')

    return (
        prediction_horizon,
        center_interval_temperatures_dic,
        set_setback_temperatures_dic,
        setback_boolean_dic,
        heating_boolean,
        cooling_boolean,
        set_temperatures_dic
    )

def get_set_temperatures(
        date_and_time_prediction,
        prediction_horizon,
        buildings_names,
        system_controls_df,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        occupancy_probability_df,
        indoor_comfort_df
):
    center_interval_temperatures_dic = {}
    set_setback_temperatures_dic = {}
    setback_boolean_dic = {}
    type_season = seasons_type(system_controls_df)
    (
        heating_boolean,
        cooling_boolean
    ) = season_all(
        date_and_time_prediction,
        type_season,
        system_controls_df
    )
    for building in buildings_names:
        (center_interval_temperatures_dic[building],
         set_setback_temperatures_dic[building],
         setback_boolean_dic[building]
         ) = set_outputs_one_building(
            building,
            prediction_horizon,
            date_and_time_prediction,
            heating_boolean,
            cooling_boolean,
            occupancy_per_building_cardinal,
            occupancy_per_building_list,
            occupancy_probability_df,
            indoor_comfort_df
        )

    return (
        center_interval_temperatures_dic,
        set_setback_temperatures_dic,
        setback_boolean_dic,
        heating_boolean,
        cooling_boolean
    )


def seasons_type(system_controls_df):
    if (system_controls_df.loc[0]['has_heating_season'] == 1 or str(
            system_controls_df.loc[0]['has_heating_season']).upper() == 'TRUE') and (
            system_controls_df.loc[0]['has_cooling_season'] == 0 or str(
            system_controls_df.loc[0]['has_cooling_season']).upper() == 'FALSE'):
        # Only has a heating season
        type_season = 1
    elif (system_controls_df.loc[0]['has_heating_season'] == 0 or str(
            system_controls_df.loc[0]['has_heating_season']).upper() == 'FALSE') and (
            system_controls_df.loc[0]['has_cooling_season'] == 1 or str(
            system_controls_df.loc[0]['has_cooling_season']).upper() == 'TRUE'):
        # Only has a cooling season
        type_season = 2
    elif (system_controls_df.loc[0]['has_heating_season'] == 1 or str(
            system_controls_df.loc[0]['has_heating_season']).upper() == 'TRUE') \
            and (system_controls_df.loc[0]['has_cooling_season'] == 1 or str(
            system_controls_df.loc[0]['has_cooling_season']).upper() == 'TRUE'):
        # Has both a heating and a cooling season
        if system_controls_df.loc[0]['heating_season_end_month'] < system_controls_df.loc[0][
                'cooling_season_end_month']:  # Comparing end of heating season month and end of cooling season month
            type_season = 3  # North hemisphere type
        elif system_controls_df.loc[0]['heating_season_end_month'] == system_controls_df.loc[0][
                'cooling_season_end_month'] and system_controls_df.loc[0][
                ' heating_season_end_day'] < system_controls_df.loc[0][
                'cooling_season_end_day']:  # Comparing end of heating season day and end of cooling season day
            type_season = 3
        else:
            type_season = 4  # South hemisphere type
    else:
        return "The code is not in line with system_controls.xlsx"
    return type_season


def date_season(time, type_season, system_controls_df):
    # For a given time step, returns the season which it corresponds to
    if type_season == 1:
        season_t = 'heating'
    elif type_season == 2:
        season_t = 'cooling'
    else:
        year_t = time.year
        heating_season_end = datetime.datetime(
            year_t,
            system_controls_df['heating_season_end_month'],
            system_controls_df['heating_season_end_day'],
            23,
            59,
            59,
            999999
        )
        cooling_season_end = datetime.datetime(
            year_t,
            system_controls_df['cooling_season_end_month'],
            system_controls_df['cooling_season_end_day'],
            23,
            59,
            59,
            999999
        )
        if type_season == 3:
            if time <= heating_season_end:
                season_t = 'heating'
            elif time <= cooling_season_end:
                season_t = 'cooling'
            else:
                season_t = 'heating'
        elif type_season == 4:
            if time <= cooling_season_end:
                season_t = 'cooling'
            elif time <= heating_season_end:
                season_t = 'heating'
            else:
                season_t = 'cooling'
        else:
            raise ValueError('Season not defined to "heating" nor "cooling"')

    return season_t


def season_all(date_and_time_prediction, type_season, system_controls_df):
    heating_boolean = {}
    cooling_boolean = {}
    for time in date_and_time_prediction:
        season_t = date_season(time, type_season, system_controls_df)
        if season_t == 'cooling':
            heating_boolean[time] = 0
            cooling_boolean[time] = 1
        elif season_t == 'heating':
            heating_boolean[time] = 1
            cooling_boolean[time] = 0
        else:
            raise ValueError('Season not defined to "heating" nor "cooling"')
    return heating_boolean, cooling_boolean


def set_outputs_one_building(
        building,
        prediction_horizon,
        date_and_time_prediction,
        heating_boolean,
        cooling_boolean,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        occupancy_probability_df,
        indoor_comfort_df
):

    center_interval_temperatures_df = pd.DataFrame(
        np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
        occupancy_per_building_list[building],
        date_and_time_prediction
    )
    set_setback_temperatures_df = pd.DataFrame(
        np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
        occupancy_per_building_list[building],
        date_and_time_prediction
    )
    setback_boolean_df = pd.DataFrame(
        np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
        occupancy_per_building_list[building],
        date_and_time_prediction
    )

    for occupancy in occupancy_per_building_list[building]:
        for time in date_and_time_prediction:
            if occupancy_probability_df.loc[occupancy][time] > 0:
                setback_boolean_df.loc[occupancy][time] = 0
                if cooling_boolean[time] == 1:
                    center_interval_temperatures_df.loc[occupancy][time] = indoor_comfort_df.loc[occupancy]['Tcs_set_C']
                    set_setback_temperatures_df.loc[occupancy][time] = indoor_comfort_df.loc[occupancy]['Tcs_set_C']
                elif heating_boolean[time] == 1:
                    center_interval_temperatures_df.loc[occupancy][time] = indoor_comfort_df.loc[occupancy]['Ths_set_C']
                    set_setback_temperatures_df.loc[occupancy][time] = indoor_comfort_df.loc[occupancy]['Ths_set_C']
                else:
                    raise ValueError('Season not defined to "heating" nor "cooling"')
            if occupancy_probability_df.loc[occupancy][time] == 0:
                setback_boolean_df.loc[occupancy][time] = 1
                if cooling_boolean[time] == 1:
                    center_interval_temperatures_df.loc[occupancy][time] = indoor_comfort_df.loc[occupancy]['Tcs_set_C']
                    set_setback_temperatures_df.loc[occupancy][time] = indoor_comfort_df.loc[occupancy]['Tcs_setb_C']
                elif heating_boolean[time] == 1:
                    center_interval_temperatures_df.loc[occupancy][time] = indoor_comfort_df.loc[occupancy]['Ths_set_C']
                    set_setback_temperatures_df.loc[occupancy][time] = indoor_comfort_df.loc[occupancy]['Ths_setb_C']
                else:
                    raise ValueError('Season not defined to "heating" nor "cooling"')

    return (
        center_interval_temperatures_df,
        set_setback_temperatures_df,
        setback_boolean_df
    )

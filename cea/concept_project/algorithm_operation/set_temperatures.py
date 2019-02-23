from datetime import datetime
import pandas as pd
import numpy as np


def main_set_temperatures(date_and_time_prediction, prediction_horizon, buildings_names, system_controls_df,
                          occupancy_per_building_cardinal, occupancy_per_building_list, occupancy_probability_df,
                          indoor_comfort_df):
    center_interval_temperatures_dic = {}
    set_setback_temperatures_dic = {}
    setback_boolean_dic = {}
    type_season = seasons_type(system_controls_df)
    heating_boolean, cooling_boolean = season_all(date_and_time_prediction, type_season, system_controls_df)
    for building in buildings_names:
        center_interval_temperatures_dic[building], set_setback_temperatures_dic[building], setback_boolean_dic[
            building] = set_outputs_one_building(building, prediction_horizon, date_and_time_prediction,
                                                 heating_boolean, cooling_boolean, occupancy_per_building_cardinal,
                                                 occupancy_per_building_list, occupancy_probability_df,
                                                 indoor_comfort_df)

    return center_interval_temperatures_dic, set_setback_temperatures_dic, setback_boolean_dic, \
        heating_boolean, cooling_boolean


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
        heating_season_end = datetime(year_t, system_controls_df['heating_season_end_month'],
                                      system_controls_df['heating_season_end_day'], 23, 59, 59, 999999)
        cooling_season_end = datetime(year_t, system_controls_df['cooling_season_end_month'],
                                      system_controls_df['cooling_season_end_day'], 23, 59, 59, 999999)
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
            print('Season type error: "type_season" is not well defined')
            quit()

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
            return 'Season error: season not defined to "heating" nor "cooling"'
    return heating_boolean, cooling_boolean


def set_outputs_one_building(building, prediction_horizon, date_and_time_prediction, heating_boolean, cooling_boolean,
                             occupancy_per_building_cardinal, occupancy_per_building_list, occupancy_probability_df,
                             indoor_comfort_df):

    center_interval_temperatures_df = pd.DataFrame(
        np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
        occupancy_per_building_list[building], date_and_time_prediction)
    set_setback_temperatures_df = pd.DataFrame(
        np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
        occupancy_per_building_list[building], date_and_time_prediction)
    setback_boolean_df = pd.DataFrame(
        np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
        occupancy_per_building_list[building], date_and_time_prediction)

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
                    return 'Season error: season not defined to "heating" nor "cooling"'
            if occupancy_probability_df.loc[occupancy][time] == 0:
                setback_boolean_df.loc[occupancy][time] = 1
                if cooling_boolean[time] == 1:
                    center_interval_temperatures_df.loc[occupancy][time] = indoor_comfort_df.loc[occupancy]['Tcs_set_C']
                    set_setback_temperatures_df.loc[occupancy][time] = indoor_comfort_df.loc[occupancy]['Tcs_setb_C']
                elif heating_boolean[time] == 1:
                    center_interval_temperatures_df.loc[occupancy][time] = indoor_comfort_df.loc[occupancy]['Ths_set_C']
                    set_setback_temperatures_df.loc[occupancy][time] = indoor_comfort_df.loc[occupancy]['Ths_setb_C']
                else:
                    return 'Season error: season not defined to "heating" nor "cooling"'

    return center_interval_temperatures_df, set_setback_temperatures_df, setback_boolean_df

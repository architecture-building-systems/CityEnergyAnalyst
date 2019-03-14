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

import datetime
import math
import os
import warnings
import shutil
import numpy as np
import pandas as pd
from cea.optimization.flexibility_model import model_building

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def main(locator, scenario,
         date_and_time_prediction,
         time_start,
         time_end,
         time_step,
         parameter_set,
         internal_loads_df,
         construction_envelope_systems_df,
         leakage_envelope_systems_df,
         window_envelope_systems_df,
         roofs_envelope_systems_df,
         wall_envelope_systems_df,
         shading_envelope_systems_df,
         zone_occupancy_df,
         architecture_df,
         weather_general_info,
         weather_timeseries_initial_df,
         occupancy_types,
         occupancy_types_cardinal,
         buildings_names,
         building_geometry_all,
         occupants_probability_dic,
         lighting_appliances_probability_dic,
         processes_probability_dic,
         monthly_use_probability_df,
         occupancy_density_m2_p,
         gross_floor_area_m2,
         mean_floor_height_m,
         DELTA_P_DIM,
         h_e,
         h_i,
         density_air,
         heat_capacity_air,
         supply_temperature_df,
         emissions_cooling_type_dic
         ):
    prepare_folder(locator) #this copies one file to the /outputs/building-definitions
    write_building_zones(locator,
                         buildings_names,
                         occupancy_types,
                         zone_occupancy_df,
                         gross_floor_area_m2,
                         mean_floor_height_m
                         )
    write_building_surfaces_interior(locator)
    write_building_surfaces_adiabatic(locator)
    write_building_surfaces_exterior(locator,
                                     buildings_names,
                                     architecture_df,
                                     occupancy_types,
                                     zone_occupancy_df,
                                     building_geometry_all
                                     )
    write_building_blind_types(locator,
                               shading_envelope_systems_df
                               )
    write_buildings(locator,
                    buildings_names,
                    weather_general_info
                    )
    write_building_surface_types(locator,
                                 wall_envelope_systems_df,
                                 window_envelope_systems_df,
                                 roofs_envelope_systems_df,
                                 h_e,
                                 h_i
                                 )
    write_building_window_types(locator,
                                window_envelope_systems_df,
                                h_e,
                                h_i
                                )
    (
        date_and_time,
        year,
        wet_bulb_temperature_df
    ) = write_weather(locator,
                      date_and_time_prediction,
                      weather_general_info,
                      weather_timeseries_initial_df
                      )
    write_building_scenarios(locator, scenario,
                             buildings_names,
                             time_start,
                             time_end,
                             time_step
                             )
    write_building_parameter_sets(locator,
                                  parameter_set,
                                  mean_floor_height_m,
                                  buildings_names,
                                  leakage_envelope_systems_df,
                                  construction_envelope_systems_df,
                                  DELTA_P_DIM,
                                  h_e,
                                  h_i,
                                  density_air,
                                  heat_capacity_air
                                  )
    write_building_linearization_types(locator
                                       )
    lighting_appliances_probability_combined_dic = write_building_internal_gain_types(locator,
                                                                                      occupancy_types,
                                                                                      internal_loads_df,
                                                                                      lighting_appliances_probability_dic,
                                                                                      processes_probability_dic,
                                                                                      occupancy_density_m2_p
                                                                                      )
    occupancy_probability_df = write_building_internal_gain_timeseries(locator,
                                                                       date_and_time_prediction,
                                                                       occupancy_types_cardinal,
                                                                       occupancy_types,
                                                                       occupants_probability_dic,
                                                                       lighting_appliances_probability_combined_dic,
                                                                       monthly_use_probability_df
                                                                       )
    write_building_zone_types(locator,
                              buildings_names,
                              occupancy_types,
                              zone_occupancy_df,
                              architecture_df,
                              supply_temperature_df,
                              emissions_cooling_type_dic
                              )

    return (
        date_and_time,
        year,
        wet_bulb_temperature_df,
        occupancy_probability_df
    )


def prepare_folder(locator):

    # Copy file(s) from default building definition # TODO: Create these file(s) dynamically
    shutil.copy(os.path.join(os.path.dirname(model_building.__file__), 'setup_data', 'building_zone_constraint_profiles.csv'),
                locator.get_mpc_results_building_definitions_folder())


def write_building_zones(
        locator,
        buildings_names,
        occupancy_types,
        zone_occupancy_df,
        gross_floor_area_m2,
        mean_floor_height_m
):
    building_zones = []
    for building in buildings_names:
        for occupancy in occupancy_types:
            if zone_occupancy_df.loc[building][occupancy] > 0:
                zone_area_build_occ = zone_occupancy_df.loc[building][occupancy] * gross_floor_area_m2[building]
                building_zones.append([
                    building,
                    occupancy,
                    building + '_' + occupancy, mean_floor_height_m[building],
                    zone_area_build_occ,
                    ''
                ])
    building_zones_df = pd.DataFrame.from_records(
        building_zones,
        columns=[
            'building_name',
            'zone_name',
            'zone_type',
            'zone_height',
            'zone_area',
            'zone_comment'
        ]
    )
    building_zones_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('building_zones'),
        index=False
    )


def write_building_surfaces_interior(locator):
    # Writing a blank file because no interior surface is considered here
    building_surfaces_interior_df = pd.DataFrame(
        index=[0],
        columns=[
            'building_name',
            'zone_name',
            'zone_adjacent_name',
            'surface_name',
            'surface_type',
            'surface_area',
            'surface_comment'
        ]
    )
    building_surfaces_interior_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('building_surfaces_interior'),
        index=False
    )


def write_building_surfaces_adiabatic(locator):
    # Writing a blank file because no adiabatic surface is considered here
    building_surfaces_adiabatic_df = pd.DataFrame(
        index=[0],
        columns=[
            'building_name',
            'zone_name',
            'surface_name',
            'surface_type',
            'surface_area',
            'surface_comment'
        ]
    )
    building_surfaces_adiabatic_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('building_surfaces_adiabatic'),
        index=False
        )


def write_building_surfaces_exterior(locator,
                                     buildings_names,
                                     architecture_df,
                                     occupancy_types,
                                     zone_occupancy_df,
                                     building_geometry_all
                                     ):
    building_surfaces_exterior = []
    for building in buildings_names:
        type_wall_build = architecture_df.loc[building]['type_wall']
        type_window_build = architecture_df.loc[building]['type_win']
        type_roof_build = architecture_df.loc[building]['type_roof']
        for occupancy in occupancy_types:
            if zone_occupancy_df.loc[building][occupancy] > 0:
                for index, row in building_geometry_all[building].iterrows():
                    if row['TYPE'] == 'walls':
                        surface_type_r = 'wall_' + type_wall_build
                    elif row['TYPE'] == 'windows':
                        surface_type_r = 'window_' + type_window_build
                    elif row['TYPE'] == 'roofs':
                        surface_type_r = 'roof_' + type_roof_build
                    else:
                        raise ValueError(
                            'In ' + building + '_geometry.csv, the "TYPE" of surface '
                            + row['SURFACE'] + 'is neither a wall, nor a window, nor a roof.'
                        )

                    orientation_r = row['orientation']
                    if orientation_r == 'top':
                        orientation_r = 'horizontal'

                    building_surfaces_exterior.append([
                        building,
                        occupancy,
                        orientation_r,
                        row['SURFACE'] + '_' + occupancy + '_' + building,
                        surface_type_r,
                        zone_occupancy_df.loc[building][occupancy] * row['AREA_m2'],
                        ''
                    ])

    building_surfaces_exterior_df = pd.DataFrame(
        building_surfaces_exterior,
        columns=[
            'building_name',
            'zone_name',
            'direction_name',
            'surface_name',
            'surface_type',
            'surface_area',
            'surface_comment'
        ]
    )

    # Merge surfaces with identical properties
    building_surfaces_exterior_df = building_surfaces_exterior_df.groupby([
        'building_name',
        'zone_name',
        'direction_name',
        'surface_type'
    ]).sum().reset_index()
    building_surfaces_exterior_df['surface_name'] = (
            'srf_'
            + building_surfaces_exterior_df['building_name'] + '_'
            + building_surfaces_exterior_df['zone_name'] + '_'
            + building_surfaces_exterior_df['direction_name'] + '_'
            + building_surfaces_exterior_df['surface_type']
    )
    building_surfaces_exterior_df['surface_comment'] = ''

    building_surfaces_exterior_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('building_surfaces_exterior'
                                                                      ),
        index=False
    )


def write_building_blind_types(locator,
                               shading_envelope_systems_df
                               ):
    building_blind_types = []
    for index, row in shading_envelope_systems_df.iterrows():
        building_blind_types.append([
            'blind_' + index,
            1 - row['rf_sh']
        ])
    building_blind_types_df = pd.DataFrame(
        building_blind_types,
        columns=[
            'blind_type',
            'blind_efficiency'
        ]
    )
    building_blind_types_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('building_blind_types'
                                                                      ),
        index=False
    )


def write_buildings(locator,
                    buildings_names,
                    weather_general_info
                    ):
    location = weather_general_info[0][1]
    buildings = []
    for building in buildings_names:
        buildings.append([
            building,
            location
        ])
    buildings_df = pd.DataFrame(
        buildings,
        columns=[
            'building_name',
            'location_name'
        ]
    )
    buildings_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('buildings'
                                                                      ),
        index=False
    )


def write_building_surface_types(locator,
                                 wall_envelope_systems_df,
                                 window_envelope_systems_df,
                                 roofs_envelope_systems_df,
                                 h_e,
                                 h_i
                                 ):
    #  TODO: consider adding heat capacity for the walls, and putting the air heat capacity
    #  instead of the construction heat capacity that is from envelope_systems.xls > CONSTRUCTION
    building_surface_types = []

    #  Wall surface types
    for index, row in wall_envelope_systems_df.iterrows():
        resistance_r = 0.5 * ((1 / row['U_wall']) - (1 / h_e) - (1 / h_i))
        building_surface_types.append([
            'wall_' + index,
            0,
            resistance_r,
            row['a_wall'],
            row['e_wall'],
            '',
            0,
            0.5
        ])

    # Roof surface types
    for index, row in roofs_envelope_systems_df.iterrows():
        resistance_r = 0.5 * ((1 / row['U_roof']) - (1 / h_e) - (1 / h_i))
        building_surface_types.append([
            'roof_' + index,
            0,
            resistance_r,
            row['a_roof'],
            row['e_roof'],
            '',
            0,
            1
        ])

    # Window surface types
    for index, row in window_envelope_systems_df.iterrows():
        resistance_r = 0.5 * ((1 / row['U_win']) - (1 / h_e) - (1 / h_i))
        building_surface_types.append([
            'window_' + index,
            0,
            resistance_r,
            row['G_win'],
            row['e_win'],  # TODO: Check this
            'window_' + index,
            1,
            0.5
        ])

    # Create dataframe
    building_surface_types_df = pd.DataFrame(
        building_surface_types,
        columns=[
            'surface_type',
            'heat_capacity',
            'thermal_resistance_surface',
            'irradiation_gain_coefficient',
            'emissivity',
            'window_type',
            'window_wall_ratio',
            'sky_view_factor'
        ]
    )
    building_surface_types_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('building_surface_types'
                                                                      ),
        index=False
    )


def write_building_window_types(locator,
                                window_envelope_systems_df,
                                h_e,
                                h_i
                                ):
    building_window_type = []
    for index, row in window_envelope_systems_df.iterrows():
        resistance_r = 0.5 * ((1 / row['U_win']) - (1 / h_e) - (1 / h_i))
        building_window_type.append([
            'window_' + index,
            resistance_r,
            row['G_win']
        ])

    building_window_type_df = pd.DataFrame(
        building_window_type,
        columns=[
            'window_type',
            'thermal_resistance_window',
            'irradiation_transfer_coefficient'
        ])
    building_window_type_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('building_window_types'
                                                                      ),
        index=False)


def calculate_building_internal_gain_types(
        internal_loads_df,
        occupancy_types,
        occupancy_density_m2_p
):
    # This function calculates the 3 internal gains types, that come from: the occupants, the lighting and appliances,
    # and the processes.
    building_internal_gain_types_initial = []
    for occupancy in occupancy_types:
        if occupancy_density_m2_p[occupancy] > 0:
            internal_gain_occupancy_occ = (
                    float(internal_loads_df.loc[occupancy]['Qs_Wp'])
                    / float(occupancy_density_m2_p[occupancy])
            )
        else:
            internal_gain_occupancy_occ = 0
        internal_gain_appliances_occ = (
                float(internal_loads_df.loc[occupancy]['Ea_Wm2'])
                + float(internal_loads_df.loc[occupancy]['El_Wm2'])
                + float(internal_loads_df.loc[occupancy]['Ed_Wm2'])
        )
        building_internal_gain_types_initial.append([
            occupancy,
            internal_gain_occupancy_occ,
            internal_gain_appliances_occ,
            float(internal_loads_df.loc[occupancy]['Epro_Wm2'])
        ])

    building_internal_gain_types_initial_df = pd.DataFrame(
        building_internal_gain_types_initial,
        columns=[
            'internal_gain_type',
            'internal_gain_occupancy_factor',
            'internal_gain_appliances_factor',
            'internal_gain_processes_factor'
        ]
    )
    building_internal_gain_types_initial_df.set_index(
        'internal_gain_type',
        inplace=True
    )

    return building_internal_gain_types_initial_df


def combine_processes_appliances_internal_gains_one_occupancy_type(
        internal_gain_appliances_initial_occ,
        internal_gain_processes_initial_occ,
        lighting_appliances_probability_occ_df,
        processes_probability_occ_df
):
    # This function combines the internal gains from the lighting and appliances, and the internal gains from the
    # processes in a single internal gain, for occupancy types that have processes.

    # Sum up the gains of lighting and appliances and processes, for each time of the day and of the week
    quantity_weekdays = []
    quantity_saturdays = []
    quantity_sundays = []

    for hour in range(1, 25):
        quantity_weekdays.append(
            float(lighting_appliances_probability_occ_df.loc['Weekday_2'][hour])
            * float(internal_gain_appliances_initial_occ)
            + float(processes_probability_occ_df.loc['Weekday_4'][hour])
            * float(internal_gain_processes_initial_occ)
        )
        quantity_saturdays.append(
            float(lighting_appliances_probability_occ_df.loc['Saturday_2'][hour])
            * float(internal_gain_appliances_initial_occ)
            + float(processes_probability_occ_df.loc['Saturday_4'][hour])
            * float(internal_gain_processes_initial_occ)
        )
        quantity_sundays.append(
            float(lighting_appliances_probability_occ_df.loc['Sunday_2'][hour])
            * float(internal_gain_appliances_initial_occ)
            + float(processes_probability_occ_df.loc['Sunday_4'][hour])
            * float(internal_gain_processes_initial_occ)
        )

    # Find the peak value
    max_weekday = max(quantity_weekdays)
    max_saturday = max(quantity_saturdays)
    max_sunday = max(quantity_sundays)
    internal_gain_combined_occ = max(max_weekday, max_saturday, max_sunday)

    # Calculate the new probability of lighting and appliances & processes combined
    combined_probability_weekdays = [float(x) / float(internal_gain_combined_occ) for x in quantity_weekdays]
    combined_probability_saturdays = [float(x) / float(internal_gain_combined_occ) for x in quantity_saturdays]
    combined_probability_sundays = [float(x) / float(internal_gain_combined_occ) for x in quantity_sundays]

    # Get the output in the same format than the other occupancy schedules data frames
    combined_probability_weekdays.insert(0, 'Weekday_2')
    combined_probability_saturdays.insert(0, 'Saturday_2')
    combined_probability_sundays.insert(0, 'Sunday_2')

    label_day = range(1, 25)
    label_day.insert(0, 'day_of_week')

    combined_probability_occ_df = pd.DataFrame(
        [
            combined_probability_weekdays,
            combined_probability_saturdays,
            combined_probability_sundays
        ],
        columns=label_day
    )
    combined_probability_occ_df.set_index(
        'day_of_week',
        inplace=True
    )

    return (
        combined_probability_occ_df,
        internal_gain_combined_occ
    )


def write_building_internal_gain_types(locator,
        occupancy_types,
        internal_loads_df,
        lighting_appliances_probability_dic,
        processes_probability_dic,
        occupancy_density_m2_p
):
    building_internal_gain_types_initial_df = calculate_building_internal_gain_types(
        internal_loads_df,
        occupancy_types,
        occupancy_density_m2_p
    )
    building_internal_gain_types = []
    lighting_appliances_probability_combined_dic = {}

    for occupancy in occupancy_types:
        if occupancy in processes_probability_dic:  # Case where the occupancy type has processes
            combined_probability_occ_df, internal_gain_combined_occ = \
                combine_processes_appliances_internal_gains_one_occupancy_type(
                    building_internal_gain_types_initial_df.loc[occupancy]['internal_gain_appliances_factor'],
                    building_internal_gain_types_initial_df.loc[occupancy]['internal_gain_processes_factor'],
                    lighting_appliances_probability_dic[occupancy], processes_probability_dic[occupancy]
                )
        else:  # Case where occupancy type doesn't have processes
            combined_probability_occ_df = lighting_appliances_probability_dic[occupancy]
            internal_gain_combined_occ = (
                building_internal_gain_types_initial_df.loc[occupancy]['internal_gain_appliances_factor']
            )

        building_internal_gain_types.append([
            occupancy,
            building_internal_gain_types_initial_df.loc[occupancy]['internal_gain_occupancy_factor'],
            internal_gain_combined_occ
        ])
        lighting_appliances_probability_combined_dic[occupancy] = combined_probability_occ_df

    building_internal_gain_types_df = pd.DataFrame(
        building_internal_gain_types,
        columns=[
            'internal_gain_type',
            'internal_gain_occupancy_factor',
            'internal_gain_appliances_factor'
        ]
    )
    building_internal_gain_types_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('building_internal_gain_types'
        ),
        index=False
    )

    return lighting_appliances_probability_combined_dic


def write_building_internal_gain_timeseries(
        locator,
        date_and_time_prediction,
        occupancy_types_cardinal,
        occupancy_types,
        occupants_probability_dic,
        lighting_appliances_probability_combined_dic,
        monthly_use_probability_df
):
    internal_gain_timeseries = []
    occupancy_probability_df = pd.DataFrame(
        np.zeros((occupancy_types_cardinal, len(date_and_time_prediction))),
        occupancy_types,
        date_and_time_prediction
    )
    for occupancy in occupancy_types:
        for time in date_and_time_prediction:
            # Probability of use - month
            month = time.month
            month_use = monthly_use_probability_df.loc[occupancy][month]

            # Probability of use - hour and weekday
            hour = time.hour
            weekday = time.weekday()
            if weekday < 5:
                weekday_string_occupants = 'Weekday_1'
                weekday_string_lighting = 'Weekday_2'
            elif weekday == 5:
                weekday_string_occupants = 'Saturday_1'
                weekday_string_lighting = 'Saturday_2'
            elif weekday == 6:
                weekday_string_occupants = 'Sunday_1'
                weekday_string_lighting = 'Sunday_2'
            else:
                raise ValueError('Weekday error')

            # Probability of use - overall
            occupancy_probability = (
                    occupants_probability_dic[occupancy].loc[weekday_string_occupants][hour + 1]
                    * month_use
            )
            lighting_appliances_probability = (
                    lighting_appliances_probability_combined_dic[occupancy].loc[weekday_string_lighting][hour + 1]
                    * month_use
            )
            occupancy_probability_df.loc[occupancy][time] = occupancy_probability
            internal_gain_timeseries.append([
                occupancy,
                time,
                occupancy_probability,
                lighting_appliances_probability
            ])

    internal_gain_timeseries_df = pd.DataFrame(
        internal_gain_timeseries,
        columns=[
            'internal_gain_type',
            'time',
            'internal_gain_occupancy',
            'internal_gain_appliances'
        ]
    )

    internal_gain_timeseries_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('building_internal_gain_timeseries'
        ),
        index=False
    )

    return occupancy_probability_df


def write_weather(locator,
        date_and_time_prediction,
        weather_general_info,
        weather_timeseries_initial_df
):
    # TODO: adapt this function to make time steps != 1 hour possible
    location = weather_general_info[0][1]
    date_and_time = []
    wet_bulb_temperature = []
    weather_timeseries = []

    # Time
    row_0 = weather_timeseries_initial_df.loc[0]
    row_end = weather_timeseries_initial_df.loc[weather_timeseries_initial_df.shape[0] - 1]
    start = datetime.datetime(
        int(row_0['year']),
        int(row_0['month']),
        int(row_0['day']),
        int(row_0['hour']) - 1,
        0,
        0
    )
    end = datetime.datetime(
        int(row_end['year']),
        int(row_end['month']),
        int(row_end['day']),
        int(row_end['hour']) - 1,
        0,
        0
    )
    my_date_and_time = pd.date_range(start=start, end=end, freq=pd.to_timedelta('01:00:00'))
    weather_timeseries_initial_df.set_index(my_date_and_time, inplace=True)

    year = int(row_0['year'])
    for index, row in weather_timeseries_initial_df.iterrows():
        # Checking that the files from which the electricity prices are extracted in get_electricity_price.py
        # are the ones of the correct year, for each time step
        if int(row['year']) != year:
            print(
                warnings.warn(
                    'The year changes throughout the prediction horizon, this may cause errors.'
                )
            )
            quit()

        # Wet-bulb temperature calculations
        temperature = float(row['dry_bulb_temperature_C'])
        humidity = float(row['relative_humidity_percent'])
        wet_bulb_temperature_r = (
                temperature
                * math.atan(0.151977 * ((humidity + 8.313659) ** 0.5))
                + math.atan(temperature + humidity)
                - math.atan(humidity - 1.676331)
                + (0.00391838 * (humidity ** (3 / 2)))
                * math.atan(0.023101 * humidity)
                - 4.686035
        )
        wet_bulb_temperature.append([
            index,
            wet_bulb_temperature_r
        ])

        # Weather timeseries
        weather_timeseries.append([
            location,
            index,
            temperature,
            temperature - 13,
            '',
            row['global_horizontal_radiation_Wh_m2'],
            row['global_horizontal_radiation_Wh_m2'],
            row['global_horizontal_radiation_Wh_m2'],
            row['global_horizontal_radiation_Wh_m2'],
            row['global_horizontal_radiation_Wh_m2']
        ])

    # Converting to dataframes
    wet_bulb_temperature_df = pd.DataFrame.from_records(
        wet_bulb_temperature,
        columns=[
            'time',
            'wet_bulb_temperature'
        ])
    wet_bulb_temperature_df.set_index('time', inplace=True)
    weather_timeseries_df = pd.DataFrame.from_records(
        weather_timeseries,
        columns=[
            'weather_type',
            'time',
            'ambient_air_temperature',
            'sky_temperature',
            'ambient_air_humidity_ratio',
            'irradiation_horizontal',
            'irradiation_east',
            'irradiation_south',
            'irradiation_west',
            'irradiation_north'
        ])
    weather_timeseries_df.set_index('time')
    weather_timeseries_df.set_index(my_date_and_time, inplace=True)

    # Reindexing to the date_and_time_prediction that we are using
    wet_bulb_temperature_df = wet_bulb_temperature_df[date_and_time_prediction[0]:date_and_time_prediction[-1]]
    wet_bulb_temperature_df.reindex(index=date_and_time_prediction, method='nearest')
    weather_timeseries_df = weather_timeseries_df[date_and_time_prediction[0]:date_and_time_prediction[-1]]
    weather_timeseries_df.reindex(index=date_and_time_prediction, method='nearest')

    # Writing the CSV file
    weather_timeseries_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('weather_timeseries'
        ),
        index=False
    )

    # Weather type information
    weather_types = [[
        location,
        'Asia/Singapore',  # TODO: Determine timezone dynamically
        float(weather_general_info[0][6]),
        float(weather_general_info[0][7]),
        13,  # TODO: Read from default file
    ]]

    # Converting to dataframe
    weather_types_df = pd.DataFrame.from_records(
        weather_types,
        columns=[
            'weather_type',
            'time_zone',
            'latitude',
            'longitude',
            'temperature_difference_sky_ambient'
        ])

    # Writing the CSV file
    weather_types_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('weather_types'
        ),
        index=False
    )

    return (
        date_and_time,
        year, wet_bulb_temperature_df
    )


def write_building_scenarios(locator,
                             scenario,
                             buildings_names,
                             time_start,
                             time_end,
                             time_step
                             ):
    building_scenarios = []
    for building in buildings_names:
        building_scenarios.append([
            scenario + '/' + building,
            building,
            'parameters_default',
            'linearization_default',
            '',
            '',
            '',
            '',
            time_start,
            time_end,
            time_step
        ])

    building_scenarios_df = pd.DataFrame(
        building_scenarios,
        columns=[
            'scenario_name',
            'building_name',
            'parameter_set',
            'linearization_type',
            'demand_controlled_ventilation_type',
            'co2_model_type',
            'humidity_model_type',
            'heating_cooling_season',
            'time_start',
            'time_end',
            'time_step'
        ])
    building_scenarios_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('building_scenarios'
                                                                      ),
        index=False
    )


def pre_write_building_infiltration_types(
        parameter_set,
        DELTA_P_DIM,
        leakage_envelope_systems_df,
        mean_floor_height_0
):
    building_infiltration_types = []
    for index, row in leakage_envelope_systems_df.iterrows():
        n_inf = (
                0.5 * row['n50']
                * (DELTA_P_DIM / 50)
                ** (2 / 3)
        )  # Air changes per hour [m3/h.m2] formula from CEA > ventilation_air_flows_simple
        infiltration_rate = n_inf / (3600 * mean_floor_height_0)  # [1/s]
        building_infiltration_types.append([
            parameter_set,
            'infiltration_' + index,
            infiltration_rate,
            '1/s',
            ''
        ])

    building_infiltration_types_df = pd.DataFrame(
        building_infiltration_types,
        columns=[
            'parameter_set',
            'parameter_name',
            'parameter_value',
            'parameter_unit',
            'parameter_comment'
        ])

    return building_infiltration_types_df


def pre_write_building_heat_capacity_types(
        parameter_set,
        construction_envelope_systems_df,
        mean_floor_height_0
):
    building_heat_capacity_types = []
    for index, row in construction_envelope_systems_df.iterrows():
        heat_capacity = row['Cm_Af'] / mean_floor_height_0  # From J.K^-1.m^-2 to J.K^-1.m^-3
        building_heat_capacity_types.append([
            parameter_set,
            'heat_capacity_' + index,
            heat_capacity,
            'J/(m3.K)',
            ''
        ])

    building_heat_capacity_types_df = pd.DataFrame(
        building_heat_capacity_types,
        columns=[
            'parameter_set',
            'parameter_name',
            'parameter_value',
            'parameter_unit',
            'parameter_comment'
        ]
    )
    return building_heat_capacity_types_df


def pre_write_heat_transfer_coefficient(
        parameter_set,
        h_e,
        h_i
):
    surface_to_ambient = [
        parameter_set,
        'heat_transfer_coefficient_surface_to_ambient',
        h_e,
        'W/(m2.K)',
        ''
    ]
    surface_to_zone = [
        parameter_set,
        'heat_transfer_coefficient_surface_to_zone',
        h_i,
        'W/(m2.K)',
        ''
    ]

    heat_transfer_coefficient_df = pd.DataFrame(
        [
            surface_to_ambient,
            surface_to_zone
        ],
        columns=[
            'parameter_set',
            'parameter_name',
            'parameter_value',
            'parameter_unit',
            'parameter_comment'
        ])
    return heat_transfer_coefficient_df


def pre_write_constants(
        density_air,
        heat_capacity_air
):
    density_air_list = [
        'constants',
        'density_air',
        density_air,
        'kg/m3',
        ''
    ]
    heat_capacity_air_list = [
        'constants',
        'heat_capacity_air',
        heat_capacity_air,
        'J/(m3.K)',
        ''
    ]
    stefan_boltzmann_constant_list = [
        'constants',
        'stefan_boltzmann_constant',
        '5.670373e-08',
        'W/(m2.K4)',
        ''
    ]

    constants_list_df = pd.DataFrame(
        [
            density_air_list,
            heat_capacity_air_list,
            stefan_boltzmann_constant_list
        ],
        columns=[
            'parameter_set',
            'parameter_name',
            'parameter_value',
            'parameter_unit',
            'parameter_comment'
        ]
    )
    return constants_list_df


def write_building_parameter_sets(locator,
                                  parameter_set,
                                  mean_floor_height_m,
                                  buildings_names,
                                  leakage_envelope_systems_df,
                                  construction_envelope_systems_df,
                                  DELTA_P_DIM,
                                  h_e,
                                  h_i,
                                  density_air,
                                  heat_capacity_air
                                  ):
    # Check whether all the buildings have the same mean floor height
    mean_floor_height_0 = mean_floor_height_m[buildings_names[0]]
    for building in buildings_names:
        if mean_floor_height_m[building] != mean_floor_height_0:
            warnings.warn(
                'The district buildings do not all have the same mean floor height. Please modify the '
                '"pre_write_building_infiltration_types" and the "pre_write_building_heat_capacity_types" functions '
                'so that each building has an infiltration and a heat capacity that are adapted to its mean floor '
                'height.'
            )
            quit()

    # Create the sub-data frames
    building_infiltration_types_df = pre_write_building_infiltration_types(
        parameter_set,
        DELTA_P_DIM,
        leakage_envelope_systems_df,
        mean_floor_height_0
    )
    building_heat_capacity_types_df = pre_write_building_heat_capacity_types(
        parameter_set,
        construction_envelope_systems_df,
        mean_floor_height_0
    )
    heat_transfer_coefficient_df = pre_write_heat_transfer_coefficient(
        parameter_set,
        h_e,
        h_i
    )
    constants_list_df = pre_write_constants(
        density_air,
        heat_capacity_air
    )

    # Create the final data frame
    sub_data_frames = [
        building_infiltration_types_df,
        building_heat_capacity_types_df,
        heat_transfer_coefficient_df,
        constants_list_df
    ]
    building_parameters_sets_df = pd.concat(sub_data_frames)
    building_parameters_sets_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('building_parameter_sets'
                                                                      ),
        index=False
    )


def write_building_linearization_types(locator):
    building_linearization_types = [[
        'linearization_default',
        15,
        25,
        25,
        35,
        15,
        15,
        30,
        17,
        0.0216,
        0.0135,
        100,
        500,
        0.005
    ]]
    building_linearization_types_df = pd.DataFrame(
        building_linearization_types,
        columns=[
            'linearization_type',
            'linearization_zone_air_temperature_heat',
            'linearization_zone_air_temperature_cool',
            'linearization_surface_temperature',
            'linearization_exterior_surface_temperature',
            'linearization_internal_gain_occupancy',
            'linearization_internal_gain_appliances',
            'linearization_ambient_air_temperature',
            'linearization_sky_temperature',
            'linearization_ambient_air_humidity_ratio',
            'linearization_zone_air_humidity_ratio',
            'linearization_irradiation',
            'linearization_co2_concentration',
            'linearization_ventilation_rate_per_square_meter'
        ]
    )
    building_linearization_types_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('building_linearization_types'
                                                                      ),
        index=False
    )


def write_building_zone_types(locator,
                              buildings_names,
                              occupancy_types,
                              zone_occupancy_df,
                              architecture_df,
                              supply_temperature_df,
                              emissions_cooling_type_dic
                              ):
    building_zone_types = []
    for building in buildings_names:
        for occupancy in occupancy_types:
            if zone_occupancy_df.loc[building][occupancy] > 0:
                # Determine whether the building has ahu, aru and/or scu
                if not math.isnan(supply_temperature_df.loc[building]['ahu']):
                    hvac_ahu_type = building + '_' + emissions_cooling_type_dic[building]
                else:
                    hvac_ahu_type = ''
                if not math.isnan(supply_temperature_df.loc[building]['aru']):
                    hvac_aru_type = building + '_' + emissions_cooling_type_dic[building]
                else:
                    hvac_aru_type = ''
                if not math.isnan(supply_temperature_df.loc[building]['scu']):
                    hvac_scu_type = building + '_' + emissions_cooling_type_dic[building]
                else:
                    hvac_scu_type = ''

                # Define row for this building and occupancy
                building_zone_types.append([
                    building + '_' + occupancy,
                    'heat_capacity_' + architecture_df.loc[building]['type_cons'],
                    '',
                    '',
                    'infiltration_' + architecture_df.loc[building]['type_leak'],
                    occupancy,
                    'window_open',
                    'blind_' + architecture_df.loc[building]['type_shade'],
                    hvac_scu_type,
                    hvac_ahu_type,
                    hvac_aru_type,
                    'zone_constraint_default'
                ])

    building_zone_types_df = pd.DataFrame.from_records(
        building_zone_types,
        columns=[
            'zone_type',
            'heat_capacity',
            'base_surface_type',
            'ceiling_surface_type',
            'infiltration_rate',
            'internal_gain_type',
            'window_type',
            'blind_type',
            'hvac_generic_type',
            'hvac_ahu_type',
            'hvac_tu_type',
            'zone_constraint_profile'
        ]
    )

    building_zone_types_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('building_zone_types'),
        index=False
    )

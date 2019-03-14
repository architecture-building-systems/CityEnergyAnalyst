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

import csv
import os

import numpy as np
import pandas as pd
import xlrd
from geopandas import GeoDataFrame as Gdf
from cea.utilities.dbf import dbf_to_dataframe

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def main(locator, weather_path,
         region,
         time_start,
         time_end
         ):
    (
        internal_loads_df,
        indoor_comfort_df,
        construction_envelope_systems_df,
        leakage_envelope_systems_df,
        window_envelope_systems_df,
        roofs_envelope_systems_df,
        wall_envelope_systems_df,
        shading_envelope_systems_df,
        emission_systems_heating_df,
        emission_systems_cooling_df,
        emission_systems_controller_df,
        system_controls_ini_df,
        cooling_generation_df
    ) = extract_cea_databases_files(locator,
                                    region
                                    )
    (
        zone_occupancy_df,
        zone_df,
        architecture_df,
        technical_systems_df,
        supply_systems_df
    ) = extract_cea_inputs_files(locator)
    (
        weather_general_info,
        weather_timeseries_initial_df
    ) = process_weather_file(weather_path)
    (
        occupancy_types_full,
        occupancy_types,
        buildings_names
    ) = extract_common_parameters(
        internal_loads_df,
        zone_occupancy_df
    )
    building_geometry_all = extract_cea_building_geometry(locator,
                                                          buildings_names
                                                          )

    (
        occupancy_types_full_cardinal,
        buildings_cardinal,
        occupancy_types_cardinal
    ) = calculate_cardinals(
        internal_loads_df,
        zone_occupancy_df,
        occupancy_types
    )
    (
        occupants_probability_dic,
        lighting_appliances_probability_dic,
        processes_probability_dic,
        monthly_use_probability_df,
        occupancy_density_m2_p
    ) = process_occupancy_schedules(locator,
                                    region,
                                    occupancy_types,
                                    occupancy_types_cardinal
                                    )
    footprint = calculate_footprint(
        buildings_names,
        building_geometry_all
    )
    (
        gross_floor_area_m2,
        floors_cardinal_df,
        total_gross_floor_area_m2
    ) = calculate_gross_floor_area(
        footprint,
        zone_df,
        buildings_names
    )
    mean_floor_height_m = calculate_mean_floor_height(
        buildings_names,
        zone_df,
        floors_cardinal_df
    )
    system_controls_df = process_system_controls_file(system_controls_ini_df)
    (
        supply_temperature_df,
        emissions_cooling_type_dic,
        emissions_controller_type_dic,
        generation_cooling_code_dic
    ) = synthetize_hvac_properties(
        buildings_names,
        buildings_cardinal,
        technical_systems_df,
        emission_systems_cooling_df,
        supply_systems_df
    )
    (
        occupancy_per_building_cardinal,
        occupancy_per_building_list
    ) = get_occupancy_per_building(
        buildings_names,
        occupancy_types,
        zone_occupancy_df
    )
    (
        T_int_cea_dic,
        T_ext_cea_df
    ) = get_temperatures(locator,
        buildings_names,
        time_start,
        time_end
    )

    return (
        internal_loads_df,
        indoor_comfort_df,
        construction_envelope_systems_df,
        leakage_envelope_systems_df,
        window_envelope_systems_df,
        roofs_envelope_systems_df,
        wall_envelope_systems_df,
        shading_envelope_systems_df,
        emission_systems_heating_df,
        emission_systems_cooling_df,
        emission_systems_controller_df,
        system_controls_ini_df,
        cooling_generation_df,
        zone_occupancy_df,
        zone_df,
        architecture_df,
        technical_systems_df,
        supply_systems_df,
        weather_general_info,
        weather_timeseries_initial_df,
        occupancy_types_full,
        occupancy_types,
        buildings_names,
        building_geometry_all,
        occupancy_types_full_cardinal,
        buildings_cardinal,
        occupancy_types_cardinal,
        occupants_probability_dic,
        lighting_appliances_probability_dic,
        processes_probability_dic,
        monthly_use_probability_df,
        occupancy_density_m2_p,
        footprint,
        gross_floor_area_m2,
        floors_cardinal_df,
        total_gross_floor_area_m2,
        mean_floor_height_m,
        system_controls_df,
        supply_temperature_df,
        emissions_cooling_type_dic,
        emissions_controller_type_dic,
        generation_cooling_code_dic,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        T_int_cea_dic,
        T_ext_cea_df
    )


def extract_cea_databases_files(locator,
                                region
                                ):
    # Get data
    internal_loads_df = pd.read_excel(locator.get_archetypes_properties(region), 'INTERNAL_LOADS')
    indoor_comfort_df = pd.read_excel(locator.get_archetypes_properties(region), 'INDOOR_COMFORT')
    construction_envelope_systems_df = pd.read_excel(locator.get_envelope_systems(region), 'CONSTRUCTION')
    leakage_envelope_systems_df = pd.read_excel(locator.get_envelope_systems(region), 'LEAKAGE')
    window_envelope_systems_df = pd.read_excel(locator.get_envelope_systems(region), 'WINDOW')
    roofs_envelope_systems_df = pd.read_excel(locator.get_envelope_systems(region), 'ROOF')
    wall_envelope_systems_df = pd.read_excel(locator.get_envelope_systems(region), 'WALL')
    shading_envelope_systems_df = pd.read_excel(locator.get_envelope_systems(region), 'SHADING')
    emission_systems_heating_df = pd.read_excel(locator.get_technical_emission_systems(region), 'heating')
    emission_systems_cooling_df = pd.read_excel(locator.get_technical_emission_systems(region), 'cooling')
    emission_systems_controller_df = pd.read_excel(locator.get_technical_emission_systems(region), 'controller')
    system_controls_ini_df = pd.read_excel(locator.get_archetypes_system_controls(region), 'heating_cooling')
    cooling_generation_df = pd.read_excel(locator.get_life_cycle_inventory_supply_systems(region), 'COOLING')

    # Set index
    internal_loads_df.set_index('Code', inplace=True)
    indoor_comfort_df.set_index('Code', inplace=True)
    construction_envelope_systems_df.set_index('code', inplace=True)
    leakage_envelope_systems_df.set_index('code', inplace=True)
    window_envelope_systems_df.set_index('code', inplace=True)
    roofs_envelope_systems_df.set_index('code', inplace=True)
    wall_envelope_systems_df.set_index('code', inplace=True)
    shading_envelope_systems_df.set_index('code', inplace=True)
    emission_systems_heating_df.set_index('code', inplace=True)
    emission_systems_cooling_df.set_index('code', inplace=True)
    emission_systems_controller_df.set_index('code', inplace=True)
    cooling_generation_df.set_index('code', inplace=True)

    return (
        internal_loads_df,
        indoor_comfort_df,
        construction_envelope_systems_df,
        leakage_envelope_systems_df,
        window_envelope_systems_df,
        roofs_envelope_systems_df,
        wall_envelope_systems_df,
        shading_envelope_systems_df,
        emission_systems_heating_df,
        emission_systems_cooling_df,
        emission_systems_controller_df,
        system_controls_ini_df,
        cooling_generation_df
    )


def extract_cea_inputs_files(locator):
    # Get dataframes
    zone_occupancy_df = dbf_to_dataframe(locator.get_building_occupancy())
    zone_df = Gdf.from_file(locator.get_zone_geometry())
    architecture_df = dbf_to_dataframe(locator.get_building_architecture())
    technical_systems_df = dbf_to_dataframe(locator.get_building_hvac())
    supply_systems_df = dbf_to_dataframe(locator.get_building_supply())

    # Set index
    zone_occupancy_df.set_index('Name', inplace=True)
    zone_df.set_index('Name', inplace=True)
    architecture_df.set_index('Name', inplace=True)
    technical_systems_df.set_index('Name', inplace=True)
    supply_systems_df.set_index('Name', inplace=True)

    return zone_occupancy_df, zone_df, architecture_df, technical_systems_df, supply_systems_df


def extract_cea_building_geometry(locator, buildings_names):
    building_geometry_all = {}
    for building in buildings_names:
        building_geometry_all[building] = pd.read_csv(locator.get_radiation_metadata(building))
    return building_geometry_all


def process_weather_file(weather_path):
    # This function deals with the fact that the weather file has an .epw format that is non-pandas dataframe ready.
    # Get data
    with open(weather_path, 'rb') as f:
        reader = csv.reader(f)
        weather_initial = list(reader)

    # Extract the file general information
    weather_general_info = weather_initial[: 8]

    # Extract the weather timeseries
    # The labels of this timeseries can be found at
    # https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.9.0/AuxiliaryPrograms.pdf at 2.9.1
    weather_timeseries_initial = weather_initial[8:]
    weather_timeseries_labels = [
        'year',
        'month',
        'day',
        'hour',
        'minute',
        'data_source',
        'dry_bulb_temperature_C',
        'dew_point_temperature_C',
        'relative_humidity_percent',
        'atmospheric_pressure_Pa',
        'extraterrestrial_horizontal_radiation_Wh_m2',
        'extraterrestrial_direct_normal_radiation_Wh_m2',
        'horizontal_infrared_radiation_intensity_Wh_m2',
        'global_horizontal_radiation_Wh_m2',
        'direct_normal_radiation_Wh_m2',
        'diffuse_horizontal_radiation_Wh_m2',
        'global_horizontal_illuminance_lux',
        'direct_normal_illuminance_lux',
        'diffuse horizontal_illuminance_lux',
        'zenith_luminance_Cd_m2',
        'wind_direction_degrees',
        'wind_speed_m_s',
        'total_sky_cover_tenths',
        'opaque_sky_cover_tenths',
        'visibility_km',
        'ceiling_height_m',
        'present_weather_observation',
        'present_weather_codes',
        'precipitable_water_mm',
        'aerosol_optical_depth_thousands',
        'snow_depth_cm',
        'days_since_last_snowfall',
        'albedo',
        'liquid_precipitation_depth_mm',
        'liquid_precipitation_quantity_hour'
    ]
    weather_timeseries_initial_df = pd.DataFrame.from_records(
        weather_timeseries_initial,
        columns=weather_timeseries_labels
    )

    return weather_general_info, weather_timeseries_initial_df


def process_occupancy_schedules(
        locator,
        region,
        occupancy_types,
        occupancy_types_cardinal
):
    # This function makes the data from the occupancy schedule file more readable and pandas dataframe-ready.
    # Get data
    book = xlrd.open_workbook(locator.get_archetypes_schedules(region))

    # Get occupancy types schedules
    occupancy_schedules = {}
    for occupancy in occupancy_types:
        occupancy_data = book.sheet_by_name(occupancy)
        occupancy_cardinal = occupancy_data.nrows
        occupancy_list = []
        for j in range(occupancy_cardinal):
            occupancy_schedules_j = occupancy_data.row_values(j)
            occupancy_list.append(occupancy_schedules_j)
        occupancy_schedules[occupancy] = occupancy_list

    # Get indexes
    index_occupancy = {}
    index_lighting_appliances = {}
    index_monthly_use = {}
    index_occupancy_density = {}
    index_process = {}
    for i in range(occupancy_types_cardinal):
        occupancy = occupancy_types[i]
        for j in range(len(occupancy_schedules[occupancy])):
            if str(occupancy_schedules[occupancy][j][1]) == 'Probability of  occupancy (daily)':
                index_occupancy[occupancy] = j
            if str(occupancy_schedules[occupancy][j][1]) == 'Probability of use of lighting and appliances (daily)':
                index_lighting_appliances[occupancy] = j
            if str(occupancy_schedules[occupancy][j][1]) == 'Probability of use  (monthly)':
                index_monthly_use[occupancy] = j
            if str(occupancy_schedules[occupancy][j][1]) == 'Occupancy density (m2/p)':
                index_occupancy_density[occupancy] = j
            if str(occupancy_schedules[occupancy][j][1]) == 'Probability of processes (daily)':
                index_process[occupancy] = j

        # Check that all the indexes have been found
        if len(index_occupancy) != i + 1:
            raise ValueError(
                'No Probability of occupancy (daily) found for occupancy type '
                + str(i) + ' in occupancy_schedules.xlsx. Please check the spelling'
            )
        if len(index_lighting_appliances) != i + 1:
            raise ValueError(
                'No Probability of use of lighting and appliances (daily) found for occupancy type '
                + str(i) + ' in occupancy_schedules.xlsx. Please check the spelling.'
            )
        if len(index_monthly_use) != i + 1:
            raise ValueError(
                'No Probability of use (monthly) found for occupancy type '
                + str(i) + ' in occupancy_schedules.xlsx. Please check the spelling.'
            )
        if len(index_occupancy_density) != i + 1:
            raise ValueError(
                'No Occupancy density found for occupancy type '
                + str(i) + ' in occupancy_schedules.xlsx. Please check the spelling.'
            )

    # Define labels
    label_day = range(1, 25)
    label_day.insert(0, 'day_of_week')
    label_month = range(1, 13)
    label_month.insert(0, 'Code')

    # Get probability of occupancy
    occupants_probability_dic = {}
    for occupancy in occupancy_types:
        occupants_probability_occ = (
            occupancy_schedules[occupancy][index_occupancy[occupancy] + 2: index_occupancy[occupancy] + 5]
        )
        occupants_probability_occ_df = pd.DataFrame.from_records(occupants_probability_occ, columns=label_day)
        occupants_probability_occ_df.set_index('day_of_week', inplace=True)
        occupants_probability_dic[occupancy] = occupants_probability_occ_df

    # Get probability of use of lighting and appliances
    lighting_appliances_probability_dic = {}
    for occupancy in occupancy_types:
        lighting_appliances_probability_occ = (
            occupancy_schedules[occupancy][
            index_lighting_appliances[occupancy] + 2: index_lighting_appliances[occupancy] + 5
            ]
        )
        lighting_appliances_probability_occ_df = pd.DataFrame.from_records(
            lighting_appliances_probability_occ,
            columns=label_day
        )
        lighting_appliances_probability_occ_df.set_index('day_of_week', inplace=True)
        lighting_appliances_probability_dic[occupancy] = lighting_appliances_probability_occ_df

    # Get probability of processes (if existing)
    processes_probability_dic = {}
    for occupancy in occupancy_types:
        if occupancy in index_process:
            processes_probability_occ = (
                occupancy_schedules[occupancy][index_process[occupancy] + 2: index_process[occupancy] + 5]
            )
            processes_probability_occ_df = pd.DataFrame.from_records(processes_probability_occ, columns=label_day)
            processes_probability_occ_df.set_index('day_of_week', inplace=True)
            processes_probability_dic[occupancy] = processes_probability_occ_df

    # Get probability of use (monthly)
    monthly_use_probability = []
    for occupancy in occupancy_types:
        monthly_use_probability_occ = occupancy_schedules[occupancy][index_monthly_use[occupancy] + 2][1:13]
        monthly_use_probability_occ.insert(0, occupancy)
        monthly_use_probability.append(monthly_use_probability_occ)

    monthly_use_probability_df = pd.DataFrame(monthly_use_probability, columns=label_month)
    monthly_use_probability_df.set_index('Code', inplace=True)

    # Get occupancy density (m2/p)
    occupancy_density_m2_p = {}
    for occupancy in occupancy_types:
        occupancy_density_occ = occupancy_schedules[occupancy][index_occupancy_density[occupancy] + 1][1]
        occupancy_density_m2_p[occupancy] = occupancy_density_occ

    return (
        occupants_probability_dic,
        lighting_appliances_probability_dic,
        processes_probability_dic,
        monthly_use_probability_df,
        occupancy_density_m2_p
    )


def extract_common_parameters(
        internal_loads_df,
        zone_occupancy_df
):
    occupancy_types_full = internal_loads_df.index
    occupancy_types = zone_occupancy_df.columns
    buildings_names = zone_occupancy_df.index

    return (
        occupancy_types_full,
        occupancy_types,
        buildings_names
    )


def calculate_cardinals(
        internal_loads_df,
        zone_occupancy_df,
        occupancy_types
):
    occupancy_types_full_cardinal = internal_loads_df.shape[0]
    buildings_cardinal = zone_occupancy_df.shape[0]
    occupancy_types_cardinal = len(occupancy_types)

    return (
        occupancy_types_full_cardinal,
        buildings_cardinal,
        occupancy_types_cardinal
    )


def calculate_footprint(
        buildings_names,
        building_geometry_all
):
    footprint = {}
    for building in buildings_names:
        footprint[building] = (
            building_geometry_all[building][building_geometry_all[building]['TYPE'] == 'roofs'].sum()['AREA_m2']
        )

    return footprint


def calculate_gross_floor_area(
        footprint,
        zone_df,
        buildings_names
):
    floors_cardinal_df = zone_df['floors_bg'] + zone_df['floors_ag']
    gross_floor_area_m2 = {}
    for building in buildings_names:
        gross_floor_area_m2[building] = footprint[building] * floors_cardinal_df[building]

    total_gross_floor_area_m2 = sum(gross_floor_area_m2.values())

    return gross_floor_area_m2, floors_cardinal_df, total_gross_floor_area_m2


def calculate_mean_floor_height(
        buildings_names,
        zone_df,
        floors_cardinal_df
):
    mean_floor_height_m = {}
    for building in buildings_names:
        mean_floor_height_m[building] = (
                (
                        float(zone_df.loc[building]['height_bg'])
                        + float(zone_df.loc[building]['height_ag'])
                )
                / float(floors_cardinal_df[building])
        )
    return mean_floor_height_m


def process_system_controls_file(system_controls_ini_df):
    # This function extracts the data in a format that will be easier to handle afterwards.
    heating_season_start_month = (
            int(system_controls_ini_df.loc[0]['heating-season-start'][0])
            * 10
            + int(system_controls_ini_df.loc[0]['heating-season-start'][1])
    )
    heating_season_start_day = (
            int(system_controls_ini_df.loc[0]['heating-season-start'][3])
            * 10
            + int(system_controls_ini_df.loc[0]['heating-season-start'][4])
    )
    heating_season_end_month = (
            int(system_controls_ini_df.loc[0]['heating-season-end'][0])
            * 10
            + int(system_controls_ini_df.loc[0]['heating-season-end'][1])
    )
    heating_season_end_day = (
            int(system_controls_ini_df.loc[0]['heating-season-end'][3])
            * 10
            + int(system_controls_ini_df.loc[0]['heating-season-end'][4])
    )
    cooling_season_start_month = (
            int(system_controls_ini_df.loc[0]['cooling-season-start'][0])
            * 10
            + int(system_controls_ini_df.loc[0]['cooling-season-start'][1])
    )
    cooling_season_start_day = (
            int(system_controls_ini_df.loc[0]['cooling-season-start'][3])
            * 10
            + int(system_controls_ini_df.loc[0]['cooling-season-start'][4])
    )
    cooling_season_end_month = (
            int(system_controls_ini_df.loc[0]['cooling-season-end'][0])
            * 10
            + int(system_controls_ini_df.loc[0]['cooling-season-end'][1])
    )
    cooling_season_end_day = (
            int(system_controls_ini_df.loc[0]['cooling-season-end'][3])
            * 10
            + int(system_controls_ini_df.loc[0]['cooling-season-end'][4])
    )

    system_controls_df = pd.DataFrame.from_records(
        [[
            system_controls_ini_df.loc[0]['has-heating-season'],
            heating_season_start_month,
            heating_season_start_day,
            heating_season_end_month,
            heating_season_end_day,
            system_controls_ini_df.loc[0]['has-cooling-season'],
            cooling_season_start_month,
            cooling_season_start_day,
            cooling_season_end_month,
            cooling_season_end_day
        ]],
        columns=[
            'has_heating_season',
            'heating_season_start_month',
            'heating_season_start_day',
            'heating_season_end_month',
            'heating_season_end_day',
            'has_cooling_season',
            'cooling_season_start_month',
            'cooling_season_start_day',
            'cooling_season_end_month',
            'cooling_season_end_day'
        ]
    )

    return system_controls_df


def synthetize_hvac_properties(
        buildings_names,
        buildings_cardinal,
        technical_systems_df,
        emission_systems_cooling_df,
        supply_systems_df
):
    emissions_cooling_type_dic = {}
    emissions_controller_type_dic = {}
    generation_cooling_code_dic = {}
    supply_temperature_df = pd.DataFrame(
        np.zeros((buildings_cardinal, 3)),
        buildings_names,
        [
            'ahu',
            'aru',
            'scu'
        ]
    )
    for building in buildings_names:
        emissions_cooling_type_dic[building] = technical_systems_df.loc[building]['type_cs']
        emissions_controller_type_dic[building] = technical_systems_df.loc[building]['type_ctrl']
        generation_cooling_code_dic[building] = supply_systems_df.loc[building, 'type_cs']
        for sys in ['ahu', 'aru', 'scu']:
            supply_temperature_df.loc[building][sys] = emission_systems_cooling_df.loc[
                emissions_cooling_type_dic[building], 'Tscs0_' + sys + '_C']

    return (
        supply_temperature_df,
        emissions_cooling_type_dic,
        emissions_controller_type_dic,
        generation_cooling_code_dic
    )


def get_occupancy_per_building(
        buildings_names,
        occupancy_types,
        zone_occupancy_df
):
    occupancy_per_building_cardinal = {}
    occupancy_per_building_list = {}
    for building in buildings_names:
        counter_build = 0
        list_build = []
        for occupancy in occupancy_types:
            if zone_occupancy_df.loc[building][occupancy] > 0:
                counter_build += 1
                list_build.append(occupancy)
        occupancy_per_building_cardinal[building] = counter_build
        occupancy_per_building_list[building] = list_build

    return (
        occupancy_per_building_cardinal,
        occupancy_per_building_list
    )


def get_temperatures(
        locator,
        buildings_names,
        time_start,
        time_end
):
    """
    Get interior and exterior temperatures from CEA demand calculations

    Previous name: compare_with_cea
    """
    T_int_cea_dic = {}
    for building in buildings_names:
        # Get data
        building_demand_cea_build_df = pd.read_csv(locator.get_demand_results_file(building))
        building_demand_cea_build_df.set_index('DATE', inplace=True)
        building_demand_cea_build_df.index = pd.to_datetime(building_demand_cea_build_df.index)

        T_int_build_df = building_demand_cea_build_df.loc[time_start:time_end, 'T_int_C']
        if building == buildings_names[0]:
            T_ext_cea_df = building_demand_cea_build_df.loc[time_start:time_end, 'T_ext_C']

        T_int_cea_dic[building] = T_int_build_df

    return (
        T_int_cea_dic,
        T_ext_cea_df
    )

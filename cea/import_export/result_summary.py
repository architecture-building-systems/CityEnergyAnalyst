"""
Read and summarise CEA results over all scenarios in a project.

"""

import os
import pandas as pd
import cea.config
import time
from datetime import datetime
import cea.inputlocator

__author__ = "Zhongming Shi, Reynold Mok"
__copyright__ = "Copyright 2024, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi, Reynold Mok"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def get_hours_start_end(config):

    # get the user-defined dates from config
    date_start = config.result_summary.period_start_date
    date_end = config.result_summary.period_end_date

    def check_user_period_validity(date):
        s = "".join(date)
        # Check for length, alphanumeric, and the presence of both letters and numbers
        return len(s) == 5 and s.isalnum() and any(c.isalpha() for c in s) and any(c.isdigit() for c in s)
    def check_user_period_impossible_date(date):
        list_impossible_dates = ['30Feb', '31Feb', '31Apr', '31Jun', '31Sep', '31Nov',
                                 'Feb30', 'Feb31', 'Apr31', 'Jun31', 'Sep31', 'Nov31']
        s = "".join(date)
        return s in list_impossible_dates

    def check_user_period_leap_date(date):
        list_leap_dates = ['29Feb', 'Feb29']
        s = "".join(date)
        return s in list_leap_dates

    def from_date_string_to_hours(list_date):
        # Define possible date formats to handle both "31Jan" and "Jan31"
        formats = ["%d%b", "%b%d"]

        # Convert list of date elements into string
        date_str = "".join(list_date)

        # Try each format to parse the date
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError("Check start date or/and end date of the defined period.")

        # Calculate the day of the year (1-365)
        day_of_year = date_obj.timetuple().tm_yday

        # Calculate the Nth hour of the year
        hour_of_year = (day_of_year - 1) * 24  # (day - 1) because days start from hour 0, not 24

        return hour_of_year

    # validate start date
    if not check_user_period_validity(date_start):
        raise ValueError('Check the start date. Select one number and one month only.')

    elif check_user_period_impossible_date(date_start):
        raise ValueError('Check the start date. Ensure the combination is an actual date.')

    elif check_user_period_leap_date(date_start):
        raise ValueError('Check the start date. CEA does not consider 29 Feb in a leap year.')

    # validate end date
    if not check_user_period_validity(date_end):
        raise ValueError('Check the end date. Select one number and one month only.')

    elif check_user_period_impossible_date(date_end):
        raise ValueError('Check the end date. Ensure the combination is an actual date.')

    elif check_user_period_leap_date(date_end):
        raise ValueError('Check the end date. CEA does not consider 29 Feb in a leap year.')

    hour_start = from_date_string_to_hours(date_start) #Nth hour of the year, starting at 0, inclusive
    hour_end = from_date_string_to_hours(date_end) + 24  #Nth hour of the year, ending at 8760, not-inclusive

    return hour_start, hour_end

def map_metrics_cea_features(list_metrics):

    dict = {
    "architecture": ['conditioned_floor_area[m2]','roof_area[m2]','gross_floor_area[m2]','occupied_floor_area[m2]'],
    "demand": ['nominal_occupancy[-]','grid_electricity_consumption[MWh]','enduse_electricity_consumption[MWh]',
               'enduse_cooling_demand[MWh]','enduse_space_cooling_demand[MWh]','enduse_heating_demand[MWh]',
               'enduse_space_heating_demand[MWh]','enduse_dhw_demand[MWh]'],
    "embodied_emissions": ['embodied_emissions_building_construction[tonCO2-eq/yr]'],
    "operation_emissions": ['operation_emissions[tonCO2-eq/yr]', 'operation_emissions_grid[tonCO2-eq/yr]'],
    "pv": ['pv_installed_area_total[m2]','pv_electricity_total[kWh]','pv_installed_area_roof[m2]',
           'pv_electricity_roof[kWh]','pv_installed_area_north[m2]','pv_electricity_north[kWh]',
           'pv_installed_area_south[m2]','pv_electricity_south[kWh]','pv_installed_area_east[m2]',
           'pv_electricity_east[kWh]','pv_installed_area_west[m2]','pv_electricity_west[kWh]'],
    "pvt": ['pvt_installed_area_total[m2]','pvt_electricity_total[kWh]','pvt_heat_total[kWh]',
            'pvt_installed_area_roof[m2]','pvt_electricity_roof[kWh]','pvt_heat_roof[kWh]',
            'pvt_installed_area_north[m2]','pvt_electricity_north[kWh]','pvt_heat_north[kWh]',
            'pvt_installed_area_south[m2]','pvt_electricity_south[kWh]','pvt_heat_south[kWh]',
            'pvt_installed_area_east[m2]','pvt_electricity_east[kWh]','pvt_heat_east[kWh]',
            'pvt_installed_area_west[m2]','pvt_electricity_west[kWh]','pvt_heat_west[kWh]'],
    "sc_et": ['sc_et_installed_area_total[m2]','sc_et_heat_total[kWh]',
              'sc_et_installed_area_roof[m2]','sc_et_heat_roof[kWh]',
              'sc_et_installed_area_north[m2]','sc_et_heat_north[kWh]',
              'sc_et_installed_area_south[m2]','sc_et_heat_south[kWh]',
              'sc_et_installed_area_east[m2]','sc_et_heat_east[kWh]',
              'sc_et_installed_area_west[m2]','sc_et_heat_west[kWh]'],
    "sc_fp": ['sc_fp_installed_area_total[m2]','sc_fp_heat_total[kWh]',
              'sc_fp_installed_area_roof[m2]','sc_fp_heat_roof[kWh]',
              'sc_fp_installed_area_north[m2]','sc_fp_heat_north[kWh]',
              'sc_fp_installed_area_south[m2]','sc_fp_heat_south[kWh]',
              'sc_fp_installed_area_east[m2]','sc_fp_heat_east[kWh]',
              'sc_fp_installed_area_west[m2]','sc_fp_heat_west[kWh]'],
    "other_renewables": ['geothermal_heat_potential[kWh]','area_for_ground_source_heat_pump[m2]',
                         'sewage_heat_potential[kWh]','water_body_heat_potential[kWh]'],
    "dh": ['DH_plant_thermal_load[kWh]','DH_plant_power[kW]',
                         'DH_electricity_consumption_for_pressure_loss[kWh]','DH_plant_pumping_power[kW]'],
    "dc": ['DC_plant_thermal_load[kWh]','DC_plant_power[kW]',
                         'DC_electricity_consumption_for_pressure_loss[kWh]','DC_plant_pumping_power[kW]'],
    }

    for cea_feature, attached_list in dict.items():
        if set(list_metrics).issubset(set(attached_list)):
            return cea_feature
    return None

def get_results_path(locator, config, cea_feature):

    selected_buildings = config.result_summary.buildings
    network_names_DH = config.result_summary.networks_dh
    network_names_DC = config.result_summary.networks_dc

    list_paths = []

    if cea_feature == 'architecture':
        path = locator.get_total_demand()
        list_paths.append(path)

    elif cea_feature == 'demand':
        for building in selected_buildings:
            path = locator.get_demand_results_file(building)
            list_paths.append(path)

    elif cea_feature == 'embodied_emissions':
        path = locator.get_lca_embodied()
        list_paths.append(path)

    elif cea_feature == 'operation_emissions':
        path = locator.get_lca_operation()
        list_paths.append(path)

    if cea_feature == 'pv':
        for building in selected_buildings:
            path = locator.PV_results(building, panel_type)
            list_paths.append(path)

    if cea_feature == 'pvt':
        for building in selected_buildings:
            path = locator.PVT_results(building)
            list_paths.append(path)

    if cea_feature == 'sc-et':
        for building in selected_buildings:
            path = locator.SC_results(building, 'ET')
            list_paths.append(path)

    if cea_feature == 'sc-fp':
        for building in selected_buildings:
            path = locator.SC_results(building, 'FP')
            list_paths.append(path)

    if cea_feature == 'other_renewables':
        path_geothermal = locator.get_geothermal_potential()
        list_paths.append(path_geothermal)
        path_sewage_heat = locator.get_sewage_heat_potential()
        list_paths.append(path_sewage_heat)
        path_water_body = locator.get_water_body_potential()
        list_paths.append(path_water_body)

    if cea_feature == 'dh':
        for network in network_names_DH:
            path_thermal = locator.get_thermal_network_plant_heat_requirement_file('DH', network, representative_week=False)
            list_paths.append(path_thermal)
            path_pump = locator.get_network_energy_pumping_requirements_file('DH', network, representative_week=False)
            list_paths.append(path_pump)

    if cea_feature == 'dc':
        for network in network_names_DC:
            path_thermal = locator.get_thermal_network_plant_heat_requirement_file('DC', network, representative_week=False)
            list_paths.append(path_thermal)
            path_pump = locator.get_network_energy_pumping_requirements_file('DC', network, representative_week=False)
            list_paths.append(path_pump)

    return list_paths

def map_metrics_and_cea_columns(input_list, direction="metrics_to_columns"):
    """
    Maps between metrics and CEA column names based on the direction.

    Parameters:
    - input_list (list): A list of metrics or CEA column names to map.
    - direction (str): Direction of mapping:
        - "metrics_to_columns": Maps metrics to CEA column names.
        - "columns_to_metrics": Maps CEA column names to metrics.

    Returns:
    - list: A list of mapped values (CEA column names or metrics).

    Raises:
    - ValueError: If an unmapped value is encountered or if the direction is invalid.
    """
    mapping_dict = {
        'conditioned_floor_area[m2]': ['Af_m2'],
        'roof_area[m2]': ['Aroof_m2'],
        'gross_floor_area[m2]': ['GFA_m2'],
        'occupied_floor_area[m2]': ['Aocc_m2'],
        'nominal_occupancy[-]': ['people'],
        'grid_electricity_consumption[MWh]': ['GRID_kWh'],
        'enduse_electricity_consumption[MWh]': ['E_sys_kWh'],
        'enduse_cooling_demand[MWh]': ['QC_sys_kWh'],
        'enduse_space_cooling_demand[MWh]': ['Qcs_sys_kWh'],
        'enduse_heating_demand[MWh]': ['QH_sys_kWh'],
        'enduse_space_heating_demand[MWh]': ['Qhs_sys_kWh'],
        'enduse_dhw_demand[MWh]': ['Qww_kWh'],
        'embodied_emissions_building_construction[tonCO2-eq/yr]': ['GHG_sys_embodied_tonCO2yr'],
        'operation_emissions[tonCO2-eq/yr]': ['GHG_sys_tonCO2'],
        'operation_emissions_grid[tonCO2-eq/yr]': ['GRID_tonCO2'],
        'pv_installed_area_total[m2]': ['Area_PV_m2'],
        'pv_electricity_total[kWh]': ['E_PV_gen_kWh'],
        'pv_installed_area_roof[m2]': ['PV_roofs_top_m2'],
        'pv_electricity_roof[kWh]': ['PV_roofs_top_E_kWh'],
        'pv_installed_area_north[m2]': ['PV_walls_north_m2'],
        'pv_electricity_north[kWh]': ['PV_walls_north_E_kWh'],
        'pv_installed_area_south[m2]': ['PV_walls_south_m2'],
        'pv_electricity_south[kWh]': ['PV_walls_south_E_kWh'],
        'pv_installed_area_east[m2]': ['PV_walls_east_m2'],
        'pv_electricity_east[kWh]': ['PV_walls_east_E_kWh'],
        'pv_installed_area_west[m2]': ['PV_walls_west_m2'],
        'pv_electricity_west[kWh]': ['PV_walls_west_E_kWh'],
        'pvt_installed_area_total[m2]': ['Area_PVT_m2'],
        'pvt_electricity_total[kWh]': ['E_PVT_gen_kWh'],
        'pvt_heat_total[kWh]': ['Q_PVT_gen_kWh'],
        'pvt_installed_area_roof[m2]': ['PVT_roofs_top_m2'],
        'pvt_electricity_roof[kWh]': ['PVT_roofs_top_E_kWh'],
        'pvt_heat_roof[kWh]': ['PVT_roofs_top_Q_kWh'],
        'pvt_installed_area_north[m2]': ['PVT_walls_north_m2'],
        'pvt_electricity_north[kWh]': ['PVT_walls_north_E_kWh'],
        'pvt_heat_north[kWh]': ['PVT_walls_north_Q_kWh'],
        'pvt_installed_area_south[m2]': ['PVT_walls_south_m2'],
        'pvt_electricity_south[kWh]': ['PVT_walls_south_E_kWh'],
        'pvt_heat_south[kWh]': ['PVT_walls_south_Q_kWh'],
        'pvt_installed_area_east[m2]': ['PVT_walls_east_m2'],
        'pvt_electricity_east[kWh]': ['PVT_walls_east_E_kWh'],
        'pvt_heat_east[kWh]': ['PVT_walls_east_Q_kWh'],
        'pvt_installed_area_west[m2]': ['PVT_walls_west_m2'],
        'pvt_electricity_west[kWh]': ['PVT_walls_west_E_kWh'],
        'pvt_heat_west[kWh]': ['PVT_walls_west_Q_kWh'],
        'sc_et_installed_area_total[m2]': ['Area_SC_m2'],
        'sc_et_heat_total[kWh]': ['Q_SC_gen_kWh'],
        'sc_et_installed_area_roof[m2]': ['SC_ET_roofs_top_m2'],
        'sc_et_heat_roof[kWh]': ['SC_ET_roofs_top_Q_kWh'],
        'sc_et_installed_area_north[m2]': ['SC_ET_walls_north_m2'],
        'sc_et_heat_north[kWh]': ['SC_ET_walls_north_Q_kWh'],
        'sc_et_installed_area_south[m2]': ['SC_ET_walls_south_m2'],
        'sc_et_heat_south[kWh]': ['SC_ET_walls_south_Q_kWh'],
        'sc_et_installed_area_east[m2]': ['SC_ET_walls_east_m2'],
        'sc_et_heat_east[kWh]': ['SC_ET_walls_east_Q_kWh'],
        'sc_et_installed_area_west[m2]': ['SC_ET_walls_west_m2'],
        'sc_et_heat_west[kWh]': ['SC_ET_walls_west_Q_kWh'],
        'sc_fp_installed_area_total[m2]': ['Area_SC_m2'],
        'sc_fp_heat_total[kWh]': ['Q_FP_gen_kWh'],
        'sc_fp_installed_area_roof[m2]': ['SC_FP_roofs_top_m2'],
        'sc_fp_heat_roof[kWh]': ['SC_FP_roofs_top_Q_kWh'],
        'sc_fp_installed_area_north[m2]': ['SC_FP_walls_north_m2'],
        'sc_fp_heat_north[kWh]': ['SC_FP_walls_north_Q_kWh'],
        'sc_fp_installed_area_south[m2]': ['SC_FP_walls_south_m2'],
        'sc_fp_heat_south[kWh]': ['SC_FP_walls_south_Q_kWh'],
        'sc_fp_installed_area_east[m2]': ['SC_FP_walls_east_m2'],
        'sc_fp_heat_east[kWh]': ['SC_FP_walls_east_Q_kWh'],
        'sc_fp_installed_area_west[m2]': ['SC_FP_walls_west_m2'],
        'sc_fp_heat_west[kWh]': ['SC_FP_walls_west_Q_kWh'],
        'geothermal_heat_potential[kWh]': ['QGHP_kW'],
        'area_for_ground_source_heat_pump[m2]': ['Area_avail_m2'],
        'sewage_heat_potential[kWh]': ['Qsw_kW'],
        'water_body_heat_potential[kWh]': ['QLake_kW'],
        'DH_plant_thermal_load[kWh]': ['thermal_load_kW'],
        'DH_plant_power[kW]': ['thermal_load_kW'],
        'DH_electricity_consumption_for_pressure_loss[kWh]': ['pressure_loss_total_kW'],
        'DH_plant_pumping_power[kW]': ['pressure_loss_total_kW'],
        'DC_plant_thermal_load[kWh]': ['thermal_load_kW'],
        'DC_plant_power[kW]': ['thermal_load_kW'],
        'DC_electricity_consumption_for_pressure_loss[kWh]': ['pressure_loss_total_kW'],
        'DC_plant_pumping_power[kW]': ['pressure_loss_total_kW'],
    }

    # Reverse the mapping if direction is "columns_to_metrics"
    if direction == "columns_to_metrics":
        mapping_dict = {cea_col: metric for metric, cea_cols in mapping_dict.items() for cea_col in cea_cols}

    # Perform the mapping
    output_set = set()
    for item in input_list:
        if item in mapping_dict:
            # Add the mapped value(s) (handle lists or single items)
            mapped_value = mapping_dict[item]
            if isinstance(mapped_value, list):
                output_set.update(mapped_value)
            else:
                output_set.add(mapped_value)
        else:
            raise ValueError(f"Unrecognized value in the input list: {item}")

    return list(output_set)


def load_cea_results_csv_files(list_paths, list_cea_column_names):
    """
    Iterates over a list of file paths, loads DataFrames from existing .csv files,
    and returns a list of these DataFrames.

    Parameters:
    - file_paths (list of str): List of file paths to .csv files.

    Returns:
    - list of pd.DataFrame: A list of DataFrames for files that exist.
    """
    list_dataframes = []
    selected_columns = ['DATE'] + list_cea_column_names
    for path in list_paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)  # Load the CSV file into a DataFrame
                df = df[selected_columns]
                df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
                list_dataframes.append(df)  # Add the DataFrame to the list
            except Exception as e:
                print(f"Error loading {path}: {e}")
        else:
            print(f"File not found: {path}")

    return list_dataframes


def aggregate_dataframes(dataframes):
    """
    Aggregates a list of DataFrames by summing or averaging cells based on column name conditions:
    - Columns containing "m2": Take the mean.
    - Columns containing "load_kW": Sum and create a new column ending with "power_kW" with max values.
    - Other columns: Sum.

    Parameters:
    - dataframes (list of pd.DataFrame): List of DataFrames to aggregate.

    Returns:
    - pd.DataFrame: Aggregated DataFrame.
    """
    # Ensure there are DataFrames to aggregate
    if not dataframes:
        raise ValueError("The list of DataFrames is empty.")

    # Start with the first DataFrame as a base
    aggregated_df = dataframes[0].copy()

    # List of columns excluding 'DATE'
    columns_to_iterate = [col for col in aggregated_df.columns if col != 'DATE']

    # Iterate through the remaining DataFrames and sum/average corresponding columns
    for df in dataframes[1:]:
        for col in columns_to_iterate:
            if "m2" in col:
                aggregated_df[col] = aggregated_df[col] + df[col]
            elif "load_kW" in col:
                aggregated_df[col] = aggregated_df[col] + df[col]
            else:
                aggregated_df[col] = aggregated_df[col] + df[col]

    # Post-process "m2" columns (take the mean)
    for col in aggregated_df.columns:
        if "m2" in col:
            aggregated_df[col] = aggregated_df[col] / len(dataframes)

    # Post-process "load_kW" columns (create corresponding "power_kW" columns)
    for col in aggregated_df.columns:
        if "load_kW" in col:
            power_col = col.replace("load_kW", "power_kW")
            aggregated_df[power_col] = max(df[col].max() for df in dataframes)

    return aggregated_df

def exec_read_and_summarise_hourly_8760(config, locator,list_metrics):

    # map the CEA Feature for the selected metrics
    cea_feature = map_metrics_cea_features(list_metrics)

    # locate the path(s) to the results of the CEA Feature
    list_paths = get_results_path(locator, config, cea_feature)

    # get the relevant CEA column names based on selected metrics
    list_cea_column_names = map_metrics_and_cea_columns(list_metrics, direction="metrics_to_columns")

    # get the useful CEA results for the user-selected metrics and hours
    list_useful_cea_results = load_cea_results_csv_files(list_paths, list_cea_column_names)

    # aggregate these results
    df_aggregated_results_hourly_8760 = aggregate_dataframes(list_useful_cea_results)

    return df_aggregated_results_hourly_8760

def slice_hourly_results_time_period(df, hour_start, hour_end):
    """
    Slices a DataFrame based on hour_start and hour_end.
    If hour_start > hour_end, wraps around the year:
    - Keeps rows from Hour 0 to hour_end
    - Keeps rows from hour_start to Hour 8760

    Parameters:
    - df (pd.DataFrame): The DataFrame to slice (8760 rows, 1 per hour).
    - hour_start (int): The starting hour (0 to 8759).
    - hour_end (int): The ending hour (0 to 8759).

    Returns:
    - pd.DataFrame: The sliced DataFrame.
    """
    if hour_start <= hour_end:
        # Normal case: Slice rows from hour_start to hour_end
        return df.iloc[hour_start:hour_end + 1]
    else:
        # Wrapping case: Combine two slices (0 to hour_end and hour_start to 8760)
        top_slice = df.iloc[0:hour_end + 1]
        bottom_slice = df.iloc[hour_start:8760]
        return pd.concat([bottom_slice, top_slice])


def aggregate_by_period(df, period, date_column='DATE'):
    """
    Aggregates a DataFrame by a given time period.

    Parameters:
    - df (pd.DataFrame): The input DataFrame.
    - period (str): Aggregation period ('monthly', 'seasonally', 'annually').
    - date_column (str): Name of the date column.

    Returns:
    - pd.DataFrame: Aggregated DataFrame.
    """
    df[date_column] = pd.to_datetime(df[date_column])

    if period == 'monthly':
        df['period'] = df[date_column].dt.month
        period_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        df['period'] = df['period'].apply(lambda x: period_names[x - 1])

        df['period'] = pd.Categorical(df['period'], categories=period_names, ordered=True)
        df = df.sort_values(by=['period'])

    elif period == 'seasonally':
        season_mapping = {
            1: 'Winter', 2: 'Winter', 12: 'Winter',
            3: 'Spring', 4: 'Spring', 5: 'Spring',
            6: 'Summer', 7: 'Summer', 8: 'Summer',
            9: 'Autumn', 10: 'Autumn', 11: 'Autumn',
        }
        period_names = ['Winter', 'Spring', 'Summer', 'Autumn']
        df['period'] = df[date_column].dt.month.map(season_mapping)

        df['period'] = pd.Categorical(df['period'], categories=period_names, ordered=True)
        df = df.sort_values(by=['period'])

    elif period == 'annually':
        df['period'] = df[date_column].dt.year

    return df.groupby('period').sum(numeric_only=True).reset_index()

def exec_aggregate_time_period(config, df_aggregated_results_hourly_8760, list_aggregate_by_time_period):

    # get the start (inclusive) and end (not-inclusive) hours
    hour_start, hour_end = get_hours_start_end(config)

    results = []

    if 'hourly' in list_aggregate_by_time_period:
        results.append(df_aggregated_results_hourly_8760)

    if 'monthly' in list_aggregate_by_time_period:
        df_monthly = aggregate_by_period(df_aggregated_results_hourly_8760, 'monthly', date_column='DATE')
        results.append(df_monthly)

    if 'seasonally' in list_aggregate_by_time_period:
        df_seasonally = aggregate_by_period(df_aggregated_results_hourly_8760, 'seasonally', date_column='DATE')
        results.append(df_seasonally)

    if 'annually' in list_aggregate_by_time_period:
        df_annually = aggregate_by_period(df_aggregated_results_hourly_8760, 'annually', date_column='DATE')
        results.append(df_annually)

    if 'custom' in list_aggregate_by_time_period:
        df_user_defined =slice_hourly_results_time_period(df_aggregated_results_hourly_8760, hour_start, hour_end)
        results.append(df_user_defined)

    return results

def results_writer_time_period(output_path, list_metrics, list_df_aggregate_time_period, list_aggregate_by_time_period):
    # Map metrics to CEA features
    cea_feature = map_metrics_cea_features(list_metrics)

    # Join the paths
    target_path = os.path.join(output_path, cea_feature)

    # Create the folder
    os.makedirs(target_path, exist_ok=True)

    # Write .csv files for each time period
    for time_period in range(len(list_aggregate_by_time_period)):
        time_period_name = list_aggregate_by_time_period[time_period]
        path_csv = os.path.join(target_path, f'{time_period_name}.csv')

        # Get the corresponding DataFrame
        df = list_df_aggregate_time_period[time_period]

        # Write the DataFrame to CSV
        df.to_csv(path_csv, index=False, float_format='%.2f')

def exec_read_and_summarise(cea_scenario):
    """
    read and summarise the "useful" CEA results one after another: demand, emissions, potentials, thermal-network

    :param cea_scenario: path to the CEA scenario to be assessed using CEA
    :type cea_scenario: file path
    :return:
    :param summary_df: dataframe of the summarised results, indicating not found when not available
    :type summary_df: DataFrame
    """

    # create an empty DataFrame to store all the results
    summary_df = pd.DataFrame([cea_scenario], columns=['scenario_name'])

    # not found message to be reflected in the summary DataFrame
    na = float('Nan')
    # read and summarise: demand
    try:
        demand_path = os.path.join(cea_scenario, 'outputs/data/demand/Total_demand.csv')
        cea_result_df = pd.read_csv(demand_path)
        summary_df['conditioned_floor_area[Af_m2]'] = cea_result_df['Af_m2'].sum()
        summary_df['roof_area[Aroof_m2]'] = cea_result_df['Aroof_m2'].sum()
        summary_df['gross_floor_area[GFA_m2]'] = cea_result_df['GFA_m2'].sum()
        summary_df['occupied_floor_area[Aocc_m2]'] = cea_result_df['Aocc_m2'].sum()
        summary_df['nominal_occupancy[people0]'] = cea_result_df['people0'].sum()
        summary_df['grid_electricity_consumption[GRID_MWhyr]'] = cea_result_df['GRID_MWhyr'].sum()
        summary_df['enduse_electricity_consumption[E_sys_MWhyr]'] = cea_result_df['E_sys_MWhyr'].sum()
        summary_df['enduse_cooling_demand[QC_sys_MWhyr]'] = cea_result_df['QC_sys_MWhyr'].sum()
        summary_df['enduse_space_cooling_demand[Qcs_sys_MWhyr]'] = cea_result_df['Qcs_sys_MWhyr'].sum()
        summary_df['enduse_heating_demand[QH_sys_MWhyr]'] = cea_result_df['QH_sys_MWhyr'].sum()
        summary_df['enduse_space_heating_demand[Qhs_MWhyr]'] = cea_result_df['Qhs_MWhyr'].sum()
        summary_df['enduse_dhw_demand[Qww_MWhyr]'] = cea_result_df['Qww_MWhyr'].sum()

    except FileNotFoundError:
        summary_df['conditioned_floor_area[Af_m2]'] = na
        summary_df['roof_area[Aroof_m2]'] = na
        summary_df['gross_floor_area[GFA_m2]'] = na
        summary_df['occupied_floor_area[Aocc_m2]'] = na
        summary_df['nominal_occupancy[people0]'] = na
        summary_df['grid_electricity_consumption[GRID_MWhyr]'] = na
        summary_df['enduse_electricity_consumption[E_sys_MWhyr]'] = na
        summary_df['enduse_cooling_demand[QC_sys_MWhyr]'] = na
        summary_df['enduse_space_cooling_demand[Qcs_sys_MWhyr]'] = na
        summary_df['enduse_heating_demand[QH_sys_MWhyr]'] = na
        summary_df['enduse_space_heating_demand[Qhs_MWhyr]'] = na
        summary_df['enduse_dhw_demand[Qww_MWhyr]'] = na

    # read and summarise: emissions-embodied
    try:
        lca_embodied_path = os.path.join(cea_scenario, 'outputs/data/emissions/Total_LCA_embodied.csv')
        cea_result_df = pd.read_csv(lca_embodied_path)
        summary_df['embodied_emissions_building_construction[GHG_sys_embodied_tonCO2yr]'] = cea_result_df['GHG_sys_embodied_tonCO2yr'].sum()
        summary_df['embodied_emissions_building_construction_per_gross_floor_area[GHG_sys_embodied_kgCO2m2yr]'] = summary_df['embodied_emissions_building_construction[GHG_sys_embodied_tonCO2yr]']/cea_result_df['GFA_m2'].sum()*1000

    except FileNotFoundError:
        summary_df['embodied_emissions_building_construction[GHG_sys_embodied_tonCO2yr]'] = na
        summary_df['embodied_emissions_building_construction_per_gross_floor_area[GHG_sys_embodied_kgCO2m2yr]'] = na

    # read and summarise: emissions-operation
    try:
        lca_operation_path = os.path.join(cea_scenario, 'outputs/data/emissions/Total_LCA_operation.csv')
        cea_result_df = pd.read_csv(lca_operation_path)
        summary_df['operation_emissions[GHG_sys_tonCO2]'] = cea_result_df['GHG_sys_tonCO2'].sum()
        summary_df['operation_emissions_per_gross_floor_area[GHG_sys_kgCO2m2yr]'] = summary_df['operation_emissions[GHG_sys_tonCO2]']/cea_result_df['GFA_m2'].sum()*1000
        summary_df['operation_emissions_grid[GHG_sys_tonCO2]'] = cea_result_df['GRID_tonCO2'].sum()
        summary_df['operation_emissions_grid_per_gross_floor_area[GHG_sys_kgCO2m2yr]'] = summary_df['operation_emissions_grid[GHG_sys_tonCO2]']/cea_result_df['GFA_m2'].sum()*1000

    except FileNotFoundError:
        summary_df['operation_emissions[GHG_sys_tonCO2]'] = na
        summary_df['operation_emissions_per_gross_floor_area[GHG_sys_kgCO2m2yr]'] = na
        summary_df['operation_emissions_grid[GHG_sys_tonCO2]'] = na
        summary_df['operation_emissions_grid_per_gross_floor_area[GHG_sys_kgCO2m2yr]'] = na

    # read and summarise: pv
    pv_database_path = os.path.join(cea_scenario, 'inputs/technology/components/CONVERSION.xlsx')
    pv_database_df = pd.read_excel(pv_database_path, sheet_name="PHOTOVOLTAIC_PANELS")
    panel_types = list(set(pv_database_df['code']))
    for panel_type in panel_types:
        pv_path = os.path.join(cea_scenario, 'outputs/data/potentials/solar/PV_{panel_type}_total_buildings.csv'.format(panel_type=panel_type))

        try:
            cea_result_df = pd.read_csv(pv_path)
            summary_df[f'PV_{panel_type}_surface_area[Area_SC_m2]'.format(panel_type=panel_type)] = cea_result_df['Area_PV_m2'].sum()
            summary_df[f'PV_{panel_type}_electricity_generated[E_PV_gen_kWh]'.format(panel_type=panel_type)] = cea_result_df['E_PV_gen_kWh'].sum()

        except FileNotFoundError:
            summary_df[f'PV_{panel_type}_surface_area[Area_SC_m2]'.format(panel_type=panel_type)] = na
            summary_df[f'PV_{panel_type}_electricity_generated[E_PV_gen_kWh]'.format(panel_type=panel_type)] = na

    # read and summarise: pvt
    try:
        pvt_path = os.path.join(cea_scenario, 'outputs/data/potentials/solar/PVT_total_buildings.csv')
        cea_result_df = pd.read_csv(pvt_path)
        summary_df['PVT_surface_area[Area_PVT_m2]'] = cea_result_df['Area_PVT_m2'].sum()
        summary_df['PVT_electricity_generated[E_PVT_gen_kWh]'] = cea_result_df['E_PVT_gen_kWh'].sum()
        summary_df['PVT_heat_generated[Q_PVT_gen_kWh]'] = cea_result_df['Q_PVT_gen_kWh'].sum()

    except FileNotFoundError:
        summary_df['PVT_surface_area[Area_PVT_m2]'] = na
        summary_df['PVT_electricity_generated[E_PVT_gen_kWh]'] = na
        summary_df['PVT_heat_generated[Q_PVT_gen_kWh]'] = na

    # read and summarise: sc-et
    try:
        sc_et_path = os.path.join(cea_scenario, 'outputs/data/potentials/solar/SC_ET_total_buildings.csv')
        cea_result_df = pd.read_csv(sc_et_path)
        summary_df['SC_evacuated_tube_surface_area[Area_SC_m2]'] = cea_result_df['Area_SC_m2'].sum()
        summary_df['SC_evacuated_tube_heat_generated[Q_SC_gen_kWh]'] = cea_result_df['Q_SC_gen_kWh'].sum()

    except FileNotFoundError:
        summary_df['SC_evacuated_tube_surface_area[Area_SC_m2]'] = na
        summary_df['SC_evacuated_tube_heat_generated[Q_SC_gen_kWh]'] = na

    # read and summarise: sc-fp
    try:
        sc_fp_path = os.path.join(cea_scenario, 'outputs/data/potentials/solar/SC_FP_total_buildings.csv')
        cea_result_df = pd.read_csv(sc_fp_path)
        summary_df['SC_flat_plate_surface_area[Area_SC_m2]'] = cea_result_df['Area_SC_m2'].sum()
        summary_df['SC_flat_plate_tube_heat_generated[Q_SC_gen_kWh]'] = cea_result_df['Q_SC_gen_kWh'].sum()

    except FileNotFoundError:
        summary_df['SC_flat_plate_surface_area[Area_SC_m2]'] = na
        summary_df['SC_flat_plate_heat_generated[Q_SC_gen_kWh]'] = na

    # read and summarise: potentials shallow-geothermal
    try:
        shallow_geothermal_path = os.path.join(cea_scenario, 'outputs/data/potentials/Shallow_geothermal_potential.csv')
        cea_result_df = pd.read_csv(shallow_geothermal_path)
        summary_df['geothermal_heat_potential[QGHP_kWh]'] = cea_result_df['QGHP_kW'].sum()
        summary_df['area_for_ground_source_heat_pump[Area_avail_m2]'] = cea_result_df['Area_avail_m2'].mean()

    except FileNotFoundError:
        summary_df['geothermal_heat_potential[QGHP_kWh]'] = na
        summary_df['area_for_ground_source_heat_pump[Area_avail_m2]'] = na

    # read and summarise: potentials sewage heat
    try:
        sewage_heat_path = os.path.join(cea_scenario, 'outputs/data/potentials/Sewage_heat_potential.csv')
        cea_result_df = pd.read_csv(sewage_heat_path)
        summary_df['sewage_heat_potential[Qsw_kWh]'] = cea_result_df['Qsw_kW'].sum()

    except FileNotFoundError:
        summary_df['sewage_heat_potential[Qsw_kWh]'] = na

    # read and summarise: potentials water body
    try:
        water_body_path = os.path.join(cea_scenario, 'outputs/data/potentials/Water_body_potential.csv')
        cea_result_df = pd.read_csv(water_body_path)
        summary_df['water_body_heat_potential[QLake_kWh]'] = cea_result_df['QLake_kW'].sum()

    except FileNotFoundError:
        summary_df['water_body_heat_potential[QLake_kWh]'] = na

    # read and summarise: district heating plant - thermal
    try:
        dh_plant_thermal_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/DH__plant_thermal_load_kW.csv')
        cea_result_df = pd.read_csv(dh_plant_thermal_path)
        summary_df['DH_plant_thermal_load[thermal_load_kWh]'] = cea_result_df['thermal_load_kW'].sum()
        summary_df['DH_plant_power[thermal_load_kW]'] = cea_result_df['thermal_load_kW'].max()

    except FileNotFoundError:
        summary_df['DH_plant_thermal_load[thermal_load_kWh]'] = na
        summary_df['DH_plant_power[thermal_load_kW]'] = na

    # read and summarise: district heating plant - pumping
    try:
        dh_plant_pumping_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/DH__plant_pumping_load_kW.csv')
        cea_result_df = pd.read_csv(dh_plant_pumping_path)
        summary_df['DH_electricity_consumption_for_pressure_loss[pressure_loss_total_kWh]'] = cea_result_df['pressure_loss_total_kW'].sum()
        summary_df['DH_plant_pumping_power[pressure_loss_total_kW]'] = cea_result_df['pressure_loss_total_kW'].max()

    except FileNotFoundError:
        summary_df['DH_electricity_consumption_for_pressure_loss[pressure_loss_total_kWh]'] = na
        summary_df['DH_plant_pumping_power[pressure_loss_total_kW]'] = na

    # read and summarise: district cooling plant - thermal
    try:
        dc_plant_thermal_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/DC__plant_thermal_load_kW.csv')
        cea_result_df = pd.read_csv(dc_plant_thermal_path)
        summary_df['DC_plant_thermal_load[thermal_load_kWh]'] = cea_result_df['thermal_load_kW'].sum()
        summary_df['DC_plant_power[thermal_load_kW]'] = cea_result_df['thermal_load_kW'].max()

    except FileNotFoundError:
        summary_df['DC_plant_thermal_load[thermal_load_kWh]'] = na
        summary_df['DC_plant_power[thermal_load_kW]'] = na

    # read and summarise: district cooling plant - pumping
    try:
        dc_plant_pumping_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/DC__plant_pumping_load_kW.csv')
        cea_result_df = pd.read_csv(dc_plant_pumping_path)
        summary_df['DC_electricity_consumption_for_pressure_loss[pressure_loss_total_kWh]'] = cea_result_df['pressure_loss_total_kW'].sum()
        summary_df['DC_plant_pumping_power[pressure_loss_total_kW]'] = cea_result_df['pressure_loss_total_kW'].max()

    except FileNotFoundError:
        summary_df['DC_electricity_consumption_for_pressure_loss[pressure_loss_total_kWh]'] = na
        summary_df['DC_plant_pumping_power[pressure_loss_total_kW]'] = na

    # return the summary DataFrame
    return summary_df

def main(config):
    """
    Read through and summarise CEA results for all scenarios under a project.

    :param config: the configuration object to use
    :type config: cea.config.Configuration
    :return:
    """


    # Start the timer
    t0 = time.perf_counter()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    assert os.path.exists(config.general.project), 'input file not found: %s' % config.project

    # gather info from config file
    output_path = config.result_summary.output_path
    list_buildings = config.result_summary.buildings
    bool_aggregate_by_building = config.result_summary.aggregate_by_building
    list_aggregate_by_time_period = config.result_summary.aggregate_by_time_period
    list_metrics_architecture = config.result_summary.metrics_architecture
    list_metrics_demand = config.result_summary.metrics_demand
    list_metrics_embodied_emissions = config.result_summary.metrics_embodied_emissions
    list_metrics_operation_emissions = config.result_summary.metrics_operation_emissions
    list_metrics_pv = config.result_summary.metrics_pv
    list_metrics_pvt = config.result_summary.metrics_pvt
    list_metrics_sc_et = config.result_summary.metrics_sc_et
    list_metrics_sc_fp = config.result_summary.metrics_sc_fp
    list_metrics_other_renewables = config.result_summary.metrics_other_renewables
    list_metrics_dh = config.result_summary.metrics_dh
    list_metrics_dc = config.result_summary.metrics_dc

    #demand
    df_demand_hourly_8760 = exec_read_and_summarise_hourly_8760(config, locator, list_metrics_demand)
    list_df_demand_aggregate_time_period = exec_aggregate_time_period(config, df_demand_hourly_8760,
                                                                   list_aggregate_by_time_period)
    results_writer_time_period(output_path, list_metrics_demand, list_df_demand_aggregate_time_period, list_aggregate_by_time_period)

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire process of export CEA simulated results is now completed - time elapsed: %d.2 seconds' % time_elapsed)



if __name__ == '__main__':
    main(cea.config.Configuration())


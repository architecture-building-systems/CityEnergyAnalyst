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


season_names = ['Winter', 'Spring', 'Summer', 'Autumn']
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def get_standardized_date_column(df):
    """
    Standardizes the date column name in the DataFrame.
    If the DataFrame contains 'DATE', 'date', or 'Date', renames it to 'DATE'.

    Parameters:
    - df (pd.DataFrame): Input DataFrame.

    Returns:
    - pd.DataFrame: DataFrame with the standardized 'DATE' column.
    """
    for col in ['DATE', 'date', 'Date']:
        if col in df.columns:
            df = df.rename(columns={col: 'date'})
            break
    return df

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

    # When left blank, start date is set to Jan 01 and end date is set to Dec 31
    list_all = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17',
                '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31',
                'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    if date_start == list_all:
        date_start = ['01','Jan']

    if date_end == list_all:
        date_end = ['31','Dec']

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
        database_pv = pd.read_excel(locator.get_database_conversion_systems(), sheet_name='PHOTOVOLTAIC_PANELS')
        list_panel_type = database_pv['code'].dropna().unique().tolist()
        for building in selected_buildings:
            for panel_type in list_panel_type:
                path = locator.PV_results(building, panel_type)
                list_paths.append(path)

    if cea_feature == 'pvt':
        for building in selected_buildings:
            path = locator.PVT_results(building)
            list_paths.append(path)

    if cea_feature == 'sc_et':
        for building in selected_buildings:
            path = locator.SC_results(building, 'ET')
            list_paths.append(path)

    if cea_feature == 'sc_fp':
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
        path_thermal = locator.get_thermal_network_plant_heat_requirement_file('DH', '', representative_week=False)
        list_paths.append(path_thermal)
        path_pump = locator.get_network_energy_pumping_requirements_file('DH', '', representative_week=False)
        list_paths.append(path_pump)

    if cea_feature == 'dc':
        path_thermal = locator.get_thermal_network_plant_heat_requirement_file('DC', '', representative_week=False)
        list_paths.append(path_thermal)
        path_pump = locator.get_network_energy_pumping_requirements_file('DC', '', representative_week=False)
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


def load_cea_results_csv_files(config, list_paths, list_cea_column_names):
    """
    Iterates over a list of file paths, loads DataFrames from existing .csv files,
    and returns a list of these DataFrames.

    Parameters:
    - file_paths (list of str): List of file paths to .csv files.

    Returns:
    - list of pd.DataFrame: A list of DataFrames for files that exist.
    """
    list_dataframes = []
    date_columns = {'Date', 'DATE', 'date'}
    for path in list_paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)  # Load the CSV file into a DataFrame
                if date_columns.intersection(df.columns):
                    df = get_standardized_date_column(df)   # Change where ['DATE'] or ['Date'] to ['date']

                    # Slice the useful columns
                    selected_columns = ['date'] + list_cea_column_names
                    available_columns = [col for col in selected_columns if col in df.columns]   # check what's available
                    df = df[available_columns]

                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    df = slice_hourly_results_time_period(config, df)   # Slice the custom period of time
                    list_dataframes.append(df)  # Add the DataFrame to the list
                else:
                    # Slice the useful columns
                    selected_columns = ['Name'] + list_cea_column_names
                    available_columns = [col for col in selected_columns if col in df.columns]   # check what's available
                    df = df[available_columns]
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
    - Columns containing "people": Take the mean, rounded to the nearest integer.
    - Other columns: Sum.

    Parameters:
    - dataframes (list of pd.DataFrame): List of DataFrames to aggregate.

    Returns:
    - pd.DataFrame: Aggregated DataFrame.
    """
    # Ensure there are DataFrames to aggregate
    if not dataframes:
        return None

    # Start with the first DataFrame as a base
    aggregated_df = dataframes[0].copy()

    # Ensure DATE is in datetime format
    if 'date' in aggregated_df.columns:
        aggregated_df['date'] = pd.to_datetime(aggregated_df['date'], errors='coerce')

    # List of columns excluding 'date'
    columns_to_iterate = [col for col in aggregated_df.columns if col != 'date']

    # Iterate through the remaining DataFrames and sum/average corresponding columns
    for df in dataframes[1:]:
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        for col in columns_to_iterate:
            if col in df.columns:  # Ensure column exists in current DataFrame
                aggregated_df[col] = aggregated_df[col].add(df[col], fill_value=0)

    # Post-process "people" columns (take the mean, rounded to integer)
    for col in aggregated_df.columns:
        if "people" in col:
            aggregated_df[col] = (aggregated_df[col] / len(dataframes)).round().astype(int)

    # Post-process "_m2" columns (take the mean)
    for col in aggregated_df.columns:
        if "_m2" in col:
            aggregated_df[col] = (aggregated_df[col] / len(dataframes)).round(2)

    # Post-process "load_kW" columns (create corresponding "power_kW" columns)
    for col in aggregated_df.columns:
        if "load_kW" in col:
            power_col = col.replace("load_kW", "power_kW")
            aggregated_df[power_col] = max(
                df[col].max() for df in dataframes if col in df.columns and not df[col].isnull().all()
            )

    # Ensure numeric columns are rounded to a reasonable number of decimal places
    aggregated_df = aggregated_df.round(2)


    return aggregated_df


def exec_read_and_summarise_hourly_8760(config, locator, list_metrics):

    # map the CEA Feature for the selected metrics
    cea_feature = map_metrics_cea_features(list_metrics)

    # locate the path(s) to the results of the CEA Feature
    list_paths = get_results_path(locator, config, cea_feature)

    # get the relevant CEA column names based on selected metrics
    list_cea_column_names = map_metrics_and_cea_columns(list_metrics, direction="metrics_to_columns")

    # get the useful CEA results for the user-selected metrics and hours
    list_useful_cea_results = load_cea_results_csv_files(config, list_paths, list_cea_column_names)

    # aggregate these results
    df_aggregated_results_hourly_8760 = aggregate_dataframes(list_useful_cea_results)

    return df_aggregated_results_hourly_8760


def exec_read_and_summarise_without_date(config, locator, list_metrics):

    # map the CEA Feature for the selected metrics
    cea_feature = map_metrics_cea_features(list_metrics)

    # locate the path(s) to the results of the CEA Feature
    list_paths = get_results_path(locator, config, cea_feature)

    # get the relevant CEA column names based on selected metrics
    list_cea_column_names = map_metrics_and_cea_columns(list_metrics, direction="metrics_to_columns")

    # get the useful CEA results for the user-selected metrics and hours
    list_useful_cea_results = load_cea_results_csv_files(config, list_paths, list_cea_column_names)

    return list_useful_cea_results

def slice_hourly_results_time_period(config, df):
    """
    Slices a DataFrame based on hour_start and hour_end from the configuration.
    If hour_start > hour_end, wraps around the year:
    - Keeps rows from Hour 0 to hour_end
    - Keeps rows from hour_start to Hour 8760
    - Drops rows that are entirely empty (all NaN values).

    Parameters:
    - config: Configuration object containing hour_start and hour_end.
    - df (pd.DataFrame): The DataFrame to slice (8760 rows, 1 per hour).

    Returns:
    - pd.DataFrame: The sliced DataFrame with empty rows removed.
    """
    # Get the start (inclusive) and end (exclusive) hours
    hour_start, hour_end = get_hours_start_end(config)

    # Perform slicing based on hour_start and hour_end
    if hour_start <= hour_end:
        # Normal case: Slice rows from hour_start to hour_end
        sliced_df = df.iloc[hour_start:hour_end].copy()
    else:
        # Wrapping case: Combine two slices (0 to hour_end and hour_start to 8760)
        top_slice = df.iloc[0:hour_end]
        bottom_slice = df.iloc[hour_start:8760]
        sliced_df = pd.concat([bottom_slice, top_slice]).copy()

    # Drop rows where all values are NaN
    sliced_df = sliced_df.dropna(how='all')

    # Reset the index to ensure consistency
    sliced_df.reset_index(drop=True, inplace=True)

    return sliced_df


def aggregate_by_period(df, period, date_column='date'):
    """
    Aggregates a DataFrame by a given time period with special handling for certain column types:
    - Columns containing '_m2' or 'people': Use .mean() and round to integer.
    - Columns containing '_kW' but not '_kWh': Use .sum() and also calculate .max().
    - Other columns: Use .sum().

    Parameters:
    - df (pd.DataFrame): The input DataFrame.
    - period (str): Aggregation period ('monthly', 'seasonally', 'annually').
    - date_column (str): Name of the date column.

    Returns:
    - pd.DataFrame: Aggregated DataFrame.
    """
    # Ensure the date column is in datetime format
    if df is None:
        return None

    if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')

    if period == 'hourly':
        df['period'] = df[date_column].apply(
        lambda date: f"hour_{(date.dayofyear - 1) * 24 + date.hour + 1:04d}" if pd.notnull(date) else None
    )

    elif period == 'daily':
        # Group by day
        df['period'] = df[date_column].dt.dayofyear.apply(lambda x: f"day_{x:03d}")

    elif period == 'monthly':
        df['period'] = df[date_column].dt.month
        df['period'] = df['period'].apply(lambda x: month_names[x - 1])
        # To get only the relevant months
        categories = df['period'].unique().tolist()
        df['period'] = pd.Categorical(df['period'], categories=categories, ordered=True)

    elif period == 'seasonally':
        season_mapping = {
            1: 'Winter', 2: 'Winter', 12: 'Winter',
            3: 'Spring', 4: 'Spring', 5: 'Spring',
            6: 'Summer', 7: 'Summer', 8: 'Summer',
            9: 'Autumn', 10: 'Autumn', 11: 'Autumn',
        }

        df['period'] = df[date_column].dt.month.map(season_mapping)
        # To get only the relevant seasons
        categories = df['period'].unique().tolist()
        df['period'] = pd.Categorical(df['period'], categories=categories, ordered=True)

    elif period == 'annually':
        df['period'] = df[date_column].dt.year

    # Initialize a DataFrame for the aggregated results
    aggregated_df = pd.DataFrame()

    # Process columns based on their naming
    for col in df.columns:
        if col == date_column or col == 'period':
            continue

        if 'people' in col:
            # Use mean and round to integer for columns with  'people'
            aggregated_col = df.groupby('period')[col].mean().round().astype(int)
        elif '_m2' in col:
            # Use mean for columns with '_m2'
            aggregated_col = df.groupby('period')[col].mean().round(2)
        elif 'power_kW' in col:
            # Use sum and max for columns with '_kW' but not '_kWh'
            aggregated_col_max = df.groupby('period')[col].max().round(2)
            aggregated_df[f"{col}_power"] = aggregated_col_max
            continue
        else:
            # Default to sum for other columns
            aggregated_col = df.groupby('period')[col].sum()

        aggregated_df[col] = aggregated_col

    aggregated_df.reset_index(inplace=True)

    return aggregated_df

def exec_aggregate_time_period(df_aggregated_results_hourly_8760, list_aggregate_by_time_period):

    results = []

    if 'hourly' in list_aggregate_by_time_period:
        df_hourly = aggregate_by_period(df_aggregated_results_hourly_8760, 'hourly', date_column='date')
        results.append(df_hourly)

    if 'daily' in list_aggregate_by_time_period:
        df_daily = aggregate_by_period(df_aggregated_results_hourly_8760, 'daily', date_column='date')
        results.append(df_daily)

    if 'monthly' in list_aggregate_by_time_period:
        df_monthly = aggregate_by_period(df_aggregated_results_hourly_8760, 'monthly', date_column='date')
        results.append(df_monthly)

    if 'seasonally' in list_aggregate_by_time_period:
        df_seasonally = aggregate_by_period(df_aggregated_results_hourly_8760, 'seasonally', date_column='date')
        results.append(df_seasonally)

    if 'annually' in list_aggregate_by_time_period:
        df_annually = aggregate_by_period(df_aggregated_results_hourly_8760, 'annually', date_column='date')
        results.append(df_annually)

    return results

def results_writer_time_period(output_path, list_metrics, list_df_aggregate_time_period):
    """
    Writes aggregated results for different time periods to CSV files.

    Parameters:
    - output_path (str): The base directory to save the results.
    - list_metrics (List[str]): A list of metrics corresponding to the results.
    - list_df_aggregate_time_period (List[pd.DataFrame]): A list of DataFrames, each representing a different aggregation period.
    """
    # Map metrics to CEA features
    cea_feature = map_metrics_cea_features(list_metrics)

    # Join the paths
    target_path = os.path.join(output_path, 'export', cea_feature)

    # Create the folder if it doesn't exist
    os.makedirs(target_path, exist_ok=True)

    # Remove all files in folder
    for filename in os.listdir(target_path):
        file_path = os.path.join(target_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # Write .csv files for each DataFrame
    for df in list_df_aggregate_time_period:
        if df is not None:
            # Determine time period name based on number of rows
            row_count = len(df)
            if row_count == 1:
                time_period_name = "annually"
            elif df['period'].isin(season_names).any():
                time_period_name = "seasonally"
            elif df['period'].isin(month_names).any():
                time_period_name = "monthly"
            elif df['period'].astype(str).str.contains("day").any():
                time_period_name = "daily"
            elif df['period'].astype(str).str.contains("hour").any():
                time_period_name = "hourly"
            else:
                raise ValueError("Bug here.")

            # Create the file path
            path_csv = os.path.join(target_path, f"{time_period_name}.csv")

            # Write the DataFrame to .csv files
            try:
                df.to_csv(path_csv, index=False, float_format="%.2f")
            except Exception as e:
                print(f"Failed to write {time_period_name} results to {path_csv}: {e}")

        else:
            pass


def results_writer_without_date(output_path, list_metrics, list_df):
    """
    Writes aggregated results for different time periods to CSV files.

    Parameters:
    - output_path (str): The base directory to save the results.
    - list_metrics (List[str]): A list of metrics corresponding to the results.
    - list_df (List[pd.DataFrame]): A list of DataFrames.
    """
    # Map metrics to CEA features
    cea_feature = map_metrics_cea_features(list_metrics)

    # Join the paths
    target_path = os.path.join(output_path, 'export', cea_feature)

    # Create the folder if it doesn't exist
    os.makedirs(target_path, exist_ok=True)

    # Remove all files in folder
    for filename in os.listdir(target_path):
        file_path = os.path.join(target_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # Create the .csv file path
    path_csv = os.path.join(target_path, f"{cea_feature}.csv")

    # Write to .csv files
    for df in list_df:
        df.to_csv(path_csv, index=False, float_format="%.2f")


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

    list_list_metrics_with_date = [
                        config.result_summary.metrics_demand,
                        config.result_summary.metrics_pv,
                        config.result_summary.metrics_pvt,
                        config.result_summary.metrics_sc_et,
                        config.result_summary.metrics_sc_fp,
                        config.result_summary.metrics_other_renewables,
                        config.result_summary.metrics_dh,
                        config.result_summary.metrics_dc
                        ]

    list_list_metrics_without_date = [
                        config.result_summary.metrics_architecture,
                        config.result_summary.metrics_embodied_emissions,
                        config.result_summary.metrics_operation_emissions,
                        ]
    # Export results that have no date information, non-8760 hours
    for list_metrics in list_list_metrics_without_date:
        list_df = exec_read_and_summarise_without_date(config, locator, list_metrics)
        results_writer_without_date(output_path, list_metrics, list_df)

    # Export results that have date information, 8760 hours
    for list_metrics in list_list_metrics_with_date:
        list_df_time_period = exec_aggregate_time_period(
            exec_read_and_summarise_hourly_8760(config, locator, list_metrics), list_aggregate_by_time_period)
        results_writer_time_period(output_path, list_metrics, list_df_time_period)



    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire process of exporting CEA simulated results is now completed - time elapsed: %d.2 seconds' % time_elapsed)



if __name__ == '__main__':
    main(cea.config.Configuration())


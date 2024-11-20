"""
Read and summarise CEA results over all scenarios in a project.

"""

import os
import pandas as pd
import cea.config
import time
from datetime import datetime
import cea.inputlocator
from cea.utilities.dbf import dbf_to_dataframe

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

    hour_start = from_date_string_to_hours(date_start)      #Nth hour of the year, starting at 0, inclusive
    hour_end = from_date_string_to_hours(date_end) + 24     #Nth hour of the year, ending at 8760, not-inclusive

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
    "other_renewables": ['geothermal_heat_potential[kWh]','area_for_ground_source_heat_pump[m2]', 'sewage_heat_potential[kWh]','water_body_heat_potential[kWh]'],
    "dh": ['DH_plant_thermal_load[kWh]','DH_plant_power[kW]',
                         'DH_electricity_consumption_for_pressure_loss[kWh]','DH_plant_pumping_power[kW]'],
    "dc": ['DC_plant_thermal_load[kWh]','DC_plant_power[kW]',
                         'DC_electricity_consumption_for_pressure_loss[kWh]','DC_plant_pumping_power[kW]'],
    }

    for cea_feature, attached_list in dict.items():
        if set(list_metrics).issubset(set(attached_list)):
            return cea_feature
    return None


def get_results_path(locator, cea_feature, list_buildings):

    list_paths = []
    list_appendix = []

    if cea_feature == 'architecture':
        path = locator.get_total_demand()
        list_paths.append(path)
        list_appendix.append(cea_feature)

    elif cea_feature == 'demand':
        for building in list_buildings:
            path = locator.get_demand_results_file(building)
            list_paths.append(path)
        list_appendix.append(cea_feature)

    elif cea_feature == 'embodied_emissions':
        path = locator.get_lca_embodied()
        list_paths.append(path)
        list_appendix.append(cea_feature)

    elif cea_feature == 'operation_emissions':
        path = locator.get_lca_operation()
        list_paths.append(path)
        list_appendix.append(cea_feature)

    if cea_feature == 'pv':
        database_pv = pd.read_excel(locator.get_database_conversion_systems(), sheet_name='PHOTOVOLTAIC_PANELS')
        list_panel_type = database_pv['code'].dropna().unique().tolist()
        for panel_type in list_panel_type:
            pv_paths = []
            for building in list_buildings:
                path = locator.PV_results(building, panel_type)
                pv_paths.append(path)
            list_paths.append(pv_paths)
            list_appendix.append(f"{cea_feature}_{panel_type}")

    if cea_feature == 'pvt':
        for building in list_buildings:
            path = locator.PVT_results(building)
            list_paths.append(path)
        list_appendix.append(cea_feature)

    if cea_feature == 'sc_et':
        for building in list_buildings:
            path = locator.SC_results(building, 'ET')
            list_paths.append(path)
        list_appendix.append(cea_feature)

    if cea_feature == 'sc_fp':
        for building in list_buildings:
            path = locator.SC_results(building, 'FP')
            list_paths.append(path)
        list_appendix.append(cea_feature)

    if cea_feature == 'other_renewables':
        path_geothermal = locator.get_geothermal_potential()
        path_sewage_heat = locator.get_sewage_heat_potential()
        path_water_body = locator.get_water_body_potential()
        list_paths.append(path_geothermal)
        list_paths.append(path_sewage_heat)
        list_paths.append(path_water_body)
        list_appendix.append(cea_feature)

    if cea_feature == 'dh':
        path_thermal = locator.get_thermal_network_plant_heat_requirement_file('DH', '', representative_week=False)
        path_pump = locator.get_network_energy_pumping_requirements_file('DH', '', representative_week=False)
        list_paths.append(path_thermal)
        list_paths.append(path_pump)
        list_appendix.append(cea_feature)

    if cea_feature == 'dc':
        path_thermal = locator.get_thermal_network_plant_heat_requirement_file('DC', '', representative_week=False)
        path_pump = locator.get_network_energy_pumping_requirements_file('DC', '', representative_week=False)
        list_paths.append(path_thermal)
        list_paths.append(path_pump)
        list_appendix.append(cea_feature)

    return list_paths, list_appendix


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
        'DH_electricity_consumption_for_pressure_loss[kWh]': ['pressure_loss_total_kW'],
        'DC_plant_thermal_load[kWh]': ['thermal_load_kW'],
        'DC_electricity_consumption_for_pressure_loss[kWh]': ['pressure_loss_total_kW'],
    }

    # Reverse the mapping if direction is "columns_to_metrics"
    if direction == "columns_to_metrics":
        mapping_dict = {cea_col: metric for metric, cea_cols in mapping_dict.items() for cea_col in cea_cols}

    # Perform the mapping
    output_list = []
    for item in input_list:
        if item in mapping_dict:
            # Map the item
            mapped_value = mapping_dict[item]
            if isinstance(mapped_value, list):
                output_list.extend(mapped_value)
            else:
                output_list.append(mapped_value)
        else:
            # If no mapping found, keep the original item
            output_list.append(item)

    return output_list


def check_list_nesting(input_list):
    """
    Checks whether every item in a list is itself a list or not.

    Returns:
    - True: if every item in the list is a list.
    - False: if no item in the list is a list.
    - ValueError: if the list contains a mix of lists and non-lists.

    Parameters:
    - input_list (list): The list to check.

    Returns:
    - bool: True or False based on the condition.

    Raises:
    - ValueError: If the list contains a mix of lists and non-lists.
    """
    if not isinstance(input_list, list):
        raise TypeError("Input must be a list.")

    all_lists = all(isinstance(item, list) for item in input_list)
    no_lists = all(not isinstance(item, list) for item in input_list)

    if all_lists:
        return True
    elif no_lists:
        return False
    else:
        raise ValueError("The input list contains a mix of lists and non-lists.")


def load_cea_results_from_csv_files(config, list_paths, list_cea_column_names):
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
                    df = slice_hourly_results_for_custom_time_period(config, df)   # Slice the custom period of time
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


def aggregate_or_combine_dataframes(config, dataframes):
    """
    Aggregates or horizontally combines a list of DataFrames:
    - If all DataFrames share the same column names (excluding 'date'), aggregate corresponding cells.
    - If DataFrames have different column names, combine them horizontally based on the 'date' column.

    Parameters:
    - dataframes (list of pd.DataFrame): List of DataFrames to process.

    Returns:
    - pd.DataFrame: Aggregated or combined DataFrame.

    """

    bool_use_acronym = config.result_summary.use_cea_acronym_format_column_names

    # Ensure there are DataFrames to process
    if not dataframes:
        return None

    # Check if all DataFrames share the same column names (excluding 'date')
    column_sets = [set(df.columns) - {'date'} for df in dataframes]
    all_columns_match = all(column_set == column_sets[0] for column_set in column_sets)

    if all_columns_match:
        # Aggregate DataFrames with the same columns
        aggregated_df = dataframes[0].copy()
        for df in dataframes[1:]:
            for col in aggregated_df.columns:
                if col == 'date':
                    continue
                if 'people' in col:
                    # Average "people" columns and round to integer
                    aggregated_df[col] = (
                        aggregated_df[col].add(df[col], fill_value=0) / len(dataframes)
                    ).round().astype(int)
                elif '_m2' in col:
                    # Average "_m2" columns
                    aggregated_df[col] = (
                        aggregated_df[col].add(df[col], fill_value=0) / len(dataframes)
                    ).round(2)
                else:
                    # Sum for other numeric columns
                    aggregated_df[col] = aggregated_df[col].add(df[col], fill_value=0)

            aggregated_df = aggregated_df.round(2)

            if not bool_use_acronym:
                aggregated_df.columns = map_metrics_and_cea_columns(aggregated_df.columns, direction="columns_to_metrics")

            return aggregated_df

    else:
        # Combine DataFrames horizontally on 'date'
        combined_df = dataframes[0].copy()
        for df in dataframes[1:]:
            combined_df = pd.merge(combined_df, df, on='date', how='outer')

        # Sort by 'date' and reset the index
        combined_df.sort_values(by='date', inplace=True)
        combined_df.reset_index(drop=True, inplace=True)

        if not bool_use_acronym:
            combined_df.columns = map_metrics_and_cea_columns(combined_df.columns, direction="columns_to_metrics")

        return combined_df


def slice_hourly_results_for_custom_time_period(config, df):
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
    - Columns containing '_m2' or 'people': Use .mean() and round.
    - Other columns: Use .sum().

    Parameters:
    - df (pd.DataFrame): The input DataFrame.
    - period (str): Aggregation period ('hourly', 'daily', 'monthly', 'seasonally', 'annually').
    - date_column (str): Name of the date column.

    Returns:
    - pd.DataFrame: Aggregated DataFrame.
    """
    if df is None or df.empty:
        return None

    # Ensure the date column is in datetime format
    if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')

    # Handle different periods
    if period == 'hourly':
        df['period'] = df[date_column].apply(
            lambda date: f"hour_{(date.dayofyear - 1) * 24 + date.hour + 1:04d}" if pd.notnull(date) else None
        )

    elif period == 'daily':
        df['period'] = df[date_column].dt.dayofyear.apply(lambda x: f"day_{x:03d}")

    elif period == 'monthly':
        df['period'] = df[date_column].dt.month
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        df['period'] = df['period'].apply(lambda x: month_names[x - 1])
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
        categories = df['period'].unique().tolist()
        df['period'] = pd.Categorical(df['period'], categories=categories, ordered=True)

    elif period == 'annually':
        df['period'] = df[date_column].dt.year

    # Initialize an aggregated DataFrame
    aggregated_df = pd.DataFrame()

    # Process columns based on their naming
    for col in df.columns:
        if col in [date_column, 'period']:
            continue

        if 'people' in col:
            aggregated_col = df.groupby('period')[col].mean().round().astype(int)
        elif '_m2' in col:
            aggregated_col = df.groupby('period')[col].mean().round(2)
        else:
            # Default to sum for other columns
            aggregated_col = df.groupby('period')[col].sum()

        aggregated_df[col] = aggregated_col

    # Preserve the date_column for hourly or daily periods
    if period in ['hourly', 'daily']:
        aggregated_df[date_column] = df.groupby('period')[date_column].first()

    aggregated_df.reset_index(inplace=True)

    return aggregated_df


def exec_read_and_slice(config, locator, list_metrics, list_buildings):

    # map the CEA Feature for the selected metrics
    cea_feature = map_metrics_cea_features(list_metrics)

    # locate the path(s) to the results of the CEA Feature
    list_paths, list_appendix = get_results_path(locator, cea_feature, list_buildings)

    # get the relevant CEA column names based on selected metrics
    list_cea_column_names = map_metrics_and_cea_columns(list_metrics, direction="metrics_to_columns")

    list_list_useful_cea_results = []
    # check if list_paths is nested, for example, for PV, the lists can be nested as there are different types of PV
    if not check_list_nesting(list_paths):
        # get the useful CEA results for the user-selected metrics and hours
        list_useful_cea_results = load_cea_results_from_csv_files(config, list_paths, list_cea_column_names)
        list_list_useful_cea_results.append(list_useful_cea_results)
    else:
        for sublist_paths in list_paths:
            list_useful_cea_results = load_cea_results_from_csv_files(config, sublist_paths, list_cea_column_names)
            list_list_useful_cea_results.append(list_useful_cea_results)

    return list_list_useful_cea_results, list_appendix


def exec_aggregate_building(config, list_list_useful_cea_results, list_buildings):

    bool_use_acronym = config.result_summary.use_cea_acronym_format_column_names
    list_results = []
    for list_useful_cea_results in list_list_useful_cea_results:

        # Compute the sum for each DataFrame
        rows = []
        for df in list_useful_cea_results:
            if df is not None:
                row_sum = df.sum(numeric_only=True)  # Exclude non-numeric columns
                rows.append(row_sum)

        # Create a DataFrame from the rows
        result_df = pd.DataFrame(rows)

        if not bool_use_acronym:
             result_df.columns = map_metrics_and_cea_columns(result_df.columns, direction="columns_to_metrics")

        if not result_df.empty:
            result_df.insert(0, 'Name', list_buildings)

        # Reset index for a clean result
        list_results.append([result_df.reset_index(drop=True)])

    return list_results


def exec_aggregate_time_period(config, list_list_useful_cea_results, list_aggregate_by_time_period):

    list_list_df = []
    list_list_time_period = []

    for list_useful_cea_results in list_list_useful_cea_results:
        df_aggregated_results_hourly = aggregate_or_combine_dataframes(config, list_useful_cea_results)

        list_df = []
        list_time_period = []

        if 'hourly' in list_aggregate_by_time_period:
            df_hourly = aggregate_by_period(df_aggregated_results_hourly, 'hourly', date_column='date')
            list_df.append(df_hourly)
            list_time_period.append('hourly')

        if 'daily' in list_aggregate_by_time_period:
            df_daily = aggregate_by_period(df_aggregated_results_hourly, 'daily', date_column='date')
            list_df.append(df_daily)
            list_time_period.append('daily')

        if 'monthly' in list_aggregate_by_time_period:
            df_monthly = aggregate_by_period(df_aggregated_results_hourly, 'monthly', date_column='date')
            list_df.append(df_monthly)
            list_time_period.append('monthly')

        if 'seasonally' in list_aggregate_by_time_period:
            df_seasonally = aggregate_by_period(df_aggregated_results_hourly, 'seasonally', date_column='date')
            list_df.append(df_seasonally)
            list_time_period.append('seasonally')

        if 'annually' in list_aggregate_by_time_period:
            df_annually = aggregate_by_period(df_aggregated_results_hourly, 'annually', date_column='date')
            list_df.append(df_annually)
            list_time_period.append('annually')

        list_list_df.append(list_df)
        list_list_time_period.append(list_time_period)

    return list_list_df, list_list_time_period


def results_writer_time_period_with_date(config, output_path, list_metrics, list_list_df_aggregate_time_period, list_list_time_period, list_appendix):
    """
    Writes aggregated results for different time periods to CSV files.

    Parameters:
    - output_path (str): The base directory to save the results.
    - list_metrics (List[str]): A list of metrics corresponding to the results.
    - list_df_aggregate_time_period (List[pd.DataFrame]): A list of DataFrames, each representing a different aggregation period.
    """
    # Map metrics to CEA features
    cea_feature = map_metrics_cea_features(list_metrics)

    # Get the hour start and hour end
    hour_start, hour_end = get_hours_start_end(config)

    # Create the target path of directory
    target_path = os.path.join(output_path, cea_feature)

    # Create the folder if it doesn't exist
    os.makedirs(target_path, exist_ok=True)

    # Remove all files in folder
    for filename in os.listdir(target_path):
        file_path = os.path.join(target_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    for m in range(len(list_list_df_aggregate_time_period)):
        list_df_aggregate_time_period = list_list_df_aggregate_time_period[m]
        list_time_period = list_list_time_period[m]
        appendix = list_appendix[m]

        # Write .csv files for each DataFrame
        for n in range(len(list_df_aggregate_time_period)):
            df = list_df_aggregate_time_period[n]
            time_period = list_time_period[n]
            if df is not None:
                # Determine time period name based on the content in Column ['period']
                if len(df) == 1 and abs(hour_end - hour_start) == 8760:
                    path_csv = os.path.join(target_path, f"{appendix}_{time_period}.csv")
                    df.to_csv(path_csv, index=False, float_format="%.2f")
                # if only one day is involved
                elif len(df) == 1 and time_period == 'daily':
                    path_csv = os.path.join(target_path, f"{appendix}_{time_period}.csv")
                    df.to_csv(path_csv, index=False, float_format="%.2f")
                    break

                elif len(df) > 1 and time_period == 'daily':
                    path_csv = os.path.join(target_path, f"{appendix}_{time_period}.csv")
                    df.to_csv(path_csv, index=False, float_format="%.2f")

                # if all days selected fall into the same month
                elif len(df) == 1 and time_period == 'monthly':
                    path_csv = os.path.join(target_path, f"{appendix}_{time_period}.csv")
                    df.to_csv(path_csv, index=False, float_format="%.2f")
                    break
                elif len(df) > 1 and time_period == 'monthly':
                    path_csv = os.path.join(target_path, f"{appendix}_{time_period}.csv")
                    df.to_csv(path_csv, index=False, float_format="%.2f")

                elif time_period == 'seasonally':
                    path_csv = os.path.join(target_path, f"{appendix}_{time_period}.csv")
                    df.to_csv(path_csv, index=False, float_format="%.2f")

                elif time_period == 'hourly':
                    path_csv = os.path.join(target_path, f"{appendix}_{time_period}.csv")
                    df.to_csv(path_csv, index=False, float_format="%.2f")

            else:
                pass    # Allow the missing results and will just pass

        # Write .csv files for sum of all selected hours
        for df in list_df_aggregate_time_period:
            if df is not None:
                if len(df) == 1 and abs(hour_end - hour_start) != 8760 \
                        and not df['period'].astype(str).str.contains("day").any() \
                        and not df['period'].isin(month_names).any() \
                        and not df['period'].isin(season_names).any() \
                        and not df['period'].astype(str).str.contains("hour").any():
                    time_period = "sum_selected_hours"
                    df['period'] = "selected_hours"
                    path_csv = os.path.join(target_path, f"{appendix}_{time_period}.csv")
                    df.to_csv(path_csv, index=False, float_format="%.2f")
            else:
                pass    # Allow the missing results and will just pass


def results_writer_time_period_without_date(output_path, list_metrics, list_list_df, list_appendix):
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
    target_path = os.path.join(output_path, cea_feature, 'buildings')

    # Create the folder if it doesn't exist
    os.makedirs(target_path, exist_ok=True)

    # Remove all files in folder
    for filename in os.listdir(target_path):
        file_path = os.path.join(target_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    for m in range(len(list_list_df)):
        list_df = list_list_df[m]
        appendix = list_appendix[m]

        if appendix == 'architecture':
            # Create the .csv file path
            path_csv = os.path.join(target_path, f"{appendix}_buildings.csv")
        else:
            path_csv = os.path.join(target_path, f"{appendix}_sum_selected_hours_buildings.csv")
        # Write to .csv files
        for df in list_df:
            if not df.empty:
                df.to_csv(path_csv, index=False, float_format="%.2f")


def filter_cea_results_by_buildings(config, list_list_useful_cea_results, list_buildings):
    """
    Filters rows in all DataFrames within a nested list of DataFrames,
    keeping only rows where the 'Name' column matches any value in list_buildings.

    Parameters:
    - list_list_useful_cea_results (list of list of pd.DataFrame): Nested list of DataFrames.
    - list_buildings (list of str): List of building names to filter by in the 'Name' column.

    Returns:
    - list of list of pd.DataFrame: Nested list of filtered DataFrames with the same shape as the input.
    """
    bool_use_acronym = config.result_summary.use_cea_acronym_format_column_names
    list_list_useful_cea_results_buildings = []

    for dataframe_list in list_list_useful_cea_results:
        filtered_list = []
        for df in dataframe_list:
            if 'Name' in df.columns:
                filtered_df = df[df['Name'].isin(list_buildings)]

                if not bool_use_acronym:
                    filtered_df.columns = map_metrics_and_cea_columns(filtered_df.columns, direction="columns_to_metrics")

                filtered_list.append(filtered_df)

            else:
                # If the 'Name' column does not exist, append an empty DataFrame
                print("Skipping a DataFrame as it does not contain the 'Name' column.")
                filtered_list.append(pd.DataFrame())
        list_list_useful_cea_results_buildings.append(filtered_list)

    return list_list_useful_cea_results_buildings

def determine_building_main_use(df_typology):

    # Create a new DataFrame to store results
    result = pd.DataFrame()
    result['Name'] = df_typology['Name']

    # Determine the main use type and its ratio
    result['main_use'] = df_typology.apply(
        lambda row: row['1ST_USE'] if row['1ST_USE_R'] >= max(row['2ND_USE_R'], row['3RD_USE_R']) else
                    row['2ND_USE'] if row['2ND_USE_R'] >= row['3RD_USE_R'] else
                    row['3RD_USE'],
        axis=1
    )
    result['main_use_r'] = df_typology.apply(
        lambda row: row['1ST_USE_R'] if row['1ST_USE_R'] >= max(row['2ND_USE_R'], row['3RD_USE_R']) else
                    row['2ND_USE_R'] if row['2ND_USE_R'] >= row['3RD_USE_R'] else
                    row['3RD_USE_R'],
        axis=1
    )

    return result


def get_building_year_standard_main_use_type(locator):

    typology_dbf = dbf_to_dataframe(locator.get_building_typology())
    df = determine_building_main_use(typology_dbf)
    df['standard'] = typology_dbf['STANDARD']
    df['year'] = typology_dbf['YEAR']

    return df

def filter_by_year_range(df_typology, integer_year_start=None, integer_year_end=None):
    """
    Filters rows in the DataFrame based on a year range.

    Parameters:
    - df_typology (pd.DataFrame): The input DataFrame containing a 'year' column.
    - integer_year_start (int, optional): Start of the year range (inclusive). Defaults to 0 if None or empty.
    - integer_year_end (int, optional): End of the year range (inclusive). Defaults to 9999 if None or empty.

    Returns:
    - pd.DataFrame: Filtered DataFrame with rows where 'year' is within the specified range.

    Raises:
    - ValueError: If 'year' column is not found or if integer_year_start > integer_year_end,
                  or if the filtered DataFrame is empty.
    """

    # Handle None or empty values
    integer_year_start = 0 if not integer_year_start else integer_year_start
    integer_year_end = 9999 if not integer_year_end else integer_year_end

    if integer_year_start > integer_year_end:
        raise ValueError("The start year cannot be greater than the end year.")

    # Filter rows where 'year' is within the range
    filtered_df = df_typology[
        (df_typology['year'] >= integer_year_start) & (df_typology['year'] <= integer_year_end)
    ]

    # Check if the filtered DataFrame is empty
    if filtered_df.empty:
        raise ValueError("No buildings meet the selected criteria for the specified year range.")

    return filtered_df

def filter_by_standard(df_typology, list_standard):
    """
    Filters rows in the DataFrame based on whether the 'standard' column matches any item in list_standard.

    Parameters:
    - df_typology (pd.DataFrame): DataFrame with a 'standard' column.
    - list_standard (list): List of standard values to filter on.

    Returns:
    - pd.DataFrame: Filtered DataFrame with rows where 'standard' matches any item in list_standard.

    Raises:
    - ValueError: If 'standard' column is not found or if the filtered DataFrame is empty.
    """

    # Filter rows where 'standard' matches any value in list_standard
    filtered_df = df_typology[df_typology['standard'].isin(list_standard)]

    # Check if the filtered DataFrame is empty
    if filtered_df.empty:
        raise ValueError("No buildings meet the selected criteria for the specified standards.")

    return filtered_df


def filter_by_main_use(df_typology, list_main_use_type):
    """
    Filters rows in the DataFrame based on whether the 'main_use' column matches any item in list_main_use_type.

    Parameters:
    - df_typology (pd.DataFrame): DataFrame with a 'main_use' column.
    - list_main_use_type (list): List of main use types to filter on.

    Returns:
    - pd.DataFrame: Filtered DataFrame with rows where 'main_use' matches any item in list_main_use_type.

    Raises:
    - ValueError: If 'main_use' column is not found or if the filtered DataFrame is empty.
    """
    if 'main_use' not in df_typology.columns:
        raise ValueError("'main_use' column not found in the DataFrame.")

    # Filter rows where 'main_use' matches any value in list_main_use_type
    filtered_df = df_typology[df_typology['main_use'].isin(list_main_use_type)]

    # Check if the filtered DataFrame is empty
    if filtered_df.empty:
        raise ValueError("No buildings meet the selected criteria for the specified main use types.")

    return filtered_df


def filter_by_main_use_ratio(df_typology, ratio_main_use_type):
    """
    Filters rows in the DataFrame where the 'main_use_r' column is equal to or larger than a given ratio.

    Parameters:
    - df_typology (pd.DataFrame): DataFrame with a 'main_use_r' column.
    - ratio_main_use_type (float): The minimum ratio threshold for filtering.

    Returns:
    - pd.DataFrame: Filtered DataFrame with rows where 'main_use_r' >= ratio_main_use_type.

    Raises:
    - ValueError: If 'main_use_r' column is not found or if the filtered DataFrame is empty.
    """

    # Filter rows where 'main_use_r' is greater than or equal to the threshold
    filtered_df = df_typology[df_typology['main_use_r'] >= ratio_main_use_type]

    # Check if the filtered DataFrame is empty
    if filtered_df.empty:
        raise ValueError("No buildings meet the criteria for the specified main use ratio.")

    return filtered_df


def filter_by_building_names(df_typology, list_buildings):
    """
    Filters rows in the DataFrame where the 'Name' column matches any item in the given list.

    Parameters:
    - df_typology (pd.DataFrame): The input DataFrame containing a 'Name' column.
    - list_buildings (list of str): List of building names to filter for.

    Returns:
    - pd.DataFrame: Filtered DataFrame with rows where 'Name' matches any item in list_buildings.

    Raises:
    - ValueError: If 'Name' column is not found or if the filtered DataFrame is empty.
    """
    if 'Name' not in df_typology.columns:
        raise ValueError("'Name' column not found in the DataFrame.")

    # Filter rows where 'Name' is in list_buildings
    filtered_df = df_typology[df_typology['Name'].isin(list_buildings)]

    # Check if the filtered DataFrame is empty
    if filtered_df.empty:
        raise ValueError("No buildings match the specified list of names.")

    return filtered_df


def serial_filer_buildings(config, locator):

    # Get the building info
    df_typology = get_building_year_standard_main_use_type(locator)

    # get the selecting criteria from config
    list_buildings = config.result_summary.buildings
    integer_year_start = config.result_summary.filer_building_by_year_start
    integer_year_end = config.result_summary.filer_building_by_year_end
    list_standard = config.result_summary.filer_building_by_standard
    list_main_use_type = config.result_summary.filer_building_by_use_type
    ratio_main_use_type = config.result_summary.min_ratio_as_main_use

    # Initial filter to keep the selected buildings
    df_typology = filter_by_building_names(df_typology, list_buildings)

    # Further select by year
    df_typology = filter_by_year_range(df_typology, integer_year_start, integer_year_end)

    # Further filter by standard
    df_typology = filter_by_standard(df_typology, list_standard)

    # Further filter by main use type
    df_typology = filter_by_main_use(df_typology, list_main_use_type)

    # Further filter by main use type ratio
    df_typology = filter_by_main_use_ratio(df_typology, ratio_main_use_type)

    return df_typology


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
    output_path = locator.get_export_folder()
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

    list_list_metrics_building = [
                        config.result_summary.metrics_demand,
                        config.result_summary.metrics_pv,
                        config.result_summary.metrics_pvt,
                        config.result_summary.metrics_sc_et,
                        config.result_summary.metrics_sc_fp,
                        ]

    # Get the hour start and hour end
    hour_start, hour_end = get_hours_start_end(config)

    # Create the folder to store all the .csv file if it doesn't exist
    output_path = os.path.join(output_path, 'results',
                               f'hours_{hour_start}_{hour_end}'.format(hour_start=hour_start, hour_end=hour_end))
    os.makedirs(output_path, exist_ok=True)

    # Store the list of selected buildings
    df_buildings = serial_filer_buildings(config, locator)
    buildings_path = os.path.join(output_path, 'selected_buildings.csv')
    df_buildings.to_csv(buildings_path, index=False)

    # Export results that have no date information, non-8760 hours, aggregate by building
    for list_metrics in list_list_metrics_without_date:
        list_list_useful_cea_results, list_appendix = exec_read_and_slice(config, locator, list_metrics, list_buildings)
        list_list_useful_cea_results_buildings = filter_cea_results_by_buildings(config, list_list_useful_cea_results, list_buildings)
        results_writer_time_period_without_date(output_path, list_metrics, list_list_useful_cea_results_buildings, list_appendix)   # Write to disk

    # Export results that have date information, 8760 hours, aggregate by time period
    for list_metrics in list_list_metrics_with_date:
        list_list_useful_cea_results, list_appendix = exec_read_and_slice(config, locator, list_metrics, list_buildings)
        list_list_df_aggregate_time_period, list_list_time_period = exec_aggregate_time_period(config, list_list_useful_cea_results, list_aggregate_by_time_period)
        results_writer_time_period_with_date(config, output_path, list_metrics, list_list_df_aggregate_time_period, list_list_time_period, list_appendix)   # Write to disk

        # aggregate by building
    if bool_aggregate_by_building:
        for list_metrics in list_list_metrics_building:
            list_list_useful_cea_results, list_appendix = exec_read_and_slice(config, locator, list_metrics, list_buildings)
            list_list_df_aggregate_building = exec_aggregate_building(config, list_list_useful_cea_results, list_buildings)
            results_writer_time_period_without_date(output_path, list_metrics, list_list_df_aggregate_building, list_appendix)  # Write to disk

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire process of exporting CEA simulated results is now completed - time elapsed: %d.2 seconds' % time_elapsed)


if __name__ == '__main__':
    main(cea.config.Configuration())


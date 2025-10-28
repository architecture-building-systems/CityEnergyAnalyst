"""
Read and summarise CEA results over all scenarios in a project.

"""
import itertools
import os
import pandas as pd
import numpy as np
import cea.config
import time
from datetime import datetime, UTC
import cea.inputlocator
import geopandas as gpd

from cea.demand.building_properties.useful_areas import calc_useful_areas


__author__ = "Zhongming Shi, Reynold Mok, Justin McCarty"
__copyright__ = "Copyright 2024, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi, Reynold Mok, Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


season_names = ['Spring', 'Summer', 'Autumn', 'Winter']
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
season_mapping = {
            3: 'Spring', 4: 'Spring', 5: 'Spring',
            6: 'Summer', 7: 'Summer', 8: 'Summer',
            9: 'Autumn', 10: 'Autumn', 11: 'Autumn',
            12: 'Winter', 1: 'Winter', 2: 'Winter'
}

# Define nominal hours for each month (non-leap year)
month_hours = {
        'Jan': 31 * 24, 'Feb': 28 * 24, 'Mar': 31 * 24,
        'Apr': 30 * 24, 'May': 31 * 24, 'Jun': 30 * 24,
        'Jul': 31 * 24, 'Aug': 31 * 24, 'Sep': 30 * 24,
        'Oct': 31 * 24, 'Nov': 30 * 24, 'Dec': 31 * 24
}

# Define nominal hours for each season
season_hours = {
        'Winter': (31 + 28 + 31) * 24,  # Dec, Jan, Feb
        'Spring': (31 + 30 + 31) * 24,  # Mar, Apr, May
        'Summer': (30 + 31 + 31) * 24,  # Jun, Jul, Aug
        'Autumn': (30 + 31 + 30) * 24   # Sep, Oct, Nov
}

# Define metrics for plot
dict_plot_metrics_cea_feature = {
    'architecture': 'architecture',
    'lifecycle_emissions': 'lifecycle-emissions',
    'operational_emissions': 'operational-emissions',
    'solar_irradiation': 'solar_irradiation',
    'demand': 'demand',
    'pv': 'pv',
    'pvt_ET': 'pvt',
    'pvt_FP': 'pvt',
    'sc_ET': 'sc',
    'sc_FP': 'sc',
    'other_renewables': 'other-renewables',
    'dh': 'dh',
    'dc': 'dc',
}

normalisation_name_mapping = {
    'grid_electricity_consumption[kWh]': 'EUI_grid_electricity[kWh/m2]',
    'enduse_electricity_demand[kWh]': 'EUI_enduse_electricity[kWh/m2]',
    'enduse_cooling_demand[kWh]': 'EUI_enduse_cooling[kWh/m2]',
    'enduse_space_cooling_demand[kWh]': 'EUI_enduse_space_cooling[kWh/m2]',
    'enduse_heating_demand[kWh]': 'EUI_enduse_heating[kWh/m2]',
    'enduse_space_heating_demand[kWh]': 'EUI_enduse_space_heating[kWh/m2]',
    'enduse_dhw_demand[kWh]': 'EUI_enduse_dhw[kWh/m2]',
    'heating[kgCO2e]': 'heating[kgCO2e/m2]',
    'hot_water[kgCO2e]': 'hot_water[kgCO2e/m2]',
    'cooling[kgCO2e]': 'cooling[kgCO2e/m2]',
    'electricity[kgCO2e]': 'electricity[kgCO2e/m2]',
    'heating_NATURALGAS[kgCO2e]': 'heating_NATURALGAS[kgCO2e/m2]',
    'heating_BIOGAS[kgCO2e]': 'heating_BIOGAS[kgCO2e/m2]',
    'heating_SOLAR[kgCO2e]': 'heating_SOLAR[kgCO2e/m2]',
    'heating_DRYBIOMASS[kgCO2e]': 'heating_DRYBIOMASS[kgCO2e/m2]',
    'heating_WETBIOMASS[kgCO2e]': 'heating_WETBIOMASS[kgCO2e/m2]',
    'heating_GRID[kgCO2e]': 'heating_GRID[kgCO2e/m2]',
    'heating_COAL[kgCO2e]': 'heating_COAL[kgCO2e/m2]',
    'heating_WOOD[kgCO2e]': 'heating_WOOD[kgCO2e/m2]',
    'heating_OIL[kgCO2e]': 'heating_OIL[kgCO2e/m2]',
    'heating_HYDROGEN[kgCO2e]': 'heating_HYDROGEN[kgCO2e/m2]',
    'heating_NONE[kgCO2e]': 'heating_NONE[kgCO2e/m2]',
    'hot_water_NATURALGAS[kgCO2e]': 'hot_water_NATURALGAS[kgCO2e/m2]',
    'hot_water_BIOGAS[kgCO2e]': 'hot_water_BIOGAS[kgCO2e/m2]',
    'hot_water_SOLAR[kgCO2e]': 'hot_water_SOLAR[kgCO2e/m2]',
    'hot_water_DRYBIOMASS[kgCO2e]': 'hot_water_DRYBIOMASS[kgCO2e/m2]',
    'hot_water_WETBIOMASS[kgCO2e]': 'hot_water_WETBIOMASS[kgCO2e/m2]',
    'hot_water_GRID[kgCO2e]': 'hot_water_GRID[kgCO2e/m2]',
    'hot_water_COAL[kgCO2e]': 'hot_water_COAL[kgCO2e/m2]',
    'hot_water_WOOD[kgCO2e]': 'hot_water_WOOD[kgCO2e/m2]',
    'hot_water_OIL[kgCO2e]': 'hot_water_OIL[kgCO2e/m2]',
    'hot_water_HYDROGEN[kgCO2e]': 'hot_water_HYDROGEN[kgCO2e/m2]',
    'hot_water_NONE[kgCO2e]': 'hot_water_NONE[kgCO2e/m2]',
    'cooling_NATURALGAS[kgCO2e]': 'cooling_NATURALGAS[kgCO2e/m2]',
    'cooling_BIOGAS[kgCO2e]': 'cooling_BIOGAS[kgCO2e/m2]',
    'cooling_SOLAR[kgCO2e]': 'cooling_SOLAR[kgCO2e/m2]',
    'cooling_DRYBIOMASS[kgCO2e]': 'cooling_DRYBIOMASS[kgCO2e/m2]',
    'cooling_WETBIOMASS[kgCO2e]': 'cooling_WETBIOMASS[kgCO2e/m2]',
    'cooling_GRID[kgCO2e]': 'cooling_GRID[kgCO2e/m2]',
    'cooling_COAL[kgCO2e]': 'cooling_COAL[kgCO2e/m2]',
    'cooling_WOOD[kgCO2e]': 'cooling_WOOD[kgCO2e/m2]',
    'cooling_OIL[kgCO2e]': 'cooling_OIL[kgCO2e/m2]',
    'cooling_HYDROGEN[kgCO2e]': 'cooling_HYDROGEN[kgCO2e/m2]',
    'cooling_NONE[kgCO2e]': 'cooling_NONE[kgCO2e/m2]',
    'electricity_NATURALGAS[kgCO2e]': 'electricity_NATURALGAS[kgCO2e/m2]',
    'electricity_BIOGAS[kgCO2e]': 'electricity_BIOGAS[kgCO2e/m2]',
    'electricity_SOLAR[kgCO2e]': 'electricity_SOLAR[kgCO2e/m2]',
    'electricity_DRYBIOMASS[kgCO2e]': 'electricity_DRYBIOMASS[kgCO2e/m2]',
    'electricity_WETBIOMASS[kgCO2e]': 'electricity_WETBIOMASS[kgCO2e/m2]',
    'electricity_GRID[kgCO2e]': 'electricity_GRID[kgCO2e/m2]',
    'electricity_COAL[kgCO2e]': 'electricity_COAL[kgCO2e/m2]',
    'electricity_WOOD[kgCO2e]': 'electricity_WOOD[kgCO2e/m2]',
    'electricity_OIL[kgCO2e]': 'electricity_OIL[kgCO2e/m2]',
    'electricity_HYDROGEN[kgCO2e]': 'electricity_HYDROGEN[kgCO2e/m2]',
    'electricity_NONE[kgCO2e]': 'electricity_NONE[kgCO2e/m2]',
    'operation_heating[kgCO2e]': 'operation_heating[kgCO2e/m2]',
    'operation_hot_water[kgCO2e]': 'operation_hot_water[kgCO2e/m2]',
    'operation_cooling[kgCO2e]': 'operation_cooling[kgCO2e/m2]',
    'operation_electricity[kgCO2e]': 'operation_electricity[kgCO2e/m2]',
    'production_wall_ag[kgCO2e]': 'production_wall_ag[kgCO2e/m2]',
    'production_wall_bg[kgCO2e]': 'production_wall_bg[kgCO2e/m2]',
    'production_wall_part[kgCO2e]': 'production_wall_part[kgCO2e/m2]',
    'production_win_ag[kgCO2e]': 'production_win_ag[kgCO2e/m2]',
    'production_roof[kgCO2e]': 'production_roof[kgCO2e/m2]',
    'production_upperside[kgCO2e]': 'production_upperside[kgCO2e/m2]',
    'production_underside[kgCO2e]': 'production_underside[kgCO2e/m2]',
    'production_floor[kgCO2e]': 'production_floor[kgCO2e/m2]',
    'production_base[kgCO2e]': 'production_base[kgCO2e/m2]',
    'production_technical_systems[kgCO2e]': 'production_technical_systems[kgCO2e/m2]',
    'biogenic_wall_ag[kgCO2e]': 'biogenic_wall_ag[kgCO2e/m2]',
    'biogenic_wall_bg[kgCO2e]': 'biogenic_wall_bg[kgCO2e/m2]',
    'biogenic_wall_part[kgCO2e]': 'biogenic_wall_part[kgCO2e/m2]',
    'biogenic_win_ag[kgCO2e]': 'biogenic_win_ag[kgCO2e/m2]',
    'biogenic_roof[kgCO2e]': 'biogenic_roof[kgCO2e/m2]',
    'biogenic_upperside[kgCO2e]': 'biogenic_upperside[kgCO2e/m2]',
    'biogenic_underside[kgCO2e]': 'biogenic_underside[kgCO2e/m2]',
    'biogenic_floor[kgCO2e]': 'biogenic_floor[kgCO2e/m2]',
    'biogenic_base[kgCO2e]': 'biogenic_base[kgCO2e/m2]',
    'biogenic_technical_systems[kgCO2e]': 'biogenic_technical_systems[kgCO2e/m2]',
    'demolition_wall_ag[kgCO2e]': 'demolition_wall_ag[kgCO2e/m2]',
    'demolition_wall_bg[kgCO2e]': 'demolition_wall_bg[kgCO2e/m2]',
    'demolition_wall_part[kgCO2e]': 'demolition_wall_part[kgCO2e/m2]',
    'demolition_win_ag[kgCO2e]': 'demolition_win_ag[kgCO2e/m2]',
    'demolition_roof[kgCO2e]': 'demolition_roof[kgCO2e/m2]',
    'demolition_upperside[kgCO2e]': 'demolition_upperside[kgCO2e/m2]',
    'demolition_underside[kgCO2e]': 'demolition_underside[kgCO2e/m2]',
    'demolition_floor[kgCO2e]': 'demolition_floor[kgCO2e/m2]',
    'demolition_base[kgCO2e]': 'demolition_base[kgCO2e/m2]',
    'demolition_technical_systems[kgCO2e]': 'demolition_technical_systems[kgCO2e/m2]'
}

# ----------------------------------------------------------------------------------------------------------------------
# Data preparation


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


def get_results_path(locator: cea.inputlocator.InputLocator, cea_feature: str, list_buildings: list)-> tuple[list[str], list[str]]:

    list_paths = []
    list_appendix = []

    if cea_feature == 'demand':
        for building in list_buildings:
            path = locator.get_demand_results_file(building)
            list_paths.append(path)
        list_appendix.append(cea_feature)

    if cea_feature == 'lifecycle_emissions':
        for building in list_buildings:
            path = locator.get_lca_timeline_building(building)
            list_paths.append(path)
        list_appendix.append(cea_feature)

    if cea_feature == 'operational_emissions':
        for building in list_buildings:
            path = locator.get_lca_operational_hourly_building(building)
            list_paths.append(path)
        list_appendix.append(cea_feature)

    if cea_feature == 'solar_irradiation':
        for building in list_buildings:
            path = locator.get_radiation_building(building)
            list_paths.append(path)
        list_appendix.append(cea_feature)

    if cea_feature == 'pv':
        database_pv = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv('PHOTOVOLTAIC_PANELS'))
        list_panel_type = database_pv['code'].dropna().unique().tolist()
        for panel_type in list_panel_type:
            pv_paths = []
            for building in list_buildings:
                path = locator.PV_results(building, panel_type)
                pv_paths.append(path)
            list_paths.append(pv_paths)
            list_appendix.append(f"{cea_feature}_{panel_type}")

    if cea_feature == 'pvt_ET':
        database_pv = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv('PHOTOVOLTAIC_PANELS'))
        list_panel_type = database_pv['code'].dropna().unique().tolist()
        for panel_type, sc_panel_type in itertools.product(list_panel_type, ['ET']):
            pv_paths = []
            for building in list_buildings:
                path = locator.PVT_results(building, panel_type, sc_panel_type)
                pv_paths.append(path)
            list_paths.append(pv_paths)
            list_appendix.append(f"{cea_feature}_{panel_type}")

    if cea_feature == 'pvt_FP':
        database_pv = pd.read_csv(locator.get_db4_components_conversion_conversion_technology_csv('PHOTOVOLTAIC_PANELS'))
        list_panel_type = database_pv['code'].dropna().unique().tolist()
        for panel_type, sc_panel_type in itertools.product(list_panel_type, ['FP']):
            pv_paths = []
            for building in list_buildings:
                path = locator.PVT_results(building, panel_type, sc_panel_type)
                pv_paths.append(path)
            list_paths.append(pv_paths)
            list_appendix.append(f"{cea_feature}_{panel_type}")

    if cea_feature == 'sc_ET':
        for sc_panel_type in ['ET']:
            sc_paths = []
            for building in list_buildings:
                path = locator.SC_results(building, sc_panel_type)
                sc_paths.append(path)
            list_paths.append(sc_paths)
            list_appendix.append(f"{cea_feature}")

    if cea_feature == 'sc_FP':
        for sc_panel_type in ['FP']:
            sc_paths = []
            for building in list_buildings:
                path = locator.SC_results(building, sc_panel_type)
                sc_paths.append(path)
            list_paths.append(sc_paths)
            list_appendix.append(f"{cea_feature}")

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


def map_metrics_cea_features(list_metrics_or_features, direction="metrics_to_features"):
    """
    Maps between metrics and CEA feature categories with support for reverse mapping.

    Parameters:
    - list_metrics_or_features (list): List of metrics or CEA feature categories to map.
    - direction (str): Direction of mapping:
        - "metrics_to_features" (default): Maps metrics to CEA feature categories.
        - "features_to_metrics": Maps CEA feature categories to metrics.

    Returns:
    - str or list: Mapped CEA feature or metrics based on the direction.

    Raises:
    - ValueError: If the direction is invalid.
    """
    mapping_dict = {
        "architecture": ['conditioned_floor_area[m2]', 'roof_area[m2]', 'gross_floor_area[m2]', 'occupied_floor_area[m2]'],
        "demand": ['grid_electricity_consumption[kWh]', 'enduse_electricity_demand[kWh]',
                   'enduse_cooling_demand[kWh]', 'enduse_space_cooling_demand[kWh]', 'enduse_heating_demand[kWh]',
                   'enduse_space_heating_demand[kWh]', 'enduse_dhw_demand[kWh]'],
        "lifecycle_emissions": [
            'operation_heating[kgCO2e]', 'operation_hot_water[kgCO2e]', 'operation_cooling[kgCO2e]',
            'operation_electricity[kgCO2e]',
            'production_wall_ag[kgCO2e]', 'production_wall_bg[kgCO2e]', 'production_wall_part[kgCO2e]',
            'production_win_ag[kgCO2e]', 'production_roof[kgCO2e]', 'production_upperside[kgCO2e]',
            'production_underside[kgCO2e]', 'production_floor[kgCO2e]', 'production_base[kgCO2e]',
            'production_technical_systems[kgCO2e]', 'biogenic_wall_ag[kgCO2e]', 'biogenic_wall_bg[kgCO2e]',
            'biogenic_wall_part[kgCO2e]', 'biogenic_win_ag[kgCO2e]', 'biogenic_roof[kgCO2e]',
            'biogenic_upperside[kgCO2e]', 'biogenic_underside[kgCO2e]', 'biogenic_floor[kgCO2e]',
            'biogenic_base[kgCO2e]', 'biogenic_technical_systems[kgCO2e]', 'demolition_wall_ag[kgCO2e]',
            'demolition_wall_bg[kgCO2e]', 'demolition_wall_part[kgCO2e]', 'demolition_win_ag[kgCO2e]',
            'demolition_roof[kgCO2e]', 'demolition_upperside[kgCO2e]', 'demolition_underside[kgCO2e]',
            'demolition_floor[kgCO2e]', 'demolition_base[kgCO2e]', 'demolition_technical_systems[kgCO2e]'
        ],
        "operational_emissions": [
            'heating[kgCO2e]', 'hot_water[kgCO2e]', 'cooling[kgCO2e]', 'electricity[kgCO2e]',
            'heating_NATURALGAS[kgCO2e]', 'heating_BIOGAS[kgCO2e]', 'heating_SOLAR[kgCO2e]',
            'heating_DRYBIOMASS[kgCO2e]', 'heating_WETBIOMASS[kgCO2e]', 'heating_GRID[kgCO2e]',
            'heating_COAL[kgCO2e]', 'heating_WOOD[kgCO2e]', 'heating_OIL[kgCO2e]',
            'heating_HYDROGEN[kgCO2e]', 'heating_NONE[kgCO2e]', 'hot_water_NATURALGAS[kgCO2e]',
            'hot_water_BIOGAS[kgCO2e]', 'hot_water_SOLAR[kgCO2e]', 'hot_water_DRYBIOMASS[kgCO2e]',
            'hot_water_WETBIOMASS[kgCO2e]', 'hot_water_GRID[kgCO2e]', 'hot_water_COAL[kgCO2e]',
            'hot_water_WOOD[kgCO2e]', 'hot_water_OIL[kgCO2e]', 'hot_water_HYDROGEN[kgCO2e]',
            'hot_water_NONE[kgCO2e]', 'cooling_NATURALGAS[kgCO2e]', 'cooling_BIOGAS[kgCO2e]',
            'cooling_SOLAR[kgCO2e]', 'cooling_DRYBIOMASS[kgCO2e]', 'cooling_WETBIOMASS[kgCO2e]',
            'cooling_GRID[kgCO2e]', 'cooling_COAL[kgCO2e]', 'cooling_WOOD[kgCO2e]', 'cooling_OIL[kgCO2e]',
            'cooling_HYDROGEN[kgCO2e]', 'cooling_NONE[kgCO2e]', 'electricity_NATURALGAS[kgCO2e]',
            'electricity_BIOGAS[kgCO2e]',
            'electricity_SOLAR[kgCO2e]', 'electricity_DRYBIOMASS[kgCO2e]', 'electricity_WETBIOMASS[kgCO2e]',
            'electricity_GRID[kgCO2e]',
            'electricity_COAL[kgCO2e]', 'electricity_WOOD[kgCO2e]', 'electricity_OIL[kgCO2e]',
            'electricity_HYDROGEN[kgCO2e]', 'electricity_NONE[kgCO2e]'
        ],
        "solar_irradiation": ['irradiation_roof[kWh]', 'irradiation_window_north[kWh]','irradiation_wall_north[kWh]',
                          'irradiation_window_south[kWh]','irradiation_wall_south[kWh]',
                          'irradiation_window_east[kWh]','irradiation_wall_east[kWh]',
                          'irradiation_window_west[kWh]','irradiation_wall_west[kWh]'],
        "pv": ['PV_installed_area_total[m2]', 'PV_electricity_total[kWh]', 'PV_installed_area_roof[m2]',
               'PV_electricity_roof[kWh]', 'PV_installed_area_north[m2]', 'PV_electricity_north[kWh]',
               'PV_installed_area_south[m2]', 'PV_electricity_south[kWh]', 'PV_installed_area_east[m2]',
               'PV_electricity_east[kWh]', 'PV_installed_area_west[m2]', 'PV_electricity_west[kWh]',
               'PV_generation_to_load[-]', 'PV_self_consumption[-]', 'PV_self_sufficiency[-]'],
        "pvt_ET": ['PVT_ET_installed_area_total[m2]', 'PVT_ET_electricity_total[kWh]', 'PVT_ET_heat_total[kWh]',
                    'PVT_ET_installed_area_roof[m2]', 'PVT_ET_electricity_roof[kWh]', 'PVT_ET_heat_roof[kWh]',
                    'PVT_ET_installed_area_north[m2]', 'PVT_ET_electricity_north[kWh]', 'PVT_ET_heat_north[kWh]',
                    'PVT_ET_installed_area_south[m2]', 'PVT_ET_electricity_south[kWh]', 'PVT_ET_heat_south[kWh]',
                    'PVT_ET_installed_area_east[m2]', 'PVT_ET_electricity_east[kWh]', 'PVT_ET_heat_east[kWh]',
                    'PVT_ET_installed_area_west[m2]', 'PVT_ET_electricity_west[kWh]', 'PVT_ET_heat_west[kWh]'],
        "pvt_FP": ['PVT_FP_installed_area_total[m2]', 'PVT_FP_electricity_total[kWh]', 'PVT_FP_heat_total[kWh]',
                    'PVT_FP_installed_area_roof[m2]', 'PVT_FP_electricity_roof[kWh]', 'PVT_FP_heat_roof[kWh]',
                    'PVT_FP_installed_area_north[m2]', 'PVT_FP_electricity_north[kWh]', 'PVT_FP_heat_north[kWh]',
                    'PVT_FP_installed_area_south[m2]', 'PVT_FP_electricity_south[kWh]', 'PVT_FP_heat_south[kWh]',
                    'PVT_FP_installed_area_east[m2]', 'PVT_FP_electricity_east[kWh]', 'PVT_FP_heat_east[kWh]',
                    'PVT_FP_installed_area_west[m2]', 'PVT_FP_electricity_west[kWh]', 'PVT_FP_heat_west[kWh]'],
        "sc_ET": ['SC_ET_installed_area_total[m2]', 'SC_ET_heat_total[kWh]',
                  'SC_ET_installed_area_roof[m2]', 'SC_ET_heat_roof[kWh]',
                  'SC_ET_installed_area_north[m2]', 'SC_ET_heat_north[kWh]',
                  'SC_ET_installed_area_south[m2]', 'SC_ET_heat_south[kWh]',
                  'SC_ET_installed_area_east[m2]', 'SC_ET_heat_east[kWh]',
                  'SC_ET_installed_area_west[m2]', 'SC_ET_heat_west[kWh]'],
        "sc_FP": ['SC_FP_installed_area_total[m2]', 'SC_FP_heat_total[kWh]',
                  'SC_FP_installed_area_roof[m2]', 'SC_FP_heat_roof[kWh]',
                  'SC_FP_installed_area_north[m2]', 'SC_FP_heat_north[kWh]',
                  'SC_FP_installed_area_south[m2]', 'SC_FP_heat_south[kWh]',
                  'SC_FP_installed_area_east[m2]', 'SC_FP_heat_east[kWh]',
                  'SC_FP_installed_area_west[m2]', 'SC_FP_heat_west[kWh]'],
        "other_renewables": ['geothermal_heat_potential[kWh]', 'area_for_ground_source_heat_pump[m2]', 'sewage_heat_potential[kWh]', 'water_body_heat_potential[kWh]'],
        "dh": ['DH_plant_thermal_load[kWh]', 'DH_plant_power[kW]',
               'DH_electricity_consumption_for_pressure_loss[kWh]', 'DH_plant_pumping_power[kW]'],
        "dc": ['DC_plant_thermal_load[kWh]', 'DC_plant_power[kW]',
               'DC_electricity_consumption_for_pressure_loss[kWh]', 'DC_plant_pumping_power[kW]'],
    }

    if direction == "metrics_to_features":
        # Find all matches
        matched_features = {feature for feature, metrics in mapping_dict.items() if set(list_metrics_or_features) & set(metrics)}

        if not matched_features:
            return None
        else:
            return list(matched_features)[0]

    elif direction == "features_to_metrics":
        # Reverse the mapping dictionary
        reverse_mapping = {feature: metrics for feature, metrics in mapping_dict.items()}
        list_metrics = []
        for feature in list_metrics_or_features:
            if feature in reverse_mapping:
                list_metrics.extend(reverse_mapping[feature])
        return list_metrics

    else:
        raise ValueError("Invalid direction. Use 'metrics_to_features' or 'features_to_metrics'.")


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
        'grid_electricity_consumption[kWh]': ['GRID_kWh'],
        'enduse_electricity_demand[kWh]': ['E_sys_kWh'],
        'enduse_cooling_demand[kWh]': ['QC_sys_kWh'],
        'enduse_space_cooling_demand[kWh]': ['Qcs_sys_kWh'],
        'enduse_heating_demand[kWh]': ['QH_sys_kWh'],
        'enduse_space_heating_demand[kWh]': ['Qhs_sys_kWh'],
        'enduse_dhw_demand[kWh]': ['Qww_kWh'],
        'irradiation_roof[kWh]': ['roofs_top_kW'],
        'irradiation_window_north[kWh]': ['windows_north_kW'],
        'irradiation_wall_north[kWh]': ['walls_north_kW'],
        'irradiation_window_south[kWh]': ['windows_south_kW'],
        'irradiation_wall_south[kWh]': ['walls_south_kW'],
        'irradiation_window_east[kWh]': ['windows_east_kW'],
        'irradiation_wall_east[kWh]': ['walls_east_kW'],
        'irradiation_window_west[kWh]': ['windows_west_kW'],
        'irradiation_wall_west[kWh]': ['walls_west_kW'],
        'PV_installed_area_total[m2]': ['area_PV_m2'],
        'PV_electricity_total[kWh]': ['E_PV_gen_kWh'],
        'PV_installed_area_roof[m2]': ['PV_roofs_top_m2'],
        'PV_electricity_roof[kWh]': ['PV_roofs_top_E_kWh'],
        'PV_installed_area_north[m2]': ['PV_walls_north_m2'],
        'PV_electricity_north[kWh]': ['PV_walls_north_E_kWh'],
        'PV_installed_area_south[m2]': ['PV_walls_south_m2'],
        'PV_electricity_south[kWh]': ['PV_walls_south_E_kWh'],
        'PV_installed_area_east[m2]': ['PV_walls_east_m2'],
        'PV_electricity_east[kWh]': ['PV_walls_east_E_kWh'],
        'PV_installed_area_west[m2]': ['PV_walls_west_m2'],
        'PV_electricity_west[kWh]': ['PV_walls_west_E_kWh'],
        'PVT_ET_installed_area_total[m2]': ['area_PVT_m2'],
        'PVT_ET_electricity_total[kWh]': ['E_PVT_gen_kWh'],
        'PVT_ET_heat_total[kWh]': ['Q_PVT_gen_kWh'],
        'PVT_ET_installed_area_roof[m2]': ['PVT_ET_roofs_top_m2'],
        'PVT_ET_electricity_roof[kWh]': ['PVT_ET_roofs_top_E_kWh'],
        'PVT_ET_heat_roof[kWh]': ['PVT_ET_roofs_top_Q_kWh'],
        'PVT_ET_installed_area_north[m2]': ['PVT_ET_walls_north_m2'],
        'PVT_ET_electricity_north[kWh]': ['PVT_ET_walls_north_E_kWh'],
        'PVT_ET_heat_north[kWh]': ['PVT_ET_walls_north_Q_kWh'],
        'PVT_ET_installed_area_south[m2]': ['PVT_ET_walls_south_m2'],
        'PVT_ET_electricity_south[kWh]': ['PVT_ET_walls_south_E_kWh'],
        'PVT_ET_heat_south[kWh]': ['PVT_ET_walls_south_Q_kWh'],
        'PVT_ET_installed_area_east[m2]': ['PVT_ET_walls_east_m2'],
        'PVT_ET_electricity_east[kWh]': ['PVT_ET_walls_east_E_kWh'],
        'PVT_ET_heat_east[kWh]': ['PVT_ET_walls_east_Q_kWh'],
        'PVT_ET_installed_area_west[m2]': ['PVT_ET_walls_west_m2'],
        'PVT_ET_electricity_west[kWh]': ['PVT_ET_walls_west_E_kWh'],
        'PVT_ET_heat_west[kWh]': ['PVT_ET_walls_west_Q_kWh'],
        'PVT_FP_installed_area_total[m2]': ['area_PVT_m2'],
        'PVT_FP_electricity_total[kWh]': ['E_PVT_gen_kWh'],
        'PVT_FP_heat_total[kWh]': ['Q_PVT_gen_kWh'],
        'PVT_FP_installed_area_roof[m2]': ['PVT_FP_roofs_top_m2'],
        'PVT_FP_electricity_roof[kWh]': ['PVT_FP_roofs_top_E_kWh'],
        'PVT_FP_heat_roof[kWh]': ['PVT_FP_roofs_top_Q_kWh'],
        'PVT_FP_installed_area_north[m2]': ['PVT_FP_walls_north_m2'],
        'PVT_FP_electricity_north[kWh]': ['PVT_FP_walls_north_E_kWh'],
        'PVT_FP_heat_north[kWh]': ['PVT_FP_walls_north_Q_kWh'],
        'PVT_FP_installed_area_south[m2]': ['PVT_FP_walls_south_m2'],
        'PVT_FP_electricity_south[kWh]': ['PVT_FP_walls_south_E_kWh'],
        'PVT_FP_heat_south[kWh]': ['PVT_FP_walls_south_Q_kWh'],
        'PVT_FP_installed_area_east[m2]': ['PVT_FP_walls_east_m2'],
        'PVT_FP_electricity_east[kWh]': ['PVT_FP_walls_east_E_kWh'],
        'PVT_FP_heat_east[kWh]': ['PVT_FP_walls_east_Q_kWh'],
        'PVT_FP_installed_area_west[m2]': ['PVT_FP_walls_west_m2'],
        'PVT_FP_electricity_west[kWh]': ['PVT_FP_walls_west_E_kWh'],
        'PVT_FP_heat_west[kWh]': ['PVT_FP_walls_west_Q_kWh'],
        'SC_ET_installed_area_total[m2]': ['area_SC_m2'],
        'SC_ET_heat_total[kWh]': ['Q_SC_gen_kWh'],
        'SC_ET_installed_area_roof[m2]': ['SC_ET_roofs_top_m2'],
        'SC_ET_heat_roof[kWh]': ['SC_ET_roofs_top_Q_kWh'],
        'SC_ET_installed_area_north[m2]': ['SC_ET_walls_north_m2'],
        'SC_ET_heat_north[kWh]': ['SC_ET_walls_north_Q_kWh'],
        'SC_ET_installed_area_south[m2]': ['SC_ET_walls_south_m2'],
        'SC_ET_heat_south[kWh]': ['SC_ET_walls_south_Q_kWh'],
        'SC_ET_installed_area_east[m2]': ['SC_ET_walls_east_m2'],
        'SC_ET_heat_east[kWh]': ['SC_ET_walls_east_Q_kWh'],
        'SC_ET_installed_area_west[m2]': ['SC_ET_walls_west_m2'],
        'SC_ET_heat_west[kWh]': ['SC_ET_walls_west_Q_kWh'],
        'SC_FP_installed_area_total[m2]': ['area_SC_m2'],
        'SC_FP_heat_total[kWh]': ['Q_FP_gen_kWh'],
        'SC_FP_installed_area_roof[m2]': ['SC_FP_roofs_top_m2'],
        'SC_FP_heat_roof[kWh]': ['SC_FP_roofs_top_Q_kWh'],
        'SC_FP_installed_area_north[m2]': ['SC_FP_walls_north_m2'],
        'SC_FP_heat_north[kWh]': ['SC_FP_walls_north_Q_kWh'],
        'SC_FP_installed_area_south[m2]': ['SC_FP_walls_south_m2'],
        'SC_FP_heat_south[kWh]': ['SC_FP_walls_south_Q_kWh'],
        'SC_FP_installed_area_east[m2]': ['SC_FP_walls_east_m2'],
        'SC_FP_heat_east[kWh]': ['SC_FP_walls_east_Q_kWh'],
        'SC_FP_installed_area_west[m2]': ['SC_FP_walls_west_m2'],
        'SC_FP_heat_west[kWh]': ['SC_FP_walls_west_Q_kWh'],
        'geothermal_heat_potential[kWh]': ['QGHP_kW'],
        'area_for_ground_source_heat_pump[m2]': ['Area_avail_m2'],
        'sewage_heat_potential[kWh]': ['Qsw_kW'],
        'water_body_heat_potential[kWh]': ['QLake_kW'],
        'DH_plant_thermal_load[kWh]': ['thermal_load_kW'],
        'DH_electricity_consumption_for_pressure_loss[kWh]': ['pressure_loss_total_kW'],
        'DC_plant_thermal_load[kWh]': ['thermal_load_kW'],
        'DC_electricity_consumption_for_pressure_loss[kWh]': ['pressure_loss_total_kW'],
        'heating[kgCO2e]': ['heating_kgCO2e'],
        'hot_water[kgCO2e]': ['hot_water_kgCO2e'],
        'cooling[kgCO2e]': ['cooling_kgCO2e'],
        'electricity[kgCO2e]': ['electricity_kgCO2e'],
        'heating_NATURALGAS[kgCO2e]': ['Qhs_sys_NATURALGAS_kgCO2e'],
        'heating_BIOGAS[kgCO2e]': ['Qhs_sys_BIOGAS_kgCO2e'],
        'heating_SOLAR[kgCO2e]': ['Qhs_sys_SOLAR_kgCO2e'],
        'heating_DRYBIOMASS[kgCO2e]': ['Qhs_sys_DRYBIOMASS_kgCO2e'],
        'heating_WETBIOMASS[kgCO2e]': ['Qhs_sys_WETBIOMASS_kgCO2e'],
        'heating_GRID[kgCO2e]': ['Qhs_sys_GRID_kgCO2e'],
        'heating_COAL[kgCO2e]': ['Qhs_sys_COAL_kgCO2e'],
        'heating_WOOD[kgCO2e]': ['Qhs_sys_WOOD_kgCO2e'],
        'heating_OIL[kgCO2e]': ['Qhs_sys_OIL_kgCO2e'],
        'heating_HYDROGEN[kgCO2e]': ['Qhs_sys_HYDROGEN_kgCO2e'],
        'heating_NONE[kgCO2e]': ['Qhs_sys_NONE_kgCO2e'],
        'hot_water_NATURALGAS[kgCO2e]': ['Qww_sys_NATURALGAS_kgCO2e'],
        'hot_water_BIOGAS[kgCO2e]': ['Qww_sys_BIOGAS_kgCO2e'],
        'hot_water_SOLAR[kgCO2e]': ['Qww_sys_SOLAR_kgCO2e'],
        'hot_water_DRYBIOMASS[kgCO2e]': ['Qww_sys_DRYBIOMASS_kgCO2e'],
        'hot_water_WETBIOMASS[kgCO2e]': ['Qww_sys_WETBIOMASS_kgCO2e'],
        'hot_water_GRID[kgCO2e]': ['Qww_sys_GRID_kgCO2e'],
        'hot_water_COAL[kgCO2e]': ['Qww_sys_COAL_kgCO2e'],
        'hot_water_WOOD[kgCO2e]': ['Qww_sys_WOOD_kgCO2e'],
        'hot_water_OIL[kgCO2e]': ['Qww_sys_OIL_kgCO2e'],
        'hot_water_HYDROGEN[kgCO2e]': ['Qww_sys_HYDROGEN_kgCO2e'],
        'hot_water_NONE[kgCO2e]': ['Qww_sys_NONE_kgCO2e'],
        'cooling_NATURALGAS[kgCO2e]': ['Qcs_sys_NATURALGAS_kgCO2e'],
        'cooling_BIOGAS[kgCO2e]': ['Qcs_sys_BIOGAS_kgCO2e'],
        'cooling_SOLAR[kgCO2e]': ['Qcs_sys_SOLAR_kgCO2e'],
        'cooling_DRYBIOMASS[kgCO2e]': ['Qcs_sys_DRYBIOMASS_kgCO2e'],
        'cooling_WETBIOMASS[kgCO2e]': ['Qcs_sys_WETBIOMASS_kgCO2e'],
        'cooling_GRID[kgCO2e]': ['Qcs_sys_GRID_kgCO2e'],
        'cooling_COAL[kgCO2e]': ['Qcs_sys_COAL_kgCO2e'],
        'cooling_WOOD[kgCO2e]': ['Qcs_sys_WOOD_kgCO2e'],
        'cooling_OIL[kgCO2e]': ['Qcs_sys_OIL_kgCO2e'],
        'cooling_HYDROGEN[kgCO2e]': ['Qcs_sys_HYDROGEN_kgCO2e'],
        'cooling_NONE[kgCO2e]': ['Qcs_sys_NONE_kgCO2e'],
        'electricity_NATURALGAS[kgCO2e]': ['E_sys_NATURALGAS_kgCO2e'],
        'electricity_BIOGAS[kgCO2e]': ['E_sys_BIOGAS_kgCO2e'],
        'electricity_SOLAR[kgCO2e]': ['E_sys_SOLAR_kgCO2e'],
        'electricity_DRYBIOMASS[kgCO2e]': ['E_sys_DRYBIOMASS_kgCO2e'],
        'electricity_WETBIOMASS[kgCO2e]': ['E_sys_WETBIOMASS_kgCO2e'],
        'electricity_GRID[kgCO2e]': ['E_sys_GRID_kgCO2e'],
        'electricity_COAL[kgCO2e]': ['E_sys_COAL_kgCO2e'],
        'electricity_WOOD[kgCO2e]': ['E_sys_WOOD_kgCO2e'],
        'electricity_OIL[kgCO2e]': ['E_sys_OIL_kgCO2e'],
        'electricity_HYDROGEN[kgCO2e]': ['E_sys_HYDROGEN_kgCO2e'],
        'electricity_NONE[kgCO2e]': ['E_sys_NONE_kgCO2e'],
        'operation_heating[kgCO2e]': ['operation_heating_kgCO2e'],
        'operation_hot_water[kgCO2e]': ['operation_hot_water_kgCO2e'],
        'operation_cooling[kgCO2e]': ['operation_cooling_kgCO2e'],
        'operation_electricity[kgCO2e]': ['operation_electricity_kgCO2e'],
        'production_wall_ag[kgCO2e]': ['production_wall_ag_kgCO2e'],
        'production_wall_bg[kgCO2e]': ['production_wall_bg_kgCO2e'],
        'production_wall_part[kgCO2e]': ['production_wall_part_kgCO2e'],
        'production_win_ag[kgCO2e]': ['production_win_ag_kgCO2e'],
        'production_roof[kgCO2e]': ['production_roof_kgCO2e'],
        'production_upperside[kgCO2e]': ['production_upperside_kgCO2e'],
        'production_underside[kgCO2e]': ['production_underside_kgCO2e'],
        'production_floor[kgCO2e]': ['production_floor_kgCO2e'],
        'production_base[kgCO2e]': ['production_base_kgCO2e'],
        'production_technical_systems[kgCO2e]': ['production_technical_systems_kgCO2e'],
        'biogenic_wall_ag[kgCO2e]': ['biogenic_wall_ag_kgCO2e'],
        'biogenic_wall_bg[kgCO2e]': ['biogenic_wall_bg_kgCO2e'],
        'biogenic_wall_part[kgCO2e]': ['biogenic_wall_part_kgCO2e'],
        'biogenic_win_ag[kgCO2e]': ['biogenic_win_ag_kgCO2e'],
        'biogenic_roof[kgCO2e]': ['biogenic_roof_kgCO2e'],
        'biogenic_upperside[kgCO2e]': ['biogenic_upperside_kgCO2e'],
        'biogenic_underside[kgCO2e]': ['biogenic_underside_kgCO2e'],
        'biogenic_floor[kgCO2e]': ['biogenic_floor_kgCO2e'],
        'biogenic_base[kgCO2e]': ['biogenic_base_kgCO2e'],
        'biogenic_technical_systems[kgCO2e]': ['biogenic_technical_systems_kgCO2e'],
        'demolition_wall_ag[kgCO2e]': ['demolition_wall_ag_kgCO2e'],
        'demolition_wall_bg[kgCO2e]': ['demolition_wall_bg_kgCO2e'],
        'demolition_wall_part[kgCO2e]': ['demolition_wall_part_kgCO2e'],
        'demolition_win_ag[kgCO2e]': ['demolition_win_ag_kgCO2e'],
        'demolition_roof[kgCO2e]': ['demolition_roof_kgCO2e'],
        'demolition_upperside[kgCO2e]': ['demolition_upperside_kgCO2e'],
        'demolition_underside[kgCO2e]': ['demolition_underside_kgCO2e'],
        'demolition_floor[kgCO2e]': ['demolition_floor_kgCO2e'],
        'demolition_base[kgCO2e]': ['demolition_base_kgCO2e'],
        'demolition_technical_systems[kgCO2e]': ['demolition_technical_systems_kgCO2e'],
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


def map_analytics_and_cea_columns(input_list, direction="analytics_to_columns"):
    """
    Maps between analytics metrics and CEA column names.

    Parameters
    ----------
    input_list : list
        A list of metrics or CEA column names to map.
    direction : str, optional
        Direction of mapping:
        - "analytics_to_columns": Maps metrics to CEA column names.
        - "columns_to_analytics": Maps CEA column names to metrics.

    Returns
    -------
    list
        A list of mapped values (CEA column names or metrics), with unique items in order.
    """
    mapping_dict = {
        'PV_generation_to_load[-]': [
            'E_PV_gen_kWh', 'PV_roofs_top_E_kWh',
            'PV_walls_north_E_kWh', 'PV_walls_south_E_kWh',
            'PV_walls_east_E_kWh', 'PV_walls_west_E_kWh'
        ],
        'PV_self_consumption[-]': [
            'E_PV_gen_kWh', 'PV_roofs_top_E_kWh',
            'PV_walls_north_E_kWh', 'PV_walls_south_E_kWh',
            'PV_walls_east_E_kWh', 'PV_walls_west_E_kWh'
        ],
        'PV_self_sufficiency[-]': [
            'E_PV_gen_kWh', 'PV_roofs_top_E_kWh',
            'PV_walls_north_E_kWh', 'PV_walls_south_E_kWh',
            'PV_walls_east_E_kWh', 'PV_walls_west_E_kWh'
        ],
    }

    # Reverse mapping for columns_to_analytics
    if direction == "columns_to_analytics":
        mapping_dict = {
            cea_col: metric
            for metric, cea_cols in mapping_dict.items()
            for cea_col in cea_cols
        }

    output_list = []
    seen = set()

    for item in input_list:
        if item in mapping_dict:
            mapped = mapping_dict[item]
            if isinstance(mapped, list):
                for m in mapped:
                    if m not in seen:
                        seen.add(m)
                        output_list.append(m)
            else:
                if mapped not in seen:
                    seen.add(mapped)
                    output_list.append(mapped)
        else:
            if item not in seen:
                seen.add(item)
                output_list.append(item)

    return output_list


def add_period_columns(df, date_column='date'):
    """
    Adds 'period_month' and 'period_season' columns to a DataFrame with 8760 rows (hourly data for a year).

    Parameters:
    - df (pd.DataFrame): DataFrame with a column named 'date' containing datetime values.
    - season_names (list of str): List of season names in order.
    - month_names (list of str): List of month names in order.
    - season_mapping (dict): Mapping of month to season.
    - date_column (str): name of the column containing datetime values.

    Returns:
    - pd.DataFrame: The original DataFrame with additional columns ['period_month', 'period_season'].
    """
    # Ensure the date column exists
    if date_column not in df.columns:
        raise ValueError(f"The column '{date_column}' is not present in the DataFrame.")

    # Convert the date column to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')

    # Check for any invalid or NaT values in the date column
    if df[date_column].isna().any():
        raise ValueError(f"The column '{date_column}' contains invalid or NaT values.")

    # Add period_month column using month names
    df['period_month'] = df[date_column].dt.month.apply(lambda x: month_names[x - 1])

    # Add period_season column using season_mapping
    df['period_season'] = df[date_column].dt.month.map(season_mapping)

    # Ensure the order of categories is maintained for month and season
    df['period_month'] = pd.Categorical(df['period_month'], categories=month_names, ordered=True)
    df['period_season'] = pd.Categorical(df['period_season'], categories=season_names, ordered=True)

    return df


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


def load_cea_results_from_csv_files(hour_start, hour_end, list_paths, list_cea_column_names) -> list[pd.DataFrame]:
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

                    # Label months and seasons
                    df = add_period_columns(df)

                    # Slice the useful columns
                    selected_columns = ['date'] + list_cea_column_names + ['period_month'] + ['period_season']
                    available_columns = [col for col in selected_columns if col in df.columns]   # check what's available
                    df = df[available_columns]

                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    df = slice_hourly_results_for_custom_time_period(hour_start, hour_end, df)   # Slice the custom period of time
                    list_dataframes.append(df)  # Add the DataFrame to the list
                elif 'period' in df.columns:
                    selected_columns = ['period'] + ['name'] + list_cea_column_names
                    available_columns = [col for col in selected_columns if col in df.columns]   # check what's available
                    df = df[available_columns]
                    list_dataframes.append(df)
                else:
                    # Slice the useful columns
                    selected_columns = ['name'] + list_cea_column_names
                    available_columns = [col for col in selected_columns if col in df.columns]   # check what's available
                    df = df[available_columns]
                    list_dataframes.append(df)  # Add the DataFrame to the list

            except Exception as e:
                print(f"Error loading {path}: {e}")
        else:
            print(f"File not found: {path}")

    return list_dataframes


# ----------------------------------------------------------------------------------------------------------------------
# Execute aggregation


def aggregate_or_combine_dataframes(bool_use_acronym, list_dataframes_uncleaned):
    """
    Aggregates or horizontally combines a list of DataFrames:
    - If all DataFrames share the same column names (excluding 'date'), aggregate corresponding cells.
    - If DataFrames have different column names, combine them horizontally based on the 'date' column.

    Parameters:
    - bool_use_acronym (bool): Whether to use acronym format for column names.
    - list_dataframes_uncleaned (list of pd.DataFrame): List of DataFrames to process.

    Returns:
    - pd.DataFrame: Aggregated or combined DataFrame.

    """

    # Ensure there are DataFrames to process
    if not list_dataframes_uncleaned:
        return None
        
    # Validate input
    if not all(isinstance(df, pd.DataFrame) for df in list_dataframes_uncleaned if df is not None):
        raise ValueError("All items in list_dataframes_uncleaned must be pandas DataFrames")

    list_dataframes = []
    columns_to_remove = ['period_month', 'period_season']

    for df in list_dataframes_uncleaned:
        # Ensure it's a DataFrame and drop the specified columns if they exist
        if isinstance(df, pd.DataFrame):
            cleaned_df = df.drop(columns=[col for col in columns_to_remove if col in df.columns], errors='ignore')
            list_dataframes.append(cleaned_df)

    # Check if all DataFrames share the same column names (excluding 'date', 'name')
    column_sets = [set(df.columns) - {'date', 'name'} for df in list_dataframes]
    all_columns_match = all(column_set == column_sets[0] for column_set in column_sets)

    def combine_dataframes(list_dataframes):
        """
        Combine a list of DataFrames horizontally. If a 'date' column exists in two or more DataFrames, it aligns them;
        otherwise, it combines them without alignment.
        """
        # Check for the 'date' column in all DataFrames
        has_date_column = [df for df in list_dataframes if 'date' in df.columns]

        if has_date_column:
            # Combine on 'date' for DataFrames that have it
            combined_df = has_date_column[0].copy()
            for df in has_date_column[1:]:
                combined_df = pd.merge(combined_df, df, on='date', how='outer')

            # Add DataFrames without 'date' as-is
            no_date_column = [df for df in list_dataframes if 'date' not in df.columns]
            for df in no_date_column:
                combined_df = pd.concat([combined_df, df], axis=1)
        else:
            # If none of the DataFrames have 'date', concatenate them directly
            combined_df = pd.concat(list_dataframes, axis=1)

        # Sort by 'date' if it exists
        if 'date' in combined_df.columns:
            combined_df.sort_values(by='date', inplace=True)
            combined_df.reset_index(drop=True, inplace=True)

        return combined_df


    if all_columns_match:
        # Aggregate DataFrames with the same columns
        if not list_dataframes:
            return None

        # Check if 'period' column exists for timeline aggregation
        has_period_column = all('period' in df.columns for df in list_dataframes)

        if has_period_column:
            # Timeline aggregation: buildings may have different start years
            # Concatenate all dataframes and aggregate by period
            combined_df = pd.concat(list_dataframes, ignore_index=True)

            # Validate 'name' column exists
            if 'name' not in combined_df.columns:
                raise ValueError("Timeline aggregation requires 'name' column in all dataframes")

            # Get numeric columns to sum
            numeric_cols = [col for col in combined_df.columns if col not in ['name', 'date', 'period']
                           and pd.api.types.is_numeric_dtype(combined_df[col])]

            # Aggregate by period, summing numeric columns
            aggregated_df = combined_df.groupby('period', as_index=False)[numeric_cols].sum()

            # Add concatenated building names
            all_building_names = ','.join(sorted(combined_df['name'].unique()))
            aggregated_df['name'] = all_building_names

        else:
            # Legacy behavior for non-timeline data with same row counts
            # Additional validation for consistent structure
            if len(set(len(df) for df in list_dataframes)) > 1:
                print("Warning: DataFrames have different numbers of rows, which may affect aggregation accuracy")

            aggregated_df = list_dataframes[0].copy()

            # Initialize aggregated_df with zeros (except date and name columns)
            for col in aggregated_df.columns:
                if col not in ['date', 'name', 'period']:
                    aggregated_df[col] = 0

            # Sum all values first
            for df in list_dataframes:
                for col in aggregated_df.columns:
                    # Only sum numeric columns, skip string columns like 'name' or 'date'
                    if pd.api.types.is_numeric_dtype(aggregated_df[col]) and pd.api.types.is_numeric_dtype(df[col]):
                        aggregated_df[col] = aggregated_df[col].add(df[col], fill_value=0)
        
        # Then apply appropriate operations
        for col in aggregated_df.columns:
            if col == 'date':
                continue
            if 'people' in col:
                # Average "people" columns and round to integer
                aggregated_df[col] = (aggregated_df[col] / len(list_dataframes)).round().astype(int)
            elif '_m2' in col or '[m2]' in col:
                # Area columns are already summed, keep as is
                pass
            else:
                # Other numeric columns are already summed, keep as is
                pass

        aggregated_df = aggregated_df.round(2)

        if not bool_use_acronym:
            aggregated_df.columns = map_metrics_and_cea_columns(aggregated_df.columns, direction="columns_to_metrics")

        return aggregated_df

    else:
        combined_df = combine_dataframes(list_dataframes)

        return combined_df


def slice_hourly_results_for_custom_time_period(hour_start, hour_end, df):
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

    # Perform slicing based on hour_start and hour_end
    if hour_start <= hour_end:
        # Normal case: Slice rows from hour_start to hour_end (hour_end is already exclusive)
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


def exec_read_and_slice(hour_start, hour_end, locator, list_metrics, list_buildings, bool_analytics=False):

    # map the CEA Feature for the selected metrics
    cea_feature = map_metrics_cea_features(list_metrics)

    # locate the path(s) to the results of the CEA Feature
    list_paths, list_appendix = get_results_path(locator, cea_feature, list_buildings)

    # get the relevant CEA column names based on selected metrics
    if not bool_analytics:
        list_cea_column_names = map_metrics_and_cea_columns(list_metrics, direction="metrics_to_columns")
    else:
        list_cea_column_names = map_analytics_and_cea_columns(list_metrics, direction="analytics_to_columns")

    list_list_useful_cea_results = []
    # check if list_paths is nested, for example, for PV, the lists can be nested as there are different types of PV
    if not check_list_nesting(list_paths):
        # get the useful CEA results for the user-selected metrics and hours
        list_useful_cea_results = load_cea_results_from_csv_files(hour_start, hour_end, list_paths, list_cea_column_names)
        list_list_useful_cea_results.append(list_useful_cea_results)
    else:
        for sublist_paths in list_paths:
            list_useful_cea_results = load_cea_results_from_csv_files(hour_start, hour_end, sublist_paths, list_cea_column_names)
            list_list_useful_cea_results.append(list_useful_cea_results)
    
    # Special handling for architecture feature
    if cea_feature == 'architecture':
        # Load source data
        zone_df = gpd.read_file(locator.get_zone_geometry()).set_index('name')
        architecture_df = pd.read_csv(locator.get_building_architecture()).set_index('name')

        # Generate architecture data using calc_useful_areas
        result_df = calc_useful_areas(zone_df, architecture_df)

        # Extract only the columns needed for architecture metrics
        architecture_data = result_df[['Af', 'footprint', 'GFA_m2', 'Aocc']].rename(columns={
            'Af': 'Af_m2',
            'footprint': 'Aroof_m2',  # Assuming footprint corresponds to roof area
            'Aocc': 'Aocc_m2'
        }).reset_index()

        list_list_useful_cea_results.append([architecture_data])
        list_appendix.append('architecture')

    return list_list_useful_cea_results, list_appendix


# ----------------------------------------------------------------------------------------------------------------------
# Execute aggregation

def aggregate_solar_data_properly_temporal(df, groupby_cols=None):
    """
    Aggregate solar data properly for TEMPORAL aggregation (hourly -> monthly/seasonal/annual):
    - Sum energy columns (E_kWh, Q_kWh) across time periods
    - Keep area columns (_m2) as the SAME CONSTANT VALUE across all time periods
    
    For district-level summaries, area columns represent total district installed area.
    This value should be IDENTICAL in annual, monthly, seasonal, daily, and hourly summaries.
    
    For example: 'PVT_ET_walls_north_m2' = total PVT area on north walls for ALL buildings combined.
    This number should appear unchanged in all time aggregations.
    
    Parameters:
    - df (pd.DataFrame): Input dataframe with solar data
    - groupby_cols (str or list): Column(s) to group by for temporal aggregation
    
    Returns:
    - pd.DataFrame or pd.Series: Properly aggregated data
    """
    if groupby_cols is not None:
        # Group by specified columns (e.g., 'period_month', 'period_season')
        grouped = df.groupby(groupby_cols, observed=True)
        
        # Separate area columns from energy columns
        area_cols = [col for col in df.columns if col.endswith('_m2') or col.endswith('[m2]')]
        energy_cols = [col for col in df.select_dtypes(include=[int, float]).columns 
                      if not col.endswith('_m2') and not col.endswith('[m2]') and col not in ([groupby_cols] if isinstance(groupby_cols, str) else groupby_cols if isinstance(groupby_cols, list) else [])]
        
        result = pd.DataFrame()
        
        # Sum energy columns across time periods
        if energy_cols:
            energy_sum = grouped[energy_cols].sum()
            result = pd.concat([result, energy_sum], axis=1)
        
        # For area columns: use the same constant value for all time periods
        # Area represents total district installation and should not change with time aggregation
        if area_cols:
            area_constant = grouped[area_cols].first()  # All rows should have same area values anyway
            result = pd.concat([result, area_constant], axis=1)
        
        # Handle remaining non-numeric columns
        remaining_cols = [col for col in df.columns if col not in energy_cols + area_cols + ([groupby_cols] if isinstance(groupby_cols, str) else groupby_cols if isinstance(groupby_cols, list) else [])]
        for col in remaining_cols:
            if pd.api.types.is_numeric_dtype(df[col]):
                result[col] = grouped[col].sum()
            else:
                result[col] = grouped[col].first()
        
        return result
    else:
        # Simple aggregation without grouping (annual aggregation)
        area_cols = [col for col in df.columns if col.endswith('_m2') or col.endswith('[m2]')]
        energy_cols = [col for col in df.select_dtypes(include=[int, float]).columns if not col.endswith('_m2') and not col.endswith('[m2]')]
        
        result = pd.Series(dtype=float)
        
        # Sum energy columns across all time
        for col in energy_cols:
            result[col] = df[col].sum()
        
        # For area columns: use the constant district total value
        # This should be the same across all hourly data points
        for col in area_cols:
            result[col] = df[col].iloc[0] if len(df) > 0 else 0
        
        # Handle remaining non-numeric columns  
        remaining_cols = [col for col in df.columns if col not in energy_cols + area_cols]
        for col in remaining_cols:
            if pd.api.types.is_numeric_dtype(df[col]):
                result[col] = df[col].sum()
            else:
                result[col] = df[col].iloc[0] if len(df) > 0 else None
        
        return result


def exec_aggregate_building_lifecycle_emissions(locator, hour_start, hour_end, summary_folder, list_metrics, bool_use_acronym,
                            list_list_useful_cea_results, list_buildings, list_appendix, list_selected_time_period,
                            date_column='date', plot=False):
    """
    Aggregates building-level results based on the provided list of DataFrames.

    Parameters:
    - bool_use_acronym (bool): Whether to map columns to acronyms.
    - list_list_useful_cea_results (list of lists of DataFrames): List of DataFrame lists to aggregate.
    - list_buildings (list): List of building names.
    - list_selected_time_period (list): List of selected time periods ('hourly', 'annually', 'monthly', 'seasonally').
    - date_column (str): The column representing datetime.

    Returns:
    - list: A list of three lists of DataFrames corresponding to the time periods:
        [hourly/annually results, monthly results, seasonally results].
    """

    for n in range(len(list_list_useful_cea_results)):
        appendix = list_appendix[n]
        list_useful_cea_results = list_list_useful_cea_results[n]

        # Initialize aggregated dataframe with all buildings
        aggregated_df = None

        for i, df in enumerate(list_useful_cea_results):
            if df is None or df.empty:
                continue

            # For lifecycle emissions, sum all rows for each building
            if aggregated_df is None:
                # First dataframe - initialize with a copy
                aggregated_df = df.copy()
            else:
                # Append subsequent dataframes and then sum by building
                aggregated_df = pd.concat([aggregated_df, df], ignore_index=True)

        # After combining all dataframes, sum all rows for each building
        if aggregated_df is not None and not aggregated_df.empty and 'name' in aggregated_df.columns:
            # Get numeric columns to sum
            numeric_cols = [col for col in aggregated_df.columns if col not in ['name', 'date']]
            # Group by building name and sum all numeric columns
            aggregated_df = aggregated_df.groupby('name', as_index=False)[numeric_cols].sum()

        if aggregated_df is not None and not aggregated_df.empty:
            # Convert column names if needed
            if not bool_use_acronym:
                aggregated_df.columns = map_metrics_and_cea_columns(aggregated_df.columns, direction="columns_to_metrics")

            # Write to disk
            cea_feature = "lifecycle_emissions"
            _cea_feature = cea_feature if not plot else cea_feature.replace("_", "-")
            _appendix = appendix if not plot else appendix.replace("_", "-")
            path = locator.get_export_results_summary_cea_feature_buildings_file(summary_folder, cea_feature=_cea_feature, appendix=_appendix)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            aggregated_df.to_csv(path, index=False, float_format='%.2f')



def exec_aggregate_building(locator, hour_start, hour_end, summary_folder, list_metrics, bool_use_acronym, list_list_useful_cea_results, list_buildings, list_appendix, list_selected_time_period, date_column='date', plot=False):
    """
    Aggregates building-level results based on the provided list of DataFrames.

    Parameters:
    - bool_use_acronym (bool): Whether to map columns to acronyms.
    - list_list_useful_cea_results (list of lists of DataFrames): List of DataFrame lists to aggregate.
    - list_buildings (list): List of building names.
    - list_selected_time_period (list): List of selected time periods ('hourly', 'annually', 'monthly', 'seasonally').
    - date_column (str): The column representing datetime.

    Returns:
    - list: A list of three lists of DataFrames corresponding to the time periods:
        [hourly/annually results, monthly results, seasonally results].
    """
    for n in range(len(list_list_useful_cea_results)):
        appendix = list_appendix[n]
        list_useful_cea_results = list_list_useful_cea_results[n]
        # Initialize separate lists for the results
        hourly_annually_results = []
        monthly_results = []
        seasonally_results = []

        annually_rows = []
        monthly_rows = []
        seasonally_rows = []

        for df in list_useful_cea_results:
            if df is None or df.empty:
                continue

            # Add labels for each hour
            df['period_hour'] = df[date_column].apply(
                lambda date: f"{(date.dayofyear - 1) * 24 + date.hour:04d}" if pd.notnull(date) else None
            )

            # Convert 'period_hour' to numeric (if it's not already)
            df['period_hour'] = pd.to_numeric(df['period_hour'], errors='coerce')

            # Handle 'monthly' aggregation
            if 'monthly' in list_selected_time_period and 'period_month' in df.columns:
                grouped_monthly = aggregate_solar_data_properly_temporal(df, 'period_month')
                grouped_monthly['period'] = grouped_monthly.index  # Add 'period' column with month names
                grouped_monthly['hour_start'] = df.groupby('period_month', observed=True)['period_hour'].first().values
                grouped_monthly['hour_end'] = df.groupby('period_month', observed=True)['period_hour'].last().values + 1
                grouped_monthly.drop(columns=['period_month', 'period_season'], errors='ignore', inplace=True)
                monthly_rows.extend(grouped_monthly.reset_index(drop=True).to_dict(orient='records'))

            # Handle 'seasonally' aggregation
            if 'seasonally' in list_selected_time_period and 'period_season' in df.columns:
                grouped_seasonally = aggregate_solar_data_properly_temporal(df, 'period_season')
                grouped_seasonally['period'] = grouped_seasonally.index  # Add 'period' column with season names
                grouped_seasonally['hour_start'] = df.groupby('period_season', observed=True)['period_hour'].first().values
                grouped_seasonally['hour_end'] = df.groupby('period_season', observed=True)['period_hour'].last().values + 1
                grouped_seasonally.drop(columns=['period_month', 'period_season'], errors='ignore', inplace=True)
                seasonally_rows.extend(grouped_seasonally.reset_index(drop=True).to_dict(orient='records'))

            # Handle 'hourly', 'annually', or no specific time period
            if not list_selected_time_period or 'hourly' in list_selected_time_period or 'annually' in list_selected_time_period:
                row_sum = aggregate_solar_data_properly_temporal(df)  # Properly aggregate solar data
                row_sum['period'] = 'selected_hours'  # Add 'period' column for this case
                row_sum['hour_start'] = df['period_hour'].iloc[0]
                row_sum['hour_end'] = df['period_hour'].iloc[-1] + 1
                row_sum.drop(labels=['period_month', 'period_season'], errors='ignore', inplace=True)
                annually_rows.append(row_sum)

        # Create DataFrames for each time period
        if annually_rows:
            hourly_annually_df = pd.DataFrame(annually_rows)
            if not hourly_annually_df.empty:
                # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
                hourly_annually_df = add_nominal_actual_and_coverage(hourly_annually_df)
                if len(hourly_annually_df) / len(hourly_annually_df['period'].unique().tolist()) == len(list_buildings):
                    hourly_annually_df.insert(0, 'name', list_buildings)
                    if not bool_use_acronym:
                        hourly_annually_df.columns = map_metrics_and_cea_columns(
                            hourly_annually_df.columns, direction="columns_to_metrics"
                        )
                    hourly_annually_results.append(hourly_annually_df.reset_index(drop=True))
                else:
                    print(f"Ensure the buildings selected for (annually) summary have all been simulated: {appendix}.".format(appendix=appendix))

        if monthly_rows:
            monthly_df = pd.DataFrame(monthly_rows)
            if not monthly_df.empty:
                if len(monthly_df) / len(monthly_df['period'].unique().tolist()) == len(list_buildings):
                    monthly_df = monthly_df[~(monthly_df['hour_start'].isnull() & monthly_df['hour_end'].isnull())]  # Remove rows with both hour_start and hour_end empty
                    # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
                    monthly_df = add_nominal_actual_and_coverage(monthly_df)
                    list_buildings_repeated = [item for item in list_buildings for _ in range(len(monthly_df['period'].unique()))]
                    list_buildings_series = pd.Series(list_buildings_repeated, index=monthly_df.index)
                    monthly_df.insert(0, 'name', list_buildings_series)
                    if not bool_use_acronym:
                        monthly_df.columns = map_metrics_and_cea_columns(
                            monthly_df.columns, direction="columns_to_metrics"
                        )
                    monthly_results.append(monthly_df.reset_index(drop=True))
                else:
                    print(f"Ensure the buildings selected for (monthly) summary have been simulated: {appendix}.".format(appendix=appendix))

        if seasonally_rows:
            seasonally_df = pd.DataFrame(seasonally_rows)
            if not seasonally_df.empty:
                seasonally_df = seasonally_df[~(seasonally_df['hour_start'].isnull() & seasonally_df['hour_end'].isnull())]  # Remove rows with both hour_start and hour_end empty

                # Handle wrap-around for periods like "Winter"
                for season in ['Winter']:
                    indices = seasonally_df['period'] == season
                    if indices.any():
                        winter_hours = df[df['period_season'] == season]['period_hour'].values
                        # Check for gaps in winter_hours
                        winter_diff = winter_hours[1:] - winter_hours[:-1]
                        gap_indices = (winter_diff > 1).nonzero()[0]  # Find indices of gaps

                        if len(gap_indices) > 0:  # Winter is non-consecutive
                            first_chunk_end = winter_hours[gap_indices[0]]  # End of the first chunk
                            second_chunk_start = winter_hours[gap_indices[0] + 1]  # Start of the second chunk
                            seasonally_df.loc[indices, 'hour_start'] = second_chunk_start
                            seasonally_df.loc[indices, 'hour_end'] = first_chunk_end
                        # If winter_hours is consecutive, no change is needed

                # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
                seasonally_df = add_nominal_actual_and_coverage(seasonally_df)
                list_buildings_repeated = [item for item in list_buildings for _ in range(len(seasonally_df['period'].unique()))]
                if len(seasonally_df) / len(seasonally_df['period'].unique().tolist()) == len(list_buildings):
                    list_buildings_series = pd.Series(list_buildings_repeated, index=seasonally_df.index)
                    seasonally_df.insert(0, 'name', list_buildings_series)
                    if not bool_use_acronym:
                        seasonally_df.columns = map_metrics_and_cea_columns(
                            seasonally_df.columns, direction="columns_to_metrics"
                        )
                    seasonally_results.append(seasonally_df.reset_index(drop=True))
                else:
                    print(f"Ensure the buildings selected for (seasonally) summary all have been simulated: {appendix}.".format(appendix=appendix))

        list_list_df = [hourly_annually_results, monthly_results, seasonally_results]
        list_time_resolution = ['annually', 'monthly', 'seasonally']

        # Write to disk
        results_writer_time_period_building(locator, hour_start, hour_end, summary_folder, list_metrics, list_list_df, [appendix], list_time_resolution, bool_analytics=False, plot=plot, bool_use_acronym=bool_use_acronym)


def add_nominal_actual_and_coverage(df):
    """
    Adds 'nominal_hours', 'actual_selected_hours', and 'coverage_ratio' columns to a DataFrame
    based on the 'period' column and existing columns 'hour_start' and 'hour_end'.

    Parameters:
    - df (pd.DataFrame): Input DataFrame with columns 'period', 'hour_start', and 'hour_end'.
    - month_names (list): List of month names in order (e.g., ['Jan', 'Feb', ...]).
    - season_names (list): List of season names (e.g., ['Winter', 'Spring', 'Summer', 'Autumn']).

    Returns:
    - pd.DataFrame: DataFrame with additional 'nominal_hours', 'actual_selected_hours', and 'coverage_ratio' columns.
    """

    if df is None or df.empty:
        return None

    if 'period' not in df.columns:
        df['period'] = df.index.tolist()
        df['period'] = df['period'].astype(str)

    # Convert 'hour_start' and 'hour_end' to numeric values
    df['hour_start'] = pd.to_numeric(df['hour_start'], errors='coerce')
    df['hour_end'] = pd.to_numeric(df['hour_end'], errors='coerce')

    # Map 'period' to nominal hours
    def calculate_nominal_hours(period):
        if period in month_hours:
            return month_hours[period]
        elif period in season_hours:
            return season_hours[period]
        elif period.startswith("D"):
            return 24
        elif period.startswith("H"):
            return 1
        elif period.startswith("Y") or period.startswith("y"):
            return 8760
        elif period == 'selected_hours':
            return 8760
        else:
            return None  # Handle unexpected values

    # Add 'nominal_hours' column
    df['nominal_hours'] = df['period'].apply(calculate_nominal_hours)
    df['nominal_hours'] = pd.to_numeric(df['nominal_hours'], errors='coerce')

    # Calculate 'actual_selected_hours'
    df['actual_selected_hours'] = df.apply(
        lambda row: abs(row['hour_end'] - row['hour_start']) + 1
        if row['hour_end'] >= row['hour_start']
        else 8760 - row['hour_start'] + 1 + row['hour_end'],
        axis=1
    )

    # Calculate 'coverage_ratio' and round to 2 decimal places
    df['coverage_ratio'] = (df['actual_selected_hours'] / df['nominal_hours']).round(2)

    # # Remove period column
    # df = df.drop(columns=['period'])

    return df


def exec_aggregate_time_period(bool_use_acronym, list_list_useful_cea_results, list_selected_time_period):

    def aggregate_by_period(df, period, date_column='date'):
        """
        Aggregates a DataFrame by a given time period with special handling for certain column types:
        - Columns containing 'people': Use .mean() and round to integer.
        - Columns containing '_m2': Use .first() (area should be constant across time periods).
        - Other columns: Use .sum().
        - Adds 'hour_start' and 'hour_end' columns for group start and end hour information.

        Parameters:
        - df (pd.DataFrame): The input DataFrame.
        - period (str): Aggregation period ('hourly', 'daily', 'monthly', 'seasonally', 'annually').
        - date_column (str): name of the date column.

        Returns:
        - pd.DataFrame: Aggregated DataFrame.
        """
        if df is None or df.empty:
            return None

        # Ensure the date column is in datetime format
        if date_column not in df.columns:
            print(f"Available columns: {df.columns.tolist()}")
            raise KeyError(f"The specified date_column '{date_column}' is not in the DataFrame.")
        if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            if df[date_column].isnull().all():
                raise ValueError(f"Failed to convert '{date_column}' to datetime format. Check the input data.")

        # Add labels for each hour
        df['period_hour'] = df[date_column].apply(
            lambda date: f"{(date.dayofyear - 1) * 24 + date.hour:04d}" if pd.notnull(date) else None
        )

        # Handle different periods
        if period == 'hourly':
            df['period'] = 'H_' + df['period_hour']
        elif period == 'daily':
            df['period'] = df[date_column].dt.dayofyear.apply(lambda x: f"D_{x - 1:03d}")
        elif period == 'monthly':
            df['period'] = df[date_column].dt.month.apply(lambda x: month_names[x - 1])
            df['period'] = pd.Categorical(df['period'], categories=month_names, ordered=True)
        elif period == 'seasonally':
            df['period'] = df[date_column].dt.month.map(season_mapping)
            df['period'] = pd.Categorical(df['period'], categories=season_names, ordered=True)
        elif period == 'annually':
            df['period'] = 'Y_' + df[date_column].dt.year.astype(str)
        else:
            raise ValueError(f"Invalid period: '{period}'. Must be one of ['hourly', 'daily', 'monthly', 'seasonally', 'annually'].")

        # Initialize an aggregated DataFrame
        aggregated_df = pd.DataFrame()

        # Process columns based on their naming
        for col in df.columns:
            if col in [date_column, 'period', 'period_hour']:
                continue

            if 'people' in col:
                aggregated_col = df.groupby('period', observed=True)[col].mean().round().astype(int)
            elif '_m2' in col or '[m2]' in col:
                # Area columns should remain constant across time periods (use first value)
                aggregated_col = df.groupby('period', observed=True)[col].first()
            else:
                # Default to sum for other columns
                aggregated_col = df.groupby('period', observed=True)[col].sum()

            aggregated_df[col] = aggregated_col

        # Convert 'period_hour' to numeric (if it's not already)
        df['period_hour'] = pd.to_numeric(df['period_hour'], errors='coerce')

        # Add hour_start and hour_end columns
        period_groups = df.groupby('period', observed=True)
        aggregated_df['hour_start'] = period_groups['period_hour'].first().values
        aggregated_df['hour_end'] = period_groups['period_hour'].last().values

        # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
        aggregated_df = add_nominal_actual_and_coverage(aggregated_df)

        # Preserve the date_column for hourly or daily periods
        if period in ['hourly', 'daily']:
            aggregated_df[date_column] = period_groups[date_column].first()

        # Drop temporary 'period_hour' column
        if 'period_hour' in aggregated_df.columns:
            aggregated_df.drop(columns=['period_hour'], inplace=True)

        # Move the period column to the first column
        cols = ['period'] + [col for col in aggregated_df.columns if col != 'period']
        aggregated_df = aggregated_df[cols]

        # Handle wrap-around for periods like "Winter"
        if period == 'seasonally':
            for season in ['Winter']:
                indices = aggregated_df['period'] == season
                if indices.any():
                    winter_hours = df[df['period'] == season]['period_hour'].values
                    # Check for gaps in winter_hours
                    winter_diff = winter_hours[1:] - winter_hours[:-1]
                    gap_indices = (winter_diff > 1).nonzero()[0]  # Find indices of gaps

                    if len(gap_indices) > 0:  # Winter is non-consecutive
                        first_chunk_end = winter_hours[gap_indices[0]]  # End of the first chunk
                        second_chunk_start = winter_hours[gap_indices[0] + 1]  # Start of the second chunk
                        aggregated_df.loc[indices, 'hour_start'] = second_chunk_start
                        aggregated_df.loc[indices, 'hour_end'] = first_chunk_end
                    # If winter_hours is consecutive, no change is needed

        return aggregated_df

    list_list_df = []
    list_list_time_period = []

    for list_useful_cea_results in list_list_useful_cea_results:
        df_aggregated_results_hourly = aggregate_or_combine_dataframes(bool_use_acronym, list_useful_cea_results)

        list_df = []
        list_time_period = []

        if 'hourly' in list_selected_time_period:
            df_hourly = aggregate_by_period(df_aggregated_results_hourly, 'hourly', date_column='date')
            # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
            df_hourly = add_nominal_actual_and_coverage(df_hourly)
            list_df.append(df_hourly)
            list_time_period.append('hourly')

        if 'daily' in list_selected_time_period:
            df_daily = aggregate_by_period(df_aggregated_results_hourly, 'daily', date_column='date')
            # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
            df_daily = add_nominal_actual_and_coverage(df_daily)
            list_df.append(df_daily)
            list_time_period.append('daily')

        if 'monthly' in list_selected_time_period:
            df_monthly = aggregate_by_period(df_aggregated_results_hourly, 'monthly', date_column='date')
            if df_monthly is not None and not df_monthly.empty:
                df_monthly = df_monthly[~(df_monthly['hour_start'].isnull() & df_monthly['hour_end'].isnull())]
            # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
            df_monthly = add_nominal_actual_and_coverage(df_monthly)
            list_df.append(df_monthly)
            list_time_period.append('monthly')

        if 'seasonally' in list_selected_time_period:
            df_seasonally = aggregate_by_period(df_aggregated_results_hourly, 'seasonally', date_column='date')
            if df_seasonally is not None and not df_seasonally.empty:
                df_seasonally = df_seasonally[~(df_seasonally['hour_start'].isnull() & df_seasonally['hour_end'].isnull())]  # Remove rows with both hour_start and hour_end empty
            # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
            df_seasonally = add_nominal_actual_and_coverage(df_seasonally)
            list_df.append(df_seasonally)
            list_time_period.append('seasonally')

        if 'annually' in list_selected_time_period:
            df_annually = aggregate_by_period(df_aggregated_results_hourly, 'annually', date_column='date')
            # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
            df_annually = add_nominal_actual_and_coverage(df_annually)
            list_df.append(df_annually)
            list_time_period.append('annually')

        list_list_df.append(list_df)
        list_list_time_period.append(list_time_period)

    return list_list_df, list_list_time_period


# Write to disk
# ----------------------------------------------------------------------------------------------------------------------


def results_writer_time_period(locator, hour_start, hour_end, summary_folder, list_metrics, list_list_df_aggregate_time_period, list_list_time_period, list_appendix, bool_analytics, plot=False):
    """
    Writes aggregated results for different time periods to CSV files.

    Parameters:
    - output_path (str): The base directory to save the results.
    - list_metrics (List[str]): A list of metrics corresponding to the results.
    - list_df_aggregate_time_period (List[pd.DataFrame]): A list of DataFrames, each representing a different aggregation period.
    """
    # Map metrics to CEA features
    cea_feature = map_metrics_cea_features(list_metrics, direction="metrics_to_features")
    if plot:
        plot_cea_feature = dict_plot_metrics_cea_feature[cea_feature]
    else:
        plot_cea_feature = None

    # Create the target path of directory
    if plot_cea_feature is not None:
        target_path = locator.get_export_plots_cea_feature_folder(plot_cea_feature)
    else:
        from cea.inputlocator import CEA_FEATURE_FOLDER_MAP
        folder_name = CEA_FEATURE_FOLDER_MAP.get(cea_feature, cea_feature)
        target_path = os.path.join(summary_folder, folder_name)

    # Create the folder if it doesn't exist
    os.makedirs(target_path, exist_ok=True)

    for m in range(len(list_list_df_aggregate_time_period)):
        list_df_aggregate_time_period = list_list_df_aggregate_time_period[m]
        list_time_period = list_list_time_period[m]
        appendix = list_appendix[m]

        # Convert underscores to hyphens if writing to plot folder
        if plot:
            cea_feature_formatted = cea_feature.replace('_', '-')
            appendix_formatted = appendix.replace('_', '-')
        else:
            cea_feature_formatted = cea_feature
            appendix_formatted = appendix

        # Write .csv files for each DataFrame
        for n in range(len(list_df_aggregate_time_period)):
            df = list_df_aggregate_time_period[n]
            time_period = list_time_period[n]
            if df is None:
                continue

            # Get the correct path based on analytics flag
            if bool_analytics:
                path_csv = locator.get_export_results_summary_cea_feature_analytics_time_resolution_file(
                    summary_folder, cea_feature, appendix, time_period, hour_start, hour_end)
            else:
                path_csv = locator.get_export_results_summary_cea_feature_time_period_file(
                    summary_folder, cea_feature_formatted, appendix_formatted, time_period, hour_start, hour_end)

            # Ensure parent directory exists
            os.makedirs(os.path.dirname(path_csv), exist_ok=True)

            # Write the CSV
            df.to_csv(path_csv, index=False, float_format="%.2f")

            # Break early for specific single-day conditions
            if len(df) == 1 and time_period in ('daily', 'monthly'):
                break


def results_writer_time_period_building(locator, hour_start, hour_end, summary_folder, list_metrics, list_list_df, list_appendix, list_time_resolution, bool_analytics, plot=False, bool_use_acronym=True):
    """
    Writes aggregated results for each building to CSV files.

    Parameters:
    - output_path (str): The base directory to save the results.
    - list_metrics (List[str]): A list of metrics corresponding to the results.
    - list_df (List[pd.DataFrame]): A list of DataFrames.
    """

    # Map metrics to CEA features
    if list_metrics is not None and len(list_metrics) > 0:
        cea_feature = map_metrics_cea_features(list_metrics, direction="metrics_to_features")
    else:
        cea_feature = list_appendix

    if plot:
        plot_cea_feature = dict_plot_metrics_cea_feature[cea_feature]
    else:
        plot_cea_feature = None

    # Join the paths
    if plot_cea_feature is not None:
        target_path = locator.get_export_plots_cea_feature_folder(plot_cea_feature)
    else:
        from cea.inputlocator import CEA_FEATURE_FOLDER_MAP
        folder_name = CEA_FEATURE_FOLDER_MAP.get(cea_feature, cea_feature)
        target_path = os.path.join(summary_folder, folder_name)

    # Create the folder if it doesn't exist
    os.makedirs(target_path, exist_ok=True)

    for m in range(len(list_list_df)):
        list_df = list_list_df[m]
        appendix = list_appendix[0]

        if plot_cea_feature is None:
            if appendix in ('architecture', 'lifecycle_emissions'):
                # Create the .csv file path
                if appendix == 'lifecycle_emissions':
                    path_csv = locator.get_export_results_summary_cea_feature_timeline_file(summary_folder, cea_feature, appendix)
                else:
                    path_csv = locator.get_export_results_summary_cea_feature_buildings_file(summary_folder, cea_feature, appendix)
                os.makedirs(locator.get_export_results_summary_cea_feature_analytics_folder(summary_folder, cea_feature), exist_ok=True)
            else:
                if not bool_analytics:
                    time_resolution = list_time_resolution[m]
                    path_csv = locator.get_export_results_summary_cea_feature_time_resolution_buildings_file(summary_folder, cea_feature, appendix, time_resolution, hour_start, hour_end)
                    os.makedirs(locator.get_export_results_summary_cea_feature_analytics_folder(summary_folder, cea_feature), exist_ok=True)
                else:
                    os.makedirs(locator.get_export_results_summary_cea_feature_analytics_folder(summary_folder, cea_feature), exist_ok=True)
                    time_resolution = list_time_resolution[m]
                    path_csv = locator.get_export_results_summary_cea_feature_analytics_time_resolution_buildings_file(summary_folder, cea_feature, appendix, time_resolution, hour_start, hour_end)
        else:
            # Convert underscores to hyphens for plot file paths
            plot_cea_feature_formatted = plot_cea_feature.replace('_', '-')
            appendix_formatted = appendix.replace('_', '-')
            cea_feature_formatted = cea_feature.replace('_', '-')

            if appendix in ('architecture'):
                # Create the .csv file path
                os.makedirs(locator.get_export_plots_cea_feature_folder(plot_cea_feature_formatted), exist_ok=True)
                path_csv = locator.get_export_plots_cea_feature_buildings_file(plot_cea_feature_formatted, appendix_formatted)
            elif appendix in ('lifecycle_emissions'):
                os.makedirs(locator.get_export_plots_cea_feature_folder(plot_cea_feature_formatted), exist_ok=True)
                path_csv = locator.get_export_results_summary_cea_feature_timeline_file(summary_folder, cea_feature_formatted, appendix_formatted)
            else:
                if not bool_analytics:
                    time_resolution = list_time_resolution[m]
                    path_csv = locator.get_export_plots_cea_feature_time_resolution_buildings_file(plot_cea_feature_formatted, appendix_formatted, time_resolution, hour_start, hour_end)
                    os.makedirs(locator.get_export_plots_cea_feature_folder(plot_cea_feature_formatted), exist_ok=True)
                else:
                    os.makedirs(locator.get_export_plots_cea_feature_folder(plot_cea_feature_formatted), exist_ok=True)
                    time_resolution = list_time_resolution[m]
                    path_csv = locator.get_export_plots_cea_feature_analytics_time_resolution_buildings_file(plot_cea_feature_formatted, appendix_formatted, time_resolution, hour_start, hour_end)

        if appendix == 'lifecycle_emissions':
            df_timeline = aggregate_or_combine_dataframes(bool_use_acronym, list_df)
            if df_timeline is not None:
                df_timeline.to_csv(path_csv, index=False, float_format="%.4f")

        else:
            # Write to .csv files
            for df in list_df:
                if not df.empty:
                    df.to_csv(path_csv, index=False, float_format="%.4f")


# Filter by criteria for buildings
# ----------------------------------------------------------------------------------------------------------------------


def filter_cea_results_by_buildings(bool_use_acronym, list_list_useful_cea_results, list_buildings):
    """
    Filters rows in all DataFrames within a nested list of DataFrames,
    keeping only rows where the 'name' column matches any value in list_buildings.

    Parameters:
    - list_list_useful_cea_results (list of lists of pd.DataFrame): Nested list of DataFrames.
    - list_buildings (list of str): List of building names to filter by in the 'name' column.

    Returns:
    - list of list of pd.DataFrame: Nested list of filtered DataFrames with the same shape as the input.
    """

    list_list_useful_cea_results_buildings = []

    for dataframe_list in list_list_useful_cea_results:
        filtered_list = []
        for df in dataframe_list:
            if 'name' in df.columns:
                filtered_df = df[df['name'].isin(list_buildings)]

                if not bool_use_acronym:
                    filtered_df.columns = map_metrics_and_cea_columns(filtered_df.columns, direction="columns_to_metrics")

                filtered_list.append(filtered_df)

            else:
                # If the 'name' column does not exist, append an empty DataFrame
                print("Skipping a DataFrame as it does not contain the 'name' column.")
                filtered_list.append(pd.DataFrame())
        list_list_useful_cea_results_buildings.append(filtered_list)

    return list_list_useful_cea_results_buildings


def determine_building_main_use(df_typology):

    # Create a new DataFrame to store results
    result = pd.DataFrame()
    result['name'] = df_typology['name']

    # Determine the main use type and its ratio
    result['main_use_type'] = df_typology.apply(
        lambda row: row['use_type1'] if row['use_type1r'] >= max(row['use_type2r'], row['use_type3r']) else
                    row['use_type2'] if row['use_type2r'] >= row['use_type3r'] else
                    row['use_type3'],
        axis=1
    )
    result['main_use_type_ratio'] = df_typology.apply(
        lambda row: row['use_type1r'] if row['use_type1r'] >= max(row['use_type2r'], row['use_type3r']) else
                    row['use_type2r'] if row['use_type2r'] >= row['use_type3r'] else
                    row['use_type3r'],
        axis=1
    )

    return result


def get_building_year_standard_main_use_type(locator):

    zone_dbf = gpd.read_file(locator.get_zone_geometry())
    df = determine_building_main_use(zone_dbf)
    df['construction_type'] = zone_dbf['const_type']
    df['construction_year'] = zone_dbf['year']

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
        (df_typology['construction_year'] >= integer_year_start) & (df_typology['construction_year'] <= integer_year_end)
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
    - ValueError: If 'const_type' column is not found or if the filtered DataFrame is empty.
    """

    # Filter rows where 'standard' matches any value in list_standard
    filtered_df = df_typology[df_typology['construction_type'].isin(list_standard)]

    # Check if the filtered DataFrame is empty
    if filtered_df.empty:
        raise ValueError("No buildings meet the selected criteria for the specified standards.")

    return filtered_df


def filter_by_main_use(df_typology, list_main_use_type):
    """
    Filters rows in the DataFrame based on whether the 'main_use_type' column matches any item in list_main_use_type.

    Parameters:
    - df_typology (pd.DataFrame): DataFrame with a 'main_use_type' column.
    - list_main_use_type (list): List of main use types to filter on.

    Returns:
    - pd.DataFrame: Filtered DataFrame with rows where 'main_use_type' matches any item in list_main_use_type.

    Raises:
    - ValueError: If 'main_use_type' column is not found or if the filtered DataFrame is empty.
    """
    if 'main_use_type' not in df_typology.columns:
        raise ValueError("'main_use_type' column not found in the DataFrame.")

    # Filter rows where 'main_use_type' matches any value in list_main_use_type
    filtered_df = df_typology[df_typology['main_use_type'].isin(list_main_use_type)]

    # Check if the filtered DataFrame is empty
    if filtered_df.empty:
        raise ValueError("No buildings meet the selected criteria for the specified main use types.")

    return filtered_df


def filter_by_main_use_ratio(df_typology, ratio_main_use_type):
    """
    Filters rows in the DataFrame where the 'main_use_type_ratio' column is equal to or larger than a given ratio.

    Parameters:
    - df_typology (pd.DataFrame): DataFrame with a 'main_use_type_ratio' column.
    - ratio_main_use_type (float): The minimum ratio threshold for filtering.

    Returns:
    - pd.DataFrame: Filtered DataFrame with rows where 'main_use_type_ratio' >= ratio_main_use_type.

    Raises:
    - ValueError: If 'main_use_type_ratio' column is not found or if the filtered DataFrame is empty.
    """

    # Filter rows where 'main_use_type_ratio' is greater than or equal to the threshold
    filtered_df = df_typology[df_typology['main_use_type_ratio'] >= ratio_main_use_type]

    # Check if the filtered DataFrame is empty
    if filtered_df.empty:
        raise ValueError("No buildings meet the criteria for the specified main use ratio.")

    return filtered_df


def filter_by_building_names(df_typology, list_buildings):
    """
    Filters rows in the DataFrame where the 'name' column matches any item in the given list.

    Parameters:
    - df_typology (pd.DataFrame): The input DataFrame containing a 'name' column.
    - list_buildings (list of str): List of building names to filter for.

    Returns:
    - pd.DataFrame: Filtered DataFrame with rows where 'name' matches any item in list_buildings.

    Raises:
    - ValueError: If 'name' column is not found or if the filtered DataFrame is empty.
    """
    if 'name' not in df_typology.columns:
        raise ValueError("'name' column not found in the DataFrame.")

    # Filter rows where 'name' is in list_buildings
    filtered_df = df_typology[df_typology['name'].isin(list_buildings)]

    # Check if the filtered DataFrame is empty
    if filtered_df.empty:
        raise ValueError("No buildings match the specified list of names.")

    return filtered_df



# ----------------------------------------------------------------------------------------------------------------------
# Execute advanced UBEM analytics

def calc_pv_analytics(locator, hour_start, hour_end, summary_folder, list_buildings, list_selected_time_period, bool_aggregate_by_building, bool_use_acronym, plot=False):
    list_pv_analytics = ['PV_generation_to_load[-]', 'PV_self_consumption[-]', 'PV_self_sufficiency[-]']
    list_demand_metrics = ['grid_electricity_consumption[kWh]']
    list_list_useful_cea_results_pv, list_appendix = exec_read_and_slice(hour_start, hour_end, locator, list_pv_analytics, list_buildings, bool_analytics=True)
    list_list_useful_cea_results_demand, _ = exec_read_and_slice(hour_start, hour_end, locator, list_demand_metrics, list_buildings)

    def replace_kwh_with_pv_analytic(string, pv_analytic):
        """
        Replaces the end of a string with 'a' if it ends with '_kWh'.

        Parameters:
        - string (str): The input string.

        Returns:
        - str: The modified string.
        """
        if string.startswith('E_PV_gen_kWh'):
            return pv_analytic
        if string.endswith('_E_kWh'):
            return string[:-5] + pv_analytic
        return string  # Return the string unchanged if condition not met

    def calc_pv_analytics_by_period(df_pv, df_demand, period, list_pv_analytics, bool_use_acronym, date_column='date'):
        """
        Calculates the three pv analytics for a given time period and
        adds 'hour_start' and 'hour_end' columns for group start and end hour information.

        Parameters:
        - df (pd.DataFrame): The input DataFrame.
        - period (str): Aggregation period ('hourly', 'daily', 'monthly', 'seasonally', 'annually').
        - date_column (str): name of the date column.

        Returns:
        - pd.DataFrame: Aggregated DataFrame.

        """
        if df_pv is None or df_demand is None or df_pv.empty or df_demand.empty:
            return None

        # Merge df_pv and df_demand
        # Check what columns are actually available and adapt accordingly
        if 'GRID_kWh' in df_demand.columns:
            demand_column = 'GRID_kWh'
        elif 'grid_electricity_consumption[kWh]' in df_demand.columns:
            demand_column = 'grid_electricity_consumption[kWh]'
        else:
            raise ValueError(f"Neither 'GRID_kWh' nor 'grid_electricity_consumption[kWh]' found in df_demand columns: {list(df_demand.columns)}")
        
        df = pd.concat([df_pv, df_demand[demand_column]], axis=1)   # Concatenate the DataFrames horizontally
        df = df.loc[:, ~df.columns.duplicated()]    # Remove duplicate columns, keeping the first occurrence

        # # Remove 'PV_' in the strings of PV analytics
        # list_analytics = [item[3:] if item.startswith('PV_') else item for item in list_pv_analytics]
        list_analytics = list_pv_analytics

        # Ensure the date column is in datetime format
        if date_column not in df.columns:
            raise KeyError(f"The specified date_column '{date_column}' is not in the DataFrame.")
        if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            if df[date_column].isnull().all():
                raise ValueError(f"Failed to convert '{date_column}' to datetime format. Check the input data.")

        # Add labels for each hour
        df['period_hour'] = df[date_column].apply(
            lambda date: f"{(date.dayofyear - 1) * 24 + date.hour:04d}" if pd.notnull(date) else None
        )

        # Handle different periods
        if period == 'daily':
            df['period'] = df[date_column].dt.dayofyear.apply(lambda x: f"D_{x - 1:03d}")
        elif period == 'monthly':
            df['period'] = df[date_column].dt.month.apply(lambda x: month_names[x - 1])
            df['period'] = pd.Categorical(df['period'], categories=month_names, ordered=True)
        elif period == 'seasonally':
            df['period'] = df[date_column].dt.month.map(season_mapping)
            df['period'] = pd.Categorical(df['period'], categories=season_names, ordered=True)
        elif period == 'annually':
            df['period'] = 'Y_' + df[date_column].dt.year.astype(str)
        else:
            raise ValueError(f"Invalid period: '{period}'. Must be one of ['hourly', 'daily', 'monthly', 'seasonally', 'annually'].")

        # Initialize an aggregated DataFrame
        pv_analytics_df = pd.DataFrame()

        # Process columns based on their naming
        for col in df.columns:
            if col in [date_column, demand_column, 'period', 'period_hour']:
                continue
            else:
                for pv_analytic in list_analytics:
                    col_new = replace_kwh_with_pv_analytic(col, pv_analytic)
                    if pv_analytic == 'PV_generation_to_load[-]':
                        pv_analytic_df = calc_solar_energy_penetration_by_period(df, col, demand_column)
                        pv_analytics_df[col_new] = pv_analytic_df[col]
                        pv_analytics_df['period'] = pv_analytic_df['period']
                    elif pv_analytic == 'PV_self_consumption[-]':
                        pv_analytic_df = calc_self_consumption_by_period(df, col, demand_column)
                        pv_analytics_df[col_new] = pv_analytic_df[col]
                        pv_analytics_df['period'] = pv_analytic_df['period']
                    elif pv_analytic == 'PV_self_sufficiency[-]':
                        pv_analytic_df = calc_self_sufficiency_by_period(df, col, demand_column)
                        pv_analytics_df[col_new] = pv_analytic_df[col]
                        pv_analytics_df['period'] = pv_analytic_df['period']

        # Convert 'period_hour' to numeric (if it's not already)
        df['period_hour'] = pd.to_numeric(df['period_hour'], errors='coerce')

        # Add hour_start and hour_end columns
        period_groups = df.groupby('period', observed=True)
        pv_analytics_df['hour_start'] = period_groups['period_hour'].first().values
        pv_analytics_df['hour_end'] = period_groups['period_hour'].last().values

        # Handle wrap-around for periods like "Winter"
        if period == 'seasonally':
            for season in ['Winter']:
                indices = pv_analytics_df['period'] == season
                if indices.any():
                    winter_hours = df[df['period'] == season]['period_hour'].values
                    # Check for gaps in winter_hours
                    winter_diff = winter_hours[1:] - winter_hours[:-1]
                    gap_indices = (winter_diff > 1).nonzero()[0]  # Find indices of gaps

                    if len(gap_indices) > 0:  # Winter is non-consecutive
                        first_chunk_end = winter_hours[gap_indices[0]]  # End of the first chunk
                        second_chunk_start = winter_hours[gap_indices[0] + 1]  # Start of the second chunk
                        pv_analytics_df.loc[indices, 'hour_start'] = second_chunk_start
                        pv_analytics_df.loc[indices, 'hour_end'] = first_chunk_end
                    # If winter_hours is consecutive, no change is needed

        # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
        pv_analytics_df = add_nominal_actual_and_coverage(pv_analytics_df)

        # Drop temporary 'period_hour' column
        if 'period_hour' in pv_analytics_df.columns:
            pv_analytics_df.drop(columns=['period_hour'], inplace=True)

        # Move the period column to the first column
        cols = ['period'] + [col for col in pv_analytics_df.columns if col != 'period']
        pv_analytics_df = pv_analytics_df[cols]

        return pv_analytics_df

    list_list_df = []
    list_list_time_period = []

    # For the district
    for list_useful_cea_results_pv in list_list_useful_cea_results_pv:
        df_pv = aggregate_or_combine_dataframes(True, list_useful_cea_results_pv)   #hourly DataFrame for all selected buildings - pv
        df_demand = aggregate_or_combine_dataframes(bool_use_acronym, list_list_useful_cea_results_demand[0])   #hourly DataFrame for all selected buildings - demand

        list_df = []
        list_time_period = []

        if 'daily' in list_selected_time_period:
            df_daily = calc_pv_analytics_by_period(df_pv, df_demand, 'daily', list_pv_analytics, bool_use_acronym, date_column='date')
            # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
            df_daily = add_nominal_actual_and_coverage(df_daily)
            list_df.append(df_daily)
            list_time_period.append('daily')

        if 'monthly' in list_selected_time_period:
            df_monthly = calc_pv_analytics_by_period(df_pv, df_demand, 'monthly', list_pv_analytics, bool_use_acronym, date_column='date')
            if df_monthly is not None and not df_monthly.empty:
                df_monthly = df_monthly[~(df_monthly['hour_start'].isnull() & df_monthly['hour_end'].isnull())]
            # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
            df_monthly = add_nominal_actual_and_coverage(df_monthly)
            list_df.append(df_monthly)
            list_time_period.append('monthly')

        if 'seasonally' in list_selected_time_period:
            df_seasonally = calc_pv_analytics_by_period(df_pv, df_demand, 'seasonally', list_pv_analytics, bool_use_acronym, date_column='date')
            if df_seasonally is not None and not df_seasonally.empty:
                df_seasonally = df_seasonally[~(df_seasonally['hour_start'].isnull() & df_seasonally['hour_end'].isnull())]  # Remove rows with both hour_start and hour_end empty
            # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
            df_seasonally = add_nominal_actual_and_coverage(df_seasonally)
            list_df.append(df_seasonally)
            list_time_period.append('seasonally')

        if 'annually' in list_selected_time_period:
            df_annually = calc_pv_analytics_by_period(df_pv, df_demand, 'annually', list_pv_analytics, bool_use_acronym, date_column='date')
            # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
            df_annually = add_nominal_actual_and_coverage(df_annually)
            list_df.append(df_annually)
            list_time_period.append('annually')

        list_list_df.append(list_df)
        list_list_time_period.append(list_time_period)

    # Write to disk - district
    results_writer_time_period(locator, hour_start, hour_end, summary_folder, list_pv_analytics, list_list_df, list_list_time_period, list_appendix, bool_analytics=True, plot=plot)

    if bool_aggregate_by_building:
        # For each building
        for pv_type in range(len(list_list_useful_cea_results_pv)):

            annually_results = []
            seasonally_results = []
            monthly_results = []

            appendix = list_appendix[pv_type]
            list_useful_cea_results_pv = list_list_useful_cea_results_pv[pv_type]

            annually_rows = []
            monthly_rows = []
            seasonally_rows = []

            for df_pv, df_demand in zip(list_useful_cea_results_pv, list_list_useful_cea_results_demand[0]):

                # Clean the unnecessary columns
                columns_to_drop = ['period_hour', 'period_season', 'period_month']
                df_pv_cleaned = df_pv.drop(columns=[col for col in columns_to_drop if col in df_pv.columns], errors='ignore')

                if 'monthly' in list_selected_time_period:
                    df_monthly = calc_pv_analytics_by_period(df_pv_cleaned, df_demand, 'monthly', list_pv_analytics, bool_use_acronym, date_column='date')
                    if df_monthly is not None and not df_monthly.empty:
                        df_monthly = df_monthly[~(df_monthly['hour_start'].isnull() & df_monthly['hour_end'].isnull())]
                    # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
                    df_monthly = add_nominal_actual_and_coverage(df_monthly)
                    monthly_rows.extend(df_monthly.reset_index(drop=True).to_dict(orient='records'))

                if 'seasonally' in list_selected_time_period:
                    df_seasonally = calc_pv_analytics_by_period(df_pv_cleaned, df_demand, 'seasonally', list_pv_analytics, bool_use_acronym, date_column='date')
                    if df_seasonally is not None and not df_seasonally.empty:
                        df_seasonally = df_seasonally[~(df_seasonally['hour_start'].isnull() & df_seasonally['hour_end'].isnull())]  # Remove rows with both hour_start and hour_end empty
                    # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
                    df_seasonally = add_nominal_actual_and_coverage(df_seasonally)
                    seasonally_rows.extend(df_seasonally.reset_index(drop=True).to_dict(orient='records'))

                if 'annually' in list_selected_time_period:
                    df_annually = calc_pv_analytics_by_period(df_pv_cleaned, df_demand, 'annually', list_pv_analytics, bool_use_acronym, date_column='date')
                    # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
                    df_annually = add_nominal_actual_and_coverage(df_annually)
                    annually_rows.extend(df_annually.reset_index(drop=True).to_dict(orient='records'))

            # Create DataFrames for each time period
            if annually_rows:
                annually_df = pd.DataFrame(annually_rows)
                if not annually_df.empty:
                    # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
                    annually_df = add_nominal_actual_and_coverage(annually_df)
                    annually_df.insert(0, 'name', list_buildings)
                    annually_results.append(annually_df.reset_index(drop=True))

            if monthly_rows:
                monthly_df = pd.DataFrame(monthly_rows)
                if not monthly_df.empty:
                    monthly_df = monthly_df[~(monthly_df['hour_start'].isnull() & monthly_df['hour_end'].isnull())]  # Remove rows with both hour_start and hour_end empty
                    # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
                    monthly_df = add_nominal_actual_and_coverage(monthly_df)
                    list_buildings_repeated = [item for item in list_buildings for _ in range(len(monthly_df['period'].unique()))]
                    list_buildings_series = pd.Series(list_buildings_repeated, index=monthly_df.index)
                    monthly_df.insert(0, 'name', list_buildings_series)
                    monthly_results.append(monthly_df.reset_index(drop=True))

            if seasonally_rows:
                seasonally_df = pd.DataFrame(seasonally_rows)
                if not seasonally_df.empty:
                    seasonally_df = seasonally_df[~(seasonally_df['hour_start'].isnull() & seasonally_df['hour_end'].isnull())]  # Remove rows with both hour_start and hour_end empty
                    # Add coverage ratios, hours fall into the selected hours divided by the nominal hours of the period
                    seasonally_df = add_nominal_actual_and_coverage(seasonally_df)
                    list_buildings_repeated = [item for item in list_buildings for _ in range(len(seasonally_df['period'].unique()))]
                    list_buildings_series = pd.Series(list_buildings_repeated, index=seasonally_df.index)
                    seasonally_df.insert(0, 'name', list_buildings_series)
                    seasonally_results.append(seasonally_df.reset_index(drop=True))

            list_list_df = [annually_results, monthly_results, seasonally_results]
            list_time_period = ['annually', 'monthly', 'seasonally']

            # Write to disk
            results_writer_time_period_building(locator, hour_start, hour_end, summary_folder, list_pv_analytics, list_list_df, [appendix], list_time_period, bool_analytics=True, plot=plot, bool_use_acronym=bool_use_acronym)


def calc_solar_energy_penetration_by_period(df, col, demand_col='GRID_kWh'):
    """
    Calculate solar energy penetration by period.

    Parameters:
    - df (pd.DataFrame): Input DataFrame with columns `col` (hourly PV yield),
                         `demand_col` (hourly energy demand),
                         and `period` (grouping period such as seasons or days).
    - col (str): Column name for hourly PV yield.
    - demand_col (str): Column name for grid electricity consumption.

    Returns:
    - pd.DataFrame: A DataFrame with the penetration calculation for each unique period.
    """
    # Ensure the required columns are present in the DataFrame
    required_columns = [col, demand_col, 'period']
    missing_columns = [c for c in required_columns if c not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Group by the 'period' column and calculate the penetration ratio
    grouped = df.groupby('period', observed=True).apply(
        lambda group: group[col].sum() / group[demand_col].sum()
        if group[demand_col].sum() != 0 else 0,
        include_groups=False
    )

    # Format the result into a new DataFrame
    df_new = grouped.reset_index(name=col)
    df_new[col] = df_new[col].round(2)  # Round to two decimal places

    return df_new


def calc_self_sufficiency_by_period(df, col, demand_col='GRID_kWh'):
    """
    Calculate self-sufficiency of solar energy by period.

    Parameters:
    - df (pd.DataFrame): Input DataFrame with columns `col` (hourly PV yield),
                         `demand_col` (hourly energy demand),
                         and `period` (grouping period such as seasons or days).
    - col (str): Column name for hourly PV yield.
    - demand_col (str): Column name for grid electricity consumption.

    Returns:
    - pd.DataFrame: A DataFrame with the self-sufficiency calculation for each unique period.
    """
    # Ensure the required columns are present in the DataFrame
    required_columns = [col, demand_col, 'period']
    missing_columns = [c for c in required_columns if c not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Group by the 'period' column and calculate the self-sufficiency ratio
    grouped = df.groupby('period', observed=True).apply(
        lambda group: (
            min(group[col].sum(), group[demand_col].sum()) /
            group[demand_col].sum()
            if group[demand_col].sum() != 0 else 0
        ),
        include_groups=False
    )

    # Format the result into a new DataFrame
    df_new = grouped.reset_index(name=col)
    df_new[col] = df_new[col].round(2)  # Round to two decimal places

    return df_new


def calc_self_consumption_by_period(df, col, demand_col='GRID_kWh'):
    """
    Calculate self-consumption of solar energy by period.

    Parameters:
    - df (pd.DataFrame): Input DataFrame with columns `col` (hourly PV yield),
                         `demand_col` (hourly energy demand),
                         and `period` (grouping period such as seasons or days).
    - col (str): Column name for hourly PV yield.
    - demand_col (str): Column name for grid electricity consumption.

    Returns:
    - pd.DataFrame: A DataFrame with the self-consumption calculation for each unique period.
    """
    # Ensure the required columns are present in the DataFrame
    required_columns = [col, demand_col, 'period']
    missing_columns = [c for c in required_columns if c not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Group by the 'period' column and calculate the self-consumption ratio
    grouped = df.groupby('period', observed=True).apply(
        lambda group: (
    min(group[col].sum(), group[demand_col].sum()) /
    group[col].sum()
    if group[col].sum() != 0 else 0
    ), include_groups=False)
    # Format the result into a new DataFrame
    df_new = grouped.reset_index(name=col)
    df_new[col] = df_new[col].round(2)  # Round to two decimal places

    return df_new


def calc_ubem_analytics_normalised(locator, hour_start, hour_end, cea_feature, summary_folder, list_time_period,
                                   bool_aggregate_by_building, bool_use_acronym,
                                   bool_use_conditioned_floor_area_for_normalisation, plot=False):
    """
    Normalizes UBEM analytics based on floor area and writes the results.
    """
    appendix = cea_feature
    list_metrics = map_metrics_cea_features([cea_feature], direction="features_to_metrics")
    list_result_time_resolution = []
    list_result_buildings = []

    if plot:
        plot_cea_feature = dict_plot_metrics_cea_feature[cea_feature]
    else:
        plot_cea_feature = None

    # Read and process the architecture DataFrame
    if plot_cea_feature is not None:
        df_building_path = locator.get_export_plots_selected_building_file()
    else:
        df_building_path = locator.get_export_results_summary_selected_building_file(summary_folder)
    df_architecture = pd.read_csv(df_building_path)

    if bool_use_acronym:
        df_architecture.columns = map_metrics_and_cea_columns(df_architecture.columns, direction="columns_to_metrics")

    # Helper function for normalization
    def normalize_dataframe(df, area_column):
        if area_column not in df_architecture.columns:
            raise ValueError(f"Column '{area_column}' not found in architecture data.")
        total_area = df_architecture[area_column].sum()
        df[list_metrics] = df[list_metrics].div(total_area)
        return df

    for time_period in list_time_period:
        # Time resolution processing
        df_time_path = locator.get_export_results_summary_cea_feature_time_period_file(
            summary_folder, cea_feature, appendix, time_period, hour_start, hour_end
        )

        if not os.path.exists(df_time_path):
            print(f"File not found: {df_time_path}.")
            break
        else:
            df_time_resolution = pd.read_csv(df_time_path)

        if bool_use_acronym:
            df_time_resolution.columns = map_metrics_and_cea_columns(
                df_time_resolution.columns, direction="columns_to_metrics"
            )

        area_column = 'conditioned_floor_area[m2]' if bool_use_conditioned_floor_area_for_normalisation else 'gross_floor_area[m2]'
        df_time_resolution = normalize_dataframe(df_time_resolution, area_column)

        result_time_resolution = df_time_resolution.rename(columns=normalisation_name_mapping)
        list_result_time_resolution.append(result_time_resolution)

        # Write to disk
        results_writer_time_period(locator, hour_start, hour_end, summary_folder, list_metrics, [list_result_time_resolution], [list_time_period], [appendix], bool_analytics=True, plot=plot)

        # Aggregate by building
        if bool_aggregate_by_building:
            if time_period in ['hourly', 'daily']:
                continue

            else:
                df_buildings_path = locator.get_export_results_summary_cea_feature_time_resolution_buildings_file(
                    summary_folder, cea_feature, appendix, time_period, hour_start, hour_end
                )
                if os.path.exists(df_buildings_path):
                    df_buildings = pd.read_csv(df_buildings_path)

                    if bool_use_acronym:
                        df_buildings.columns = map_metrics_and_cea_columns(df_buildings.columns, direction="columns_to_metrics")

                    result_buildings = pd.merge(
                        df_buildings,
                        df_architecture[['name', area_column]],
                        on='name', how='inner'
                    )
                    for col in list_metrics:
                        if col in result_buildings.columns:
                            result_buildings[col] = result_buildings[col] / result_buildings[area_column]
                    result_buildings.drop(columns=[area_column], inplace=True)

                    result_buildings = result_buildings.rename(columns=normalisation_name_mapping)

                    list_result_buildings.append(result_buildings)

                    results_writer_time_period_building(locator, hour_start, hour_end, summary_folder, list_metrics,
                    [list_result_buildings], [appendix], [time_period], bool_analytics=True, plot=plot, bool_use_acronym=bool_use_acronym)
                else:
                    print("Aggregation by buildings was skipped as the required input file was not found: {appendix}.".format(appendix=appendix))


# ----------------------------------------------------------------------------------------------------------------------
# Prepare the lists of metrics

list_metrics_building_energy_demand = ['grid_electricity_consumption[kWh]','enduse_electricity_demand[kWh]','enduse_cooling_demand[kWh]','enduse_space_cooling_demand[kWh]','enduse_heating_demand[kWh]','enduse_space_heating_demand[kWh]','enduse_dhw_demand[kWh]']
list_metrics_solar_irradiation = ['irradiation_roof[kWh]', 'irradiation_window_north[kWh]', 'irradiation_wall_north[kWh]', 'irradiation_window_south[kWh]', 'irradiation_wall_south[kWh]', 'irradiation_window_east[kWh]', 'irradiation_wall_east[kWh]', 'irradiation_window_west[kWh]', 'irradiation_wall_west[kWh]']
list_metrics_photovoltaic_panels = ['PV_installed_area_total[m2]', 'PV_electricity_total[kWh]', 'PV_installed_area_roof[m2]', 'PV_electricity_roof[kWh]', 'PV_installed_area_north[m2]', 'PV_electricity_north[kWh]', 'PV_installed_area_south[m2]', 'PV_electricity_south[kWh]', 'PV_installed_area_east[m2]', 'PV_electricity_east[kWh]', 'PV_installed_area_west[m2]', 'PV_electricity_west[kWh]']
list_metrics_photovoltaic_thermal_panels_et = ['PVT_ET_installed_area_total[m2]', 'PVT_ET_electricity_total[kWh]', 'PVT_ET_heat_total[kWh]', 'PVT_ET_installed_area_roof[m2]', 'PVT_ET_electricity_roof[kWh]', 'PVT_ET_heat_roof[kWh]', 'PVT_ET_installed_area_north[m2]', 'PVT_ET_electricity_north[kWh]', 'PVT_ET_heat_north[kWh]', 'PVT_ET_installed_area_south[m2]', 'PVT_ET_electricity_south[kWh]', 'PVT_ET_heat_south[kWh]', 'PVT_ET_installed_area_east[m2]', 'PVT_ET_electricity_east[kWh]', 'PVT_ET_heat_east[kWh]', 'PVT_ET_installed_area_west[m2]', 'PVT_ET_electricity_west[kWh]', 'PVT_ET_heat_west[kWh]']
list_metrics_photovoltaic_thermal_panels_fp = ['PVT_FP_installed_area_total[m2]', 'PVT_FP_electricity_total[kWh]', 'PVT_FP_heat_total[kWh]', 'PVT_FP_installed_area_roof[m2]', 'PVT_FP_electricity_roof[kWh]', 'PVT_FP_heat_roof[kWh]', 'PVT_FP_installed_area_north[m2]', 'PVT_FP_electricity_north[kWh]', 'PVT_FP_heat_north[kWh]', 'PVT_FP_installed_area_south[m2]', 'PVT_FP_electricity_south[kWh]', 'PVT_FP_heat_south[kWh]', 'PVT_FP_installed_area_east[m2]', 'PVT_FP_electricity_east[kWh]', 'PVT_FP_heat_east[kWh]', 'PVT_FP_installed_area_west[m2]', 'PVT_FP_electricity_west[kWh]', 'PVT_FP_heat_west[kWh]']
list_metrics_solar_collectors_et = ['SC_ET_installed_area_total[m2]', 'SC_ET_heat_total[kWh]', 'SC_ET_installed_area_roof[m2]', 'SC_ET_heat_roof[kWh]', 'SC_ET_installed_area_north[m2]', 'SC_ET_heat_north[kWh]', 'SC_ET_installed_area_south[m2]', 'SC_ET_heat_south[kWh]', 'SC_ET_installed_area_east[m2]', 'SC_ET_heat_east[kWh]', 'SC_ET_installed_area_west[m2]', 'SC_ET_heat_west[kWh]']
list_metrics_solar_collectors_fp = ['SC_FP_installed_area_total[m2]','SC_FP_heat_total[kWh]','SC_FP_installed_area_roof[m2]','SC_FP_heat_roof[kWh]','SC_FP_installed_area_north[m2]','SC_FP_heat_north[kWh]','SC_FP_installed_area_south[m2]','SC_FP_heat_south[kWh]','SC_FP_installed_area_east[m2]','SC_FP_heat_east[kWh]','SC_FP_installed_area_west[m2]','SC_FP_heat_west[kWh]']
list_metrics_other_renewables = ['geothermal_heat_potential[kWh]','area_for_ground_source_heat_pump[m2]', 'sewage_heat_potential[kWh]', 'water_body_heat_potential[kWh]']
list_metrics_district_heating = ['DH_plant_thermal_load[kWh]','DH_electricity_consumption_for_pressure_loss[kWh]']
list_metrics_district_cooling = ['DC_plant_thermal_load[kWh]','DC_electricity_consumption_for_pressure_loss[kWh]']

list_metrics_architecture = ['conditioned_floor_area[m2]','roof_area[m2]','gross_floor_area[m2]','occupied_floor_area[m2]']
list_metrics_lifecycle_emissions = [
    'operation_heating[kgCO2e]', 'operation_hot_water[kgCO2e]', 'operation_cooling[kgCO2e]', 'operation_electricity[kgCO2e]',
    'production_wall_ag[kgCO2e]', 'production_wall_bg[kgCO2e]', 'production_wall_part[kgCO2e]',
    'production_win_ag[kgCO2e]', 'production_roof[kgCO2e]', 'production_upperside[kgCO2e]',
    'production_underside[kgCO2e]', 'production_floor[kgCO2e]', 'production_base[kgCO2e]',
    'production_technical_systems[kgCO2e]', 'biogenic_wall_ag[kgCO2e]', 'biogenic_wall_bg[kgCO2e]',
    'biogenic_wall_part[kgCO2e]', 'biogenic_win_ag[kgCO2e]', 'biogenic_roof[kgCO2e]',
    'biogenic_upperside[kgCO2e]', 'biogenic_underside[kgCO2e]', 'biogenic_floor[kgCO2e]',
    'biogenic_base[kgCO2e]', 'biogenic_technical_systems[kgCO2e]', 'demolition_wall_ag[kgCO2e]',
    'demolition_wall_bg[kgCO2e]', 'demolition_wall_part[kgCO2e]', 'demolition_win_ag[kgCO2e]',
    'demolition_roof[kgCO2e]', 'demolition_upperside[kgCO2e]', 'demolition_underside[kgCO2e]',
    'demolition_floor[kgCO2e]', 'demolition_base[kgCO2e]', 'demolition_technical_systems[kgCO2e]'
]
list_metrics_operational_emissions = [
    'heating[kgCO2e]', 'hot_water[kgCO2e]', 'cooling[kgCO2e]', 'electricity[kgCO2e]',
    'heating_NATURALGAS[kgCO2e]', 'heating_BIOGAS[kgCO2e]', 'heating_SOLAR[kgCO2e]',
    'heating_DRYBIOMASS[kgCO2e]', 'heating_WETBIOMASS[kgCO2e]', 'heating_GRID[kgCO2e]',
    'heating_COAL[kgCO2e]', 'heating_WOOD[kgCO2e]', 'heating_OIL[kgCO2e]',
    'heating_HYDROGEN[kgCO2e]', 'heating_NONE[kgCO2e]', 'hot_water_NATURALGAS[kgCO2e]',
    'hot_water_BIOGAS[kgCO2e]', 'hot_water_SOLAR[kgCO2e]', 'hot_water_DRYBIOMASS[kgCO2e]',
    'hot_water_WETBIOMASS[kgCO2e]', 'hot_water_GRID[kgCO2e]', 'hot_water_COAL[kgCO2e]',
    'hot_water_WOOD[kgCO2e]', 'hot_water_OIL[kgCO2e]', 'hot_water_HYDROGEN[kgCO2e]',
    'hot_water_NONE[kgCO2e]', 'cooling_NATURALGAS[kgCO2e]', 'cooling_BIOGAS[kgCO2e]',
    'cooling_SOLAR[kgCO2e]', 'cooling_DRYBIOMASS[kgCO2e]', 'cooling_WETBIOMASS[kgCO2e]',
    'cooling_GRID[kgCO2e]', 'cooling_COAL[kgCO2e]', 'cooling_WOOD[kgCO2e]', 'cooling_OIL[kgCO2e]',
    'cooling_HYDROGEN[kgCO2e]', 'cooling_NONE[kgCO2e]', 'electricity_NATURALGAS[kgCO2e]', 'electricity_BIOGAS[kgCO2e]',
    'electricity_SOLAR[kgCO2e]', 'electricity_DRYBIOMASS[kgCO2e]', 'electricity_WETBIOMASS[kgCO2e]', 'electricity_GRID[kgCO2e]',
    'electricity_COAL[kgCO2e]', 'electricity_WOOD[kgCO2e]', 'electricity_OIL[kgCO2e]', 'electricity_HYDROGEN[kgCO2e]', 'electricity_NONE[kgCO2e]'
]

def get_list_list_metrics_with_date(config):
    list_list_metrics_with_date = []
    if config.result_summary.metrics_building_energy_demand:
        list_list_metrics_with_date.append(list_metrics_building_energy_demand)
    if config.result_summary.metrics_solar_irradiation:
        list_list_metrics_with_date.append(list_metrics_solar_irradiation)
    if config.result_summary.metrics_photovoltaic_panels:
        list_list_metrics_with_date.append(list_metrics_photovoltaic_panels)
    if config.result_summary.metrics_photovoltaic_thermal_panels:
        list_list_metrics_with_date.append(list_metrics_photovoltaic_thermal_panels_et)
        list_list_metrics_with_date.append(list_metrics_photovoltaic_thermal_panels_fp)
    if config.result_summary.metrics_solar_collectors:
        list_list_metrics_with_date.append(list_metrics_solar_collectors_et)
        list_list_metrics_with_date.append(list_metrics_solar_collectors_fp)
    if config.result_summary.metrics_other_renewables:
        list_list_metrics_with_date.append(list_metrics_other_renewables)
    if config.result_summary.metrics_district_heating:
        list_list_metrics_with_date.append(list_metrics_district_heating)
    if config.result_summary.metrics_district_cooling:
        list_list_metrics_with_date.append(list_metrics_district_cooling)
    if config.result_summary.metrics_emissions:
        list_list_metrics_with_date.append(list_metrics_operational_emissions)

    return list_list_metrics_with_date


def get_list_list_metrics_with_date_plot(list_cea_feature_to_plot):
    list_list_metrics_with_date = []
    if 'demand' in list_cea_feature_to_plot:
        list_list_metrics_with_date.append(list_metrics_building_energy_demand)
    if 'solar_irradiation' in list_cea_feature_to_plot:
        list_list_metrics_with_date.append(list_metrics_solar_irradiation)
    if 'pv' in list_cea_feature_to_plot:
        list_list_metrics_with_date.append(list_metrics_photovoltaic_panels)
    if 'pvt' in list_cea_feature_to_plot:
        list_list_metrics_with_date.append(list_metrics_photovoltaic_thermal_panels_et)
        list_list_metrics_with_date.append(list_metrics_photovoltaic_thermal_panels_fp)
    if 'sc' in list_cea_feature_to_plot:
        list_list_metrics_with_date.append(list_metrics_solar_collectors_et)
        list_list_metrics_with_date.append(list_metrics_solar_collectors_fp)
    if 'other_renewables' in list_cea_feature_to_plot:
        list_list_metrics_with_date.append(list_metrics_other_renewables)
    if 'dh' in list_cea_feature_to_plot:
        list_list_metrics_with_date.append(list_metrics_district_heating)
    if 'dc' in list_cea_feature_to_plot:
        list_list_metrics_with_date.append(list_metrics_district_cooling)
    if 'operational_emissions' in list_cea_feature_to_plot:
        list_list_metrics_with_date.append(list_metrics_operational_emissions)
    return list_list_metrics_with_date


def get_list_list_metrics_without_date(config):
    list_list_metrics_without_date = []
    if config.result_summary.metrics_emissions:
        list_list_metrics_without_date.append(list_metrics_lifecycle_emissions)

    return list_list_metrics_without_date


def get_list_list_metrics_without_date_plot(list_cea_feature_to_plot):
    list_list_metrics_without_date = []
    if 'lifecycle_emissions' in list_cea_feature_to_plot:
        list_list_metrics_without_date.append(list_metrics_lifecycle_emissions)

    return list_list_metrics_without_date


def get_list_list_metrics_building(config):
    list_list_metrics_building = []
    if config.result_summary.metrics_building_energy_demand:
        list_list_metrics_building.append(list_metrics_building_energy_demand)
    if config.result_summary.metrics_solar_irradiation:
        list_list_metrics_building.append(list_metrics_solar_irradiation)
    if config.result_summary.metrics_photovoltaic_panels:
        list_list_metrics_building.append(list_metrics_photovoltaic_panels)
    if config.result_summary.metrics_photovoltaic_thermal_panels:
        list_list_metrics_building.append(list_metrics_photovoltaic_thermal_panels_et)
        list_list_metrics_building.append(list_metrics_photovoltaic_thermal_panels_fp)
    if config.result_summary.metrics_solar_collectors:
        list_list_metrics_building.append(list_metrics_solar_collectors_et)
        list_list_metrics_building.append(list_metrics_solar_collectors_fp)
    if config.result_summary.metrics_emissions:
        list_list_metrics_building.append(list_metrics_lifecycle_emissions)
        list_list_metrics_building.append(list_metrics_operational_emissions)

    return list_list_metrics_building


def get_list_list_metrics_building_plot(list_cea_feature_to_plot):
    list_list_metrics_building = []
    if 'demand' in list_cea_feature_to_plot:
        list_list_metrics_building.append(list_metrics_building_energy_demand)
    if 'solar_irradiation' in list_cea_feature_to_plot:
        list_list_metrics_building.append(list_metrics_solar_irradiation)
    if 'pv' in list_cea_feature_to_plot:
        list_list_metrics_building.append(list_metrics_photovoltaic_panels)
    if 'pvt' in list_cea_feature_to_plot:
        list_list_metrics_building.append(list_metrics_photovoltaic_thermal_panels_et)
        list_list_metrics_building.append(list_metrics_photovoltaic_thermal_panels_fp)
    if 'sc' in list_cea_feature_to_plot:
        list_list_metrics_building.append(list_metrics_solar_collectors_et)
        list_list_metrics_building.append(list_metrics_solar_collectors_fp)
    if 'operational_emissions' in list_cea_feature_to_plot:
        list_list_metrics_building.append(list_metrics_operational_emissions)
    if 'lifecycle_emissions' in list_cea_feature_to_plot:
        list_list_metrics_building.append(list_metrics_lifecycle_emissions)

    return list_list_metrics_building

def filter_buildings(locator, list_buildings,
                     integer_year_start, integer_year_end, list_standard,
                     list_main_use_type, ratio_main_use_type):
    df_buildings = get_building_year_standard_main_use_type(locator)
    # Names: only filter if explicitly provided
    if list_buildings:
        df_buildings = filter_by_building_names(df_buildings, list_buildings)
    # Year range: always safe (defaults handled inside)
    df_buildings = filter_by_year_range(df_buildings, integer_year_start, integer_year_end)
    # Construction type: only if provided
    if list_standard:
        df_buildings = filter_by_standard(df_buildings, list_standard)
    # Main use type: only if provided
    if list_main_use_type:
        df_buildings = filter_by_main_use(df_buildings, list_main_use_type)
    # Main use ratio: only if provided (defaults to 0 if None/empty)
    if ratio_main_use_type is not None:
        df_buildings = filter_by_main_use_ratio(df_buildings, ratio_main_use_type)
    list_buildings_out = df_buildings['name'].to_list()
    return df_buildings, list_buildings_out


def replace_hyphens_with_underscores(string_list):
    """
    Replaces all hyphens (-) with underscores (_) in each string of the input list.
    Args:
        string_list (list of str): List of strings to process.
    Returns:
        list of str: List with hyphens replaced by underscores.
    """
    return [s.replace('-', '_') for s in string_list]


def process_building_summary(config, locator,
                             hour_start, hour_end, list_buildings,
                             integer_year_start, integer_year_end, list_standard,
                             list_main_use_type, ratio_main_use_type,
                             bool_use_acronym, bool_aggregate_by_building,
                             bool_include_advanced_analytics, list_selected_time_period,
                             bool_use_conditioned_floor_area_for_normalisation,
                             plot=False, list_cea_feature_to_plot=None):
    """
    Processes and exports building summary results, filtering buildings based on user-defined criteria.

    Args:
        config: Configuration object containing user inputs.
        locator: Locator object to find file paths.
        hour_start (int): Start hour for analysis.
        hour_end (int): End hour for analysis.
        list_buildings (list): List of building names to process.
        integer_year_start (int): Minimum building construction year.
        integer_year_end (int): Maximum building construction year.
        list_standard (list): Building standard filter.
        list_main_use_type (list): Main use type filter.
        ratio_main_use_type (float): Ratio for main use type filtering.
        bool_use_acronym (bool): Whether to use building acronyms.
        bool_aggregate_by_building (bool): Whether to aggregate results by building.
        bool_include_advanced_analytics (bool): Whether to include advanced analytics.
        list_selected_time_period (list): List of time periods for aggregation.
        bool_use_conditioned_floor_area_for_normalisation (bool): Normalize results using conditioned floor area.
        plot (bool): Whether to plot the results.

    Returns:
        None
    """

    # list_cea_feature_to_plot = ['demand', 'solar_irradiation', 'pv', 'pvt', 'sc', 'other_renewables', 'dh', 'dc', 'emissions']

    # Step 1: Get Selected Metrics
    if not plot:
        list_list_metrics_with_date = get_list_list_metrics_with_date(config)
        list_list_metrics_without_date = get_list_list_metrics_without_date(config)
        list_list_metrics_building = get_list_list_metrics_building(config)

    else:
        if list_cea_feature_to_plot is not None:
            list_cea_feature_to_plot = replace_hyphens_with_underscores(list_cea_feature_to_plot)
            list_list_metrics_with_date = get_list_list_metrics_with_date_plot(list_cea_feature_to_plot)
            list_list_metrics_without_date = get_list_list_metrics_without_date_plot(list_cea_feature_to_plot)
            list_list_metrics_building = get_list_list_metrics_building_plot(list_cea_feature_to_plot)
        else:
            raise ValueError("Specify the list of CEA features to plot.")

    # Step 2: Get User-Defined Folder Name & Create Folder if it Doesn't Exist
    if not plot:
        folder_name = config.result_summary.folder_name_to_save_exported_results or "summary"
        summary_folder = locator.get_export_results_summary_folder(f"{folder_name}-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}")
        print(f"Results will be saved to: {summary_folder}")
    else:
        summary_folder = locator.get_export_plots_folder()
    os.makedirs(summary_folder, exist_ok=True)

    # Step 3: Get & Filter Buildings
    df_buildings, list_buildings = filter_buildings(locator, list_buildings,
                             integer_year_start, integer_year_end, list_standard,
                             list_main_use_type, ratio_main_use_type)

    # Step 4: Get Building GFA & Merge with df_buildings
    list_list_useful_cea_results, list_appendix = exec_read_and_slice(hour_start, hour_end, locator, list_metrics_architecture, list_buildings)
    list_list_useful_cea_results_buildings = filter_cea_results_by_buildings(bool_use_acronym, list_list_useful_cea_results, list_buildings)
    df_buildings = pd.merge(df_buildings, list_list_useful_cea_results_buildings[0][0], on='name', how='inner')

    # Step 5: Save Building Summary to Disk
    # Round all numeric columns to 2 decimal places
    numeric_columns = df_buildings.select_dtypes(include=[np.number]).columns
    df_buildings[numeric_columns] = df_buildings[numeric_columns].round(2)
    
    if not plot:
        buildings_path = locator.get_export_results_summary_selected_building_file(summary_folder)
    else:
        buildings_path = locator.get_export_plots_selected_building_file()
    df_buildings.to_csv(buildings_path, index=False, float_format="%.2f")

    # Step 6: Export Results Without Date (Non-8760 Hours, Aggregate by Building)
    for list_metrics in list_list_metrics_without_date:
        list_list_useful_cea_results, list_appendix = exec_read_and_slice(hour_start, hour_end, locator, list_metrics, list_buildings)
        list_list_useful_cea_results_buildings = filter_cea_results_by_buildings(bool_use_acronym, list_list_useful_cea_results, list_buildings)
        results_writer_time_period_building(locator, hour_start, hour_end, summary_folder, list_metrics, list_list_useful_cea_results_buildings, list_appendix, list_time_resolution=None, bool_analytics=False, plot=plot, bool_use_acronym=bool_use_acronym)

    # Step 7: Export Results With Date (8760 Hours, Aggregate by Time Period)
    for list_metrics in list_list_metrics_with_date:
        list_list_useful_cea_results, list_appendix = exec_read_and_slice(hour_start, hour_end, locator, list_metrics, list_buildings)
        list_list_df_aggregate_time_period, list_list_time_period = exec_aggregate_time_period(bool_use_acronym, list_list_useful_cea_results, list_selected_time_period)
        results_writer_time_period(locator, hour_start, hour_end, summary_folder, list_metrics, list_list_df_aggregate_time_period, list_list_time_period, list_appendix, bool_analytics=False, plot=plot)

    # Step 8: Aggregate by Building (if Enabled)
    if bool_aggregate_by_building:
        for list_metrics in list_list_metrics_building:
            list_list_useful_cea_results, list_appendix = exec_read_and_slice(hour_start, hour_end, locator, list_metrics, list_buildings)
            if list_appendix == ['lifecycle_emissions']:
                exec_aggregate_building_lifecycle_emissions(locator, hour_start, hour_end, summary_folder, list_metrics, bool_use_acronym, list_list_useful_cea_results, list_buildings, list_appendix, list_selected_time_period, plot=plot)
            else:
                exec_aggregate_building(locator, hour_start, hour_end, summary_folder, list_metrics, bool_use_acronym, list_list_useful_cea_results, list_buildings, list_appendix, list_selected_time_period, plot=plot)

    # Step 9: Include Advanced Analytics (if Enabled)
    if bool_include_advanced_analytics:
        if plot:
            if list_cea_feature_to_plot is None:
                raise ValueError("Specify the list of CEA features to plot.")

            if any(item in list_cea_feature_to_plot for item in ['demand']):
                calc_ubem_analytics_normalised(locator, hour_start, hour_end, "demand", summary_folder,
                                               list_selected_time_period, bool_aggregate_by_building, bool_use_acronym,
                                               bool_use_conditioned_floor_area_for_normalisation, plot=plot)
            if any(item in list_cea_feature_to_plot for item in ['pv']):
                calc_pv_analytics(locator, hour_start, hour_end, summary_folder, list_buildings,
                                  list_selected_time_period, bool_aggregate_by_building, bool_use_acronym, plot=plot)
            if any(item in list_cea_feature_to_plot for item in ['operational_emissions']):
                calc_ubem_analytics_normalised(locator, hour_start, hour_end, "operational_emissions", summary_folder,
                                               list_selected_time_period, bool_aggregate_by_building, bool_use_acronym,
                                               bool_use_conditioned_floor_area_for_normalisation, plot=plot)
        else:
            if config.result_summary.metrics_building_energy_demand:
                calc_ubem_analytics_normalised(locator, hour_start, hour_end, "demand", summary_folder,
                                               list_selected_time_period, bool_aggregate_by_building, bool_use_acronym,
                                               bool_use_conditioned_floor_area_for_normalisation, plot=plot)

            if config.result_summary.metrics_photovoltaic_panels:
                calc_pv_analytics(locator, hour_start, hour_end, summary_folder, list_buildings, list_selected_time_period,
                                  bool_aggregate_by_building, bool_use_acronym, plot=plot)

            if config.result_summary.metrics_emissions:
                calc_ubem_analytics_normalised(locator, hour_start, hour_end, "operational_emissions", summary_folder,
                                               list_selected_time_period, bool_aggregate_by_building, bool_use_acronym,
                                               bool_use_conditioned_floor_area_for_normalisation, plot=plot)


# ----------------------------------------------------------------------------------------------------------------------
# Activate: Export results to .csv (summary & analytics)


def main(config: cea.config.Configuration):
    """
    Read through and summarise CEA results for all scenarios under a project.

    :param config: the configuration object to use
    :type config: cea.config.Configuration
    :return:
    """

    # Start the timer
    t0 = time.perf_counter()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    # Gather info from config file
    list_buildings = config.plots_building_filter.buildings
    integer_year_start = config.plots_building_filter.filter_buildings_by_year_start
    integer_year_end = config.plots_building_filter.filter_buildings_by_year_end
    list_standard = config.plots_building_filter.filter_buildings_by_construction_type
    list_main_use_type = config.plots_building_filter.filter_buildings_by_use_type
    ratio_main_use_type = config.plots_building_filter.min_ratio_as_main_use
    bool_aggregate_by_building = config.result_summary.aggregate_by_building
    list_selected_time_period = config.result_summary.aggregate_by_time_period
    hour_start, hour_end = get_hours_start_end(config)
    bool_include_advanced_analytics = config.result_summary.include_advanced_analytics
    bool_use_acronym = config.result_summary.use_cea_acronym_format_column_names
    bool_use_conditioned_floor_area_for_normalisation = config.result_summary.use_conditioned_floor_area_for_normalisation

    # Process building summary
    process_building_summary(config, locator, hour_start, hour_end, list_buildings,
                             integer_year_start, integer_year_end, list_standard,
                             list_main_use_type, ratio_main_use_type,
                             bool_use_acronym, bool_aggregate_by_building,
                             bool_include_advanced_analytics, list_selected_time_period,
                             bool_use_conditioned_floor_area_for_normalisation, plot=False)

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire process of exporting and summarising the CEA simulated results is now completed - time elapsed: %d.2 seconds' % time_elapsed)


if __name__ == '__main__':
    main(cea.config.Configuration())


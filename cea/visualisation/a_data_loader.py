"""
InputProcessor - Determines the correct CSV file in the summary folder and triggers the summary feature to generate this file.
Ensure this file exists or break the script.

"""
import os

import geopandas as gpd
import pandas as pd

from cea.import_export.result_summary import (
    get_emission_context,
    process_building_summary,
)
from cea.inputlocator import InputLocator
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def get_building_names_from_zone(locator):
    """
    Get building names from zone geometry.

    Parameters
    ----------
    locator : InputLocator
        File path resolver

    Returns
    -------
    pd.DataFrame
        Zone geometry with 'Name' or 'name' column (caller should check both)
    """

    zone_path = locator.get_zone_geometry()
    crs = get_geographic_coordinate_system()
    zone_df = gpd.read_file(zone_path).to_crs(crs)

    return zone_df


def raise_missing_pv_error(pv_codes, context='file'):
    """
    Raise FileNotFoundError for missing PV results.

    :param pv_codes: Single PV code (str) or list of PV codes (list)
    :param context: 'file' for missing PV files, 'emission' for missing PV data in emission results
    :raises FileNotFoundError: Always raises with formatted error message
    """
    if isinstance(pv_codes, str):
        pv_codes = [pv_codes]

    if context == 'emission':
        # Error when PV columns are missing from emission results
        if len(pv_codes) == 1:
            error_msg = (
                f"PV data missing for panel type: {pv_codes[0]} in emission results. "
                f"Please run the 'emissions' script with include_pv=True and pv_codes=['{pv_codes[0]}'] "
                f"to include PV offsetting in emission calculations."
            )
        else:
            pv_list = ', '.join([f"'{code}'" for code in sorted(pv_codes)])
            error_msg = (
                f"PV data missing for panel type(s): {', '.join(sorted(pv_codes))} in emission results. "
                f"Please run the 'emissions' script with include_pv=True and pv_codes=[{pv_list}] "
                f"to include PV offsetting in emission calculations."
            )
    else:
        # Error when PV result files don't exist
        if len(pv_codes) == 1:
            error_msg = (
                f"PV electricity results missing for panel type: {pv_codes[0]}. "
                f"Please run the 'photovoltaic (PV) panels' script first to generate PV potential results for this panel type."
            )
        else:
            error_msg = (
                f"PV electricity results missing for panel type(s): {', '.join(sorted(pv_codes))}. "
                f"Please run the 'photovoltaic (PV) panels' script first to generate PV potential results for these panel types."
            )

    print(f"ERROR: {error_msg}")
    raise FileNotFoundError(error_msg)


demand_metrics = ['grid_electricity_consumption', 'enduse_electricity_demand', 'enduse_cooling_demand', 'enduse_space_cooling_demand',	'enduse_heating_demand', 'enduse_space_heating_demand',	'enduse_dhw_demand']
demand_analytics = ['EUI_grid_electricity',	'EUI_enduse_electricity', 'EUI_enduse_cooling',	'EUI_enduse_space cooling',	'EUI_enduse_heating', 'EUI_enduse_space_heating', 'EUI_enduse_dhw']

solar_metrics = ['total', 'roofs_top', 'walls_north', 'walls_east', 'walls_south', 'walls_west']
solar_analytics = ['solar_energy_penetration', 'self_consumption', 'self_sufficiency']


def get_plot_metrics_dict(locator):
    """Get dictionary of plot metrics for each CEA feature, with lazy emission context initialisation."""
    emission_context = get_emission_context(locator)
    lifecycle_emission_metrics = emission_context["yearly_colnames"]
    operational_emission_metrics = emission_context["hourly_colnames"]

    return {
        'demand': demand_metrics,
        'pv': solar_metrics,
        'pvt': solar_metrics,
        'sc': solar_metrics,
        'lifecycle-emissions': lifecycle_emission_metrics,
        'operational-emissions': operational_emission_metrics,
        'emission-timeline': lifecycle_emission_metrics,
        'heat-rejection': ['heat_rejection']
    }


def get_plot_analytics_dict(locator):
    """Get dictionary of plot analytics for each CEA feature."""
    # This doesn't need emission context, but kept for consistency
    return {
        'demand': demand_analytics,
        'pv': solar_analytics,
        'pvt': [],
        'sc': [],
        'lifecycle-emissions': [],
        'operational-emissions': [],
        'heat-rejection': []
    }

# Trigger the summary feature and point to the csv results file
class csv_pointer:
    """Maps user input combinations to pre-defined CSV file paths."""

    def __init__(self, plot_config, plots_building_filter, scenario, plot_cea_feature, period_start, period_end, solar_panel_types_list):
        """
        :param plot_config: User-defined configuration settings.
        :param scenario: CEA scenario path.
        :param plot_cea_feature: The feature to plot.
        :param period_start: Start hour for analysis.
        :param period_end: End hour for analysis.
        """

        x, x_facet = get_x_and_x_facet(plot_config.x_to_plot)
        self.config = plot_config
        self.scenario = scenario
        self.locator = InputLocator(scenario=scenario)
        self.plot_cea_feature = plot_cea_feature
        self.period_start = period_start
        self.period_end = period_end
        self.buildings = plots_building_filter.buildings

        # For lifecycle-emissions, emission-timeline, and operational-emissions,
        # y_metric_to_plot is generated in b_data_processor from multiple parameters
        # For other features, read it from config
        if plot_cea_feature in ('lifecycle-emissions', 'emission-timeline', 'operational-emissions'):
            self.y_metric_to_plot = []  # Will be generated later in b_data_processor
        else:
            self.y_metric_to_plot = plot_config.y_metric_to_plot
            # Legacy PV handling for other plots if needed
            if hasattr(plot_config, 'pv_code') and plot_config.pv_code is not None:
                pv_code = plot_config.pv_code
                self.y_metric_to_plot.append(f"PV_{pv_code}_offset_total")

        self.y_normalised_by = plot_config.y_normalised_by
        self.x = x
        self.x_to_plot = plot_config.x_to_plot
        self.x_facet = x_facet
        self.integer_year_start = plots_building_filter.filter_buildings_by_year_start
        self.integer_year_end = plots_building_filter.filter_buildings_by_year_end
        self.list_construction_type = plots_building_filter.filter_buildings_by_construction_type
        self.list_use_type = plots_building_filter.filter_buildings_by_use_type
        self.min_ratio_as_main_use = plots_building_filter.min_ratio_as_main_use
        self.plot = True

        if plot_cea_feature in ('pv', 'sc'):
            self.appendix = f"{plot_cea_feature}_{solar_panel_types_list[0]}"
        elif plot_cea_feature == 'pvt':
            if len(solar_panel_types_list) == 2:
                self.appendix = f"{plot_cea_feature}_{solar_panel_types_list[0]}_{solar_panel_types_list[1]}"
            else:
                raise ValueError("PVT requires two solar panel types.")
        else:
            self.appendix = plot_cea_feature

        self.bool_aggregate_by_building = self.x == "by_building"

        time_period_map = {
            "building": "annually",
            "building_faceted_by_decades": "annually",
            "building_faceted_by_months": "monthly",
            "building_faceted_by_seasons": "seasonally",
            "building_faceted_by_construction_type": "annually",
            "building_faceted_by_main_use_type": "annually",
            "district_and_hourly": 'hourly',
            "district_and_hourly_faceted_by_months": 'hourly',
            "district_and_hourly_faceted_by_seasons": 'hourly',
            "district_and_daily": "daily",
            "district_and_daily_faceted_by_months": "daily",
            "district_and_daily_faceted_by_seasons": "daily",
            "district_and_monthly": "monthly",
            "district_and_monthly_faceted_by_seasons": "monthly",
            "district_and_seasonally": "seasonally",
            "district_and_annually_or_selected_period": "annually",
            "district_and_annually_faceted_by_decades": "annually",
            "district_and_annually": "timeline",

        }
        self.time_period = time_period_map.get(self.x_to_plot)

    def execute_summary(self, bool_include_advanced_analytics):
        """Executes the summary feature to generate the required CSV output."""
        list_metrics_analytics = get_plot_analytics_dict(self.locator).get(self.plot_cea_feature, [])
        if any(item in list_metrics_analytics for item in self.y_metric_to_plot):
            bool_include_advanced_analytics = True

        bool_use_acronym = True

        bool_use_conditioned_floor_area_for_normalisation = self.y_normalised_by == "conditioned_floor_area"
        # bool_use_solar_technology_area_installed_for_respective_surface = self.y_normalised_by == "solar_technology_area_installed_for_respective_surface"

        process_building_summary(
            self.config, self.locator,
            self.period_start, self.period_end, self.buildings,
            self.integer_year_start, self.integer_year_end, self.list_construction_type,
            self.list_use_type, self.min_ratio_as_main_use,
            bool_use_acronym, self.bool_aggregate_by_building,
            bool_include_advanced_analytics, [self.time_period],
            bool_use_conditioned_floor_area_for_normalisation,
            plot=True, list_cea_feature_to_plot=[self.plot_cea_feature]
        )

    def get_summary_results_csv_path(self):
        """Returns the correct path for the summary results CSV file based on user inputs."""
        summary_folder = self.locator.get_export_plots_folder()
        list_metrics_non_analytics = get_plot_metrics_dict(self.locator).get(self.plot_cea_feature, [])
        list_metrics_analytics = get_plot_analytics_dict(self.locator).get(self.plot_cea_feature, [])

        if all(item in list_metrics_non_analytics for item in self.y_metric_to_plot):
            return self._get_non_analytics_summary_path(summary_folder)
        elif all(item in list_metrics_analytics for item in self.y_metric_to_plot):
            return self._get_analytics_summary_path(summary_folder)
        else:
            raise ValueError(f"Invalid y-metric-to-plot: {self.y_metric_to_plot}. Current combination is not supported.")

    def _get_non_analytics_summary_path(self, summary_folder):
        """Helper function to retrieve the non-analytics summary CSV path."""
        cea_feature = self.plot_cea_feature if not self.plot else self.plot_cea_feature.replace('_', '-')
        appendix = self.appendix if not self.plot else self.appendix.replace('_', '-')

        if self.bool_aggregate_by_building:
            return self.locator.get_export_plots_cea_feature_time_resolution_buildings_file(
                cea_feature, appendix, self.time_period, self.period_start, self.period_end
            )
        else:
            return self.locator.get_export_results_summary_cea_feature_time_period_file(
                summary_folder, cea_feature, appendix, self.time_period, self.period_start, self.period_end
            )

    def _get_analytics_summary_path(self, summary_folder):
        """Helper function to retrieve the analytics summary CSV path."""
        if self.bool_aggregate_by_building:
            return self.locator.get_export_plots_cea_feature_analytics_time_resolution_buildings_file(
                self.plot_cea_feature, self.appendix, self.time_period, self.period_start, self.period_end
            )
        else:
            return self.locator.get_export_results_summary_cea_feature_analytics_time_resolution_file(
                summary_folder, self.plot_cea_feature, self.appendix, self.time_period, self.period_start, self.period_end
            )


# from X-to-plot to X and X_facet
def get_x_and_x_facet(x_to_plot):
    if x_to_plot == "building":
        x = 'by_building'
        x_facet = None
    elif x_to_plot == "building_faceted_by_months":
        x = 'by_building'
        x_facet = 'months'
    elif x_to_plot == "building_faceted_by_seasons":
        x = 'by_building'
        x_facet = 'seasons'
    elif x_to_plot == "building_faceted_by_decades":
        x = 'by_building'
        x_facet = 'decades'
    elif x_to_plot == "building_faceted_by_construction_type":
        x = 'by_building'
        x_facet = 'construction_type'
    elif x_to_plot == "building_faceted_by_main_use_type":
        x = 'by_building'
        x_facet = 'main_use_type'
    elif x_to_plot == "district_and_hourly":
        x = 'by_period'
        x_facet = None
    elif x_to_plot == "district_and_hourly_faceted_by_months":
        x = 'by_period'
        x_facet = 'months'
    elif x_to_plot == "district_and_hourly_faceted_by_seasons":
        x = 'by_period'
        x_facet = 'seasons'
    elif x_to_plot == "district_and_annually_faceted_by_decades":
        x = 'by_period'
        x_facet = 'decades'
    elif x_to_plot == "district_and_daily":
        x = 'by_period'
        x_facet = None
    elif x_to_plot == "district_and_daily_faceted_by_months":
        x = 'by_period'
        x_facet = 'months'
    elif x_to_plot == "district_and_daily_faceted_by_seasons":
        x = 'by_period'
        x_facet = 'seasons'
    elif x_to_plot == "district_and_monthly":
        x = 'by_period'
        x_facet = None
    elif x_to_plot == "district_and_monthly_faceted_by_seasons":
        x = 'by_period'
        x_facet = 'seasons'
    elif x_to_plot == "district_and_seasonally":
        x = 'by_period'
        x_facet = None
    elif x_to_plot == "district_and_annually_or_selected_period":
        x = 'by_period'
        x_facet = None
    elif x_to_plot == "district_and_annually":
        x = 'by_period'
        x_facet = None
    else:
        raise ValueError(f"Invalid x-to-plot: {x_to_plot}")

    return x, x_facet


# Main function
def plot_input_processor(plot_config, plots_building_filter, scenario, plot_cea_feature, period_start, period_end, solar_panel_types_list, bool_include_advanced_analytics=False):
    """
    Processes and exports building summary results, filtering buildings based on user-defined criteria.

    Args:
        config: Configuration object containing user inputs.
        scenario: Path to the scenario folder.
        plot_cea_feature: The plot_cea_feature to process.
        period_start (int): Start hour for analysis.
        hour_end (int): End hour for analysis.

    Returns:
        None
    """
    # Early validation: Check if PV panel results exist for emission plots
    if plot_cea_feature in ('operational-emissions', 'lifecycle-emissions'):
        pv_code = getattr(plot_config, 'pv_code', None)
        if pv_code:
            # Check if any building has PV data for this panel type
            locator = InputLocator(scenario)

            # Get list of buildings to check
            buildings = plots_building_filter.buildings
            if not buildings:
                zone_df = get_building_names_from_zone(locator)
                buildings = zone_df['name'].tolist()

            # Check if PV results exist for at least one building (representative check)
            if buildings:
                first_building = buildings[0]
                pv_path = locator.PV_results(first_building, pv_code)
                if not os.path.exists(pv_path):
                    raise_missing_pv_error(pv_code)

    # Instantiate the csv_pointer class
    plot_instance_a = csv_pointer(plot_config, plots_building_filter, scenario, plot_cea_feature, period_start, period_end, solar_panel_types_list)

    # Get the summary results CSV path
    summary_results_csv_path = plot_instance_a.get_summary_results_csv_path()

    # Delete the existing file if it exists to prevent loading stale cached data
    if os.path.exists(summary_results_csv_path):
        os.remove(summary_results_csv_path)

    # Execute the summary process
    plot_instance_a.execute_summary(bool_include_advanced_analytics)

    # Load the summary results data
    try:
        df_summary_data = pd.read_csv(summary_results_csv_path)

        # Validate data structure based on time period
        # Hourly/daily data should have 'date' column
        # Monthly/seasonal/annual/timeline data should have 'period' column
        if plot_instance_a.time_period in ('hourly', 'daily'):
            # For hourly/daily operational emissions, expect 'date' column
            if 'period' in df_summary_data.columns and 'date' not in df_summary_data.columns:
                error_msg = (
                    f"Data structure error in summary file: {summary_results_csv_path}\n"
                    f"Expected {plot_instance_a.time_period} data with 'date' column, but found 'period' column.\n"
                    f"This suggests aggregated period data was incorrectly written to the {plot_instance_a.time_period} summary file.\n"
                    f"Available columns: {df_summary_data.columns.tolist()}\n"
                    "File will be deleted and regenerated."
                )
                print(error_msg)
                # Delete the incorrect file
                os.remove(summary_results_csv_path)
                raise ValueError(error_msg)
        elif plot_instance_a.time_period in ('monthly', 'seasonally', 'annually', 'timeline'):
            # For monthly/seasonal/annual/timeline data, expect 'period' column
            if 'date' in df_summary_data.columns and 'period' not in df_summary_data.columns:
                error_msg = (
                    f"Data structure error in summary file: {summary_results_csv_path}\n"
                    f"Expected {plot_instance_a.time_period} data with 'period' column, but found 'date' column.\n"
                    f"This suggests hourly/daily data was incorrectly written to the {plot_instance_a.time_period} summary file.\n"
                    f"Available columns: {df_summary_data.columns.tolist()}\n"
                    "File will be deleted and regenerated."
                )
                print(error_msg)
                # Delete the incorrect file
                os.remove(summary_results_csv_path)
                raise ValueError(error_msg)

    except Exception as e:
        print(f"Error loading csv file: {e}")
        df_summary_data = None

    # Load the architecture data
    try:
        df_architecture_data = pd.read_csv(plot_instance_a.locator.get_export_plots_selected_building_file())
    except Exception as e:
        print(f"Error loading csv file: {e}")
        df_architecture_data = None

    return df_summary_data, df_architecture_data, plot_instance_a




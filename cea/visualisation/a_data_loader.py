"""
InputProcessor – Determines the correct CSV file in the summary folder and triggers the summary feature to generate this file.
Ensure this file exists or break the script.

"""

import cea.inputlocator
import os
import cea.config
from cea.import_export.result_summary import process_building_summary
import pandas as pd



__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

demand_metrics = ['grid_electricity_consumption', 'enduse_electricity_demand', 'enduse_cooling_demand', 'enduse_space_cooling_demand',	'enduse_heating_demand', 'enduse_space_heating_demand',	'enduse_dhw_demand']
demand_analytics = ['EUI_grid_electricity',	'EUI_enduse_electricity', 'EUI_enduse_cooling',	'EUI_enduse_space cooling',	'EUI_enduse_heating', 'EUI_enduse_space_heating', 'EUI_enduse_dhw']

dict_plot_metrics_cea_feature = {
    'demand':demand_metrics,
}

dict_plot_analytics_cea_feature = {
    'demand':demand_analytics,
}

# Trigger the summary feature and point to the csv results file
class csv_pointer:
    """Maps user input combinations to pre-defined CSV file paths."""

    def __init__(self, config_config, scenario, plot_cea_feature, hour_start, hour_end):
        """
        :param config_config: User-defined configuration settings.
        :param scenario: CEA scenario path.
        :param plot_cea_feature: The feature to plot.
        :param hour_start: Start hour for analysis.
        :param hour_end: End hour for analysis.
        """

        x, x_facet = get_x_and_x_facet(config_config.x_to_plot)
        self.config = config_config
        self.scenario = scenario
        self.locator = cea.inputlocator.InputLocator(scenario=scenario)
        self.plot_cea_feature = plot_cea_feature
        self.hour_start = hour_start
        self.hour_end = hour_end
        self.buildings = config_config.buildings
        self.y_metric_to_plot = config_config.y_metric_to_plot
        self.y_normalised_by = config_config.y_normalised_by
        self.x_to_plot = config_config.x_to_plot
        self.x = x
        self.x_facet = x_facet
        self.integer_year_start = config_config.filter_buildings_by_year_start
        self.integer_year_end = config_config.filter_buildings_by_year_end
        self.list_construction_type = config_config.filter_buildings_by_construction_type
        self.list_use_type = config_config.filter_buildings_by_use_type
        self.min_ratio_as_main_use = config_config.min_ratio_as_main_use
        self.appendix = plot_cea_feature if plot_cea_feature == "demand" else "default"

        self.bool_aggregate_by_building = self.x == "by_building"

        time_period_map = {
            "building": "annually",
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
            "district_and_annually_or_selected_period": "annually"
        }
        self.time_period = time_period_map.get(self.x_to_plot)

    def execute_summary(self):
        """Executes the summary feature to generate the required CSV output."""
        list_metrics_non_analytics = dict_plot_metrics_cea_feature.get(self.appendix, [])
        list_metrics_analytics = dict_plot_analytics_cea_feature.get(self.appendix, [])
        if all(item in list_metrics_non_analytics for item in self.y_metric_to_plot):
            bool_include_advanced_analytics = False
        elif all(item in list_metrics_analytics for item in self.y_metric_to_plot):
            bool_include_advanced_analytics = True
        else:
            raise ValueError(f"Invalid y-metric-to-plot: {self.y_metric_to_plot}. Current combination is not supported.")
        bool_use_acronym = True

        bool_use_conditioned_floor_area_for_normalisation = self.y_normalised_by == "conditioned_floor_area"

        process_building_summary(
            self.config, self.locator,
            self.hour_start, self.hour_end, self.buildings,
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
        list_metrics_non_analytics = dict_plot_metrics_cea_feature.get(self.appendix, [])
        list_metrics_analytics = dict_plot_analytics_cea_feature.get(self.appendix, [])

        if all(item in list_metrics_non_analytics for item in self.y_metric_to_plot):
            return self._get_non_analytics_summary_path(summary_folder)
        elif all(item in list_metrics_analytics for item in self.y_metric_to_plot):
            return self._get_analytics_summary_path(summary_folder)
        else:
            raise ValueError(f"Invalid y-metric-to-plot: {self.y_metric_to_plot}. Current combination is not supported.")

    def _get_non_analytics_summary_path(self, summary_folder):
        """Helper function to retrieve the non-analytics summary CSV path."""
        if self.bool_aggregate_by_building:
            return self.locator.get_export_plots_cea_feature_time_resolution_buildings_file(
                self.plot_cea_feature, self.appendix, self.time_period, self.hour_start, self.hour_end
            )
        else:
            return self.locator.get_export_results_summary_cea_feature_time_period_file(
                summary_folder, self.plot_cea_feature, self.appendix, self.time_period, self.hour_start, self.hour_end
            )

    def _get_analytics_summary_path(self, summary_folder):
        """Helper function to retrieve the analytics summary CSV path."""
        if self.bool_aggregate_by_building:
            return self.locator.get_export_plots_cea_feature_analytics_time_resolution_buildings_file(
                self.plot_cea_feature, self.appendix, self.time_period, self.hour_start, self.hour_end
            )
        else:
            return self.locator.get_export_results_summary_cea_feature_analytics_time_resolution_file(
                summary_folder, self.plot_cea_feature, self.appendix, self.time_period, self.hour_start, self.hour_end
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
    else:
        raise ValueError(f"Invalid x-to-plot: {x_to_plot}")

    return x, x_facet


# Main function
def plot_input_processor(config_config, scenario, plot_cea_feature, hour_start, hour_end):
    """
    Processes and exports building summary results, filtering buildings based on user-defined criteria.

    Args:
        config: Configuration object containing user inputs.
        scenario: Path to the scenario folder.
        plot_cea_feature: The plot_cea_feature to process.
        hour_start (int): Start hour for analysis.
        hour_end (int): End hour for analysis.

    Returns:
        None
    """
    # Instantiate the csv_pointer class
    plot_instance_a = csv_pointer(config_config, scenario, plot_cea_feature, hour_start, hour_end)

    # Get the summary results CSV path
    summary_results_csv_path = plot_instance_a.get_summary_results_csv_path()

    # Delete the existing file if it exists
    if os.path.exists(summary_results_csv_path):
        os.remove(summary_results_csv_path)

    # Execute the summary process
    plot_instance_a.execute_summary()

    # Load the summary results data
    try:
        df_summary_data = pd.read_csv(summary_results_csv_path)
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




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
        self.config = config_config
        self.scenario = scenario
        self.locator = cea.inputlocator.InputLocator(scenario=scenario)
        self.plot_cea_feature = plot_cea_feature
        self.hour_start = hour_start
        self.hour_end = hour_end
        self.buildings = config_config.buildings
        self.y_metric_to_plot = config_config.Y_metric_to_plot
        self.normalised_by = config_config.normalised_by
        self.x_to_plot = config_config.X_to_plot
        self.x_faceted = config_config.X_faceted
        self.integer_year_start = config_config.filter_buildings_by_year_start
        self.integer_year_end = config_config.filter_buildings_by_year_end
        self.list_construction_type = config_config.filter_buildings_by_construction_type
        self.list_use_type = config_config.filter_buildings_by_use_type
        self.min_ratio_as_main_use = config_config.min_ratio_as_main_use
        self.appendix = plot_cea_feature if plot_cea_feature == "demand" else "default"

        self.bool_aggregate_by_building = self.x_to_plot == "by_building"

        time_period_map = {
            "by_months": ["monthly"],
            "by_seasons": ["seasonally"],
            "by_district_and_time_period_hourly": ["hourly"],
            "by_district_and_time_period_daily": ["daily"],
            "by_district_and_time_period_monthly": ["monthly"],
            "by_district_and_time_period_seasonally": ["seasonally"],
            "by_district_and_time_period_annually_or_selected": ["annually"]
        }
        self.time_period = time_period_map.get(self.x_faceted if self.bool_aggregate_by_building else self.x_to_plot, [])

    def execute_summary(self):
        """Executes the summary feature to generate the required CSV output."""
        bool_use_acronym = True
        bool_include_advanced_analytics = True
        bool_use_conditioned_floor_area_for_normalisation = self.normalised_by == "conditioned_floor_area"

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
        list_metrics_non_analytics = ['end_use', 'final_use']
        list_metrics_analytics = ['energy_use_intensity']

        if self.y_metric_to_plot in list_metrics_non_analytics:
            return self._get_non_analytics_summary_path(summary_folder)
        elif self.y_metric_to_plot in list_metrics_analytics:
            return self._get_analytics_summary_path(summary_folder)
        else:
            raise ValueError(f"Invalid y-metric-to-plot: {self.y_metric_to_plot}")

    def _get_non_analytics_summary_path(self, summary_folder):
        """Helper function to retrieve the non-analytics summary CSV path."""
        if self.bool_aggregate_by_building:
            return self.locator.get_export_plots_cea_feature_time_resolution_buildings_file(
                self.plot_cea_feature, self.appendix, self.time_period, self.hour_start, self.hour_end
            )
        else:
            return self.locator.get_export_results_summary_cea_feature_time_resolution_file(
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


# Main function
def plot_input_processor(config, scenario, plot_cea_feature, hour_start, hour_end):
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
    plot_instance = csv_pointer(config, scenario, plot_cea_feature, hour_start, hour_end)

    # Get the summary results CSV path
    summary_results_csv_path = plot_instance.get_summary_results_csv_path()

    # Delete the existing file if it exists
    if os.path.exists(summary_results_csv_path):
        os.remove(summary_results_csv_path)

    # Execute the summary process
    plot_instance.execute_summary()

    # Load the summary results data
    try:
        df_summary_data = pd.read_csv(summary_results_csv_path)
    except Exception as e:
        print(f"Error loading csv file: {e}")
        df_summary_data = None

    # Load the architecture data
    try:
        df_architecture_data = pd.read_csv(plot_instance.locator.get_export_plots_selected_building_file())
    except Exception as e:
        print(f"Error loading csv file: {e}")
        df_architecture_data = None

    return df_summary_data, df_architecture_data




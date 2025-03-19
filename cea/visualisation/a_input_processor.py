"""
InputProcessor – Determines the correct CSV file in the summary folder and triggers the summary feature to generate this file.
Ensure this file exists or break the script.

"""

import cea.inputlocator
import os
import cea.config
import time
import geopandas as gpd


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.import_export.result_summary import process_building_summary

DICT_EXAMPLE = {'plot_type': 'bar',
                'cea_feature': 'demand',
                'buildings': ['B0001', 'B0002', 'B0003'],
                'y-metric-to-plot': 'end_use',
                'y-metric-unit': 'MWh',
                'y-normalised-by': 'gross_floor_area',
                'y-min': '',
                'y-max': '',
                'y-step': '',
                'y-label': '',
                'x-to-plot': 'by_building',
                'x-faceted': 'no_facet',
                'x-label': '',
                'transposed': False,
                'filter-buildings-by-year-start': 1900,
                'filter-buildings-by-year-end': 2050,
                'filter-buildings-by-construction-type': [],
                'filter-buildings-by-use-type': [],
                'min-ratio-as-main-use': 0,
}


class csv_pointer:
    """Maps user input combinations to pre-defined CSV file paths."""

    def __init__(self, config_config, scenario, plot_cea_feature, hour_start, hour_end):
        """
        :param user_input: Dictionary containing user selections.

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

        if plot_cea_feature == "demand":
            self.appendix = plot_cea_feature

        if self.x_to_plot == "by_building":
            bool_aggregate_by_building = True
            if self.x_faceted == "by_months":
                time_period = ["monthly"]
            elif self.x_faceted == "by_seasons":
                time_period = ["seasonally"]
            else:
                time_period = []
        else:
            bool_aggregate_by_building = False
            if self.x_to_plot == "by_district_and_time_period_hourly":
                time_period = ['hourly']
            elif self.x_to_plot == "by_district_and_time_period_daily":
                time_period = ['daily']
            elif self.x_to_plot == "by_district_and_time_period_monthly":
                time_period = ['monthly']
            elif self.x_to_plot == "by_district_and_time_period_seasonally":
                time_period = ['seasonally']
            elif self.x_to_plot == "by_district_and_time_period_annually_or_selected":
                time_period = ['annually']
            else:
                time_period = []
        self.bool_aggregate_by_building = bool_aggregate_by_building
        self.time_period = time_period

    def execute_summary(self):
        # Prepare the arguments for the summary feature
        config = self.config
        locator = self.locator
        hour_start = self.hour_start
        hour_end = self.hour_end
        list_buildings = self.buildings
        integer_year_start = self.integer_year_start
        integer_year_end = self.integer_year_end
        list_standard = self.list_construction_type
        list_main_use_type = self.list_use_type
        ratio_main_use_type = self.min_ratio_as_main_use
        bool_use_acronym = True
        bool_aggregate_by_building = self.bool_aggregate_by_building
        list_selected_time_period = [self.time_period]

        bool_include_advanced_analytics = True
        normalised_by = self.normalised_by
        if normalised_by == "conditioned_floor_area":
            bool_use_conditioned_floor_area_for_normalisation = True
        else:
            bool_use_conditioned_floor_area_for_normalisation = False
        list_cea_feature_to_plot = [self.plot_cea_feature]

        # Execute the summary feature
        process_building_summary(config, locator,
                             hour_start, hour_end, list_buildings,
                             integer_year_start, integer_year_end, list_standard,
                             list_main_use_type, ratio_main_use_type,
                             bool_use_acronym, bool_aggregate_by_building,
                             bool_include_advanced_analytics, list_selected_time_period,
                             bool_use_conditioned_floor_area_for_normalisation,
                             plot=True, list_cea_feature_to_plot=list_cea_feature_to_plot)

    def get_summary_results_csv_path(self):
        locator = self.locator
        plot_cea_feature = self.plot_cea_feature
        appendix = self.appendix
        bool_aggregate_by_building = self.bool_aggregate_by_building
        time_period = self.time_period
        hour_start = self.hour_start
        hour_end = self.hour_end
        y_metric_to_plot = self.y_metric_to_plot
        summary_folder = locator.get_export_plots_folder()

        list_metrics_non_analytics = ['end_use', 'final_use']
        list_metrics_analytics = ['energy_use_intensity']

        # X-axis: by_building
        if bool_aggregate_by_building:
            if y_metric_to_plot in list_metrics_non_analytics:
                summary_results_csv_path = locator.get_export_plots_cea_feature_time_resolution_buildings_file(plot_cea_feature, appendix, time_period, hour_start, hour_end)
            elif y_metric_to_plot in list_metrics_analytics:
                summary_results_csv_path = locator.get_export_plots_cea_feature_analytics_time_resolution_buildings_file(plot_cea_feature, appendix, time_period, hour_start,hour_end)
            else:
                raise ValueError(f"Invalid y-metric-to-plot: {y_metric_to_plot}")

        # X-axis: by_district
        else:
            if y_metric_to_plot in list_metrics_non_analytics:
                summary_results_csv_path = locator.get_export_results_summary_cea_feature_time_resolution_file(summary_folder, plot_cea_feature, appendix, time_period, hour_start, hour_end)
            elif y_metric_to_plot in list_metrics_analytics:
                summary_results_csv_path = locator.get_export_results_summary_cea_feature_analytics_time_resolution_file(summary_folder, plot_cea_feature, appendix, time_period, hour_start, hour_end)
            else:
                raise ValueError(f"Invalid y-metric-to-plot: {y_metric_to_plot}")

        return summary_results_csv_path

    def get_selected_building_csv_path(self):
        locator = self.locator
        selected_building_csv_path = locator.get_export_plots_selected_building_file()
        return selected_building_csv_path


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
        print(f"Deleted existing summary file: {summary_results_csv_path}")

    # Execute the summary process
    plot_instance.execute_summary()
    print(f"Summary execution completed. Results saved at: {summary_results_csv_path}")


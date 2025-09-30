"""
InputProcessor – Determines the correct CSV file in the summary folder and triggers the summary feature to generate this file.
Ensure this file exists or break the script.

"""

import cea.inputlocator
import os

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

solar_metrics = ['total', 'roofs_top', 'walls_north', 'walls_east', 'walls_south', 'walls_west']
solar_analytics = ['solar_energy_penetration', 'self_consumption', 'self_sufficiency']

lifecycle_emission_metrics = [
    'heating',
    'hot_water',
    'cooling',
    'electricity',
    'production_wall_ag',
    'production_wall_bg',
    'production_wall_part',
    'production_win_ag',
    'production_roof',
    'production_upperside',
    'production_underside',
    'production_floor',
    'production_base',
    'production_technical_systems',
    'biogenic_wall_ag',
    'biogenic_wall_bg',
    'biogenic_wall_part',
    'biogenic_win_ag',
    'biogenic_roof',
    'biogenic_upperside',
    'biogenic_underside',
    'biogenic_floor',
    'biogenic_base',
    'biogenic_technical_systems',
    'demolition_wall_ag',
    'demolition_wall_bg',
    'demolition_wall_part',
    'demolition_win_ag',
    'demolition_roof',
    'demolition_upperside',
    'demolition_underside',
    'demolition_floor',
    'demolition_base',
    'demolition_technical_systems'
]


operational_emission_metrics = [
    'heating', 'hot_water', 'cooling', 'electricity',
    'Qhs_sys_NATURALGAS', 'Qhs_sys_BIOGAS', 'Qhs_sys_SOLAR',
    'Qhs_sys_DRYBIOMASS', 'Qhs_sys_WETBIOMASS', 'Qhs_sys_GRID',
    'Qhs_sys_COAL', 'Qhs_sys_WOOD', 'Qhs_sys_OIL',
    'Qhs_sys_HYDROGEN', 'Qhs_sys_NONE',
    'Qww_sys_NATURALGAS', 'Qww_sys_BIOGAS', 'Qww_sys_SOLAR',
    'Qww_sys_DRYBIOMASS', 'Qww_sys_WETBIOMASS', 'Qww_sys_GRID',
    'Qww_sys_COAL', 'Qww_sys_WOOD', 'Qww_sys_OIL',
    'Qww_sys_HYDROGEN', 'Qww_sys_NONE',
    'Qcs_sys_NATURALGAS', 'Qcs_sys_BIOGAS', 'Qcs_sys_SOLAR',
    'Qcs_sys_DRYBIOMASS', 'Qcs_sys_WETBIOMASS', 'Qcs_sys_GRID',
    'Qcs_sys_COAL', 'Qcs_sys_WOOD', 'Qcs_sys_OIL',
    'Qcs_sys_HYDROGEN', 'Qcs_sys_NONE',
    'E_sys_NATURALGAS', 'E_sys_BIOGAS', 'E_sys_SOLAR',
    'E_sys_DRYBIOMASS', 'E_sys_WETBIOMASS', 'E_sys_GRID',
    'E_sys_COAL', 'E_sys_WOOD', 'E_sys_OIL',
    'E_sys_HYDROGEN', 'E_sys_NONE'
]



dict_plot_metrics_cea_feature = {
    'demand': demand_metrics,
    'pv': solar_metrics,
    'pvt': solar_metrics,
    'sc': solar_metrics,
    'lifecycle-emissions': lifecycle_emission_metrics,
    'operational-emissions': operational_emission_metrics
}

dict_plot_analytics_cea_feature = {
    'demand': demand_analytics,
    'pv': solar_analytics,
    'pvt': [],
    'sc': [],
    'lifecycle-emissions': [],
    'operational-emissions': []
}

# Trigger the summary feature and point to the csv results file
class csv_pointer:
    """Maps user input combinations to pre-defined CSV file paths."""

    def __init__(self, plot_config, plot_config_general, plots_building_filter, scenario, plot_cea_feature, hour_start, hour_end, solar_panel_types_list):
        """
        :param plot_config: User-defined configuration settings.
        :param scenario: CEA scenario path.
        :param plot_cea_feature: The feature to plot.
        :param hour_start: Start hour for analysis.
        :param hour_end: End hour for analysis.
        """

        x, x_facet = get_x_and_x_facet(plot_config_general.x_to_plot)
        self.config = plot_config
        self.scenario = scenario
        self.locator = cea.inputlocator.InputLocator(scenario=scenario)
        self.plot_cea_feature = plot_cea_feature
        self.hour_start = hour_start
        self.hour_end = hour_end
        self.buildings = plot_config_general.buildings
        self.y_metric_to_plot = plot_config.y_metric_to_plot
        self.y_normalised_by = plot_config.y_normalised_by
        self.x_to_plot = plot_config_general.x_to_plot
        self.x = x
        self.x_facet = x_facet
        self.integer_year_start = plots_building_filter.filter_buildings_by_year_start
        self.integer_year_end = plots_building_filter.filter_buildings_by_year_end
        self.list_construction_type = plots_building_filter.filter_buildings_by_construction_type
        self.list_use_type = plots_building_filter.filter_buildings_by_use_type
        self.min_ratio_as_main_use = plots_building_filter.min_ratio_as_main_use

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

    def execute_summary(self, bool_include_advanced_analytics):
        """Executes the summary feature to generate the required CSV output."""
        list_metrics_analytics = dict_plot_analytics_cea_feature.get(self.plot_cea_feature, [])
        if any(item in list_metrics_analytics for item in self.y_metric_to_plot):
            bool_include_advanced_analytics = True

        bool_use_acronym = True

        bool_use_conditioned_floor_area_for_normalisation = self.y_normalised_by == "conditioned_floor_area"
        # bool_use_solar_technology_area_installed_for_respective_surface = self.y_normalised_by == "solar_technology_area_installed_for_respective_surface"

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
        list_metrics_non_analytics = dict_plot_metrics_cea_feature.get(self.plot_cea_feature, [])
        list_metrics_analytics = dict_plot_analytics_cea_feature.get(self.plot_cea_feature, [])

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
def plot_input_processor(plot_config, plot_config_general, plots_building_filter, scenario, plot_cea_feature, hour_start, hour_end, solar_panel_types_list, bool_include_advanced_analytics=False):
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
    plot_instance_a = csv_pointer(plot_config, plot_config_general, plots_building_filter, scenario, plot_cea_feature, hour_start, hour_end, solar_panel_types_list)

    # Get the summary results CSV path
    summary_results_csv_path = plot_instance_a.get_summary_results_csv_path()

    # Delete the existing file if it exists
    if os.path.exists(summary_results_csv_path):
        os.remove(summary_results_csv_path)

    # Execute the summary process
    plot_instance_a.execute_summary(bool_include_advanced_analytics)

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




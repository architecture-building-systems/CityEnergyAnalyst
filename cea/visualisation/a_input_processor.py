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

    def __init__(self, locator, config_config, scenario, cea_feature, hour_start, hour_end):
        """
        :param user_input: Dictionary containing user selections.

        """
        self.config = config_config
        self.scenario = scenario
        self.locator = cea.inputlocator.InputLocator(scenario=scenario)
        self.cea_feature = cea_feature
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
        x_to_plot = self.x_to_plot
        x_faceted = self.x_faceted
        if x_to_plot == "by_building":
            bool_aggregate_by_building = True
            if x_faceted == "by_months":
                list_selected_time_period = ["monthly"]
            elif x_faceted == "by_seasons":
                list_selected_time_period = ["seasonally"]
            else:
                list_selected_time_period = []
        else:
            bool_aggregate_by_building = False
            list_selected_time_period = []
        bool_include_advanced_analytics = True
        normalised_by = self.normalised_by
        if normalised_by == "conditioned_floor_area":
            bool_use_conditioned_floor_area_for_normalisation = True
        else:
            bool_use_conditioned_floor_area_for_normalisation = False
        list_cea_feature_to_plot = [self.cea_feature]

        # Execute the summary feature
        process_building_summary(config, locator,
                             hour_start, hour_end, list_buildings,
                             integer_year_start, integer_year_end, list_standard,
                             list_main_use_type, ratio_main_use_type,
                             bool_use_acronym, bool_aggregate_by_building,
                             bool_include_advanced_analytics, list_selected_time_period,
                             bool_use_conditioned_floor_area_for_normalisation,
                             plot=True, list_cea_feature_to_plot=list_cea_feature_to_plot)
        #

    def csv_mapping(self):
        # Define key order to generate passkey
        self.required_keys = ["key1", "key2", "key3"]  # Adjust based on actual keys

        # Predefined passkey-to-file mapping
        self.csv_mapping = {
            ("value_a", "value_c", "value_a"): "file1.csv",
            ("value_b", "value_c", "value_a"): "file2.csv",
            ("value_a", "value_d", "value_b"): "file3.csv",
        }

    def get_csv_path(self):
        """Returns the full path of the matched CSV file if it exists."""

        # Generate passkey tuple from user input
        passkey = tuple(self.user_input_dict.get(key, "default") for key in self.required_keys)

        # Lookup file based on passkey
        filename = self.csv_mapping.get(passkey)

        if filename:
            csv_path = os.path.join(self.base_dir, filename)
            return csv_path if os.path.exists(csv_path) else None  # Return path only if file exists

        return None  # No match found

# # ✅ **Example Usage**
# user_input = {
#     "key1": "value_a",
#     "key2": "value_c",
#     "key3": "value_a",
# }
#
# selector = CSVSelector(user_input)
# csv_path = selector.get_csv_path()
#
# print(csv_path)  # Expected: "data/results/file1.csv" (if it exists)

def main():
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    EnergyBalancePlot(config.project, {'building': config.plots.building,
                                       'scenario-name': config.scenario_name},
                      cache).plot(auto_open=True)


if __name__ == '__main__':
    main()

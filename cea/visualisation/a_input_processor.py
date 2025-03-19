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

    def __init__(self, config_config, scenario, cea_feature):
        """
        :param user_input: Dictionary containing user selections.

        """
        self.config = config_config
        self.scenario = scenario
        self.cea_feature = cea_feature
        self.buildings = config_config.buildings
        self.y_metric_to_plot = config_config.y_metric_to_plot
        

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

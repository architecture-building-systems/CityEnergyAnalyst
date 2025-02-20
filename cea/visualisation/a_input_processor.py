"""
InputProcessor – Determines the correct CSV file

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



class CSVSelector:
    """Maps user input combinations to pre-defined CSV file paths."""

    def __init__(self, user_input, base_dir="data/results"):
        """
        :param user_input: Dictionary containing user selections.
        :param base_dir: Base directory where CSV files are stored.
        """
        self.user_input = user_input
        self.base_dir = base_dir

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
        passkey = tuple(self.user_input.get(key, "default") for key in self.required_keys)

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

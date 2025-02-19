"""
CSVLoader – Reads CSV data, cleans and processes it for visualization

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


class CSVLoader:
    """Loads CSV data dynamically."""

    def __init__(self, file_path):
        self.file_path = file_path

    def load_data(self):
        """Reads CSV and returns a Pandas DataFrame."""
        try:
            df = pd.read_csv(self.file_path)
            return df
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return None

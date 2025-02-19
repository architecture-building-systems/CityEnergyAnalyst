"""
PlotFormatter – prepares the formatting settings for the Plotly graph

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



class DataProcessor:
    """Cleans and processes the CSV data for visualization."""

    def __init__(self, dataframe):
        self.df = dataframe

    def process_data(self):
        """Applies necessary data transformations."""
        if self.df is None:
            return None

        # Example: Calculate total energy demand per building
        if "total" not in self.df.columns:
            self.df["total"] = self.df.iloc[:, 1:].sum(axis=1)  # Sum all columns except 'Building Name'

        return self.df

# ✅ **Test DataProcessor**
processor = DataProcessor(data)
processed_data = processor.process_data()
print(processed_data.head())  # Check the transformed data

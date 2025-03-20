"""
Exporter – Handles CSV & image export

"""

import cea.inputlocator
import os
import cea.config
import time
import geopandas as gpd
import plotly.graph_objects as go
import plotly.io as pio


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class Exporter:
    """Handles exporting the chart as CSV or Image."""

    def __init__(self, dataframe, figure):
        self.df = dataframe
        self.fig = figure

    def export_csv(self, output_path="export.csv"):
        """Exports the processed data to a CSV file."""
        self.df.to_csv(output_path, index=False)
        print(f"CSV saved at: {output_path}")

    def export_image(self, output_path="export.png"):
        """Exports the Plotly figure as an image."""
        pio.write_image(self.fig, output_path)
        print(f"Image saved at: {output_path}")

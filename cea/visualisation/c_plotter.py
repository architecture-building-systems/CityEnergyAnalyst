"""
PlotManager – Generates the Plotly graph

"""

import cea.inputlocator
import os
import cea.config
import time
import geopandas as gpd
import plotly.graph_objects as go


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"



class PlotManager:
    """Generates a Plotly graph from processed data."""

    def __init__(self, dataframe, graph_type="bar"):
        self.df = dataframe
        self.graph_type = graph_type  # e.g., 'bar', 'line', 'pie'

    def generate_graph(self):
        """Creates a Plotly figure."""
        if self.df is None:
            return None

        fig = go.Figure()

        # Create stacked bar chart
        for col in self.df.columns[1:-1]:  # Excluding 'Building Name' and 'Total'
            fig.add_trace(go.Bar(
                x=self.df["Building Name"],
                y=self.df[col],
                name=col
            ))

        fig.update_layout(
            title="Energy Demand Analysis",
            xaxis_title="Building",
            yaxis_title="Energy Demand (MWh/yr)",
            barmode="stack"
        )

        return fig

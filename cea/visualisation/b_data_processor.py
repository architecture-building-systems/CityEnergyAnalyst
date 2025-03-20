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



class data_processor:
    """Cleans and processes the CSV data for visualization."""

    def __init__(self, config_config, scenario, plot_cea_feature, df_summary_data, df_architecture_data):
        self.df_summary_data = df_summary_data
        self.df_architecture_data = df_architecture_data
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

    def process_architecture_data(self):
        if self.normalised_by == 'gross_floor_area':
            normaliser_m2 = self.df_architecture_data.set_index('name').loc[self.buildings, ['GFA_m2']].copy()
            normaliser_m2 = normaliser_m2.rename(columns={'GFA_m2': 'normaliser_m2'})
        elif self.normalised_by == 'conditioned_floor_area':
            normaliser_m2 = self.df_architecture_data.set_index('name').loc[self.buildings, ['Af_m2']].copy()
            normaliser_m2 = normaliser_m2.rename(columns={'Af_m2': 'normaliser_m2'})
        else:
            normaliser_m2 = self.df_architecture_data.set_index('name').loc[self.buildings].copy()
            normaliser_m2['normaliser_m2'] = 1  # Replace all values with 1

        # Ensure only the 'normaliser_m2' column is retained
        normaliser_m2 = normaliser_m2[['normaliser_m2']]

        return normaliser_m2

    def process_demand_data(self):
        if self.df is None:
            return None

        # Example: Calculate total energy demand per building
        if "total" not in self.df.columns:
            self.df["total"] = self.df.iloc[:, 1:].sum(axis=1)  # Sum all columns except 'Building Name'

        return self.df


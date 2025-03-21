"""
PlotFormatter – prepares the formatting settings for the Plotly graph

"""

import pandas as pd


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

    def __init__(self, config_config, plot_instance, plot_cea_feature, df_summary_data, df_architecture_data):
        self.df_summary_data = df_summary_data
        self.df_architecture_data = df_architecture_data
        self.buildings = config_config.buildings
        self.y_metric_to_plot = config_config.y_metric_to_plot
        self.y_normalised_by = config_config.y_normalised_by
        self.x_to_plot = plot_instance.x_to_plot
        self.x_facet = plot_instance.x_facet
        self.integer_year_start = config_config.filter_buildings_by_year_start
        self.integer_year_end = config_config.filter_buildings_by_year_end
        self.list_construction_type = config_config.filter_buildings_by_construction_type
        self.list_use_type = config_config.filter_buildings_by_use_type
        self.min_ratio_as_main_use = config_config.min_ratio_as_main_use
        self.appendix = plot_cea_feature if plot_cea_feature == "demand" else "default"

    def process_architecture_data(self):
        if self.y_normalised_by == 'gross_floor_area':
            normaliser_m2 = self.df_architecture_data.set_index('name').loc[self.buildings, ['GFA_m2']].copy()
            normaliser_m2 = normaliser_m2.rename(columns={'GFA_m2': 'normaliser_m2'})
        elif self.y_normalised_by == 'conditioned_floor_area':
            normaliser_m2 = self.df_architecture_data.set_index('name').loc[self.buildings, ['Af_m2']].copy()
            normaliser_m2 = normaliser_m2.rename(columns={'Af_m2': 'normaliser_m2'})
        elif self.y_normalised_by == 'no_normalisation':
            normaliser_m2 = self.df_architecture_data.set_index('name').loc[self.buildings].copy()
            normaliser_m2['normaliser_m2'] = 1  # Replace all values with 1
        else:
            raise ValueError(f"Invalid y-normalised-by: {self.y_normalised_by}")

        # Ensure only the 'normaliser_m2' column is retained
        normaliser_m2 = normaliser_m2[['normaliser_m2']]

        return normaliser_m2

    def process_demand_data(self):
        y_cea_metric_map = {
            'grid_electricity_consumption': 'GRID_kWh',
            'enduse_electricity_demand': 'E_sys_kWh',
            'enduse_cooling_demand': 'QC_sys_kWh',
            'enduse_space_cooling_demand': 'Qcs_sys_kWh',
            'enduse_heating_demand': 'QH_sys_kWh',
            'enduse_space_heating_demand': 'Qhs_sys_kWh',
            'enduse_dhw_demand': 'Qww_kWh'
        }

        # Get the list of columns to plot
        list_columns = [y_cea_metric_map[key] for key in self.y_metric_to_plot if key in y_cea_metric_map]

        # slice the data frame to only keep the useful columns for Y-axis
        if self.x_to_plot == 'by_building':
            df_y_metrics = self.df_summary_data.set_index('name')[list_columns]
        elif self.x_to_plot == 'by_period':
            df_y_metrics = self.df_summary_data.set_index('period')[list_columns]
        else:
            raise ValueError(f"Invalid x-to-plot: {self.x_to_plot}")
        return df_y_metrics


# Main function
def calc_x_y_metric(config_config, plot_instance, plot_cea_feature, df_summary_data, df_architecture_data):
    plot_instance = data_processor(config_config, plot_instance, plot_cea_feature, df_summary_data, df_architecture_data)
    df_to_plotly = pd.DataFrame()
    if plot_cea_feature == "demand":

        # Calculating X:
        if plot_instance.x_to_plot == 'by_building':
            # Calculating Y: even when no_normalisation is selected, will just divide by 1 to keep the same value (not normalised)
            normaliser_m2 = plot_instance.process_architecture_data()
            df_y_metrics = plot_instance.process_demand_data()
            df_to_plotly = df_y_metrics.div(normaliser_m2.iloc[:, 0], axis=0)

            # Calculating X:
            df_to_plotly = df_to_plotly.reset_index(drop=False)
            df_to_plotly = df_to_plotly.rename(columns={'name': 'X'})

            # Calculating X_facet:
            if plot_instance.x_facet is None:
                pass
            elif plot_instance.x_facet == 'months':
                df_to_plotly['X_facet'] = df_summary_data['period']
            elif plot_instance.x_facet == 'seasons':
                df_to_plotly['X_facet'] = df_summary_data['period']
            elif plot_instance.x_facet == 'construction_type':
                df_to_plotly['X_facet'] = df_architecture_data['construction_type']
            elif plot_instance.x_facet == 'main_use_type':
                df_to_plotly['X_facet'] = df_architecture_data['main_use_type']
            else:
                raise ValueError(f"Invalid x-facet: {plot_instance.x_facet}")

        elif plot_instance.x_to_plot == 'by_period':
            # Calculating Y: even when no_normalisation is selected, will just divide by 1 to keep the same value (not normalised)
            normaliser_m2 = plot_instance.process_architecture_data()
            normaliser_m2_sum = normaliser_m2.iloc[:, 0].sum()
            df_y_metrics = plot_instance.process_demand_data()
            if plot_instance.y_normalised_by == 'no_normalisation':
                df_to_plotly = df_y_metrics
            else:
                df_to_plotly = df_y_metrics / normaliser_m2_sum

            # Calculating X:
            df_to_plotly = df_to_plotly.reset_index(drop=False)
            df_to_plotly = df_to_plotly.rename(columns={'period': 'X'})

            # Calculating X_facet:
            if plot_instance.x_facet is None:
                pass
            elif plot_instance.x_facet == 'daily':
                df_to_plotly['X_facet'] = df_summary_data['period']
            elif plot_instance.x_facet == 'monthly':
                df_to_plotly['X_facet'] = df_summary_data['period']
            elif plot_instance.x_facet == 'seasonally':
                df_to_plotly['X_facet'] = df_summary_data['period']
            elif plot_instance.x_facet == 'annually_or_selected':
                df_to_plotly['X_facet'] = df_summary_data['period']
            else:
                raise ValueError(f"Invalid x-facet: {plot_instance.x_facet}")

        else:
            raise ValueError(f"Invalid x-to-plot: {plot_instance.x_to_plot}")

        # Drop the index
        df_to_plotly = df_to_plotly.reset_index(drop=True)

    return df_to_plotly

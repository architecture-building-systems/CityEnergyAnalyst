"""
PlotFormatter – prepares the formatting settings for the Plotly graph

"""

import pandas as pd
import re

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
        self.y_metric_unit = config_config.y_metric_unit
        self.y_normalised_by = config_config.y_normalised_by
        self.x_to_plot = plot_instance.x
        self.x_group = plot_instance.x_group
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


def normalize_dataframe_by_index(dataframe_A, dataframe_B):
    """
    Normalize each column in dataframe_A by the corresponding value in dataframe_B based on index matching.

    Parameters:
    - dataframe_A (pd.DataFrame): A DataFrame with potentially repeated index values and one or more columns.
    - dataframe_B (pd.DataFrame): A DataFrame with unique index values and exactly one column (the normaliser).

    Returns:
    - pd.DataFrame: A normalized version of dataframe_A with the same shape.
    """

    # Ensure both inputs are DataFrames
    if not isinstance(dataframe_A, pd.DataFrame) or not isinstance(dataframe_B, pd.DataFrame):
        raise ValueError("Both inputs must be pandas DataFrames.")

    # Check that dataframe_B has only one column
    if dataframe_B.shape[1] != 1:
        raise ValueError("dataframe_B must have exactly one column.")

    # Copy inputs to avoid modifying them
    dfA = dataframe_A.copy()
    dfB = dataframe_B.copy()

    # Reset index for merge
    dfA_reset = dfA.reset_index()
    dfB_reset = dfB.reset_index()

    # Get index name for merge
    key_column = dfB.index.name if dfB.index.name is not None else 'index'
    dfB_reset.columns = [key_column, 'normaliser']

    if key_column not in dfA_reset.columns:
        dfA_reset[key_column] = dataframe_A.index

    # Merge
    merged = dfA_reset.merge(dfB_reset, on=key_column, how='left')

    # Normalize original columns
    original_columns = dataframe_A.columns
    for col in original_columns:
        merged[col] = merged[col] / merged['normaliser']

    # Drop normaliser column
    merged = merged.drop(columns=['normaliser'])

    # Restore original index
    merged.set_index(key_column, inplace=True)

    return merged


def convert_energy_units(dataframe, target_unit, normalised=False):
    """
    Converts energy unit columns in a DataFrame to the specified unit.

    Parameters:
        dataframe (pd.DataFrame): The input DataFrame with energy columns.
        target_unit (str): One of ['Wh', 'kWh', 'MWh'].
        normalised (bool): If True, appends '/m2' to the renamed unit.

    Returns:
        pd.DataFrame: A new DataFrame with converted energy units and renamed columns.
    """
    assert target_unit in ['Wh', 'kWh', 'MWh'], "target_unit must be one of ['Wh', 'kWh', 'MWh']"

    conversion_to_wh = {'Wh': 1, 'kWh': 1_000, 'MWh': 1_000_000}
    df = dataframe.copy()
    new_columns = {}

    for col in df.columns:
        for unit in conversion_to_wh:
            if col.endswith(f"_{unit}"):
                # Convert values
                factor = conversion_to_wh[unit] / conversion_to_wh[target_unit]
                df[col] = df[col] * factor

                # Rename column
                suffix = f"{target_unit}/m2" if normalised else target_unit
                new_col = col.replace(f"_{unit}", f"_{suffix}")
                new_columns[col] = new_col
                break  # Stop after first match

    df.rename(columns=new_columns, inplace=True)
    return df


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
            df_to_plotly = normalize_dataframe_by_index(df_y_metrics, normaliser_m2)

            # Calculating X:
            df_to_plotly = df_to_plotly.reset_index(drop=False)
            df_to_plotly = df_to_plotly.rename(columns={'name': 'X'})

            # Calculating X_group:
            if plot_instance.x_group is None:
                pass
            elif plot_instance.x_group == 'months':
                df_to_plotly['X_group'] = df_summary_data['period']
            elif plot_instance.x_group == 'seasons':
                df_to_plotly['X_group'] = df_summary_data['period']
            elif plot_instance.x_group == 'construction_type':
                df_to_plotly['X_group'] = df_architecture_data['construction_type']
            elif plot_instance.x_group == 'main_use_type':
                df_to_plotly['X_group'] = df_architecture_data['main_use_type']
            else:
                raise ValueError(f"Invalid x-group: {plot_instance.x_group}")

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

            # Calculating X_group:
            if plot_instance.x_group is None:
                pass
            elif plot_instance.x_group == 'daily':
                df_to_plotly['X_group'] = df_summary_data['period']
            elif plot_instance.x_group == 'monthly':
                df_to_plotly['X_group'] = df_summary_data['period']
            elif plot_instance.x_group == 'seasonally':
                df_to_plotly['X_group'] = df_summary_data['period']
            elif plot_instance.x_group == 'annually_or_selected':
                df_to_plotly['X_group'] = df_summary_data['period']
            else:
                raise ValueError(f"Invalid x-group: {plot_instance.x_group}")

        else:
            raise ValueError(f"Invalid x-to-plot: {plot_instance.x_to_plot}")

        # Drop the index
        df_to_plotly = df_to_plotly.reset_index(drop=True)

        # Convert energy units
        if plot_instance.y_normalised_by == 'no_normalisation':
            df_to_plotly = convert_energy_units(df_to_plotly, plot_instance.y_metric_unit, normalised=False)
        elif plot_instance.y_normalised_by == 'gross_floor_area' or 'conditioned_floor_area':
            df_to_plotly = convert_energy_units(df_to_plotly, plot_instance.y_metric_unit, normalised=True)
        else:
            raise ValueError(f"Invalid y-normalised-by: {plot_instance.y_normalised_by}")

    return df_to_plotly

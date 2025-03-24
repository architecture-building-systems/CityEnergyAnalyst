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

demand_x_to_plot_building = ['building', 'building_faceted_by_months', 'building_faceted_by_seasons', 'building_faceted_by_construction_type', 'building_faceted_by_main_use_type']

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
        self.x_facet = plot_instance.x_facet
        self.x_sorted_by = config_config.x_sorted_by
        self.x_sorted_reversed = config_config.x_sorted_reversed
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

    def process_sorting_key(self):
        if self.x_sorted_by == 'default':
            sorting_key = self.df_architecture_data.set_index('name').loc[self.buildings].copy()
            sorting_key['sorting_key'] = self.df_architecture_data.reset_index().index
        elif self.x_sorted_by == 'construction_year':
            sorting_key = self.df_architecture_data.set_index('name').loc[self.buildings, ['construction_year']].copy()
            sorting_key = sorting_key.rename(columns={'construction_year': 'sorting_key'})
        elif self.x_sorted_by == 'gross_floor_area':
            sorting_key = self.df_architecture_data.set_index('name').loc[self.buildings, ['GFA_m2']].copy()
            sorting_key = sorting_key.rename(columns={'GFA_m2': 'sorting_key'})
        elif self.x_sorted_by == 'conditioned_floor_area':
            sorting_key = self.df_architecture_data.set_index('name').loc[self.buildings, ['Af_m2']].copy()
            sorting_key = sorting_key.rename(columns={'Af_m2': 'sorting_key'})
        elif self.x_sorted_by == 'roof_area':
            sorting_key = self.df_architecture_data.set_index('name').loc[self.buildings, ['Aroof_m2']].copy()
            sorting_key = sorting_key.rename(columns={'Aroof_m2': 'sorting_key'})
        else:
            raise ValueError(f"Invalid x-sorted-by: {self.x_sorted_by}")

        sorting_key = sorting_key[['sorting_key']]

        return sorting_key

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
        return df_y_metrics, list_columns


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


def generate_dataframe_for_plotly(plot_instance, df_summary_data, df_architecture_data):
    """
    Generate a Plotly-ready DataFrame based on a plot_instance configuration.

    Parameters:
        plot_instance: An object containing plotting config and methods.
        df_summary_data (pd.DataFrame): DataFrame of aggregated demand results.
        df_architecture_data (pd.DataFrame): DataFrame of architecture/building metadata.

    Returns:
        pd.DataFrame: A normalized, unit-converted dataframe ready for Plotly visualization.
    """
    # Process normaliser and demand data
    normaliser_m2 = plot_instance.process_architecture_data()
    df_y_metrics, list_y_columns = plot_instance.process_demand_data()

    if plot_instance.x_to_plot == 'by_building':
        # Normalize Y
        df_to_plotly = normalize_dataframe_by_index(df_y_metrics, normaliser_m2)

        # Set X
        df_to_plotly = df_to_plotly.reset_index(drop=False)
        df_to_plotly = df_to_plotly.rename(columns={'name': 'X'})

        # Set X_facet
        if plot_instance.x_facet in ['months', 'seasons']:
            df_to_plotly['X_facet'] = df_summary_data['period']
        elif plot_instance.x_facet == 'construction_type':
            df_to_plotly['X_facet'] = df_architecture_data['construction_type']
        elif plot_instance.x_facet == 'main_use_type':
            df_to_plotly['X_facet'] = df_architecture_data['main_use_type']
        elif plot_instance.x_facet is not None:
            raise ValueError(f"Invalid x-facet: {plot_instance.x_facet}")

    elif plot_instance.x_to_plot == 'by_period':
        # Normalize Y
        if plot_instance.y_normalised_by == 'no_normalisation':
            df_to_plotly = df_y_metrics
        else:
            normaliser_m2_sum = normaliser_m2.iloc[:, 0].sum()
            df_to_plotly = df_y_metrics / normaliser_m2_sum

        # Set X
        df_to_plotly = df_to_plotly.reset_index(drop=False)
        df_to_plotly = df_to_plotly.rename(columns={'period': 'X'})

        # Set X_facet
        if plot_instance.x_facet in ['daily', 'monthly', 'seasonally', 'annually_or_selected']:
            df_to_plotly['X_facet'] = df_summary_data['period']
        elif plot_instance.x_facet is not None:
            raise ValueError(f"Invalid x-facet: {plot_instance.x_facet}")

    else:
        raise ValueError(f"Invalid x-to-plot: {plot_instance.x_to_plot}")

    # Clean up
    df_to_plotly = df_to_plotly.reset_index(drop=True)

    # Convert energy units
    if plot_instance.y_normalised_by == 'no_normalisation':
        df_to_plotly = convert_energy_units(df_to_plotly, plot_instance.y_metric_unit, normalised=False)
    elif plot_instance.y_normalised_by in ['gross_floor_area', 'conditioned_floor_area']:
        df_to_plotly = convert_energy_units(df_to_plotly, plot_instance.y_metric_unit, normalised=True)
    else:
        raise ValueError(f"Invalid y-normalised-by: {plot_instance.y_normalised_by}")

    # Sort X-axis

    return df_to_plotly, list_y_columns


def sort_df_by_sorting_key(df_1, df_2, descending=False):
    # Copy to avoid mutating original data
    df_1 = df_1.copy()
    df_2 = df_2.copy()

    # Map sorting_key to df_2 using df_2['X']
    sorting_map = df_1['sorting_key']
    df_2['_sorting_key'] = df_2['X'].map(sorting_map)

    # Sort with stable sort to preserve original order for ties
    df_2_sorted = df_2.sort_values(
        by='_sorting_key',
        ascending=not descending,
        kind='mergesort'
    )

    # Drop helper column
    df_2_sorted = df_2_sorted.drop(columns=['_sorting_key'])

    return df_2_sorted

# Main function
def calc_x_y_metric(config_config, plot_instance_a, plot_cea_feature, df_summary_data, df_architecture_data):
    plot_instance_b = data_processor(config_config, plot_instance_a, plot_cea_feature, df_summary_data, df_architecture_data)

    if plot_cea_feature == "demand":
        df_to_plotly, list_y_columns = generate_dataframe_for_plotly(plot_instance_b, df_summary_data, df_architecture_data)

        if plot_instance_b.x_to_plot in demand_x_to_plot_building:
            df_to_plotly = sort_df_by_sorting_key(plot_instance_b.process_sorting_key(), df_to_plotly, descending=plot_instance_b.x_sorted_reversed)

    else:
        print("Error: Unsupported feature:", plot_cea_feature)
        df_to_plotly = pd.DataFrame()   # This is unlikely to be used
        list_y_columns = []
    return df_to_plotly, list_y_columns

"""
PlotFormatter – prepares the formatting settings for the Plotly graph

"""

import pandas as pd
import numpy as np
from cea.import_export.result_summary import month_names, month_hours, season_mapping


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

x_to_plot_building = ['building', 'building_faceted_by_months', 'building_faceted_by_seasons', 'building_faceted_by_construction_type', 'building_faceted_by_main_use_type', 'building_faceted_by_decades']

class data_processor:
    """Cleans and processes the CSV data for visualization."""

    def __init__(self, plot_config, plot_config_general, plots_building_filter, plot_instance, plot_cea_feature, df_summary_data, df_architecture_data, solar_panel_types_list):
        self.df_summary_data = df_summary_data
        self.df_architecture_data = df_architecture_data
        self.buildings = plots_building_filter.buildings
        self.y_metric_to_plot = plot_config.y_metric_to_plot
        self.y_metric_unit = plot_config.y_metric_unit
        self.y_normalised_by = plot_config.y_normalised_by
        self.x_to_plot = plot_instance.x
        self.x_facet = plot_instance.x_facet
        self.x_sorted_by = plot_config_general.x_sorted_by
        self.x_sorted_reversed = plot_config_general.x_sorted_reversed
        self.integer_year_start = plots_building_filter.filter_buildings_by_year_start
        self.integer_year_end = plots_building_filter.filter_buildings_by_year_end
        self.list_construction_type = plots_building_filter.filter_buildings_by_construction_type
        self.list_use_type = plots_building_filter.filter_buildings_by_use_type
        self.min_ratio_as_main_use = plots_building_filter.min_ratio_as_main_use

        if plot_cea_feature in ('pv', 'sc'):
            self.appendix = f"{plot_cea_feature}_{solar_panel_types_list[0]}"
        elif plot_cea_feature == 'pvt':
            if len(solar_panel_types_list) == 2:
                self.appendix = f"{plot_cea_feature}_{solar_panel_types_list[0]}_{solar_panel_types_list[1]}"
            else:
                raise ValueError("PVT requires two solar panel types.")
        else:
            self.appendix = plot_cea_feature

    def process_architecture_data(self):
        if self.y_normalised_by == 'gross_floor_area':
            try:
                normaliser_m2 = self.df_architecture_data.set_index('name').loc[self.buildings, ['GFA_m2']].copy()
            except KeyError as e:
                missing = set(self.buildings) - set(self.df_architecture_data['name'].unique())
                raise ValueError(f"Missing building entries in architecture data: {missing}") from e
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


    def process_data(self, plot_cea_feature):
        if plot_cea_feature == 'demand':
            y_cea_metric_map = {
                'grid_electricity_consumption': 'GRID_kWh',
                'enduse_electricity_demand': 'E_sys_kWh',
                'enduse_cooling_demand': 'QC_sys_kWh',
                'enduse_space_cooling_demand': 'Qcs_sys_kWh',
                'enduse_heating_demand': 'QH_sys_kWh',
                'enduse_space_heating_demand': 'Qhs_sys_kWh',
                'enduse_dhw_demand': 'Qww_kWh',
            }

        elif plot_cea_feature == 'pv':
            y_cea_metric_map = {
                'total': ['E_PV_gen_kWh', 'area_PV_m2'],
                'roofs_top': ['PV_roofs_top_E_kWh', 'PV_roofs_top_m2'],
                'walls_north': ['PV_walls_north_E_kWh', 'PV_walls_north_m2'],
                'walls_east': ['PV_walls_east_E_kWh', 'PV_walls_east_m2'],
                'walls_south': ['PV_walls_south_E_kWh', 'PV_walls_south_m2'],
                'walls_west': ['PV_walls_west_E_kWh', 'PV_walls_west_m2'],
            }

        elif plot_cea_feature == 'pvt':
            if 'ET' in self.appendix:
                y_cea_metric_map = {
                    'total': ['E_PVT_gen_kWh', 'Q_PVT_gen_kWh', 'area_PVT_m2'],
                    'roofs_top': ['PVT_ET_roofs_top_E_kWh', 'PVT_ET_roofs_top_Q_kWh', 'PVT_ET_roofs_top_m2'],
                    'walls_north': ['PVT_ET_walls_north_E_kWh', 'PVT_ET_walls_north_Q_kWh', 'PVT_ET_walls_north_m2'],
                    'walls_east': ['PVT_ET_walls_east_E_kWh', 'PVT_ET_walls_east_Q_kWh', 'PVT_ET_walls_east_m2'],
                    'walls_south': ['PVT_ET_walls_south_E_kWh', 'PVT_ET_walls_south_Q_kWh', 'PVT_ET_walls_south_m2'],
                    'walls_west': ['PVT_ET_walls_west_E_kWh', 'PVT_ET_walls_west_Q_kWh', 'PVT_ET_walls_west_m2'],
                }
            elif 'FP' in self.appendix:
                y_cea_metric_map = {
                    'total': ['E_PVT_gen_kWh', 'Q_PVT_gen_kWh', 'area_PVT_m2'],
                    'roofs_top': ['PVT_FP_roofs_top_E_kWh', 'PVT_FP_roofs_top_Q_kWh', 'PVT_FP_roofs_top_m2'],
                    'walls_north': ['PVT_FP_walls_north_E_kWh', 'PVT_FP_walls_north_Q_kWh', 'PVT_FP_walls_north_m2'],
                    'walls_east': ['PVT_FP_walls_east_E_kWh', 'PVT_FP_walls_east_Q_kWh', 'PVT_FP_walls_east_m2'],
                    'walls_south': ['PVT_FP_walls_south_E_kWh', 'PVT_FP_walls_south_Q_kWh', 'PVT_FP_walls_south_m2'],
                    'walls_west': ['PVT_FP_walls_west_E_kWh', 'PVT_FP_walls_west_Q_kWh', 'PVT_FP_walls_west_m2'],
                }
            else:
                raise ValueError(f"Invalid PVT collector type in appendix: {self.appendix}")

        elif plot_cea_feature == 'sc':
            if 'ET' in self.appendix:
                y_cea_metric_map = {
                    'total': ['Q_SC_gen_kWh', 'area_SC_m2'],
                    'roofs_top': ['SC_ET_roofs_top_Q_kWh', 'SC_ET_roofs_top_m2'],
                    'walls_north': ['SC_ET_walls_north_Q_kWh', 'SC_ET_walls_north_m2'],
                    'walls_east': ['SC_ET_walls_east_Q_kWh', 'SC_ET_walls_east_m2'],
                    'walls_south': ['SC_ET_walls_south_Q_kWh', 'SC_ET_walls_south_m2'],
                    'walls_west': ['SC_ET_walls_west_Q_kWh', 'SC_ET_walls_west_m2'],
                }
            elif 'FP' in self.appendix:
                y_cea_metric_map = {
                    'total': ['Q_SC_gen_kWh', 'area_SC_m2'],
                    'roofs_top': ['SC_FP_roofs_top_Q_kWh', 'SC_FP_roofs_top_m2'],
                    'walls_north': ['SC_FP_walls_north_Q_kWh', 'SC_FP_walls_north_m2'],
                    'walls_east': ['SC_FP_walls_east_Q_kWh', 'SC_FP_walls_east_m2'],
                    'walls_south': ['SC_FP_walls_south_Q_kWh', 'SC_FP_walls_south_m2'],
                    'walls_west': ['SC_FP_walls_west_Q_kWh', 'SC_FP_walls_west_m2'],
                }
            else:
                raise ValueError(f"Invalid SC collector type in appendix: {self.appendix}")
        elif plot_cea_feature == 'operational-emissions':
            y_cea_metric_map = {
                'heating': ['heating_kgCO2e'],
                'hot_water': ['hot_water_kgCO2e'],
                'cooling': ['cooling_kgCO2e'],
                'electricity': ['electricity_kgCO2e'],
                'heating_NATURALGAS': ['Qhs_sys_NATURALGAS_kgCO2e'],
                'heating_BIOGAS': ['Qhs_sys_BIOGAS_kgCO2e'],
                'heating_SOLAR': ['Qhs_sys_SOLAR_kgCO2e'],
                'heating_DRYBIOMASS': ['Qhs_sys_DRYBIOMASS_kgCO2e'],
                'heating_WETBIOMASS': ['Qhs_sys_WETBIOMASS_kgCO2e'],
                'heating_GRID': ['Qhs_sys_GRID_kgCO2e'],
                'heating_COAL': ['Qhs_sys_COAL_kgCO2e'],
                'heating_WOOD': ['Qhs_sys_WOOD_kgCO2e'],
                'heating_OIL': ['Qhs_sys_OIL_kgCO2e'],
                'heating_HYDROGEN': ['Qhs_sys_HYDROGEN_kgCO2e'],
                'heating_NONE': ['Qhs_sys_NONE_kgCO2e'],
                'hot_water_NATURALGAS': ['Qww_sys_NATURALGAS_kgCO2e'],
                'hot_water_BIOGAS': ['Qww_sys_BIOGAS_kgCO2e'],
                'hot_water_SOLAR': ['Qww_sys_SOLAR_kgCO2e'],
                'hot_water_DRYBIOMASS': ['Qww_sys_DRYBIOMASS_kgCO2e'],
                'hot_water_WETBIOMASS': ['Qww_sys_WETBIOMASS_kgCO2e'],
                'hot_water_GRID': ['Qww_sys_GRID_kgCO2e'],
                'hot_water_COAL': ['Qww_sys_COAL_kgCO2e'],
                'hot_water_WOOD': ['Qww_sys_WOOD_kgCO2e'],
                'hot_water_OIL': ['Qww_sys_OIL_kgCO2e'],
                'hot_water_HYDROGEN': ['Qww_sys_HYDROGEN_kgCO2e'],
                'hot_water_NONE': ['Qww_sys_NONE_kgCO2e'],
                'cooling_NATURALGAS': ['Qcs_sys_NATURALGAS_kgCO2e'],
                'cooling_BIOGAS': ['Qcs_sys_BIOGAS_kgCO2e'],
                'cooling_SOLAR': ['Qcs_sys_SOLAR_kgCO2e'],
                'cooling_DRYBIOMASS': ['Qcs_sys_DRYBIOMASS_kgCO2e'],
                'cooling_WETBIOMASS': ['Qcs_sys_WETBIOMASS_kgCO2e'],
                'cooling_GRID': ['Qcs_sys_GRID_kgCO2e'],
                'cooling_COAL': ['Qcs_sys_COAL_kgCO2e'],
                'cooling_WOOD': ['Qcs_sys_WOOD_kgCO2e'],
                'cooling_OIL': ['Qcs_sys_OIL_kgCO2e'],
                'cooling_HYDROGEN': ['Qcs_sys_HYDROGEN_kgCO2e'],
                'cooling_NONE': ['Qcs_sys_NONE_kgCO2e'],
                'electricity_NATURALGAS': ['E_sys_NATURALGAS_kgCO2e'],
                'electricity_BIOGAS': ['E_sys_BIOGAS_kgCO2e'],
                'electricity_SOLAR': ['E_sys_SOLAR_kgCO2e'],
                'electricity_DRYBIOMASS': ['E_sys_DRYBIOMASS_kgCO2e'],
                'electricity_WETBIOMASS': ['E_sys_WETBIOMASS_kgCO2e'],
                'electricity_GRID': ['E_sys_GRID_kgCO2e'],
                'electricity_COAL': ['E_sys_COAL_kgCO2e'],
                'electricity_WOOD': ['E_sys_WOOD_kgCO2e'],
                'electricity_OIL': ['E_sys_OIL_kgCO2e'],
                'electricity_HYDROGEN': ['E_sys_HYDROGEN_kgCO2e'],
                'electricity_NONE': ['E_sys_NONE_kgCO2e'],
            }
        elif plot_cea_feature == 'lifecycle-emissions':
            y_cea_metric_map = {
                'operation_heating': ['operation_heating_kgCO2e'],
                'operation_hot_water': ['operation_hot_water_kgCO2e'],
                'operation_cooling': ['operation_cooling_kgCO2e'],
                'operation_electricity': ['operation_electricity_kgCO2e'],
                'production_wall_ag': ['production_wall_ag_kgCO2e'],
                'production_wall_bg': ['production_wall_bg_kgCO2e'],
                'production_wall_part': ['production_wall_part_kgCO2e'],
                'production_win_ag': ['production_win_ag_kgCO2e'],
                'production_roof': ['production_roof_kgCO2e'],
                'production_upperside': ['production_upperside_kgCO2e'],
                'production_underside': ['production_underside_kgCO2e'],
                'production_floor': ['production_floor_kgCO2e'],
                'production_base': ['production_base_kgCO2e'],
                'production_technical_systems': ['production_technical_systems_kgCO2e'],
                'biogenic_wall_ag': ['biogenic_wall_ag_kgCO2e'],
                'biogenic_wall_bg': ['biogenic_wall_bg_kgCO2e'],
                'biogenic_wall_part': ['biogenic_wall_part_kgCO2e'],
                'biogenic_win_ag': ['biogenic_win_ag_kgCO2e'],
                'biogenic_roof': ['biogenic_roof_kgCO2e'],
                'biogenic_upperside': ['biogenic_upperside_kgCO2e'],
                'biogenic_underside': ['biogenic_underside_kgCO2e'],
                'biogenic_floor': ['biogenic_floor_kgCO2e'],
                'biogenic_base': ['biogenic_base_kgCO2e'],
                'biogenic_technical_systems': ['biogenic_technical_systems_kgCO2e'],
                'demolition_wall_ag': ['demolition_wall_ag_kgCO2e'],
                'demolition_wall_bg': ['demolition_wall_bg_kgCO2e'],
                'demolition_wall_part': ['demolition_wall_part_kgCO2e'],
                'demolition_win_ag': ['demolition_win_ag_kgCO2e'],
                'demolition_roof': ['demolition_roof_kgCO2e'],
                'demolition_upperside': ['demolition_upperside_kgCO2e'],
                'demolition_underside': ['demolition_underside_kgCO2e'],
                'demolition_floor': ['demolition_floor_kgCO2e'],
                'demolition_base': ['demolition_base_kgCO2e'],
                'demolition_technical_systems': ['demolition_technical_systems_kgCO2e'],

            }

        else:
            raise ValueError(f"Unknown plot_cea_feature: '{plot_cea_feature}'")

        # Flatten metric list and remove any invalid entries
        list_columns = []
        for key in self.y_metric_to_plot:
            if key not in y_cea_metric_map:
                print(f"⚠️ Warning: '{key}' not found in metric map for {plot_cea_feature}. Skipped.")
                continue
            val = y_cea_metric_map[key]
            list_columns.extend(val if isinstance(val, list) else [val])

        # Debug: Check what columns are available
        if not list_columns:
            print(f"❌ No valid columns found for {plot_cea_feature} with metrics {self.y_metric_to_plot}")
            print(f"Available columns in data: {list(self.df_summary_data.columns)}")
            return pd.DataFrame(), []
        
        # Check if the required columns exist in the data
        missing_columns = [col for col in list_columns if col not in self.df_summary_data.columns]
        if missing_columns:
            print(f"⚠️ Missing columns in data: {missing_columns}")
            print(f"Available columns: {list(self.df_summary_data.columns)}")
            # Filter out missing columns
            list_columns = [col for col in list_columns if col in self.df_summary_data.columns]
            if not list_columns:
                print("❌ No valid columns remaining after filtering")
                return pd.DataFrame(), []

        # Select proper index
        if self.x_to_plot == 'by_building':
            df_y_metrics = self.df_summary_data.set_index('name')[list_columns]
        elif self.x_to_plot == 'by_period':
            df_y_metrics = self.df_summary_data.set_index('period')[list_columns]
        else:
            raise ValueError(f"Invalid x_to_plot: {self.x_to_plot}")

        return df_y_metrics, list_columns


def normalise_dataframe_by_index(dataframe_A, dataframe_B):
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


def convert_energy_units(dataframe, target_unit, normalised=False, plot_cea_feature=None):
    """
    Converts energy unit columns in a DataFrame to the specified unit.

    Parameters:
        dataframe (pd.DataFrame): The input DataFrame with energy columns.
        target_unit (str): One of ['Wh', 'kWh', 'MWh'].
        normalised (bool): If True, appends '/m2' to the renamed unit.

    Returns:
        pd.DataFrame: A new DataFrame with converted energy units and renamed columns.
    """
    if plot_cea_feature in ('operational-emissions', 'lifecycle-emissions'):
        assert target_unit in ['gCO2e', 'kgCO2e', 'tonCO2e'], "target_unit must be one of ['gCO2e', 'kgCO2e', 'tonCO2e']"

        conversion_to_wh = {'gCO2e': 1, 'kgCO2e': 1_000, 'tonCO2e': 1_000_000}
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

    else:
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


def generate_dataframe_for_plotly(plot_instance, df_summary_data, df_architecture_data, plot_cea_feature):
    """
    Generate a Plotly-ready DataFrame based on user-defined configuration.

    Parameters
    ----------
    plot_instance : object
        Configuration and logic object containing plotting parameters and methods.
    df_summary_data : pd.DataFrame
        Aggregated demand or generation results.
    df_architecture_data : pd.DataFrame
        Metadata for buildings (e.g., use type, construction year).
    plot_cea_feature : str
        Feature to be plotted: 'demand', 'pv', 'pvt', or 'sc'.

    Returns
    -------
    pd.DataFrame
        A processed DataFrame ready for Plotly visualization.
    list
        List of column names used for plotting Y-values.
    """
    # Step 1: Prepare normaliser and raw Y-axis metrics
    if plot_instance.y_normalised_by in ('no_normalisation', 'gross_floor_area', 'conditioned_floor_area'):
        normaliser_m2 = plot_instance.process_architecture_data()
    df_y_metrics, list_y_columns = plot_instance.process_data(plot_cea_feature)

    # Step 2: Handle "by_building" mode
    if plot_instance.x_to_plot == 'by_building':
        if plot_cea_feature in ('demand',  'operational-emissions', 'lifecycle-emissions'):
            df_to_plotly = normalise_dataframe_by_index(df_y_metrics, normaliser_m2)

        elif plot_cea_feature in ('pv', 'pvt', 'sc'):
            norm = plot_instance.y_normalised_by
            if norm == 'no_normalisation':
                df_to_plotly = remove_m2_columns(df_y_metrics)
            elif norm == 'solar_technology_area_installed_for_respective_surface':
                df_to_plotly = normalise_dataframe_columns_by_m2_columns(df_y_metrics)
            elif norm == 'gross_floor_area':
                df_to_plotly = normalise_dataframe_by_index(remove_m2_columns(df_y_metrics), normaliser_m2)
            else:
                raise ValueError(f"Invalid y_normalised_by: {norm}")
        else:
            raise ValueError(f"Invalid plot_cea_feature: {plot_cea_feature}")

        # Assign X and X_facet
        df_to_plotly = df_to_plotly.reset_index(drop=False).rename(columns={'name': 'X'})
        facet = plot_instance.x_facet
        if facet in ['months', 'seasons']:
            df_to_plotly['X_facet'] = df_summary_data['period']
        elif facet in ['construction_type', 'main_use_type']:
            df_to_plotly['X_facet'] = df_architecture_data[facet]
        elif facet is not None:
            raise ValueError(f"Invalid x_facet: {facet}")

    # Step 3: Handle "by_period" mode
    elif plot_instance.x_to_plot == 'by_period':
        norm = plot_instance.y_normalised_by
        if norm == 'no_normalisation':
            df_to_plotly = remove_m2_columns(df_y_metrics) if plot_cea_feature in ('pv', 'pvt', 'sc') else df_y_metrics
        elif norm == 'solar_technology_area_installed_for_respective_surface':
            if plot_cea_feature in ('pv', 'pvt', 'sc'):
                df_to_plotly = normalise_dataframe_columns_by_m2_columns(df_y_metrics)
            else:
                raise ValueError(f"Invalid plot_cea_feature: {plot_cea_feature}")
        else:
            total_area = normaliser_m2.iloc[:, 0].sum()
            df_to_plotly = df_y_metrics / total_area

        # Assign X and X_facet
        df_to_plotly = df_to_plotly.reset_index(drop=False).rename(columns={'period': 'X'})
        facet = plot_instance.x_facet
        if facet in ['months', 'seasons']:
            df_to_plotly = calc_x_facet(df_to_plotly, facet)
        elif facet is not None:
            raise ValueError(f"Invalid x_facet: {facet}")
    else:
        raise ValueError(f"Invalid x_to_plot: {plot_instance.x_to_plot}")

    # Step 4: Clean index
    df_to_plotly = df_to_plotly.reset_index(drop=True)

    # Step 5: Convert energy units
    is_normalised = plot_instance.y_normalised_by != 'no_normalisation'
    df_to_plotly = convert_energy_units(df_to_plotly, plot_instance.y_metric_unit, normalised=is_normalised, plot_cea_feature=plot_cea_feature)

    # Step 6: Refine list_y_columns
    valid_cols = df_to_plotly.columns.difference(['X', 'X_facet']).tolist()
    updated_list_y_columns = []
    for col in list_y_columns:
        if col.endswith('_m2'):
            continue
        if col in valid_cols:
            updated_list_y_columns.append(col)
        else:
            if plot_cea_feature in ('operational-emissions', 'lifecycle-emissions'):
                base = col.replace('_kgCO2e', f'_{plot_instance.y_metric_unit}')
            else:
                base = col.replace('_kWh', f'_{plot_instance.y_metric_unit}')
            maybe_col = f"{base}/m2" if is_normalised else base
            if maybe_col in valid_cols:
                updated_list_y_columns.append(maybe_col)
    list_y_columns = updated_list_y_columns

    # Step 7: Reorder columns for 'pvt' (electricity first, then heat)
    if plot_cea_feature == 'pvt':
        elec_cols = [c for c in list_y_columns if 'E_' in c]
        heat_cols = [c for c in list_y_columns if 'Q_' in c]
        list_y_columns = elec_cols + heat_cols
        essentials = ['X', 'X_facet'] if 'X_facet' in df_to_plotly.columns else ['X']
        df_to_plotly = df_to_plotly[essentials + list_y_columns]

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

def remove_m2_columns(df):
    """
    Remove all columns that end with '_m2' from the given DataFrame.

    Parameters:
    - df (pd.DataFrame): Input DataFrame.

    Returns:
    - pd.DataFrame: A new DataFrame without '_m2' columns.
    """
    return df[[col for col in df.columns if not col.endswith('_m2')]]


def calc_x_facet(df_to_plotly, facet_by):
    def get_month_from_x(x):
        if x.startswith("H_"):
            hour_index = int(x.replace("H_", ""))
            total = 0
            for i, m in enumerate(month_names):
                total += month_hours[m]
                if hour_index < total:
                    return m
        elif x.startswith("D_"):
            day_index = int(x.replace("D_", ""))
            total_days = 0
            for i, m in enumerate(month_names):
                days_in_month = month_hours[m] // 24
                total_days += days_in_month
                if day_index < total_days:
                    return m
        elif x in month_names:
            return x
        return None

    if facet_by not in ['months', 'seasons']:
        raise ValueError("facet_by must be either 'months' or 'season'")

    # Compute months first
    df_to_plotly['X_facet'] = df_to_plotly['X'].apply(get_month_from_x)

    # If facet_by is season, map month to season
    if facet_by == 'seasons':
        df_to_plotly['X_facet'] = df_to_plotly['X_facet'].map(lambda m: season_mapping[month_names.index(m) + 1] if m in month_names else None)

    return df_to_plotly


def normalise_dataframe_columns_by_m2_columns(df_y_metrics):
    """
    Normalize metric columns in the dataframe by their corresponding m2 columns and drop the m2 columns.

    If area is zero or missing for any row, the resulting value will be set to 0 (instead of dividing by zero).

    Parameters
    ----------
    df_y_metrics : pd.DataFrame
        Input dataframe with area and metric columns.

    Returns
    -------
    pd.DataFrame
        Normalized dataframe with area columns removed.
    """
    mapping = {
        'area_PV_m2': 'E_PV_gen_kWh',
        'PV_roofs_top_m2': 'PV_roofs_top_E_kWh',
        'PV_walls_north_m2': 'PV_walls_north_E_kWh',
        'PV_walls_east_m2': 'PV_walls_east_E_kWh',
        'PV_walls_south_m2': 'PV_walls_south_E_kWh',
        'PV_walls_west_m2': 'PV_walls_west_E_kWh',
        'area_PVT_m2': ['E_PVT_gen_kWh', 'Q_PVT_gen_kWh'],
        'PVT_ET_roofs_top_m2': ['PVT_ET_roofs_top_E_kWh', 'PVT_ET_roofs_top_Q_kWh'],
        'PVT_ET_walls_north_m2': ['PVT_ET_walls_north_E_kWh', 'PVT_ET_walls_north_Q_kWh'],
        'PVT_ET_walls_east_m2': ['PVT_ET_walls_east_E_kWh', 'PVT_ET_walls_east_Q_kWh'],
        'PVT_ET_walls_south_m2': ['PVT_ET_walls_south_E_kWh', 'PVT_ET_walls_south_Q_kWh'],
        'PVT_ET_walls_west_m2': ['PVT_ET_walls_west_E_kWh', 'PVT_ET_walls_west_Q_kWh'],
        'PVT_FP_roofs_top_m2': ['PVT_FP_roofs_top_E_kWh', 'PVT_FP_roofs_top_Q_kWh'],
        'PVT_FP_walls_north_m2': ['PVT_FP_walls_north_E_kWh', 'PVT_FP_walls_north_Q_kWh'],
        'PVT_FP_walls_east_m2': ['PVT_FP_walls_east_E_kWh', 'PVT_FP_walls_east_Q_kWh'],
        'PVT_FP_walls_south_m2': ['PVT_FP_walls_south_E_kWh', 'PVT_FP_walls_south_Q_kWh'],
        'PVT_FP_walls_west_m2': ['PVT_FP_walls_west_E_kWh', 'PVT_FP_walls_west_Q_kWh'],
        'area_SC_m2': 'Q_SC_gen_kWh',
        'SC_ET_roofs_top_m2': 'SC_ET_roofs_top_Q_kWh',
        'SC_ET_walls_north_m2': 'SC_ET_walls_north_Q_kWh',
        'SC_ET_walls_east_m2': 'SC_ET_walls_east_Q_kWh',
        'SC_ET_walls_south_m2': 'SC_ET_walls_south_Q_kWh',
        'SC_ET_walls_west_m2': 'SC_ET_walls_west_Q_kWh',
        'SC_FP_roofs_top_m2': 'SC_FP_roofs_top_Q_kWh',
        'SC_FP_walls_north_m2': 'SC_FP_walls_north_Q_kWh',
        'SC_FP_walls_east_m2': 'SC_FP_walls_east_Q_kWh',
        'SC_FP_walls_south_m2': 'SC_FP_walls_south_Q_kWh',
        'SC_FP_walls_west_m2': 'SC_FP_walls_west_Q_kWh',
    }

    df = df_y_metrics.copy()

    for area_col, metrics in mapping.items():
        if area_col not in df.columns:
            continue

        if isinstance(metrics, str):
            metrics = [metrics]

        for metric in metrics:
            if metric in df.columns:
                # Avoid division by 0 by masking
                with np.errstate(divide='ignore', invalid='ignore'):
                    area = df[area_col]
                    mask = area > 0
                    # Create normalized values: 0 where area <= 0, metric/area where area > 0
                    df[metric] = np.where(mask, df[metric] / area, 0.0)

    # Drop all *_m2 columns
    df.drop(columns=[col for col in df.columns if col.endswith('_m2')], inplace=True)

    return df


# Main function
def calc_x_y_metric(plot_config, plot_config_general, plots_building_filter, plot_instance_a, plot_cea_feature, df_summary_data, df_architecture_data, solar_panel_types_list):
    plot_instance_b = data_processor(plot_config, plot_config_general, plots_building_filter, plot_instance_a, plot_cea_feature, df_summary_data, df_architecture_data, solar_panel_types_list)

    if plot_cea_feature in ["demand", "pv", "pvt", "sc", "operational-emissions", "lifecycle-emissions"]:
        df_to_plotly, list_y_columns = generate_dataframe_for_plotly(plot_instance_b, df_summary_data, df_architecture_data, plot_cea_feature)

        if plot_instance_b.x_to_plot in x_to_plot_building:
            df_to_plotly = sort_df_by_sorting_key(plot_instance_b.process_sorting_key(), df_to_plotly, descending=plot_instance_b.x_sorted_reversed)

    else:
        print("Error: Unsupported feature:", plot_cea_feature)
        df_to_plotly = pd.DataFrame()   # This is unlikely to be used
        list_y_columns = []
    return df_to_plotly, list_y_columns

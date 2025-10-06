# -*- coding: utf-8 -*-




import math
import os
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objs as go
from plotly.offline import plot
import sys

import cea.config
import cea.plots.demand
from cea.visualisation.a_data_loader import plot_input_processor
from cea.visualisation.b_data_processor import calc_x_y_metric
from cea.visualisation.format.plot_colours import COLOURS_TO_RGB, get_column_color
from cea.import_export.result_summary import filter_buildings

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

class EmissionTimelinePlot:
    """
    Creates a line plot showing emissions over time.
    - Positive emissions (operation, production, demolition) above x-axis
    - Negative emissions (biogenic, pv) below x-axis
    """

    def __init__(self, df_to_plotly, list_y_columns, plot_title="Emission Timeline", bool_accumulated=False):
        """
        Initialize the EmissionTimelinePlot.

        Parameters:
        -----------
        df_to_plotly : pd.DataFrame
            DataFrame containing emission data with columns:
            - 'X': year values
            - emission columns (e.g., 'operation_heating_kgCO2e', 'biogenic_wall_ag_kgCO2e', etc.)
        list_y_columns : list
            List of column names to plot
        plot_title : str
            Title for the plot
        bool_accumulated : bool
            If True, show cumulative emissions over time. If False, show annual emissions.
        """
        self.df = df_to_plotly
        self.y_columns = list_y_columns
        self.plot_title = plot_title
        self.bool_accumulated = bool_accumulated

    def categorize_and_aggregate_emissions(self):
        """
        Categorize emission columns and aggregate by category.

        Returns:
        --------
        dict: Dictionary with category names as keys and aggregated Series as values
              Also includes metadata about whether each category is positive or negative
        """
        categories = {
            'operation': {'columns': [], 'positive': True},
            'production': {'columns': [], 'positive': True},
            'demolition': {'columns': [], 'positive': True},
            'biogenic': {'columns': [], 'positive': False},
            'pv': {'columns': [], 'positive': False}
        }

        # Categorize columns
        for col in self.y_columns:
            col_lower = col.lower()
            if 'biogenic' in col_lower:
                categories['biogenic']['columns'].append(col)
            elif 'pv' in col_lower:
                categories['pv']['columns'].append(col)
            elif 'operation' in col_lower:
                categories['operation']['columns'].append(col)
            elif 'production' in col_lower:
                categories['production']['columns'].append(col)
            elif 'demolition' in col_lower:
                categories['demolition']['columns'].append(col)

        # Aggregate columns within each category
        aggregated_data = {}
        for category, info in categories.items():
            if info['columns']:
                # Sum all columns in this category
                aggregated_data[category] = {
                    'data': self.df[info['columns']].sum(axis=1),
                    'positive': info['positive']
                }

        return aggregated_data

    def create_plot(self):
        """
        Create the Plotly figure with line graphs, aggregated by category.

        Returns:
        --------
        go.Figure: Plotly figure object
        """
        aggregated_data = self.categorize_and_aggregate_emissions()

        # Define colors for each category
        category_colors = {
            'operation': COLOURS_TO_RGB['red'],
            'production': COLOURS_TO_RGB['orange'],
            'demolition': COLOURS_TO_RGB['green'],
            'biogenic': COLOURS_TO_RGB['blue'],
            'pv': COLOURS_TO_RGB['yellow']
        }

        fig = go.Figure()

        # Add traces for each category
        for category, info in aggregated_data.items():
            color = category_colors.get(category, COLOURS_TO_RGB['grey'])
            display_name = category.capitalize()
            is_positive = info['positive']
            data = info['data']

            if is_positive:
                # Positive emissions (above x-axis) - solid line
                fig.add_trace(go.Scatter(
                    x=self.df['X'],
                    y=data,
                    mode='lines',
                    name=display_name,
                    line=dict(color=color, width=3),
                    hovertemplate=f'<b>{display_name}</b><br>Year: %{{x}}<br>Emission: %{{y:.2f}}<extra></extra>'
                ))
            else:
                # Negative emissions (below x-axis) - dashed line
                fig.add_trace(go.Scatter(
                    x=self.df['X'],
                    y=-data,  # Negate to show below x-axis
                    mode='lines',
                    name=display_name,
                    line=dict(color=color, width=3, dash='dash'),
                    hovertemplate=f'<b>{display_name}</b><br>Year: %{{x}}<br>Emission: -%{{y:.2f}}<extra></extra>'
                ))

        # Update layout
        fig.update_layout(
            title=dict(
                text=self.plot_title,
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(
                title='Year',
                showgrid=True,
                gridcolor='rgba(200,200,200,0.3)'
            ),
            yaxis=dict(
                title=self._get_y_axis_label(),
                showgrid=True,
                gridcolor='rgba(200,200,200,0.3)',
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='black'
            ),
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation='v',
                yanchor='top',
                y=1,
                xanchor='left',
                x=1.05
            ),
            margin=dict(l=80, r=200, t=80, b=60)
        )

        return fig

    def _get_display_name(self, column_name):
        """
        Convert column name to display name.
        Removes unit suffixes and formats for readability.

        Parameters:
        -----------
        column_name : str
            Column name with unit (e.g., 'operation_heating_kgCO2e')

        Returns:
        --------
        str: Display name (e.g., 'Operation Heating')
        """
        # Remove unit patterns
        base_name = column_name
        for unit in ['_tonCO2e', '_kgCO2e', '_gCO2e', '_MWh', '_kWh', '_Wh']:
            if base_name.endswith(unit):
                base_name = base_name[:-len(unit)]
                break

        # Remove /m2 suffix
        if '/m2' in base_name:
            base_name = base_name.split('/m2')[0]

        # Convert underscores to spaces and capitalize
        display_name = base_name.replace('_', ' ').title()

        return display_name

    def _get_y_axis_label(self):
        """
        Determine y-axis label from column units.

        Returns:
        --------
        str: Y-axis label
        """
        if not self.y_columns:
            return 'Emissions'

        # Check first column for unit
        sample_col = self.y_columns[0]

        if '_tonCO2e' in sample_col:
            unit = 'tonCO2e'
        elif '_kgCO2e' in sample_col:
            unit = 'kgCO2e'
        elif '_gCO2e' in sample_col:
            unit = 'gCO2e'
        else:
            unit = 'CO2e'

        # Check for normalization
        if '/m2' in sample_col:
            return f'Emissions ({unit}/m²)'
        else:
            return f'Emissions ({unit})'

def plot_emission_timeline(config, context: dict):
    scenario = config.scenario
    plot_cea_feature = 'lifecycle-emissions'
    period_start = context.get('period_start', 0)
    period_end = context.get('period_end', 8759)
    plot_cea_feature_umbrella = context.get('feature', 'emission-timeline')
    solar_panel_types_list = []
    plot_config_general = config.sections["plots-general"]
    plots_building_filter = config.sections["plots-building-filter"]
    plot_config = config.sections[f"plots-{plot_cea_feature_umbrella}"]
    bool_include_advanced_analytics = False

    # Activate a_data_loader
    df_summary_data, df_architecture_data, plot_instance = plot_input_processor(plot_config, plot_config_general,
                                                                                plots_building_filter, scenario,
                                                                                plot_cea_feature,
                                                                                period_start, period_end,
                                                                                solar_panel_types_list,
                                                                                bool_include_advanced_analytics)
    # Activate b_data_processor
    df_to_plotly, list_y_columns = calc_x_y_metric(plot_config, plot_config_general, plots_building_filter,
                                                   plot_instance, plot_cea_feature, df_summary_data,
                                                   df_architecture_data,
                                                   solar_panel_types_list)

    # Create EmissionTimelinePlot instance
    plot_obj = EmissionTimelinePlot(df_to_plotly, list_y_columns, plot_title="Emission Timeline")

    # Generate the figure
    fig = plot_obj.create_plot()

    return fig


def main(config):
    import cea.inputlocator

    locator = cea.inputlocator.InputLocator(config.scenario)
    # cache = cea.plots.cache.PlotCache(config.project)
    cache = cea.plots.cache.NullPlotCache()


    list_buildings = config.plots_general.buildings
    integer_year_start = config.plots_building_filter.filter_buildings_by_year_start
    integer_year_end = config.plots_building_filter.filter_buildings_by_year_end
    list_standard = config.plots_building_filter.filter_buildings_by_construction_type
    list_main_use_type = config.plots_building_filter.filter_buildings_by_use_type
    ratio_main_use_type = config.plots_building_filter.min_ratio_as_main_use
    _, list_buildings = filter_buildings(locator, list_buildings,
                                         integer_year_start, integer_year_end, list_standard,
                                         list_main_use_type, ratio_main_use_type)

    bool_accumulated = True

    print(f"Filtered buildings list: {list_buildings}")
    print(f"Number of buildings: {len(list_buildings)}")


    context = {'feature': 'emission-timeline', 'period_end': 2035, 'period_start': 2060, 'solar_panel_types': {}}

    # Generate comfort charts for all buildings
    fig = plot_emission_timeline(config, context)

    print(fig)


    plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    # Always show in browser
    fig.show(renderer="browser")

    return plot_html



if __name__ == '__main__':
    main(cea.config.Configuration())

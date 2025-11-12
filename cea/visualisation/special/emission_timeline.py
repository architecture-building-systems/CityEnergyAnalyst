# -*- coding: utf-8 -*-

import pandas as pd
import plotly.graph_objs as go
import cea.config
from cea.visualisation.a_data_loader import plot_input_processor
from cea.visualisation.b_data_processor import calc_x_y_metric
from cea.visualisation.format.plot_colours import COLOURS_TO_RGB
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

    def __init__(self, config, df_to_plotly, list_y_columns, plot_title="Emission Timeline",
                 bool_accumulated=False, period_start=None, period_end=None):
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
        period_start : int, optional
            Start year for filtering data. If None, use all data from the beginning.
        period_end : int, optional
            End year for filtering data. If None, use all data to the end.
        """
        # Filter dataframe by period if specified
        if period_start is not None or period_end is not None:
            # Convert X column to numeric for comparison
            # Handle formats like 'Y_2024' or just '2024'
            x_values = df_to_plotly['X'].astype(str).str.replace('Y_', '', regex=False)
            x_values = pd.to_numeric(x_values, errors='coerce')
            # Create mask with the same index as df_to_plotly to avoid alignment errors
            mask = pd.Series(True, index=df_to_plotly.index)

            if period_start is not None:
                mask &= x_values >= period_start
            if period_end is not None:
                mask &= x_values <= period_end

            self.df = df_to_plotly[mask].copy()
        else:
            self.df = df_to_plotly

        self.y_columns = list_y_columns
        self.plot_title = plot_title
        self.bool_accumulated = bool_accumulated
        self.period_start = period_start
        self.period_end = period_end
        self.config = config

        self.plot_type = config.plots_emission_timeline.plot_type

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
            'biogenic': {'columns': [], 'positive': True},
            'pv': {'columns': [], 'positive': True}
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
        Create the Plotly figure with different plot types (line_cumulative, line_net_cumulative, shaded_stack_cumulative, shaded_stack_percentage_cumulative).

        Returns:
        --------
        go.Figure: Plotly figure object
        """
        if self.plot_type == 'line_cumulative':
            return self._create_line_plot()
        elif self.plot_type == 'line_net_cumulative':
            return self._create_line_net_plot()
        elif self.plot_type == 'shaded_stack_cumulative':
            return self._create_stacked_area_plot(percentage=False)
        elif self.plot_type == 'shaded_stack_percentage_cumulative':
            return self._create_stacked_area_plot(percentage=True)
        else:
            # Default to line_cumulative plot
            return self._create_line_plot()

    def _create_line_plot(self):
        """
        Create line plot showing emissions over time.
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
            display_name = 'PV' if category == 'pv' else category.capitalize()
            is_positive = info['positive']
            data = info['data']

            # Apply cumulative sum if bool_accumulated is True
            if self.bool_accumulated:
                data = data.cumsum()
                hover_label = "Cumulative Emission"
            else:
                hover_label = "Emission"

            if is_positive:
                # Positive emissions (above x-axis) - solid line
                fig.add_trace(go.Scatter(
                    x=self.df['X'],
                    y=data,
                    mode='lines',
                    name=display_name,
                    line=dict(color=color, width=3),
                    hovertemplate=f'<b>{display_name}</b><br>Year: %{{x}}<br>{hover_label}: %{{y:.2f}}<extra></extra>'
                ))
            else:
                # Negative emissions (below x-axis) - dashed line
                fig.add_trace(go.Scatter(
                    x=self.df['X'],
                    y=-data,  # Negate to show below x-axis
                    mode='lines',
                    name=display_name,
                    line=dict(color=color, width=3,
                              # dash='dash'
                              ),
                    hovertemplate=f'<b>{display_name}</b><br>Year: %{{x}}<br>{hover_label}: -%{{y:.2f}}<extra></extra>'
                ))

        # Update layout
        y_axis_title = self._get_y_axis_label()
        if self.bool_accumulated:
            y_axis_title = y_axis_title.replace('Emissions', 'Cumulative Emissions')

        fig.update_layout(
            title=dict(
                text=self.plot_title,
                x=0,
                xanchor='left'
            ),
            xaxis=dict(
                title='Time horizon - Year',
                showgrid=True,
                gridcolor='rgba(200,200,200,0.3)'
            ),
            yaxis=dict(
                title=y_axis_title,
                showgrid=True,
                gridcolor='rgba(200,200,200,0.3)',
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='black',
                rangemode='tozero'
            ),
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation='h',
                yanchor='top',
                y=-0.15,
                xanchor='left',
                x=0
            ),
            margin=dict(l=80, r=80, t=80, b=120)
        )

        return fig

    def _create_line_net_plot(self):
        """
        Create line plot showing net emissions (positive - negative) over time.
        This plot always shows cumulative emissions to track progress toward net-zero.

        Returns:
        --------
        go.Figure: Plotly figure object
        """
        aggregated_data = self.categorize_and_aggregate_emissions()

        # Separate positive and negative emissions
        positive_total = pd.Series(0, index=self.df.index)
        negative_total = pd.Series(0, index=self.df.index)

        for category, info in aggregated_data.items():
            data = info['data']
            if info['positive']:
                positive_total += data
            else:
                negative_total += data

        # Calculate net emissions (positive - negative)
        net_emissions = positive_total - negative_total

        # Apply cumulative sum (line_net always shows cumulative)
        net_emissions_cumulative = net_emissions.cumsum()

        fig = go.Figure()

        # Add net emissions line
        fig.add_trace(go.Scatter(
            x=self.df['X'],
            y=net_emissions_cumulative,
            mode='lines',
            name='Net Emissions',
            line=dict(color=COLOURS_TO_RGB['black'], width=3),
            hovertemplate='<b>Net Emissions</b><br>Year: %{x}<br>Cumulative Net Emission: %{y:.2f}<extra></extra>'
        ))

        # Add vertical line for net-zero target year if configured
        net_zero_target_year = self.config.plots_emission_timeline.net_zero_target_year
        if net_zero_target_year is not None and not self.df.empty:
            # Format the target year to match X-axis format (e.g., Y_2060)
            # Check if X values have Y_ prefix
            first_x = str(self.df['X'].iloc[0])
            if first_x.startswith('Y_'):
                target_year_formatted = f'Y_{net_zero_target_year}'
            else:
                target_year_formatted = net_zero_target_year

            # Get the y-axis range for the vertical line
            # Ensure the line passes through 0 by extending the range if needed
            y_min = min(net_emissions_cumulative.min(), 0)
            y_max = max(net_emissions_cumulative.max(), 0)

            fig.add_trace(go.Scatter(
                x=[target_year_formatted, target_year_formatted],
                y=[y_min, y_max],
                mode='lines',
                name=f'Target Year ({net_zero_target_year})',
                line=dict(color='red', width=2, dash='dot'),
                hovertemplate=f'<b>Net-Zero Target Year: {net_zero_target_year}</b><extra></extra>'
            ))

        # Update layout
        y_axis_title = self._get_y_axis_label()
        y_axis_title = y_axis_title.replace('Emissions', 'Cumulative Net Emissions')

        # Add cumulative suffix to title
        plot_title = self.plot_title
        if 'cumulative' not in plot_title.lower():
            plot_title = plot_title + " (Cumulative)"

        fig.update_layout(
            title=dict(
                text=plot_title,
                x=0,
                xanchor='left'
            ),
            xaxis=dict(
                title='Time horizon - Year',
                showgrid=True,
                gridcolor='rgba(200,200,200,0.3)'
            ),
            yaxis=dict(
                title=y_axis_title,
                showgrid=True,
                gridcolor='rgba(200,200,200,0.3)',
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='black',
                rangemode='tozero'
            ),
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation='h',
                yanchor='top',
                y=-0.15,
                xanchor='left',
                x=0
            ),
            margin=dict(l=80, r=80, t=80, b=120)
        )

        return fig

    def _create_stacked_area_plot(self, percentage=False):
        """
        Create stacked area plot showing emissions over time.

        Parameters:
        -----------
        percentage : bool
            If True, show as percentage (0-100%). If False, show absolute values.
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

        # Separate positive and negative emissions
        positive_data = {}
        negative_data = {}

        for category, info in aggregated_data.items():
            data = info['data']

            # Apply cumulative sum if bool_accumulated is True
            if self.bool_accumulated:
                data = data.cumsum()

            if info['positive']:
                positive_data[category] = data
            else:
                negative_data[category] = data

        # Convert to percentage if requested
        if percentage:
            # Calculate totals for each year
            if positive_data:
                positive_total = pd.DataFrame(positive_data).sum(axis=1)
                for category in positive_data:
                    positive_data[category] = (positive_data[category] / positive_total * 100).fillna(0)

            if negative_data:
                negative_total = pd.DataFrame(negative_data).sum(axis=1)
                for category in negative_data:
                    negative_data[category] = (negative_data[category] / negative_total * 100).fillna(0)

        # Add positive emission traces (stacked)
        for category, data in positive_data.items():
            color = category_colors.get(category, COLOURS_TO_RGB['grey'])
            display_name = 'PV' if category == 'pv' else category.capitalize()

            hover_label = "Percentage" if percentage else ("Cumulative Emission" if self.bool_accumulated else "Emission")
            hover_format = "%{y:.1f}%" if percentage else "%{y:.2f}"

            fig.add_trace(go.Scatter(
                x=self.df['X'],
                y=data,
                mode='lines',
                name=display_name,
                line=dict(width=0),
                fillcolor=color,
                fill='tonexty',
                stackgroup='positive',
                hovertemplate=f'<b>{display_name}</b><br>Year: %{{x}}<br>{hover_label}: {hover_format}<extra></extra>'
            ))

        # Add negative emission traces (stacked below x-axis)
        for category, data in negative_data.items():
            color = category_colors.get(category, COLOURS_TO_RGB['grey'])
            display_name = 'PV' if category == 'pv' else category.capitalize()

            hover_label = "Percentage" if percentage else ("Cumulative Emission" if self.bool_accumulated else "Emission")
            hover_format = "-%{y:.1f}%" if percentage else "-%{y:.2f}"

            fig.add_trace(go.Scatter(
                x=self.df['X'],
                y=-data,  # Negate to show below x-axis
                mode='lines',
                name=display_name,
                line=dict(width=0, dash='dash'),
                fillcolor=color,
                fill='tonexty',
                stackgroup='negative',
                hovertemplate=f'<b>{display_name}</b><br>Year: %{{x}}<br>{hover_label}: {hover_format}<extra></extra>'
            ))

        # Update layout
        if percentage:
            y_axis_title = 'Percentage (%)'
        else:
            y_axis_title = self._get_y_axis_label()
            if self.bool_accumulated:
                y_axis_title = y_axis_title.replace('Emissions', 'Cumulative Emissions')

        # Add cumulative suffix to title
        plot_title = self.plot_title
        if 'cumulative' not in plot_title.lower():
            plot_title = plot_title + " (Cumulative)"

        fig.update_layout(
            title=dict(
                text=plot_title,
                x=0,
                xanchor='left'
            ),
            xaxis=dict(
                title='Time horizon - Year',
                showgrid=True,
                gridcolor='rgba(200,200,200,0.3)'
            ),
            yaxis=dict(
                title=y_axis_title,
                showgrid=True,
                gridcolor='rgba(200,200,200,0.3)',
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='black',
                rangemode='tozero'
            ),
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation='h',
                yanchor='top',
                y=-0.15,
                xanchor='left',
                x=0
            ),
            margin=dict(l=80, r=80, t=80, b=120)
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
            return f'Emissions ({unit}/m2)'
        else:
            return f'Emissions ({unit})'

def plot_emission_timeline(config, context: dict):
    scenario = config.scenario
    plot_cea_feature = 'lifecycle-emissions'
    period_start = context.get('period_start', 0)
    period_end = context.get('period_end', 8759)
    plot_cea_feature_umbrella = context.get('feature', 'emission-timeline')
    bool_accumulated = True
    solar_panel_types_list = []
    plots_building_filter = config.sections["plots-building-filter"]
    plot_config = config.sections[f"plots-{plot_cea_feature_umbrella}"]
    bool_include_advanced_analytics = False
    plot_config.x_to_plot = 'district_and_annually'

    # FIXME: temporary fix for missing x_sorted_by and x_sorted_reversed in plot_config_general
    # use dummy config for plot_config_general
    class DummyConfig:
        def __init__(self):
            self.x_sorted_by = "default"
            self.x_sorted_reversed = False
    plot_config_general = DummyConfig()

    # Activate a_data_loader
    df_summary_data, df_architecture_data, plot_instance = plot_input_processor(plot_config,
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

    # # Add placeholder columns for biogenic and PV if their source columns exist (dummy values)
    # if 'operation_hot_water_kgCO2e/m2' in df_to_plotly.columns:
    #     df_to_plotly['biogenic_underside_kgCO2e/m2'] = df_to_plotly['production_technical_systems_kgCO2e/m2']
    #     list_y_columns.append('biogenic_underside_kgCO2e/m2')
    # if 'operation_electricity_kgCO2e/m2' in df_to_plotly.columns:
    #     df_to_plotly['pv_kgCO2e/m2'] = df_to_plotly['operation_electricity_kgCO2e/m2']
    #     list_y_columns.append('pv_kgCO2e/m2')

    # Create EmissionTimelinePlot instance
    plot_title = "CEA-4 Emission Timeline"
    plot_obj = EmissionTimelinePlot(config, df_to_plotly, list_y_columns, plot_title=plot_title,
                                    bool_accumulated=bool_accumulated,
                                    period_start=period_start, period_end=period_end)

    # Generate the figure
    fig = plot_obj.create_plot()

    return fig


def create_emission_timeline_plot(config):
    import cea.inputlocator

    locator = cea.inputlocator.InputLocator(config.scenario)
    # cache = cea.plots.cache.PlotCache(config.project)
    # cache = cea.plots.cache.NullPlotCache()

    list_buildings = config.plots_building_filter.buildings
    integer_year_start = config.plots_building_filter.filter_buildings_by_year_start
    integer_year_end = config.plots_building_filter.filter_buildings_by_year_end
    list_standard = config.plots_building_filter.filter_buildings_by_construction_type
    list_main_use_type = config.plots_building_filter.filter_buildings_by_use_type
    ratio_main_use_type = config.plots_building_filter.min_ratio_as_main_use
    _, list_buildings = filter_buildings(locator, list_buildings,
                                         integer_year_start, integer_year_end, list_standard,
                                         list_main_use_type, ratio_main_use_type)

    print(f"Filtered buildings list: {list_buildings}")
    print(f"Number of buildings: {len(list_buildings)}")

    context = config.plots_emission_timeline.context

    # Generate emission timeline
    fig = plot_emission_timeline(config, context)

    return fig

def main(config):
    fig = create_emission_timeline_plot(config)
    plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    return plot_html


if __name__ == '__main__':
    fig = create_emission_timeline_plot(cea.config.Configuration())
    fig.show(renderer="browser")

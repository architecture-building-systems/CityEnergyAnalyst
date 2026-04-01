# -*- coding: utf-8 -*-

import os

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
            - emission columns (e.g., 'operation_Qhs_sys_kgCO2e', 'biogenic_wall_ag_kgCO2e', etc.)
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

    def _aggregate_into_9_categories(self):
        """
        Aggregate emission columns into main categories:
        - space_heating (operation_Qhs_sys)
        - space_cooling (operation_Qcs_sys)
        - dhw (operation_Qww_sys)
        - electricity (operation_E_sys)
        - production (all production_*)
        - demolition (all demolition_*)
        - biogenic (all biogenic_*)
        - solar_offset (PV_E_offset_*, PVT_E_offset_*, PVT_Q_offset_*, SC_Q_offset_*)

        Returns:
        --------
        dict: Dictionary with category names as keys and metadata
        """
        categories = {
            'space_heating': {'columns': [], 'positive': True, 'display_name': 'space_heating'},
            'space_cooling': {'columns': [], 'positive': True, 'display_name': 'space_cooling'},
            'DHW': {'columns': [], 'positive': True, 'display_name': 'DHW'},
            'electricity': {'columns': [], 'positive': True, 'display_name': 'electricity'},
            'DH': {'columns': [], 'positive': True, 'display_name': 'DH'},
            'DC': {'columns': [], 'positive': True, 'display_name': 'DC'},
            'production': {'columns': [], 'positive': True, 'display_name': 'production'},
            'demolition': {'columns': [], 'positive': True, 'display_name': 'demolition'},
            'biogenic': {'columns': [], 'positive': False, 'display_name': 'biogenic'},
            'solar_offset': {'columns': [], 'positive': False, 'display_name': 'solar_offset'},
        }

        # Categorize columns
        for col in self.y_columns:
            col_lower = col.lower()

            # Check for specific operation services (including booster columns)
            if 'operation_qhs_sys' in col_lower or 'operation_qhs_booster' in col_lower or 'operation_space_heating' in col_lower:
                categories['space_heating']['columns'].append(col)
            elif 'operation_qcs_sys' in col_lower or 'operation_space_cooling' in col_lower:
                categories['space_cooling']['columns'].append(col)
            elif 'operation_qww_sys' in col_lower or 'operation_qww_booster' in col_lower or 'operation_dhw' in col_lower:
                categories['DHW']['columns'].append(col)
            elif 'operation_e_sys' in col_lower or 'operation_electricity' in col_lower:
                categories['electricity']['columns'].append(col)
            # District plant columns
            elif col_lower == 'operation_dh_kgco2e':
                categories['DH']['columns'].append(col)
            elif col_lower == 'operation_dc_kgco2e':
                categories['DC']['columns'].append(col)
            # Solar offset columns (PV_E_offset, PVT_E_offset, PVT_Q_offset, SC_Q_offset)
            elif col_lower.endswith('_offset_kgco2e') or col_lower.endswith('_offset'):
                categories['solar_offset']['columns'].append(col)
            # Check for lifecycle embodied categories
            elif col_lower.startswith('biogenic'):
                categories['biogenic']['columns'].append(col)
            elif col_lower.startswith('production'):
                categories['production']['columns'].append(col)
            elif col_lower.startswith('demolition'):
                categories['demolition']['columns'].append(col)

        # Aggregate columns within each category
        aggregated_data = {}
        for category, info in categories.items():
            if info['columns']:
                # Sum all columns in this category
                aggregated_data[category] = {
                    'data': self.df[info['columns']].sum(axis=1),
                    'positive': info['positive'],
                    'display_name': info['display_name']
                }

        return aggregated_data

    def categorize_and_aggregate_emissions(self):
        """
        Categorize emission columns and aggregate by category.
        DEPRECATED: Use _aggregate_into_9_categories() instead.

        Returns:
        --------
        dict: Dictionary with category names as keys and aggregated Series as values
              Also includes metadata about whether each category is positive or negative
        """
        categories = {
            'operation': {'columns': [], 'positive': True},
            'production': {'columns': [], 'positive': True},
            'demolition': {'columns': [], 'positive': True},
            'biogenic': {'columns': [], 'positive': False},  # Negative: carbon storage
            'pv': {'columns': [], 'positive': False}  # Negative: PV offset/export
        }

        # Categorize columns
        for col in self.y_columns:
            col_lower = col.lower()
            if col_lower.startswith('biogenic'):
                categories['biogenic']['columns'].append(col)
            elif col_lower.startswith('pv'):
                categories['pv']['columns'].append(col)
            elif col_lower.startswith('operation'):
                categories['operation']['columns'].append(col)
            elif col_lower.startswith('production'):
                categories['production']['columns'].append(col)
            elif col_lower.startswith('demolition'):
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
        Aggregates into 9 main categories with colors matching the bar plots.
        """
        aggregated_data = self._aggregate_into_9_categories()

        # Define colors matching the bar plot scheme
        category_colors = {
            'space_heating': COLOURS_TO_RGB['red'],
            'space_cooling': COLOURS_TO_RGB['blue'],
            'DHW': COLOURS_TO_RGB['orange'],
            'electricity': COLOURS_TO_RGB['green'],
            'DH': COLOURS_TO_RGB['red_light'],
            'DC': COLOURS_TO_RGB['blue_light'],
            'production': COLOURS_TO_RGB['purple'],
            'demolition': COLOURS_TO_RGB['brown'],
            'biogenic': COLOURS_TO_RGB['grey'],
            'solar_offset': COLOURS_TO_RGB['yellow'],
        }

        fig = go.Figure()

        # Add traces for each category
        for category, info in aggregated_data.items():
            color = category_colors.get(category, COLOURS_TO_RGB['grey'])
            display_name = info['display_name']
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
                # Negative emissions (below x-axis)
                fig.add_trace(go.Scatter(
                    x=self.df['X'],
                    y=data,  # Use data as-is (already negative)
                    mode='lines',
                    name=display_name,
                    line=dict(color=color, width=3),
                    hovertemplate=f'<b>{display_name}</b><br>Year: %{{x}}<br>{hover_label}: %{{y:.2f}}<extra></extra>'
                ))

        # Update layout
        y_axis_title = self._get_y_axis_label()
        if self.bool_accumulated:
            y_axis_title = y_axis_title.replace('Emissions', 'Cumulative Emissions')

        # Configure y-axis range and step from config
        yaxis_config = dict(
            title=y_axis_title,
            showgrid=True,
            gridcolor='rgba(200,200,200,0.3)',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='black'
            # Allow negative values to show below x-axis
        )

        # Apply y-axis min/max if specified in config
        y_min = getattr(self.config.plots_emission_timeline, 'y_min', None)
        y_max = getattr(self.config.plots_emission_timeline, 'y_max', None)

        if y_min is not None or y_max is not None:
            yaxis_config['range'] = [y_min, y_max]

        # Apply y-axis step if specified in config
        if hasattr(self.config.plots_emission_timeline, 'y_step') and self.config.plots_emission_timeline.y_step is not None:
            yaxis_config['dtick'] = self.config.plots_emission_timeline.y_step

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
            yaxis=yaxis_config,
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation='h',
                yanchor='top',
                y=-0.2,
                xanchor='left',
                x=0
            ),
            margin=dict(l=80, r=80, t=80, b=200)
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

        # Calculate net emissions (positive + negative, where negative values are already negative)
        net_emissions = positive_total + negative_total

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

        # Configure y-axis range and step from config
        yaxis_config = dict(
            title=y_axis_title,
            showgrid=True,
            gridcolor='rgba(200,200,200,0.3)',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='black'
            # Allow negative values to show below x-axis for net emissions
        )

        # Apply y-axis min/max if specified in config
        y_min = getattr(self.config.plots_emission_timeline, 'y_min', None)
        y_max = getattr(self.config.plots_emission_timeline, 'y_max', None)

        if y_min is not None or y_max is not None:
            yaxis_config['range'] = [y_min, y_max]

        # Apply y-axis step if specified in config
        if hasattr(self.config.plots_emission_timeline, 'y_step') and self.config.plots_emission_timeline.y_step is not None:
            yaxis_config['dtick'] = self.config.plots_emission_timeline.y_step

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
            yaxis=yaxis_config,
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation='h',
                yanchor='top',
                y=-0.2,
                xanchor='left',
                x=0
            ),
            margin=dict(l=80, r=80, t=80, b=200)
        )

        return fig

    def _create_stacked_area_plot(self, percentage=False):
        """
        Create stacked area plot showing emissions over time.
        Aggregates into 9 main categories with colors matching the bar plots.

        Parameters:
        -----------
        percentage : bool
            If True, show as percentage (0-100%). If False, show absolute values.
        """
        aggregated_data = self._aggregate_into_9_categories()

        # Define colors matching the bar plot scheme
        category_colors = {
            'space_heating': COLOURS_TO_RGB['red'],
            'space_cooling': COLOURS_TO_RGB['blue'],
            'DHW': COLOURS_TO_RGB['orange'],
            'electricity': COLOURS_TO_RGB['green'],
            'DH': COLOURS_TO_RGB['red_light'],
            'DC': COLOURS_TO_RGB['blue_light'],
            'production': COLOURS_TO_RGB['purple'],
            'demolition': COLOURS_TO_RGB['brown'],
            'biogenic': COLOURS_TO_RGB['grey'],
            'solar_offset': COLOURS_TO_RGB['yellow'],
        }

        fig = go.Figure()

        # Separate positive and negative emissions by category
        positive_data = {}
        negative_data = {}

        for category, info in aggregated_data.items():
            data = info['data']

            # Apply cumulative sum if bool_accumulated is True
            if self.bool_accumulated:
                data = data.cumsum()

            if info['positive']:
                positive_data[category] = {'data': data, 'display_name': info['display_name']}
            else:
                negative_data[category] = {'data': data, 'display_name': info['display_name']}

        # Convert to percentage if requested
        if percentage:
            # Calculate positive total BEFORE converting to percentages (needed for negative scaling)
            if positive_data:
                positive_total = pd.DataFrame({k: v['data'] for k, v in positive_data.items()}).sum(axis=1)

            # Convert positive data to percentages (0-100%)
            if positive_data:
                for category in positive_data:
                    positive_data[category]['data'] = (positive_data[category]['data'] / positive_total * 100).fillna(0)

            # Scale negative values proportionate to positive values (not 0 to -100%)
            # E.g., if positive=100, negative=-30, then negative shows as -30% (30% of positive)
            if negative_data and positive_data:
                for category in negative_data:
                    negative_data[category]['data'] = (negative_data[category]['data'] / positive_total * 100).fillna(0)

        # Add positive emission traces (stacked)
        for category, info in positive_data.items():
            color = category_colors.get(category, COLOURS_TO_RGB['grey'])
            display_name = info['display_name']
            data = info['data']

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
        for category, info in negative_data.items():
            color = category_colors.get(category, COLOURS_TO_RGB['grey'])
            display_name = info['display_name']
            data = info['data']

            hover_label = "Percentage" if percentage else ("Cumulative Emission" if self.bool_accumulated else "Emission")

            # Data is already negative (either from source or from abs() division above)
            # Use as-is to show below x-axis
            y_data = data
            hover_format = "%{y:.1f}%" if percentage else "%{y:.2f}"

            fig.add_trace(go.Scatter(
                x=self.df['X'],
                y=y_data,
                mode='lines',
                name=display_name,
                line=dict(width=0),
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

        # Configure y-axis range and step from config
        yaxis_config = dict(
            title=y_axis_title,
            showgrid=True,
            gridcolor='rgba(200,200,200,0.3)',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='black'
            # Allow negative values to show below x-axis with stackgroup='negative'
        )

        # Apply y-axis min/max if specified in config
        y_min = getattr(self.config.plots_emission_timeline, 'y_min', None)
        y_max = getattr(self.config.plots_emission_timeline, 'y_max', None)

        if y_min is not None or y_max is not None:
            yaxis_config['range'] = [y_min, y_max]

        # Apply y-axis step if specified in config
        if hasattr(self.config.plots_emission_timeline, 'y_step') and self.config.plots_emission_timeline.y_step is not None:
            yaxis_config['dtick'] = self.config.plots_emission_timeline.y_step

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
            yaxis=yaxis_config,
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation='h',
                yanchor='top',
                y=-0.2,
                xanchor='left',
                x=0
            ),
            margin=dict(l=80, r=80, t=80, b=200)
        )

        return fig

    def _get_display_name(self, column_name):
        """
        Convert column name to display name.
        Removes unit suffixes and formats for readability.

        Parameters:
        -----------
        column_name : str
            Column name with unit (e.g., `operation_Qhs_sys_kgCO2e`)

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

def _load_whatif_timeline_df(locator, whatif_names):
    """
    Load and aggregate the district-level emission timeline from what-if results.

    Returns a DataFrame with:
    - 'X': year values
    - emission columns with _kgCO2e suffix (operation_Qhs_sys_kgCO2e, production_kgCO2e, etc.)
    """
    dfs = []
    for whatif_name in whatif_names:
        timeline_path = locator.get_emissions_whatif_timeline_file(whatif_name)
        if not os.path.exists(timeline_path):
            print(f"Warning: timeline file not found for what-if '{whatif_name}': {timeline_path}")
            continue
        df = pd.read_csv(timeline_path)
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    # Sum across multiple what-if scenarios (numeric columns only)
    if len(dfs) == 1:
        combined = dfs[0]
    else:
        numeric_cols = dfs[0].select_dtypes(include='number').columns.tolist()
        non_numeric = [c for c in dfs[0].columns if c not in numeric_cols]
        combined = dfs[0].copy()
        for df in dfs[1:]:
            combined[numeric_cols] = combined[numeric_cols].add(df[numeric_cols].fillna(0), fill_value=0)

    # Detect year column (the timeline index is named 'period' with values like 'Y_2024')
    year_col = None
    for candidate in ('period', 'year', 'Year', 'Y', 'index'):
        if candidate in combined.columns:
            year_col = candidate
            break

    if year_col is None and combined.index.name:
        combined = combined.reset_index()
        year_col = combined.columns[0]
    elif year_col is None:
        combined = combined.reset_index()
        year_col = combined.columns[0]

    combined = combined.rename(columns={year_col: 'X'})
    return combined


def _get_timeline_y_columns(df, operation_services, y_categories):
    """Detect which timeline columns match the requested services and categories."""
    service_to_tech = {
        'electricity': ['operation_E_sys'],
        'space_heating': ['operation_Qhs_sys', 'operation_Qhs_booster'],
        'space_cooling': ['operation_Qcs_sys'],
        'DHW': ['operation_Qww_sys', 'operation_Qww_booster'],
    }
    solar_to_col = {
        'PV_E': 'PV_E_offset',
        'PVT_E': 'PVT_E_offset',
        'PVT_Q': 'PVT_Q_offset',
        'SC_Q': 'SC_Q_offset',
    }

    wanted = []
    if 'operation' in y_categories:
        for service in operation_services:
            if service in service_to_tech:
                for base in service_to_tech[service]:
                    col = next((c for c in df.columns if c.startswith(base)), None)
                    if col:
                        wanted.append(col)
        # Always include plant (DH/DC) operation columns if present
        for col in df.columns:
            if col in ('operation_DH_kgCO2e', 'operation_DC_kgCO2e'):
                if col not in wanted:
                    wanted.append(col)
        # Always include all solar offset columns that exist in the timeline (regardless of
        # which solar services the user has ticked — they come from what-if emissions results)
        for col in df.columns:
            if col.endswith('_offset_kgCO2e') or col.endswith('_offset'):
                if col not in wanted:
                    wanted.append(col)

    for category in ('production', 'demolition', 'biogenic'):
        if category in y_categories:
            cols = [c for c in df.columns if c.startswith(f'{category}_')]
            wanted.extend(cols)

    return wanted


def plot_emission_timeline_single(config, context: dict, whatif_name: str):
    """Generate a single emission timeline figure for one what-if scenario."""
    import cea.inputlocator

    scenario = config.scenario
    plot_cea_feature_umbrella = context.get('feature', 'emission-timeline')
    period_start = context.get('period_start', None)
    period_end = context.get('period_end', None)
    bool_accumulated = True
    plot_config = config.sections[f"plots-{plot_cea_feature_umbrella}"]

    locator = cea.inputlocator.InputLocator(scenario)
    df_to_plotly = _load_whatif_timeline_df(locator, [whatif_name])

    if df_to_plotly.empty:
        import plotly.graph_objs as go
        return go.Figure()

    operation_services = getattr(plot_config, 'operation_services', [])
    y_categories = getattr(plot_config, 'y_category_to_plot', ['operation', 'production', 'demolition', 'biogenic'])
    list_y_columns = _get_timeline_y_columns(df_to_plotly, operation_services, y_categories)

    plot_title = f"Emission Timeline \u2014 {whatif_name}"
    plot_obj = EmissionTimelinePlot(config, df_to_plotly, list_y_columns, plot_title=plot_title,
                                    bool_accumulated=bool_accumulated,
                                    period_start=period_start, period_end=period_end)
    return plot_obj.create_plot()


def plot_emission_timeline(config, context: dict):
    """Generate emission timeline figure(s). Aggregates all what-if scenarios into one plot."""
    import cea.inputlocator

    scenario = config.scenario
    plot_cea_feature_umbrella = context.get('feature', 'emission-timeline')
    period_start = context.get('period_start', None)
    period_end = context.get('period_end', None)
    bool_accumulated = True
    plot_config = config.sections[f"plots-{plot_cea_feature_umbrella}"]

    whatif_names = getattr(plot_config, 'what_if_name', [])
    if isinstance(whatif_names, str):
        whatif_names = [whatif_names] if whatif_names else []

    if whatif_names:
        locator = cea.inputlocator.InputLocator(scenario)
        df_to_plotly = _load_whatif_timeline_df(locator, whatif_names)

        if df_to_plotly.empty:
            import plotly.graph_objs as go
            return go.Figure()

        operation_services = getattr(plot_config, 'operation_services', [])
        y_categories = getattr(plot_config, 'y_category_to_plot', ['operation', 'production', 'demolition', 'biogenic'])
        list_y_columns = _get_timeline_y_columns(df_to_plotly, operation_services, y_categories)

    else:
        # Legacy path: use process_building_summary pipeline
        plot_cea_feature = 'lifecycle-emissions'
        solar_panel_types_list = []
        plots_building_filter = config.sections["plots-building-filter"]
        bool_include_advanced_analytics = False
        plot_config.x_to_plot = 'district_and_annually'

        class DummyConfig:
            def __init__(self):
                self.x_sorted_by = "default"
                self.x_sorted_reversed = False
        plot_config_general = DummyConfig()

        df_summary_data, df_architecture_data, plot_instance = plot_input_processor(
            plot_config, plots_building_filter, scenario, plot_cea_feature,
            period_start or 0, period_end or 8759, solar_panel_types_list,
            bool_include_advanced_analytics
        )

        df_to_plotly, list_y_columns = calc_x_y_metric(
            plot_config, plot_config_general, plots_building_filter,
            plot_instance, plot_cea_feature, df_summary_data, df_architecture_data,
            solar_panel_types_list, scenario
        )

    plot_title = "CEA-4 Emission Timeline"
    plot_obj = EmissionTimelinePlot(config, df_to_plotly, list_y_columns, plot_title=plot_title,
                                    bool_accumulated=bool_accumulated,
                                    period_start=period_start, period_end=period_end)
    return plot_obj.create_plot()


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
    plot_config = config.plots_emission_timeline
    whatif_names = getattr(plot_config, 'what_if_name', [])
    if isinstance(whatif_names, str):
        whatif_names = [whatif_names] if whatif_names else []

    # Single what-if or legacy: return one figure
    if len(whatif_names) <= 1:
        fig = create_emission_timeline_plot(config)
        fig.update_layout(autosize=True)
        html = fig.to_html(full_html=True, include_plotlyjs='cdn', config={'responsive': True})
        return html.replace('<head>', '<head><style>html,body{height:100%;margin:0}</style>', 1)

    # Multi what-if: one figure per scenario with aligned y-axes
    slots = []
    for whatif_name in whatif_names:
        try:
            context = plot_config.context
            context['feature'] = 'emission-timeline'
            fig = plot_emission_timeline_single(config, context, whatif_name)
            slots.append(('ok', whatif_name, fig))
        except Exception as e:
            slots.append(('err', whatif_name, (
                f'<div style="padding:20px;border:2px solid #ff6b6b;border-radius:5px;'
                f'background:#ffe0e0;margin:12px 0">'
                f'<h3>Error plotting <em>{whatif_name}</em></h3>'
                f'<code>{e}</code></div>'
            )))

    # Align y-axes across all figures
    global_y_min = global_y_max = None
    y_min_cfg = getattr(plot_config, 'y_min', None)
    y_max_cfg = getattr(plot_config, 'y_max', None)
    if y_min_cfg is None and y_max_cfg is None:
        for kind, _, fig in slots:
            if kind != 'ok':
                continue
            for trace in fig.data:
                if hasattr(trace, 'y') and trace.y is not None and len(trace.y) > 0:
                    t_min, t_max = min(trace.y), max(trace.y)
                    if global_y_min is None or t_min < global_y_min:
                        global_y_min = t_min
                    if global_y_max is None or t_max > global_y_max:
                        global_y_max = t_max

    html_outputs = []
    plotly_included = False
    for slot in slots:
        if slot[0] == 'err':
            html_outputs.append(slot[2])
            continue
        _, whatif_name, fig = slot
        if global_y_min is not None:
            margin = (global_y_max - global_y_min) * 0.05
            fig.update_yaxes(range=[global_y_min - margin, global_y_max + margin])
        fig.update_layout(autosize=False, height=700, width=960)
        include_js = 'cdn' if not plotly_included else False
        plotly_included = True
        html_outputs.append(fig.to_html(full_html=False, include_plotlyjs=include_js,
                                        config={'responsive': False}))

    body = '\n'.join(html_outputs)
    return (
        '<!DOCTYPE html><html>'
        '<head><meta charset="utf-8"></head>'
        f'<body style="margin:0;overflow:auto">{body}</body></html>'
    )


if __name__ == '__main__':
    fig = create_emission_timeline_plot(cea.config.Configuration())
    fig.show(renderer="browser")

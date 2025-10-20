"""
PlotManager – Generates the Plotly graph

"""

from cea.visualisation.format.plot_colours import COLOURS_TO_RGB, get_column_color
from cea.visualisation.b_data_processor import x_to_plot_building
from cea.import_export.result_summary import month_names, season_names
from math import ceil
import plotly.graph_objects as go
from plotly.subplots import make_subplots


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def get_display_name_for_column(column_name, y_metric_to_plot):
    """
    Map a processed column name back to its user-friendly display name.
    
    For solar features, columns like 'PV_roofs_top_E_kWh/m2' should map to 'roof',
    'PVT_ET_roofs_top_E_kWh/m2' should map to 'roof (electricity)', etc.
    
    Parameters:
    - column_name (str): The processed column name (e.g., 'PV_roofs_top_E_kWh/m2')
    - y_metric_to_plot (list): List of user-friendly names (e.g., ['roof', 'wall_north'])
    
    Returns:
    - str: The user-friendly display name or the column name if no mapping found
    """
    if not isinstance(y_metric_to_plot, list):
        return column_name
    
    # Area columns should not appear in plots, but if they do, make them distinct
    if column_name.endswith('_m2'):
        return f"{column_name} (Area)"
    
    # Solar surface mapping
    surface_mappings = {
        'roofs_top': 'roofs_top',
        'walls_north': 'walls_north',
        'walls_east': 'walls_east',
        'walls_south': 'walls_south',
        'walls_west': 'walls_west',
        'total': 'total'
    }
    
    # Check each surface mapping
    for col_pattern, user_name in surface_mappings.items():
        if col_pattern in column_name and user_name in y_metric_to_plot:
            # For PVT columns, distinguish between electricity (E) and heat (Q)
            if 'PVT' in column_name:
                if '_E_' in column_name:
                    return f"{user_name} (electricity)"
                elif '_Q_' in column_name:
                    return f"{user_name} (heat)"
            # For SC (solar collector) columns, only heat
            elif 'SC' in column_name and '_Q_' in column_name:
                return f"{user_name} (heat)"
            # For PV columns, only electricity (default behavior)
            return user_name
    
    # Fallback to column name if no mapping found
    return column_name


class bar_plot:
    """Generates a Plotly bar plot from processed data."""

    def __init__(self, plot_config, plot_config_general, dataframe, list_y_columns, plot_cea_feature, solar_panel_types_list, hide_title=False):

        # Get the dataframe prepared by the data processor, including Y(s), X, and X_facet
        self.df = dataframe
        self.plot_cea_feature = plot_cea_feature
        self.hide_title = hide_title

        # Get the settings for the format
        self.plot_title = plot_config_general.plot_title
        self.y_metric_to_plot = plot_config.y_metric_to_plot
        self.y_columns = list_y_columns
        self.y_metric_unit = plot_config.y_metric_unit
        self.y_normalised_by = plot_config.y_normalised_by
        self.y_min = plot_config_general.y_min
        self.y_max = plot_config_general.y_max
        self.y_step = plot_config_general.y_step
        self.y_label = plot_config_general.y_label
        self.x_to_plot = plot_config.x_to_plot
        self.facet_by_numbers_wrapped = plot_config_general.facet_by_numbers_wrapped
        self.facet_by_rows = plot_config_general.facet_by_rows
        self.x_sorted_by = plot_config_general.x_sorted_by
        self.x_sorted_reversed = plot_config_general.x_sorted_reversed
        self.x_label = plot_config_general.x_label

        if plot_cea_feature in ('pv', 'sc'):
            self.appendix = f"{solar_panel_types_list[0]}"
        elif plot_cea_feature == 'pvt':
            if len(solar_panel_types_list) == 2:
                self.appendix = f"{solar_panel_types_list[0]}_{solar_panel_types_list[1]}"
            else:
                raise ValueError("PVT requires two solar panel types.")
        else:
            self.appendix = plot_cea_feature

        # Parse plot_type and plot_mode
        self.plot_type, self.y_barmode = parse_plot_type(plot_config_general.plot_type)

        # Update y_columns based on if normalisation is selected
        # Note: Column names are already updated during unit conversion in data processor
        self.y_columns_normalised = list_y_columns

    def generate_fig(self):
        """Creates a Plotly figure."""

        # Process the data if 100% stacked bar chart is selected
        if self.y_barmode == 'stack_percentage':
            df = convert_to_percent_stacked(self.df, self.y_columns_normalised)
        else:
            df = self.df

        # Create bar chart
        fig = plot_faceted_bars(df, x_col='X', facet_col='X_facet', value_columns=self.y_columns_normalised,
                                y_metric_to_plot=self.y_metric_to_plot, bool_use_rows=self.facet_by_rows,
                                number_of_rows_or_columns=self.facet_by_numbers_wrapped,
                                y_max=self.y_max, y_min=self.y_min, y_step=self.y_step, barmode=self.y_barmode)

        # Position legend below
        fig = position_legend_between_title_and_graph(fig, self.plot_cea_feature)

        return fig

    def fig_format(self, fig, plot_cea_feature):
        # Set the title
        if self.plot_title:
            title = self.plot_title
        else:
            if plot_cea_feature == 'demand':
                title = "CEA-4 Building Energy Demand"
            elif plot_cea_feature == 'pv':
                title = "CEA-4 Photovoltaic (PV) Panels: {panel_type}".format(panel_type=self.appendix)
            elif plot_cea_feature == 'pvt':
                title = "CEA-4 Photovoltaic-Thermal (PVT) Panels: {panel_type}".format(panel_type=self.appendix)
            elif plot_cea_feature == 'sc':
                title = "CEA-4 Solar Collectors (SC): {panel_type}".format(panel_type=self.appendix)
            elif plot_cea_feature == 'lifecycle-emissions':
                title = "CEA-4 Lifecycle Emissions"
            elif plot_cea_feature == 'operational-emissions':
                title = "CEA-4 Operational Emissions"
            else:
                raise ValueError(f"Invalid plot_cea_feature: {plot_cea_feature}. Please add the title mapping.")

        # Set the y-axis label
        if self.y_label:
            y_label = self.y_label
        elif self.y_barmode == 'stack_percentage':
            y_label = "Percentage (%)"
        else:
            if plot_cea_feature == 'demand':
                if self.y_metric_unit == 'MWh' and self.y_normalised_by == 'no_normalisation':
                    y_label = "Energy Demand (MWh/yr)"
                elif self.y_metric_unit == 'MWh' and self.y_normalised_by != 'no_normalisation':
                    y_label = "Energy Use Intensity (MWh/yr/m2)"
                elif self.y_metric_unit == 'kWh' and self.y_normalised_by == 'no_normalisation':
                    y_label = "Energy Demand (kWh/yr)"
                elif self.y_metric_unit == 'kWh' and self.y_normalised_by != 'no_normalisation':
                    y_label = "Energy Use Intensity (kWh/yr/m2)"
                elif self.y_metric_unit == 'Wh' and self.y_normalised_by == 'no_normalisation':
                    y_label = "Energy Demand (Wh/yr)"
                elif self.y_metric_unit == 'Wh' and self.y_normalised_by != 'no_normalisation':
                    y_label = "Energy Use Intensity (Wh/yr/m2)"
                else:
                    raise ValueError(f"Invalid y-metric-unit: {self.y_metric_unit}")

            elif plot_cea_feature == 'pv':
                if self.y_metric_unit == 'MWh' and self.y_normalised_by == 'no_normalisation':
                    y_label = "PV Electricity Yield (MWh/yr)"
                elif self.y_metric_unit == 'MWh' and self.y_normalised_by == 'gross_floor_area':
                    y_label = "PV Electricity Yield per Gross Floor Area (MWh/yr/m2)"
                elif self.y_metric_unit == 'MWh' and self.y_normalised_by == 'solar_technology_area_installed_for_respective_surface':
                    y_label = "PV Electricity Yield per Installed Area (MWh/yr/m2)"
                elif self.y_metric_unit == 'kWh' and self.y_normalised_by == 'no_normalisation':
                    y_label = "PV Electricity Yield (kWh/yr)"
                elif self.y_metric_unit == 'kWh' and self.y_normalised_by == 'gross_floor_area':
                    y_label = "PV Electricity Yield per Gross Floor Area (kWh/yr/m2)"
                elif self.y_metric_unit == 'kWh' and self.y_normalised_by == 'solar_technology_area_installed_for_respective_surface':
                    y_label = "PV Electricity Yield per Installed Area (kWh/yr/m2)"
                elif self.y_metric_unit == 'Wh' and self.y_normalised_by == 'no_normalisation':
                    y_label = "PV Electricity Yield (Wh/yr)"
                elif self.y_metric_unit == 'Wh' and self.y_normalised_by == 'gross_floor_area':
                    y_label = "PV Electricity Yield per Gross Floor Area (Wh/yr/m2)"
                elif self.y_metric_unit == 'Wh' and self.y_normalised_by == 'solar_technology_area_installed_for_respective_surface':
                    y_label = "PV Electricity Yield per Installed Area (Wh/yr/m2)"
                else:
                    raise ValueError(f"Invalid y-metric-unit: {self.y_metric_unit}")

            elif plot_cea_feature == 'pvt':
                if self.y_metric_unit == 'MWh' and self.y_normalised_by == 'no_normalisation':
                    y_label = "PVT Electricity & Heat Yield (MWh/yr)"
                elif self.y_metric_unit == 'MWh' and self.y_normalised_by == 'gross_floor_area':
                    y_label = "PVT Electricity & Heat Yield per Gross Floor Area (MWh/yr/m2)"
                elif self.y_metric_unit == 'MWh' and self.y_normalised_by == 'solar_technology_area_installed_for_respective_surface':
                    y_label = "PVT Electricity & Heat Yield per Installed Area (MWh/yr/m2)"
                elif self.y_metric_unit == 'kWh' and self.y_normalised_by == 'no_normalisation':
                    y_label = "PVT Electricity & Heat Yield (kWh/yr)"
                elif self.y_metric_unit == 'kWh' and self.y_normalised_by == 'gross_floor_area':
                    y_label = "PVT Electricity & Heat Yield per Gross Floor Area (kWh/yr/m2)"
                elif self.y_metric_unit == 'kWh' and self.y_normalised_by == 'solar_technology_area_installed_for_respective_surface':
                    y_label = "PVT Electricity & Heat Yield per Installed Area (kWh/yr/m2)"
                elif self.y_metric_unit == 'Wh' and self.y_normalised_by == 'no_normalisation':
                    y_label = "PVT Electricity & Heat Yield (Wh/yr)"
                elif self.y_metric_unit == 'Wh' and self.y_normalised_by == 'gross_floor_area':
                    y_label = "PVT Electricity & Heat Yield per Gross Floor Area (Wh/yr/m2)"
                elif self.y_metric_unit == 'Wh' and self.y_normalised_by == 'solar_technology_area_installed_for_respective_surface':
                    y_label = "PVT Electricity & Heat Yield per Installed Area (Wh/yr/m2)"
                else:
                    raise ValueError(f"Invalid y-metric-unit: {self.y_metric_unit}")

            elif plot_cea_feature == 'sc':
                if self.y_metric_unit == 'MWh' and self.y_normalised_by == 'no_normalisation':
                    y_label = "SC Heat Yield (MWh/yr)"
                elif self.y_metric_unit == 'MWh' and self.y_normalised_by == 'gross_floor_area':
                    y_label = "SC Heat Yield per Gross Floor Area (MWh/yr/m2)"
                elif self.y_metric_unit == 'MWh' and self.y_normalised_by == 'solar_technology_area_installed_for_respective_surface':
                    y_label = "SC Heat Yield per Installed Area (MWh/yr/m2)"
                elif self.y_metric_unit == 'kWh' and self.y_normalised_by == 'no_normalisation':
                    y_label = "SC Heat Yield (kWh/yr)"
                elif self.y_metric_unit == 'kWh' and self.y_normalised_by == 'gross_floor_area':
                    y_label = "SC Heat Yield per Gross Floor Area (kWh/yr/m2)"
                elif self.y_metric_unit == 'kWh' and self.y_normalised_by == 'solar_technology_area_installed_for_respective_surface':
                    y_label = "SC Heat Yield per Installed Area (kWh/yr/m2)"
                elif self.y_metric_unit == 'Wh' and self.y_normalised_by == 'no_normalisation':
                    y_label = "SC Heat Yield (Wh/yr)"
                elif self.y_metric_unit == 'Wh' and self.y_normalised_by == 'gross_floor_area':
                    y_label = "SC Heat Yield per Gross Floor Area (Wh/yr/m2)"
                elif self.y_metric_unit == 'Wh' and self.y_normalised_by == 'solar_technology_area_installed_for_respective_surface':
                    y_label = "SC Heat Yield per Installed Area (Wh/yr/m2)"
                else:
                    raise ValueError(f"Invalid y-metric-unit: {self.y_metric_unit}")
            
            elif plot_cea_feature == 'lifecycle-emissions':
                if self.y_metric_unit == 'tonCO2e' and self.y_normalised_by == 'no_normalisation':
                    y_label = "Lifecycle Emissions (tonnes CO2e/yr)"
                elif self.y_metric_unit == 'tonCO2e' and self.y_normalised_by == 'conditioned_floor_area':
                    y_label = "Lifecycle Emissions per Conditioned Floor Area (tonnes CO2e/yr/m2)"
                elif self.y_metric_unit == 'tonCO2e' and self.y_normalised_by == 'gross_floor_area':
                    y_label = "Lifecycle Emissions per Gross Floor Area (tonnes CO2e/yr/m2)"
                elif self.y_metric_unit == 'kgCO2e' and self.y_normalised_by == 'conditioned_floor_area':
                    y_label = "Lifecycle Emissions per Conditioned Floor Area (kg CO2e/yr/m2)"
                elif self.y_metric_unit == 'kgCO2e' and self.y_normalised_by == 'no_normalisation':
                    y_label = "Lifecycle Emissions (kg CO2e/yr)"
                elif self.y_metric_unit == 'kgCO2e' and self.y_normalised_by == 'gross_floor_area':
                    y_label = "Lifecycle Emissions per Gross Floor Area (kg CO2e/yr/m2)"
                elif self.y_metric_unit == 'gCO2e' and self.y_normalised_by == 'conditioned_floor_area':
                    y_label = "Lifecycle Emissions per Conditioned Floor Area (g CO2e/yr/m2)"
                elif self.y_metric_unit == 'gCO2e' and self.y_normalised_by == 'no_normalisation':
                    y_label = "Lifecycle Emissions (g CO2e/yr)"
                elif self.y_metric_unit == 'gCO2e' and self.y_normalised_by == 'gross_floor_area':
                    y_label = "Lifecycle Emissions per Gross Floor Area (g CO2e/yr/m2)"
                else:
                    raise ValueError(f"Invalid y-metric-unit: {self.y_metric_unit}")
            
            elif plot_cea_feature == 'operational-emissions':
                if self.y_metric_unit == 'tonCO2e' and self.y_normalised_by == 'no_normalisation':
                    y_label = "Operational Emissions (tonnes CO2e/yr)"
                elif self.y_metric_unit == 'tonCO2e' and self.y_normalised_by == 'conditioned_floor_area':
                    y_label = "Operational Emissions per Conditioned Floor Area (tonnes CO2e/yr/m2)"
                elif self.y_metric_unit == 'tonCO2e' and self.y_normalised_by == 'gross_floor_area':
                    y_label = "Operational Emissions per Gross Floor Area (tonnes CO2e/yr/m2)"
                elif self.y_metric_unit == 'kgCO2e' and self.y_normalised_by == 'conditioned_floor_area':
                    y_label = "Operational Emissions per Conditioned Floor Area (kg CO2e/yr/m2)"
                elif self.y_metric_unit == 'kgCO2e' and self.y_normalised_by == 'no_normalisation':
                    y_label = "Operational Emissions (kg CO2e/yr)"
                elif self.y_metric_unit == 'kgCO2e' and self.y_normalised_by == 'gross_floor_area':
                    y_label = "Operational Emissions per Gross Floor Area (kg CO2e/yr/m2)"
                elif self.y_metric_unit == 'gCO2e' and self.y_normalised_by == 'conditioned_floor_area':
                    y_label = "Operational Emissions per Conditioned Floor Area (g CO2e/yr/m2)"
                elif self.y_metric_unit == 'gCO2e' and self.y_normalised_by == 'no_normalisation':
                    y_label = "Operational Emissions (g CO2e/yr)"
                elif self.y_metric_unit == 'gCO2e' and self.y_normalised_by == 'gross_floor_area':
                    y_label = "Operational Emissions per Gross Floor Area (g CO2e/yr/m2)"
                else:
                    raise ValueError(f"Invalid y-metric-unit: {self.y_metric_unit}")
            
            else:
                raise ValueError(f"Invalid plot_cea_feature: {plot_cea_feature}. Please add the y_label mapping.")

        # Set the x-axis label
        if self.x_label:
            x_label = self.x_label
        else:
            if self.x_to_plot == 'building':
                x_label = "Buildings"
            elif self.x_to_plot == 'building_faceted_by_months':
                x_label = "Buildings"
            elif self.x_to_plot == 'building_faceted_by_seasons':
                x_label = "Buildings"
            elif self.x_to_plot == 'building_faceted_by_construction_type':
                x_label = "Buildings"
            elif self.x_to_plot == 'building_faceted_by_main_use_type':
                x_label = "Buildings"
            elif self.x_to_plot == 'district_and_hourly':
                x_label = "Hours"
            elif self.x_to_plot == 'district_and_hourly_faceted_by_months':
                x_label = "Hours"
            elif self.x_to_plot == 'district_and_hourly_faceted_by_seasons':
                x_label = "Hours"
            elif self.x_to_plot == 'district_and_daily':
                x_label = "Days"
            elif self.x_to_plot == 'district_and_daily_faceted_by_months':
                x_label = "Days"
            elif self.x_to_plot == 'district_and_daily_faceted_by_seasons':
                x_label = "Days"
            elif self.x_to_plot == 'district_and_monthly':
                x_label = "Months"
            elif self.x_to_plot == 'district_and_monthly_faceted_by_seasons':
                x_label = "Months"
            elif self.x_to_plot == 'district_and_seasonally':
                x_label = "Seasons"
            elif self.x_to_plot == 'district_and_annually_or_selected_period':
                x_label = "Selected period"
            elif self.x_to_plot == 'district_and_annually':
                x_label = "Timeline"
            else:
                raise ValueError(f"Invalid x-to-plot: {self.x_to_plot}")

        if self.y_barmode == 'stack_percentage':
            barmode = 'stack'
        else:
            barmode = self.y_barmode

        # About title and bar mode - hide title if requested
        if not self.hide_title:
            if self.x_to_plot in x_to_plot_building and not self.x_sorted_reversed:
                title = f"<b>{y_label} by {x_label}, sorted by {self.x_sorted_by} (low to high)</b><br><sub>{title}</sub>"
            elif self.x_to_plot in x_to_plot_building and self.x_sorted_reversed:
                title = f"<b>{y_label} by {x_label}, sorted by {self.x_sorted_by} (high to low)</b><br><sub>{title}</sub>"
            else:
                title = f"<b>{y_label} by {x_label}</b><br><sub>{title}</sub>"
            fig.update_layout(
                title=dict(
                    text=title,
                    x=0,
                    y=0.98,
                    xanchor='left',
                    yanchor='top',
                    font=dict(size=20)  # Optional: adjust size, color, etc.
                ),
                barmode=barmode
            )
        else:
            # Hide title but keep barmode
            fig.update_layout(barmode=barmode)

        # About background color and dimensions
        fig.update_layout(
            plot_bgcolor=COLOURS_TO_RGB.get('background_grey'),       # Inside the plotting area
            paper_bgcolor="white",      # Entire figure background (including margins)
            width=1000,  # Set plot width in pixels
            height=600,  # Set plot height in pixels
        )

        # About the grid color and bar gaps
        if "hourly" in self.x_to_plot:
            fig.update_xaxes(
                showgrid=False,
            )
            fig.update_xaxes(
                type="category",
                # Reduce the number of tick labels for better readability
                tickmode='linear',
                dtick=168,  # Show every 7 days (168 hours) for weekly ticks
                tickangle=45
            )
            # Remove gaps completely for hourly plots (narrow bars)
            fig.update_layout(bargap=0.0, bargroupgap=0.0)
        elif "daily" in self.x_to_plot:
            fig.update_xaxes(
                gridcolor="white",
                gridwidth=1.5,    # Grid line color
                tickson='boundaries',
            )
            # Remove gaps completely for daily plots (narrow bars)
            fig.update_layout(bargap=0.0, bargroupgap=0.0)
        else:
            fig.update_xaxes(
                gridcolor="white",
                gridwidth=2.5,    # Grid line color
                tickson='boundaries',
            )
            # Set appropriate gaps for building plots (wider bars with spacing)
            fig.update_layout(bargap=0.2, bargroupgap=0.1)

        fig.update_yaxes(
            gridcolor="white",
            gridwidth=1.2,
        )

        return fig


def position_legend_between_title_and_graph(fig, plot_cea_feature=None):
    """
    Position legend below the graph.

    Parameters:
    - fig: plotly.graph_objects.Figure
    - plot_cea_feature: str, the CEA feature being plotted (unused, kept for compatibility)
    """

    # Standard horizontal legend below the graph
    fig.update_layout(
        legend=dict(
            orientation='h',
            yanchor="top",
            y=-0.15,  # Position legend below the graph
            xanchor="left",
            x=0
        )
    )

    return fig


def convert_to_percent_stacked(df, list_y_columns):
    """
    Converts selected columns of a DataFrame to row-wise percentages for 100% stacked bar chart.

    Parameters:
        df (pd.DataFrame): Input DataFrame with numeric values.
        list_y_columns (list of str): Columns to convert to percentage (must exist in df).

    Returns:
        pd.DataFrame: DataFrame with same columns where list_y_columns are converted to percentages.
    """
    df_percent = df.copy()
    row_sums = df_percent[list_y_columns].sum(axis=1)
    df_percent[list_y_columns] = df_percent[list_y_columns].div(row_sums, axis=0) * 100
    return df_percent


def plot_faceted_bars(
    df,
    x_col,
    facet_col,
    value_columns,
    y_metric_to_plot,
    bool_use_rows=False,
    number_of_rows_or_columns=None,
    y_min=None,
    y_max=None,
    y_step=None,
    barmode="group"):

    season_display_names = {
        'Spring': "<b>Spring</b> (Mar - May)",
        'Summer': "<b>Summer</b> (Jun - Aug)",
        'Autumn': "<b>Autumn</b> (Sep - Nov)",
        'Winter': "<b>Winter</b> (Dec - Feb)"
    }

    month_order = {month: i for i, month in enumerate(month_names)}
    is_faceted = facet_col is not None and facet_col in df.columns

    if is_faceted:
        raw_facets = df[facet_col].unique()

        # Apply ordered facet list
        if all(f in month_names for f in raw_facets):
            facets = [f for f in month_names if f in raw_facets]
        elif all(f in season_names for f in raw_facets):
            facets = [f for f in season_names if f in raw_facets]
        else:
            facets = list(raw_facets)

        num_facets = len(facets)

        if number_of_rows_or_columns is None:
            number_of_rows_or_columns = 4 if num_facets > 1 else 1

        if bool_use_rows:
            rows = number_of_rows_or_columns
            cols = ceil(num_facets / rows)
        else:
            cols = number_of_rows_or_columns
            rows = ceil(num_facets / cols)

        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=[""] * num_facets,
            shared_yaxes=True,
            horizontal_spacing=0.01,
            vertical_spacing=0.18  # Increased from 0.125 to prevent overlap between rows
        )

        for i, facet in enumerate(facets):
            row = (i // cols) + 1
            col = (i % cols) + 1
            facet_df = df[df[facet_col] == facet].copy()

            # Sort x-axis values inside each facet
            if df[x_col].str.startswith("hour_").any():
                facet_df["__sort"] = facet_df[x_col].str.extract(r"hour_(\d+)").astype(int)
                if facet == "Winter":
                    facet_df["__sort"] = facet_df["__sort"].apply(lambda x: x if x >= 8016 else x + 8760)
                facet_df = facet_df.sort_values("__sort")

            elif df[x_col].str.startswith("day_").any():
                facet_df["__sort"] = facet_df[x_col].str.extract(r"day_(\d+)").astype(int)
                if facet == "Winter":
                    facet_df["__sort"] = facet_df["__sort"].apply(lambda x: x if x >= 334 else x + 365)
                facet_df = facet_df.sort_values("__sort")

            elif df[x_col].isin(month_names).all():
                facet_df["__sort"] = facet_df[x_col].map(month_order)
                # Fix Winter sorting: Dec (11) → Jan (0) → Feb (1)
                if facet == "Winter":
                    facet_df["__sort"] = facet_df["__sort"].apply(lambda x: x if x >= 11 else x + 12)
                facet_df = facet_df.sort_values("__sort")

            else:
                facet_df = facet_df.sort_values(by=x_col)

            for j, val_col in enumerate(value_columns):
                # Create mapping from column name to user-friendly surface name
                heading = get_display_name_for_column(val_col, y_metric_to_plot)

                color_key = get_column_color(val_col)
                bar_color = COLOURS_TO_RGB.get(color_key, "rgb(127,128,134)")

                # For grouped bars, use offsetgroup; for stacked bars, don't use offsetgroup
                bar_params = {
                    'x': facet_df[x_col],
                    'y': facet_df[val_col],
                    'name': heading,
                    'legendgroup': heading,
                    'showlegend': (i == 0),
                    'marker': dict(color=bar_color, line=dict(width=0)),  # Remove bar borders
                }
                
                # Only set width for stacked bars, not for grouped bars
                if barmode != 'group':
                    bar_params['width'] = min(0.4, max(0.1, 200/len(facet_df)))  # Dynamic bar width for stacked bars
                
                if barmode == 'group':
                    bar_params['offsetgroup'] = j
                
                fig.add_trace(go.Bar(**bar_params), row=row, col=col)

        # Set subplot vertical domains
        available_height = 0.88  # Use more vertical space since legend is below
        row_spacing = 0.18  # Increased from 0.125 to prevent overlap between rows
        total_spacing = row_spacing * (rows - 1)
        row_height = (available_height - total_spacing) / rows

        for r in range(1, rows + 1):
            row_bottom = 0.05 + (rows - r) * (row_height + row_spacing)
            row_top = row_bottom + row_height

            for c in range(1, cols + 1):
                subplot_index = (r - 1) * cols + c
                if subplot_index > len(facets):
                    continue

                yaxis_name = f'yaxis{"" if subplot_index == 1 else subplot_index}'
                if yaxis_name in fig.layout:
                    fig.layout[yaxis_name].domain = [row_bottom, row_top]

        # Custom subplot titles
        annotations = []
        for i, facet in enumerate(facets):
            subplot_index = i + 1
            xaxis_key = f'xaxis{"" if subplot_index == 1 else subplot_index}'
            yaxis_key = f'yaxis{"" if subplot_index == 1 else subplot_index}'

            x_dom = fig.layout[xaxis_key].domain
            y_dom = fig.layout[yaxis_key].domain

            display_text = season_display_names.get(facet, f"<b>{facet}</b>")

            annotations.append(dict(
                text=f"<span style='font-size:10pt'>{display_text}</span>",
                xref='paper',
                yref='paper',
                x=x_dom[0],
                y=y_dom[1] + 0.01,
                xanchor='left',
                yanchor='bottom',
                showarrow=False
            ))

        fig.update_layout(annotations=annotations)

    else:
        # No faceting
        fig = go.Figure()
        for j, val_col in enumerate(value_columns):
            # Create mapping from column name to user-friendly surface name
            heading = get_display_name_for_column(val_col, y_metric_to_plot)

            color_key = get_column_color(val_col)
            bar_color = COLOURS_TO_RGB.get(color_key, "rgb(127,128,134)")

            # For grouped bars, use offsetgroup; for stacked bars, don't use offsetgroup
            bar_params = {
                'x': df[x_col],
                'y': df[val_col],
                'name': heading,
                'legendgroup': heading,
                'marker': dict(color=bar_color, line=dict(width=0)),  # Remove bar borders
            }
            
            # Only set width for stacked bars, not for grouped bars
            if barmode != 'group':
                bar_params['width'] = min(0.25, max(0.1, 200/len(df)))  # Dynamic bar width for stacked bars
            
            if barmode == 'group':
                bar_params['offsetgroup'] = j
            
            fig.add_trace(go.Bar(**bar_params))

        fig.update_layout(yaxis=dict(domain=[0.05, 0.95]))  # Use more vertical space with legend below

    # Y-Axis limits and tick steps
    if y_max is None:
        if barmode == "stack":
            y_max = df[value_columns].sum(axis=1).max() * 1.05
        elif barmode == "stack_percentage":
            y_max = 100
        elif barmode == "group":
            y_max = df[value_columns].max().max() * 1.05
        else:
            raise ValueError(f"Invalid barmode: {barmode}")

    if y_min is None:
        y_min = 0

    fig.update_yaxes(range=[y_min, y_max])

    if y_step is not None:
        fig.update_yaxes(dtick=y_step)

    # Gap settings are handled in fig_format method

    return fig


def parse_plot_type(plot_type_str):
    """
    Split a plot_type string like 'bar_plot_stack' into ('bar_plot', 'stack').

    Returns:
        plot_type (str), plot_mode (str)
    """
    valid_plot_types = {"bar_plot"}
    valid_plot_modes = {"group", "stack", "stack_percentage"}

    parts = plot_type_str.lower().split("_")

    for i in range(1, len(parts) + 1):
        plot_type_candidate = "_".join(parts[:i])
        plot_mode_candidate = "_".join(parts[i:]) if i < len(parts) else None

        if plot_type_candidate in valid_plot_types:
            if plot_mode_candidate in valid_plot_modes:
                return plot_type_candidate, plot_mode_candidate
            else:
                return plot_type_candidate, None

    return None, None  # Not recognized


# Main function
def generate_fig(plot_config, plot_config_general, df_to_plotly, list_y_columns, plot_cea_feature, solar_panel_types_list, hide_title=False):

     if plot_config_general.plot_type.startswith("bar_plot"):
        # Instantiate the bar_plot class
        plot_instance_c = bar_plot(plot_config, plot_config_general, df_to_plotly, list_y_columns, plot_cea_feature, solar_panel_types_list, hide_title)

        # Generate the Plotly figure
        fig = plot_instance_c.generate_fig()

        # Format the Plotly figure
        fig = plot_instance_c.fig_format(fig, plot_cea_feature)

        return fig

     else:
        raise ValueError(f"Invalid plot type: {plot_config_general.plot_type}")





"""
PlotManager – Generates the Plotly graph

"""

from cea.visualisation.format.plot_colours import COLOURS_TO_RGB, COLUMNS_TO_COLOURS
from cea.visualisation.b_data_processor import demand_x_to_plot_building
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


class bar_plot:
    """Generates a Plotly bar plot from processed data."""

    def __init__(self, config_config, dataframe, list_y_columns):

        # Get the dataframe prepared by the data processor, including Y(s), X, and X_facet
        self.df = dataframe

        # Get the settings for the format
        self.plot_title = config_config.plot_title
        self.y_metric_to_plot = config_config.y_metric_to_plot
        self.y_columns = list_y_columns
        self.y_metric_unit = config_config.y_metric_unit
        self.y_normalised_by = config_config.y_normalised_by
        self.y_min = config_config.y_min
        self.y_max = config_config.y_max
        self.y_step = config_config.y_step
        self.y_barmode = config_config.y_barmode
        self.y_label = config_config.y_label
        self.x_to_plot = config_config.x_to_plot
        self.facet_by_numbers_wrapped = config_config.facet_by_numbers_wrapped
        self.facet_by_rows = config_config.facet_by_rows
        self.x_sorted_by = config_config.x_sorted_by
        self.x_sorted_reversed = config_config.x_sorted_reversed
        self.x_label = config_config.x_label

        # Update y_columns based on if normalisation is selected
        if self.y_normalised_by == 'no_normalisation':
            self.y_columns_normalised = list_y_columns
        else:
            self.y_columns_normalised = [item + "/m2" for item in self.y_columns]

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
        fig = position_legend_between_title_and_graph(fig)

        return fig

    def fig_format(self, fig):
        # Set the title
        if self.plot_title:
            title = self.plot_title
        else:
            title = "CEA-4 Building Energy Demand"

        # Set the y-axis label
        if self.y_label:
            y_label = self.y_label
        elif self.y_barmode == 'stack_percentage':
            y_label = "Percentage (%)"
        else:
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
            else:
                raise ValueError(f"Invalid x-to-plot: {self.x_to_plot}")

        if self.y_barmode == 'stack_percentage':
            barmode = 'stack'
        else:
            barmode = self.y_barmode

        # About title and bar mode
        if self.x_to_plot in demand_x_to_plot_building and not self.x_sorted_reversed:
            title = f"<b>{y_label} by {x_label}, sorted by {self.x_sorted_by} (low to high)</b><br><sub>{title}</sub>"
        elif self.x_to_plot in demand_x_to_plot_building and self.x_sorted_reversed:
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

        # About background color
        fig.update_layout(
            plot_bgcolor=COLOURS_TO_RGB.get('background_grey'),       # Inside the plotting area
            paper_bgcolor="white",      # Entire figure background (including margins)
        )

        fig.update_xaxes(
            gridcolor="white",
            gridwidth=2.5, # Grid line color
            tickson='boundaries',
        )

        fig.update_yaxes(
            gridcolor="white",
            gridwidth=1.2,
        )

        return fig


def position_legend_between_title_and_graph(fig):
    """
    Position legend between the title and plot, and push the graph downward.

    Parameters:
    - fig: plotly.graph_objects.Figure
    """

    # Shrink top margin and push down plot
    fig.update_layout(
        legend=dict(
            orientation='h',
            yanchor="top",
            y=1.02,  # Slightly below the top of the whole layout
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
            vertical_spacing=0.125
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
                heading = y_metric_to_plot[j] if isinstance(y_metric_to_plot, list) else val_col
                color_key = COLUMNS_TO_COLOURS.get(val_col, "grey")
                bar_color = COLOURS_TO_RGB.get(color_key, "rgb(127,128,134)")

                fig.add_trace(
                    go.Bar(
                        x=facet_df[x_col],
                        y=facet_df[val_col],
                        name=heading,
                        offsetgroup=j,
                        legendgroup=heading,
                        showlegend=(i == 0),
                        marker=dict(color=bar_color)
                    ),
                    row=row,
                    col=col
                )

        # Set subplot vertical domains
        available_height = 0.80
        row_spacing = 0.125
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
            heading = y_metric_to_plot[j] if isinstance(y_metric_to_plot, list) else val_col
            color_key = COLUMNS_TO_COLOURS.get(val_col, "grey")
            bar_color = COLOURS_TO_RGB.get(color_key, "rgb(127,128,134)")

            fig.add_trace(
                go.Bar(
                    x=df[x_col],
                    y=df[val_col],
                    name=heading,
                    offsetgroup=j,
                    legendgroup=heading,
                    marker=dict(color=bar_color)
                )
            )

        fig.update_layout(yaxis=dict(domain=[0.02, 0.82]))

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

    return fig


# Main function
def generate_fig(config_config, df_to_plotly, list_y_columns):

     if config_config.plot_type == "bar_plot":
        # Instantiate the bar_plot class
        plot_instance_c = bar_plot(config_config, df_to_plotly, list_y_columns)

        # Generate the Plotly figure
        fig = plot_instance_c.generate_fig()

        # Format the Plotly figure
        fig = plot_instance_c.fig_format(fig)

        return fig

     else:
        raise ValueError(f"Invalid plot type: {config_config.plot_type}")





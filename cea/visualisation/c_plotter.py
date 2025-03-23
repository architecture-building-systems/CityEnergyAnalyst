"""
PlotManager – Generates the Plotly graph

"""

import cea.inputlocator
import os
import cea.config
import time
import geopandas as gpd
import plotly.graph_objects as go


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

        # Get the dataframe prepared by the data processor, including Y(s), X, and X_group
        self.df = dataframe

        # Get the settings for the format
        self.plot_title = config_config.plot_title
        self.transposed = config_config.transposed
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
        self.x_sorted_by = config_config.x_sorted_by
        self.x_sorted_reversed = config_config.x_sorted_reversed
        self.x_faceted_by = config_config.x_faceted_by
        self.x_label = config_config.x_label

    def generate_fig(self):
        """Creates a Plotly figure."""

        fig = go.Figure()

        # Process the data if 100% stacked bar chart is selected
        if self.y_barmode == 'stack_percentage':
            df = convert_to_percent_stacked(self.df, self.y_columns)
        else:
            df = self.df

        # Combine the two x-axis levels
        df["x_combined"] = df['X'].astype(str) + "<br>" + df['X_group'].astype(str)

        # Create bar chart
        for col, heading in zip(self.y_columns, self.y_metric_to_plot):
            fig.add_bar(x=df["x_combined"], y=df[col], name=heading)

        return fig

    def fig_format(self, fig):
        # Set the title
        if self.plot_title:
            title = self.plot_title
        else:
            title = "Building Energy Demand"

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
            elif self.x_to_plot == 'building_grouped_by_months':
                x_label = "Buildings (grouped by months)"
            elif self.x_to_plot == 'building_grouped_by_seasons':
                x_label = "Buildings (grouped by seasons)"
            elif self.x_to_plot == 'building_grouped_by_construction_type':
                x_label = "Buildings (grouped by construction type)"
            elif self.x_to_plot == 'building_grouped_by_main_use_type':
                x_label = "Buildings (grouped by main use type)"
            elif self.x_to_plot == 'district_and_hourly':
                x_label = "Hours"
            elif self.x_to_plot == 'district_and_daily':
                x_label = "Days"
            elif self.x_to_plot == 'district_and_monthly':
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
        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title=y_label,
            barmode=barmode
        )

        fig.update_layout(legend=dict(
            orientation="h",          # Horizontal layout
            yanchor="bottom",
            y=-0.15,                   # Move below the plot
            xanchor="left",
            x=0.0
        ),
            margin=dict(t=50, b=10)       # Add extra space below the plot for the legend
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





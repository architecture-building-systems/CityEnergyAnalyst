"""
Cost breakdown visualization for baseline supply system costs.

Creates a stacked horizontal bar chart showing total costs broken down by:
- Scale (BUILDING vs DISTRICT)
- Cost type (CAPEX total, CAPEX annualised, OPEX fixed, OPEX variable)
"""

import pandas as pd
import plotly.express as px
import cea.config
from cea.inputlocator import InputLocator
from cea.visualisation.format.plot_colours import COLOURS_TO_RGB

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def load_and_aggregate_costs(locator):
    """
    Load baseline costs detailed data and aggregate by scale.

    :param locator: InputLocator instance
    :return: DataFrame with aggregated costs by scale
    """
    # Load detailed costs
    detailed_costs_path = locator.get_baseline_costs_detailed()
    df = pd.read_csv(detailed_costs_path)

    # Remove zero-cost placeholder rows
    df = df[df['code'] != 'NONE']

    # Aggregate by scale
    aggregated = df.groupby('scale').agg({
        'capex_total_USD': 'sum',
        'capex_a_USD': 'sum',
        'opex_fixed_a_USD': 'sum',
        'opex_var_a_USD': 'sum'
    }).reset_index()

    return aggregated


def create_cost_breakdown_chart(aggregated_df):
    """
    Create stacked horizontal bar chart of costs by scale and type.

    :param aggregated_df: DataFrame with columns: scale, capex_total_USD, capex_a_USD, opex_fixed_a_USD, opex_var_a_USD
    :return: Plotly Figure object
    """
    # Transform to long format for Plotly Express
    cost_columns = {
        'capex_total_USD': 'CAPEX Total',
        'capex_a_USD': 'CAPEX Annualised',
        'opex_fixed_a_USD': 'OPEX Fixed (annual)',
        'opex_var_a_USD': 'OPEX Variable (annual)'
    }

    df_long = aggregated_df.melt(
        id_vars=['scale'],
        value_vars=list(cost_columns.keys()),
        var_name='cost_type_raw',
        value_name='total_cost_usd'
    )

    # Map to readable cost type names
    df_long['cost_type'] = df_long['cost_type_raw'].map(cost_columns)

    # Calculate total cost per scale for sorting
    scale_totals = df_long.groupby('scale')['total_cost_usd'].sum().reset_index()
    scale_totals.columns = ['scale', 'scale_total']
    df_long = df_long.merge(scale_totals, on='scale')

    # Sort by total cost (descending)
    df_long = df_long.sort_values('scale_total', ascending=True)  # True for horizontal bars (top = largest)

    # Define CEA color scheme for cost types
    cost_type_colors = {
        'CAPEX Total': COLOURS_TO_RGB['blue'],
        'CAPEX Annualised': COLOURS_TO_RGB['blue_light'],
        'OPEX Fixed (annual)': COLOURS_TO_RGB['orange'],
        'OPEX Variable (annual)': COLOURS_TO_RGB['red']
    }

    # Create stacked horizontal bar chart
    fig = px.bar(
        df_long,
        y='scale',
        x='total_cost_usd',
        color='cost_type',
        orientation='h',
        title='Total Project Cost Breakdown by Scale and Type',
        labels={
            'scale': 'Project Scale',
            'total_cost_usd': 'Total Cost (USD)',
            'cost_type': 'Cost Type'
        },
        hover_data={
            'scale': True,
            'cost_type': True,
            'total_cost_usd': ':.2f',
            'cost_type_raw': False,
            'scale_total': False
        },
        color_discrete_map=cost_type_colors
    )

    # Improve layout with CEA background color
    fig.update_layout(
        xaxis_title='Total Cost (USD)',
        yaxis_title='Project Scale',
        hovermode='closest',
        legend_title='Cost Type',
        height=400,
        margin=dict(l=100, r=50, t=80, b=60),
        plot_bgcolor=COLOURS_TO_RGB['background_grey'],
        paper_bgcolor=COLOURS_TO_RGB['white']
    )

    # Format hover template
    fig.update_traces(
        hovertemplate='<b>%{y}</b><br>' +
                      'Cost Type: %{fullData.name}<br>' +
                      'Total Cost: $%{x:,.2f}<br>' +
                      '<extra></extra>'
    )

    return fig


def main(config):
    """
    Main entry point for cost breakdown visualization.

    :param config: Configuration instance
    :return: HTML string of the Plotly figure
    """
    locator = InputLocator(config.scenario)

    # Check if baseline costs file exists
    detailed_costs_path = locator.get_baseline_costs_detailed()
    try:
        # Load and aggregate data
        aggregated_df = load_and_aggregate_costs(locator)

        # Create visualization
        fig = create_cost_breakdown_chart(aggregated_df)

        return fig.to_html()

    except FileNotFoundError:
        error_html = f"""
        <div style="padding: 20px; border: 2px solid #ff6b6b; border-radius: 5px; background-color: #ffe0e0;">
            <h3 style="color: #c92a2a; margin-top: 0;">Baseline Costs Data Not Found</h3>
            <p>The baseline costs file could not be found:</p>
            <code style="display: block; padding: 10px; background-color: #fff; border-radius: 3px; margin: 10px 0;">
                {detailed_costs_path}
            </code>
            <p>Please run the <strong>baseline-costs</strong> script first to generate the required data.</p>
        </div>
        """
        return error_html

    except Exception as e:
        error_html = f"""
        <div style="padding: 20px; border: 2px solid #ff6b6b; border-radius: 5px; background-color: #ffe0e0;">
            <h3 style="color: #c92a2a; margin-top: 0;">Error Creating Visualization</h3>
            <p>An error occurred while creating the cost breakdown chart:</p>
            <code style="display: block; padding: 10px; background-color: #fff; border-radius: 3px; margin: 10px 0;">
                {str(e)}
            </code>
        </div>
        """
        return error_html


if __name__ == '__main__':
    # For interactive viewing in PyCharm or Jupyter
    config = cea.config.Configuration()
    locator = InputLocator(config.scenario)

    # Load and aggregate data
    aggregated_df = load_and_aggregate_costs(locator)

    # Create and show visualization
    fig = create_cost_breakdown_chart(aggregated_df)
    fig.show(renderer="browser")

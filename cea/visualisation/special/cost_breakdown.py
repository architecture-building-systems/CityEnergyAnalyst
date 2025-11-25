"""
Cost breakdown visualization for baseline supply system costs.

Creates a stacked horizontal bar chart showing total costs broken down by:
- Cost category (CAPEX, OPEX, etc.)
- Grouping (scale, building/network, energy carrier, service, component type)
- Normalisation (absolute, per GFA, per conditioned area)
- Unit (USD, kUSD, mioUSD)
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


def load_baseline_costs_data(locator):
    """
    Load baseline costs detailed data and architecture data for normalisation.

    :param locator: InputLocator instance
    :return: tuple of (detailed_df, architecture_df)
    """
    detailed_costs_path = locator.get_baseline_costs_detailed()
    detailed_df = pd.read_csv(detailed_costs_path)

    # Load architecture data for GFA normalisation
    # Use total_demand which has both GFA_m2 and Af_m2
    demand_path = locator.get_total_demand()
    architecture_df = pd.read_csv(demand_path)[['name', 'GFA_m2', 'Af_m2']]

    return detailed_df, architecture_df


def get_component_name(code):
    """
    Convert component code to readable name.

    :param code: Component code (e.g., CH1, BO1, E230AC)
    :return: Readable component name
    """
    # Component type mappings
    component_names = {
        # Chillers
        'CH1': 'Water Chiller',
        'CH2': 'Air Chiller',
        'CH3': 'Compression Chiller',

        # Cooling Towers
        'CT1': 'Cooling Tower (Wet)',
        'CT2': 'Cooling Tower (Dry)',

        # Boilers
        'BO1': 'Boiler (Natural Gas)',
        'BO2': 'Boiler (Oil)',
        'BO4': 'Boiler (Coal)',
        'BO5': 'Boiler (Electric)',
        'BO6': 'Boiler (Wood)',

        # Heat Pumps
        'HP1': 'Heat Pump (Air)',
        'HP2': 'Heat Pump (Water)',

        # Piping
        'PIPES': 'Distribution Piping',

        # Energy Carriers
        'E230AC': 'Electricity (Grid)',
        'E22kAC': 'Electricity (Med Voltage)',
        'E66kAC': 'Electricity (High Voltage)',
        'Cgas': 'Natural Gas',
        'NATURALGAS': 'Natural Gas',
        'Coil': 'Oil',
        'Ccoa': 'Coal',
        'Cwod': 'Wood',
        'Cbig': 'Biogas',
        'Cwbm': 'Wet Biomass',
        'Cdbm': 'Dry Biomass',
        'Chyd': 'Hydrogen',

        # Placeholder
        'NONE': 'No System',
    }

    return component_names.get(code, code)


def process_data_by_grouping(detailed_df, architecture_df, x_to_plot, y_cost_categories,
                               y_normalised_by, y_metric_unit):
    """
    Process and aggregate data according to x-axis grouping and cost categories.

    :param detailed_df: DataFrame from baseline_costs_detailed.csv
    :param architecture_df: DataFrame from zone_geometry for normalisation
    :param x_to_plot: Grouping option (by_scale, by_building_and_network, etc.)
    :param y_cost_categories: List of cost categories to include
    :param y_normalised_by: Normalisation option
    :param y_metric_unit: Unit for display
    :return: DataFrame in long format for plotting
    """
    # Remove zero-cost placeholder rows
    df = detailed_df[detailed_df['code'] != 'NONE'].copy()

    # Map cost category names from config to DataFrame columns
    cost_column_map = {
        'CAPEX_total': 'capex_total_USD',
        'CAPEX_annualised': 'capex_a_USD',
        'OPEX_fixed_annual': 'opex_fixed_a_USD',
        'OPEX_variable_annual': 'opex_var_a_USD',
        'Total_annualised_costs': None  # Will be calculated
    }

    # Calculate TAC if requested
    if 'Total_annualised_costs' in y_cost_categories:
        df['TAC_USD'] = df['capex_a_USD'] + df['opex_fixed_a_USD'] + df['opex_var_a_USD']
        cost_column_map['Total_annualised_costs'] = 'TAC_USD'

    # Select only requested cost categories
    selected_cost_cols = [cost_column_map[cat] for cat in y_cost_categories if cost_column_map[cat]]

    # Group data based on x_to_plot
    if x_to_plot == 'by_scale':
        group_by = ['scale']
        df_agg = df.groupby(group_by)[selected_cost_cols].sum().reset_index()

    elif x_to_plot == 'by_building_and_network':
        group_by = ['name']
        df_agg = df.groupby(group_by)[selected_cost_cols].sum().reset_index()

    elif x_to_plot == 'by_energy_carrier':
        # Only energy carriers (placement == 'energy_carrier')
        df_energy = df[df['placement'] == 'energy_carrier'].copy()
        df_energy['carrier_name'] = df_energy['code'].apply(get_component_name)
        group_by = ['carrier_name']
        df_agg = df_energy.groupby(group_by)[selected_cost_cols].sum().reset_index()
        df_agg = df_agg.rename(columns={'carrier_name': 'group'})

    elif x_to_plot == 'by_operation_service':
        # Group by service (e.g., GRID_cs, NG_hs, DC_network)
        # Map service codes to readable names
        df['service_display'] = df['service'].replace({
            'GRID_cs': 'Cooling (Grid)',
            'GRID_hs': 'Heating (Grid)',
            'NG_hs': 'Heating (Natural Gas)',
            'NG_ww': 'DHW (Natural Gas)',
            'DC_network': 'District Cooling Network',
            'DH_network': 'District Heating Network',
            'NONE': 'No System'
        })
        group_by = ['service_display']
        df_agg = df.groupby(group_by)[selected_cost_cols].sum().reset_index()
        df_agg = df_agg.rename(columns={'service_display': 'group'})

    elif x_to_plot == 'by_component_type':
        # Only physical components (exclude energy carriers)
        df_components = df[df['placement'] != 'energy_carrier'].copy()
        df_components['component_name'] = df_components['code'].apply(get_component_name)
        group_by = ['component_name']
        df_agg = df_components.groupby(group_by)[selected_cost_cols].sum().reset_index()
        df_agg = df_agg.rename(columns={'component_name': 'group'})

    else:
        raise ValueError(f"Invalid x-to-plot option: {x_to_plot}")

    # Apply normalisation
    if y_normalised_by != 'no_normalisation':
        # Get normalisation factors
        if x_to_plot in ['by_scale', 'by_energy_carrier', 'by_operation_service', 'by_component_type']:
            # For aggregated views, use total GFA/Af across all buildings
            if y_normalised_by == 'gross_floor_area':
                total_area = architecture_df['GFA_m2'].sum()
            else:  # conditioned_floor_area
                total_area = architecture_df['Af_m2'].sum()

            # Divide all cost columns by total area
            for col in selected_cost_cols:
                df_agg[col] = df_agg[col] / total_area

        elif x_to_plot == 'by_building_and_network':
            # For building/network view, normalise per building/network
            # Create normaliser lookup
            arch_lookup = architecture_df.set_index('name')

            # Get area column
            area_col = 'GFA_m2' if y_normalised_by == 'gross_floor_area' else 'Af_m2'

            # Apply normalisation per building/network
            for idx, row in df_agg.iterrows():
                name = row['name']
                # For networks, sum GFA of buildings in network
                if name.endswith('_DC') or name.endswith('_DH'):
                    # Get buildings in network from detailed_df
                    network_buildings = df[df['name'] == name]['name'].unique()
                    # For now, use total area (this is approximate)
                    normaliser = total_area if y_normalised_by == 'gross_floor_area' else architecture_df['Af_m2'].sum()
                elif name in arch_lookup.index:
                    normaliser = arch_lookup.loc[name, area_col]
                else:
                    normaliser = 1  # Avoid division by zero

                for col in selected_cost_cols:
                    df_agg.at[idx, col] = row[col] / normaliser

    # Apply unit conversion
    unit_divisors = {
        'USD': 1,
        'kUSD': 1000,
        'mioUSD': 1000000
    }
    divisor = unit_divisors.get(y_metric_unit, 1)

    for col in selected_cost_cols:
        df_agg[col] = df_agg[col] / divisor

    # Transform to long format for plotting
    id_col = group_by[0] if x_to_plot != 'by_building_and_network' else 'name'
    if x_to_plot in ['by_energy_carrier', 'by_operation_service', 'by_component_type']:
        id_col = 'group'

    # Reverse mapping for readable names
    cost_display_names = {
        'capex_total_USD': 'CAPEX Total',
        'capex_a_USD': 'CAPEX Annualised',
        'opex_fixed_a_USD': 'OPEX Fixed',
        'opex_var_a_USD': 'OPEX Variable',
        'TAC_USD': 'Total Annualised Cost'
    }

    df_long = df_agg.melt(
        id_vars=[id_col],
        value_vars=selected_cost_cols,
        var_name='cost_type_raw',
        value_name='total_cost'
    )

    df_long['cost_type'] = df_long['cost_type_raw'].map(cost_display_names)

    # Calculate total per group for sorting
    group_totals = df_long.groupby(id_col)['total_cost'].sum().reset_index()
    group_totals.columns = [id_col, 'group_total']
    df_long = df_long.merge(group_totals, on=id_col)

    # Sort by total (descending)
    df_long = df_long.sort_values('group_total', ascending=True)  # True for horizontal bars

    return df_long, id_col


def create_cost_breakdown_chart(df_long, id_col, y_metric_unit, y_normalised_by, x_to_plot):
    """
    Create stacked horizontal bar chart of costs.

    :param df_long: DataFrame in long format
    :param id_col: Column name for grouping
    :param y_metric_unit: Unit for display
    :param y_normalised_by: Normalisation option
    :param x_to_plot: Grouping option for title
    :return: Plotly Figure object
    """
    # Define CEA color scheme for cost types
    cost_type_colors = {
        'CAPEX Total': COLOURS_TO_RGB['blue'],
        'CAPEX Annualised': COLOURS_TO_RGB['blue_light'],
        'OPEX Fixed': COLOURS_TO_RGB['orange'],
        'OPEX Variable': COLOURS_TO_RGB['red'],
        'Total Annualised Cost': COLOURS_TO_RGB['purple']
    }

    # Determine unit label
    if y_normalised_by == 'no_normalisation':
        unit_suffix = ''
    elif y_normalised_by == 'gross_floor_area':
        unit_suffix = '/m² GFA'
    else:  # conditioned_floor_area
        unit_suffix = '/m² Af'

    unit_label = f"{y_metric_unit}{unit_suffix}"

    # Determine title based on grouping
    grouping_titles = {
        'by_scale': 'by Scale',
        'by_building_and_network': 'by Building and Network',
        'by_energy_carrier': 'by Energy Carrier',
        'by_operation_service': 'by Operation Service',
        'by_component_type': 'by Component Type'
    }

    title = f"Cost Breakdown {grouping_titles.get(x_to_plot, '')}"

    # Create stacked horizontal bar chart
    fig = px.bar(
        df_long,
        y=id_col,
        x='total_cost',
        color='cost_type',
        orientation='h',
        title=title,
        labels={
            id_col: 'Category',
            'total_cost': f'Cost ({unit_label})',
            'cost_type': 'Cost Category'
        },
        hover_data={
            id_col: True,
            'cost_type': True,
            'total_cost': ':.2f',
            'cost_type_raw': False,
            'group_total': False
        },
        color_discrete_map=cost_type_colors
    )

    # Improve layout with CEA background color
    fig.update_layout(
        xaxis_title=f'Cost ({unit_label})',
        yaxis_title='',
        hovermode='closest',
        legend_title='Cost Category',
        height=max(400, len(df_long[id_col].unique()) * 40),  # Dynamic height
        margin=dict(l=150, r=50, t=80, b=60),
        plot_bgcolor=COLOURS_TO_RGB['background_grey'],
        paper_bgcolor=COLOURS_TO_RGB['white']
    )

    # Format hover template
    fig.update_traces(
        hovertemplate='<b>%{y}</b><br>' +
                      'Cost Category: %{fullData.name}<br>' +
                      f'Cost: %{{x:,.2f}} {unit_label}<br>' +
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

    # Get plot configuration
    plot_config = config.plots_cost_breakdown

    # Extract parameters
    y_cost_categories = plot_config.y_cost_category_to_plot
    y_normalised_by = plot_config.y_normalised_by
    y_metric_unit = plot_config.y_metric_unit
    x_to_plot = plot_config.x_to_plot

    # Check if baseline costs file exists
    detailed_costs_path = locator.get_baseline_costs_detailed()
    try:
        # Load data
        detailed_df, architecture_df = load_baseline_costs_data(locator)

        # Process data according to configuration
        df_long, id_col = process_data_by_grouping(
            detailed_df, architecture_df,
            x_to_plot, y_cost_categories,
            y_normalised_by, y_metric_unit
        )

        # Create visualization
        fig = create_cost_breakdown_chart(df_long, id_col, y_metric_unit, y_normalised_by, x_to_plot)

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

    # Get plot configuration
    plot_config = config.plots_cost_breakdown

    # Load data
    detailed_df, architecture_df = load_baseline_costs_data(locator)

    # Process data
    df_long, id_col = process_data_by_grouping(
        detailed_df, architecture_df,
        plot_config.x_to_plot,
        plot_config.y_cost_category_to_plot,
        plot_config.y_normalised_by,
        plot_config.y_metric_unit
    )

    # Create and show visualization
    fig = create_cost_breakdown_chart(
        df_long, id_col,
        plot_config.y_metric_unit,
        plot_config.y_normalised_by,
        plot_config.x_to_plot
    )
    fig.show(renderer="browser")

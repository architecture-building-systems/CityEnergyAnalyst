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
import geopandas as gpd
import os
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


def get_network_buildings_and_area(locator, network_name, network_type, architecture_df, area_col):
    """
    Get the list of buildings connected to a network and calculate their total area.

    :param locator: InputLocator instance
    :param network_name: Network name (e.g., 'qqq')
    :param network_type: 'DH' or 'DC'
    :param architecture_df: DataFrame with building areas
    :param area_col: 'GFA_m2' or 'Af_m2'
    :return: Total area of buildings connected to this network
    """
    try:
        # Get the nodes.shp file for this network
        network_folder = locator.get_output_thermal_network_type_folder(network_type, network_name)
        layout_folder = os.path.join(network_folder, 'layout')
        nodes_file = os.path.join(layout_folder, 'nodes.shp')

        if not os.path.exists(nodes_file):
            # If nodes file doesn't exist, return 0
            return 0

        # Read nodes and get buildings connected to network
        nodes = gpd.read_file(nodes_file)
        network_buildings = nodes[nodes['type'] == 'CONSUMER']['building'].unique().tolist()

        # Calculate total area of these buildings
        arch_lookup = architecture_df.set_index('name')
        total_area = 0
        for building in network_buildings:
            if building in arch_lookup.index:
                total_area += arch_lookup.loc[building, area_col]

        return total_area

    except Exception as e:
        # If any error occurs, return 0
        print(f"Warning: Could not calculate area for {network_name}_{network_type}: {e}")
        return 0


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


def load_whatif_costs_data(locator, whatif_name):
    """
    Load costs_components.csv from a what-if analysis output folder and normalise
    column names to match the legacy schema expected by process_data_by_grouping().

    :param locator: InputLocator instance
    :param whatif_name: What-if scenario name
    :return: tuple of (detailed_df, architecture_df)
    """
    df = pd.read_csv(locator.get_costs_whatif_components_file(whatif_name))

    # Rename new-style columns to legacy names so process_data_by_grouping() is reused unchanged
    df = df.rename(columns={
        'CAPEX_total':          'capex_total_USD',
        'CAPEX_annualised':     'capex_a_USD',
        'OPEX_fixed_annual':    'opex_fixed_a_USD',
        'OPEX_variable_annual': 'opex_var_a_USD',
        'component_code':       'code',
    })

    # Mark energy-carrier rows so by_energy_carrier grouping works (carrier column
    # plays the role of placement=='energy_carrier' in the legacy schema).
    if 'carrier' in df.columns and 'placement' not in df.columns:
        df['placement'] = df['carrier'].apply(
            lambda c: 'energy_carrier' if pd.notna(c) and str(c).strip() else 'component'
        )

    # Architecture: use the final-energy buildings summary for GFA
    arch_path = locator.get_final_energy_buildings_file(whatif_name)
    arch = pd.read_csv(arch_path)[['name', 'GFA_m2']]
    arch = arch[arch['name'].notna()].copy()
    arch['Af_m2'] = arch['GFA_m2']

    return df, arch


def process_data_by_grouping(detailed_df, architecture_df, x_to_plot, y_cost_categories,
                               y_normalised_by, y_metric_unit, locator, config):
    """
    Process and aggregate data according to x-axis grouping and cost categories.

    :param detailed_df: DataFrame from baseline_costs_detailed.csv
    :param architecture_df: DataFrame from zone_geometry for normalisation
    :param x_to_plot: Grouping option (by_scale, by_building_and_network, etc.)
    :param y_cost_categories: List of cost categories to include
    :param y_normalised_by: Normalisation option
    :param y_metric_unit: Unit for display
    :param locator: InputLocator instance
    :param config: Configuration object
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
        # Calculate total area upfront (needed for both aggregated and building/network views)
        if y_normalised_by == 'gross_floor_area':
            total_area = architecture_df['GFA_m2'].sum()
            area_col = 'GFA_m2'
        else:  # conditioned_floor_area
            total_area = architecture_df['Af_m2'].sum()
            area_col = 'Af_m2'

        # Get normalisation factors
        if x_to_plot in ['by_scale', 'by_energy_carrier', 'by_operation_service', 'by_component_type']:
            # For aggregated views, use total GFA/Af across all buildings
            # Divide all cost columns by total area
            for col in selected_cost_cols:
                df_agg[col] = df_agg[col] / total_area

        elif x_to_plot == 'by_building_and_network':
            # For building/network view, normalise per building/network
            # Create normaliser lookup
            arch_lookup = architecture_df.set_index('name')

            # Apply normalisation per building/network
            for idx, row in df_agg.iterrows():
                name = row['name']
                # For networks, calculate actual sum of areas of serving buildings
                if name.endswith('_DC'):
                    # Extract network name from network_id (format: {network_name}_DC)
                    network_name = name[:-3]  # Remove '_DC' suffix
                    # Get DC network buildings and their total area
                    normaliser = get_network_buildings_and_area(locator, network_name, 'DC', architecture_df, area_col)
                    if normaliser == 0:
                        normaliser = 1  # Avoid division by zero
                elif name.endswith('_DH'):
                    # Extract network name from network_id (format: {network_name}_DH)
                    network_name = name[:-3]  # Remove '_DH' suffix
                    # Get DH network buildings and their total area
                    normaliser = get_network_buildings_and_area(locator, network_name, 'DH', architecture_df, area_col)
                    if normaliser == 0:
                        normaliser = 1  # Avoid division by zero
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

    # Apply sorting based on x-sorted-by parameter from plots-general
    plot_config_general = config.plots_general
    x_sorted_by = plot_config_general.x_sorted_by
    x_sorted_reversed = plot_config_general.x_sorted_reversed

    # For cost breakdown, "default" means sort by total cost
    if x_sorted_by == 'default':
        # Sort by total cost (default for cost plots)
        df_long = df_long.sort_values('group_total', ascending=not x_sorted_reversed)
    elif x_sorted_by in ['gross_floor_area', 'conditioned_floor_area']:
        # Sort by building area (only works for by_building_and_network)
        if x_to_plot == 'by_building_and_network':
            area_col = 'GFA_m2' if x_sorted_by == 'gross_floor_area' else 'Af_m2'
            arch_lookup = architecture_df.set_index('name')
            # Add area column to df_long for sorting
            df_long['sort_area'] = df_long[id_col].apply(
                lambda x: arch_lookup.loc[x, area_col] if x in arch_lookup.index else 0
            )
            df_long = df_long.sort_values('sort_area', ascending=not x_sorted_reversed)
        else:
            # Fall back to total cost sorting if not by_building_and_network
            df_long = df_long.sort_values('group_total', ascending=not x_sorted_reversed)
    elif x_sorted_by == 'building_name':
        df_long = df_long.sort_values(id_col, ascending=not x_sorted_reversed)
    else:
        # For other sorting options in plots-general (construction_year, roof_area, etc.)
        # that don't apply to cost breakdown, fall back to total cost sorting
        df_long = df_long.sort_values('group_total', ascending=not x_sorted_reversed)

    return df_long, id_col


def create_cost_breakdown_chart(df_long, id_col, y_metric_unit, y_normalised_by, x_to_plot, plot_config_general,
                                x_range=None, category_order=None):
    """
    Create stacked horizontal bar chart of costs.

    :param df_long: DataFrame in long format
    :param id_col: Column name for grouping
    :param y_metric_unit: Unit for display
    :param y_normalised_by: Normalisation option
    :param x_to_plot: Grouping option for title
    :param plot_config_general: General plot configuration
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
    if plot_config_general.plot_title:
        title = plot_config_general.plot_title
    else:
        grouping_titles = {
            'by_scale': 'by Scale',
            'by_building_and_network': 'by Building and Network',
            'by_energy_carrier': 'by Energy Carrier',
            'by_operation_service': 'by Operation Service',
            'by_component_type': 'by Component Type'
        }
        title = f"Cost Breakdown {grouping_titles.get(x_to_plot, '')}"

    # Determine y-axis label
    if plot_config_general.y_label:
        y_label = plot_config_general.y_label
    else:
        y_label = f'Cost ({unit_label})'

    # Determine x-axis label
    if plot_config_general.x_label:
        x_label = plot_config_general.x_label
    else:
        x_label = ''

    # Determine bar mode from general plot config
    plot_type = plot_config_general.plot_type
    is_percentage = 'percentage' in plot_type
    if 'group' in plot_type:
        barmode = 'group'
    else:
        barmode = 'stack'

    # For percentage mode, convert values to percentages per category
    plot_df = df_long.copy()
    if is_percentage:
        group_totals = plot_df.groupby(id_col)['total_cost'].transform('sum')
        group_totals = group_totals.where(group_totals != 0, 1.0)
        plot_df['total_cost'] = (plot_df['total_cost'] / group_totals) * 100.0
        plot_df['total_cost'] = plot_df['total_cost'].fillna(0.0)

    # Create horizontal bar chart
    fig = px.bar(
        plot_df,
        y=id_col,
        x='total_cost',
        color='cost_type',
        orientation='h',
        barmode=barmode,
        title=title,
        labels={
            id_col: x_label if x_label else 'Category',
            'total_cost': 'Percentage (%)' if is_percentage else y_label,
            'cost_type': 'Cost Category'
        },
        hover_data={
            id_col: True,
            'cost_type': True,
            'total_cost': ':.1f' if is_percentage else ':.2f',
            'cost_type_raw': False,
            'group_total': False
        },
        color_discrete_map=cost_type_colors
    )

    # Height: use global category count when provided (ensures consistent height across scenarios)
    n_categories = len(category_order) if category_order is not None else len(df_long[id_col].unique())
    fig.update_layout(
        xaxis_title='Percentage (%)' if is_percentage else y_label,
        yaxis_title=x_label if x_label else '',
        hovermode='closest',
        legend_title='Cost Category',
        height=max(400, n_categories * 40),
        margin=dict(l=150, r=50, t=80, b=60),
        plot_bgcolor=COLOURS_TO_RGB['background_grey'],
        paper_bgcolor=COLOURS_TO_RGB['white'],
    )

    # Y-axis category order: enforce global order when comparing multiple scenarios
    if category_order is not None:
        fig.update_yaxes(categoryorder='array', categoryarray=category_order)

    # X-axis range: user override wins; otherwise use global max when provided
    if plot_config_general.y_min is not None or plot_config_general.y_max is not None:
        fig.update_xaxes(range=[plot_config_general.y_min, plot_config_general.y_max])
    elif x_range is not None:
        fig.update_xaxes(range=x_range)

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

    # Get plot configurations
    plot_config = config.plots_cost_breakdown
    plot_config_general = config.plots_general

    # Extract parameters
    y_cost_categories = plot_config.y_category_to_plot
    y_normalised_by = plot_config.y_normalised_by
    y_metric_unit = plot_config.y_metric_unit
    x_to_plot = plot_config.x_to_plot

    whatif_names = getattr(plot_config, 'what_if_name', [])

    # When no what-if selected, fall back to baseline data (single chart)
    if not whatif_names:
        detailed_costs_path = locator.get_baseline_costs_detailed()
        try:
            detailed_df, architecture_df = load_baseline_costs_data(locator)
            df_long, id_col = process_data_by_grouping(
                detailed_df, architecture_df,
                x_to_plot, y_cost_categories,
                y_normalised_by, y_metric_unit,
                locator, config
            )
            fig = create_cost_breakdown_chart(df_long, id_col, y_metric_unit, y_normalised_by, x_to_plot, plot_config_general)
            fig.update_layout(autosize=True)
            html = fig.to_html(full_html=True, include_plotlyjs='cdn', config={'responsive': True})
            return html.replace('<head>', '<head><style>html,body{height:100%;margin:0}</style>', 1)
        except FileNotFoundError:
            return (
                f'<div style="padding:20px;border:2px solid #ff6b6b;border-radius:5px;background:#ffe0e0;">'
                f'<h3>Baseline costs data not found</h3>'
                f'<p>Run <strong>baseline-costs</strong> first.</p>'
                f'<code>{detailed_costs_path}</code></div>'
            )
        except Exception as e:
            return (
                f'<div style="padding:20px;border:2px solid #ff6b6b;border-radius:5px;background:#ffe0e0;">'
                f'<h3>Error creating visualisation</h3><code>{e}</code></div>'
            )

    # ── First pass: process all scenarios, collect data for axis alignment ───
    # slot: ('ok', whatif_name, df_long, id_col) or ('err', html_str)
    slots = []
    for whatif_name in whatif_names:
        try:
            detailed_df, architecture_df = load_whatif_costs_data(locator, whatif_name)
            df_long, id_col = process_data_by_grouping(
                detailed_df, architecture_df,
                x_to_plot, y_cost_categories,
                y_normalised_by, y_metric_unit,
                locator, config
            )
            slots.append(('ok', whatif_name, df_long, id_col))
        except FileNotFoundError:
            slots.append(('err', (
                f'<div style="padding:20px;border:2px solid #ff6b6b;border-radius:5px;'
                f'background:#ffe0e0;margin:12px 0">'
                f'<h3>Costs data not found for <em>{whatif_name}</em></h3>'
                f'<p>Run <strong>system-costs</strong> for this scenario first.</p></div>'
            )))
        except Exception as e:
            slots.append(('err', (
                f'<div style="padding:20px;border:2px solid #ff6b6b;border-radius:5px;'
                f'background:#ffe0e0;margin:12px 0">'
                f'<h3>Error for <em>{whatif_name}</em></h3><code>{e}</code></div>'
            )))

    # Compute global axis alignment from all successful scenarios
    ok_slots = [(n, dl, ic) for kind, *rest in slots if kind == 'ok' for n, dl, ic in [rest]]
    if ok_slots:
        # Global x max: max stacked total per category across all scenarios
        global_x_max = max(
            dl.groupby(ic)['total_cost'].sum().max()
            for _, dl, ic in ok_slots
        )
        x_range = [0, global_x_max * 1.05]
        # Global category order: union of all categories, sorted by max total across scenarios
        category_totals: dict = {}
        for _, dl, ic in ok_slots:
            for cat, total in dl.groupby(ic)['total_cost'].sum().items():
                category_totals[cat] = max(category_totals.get(cat, 0.0), total)
        category_order = sorted(category_totals, key=lambda c: category_totals[c])
    else:
        x_range = None
        category_order = None

    # ── Second pass: render with shared axes, preserve order ─────────────────
    html_outputs = []
    plotly_included = False
    for slot in slots:
        if slot[0] == 'err':
            html_outputs.append(slot[1])
            continue
        _, whatif_name, df_long, id_col = slot
        # Add zero rows for categories absent in this scenario so all bars are visible
        if category_order is not None:
            cost_types = df_long[['cost_type_raw', 'cost_type']].drop_duplicates()
            present = set(df_long[id_col].unique())
            missing = [c for c in category_order if c not in present]
            if missing:
                padding_rows = []
                for cat in missing:
                    for _, ct_row in cost_types.iterrows():
                        padding_rows.append({
                            id_col: cat,
                            'cost_type_raw': ct_row['cost_type_raw'],
                            'cost_type': ct_row['cost_type'],
                            'total_cost': 0.0,
                            'group_total': 0.0,
                        })
                df_long = pd.concat([df_long, pd.DataFrame(padding_rows)], ignore_index=True)
        fig = create_cost_breakdown_chart(
            df_long, id_col, y_metric_unit, y_normalised_by, x_to_plot, plot_config_general,
            x_range=x_range, category_order=category_order,
        )
        scenario_name = os.path.basename(config.scenario)
        feature_label = 'CEA-4 Cost Breakdown'
        subtitle = ' | '.join([feature_label, scenario_name, whatif_name])
        fig.update_layout(
            autosize=True,
            title=dict(
                text=f"<b>Cost Breakdown</b><br><sub>{subtitle}</sub>",
                x=0, xanchor='left', yanchor='top', font=dict(size=20),
            ),
            margin=dict(t=80),
        )
        include_js = 'cdn' if not plotly_included else False
        plotly_included = True
        html_outputs.append(fig.to_html(full_html=False, include_plotlyjs=include_js,
                                        config={'responsive': True}))

    body = '\n'.join(html_outputs)
    return (
        '<!DOCTYPE html><html>'
        '<head><meta charset="utf-8"><style>html,body{height:100%;margin:0}</style></head>'
        f'<body>{body}</body></html>'
    )


if __name__ == '__main__':
    # For interactive viewing in PyCharm or Jupyter
    config = cea.config.Configuration()
    locator = InputLocator(config.scenario)

    # Get plot configurations
    plot_config = config.plots_cost_breakdown
    plot_config_general = config.plots_general

    # Load data
    detailed_df, architecture_df = load_baseline_costs_data(locator)

    # Process data
    df_long, id_col = process_data_by_grouping(
        detailed_df, architecture_df,
        plot_config.x_to_plot,
        plot_config.y_category_to_plot,
        plot_config.y_normalised_by,
        plot_config.y_metric_unit,
        locator, config
    )

    # Create and show visualization
    fig = create_cost_breakdown_chart(
        df_long, id_col,
        plot_config.y_metric_unit,
        plot_config.y_normalised_by,
        plot_config.x_to_plot,
        plot_config_general
    )
    fig.show(renderer="browser")

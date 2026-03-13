"""
Sankey diagram of system costs broken down by energy carrier, service and cost category.

Reads costs_components.csv from a what-if analysis output and builds a 3-layer Sankey:
    [Carrier]  →  [Service]  →  [Cost category]

Each link value is the sum of the selected cost categories (CAPEX_annualised,
OPEX_fixed_annual, OPEX_variable_annual, etc.) in the chosen unit.
"""

import os
import pandas as pd
import plotly.graph_objects as go
import cea.config
from cea.inputlocator import InputLocator
from cea.visualisation.format.plot_colours import COLOURS_TO_RGB, get_column_color

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# ── readable display names ──────────────────────────────────────────────────

_CARRIER_DISPLAY = {
    'NATURALGAS': 'Natural Gas',
    'GRID':       'Electricity (Grid)',
    'DH':         'District Heating',
    'DC':         'District Cooling',
    'OIL':        'Oil',
    'COAL':       'Coal',
    'WOOD':       'Wood',
    'BIOGAS':     'Biogas',
    'HYDROGEN':   'Hydrogen',
    'SOLAR':      'Solar',
    'NONE':       'No Carrier',
}

_SERVICE_DISPLAY = {
    'hs':  'Space Heating',
    'ww':  'Domestic Hot Water',
    'cs':  'Space Cooling',
    'e':   'Electricity',
    'DH':  'District Heating',
    'DC':  'District Cooling',
}

_COST_CAT_DISPLAY = {
    'capex_total_USD':   'CAPEX Total',
    'capex_a_USD':       'CAPEX Annualised',
    'opex_fixed_a_USD':  'OPEX Fixed',
    'opex_var_a_USD':    'OPEX Variable',
    'TAC_USD':           'Total Annualised',
}

# Service node colours (borrow from demand palette)
_SERVICE_COLOURS = {
    'Space Heating':       COLOURS_TO_RGB['red'],
    'Domestic Hot Water':  COLOURS_TO_RGB['orange'],
    'Space Cooling':       COLOURS_TO_RGB['blue'],
    'Electricity':         COLOURS_TO_RGB['green'],
    'District Heating':    COLOURS_TO_RGB['red_light'],
    'District Cooling':    COLOURS_TO_RGB['blue_light'],
}

_UNIT_DIVISORS = {'USD': 1, 'kUSD': 1_000, 'mioUSD': 1_000_000}


# ── data helpers ─────────────────────────────────────────────────────────────

def _carrier_colour(carrier_display_name):
    """Return an rgba colour string for a carrier node."""
    # Reverse-lookup the raw key from the display name
    raw = next((k for k, v in _CARRIER_DISPLAY.items() if v == carrier_display_name), carrier_display_name)
    name = get_column_color(raw)
    return COLOURS_TO_RGB.get(name, COLOURS_TO_RGB['grey'])


def _cost_cat_colour(cost_cat_key):
    """Return an rgba colour string for a cost-category node."""
    name = get_column_color(cost_cat_key)
    return COLOURS_TO_RGB.get(name, COLOURS_TO_RGB['grey'])


def _to_rgba(rgb_str, alpha=0.6):
    """Convert 'rgb(r,g,b)' to 'rgba(r,g,b,a)'."""
    return rgb_str.replace('rgb(', 'rgba(').replace(')', f',{alpha})')


def build_sankey_data(df, cost_cats, unit_divisor, normaliser=1.0):
    """
    Transform costs_components DataFrame into Sankey node/link lists.

    Parameters
    ----------
    df : pd.DataFrame
        costs_components.csv content.
    cost_cats : list[str]
        Selected cost-category column names (e.g. ['CAPEX_annualised', 'OPEX_fixed_annual']).
    unit_divisor : float
        Divide all values by this (1 for USD, 1000 for kUSD, etc.).
    normaliser : float
        Divide all values by this area (m²) when normalising by GFA.

    Returns
    -------
    dict with keys: node_labels, node_colors, source, target, value, link_colors
    """
    # ── resolve readable carrier / service names ──────────────────────────
    df = df.copy()

    # Carrier column (use 'carrier' if present, else derive from 'code')
    if 'carrier' in df.columns:
        df['carrier_display'] = df['carrier'].fillna('NONE').apply(
            lambda c: _CARRIER_DISPLAY.get(str(c).strip(), str(c).strip())
        )
    else:
        df['carrier_display'] = 'Unknown'

    # Service column
    if 'service' in df.columns:
        df['service_display'] = df['service'].fillna('Unknown').apply(
            lambda s: _SERVICE_DISPLAY.get(str(s).strip(), str(s).strip())
        )
    else:
        df['service_display'] = 'Unknown'

    # Sum cost cols into a single value column
    present_cats = [c for c in cost_cats if c in df.columns]
    if not present_cats:
        return None
    df['_value'] = df[present_cats].sum(axis=1)

    # ── layer 1→2: carrier → service ──────────────────────────────────────
    l1_l2 = (
        df.groupby(['carrier_display', 'service_display'])['_value']
        .sum()
        .reset_index()
    )
    l1_l2 = l1_l2[l1_l2['_value'] > 0]

    # ── layer 2→3: service → cost category (one link per selected cat) ────
    records = []
    for cat in present_cats:
        agg = df.groupby('service_display')[cat].sum().reset_index()
        agg.columns = ['service_display', '_value']
        agg['cost_cat'] = _COST_CAT_DISPLAY.get(cat, cat)
        records.append(agg[agg['_value'] > 0])
    l2_l3 = pd.concat(records, ignore_index=True) if records else pd.DataFrame()

    if l1_l2.empty and l2_l3.empty:
        return None

    # ── build node list ────────────────────────────────────────────────────
    carriers  = sorted(l1_l2['carrier_display'].unique().tolist())
    services  = sorted(set(l1_l2['service_display'].tolist()) | set(l2_l3['service_display'].tolist()) if not l2_l3.empty else set(l1_l2['service_display'].tolist()))
    cost_cats_display = [_COST_CAT_DISPLAY.get(c, c) for c in present_cats]

    node_labels = carriers + services + cost_cats_display
    idx = {label: i for i, label in enumerate(node_labels)}

    # ── node colours ──────────────────────────────────────────────────────
    node_colors = (
        [COLOURS_TO_RGB.get(get_column_color(next((k for k, v in _CARRIER_DISPLAY.items() if v == c), c)), COLOURS_TO_RGB['grey']) for c in carriers]
        + [_SERVICE_COLOURS.get(s, COLOURS_TO_RGB['grey']) for s in services]
        + [_cost_cat_colour(next((k for k, v in _COST_CAT_DISPLAY.items() if v == cd), cd)) for cd in cost_cats_display]
    )

    # ── build links ───────────────────────────────────────────────────────
    sources, targets, values, link_colors = [], [], [], []
    divisor = unit_divisor * normaliser

    for _, row in l1_l2.iterrows():
        if row['carrier_display'] not in idx or row['service_display'] not in idx:
            continue
        sources.append(idx[row['carrier_display']])
        targets.append(idx[row['service_display']])
        values.append(row['_value'] / divisor)
        link_colors.append(_to_rgba(COLOURS_TO_RGB.get(
            get_column_color(next((k for k, v in _CARRIER_DISPLAY.items() if v == row['carrier_display']), row['carrier_display'])),
            COLOURS_TO_RGB['grey']
        )))

    for _, row in l2_l3.iterrows():
        if row['service_display'] not in idx or row['cost_cat'] not in idx:
            continue
        sources.append(idx[row['service_display']])
        targets.append(idx[row['cost_cat']])
        values.append(row['_value'] / divisor)
        link_colors.append(_to_rgba(_SERVICE_COLOURS.get(row['service_display'], COLOURS_TO_RGB['grey'])))

    return {
        'node_labels':  node_labels,
        'node_colors':  node_colors,
        'source':       sources,
        'target':       targets,
        'value':        values,
        'link_colors':  link_colors,
    }


# ── figure builder ────────────────────────────────────────────────────────────

def create_sankey_fig(sankey_data, title, unit_label):
    """
    Build a Plotly go.Sankey figure from pre-computed node/link data.

    Parameters
    ----------
    sankey_data : dict
        Output of build_sankey_data().
    title : str
        Figure title.
    unit_label : str
        Unit string shown in hover (e.g. 'kUSD' or 'USD/m² GFA').

    Returns
    -------
    go.Figure
    """
    fig = go.Figure(go.Sankey(
        arrangement='snap',
        node=dict(
            label=sankey_data['node_labels'],
            color=sankey_data['node_colors'],
            pad=20,
            thickness=20,
            line=dict(color=COLOURS_TO_RGB['grey_lighter'], width=0.5),
        ),
        link=dict(
            source=sankey_data['source'],
            target=sankey_data['target'],
            value=sankey_data['value'],
            color=sankey_data['link_colors'],
            hovertemplate=(
                '%{source.label} → %{target.label}<br>'
                f'Cost: %{{value:,.2f}} {unit_label}<br>'
                '<extra></extra>'
            ),
        ),
    ))

    fig.update_layout(
        title_text=title,
        title_font_size=16,
        font_size=12,
        plot_bgcolor=COLOURS_TO_RGB['background_grey'],
        paper_bgcolor=COLOURS_TO_RGB['white'],
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


# ── main entry point ──────────────────────────────────────────────────────────

def main(config: cea.config.Configuration):
    """
    Entry point for the plot-cost-sankey script.

    :param config: CEA Configuration instance
    :return: HTML string of the Plotly Sankey figure
    """
    locator = InputLocator(config.scenario)
    plot_config = config.plots_cost_sankey

    whatif_names = getattr(plot_config, 'what_if_name', [])
    if not whatif_names:
        return (
            '<div style="padding:20px;border:2px solid #ffcc00;border-radius:5px;background:#fff8e1;">'
            '<h3>No what-if scenario selected</h3>'
            '<p>Please select a what-if scenario with system costs results in the '
            '<strong>plots-cost-sankey</strong> configuration.</p>'
            '</div>'
        )

    whatif_name = whatif_names[0]
    components_path = locator.get_costs_whatif_components_file(whatif_name)
    if not os.path.exists(components_path):
        return (
            f'<div style="padding:20px;border:2px solid #ff6b6b;border-radius:5px;background:#ffe0e0;">'
            f'<h3>Costs data not found</h3>'
            f'<p>Run <strong>system-costs</strong> for scenario <em>{whatif_name}</em> first.</p>'
            f'<code>{components_path}</code>'
            f'</div>'
        )

    df = pd.read_csv(components_path)

    # Cost categories and unit
    cost_cats = plot_config.y_cost_category_to_plot
    y_metric_unit = plot_config.y_metric_unit
    unit_divisor = _UNIT_DIVISORS.get(y_metric_unit, 1)

    # Normalisation
    y_normalised_by = plot_config.y_normalised_by
    normaliser = 1.0
    if y_normalised_by == 'gross_floor_area':
        fe_path = locator.get_final_energy_buildings_file(whatif_name)
        if os.path.exists(fe_path):
            fe_df = pd.read_csv(fe_path)
            gfa = fe_df['GFA_m2'].sum() if 'GFA_m2' in fe_df.columns else 1.0
            normaliser = gfa if gfa > 0 else 1.0
        unit_label = f'{y_metric_unit}/m² GFA'
    else:
        unit_label = y_metric_unit

    # Build Sankey data
    sankey_data = build_sankey_data(df, cost_cats, unit_divisor, normaliser)
    if sankey_data is None:
        return (
            '<div style="padding:20px;border:2px solid #ffcc00;border-radius:5px;background:#fff8e1;">'
            '<h3>No cost data to display</h3>'
            '<p>The selected cost categories produced no non-zero values.</p>'
            '</div>'
        )

    # Title
    if plot_config.plot_title:
        title = plot_config.plot_title
    else:
        title = f'System Costs — {whatif_name}'

    fig = create_sankey_fig(sankey_data, title, unit_label)

    #
    plot_width = 1600
    plot_height = int(plot_width / 16 * 7)
    fig.update_layout(width=plot_width, height=plot_height)

    return fig.to_html(full_html=False, include_plotlyjs='cdn')

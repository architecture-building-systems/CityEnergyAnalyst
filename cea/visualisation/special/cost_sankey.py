"""
Cost Sankey diagram — 3-layer, money-only.

    [Service]  →  [Technology]  →  [Cost Category]

All link widths are in the same money unit (USD/year annualised).
No energy carriers appear in this diagram; energy flows belong in a
separate Energy Sankey.

Data source: costs_components.csv produced by cea.analysis.costs.main.
"""

import os
import pandas as pd
import plotly.graph_objects as go
import cea.config
from cea.inputlocator import InputLocator
from cea.visualisation.format.plot_colours import COLOURS_TO_RGB

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.2"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# ── Layer 0: service groups ───────────────────────────────────────────────────

# Maps raw `service` column values → display group name
_SERVICE_GROUP_MAP = {
    'hs':            'Space Heating',
    'DH':            'Space Heating',
    'hs_booster':    'Space Heating',
    'ww':            'Domestic Hot Water',
    'ww_booster':    'Domestic Hot Water',
    'cs':            'Space Cooling',
    'DC':            'Space Cooling',
    'e':             'Electricity',
    'E':             'Electricity',
    'hs_piping':     'Distribution',
    'cs_piping':     'Distribution',
    'hs_pumping':    'Distribution',
    'cs_pumping':    'Distribution',
}

_SERVICE_ORDER = [
    'Space Heating',
    'Domestic Hot Water',
    'Space Cooling',
    'Electricity',
    'Solar Generation',
    'Distribution',
]

_SERVICE_COLOURS = {
    'Space Heating':      COLOURS_TO_RGB['red'],
    'Domestic Hot Water': COLOURS_TO_RGB['orange'],
    'Space Cooling':      COLOURS_TO_RGB['blue'],
    'Electricity':        COLOURS_TO_RGB['green'],
    'Solar Generation':   COLOURS_TO_RGB['yellow'],
    'Distribution':       COLOURS_TO_RGB['grey_light'],
}


def _service_group(raw):
    """Map a raw service code to its display group name."""
    s = str(raw).strip()
    if s in _SERVICE_GROUP_MAP:
        return _SERVICE_GROUP_MAP[s]
    if s.startswith('PV_') or s.startswith('SC_') or s.startswith('PVT_'):
        return 'Solar Generation'
    if 'piping' in s.lower():
        return 'Distribution'
    if 'pumping' in s.lower():
        return 'Distribution'
    return s  # fallback: use raw value as its own group


# ── Layer 1: technologies ─────────────────────────────────────────────────────

_COMPONENT_PREFIX_DISPLAY = [
    # (prefix, display_template)  — ordered longest-first to avoid short-prefix shadowing
    ('PVT', 'PVT Panel'),
    ('PV',  'PV Panel'),
    ('SC',  'Solar Collector'),
    ('BO',  'Boiler'),
    ('HP',  'Heat Pump'),
    ('CH',  'Chiller'),
    ('CT',  'Cooling Tower'),
    ('PU',  'Pump'),
    ('HEX', 'Heat Exchanger'),
]

_COMPONENT_EXACT_DISPLAY = {
    'PIPES': 'Piping',
    'GRID':  'Grid Connection',
}

_TECH_COLOURS = {
    'Boiler':          COLOURS_TO_RGB['red_light'],
    'Heat Pump':       COLOURS_TO_RGB['blue_light'],
    'Chiller':         COLOURS_TO_RGB['blue'],
    'Cooling Tower':   COLOURS_TO_RGB['teal_light'],
    'Pump':            COLOURS_TO_RGB['green_light'],
    'Piping':          COLOURS_TO_RGB['grey_lighter'],
    'Heat Exchanger':  COLOURS_TO_RGB['grey_light'],
    'Grid Connection': COLOURS_TO_RGB['green_light'],
    'PV Panel':        COLOURS_TO_RGB['yellow'],
    'Solar Collector': COLOURS_TO_RGB['yellow_light'],
    'PVT Panel':       COLOURS_TO_RGB['yellow_light'],
}


def _component_display(code):
    """Map a component code to a readable technology label."""
    code = str(code).strip()
    if code in _COMPONENT_EXACT_DISPLAY:
        return _COMPONENT_EXACT_DISPLAY[code]
    for prefix, label in _COMPONENT_PREFIX_DISPLAY:
        if code.startswith(prefix):
            return f'{label} ({code})'
    return code


def _tech_base_type(display_label):
    """Extract the base type string from a display label for colour lookup."""
    for base in _TECH_COLOURS:
        if display_label.startswith(base):
            return base
    return None


def _tech_colour(display_label):
    base = _tech_base_type(display_label)
    return _TECH_COLOURS.get(base, COLOURS_TO_RGB['grey'])


# ── Layer 2: cost categories ──────────────────────────────────────────────────

_COST_CAT_DISPLAY = {
    'capex_total_USD':  'CAPEX Total',
    'capex_a_USD':      'CAPEX Annualised',
    'opex_fixed_a_USD': 'OPEX Fixed',
    'opex_var_a_USD':   'OPEX Variable',
    'TAC_USD':          'Total Annualised',
}

_COST_CAT_COLOURS = {
    'CAPEX Total':       COLOURS_TO_RGB['purple'],
    'CAPEX Annualised':  COLOURS_TO_RGB['purple_light'],
    'OPEX Fixed':        COLOURS_TO_RGB['brown'],
    'OPEX Variable':     COLOURS_TO_RGB['brown_light'],
    'Total Annualised':  COLOURS_TO_RGB['grey'],
}

_UNIT_DIVISORS = {'USD': 1, 'kUSD': 1_000, 'mioUSD': 1_000_000}


# ── helpers ───────────────────────────────────────────────────────────────────

def _to_rgba(rgb_str, alpha=0.5):
    """Convert 'rgb(r,g,b)' → 'rgba(r,g,b,alpha)'."""
    return rgb_str.replace('rgb(', 'rgba(').replace(')', f',{alpha})')


# ── core data builder ─────────────────────────────────────────────────────────

def build_sankey_data(df, cost_cats, unit_divisor, normaliser=1.0):
    """
    Transform costs_components DataFrame into a 3-layer cost Sankey.

    Layers (all widths in money units):
        Layer 0  Service group   e.g. Space Heating, Solar Generation
        Layer 1  Technology      e.g. Boiler (BO1), PV Panel (PV1)
        Layer 2  Cost category   e.g. CAPEX Annualised, OPEX Variable

    Parameters
    ----------
    df : pd.DataFrame
        costs_components.csv content.
    cost_cats : list[str]
        Column names to include (e.g. ['capex_a_USD', 'opex_var_a_USD']).
    unit_divisor : float
        1 for USD, 1 000 for kUSD, 1 000 000 for mioUSD.
    normaliser : float
        GFA in m² when normalising per m²; 1.0 otherwise.

    Returns
    -------
    dict  with keys: node_labels, node_colors, source, target, value, link_colors
    None  if no non-zero data found.
    """
    df = df.copy()

    present_cats = [c for c in cost_cats if c in df.columns]
    if not present_cats:
        return None

    divisor = unit_divisor * normaliser

    # Resolve display columns
    df['_service_group'] = df['service'].fillna('Unknown').apply(_service_group)
    df['_tech_display']  = df['component_code'].fillna('Unknown').apply(_component_display)

    # ── Layer 0→1: service → technology ──────────────────────────────────
    l01 = (
        df.groupby(['_service_group', '_tech_display'])[present_cats]
        .sum()
        .assign(_total=lambda x: x.sum(axis=1))
        .reset_index()
    )
    l01 = l01[l01['_total'] > 0]

    # ── Layer 1→2: technology → cost category ────────────────────────────
    records = []
    for cat in present_cats:
        agg = df.groupby('_tech_display')[cat].sum().reset_index()
        agg.columns = ['_tech_display', '_value']
        agg['_cost_cat'] = _COST_CAT_DISPLAY.get(cat, cat)
        records.append(agg[agg['_value'] > 0])
    l12 = pd.concat(records, ignore_index=True) if records else pd.DataFrame()

    if l01.empty:
        return None

    # ── node lists ────────────────────────────────────────────────────────
    # Services: preserve preferred order, then any extras alphabetically
    svc_set = set(l01['_service_group'].unique())
    services = [s for s in _SERVICE_ORDER if s in svc_set]
    services += sorted(svc_set - set(services))

    tech_set = set(l01['_tech_display'].unique())
    if not l12.empty:
        tech_set |= set(l12['_tech_display'].unique())
    technologies = sorted(tech_set)

    cost_cats_display = [_COST_CAT_DISPLAY.get(c, c) for c in present_cats]

    node_labels = services + technologies + cost_cats_display
    idx = {label: i for i, label in enumerate(node_labels)}

    node_colors = (
        [_SERVICE_COLOURS.get(s, COLOURS_TO_RGB['grey']) for s in services]
        + [_tech_colour(t) for t in technologies]
        + [_COST_CAT_COLOURS.get(c, COLOURS_TO_RGB['grey']) for c in cost_cats_display]
    )

    # ── links ─────────────────────────────────────────────────────────────
    sources, targets, values, link_colors = [], [], [], []

    for _, row in l01.iterrows():
        svc = row['_service_group']
        tech = row['_tech_display']
        if svc not in idx or tech not in idx:
            continue
        sources.append(idx[svc])
        targets.append(idx[tech])
        values.append(row['_total'] / divisor)
        link_colors.append(_to_rgba(_SERVICE_COLOURS.get(svc, COLOURS_TO_RGB['grey'])))

    if not l12.empty:
        for _, row in l12.iterrows():
            tech = row['_tech_display']
            cat  = row['_cost_cat']
            if tech not in idx or cat not in idx:
                continue
            sources.append(idx[tech])
            targets.append(idx[cat])
            values.append(row['_value'] / divisor)
            link_colors.append(_to_rgba(_tech_colour(tech)))

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
    Build a Plotly Sankey figure from pre-computed node/link data.

    Parameters
    ----------
    sankey_data : dict   Output of build_sankey_data().
    title : str          Figure title.
    unit_label : str     Unit string for hover text (e.g. 'kUSD' or 'USD/m² GFA').

    Returns
    -------
    go.Figure
    """
    fig = go.Figure(go.Sankey(
        arrangement='snap',
        node=dict(
            label=sankey_data['node_labels'],
            color=sankey_data['node_colors'],
            pad=24,
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

    Produces a 3-layer cost Sankey:
        [Service]  →  [Technology]  →  [Cost Category]

    All link widths are in money units (USD/year or kUSD/year).

    :param config: CEA Configuration instance
    :return: HTML string of the Plotly Sankey figure
    """
    locator = InputLocator(config.scenario)
    plot_config = config.plots_cost_sankey

    whatif_names = getattr(plot_config, 'what_if_name', [])
    if not whatif_names:
        return (
            '<div style="padding:20px;border:2px solid #ffcc00;border-radius:5px;'
            'background:#fff8e1;">'
            '<h3>No what-if scenario selected</h3>'
            '<p>Please select a what-if scenario with system costs results.</p>'
            '</div>'
        )

    whatif_name = whatif_names[0]
    components_path = locator.get_costs_whatif_components_file(whatif_name)
    if not os.path.exists(components_path):
        return (
            f'<div style="padding:20px;border:2px solid #ff6b6b;border-radius:5px;'
            f'background:#ffe0e0;">'
            f'<h3>Costs data not found</h3>'
            f'<p>Run <strong>system-costs</strong> for scenario <em>{whatif_name}</em> first.</p>'
            f'<code>{components_path}</code>'
            f'</div>'
        )

    df = pd.read_csv(components_path)

    cost_cats    = plot_config.y_cost_category_to_plot
    y_metric_unit = plot_config.y_metric_unit
    unit_divisor  = _UNIT_DIVISORS.get(y_metric_unit, 1)

    # Normalisation
    normaliser = 1.0
    if plot_config.y_normalised_by == 'gross_floor_area':
        fe_path = locator.get_final_energy_buildings_file(whatif_name)
        if os.path.exists(fe_path):
            fe_df = pd.read_csv(fe_path)
            gfa = fe_df['GFA_m2'].sum() if 'GFA_m2' in fe_df.columns else 1.0
            normaliser = gfa if gfa > 0 else 1.0
        unit_label = f'{y_metric_unit}/m² GFA'
    else:
        unit_label = y_metric_unit

    sankey_data = build_sankey_data(df, cost_cats, unit_divisor, normaliser)
    if sankey_data is None:
        return (
            '<div style="padding:20px;border:2px solid #ffcc00;border-radius:5px;'
            'background:#fff8e1;">'
            '<h3>No cost data to display</h3>'
            '<p>The selected cost categories produced no non-zero values.</p>'
            '</div>'
        )

    title = plot_config.plot_title or f'System Costs — {whatif_name}'
    fig = create_sankey_fig(sankey_data, title, unit_label)

    plot_width = 1600
    fig.update_layout(width=plot_width, height=int(plot_width / 16 * 7))

    return fig.to_html(full_html=False, include_plotlyjs='cdn')

"""
Cost Sankey diagram — 3 or 4-layer, money-only.

    [Service]  →  [Technology]  →  [Cost Detail]  →  [CAPEX / OPEX]  (4-layer)
    [Service]  →  [Technology]  →  [CAPEX]                            (3-layer, CAPEX only)

Layer count:
  - CAPEX only  → 3 layers (Service → Technology → CAPEX)
  - OPEX only   → 4 layers (Service → Technology → OPEX Fixed / OPEX Variable → OPEX)
  - Both        → 4 layers (Service → Technology → CAPEX detail / OPEX Fixed / OPEX Variable → CAPEX / OPEX)

All link widths are in the same money unit (USD/year or total USD).
No energy carriers appear in this diagram; energy flows belong in a separate Energy Sankey.

Data source: costs_components.csv produced by cea.analysis.costs.main.
"""

import os
import pandas as pd
import plotly.graph_objects as go
import cea.config
from cea.inputlocator import InputLocator
from cea.visualisation.format.plot_colours import (
    COLOURS_TO_RGB,
    COMPONENT_TECH_COLOURS,
    component_display,
    component_tech_colour,
)

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.3"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# ── Layer 0: service groups ───────────────────────────────────────────────────

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
    'Solar',
    'Distribution',
]

_SERVICE_COLOURS = {
    'Space Heating':      COLOURS_TO_RGB['red_light'],
    'Domestic Hot Water': COLOURS_TO_RGB['orange_light'],
    'Space Cooling':      COLOURS_TO_RGB['blue_light'],
    'Electricity':        COLOURS_TO_RGB['green_light'],
    'Solar':   COLOURS_TO_RGB['yellow_light'],
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
    return s


# ── Layer 1: technologies ─────────────────────────────────────────────────────


def _tech_base_type(display_label):
    for base in COMPONENT_TECH_COLOURS:
        if display_label.startswith(base):
            return base
    return None


def _tech_colour(display_label):
    base = _tech_base_type(display_label)
    return COMPONENT_TECH_COLOURS.get(base, COLOURS_TO_RGB['grey'])


# ── Layer 2: cost detail nodes ────────────────────────────────────────────────

# Maps CSV column → detail node label
_DETAIL_LABEL_MAP = {
    'capex_a_USD':      'CAPEX Annualised',
    'capex_total_USD':  'CAPEX Total',
    'opex_fixed_a_USD': 'OPEX Fixed',
    'opex_var_a_USD':   'OPEX Variable',
}

_DETAIL_COLOURS = {
    'CAPEX Annualised': COLOURS_TO_RGB['brown_light'],
    'CAPEX Total':      COLOURS_TO_RGB['brown_light'],
    'OPEX Fixed':       COLOURS_TO_RGB['grey_light'],
    'OPEX Variable':    COLOURS_TO_RGB['grey_light'],
}

# ── Layer 3: summary nodes ────────────────────────────────────────────────────

_SUMMARY_COLOURS = {
    'CAPEX': COLOURS_TO_RGB['brown'],
    'OPEX':  COLOURS_TO_RGB['grey'],
}

_UNIT_DIVISORS = {'USD': 1, 'kUSD': 1_000, 'mioUSD': 1_000_000}


# ── helpers ───────────────────────────────────────────────────────────────────

def _to_rgba(rgb_str, alpha=0.5):
    """Convert 'rgb(r,g,b)' → 'rgba(r,g,b,alpha)'."""
    return rgb_str.replace('rgb(', 'rgba(').replace(')', f',{alpha})')


# ── core data builder ─────────────────────────────────────────────────────────

def build_sankey_data(df, cost_cats_selection, capex_view, x_to_plot, unit_divisor, normaliser=1.0):
    """
    Transform costs_components DataFrame into a cost Sankey.

    Layer structure depends on x_to_plot and cost_cats_selection:

      service + component (or empty = both):
        CAPEX only → Service → Component → CAPEX
        OPEX only  → Service → Component → OPEX Fixed / OPEX Variable → OPEX
        Both       → Service → Component → CAPEX / OPEX Fixed / OPEX Variable → CAPEX / OPEX

      service only:
        CAPEX only → Service → CAPEX
        OPEX only  → Service → OPEX Fixed / OPEX Variable → OPEX
        Both       → Service → CAPEX / OPEX Fixed / OPEX Variable → CAPEX / OPEX

      component only:
        CAPEX only → Component → CAPEX
        OPEX only  → Component → OPEX Fixed / OPEX Variable → OPEX
        Both       → Component → CAPEX / OPEX Fixed / OPEX Variable → CAPEX / OPEX

    Parameters
    ----------
    df : pd.DataFrame
        costs_components.csv content.
    cost_cats_selection : list[str]
        High-level selections: subset of ['CAPEX', 'OPEX']. Empty = both.
    capex_view : str
        'annualised' → use capex_a_USD; 'total' → use capex_total_USD.
    x_to_plot : list[str]
        Subset of ['service', 'component']. Empty = both.
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
    divisor = unit_divisor * normaliser

    # Empty = all selected
    if not cost_cats_selection:
        cost_cats_selection = ['CAPEX', 'OPEX']
    if not x_to_plot:
        x_to_plot = ['service', 'component']

    include_capex = 'CAPEX' in cost_cats_selection
    include_opex = 'OPEX' in cost_cats_selection
    show_service = 'service' in x_to_plot
    show_component = 'component' in x_to_plot

    capex_col = 'capex_a_USD' if capex_view == 'annualised' else 'capex_total_USD'
    capex_detail_label = _DETAIL_LABEL_MAP[capex_col]

    capex_cols = [capex_col] if include_capex and capex_col in df.columns else []
    opex_cols = [c for c in ['opex_fixed_a_USD', 'opex_var_a_USD'] if c in df.columns] if include_opex else []
    all_cols = capex_cols + opex_cols

    if not all_cols:
        return None

    df['_service_group'] = df['service'].fillna('Unknown').apply(_service_group)
    df['_tech_display']  = df['component_code'].fillna('Unknown').apply(component_display)

    # Column → detail label mapping (insertion order preserved)
    col_to_label = {}
    if capex_cols:
        col_to_label[capex_col] = capex_detail_label
    for col in opex_cols:
        col_to_label[col] = _DETAIL_LABEL_MAP[col]
    detail_labels = list(dict.fromkeys(col_to_label.values()))

    # Summary layer: always when OPEX selected (aggregates Fixed + Variable)
    need_summary = include_opex
    summary_labels = []
    if need_summary:
        if include_capex and capex_cols:
            summary_labels.append('CAPEX')
        if opex_cols:
            summary_labels.append('OPEX')

    # ── Build node list ───────────────────────────────────────────────────
    # Collect service/tech sets from rows with non-zero totals
    totals = df.groupby(['_service_group', '_tech_display'])[all_cols].sum()
    totals = totals[totals.sum(axis=1) > 0].reset_index()

    services, technologies = [], []
    if show_service:
        svc_set = set(totals['_service_group'].unique())
        services = [s for s in _SERVICE_ORDER if s in svc_set]
        services += sorted(svc_set - set(services))
    if show_component:
        technologies = sorted(set(totals['_tech_display'].unique()))

    node_labels = services + technologies + detail_labels + summary_labels
    if not node_labels:
        return None
    idx = {label: i for i, label in enumerate(node_labels)}

    node_colors = (
        [_SERVICE_COLOURS.get(s, COLOURS_TO_RGB['grey']) for s in services]
        + [_tech_colour(t) for t in technologies]
        + [_DETAIL_COLOURS.get(d, COLOURS_TO_RGB['grey']) for d in detail_labels]
        + [_SUMMARY_COLOURS.get(s, COLOURS_TO_RGB['grey']) for s in summary_labels]
    )

    sources, targets, values, link_colors = [], [], [], []

    if show_service and show_component:
        # ── Service → Component ───────────────────────────────────────────
        for _, row in totals.iterrows():
            svc = row['_service_group']
            tech = row['_tech_display']
            if svc not in idx or tech not in idx:
                continue
            sources.append(idx[svc])
            targets.append(idx[tech])
            values.append(row[all_cols].sum() / divisor)
            link_colors.append(_to_rgba(_SERVICE_COLOURS.get(svc, COLOURS_TO_RGB['grey'])))

        # ── Component → Detail ────────────────────────────────────────────
        for col, detail_label in col_to_label.items():
            if col not in df.columns or detail_label not in idx:
                continue
            for tech, val in df.groupby('_tech_display')[col].sum().items():
                if val <= 0 or tech not in idx:
                    continue
                sources.append(idx[tech])
                targets.append(idx[detail_label])
                values.append(val / divisor)
                link_colors.append(_to_rgba(_tech_colour(tech)))

    elif show_service:
        # ── Service → Detail ──────────────────────────────────────────────
        for col, detail_label in col_to_label.items():
            if col not in df.columns or detail_label not in idx:
                continue
            for svc, val in df.groupby('_service_group')[col].sum().items():
                if val <= 0 or svc not in idx:
                    continue
                sources.append(idx[svc])
                targets.append(idx[detail_label])
                values.append(val / divisor)
                link_colors.append(_to_rgba(_SERVICE_COLOURS.get(svc, COLOURS_TO_RGB['grey'])))

    else:
        # show_component only (or fallback)
        # ── Component → Detail ────────────────────────────────────────────
        for col, detail_label in col_to_label.items():
            if col not in df.columns or detail_label not in idx:
                continue
            for tech, val in df.groupby('_tech_display')[col].sum().items():
                if val <= 0 or tech not in idx:
                    continue
                sources.append(idx[tech])
                targets.append(idx[detail_label])
                values.append(val / divisor)
                link_colors.append(_to_rgba(_tech_colour(tech)))

    # ── Detail → Summary ─────────────────────────────────────────────────
    if need_summary:
        label_to_col = {v: k for k, v in col_to_label.items()}
        detail_to_summary = {}
        if include_capex and capex_detail_label in detail_labels:
            detail_to_summary[capex_detail_label] = 'CAPEX'
        for col in opex_cols:
            detail_to_summary[_DETAIL_LABEL_MAP[col]] = 'OPEX'

        for detail_label, summary_label in detail_to_summary.items():
            col = label_to_col.get(detail_label)
            if col is None or col not in df.columns:
                continue
            if detail_label not in idx or summary_label not in idx:
                continue
            total_val = df[col].sum()
            if total_val <= 0:
                continue
            sources.append(idx[detail_label])
            targets.append(idx[summary_label])
            values.append(total_val / divisor)
            link_colors.append(_to_rgba(_DETAIL_COLOURS.get(detail_label, COLOURS_TO_RGB['grey'])))

    if not sources:
        return None

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

    cost_cats_selection = plot_config.y_cost_category_to_plot
    capex_view = plot_config.capex_view
    y_metric_unit = plot_config.y_metric_unit
    unit_divisor = _UNIT_DIVISORS.get(y_metric_unit, 1)

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

    x_to_plot = plot_config.x_to_plot
    sankey_data = build_sankey_data(df, cost_cats_selection, capex_view, x_to_plot, unit_divisor, normaliser)
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

    fig.update_layout(autosize=True)
    html = fig.to_html(full_html=True, include_plotlyjs='cdn', config={'responsive': True})
    return html.replace('<head>', '<head><style>html,body{height:100%;margin:0}</style>', 1)

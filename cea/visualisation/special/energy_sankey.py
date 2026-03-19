"""
Energy Flow Sankey diagram.

    [Carrier]  →  [Scale]  →  [Component]  →  [Service]

Layer count controlled by x-to-plot (scale, component, both, or neither).
All link widths are in energy units (kWh / MWh / GWh / kWh/m²).

Data source: B####.csv hourly files + configuration.json from final-energy analysis.
"""

import json
import os
import pandas as pd
import plotly.graph_objects as go
import cea.config
from cea.inputlocator import InputLocator
from cea.visualisation.format.plot_colours import COLOURS_TO_RGB

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# ── Layer 0: energy carriers ──────────────────────────────────────────────────

_CARRIER_COLOURS = {
    'NATURALGAS': COLOURS_TO_RGB['orange'],
    'GRID':       COLOURS_TO_RGB['green'],
    'DH':         COLOURS_TO_RGB['red'],
    'DC':         COLOURS_TO_RGB['blue'],
    'WOOD':       COLOURS_TO_RGB['brown'],
    'OIL':        COLOURS_TO_RGB['brown_light'],
    'COAL':       COLOURS_TO_RGB['grey'],
    'SOLAR':      COLOURS_TO_RGB['yellow'],
}

_CARRIER_DISPLAY = {
    'NATURALGAS': 'Natural Gas',
    'GRID':       'Electricity Grid',
    'DH':         'District Heating',
    'DC':         'District Cooling',
    'WOOD':       'Wood',
    'OIL':        'Oil',
    'COAL':       'Coal',
    'SOLAR':      'Solar',
}


def _carrier_display(code):
    return _CARRIER_DISPLAY.get(code, code)


def _carrier_colour(code):
    # Solar panel variants all map to yellow
    if code.startswith('PV_') or code.startswith('SC_') or code.startswith('PVT_'):
        return COLOURS_TO_RGB['yellow']
    return _CARRIER_COLOURS.get(code, COLOURS_TO_RGB['grey'])


# ── Layer 1: scale ────────────────────────────────────────────────────────────

_SCALE_COLOURS = {
    'Building': COLOURS_TO_RGB['blue_light'],
    'District': COLOURS_TO_RGB['teal_light'],
}

# ── Layer 2: components ───────────────────────────────────────────────────────

_COMPONENT_PREFIX_DISPLAY = [
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
    'GRID':  'City Grid',
}

_TECH_COLOURS = {
    'Boiler':          COLOURS_TO_RGB['red'],
    'Heat Pump':       COLOURS_TO_RGB['orange'],
    'Chiller':         COLOURS_TO_RGB['blue'],
    'Cooling Tower':   COLOURS_TO_RGB['blue'],
    'Pump':            COLOURS_TO_RGB['orange'],
    'Piping':          COLOURS_TO_RGB['grey'],
    'Heat Exchanger':  COLOURS_TO_RGB['orange'],
    'City Grid':       COLOURS_TO_RGB['green'],
    'PV Panel':        COLOURS_TO_RGB['yellow'],
    'Solar Collector': COLOURS_TO_RGB['yellow'],
    'PVT Panel':       COLOURS_TO_RGB['yellow'],
}


def _component_display(code):
    code = str(code).strip()
    if code in _COMPONENT_EXACT_DISPLAY:
        return _COMPONENT_EXACT_DISPLAY[code]
    for prefix, label in _COMPONENT_PREFIX_DISPLAY:
        if code.startswith(prefix):
            return f'{label} ({code})'
    return code


def _tech_colour(display_label):
    for base, colour in _TECH_COLOURS.items():
        if display_label.startswith(base):
            return colour
    return COLOURS_TO_RGB['grey']


# ── Layer 3: services ─────────────────────────────────────────────────────────

_SERVICE_ORDER = [
    'Space Heating',
    'Domestic Hot Water',
    'Space Cooling',
    'Electricity',
]

_SERVICE_COLOURS = {
    'Space Heating':      COLOURS_TO_RGB['red_light'],
    'Domestic Hot Water': COLOURS_TO_RGB['orange_light'],
    'Space Cooling':      COLOURS_TO_RGB['blue_light'],
    'Electricity':        COLOURS_TO_RGB['green_light'],
}

# Maps config parameter choice → service display name
_SERVICE_DISPLAY = {
    'space_heating':    'Space Heating',
    'domestic_hot_water': 'Domestic Hot Water',
    'space_cooling':    'Space Cooling',
    'electricity':      'Electricity',
}

# Maps config key in configuration.json → (service display name, B####.csv column prefix)
_CONFIG_KEY_MAP = {
    'space_heating': ('Space Heating',      'Qhs_sys'),
    'hot_water':     ('Domestic Hot Water', 'Qww_sys'),
    'space_cooling': ('Space Cooling',      'Qcs_sys'),
    'electricity':   ('Electricity',        'E_sys'),
}

_UNIT_DIVISORS = {'kWh': 1, 'MWh': 1_000, 'GWh': 1_000_000}


# ── helpers ───────────────────────────────────────────────────────────────────

def _to_rgba(rgb_str, alpha=0.5):
    return rgb_str.replace('rgb(', 'rgba(').replace(')', f',{alpha})')


# ── data loader ───────────────────────────────────────────────────────────────

def load_energy_flow_data(locator, whatif_name):
    """
    Aggregate energy flow across all buildings into a flat DataFrame.

    Returns
    -------
    pd.DataFrame  columns: carrier, scale, component, service, value_kWh
    """
    config_file = locator.get_analysis_configuration_file(whatif_name)
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    with open(config_file) as f:
        config_data = json.load(f)

    building_configs = config_data.get('buildings', {})

    records = []

    for building, bconfig in building_configs.items():
        bfile = locator.get_final_energy_building_file(building, whatif_name)
        if not os.path.exists(bfile):
            continue

        annual = pd.read_csv(bfile).sum(numeric_only=True)

        for cfg_key, (svc_display, col_prefix) in _CONFIG_KEY_MAP.items():
            svc_config = bconfig.get(cfg_key)
            if not svc_config:
                continue

            primary_carrier = svc_config.get('carrier', '')
            component_code = svc_config.get('primary_component', '')
            scale_label = 'District' if svc_config.get('scale') == 'DISTRICT' else 'Building'

            for col in annual.index:
                if not (col.startswith(f'{col_prefix}_') and col.endswith('_kWh')
                        and col != f'{col_prefix}_kWh'):
                    continue
                val = annual[col]
                if val <= 0:
                    continue

                carrier = col[len(col_prefix) + 1:-4]  # strip {prefix}_ and _kWh
                comp = _component_display(component_code) if carrier == primary_carrier else ''

                records.append({
                    'carrier':   _carrier_display(carrier),
                    '_carrier_raw': carrier,
                    'scale':     scale_label,
                    'component': comp,
                    'service':   svc_display,
                    'value_kWh': val,
                })

    if not records:
        return pd.DataFrame(columns=['carrier', '_carrier_raw', 'scale', 'component', 'service', 'value_kWh'])

    df = pd.DataFrame(records)
    return df.groupby(['carrier', '_carrier_raw', 'scale', 'component', 'service'],
                      as_index=False)['value_kWh'].sum()


# ── core data builder ─────────────────────────────────────────────────────────

def build_sankey_data(df, service_filter, x_to_plot, unit_divisor, normaliser=1.0):
    """
    Transform energy flow DataFrame into Sankey node/link data.

    Parameters
    ----------
    df : pd.DataFrame           Output of load_energy_flow_data().
    service_filter : list[str]  Subset of _SERVICE_DISPLAY keys. Empty = all.
    x_to_plot : list[str]       Subset of ['scale', 'component']. Empty = both.
    unit_divisor : float        1 for kWh, 1000 for MWh, 1e6 for GWh.
    normaliser : float          GFA in m² when normalising per m²; 1.0 otherwise.

    Returns
    -------
    dict  node_labels, node_colors, source, target, value, link_colors
    None  if no non-zero data.
    """
    if not service_filter:
        service_filter = list(_SERVICE_DISPLAY.keys())
    if not x_to_plot:
        x_to_plot = ['scale', 'component']

    # Map param choices to display names
    service_display_filter = [_SERVICE_DISPLAY[s] for s in service_filter if s in _SERVICE_DISPLAY]

    show_scale = 'scale' in x_to_plot
    show_component = 'component' in x_to_plot
    divisor = unit_divisor * normaliser

    df = df[df['service'].isin(service_display_filter)].copy()
    df = df[df['value_kWh'] > 0]
    if df.empty:
        return None

    # Collect ordered unique nodes per layer
    carrier_set = set(df['carrier'].unique())
    carriers = sorted(carrier_set)

    scales = sorted(df['scale'].unique()) if show_scale else []
    components = [c for c in sorted(df['component'].unique()) if c] if show_component else []
    svc_set = set(df['service'].unique())
    services = [s for s in _SERVICE_ORDER if s in svc_set]
    services += sorted(svc_set - set(services))

    node_labels = carriers + scales + components + services
    if not node_labels:
        return None

    idx = {label: i for i, label in enumerate(node_labels)}

    node_colors = (
        [_carrier_colour(row['_carrier_raw']) for _, row in
         df.drop_duplicates('carrier').set_index('carrier').reindex(carriers).reset_index().iterrows()]
        + [_SCALE_COLOURS.get(s, COLOURS_TO_RGB['grey']) for s in scales]
        + [_tech_colour(c) for c in components]
        + [_SERVICE_COLOURS.get(s, COLOURS_TO_RGB['grey']) for s in services]
    )

    sources, targets, values, link_colors = [], [], [], []

    def add_link(src, tgt, val, colour):
        if src not in idx or tgt not in idx or val <= 0:
            return
        sources.append(idx[src])
        targets.append(idx[tgt])
        values.append(val / divisor)
        link_colors.append(_to_rgba(colour))

    # Helper to get carrier colour from display name
    _carrier_colour_by_display = {
        row['carrier']: _carrier_colour(row['_carrier_raw'])
        for _, row in df.drop_duplicates('carrier').iterrows()
    }

    if show_scale and show_component:
        for (c, sc), g in df.groupby(['carrier', 'scale']):
            add_link(c, sc, g['value_kWh'].sum(), _carrier_colour_by_display.get(c, COLOURS_TO_RGB['grey']))
        for (sc, comp), g in df[df['component'] != ''].groupby(['scale', 'component']):
            add_link(sc, comp, g['value_kWh'].sum(), _SCALE_COLOURS.get(sc, COLOURS_TO_RGB['grey']))
        for (comp, svc), g in df[df['component'] != ''].groupby(['component', 'service']):
            add_link(comp, svc, g['value_kWh'].sum(), _tech_colour(comp))
        # Rows without component: scale → service directly
        for (sc, svc), g in df[df['component'] == ''].groupby(['scale', 'service']):
            add_link(sc, svc, g['value_kWh'].sum(), _SCALE_COLOURS.get(sc, COLOURS_TO_RGB['grey']))

    elif show_scale:
        for (c, sc), g in df.groupby(['carrier', 'scale']):
            add_link(c, sc, g['value_kWh'].sum(), _carrier_colour_by_display.get(c, COLOURS_TO_RGB['grey']))
        for (sc, svc), g in df.groupby(['scale', 'service']):
            add_link(sc, svc, g['value_kWh'].sum(), _SCALE_COLOURS.get(sc, COLOURS_TO_RGB['grey']))

    elif show_component:
        for (c, comp), g in df[df['component'] != ''].groupby(['carrier', 'component']):
            add_link(c, comp, g['value_kWh'].sum(), _carrier_colour_by_display.get(c, COLOURS_TO_RGB['grey']))
        for (comp, svc), g in df[df['component'] != ''].groupby(['component', 'service']):
            add_link(comp, svc, g['value_kWh'].sum(), _tech_colour(comp))
        # No component: carrier → service directly
        for (c, svc), g in df[df['component'] == ''].groupby(['carrier', 'service']):
            add_link(c, svc, g['value_kWh'].sum(), _carrier_colour_by_display.get(c, COLOURS_TO_RGB['grey']))

    else:
        for (c, svc), g in df.groupby(['carrier', 'service']):
            add_link(c, svc, g['value_kWh'].sum(), _carrier_colour_by_display.get(c, COLOURS_TO_RGB['grey']))

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
                f'Energy: %{{value:,.2f}} {unit_label}<br>'
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
    locator = InputLocator(config.scenario)
    plot_config = config.plots_energy_sankey

    whatif_names = getattr(plot_config, 'what_if_name', [])
    if not whatif_names:
        return (
            '<div style="padding:20px;border:2px solid #ffcc00;border-radius:5px;'
            'background:#fff8e1;">'
            '<h3>No what-if scenario selected</h3>'
            '<p>Please select a what-if scenario with final energy results.</p>'
            '</div>'
        )

    whatif_name = whatif_names[0]
    config_path = locator.get_analysis_configuration_file(whatif_name)
    if not os.path.exists(config_path):
        return (
            f'<div style="padding:20px;border:2px solid #ff6b6b;border-radius:5px;'
            f'background:#ffe0e0;">'
            f'<h3>Final energy data not found</h3>'
            f'<p>Run <strong>final-energy</strong> for scenario <em>{whatif_name}</em> first.</p>'
            f'<code>{config_path}</code>'
            f'</div>'
        )

    df = load_energy_flow_data(locator, whatif_name)

    service_filter = plot_config.y_service_category_to_plot
    x_to_plot = plot_config.x_to_plot
    y_metric_unit = plot_config.y_metric_unit
    unit_divisor = _UNIT_DIVISORS.get(y_metric_unit, 1_000)

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

    sankey_data = build_sankey_data(df, service_filter, x_to_plot, unit_divisor, normaliser)
    if sankey_data is None:
        return (
            '<div style="padding:20px;border:2px solid #ffcc00;border-radius:5px;'
            'background:#fff8e1;">'
            '<h3>No energy flow data to display</h3>'
            '<p>The selected service categories produced no non-zero values.</p>'
            '</div>'
        )

    title = plot_config.plot_title or f'Energy Flow — {whatif_name}'
    fig = create_sankey_fig(sankey_data, title, unit_label)

    fig.update_layout(autosize=True)
    html = fig.to_html(full_html=True, include_plotlyjs='cdn', config={'responsive': True})
    return html.replace('<head>', '<head><style>html,body{height:100%;margin:0}</style>', 1)


if __name__ == '__main__':
    main(cea.config.Configuration())

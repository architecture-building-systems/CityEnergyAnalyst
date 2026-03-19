"""
Energy Flow Sankey diagram.

    [Carrier]  →  [Plant Component]  →  [Network]  →  [Building Component]  →  [Service]

For district systems (DC/DH), the primary carrier is what the plant consumes (e.g. GRID for
a chiller). For building-scale systems, the carrier is what the building equipment consumes
(e.g. NATURALGAS for a gas boiler).

Layer visibility is controlled by x-to-plot:
  'component' → show plant-side equipment and building-side equipment nodes
  'scale'     → show DC/DH network node (district) or Building node (building-scale)

Data sources:
  - B####.csv          hourly building final energy files
  - {net}_{type}_{plant}.csv  hourly plant final energy files (if available)
  - configuration.json component/scale/carrier mapping
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
    if code.startswith('PV_') or code.startswith('SC_') or code.startswith('PVT_'):
        return COLOURS_TO_RGB['yellow']
    return _CARRIER_COLOURS.get(code, COLOURS_TO_RGB['grey'])


# ── Layer 1: scale ────────────────────────────────────────────────────────────

_SCALE_COLOURS = {
    'Building':         COLOURS_TO_RGB['blue_light'],
    'DC Network':       COLOURS_TO_RGB['teal_light'],
    'DH Network':       COLOURS_TO_RGB['red_light'],
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
    'space_heating':      'Space Heating',
    'domestic_hot_water': 'Domestic Hot Water',
    'space_cooling':      'Space Cooling',
    'electricity':        'Electricity',
}

# Maps configuration.json key → (service display name, B####.csv column prefix)
_CONFIG_KEY_MAP = {
    'space_heating': ('Space Heating',      'Qhs_sys'),
    'hot_water':     ('Domestic Hot Water', 'Qww_sys'),
    'space_cooling': ('Space Cooling',      'Qcs_sys'),
    'electricity':   ('Electricity',        'E_sys'),
}

_UNIT_DIVISORS = {'kWh': 1, 'MWh': 1_000, 'GWh': 1_000_000}

# Placeholder node labels for empty layers
_NO_DISTRICT = 'No District System'
_NO_BUILDING = 'No Building Conversion'
_PLACEHOLDER_COLOUR = COLOURS_TO_RGB.get('grey_lighter', 'rgb(210,210,210)')

# Fixed x positions for the 4 layers (Plotly 0–1 range, exclusive of exact 0/1)
_LAYER_X = {0: 0.01, 1: 0.34, 2: 0.67, 3: 0.99}


# ── helpers ───────────────────────────────────────────────────────────────────

def _to_rgba(rgb_str, alpha=0.5):
    return rgb_str.replace('rgb(', 'rgba(').replace(')', f',{alpha})')


# ── plant data loader ─────────────────────────────────────────────────────────

def _load_plant_totals(locator, whatif_name, plant_configs, building_configs):
    """
    Load annual plant energy input totals from plant CSV files.

    Returns dict keyed by network_type ('DH' or 'DC'):
      {
        '_carrier_raw': 'GRID',
        'carrier': 'Electricity Grid',
        'component': 'Chiller (CH1)',
        'input_kWh': 5_000_000.0,
      }
    Returns an empty dict if no plant files exist.
    """
    # Collect network_name per network_type from building configs
    network_names = {}
    for bconfig in building_configs.values():
        for cfg_key in ('space_heating', 'hot_water', 'space_cooling'):
            cfg = bconfig.get(cfg_key)
            if not cfg or cfg.get('scale') != 'DISTRICT':
                continue
            nt = 'DH' if cfg_key in ('space_heating', 'hot_water') else 'DC'
            if nt not in network_names and cfg.get('network_name'):
                network_names[nt] = cfg['network_name']

    totals = {}
    folder = locator.get_final_energy_folder(whatif_name)

    for plant_name, plant_cfg in plant_configs.items():
        network_type = plant_cfg.get('network_type', '')
        carrier_raw = plant_cfg.get('carrier', 'GRID')
        component_code = plant_cfg.get('primary_component', '')
        network_name = network_names.get(network_type, '')
        if not network_type or not network_name:
            continue

        # Scan for all plant files: {network_name}_{network_type}_{plant_name}.csv
        prefix = f'{network_name}_{network_type}_'
        plant_files = [
            os.path.join(folder, f) for f in os.listdir(folder)
            if f.startswith(prefix) and f.endswith('.csv')
        ]
        if not plant_files:
            continue

        carrier_col = (
            f'plant_cooling_{carrier_raw}_kWh'
            if network_type == 'DC'
            else f'plant_heating_{carrier_raw}_kWh'
        )

        total_input = 0.0
        for fpath in plant_files:
            df = pd.read_csv(fpath)
            if carrier_col in df.columns:
                total_input += df[carrier_col].sum()

        if total_input > 0:
            if network_type in totals:
                totals[network_type]['input_kWh'] += total_input
            else:
                totals[network_type] = {
                    '_carrier_raw': carrier_raw,
                    'carrier': _carrier_display(carrier_raw),
                    'component': _component_display(component_code) if component_code else '',
                    'input_kWh': total_input,
                }

    return totals


# ── data loader ───────────────────────────────────────────────────────────────

def load_energy_flow_data(locator, whatif_name):
    """
    Aggregate energy flow across all buildings and plants into a flat DataFrame.

    Columns
    -------
    primary_carrier    display name of the primary energy carrier entering the system
    _carrier_raw       raw carrier code (for colour lookup)
    plant_component    plant-side equipment display name (DISTRICT only, else '')
    network            network type 'DC' or 'DH' (DISTRICT only, else '')
    building_component building-side equipment display name (HEX for district, equipment for building)
    scale              'District' or 'Building'
    service            end-use service display name
    value_kWh          building-side annual energy consumption
    plant_input_kWh    annual primary energy input to the plant (DISTRICT only; equals value_kWh
                       for building-scale rows)
    _has_plant_data    True if plant CSV files were found
    """
    config_file = locator.get_analysis_configuration_file(whatif_name)
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    with open(config_file) as f:
        config_data = json.load(f)

    building_configs = config_data.get('buildings', {})
    plant_configs = config_data.get('plants', {})

    plant_totals = _load_plant_totals(locator, whatif_name, plant_configs, building_configs)

    records = []

    for building, bconfig in building_configs.items():
        bfile = locator.get_final_energy_building_file(building, whatif_name)
        if not os.path.exists(bfile):
            continue

        annual = pd.read_csv(bfile).sum(numeric_only=True)

        for cfg_key, (svc_display, col_prefix) in _CONFIG_KEY_MAP.items():
            svc_config = bconfig.get(cfg_key)

            # Electricity has no supply config entry — read columns directly at building scale
            if not svc_config:
                if cfg_key != 'electricity':
                    continue
                for col in annual.index:
                    if not (col.startswith(f'{col_prefix}_') and col.endswith('_kWh')
                            and col != f'{col_prefix}_kWh'):
                        continue
                    val = annual[col]
                    if val <= 0:
                        continue
                    carrier_raw = col[len(col_prefix) + 1:-4]
                    records.append({
                        'primary_carrier':    _carrier_display(carrier_raw),
                        '_carrier_raw':       carrier_raw,
                        'plant_component':    '',
                        'network':            '',
                        'building_component': '',
                        'scale':              'Building',
                        'service':            svc_display,
                        'value_kWh':          val,
                        'plant_input_kWh':    val,
                        '_has_plant_data':    False,
                    })
                continue

            scale = svc_config.get('scale', 'BUILDING')

            if scale == 'DISTRICT':
                network_type = 'DH' if cfg_key in ('space_heating', 'hot_water') else 'DC'
                col = f'{col_prefix}_{network_type}_kWh'
                val = annual.get(col, 0)
                if val <= 0:
                    continue

                pt = plant_totals.get(network_type)
                if pt:
                    carrier_raw = pt['_carrier_raw']
                    carrier = pt['carrier']
                    plant_comp = pt['component']
                    plant_input = pt['input_kWh']
                    has_plant = True
                else:
                    # No plant files: fall back to network carrier as entry point
                    carrier_raw = network_type  # 'DC' or 'DH'
                    carrier = _carrier_display(carrier_raw)
                    plant_comp = _component_display(svc_config.get('primary_component', ''))
                    plant_input = val
                    has_plant = False

                building_comp = svc_config.get('tertiary_component') or ''
                if building_comp:
                    building_comp = _component_display(building_comp)

                records.append({
                    'primary_carrier':    carrier,
                    '_carrier_raw':       carrier_raw,
                    'plant_component':    plant_comp,
                    'network':            network_type,
                    'building_component': building_comp,
                    'scale':              'District',
                    'service':            svc_display,
                    'value_kWh':          val,
                    'plant_input_kWh':    plant_input,
                    '_has_plant_data':    has_plant,
                })

            else:
                primary_carrier_raw = svc_config.get('carrier', '')
                component_code = svc_config.get('primary_component', '')

                for col in annual.index:
                    if not (col.startswith(f'{col_prefix}_') and col.endswith('_kWh')
                            and col != f'{col_prefix}_kWh'):
                        continue
                    val = annual[col]
                    if val <= 0:
                        continue

                    carrier_raw = col[len(col_prefix) + 1:-4]
                    comp = _component_display(component_code) if carrier_raw == primary_carrier_raw else ''

                    records.append({
                        'primary_carrier':    _carrier_display(carrier_raw),
                        '_carrier_raw':       carrier_raw,
                        'plant_component':    '',
                        'network':            '',
                        'building_component': comp,
                        'scale':              'Building',
                        'service':            svc_display,
                        'value_kWh':          val,
                        'plant_input_kWh':    val,
                        '_has_plant_data':    False,
                    })

    if not records:
        cols = ['primary_carrier', '_carrier_raw', 'plant_component', 'network',
                'building_component', 'scale', 'service', 'value_kWh',
                'plant_input_kWh', '_has_plant_data']
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(records)

    group_cols = ['primary_carrier', '_carrier_raw', 'plant_component', 'network',
                  'building_component', 'scale', 'service', '_has_plant_data']

    district = df[df['scale'] == 'District']
    building = df[df['scale'] == 'Building']

    parts = []
    if not district.empty:
        # value_kWh: sum across buildings
        # plant_input_kWh: when plant data exists the total is the same for every building row
        #   → take max to avoid double-counting; when no plant data it equals value_kWh → sum
        has_plant = district.groupby(group_cols)['_has_plant_data'].any()
        d_agg = district.groupby(group_cols, as_index=False).agg(
            value_kWh=('value_kWh', 'sum'),
            plant_input_kWh=('plant_input_kWh', 'sum'),
        )
        # Overwrite with max for rows that have real plant data (avoids double-counting)
        for i, row in d_agg.iterrows():
            key = tuple(row[c] for c in group_cols)
            if has_plant.get(key, False):
                grp = district.groupby(group_cols).get_group(key)
                d_agg.at[i, 'plant_input_kWh'] = grp['plant_input_kWh'].max()
        parts.append(d_agg)
    if not building.empty:
        b_agg = building.groupby(group_cols, as_index=False).agg(
            value_kWh=('value_kWh', 'sum'),
            plant_input_kWh=('plant_input_kWh', 'sum'),
        )
        parts.append(b_agg)

    return pd.concat(parts, ignore_index=True)


# ── core data builder ─────────────────────────────────────────────────────────

def build_sankey_data(df, service_filter, x_to_plot, unit_divisor, normaliser=1.0):
    """
    Build a STRICT 4-layer Sankey: City → District → Building → End-use service.

    Every flow path occupies all four layers. When no real component exists at a layer,
    an explicit placeholder node is inserted:
      - 'No District System'  when a building-scale flow has no district plant
      - 'No Building Conversion' when a flow has no building-side equipment

    x_to_plot controls whether real component nodes are shown at each layer:
      'district' → show district plant equipment (Chiller, DH Boiler, …)
      'building' → show building equipment (Heat Exchanger, standalone Boiler, …)
    Placeholder nodes are always shown regardless of x_to_plot.

    Parameters
    ----------
    df             Output of load_energy_flow_data().
    service_filter list[str]  Subset of _SERVICE_DISPLAY keys. Empty = all.
    x_to_plot      list[str]  Subset of ['district', 'building'].
    unit_divisor   float
    normaliser     float      GFA in m² when normalising per m²; 1.0 otherwise.

    Returns
    -------
    dict  node_labels, node_colors, node_x, node_y, source, target, value, link_colors
    None  if no non-zero data.
    """
    if not service_filter:
        service_filter = list(_SERVICE_DISPLAY.keys())

    show_district = 'district' in x_to_plot
    show_building = 'building' in x_to_plot
    divisor = unit_divisor * normaliser

    service_display_filter = [_SERVICE_DISPLAY[s] for s in service_filter if s in _SERVICE_DISPLAY]
    df = df[df['service'].isin(service_display_filter)].copy()
    df = df[df['value_kWh'] > 0]
    if df.empty:
        return None

    district_df = df[df['scale'] == 'District']
    building_df = df[df['scale'] == 'Building']

    # ── Layer 0: City ──────────────────────────────────────────────────────
    l0 = sorted(df['primary_carrier'].unique())

    # ── Layer 1: District ──────────────────────────────────────────────────
    # Real district components + placeholder if any building-scale flows exist
    l1_real = (
        sorted(set(district_df['plant_component'].unique()) - {''})
        if show_district and not district_df.empty else []
    )
    l1_placeholder = [_NO_DISTRICT] if not building_df.empty else []
    l1 = l1_real + l1_placeholder

    # ── Layer 2: Building ──────────────────────────────────────────────────
    # Real building components + placeholder if any flow has no building equipment
    l2_real = (
        sorted(set(df['building_component'].unique()) - {''})
        if show_building else []
    )
    need_bldg_placeholder = df['building_component'].eq('').any()
    l2_placeholder = [_NO_BUILDING] if need_bldg_placeholder else []
    l2 = l2_real + l2_placeholder

    # ── Layer 3: End-use service ───────────────────────────────────────────
    svc_set = set(df['service'].unique())
    l3 = [s for s in _SERVICE_ORDER if s in svc_set] + sorted(svc_set - set(_SERVICE_ORDER))

    # ── Build node list with fixed x positions ─────────────────────────────
    layer_nodes = [(l0, 0), (l1, 1), (l2, 2), (l3, 3)]
    node_labels, node_x, node_layer = [], [], []
    for nodes, layer in layer_nodes:
        for n in nodes:
            node_labels.append(n)
            node_x.append(_LAYER_X[layer])
            node_layer.append(layer)

    if not node_labels:
        return None

    idx = {label: i for i, label in enumerate(node_labels)}

    # Distribute y evenly within each layer column
    layer_counts = {0: len(l0), 1: len(l1), 2: len(l2), 3: len(l3)}
    layer_counters = {k: 0 for k in range(4)}
    node_y = []
    for layer in node_layer:
        n = layer_counts[layer]
        i = layer_counters[layer]
        node_y.append((i + 0.5) / n if n > 1 else 0.5)
        layer_counters[layer] += 1

    # ── Node colours ───────────────────────────────────────────────────────
    carrier_colour_map = {
        row['primary_carrier']: _carrier_colour(row['_carrier_raw'])
        for _, row in df.drop_duplicates('primary_carrier').iterrows()
    }

    def _node_colour(label, layer):
        if label in (_NO_DISTRICT, _NO_BUILDING):
            return _PLACEHOLDER_COLOUR
        if layer == 0:
            return carrier_colour_map.get(label, COLOURS_TO_RGB['grey'])
        if layer in (1, 2):
            return _tech_colour(label)
        return _SERVICE_COLOURS.get(label, COLOURS_TO_RGB['grey'])

    node_colors = [_node_colour(label, layer) for label, layer in zip(node_labels, node_layer)]

    # ── Link builder ───────────────────────────────────────────────────────
    srcs, tgts, vals, link_colors = [], [], [], []

    def add_link(src, tgt, val, colour):
        if src not in idx or tgt not in idx or val <= 0:
            return
        srcs.append(idx[src])
        tgts.append(idx[tgt])
        vals.append(val / divisor)
        link_colors.append(_to_rgba(colour))

    # ── District flows: carrier → district_comp → building_comp → service ──
    if not district_df.empty:
        # Layer 0→1: one link per (carrier, plant_comp) — use plant_input_kWh
        for (carrier, pc), grp in district_df.groupby(['primary_carrier', 'plant_component']):
            c_colour = carrier_colour_map.get(carrier, COLOURS_TO_RGB['grey'])
            plant_val = grp['plant_input_kWh'].iloc[0]
            d1 = pc if (show_district and pc) else _NO_DISTRICT
            add_link(carrier, d1, plant_val, c_colour)

        # Layer 1→2→3: per row (aggregated to one row per service)
        for _, row in district_df.iterrows():
            pc = row['plant_component']
            bc = row['building_component']
            service = row['service']
            val = row['value_kWh']

            d1 = pc if (show_district and pc and pc in idx) else _NO_DISTRICT
            d2 = bc if (show_building and bc and bc in idx) else _NO_BUILDING
            d1_colour = _tech_colour(d1) if d1 != _NO_DISTRICT else _PLACEHOLDER_COLOUR
            d2_colour = _tech_colour(d2) if d2 != _NO_BUILDING else _PLACEHOLDER_COLOUR

            add_link(d1, d2, val, d1_colour)
            add_link(d2, service, val, d2_colour)

    # ── Building-scale flows: carrier → No District → building_comp → service
    for _, row in building_df.iterrows():
        carrier = row['primary_carrier']
        bc = row['building_component']
        service = row['service']
        val = row['value_kWh']
        c_colour = carrier_colour_map.get(carrier, COLOURS_TO_RGB['grey'])

        d2 = bc if (show_building and bc and bc in idx) else _NO_BUILDING
        d2_colour = _tech_colour(d2) if d2 != _NO_BUILDING else _PLACEHOLDER_COLOUR

        add_link(carrier, _NO_DISTRICT, val, c_colour)
        add_link(_NO_DISTRICT, d2, val, _PLACEHOLDER_COLOUR)
        add_link(d2, service, val, d2_colour)

    if not srcs:
        return None

    return {
        'node_labels': node_labels,
        'node_colors': node_colors,
        'node_x':      node_x,
        'node_y':      node_y,
        'source':      srcs,
        'target':      tgts,
        'value':       vals,
        'link_colors': link_colors,
    }


# ── figure builder ────────────────────────────────────────────────────────────

def create_sankey_fig(sankey_data, title, unit_label):
    fig = go.Figure(go.Sankey(
        arrangement='fixed',
        node=dict(
            label=sankey_data['node_labels'],
            color=sankey_data['node_colors'],
            x=sankey_data['node_x'],
            y=sankey_data['node_y'],
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
